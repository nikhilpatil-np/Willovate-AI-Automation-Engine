import json
import os
from entity_extractor import extract_entities


def generate_workflow(instruction):

    text = instruction.lower()
    entities = extract_entities(instruction)

    workflow = {
        "steps": []
    }

    # -----------------------------
    # Add Customer
    # -----------------------------
    if "customer" in text and ("add" in text or "create" in text):

        workflow["steps"].append({
            "action": "OPEN_PAGE",
            "target": "Customers"
        })

        workflow["steps"].append({
            "action": "CLICK",
            "target": "Add Customer"
        })

        if "name" in entities:
            workflow["steps"].append({
                "action": "ENTER_TEXT",
                "target": "Customer Name",
                "value": entities["name"]
            })

        if "phone" in entities:
            workflow["steps"].append({
                "action": "ENTER_TEXT",
                "target": "Phone Number",
                "value": entities["phone"]
            })

        workflow["steps"].append({
            "action": "CLICK",
            "target": "Save"
        })

    # -----------------------------
    # Download Report
    # -----------------------------
    elif "download" in text and "report" in text:

        workflow["steps"].append({
            "action": "OPEN_PAGE",
            "target": "Reports"
        })

        workflow["steps"].append({
            "action": "CLICK",
            "target": "Download"
        })

    # -----------------------------
    # Upload File
    # -----------------------------
    elif "upload" in text:

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

    else:

        workflow["steps"].append({
            "action": "UNKNOWN",
            "target": "Unsupported Instruction"
        })

    return workflow


if __name__ == "__main__":

    os.makedirs("outputs/workflow_generation", exist_ok=True)

    while True:

        instruction = input("\nEnter instruction (type exit): ")

        if instruction.lower() == "exit":
            break

        result = generate_workflow(instruction)

        print("\nGenerated Workflow:\n")
        print(json.dumps(result, indent=4))

        # Save workflow automatically
        with open(
            "outputs/workflow_generation/sample_workflow.json",
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(result, f, indent=4)

        print("\nWorkflow saved successfully!")