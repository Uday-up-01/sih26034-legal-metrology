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
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Requires the Tesseract executable installed on the machine for `/api/analyze-image`.

Test without OCR:
```bash
curl -X POST http://localhost:8000/api/analyze-text \\
  -H "Content-Type: application/json" \\
  -d '{"text":"Maximum Retail Price: ₹40\\nNet Weight: 100 g\\nManufactured by: Demo Foods Pvt Ltd"}'
```

## Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## Day-2 target
Expand structured extraction, improve OCR line grouping/evidence, and verify the next legal rules before adding them to `rules_v1.json`.
