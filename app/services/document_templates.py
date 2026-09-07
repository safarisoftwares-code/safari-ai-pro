# ============================================
# BEAUTIFUL DOCUMENT TEMPLATES FOR SAFARI AI
# ============================================

CERTIFICATE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
<style>
body{{font-family:Georgia,serif;background:#f5e6d3;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}}
.cert{{background:#fff;max-width:700px;padding:50px;border:3px solid #8b4513;border-radius:10px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.15);position:relative}}
h1{{color:#8b4513;font-size:28px;letter-spacing:2px}}
.name{{color:#d2691e;font-size:40px;font-weight:bold;margin:20px 0;font-family:Georgia,serif}}
.achievement{{color:#555;font-size:16px;line-height:1.7}}
.stamp{{position:absolute;top:30%;right:40px;transform:rotate(-15deg);border:3px solid #d32f2f;border-radius:50%;width:100px;height:100px;display:flex;align-items:center;justify-content:center;color:#d32f2f;font-size:10px;font-weight:bold;opacity:.5}}
.sign-section{{display:flex;justify-content:space-between;margin-top:40px}}
.sign-line{{border-bottom:2px solid #333;width:180px;font-family:'Brush Script MT',cursive;font-size:20px}}
</style>
</head>
<body>
<div class="cert">
<div class="stamp">SAFARI<br>SOFTWARES<br>SEAL</div>
<h1>CERTIFICATE OF ACHIEVEMENT</h1>
<p>This certifies that</p>
<div class="name">{{name}}</div>
<p class="achievement">{{achievement}}</p>
<p>Issued on {{date}}</p>
<div class="sign-section">
<div><div class="sign-line">Safari Softwares</div><p>Authorized Signature</p></div>
<div><div class="sign-line">{{name}}</div><p>Recipient</p></div>
</div>
</div>
</body>
</html>
'''

RECOMMENDATION_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
<style>
body{{font-family:Georgia,serif;background:#f5e6d3;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}}
.letter{{background:#fff;max-width:650px;padding:50px;border:2px solid #8b4513;border-radius:10px;box-shadow:0 20px 60px rgba(0,0,0,.15)}}
h1{{color:#8b4513;font-size:24px;text-align:center;margin-bottom:20px}}
.sender{{font-size:14px;color:#555;line-height:1.5}}
.body-text{{font-size:14px;color:#333;line-height:1.8;text-align:justify}}
.sign{{margin-top:40px}}
</style>
</head>
<body>
<div class="letter">
<h1>RECOMMENDATION LETTER</h1>
<div class="sender">
<strong>{{your_name}}</strong><br>
{{your_position}}<br>
{{organization}}<br>
Nairobi, Kenya
</div>
<p>{{date}}</p>
<p>To Whom It May Concern,</p>
<div class="body-text">
<p>I am delighted to recommend <strong>{{candidate_name}}</strong> who served as {{candidate_position}} at {{organization}} from {{duration}}.</p>
<p>Their notable achievement was {{achievement}}.</p>
<p>I wholeheartedly recommend {{candidate_name}} without reservation.</p>
</div>
<div class="sign">
<p>Sincerely,</p>
<p><strong>{{your_name}}</strong><br>{{your_position}}</p>
</div>
</div>
</body>
</html>
'''