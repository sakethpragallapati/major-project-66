"""Letters in other insurers' layouts, and images and PDFs in the forms people upload them."""

import io
import json
from pathlib import Path

import pytest

from denial_ai.graph import Pipeline
from denial_ai.intake.extractor import extract_entities
from denial_ai.intake.loader import clean_text, load_bytes, repair_ocr_text
from denial_ai.intake.respace import respace, split_run

FIXTURES = Path(__file__).parent / "fixtures"
LAYOUTS = json.loads((FIXTURES / "layout_letters.json").read_text(encoding="utf-8"))
SCAN_TRUTH = json.loads((FIXTURES / "scanned_letter.json").read_text(encoding="utf-8"))["ground_truth_entities"]
SCAN_FIELDS = ["claim_id", "patient_name", "insurer", "policy_product", "admission_date", "denial_date",
               "hospital_name", "claimed_amount", "cited_clause_raw"]


def _wrong(entities, truth):
    return {k: (v, getattr(entities, k)) for k, v in truth.items() if getattr(entities, k) != v}


def _check_layout(name, case):
    want = LAYOUTS[name]
    assert not _wrong(case.entities, want["truth"])
    if "category" in want:
        assert case.triage.primary_category == want["category"]
        assert case.triage.matched_reason_id == want["reason_id"]


# ---------- the layouts, as OCR returns their text (no OCR needed) ----------

# The cashless letter as the OCR model reads it before repair: spaces lost, a lower-case
# "i" inside a word in capitals, the colon column dropped and a PIN code on its own line.
CASHLESS_OCR_TEXT = """STAR Health Insurance
Unable toAdmit Claim
Date : 18-May-24
Dear Sir/Madam,
Greetingsfrom STARHealth!
We are writing with regard to your claim request for the below-mentioned insured patient, for the treatmentofGASTROENTERiTIS:
Claim Intimation Number CIR/2024/240517/7712093
Name of theInsured MEERA KRISHNAN
Age/ Gender 41years2months/Female
Product Name YoungStar InsurancePolicy
Policy Number 10000099887766
Policy Period 15-Jan-24 to 14-Jan-25
Date of Admission 17-May-24
Nameof theHospitaland Location Sunrise Multispeciality Hospital, Nashik - NASHIK -
422005
After a comprehensive assessment by our medical team,we've observed that we're unable to admit the claim because of the below-mentioned reason(s):
Detailed Remarks:
1.The Company is not liable to make any payment under this policy in respect of any hospitalisationwhich is not medically necessary / does not warrant hospitalization.
Asyour trusted partner inhealthcare,we lookforward to our continued association for the greater benefit of patients across the country.
Regards, (Team STAR Health)"""

PROPOSAL_TEXT = """HDFC ERGO General Insurance Company Limited
Date: 12-02-2025
MR Arjun Mehta
Subject: Rejection of Proposal for my: Optima Secure Application No. HE00987654Q202502
Dear Arjun Mehta,
Your application has been reviewed by our underwriting experts and basis the available information and our underwriting norms, we are unable to offer coverage to the following member(s) due to reason(s) as specified:
Arjun Mehta | Uncontrolled diabetes
However, MR Arjun Mehta can reapply in alternate product Arogya Sanjeevani with sum insured INR 5,00,000.
We have initiated the process to refund the premium paid which you shall be receiving shortly."""


def test_cashless_layout_from_ocr_text():
    text = clean_text(repair_ocr_text(CASHLESS_OCR_TEXT))
    case = Pipeline(use_langgraph=False).run(text=text)
    _check_layout("cashless_denial_letter.png", case)
    e = case.entities
    # only the listed reason is used for triage, not the greeting or the closing courtesy line
    assert e.denial_reason_text.startswith("The Company is not liable")
    assert "trusted partner" not in e.denial_reason_text and "Greetings" not in e.denial_reason_text
    assert any("Young Star Insurance Policy" in i and "not in the knowledge base" in i for i in case.triage.intake_issues)
    assert "policy_product" not in e.missing_fields      # it was found, just not in the knowledge base


def test_proposal_rejection_is_not_triaged_as_a_claim():
    case = Pipeline(use_langgraph=False).run(text=PROPOSAL_TEXT)
    _check_layout("proposal_rejection_letter.png", case)
    t = case.triage
    assert t.matched_reason_id is None and t.dispatch == [] and t.secondary_categories == []
    assert t.needs_human_review and t.review_reasons == t.intake_issues
    assert t.intake_issues[0].startswith("not a claim denial")
    assert not case.entities.clause_candidates            # no clause lookup for an underwriting decision
    assert "reapply" not in case.entities.denial_reason_text


# ---------- the same layouts read from files ----------

@pytest.mark.parametrize("name", ["cashless_denial_letter.png", "proposal_rejection_letter.png"])
def test_layout_images(name):
    pytest.importorskip("rapidocr_onnxruntime")
    text, method = load_bytes((FIXTURES / name).read_bytes(), name)
    assert method == "image OCR"
    _check_layout(name, Pipeline(use_langgraph=False).run(text=text))


def test_text_layer_pdf_keeps_table_rows_together():
    name = "text_layer_table.pdf"
    text, method = load_bytes((FIXTURES / name).read_bytes(), name)
    assert method == "pdf text layer"
    # labels and values are separate text runs in the PDF; they must come out on one line
    assert "Patient Name Rohan Verma" in text and "Claim No: MA-2024-7781203 Date: 03/04/2024" in text
    case = Pipeline(use_langgraph=False).run(text=text)
    _check_layout(name, case)
    assert any("no Niva Bupa policy wordings" in i for i in case.triage.intake_issues)


# ---------- how the page arrives: turned, transparent, several pages ----------

def _scan_image():
    from PIL import Image
    return Image.open(FIXTURES / "scanned_letter.png")


def _png(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _scan_fields_ok(text):
    e = extract_entities(text)
    return {k: (SCAN_TRUTH[k], getattr(e, k)) for k in SCAN_FIELDS if getattr(e, k) != SCAN_TRUTH[k]}


@pytest.mark.parametrize("degrees", [3, 90, 180, 270])
def test_turned_scan_is_put_upright(degrees):
    pytest.importorskip("rapidocr_onnxruntime")
    from PIL import Image
    turned = _scan_image().convert("L").rotate(degrees, expand=True, fillcolor=255, resample=Image.BICUBIC)
    text, _ = load_bytes(_png(turned), "turned.png")
    assert not _scan_fields_ok(text)


def test_ocr_slips_are_repaired():
    text = clean_text(repair_ocr_text(
        "DearMs.Anjali Verma,\nWe refer to ClaimCLM-2025-00342under my:Optima Secure for Rs3.95.0o0 at "
        "Aster Medcity,Kochi, where you were admitted on19September2024."))
    e = extract_entities(text)
    assert e.patient_name == "Anjali Verma" and e.claim_id == "CLM-2025-00342"
    assert e.claimed_amount == 395000.0 and e.admission_date == "2024-09-19"
    assert "Aster Medcity, Kochi" in text
    # the rupee sign lost, and "Iyer" read as "lyer"
    e = extract_entities("Dear Mr. Ramesh lyer,\nThank you for your claim of 1,12,000 for treatment at X.")
    assert e.patient_name == "Ramesh Iyer" and e.claimed_amount == 112000.0
    from denial_ai.intake.normalizer import parse_amount
    assert parse_amount("98.450") == 98450 and parse_amount("12500.50") == 12500.5
    assert parse_amount("1,275,000") == 1275000


def test_transparent_png_and_phone_photo_rotation():
    pytest.importorskip("rapidocr_onnxruntime")
    from PIL import Image
    scan = _scan_image().convert("L")
    # black text on a transparent background: flattening alpha naively gives black on black
    rgba = Image.new("RGBA", scan.size, (0, 0, 0, 0))
    rgba.putalpha(scan.point(lambda v: 255 - v))
    assert not _scan_fields_ok(load_bytes(_png(rgba), "transparent.png")[0])
    # a phone photo stored sideways with an EXIF orientation tag
    exif = Image.Exif()
    exif[0x0112] = 6                                     # "rotate 90 degrees clockwise to view"
    buf = io.BytesIO()
    scan.rotate(90, expand=True).convert("RGB").save(buf, format="JPEG", quality=90, exif=exif)
    assert not _scan_fields_ok(load_bytes(buf.getvalue(), "photo.jpg")[0])


def test_multi_page_tiff_reads_every_page():
    pytest.importorskip("rapidocr_onnxruntime")
    from PIL import Image
    scan = _scan_image().convert("L")
    top, bottom = scan.crop((0, 0, scan.width, scan.height // 2)), scan.crop((0, scan.height // 2, scan.width,
                                                                              scan.height))
    buf = io.BytesIO()
    top.save(buf, format="TIFF", save_all=True, append_images=[bottom])
    text, _ = load_bytes(buf.getvalue(), "fax.tiff")
    assert "CLM-2024-2519" in text and "Room Rent" in text


# ---------- pieces ----------

def test_respacing_splits_merged_words_but_not_names():
    assert split_run("hospitalisationwhich") == ["hospitalisation", "which"]
    assert split_run("treatmentofFEVER") == ["treatment", "of", "FEVER"]          # not "off EVER"
    assert split_run("COMPASSITSOLUTIONS") == ["COMPASS", "IT", "SOLUTIONS"]
    for name in ["VASUNDHRASHAHI", "Medicity", "Rudrapur", "Andheri", "Fortis", "AdvantEdge"]:
        assert split_run(name) is None
    assert respace("mail care@hdfcergo.com or www.starhealth.in") == "mail care@hdfcergo.com or www.starhealth.in"


def test_label_variants():
    e = extract_entities(clean_text(
        "Claim No: CLM-2024-10001 Date: 04/05/2024\n"              # two pairs on one row
        "Claim lntimation Nurnber:\n"                              # misread label, value below
        "Patient Name: RAVI KUMAR (M/45)\n"
        "Hospital Name & Address: City Care Hospital, Pune - 411001\n"
        "Diagnosis: Acute appendicitis\n"
        "Dear Sir, your claim is repudiated."))
    assert e.claim_id == "CLM-2024-10001" and e.denial_date == "2024-05-04"
    assert e.patient_name == "RAVI KUMAR"
    assert e.hospital_name == "City Care Hospital, Pune"
    assert e.diagnosis == "Acute appendicitis"
    # a sentence that only contains a label word is not split into a label
    e = extract_entities(clean_text('HDFC ERGO\nYour claim under Optima Restore is rejected. As per the policy: "x".'))
    assert e.policy_product == "Optima Restore"


def test_insurers_outside_the_knowledge_base_are_named():
    for text, insurer in [("Bajaj Allianz General Insurance Company Ltd", "Bajaj Allianz"),
                          ("The New India Assurance Co. Ltd.", "New India Assurance"),
                          ("ACKO General Insurance", "Acko"), ("backorder of supplies", None)]:
        assert extract_entities(text).insurer == insurer
