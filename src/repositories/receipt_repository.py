import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.receipt import Receipt


class ReceiptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, image_path: str) -> Receipt:
        """Persist a new Receipt with status=pending and return it with id assigned.

        Args:
            image_path: Relative path where the uploaded image was stored.

        Returns:
            The persisted Receipt instance.
        """
        receipt = Receipt(image_path=image_path)
        self._session.add(receipt)
        await self._session.flush()
        await self._session.refresh(receipt)
        return receipt

    async def get_by_id(self, receipt_id: uuid.UUID) -> Receipt | None:
        """Fetch a Receipt by primary key.

        Args:
            receipt_id: UUID of the receipt to fetch.

        Returns:
            The Receipt if found, None otherwise.
        """
        result = await self._session.execute(
            select(Receipt).where(Receipt.id == receipt_id)
        )
        return result.scalar_one_or_none()
