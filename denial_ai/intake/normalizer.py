"""Turn extracted strings into typed values and link them to the knowledge base."""

import math
import re
from datetime import date

from ..knowledge import INSURER_ALIASES, TPA_ALIASES, clause_number_key, get_kb
from ..schemas import ClauseMatch

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}

MONTH_NAME = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?"
              r"|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)")
DATE_PATTERN = (
    r"\d{4}-\d{1,2}-\d{1,2}"
    r"|\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}"
    # 13 August 2024, 13th Aug, 2024, 02-FEB-2023, 08-JAN-23 (two-digit year only with a month name)
    r"|\d{1,2}(?:st|nd|rd|th)?[\s\-/]*(?i:" + MONTH_NAME + r")\.?,?[\s\-/]*(?:\d{4}|\d{2}(?!\d))"
    r"|(?i:" + MONTH_NAME + r")\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}"
)
AMOUNT_PATTERN = r"(?:Rs\.?|INR|₹)\s*(\d[\d,.]*\d|\d)"


def parse_date(s):
    """Return an ISO date string. Numeric dates are read day first, as in Indian letters."""
    if not s:
        return None
    s = s.strip().rstrip(".,")
    try:
        if m := re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s):
            y, mo, d = map(int, m.groups())
        elif m := re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})", s):
            d, mo, y = map(int, m.groups())
            y += 2000 if y < 100 else 0
        elif m := re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?[\s\-/]*([A-Za-z]{3,9})\.?,?[\s\-/]*(\d{4}|\d{2})", s):
            d, mo, y = int(m[1]), MONTHS[m[2][:3].lower()], int(m[3])
            y += 2000 if y < 100 else 0
        elif m := re.fullmatch(r"([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", s):
            d, mo, y = int(m[2]), MONTHS[m[1][:3].lower()], int(m[3])
        else:
            return None
        return date(y, mo, d).isoformat()
    except (KeyError, ValueError):
        return None


def parse_amount(s):
    """'1,275,000' or '4,50,000' (lakh grouping) or '12500.50' -> float. OCR may read
    the commas as dots ('3.95.000', '98.450'): when every separator is followed by a
    group of digits and the last group has three, they are all thousands separators."""
    if not s:
        return None
    s = s.strip().rstrip(".,")
    try:
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{2,3})*[.,]\d{3}", s):
            return float(re.sub(r"[.,]", "", s))
        return float(s.replace(",", ""))
    except ValueError:
        return None


def name_pattern(name):
    """Regex for a multi-word name that also matches it with the spaces lost or
    doubled, as OCR often returns it ("HDFCERGO", "Optima  Restore"), or with a
    space put inside a word written in two capitalised parts ("Advant Edge")."""
    words = [re.sub(r"(?<=[a-z])(?=[A-Z])", r"\\s*", re.escape(w)) for w in name.split()]
    return r"\s*".join(words)


def _alias_pattern(alias):
    # A one-word alias ("ACKO", "Medsave") must stand alone; a longer one may have
    # its spaces lost or be glued to the next word by OCR ("HDFCERGOGeneral").
    p = name_pattern(alias)
    return rf"(?<![A-Za-z]){p}(?![A-Za-z])" if " " not in alias else p


def match_insurer(text, aliases_by_name=INSURER_ALIASES):
    """Earliest insurer named in the text, with the spans of every alias mention."""
    best, spans = None, []
    for insurer, aliases in aliases_by_name.items():
        for alias in sorted(aliases, key=len, reverse=True):
            for m in re.finditer(_alias_pattern(alias), text, re.I):
                spans.append(m.span())
                if best is None or m.start() < best[1]:
                    best = (insurer, m.start())
    return (best[0] if best else None), spans


def match_tpa(text):
    """Third-party administrator named in the letter, if any."""
    return match_insurer(text, TPA_ALIASES)[0]


def match_product(text, insurer=None, skip_spans=()):
    """Longest product name in the text that is not part of an insurer name."""
    kb = get_kb()
    aliases = sorted(kb.product_aliases.items(), key=lambda kv: len(kv[0]), reverse=True)
    for alias, product in aliases:
        if insurer and kb.insurer_of(product) != insurer:
            continue
        # "Proposal for my: Optima Secure" and "Product Name:Optima Secure" both name the product.
        for m in re.finditer(r"(?<![A-Za-z0-9])" + name_pattern(alias) + r"(?![A-Za-z0-9])", text):
            # Longer names are tried first, so "Care Supreme" wins over "Care";
            # "Care" inside the insurer name "Care Health" is skipped here.
            if any(a <= m.start() < b for a, b in skip_spans):
                continue
            return product
    return None


def check_icd10(code):
    row = get_kb().icd10_lookup(code)
    if row is None:
        return False, None
    return True, row["is_billable"] == "True"


# Policy vocabulary used to widen the stated reason before it is compared with
# clause text. A letter says "Non-Medical Expenses"; the clause says "consumables".
REASON_SYNONYMS = {
    r"non[- ]medical": ["non-medical", "consumables", "non-payable", "annexure", "items"],
    r"pre[- ]existing": ["pre-existing", "ped", "waiting"],
    r"30[- ]day|initial": ["30 days", "first 30", "commencement", "accident", "waiting"],
    r"specified|specific": ["specified", "specific", "24 months", "listed", "waiting"],
    r"waiting": ["waiting period", "months"],
    r"room rent": ["room rent", "room", "proportionate", "single private"],
    r"co[- ]?pay": ["co-payment", "copayment", "co-pay"],
    r"investigation|evaluation": ["investigation", "evaluation", "diagnostic"],
    r"unproven|experimental": ["unproven", "experimental"],
    r"modern treatment": ["modern treatment", "robotic", "immunotherapy"],
}

STOPWORDS = set("the of and or for to in on a an is are be by with as under any this that "
                "policy clause section treatment expenses exclusion period".split())


def _terms(text):
    return {w.rstrip("s") for w in re.findall(r"[a-z0-9][a-z0-9\-]+", text.lower()) if w not in STOPWORDS}


QUOTE_MIN_CHARS = 60      # a letter sentence this long can be a quotation of the policy
QUOTE_MIN_SIMILARITY = 90  # rapidfuzz partial_ratio for "the letter quotes this clause"
CONFIDENT_RATIO = 1.5      # top score must beat the runner-up by this factor
SAME_WORDING = 90          # rapidfuzz ratio above which two clauses state the same rule


def _quoted_clause_ids(letter_text, clauses):
    """Clauses whose wording the letter reproduces. IRDAI asks insurers to quote the
    exclusion they rely on, and a quotation pins the clause down exactly."""
    from rapidfuzz import fuzz

    sentences = [s.strip() for s in re.split(r"(?<=[.;:])\s+|\n+|[\"“”]", letter_text or "")
                 if len(s.strip()) >= QUOTE_MIN_CHARS]
    found = {}
    for c in clauses:
        body = c["clause_text"].lower()
        best = max((fuzz.partial_ratio(s.lower(), body) for s in sentences), default=0)
        if best >= QUOTE_MIN_SIMILARITY:
            found[c["clause_id"]] = best
    return found


def _rank(candidates, hint, context):
    """Score candidates against the stated reason. The short reason next to the clause
    ("Room Rent Limit") is the main query; the rest of the letter only breaks ties,
    since it also names the hospital, procedure and dates."""
    reason = (hint or "").lower()
    context_text = (context or "").lower()
    phrases = []
    for pattern, words in REASON_SYNONYMS.items():
        if re.search(pattern, reason or context_text):
            phrases.extend(words)
    query = _terms(reason) | {p for p in phrases if " " not in p}
    context_terms = _terms(context_text) - query
    reason = reason or context_text

    # Inverse document frequency over the candidate set, so terms that every
    # candidate shares count for little.
    docs = [(c, (c["section"] + " " + c["clause_text"]).lower()) for c in candidates]
    doc_terms = [_terms(d) for _, d in docs]
    n = len(docs)

    def idf(t):
        return math.log((n + 1) / (sum(t in dt for dt in doc_terms) + 0.5))

    scored = []
    for (c, d), dt in zip(docs, doc_terms):
        score = sum(idf(t) for t in query & dt) + 0.2 * sum(idf(t) for t in context_terms & dt)
        score += sum(1.5 for p in phrases if " " in p and p in d)
        if "waiting" in reason and c["clause_type"] == "WAITING_PERIOD":
            score += 1.0
        if "exclusion" in reason and c["clause_type"] == "EXCLUSION":
            score += 1.0
        scored.append([score, c, "reason terms"])
    return scored


def resolve_clause(product, clause_raw, hint, context=None, letter_text=None, top_k=3):
    """Find the policy clause a letter relies on.

    Returns (candidates, status, note). Status is one of:
      quoted            the letter reproduces the clause's wording
      unique            only one clause of the product carries the cited number
      confident         several do, and the stated reason clearly favours one
      ambiguous         several do and the reason does not separate them: needs review
      number_not_found  the cited number is not in this product's wording; best guesses by reason
      no_number         no clause number was cited; best guesses by reason
      unresolved        nothing to go on
    """
    kb = get_kb()
    if not product:
        return [], "unresolved", "product not identified"
    product_clauses = [c for c in kb.clauses if c["product_name"] == product]
    quoted = _quoted_clause_ids(letter_text, product_clauses)

    number = None
    if clause_raw:
        number = re.sub(r"^(clause|section|condition|exclusion)\s*(no\.?)?\s*", "", clause_raw.strip(), flags=re.I)
    numbered = kb.clause_candidates(product, number) if number else []

    if numbered:
        pool, status = numbered, None
    elif quoted:
        pool, status = [c for c in product_clauses if c["clause_id"] in quoted], None
    elif hint or context:
        pool = product_clauses
        status = "number_not_found" if number else "no_number"
    else:
        return [], "unresolved", "no clause number, quotation or stated reason"

    scored = _rank(pool, hint, context)
    for s in scored:
        if s[1]["clause_id"] in quoted:
            s[0] += 10.0
            s[2] = f"letter quotes this clause ({quoted[s[1]['clause_id']]:.0f}% match)"
    scored.sort(key=lambda sc: -sc[0])

    # Policies sometimes print the same rule twice (in a summary table and in the
    # exclusions section). Near-identical wording is one answer, not a tie.
    from rapidfuzz import fuzz

    lead_text = scored[0][1]["clause_text"][:400]
    rivals = [s for s in scored[1:] if fuzz.ratio(lead_text, s[1]["clause_text"][:400]) < SAME_WORDING]
    top, second = scored[0][0], (rivals[0][0] if rivals else 0.0)
    if status is None:
        if scored[0][1]["clause_id"] in quoted:
            status = "quoted"
        elif len(scored) == 1 or (not rivals and top > 0):
            status = "unique"
        elif top > 0 and top >= CONFIDENT_RATIO * second:
            status = "confident"
        else:
            status = "ambiguous"

    notes = {
        "quoted": "the letter reproduces this clause's wording",
        "unique": (f"only clause numbered {number} in {product}" if len(scored) == 1 else
                   f"{len(scored)} clauses numbered {number}; the best matches state the same rule"),
        "confident": f"{len(scored)} clauses numbered {number}; the stated reason favours this one",
        "ambiguous": f"{len(scored)} clauses numbered {number} and the stated reason does not separate them",
        "number_not_found": f"no clause numbered {number} in {product}; ranked by the stated reason",
        "no_number": "no clause number cited; ranked by the stated reason",
    }
    norm = top if top > 0 else 1.0
    matches = [
        ClauseMatch(
            clause_id=c["clause_id"], clause_number=c["clause_number"], clause_type=c["clause_type"],
            section=c["section"], score=round(max(s, 0.0) / norm, 3), evidence=why,
            text_preview=c["clause_text"][:200],
        )
        for s, c, why in scored[:top_k]
    ]
    return matches, status, notes[status]


__all__ = ["DATE_PATTERN", "AMOUNT_PATTERN", "parse_date", "parse_amount", "match_insurer", "match_tpa",
           "match_product", "check_icd10", "resolve_clause", "clause_number_key"]
