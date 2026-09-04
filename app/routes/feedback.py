from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import Feedback
from app.config import settings

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

@router.post("/submit")
async def submit_feedback(
    name: str = Form(...),
    email: str = Form(...),
    rating: int = Form(default=5),
    category: str = Form(default="general"),
    message: str = Form(...),
    db: Session = Depends(get_db)
):
    if not name.strip() or not message.strip():
        raise HTTPException(status_code=400, detail="Name and message are required.")
    
    if rating < 1 or rating > 5:
        rating = 5
    
    feedback = Feedback(
        name=name.strip(),
        email=email.strip(),
        rating=rating,
        category=category,
        message=message.strip()
    )
    db.add(feedback)
    db.commit()
    
    return {"status": "success", "message": "Feedback submitted! Thank you."}

@router.get("/list")
async def list_feedback(pw: str = "", db: Session = Depends(get_db)):
    if not settings.ADMIN_PASSWORD or pw != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password")
    
    feedbacks = db.query(Feedback).order_by(Feedback.created_at.desc()).all()
    return {"status": "success", "feedbacks": [f.to_dict() for f in feedbacks]}
