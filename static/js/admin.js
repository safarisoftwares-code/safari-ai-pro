function openReply(id) {
    document.getElementById('replyFeedbackId').value = id;
    document.getElementById('replyModal').style.display = 'flex';
}
function closeReply() {
    document.getElementById('replyModal').style.display = 'none';
    document.getElementById('replyMessage').value = '';
}
async function sendReply() {
    var id = document.getElementById('replyFeedbackId').value;
    var reply = document.getElementById('replyMessage').value.trim();
    if(!reply) { alert('Type a reply first.'); return; }
    var pw = new URLSearchParams(window.location.search).get('pw');
    var fd = new FormData();
    fd.append('feedback_id', id);
    fd.append('reply', reply);
    fd.append('pw', pw);
    var r = await fetch('/api/v1/feedback/reply', {method:'POST', body:fd});
    var d = await r.json();
    alert(d.message || 'Done!');
    window.location.reload();
}
