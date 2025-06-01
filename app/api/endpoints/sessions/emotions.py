from fastapi import APIRouter, Depends, HTTPException
from app.services.sessionDB import SessionDB
from app.services.sessionFetcher import SessionFetcher
from app.api.dependencies.auth import get_current_user

router = APIRouter()
session_db = SessionDB()
session_fetcher = SessionFetcher()

@router.get("/{session_id}")
def get_emotions(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Emotions not found or access denied")

    emotions_status = session.get("emotions_status")

    if emotions_status != "completed":
        return {
            "status": emotions_status,
            "data": None
        }

    try:
        emotions = session_fetcher.get_emotions(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emotions: {str(e)}")

    return {
        "status": "completed",
        "data": emotions
    }
