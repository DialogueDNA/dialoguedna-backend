# from fastapi import UploadFile, File, Form, HTTPException, Depends, BackgroundTasks, APIRouter
# from app.services.facade import DialogueProcessor
# from app.database.session_db import SessionDB
# from app.api.dependencies.auth import get_current_user
# import app.core.constants.db.supabase_constants as db_constants
#
# router = APIRouter()
# processor = DialogueProcessor()
# session_db = SessionDB()
#
# @router.post("/")
# async def create_session(
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...),
#     title: str = Form(...),
#     current_user: dict = Depends(get_current_user)
# ):
#     user_id = current_user[db_constants.AUTH_COLUMN_UNIQUE_ID]
#
#     # ✅ Upload file and get session_id + blob path
#     try:
#         session_id, audio_path = processor.upload_audio_file(file=file)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Audio upload failed: {str(e)}")
#
#     # ✅ Create session record in DB
#     new_session = {
#         db_constants.SESSIONS_COLUMN_UNIQUE_ID: session_id,
#         db_constants.SESSIONS_COLUMN_USER_ID: user_id,
#         db_constants.SESSIONS_COLUMN_TITLE: title,
#         db_constants.SESSIONS_COLUMN_METADATA_STATUS: db_constants.SESSION_STATUS_COMPLETED,
#         db_constants.SESSIONS_COLUMN_LANGUAGE: db_constants.SESSION_STATUS_NOT_STARTED,
#         db_constants.SESSIONS_COLUMN_DURATION: None,
#         db_constants.SESSIONS_COLUMN_PARTICIPANTS: [],
#         db_constants.SESSIONS_COLUMN_SOURCE: "web",
#         db_constants.SESSIONS_COLUMN_IS_FAVORITE: False,
#         db_constants.SESSIONS_COLUMN_TAGS: [],
#         db_constants.SESSIONS_COLUMN_AUDIO_FILE_STATUS: db_constants.SESSION_STATUS_COMPLETED,
#         db_constants.SESSIONS_COLUMN_AUDIO_FILE_URL: audio_path,
#         db_constants.SESSIONS_COLUMN_TRANSCRIPT_STATUS: db_constants.SESSION_STATUS_NOT_STARTED,
#         db_constants.SESSIONS_COLUMN_TRANSCRIPT_URL: None,
#         db_constants.SESSIONS_COLUMN_EMOTION_BREAKDOWN_STATUS: db_constants.SESSION_STATUS_NOT_STARTED,
#         db_constants.SESSIONS_COLUMN_EMOTION_BREAKDOWN_URL: None,
#         db_constants.SESSIONS_COLUMN_SUMMARY_STATUS: db_constants.SESSION_STATUS_NOT_STARTED,
#         db_constants.SESSIONS_COLUMN_SUMMARY_URL: None,
#         db_constants.SESSIONS_COLUMN_STATUS: db_constants.SESSION_STATUS_PROGRESSING,
#         db_constants.SESSIONS_COLUMN_PROCESSING_ERROR: None,
#     }
#
#     try:
#         session_db.create_session(new_session)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to create session record: {str(e)}")
#
#     # ✅ Start background processing
#     background_tasks.add_task(
#         processor.process_audio,
#         session_id=session_id,
#         audio_path=audio_path
#     )
#
#     return {"session_id": session_id}