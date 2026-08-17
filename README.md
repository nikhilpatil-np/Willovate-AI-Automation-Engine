# Willovate AI Automation Engine

**AI-powered system that converts natural-language instructions into executable automation workflows.**

> Author: **Nikhil Patil** — AI/ML Engineer Intern, Willovate Pvt. Ltd.

---

## Final Demo Command

```
Open the CRM, add Pankaj Koche as a customer with phone number 9876543210,
save the record and verify that the customer appears in the table.
```

**Result:**

```json
{
  "intent": "add_customer",
  "steps": [
    { "action": "OPEN_PAGE",     "target": "customers" },
    { "action": "ENTER_TEXT",    "target": "customer-name",  "value": "Pankaj Koche" },
    { "action": "ENTER_TEXT",    "target": "phone-number",   "value": "9876543210" },
    { "action": "CLICK",         "target": "add-customer" },
    { "action": "CLICK",         "target": "save" },
    { "action": "READ_TABLE",    "target": "customer-table" },
    { "action": "VERIFY_RECORD", "target": "customer-table", "value": "Pankaj Koche" }
  ]
}
```

**Execution:** 7/7 steps ✅ — Success: True — Verification: True

---

## How to Run

```powershell
cd c:\willovate\Willovate-AI-Automation-Engine

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Start the server
uvicorn main:app --port 8000
```

Open **http://127.0.0.1:8000** in your browser.

API docs: **http://127.0.0.1:8000/docs**

---

## Project Overview

The Willovate AI Automation Engine is a full AI/ML pipeline that:

1. Accepts a natural-language instruction (English, Hindi, Hinglish)
2. Detects the intent using a trained ML model
3. Extracts entities (name, phone, email, price, file)
4. Detects missing required information
5. Assesses risk level (LOW / MEDIUM / HIGH)
6. Generates a clean, ordered workflow JSON
7. Validates the workflow against a JSON schema
8. Checks for hallucinations and unsupported actions
9. Executes the workflow on a real web app using Playwright
10. Verifies the result in the browser

---

## Quick Example

**Input:**
```
Add Rahul with phone number 9876543210 as a customer.
```

**Generated Workflow:**
```json
{
  "intent": "add_customer",
  "steps": [
    { "action": "OPEN_PAGE",  "target": "customers" },
    { "action": "ENTER_TEXT", "target": "customer-name", "value": "Rahul" },
    { "action": "ENTER_TEXT", "target": "phone-number",  "value": "9876543210" },
    { "action": "CLICK",      "target": "add-customer" },
    { "action": "CLICK",      "target": "save" }
  ]
}
```

---

## Architecture

```
User Instruction (English / Hindi / Hinglish)
        ↓
Language Normalizer
        ↓
Intent Detection  (TF-IDF + Logistic Regression)
        ↓
Entity Extraction  (Regex pipeline)
        ↓
Missing Info Detection
        ↓
Risk Detection
        ↓
Multi-Step Planner  →  Workflow JSON
        ↓
JSON Schema Validator
        ↓
Hallucination Detector
        ↓
Browser Runner (Playwright)
        ↓
CRM Web Application
        ↓
Table Verification
        ↓
Final Result
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/generate-workflow` | Generate workflow from instruction (Stage 1) |
| POST | `/api/v1/execute` | Full execution — pipeline + browser (Stage 1+2+3) |
| POST | `/api/v1/normalize` | Language detection and normalization |
| POST | `/api/v1/detect-intent` | Intent detection only |
| POST | `/api/v1/multi-step-plan` | Multi-step planning only |
| GET  | `/api/v1/health` | Server health and model status |

---

## Supported Intents (14)

| Intent | Example |
|--------|---------|
| ADD_CUSTOMER | Add Rahul as customer |
| UPDATE_CUSTOMER | Update Rahul's phone |
| DELETE_CUSTOMER | Delete customer Amit |
| UPDATE_PRODUCT | Change price to 599 |
| UPDATE_EMPLOYEE | Update employee record |
| DELETE_EMPLOYEE | Remove employee |
| DOWNLOAD_REPORT | Download today's report |
| UPLOAD_FILE | Upload invoice.pdf |
| READ_TABLE | Read customer list |
| SEND_EMAIL | Send email to manager |
| FILL_FORM | Fill the contact form |
| OPEN_PAGE | Open settings page |
| CLICK_BUTTON | Click the submit button |
| TAKE_SCREENSHOT | Take a screenshot |

---

## Supported Actions

| Action | Description |
|--------|-------------|
| OPEN_PAGE | Navigate to a page |
| CLICK | Click a button or link |
| ENTER_TEXT | Type into an input field |
| SELECT_OPTION | Select from a dropdown |
| UPLOAD_FILE | Upload a file |
| DOWNLOAD_FILE | Download a file |
| READ_TABLE | Read data from a table |
| READ_TEXT | Read text from the page |
| SCROLL | Scroll the page |
| WAIT | Wait for a given time |
| SUBMIT | Submit a form |
| TAKE_SCREENSHOT | Capture the current page |
| VERIFY_RECORD | Verify a record exists in a table |
| SEND_EMAIL | Send an email |

---

## Model

| Property | Value |
|----------|-------|
| Algorithm | TF-IDF + Logistic Regression |
| Dataset | 251 labelled instructions |
| Languages | English, Hindi, Hinglish |
| Accuracy | 82.93% |
| Intents | 14 classes |
| Licence | scikit-learn (BSD) |

Full evaluation report: `outputs/evaluation/model_evaluation_report.txt`

---

## Project Structure

```
Willovate-AI-Automation-Engine/
├── main.py                          ← FastAPI entry point
├── frontend/
│   └── index.html                   ← Web UI
├── app/
│   ├── api/
│   │   ├── routes.py
│   │   └── nl_pipeline.py
│   ├── config/
│   │   └── settings.py
│   ├── core/
│   │   ├── language_normalizer.py   ← EN/Hindi/Hinglish normalization
│   │   ├── intent_detector.py       ← Keyword fallback intent detector
│   │   ├── entity_extractor.py      ← Regex entity extraction
│   │   ├── missing_information.py   ← Missing field detection
│   │   ├── risk_detector.py         ← LOW/MEDIUM/HIGH risk
│   │   ├── multi_step_planner.py    ← Workflow generation
│   │   ├── hallucination_detector.py← Unsupported action check
│   │   └── error_detector.py        ← Error message analysis
│   ├── models/
│   │   ├── train_intent_model.py
│   │   ├── train_entity_model.py
│   │   ├── test_intent_model.py
│   │   └── evaluate_models.py
│   ├── schemas/
│   │   └── workflow.schema.json
│   ├── services/
│   │   ├── orchestrator.py          ← Main pipeline coordinator
│   │   └── model_server.py          ← ML model wrapper
│   └── utils/
│       ├── validator.py             ← JSON schema validation
│       └── logger.py
├── automation/
│   ├── browser_runner.py            ← Playwright executor
│   ├── crm.html                     ← Sample CRM web app
│   └── workflow.json                ← Demo workflow
├── data/
│   ├── raw/training_dataset.csv
│   ├── processed/
│   │   ├── intent_dataset.csv
│   │   └── entity_dataset.csv
│   └── samples/
│       ├── workflows/sample_workflows.json
│       └── screenshots/
├── models/
│   └── intent_model.pkl
├── outputs/
│   ├── intent_detection/
│   │   ├── accuracy.txt
│   │   └── classification_report.txt
│   └── evaluation/
│       └── model_evaluation_report.txt
├── docs/
│   └── architecture.md
└── screenshots/
    ├── day2/
    ├── day3/
    └── 



---

## 9-Day Progress

| Day | Branch | Work Completed |
|-----|--------|----------------|
| Day 1 | day-1-project-setup | Project structure, venv, config, Git setup |
| Day 2 | day-2-intent-detection | Intent detection dataset, TF-IDF + LR model, 82.93% accuracy |
| Day 3 | day-3-entity-extraction | Entity extraction (name, phone, email, price, file), missing info detection |
| Day 4 | day-4-workflow-validation-risk | Workflow validation, JSON schema, risk detection (LOW/MEDIUM/HIGH) |
| Day 5 | day-5-multi-step-planning | Multi-step workflow planning, compound instruction handling |
| Day 6 | day-6-action-ui-mapping | Action prediction, UI element mapping (button/input/dropdown/table) |
| Day 7 | day-7-screenshot-understanding | Screenshot analyzer, OCR, UI region detection, error detection |
| Day 8 | day-8-browser-automation | Playwright browser runner, CRM automation, table verification |
| Day 9 | day-9-final-integration | Full pipeline integration, frontend UI, evaluation report, final demo |

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Backend | Python, FastAPI, Uvicorn |
| ML/NLP | scikit-learn, TF-IDF, Logistic Regression |
| Automation | Playwright, Chromium |
| Validation | jsonschema |
| Frontend | HTML, CSS, JavaScript (single file) |
| Data | pandas, CSV |

---

## Evaluation Summary (Day 9)

| Metric | Result |
|--------|--------|
| Intent accuracy | 82.93% |
| Entity extraction | ~97% |
| Workflow JSON validity | 100% |
| Missing info detection | 100% |
| Risk classification | 3 levels — working |
| Hinglish support | Yes |
| Hallucination rate | 0% |
| End-to-end demo | PASS ✅ |

---

## MVP Deliverables Checklist

| Deliverable | Status |
|-------------|--------|
| Natural-language instruction API | ✅ |
| Intent and entity extraction | ✅ |
| Workflow JSON generation | ✅ |
| Missing-information questions | ✅ |
| English and Hinglish support | ✅ |
| Screenshot understanding | ✅ |
| Multi-step workflow planning | ✅ |
| Risk classification | ✅ |
| Error analysis | ✅ |
| Training dataset | ✅ |
| Model evaluation report | ✅ |
| Fine-tuned / optimized open-source model | ✅ (TF-IDF + LR) |
| Working demo on sample web application | ✅ |
