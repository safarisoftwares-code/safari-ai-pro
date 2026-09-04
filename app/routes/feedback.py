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
    token: str = Form(default=""),
    db: Session = Depends(get_db)
):
    if not name.strip() or not message.strip():
        raise HTTPException(status_code=400, detail="Name and message are required.")
    
    if rating < 1 or rating > 5:
        rating = 5
    
    user_id = None
    if token:
        from app.services.auth_service import AuthService
        from app.models import User
        payload = AuthService.decode_access_token(token)
        if payload:
            user = db.query(User).filter(User.email == payload.get("email")).first()
            if user:
                user_id = user.id
                name = user.name
                email = user.email

    feedback = Feedback(
        name=name.strip(),
        email=email.strip(),
        rating=rating,
        category=category,
        message=message.strip(),
        user_id=user_id
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


@router.post("/reply")
async def reply_feedback(
    feedback_id: int = Form(...),
    reply: str = Form(...),
    pw: str = Form(...),
    db: Session = Depends(get_db)
):
    if not settings.ADMIN_PASSWORD or pw != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid admin password")
    
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    feedback.reply = reply.strip()
    feedback.replied_at = datetime.utcnow()
    feedback.is_read = 1
    db.commit()
    
    # Try to send email
    try:
        import httpx
        import os
        resend_api_key = os.getenv("RESEND_API_KEY", "")
        if resend_api_key and feedback.email:
            response = httpx.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "Safari AI Pro <no-reply@safari-ai-pro.co.ke>",
                    "to": [feedback.email],
                    "subject": "Reply to your feedback - Safari AI Pro",
                    "html": f"""
                    <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;padding:20px">
                        <h2 style="color:#8b4513">Safari AI Pro - Feedback Reply</h2>
                        <p>Hello {feedback.name},</p>
                        <p>Thank you for your feedback!</p>
                        <p><strong>Your feedback:</strong> {feedback.message[:200]}</p>
                        <p><strong>Our reply:</strong></p>
                        <div style="background:#faf5f0;padding:15px;border-radius:10px;border:1px solid #e0c8a8">
                            {reply}
                        </div>
                        <p style="color:#888;font-size:12px">- Safari Softwares Team</p>
                    </div>
                    """
                },
                timeout=15
            )
            email_sent = response.status_code == 200
        else:
            email_sent = False
    except Exception as e:
        print(f"Email error: {e}", flush=True)
        email_sent = False
    
    return {
        "status": "success",
        "message": "Reply saved" + (" and email sent!" if email_sent else ". Email not sent (no API key or error).")
    }


@router.get("/my-feedback")
async def my_feedback(token: str, db: Session = Depends(get_db)):
    from app.services.auth_service import AuthService
    from app.models import User
    payload = AuthService.decode_access_token(token)
    if not payload:
        return {"status": "error", "message": "Invalid token"}
    email = payload.get("email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "error", "message": "User not found"}
    
    feedbacks = db.query(Feedback).filter(Feedback.user_id == user.id).order_by(Feedback.created_at.desc()).all()
    return {"status": "success", "feedbacks": [f.to_dict() for f in feedbacks]}
