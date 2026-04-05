import hashlib
import json

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

def hash_request_payload(payload: dict) -> str:
    '''
    Create a stable hash for a request payload.

    The payload is converted to a sorted JSON first so the same logical
    data produces the same hash even if key order differs

    Idempotency is not just "same key"
    Its really:
        - same merchant
        - same endpoint
        - same idempotency key
        - same request payload
    This helper gives us the payload fingerprint piece.

    side note: Payload = the meaningful data sent in the body of a request.
    '''
    normalized_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized_payload.encode()).hexdigest()