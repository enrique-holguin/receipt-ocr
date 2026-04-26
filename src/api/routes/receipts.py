import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db, get_settings
from src.core.config import Settings
from src.repositories.receipt_repository import ReceiptRepository
from src.schemas.receipt import ReceiptRead
from src.services.processing_service import process_receipt
from src.services.upload_service import (
    EmptyFileError,
    FileTooLargeError,
    UnsupportedMediaTypeError,
    store_uploaded_image,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/receipts", tags=["receipts"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=ReceiptRead)
async def upload_receipt(
    file: Annotated[UploadFile, File(description="Receipt image (JPEG, PNG or WebP).")],
    session: DbDep,
    settings: SettingsDep,
) -> ReceiptRead:
    """Upload a receipt image and create a pending extraction job."""
    try:
        stored = await store_uploaded_image(
            file=file,
            uploads_dir=settings.uploads_dir,
            max_bytes=settings.max_upload_bytes,
        )
    except UnsupportedMediaTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {exc}. Allowed: JPEG, PNG, WebP.",
        ) from exc
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except EmptyFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        ) from exc

    repo = ReceiptRepository(session)
    receipt = await repo.create(image_path=str(stored.path))

    receipt = await process_receipt(receipt.id, session)
    await session.commit()

    logger.info("processed receipt id=%s status=%s", receipt.id, receipt.status)
    return ReceiptRead.model_validate(receipt)


@router.get("/{receipt_id}", response_model=ReceiptRead)
async def get_receipt(
    receipt_id: uuid.UUID,
    session: DbDep,
) -> ReceiptRead:
    """Fetch a receipt by its UUID."""
    repo = ReceiptRepository(session)
    receipt = await repo.get_by_id(receipt_id)
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {receipt_id} not found.",
        )
    return ReceiptRead.model_validate(receipt)
