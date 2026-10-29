"""Evaluate intake extraction on G1 (golden intake entities benchmark).

Per field: exact match, plus token F1 for text fields. For the cited clause the
top-1 and top-3 accuracy of the clause resolver are reported, because one
clause number can match many clauses of the same product.

    python -m evaluation.eval_intake
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from denial_ai.intake.extractor import extract_entities  # noqa: E402
from denial_ai.intake.loader import clean_text  # noqa: E402

GOLDEN = ROOT / "data" / "golden" / "G1_golden_intake_entities.json"
OUT = ROOT / "evaluation" / "results"
TEXT_FIELDS = {"patient_name", "hospital_name", "procedure", "insurer", "policy_product", "denial_category_hint"}


def token_f1(pred, gold):
    p, g = re.findall(r"\w+", str(pred or "").lower()), re.findall(r"\w+", str(gold).lower())
    common = sum((Counter(p) & Counter(g)).values())
    if not p or not g or not common:
        return float(p == g)
    precision, recall = common / len(p), common / len(g)
    return 2 * precision * recall / (precision + recall)


def main():
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))
    fields = [f for f in cases[0]["ground_truth_entities"] if f != "cited_clause_id"]
    exact = Counter()
    f1 = Counter()
    clause_top1 = clause_top3 = 0
    errors = []

    for c in cases:
        gold = c["ground_truth_entities"]
        pred = extract_entities(clean_text(c["raw_letter_text"]))
        for f in fields:
            value = getattr(pred, f)
            ok = value == gold[f]
            exact[f] += ok
            f1[f] += token_f1(value, gold[f]) if f in TEXT_FIELDS else float(ok)
            if not ok:
                errors.append({"case_id": c["case_id"], "field": f, "gold": gold[f], "pred": value})
        ids = [m.clause_id for m in pred.clause_candidates]
        clause_top1 += bool(ids) and ids[0] == gold["cited_clause_id"]
        clause_top3 += gold["cited_clause_id"] in ids
        if not ids or ids[0] != gold["cited_clause_id"]:
            errors.append({"case_id": c["case_id"], "field": "cited_clause_id", "gold": gold["cited_clause_id"],
                           "pred": ids[:3], "hint": gold["denial_category_hint"]})

    n = len(cases)
    report = {
        "benchmark": "G1",
        "cases": n,
        "fields": {f: {"exact_match": round(exact[f] / n, 4), "token_f1": round(f1[f] / n, 4)} for f in fields},
        "mean_exact_match": round(sum(exact.values()) / (n * len(fields)), 4),
        "clause_id_top1": round(clause_top1 / n, 4),
        "clause_id_top3": round(clause_top3 / n, 4),
        "errors": errors,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "g1_intake.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"G1 intake ({n} letters)")
    for f, r in report["fields"].items():
        print(f"  {f:22s} exact {r['exact_match']:.3f}  token-F1 {r['token_f1']:.3f}")
    print(f"  {'mean over fields':22s} exact {report['mean_exact_match']:.3f}")
    print(f"  {'cited_clause_id':22s} top-1 {report['clause_id_top1']:.3f}  top-3 {report['clause_id_top3']:.3f}")


if __name__ == "__main__":
    main()
