from pydantic import BaseModel, Field
from datetime import datetime

class PortfolioCreate(BaseModel):
    btc_amount: float
    purchase_price: float

class PortfolioOut(BaseModel):
    id: int
    user_id: int
    btc_amount: float
    purchase_price: float
    created_at: datetime = Field(default=None)  # Accept datetime object

    class Config:
        from_attributes = True





