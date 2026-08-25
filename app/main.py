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
    if not settings.ADMIN_PASSWORD or pw != settings.ADMIN_PASSWORD:
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
    api_keys = db.query(APIKey).all()
    
    user_rows = ""
    for u in users:
        status = "Banned" if u.is_banned else "Active"
        status_color = "red" if u.is_banned else "green"
        action = f'<a href="/admin/ban?email={u.email}&pw={pw}" style="color:red">Ban</a>' if not u.is_banned else f'<a href="/admin/unban?email={u.email}&pw={pw}" style="color:green">Unban</a>'
        user_rows += f"<tr><td>{u.name}</td><td>{u.email}</td><td>{u.plan}</td><td>{u.queries_today}/{u.daily_limit}</td><td>{u.total_queries}</td><td style='color:{status_color}'>{status}</td><td>{action}</td></tr>"
    
    api_rows = ""
    for k in api_keys:
        email_display = k.email if k.email else (k.user.email if k.user else "N/A")
        api_rows += f"""<tr>
            <td>{email_display}</td>
            <td>{k.plan}</td>
            <td>0/{k.daily_limit}</td>
            <td>0</td>
            <td><code id="key_{k.id}">{k.key}</code> <button onclick="copyKey('key_{k.id}')" style="background:#2e7d32;color:#fff;border:none;padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px">Copy</button> <button onclick="printKey('key_{k.id}')" style="background:#1565c0;color:#fff;border:none;padding:3px 8px;border-radius:4px;cursor:pointer;font-size:11px">Print</button></td>
            <td><form method='post' action='/admin/revoke-key' style='display:inline' onsubmit='return confirm(\"Revoke this API key?\")'><input type='hidden' name='key' value='{k.key}'><input type='hidden' name='pw' value='{pw}'><button type='submit' style='background:#d32f2f;color:#fff;border:none;padding:5px 10px;border-radius:5px;cursor:pointer'>Revoke</button></form></td>
        </tr>"""
    
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Admin Panel - Safari AI Pro</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',sans-serif;background:#f5e6d3;padding:20px;min-height:100vh}}
.c{{max-width:1300px;margin:auto;background:#fff;border-radius:20px;box-shadow:0 10px 40px rgba(0,0,0,.15);padding:30px}}
.header-row{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:20px}}
h1{{color:#8b4513;font-size:24px}}
.btn-logout{{background:#d32f2f;color:#fff;border:none;padding:8px 16px;border-radius:8px;cursor:pointer;font-size:13px;text-decoration:none}}
.stats{{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap}}
.stat-card{{background:#faf5f0;padding:15px;border-radius:10px;text-align:center;min-width:100px;flex:1;border:1px solid #e0c8a8}}
.stat-card h3{{color:#d2691e;font-size:11px;margin-bottom:5px}}
.stat-card .num{{color:#8b4513;font-size:24px;font-weight:bold}}
.form-section{{background:#faf5f0;padding:20px;border-radius:10px;margin:20px 0;border:1px solid #e0c8a8}}
.form-section h3{{color:#8b4513;margin-bottom:15px}}
.form-row{{display:flex;gap:10px;flex-wrap:wrap}}
.form-row input{{flex:1;padding:10px;border:2px solid #d2691e;border-radius:8px;font-size:14px;outline:0;min-width:150px}}
.form-row select{{padding:10px;border:2px solid #d2691e;border-radius:8px;font-size:14px;outline:0}}
.form-row button{{background:#d2691e;color:#fff;border:none;padding:10px 20px;border-radius:8px;cursor:pointer;font-weight:bold}}
.table-wrapper{{overflow-x:auto;border-radius:10px;border:1px solid #e0c8a8;margin:15px 0}}
table{{width:100%;border-collapse:collapse;font-size:13px;min-width:700px}}
th{{background:#d2691e;color:#fff;padding:10px;text-align:left;border:1px solid #e0c8a8;position:sticky;top:0}}
td{{padding:8px 10px;border:1px solid #e0c8a8}}
tr:hover{{background:#faf5f0}}
h2{{color:#8b4513;font-size:16px;margin-top:20px}}
a{{color:#d2691e;text-decoration:none}}
code{{background:#f0e0d0;padding:3px 8px;border-radius:4px;font-size:12px}}
@media(max-width:600px){{.c{{padding:15px}}.stat-card{{min-width:45%}}}}
</style>
</head>
<body>
<div class="c">
<div class="header-row">
<h1>&#x1F981; Admin Panel - Safari AI Pro</h1>
<a href="/" class="btn-logout">Exit Admin</a>
</div>
<div class="stats">
<div class="stat-card"><h3>Total Users</h3><div class="num">{len(users)}</div></div>
<div class="stat-card"><h3>Free</h3><div class="num">{sum(1 for u in users if u.plan=='free')}</div></div>
<div class="stat-card"><h3>Pro</h3><div class="num">{sum(1 for u in users if u.plan=='pro')}</div></div>
<div class="stat-card"><h3>Enterprise</h3><div class="num">{sum(1 for u in users if u.plan=='enterprise')}</div></div>
<div class="stat-card"><h3>API Keys</h3><div class="num">{len(api_keys)}</div></div>
<div class="stat-card"><h3>Banned</h3><div class="num">{sum(1 for u in users if u.is_banned)}</div></div>
</div>

<div class="form-section">
<h3>Generate New API Key</h3>
<form method="post" action="/admin/generate">
<div class="form-row">
<input type="hidden" name="pw" value="{pw}">
<input type="email" name="email" placeholder="User email address" required>
<select name="plan">
<option value="free">Free (10/day)</option>
<option value="pro">Pro (1,000/day)</option>
<option value="enterprise">Enterprise (10,000/day)</option>
</select>
<button type="submit">Generate Key</button>
</div>
</form>
</div>

<h2>Login Accounts</h2>
<div class="table-wrapper">
<table>
<tr><th>Name</th><th>Email</th><th>Plan</th><th>Usage Today</th><th>Total</th><th>Status</th><th>Actions</th></tr>
{user_rows}
</table>
</div>

<h2>API Key Users</h2>
<div class="table-wrapper">
<table>
<tr><th>Email</th><th>Plan</th><th>Usage</th><th>Total</th><th>API Key</th><th>Action</th></tr>
{api_rows}
</table>
</div>

<a href="/">Back to Chat</a>
</div>
<script>
function copyKey(elementId) {{
    var key = document.getElementById(elementId).innerText;
    navigator.clipboard.writeText(key).then(function() {{
        alert('API Key copied to clipboard!');
    }});
}}
function printKey(elementId) {{
    var key = document.getElementById(elementId).innerText;
    var win = window.open('', '_blank');
    win.document.write('<h2>Safari AI Pro - API Key</h2><p><strong>Key:</strong> ' + key + '</p><p><em>Generated by Safari Softwares</em></p>');
    win.document.write('<script>window.print()</scr' + 'ipt>');
}}
</script>
</body></html>"""

@app.post("/admin/generate")
async def admin_generate(email: str = Form(...), plan: str = Form(default="free"), pw: str = Form(...), db: Session = Depends(get_db)):
    if not settings.ADMIN_PASSWORD or pw != settings.ADMIN_PASSWORD:
        return RedirectResponse("/admin")
    api_key = hashlib.sha256(f"{email}{time.time()}".encode()).hexdigest()[:32]
    limit_map = {"free": 10, "pro": 1000, "enterprise": 10000}
    user = db.query(User).filter(User.email == email).first()
    new_key = APIKey(key=api_key, email=email, user_id=user.id if user else None, plan=plan, daily_limit=limit_map.get(plan, 10), is_active=True)
    db.add(new_key)
    db.commit()
    return RedirectResponse(f"/admin?pw={pw}", status_code=303)

@app.post("/admin/revoke-key")
async def admin_revoke_key(key: str = Form(...), pw: str = Form(...), db: Session = Depends(get_db)):
    if not settings.ADMIN_PASSWORD or pw != settings.ADMIN_PASSWORD:
        return RedirectResponse("/admin")
    api_key = db.query(APIKey).filter(APIKey.key == key).first()
    if api_key:
        db.delete(api_key)
        db.commit()
    return RedirectResponse(f"/admin?pw={pw}", status_code=303)

@app.get("/admin/ban")
async def admin_ban(email: str = "", pw: str = "", db: Session = Depends(get_db)):
    if not settings.ADMIN_PASSWORD or pw != settings.ADMIN_PASSWORD:
        return RedirectResponse("/admin")
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_banned = True
        db.commit()
    return RedirectResponse(f"/admin?pw={pw}")

@app.get("/admin/unban")
async def admin_unban(email: str = "", pw: str = "", db: Session = Depends(get_db)):
    if not settings.ADMIN_PASSWORD or pw != settings.ADMIN_PASSWORD:
        return RedirectResponse("/admin")
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_banned = False
        db.commit()
    return RedirectResponse(f"/admin?pw={pw}")

@app.get("/health")
async def health():
    return {"status":"ok","service":settings.APP_NAME,"version":settings.APP_VERSION,"timestamp":datetime.now().isoformat()}
