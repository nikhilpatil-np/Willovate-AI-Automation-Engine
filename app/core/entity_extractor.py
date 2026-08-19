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

    _sep = r"(?:as|with|to|and|for|in|email|phone|number|customer|employee|product|file|report)\b"

    name_patterns = [

        # name at end: "add customer named nikhil" / "add customer as nikhil"
        # handles normalized Hinglish: jodo customer as nikhil → add customer named nikhil
        r"\b(?:add|create|register)\s+(?:customer|client|employee|user)\s+"
        r"(?:named?|as)\s+"
        r"([A-Za-z]+(?:\s+[A-Za-z]+){0,1})\s*(?:phone|email|with|$)",

        # add / create / register  <Name>  as|with|to|customer|employee
        r"\b(?:add|create|register)\s+"
        r"((?:(?!" + _sep + r")[A-Za-z]+)(?:\s+(?:(?!" + _sep + r")[A-Za-z]+)){0,2})"
        r"\s+(?=" + _sep + r")",

        # add / create / register customer/client <Name>
        r"\b(?:add|create|register)\s+(?:customer|client|employee|user)\s+"
        r"((?:(?!" + _sep + r")[A-Za-z]+)(?:\s+(?:(?!" + _sep + r")[A-Za-z]+)){0,1})\b",

        # Hinglish: <Name> naam ka  (e.g. "Rahul naam ka customer jod do")
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,1})\s+naam\b",

        # Hinglish: <Name> ko customer / <Name> ka customer
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,1})\s+(?:ko|ka|ki)\s+(?:customer|employee|client)\b",

        # delete / remove  customer|employee  <Name>
        r"\b(?:delete|remove)\s+(?:customer|employee|client|staff)\s+"
        r"([A-Za-z]+(?:\s+[A-Za-z]+){0,1})\b",

        # delete / remove  <Name>  customer|employee
        r"\b(?:delete|remove)\s+"
        r"((?:(?!" + _sep + r")[A-Za-z]+)(?:\s+(?:(?!" + _sep + r")[A-Za-z]+)){0,1})"
        r"\s+(?=customer\b|employee\b|client\b|staff\b)",
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
                "a", "an", "the", "new", "it",
                "customer", "employee", "product", "file", "report",
                "email", "phone", "number", "client", "user", "staff",
                "named", "name", "karo", "kar", "do", "ka", "ki", "ko",
                "jodo", "jod", "banao", "bana", "add", "create",
            }

            if candidate.lower() not in invalid_names:
                entities["name"] = candidate.title() if candidate.islower() else candidate
                break

    # If name still not found on original, try on normalized text
    if "name" not in entities:
        from app.core.language_normalizer import normalize
        norm_text = normalize(text)
        for pattern in name_patterns:
            match = re.search(pattern, norm_text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                invalid_names = {
                    "a", "an", "the", "new", "it",
                    "customer", "employee", "product", "file", "report",
                    "email", "phone", "number", "client", "user", "staff",
                    "named", "name", "karo", "kar", "do", "ka", "ki", "ko",
                    "jodo", "jod", "banao", "bana", "add", "create",
                }
                if candidate.lower() not in invalid_names:
                    entities["name"] = candidate.title() if candidate.islower() else candidate
                    break


    return entities


# ---------------------------------
# Web Change Entities (color, logo, banner, element)
# ---------------------------------

def extract_web_entities(text: str) -> dict:
    """
    Extract entities specific to web change instructions.

    Examples:
      "Change logo to willovate.png"        → {logo: willovate.png}
      "Change header color to blue"         → {element: header, color: blue}
      "Add banner with text 50% off today"  → {banner_text: 50% off today}
      "Change background to #ff0000"        → {color: #ff0000}
      "Change sidebar color to dark green"  → {element: sidebar, color: dark green}
      "Change title to Welcome to CRM"      → {element: title, text: Welcome to CRM}
    """
    entities = {}

    t = text.lower()

    # ── Logo ──────────────────────────────────────────────────────────────
    logo = re.search(
        r"logo\s+(?:to|with|as|=)?\s*([\w\-]+\.(?:png|jpg|jpeg|svg|gif|ico))",
        text, re.IGNORECASE
    )
    if logo:
        entities["logo"] = logo.group(1)

    # ── Color (hex or named) ───────────────────────────────────────────────
    color = re.search(
        r"(?:color|colour|background|bg)\s+(?:to|as|=)?\s*"
        r"(#[0-9a-fA-F]{3,6}|[a-z][\w\s]{2,20}?)(?:\s*$|\s+(?:and|,))",
        text, re.IGNORECASE
    )
    if not color:
        color = re.search(
            r"(?:to|as)\s+(#[0-9a-fA-F]{3,6}|"
            r"red|blue|green|yellow|orange|purple|pink|white|black|gray|grey|"
            r"dark\s+\w+|light\s+\w+|navy|teal|maroon|cyan|magenta)\b",
            text, re.IGNORECASE
        )
    if color:
        entities["color"] = color.group(1).strip()

    # ── Banner / Offer text ────────────────────────────────────────────────
    banner = re.search(
        r"(?:banner|offer|announcement|notice)\s+(?:with\s+)?(?:text\s+)?[\"']?(.+?)[\"']?\s*$",
        text, re.IGNORECASE
    )
    if banner:
        entities["banner_text"] = banner.group(1).strip()

    # ── Title / Header text ────────────────────────────────────────────────
    title = re.search(
        r"(?:title|heading|header\s+text)\s+(?:to|as|with)?\s*[\"']?(.+?)[\"']?\s*$",
        text, re.IGNORECASE
    )
    if title:
        entities["text"] = title.group(1).strip()

    # ── Element target ─────────────────────────────────────────────────────
    for elem in ("logo", "header", "sidebar", "topbar", "footer",
                 "background", "title", "button", "navbar"):
        if elem in t:
            entities["element"] = elem
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