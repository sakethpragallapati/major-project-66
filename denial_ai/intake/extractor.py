"""Field extraction from a repudiation letter.

Two passes: labelled fields ("Claim: CLM-2024-1234", "Billed Amount: Rs. 2,00,000")
and narrative patterns ("your claim for Rs ... has been repudiated under Clause 4.3").
A labelled value wins over a narrative one. Fields that are not found stay empty.
"""

import re

from rapidfuzz import fuzz, process

from ..schemas import IntakeEntities
from .normalizer import (AMOUNT_PATTERN, DATE_PATTERN, check_icd10, match_insurer, match_product, match_tpa,
                         parse_amount, parse_date, resolve_clause)

# Label (lower case, no punctuation, "&" read as "and", "(s)" dropped) -> field.
LABELS = {
    "claim": "claim_id", "claim no": "claim_id", "claim number": "claim_id", "claim id": "claim_id",
    "claim reference": "claim_id", "claim ref": "claim_id", "ccn": "claim_id", "al no": "claim_id",
    "claim intimation number": "claim_id", "claim intimation no": "claim_id", "intimation number": "claim_id",
    "intimation no": "claim_id", "claim registration number": "claim_id", "claim reg no": "claim_id",
    "claim reference number": "claim_id", "claim ref no": "claim_id", "tpa claim no": "claim_id",
    "tpa claim number": "claim_id", "pre-auth no": "claim_id", "pre-auth number": "claim_id",
    "preauth no": "claim_id", "preauth number": "claim_id", "al number": "claim_id",
    "cashless request no": "claim_id", "cashless request number": "claim_id",
    "application no": "application_number", "application number": "application_number",
    "proposal no": "application_number", "proposal number": "application_number",
    # A letter's own reference is not the claim number ("Ref : 82"), though some insurers put
    # the claim number there; extract_entities decides.
    "ref": "letter_ref", "reference": "letter_ref", "reference no": "letter_ref", "letter ref": "letter_ref",
    "our ref": "letter_ref",
    "policy no": "policy_number", "policy number": "policy_number",
    "policy": "policy_label", "plan": "policy_label", "product": "policy_label", "policy name": "policy_label",
    "product name": "policy_label", "plan name": "policy_label", "scheme name": "policy_label",
    "policy holder": "policy_holder", "proposer": "policy_holder", "corporate name": "policy_holder",
    "group name": "policy_holder", "employer": "policy_holder", "policy holder name": "policy_holder",
    "coverage period": "coverage_period", "policy period": "coverage_period", "period of insurance": "coverage_period",
    "policy tenure": "coverage_period", "period of cover": "coverage_period",
    "uhid": "member_id", "member id": "member_id", "health card no": "member_id", "id card no": "member_id",
    "tpa id": "member_id", "e-card no": "member_id",
    "tpa": "tpa", "tpa name": "tpa",
    "date": "denial_date", "letter date": "denial_date", "date of letter": "denial_date", "dated": "denial_date",
    "date of admission": "admission_date", "admission date": "admission_date", "doa": "admission_date",
    "date of hospitalization": "admission_date", "date of hospitalisation": "admission_date",
    "hospital": "hospital_name", "hospital name": "hospital_name", "name of hospital": "hospital_name",
    "name of the hospital": "hospital_name", "name of the hospital and location": "hospital_name",
    "hospital name and address": "hospital_name", "hospital name and location": "hospital_name",
    "hospital name and city": "hospital_name", "name of hospital and city": "hospital_name",
    "provider name": "hospital_name", "treating hospital": "hospital_name",
    "diagnosis": "diagnosis", "provisional diagnosis": "diagnosis", "final diagnosis": "diagnosis",
    "ailment": "diagnosis", "illness": "diagnosis", "nature of illness": "diagnosis", "disease": "diagnosis",
    "procedure": "procedure", "procedure/treatment": "procedure", "treatment": "procedure", "surgery": "procedure",
    "diagnosis code": "icd10_code", "icd-10 code": "icd10_code", "icd-10": "icd10_code", "icd code": "icd10_code",
    "claimed amount": "claimed_amount", "billed amount": "claimed_amount", "claim amount": "claimed_amount",
    "amount claimed": "claimed_amount", "bill amount": "claimed_amount", "total bill amount": "claimed_amount",
    "requested amount": "claimed_amount", "amount requested": "claimed_amount",
    "denial reason": "reason_label", "reason for denial": "reason_label", "denial ground": "reason_label",
    "reason for repudiation": "reason_label", "ground of repudiation": "reason_label", "reason": "reason_label",
    "reason for rejection": "reason_label", "rejection reason": "reason_label", "repudiation reason": "reason_label",
    "reason for non admission": "reason_label", "reasons": "reason_label",
    "to": "patient_name", "patient name": "patient_name", "patient": "patient_name", "insured name": "patient_name",
    "name of patient": "patient_name", "name of insured": "patient_name", "claim of": "patient_name",
    "name of the patient": "patient_name", "insured person": "patient_name", "member name": "patient_name",
    "name of the insured": "patient_name", "name of insured person": "patient_name",
    "name of the insured person": "patient_name", "patients name": "patient_name", "claimant name": "patient_name",
    "name of claimant": "patient_name", "name of the claimant": "patient_name", "beneficiary name": "patient_name",
    "insured member": "patient_name", "name of the member": "patient_name",
}
# Labels that hold no field here but end the value before them ("Patient: Ravi Kumar  Age: 45").
OTHER_LABELS = ["age", "gender", "sex", "age/gender", "age / gender", "time", "sum insured", "contact no", "mobile",
                "mobile no", "phone", "email", "e-mail", "address", "relation", "relationship", "date of discharge",
                "discharge date", "doctor", "treating doctor", "room category", "room type", "city", "state",
                "pin", "pincode", "employee id", "employee code", "balance sum insured"]
# Labels with the spaces removed, because OCR often joins words ("Claimof", "PolicyNumber").
LABELS_NOSPACE = {k.replace(" ", ""): v for k, v in LABELS.items()}
# Labels that may appear in a table row with no colon ("Claim Number   220202875738"). Single
# words are left out ("Date", "Claim", "Reason"), since many ordinary sentences start with them,
# and so are reasons ("The reason for rejection is ...").
TABLE_LABELS = sorted((k for k, f in LABELS.items() if (" " in k or k in {"uhid", "doa", "ccn"})
                       and f != "reason_label"), key=len, reverse=True)


def _label_regex(labels):
    return "|".join(r"\s*".join(map(re.escape, k.split())) for k in labels)


# OCR may read the colon after a label as a dot or a semicolon ("Name of Insured. Mr. X").
TABLE_LABEL_RE = re.compile(r"^\s*(" + _label_regex(TABLE_LABELS) + r")\s*[.;]?\s+(\S.{0,80}?)\s*$", re.I)
# Where a second "Label:" starts on the same row.
NEXT_LABEL_RE = re.compile(r"(?<=\s)(?:" + _label_regex(sorted(list(LABELS) + OTHER_LABELS, key=len, reverse=True))
                           + r")\s*(?:\(s\))?\s*:", re.I)
ID_TOKEN = r"\b(?=[A-Z0-9/\-]*\d)[A-Z0-9][A-Z0-9/\-]{4,}\b"
COMPANY = (r"P\s*V\s*T\.?\s*L\s*T\s*D|PRIVATE\s*LIMITED|\bLIMITED\b|\bLTD\b|\bLLP\b|CORPORATION|\bINC\b"
           r"|TECHNOLOGIES|SOLUTIONS|SERVICES|INDUSTRIES|ENTERPRISES")

# A number written with thousands groups, as an amount is: 1,12,000 or 98,450 (not 05.03.2025).
GROUPED_NUMBER = r"\d{1,3}(?:[,.]\d{2,3})*[,.]\d{3}(?![\d])"
# CLM-2024-1234, STAR/CLM/2024/889, CIR/2025/161218/1829414
CLAIM_ID = r"\b[A-Z]{2,5}[-/]\d{4}(?:[-/]\d{2,10}){1,3}\b"
ICD10 = r"\b[A-TV-Z]\d[0-9AB](?:\.[0-9A-Z]{1,4})?\b"
CLAUSE = (r"\b(?:Clause|Section|Condition|Exclusion)\s+(?:No\.?\s*)?\d+(?:\.\d+)*(?:\s*\([a-z]{1,4}\))?"
          r"|\bCode[\s\-]*Excl\s*-?\s*\d+")
HONORIFIC = r"(?:Mr\.?/Ms\.?\s*|(?:Mrs|Mr|Ms|Dr|Smt)\.\s*|(?:Mrs|Mr|Ms|Dr|Shri|Smt|Kumari)\s+)"
DENIAL_VERBS = (r"repudiat|denied|disallow|not payable|rejected|not admissible|inadmissible|declined|excluded"
                r"|unable\s*to\s*(?:admit|settle|consider|offer)|cannot\s*be\s*(?:settled|admitted|considered)"
                r"|not\s*liable")
# A letter refusing a new policy, not a claim.
PROPOSAL_REJECTION = (r"rejection\s*of\s*(?:your\s*)?proposal|proposal\s*(?:has\s*been\s*|is\s*|stands\s*)?"
                      r"(?:declined|rejected|not\s*accepted)|unable\s*to\s*offer\s*(?:the\s*|any\s*)?"
                      r"(?:coverage|cover|insurance)|declined?\s*(?:your\s*|the\s*)?proposal")
# Sentences that appear in any letter whatever the reason.
BOILERPLATE = (r"grievance|ombudsman|right to appeal|file an appeal|appeal window|quote the claim number"
               r"|therefore closed|contact your TPA|^(?:claim )?repudiation (?:notice|letter)$"
               r"|^subject:|^issued by|^ref(?:erence)?\b|^date\b|reviewed by our medical team"
               # courtesy lines, contact details and signatures; OCR may drop their spaces
               r"|thank\s*you|on\s*behalf\s*of|remain\s*committed|valued\s*customer|further\s*clarification"
               r"|pleased\s*to\s*assist|in\s*case\s*(?:you|no\s*response)|considered\s*as\s*accepted|kindly\s*contact"
               r"|https?://|e-?mail\s*us|toll\s*free|customer\s*care|vice\s*president|authori[sz]ed\s*signatory"
               r"|^sr\.?\s*no\b|^for\s+.{0,60}(?:company|ltd|limited)\b"
               r"|greetings|writing\s*(?:to\s*you\s*)?with\s*regard|trusted\s*partner|look\s*forward"
               r"|continued\s*association|^regards|^yours\b|^team\b|\(team\b|registration\s*no|\bCIN\s*:"
               r"|registered\s*(?:&|and)?\s*corporate\s*office|registered\s*office|corporate\s*office|website"
               r"|\bIRDAI?\s*reg|welcome\s*to|for\s*choosing|quote\s*your|future\s*correspondence"
               r"|^note\s*:?$|please\s*note|applied\s*for\s*more\s*than\s*one|nearest\s*branch")
# A heading or lead-in after which the letter lists its reasons.
REASON_HEAD = re.compile(
    r"^\s*(?:detailed\s*remarks?|remarks?|reasons?\s*(?:\(s\))?\s*(?:for|of)\s*(?:the\s*)?(?:denial|rejection"
    r"|repudiation|non[\s\-]*admission|disallowance)|(?:denial|rejection|repudiation)\s*reasons?\s*(?:\(s\))?"
    r"|reasons?\s*(?:\(s\))?|query\s*details?)\s*:\s*(.*)$", re.I)
REASON_INTRO = re.compile(
    r"(?:following|below[\s\-]*mentioned|under[\s\-]*mentioned)\s*(?:reasons?|grounds?)\s*(?:\(s\))?\s*[:.]?\s*$"
    r"|(?:reasons?|grounds?)\s*(?:\(s\))?\s*(?:as\s*)?(?:specified|mentioned|given|stated)\s*(?:below)?\s*[:.]?\s*$"
    r"|following\s*member\s*\(s\)\s*due\s*to\s*reason.*[:.]\s*$", re.I)
TABLE_HEAD = re.compile(r"^\s*(?:s(?:r|l)?\.?\s*no\.?)\s+.*(?:reason|description|remarks)", re.I)
# Lines that end a list of reasons: closing courtesy, an offer to reapply, contact details.
REASON_STOP = BOILERPLATE + r"|re-?\s*apply|alternate\s*product|we\s*(?:have\s*)?initiated|refund|^dear\b"
# "The Company shall not be liable to make any payment under this policy in respect of any ..."
EXCLUSION_PREAMBLE = (r"^(?:the\s*)?company\s*(?:is|shall)\s*not\s*(?:be\s*)?liable\s*to\s*make\s*any\s*payment"
                      r"\s*under\s*(?:this|the)\s*policy\s*in\s*respect\s*of\s*(?:any\s*)?"
                      r"(?:expenses?\s*(?:incurred\s*)?(?:for|on|in\s*respect\s*of|towards)\s*)?")


LABEL_LINE = r"\s*([A-Za-z][A-Za-z0-9 /\-.&'()]{0,45}?)\s*:\s*(.*?)\s*$"
WRAPPABLE = {"procedure", "hospital_name", "reason_label", "policy_label", "policy_holder", "diagnosis"}
# Label-only lines ("Claim Number:" with the value below) are trusted only for these.
LABEL_ONLY_FIELDS = {"claim_id", "application_number", "policy_number", "member_id", "admission_date",
                     "hospital_name", "diagnosis", "policy_label", "claimed_amount", "coverage_period"}


LABEL_ONLY_RE = re.compile(r"\s*(" + _label_regex(TABLE_LABELS) + r")\s*", re.I)


def _label_key(label):
    label = label.lower().replace("&", " and ").replace("(s)", "")
    label = re.sub(r"[.']", "", label)
    return re.sub(r"\s+", " ", label).strip()


OTHER_KEYS = {_label_key(k).replace(" ", "") for k in OTHER_LABELS}


def _field_of_label(label):
    key = _label_key(label)
    nospace = key.replace(" ", "")
    field = LABELS.get(key) or LABELS_NOSPACE.get(nospace)
    if not field and len(nospace) >= 10 and nospace not in OTHER_KEYS:
        # OCR misreads a letter or two in a long label ("Claim lntimation Nurnber").
        hit = process.extractOne(nospace, list(LABELS_NOSPACE), scorer=fuzz.ratio, score_cutoff=90)
        field = LABELS_NOSPACE[hit[0]] if hit else None
    return field


def _label_of(part):
    """(field, value) when `part` is "Label: value", "Label:" alone (value "") or a
    table row "Label   value"."""
    if m := re.match(LABEL_LINE, part):
        field = _field_of_label(m[1])
        if field and (m[2] or field in LABEL_ONLY_FIELDS):
            return field, m[2].strip()
    if len(part) <= 100 and (m := TABLE_LABEL_RE.match(part)):
        return _field_of_label(m[1]), m[2].strip()
    if len(part) <= 50 and (m := LABEL_ONLY_RE.fullmatch(part)):
        field = _field_of_label(m[1])
        if field in LABEL_ONLY_FIELDS:
            return field, ""
    return None


def _is_label_pair(segment):
    m = re.match(LABEL_LINE, segment)
    return bool(m and (_field_of_label(m[1]) or _label_key(m[1]).replace(" ", "") in OTHER_KEYS))


def _segments(line):
    """A row split into "Label: value" pieces: at "|" and where a second label starts
    after a first one ("Claim No: CLM-2024-1 Date: 12/03/2024"). A sentence that only
    contains a label word ("as per the policy: ...") is not split."""
    out = []
    for part in line.split("|"):
        cuts = [0]
        for m in NEXT_LABEL_RE.finditer(part):
            if m.start() > cuts[-1] and _is_label_pair(part[cuts[-1]:m.start()]):
                cuts.append(m.start())
        out += [part[a:b].strip() for a, b in zip(cuts, cuts[1:] + [len(part)]) if part[a:b].strip()]
    return out


def _labelled_fields(text):
    found = {}
    lines = text.split("\n")
    for i, line in enumerate(lines):
        parts = _segments(line)
        for j, part in enumerate(parts):
            hit = _label_of(part)
            if not hit:
                continue
            field, value = hit
            if field in found:
                continue
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if not value:
                # "Claim Number:" with the value on the next line, as text-layer PDFs give a table.
                if j == len(parts) - 1 and nxt and not _label_of(nxt) and not re.match(r"dear\b", nxt, re.I):
                    found[field] = nxt
                continue
            # A long value can continue on the next line, which then has no label.
            if (field in WRAPPABLE and j == len(parts) - 1 and nxt and len(nxt) <= 60
                    and not _label_of(nxt) and not re.search(r"[.:]$", value)
                    and not re.search(r"[.!?]$", nxt) and len(nxt.split()) <= 6):
                value = f"{value} {nxt}"
            found[field] = value
    return found


def _first(patterns, text, flags=0):
    for p in patterns:
        if m := re.search(p, text, flags):
            return m.group(1).strip(" ,.")
    return None


def _respace(value):
    """Put back spaces OCR dropped between capitalised words ("AorticValve")."""
    return re.sub(r"(?<=[a-z]{2})(?=[A-Z][a-z])", " ", value) if value else value


COMPANY_WORDS = ["PRIVATE", "LIMITED", "SOLUTIONS", "SERVICES", "TECHNOLOGIES", "INDUSTRIES", "ENTERPRISES",
                 "INDIA", "PVT", "LTD", "LLP"]


def _split_company(name):
    """Split company words that OCR glued on at the end of a name:
    "BLUEWAVEDIGITALSERVICESPVTLTD" -> "BLUEWAVEDIGITAL SERVICES PVT LTD"."""
    out = []
    for token in name.split():
        tail = []
        while True:
            word = next((w for w in COMPANY_WORDS if token.upper().endswith(w) and len(token) > len(w)), None)
            if not word:
                break
            tail.insert(0, token[-len(word):])
            token = token[:-len(word)]
        out.extend([token] + tail)
    return " ".join(out)


def _strip_honorific(name):
    return re.sub(r"^" + HONORIFIC, "", name.strip()).strip(" ,.")


def _sentences(text):
    # Split before a capital letter only, so "Rs. 930,000" stays in one piece,
    # and never after a title or abbreviation such as "Mr." or "No.".
    split = r"(?<!Mr\.)(?<!Ms\.)(?<!Mrs\.)(?<!Dr\.)(?<!Rs\.)(?<!No\.)(?<=[.!?])\s+(?=[A-Z])|\n+"
    return [s for s in re.split(split, text) if s.strip()]


def _reason_sentences(text):
    """The letter's body without headers, labelled fields and standard closing lines.

    Insurers often state the reason without a denial verb ("the dependent was
    added after the date of hospitalization"), so the body is kept whole and
    only text that never carries a reason is removed.
    """
    # The letterhead, address block and date come before the salutation.
    if (m := re.search(r"^[ \t]*Dear\b", text, re.M | re.I)) and m.start() < 0.6 * len(text):
        text = text[m.start():]
    kept = []
    for s in _sentences(text):
        s = re.sub(r"^\s*Dear\s+[^,]{1,60},\s*", "", s).strip()
        if TABLE_LABEL_RE.match(s) and not re.search(DENIAL_VERBS, s, re.I):   # "Claim Number 2202..."
            continue
        s = re.sub(r"^(?:With reference to|This refers to|After review of the documents submitted for)"
                   r"[^,.]{0,120}?(?:claim\s+)?" + CLAIM_ID + r"[^,.]*[,.]\s*", "", s, flags=re.I).strip()
        s = re.sub(r"^We have examined your claim\s+" + CLAIM_ID + r"[^.]*\.\s*", "", s, flags=re.I).strip()
        # "We regret to inform you that" carries no reason, but the rest of the sentence may.
        s = re.sub(r"^(?:We\s+have\s+perused[^.]{0,80}?and\s+)?(?:we\s+)?regret\s*to\s*inform\s*you\s*(?:that\s*)?",
                   "", s, flags=re.I).strip()
        if len(s.split()) < 4 and not re.search(DENIAL_VERBS, s, re.I):   # headers, names, salutations
            continue
        if s.upper() == s and not re.search(DENIAL_VERBS, s, re.I):      # letterheads in capitals
            continue
        if re.match(r"^[A-Za-z][A-Za-z0-9 /\-.]{0,30}:\s*(?!.*\bClause\b)", s) and not re.search(
                DENIAL_VERBS, s, re.I):
            continue
        if re.search(BOILERPLATE, s, re.I) and not re.search(r"\bclause\b|\bexclu|\bwaiting\b", s, re.I):
            continue
        kept.append(s)
    return " ".join(kept) if kept else None


def extract_entities(text):
    lab = _labelled_fields(text)
    e = IntakeEntities()

    # Claim ID: a labelled claim number (CLM-2024-1234 or a plain number such as
    # 220202875738), then an ID written next to the word "claim", then a letter
    # reference that has the claim-ID shape, then any claim-shaped ID. A bare letter
    # reference ("Ref : 82") is never taken as the claim number.
    raw_claim, ref = lab.get("claim_id"), lab.get("letter_ref")
    near_claim = (re.search(r"\bclaim\b[^\n]{0,30}?(" + CLAIM_ID + ")", text, re.I)
                  or re.search(r"\bclaim\s*(?:no\.?|number|id|ref(?:erence)?)\s*[:.\-]?\s*(" + ID_TOKEN + ")",
                               text, re.I))
    any_id = re.search(CLAIM_ID, text)
    if raw_claim and (m := re.search(CLAIM_ID, raw_claim) or re.search(ID_TOKEN, raw_claim.upper())):
        e.claim_id = m[0]
    elif near_claim:
        e.claim_id = near_claim[1]
    elif ref and re.search(CLAIM_ID, ref):
        e.claim_id = re.search(CLAIM_ID, ref)[0]
    elif any_id:
        e.claim_id = any_id[0]
    if ref and ref != e.claim_id:
        e.letter_ref = ref
    e.member_id = (m[0] if (m := re.search(ID_TOKEN, (lab.get("member_id") or "").upper())) else None)
    app = lab.get("application_number") or _first(
        [r"(?i:application|proposal)\s*(?i:no\.?|number)\s*[:.\-]?\s*([A-Z0-9][A-Z0-9/\-]{5,})"], text)
    e.application_number = (m[0] if app and (m := re.search(ID_TOKEN, app.upper())) else None)

    # Patient: "Dear Sir/Madam" names nobody, so it falls through to the address block.
    name = lab.get("patient_name") or _first(
        [r"Dear\s+(?:" + HONORIFIC + r")?(?!(?:Sir|Madam|Customer|Policyholder)\b)([A-Z][A-Za-z.' ]+?)\s*,",
         r"^To,?\s*\n\s*(?:" + HONORIFIC + r")?([A-Z][A-Za-z.' ]+?)\s*$",
         r"\bInsured\s*:\s*([A-Z][A-Za-z.' ]+)"], text, re.M)
    if name:
        # "RAVI KUMAR (M/45)", "Ravi Kumar, 45 years"
        name = re.sub(r"\s*(?:\(|,|-)\s*(?:\d|[MF]\s*/|male|female).*$", "", name, flags=re.I)
        # A name's words are capitalised, so a word starting "l" was an "I" ("Ramesh lyer").
        name = re.sub(r"\bl(?=[a-z])", "I", name)
    e.patient_name = _strip_honorific(name) if name else None

    # Insurer, TPA and product
    e.insurer, insurer_spans = match_insurer(text)
    e.tpa = match_tpa(lab.get("tpa") or "") or match_tpa(text) or (lab.get("tpa") or "").strip(" ,.") or None
    product_text = lab.get("policy_label") or ""
    e.policy_product = (match_product(product_text, e.insurer) if product_text else None) \
        or match_product(text, e.insurer, insurer_spans)
    if e.policy_product and not e.insurer:
        from ..knowledge import get_kb
        e.insurer = get_kb().insurer_of(e.policy_product)
    e.policy_number = (m[0] if (m := re.search(ID_TOKEN, (lab.get("policy_number") or "").upper())) else None) \
        or _first([r"Policy\s+No\.?\s*:?\s*([A-Z0-9/\-]{5,})"], text)

    # Group policies carry the employer's name instead of a retail product, and their
    # wording is not in the knowledge base.
    holder = lab.get("policy_holder") or (product_text if product_text and not e.policy_product else None)
    if e.policy_product:
        e.policy_type = "retail"
    elif (holder and re.search(COMPANY, holder, re.I)) or re.search(
            r"\bgroup\s*(?:health|mediclaim|insurance|policy)|\bcorporate\s*(?:policy|cover)", text, re.I):
        e.policy_type = "group"
        e.policy_holder = _split_company(re.sub(r"\s+", " ", holder).strip(" ,.")) if holder else None
    elif product_text:
        # A retail product that is not in the knowledge base ("Star Women Care Insurance Policy").
        e.policy_product_raw = re.sub(r"\s+", " ", product_text).strip(" ,.")

    # Coverage period: "21-JUL-22 to 20-JUL-23"; OCR may glue "to" to the dates.
    period = lab.get("coverage_period") or _first(
        [r"(?:coverage|policy|insurance)\s*period[^\n\d]{0,20}(\d[^\n]{6,40})"], text, re.I) or ""
    dates = re.findall(DATE_PATTERN, period)
    if len(dates) >= 2:
        e.policy_start, e.policy_end = parse_date(dates[0]), parse_date(dates[1])

    # Dates
    e.denial_date = parse_date(_first([r"(" + DATE_PATTERN + r")"], lab.get("denial_date", "")))
    if not e.denial_date:
        # A bare date on its own line near the top of the letter is the letter date.
        head = "\n".join(text.split("\n")[:6])
        e.denial_date = parse_date(_first([r"^\s*(?:Dated?\s*:?\s*)?(" + DATE_PATTERN + r")\s*$"], head, re.M | re.I))
    e.admission_date = parse_date(
        _first([r"(" + DATE_PATTERN + r")"], lab.get("admission_date", ""))
        or _first([r"(?:hospitali[sz]ation|admission|admitted|performed|undergone)"
                   r"(?:\s+at\s+[^\n]{2,80}?)?\s+(?:on|from)\s+(" + DATE_PATTERN + r")",
                   r"date of admission\s*:?\s*(" + DATE_PATTERN + r")"], text, re.I))

    # Hospital and procedure. A hospital name may wrap onto the next line.
    # Of the narrative matches, the shortest is the name; longer ones run on into the next clause.
    hospital = lab.get("hospital_name") or min(
        (m[1] for p in [r"\bat\s+([A-Z][^()]{1,80}?)\s+for\s+(?!Rs\b)",
                        r"\bat\s+([A-Z][^()]{1,80}?),\s*(?:admitted|where)\b",
                        r"\bat\s+([A-Z][^()]{1,80}?)\s+has been",
                        r"\bat\s+([A-Z][^()]{1,80}?)\s+(?:on|from)\s+(?=\d)"]
         for m in [re.search(p, text, re.S)] if m),
        key=len, default=None)
    e.hospital_name = _clean_hospital(hospital, labelled="hospital_name" in lab) if hospital else None
    diagnosis = lab.get("diagnosis") or _first(
        [r"\btreatment\s+of\s+([A-Za-z][A-Za-z ,/\-']{2,60}?)\s*(?:[:;.]|$)",
         r"\bdiagnosed\s+(?:with|as)\s+([A-Za-z][A-Za-z ,/\-']{2,60}?)\s*(?:[:;.,(]|$)",
         r"\bdiagnosis\s+of\s+([A-Za-z][A-Za-z ,/\-']{2,60}?)\s*(?:[:;.,(]|$)"], text, re.M | re.I)
    if diagnosis and "diagnosis" not in lab:
        # "treatment of obesity are excluded" names the illness, then runs on into the sentence.
        diagnosis = re.split(r"\s+(?:is|are|was|were|shall|will|be|has|have|had|not|which|that|under|as|at|on"
                             r"|from|in|for|and\s+its)\b", diagnosis, maxsplit=1, flags=re.I)[0]
    e.diagnosis = re.sub(r"^(?:the|a|an)\s+", "", re.sub(r"\s+", " ", diagnosis), flags=re.I).strip(" ,.") \
        if diagnosis else None
    proc = lab.get("procedure") or _first([
        r"\bat\s+[A-Z][^()\n]*?\s+for\s+(?!Rs\b)(.+?)\s*\(ICD",
        r"\btowards\s+(.+?)\s+(?:performed|undergone|availed)\b",
        r"\bfor\s+(?!Rs\b|INR\b)([A-Z][^\n]+?(?:\n[^\n]+?)?)\s+at\s+[A-Z]",
    ], text, re.S)   # a procedure name may wrap onto the next line
    if proc:
        proc = re.sub(r"\s+", " ", re.sub(r"\s*\[[^\]]*\]\s*$", "", proc)).strip(" ,.")
    e.procedure = _respace(proc)
    e.hospital_name = _respace(e.hospital_name)
    e.patient_name = _respace(e.patient_name)
    if not e.admission_date and e.hospital_name:
        # "... extraction at Apollo Dental, Hyderabad on 05.03.2025 is not payable"
        e.admission_date = parse_date(_first(
            [r"\bat\s+" + r"\s*".join(map(re.escape, e.hospital_name.split())) + r"[^\n.]{0,20}?\s+(?:on|from)\s+("
             + DATE_PATTERN + r")"], text, re.I))

    # ICD-10: labelled, then next to "ICD"/"diagnosis code", then in brackets
    icd = None
    for src in (lab.get("icd10_code"),
                _first([r"ICD-?10(?:\s*Code)?\s*:?\s*(" + ICD10 + ")", r"diagnosis code\s*:?\s*(" + ICD10 + ")",
                        r"\[(" + ICD10 + r")\]"], text, re.I)):
        if src and (m := re.search(ICD10, src.upper())):
            icd = m[0]
            break
    e.icd10_code = icd
    if icd:
        e.icd10_valid, e.icd10_billable = check_icd10(icd)

    # Amount: labelled, then the first amount in a sentence about the claim
    amt = lab.get("claimed_amount")
    if amt and (m := re.search(AMOUNT_PATTERN, amt)):
        e.claimed_amount = parse_amount(m[1])
    elif amt:
        e.claimed_amount = parse_amount(re.sub(r"[^\d.,]", "", amt))
    else:
        for s in _sentences(text):
            if re.search(r"claim|billed|amount", s, re.I) and (m := re.search(AMOUNT_PATTERN, s)):
                e.claimed_amount = parse_amount(m[1])
                break
        else:
            # OCR often drops the "₹", and a PDF font without it prints another sign:
            # "your claim of 1,12,000 for treatment of ..."
            if m := re.search(r"(?:claim(?:ed)?(?:\s*amount)?|amount(?:\s*claimed)?|bill(?:ed)?(?:\s*amount)?)"
                              r"\s*(?:of|for|:)?\s*[^\w\s]?\s*(" + GROUPED_NUMBER + ")", text, re.I):
                e.claimed_amount = parse_amount(m[1])

    # Cited clause and the short reason named next to it
    reason_label = lab.get("reason_label", "")
    m = re.search(CLAUSE, reason_label) or re.search(CLAUSE, text)
    if m:
        e.cited_clause_raw = re.sub(r"\s+", " ", m[0]).strip()
        after = (reason_label if re.search(CLAUSE, reason_label) else text)[m.end():]
        e.denial_category_hint = _first([
            r"^\s*\(([^)]+)\)",
            r"^\s*[-:]\s*([^\n.]+)",
            r"^\s*,?\s*which\s+pertains\s+to\s+([^,\n.]+)",
        ], after)
    if not e.denial_category_hint and reason_label and not re.search(CLAUSE, reason_label):
        e.denial_category_hint = _short_reason(reason_label) or reason_label.strip(" .")
    section = _reason_section(text, e.patient_name)
    if not e.denial_category_hint:
        e.denial_category_hint = (_reason_from_table(text) or (_short_reason(section[0]) if section else None)
                                  or _standard_reason_named(text))
    e.denial_reason_text = (_with_cited_clause(" ".join(section), text, e.cited_clause_raw) if section
                            else _reason_sentences(text))

    # A letter refusing a new policy is not a claim denial.
    if re.search(PROPOSAL_REJECTION, text, re.I) and not e.claim_id and len(re.findall(r"\bclaim", text, re.I)) < 2:
        e.letter_type = "proposal_rejection"
    elif e.claim_id or e.insurer or e.patient_name:
        e.letter_type = "claim_denial"

    if e.policy_product and e.letter_type != "proposal_rejection":
        e.clause_candidates, e.clause_resolution, e.clause_resolution_note = resolve_clause(
            e.policy_product, e.cited_clause_raw, e.denial_category_hint, e.denial_reason_text, text)
        # A clause is named as "cited" only when the letter points at it by number or
        # quotation; reason-only matches stay as suggestions for the reviewer.
        if e.clause_resolution in ("quoted", "unique", "confident", "ambiguous") and e.clause_candidates:
            e.cited_clause_id = e.clause_candidates[0].clause_id

    # Time limit for a response or appeal, in days, weeks or months ("within a period of 8 weeks").
    if m := re.search(r"within\s*(?:a\s*period\s*of\s*)?(\d{1,3})\s*(day|week|month)s?"
                      r"|(\d{1,3})\s*(day|week|month)s?\s*from\s*the\s*date", text, re.I):
        n, unit = int(m[1] or m[3]), (m[2] or m[4]).lower()
        e.appeal_window_days = n * {"day": 1, "week": 7, "month": 30}[unit]
        e.deadline_note = next((s.strip() for s in _sentences(text) if m[0] in s), m[0]).strip("\"'“” ")

    core = ["claim_id", "patient_name", "insurer", "policy_product", "policy_number", "denial_date",
            "admission_date", "hospital_name", "procedure", "icd10_code", "claimed_amount", "cited_clause_raw"]
    if e.letter_type == "proposal_rejection":
        core = ["application_number", "patient_name", "insurer", "policy_product", "denial_date"]
    e.missing_fields = [f for f in core if getattr(e, f) in (None, "")
                        and not (f == "policy_product" and (e.policy_type == "group" or e.policy_product_raw))]
    return e


def _clean_hospital(value, labelled):
    """Hospital name without the location a letter adds to it:
    "The Medicity, Rudrapur - RUDRAPUR - 263153" -> "The Medicity, Rudrapur"."""
    value = re.sub(r"\s+", " ", value).strip(" ,.")
    if labelled:
        value = re.sub(r"[\s,\-]*\b\d{6}\b$", "", value).strip(" ,.-")       # PIN code
        value = re.split(r"\s+-\s+", value)[0].strip(" ,.-")
    return value or None


def _reason_section(text, patient=None):
    """The reasons a letter lists after a heading ("Detailed Remarks:") or a lead-in
    ("...for the following reasons."), one item per line, without numbering."""
    lines = [ln.strip() for ln in text.split("\n")]
    start = None
    for i, line in enumerate(lines):
        if m := REASON_HEAD.match(line):
            start = i + 1
            if m[1].strip():
                lines[i] = m[1]
                start = i
            break
        if REASON_INTRO.search(line):
            start = i + 1
            break
    if start is None:
        return []
    items = []
    for line in lines[start:start + 10]:
        if not line:
            if items:
                break
            continue
        if m := REASON_HEAD.match(line):          # "Detailed Remarks:" after the lead-in
            line = m[1].strip()
        if not line or TABLE_HEAD.match(line):    # "Sr No  Reason  Description"
            continue
        if re.search(REASON_STOP, line, re.I) and not re.search(r"\bclause\b|\bexclu|\bwaiting\b", line, re.I):
            break
        if _label_of(line) and not re.search(DENIAL_VERBS, line, re.I):
            break
        if patient:
            # A member table: "Niraj Dodia | BMI out of range"
            line = re.sub(r"^" + r"\s*".join(map(re.escape, patient.split())) + r"\s*[|:\-]?\s*", "", line, flags=re.I)
        line = re.sub(r"^\s*(?:\d{1,2}\s*[.)]|[•\-*])\s*", "", line).strip()
        if line:
            items.append(line)
    return items


def _short_reason(item):
    """A short form of one listed reason, for the "stated reason" field."""
    item = re.sub(r"^\s*(?:\d{1,2}\s*[.)]|[•\-*])\s*", "", item).strip()
    item = re.sub(EXCLUSION_PREAMBLE, "", item, flags=re.I).strip(" .")
    return item if 0 < len(item) <= 100 else None


def _with_cited_clause(reasons, text, clause_raw):
    """The listed reasons, led by the sentence that cites a clause if it lies outside them."""
    if clause_raw and clause_raw not in reasons:
        lead = next((s.strip() for s in _sentences(text) if clause_raw in re.sub(r"\s+", " ", s)), None)
        if lead and len(lead) <= 300:
            return f"{lead} {reasons}"
    return reasons


def _reason_from_table(text):
    """The reason cell of a "Sr No | Reason | Description" table."""
    m = re.search(r"Rea\s*son\s+Des\s*cription\s*\n\s*(?:\d+\s+)?([A-Za-z][A-Za-z ,/&'\-]{3,60}?)\s*"
                  r"(?=\d+\s*[.)]|\n|$)", text, re.I)
    return m[1].strip(" ,.-") if m else None


def _standard_reason_named(text):
    """A standard denial reason named in the letter, such as "Sum Insured Exhausted"."""
    from ..knowledge import get_kb
    from .normalizer import name_pattern

    names = sorted({r["sub_category"] for r in get_kb().denial_reasons}, key=len, reverse=True)
    for name in names:
        if re.search(r"(?<!\w)" + name_pattern(name) + r"(?!\w)", text, re.I):
            return name
    return None
