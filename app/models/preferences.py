from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from app.core.database import Base

class Preferences(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    auto_trade = Column(Boolean, default=False)  # Enable/disable auto-trading
    threshold_limit = Column(Float, default=0.02)  # Minimum price change to trigger trade (e.g., 2%)