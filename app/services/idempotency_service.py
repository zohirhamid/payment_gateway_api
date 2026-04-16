import json

from sqlalchemy.orm import Session

from app.core.exceptions import IdempotencyConflictError
from app.db.models.idempotency_record import IdempotencyRecord


def get_idempotency_record(
        db: Session,
        merchant_id: int,
        endpoint: str,
        idempotency_key: str,
) -> IdempotencyRecord | None:
    '''Look up a previously stored idempotency record for a merchant + endpoint + key
    '''
    return (
        db.query(IdempotencyRecord)
        .filter(
            IdempotencyRecord.merchant_id == merchant_id,
            IdempotencyRecord.endpoint == endpoint,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
        .first()
    )


def check_idempotency(
    *,
    db: Session,
    merchant_id: int,
    endpoint: str,
    idempotency_key: str | None,
    request_hash: str,
) -> dict | None:
    """
    Return a stored response body for a matching idempotency request.

    If the key exists with a different payload hash, raise IdempotencyConflictError.
    """
    if not idempotency_key:
        return None

    existing_record = get_idempotency_record(
        db=db,
        merchant_id=merchant_id,
        endpoint=endpoint,
        idempotency_key=idempotency_key,
    )

    if existing_record is None:
        return None

    if existing_record.request_hash != request_hash:
        raise IdempotencyConflictError(
            "Idempotency key was already used with a different payload."
        )

    return json.loads(existing_record.response_body)


def create_idempotency_record(
    db: Session,
    merchant_id: int,
    endpoint: str,
    idempotency_key: str,
    request_hash: str,
    response_status_code: int,
    response_body: str,
) -> IdempotencyRecord:
    '''
    Save the result of a completed write request so it can be replayed
    safelt if the client retries with the same idempotency key.
    '''
    record = IdempotencyRecord(
        merchant_id=merchant_id,
        endpoint=endpoint,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        response_status_code=response_status_code,
        response_body=response_body,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
