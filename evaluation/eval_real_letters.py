"""Run intake and triage on the real letters in "data/Denial letters/".

Every .pdf, .png, .jpg, .jpeg, .tif, .tiff, .webp or .txt file in the folder is read
(with OCR when it has no text layer), extracted and triaged. Results go to
evaluation/results/real_letters.json and real_letters.csv, to check by eye against
the letters. The folder and the results are git-ignored, since real letters carry
claimants' personal data.

    python -m evaluation.eval_real_letters
"""

import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from denial_ai.graph import Pipeline  # noqa: E402
from denial_ai.intake.loader import load_bytes  # noqa: E402

LETTERS = ROOT / "data" / "Denial letters"
OUT = ROOT / "evaluation" / "results"
SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".txt"}
SHOWN = ["letter_type", "insurer", "tpa", "policy_product", "policy_product_raw", "policy_type", "claim_id",
         "application_number", "patient_name", "policy_number", "denial_date", "admission_date", "hospital_name",
         "diagnosis", "claimed_amount", "cited_clause_raw", "denial_category_hint"]


def main(folder=LETTERS):
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in SUFFIXES and p.name != "README.md")
    if not files:
        print(f"No letters in {folder}.")
        return
    pipe = Pipeline(use_langgraph=False)

    rows = []
    for path in files:
        started = time.perf_counter()
        try:
            text, method = load_bytes(path.read_bytes(), path.name)
            case = pipe.run(text=text)
        except Exception as exc:
            rows.append({"file": path.name, "error": str(exc)})
            print(f"  {path.name}: could not read ({exc})")
            continue
        e, t = case.entities, case.triage
        row = {"file": path.name, "read_method": method, "seconds": round(time.perf_counter() - started, 1),
               **{f: getattr(e, f) for f in SHOWN},
               "category": t.primary_category, "confidence": t.confidence, "matched_reason": t.matched_reason_id,
               "needs_review": t.needs_human_review, "review_reasons": "; ".join(t.review_reasons),
               "missing_fields": ", ".join(e.missing_fields)}

        rows.append(row)
        verdict = ("not a claim denial (proposal rejected)" if e.letter_type == "proposal_rejection"
                   else f"{t.primary_category} ({t.confidence:.2f})")
        print(f"  {path.name}: {verdict}{' REVIEW' if t.needs_human_review else ''}")

    OUT.mkdir(parents=True, exist_ok=True)
    summary = {"letters": len(files), "flagged_for_review": sum(bool(r.get("needs_review")) for r in rows)}
    (OUT / "real_letters.json").write_text(json.dumps({"summary": summary, "letters": rows}, indent=2,
                                                      ensure_ascii=False, default=str), encoding="utf-8")
    with (OUT / "real_letters.csv").open("w", newline="", encoding="utf-8") as f:
        cols = ["file", "read_method", "seconds", *SHOWN, "category", "confidence", "matched_reason",
                "needs_review", "review_reasons", "missing_fields", "error"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"\n{summary}")
    print(f"Results in {OUT / 'real_letters.json'} and real_letters.csv")


if __name__ == "__main__":
    main()
