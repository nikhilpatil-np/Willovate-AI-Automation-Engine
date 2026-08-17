"""
Pipeline Orchestrator
=====================
Service layer that ties every core module together into a single
callable. nl_pipeline.py and any future entry point should import
this instead of calling core modules directly.

Flow:
  1. Normalize language (English / Hindi / Hinglish)
  2. Detect intent
  3. Extract entities
  4. Detect missing information
  5. Detect risk (on instruction text)
  6. Plan multi-step workflow
  7. Validate JSON
  8. Detect hallucinations / unsupported actions
  9. Return unified response dict
"""

from app.core.language_normalizer import normalize_with_meta
from app.core.entity_extractor import extract_entities
from app.core.missing_information import detect_missing_information
from app.core.risk_detector import detect_risk
from app.core.multi_step_planner import plan_multi_step
from app.core.hallucination_detector import detect_hallucinations
from app.utils.validator import validate_workflow
from app.services.model_server import get_model_server
import logging

logger = logging.getLogger(__name__)

# Module-level singleton — loads intent_model.pkl once at startup
_model_server = get_model_server()


def run_pipeline(instruction: str, lang: str = "auto") -> dict:
    """
    Execute the full NL → workflow pipeline for a single instruction.

    Args:
        instruction: Raw user instruction (any language).
        lang:        Hint — "en", "hi", "hinglish", or "auto" (default).

    Returns:
        {
            "original_instruction": str,
            "detected_language":    str,
            "normalized_instruction": str,
            "intent":               str,
            "entities":             dict,
            "missing":              list[str],
            "risk":                 dict,
            "workflow":             dict,
            "valid":                bool,
            "validation_error":     str | None,
            "hallucination_report": dict,
        }
    """

    logger.info("Pipeline start | instruction=%r", instruction)

    # ------------------------------------------------------------------
    # Step 1 — Language normalization
    # ------------------------------------------------------------------
    lang_meta = normalize_with_meta(instruction)
    normalized = lang_meta["normalized"]
    detected_language = lang_meta["detected_language"]

    logger.debug("Normalized: %r  lang=%s", normalized, detected_language)

    # ------------------------------------------------------------------
    # Step 2 — Intent detection via trained ML model
    #           (runs on normalized text; falls back to keywords if model
    #            is unavailable — handled transparently by model_server)
    # ------------------------------------------------------------------
    intent = _model_server.predict_intent(normalized)
    logger.debug("Intent: %s", intent)

    # ------------------------------------------------------------------
    # Step 3 — Entity extraction (run on original to preserve names/numbers)
    # ------------------------------------------------------------------
    entities = extract_entities(instruction)
    logger.debug("Entities: %s", entities)

    # ------------------------------------------------------------------
    # Step 4 — Missing information
    # ------------------------------------------------------------------
    missing = detect_missing_information(intent, entities)
    logger.debug("Missing: %s", missing)

    # ------------------------------------------------------------------
    # Step 5 — Risk detection (pass instruction text)
    # ------------------------------------------------------------------
    risk = detect_risk(instruction)
    logger.debug("Risk: %s", risk)

    # ------------------------------------------------------------------
    # Step 6 — Multi-step workflow planning
    # ------------------------------------------------------------------
    plan = plan_multi_step(instruction)
    workflow = {
        "intent":  plan["intent"],
        "steps":   plan["steps"],
    }
    logger.debug("Steps generated: %d", len(workflow["steps"]))

    # ------------------------------------------------------------------
    # Step 7 — JSON schema validation
    # ------------------------------------------------------------------
    valid, validation_error = validate_workflow(workflow)
    logger.debug("Valid: %s  error=%s", valid, validation_error)

    # ------------------------------------------------------------------
    # Step 8 — Hallucination / unsupported-action detection
    # ------------------------------------------------------------------
    hallucination_report = detect_hallucinations(
        [workflow],
        instructions=[instruction],
        check_grounding=True,
    )

    logger.info(
        "Pipeline done | intent=%s valid=%s risk=%s",
        intent, valid, risk.get("risk_level"),
    )

    return {
        "original_instruction":   instruction,
        "detected_language":      detected_language,
        "normalized_instruction": normalized,
        "intent":                 intent,
        "entities":               entities,
        "missing":                missing,
        "risk":                   risk,
        "workflow":               workflow,
        "valid":                  valid,
        "validation_error":       validation_error,
        "hallucination_report":   hallucination_report,
    }


async def execute_instruction(instruction: str, lang: str = "auto", headless: bool = True) -> dict:
    """
    Full end-to-end pipeline: Stage 1 + Stage 2 + Stage 3.

      Stage 1 — AI generates workflow JSON        (run_pipeline)
      Stage 2 — Browser runner executes workflow  (execute_workflow)
      Stage 3 — Execution result returned         (dict from runner)

    Args:
        instruction: Raw user instruction (any language).
        lang:        Language hint — "en", "hi", "hinglish", or "auto".
        headless:    True = no visible browser (API/CI mode).
                     False = opens Chromium window (local demo).

    Returns:
        Combined dict with all Stage 1 pipeline fields plus:
        {
            "execution": {
                "success":        bool,
                "steps_executed": int,
                "steps_total":    int,
                "failed_step":    int | None,
                "failed_action":  str | None,
                "error":          dict | None,
                "retry_count":    int,
                "verification":   bool,
                "customers":      list | None,
                "step_results":   list[dict],
            }
        }
    """

    # ------------------------------------------------------------------
    # Stage 1 — Generate workflow
    # ------------------------------------------------------------------
    pipeline_result = run_pipeline(instruction, lang=lang)

    # Abort execution if the risk level is HIGH and confirmation is needed
    risk_level = pipeline_result.get("risk", {}).get("risk_level", "LOW")
    if risk_level == "HIGH":
        logger.warning("Execution blocked — HIGH risk instruction: %r", instruction)
        pipeline_result["execution"] = {
            "success":        False,
            "steps_executed": 0,
            "steps_total":    len(pipeline_result["workflow"].get("steps", [])),
            "failed_step":    None,
            "failed_action":  None,
            "error":          {"message": "Execution blocked: HIGH risk operation requires manual confirmation."},
            "retry_count":    0,
            "verification":   False,
            "customers":      None,
            "step_results":   [],
        }
        return pipeline_result

    # Abort if workflow JSON is invalid
    if not pipeline_result.get("valid", False):
        logger.error("Execution skipped — invalid workflow JSON: %s", pipeline_result.get("validation_error"))
        pipeline_result["execution"] = {
            "success":        False,
            "steps_executed": 0,
            "steps_total":    len(pipeline_result["workflow"].get("steps", [])),
            "failed_step":    None,
            "failed_action":  None,
            "error":          {"message": f"Invalid workflow: {pipeline_result.get('validation_error')}"},
            "retry_count":    0,
            "verification":   False,
            "customers":      None,
            "step_results":   [],
        }
        return pipeline_result

    # Abort if required fields are missing — do not run browser with empty form
    missing = pipeline_result.get("missing", [])
    if missing:
        logger.warning("Execution blocked — missing required fields: %s", missing)
        pipeline_result["execution"] = {
            "success":        False,
            "steps_executed": 0,
            "steps_total":    len(pipeline_result["workflow"].get("steps", [])),
            "failed_step":    None,
            "failed_action":  None,
            "error":          {
                "message": f"Missing required fields: {', '.join(missing)}. "
                           f"Please provide: {', '.join(missing)}."
            },
            "retry_count":    0,
            "verification":   False,
            "customers":      None,
            "step_results":   [],
        }
        return pipeline_result

    # ------------------------------------------------------------------
    from automation.browser_runner import execute_workflow

    # Pass entities into workflow so browser_runner can resolve verify fields
    workflow = dict(pipeline_result["workflow"])
    workflow["entities"] = pipeline_result.get("entities", {})

    logger.info("Executing workflow | steps=%d headless=%s", len(workflow.get("steps", [])), headless)

    execution_result = await execute_workflow(workflow, headless=headless)

    # ------------------------------------------------------------------
    # Stage 3 — Attach execution result and return
    # ------------------------------------------------------------------
    pipeline_result["execution"] = execution_result

    logger.info(
        "Execution done | success=%s verified=%s retries=%d",
        execution_result.get("success"),
        execution_result.get("verification"),
        execution_result.get("retry_count", 0),
    )

    return pipeline_result


# ---------------------------------------------------------------------------
# Direct testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import json

    test_cases = [
        "Add Rahul as customer with phone 9876543210 and save.",
        "Rahul naam ka customer jod do.",
        "ग्राहक जोड़ो",
        "Open the CRM, add Pankaj Koche with phone 9876543210, save and verify the table.",
        "Download today's report, convert to Excel and email it to manager@company.com.",
    ]

    for tc in test_cases:
        print("\n" + "=" * 60)
        print("Instruction:", tc)
        result = run_pipeline(tc)
        print(json.dumps(result, indent=2, ensure_ascii=False))
