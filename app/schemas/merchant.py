from pydantic import BaseModel

class MerchantResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MerchantCreateResponse(BaseModel):
    id: int
    name: str
    api_key: str

    class Config:
        from_attributes = True