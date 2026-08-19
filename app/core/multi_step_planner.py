"""
Multi-Step Planner
==================
Converts a natural-language instruction into a clean, ordered workflow JSON.

The generated workflow matches the actual CRM HTML element IDs and button
names so the browser runner can execute every step without guessing.

Example output for:
  "Open the CRM, add Pankaj Koche as a customer with phone number 9876543210,
   save the record and verify that the customer appears in the table."

{
  "intent": "add_customer",
  "steps": [
    {"action": "OPEN_PAGE",   "target": "customers"},
    {"action": "ENTER_TEXT",  "target": "customer-name",  "value": "Pankaj Koche"},
    {"action": "ENTER_TEXT",  "target": "phone-number",   "value": "9876543210"},
    {"action": "CLICK",       "target": "add-customer"},
    {"action": "CLICK",       "target": "save"},
    {"action": "READ_TABLE",  "target": "customer-table"},
    {"action": "VERIFY_RECORD", "target": "customer-table", "value": "Pankaj Koche"}
  ]
}
"""

import re
from app.core.entity_extractor import extract_entities, extract_web_entities


# ---------------------------------------------------------------------------
# Split patterns — only strong connectors, not plain "and" / ","
# ---------------------------------------------------------------------------

SPLIT_PATTERNS = [
    r"\s+and then\s+",
    r"\s+phir\s+",
    r"\s+fir\s+",
    r"\s+uske baad\s+",
    r"\s+then\s+",
    r",\s*and\s+",
]

# ---------------------------------------------------------------------------
# Intent classifiers
# ---------------------------------------------------------------------------

def _intent(text: str) -> str:
    t = text.lower()
    # Offer / discount / sale banner — check before generic change_web
    if any(k in t for k in (
        "add offer", "add discount", "add sale", "add deal", "add promo",
        "offer add", "discount add", "sale add",
        "offer karo", "offer lagao", "sale lagao",
    )):
        return "add_offer"
    # Web change check first — before update_record which also uses "change"
    if any(k in t for k in (
        "change logo", "update logo", "set logo", "change the logo", "update the logo",
        "change header", "set header", "change header color", "set header color",
        "change header background", "set header background",
        "change background", "set background", "change bg", "set bg",
        "change sidebar", "set sidebar", "sidebar color", "sidebar background",
        "add banner", "show banner", "create banner",
        "change title", "set title",
        "change button color", "set button color",
        "change theme", "set theme",
        "change color", "set color",
        "logo badlo", "banner add", "color change", "rang badlo",
        "header badlo", "background badlo", "sidebar badlo",
    )) or re.search(r"\blogo\b", t):
        return "change_web"
    if any(k in t for k in ("add", "create", "register", "jod", "bana", "जोड़", "बना")):
        if any(k in t for k in ("customer", "ग्राहक", "कस्टमर", "client")):
            return "add_customer"
        if any(k in t for k in ("employee", "staff", "कर्मचारी")):
            return "add_employee"
        if any(k in t for k in ("product", "item", "प्रोडक्ट")):
            return "add_product"
    if any(k in t for k in ("delete", "remove", "hata", "हटाओ", "hatao")):
        if any(k in t for k in ("product", "products", "item")):
            return "delete_product"
        if any(k in t for k in ("employee", "employees", "staff")):
            return "delete_employee"
        return "delete_customer"
    if any(k in t for k in ("update", "modify", "change", "edit")):
        return "update_record"
    if any(k in t for k in ("download", "report", "csv")):
        return "download_report"
    if any(k in t for k in ("upload",)):
        return "upload_file"
    if any(k in t for k in ("send email", "send mail", "email bhejo")):
        return "send_email"
    if any(k in t for k in ("screenshot",)):
        return "take_screenshot"
    return "unknown"


def _is_customer_add(text: str) -> bool:
    t = text.lower()
    has_noun = any(k in t for k in ("customer", "ग्राहक", "कस्टमर", "client"))
    has_verb = any(k in t for k in ("add", "create", "register", "jod", "bana", "जोड़", "बना"))
    return has_noun and has_verb


def _is_employee_add(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ("employee", "staff", "कर्मचारी")) and \
           any(k in t for k in ("add", "create", "register"))


# ---------------------------------------------------------------------------
# Step builder for one sub-task
# ---------------------------------------------------------------------------

def _steps_for(subtask: str, entities: dict) -> list:
    t    = subtask.lower().strip()
    steps = []

    # ── OPEN CRM / navigate to page ────────────────────────────────────────
    if re.search(r"\bopen\s+(?:the\s+)?crm\b", t):
        steps.append({"action": "OPEN_PAGE", "target": "customers"})
        # don't return — same sentence may have "add customer" etc.

    # ── ADD CUSTOMER ────────────────────────────────────────────────────────
    if _is_customer_add(t):
        # Only add OPEN_PAGE if not already added above
        if not any(s["action"] == "OPEN_PAGE" for s in steps):
            steps.append({"action": "OPEN_PAGE", "target": "customers"})

        if "name" in entities:
            steps.append({
                "action": "ENTER_TEXT",
                "target": "customer-name",
                "value":  entities["name"],
            })
        if "phone" in entities:
            steps.append({
                "action": "ENTER_TEXT",
                "target": "phone-number",
                "value":  entities["phone"],
            })
        if "email" in entities:
            steps.append({
                "action": "ENTER_TEXT",
                "target": "customer-email",
                "value":  entities["email"],
            })

        steps.append({"action": "CLICK", "target": "add-customer"})

        # Always read the table after adding so result is visible
        steps.append({"action": "READ_TABLE",    "target": "customer-table"})
        if "name" in entities:
            steps.append({
                "action": "VERIFY_RECORD",
                "target": "customer-table",
                "value":  entities["name"],
            })

    # ── ADD PRODUCT ─────────────────────────────────────────────────────────
    elif any(k in t for k in ("add product", "create product", "new product",
                               "insert product", "product add", "product jod",
                               "naya product", "product banao", "product daalo")):
        if not any(s["action"] == "OPEN_PAGE" for s in steps):
            steps.append({"action": "OPEN_PAGE", "target": "products"})

        if "product_name" in entities:
            steps.append({
                "action": "ENTER_TEXT",
                "target": "product-name",
                "value":  entities["product_name"],
            })
        if "price" in entities:
            steps.append({
                "action": "ENTER_TEXT",
                "target": "product-price",
                "value":  entities["price"],
            })
        if "category" in entities:
            steps.append({
                "action": "ENTER_TEXT",
                "target": "product-category",
                "value":  entities["category"],
            })
        if "stock" in entities:
            steps.append({
                "action": "ENTER_TEXT",
                "target": "product-stock",
                "value":  entities["stock"],
            })

        steps.append({"action": "CLICK", "target": "add-product"})
        steps.append({"action": "READ_TABLE", "target": "product-table"})
        if "product_name" in entities:
            steps.append({
                "action": "VERIFY_RECORD",
                "target": "product-table",
                "value":  entities["product_name"],
            })

    # ── ADD EMPLOYEE ────────────────────────────────────────────────────────
    elif _is_employee_add(t):
        if not any(s["action"] == "OPEN_PAGE" for s in steps):
            steps.append({"action": "OPEN_PAGE", "target": "employees"})

        if "name" in entities:
            steps.append({
                "action": "ENTER_TEXT",
                "target": "employee-name",
                "value":  entities["name"],
            })
        if "phone" in entities:
            steps.append({
                "action": "ENTER_TEXT",
                "target": "employee-phone",
                "value":  entities["phone"],
            })

        steps.append({"action": "CLICK", "target": "add-employee"})

    # ── SAVE ────────────────────────────────────────────────────────────────
    if re.search(r"\bsave\b|save\s*kar|सेव", t):
        # Insert SAVE before the READ_TABLE we already added
        # Find position of READ_TABLE and insert before it
        rt_idx = next((i for i, s in enumerate(steps) if s["action"] == "READ_TABLE"), len(steps))
        steps.insert(rt_idx, {"action": "CLICK", "target": "save"})

    # ── EXTRA VERIFY / READ TABLE (only if not already present) ─────────────
    if re.search(r"\bverif|\bcheck|\bappear|\btable\b|\blist\b", t):
        if not any(s["action"] == "READ_TABLE" for s in steps):
            steps.append({"action": "READ_TABLE",    "target": "customer-table"})
            if "name" in entities:
                steps.append({
                    "action": "VERIFY_RECORD",
                    "target": "customer-table",
                    "value":  entities["name"],
                })

    # ── DOWNLOAD REPORT ─────────────────────────────────────────────────────
    if "download" in t and ("report" in t or "csv" in t or "excel" in t):
        steps.append({"action": "OPEN_PAGE", "target": "reports"})

        # Detect which report type the user asked for
        is_today   = any(k in t for k in ("today", "aaj", "आज", "today's", "todays"))
        is_product = any(k in t for k in ("product", "products", "item", "items"))
        is_customer = any(k in t for k in ("customer", "customers", "client"))

        if is_today:
            report_target = "download-today-report"
        elif is_product:
            report_target = "download-product-report"
        elif is_customer:
            report_target = "download-customer-report"
        else:
            # Default to customer report when unspecified
            report_target = "download-customer-report"

        steps.append({"action": "CLICK", "target": report_target})

    # ── UPLOAD FILE ─────────────────────────────────────────────────────────
    if "upload" in t:
        steps.append({"action": "OPEN_PAGE",   "target": "upload"})
        if "file" in entities:
            steps.append({"action": "UPLOAD_FILE", "target": entities["file"]})

    # ── SEND EMAIL ──────────────────────────────────────────────────────────
    if re.search(r"send\s+(?:an?\s+)?(?:email|mail)|email\s*bhejo", t):
        recipient = entities.get("email") or "manager"
        steps.append({"action": "SEND_EMAIL", "target": recipient})

    # ── SCREENSHOT ──────────────────────────────────────────────────────────
    if re.search(r"screenshot|स्क्रीनशॉट", t):
        steps.append({"action": "TAKE_SCREENSHOT", "target": "current-page"})

    # ── SCROLL ──────────────────────────────────────────────────────────────
    if re.search(r"\bscroll\b", t):
        steps.append({"action": "SCROLL", "target": "down" if "down" in t else "up"})

    # ── WAIT ────────────────────────────────────────────────────────────────
    m = re.search(r"\bwait\s+(?:for\s+)?(\d+)\s*(?:sec|second)", t)
    if m:
        steps.append({"action": "WAIT", "target": m.group(1) + "s"})

    # ── WEB CHANGES ─────────────────────────────────────────────────────────
    # Change logo
    if re.search(
        r"\b(?:change|update|set)\s+(?:the\s+)?logo\b"
        r"|\blogo\s+(?:change|update|badlo)\b",
        t,
    ):
        logo = entities.get("logo", "")
        steps.append({
            "action": "CHANGE_LOGO",
            "target": "sidebar-logo",
            "value":  logo,
        })

    # Change sidebar color/background — must come before the generic color block
    # so "change sidebar color to blue" only generates ONE step, not two.
    elif re.search(
        r"\b(?:change|update|set)\s+sidebar\b"
        r"|\bsidebar\s+(?:color|background|bg|badlo)\b",
        t,
    ):
        color = entities.get("color", "")
        steps.append({
            "action": "CHANGE_STYLE",
            "target": "sidebar",
            "value":  color,
        })

    # Change header/topbar color or background
    elif re.search(
        r"\b(?:change|update|set)\s+header\b"
        r"|\bheader\s+(?:color|background|bg|badlo)\b"
        r"|\b(?:change|update|set)\s+topbar\b",
        t,
    ):
        color = entities.get("color", "")
        steps.append({
            "action": "CHANGE_STYLE",
            "target": "header",
            "value":  color,
        })

    # Change body/page background or generic color/theme
    elif re.search(
        r"\b(?:change|update|set)\s+(?:the\s+)?(?:background|bg|theme|color)\b"
        r"|\bcolor\s+(?:change|badlo)\b"
        r"|\bbackground\s+(?:change|badlo)\b"
        r"|\brang\s+badlo\b",
        t,
    ):
        element = entities.get("element", "body")
        color   = entities.get("color", "")
        steps.append({
            "action": "CHANGE_STYLE",
            "target": element,
            "value":  color,
        })

    # Add offer / discount / sale — product-aware banner (checks DB first)
    elif re.search(
        r"\badd\s+(?:offer|discount|sale|deal|promo)\b"
        r"|\boffer\s+(?:add|lagao|karo)\b|\bsale\s+add\b",
        t,
    ):
        banner_text   = entities.get("banner_text", "")
        offer_scope   = entities.get("offer_scope", "all")
        offer_product = entities.get("offer_product", "")
        if not banner_text:
            raw = re.search(r"(?:with\s+)?text\s+(.+)", t, re.IGNORECASE)
            if not raw:
                raw = re.search(
                    r"\b(?:offer|discount|sale|deal|promo)\s+(?!on\b)(.+)",
                    t, re.IGNORECASE,
                )
            banner_text = raw.group(1).strip() if raw else "Special Offer!"
        steps.append({
            "action":        "OFFER_BANNER",
            "target":        "products",
            "value":         banner_text,
            "offer_scope":   offer_scope,
            "offer_product": offer_product,
        })

    # Add plain banner / announcement (non-product)
    elif re.search(
        r"\b(?:add|show|create)\s+(?:banner|announcement|notice)\b"
        r"|\bbanner\s+(?:add|lagao)\b"
        r"|\bbanner\s+add\s+karo\b",
        t,
    ):
        banner_text = entities.get("banner_text", "Special Offer!")
        steps.append({
            "action": "ADD_BANNER",
            "target": "topbar",
            "value":  banner_text,
        })

    # Change title / heading text
    elif re.search(
        r"\b(?:change|update|set)\s+(?:title|heading|topbar\s+title)\b"
        r"|\btitle\s+(?:change|badlo)\b",
        t,
    ):
        text_val = entities.get("text", "")
        steps.append({
            "action": "CHANGE_TEXT",
            "target": "topbar-title",
            "value":  text_val,
        })

    # ── DELETE RECORD ────────────────────────────────────────────────────────
    if any(k in t for k in ("delete", "remove", "hata", "हटाओ")):
        # "delete all" / "clear all" → wipe entire table via API
        if any(k in t for k in ("all", "every", "everything", "sab", "सब")):
            # Which table? default customers
            table = "customers"
            if any(k in t for k in ("product", "products")):
                table = "products"
            elif any(k in t for k in ("employee", "employees", "staff")):
                table = "employees"
            steps.append({"action": "OPEN_PAGE", "target": table})
            steps.append({"action": "CLEAR_ALL", "target": table})
            steps.append({"action": "READ_TABLE", "target": table + "-table"})
        else:
            # Delete a specific named record
            table = "customers"
            if any(k in t for k in ("product", "item")):
                table = "products"
            elif any(k in t for k in ("employee", "staff")):
                table = "employees"
            steps.append({"action": "OPEN_PAGE", "target": table})
            steps.append({
                "action": "DELETE_RECORD",
                "target": table + "-table",
                "value":  entities.get("name", ""),
            })
            steps.append({"action": "READ_TABLE", "target": table + "-table"})

    return steps


# ---------------------------------------------------------------------------
# Instruction splitter
# ---------------------------------------------------------------------------

def _split(instruction: str) -> list:
    text = instruction.strip()
    for pattern in SPLIT_PATTERNS:
        text = re.sub(pattern, "|", text, flags=re.IGNORECASE)
    parts = [p.strip() for p in text.split("|") if p.strip()]
    return parts or [instruction.strip()]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def plan_multi_step(instruction: str) -> dict:
    """
    Convert a natural-language instruction into a clean workflow dict.

    Returns:
        {
            "intent": str,
            "steps":  [ {"action": str, "target": str, ??"value": str}, ... ]
        }
    """

    entities  = extract_entities(instruction)
    # Merge web-specific entities (banner_text, color, logo, etc.) so that
    # _steps_for() can use them instead of falling back to hardcoded defaults.
    entities.update(extract_web_entities(instruction))
    sub_tasks = _split(instruction)

    all_steps: list = []
    for sub in sub_tasks:
        all_steps.extend(_steps_for(sub, entities))

    # Fallback: run planner on full instruction as single task
    if not all_steps:
        all_steps = _steps_for(instruction, entities)

    # Deduplicate consecutive identical steps
    deduped: list = []
    for step in all_steps:
        if not deduped or deduped[-1] != step:
            deduped.append(step)

    # Auto-append screenshot after OFFER_BANNER so result is visible in UI
    has_offer = any(s.get("action") == "OFFER_BANNER" for s in deduped)
    has_shot  = any(s.get("action") == "TAKE_SCREENSHOT" for s in deduped)
    if has_offer and not has_shot:
        deduped.append({"action": "TAKE_SCREENSHOT", "target": "current-page"})

    return {
        "intent": _intent(instruction),
        "steps":  deduped,
    }


# ---------------------------------------------------------------------------
# Direct testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    import json

    tests = [
        "Open the CRM, add Pankaj Koche as a customer with phone number 9876543210, save the record and verify that the customer appears in the table.",
        "Add Nikhil as customer with phone 9823456789",
        "Add Pankaj Koche as customer with phone 9876543210 and save",
        "Rahul naam ka customer jod do phone 9876543210",
        "Download today's report",
        "Upload invoice.pdf",
    ]

    for t in tests:
        result = plan_multi_step(t)
        print(f"\nInstruction: {t}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
