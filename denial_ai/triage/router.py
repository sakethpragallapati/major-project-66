"""Map each denial category to the Objective 03 investigation it triggers."""

from ..schemas import InvestigationPlan

PIPELINES = {
    "MEDICAL_NECESSITY": InvestigationPlan(
        category="MEDICAL_NECESSITY",
        pipeline="medical_necessity_investigation",
        checks=["clinical severity and vital signs at admission",
                "conservative treatment tried and its duration",
                "procedure-diagnosis consistency",
                "need for inpatient care versus day care"],
        runtime_tables=["procedure_diagnosis_map.csv", "procedure_codes.csv", "icd10_codes.csv", "policy_clauses.csv"],
        documents_needed=["discharge summary", "investigation reports", "treating doctor's certificate"],
    ),
    "PRE_EXISTING_WAITING_PERIOD": InvestigationPlan(
        category="PRE_EXISTING_WAITING_PERIOD",
        pipeline="chronology_ped_investigation",
        checks=["policy inception and continuous-renewal dates",
                "date of first diagnosis or symptoms",
                "waiting period applicable to the condition",
                "60-month moratorium",
                "portability credit"],
        runtime_tables=["policy_clauses.csv", "icd10_codes.csv"],
        documents_needed=["policy schedules for every renewal", "proposal form", "earliest consultation records"],
    ),
    "POLICY_EXCLUSION": InvestigationPlan(
        category="POLICY_EXCLUSION",
        pipeline="exclusion_applicability_investigation",
        checks=["verbatim exclusion text and its exceptions",
                "whether the diagnosis falls inside the exclusion",
                "accident or medical-necessity exceptions"],
        runtime_tables=["policy_clauses.csv", "icd10_codes.csv", "procedure_codes.csv"],
        documents_needed=["policy wording", "discharge summary", "accident or FIR records where relevant"],
    ),
    "FINANCIAL_LIMIT": InvestigationPlan(
        category="FINANCIAL_LIMIT",
        pipeline="financial_limit_audit",
        checks=["sum insured and bonus balance",
                "room-rent proportion and its exemptions",
                "co-payment and deductible arithmetic",
                "non-medical items against the IRDAI list"],
        runtime_tables=["nme_exclusions.csv", "policy_clauses.csv"],
        documents_needed=["itemised final bill", "policy schedule", "settlement letter with deductions"],
    ),
    "DOCUMENTATION": InvestigationPlan(
        category="DOCUMENTATION",
        pipeline="documentation_gap_check",
        checks=["documents requested versus documents submitted",
                "date and name consistency across records",
                "whether the gap can be cured by resubmission"],
        runtime_tables=["denial_reasons.csv"],
        documents_needed=["submission acknowledgement", "the documents named in the letter"],
    ),
    "ADMINISTRATIVE_PROCEDURAL": InvestigationPlan(
        category="ADMINISTRATIVE_PROCEDURAL",
        pipeline="procedural_compliance_check",
        checks=["intimation and submission timelines against the policy",
                "reasonable-cause condonation for delay",
                "network, TPA and pre-authorisation records",
                "duplicate or other-policy claims"],
        runtime_tables=["policy_clauses.csv", "denial_reasons.csv"],
        documents_needed=["intimation proof (email or call reference)", "TPA correspondence"],
    ),
    "ELIGIBILITY_COVERAGE": InvestigationPlan(
        category="ELIGIBILITY_COVERAGE",
        pipeline="eligibility_verification",
        checks=["insured member list and endorsements",
                "policy status on the date of treatment, including the grace period",
                "age and territory conditions",
                "grounds and evidence for any fraud or cancellation finding"],
        runtime_tables=["policy_clauses.csv"],
        documents_needed=["policy schedule and endorsements", "premium payment receipts"],
    ),
}


# Checks for specific standard reasons. When the matched reason has an entry here, its
# checks and documents replace the category's general ones for the primary category,
# since a "sum insured exhausted" denial has nothing to do with room rent or co-payment.
REASON_FOCUS = {
    "FIN-001": (["sum insured for the policy year, plus cumulative bonus",
                 "restore, recharge or reinstatement benefit and whether it applies to this illness",
                 "earlier claims paid in the same policy year and their amounts",
                 "whether the admission date falls in a new policy year after renewal",
                 "any top-up or super top-up cover that should pay next"],
                ["policy schedule showing sum insured and bonus", "claim history statement for the policy year",
                 "renewal schedule if the admission is near the renewal date"]),
    "FIN-002": (["eligible room category or rent limit in the policy schedule",
                 "room actually occupied and its daily rate",
                 "proportionate deduction applied only to associated charges, not to medicines or implants",
                 "ICU charges handled under their own limit"],
                ["itemised bill with room charges", "policy schedule"]),
    "FIN-004": (["co-payment percentage and the condition that triggers it (age, zone, network)",
                 "co-payment applied to the admissible amount, not the billed amount"],
                ["policy schedule", "settlement letter with the deduction"]),
    "FIN-005": (["deductible amount and whether it is per claim or per year",
                 "earlier claims in the year that already used up the deductible"],
                ["policy schedule", "claim history statement"]),
    "FIN-008": (["each deducted item against the IRDAI list of non-payable items",
                 "items that are payable when part of a procedure package"],
                ["itemised bill", "settlement letter with deductions"]),
    "PW-001": (["date of first diagnosis or symptoms against the policy start date",
                "PED waiting period in the wording (at most 36 months under the 2024 Master Circular)",
                "continuous coverage including earlier policies and portability",
                "60-month moratorium"],
               ["earliest consultation records", "all policy schedules since first inception", "proposal form"]),
    "PW-004": (["admission date against the first policy start date (30-day window)",
                "whether the illness was caused by an accident, which is exempt",
                "renewal or portability, which removes the 30-day wait"],
               ["policy schedule with first inception date", "previous policy if ported"]),
    "ELG-001": (["policy status on the admission date",
                 "premium payment date against the 30-day grace period",
                 "whether coverage continued during the grace period under the wording"],
                ["premium receipts", "renewal notice and schedule"]),
    "ADM-001": (["intimation and submission dates against the policy time limits",
                 "reason for the delay and whether the insurer must condone it (IRDAI: genuine delay is not a ground to reject)"],
                ["proof of intimation", "explanation for the delay with supporting records"]),
}


def dispatch_plan(categories, reason_id=None):
    plans = [PIPELINES[c] for c in categories]
    if reason_id in REASON_FOCUS and plans and reason_id.split("-")[0] == _PREFIX[plans[0].category]:
        checks, documents = REASON_FOCUS[reason_id]
        plans[0] = plans[0].model_copy(update={"checks": checks, "documents_needed": documents,
                                               "focus": reason_id})
    return plans


_PREFIX = {"MEDICAL_NECESSITY": "MN", "PRE_EXISTING_WAITING_PERIOD": "PW", "POLICY_EXCLUSION": "PE",
           "FINANCIAL_LIMIT": "FIN", "DOCUMENTATION": "DOC", "ADMINISTRATIVE_PROCEDURAL": "ADM",
           "ELIGIBILITY_COVERAGE": "ELG"}
