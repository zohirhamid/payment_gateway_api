from sqlalchemy import DateTime, ForeignKey, String, func, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.enums import PaymentIntentStatus


from app.db.base import Base

class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[PaymentIntentStatus] = mapped_column(
        Enum(PaymentIntentStatus, name="payment_intent_status"),
        nullable=False,
        default=PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
    )
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    #payment_method_reference: Mapped[] = mapped_column() (a reference to payment_methods table)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    confirmed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    processing_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    succeeded_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))