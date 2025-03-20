from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_email
from app.core.security import get_current_user
from app.core.config import settings
from app.ml.lstm_model import predict_next_price
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
    stop_loss: float = None,  # Optional stop-loss price
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.binance_api_key or not user.binance_api_secret:
        raise HTTPException(status_code=400, detail="Binance API credentials not provided")

    api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
    api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()

    exchange = binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })

    # Predict next price using LSTM
    try:
        current_price, predicted_price = predict_next_price(symbol)
        print(f"DEBUG: Current price: {current_price}, Predicted price: {predicted_price}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price prediction failed: {str(e)}")

    # Decide whether to trade based on prediction
    if side == "buy" and predicted_price > current_price:
        print("DEBUG: Predicted price increase - proceeding with buy")
    elif side == "sell" and predicted_price < current_price:
        print("DEBUG: Predicted price decrease - proceeding with sell")
    else:
        print("DEBUG: No trade - prediction does not favor the action")
        return {"message": "No trade executed - prediction does not favor the action"}

    try:
        # Execute market order
        order = exchange.create_market_order(symbol, side, amount)
        
        # If stop-loss is provided, create a stop-loss order
        if stop_loss:
            stop_side = "sell" if side == "buy" else "buy"
            exchange.create_order(symbol, "stop_loss_limit", stop_side, amount, stop_loss, {"stopPrice": stop_loss})
            print(f"DEBUG: Stop-loss order placed at {stop_loss}")

        return {"message": f"Trade executed: {json.dumps(order)}"}
    except Exception as e:
        if "invalid api key" in str(e).lower() or "permission" in str(e).lower():
            refresh_binance_token(user, db)
            api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
            api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()
            exchange = binance({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
            })
            order = exchange.create_market_order(symbol, side, amount)
            if stop_loss:
                stop_side = "sell" if side == "buy" else "buy"
                exchange.create_order(symbol, "stop_loss_limit", stop_side, amount, stop_loss, {"stopPrice": stop_loss})
            return {"message": f"Trade executed after refresh: {json.dumps(order)}"}
        raise HTTPException(status_code=500, detail=f"Trade failed: {str(e)}")