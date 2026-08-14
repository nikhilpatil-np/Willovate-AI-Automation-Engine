import json
import os

from workflow_generator import generate_workflow


OUTPUT_PATH = (
    "outputs/json_generation/sample_json.json"
)


if __name__ == "__main__":

    # Create output directory
    os.makedirs(
        "outputs/json_generation",
        exist_ok=True
    )

    while True:

        instruction = input(
            "\nEnter instruction (type exit): "
        )

        if instruction.lower() == "exit":
            break

        # Generate workflow
        workflow = generate_workflow(
            instruction
        )

        print("\nGenerated JSON:\n")

        print(
            json.dumps(
                workflow,
                indent=4
            )
        )

        # Save workflow
        with open(
            OUTPUT_PATH,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                workflow,
                f,
                indent=4
            )

        print(
            "\nJSON saved successfully!"
        )

        print(
            f"Location: {OUTPUT_PATH}"
        )