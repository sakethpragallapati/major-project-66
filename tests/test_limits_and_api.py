"""Tests for OCR intake, clause resolution status and the web API."""

import json
from pathlib import Path

import pytest

from denial_ai.intake.extractor import extract_entities
from denial_ai.intake.loader import clean_text, load_letter
from denial_ai.graph import Pipeline

FIXTURES = Path(__file__).parent / "fixtures"
SCAN_TRUTH = json.loads((FIXTURES / "scanned_letter.json").read_text(encoding="utf-8"))["ground_truth_entities"]


@pytest.mark.parametrize("name", ["scanned_letter.png", "scanned_letter.pdf"])
def test_scanned_letter_is_read_by_ocr(name):
    pytest.importorskip("rapidocr_onnxruntime")
    e = extract_entities(load_letter(FIXTURES / name))
    wrong = {k: (v, getattr(e, k)) for k, v in SCAN_TRUTH.items() if getattr(e, k) != v}
    assert not wrong


GROUP = json.loads((FIXTURES / "group_policy_letter.json").read_text(encoding="utf-8"))

# The same letter as OCR returns it, with the glitches seen on the real one: labels
# without colons, words run together, "to" glued to the dates.
GROUP_OCR_TEXT = """ICIcILombard ICICI Lombard
GENERALINSURANCE
Ref :417
Date:14-MAR-2024
To
Dear Sir/IMadlam,
Claim Number 230315448812
Claimof KAVITHA RAMAN
UHID IL30551234567
Policy Number 4016/245678901/02/000
Policy Name BLUEWAVEDIGITAL
SERVICESPVTLTD
Coverage Period 01-APR-23to31-MAR-24
Date ofAdmission 26-FEB-24
On behalf of ICICI Lombard General Insurance Co. Ltd,we thank you for preferring ICICI Lombard as your health insurance partner.
We have perused the documents submitted by you andregret to inform you that your claim cannot be settled for thefollowing reasons.
Sr No Reason Description
Sum Insured Exhausted 1.As thebalance sum insured availableunder this policyis exhausted,hence the claim stands rejected.
Incaseyouhave any query,kindlycontactuswithinaperiodof 8weeks.
For ICICI Lombard General Insurance Company Ltd"""


def _check_group_letter(case):
    e = case.entities
    wrong = {k: (v, getattr(e, k)) for k, v in GROUP["truth"].items() if getattr(e, k) != v}
    assert not wrong
    assert e.policy_holder.replace(" ", "") == "BLUEWAVEDIGITALSERVICESPVTLTD"
    assert e.policy_holder.endswith("SERVICES PVT LTD")
    t = case.triage
    assert t.primary_category == GROUP["category"] and t.matched_reason_id == GROUP["reason_id"]
    assert "Ombudsman" in t.matched_reason["appeal_route"]
    assert t.dispatch[0].focus == "FIN-001"
    assert any("restore" in c for c in t.dispatch[0].checks)
    assert any(i.startswith("group policy") for i in t.intake_issues) and t.needs_human_review
    # courtesy lines are not part of the text used for triage
    assert "thank" not in e.denial_reason_text.lower() and "query" not in e.denial_reason_text.lower()


def test_group_policy_letter_as_ocr_text():
    _check_group_letter(Pipeline(use_langgraph=False).run(text=GROUP_OCR_TEXT))


def test_group_policy_letter_image():
    pytest.importorskip("rapidocr_onnxruntime")
    _check_group_letter(Pipeline(use_langgraph=False).run(text=load_letter(FIXTURES / "group_policy_letter.png")))


def test_letter_reference_is_not_the_claim_number():
    e = extract_entities(clean_text("Ref : 82\nDate : 02-FEB-2023\nClaim Number 220202875738\nDear Sir/Madam,"))
    assert e.claim_id == "220202875738" and e.letter_ref == "82"
    assert e.denial_date == "2023-02-02"
    assert e.patient_name is None


def test_wrapped_lines_are_rejoined():
    text = clean_text("Your claim has been denied under Clause 1(i), which\npertains to Room Rent Limit.\nAt BLK-\nMAX")
    assert "which pertains to Room Rent Limit" in text and "BLK-MAX" in text


def test_quoted_clause_is_pinned_without_a_number():
    letter = ('HDFC ERGO\nYour claim under Optima Restore is rejected. As per the policy: "Expenses related to the '
              'treatment of a pre-existing disease (PED) and its direct complications shall be excluded until the '
              'expiry of 36 months of continuous coverage".')
    e = extract_entities(clean_text(letter))
    assert e.clause_resolution == "quoted"
    assert e.cited_clause_id == "OPTIMA-EXC-0767"


def test_unknown_clause_number_is_flagged_for_review():
    letter = ("HDFC ERGO\nDear Mr. Ravi Kumar,\nYour claim CLM-2025-1111 under Optima Restore is repudiated "
              "under Clause 97.4 (Room Rent Limit).")
    case = Pipeline(use_langgraph=False).run(text=letter)
    assert case.entities.clause_resolution == "number_not_found"
    assert case.entities.cited_clause_id is None
    assert case.entities.clause_candidates            # suggestions are still offered
    assert any("cited clause unclear" in r for r in case.triage.review_reasons)


def test_api_analyse_list_and_delete(monkeypatch):
    from fastapi.testclient import TestClient

    from denial_ai import api

    monkeypatch.setattr(api, "CASES", {})
    client = TestClient(api.app)
    assert client.get("/").status_code == 200
    assert client.get("/api/meta").json()["categories"]

    r = client.post("/api/analyze", data={"text": "The discharge summary has not been submitted despite reminders."})
    assert r.status_code == 200
    first = r.json()
    assert first["triage"]["primary_category"] == "DOCUMENTATION"
    client.post("/api/analyze", data={"text": "Room rent exceeded the eligible limit."})
    client.post("/api/analyze", data={"text": "The policy had lapsed on the date of admission."})
    assert len(client.get("/api/cases").json()) == 3

    assert client.delete(f"/api/cases/{first['id']}").json() == {"deleted": first["id"]}
    assert client.get(f"/api/cases/{first['id']}").status_code == 404
    assert client.delete(f"/api/cases/{first['id']}").status_code == 404
    assert len(client.get("/api/cases").json()) == 2

    assert client.delete("/api/cases").json() == {"deleted": 2}
    assert client.get("/api/cases").json() == []
    assert client.post("/api/analyze", data={"text": "  "}).status_code == 400
