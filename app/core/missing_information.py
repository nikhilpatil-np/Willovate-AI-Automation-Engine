from entity_extractor import extract_entities

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