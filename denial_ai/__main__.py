"""Run intake and triage on one denial letter.

    python -m denial_ai letter.txt
    python -m denial_ai letter.pdf --json
    python -m denial_ai --text "The claim is repudiated as ..."
"""

import argparse
import sys

from .graph import Pipeline


def summary(case):
    e, t = case.entities, case.triage
    lines = ["INTAKE"]
    for field in ("claim_id", "patient_name", "insurer", "policy_product", "policy_number", "admission_date",
                  "denial_date", "hospital_name", "procedure", "icd10_code", "claimed_amount",
                  "cited_clause_raw", "cited_clause_id", "denial_category_hint", "appeal_window_days"):
        value = getattr(e, field)
        if value not in (None, ""):
            lines.append(f"  {field:22s} {value}")
    if e.icd10_code:
        lines.append(f"  {'icd10 check':22s} valid={e.icd10_valid} billable={e.icd10_billable}")
    if len(e.clause_candidates) > 1:
        others = ", ".join(f"{m.clause_id} ({m.score:.2f})" for m in e.clause_candidates[1:])
        lines.append(f"  {'other clause matches':22s} {others}")
    if e.missing_fields:
        lines.append(f"  {'not found':22s} {', '.join(e.missing_fields)}")

    lines += ["", "TRIAGE",
              f"  primary category       {t.primary_category} (confidence {t.confidence:.2f}, margin {t.margin:.2f})"]
    if t.secondary_categories:
        lines.append(f"  secondary              {', '.join(t.secondary_categories)}")
    if t.matched_reason:
        r = t.matched_reason
        lines.append(f"  standard reason        {t.matched_reason_id} {r['sub_category']} "
                     f"(CARC {r['carc_code']}, RARC {r['rarc_code']})")
        lines.append(f"  appeal route           {r['appeal_route']}")
    lines.append(f"  human review           {'YES: ' + '; '.join(t.review_reasons) if t.needs_human_review else 'no'}")
    for v in t.votes:
        status = "abstained" if v.abstained else max(v.scores, key=v.scores.get)
        lines.append(f"  agent {v.agent:16s} {status}  [{'; '.join(v.evidence[:3])}]")
    lines += ["", "DISPATCH"]
    for p in t.dispatch:
        lines.append(f"  {p.pipeline} ({p.category})")
        lines.append(f"    checks: {'; '.join(p.checks)}")
        lines.append(f"    documents: {', '.join(p.documents_needed)}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="denial_ai", description="Denial letter intake and triage")
    ap.add_argument("path", nargs="?", help="letter as .txt or .pdf")
    ap.add_argument("--text", help="letter text instead of a file")
    ap.add_argument("--json", action="store_true", help="print the full case record as JSON")
    ap.add_argument("--no-graph", action="store_true", help="run nodes sequentially without LangGraph")
    args = ap.parse_args(argv)
    if not (args.path or args.text):
        ap.error("give a file path or --text")

    case = Pipeline(use_langgraph=not args.no_graph).run(text=args.text, source=args.path)
    sys.stdout.reconfigure(encoding="utf-8")
    print(case.model_dump_json(indent=2) if args.json else summary(case))


if __name__ == "__main__":
    main()
