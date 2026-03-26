from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Charge(Base):
    """Represents a single payment attempt for a `PaymentIntent`.

    Why this exists:
    - `PaymentIntent` models the intent to pay and its lifecycle.
    - `Charge` captures the outcome of the actual attempt (success/failure) and any
      failure reason, so the API can expose a stable record of what happened.

    MVP constraints:
    - Each `PaymentIntent` can have at most one `Charge` (`payment_intent_id` is unique).
    - A `Charge` is created when a `PaymentIntent` is confirmed.

    Attributes:
        id: Primary key.
        payment_intent_id: Associated PaymentIntent id (unique).
        amount: Amount attempted, in the smallest currency unit (e.g. cents).
        status: Attempt status (e.g. pending/succeeded/failed).
        failure_reason: Optional free-text reason when the attempt fails.
    """

    __tablename__ = "charges"

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_intent_id: Mapped[int] = mapped_column(
        ForeignKey("payment_intents.id"),
        nullable=False,
        unique=True,
    )
    amount: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
