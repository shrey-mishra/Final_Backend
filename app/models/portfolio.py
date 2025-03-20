from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    btc_amount = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())