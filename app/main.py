from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Form, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import hashlib
import time
import os

from app.config import settings
from app.database import init_db, get_db
from app.models import User, Chat, APIKey
from app.routes import auth, chat, admin, upload
from app.middleware.rate_limit import RateLimitMiddleware

init_db()

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RateLimitMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(upload.router)

@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse("templates/index.html")

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return FileResponse("templates/login.html")

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page():
    return FileResponse("templates/reset-password.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    return FileResponse("templates/dashboard.html")

@app.get("/profile", response_class=HTMLResponse)
async def profile_page():
    return FileResponse("templates/profile.html")

@app.get("/terms", response_class=HTMLResponse)
async def terms_page():
    return FileResponse("templates/terms.html")

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page():
    return FileResponse("templates/privacy.html")

@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page():
    return FileResponse("templates/pricing.html")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(pw: str = "", db: Session = Depends(get_db)):
    if pw != settings.ADMIN_PASSWORD:
        return """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Admin Login</title>
<style>
body{font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;background:#f5e6d3}
form{background:#fff;padding:40px;border-radius:15px;box-shadow:0 10px 40px rgba(0,0,0,.2);width:100%;max-width:400px}
h2{color:#8b4513;margin-bottom:20px;text-align:center}
.pw-wrapper{position:relative;margin-bottom:15px}
.pw-wrapper input{padding:12px 45px 12px 12px;width:100%;border:2px solid #d2691e;border-radius:8px;font-size:16px;outline:0;box-sizing:border-box}
.toggle-pw{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;font-size:18px;padding:5px;width:30px;height:30px}
button[type=submit]{background:#d2691e;color:#fff;border:0;padding:14px;border-radius:8px;cursor:pointer;font-weight:bold;width:100%;font-size:16px}
.back{display:block;text-align:center;margin-top:15px;color:#d2691e;text-decoration:none;font-size:13px}
</style>
</head>
<body>
<form method="get" action="/admin">
<h2>&#x1F981; Admin Login</h2>
<div class="pw-wrapper">
<input type="password" id="pwInput" name="pw" placeholder="Admin password" required>
<button type="button" class="toggle-pw" onclick="togglePw()">&#128065;</button>
</div>
<button type="submit">Login</button>
<a href="/" class="back">Back to Chat</a>
</form>
<script>function togglePw(){var i=document.getElementById('pwInput');if(i.type==='password'){i.type='text';}else{i.type='password';}}</script>
</body></html>"""
    
    users = db.query(User).all()
    user_rows = ""
    for u in users:
        status = "Banned" if u.is_banned else "Active"
        action = f'<a href="/admin/ban?email={u.email}&pw={pw}">Ban</a>' if not u.is_banned else f'<a href="/admin/unban?email={u.email}&pw={pw}">Unban</a>'
        user_rows += f"<tr><td>{u.name}</td><td>{u.email}</td><td>{u.plan}</td><td>{u.queries_today}/{u.daily_limit}</td><td>{u.total_queries}</td><td>{status}</td><td>{action}</td></tr>"
    
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Admin Panel</title>
<style>
body{{font-family:Segoe UI,sans-serif;background:#f5e6d3;padding:20px}}
.c{{max-width:1200px;margin:auto;background:#fff;padding:30px;border-radius:15px}}
h1{{color:#8b4513}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:10px;border:1px solid #e0c8a8;text-align:left}}
th{{background:#d2691e;color:#fff}}
a{{color:#d2691e;text-decoration:none}}
</style>
</head>
<body><div class="c">
<h1>Admin Panel - Safari AI Pro</h1>
<p>Users: {len(users)}</p>
<table><tr><th>Name</th><th>Email</th><th>Plan</th><th>Usage</th><th>Total</th><th>Status</th><th>Actions</th></tr>{user_rows}</table>
<a href="/">Exit</a>
</div></body></html>"""

@app.get("/admin/ban")
async def admin_ban(email: str = "", pw: str = "", db: Session = Depends(get_db)):
    if pw != settings.ADMIN_PASSWORD:
        return RedirectResponse("/admin")
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_banned = True
        db.commit()
    return RedirectResponse(f"/admin?pw={pw}")

@app.get("/admin/unban")
async def admin_unban(email: str = "", pw: str = "", db: Session = Depends(get_db)):
    if pw != settings.ADMIN_PASSWORD:
        return RedirectResponse("/admin")
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_banned = False
        db.commit()
    return RedirectResponse(f"/admin?pw={pw}")

@app.get("/health")
async def health():
    return {"status":"ok","service":settings.APP_NAME,"version":settings.APP_VERSION,"timestamp":datetime.now().isoformat()}
