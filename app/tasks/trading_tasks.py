from app.tasks import celery  # Import from parent module
from app.core.database import SessionLocal
from app.services.auth_service import get_user_by_email
from app.core.config import settings
from cryptography.fernet import Fernet
from ccxt import binance

@celery.task
def validate_user_binance_keys(user_email: str):
    db = SessionLocal()
    try:
        user = get_user_by_email(db, user_email)
        if not user or not user.binance_api_key or not user.binance_api_secret:
            return {"status": "failed", "message": "No credentials"}
        
        cipher = Fernet(settings.FERNET_KEY.encode())
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