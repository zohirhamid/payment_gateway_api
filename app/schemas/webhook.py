from pydantic import BaseModel

class WebhookPaymentData(BaseModel):
    payment_intent_id: int
    amount: int
    currency: str
    status: str

class WebhookEventPayload(BaseModel):
    id: int
    type: str
    data: WebhookPaymentData
