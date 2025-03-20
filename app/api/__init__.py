from .auth import router as auth_router
from .portfolio import router as portfolio
from .trading import router as trading  # Ensure this line exists
from fastapi import APIRouter

alerts = APIRouter()

__all__ = ["auth_router", "portfolio", "trading", "alerts"]