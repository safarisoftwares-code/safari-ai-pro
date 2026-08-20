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

def render_admin_page(pw: str, db: Session) -> str:
    users = db.query(User).all()
    api_keys = db.query(APIKey).all()
    
    total_users = len(users)
    free_users = sum(1 for u in users if u.plan == 'free')
    pro_users = sum(1 for u in users if u.plan == 'pro')
    enterprise_users = sum(1 for u in users if u.plan == 'enterprise')
    banned_users = sum(1 for u in users if u.is_banned)
    api_key_count = len(api_keys)
    
    login_rows = ""
    for u in users:
        plan_class = u.plan
        status_class = "status-banned" if u.is_banned else "status-active"
        status_text = "Banned" if u.is_banned else "Active"
        action = f'<a href="/admin/ban?email={u.email}&pw={pw}" class="btn-ban">Ban</a>' if not u.is_banned else f'<a href="/admin/unban?email={u.email}&pw={pw}" class="btn-unban">Unban</a>'
        login_rows += f"""<tr>
            <td>{u.name}</td>
            <td>{u.email}</td>
            <td><span class="plan-badge plan-{plan_class}">{u.plan.upper()}</span></td>
            <td>{u.queries_today}/{u.daily_limit}</td>
            <td>{u.total_queries}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{action}</td>
        </tr>"""
    
    api_rows = ""
    for k in api_keys:
        email = k.user.email if k.user else "N/A"
        plan_class = k.plan
        api_rows += f"""<tr>
            <td>{email}</td>
            <td><span class="plan-badge plan-{plan_class}">{k.plan.upper()}</span></td>
            <td>0/{k.daily_limit}</td>
            <td>0</td>
            <td><code>{k.key[:16]}...</code></td>
            <td>
                <form method="post" action="/admin/revoke-key" style="display:inline" onsubmit="return confirm('Revoke this API key?')">
                    <input type="hidden" name="key" value="{k.key}">
                    <input type="hidden" name="pw" value="{pw}">
                    <button type="submit" class="btn-revoke">Revoke</button>
                </form>
            </td>
        </tr>"""
    
    with open("templates/admin.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    html = html.replace("{{TOTAL_USERS}}", str(total_users))
    html = html.replace("{{FREE_USERS}}", str(free_users))
    html = html.replace("{{PRO_USERS}}", str(pro_users))
    html = html.replace("{{ENTERPRISE_USERS}}", str(enterprise_users))
    html = html.replace("{{BANNED_USERS}}", str(banned_users))
    html = html.replace("{{API_KEY_COUNT}}", str(api_key_count))
    html = html.replace("{{LOGIN_ACCOUNT_ROWS}}", login_rows)
    html = html.replace("{{API_USER_ROWS}}", api_rows)
    html = html.replace("{{PW}}", pw)
    
    return html

@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse("templates/index.html")

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return FileResponse("templates/login.html")

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
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Admin Login</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;background:#f5e6d3}
form{background:#fff;padding:40px;border-radius:15px;box-shadow:0 10px 40px rgba(0,0,0,.2);width:100%;max-width:400px}
h2{color:#8b4513;margin-bottom:20px;text-align:center}
.pw-wrapper{position:relative;margin-bottom:15px}
.pw-wrapper input{padding:12px 45px 12px 12px;width:100%;border:2px solid #d2691e;border-radius:8px;font-size:16px;outline:0;box-sizing:border-box}
.pw-wrapper input:focus{border-color:#8b4513}
.toggle-pw{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;font-size:18px;padding:5px;width:30px;height:30px;display:flex;align-items:center;justify-content:center}
.toggle-pw:hover{background:#f0e0d0;border-radius:50%}
button[type=submit]{background:#d2691e;color:#fff;border:0;padding:14px;border-radius:8px;cursor:pointer;font-weight:bold;width:100%;font-size:16px}
button[type=submit]:hover{background:#8b4513}
.back{display:block;text-align:center;margin-top:15px;color:#d2691e;text-decoration:none;font-size:13px}
</style>
</head>
<body>
<form method="get" action="/admin">
<h2>&#x1F981; Admin Login</h2>
<div class="pw-wrapper">
<input type="password" id="pwInput" name="pw" placeholder="Enter admin password" required>
<button type="button" class="toggle-pw" onclick="togglePw()">&#128065;</button>
</div>
<button type="submit">Login to Admin</button>
<a href="/" class="back">Back to Chat</a>
</form>
<script>
function togglePw(){var i=document.getElementById('pwInput');if(i.type==='password'){i.type='text';}else{i.type='password';}}
</script>
</body></html>"""
    
    return render_admin_page(pw, db)

@app.post("/admin/logout")
async def admin_logout():
    return RedirectResponse("/admin", status_code=303)

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
