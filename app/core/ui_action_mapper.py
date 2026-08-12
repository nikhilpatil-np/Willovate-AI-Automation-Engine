import json

from action_predictor import predict_action
from ui_element_mapper import identify_ui_element


def map_instruction(instruction):

    actions = predict_action(instruction)

    results = []

    for action in actions:

        if action == "OPEN_PAGE":
            target = "Page"

        elif action == "CLICK":
            target = "Button"

        elif action == "ENTER_TEXT":
            target = "Input Field"

        elif action == "SELECT_OPTION":
            target = "Dropdown"

        elif action == "UPLOAD_FILE":
            target = "File Input"

        elif action == "DOWNLOAD_FILE":
            target = "Download Button"

        elif action == "READ_TABLE":
            target = "Table"

        elif action == "SCROLL":
            target = "Page"

        elif action == "SUBMIT":
            target = "Submit Button"

        elif action == "TAKE_SCREENSHOT":
            target = "Page"

        else:
            target = "Unknown"

        element = identify_ui_element(action, target)

        results.append({
            "action": action,
            "target": target,
            "element": element["element_type"]
        })

    return {
        "instruction": instruction,
        "steps": results
    }


if __name__ == "__main__":

    test_instructions = [
        "Click Add Customer",
        "Enter Rahul in customer name",
        "Select Maharashtra from dropdown",
        "Upload invoice.pdf",
        "Download today's report",
        "Read the customer table",
        "Scroll down",
        "Submit the form",
        "Take a screenshot"
    ]

    print("\nUI Action Mapping Results:\n")

    for instruction in test_instructions:

        result = map_instruction(instruction)

        print(json.dumps(result, indent=4))
        print("-" * 60)