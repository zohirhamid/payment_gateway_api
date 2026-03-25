from pydantic import BaseModel, Field

class PaymentIntentCreate(BaseModel):
    '''
    PaymentIntentCreate validates incoming data:
        - amount must be greater than 0
        - currency must be 3 characters
    '''
    amount: int = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)

class PaymentIntentResponse(BaseModel):
    '''
        defines what the API returns
    '''
    id: int
    merchant_id: int
    amount: int
    currency: str
    status: str


