from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.config import settings

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

def verify_admin(password: str) -> bool:
    return password == settings.ADMIN_PASSWORD

@router.get("/users")
async def list_users(pw: str, db: Session = Depends(get_db)):
    if not verify_admin(pw):
        raise HTTPException(status_code=403, detail="Invalid admin password")
    users = db.query(User).all()
    return {"status": "success", "users": [u.to_dict() for u in users]}

@router.post("/ban")
async def ban_user(email: str = Form(...), reason: str = Form(default=""), pw: str = Form(...), db: Session = Depends(get_db)):
    if not verify_admin(pw):
        raise HTTPException(status_code=403, detail="Invalid admin password")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = True
    user.ban_reason = reason
    db.commit()
    return {"status": "success", "message": f"User {email} banned."}

@router.post("/unban")
async def unban_user(email: str = Form(...), pw: str = Form(...), db: Session = Depends(get_db)):
    if not verify_admin(pw):
        raise HTTPException(status_code=403, detail="Invalid admin password")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = False
    user.ban_reason = None
    db.commit()
    return {"status": "success", "message": f"User {email} unbanned."}

@router.post("/set-plan")
async def set_plan(email: str = Form(...), plan: str = Form(...), pw: str = Form(...), db: Session = Depends(get_db)):
    if not verify_admin(pw):
        raise HTTPException(status_code=403, detail="Invalid admin password")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    limits = {"free": settings.DAILY_FREE_LIMIT, "pro": settings.DAILY_PRO_LIMIT, "enterprise": settings.DAILY_ENTERPRISE_LIMIT}
    user.plan = plan
    user.daily_limit = limits.get(plan, settings.DAILY_FREE_LIMIT)
    db.commit()
    return {"status": "success", "message": f"User {email} plan set to {plan}."}
