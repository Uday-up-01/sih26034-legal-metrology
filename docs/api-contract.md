# API Contract v0.1

## POST /api/analyze-image
Multipart form-data: `file`

Returns:
```json
{
  "ruleset_id": "LM-PCR-Prototype-v1",
  "overall_status": "COMPLIANT_FOR_PROTOTYPE_RULESET",
  "extracted_fields": [],
  "checks": []
}
```

## POST /api/analyze-text
Developer/testing fallback that bypasses OCR while exercising extraction + compliance.
