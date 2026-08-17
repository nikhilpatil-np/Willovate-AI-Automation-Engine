"""
Risk Detector
=============
Classifies an instruction string as LOW / MEDIUM / HIGH risk.

HIGH  — deletes, drops, shutdowns, irreversible bulk operations
MEDIUM — updates, cancellations, email sends, file operations
LOW   — simple reads, additions, screenshots
"""

import json


HIGH_RISK_KEYWORDS = [
    "delete all",
    "remove all",
    "delete database",
    "drop database",
    "drop table",
    "format",
    "shutdown",
    "terminate",
    "wipe",
    "purge all",
]

MEDIUM_RISK_KEYWORDS = [
    "delete",
    "remove",
    "cancel",
    "send email",
    "send mail",
    "update",
    "modify",
    "change password",
    "reset",
    "override",
]


def detect_risk(instruction: str) -> dict:
    """
    Classify the risk level of a natural-language instruction.

    Args:
        instruction: Raw instruction string (any language — checked after lowercasing).

    Returns:
        {
            "risk_level":             "LOW" | "MEDIUM" | "HIGH",
            "requires_confirmation":  bool,
            "reason":                 str,
        }
    """
    text = instruction.lower()

    for keyword in HIGH_RISK_KEYWORDS:
        if keyword in text:
            return {
                "risk_level":            "HIGH",
                "requires_confirmation": True,
                "reason":                f"High-risk operation detected: '{keyword}'",
            }

    for keyword in MEDIUM_RISK_KEYWORDS:
        if keyword in text:
            return {
                "risk_level":            "MEDIUM",
                "requires_confirmation": True,
                "reason":                f"Potentially sensitive operation detected: '{keyword}'",
            }

    return {
        "risk_level":            "LOW",
        "requires_confirmation": False,
        "reason":                "No risky operation detected.",
    }


# ---------------------------------------------------------------------------
# Direct testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 50)
    print("Risk Detection")
    print("=" * 50)

    samples = [
        "Add Nikhil as customer with phone 9823456789",
        "Delete all customers",
        "Send email to manager",
        "Update product price to 599",
        "Drop database",
        "Download report",
    ]

    for s in samples:
        result = detect_risk(s)
        print(f"\n[{result['risk_level']:6}] {s}")
        print(f"         {result['reason']}")

    print("\n--- Interactive mode (type 'exit' to quit) ---")
    while True:
        instruction = input("\nEnter instruction: ").strip()
        if instruction.lower() in ("exit", "quit", ""):
            break
        print(json.dumps(detect_risk(instruction), indent=2))
