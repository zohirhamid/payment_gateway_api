import json

from sqlalchemy.orm import Session

from app.core.enums import ChargeStatus, PaymentIntentStatus
from app.core.exceptions import (
    ChargeNotFoundError,
    ChargeStateError,
    PaymentIntentStateError,
)
from app.db.repositories.charge_repository import get_by_payment_intent_for_merchant
from app.services.charge_service import create_and_process_charge
from app.services.idempotency_service import (
    check_idempotency,
    create_idempotency_record,
)
from app.services.payment_intents.query_service import get_payment_intent
from app.services.payment_intents.response_builders import _build_payment_intent_response
from app.services.payment_service import build_webhook_payload
from app.services.payment_state_machine import apply_payment_intent_status_transition
from app.services.webhook_service import create_webhook_event
from app.utils.hashing import hash_request_payload


def confirm_payment_intent(
    *,
    db: Session,
    merchant_id: int,
    payment_intent_id: int,
    idempotency_key: str | None,
) -> tuple[dict, int | None]:
    """
    Confirm a payment intent and simulate a payment attempt.

    Output:
        (confirm_response_payload, webhook_event_id)

        If an idempotency record is replayed, webhook_event_id is None to avoid
        scheduling duplicate webhook delivery.
    """

    endpoint = "confirm_payment_intent"
    request_hash = hash_request_payload({"payment_intent_id": payment_intent_id})

    existing_response = check_idempotency(
        db=db,
        merchant_id=merchant_id,
        endpoint=endpoint,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
    )
    if existing_response is not None:
        return existing_response, None

    payment_intent = get_payment_intent(
        db=db,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    # Only confirm once in this MVP.
    if payment_intent.status not in {
        PaymentIntentStatus.REQUIRES_PAYMENT_METHOD,
        PaymentIntentStatus.REQUIRES_CONFIRMATION,
    }:
        raise PaymentIntentStateError(
            "Payment intent has already been processed or is not confirmable."
        )

    if payment_intent.status == PaymentIntentStatus.REQUIRES_PAYMENT_METHOD:
        payment_intent = apply_payment_intent_status_transition(
            db=db,
            payment_intent=payment_intent,
            new_status=PaymentIntentStatus.REQUIRES_CONFIRMATION,
        )

    payment_intent = apply_payment_intent_status_transition(
        db=db,
        payment_intent=payment_intent,
        new_status=PaymentIntentStatus.PROCESSING,
    )

    charge, failure_reason = create_and_process_charge(
        db=db,
        payment_intent=payment_intent,
        merchant_id=merchant_id,
    )

    payment_intent = apply_payment_intent_status_transition(
        db=db,
        payment_intent=payment_intent,
        new_status=(
            PaymentIntentStatus.REQUIRES_CAPTURE
            if charge.status == ChargeStatus.AUTHORIZED
            else PaymentIntentStatus.FAILED
        ),
        failure_reason=failure_reason,
    )

    if payment_intent.status == PaymentIntentStatus.SUCCEEDED:
        event_type = "payment.succeeded"
    elif payment_intent.status == PaymentIntentStatus.REQUIRES_CAPTURE:
        event_type = "payment.requires_capture"
    else:
        event_type = "payment.failed"

    webhook_payload = build_webhook_payload(
        payment_intent=payment_intent,
        event_id=0,
        event_type=event_type,
    )

    webhook_event = create_webhook_event(
        db=db,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent.id,
        event_type=event_type,
        payload=webhook_payload,
    )

    response_payload = {
        "payment_intent_id": payment_intent.id,
        "charge_id": charge.id,
        "status": getattr(payment_intent.status, "value", payment_intent.status),
    }

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

    return response_payload, webhook_event.id


def capture_payment_intent(
    *,
    db: Session,
    merchant_id: int,
    payment_intent_id: int,
    idempotency_key: str | None,
) -> tuple[dict, int | None]:
    """
    Capture a previously authorized payment intent.

    Output:
        (capture_response_payload, webhook_event_id)

        If an idempotency record is replayed, webhook_event_id is None to avoid
        scheduling duplicate webhook delivery.
    """

    endpoint = "capture_payment_intent"
    request_hash = hash_request_payload({"payment_intent_id": payment_intent_id})

    existing_response = check_idempotency(
        db=db,
        merchant_id=merchant_id,
        endpoint=endpoint,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
    )

    if existing_response is not None:
        return existing_response, None

    payment_intent = get_payment_intent(
        db=db,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
    )

    if payment_intent.status != PaymentIntentStatus.REQUIRES_CAPTURE:
        raise PaymentIntentStateError(
            "Payment intent cannot be captured in its current state."
        )

    charge = get_by_payment_intent_for_merchant(
        db=db,
        payment_intent_id=payment_intent_id,
        merchant_id=merchant_id,
    )

    if charge is None:
        raise ChargeNotFoundError("Charge not found.")

    if charge.status != ChargeStatus.AUTHORIZED:
        raise ChargeStateError("Charge is not in a capturable state.")

    charge.status = ChargeStatus.CAPTURED
    db.add(charge)
    db.commit()
    db.refresh(charge)

    payment_intent = apply_payment_intent_status_transition(
        db=db,
        payment_intent=payment_intent,
        new_status=PaymentIntentStatus.SUCCEEDED,
    )

    webhook_payload = build_webhook_payload(
        payment_intent=payment_intent,
        event_id=0,
        event_type="payment.succeeded",
    )

    webhook_event = create_webhook_event(
        db=db,
        merchant_id=merchant_id,
        payment_intent_id=payment_intent.id,
        event_type="payment.succeeded",
        payload=webhook_payload,
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

    return response_payload, webhook_event.id
