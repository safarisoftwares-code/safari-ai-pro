path = 'app/routes/chat.py'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Add sync endpoint before the last route
old = "@router.get('/history')"

new = """@router.post('/sync')
async def sync_chats(token: str = Form(...), chats: str = Form(...), db: Session = Depends(get_db)):
    payload = AuthService.decode_access_token(token)
    if not payload:
        return {'status': 'error', 'message': 'Invalid token'}
    email = payload.get('email')
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {'status': 'error', 'message': 'User not found'}
    try:
        chat_data = json.loads(chats)
        for chat_id, chat_info in chat_data.items():
            existing = db.query(Chat).filter(Chat.session_id == chat_id, Chat.user_id == user.id).first()
            if existing:
                existing.messages = json.dumps(chat_info.get('messages', []))
                existing.title = chat_info.get('name', 'Chat')
                existing.updated_at = datetime.utcnow()
            else:
                new_chat = Chat(session_id=chat_id, user_id=user.id, title=chat_info.get('name', 'Chat'), messages=json.dumps(chat_info.get('messages', [])))
                db.add(new_chat)
        db.commit()
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@router.get('/history')"""

if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('SYNC ENDPOINT ADDED')
else:
    print('Pattern not found')
