let chats={};
let activeChat=null;
let isProcessing=false;
let pendingFile=null;
let pendingImage=null;
let guestRemaining=null;
let mediaRecorder=null;
let audioChunks=[];
let isRecording=false;
const GUEST_WARNING_THRESHOLD=5;

function renderMarkdown(text){
    if(typeof marked!=='undefined'){
        var html = marked.parse(text);
        if(typeof MathJax !== 'undefined'){
            setTimeout(function(){ MathJax.typesetPromise(); }, 150);
        }
        return html;
    }
    return text.replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function addCodeButtons(container){
    var codeBlocks=container.querySelectorAll('pre code');
    codeBlocks.forEach(function(codeBlock,i){
        var pre=codeBlock.parentElement;
        if(pre.querySelector('.code-btn-group'))return;
        var btnGroup=document.createElement('div');
        btnGroup.className='code-btn-group';
        btnGroup.style.cssText='position:absolute;top:8px;right:8px;display:flex;gap:5px';
        var copyBtn=document.createElement('button');
        copyBtn.textContent='Copy';
        copyBtn.style.cssText='background:#2e7d32;color:#fff;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:11px;font-weight:bold';
        copyBtn.onclick=function(){navigator.clipboard.writeText(codeBlock.textContent).then(function(){copyBtn.textContent='Copied!';setTimeout(function(){copyBtn.textContent='Copy';},1500);showToast('Code copied!');});};
        var downloadBtn=document.createElement('button');
        downloadBtn.textContent='Download';
        downloadBtn.style.cssText='background:#d2691e;color:#fff;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:11px;font-weight:bold';
        downloadBtn.onclick=function(){var lang='txt';var classMatch=codeBlock.className.match(/language-(\w+)/);if(classMatch)lang=classMatch[1];downloadFile(codeBlock.textContent,'generated.'+lang,'text/plain');showToast('File downloaded!');};
        btnGroup.appendChild(copyBtn);
        btnGroup.appendChild(downloadBtn);
        pre.style.position='relative';
        pre.appendChild(btnGroup);
    });
}

function addDocumentButtons(container){
    var docMessages=container.querySelectorAll('.doc-download-ready');
    docMessages.forEach(function(msgDiv){
        if(msgDiv.querySelector('.doc-btn-group'))return;
        var text=msgDiv.innerText || msgDiv.textContent;
        if(text.length < 100) return;
        var btnGroup=document.createElement('div');
        btnGroup.className='doc-btn-group';
        btnGroup.style.cssText='display:flex;gap:6px;margin-top:10px;flex-wrap:wrap';
        var docName=text.substring(0,50).replace(/[^a-zA-Z0-9]/g,'_').toLowerCase()+'_document';
        
        var copyAllBtn=document.createElement('button');
        copyAllBtn.textContent='Copy All';
        copyAllBtn.style.cssText='background:#6a1b9a;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:11px;font-weight:bold';
        copyAllBtn.onclick=function(){
            navigator.clipboard.writeText(text).then(function(){
                copyAllBtn.textContent='Copied!';
                setTimeout(function(){copyAllBtn.textContent='Copy All';},1500);
                showToast('Full response copied to clipboard!');
            });
        };
        
        var txtBtn=document.createElement('button');
        txtBtn.textContent='Download .txt';
        txtBtn.style.cssText='background:#d2691e;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:11px;font-weight:bold';
        txtBtn.onclick=function(){downloadFile(text,docName+'.txt','text/plain');showToast('Downloaded as TXT!');};
        
        var htmlBtn=document.createElement('button');
        htmlBtn.textContent='Download .html';
        htmlBtn.style.cssText='background:#2e7d32;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:11px;font-weight:bold';
        htmlBtn.onclick=function(){var htmlContent='<!DOCTYPE html><html><head><meta charset="UTF-8"><title>'+docName+'</title><style>body{font-family:Segoe UI,sans-serif;padding:40px;max-width:800px;margin:auto;line-height:1.7}h1{color:#8b4513}h2{color:#d2691e;margin-top:20px}</style></head><body>'+msgDiv.innerHTML+'</body></html>';downloadFile(htmlContent,docName+'.html','text/html');showToast('Downloaded as HTML!');};
        
        var docBtn=document.createElement('button');
        docBtn.textContent='Download .doc';
        docBtn.style.cssText='background:#1565c0;color:#fff;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:11px;font-weight:bold';
        docBtn.onclick=function(){var docContent='<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word"><head><meta charset="UTF-8"><title>'+docName+'</title></head><body>'+msgDiv.innerHTML+'</body></html>';downloadFile(docContent,docName+'.doc','application/msword');showToast('Downloaded as Word!');};
        
        btnGroup.appendChild(copyAllBtn);
        btnGroup.appendChild(txtBtn);
        btnGroup.appendChild(htmlBtn);
        btnGroup.appendChild(docBtn);
        msgDiv.appendChild(btnGroup);
    });
}

function downloadFile(content,filename,mimeType){
    var blob=new Blob([content],{type:mimeType});
    var url=URL.createObjectURL(blob);
    var a=document.createElement('a');
    a.href=url;
    a.download=filename;
    a.click();
    URL.revokeObjectURL(url);
}

function toggleSearch(){
    var bar=document.getElementById('searchBar');
    var results=document.getElementById('searchResults');
    if(!bar)return;
    if(bar.style.display==='none'||bar.style.display===''){
        bar.style.display='flex';
        setTimeout(function(){var input=document.getElementById('searchInput');if(input)input.focus();},100);
    }else{
        bar.style.display='none';
        if(results)results.style.display='none';
        var input=document.getElementById('searchInput');
        if(input)input.value='';
    }
}

function closeSearch(){
    var bar=document.getElementById('searchBar');
    var results=document.getElementById('searchResults');
    if(bar)bar.style.display='none';
    if(results)results.style.display='none';
    var input=document.getElementById('searchInput');
    if(input)input.value='';
}

function searchChats(query){
    var results=document.getElementById('searchResults');
    if(!results)return;
    if(!query||query.trim().length<2){results.style.display='none';results.innerHTML='';return;}
    var allResults=[];
    var q=query.toLowerCase();
    Object.keys(chats).forEach(function(chatId){
        var chat=chats[chatId];
        var msgs=chat.messages||[];
        var times=chat.timestamps||[];
        msgs.forEach(function(m,i){
            var content=m.substring(2);
            if(content.toLowerCase().indexOf(q)!==-1){allResults.push({chatId:chatId,chatName:chat.name||'Chat',content:content,time:times[i]||null,index:i});}
        });
    });
    if(allResults.length===0){results.innerHTML='<p style="text-align:center;color:#999;font-size:12px;padding:10px">No results found</p>';results.style.display='block';return;}
    results.innerHTML='';
    allResults.slice(0,20).forEach(function(r){
        var div=document.createElement('div');
        div.className='search-result';
        var preview=r.content;
        if(preview.length>100)preview=preview.substring(0,100)+'...';
        var idx=preview.toLowerCase().indexOf(q);
        var highlighted=preview;
        if(idx!==-1){highlighted=preview.substring(0,idx)+'<span class="highlight">'+preview.substring(idx,idx+q.length)+'</span>'+preview.substring(idx+q.length);}
        var timeStr=r.time?new Date(r.time).toLocaleString():'';
        div.innerHTML=highlighted+'<span class="src">'+r.chatName+' | '+timeStr+'</span>';
        div.onclick=function(){activeChat=r.chatId;renderTabs();renderMessages();closeSearch();showToast('Jumped to chat');};
        results.appendChild(div);
    });
    results.style.display='block';
}

function showExportMenu(){
    var overlay=document.createElement('div');
    overlay.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:999;display:flex;justify-content:center;align-items:center';
    overlay.onclick=function(e){if(e.target===overlay)overlay.remove();};
    var menu=document.createElement('div');
    menu.style.cssText='background:#fff;border-radius:15px;padding:25px;width:90%;max-width:350px;text-align:center';
    menu.innerHTML='<h3 style="color:#8b4513;margin-bottom:15px">Export Chat As</h3>';
    var formats=[{name:'Text File (.txt)',action:function(){exportChatTXT();}},{name:'JSON File (.json)',action:function(){exportChatJSON();}},{name:'PDF Document (.pdf)',action:function(){exportChatPDF();}}];
    formats.forEach(function(f){
        var btn=document.createElement('button');
        btn.textContent=f.name;
        btn.style.cssText='display:block;width:100%;padding:12px;margin:8px 0;border:2px solid #d2691e;border-radius:10px;background:#fff;color:#d2691e;cursor:pointer;font-weight:bold;font-size:14px';
        btn.onclick=function(){overlay.remove();f.action();};
        menu.appendChild(btn);
    });
    var cancelBtn=document.createElement('button');
    cancelBtn.textContent='Cancel';
    cancelBtn.style.cssText='display:block;width:100%;padding:10px;margin-top:10px;border:none;border-radius:10px;background:#f0e0d0;color:#8b4513;cursor:pointer;font-weight:bold';
    cancelBtn.onclick=function(){overlay.remove();};
    menu.appendChild(cancelBtn);
    overlay.appendChild(menu);
    document.body.appendChild(overlay);
}

function getChatData(){
    if(!activeChat||!chats[activeChat])return null;
    var chat=chats[activeChat];
    var msgs=chat.messages||[];
    var times=chat.timestamps||[];
    var data={title:chat.name||'Chat',exported_at:new Date().toISOString(),messages:[]};
    msgs.forEach(function(m,i){var time=times[i]?new Date(times[i]).toLocaleString():'';if(m.startsWith('U:')){data.messages.push({role:'user',content:m.substring(2),time:time});}else if(m.startsWith('S:')){data.messages.push({role:'assistant',content:m.substring(2),time:time});}});
    return data;
}

function exportChatTXT(){var data=getChatData();if(!data)return;var text='Safari AI Pro Chat Export\nDate: '+new Date().toLocaleString()+'\nChat: '+data.title+'\n'+'='.repeat(50)+'\n\n';data.messages.forEach(function(m){var role=m.role==='user'?'You':'Safari AI';text+=role+' ('+m.time+'): '+m.content+'\n\n';});downloadFile(text,'chat.txt','text/plain');showToast('Exported as TXT!');}
function exportChatJSON(){var data=getChatData();if(!data)return;downloadFile(JSON.stringify(data,null,2),'chat.json','application/json');showToast('Exported as JSON!');}
function exportChatPDF(){var data=getChatData();if(!data)return;var html='<!DOCTYPE html><html><head><meta charset="UTF-8"><title>'+data.title+'</title><style>body{font-family:Segoe UI,sans-serif;padding:40px;max-width:800px;margin:auto;line-height:1.7}h1{color:#8b4513}.msg{margin:15px 0;padding:12px;border-radius:10px}.user{background:#8b4513;color:#fff}.assistant{background:#faf5f0;border:1px solid #d2691e}.time{font-size:10px;color:#999}</style></head><body><h1>Safari AI Pro - Chat Export</h1>';data.messages.forEach(function(m){var cls=m.role==='user'?'user':'assistant';var name=m.role==='user'?'You':'Safari AI';html+='<div class="msg '+cls+'"><strong>'+name+'</strong><br>'+m.content.replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>')+'<div class="time">'+m.time+'</div></div>';});html+='</body></html>';var blob=new Blob([html],{type:'text/html'});var url=URL.createObjectURL(blob);var win=window.open(url,'_blank');setTimeout(function(){if(win)win.print();},500);showToast('PDF export opened! Press Ctrl+P to save.');}

async function startRecording(){if(isRecording){stopRecording();return;}try{const stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,sampleRate:16000,echoCancellation:true,noiseSuppression:true}});const mimeType=MediaRecorder.isTypeSupported('audio/webm')?'audio/webm':'audio/mp4';mediaRecorder=new MediaRecorder(stream,{mimeType:mimeType});audioChunks=[];mediaRecorder.ondataavailable=function(e){if(e.data.size>0){audioChunks.push(e.data);}};mediaRecorder.onstop=async function(){const audioBlob=new Blob(audioChunks,{type:mimeType});if(audioBlob.size<1000){showToast('Recording too short.');stream.getTracks().forEach(track=>track.stop());return;}const formData=new FormData();const ext=mimeType.includes('webm')?'webm':'m4a';formData.append('audio',audioBlob,'recording.'+ext);showToast('Transcribing...');try{const r=await fetch('/api/v1/chat/transcribe',{method:'POST',body:formData});const d=await r.json();if(d.status==='success'&&d.transcript){document.getElementById('q').value=d.transcript;showToast('Voice transcribed!');}else{showToast('Could not transcribe.');}}catch(e){showToast('Transcription error.');}stream.getTracks().forEach(track=>track.stop());};mediaRecorder.start(1000);isRecording=true;document.getElementById('micBtn').style.background='#ff6b6b';document.getElementById('micBtn').textContent='Stop';showToast('Recording... Click Stop.');}catch(e){showToast('Microphone not available.');}}
function stopRecording(){if(mediaRecorder&&isRecording){mediaRecorder.stop();isRecording=false;document.getElementById('micBtn').style.background='#e8f5e9';document.getElementById('micBtn').textContent='Mic';}}
function isLoggedIn(){return !!localStorage.getItem('safari_token');}
function showToast(msg){var t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(function(){t.classList.remove('show');},3000);}
async function fetchGuestStatus(){try{var r=await fetch('/api/v1/chat/guest-status');var d=await r.json();if(d.status==='success'){guestRemaining=d.remaining;updateUserUI();}}catch(e){}}
function updateUserUI(){var token=localStorage.getItem('safari_token');var name=localStorage.getItem('safari_name');var guestBadge=document.getElementById('guestBadge');var profileLink=document.getElementById('profileLink');if(token&&name){document.getElementById('userName').textContent=name;document.getElementById('loginLink').style.display='none';document.getElementById('logoutBtn').style.display='inline-block';if(profileLink)profileLink.style.display='inline';guestBadge.style.display='none';}else{document.getElementById('userName').textContent='';document.getElementById('loginLink').style.display='inline';document.getElementById('logoutBtn').style.display='none';if(profileLink)profileLink.style.display='none';if(guestRemaining!==null){guestBadge.textContent='Guest: '+guestRemaining+' queries left';guestBadge.style.display='inline-block';if(guestRemaining<=3){guestBadge.style.background='#d32f2f';}else{guestBadge.style.background='#ff9800';}}}}
function logoutUser(){localStorage.clear();chats={};activeChat=null;guestRemaining=null;var id='chat_'+Date.now();chats[id]={name:'New Chat',messages:[],timestamps:[]};activeChat=id;saveChats();updateUserUI();renderTabs();renderMessages();showToast('Logged out.');}
function loadChats(){try{var saved=localStorage.getItem('safari_pro_chats');if(saved)chats=JSON.parse(saved);}catch(e){chats={};}if(!chats||Object.keys(chats).length===0){chats={};var id='chat_'+Date.now();chats[id]={name:'New Chat',messages:[],timestamps:[]};saveChats();}}
function saveChats(){try{localStorage.setItem('safari_pro_chats',JSON.stringify(chats));}catch(e){}syncChatsToServer();}
window.syncChatsToServer=async function(){try{var token=localStorage.getItem('safari_token');if(!token)return;var fd=new FormData();fd.append('token',token);fd.append('chats',JSON.stringify(chats));await fetch('/api/v1/chat/sync',{method:'POST',body:fd});}catch(e){}}
function getChatPreview(messages){if(!messages||messages.length===0)return'New Chat';for(var i=0;i<messages.length;i++){if(messages[i].startsWith('U:'))return messages[i].substring(2).substring(0,30);}return'Chat';}
function renderTabs(){var tabs=document.getElementById('tabs');if(!tabs)return;tabs.innerHTML='';var chatIds=Object.keys(chats);var realIds=chatIds.filter(function(id){return chats[id].messages&&chats[id].messages.length>0;});var visibleIds=realIds.slice(-3);var hiddenIds=realIds.slice(0,-3);visibleIds.forEach(function(id){var chat=chats[id];if(!chat.name||chat.name==='New Chat'){chat.name=getChatPreview(chat.messages);}if(chat.name==='New Chat')return;var tab=document.createElement('div');tab.className='tab'+(id===activeChat?' active':'');var nameSpan=document.createElement('span');nameSpan.className='tab-name';nameSpan.textContent=chat.name.length>20?chat.name.substring(0,20)+'...':chat.name;tab.appendChild(nameSpan);tab.addEventListener('click',function(e){if(e.target.classList.contains('del')||e.target.classList.contains('rename-btn'))return;switchChat(id);});if(chatIds.length>1){var renameBtn=document.createElement('span');renameBtn.className='rename-btn';renameBtn.textContent='R';renameBtn.title='Rename';renameBtn.addEventListener('click',function(e){e.stopPropagation();renameChatTab(id);});tab.appendChild(renameBtn);var del=document.createElement('span');del.className='del';del.textContent='x';del.title='Delete';del.addEventListener('click',function(e){e.stopPropagation();if(confirm('Delete this chat?')){deleteChat(id);}});tab.appendChild(del);}tabs.appendChild(tab);});if(hiddenIds.length>0){var showMore=document.createElement('div');showMore.className='tab';showMore.textContent='▼ More ('+hiddenIds.length+')';showMore.style.cssText='text-align:center;font-weight:bold;color:#8b4513;background:#f0e0d0;cursor:pointer;padding:8px;border-radius:8px;margin:4px 0';showMore.addEventListener('click',function(e){e.stopPropagation();showAllChats();});tabs.appendChild(showMore);}}
window.showAllChats=function(){var tabs=document.getElementById('tabs');if(!tabs)return;tabs.innerHTML='';var chatIds=Object.keys(chats);chatIds.forEach(function(id){var chat=chats[id];var tab=document.createElement('div');tab.className='tab'+(id===activeChat?' active':'');var nameSpan=document.createElement('span');nameSpan.className='tab-name';nameSpan.textContent=(chat.name||'Chat').substring(0,20);tab.appendChild(nameSpan);tab.addEventListener('click',function(){switchChat(id);});if(chatIds.length>1){var del=document.createElement('span');del.className='del';del.textContent='x';del.addEventListener('click',function(e){e.stopPropagation();if(confirm('Delete this chat?')){deleteChat(id);}});tab.appendChild(del);}tabs.appendChild(tab);});var backBtn=document.createElement('div');backBtn.className='tab';backBtn.textContent='▲ Show Recent';backBtn.style.cssText='text-align:center;font-weight:bold;color:#8b4513;background:#f0e0d0;cursor:pointer;padding:8px;border-radius:8px;margin:4px 0';backBtn.addEventListener('click',function(){renderTabs();});tabs.appendChild(backBtn);};
function renameChatTab(id){var chat=chats[id];var newName=prompt('Enter new name:',chat.name||'New Chat');if(newName&&newName.trim()){chat.name=newName.trim();saveChats();renderTabs();}}
function switchChat(id){activeChat=id;renderTabs();renderMessages();var sidebar=document.querySelector('.sidebar');if(sidebar){sidebar.classList.remove('show');}}
window.newChat=function(){var chatIds=Object.keys(chats);for(var i=0;i<chatIds.length;i++){var c=chats[chatIds[i]];if(!c.messages||c.messages.length===0){activeChat=chatIds[i];renderTabs();renderMessages();return;}}var id='chat_'+Date.now();chats[id]={name:'New Chat',messages:[],timestamps:[]};activeChat=id;saveChats();renderTabs();renderMessages();}
window.showAllChats=function(){var tabs=document.getElementById('tabs');if(!tabs)return;tabs.innerHTML='';var chatIds=Object.keys(chats);chatIds.forEach(function(id){var chat=chats[id];var tab=document.createElement('div');tab.className='tab'+(id===activeChat?' active':'');var nameSpan=document.createElement('span');nameSpan.className='tab-name';nameSpan.textContent=(chat.name||'Chat').substring(0,20);tab.appendChild(nameSpan);tab.addEventListener('click',function(){switchChat(id);});if(chatIds.length>1){var del=document.createElement('span');del.className='del';del.textContent='x';del.addEventListener('click',function(e){e.stopPropagation();if(confirm('Delete this chat?')){deleteChat(id);}});tab.appendChild(del);}tabs.appendChild(tab);});var backBtn=document.createElement('div');backBtn.className='tab';backBtn.textContent='▲ Show Recent';backBtn.style.cssText='text-align:center;font-weight:bold;color:#8b4513;background:#f0e0d0;cursor:pointer;padding:6px';backBtn.addEventListener('click',function(){renderTabs();});tabs.appendChild(backBtn);};
window.clearAllChats=function(){if(confirm('Final confirmation: Delete ALL chats?')){chats={};var id='chat_'+Date.now();chats[id]={name:'New Chat',messages:[],timestamps:[]};activeChat=id;saveChats();renderTabs();renderMessages();showToast('All chats cleared!');}}
function deleteChat(id){if(Object.keys(chats).length<=1){showToast('Cannot delete last chat');return;}delete chats[id];saveChats();if(activeChat===id){activeChat=Object.keys(chats)[0];}renderTabs();renderMessages();showToast('Chat deleted');}
function copyMessage(text,btn){navigator.clipboard.writeText(text).then(function(){btn.innerHTML='&#9989;';setTimeout(function(){btn.innerHTML='&#128203;';},1500);showToast('Copied!');});}
function editMessage(index,msgDiv){var chat=chats[activeChat];var msg=chat.messages[index];var content=msg.substring(2);var editDiv=document.createElement('div');editDiv.className='m u';editDiv.style.width='75%';var input=document.createElement('textarea');input.className='edit-input';input.value=content;input.rows=Math.min(5,content.split('\n').length);editDiv.appendChild(input);var actions=document.createElement('div');actions.className='edit-actions';var saveBtn=document.createElement('button');saveBtn.className='btn-save';saveBtn.textContent='Save';saveBtn.onclick=function(){var newContent=input.value.trim();if(newContent){chat.messages=chat.messages.slice(0,index);chat.timestamps=chat.timestamps.slice(0,index);chat.messages.push('U:'+newContent);chat.timestamps.push(Date.now());saveChats();renderMessages();setProcessing(true);sendEditedMessage(newContent);}};var cancelBtn=document.createElement('button');cancelBtn.className='btn-cancel';cancelBtn.textContent='Cancel';cancelBtn.onclick=function(){renderMessages();};actions.appendChild(saveBtn);actions.appendChild(cancelBtn);editDiv.appendChild(actions);msgDiv.parentElement.replaceChild(editDiv,msgDiv);input.focus();}
async function sendEditedMessage(question){try{var form=new FormData();form.append('question',question);form.append('session_id',activeChat);var token=localStorage.getItem('safari_token');if(token)form.append('token',token);var r=await fetch('/api/v1/chat/ask',{method:'POST',body:form});var d=await r.json();var errMsg=d.response||d.detail||JSON.stringify(d);chats[activeChat].messages.push('S:'+errMsg);chats[activeChat].timestamps.push(Date.now());}catch(e){chats[activeChat].messages.push('S:Connection error.');chats[activeChat].timestamps.push(Date.now());}saveChats();renderMessages();setProcessing(false);}
function addWarningToChat(remaining){var box=document.getElementById('b');var wrapper=document.createElement('div');wrapper.className='m-wrapper bot';wrapper.innerHTML='<div class="warning-msg">Warning: You have '+remaining+' free queries left. <a href="/login">Login now</a> for unlimited access.</div>';box.appendChild(wrapper);box.scrollTop=box.scrollHeight;if(!chats[activeChat])return;chats[activeChat].messages.push('W:'+remaining);chats[activeChat].timestamps.push(Date.now());saveChats();}
function renderMessages(){var box=document.getElementById('b');if(!box)return;box.innerHTML='';if(!activeChat||!chats[activeChat])return;var msgs=chats[activeChat].messages||[];var times=chats[activeChat].timestamps||[];if(msgs.length===0){box.innerHTML='<div class="m s" style="max-width:60%">&#x1F981; Hello! Ask me anything or attach a file!</div>';}msgs.forEach(function(m,i){var wrapper=document.createElement('div');if(m.startsWith('U:')){wrapper.className='m-wrapper user';var msgDiv=document.createElement('div');msgDiv.className='m u';msgDiv.textContent=m.substring(2);wrapper.appendChild(msgDiv);var actions=document.createElement('div');actions.className='msg-actions';var editBtn=document.createElement('button');editBtn.className='msg-action-btn btn-edit';editBtn.innerHTML='&#128394;';editBtn.title='Edit';editBtn.style.background='#ff9800';editBtn.style.color='#fff';editBtn.onclick=function(){editMessage(i,msgDiv);};actions.appendChild(editBtn);wrapper.appendChild(actions);}else if(m.startsWith('S:')){wrapper.className='m-wrapper bot';var msgDiv2=document.createElement('div');msgDiv2.className='m s markdown-body doc-download-ready';msgDiv2.innerHTML=renderMarkdown(m.substring(2));wrapper.appendChild(msgDiv2);var actions2=document.createElement('div');actions2.className='msg-actions';var copyBtn=document.createElement('button');copyBtn.className='msg-action-btn btn-copy';copyBtn.innerHTML='&#128203;';copyBtn.title='Copy';copyBtn.onclick=function(){copyMessage(m.substring(2),copyBtn);};actions2.appendChild(copyBtn);wrapper.appendChild(actions2);}else if(m.startsWith('W:')){wrapper.className='m-wrapper bot';wrapper.innerHTML='<div class="warning-msg">Warning: You have '+m.substring(2)+' free queries left. <a href="/login">Login now</a> for unlimited access.</div>';}if(times[i]){var timeStamp=document.createElement('div');timeStamp.className='time-stamp';timeStamp.textContent=new Date(times[i]).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});wrapper.appendChild(timeStamp);}box.appendChild(wrapper);});addCodeButtons(box);addDocumentButtons(box);if(typeof MathJax !== 'undefined'){MathJax.typesetPromise();}box.scrollTop=box.scrollHeight;}
function setProcessing(state){isProcessing=state;var btn=document.getElementById('askBtn');var typing=document.getElementById('typing');if(state){btn.disabled=true;btn.textContent='Thinking...';typing.classList.add('show');}else{btn.disabled=false;btn.textContent='Ask';typing.classList.remove('show');}}
async function ask(){if(isProcessing)return;var input=document.getElementById('q');var question=input.value.trim();if(!question&&!pendingFile&&!pendingImage)return;if(question.length>2000){showToast('Message too long.');return;}if(!activeChat||!chats[activeChat])newChat();if(!chats[activeChat].messages)chats[activeChat].messages=[];if(!chats[activeChat].timestamps)chats[activeChat].timestamps=[];var displayText=question;if(pendingImage){displayText=question?question+' [Image: '+pendingImage.name+']':'[Image: '+pendingImage.name+']';}else if(pendingFile){displayText=question?question+' [Attached: '+pendingFile.name+']':'[Attached: '+pendingFile.name+']';}chats[activeChat].messages.push('U:'+displayText);chats[activeChat].timestamps.push(Date.now());saveChats();renderTabs();renderMessages();input.value='';var preview=document.getElementById('filePreview');preview.style.display='none';var imgPreview=document.getElementById('imagePreview');if(imgPreview)imgPreview.style.display='none';setProcessing(true);try{if(pendingImage){var imgForm=new FormData();imgForm.append('session_id',activeChat);imgForm.append('question',question||'Please analyze this image');imgForm.append('image',pendingImage);var token=localStorage.getItem('safari_token');if(token)imgForm.append('token',token);var imgResp=await fetch('/api/v1/chat/ask',{method:'POST',body:imgForm});var imgData=await imgResp.json();var imgErr=imgData.response||imgData.detail||JSON.stringify(imgData);chats[activeChat].messages.push('S:'+imgErr);chats[activeChat].timestamps.push(Date.now());pendingImage=null;}else if(pendingFile){var uploadForm=new FormData();uploadForm.append('session_id',activeChat);uploadForm.append('file',pendingFile);var uploadResp=await fetch('/api/v1/upload/',{method:'POST',body:uploadForm});var uploadData=await uploadResp.json();if(uploadData.status==='success'){var askForm=new FormData();askForm.append('session_id',activeChat);askForm.append('question',question||'Please analyze the attached file');var token=localStorage.getItem('safari_token');if(token)askForm.append('token',token);var askResp=await fetch('/api/v1/chat/ask',{method:'POST',body:askForm});var askData=await askResp.json();var errMsg2=askData.response||askData.detail||JSON.stringify(askData);chats[activeChat].messages.push('S:'+errMsg2);chats[activeChat].timestamps.push(Date.now());}else{chats[activeChat].messages.push('S:'+(uploadData.detail||'Upload failed.'));chats[activeChat].timestamps.push(Date.now());}pendingFile=null;}else{var form=new FormData();form.append('question',question);form.append('session_id',activeChat);var token=localStorage.getItem('safari_token');if(token)form.append('token',token);var r=await fetch('/api/v1/chat/ask',{method:'POST',body:form});var d=await r.json();var errMsg3=d.response||d.detail||JSON.stringify(d);chats[activeChat].messages.push('S:'+errMsg3);chats[activeChat].timestamps.push(Date.now());}}catch(e){chats[activeChat].messages.push('S:Connection error.');chats[activeChat].timestamps.push(Date.now());}saveChats();renderMessages();setProcessing(false);}
function selectFile(input){var file=input.files[0];if(!file)return;if(file.size>10*1024*1024){showToast('File too large. Maximum 10MB.');input.value='';return;}pendingFile=file;pendingImage=null;var preview=document.getElementById('filePreview');document.getElementById('fileName').textContent=file.name;preview.style.display='flex';var imgPreview=document.getElementById('imagePreview');if(imgPreview)imgPreview.style.display='none';showToast('File ready. Type question and Ask.');}
function selectImage(input){var file=input.files[0];if(!file)return;if(file.size>10*1024*1024){showToast('Image too large. Maximum 10MB.');input.value='';return;}pendingImage=file;pendingFile=null;var preview=document.getElementById('imagePreview');if(preview){document.getElementById('imageName').textContent=file.name;preview.style.display='flex';}var filePreview=document.getElementById('filePreview');if(filePreview)filePreview.style.display='none';showToast('Image ready. Type question and Ask.');}
function clearAttachment(){pendingFile=null;pendingImage=null;var input=document.getElementById('fileInput');if(input)input.value='';var imgInput=document.getElementById('imageInput');if(imgInput)imgInput.value='';document.getElementById('filePreview').style.display='none';var imgPreview=document.getElementById('imagePreview');if(imgPreview)imgPreview.style.display='none';showToast('Attachment removed.');}
document.addEventListener('keydown',function(e){if(e.ctrlKey&&e.key==='f'){e.preventDefault();toggleSearch();}});
document.addEventListener('DOMContentLoaded',function(){fetchGuestStatus();loadChats();var chatIds=Object.keys(chats);var existingEmpty=null;for(var i=0;i<chatIds.length;i++){var c=chats[chatIds[i]];if(!c.messages||c.messages.length===0){existingEmpty=chatIds[i];break;}}if(existingEmpty){activeChat=existingEmpty;}else{activeChat='chat_'+Date.now();chats[activeChat]={name:'New Chat',messages:[],timestamps:[]};saveChats();}renderTabs();renderMessages();});


window.toggleSidebar=function(){
    var sidebar=document.querySelector('.sidebar');
    if(sidebar){
        sidebar.classList.toggle('show');
    }
};


// FEEDBACK FUNCTIONS
let feedbackRating = 5;

function openFeedback(){
    document.getElementById('feedbackModal').classList.add('show');
    var name = localStorage.getItem('safari_name');
    if(name) document.getElementById('fbName').value = name;
}

function closeFeedback(){
    document.getElementById('feedbackModal').classList.remove('show');
}

function setRating(r){
    feedbackRating = r;
    var stars = document.querySelectorAll('#starRating span');
    stars.forEach(function(s, i){
        if(i < r) s.classList.add('active');
        else s.classList.remove('active');
    });
}

async function submitFeedback(){
    var name = document.getElementById('fbName').value.trim();
    var email = document.getElementById('fbEmail').value.trim();
    var category = document.getElementById('fbCategory').value;
    var message = document.getElementById('fbMessage').value.trim();
    
    if(!name || !message){
        showToast('Please fill name and feedback message.');
        return;
    }
    
    var fd = new FormData();
    fd.append('name', name);
    fd.append('email', email || 'anonymous@user.com');
    fd.append('rating', feedbackRating);
    fd.append('category', category);
    fd.append('message', message);
    var token = localStorage.getItem('safari_token');
    if(token) fd.append('token', token);
    
    try{
        var r = await fetch('/api/v1/feedback/submit', {method:'POST', body:fd});
        var d = await r.json();
        if(d.status === 'success'){
            showToast('Feedback sent! Thank you! 🦁');
            closeFeedback();
            document.getElementById('fbMessage').value = '';
            document.getElementById('fbEmail').value = '';
            setRating(5);
        } else {
            showToast(d.detail || 'Could not send feedback.');
        }
    } catch(e){
        showToast('Error sending feedback.');
    }
}


// Close sidebar when clicking outside
document.addEventListener('click', function(e){
    var sidebar = document.querySelector('.sidebar');
    var hamburger = document.querySelector('.hamburger-btn');
    if(sidebar && sidebar.classList.contains('show')){
        if(!sidebar.contains(e.target) && !hamburger.contains(e.target)){
            sidebar.classList.remove('show');
        }
    }
});


// Register Service Worker for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js').then(function(reg) {
            console.log('Service Worker registered!', reg.scope);
        }).catch(function(err) {
            console.log('Service Worker registration failed:', err);
        });
    });
}


// Prevent Chrome from showing install badge automatically
let deferredPrompt;
window.addEventListener('beforeinstallprompt', function(e) {
    e.preventDefault();
    deferredPrompt = e;
});
