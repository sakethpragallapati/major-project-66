"""Unit tests for intake and triage, on letters written in formats G1 does not use."""

import pytest

from denial_ai.graph import Pipeline
from denial_ai.intake.extractor import extract_entities
from denial_ai.intake.loader import clean_text
from denial_ai.intake.normalizer import match_product, parse_amount, parse_date
from denial_ai.triage.agents import CueAgent, ReasonMatchAgent
from denial_ai.triage.supervisor import decide
from denial_ai.schemas import AgentVote

LETTER_DMY = """STAR HEALTH AND ALLIED INSURANCE CO. LTD.
Dated: 05/03/2024

Claim No: CLM-2024-55120
Patient Name: Smt. Lakshmi Narayan
Policy No.: P/181211/01/2024/004512
Plan: Family Health Optima
Date of Admission: 14/02/2024
Hospital Name: Apollo Hospitals, Chennai
Diagnosis Code: E11.9
Claimed Amount: Rs. 1,85,000/-

Dear Madam,
Your claim has been repudiated under Clause 3.2 (Pre-Existing Disease Waiting Period) as the
records show diabetes since 2019. You may approach the Grievance Redressal Officer within 15 days.
"""

LETTER_NARRATIVE = """HDFC ERGO General Insurance
12th March 2025

Dear Mr. Vikram Singh,
With reference to your hospitalisation on 2 March 2025 at Fortis Hospital, Mohali for Total Knee
Replacement (ICD-10: M17.11), your claim for INR 4,50,000 under Optima Restore has been disallowed under
Code-Excl03 (Initial waiting period)."""


def test_dates_and_amounts():
    assert parse_date("05/03/2024") == "2024-03-05"          # day first
    assert parse_date("12th March 2025") == "2025-03-12"
    assert parse_date("March 2, 2025") == "2025-03-02"
    assert parse_date("31/02/2024") is None
    assert parse_amount("1,85,000") == 185000.0               # lakh grouping
    assert parse_amount("4,50,000.50") == 450000.5


def test_product_inside_insurer_name_is_skipped():
    text = "Care Health\nYour claim under Care Supreme has been repudiated."
    assert match_product(text, "Care Health") == "Care Supreme"


def test_labelled_letter_with_indian_formats():
    e = extract_entities(clean_text(LETTER_DMY))
    assert e.claim_id == "CLM-2024-55120"
    assert e.patient_name == "Lakshmi Narayan"
    assert e.insurer == "Star Health"
    assert e.policy_product == "Family Health Optima"
    assert e.denial_date == "2024-03-05"
    assert e.admission_date == "2024-02-14"
    assert e.claimed_amount == 185000.0
    assert e.icd10_code == "E11.9" and e.icd10_valid
    assert e.cited_clause_raw == "Clause 3.2"
    assert e.denial_category_hint == "Pre-Existing Disease Waiting Period"
    assert e.appeal_window_days == 15


def test_narrative_letter_with_code_excl_clause():
    e = extract_entities(clean_text(LETTER_NARRATIVE))
    assert e.insurer == "HDFC ERGO"
    assert e.policy_product == "Optima Restore"
    assert e.patient_name == "Vikram Singh"
    assert e.denial_date == "2025-03-12"
    assert e.admission_date == "2025-03-02"
    assert e.hospital_name == "Fortis Hospital, Mohali"
    assert e.procedure == "Total Knee Replacement"
    assert e.claimed_amount == 450000.0
    assert e.cited_clause_raw.lower().startswith("code-excl")


def test_missing_fields_are_reported_not_guessed():
    e = extract_entities("The claim is closed as the documents were not submitted.")
    assert e.claim_id is None and e.claimed_amount is None
    assert "claim_id" in e.missing_fields


@pytest.mark.parametrize("text,expected", [
    ("The pre-existing disease waiting period of 36 months has not been completed.", "PRE_EXISTING_WAITING_PERIOD"),
    ("Room rent exceeded the eligible limit, so a proportionate deduction was applied.", "FINANCIAL_LIMIT"),
    ("The discharge summary has not been submitted despite reminders.", "DOCUMENTATION"),
    ("The claim was intimated 20 days after discharge, beyond the stipulated time.", "ADMINISTRATIVE_PROCEDURAL"),
    ("The policy had lapsed and was not in force on the date of admission.", "ELIGIBILITY_COVERAGE"),
    ("Cosmetic surgery is a permanent exclusion under the policy.", "POLICY_EXCLUSION"),
    ("The admission was not medically necessary; the condition could be treated on an outpatient basis.",
     "MEDICAL_NECESSITY"),
])
def test_triage_categories(text, expected):
    case = Pipeline(use_langgraph=False).run(text=text)
    assert case.triage.primary_category == expected
    assert case.triage.dispatch[0].category == expected


def test_reason_agent_returns_standard_reason():
    case = Pipeline(agents=[ReasonMatchAgent()], use_langgraph=False).run(
        text="Co-payment of 20% has been deducted from the admissible amount.")
    assert case.triage.primary_category == "FINANCIAL_LIMIT"
    assert case.triage.matched_reason_id == "FIN-004"
    assert case.triage.matched_reason["carc_code"] == "3"


def test_disagreement_flags_review():
    votes = [AgentVote(agent="cue", scores={"DOCUMENTATION": 1.0}),
             AgentVote(agent="reason", scores={"ADMINISTRATIVE_PROCEDURAL": 1.0})]
    t = decide(votes)
    assert t.needs_human_review and not t.agents_agree


def test_all_abstain_flags_review():
    t = decide([AgentVote(agent="cue", abstained=True)])
    assert t.needs_human_review


def test_langgraph_and_sequential_agree():
    pytest.importorskip("langgraph")
    a = Pipeline(use_langgraph=True).run(text=LETTER_DMY)
    b = Pipeline(use_langgraph=False).run(text=LETTER_DMY)
    assert a.entities == b.entities
    assert a.triage.primary_category == b.triage.primary_category == "PRE_EXISTING_WAITING_PERIOD"
    assert [v.agent for v in a.triage.votes] == [v.agent for v in b.triage.votes]


def test_cue_agent_abstains_without_cues():
    case = Pipeline(agents=[CueAgent()], use_langgraph=False).run(text="Thank you for your letter.")
    assert case.triage.votes[0].abstained
