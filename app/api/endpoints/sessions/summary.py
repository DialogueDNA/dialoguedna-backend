from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.services.sessionDB import SessionDB
from app.services.sessionFetcher import SessionFetcher
from app.utils.pdf import generate_session_pdf
from app.api.dependencies.auth import get_current_user

router = APIRouter()
session_db = SessionDB()
session_fetcher = SessionFetcher()

# GET: text summary of a session
@router.get("/{session_id}")
def get_summary(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Summary not found or access denied")

    summary_status = session.get("summary_status")

    if summary_status != "completed":
        return {
            "status": summary_status,
            "data": None
        }

    try:
        summary = session_fetcher.get_summary(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")

    return {
        "status": "completed",
        "data": summary
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
