import json


def identify_ui_element(action, target):
    """
    Identify the UI element required for an automation action.
    """

    action = action.upper()
    target = target.lower()

    # CLICK action
    if action == "CLICK":
        return {
            "element_type": "BUTTON",
            "target": target
        }

    # ENTER TEXT action
    elif action == "ENTER_TEXT":
        return {
            "element_type": "INPUT",
            "target": target
        }

    # SELECT OPTION action
    elif action == "SELECT_OPTION":
        return {
            "element_type": "DROPDOWN",
            "target": target
        }

    # UPLOAD FILE action
    elif action == "UPLOAD_FILE":
        return {
            "element_type": "FILE_INPUT",
            "target": target
        }

    # READ TABLE action
    elif action == "READ_TABLE":
        return {
            "element_type": "TABLE",
            "target": target
        }

    # OPEN PAGE action
    elif action == "OPEN_PAGE":
        return {
            "element_type": "PAGE",
            "target": target
        }

    # DOWNLOAD FILE action
    elif action == "DOWNLOAD_FILE":
        return {
            "element_type": "BUTTON",
            "target": target
        }

    # SCROLL action
    elif action == "SCROLL":
        return {
            "element_type": "PAGE",
            "target": target
        }

    # SUBMIT action
    elif action == "SUBMIT":
        return {
            "element_type": "BUTTON",
            "target": target
        }

    # TAKE SCREENSHOT action
    elif action == "TAKE_SCREENSHOT":
        return {
            "element_type": "PAGE",
            "target": target
        }

    # READ TEXT action
    elif action == "READ_TEXT":
        return {
            "element_type": "TEXT",
            "target": target
        }

    # Unknown action
    else:
        return {
            "element_type": "UNKNOWN",
            "target": target
        }


def map_workflow_elements(workflow):

    mapped_steps = []

    for step in workflow.get("steps", []):

        action = step.get("action", "")
        target = step.get("target", "")

        element = identify_ui_element(action, target)

        mapped_step = {
            "action": action,
            "target": target,
            "element": element["element_type"]
        }

        if "value" in step:
            mapped_step["value"] = step["value"]

        mapped_steps.append(mapped_step)

    return {
        "steps": mapped_steps
    }


if __name__ == "__main__":

    test_workflow = {
        "steps": [
            {
                "action": "OPEN_PAGE",
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
                "action": "ENTER_TEXT",
                "target": "Phone Number",
                "value": "9876543210"
            },
            {
                "action": "CLICK",
                "target": "Save"
            },
            {
                "action": "DOWNLOAD_FILE",
                "target": "Report"
            },
            {
                "action": "SCROLL",
                "target": "Page"
            },
            {
                "action": "SUBMIT",
                "target": "Form"
            },
            {
                "action": "TAKE_SCREENSHOT",
                "target": "Page"
            }
        ]
    }

    result = map_workflow_elements(test_workflow)

    print("\nUI Element Mapping:\n")
    print(json.dumps(result, indent=4))