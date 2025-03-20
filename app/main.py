from fastapi import FastAPI
from app.api import auth_router, portfolio as portfolio_router, trading, alerts
from app.core.database import engine
from app.models.user import User
from app.models.portfolio import Portfolio
from app.tasks import celery

app = FastAPI(title="Bitcoin Trading Backend")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
app.include_router(trading, prefix="/trading", tags=["trading"])
app.include_router(alerts, prefix="/alerts", tags=["alerts"])

User.metadata.create_all(bind=engine)
Portfolio.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Bitcoin Trading Backend is running"}

@app.on_event("startup")
def schedule_validation():
    from celery.schedules import crontab
    celery.conf.beat_schedule = {
        "validate-binance-keys": {
            "task": "app.tasks.trading_tasks.validate_user_binance_keys",
            "schedule": crontab(hour=0, minute=0),
            "args": ("testuser@example.com",)
        },
        "check-price-decline": {
            "task": "app.tasks.alert_tasks.check_price_decline",
            "schedule": crontab(minute="*/15"),  # Run every 15 minutes
            "args": ("testuser@example.com", "BTC/USDT", 0.05)
        }
    }