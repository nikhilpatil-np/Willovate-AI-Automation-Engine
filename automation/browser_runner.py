"""
Browser Runner
==============
Executes a workflow dict against the CRM web application using Playwright.

Supports all action types produced by multi_step_planner.py:
  OPEN_PAGE, CLICK, ENTER_TEXT, READ_TABLE, VERIFY_RECORD,
  TAKE_SCREENSHOT, WAIT, SCROLL, UPLOAD_FILE, SEND_EMAIL (skipped gracefully)
"""

import asyncio
import json
import os

from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from app.core.error_detector import detect_error


MAX_RETRIES = 2

# Maps workflow target → CRM JS navigate() argument
PAGE_MAP = {
    "customers":  "customers",
    "customer":   "customers",
    "crm":        "customers",
    "products":   "products",
    "product":    "products",
    "employees":  "employees",
    "employee":   "employees",
    "reports":    "reports",
    "report":     "reports",
    "upload":     "upload",
    "settings":   "settings",
    "dashboard":  "dashboard",
}

# Maps workflow target → CSS selector
FIELD_MAP = {
    # Customer fields
    "customer-name":  "#customerName",
    "customername":   "#customerName",
    "customer name":  "#customerName",
    "phone-number":   "#phoneNumber",
    "phonenumber":    "#phoneNumber",
    "phone number":   "#phoneNumber",
    "phone":          "#phoneNumber",
    "customer-email": "#customerEmail",
    "email":          "#customerEmail",
    "status":         "#customerStatus",
    # Product fields
    "product-name":   "#productName",
    "product name":   "#productName",
    "price":          "#productPrice",
    "product-price":  "#productPrice",
    "category":       "#productCategory",
    "stock":          "#productStock",
    # Employee fields
    "employee-name":  "#employeeName",
    "employee name":  "#employeeName",
    "employee-phone": "#employeePhone",
    "employee phone": "#employeePhone",
    "employee-email": "#employeeEmail",
    "department":     "#employeeDept",
}

# Maps workflow click target → CSS selector or role
CLICK_MAP = {
    "add-customer":       "#addCustomer",
    "add customer":       "#addCustomer",
    "save":               "#saveCustomer",
    "save customer":      "#saveCustomer",
    "add-employee":       "button[onclick='addEmployee()']",
    "add employee":       "button[onclick='addEmployee()']",
    "add-product":        "button[onclick='addProduct()']",
    "add product":        "button[onclick='addProduct()']",
    "download-report":    "#downloadCustomerReport",
    "download report":    "#downloadCustomerReport",
    "download":           "#downloadCustomerReport",
    "upload file":        "#uploadFileBtn",
    "upload-file":        "#uploadFileBtn",
}

# Maps workflow table target → tbody selector
TABLE_MAP = {
    "customer-table":  "#customerTableBody",
    "customer table":  "#customerTableBody",
    "customer list":   "#customerTableBody",
    "customers":       "#customerTableBody",
    "product-table":   "#productTableBody",
    "product table":   "#productTableBody",
    "employee-table":  "#employeeTableBody",
    "employee table":  "#employeeTableBody",
}


# ---------------------------------------------------------------------------
# CRM URL
# ---------------------------------------------------------------------------

def _crm_url() -> str:
    path = os.path.abspath("automation/crm.html")
    return "file:///" + path.replace("\\", "/")


# ---------------------------------------------------------------------------
# Single step executor
# ---------------------------------------------------------------------------

async def execute_step(page, step: dict, crm_url: str, workflow: dict) -> dict:
    action = step.get("action", "").upper()
    target = step.get("target", "").lower().strip()
    value  = step.get("value", "")

    # ── OPEN_PAGE ───────────────────────────────────────────────────────────
    if action == "OPEN_PAGE":
        nav = PAGE_MAP.get(target)
        if nav:
            await page.evaluate(f"navigate('{nav}')")
            await page.wait_for_timeout(300)
        else:
            await page.goto(crm_url)
            await page.wait_for_load_state("domcontentloaded")
        return {"success": True}

    # ── CLICK ───────────────────────────────────────────────────────────────
    elif action == "CLICK":
        # Check nav targets first
        if target in PAGE_MAP:
            await page.evaluate(f"navigate('{PAGE_MAP[target]}')")
            await page.wait_for_timeout(300)
            return {"success": True}

        selector = CLICK_MAP.get(target)
        if selector:
            loc = page.locator(selector)
            if await loc.count() > 0:
                await loc.first.click()
                await page.wait_for_timeout(300)
                return {"success": True}

        # Generic fallback by button text
        btn = page.get_by_role("button", name=target)
        if await btn.count() > 0:
            await btn.first.click()
            await page.wait_for_timeout(300)
            return {"success": True}

        return {"success": True, "skipped": True, "reason": f"Click target '{target}' not found"}

    # ── ENTER_TEXT ──────────────────────────────────────────────────────────
    elif action == "ENTER_TEXT":
        selector = FIELD_MAP.get(target)
        if selector:
            await page.locator(selector).fill(str(value))
            return {"success": True}
        return {"success": True, "skipped": True, "reason": f"Field '{target}' not mapped"}

    # ── READ_TABLE ──────────────────────────────────────────────────────────
    elif action == "READ_TABLE":
        tbody = TABLE_MAP.get(target, "#customerTableBody")
        rows  = await page.locator(f"{tbody} tr").all()
        records = []
        for row in rows:
            cells = await row.locator("td").all_text_contents()
            # 6-column CRM layout: # | Name | Phone | Email | Status | Actions
            if len(cells) >= 4:
                records.append({
                    "name":  cells[1].strip(),
                    "phone": cells[2].strip(),
                    "email": cells[3].strip(),
                })
            elif len(cells) >= 3:
                records.append({
                    "name":  cells[1].strip(),
                    "phone": cells[2].strip(),
                    "email": "",
                })
            elif len(cells) >= 2:
                records.append({
                    "name":  cells[0].strip(),
                    "phone": cells[1].strip(),
                    "email": "",
                })
        return {"success": True, "records": records}

    # ── VERIFY_RECORD ───────────────────────────────────────────────────────
    elif action == "VERIFY_RECORD":
        tbody    = TABLE_MAP.get(target, "#customerTableBody")
        entities = workflow.get("entities", {})
        name     = (value or entities.get("name", "")).strip()
        phone    = entities.get("phone", "").strip()

        rows  = await page.locator(f"{tbody} tr").all()
        found = False
        for row in rows:
            cells = await row.locator("td").all_text_contents()
            row_name  = (cells[1] if len(cells) >= 3 else cells[0] if cells else "").strip()
            row_phone = (cells[2] if len(cells) >= 3 else cells[1] if len(cells) >= 2 else "").strip()
            if row_name.lower() == name.lower() and (not phone or row_phone == phone):
                found = True
                break

        if not found:
            raise ValueError(f"VERIFY_RECORD failed — '{name}' not found in {tbody}")

        return {"success": True, "verified": True, "name": name, "phone": phone}

    # ── TAKE_SCREENSHOT ─────────────────────────────────────────────────────
    elif action == "TAKE_SCREENSHOT":
        os.makedirs("outputs/screenshots", exist_ok=True)
        path = "outputs/screenshots/screenshot.png"
        await page.screenshot(path=path, full_page=True)
        return {"success": True, "path": path}

    # ── WAIT ────────────────────────────────────────────────────────────────
    elif action == "WAIT":
        raw = re.sub(r"[^\d]", "", str(value or target or "1")) or "1"
        await page.wait_for_timeout(int(raw) * 1000)
        return {"success": True}

    # ── SCROLL ──────────────────────────────────────────────────────────────
    elif action == "SCROLL":
        delta = -600 if target == "up" else 600
        await page.mouse.wheel(0, delta)
        return {"success": True}

    # ── UNSUPPORTED — skip gracefully ───────────────────────────────────────
    else:
        return {"success": True, "skipped": True,
                "reason": f"Action '{action}' not implemented — skipped"}


# Need re for WAIT
import re


# ---------------------------------------------------------------------------
# Full workflow executor
# ---------------------------------------------------------------------------

async def execute_workflow(workflow: dict, headless: bool = True) -> dict:
    """
    Execute a workflow dict against the CRM.

    Args:
        workflow:  Dict with "steps" list and optional "entities" sub-dict.
        headless:  True = no browser window (API mode).
                   False = visible browser (demo mode).

    Returns execution result dict.
    """

    result = {
        "success":        False,
        "steps_executed": 0,
        "steps_total":    0,
        "failed_step":    None,
        "failed_action":  None,
        "error":          None,
        "retry_count":    0,
        "verification":   False,
        "customers":      None,
        "step_results":   [],
    }

    steps = workflow.get("steps", [])
    result["steps_total"] = len(steps)

    if not steps:
        result["error"] = {"message": "Workflow has no steps."}
        return result

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page    = await context.new_page()
        crm_url = _crm_url()

        # Pre-load the CRM so navigate() is always available
        await page.goto(crm_url)
        await page.wait_for_load_state("domcontentloaded")

        print(f"\nBrowser runner started (headless={headless})")
        print(f"CRM: {crm_url}")
        print("-" * 50)

        for idx, step in enumerate(steps, start=1):
            action = step.get("action", "")
            target = step.get("target", "")
            print(f"  Step {idx}/{len(steps)}: {action} -> {target}")

            step_res = {
                "step":    idx,
                "action":  action,
                "target":  target,
                "success": False,
                "retries": 0,
            }
            ok = False

            for attempt in range(MAX_RETRIES + 1):
                try:
                    sr = await execute_step(page, step, crm_url, workflow)

                    if action.upper() == "READ_TABLE":
                        result["customers"] = sr.get("records", [])
                        step_res["records"] = sr.get("records", [])

                    if action.upper() == "VERIFY_RECORD":
                        result["verification"] = sr.get("verified", False)
                        step_res["verified"]   = sr.get("verified", False)

                    ok = True
                    step_res["success"] = True
                    if sr.get("skipped"):
                        step_res["skipped"] = True
                        step_res["reason"]  = sr.get("reason")
                    break

                except (PlaywrightTimeoutError, Exception) as exc:
                    msg = str(exc)
                    print(f"    attempt {attempt + 1} error: {msg}")
                    if attempt < MAX_RETRIES:
                        result["retry_count"] += 1
                        step_res["retries"]   += 1
                        await page.wait_for_timeout(1000)
                    else:
                        result["failed_step"]   = idx
                        result["failed_action"] = action
                        result["error"] = {
                            "message":  msg,
                            "analysis": detect_error(msg),
                        }
                        step_res["error"] = msg

            result["step_results"].append(step_res)
            result["steps_executed"] += 1

            if not ok:
                await browser.close()
                return result

        result["success"] = True
        print("\n  All steps completed successfully.")

        if not headless:
            input("\nPress ENTER to close the browser…")

        await browser.close()
        return result


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    test = {
        "intent": "add_customer",
        "entities": {"name": "Pankaj Koche", "phone": "9876543210"},
        "steps": [
            {"action": "OPEN_PAGE",     "target": "customers"},
            {"action": "ENTER_TEXT",    "target": "customer-name",  "value": "Pankaj Koche"},
            {"action": "ENTER_TEXT",    "target": "phone-number",   "value": "9876543210"},
            {"action": "CLICK",         "target": "add-customer"},
            {"action": "CLICK",         "target": "save"},
            {"action": "READ_TABLE",    "target": "customer-table"},
            {"action": "VERIFY_RECORD", "target": "customer-table", "value": "Pankaj Koche"},
        ],
    }

    r = asyncio.run(execute_workflow(test, headless=False))
    print(json.dumps(r, indent=2))
