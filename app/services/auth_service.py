from sqlalchemy.orm import Session

from app.db.models.merchant import Merchant
from app.utils.hashing import hash_api_key

def get_merchant_by_api_key(db: Session, api_key: str) -> Merchant | None:
    hashed_api_key = hash_api_key(api_key)

    return (
        db.query(Merchant).filter(Merchant.api_key_hash == hashed_api_key).first()
    )



