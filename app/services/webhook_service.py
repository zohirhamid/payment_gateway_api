from datetime import datetime
import json
from time import timezone
import httpx

from sqlalchemy.orm import Session
from app.db.models.merchant import Merchant
from app.db.models.webhook_event import WebhookEvent

import json
from sqlalchemy.orm import Session
from app.db.models.webhook_event import WebhookEvent
from app.db.session import SessionLocal

MAX_WEBHOOK_RETRIES = 5

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
        payload=json.dumps(payload), # Serialize payload
        delivery_status="pending",
    )

    db.add(webhook_event)
    db.commit()
    db.refresh(webhook_event)

    return webhook_event


def can_retry_webhook_event(webhook_event: WebhookEvent) -> bool:
    return (
        webhook_event.delivery_status == "failed"
        and webhook_event.retry_count < MAX_WEBHOOK_RETRIES
    )


def deliver_webhook_event(
        db: Session,
        webhook_event: WebhookEvent,
        webhook_url: str) -> WebhookEvent:
    '''
    Deliver one webhook event to one merchant webhook URL and update its delivery status.

    1. Deserialize the stored payload from the DB
    2. Send an HTTP POST to the merchant webhook URL 
        3. if the response is successful, mark the event as "delivered"
        4. otherwise mark it as "failed"
    5. Commit the DB change
    6. Return something useful, like the updated event or a boolean
    '''
    webhook_event.last_attempt_at = datetime.now(timezone.utc)  # type: ignore[assignment]

    if not webhook_url:
        webhook_event.delivery_status = "failed"
        webhook_event.retry_count += 1
        webhook_event.last_error = "Missing webhook URL."
        db.commit()
        db.refresh(webhook_event)
        return webhook_event

    try:
        payload = json.loads(webhook_event.payload)
        
        response = httpx.post(
            webhook_url,
            json=payload,
            timeout=5.0,
        )

        if 200 <= response.status_code < 300:
            webhook_event.delivery_status = "delivered"
            webhook_event.last_error = None
        else:
            webhook_event.delivery_status = "failed"
            webhook_event.retry_count += 1
            webhook_event.last_error = f"Non-2xx response: {response.status_code}"

    except json.JSONDecodeError:
        webhook_event.delivery_status = "failed"
        webhook_event.retry_count += 1
        webhook_event.last_error = "Stored payload is not valid JSON."

    except httpx.TimeoutException:
        webhook_event.delivery_status = "failed"
        webhook_event.retry_count += 1
        webhook_event.last_error = "Webhook delivery timed out."

    except httpx.HTTPError as exc:
        webhook_event.delivery_status = "failed"
        webhook_event.retry_count += 1
        webhook_event.last_error = f"HTTP error during webhook delivery: {str(exc)}"

    db.commit()
    db.refresh(webhook_event)
    return webhook_event

def deliver_webhook_event_task(webhook_event_id: int):
    """
    Background-task safe wrapper for webhook delivery.

    This function must not rely on the request-scoped database session,
    because it runs after the HTTP response is sent. Instead, it creates
    a fresh DB session, loads the webhook event and merchant, then calls
    the lower-level delivery function.
    """
    db = SessionLocal()

    try:
        webhook_event = (
            db.query(WebhookEvent)
            .filter(WebhookEvent.id == webhook_event_id)
            .first()
        )

        if webhook_event is None:
            return
        
        merchant = (
            db.query(Merchant)
            .filter(Merchant.id == webhook_event.merchant_id)
            .first()
        )

        if merchant is None or not merchant.webhook_url:
            webhook_event.last_attempt_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            webhook_event.delivery_status = "failed"
            webhook_event.retry_count += 1
            webhook_event.last_error = "Merchant not found or webhook URL missing."
            db.commit()
            return
        
        deliver_webhook_event(
            db=db,
            webhook_event=webhook_event,
            webhook_url=merchant.webhook_url
        )

    finally:
        db.close()