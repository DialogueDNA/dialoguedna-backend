from fastapi import APIRouter, Depends, HTTPException
from app.db.session_db import SessionDB
from app.storage.session_storage import SessionStorage
from app.api.dependencies.auth import get_current_user

router = APIRouter()
session_db = SessionDB()
session_storage = SessionStorage()

@router.get("/{session_id}")
def get_audio(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Audio not found or access denied")

    audio_status = session.get("audio_file_status")
    audio_blob_path = session.get("audio_file_url")

    if audio_status != "completed" or not audio_blob_path:
        return {
            "status": audio_status,
            "data": None
        }

    try:
        audio_url = session_storage.generate_sas_url(audio_blob_path)
        return {
            "status": "completed",
            "data": audio_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio URL: {str(e)}")