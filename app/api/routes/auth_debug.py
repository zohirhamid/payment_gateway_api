import uuid
from typing import List

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant, get_db
from app.core.security import bearer_scheme, get_bearer_token
from app.db.models.merchant import Merchant
from app.schemas.merchant import MerchantCreateResponse, MerchantResponse
from app.utils.api_key import generate_api_key
from app.utils.hashing import hash_api_key

router = APIRouter()

@router.get("/health")
def health_check():
    return {
        "status": "ok"
        }
'''
@router.post("/test-merchants", response_model=MerchantCreateResponse)
def create_test_merchant(db: Session = Depends(get_db)):
    raw_api_key = generate_api_key()
    hashed_api_key = hash_api_key(raw_api_key)

    merchant = Merchant(
        name="Test Merchant",
        api_key_hash=hashed_api_key,
        webhook_url="https://example.com/webhook",
        )

    db.add(merchant)
    db.commit()
    db.refresh(merchant)

    return {
        "id": merchant.id,
        "name": merchant.name,
        "api_key": raw_api_key,
    }
    '''


# List[MerchantResponse]: this endpoint returns a list where each item should match MerchantResponse
@router.get("/merchants", response_model=List[MerchantResponse])
def list_test_merchants(db: Session = Depends(get_db)):
    merchants = db.query(Merchant).all()

    return merchants

@router.get("/debug-token")
def debug_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    '''
    Depends(bearer_scheme): read the authorization header using the HTTP Bearer parser.
    if u send "Authorization: Bearer pg_live_abc123" FastAPI turns that into a credentials object.
    '''
    token = get_bearer_token(credentials)
    return {"token": token}


'''
# depends: "before running this endpoint, execute this function and give me its result"
@router.get("/me", response_model=MerchantResponse)
def read_me(current_merchant: Merchant = Depends(get_current_merchant)):
    return current_merchant
'''