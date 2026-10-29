"""Robustness of intake beyond the G1 templates.

Part 1 rewrites every G1 letter in ways real letters differ, one change at a
time, and checks that the extracted fields stay the same:
  dates in dd/mm/yyyy or "13 August 2024", amounts in lakh grouping with ₹ or INR,
  lines wrapped as in a PDF, upper-case headers, and spaces lost by OCR.
Part 2 runs hand-written letters in other layouts (evaluation/heldout_letters.json),
which were written before the pipeline was run on them and are not used for tuning.

    python -m evaluation.eval_robustness
"""

import json
import random
import re
import sys
import textwrap
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from denial_ai.graph import Pipeline  # noqa: E402
from denial_ai.intake.extractor import extract_entities  # noqa: E402
from denial_ai.intake.loader import clean_text  # noqa: E402

G1 = ROOT / "data" / "golden" / "G1_golden_intake_entities.json"
HELDOUT = ROOT / "evaluation" / "heldout_letters.json"
OUT = ROOT / "evaluation" / "results"
FIELDS = ["claim_id", "patient_name", "insurer", "policy_product", "admission_date", "denial_date",
          "hospital_name", "procedure", "icd10_code", "claimed_amount", "cited_clause_raw"]
ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
AMOUNT = re.compile(r"Rs\.? ?([\d,]+)(/-)?")


def lakh(n):
    """265000 -> '2,65,000'."""
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
    return f"{head},{tail}"


def dmy(m):
    return f"{m[3]}/{m[2]}/{m[1]}"


def long_date(m):
    d = date(int(m[1]), int(m[2]), int(m[3]))
    return f"{d.day} {d.strftime('%B')} {d.year}"


PERTURBATIONS = {
    "dates_dd/mm/yyyy": lambda t: ISO.sub(dmy, t),
    "dates_long_form": lambda t: ISO.sub(long_date, t),
    "amount_lakh_rupee_sign": lambda t: AMOUNT.sub(lambda m: "₹" + lakh(m[1].replace(",", "")) + "/-", t),
    "amount_INR": lambda t: AMOUNT.sub(lambda m: "INR " + lakh(m[1].replace(",", "")), t),
    "pdf_line_wrap": lambda t: "\n".join(
        "\n".join(textwrap.wrap(line, 58)) if len(line) > 58 else line for line in t.split("\n")),
    "uppercase_header": lambda t: "\n".join(
        [t.split("\n")[0].upper()] + t.split("\n")[1:]),
    "ocr_lost_spaces_in_names": lambda t: re.sub(r"\b(HDFC|ICICI|Star|Care) (ERGO|Lombard|Health)\b", r"\1\2", t),
}


def field_errors(pred, gold):
    return [f for f in FIELDS if f in gold and getattr(pred, f) != gold[f]]


def main():
    g1 = json.loads(G1.read_text(encoding="utf-8"))
    report = {"perturbations": {}, "heldout_letters": {}}

    print(f"Part 1: G1 letters rewritten ({len(g1)} letters per variant)")
    for name, fn in PERTURBATIONS.items():
        exact = total = clause_ok = 0
        failures = {}
        for c in g1:
            gold = c["ground_truth_entities"]
            pred = extract_entities(clean_text(fn(c["raw_letter_text"])))
            errs = field_errors(pred, gold)
            exact += not errs
            total += 1
            clause_ok += pred.cited_clause_id == gold["cited_clause_id"]
            for f in errs:
                failures[f] = failures.get(f, 0) + 1
        report["perturbations"][name] = {"letters_all_fields_correct": round(exact / total, 4),
                                         "clause_id_top1": round(clause_ok / total, 4),
                                         "field_failures": failures}
        print(f"  {name:26s} all fields correct {exact / total:.3f}  clause top-1 {clause_ok / total:.3f}"
              + (f"  failures {failures}" if failures else ""))

    held = json.loads(HELDOUT.read_text(encoding="utf-8"))
    pipe = Pipeline(use_langgraph=False)
    correct = checked = cat_ok = 0
    details = []
    print(f"\nPart 2: hand-written letters in other layouts ({len(held)} letters)")
    for h in held:
        case = pipe.run(text=h["text"])
        truth = {k: v for k, v in h["truth"].items() if k != "category"}
        errs = {f: {"gold": v, "pred": getattr(case.entities, f)} for f, v in truth.items()
                if getattr(case.entities, f) != v}
        checked += len(truth)
        correct += len(truth) - len(errs)
        cat_ok += case.triage.primary_category == h["truth"]["category"]
        details.append({"id": h["id"], "field_errors": errs, "category_gold": h["truth"]["category"],
                        "category_pred": case.triage.primary_category,
                        "needs_review": case.triage.needs_human_review})
        print(f"  {h['id']}: {len(truth) - len(errs)}/{len(truth)} fields, category "
              f"{'ok' if details[-1]['category_pred'] == h['truth']['category'] else 'WRONG ' + details[-1]['category_pred']}"
              + (f"  errors {list(errs)}" if errs else ""))
    report["heldout_letters"] = {"field_accuracy": round(correct / checked, 4),
                                 "category_accuracy": round(cat_ok / len(held), 4), "letters": details}
    print(f"  field accuracy {correct / checked:.3f}, category accuracy {cat_ok / len(held):.3f}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "robustness.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    random.seed(0)
    main()
