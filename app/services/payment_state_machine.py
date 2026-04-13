from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.enums import PaymentIntentStatus
from app.core.state_machine import transition_status
from app.db.models.payment_intent import PaymentIntent


def apply_payment_intent_status_transition(
        *,
        db: Session,
        intent: PaymentIntent,
        new_status: PaymentIntentStatus,
        occurred_at: datetime | None = None,
        failure_reason: str | None = None,
) -> PaymentIntent:
    
    current_status = intent.status
    
    validate_status = transition_status(
        current_status=current_status,
        new_status=new_status,
        )
    
    timestamp = occurred_at or datetime.now(timezone.utc)

    # update status
    intent.status = validate_status

    # Set timestamp
    timestamp_field = status_timestamp_field(validate_status)
    if timestamp_field:
        setattr(intent, timestamp_field, timestamp)

    # handle failure reason
    if validate_status == PaymentIntentStatus.FAILED:
        intent.failure_reason = failure_reason
    else:
        intent.failure_reason = None

    db.add(intent)
    db.commit()
    db.refresh(intent)

    return intent


def status_timestamp_field(status: PaymentIntentStatus) -> str | None:
    """
    Return the PaymentIntent timestamp attribute name for a given status.
    """
    if status == PaymentIntentStatus.REQUIRES_CONFIRMATION:
        return "confirmed_at"
    if status == PaymentIntentStatus.PROCESSING:
        return "processing_at"
    if status == PaymentIntentStatus.SUCCEEDED:
        return "succeeded_at"
    if status == PaymentIntentStatus.FAILED:
        return "failed_at"
    if status == PaymentIntentStatus.CANCELED:
        return "canceled_at"

    return None