from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import (cancel_payment_rate_limit,
                          capture_payment_rate_limit,
                          confirm_payment_rate_limit,
                          create_payment_intent_rate_limit,
                          get_current_merchant, get_db, get_idempotency_key)
from app.core.enums import PaymentIntentStatus
from app.db.models.merchant import Merchant
from app.schemas.payment_intent import (PaymentIntentAttachPaymentMethod,
                                        PaymentIntentConfirmResponse,
                                        PaymentIntentCreate,
                                        PaymentIntentResponse)
from app.services.payment_intents.command_service import (
    attach_payment_method as attach_payment_method_service,
    cancel_payment_intent as cancel_payment_intent_service,
    create_payment_intent as create_payment_intent_service,
)
from app.services.payment_intents.orchestrator import (
    capture_payment_intent as capture_payment_intent_service,
    confirm_payment_intent as confirm_payment_intent_service,
)
from app.services.payment_intents.query_service import (
    get_payment_intent as get_payment_intent_service,
    list_payment_intents as list_payment_intents_service,
)


from app.services.webhook_service import deliver_webhook_event_task

router = APIRouter(prefix="/payment_intents", tags=["payment_intents"])


@router.post("/", dependencies=[Depends(create_payment_intent_rate_limit)], response_model=PaymentIntentResponse)
def create_payment_intent(
    payload: PaymentIntentCreate,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
    idempotency_key: str | None = Depends(get_idempotency_key)
):
    response_payload = create_payment_intent_service(
        db=db,
        merchant_id=current_merchant.id,
        payload=payload,
        idempotency_key=idempotency_key,
    )
    return PaymentIntentResponse(**response_payload)

@router.get("/{payment_intent_id}", response_model=PaymentIntentResponse)
def get_payment_intent(
    payment_intent_id: int,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)):
    return get_payment_intent_service(
        db=db,
        merchant_id=current_merchant.id,
        payment_intent_id=payment_intent_id,
    )

@router.get("/", response_model=List[PaymentIntentResponse])
def get_payment_intents(
    status: PaymentIntentStatus | None = None,
    currency: str | None = None,
    amount_gte: int | None = Query(default=None, ge=1),
    amount_lte: int | None = Query(default=None, ge=1),
    created_at_gte: datetime | None = None,
    created_at_lte: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),):
    
    return list_payment_intents_service(
        db=db,
        merchant_id=current_merchant.id,
        status=status,
        currency=currency,
        amount_gte=amount_gte,
        amount_lte=amount_lte,
        created_at_gte=created_at_gte,
        created_at_lte=created_at_lte,
        limit=limit,
        offset=offset,
    )

@router.post("/{payment_intent_id}/confirm", dependencies=[Depends(confirm_payment_rate_limit)], response_model=PaymentIntentConfirmResponse)
def confirm_payment_intent(
    payment_intent_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
    idempotency_key: str | None = Depends(get_idempotency_key),
):
    response_payload, webhook_event_id = confirm_payment_intent_service(
        db=db,
        merchant_id=current_merchant.id,
        payment_intent_id=payment_intent_id,
        idempotency_key=idempotency_key,
    )

    if webhook_event_id is not None:
        background_tasks.add_task(deliver_webhook_event_task, webhook_event_id)

    return PaymentIntentConfirmResponse(**response_payload)


@router.post(
    "/{payment_intent_id}/capture",
    dependencies=[Depends(capture_payment_rate_limit)],
    response_model=PaymentIntentResponse,
)
def capture_payment_intent(
    payment_intent_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
    idempotency_key: str | None = Depends(get_idempotency_key),
):
    response_payload, webhook_event_id = capture_payment_intent_service(
        db=db,
        merchant_id=current_merchant.id,
        payment_intent_id=payment_intent_id,
        idempotency_key=idempotency_key,
    )

    if webhook_event_id is not None:
        background_tasks.add_task(deliver_webhook_event_task, webhook_event_id)

    return PaymentIntentResponse(**response_payload)


@router.post(
    "/{payment_intent_id}/cancel",
    dependencies=[Depends(cancel_payment_rate_limit)],
    response_model=PaymentIntentResponse,
)
def cancel_payment_intent(
    payment_intent_id: int,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
    idempotency_key: str | None = Depends(get_idempotency_key)):

    payload = cancel_payment_intent_service(
        db=db,
        merchant_id=current_merchant.id,
        payment_intent_id=payment_intent_id,
        idempotency_key=idempotency_key,
    )
    
    return PaymentIntentResponse(**payload)


@router.post("/{payment_intent_id}/attach_payment_method", response_model=PaymentIntentResponse)
def attach_payment_method(
    payment_intent_id: int,
    payload: PaymentIntentAttachPaymentMethod,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant),
) -> PaymentIntentResponse:
    response_payload = attach_payment_method_service(
        db=db,
        merchant_id=current_merchant.id,
        payment_intent_id=payment_intent_id,
        payment_method_reference=payload.payment_method_reference,
    )
    return PaymentIntentResponse(**response_payload)
