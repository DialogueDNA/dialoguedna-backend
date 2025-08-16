# from fastapi import APIRouter, Depends, HTTPException
# from app.database.session_db import SessionDB
# import app.core.constants.db.supabase_constants as db_constants
# from app.storage.session_storage import SessionStorage
# from app.api.dependencies.auth import get_current_user
#
# router = APIRouter()
# session_db = SessionDB()
# session_storage = SessionStorage()
#
# @router.get("/{session_id}")
# def get_audio(session_id: str, current_user: dict = Depends(get_current_user)):
#     session = session_db.get_session(session_id)
#
#     if not session or session[db_constants.SESSIONS_COLUMN_USER_ID] != current_user[db_constants.AUTH_COLUMN_UNIQUE_ID]:
#         raise HTTPException(status_code=404, detail="Audio not found or access denied")
#
#     audio_status = session.get(db_constants.SESSIONS_COLUMN_AUDIO_FILE_STATUS)
#     audio_blob_path = session.get(db_constants.SESSIONS_COLUMN_AUDIO_FILE_URL)
#
#     if audio_status != db_constants.SESSION_STATUS_COMPLETED or not audio_blob_path:
#         return {
#             "status": audio_status,
#             "data": None
#         }
#
#     try:
#         audio_url = session_storage.generate_sas_url(audio_blob_path)
#         return {
#             "status": "completed",
#             "data": audio_url
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to generate audio URL: {str(e)}")