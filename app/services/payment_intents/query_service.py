from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import PaymentIntentStatus
from app.core.exceptions import PaymentIntentNotFoundError
from app.db.models.payment_intent import PaymentIntent
from app.db.repositories.payment_intent_repository import list_for_merchant, get_by_id_for_merchant

def get_payment_intent(
    *,
    db: Session,
    merchant_id: int,
    payment_intent_id: int,
) -> PaymentIntent:
    """
    Fetch a single payment intent scoped to a merchant.
    """
    payment_intent = get_by_id_for_merchant(
        db=db,
        payment_intent_id=payment_intent_id,
        merchant_id=merchant_id
    )

    if payment_intent is None:
        raise PaymentIntentNotFoundError("Payment intent not found.")

    return payment_intent


def list_payment_intents(
    *,
    db: Session,
    merchant_id: int,
    status: PaymentIntentStatus | None = None,
    currency: str | None = None,
    amount_gte: int | None = None,
    amount_lte: int | None = None,
    created_at_gte: datetime | None = None,
    created_at_lte: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[PaymentIntent]:

    limit = max(1, min(limit, 500))
    offset = max(0, offset)

    return list_for_merchant(
        db=db,
        merchant_id=merchant_id,
        status=status,
        currency=currency,
        amount_gte=amount_gte,
        amount_lte=amount_lte,
        created_at_gte=created_at_gte,
        created_at_lte=created_at_lte,
        limit=limit,
        offset=offset,
    )
