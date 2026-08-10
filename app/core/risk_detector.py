import json


HIGH_RISK_KEYWORDS = [
    "delete all",
    "remove all",
    "delete database",
    "drop database",
    "format",
    "shutdown",
    "terminate",
]

MEDIUM_RISK_KEYWORDS = [
    "delete",
    "remove",
    "cancel",
    "send email",
    "update",
]


def detect_risk(instruction):

    text = instruction.lower()

    # Check HIGH risk
    for keyword in HIGH_RISK_KEYWORDS:
        if keyword in text:
            return {
                "risk_level": "HIGH",
                "requires_confirmation": True,
                "reason": f"High-risk operation detected: {keyword}"
            }

    # Check MEDIUM risk
    for keyword in MEDIUM_RISK_KEYWORDS:
        if keyword in text:
            return {
                "risk_level": "MEDIUM",
                "requires_confirmation": True,
                "reason": f"Potentially sensitive operation detected: {keyword}"
            }

    # Default LOW risk
    return {
        "risk_level": "LOW",
        "requires_confirmation": False,
        "reason": "No risky operation detected."
    }


if __name__ == "__main__":

    print("=" * 50)
    print("Risk Detection")
    print("=" * 50)

    while True:

        instruction = input("\nEnter instruction (type exit): ")

        if instruction.lower() == "exit":
            break

        result = detect_risk(instruction)

        print("\nRisk Result:")
        print(json.dumps(result, indent=4))