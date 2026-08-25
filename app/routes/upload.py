from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from app.services.file_service import FileService

router = APIRouter(prefix="/api/v1/upload", tags=["upload"])
uploaded_documents = {}

@router.post("/")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(default="default")):
    content = await file.read()
    
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 10MB.")
    
    text = FileService.extract_text(file.filename, content)
    
    if not text:
        return {"status": "error", "message": "Could not read this file. Please try a different file."}
    
    uploaded_documents[session_id] = {"filename": file.filename, "content": text}
    
    return {
        "status": "success",
        "filename": file.filename,
        "preview": text[:300],
        "message": "File attached!"
    }
