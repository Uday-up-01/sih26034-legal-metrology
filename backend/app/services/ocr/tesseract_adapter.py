from pathlib import Path
from collections import defaultdict
from statistics import median

import cv2
import pytesseract
from pytesseract import Output

from app.schemas.inspection import OCRBlock, BoundingBox


# Main OCR enlargement.
SCALE_FACTOR = 2.0

# Ignore very unreliable OCR words.
MIN_CONFIDENCE = 30.0


def _preprocess_image(image):
    """
    Preprocess the complete package image for OCR.
    """

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY,
    )

    gray = cv2.resize(
        gray,
        None,
        fx=SCALE_FACTOR,
        fy=SCALE_FACTOR,
        interpolation=cv2.INTER_CUBIC,
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    gray = clahe.apply(
        gray
    )

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0,
    )

    binary = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )[1]

    return binary


def _extract_mrp_region(image):
    """
    Focused OCR for the upper-right MRP area.

    Multiple OCR passes are used because the normal
    full-image OCR detects the MRP heading but may miss
    the large isolated price value.
    """

    height, width = image.shape[:2]

    # Upper-right region.
    x1 = int(
        width * 0.52
    )

    y1 = int(
        height * 0.01
    )

    x2 = width

    y2 = int(
        height * 0.30
    )

    crop = image[
        y1:y2,
        x1:x2,
    ]

    if crop.size == 0:
        return "", None

    gray = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2GRAY,
    )

    enlarged = cv2.resize(
        gray,
        None,
        fx=4.0,
        fy=4.0,
        interpolation=cv2.INTER_CUBIC,
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    )

    enhanced = clahe.apply(
        enlarged
    )

    blurred = cv2.GaussianBlur(
        enhanced,
        (3, 3),
        0,
    )

    thresholded = cv2.threshold(
        blurred,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )[1]

    adaptive = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    # -----------------------------------------------------
    # Pass 1: enhanced grayscale + sparse text
    # -----------------------------------------------------

    text_1 = pytesseract.image_to_string(
        enhanced,
        config=(
            "--oem 3 "
            "--psm 11 "
            "-l eng"
        ),
    )

    # -----------------------------------------------------
    # Pass 2: thresholded + sparse text
    # -----------------------------------------------------

    text_2 = pytesseract.image_to_string(
        thresholded,
        config=(
            "--oem 3 "
            "--psm 11 "
            "-l eng"
        ),
    )

    # -----------------------------------------------------
    # Pass 3: enhanced + normal block mode
    # -----------------------------------------------------

    text_3 = pytesseract.image_to_string(
        enhanced,
        config=(
            "--oem 3 "
            "--psm 6 "
            "-l eng"
        ),
    )

    # -----------------------------------------------------
    # Pass 4: adaptive threshold + sparse text
    # -----------------------------------------------------

    text_4 = pytesseract.image_to_string(
        adaptive,
        config=(
            "--oem 3 "
            "--psm 11 "
            "-l eng"
        ),
    )

    # -----------------------------------------------------
    # Pass 5: tighter price-only strip
    # -----------------------------------------------------

    crop_height = crop.shape[0]
    crop_width = crop.shape[1]

    price_y1 = int(
        crop_height * 0.20
    )

    price_y2 = int(
        crop_height * 0.58
    )

    price_crop = crop[
        price_y1:price_y2,
        0:crop_width,
    ]

    text_5 = ""

    if price_crop.size > 0:

        price_gray = cv2.cvtColor(
            price_crop,
            cv2.COLOR_BGR2GRAY,
        )

        price_gray = cv2.resize(
            price_gray,
            None,
            fx=5.0,
            fy=5.0,
            interpolation=cv2.INTER_CUBIC,
        )

        price_gray = cv2.GaussianBlur(
            price_gray,
            (3, 3),
            0,
        )

        price_binary = cv2.threshold(
            price_gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )[1]

        text_5 = pytesseract.image_to_string(
            price_binary,
            config=(
                "--oem 3 "
                "--psm 7 "
                "-l eng "
                "-c tessedit_char_whitelist="
                "0123456789.RsINR₹/-"
            ),
        )

    # -----------------------------------------------------
    # Debug output
    # -----------------------------------------------------

    print(
        "\n========== MRP OCR PASS 1 =========="
    )
    print(
        text_1
    )

    print(
        "\n========== MRP OCR PASS 2 =========="
    )
    print(
        text_2
    )

    print(
        "\n========== MRP OCR PASS 3 =========="
    )
    print(
        text_3
    )

    print(
        "\n========== MRP OCR PASS 4 =========="
    )
    print(
        text_4
    )

    print(
        "\n========== MRP OCR PASS 5 =========="
    )
    print(
        text_5
    )

    print(
        "====================================\n"
    )

    # Pass 1, 2 and 3 already detected 40.00
    # in your test image. Combining them gives the
    # declaration extractor multiple chances to detect it.
    combined_text = "\n".join(
        [
            text_1,
            text_2,
            text_3,
        ]
    ).strip()

    if not combined_text:
        combined_text = "\n".join(
            [
                text_4,
                text_5,
            ]
        ).strip()

    bbox = BoundingBox(
        x=x1,
        y=y1,
        width=x2 - x1,
        height=y2 - y1,
    )

    return combined_text, bbox


def _split_large_horizontal_gaps(words):
    """
    Split distant horizontal text groups.

    Example:

        NET WEIGHT: 100 g        care@demo.com
    """

    if not words:
        return []

    words = sorted(
        words,
        key=lambda item: item["left"],
    )

    heights = [
        word["height"]
        for word in words
        if word["height"] > 0
    ]

    typical_height = (
        median(
            heights
        )
        if heights
        else 20
    )

    gap_threshold = max(
        typical_height * 4,
        80,
    )

    groups = []

    current_group = [
        words[0]
    ]

    for previous, current in zip(
        words,
        words[1:],
    ):

        previous_right = (
            previous["left"]
            + previous["width"]
        )

        gap = (
            current["left"]
            - previous_right
        )

        if gap > gap_threshold:

            groups.append(
                current_group
            )

            current_group = [
                current
            ]

        else:

            current_group.append(
                current
            )

    groups.append(
        current_group
    )

    return groups


def _create_ocr_block(
    words,
    image_path: str,
):
    """
    Convert grouped Tesseract words into one OCRBlock.
    """

    if not words:
        return None

    words = sorted(
        words,
        key=lambda item: item["left"],
    )

    line_text = " ".join(
        word["text"]
        for word in words
    )

    x1 = min(
        word["left"]
        for word in words
    )

    y1 = min(
        word["top"]
        for word in words
    )

    x2 = max(
        word["left"]
        + word["width"]
        for word in words
    )

    y2 = max(
        word["top"]
        + word["height"]
        for word in words
    )

    average_confidence = (
        sum(
            word["confidence"]
            for word in words
        )
        / len(words)
    )

    # Convert coordinates from enlarged OCR image
    # back to original image coordinates.
    original_x = int(
        x1 / SCALE_FACTOR
    )

    original_y = int(
        y1 / SCALE_FACTOR
    )

    original_width = int(
        (x2 - x1)
        / SCALE_FACTOR
    )

    original_height = int(
        (y2 - y1)
        / SCALE_FACTOR
    )

    return OCRBlock(
        text=line_text,

        confidence=min(
            max(
                average_confidence / 100.0,
                0.0,
            ),
            1.0,
        ),

        bbox=BoundingBox(
            x=original_x,
            y=original_y,
            width=original_width,
            height=original_height,
        ),

        source_image=Path(
            image_path
        ).name,
    )


def extract_text(
    image_path: str,
) -> list[OCRBlock]:
    """
    Main OCR entry point.
    """

    image = cv2.imread(
        image_path
    )

    if image is None:
        raise ValueError(
            "Unable to read image"
        )

    # =====================================================
    # Focused MRP OCR
    # =====================================================

    mrp_text, mrp_bbox = (
        _extract_mrp_region(
            image
        )
    )

    # =====================================================
    # Main full-image OCR
    # =====================================================

    processed = _preprocess_image(
        image
    )

    data = pytesseract.image_to_data(
        processed,

        output_type=Output.DICT,

        config=(
            "--oem 3 "
            "--psm 6 "
            "-l eng "
            "-c preserve_interword_spaces=1"
        ),
    )

    lines = defaultdict(
        list
    )

    total_items = len(
        data["text"]
    )

    for i in range(
        total_items
    ):

        raw_text = (
            data["text"][i]
        )

        if raw_text is None:
            continue

        text = (
            raw_text.strip()
        )

        if not text:
            continue

        try:

            confidence = float(
                data["conf"][i]
            )

        except (
            ValueError,
            TypeError,
        ):

            continue

        if confidence < MIN_CONFIDENCE:
            continue

        line_key = (
            int(
                data["block_num"][i]
            ),

            int(
                data["par_num"][i]
            ),

            int(
                data["line_num"][i]
            ),
        )

        lines[
            line_key
        ].append(
            {
                "text": text,

                "confidence": confidence,

                "left": int(
                    data["left"][i]
                ),

                "top": int(
                    data["top"][i]
                ),

                "width": int(
                    data["width"][i]
                ),

                "height": int(
                    data["height"][i]
                ),
            }
        )

    blocks: list[OCRBlock] = []

    # =====================================================
    # Add focused MRP OCR as a synthetic OCR block
    # =====================================================

    if (
        mrp_text
        and mrp_bbox is not None
    ):

        mrp_block = OCRBlock(
            text=mrp_text,

            # This confidence is intentionally lower than
            # highly confident full-image OCR because this
            # result comes from several focused OCR passes.
            confidence=0.90,

            bbox=mrp_bbox,

            source_image=Path(
                image_path
            ).name,
        )

        blocks.append(
            mrp_block
        )

    # =====================================================
    # Convert regular OCR words into line blocks
    # =====================================================

    for words in lines.values():

        groups = (
            _split_large_horizontal_gaps(
                words
            )
        )

        for group in groups:

            block = (
                _create_ocr_block(
                    group,
                    image_path,
                )
            )

            if block is not None:

                blocks.append(
                    block
                )

    # =====================================================
    # Sort OCR blocks visually
    # =====================================================

    blocks.sort(
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
        )
    )

    # =====================================================
    # Temporary debug output
    # =====================================================

    print(
        "\n========== OCR BLOCKS =========="
    )

    for block in blocks:

        print(
            f"TEXT={block.text!r} | "
            f"CONF={block.confidence:.2f} | "
            f"BBOX={block.bbox}"
        )

    print(
        "================================\n"
    )

    return blocks