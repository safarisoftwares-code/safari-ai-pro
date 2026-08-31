import json
import time
import os
import tempfile
from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date

from app.database import get_db
from app.models import User, Chat, APIKey
from app.services.ai_service import AIService
from app.services.auth_service import AuthService
from app.config import settings
from app.routes.upload import uploaded_documents

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
ai_service = AIService()

GUEST_LIMIT = settings.GUEST_LIMIT
GUEST_WARNING_THRESHOLD = 5
GUEST_RESET_HOURS = 24

guest_queries = {}

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def check_guest_quota(ip: str) -> dict:
    now = time.time()
    if ip not in guest_queries:
        return {"used": 0, "remaining": GUEST_LIMIT, "blocked": False}
    data = guest_queries[ip]
    if now - data["first_query_time"] > GUEST_RESET_HOURS * 3600:
        guest_queries[ip] = {"count": 0, "first_query_time": now}
        return {"used": 0, "remaining": GUEST_LIMIT, "blocked": False}
    used = data["count"]
    remaining = max(0, GUEST_LIMIT - used)
    return {"used": used, "remaining": remaining, "blocked": used >= GUEST_LIMIT}

def increment_guest_quota(ip: str):
    now = time.time()
    if ip not in guest_queries:
        guest_queries[ip] = {"count": 1, "first_query_time": now}
    else:
        data = guest_queries[ip]
        if now - data["first_query_time"] > GUEST_RESET_HOURS * 3600:
            guest_queries[ip] = {"count": 1, "first_query_time": now}
        else:
            data["count"] += 1

def validate_api_key(api_key: str, db: Session):
    key = db.query(APIKey).filter(APIKey.key == api_key, APIKey.is_active == True).first()
    return key

@router.get("/guest-status")
async def guest_status(request: Request):
    ip = get_client_ip(request)
    status = check_guest_quota(ip)
    return {"status": "success", "used": status["used"], "remaining": status["remaining"], "limit": GUEST_LIMIT, "blocked": status["blocked"]}

@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    try:
        content = await audio.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        transcript = ai_service.transcribe_audio(tmp_path)
        os.unlink(tmp_path)
        if transcript:
            return {"status": "success", "transcript": transcript}
        else:
            return {"status": "error", "message": "Could not transcribe audio."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/ask")
async def ask(
    request: Request,
    question: str = Form(default=""),
    session_id: str = Form(default="default"),
    token: Optional[str] = Form(default=None),
    image: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db)
):
    question = question.strip()
    
    image_info = None
    if image:
        image_content = await image.read()
        if len(image_content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"Image too large. Maximum {settings.MAX_UPLOAD_SIZE_MB}MB.")
        image_info = {"filename": image.filename, "size_kb": round(len(image_content) / 1024, 1)}
        question = f"The user uploaded an image. Image analysis is under development."

    if not question and not image_info:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    user = None
    is_logged_in = False
    if token:
        payload = AuthService.decode_access_token(token)
        if payload:
            email = payload.get("email")
            user = db.query(User).filter(User.email == email).first()
            if user:
                is_logged_in = True

    if not is_logged_in:
        ip = get_client_ip(request)
        status = check_guest_quota(ip)
        if status["blocked"]:
            raise HTTPException(status_code=429, detail=f"Free limit of {GUEST_LIMIT} queries reached.")
        increment_guest_quota(ip)

    history = []
    chat = db.query(Chat).filter(Chat.session_id == session_id).first()
    if chat:
        try:
            messages = json.loads(chat.messages)
            for msg in messages[-10:]:
                if msg.startswith("U:"):
                    history.append({"role": "user", "content": msg[2:]})
                elif msg.startswith("S:"):
                    history.append({"role": "assistant", "content": msg[2:]})
        except:
            history = []

    document = uploaded_documents.get(session_id)
    response = ai_service.think(question, history, document, user.email if user else "guest")

    if chat:
        messages = json.loads(chat.messages)
        messages.append(f"U:{question}")
        messages.append(f"S:{response}")
        chat.messages = json.dumps(messages[-100:])
        chat.updated_at = datetime.utcnow()
    else:
        messages = [f"U:{question}", f"S:{response}"]
        chat = Chat(session_id=session_id, user_id=user.id if user else None, title=question[:50], messages=json.dumps(messages))
        db.add(chat)
    db.commit()

    remaining = None
    if not is_logged_in:
        ip = get_client_ip(request)
        status = check_guest_quota(ip)
        remaining = status["remaining"]

    return {"status": "success", "response": response, "session_id": session_id, "guest_remaining": remaining}

@router.get("/history")
async def get_history(session_id: str, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.session_id == session_id).first()
    if not chat:
        return {"status": "success", "messages": []}
    try:
        messages = json.loads(chat.messages)
    except:
        messages = []
    return {"status": "success", "messages": messages}

# ============ EXTERNAL API (for other software) ============

@router.post("/external/ask")
async def external_ask(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """External API endpoint - use X-API-Key header for authentication."""
    
    # Validate API key
    api_key = validate_api_key(x_api_key, db)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    # Get request body
    try:
        body = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Request body must be JSON")
    
    question = body.get("question", body.get("prompt", ""))
    session_id = body.get("session_id", f"ext_{api_key.id}_{int(time.time())}")
    
    if not question:
        raise HTTPException(status_code=400, detail="Question/prompt is required")
    
    if len(question) > 2000:
        raise HTTPException(status_code=400, detail="Question too long (max 2000 characters)")
    
    # Check daily limit for this API key
    today = date.today().isoformat()
    if not hasattr(api_key, 'last_used_date') or api_key.last_used_date != today:
        api_key.last_used_date = today
        api_key.queries_today = 0
    if api_key.queries_today >= api_key.daily_limit:
        raise HTTPException(status_code=429, detail=f"API key daily limit of {api_key.daily_limit} reached")
    
    # Get AI response
    response = ai_service.think(question, None, None, api_key.email or "external")
    
    # Update usage
    api_key.queries_today = (api_key.queries_today or 0) + 1
    api_key.last_used = datetime.utcnow()
    db.commit()
    
    return {
        "status": "success",
        "response": response,
        "model": ai_service.model,
        "api_key_plan": api_key.plan,
        "queries_today": api_key.queries_today,
        "daily_limit": api_key.daily_limit
    }

@router.get("/external/status")
async def external_status(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Check API key status."""
    api_key = validate_api_key(x_api_key, db)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    return {
        "status": "success",
        "plan": api_key.plan,
        "daily_limit": api_key.daily_limit,
        "queries_today": api_key.queries_today or 0,
        "is_active": api_key.is_active,
        "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
        "last_used": api_key.last_used.isoformat() if api_key.last_used else None
    }
