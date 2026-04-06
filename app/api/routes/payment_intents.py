from typing import List
import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant, get_db, get_idempotency_key
from app.utils.hashing import hash_request_payload

from app.db.models.merchant import Merchant
from app.db.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import PaymentIntentCreate, PaymentIntentResponse

from app.db.models.charge import Charge
from app.schemas.payment_intent import PaymentIntentConfirmResponse

from app.services.payment_service import build_webhook_payload, simulate_payment_result
from app.services.webhook_service import create_webhook_event, deliver_webhook_event_task

from app.services.idempotency_service import (
    create_idempotency_record,
    get_idempotency_record,
)

router = APIRouter(prefix="/payment_intents", tags=["payment_intents"])


@router.post("/", response_model=PaymentIntentResponse)
def create_payment_intent(
    payload: PaymentIntentCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
    idempotency_key: str | None = Depends(get_idempotency_key)
):
    """
    Create a new PaymentIntent for the authenticated merchant.

    If an Idempotency-Key header is provided and a matching prior request
    exists with the same payload, the original response is replayed.
    """

    # idempotency
    request_hash = hash_request_payload(payload.model_dump())

    if idempotency_key:
        existing_record = get_idempotency_record(
            db=db,
            merchant_id=current_merchant.id,
            endpoint="create_payment_intent",
            idempotency_key=idempotency_key,
        )

        if existing_record:
            if existing_record.request_hash != request_hash:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key was already used with a different payload.",
                )
            # return existing response
            return PaymentIntentResponse(**json.loads(existing_record.response_body))
    
    # First time?
    payment_intent = PaymentIntent(
        merchant_id=current_merchant.id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        status="requires_payment_method",
    )

    db.add(payment_intent)
    db.commit()
    db.refresh(payment_intent)

    response_payload = {
        "id": payment_intent.id,
        "merchant_id": payment_intent.merchant_id,
        "amount": payment_intent.amount,
        "currency": payment_intent.currency,
        "status": payment_intent.status,
        "created_at": payment_intent.created_at.isoformat(), # type: ignore
    }

    if idempotency_key:
        create_idempotency_record(
            db=db,
            merchant_id=current_merchant.id,
            endpoint="create_payment_intent",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_status_code=200,
            response_body=json.dumps(response_payload),
        )

    return payment_intent

@router.get("/{payment_intent_id}", response_model=PaymentIntentResponse)
def get_payment_intent(
    payment_intent_id: int,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
):
    """Fetch a single PaymentIntent belonging to the authenticated merchant.

    Takes:
        payment_intent_id: Path parameter for the PaymentIntent id.
        db: SQLAlchemy session injected by `Depends(get_db)`.
        current_merchant: Authenticated merchant injected by `get_current_merchant`.

    Returns:
        The requested PaymentIntent if it exists and belongs to the merchant.

    Raises:
        HTTPException: 404 if the PaymentIntent does not exist (or is not accessible).
    """

    payment_intent = (
        db.query(PaymentIntent)
        .filter(
            PaymentIntent.id == payment_intent_id,
            PaymentIntent.merchant_id == current_merchant.id,
        )
        .first()
    )

    if payment_intent is None:
        raise HTTPException(status_code=404, detail="Payment intent not found.")

    return payment_intent

@router.get("/", response_model=List[PaymentIntentResponse])
def get_payment_intents(
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
):
    """List PaymentIntents for the authenticated merchant.

    Takes:
        db: SQLAlchemy session injected by `Depends(get_db)`.
        current_merchant: Authenticated merchant injected by `get_current_merchant`.

    Returns:
        A list of PaymentIntents, newest first.
    """

    payment_intents = (
        db.query(PaymentIntent)
        .filter(PaymentIntent.merchant_id == current_merchant.id)
        .order_by(PaymentIntent.id.desc())
        .all()
    )

    return payment_intents

@router.post("/{payment_intent_id}/confirm", response_model=PaymentIntentConfirmResponse)
def confirm_payment_intent(
    payment_intent_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
    idempotency_key: str | None = Depends(get_idempotency_key),
):
    """
    Confirm a payment intent and simulate a payment attempt.

    Flow:
    - Optionally replay a previous response if the same idempotency key was used
    - Ensure the payment intent exists and belongs to the merchant
    - Ensure it is in a confirmable state
    - Create a charge
    - Simulate payment success/failure
    - Update both charge and payment intent
    - Create a webhook event
    - Schedule webhook delivery in the background
    """

    # Created a hashed payload
    confirm_payload = { # the id of a specific payment intent
        "payment_intent_id": payment_intent_id
        }
    request_hash = hash_request_payload(confirm_payload)

    # 
    if idempotency_key:
        existing_record = get_idempotency_record(
            db=db,
            merchant_id=current_merchant.id,
            endpoint="confirm_payment_intent",
            idempotency_key=idempotency_key,
        )

        if existing_record:
            if existing_record.request_hash != request_hash:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency key was already used with a different payload.",
                )

            return PaymentIntentConfirmResponse(**json.loads(existing_record.response_body))

    payment_intent = ( # get the current payment intent and check if it belongs to the current merchant
        db.query(PaymentIntent)
        .filter(
            PaymentIntent.id == payment_intent_id,
            PaymentIntent.merchant_id == current_merchant.id,
        )
        .first()
    )

    if payment_intent is None:
        raise HTTPException(status_code=404, detail="Payment intent not found.")
    
    
    # A payment intent can only be confirmed once in this MVP.
    # After confirmation, it moves to a terminal state:
    # - succeeded
    # - failed
    #
    # This prevents duplicate charge creation from repeated confirm calls.
    if payment_intent.status != "requires_payment_method":
        raise HTTPException(
            status_code=409,
            detail="Payment intent cannot be confirmed in its current state.",
        )

    # Step 1: Create charge
    charge = Charge( # Create a charge for the current paymentIntent
        payment_intent_id=payment_intent.id,
        amount=payment_intent.amount,
        status="pending",
    )
    db.add(charge)

    # Step 2: simulates the payment outcome
    result = simulate_payment_result()

    if result == "succeeded":
        charge.status = "succeeded"
        payment_intent.status = "succeeded"
    else:
        charge.status = "failed"
        charge.failure_reason = "Payment was declined"
        payment_intent.status = "failed"

    # Save charge to database
    db.commit()
    db.refresh(charge)
    db.refresh(payment_intent)


    # Creates a webhook event (for the payment result)
    event_type = (
        "payment.succeeded"
        if payment_intent.status == "succeeded"
        else "payment.failed"
    )

    webhook_payload = build_webhook_payload(payment_intent=payment_intent, event_id=0)

    webhook_event = create_webhook_event(
        db=db,
        merchant_id=current_merchant.id,
        payment_intent_id=payment_intent.id,
        event_type=event_type,
        payload=webhook_payload,
    )

    background_tasks.add_task(
        deliver_webhook_event_task,
        webhook_event.id,
    )

    response_payload = {
        "payment_intent_id": payment_intent.id,
        "charge_id": charge.id,
        "status": payment_intent.status,
    }

    if idempotency_key:
        create_idempotency_record(
            db=db,
            merchant_id=current_merchant.id,
            endpoint="confirm_payment_intent",
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_status_code=200,
            response_body=json.dumps(response_payload),
        )

    return response_payload
