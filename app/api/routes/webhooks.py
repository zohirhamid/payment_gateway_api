import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant, get_db
from app.db.models.merchant import Merchant
from app.db.models.webhook_event import WebhookEvent
from app.schemas.webhook import WebhookEventResponse

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/test-receiver")
def test_webhook_receiver(payload: dict):
    '''
    Simple local webhook receiver for testing webhook delivery.

    It accepts any JSON payload, prints it for debugging,
    and returns a success response.
    '''
    print("Received webhook payload:", payload)

    return {
        "reveived": True,
        "payload": payload,
    }


@router.get("/webhook/events", response_model=list[WebhookEventResponse])
def list_webhook_events(
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
):
    webhook_events = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.merchant_id == current_merchant.id)
        .order_by(WebhookEvent.id.desc())
        .all()
    )

    results: list[dict] = []
    for event in webhook_events:
        payload: dict
        try:
            payload = json.loads(event.payload)
        except json.JSONDecodeError:
            payload = {"raw": event.payload}

        results.append(
            {
                "id": event.id,
                "merchant_id": event.merchant_id,
                "payment_intent_id": event.payment_intent_id,
                "event_type": event.event_type,
                "delivery_status": event.delivery_status,
                "payload": payload,
                "created_at": event.created_at,
            }
        )

    return results
