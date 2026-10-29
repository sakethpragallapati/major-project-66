"""
build_golden_datasets.py
========================
Builds the 7 Golden Evaluation Benchmark JSONs for the 3-Tier DeepEval evaluation suite.

Every ground-truth value is traceable either to the case input itself (letter, clinical
note, dates) or to a record in the runtime knowledge base (data/runtime/*.csv). Each
builder checks its own invariants and stops with an error if a case breaks them.

Output:
  data/golden/
  ├── G1_golden_intake_entities.json         (100 cases)
  ├── G2_golden_clause_retrieval.json        (100 queries)
  ├── G3_golden_clinical_evidence.json       (60 cases)
  ├── G4_golden_chronology_ped.json          (60 cases)
  ├── G5_golden_reasoning_toulmin.json       (80 cases)
  ├── G6_golden_appeal_drafts.json           (40 cases)
  └── G7_golden_denial_router.json           (140 cases)
"""

import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timedelta

# Ensure UTF-8 console output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────
BASE_DIR = Path(r"c:\Users\Saketh\Desktop\Major Project")
GOLDEN_DIR = BASE_DIR / "data" / "golden"
GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
RUNTIME_DIR = BASE_DIR / "data" / "runtime"

random.seed(42)  # Reproducibility

# All generated dates fall on or before this day, so no case describes the future.
LATEST_DATE = datetime(2025, 12, 31)

# IRDAI Master Circular on Health Insurance Business (2024): after 60 months of continuous
# coverage a claim cannot be contested on grounds of non-disclosure, except proven fraud.
MORATORIUM_MONTHS = 60
DAYS_PER_MONTH = 30.4375

# ──────────────────────────────────────────────────────────────
# Helper Data Pools
# ──────────────────────────────────────────────────────────────
INDIAN_NAMES = [
    "Ramesh Kumar", "Priya Sharma", "Suresh Patel", "Anita Devi", "Vikram Singh",
    "Meera Reddy", "Rajesh Gupta", "Sunita Mishra", "Arun Nair", "Kavita Joshi",
    "Mahesh Yadav", "Deepa Iyer", "Sanjay Desai", "Lakshmi Rao", "Amit Verma",
    "Pooja Kapoor", "Ravi Menon", "Neha Agarwal", "Prakash Choudhury", "Geeta Pillai",
    "Venkatesh Murthy", "Asha Tiwari", "Dinesh Saxena", "Rekha Bhat", "Kishore Sinha",
    "Madhavi Kulkarni", "Harish Pandey", "Savita Hegde", "Gopal Mehta", "Usha Chauhan",
    "Naresh Biswas", "Padma Srinivasan", "Alok Tripathi", "Jaya Kamath", "Mohan Das",
    "Swati Ghosh", "Pavan Kumar B", "Kamala Subramaniam", "Vijay Khanna", "Indira Rajan",
    "Ashok Malhotra", "Saroja Nambiar", "Rajeev Bansal", "Vanaja Kurian", "Tarun Bhatt",
    "Leela Krishnan", "Sunil Jha", "Rani Mukherjee", "Girish Kaul", "Hema Sundaram",
]

HOSPITALS = [
    "Apollo Hospitals, Hyderabad", "Fortis Hospital, Gurgaon", "Max Super Speciality, Saket",
    "Manipal Hospital, Bangalore", "AIIMS, New Delhi", "Medanta, Gurgaon",
    "Kokilaben Dhirubhai Ambani, Mumbai", "Narayana Health, Bangalore",
    "Tata Memorial Hospital, Mumbai", "CMC Vellore", "KIMS, Hyderabad",
    "Yashoda Hospital, Hyderabad", "Lilavati Hospital, Mumbai", "Ruby Hall Clinic, Pune",
    "Artemis Hospital, Gurgaon", "BLK-MAX, New Delhi", "Global Hospitals, Hyderabad",
    "Amrita Hospital, Kochi", "SRM Institute, Chennai", "Aster MIMS, Kozhikode",
]

DOCTORS = ["Sen", "Mehta", "Iyer", "Sharma", "Reddy", "Gupta", "Patel", "Nair", "Rao", "Menon"]

DATA_DIR = BASE_DIR / "data"
POLICY_DIR = DATA_DIR / "policy_wordings"

if str(DATA_DIR) not in sys.path:
    sys.path.insert(0, str(DATA_DIR))

try:
    from policy_discovery import get_all_products_from_policies, discover_policy_documents
except ImportError:
    from data.policy_discovery import get_all_products_from_policies, discover_policy_documents

# Dynamically discovered products and insurers from data/policy_wordings/
ALL_PRODUCTS = get_all_products_from_policies(POLICY_DIR)
INSURER_OF = {product: insurer for insurer, product, _ in ALL_PRODUCTS}

# (procedure, ICD-10-CM indication, CPT/HCPCS code, specialty)
PROCEDURES_MN = [
    ("Total Knee Replacement", "M17.11", "27447", "Orthopedic Surgery"),
    ("Total Hip Replacement", "M16.11", "27130", "Orthopedic Surgery"),
    ("Lumbar Spinal Fusion", "M47.816", "22612", "Orthopedic Surgery"),
    ("Coronary Artery Bypass Graft", "I25.10", "33533", "Cardiovascular Surgery"),
    ("Percutaneous Coronary Stent", "I25.110", "92928", "Cardiovascular Surgery"),
    ("Aortic Valve Replacement", "I35.0", "33405", "Cardiovascular Surgery"),
    ("Laparoscopic Sleeve Gastrectomy", "E66.01", "43775", "Bariatric Surgery"),
    ("Mastectomy (Breast Cancer)", "C50.911", "19303", "Oncology Surgery"),
    ("IMRT Radiation Therapy", "C34.90", "77385", "Radiation Oncology"),
    ("Craniotomy for Tumor", "C71.9", "61510", "Neurosurgery"),
    ("Cervical Spinal Fusion", "M47.812", "22551", "Orthopedic Surgery"),
    ("Renal Transplant", "N18.6", "50360", "Transplant Surgery"),
    ("Liver Transplant", "K74.60", "47135", "Transplant Surgery"),
    ("Robotic Prostatectomy", "C61", "55866", "Urology"),
    ("Septoplasty", "J34.2", "30520", "ENT Surgery"),
]

# (condition, ICD-10-CM code, applicable PED waiting period in months)
PED_CONDITIONS = [
    ("Essential Hypertension", "I10", 36),
    ("Type 2 Diabetes Mellitus", "E11.9", 36),
    ("Hypothyroidism", "E03.9", 36),
    ("Chronic Kidney Disease", "N18.30", 48),
    ("Coronary Artery Disease", "I25.10", 48),
    ("Hypertensive Nephropathy", "I12.0", 36),
    ("Diabetic Retinopathy", "E11.311", 48),
    ("COPD", "J44.1", 48),
    ("Osteoarthritis (Bilateral Knee)", "M17.0", 24),
    ("Benign Prostatic Hyperplasia", "N40.0", 24),
    ("Atrial Fibrillation", "I48.91", 48),
    ("Epilepsy", "G40.909", 48),
    ("Hyperlipidemia", "E78.5", 36),
    ("Heart Failure", "I50.9", 48),
    ("Calculus of Kidney", "N20.0", 24),
]

CATEGORIES = [
    "MEDICAL_NECESSITY",
    "PRE_EXISTING_WAITING_PERIOD",
    "POLICY_EXCLUSION",
    "FINANCIAL_LIMIT",
    "DOCUMENTATION",
    "ADMINISTRATIVE_PROCEDURAL",
    "ELIGIBILITY_COVERAGE",
]

# Indian grievance forums, in the order a policyholder escalates
FORUMS = [
    "Grievance Redressal Officer of the insurer",
    "Insurance Ombudsman",
    "IRDAI Bima Bharosa portal",
    "District Consumer Disputes Redressal Commission",
]


def random_date(start_year=2020, end_year=2024):
    start = datetime(start_year, 1, 1)
    end = min(datetime(end_year, 12, 31), LATEST_DATE)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def format_date(dt):
    return dt.strftime("%Y-%m-%d")


def random_amount(low=50000, high=1500000):
    return round(random.randint(low, high) / 1000) * 1000


def months_between(start, end):
    return round((end - start).days / DAYS_PER_MONTH, 1)


def _check(condition, case_id, message):
    if not condition:
        raise ValueError(f"{case_id}: {message}")


# ──────────────────────────────────────────────────────────────
# Runtime knowledge base (ground truth for G1, G2, G6 comes from here)
# ──────────────────────────────────────────────────────────────
def _read_csv(name):
    with open(RUNTIME_DIR / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


CLAUSES = _read_csv("policy_clauses.csv")
ICD_CODES = {r["code"] for r in _read_csv("icd10_codes.csv")}
PROCEDURE_CODES = {r["hcpcs_code"] for r in _read_csv("procedure_codes.csv")}

for _proc, _icd, _cpt, _ in PROCEDURES_MN:
    assert _icd in ICD_CODES, f"ICD-10 code {_icd} ({_proc}) missing from icd10_codes.csv"
    assert _cpt in PROCEDURE_CODES, f"Procedure code {_cpt} ({_proc}) missing from procedure_codes.csv"
for _cond, _icd, _ in PED_CONDITIONS:
    assert _icd in ICD_CODES, f"ICD-10 code {_icd} ({_cond}) missing from icd10_codes.csv"

_TEXT_COUNTS = Counter(r["clause_text"].strip() for r in CLAUSES)
_CLAUSE_NUMBER = re.compile(r"^(\d+(\.\d+)*\.?|Code-?\s?Excl\s?\d+)$", re.I)


def _is_tabular(text):
    """Benefit tables flatten into text where the same phrase repeats across columns."""
    words = text.lower().split()
    trigrams = Counter(" ".join(words[i:i + 3]) for i in range(len(words) - 2))
    return any(n >= 3 for n in trigrams.values())


def _is_citable(row):
    """A clause can serve as ground truth only if it has a real clause number, is not a
    duplicate, a table-of-contents line or a flattened table, and is a reasonable length."""
    text = row["clause_text"]
    return (bool(_CLAUSE_NUMBER.match(row["clause_number"].strip()))
            and _TEXT_COUNTS[text.strip()] == 1
            and not re.search(r"\.{5,}", text)
            and not _is_tabular(text)
            and 60 <= len(text) <= 1500)


CITABLE = [r for r in CLAUSES if _is_citable(r)]

# topic -> (pattern, label used in letters, retrieval question)
TOPICS = {
    "cosmetic": (r"cosmetic|plastic surgery", "Cosmetic or Plastic Surgery Exclusion",
                 "Is cosmetic or plastic surgery covered under {product}, and are there any exceptions?"),
    "obesity": (r"obesity|bariatric|weight control", "Obesity and Weight Control Exclusion",
                "Will {product} pay for bariatric surgery for morbid obesity?"),
    "maternity": (r"maternity|pregnan|childbirth", "Maternity Expenses Exclusion",
                  "Are maternity and childbirth expenses covered under {product}?"),
    "dental": (r"\bdental\b", "Dental Treatment Exclusion",
               "Is dental treatment covered under {product} when it is not caused by an accident?"),
    "infertility": (r"infertil|sterility", "Infertility Treatment Exclusion",
                    "Does {product} cover infertility or sterility treatment?"),
    "adventure": (r"hazardous|adventure sport", "Hazardous or Adventure Sports Exclusion",
                  "Is an injury from an adventure sport covered under {product}?"),
    "unproven": (r"unproven|experimental", "Unproven or Experimental Treatment Exclusion",
                 "Does {product} pay for unproven or experimental treatment?"),
    "ped_wait": (r"pre-existing disease", "Pre-Existing Disease Waiting Period",
                 "What is the waiting period for a pre-existing disease under {product}?"),
    "specified_wait": (r"specified disease|specific waiting|24 months", "Specified Disease Waiting Period",
                       "Which illnesses have a specific waiting period under {product}, and how long is it?"),
    "initial_wait": (r"30 days|first 30|initial waiting", "Initial 30-Day Waiting Period",
                     "Is an illness in the first 30 days of {product} covered?"),
    "room_rent": (r"room rent|room charges|single private", "Room Rent Limit",
                  "What room rent limit applies under {product}, and what happens if I choose a higher room?"),
    "nme": (r"non-medical|consumables|annexure", "Non-Medical Expenses",
            "Which non-medical items or consumables are not payable under {product}?"),
    "daycare": (r"day care", "Day Care Treatment",
                "Is a day care procedure needing less than 24 hours of hospitalization covered under {product}?"),
    "ayush": (r"ayush", "AYUSH Treatment",
              "Does {product} cover Ayurveda, Unani, Siddha or Homeopathy (AYUSH) treatment?"),
    "modern": (r"robotic|modern treatment|immunotherap", "Modern Treatment Methods",
               "Are robotic surgery and other modern treatments covered under {product}?"),
    "moratorium": (r"moratorium|sixty months|60 continuous months|eight years", "Moratorium Period",
                   "After how many years can {product} no longer contest a claim for non-disclosure?"),
    "investigation": (r"investigation|evaluation", "Investigation and Evaluation Exclusion",
                      "Is a hospital stay only for diagnostic investigation covered under {product}?"),
    "rest_cure": (r"rest cure|rehabilitation|respite", "Rest Cure and Rehabilitation Exclusion",
                  "Does {product} pay for rest cure or rehabilitation stays?"),
    "war": (r"\bwar\b|nuclear", "War and Nuclear Risk Exclusion",
            "Are injuries from war or nuclear events covered under {product}?"),
    "grace": (r"grace period", "Grace Period on Renewal",
              "Is a hospitalization during the renewal grace period covered under {product}?"),
    "portability": (r"portab", "Portability",
                    "If I port my policy to {product}, do I keep credit for waiting periods already served?"),
    "co_pay": (r"co-pay", "Co-Payment Deduction",
               "Is there a co-payment deduction on claims under {product}?"),
    "ambulance": (r"ambulance", "Ambulance Cover",
                  "How much does {product} pay for road ambulance charges?"),
    "pre_post": (r"pre-hospitali|post-hospitali", "Pre- and Post-Hospitalization Expenses",
                 "For how many days before and after admission are expenses covered under {product}?"),
    "organ_donor": (r"organ donor", "Organ Donor Expenses",
                    "Are the organ donor's hospital expenses covered under {product}?"),
    "domiciliary": (r"domiciliary", "Domiciliary Hospitalization",
                    "Is treatment taken at home (domiciliary hospitalization) covered under {product}?"),
}


EXCLUSION_TOPICS = {"cosmetic", "obesity", "maternity", "dental", "infertility", "adventure", "unproven",
                    "investigation", "rest_cure", "war"}
WAITING_TOPICS = {"ped_wait", "specified_wait", "initial_wait", "moratorium"}


def _best_clause(product, topic):
    """Pick the clause of `product` that discusses `topic` most directly: the clause type
    should fit the question, the topic must appear early in the text, and
    exception-bearing clauses are preferred."""
    pattern = TOPICS[topic][0]
    wanted = "EXCLUSION" if topic in EXCLUSION_TOPICS else "WAITING_PERIOD" if topic in WAITING_TOPICS else None
    hits = []
    for r in CITABLE:
        if r["product_name"] != product:
            continue
        m = re.search(pattern, r["clause_text"], re.I)
        if m:
            type_mismatch = wanted is not None and r["clause_type"] != wanted
            hits.append((m.start() > 150, type_mismatch, r["has_exception"] != "True", m.start(), r["clause_id"], r))
    return min(hits)[-1] if hits else None


TOPIC_CLAUSES = {}
for _, _product, _ in ALL_PRODUCTS:
    for _topic in TOPICS:
        _clause = _best_clause(_product, _topic)
        if _clause:
            TOPIC_CLAUSES[(_product, _topic)] = _clause


def clause_for(product, topics):
    """Return (topic, clause) for the first topic in `topics` that `product` covers."""
    for t in topics:
        if (product, t) in TOPIC_CLAUSES:
            return t, TOPIC_CLAUSES[(product, t)]
    return None, None


def snippet(text, pattern, width=380):
    """Verbatim passage of `text` around the first match of `pattern`, cut at word boundaries."""
    m = re.search(pattern, text, re.I)
    start = 0 if not m else max(0, m.start() - 120)
    if start:
        space = text.find(" ", start)
        start = space + 1 if 0 <= space < m.start() else start
    end = min(len(text), start + width)
    if end < len(text):
        space = text.rfind(" ", start, end)
        end = space if space > start else end
    return text[start:end].strip()


def clause_label(row):
    number = row["clause_number"].strip().rstrip(".")
    return number if number.lower().startswith("code") else f"Clause {number}"


# ╔══════════════════════════════════════════════════════════════╗
# ║  G1: GOLDEN INTAKE ENTITIES                                 ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g1():
    print("\n[G1] Building golden_intake_entities.json (100 cases)...")
    cases = []

    denial_templates = [
        "{insurer}\nDate: {denial_date}\nRef: {claim_id}\n\nDear {name},\nWith reference to your hospitalization on {admission_date} at {hospital} for {procedure} (ICD-10: {icd10}), your claim for Rs {amount} under {product} has been repudiated under {clause} ({clause_desc}). You may file an appeal within 30 days of this letter.",
        "{insurer} | Claim Repudiation Letter\nLetter date: {denial_date}\nClaim Reference: {claim_id}\nDear {name},\nThis is to inform you that your health insurance claim under Policy No. {policy_no} ({product}) for treatment at {hospital} has been denied.\nProcedure: {procedure}\nDiagnosis Code: {icd10}\nClaimed Amount: Rs. {amount}\nDenial Reason: {clause} - {clause_desc}\nDate of Admission: {admission_date}\nPlease contact your TPA for further details.",
        "Subject: Claim Repudiation Notice - {claim_id}\nIssued by: {insurer}\nDate: {denial_date}\n\nDear Mr./Ms. {name},\n\nWe regret to inform you that your claim bearing reference number {claim_id} for {procedure} at {hospital}, admitted on {admission_date}, has been repudiated.\n\nThe claim amount of Rs. {amount} is not payable under {product} due to {clause} ({clause_desc}). The diagnosis code {icd10} has been reviewed by our medical team.\n\nAppeal window: 30 days from the date of this letter.",
        "REPUDIATION NOTICE\n{insurer}\nDate of letter: {denial_date}\n\nTo: {name}\nPolicy: {product} | Claim: {claim_id}\nHospital: {hospital}\nDate of Hospitalization: {admission_date}\nProcedure/Treatment: {procedure} [{icd10}]\nBilled Amount: Rs. {amount}\n\nDenial Ground: Your claim has been denied under {clause}, which pertains to {clause_desc}, as per the policy terms and conditions.\n\nYou have the right to appeal this decision.",
        "{insurer}\n{denial_date}\n\nDear {name},\n\nYour claim {claim_id} for Rs. {amount}/- towards {procedure} performed on {admission_date} at {hospital} has been disallowed under your {product} policy.\n\nReason for Denial: {clause} - {clause_desc}\nICD-10 Code: {icd10}\n\nAs per IRDAI guidelines, you may approach the Insurance Ombudsman if you are dissatisfied with this decision.",
    ]

    procedure_topics = ["investigation", "unproven", "room_rent", "co_pay", "nme", "modern"]
    ped_topics = ["ped_wait", "specified_wait", "initial_wait"]

    for i in range(100):
        is_ped = i >= 50
        name = random.choice(INDIAN_NAMES)
        hospital = random.choice(HOSPITALS)
        insurer, product, code = random.choice(ALL_PRODUCTS)
        admission = random_date(2023, 2025)
        denial = admission + timedelta(days=random.randint(12, 45))
        if denial > LATEST_DATE:
            admission -= denial - LATEST_DATE
            denial = LATEST_DATE
        claim_id = f"CLM-{admission.year}-{random.randint(1000, 9999)}"
        policy_no = f"{code}/{random.randint(1000, 9999)}/{admission.year}"
        amount = random_amount()

        if is_ped:
            condition, icd10, _ = random.choice(PED_CONDITIONS)
            procedure = f"Treatment for {condition}"
            topics = random.sample(ped_topics, len(ped_topics))
        else:
            procedure, icd10, _, _ = random.choice(PROCEDURES_MN)
            topics = random.sample(procedure_topics, len(procedure_topics))
        topic, clause_row = clause_for(product, topics)
        while clause_row is None:  # this product has no citable clause on these topics
            insurer, product, code = random.choice(ALL_PRODUCTS)
            policy_no = f"{code}/{random.randint(1000, 9999)}/{admission.year}"
            topic, clause_row = clause_for(product, topics)
        clause = clause_label(clause_row)
        clause_desc = TOPICS[topic][1]

        raw_letter = random.choice(denial_templates).format(
            claim_id=claim_id, name=name, denial_date=format_date(denial),
            admission_date=format_date(admission), hospital=hospital, procedure=procedure,
            icd10=icd10, amount=f"{amount:,.0f}", clause=clause, clause_desc=clause_desc,
            product=product, policy_no=policy_no, insurer=insurer,
        )

        entities = {
            "claim_id": claim_id,
            "patient_name": name,
            "insurer": insurer,
            "policy_product": product,
            "admission_date": format_date(admission),
            "denial_date": format_date(denial),
            "hospital_name": hospital,
            "procedure": procedure,
            "icd10_code": icd10,
            "claimed_amount": float(amount),
            "cited_clause_raw": clause,
            "cited_clause_id": clause_row["clause_id"],
            "denial_category_hint": clause_desc,
        }
        case_id = f"G1-{i+1:03d}"
        for key, value in entities.items():
            if key == "cited_clause_id":
                continue
            shown = f"{value:,.0f}" if key == "claimed_amount" else str(value)
            _check(shown in raw_letter, case_id, f"{key}={shown!r} does not appear in the letter")

        cases.append({"case_id": case_id, "raw_letter_text": raw_letter, "ground_truth_entities": entities})

    _save_json(cases, "G1_golden_intake_entities.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G2: GOLDEN CLAUSE RETRIEVAL                                ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g2():
    print("\n[G2] Building golden_clause_retrieval.json (100 queries)...")
    clause_ids = {r["clause_id"] for r in CLAUSES}

    # Round-robin over topics so that the 100 queries cover as many topics as possible.
    by_topic = defaultdict(list)
    for (product, topic), row in sorted(TOPIC_CLAUSES.items()):
        by_topic[topic].append((product, row))
    for pairs in by_topic.values():
        random.shuffle(pairs)
    selected, used = [], set()
    while len(selected) < 100:
        progressed = False
        for topic in TOPICS:
            # A clause is used once, and so is a wording that several products share
            # (IRDAI standard text), so every query has its own passage.
            def taken(row):
                return {row["clause_id"], row["clause_text"], snippet(row["clause_text"], TOPICS[topic][0])} & used
            while by_topic[topic] and taken(by_topic[topic][-1][1]):
                by_topic[topic].pop()
            if by_topic[topic] and len(selected) < 100:
                product, row = by_topic[topic].pop()
                selected.append((topic, product, row))
                used.update((row["clause_id"], row["clause_text"], snippet(row["clause_text"], TOPICS[topic][0])))
                progressed = True
        if not progressed:
            raise ValueError(f"Only {len(selected)} citable product/topic pairs; need 100")

    cases = []
    for i, (topic, product, row) in enumerate(selected):
        pattern, _, question = TOPICS[topic]
        # Distractors: same product and clause type, but not about this topic.
        pool = [r for r in CITABLE if r["product_name"] == product and r["clause_id"] != row["clause_id"]
                and not re.search(pattern, r["clause_text"], re.I)]
        same_type = [r for r in pool if r["clause_type"] == row["clause_type"]] or pool
        distractors = [r["clause_id"] for r in random.sample(same_type, min(2, len(same_type)))]
        passage = snippet(row["clause_text"], pattern)

        case = {
            "query_id": f"G2-{i+1:03d}",
            "user_query": question.format(product=product),
            "product_name": product,
            "insurer": INSURER_OF[product],
            "topic": topic,
            "expected_clause_id": row["clause_id"],
            "expected_subclause": row["clause_number"].strip(),
            "clause_type": row["clause_type"],
            "has_exception": row["has_exception"] == "True",
            "exception_text": row["exception_text"],
            "ground_truth_context_snippet": passage,
            "distractor_clauses": distractors,
        }
        _check(case["expected_clause_id"] in clause_ids, case["query_id"], "expected clause not in clause base")
        _check(all(d in clause_ids for d in distractors), case["query_id"], "distractor not in clause base")
        _check(passage in row["clause_text"], case["query_id"], "snippet is not verbatim")
        cases.append(case)

    _check(len({c["user_query"] for c in cases}) == len(cases), "G2", "duplicate queries")
    _save_json(cases, "G2_golden_clause_retrieval.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G3: GOLDEN CLINICAL EVIDENCE                               ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g3():
    print("\n[G3] Building golden_clinical_evidence.json (60 cases)...")

    # Each note is assembled from sentences; every sentence that carries a checklist fact is
    # recorded as an evidence span, so the spans are verbatim by construction.
    def knee(p, overturn):
        if overturn:
            return {
                "intro": f"{p['age']}yo {p['gender']} with chronic {p['side']} knee pain.",
                "conservative": f"Pain unresponsive to {p['months']} months of physical therapy, intra-articular steroid injections and daily NSAIDs.",
                "severity": "Weight-bearing radiographs show Kellgren-Lawrence grade 4 osteoarthritis with bone-on-bone contact.",
                "physician": f"Orthopaedic surgeon Dr. {p['doctor']} certifies that total knee replacement is medically necessary.",
                "modalities": ["physical therapy", "intra-articular steroid injections", "NSAIDs"],
                "grade": "Kellgren-Lawrence grade 4 osteoarthritis",
            }
        return {
            "intro": f"{p['age']}yo {p['gender']} with intermittent {p['side']} knee pain for 3 months.",
            "conservative": None,
            "severity": "Radiographs show Kellgren-Lawrence grade 2 osteoarthritis with preserved joint space.",
            "physician": "Patient requests surgery for faster recovery; no trial of physiotherapy is documented.",
            "modalities": [],
            "grade": "Kellgren-Lawrence grade 2 osteoarthritis",
        }

    def spine(p, overturn):
        if overturn:
            return {
                "intro": f"{p['age']}yo {p['gender']} with low back pain radiating to the {p['side']} leg.",
                "conservative": f"Symptoms persist after {p['months']} months of physical therapy, epidural steroid injections and NSAIDs.",
                "severity": f"MRI shows severe foraminal stenosis at {p['level']} with {p['deficit']}.",
                "physician": f"Spine surgeon Dr. {p['doctor']} certifies that decompression and fusion are medically necessary.",
                "modalities": ["physical therapy", "epidural steroid injections", "NSAIDs"],
                "grade": "severe foraminal stenosis",
            }
        return {
            "intro": f"{p['age']}yo {p['gender']} with mechanical low back pain for 6 weeks.",
            "conservative": None,
            "severity": f"MRI shows mild disc bulge at {p['level']} without neural compression; neurological examination is normal.",
            "physician": "Fusion is requested before any course of physiotherapy has been tried.",
            "modalities": [],
            "grade": "mild disc bulge",
        }

    def cabg(p, overturn):
        if overturn:
            return {
                "intro": f"{p['age']}yo {p['gender']} with exertional angina, NYHA class III.",
                "conservative": f"Angina persists despite {p['months']} months of optimal medical therapy with antiplatelets, statins and beta-blockers.",
                "severity": f"Coronary angiography shows triple-vessel disease with LVEF {p['lvef']}%.",
                "physician": f"Cardiothoracic surgeon Dr. {p['doctor']} certifies that CABG is medically necessary.",
                "modalities": ["antiplatelets", "statins", "beta-blockers"],
                "grade": "triple-vessel disease",
            }
        return {
            "intro": f"{p['age']}yo {p['gender']} with stable angina, NYHA class I.",
            "conservative": None,
            "severity": "Coronary angiography shows single-vessel disease with normal LVEF; symptoms are controlled on medication.",
            "physician": "The cardiology note recommends continuing medical therapy; surgery is not advised.",
            "modalities": [],
            "grade": "single-vessel disease",
        }

    def mastectomy(p, overturn):
        return {
            "intro": f"{p['age']}yo female with a {p['size']} cm mass in the {p['side']} breast.",
            "conservative": None,
            "severity": f"Core biopsy confirms {p['stage']} invasive ductal carcinoma, {p['receptor']}.",
            "physician": f"The tumour board led by Dr. {p['doctor']} recommends mastectomy followed by adjuvant therapy.",
            "modalities": [],
            "grade": f"{p['stage']} invasive ductal carcinoma",
        }

    def stent(p, overturn):
        return {
            "intro": f"{p['age']}yo {p['gender']} admitted with acute {p['event']}.",
            "conservative": None,
            "severity": f"Troponin is elevated and emergency angiography shows a 95% occlusion of the {p['artery']}.",
            "physician": f"Dr. {p['doctor']} performed emergency primary angioplasty with stent placement.",
            "modalities": [],
            "grade": f"95% occlusion of the {p['artery']}",
        }

    # (procedure, builder, whether the procedure is acute or oncologic, so no conservative trial applies)
    templates = [
        ("Total Knee Replacement", knee, False),
        ("Lumbar Spinal Fusion", spine, False),
        ("Coronary Artery Bypass Graft", cabg, False),
        ("Mastectomy (Breast Cancer)", mastectomy, True),
        ("Percutaneous Coronary Stent", stent, True),
    ]
    elective = [t for t in templates if not t[2]]

    cases = []
    for i in range(60):
        overturn = i < 42
        procedure, make, acute = templates[i % len(templates)] if overturn else elective[i % len(elective)]
        params = {
            "age": random.randint(35, 75), "gender": random.choice(["male", "female"]),
            "side": random.choice(["right", "left"]), "months": random.choice([6, 8, 12, 15, 18, 24]),
            "doctor": random.choice(DOCTORS), "level": random.choice(["L4-L5", "L5-S1", "L3-L4"]),
            "deficit": random.choice(["foot drop", "diminished ankle reflex", "motor weakness grade 3/5"]),
            "lvef": random.choice([30, 35, 40]), "size": round(random.uniform(1.5, 5.0), 1),
            "stage": random.choice(["Stage IIA", "Stage IIB", "Stage IIIA"]),
            "receptor": random.choice(["ER+/PR+/HER2-", "triple negative", "ER+/PR-/HER2+"]),
            "event": random.choice(["anterior STEMI", "inferior STEMI"]),
            "artery": random.choice(["LAD", "RCA", "LCx"]),
        }
        parts = make(params, overturn)
        sentences = [parts["intro"], parts["conservative"], parts["severity"], parts["physician"]]
        notes = " ".join(s for s in sentences if s)

        attempted = parts["conservative"] is not None
        physician_states_necessity = overturn
        checklist = {
            "conservative_treatment_attempted": attempted,
            "conservative_treatment_duration_months": params["months"] if attempted else 0,
            "treatment_modalities": parts["modalities"],
            "disease_severity_grade": parts["grade"],
            "physician_necessity_stated": physician_states_necessity,
            "acute_or_oncologic_indication": acute,
        }
        spans = [s for s in (parts["conservative"], parts["severity"], parts["physician"]) if s]

        case_id = f"G3-{i+1:03d}"
        _check(all(s in notes for s in spans), case_id, "evidence span not verbatim")
        _check(parts["grade"] in notes, case_id, "severity grade not in note")
        necessary = acute or (attempted and params["months"] >= 6 and physician_states_necessity)
        _check(necessary == overturn, case_id, "determination does not follow from the checklist")

        cases.append({
            "case_id": case_id,
            "clinical_notes": notes,
            "procedure": procedure,
            "ground_truth_checklist": checklist,
            "verbatim_evidence_spans": spans,
            "expected_determination": "OVERTURN" if overturn else "UPHOLD",
        })

    _save_json(cases, "G3_golden_clinical_evidence.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G4: GOLDEN CHRONOLOGY PED                                  ║
# ╚══════════════════════════════════════════════════════════════╝
def ped_decision(elapsed_months, onset, inception, waiting_months, declared):
    """Decision rule of the chronology engine (Algorithm 3.3 in the report)."""
    if elapsed_months >= MORATORIUM_MONTHS:
        return "DENIAL_REVERSAL_MORATORIUM_APPLIES"
    if onset >= inception:
        return "DENIAL_REVERSAL_POST_INCEPTION_ONSET"
    if elapsed_months >= waiting_months:
        return "DENIAL_REVERSAL_WAITING_PERIOD_EXPIRED"
    if not declared:
        return "DENIAL_UPHELD_NON_DISCLOSURE"
    return "DENIAL_UPHELD_WITHIN_WAITING_PERIOD"


def build_g4():
    print("\n[G4] Building golden_chronology_ped.json (60 cases)...")
    # scenario -> number of cases
    plan = ["moratorium"] * 14 + ["post_inception"] * 10 + ["waiting_expired"] * 14 + \
           ["non_disclosure"] * 11 + ["within_waiting"] * 11
    cases = []

    for i, scenario in enumerate(plan):
        condition, icd10, waiting = random.choice(PED_CONDITIONS)
        name = random.choice(INDIAN_NAMES)

        if scenario == "moratorium":
            elapsed = random.randint(MORATORIUM_MONTHS, MORATORIUM_MONTHS + 30)
        elif scenario == "post_inception":
            elapsed = random.randint(6, MORATORIUM_MONTHS - 1)
        elif scenario == "waiting_expired":
            elapsed = random.randint(waiting, MORATORIUM_MONTHS - 1)
        else:
            elapsed = random.randint(2, waiting - 1)

        admission = random_date(2023, 2025)
        inception = admission - timedelta(days=round(elapsed * DAYS_PER_MONTH + random.randint(0, 20)))
        if scenario == "post_inception":
            onset = inception + timedelta(days=random.randint(45, max(46, (admission - inception).days - 30)))
        else:
            onset = inception - timedelta(days=random.randint(180, 1825))
        declared = {"moratorium": random.choice([True, False]), "post_inception": False,
                    "waiting_expired": True, "non_disclosure": False, "within_waiting": True}[scenario]

        elapsed_months = months_between(inception, admission)
        decision = ped_decision(elapsed_months, onset, inception, waiting, declared)

        if onset < inception:
            years_before = max(1, round((inception - onset).days / 365.25))
            history = f"Patient has a history of {condition.lower()} diagnosed about {years_before} year(s) before policy inception ({format_date(onset)})."
        else:
            months_after = max(1, round((onset - inception).days / DAYS_PER_MONTH))
            history = f"Patient has a history of {condition.lower()} first diagnosed {months_after} months after policy inception ({format_date(onset)})."

        case_id = f"G4-{i+1:03d}"
        _check(admission <= LATEST_DATE, case_id, "admission date is in the future")
        expected = {"moratorium": "DENIAL_REVERSAL_MORATORIUM_APPLIES",
                    "post_inception": "DENIAL_REVERSAL_POST_INCEPTION_ONSET",
                    "waiting_expired": "DENIAL_REVERSAL_WAITING_PERIOD_EXPIRED",
                    "non_disclosure": "DENIAL_UPHELD_NON_DISCLOSURE",
                    "within_waiting": "DENIAL_UPHELD_WITHIN_WAITING_PERIOD"}[scenario]
        _check(decision == expected, case_id, f"scenario {scenario} produced {decision}")

        cases.append({
            "case_id": case_id,
            "patient_name": name,
            "policy_inception_date": format_date(inception),
            "admission_date": format_date(admission),
            "claimed_condition": condition,
            "icd10_code": icd10,
            "clinical_history_onset_statement": history,
            "proposal_form_ped_declared": declared,
            "continuous_renewal_years": int(elapsed_months // 12),
            "applicable_waiting_period_months": waiting,
            "moratorium_threshold_months": MORATORIUM_MONTHS,
            "ground_truth_calculation": {
                "elapsed_days": (admission - inception).days,
                "elapsed_months": elapsed_months,
                "first_symptom_relative_to_inception": "POST_INCEPTION" if onset >= inception else "PRE_INCEPTION",
                "waiting_period_satisfied": elapsed_months >= waiting,
                "pre_existing_non_disclosure": onset < inception and not declared,
                "moratorium_clause_applicable": elapsed_months >= MORATORIUM_MONTHS,
                "symbolic_decision": decision,
            },
        })

    random.shuffle(cases)
    for i, case in enumerate(cases):
        case["case_id"] = f"G4-{i+1:03d}"
    _save_json(cases, "G4_golden_chronology_ped.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G5: GOLDEN REASONING TOULMIN                               ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g5():
    print("\n[G5] Building golden_reasoning_toulmin.json (80 cases)...")
    elective_procedures = ["Total Knee Replacement", "Total Hip Replacement", "Lumbar Spinal Fusion",
                           "Cervical Spinal Fusion", "Septoplasty", "Laparoscopic Sleeve Gastrectomy"]

    # category -> list of (claim, grounds, warrant, backing, exception_status, rebuttal);
    # SATISFIED means an exception or protection defeats the denial.
    def cases_for(category, p):
        proc, cond = p["procedure"], p["condition"]
        return {
            "MEDICAL_NECESSITY": [
                (f"{proc} was elective and not medically necessary.",
                 f"The record documents {p['months']} months of failed physiotherapy and medication, imaging confirming severe disease, and a specialist certificate of necessity.",
                 "The policy excludes elective procedures unless they are medically necessary as certified by the treating specialist.",
                 "The policy definition of Medically Necessary Treatment.",
                 "SATISFIED", "Failed conservative treatment and specialist certification establish medical necessity."),
                (f"{proc} was elective and not medically necessary.",
                 f"Surgery was performed {p['weeks']} weeks after symptom onset with no physiotherapy or medication trial and no specialist certificate.",
                 "The policy excludes elective procedures unless they are medically necessary as certified by the treating specialist.",
                 "The policy definition of Medically Necessary Treatment.",
                 "NOT_SATISFIED", "No record supports medical necessity, so the exclusion applies."),
            ],
            "PRE_EXISTING_WAITING_PERIOD": [
                (f"Treatment for {cond} falls within the pre-existing disease waiting period.",
                 f"The policy has been continuously renewed for {p['elapsed']} months, beyond the {p['wp']}-month waiting period.",
                 f"Pre-existing diseases are covered after {p['wp']} months of continuous coverage.",
                 "The waiting-period clause of the policy wording.",
                 "SATISFIED", "The waiting period had expired before admission."),
                (f"Treatment for {cond} falls within the pre-existing disease waiting period.",
                 f"The policy has been continuously renewed for {p['moratorium']} months.",
                 "After 60 months of continuous coverage a claim cannot be contested on grounds of non-disclosure, except proven fraud.",
                 "IRDAI Master Circular on Health Insurance Business (2024), moratorium provision.",
                 "SATISFIED", "The moratorium period is complete and no fraud is alleged."),
                (f"Treatment for {cond} falls within the pre-existing disease waiting period.",
                 f"{cond} was diagnosed {p['before']} months before inception and admission occurred {p['short']} months after inception.",
                 f"Pre-existing diseases are covered after {p['wp']} months of continuous coverage.",
                 "The waiting-period clause of the policy wording.",
                 "NOT_SATISFIED", "The waiting period had not expired at admission."),
            ],
            "POLICY_EXCLUSION": [
                ("Cosmetic surgery is excluded under the policy.",
                 f"Reconstructive surgery was performed after a road traffic accident on {p['date']}, documented in the emergency record.",
                 "Cosmetic or plastic surgery is excluded unless it is reconstruction following an accident, burns or cancer.",
                 "The standard IRDAI exclusion wording for cosmetic surgery.",
                 "SATISFIED", "Reconstruction after an accident falls within the exception."),
                ("Cosmetic surgery is excluded under the policy.",
                 f"{p['cosmetic']} was performed on {p['date']} to change appearance; no injury, burn or cancer is recorded.",
                 "Cosmetic or plastic surgery is excluded unless it is reconstruction following an accident, burns or cancer.",
                 "The standard IRDAI exclusion wording for cosmetic surgery.",
                 "NOT_SATISFIED", "No condition of the exception is met."),
            ],
            "FINANCIAL_LIMIT": [
                ("A proportionate deduction applies to the whole bill because a higher room was chosen.",
                 f"The deduction of Rs {p['deduction']:,} was applied to medicines, implants and diagnostics as well as room-related charges.",
                 "Proportionate deductions apply only to charges that vary with the room category.",
                 "IRDAI guidelines on proportionate deduction.",
                 "SATISFIED", "Medicines, implants and diagnostics must not be scaled."),
                ("The claim is limited by the room rent cap.",
                 f"The patient chose a room costing Rs {p['room']:,} per day against an eligible limit of Rs {p['limit']:,}, and the deduction was applied only to room-related charges.",
                 "Proportionate deductions apply to charges that vary with the room category.",
                 "The room rent clause of the policy wording.",
                 "NOT_SATISFIED", "The deduction was applied correctly."),
            ],
            "DOCUMENTATION": [
                ("The claim is incomplete because the discharge summary is missing.",
                 f"The discharge summary was uploaded with the claim on {p['date']}, as shown in the submission acknowledgement.",
                 "A claim may be held only for documents that have not been submitted.",
                 "The claim documentation clause of the policy wording.",
                 "SATISFIED", "The requested document was already on file."),
                ("The claim is incomplete because the discharge summary is missing.",
                 f"The submission acknowledgement dated {p['date']} lists only the bills; no discharge summary was submitted.",
                 "A claim may be held only for documents that have not been submitted.",
                 "The claim documentation clause of the policy wording.",
                 "NOT_SATISFIED", "The document is genuinely missing and must be obtained from the hospital."),
            ],
            "ADMINISTRATIVE_PROCEDURAL": [
                ("The claim is rejected because the hospitalization was intimated late.",
                 f"The patient was admitted unconscious to the ICU, and the family intimated the insurer {p['delay']} days later, on regaining contact.",
                 "Claims should be intimated within the specified time, but genuine claims are not rejected for delay caused by circumstances beyond the insured's control.",
                 "IRDAI guidance on condonation of delay in claim intimation.",
                 "SATISFIED", "The delay was beyond the insured's control."),
                ("The claim is rejected because the hospitalization was intimated late.",
                 f"The planned admission was intimated {p['delay']} days after discharge with no reason given.",
                 "Claims should be intimated within the specified time, but genuine claims are not rejected for delay caused by circumstances beyond the insured's control.",
                 "IRDAI guidance on condonation of delay in claim intimation.",
                 "NOT_SATISFIED", "No circumstance justifies the delay."),
            ],
            "ELIGIBILITY_COVERAGE": [
                ("The policy had lapsed on the date of admission.",
                 f"The renewal premium was paid {p['grace']} days after the due date, within the grace period, and admission followed.",
                 "A policy renewed within the grace period continues without a break in coverage.",
                 "The grace period clause of the policy wording.",
                 "SATISFIED", "Renewal within the grace period preserved coverage."),
                ("The policy had lapsed on the date of admission.",
                 f"The renewal premium was paid {p['late']} days after the due date, after the grace period had ended.",
                 "A policy renewed within the grace period continues without a break in coverage.",
                 "The grace period clause of the policy wording.",
                 "NOT_SATISFIED", "The grace period had ended, so the policy was not in force."),
            ],
        }[category]

    per_category = [12, 12, 12, 11, 11, 11, 11]
    cases, seen = [], set()
    for category, n in zip(CATEGORIES, per_category):
        for j in range(n):
            for _ in range(50):
                wp = random.choice([24, 36, 48])
                p = {
                    "procedure": random.choice(elective_procedures),
                    "condition": random.choice(PED_CONDITIONS)[0],
                    "months": random.choice([6, 8, 9, 12, 15, 18, 24]), "weeks": random.randint(2, 8),
                    "wp": wp, "elapsed": wp + random.randint(1, 20), "moratorium": random.randint(60, 84),
                    "before": random.randint(6, 48), "short": random.randint(2, wp - 1),
                    "date": format_date(random_date(2023, 2025)),
                    "cosmetic": random.choice(["Rhinoplasty", "Liposuction", "Abdominoplasty", "Blepharoplasty"]),
                    "deduction": random.randint(20, 90) * 1000, "room": random.choice([8000, 10000, 12000]),
                    "limit": random.choice([4000, 5000, 6000]), "delay": random.randint(5, 25),
                    "grace": random.randint(3, 28), "late": random.randint(35, 70),
                }
                options = cases_for(category, p)
                satisfied = [o for o in options if o[4] == "SATISFIED"]
                not_satisfied = [o for o in options if o[4] == "NOT_SATISFIED"]
                claim, grounds, warrant, backing, status, rebuttal = random.choice(satisfied if j % 2 == 0 else not_satisfied)
                if grounds not in seen:
                    seen.add(grounds)
                    break
            else:
                raise ValueError(f"G5: could not generate a distinct {category} case")
            cases.append({
                "case_id": f"G5-{len(cases)+1:03d}",
                "category": category,
                "toulmin_components": {
                    "claim": claim,
                    "grounds": grounds,
                    "warrant": warrant,
                    "backing": backing,
                    "exception_status": status,
                    "rebuttal": rebuttal,
                },
                "expected_verdict": "CONTRADICTS_DENIAL" if status == "SATISFIED" else "SUPPORTS_DENIAL",
                "confidence_threshold": 0.85,
            })

    _save_json(cases, "G5_golden_reasoning_toulmin.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G6: GOLDEN APPEAL DRAFTS                                   ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g6():
    print("\n[G6] Building golden_appeal_drafts.json (40 cases)...")
    # Appeals argue that an exception printed in the cited clause applies, so only
    # exclusion or waiting-period clauses containing an exception sentence are usable.
    # The sentence is read from the clause text itself; the has_exception flag in the
    # runtime CSV is keyword-based and not reliable enough to use here.
    exception_sentence = re.compile(r"[^.;:]*\b(unless|except(?! as)|provided that)\b[^.;]*[.;]", re.I)
    usable = []
    for r in CITABLE:
        if r["clause_type"] not in ("EXCLUSION", "WAITING_PERIOD"):
            continue
        m = exception_sentence.search(r["clause_text"])
        if m and 50 <= len(m.group(0).strip()) <= 400:
            usable.append((r, m.group(0).strip()))
    topic_of = {row["clause_id"]: topic for (_, topic), row in TOPIC_CLAUSES.items()}
    # Clauses that are the best match for a known topic come first.
    random.shuffle(usable)
    usable.sort(key=lambda u: u[0]["clause_id"] not in topic_of)
    _check(len(usable) >= 20, "G6", f"only {len(usable)} clauses with an exception sentence")

    cases = []
    for i in range(40):
        # When there are fewer than 40 such clauses, the list is reused with new claimants and forums.
        row, exception_quote = usable[i % len(usable)]
        product = row["product_name"]
        topic = topic_of.get(row["clause_id"])
        insurer = INSURER_OF[product]
        name = random.choice(INDIAN_NAMES)
        hospital = random.choice(HOSPITALS)
        doctor = random.choice(DOCTORS)
        admission = random_date(2023, 2025)
        denial = min(admission + timedelta(days=random.randint(12, 40)), LATEST_DATE)
        claim_id = f"CLM-{admission.year}-{random.randint(1000, 9999)}"
        forum = FORUMS[i % len(FORUMS)]
        clause = clause_label(row)
        label = TOPICS[topic][1] if topic else ("Policy Exclusion" if row["clause_type"] == "EXCLUSION" else "Waiting Period")

        citations = [
            f"{clause} of {product}",
            f"Repudiation letter dated {format_date(denial)}",
            f"Discharge summary from {hospital} dated {format_date(admission)}",
            f"Certificate of the treating doctor, Dr. {doctor}",
        ]
        appeal_text = (
            f"To: The {forum}\n\n"
            f"Subject: Appeal against repudiation of Claim {claim_id} under {product}\n\n"
            f"Respected Sir/Madam,\n\n"
            f"I, {name}, hold the {product} policy issued by {insurer}. My claim {claim_id} for treatment at "
            f"{hospital} was repudiated by the insurer's {citations[1].lower().replace('repudiation letter', 'letter')}, "
            f"citing {citations[0]} ({label}).\n\n"
            f"The same clause provides an exception, which reads: \"{exception_quote}\". "
            f"The {citations[2]} and the {citations[3]} show that the circumstances described in this exception "
            f"apply to my case. Copies are attached.\n\n"
            f"Because the insurer applied {clause} without considering this exception, I request the "
            f"{forum} to direct {insurer} to reconsider and settle my claim.\n\n"
            f"Enclosures: {'; '.join(citations[1:])}.\n\n"
            f"Yours faithfully,\n{name}"
        )

        case_id = f"G6-{i+1:03d}"
        _check(all(c in appeal_text for c in citations), case_id, "a mandatory citation is not in the reference letter")
        _check(exception_quote in row["clause_text"], case_id, "exception quote is not verbatim")

        cases.append({
            "case_id": case_id,
            "case_facts": {
                "claim_id": claim_id,
                "patient": name,
                "hospital": hospital,
                "insurer": insurer,
                "product": product,
                "clause": row["clause_number"].strip(),
                "clause_id": row["clause_id"],
                "topic": label,
                "exception_text": exception_quote,
                "admission_date": format_date(admission),
                "denial_date": format_date(denial),
            },
            "mandatory_citations": citations,
            "target_forum": forum,
            "reference_appeal_text": appeal_text,
        })

    _save_json(cases, "G6_golden_appeal_drafts.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G7: GOLDEN DENIAL ROUTER                                   ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g7():
    print("\n[G7] Building golden_denial_router.json (140 cases)...")

    openers = [
        "With reference to claim {claim_id}, ",
        "After review of the documents submitted for claim {claim_id}, ",
        "We have examined your claim {claim_id} for hospitalization at {hospital}. ",
        "Dear {name}, ",
        "This refers to your claim {claim_id} under {product}. ",
        "",
    ]
    closers = [
        "",
        " You may write to our Grievance Redressal Officer if you disagree.",
        " The claim is therefore closed.",
        " Please quote the claim number in all further correspondence.",
    ]
    reasons = {
        "MEDICAL_NECESSITY": [
            "our medical panel has found that {procedure} was not medically necessary and could have been managed conservatively.",
            "the treating doctor's notes do not justify inpatient admission for {procedure}; the condition could be treated on an outpatient basis.",
            "{procedure} has been assessed as elective, as no failed conservative treatment is documented.",
            "the investigations on record do not support the need for {procedure} at this stage of the illness.",
            "the requested {procedure} is not in line with accepted clinical guidelines for the diagnosis recorded.",
            "the hospitalization was primarily for observation and did not require active inpatient treatment.",
        ],
        "PRE_EXISTING_WAITING_PERIOD": [
            "{condition} existed before the policy began and the {wp}-month pre-existing disease waiting period has not been completed.",
            "the records show that {condition} was diagnosed before inception, so it is a pre-existing disease still within its waiting period.",
            "treatment of {condition} is subject to a {wp}-month waiting period that had not expired on the date of admission.",
            "{condition} is a listed condition with a specific waiting period that was not completed at the time of treatment.",
            "the claim arose within the first 30 days of the policy for an illness that was not caused by an accident.",
            "the proposal form did not disclose the earlier diagnosis of {condition}, and the waiting period had not been served.",
        ],
        "POLICY_EXCLUSION": [
            "dental treatment not arising from an accident is a permanent exclusion under the policy.",
            "the treatment relates to {exclusion}, which is excluded under the policy wording.",
            "expenses for {exclusion} fall under the standard exclusions specified by IRDAI.",
            "the policy does not cover {exclusion}, and no exception to this exclusion applies.",
            "injuries arising from participation in hazardous adventure sports are excluded.",
            "hospitalization for evaluation and investigation only, without active treatment, is excluded.",
        ],
        "FINANCIAL_LIMIT": [
            "the room chosen costs Rs {room:,} per day against an eligible limit of Rs {limit:,}, so a proportionate deduction has been applied.",
            "the sum insured for this policy year has been exhausted by earlier claims, and only Rs {balance:,} could be paid.",
            "a co-payment of {copay}% applies to this claim under the policy terms, and the payable amount has been reduced accordingly.",
            "the sub-limit of Rs {sublimit:,} for this procedure has been applied to the admissible amount.",
            "items worth Rs {nme:,} fall under the list of non-payable items and have been deducted.",
            "the claimed amount is within the policy deductible of Rs {deductible:,}, so nothing is payable.",
        ],
        "DOCUMENTATION": [
            "the discharge summary from {hospital} has not been received, and the claim cannot be assessed without it.",
            "the original itemized bills and payment receipts are still awaited.",
            "the investigation reports supporting the diagnosis have not been submitted despite two reminders.",
            "the claim form is unsigned and the dates on it do not match the hospital records.",
            "the implant invoice and sticker required for this procedure have not been provided.",
            "the indoor case papers requested on {date} have not been received.",
        ],
        "ADMINISTRATIVE_PROCEDURAL": [
            "the claim documents were submitted {days} days after discharge, beyond the time allowed under the policy.",
            "the planned hospitalization was not intimated to the insurer or TPA before admission.",
            "treatment was taken at a non-network hospital without the prior approval required for planned admissions.",
            "the same hospitalization has already been settled under another claim, so this is a duplicate claim.",
            "the cashless request was withdrawn by the hospital and no reimbursement claim was filed within the time limit.",
            "the claim was filed with the wrong TPA and was not transferred within the permitted time.",
        ],
        "ELIGIBILITY_COVERAGE": [
            "the policy was not in force on the date of admission because the renewal premium was received {days} days late.",
            "the patient is not listed as an insured member in the policy schedule.",
            "the insured person had crossed the maximum age for dependent children on the date of admission.",
            "the hospitalization occurred before the policy start date.",
            "the policy had been cancelled at the policyholder's request before the date of treatment.",
            "the dependent was added to the policy after the date of hospitalization.",
        ],
    }
    exclusions = ["infertility treatment", "cosmetic surgery", "treatment for alcohol dependence",
                  "obesity treatment", "spectacles and contact lenses", "external congenital anomalies"]

    cases, seen = [], set()
    for category in CATEGORIES:
        made = 0
        while made < 20:
            opener = random.choice(openers)
            text = opener + random.choice(reasons[category]) + random.choice(closers)
            name = random.choice(INDIAN_NAMES)
            hospital = random.choice(HOSPITALS)
            _, product, _ = random.choice(ALL_PRODUCTS)
            ped = random.choice(PED_CONDITIONS)
            text = text.format(
                claim_id=f"CLM-{random.randint(2023, 2025)}-{random.randint(1000, 9999)}", name=name,
                hospital=hospital, product=product, procedure=random.choice(PROCEDURES_MN)[0],
                condition=ped[0], wp=ped[2], exclusion=random.choice(exclusions),
                room=random.choice([6000, 8000, 10000]), limit=random.choice([3000, 4000, 5000]),
                balance=random.randint(10, 90) * 1000, copay=random.choice([10, 20]),
                sublimit=random.choice([40000, 75000, 100000]), nme=random.randint(2, 15) * 1000,
                deductible=random.choice([25000, 50000, 100000]), date=format_date(random_date(2024, 2025)),
                days=random.choice([45, 60, 75, 90]),
            )
            text = text[0].upper() + text[1:]
            if text in seen:
                continue
            seen.add(text)
            cases.append({
                "case_id": f"G7-{len(cases)+1:03d}",
                "raw_denial_paragraph": text,
                "ground_truth_category": category,
                "patient_name": name,
                "source_product": product,
            })
            made += 1

    _check(len({c["raw_denial_paragraph"] for c in cases}) == len(cases), "G7", "duplicate paragraphs")
    _save_json(cases, "G7_golden_denial_router.json")
    return len(cases)


# ──────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────
def _save_json(data, filename):
    output_path = GOLDEN_DIR / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  -> Saved {len(data)} cases to {output_path}")


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    insurers_list = sorted(set(p[0] for p in ALL_PRODUCTS))
    print("=" * 70)
    print("  BUILDING 7 ESSENTIAL GOLDEN EVALUATION BENCHMARK JSONs")
    print(f"  Discovered {len(ALL_PRODUCTS)} products across {len(insurers_list)} insurers: {', '.join(insurers_list)}")
    print(f"  Citable clauses in knowledge base: {len(CITABLE)} | product/topic pairs: {len(TOPIC_CLAUSES)}")
    print("=" * 70)

    counts = {}
    counts["G1_intake_entities"] = build_g1()
    counts["G2_clause_retrieval"] = build_g2()
    counts["G3_clinical_evidence"] = build_g3()
    counts["G4_chronology_ped"] = build_g4()
    counts["G5_reasoning_toulmin"] = build_g5()
    counts["G6_appeal_drafts"] = build_g6()
    counts["G7_denial_router"] = build_g7()

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    for name, count in counts.items():
        print(f"  {name:40s} -> {count:5d} cases")
    print(f"\n  Total golden test cases: {sum(counts.values())}")
    print(f"  Output directory: {GOLDEN_DIR}")
    print("=" * 70)
