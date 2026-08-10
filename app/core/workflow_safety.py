import json

from workflow_generator import generate_workflow
from workflow_validator import validate_workflow
from risk_detector import detect_risk


def check_workflow_safety(instruction):

    # Generate workflow
    workflow = generate_workflow(instruction)

    # Validate workflow
    validation = validate_workflow(workflow)

    # Detect risk
    risk = detect_risk(instruction)

    return {
        "instruction": instruction,
        "workflow": workflow,
        "validation": validation,
        "risk": risk
    }


if __name__ == "__main__":

    print("=" * 50)
    print("Workflow Safety Checker")
    print("=" * 50)

    while True:

        instruction = input("\nEnter instruction (type exit): ")

        if instruction.lower() == "exit":
            break

        result = check_workflow_safety(instruction)

        print("\nFinal Result:")
        print(json.dumps(result, indent=4))