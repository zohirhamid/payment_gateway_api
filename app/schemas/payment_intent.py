"""Pydantic schemas used by the PaymentIntent API endpoints."""

from datetime import datetime
from pydantic import BaseModel, Field


class PaymentIntentCreate(BaseModel):
    amount: int = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)


class PaymentIntentResponse(BaseModel):
    id: int
    merchant_id: int
    amount: int
    currency: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentIntentConfirmResponse(BaseModel):
    payment_intent_id: int
    charge_id: int
    status: str
