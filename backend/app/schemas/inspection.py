from typing import Literal, Optional
from pydantic import BaseModel, Field

Status = Literal["PASS", "FAIL", "REVIEW", "N/A"]

class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class OCRBlock(BaseModel):
    text: str
    confidence: float = Field(ge=0, le=1)
    bbox: Optional[BoundingBox] = None
    source_image: Optional[str] = None

class ExtractedField(BaseModel):
    field_name: str
    raw_text: Optional[str] = None
    normalized_value: Optional[str] = None
    confidence: float = Field(default=0, ge=0, le=1)
    bbox: Optional[BoundingBox] = None
    source_image: Optional[str] = None

class ComplianceResult(BaseModel):
    rule_id: str
    field: str
    label: str
    status: Status
    reason: str
    evidence: Optional[ExtractedField] = None

class AnalyzeTextRequest(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    ruleset_id: str
    overall_status: str
    extracted_fields: list[ExtractedField]
    checks: list[ComplianceResult]
