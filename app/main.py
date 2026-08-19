from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Form, Depends
from sqlalchemy.orm import Session
from datetime import datetime, date
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

def render_analytics_page(pw: str, db: Session) -> str:
    users = db.query(User).all()
    chats = db.query(Chat).all()
    
    total_users = len(users)
    total_queries = sum(u.total_queries for u in users)
    today_queries = sum(u.queries_today for u in users)
    active_chats = len(chats)
    
    free_count = sum(1 for u in users if u.plan == 'free')
    pro_count = sum(1 for u in users if u.plan == 'pro')
    enterprise_count = sum(1 for u in users if u.plan == 'enterprise')
    
    sorted_users = sorted(users, key=lambda u: u.total_queries, reverse=True)[:5]
    top_users = ""
    max_queries = max([u.total_queries for u in sorted_users], default=1)
    for u in sorted_users:
        pct = int((u.total_queries / max_queries) * 100) if max_queries > 0 else 0
        top_users += f"""<div class="bar-chart">
            <span class="bar-label">{u.name[:15]}</span>
            <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
            <span class="bar-value">{u.total_queries}</span>
        </div>"""
    
    recent_users = ""
    for u in sorted(users, key=lambda u: u.created_at, reverse=True)[:10]:
        joined = u.created_at.strftime('%Y-%m-%d') if u.created_at else 'N/A'
        recent_users += f"<tr><td>{u.name}</td><td>{u.email}</td><td>{u.plan.upper()}</td><td>{u.total_queries}</td><td>{joined}</td></tr>"
    
    with open("templates/analytics.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    html = html.replace("{{TOTAL_USERS}}", str(total_users))
    html = html.replace("{{TOTAL_QUERIES}}", str(total_queries))
    html = html.replace("{{TODAY_QUERIES}}", str(today_queries))
    html = html.replace("{{ACTIVE_CHATS}}", str(active_chats))
    html = html.replace("{{FREE_COUNT}}", str(free_count))
    html = html.replace("{{PRO_COUNT}}", str(pro_count))
    html = html.replace("{{ENTERPRISE_COUNT}}", str(enterprise_count))
    html = html.replace("{{TOP_USERS}}", top_users)
    html = html.replace("{{RECENT_USERS}}", recent_users)
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

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(pw: str = "", db: Session = Depends(get_db)):
    if pw != settings.ADMIN_PASSWORD:
        return RedirectResponse("/admin")
    return render_analytics_page(pw, db)

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(pw: str = "", db: Session = Depends(get_db)):
    if pw != settings.ADMIN_PASSWORD:
        return """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Admin Login - Safari AI Pro</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;background:#f5e6d3}
form{background:#fff;padding:40px;border-radius:15px;box-shadow:0 10px 40px rgba(0,0,0,.2);width:100%;max-width:400px}
h2{color:#8b4513;margin-bottom:20px;text-align:center;font-size:24px}
p{color:#888;text-align:center;margin-bottom:20px;font-size:13px}
input{padding:12px;margin-bottom:20px;width:100%;border:2px solid #d2691e;border-radius:8px;font-size:16px;outline:0}
button{background:#d2691e;color:#fff;border:0;padding:14px;border-radius:8px;cursor:pointer;font-weight:bold;width:100%;font-size:16px}
button:hover{background:#8b4513}
.back{display:block;text-align:center;margin-top:15px;color:#d2691e;text-decoration:none;font-size:13px}
</style>
</head>
<body>
<form method="get" action="/admin">
<h2>&#x1F981; Safari AI Pro Admin</h2>
<p>Enter admin password to continue</p>
<input type="password" name="pw" placeholder="Admin password" required autofocus>
<button type="submit">Login to Admin</button>
<a href="/" class="back">Back to Chat</a>
</form>
</body></html>"""
    
    return render_admin_page(pw, db)

@app.post("/admin/generate")
async def admin_generate(email: str = Form(...), plan: str = Form(default="free"), pw: str = Form(...), db: Session = Depends(get_db)):
    if pw != settings.ADMIN_PASSWORD:
        return RedirectResponse("/admin")
    
    api_key = hashlib.sha256(f"{email}{time.time()}".encode()).hexdigest()[:32]
    limit_map = {"free": 10, "pro": 1000, "enterprise": 10000}
    
    user = db.query(User).filter(User.email == email).first()
    
    new_key = APIKey(
        key=api_key,
        user_id=user.id if user else None,
        plan=plan,
        daily_limit=limit_map.get(plan, 10),
        is_active=True
    )
    db.add(new_key)
    db.commit()
    
    return RedirectResponse(f"/admin?pw={pw}", status_code=303)

@app.post("/admin/revoke-key")
async def admin_revoke_key(key: str = Form(...), pw: str = Form(...), db: Session = Depends(get_db)):
    if pw != settings.ADMIN_PASSWORD:
        return RedirectResponse("/admin")
    
    api_key = db.query(APIKey).filter(APIKey.key == key).first()
    if api_key:
        db.delete(api_key)
        db.commit()
    
    return RedirectResponse(f"/admin?pw={pw}", status_code=303)

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

@app.post("/admin/logout")
async def admin_logout():
    return RedirectResponse("/admin", status_code=303)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }
