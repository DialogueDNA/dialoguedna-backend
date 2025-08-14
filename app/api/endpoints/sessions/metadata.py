from fastapi import APIRouter, Depends, HTTPException
from app.database.session_db import SessionDB
from app.api.dependencies.auth import get_current_user
import app.core.constants.db.supabase_constants as db_constants

router = APIRouter()
session_db = SessionDB()

# GET: all sessions metadata for current user
@router.get("/")
def get_sessions_metadata(current_user: dict = Depends(get_current_user)):
    try:
        sessions = session_db.get_all_sessions_for_user(current_user[db_constants.AUTH_COLUMN_UNIQUE_ID])

        metadata_only = [
            {
                "id": s[db_constants.SESSIONS_COLUMN_UNIQUE_ID],
                "title": s[db_constants.SESSIONS_COLUMN_TITLE],
                "duration": s.get(db_constants.SESSIONS_COLUMN_DURATION),
                "participants": s.get(db_constants.SESSIONS_COLUMN_PARTICIPANTS, []),
                "created_at": s[db_constants.SESSIONS_COLUMN_CREATED_AT],
                "updated_at": s[db_constants.SESSIONS_COLUMN_UPDATED_AT],
                "transcript_status": s.get(db_constants.SESSIONS_COLUMN_TRANSCRIPT_STATUS, db_constants.SESSION_STATUS_PROGRESSING),
                "summary_status": s.get(db_constants.SESSIONS_COLUMN_SUMMARY_STATUS, db_constants.SESSION_STATUS_PROGRESSING),
                "emotion_breakdown_status": s.get(db_constants.SESSIONS_COLUMN_EMOTION_BREAKDOWN_STATUS, db_constants.SESSION_STATUS_PROGRESSING),
                "metadata_status": s.get(db_constants.SESSIONS_COLUMN_METADATA_STATUS, db_constants.SESSION_STATUS_COMPLETED),
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
        if not session or session[db_constants.SESSIONS_COLUMN_USER_ID] != current_user[db_constants.AUTH_COLUMN_UNIQUE_ID]:
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
                "id": session[db_constants.SESSIONS_COLUMN_UNIQUE_ID],
                "title": session[db_constants.SESSIONS_COLUMN_TITLE],
                "duration": session.get(db_constants.SESSIONS_COLUMN_DURATION),
                "participants": session.get(db_constants.SESSIONS_COLUMN_PARTICIPANTS, []),
                "created_at": session[db_constants.SESSIONS_COLUMN_CREATED_AT],
                "updated_at": session[db_constants.SESSIONS_COLUMN_UPDATED_AT],
                "audio_file_status": session.get(db_constants.SESSIONS_COLUMN_AUDIO_FILE_STATUS),
                "transcript_status": session.get(db_constants.SESSIONS_COLUMN_TRANSCRIPT_STATUS),
                "summary_status": session.get(db_constants.SESSIONS_COLUMN_SUMMARY_STATUS),
                "emotion_breakdown_status": session.get(db_constants.SESSIONS_COLUMN_EMOTION_BREAKDOWN_STATUS),
                "metadata_status": metadata_status
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving session: {str(e)}")