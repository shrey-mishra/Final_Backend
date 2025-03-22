from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.preferences import Preferences
from app.services.auth_service import get_user_by_email
from app.core.security import get_current_user
from app.core.config import settings
from app.ml.lstm_model import predict_next_price
from app.tasks.trading_tasks import execute_order_task  
from ccxt import binance
import json
from cryptography.fernet import Fernet
import requests

router = APIRouter()

cipher = Fernet(settings.FERNET_KEY.encode())

def refresh_binance_token(user: User, db: Session):
    token_url = "https://accounts.binance.com/en/oauth/token"
    data = {
        "client_id": settings.BINANCE_CLIENT_ID,
        "client_secret": settings.BINANCE_CLIENT_SECRET,
        "refresh_token": cipher.decrypt(user.binance_api_secret.encode()).decode(),
        "grant_type": "refresh_token"
    }
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        token_data = response.json()
        user.binance_api_key = cipher.encrypt(token_data["access_token"].encode()).decode()
        user.binance_api_secret = cipher.encrypt(token_data["refresh_token"].encode()).decode()
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="Failed to refresh Binance token")

@router.post("/execute")
def execute_trade(
    symbol: str = "BTC/USDT",
    side: str = "buy",
    amount: float = 0.01,
    stop_loss: float = None,
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.binance_api_key or not user.binance_api_secret:
        raise HTTPException(status_code=400, detail="Binance API credentials not provided")

    # Check user preferences
    preferences = db.query(Preferences).filter(Preferences.user_id == user.id).first()
    if not preferences:
        raise HTTPException(status_code=404, detail="User preferences not found")
    
    if not preferences.auto_trade:
        raise HTTPException(status_code=400, detail="Auto-trading is disabled for this user")

    try:
        current_price, predicted_price = predict_next_price(symbol)
        print(f"DEBUG: Current price: {current_price}, Predicted price: {predicted_price}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price prediction failed: {str(e)}")

    # Check if the price change meets the threshold
    price_change = (predicted_price - current_price) / current_price
    if abs(price_change) < preferences.threshold_limit:
        print(f"DEBUG: Price change {price_change*100:.2f}% is below threshold {preferences.threshold_limit*100:.2f}%")
        return {"message": "No trade executed - price change below threshold"}

    if side == "buy" and predicted_price > current_price:
        print("DEBUG: Predicted price increase - proceeding with buy")
    elif side == "sell" and predicted_price < current_price:
        print("DEBUG: Predicted price decrease - proceeding with sell")
    else:
        print("DEBUG: No trade - prediction does not favor the action")
        return {"message": "No trade executed - prediction does not favor the action"}

    # Offload the trade execution to Celery for segregated processing
    task = execute_order_task.delay(user.id, symbol, side, amount, stop_loss)
    return {"message": f"Trade execution task queued: {task.id}"}