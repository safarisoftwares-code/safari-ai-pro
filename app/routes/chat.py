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

def is_website_question(message: str) -> bool:
    """Check if user is asking about Safari Softwares website."""
    msg_lower = message.lower()
    website_keywords = [
        "website", "url", "website address", "web address", "their website",
        "mother company website", "parent company website", "company website"
    ]
    safari_keywords = ["safari softwares", "mother company", "parent company", "your company"]
    has_website = any(kw in msg_lower for kw in website_keywords)
    has_safari = any(kw in msg_lower for kw in safari_keywords)
    return has_website and has_safari

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
    
    # HARD-CODED RESPONSES for critical questions
    if is_website_question(question):
        return {
            "status": "success",
            "response": "Here are the official Safari Softwares URLs: 🔥🌍\n\n**Safari Softwares Website:** https://safarisoftwares.co.ke/\n\n**Safari Softwares Domain:** https://safarisoftwares.co.ke/\n\n**Safari AI Pro:** https://safari-ai-pro.co.ke\n\nThese are the ONLY correct URLs! ✅✨",
            "session_id": session_id,
            "guest_remaining": None
        }
    
    image_info = None
    if image:
        image_content = await image.read()
        if len(image_content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"Image too large.")
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
                today = date.today().isoformat()
                if user.last_reset != today:
                    user.queries_today = 0
                    user.last_reset = today
                if user.queries_today >= user.daily_limit:
                    raise HTTPException(status_code=429, detail=f"Daily limit of {user.daily_limit} queries reached.")
                user.queries_today += 1
                user.total_queries += 1
                db.commit()

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

@router.post("/sync")
async def sync_chats(token: str = Form(...), chats: str = Form(...), db: Session = Depends(get_db)):
    payload = AuthService.decode_access_token(token)
    if not payload:
        return {"status": "error", "message": "Invalid token"}
    email = payload.get("email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "error", "message": "User not found"}
    try:
        chat_data = json.loads(chats)
        for chat_id, chat_info in chat_data.items():
            existing = db.query(Chat).filter(Chat.session_id == chat_id, Chat.user_id == user.id).first()
            if existing:
                existing.messages = json.dumps(chat_info.get("messages", []))
                existing.title = chat_info.get("name", "Chat")
                existing.updated_at = datetime.utcnow()
            else:
                new_chat = Chat(session_id=chat_id, user_id=user.id, title=chat_info.get("name", "Chat"), messages=json.dumps(chat_info.get("messages", [])))
                db.add(new_chat)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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

@router.post("/external/ask")
async def external_ask(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    api_key = db.query(APIKey).filter(APIKey.key == x_api_key, APIKey.is_active == True).first()
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    try:
        body = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Request body must be JSON")
    question = body.get("question", body.get("prompt", ""))
    if is_website_question(question):
        return {"status": "success", "response": "Safari Softwares: https://safarisoftwares.co.ke/ | Domain: https://safarisoftwares.co.ke/ | Safari AI Pro: https://safari-ai-pro.co.ke"}
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    response = ai_service.think(question, None, None, api_key.email or "external")
    return {"status": "success", "response": response, "model": ai_service.model, "api_key_plan": api_key.plan}
