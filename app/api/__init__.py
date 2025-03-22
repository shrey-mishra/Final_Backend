from .auth import router as auth_router
from .portfolio import router as portfolio
from .trading import router as trading
from .live_feeds import router as live_feeds  # Add this
from fastapi import APIRouter

alerts = APIRouter()

__all__ = ["auth_router", "portfolio", "trading", "live_feeds", "alerts"]