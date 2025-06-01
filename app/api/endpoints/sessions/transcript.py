from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies.auth import get_current_user
from app.services.sessionDB import SessionDB
from app.services.sessionFetcher import SessionFetcher  # Adjust import path if needed

router = APIRouter()
session_db = SessionDB()
session_fetcher = SessionFetcher()

@router.get("/{session_id}")
def get_transcript(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    # ❌ Session not found or unauthorized
    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Transcript not found or access denied")

    transcript_status = session.get("transcript_status")

    if transcript_status != "completed":
        return {
            "status": transcript_status,
            "data": None
        }

    # ✅ Transcript is ready — fetch from Azure
    try:
        transcript = session_fetcher.get_transcript(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transcript: {str(e)}")

    return {
        "status": "completed",
        "data": transcript
    }
