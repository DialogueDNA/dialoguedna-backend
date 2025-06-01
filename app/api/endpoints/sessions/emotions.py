from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies.auth import get_current_user
from app.services.infrastructure.sessionDB import SessionDB

router = APIRouter()
session_db = SessionDB()

@router.get("/{session_id}")
def get_emotions(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Emotion data not found or access denied")

    return {
        "status": session.get("emotion_breakdown_status"),
        "data": session.get("emotion_breakdown")
    }
