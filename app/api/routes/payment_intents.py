from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from app.api.deps import get_current_merchant, get_db
from app.db.models.payment_intent import PaymentIntent
from app.db.models.merchant import Merchant
from app.schemas.payment_intent import PaymentIntentCreate, PaymentIntentResponse

router = APIRouter(prefix="/payment_intents", tags=["payment_intents"])


@router.post("/", response_model=PaymentIntentResponse)
def create_payment_intent(
    payload: PaymentIntentCreate,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
    ):

    payment_intent = PaymentIntent(
        merchant_id=current_merchant.id,
        amount=payload.amount,
        currency=payload.currency,
        status="requires_payment_method",
    )

    db.add(payment_intent)
    db.commit()
    db.refresh(payment_intent)

    return payment_intent


@router.get("/{payment_intent_id}", response_model=PaymentIntentResponse)
def get_payment_intent(
    payment_intent_id: int,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)):

    payment_intent = (
        db.query(PaymentIntent).filter(
            PaymentIntent.id == payment_intent_id,
            PaymentIntent.merchant.id == current_merchant.id,
        ).first()
    )

    if payment_intent is None:
        raise HTTPException(status_code=404, detail="Payment intent not found.")
    
    return payment_intent

@router.get("/", response_model=List[PaymentIntentResponse])
def get_payment_intents(db: Session = Depends(get_db), current_merchant: Merchant = Depends(get_current_merchant)):

    payment_intents = (
        db.query(PaymentIntent)
        .filter(PaymentIntent.merchant_id == current_merchant.id)
        .order_by(PaymentIntent.id.desc())
        .all()
    )

    return payment_intents