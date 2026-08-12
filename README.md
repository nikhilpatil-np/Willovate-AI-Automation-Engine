# Willovate AI Automation Engine

## Project Overview

The **Willovate AI Automation Engine** is an AI-powered platform that converts natural language instructions into executable automation workflows. The system understands user commands, detects user intent, extracts important entities, validates the input, generates workflow steps, and converts them into structured JSON for automation execution.

---

# Example

## User Input

```
Open the CRM and add Rahul with phone number 9876543210.
```

## Generated Workflow

```json
{
  "steps": [
    {
      "action": "OPEN_PAGE",
      "target": "CRM"
    },
    {
      "action": "CLICK",
      "target": "Add Customer"
    },
    {
      "action": "ENTER_TEXT",
      "target": "Customer Name",
      "value": "Rahul"
    },
    {
      "action": "ENTER_TEXT",
      "target": "Phone Number",
      "value": "9876543210"
    },
    {
      "action": "CLICK",
      "target": "Save"
    }
  ]
}
```

---

# Features

- Intent Detection
- Entity Extraction
- Missing Information Detection
- Workflow Generation
- JSON Workflow Generation
- Multi-Step Planning
- English, Hindi & Hinglish Support
- Screenshot Understanding
- Risk Detection
- Workflow Validation
- FastAPI Backend
- Streamlit Dashboard

---

# Tech Stack

- Python
- FastAPI
- Scikit-Learn
- Logistic Regression
- TF-IDF Vectorizer
- Transformers
- Sentence Transformers
- spaCy
- Pandas
- OpenCV
- Playwright
- Streamlit
- Joblib

---

# Current Progress

## ✅ Day 1 (06 Aug 2026)

- Project folder structure created
- Python virtual environment configured
- FastAPI project initialized
- Initial dataset prepared
- Git repository created
- GitHub repository connected

---

## ✅ Day 2 (07 Aug 2026)

- Created Intent Detection dataset (251 samples)
- Cleaned and verified dataset
- Implemented TF-IDF Vectorizer
- Trained Logistic Regression model
- Achieved **90.2% Accuracy**
- Saved trained model (`intent_model.pkl`)
- Built Intent Prediction module
- Generated Classification Report
- Tested multiple user instructions

---

## ✅ Day 3 (08 Aug 2026)

- Expanded instruction dataset
- Built Entity Extraction module
- Extracted Name, Phone Number, Email, Price and File Name
- Implemented Missing Information Detection
- Built Workflow Generator
- Generated Automation Workflow
- Converted Workflow into JSON format
- Saved workflow outputs automatically
- Tested all modules successfully
- Updated project documentation

## ✅ Day 4 — Workflow Validation & Risk Detection

**Date:** 10 Aug 2026

- Developed the Workflow Validation module
- Validated workflow structure and workflow steps
- Checked supported actions and required targets
- Detected invalid and unsupported workflow actions
- Developed the Risk Detection module
- Added LOW, MEDIUM and HIGH risk levels
- Added confirmation requirement for risky operations
- Created the Workflow Safety Checker
- Integrated Workflow Generation, Workflow Validation and Risk Detection
- Tested valid and invalid workflows
- Tested LOW, MEDIUM and HIGH-risk instructions
- Captured Day 4 testing screenshots
- Updated project documentation

## ✅ Day 5 (11 Aug 2026)

- Implemented multi-step workflow planning
- Added ordered task processing
- Improved workflow generation for multiple actions
- Preserved user instruction order during workflow generation
- Tested customer, file upload and report download workflows
- Implemented multi-step JSON generation
- Verified generated JSON output
- Captured Day 5 workflow and JSON screenshots
---
## ✅ Day 6 – Action Prediction & UI Element Understanding

- Implemented Action Prediction module
- Added support for multiple automation actions
- Implemented UI Element Mapping
- Mapped actions to required UI elements
- Connected Workflow Generator with UI Element Mapper
- Tested complete UI-aware workflows
- Supported BUTTON, INPUT, DROPDOWN, FILE_INPUT, TABLE and PAGE elements
- Tested customer creation workflow
- Tested file upload and report download workflow
- Added Day 6 screenshots and documentation

### Supported Actions

- OPEN_PAGE
- CLICK
- ENTER_TEXT
- SELECT_OPTION
- UPLOAD_FILE
- DOWNLOAD_FILE
- READ_TABLE
- SCROLL
- SUBMIT
- TAKE_SCREENSHOT

### UI Element Mapping

| Action | UI Element |
|---|---|
| OPEN_PAGE | PAGE |
| CLICK | BUTTON |
| ENTER_TEXT | INPUT |
| SELECT_OPTION | DROPDOWN |
| UPLOAD_FILE | FILE_INPUT |
| DOWNLOAD_FILE | BUTTON |
| READ_TABLE | TABLE |
| SCROLL | PAGE |
| SUBMIT | BUTTON |
| TAKE_SCREENSHOT | PAGE |

### Day 6 Test Result

Example instruction:

`Open the CRM, add Rahul as a customer with phone 9876543210 and save the record.`

The system successfully generated a UI-aware workflow by combining workflow generation, action prediction and UI element mapping.

# Project Folder Structure

```
Willovate-AI-Automation-Engine
│
├── app
│   ├── api
│   ├── config
│   ├── core
│   │   ├── entity_extractor.py
│   │   ├── missing_information.py
│   │   ├── workflow_generator.py
│   │   └── json_generator.py
│   │
│   ├── models
│   │   ├── train_intent_model.py
│   │   └── test_intent_model.py
│   │
│   └── utils
│
├── data
│   ├── raw
│   └── processed
│
├── models
│
├── outputs
│   ├── intent_detection
│   ├── entity_extraction
│   ├── missing_information
│   ├── workflow_generation
│   └── json_generation
│
├── screenshots
│   ├── day2
│   └── day3
│
├── docs
│
├── README.md
├── requirements.txt
└── main.py
```

---

# Intent Detection Model

### Algorithm

- TF-IDF Vectorizer
- Logistic Regression

### Dataset Size

- 251 Instructions

### Model Accuracy

**90.2%**

### Supported Intents

- ADD_CUSTOMER
- UPDATE_CUSTOMER
- DELETE_CUSTOMER
- UPDATE_PRODUCT
- UPDATE_EMPLOYEE
- DELETE_EMPLOYEE
- DOWNLOAD_REPORT
- UPLOAD_FILE
- READ_TABLE
- SEND_EMAIL
- FILL_FORM
- OPEN_PAGE
- CLICK_BUTTON

---

# Entity Extraction

The Entity Extraction module identifies important information from user instructions.

### Supported Entities

- Customer Name
- Phone Number
- Email Address
- File Name
- Product Price

### Example

Input

```
Add Rahul with phone 9876543210
```

Output

```json
{
  "name": "Rahul",
  "phone": "9876543210"
}
```

---

# Missing Information Detection

The system verifies whether the user has provided all required information.

### Example

Input

```
Create customer
```

Output

```
Missing Fields

- Customer Name
- Phone Number
```

---

# Workflow Generator

The Workflow Generator converts user instructions into executable automation steps.

Example

Input

```
Add Rahul customer with phone 9876543210
```

Output

```json
{
  "steps": [
    {
      "action": "OPEN_PAGE",
      "target": "Customers"
    },
    {
      "action": "CLICK",
      "target": "Add Customer"
    },
    {
      "action": "ENTER_TEXT",
      "target": "Customer Name",
      "value": "Rahul"
    },
    {
      "action": "ENTER_TEXT",
      "target": "Phone Number",
      "value": "9876543210"
    },
    {
      "action": "CLICK",
      "target": "Save"
    }
  ]
}
```

---

# JSON Generator

The JSON Generator converts workflow steps into structured JSON that can be executed by an automation engine or API.

Output Format

```json
{
  "steps": [
    {
      "action": "OPEN_PAGE",
      "target": "Customers"
    },
    {
      "action": "CLICK",
      "target": "Add Customer"
    }
  ]
}
```

---

# Git Progress

| Day | Branch |
|------|--------|
| Day 1 | day-1-project-setup |
| Day 2 | day-2-intent-detection |
| Day 3 | day-3-entity-extraction |

---

# Future Work

- Workflow Validation
- Risk Detection
- Multi-Step Planning
- Screenshot Understanding
- Automation Runner
- FastAPI Integration
- Streamlit Dashboard
- AI Agent Integration
- Model Optimization

---

# Author

**Nikhil Patil**

AI/ML Engineer Intern

Willovate Pvt. Ltd.