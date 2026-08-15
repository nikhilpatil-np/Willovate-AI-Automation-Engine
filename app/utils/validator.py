import json
from pathlib import Path
import jsonschema

SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "workflow.schema.json"


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


_SCHEMA = load_schema()


def validate_workflow(workflow: dict):
    """Validate workflow dict against JSON schema.

    Returns (True, None) on success or (False, error_message) on failure.
    """
    try:
        jsonschema.validate(instance=workflow, schema=_SCHEMA)
        return True, None
    except jsonschema.ValidationError as ex:
        return False, str(ex)


if __name__ == "__main__":
    ok, err = validate_workflow({"steps": [{"action": "OPEN_PAGE", "target": "CRM"}]})
    print(ok, err)
