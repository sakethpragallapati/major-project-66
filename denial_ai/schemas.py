"""Data models passed between the intake and triage nodes."""

from typing import Optional

from pydantic import BaseModel, Field


class ClauseMatch(BaseModel):
    clause_id: str
    clause_number: str
    clause_type: str
    section: str
    score: float
    text_preview: str
    evidence: str = ""


class IntakeEntities(BaseModel):
    letter_type: Optional[str] = None            # "claim_denial" or "proposal_rejection" (a new policy refused)
    claim_id: Optional[str] = None
    application_number: Optional[str] = None     # proposal / application number on a proposal rejection
    letter_ref: Optional[str] = None             # the letter's own reference number, not the claim
    patient_name: Optional[str] = None
    member_id: Optional[str] = None              # UHID / health card number
    insurer: Optional[str] = None
    tpa: Optional[str] = None                    # third-party administrator named in the letter
    policy_product: Optional[str] = None         # product in the knowledge base
    policy_product_raw: Optional[str] = None     # product name as printed, when it is not in the knowledge base
    policy_type: Optional[str] = None            # "retail" (product in the knowledge base) or "group"
    policy_holder: Optional[str] = None          # employer or group name on a group policy
    policy_number: Optional[str] = None
    policy_start: Optional[str] = None           # coverage period, ISO dates
    policy_end: Optional[str] = None
    admission_date: Optional[str] = None      # ISO yyyy-mm-dd
    denial_date: Optional[str] = None         # ISO yyyy-mm-dd
    hospital_name: Optional[str] = None
    diagnosis: Optional[str] = None           # illness as written ("FEVER")
    procedure: Optional[str] = None
    icd10_code: Optional[str] = None
    icd10_valid: Optional[bool] = None        # code exists in icd10_codes.csv
    icd10_billable: Optional[bool] = None
    claimed_amount: Optional[float] = None
    cited_clause_raw: Optional[str] = None
    cited_clause_id: Optional[str] = None
    clause_candidates: list[ClauseMatch] = Field(default_factory=list)
    clause_resolution: Optional[str] = None      # quoted / unique / confident / ambiguous / ...
    clause_resolution_note: Optional[str] = None
    denial_category_hint: Optional[str] = None   # short reason named next to the clause
    denial_reason_text: Optional[str] = None     # sentence(s) stating the denial
    appeal_window_days: Optional[int] = None
    deadline_note: Optional[str] = None          # the sentence that sets the time limit
    missing_fields: list[str] = Field(default_factory=list)


class AgentVote(BaseModel):
    agent: str
    scores: dict[str, float] = Field(default_factory=dict)   # category -> probability
    evidence: list[str] = Field(default_factory=list)
    abstained: bool = False
    reason_id: Optional[str] = None


class InvestigationPlan(BaseModel):
    category: str
    pipeline: str
    checks: list[str]
    runtime_tables: list[str]
    documents_needed: list[str]
    focus: Optional[str] = None      # standard reason the checks were narrowed to


class TriageDecision(BaseModel):
    primary_category: str
    secondary_categories: list[str] = Field(default_factory=list)
    distribution: dict[str, float]
    confidence: float
    margin: float
    agents_agree: bool
    needs_human_review: bool
    review_reasons: list[str] = Field(default_factory=list)
    intake_issues: list[str] = Field(default_factory=list)   # the subset of review_reasons about intake
    matched_reason_id: Optional[str] = None
    matched_reason: Optional[dict] = None
    votes: list[AgentVote] = Field(default_factory=list)
    dispatch: list[InvestigationPlan] = Field(default_factory=list)


class CaseState(BaseModel):
    source: Optional[str] = None
    raw_text: str = ""
    entities: Optional[IntakeEntities] = None
    votes: list[AgentVote] = Field(default_factory=list)
    triage: Optional[TriageDecision] = None
