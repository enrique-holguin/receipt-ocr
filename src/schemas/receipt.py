import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from src.models.receipt import DocumentType, ReceiptStatus


class ReceiptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_type: DocumentType
    merchant_name: str | None
    merchant_ruc: str | None
    amount: Decimal | None
    currency: str
    issued_at: datetime | None
    payment_method: str | None
    operation_code: str | None
    raw_ocr_text: str | None
    ocr_confidence: float | None
    recipient_name: str | None
    error_message: str | None
    image_path: str
    status: ReceiptStatus
    created_at: datetime
    updated_at: datetime
