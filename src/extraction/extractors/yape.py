from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

_MONTH_MAP = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "setiembre": 9, "septiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

_AMOUNT_RE = re.compile(r"[Ss]/\.?\s*(\d{1,6}(?:[.,]\d{2})?)")
_CODE_RE = re.compile(
    r"(?:c[oó]digo|operaci[oó]n|n[uú]mero|#)\s*:?\s*(\d{6,12})",
    re.IGNORECASE,
)
_CODE_BARE_RE = re.compile(r"\b(\d{8,12})\b")
_DATE_DMY_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b")
_DATE_TEXT_RE = re.compile(
    r"\b(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+(?:de\s+)?(\d{4})\b",
    re.IGNORECASE,
)
_RECIPIENT_RE = re.compile(
    r"(?:\bpara\b|\bdestinario\b|\benviaste?\s+a\b)\s*:?\s*(.{3,40}?)(?:\n|$)",
    re.IGNORECASE,
)


def _parse_amount(text: str) -> Decimal | None:
    match = _AMOUNT_RE.search(text)
    if not match:
        return None
    raw = match.group(1).replace(",", ".")
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def _parse_operation_code(text: str) -> str | None:
    match = _CODE_RE.search(text)
    if match:
        return match.group(1)
    match = _CODE_BARE_RE.search(text)
    return match.group(1) if match else None


def _parse_date(text: str) -> datetime | None:
    match = _DATE_TEXT_RE.search(text)
    if match:
        day = int(match.group(1))
        month = _MONTH_MAP.get(match.group(2).lower())
        year = int(match.group(3))
        if month:
            try:
                return datetime(year, month, day)
            except ValueError:
                pass

    match = _DATE_DMY_RE.search(text)
    if match:
        day, month_num, year_raw = int(match.group(1)), int(match.group(2)), match.group(3)
        year = int(year_raw) if len(year_raw) == 4 else 2000 + int(year_raw)
        try:
            return datetime(year, month_num, day)
        except ValueError:
            pass

    return None


def _parse_recipient(text: str) -> str | None:
    match = _RECIPIENT_RE.search(text)
    if not match:
        return None
    candidate = match.group(1).strip()
    return candidate if len(candidate) >= 3 else None  # noqa: PLR2004  # min meaningful name length


def extract_yape(text: str) -> dict[str, Any]:
    """Extract Yape receipt fields from raw OCR text.

    Keys match Receipt model column names. Missing fields are included as None.

    Args:
        text: Raw OCR text from a Yape payment screenshot.

    Returns:
        Dict with keys: amount, operation_code, issued_at, recipient_name.
    """
    return {
        "amount": _parse_amount(text),
        "operation_code": _parse_operation_code(text),
        "issued_at": _parse_date(text),
        "recipient_name": _parse_recipient(text),
    }
