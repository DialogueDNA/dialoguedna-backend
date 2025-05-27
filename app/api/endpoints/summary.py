from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.core.config import supabase
from app.api.dependencies.auth import get_current_user
from app.utils.pdf import generate_session_pdf  # You must implement this

router = APIRouter()

# GET: text summary of a session
@router.get("/{session_id}")
def get_summary(session_id: str, current_user: dict = Depends(get_current_user)):
    session = supabase.table("sessions").select("summary").eq("id", session_id).eq("user_id", current_user["id"]).single().execute()

    if not session.data:
        raise HTTPException(status_code=404, detail="Summary not found")

    return {"summary": session.data["summary"]}

# GET: download summary as PDF
@router.get("/{session_id}/download")
def download_summary_pdf(session_id: str, current_user: dict = Depends(get_current_user)):
    session = supabase.table("sessions").select("*").eq("id", session_id).eq("user_id", current_user["id"]).single().execute()

    if not session.data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Generate and serve the PDF
    pdf_path = generate_session_pdf(session.data)
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"session-{session_id}.pdf")
