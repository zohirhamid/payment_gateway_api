import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant, get_db
from app.core.security import bearer_scheme, get_bearer_token
from app.db.models.merchant import Merchant
from app.schemas.merchant import MerchantCreateResponse, MerchantResponse
from app.utils.api_key import generate_api_key
from app.utils.hashing import hash_api_key
from app.db.models.charge import Charge
from app.schemas.charge import ChargeResponse

router = APIRouter()


@router.get("/health")
def health_check():
    """Health check endpoint.

    Why this exists:
        Provides a lightweight way for deploy/runtime tooling to verify the API
        process is up and responding.

    Returns:
        A small JSON payload indicating status.
    """

    return {"status": "ok"}

# List[MerchantResponse]: this endpoint returns a list where each item should match MerchantResponse
@router.get("/merchants", response_model=List[MerchantResponse])
def list_test_merchants(db: Session = Depends(get_db)):
    """List merchants (debug-only).

    Why this exists:
        Useful during local development to quickly inspect what test merchants
        exist in the database.

    Takes:
        db: SQLAlchemy session injected by `Depends(get_db)`.

    Returns:
        A list of merchants serialized as `MerchantResponse`.
    """

    merchants = db.query(Merchant).all()
    return merchants


@router.get("/debug-token")
def debug_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Echo the bearer token parsed from the `Authorization` header.

    What it does:
        Uses FastAPI's HTTP Bearer dependency to parse `Authorization: Bearer <token>`
        into a credentials object, then extracts the raw token string.

    Takes:
        credentials: Parsed HTTP Bearer auth credentials.

    Returns:
        JSON payload containing the extracted `token` string.
    """

    token = get_bearer_token(credentials)
    return {"token": token}


@router.get("/test-charges", response_model=List[ChargeResponse])
def list_test_charges(db: Session = Depends(get_db)):
    charges = (
        db.query(Charge)
        .order_by(Charge.id.desc())
        .all()
    )
    return charges


@router.get("/test-charges/{charge_id}", response_model=ChargeResponse)
def get_test_charge(charge_id: int, db: Session = Depends(get_db)):
    charge = db.query(Charge).filter(Charge.id == charge_id).first()

    if charge is None:
        raise HTTPException(status_code=404, detail="Charge not found.")

    return charge