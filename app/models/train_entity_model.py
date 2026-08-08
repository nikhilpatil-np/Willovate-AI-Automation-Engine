import re

def extract_entities(text):
    entities = {}

    # Phone number
    phone = re.search(r"\b\d{10}\b", text)
    if phone:
        entities["phone"] = phone.group()

    # Email
    email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if email:
        entities["email"] = email.group()

    # Price
    price = re.search(
        r"(?:price\s*(?:to|is|=)?\s*|₹|Rs\.?\s*|INR\s*)(\d+)",
        text,
        re.IGNORECASE
    )
    if price:
        entities["price"] = price.group(1)

    # File name
    file = re.search(
        r"\b[\w\-.]+\.(?:pdf|csv|xlsx|jpg|png|zip)\b",
        text,
        re.IGNORECASE
    )
    if file:
        entities["file"] = file.group()

    # Name (basic pattern)
    name = re.search(r"(?:add|create|register|delete|employee|customer)\s+([A-Z][a-z]+)", text, re.IGNORECASE)
    if name:
        entities["name"] = name.group(1)

    return entities


if __name__ == "__main__":
    while True:
        text = input("\nEnter instruction (type exit): ")

        if text.lower() == "exit":
            break

        print(extract_entities(text))