from fastapi import APIRouter, Depends, HTTPException
from app.db.session_db import SessionDB
from app.storage.session_storage import SessionStorage
from app.api.dependencies.auth import get_current_user

router = APIRouter()
session_db = SessionDB()
session_storage = SessionStorage()

@router.get("/{session_id}")
def get_emotions(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Emotions not found or access denied")

    emotions_status = session.get("emotion_breakdown_status")
    emotions_blob = session.get("emotion_breakdown_url")

    if emotions_status != "completed" or not emotions_blob:
        return {
            "status": emotions_status,
            "data": None
        }

    try:
        emotions_url = session_storage.generate_sas_url(emotions_blob)
        return {
            "status": "completed",
            "data": emotions_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emotions: {str(e)}")