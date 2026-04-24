"""Integration tests for ReceiptRepository — hits a real Postgres DB."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.receipt import ReceiptStatus
from src.repositories.receipt_repository import ReceiptRepository


async def test_create_returns_receipt_with_id(db_session: AsyncSession) -> None:
    repo = ReceiptRepository(db_session)
    receipt = await repo.create(image_path="uploads/test.png")
    await db_session.commit()

    assert receipt.id is not None
    assert isinstance(receipt.id, uuid.UUID)
    assert receipt.status == ReceiptStatus.PENDING
    assert receipt.image_path == "uploads/test.png"
    assert receipt.currency == "PEN"


async def test_get_by_id_returns_none_when_not_found(db_session: AsyncSession) -> None:
    repo = ReceiptRepository(db_session)
    result = await repo.get_by_id(uuid.uuid4())
    assert result is None


async def test_get_by_id_returns_receipt_when_exists(db_session: AsyncSession) -> None:
    repo = ReceiptRepository(db_session)
    created = await repo.create(image_path="uploads/test.png")
    await db_session.commit()

    found = await repo.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id
    assert found.image_path == created.image_path
