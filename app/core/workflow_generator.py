import json
from entity_extractor import extract_entities


def generate_workflow(instruction):

    text = instruction.lower()
    entities = extract_entities(instruction)

    workflow = {
        "steps": []
    }

    # ---------------------------------
    # Split instruction into task parts
    # ---------------------------------

    parts = (
        text.replace(" and then ", "|")
            .replace(" then ", "|")
            .replace(" and ", "|")
            .split("|")
    )

    # ---------------------------------
    # Process each task
    # ---------------------------------

    for part in parts:

        part = part.strip()

        # ---------------------------------
        # Open CRM
        # ---------------------------------

        if "crm" in part:

            workflow["steps"].append({
                "action": "OPEN_PAGE",
                "target": "CRM"
            })

        # ---------------------------------
        # Add Customer
        # ---------------------------------

        if "customer" in part and (
            "add" in part or
            "create" in part
        ):

            workflow["steps"].append({
                "action": "OPEN_PAGE",
                "target": "Customers"
            })

            workflow["steps"].append({
                "action": "CLICK",
                "target": "Add Customer"
            })

            # Customer Name
            if "name" in entities:

                workflow["steps"].append({
                    "action": "ENTER_TEXT",
                    "target": "Customer Name",
                    "value": entities["name"]
                })

            # Phone Number
            if "phone" in entities:

                workflow["steps"].append({
                    "action": "ENTER_TEXT",
                    "target": "Phone Number",
                    "value": entities["phone"]
                })

            # Add Customer
            workflow["steps"].append({
                "action": "CLICK",
                "target": "Add Customer"
            })

            # Verification information
            workflow["verify_name"] = entities.get(
                "name",
                ""
            )

            workflow["verify_phone"] = entities.get(
                "phone",
                ""
            )

            # Read customer table
            workflow["steps"].append({
                "action": "READ_TABLE",
                "target": "Customer List"
            })

        # ---------------------------------
        # Upload File
        # ---------------------------------

        if "upload" in part:

            workflow["steps"].append({
                "action": "OPEN_PAGE",
                "target": "Upload"
            })

            workflow["steps"].append({
                "action": "CLICK",
                "target": "Upload File"
            })

            if "file" in entities:

                workflow["steps"].append({
                    "action": "UPLOAD_FILE",
                    "target": entities["file"]
                })

        # ---------------------------------
        # Download Report
        # ---------------------------------

        if "download" in part and "report" in part:

            workflow["steps"].append({
                "action": "OPEN_PAGE",
                "target": "Reports"
            })

            workflow["steps"].append({
                "action": "CLICK",
                "target": "Download"
            })

        # ---------------------------------
        # Click Save Button
        # ---------------------------------

        if (
            "click" in part
            and "save" in part
            and "customer" not in part
        ):

            workflow["steps"].append({
                "action": "CLICK",
                "target": "Save"
            })

    # ---------------------------------
    # Unknown Instruction
    # ---------------------------------

    if not workflow["steps"]:

        workflow["steps"].append({
            "action": "UNKNOWN",
            "target": "Unsupported Instruction"
        })

    return workflow


# ---------------------------------
# Direct Testing
# ---------------------------------

if __name__ == "__main__":

    while True:

        instruction = input(
            "\nEnter instruction (type exit): "
        )

        if instruction.lower() == "exit":
            break

        result = generate_workflow(instruction)

        print(
            "\nGenerated Multi-Step Workflow:\n"
        )

        print(
            json.dumps(
                result,
                indent=4
            )
        )