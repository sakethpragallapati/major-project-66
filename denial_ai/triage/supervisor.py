"""Combine the agents' votes into one triage decision."""

from .. import config
from ..knowledge import get_kb
from ..schemas import TriageDecision
from .router import dispatch_plan

CATS = config.CATEGORIES


def decide(votes, weights=None, entities=None):
    weights = weights or config.AGENT_WEIGHTS
    active = [v for v in votes if not v.abstained and v.scores]
    review = []

    if not active:
        dist = {c: round(1 / len(CATS), 4) for c in CATS}
        review.append("every agent abstained")
    else:
        total_w = sum(weights.get(v.agent, 0.0) for v in active) or 1.0
        dist = {c: round(sum(weights.get(v.agent, 0.0) * v.scores.get(c, 0.0) for v in active) / total_w, 4)
                for c in CATS}

    ranked = sorted(CATS, key=lambda c: -dist[c])
    primary, confidence = ranked[0], dist[ranked[0]]
    margin = round(confidence - dist[ranked[1]], 4)

    # The two strongest agents (by weight) should name the same category.
    leaders = sorted(active, key=lambda v: -weights.get(v.agent, 0.0))[:2]
    tops = {max(v.scores, key=v.scores.get) for v in leaders}
    agree = len(tops) <= 1

    if confidence < config.REVIEW_MIN_CONFIDENCE:
        review.append(f"confidence {confidence:.2f} below {config.REVIEW_MIN_CONFIDENCE}")
    if margin < config.REVIEW_MIN_MARGIN:
        review.append(f"margin {margin:.2f} to {ranked[1]} below {config.REVIEW_MIN_MARGIN}")
    if not agree:
        review.append("agents disagree: " + ", ".join(
            f"{v.agent}={max(v.scores, key=v.scores.get)}" for v in leaders))

    intake = intake_issues(entities) if entities is not None else []
    if entities is not None and entities.letter_type == "proposal_rejection":
        review = []           # the claim-triage flags mean nothing for a refused proposal
    review += intake

    # Secondary issues need their own phrase evidence, not just leftover probability.
    cue_vote = next((v for v in active if v.agent == "cue"), None)
    secondary = [c for c in ranked[1:] if dist[c] >= config.SECONDARY_MIN_SCORE
                 and cue_vote is not None and cue_vote.scores.get(c, 0) > 0]

    # The standard reason: the reason agent's best match if it lies in the primary category.
    reason_vote = next((v for v in active if v.agent == "reason"), None)
    reason_row = None
    if reason_vote and reason_vote.reason_id:
        row = next(r for r in get_kb().denial_reasons if r["reason_id"] == reason_vote.reason_id)
        if row["category"] == primary:
            reason_row = row

    # A refused proposal is not a claim: the categories are kept as the agents' reading
    # of the reason, but no standard claim reason, appeal route or investigation applies.
    if entities is not None and entities.letter_type == "proposal_rejection":
        secondary, reason_row = [], None

    return TriageDecision(
        primary_category=primary,
        secondary_categories=secondary,
        distribution=dist,
        confidence=confidence,
        margin=margin,
        agents_agree=agree,
        needs_human_review=bool(review),
        review_reasons=review,
        intake_issues=intake,
        matched_reason_id=reason_row["reason_id"] if reason_row else None,
        matched_reason={k: reason_row[k] for k in ("sub_category", "reason_text", "carc_code", "rarc_code",
                                                   "irdai_clause_grounding", "appeal_route")} if reason_row else None,
        votes=votes,
        dispatch=[] if entities is not None and entities.letter_type == "proposal_rejection"
        else dispatch_plan([primary] + secondary, reason_row["reason_id"] if reason_row else None),
    )


def intake_issues(e):
    """Problems in the extracted case that the investigation stage cannot work around.

    Only raised for a letter, i.e. text that names an insurer, a claim or a patient;
    a bare reason paragraph is triaged without them.
    """
    if not (e.insurer or e.claim_id or e.patient_name):
        return []
    if e.letter_type == "proposal_rejection":
        product = f" for {e.policy_product or e.policy_product_raw}" if (e.policy_product or e.policy_product_raw) else ""
        return [f"not a claim denial: the insurer refused a proposal{product} (an application for a new policy) "
                "on underwriting grounds, so the claim-denial categories and appeal routes do not apply"]
    issues = []
    if not e.claim_id:
        issues.append("claim number not found in the letter")
    if not e.patient_name:
        issues.append("patient name not found in the letter")
    if not e.admission_date:
        issues.append("admission date not found; waiting-period and eligibility checks need it")
    if e.policy_type == "group":
        holder = f" for {e.policy_holder}" if e.policy_holder else ""
        issues.append(f"group policy{holder}: its wording is not in the knowledge base, so clause checks "
                      "need the policy document or the group terms")
    elif e.insurer and not e.policy_product:
        known = e.insurer in set(get_kb().products.values())
        if e.policy_product_raw:
            issues.append(f"product \"{e.policy_product_raw}\" is not in the knowledge base"
                          f"{'' if known else f' (no {e.insurer} wordings are)'}, so its wording cannot be looked up")
        elif not known:
            issues.append(f"no {e.insurer} policy wordings are in the knowledge base, so the clause cannot be looked up")
        else:
            issues.append("policy product not identified, so the policy wording cannot be looked up")
    if e.clause_resolution in ("ambiguous", "number_not_found"):
        issues.append(f"cited clause unclear: {e.clause_resolution_note}")
    return issues
