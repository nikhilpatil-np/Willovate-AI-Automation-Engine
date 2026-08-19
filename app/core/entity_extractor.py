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
        # price 599  (no separator)
        price_context = re.search(
            r"\bprice\b\s*"
            r"(?:is|to|at|=|:)?\s*"
            r"(\d{1,8})\b",
            text,
            re.IGNORECASE
        )

        if price_context:
            entities["price"] = price_context.group(1)


    # ---------------------------------
    # Product Name
    # ---------------------------------

    # Matches patterns like:
    #   "add product Laptop with price..."
    #   "add product named Laptop"
    #   "create product Laptop"
    #   "product Laptop with price"
    #   "Update product Laptop price"
    product_name_patterns = [
        # add/create/new product <Name>
        r"\b(?:add|create|new|insert)\s+(?:a\s+)?product\s+(?:named?\s+)?"
        r"([A-Za-z][A-Za-z0-9\s\-]{1,30}?)"
        r"(?:\s+(?:with|at|price|in|stock|category|and|$))",

        # product <Name> with/price/in
        r"\bproduct\s+(?:named?\s+)?"
        r"([A-Za-z][A-Za-z0-9\s\-]{1,30}?)"
        r"(?:\s+(?:with|at|price|in|stock|category|and))",

        # update/change product <Name>
        r"\b(?:update|change|modify|edit)\s+product\s+"
        r"([A-Za-z][A-Za-z0-9\s\-]{1,30}?)"
        r"(?:\s+(?:price|stock|category|with|to|and|$))",
    ]

    for pattern in product_name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            _invalid = {"a", "an", "the", "new", "product", "price", "stock",
                        "category", "electronics", "with", "at", "in", "and"}
            if candidate.lower() not in _invalid and len(candidate) > 1:
                entities["product_name"] = candidate.title()
                break

    # ---------------------------------
    # Category
    # ---------------------------------

    category_match = re.search(
        r"\bin\s+([A-Za-z][A-Za-z\s]{2,20}?)\s+category\b"
        r"|\bcategory\s*(?:is|:)?\s*([A-Za-z][A-Za-z\s]{2,20})\b",
        text, re.IGNORECASE
    )
    if category_match:
        entities["category"] = (category_match.group(1) or category_match.group(2)).strip().title()

    # ---------------------------------
    # Stock
    # ---------------------------------

    stock_match = re.search(
        r"\bstock\s*(?:is|:|=|of)?\s*(\d{1,6})\b"
        r"|\b(\d{1,6})\s+(?:units?|items?|pcs?|pieces?)\b",
        text, re.IGNORECASE
    )
    if stock_match:
        entities["stock"] = stock_match.group(1) or stock_match.group(2)

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
    # Handles: "add offer with text X", "add banner with text X",
    #          "add offer on Product with text X",
    #          "add sale with banner text X"
    banner = re.search(
        r"(?:banner|offer|discount|sale|deal|promo|announcement|notice)"
        r"(?:\s+on\s+[\w\s]+?)?"                  # optional "on <product>"
        r"\s+(?:with\s+)?(?:banner\s+)?text\s+"   # "text" or "banner text" keyword
        r"[\"']?(.+?)[\"']?\s*$",
        text, re.IGNORECASE
    )
    if not banner:
        # Fallback: "add banner <text>" without "text" keyword
        banner = re.search(
            r"(?:add\s+)?(?:banner|announcement|notice)\s+"
            r"(?:with\s+)?[\"']?(.+?)[\"']?\s*$",
            text, re.IGNORECASE
        )
    if banner:
        entities["banner_text"] = banner.group(1).strip()

    # ── Offer scope: all products or single product ────────────────────────
    # "add offer for all products"  → offer_scope = "all"
    # "add offer on Laptop"         → offer_scope = "single"
    # "add offer Summer Sale 50%"   → offer_scope = "all"  (no product named)
    if re.search(r"\b(?:offer|discount|sale|deal|promo)\b", text, re.IGNORECASE):
        # Check for explicit "all" scope
        if re.search(
            r"\b(?:all\s+products?|every\s+product|sab\s+products?)\b",
            text, re.IGNORECASE
        ):
            entities["offer_scope"] = "all"
        else:
            # Try to extract a specific product name for single-product offer
            single_match = re.search(
                r"\b(?:offer|discount|sale|deal|promo)\s+"
                r"(?:on|for|to|of)\s+"
                r"(?!all\b)([A-Za-z][A-Za-z0-9\s\-]{1,30}?)"
                r"(?:\s+(?:product|item|only|with|$)|$)",
                text, re.IGNORECASE
            )
            if single_match:
                candidate = single_match.group(1).strip()
                _skip = {"all", "every", "the", "a", "an", "my", "our", "products", "product"}
                if candidate.lower() not in _skip and len(candidate) > 1:
                    entities["offer_product"] = candidate.title()
                    entities["offer_scope"] = "single"
                else:
                    entities["offer_scope"] = "all"
            else:
                # Default: no specific product named → apply to all
                entities["offer_scope"] = "all"

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