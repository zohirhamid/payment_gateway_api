from fastapi import APIRouter, Request

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/test-receiver")
def test_webhook_receiver(payload: dict):
    '''
    Simple local webhook receiver for testing webhook delivery.

    It accepts any JSON payload, prints it for debugging,
    and returns a success response.
    '''
    print("Received webhook payload:", payload)

    return {
        "reveived": True,
        "payload": payload,
    }
