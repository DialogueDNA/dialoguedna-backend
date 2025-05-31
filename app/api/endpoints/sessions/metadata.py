from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies.auth import get_current_user
from app.services.sessionDB import SessionDB

router = APIRouter()
session_db = SessionDB()

# GET: all sessions metadata for current user
@router.get("/")
def get_sessions_metadata(current_user: dict = Depends(get_current_user)):
    try:
        # Fetch sessions for the current user, selecting only safe metadata fields
        response = session_db.table \
            .select("id, title, duration, participants, created_at, updated_at") \
            .eq("user_id", current_user["id"]) \
            .execute()

        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")

# GET: metadata for a specific session
@router.get("/{session_id}")
def get_session_metadata(session_id: str, current_user: dict = Depends(get_current_user)):
    try:
        session = session_db.get_session(session_id)

        if not session or session["user_id"] != current_user["id"]:
            return {
                "status": "Error",
                "data": None
            }

        processing_status = session.get("metadata_status")

        return {
            "status": processing_status,
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
                "metadata_status": session.get("metadata_status")
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")
