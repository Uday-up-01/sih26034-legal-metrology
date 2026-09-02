import re
from rapidfuzz import fuzz
from app.schemas.inspection import ExtractedField, OCRBlock

MRP_PATTERNS = [
    re.compile(r"(?:MRP|M\.R\.P\.?|MAX(?:IMUM)?\s+RETAIL\s+PRICE)\s*[:\-]?\s*(?:RS\.?|INR|₹)?\s*([0-9]+(?:\.[0-9]{1,2})?)", re.I),
    re.compile(r"(?:₹|RS\.?|INR)\s*([0-9]+(?:\.[0-9]{1,2})?).{0,20}(?:INCL|INCLUSIVE|TAX)", re.I),
]
NET_QTY_PATTERN = re.compile(
    r"(?:NET\s*(?:WT|WEIGHT|QTY|QUANTITY)?\.?\s*[:\-]?\s*)?([0-9]+(?:\.[0-9]+)?)\s*(KG|G|GM|GRAMS?|ML|L|LTR|LITRE|LITRES|PCS|PIECES?|NOS)\b",
    re.I,
)

MANUFACTURER_HINTS = ["manufactured by", "mfd by", "packed by", "packer", "imported by", "manufacturer"]


def _best_block(blocks, predicate):
    matches = [b for b in blocks if predicate(b.text)]
    return max(matches, key=lambda b: b.confidence, default=None)


def extract_declarations(blocks: list[OCRBlock]) -> list[ExtractedField]:
    fields: list[ExtractedField] = []

    mrp_block = _best_block(blocks, lambda text: any(p.search(text) for p in MRP_PATTERNS))
    if mrp_block:
        value = None
        for pattern in MRP_PATTERNS:
            m = pattern.search(mrp_block.text)
            if m:
                value = m.group(1)
                break
        fields.append(ExtractedField(
            field_name="mrp", raw_text=mrp_block.text,
            normalized_value=value, confidence=mrp_block.confidence,
            bbox=mrp_block.bbox, source_image=mrp_block.source_image
        ))

    qty_block = _best_block(blocks, lambda text: bool(NET_QTY_PATTERN.search(text)))
    if qty_block:
        m = NET_QTY_PATTERN.search(qty_block.text)
        normalized = f"{m.group(1)} {m.group(2).upper()}" if m else None
        fields.append(ExtractedField(
            field_name="net_quantity", raw_text=qty_block.text,
            normalized_value=normalized, confidence=qty_block.confidence,
            bbox=qty_block.bbox, source_image=qty_block.source_image
        ))

    def manufacturer_score(text: str) -> int:
        lower = text.lower()
        return max((fuzz.partial_ratio(lower, hint) for hint in MANUFACTURER_HINTS), default=0)

    manufacturer_candidates = [(manufacturer_score(b.text), b) for b in blocks]
    manufacturer_candidates = [pair for pair in manufacturer_candidates if pair[0] >= 75]
    if manufacturer_candidates:
        _, block = max(manufacturer_candidates, key=lambda pair: (pair[0], pair[1].confidence))
        fields.append(ExtractedField(
            field_name="manufacturer", raw_text=block.text,
            normalized_value=block.text.strip(), confidence=block.confidence,
            bbox=block.bbox, source_image=block.source_image
        ))

    return fields
