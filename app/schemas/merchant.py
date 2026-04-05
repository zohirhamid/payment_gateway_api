from pydantic import BaseModel
from datetime import datetime

class MerchantResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class MerchantCreateResponse(BaseModel):
    id: int
    name: str
    api_key: str
    created_at: datetime

    class Config:
        from_attributes = True
