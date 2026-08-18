from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    plan = Column(String(20), default="free")
    daily_limit = Column(Integer, default=10)
    queries_today = Column(Integer, default=0)
    total_queries = Column(Integer, default=0)
    last_reset = Column(String(10), default=date.today().isoformat())
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    ban_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "plan": self.plan,
            "daily_limit": self.daily_limit,
            "queries_today": self.queries_today,
            "total_queries": self.total_queries,
            "is_active": self.is_active,
            "is_banned": self.is_banned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
