from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from app.schemas.user import UserCreate, UserOut, UserLogin
from app.services.auth_service import create_user, authenticate_user, get_user_by_email , delete_user
from app.core.security import create_access_token, get_current_user
from app.core.database import get_db
from app.core.config import settings
from sqlalchemy.orm import Session
import requests
from cryptography.fernet import Fernet
import redis
from pydantic import BaseModel  # Add this

router = APIRouter()

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Define a Pydantic model for Binance credentials
class BinanceCredentials(BaseModel):
    api_key: str
    api_secret: str

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user)
    return db_user

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout")
def logout(current_user_email: str = Depends(get_current_user)):
    redis_client.setex(current_user_email, 3600, "blacklisted")
    return {"message": "Logged out"}

@router.delete("/user")
def delete_account(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    delete_user(db, db_user)
    return {"message": "Account deleted"}

@router.post("/binance/validate")
def validate_binance_keys(
    credentials: BinanceCredentials,  # Use Pydantic model for JSON body
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ccxt import binance
    exchange = binance({
        'apiKey': credentials.api_key,
        'secret': credentials.api_secret,
        'enableRateLimit': True,
    })
    try:
        exchange.load_markets()
        user = get_user_by_email(db, current_user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        cipher = Fernet(settings.FERNET_KEY.encode())
        user.binance_api_key = cipher.encrypt(credentials.api_key.encode()).decode()
        user.binance_api_secret = cipher.encrypt(credentials.api_secret.encode()).decode()
        db.commit()
        return {"message": "Binance API credentials validated and stored"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Binance credentials: {str(e)}")