def detect_missing_information(intent: str, entities: dict):
    """Return list of missing entity keys required for the given intent."""

    required = []

    if intent == "ADD_CUSTOMER":
        required = ["name", "phone"]

    elif intent == "ADD_PRODUCT":
        required = ["product_name", "price"]

    elif intent == "UPDATE_PRODUCT":
        required = ["product_name", "price"]

    elif intent == "UPLOAD_FILE":
        required = ["file"]

    elif intent == "SEND_EMAIL":
        required = ["email", "subject"]

    elif intent in ("ADD_OFFER", "add_offer"):
        # Must have something to display as the offer text
        if not entities.get("banner_text"):
            required = ["banner_text"]

    elif intent in ("CHANGE_WEB", "change_web"):
        # Need at least an element or a color or banner_text or logo
        has_target = any(k in entities for k in
                         ("element", "color", "logo", "banner_text", "text"))
        if not has_target:
            required = ["element"]

    missing = [k for k in required if k not in entities or not entities.get(k)]

    return missing
from app.core.entity_extractor import extract_entities

def check_missing_information(text):

    entities = extract_entities(text)

    missing = []

    text = text.lower()

    # Customer
    if "customer" in text:

        if "name" not in entities:
            missing.append("Customer Name")

        if "phone" not in entities:
            missing.append("Phone Number")

    # Employee
    elif "employee" in text:

        if "name" not in entities:
            missing.append("Employee Name")

    # Email
    elif "email" in text:

        if "email" not in entities:
            missing.append("Email Address")

    # Upload
    elif "upload" in text:

        if "file" not in entities:
            missing.append("File Name")

    # Product
    elif "product" in text:

        if "price" not in entities:
            missing.append("Product Price")

    return missing


if __name__ == "__main__":

    print("=" * 50)
    print("Missing Information Detection")
    print("=" * 50)

    while True:

        instruction = input("\nEnter instruction (type exit): ")

        if instruction.lower() == "exit":
            break

        missing = check_missing_information(instruction)

        if len(missing) == 0:
            print("\nAll required information is available.")
        else:
            print("\nMissing Information:")
            for item in missing:
                print("-", item)