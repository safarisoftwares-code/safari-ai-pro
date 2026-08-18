import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = "Safari AI Pro"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "safarisoftwares@gmail.com")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./safari_pro.db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "safari-ai-pro-secret-key-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRY_MINUTES: int = int(os.getenv("JWT_EXPIRY_MINUTES", "10080"))
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
    DAILY_FREE_LIMIT: int = int(os.getenv("DAILY_FREE_LIMIT", "10"))
    DAILY_PRO_LIMIT: int = int(os.getenv("DAILY_PRO_LIMIT", "1000"))
    DAILY_ENTERPRISE_LIMIT: int = int(os.getenv("DAILY_ENTERPRISE_LIMIT", "10000"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "2"))

settings = Settings()
