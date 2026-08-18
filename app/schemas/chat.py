from pydantic import BaseModel, Field

class MessageRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default", max_length=50)

class ChatResponse(BaseModel):
    response: str
    session_id: str

class ChatCreate(BaseModel):
    title: str = Field(default="New Chat", max_length=200)
