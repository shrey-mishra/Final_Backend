from app.tasks import celery
from app.core.database import SessionLocal
from app.services.auth_service import get_user_by_email
from app.core.config import settings
from ccxt import binance
import telegram
import smtplib
from email.mime.text import MIMEText

@celery.task
def check_price_decline(user_email: str, symbol: str = "BTC/USDT", threshold: float = 0.05):
    db = SessionLocal()
    try:
        user = get_user_by_email(db, user_email)
        if not user:
            return {"status": "failed", "message": "User not found"}

        # Fetch current price
        exchange = binance()
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker["last"]

        # Fetch user's portfolio
        from app.models.portfolio import Portfolio
        portfolios = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        if not portfolios:
            return {"status": "failed", "message": "No portfolio data"}

        # Check for price decline
        for portfolio in portfolios:
            purchase_price = portfolio.purchase_price
            decline = (purchase_price - current_price) / purchase_price
            if decline >= threshold:
                # Send Telegram alert
                bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)
                bot.send_message(chat_id=settings.TELEGRAM_CHAT_ID, text=f"Price decline alert: {symbol} dropped {decline*100:.2f}% below your purchase price of {purchase_price}. Current price: {current_price}")

                # Send email alert
                msg = MIMEText(f"Price decline alert: {symbol} dropped {decline*100:.2f}% below your purchase price of {purchase_price}. Current price: {current_price}")
                msg["Subject"] = f"Price Decline Alert for {symbol}"
                msg["From"] = settings.EMAIL_SENDER
                msg["To"] = user.email
                with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                    server.starttls()
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.send_message(msg)

                return {"status": "success", "message": f"Alert sent for {symbol} - decline: {decline*100:.2f}%"}
        return {"status": "success", "message": "No significant decline detected"}
    except Exception as e:
        return {"status": "failed", "message": str(e)}
    finally:
        db.close()