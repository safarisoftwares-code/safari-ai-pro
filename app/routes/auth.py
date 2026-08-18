from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import User
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

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
