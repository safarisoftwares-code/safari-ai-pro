from pydantic import BaseModel
from typing import Optional

class APIKeyCreate(BaseModel):
    plan: str = "free"
    daily_limit: Optional[int] = None

class APIKeyResponse(BaseModel):
    key: str
    plan: str
    daily_limit: int
