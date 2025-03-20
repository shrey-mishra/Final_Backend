from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.schemas.user import UserCreate
from passlib.context import CryptContext
from fastapi import HTTPException
from cryptography.fernet import Fernet
import base64

# Generate a Fernet key (store securely in production, e.g., .env)
key = Fernet.generate_key()
cipher = Fernet(key)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    # Encrypt Binance credentials if provided
    encrypted_api_key = cipher.encrypt(user.binance_api_key.encode()) if user.binance_api_key else None
    encrypted_api_secret = cipher.encrypt(user.binance_api_secret.encode()) if user.binance_api_secret else None
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        binance_api_key=encrypted_api_key.decode() if encrypted_api_key else None,
        binance_api_secret=encrypted_api_secret.decode() if encrypted_api_secret else None
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=422, detail="Email already registered")

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return None
    return user

def delete_user(db: Session, user: User):
    db.delete(user)
    db.commit()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()





