from datetime import datetime
from decimal import Decimal

from src.extraction.extractors.yape import extract_yape

_FULL_TEXT = """
Yape
Pagaste exitosamente
Para: María García
S/ 35.50
Código de operación: 987654321
15/04/2024
"""

_PARTIAL_TEXT = """
Yape
S/120.00
operación 123456789
"""

_MINIMAL_TEXT = """
Yape
S/ 8.00
"""


def test_full_extraction() -> None:
    result = extract_yape(_FULL_TEXT)

    assert result["amount"] == Decimal("35.50")
    assert result["operation_code"] == "987654321"
    assert result["issued_at"] == datetime(2024, 4, 15)
    assert result["recipient_name"] == "María García"


def test_partial_extraction_no_date_no_recipient() -> None:
    result = extract_yape(_PARTIAL_TEXT)

    assert result["amount"] == Decimal("120.00")
    assert result["operation_code"] == "123456789"
    assert result["issued_at"] is None
    assert result["recipient_name"] is None


def test_minimal_only_amount() -> None:
    result = extract_yape(_MINIMAL_TEXT)

    assert result["amount"] == Decimal("8.00")
    assert result["operation_code"] is None
    assert result["issued_at"] is None
    assert result["recipient_name"] is None


def test_amount_with_dot_prefix() -> None:
    result = extract_yape("S/. 99.90 transferido")
    assert result["amount"] == Decimal("99.90")


def test_date_text_format() -> None:
    result = extract_yape("Yape\nS/10.00\n3 de marzo de 2024")
    assert result["issued_at"] == datetime(2024, 3, 3)


def test_no_fields_returns_nones() -> None:
    result = extract_yape("texto aleatorio sin campos")
    assert result["amount"] is None
    assert result["operation_code"] is None
    assert result["issued_at"] is None
    assert result["recipient_name"] is None
