import json
import time
import os
import tempfile
from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, AsyncGenerator
from datetime import datetime, date

from app.database import get_db
from app.models import User, Chat
from app.services.ai_service import AIService
from app.services.auth_service import AuthService
from app.config import settings

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
ai_service = AIService()
uploaded_documents = {}

GUEST_LIMIT = 8
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

@router.get("/guest-status")
async def guest_status(request: Request):
    ip = get_client_ip(request)
    status = check_guest_quota(ip)
    return {
        "status": "success",
        "used": status["used"],
        "remaining": status["remaining"],
        "limit": GUEST_LIMIT,
        "blocked": status["blocked"]
    }

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...)
):
    try:
        content = await audio.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        transcript = ai_service.transcribe_audio(tmp_path)
        
        os.unlink(tmp_path)
        
        if transcript:
            return {"status": "success", "transcript": transcript}
        else:
            return {"status": "error", "message": "Could not transcribe audio."}
    
    except Exception as e:
        print(f"Transcription endpoint error: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/save-chat")
async def save_chat(
    session_id: str = Form(...),
    title: str = Form(default="New Chat"),
    messages: str = Form(default="[]"),
    token: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    user = None
    if token:
        payload = AuthService.decode_access_token(token)
        if payload:
            email = payload.get("email")
            user = db.query(User).filter(User.email == email).first()
    
    chat = db.query(Chat).filter(Chat.session_id == session_id).first()
    
    if chat:
        chat.title = title
        chat.messages = messages
        chat.updated_at = datetime.utcnow()
    else:
        chat = Chat(
            session_id=session_id,
            user_id=user.id if user else None,
            title=title,
            messages=messages
        )
        db.add(chat)
    
    db.commit()
    return {"status": "success", "message": "Chat saved."}

@router.get("/load-chats")
async def load_chats(
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user = None
    if token:
        payload = AuthService.decode_access_token(token)
        if payload:
            email = payload.get("email")
            user = db.query(User).filter(User.email == email).first()
    
    if user:
        chats = db.query(Chat).filter(Chat.user_id == user.id).order_by(Chat.updated_at.desc()).all()
    else:
        chats = []
    
    chat_list = []
    for c in chats:
        chat_list.append({
            "session_id": c.session_id,
            "title": c.title,
            "messages": c.messages,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        })
    
    return {"status": "success", "chats": chat_list}

@router.post("/delete-chat")
async def delete_chat(
    session_id: str = Form(...),
    db: Session = Depends(get_db)
):
    chat = db.query(Chat).filter(Chat.session_id == session_id).first()
    if chat:
        db.delete(chat)
        db.commit()
        return {"status": "success", "message": "Chat deleted."}
    return {"status": "not_found", "message": "Chat not found."}

@router.post("/ask-stream")
async def ask_stream(
    request: Request,
    question: str = Form(...),
    session_id: str = Form(default="default"),
    token: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    question = question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(question) > 2000:
        raise HTTPException(status_code=400, detail="Question too long (max 2000 characters)")

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
                    raise HTTPException(status_code=429, detail=f"Daily limit reached.")
                user.queries_today += 1
                user.total_queries += 1
                db.commit()

    if not is_logged_in:
        ip = get_client_ip(request)
        status = check_guest_quota(ip)
        if status["blocked"]:
            raise HTTPException(status_code=429, detail="Free limit reached. Please login.")
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
    user_identifier = user.email if user else "guest"

    async def generate() -> AsyncGenerator[str, None]:
        full_response = ""
        try:
            for chunk in ai_service.think_stream(question, history, document, user_identifier):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            if chat:
                messages = json.loads(chat.messages)
                messages.append(f"U:{question}")
                messages.append(f"S:{full_response}")
                chat.messages = json.dumps(messages[-100:])
                chat.updated_at = datetime.utcnow()
            else:
                messages = [f"U:{question}", f"S:{full_response}"]
                chat = Chat(session_id=session_id, user_id=user.id if user else None, title=question[:50], messages=json.dumps(messages))
                db.add(chat)
            db.commit()
            
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("/ask")
async def ask(
    request: Request,
    question: str = Form(...),
    session_id: str = Form(default="default"),
    token: Optional[str] = Form(default=None),
    db: Session = Depends(get_db)
):
    question = question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(question) > 2000:
        raise HTTPException(status_code=400, detail="Question too long (max 2000 characters)")

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
            raise HTTPException(status_code=429, detail="Free limit reached. Please login to continue.")
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
    user_identifier = user.email if user else "guest"
    
    response = ai_service.think(question, history, document, user_identifier)

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

    return {
        "status": "success",
        "response": response,
        "session_id": session_id,
        "guest_remaining": remaining
    }

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
