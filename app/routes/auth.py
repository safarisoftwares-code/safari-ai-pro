from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import secrets

from app.database import get_db
from app.models import User, Chat
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

reset_tokens = {}

@router.post("/signup")
async def signup(name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if "@" not in email or len(password) < 4:
        raise HTTPException(status_code=400, detail="Invalid email or password too short.")

    existing = db.query(User).filter(User.email == email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account already exists.")

    user = User(
        name=name.strip(),
        email=email.lower(),
        password_hash=AuthService.hash_password(password),
        plan="free",
        daily_limit=10,
        last_reset=datetime.now().date().isoformat()
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = AuthService.create_access_token({"email": user.email, "name": user.name})

    return {"status": "success", "access_token": token, "token_type": "bearer", "user": user.to_dict()}

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.lower()).first()

    if not user:
        raise HTTPException(status_code=401, detail="Account not found.")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account suspended. Contact Safari Softwares.")
    if not AuthService.verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password.")

    user.last_login = datetime.utcnow()
    db.commit()

    token = AuthService.create_access_token({"email": user.email, "name": user.name})

    return {"status": "success", "access_token": token, "token_type": "bearer", "user": user.to_dict()}

@router.post("/forgot-password")
async def forgot_password(email: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.lower()).first()
    
    if not user:
        return {"status": "error", "message": "If this email exists, a reset link has been sent."}
    
    if user.is_banned:
        return {"status": "error", "message": "Account suspended. Contact Safari Softwares."}
    
    reset_token = secrets.token_urlsafe(32)
    reset_tokens[reset_token] = {
        "email": email.lower(),
        "expires": datetime.utcnow().timestamp() + 3600
    }
    
    # In production, send this via email
    # For now, return it directly (development only)
    return {
        "status": "success",
        "message": "Password reset token generated.",
        "reset_token": reset_token,
        "note": "In production, this token would be sent via email."
    }

@router.post("/reset-password")
async def reset_password(
    reset_token: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if len(new_password) < 4:
        return {"status": "error", "message": "Password must be at least 4 characters."}
    
    token_data = reset_tokens.get(reset_token)
    if not token_data:
        return {"status": "error", "message": "Invalid or expired reset token."}
    
    if datetime.utcnow().timestamp() > token_data["expires"]:
        del reset_tokens[reset_token]
        return {"status": "error", "message": "Reset token has expired."}
    
    email = token_data["email"]
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return {"status": "error", "message": "User not found."}
    
    user.password_hash = AuthService.hash_password(new_password)
    db.commit()
    
    del reset_tokens[reset_token]
    
    return {"status": "success", "message": "Password reset successfully. Please login with your new password."}

@router.get("/me")
async def me(token: str, db: Session = Depends(get_db)):
    payload = AuthService.decode_access_token(token)
    if not payload:
        return {"status": "error", "message": "Invalid token"}
    
    email = payload.get("email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "error", "message": "User not found"}
    
    return {"status": "success", "user": user.to_dict()}

@router.post("/update-profile")
async def update_profile(
    token: str = Form(...),
    name: str = Form(default=""),
    db: Session = Depends(get_db)
):
    payload = AuthService.decode_access_token(token)
    if not payload:
        return {"status": "error", "message": "Invalid token"}
    
    email = payload.get("email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "error", "message": "User not found"}
    
    if name and name.strip():
        user.name = name.strip()
        db.commit()
    
    return {"status": "success", "message": "Profile updated.", "user": user.to_dict()}

@router.post("/change-password")
async def change_password(
    token: str = Form(...),
    current_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    payload = AuthService.decode_access_token(token)
    if not payload:
        return {"status": "error", "message": "Invalid token"}
    
    email = payload.get("email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "error", "message": "User not found"}
    
    if not AuthService.verify_password(current_password, user.password_hash):
        return {"status": "error", "message": "Current password is incorrect."}
    
    if len(new_password) < 4:
        return {"status": "error", "message": "New password must be at least 4 characters."}
    
    user.password_hash = AuthService.hash_password(new_password)
    db.commit()
    
    return {"status": "success", "message": "Password changed successfully."}

@router.post("/delete")
async def delete_account(token: str = Form(...), db: Session = Depends(get_db)):
    payload = AuthService.decode_access_token(token)
    if not payload:
        return {"status": "error", "message": "Invalid token"}
    
    email = payload.get("email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "error", "message": "User not found"}
    
    db.query(Chat).filter(Chat.user_id == user.id).delete()
    db.delete(user)
    db.commit()
    
    return {"status": "success", "message": "Account deleted successfully."}
