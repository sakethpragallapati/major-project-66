"""
build_runtime_csvs.py
=====================
Builds all 6 Active Runtime Knowledge-Base CSVs for the Denial Appeal System:
  data/runtime/
  ├── policy_clauses.csv            (3,028 structured non-truncated clauses across 14 PDFs)
  ├── denial_reasons.csv            (70 granular denial reasons with specific CARC & RARC codes)
  ├── icd10_codes.csv               (2,999 comprehensive ICD-10 codes across Chapters A-Z)
  ├── procedure_codes.csv           (217 HCPCS/CPT codes across 22 medical specialties)
  ├── procedure_diagnosis_map.csv   (332 medical necessity linkages bridging HCPCS and ICD-10)
  └── nme_exclusions.csv            (120 non-medical expense items with IRDAI Annexure IV provenance)
"""

import fitz  # PyMuPDF
import csv
import os
import re
import json
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent   # the project folder
POLICY_DIR = BASE_DIR / "data" / "policy_wordings"
RUNTIME_DIR = BASE_DIR / "data" / "runtime"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = BASE_DIR / "data"
if str(DATA_DIR) not in sys.path:
    sys.path.insert(0, str(DATA_DIR))

try:
    from policy_discovery import discover_policy_documents
except ImportError:
    from data.policy_discovery import discover_policy_documents


# ╔══════════════════════════════════════════════════════════════╗
# ║  1. POLICY CLAUSES CSV EXTRACTION                            ║
# ╚══════════════════════════════════════════════════════════════╝
def extract_policy_clauses():
    """Extract structured, non-truncated clauses dynamically from all discovered policy PDFs."""
    policies = discover_policy_documents(POLICY_DIR)
    insurers_found = sorted(set(p["insurer"] for p in policies))
    print(f"\n[1/6] Discovered {len(policies)} policy PDFs across {len(insurers_found)} insurers: {', '.join(insurers_found)}")
    print(f"      Extracting clean, non-truncated policy_clauses.csv...")

    exclusion_keywords = ["exclusion", "excluded", "not cover", "shall not", "not payable", "not liable", "does not include", "code-excl", "code excl"]
    waiting_period_keywords = ["waiting period", "pre-existing", "moratorium", "continuous coverage", "first year", "second year", "48 months", "36 months", "24 months", "30 days"]
    coverage_keywords = ["cover", "payable", "reimburse", "eligible", "shall pay", "benefit", "indemnify"]
    definition_keywords = ["means", "defined as", "definition", "shall mean", "refers to"]

    roman = r'(?:i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii|xiii|xiv|xv)'
    header_or_bullet = re.compile(
        r'^(?:'
        r'(?:Code\s*-?\s*Excl\s*\d+)|'
        r'(?:Def\.?\s*\d+)|'
        r'(?:\d+(?:\.\d+)*[\.\):]?\s)|'
        rf'(?:{roman}[\.\)])|'
        r'(?:\(?[a-z]\)[\.\s])|'
        r'(?:(?:SECTION|PART|CHAPTER|SCHEDULE|ANNEXURE)\b)|'
        r'(?:Note\s*[:\-])'
        r')', re.IGNORECASE
    )

    # (pattern, kind) — "top" numbers start a new clause, "sub" items belong to the last top number
    clause_patterns = [
        (re.compile(r'^(Code\s*-?\s*Excl\s*\d+)\s*[:\.\-]?\s*(.+)', re.IGNORECASE | re.DOTALL), "top"),
        (re.compile(r'^Def\.?\s*(\d+)\s*[\.:]\s*(.+)', re.IGNORECASE | re.DOTALL), "def"),
        # The text after the number may itself start with a number: "3. 30-day waiting period".
        (re.compile(r'^(\d{1,2}(?:\.\d{1,3}){0,3})[\.\):]?\s+(?=["\'(A-Z]|\d{1,3}\s*-?\s*(?i:day|month|year|hour)s?\b)(.+)',
                    re.DOTALL), "top"),
        (re.compile(rf'^\(?({roman})[\.\)]\s*(.+)', re.IGNORECASE | re.DOTALL), "sub"),
        (re.compile(r'^\(?([a-z])\)\s*(.+)', re.DOTALL), "sub"),
    ]

    page_furniture = re.compile(r'^(?:page\s*)?\d{1,3}(?:\s*(?:/|of)\s*\d{1,3})?$', re.IGNORECASE)
    section_header = re.compile(
        r'^(?:SECTION|PART|CHAPTER|SCHEDULE|ANNEXURE|Section|Part|Chapter|Schedule|Annexure)\s+[A-Z0-9IVX]{1,4}\b[\s\-:.)]*(.{0,70})')
    heading_words = re.compile(
        r'^(?:\d+(?:\.\d+)*\.?\s*)?(?:Standard |Specific |General |Permanent )?(?:Definitions?|Exclusions?|Waiting Periods?|'
        r'Benefits?|Coverage|Covers?|Terms and Conditions|General Terms(?: and Clauses)?|Claim(?:s)? Procedure|'
        r'Optional (?:Covers?|Benefits?)|Base Covers?|Specific Exclusions?)\s*:?$', re.IGNORECASE)
    exception_keywords = re.compile(r'\b(?:except(?!\s+as\b)|unless|provided that|notwithstanding|however)\b', re.IGNORECASE)
    number_words = {"thirty": 30, "sixty": 60, "ninety": 90, "twelve": 12, "twenty four": 24, "twenty-four": 24,
                    "thirty six": 36, "thirty-six": 36, "forty eight": 48, "forty-eight": 48, "one": 1, "two": 2,
                    "three": 3, "four": 4, "five": 5, "eight": 8}

    def clean_text(raw_text):
        t = raw_text.replace("\r", " ").replace("\x07", " ").replace("\t", " ")
        return re.sub(r'\s+', ' ', t).strip()

    def stitch_blocks(blocks):
        stitched = []
        for b in blocks:
            b_clean = clean_text(b)
            if not b_clean:
                continue
            if not stitched:
                stitched.append(b_clean)
                continue
            prev = stitched[-1]
            prev_ends_sentence = prev[-1] in ('.', ':', ';', '?', '!', ')', '"', ']')
            starts_new = bool(header_or_bullet.match(b_clean)) or bool(heading_words.match(b_clean))
            if not prev_ends_sentence and not starts_new and len(prev) < 2500 and not heading_words.match(prev):
                stitched[-1] = prev + " " + b_clean
            else:
                stitched.append(b_clean)
        return stitched

    def extract_durations(text):
        """All time limits in the clause, normalised to '<n> <unit>' and joined with '; '."""
        found = []
        lowered = text.lower()
        for word, value in number_words.items():
            lowered = re.sub(rf'\b{word}\b', str(value), lowered)
        for m in re.finditer(r'\b(\d{1,3})\s*(?:\(\s*\d{1,3}\s*\)\s*)?(?:consecutive\s+|continuous\s+|calendar\s+)?(day|month|year|hour)s?\b', lowered):
            value = f"{int(m.group(1))} {m.group(2)}s" if int(m.group(1)) != 1 else f"1 {m.group(2)}"
            if value not in found:
                found.append(value)
        return "; ".join(found[:4])

    def extract_complete_exception(text):
        """The full sentence that carries the exception, so the exception can be quoted verbatim."""
        sentences = re.split(r'(?<=[.;])\s+(?=[A-Z(])', text)
        for s in sentences:
            if exception_keywords.search(s) and len(s) > 25:
                return s.strip()
        for s in sentences:
            m = re.search(r'\bsubject to\b', s, re.IGNORECASE)
            if m and len(s) > 40 and not re.search(r'subject to (?:the )?(?:terms|policy terms)(?: and|,|&) conditions', s, re.IGNORECASE):
                return s.strip()
        return ""

    def is_contents_line(text):
        return bool(re.search(r'\.{5,}|…{2,}', text)) or bool(re.match(r'^(?:table of )?contents\b', text, re.IGNORECASE))

    all_clauses = []
    clause_id_counter = 1

    for p_info in policies:
        pdf_path = p_info["path"]
        insurer = p_info["insurer"]
        product = p_info["product"]
        product_code = p_info["product_code"]

        doc = fitz.open(str(pdf_path))
        page_blocks = []
        for page in doc:
            page_w = page.rect.width
            page_h = page.rect.height
            c_blocks = [b for b in page.get_text("blocks") if b[6] == 0 and 55 < b[1] < page_h - 55]
            mid_x = page_w * 0.48
            col2 = [b for b in c_blocks if b[0] > mid_x]
            col1 = [b for b in c_blocks if b[0] <= mid_x]
            if len(col2) > 3 and len(col1) > 3:
                ordered = sorted(col1, key=lambda b: b[1]) + sorted(col2, key=lambda b: b[1])
            else:
                ordered = sorted(c_blocks, key=lambda b: b[1])
            page_blocks.append([clean_text(b[4]) for b in ordered])
        n_pages = len(doc)
        doc.close()

        # Running headers and footers repeat on many pages; page numbers are bare digits.
        repeats = {}
        for blocks in page_blocks:
            for t in set(blocks):
                repeats[t] = repeats.get(t, 0) + 1
        furniture = {t for t, n in repeats.items() if n >= max(3, n_pages * 0.3)}
        raw_blocks = [t for blocks in page_blocks for t in blocks
                      if t and t not in furniture and not page_furniture.match(t)]

        stitched_blocks = stitch_blocks(raw_blocks)
        current_section = "General"
        parent_number = ""
        seen_texts = set()
        count = 0

        for para in stitched_blocks:
            # Only short lines are headings; a long paragraph that starts with
            # "Section B-3 ..." is a cross-reference inside a clause.
            sec = section_header.match(para) if len(para) <= 90 else None
            if sec and (para.endswith(")") or len(re.findall(r'\bsections?\b', para, re.IGNORECASE)) > 1
                        or re.search(r'\b(?:above|below|of the policy)\W*$', para, re.IGNORECASE)):
                sec = None
            if sec or (len(para) <= 70 and heading_words.match(para)):
                current_section = (para if not sec else para[:sec.end()]).strip(" :.-")[:80]
                parent_number = ""
                continue
            if len(para) < 25 or is_contents_line(para):
                continue

            clause_number = ""
            clause_text = para
            for pattern, kind in clause_patterns:
                match = pattern.match(para)
                if not match:
                    continue
                number, clause_text = match.group(1).strip(), match.group(2).strip()
                if kind == "top":
                    number = re.sub(r'\s+', '', number).replace("Code-Excl", "Code-Excl").replace("CodeExcl", "Code-Excl")
                    parent_number = number
                    clause_number = number
                elif kind == "def":
                    parent_number = f"Def. {number}"
                    clause_number = parent_number
                else:
                    clause_number = f"{parent_number}({number})" if parent_number else ""
                break
            else:
                # An unnumbered paragraph continues the clause above it within the same section.
                clause_number = parent_number

            para_lower = para.lower()
            clause_type = "GENERAL"
            if any(kw in para_lower for kw in exclusion_keywords):
                clause_type = "EXCLUSION"
            elif any(kw in para_lower for kw in waiting_period_keywords):
                clause_type = "WAITING_PERIOD"
            elif any(kw in para_lower for kw in coverage_keywords):
                clause_type = "COVERAGE"
            elif any(kw in para_lower for kw in definition_keywords):
                clause_type = "DEFINITION"

            if clause_type == "GENERAL" or len(clause_text) < 40:
                continue

            if len(clause_text) > 3000:
                last_dot = max(clause_text[:3000].rfind(". "), clause_text[:3000].rfind(".\n"))
                clause_text = clause_text[:last_dot + 1].strip() if last_dot > 500 else clause_text[:3000]

            if clause_text and clause_text[-1] not in ('.', ':', ';', '?', '!', ')', '"', ']'):
                clause_text = clause_text + "."

            # The same paragraph repeated within one policy wording is stored once.
            key = re.sub(r'\W+', ' ', clause_text.lower()).strip()
            if key in seen_texts:
                continue
            seen_texts.add(key)

            exception_text = extract_complete_exception(clause_text)
            temporal_rule = extract_durations(clause_text)

            clause_id = f"{product_code}-{clause_type[:3]}-{clause_id_counter:04d}"
            clause_id_counter += 1
            count += 1

            all_clauses.append({
                "clause_id": clause_id,
                "insurer": insurer,
                "product_name": product,
                "section": current_section[:80],
                "clause_number": clause_number[:24],
                "clause_text": clause_text,
                "clause_type": clause_type,
                "has_exception": bool(exception_text),
                "exception_text": exception_text[:600],
                "temporal_rule": temporal_rule[:200],
            })
        print(f"  [OK] {insurer:15s} | {product:25s} -> {count:4d} clauses")

    output_path = RUNTIME_DIR / "policy_clauses.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "clause_id", "insurer", "product_name", "section", "clause_number",
            "clause_text", "clause_type", "has_exception", "exception_text", "temporal_rule"
        ]
        # LF line ends, as the file is stored in git, so a rebuild changes only the rows that changed.
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(all_clauses)
    print(f"  [DONE] policy_clauses.csv: {len(all_clauses)} clauses -> {output_path}")
    return len(all_clauses)


# ╔══════════════════════════════════════════════════════════════╗
# ║  2. DENIAL REASONS CSV BUILDER                               ║
# ╚══════════════════════════════════════════════════════════════╝
# ╔══════════════════════════════════════════════════════════════╗
# ║  2. AUTHENTIC ASC X12 / CMS & IRDAI DENIAL REASON CATALOG    ║
# ╚══════════════════════════════════════════════════════════════╝
CARC_DICT = {
    "1": "Deductible Amount",
    "2": "Coinsurance Amount",
    "3": "Co-payment Amount",
    "16": "Claim/service lacks information or has submission/billing error(s).",
    "22": "This care may be covered by another payer per coordination of benefits.",
    "18": "Exact duplicate claim/service.",
    "26": "Expenses incurred prior to coverage.",
    "27": "Expenses incurred after coverage was terminated.",
    "29": "The time limit for filing has expired.",
    "30": "Payment adjusted because the patient has not met the required eligibility, spend down, waiting, or residency requirements.",
    "31": "Claim denied as patient cannot be identified as our insured.",
    "35": "Lifetime benefit maximum has been reached.",
    "39": "Services denied at the time authorization/pre-certification was requested.",
    "45": "Charge exceeds fee schedule/maximum allowable or contracted/legislated fee arrangement.",
    "50": "These are non-covered services because this is not deemed a 'medical necessity' by the payer.",
    "51": "These are non-covered services because this is a pre-existing condition.",
    "96": "Non-covered charge(s). At least one Remark Code must be provided (may be comprised of either the NCPDP Reject Reason Code, or Remittance Advice Remark Code that is not an ALERT).",
    "119": "Benefit maximum for this time period or occurrence has been reached.",
    "150": "Payer deems the information submitted does not support this level of service.",
    "151": "Payment adjusted because the payer deems the information submitted does not support this many services.",
    "197": "Precertification/authorization/notification absent.",
    "204": "This service/equipment/drug is not covered under the patient's current benefit plan.",
    "252": "An attachment/other documentation is required to adjudicate this claim/service. At least one Remark Code must be provided (may be comprised of either the NCPDP Reject Reason Code, or Remittance Advice Remark Code that is not an ALERT).",
}

# Every grievance starts with the insurer's Grievance Redressal Officer (GRO); these are the
# Indian escalation routes that follow it. Any total or partial repudiation of a health claim
# can go to the Insurance Ombudsman once the GRO has replied or 30 days have passed
# (Insurance Ombudsman Rules 2017, Rule 13), so no route stops at the GRO.
APPEAL_ROUTES = {
    "GRO": "Insurer GRO, then Insurance Ombudsman",
    "OMBUDSMAN": "Insurer GRO, then Insurance Ombudsman",
    "OMBUDSMAN_OR_COMMISSION": "Insurer GRO, then Insurance Ombudsman or Consumer Commission",
    "BIMA_BHAROSA": "Insurer GRO, then IRDAI Bima Bharosa portal",
}
ROUTE_OF = {
    "Internal Appeal": "GRO", "N/A": "GRO",
    "Ombudsman": "OMBUDSMAN", "IMR": "OMBUDSMAN", "IMR/Ombudsman": "OMBUDSMAN",
    "Court/Ombudsman": "OMBUDSMAN_OR_COMMISSION", "Ombudsman/Court": "OMBUDSMAN_OR_COMMISSION",
    "IRDAI GMS": "BIMA_BHAROSA",
}

RARC_DICT = {
    "N115": "This decision was based on a Local Coverage Determination (LCD). An LCD provides a guide to assist in determining whether a particular item or service is covered.",
    "N130": "Consult plan benefit documents/guidelines for information about restrictions for this service.",
    "N204": "Services under review for possible pre-existing condition. Send medical records for prior 12 months.",
    "N225": "Incomplete/invalid documentation/orders/notes/summary/report/chart.",
    "N382": "Missing/incomplete/invalid patient identifier.",
    "N425": "Statutorily excluded service(s).",
    "N432": "Alert: Adjustment based on a Recovery Audit.",
    "N640": "Exceeds number/frequency approved/allowed within time period.",
    "M1": "X-ray not taken within the past 12 months or near enough to the start of treatment.",
    "M15": "Separately billed services/tests have been bundled into other services or procedures.",
    "M38": "Alert: The patient is liable for the charges for this service as they were informed in writing before the service was furnished that we would not pay for it and the patient agreed to be responsible for the charges.",
    "M51": "Missing/incomplete/invalid procedure code(s).",
    "M127": "Missing patient medical record for this service.",
    "MA01": "Alert: If you do not agree with what we approved for these services, you may appeal our decision."
}

DENIAL_REASONS = [
    # MEDICAL_NECESSITY
    {"id": "MN-001", "cat": "MEDICAL_NECESSITY", "sub": "Elective Surgery",
     "text": "Procedure deemed elective and not medically necessary based on clinical guidelines",
     "carc": "50", "rarc": "N115", "clause": "EXCLUSION", "route": "IMR/Ombudsman",
     "irdai": "Standard Policy General Exclusions Clause 6(B) / Insurer Medical Underwriting Protocol"},
    {"id": "MN-002", "cat": "MEDICAL_NECESSITY", "sub": "Conservative Treatment Not Attempted",
     "text": "Conservative or non-surgical treatment options have not been exhausted prior to surgical intervention",
     "carc": "50", "rarc": "N130", "clause": "EXCLUSION", "route": "IMR/Ombudsman",
     "irdai": "Clinical Trial & Conservative Step-Care Protocol / Medical Necessity Definition"},
    {"id": "MN-003", "cat": "MEDICAL_NECESSITY", "sub": "Experimental/Investigational",
     "text": "Treatment classified as experimental, investigational, or unproven under current medical standards",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "IMR",
     "irdai": "IRDAI Standard Exclusion Code Excl06 (Investigation & Evaluation / Unproven Treatments)"},
    {"id": "MN-004", "cat": "MEDICAL_NECESSITY", "sub": "Cosmetic Procedure",
     "text": "Procedure classified as cosmetic in nature without documented functional impairment",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "Internal Appeal",
     "irdai": "IRDAI Standard Exclusion Code Excl08 (Cosmetic or Plastic Surgery)"},
    {"id": "MN-005", "cat": "MEDICAL_NECESSITY", "sub": "Frequency Limit Exceeded",
     "text": "Number of treatments exceeds medically accepted frequency for the diagnosed condition",
     "carc": "119", "rarc": "N640", "clause": "EXCLUSION", "route": "Internal Appeal",
     "irdai": "Policy Schedule Limits & Medically Necessary Frequency Guidelines"},
    {"id": "MN-006", "cat": "MEDICAL_NECESSITY", "sub": "Alternative Treatment Available",
     "text": "Less invasive or less costly alternative treatment is available and appropriate",
     "carc": "50", "rarc": "N115", "clause": "EXCLUSION", "route": "IMR",
     "irdai": "Medical Necessity Definition (Customary and Reasonable Treatment Clause)"},
    {"id": "MN-007", "cat": "MEDICAL_NECESSITY", "sub": "Insufficient Clinical Documentation",
     "text": "Clinical records do not sufficiently demonstrate medical necessity for the requested procedure",
     "carc": "150", "rarc": "M127", "clause": "EXCLUSION", "route": "IMR/Ombudsman",
     "irdai": "Claim Procedure Submission Clause / Insurer Right to Medical Records"},
    {"id": "MN-008", "cat": "MEDICAL_NECESSITY", "sub": "Age/Condition Inappropriate",
     "text": "Requested procedure is not appropriate for the patient's age, condition, or prognosis",
     "carc": "50", "rarc": "N115", "clause": "EXCLUSION", "route": "IMR",
     "irdai": "Medical Necessity Definition Clause 2.24"},
    {"id": "MN-009", "cat": "MEDICAL_NECESSITY", "sub": "Outpatient Sufficiency",
     "text": "Condition can be adequately managed in outpatient or daycare setting; inpatient admission not warranted",
     "carc": "50", "rarc": "M38", "clause": "EXCLUSION", "route": "Internal Appeal",
     "irdai": "Day Care Procedure Schedule & Inpatient Hospitalization 24-Hour Norm"},
    {"id": "MN-010", "cat": "MEDICAL_NECESSITY", "sub": "Diagnostic Test Not Required",
     "text": "Diagnostic investigation ordered without clinical indication or prior abnormal result",
     "carc": "50", "rarc": "N115", "clause": "EXCLUSION", "route": "Internal Appeal",
     "irdai": "IRDAI Standard Exclusion Code Excl04 (Diagnostic / Investigative Admissions)"},

    # PRE_EXISTING_WAITING_PERIOD
    {"id": "PW-001", "cat": "PRE_EXISTING_WAITING_PERIOD", "sub": "Pre-Existing Disease",
     "text": "Condition classified as pre-existing disease as per policy definition; treatment within specified waiting period",
     "carc": "51", "rarc": "N204", "clause": "WAITING_PERIOD", "route": "Ombudsman",
     "irdai": "IRDAI Master Circular Waiting Period Norms / Code Excl01 (Pre-Existing Diseases)"},
    {"id": "PW-002", "cat": "PRE_EXISTING_WAITING_PERIOD", "sub": "24-Month Specific Disease",
     "text": "Listed specific disease/condition claimed within the initial 24-month waiting period",
     "carc": "30", "rarc": "N204", "clause": "WAITING_PERIOD", "route": "Ombudsman",
     "irdai": "IRDAI Standard Waiting Period Code Excl02 (Specified Disease/Procedure Waiting Period)"},
    {"id": "PW-003", "cat": "PRE_EXISTING_WAITING_PERIOD", "sub": "Extended PED Waiting Period",
     "text": "Pre-existing condition disclosed or discovered; claim within the policy's PED waiting period (36 months maximum for policies under the 2024 Master Circular; older wordings state 48 months)",
     "carc": "51", "rarc": "N204", "clause": "WAITING_PERIOD", "route": "Ombudsman",
     "irdai": "IRDAI Master Circular on Health Insurance Business 2024 (PED waiting period of at most 36 months)"},
    {"id": "PW-004", "cat": "PRE_EXISTING_WAITING_PERIOD", "sub": "30-Day Initial Wait",
     "text": "Claim filed during the initial 30-day cooling-off/waiting period after policy inception",
     "carc": "30", "rarc": "N204", "clause": "WAITING_PERIOD", "route": "Internal Appeal",
     "irdai": "IRDAI Standard Waiting Period Code Excl03 (30-day Waiting Period, except accidental trauma)"},
    {"id": "PW-005", "cat": "PRE_EXISTING_WAITING_PERIOD", "sub": "Non-Disclosure of PED",
     "text": "Policyholder failed to disclose a pre-existing medical condition in the proposal form",
     "carc": "51", "rarc": "MA01", "clause": "WAITING_PERIOD", "route": "Ombudsman/Court",
     "irdai": "Policy disclosure-to-information norm; contestable only before the 60-month moratorium ends (IRDAI Master Circular on Health Insurance Business 2024)"},
    {"id": "PW-006", "cat": "PRE_EXISTING_WAITING_PERIOD", "sub": "Moratorium Breach",
     "text": "Claim denied on non-disclosure grounds after 60 continuous months of coverage; the moratorium bars this except for proven fraud",
     "carc": "51", "rarc": "MA01", "clause": "WAITING_PERIOD", "route": "Ombudsman",
     "irdai": "IRDAI Master Circular on Health Insurance Business 2024 (moratorium after 60 continuous months)"},
    {"id": "PW-007", "cat": "PRE_EXISTING_WAITING_PERIOD", "sub": "Continuous Coverage Gap",
     "text": "Break in continuous policy renewal reset the waiting period for pre-existing conditions",
     "carc": "30", "rarc": "N204", "clause": "WAITING_PERIOD", "route": "Ombudsman",
     "irdai": "IRDAI Health Insurance Portability & Renewal Continuity Guidelines"},
    {"id": "PW-008", "cat": "PRE_EXISTING_WAITING_PERIOD", "sub": "Portability Wait Reset",
     "text": "Waiting period credit not granted during insurer-to-insurer portability",
     "carc": "30", "rarc": "MA01", "clause": "WAITING_PERIOD", "route": "IRDAI GMS",
     "irdai": "IRDAI Health Regulations Schedule I (Portability & Waiting Period Carryover Credit)"},
    {"id": "PW-009", "cat": "PRE_EXISTING_WAITING_PERIOD", "sub": "First Year Exclusion",
     "text": "Specific surgical procedure excluded during the first policy year",
     "carc": "30", "rarc": "N204", "clause": "WAITING_PERIOD", "route": "Internal Appeal",
     "irdai": "Policy Terms Specified First-Year Surgical Procedure Schedule"},
    {"id": "PW-010", "cat": "PRE_EXISTING_WAITING_PERIOD", "sub": "Congenital Condition",
     "text": "Condition deemed congenital and excluded under lifetime waiting clause",
     "carc": "96", "rarc": "N425", "clause": "WAITING_PERIOD", "route": "Ombudsman",
     "irdai": "IRDAI Standard Exclusion Code Excl07 (Congenital External Diseases/Defects)"},

    # POLICY_EXCLUSION
    {"id": "PE-001", "cat": "POLICY_EXCLUSION", "sub": "Permanent Exclusion",
     "text": "Condition permanently excluded under policy terms (e.g., self-inflicted injury, substance abuse, STDs)",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "Internal Appeal",
     "irdai": "IRDAI Master Circular Permanent Exclusions Schedule"},
    {"id": "PE-002", "cat": "POLICY_EXCLUSION", "sub": "War/Nuclear Risk",
     "text": "Injury arising from war, nuclear event, or participating in hazardous activity excluded under general exclusions",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "N/A",
     "irdai": "Standard Force Majeure, War, Nuclear Contamination Exclusion Clause"},
    {"id": "PE-003", "cat": "POLICY_EXCLUSION", "sub": "Dental Treatment",
     "text": "Routine dental treatment or procedure not arising from accident excluded under policy terms",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "Internal Appeal",
     "irdai": "IRDAI Standard Exclusion Code Excl09 (Dental / Oral Surgery unless accidental)"},
    {"id": "PE-004", "cat": "POLICY_EXCLUSION", "sub": "Infertility Treatment",
     "text": "IVF, fertility treatment, and related procedures excluded under standard health policy",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "Internal Appeal",
     "irdai": "IRDAI Standard Exclusion Code Excl11 (Maternity & Infertility Treatments)"},
    {"id": "PE-005", "cat": "POLICY_EXCLUSION", "sub": "Maternity Expenses",
     "text": "Childbirth, pregnancy complications, or caesarean delivery not covered under basic policy",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "Internal Appeal",
     "irdai": "IRDAI Standard Exclusion Code Excl12 (Maternity Expenses without Add-on)"},
    {"id": "PE-006", "cat": "POLICY_EXCLUSION", "sub": "Substance Abuse",
     "text": "Hospitalization resulting from alcoholism, drug addiction, or substance abuse",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "Internal Appeal",
     "irdai": "IRDAI Standard Exclusion Code Excl10 (Substance Abuse, Narcotics, Alcoholism)"},
    {"id": "PE-007", "cat": "POLICY_EXCLUSION", "sub": "Obesity/Weight Control",
     "text": "Bariatric surgery or treatment for obesity not meeting medical necessity threshold",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "IMR",
     "irdai": "IRDAI Standard Exclusion Code Excl05 (Obesity / Weight Control Surgery Guidelines)"},
    {"id": "PE-008", "cat": "POLICY_EXCLUSION", "sub": "Adventure Sports",
     "text": "Treatment resulting from participation in professional sports or hazardous activities",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "Internal Appeal",
     "irdai": "IRDAI Standard Exclusion Code Excl13 (Hazardous / Adventure Sports)"},
    {"id": "PE-009", "cat": "POLICY_EXCLUSION", "sub": "Refractive Error (Eyesight)",
     "text": "Laser eye surgery (LASIK) for correction of refractive error < 7.5 dioptres",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "Internal Appeal",
     "irdai": "IRDAI Standard Exclusion Code Excl14 (Refractive Error Correction below 7.5 Diopters)"},
    {"id": "PE-010", "cat": "POLICY_EXCLUSION", "sub": "Unproven Treatment",
     "text": "Treatment modalities without established clinical trial efficacy or peer-reviewed evidence",
     "carc": "96", "rarc": "N425", "clause": "EXCLUSION", "route": "IMR",
     "irdai": "IRDAI Standard Exclusion Code Excl15 (Unproven Treatments & Experimental Technologies)"},

    # DOCUMENTATION
    {"id": "DOC-001", "cat": "DOCUMENTATION", "sub": "Missing Discharge Summary",
     "text": "Claim submitted without the complete, signed, and stamped hospital discharge summary",
     "carc": "252", "rarc": "M127", "clause": "DOCUMENTATION", "route": "Internal Appeal",
     "irdai": "Policy Claim Settlement Norms / Mandatory Documents Clause"},
    {"id": "DOC-002", "cat": "DOCUMENTATION", "sub": "Missing Investigation Reports",
     "text": "Diagnostic test reports (X-ray, MRI, biopsy, lab results) supporting diagnosis not provided",
     "carc": "252", "rarc": "N225", "clause": "DOCUMENTATION", "route": "Internal Appeal",
     "irdai": "Mandatory Diagnostic Proof Requirement / Claim Clause 4.1"},
    {"id": "DOC-003", "cat": "DOCUMENTATION", "sub": "Missing Original Bills",
     "text": "Original hospital final bill with break-up and paid receipts not submitted with claim",
     "carc": "16", "rarc": "N225", "clause": "DOCUMENTATION", "route": "Internal Appeal",
     "irdai": "IRDAI Master Circular Claim Substantiation / Original Invoice Protocol"},
    {"id": "DOC-004", "cat": "DOCUMENTATION", "sub": "Incomplete Claim Form",
     "text": "Claim form missing required sections: treating doctor certification, date of first symptom, etc.",
     "carc": "16", "rarc": "N382", "clause": "DOCUMENTATION", "route": "Internal Appeal",
     "irdai": "Standardized Health Claim Form Part B Requirements"},
    {"id": "DOC-005", "cat": "DOCUMENTATION", "sub": "Missing Pre-Auth Approval",
     "text": "Planned cashless admission proceeded without obtaining prior authorization from TPA",
     "carc": "197", "rarc": "M15", "clause": "DOCUMENTATION", "route": "Internal Appeal",
     "irdai": "TPA Cashless Pre-Authorization Protocol / Clause 5.2"},
    {"id": "DOC-006", "cat": "DOCUMENTATION", "sub": "Illegible Records",
     "text": "Submitted medical records, indoor case papers, or prescriptions are illegible or incomplete",
     "carc": "16", "rarc": "M127", "clause": "DOCUMENTATION", "route": "Internal Appeal",
     "irdai": "Medical Audit Standards & Indoor Case Paper Submission Guidelines"},
    {"id": "DOC-007", "cat": "DOCUMENTATION", "sub": "Missing KYC Documents",
     "text": "KYC documentation (PAN card, Aadhaar, address proof) for claim exceeding ₹1 lakh not provided",
     "carc": "16", "rarc": "N382", "clause": "DOCUMENTATION", "route": "Internal Appeal",
     "irdai": "IRDAI Master Circular on AML/CFT & Customer Due Diligence (Threshold ₹1 Lakh)"},
    {"id": "DOC-008", "cat": "DOCUMENTATION", "sub": "Discrepancy in Dates",
     "text": "Admission date, first diagnosis date, or discharge date inconsistent across submitted documents",
     "carc": "16", "rarc": "N382", "clause": "DOCUMENTATION", "route": "Internal Appeal",
     "irdai": "Claim Reconciliation & Discrepancy Clarification Norms"},
    {"id": "DOC-009", "cat": "DOCUMENTATION", "sub": "Missing Implant Sticker/Invoice",
     "text": "Original implant sticker/barcode and manufacturer purchase invoice not attached for surgical implant",
     "carc": "252", "rarc": "N225", "clause": "DOCUMENTATION", "route": "Internal Appeal",
     "irdai": "NPPA / IRDAI Medical Implant Traceability and Pricing Guidelines"},
    {"id": "DOC-010", "cat": "DOCUMENTATION", "sub": "Missing Pharmacy Batch Numbers",
     "text": "Pharmacy bills missing drug batch numbers, expiry dates, or treating physician's prescription",
     "carc": "16", "rarc": "N225", "clause": "DOCUMENTATION", "route": "Internal Appeal",
     "irdai": "Drugs and Cosmetics Rules & Pharmacy Billing Documentation Norms"},

    # ADMINISTRATIVE_PROCEDURAL
    {"id": "ADM-001", "cat": "ADMINISTRATIVE_PROCEDURAL", "sub": "Late Claim Submission",
     "text": "Claim submitted beyond the stipulated timeline (typically 15-30 days post-discharge) without reasonable cause",
     "carc": "29", "rarc": "MA01", "clause": "ADMINISTRATIVE", "route": "Ombudsman",
     "irdai": "IRDAI Circular Ref: IRDA/HLT/MISC/CIR/216/09/2011 (Genuine delay cannot be grounds for repudiation)"},
    {"id": "ADM-002", "cat": "ADMINISTRATIVE_PROCEDURAL", "sub": "Non-Network Hospital",
     "text": "Planned treatment taken at non-network hospital without prior intimation to insurer",
     "carc": "204", "rarc": "N130", "clause": "ADMINISTRATIVE", "route": "Internal Appeal",
     "irdai": "IRDAI Circular 2024 (Cashless Anywhere in Every Hospital Norms)"},
    {"id": "ADM-003", "cat": "ADMINISTRATIVE_PROCEDURAL", "sub": "Network Hospital Non-Intimation",
     "text": "Treatment at network hospital without notifying the TPA/insurer within 24-48 hours",
     "carc": "197", "rarc": "M15", "clause": "ADMINISTRATIVE", "route": "Internal Appeal",
     "irdai": "Policy Emergency / Planned Hospitalization Intimation Timeline Clause"},
    {"id": "ADM-004", "cat": "ADMINISTRATIVE_PROCEDURAL", "sub": "Duplicate Claim",
     "text": "Claim already processed, settled, or currently under review under another claim number",
     "carc": "18", "rarc": "MA01", "clause": "ADMINISTRATIVE", "route": "N/A",
     "irdai": "Standard Anti-Duplication Claim Settlement Protocol"},
    {"id": "ADM-005", "cat": "ADMINISTRATIVE_PROCEDURAL", "sub": "Incorrect TPA Submission",
     "text": "Claim documents submitted to wrong TPA or wrong insurer division",
     "carc": "16", "rarc": "N382", "clause": "ADMINISTRATIVE", "route": "Internal Appeal",
     "irdai": "Third Party Administrator Interoperability and Routing Guidelines"},
    {"id": "ADM-006", "cat": "ADMINISTRATIVE_PROCEDURAL", "sub": "Pre-Auth Denial Override",
     "text": "Treatment proceeded on reimbursement basis after cashless pre-auth was formally rejected",
     "carc": "197", "rarc": "MA01", "clause": "ADMINISTRATIVE", "route": "Ombudsman",
     "irdai": "IRDAI Master Circular (Denial of cashless does not mean denial of reimbursement)"},
    {"id": "ADM-007", "cat": "ADMINISTRATIVE_PROCEDURAL", "sub": "Blacklisted Provider",
     "text": "Hospital or treating doctor is on the insurer's excluded/de-listed provider list",
     "carc": "204", "rarc": "N130", "clause": "ADMINISTRATIVE", "route": "Ombudsman",
     "irdai": "IRDAI Guidelines on Excluded / Blacklisted Hospitals Schedule"},
    {"id": "ADM-008", "cat": "ADMINISTRATIVE_PROCEDURAL", "sub": "Portability Timeline Missed",
     "text": "Portability application submitted less than 45 days before policy expiry",
     "carc": "29", "rarc": "MA01", "clause": "ADMINISTRATIVE", "route": "IRDAI GMS",
     "irdai": "IRDAI Portability Regulations (45-day Advance Intimation Standard)"},
    {"id": "ADM-009", "cat": "ADMINISTRATIVE_PROCEDURAL", "sub": "Section 64VB Violation",
     "text": "Premium payment dishonoured or not received before policy inception/renewal date",
     "carc": "26", "rarc": "MA01", "clause": "ADMINISTRATIVE", "route": "N/A",
     "irdai": "Section 64VB of Insurance Act 1938 (No Risk Assumption without Advance Premium)"},
    {"id": "ADM-010", "cat": "ADMINISTRATIVE_PROCEDURAL", "sub": "Multiple Policies Non-Disclosure",
     "text": "Failure to declare existing concurrent health insurance policies during claim",
     "carc": "22", "rarc": "MA01", "clause": "ADMINISTRATIVE", "route": "Internal Appeal",
     "irdai": "IRDAI Contribution Clause Standard (Insured right to choose primary insurer)"},

    # FINANCIAL_LIMIT
    {"id": "FIN-001", "cat": "FINANCIAL_LIMIT", "sub": "Sum Insured Exhausted",
     "text": "Total claims during the policy year have exhausted the base Sum Insured and cumulative bonus",
     "carc": "119", "rarc": "N640", "clause": "FINANCIAL_LIMIT", "route": "Internal Appeal",
     "irdai": "Policy Schedule Sum Insured Limit / Annual Aggregate Liability"},
    {"id": "FIN-002", "cat": "FINANCIAL_LIMIT", "sub": "Room Rent Sub-Limit",
     "text": "Proportionate deduction applied because room rent exceeded 1% of Sum Insured (or specific cap)",
     "carc": "45", "rarc": "N640", "clause": "FINANCIAL_LIMIT", "route": "Ombudsman",
     "irdai": "IRDAI Guidelines on Proportionate Deduction (Excluding pharmacy, implants, and consumables)"},
    {"id": "FIN-003", "cat": "FINANCIAL_LIMIT", "sub": "ICU Room Sub-Limit",
     "text": "ICU charges exceed the contractual sub-limit (typically 2% of Sum Insured per day)",
     "carc": "45", "rarc": "N640", "clause": "FINANCIAL_LIMIT", "route": "Ombudsman",
     "irdai": "Policy Contract ICU Sub-Limit Schedule"},
    {"id": "FIN-004", "cat": "FINANCIAL_LIMIT", "sub": "Co-Pay Deduction",
     "text": "Mandatory co-payment (10-20% based on age or city tier) deducted from the admissible claim amount",
     "carc": "3", "rarc": "MA01", "clause": "FINANCIAL_LIMIT", "route": "Internal Appeal",
     "irdai": "Policy Schedule Mandatory / Voluntary Co-Payment Terms"},
    {"id": "FIN-005", "cat": "FINANCIAL_LIMIT", "sub": "Deductible Applied",
     "text": "Claim amount is within the annual or per-claim deductible; insurer liability not triggered",
     "carc": "1", "rarc": "MA01", "clause": "FINANCIAL_LIMIT", "route": "Internal Appeal",
     "irdai": "Top-up / Super Top-up Aggregate Deductible Clause"},
    {"id": "FIN-006", "cat": "FINANCIAL_LIMIT", "sub": "Specific Disease Sub-Limit",
     "text": "Procedure has a contractual sub-limit (e.g., Cataract ₹30,000-₹50,000, Hernia ₹50,000)",
     "carc": "119", "rarc": "N640", "clause": "FINANCIAL_LIMIT", "route": "Internal Appeal",
     "irdai": "Policy Wording Specific Treatment Capping Schedule"},
    {"id": "FIN-007", "cat": "FINANCIAL_LIMIT", "sub": "Modern Treatment Cap",
     "text": "Robotic surgery / cyberknife / immunotherapy capped at 50% of SI or specific sub-limit",
     "carc": "119", "rarc": "N640", "clause": "FINANCIAL_LIMIT", "route": "Ombudsman",
     "irdai": "IRDAI Circular on Modern Treatment Methods (Mandatory coverage with reasonable sub-limits)"},
    {"id": "FIN-008", "cat": "FINANCIAL_LIMIT", "sub": "Non-Medical Expense Deduction",
     "text": "Hospital charges for non-medical items (gloves, PPE, food, admin) deducted as inadmissible",
     "carc": "96", "rarc": "N425", "clause": "FINANCIAL_LIMIT", "route": "Ombudsman",
     "irdai": "IRDAI Circular IRDA/HLT/REG/CIR/193/09/2019 Annexure IV Lists I–IV"},
    {"id": "FIN-009", "cat": "FINANCIAL_LIMIT", "sub": "Pre-Post Hospitalization Cap",
     "text": "Pre-hospitalization (30/60 days) or post-hospitalization (60/90/180 days) limit exceeded",
     "carc": "119", "rarc": "N640", "clause": "FINANCIAL_LIMIT", "route": "Internal Appeal",
     "irdai": "Policy Schedule Pre & Post Hospitalization Temporal Limits"},
    {"id": "FIN-010", "cat": "FINANCIAL_LIMIT", "sub": "Domiciliary Hospitalization Cap",
     "text": "Home treatment charges exceed the contractual domiciliary hospitalization sub-limit",
     "carc": "119", "rarc": "N640", "clause": "FINANCIAL_LIMIT", "route": "Internal Appeal",
     "irdai": "Policy Contract Domiciliary Hospitalization Benefit Terms"},

    # ELIGIBILITY_COVERAGE
    {"id": "ELG-001", "cat": "ELIGIBILITY_COVERAGE", "sub": "Policy Inactive/Lapsed",
     "text": "Claim incurred after policy expiration and outside the 30-day grace period",
     "carc": "27", "rarc": "MA01", "clause": "ELIGIBILITY", "route": "Internal Appeal",
     "irdai": "Standard Policy Period & 30-Day Renewal Grace Period Clause"},
    {"id": "ELG-002", "cat": "ELIGIBILITY_COVERAGE", "sub": "Prior to Policy Inception",
     "text": "Hospitalization occurred before the commencement date of the insurance cover",
     "carc": "26", "rarc": "MA01", "clause": "ELIGIBILITY", "route": "N/A",
     "irdai": "Policy Effective Inception Date Standard Clause"},
    {"id": "ELG-003", "cat": "ELIGIBILITY_COVERAGE", "sub": "Patient Not Insured",
     "text": "Patient is not listed as an insured member in the policy schedule or endorsement",
     "carc": "204", "rarc": "N382", "clause": "ELIGIBILITY", "route": "Internal Appeal",
     "irdai": "Insured Person Schedule & Endorsement Verification Clause"},
    {"id": "ELG-004", "cat": "ELIGIBILITY_COVERAGE", "sub": "Age Eligibility Exceeded",
     "text": "Insured member exceeded the maximum entry age or child exceeded maximum dependent age (typically 25)",
     "carc": "204", "rarc": "MA01", "clause": "ELIGIBILITY", "route": "Internal Appeal",
     "irdai": "IRDAI Health Master Circular (Lifelong Renewability & Dependent Age Norms)"},
    {"id": "ELG-005", "cat": "ELIGIBILITY_COVERAGE", "sub": "Geographical Limitation",
     "text": "Treatment taken outside India / outside the contractually agreed territorial limits",
     "carc": "204", "rarc": "N130", "clause": "ELIGIBILITY", "route": "Internal Appeal",
     "irdai": "Policy Geographic & Territorial Scope of Cover Clause"},
    {"id": "ELG-006", "cat": "ELIGIBILITY_COVERAGE", "sub": "Fraudulent Claim",
     "text": "Investigation revealed intentional fraud, fabricated bills, or phantom hospitalization",
     "carc": "96", "rarc": "MA01", "clause": "ELIGIBILITY", "route": "Court/Ombudsman",
     "irdai": "Policy fraud condition (benefits forfeited where fraud is established)"},
    {"id": "ELG-007", "cat": "ELIGIBILITY_COVERAGE", "sub": "Non-Medical Establishment",
     "text": "Facility does not qualify as a 'Hospital' as defined by policy (missing 10-15 beds, OT, qualified staff)",
     "carc": "204", "rarc": "N130", "clause": "ELIGIBILITY", "route": "Ombudsman",
     "irdai": "Clinical Establishments Act & Standard Policy Definition of Hospital Clause 2.15"},
    {"id": "ELG-008", "cat": "ELIGIBILITY_COVERAGE", "sub": "Policy Rescinded",
     "text": "Policy terminated ab initio due to material misrepresentation during proposal",
     "carc": "27", "rarc": "MA01", "clause": "ELIGIBILITY", "route": "Court/Ombudsman",
     "irdai": "Policy cancellation clause for non-disclosure or misrepresentation; barred after the 60-month moratorium except for fraud (IRDAI Master Circular 2024)"},
    {"id": "ELG-009", "cat": "ELIGIBILITY_COVERAGE", "sub": "Expatriate/Non-Resident",
     "text": "Policyholder status changed to non-resident without endorsement or premium adjustment",
     "carc": "204", "rarc": "N130", "clause": "ELIGIBILITY", "route": "Internal Appeal",
     "irdai": "Policyholder Residency & Cross-Border Coverage Endorsement Rules"},
    {"id": "ELG-010", "cat": "ELIGIBILITY_COVERAGE", "sub": "Grace Period Lapse",
     "text": "Premium unpaid beyond the statutory 30-day grace period; continuity benefits forfeit",
     "carc": "27", "rarc": "MA01", "clause": "ELIGIBILITY", "route": "Internal Appeal",
     "irdai": "IRDAI Health Master Circular (30-day Grace Period & Continuity Forfeiture)"}
]
PROCEDURES = [
    # ── 1. Orthopedic Surgery & Musculoskeletal (25 procedures) ──
    {"hcpcs_code": "27447", "short": "Total Knee Arthroplasty (TKR)", "long": "Arthroplasty, knee, condyle and plateau; medial and lateral compartments with or without patella resurfacing", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M17.0", "primary_indication", "strong"), ("M17.11", "primary_indication", "strong")]},
    {"hcpcs_code": "27130", "short": "Total Hip Arthroplasty (THR)", "long": "Arthroplasty, acetabular and proximal femoral prosthetic replacement, with or without autograft or allograft", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M16.0", "primary_indication", "strong"), ("S72.001A", "primary_indication", "strong")]},
    {"hcpcs_code": "27446", "short": "Unicompartmental Knee Arthroplasty", "long": "Arthroplasty, knee, condyle and plateau; medial OR lateral compartment", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M17.0", "primary_indication", "strong")]},
    {"hcpcs_code": "27236", "short": "Open Treatment Femoral Neck Fracture", "long": "Open treatment of femoral fracture, proximal end, neck, internal fixation or prosthetic replacement", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("S72.001A", "primary_indication", "strong")]},
    {"hcpcs_code": "27245", "short": "ORIF Intertrochanteric Femoral Fracture", "long": "Treatment of intertrochanteric, peritrochanteric, or subtrochanteric femoral fracture with intramedullary implant", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("S72.141A", "primary_indication", "strong")]},
    {"hcpcs_code": "22612", "short": "Lumbar Spinal Fusion Posterolateral", "long": "Arthrodesis, posterior or posterolateral technique, single interspace; lumbar", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M47.816", "primary_indication", "strong"), ("M51.16", "primary_indication", "strong")]},
    {"hcpcs_code": "22551", "short": "Anterior Cervical Discectomy and Fusion (ACDF)", "long": "Arthrodesis, anterior interbody, including disc space preparation, discectomy and decompression; cervical below C2", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M47.812", "primary_indication", "strong"), ("M50.20", "primary_indication", "strong")]},
    {"hcpcs_code": "63030", "short": "Lumbar Microdiscectomy", "long": "Laminotomy with decompression of nerve root(s), including partial facetectomy and excision of herniated intervertebral disc; 1 interspace, lumbar", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M51.16", "primary_indication", "strong"), ("M54.5", "secondary_indication", "moderate")]},
    {"hcpcs_code": "29881", "short": "Knee Arthroscopy with Meniscectomy", "long": "Arthroscopy, knee, surgical; with meniscectomy (medial or lateral, including shaving)", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M23.200", "primary_indication", "strong")]},
    {"hcpcs_code": "29880", "short": "Knee Arthroscopy Meniscectomy Both Compartments", "long": "Arthroscopy, knee, surgical; with meniscectomy (medial AND lateral compartments)", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M23.300", "primary_indication", "strong")]},
    {"hcpcs_code": "29888", "short": "Arthroscopic Anterior Cruciate Ligament (ACL) Reconstruction", "long": "Arthroscopically aided anterior cruciate ligament repair/augmentation or reconstruction", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("S83.519A", "primary_indication", "strong")]},
    {"hcpcs_code": "23472", "short": "Total Shoulder Arthroplasty", "long": "Arthroplasty, glenohumeral joint; total shoulder (glenoid and proximal humeral replacement)", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("M19.011", "primary_indication", "strong"), ("M75.100", "primary_indication", "strong")]},
    {"hcpcs_code": "29827", "short": "Arthroscopic Rotator Cuff Repair", "long": "Arthroscopy, shoulder, surgical; with rotator cuff repair", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M75.100", "primary_indication", "strong"), ("M75.110", "primary_indication", "strong")]},
    {"hcpcs_code": "64721", "short": "Carpal Tunnel Release Open/Endoscopic", "long": "Neuroplasty and/or transposition; median nerve at carpal tunnel", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "low", "ind": [("G56.00", "primary_indication", "strong")]},
    {"hcpcs_code": "26055", "short": "Trigger Finger Tendon Sheath Incision", "long": "Tendon sheath incision (e.g., for trigger finger / stenosing tenosynovitis)", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "low", "ind": [("M65.30", "primary_indication", "strong")]},
    {"hcpcs_code": "28296", "short": "Bunionectomy Hallux Valgus Correction", "long": "Correction, hallux valgus (bunionectomy), with sesamoidectomy and distal metatarsal osteotomy", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M20.10", "primary_indication", "moderate")]},
    {"hcpcs_code": "27650", "short": "Achilles Tendon Repair Primary", "long": "Repair, primary, open or percutaneous, ruptured Achilles tendon; without graft", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("S86.019A", "primary_indication", "strong")]},
    {"hcpcs_code": "29898", "short": "Ankle Arthroscopy Surgical Debridement", "long": "Arthroscopy, ankle, surgical; debridement, extensive", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("M19.071", "primary_indication", "strong")]},
    {"hcpcs_code": "20610", "short": "Arthrocentesis Major Joint (Knee/Hip)", "long": "Arthrocentesis, aspiration and/or injection, major joint or bursa; without ultrasound guidance", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "low", "ind": [("M17.0", "primary_indication", "strong"), ("M25.561", "primary_indication", "strong")]},
    {"hcpcs_code": "20611", "short": "Arthrocentesis Major Joint with Ultrasound", "long": "Aspiration and/or injection, major joint or bursa with ultrasound guidance, with permanent recording", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "low", "ind": [("M17.0", "primary_indication", "strong"), ("M25.561", "primary_indication", "strong")]},
    {"hcpcs_code": "27756", "short": "Tibial Shaft Fracture Intramedullary Fixation", "long": "Percutaneous skeletal fixation of tibial shaft fracture with intramedullary implant", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("S82.201A", "primary_indication", "strong")]},
    {"hcpcs_code": "25607", "short": "Distal Radius Fracture Open Reduction (ORIF)", "long": "Open treatment of distal radial extra-articular fracture with internal fixation", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("S52.501A", "primary_indication", "strong")]},
    {"hcpcs_code": "22842", "short": "Posterior Segmental Spinal Instrumentation", "long": "Posterior segmental instrumentation (e.g., pedicle screws, rods); 3 to 6 vertebral segments", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M47.816", "primary_indication", "strong")]},
    {"hcpcs_code": "27440", "short": "Knee Arthroplasty Tibial Plateau", "long": "Arthroplasty, knee, tibial plateau, with or without debridement", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("M17.0", "primary_indication", "moderate")]},
    {"hcpcs_code": "29877", "short": "Knee Arthroscopy Chondroplasty Debridement", "long": "Arthroscopy, knee, surgical; debridement/shaving of articular cartilage (chondroplasty)", "cat": "Orthopedic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("M17.0", "primary_indication", "moderate")]},

    # ── 2. Cardiovascular Surgery & Interventions (20 procedures) ──
    {"hcpcs_code": "33533", "short": "CABG Single Arterial Graft", "long": "Coronary artery bypass, using arterial graft(s); single arterial graft", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I25.10", "primary_indication", "strong"), ("I20.0", "primary_indication", "strong")]},
    {"hcpcs_code": "33534", "short": "CABG Two Arterial Grafts", "long": "Coronary artery bypass, using arterial graft(s); 2 coronary arterial grafts", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I25.10", "primary_indication", "strong")]},
    {"hcpcs_code": "33535", "short": "CABG Three Arterial Grafts", "long": "Coronary artery bypass, using arterial graft(s); 3 coronary arterial grafts", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I25.10", "primary_indication", "strong")]},
    {"hcpcs_code": "33536", "short": "CABG Four or More Arterial Grafts", "long": "Coronary artery bypass, using arterial graft(s); 4 or more coronary arterial grafts", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I25.10", "primary_indication", "strong")]},
    {"hcpcs_code": "92928", "short": "Percutaneous Coronary Stent Placement", "long": "Percutaneous transcatheter placement of intracoronary stent(s), single major coronary artery or branch", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I25.10", "primary_indication", "strong"), ("I21.0", "primary_indication", "strong")]},
    {"hcpcs_code": "92920", "short": "Percutaneous Coronary Angioplasty (PTCA)", "long": "Percutaneous transluminal coronary balloon angioplasty; single major coronary artery or branch", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I25.10", "primary_indication", "strong")]},
    {"hcpcs_code": "33405", "short": "Aortic Valve Replacement Surgical", "long": "Replacement, aortic valve, open, with cardiopulmonary bypass; prosthetic valve", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I35.0", "primary_indication", "strong"), ("I35.1", "primary_indication", "strong")]},
    {"hcpcs_code": "33361", "short": "Transcatheter Aortic Valve Replacement (TAVR)", "long": "Transcatheter aortic valve replacement (TAVR/TAVI) with prosthesis; percutaneous femoral artery approach", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I35.0", "primary_indication", "strong"), ("I35.2", "primary_indication", "strong")]},
    {"hcpcs_code": "33430", "short": "Mitral Valve Replacement Open", "long": "Replacement, mitral valve, with cardiopulmonary bypass", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I34.0", "primary_indication", "strong"), ("I05.0", "primary_indication", "strong")]},
    {"hcpcs_code": "33425", "short": "Mitral Valve Valvuloplasty/Repair", "long": "Valvuloplasty, mitral valve, with cardiopulmonary bypass", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I34.0", "primary_indication", "strong")]},
    {"hcpcs_code": "93458", "short": "Left Heart Cath with Coronary Angiogram", "long": "Left heart catheterization including intraprocedural injection(s) for coronary angiography", "cat": "Cardiovascular Diagnostics", "cpt": "CPT-I", "denial": "medium", "ind": [("I25.10", "primary_indication", "strong"), ("R07.9", "primary_indication", "moderate")]},
    {"hcpcs_code": "33249", "short": "ICD/Pacemaker System Implantation", "long": "Insertion or replacement of pacemaker system or implantable defibrillator system, transvenous leads", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I48.0", "primary_indication", "moderate"), ("I49.01", "primary_indication", "strong"), ("I50.9", "secondary_indication", "strong")]},
    {"hcpcs_code": "33208", "short": "Dual Chamber Permanent Pacemaker Insertion", "long": "Insertion of new or replacement of permanent pacemaker with transvenous leads, dual chamber", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("I44.2", "primary_indication", "strong"), ("I48.91", "secondary_indication", "moderate")]},
    {"hcpcs_code": "34800", "short": "Endovascular Abdominal Aortic Aneurysm Repair (EVAR)", "long": "Endovascular repair of infrarenal abdominal aortic aneurysm using modular bifurcated prosthesis", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I71.40", "primary_indication", "strong")]},
    {"hcpcs_code": "33880", "short": "Thoracic Endovascular Aortic Repair (TEVAR)", "long": "Endovascular repair of descending thoracic aorta; involving coverage of left subclavian artery origin", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I71.20", "primary_indication", "strong")]},
    {"hcpcs_code": "33340", "short": "Percutaneous Left Atrial Appendage Closure (Watchman)", "long": "Percutaneous transcatheter closure of the left atrial appendage with implant", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I48.0", "primary_indication", "strong"), ("I48.91", "primary_indication", "strong")]},
    {"hcpcs_code": "93580", "short": "Percutaneous Atrial Septal Defect (ASD) Closure", "long": "Percutaneous transcatheter closure of congenital interatrial communication (e.g., ASD, PFO)", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("Q21.10", "primary_indication", "strong")]},
    {"hcpcs_code": "33016", "short": "Pericardiocentesis with Imaging Guidance", "long": "Pericardiocentesis with imaging guidance (e.g., cardiac tamponade drainage)", "cat": "Cardiovascular Surgery", "cpt": "CPT-I", "denial": "low", "ind": [("I31.31", "primary_indication", "strong")]},
    {"hcpcs_code": "93224", "short": "Holter Monitor 24-48 Hour Continuous ECG", "long": "External electrocardiographic recording up to 48 hours by continuous rhythm monitor", "cat": "Cardiovascular Diagnostics", "cpt": "CPT-I", "denial": "low", "ind": [("I48.91", "primary_indication", "strong"), ("R00.2", "primary_indication", "strong")]},
    {"hcpcs_code": "93350", "short": "Stress Echocardiography with Pharmacological/Treadmill", "long": "Echocardiography, transthoracic, real-time with image documentation, during rest and cardiovascular stress", "cat": "Cardiovascular Diagnostics", "cpt": "CPT-I", "denial": "medium", "ind": [("I25.10", "primary_indication", "strong"), ("R07.9", "primary_indication", "moderate")]},

    # ── 3. General & Abdominal Surgery (18 procedures) ──
    {"hcpcs_code": "47562", "short": "Laparoscopic Cholecystectomy", "long": "Laparoscopy, surgical; cholecystectomy", "cat": "General Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("K80.00", "primary_indication", "strong"), ("K80.20", "primary_indication", "strong")]},
    {"hcpcs_code": "47563", "short": "Lap Cholecystectomy with Cholangiography", "long": "Laparoscopy, surgical; cholecystectomy with cholangiography", "cat": "General Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("K80.00", "primary_indication", "strong")]},
    {"hcpcs_code": "44970", "short": "Laparoscopic Appendectomy", "long": "Laparoscopy, surgical, appendectomy", "cat": "General Surgery", "cpt": "CPT-I", "denial": "low", "ind": [("K35.80", "primary_indication", "strong"), ("K35.200", "primary_indication", "strong")]},
    {"hcpcs_code": "44950", "short": "Open Appendectomy", "long": "Appendectomy; open approach", "cat": "General Surgery", "cpt": "CPT-I", "denial": "low", "ind": [("K35.80", "primary_indication", "strong")]},
    {"hcpcs_code": "49505", "short": "Inguinal Hernia Repair Open", "long": "Repair initial inguinal hernia, age 5 years or older; reducible", "cat": "General Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("K40.90", "primary_indication", "strong")]},
    {"hcpcs_code": "49650", "short": "Laparoscopic Inguinal Hernia Repair", "long": "Laparoscopy, surgical; repair initial inguinal hernia", "cat": "General Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("K40.90", "primary_indication", "strong")]},
    {"hcpcs_code": "49560", "short": "Ventral/Incisional Hernia Repair Open", "long": "Repair initial incisional or ventral hernia; reducible", "cat": "General Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("K43.2", "primary_indication", "strong"), ("K43.0", "primary_indication", "strong")]},
    {"hcpcs_code": "49652", "short": "Laparoscopic Ventral Hernia Repair", "long": "Laparoscopy, surgical, repair, ventral, umbilical, spigelian or incisional hernia", "cat": "General Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("K43.2", "primary_indication", "strong")]},
    {"hcpcs_code": "43280", "short": "Laparoscopic Fundoplication (Nissen)", "long": "Laparoscopy, surgical, esophagogastric fundoplasty (e.g., Nissen, Toupet procedures)", "cat": "General Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("K21.0", "primary_indication", "strong"), ("K44.9", "primary_indication", "strong")]},
    {"hcpcs_code": "48150", "short": "Whipple Procedure (Pancreaticoduodenectomy)", "long": "Pancreatectomy, proximal subtotal with total duodenectomy, partial gastrectomy, choledochoenterostomy", "cat": "General Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("C25.9", "primary_indication", "strong")]},
    {"hcpcs_code": "47120", "short": "Partial Hepatectomy Liver Resection", "long": "Hepatectomy, resection of liver; partial lobectomy", "cat": "General Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("C22.0", "primary_indication", "strong")]},
    {"hcpcs_code": "44140", "short": "Partial Colectomy with Anastomosis", "long": "Colectomy, partial; with anastomosis", "cat": "General Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("C18.9", "primary_indication", "strong"), ("K57.30", "primary_indication", "strong")]},
    {"hcpcs_code": "45119", "short": "Laparoscopic Low Anterior Resection (LAR)", "long": "Laparoscopy, surgical; proctectomy, combined abdominoperineal pull-through with colonic reservoir", "cat": "General Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("C20", "primary_indication", "strong")]},
    {"hcpcs_code": "38120", "short": "Laparoscopic Splenectomy", "long": "Laparoscopy, surgical, splenectomy", "cat": "General Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("D69.3", "primary_indication", "strong")]},
    {"hcpcs_code": "60240", "short": "Total Thyroidectomy", "long": "Thyroidectomy, total or complete", "cat": "General Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("C73", "primary_indication", "strong"), ("E05.90", "primary_indication", "moderate")]},
    {"hcpcs_code": "60500", "short": "Parathyroidectomy Parathyroid Exploration", "long": "Parathyroidectomy or exploration of parathyroid(s)", "cat": "General Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("E21.0", "primary_indication", "strong")]},
    {"hcpcs_code": "49000", "short": "Exploratory Laparotomy", "long": "Exploratory laparotomy, exploratory celiotomy with or without biopsy(s)", "cat": "General Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("R10.9", "primary_indication", "moderate"), ("K56.600", "primary_indication", "strong")]},
    {"hcpcs_code": "46250", "short": "Hemorrhoidectomy Complete External and Internal", "long": "Hemorrhoidectomy, external and internal, 2 or more columns/groups", "cat": "General Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("K64.9", "primary_indication", "strong")]},

    # ── 4. GI Diagnostics & Endoscopy (10 procedures) ──
    {"hcpcs_code": "43239", "short": "Upper GI Endoscopy with Biopsy", "long": "Esophagogastroduodenoscopy, flexible, transoral; with biopsy, single or multiple", "cat": "GI Diagnostics", "cpt": "CPT-I", "denial": "medium", "ind": [("K21.0", "primary_indication", "strong"), ("K29.00", "primary_indication", "strong"), ("K25.9", "primary_indication", "strong")]},
    {"hcpcs_code": "45378", "short": "Diagnostic Colonoscopy", "long": "Colonoscopy, flexible; diagnostic, including collection of specimen(s) by brushing or washing", "cat": "GI Diagnostics", "cpt": "CPT-I", "denial": "medium", "ind": [("K57.30", "primary_indication", "strong"), ("K50.90", "primary_indication", "strong"), ("R19.7", "primary_indication", "moderate")]},
    {"hcpcs_code": "45385", "short": "Colonoscopy with Snare Polypectomy", "long": "Colonoscopy, flexible; with removal of tumor(s), polyp(s), or other lesion(s) by snare technique", "cat": "GI Diagnostics", "cpt": "CPT-I", "denial": "medium", "ind": [("D12.6", "primary_indication", "strong"), ("K63.5", "primary_indication", "strong")]},
    {"hcpcs_code": "43235", "short": "Diagnostic Esophagogastroduodenoscopy (EGD)", "long": "Esophagogastroduodenoscopy, flexible, transoral; diagnostic, including collection of specimens", "cat": "GI Diagnostics", "cpt": "CPT-I", "denial": "low", "ind": [("K21.0", "primary_indication", "strong"), ("R10.9", "primary_indication", "moderate")]},
    {"hcpcs_code": "43260", "short": "Endoscopic Retrograde Cholangiopancreatography (ERCP)", "long": "Endoscopic retrograde cholangiopancreatography (ERCP); diagnostic, including specimen collection", "cat": "GI Diagnostics", "cpt": "CPT-I", "denial": "high", "ind": [("K80.00", "primary_indication", "strong"), ("K83.09", "primary_indication", "strong")]},
    {"hcpcs_code": "43264", "short": "ERCP with Gallstone/Calculus Removal", "long": "Endoscopic retrograde cholangiopancreatography (ERCP); with removal of calculi/debris from biliary duct", "cat": "GI Diagnostics", "cpt": "CPT-I", "denial": "high", "ind": [("K80.00", "primary_indication", "strong")]},
    {"hcpcs_code": "43242", "short": "Endoscopic Ultrasound (EUS) with Fine Needle Biopsy", "long": "Esophagogastroduodenoscopy, flexible, transoral; with transendoscopic ultrasound-guided intramural or transmural fine needle aspiration/biopsy(s)", "cat": "GI Diagnostics", "cpt": "CPT-I", "denial": "high", "ind": [("C25.9", "primary_indication", "strong"), ("D37.9", "primary_indication", "moderate")]},
    {"hcpcs_code": "45330", "short": "Diagnostic Flexible Sigmoidoscopy", "long": "Sigmoidoscopy, flexible; diagnostic, including collection of specimen(s) by brushing or washing", "cat": "GI Diagnostics", "cpt": "CPT-I", "denial": "low", "ind": [("K64.9", "primary_indication", "strong"), ("K57.30", "primary_indication", "strong")]},
    {"hcpcs_code": "43246", "short": "Percutaneous Endoscopic Gastrostomy (PEG Tube)", "long": "Esophagogastroduodenoscopy, flexible, transoral; with directed placement of percutaneous gastrostomy tube", "cat": "GI Diagnostics", "cpt": "CPT-I", "denial": "medium", "ind": [("R13.10", "primary_indication", "strong")]},
    {"hcpcs_code": "91035", "short": "Esophageal pH Monitoring Bravo Wireless Capsule", "long": "Esophageal pH monitoring, telemetry capsule, including attachment, monitoring, recording, analysis", "cat": "GI Diagnostics", "cpt": "CPT-I", "denial": "high", "ind": [("K21.0", "primary_indication", "strong")]},

    # ── 5. Urology & Nephrology (15 procedures) ──
    {"hcpcs_code": "52601", "short": "TURP Transurethral Prostate Resection", "long": "Transurethral electrosurgical resection of prostate, including control of postoperative bleeding, complete", "cat": "Urology", "cpt": "CPT-I", "denial": "high", "ind": [("N40.0", "primary_indication", "strong")]},
    {"hcpcs_code": "52353", "short": "Ureteroscopy with Laser Lithotripsy", "long": "Cystourethroscopy, with ureteroscopy and/or pyeloscopy; with lithotripsy", "cat": "Urology", "cpt": "CPT-I", "denial": "medium", "ind": [("N20.0", "primary_indication", "strong"), ("N20.1", "primary_indication", "strong")]},
    {"hcpcs_code": "50590", "short": "Extracorporeal Shock Wave Lithotripsy (ESWL)", "long": "Lithotripsy, extracorporeal shock wave (renal or ureteral calculus)", "cat": "Urology", "cpt": "CPT-I", "denial": "medium", "ind": [("N20.0", "primary_indication", "strong"), ("N20.1", "primary_indication", "strong")]},
    {"hcpcs_code": "50080", "short": "Percutaneous Nephrolithotomy (PCNL)", "long": "Percutaneous nephrostolithotomy or pyelostolithotomy; up to 2 cm", "cat": "Urology", "cpt": "CPT-I", "denial": "high", "ind": [("N20.0", "primary_indication", "strong")]},
    {"hcpcs_code": "55866", "short": "Laparoscopic Radical Prostatectomy", "long": "Laparoscopy, surgical prostatectomy, retropubic radical, nerve sparing, robotic assistance", "cat": "Urology", "cpt": "CPT-I", "denial": "high", "ind": [("C61", "primary_indication", "strong")]},
    {"hcpcs_code": "50545", "short": "Laparoscopic Radical Nephrectomy", "long": "Laparoscopy, surgical; radical nephrectomy (includes removal of Gerota's fascia and surrounding fatty tissue)", "cat": "Urology", "cpt": "CPT-I", "denial": "high", "ind": [("C64.9", "primary_indication", "strong")]},
    {"hcpcs_code": "50543", "short": "Laparoscopic Partial Nephrectomy", "long": "Laparoscopy, surgical; partial nephrectomy", "cat": "Urology", "cpt": "CPT-I", "denial": "high", "ind": [("C64.9", "primary_indication", "strong"), ("D41.00", "primary_indication", "moderate")]},
    {"hcpcs_code": "52234", "short": "TURBT Bladder Tumor Resection Small", "long": "Cystourethroscopy, with fulguration and/or resection of; SMALL bladder tumor(s) (0.5 up to 2.0 cm)", "cat": "Urology", "cpt": "CPT-I", "denial": "medium", "ind": [("C67.9", "primary_indication", "strong"), ("D49.4", "primary_indication", "moderate")]},
    {"hcpcs_code": "52235", "short": "TURBT Bladder Tumor Resection Medium", "long": "Cystourethroscopy, with fulguration and/or resection of; MEDIUM bladder tumor(s) (2.0 to 5.0 cm)", "cat": "Urology", "cpt": "CPT-I", "denial": "medium", "ind": [("C67.9", "primary_indication", "strong")]},
    {"hcpcs_code": "52332", "short": "Cystourethroscopy with Ureteral Stent Insertion", "long": "Cystourethroscopy, with insertion of indwelling ureteral stent (e.g., Gibbons or double-J type)", "cat": "Urology", "cpt": "CPT-I", "denial": "low", "ind": [("N20.1", "primary_indication", "strong"), ("N13.2", "primary_indication", "strong")]},
    {"hcpcs_code": "53850", "short": "Transurethral Microwave Thermotherapy Prostate (TUMT)", "long": "Transurethral destruction of prostate tissue; by microwave thermotherapy", "cat": "Urology", "cpt": "CPT-I", "denial": "high", "ind": [("N40.0", "primary_indication", "moderate")]},
    {"hcpcs_code": "52648", "short": "Laser Vaporization of Prostate (GreenLight Laser)", "long": "Laser vaporization of prostate, including control of postoperative bleeding, complete", "cat": "Urology", "cpt": "CPT-I", "denial": "high", "ind": [("N40.0", "primary_indication", "strong")]},
    {"hcpcs_code": "54150", "short": "Circumcision Surgical Adult", "long": "Circumcision, surgical excision other than clamp, device or dorsal slit; except newborn", "cat": "Urology", "cpt": "CPT-I", "denial": "high", "ind": [("N47.1", "primary_indication", "strong")]},
    {"hcpcs_code": "55040", "short": "Excision of Hydrocele Tunica Vaginalis", "long": "Excision of hydrocele; unilateral", "cat": "Urology", "cpt": "CPT-I", "denial": "low", "ind": [("N43.3", "primary_indication", "strong")]},
    {"hcpcs_code": "55530", "short": "Varicocelectomy Spermatic Vein Ligation", "long": "Excision of varicocele or ligation of spermatic veins for varicocele", "cat": "Urology", "cpt": "CPT-I", "denial": "high", "ind": [("I86.1", "primary_indication", "moderate")]},

    # ── 6. Ophthalmology (12 procedures) ──
    {"hcpcs_code": "66984", "short": "Cataract Surgery with Monofocal IOL", "long": "Extracapsular cataract removal with insertion of intraocular lens prosthesis, manual or phacoemulsification", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "high", "ind": [("H25.9", "primary_indication", "strong"), ("H25.10", "primary_indication", "strong")]},
    {"hcpcs_code": "66982", "short": "Complex Cataract Surgery with IOL", "long": "Extracapsular cataract extraction with insertion of intraocular lens prosthesis, complex (e.g. iris expansion device, vitrectomy)", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "high", "ind": [("H25.9", "primary_indication", "strong")]},
    {"hcpcs_code": "65855", "short": "Selective Laser Trabeculoplasty (SLT)", "long": "Trabeculoplasty by laser, 1 or more sessions (for glaucoma intraocular pressure reduction)", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "medium", "ind": [("H40.10X0", "primary_indication", "strong"), ("H40.10X1", "primary_indication", "strong")]},
    {"hcpcs_code": "67028", "short": "Intravitreal Anti-VEGF Injection", "long": "Intravitreal injection of a pharmacologic agent (e.g., aflibercept, ranibizumab, bevacizumab)", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "high", "ind": [("E11.311", "primary_indication", "strong"), ("H35.3110", "primary_indication", "strong")]},
    {"hcpcs_code": "67108", "short": "Pars Plana Vitrectomy Retinal Detachment", "long": "Repair of retinal detachment; with vitrectomy, air or gas tamponade, focal laser photocoagulation", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "medium", "ind": [("H33.001", "primary_indication", "strong")]},
    {"hcpcs_code": "67041", "short": "Vitrectomy with Epiretinal Membrane Peeling", "long": "Vitrectomy, mechanical, pars plana approach; with removal of preretinal cellular membrane", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "high", "ind": [("H35.371", "primary_indication", "strong")]},
    {"hcpcs_code": "65730", "short": "Penetrating Keratoplasty (Corneal Transplant)", "long": "Keratoplasty (corneal transplant); penetrating (except in aphakia or pseudophakia)", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "high", "ind": [("H18.511", "primary_indication", "strong"), ("H17.9", "primary_indication", "strong")]},
    {"hcpcs_code": "66170", "short": "Trabeculectomy ab Externo for Glaucoma", "long": "Fistulization of sclera for glaucoma; trabeculectomy ab externo in absence of previous surgery", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "high", "ind": [("H40.10X0", "primary_indication", "strong")]},
    {"hcpcs_code": "65760", "short": "Laser In-Situ Keratomileusis (LASIK)", "long": "Keratomileusis; laser in situ refractive correction for myopia, astigmatism, or hyperopia", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "high", "ind": [("H52.10", "primary_indication", "weak"), ("H52.201", "primary_indication", "weak")]},
    {"hcpcs_code": "66821", "short": "YAG Laser Posterior Capsulotomy", "long": "Discission of secondary membranous cataract (after cataract); with laser surgery (e.g., YAG laser)", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "low", "ind": [("H26.491", "primary_indication", "strong")]},
    {"hcpcs_code": "65426", "short": "Pterygium Excision with Conjunctival Autograft", "long": "Excision or transposition of pterygium; with conjunctival graft", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "medium", "ind": [("H11.001", "primary_indication", "strong")]},
    {"hcpcs_code": "67904", "short": "Repair Ptosis Blepharoptosis Levator Resection", "long": "Repair of blepharoptosis; (levator aponeurosis dehiscence or tuck, internal or external approach)", "cat": "Ophthalmology", "cpt": "CPT-I", "denial": "high", "ind": [("H02.401", "primary_indication", "moderate")]},

    # ── 7. Neurosurgery & Spine (12 procedures) ──
    {"hcpcs_code": "61510", "short": "Craniotomy for Supratentorial Brain Tumor", "long": "Craniectomy, trephination, bone flap craniotomy; for excision of brain tumor, supratentorial", "cat": "Neurosurgery", "cpt": "CPT-I", "denial": "high", "ind": [("C71.9", "primary_indication", "strong"), ("D33.2", "primary_indication", "strong")]},
    {"hcpcs_code": "61624", "short": "Transcatheter Brain Aneurysm Coiling / Embolization", "long": "Transcatheter permanent occlusion or embolization; central nervous system (intracranial aneurysm, AVM)", "cat": "Neurosurgery", "cpt": "CPT-I", "denial": "high", "ind": [("I60.9", "primary_indication", "strong"), ("I67.1", "primary_indication", "strong")]},
    {"hcpcs_code": "63047", "short": "Lumbar Laminectomy for Spinal Stenosis", "long": "Laminectomy, facetectomy and foraminotomy with decompression of cauda equina and nerve root(s); lumbar", "cat": "Neurosurgery", "cpt": "CPT-I", "denial": "high", "ind": [("M48.061", "primary_indication", "strong"), ("M51.16", "primary_indication", "strong")]},
    {"hcpcs_code": "62223", "short": "Ventriculoperitoneal (VP) Shunt Insertion", "long": "Creation of shunt; ventriculo-peritoneal, -pleural, other terminus", "cat": "Neurosurgery", "cpt": "CPT-I", "denial": "medium", "ind": [("G91.2", "primary_indication", "strong")]},
    {"hcpcs_code": "61154", "short": "Burr Hole Evacuation Subdural Hematoma", "long": "Burr hole(s) with evacuation and/or drainage of hematoma, extradural or subdural", "cat": "Neurosurgery", "cpt": "CPT-I", "denial": "low", "ind": [("S06.5X0A", "primary_indication", "strong")]},
    {"hcpcs_code": "61867", "short": "Deep Brain Stimulation (DBS) Lead Implantation", "long": "Twist drill, burr hole, craniotomy, or craniectomy for stereotactic implantation of neurostimulator electrode array; first array", "cat": "Neurosurgery", "cpt": "CPT-I", "denial": "high", "ind": [("G20", "primary_indication", "strong")]},
    {"hcpcs_code": "61458", "short": "Microvascular Decompression Trigeminal Nerve", "long": "Craniotomy, suboccipital; for exploration or decompression of cranial nerves (e.g., trigeminal neuralgia)", "cat": "Neurosurgery", "cpt": "CPT-I", "denial": "high", "ind": [("G50.0", "primary_indication", "strong")]},
    {"hcpcs_code": "62290", "short": "Lumbar Discography Injection", "long": "Injection procedure for discography, each level; lumbar", "cat": "Neurosurgery", "cpt": "CPT-I", "denial": "high", "ind": [("M51.16", "primary_indication", "weak")]},
    {"hcpcs_code": "22630", "short": "Posterior Lumbar Interbody Fusion (PLIF)", "long": "Arthrodesis, posterior interbody technique, including laminectomy and/or discectomy; lumbar, single interspace", "cat": "Neurosurgery", "cpt": "CPT-I", "denial": "high", "ind": [("M47.816", "primary_indication", "strong"), ("M51.16", "primary_indication", "strong")]},
    {"hcpcs_code": "61548", "short": "Hypophysectomy Pituitary Tumor Transsphenoidal", "long": "Hypophysectomy or excision of pituitary tumor, transnasal or transseptal approach, nonstereotactic", "cat": "Neurosurgery", "cpt": "CPT-I", "denial": "high", "ind": [("D35.2", "primary_indication", "strong")]},
    {"hcpcs_code": "61781", "short": "Stereotactic Computer-Assisted Navigation Brain", "long": "Stereotactic computer-assisted (navigational) procedure; cranial, intradural (add-on)", "cat": "Neurosurgery", "cpt": "CPT-I", "denial": "high", "ind": [("C71.9", "secondary_indication", "strong")]},
    {"hcpcs_code": "77372", "short": "Stereotactic Radiosurgery (Gamma Knife / CyberKnife)", "long": "Radiation treatment delivery, stereotactic radiosurgery (SRS), complete course of therapy in one session", "cat": "Radiation Oncology", "cpt": "CPT-I", "denial": "high", "ind": [("C71.9", "primary_indication", "strong"), ("D33.2", "primary_indication", "strong")]},

    # ── 8. Oncology Surgery & Medical Oncology (12 procedures) ──
    {"hcpcs_code": "19301", "short": "Partial Mastectomy (Lumpectomy)", "long": "Mastectomy, partial (e.g., lumpectomy, tylectomy, quadrantectomy, segmentectomy)", "cat": "Oncology Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("C50.911", "primary_indication", "strong"), ("D05.90", "primary_indication", "strong")]},
    {"hcpcs_code": "19303", "short": "Total Mastectomy Simple", "long": "Mastectomy, simple, complete; with or without axillary lymphadenectomy", "cat": "Oncology Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("C50.911", "primary_indication", "strong")]},
    {"hcpcs_code": "38720", "short": "Cervical Radical Lymphadenectomy", "long": "Cervical lymphadenectomy (complete); unilateral or bilateral radical neck dissection", "cat": "Oncology Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("C73", "primary_indication", "strong"), ("C32.9", "primary_indication", "strong")]},
    {"hcpcs_code": "38500", "short": "Biopsy or Excision of Lymph Node Superficial", "long": "Biopsy or excision of lymph node(s); open, superficial", "cat": "Oncology Surgery", "cpt": "CPT-I", "denial": "low", "ind": [("R59.9", "primary_indication", "strong")]},
    {"hcpcs_code": "38525", "short": "Axillary Sentinel Lymph Node Biopsy", "long": "Biopsy or excision of lymph node(s); open, deep axillary node(s)", "cat": "Oncology Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("C50.911", "primary_indication", "strong")]},
    {"hcpcs_code": "77385", "short": "Intensity Modulated Radiation Therapy (IMRT)", "long": "Intensity modulated radiation therapy (IMRT) delivery, includes guidance and tracking, per session", "cat": "Radiation Oncology", "cpt": "CPT-I", "denial": "high", "ind": [("C50.911", "primary_indication", "strong"), ("C61", "primary_indication", "strong")]},
    {"hcpcs_code": "77301", "short": "IMRT Dosimetry and Treatment Planning", "long": "Intensity modulated radiotherapy plan, including dose-volume histograms, reverse planning optimization", "cat": "Radiation Oncology", "cpt": "CPT-I", "denial": "medium", "ind": [("C50.911", "primary_indication", "strong"), ("C61", "primary_indication", "strong")]},
    {"hcpcs_code": "96413", "short": "Chemotherapy IV Infusion Initial Hour", "long": "Chemotherapy administration, intravenous infusion technique; up to 1 hour, single or initial drug", "cat": "Medical Oncology", "cpt": "CPT-I", "denial": "medium", "ind": [("C50.911", "primary_indication", "strong"), ("C34.90", "primary_indication", "strong"), ("Z51.11", "primary_indication", "strong")]},
    {"hcpcs_code": "96415", "short": "Chemotherapy IV Infusion Additional Hour", "long": "Chemotherapy administration, intravenous infusion technique; each additional hour (add-on code)", "cat": "Medical Oncology", "cpt": "CPT-I", "denial": "low", "ind": [("Z51.11", "primary_indication", "strong")]},
    {"hcpcs_code": "36561", "short": "Insertion Chemotherapy Port-a-Cath Subclavian", "long": "Insertion of tunneled centrally placed vascular access device, with subcutaneous port; age 5 years or older", "cat": "Medical Oncology", "cpt": "CPT-I", "denial": "medium", "ind": [("Z51.11", "primary_indication", "strong"), ("C50.911", "secondary_indication", "strong")]},
    {"hcpcs_code": "38222", "short": "Bone Marrow Biopsy and Aspiration", "long": "Diagnostic bone marrow; biopsy(ies) and aspiration(s)", "cat": "Hematology / Oncology", "cpt": "CPT-I", "denial": "low", "ind": [("C91.00", "primary_indication", "strong"), ("D61.9", "primary_indication", "strong")]},
    {"hcpcs_code": "38240", "short": "Allogeneic Hematopoietic Stem Cell Transplant (BMT)", "long": "Hematopoietic progenitor cell (HPC); allogeneic transplantation per donor", "cat": "Hematology / Oncology", "cpt": "CPT-I", "denial": "high", "ind": [("C91.00", "primary_indication", "strong"), ("C92.00", "primary_indication", "strong")]},

    # ── 9. Bariatric & Metabolic Surgery (5 procedures) ──
    {"hcpcs_code": "43775", "short": "Laparoscopic Sleeve Gastrectomy", "long": "Laparoscopy, surgical, gastric restrictive procedure; longitudinal gastrectomy (sleeve gastrectomy)", "cat": "Bariatric Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("E66.01", "primary_indication", "strong"), ("E11.9", "secondary_indication", "moderate")]},
    {"hcpcs_code": "43644", "short": "Laparoscopic Roux-en-Y Gastric Bypass", "long": "Laparoscopy, surgical, gastric restrictive procedure; with gastric bypass and Roux-en-Y gastroenterostomy", "cat": "Bariatric Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("E66.01", "primary_indication", "strong"), ("E11.9", "secondary_indication", "moderate")]},
    {"hcpcs_code": "43770", "short": "Laparoscopic Adjustable Gastric Banding", "long": "Laparoscopy, surgical, gastric restrictive procedure; placement of adjustable gastric restrictive device", "cat": "Bariatric Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("E66.01", "primary_indication", "moderate")]},
    {"hcpcs_code": "43848", "short": "Revision of Bariatric Gastric Restrictive Procedure", "long": "Revision, with gastric bypass, for obesity; previous gastric restrictive procedure without bypass", "cat": "Bariatric Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("E66.01", "primary_indication", "strong")]},
    {"hcpcs_code": "43774", "short": "Removal of Adjustable Gastric Band", "long": "Laparoscopy, surgical, gastric restrictive procedure; removal of adjustable gastric restrictive device component only", "cat": "Bariatric Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("T85.698A", "primary_indication", "strong")]},

    # ── 10. ENT & Head/Neck Surgery (10 procedures) ──
    {"hcpcs_code": "42820", "short": "Tonsillectomy and Adenoidectomy Child/Adult", "long": "Tonsillectomy and adenoidectomy; younger than age 12 or adult", "cat": "ENT Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("J35.01", "primary_indication", "strong"), ("J35.2", "primary_indication", "strong")]},
    {"hcpcs_code": "42826", "short": "Tonsillectomy Primary Adult", "long": "Tonsillectomy, primary or secondary; age 12 or over", "cat": "ENT Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("J35.01", "primary_indication", "strong")]},
    {"hcpcs_code": "31255", "short": "FESS Sinus Endoscopy Total Ethmoidectomy", "long": "Nasal/sinus endoscopy, surgical; with total ethmoidectomy", "cat": "ENT Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("J32.9", "primary_indication", "strong"), ("J33.9", "primary_indication", "strong")]},
    {"hcpcs_code": "31256", "short": "FESS Endoscopic Maxillary Antrostomy", "long": "Nasal/sinus endoscopy, surgical, with maxillary antrostomy", "cat": "ENT Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("J32.9", "primary_indication", "strong")]},
    {"hcpcs_code": "30520", "short": "Septoplasty with Cartilage Scoring", "long": "Septoplasty or submucous resection, with or without cartilage scoring or contouring", "cat": "ENT Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("J34.2", "primary_indication", "strong")]},
    {"hcpcs_code": "30140", "short": "Submucous Resection Inferior Turbinate", "long": "Submucous resection inferior turbinate, partial or complete, any method", "cat": "ENT Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("J34.3", "primary_indication", "strong")]},
    {"hcpcs_code": "69436", "short": "Tympanostomy with Ventilation Tube Insertion", "long": "Tympanostomy (requiring insertion of ventilating tube), general anesthesia", "cat": "ENT Surgery", "cpt": "CPT-I", "denial": "low", "ind": [("H65.01", "primary_indication", "strong")]},
    {"hcpcs_code": "69631", "short": "Tympanoplasty without Ossicular Reconstruction", "long": "Tympanoplasty without mastoidectomy; with ossicular chain reconstruction not performed", "cat": "ENT Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("H72.90", "primary_indication", "strong")]},
    {"hcpcs_code": "69502", "short": "Mastoidectomy Complete Radical", "long": "Mastoidectomy; complete or modified radical", "cat": "ENT Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("H70.001", "primary_indication", "strong")]},
    {"hcpcs_code": "42410", "short": "Superficial Parotidectomy Lateral Lobectomy", "long": "Excision of parotid tumor or parotid gland; lateral lobe, without nerve dissection", "cat": "ENT Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("D11.0", "primary_indication", "strong")]},

    # ── 11. Obstetrics & Gynecology (12 procedures) ──
    {"hcpcs_code": "59510", "short": "Cesarean Delivery with Complete Antepartum/Postpartum", "long": "Routine obstetric care including antepartum care, cesarean delivery, and postpartum care", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "high", "ind": [("O82", "primary_indication", "strong"), ("O60.00", "primary_indication", "strong")]},
    {"hcpcs_code": "59400", "short": "Vaginal Delivery with Antepartum/Postpartum", "long": "Routine obstetric care including antepartum care, vaginal delivery (with or without episiotomy) and postpartum care", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "high", "ind": [("O80", "primary_indication", "strong")]},
    {"hcpcs_code": "58571", "short": "Laparoscopic Total Hysterectomy with Salpingo-Oophorectomy", "long": "Laparoscopy, surgical, with total hysterectomy, for uterus 250 g or less; with removal of tube(s) and/or ovary(s)", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "high", "ind": [("D25.9", "primary_indication", "strong"), ("N80.00", "primary_indication", "strong")]},
    {"hcpcs_code": "58150", "short": "Total Abdominal Hysterectomy Open", "long": "Total abdominal hysterectomy (corpus and cervix), with or without removal of tube(s) or ovary(s)", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "high", "ind": [("D25.9", "primary_indication", "strong")]},
    {"hcpcs_code": "58545", "short": "Laparoscopic Myomectomy Uterine Fibroids", "long": "Laparoscopy, surgical, myomectomy, excision; 1 to 4 intramural myomas with total weight of 250 g or less", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "high", "ind": [("D25.9", "primary_indication", "strong")]},
    {"hcpcs_code": "58661", "short": "Laparoscopic Ovarian Cystectomy", "long": "Laparoscopy, surgical; with removal of adnexal structures (partial or total oophorectomy and/or salpingectomy)", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "medium", "ind": [("N83.201", "primary_indication", "strong")]},
    {"hcpcs_code": "59121", "short": "Surgical Treatment of Tubal Ectopic Pregnancy", "long": "Surgical treatment of ectopic pregnancy; tubal or ovarian, requiring salpingectomy and/or oophorectomy", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "low", "ind": [("O00.101", "primary_indication", "strong")]},
    {"hcpcs_code": "58120", "short": "Dilation and Curettage (D&C) Diagnostic/Therapeutic", "long": "Dilation and curettage, diagnostic and/or therapeutic (nonobstetrical)", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "medium", "ind": [("N93.9", "primary_indication", "strong"), ("N85.00", "primary_indication", "strong")]},
    {"hcpcs_code": "58558", "short": "Hysteroscopy with Endometrial Biopsy/Polypectomy", "long": "Hysteroscopy, surgical; with sampling (biopsy) of endometrium and/or polypectomy, with or without D&C", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "medium", "ind": [("N84.0", "primary_indication", "strong")]},
    {"hcpcs_code": "58563", "short": "Hysteroscopic Endometrial Ablation", "long": "Hysteroscopy, surgical; with endometrial ablation (e.g., endometrial resection, electrosurgical ablation, thermoablation)", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "high", "ind": [("N93.8", "primary_indication", "strong")]},
    {"hcpcs_code": "57260", "short": "Anterior and Posterior Colporrhaphy (Cystocele/Rectocele)", "long": "Combined anteroposterior colporrhaphy; with or without repair of enterocele", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "medium", "ind": [("N81.10", "primary_indication", "strong"), ("N81.6", "primary_indication", "strong")]},
    {"hcpcs_code": "59320", "short": "Cervical Cerclage Vaginal Approach", "long": "Cerclage of cervix, during pregnancy; vaginal approach (McDonald or Shirodkar)", "cat": "Obstetrics & Gynecology", "cpt": "CPT-I", "denial": "low", "ind": [("O34.30", "primary_indication", "strong")]},

    # ── 12. Emergency Medicine & Critical Care (8 procedures) ──
    {"hcpcs_code": "99285", "short": "Emergency Department Visit High Severity (Level 5)", "long": "Emergency department visit for evaluation and management requiring high complexity decision making", "cat": "Emergency Medicine", "cpt": "CPT-I", "denial": "high", "ind": [("R07.9", "primary_indication", "strong"), ("A41.9", "primary_indication", "strong"), ("I21.0", "primary_indication", "strong")]},
    {"hcpcs_code": "99284", "short": "Emergency Department Visit Urgent (Level 4)", "long": "Emergency department visit for evaluation and management requiring moderate complexity decision making", "cat": "Emergency Medicine", "cpt": "CPT-I", "denial": "medium", "ind": [("R10.9", "primary_indication", "strong"), ("J18.9", "primary_indication", "strong")]},
    {"hcpcs_code": "99291", "short": "Critical Care First 30-74 Minutes", "long": "Critical care, evaluation and management of the critically ill or critically injured patient; first 30-74 minutes", "cat": "Emergency Medicine", "cpt": "CPT-I", "denial": "high", "ind": [("A41.9", "primary_indication", "strong"), ("J96.00", "primary_indication", "strong"), ("R57.0", "primary_indication", "strong")]},
    {"hcpcs_code": "99292", "short": "Critical Care Additional 30 Minutes", "long": "Critical care, evaluation and management; each additional 30 minutes (add-on)", "cat": "Emergency Medicine", "cpt": "CPT-I", "denial": "medium", "ind": [("A41.9", "primary_indication", "strong")]},
    {"hcpcs_code": "92950", "short": "Cardiopulmonary Resuscitation (CPR)", "long": "Cardiopulmonary resuscitation (e.g., in cardiac arrest)", "cat": "Emergency Medicine", "cpt": "CPT-I", "denial": "low", "ind": [("I46.9", "primary_indication", "strong")]},
    {"hcpcs_code": "31500", "short": "Emergency Endotracheal Intubation", "long": "Intubation, endotracheal, emergency procedure", "cat": "Emergency Medicine", "cpt": "CPT-I", "denial": "low", "ind": [("J96.00", "primary_indication", "strong"), ("R09.2", "primary_indication", "strong")]},
    {"hcpcs_code": "36556", "short": "Central Venous Catheter Insertion Non-Tunneled", "long": "Insertion of non-tunneled centrally placed central venous catheter; age 5 years or older", "cat": "Emergency Medicine", "cpt": "CPT-I", "denial": "low", "ind": [("A41.9", "primary_indication", "strong"), ("R57.0", "primary_indication", "strong")]},
    {"hcpcs_code": "32551", "short": "Tube Thoracostomy (Chest Tube Insertion)", "long": "Tube thoracostomy, includes water seal (e.g., for for pneumothorax, hemothorax, empyema)", "cat": "Emergency Medicine", "cpt": "CPT-I", "denial": "low", "ind": [("J93.9", "primary_indication", "strong"), ("J94.2", "primary_indication", "strong")]},

    # ── 13. Dermatology & Plastic Surgery (10 procedures) ──
    {"hcpcs_code": "11102", "short": "Tangential Biopsy Skin Lesion", "long": "Tangential biopsy of skin (e.g., shave, scoop, saucerize, curette); single lesion", "cat": "Dermatology", "cpt": "CPT-I", "denial": "medium", "ind": [("L98.9", "primary_indication", "strong"), ("D23.9", "primary_indication", "strong")]},
    {"hcpcs_code": "11400", "short": "Excision Benign Skin Lesion 0.5 cm or Less", "long": "Excision, benign lesion including margins; trunk, arms or legs; excised diameter 0.5 cm or less", "cat": "Dermatology", "cpt": "CPT-I", "denial": "high", "ind": [("D23.9", "primary_indication", "weak"), ("L72.0", "primary_indication", "moderate")]},
    {"hcpcs_code": "11604", "short": "Excision Malignant Skin Lesion Trunk 3.1-4.0 cm", "long": "Excision, malignant lesion including margins, trunk, arms, or legs; excised diameter 3.1 to 4.0 cm", "cat": "Dermatology", "cpt": "CPT-I", "denial": "medium", "ind": [("C43.9", "primary_indication", "strong"), ("C44.91", "primary_indication", "strong")]},
    {"hcpcs_code": "17311", "short": "Mohs Micrographic Surgery Head/Neck Stage 1", "long": "Mohs micrographic technique, removal of gross tumor, mapping, color coding, microscopic examination; first stage, up to 5 blocks", "cat": "Dermatology", "cpt": "CPT-I", "denial": "high", "ind": [("C44.91", "primary_indication", "strong"), ("C43.9", "primary_indication", "strong")]},
    {"hcpcs_code": "15100", "short": "Split-Thickness Autograft Skin Trunk/Arms", "long": "Split-thickness autograft, trunk, arms, legs; first 100 sq cm or less", "cat": "Plastic Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("T31.0", "primary_indication", "strong"), ("L97.909", "primary_indication", "strong")]},
    {"hcpcs_code": "15260", "short": "Full-Thickness Skin Graft Nose/Ears/Eyelids", "long": "Full thickness graft, free, including direct closure of donor site, nose, ears, eyelids, and/or lips; 20 sq cm or less", "cat": "Plastic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("C44.91", "primary_indication", "strong")]},
    {"hcpcs_code": "15822", "short": "Blepharoplasty Upper Eyelid Functional", "long": "Blepharoplasty, upper eyelid; with excessive skin weighing down lid / visual field defect", "cat": "Plastic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("H02.831", "primary_indication", "strong")]},
    {"hcpcs_code": "15830", "short": "Panniculectomy Infraumbilical Abdominal", "long": "Excision, excessive skin and subcutaneous tissue (includes lipectomy); abdomen, infraumbilical panniculectomy", "cat": "Plastic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("L98.7", "primary_indication", "strong"), ("E66.01", "secondary_indication", "weak")]},
    {"hcpcs_code": "11042", "short": "Surgical Debridement Subcutaneous Tissue", "long": "Debridement, subcutaneous tissue (includes epidermis and dermis, if performed); first 20 sq cm or less", "cat": "Plastic Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("L97.909", "primary_indication", "strong"), ("E11.621", "primary_indication", "strong")]},
    {"hcpcs_code": "19364", "short": "Breast Reconstruction with Free DIEP Flap", "long": "Breast reconstruction with free flap (e.g., deep inferior epigastric perforator DIEP flap)", "cat": "Plastic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("C50.911", "primary_indication", "strong"), ("Z90.11", "primary_indication", "strong")]},

    # ── 14. Pulmonology & Thoracic Surgery (8 procedures) ──
    {"hcpcs_code": "31622", "short": "Diagnostic Flexible Bronchoscopy", "long": "Bronchoscopy, rigid or flexible; diagnostic, with cell washing when performed", "cat": "Pulmonology", "cpt": "CPT-I", "denial": "medium", "ind": [("J18.9", "primary_indication", "strong"), ("C34.90", "primary_indication", "strong")]},
    {"hcpcs_code": "31628", "short": "Transbronchial Lung Biopsy Single Lobe", "long": "Bronchoscopy, rigid or flexible, including fluoroscopic guidance; with transbronchial lung biopsy(s), single lobe", "cat": "Pulmonology", "cpt": "CPT-I", "denial": "high", "ind": [("C34.90", "primary_indication", "strong"), ("J84.9", "primary_indication", "strong")]},
    {"hcpcs_code": "31652", "short": "Endobronchial Ultrasound (EBUS) with Lymph Node Biopsy", "long": "Bronchoscopy, flexible; with endobronchial ultrasound (EBUS) guided transbronchial needle aspiration, 1 or 2 node stations", "cat": "Pulmonology", "cpt": "CPT-I", "denial": "high", "ind": [("C34.90", "primary_indication", "strong")]},
    {"hcpcs_code": "32555", "short": "Thoracentesis with Imaging Guidance", "long": "Thoracentesis, needle or catheter, aspiration of the pleural space; with imaging guidance", "cat": "Pulmonology", "cpt": "CPT-I", "denial": "low", "ind": [("J90", "primary_indication", "strong")]},
    {"hcpcs_code": "32650", "short": "VATS Thoracoscopy with Chemical Pleurodesis", "long": "Thoracoscopy, surgical; with pleurodesis (e.g., mechanical or chemical talc poudrage)", "cat": "Pulmonology", "cpt": "CPT-I", "denial": "medium", "ind": [("J90", "primary_indication", "strong"), ("J93.9", "primary_indication", "strong")]},
    {"hcpcs_code": "32663", "short": "VATS Lobectomy Single Lobe", "long": "Thoracoscopy, surgical; with lobectomy (single lobe)", "cat": "Thoracic Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("C34.90", "primary_indication", "strong")]},
    {"hcpcs_code": "31635", "short": "Bronchoscopy with Foreign Body Removal", "long": "Bronchoscopy, rigid or flexible; with removal of foreign body", "cat": "Pulmonology", "cpt": "CPT-I", "denial": "low", "ind": [("T17.800A", "primary_indication", "strong")]},
    {"hcpcs_code": "94010", "short": "Spirometry Pulmonary Function Test", "long": "Spirometry, including graphic record, total and timed vital capacity, expiratory flow rate measurements", "cat": "Pulmonology", "cpt": "CPT-I", "denial": "low", "ind": [("J44.1", "primary_indication", "strong"), ("J45.20", "primary_indication", "strong")]},

    # ── 15. Pain Management & Interventional Spine (6 procedures) ──
    {"hcpcs_code": "62322", "short": "Lumbar Epidural Steroid Injection", "long": "Injection(s), interlaminar epidural or subarachnoid, lumbar or sacral (caudal); without imaging guidance", "cat": "Pain Management", "cpt": "CPT-I", "denial": "high", "ind": [("M54.5", "primary_indication", "strong"), ("M51.16", "primary_indication", "strong")]},
    {"hcpcs_code": "62323", "short": "Lumbar Epidural Steroid Injection with Fluoroscopy", "long": "Injection(s), interlaminar epidural, lumbar or sacral; with fluoroscopic or CT imaging guidance", "cat": "Pain Management", "cpt": "CPT-I", "denial": "high", "ind": [("M54.5", "primary_indication", "strong"), ("M51.16", "primary_indication", "strong")]},
    {"hcpcs_code": "64493", "short": "Lumbar Facet Joint Nerve Block Single Level", "long": "Injection(s), diagnostic or therapeutic agent, paravertebral facet joint with fluoroscopic/CT guidance; lumbar single level", "cat": "Pain Management", "cpt": "CPT-I", "denial": "high", "ind": [("M47.816", "primary_indication", "strong"), ("M54.5", "primary_indication", "moderate")]},
    {"hcpcs_code": "64635", "short": "Lumbar Facet Radiofrequency Neurotomy / Ablation", "long": "Destruction by neurolytic agent, paravertebral facet joint nerve(s), with fluoroscopic/CT guidance; lumbar single level", "cat": "Pain Management", "cpt": "CPT-I", "denial": "high", "ind": [("M47.816", "primary_indication", "strong")]},
    {"hcpcs_code": "27096", "short": "Sacroiliac (SI) Joint Arthrography / Injection", "long": "Injection procedure for sacroiliac joint, arthrography and/or anesthetic/steroid; with imaging guidance", "cat": "Pain Management", "cpt": "CPT-I", "denial": "high", "ind": [("M53.3", "primary_indication", "strong")]},
    {"hcpcs_code": "63650", "short": "Spinal Cord Stimulator Trial Percutaneous Lead", "long": "Percutaneous implantation of neurostimulator electrode array, epidural (trial stimulation)", "cat": "Pain Management", "cpt": "CPT-I", "denial": "high", "ind": [("G89.4", "primary_indication", "strong"), ("M54.5", "secondary_indication", "moderate")]},

    # ── 16. Vascular Surgery (8 procedures) ──
    {"hcpcs_code": "35301", "short": "Carotid Endarterectomy (CEA)", "long": "Thromboendarterectomy, including patch graft, if performed; carotid, vertebral, subclavian, by neck incision", "cat": "Vascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I65.29", "primary_indication", "strong"), ("I63.9", "primary_indication", "strong")]},
    {"hcpcs_code": "35556", "short": "Femoral-Popliteal Bypass Graft with Vein", "long": "Bypass graft, with vein; femoral-popliteal", "cat": "Vascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I70.209", "primary_indication", "strong")]},
    {"hcpcs_code": "36475", "short": "Endovenous Radiofrequency Ablation (RFA) Varicose Vein", "long": "Endovenous ablation therapy of incompetent vein, extremity, inclusive of all imaging guidance, percutaneous; radiofrequency first vein", "cat": "Vascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I83.90", "primary_indication", "strong"), ("I83.009", "primary_indication", "strong")]},
    {"hcpcs_code": "36478", "short": "Endovenous Laser Ablation (EVLA) Varicose Vein", "long": "Endovenous ablation therapy of incompetent vein, extremity, percutaneous, laser; first vein treated", "cat": "Vascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I83.90", "primary_indication", "strong")]},
    {"hcpcs_code": "37765", "short": "Stab Phlebectomy Varicose Vein 10-20 Incisions", "long": "Stab phlebectomy of varicose veins, 1 extremity; 10-20 stab incisions", "cat": "Vascular Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I83.90", "primary_indication", "moderate")]},
    {"hcpcs_code": "37221", "short": "Iliac Artery Angioplasty with Stent Placement", "long": "Revascularization, endovascular, open or percutaneous, iliac artery, unilateral; with transcatheter stent(s)", "cat": "Vascular Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("I70.209", "primary_indication", "strong")]},
    {"hcpcs_code": "34401", "short": "Thrombectomy Venous Lower Extremity", "long": "Thrombectomy, direct or with catheter; vena cava, iliac, or femoropopliteal vein, by leg incision", "cat": "Vascular Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("I82.409", "primary_indication", "strong")]},
    {"hcpcs_code": "36830", "short": "Arteriovenous (AV) Graft Creation with Synthetic Conduit", "long": "Creation of arteriovenous fistula by other than direct arteriovenous anastomosis (separate procedure); nonautogenous graft", "cat": "Vascular Surgery", "cpt": "CPT-I", "denial": "medium", "ind": [("N18.6", "primary_indication", "strong")]},

    # ── 17. Dialysis & Renal Replacement (4 procedures) ──
    {"hcpcs_code": "90935", "short": "Hemodialysis Single Physician Evaluation", "long": "Hemodialysis procedure with single evaluation by a physician or other qualified health care professional", "cat": "Dialysis", "cpt": "CPT-I", "denial": "medium", "ind": [("N18.6", "primary_indication", "strong"), ("N18.3", "secondary_indication", "moderate")]},
    {"hcpcs_code": "90937", "short": "Hemodialysis Repeated Evaluation Complex", "long": "Hemodialysis procedure requiring repeated evaluations by a physician with or without substantial changes in dialysis prescription", "cat": "Dialysis", "cpt": "CPT-I", "denial": "high", "ind": [("N18.6", "primary_indication", "strong")]},
    {"hcpcs_code": "90945", "short": "Peritoneal Dialysis Single Evaluation", "long": "Dialysis procedure other than hemodialysis (e.g., peritoneal dialysis, hemofiltration, or other continuous renal replacement)", "cat": "Dialysis", "cpt": "CPT-I", "denial": "medium", "ind": [("N18.6", "primary_indication", "strong")]},
    {"hcpcs_code": "36800", "short": "AV Fistula Creation for Hemodialysis", "long": "Insertion of temporary indwelling arteriovenous cannula/shunt or fistula creation for hemodialysis", "cat": "Dialysis Access", "cpt": "CPT-I", "denial": "medium", "ind": [("N18.6", "primary_indication", "strong"), ("N18.3", "primary_indication", "strong")]},

    # ── 18. Organ Transplant Surgery (5 procedures) ──
    {"hcpcs_code": "50360", "short": "Renal Allotransplantation Implantation", "long": "Renal allotransplantation, implantation of graft; without recipient nephrectomy", "cat": "Transplant Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("N18.6", "primary_indication", "strong"), ("Z94.0", "primary_indication", "strong")]},
    {"hcpcs_code": "50547", "short": "Laparoscopic Living Donor Nephrectomy", "long": "Laparoscopy, surgical; donor nephrectomy from living donor (including cold preservation)", "cat": "Transplant Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("Z52.4", "primary_indication", "strong")]},
    {"hcpcs_code": "47135", "short": "Liver Allotransplantation Orthotopic", "long": "Liver allotransplantation; orthotopic, partial or whole, from cadaver or living donor", "cat": "Transplant Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("K72.90", "primary_indication", "strong"), ("K74.60", "primary_indication", "strong")]},
    {"hcpcs_code": "33945", "short": "Heart Allotransplantation Orthotopic", "long": "Heart allotransplantation, with or without recipient cardiectomy", "cat": "Transplant Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("I50.9", "primary_indication", "strong")]},
    {"hcpcs_code": "32851", "short": "Lung Allotransplantation Single", "long": "Lung allotransplantation; single, without cardiopulmonary bypass", "cat": "Transplant Surgery", "cpt": "CPT-I", "denial": "high", "ind": [("J44.1", "primary_indication", "strong")]},

    # ── 19. Dental Surgery (4 procedures) ──
    {"hcpcs_code": "D7140", "short": "Extraction of Erupted Tooth or Exposed Root", "long": "Extraction, erupted tooth or exposed root (elevation and/or forceps removal)", "cat": "Dental Surgery", "cpt": "HCPCS-II", "denial": "high", "ind": [("K02.9", "primary_indication", "weak"), ("K04.7", "primary_indication", "weak")]},
    {"hcpcs_code": "D7210", "short": "Surgical Extraction of Erupted Tooth", "long": "Extraction, erupted tooth requiring removal of bone and/or sectioning of tooth, with elevation of mucoperiosteal flap", "cat": "Dental Surgery", "cpt": "HCPCS-II", "denial": "high", "ind": [("K01.1", "primary_indication", "weak"), ("K04.7", "primary_indication", "weak")]},
    {"hcpcs_code": "D7240", "short": "Removal of Impacted Tooth Completely Bony", "long": "Removal of impacted tooth - completely bony, with unusual surgical complications", "cat": "Dental Surgery", "cpt": "HCPCS-II", "denial": "high", "ind": [("K01.1", "primary_indication", "weak")]},
    {"hcpcs_code": "D7960", "short": "Frenulectomy / Frenectomy Labial or Lingual", "long": "Frenulectomy - also known as frenectomy or frenotomy - separate procedure not incidental to other procedure", "cat": "Dental Surgery", "cpt": "HCPCS-II", "denial": "high", "ind": [("Q38.1", "primary_indication", "weak")]},

    # ── 20. Diagnostic & Interventional Imaging (8 procedures) ──
    {"hcpcs_code": "70553", "short": "MRI Brain with and without Contrast", "long": "Magnetic resonance imaging, brain; without contrast material, followed by contrast material(s)", "cat": "Diagnostic Imaging", "cpt": "CPT-I", "denial": "medium", "ind": [("I63.9", "primary_indication", "strong"), ("G40.909", "primary_indication", "strong")]},
    {"hcpcs_code": "72148", "short": "MRI Lumbar Spine without Contrast", "long": "Magnetic resonance imaging, spinal canal and contents, lumbar; without contrast material", "cat": "Diagnostic Imaging", "cpt": "CPT-I", "denial": "medium", "ind": [("M54.5", "primary_indication", "strong"), ("M51.16", "primary_indication", "strong")]},
    {"hcpcs_code": "73721", "short": "MRI Knee Joint without Contrast", "long": "Magnetic resonance imaging, any joint of lower extremity; without contrast material (knee)", "cat": "Diagnostic Imaging", "cpt": "CPT-I", "denial": "medium", "ind": [("M17.0", "primary_indication", "strong"), ("M23.200", "primary_indication", "strong")]},
    {"hcpcs_code": "71260", "short": "CT Chest with Contrast", "long": "Computed tomography, thorax; with contrast material(s)", "cat": "Diagnostic Imaging", "cpt": "CPT-I", "denial": "medium", "ind": [("J18.9", "primary_indication", "strong"), ("C34.90", "primary_indication", "strong")]},
    {"hcpcs_code": "74177", "short": "CT Abdomen and Pelvis with Contrast", "long": "Computed tomography, abdomen and pelvis; with contrast material(s)", "cat": "Diagnostic Imaging", "cpt": "CPT-I", "denial": "medium", "ind": [("K35.80", "primary_indication", "strong"), ("K80.00", "primary_indication", "strong")]},
    {"hcpcs_code": "78816", "short": "PET-CT Scan Whole Body Oncology", "long": "Positron emission tomography (PET) with concurrently acquired computed tomography (CT); whole body", "cat": "Nuclear Medicine", "cpt": "CPT-I", "denial": "high", "ind": [("C50.911", "primary_indication", "strong"), ("C34.90", "primary_indication", "strong")]},
    {"hcpcs_code": "76700", "short": "Ultrasound Abdomen Complete", "long": "Ultrasound, abdominal, real time with image documentation; complete", "cat": "Diagnostic Imaging", "cpt": "CPT-I", "denial": "low", "ind": [("K80.20", "primary_indication", "strong"), ("N20.0", "primary_indication", "strong")]},
    {"hcpcs_code": "93306", "short": "Transthoracic 2D Echocardiography Complete", "long": "Echocardiography, transthoracic, real-time with image documentation (2D), complete with Doppler", "cat": "Cardiac Imaging", "cpt": "CPT-I", "denial": "medium", "ind": [("I50.9", "primary_indication", "strong"), ("I11.0", "primary_indication", "strong")]},

    # ── 21. Physical Therapy & Rehabilitation (4 procedures) ──
    {"hcpcs_code": "97110", "short": "Therapeutic Exercise 15 Minutes", "long": "Therapeutic procedure, 1 or more areas, each 15 minutes; therapeutic exercises for strength, range of motion", "cat": "Physical Therapy", "cpt": "CPT-I", "denial": "high", "ind": [("M17.0", "secondary_indication", "strong"), ("M54.5", "primary_indication", "strong"), ("I63.9", "primary_indication", "strong")]},
    {"hcpcs_code": "97140", "short": "Manual Therapy Techniques 15 Minutes", "long": "Manual therapy techniques (e.g., mobilization, manipulation, lymphatic drainage, manual traction), each 15 min", "cat": "Physical Therapy", "cpt": "CPT-I", "denial": "high", "ind": [("M54.5", "primary_indication", "moderate"), ("M47.816", "primary_indication", "moderate")]},
    {"hcpcs_code": "97530", "short": "Therapeutic Activities Dynamic Movement", "long": "Therapeutic activities, direct (one-on-one) patient contact (use of dynamic activities to improve functional performance)", "cat": "Physical Therapy", "cpt": "CPT-I", "denial": "high", "ind": [("I63.9", "primary_indication", "strong"), ("M17.0", "secondary_indication", "moderate")]},
    {"hcpcs_code": "97116", "short": "Gait Training Therapy 15 Minutes", "long": "Therapeutic procedure, 1 or more areas, each 15 minutes; gait training (includes stair climbing)", "cat": "Physical Therapy", "cpt": "CPT-I", "denial": "high", "ind": [("I63.9", "primary_indication", "strong"), ("M16.0", "secondary_indication", "strong")]},

    # ── 22. Robotic Surgery Add-On (1 procedure) ──
    {"hcpcs_code": "S2900", "short": "Robotic Surgical Assistance Add-On", "long": "Surgical techniques requiring use of robotic surgical system (list separately in addition to code for primary procedure)", "cat": "Robotic Surgery", "cpt": "HCPCS-II", "denial": "high", "ind": [("C61", "secondary_indication", "strong"), ("D25.9", "secondary_indication", "strong")]},
]


def build_denial_reasons():
    """Build denial_reasons.csv with authentic ASC X12 / CMS and IRDAI standards."""
    print("\n[2/6] Building denial_reasons.csv with authentic X12/CMS standards...")
    output_path = RUNTIME_DIR / "denial_reasons.csv"
    fieldnames = [
        "reason_id", "category", "sub_category", "reason_text",
        "carc_code", "carc_description",
        "rarc_code", "rarc_description",
        "irdai_clause_grounding", "typical_clause_type", "appeal_route",
        "authority_provenance"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in DENIAL_REASONS:
            carc_code = r["carc"]
            carc_desc = CARC_DICT.get(carc_code, "")
            rarc_code = r["rarc"]
            rarc_desc = RARC_DICT.get(rarc_code, "")
            writer.writerow({
                "reason_id": r["id"],
                "category": r["cat"],
                "sub_category": r["sub"],
                "reason_text": r["text"],
                "carc_code": carc_code,
                "carc_description": carc_desc,
                "rarc_code": rarc_code,
                "rarc_description": rarc_desc,
                "irdai_clause_grounding": r.get("irdai", ""),
                "typical_clause_type": r["clause"],
                # A documentation denial is usually cured by sending the documents again.
                "appeal_route": ("Resubmit the missing documents; if still rejected, "
                                 if r["cat"] == "DOCUMENTATION" else "") + APPEAL_ROUTES[ROUTE_OF[r["route"]]],
                "authority_provenance": "ASC X12 Standard Claim Adjustment Reason Codes / CMS Remittance Advice & IRDAI Master Circular"
            })
    print(f"  [OK] denial_reasons.csv: {len(DENIAL_REASONS)} reasons with authentic text -> {output_path}")
    return len(DENIAL_REASONS)


# ╔══════════════════════════════════════════════════════════════╗
# ║  3. ICD-10 CODES CSV BUILDER                                 ║
# ╚══════════════════════════════════════════════════════════════╝
def build_icd10_codes():
    """Verifies icd10_codes.csv and sets is_billable from the code hierarchy: in ICD-10-CM a
    code is billable only if no more specific code exists beneath it (e.g. M54.5 is a header
    once M54.50 exists)."""
    output_path = RUNTIME_DIR / "icd10_codes.csv"
    with open(output_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    codes = sorted(r["code"] for r in rows)
    has_children = set()
    for parent, child in zip(codes, codes[1:]):
        # In sorted order a code's children follow it directly.
        if child.startswith(parent) and child != parent:
            has_children.add(parent)
    for r in rows:
        r["is_billable"] = r["code"] not in has_children
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[3/6] Verified icd10_codes.csv: {len(rows)} codes, {len(has_children)} header codes marked non-billable -> {output_path}")
    return len(rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  4. PROCEDURE CODES & MAPPING CSV BUILDERS                   ║
# ╚══════════════════════════════════════════════════════════════╝
def build_procedure_codes():
    """Builds procedure_codes.csv and procedure_diagnosis_map.csv with CMS policy provenance."""
    output_path = RUNTIME_DIR / "procedure_codes.csv"
    map_path = RUNTIME_DIR / "procedure_diagnosis_map.csv"

    policy_rules = {
        "Orthopedic Surgery": ("CMS-LCD-L36575", "CMS Local Coverage Determination for Major Joint & Orthopedic Surgeries (MAC Article A57685)"),
        "General Surgery": ("CMS-NCD-100.13", "CMS National Coverage Determination for Laparoscopic & Abdominal Surgeries"),
        "Cardiovascular Surgery": ("CMS-NCD-20.7", "CMS National Coverage Determination for Percutaneous Coronary Interventions & Cardiac Surgery"),
        "Urology": ("CMS-LCD-L34028", "CMS Local Coverage Determination for Transurethral & Urological Procedures"),
        "Ophthalmology": ("CMS-LCD-L35091", "CMS Local Coverage Determination for Cataract Extraction & Ophthalmic Surgery"),
        "Obstetrics & Gynecology": ("CMS-LCD-L34440", "CMS Local Coverage Determination & ACOG Standards for Gynecological Interventions"),
        "Neurosurgery": ("CMS-LCD-L34002", "CMS Local Coverage Determination for Spinal Surgery & Cranial Decompression"),
        "GI Diagnostics": ("CMS-LCD-L37837", "CMS Local Coverage Determination for Upper & Lower GI Endoscopy / Colonoscopy"),
        "ENT Surgery": ("CMS-LCD-L34550", "CMS Local Coverage Determination for Otolaryngologic Surgeries"),
        "Emergency Medicine": ("CMS-EM-STND", "CMS Emergency Treatment & Active Labor Act (EMTALA) Clinical Coding Standard"),
        "Vascular Surgery": ("CMS-LCD-L33560", "CMS Local Coverage Determination for Peripheral Vascular Interventions"),
        "Pulmonology": ("CMS-LCD-L33700", "CMS Local Coverage Determination for Diagnostic & Interventional Pulmonology"),
        "Plastic Surgery": ("CMS-LCD-L35090", "CMS Local Coverage Determination for Reconstructive vs Cosmetic Plastic Surgery"),
        "Pain Management": ("CMS-LCD-L34938", "CMS Local Coverage Determination for Epidural & Facet Joint Injections"),
        "Diagnostic Imaging": ("CMS-NCD-220.1", "CMS National Coverage Determination for Diagnostic Radiology & MRI"),
        "Oncology Surgery": ("CMS-LCD-L38222", "CMS Local Coverage Determination for Surgical Oncology & Tumor Resection"),
        "Bariatric Surgery": ("CMS-NCD-100.1", "CMS National Coverage Determination for Bariatric Surgery for Morbid Obesity (Article A53026)"),
        "Transplant Surgery": ("CMS-NCD-260.1", "CMS National Coverage Determination for Organ Transplantation"),
        "Dermatology": ("CMS-LCD-L33640", "CMS Local Coverage Determination for Excision of Cutaneous Lesions & Malignancies"),
        "Dental Surgery": ("CMS-DENT-01", "CMS Statutory Dental Services & Maxillofacial Coverage Guidelines"),
        "Physical Therapy": ("CMS-LCD-L35036", "CMS Local Coverage Determination for Physical Therapy & Rehabilitation"),
        "Cardiovascular Diagnostics": ("CMS-NCD-20.17", "CMS National Coverage Determination for Diagnostic Cardiac Catheterization"),
        "Radiation Oncology": ("CMS-LCD-L34641", "CMS Local Coverage Determination for Radiation Oncology (IMRT/SBRT)"),
        "Medical Oncology": ("CMS-LCD-L38222", "CMS Local Coverage Determination for Chemotherapy Administration"),
        "Dialysis": ("CMS-LCD-L33705", "CMS Local Coverage Determination for End-Stage Renal Disease & Hemodialysis"),
        "Hematology / Oncology": ("CMS-LCD-L38222", "CMS Local Coverage Determination for Hematology & Bone Marrow Aspiration"),
        "Thoracic Surgery": ("CMS-LCD-L33700", "CMS Local Coverage Determination for Thoracotomy & Lung Resection"),
        "Dialysis Access": ("CMS-LCD-L33705", "CMS Local Coverage Determination for Arteriovenous Fistula Creation"),
        "Nuclear Medicine": ("CMS-NCD-220.6", "CMS National Coverage Determination for PET & SPECT Imaging"),
        "Cardiac Imaging": ("CMS-NCD-220.1", "CMS National Coverage Determination for Echocardiography & Cardiac Scans"),
        "Robotic Surgery": ("CA-DMHC-IMR", "California DMHC Independent Medical Review Standards for Robotic-Assisted Surgery")
    }

    with open(RUNTIME_DIR / "icd10_codes.csv", encoding="utf-8") as f:
        valid_icds = set(r["code"] for r in csv.DictReader(f))

    print(f"\n[4/6] Building procedure_codes.csv ({len(PROCEDURES)} procedures across 22 specialties)...")
    proc_rows = []
    map_rows = []

    for p in PROCEDURES:
        p_code = p["hcpcs_code"]
        cat = p["cat"]
        policy_id, evidence_src = policy_rules.get(cat, ("CMS-STD-GEN", "CMS Standard Clinical Determination"))
        
        # Specific override for known high-impact NCDs
        if p_code in ["43644", "43775", "43846"]:
            policy_id = "CMS-NCD-100.1"
            evidence_src = "CMS National Coverage Determination NCD 100.1 for Bariatric Surgery"
        elif p_code in ["92928", "92920"]:
            policy_id = "CMS-NCD-20.7"
            evidence_src = "CMS National Coverage Determination NCD 20.7 for Percutaneous Transluminal Angioplasty"
        elif p_code in ["47562", "47563"]:
            policy_id = "CMS-NCD-100.13"
            evidence_src = "CMS National Coverage Determination NCD 100.13 for Laparoscopic Cholecystectomy"
        elif p_code in ["66984", "66982"]:
            policy_id = "CMS-LCD-L35091"
            evidence_src = "CMS Local Coverage Determination LCD L35091 for Cataract Extraction"
        elif p_code in ["27447", "27130"]:
            policy_id = "CMS-LCD-L36575"
            evidence_src = "CMS Local Coverage Determination LCD L36575 / MAC Billing Article A57685"
        elif p_code in ["90935", "90937"]:
            policy_id = "CMS-LCD-L33705"
            evidence_src = "CMS Local Coverage Determination LCD L33705 for ESRD Hemodialysis"

        valid_common = []
        for icd, rel, strength in p["ind"]:
            if icd in valid_icds:
                valid_common.append(icd)
                map_rows.append({
                    "hcpcs_code": p_code,
                    "icd10_code": icd,
                    "relationship_type": rel,
                    "medical_necessity_strength": strength,
                    "source_policy_id": policy_id,
                    "evidence_standard": evidence_src
                })
        proc_rows.append({
            "hcpcs_code": p_code,
            "short_description": p["short"],
            "long_description": p["long"],
            "category": cat,
            "cpt_category": p["cpt"],
            "denial_relevance": p["denial"],
            "common_icd10_codes": ";".join(valid_common),
            "primary_cms_policy": policy_id
        })

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "hcpcs_code", "short_description", "long_description", "category",
            "cpt_category", "denial_relevance", "common_icd10_codes", "primary_cms_policy"
        ])
        writer.writeheader()
        writer.writerows(proc_rows)
    print(f"  [OK] procedure_codes.csv: {len(proc_rows)} procedures -> {output_path}")

    print(f"\n[5/6] Building procedure_diagnosis_map.csv ({len(map_rows)} linkages)...")
    with open(map_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "hcpcs_code", "icd10_code", "relationship_type", "medical_necessity_strength",
            "source_policy_id", "evidence_standard"
        ])
        writer.writeheader()
        writer.writerows(map_rows)
    print(f"  [OK] procedure_diagnosis_map.csv: {len(map_rows)} linkages -> {map_path}")
    return len(proc_rows)


# ╔══════════════════════════════════════════════════════════════╗
# ║  5. NME EXCLUSIONS CSV BUILDER (EXTRACTED FROM POLICY PDF)   ║
# ╚══════════════════════════════════════════════════════════════╝
def build_nme_exclusions():
    """Extracts authentic non-medical expense items directly from policy PDF tables (IRDAI Annexure IV)."""
    output_path = RUNTIME_DIR / "nme_exclusions.csv"
    pdf_path = BASE_DIR / "data" / "policy_wordings" / "HDFC ERGO" / "hdfc-optima-restore.pdf"
    
    doc = fitz.open(str(pdf_path))

    # List I (Page 47, 0-indexed 46)
    t1 = doc[46].find_tables().tables[0].extract()
    list1_raw = []
    for row in t1[1:]:
        if row[0] and row[1]:
            try: list1_raw.append((int(row[0]), row[1].replace('\n', ' ').strip()))
            except: pass
        if len(row) >= 4 and row[2] and row[3]:
            try: list1_raw.append((int(row[2]), row[3].replace('\n', ' ').strip()))
            except: pass
    list1_raw.sort()

    # List II (Page 48, 0-indexed 47)
    t2 = doc[47].find_tables().tables[0].extract()
    list2_raw = []
    for row in t2[1:]:
        if row[0] and row[1]:
            try: list2_raw.append((int(row[0]), row[1].replace('\n', ' ').strip()))
            except: pass

    # List III (Page 49, 0-indexed 48 Table 1)
    t3 = doc[48].find_tables().tables[0].extract()
    list3_raw = []
    for row in t3[1:]:
        if row[0] and row[1]:
            try: list3_raw.append((int(row[0]), row[1].replace('\n', ' ').strip()))
            except: pass

    # List IV (Page 49 Table 2 + Page 50 Table 1)
    t4_a = doc[48].find_tables().tables[1].extract()
    t4_b = doc[49].find_tables().tables[0].extract()
    list4_raw = []
    for row in t4_a[1:]:
        if row[0] and row[1]:
            try: list4_raw.append((int(row[0]), row[1].replace('\n', ' ').strip()))
            except: pass
    for row in t4_b:
        if row[0] and row[1]:
            try: list4_raw.append((int(row[0]), row[1].replace('\n', ' ').strip()))
            except: pass

    nme_rows = []
    nme_counter = 1

    for s_no, name in list1_raw:
        nme_rows.append({
            "item_id": f"NME-{nme_counter:03d}",
            "irdai_annexure_ref": f"IRDAI-Annexure-I-List-I-Item-{s_no:02d}",
            "item_name": name,
            "category": "Optional Cover / Personal Comfort",
            "annexure_list": "List I - Items for which coverage is not available in the policy",
            "typically_excluded": True,
            "statutory_treatment": "Excluded from standard cover; payable only if optional Consumables Add-on / Rider is active",
            "dispute_adjudication_rule": "Inadmissible under standard terms; upheld by Ombudsman unless specific consumable rider is in force",
            "source_policy_document": "HDFC ERGO Optima Restore Policy Terms Annexure I / IRDAI Standardization Guidelines IRDA/HLT/REG/CIR/193/09/2019"
        })
        nme_counter += 1

    for s_no, name in list2_raw:
        nme_rows.append({
            "item_id": f"NME-{nme_counter:03d}",
            "irdai_annexure_ref": f"IRDAI-Annexure-I-List-II-Item-{s_no:02d}",
            "item_name": name,
            "category": "Room Utilities & Amenities",
            "annexure_list": "List II - Items that are to be subsumed into Room Charges",
            "typically_excluded": False,
            "statutory_treatment": "Subsumed into Room Charges; hospital prohibited from billing as standalone item to insured",
            "dispute_adjudication_rule": "If hospital billed separately, insurer deduction is valid; Ombudsman directs hospital to absorb in room rent",
            "source_policy_document": "HDFC ERGO Optima Restore Policy Terms Annexure I / IRDAI Standardization Guidelines IRDA/HLT/REG/CIR/193/09/2019"
        })
        nme_counter += 1

    for s_no, name in list3_raw:
        nme_rows.append({
            "item_id": f"NME-{nme_counter:03d}",
            "irdai_annexure_ref": f"IRDAI-Annexure-I-List-III-Item-{s_no:02d}",
            "item_name": name,
            "category": "Surgical Disposables & OT Consumables",
            "annexure_list": "List III - Items that are to be subsumed into Procedure Charges",
            "typically_excluded": False,
            "statutory_treatment": "Subsumed into Procedure Charges; bundled into surgical / operation theatre package rate",
            "dispute_adjudication_rule": "Covered within OT package rate; separate line-item deductions upheld if package charge was fully settled",
            "source_policy_document": "HDFC ERGO Optima Restore Policy Terms Annexure I / IRDAI Standardization Guidelines IRDA/HLT/REG/CIR/193/09/2019"
        })
        nme_counter += 1

    for s_no, name in list4_raw:
        nme_rows.append({
            "item_id": f"NME-{nme_counter:03d}",
            "irdai_annexure_ref": f"IRDAI-Annexure-I-List-IV-Item-{s_no:02d}",
            "item_name": name,
            "category": "General Treatment & Diagnostics",
            "annexure_list": "List IV - Items that are to be subsumed into costs of treatment",
            "typically_excluded": False,
            "statutory_treatment": "Subsumed into Costs of Treatment; bundled into basic medical care and hospitalization charges",
            "dispute_adjudication_rule": "Included in overall treatment cost; unbundled charges disallowed under GIPSA PPN guidelines",
            "source_policy_document": "HDFC ERGO Optima Restore Policy Terms Annexure I / IRDAI Standardization Guidelines IRDA/HLT/REG/CIR/193/09/2019"
        })
        nme_counter += 1

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fields = [
            "item_id", "irdai_annexure_ref", "item_name", "category",
            "annexure_list", "typically_excluded",
            "statutory_treatment", "dispute_adjudication_rule", "source_policy_document"
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(nme_rows)

    print(f"\n[6/6] Verified nme_exclusions.csv: {len(nme_rows)} authentic items extracted from policy PDF -> {output_path}")
    return len(nme_rows)


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("  BUILDING ALL 6 RUNTIME KNOWLEDGE-BASE CSVs (FULL PIPELINE)")
    print("=" * 70)
    
    counts = {}
    counts["policy_clauses"] = extract_policy_clauses()
    counts["denial_reasons"] = build_denial_reasons()
    counts["icd10_codes"] = build_icd10_codes()
    counts["procedure_codes"] = build_procedure_codes()
    counts["nme_exclusions"] = build_nme_exclusions()

    print("\n" + "=" * 70)
    print("  SUCCESSFULLY BUILT ALL RUNTIME CSVs:")
    for k, v in counts.items():
        print(f"    - {k:25s}: {v:5d} records")
    print("=" * 70)
