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
    location: str = Form(default="Nairobi, Kenya")
):
    if doc_type == "certificate":
        return HTMLResponse(DocumentService.generate_certificate(name, achievement, date, quote))
    elif doc_type == "recommendation":
        return HTMLResponse(DocumentService.generate_recommendation(your_name, your_position, candidate_name, candidate_position, organization, duration, achievement, gender, location))
    elif doc_type == "proposal":
        return HTMLResponse(DocumentService.generate_proposal(name, "Custom Service", details))
    else:
        return HTMLResponse("<h2>Unknown document type</h2>")