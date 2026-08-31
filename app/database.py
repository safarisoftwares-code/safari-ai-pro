from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

from app.config import settings

if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    from app.models import User, Chat, APIKey, RevokedToken, Learning
    Base.metadata.create_all(bind=engine)
    
    # Add missing columns for PostgreSQL (free tier no shell)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS email VARCHAR(120)"))
            conn.execute(text("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS queries_today INTEGER DEFAULT 0"))
            conn.execute(text("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS last_used_date VARCHAR(10)"))
            conn.commit()
            print("Database columns verified", flush=True)
    except Exception as e:
        print(f"Column check: {e}", flush=True)
    
    db = SessionLocal()
    users = db.query(User).all()
    for u in users:
        correct_limit = {
            "free": settings.DAILY_FREE_LIMIT,
            "pro": settings.DAILY_PRO_LIMIT,
            "enterprise": settings.DAILY_ENTERPRISE_LIMIT
        }.get(u.plan, settings.DAILY_FREE_LIMIT)
        if u.daily_limit != correct_limit:
            u.daily_limit = correct_limit
            print(f"Updated {u.email} ({u.plan}) to {correct_limit}", flush=True)
    db.commit()
    db.close()
