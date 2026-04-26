from __future__ import annotations

import logging
import traceback
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.extraction.classifier import classify
from src.extraction.extractors import EXTRACTORS
from src.models.receipt import Receipt, ReceiptStatus
from src.ocr.engine import extract_text
from src.repositories.receipt_repository import ReceiptRepository

logger = logging.getLogger(__name__)


async def process_receipt(receipt_id: uuid.UUID, db: AsyncSession) -> Receipt:
    """Run OCR + extraction on an already-persisted Receipt and update it in place.

    Args:
        receipt_id: UUID of the Receipt to process.
        db: Active async database session.

    Returns:
        The updated Receipt instance.

    Raises:
        LookupError: If no Receipt with receipt_id exists.
    """
    repo = ReceiptRepository(db)
    receipt = await repo.get_by_id(receipt_id)
    if receipt is None:
        raise LookupError(f"Receipt {receipt_id} not found.")

    logger.info("processing receipt id=%s path=%s", receipt_id, receipt.image_path)

    try:
        raw_text, confidence = extract_text(Path(receipt.image_path))
        doc_type = classify(raw_text)
        extractor = EXTRACTORS.get(doc_type)
        extracted = extractor(raw_text) if extractor is not None else {}

        receipt.raw_ocr_text = raw_text
        receipt.ocr_confidence = confidence
        receipt.document_type = doc_type

        for field, value in extracted.items():
            setattr(receipt, field, value)

        has_amount = extracted.get("amount") is not None
        has_extra = any(
            extracted.get(f) is not None
            for f in ("operation_code", "issued_at", "recipient_name")
        )
        receipt.status = (
            ReceiptStatus.PROCESSED if has_amount and has_extra else ReceiptStatus.NEEDS_REVIEW
        )

    except Exception:
        receipt.status = ReceiptStatus.FAILED
        receipt.error_message = traceback.format_exc()
        logger.error("OCR failed for receipt id=%s\n%s", receipt_id, receipt.error_message)

    await db.flush()
    await db.refresh(receipt)

    logger.info(
        "finished receipt id=%s document_type=%s status=%s",
        receipt_id,
        receipt.document_type,
        receipt.status,
    )
    return receipt
