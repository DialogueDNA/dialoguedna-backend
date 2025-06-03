from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.db.session_db import SessionDB
from app.storage.session_storage import SessionStorage
from app.utils.pdf import generate_session_pdf
from app.api.dependencies.auth import get_current_user
import requests

router = APIRouter()
session_db = SessionDB()
session_storage = SessionStorage()

# GET: text summary of a session
@router.get("/{session_id}")
def get_summary(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Summary not found or access denied")

    summary_status = session.get("summary_status")
    summary_blob = session.get("summary_url")

    if summary_status != "completed" or not summary_blob:
        return {
            "status": summary_status,
            "data": None
        }

    try:
        summary_url = session_storage.generate_sas_url(summary_blob)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")

    return {
        "status": "completed",
        "data": summary_url
    }

# GET: download summary as PDF
@router.get("/{session_id}/download")
def download_summary_pdf(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    summary_blob = session.get("summary_url")
    if not summary_blob:
        raise HTTPException(status_code=404, detail="Summary not yet generated")

    try:
        summary_url = session_storage.generate_sas_url(summary_blob)
        summary_text = requests.get(summary_url).text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")

    # Use the session metadata and summary text to generate the PDF
    pdf_path = generate_session_pdf({
        "title": session.get("title"),
        "created_at": session.get("created_at"),
        "duration": session.get("duration"),
        "participants": session.get("participants"),
        "summary": summary_text
    })

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"session-{session_id}.pdf")