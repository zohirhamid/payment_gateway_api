from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import bearer_scheme, get_bearer_token
from app.db.session import get_db
from app.services.auth_service import get_merchant_by_api_key
'''
this file is the central place for reusable dependencies like:
    get_db
    get_current_merchant
    maybe pagination deps
    maybe common query param deps
'''

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
