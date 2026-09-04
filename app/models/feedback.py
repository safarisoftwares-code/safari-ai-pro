from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base

class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False)
    rating = Column(Integer, default=5)
    category = Column(String(50), default="general")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, nullable=True)
    is_read = Column(Integer, default=0)
    reply = Column(Text, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "rating": self.rating,
            "category": self.category,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_read": self.is_read,
            "reply": self.reply,
            "replied_at": self.replied_at.isoformat() if self.replied_at else None
        }
