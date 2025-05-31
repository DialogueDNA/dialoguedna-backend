from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.api.dependencies.auth import get_current_user
from app.services.sessionDB import SessionDB
from app.utils.pdf import generate_session_pdf  # assumed to return a file path

router = APIRouter()
session_db = SessionDB()

# GET: text summary of a session
@router.get("/{session_id}")
def get_summary(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Summary not found or access denied")

    return {
        "status": session.get("summary_status"),
        "data": session.get("summary")
    }

# GET: download summary as PDF
@router.get("/{session_id}/download")
def download_summary_pdf(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    # You might also check summary_status here
    if not session.get("summary"):
        raise HTTPException(status_code=404, detail="Summary not yet generated")

    # Generate and serve the PDF
    pdf_path = generate_session_pdf(session)
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"session-{session_id}.pdf")
