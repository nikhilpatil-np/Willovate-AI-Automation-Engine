# Willovate AI Automation Engine

## Project Overview

The Willovate AI Automation Engine converts natural language instructions into executable automation workflows.

Example:

User Input

Open the CRM and add Rahul with phone number 9876543210.

Generated Workflow

{
  "steps":[
    {
      "action":"OPEN_PAGE",
      "target":"CRM"
    },
    {
      "action":"CLICK",
      "target":"Add Customer"
    },
    {
      "action":"ENTER_TEXT",
      "target":"Customer Name",
      "value":"Rahul"
    },
    {
      "action":"ENTER_TEXT",
      "target":"Phone Number",
      "value":"9876543210"
    },
    {
      "action":"CLICK",
      "target":"Save"
    }
  ]
}

---

## Features

- Intent Detection
- Entity Extraction
- Workflow Generation
- Missing Information Detection
- Multi-step Planning
- English/Hindi/Hinglish Support
- Screenshot Understanding
- Risk Detection
- Workflow Validation
- FastAPI Backend
- Streamlit Dashboard

---

## Tech Stack

Python

FastAPI

Transformers

Sentence Transformers

spaCy

OpenCV

Playwright

Streamlit

Pandas

Scikit-Learn

---

## Folder Structure

See architecture.md