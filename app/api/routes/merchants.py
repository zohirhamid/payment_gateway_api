from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_merchant, get_db
from app.db.models.merchant import Merchant
from app.schemas.merchant import MerchantCreateResponse, MerchantResponse
from app.utils.api_key import generate_api_key
from app.utils.hashing import hash_api_key

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.post("/", response_model=MerchantCreateResponse)
def create_merchant(db: Session = Depends(get_db)):
    raw_api_key = generate_api_key()
    hashed_api_key = hash_api_key(raw_api_key)

    merchant = Merchant(
        name="Test Merchant",
        api_key_hash=hashed_api_key,
        webhook_url="http://127.0.0.1:8000/webhooks/test-receiver",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)

    return {
        "id": merchant.id,
        "name": merchant.name,
        "api_key": raw_api_key,
    }

# depends: "before running this endpoint, execute this function and give me its result"
@router.get("/me", response_model=MerchantResponse)
def read_me(current_merchant: Merchant = Depends(get_current_merchant)):
    return current_merchant