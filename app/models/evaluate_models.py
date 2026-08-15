"""
Model Evaluation Script
========================
Measures all 8 metrics defined in the project requirements (Req 15):

  1. Intent accuracy
  2. Entity-extraction accuracy
  3. Workflow-generation accuracy
  4. JSON validity rate
  5. Missing-information accuracy
  6. Hinglish accuracy
  7. Unsupported-action rate
  8. Hallucination rate

Usage:
  python app/models/evaluate_models.py

Output:
  Prints a per-metric report to stdout.
  Saves full JSON report to outputs/evaluation_report.json
"""

import json
import os
import csv
from pathlib import Path

from app.core.intent_detector       import IntentDetector
from app.core.entity_extractor      import extract_entities
from app.core.multi_step_planner    import plan_multi_step   # fixed — was workflow_generator
from app.core.missing_information   import detect_missing_information
from app.core.language_normalizer   import detect_language, normalize
from app.core.hallucination_detector import detect_hallucinations
from app.utils.validator            import validate_workflow


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT           = Path(__file__).parents[2]
INTENT_DATASET = ROOT / "data" / "processed" / "intent_dataset.csv"
ENTITY_DATASET = ROOT / "data" / "processed" / "entity_dataset.csv"
OUTPUT_DIR     = ROOT / "outputs"
REPORT_PATH    = OUTPUT_DIR / "evaluation_report.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_csv(path: Path) -> list:
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _pct(correct: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(correct / total * 100, 2)


def _generate(instruction: str) -> dict:
    """Wrapper that calls plan_multi_step and returns a workflow dict."""
    return plan_multi_step(instruction)


# ---------------------------------------------------------------------------
# Metric 1 — Intent Accuracy
# ---------------------------------------------------------------------------

def evaluate_intent_accuracy() -> dict:
    from app.services.model_server import get_model_server
    server = get_model_server()
    rows   = _load_csv(INTENT_DATASET)
    correct = 0
    errors  = []

    for row in rows:
        instruction = row["instruction"].strip()
        expected    = row["intent"].strip().upper()
        predicted   = server.predict_intent(instruction).upper()

        if predicted == expected:
            correct += 1
        else:
            errors.append({
                "instruction": instruction,
                "expected":    expected,
                "predicted":   predicted,
            })

    total = len(rows)
    return {
        "metric":       "intent_accuracy",
        "total":        total,
        "correct":      correct,
        "accuracy_pct": _pct(correct, total),
        "errors":       errors[:10],
    }


# ---------------------------------------------------------------------------
# Metric 2 — Entity-Extraction Accuracy
# ---------------------------------------------------------------------------

def evaluate_entity_accuracy() -> dict:
    rows        = _load_csv(ENTITY_DATASET)
    entity_keys = ["name", "phone", "email", "product", "price", "page", "file"]
    field_stats = {k: {"total": 0, "correct": 0} for k in entity_keys}
    errors      = []

    for row in rows:
        instruction = row["instruction"].strip()
        extracted   = extract_entities(instruction)
        row_errors  = []

        for key in entity_keys:
            expected_raw = row.get(key, "").strip()
            if not expected_raw:
                continue
            field_stats[key]["total"]  += 1
            predicted = str(extracted.get(key, "")).strip()
            if predicted.lower() == expected_raw.lower():
                field_stats[key]["correct"] += 1
            else:
                row_errors.append({
                    "field":     key,
                    "expected":  expected_raw,
                    "predicted": predicted,
                })

        if row_errors:
            errors.append({"instruction": instruction, "field_errors": row_errors})

    per_field   = {k: _pct(v["correct"], v["total"]) for k, v in field_stats.items()}
    total_all   = sum(v["total"]   for v in field_stats.values())
    correct_all = sum(v["correct"] for v in field_stats.values())

    return {
        "metric":                  "entity_extraction_accuracy",
        "total_fields":            total_all,
        "correct_fields":          correct_all,
        "overall_accuracy_pct":    _pct(correct_all, total_all),
        "per_field_accuracy_pct":  per_field,
        "errors":                  errors[:10],
    }


# ---------------------------------------------------------------------------
# Metric 3 — Workflow-Generation Accuracy
# ---------------------------------------------------------------------------

WORKFLOW_TEST_CASES = [
    {
        "instruction":       "Add Rahul as customer with phone 9876543210",
        "expected_actions":  ["OPEN_PAGE", "ENTER_TEXT", "CLICK"],
    },
    {
        "instruction":       "Open the CRM and download report",
        "expected_actions":  ["OPEN_PAGE", "CLICK"],
    },
    {
        "instruction":       "Upload invoice.pdf",
        "expected_actions":  ["OPEN_PAGE", "UPLOAD_FILE"],
    },
    {
        "instruction":       "Add Pankaj Koche as customer with phone 9876543210 and save",
        "expected_actions":  ["OPEN_PAGE", "ENTER_TEXT", "CLICK"],
    },
    {
        "instruction":       "Rahul naam ka customer jod do phone 9876543210",
        "expected_actions":  ["OPEN_PAGE", "CLICK"],
    },
    {
        "instruction":       "Open the CRM, add Pankaj Koche as a customer with phone 9876543210, save and verify",
        "expected_actions":  ["OPEN_PAGE", "ENTER_TEXT", "CLICK", "READ_TABLE", "VERIFY_RECORD"],
    },
    {
        "instruction":       "Take a screenshot",
        "expected_actions":  ["TAKE_SCREENSHOT"],
    },
    {
        "instruction":       "Download today's report",
        "expected_actions":  ["OPEN_PAGE", "CLICK"],
    },
]


def evaluate_workflow_accuracy() -> dict:
    correct = 0
    errors  = []

    for tc in WORKFLOW_TEST_CASES:
        instruction = tc["instruction"]
        workflow    = _generate(instruction)
        generated   = {s.get("action", "") for s in workflow.get("steps", [])}
        all_present = all(a in generated for a in tc["expected_actions"])

        if all_present:
            correct += 1
        else:
            errors.append({
                "instruction":       instruction,
                "expected_actions":  tc["expected_actions"],
                "generated_actions": sorted(generated),
                "missing_actions":   [a for a in tc["expected_actions"] if a not in generated],
            })

    total = len(WORKFLOW_TEST_CASES)
    return {
        "metric":       "workflow_generation_accuracy",
        "total":        total,
        "correct":      correct,
        "accuracy_pct": _pct(correct, total),
        "errors":       errors,
    }


# ---------------------------------------------------------------------------
# Metric 4 — JSON Validity Rate
# ---------------------------------------------------------------------------

def evaluate_json_validity() -> dict:
    valid_count = 0
    errors      = []

    for tc in WORKFLOW_TEST_CASES:
        instruction = tc["instruction"]
        workflow    = _generate(instruction)
        is_valid, err_msg = validate_workflow(workflow)

        if is_valid:
            valid_count += 1
        else:
            errors.append({
                "instruction":      instruction,
                "validation_error": err_msg,
            })

    total = len(WORKFLOW_TEST_CASES)
    return {
        "metric":       "json_validity_rate",
        "total":        total,
        "valid":        valid_count,
        "validity_pct": _pct(valid_count, total),
        "errors":       errors,
    }


# ---------------------------------------------------------------------------
# Metric 5 — Missing-Information Accuracy
# ---------------------------------------------------------------------------

MISSING_INFO_CASES = [
    ("Create a customer",                         "ADD_CUSTOMER",   {},                                          ["name", "phone"]),
    ("Add Rahul as customer",                     "ADD_CUSTOMER",   {"name": "Rahul"},                           ["phone"]),
    ("Update product",                            "UPDATE_PRODUCT", {},                                          ["product", "price"]),
    ("Upload file",                               "UPLOAD_FILE",    {},                                          ["file"]),
    ("Add Rahul with phone 9876543210",            "ADD_CUSTOMER",   {"name": "Rahul", "phone": "9876543210"},    []),
    ("Send email",                                "SEND_EMAIL",     {},                                          ["email"]),
    ("Delete customer",                           "DELETE_CUSTOMER",{},                                          ["name"]),
]


def evaluate_missing_info_accuracy() -> dict:
    correct = 0
    errors  = []

    for instruction, intent, entities, expected in MISSING_INFO_CASES:
        predicted = detect_missing_information(intent, entities)
        if sorted(predicted) == sorted(expected):
            correct += 1
        else:
            errors.append({
                "instruction":      instruction,
                "expected_missing": expected,
                "predicted_missing": predicted,
            })

    total = len(MISSING_INFO_CASES)
    return {
        "metric":       "missing_information_accuracy",
        "total":        total,
        "correct":      correct,
        "accuracy_pct": _pct(correct, total),
        "errors":       errors,
    }


# ---------------------------------------------------------------------------
# Metric 6 — Hinglish Accuracy
# ---------------------------------------------------------------------------

HINGLISH_CASES = [
    ("Rahul naam ka customer jod do",     "ADD_CUSTOMER"),
    ("CRM kholo aur customer banao",      "ADD_CUSTOMER"),
    ("Product ka price 599 kar do",       "UPDATE_PRODUCT"),
    ("File upload karo",                  "UPLOAD_FILE"),
    ("Report download karo",              "DOWNLOAD_REPORT"),
    ("ग्राहक जोड़ो",                        "ADD_CUSTOMER"),
    ("ईमेल भेजो",                          "SEND_EMAIL"),
    ("Customer delete karo",              "DELETE_CUSTOMER"),
    ("Employee add karo",                 "ADD_CUSTOMER"),
    ("Screenshot lo",                     "TAKE_SCREENSHOT"),
]


def evaluate_hinglish_accuracy() -> dict:
    detector = IntentDetector()
    correct  = 0
    errors   = []

    for raw, expected in HINGLISH_CASES:
        normalized = normalize(raw)
        predicted  = detector.detect_intent(normalized).upper()
        expected_u = expected.upper()

        if predicted == expected_u:
            correct += 1
        else:
            errors.append({
                "original":   raw,
                "normalized": normalized,
                "expected":   expected_u,
                "predicted":  predicted,
            })

    total = len(HINGLISH_CASES)
    return {
        "metric":       "hinglish_accuracy",
        "total":        total,
        "correct":      correct,
        "accuracy_pct": _pct(correct, total),
        "errors":       errors,
    }


# ---------------------------------------------------------------------------
# Metric 7 — Unsupported-Action Rate
# ---------------------------------------------------------------------------

def evaluate_unsupported_action_rate() -> dict:
    workflows = [_generate(tc["instruction"]) for tc in WORKFLOW_TEST_CASES]
    result    = detect_hallucinations(workflows)

    return {
        "metric":               "unsupported_action_rate",
        "total_steps":          result["total_steps"],
        "unsupported_steps":    result["unsupported_count"],
        "unsupported_rate_pct": result["unsupported_rate_pct"],
        "unsupported_actions":  result["unsupported_actions"],
    }


# ---------------------------------------------------------------------------
# Metric 8 — Hallucination Rate
# ---------------------------------------------------------------------------

def evaluate_hallucination_rate() -> dict:
    instructions = [tc["instruction"] for tc in WORKFLOW_TEST_CASES]
    workflows    = [_generate(i) for i in instructions]
    result       = detect_hallucinations(
        workflows,
        instructions=instructions,
        check_grounding=True,
    )

    return {
        "metric":                  "hallucination_rate",
        "total_steps":             result["total_steps"],
        "hallucinated_steps":      result["hallucinated_count"],
        "hallucination_rate_pct":  result["hallucination_rate_pct"],
        "examples":                result.get("hallucinated_examples", [])[:5],
    }


# ---------------------------------------------------------------------------
# Report runner
# ---------------------------------------------------------------------------

def run_evaluation() -> dict:

    print("\n" + "=" * 60)
    print("  Willovate AI Automation Engine — Model Evaluation")
    print("=" * 60)

    metrics = [
        ("1. Intent Accuracy",              evaluate_intent_accuracy),
        ("2. Entity-Extraction Accuracy",   evaluate_entity_accuracy),
        ("3. Workflow-Generation Accuracy", evaluate_workflow_accuracy),
        ("4. JSON Validity Rate",           evaluate_json_validity),
        ("5. Missing-Info Accuracy",        evaluate_missing_info_accuracy),
        ("6. Hinglish Accuracy",            evaluate_hinglish_accuracy),
        ("7. Unsupported-Action Rate",      evaluate_unsupported_action_rate),
        ("8. Hallucination Rate",           evaluate_hallucination_rate),
    ]

    report = {}

    for label, fn in metrics:
        print(f"\n  {label} ...", end=" ", flush=True)
        try:
            result = fn()
            report[result["metric"]] = result
            if "accuracy_pct" in result:
                print(f"{result['accuracy_pct']}%  ({result.get('correct','?')}/{result.get('total','?')})")
            elif "validity_pct" in result:
                print(f"Valid {result['validity_pct']}%")
            elif "unsupported_rate_pct" in result:
                print(f"Unsupported {result['unsupported_rate_pct']}%")
            elif "hallucination_rate_pct" in result:
                print(f"Hallucinated {result['hallucination_rate_pct']}%")
            else:
                print("done")
        except Exception as exc:
            print(f"ERROR — {exc}")
            report[label] = {"error": str(exc)}

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved: {REPORT_PATH}")
    print("=" * 60 + "\n")
    return report


if __name__ == "__main__":
    run_evaluation()
