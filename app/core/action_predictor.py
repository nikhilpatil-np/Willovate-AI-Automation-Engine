import json


def predict_action(instruction):

    text = instruction.lower()

    actions = []

    # Open page
    if "open" in text:
        actions.append("OPEN_PAGE")

    # Click
    if "click" in text:
        actions.append("CLICK")

    # Add / Enter customer information
    if any(word in text for word in ["add", "enter", "type", "fill"]):
        actions.append("ENTER_TEXT")

    # Select
    if any(word in text for word in ["select", "choose", "dropdown"]):
        actions.append("SELECT_OPTION")

    # Upload
    if "upload" in text:
        actions.append("UPLOAD_FILE")

    # Download
    if "download" in text:
        actions.append("DOWNLOAD_FILE")

    # Read table
    if "table" in text or "read records" in text:
        actions.append("READ_TABLE")

    # Scroll
    if "scroll" in text:
        actions.append("SCROLL")

    # Submit
    if "submit" in text:
        actions.append("SUBMIT")

    # Screenshot
    if "screenshot" in text:
        actions.append("TAKE_SCREENSHOT")

    if not actions:
        actions.append("UNKNOWN")

    return actions


if __name__ == "__main__":

    test_instructions = [
        "Open the customer page",
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

    print("\nAction Prediction Results:\n")

    for instruction in test_instructions:

        result = predict_action(instruction)

        print("Instruction:", instruction)
        print("Predicted Actions:", result)
        print("-" * 60)