from app.core.enums import PaymentIntentStatus

ALLOWED_TRANSITIONS: dict[PaymentIntentStatus, set[PaymentIntentStatus]] = {
    PaymentIntentStatus.REQUIRES_PAYMENT_METHOD: {
        PaymentIntentStatus.REQUIRES_CONFIRMATION,
        PaymentIntentStatus.CANCELED,
    },
    PaymentIntentStatus.REQUIRES_CONFIRMATION: {
        PaymentIntentStatus.PROCESSING,
        PaymentIntentStatus.CANCELED,
    },
    PaymentIntentStatus.PROCESSING: {
        PaymentIntentStatus.SUCCEEDED,
        PaymentIntentStatus.FAILED,
    },
    PaymentIntentStatus.SUCCEEDED: set(),
    PaymentIntentStatus.FAILED: set(),
    PaymentIntentStatus.CANCELED: set(),
}


def transition_status(
    current_status: PaymentIntentStatus,
    new_status: PaymentIntentStatus
) -> PaymentIntentStatus:

    allowed_next_states = ALLOWED_TRANSITIONS.get(current_status, set())

    if new_status not in allowed_next_states:
        raise ValueError(
            f"Invalid transition from {current_status} to {new_status}"
        )
    
    return new_status