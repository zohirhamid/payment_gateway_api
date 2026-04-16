from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.enums import ChargeStatus, RefundReason, RefundStatus
from app.core.exceptions import ChargeNotFoundError, ChargeStateError, RefundNotFoundError
from app.db.models.charge import Charge
from app.db.models.refund import Refund


def create_refund_record(db: Session, charge: Charge, amount: int, reason: RefundReason) -> Refund:
    '''
    create a new refund row in PENDING state
    '''
    refund = Refund(
        charge_id=charge.id,
        payment_intent_id=charge.payment_intent_id,
        merchant_id=charge.merchant_id,
        amount=amount,
        currency=charge.currency,
        status=RefundStatus.PENDING,
        reason=reason,
    )
    db.add(refund)
    db.commit()
    db.refresh(refund)
    return refund


def validate_refund_request(
    db: Session,
    merchant_id: int,
    charge_id: int,
) -> tuple[Charge, int]:
    '''
    check if refund is allowed
    - charge exists & belongs to merchant
    - charge is refundable
    - amount is valid
    - refund won't exceed captured amount
    '''
    charge = (
        db.query(Charge)
        .filter(Charge.id == charge_id, Charge.merchant_id == merchant_id)
        .first()
    )

    if charge is None:
        raise ChargeNotFoundError("Charge not found.")

    if charge.status != ChargeStatus.CAPTURED:
        raise ChargeStateError("Charge is not refundable in its current state.")

    refundable_amount = calculate_refundable_amount(charge)
    if refundable_amount <= 0:
        raise ChargeStateError("Charge has already been fully refunded.")

    return charge, refundable_amount


def calculate_refundable_amount(charge: Charge) -> int:
    '''
    return how much money is still refundable for a charge
    '''
    refundable_amount = charge.amount - charge.refunded_amount
    return refundable_amount if refundable_amount > 0 else 0


def simulate_refund_result() -> str:
    '''
    Simulate a refund outcome. Current implementation is deterministic for prototype stability.
    '''
    return "succeeded"


def process_refund(
    db: Session,
    merchant_id: int,
    charge_id: int,
    reason: RefundReason,
) -> Refund:
    
    charge, refundable_amount = validate_refund_request(
        db=db,
        merchant_id=merchant_id,
        charge_id=charge_id,
    )

    refund = create_refund_record(
        db=db,
        charge=charge,
        amount=refundable_amount,
        reason=reason,
    )

    result = simulate_refund_result()

    if result == "succeeded":
        mark_refund_succeeded(db=db, refund=refund, charge=charge)
    else:
        mark_refund_failed(
            db=db,
            refund=refund,
            failure_reason="Refund processor declined the request.",
        )

    return refund


def mark_refund_succeeded(db: Session, refund: Refund, charge: Charge) -> Refund:
    '''
    Set refund status to succeeded and timestamps.
    '''
    refund.status = RefundStatus.SUCCEEDED
    refund.succeeded_at = datetime.now(timezone.utc)
    charge.refunded_amount += refund.amount
    db.add(refund)
    db.add(charge)
    db.commit()
    db.refresh(refund)
    db.refresh(charge)
    return refund


def mark_refund_failed(db: Session, refund: Refund, failure_reason: str) -> Refund:
    '''
    Set refund status to failed, timestamps, and failure reason.
    '''
    refund.status = RefundStatus.FAILED
    refund.failure_reason = failure_reason
    refund.failed_at = datetime.now(timezone.utc)
    db.add(refund)
    db.commit()
    db.refresh(refund)
    return refund


def get_refund(db: Session, merchant_id: int, refund_id: int) -> Refund:
    '''
    Fetch one refund by ID with merchant ownership checks.
    '''
    refund = (
        db.query(Refund)
        .filter(Refund.id == refund_id, Refund.merchant_id == merchant_id)
        .first()
    )
    if refund is None:
        raise RefundNotFoundError("Refund not found.")
    return refund


def list_refunds_for_charge(db: Session, merchant_id: int, charge_id: int) -> list[Refund]:
    '''
    Return all refunds linked to a charge.
    '''
    return (
        db.query(Refund)
        .filter(Refund.charge_id == charge_id, Refund.merchant_id == merchant_id)
        .order_by(Refund.id)
        .all()
    )
