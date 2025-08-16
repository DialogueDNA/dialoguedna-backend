# from fastapi import APIRouter, Depends, HTTPException
# from fastapi.responses import FileResponse
# from app.database.session_db import SessionDB
# import app.core.constants.db.supabase_constants as db_constants
# from app.storage.session_storage import SessionStorage
# from app.common.utils import generate_session_pdf
# from app.api.dependencies.auth import get_current_user
# import requests
#
# router = APIRouter()
# session_db = SessionDB()
# session_storage = SessionStorage()
#
# # GET: text summary of a session
# @router.get("/{session_id}")
# def get_summary(session_id: str, current_user: dict = Depends(get_current_user)):
#     session = session_db.get_session(session_id)
#     if not session or session[db_constants.SESSIONS_COLUMN_USER_ID] != current_user[db_constants.AUTH_COLUMN_UNIQUE_ID]:
#         raise HTTPException(status_code=404, detail="Summary not found or access denied")
#
#     summary_status = session.get(db_constants.SESSIONS_COLUMN_SUMMARY_STATUS)
#     summary_blob = session.get(db_constants.SESSIONS_COLUMN_SUMMARY_URL)
#
#     if summary_status != db_constants.SESSION_STATUS_COMPLETED or not summary_blob:
#         return {
#             "status": summary_status,
#             "data": None
#         }
#
#     try:
#         summary_url = session_storage.generate_sas_url(summary_blob)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")
#
#     return {
#         "status": "completed",
#         "data": summary_url
#     }
#
# # GET: download summary as PDF
# @router.get("/{session_id}/download")
# def download_summary_pdf(session_id: str, current_user: dict = Depends(get_current_user)):
#     session = session_db.get_session(session_id)
#
#     if not session or session[db_constants.SESSIONS_COLUMN_USER_ID] != current_user[db_constants.AUTH_COLUMN_UNIQUE_ID]:
#         raise HTTPException(status_code=404, detail="Session not found or access denied")
#
#     summary_blob = session.get(db_constants.SESSIONS_COLUMN_SUMMARY_URL)
#     if not summary_blob:
#         raise HTTPException(status_code=404, detail="Summary not yet generated")
#
#     try:
#         summary_url = session_storage.generate_sas_url(summary_blob)
#         summary_text = requests.get(summary_url).text
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")
#
#     # Use the session metadata and summary text to generate the PDF
#     pdf_path = generate_session_pdf({
#         "title": session.get(db_constants.SESSIONS_COLUMN_TITLE),
#         "created_at": session.get(db_constants.SESSIONS_COLUMN_CREATED_AT),
#         "duration": session.get(db_constants.SESSIONS_COLUMN_DURATION),
#         "participants": session.get("SESSIONS_COLUMN_PARTICIPANTS", []),
#         "summary": summary_text
#     })
#
#     return FileResponse(pdf_path, media_type="application/pdf", filename=f"session-{session_id}.pdf")