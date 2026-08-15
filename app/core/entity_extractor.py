import re


def extract_entities(text):
    entities = {}

    # ---------------------------------
    # Phone Number
    # ---------------------------------

    phone = re.search(r"\b\d{10}\b", text)

    if phone:
        entities["phone"] = phone.group()


    # ---------------------------------
    # Email
    # ---------------------------------

    email = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    if email:
        entities["email"] = email.group()


    # ---------------------------------
    # Price
    # ---------------------------------

    # ₹599 / Rs 599 / INR 599
    price = re.search(
        r"(?:₹|Rs\.?|INR)\s*(\d{1,6})\b",
        text,
        re.IGNORECASE
    )

    if price:
        entities["price"] = price.group(1)

    else:
        # price is 599
        # price: 599
        # price = 599
        # price to 599
        price_context = re.search(
            r"\bprice\b\s*"
            r"(?:is|to|at|=|:)?\s*"
            r"(\d{1,6})\b",
            text,
            re.IGNORECASE
        )

        if price_context:
            entities["price"] = price_context.group(1)


    # ---------------------------------
    # File Name
    # ---------------------------------

    file = re.search(
        r"\b[\w\-]+\."
        r"(pdf|csv|xlsx|jpg|png|zip)\b",
        text,
        re.IGNORECASE
    )

    if file:
        entities["file"] = file.group()


    # ---------------------------------
    # Name
    # ---------------------------------

    # Capture the name between the command verb and a known separator.
    #
    # Examples:
    #   Add Rahul as customer           → Rahul
    #   Add Rahul with phone number     → Rahul
    #   Add Pankaj Koche as customer    → Pankaj Koche
    #   Create Rahul as employee        → Rahul
    #   Delete customer Rahul           → Rahul
    #
    # Strategy: match one or two capitalised words that appear
    # immediately after the verb and stop before any separator keyword.
    # Using a negative lookahead inside the capture group ensures
    # separator words ("as", "with", "customer", …) are never included.

    _sep = r"(?:as|with|to|and|for|in|customer|employee|product|file|report)\b"

    name_patterns = [

        # add / create / register  <Name>  as|with|to|customer|employee
        r"\b(?:add|create|register)\s+"
        r"((?:(?!" + _sep + r")[A-Za-z]+)(?:\s+(?:(?!" + _sep + r")[A-Za-z]+)){0,2})"
        r"\s+(?=" + _sep + r")",

        # delete / remove  customer|employee  <Name>
        r"\b(?:delete|remove)\s+(?:customer|employee)\s+"
        r"([A-Za-z]+(?:\s+[A-Za-z]+){0,1})\b",

        # delete / remove  <Name>  customer|employee
        r"\b(?:delete|remove)\s+"
        r"((?:(?!" + _sep + r")[A-Za-z]+)(?:\s+(?:(?!" + _sep + r")[A-Za-z]+)){0,1})"
        r"\s+(?=customer\b|employee\b)",
    ]

    for pattern in name_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            candidate = match.group(1).strip()

            invalid_names = {
                "a", "an", "the", "new",
                "customer", "employee", "product", "file", "report",
            }

            if candidate.lower() not in invalid_names:
                entities["name"] = candidate
                break


    return entities


# ---------------------------------
# Testing
# ---------------------------------

if __name__ == "__main__":

    test_messages = [

        "Create a customer",

        "Add Rahul as customer",

        "Add Rahul with phone number 9876543210",

        "Add Pankaj Koche with phone number 9876543210",

        "Add Rahul Sharma as customer",

        "Create Rahul as employee",

        "Product price is ₹599",

        "Change product price to 599",

        "Upload report.xlsx"
    ]


    for text in test_messages:

        print("\nInstruction:")
        print(text)

        print("\nEntities:")

        print(extract_entities(text))