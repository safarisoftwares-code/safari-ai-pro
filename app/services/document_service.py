from datetime import datetime

class DocumentService:
    
    @staticmethod
    def generate_certificate(name, achievement, date=None, quote="", issuer="Safari Softwares"):
        if not date:
            date = datetime.now().strftime("%B %d, %Y")
        
        return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Certificate - {name}</title>
<style>
body{{font-family:Georgia,serif;background:#f5e6d3;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px;margin:0}}
.cert{{background:#fff;max-width:700px;padding:50px;border:3px solid #8b4513;border-radius:10px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.15);position:relative}}
h1{{color:#8b4513;font-size:28px;letter-spacing:2px;margin-bottom:10px}}
.subtitle{{color:#888;font-size:14px;margin-bottom:20px}}
.name{{color:#d2691e;font-size:42px;font-weight:bold;margin:20px 0;font-family:Georgia,serif}}
.achievement{{color:#555;font-size:16px;line-height:1.7;margin:15px 0}}
.date{{color:#555;font-size:14px;margin-top:20px}}
.quote{{font-style:italic;color:#888;margin:20px 0;padding:15px;border-left:4px solid #8b4513;background:#faf5f0;border-radius:0 8px 8px 0;text-align:left}}
.sign-section{{display:flex;justify-content:space-between;margin-top:40px;padding:0 20px}}
.sign-box{{text-align:center}}
.sign-line{{border-bottom:2px solid #333;width:180px;margin-bottom:5px;font-family:'Brush Script MT',cursive;font-size:20px;color:#555;padding-bottom:2px}}
.sign-label{{font-size:11px;color:#888}}
.stamp{{position:absolute;top:30%;right:40px;transform:rotate(-15deg);border:3px solid #d32f2f;border-radius:50%;width:100px;height:100px;display:flex;align-items:center;justify-content:center;color:#d32f2f;font-size:10px;font-weight:bold;opacity:.5;line-height:1.3}}
.download-btn{{display:inline-block;margin-top:30px;padding:12px 24px;background:#d2691e;color:#fff;border:none;border-radius:25px;cursor:pointer;font-weight:bold;font-size:14px;text-decoration:none}}
@media print{{body{{background:#fff}}.download-btn{{display:none}}}}
</style>
</head>
<body>
<div class="cert">
<div class="stamp">SAFARI<br>SOFTWARES<br>★<br>SEAL</div>
<h1>CERTIFICATE OF ACHIEVEMENT</h1>
<p class="subtitle">This certifies that</p>
<div class="name">{name}</div>
<p class="achievement">{achievement}</p>
<p class="date">Issued on {date}</p>
{'<div class="quote">' + quote + '</div>' if quote else ''}
<p class="date">Issued by: {issuer}</p>
<div class="sign-section">
<div class="sign-box">
<div class="sign-line">{issuer}</div>
<div class="sign-label">Authorized Signature</div>
</div>
<div class="sign-box">
<div class="sign-line">{name}</div>
<div class="sign-label">Recipient</div>
</div>
</div>
<a href="/" style="display:inline-block;margin-top:20px;margin-right:10px;padding:10px 20px;background:#f0e0d0;color:#8b4513;border:none;border-radius:25px;cursor:pointer;font-weight:bold;font-size:13px;text-decoration:none">← Back to Chat</a> <a href="#" class="download-btn" onclick="window.print()">Download PDF / Print</a>
</div>
</body>
</html>'''

    @staticmethod
    def generate_recommendation(your_name, your_position, candidate_name, candidate_position, organization, duration, achievement, gender="their", location="Nairobi, Kenya"):
        date = datetime.now().strftime("%B %d, %Y")
        
        return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Recommendation - {candidate_name}</title>
<style>
body{{font-family:Georgia,serif;background:#f5e6d3;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px;margin:0}}
.letter{{background:#fff;max-width:650px;padding:50px;border:2px solid #8b4513;border-radius:10px;box-shadow:0 20px 60px rgba(0,0,0,.15)}}
h1{{color:#8b4513;font-size:24px;text-align:center;margin-bottom:20px;letter-spacing:2px}}
.sender{{font-size:14px;color:#555;line-height:1.5;margin-bottom:20px}}
.date{{font-size:13px;color:#555;margin-bottom:20px}}
.salutation{{font-size:14px;color:#333;margin-bottom:20px}}
.body-text{{font-size:14px;color:#333;line-height:1.8;text-align:justify}}
.body-text p{{margin-bottom:15px}}
.sign{{margin-top:40px;font-size:14px;color:#333}}
.download-btn{{display:inline-block;margin-top:30px;padding:12px 24px;background:#d2691e;color:#fff;border:none;border-radius:25px;cursor:pointer;font-weight:bold;font-size:14px;text-decoration:none}}
@media print{{body{{background:#fff}}.download-btn{{display:none}}}}
</style>
</head>
<body>
<div class="letter">
<h1>RECOMMENDATION LETTER</h1>
<div class="sender">
<strong>For: {candidate_name}</strong><br>
Position: {candidate_position}<br>
Organization: {organization}<br><br>
Nairobi, Kenya
</div>
<p class="date">{date}</p>
<p class="salutation">To Whom It May Concern,</p>
<div class="body-text">
<p>I am delighted to write this recommendation for <strong>{candidate_name}</strong>, who served as <strong>{candidate_position}</strong> at <strong>{organization}</strong> from <strong>{duration}</strong>.</p>
<p>During {gender} time with us, {candidate_name} consistently demonstrated exceptional professionalism, technical expertise, and dedication. {gender.capitalize()} most notable achievement was {achievement}.</p>
<p>{candidate_name} possesses strong problem-solving skills, works well in teams, and shows remarkable initiative. They would be a valuable asset to any organization.</p>
<p>I wholeheartedly recommend {candidate_name} without reservation. Please feel free to contact me if you need any further information.</p>
</div>
<div class="sign">
<p>Sincerely,</p>
<p style="margin-top:30px"><strong>{your_name}</strong><br>{your_position}<br>{organization}</p>
</div>
<a href="/" style="display:inline-block;margin-top:20px;margin-right:10px;padding:10px 20px;background:#f0e0d0;color:#8b4513;border:none;border-radius:25px;cursor:pointer;font-weight:bold;font-size:13px;text-decoration:none">← Back to Chat</a> <a href="#" class="download-btn" onclick="window.print()">Download PDF / Print</a>
</div>
</body>
</html>'''

    @staticmethod
    def generate_proposal(client_name, service, details):
        date = datetime.now().strftime("%B %d, %Y")
        
        return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Proposal - {client_name}</title>
<style>
body{{font-family:'Segoe UI',sans-serif;background:#f5e6d3;padding:20px;margin:0}}
.proposal{{background:#fff;max-width:800px;margin:auto;padding:40px;border-radius:10px;box-shadow:0 20px 60px rgba(0,0,0,.15)}}
h1{{color:#8b4513;font-size:26px;border-bottom:3px solid #d2691e;padding-bottom:10px}}
h2{{color:#d2691e;font-size:18px;margin-top:25px}}
p{{color:#333;font-size:14px;line-height:1.7}}
.highlight{{background:#faf5f0;border-left:4px solid #d2691e;padding:12px;margin:15px 0}}
.download-btn{{display:inline-block;margin-top:30px;padding:12px 24px;background:#d2691e;color:#fff;border:none;border-radius:25px;cursor:pointer;font-weight:bold;font-size:14px}}
@media print{{body{{background:#fff}}.download-btn{{display:none}}}}
</style>
</head>
<body>
<div class="proposal">
<h1>BUSINESS PROPOSAL</h1>
<p><strong>Prepared for:</strong> {client_name}</p>
<p><strong>Date:</strong> {date}</p>
<p><strong>Service:</strong> {service}</p>
<h2>Executive Summary</h2>
<p>{details}</p>
<h2>Our Approach</h2>
<p>Safari Softwares delivers custom software solutions tailored to your needs. Our proven methodology ensures timely delivery and measurable results.</p>
<h2>Pricing</h2>
<div class="highlight">Contact us for a detailed quote tailored to your requirements.</div>
<h2>Next Steps</h2>
<p>We would be happy to schedule a discovery call to discuss your project in detail.</p>
<a href="/" style="display:inline-block;margin-top:20px;margin-right:10px;padding:10px 20px;background:#f0e0d0;color:#8b4513;border:none;border-radius:25px;cursor:pointer;font-weight:bold;font-size:13px;text-decoration:none">← Back to Chat</a> <a href="#" class="download-btn" onclick="window.print()">Download PDF / Print</a>
</div>
</body>
</html>'''
    @staticmethod
    def generate_proposal_robust(client_name, client_company, project_title, executive_summary, problem_statement, solution, scope, timeline_start, timeline_end, budget, currency, payment_terms, validity, contact_email, contact_phone, provider_name="", provider_company="", provider_email="", provider_phone=""):
        date = datetime.now().strftime("%B %d, %Y")
        
        return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Proposal - {project_title}</title>
<style>
body{{font-family:'Segoe UI',sans-serif;background:#f5e6d3;padding:20px;margin:0}}
.proposal{{background:#fff;max-width:800px;margin:auto;padding:40px;border-radius:10px;box-shadow:0 20px 60px rgba(0,0,0,.15)}}
h1{{color:#8b4513;font-size:26px;border-bottom:3px solid #d2691e;padding-bottom:10px}}
h2{{color:#d2691e;font-size:18px;margin-top:25px}}
p{{color:#333;font-size:14px;line-height:1.7}}
table{{width:100%;border-collapse:collapse;margin:15px 0;font-size:13px}}
th{{background:#d2691e;color:#fff;padding:10px;text-align:left}}
td{{padding:8px;border-bottom:1px solid #e0c8a8}}
.highlight{{background:#faf5f0;border-left:4px solid #d2691e;padding:12px;margin:15px 0}}
.download-btn{{display:inline-block;margin-top:30px;padding:12px 24px;background:#d2691e;color:#fff;border:none;border-radius:25px;cursor:pointer;font-weight:bold;font-size:14px}}
@media print{{body{{background:#fff}}.download-btn{{display:none}}}}
</style>
</head>
<body>
<div class="proposal">
<h1>BUSINESS PROPOSAL</h1>
<p><strong>Project:</strong> {project_title}</p>
<p><strong>Prepared By:</strong> {provider_name}, {provider_company}<br><strong>Prepared For:</strong> {client_name}, {client_company}</p>
<p><strong>Date:</strong> {date}</p>

<h2>1. Executive Summary</h2>
<p>{executive_summary}</p>

<h2>2. Problem Statement</h2>
<p>{problem_statement}</p>

<h2>3. Proposed Solution</h2>
<p>{solution}</p>

<h2>4. Scope of Work</h2>
<p>{scope}</p>

<h2>5. Timeline</h2>
<table>
<tr><th>Phase</th><th>Date</th></tr>
<tr><td>Start Date</td><td>{timeline_start}</td></tr>
<tr><td>End Date</td><td>{timeline_end}</td></tr>
</table>

<h2>6. Investment</h2>
<div class="highlight">
<p><strong>Total Budget:</strong> {currency} {budget}</p>
<p><strong>Payment Terms:</strong> {payment_terms}</p>
<p><strong>Proposal Validity:</strong> {validity} days</p>
</div>

<h2>7. Next Steps</h2>
<p>We would be happy to schedule a discovery call to discuss this proposal in detail.</p>

<h2>8. Contact</h2>
<p><strong>Provider:</strong> {provider_name} - {provider_email} | {provider_phone}</p>
<p><strong>Client:</strong> {client_name} - {contact_email} | {contact_phone}</p>

<a href="/" style="display:inline-block;margin-top:20px;margin-right:10px;padding:10px 20px;background:#f0e0d0;color:#8b4513;border:none;border-radius:25px;cursor:pointer;font-weight:bold;font-size:13px;text-decoration:none">← Back to Chat</a> <a href="#" class="download-btn" onclick="window.print()">Download PDF / Print</a>
</div>
</body>
</html>'''
