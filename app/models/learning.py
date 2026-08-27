from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base

class Learning(Base):
    __tablename__ = "learnings"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(50), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "topic": self.topic[:200],
            "content": self.content[:500],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
