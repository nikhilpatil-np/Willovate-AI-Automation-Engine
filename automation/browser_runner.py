"""
Browser Runner
==============
Executes a workflow dict against the CRM web application using Playwright.

Supports all action types produced by multi_step_planner.py:
  OPEN_PAGE, CLICK, ENTER_TEXT, READ_TABLE, VERIFY_RECORD,
  TAKE_SCREENSHOT, WAIT, SCROLL, UPLOAD_FILE, SEND_EMAIL (skipped gracefully)

CRM Backend
-----------
The CRM now persists data via a FastAPI + SQLite backend on port 8001.
This module auto-starts that server before the browser opens and shuts it
down when done (if it was started by us).  If the server is already running
(e.g. started manually), it is left alone.
"""

import asyncio
import json
import os
import socket
import subprocess
import sys
import time

from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from app.core.error_detector import detect_error


MAX_RETRIES  = 2
CRM_API_PORT = 8001          # must match crm_service.py and crm.html API const
CRM_API_HOST = "127.0.0.1"

# ---------------------------------------------------------------------------
# CRM backend lifecycle helpers
# ---------------------------------------------------------------------------

def _is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """Return True if something is already listening on host:port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _start_crm_server() -> subprocess.Popen | None:
    """
    Start the CRM FastAPI server as a background subprocess.

    Returns the Popen object so the caller can terminate it later,
    or None if the server was already running before we tried.
    """
    if _is_port_open(CRM_API_HOST, CRM_API_PORT):
        print(f"  CRM backend already running on port {CRM_API_PORT} — reusing.")
        return None  # not our process to manage

    print(f"  Starting CRM backend on port {CRM_API_PORT}…")
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "app.services.crm_service:app",
            "--host", CRM_API_HOST,
            "--port", str(CRM_API_PORT),
            "--log-level", "warning",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait up to 8 seconds for the server to become ready
    deadline = time.time() + 8.0
    while time.time() < deadline:
        if _is_port_open(CRM_API_HOST, CRM_API_PORT):
            print(f"  CRM backend ready on port {CRM_API_PORT}.")
            return proc
        time.sleep(0.25)

    # If it never came up, kill it and warn — workflow will still attempt to run
    proc.terminate()
    print(f"  WARNING: CRM backend did not start within 8 s. "
          f"DB persistence may not work.")
    return None


def _stop_crm_server(proc: subprocess.Popen | None) -> None:
    """Terminate the CRM server subprocess if we started it."""
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
        print(f"  CRM backend stopped.")
    except Exception:
        proc.kill()

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
    "product-name":     "#productName",
    "product name":     "#productName",
    "price":            "#productPrice",
    "product-price":    "#productPrice",
    "category":         "#productCategory",
    "product-category": "#productCategory",
    "stock":            "#productStock",
    "product-stock":    "#productStock",
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
    "download-report":          "#downloadCustomerReport",
    "download report":          "#downloadCustomerReport",
    "download":                 "#downloadCustomerReport",
    "download-customer-report": "#downloadCustomerReport",
    "download customer report": "#downloadCustomerReport",
    "download-product-report":  "#downloadProductReport",
    "download product report":  "#downloadProductReport",
    "download-today-report":    "#downloadTodayReport",
    "download today report":    "#downloadTodayReport",
    "upload file":        "#uploadFileBtn",
    "upload-file":        "#uploadFileBtn",
}

# Maps workflow table target → tbody selector
TABLE_MAP = {
    "customer-table":   "#customerTableBody",
    "customer table":   "#customerTableBody",
    "customers-table":  "#customerTableBody",
    "customer list":    "#customerTableBody",
    "customers":        "#customerTableBody",
    "product-table":    "#productTableBody",
    "product table":    "#productTableBody",
    "products-table":   "#productTableBody",
    "products":         "#productTableBody",
    "employee-table":   "#employeeTableBody",
    "employee table":   "#employeeTableBody",
    "employees-table":  "#employeeTableBody",
}


# ---------------------------------------------------------------------------
# CRM URL
# ---------------------------------------------------------------------------

def _crm_url() -> str:
    """
    Return the URL used to open the CRM in Playwright.

    We still serve the HTML as a local file — this is fine because every
    API call inside crm.html uses an absolute http://localhost:8001 URL,
    so the browser's CORS rules are satisfied by our server's allow_origins=["*"].
    """
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

        # ── Report downloads — handled directly via API (Playwright cannot
        #    intercept JS blob-URL downloads triggered by <a>.click())  ──────
        _report_download_map = {
            "download-customer-report": ("customers", "csv"),
            "download customer report": ("customers", "csv"),
            "download-report":          ("customers", "csv"),
            "download report":          ("customers", "csv"),
            "download":                 ("customers", "csv"),
            "download-product-report":  ("products",  "csv"),
            "download product report":  ("products",  "csv"),
            "download-today-report":    ("today",     "xlsx"),
            "download today report":    ("today",     "xlsx"),
        }
        if target in _report_download_map:
            report_type, fmt = _report_download_map[target]
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)

            import urllib.request, json as _json
            from datetime import date
            today_str = date.today().strftime("%Y-%m-%d")
            api_base  = f"http://{CRM_API_HOST}:{CRM_API_PORT}"

            if report_type == "today":
                # Fetch multi-sheet Excel from /report/today
                url  = f"{api_base}/report/today"
                dest = os.path.join(downloads_dir, f"today_report_{today_str}.xlsx")
                urllib.request.urlretrieve(url, dest)
                print(f"  Downloaded: {dest}")
                return {"success": True, "downloaded": dest}
            else:
                # Fetch JSON records, convert to CSV
                url     = f"{api_base}/{report_type}"
                with urllib.request.urlopen(url) as resp:
                    records = _json.loads(resp.read())
                if not records:
                    return {"success": True, "skipped": True,
                            "reason": f"No {report_type} records to download"}
                keys    = [k for k in records[0].keys() if k != "id"]
                lines   = [",".join(keys)]
                for row in records:
                    lines.append(",".join(f'"{row.get(k,"")}"' for k in keys))
                csv_text = "\n".join(lines)
                dest = os.path.join(downloads_dir, f"{report_type}_report_{today_str}.csv")
                with open(dest, "w", encoding="utf-8") as fh:
                    fh.write(csv_text)
                print(f"  Downloaded: {dest}")
                return {"success": True, "downloaded": dest}

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

        # Wait for the async API fetch to finish rendering the table
        try:
            await page.wait_for_function(
                f"document.querySelector('{tbody}').innerText.indexOf('Loading') === -1",
                timeout=5000,
            )
        except PlaywrightTimeoutError:
            pass  # table may be empty — proceed
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

        # Wait for the table to finish loading from the API (no "Loading…" text)
        try:
            await page.wait_for_function(
                f"document.querySelector('{tbody}').innerText.indexOf('Loading') === -1",
                timeout=5000,
            )
        except PlaywrightTimeoutError:
            pass  # proceed anyway — table may just be empty

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

    # ── OFFER_BANNER — product-aware offer banner ──────────────────────────
    # Fetches products from the CRM API first.
    # • No products at all  → raises ValueError (execution blocked with message)
    # • offer_scope=single  → checks the named product exists, applies targeted banner
    # • offer_scope=all     → applies banner listing all products
    elif action == "OFFER_BANNER":
        import urllib.request
        import json as _json

        banner_text   = str(value or "Special Offer!").strip()
        offer_scope   = step.get("offer_scope", "all")
        offer_product = str(step.get("offer_product", "")).strip()
        api_base      = f"http://{CRM_API_HOST}:{CRM_API_PORT}"

        # ── Step 1: Fetch all products from CRM backend ────────────────────
        try:
            with urllib.request.urlopen(f"{api_base}/products", timeout=5) as resp:
                products = _json.loads(resp.read())
        except Exception as e:
            raise ValueError(
                f"Could not connect to CRM backend to check products: {e}. "
                f"Make sure the CRM server is running on port {CRM_API_PORT}."
            )

        # ── Step 2: Block if no products exist ─────────────────────────────
        if not products:
            raise ValueError(
                "No products found in the CRM database. "
                "You cannot add a product offer because there are no products. "
                "Please add at least one product first, then apply the offer."
            )

        # ── Step 3: For single-product offer, verify the product exists ─────
        if offer_scope == "single" and offer_product:
            matched = [
                p for p in products
                if p.get("name", "").lower() == offer_product.lower()
            ]
            if not matched:
                product_list = ", ".join(p["name"] for p in products)
                raise ValueError(
                    f"Product '{offer_product}' not found in the CRM. "
                    f"Available products: {product_list}. "
                    f"Please check the product name and try again."
                )
            # Narrow down to just the matched product
            target_products = matched
            scope_label = f"on {matched[0]['name']}"
        else:
            target_products = products
            scope_label = "on All Products"

        # ── Step 4: Build product detail lines for the banner ──────────────
        if offer_scope == "single" and target_products:
            p = target_products[0]
            product_detail = (
                f"{p['name']}"
                + (f" — ₹{p['price']}" if p.get("price") else "")
                + (f" ({p['category']})" if p.get("category") else "")
            )
        else:
            # Show up to 3 product names in the banner, then "& more" if needed
            names = [p["name"] for p in target_products[:3]]
            product_detail = ", ".join(names)
            if len(target_products) > 3:
                product_detail += f" & {len(target_products) - 3} more"

        # ── Step 5: Navigate to products page so banner is contextual ───────
        await page.evaluate("navigate('products')")
        await page.wait_for_timeout(400)

        # ── Step 6: Inject styled offer banner into the CRM page ───────────
        # Escape single quotes in dynamic text to avoid JS injection issues
        safe_text    = banner_text.replace("'", "\\'")
        safe_detail  = product_detail.replace("'", "\\'")
        safe_scope   = scope_label.replace("'", "\\'")

        await page.evaluate(f"""
            (function() {{
                // Remove existing offer banner if any
                var existing = document.getElementById('ai-offer-banner');
                if (existing) existing.remove();

                // ── Outer wrapper ──────────────────────────────────────────
                var wrapper = document.createElement('div');
                wrapper.id = 'ai-offer-banner';
                wrapper.style.cssText = [
                    'background: linear-gradient(135deg, #e63946 0%, #c1121f 100%)',
                    'color: #fff',
                    'padding: 14px 24px',
                    'display: flex',
                    'align-items: center',
                    'justify-content: space-between',
                    'gap: 16px',
                    'box-shadow: 0 3px 12px rgba(230,57,70,.35)',
                    'position: relative',
                    'z-index: 500',
                    'flex-wrap: wrap',
                ].join(';');

                // ── Left: tag + text ────────────────────────────────────────
                var left = document.createElement('div');
                left.style.cssText = 'display:flex;align-items:center;gap:12px;flex-wrap:wrap;';

                var tag = document.createElement('span');
                tag.style.cssText = [
                    'background: #fff',
                    'color: #e63946',
                    'font-size: 11px',
                    'font-weight: 800',
                    'padding: 3px 10px',
                    'border-radius: 20px',
                    'letter-spacing: .6px',
                    'text-transform: uppercase',
                    'flex-shrink: 0',
                ].join(';');
                tag.textContent = '🏷 OFFER';

                var textBlock = document.createElement('div');

                var headline = document.createElement('div');
                headline.style.cssText = 'font-size:15px;font-weight:700;line-height:1.3;';
                headline.textContent = '{safe_text}';

                var sub = document.createElement('div');
                sub.style.cssText = 'font-size:12px;opacity:.88;margin-top:3px;';
                sub.textContent = '{safe_detail}  •  {safe_scope}';

                textBlock.appendChild(headline);
                textBlock.appendChild(sub);

                left.appendChild(tag);
                left.appendChild(textBlock);

                // ── Right: product count pill + close ────────────────────────
                var right = document.createElement('div');
                right.style.cssText = 'display:flex;align-items:center;gap:10px;flex-shrink:0;';

                var pill = document.createElement('span');
                pill.style.cssText = [
                    'background: rgba(255,255,255,.22)',
                    'border: 1px solid rgba(255,255,255,.4)',
                    'border-radius: 20px',
                    'padding: 3px 12px',
                    'font-size: 12px',
                    'font-weight: 600',
                ].join(';');
                pill.textContent = '{len(target_products)} product' + ({len(target_products)} === 1 ? '' : 's');

                var closeBtn = document.createElement('span');
                closeBtn.style.cssText = 'cursor:pointer;opacity:.75;font-size:18px;line-height:1;padding:0 4px;';
                closeBtn.innerHTML = '&times;';
                closeBtn.title = 'Dismiss offer banner';
                closeBtn.onclick = function() {{
                    document.getElementById('ai-offer-banner').remove();
                }};

                right.appendChild(pill);
                right.appendChild(closeBtn);

                wrapper.appendChild(left);
                wrapper.appendChild(right);

                // ── Insert at top of the .main area ─────────────────────────
                var main = document.querySelector('.main');
                if (main) {{
                    main.insertBefore(wrapper, main.firstChild);
                }} else {{
                    document.body.insertBefore(wrapper, document.body.firstChild);
                }}
            }})();
        """)

        # ── Step 7: Persist the offer to the backend so real browser shows it ─
        import json as _json2
        offer_payload = _json.dumps({
            "banner_text":  banner_text,
            "offer_scope":  offer_scope,
            "products":     ", ".join(p["name"] for p in target_products),
        }).encode("utf-8")
        try:
            req = urllib.request.Request(
                f"{api_base}/offer",
                data=offer_payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=3)
            print(f"  Offer persisted to backend: {banner_text}")
        except Exception as e:
            print(f"  Warning: could not persist offer to backend: {e}")

        return {
            "success":       True,
            "offer_applied": True,
            "scope":         offer_scope,
            "products":      [p["name"] for p in target_products],
            "banner_text":   banner_text,
        }

    # ── CHANGE_LOGO ─────────────────────────────────────────────────────────
    # POSTs a flag to the CRM backend so the real browser tab opens the
    # logo-upload modal (the CRM page polls /ui/logo-request every 2 s).
    # The headless Playwright session cannot interact with the user's actual
    # browser window, so we signal via the persistent backend instead.
    elif action == "CHANGE_LOGO":
        import urllib.request as _urllib_req
        api_base = f"http://{CRM_API_HOST}:{CRM_API_PORT}"
        try:
            req = _urllib_req.Request(
                f"{api_base}/ui/logo-request",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            _urllib_req.urlopen(req, timeout=5)
            print("  Logo-change request posted — CRM page will open upload modal.")
        except Exception as e:
            raise ValueError(
                f"Could not post logo-change request to CRM backend: {e}. "
                f"Make sure the CRM server is running on port {CRM_API_PORT}."
            )
        return {
            "success":      True,
            "changed":      "logo",
            "modal_opened": True,
            "message":      "Logo upload modal will open in your CRM browser tab.",
        }

    # ── CHANGE_STYLE ────────────────────────────────────────────────────────
    elif action == "CHANGE_STYLE":
        element_map = {
            "sidebar":    ".sidebar",
            "header":     ".topbar",
            "topbar":     ".topbar",
            "background": "body",
            "body":       "body",
            "navbar":     ".sidebar",
            "footer":     "footer",
        }
        selector  = element_map.get(target.lower(), "." + target.lower())
        color_val = str(value or "").strip()
        if color_val:
            await page.evaluate(f"""
                var el = document.querySelector('{selector}');
                if (el) el.style.background = '{color_val}';
            """)
            # Persist to backend so real browser tab picks it up via style poller
            import urllib.request as _urllib_req, json as _json
            api_base = f"http://{CRM_API_HOST}:{CRM_API_PORT}"
            payload  = _json.dumps({"element": target.lower(), "color": color_val}).encode()
            try:
                req = _urllib_req.Request(
                    f"{api_base}/ui/style",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                _urllib_req.urlopen(req, timeout=3)
                print(f"  Style persisted: {target} → {color_val}")
            except Exception as e:
                print(f"  Warning: could not persist style to backend: {e}")
        return {"success": True, "changed": target, "value": color_val}

    # ── ADD_BANNER ──────────────────────────────────────────────────────────
    elif action == "ADD_BANNER":
        banner_text = str(value or "Special Offer!").strip()
        safe_text   = banner_text.replace("'", "\\'")
        await page.evaluate(f"""
            // Remove existing banner if any
            var existing = document.getElementById('ai-banner');
            if (existing) existing.remove();

            // Create new banner
            var banner = document.createElement('div');
            banner.id = 'ai-banner';
            banner.style.cssText = 'background:#e63946;color:#fff;text-align:center;'
                + 'padding:10px 20px;font-size:14px;font-weight:600;'
                + 'position:relative;z-index:1000;display:flex;'
                + 'align-items:center;justify-content:center;gap:12px;';
            var span = document.createElement('span');
            span.textContent = '{safe_text}';
            var close = document.createElement('span');
            close.innerHTML = '&times;';
            close.style.cssText = 'cursor:pointer;opacity:.75;font-size:18px;line-height:1;';
            close.onclick = function() {{ document.getElementById('ai-banner').remove(); }};
            banner.appendChild(span);
            banner.appendChild(close);

            // Insert at top of main area
            var main = document.querySelector('.main');
            if (main) main.insertBefore(banner, main.firstChild);
        """)
        # Persist to backend so real browser tab picks it up via banner poller
        import urllib.request as _urllib_req, json as _json
        api_base = f"http://{CRM_API_HOST}:{CRM_API_PORT}"
        payload  = _json.dumps({
            "text":       banner_text,
            "bg_color":   "#e63946",
            "text_color": "#ffffff",
        }).encode()
        try:
            req = _urllib_req.Request(
                f"{api_base}/ui/banner",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            _urllib_req.urlopen(req, timeout=3)
            print(f"  Banner persisted: {banner_text}")
        except Exception as e:
            print(f"  Warning: could not persist banner to backend: {e}")
        return {"success": True, "changed": "banner", "value": banner_text}

    # ── CHANGE_TEXT ─────────────────────────────────────────────────────────
    elif action == "CHANGE_TEXT":
        element_map = {
            "topbar-title": "#topbar-title",
            "title":        "#topbar-title",
            "header":       "#topbar-title",
            "sidebar-logo": ".sidebar-logo",
        }
        selector = element_map.get(target.lower(), "#" + target.lower())
        text_val = str(value or "").strip()
        if text_val:
            await page.evaluate(f"""
                var el = document.querySelector('{selector}');
                if (el) el.textContent = '{text_val}';
            """)
        return {"success": True, "changed": target, "value": text_val}

    # ── DELETE_RECORD — delete a specific record by name via the CRM API ───────
    elif action == "DELETE_RECORD":
        import urllib.request
        name  = str(value or "").strip().lower()
        # Map target table to API endpoint
        endpoint_map = {
            "customer-table":  "customers",
            "customer table":  "customers",
            "customers":       "customers",
            "product-table":   "products",
            "product table":   "products",
            "products":        "products",
            "employee-table":  "employees",
            "employee table":  "employees",
            "employees":       "employees",
        }
        endpoint = endpoint_map.get(target, "customers")
        api_base = f"http://{CRM_API_HOST}:{CRM_API_PORT}"

        # Fetch all records, find matching row by name
        import json as _json, urllib.error
        try:
            with urllib.request.urlopen(f"{api_base}/{endpoint}") as resp:
                records = _json.loads(resp.read())
        except Exception as e:
            raise ValueError(f"DELETE_RECORD: could not fetch {endpoint}: {e}")

        # Find matching record
        match = next(
            (r for r in records if r.get("name", "").lower() == name),
            None
        )
        if not match:
            raise ValueError(f"DELETE_RECORD: '{name}' not found in {endpoint}")

        # Delete by ID
        req = urllib.request.Request(
            f"{api_base}/{endpoint}/{match['id']}",
            method="DELETE",
        )
        try:
            urllib.request.urlopen(req)
        except Exception as e:
            raise ValueError(f"DELETE_RECORD: API delete failed: {e}")

        # Reload the page table to reflect deletion
        await page.reload()
        await page.wait_for_load_state("domcontentloaded")
        await page.evaluate(f"navigate('{endpoint}')")
        await page.wait_for_timeout(800)
        return {"success": True, "deleted": name, "id": match["id"]}

    # ── CLEAR_ALL — wipe a single table via DELETE /<table>/all ─────────────
    elif action == "CLEAR_ALL":
        import urllib.request
        api_base = f"http://{CRM_API_HOST}:{CRM_API_PORT}"

        # Map the workflow target to the correct per-table endpoint.
        # Fall back to /data/all only when target is explicitly "all".
        table_endpoint_map = {
            "customers":  "customers",
            "customer":   "customers",
            "products":   "products",
            "product":    "products",
            "employees":  "employees",
            "employee":   "employees",
        }
        table = table_endpoint_map.get(target)
        endpoint = f"/{table}/all" if table else "/data/all"

        req = urllib.request.Request(f"{api_base}{endpoint}", method="DELETE")
        try:
            urllib.request.urlopen(req)
        except Exception as e:
            raise ValueError(f"CLEAR_ALL: API call to {endpoint} failed: {e}")

        # Reload the CRM page so the table reflects the cleared state
        await page.reload()
        await page.wait_for_load_state("domcontentloaded")
        nav_target = PAGE_MAP.get(target, "customers")
        await page.evaluate(f"navigate('{nav_target}')")
        await page.wait_for_timeout(800)
        return {"success": True, "cleared": table or "all"}

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

    Backend lifecycle
    -----------------
    Automatically starts the CRM FastAPI server (port 8001) if it is not
    already running, and stops it again when the workflow finishes.
    If the server is already up (e.g. started manually), it is left alone.
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
        "offer_applied":  False,
        "offer_scope":    None,
        "offer_products": [],
        "banner_text":    "",
        "step_results":   [],
    }

    steps = workflow.get("steps", [])
    result["steps_total"] = len(steps)

    if not steps:
        result["error"] = {"message": "Workflow has no steps."}
        return result

    # ── Start the CRM backend (if not already running) ──────────────────────
    crm_proc = _start_crm_server()

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)

            # Route browser-triggered downloads (CSV reports etc.) to the
            # user's real Downloads folder so they survive after browser closes.
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_dir, exist_ok=True)

            context = await browser.new_context(accept_downloads=True)
            page    = await context.new_page()

            # Intercept every download event and save to ~/Downloads
            async def _save_download(download):
                dest = os.path.join(downloads_dir, download.suggested_filename)
                await download.save_as(dest)
                print(f"  Downloaded: {dest}")

            page.on("download", _save_download)
            crm_url = _crm_url()

            # Pre-load the CRM so navigate() is always available
            await page.goto(crm_url)
            await page.wait_for_load_state("domcontentloaded")

            # Give the page a moment to fire its init fetch to the backend
            await page.wait_for_timeout(800)

            print(f"\nBrowser runner started (headless={headless})")
            print(f"CRM:     {crm_url}")
            print(f"Backend: http://{CRM_API_HOST}:{CRM_API_PORT}")
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

                        if action.upper() == "OFFER_BANNER":
                            result["offer_applied"]  = sr.get("offer_applied", False)
                            result["offer_scope"]    = sr.get("scope", "all")
                            result["offer_products"] = sr.get("products", [])
                            result["banner_text"]    = sr.get("banner_text", "")
                            step_res["offer_applied"]  = sr.get("offer_applied", False)
                            step_res["offer_scope"]    = sr.get("scope", "all")
                            step_res["offer_products"] = sr.get("products", [])

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

    finally:
        # ── Stop the CRM backend only if we started it ───────────────────
        _stop_crm_server(crm_proc)

    return result


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
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
