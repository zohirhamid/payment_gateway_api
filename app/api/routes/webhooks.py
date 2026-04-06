import json
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant, get_db
from app.db.models.merchant import Merchant

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.db.models.webhook_event import WebhookEvent
from app.schemas.webhook import (
    BulkWebhookRetryResponse,
    WebhookEventResponse,
    WebhookRetryResponse,
)
from app.services.webhook_service import (
    MAX_WEBHOOK_RETRIES,
    can_retry_webhook_event,
    deliver_webhook_event_task,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/test-receiver")
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


@router.get("/events", response_model=list[WebhookEventResponse])
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


@router.post("/events/{event_id}/retry", response_model=WebhookRetryResponse)
def retry_webhook_event(
    event_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    webhook_event = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.id == event_id)
        .first()
    )

    if webhook_event is None:
        raise HTTPException(status_code=404, detail="Webhook event not found.")

    if webhook_event.delivery_status == "delivered":
        raise HTTPException(
            status_code=409,
            detail="Webhook event has already been delivered.",
        )

    if webhook_event.retry_count >= MAX_WEBHOOK_RETRIES:
        raise HTTPException(
            status_code=409,
            detail="Webhook event has reached the maximum retry limit.",
        )

    if not can_retry_webhook_event(webhook_event):
        raise HTTPException(
            status_code=409,
            detail="Webhook event is not eligible for retry.",
        )

    background_tasks.add_task(deliver_webhook_event_task, webhook_event.id)

    return {
        "id": webhook_event.id,
        "delivery_status": webhook_event.delivery_status,
        "retry_count": webhook_event.retry_count,
        "message": "Webhook retry scheduled.",
    }


@router.post("/retry-failed", response_model=BulkWebhookRetryResponse)
def retry_failed_webhook_events(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    failed_events = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.delivery_status == "failed")
        .order_by(WebhookEvent.id.asc())
        .all()
    )

    eligible_events = [
        event for event in failed_events
        if can_retry_webhook_event(event)
    ]

    for event in eligible_events:
        background_tasks.add_task(deliver_webhook_event_task, event.id)

    return {
        "scheduled_count": len(eligible_events),
        "event_ids": [event.id for event in eligible_events],
        "message": "Eligible failed webhook events have been scheduled for retry.",
    }