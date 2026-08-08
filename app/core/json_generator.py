import json
import os
from workflow_generator import generate_workflow

if __name__ == "__main__":

    os.makedirs("outputs/json_generation", exist_ok=True)

    while True:

        instruction = input("\nEnter instruction (type exit): ")

        if instruction.lower() == "exit":
            break

        workflow = generate_workflow(instruction)

        print("\nGenerated JSON:\n")
        print(json.dumps(workflow, indent=4))

        with open(
            "outputs/json_generation/sample_json.json",
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(workflow, f, indent=4)

        print("\nJSON saved successfully!")