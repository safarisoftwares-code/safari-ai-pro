// File Preview Module - shows 20 lines with dropdown
function showFilePreview(file) {
    var reader = new FileReader();
    reader.onload = function(e) {
        var text = e.target.result;
        var lines = text.split('\n');
        var previewLines = lines.slice(0, 20).join('\n');
        var hiddenLines = lines.slice(20).join('\n');
        
        var previewBox = document.createElement('div');
        previewBox.style.cssText = 'position:fixed;bottom:60px;left:10px;right:10px;background:#fff;border:2px solid #d2691e;border-radius:10px;padding:10px;max-height:250px;overflow-y:auto;z-index:100;font-size:11px;box-shadow:0 5px 20px rgba(0,0,0,.3)';
        
        previewBox.innerHTML = '<div style="display:flex;justify-content:space-between;margin-bottom:5px"><strong style="color:#8b4513">' + file.name + '</strong><span style="color:#888;font-size:10px">' + lines.length + ' lines</span></div>';
        
        var content = document.createElement('pre');
        content.style.cssText = 'margin:0;white-space:pre-wrap;font-size:11px;color:#333;max-height:120px;overflow-y:auto';
        content.textContent = previewLines;
        previewBox.appendChild(content);
        
        if(hiddenLines.trim().length > 0) {
            var btn = document.createElement('button');
            btn.textContent = '▼ Show all ' + lines.length + ' lines';
            btn.style.cssText = 'width:100%;padding:8px;background:#f0e0d0;color:#8b4513;border:none;border-radius:5px;cursor:pointer;font-weight:bold;font-size:11px;margin-top:5px';
            btn.onclick = function() {
                if(btn.textContent.indexOf('▼') === 0) {
                    content.textContent = previewLines + '\n' + hiddenLines;
                    btn.textContent = '▲ Show first 20 lines';
                } else {
                    content.textContent = previewLines;
                    btn.textContent = '▼ Show all ' + lines.length + ' lines';
                }
            };
            previewBox.appendChild(btn);
        }
        
        var closeBtn = document.createElement('button');
        closeBtn.textContent = '✕ Close';
        closeBtn.style.cssText = 'width:100%;padding:6px;background:#d32f2f;color:#fff;border:none;border-radius:5px;cursor:pointer;font-weight:bold;font-size:10px;margin-top:5px';
        closeBtn.onclick = function(){previewBox.remove();};
        previewBox.appendChild(closeBtn);
        
        document.body.appendChild(previewBox);
    };
    reader.readAsText(file);
}