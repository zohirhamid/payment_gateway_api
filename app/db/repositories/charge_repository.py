from sqlalchemy.orm import Session
from app.db.models.charge import Charge

def get_by_payment_intent_for_merchant(
    db: Session,
    *,
    payment_intent_id: int,
    merchant_id: int,
) -> Charge | None:
    return (
        db.query(Charge)
        .filter(
            Charge.payment_intent_id == payment_intent_id,
            Charge.merchant_id == merchant_id,
        ).first()
    )