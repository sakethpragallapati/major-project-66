"""Put back the spaces OCR drops between words ("hospitalisationwhich").

A run of eight or more letters that is not itself a known word is split into
known words with the lowest total cost, where a common word costs less than a
rare one (Zipf's law, as in the wordninja segmenter). The words come from the
runtime tables (policy wordings, denial reasons, ICD-10 and procedure names),
the insurer names and a short list of words used in letters. A run that cannot
be split entirely into known words, such as a name ("VASUNDHRASHAHI"), is left
as it is.
"""

import math
import re
from functools import lru_cache

MIN_RUN = 8          # shorter runs are left alone: "Fortis" is not "fort is"...
MIN_CASE_RUN = 5     # ...unless a capital follows a small letter inside them ("toAdmit")
MIN_MEAN_PIECE = 3   # "Andheri" is not "and her i"
COMMON_BOOST = 50    # extra count given to common English words when ranking
CASE_BONUS = 3.0     # cost taken off a split where a capital follows a small letter
ADDRESS = r"[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+|(?:https?://|www\.)\S+|\b[\w\-]+\.(?:com|in|org|net|co\.in)\b"
# Two-letter words allowed as a piece; others ("un", "re", "co") split real words wrongly.
SHORT_WORDS = {"a", "to", "of", "in", "on", "at", "by", "is", "it", "as", "an", "or", "be", "we", "us", "no",
               "my", "do", "if", "so", "up", "me", "he", "id"}

LETTER_WORDS = """
dear sir madam greetings regards sincerely faithfully truly team trusted partner partners assistance nearest branch
branches kindly perused regret inform unable admit admitted assessment observed comprehensive writing regard mentioned
below above remarks detailed correspondence future quote application proposal proposed underwriting experts norms
offer coverage member members refund premium shortly receiving initiated process note applied product products
decision decisions communicated independently individual conditions terms cost wherever deducted balance applicable
customer customers care contact call write visit complete list website email toll free number welcome choosing thank
thanks health insurance company limited general allied private solutions services technologies compass insured
patient patients hospital hospitals hospitalisation hospitalization treatment fever medically necessary warrant liable
payment respect policy claim claims intimation name age gender female male years months period date admission
location greater benefit across country association continued forward look insurability indicator disease comparison
subject medical reports finding findings cited reviewed basis available information following reason reasons
specified however reapply alternate alternative sum query response received accepted rejection satisfied
resolution provided grievance redressal procedure ombudsman office details associate vice president exhausted
settled documents submitted preferring behalf committed valued assure best times clarification feel address
preference pleased assist reject stands rejected repudiated repudiation denied declined approved approval
reimbursement cashless authorisation authorization request requested regarding enclosed attached unfortunately
please contact helpline registered corporate floor road building mumbai chennai delhi bangalore hyderabad pune
lombard icici hdfc ergo optima secure restore star women care supreme arogya sanjeevani bupa niva digit bajaj
allianz tata aig pvt ltd llp
"""


@lru_cache(maxsize=1)
def _costs():
    """Word -> cost, and the set of words that may be a piece of a split run."""
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

    from ..knowledge import get_kb

    kb = get_kb()
    counts = {}

    def add(text, weight=1):
        for w in re.findall(r"[a-z]+", (text or "").lower()):
            counts[w] = counts.get(w, 0) + weight

    for r in kb.clauses:
        add(r["clause_text"])
        add(r["exception_text"])
        add(r["section"])
        add(r["product_name"])
    for r in kb.denial_reasons:
        for k in ("sub_category", "reason_text", "carc_description", "rarc_description", "irdai_clause_grounding",
                  "appeal_route"):
            add(r[k])
    for r in kb.icd10.values():
        add(r["short_description"])
    common = set(LETTER_WORDS.split()) | {w for w in ENGLISH_STOP_WORDS if len(w) > 2 or w in SHORT_WORDS}
    words = {w for w, n in counts.items() if n >= 2 and len(w) > 2} - common

    def freq(w):
        return math.inf if w in common else counts.get(w, 0) if w in words else 0

    def piece_ok(w):
        return w in SHORT_WORDS if len(w) <= 2 else (w in common or (w in words and len(w) >= 4))

    # The policy wordings were themselves extracted from PDFs and hold some merged
    # words ("incase", "icicilombard"): a word made of two far more frequent words is dropped.
    words = {w for w in words if not any(
        piece_ok(w[:i]) and piece_ok(w[i:]) and counts[w] * 10 < min(freq(w[:i]), freq(w[i:]))
        for i in range(1, len(w)))}
    # Ranked by how often the tables use them, common words ahead of rare ones, so
    # "treatmentoffever" is "of fever" rather than "off ever".
    ranked = sorted(common | words, key=lambda w: (-(counts.get(w, 0) + (COMMON_BOOST if w in common else 0)), w))
    log_n = math.log(len(ranked))
    costs = {w: math.log((i + 1) * log_n) for i, w in enumerate(ranked)}
    # A short rare word is too easily found inside a name, so three-letter pieces must be common.
    pieces = common | {w for w in words if len(w) >= 4}
    return costs, pieces


def split_run(run):
    """Known words that make up `run`, or None if it cannot be split into them."""
    costs, allowed = _costs()
    low = run.lower()
    if low in costs:
        return None
    longest = 24
    best = [(0.0, 0)] + [(math.inf, 0)] * len(low)
    for i in range(1, len(low) + 1):
        for j in range(max(0, i - longest), i):
            piece = low[j:i]
            if piece not in allowed or (len(piece) <= 2 and piece not in SHORT_WORDS):
                continue
            cost = costs[piece]
            # A capital after a small letter ("ofFEVER", "theInsured") marks a word start.
            if 0 < j and run[j - 1].islower() and run[j].isupper():
                cost -= CASE_BONUS
            if best[j][0] + cost < best[i][0]:
                best[i] = (best[j][0] + cost, j)
    if best[-1][0] == math.inf:
        return None
    pieces, i = [], len(low)
    while i > 0:
        j = best[i][1]
        pieces.insert(0, run[j:i])
        i = j
    if len(pieces) < 2 or len(run) / len(pieces) < MIN_MEAN_PIECE:
        return None
    return pieces


def respace(text):
    """Text with merged words split, for OCR output only. E-mail and web
    addresses are left as they are."""
    def fix(m):
        run = m[0]
        if len(run) < MIN_RUN and not re.search(r"[a-z][A-Z]", run):
            return run
        pieces = split_run(run)
        if not pieces and run.lower() not in _costs()[0]:
            # A word the vocabulary lacks: split only where a capital follows two small
            # letters and both sides are three letters or more ("YoungStar", not "McDonald").
            return re.sub(r"(?<=[a-z]{2})(?=[A-Z][a-z]{2})", " ", run)
        return " ".join(pieces) if pieces else run

    out, pos = [], 0
    for m in re.finditer(ADDRESS, text):
        out.append(re.sub(r"[A-Za-z]{%d,}" % MIN_CASE_RUN, fix, text[pos:m.start()]) + m[0])
        pos = m.end()
    out.append(re.sub(r"[A-Za-z]{%d,}" % MIN_CASE_RUN, fix, text[pos:]))
    return "".join(out)
