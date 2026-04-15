import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.enums import PaymentIntentStatus
from app.db.models.payment_intent import PaymentIntent
from app.schemas.payment_intent import PaymentIntentCreate
from app.services.idempotency_service import check_idempotency, create_idempotency_record
from app.services.payment_intents.query_service import get_payment_intent
from app.services.payment_intents.response_builders import _build_payment_intent_response
from app.services.payment_state_machine import apply_payment_intent_status_transition
from app.utils.hashing import hash_request_payload


def create_payment_intent(
    *,
    db: Session,
    merchant_id: int,
    payload: PaymentIntentCreate,
    idempotency_key: str | None,
) -> dict:
    '''
    Output: Dict matching `PaymentIntentResponse` shape.
    '''

    endpoint = "create_payment_intent"
    request_hash = hash_request_payload(payload.model_dump())

    existing_response = check_idempotency(
        db=db,
        merchant_id=merchant_id,
        endpoint=endpoint,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
    )
    if existing_response is not None:
        return existing_response

    payment_intent = PaymentIntent(
        merchant_id=merchant_id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        status=PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
    )

    db.add(payment_intent)
    db.commit()
    db.refresh(payment_intent)

    response_payload = _build_payment_intent_response(payment_intent)

    if idempotency_key:
        create_idempotency_record(
            db=db,
            merchant_id=merchant_id,
            endpoint=endpoint,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_status_code=200,
            response_body=json.dumps(response_payload),
        )

    return response_payload

def attach_payment_method(
    *,
    db: Session,
    merchant_id: int,
    payment_intent_id: int,
    payment_method_reference: str,
) -> dict:
    payment_intent = get_payment_intent(
        db=db,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    if payment_intent.status != PaymentIntentStatus.REQUIRES_PAYMENT_METHOD:
        raise HTTPException(
            status_code=409,
            detail="Payment method cannot be attached in the current state.",
        )

    payment_intent.payment_method_reference = payment_method_reference

    payment_intent = apply_payment_intent_status_transition(
        db=db,
        payment_intent=payment_intent,
        new_status=PaymentIntentStatus.REQUIRES_CONFIRMATION,
    )

    return _build_payment_intent_response(payment_intent)

def cancel_payment_intent(
    *,
    db: Session,
    merchant_id: int,
    payment_intent_id: int,
    idempotency_key: str | None,
) -> dict:
    """
    Cancel a payment intent (only allowed before processing).

    Output:
        Dict matching `PaymentIntentResponse` shape.
    """

    endpoint = "cancel_payment_intent"
    request_hash = hash_request_payload({"payment_intent_id": payment_intent_id})

    existing_response = check_idempotency(
        db=db,
        merchant_id=merchant_id,
        endpoint=endpoint,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
    )
    if existing_response is not None:
        return existing_response

    payment_intent = get_payment_intent(
        db=db,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    if payment_intent.status not in {
        PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
        PaymentIntentStatus.REQUIRES_CONFIRMATION,
    }:
        raise HTTPException(
            status_code=409,
            detail="Payment intent cannot be canceled in its current state.",
        )

    payment_intent = apply_payment_intent_status_transition(
        db=db,
        payment_intent=payment_intent,
        new_status=PaymentIntentStatus.CANCELED,
    )

    response_payload = _build_payment_intent_response(payment_intent)

    if idempotency_key:
        create_idempotency_record(
            db=db,
            merchant_id=merchant_id,
            endpoint=endpoint,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_status_code=200,
            response_body=json.dumps(response_payload),
        )

    return response_payload
