import json

from workflow_generator import generate_workflow
from ui_element_mapper import identify_ui_element


def map_workflow_to_ui(workflow):

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

    instruction = input("\nEnter instruction: ")

    workflow = generate_workflow(instruction)

    result = map_workflow_to_ui(workflow)

    print("\nFinal UI-Aware Workflow:\n")

    print(json.dumps(result, indent=4))