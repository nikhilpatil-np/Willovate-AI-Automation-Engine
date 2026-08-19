"""
CRM Service
===========
Standalone FastAPI app that provides persistent SQLite-backed CRUD
endpoints for the Willovate CRM.

Runs on port 8001 (separate from the main AI engine on port 8000).

Endpoints:
    Customers:
        GET    /customers           — list all
        POST   /customers           — create
        DELETE /customers/{id}      — delete

    Products:
        GET    /products
        POST   /products
        DELETE /products/{id}

    Employees:
        GET    /employees
        POST   /employees
        DELETE /employees/{id}

    System:
        GET    /health
        DELETE /data/all            — wipe all tables (danger zone)

Run:
    uvicorn app.services.crm_service:app --port 8001 --reload

Or use the helper at the bottom:
    python -m app.services.crm_service
"""

import io
import sqlite3
import os
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Optional

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parents[2]
DB_PATH = ROOT / "data" / "crm.db"


def _init_db():
    """Create tables if they don't exist."""
    os.makedirs(DB_PATH.parent, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT    NOT NULL,
                phone   TEXT    NOT NULL,
                email   TEXT    DEFAULT '',
                status  TEXT    DEFAULT 'Active',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT    NOT NULL,
                price    REAL    NOT NULL,
                category TEXT    DEFAULT '',
                stock    INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT NOT NULL,
                phone      TEXT DEFAULT '',
                email      TEXT DEFAULT '',
                department TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS active_offer (
                id          INTEGER PRIMARY KEY CHECK (id = 1),
                banner_text TEXT    NOT NULL,
                offer_scope TEXT    DEFAULT 'all',
                products    TEXT    DEFAULT '',
                created_at  TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ui_settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


@contextmanager
def get_db():
    """Yield a SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CustomerIn(BaseModel):
    name:   str
    phone:  str
    email:  Optional[str] = ""
    status: Optional[str] = "Active"


class ProductIn(BaseModel):
    name:     str
    price:    float
    category: Optional[str] = ""
    stock:    Optional[int] = 0


class EmployeeIn(BaseModel):
    name:       str
    phone:      Optional[str] = ""
    email:      Optional[str] = ""
    department: Optional[str] = ""


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Willovate CRM API",
    version="1.0.0",
    description="Persistent SQLite-backed CRUD API for the Willovate CRM frontend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialise DB tables on startup
_init_db()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "db": str(DB_PATH)}


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

@app.get("/customers", tags=["Customers"])
def list_customers():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, phone, email, status, created_at FROM customers ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/customers", tags=["Customers"], status_code=201)
def create_customer(customer: CustomerIn):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO customers (name, phone, email, status) VALUES (?, ?, ?, ?)",
            (customer.name, customer.phone, customer.email, customer.status),
        )
        new_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, name, phone, email, status, created_at FROM customers WHERE id = ?",
            (new_id,),
        ).fetchone()
    return dict(row)


@app.delete("/customers/all", tags=["Customers"])
def clear_all_customers():
    """Delete all rows from the customers table only."""
    with get_db() as conn:
        conn.execute("DELETE FROM customers")
    return {"cleared": "customers"}


@app.delete("/customers/{customer_id}", tags=["Customers"])
def delete_customer(customer_id: int):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Customer not found")
        conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    return {"deleted": customer_id}


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@app.get("/products", tags=["Products"])
def list_products():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, price, category, stock, created_at FROM products ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/products", tags=["Products"], status_code=201)
def create_product(product: ProductIn):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO products (name, price, category, stock) VALUES (?, ?, ?, ?)",
            (product.name, product.price, product.category, product.stock),
        )
        new_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, name, price, category, stock, created_at FROM products WHERE id = ?",
            (new_id,),
        ).fetchone()
    return dict(row)


@app.delete("/products/all", tags=["Products"])
def clear_all_products():
    """Delete all rows from the products table only."""
    with get_db() as conn:
        conn.execute("DELETE FROM products")
    return {"cleared": "products"}


@app.delete("/products/{product_id}", tags=["Products"])
def delete_product(product_id: int):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    return {"deleted": product_id}


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------

@app.get("/employees", tags=["Employees"])
def list_employees():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, name, phone, email, department, created_at FROM employees ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/employees", tags=["Employees"], status_code=201)
def create_employee(employee: EmployeeIn):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO employees (name, phone, email, department) VALUES (?, ?, ?, ?)",
            (employee.name, employee.phone, employee.email, employee.department),
        )
        new_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, name, phone, email, department, created_at FROM employees WHERE id = ?",
            (new_id,),
        ).fetchone()
    return dict(row)


@app.delete("/employees/all", tags=["Employees"])
def clear_all_employees():
    """Delete all rows from the employees table only."""
    with get_db() as conn:
        conn.execute("DELETE FROM employees")
    return {"cleared": "employees"}


@app.delete("/employees/{employee_id}", tags=["Employees"])
def delete_employee(employee_id: int):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM employees WHERE id = ?", (employee_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Employee not found")
        conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    return {"deleted": employee_id}


# ---------------------------------------------------------------------------
# Today's Report — multi-sheet Excel
# ---------------------------------------------------------------------------


@app.get("/report/today", tags=["Reports"])
def download_today_report():
    """
    Build an Excel workbook with two sheets — Customers and Products —
    populated with live data from SQLite.

    The file is named  today_report_YYYY-MM-DD.xlsx  and streamed back
    as a download so the browser saves it directly to Downloads.
    """
    today_str = date.today().strftime("%Y-%m-%d")

    with get_db() as conn:
        customers = conn.execute(
            "SELECT name, phone, email, status, created_at FROM customers ORDER BY id"
        ).fetchall()
        products = conn.execute(
            "SELECT name, price, category, stock, created_at FROM products ORDER BY id"
        ).fetchall()

    navy  = PatternFill("solid", fgColor="1A2340")
    green = PatternFill("solid", fgColor="1A5C36")
    white_bold = Font(bold=True, color="FFFFFF")
    center = Alignment(horizontal="center")

    def _write_sheet(ws, title_text, headers, rows, header_fill):
        """Write title row (row 1), header row (row 2), then data rows."""
        num_cols = len(headers)

        # Row 1 — merged title
        ws.cell(row=1, column=1, value=title_text)
        end_col_letter = openpyxl.utils.get_column_letter(num_cols)
        ws.merge_cells(f"A1:{end_col_letter}1")
        title_cell = ws["A1"]
        title_cell.font = Font(bold=True, size=13, color="1A2340")
        title_cell.alignment = center

        # Row 2 — column headers
        for col, h in enumerate(headers, start=1):
            cell = ws.cell(row=2, column=col, value=h)
            cell.fill = header_fill
            cell.font = white_bold
            cell.alignment = center

        # Data rows starting at row 3
        for r_idx, row in enumerate(rows, start=3):
            for c_idx, val in enumerate(row, start=1):
                ws.cell(row=r_idx, column=c_idx, value=val)

        # Auto-width (sample from header + data rows)
        for c_idx, h in enumerate(headers, start=1):
            col_letter = openpyxl.utils.get_column_letter(c_idx)
            max_len = len(str(h))
            for r_idx in range(3, 3 + len(rows)):
                v = ws.cell(row=r_idx, column=c_idx).value
                max_len = max(max_len, len(str(v or "")))
            ws.column_dimensions[col_letter].width = min(max_len + 4, 40)

    wb = openpyxl.Workbook()

    # ── Sheet 1: Customers ──────────────────────────────────────────────────
    ws_c = wb.active
    ws_c.title = "Customers"
    cust_data = [
        (r["name"], r["phone"], r["email"] or "", r["status"], r["created_at"])
        for r in customers
    ]
    _write_sheet(
        ws_c,
        f"Customer Report — {today_str}",
        ["Name", "Phone", "Email", "Status", "Created At"],
        cust_data,
        navy,
    )

    # ── Sheet 2: Products ───────────────────────────────────────────────────
    ws_p = wb.create_sheet("Products")
    prod_data = [
        (r["name"], r["price"], r["category"] or "", r["stock"], r["created_at"])
        for r in products
    ]
    _write_sheet(
        ws_p,
        f"Product Report — {today_str}",
        ["Name", "Price (₹)", "Category", "Stock", "Created At"],
        prod_data,
        green,
    )

    # ── Stream the workbook ─────────────────────────────────────────────────
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"today_report_{today_str}.xlsx"
    resp_headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=resp_headers,
    )


# ---------------------------------------------------------------------------
# UI Settings — Logo & Logo-change request
# ---------------------------------------------------------------------------

class LogoIn(BaseModel):
    data: str          # base64 data-URI  e.g. "data:image/png;base64,..."
    filename: Optional[str] = ""


class StyleIn(BaseModel):
    element: str       # "sidebar" | "header" | "body" | etc.
    color:   str       # any CSS color value


class BannerIn(BaseModel):
    text:    str
    bg_color: Optional[str] = "#e63946"
    text_color: Optional[str] = "#ffffff"


@app.get("/ui/logo", tags=["UI"])
def get_logo():
    """Return the saved logo data-URI, or null if none set."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM ui_settings WHERE key = 'logo'"
        ).fetchone()
    if row:
        return {"data": row["value"]}
    return None


@app.post("/ui/logo", tags=["UI"], status_code=201)
def save_logo(logo: LogoIn):
    """Save (or replace) the CRM logo as a base64 data-URI."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO ui_settings (key, value, updated_at)
            VALUES ('logo', ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value      = excluded.value,
                updated_at = excluded.updated_at
        """, (logo.data,))
    return {"saved": True}


@app.delete("/ui/logo", tags=["UI"])
def delete_logo():
    """Remove the custom logo (reverts to text logo)."""
    with get_db() as conn:
        conn.execute("DELETE FROM ui_settings WHERE key = 'logo'")
    return {"cleared": True}


# ── Logo-change request flag ─────────────────────────────────────────────
# The AI engine POSTs to /ui/logo-request to signal the CRM page that it
# should open the logo upload modal.  The CRM page polls GET every 2 s;
# once it opens the modal it DELETEs the flag.

@app.post("/ui/logo-request", tags=["UI"], status_code=201)
def request_logo_change():
    """Set the logo-change flag so the CRM page opens the upload modal."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO ui_settings (key, value, updated_at)
            VALUES ('logo_request', 'pending', datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value      = 'pending',
                updated_at = excluded.updated_at
        """)
    return {"requested": True}


@app.get("/ui/logo-request", tags=["UI"])
def get_logo_request():
    """Return whether a logo-change is pending."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM ui_settings WHERE key = 'logo_request'"
        ).fetchone()
    return {"pending": bool(row and row["value"] == "pending")}


@app.delete("/ui/logo-request", tags=["UI"])
def clear_logo_request():
    """Clear the logo-change flag after the CRM page has handled it."""
    with get_db() as conn:
        conn.execute("DELETE FROM ui_settings WHERE key = 'logo_request'")
    return {"cleared": True}


# ── UI Style (sidebar color, header background, etc.) ────────────────────────

@app.get("/ui/styles", tags=["UI"])
def get_styles():
    """Return all saved element styles as a dict {element: color}."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT key, value FROM ui_settings WHERE key LIKE 'style_%'"
        ).fetchall()
    return {row["key"].replace("style_", "", 1): row["value"] for row in rows}


@app.post("/ui/style", tags=["UI"], status_code=201)
def save_style(style: StyleIn):
    """Persist an element's background color (e.g. sidebar → blue)."""
    key = f"style_{style.element.lower()}"
    with get_db() as conn:
        conn.execute("""
            INSERT INTO ui_settings (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value      = excluded.value,
                updated_at = excluded.updated_at
        """, (key, style.color))
    return {"saved": True, "element": style.element, "color": style.color}


@app.delete("/ui/style/{element}", tags=["UI"])
def delete_style(element: str):
    """Remove a saved element style (revert to CSS default)."""
    key = f"style_{element.lower()}"
    with get_db() as conn:
        conn.execute("DELETE FROM ui_settings WHERE key = ?", (key,))
    return {"cleared": element}


# ── UI Banner (persistent top-of-page announcement) ─────────────────────────

@app.get("/ui/banner", tags=["UI"])
def get_banner():
    """Return the saved announcement banner, or null if none."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM ui_settings WHERE key = 'banner'"
        ).fetchone()
    if row:
        import json as _json
        try:
            return _json.loads(row["value"])
        except Exception:
            return {"text": row["value"], "bg_color": "#e63946", "text_color": "#ffffff"}
    return None


@app.post("/ui/banner", tags=["UI"], status_code=201)
def save_banner(banner: BannerIn):
    """Persist an announcement banner."""
    import json as _json
    payload = _json.dumps({
        "text":       banner.text,
        "bg_color":   banner.bg_color,
        "text_color": banner.text_color,
    })
    with get_db() as conn:
        conn.execute("""
            INSERT INTO ui_settings (key, value, updated_at)
            VALUES ('banner', ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value      = excluded.value,
                updated_at = excluded.updated_at
        """, (payload,))
    return {"saved": True}


@app.delete("/ui/banner", tags=["UI"])
def delete_banner():
    """Remove the announcement banner."""
    with get_db() as conn:
        conn.execute("DELETE FROM ui_settings WHERE key = 'banner'")
    return {"cleared": True}


# ---------------------------------------------------------------------------
# Active Offer Banner
# ---------------------------------------------------------------------------

class OfferIn(BaseModel):
    banner_text:  str
    offer_scope:  Optional[str] = "all"
    products:     Optional[str] = ""   # comma-separated product names


@app.get("/offer", tags=["Offer"])
def get_offer():
    """Return the currently active offer banner, or null if none."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT banner_text, offer_scope, products, created_at FROM active_offer WHERE id = 1"
        ).fetchone()
    if row:
        return dict(row)
    return None


@app.post("/offer", tags=["Offer"], status_code=201)
def set_offer(offer: OfferIn):
    """Create or replace the active offer banner (only one at a time)."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO active_offer (id, banner_text, offer_scope, products, created_at)
            VALUES (1, ?, ?, ?, datetime('now'))
            ON CONFLICT(id) DO UPDATE SET
                banner_text = excluded.banner_text,
                offer_scope = excluded.offer_scope,
                products    = excluded.products,
                created_at  = excluded.created_at
        """, (offer.banner_text, offer.offer_scope, offer.products))
    return {"saved": True}


@app.delete("/offer", tags=["Offer"])
def clear_offer():
    """Remove the active offer banner."""
    with get_db() as conn:
        conn.execute("DELETE FROM active_offer WHERE id = 1")
    return {"cleared": True}


# ---------------------------------------------------------------------------
# Danger zone — wipe all data
# ---------------------------------------------------------------------------

@app.delete("/data/all", tags=["System"])
def clear_all_data():
    """Delete every row from all tables. Matches the CRM 'Clear All Data' button."""
    with get_db() as conn:
        conn.execute("DELETE FROM customers")
        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM employees")
        conn.execute("DELETE FROM active_offer")
    return {"cleared": True}


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.services.crm_service:app", host="0.0.0.0", port=8001, reload=True)
