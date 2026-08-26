# Willovate AI Automation Engine — System Architecture

## Overview

The engine runs as two independent processes that communicate over HTTP:

- **AI Engine** (port 8000) — FastAPI app that handles all NLP, workflow generation, and orchestration
- **CRM Backend** (port 8001) — FastAPI app that manages SQLite persistence and serves the CRM REST API

---

## End-to-End Request Flow

```
User (browser or API client)
        │
        │  POST /api/v1/execute
        │  { "instruction": "Add Pankaj Koche as customer with phone 9876543210 and save" }
        ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI Engine  (port 8000)                    │
│                       main.py                               │
│                                                             │
│  FastAPI route  →  orchestrator.execute_instruction()       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Stage 1: NL Pipeline                   │   │
│  │                                                     │   │
│  │  1. language_normalizer.normalize_with_meta()       │   │
│  │     "Pankaj Koche naam ka..." → "add customer ..." │   │
│  │     detected_language: en | hi | hinglish           │   │
│  │                                                     │   │
│  │  2. model_server.predict_intent()                   │   │
│  │     keyword rules first → ML model (TF-IDF+LR)     │   │
│  │     → "ADD_CUSTOMER"                                │   │
│  │                                                     │   │
│  │  3. entity_extractor.extract_entities()             │   │
│  │     regex pipeline on original text                 │   │
│  │     → { name: "Pankaj Koche", phone: "9876543210" } │   │
│  │                                                     │   │
│  │  4. missing_information.detect_missing_information()│   │
│  │     checks required fields per intent               │   │
│  │     → []  (nothing missing)                         │   │
│  │                                                     │   │
│  │  5. risk_detector.detect_risk()                     │   │
│  │     keyword scan for HIGH/MEDIUM/LOW                │   │
│  │     → { risk_level: "LOW" }                         │   │
│  │                                                     │   │
│  │  6. multi_step_planner.plan_multi_step()            │   │
│  │     rule-based step builder using real HTML IDs     │   │
│  │     → workflow JSON  (7 steps)                      │   │
│  │                                                     │   │
│  │  7. validator.validate_workflow()                   │   │
│  │     JSON schema check (workflow.schema.json)        │   │
│  │     → valid: true                                   │   │
│  │                                                     │   │
│  │  8. hallucination_detector.detect_hallucinations()  │   │
│  │     unsupported-action check + grounding check      │   │
│  │     → hallucination_rate: 0%                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Stage 2: Browser Execution             │   │
│  │                                                     │   │
│  │  browser_runner.execute_workflow()                  │   │
│  │    │                                                │   │
│  │    ├─ auto-starts CRM backend on port 8001          │   │
│  │    │  (subprocess uvicorn if not already running)   │   │
│  │    │                                                │   │
│  │    └─ Playwright (Chromium, headless or visible)    │   │
│  │         opens crm.html via http://127.0.0.1:8001    │   │
│  │         executes each workflow step:                │   │
│  │           OPEN_PAGE   → navigate('customers')       │   │
│  │           ENTER_TEXT  → page.fill('#customerName')  │   │
│  │           ENTER_TEXT  → page.fill('#phoneNumber')   │   │
│  │           CLICK       → page.click('#addCustomer')  │   │
│  │           CLICK       → page.click('#saveCustomer') │   │
│  │           READ_TABLE  → reads #customerTableBody    │   │
│  │           VERIFY_RECORD → finds "Pankaj Koche" row  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Stage 3: Result                        │   │
│  │                                                     │   │
│  │  {                                                  │   │
│  │    "intent": "ADD_CUSTOMER",                        │   │
│  │    "entities": { "name": "Pankaj Koche", ... },     │   │
│  │    "risk": { "risk_level": "LOW" },                 │   │
│  │    "workflow": { "steps": [ ... ] },                │   │
│  │    "valid": true,                                   │   │
│  │    "execution": {                                   │   │
│  │      "success": true,                               │   │
│  │      "steps_executed": 7,                           │   │
│  │      "verification": true                           │   │
│  │    }                                                │   │
│  │  }                                                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
        │
        │  (browser_runner calls CRM API directly for
        │   DELETE, CLEAR_ALL, OFFER, STYLE, BANNER actions)
        ▼
┌──────────────────────────────────────────────────┐
│             CRM Backend  (port 8001)             │
│             app/services/crm_service.py          │
│                                                  │
│  SQLite  ←→  FastAPI CRUD endpoints              │
│  data/crm.db                                     │
│                                                  │
│  /customers      GET, POST, DELETE/{id}          │
│  /products       GET, POST, DELETE/{id}          │
│  /employees      GET, POST, DELETE/{id}          │
│  /report/today   GET  (multi-sheet Excel)        │
│  /ui/logo        GET, POST                       │
│  /ui/styles      GET, POST                       │
│  /ui/banner      GET, POST                       │
│  /offer          GET, POST                       │
│  /data/all       DELETE  (⚠ wipes all tables)    │
└──────────────────────────────────────────────────┘
        ▲
        │  polls every 2–5 s for UI updates
        │  (logo-request, styles, banner, offer)
        ▼
┌──────────────────────────────────────────────────┐
│            CRM Web App  (automation/crm.html)    │
│                                                  │
│  Vanilla JS SPA served by the CRM backend        │
│  Pages: Customers │ Products │ Reports │ Upload  │
│                                                  │
│  Displays live data from /customers, /products   │
│  Applies AI-driven style/logo/banner changes     │
└──────────────────────────────────────────────────┘
```

---

## Module Map

```
Willovate-AI-Automation-Engine/
│
├── main.py                        FastAPI entry point, all API routes
│
├── app/
│   ├── config/
│   │   └── settings.py            Project constants (name, version, ports, limits)
│   │
│   ├── core/                      Pure NLP / AI modules (no I/O side effects)
│   │   ├── language_normalizer.py  EN / Hindi / Hinglish → clean English
│   │   ├── intent_detector.py      Keyword-based fallback intent classifier
│   │   ├── entity_extractor.py     Regex pipeline (name, phone, email, price, …)
│   │   ├── missing_information.py  Required-field checker per intent
│   │   ├── risk_detector.py        LOW / MEDIUM / HIGH risk classifier
│   │   ├── multi_step_planner.py   Workflow step builder (maps to real HTML IDs)
│   │   ├── hallucination_detector.py  Unsupported-action + grounding checks
│   │   ├── action_predictor.py     Lightweight action-list predictor (utility)
│   │   ├── error_detector.py       Error keyword scanner (used by browser_runner)
│   │   └── screenshot_understanding.py  OCR + CV region detection (optional deps)
│   │
│   ├── services/
│   │   ├── orchestrator.py         Pipeline coordinator — chains all 8 NLP steps
│   │   ├── model_server.py         ML model wrapper / singleton (intent_model.pkl)
│   │   └── crm_service.py          CRM FastAPI app + SQLite CRUD (port 8001)
│   │
│   ├── schemas/
│   │   └── workflow.schema.json    JSON Schema for workflow validation
│   │
│   └── utils/
│       ├── validator.py            validate_workflow() via jsonschema
│       └── logger.py               Logging config (level from settings.py)
│
├── automation/
│   ├── browser_runner.py           Playwright executor — all action handlers
│   ├── crm.html                    CRM single-page web application
│   └── workflow.json               Static demo workflow (reference)
│
├── frontend/
│   └── index.html                  AI Engine UI (pipeline analysis + execution)
│
├── models/
│   └── intent_model.pkl            Trained TF-IDF + Logistic Regression pipeline
│
├── data/
│   ├── raw/training_dataset.csv
│   └── processed/
│       ├── intent_dataset.csv      251 labelled instructions (14 intent classes)
│       └── entity_dataset.csv      Entity extraction evaluation set
│
├── app/models/                     Training and evaluation scripts
│   ├── train_intent_model.py
│   ├── test_intent_model.py
│   └── evaluate_models.py          8-metric evaluation (accuracy, hallucination, …)
│
├── outputs/
│   ├── evaluation_report.json
│   └── evaluation/
│       └── model_evaluation_report.txt
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── docs/
│   ├── architecture.md             ← this file
│   ├── README.md
│   ├── END_TO_END_PROJECT_PLAN.md
│   └── project.txt
│
└── requirements.txt
```

---

## Intent Model

| Property | Value |
|----------|-------|
| Algorithm | TF-IDF + Logistic Regression (sklearn Pipeline) |
| Training samples | 251 labelled instructions |
| Intent classes | 14 |
| Languages | English, Hindi (Devanagari), Hinglish |
| Accuracy | 82.93% |
| Fallback | Keyword-based IntentDetector (always runs first) |
| Strategy | Hybrid — keywords take priority, ML handles unseen phrasing |

---

## Supported Intent Classes

| Intent | Trigger example |
|--------|----------------|
| ADD_CUSTOMER | "Add Rahul as customer" |
| DELETE_CUSTOMER | "Delete customer Amit" |
| ADD_PRODUCT | "Add Laptop with price 45000" |
| UPDATE_PRODUCT | "Change product price to 599" |
| DELETE_PRODUCT | "Remove product Laptop" |
| ADD_EMPLOYEE | "Add employee Ravi" |
| DELETE_EMPLOYEE | "Remove employee Ravi" |
| DOWNLOAD_REPORT | "Download today's report" |
| UPLOAD_FILE | "Upload invoice.pdf" |
| SEND_EMAIL | "Send email to manager" |
| TAKE_SCREENSHOT | "Take a screenshot" |
| ADD_OFFER | "Add offer 20% off on Laptop" |
| CHANGE_WEB | "Change header color to blue" |
| UNKNOWN | anything not matched |

---

## Risk Classification

| Level | Triggers | Confirmation required |
|-------|----------|----------------------|
| HIGH | delete all, drop database, wipe, purge all | Yes — blocked until `confirmed: true` |
| MEDIUM | delete, update, change password, send email, reset | Yes — user warned |
| LOW | add, read, screenshot, download | No |

---

## Workflow Action Types

| Action | Description |
|--------|-------------|
| OPEN_PAGE | Navigate to a named CRM page |
| CLICK | Click a button by CSS selector |
| ENTER_TEXT | Fill an input field |
| SELECT_OPTION | Choose from a dropdown |
| READ_TABLE | Read all rows from a table body |
| VERIFY_RECORD | Assert a named record exists in a table |
| DELETE_RECORD | Delete a record by name via the CRM API |
| CLEAR_ALL | Wipe an entire table via the CRM API |
| UPLOAD_FILE | Upload a file via file input |
| DOWNLOAD_FILE | Download a file (CSV / Excel) |
| TAKE_SCREENSHOT | Save a full-page screenshot |
| SCROLL | Scroll the page up or down |
| WAIT | Pause for N seconds |
| SEND_EMAIL | Send an email (logged, not executed) |
| CHANGE_LOGO | Signal the CRM to open the logo-upload modal |
| CHANGE_STYLE | Inject CSS change via page.evaluate + persist to /ui/style |
| ADD_BANNER | Inject a notification banner + persist to /ui/banner |
| OFFER_BANNER | Inject a product-offer banner + persist to /offer |
| CHANGE_TEXT | Update a text element on the CRM page |
