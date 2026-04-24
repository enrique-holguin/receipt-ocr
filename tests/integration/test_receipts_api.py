"""Integration tests for the receipts API endpoints."""

import uuid

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# POST /receipts/upload
# ---------------------------------------------------------------------------


async def test_upload_png_returns_201(client: AsyncClient, fake_image_png: bytes) -> None:
    response = await client.post(
        "/receipts/upload",
        files={"file": ("receipt.png", fake_image_png, "image/png")},
    )
    assert response.status_code == 201


async def test_upload_jpeg_returns_201(client: AsyncClient, fake_image_jpeg: bytes) -> None:
    response = await client.post(
        "/receipts/upload",
        files={"file": ("receipt.jpg", fake_image_jpeg, "image/jpeg")},
    )
    assert response.status_code == 201


async def test_upload_webp_returns_201(client: AsyncClient, fake_image_webp: bytes) -> None:
    response = await client.post(
        "/receipts/upload",
        files={"file": ("receipt.webp", fake_image_webp, "image/webp")},
    )
    assert response.status_code == 201


async def test_upload_response_is_valid_receipt_read(
    client: AsyncClient, fake_image_png: bytes
) -> None:
    response = await client.post(
        "/receipts/upload",
        files={"file": ("receipt.png", fake_image_png, "image/png")},
    )
    body = response.json()
    assert uuid.UUID(body["id"])
    assert body["status"] == "pending"
    assert body["document_type"] == "unknown"
    assert body["currency"] == "PEN"
    assert body["image_path"].endswith(".png")


async def test_upload_image_saved_to_disk(
    client: AsyncClient, fake_image_png: bytes, test_settings: object
) -> None:
    from src.core.config import Settings

    settings = test_settings  # type: ignore[assignment]
    assert isinstance(settings, Settings)

    response = await client.post(
        "/receipts/upload",
        files={"file": ("receipt.png", fake_image_png, "image/png")},
    )
    image_path = response.json()["image_path"]
    assert response.status_code == 201
    from pathlib import Path

    assert Path(image_path).exists()


async def test_upload_pdf_returns_415(client: AsyncClient) -> None:
    response = await client.post(
        "/receipts/upload",
        files={"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert response.status_code == 415


async def test_upload_empty_file_returns_422(client: AsyncClient) -> None:
    response = await client.post(
        "/receipts/upload",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 422


async def test_upload_without_file_returns_422(client: AsyncClient) -> None:
    response = await client.post("/receipts/upload")
    assert response.status_code == 422


async def test_upload_too_large_returns_413(client: AsyncClient) -> None:
    # 10 MiB + 1 byte — must exceed the default MAX_UPLOAD_BYTES
    big_content = b"x" * (10 * 1024 * 1024 + 1)
    response = await client.post(
        "/receipts/upload",
        files={"file": ("big.png", big_content, "image/png")},
    )
    assert response.status_code == 413


# ---------------------------------------------------------------------------
# GET /receipts/{receipt_id}
# ---------------------------------------------------------------------------


async def test_get_receipt_returns_200(
    client: AsyncClient, fake_image_png: bytes
) -> None:
    upload = await client.post(
        "/receipts/upload",
        files={"file": ("receipt.png", fake_image_png, "image/png")},
    )
    receipt_id = upload.json()["id"]
    response = await client.get(f"/receipts/{receipt_id}")
    assert response.status_code == 200
    assert response.json()["id"] == receipt_id


async def test_get_receipt_nonexistent_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/receipts/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_get_receipt_malformed_id_returns_422(client: AsyncClient) -> None:
    response = await client.get("/receipts/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.parametrize(
    "bad_id",
    ["abc", "123", "not-a-uuid", "00000000-0000-0000-0000-00000000000Z"],
)
async def test_get_receipt_various_bad_ids_return_422(
    client: AsyncClient, bad_id: str
) -> None:
    response = await client.get(f"/receipts/{bad_id}")
    assert response.status_code == 422
