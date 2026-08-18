from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Form, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.config import settings
from app.database import init_db, get_db
from app.models import User, Chat
from app.routes import auth, chat, admin, upload
from app.middleware.rate_limit import RateLimitMiddleware

init_db()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional AI Agent by Safari Softwares"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    return FileResponse("templates/dashboard.html")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(pw: str = "", db: Session = Depends(get_db)):
    if pw != settings.ADMIN_PASSWORD:
        return """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Admin Login</title>
<style>
body{font-family:Segoe UI,sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;background:#f5e6d3}
form{background:#fff;padding:40px;border-radius:15px;box-shadow:0 10px 40px rgba(0,0,0,.2);width:100%;max-width:400px}
h2{color:#8b4513;margin-bottom:20px;text-align:center}
input{padding:12px;margin-bottom:20px;width:100%;border:2px solid #d2691e;border-radius:8px;font-size:16px}
button{background:#d2691e;color:#fff;border:0;padding:14px;border-radius:8px;cursor:pointer;font-weight:bold;width:100%}
</style>
</head>
<body>
<form method="get" action="/admin">
<h2>Safari AI Admin</h2>
<input type="password" name="pw" placeholder="Admin password" required>
<button type="submit">Login</button>
</form>
</body></html>"""
    
    users = db.query(User).all()
    user_rows = ""
    for u in users:
        status = "Banned" if u.is_banned else "Active"
        user_rows += f"<tr><td>{u.name}</td><td>{u.email}</td><td>{u.plan}</td><td>{u.queries_today}/{u.daily_limit}</td><td>{u.total_queries}</td><td>{status}</td><td><a href='/admin/ban?email={u.email}&pw={pw}' style='color:red'>Ban</a> | <a href='/admin/unban?email={u.email}&pw={pw}' style='color:green'>Unban</a></td></tr>"
    
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Admin Panel</title>
<style>
body{{font-family:Segoe UI,sans-serif;background:#f5e6d3;padding:20px}}
.c{{max-width:1200px;margin:auto;background:#fff;padding:30px;border-radius:15px}}
h1{{color:#8b4513;margin-bottom:20px}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:12px;border:1px solid #e0c8a8;text-align:left}}
th{{background:#d2691e;color:#fff}}
a{{color:#d2691e;text-decoration:none}}
</style>
</head>
<body>
<div class="c">
<h1>Admin Panel - Safari AI Pro</h1>
<p>Total Users: {len(users)}</p>
<table><tr><th>Name</th><th>Email</th><th>Plan</th><th>Usage</th><th>Total</th><th>Status</th><th>Actions</th></tr>{user_rows}</table>
<a href="/">Exit Admin</a>
</div>
</body></html>"""

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

@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page():
    return """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Pricing</title>
<style>body{font-family:Segoe UI,sans-serif;background:#f5e6d3;display:flex;justify-content:center;align-items:center;min-height:100vh}h1{color:#8b4513}a{color:#d2691e}</style>
</head>
<body><div style="text-align:center"><h1>Pricing</h1><p>Free: 10/day | Pro: 1000/day | Enterprise: 10000/day</p><a href="/">Back</a></div></body></html>"""

@app.get("/terms", response_class=HTMLResponse)
async def terms_page():
    return """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Terms</title>
<style>body{font-family:Segoe UI,sans-serif;background:#f5e6d3;padding:40px;max-width:800px;margin:auto}h1{color:#8b4513}a{color:#d2691e}</style>
</head>
<body><h1>Terms and Conditions</h1><p>By using Safari AI Pro, you agree to these terms.</p><a href="/">Back</a></body></html>"""

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_page():
    return """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Privacy</title>
<style>body{font-family:Segoe UI,sans-serif;background:#f5e6d3;padding:40px;max-width:800px;margin:auto}h1{color:#8b4513}a{color:#d2691e}</style>
</head>
<body><h1>Privacy Policy</h1><p>We do not sell your data.</p><a href="/">Back</a></body></html>"""

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }
