"""
build_runtime_csvs.py
=====================
Builds all 5 Active Runtime Knowledge-Base CSVs for the Denial Appeal System.

Output:
  data/runtime/
  ├── policy_clauses.csv       (~300 structured clauses from 7 ICICI PDFs)
  ├── denial_reasons.csv       (~80 denial categories from CARC/RARC + IRDAI)
  ├── icd10_codes.csv          (core diagnosis codes for entity validation)
  ├── procedure_codes.csv      (core procedure codes for surgery validation)
  └── nme_exclusions.csv       (~120 non-medical expense items from annexures)
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

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────
BASE_DIR = Path(r"c:\Users\Saketh\Desktop\Major Project")
POLICY_DIR = BASE_DIR / "data" / "policy_wordings"
RUNTIME_DIR = BASE_DIR / "data" / "runtime"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

# Add data folder to path for local imports
DATA_DIR = BASE_DIR / "data"
if str(DATA_DIR) not in sys.path:
    sys.path.insert(0, str(DATA_DIR))

try:
    from policy_discovery import discover_policy_documents
except ImportError:
    from data.policy_discovery import discover_policy_documents

# ╔══════════════════════════════════════════════════════════════╗
# ║  1. POLICY CLAUSES CSV                                      ║
# ╚══════════════════════════════════════════════════════════════╝
def extract_policy_clauses():
    """Extract structured clauses dynamically from all discovered policy PDFs recursively."""
    policies = discover_policy_documents(POLICY_DIR)
    insurers_found = sorted(set(p["insurer"] for p in policies))
    print(f"\n[1/5] Dynamically discovered {len(policies)} policy PDFs across {len(insurers_found)} insurers: {', '.join(insurers_found)}")
    print(f"      Extracting policy_clauses.csv...")
    
    all_clauses = []
    clause_id_counter = 1
    
    # Regex patterns for clause identification
    clause_patterns = [
        # Pattern: IRDAI Standard Code-Excl (Code-Excl01, Code-Excl02)
        re.compile(r'^(Code-Excl\d+)\s*[:\.\-]?\s*(.+)', re.IGNORECASE | re.MULTILINE),
        # Pattern: numbered sections like "1.", "1.1", "1.1.1", "4.3.2"
        re.compile(r'^(\d+(?:\.\d+)*)\s*[:\.\)]\s*(.+)', re.MULTILINE),
        # Pattern: Roman numeral sections
        re.compile(r'^(?:(?:i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii)[\.\)]\s*)(.+)', re.IGNORECASE | re.MULTILINE),
        # Pattern: lettered items (a), (b), etc.
        re.compile(r'^\s*\(?[a-z]\)\s*(.+)', re.MULTILINE),
    ]
    
    # Keywords to classify clause types
    exclusion_keywords = ["exclusion", "excluded", "not cover", "shall not", "not payable", "not liable", "does not include", "code-excl"]
    waiting_period_keywords = ["waiting period", "pre-existing", "moratorium", "continuous coverage", "first year", "second year", "48 months", "36 months", "24 months", "30 days"]
    coverage_keywords = ["cover", "payable", "reimburse", "eligible", "shall pay", "benefit", "indemnify"]
    definition_keywords = ["means", "defined as", "definition", "shall mean", "refers to"]
    exception_keywords = ["except", "exception", "provided that", "unless", "however", "notwithstanding", "subject to"]
    
    for p_info in policies:
        pdf_path = p_info["path"]
        insurer = p_info["insurer"]
        product = p_info["product"]
        product_code = p_info["product_code"]
        
        print(f"  [PDF] Processing: {insurer} | {product} ({p_info['rel_path']})")
        doc = fitz.open(str(pdf_path))
        
        # Extract text page-by-page
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        doc.close()
        
        # Split text into meaningful paragraphs
        paragraphs = re.split(r'\n\s*\n', full_text)
        
        current_section = "General"
        for para in paragraphs:
            para = para.strip()
            if len(para) < 20:  # Skip very short paragraphs
                continue
            
            # Detect section headers
            section_match = re.match(r'^(?:SECTION|PART|CHAPTER|SCHEDULE|ANNEXURE)\s*[-:]?\s*(\w.*?)$', para, re.IGNORECASE)
            if section_match:
                current_section = section_match.group(1).strip()[:100]
                continue
            
            # Try to match clause patterns
            clause_number = ""
            clause_text = para
            
            for pattern in clause_patterns:
                match = pattern.search(para)
                if match:
                    if match.lastindex and match.lastindex >= 1:
                        clause_number = match.group(1).strip() if match.lastindex >= 2 else ""
                        clause_text = match.group(match.lastindex).strip()
                    break
            
            # Classify clause type
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
            
            # Check for exceptions
            has_exception = any(kw in para_lower for kw in exception_keywords)
            exception_text = ""
            if has_exception:
                # Extract the exception portion
                for kw in exception_keywords:
                    idx = para_lower.find(kw)
                    if idx != -1:
                        exception_text = para[idx:idx+300].strip()
                        break
            
            # Detect temporal rules
            temporal_rule = ""
            temporal_patterns = [
                r'(\d+)\s*(?:months?|years?)\s*(?:waiting|period|from)',
                r'(?:within|after|before)\s*(\d+)\s*(?:days?|months?|years?)',
                r'(?:first|second|third|fourth)\s*(?:year|policy year)',
            ]
            for tp in temporal_patterns:
                t_match = re.search(tp, para_lower)
                if t_match:
                    temporal_rule = t_match.group(0).strip()
                    break
            
            # Only keep substantive clauses (skip page numbers, headers, TOC entries)
            if len(clause_text) > 40 and clause_type != "GENERAL":
                clause_id = f"{product_code}-{clause_type[:3]}-{clause_id_counter:04d}"
                
                all_clauses.append({
                    "clause_id": clause_id,
                    "insurer": insurer,
                    "product_name": product,
                    "section": current_section[:100],
                    "clause_number": clause_number[:20],
                    "clause_text": clause_text[:2000],  # Cap at 2000 chars
                    "clause_type": clause_type,
                    "has_exception": has_exception,
                    "exception_text": exception_text[:500] if exception_text else "",
                    "temporal_rule": temporal_rule[:100] if temporal_rule else "",
                })
                clause_id_counter += 1
    
    # Write CSV
    output_path = RUNTIME_DIR / "policy_clauses.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "clause_id", "insurer", "product_name", "section", "clause_number",
            "clause_text", "clause_type", "has_exception", "exception_text", "temporal_rule"
        ])
        writer.writeheader()
        writer.writerows(all_clauses)
    
    print(f"  [OK] policy_clauses.csv: {len(all_clauses)} clauses extracted -> {output_path}")
    return len(all_clauses)


# ╔══════════════════════════════════════════════════════════════╗
# ║  2. DENIAL REASONS CSV                                      ║
# ╚══════════════════════════════════════════════════════════════╝
def build_denial_reasons():
    """Build denial_reasons.csv from CARC/RARC codes + IRDAI denial taxonomy."""
    print("\n[2/5] Building denial_reasons.csv...")
    
    # Comprehensive healthcare denial reasons combining CARC/RARC + IRDAI categories
    reasons = [
        # MEDICAL_NECESSITY denials
        {"reason_id": "MN-001", "category": "MEDICAL_NECESSITY", "sub_category": "Elective Surgery", "reason_text": "Procedure deemed elective and not medically necessary based on clinical guidelines", "carc_code": "50", "typical_clause_type": "EXCLUSION", "appeal_route": "IMR/Ombudsman"},
        {"reason_id": "MN-002", "category": "MEDICAL_NECESSITY", "sub_category": "Conservative Treatment Not Attempted", "reason_text": "Conservative or non-surgical treatment options have not been exhausted prior to surgical intervention", "carc_code": "50", "typical_clause_type": "EXCLUSION", "appeal_route": "IMR/Ombudsman"},
        {"reason_id": "MN-003", "category": "MEDICAL_NECESSITY", "sub_category": "Experimental/Investigational", "reason_text": "Treatment classified as experimental, investigational, or unproven under current medical standards", "carc_code": "50", "typical_clause_type": "EXCLUSION", "appeal_route": "IMR"},
        {"reason_id": "MN-004", "category": "MEDICAL_NECESSITY", "sub_category": "Cosmetic Procedure", "reason_text": "Procedure classified as cosmetic in nature without documented functional impairment", "carc_code": "50", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "MN-005", "category": "MEDICAL_NECESSITY", "sub_category": "Frequency Limit Exceeded", "reason_text": "Number of treatments exceeds medically accepted frequency for the diagnosed condition", "carc_code": "50", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "MN-006", "category": "MEDICAL_NECESSITY", "sub_category": "Alternative Treatment Available", "reason_text": "Less invasive or less costly alternative treatment is available and appropriate", "carc_code": "50", "typical_clause_type": "EXCLUSION", "appeal_route": "IMR"},
        {"reason_id": "MN-007", "category": "MEDICAL_NECESSITY", "sub_category": "Insufficient Clinical Documentation", "reason_text": "Clinical records do not sufficiently demonstrate medical necessity for the requested procedure", "carc_code": "50", "typical_clause_type": "EXCLUSION", "appeal_route": "IMR/Ombudsman"},
        {"reason_id": "MN-008", "category": "MEDICAL_NECESSITY", "sub_category": "Age/Condition Inappropriate", "reason_text": "Requested procedure is not appropriate for the patient's age, condition, or prognosis", "carc_code": "50", "typical_clause_type": "EXCLUSION", "appeal_route": "IMR"},
        {"reason_id": "MN-009", "category": "MEDICAL_NECESSITY", "sub_category": "Outpatient Sufficiency", "reason_text": "Condition can be adequately managed in outpatient or daycare setting; inpatient admission not warranted", "carc_code": "50", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "MN-010", "category": "MEDICAL_NECESSITY", "sub_category": "Diagnostic Test Not Required", "reason_text": "Diagnostic investigation ordered without clinical indication or prior abnormal result", "carc_code": "50", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        
        # PRE_EXISTING_WAITING_PERIOD denials
        {"reason_id": "PW-001", "category": "PRE_EXISTING_WAITING_PERIOD", "sub_category": "Pre-Existing Disease", "reason_text": "Condition classified as pre-existing disease as per policy definition; treatment within specified waiting period", "carc_code": "27", "typical_clause_type": "WAITING_PERIOD", "appeal_route": "Ombudsman"},
        {"reason_id": "PW-002", "category": "PRE_EXISTING_WAITING_PERIOD", "sub_category": "24-Month Specific Disease", "reason_text": "Listed specific disease/condition claimed within the initial 24-month waiting period", "carc_code": "27", "typical_clause_type": "WAITING_PERIOD", "appeal_route": "Ombudsman"},
        {"reason_id": "PW-003", "category": "PRE_EXISTING_WAITING_PERIOD", "sub_category": "48-Month PED", "reason_text": "Pre-existing condition disclosed or discovered; claim within 48-month (4-year) waiting period", "carc_code": "27", "typical_clause_type": "WAITING_PERIOD", "appeal_route": "Ombudsman"},
        {"reason_id": "PW-004", "category": "PRE_EXISTING_WAITING_PERIOD", "sub_category": "30-Day Initial Wait", "reason_text": "Claim filed during the initial 30-day cooling-off/waiting period after policy inception", "carc_code": "27", "typical_clause_type": "WAITING_PERIOD", "appeal_route": "Internal Appeal"},
        {"reason_id": "PW-005", "category": "PRE_EXISTING_WAITING_PERIOD", "sub_category": "Non-Disclosure of PED", "reason_text": "Policyholder failed to disclose pre-existing medical condition in proposal form; policy voidable under Section 45", "carc_code": "27", "typical_clause_type": "WAITING_PERIOD", "appeal_route": "Ombudsman/Court"},
        {"reason_id": "PW-006", "category": "PRE_EXISTING_WAITING_PERIOD", "sub_category": "Moratorium Breach", "reason_text": "Claim denied despite 8-year moratorium period completion; insurer incorrectly invoking pre-existence", "carc_code": "27", "typical_clause_type": "WAITING_PERIOD", "appeal_route": "Ombudsman"},
        {"reason_id": "PW-007", "category": "PRE_EXISTING_WAITING_PERIOD", "sub_category": "Continuous Coverage Gap", "reason_text": "Break in continuous policy renewal reset the waiting period for pre-existing conditions", "carc_code": "27", "typical_clause_type": "WAITING_PERIOD", "appeal_route": "Ombudsman"},
        {"reason_id": "PW-008", "category": "PRE_EXISTING_WAITING_PERIOD", "sub_category": "Portability Wait Reset", "reason_text": "Waiting period credit not granted during insurer-to-insurer portability", "carc_code": "27", "typical_clause_type": "WAITING_PERIOD", "appeal_route": "IRDAI GMS"},
        {"reason_id": "PW-009", "category": "PRE_EXISTING_WAITING_PERIOD", "sub_category": "First Year Exclusion", "reason_text": "Specific surgical procedure excluded during the first policy year", "carc_code": "27", "typical_clause_type": "WAITING_PERIOD", "appeal_route": "Internal Appeal"},
        {"reason_id": "PW-010", "category": "PRE_EXISTING_WAITING_PERIOD", "sub_category": "Congenital Condition", "reason_text": "Condition deemed congenital and excluded under lifetime waiting clause", "carc_code": "27", "typical_clause_type": "WAITING_PERIOD", "appeal_route": "Ombudsman"},
        
        # POLICY_EXCLUSION denials
        {"reason_id": "PE-001", "category": "POLICY_EXCLUSION", "sub_category": "Permanent Exclusion", "reason_text": "Condition permanently excluded under policy terms (e.g., self-inflicted injury, substance abuse, STDs)", "carc_code": "96", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "PE-002", "category": "POLICY_EXCLUSION", "sub_category": "War/Nuclear Risk", "reason_text": "Injury arising from war, nuclear event, or participating in hazardous activity excluded under general exclusions", "carc_code": "96", "typical_clause_type": "EXCLUSION", "appeal_route": "N/A"},
        {"reason_id": "PE-003", "category": "POLICY_EXCLUSION", "sub_category": "Dental Treatment", "reason_text": "Routine dental treatment or procedure not arising from accident excluded under policy terms", "carc_code": "96", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "PE-004", "category": "POLICY_EXCLUSION", "sub_category": "Infertility Treatment", "reason_text": "IVF, fertility treatment, and related procedures excluded under standard health policy", "carc_code": "96", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "PE-005", "category": "POLICY_EXCLUSION", "sub_category": "Maternity (Without Rider)", "reason_text": "Maternity expenses excluded unless specific maternity rider/add-on was purchased", "carc_code": "96", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "PE-006", "category": "POLICY_EXCLUSION", "sub_category": "Obesity Surgery", "reason_text": "Bariatric/weight-loss surgery excluded unless BMI exceeds threshold and comorbidities documented", "carc_code": "96", "typical_clause_type": "EXCLUSION", "appeal_route": "IMR"},
        {"reason_id": "PE-007", "category": "POLICY_EXCLUSION", "sub_category": "AYUSH Not Covered", "reason_text": "Alternative medicine (Ayurveda, Unani, Siddha, Homeopathy) not covered under base plan", "carc_code": "96", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "PE-008", "category": "POLICY_EXCLUSION", "sub_category": "Refractive Error", "reason_text": "Corrective eye surgery for refractive errors (LASIK, PRK) excluded under policy terms", "carc_code": "96", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "PE-009", "category": "POLICY_EXCLUSION", "sub_category": "Unproven Treatment", "reason_text": "Treatment not recognized by established medical bodies or not evidence-based", "carc_code": "96", "typical_clause_type": "EXCLUSION", "appeal_route": "IMR"},
        {"reason_id": "PE-010", "category": "POLICY_EXCLUSION", "sub_category": "Hazardous Activity", "reason_text": "Injury sustained during participation in extreme sports, racing, or hazardous recreation", "carc_code": "96", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        
        # FINANCIAL_LIMIT denials
        {"reason_id": "FL-001", "category": "FINANCIAL_LIMIT", "sub_category": "Sum Insured Exhausted", "reason_text": "Total admissible claim amount exceeds the remaining sum insured for the policy year", "carc_code": "119", "typical_clause_type": "COVERAGE", "appeal_route": "Internal Appeal"},
        {"reason_id": "FL-002", "category": "FINANCIAL_LIMIT", "sub_category": "Sub-Limit Exceeded", "reason_text": "Specific expense category exceeds the applicable sub-limit (room rent, ICU, ambulance)", "carc_code": "119", "typical_clause_type": "COVERAGE", "appeal_route": "Internal Appeal"},
        {"reason_id": "FL-003", "category": "FINANCIAL_LIMIT", "sub_category": "Room Rent Capping", "reason_text": "Room charges exceed the per-day limit; proportionate deduction applied to all medical expenses", "carc_code": "119", "typical_clause_type": "COVERAGE", "appeal_route": "Ombudsman"},
        {"reason_id": "FL-004", "category": "FINANCIAL_LIMIT", "sub_category": "Deductible Not Met", "reason_text": "Claim amount is below the mandatory deductible/excess threshold", "carc_code": "119", "typical_clause_type": "COVERAGE", "appeal_route": "Internal Appeal"},
        {"reason_id": "FL-005", "category": "FINANCIAL_LIMIT", "sub_category": "Co-Payment Applied", "reason_text": "Mandatory co-payment percentage deducted from the admissible claim amount", "carc_code": "119", "typical_clause_type": "COVERAGE", "appeal_route": "Internal Appeal"},
        {"reason_id": "FL-006", "category": "FINANCIAL_LIMIT", "sub_category": "Non-Medical Expenses", "reason_text": "Non-medical expenses (NME) deducted as per IRDAI guidelines Annexure IV", "carc_code": "119", "typical_clause_type": "COVERAGE", "appeal_route": "Internal Appeal"},
        {"reason_id": "FL-007", "category": "FINANCIAL_LIMIT", "sub_category": "Reasonable & Customary", "reason_text": "Charges exceed reasonable and customary rates for the geographic area and facility type", "carc_code": "119", "typical_clause_type": "COVERAGE", "appeal_route": "Ombudsman"},
        {"reason_id": "FL-008", "category": "FINANCIAL_LIMIT", "sub_category": "Package Rate Applied", "reason_text": "Treatment covered under network hospital package rate; excess charges non-reimbursable", "carc_code": "119", "typical_clause_type": "COVERAGE", "appeal_route": "Internal Appeal"},
        {"reason_id": "FL-009", "category": "FINANCIAL_LIMIT", "sub_category": "Cumulative Bonus Lost", "reason_text": "No-claim bonus/cumulative bonus not applicable due to prior year claim utilization", "carc_code": "119", "typical_clause_type": "COVERAGE", "appeal_route": "Internal Appeal"},
        {"reason_id": "FL-010", "category": "FINANCIAL_LIMIT", "sub_category": "Super Top-Up Deductible", "reason_text": "Aggregate deductible for super top-up policy not met by prior base policy utilization", "carc_code": "119", "typical_clause_type": "COVERAGE", "appeal_route": "Internal Appeal"},
        
        # DOCUMENTATION denials
        {"reason_id": "DC-001", "category": "DOCUMENTATION", "sub_category": "Missing Discharge Summary", "reason_text": "Final discharge summary from treating hospital not submitted with the claim documents", "carc_code": "16", "typical_clause_type": "GENERAL", "appeal_route": "Resubmission"},
        {"reason_id": "DC-002", "category": "DOCUMENTATION", "sub_category": "Incomplete Bills", "reason_text": "Itemized hospital bills with breakup of charges not provided or partially submitted", "carc_code": "16", "typical_clause_type": "GENERAL", "appeal_route": "Resubmission"},
        {"reason_id": "DC-003", "category": "DOCUMENTATION", "sub_category": "Missing Investigation Reports", "reason_text": "Diagnostic investigation reports (lab, radiology, pathology) required for claim assessment not submitted", "carc_code": "16", "typical_clause_type": "GENERAL", "appeal_route": "Resubmission"},
        {"reason_id": "DC-004", "category": "DOCUMENTATION", "sub_category": "No Pre-Authorization", "reason_text": "Planned hospitalization proceeding without prior pre-authorization from TPA/insurer as required", "carc_code": "16", "typical_clause_type": "GENERAL", "appeal_route": "Internal Appeal"},
        {"reason_id": "DC-005", "category": "DOCUMENTATION", "sub_category": "KYC Non-Compliance", "reason_text": "Identity documents (Aadhaar, PAN, photo ID) not submitted with the claim application", "carc_code": "16", "typical_clause_type": "GENERAL", "appeal_route": "Resubmission"},
        {"reason_id": "DC-006", "category": "DOCUMENTATION", "sub_category": "Prescription Missing", "reason_text": "Treating physician prescription for the claimed treatment or medication not provided", "carc_code": "16", "typical_clause_type": "GENERAL", "appeal_route": "Resubmission"},
        {"reason_id": "DC-007", "category": "DOCUMENTATION", "sub_category": "Claim Form Incomplete", "reason_text": "Claim intimation form incomplete, unsigned, or contains discrepancies with hospital records", "carc_code": "16", "typical_clause_type": "GENERAL", "appeal_route": "Resubmission"},
        {"reason_id": "DC-008", "category": "DOCUMENTATION", "sub_category": "FIR Not Submitted", "reason_text": "Accident/medico-legal case requiring FIR/MLC report which was not submitted", "carc_code": "16", "typical_clause_type": "GENERAL", "appeal_route": "Resubmission"},
        {"reason_id": "DC-009", "category": "DOCUMENTATION", "sub_category": "Previous Treatment Records", "reason_text": "Prior medical records demonstrating treatment history for the condition not provided", "carc_code": "16", "typical_clause_type": "GENERAL", "appeal_route": "Resubmission"},
        {"reason_id": "DC-010", "category": "DOCUMENTATION", "sub_category": "Referral Letter Missing", "reason_text": "Specialist referral letter from primary physician not submitted for the claimed consultation", "carc_code": "16", "typical_clause_type": "GENERAL", "appeal_route": "Resubmission"},
        
        # ADMINISTRATIVE_PROCEDURAL denials
        {"reason_id": "AP-001", "category": "ADMINISTRATIVE_PROCEDURAL", "sub_category": "Late Claim Filing", "reason_text": "Claim submitted beyond the stipulated time limit (usually 15-30 days post discharge)", "carc_code": "29", "typical_clause_type": "GENERAL", "appeal_route": "Internal Appeal"},
        {"reason_id": "AP-002", "category": "ADMINISTRATIVE_PROCEDURAL", "sub_category": "Non-Network Hospital", "reason_text": "Treatment taken at non-network hospital without emergency justification or prior approval", "carc_code": "29", "typical_clause_type": "GENERAL", "appeal_route": "Internal Appeal"},
        {"reason_id": "AP-003", "category": "ADMINISTRATIVE_PROCEDURAL", "sub_category": "Late Intimation", "reason_text": "Hospitalization not intimated to insurer/TPA within 24-48 hours as per policy terms", "carc_code": "29", "typical_clause_type": "GENERAL", "appeal_route": "Internal Appeal"},
        {"reason_id": "AP-004", "category": "ADMINISTRATIVE_PROCEDURAL", "sub_category": "Planned Without Pre-Auth", "reason_text": "Planned/elective procedure without mandatory pre-authorization approval", "carc_code": "29", "typical_clause_type": "GENERAL", "appeal_route": "Internal Appeal"},
        {"reason_id": "AP-005", "category": "ADMINISTRATIVE_PROCEDURAL", "sub_category": "Premium Lapsed", "reason_text": "Policy premium not paid within the grace period; policy lapsed at time of hospitalization", "carc_code": "29", "typical_clause_type": "GENERAL", "appeal_route": "IRDAI GMS"},
        {"reason_id": "AP-006", "category": "ADMINISTRATIVE_PROCEDURAL", "sub_category": "Duplicate Claim", "reason_text": "Same claim already filed and settled under another policy or insurer", "carc_code": "29", "typical_clause_type": "GENERAL", "appeal_route": "Internal Appeal"},
        {"reason_id": "AP-007", "category": "ADMINISTRATIVE_PROCEDURAL", "sub_category": "Non-Compliance Post Discharge", "reason_text": "Follow-up requirements (e.g., physiotherapy attendance) not complied with", "carc_code": "29", "typical_clause_type": "GENERAL", "appeal_route": "Internal Appeal"},
        {"reason_id": "AP-008", "category": "ADMINISTRATIVE_PROCEDURAL", "sub_category": "Incorrect Hospital Category", "reason_text": "Hospital does not meet the minimum bed/registration criteria under policy definition", "carc_code": "29", "typical_clause_type": "GENERAL", "appeal_route": "Ombudsman"},
        {"reason_id": "AP-009", "category": "ADMINISTRATIVE_PROCEDURAL", "sub_category": "Age Limit Exceeded", "reason_text": "Insured person exceeds the maximum entry age or renewal age limit for the policy", "carc_code": "29", "typical_clause_type": "GENERAL", "appeal_route": "Internal Appeal"},
        {"reason_id": "AP-010", "category": "ADMINISTRATIVE_PROCEDURAL", "sub_category": "Geographical Exclusion", "reason_text": "Treatment taken outside India or outside the policy's geographical coverage territory", "carc_code": "29", "typical_clause_type": "GENERAL", "appeal_route": "Internal Appeal"},
        
        # ELIGIBILITY_COVERAGE denials
        {"reason_id": "EC-001", "category": "ELIGIBILITY_COVERAGE", "sub_category": "Policy Not Active", "reason_text": "Policy was not in force on the date of hospitalization or treatment", "carc_code": "26", "typical_clause_type": "GENERAL", "appeal_route": "Internal Appeal"},
        {"reason_id": "EC-002", "category": "ELIGIBILITY_COVERAGE", "sub_category": "Member Not Covered", "reason_text": "Claimant is not a listed insured member under the active policy", "carc_code": "26", "typical_clause_type": "GENERAL", "appeal_route": "Internal Appeal"},
        {"reason_id": "EC-003", "category": "ELIGIBILITY_COVERAGE", "sub_category": "OPD Not Covered", "reason_text": "Outpatient consultation and diagnostic expenses not covered under base hospitalization policy", "carc_code": "26", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "EC-004", "category": "ELIGIBILITY_COVERAGE", "sub_category": "Day Care Not Listed", "reason_text": "Day care procedure claimed is not in the approved list of day care treatments under the policy", "carc_code": "26", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "EC-005", "category": "ELIGIBILITY_COVERAGE", "sub_category": "Minimum Hospitalization Not Met", "reason_text": "Hospitalization less than 24 hours and procedure not in approved day care list", "carc_code": "26", "typical_clause_type": "EXCLUSION", "appeal_route": "Ombudsman"},
        {"reason_id": "EC-006", "category": "ELIGIBILITY_COVERAGE", "sub_category": "Coverage Territory", "reason_text": "Treatment location falls outside the geographical coverage area of the policy", "carc_code": "26", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "EC-007", "category": "ELIGIBILITY_COVERAGE", "sub_category": "Age Band Restriction", "reason_text": "Specific coverage limited to certain age bands; claimant outside eligible age range", "carc_code": "26", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "EC-008", "category": "ELIGIBILITY_COVERAGE", "sub_category": "Rider Not Purchased", "reason_text": "Optional coverage rider (maternity, dental, OPD) not purchased; claim under base plan ineligible", "carc_code": "26", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
        {"reason_id": "EC-009", "category": "ELIGIBILITY_COVERAGE", "sub_category": "Domiciliary Treatment", "reason_text": "Home treatment/domiciliary hospitalization not meeting policy criteria for coverage", "carc_code": "26", "typical_clause_type": "EXCLUSION", "appeal_route": "Ombudsman"},
        {"reason_id": "EC-010", "category": "ELIGIBILITY_COVERAGE", "sub_category": "Second Opinion Required", "reason_text": "Policy requires second medical opinion before proceeding; second opinion not obtained", "carc_code": "26", "typical_clause_type": "EXCLUSION", "appeal_route": "Internal Appeal"},
    ]
    
    output_path = RUNTIME_DIR / "denial_reasons.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "reason_id", "category", "sub_category", "reason_text",
            "carc_code", "typical_clause_type", "appeal_route"
        ])
        writer.writeheader()
        writer.writerows(reasons)
    
    print(f"  [OK] denial_reasons.csv: {len(reasons)} denial reasons -> {output_path}")
    return len(reasons)


# ╔══════════════════════════════════════════════════════════════╗
# ║  3. ICD-10 CODES CSV                                        ║
# ╚══════════════════════════════════════════════════════════════╝
def build_icd10_codes():
    """Build icd10_codes.csv with healthcare-relevant diagnosis codes."""
    print("\n[3/5] Building icd10_codes.csv...")
    
    # Core ICD-10-CM codes relevant to health insurance denial appeals
    # Organized by system/category commonly seen in claim denials
    codes = [
        # Cardiovascular
        {"code": "I10", "short_description": "Essential (primary) hypertension", "long_description": "Essential (primary) hypertension", "is_billable": True},
        {"code": "I11.0", "short_description": "Hypertensive heart disease with heart failure", "long_description": "Hypertensive heart disease with heart failure", "is_billable": True},
        {"code": "I11.9", "short_description": "Hypertensive heart disease without heart failure", "long_description": "Hypertensive heart disease without heart failure", "is_billable": True},
        {"code": "I12.0", "short_description": "Hypertensive chronic kidney disease with stage 5 CKD", "long_description": "Hypertensive chronic kidney disease with stage 5 chronic kidney disease or end stage renal disease", "is_billable": True},
        {"code": "I12.9", "short_description": "Hypertensive chronic kidney disease with stage 1-4 CKD", "long_description": "Hypertensive chronic kidney disease with stage 1 through stage 4 chronic kidney disease, or unspecified chronic kidney disease", "is_billable": True},
        {"code": "I20.0", "short_description": "Unstable angina", "long_description": "Unstable angina", "is_billable": True},
        {"code": "I21.0", "short_description": "ST elevation myocardial infarction anterior wall", "long_description": "ST elevation (STEMI) myocardial infarction involving left main coronary artery", "is_billable": True},
        {"code": "I21.3", "short_description": "ST elevation myocardial infarction unspecified site", "long_description": "ST elevation (STEMI) myocardial infarction of unspecified site", "is_billable": True},
        {"code": "I25.10", "short_description": "Atherosclerotic heart disease of native coronary artery", "long_description": "Atherosclerotic heart disease of native coronary artery without angina pectoris", "is_billable": True},
        {"code": "I25.110", "short_description": "Atherosclerotic heart disease with unstable angina", "long_description": "Atherosclerotic heart disease of native coronary artery with unstable angina pectoris", "is_billable": True},
        {"code": "I48.0", "short_description": "Paroxysmal atrial fibrillation", "long_description": "Paroxysmal atrial fibrillation", "is_billable": True},
        {"code": "I48.91", "short_description": "Unspecified atrial fibrillation", "long_description": "Unspecified atrial fibrillation", "is_billable": True},
        {"code": "I50.9", "short_description": "Heart failure, unspecified", "long_description": "Heart failure, unspecified", "is_billable": True},
        {"code": "I63.9", "short_description": "Cerebral infarction, unspecified", "long_description": "Cerebral infarction, unspecified", "is_billable": True},
        {"code": "I70.0", "short_description": "Atherosclerosis of aorta", "long_description": "Atherosclerosis of aorta", "is_billable": True},
        
        # Diabetes
        {"code": "E11.9", "short_description": "Type 2 diabetes mellitus without complications", "long_description": "Type 2 diabetes mellitus without complications", "is_billable": True},
        {"code": "E11.65", "short_description": "Type 2 diabetes with hyperglycemia", "long_description": "Type 2 diabetes mellitus with hyperglycemia", "is_billable": True},
        {"code": "E11.21", "short_description": "Type 2 diabetes with diabetic nephropathy", "long_description": "Type 2 diabetes mellitus with diabetic nephropathy", "is_billable": True},
        {"code": "E11.22", "short_description": "Type 2 diabetes with diabetic CKD", "long_description": "Type 2 diabetes mellitus with diabetic chronic kidney disease", "is_billable": True},
        {"code": "E11.40", "short_description": "Type 2 diabetes with diabetic neuropathy", "long_description": "Type 2 diabetes mellitus with diabetic neuropathy, unspecified", "is_billable": True},
        {"code": "E11.311", "short_description": "Type 2 diabetes with diabetic retinopathy", "long_description": "Type 2 diabetes mellitus with unspecified diabetic retinopathy with macular edema", "is_billable": True},
        {"code": "E10.9", "short_description": "Type 1 diabetes mellitus without complications", "long_description": "Type 1 diabetes mellitus without complications", "is_billable": True},
        
        # Musculoskeletal/Orthopedic (common in denial appeals)
        {"code": "M17.0", "short_description": "Bilateral primary osteoarthritis of knee", "long_description": "Bilateral primary osteoarthritis of knee", "is_billable": True},
        {"code": "M17.11", "short_description": "Primary osteoarthritis, right knee", "long_description": "Primary osteoarthritis, right knee", "is_billable": True},
        {"code": "M17.12", "short_description": "Primary osteoarthritis, left knee", "long_description": "Primary osteoarthritis, left knee", "is_billable": True},
        {"code": "M16.0", "short_description": "Bilateral primary osteoarthritis of hip", "long_description": "Bilateral primary osteoarthritis of hip", "is_billable": True},
        {"code": "M16.11", "short_description": "Primary osteoarthritis, right hip", "long_description": "Primary osteoarthritis, right hip", "is_billable": True},
        {"code": "M47.812", "short_description": "Spondylosis without myelopathy cervical", "long_description": "Spondylosis without myelopathy or radiculopathy, cervical region", "is_billable": True},
        {"code": "M47.816", "short_description": "Spondylosis without myelopathy lumbar", "long_description": "Spondylosis without myelopathy or radiculopathy, lumbar region", "is_billable": True},
        {"code": "M51.16", "short_description": "Intervertebral disc degeneration lumbar", "long_description": "Intervertebral disc degeneration, lumbar region", "is_billable": True},
        {"code": "M54.5", "short_description": "Low back pain", "long_description": "Low back pain", "is_billable": True},
        {"code": "M79.3", "short_description": "Panniculitis, unspecified", "long_description": "Panniculitis, unspecified", "is_billable": True},
        {"code": "S72.001A", "short_description": "Fracture of unspecified part of neck of right femur", "long_description": "Fracture of unspecified part of neck of right femur, initial encounter for closed fracture", "is_billable": True},
        {"code": "S82.001A", "short_description": "Unspecified fracture of right patella", "long_description": "Unspecified fracture of right patella, initial encounter for closed fracture", "is_billable": True},
        
        # Respiratory
        {"code": "J18.9", "short_description": "Pneumonia, unspecified organism", "long_description": "Pneumonia, unspecified organism", "is_billable": True},
        {"code": "J44.1", "short_description": "COPD with acute exacerbation", "long_description": "Chronic obstructive pulmonary disease with (acute) exacerbation", "is_billable": True},
        {"code": "J45.20", "short_description": "Mild intermittent asthma, uncomplicated", "long_description": "Mild intermittent asthma, uncomplicated", "is_billable": True},
        {"code": "J45.41", "short_description": "Moderate persistent asthma with acute exacerbation", "long_description": "Moderate persistent asthma with (acute) exacerbation", "is_billable": True},
        {"code": "J96.00", "short_description": "Acute respiratory failure", "long_description": "Acute respiratory failure, unspecified whether with hypoxia or hypercapnia", "is_billable": True},
        
        # Renal/Urological
        {"code": "N18.6", "short_description": "End stage renal disease", "long_description": "End stage renal disease", "is_billable": True},
        {"code": "N18.3", "short_description": "Chronic kidney disease, stage 3", "long_description": "Chronic kidney disease, stage 3 (moderate)", "is_billable": True},
        {"code": "N20.0", "short_description": "Calculus of kidney", "long_description": "Calculus of kidney", "is_billable": True},
        {"code": "N40.0", "short_description": "Benign prostatic hyperplasia without obstruction", "long_description": "Benign prostatic hyperplasia without lower urinary tract symptoms", "is_billable": True},
        
        # Gastrointestinal
        {"code": "K35.80", "short_description": "Unspecified acute appendicitis", "long_description": "Unspecified acute appendicitis", "is_billable": True},
        {"code": "K40.90", "short_description": "Unilateral inguinal hernia without obstruction", "long_description": "Unilateral inguinal hernia, without obstruction or gangrene, not specified as recurrent", "is_billable": True},
        {"code": "K80.00", "short_description": "Calculus of gallbladder with acute cholecystitis", "long_description": "Calculus of gallbladder with acute cholecystitis without obstruction", "is_billable": True},
        {"code": "K80.20", "short_description": "Calculus of gallbladder without cholecystitis", "long_description": "Calculus of gallbladder without cholecystitis without obstruction", "is_billable": True},
        {"code": "K21.0", "short_description": "GERD with esophagitis", "long_description": "Gastro-esophageal reflux disease with esophagitis", "is_billable": True},
        {"code": "K57.30", "short_description": "Diverticulosis of large intestine without hemorrhage", "long_description": "Diverticulosis of large intestine without perforation or abscess without bleeding", "is_billable": True},
        
        # Neoplasms
        {"code": "C50.911", "short_description": "Malignant neoplasm of right breast", "long_description": "Malignant neoplasm of unspecified site of right female breast", "is_billable": True},
        {"code": "C34.90", "short_description": "Malignant neoplasm of lung", "long_description": "Malignant neoplasm of unspecified part of unspecified bronchus or lung", "is_billable": True},
        {"code": "C61", "short_description": "Malignant neoplasm of prostate", "long_description": "Malignant neoplasm of prostate", "is_billable": True},
        {"code": "C18.9", "short_description": "Malignant neoplasm of colon, unspecified", "long_description": "Malignant neoplasm of colon, unspecified", "is_billable": True},
        {"code": "C73", "short_description": "Malignant neoplasm of thyroid gland", "long_description": "Malignant neoplasm of thyroid gland", "is_billable": True},
        {"code": "D25.9", "short_description": "Leiomyoma of uterus, unspecified", "long_description": "Leiomyoma of uterus, unspecified", "is_billable": True},
        
        # Neurological
        {"code": "G20", "short_description": "Parkinson's disease", "long_description": "Parkinson's disease", "is_billable": True},
        {"code": "G35", "short_description": "Multiple sclerosis", "long_description": "Multiple sclerosis", "is_billable": True},
        {"code": "G40.909", "short_description": "Epilepsy, unspecified, not intractable", "long_description": "Epilepsy, unspecified, not intractable, without status epilepticus", "is_billable": True},
        {"code": "G43.909", "short_description": "Migraine, unspecified, not intractable", "long_description": "Migraine, unspecified, not intractable, without status migrainosus", "is_billable": True},
        
        # Eye
        {"code": "H25.9", "short_description": "Unspecified age-related cataract", "long_description": "Unspecified age-related cataract", "is_billable": True},
        {"code": "H40.10X0", "short_description": "Unspecified open-angle glaucoma", "long_description": "Unspecified open-angle glaucoma, stage unspecified", "is_billable": True},
        {"code": "H52.10", "short_description": "Myopia, unspecified eye", "long_description": "Myopia, unspecified eye", "is_billable": True},
        
        # Metabolic
        {"code": "E03.9", "short_description": "Hypothyroidism, unspecified", "long_description": "Hypothyroidism, unspecified", "is_billable": True},
        {"code": "E05.90", "short_description": "Thyrotoxicosis, unspecified", "long_description": "Thyrotoxicosis, unspecified without thyrotoxic crisis or storm", "is_billable": True},
        {"code": "E78.5", "short_description": "Hyperlipidemia, unspecified", "long_description": "Hyperlipidemia, unspecified", "is_billable": True},
        {"code": "E66.01", "short_description": "Morbid (severe) obesity due to excess calories", "long_description": "Morbid (severe) obesity due to excess calories", "is_billable": True},
        
        # Infectious
        {"code": "A09", "short_description": "Infectious gastroenteritis and colitis", "long_description": "Infectious gastroenteritis and colitis, unspecified", "is_billable": True},
        {"code": "A41.9", "short_description": "Sepsis, unspecified organism", "long_description": "Sepsis, unspecified organism", "is_billable": True},
        {"code": "B34.9", "short_description": "Viral infection, unspecified", "long_description": "Viral infection, unspecified", "is_billable": True},
        {"code": "A90", "short_description": "Dengue fever [classical dengue]", "long_description": "Dengue fever [classical dengue]", "is_billable": True},
        {"code": "A01.0", "short_description": "Typhoid fever", "long_description": "Typhoid fever", "is_billable": True},
        {"code": "B50.9", "short_description": "Plasmodium falciparum malaria, unspecified", "long_description": "Plasmodium falciparum malaria, unspecified", "is_billable": True},
        
        # Pregnancy/Maternity (common exclusion check)
        {"code": "O80", "short_description": "Encounter for full-term uncomplicated delivery", "long_description": "Encounter for full-term uncomplicated delivery", "is_billable": True},
        {"code": "O82", "short_description": "Encounter for cesarean delivery", "long_description": "Encounter for cesarean delivery without indication", "is_billable": True},
        
        # Mental Health
        {"code": "F32.9", "short_description": "Major depressive disorder, single episode", "long_description": "Major depressive disorder, single episode, unspecified", "is_billable": True},
        {"code": "F41.9", "short_description": "Anxiety disorder, unspecified", "long_description": "Anxiety disorder, unspecified", "is_billable": True},
        
        # Hypertensive Nephropathy (specific to PED cases)
        {"code": "I12.0", "short_description": "Hypertensive CKD stage 5", "long_description": "Hypertensive chronic kidney disease with stage 5 chronic kidney disease or end stage renal disease", "is_billable": True},
        {"code": "N08", "short_description": "Glomerular disorders in diseases classified elsewhere", "long_description": "Glomerular disorders in diseases classified elsewhere", "is_billable": True},
    ]
    
    output_path = RUNTIME_DIR / "icd10_codes.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "short_description", "long_description", "is_billable"])
        writer.writeheader()
        writer.writerows(codes)
    
    print(f"  [OK] icd10_codes.csv: {len(codes)} ICD-10 codes -> {output_path}")
    return len(codes)


# ╔══════════════════════════════════════════════════════════════╗
# ║  4. PROCEDURE CODES CSV                                     ║
# ╚══════════════════════════════════════════════════════════════╝
def build_procedure_codes():
    """Build procedure_codes.csv with healthcare-relevant HCPCS/CPT codes."""
    print("\n[4/5] Building procedure_codes.csv...")
    
    codes = [
        # Orthopedic Surgeries (high denial rate)
        {"hcpcs_code": "27447", "short_description": "Total Knee Replacement (TKR)", "category": "Orthopedic Surgery"},
        {"hcpcs_code": "27130", "short_description": "Total Hip Replacement (THR)", "category": "Orthopedic Surgery"},
        {"hcpcs_code": "27446", "short_description": "Revision of Total Knee Arthroplasty", "category": "Orthopedic Surgery"},
        {"hcpcs_code": "27236", "short_description": "Open Treatment of Femoral Fracture", "category": "Orthopedic Surgery"},
        {"hcpcs_code": "22612", "short_description": "Lumbar Spinal Fusion", "category": "Orthopedic Surgery"},
        {"hcpcs_code": "22551", "short_description": "Cervical Spinal Fusion, Anterior", "category": "Orthopedic Surgery"},
        {"hcpcs_code": "63030", "short_description": "Lumbar Laminectomy/Discectomy", "category": "Orthopedic Surgery"},
        {"hcpcs_code": "29881", "short_description": "Arthroscopy Knee with Meniscectomy", "category": "Orthopedic Surgery"},
        {"hcpcs_code": "23472", "short_description": "Total Shoulder Replacement", "category": "Orthopedic Surgery"},
        {"hcpcs_code": "27245", "short_description": "ORIF Intertrochanteric Femoral Fracture", "category": "Orthopedic Surgery"},
        
        # Cardiovascular
        {"hcpcs_code": "33533", "short_description": "Coronary Artery Bypass Graft (CABG) Single", "category": "Cardiovascular Surgery"},
        {"hcpcs_code": "33534", "short_description": "Coronary Artery Bypass Graft (CABG) Two", "category": "Cardiovascular Surgery"},
        {"hcpcs_code": "33535", "short_description": "Coronary Artery Bypass Graft (CABG) Three", "category": "Cardiovascular Surgery"},
        {"hcpcs_code": "92928", "short_description": "Percutaneous Coronary Stent Placement", "category": "Cardiovascular Surgery"},
        {"hcpcs_code": "92920", "short_description": "Percutaneous Transluminal Coronary Angioplasty (PTCA)", "category": "Cardiovascular Surgery"},
        {"hcpcs_code": "33405", "short_description": "Aortic Valve Replacement", "category": "Cardiovascular Surgery"},
        {"hcpcs_code": "33430", "short_description": "Mitral Valve Replacement", "category": "Cardiovascular Surgery"},
        {"hcpcs_code": "93458", "short_description": "Cardiac Catheterization Left Heart", "category": "Cardiovascular Diagnostics"},
        {"hcpcs_code": "33249", "short_description": "ICD/Pacemaker Implantation", "category": "Cardiovascular Surgery"},
        {"hcpcs_code": "34800", "short_description": "Endovascular Repair Infrarenal Aortic Aneurysm", "category": "Cardiovascular Surgery"},
        
        # General Surgery
        {"hcpcs_code": "47562", "short_description": "Laparoscopic Cholecystectomy", "category": "General Surgery"},
        {"hcpcs_code": "47563", "short_description": "Laparoscopic Cholecystectomy with Cholangiography", "category": "General Surgery"},
        {"hcpcs_code": "44970", "short_description": "Laparoscopic Appendectomy", "category": "General Surgery"},
        {"hcpcs_code": "49505", "short_description": "Inguinal Hernia Repair", "category": "General Surgery"},
        {"hcpcs_code": "49650", "short_description": "Laparoscopic Inguinal Hernia Repair", "category": "General Surgery"},
        {"hcpcs_code": "49560", "short_description": "Ventral/Incisional Hernia Repair", "category": "General Surgery"},
        {"hcpcs_code": "43239", "short_description": "Upper GI Endoscopy with Biopsy", "category": "GI Diagnostics"},
        {"hcpcs_code": "45378", "short_description": "Colonoscopy Diagnostic", "category": "GI Diagnostics"},
        {"hcpcs_code": "45385", "short_description": "Colonoscopy with Polypectomy", "category": "GI Diagnostics"},
        {"hcpcs_code": "43280", "short_description": "Laparoscopic Fundoplication (Anti-Reflux)", "category": "General Surgery"},
        
        # Urology
        {"hcpcs_code": "52601", "short_description": "TURP (Transurethral Resection of Prostate)", "category": "Urology"},
        {"hcpcs_code": "52353", "short_description": "Ureteroscopy with Lithotripsy", "category": "Urology"},
        {"hcpcs_code": "50590", "short_description": "Extracorporeal Shock Wave Lithotripsy (ESWL)", "category": "Urology"},
        {"hcpcs_code": "50080", "short_description": "Percutaneous Nephrolithotomy (PCNL)", "category": "Urology"},
        {"hcpcs_code": "55866", "short_description": "Laparoscopic Radical Prostatectomy", "category": "Urology"},
        
        # Ophthalmology
        {"hcpcs_code": "66984", "short_description": "Cataract Surgery with IOL Implantation", "category": "Ophthalmology"},
        {"hcpcs_code": "65855", "short_description": "Trabeculoplasty by Laser", "category": "Ophthalmology"},
        {"hcpcs_code": "67028", "short_description": "Intravitreal Injection", "category": "Ophthalmology"},
        {"hcpcs_code": "65760", "short_description": "Keratomileusis (LASIK)", "category": "Ophthalmology"},
        
        # Neurosurgery
        {"hcpcs_code": "61510", "short_description": "Craniotomy for Tumor Removal", "category": "Neurosurgery"},
        {"hcpcs_code": "61624", "short_description": "Transcatheter Embolization CNS", "category": "Neurosurgery"},
        {"hcpcs_code": "63047", "short_description": "Laminectomy Lumbar with Decompression", "category": "Neurosurgery"},
        
        # Oncology/Cancer
        {"hcpcs_code": "19301", "short_description": "Mastectomy, Partial (Lumpectomy)", "category": "Oncology Surgery"},
        {"hcpcs_code": "19303", "short_description": "Mastectomy, Simple Complete", "category": "Oncology Surgery"},
        {"hcpcs_code": "38720", "short_description": "Cervical Lymphadenectomy (Radical)", "category": "Oncology Surgery"},
        {"hcpcs_code": "77385", "short_description": "Intensity Modulated Radiation Therapy (IMRT)", "category": "Radiation Oncology"},
        {"hcpcs_code": "96413", "short_description": "Chemotherapy Administration IV Infusion", "category": "Medical Oncology"},
        
        # Bariatric (commonly denied)
        {"hcpcs_code": "43775", "short_description": "Laparoscopic Sleeve Gastrectomy", "category": "Bariatric Surgery"},
        {"hcpcs_code": "43644", "short_description": "Laparoscopic Roux-en-Y Gastric Bypass", "category": "Bariatric Surgery"},
        
        # ENT
        {"hcpcs_code": "42820", "short_description": "Tonsillectomy and Adenoidectomy", "category": "ENT Surgery"},
        {"hcpcs_code": "31255", "short_description": "Nasal/Sinus Endoscopy with Ethmoidectomy", "category": "ENT Surgery"},
        {"hcpcs_code": "30520", "short_description": "Septoplasty", "category": "ENT Surgery"},
        
        # Obstetrics
        {"hcpcs_code": "59510", "short_description": "Cesarean Delivery", "category": "Obstetrics"},
        {"hcpcs_code": "59400", "short_description": "Routine Obstetric Care Including Vaginal Delivery", "category": "Obstetrics"},
        
        # Dialysis
        {"hcpcs_code": "90935", "short_description": "Hemodialysis, Single Session", "category": "Dialysis"},
        {"hcpcs_code": "90945", "short_description": "Dialysis, Other Than Hemodialysis", "category": "Dialysis"},
        {"hcpcs_code": "36800", "short_description": "AV Fistula Creation for Hemodialysis", "category": "Dialysis Access"},
        
        # Rehabilitation (often denied)
        {"hcpcs_code": "97110", "short_description": "Therapeutic Exercise", "category": "Physical Therapy"},
        {"hcpcs_code": "97140", "short_description": "Manual Therapy Techniques", "category": "Physical Therapy"},
        {"hcpcs_code": "97530", "short_description": "Therapeutic Activities", "category": "Physical Therapy"},
        
        # Robotic Surgery (Modern)
        {"hcpcs_code": "S2900", "short_description": "Robotic Surgical Assistance (Add-on)", "category": "Robotic Surgery"},
        
        # Transplant
        {"hcpcs_code": "50360", "short_description": "Renal Transplant, Allotransplant", "category": "Transplant Surgery"},
        {"hcpcs_code": "47135", "short_description": "Liver Transplant, Allotransplant", "category": "Transplant Surgery"},
        {"hcpcs_code": "33945", "short_description": "Heart Transplant", "category": "Transplant Surgery"},
        
        # Dental (exclusion check)
        {"hcpcs_code": "D7140", "short_description": "Extraction, Erupted Tooth or Exposed Root", "category": "Dental"},
        {"hcpcs_code": "D7210", "short_description": "Extraction, Surgical, Erupted Tooth", "category": "Dental"},
        
        # Imaging/Diagnostics
        {"hcpcs_code": "70553", "short_description": "MRI Brain with and without Contrast", "category": "Diagnostic Imaging"},
        {"hcpcs_code": "71260", "short_description": "CT Chest with Contrast", "category": "Diagnostic Imaging"},
        {"hcpcs_code": "74177", "short_description": "CT Abdomen and Pelvis with Contrast", "category": "Diagnostic Imaging"},
        {"hcpcs_code": "78816", "short_description": "PET-CT Scan", "category": "Nuclear Medicine"},
        {"hcpcs_code": "76700", "short_description": "Ultrasound Abdomen Complete", "category": "Diagnostic Imaging"},
        {"hcpcs_code": "93306", "short_description": "Transthoracic Echocardiography Complete", "category": "Cardiac Imaging"},
    ]
    
    output_path = RUNTIME_DIR / "procedure_codes.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["hcpcs_code", "short_description", "category"])
        writer.writeheader()
        writer.writerows(codes)
    
    print(f"  [OK] procedure_codes.csv: {len(codes)} procedure codes -> {output_path}")
    return len(codes)


# ╔══════════════════════════════════════════════════════════════╗
# ║  5. NME EXCLUSIONS CSV                                      ║
# ╚══════════════════════════════════════════════════════════════╝
def build_nme_exclusions():
    """Build nme_exclusions.csv — Non-Medical Expense items per IRDAI Annexure IV."""
    print("\n[5/5] Building nme_exclusions.csv...")
    
    # IRDAI Master Circular on Standardization of Non-Medical Expenses (Annexure IV)
    items = [
        # Consumables / Disposables
        {"item_id": "NME-001", "item_name": "Admission Kit / Welcome Kit", "category": "Consumables", "typically_excluded": True},
        {"item_id": "NME-002", "item_name": "Gown / Pajama / Patient Dress", "category": "Consumables", "typically_excluded": True},
        {"item_id": "NME-003", "item_name": "Toiletries (Soap, Toothpaste, Toothbrush)", "category": "Consumables", "typically_excluded": True},
        {"item_id": "NME-004", "item_name": "Slippers / Footwear", "category": "Consumables", "typically_excluded": True},
        {"item_id": "NME-005", "item_name": "Tissue Paper / Paper Towels", "category": "Consumables", "typically_excluded": True},
        {"item_id": "NME-006", "item_name": "Sanitary Pads / Diapers (Adult)", "category": "Consumables", "typically_excluded": True},
        {"item_id": "NME-007", "item_name": "Face Mask (Non-Surgical)", "category": "Consumables", "typically_excluded": True},
        {"item_id": "NME-008", "item_name": "Hand Gloves (Non-Surgical)", "category": "Consumables", "typically_excluded": True},
        {"item_id": "NME-009", "item_name": "Cap / Shoe Cover (Non-OT)", "category": "Consumables", "typically_excluded": True},
        {"item_id": "NME-010", "item_name": "Cotton Balls / Cotton Roll", "category": "Consumables", "typically_excluded": False},
        {"item_id": "NME-011", "item_name": "Gauze / Bandage (Regular Dressing)", "category": "Consumables", "typically_excluded": False},
        {"item_id": "NME-012", "item_name": "Micropore Tape / Surgical Tape", "category": "Consumables", "typically_excluded": False},
        
        # Food & Beverages
        {"item_id": "NME-013", "item_name": "Extra Diet / Special Meal Charges", "category": "Food & Beverage", "typically_excluded": True},
        {"item_id": "NME-014", "item_name": "Mineral Water / Packaged Drinking Water", "category": "Food & Beverage", "typically_excluded": True},
        {"item_id": "NME-015", "item_name": "Guest Meal / Attendant Food Charges", "category": "Food & Beverage", "typically_excluded": True},
        {"item_id": "NME-016", "item_name": "Tea / Coffee / Juice (Non-Dietary)", "category": "Food & Beverage", "typically_excluded": True},
        {"item_id": "NME-017", "item_name": "Fruit Basket / Dry Fruits (Complimentary)", "category": "Food & Beverage", "typically_excluded": True},
        
        # Room / Housekeeping
        {"item_id": "NME-018", "item_name": "Extra Bed / Attendant Bed Charges", "category": "Room Amenities", "typically_excluded": True},
        {"item_id": "NME-019", "item_name": "Laundry / Linen Charges", "category": "Room Amenities", "typically_excluded": True},
        {"item_id": "NME-020", "item_name": "Room Freshener / Mosquito Repellent", "category": "Room Amenities", "typically_excluded": True},
        {"item_id": "NME-021", "item_name": "TV / Cable / Entertainment Charges", "category": "Room Amenities", "typically_excluded": True},
        {"item_id": "NME-022", "item_name": "Wi-Fi / Internet Charges", "category": "Room Amenities", "typically_excluded": True},
        {"item_id": "NME-023", "item_name": "Telephone / STD / ISD Charges", "category": "Room Amenities", "typically_excluded": True},
        {"item_id": "NME-024", "item_name": "Newspaper / Magazine Charges", "category": "Room Amenities", "typically_excluded": True},
        {"item_id": "NME-025", "item_name": "Room Heater / Air Cooler Charges", "category": "Room Amenities", "typically_excluded": True},
        
        # Administrative
        {"item_id": "NME-026", "item_name": "Registration / Admission Charges", "category": "Administrative", "typically_excluded": False},
        {"item_id": "NME-027", "item_name": "Service Charge (on Room)", "category": "Administrative", "typically_excluded": True},
        {"item_id": "NME-028", "item_name": "Surcharge on Billing", "category": "Administrative", "typically_excluded": True},
        {"item_id": "NME-029", "item_name": "Medical Records / Report Charges", "category": "Administrative", "typically_excluded": True},
        {"item_id": "NME-030", "item_name": "Medical Certificate / Fitness Certificate", "category": "Administrative", "typically_excluded": True},
        {"item_id": "NME-031", "item_name": "Documentation / Courier / Postal Charges", "category": "Administrative", "typically_excluded": True},
        {"item_id": "NME-032", "item_name": "Convenience Charges / Facility Fee", "category": "Administrative", "typically_excluded": True},
        {"item_id": "NME-033", "item_name": "Attendant / Visitor Pass Charges", "category": "Administrative", "typically_excluded": True},
        {"item_id": "NME-034", "item_name": "Credit Card / Processing Fee", "category": "Administrative", "typically_excluded": True},
        
        # Surgical Consumables (may or may not be excluded)
        {"item_id": "NME-035", "item_name": "Surgical Gloves (Sterile)", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-036", "item_name": "Surgical Drapes / Gowns (OT)", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-037", "item_name": "Suture Material / Staples", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-038", "item_name": "Catheter (Foley / IV / Central Line)", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-039", "item_name": "Syringe / Needle / Cannula", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-040", "item_name": "IV Infusion Set / Blood Transfusion Set", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-041", "item_name": "Urine Bag / Collection Container", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-042", "item_name": "Ryles Tube / NG Tube", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-043", "item_name": "Oxygen Mask / Nasal Prongs", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-044", "item_name": "Nebulizer Kit / Circuit", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-045", "item_name": "ECG Electrodes / Monitoring Patches", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-046", "item_name": "Pulse Oximeter Probe (Disposable)", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-047", "item_name": "Endotracheal Tube / LMA", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-048", "item_name": "Surgical Blade / Scalpel (Disposable)", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-049", "item_name": "Drain Tube / Chest Tube", "category": "Surgical Consumables", "typically_excluded": False},
        {"item_id": "NME-050", "item_name": "Sterile Water / Normal Saline (for Irrigation)", "category": "Surgical Consumables", "typically_excluded": False},
        
        # Implants & Prosthetics (covered but with sub-limits)
        {"item_id": "NME-051", "item_name": "Knee Implant (TKR)", "category": "Implants", "typically_excluded": False},
        {"item_id": "NME-052", "item_name": "Hip Implant (THR)", "category": "Implants", "typically_excluded": False},
        {"item_id": "NME-053", "item_name": "Coronary Stent (Drug Eluting)", "category": "Implants", "typically_excluded": False},
        {"item_id": "NME-054", "item_name": "Pacemaker / ICD", "category": "Implants", "typically_excluded": False},
        {"item_id": "NME-055", "item_name": "Intraocular Lens (IOL)", "category": "Implants", "typically_excluded": False},
        {"item_id": "NME-056", "item_name": "Spinal Instrumentation (Screws, Rods, Cage)", "category": "Implants", "typically_excluded": False},
        {"item_id": "NME-057", "item_name": "Orthopedic Plates / Screws / Nails", "category": "Implants", "typically_excluded": False},
        {"item_id": "NME-058", "item_name": "Hernia Mesh (Synthetic)", "category": "Implants", "typically_excluded": False},
        {"item_id": "NME-059", "item_name": "Cochlear Implant", "category": "Implants", "typically_excluded": False},
        
        # Pharmacy / Non-Prescription
        {"item_id": "NME-060", "item_name": "Vitamins / Nutritional Supplements (Non-Prescription)", "category": "Pharmacy", "typically_excluded": True},
        {"item_id": "NME-061", "item_name": "Creams / Ointments / Lotions (Cosmetic)", "category": "Pharmacy", "typically_excluded": True},
        {"item_id": "NME-062", "item_name": "Protein Powder / Nutritional Drink", "category": "Pharmacy", "typically_excluded": True},
        {"item_id": "NME-063", "item_name": "Hand Sanitizer / Disinfectant (Patient Use)", "category": "Pharmacy", "typically_excluded": True},
        {"item_id": "NME-064", "item_name": "Cold Pack / Hot Pack", "category": "Pharmacy", "typically_excluded": True},
        {"item_id": "NME-065", "item_name": "Elastic Bandage / Crepe Bandage", "category": "Pharmacy", "typically_excluded": False},
        
        # Physiotherapy Equipment (take-home)
        {"item_id": "NME-066", "item_name": "Walking Aid / Walker", "category": "Equipment", "typically_excluded": True},
        {"item_id": "NME-067", "item_name": "Wheelchair (Take-Home)", "category": "Equipment", "typically_excluded": True},
        {"item_id": "NME-068", "item_name": "Cervical Collar / Lumbar Belt", "category": "Equipment", "typically_excluded": True},
        {"item_id": "NME-069", "item_name": "Knee Brace / Ankle Support", "category": "Equipment", "typically_excluded": True},
        {"item_id": "NME-070", "item_name": "CPAP / BiPAP Machine (Take-Home)", "category": "Equipment", "typically_excluded": True},
        {"item_id": "NME-071", "item_name": "Glucometer / BP Monitor (Take-Home)", "category": "Equipment", "typically_excluded": True},
        
        # Miscellaneous
        {"item_id": "NME-072", "item_name": "Ambulance Charges (Non-Emergency)", "category": "Miscellaneous", "typically_excluded": True},
        {"item_id": "NME-073", "item_name": "Parking Charges", "category": "Miscellaneous", "typically_excluded": True},
        {"item_id": "NME-074", "item_name": "Baby Kit / Nursery Charges", "category": "Miscellaneous", "typically_excluded": True},
        {"item_id": "NME-075", "item_name": "Photography / CCTV charges", "category": "Miscellaneous", "typically_excluded": True},
        {"item_id": "NME-076", "item_name": "Housekeeping / Cleaning Charges", "category": "Miscellaneous", "typically_excluded": True},
        {"item_id": "NME-077", "item_name": "Bio-Hazard / Waste Disposal Fee", "category": "Miscellaneous", "typically_excluded": True},
        
        # Additional Items commonly found in Indian hospital bills
        {"item_id": "NME-078", "item_name": "Blood Grouping & Cross Match", "category": "Lab - Routine", "typically_excluded": False},
        {"item_id": "NME-079", "item_name": "ECG Recording", "category": "Diagnostics", "typically_excluded": False},
        {"item_id": "NME-080", "item_name": "Chest X-Ray", "category": "Diagnostics", "typically_excluded": False},
        {"item_id": "NME-081", "item_name": "Pre-Anesthesia Evaluation", "category": "Anesthesia", "typically_excluded": False},
        {"item_id": "NME-082", "item_name": "OT Charges / OT Equipment Usage", "category": "Operating Theatre", "typically_excluded": False},
        {"item_id": "NME-083", "item_name": "Anesthesiologist Fee", "category": "Anesthesia", "typically_excluded": False},
        {"item_id": "NME-084", "item_name": "Surgeon Fee", "category": "Professional Fees", "typically_excluded": False},
        {"item_id": "NME-085", "item_name": "Consultation Fee (Specialist)", "category": "Professional Fees", "typically_excluded": False},
        {"item_id": "NME-086", "item_name": "Nursing Charges", "category": "Nursing", "typically_excluded": False},
        {"item_id": "NME-087", "item_name": "ICU Charges (Per Day)", "category": "ICU", "typically_excluded": False},
        {"item_id": "NME-088", "item_name": "Ventilator Charges (Per Hour)", "category": "ICU", "typically_excluded": False},
        {"item_id": "NME-089", "item_name": "Blood / Blood Products Charges", "category": "Blood Bank", "typically_excluded": False},
        {"item_id": "NME-090", "item_name": "Central Sterile Supply Department (CSSD)", "category": "Sterilization", "typically_excluded": False},
        
        # Newer items per IRDAI 2024 guidelines
        {"item_id": "NME-091", "item_name": "PPE Kit (COVID / Infection Control)", "category": "Infection Control", "typically_excluded": True},
        {"item_id": "NME-092", "item_name": "Antigen / RT-PCR Test (Mandatory Pre-Admission)", "category": "Diagnostics", "typically_excluded": False},
        {"item_id": "NME-093", "item_name": "Isolation Room Surcharge", "category": "Room Amenities", "typically_excluded": True},
        {"item_id": "NME-094", "item_name": "Telehealth / Virtual Consultation Fee", "category": "Telemedicine", "typically_excluded": True},
        {"item_id": "NME-095", "item_name": "Second Opinion / Remote Specialist Consultation", "category": "Telemedicine", "typically_excluded": True},
        
        # Items frequently disputed
        {"item_id": "NME-096", "item_name": "Physiotherapy Session (In-Hospital)", "category": "Rehabilitation", "typically_excluded": False},
        {"item_id": "NME-097", "item_name": "Occupational Therapy Session", "category": "Rehabilitation", "typically_excluded": False},
        {"item_id": "NME-098", "item_name": "Speech Therapy Session", "category": "Rehabilitation", "typically_excluded": False},
        {"item_id": "NME-099", "item_name": "Dietician Consultation", "category": "Allied Health", "typically_excluded": True},
        {"item_id": "NME-100", "item_name": "Psychologist / Counselor Session", "category": "Allied Health", "typically_excluded": True},
        
        # Pharmacy charges commonly deducted
        {"item_id": "NME-101", "item_name": "Antiseptic Solution (Betadine / Chlorhexidine)", "category": "Pharmacy", "typically_excluded": False},
        {"item_id": "NME-102", "item_name": "Eye Drops / Ear Drops (Post-Surgical)", "category": "Pharmacy", "typically_excluded": False},
        {"item_id": "NME-103", "item_name": "Insulin Pen / Needle (Take-Home)", "category": "Pharmacy", "typically_excluded": True},
        {"item_id": "NME-104", "item_name": "Compression Stockings (DVT Prophylaxis)", "category": "Equipment", "typically_excluded": False},
        {"item_id": "NME-105", "item_name": "Abdominal Binder (Post-Surgery)", "category": "Equipment", "typically_excluded": False},
        
        # Charges specific to Indian hospitals
        {"item_id": "NME-106", "item_name": "AC Charges (Separate from Room)", "category": "Room Amenities", "typically_excluded": True},
        {"item_id": "NME-107", "item_name": "Generator / Power Backup Charges", "category": "Room Amenities", "typically_excluded": True},
        {"item_id": "NME-108", "item_name": "Water Purifier / RO Charges", "category": "Room Amenities", "typically_excluded": True},
        {"item_id": "NME-109", "item_name": "Lift / Elevator Usage Charges", "category": "Miscellaneous", "typically_excluded": True},
        {"item_id": "NME-110", "item_name": "Gas Pipeline Charges (Oxygen / Nitrous)", "category": "Miscellaneous", "typically_excluded": False},
        {"item_id": "NME-111", "item_name": "Fumigation Charges", "category": "Infection Control", "typically_excluded": True},
        {"item_id": "NME-112", "item_name": "Patient Identification Band / Wristband", "category": "Consumables", "typically_excluded": True},
        {"item_id": "NME-113", "item_name": "Emergency / After-Hours Surcharge", "category": "Administrative", "typically_excluded": True},
        {"item_id": "NME-114", "item_name": "Night Charges / Holiday Surcharge", "category": "Administrative", "typically_excluded": True},
        {"item_id": "NME-115", "item_name": "MLC / Police Verification Charges", "category": "Administrative", "typically_excluded": True},
        {"item_id": "NME-116", "item_name": "Death Certificate / Birth Certificate Charges", "category": "Administrative", "typically_excluded": True},
        {"item_id": "NME-117", "item_name": "Embalming Charges", "category": "Miscellaneous", "typically_excluded": True},
        {"item_id": "NME-118", "item_name": "Mortuary Charges", "category": "Miscellaneous", "typically_excluded": True},
        {"item_id": "NME-119", "item_name": "Hearse Van / Body Transfer Charges", "category": "Miscellaneous", "typically_excluded": True},
        {"item_id": "NME-120", "item_name": "Organ Retrieval / Preservation Charges", "category": "Transplant", "typically_excluded": False},
    ]
    
    output_path = RUNTIME_DIR / "nme_exclusions.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item_id", "item_name", "category", "typically_excluded"])
        writer.writeheader()
        writer.writerows(items)
    
    print(f"  [OK] nme_exclusions.csv: {len(items)} NME items -> {output_path}")
    return len(items)


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("  BUILDING ALL 5 RUNTIME KNOWLEDGE-BASE CSVs")
    print("=" * 70)
    
    counts = {}
    counts["policy_clauses"] = extract_policy_clauses()
    counts["denial_reasons"] = build_denial_reasons()
    counts["icd10_codes"] = build_icd10_codes()
    counts["procedure_codes"] = build_procedure_codes()
    counts["nme_exclusions"] = build_nme_exclusions()
    
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    for name, count in counts.items():
        print(f"  {name:25s} -> {count:5d} rows")
    print(f"\n  Total rows across all CSVs: {sum(counts.values())}")
    print(f"  Output directory: {RUNTIME_DIR}")
    print("=" * 70)
