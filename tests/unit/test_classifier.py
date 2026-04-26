import pytest

from src.extraction.classifier import classify
from src.models.receipt import DocumentType


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Pagaste con Yape a Juan Pérez S/25.00", DocumentType.YAPE),
        ("YAPE - Operación exitosa", DocumentType.YAPE),
        ("yape código 123456789", DocumentType.YAPE),
        ("Transferencia bancaria BCP S/500.00", DocumentType.UNKNOWN),
        ("Boleta de venta electrónica", DocumentType.UNKNOWN),
        ("", DocumentType.UNKNOWN),
    ],
)
def test_classify(text: str, expected: DocumentType) -> None:
    assert classify(text) == expected


def test_classify_case_insensitive() -> None:
    assert classify("YAPE pago exitoso") == DocumentType.YAPE
    assert classify("Yape") == DocumentType.YAPE
    assert classify("yApE") == DocumentType.YAPE
