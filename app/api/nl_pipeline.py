"""
NL Pipeline — API Router
=========================
Defines all pipeline endpoints as an APIRouter so they are fully
visible in the main Swagger UI at /docs.

Endpoints (all prefixed with /api/v1 when registered in routes.py):
  POST /api/v1/generate-workflow  — full AI pipeline (Stage 1)
  POST /api/v1/execute            — full pipeline + browser execution (Stage 1+2+3)
  POST /api/v1/normalize          — language normalisation only
  POST /api/v1/detect-intent      — intent detection only
  POST /api/v1/multi-step-plan    — multi-step planner only
  GET  /api/v1/health             — pipeline liveness check
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.orchestrator import run_pipeline, execute_instruction
from app.core.language_normalizer import normalize_with_meta
from app.core.multi_step_planner import plan_multi_step
from app.services.model_server import get_model_server
from app.config.settings import PROJECT_NAME, VERSION

# ---------------------------------------------------------------------------
# Router  (prefix and tags applied in routes.py)
# ---------------------------------------------------------------------------

router = APIRouter()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class InstructionRequest(BaseModel):
    instruction: str
    lang: Optional[str] = "auto"


class ExecuteRequest(BaseModel):
    instruction: str
    lang: Optional[str] = "auto"
    headless: Optional[bool] = True


class NormalizeRequest(BaseModel):
    text: str


class MultiStepRequest(BaseModel):
    instruction: str


# ---------------------------------------------------------------------------
# POST /generate-workflow
# ---------------------------------------------------------------------------

@router.post("/generate-workflow", tags=["Pipeline"])
async def generate_workflow(req: InstructionRequest):
    """
    **Stage 1 only** — AI understands the instruction and returns workflow JSON.

    Pass any instruction in English, Hindi, or Hinglish.

    Returns intent, entities, missing fields, risk level, workflow steps,
    JSON validation result, and hallucination report.
    """

    if not req.instruction.strip():
        raise HTTPException(status_code=400, detail="Instruction cannot be empty.")

    return run_pipeline(req.instruction, lang=req.lang or "auto")


# ---------------------------------------------------------------------------
# POST /execute
# ---------------------------------------------------------------------------

@router.post("/execute", tags=["Pipeline"])
async def execute(req: ExecuteRequest):
    """
    **Stage 1 + 2 + 3** — Generate workflow AND execute it on the CRM browser.

    - `headless: true` (default) — runs silently, no browser window
    - `headless: false` — opens a visible Chromium window (demo mode)

    HIGH risk instructions (delete all, payments) are blocked automatically.

    Extra response fields: `execution.success`, `execution.verification`,
    `execution.customers`, `execution.step_results`
    """

    if not req.instruction.strip():
        raise HTTPException(status_code=400, detail="Instruction cannot be empty.")

    return await execute_instruction(
        req.instruction,
        lang=req.lang or "auto",
        headless=req.headless if req.headless is not None else True,
    )


# ---------------------------------------------------------------------------
# POST /normalize
# ---------------------------------------------------------------------------

@router.post("/normalize", tags=["Language"])
async def normalize(req: NormalizeRequest):
    """
    Detect language (English / Hindi / Hinglish) and normalize to clean English.
    """

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    return normalize_with_meta(req.text)


# ---------------------------------------------------------------------------
# POST /detect-intent
# ---------------------------------------------------------------------------

@router.post("/detect-intent", tags=["Language"])
async def detect_intent_endpoint(req: InstructionRequest):
    """
    Run language normalization + ML intent detection on an instruction.
    """

    if not req.instruction.strip():
        raise HTTPException(status_code=400, detail="Instruction cannot be empty.")

    meta   = normalize_with_meta(req.instruction)
    server = get_model_server()
    intent = server.predict_intent(meta["normalized"])

    return {
        "original":          req.instruction,
        "detected_language": meta["detected_language"],
        "normalized":        meta["normalized"],
        "intent":            intent,
        "model_info":        server.model_info(),
    }


# ---------------------------------------------------------------------------
# POST /multi-step-plan
# ---------------------------------------------------------------------------

@router.post("/multi-step-plan", tags=["Language"])
async def multi_step_plan(req: MultiStepRequest):
    """
    Break a compound instruction into ordered sub-tasks and workflow steps.
    """

    if not req.instruction.strip():
        raise HTTPException(status_code=400, detail="Instruction cannot be empty.")

    return plan_multi_step(req.instruction)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@router.get("/health", tags=["System"])
async def health():
    """Pipeline liveness — confirms the ML model is loaded."""

    server = get_model_server()

    return {
        "status":       "ok",
        "project":      PROJECT_NAME,
        "version":      VERSION,
        "model_loaded": not server.is_using_fallback(),
    }
