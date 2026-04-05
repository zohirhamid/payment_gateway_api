import json
import httpx

from sqlalchemy.orm import Session
from app.db.models.webhook_event import WebhookEvent

import json
from sqlalchemy.orm import Session
from app.db.models.webhook_event import WebhookEvent


def create_webhook_event(
    db: Session,
    merchant_id: int,
    payment_intent_id: int,
    event_type: str,
    payload: dict,
) -> WebhookEvent:
    """
    Persist a webhook event so it can be delivered to the merchant later.

    In this MVP, events are stored first and delivered afterward.
    This keeps event creation separate from delivery logic.
    """
    webhook_event = WebhookEvent(
        merchant_id=merchant_id,
        payment_intent_id=payment_intent_id,
        event_type=event_type,
        payload=json.dumps(payload),
        delivery_status="pending",
    )

    db.add(webhook_event)
    db.commit()
    db.refresh(webhook_event)

    return webhook_event

def deliver_webhook_event(
        db: Session,
        webhook_event: WebhookEvent,
        webhook_url: str) -> str:
    '''
    Deliver one webhook event to one merchant webhook URL and update its delivery status.

    1. Deserialize the stored payload from the DB
    2. send an HTTP POST to the merchant webhook URL
        3. if the response is successful, mark the event as "delivered"
        4. otherwise mark it as "failed"
    5. commit the DB change
    6. return something useful, like the updated event or a boolean
    '''
    payload = json.loads(webhook_event.payload)

    try:
        response = httpx.post(
            webhook_url,
            json=payload,
            timeout=5.0,
        )

        if 200 <= response.status_code < 300:
            webhook_event.delivery_status = "delivered"
        else:
            webhook_event.delivery_status = "failed"
    except httpx.RequestError:
        webhook_event.delivery_status = "failed"

    db.commit()
    db.refresh(webhook_event)

    return webhook_event.delivery_status