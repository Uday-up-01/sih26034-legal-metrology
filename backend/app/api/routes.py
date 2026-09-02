from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.inspection import AnalyzeTextRequest, AnalysisResponse, OCRBlock
from app.services.extraction.declarations import extract_declarations
from app.services.compliance.engine import evaluate
from app.services.ocr.tesseract_adapter import extract_text

router = APIRouter()
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "storage" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/health")
def health():
    return {"status": "ok", "service": "sih26034-backend"}

@router.post("/analyze-text", response_model=AnalysisResponse)
def analyze_text(payload: AnalyzeTextRequest):
    lines = [line.strip() for line in payload.text.splitlines() if line.strip()]
    blocks = [OCRBlock(text=line, confidence=0.99) for line in lines]
    fields = extract_declarations(blocks)
    ruleset_id, checks, overall = evaluate(fields)
    return AnalysisResponse(ruleset_id=ruleset_id, overall_status=overall, extracted_fields=fields, checks=checks)

@router.post("/analyze-image", response_model=AnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    suffix = Path(file.filename or "upload.jpg").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Only JPG, PNG and WEBP images are supported")

    target = UPLOAD_DIR / f"{uuid4().hex}{suffix}"
    target.write_bytes(await file.read())
    try:
        blocks = extract_text(str(target))
        fields = extract_declarations(blocks)
        ruleset_id, checks, overall = evaluate(fields)
        return AnalysisResponse(ruleset_id=ruleset_id, overall_status=overall, extracted_fields=fields, checks=checks)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
