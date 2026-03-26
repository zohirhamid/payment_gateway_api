"""Pydantic schemas used by the PaymentIntent API endpoints."""

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

class PaymentIntentConfirmResponse(BaseModel):
    payment_intent_id: int
    charge_id: int
    status: str

