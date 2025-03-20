from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    FERNET_KEY: str
    BINANCE_CLIENT_ID: str
    BINANCE_CLIENT_SECRET: str
    BINANCE_REDIRECT_URI: str
    TELEGRAM_BOT_TOKEN: str  # Add your Telegram bot token
    TELEGRAM_CHAT_ID: str  # Add your Telegram chat ID
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str  # Add your email username
    SMTP_PASSWORD: str  # Add your email password
    EMAIL_SENDER: str  # Add your sender email

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()