"""
Model Evaluation Script
========================
Measures all 8 metrics defined in the project requirements (Req #15):

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
  Prints a per-metric report to stdout and saves a JSON report to
  outputs/evaluation_report.json
"""

import json
import os
import csv
from pathlib import Path

from app.core.intent_detector import IntentDetector
from app.core.entity_extractor import extract_entities
from app.core.workflow_generator import generate_workflow
from app.core.missing_information import detect_missing_information
from app.core.language_normalizer import detect_language
from app.core.hallucination_detector import detect_hallucinations
from app.utils.validator import validate_workflow


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parents[2]
INTENT_DATASET = ROOT / "data" / "processed" / "intent_dataset.csv"
ENTITY_DATASET = ROOT / "data" / "processed" / "entity_dataset.csv"
OUTPUT_DIR = ROOT / "outputs"
REPORT_PATH = OUTPUT_DIR / "evaluation_report.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_csv(path: Path) -> list:
    """Load a CSV file into a list of dicts."""
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _pct(correct: int, total: int) -> float:
    """Return percentage rounded to 2 decimal places."""
    if total == 0:
        return 0.0
    return round(correct / total * 100, 2)


# ---------------------------------------------------------------------------
# Metric 1 — Intent Accuracy
# ---------------------------------------------------------------------------

def evaluate_intent_accuracy() -> dict:
    """Compare predicted intent vs. ground-truth intent_dataset.csv."""

    detector = IntentDetector()
    rows = _load_csv(INTENT_DATASET)

    correct = 0
    errors = []

    for row in rows:
        instruction = row["instruction"].strip()
        expected = row["intent"].strip()
        predicted = detector.detect_intent(instruction)

        if predicted == expected:
            correct += 1
        else:
            errors.append({
                "instruction": instruction,
                "expected": expected,
                "predicted": predicted,
            })

    total = len(rows)
    accuracy = _pct(correct, total)

    return {
        "metric": "intent_accuracy",
        "total": total,
        "correct": correct,
        "accuracy_pct": accuracy,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Metric 2 — Entity-Extraction Accuracy
# ---------------------------------------------------------------------------

def evaluate_entity_accuracy() -> dict:
    """Compare extracted entities vs. ground-truth entity_dataset.csv."""

    rows = _load_csv(ENTITY_DATASET)

    entity_keys = ["name", "phone", "email", "product", "price", "page", "file"]
    field_stats = {k: {"total": 0, "correct": 0} for k in entity_keys}
    errors = []

    for row in rows:
        instruction = row["instruction"].strip()
        extracted = extract_entities(instruction)

        row_errors = []

        for key in entity_keys:
            expected_raw = row.get(key, "").strip()
            if not expected_raw:
                continue  # field not present in this row

            field_stats[key]["total"] += 1
            predicted = extracted.get(key, "")

            if str(predicted).strip().lower() == expected_raw.lower():
                field_stats[key]["correct"] += 1
            else:
                row_errors.append({
                    "field": key,
                    "expected": expected_raw,
                    "predicted": predicted,
                })

        if row_errors:
            errors.append({"instruction": instruction, "field_errors": row_errors})

    # Per-field accuracy
    per_field = {}
    total_all = 0
    correct_all = 0

    for key, stats in field_stats.items():
        per_field[key] = _pct(stats["correct"], stats["total"])
        total_all += stats["total"]
        correct_all += stats["correct"]

    return {
        "metric": "entity_extraction_accuracy",
        "total_fields": total_all,
        "correct_fields": correct_all,
        "overall_accuracy_pct": _pct(correct_all, total_all),
        "per_field_accuracy_pct": per_field,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Metric 3 — Workflow-Generation Accuracy
# (checks that key expected steps appear in generated workflow)
# ---------------------------------------------------------------------------

WORKFLOW_TEST_CASES = [
    {
        "instruction": "Add Rahul as customer with phone 9876543210",
        "expected_actions": ["OPEN_PAGE", "ENTER_TEXT", "CLICK"],
    },
    {
        "instruction": "Open the CRM and download report",
        "expected_actions": ["OPEN_PAGE", "CLICK"],
    },
    {
        "instruction": "Upload invoice.pdf",
        "expected_actions": ["OPEN_PAGE", "CLICK", "UPLOAD_FILE"],
    },
    {
        "instruction": "Add Pankaj Koche as customer with phone 9876543210 and save",
        "expected_actions": ["OPEN_PAGE", "ENTER_TEXT", "CLICK"],
    },
    {
        "instruction": "Rahul naam ka customer jod do",
        "expected_actions": ["OPEN_PAGE", "CLICK"],
    },
]


def evaluate_workflow_accuracy() -> dict:
    """Check that generated workflows contain all expected action types."""

    correct = 0
    errors = []

    for tc in WORKFLOW_TEST_CASES:
        instruction = tc["instruction"]
        workflow = generate_workflow(instruction)
        generated_actions = {
            step.get("action", "") for step in workflow.get("steps", [])
        }

        all_present = all(
            action in generated_actions for action in tc["expected_actions"]
        )

        if all_present:
            correct += 1
        else:
            missing = [
                a for a in tc["expected_actions"] if a not in generated_actions
            ]
            errors.append({
                "instruction": instruction,
                "expected_actions": tc["expected_actions"],
                "generated_actions": list(generated_actions),
                "missing_actions": missing,
            })

    total = len(WORKFLOW_TEST_CASES)

    return {
        "metric": "workflow_generation_accuracy",
        "total": total,
        "correct": correct,
        "accuracy_pct": _pct(correct, total),
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Metric 4 — JSON Validity Rate
# ---------------------------------------------------------------------------

def evaluate_json_validity() -> dict:
    """Run every workflow test case through the JSON schema validator."""

    valid_count = 0
    errors = []

    for tc in WORKFLOW_TEST_CASES:
        instruction = tc["instruction"]
        workflow = generate_workflow(instruction)
        is_valid, err_msg = validate_workflow(workflow)

        if is_valid:
            valid_count += 1
        else:
            errors.append({
                "instruction": instruction,
                "validation_error": err_msg,
            })

    total = len(WORKFLOW_TEST_CASES)

    return {
        "metric": "json_validity_rate",
        "total": total,
        "valid": valid_count,
        "validity_pct": _pct(valid_count, total),
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Metric 5 — Missing-Information Accuracy
# ---------------------------------------------------------------------------

MISSING_INFO_TEST_CASES = [
    # (instruction, expected_intent, expected_entities, expected_missing_keys)
    ("Create a customer",         "ADD_CUSTOMER",   {},                          ["name", "phone"]),
    ("Add Rahul as customer",     "ADD_CUSTOMER",   {"name": "Rahul"},           ["phone"]),
    ("Update product",            "UPDATE_PRODUCT", {},                          ["product", "price"]),
    ("Upload file",               "UPLOAD_FILE",    {},                          ["file"]),
    ("Add Rahul with phone 9876543210", "ADD_CUSTOMER", {"name": "Rahul", "phone": "9876543210"}, []),
]


def evaluate_missing_info_accuracy() -> dict:
    """Check that missing-info detection returns the correct missing keys."""

    correct = 0
    errors = []

    for instruction, intent, entities, expected_missing in MISSING_INFO_TEST_CASES:
        predicted_missing = detect_missing_information(intent, entities)

        if sorted(predicted_missing) == sorted(expected_missing):
            correct += 1
        else:
            errors.append({
                "instruction": instruction,
                "expected_missing": expected_missing,
                "predicted_missing": predicted_missing,
            })

    total = len(MISSING_INFO_TEST_CASES)

    return {
        "metric": "missing_information_accuracy",
        "total": total,
        "correct": correct,
        "accuracy_pct": _pct(correct, total),
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Metric 6 — Hinglish Accuracy
# ---------------------------------------------------------------------------

HINGLISH_TEST_CASES = [
    {
        "instruction": "Rahul naam ka customer jod do",
        "expected_intent": "ADD_CUSTOMER",
    },
    {
        "instruction": "CRM kholo aur customer banao",
        "expected_intent": "ADD_CUSTOMER",
    },
    {
        "instruction": "Product ka price ₹599 kar do",
        "expected_intent": "UPDATE_PRODUCT",
    },
    {
        "instruction": "File upload karo",
        "expected_intent": "UPLOAD_FILE",
    },
    {
        "instruction": "Report download karo",
        "expected_intent": "DOWNLOAD_REPORT",
    },
    {
        "instruction": "ग्राहक जोड़ो",
        "expected_intent": "ADD_CUSTOMER",
    },
    {
        "instruction": "ईमेल भेजो",
        "expected_intent": "SEND_EMAIL",
    },
]


def evaluate_hinglish_accuracy() -> dict:
    """Measure intent detection accuracy specifically on Hinglish / Hindi inputs."""

    from app.core.language_normalizer import normalize
    detector = IntentDetector()

    correct = 0
    errors = []

    for tc in HINGLISH_TEST_CASES:
        raw = tc["instruction"]
        normalized = normalize(raw)
        predicted = detector.detect_intent(normalized)
        expected = tc["expected_intent"]

        if predicted == expected:
            correct += 1
        else:
            errors.append({
                "original": raw,
                "normalized": normalized,
                "expected": expected,
                "predicted": predicted,
            })

    total = len(HINGLISH_TEST_CASES)

    return {
        "metric": "hinglish_accuracy",
        "total": total,
        "correct": correct,
        "accuracy_pct": _pct(correct, total),
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Metric 7 — Unsupported-Action Rate
# ---------------------------------------------------------------------------

def evaluate_unsupported_action_rate() -> dict:
    """
    Measure how often the generator produces actions outside the
    supported action list.
    """

    result = detect_hallucinations(
        [generate_workflow(tc["instruction"]) for tc in WORKFLOW_TEST_CASES]
    )

    return {
        "metric": "unsupported_action_rate",
        "total_steps": result["total_steps"],
        "unsupported_steps": result["unsupported_count"],
        "unsupported_rate_pct": result["unsupported_rate_pct"],
        "unsupported_actions": result["unsupported_actions"],
    }


# ---------------------------------------------------------------------------
# Metric 8 — Hallucination Rate
# ---------------------------------------------------------------------------

def evaluate_hallucination_rate() -> dict:
    """
    Measure how often generated steps have no clear grounding in the
    original instruction (hallucinated targets or values).
    """

    result = detect_hallucinations(
        [generate_workflow(tc["instruction"]) for tc in WORKFLOW_TEST_CASES],
        instructions=[tc["instruction"] for tc in WORKFLOW_TEST_CASES],
        check_grounding=True,
    )

    return {
        "metric": "hallucination_rate",
        "total_steps": result["total_steps"],
        "hallucinated_steps": result["hallucinated_count"],
        "hallucination_rate_pct": result["hallucination_rate_pct"],
        "examples": result.get("hallucinated_examples", []),
    }


# ---------------------------------------------------------------------------
# Report runner
# ---------------------------------------------------------------------------

def run_evaluation() -> dict:
    """Run all 8 metrics and return the full report dict."""

    print("\n" + "=" * 60)
    print("  Willovate AI — Model Evaluation Report")
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
        print(f"\n  Running: {label} ...", end=" ", flush=True)
        try:
            result = fn()
            report[result["metric"]] = result

            # Print summary line
            if "accuracy_pct" in result:
                print(f"{result['accuracy_pct']}%  "
                      f"({result.get('correct', '?')}/{result.get('total', '?')})")
            elif "validity_pct" in result:
                print(f"{result['validity_pct']}%")
            elif "unsupported_rate_pct" in result:
                print(f"Unsupported: {result['unsupported_rate_pct']}%")
            elif "hallucination_rate_pct" in result:
                print(f"Hallucinated: {result['hallucination_rate_pct']}%")
            else:
                print("done")
        except Exception as exc:
            print(f"ERROR — {exc}")
            report[label] = {"error": str(exc)}

    # Save report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n  Report saved to: {REPORT_PATH}")
    print("=" * 60 + "\n")

    return report


if __name__ == "__main__":
    run_evaluation()
