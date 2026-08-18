let chats={};
let activeChat=null;
let isProcessing=false;
let pendingFile=null;
let guestRemaining=null;
let mediaRecorder=null;
let audioChunks=[];
let isRecording=false;
const GUEST_WARNING_THRESHOLD=5;

async function startRecording(){
    if(isRecording){
        stopRecording();
        return;
    }
    try{
        const stream=await navigator.mediaDevices.getUserMedia({audio:true});
        mediaRecorder=new MediaRecorder(stream);
        audioChunks=[];
        mediaRecorder.ondataavailable=function(e){audioChunks.push(e.data);};
        mediaRecorder.onstop=async function(){
            const audioBlob=new Blob(audioChunks,{type:'audio/wav'});
            const formData=new FormData();
            formData.append('audio',audioBlob,'recording.wav');
            showToast('Transcribing...');
            try{
                const r=await fetch('/api/v1/chat/transcribe',{method:'POST',body:formData});
                const d=await r.json();
                if(d.status==='success'){
                    document.getElementById('q').value=d.transcript;
                    showToast('Voice transcribed!');
                }else{
                    showToast('Transcription failed.');
                }
            }catch(e){
                showToast('Error transcribing.');
            }
            stream.getTracks().forEach(track=>track.stop());
        };
        mediaRecorder.start();
        isRecording=true;
        document.getElementById('micBtn').style.background='#ff6b6b';
        document.getElementById('micBtn').textContent='Stop';
        showToast('Recording... Click mic to stop.');
    }catch(e){
        showToast('Microphone not available.');
    }
}

function stopRecording(){
    if(mediaRecorder&&isRecording){
        mediaRecorder.stop();
        isRecording=false;
        document.getElementById('micBtn').style.background='#e8f5e9';
        document.getElementById('micBtn').textContent='Mic';
    }
}

function isLoggedIn(){return !!localStorage.getItem('safari_token');}

function showToast(msg){var t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(function(){t.classList.remove('show');},3000);}
async function fetchGuestStatus(){
    try{
        var r=await fetch('/api/v1/chat/guest-status');
        var d=await r.json();
        if(d.status==='success'){
            guestRemaining=d.remaining;
            updateUserUI();
        }
    }catch(e){}
}
function updateUserUI(){
    var token=localStorage.getItem('safari_token');
    var name=localStorage.getItem('safari_name');
    var guestBadge=document.getElementById('guestBadge');
    if(token&&name){
        document.getElementById('userName').textContent=name;
        document.getElementById('loginLink').style.display='none';
        document.getElementById('logoutBtn').style.display='inline-block';
        guestBadge.style.display='none';
    }else{
        document.getElementById('userName').textContent='';
        document.getElementById('loginLink').style.display='inline';
        document.getElementById('logoutBtn').style.display='none';
        if(guestRemaining!==null){
            guestBadge.textContent='Guest: '+guestRemaining+' queries left';
            guestBadge.style.display='inline-block';
            if(guestRemaining<=3){guestBadge.style.background='#d32f2f';}else{guestBadge.style.background='#ff9800';}
        }
    }
}
function logoutUser(){localStorage.removeItem('safari_token');localStorage.removeItem('safari_name');fetchGuestStatus();showToast('Logged out');}
function loadChats(){try{var saved=localStorage.getItem('safari_pro_chats');if(saved)chats=JSON.parse(saved);}catch(e){chats={};}if(!chats||Object.keys(chats).length===0){chats={};var id='chat_'+Date.now();chats[id]={name:'New Chat',messages:[],timestamps:[]};saveChats();}}
function saveChats(){try{localStorage.setItem('safari_pro_chats',JSON.stringify(chats));}catch(e){}}
function getChatPreview(messages){if(!messages||messages.length===0)return'New Chat';for(var i=0;i<messages.length;i++){if(messages[i].startsWith('U:'))return messages[i].substring(2).substring(0,30);}return'Chat';}
function renderTabs(){var tabs=document.getElementById('tabs');if(!tabs)return;tabs.innerHTML='';var chatIds=Object.keys(chats);chatIds.forEach(function(id){var chat=chats[id];if(!chat.name||chat.name==='New Chat'){chat.name=getChatPreview(chat.messages);}var tab=document.createElement('div');tab.className='tab'+(id===activeChat?' active':'');var nameSpan=document.createElement('span');nameSpan.className='tab-name';nameSpan.textContent=chat.name.length>20?chat.name.substring(0,20)+'...':chat.name;tab.appendChild(nameSpan);tab.addEventListener('click',function(e){if(e.target.classList.contains('del')||e.target.classList.contains('rename-btn'))return;switchChat(id);});if(chatIds.length>1){var renameBtn=document.createElement('span');renameBtn.className='rename-btn';renameBtn.textContent='R';renameBtn.title='Rename';renameBtn.addEventListener('click',function(e){e.stopPropagation();renameChatTab(id);});tab.appendChild(renameBtn);var del=document.createElement('span');del.className='del';del.textContent='x';del.title='Delete';del.addEventListener('click',function(e){e.stopPropagation();if(confirm('Delete this chat?')){deleteChat(id);}});tab.appendChild(del);}tabs.appendChild(tab);});var addBtn=document.createElement('div');addBtn.className='tab add';addBtn.textContent='+';addBtn.title='New Chat';addBtn.addEventListener('click',newChat);tabs.appendChild(addBtn);}
function renameChatTab(id){var chat=chats[id];var newName=prompt('Enter new name:',chat.name||'New Chat');if(newName&&newName.trim()){chat.name=newName.trim();saveChats();renderTabs();}}
function switchChat(id){activeChat=id;renderTabs();renderMessages();}
function newChat(){var chatIds=Object.keys(chats);for(var i=0;i<chatIds.length;i++){var c=chats[chatIds[i]];if(!c.messages||c.messages.length===0){activeChat=chatIds[i];renderTabs();renderMessages();return;}}var id='chat_'+Date.now();chats[id]={name:'New Chat',messages:[],timestamps:[]};activeChat=id;saveChats();renderTabs();renderMessages();}
function deleteChat(id){if(Object.keys(chats).length<=1){showToast('Cannot delete last chat');return;}delete chats[id];saveChats();if(activeChat===id){activeChat=Object.keys(chats)[0];}renderTabs();renderMessages();showToast('Chat deleted');}
function exportChat(){if(!activeChat||!chats[activeChat])return;var chat=chats[activeChat];var text='Safari AI Pro Chat Export\nDate: '+new Date().toLocaleString()+'\nChat: '+chat.name+'\n'+'='.repeat(50)+'\n\n';var msgs=chat.messages||[];var times=chat.timestamps||[];msgs.forEach(function(m,i){var time=times[i]?new Date(times[i]).toLocaleTimeString():'';if(m.startsWith('U:')){text+='You ('+time+'): '+m.substring(2)+'\n\n';}else if(m.startsWith('S:')){text+='Safari AI ('+time+'): '+m.substring(2)+'\n\n';}});var blob=new Blob([text],{type:'text/plain'});var url=URL.createObjectURL(blob);var a=document.createElement('a');a.href=url;a.download='safari-ai-pro-chat.txt';a.click();URL.revokeObjectURL(url);showToast('Chat exported!');}
function copyMessage(text,btn){navigator.clipboard.writeText(text).then(function(){btn.textContent='OK';setTimeout(function(){btn.textContent='C';},1500);showToast('Copied!');});}
function editMessage(index,msgDiv){var chat=chats[activeChat];var msg=chat.messages[index];var content=msg.substring(2);var editDiv=document.createElement('div');editDiv.className='m u';editDiv.style.width='75%';var input=document.createElement('textarea');input.className='edit-input';input.value=content;input.rows=Math.min(5,content.split('\n').length);editDiv.appendChild(input);var actions=document.createElement('div');actions.className='edit-actions';var saveBtn=document.createElement('button');saveBtn.className='btn-save';saveBtn.textContent='Save';saveBtn.onclick=function(){var newContent=input.value.trim();if(newContent){chat.messages=chat.messages.slice(0,index);chat.timestamps=chat.timestamps.slice(0,index);chat.messages.push('U:'+newContent);chat.timestamps.push(Date.now());saveChats();renderMessages();setProcessing(true);sendEditedMessage(newContent);}};var cancelBtn=document.createElement('button');cancelBtn.className='btn-cancel';cancelBtn.textContent='Cancel';cancelBtn.onclick=function(){renderMessages();};actions.appendChild(saveBtn);actions.appendChild(cancelBtn);editDiv.appendChild(actions);msgDiv.parentElement.replaceChild(editDiv,msgDiv);input.focus();}
async function sendEditedMessage(question){try{var form=new FormData();form.append('question',question);form.append('session_id',activeChat);var token=localStorage.getItem('safari_token');if(token)form.append('token',token);var r=await fetch('/api/v1/chat/ask',{method:'POST',body:form});var d=await r.json();var errMsg=d.response||d.detail||JSON.stringify(d);chats[activeChat].messages.push('S:'+errMsg);chats[activeChat].timestamps.push(Date.now());}catch(e){chats[activeChat].messages.push('S:Connection error: '+e.message);chats[activeChat].timestamps.push(Date.now());}saveChats();renderMessages();setProcessing(false);}
function addWarningToChat(remaining){var box=document.getElementById('b');var wrapper=document.createElement('div');wrapper.className='m-wrapper bot';wrapper.innerHTML='<div class="warning-msg">Warning: You have '+remaining+' free queries left. <a href="/login">Login now</a> for unlimited access.</div>';box.appendChild(wrapper);box.scrollTop=box.scrollHeight;if(!chats[activeChat])return;chats[activeChat].messages.push('W:'+remaining);chats[activeChat].timestamps.push(Date.now());saveChats();}
function renderMessages(){var box=document.getElementById('b');if(!box)return;box.innerHTML='';if(!activeChat||!chats[activeChat])return;var msgs=chats[activeChat].messages||[];var times=chats[activeChat].timestamps||[];if(msgs.length===0){box.innerHTML='<div class="m s" style="max-width:60%">&#x1F981; Hello! Ask me anything or attach a file!</div>';}msgs.forEach(function(m,i){var wrapper=document.createElement('div');if(m.startsWith('U:')){wrapper.className='m-wrapper user';var msgDiv=document.createElement('div');msgDiv.className='m u';msgDiv.textContent=m.substring(2);wrapper.appendChild(msgDiv);var actions=document.createElement('div');actions.className='msg-actions';var editBtn=document.createElement('button');editBtn.className='msg-action-btn btn-edit';editBtn.textContent='E';editBtn.title='Edit';editBtn.onclick=function(){editMessage(i,msgDiv);};actions.appendChild(editBtn);wrapper.appendChild(actions);}else if(m.startsWith('S:')){wrapper.className='m-wrapper bot';var msgDiv2=document.createElement('div');msgDiv2.className='m s';msgDiv2.textContent=m.substring(2);wrapper.appendChild(msgDiv2);var actions2=document.createElement('div');actions2.className='msg-actions';var copyBtn=document.createElement('button');copyBtn.className='msg-action-btn btn-copy';copyBtn.textContent='C';copyBtn.title='Copy';copyBtn.onclick=function(){copyMessage(m.substring(2),copyBtn);};actions2.appendChild(copyBtn);wrapper.appendChild(actions2);}else if(m.startsWith('W:')){wrapper.className='m-wrapper bot';wrapper.innerHTML='<div class="warning-msg">Warning: You have '+m.substring(2)+' free queries left. <a href="/login">Login now</a> for unlimited access.</div>';}if(times[i]){var timeStamp=document.createElement('div');timeStamp.className='time-stamp';timeStamp.textContent=new Date(times[i]).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});wrapper.appendChild(timeStamp);}box.appendChild(wrapper);});box.scrollTop=box.scrollHeight;}
function setProcessing(state){isProcessing=state;var btn=document.getElementById('askBtn');var typing=document.getElementById('typing');if(state){btn.disabled=true;btn.textContent='Thinking...';typing.classList.add('show');}else{btn.disabled=false;btn.textContent='Ask';typing.classList.remove('show');}}
async function ask(){
    if(isProcessing)return;
    var input=document.getElementById('q');
    var question=input.value.trim();
    if(!question&&!pendingFile)return;
    if(question.length>2000){showToast('Message too long.');return;}
    if(!activeChat||!chats[activeChat])newChat();
    if(!chats[activeChat].messages)chats[activeChat].messages=[];
    if(!chats[activeChat].timestamps)chats[activeChat].timestamps=[];
    var displayText=question;
    if(pendingFile){displayText=question?question+' [Attached: '+pendingFile.name+']':'[Attached: '+pendingFile.name+']';}
    chats[activeChat].messages.push('U:'+displayText);
    chats[activeChat].timestamps.push(Date.now());
    saveChats();
    renderTabs();
    renderMessages();
    input.value='';
    var preview=document.getElementById('filePreview');
    preview.style.display='none';
    setProcessing(true);
    try{
        if(pendingFile){
            var uploadForm=new FormData();
            uploadForm.append('session_id',activeChat);
            uploadForm.append('file',pendingFile);
            var uploadResp=await fetch('/api/v1/upload/',{method:'POST',body:uploadForm});
            var uploadData=await uploadResp.json();
            if(uploadData.status==='success'){
                var askForm=new FormData();
                askForm.append('session_id',activeChat);
                askForm.append('question',question||'Please analyze the attached file');
                var token=localStorage.getItem('safari_token');
                if(token)askForm.append('token',token);
                var askResp=await fetch('/api/v1/chat/ask',{method:'POST',body:askForm});
                var askData=await askResp.json();
                var errMsg2=askData.response||askData.detail||JSON.stringify(askData);
                chats[activeChat].messages.push('S:'+errMsg2);
                chats[activeChat].timestamps.push(Date.now());
                if(askData.guest_remaining!==undefined&&askData.guest_remaining!==null){
                    guestRemaining=askData.guest_remaining;
                    updateUserUI();
                    if(guestRemaining<=3&&guestRemaining>0){addWarningToChat(guestRemaining);}
                }
            }else{
                chats[activeChat].messages.push('S:'+(uploadData.detail||uploadData.message||'Upload failed.'));
                chats[activeChat].timestamps.push(Date.now());
            }
            pendingFile=null;
        }else{
            var form=new FormData();
            form.append('question',question);
            form.append('session_id',activeChat);
            var token=localStorage.getItem('safari_token');
            if(token)form.append('token',token);
            var r=await fetch('/api/v1/chat/ask',{method:'POST',body:form});
            var d=await r.json();
            var errMsg3=d.response||d.detail||JSON.stringify(d);
            chats[activeChat].messages.push('S:'+errMsg3);
            chats[activeChat].timestamps.push(Date.now());
            if(d.guest_remaining!==undefined&&d.guest_remaining!==null){
                guestRemaining=d.guest_remaining;
                updateUserUI();
                if(guestRemaining<=3&&guestRemaining>0){addWarningToChat(guestRemaining);}
                if(guestRemaining===0){showToast('Free limit reached.');setTimeout(function(){window.location.href='/login';},2000);}
            }
        }
    }catch(e){
        chats[activeChat].messages.push('S:Connection error: '+e.message);
        chats[activeChat].timestamps.push(Date.now());
    }
    saveChats();
    renderMessages();
    setProcessing(false);
}
function selectFile(input){var file=input.files[0];if(!file)return;if(file.size>2*1024*1024){showToast('File too large. Max 2MB.');input.value='';return;}pendingFile=file;var preview=document.getElementById('filePreview');document.getElementById('fileName').textContent=file.name;preview.style.display='flex';showToast('File ready. Type question and Ask.');}
function clearAttachment(){pendingFile=null;var input=document.getElementById('fileInput');input.value='';document.getElementById('filePreview').style.display='none';showToast('Attachment removed.');}
document.addEventListener('DOMContentLoaded',function(){fetchGuestStatus();loadChats();var chatIds=Object.keys(chats);var existingEmpty=null;for(var i=0;i<chatIds.length;i++){var c=chats[chatIds[i]];if(!c.messages||c.messages.length===0){existingEmpty=chatIds[i];break;}}if(existingEmpty){activeChat=existingEmpty;}else{activeChat='chat_'+Date.now();chats[activeChat]={name:'New Chat',messages:[],timestamps:[]};saveChats();}renderTabs();renderMessages();});
