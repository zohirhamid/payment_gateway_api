from pydantic import BaseModel
from datetime import datetime

class ChargeResponse(BaseModel):
    id: int
    payment_intent_id: int
    amount: int
    status: str
    failure_reason: str | None
    created_at: datetime

    class Config:
        from_attributes = True
    
