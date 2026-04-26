"""Integration tests for OCR processing triggered by POST /receipts/upload."""

from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient

_YAPE_OCR_TEXT = """
Yape
Para: Carlos Ríos
S/ 50.00
Código de operación: 123456789
10/03/2024
"""


async def test_upload_yape_sets_document_type_and_amount(
    client: AsyncClient,
    fake_image_png: bytes,
    mock_extract_text: MagicMock,
) -> None:
    mock_extract_text.return_value = (_YAPE_OCR_TEXT, 0.92)

    response = await client.post(
        "/receipts/upload",
        files={"file": ("yape.png", fake_image_png, "image/png")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["document_type"] == "yape"
    assert body["status"] == "processed"
    assert body["amount"] == "50.00"
    assert body["operation_code"] == "123456789"


async def test_upload_empty_ocr_returns_needs_review(
    client: AsyncClient,
    fake_image_png: bytes,
    mock_extract_text: MagicMock,
) -> None:
    mock_extract_text.return_value = ("", 0.0)

    response = await client.post(
        "/receipts/upload",
        files={"file": ("blank.png", fake_image_png, "image/png")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "needs_review"
    assert body["amount"] is None


async def test_upload_ocr_failure_returns_failed_status(
    client: AsyncClient,
    fake_image_png: bytes,
    mock_extract_text: MagicMock,
) -> None:
    mock_extract_text.side_effect = RuntimeError("PaddleOCR exploded")

    response = await client.post(
        "/receipts/upload",
        files={"file": ("bad.png", fake_image_png, "image/png")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert body["error_message"] is not None
    assert "PaddleOCR exploded" in body["error_message"]


@pytest.mark.parametrize(
    "ocr_text, expected_status",
    [
        ("Yape S/25.00 código 999888777 10/01/2024", "processed"),
        ("Yape texto sin monto", "needs_review"),
    ],
)
async def test_upload_processing_status_logic(
    client: AsyncClient,
    fake_image_png: bytes,
    mock_extract_text: MagicMock,
    ocr_text: str,
    expected_status: str,
) -> None:
    mock_extract_text.return_value = (ocr_text, 0.85)

    response = await client.post(
        "/receipts/upload",
        files={"file": ("receipt.png", fake_image_png, "image/png")},
    )

    assert response.status_code == 201
    assert response.json()["status"] == expected_status
