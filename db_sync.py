path = 'static/js/chat.js'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

# Add database sync after saveChats
old = "function saveChats(){try{localStorage.setItem('safari_pro_chats',JSON.stringify(chats));}catch(e){}}"

new = """function saveChats(){try{localStorage.setItem('safari_pro_chats',JSON.stringify(chats));}catch(e){}syncChatsToServer();}
window.syncChatsToServer=async function(){try{var token=localStorage.getItem('safari_token');if(!token)return;var fd=new FormData();fd.append('token',token);fd.append('chats',JSON.stringify(chats));await fetch('/api/v1/chat/sync',{method:'POST',body:fd});}catch(e){}}"""

if old in c:
    c = c.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('DB SYNC ADDED')
else:
    print('Pattern not found')
