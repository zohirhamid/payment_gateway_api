from app.db.models.payment_intent import PaymentIntent


def _build_payment_intent_response(payment_intent: PaymentIntent) -> dict:
    return {
        "id": payment_intent.id,
        "merchant_id": payment_intent.merchant_id,
        "amount": payment_intent.amount,
        "currency": payment_intent.currency,
        "status": getattr(payment_intent.status, "value", payment_intent.status),
        "created_at": payment_intent.created_at.isoformat(),  # type: ignore[union-attr]
    }

