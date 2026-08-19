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
from app.core.entity_extractor import extract_entities


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
    # Web change check first — before update_record which also uses "change"
    if any(k in t for k in (
        "change logo", "update logo", "change header color", "change background",
        "change sidebar", "add banner", "add offer", "change title",
        "change button color", "change theme", "change color",
        "logo badlo", "banner add", "color change",
    )):
        return "change_web"
    if any(k in t for k in ("add", "create", "register", "jod", "bana", "जोड़", "बना")):
        if any(k in t for k in ("customer", "ग्राहक", "कस्टमर", "client")):
            return "add_customer"
        if any(k in t for k in ("employee", "staff", "कर्मचारी")):
            return "add_employee"
        if any(k in t for k in ("product", "item", "प्रोडक्ट")):
            return "add_product"
    if any(k in t for k in ("delete", "remove", "हटाओ")):
        return "delete_record"
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
    if "download" in t and ("report" in t or "csv" in t):
        steps.append({"action": "OPEN_PAGE", "target": "reports"})
        steps.append({"action": "CLICK",     "target": "download-report"})

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
    if re.search(r"\bchange\s+logo\b|\bupdate\s+logo\b|\blogo\s+(?:change|badlo)\b", t):
        logo = entities.get("logo", "")
        steps.append({
            "action": "CHANGE_LOGO",
            "target": "sidebar-logo",
            "value":  logo,
        })

    # Change color / background / sidebar / header color
    elif re.search(r"\bchange\s+(?:header\s+)?(?:color|background|bg|sidebar|theme)\b"
                   r"|\bcolor\s+change\b|\bbackground\s+(?:change|badlo)\b", t):
        element = entities.get("element", "body")
        color   = entities.get("color", "")
        steps.append({
            "action": "CHANGE_STYLE",
            "target": element,
            "value":  color,
        })

    # Add banner / offer / announcement
    elif re.search(r"\badd\s+(?:banner|offer|announcement|notice)\b"
                   r"|\bbanner\s+add\b|\boffer\s+add\b", t):
        banner_text = entities.get("banner_text", "Special Offer!")
        steps.append({
            "action": "ADD_BANNER",
            "target": "topbar",
            "value":  banner_text,
        })

    # Change title / heading text
    elif re.search(r"\bchange\s+(?:title|heading|topbar\s+title)\b"
                   r"|\btitle\s+(?:change|badlo)\b", t):
        text_val = entities.get("text", "")
        steps.append({
            "action": "CHANGE_TEXT",
            "target": "topbar-title",
            "value":  text_val,
        })

    # Change sidebar color specifically
    if re.search(r"\bchange\s+sidebar\b|\bsidebar\s+(?:color|background)\b", t):
        color = entities.get("color", "")
        steps.append({
            "action": "CHANGE_STYLE",
            "target": "sidebar",
            "value":  color,
        })

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
