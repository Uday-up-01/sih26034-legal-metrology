from pathlib import Path
import cv2
import pytesseract
from pytesseract import Output
from app.schemas.inspection import OCRBlock, BoundingBox


def extract_text(image_path: str) -> list[OCRBlock]:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Unable to read image")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    data = pytesseract.image_to_data(gray, output_type=Output.DICT, config="--psm 6")
    blocks: list[OCRBlock] = []

    for i, text in enumerate(data["text"]):
        text = text.strip()
        if not text:
            continue
        conf_raw = float(data["conf"][i])
        if conf_raw < 0:
            continue
        blocks.append(OCRBlock(
            text=text,
            confidence=min(max(conf_raw / 100.0, 0), 1),
            bbox=BoundingBox(
                x=int(data["left"][i]), y=int(data["top"][i]),
                width=int(data["width"][i]), height=int(data["height"][i])
            ),
            source_image=Path(image_path).name,
        ))
    return blocks
