from sqlalchemy import Column, Integer, String
from app.core.database import Base
from cryptography.fernet import Fernet

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    binance_api_key = Column(String, nullable=True)  # Optional for now
    binance_api_secret = Column(String, nullable=True)  # Optional for now