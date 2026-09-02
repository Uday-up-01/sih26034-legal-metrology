# SIH26034 Packaged Commodity Compliance Inspector — Prototype

Day-1 starter for an evidence-aware Legal Metrology inspection workflow.

## Current vertical slice

Package image → local Tesseract OCR → declaration extraction → deterministic rules → result UI

Implemented prototype fields:

- MRP
- Net quantity
- Manufacturer / packer / importer hint

> The current rules are engineering placeholders and must be verified against the latest official Legal Metrology requirements before presenting them as legal conclusions.

## Backend

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload