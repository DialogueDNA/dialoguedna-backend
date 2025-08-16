# from fastapi import APIRouter, HTTPException, Depends
# from pydantic import BaseModel
#
# from app.database.session_db import SessionDB
# import app.core.constants.db.supabase_constants as db_constants
# from app.storage.session_storage import SessionStorage
# from app.api.dependencies.auth import get_current_user
#
# router = APIRouter()
# session_db = SessionDB()
# session_storage = SessionStorage()
#
# class BulkDeleteRequest(BaseModel):
#     session_ids: list[str]
#
# def delete_related_blobs(session: dict):
#     session_id = session["id"]
#
#     if session.get("audio_file_status") == db_constants.SESSION_STATUS_COMPLETED:
#         session_storage.delete_audio(session_id)
#
#     if session.get("transcript_status") == db_constants.SESSION_STATUS_COMPLETED:
#         session_storage.delete_transcript(session_id)
#
#     if session.get("summary_status") == db_constants.SESSION_STATUS_COMPLETED:
#         session_storage.delete_summary(session_id)
#
#     if session.get("emotion_breakdown_status") == db_constants.SESSION_STATUS_COMPLETED:
#         session_storage.delete_emotions(session_id)
#
# @router.delete("/{session_id}")
# async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
#     user_id = current_user[db_constants.AUTH_COLUMN_UNIQUE_ID]
#     session = session_db.get_session(session_id)
#
#     if not session or session.get(db_constants.SESSIONS_COLUMN_USER_ID) != user_id:
#         raise HTTPException(status_code=404, detail="Session not found or unauthorized")
#
#     try:
#         delete_related_blobs(session)
#         session_db.delete_session(session_id)
#         return {"success": True}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
#
# @router.post("/bulk")
# async def delete_multiple_sessions(
#     payload: BulkDeleteRequest,
#     current_user: dict = Depends(get_current_user)
# ):
#     session_ids = payload.session_ids
#     user_id = current_user[db_constants.AUTH_COLUMN_UNIQUE_ID]
#     failed_deletes = []
#
#     for session_id in session_ids:
#         try:
#             session = session_db.get_session(session_id)
#             if not session or session.get(db_constants.SESSIONS_COLUMN_USER_ID) != user_id:
#                 failed_deletes.append(session_id)
#                 continue
#             delete_related_blobs(session)
#             session_db.delete_session(session_id)
#         except Exception:
#             failed_deletes.append(session_id)
#
#     if failed_deletes:
#         return {
#             "success": False,
#             "failed_ids": failed_deletes,
#             "message": "Some sessions could not be deleted"
#         }
#
#     return {"success": True}