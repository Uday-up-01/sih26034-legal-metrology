import re
from math import hypot

from rapidfuzz import fuzz

from app.schemas.inspection import (
    ExtractedField,
    OCRBlock,
    BoundingBox,
)


# =========================================================
# Patterns
# =========================================================

MRP_LABEL_PATTERN = re.compile(
    r"\b(?:MRP|M\.R\.P\.?|MAX(?:IMUM)?\s+RETAIL\s+PRICE)\b",
    re.I,
)

PRICE_VALUE_PATTERN = re.compile(
    r"(?<!\d)([0-9]{1,6}(?:\.[0-9]{1,2})?)(?!\d)",
    re.I,
)

NET_LABEL_PATTERN = re.compile(
    r"\bNET\s*(?:WT|WEIGHT|QTY|QUANTITY)?\b",
    re.I,
)

NET_VALUE_PATTERN = re.compile(
    r"([0-9]+(?:\.[0-9]+)?)\s*"
    r"(KG|G|GM|GRAMS?|ML|L|LTR|LITRE|LITRES|PCS|PIECES?|NOS)\b",
    re.I,
)

MANUFACTURER_HINTS = [
    "manufactured by",
    "mfd by",
    "packed by",
    "packer",
    "imported by",
    "manufacturer",
]

PRICE_REJECTION_TERMS = [
    "unit sale price",
    "unit price",
    "per g",
    "per kg",
    "per gm",
    "per ml",
    "per litre",
    "per liter",
]


# =========================================================
# General helpers
# =========================================================

def _combine_bbox(
    blocks: list[OCRBlock],
) -> BoundingBox | None:

    boxes = [
        block.bbox
        for block in blocks
        if block.bbox
    ]

    if not boxes:
        return None

    x1 = min(
        box.x
        for box in boxes
    )

    y1 = min(
        box.y
        for box in boxes
    )

    x2 = max(
        box.x + box.width
        for box in boxes
    )

    y2 = max(
        box.y + box.height
        for box in boxes
    )

    return BoundingBox(
        x=x1,
        y=y1,
        width=x2 - x1,
        height=y2 - y1,
    )


def _average_confidence(
    blocks: list[OCRBlock],
) -> float:

    if not blocks:
        return 0.0

    return sum(
        block.confidence
        for block in blocks
    ) / len(blocks)


def _center_x(
    block: OCRBlock,
) -> float:

    if not block.bbox:
        return 0.0

    return (
        block.bbox.x
        + block.bbox.width / 2
    )


def _center_y(
    block: OCRBlock,
) -> float:

    if not block.bbox:
        return 0.0

    return (
        block.bbox.y
        + block.bbox.height / 2
    )


def _distance(
    first: OCRBlock,
    second: OCRBlock,
) -> float:

    return hypot(
        _center_x(first)
        - _center_x(second),

        _center_y(first)
        - _center_y(second),
    )


def _same_row(
    first: OCRBlock,
    second: OCRBlock,
    tolerance: int = 50,
) -> bool:

    return abs(
        _center_y(first)
        - _center_y(second)
    ) <= tolerance


def _is_right_of(
    candidate: OCRBlock,
    reference: OCRBlock,
) -> bool:

    if not candidate.bbox or not reference.bbox:
        return False

    return (
        candidate.bbox.x
        >= reference.bbox.x
    )


def _is_below(
    candidate: OCRBlock,
    reference: OCRBlock,
) -> bool:

    if not candidate.bbox or not reference.bbox:
        return False

    return (
        candidate.bbox.y
        >= reference.bbox.y
    )


def _contains_rejected_price_context(
    text: str,
) -> bool:

    lower = text.lower()

    return any(
        term in lower
        for term in PRICE_REJECTION_TERMS
    )


def _normalize_unit(
    unit: str,
) -> str:

    unit = unit.upper()

    if unit in {
        "GM",
        "GRAM",
        "GRAMS",
    }:
        return "G"

    if unit in {
        "LTR",
        "LITRE",
        "LITRES",
    }:
        return "L"

    if unit in {
        "PIECE",
        "PIECES",
    }:
        return "PCS"

    return unit


# =========================================================
# MRP extraction
# =========================================================

def _extract_mrp(
    blocks: list[OCRBlock],
) -> ExtractedField | None:
    """
    Extract MRP safely.

    Important:
    - Search only after the MRP label.
    - Stop before Unit Sale Price and other declarations.
    - Never use unit sale price as MRP.
    """

    for block in blocks:

        label_match = MRP_LABEL_PATTERN.search(
            block.text
        )

        if not label_match:
            continue

        # -------------------------------------------------
        # 1. Search inside the same OCR block
        # -------------------------------------------------

        text_after_label = block.text[
            label_match.end():
        ]

        lower_text = text_after_label.lower()

        stop_terms = [
            "unit sale price",
            "unit price",
            "date of manufacturing",
            "dateof manufacturing",
            "date of manufact",
            "best before",
            "batch no",
            "customer care",
            "net weight",
            "net qty",
            "manufactured by",
        ]

        stop_positions = []

        for term in stop_terms:

            position = lower_text.find(
                term
            )

            if position != -1:
                stop_positions.append(
                    position
                )

        if stop_positions:

            text_after_label = (
                text_after_label[
                    :min(stop_positions)
                ]
            )

        # Prevent searching too far from MRP label.
        text_after_label = (
            text_after_label[:150]
        )

        price_matches = (
            PRICE_VALUE_PATTERN.findall(
                text_after_label
            )
        )

        for value in price_matches:

            try:
                numeric_value = float(
                    value
                )

            except ValueError:
                continue

            # Ignore nonsense/very small values.
            if numeric_value < 1:
                continue

            return ExtractedField(
                field_name="mrp",
                raw_text=(
                    f"MAXIMUM RETAIL PRICE: {value}"
                ),
                normalized_value=value,
                confidence=block.confidence,
                bbox=block.bbox,
                source_image=block.source_image,
            )

        # -------------------------------------------------
        # 2. Spatial fallback
        # -------------------------------------------------

        candidates = []

        for candidate in blocks:

            if candidate is block:
                continue

            if not candidate.bbox or not block.bbox:
                continue

            candidate_text = (
                candidate.text.strip()
            )

            if not candidate_text:
                continue

            if _contains_rejected_price_context(
                candidate_text
            ):
                continue

            if NET_LABEL_PATTERN.search(
                candidate_text
            ):
                continue

            if _manufacturer_score(
                candidate_text
            ) >= 75:
                continue

            value_match = (
                PRICE_VALUE_PATTERN.search(
                    candidate_text
                )
            )

            if not value_match:
                continue

            value = value_match.group(1)

            try:
                numeric_value = float(
                    value
                )

            except ValueError:
                continue

            if numeric_value < 1:
                continue

            score = None

            if (
                _same_row(
                    block,
                    candidate,
                    tolerance=55,
                )
                and _is_right_of(
                    candidate,
                    block,
                )
            ):

                score = _distance(
                    block,
                    candidate,
                )

            elif _is_below(
                candidate,
                block,
            ):

                vertical_gap = (
                    candidate.bbox.y
                    - (
                        block.bbox.y
                        + block.bbox.height
                    )
                )

                horizontal_gap = abs(
                    _center_x(candidate)
                    - _center_x(block)
                )

                if (
                    vertical_gap <= 180
                    and horizontal_gap <= 500
                ):

                    score = (
                        500
                        + vertical_gap
                        + horizontal_gap * 0.25
                    )

            if score is not None:

                candidates.append(
                    (
                        score,
                        candidate,
                        value,
                    )
                )

        if not candidates:
            continue

        candidates.sort(
            key=lambda item: item[0]
        )

        _, value_block, value = (
            candidates[0]
        )

        selected = [
            block,
            value_block,
        ]

        return ExtractedField(
            field_name="mrp",
            raw_text=(
                f"{block.text} "
                f"{value_block.text}"
            ),
            normalized_value=value,
            confidence=_average_confidence(
                selected
            ),
            bbox=_combine_bbox(
                selected
            ),
            source_image=block.source_image,
        )

    return None


# =========================================================
# Net Quantity extraction
# =========================================================

def _extract_net_quantity(
    blocks: list[OCRBlock],
) -> ExtractedField | None:

    # -----------------------------------------------------
    # 1. Prefer values around NET WEIGHT / NET QTY
    # -----------------------------------------------------

    for label in blocks:

        if not NET_LABEL_PATTERN.search(
            label.text
        ):
            continue

        same_line_match = (
            NET_VALUE_PATTERN.search(
                label.text
            )
        )

        if same_line_match:

            value = (
                same_line_match.group(1)
            )

            unit = _normalize_unit(
                same_line_match.group(2)
            )

            return ExtractedField(
                field_name="net_quantity",
                raw_text=label.text,
                normalized_value=f"{value} {unit}",
                confidence=label.confidence,
                bbox=label.bbox,
                source_image=label.source_image,
            )

        candidates = []

        for candidate in blocks:

            if candidate is label:
                continue

            match = (
                NET_VALUE_PATTERN.search(
                    candidate.text
                )
            )

            if not match:
                continue

            score = None

            if (
                _same_row(
                    label,
                    candidate,
                    tolerance=55,
                )
                and _is_right_of(
                    candidate,
                    label,
                )
            ):

                score = _distance(
                    label,
                    candidate,
                )

            elif _is_below(
                candidate,
                label,
            ):

                vertical_gap = (
                    candidate.bbox.y
                    - (
                        label.bbox.y
                        + label.bbox.height
                    )
                )

                if vertical_gap <= 150:

                    score = (
                        500
                        + vertical_gap
                    )

            if score is not None:

                value = match.group(1)

                unit = _normalize_unit(
                    match.group(2)
                )

                candidates.append(
                    (
                        score,
                        candidate,
                        value,
                        unit,
                    )
                )

        if candidates:

            candidates.sort(
                key=lambda item: item[0]
            )

            (
                _,
                value_block,
                value,
                unit,
            ) = candidates[0]

            selected = [
                label,
                value_block,
            ]

            return ExtractedField(
                field_name="net_quantity",
                raw_text=(
                    f"{label.text} "
                    f"{value_block.text}"
                ),
                normalized_value=(
                    f"{value} {unit}"
                ),
                confidence=(
                    _average_confidence(
                        selected
                    )
                ),
                bbox=_combine_bbox(
                    selected
                ),
                source_image=(
                    label.source_image
                ),
            )

    # -----------------------------------------------------
    # 2. Fallback
    # -----------------------------------------------------

    for block in blocks:

        match = (
            NET_VALUE_PATTERN.search(
                block.text
            )
        )

        if not match:
            continue

        value = match.group(1)

        unit = _normalize_unit(
            match.group(2)
        )

        return ExtractedField(
            field_name="net_quantity",
            raw_text=block.text,
            normalized_value=(
                f"{value} {unit}"
            ),
            confidence=block.confidence,
            bbox=block.bbox,
            source_image=block.source_image,
        )

    return None


# =========================================================
# Manufacturer extraction
# =========================================================

def _manufacturer_score(
    text: str,
) -> int:

    lower = text.lower()

    return max(
        (
            fuzz.partial_ratio(
                lower,
                hint,
            )
            for hint in MANUFACTURER_HINTS
        ),
        default=0,
    )


def _clean_manufacturer_name(
    text: str,
) -> str:
    """
    Remove manufacturer declaration heading and
    common OCR artifacts such as 'i)'.
    """

    cleaned = re.sub(
        r"(?i)\b("
        r"manufactured\s+by|"
        r"mfd\s+by|"
        r"packed\s+by|"
        r"imported\s+by|"
        r"manufacturer"
        r")\s*[:\-]?",
        "",
        text,
    ).strip()

    # Example:
    # i) Demo Foods Pvt. Ltd.
    # -> Demo Foods Pvt. Ltd.
    cleaned = re.sub(
        r"^[\s\W]*(?:[a-zA-Z]\))?\s*",
        "",
        cleaned,
    ).strip()

    return cleaned


def _extract_manufacturer(
    blocks: list[OCRBlock],
) -> ExtractedField | None:

    best_block = None
    best_score = 0

    for block in blocks:

        score = _manufacturer_score(
            block.text
        )

        if (
            score >= 75
            and score > best_score
        ):
            best_score = score
            best_block = block

    if best_block is None:
        return None

    # -----------------------------------------------------
    # Manufacturer may already be in same block
    # -----------------------------------------------------

    normalized = (
        _clean_manufacturer_name(
            best_block.text
        )
    )

    # Only accept same-block value when there is
    # actually meaningful text after the heading.
    if (
        normalized
        and normalized.lower()
        != best_block.text.lower()
        and len(normalized) > 2
    ):

        return ExtractedField(
            field_name="manufacturer",
            raw_text=best_block.text,
            normalized_value=normalized,
            confidence=best_block.confidence,
            bbox=best_block.bbox,
            source_image=best_block.source_image,
        )

    # -----------------------------------------------------
    # Otherwise find nearest manufacturer value block
    # -----------------------------------------------------

    candidates = []

    for candidate in blocks:

        if candidate is best_block:
            continue

        if (
            not candidate.bbox
            or not best_block.bbox
        ):
            continue

        text = (
            candidate.text.strip()
        )

        if not text:
            continue

        if MRP_LABEL_PATTERN.search(
            text
        ):
            continue

        if NET_LABEL_PATTERN.search(
            text
        ):
            continue

        if _manufacturer_score(
            text
        ) >= 75:
            continue

        score = None

        if (
            _same_row(
                best_block,
                candidate,
                tolerance=50,
            )
            and _is_right_of(
                candidate,
                best_block,
            )
        ):

            score = _distance(
                best_block,
                candidate,
            )

        elif _is_below(
            candidate,
            best_block,
        ):

            vertical_gap = (
                candidate.bbox.y
                - (
                    best_block.bbox.y
                    + best_block.bbox.height
                )
            )

            horizontal_gap = abs(
                _center_x(candidate)
                - _center_x(best_block)
            )

            if (
                vertical_gap <= 120
                and horizontal_gap <= 450
            ):

                score = (
                    500
                    + vertical_gap
                    + horizontal_gap * 0.25
                )

        if score is not None:

            candidates.append(
                (
                    score,
                    candidate,
                )
            )

    if not candidates:

        return ExtractedField(
            field_name="manufacturer",
            raw_text=best_block.text,
            normalized_value=best_block.text,
            confidence=best_block.confidence,
            bbox=best_block.bbox,
            source_image=best_block.source_image,
        )

    candidates.sort(
        key=lambda item: item[0]
    )

    _, value_block = (
        candidates[0]
    )

    selected = [
        best_block,
        value_block,
    ]

    normalized_value = (
        _clean_manufacturer_name(
            value_block.text
        )
    )

    return ExtractedField(
        field_name="manufacturer",
        raw_text=(
            f"{best_block.text} "
            f"{value_block.text}"
        ),
        normalized_value=(
            normalized_value
            or value_block.text.strip()
        ),
        confidence=_average_confidence(
            selected
        ),
        bbox=_combine_bbox(
            selected
        ),
        source_image=best_block.source_image,
    )


# =========================================================
# Main function
# =========================================================

def extract_declarations(
    blocks: list[OCRBlock],
) -> list[ExtractedField]:

    fields: list[ExtractedField] = []

    blocks = sorted(
        blocks,
        key=lambda block: (
            (
                block.bbox.y
                if block.bbox
                else 0
            ),
            (
                block.bbox.x
                if block.bbox
                else 0
            ),
        ),
    )

    mrp = _extract_mrp(
        blocks
    )

    if mrp:
        fields.append(
            mrp
        )

    net_quantity = (
        _extract_net_quantity(
            blocks
        )
    )

    if net_quantity:
        fields.append(
            net_quantity
        )

    manufacturer = (
        _extract_manufacturer(
            blocks
        )
    )

    if manufacturer:
        fields.append(
            manufacturer
        )

    return fields