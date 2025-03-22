from app.tasks import celery
from app.core.database import SessionLocal
from app.services.auth_service import get_user_by_email
from app.core.config import settings
from cryptography.fernet import Fernet
from ccxt import binance
from app.models.user import User
cipher = Fernet(settings.FERNET_KEY.encode())

@celery.task
def validate_user_binance_keys(user_email: str):
    db = SessionLocal()
    try:
        user = get_user_by_email(db, user_email)
        if not user or not user.binance_api_key or not user.binance_api_secret:
            return {"status": "failed", "message": "No credentials"}
        
        api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
        api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()

        exchange = binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        exchange.load_markets()
        return {"status": "success", "message": "Keys valid"}
    except Exception as e:
        return {"status": "failed", "message": str(e)}
    finally:
        db.close()

@celery.task
def execute_order_task(user_id: int, symbol: str, side: str, amount: float, stop_loss: float = None):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "failed", "message": "User not found"}
        if not user.binance_api_key or not user.binance_api_secret:
            return {"status": "failed", "message": "Binance API credentials not provided"}

        api_key = cipher.decrypt(user.binance_api_key.encode()).decode()
        api_secret = cipher.decrypt(user.binance_api_secret.encode()).decode()

        exchange = binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'urls': {
                'api': 'https://testnet.binance.vision/api',  # Use Testnet
            },
        })

        order = exchange.create_market_order(symbol, side, amount)
        if stop_loss:
            stop_side = "sell" if side == "buy" else "buy"
            exchange.create_order(symbol, "stop_loss_limit", stop_side, amount, stop_loss, {"stopPrice": stop_loss})
        return {"status": "success", "message": f"Trade executed: {json.dumps(order)}"}
    except Exception as e:
        return {"status": "failed", "message": str(e)}
    finally:
        db.close()