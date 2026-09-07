from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

@router.get("/form", response_class=HTMLResponse)
async def document_form():
    return FileResponse("templates/document_form.html")

@router.post("/generate", response_class=HTMLResponse)
async def generate_document(
    doc_type: str = Form(...),
    name: str = Form(default=""),
    your_name: str = Form(default=""),
    your_position: str = Form(default=""),
    candidate_name: str = Form(default=""),
    candidate_position: str = Form(default=""),
    organization: str = Form(default="Safari Softwares"),
    duration: str = Form(default=""),
    achievement: str = Form(default=""),
    date: str = Form(default=""),
    quote: str = Form(default=""),
    details: str = Form(default=""),
    gender: str = Form(default="their"),
    location: str = Form(default="Nairobi, Kenya"),
    client_name: str = Form(default=""),
    client_company: str = Form(default=""),
    project_title: str = Form(default=""),
    executive_summary: str = Form(default=""),
    problem_statement: str = Form(default=""),
    solution: str = Form(default=""),
    scope: str = Form(default=""),
    timeline_start: str = Form(default=""),
    timeline_end: str = Form(default=""),
    budget: str = Form(default=""),
    currency: str = Form(default="KSh"),
    payment_terms: str = Form(default=""),
    validity: str = Form(default="30"),
    contact_email: str = Form(default=""),
    contact_phone: str = Form(default=""),
    provider_name: str = Form(default=""),
    provider_company: str = Form(default=""),
    provider_email: str = Form(default=""),
    provider_phone: str = Form(default="")
):
    if doc_type == "certificate":
        return HTMLResponse(DocumentService.generate_certificate(name, achievement, date, quote))
    elif doc_type == "recommendation":
        return HTMLResponse(DocumentService.generate_recommendation(your_name, your_position, candidate_name, candidate_position, organization, duration, achievement, gender, location))
    elif doc_type == "proposal":
        return HTMLResponse(DocumentService.generate_proposal_robust(client_name, client_company, project_title, executive_summary, problem_statement, solution, scope, timeline_start, timeline_end, budget, currency, payment_terms, validity, contact_email, contact_phone, provider_name, provider_company, provider_email, provider_phone))
    else:
        return HTMLResponse("<h2>Unknown document type</h2>")