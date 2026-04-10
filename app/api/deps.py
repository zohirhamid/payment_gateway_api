from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import bearer_scheme, get_bearer_token
from app.db.session import get_db
from app.services.auth_service import get_merchant_by_api_key

from importlib import import_module
from app.core.rate_limit import RateLimitRule, rate_limit

_redis_client = None


CREATE_PAYMENT_INTENT_RULE = RateLimitRule(
    scope="create_payment_intent",
    limit=5,
    window_seconds=60,
)

CONFIRM_PAYMENT_RULE = RateLimitRule(
    scope="confirm_payment",
    limit=10,
    window_seconds=60,
)

create_payment_intent_rate_limit = rate_limit(CREATE_PAYMENT_INTENT_RULE)
confirm_payment_rate_limit = rate_limit(CONFIRM_PAYMENT_RULE)

def get_redis():
    """Return a shared Redis client for request dependencies."""
    global _redis_client

    try:
        redis = import_module("redis")
    except ModuleNotFoundError as exc:
        raise RuntimeError("The redis package is required for get_redis().") from exc

    if _redis_client is None:
        redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
        _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

    return _redis_client

def get_current_merchant(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    '''
    This runs the full auth dependency:
        - open DB session
        - read bearer token
        - extract raw API key
        - hash it
        - find mercjant in DB
        - return 401 if invalid
        - return merchant if valid (authenticated merchant object)
    '''
    api_key = get_bearer_token(credentials)
    merchant = get_merchant_by_api_key(db, api_key)

    if merchant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    
    return merchant 

def get_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str | None:
    '''
    Read the Idempotency-Key header from the request.

    We keep this as a dependency so write endpoints can opt into idempotency support
    without manually parsing headers.
    '''
    return idempotency_key
