"""
Willovate AI Automation Engine — Entry Point
=============================================
All API endpoints defined here so they are fully visible in Swagger UI.

Run:
    uvicorn main:app --reload --port 8000

Then open:
    http://127.0.0.1:8000/docs
    http://127.0.0.1:8000          ← frontend served here
"""

import sys
import asyncio

# ── Windows / Python 3.13 — must use ProactorEventLoop for subprocess support
# ── (Playwright needs create_subprocess_exec which SelectorEventLoop forbids)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    # Also replace the running loop so uvicorn inherits Proactor from the start
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

# ── Apply logging config (format, level) for the whole app ─────────────────
import app.utils.logger  # noqa: F401  — side-effect import, sets basicConfig

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

from app.config.settings import PROJECT_NAME, VERSION
from app.services.orchestrator import run_pipeline, execute_instruction
from app.core.language_normalizer import normalize_with_meta
from app.core.multi_step_planner import plan_multi_step
from app.services.model_server import get_model_server

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title=PROJECT_NAME,
    version=VERSION,
    description=(
        "AI system that converts natural-language instructions "
        "(English, Hindi, Hinglish) into executable automation workflows. "
        "Use **/api/v1/generate-workflow** to test any instruction."
    ),
)

# ---------------------------------------------------------------------------
# CORS — allow all origins so the frontend (file://, localhost, etc.) can
# call the API without browser blocking.
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Serve the frontend at /  (frontend/index.html)
# ---------------------------------------------------------------------------

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


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
    confirmed: Optional[bool] = False   # set True to proceed past HIGH risk after user confirmation

class NormalizeRequest(BaseModel):
    text: str

class MultiStepRequest(BaseModel):
    instruction: str


# ---------------------------------------------------------------------------
# System routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["System"])
def home():
    """Serve the frontend UI or return the API welcome message."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {
        "message": f"{PROJECT_NAME} is running",
        "version": VERSION,
        "docs":    "/docs",
        "api":     "/api/v1/generate-workflow",
        "frontend": "Place frontend/index.html to serve the UI here.",
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Suppress favicon 404 in server logs."""
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/health", tags=["System"])
def health():
    """Liveness check."""
    return {"status": "ok", "version": VERSION}


@app.get("/api/v1/health", tags=["System"])
def pipeline_health():
    """Pipeline liveness — confirms the ML model is loaded."""
    server = get_model_server()
    return {
        "status":       "ok",
        "project":      PROJECT_NAME,
        "version":      VERSION,
        "model_loaded": not server.is_using_fallback(),
    }


# ---------------------------------------------------------------------------
# Pipeline routes
# ---------------------------------------------------------------------------

@app.post("/api/v1/generate-workflow", tags=["Pipeline"])
async def generate_workflow(req: InstructionRequest):
    """
    **Main endpoint — Stage 1 only.**

    Give any instruction in English, Hindi, or Hinglish.
    Returns intent, entities, missing fields, risk level, workflow steps,
    and validation result — without executing the browser.

    **Example instructions:**
    - `Add Nikhil as customer with phone 9823456789`
    - `Add Pankaj Koche as a customer with phone number 9876543210 and save`
    - `Delete customer Amit`
    - `Rahul naam ka customer jod do`
    """
    if not req.instruction.strip():
        raise HTTPException(status_code=400, detail="Instruction cannot be empty.")
    return run_pipeline(req.instruction, lang=req.lang or "auto")


@app.post("/api/v1/execute", tags=["Pipeline"])
async def execute(req: ExecuteRequest):
    """
    **Full end-to-end — Stage 1 + Stage 2 + Stage 3.**

    - Stage 1: AI generates the workflow JSON
    - Stage 2: Playwright bot executes it on the CRM browser
    - Stage 3: Returns execution result with verification

    Set `headless: false` to see the browser open on screen (demo mode).
    HIGH-risk instructions are blocked automatically.
    """
    if not req.instruction.strip():
        raise HTTPException(status_code=400, detail="Instruction cannot be empty.")
    return await execute_instruction(
        req.instruction,
        lang=req.lang or "auto",
        headless=req.headless if req.headless is not None else True,
        confirmed=req.confirmed or False,
    )


# ---------------------------------------------------------------------------
# Language routes
# ---------------------------------------------------------------------------

@app.post("/api/v1/normalize", tags=["Language"])
async def normalize(req: NormalizeRequest):
    """
    Detect language (English / Hindi / Hinglish) and normalize to clean English.

    **Example:** `Rahul naam ka customer jod do` → `rahul named customer add`
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    return normalize_with_meta(req.text)


@app.post("/api/v1/detect-intent", tags=["Language"])
async def detect_intent_endpoint(req: InstructionRequest):
    """
    Run language normalization + ML intent detection.

    **Returns:** detected language, normalized text, intent label, model info.
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


@app.post("/api/v1/multi-step-plan", tags=["Language"])
async def multi_step_plan(req: MultiStepRequest):
    """
    Break a compound instruction into ordered sub-tasks and steps.

    **Example:** `Download report, convert to Excel and email it to manager`
    """
    if not req.instruction.strip():
        raise HTTPException(status_code=400, detail="Instruction cannot be empty.")
    return plan_multi_step(req.instruction)
