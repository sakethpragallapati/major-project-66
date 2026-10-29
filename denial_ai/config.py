"""Paths, agent weights and thresholds for intake and triage."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = Path(os.environ.get("DENIAL_AI_RUNTIME_DIR", ROOT / "data" / "runtime"))

CATEGORIES = [
    "MEDICAL_NECESSITY",
    "PRE_EXISTING_WAITING_PERIOD",
    "POLICY_EXCLUSION",
    "FINANCIAL_LIMIT",
    "DOCUMENTATION",
    "ADMINISTRATIVE_PROCEDURAL",
    "ELIGIBILITY_COVERAGE",
]

# Weight of each agent in the supervisor's soft vote. An agent that abstains
# contributes nothing, and the remaining weights are renormalized.
AGENT_WEIGHTS = {
    "cue": 0.45,
    "reason": 0.35,
    "clause": 0.10,
    "llm": 0.40,
}

REVIEW_MIN_CONFIDENCE = 0.50   # below this the case goes to a human reviewer
REVIEW_MIN_MARGIN = 0.15       # gap between the first and second category
SECONDARY_MIN_SCORE = 0.25     # other categories reported alongside the primary one

# Optional LLM voter: DENIAL_AI_LLM=nvidia|groq|openai plus the provider's API key.
LLM_PROVIDER = os.environ.get("DENIAL_AI_LLM", "").strip().lower()
LLM_PROVIDERS = {
    "nvidia": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY", "meta/llama-3.1-70b-instruct"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "llama-3.1-8b-instant"),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o-mini"),
}
LLM_MODEL = os.environ.get("DENIAL_AI_LLM_MODEL", "")
