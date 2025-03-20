from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    binance_api_key: str = None  # Optional
    binance_api_secret: str = None  # Optional

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: int
    binance_api_key: str | None = None  # Allow None
    binance_api_secret: str | None = None  # Allow None

    class Config:
        from_attributes = True