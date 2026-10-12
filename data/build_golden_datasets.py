"""
build_golden_datasets.py
========================
Builds all 10 Golden Evaluation Benchmark JSONs for the 3-Tier DeepEval evaluation suite.

Output:
  data/golden/
  ├── G1_golden_intake_entities.json         (100 cases)
  ├── G2_golden_clause_retrieval.json        (100 triplets)
  ├── G3_golden_clinical_evidence.json       (60 cases)
  ├── G4_golden_chronology_ped.json          (60 cases)
  ├── G5_golden_reasoning_toulmin.json       (80 cases)
  ├── G6_golden_appeal_drafts.json           (40 cases)
  ├── G7_golden_pipeline_medical_necessity.json (50 cases)
  ├── G8_golden_pipeline_waiting_period.json    (50 cases)
  ├── G9_golden_denial_router.json           (140 cases)
  └── G10_golden_hitl_benchmark.json         (30 cases)
"""

import json
import os
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta
from copy import deepcopy

# Ensure UTF-8 console output on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────
BASE_DIR = Path(r"c:\Users\Saketh\Desktop\Major Project")
GOLDEN_DIR = BASE_DIR / "data" / "golden"
GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)  # Reproducibility

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
ICICI_PRODUCTS = [p[1] for p in ALL_PRODUCTS if p[0] == "ICICI Lombard"]

PROCEDURES_MN = [
    ("Total Knee Replacement", "M17.11", "27447", "Orthopedic Surgery"),
    ("Total Hip Replacement", "M16.11", "27130", "Orthopedic Surgery"),
    ("Lumbar Spinal Fusion", "M47.816", "22612", "Orthopedic Surgery"),
    ("Coronary Artery Bypass Graft", "I25.10", "33533", "Cardiovascular Surgery"),
    ("Percutaneous Coronary Stent", "I25.110", "92928", "Cardiovascular Surgery"),
    ("Aortic Valve Replacement", "I50.9", "33405", "Cardiovascular Surgery"),
    ("Laparoscopic Sleeve Gastrectomy", "E66.01", "43775", "Bariatric Surgery"),
    ("Mastectomy (Breast Cancer)", "C50.911", "19303", "Oncology Surgery"),
    ("IMRT Radiation Therapy", "C34.90", "77385", "Radiation Oncology"),
    ("Craniotomy for Tumor", "G40.909", "61510", "Neurosurgery"),
    ("Cervical Spinal Fusion", "M47.812", "22551", "Orthopedic Surgery"),
    ("Renal Transplant", "N18.6", "50360", "Transplant Surgery"),
    ("Liver Transplant", "K80.20", "47135", "Transplant Surgery"),
    ("Robotic Prostatectomy", "C61", "55866", "Urology"),
    ("Septoplasty", "J45.20", "30520", "ENT Surgery"),
]

PED_CONDITIONS = [
    ("Essential Hypertension", "I10", 48),
    ("Type 2 Diabetes Mellitus", "E11.9", 48),
    ("Hypothyroidism", "E03.9", 48),
    ("Chronic Kidney Disease", "N18.3", 48),
    ("Coronary Artery Disease", "I25.10", 48),
    ("Hypertensive Nephropathy", "I12.0", 36),
    ("Diabetic Retinopathy", "E11.311", 48),
    ("COPD", "J44.1", 48),
    ("Osteoarthritis (Bilateral Knee)", "M17.0", 24),
    ("Benign Prostatic Hyperplasia", "N40.0", 24),
    ("Atrial Fibrillation", "I48.91", 48),
    ("Epilepsy", "G40.909", 48),
    ("Hyperlipidemia", "E78.5", 48),
    ("Heart Failure", "I50.9", 48),
    ("Calculus of Kidney", "N20.0", 24),
]

DENIAL_CLAUSES = [
    ("Clause 4.3", "Elective Surgery Exclusion"),
    ("Clause 4.4", "Pre-Existing Disease Exclusion"),
    ("Clause 4.5", "Experimental Treatment Exclusion"),
    ("Clause 5.1", "Waiting Period - 30 Days"),
    ("Clause 5.2", "Waiting Period - Specific Diseases (24 Months)"),
    ("Clause 5.3", "Waiting Period - Pre-Existing (48 Months)"),
    ("Clause 3.1", "General Exclusions - Self-Inflicted"),
    ("Clause 3.8", "Cosmetic/Plastic Surgery Exclusion"),
    ("Clause 6.1", "Sub-Limit Room Rent"),
    ("Clause 6.4", "Co-Payment Deduction"),
]


def random_date(start_year=2020, end_year=2024):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def format_date(dt):
    return dt.strftime("%Y-%m-%d")


def random_amount(low=50000, high=1500000):
    return round(random.randint(low, high) / 1000) * 1000


# ╔══════════════════════════════════════════════════════════════╗
# ║  G1: GOLDEN INTAKE ENTITIES                                 ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g1():
    print("\n[G1] Building golden_intake_entities.json (100 cases)...")
    cases = []

    denial_templates = [
        "Ref: {claim_id}. Dear {name}, with reference to your hospitalization on {date} at {hospital} for {procedure} (ICD-10: {icd10}), your claim for Rs {amount} has been repudiated under {clause} ({clause_desc}). The insurer has determined that the treatment does not meet the criteria for coverage under your policy {product}. You may file an appeal within 30 days.",
        "Claim Reference: {claim_id}\nDear {name},\nThis is to inform you that your health insurance claim under Policy No. {policy_no} ({product}) for treatment at {hospital} has been denied.\nProcedure: {procedure}\nDiagnosis Code: {icd10}\nClaimed Amount: Rs. {amount}\nDenial Reason: {clause} - {clause_desc}\nDate of Admission: {date}\nPlease contact your TPA for further details.",
        "Subject: Claim Repudiation Notice - {claim_id}\n\nDear Mr./Ms. {name},\n\nWe regret to inform you that your claim bearing reference number {claim_id} dated {date} for {procedure} at {hospital} has been repudiated.\n\nThe claim amount of Rs. {amount} is not payable under {product} due to {clause} ({clause_desc}). The diagnosis code {icd10} has been reviewed by our medical team.\n\nAppeal window: 30 days from the date of this letter.",
        "REPUDIATION NOTICE\n\nTo: {name}\nPolicy: {product} | Claim: {claim_id}\nHospital: {hospital}\nDate of Hospitalization: {date}\nProcedure/Treatment: {procedure} [{icd10}]\nBilled Amount: Rs. {amount}\n\nDenial Ground: Your claim has been denied under {clause} which pertains to {clause_desc}. The procedure is deemed {clause_desc} as per policy terms and conditions.\n\nYou have the right to appeal this decision.",
        "Dear {name},\n\nYour claim {claim_id} for Rs. {amount}/- towards {procedure} performed on {date} at {hospital} has been disallowed under your {product} policy.\n\nReason for Denial: {clause} - {clause_desc}\nICD-10 Code: {icd10}\n\nAs per IRDAI guidelines, you may approach the Insurance Ombudsman if you are dissatisfied with this decision. The claim documents have been reviewed by our panel of medical experts who have concluded that the criteria under {clause} are applicable.",
    ]

    for i in range(100):
        proc = random.choice(PROCEDURES_MN) if i < 50 else None
        ped = random.choice(PED_CONDITIONS) if i >= 50 else None
        clause_info = random.choice(DENIAL_CLAUSES)
        name = random.choice(INDIAN_NAMES)
        hospital = random.choice(HOSPITALS)
        insurer, product, code = random.choice(ALL_PRODUCTS)
        denial_date = random_date(2023, 2024)
        claim_id = f"CLM-{denial_date.year}-{random.randint(1000, 9999)}"
        policy_no = f"{code}/{random.randint(1000,9999)}/{denial_date.year}"
        amount = random_amount()

        if proc:
            procedure, icd10, hcpcs, category = proc
        else:
            condition, icd10, wp = ped
            procedure = f"Treatment for {condition}"
            hcpcs = ""
            category = "Medical Management"

        template = random.choice(denial_templates)
        raw_letter = template.format(
            claim_id=claim_id, name=name, date=format_date(denial_date),
            hospital=hospital, procedure=procedure, icd10=icd10,
            amount=f"{amount:,.0f}", clause=clause_info[0],
            clause_desc=clause_info[1], product=product, policy_no=policy_no,
        )

        case = {
            "case_id": f"G1-{i+1:03d}",
            "raw_letter_text": raw_letter,
            "ground_truth_entities": {
                "claim_id": claim_id,
                "patient_name": name,
                "denial_date": format_date(denial_date),
                "procedure": procedure,
                "icd10_code": icd10,
                "claimed_amount": float(amount),
                "cited_clause_raw": clause_info[0],
                "denial_category_hint": clause_info[1],
                "hospital_name": hospital,
                "insurer": insurer,
                "policy_product": product,
            },
        }
        cases.append(case)

    _save_json(cases, "G1_golden_intake_entities.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G2: GOLDEN CLAUSE RETRIEVAL                                ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g2():
    print("\n[G2] Building golden_clause_retrieval.json (100 triplets)...")
    
    # Structured clause queries and expected retrievals from the ICICI policy PDFs
    clause_templates = [
        {
            "query_template": "Is {procedure} covered if conservative medical treatment failed under {product}?",
            "product": "Health Shield 360",
            "expected_clause_id": "HS360-EXC-{n:04d}",
            "expected_subclause": "4.3.2",
            "has_exception": True,
            "context_template": "Sub-clause 4.3.2: Elective procedures shall not include surgeries where conservative medical management has failed for a period exceeding six continuous months as certified by the attending specialist.",
            "distractors": ["HS360-EXC-001", "HS360-COV-012"],
        },
        {
            "query_template": "What is the waiting period for {condition} under {product}?",
            "product": "Complete Health Insurance",
            "expected_clause_id": "COMPLE-WAI-{n:04d}",
            "expected_subclause": "5.3.1",
            "has_exception": False,
            "context_template": "Clause 5.3.1: Any Pre-Existing Disease shall be covered only after the Insured Person has been continuously covered for a period of 48 months from the date of inception of the first policy, subject to continuous renewal without break.",
            "distractors": ["COMPLE-WAI-001", "COMPLE-DEF-005"],
        },
        {
            "query_template": "Are cosmetic surgeries covered under {product}?",
            "product": "Arogya Sanjeevani",
            "expected_clause_id": "AROGYA-EXC-{n:04d}",
            "expected_subclause": "Excl04.3",
            "has_exception": True,
            "context_template": "Exclusion Excl04.3: Cosmetic or plastic surgery is excluded unless required for reconstruction following an Accident, burn, or cancer, or as part of medically necessary treatment.",
            "distractors": ["AROGYA-EXC-001", "AROGYA-COV-008"],
        },
        {
            "query_template": "What are the room rent limits under {product}?",
            "product": "Elevate Health",
            "expected_clause_id": "ELEVAT-COV-{n:04d}",
            "expected_subclause": "6.1.1",
            "has_exception": False,
            "context_template": "Clause 6.1.1: Room and Boarding expenses shall be payable up to the Single Private AC Room category in the Network Hospital. In case of a non-network hospital, the amount shall be limited to 1% of the Sum Insured per day or actual charges, whichever is less.",
            "distractors": ["ELEVAT-COV-001", "ELEVAT-EXC-015"],
        },
        {
            "query_template": "Does {product} cover {procedure} if it's listed as a day care procedure?",
            "product": "Health AdvantEdge",
            "expected_clause_id": "HEALTH-COV-{n:04d}",
            "expected_subclause": "2.4.1",
            "has_exception": False,
            "context_template": "Clause 2.4.1: Day Care Treatment means medical treatment, and/or surgical procedure which requires less than 24 hours of hospitalization and is listed in the approved list of Day Care procedures as defined in the policy schedule.",
            "distractors": ["HEALTH-COV-001", "HEALTH-EXC-020"],
        },
        {
            "query_template": "What is the moratorium clause under {product} for pre-existing conditions?",
            "product": "Complete Health Insurance",
            "expected_clause_id": "COMPLE-WAI-{n:04d}",
            "expected_subclause": "5.4.1",
            "has_exception": False,
            "context_template": "Clause 5.4.1 (Moratorium): After completion of 8 continuous years under the policy, no claim shall be contestable on the ground that a disease or condition was pre-existing at the time of inception, provided disclosure was made in good faith.",
            "distractors": ["COMPLE-WAI-003", "COMPLE-DEF-010"],
        },
        {
            "query_template": "Is {procedure} excluded as an experimental treatment under {product}?",
            "product": "Health Shield 360",
            "expected_clause_id": "HS360-EXC-{n:04d}",
            "expected_subclause": "4.5.1",
            "has_exception": True,
            "context_template": "Clause 4.5.1: Experimental, investigational, or unproven treatment shall be excluded unless (a) the treatment is approved by CDSCO/DCGI, and (b) it has been performed at a recognized centre of excellence with published outcomes.",
            "distractors": ["HS360-EXC-002", "HS360-COV-005"],
        },
        {
            "query_template": "What are the co-payment requirements for {condition} treatment under {product}?",
            "product": "Arogya Sanjeevani",
            "expected_clause_id": "AROGYA-COV-{n:04d}",
            "expected_subclause": "6.4.1",
            "has_exception": False,
            "context_template": "Clause 6.4.1: A mandatory co-payment of 5% of the admissible claim amount shall be borne by the Insured Person for each and every claim. This co-payment is applicable over and above any deductible specified in the policy schedule.",
            "distractors": ["AROGYA-COV-002", "AROGYA-EXC-011"],
        },
        {
            "query_template": "Can I claim ambulance charges under {product}?",
            "product": "Elevate Health",
            "expected_clause_id": "ELEVAT-COV-{n:04d}",
            "expected_subclause": "2.7.1",
            "has_exception": True,
            "context_template": "Clause 2.7.1: Ambulance charges are covered up to Rs. 2,000 per hospitalization for emergency transportation to the nearest network hospital. Non-emergency ambulance charges are excluded.",
            "distractors": ["ELEVAT-COV-008", "ELEVAT-EXC-025"],
        },
        {
            "query_template": "What is the sub-limit for {procedure} implant costs under {product}?",
            "product": "Max Protect",
            "expected_clause_id": "MAXPRO-COV-{n:04d}",
            "expected_subclause": "6.2.1",
            "has_exception": True,
            "context_template": "Clause 6.2.1: Implant costs shall be covered up to the limits specified in the policy schedule. Where the cost of implant exceeds the specified sub-limit, the excess shall be borne by the Insured Person. Implants must be from an approved manufacturer list.",
            "distractors": ["MAXPRO-COV-002", "MAXPRO-EXC-009"],
        },
        # Care Health
        {
            "query_template": "Is robotic surgery or modern treatment covered under {product}?",
            "product": "Care Supreme",
            "expected_clause_id": "CARESP-COV-{n:04d}",
            "expected_subclause": "Modern-Treatments",
            "has_exception": True,
            "context_template": "Modern treatments including Robotic Surgeries, Deep Brain Stimulation, and Immunotherapy approved by IRDAI are payable up to the Sum Insured without sub-limits.",
            "distractors": ["CARESP-EXC-001", "CARESP-DEF-004"],
        },
        {
            "query_template": "What is the waiting period for pre-existing disease under {product}?",
            "product": "Care",
            "expected_clause_id": "CARE-WAI-{n:04d}",
            "expected_subclause": "Clause 3.1",
            "has_exception": False,
            "context_template": "Clause 3.1: Pre-existing Disease waiting period is 48 months of continuous coverage from the date of first inception of the policy.",
            "distractors": ["CARE-WAI-002", "CARE-DEF-001"],
        },
        # HDFC ERGO
        {
            "query_template": "How does the automatic restore benefit work under {product}?",
            "product": "my:Optima Secure",
            "expected_clause_id": "MYOPTI-COV-{n:04d}",
            "expected_subclause": "Restore Benefit",
            "has_exception": True,
            "context_template": "Automatic Restore Benefit restores 100% of base Sum Insured upon partial or full exhaustion for any subsequent hospitalization within the policy period.",
            "distractors": ["MYOPTI-COV-005", "MYOPTI-EXC-010"],
        },
        {
            "query_template": "What is the waiting period for specific joint replacement under {product}?",
            "product": "Optima Restore",
            "expected_clause_id": "OPTIMA-WAI-{n:04d}",
            "expected_subclause": "Section 3.2",
            "has_exception": False,
            "context_template": "Section 3.2: Specific illnesses including Joint Replacement, Cataract, and Hernia have a mandatory 24 months waiting period.",
            "distractors": ["OPTIMA-WAI-001", "OPTIMA-DEF-003"],
        },
        # Star Health
        {
            "query_template": "Are bariatric and metabolic surgeries covered under {product}?",
            "product": "Star Comprehensive",
            "expected_clause_id": "STARCO-COV-{n:04d}",
            "expected_subclause": "Bariatric Surgery Benefit",
            "has_exception": True,
            "context_template": "Bariatric surgery is covered subject to prior approval, age above 18, BMI greater than 35 with severe co-morbidities, and failed medical management.",
            "distractors": ["STARCO-EXC-003", "STARCO-COV-015"],
        },
        {
            "query_template": "What is the waiting period for cataract surgery under {product}?",
            "product": "Family Health Optima",
            "expected_clause_id": "STARFH-WAI-{n:04d}",
            "expected_subclause": "Specific Illness Waiting Period",
            "has_exception": False,
            "context_template": "Expenses related to Cataract surgery are subject to a waiting period of 24 months from the first inception of the policy.",
            "distractors": ["STARFH-WAI-002", "STARFH-DEF-006"],
        },
    ]

    # Dynamically ensure any discovered product in ALL_PRODUCTS is covered
    existing_products = {t["product"] for t in clause_templates}
    for insurer, product, code in ALL_PRODUCTS:
        if product not in existing_products:
            clause_templates.append({
                "query_template": "Is {procedure} covered if conservative medical treatment failed under {product}?",
                "product": product,
                "expected_clause_id": f"{code}-EXC-{{n:04d}}",
                "expected_subclause": "Elective Surgery Exception",
                "has_exception": True,
                "context_template": f"Sub-clause for {product}: Elective procedures shall not include surgeries where conservative medical management has failed for a period exceeding six continuous months as certified by the attending specialist.",
                "distractors": [f"{code}-EXC-001", f"{code}-COV-012"],
            })
            clause_templates.append({
                "query_template": "What is the waiting period for {condition} under {product}?",
                "product": product,
                "expected_clause_id": f"{code}-WAI-{{n:04d}}",
                "expected_subclause": "Pre-Existing Waiting Period",
                "has_exception": False,
                "context_template": f"Clause under {product}: Any Pre-Existing Disease shall be covered only after continuous coverage of 36 to 48 months from the date of first inception of the policy.",
                "distractors": [f"{code}-WAI-001", f"{code}-DEF-005"],
            })
            clause_templates.append({
                "query_template": "Are robotic surgery or modern treatments covered under {product}?",
                "product": product,
                "expected_clause_id": f"{code}-COV-{{n:04d}}",
                "expected_subclause": "Modern Treatments",
                "has_exception": True,
                "context_template": f"Modern treatments including Robotic Surgeries and Immunotherapy approved by IRDAI are payable up to the Sum Insured under {product}.",
                "distractors": [f"{code}-EXC-001", f"{code}-DEF-004"],
            })

    cases = []
    n = 1
    for i in range(100):
        template = clause_templates[i % len(clause_templates)]
        proc = random.choice(PROCEDURES_MN)
        ped = random.choice(PED_CONDITIONS)

        query = template["query_template"].format(
            procedure=proc[0], condition=ped[0], product=template["product"]
        )

        case = {
            "query_id": f"G2-{i+1:03d}",
            "user_query": query,
            "product_name": template["product"],
            "expected_clause_id": template["expected_clause_id"].format(n=n),
            "expected_subclause": template["expected_subclause"],
            "has_exception": template["has_exception"],
            "ground_truth_context_snippet": template["context_template"],
            "distractor_clauses": template["distractors"],
        }
        cases.append(case)
        n += 1

    _save_json(cases, "G2_golden_clause_retrieval.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G3: GOLDEN CLINICAL EVIDENCE                               ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g3():
    print("\n[G3] Building golden_clinical_evidence.json (60 cases)...")

    clinical_templates = [
        {
            "procedure": "Total Knee Replacement",
            "clinical_notes": "{age}yo {gender} with chronic {side} knee pain unresponsive to {duration} months of {treatments}. Weight-bearing radiographs reveal {severity} osteoarthritis with {finding}. {doctor} certifies surgical intervention is {necessity}.",
            "checklist": {
                "conservative_treatment_attempted": True,
                "treatment_modalities": ["physical therapy", "steroid injections", "NSAIDs"],
                "disease_severity_grade": "Grade IV / Bone-on-bone",
                "physician_necessity_stated": True,
            },
        },
        {
            "procedure": "Coronary Artery Bypass Graft",
            "clinical_notes": "{age}yo {gender} presenting with {symptom} and documented {vessel}-vessel coronary artery disease on angiography dated {angio_date}. LVEF {lvef}%. {history}. Cardiothoracic surgeon Dr. {doctor} recommends CABG as medical management has failed after {duration} months of {treatments}.",
            "checklist": {
                "conservative_treatment_attempted": True,
                "treatment_modalities": ["dual antiplatelet therapy", "statins", "beta-blockers"],
                "disease_severity_grade": "Multi-vessel CAD / Low EF",
                "physician_necessity_stated": True,
            },
        },
        {
            "procedure": "Lumbar Spinal Fusion",
            "clinical_notes": "{age}yo {gender} with progressive low back pain radiating to {side} lower extremity for {duration} months. MRI shows {finding} at {level}. Failed {treatments} over {duration} months. Neurological deficit noted: {deficit}. Spine surgeon Dr. {doctor} recommends surgical decompression and fusion.",
            "checklist": {
                "conservative_treatment_attempted": True,
                "treatment_modalities": ["physical therapy", "epidural injections", "NSAIDs"],
                "disease_severity_grade": "Severe disc herniation with neurological deficit",
                "physician_necessity_stated": True,
            },
        },
        {
            "procedure": "Mastectomy for Breast Cancer",
            "clinical_notes": "{age}yo {gender} diagnosed with {stage} invasive ductal carcinoma of {side} breast. Biopsy confirmed on {biopsy_date}. Tumor size {size}cm. {receptor_status}. Oncology tumor board recommends mastectomy followed by adjuvant chemotherapy. Dr. {doctor} at {hospital} has scheduled surgery.",
            "checklist": {
                "conservative_treatment_attempted": False,
                "treatment_modalities": [],
                "disease_severity_grade": "Stage II-III Invasive Carcinoma",
                "physician_necessity_stated": True,
            },
        },
        {
            "procedure": "Percutaneous Coronary Stent Placement",
            "clinical_notes": "{age}yo {gender} admitted with acute {event_type} on {admission_date}. Troponin elevated at {troponin}. Emergent coronary angiography shows {finding}. {doctor} performed primary PCI with {stent_type} stent deployment to {artery}. Post-procedure TIMI {timi} flow achieved.",
            "checklist": {
                "conservative_treatment_attempted": False,
                "treatment_modalities": [],
                "disease_severity_grade": "Acute coronary syndrome / STEMI",
                "physician_necessity_stated": True,
            },
        },
    ]

    cases = []
    for i in range(60):
        template = clinical_templates[i % len(clinical_templates)]
        age = random.randint(35, 75)
        gender = random.choice(["male", "female"])
        side = random.choice(["right", "left", "bilateral"])
        duration = random.choice([6, 8, 12, 15, 18, 24])
        doctor = random.choice(["Sen", "Mehta", "Iyer", "Sharma", "Reddy", "Gupta", "Patel", "Nair"])

        params = {
            "age": age, "gender": gender, "side": side, "duration": duration,
            "doctor": doctor, "necessity": random.choice(["imperative", "medically necessary", "the only viable option"]),
            "treatments": random.choice(["physical therapy, steroid injections, and daily NSAIDs",
                                         "conservative management including medications and physiotherapy",
                                         "pharmacological therapy and rehabilitation"]),
            "severity": random.choice(["Grade IV", "severe end-stage", "Grade III-IV"]),
            "finding": random.choice(["complete joint space loss and bone-on-bone contact",
                                      "severe degenerative changes with subchondral sclerosis",
                                      "significant narrowing with osteophyte formation"]),
            "symptom": random.choice(["unstable angina", "exertional chest pain NYHA Class III", "acute chest pain with diaphoresis"]),
            "vessel": random.choice(["triple", "double", "left main plus two"]),
            "angio_date": format_date(random_date(2023, 2024)),
            "lvef": random.choice([25, 30, 35, 40, 45]),
            "history": random.choice(["History of prior MI in 2022", "Known diabetic with peripheral vascular disease",
                                      "Previous PCI to RCA in 2021"]),
            "level": random.choice(["L4-L5", "L5-S1", "L3-L4"]),
            "deficit": random.choice(["foot drop", "diminished ankle reflex", "motor weakness grade 3/5"]),
            "stage": random.choice(["Stage IIA", "Stage IIB", "Stage IIIA"]),
            "biopsy_date": format_date(random_date(2023, 2024)),
            "size": round(random.uniform(1.5, 5.0), 1),
            "receptor_status": random.choice(["ER+/PR+/HER2-", "Triple negative", "ER+/PR-/HER2+"]),
            "hospital": random.choice(HOSPITALS),
            "event_type": random.choice(["anterior STEMI", "inferior STEMI", "NSTEMI"]),
            "admission_date": format_date(random_date(2023, 2024)),
            "troponin": round(random.uniform(0.5, 15.0), 2),
            "stent_type": random.choice(["drug-eluting", "biodegradable polymer", "everolimus-eluting"]),
            "artery": random.choice(["LAD", "RCA", "LCx"]),
            "timi": random.choice([2, 3]),
        }

        try:
            clinical_notes = template["clinical_notes"].format(**params)
        except KeyError:
            clinical_notes = template["clinical_notes"]

        checklist = deepcopy(template["checklist"])
        checklist["conservative_treatment_duration_months"] = duration if checklist["conservative_treatment_attempted"] else 0

        # Extract evidence spans
        evidence_spans = []
        if checklist["conservative_treatment_attempted"]:
            evidence_spans.append(f"unresponsive to {duration} months")
        evidence_spans.append(template["checklist"]["disease_severity_grade"])

        # Determine if this should be overturn or uphold
        is_overturn = i < 42  # 70% overturn
        if not is_overturn:
            # Modify to make it an uphold case (cosmetic, no conservative treatment)
            checklist["conservative_treatment_attempted"] = False
            checklist["conservative_treatment_duration_months"] = 0
            checklist["physician_necessity_stated"] = False

        case = {
            "case_id": f"G3-{i+1:03d}",
            "clinical_notes": clinical_notes,
            "procedure": template["procedure"],
            "ground_truth_checklist": checklist,
            "verbatim_evidence_spans": evidence_spans,
            "expected_determination": "OVERTURN" if is_overturn else "UPHOLD",
        }
        cases.append(case)

    _save_json(cases, "G3_golden_clinical_evidence.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G4: GOLDEN CHRONOLOGY PED                                  ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g4():
    print("\n[G4] Building golden_chronology_ped.json (60 cases)...")
    cases = []

    for i in range(60):
        condition, icd10, base_waiting_months = random.choice(PED_CONDITIONS)
        name = random.choice(INDIAN_NAMES)
        
        # Generate policy inception date (2018-2022)
        inception = random_date(2018, 2022)
        
        # Determine scenario type
        if i < 25:
            # Scenario A: Waiting period SATISFIED (denial should be reversed)
            elapsed_extra = random.randint(1, 24)  # months beyond waiting period
            admission = inception + timedelta(days=(base_waiting_months + elapsed_extra) * 30)
            onset_type = "POST_INCEPTION"
            onset_date = inception + timedelta(days=random.randint(30, 365))
            ped_declared = random.choice([True, False])
            waiting_satisfied = True
            moratorium = False
            symbolic = "DENIAL_REVERSAL_WAITING_PERIOD_EXPIRED"
        elif i < 35:
            # Scenario B: MORATORIUM clause applies (8 years continuous, denial reversed)
            inception = random_date(2014, 2016)
            admission = inception + timedelta(days=random.randint(2920, 3650))  # 8-10 years
            onset_type = "PRE_INCEPTION"
            onset_date = inception - timedelta(days=random.randint(365, 1825))
            ped_declared = False
            waiting_satisfied = True
            moratorium = True
            base_waiting_months = 96  # 8 years = moratorium
            symbolic = "DENIAL_REVERSAL_MORATORIUM_APPLIES"
        elif i < 45:
            # Scenario C: Waiting period NOT satisfied (denial upheld)
            remaining = random.randint(1, base_waiting_months - 1)
            admission = inception + timedelta(days=remaining * 30)
            onset_type = random.choice(["PRE_INCEPTION", "POST_INCEPTION"])
            onset_date = inception - timedelta(days=random.randint(30, 730)) if onset_type == "PRE_INCEPTION" else inception + timedelta(days=random.randint(30, 180))
            ped_declared = random.choice([True, False])
            waiting_satisfied = False
            moratorium = False
            symbolic = "DENIAL_UPHELD_WITHIN_WAITING_PERIOD"
        else:
            # Scenario D: Non-disclosure fraud (denial upheld)
            admission = inception + timedelta(days=random.randint(60, 365))
            onset_type = "PRE_INCEPTION"
            onset_date = inception - timedelta(days=random.randint(30, 1095))
            ped_declared = False
            waiting_satisfied = False
            moratorium = False
            symbolic = "DENIAL_UPHELD_NON_DISCLOSURE"

        elapsed_days = (admission - inception).days
        elapsed_months = round(elapsed_days / 30.44, 1)
        continuous_years = max(1, elapsed_days // 365)

        history_statement = f"Patient has a history of {condition.lower()} diagnosed "
        if onset_type == "PRE_INCEPTION":
            years_before = max(1, (inception - onset_date).days // 365)
            history_statement += f"{years_before} years before policy inception ({format_date(onset_date)})."
        else:
            months_after = max(1, (onset_date - inception).days // 30)
            history_statement += f"{months_after} months after policy inception ({format_date(onset_date)})."

        case = {
            "case_id": f"G4-{i+1:03d}",
            "patient_name": name,
            "policy_inception_date": format_date(inception),
            "admission_date": format_date(admission),
            "claimed_condition": condition,
            "icd10_code": icd10,
            "clinical_history_onset_statement": history_statement,
            "proposal_form_ped_declared": ped_declared,
            "continuous_renewal_years": continuous_years,
            "applicable_waiting_period_months": base_waiting_months,
            "ground_truth_calculation": {
                "elapsed_months": elapsed_months,
                "first_symptom_relative_to_inception": onset_type,
                "waiting_period_satisfied": waiting_satisfied,
                "pre_existing_non_disclosure": (onset_type == "PRE_INCEPTION" and not ped_declared),
                "moratorium_clause_applicable": moratorium,
                "symbolic_decision": symbolic,
            },
        }
        cases.append(case)

    _save_json(cases, "G4_golden_chronology_ped.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G5: GOLDEN REASONING TOULMIN                               ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g5():
    print("\n[G5] Building golden_reasoning_toulmin.json (80 cases)...")
    cases = []

    mn_grounds = [
        ("Patient underwent {duration} months of failed conservative management including {treatments}.",
         "Clause 4.3 excludes elective surgeries unless conservative treatment failed for >= 6 months.",
         "SATISFIED", "No contradicting evidence found; physician certifies necessity."),
        ("Acute presentation requiring emergent surgical intervention; no window for conservative therapy.",
         "Emergency treatment is covered under all plans regardless of elective exclusions.",
         "SATISFIED", "Emergency nature documented in ER admission records."),
        ("Prior authorization was obtained from TPA confirming medical necessity for the procedure.",
         "Pre-authorized procedures are deemed medically necessary per insurer's own assessment.",
         "SATISFIED", "Pre-authorization approval letter on file."),
        ("No evidence of conservative treatment attempted before surgical intervention.",
         "Clause 4.3 requires documentation of failed conservative management before elective surgery coverage.",
         "NOT_SATISFIED", "Patient records show no physiotherapy or non-surgical treatment."),
        ("Treatment is classified as cosmetic by the insurer's medical panel.",
         "Clause 3.8 excludes cosmetic procedures unless functionally necessary post-accident or cancer.",
         "NOT_SATISFIED", "No evidence of functional impairment or post-accident reconstruction."),
    ]

    ped_grounds = [
        ("Policy in continuous force for {elapsed} months; waiting period of {wp} months expired {extra} months ago.",
         "Clause 5.3: PED covered after {wp} months of continuous coverage.",
         "SATISFIED", "Insurer cannot contest coverage after waiting period expiry."),
        ("Eight-year moratorium period completed; insurer cannot invoke pre-existing disease ground.",
         "IRDAI Moratorium Clause: After 96 months of continuous coverage, no PED exclusion is valid.",
         "SATISFIED", "Statutory moratorium overrides contractual PED exclusion."),
        ("Condition first diagnosed {months} months after policy inception; not pre-existing.",
         "Clause 5.3 defines PED as conditions existing prior to policy inception.",
         "SATISFIED", "Clinical records confirm post-inception onset; PED clause inapplicable."),
        ("Claim filed within {wp}-month waiting period; PED waiting period not yet exhausted.",
         "Clause 5.3: Pre-existing conditions have a mandatory {wp}-month waiting period.",
         "NOT_SATISFIED", "Waiting period arithmetic confirms claim is premature."),
        ("Policyholder concealed history of {condition} diagnosed 2 years before policy inception.",
         "Insurance Act Section 45: Material non-disclosure within 3 years renders policy voidable.",
         "NOT_SATISFIED", "Proposal form omission confirmed by pre-policy medical records."),
    ]

    for i in range(80):
        is_mn = i < 40
        category = "MEDICAL_NECESSITY" if is_mn else "PRE_EXISTING_WAITING_PERIOD"
        pool = mn_grounds if is_mn else ped_grounds
        idx = i % len(pool)
        grounds_t, warrant_t, exception_status, rebuttal = pool[idx]

        proc = random.choice(PROCEDURES_MN) if is_mn else None
        ped = random.choice(PED_CONDITIONS) if not is_mn else None
        duration = random.choice([6, 8, 12, 15, 18])
        wp = ped[2] if ped else 48
        elapsed = wp + random.randint(1, 24)

        grounds = grounds_t.format(
            duration=duration,
            treatments="physical therapy, steroid injections, and NSAIDs",
            elapsed=elapsed, wp=wp, extra=elapsed - wp,
            months=random.randint(6, 24),
            condition=ped[0] if ped else "hypertension",
        )
        warrant = warrant_t.format(wp=wp)

        if is_mn:
            claim_text = f"{proc[0]} is an excluded elective procedure."
        else:
            claim_text = f"Treatment for {ped[0]} is excluded as a pre-existing disease."

        verdict = "CONTRADICTS_DENIAL" if exception_status == "SATISFIED" else "SUPPORTS_DENIAL"
        confidence = round(random.uniform(0.85, 0.99), 2) if exception_status == "SATISFIED" else round(random.uniform(0.80, 0.95), 2)

        case = {
            "case_id": f"G5-{i+1:03d}",
            "category": category,
            "toulmin_components": {
                "claim": claim_text,
                "grounds": grounds,
                "warrant": warrant,
                "exception_status": exception_status,
                "rebuttal": rebuttal,
            },
            "expected_verdict": verdict,
            "confidence_threshold": confidence,
        }
        cases.append(case)

    _save_json(cases, "G5_golden_reasoning_toulmin.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G6: GOLDEN APPEAL DRAFTS                                   ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g6():
    print("\n[G6] Building golden_appeal_drafts.json (40 cases)...")
    cases = []

    forums = ["Insurance Ombudsman", "IRDAI Grievance Management System", "Consumer Court (District Forum)", "Internal Grievance Redressal"]

    for i in range(40):
        is_mn = i < 20
        name = random.choice(INDIAN_NAMES)
        hospital = random.choice(HOSPITALS)
        insurer, product, code = random.choice(ALL_PRODUCTS)
        claim_date = random_date(2023, 2024)
        claim_id = f"CLM-{claim_date.year}-{random.randint(1000, 9999)}"
        forum = forums[i % len(forums)]

        if is_mn:
            proc = random.choice(PROCEDURES_MN)
            clause = "4.3"
            exception = "4.3.2"
            duration = random.choice([8, 12, 15, 18])
            citations = [
                f"Clause {clause}.{random.choice(['2', '3'])} of {product}",
                f"Discharge Summary dated {format_date(claim_date)}",
                f"{duration} months of documented conservative management",
                f"Specialist certification by Dr. {random.choice(['Sen', 'Mehta', 'Iyer', 'Sharma'])} at {hospital}",
            ]
            subject = f"Appeal against wrongful repudiation of Claim {claim_id} for {proc[0]}"
            appeal_text = (
                f"To: The {forum}, {random.choice(['Hyderabad', 'Mumbai', 'Delhi', 'Bangalore', 'Chennai'])}\n\n"
                f"Subject: {subject}\n\n"
                f"Respected Sir/Madam,\n\n"
                f"I, {name}, holder of {product} policy with {insurer}, hereby appeal the denial of my claim {claim_id} "
                f"for {proc[0]} performed at {hospital} on {format_date(claim_date)}.\n\n"
                f"The insurer has wrongfully denied coverage citing {clause} (Elective Surgery Exclusion). "
                f"However, as documented in the attached medical records, I have undergone {duration} months of "
                f"conservative treatment including physical therapy, steroid injections, and medications, which have "
                f"failed to provide relief. The treating specialist has certified that surgery was the only viable option.\n\n"
                f"Sub-clause {exception} of the policy clearly states that elective procedures are covered when "
                f"conservative medical management has failed for a period exceeding six months. My case meets this "
                f"exception criterion.\n\n"
                f"I request the honorable {forum} to direct {insurer} to honour my claim in full.\n\n"
                f"Yours faithfully,\n{name}"
            )
        else:
            ped = random.choice(PED_CONDITIONS)
            clause = "5.3"
            exception = "5.3.1"
            inception = random_date(2018, 2021)
            elapsed_months = random.randint(49, 96)
            citations = [
                f"Clause {clause} of {product} (Pre-Existing Disease Waiting Period)",
                f"Policy inception certificate dated {format_date(inception)}",
                f"Continuous renewal receipts for {elapsed_months // 12} years",
                f"IRDAI Master Circular on Moratorium Period" if elapsed_months >= 96 else f"Discharge summary from {hospital}",
            ]
            subject = f"Appeal against wrongful repudiation of Claim {claim_id} for {ped[0]}"
            appeal_text = (
                f"To: The {forum}, {random.choice(['Hyderabad', 'Mumbai', 'Delhi', 'Bangalore', 'Chennai'])}\n\n"
                f"Subject: {subject}\n\n"
                f"Respected Sir/Madam,\n\n"
                f"I, {name}, holder of {product} policy with {insurer} (inception: {format_date(inception)}), hereby appeal "
                f"the denial of my claim {claim_id} for treatment of {ped[0]} at {hospital}.\n\n"
                f"The insurer has denied my claim citing Clause {clause} (Pre-Existing Disease Waiting Period). "
                f"However, my policy has been continuously renewed for {elapsed_months} months ({elapsed_months // 12} years) "
                f"without any break. The applicable waiting period of {ped[2]} months has been fully served.\n\n"
                f"{'Additionally, the 8-year moratorium period under IRDAI guidelines has been completed, and the insurer cannot invoke the PED exclusion.' if elapsed_months >= 96 else ''}\n\n"
                f"I request the honorable {forum} to direct {insurer} to settle my claim immediately.\n\n"
                f"Yours faithfully,\n{name}"
            )

        case = {
            "case_id": f"G6-{i+1:03d}",
            "case_facts": {
                "claim_id": claim_id,
                "clause": clause,
                "exception": exception,
                "patient": name,
                "hospital": hospital,
                "insurer": insurer,
                "product": product,
            },
            "mandatory_citations": citations,
            "target_forum": forum,
            "reference_appeal_text": appeal_text,
        }
        cases.append(case)

    _save_json(cases, "G6_golden_appeal_drafts.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G7: GOLDEN PIPELINE MEDICAL NECESSITY                      ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g7():
    print("\n[G7] Building golden_pipeline_medical_necessity.json (50 cases)...")
    cases = []

    for i in range(50):
        is_overturn = i < 35  # 35 overturn, 15 upheld
        proc = random.choice(PROCEDURES_MN)
        name = random.choice(INDIAN_NAMES)
        hospital = random.choice(HOSPITALS)
        insurer, product, _ = random.choice(ALL_PRODUCTS)
        age = random.randint(35, 75)
        gender = random.choice(["male", "female"])
        claim_date = random_date(2023, 2024)
        claim_id = f"CLM-{claim_date.year}-{random.randint(1000, 9999)}"
        amount = random_amount(200000, 2500000)
        duration = random.choice([6, 8, 12, 15, 18, 24])

        if is_overturn:
            clinical_narrative = (
                f"{age}yo {gender} admitted to {hospital} on {format_date(claim_date)} for {proc[0]}. "
                f"Diagnosis: {proc[1]}. Patient has failed {duration} months of conservative management "
                f"including physiotherapy, medication, and specialist consultations. "
                f"Treating physician certifies that surgical intervention is medically necessary. "
                f"Claim amount: Rs. {amount:,.0f}."
            )
            expected_verdict = "OVERTURN"
            evidence_matrix = {
                "conservative_failure_documented": True,
                "duration_months": duration,
                "physician_certification": True,
                "acute_severity_documented": True,
                "guideline_conformance": True,
            }
        else:
            scenarios = [
                f"Request for {proc[0]} classified as cosmetic. No functional impairment documented.",
                f"Request for experimental {proc[0]} technique not approved by CDSCO.",
                f"No evidence of any conservative treatment attempted before requesting {proc[0]}.",
            ]
            clinical_narrative = (
                f"{age}yo {gender} at {hospital}. {random.choice(scenarios)} "
                f"Diagnosis: {proc[1]}. Claim amount: Rs. {amount:,.0f}."
            )
            expected_verdict = "UPHOLD"
            evidence_matrix = {
                "conservative_failure_documented": False,
                "duration_months": 0,
                "physician_certification": False,
                "acute_severity_documented": False,
                "guideline_conformance": False,
            }

        case = {
            "case_id": f"G7-{i+1:03d}",
            "raw_input_narrative": clinical_narrative,
            "patient_name": name,
            "procedure": proc[0],
            "icd10_code": proc[1],
            "hcpcs_code": proc[2],
            "hospital": hospital,
            "insurer": insurer,
            "product": product,
            "claim_id": claim_id,
            "claimed_amount": float(amount),
            "ground_truth_verdict_and_summary": expected_verdict,
            "evidence_coverage_matrix": evidence_matrix,
            "case_facts": {
                "age": age,
                "gender": gender,
                "admission_date": format_date(claim_date),
                "procedure_category": proc[3],
            },
        }
        cases.append(case)

    _save_json(cases, "G7_golden_pipeline_medical_necessity.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G8: GOLDEN PIPELINE WAITING PERIOD                         ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g8():
    print("\n[G8] Building golden_pipeline_waiting_period.json (50 cases)...")
    cases = []

    for i in range(50):
        condition, icd10, base_wp = random.choice(PED_CONDITIONS)
        name = random.choice(INDIAN_NAMES)
        hospital = random.choice(HOSPITALS)
        insurer, product, _ = random.choice(ALL_PRODUCTS)

        if i < 25:
            # Reversal: waiting period expired
            inception = random_date(2018, 2020)
            extra_months = random.randint(1, 36)
            admission = inception + timedelta(days=(base_wp + extra_months) * 30)
            elapsed = base_wp + extra_months
            verdict = "REVERSAL"
            ruling = f"Waiting period of {base_wp} months fully served. {elapsed} months elapsed. Denial reversed."
            scenario = "WAITING_PERIOD_EXPIRED"
        elif i < 35:
            # Reversal: moratorium applies
            inception = random_date(2014, 2016)
            admission = inception + timedelta(days=random.randint(2920, 3650))
            elapsed = round((admission - inception).days / 30.44)
            verdict = "REVERSAL"
            ruling = f"Moratorium period (96 months) completed. {elapsed} months of continuous coverage. Denial reversed per IRDAI guidelines."
            scenario = "MORATORIUM_APPLIES"
        else:
            # Upheld: within waiting period or non-disclosure
            inception = random_date(2022, 2023)
            months_in = random.randint(3, base_wp - 1)
            admission = inception + timedelta(days=months_in * 30)
            elapsed = months_in
            verdict = "UPHELD"
            if i < 45:
                ruling = f"Claim filed within {base_wp}-month waiting period ({elapsed} months elapsed). Denial upheld."
                scenario = "WITHIN_WAITING_PERIOD"
            else:
                ruling = f"Material non-disclosure of {condition.lower()} detected. Policy voidable under Section 45."
                scenario = "NON_DISCLOSURE"

        amount = random_amount(100000, 800000)
        claim_id = f"CLM-{admission.year}-{random.randint(1000, 9999)}"

        case = {
            "case_id": f"G8-{i+1:03d}",
            "patient_name": name,
            "raw_input_narrative": (
                f"{name} seeks claim under {product} for treatment of {condition} at {hospital}. "
                f"Policy inception: {format_date(inception)}. Admission: {format_date(admission)}. "
                f"Claim ID: {claim_id}. Amount: Rs. {amount:,.0f}. "
                f"Insurer denies citing pre-existing disease exclusion."
            ),
            "policy_inception_date": format_date(inception),
            "admission_date": format_date(admission),
            "claimed_condition": condition,
            "icd10_code": icd10,
            "insurer": insurer,
            "product": product,
            "hospital": hospital,
            "claim_id": claim_id,
            "claimed_amount": float(amount),
            "applicable_waiting_period_months": base_wp,
            "elapsed_months": elapsed,
            "ground_truth_verdict": verdict,
            "ground_truth_ruling": ruling,
            "scenario_type": scenario,
        }
        cases.append(case)

    _save_json(cases, "G8_golden_pipeline_waiting_period.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G9: GOLDEN DENIAL ROUTER                                   ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g9():
    print("\n[G9] Building golden_denial_router.json (140 cases)...")
    
    CATEGORIES = [
        "MEDICAL_NECESSITY",
        "PRE_EXISTING_WAITING_PERIOD",
        "POLICY_EXCLUSION",
        "FINANCIAL_LIMIT",
        "DOCUMENTATION",
        "ADMINISTRATIVE_PROCEDURAL",
        "ELIGIBILITY_COVERAGE",
    ]

    templates = {
        "MEDICAL_NECESSITY": [
            "Your claim for {procedure} has been denied as the treatment is not considered medically necessary. Our medical panel has reviewed the case and determined that the procedure is elective in nature.",
            "The insurer has determined that {procedure} does not meet the criteria for medical necessity as per the policy terms. Conservative treatment options have not been exhausted.",
            "Claim denied: The requested {procedure} is classified as an experimental/unproven treatment under current clinical guidelines.",
            "Your request for {procedure} has been denied. The condition can be adequately managed through outpatient treatment without hospitalization.",
            "The medical review board has determined that the proposed {procedure} is cosmetic in nature and does not qualify as medically necessary treatment.",
        ],
        "PRE_EXISTING_WAITING_PERIOD": [
            "Your claim for treatment of {condition} has been denied as it is classified as a pre-existing disease. The {wp}-month waiting period has not been completed.",
            "Claim repudiated: {condition} was pre-existing at the time of policy inception. Waiting period of {wp} months not served.",
            "The condition {condition} is deemed pre-existing based on medical records predating the policy inception. Coverage will begin after the mandatory waiting period.",
            "Your claim is denied under the 24-month specific disease waiting period clause. {condition} falls under the list of specified diseases requiring completion of the waiting period.",
            "Non-disclosure of pre-existing {condition} detected during claim investigation. The proposal form did not mention this condition.",
        ],
        "POLICY_EXCLUSION": [
            "Your claim for {procedure} is excluded under the permanent exclusions section of your policy. This treatment falls under the list of excluded procedures.",
            "Claim denied: Treatment for {condition} is permanently excluded under the policy terms. This includes self-inflicted injuries and substance abuse related conditions.",
            "The claimed dental treatment is excluded under your health insurance policy as it does not arise from an accident.",
            "Infertility treatments including IVF are excluded under the base health insurance plan. A separate fertility rider was not purchased.",
            "AYUSH (Ayurveda, Unani, Siddha, Homeopathy) treatments are not covered under your current policy plan.",
        ],
        "FINANCIAL_LIMIT": [
            "Your claim amount exceeds the remaining sum insured for this policy year. The admissible amount has been limited to the available balance.",
            "Room charges of Rs. {amount}/day exceed the per-day limit of Rs. {sublimit}/day. Proportionate deduction has been applied to all related expenses.",
            "The claimed amount is below the mandatory deductible/excess threshold of Rs. {deductible}. No amount is payable.",
            "Non-medical expenses totaling Rs. {nme_amount} have been deducted as per IRDAI guidelines on NME items.",
            "A mandatory co-payment of 5% has been applied to the admissible claim amount as per policy terms.",
        ],
        "DOCUMENTATION": [
            "Your claim cannot be processed due to missing discharge summary from {hospital}. Please submit the complete hospital discharge report.",
            "Itemized hospital bills with detailed breakup of charges have not been provided. The claim is on hold pending documentation.",
            "Pre-authorization was not obtained before the planned hospitalization. This is mandatory for elective procedures under your policy.",
            "The claim form is incomplete and contains discrepancies between the dates mentioned and the hospital records.",
            "Diagnostic investigation reports (lab reports, radiology) required for claim assessment have not been submitted.",
        ],
        "ADMINISTRATIVE_PROCEDURAL": [
            "Your claim has been denied as it was submitted {days} days after discharge, exceeding the stipulated 30-day filing window.",
            "Hospitalization was not intimated to the TPA within 48 hours as required under the policy terms.",
            "Treatment was taken at a non-network hospital without emergency justification or prior approval.",
            "Policy premium was not paid within the grace period. The policy was lapsed at the time of hospitalization.",
            "This appears to be a duplicate claim. A claim for the same hospitalization has already been processed under another policy.",
        ],
        "ELIGIBILITY_COVERAGE": [
            "The policy was not in force on the date of hospitalization. Your coverage had expired {days} days prior to admission.",
            "The claimant is not listed as an insured member under the active policy. Only the primary policyholder and declared dependents are covered.",
            "Outpatient (OPD) consultation expenses are not covered under your hospitalization policy.",
            "The claimed day care procedure is not listed in the approved day care procedures list under your policy.",
            "Hospitalization was less than 24 hours and the procedure does not qualify as an approved day care treatment.",
        ],
    }

    cases = []
    case_num = 1
    for category in CATEGORIES:
        category_templates = templates[category]
        for j in range(20):
            template = category_templates[j % len(category_templates)]
            proc = random.choice(PROCEDURES_MN)
            ped = random.choice(PED_CONDITIONS)
            name = random.choice(INDIAN_NAMES)
            hospital = random.choice(HOSPITALS)

            text = template.format(
                procedure=proc[0], condition=ped[0], wp=ped[2],
                amount=random.choice([3000, 5000, 8000, 10000]),
                sublimit=random.choice([2000, 3000, 4000]),
                deductible=random.choice([10000, 25000, 50000]),
                nme_amount=random.choice([2500, 5000, 8000, 12000]),
                hospital=hospital,
                days=random.choice([45, 60, 75, 90]),
            )

            case = {
                "case_id": f"G9-{case_num:03d}",
                "raw_denial_paragraph": text,
                "ground_truth_category": category,
                "patient_name": name,
                "source_product": random.choice(ICICI_PRODUCTS),
            }
            cases.append(case)
            case_num += 1

    _save_json(cases, "G9_golden_denial_router.json")
    return len(cases)


# ╔══════════════════════════════════════════════════════════════╗
# ║  G10: GOLDEN HITL BENCHMARK                                 ║
# ╚══════════════════════════════════════════════════════════════╝
def build_g10():
    print("\n[G10] Building golden_hitl_benchmark.json (30 cases)...")
    cases = []

    for i in range(30):
        is_mn = i < 15
        name = random.choice(INDIAN_NAMES)
        hospital = random.choice(HOSPITALS)
        insurer, product, _ = random.choice(ALL_PRODUCTS)
        claim_date = random_date(2023, 2024)
        claim_id = f"CLM-{claim_date.year}-{random.randint(1000, 9999)}"
        amount = random_amount(300000, 2000000)

        if is_mn:
            proc = random.choice(PROCEDURES_MN)
            category = "MEDICAL_NECESSITY"
            condition = proc[0]
            verdict = random.choice(["OVERTURN", "UPHOLD"])
        else:
            ped = random.choice(PED_CONDITIONS)
            category = "PRE_EXISTING_WAITING_PERIOD"
            condition = ped[0]
            verdict = random.choice(["REVERSAL", "UPHELD"])

        # Adjudicator scoring
        persuasiveness = round(random.uniform(3.5, 5.0), 1)
        factual_correctness = round(random.uniform(3.8, 5.0), 1)
        reversal_feasibility = round(random.uniform(0.5, 1.0), 2) if verdict in ["OVERTURN", "REVERSAL"] else round(random.uniform(0.1, 0.4), 2)

        case = {
            "case_id": f"G10-{i+1:03d}",
            "claim_id": claim_id,
            "patient_name": name,
            "category": category,
            "condition": condition,
            "hospital": hospital,
            "insurer": insurer,
            "product": product,
            "claimed_amount": float(amount),
            "claim_date": format_date(claim_date),
            "system_generated_verdict": verdict,
            "adjudicator_consensus": {
                "reviewer_1_verdict": verdict,
                "reviewer_2_verdict": verdict if random.random() > 0.15 else ("OVERTURN" if verdict == "UPHOLD" else "UPHOLD"),
                "appeal_persuasiveness_score": persuasiveness,
                "factual_correctness_score": factual_correctness,
                "reversal_feasibility_score": reversal_feasibility,
                "consensus_verdict": verdict,
                "inter_rater_agreement": round(random.uniform(0.75, 0.95), 2),
            },
            "complete_appeal_pack": {
                "denial_letter_present": True,
                "clinical_evidence_present": True,
                "policy_clause_analysis_present": True,
                "toulmin_reasoning_present": True,
                "appeal_draft_present": True,
            },
        }
        cases.append(case)

    _save_json(cases, "G10_golden_hitl_benchmark.json")
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
    print("  BUILDING ALL 10 GOLDEN EVALUATION BENCHMARK JSONs")
    print(f"  Discovered {len(ALL_PRODUCTS)} products across {len(insurers_list)} insurers: {', '.join(insurers_list)}")
    print("=" * 70)

    counts = {}
    counts["G1_intake_entities"] = build_g1()
    counts["G2_clause_retrieval"] = build_g2()
    counts["G3_clinical_evidence"] = build_g3()
    counts["G4_chronology_ped"] = build_g4()
    counts["G5_reasoning_toulmin"] = build_g5()
    counts["G6_appeal_drafts"] = build_g6()
    counts["G7_pipeline_medical_necessity"] = build_g7()
    counts["G8_pipeline_waiting_period"] = build_g8()
    counts["G9_denial_router"] = build_g9()
    counts["G10_hitl_benchmark"] = build_g10()

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    for name, count in counts.items():
        print(f"  {name:40s} -> {count:5d} cases")
    print(f"\n  Total golden test cases: {sum(counts.values())}")
    print(f"  Output directory: {GOLDEN_DIR}")
    print("=" * 70)
