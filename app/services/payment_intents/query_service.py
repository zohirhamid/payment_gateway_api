from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.enums import PaymentIntentStatus
from app.db.models.payment_intent import PaymentIntent


def get_payment_intent(
    *,
    db: Session,
    merchant_id: int,
    payment_intent_id: int,
) -> PaymentIntent:
    """
    Fetch a single payment intent scoped to a merchant.
    """
    payment_intent = (
        db.query(PaymentIntent)
        .filter(
            PaymentIntent.id == payment_intent_id,
            PaymentIntent.merchant_id == merchant_id,
        )
        .first()
    )

    if payment_intent is None:
        raise HTTPException(status_code=404, detail="Payment intent not found.")

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
    """
    List payment intents scoped to a merchant.

    Inputs:
        db: SQLAlchemy session.
        merchant_id: Authenticated merchant id (ownership scope).
        status: Optional filter by PaymentIntent status.
        currency: Optional filter by 3-letter currency (case-insensitive).
        amount_gte: Optional minimum amount (inclusive).
        amount_lte: Optional maximum amount (inclusive).
        created_at_gte: Optional earliest created_at (inclusive).
        created_at_lte: Optional latest created_at (inclusive).
        limit: Max rows to return.
        offset: Rows to skip (pagination).

    Output:
        List of PaymentIntent model instances, newest-first.
    """
    limit = max(1, min(limit, 500))
    offset = max(0, offset)

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
