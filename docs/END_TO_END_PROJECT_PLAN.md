# Willovate AI Automation Engine

## 1. Project Objective

This project aims to build an AI-powered automation engine that reads a natural-language instruction, understands the user’s goal, extracts important values, builds a valid workflow, executes the workflow on a web application, and returns the final result with verification.

This matches the requirement in the project brief and follows the same idea as UiPath-style process automation, but with AI-driven workflow generation.

Example instruction:

> Open the CRM, add Pankaj Koche as a customer with phone number 9876543210, save the record and verify that the customer appears in the table.

Expected behavior:

- Detect intent: add customer
- Extract entities: name, phone number
- Generate workflow JSON
- Validate workflow
- Execute workflow in browser
- Verify result in UI table
- Return success/failure result

---

## 2. Overall Architecture

The end-to-end system should be built as a pipeline:

```mermaid
flowchart LR
    A[User instruction] --> B[Language normalization]
    B --> C[Intent detection]
    C --> D[Entity extraction]
    D --> E[Missing info detection]
    E --> F[Risk detection]
    F --> G[Multi-step planner]
    G --> H[Workflow validator]
    H --> I[Hallucination check]
    I --> J[Workflow JSON]
    J --> K[Browser automation runner]
    K --> L[Web app execution]
    L --> M[Verification + final result]
```

### Core components

1. Input layer
   - REST API using FastAPI
   - Accepts English, Hindi, and Hinglish instructions

2. AI processing layer
   - intent detection
   - entity extraction
   - missing information detection
   - risk classification
   - workflow generation
   - validation and safety checks

3. Automation layer
   - Playwright-based browser runner
   - executes generated steps
   - reads UI elements and verifies state

4. Output layer
   - workflow JSON
   - execution result
   - verification status
   - error detection and retry suggestions

---

## 3. What this project already has

The repository already contains a strong starting structure for the MVP:

- API layer: app/api/nl_pipeline.py
- Pipeline orchestrator: app/services/orchestrator.py
- Workflow generation: app/core/workflow_generator.py
- Entity extraction: app/core/entity_extractor.py
- Missing information detection: app/core/missing_information.py
- Risk detection: app/core/risk_detector.py
- Multi-step planning: app/core/multi_step_planner.py
- Validation: app/utils/validator.py
- Browser automation: automation/browser_runner.py
- Sample CRM app: automation/crm.html

This means the project is already close to a working prototype. The next step is to convert this prototype into a production-quality MVP with stronger model evaluation, multilingual support, and robust execution verification.

---

## 4. End-to-End Implementation Flow

### Stage 1: Understand the instruction

The system should accept a raw command such as:

> Add Rahul with phone number 9876543210 as a customer in the CRM.

Then it should do the following:

1. Detect the language
   - English
   - Hindi
   - Hinglish

2. Normalize text
   - convert slang or mixed-language input into standard English
   - example: “Rahul naam ka employee add karo” → “Add employee named Rahul”

3. Detect intent
   - add_customer
   - update_product
   - download_report
   - fill_form
   - upload_file
   - read_table
   - send_email

4. Extract entities
   - customer name
   - phone number
   - email
   - product name
   - price
   - date
   - file name 
   
   - page name

5. Detect missing information
   - if the instruction says “Create a customer” and no name or phone is provided, ask the user to provide them

6. Detect risk level
   - low: simple data entry
   - medium: report generation, updates
   - high: delete records, payment, account changes

### Stage 2: Generate workflow

Once intent and entities are known, generate a structured workflow in JSON:

```json
{
  "steps": [
    {"action": "OPEN_PAGE", "target": "customers"},
    {"action": "CLICK", "target": "add-customer"},
    {"action": "ENTER_TEXT", "target": "customer-name", "value": "Rahul"},
    {"action": "ENTER_TEXT", "target": "phone-number", "value": "9876543210"},
    {"action": "CLICK", "target": "save"},
    {"action": "READ_TABLE", "target": "customer-table"}
  ]
}
```

The workflow generator must:

- preserve order of actions
- support multi-step instructions
- reject unsupported actions
- produce valid JSON

### Stage 3: Validate workflow

Before execution, validate:

- JSON is valid
- actions are supported
- required parameters exist
- target names match UI objects
- step order is logical
- risky actions require confirmation

### Stage 4: Execute workflow in browser

The automation runner uses Playwright to open a web app and run each step:

- OPEN_PAGE
- CLICK
- ENTER_TEXT
- SELECT_OPTION
- UPLOAD_FILE
- DOWNLOAD_FILE
- READ_TABLE
- SCROLL
- WAIT
- SUBMIT
- TAKE_SCREENSHOT

The runner should:

- open the target page
- interact with buttons, input fields, dropdowns, tables
- wait for page state
- capture screenshots on failure or success
- track each step result

### Stage 5: Verify final outcome

For instructions that require confirmation, like:

> verify that the customer appears in the table

the runner must:

- read the table
- compare values with expected entity values
- mark success only if the expected record is found

This is the most important part of real-world automation reliability.

---

## 5. Technical Design

### API design

Use FastAPI endpoints similar to the current project:

- POST /api/v1/generate-workflow
- POST /api/v1/execute
- POST /api/v1/normalize
- POST /api/v1/detect-intent
- POST /api/v1/multi-step-plan
- GET /api/v1/health

### Suggested request format

```json
{
  "instruction": "Open the CRM, add Pankaj Koche as a customer with phone number 9876543210, save the record and verify that the customer appears in the table.",
  "lang": "auto",
  "headless": true
}
```

### Suggested response format

```json
{
  "intent": "add_customer",
  "entities": {
    "name": "Pankaj Koche",
    "phone": "9876543210"
  },
  "missing": [],
  "risk": {
    "risk_level": "LOW",
    "requires_confirmation": false
  },
  "workflow": {
    "steps": [
      {"action": "OPEN_PAGE", "target": "crm"},
      {"action": "CLICK", "target": "add-customer"},
      {"action": "ENTER_TEXT", "target": "customer-name", "value": "Pankaj Koche"},
      {"action": "ENTER_TEXT", "target": "phone-number", "value": "9876543210"},
      {"action": "CLICK", "target": "save"},
      {"action": "READ_TABLE", "target": "customer-table"}
    ]
  },
  "execution": {
    "success": true,
    "verification": true
  }
}
```

---

## 6. Model Strategy

### 6.1 Intent detection

Use a lightweight multilingual model or hybrid model:

- TF-IDF + Logistic Regression for fast MVP
- DistilBERT / XLM-RoBERTa for stronger multilingual support
- Fine-tune on Willovate’s dataset

Recommended approach:

1. Start with TF-IDF + Logistic Regression for baseline
2. Then evaluate DistilBERT / XLM-R
3. Select the best model based on accuracy and latency
4. Fine-tune using domain-specific datasets

### 6.2 Entity extraction

Use:

- rule-based extraction for phone, email, dates, price
- NER model for name / product / page names
- custom extraction pipeline for Hindi and Hinglish mixed text

### 6.3 Multilingual support

The project requirement explicitly demands:

- English
- Hindi
- Hinglish

This should be handled with:

- language normalization
- translation or canonicalization layer
- multilingual intent model
- entity extraction with transliteration support

Examples:

- “Add a new employee”
- “Rahul naam ka employee add karo.”
- “Product ka price ₹599 kar do.”

---

## 7. Data Strategy

The project must include a real training dataset with examples from multiple formats.

### Dataset fields

- user instruction
- expected intent
- extracted entities
- expected workflow
- missing fields
- risk level
- language type
- notes for ambiguity or spelling mistakes

### Include data variations

- English instructions
- Hindi instructions
- Hinglish instructions
- spelling mistakes
- incomplete commands
- compound instructions
- multi-step tasks

Example row:

```json
{
  "instruction": "Rahul ka phone 9876543210 se customer add karo",
  "intent": "add_customer",
  "entities": {"name": "Rahul", "phone": "9876543210"},
  "expected_workflow": ["OPEN_PAGE", "CLICK", "ENTER_TEXT", "ENTER_TEXT", "CLICK"],
  "missing_fields": [],
  "risk_level": "LOW",
  "language": "hinglish"
}
```

---

## 8. Validation and Safety Rules

The workflow must not be executed blindly.

### Workflow validation checklist

- JSON is valid
- action is in allowed list
- target is present
- values are filled where required
- sequence is logical
- no unsupported action names
- risky steps require confirmation

### Risk examples

- delete records
- update multiple records
- submit payments
- change account settings

High-risk instructions should be blocked or require manual approval before execution.

---

## 9. Error Handling and Recovery

A production pipeline should not fail silently.

### Error handling strategy

1. Detect UI failure
2. Identify failed step and action
3. Read error text from page or logs
4. Suggest alternative action
5. Retry when safe
6. Stop for critical failures

This is essential because automation often fails due to element timing, page state, or changed selectors.

---

## 10. Evaluation Plan

The project requirement includes specific evaluation metrics. These should be measured for every sprint.

### Required metrics

- Intent accuracy
- Entity extraction accuracy
- Workflow generation accuracy
- JSON validity rate
- Missing information detection accuracy
- Hinglish accuracy
- Unsupported action rate
- Hallucination rate

### Evaluation methods

- hold-out test set
- confusion matrix for intent
- exact match / partial match for entities
- schema validation for workflow JSON
- human review for ambiguous tasks

---

## 11. MVP Deliverables

The MVP should include:

- natural-language instruction API
- intent and entity extraction
- workflow JSON generation
- missing-information questions
- English and Hinglish support
- screenshot understanding
- multi-step workflow planning
- risk classification
- error analysis
- training dataset
- model evaluation report
- fine-tuned or optimized open-source model
- demo on one sample CRM web app

---

## 12. Recommended Implementation Roadmap

### Phase 1: Core AI pipeline

- Build NLP normalization
- Integrate intent detection model
- Build entity extraction logic
- Add missing information detection
- Add custom workflow generation
- Add schema validation

### Phase 2: Execution engine

- Connect Playwright browser runner
- Support key actions like CLICK, ENTER_TEXT, READ_TABLE
- Add verification step for record existence
- Add screenshot and error handling

### Phase 3: Safety and quality

- Add risk detection
- Add high-risk confirmation flow
- Add hallucination detection
- Add unsupported workflow rejection

### Phase 4: Multilingual and training

- Expand dataset with Hindi and Hinglish examples
- Improve entity recognition
- Fine-tune open-source multilingual model
- Measure and improve metrics

### Phase 5: Demo and polish

- Finalize API endpoints
- Build sample CRM demo
- Provide one end-to-end scenario
- Record demonstration output

---

## 13. Demo flow for the final system

A final demonstration should run like this:

1. User sends instruction:
   > Open the CRM, add Pankaj Koche as a customer with phone number 9876543210, save the record and verify that the customer appears in the table.

2. System responds with:
   - detected language
   - intent
   - extracted entities
   - risk level
   - generated workflow JSON

3. System executes the browser automation:
   - opens CRM
   - clicks Add Customer
   - fills name and phone number
   - saves the record
   - reads customer table
   - verifies the matching record

4. Final result:
   - success: true
   - verification: true
   - record found in table

---

## 14. Recommended stack

### Backend

- Python
- FastAPI
- Pydantic

### AI / ML

- scikit-learn
- TF-IDF
- Logistic Regression
- transformers
- sentence-transformers
- multilingual model such as XLM-R or DistilBERT

### Automation

- Playwright
- Chromium

### Data and validation

- pandas
- jsonschema
- CSV/JSON dataset pipelines

---

## 15. Practical approach to achieve this project

The best way to achieve the project successfully is to build it in layers rather than trying to build everything at once.

### Recommended delivery model

1. Build the NLP layer first
   - normalize text
   - detect intent
   - extract entities

2. Build the workflow layer next
   - create workflow schema
   - create action list
   - validate workflow output

3. Build the browser automation runner
   - handle core actions
   - verify UI output
   - ensure stable selectors

4. Connect everything in an orchestrator
   - one API entry point
   - sequence all modules

5. Add safety and evaluation
   - risk detection
   - error analysis
   - metrics and dataset improvements

6. Fine-tune the model
   - use collected domain data
   - improve multilingual coverage
   - compare model performance

This is the realistic route to a working end-to-end system in the current codebase.

---

## 16. Final outcome

The final product should be an AI automation system that can:

- understand natural-language instructions
- extract key data from text
- generate valid automation workflow JSON
- validate safety and correctness
- execute automation in a browser
- verify the outcome on the actual page
- return a final result to the user

This is the real end-to-end automation engine described in the project requirement file and is achievable by combining the current repository structure with a disciplined AI + automation pipeline approach.

---

## 17. Recommended next steps for this repository

1. Review and clean the dataset for Hindi and Hinglish training examples
2. Improve intent model accuracy with a multilingual model baseline
3. Expand workflow validation rules and action support
4. Add robust browser verification for table and form operations
5. Add evaluation scripts and model comparison reports
6. Finalize one end-to-end CRM demo scenario

That will turn the project from a prototype into a real MVP aligned with the requirement brief.
