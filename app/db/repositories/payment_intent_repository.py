from datetime import datetime
from sqlalchemy.orm import Session

from app.core.enums import PaymentIntentStatus
from app.db.models.payment_intent import PaymentIntent


def create_intent(
    db: Session,
    *,
    merchant_id: int,
    amount: int,
    currency: str,
    status: PaymentIntentStatus,
) -> PaymentIntent:
    payment_intent = PaymentIntent(
        merchant_id=merchant_id,
        amount=amount,
        currency=currency,
        status=status
    )

    return payment_intent


def get_by_id_for_merchant(
    db: Session,
    *,
    payment_intent_id: int,
    merchant_id: int,
) -> PaymentIntent | None:
    return (
        db.query(PaymentIntent)
        .filter(
            PaymentIntent.id == payment_intent_id,
            PaymentIntent.merchant_id == merchant_id,
        ).first()
    )


def list_for_merchant(
    db: Session,
    *,
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
    query = db.query(PaymentIntent).filter(PaymentIntent.merchant_id == merchant_id)

    if status is not None:
        query = query.filter(PaymentIntent.status == status)
    if currency:
        query = query.filter(PaymentIntent.currency == currency.upper())
    if amount_gte is not None:
        query = query.filter(PaymentIntent.amount >= amount_gte)
    if amount_lte is not None:
        query = query.filter(PaymentIntent.amount <= amount_lte)
    if created_at_gte is not None:
        query = query.filter(PaymentIntent.created_at >= created_at_gte)
    if created_at_lte is not None:
        query = query.filter(PaymentIntent.created_at <= created_at_lte)

    return (
        query.order_by(PaymentIntent.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

