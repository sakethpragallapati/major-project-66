"""Triage agents. Each agent reads the case and returns a vote: a probability per
category plus the evidence behind it, or an abstention."""

import json
import re
from functools import lru_cache

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FeatureUnion

from .. import config
from ..knowledge import get_kb
from ..schemas import AgentVote
from .cues import CUES

CATS = config.CATEGORIES


def triage_text(state):
    """The part of the letter that states the reason, or the whole letter."""
    e = state.entities
    parts = [e.denial_category_hint, e.denial_reason_text] if e else []
    text = " ".join(p for p in parts if p)
    return text or state.raw_text


def _normalize(scores):
    total = sum(scores.values())
    return {c: round(scores.get(c, 0.0) / total, 4) for c in CATS} if total > 0 else {}


def score_cues(text):
    scores, evidence = {}, []
    low = text.lower()
    for cat, cues in CUES.items():
        for pattern, weight in cues:
            if m := re.search(pattern, low):
                scores[cat] = scores.get(cat, 0) + weight
                evidence.append(f"{cat}: '{m[0]}' (+{weight})")
    return scores, evidence


class CueAgent:
    name = "cue"
    strong_weight = 3

    def __call__(self, state):
        scores, evidence = score_cues(triage_text(state))
        if not scores:
            return AgentVote(agent=self.name, abstained=True, evidence=["no category cue found"])
        # One weak cue is weak evidence: blend towards uniform until the matched
        # weight reaches that of one strong cue.
        strength = min(1.0, sum(scores.values()) / self.strong_weight)
        probs = _normalize(scores)
        probs = {c: round(strength * probs[c] + (1 - strength) / len(CATS), 4) for c in CATS}
        return AgentVote(agent=self.name, scores=probs, evidence=evidence)


@lru_cache(maxsize=1)
def _reason_index():
    reasons = get_kb().denial_reasons
    docs = [f"{r['sub_category']}. {r['sub_category']}. {r['reason_text']}" for r in reasons]
    vec = FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
    ])
    matrix = vec.fit_transform(docs)
    return reasons, vec, matrix


# Indian letters and the reason table say some things in different words: a letter says
# the illness "does not warrant hospitalisation", the table says "inpatient admission not
# warranted". The letter's text is widened with the table's words before matching.
LETTER_TO_TABLE = {
    r"(?:(?:does|did)\s*not\s*warrant|not\s*(?:medically\s*)?(?:warranted|justified|required|necessary)\s*(?:for\s*)?)"
    r"\W*(?:\w+\W+){0,3}?hospitali[sz]|hospitali[sz]\w*\W+(?:\w+\W+){0,6}?(?:(?:does|did)\s*not\s*warrant"
    r"|not\s*(?:warranted|justified|required))": "inpatient admission not warranted outpatient",
    r"(?:managed|treated)\s*(?:on|as|in)\s*(?:an?\s*)?(?:opd|out[\s\-]*patient|day\s*care)": "outpatient setting",
}


def _widen(text):
    extra = [words for pattern, words in LETTER_TO_TABLE.items() if re.search(pattern, text, re.I)]
    return " ".join([text] + extra)


class ReasonMatchAgent:
    """Nearest standard denial reasons in denial_reasons.csv by TF-IDF similarity."""
    name = "reason"
    top_k = 3
    temperature = 0.05
    min_similarity = 0.08

    def __call__(self, state):
        reasons, vec, matrix = _reason_index()
        sims = cosine_similarity(vec.transform([_widen(triage_text(state))]), matrix)[0]
        best = int(np.argmax(sims))
        if sims[best] < self.min_similarity:
            return AgentVote(agent=self.name, abstained=True, evidence=[f"best similarity {sims[best]:.2f}"])

        # Category score = mean of its top-k reason similarities, softened into a distribution.
        cat_scores = {}
        for cat in CATS:
            idx = [i for i, r in enumerate(reasons) if r["category"] == cat]
            top = sorted(sims[idx], reverse=True)[: self.top_k]
            cat_scores[cat] = float(np.mean(top))
        vals = np.array([cat_scores[c] for c in CATS])
        probs = np.exp((vals - vals.max()) / self.temperature)
        probs /= probs.sum()

        order = np.argsort(-sims)[:3]
        evidence = [f"{reasons[i]['reason_id']} {reasons[i]['sub_category']} ({sims[i]:.2f})" for i in order]
        return AgentVote(agent=self.name, scores={c: round(float(p), 4) for c, p in zip(CATS, probs)},
                         evidence=evidence, reason_id=reasons[best]["reason_id"])


CLAUSE_TYPE_PRIOR = {
    "WAITING_PERIOD": {"PRE_EXISTING_WAITING_PERIOD": 1.0},
    "EXCLUSION": {"POLICY_EXCLUSION": 0.6, "MEDICAL_NECESSITY": 0.2, "FINANCIAL_LIMIT": 0.2},
}


class ClauseTypeAgent:
    """Reads the clause the letter cites: its type and the cues in its text."""
    name = "clause"

    def __call__(self, state):
        e = state.entities
        if not (e and e.clause_candidates):
            return AgentVote(agent=self.name, abstained=True, evidence=["no resolved clause"])
        if e.clause_resolution not in ("quoted", "unique", "confident"):
            return AgentVote(agent=self.name, abstained=True,
                             evidence=[f"clause not pinned down ({e.clause_resolution})"])
        top = e.clause_candidates[0]
        scores = dict(CLAUSE_TYPE_PRIOR.get(top.clause_type, {}))
        cue_scores, _ = score_cues(top.section + " " + top.text_preview)
        for cat, s in _normalize(cue_scores).items():
            scores[cat] = scores.get(cat, 0) + s
        if not scores:
            return AgentVote(agent=self.name, abstained=True, evidence=[f"{top.clause_id} gives no signal"])
        return AgentVote(agent=self.name, scores=_normalize(scores),
                         evidence=[f"{top.clause_id} ({top.clause_type}, {top.section})"])


LLM_PROMPT = """You classify Indian health-insurance claim denial letters into exactly one category.
Categories:
- MEDICAL_NECESSITY: treatment or admission judged not medically necessary, elective, or treatable as outpatient.
- PRE_EXISTING_WAITING_PERIOD: pre-existing disease, initial 30-day, specified-disease or other waiting period not completed, non-disclosure of a prior illness.
- POLICY_EXCLUSION: the treatment or cause is excluded by the policy (dental, cosmetic, maternity, adventure sports, substance abuse, unproven treatment, investigation-only stays and so on).
- FINANCIAL_LIMIT: sum insured exhausted, sub-limits, room rent caps, co-payment, deductible, non-medical items deducted.
- DOCUMENTATION: required documents missing, incomplete, unsigned, illegible or inconsistent.
- ADMINISTRATIVE_PROCEDURAL: late intimation or submission, duplicate claim, network or TPA procedure, pre-authorisation, premium or other-policy issues.
- ELIGIBILITY_COVERAGE: the person or the date is not covered: not an insured member, policy lapsed, cancelled or not yet started, age or territory limits, fraud.
Answer with JSON only: {"category": "<one category>", "confidence": <0 to 1>}"""


class LLMAgent:
    """Optional voter. Enabled with DENIAL_AI_LLM=nvidia|groq|openai and the provider key."""
    name = "llm"

    def __init__(self):
        self.client, self.model = None, None
        provider = config.LLM_PROVIDERS.get(config.LLM_PROVIDER)
        if provider:
            import os
            base_url, key_env, default_model = provider
            if os.environ.get(key_env):
                from openai import OpenAI
                self.client = OpenAI(base_url=base_url, api_key=os.environ[key_env])
                self.model = config.LLM_MODEL or default_model

    def __call__(self, state):
        if self.client is None:
            return AgentVote(agent=self.name, abstained=True, evidence=["LLM agent not configured"])
        try:
            reply = self.client.chat.completions.create(
                model=self.model, temperature=0, max_tokens=60,
                messages=[{"role": "system", "content": LLM_PROMPT},
                          {"role": "user", "content": triage_text(state)[:4000]}],
            ).choices[0].message.content
            data = json.loads(re.search(r"\{.*\}", reply, re.S)[0])
            cat, conf = data["category"], float(data.get("confidence", 0.7))
            if cat not in CATS:
                raise ValueError(f"unknown category {cat}")
        except Exception as exc:  # network, parsing or schema problems: abstain, never fail the case
            return AgentVote(agent=self.name, abstained=True, evidence=[f"LLM error: {exc}"])
        rest = (1 - conf) / (len(CATS) - 1)
        return AgentVote(agent=self.name, scores={c: (conf if c == cat else rest) for c in CATS},
                         evidence=[f"{self.model}: {cat} ({conf:.2f})"])


def default_agents():
    return [CueAgent(), ReasonMatchAgent(), ClauseTypeAgent(), LLMAgent()]
