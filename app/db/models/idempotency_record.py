from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IdempotencyRecord(Base):
    """
    Stores the result of a previously processed write request.

    This lets the API safely handle client retries without creating
    duplicate resources or duplicate payment processing.

    In this MVP, idempotency is scoped by:
    - merchant
    - endpoint
    - idempotency key
    """

    __tablename__ = "idempotency_records"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Merchant that made the original request
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False)

    # Logical endpoint name, e.g. "create_payment_intent" or "confirm_payment_intent"
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)

    # Client-provided idempotency key
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)

    # Hash of the original request payload
    request_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Stored response details so the original response can be replayed
    response_status_code: Mapped[int] = mapped_column(nullable=False)
    response_body: Mapped[str] = mapped_column(String, nullable=False)