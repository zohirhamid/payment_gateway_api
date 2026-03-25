from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(scheme_name="BearerAuth")

def get_bearer_token(credentials: HTTPAuthorizationCredentials) -> str:
    if credentials.scheme.lower() != "bearer": # check that the auth scheme is really Bearer.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme.",
        )
    return credentials.credentials # returns the raw API key string only