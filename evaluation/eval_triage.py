"""Evaluate the triage router on G7 (golden denial router benchmark).

Reports accuracy, macro-F1, per-class scores and the confusion matrix for the
full ensemble and for each agent on its own (ablation).

    python -m evaluation.eval_triage
"""

import json
import sys
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from denial_ai.config import CATEGORIES  # noqa: E402
from denial_ai.graph import Pipeline  # noqa: E402
from denial_ai.triage.agents import ClauseTypeAgent, CueAgent, LLMAgent, ReasonMatchAgent  # noqa: E402

GOLDEN = ROOT / "data" / "golden" / "G7_golden_denial_router.json"
HELDOUT = ROOT / "evaluation" / "heldout_denials.json"
OUT = ROOT / "evaluation" / "results"


def run(agents, cases):
    pipe = Pipeline(agents=agents, use_langgraph=False)
    preds, review = [], 0
    for c in cases:
        t = pipe.run(text=c["raw_denial_paragraph"]).triage
        preds.append(t.primary_category)
        # Count only the router's own flags: G7 paragraphs are not whole letters, so
        # intake flags (no patient, no admission date) say nothing about triage.
        review += len(t.review_reasons) > len(t.intake_issues)
    return preds, review


def main():
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))
    gold = [c["ground_truth_category"] for c in cases]
    configs = {
        "ensemble": [CueAgent(), ReasonMatchAgent(), ClauseTypeAgent(), LLMAgent()],
        "cue_only": [CueAgent()],
        "reason_only": [ReasonMatchAgent()],
    }
    report = {"benchmark": "G7", "cases": len(cases), "configs": {}}
    for name, agents in configs.items():
        preds, review = run(agents, cases)
        report["configs"][name] = {
            "accuracy": round(accuracy_score(gold, preds), 4),
            "macro_f1": round(f1_score(gold, preds, labels=CATEGORIES, average="macro", zero_division=0), 4),
            "flagged_for_review": review,
        }
        if name == "ensemble":
            report["per_class"] = classification_report(gold, preds, labels=CATEGORIES, output_dict=True,
                                                        zero_division=0)
            report["confusion_matrix"] = {"labels": CATEGORIES,
                                          "matrix": confusion_matrix(gold, preds, labels=CATEGORIES).tolist()}
            report["errors"] = [
                {"case_id": c["case_id"], "gold": g, "pred": p, "text": c["raw_denial_paragraph"]}
                for c, g, p in zip(cases, gold, preds) if g != p]

    # Held-out set: hand-written denials in wording the G7 templates do not use.
    # It was written before the router was run on it and is not used for tuning.
    held = json.loads(HELDOUT.read_text(encoding="utf-8"))
    held_gold = [h["category"] for h in held]
    held_preds, held_review = run(configs["ensemble"], [{"raw_denial_paragraph": h["text"]} for h in held])
    report["heldout"] = {
        "cases": len(held),
        "accuracy": round(accuracy_score(held_gold, held_preds), 4),
        "macro_f1": round(f1_score(held_gold, held_preds, labels=CATEGORIES, average="macro", zero_division=0), 4),
        "flagged_for_review": held_review,
        "errors": [{"id": h["id"], "gold": g, "pred": p, "text": h["text"]}
                   for h, g, p in zip(held, held_gold, held_preds) if g != p],
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "g7_triage.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"G7 triage ({len(cases)} cases)")
    for name, r in report["configs"].items():
        print(f"  {name:12s} accuracy {r['accuracy']:.3f}  macro-F1 {r['macro_f1']:.3f}  "
              f"flagged {r['flagged_for_review']}")
    print("\nConfusion matrix (rows = gold):")
    short = [c[:6] for c in CATEGORIES]
    print("        " + " ".join(f"{s:>6s}" for s in short))
    for s, row in zip(short, report["confusion_matrix"]["matrix"]):
        print(f"{s:>7s} " + " ".join(f"{v:6d}" for v in row))
    h = report["heldout"]
    print(f"\nHeld-out set ({h['cases']} cases): accuracy {h['accuracy']:.3f}  macro-F1 {h['macro_f1']:.3f}  "
          f"flagged {h['flagged_for_review']}")
    print(f"\n{len(report['errors'])} G7 errors and {len(h['errors'])} held-out errors written to "
          f"{OUT / 'g7_triage.json'}")


if __name__ == "__main__":
    main()
