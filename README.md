# Willovate AI Automation Engine

## Project Overview

The Willovate AI Automation Engine is an AI-powered platform that converts natural language instructions into executable automation workflows. The system understands user commands, identifies the required task, extracts important information, generates workflow steps, and prepares them for execution on web applications.

Example:

### User Input

Open the CRM and add Rahul with phone number 9876543210.

### Expected Workflow

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

# Project Features

- Intent Detection
- Entity Extraction
- Workflow Planning
- Workflow JSON Generation
- Missing Information Detection
- Multi-step Planning
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

- Project setup completed
- Folder structure created
- Python environment configured
- FastAPI project initialized
- Initial training dataset prepared
- Git repository created

## ✅ Day 2 (07 Aug 2026)

- Intent Detection dataset created (251 samples)
- Dataset cleaned and verified
- TF-IDF Vectorizer implemented
- Logistic Regression model trained
- Model Accuracy: **90.2%**
- Model saved as `intent_model.pkl`
- Intent prediction tested successfully
- Evaluation report generated

---

# Folder Structure

```
Willovate-AI-Automation-Engine
│
├── app
│   ├── api
│   ├── config
│   ├── core
│   ├── models
│   └── utils
│
├── data
│   ├── raw
│   └── processed
│
├── models
│
├── outputs
│
├── screenshots
│
├── docs
│
├── requirements.txt
├── README.md
└── main.py
```

---

# Intent Detection Model

Algorithm:
- TF-IDF Vectorizer
- Logistic Regression

Dataset Size:
- 251 Instructions

Model Accuracy:
- **90.2%**

Supported Intents:

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

# Future Work

- Entity Extraction
- Missing Information Detection
- Workflow Planning
- JSON Workflow Generator
- Risk Detection
- Screenshot Understanding
- Automation Runner
- Streamlit Dashboard

---

# Author

Nikhil Patil

AI/ML Engineer Intern

Willovate Pvt. Ltd.