from fastapi import APIRouter, Depends, HTTPException
from app.db.session_db import SessionDB
from app.api.dependencies.auth import get_current_user

router = APIRouter()
session_db = SessionDB()

# GET: all sessions metadata for current user
@router.get("/")
def get_sessions_metadata(current_user: dict = Depends(get_current_user)):
    try:
        sessions = session_db.get_all_sessions_for_user(current_user["id"])

        metadata_only = [
            {
                "id": s["id"],
                "title": s["title"],
                "duration": s.get("duration"),
                "participants": s.get("participants", []),
                "created_at": s["created_at"],
                "updated_at": s["updated_at"],
                "transcript_status": s.get("transcript_status", "Pending"),
                "summary_status": s.get("summary_status", "Pending"),
                "emotion_breakdown_status": s.get("emotion_breakdown_status", "Pending"),
                "metadata_status": s.get("metadata_status", "Ready")
            }
            for s in sessions
        ]

        return metadata_only

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")

# GET: metadata for a specific session
@router.get("/{session_id}")
def get_session_metadata(session_id: str, current_user: dict = Depends(get_current_user)):
    try:
        session = session_db.get_session(session_id)

        # ❌ Session doesn't exist or not authorized
        if not session or session["user_id"] != current_user["id"]:
            raise HTTPException(status_code=404, detail="Session not found or access denied")

        metadata_status = session.get("metadata_status")

        if metadata_status != "completed":
            return {
                "status": metadata_status,
                "data": None
            }

        # ✅ Metadata is ready — return structured session info
        return {
            "status": "completed",
            "data": {
                "id": session["id"],
                "title": session["title"],
                "duration": session.get("duration"),
                "participants": session.get("participants", []),
                "created_at": session["created_at"],
                "updated_at": session["updated_at"],
                "audio_file_status": session.get("audio_file_status"),
                "transcript_status": session.get("transcript_status"),
                "summary_status": session.get("summary_status"),
                "emotion_breakdown_status": session.get("emotion_breakdown_status"),
                "metadata_status": metadata_status
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")