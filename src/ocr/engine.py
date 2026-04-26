from __future__ import annotations

import functools
from pathlib import Path

from paddleocr import PaddleOCR  # type: ignore[import-untyped]

_CONFIDENCE_THRESHOLD = 0.3


@functools.lru_cache(maxsize=1)
def _get_ocr() -> PaddleOCR:
    return PaddleOCR(use_angle_cls=True, lang="es", show_log=False)


def extract_text(image_path: Path) -> tuple[str, float]:
    """Run OCR on an image and return the full text and average confidence.

    Args:
        image_path: Path to the image file.

    Returns:
        Tuple of (full_text, avg_confidence). full_text is blocks joined by newlines,
        ordered top-to-bottom, left-to-right. avg_confidence is the mean confidence
        of blocks above the threshold; 0.0 if no blocks pass.
    """
    ocr = _get_ocr()
    result = ocr.ocr(str(image_path), cls=True)

    lines: list[str] = []
    confidences: list[float] = []

    if not result or result[0] is None:
        return "", 0.0

    # PaddleOCR returns list[list[list]] — one page, then blocks, then [bbox, (text, conf)]
    for page in result:
        if page is None:
            continue
        # Sort blocks by vertical position (top of bbox), then horizontal
        sorted_blocks = sorted(page, key=lambda b: (b[0][0][1], b[0][0][0]))
        for block in sorted_blocks:
            text: str = block[1][0]
            confidence: float = float(block[1][1])
            if confidence >= _CONFIDENCE_THRESHOLD:
                lines.append(text)
                confidences.append(confidence)

    full_text = "\n".join(lines)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return full_text, avg_confidence
