import json


VALID_ACTIONS = {
    "OPEN_PAGE",
    "CLICK",
    "ENTER_TEXT",
    "UPLOAD_FILE",
    "DOWNLOAD_FILE",
    "SEND_EMAIL"
}


def validate_workflow(workflow):

    errors = []

    # Check workflow format
    if not isinstance(workflow, dict):
        errors.append("Workflow must be a dictionary.")
        return {
            "valid": False,
            "errors": errors
        }

    # Check steps
    if "steps" not in workflow:
        errors.append("Workflow does not contain steps.")
        return {
            "valid": False,
            "errors": errors
        }

    steps = workflow["steps"]

    if not isinstance(steps, list):
        errors.append("Steps must be a list.")
        return {
            "valid": False,
            "errors": errors
        }

    if len(steps) == 0:
        errors.append("Workflow contains no steps.")

    # Validate each step
    for index, step in enumerate(steps):

        if not isinstance(step, dict):
            errors.append(
                f"Step {index + 1}: Invalid step format."
            )
            continue

        if "action" not in step:
            errors.append(
                f"Step {index + 1}: Missing action."
            )
            continue

        action = step["action"]

        if action not in VALID_ACTIONS:
            errors.append(
                f"Step {index + 1}: Invalid action '{action}'."
            )

        if "target" not in step:
            errors.append(
                f"Step {index + 1}: Missing target."
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


if __name__ == "__main__":

    print("=" * 50)
    print("Workflow Validation")
    print("=" * 50)

    test_workflow = {
        "steps": [
            {
                "action": "UNKNOWN_ACTION",
                "target": "Customers"
            },
            {
                "action": "CLICK",
                "target": "Add Customer"
            },
            {
                "action": "ENTER_TEXT",
                "target": "Customer Name",
                "value": "Rahul"
            },
            {
                "action": "CLICK",
                "target": "Save"
            }
        ]
    }

    result = validate_workflow(test_workflow)

    print("\nValidation Result:")
    print(json.dumps(result, indent=4))