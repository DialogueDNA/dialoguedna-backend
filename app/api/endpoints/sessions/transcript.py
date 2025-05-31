from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies.auth import get_current_user
from app.services.sessionDB import SessionDB

router = APIRouter()
session_db = SessionDB()

@router.get("/{session_id}")
def get_transcript(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Transcript not found or access denied")

    return {
        "status": session.get("transcript_status", "Ready"),
        "data": {
            "transcript": session.get("transcript")
        }
    }
