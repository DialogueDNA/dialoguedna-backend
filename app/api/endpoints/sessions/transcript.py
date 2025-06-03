from fastapi import APIRouter, Depends, HTTPException
from app.db.session_db import SessionDB
from app.storage.session_storage import SessionStorage
from app.api.dependencies.auth import get_current_user
import requests

router = APIRouter()
session_db = SessionDB()
session_storage = SessionStorage()

@router.get("/{session_id}")
def get_transcript(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Transcript not found or access denied")

    transcript_status = session.get("transcript_status")
    transcript_blob = session.get("transcript_url")

    if transcript_status != "completed" or not transcript_blob:
        return {
            "status": transcript_status,
            "data": None
        }

    try:
        transcript_url = session_storage.generate_sas_url(transcript_blob)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transcript: {str(e)}")

    return {
        "status": "completed",
        "data": transcript_url
    }