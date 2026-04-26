import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin

_enum_values = lambda e: [m.value for m in e]  # noqa: E731


class DocumentType(enum.StrEnum):
    YAPE = "yape"
    PLIN = "plin"
    TRANSFER = "transfer"
    SUNAT_BOLETA = "sunat_boleta"
    SUNAT_FACTURA = "sunat_factura"
    OTHER = "other"
    UNKNOWN = "unknown"


class ReceiptStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class Receipt(Base, TimestampMixin):
    __tablename__ = "receipts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SAEnum(DocumentType, name="document_type", values_callable=_enum_values),
        nullable=False,
        default=DocumentType.UNKNOWN,
    )
    merchant_name: Mapped[str | None] = mapped_column(String, nullable=True)
    merchant_ruc: Mapped[str | None] = mapped_column(String(11), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String, nullable=True)
    operation_code: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    recipient_name: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ReceiptStatus] = mapped_column(
        SAEnum(ReceiptStatus, name="receipt_status", values_callable=_enum_values),
        nullable=False,
        default=ReceiptStatus.PENDING,
    )
