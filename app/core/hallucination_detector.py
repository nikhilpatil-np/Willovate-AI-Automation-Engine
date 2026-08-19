"""
Hallucination Detector
======================
Detects two classes of problems in generated workflows:

  1. Unsupported actions — steps whose "action" value is not in the
     official supported-action list (same list as workflow_validator.py).

  2. Hallucinated targets — steps whose "target" or "value" has no
     plausible grounding in the original instruction
     (only checked when check_grounding=True and instructions are supplied).

Used by:
  - app/models/evaluate_models.py  (metrics 7 & 8)
  - app/services/orchestrator.py   (per-request quality check)
  - app/api/nl_pipeline.py         (optional response field)
"""

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Supported action list (mirrors workflow_validator.py)
# ---------------------------------------------------------------------------

SUPPORTED_ACTIONS = {
    "OPEN_URL",
    "OPEN_PAGE",
    "CLICK",
    "ENTER_TEXT",
    "SELECT_OPTION",
    "UPLOAD_FILE",
    "DOWNLOAD_FILE",
    "READ_TEXT",
    "READ_TABLE",
    "SCROLL",
    "WAIT",
    "SUBMIT",
    "TAKE_SCREENSHOT",
    "SEND_EMAIL",
    "CONVERT_FILE",
    "DELETE_RECORD",
    "UPDATE_RECORD",
    "VERIFY_RECORD",
    # Web change actions
    "CHANGE_LOGO",
    "CHANGE_STYLE",
    "ADD_BANNER",
    "CHANGE_TEXT",
}

# ---------------------------------------------------------------------------
# Grounding helpers
# ---------------------------------------------------------------------------

# Words that are generic UI targets — always considered grounded
GENERIC_TARGETS = {
    # Navigation & actions
    "save", "cancel", "submit", "close", "back", "next", "ok",
    "add customer", "add employee", "add product",
    "upload file", "download", "download report",
    "customer list", "product list", "employee list",
    # Pages
    "customers", "products", "employees", "reports", "upload",
    "crm", "dashboard", "settings",
    # Form fields — standard UI labels always grounded by intent
    "customer name", "phone number", "phone", "email",
    "customer email", "employee name", "employee phone", "employee email",
    "product name", "product price", "price", "category", "stock",
    "department", "status",
    # Misc
    "current_page", "excel", "xlsx", "down", "up",
}


def _is_grounded(value: str, instruction: str) -> bool:
    """
    Return True if `value` has plausible grounding in the instruction.

    Grounding rules (any one is sufficient):
      a) The value (case-insensitive) appears verbatim in the instruction.
      b) Each word in the value appears in the instruction.
      c) The value is a known generic UI target.
      d) The value is a number (phone, price, wait seconds).
      e) The value matches an email pattern (extracted by entity extractor).
    """

    val_lower = value.lower().strip()

    # Generic UI target
    if val_lower in GENERIC_TARGETS:
        return True

    # Numeric value
    if re.fullmatch(r"[\d\s₹.,%-]+", val_lower):
        return True

    # Email pattern
    if re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", val_lower):
        return True

    instr_lower = instruction.lower()

    # Verbatim substring
    if val_lower in instr_lower:
        return True

    # All words present (handles reordering)
    words = [w for w in re.split(r"\W+", val_lower) if len(w) > 2]
    if words and all(w in instr_lower for w in words):
        return True

    return False


# ---------------------------------------------------------------------------
# Core detector
# ---------------------------------------------------------------------------

def detect_hallucinations(
    workflows: list,
    instructions: Optional[list] = None,
    check_grounding: bool = False,
) -> dict:
    """
    Analyse a list of workflow dicts for unsupported actions and,
    optionally, hallucinated targets.

    Args:
        workflows:       List of workflow dicts, each with a "steps" key.
        instructions:    Parallel list of original instruction strings.
                         Required when check_grounding=True.
        check_grounding: When True, also flag steps whose target/value
                         cannot be grounded in the original instruction.

    Returns:
        {
            "total_steps":           int,
            "unsupported_count":     int,
            "unsupported_rate_pct":  float,
            "unsupported_actions":   list[str],   # distinct unsupported action names
            "hallucinated_count":    int,          # only when check_grounding=True
            "hallucination_rate_pct": float,
            "hallucinated_examples": list[dict],
        }
    """

    total_steps = 0
    unsupported_count = 0
    unsupported_action_names = set()
    hallucinated_count = 0
    hallucinated_examples = []

    for idx, workflow in enumerate(workflows):
        instruction = (
            instructions[idx]
            if (instructions and idx < len(instructions))
            else ""
        )

        steps = workflow.get("steps", [])

        for step in steps:
            total_steps += 1
            action = step.get("action", "").upper()

            # ----- Unsupported action -----
            if action not in SUPPORTED_ACTIONS:
                unsupported_count += 1
                unsupported_action_names.add(action)

            # ----- Hallucinated grounding -----
            if check_grounding and instruction:
                target = step.get("target", "")
                value = step.get("value", "")

                target_grounded = _is_grounded(target, instruction) if target else True
                value_grounded = _is_grounded(value, instruction) if value else True

                if not target_grounded or not value_grounded:
                    hallucinated_count += 1
                    hallucinated_examples.append({
                        "instruction": instruction,
                        "step":        step,
                        "ungrounded":  {
                            "target": target if not target_grounded else None,
                            "value":  value  if not value_grounded  else None,
                        },
                    })

    def _rate(n: int) -> float:
        if total_steps == 0:
            return 0.0
        return round(n / total_steps * 100, 2)

    return {
        "total_steps":            total_steps,
        "unsupported_count":      unsupported_count,
        "unsupported_rate_pct":   _rate(unsupported_count),
        "unsupported_actions":    sorted(unsupported_action_names),
        "hallucinated_count":     hallucinated_count,
        "hallucination_rate_pct": _rate(hallucinated_count),
        "hallucinated_examples":  hallucinated_examples,
    }


# ---------------------------------------------------------------------------
# Convenience: check a single workflow
# ---------------------------------------------------------------------------

def check_workflow(workflow: dict, instruction: str = "") -> dict:
    """Wrapper for a single workflow."""
    return detect_hallucinations(
        [workflow],
        instructions=[instruction] if instruction else None,
        check_grounding=bool(instruction),
    )


# ---------------------------------------------------------------------------
# Direct testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import json

    test_workflows = [
        {
            "instruction": "Add Rahul as customer with phone 9876543210",
            "workflow": {
                "steps": [
                    {"action": "OPEN_PAGE",   "target": "Customers"},
                    {"action": "ENTER_TEXT",  "target": "Customer Name", "value": "Rahul"},
                    {"action": "ENTER_TEXT",  "target": "Phone Number",  "value": "9876543210"},
                    {"action": "CLICK",       "target": "Add Customer"},
                ]
            }
        },
        {
            "instruction": "Upload invoice.pdf",
            "workflow": {
                "steps": [
                    {"action": "OPEN_PAGE",    "target": "Upload"},
                    {"action": "UPLOAD_FILE",  "target": "invoice.pdf"},
                    {"action": "TELEPORT",     "target": "Mars"},   # fake / unsupported
                ]
            }
        },
    ]

    print("=" * 60)
    print("Hallucination Detector Test")
    print("=" * 60)

    for tc in test_workflows:
        print(f"\nInstruction: {tc['instruction']}")
        result = check_workflow(tc["workflow"], tc["instruction"])
        print(json.dumps(result, indent=2))
