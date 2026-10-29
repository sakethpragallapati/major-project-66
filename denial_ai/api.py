"""HTTP API and web interface for intake and triage.

    python -m uvicorn denial_ai.api:app --port 8000
    then open http://localhost:8000

Analysed cases are kept in memory for the session only; nothing is written to disk.
"""

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from . import config
from .graph import Pipeline
from .intake.loader import load_bytes
from .knowledge import get_kb

WEB_DIR = Path(__file__).resolve().parent / "web"
MAX_UPLOAD_BYTES = 15 * 1024 * 1024

app = FastAPI(title="Denial Intake and Triage", version="1.0")
pipeline = Pipeline()
CASES = {}   # case id -> {"case": CaseState, "filename", "read_method", ...}


def _analyse(text, filename, read_method, started):
    case = pipeline.run(text=text)
    case_id = uuid.uuid4().hex[:10]
    CASES[case_id] = {"case": case, "filename": filename, "read_method": read_method,
                      "seconds": round(time.perf_counter() - started, 2),
                      "created": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    return _payload(case_id)


def _payload(case_id):
    item = CASES[case_id]
    return {"id": case_id, "filename": item["filename"], "read_method": item["read_method"],
            "seconds": item["seconds"], "created": item["created"],
            **json.loads(item["case"].model_dump_json())}


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/meta")
def meta():
    llm = config.LLM_PROVIDERS.get(config.LLM_PROVIDER)
    try:
        import rapidocr_onnxruntime  # noqa: F401
        ocr = True
    except ImportError:
        ocr = False
    return {"categories": config.CATEGORIES, "agents": [a.name for a in pipeline.agents],
            "agent_weights": config.AGENT_WEIGHTS, "llm_provider": config.LLM_PROVIDER if llm else None,
            "ocr_available": ocr, "langgraph": pipeline.graph is not None,
            "thresholds": {"min_confidence": config.REVIEW_MIN_CONFIDENCE, "min_margin": config.REVIEW_MIN_MARGIN}}


@app.post("/api/analyze")
async def analyze(file: Optional[UploadFile] = File(None), text: Optional[str] = Form(None)):
    started = time.perf_counter()
    if file is not None and file.filename:
        data = await file.read()
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, "file is larger than 15 MB")
        try:
            letter, method = load_bytes(data, file.filename)
        except Exception as exc:
            raise HTTPException(422, f"could not read {file.filename}: {exc}")
        return _analyse(letter, file.filename, method, started)
    if text and text.strip():
        return _analyse(text, None, "pasted text", started)
    raise HTTPException(400, "upload a file or paste the letter text")


@app.get("/api/clauses/{clause_id}")
def clause(clause_id: str):
    row = next((c for c in get_kb().clauses if c["clause_id"] == clause_id), None)
    if row is None:
        raise HTTPException(404, "unknown clause")
    return row


@app.get("/api/cases")
def cases():
    return [{"id": cid, "filename": v["filename"], "created": v["created"],
             "claim_id": v["case"].entities.claim_id, "category": v["case"].triage.primary_category,
             "needs_review": v["case"].triage.needs_human_review}
            for cid, v in reversed(CASES.items())]


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    if case_id not in CASES:
        raise HTTPException(404, "unknown case")
    return _payload(case_id)


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: str):
    if CASES.pop(case_id, None) is None:
        raise HTTPException(404, "unknown case")
    return {"deleted": case_id}


@app.delete("/api/cases")
def delete_all_cases():
    n = len(CASES)
    CASES.clear()
    return {"deleted": n}
