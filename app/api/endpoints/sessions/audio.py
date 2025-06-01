from fastapi import APIRouter, Depends, HTTPException
from app.services.sessionDB import SessionDB
from app.services.sessionFetcher import SessionFetcher
from app.api.dependencies.auth import get_current_user

router = APIRouter()
session_db = SessionDB()
session_fetcher = SessionFetcher()

@router.get("/{session_id}")
def get_audio(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Audio not found or access denied")

    audio_status = session.get("audio_status")

    if audio_status != "completed":
        return {
            "status": audio_status,
            "data": None
        }

    try:
        audio_url = session_fetcher.get_audio(session_id)
        return {
            "status": "completed",
            "data": audio_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio URL: {str(e)}")
