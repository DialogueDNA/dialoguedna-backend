from pydantic import BaseModel
from app.services.summary.prompts import PROMPT_LABELS, PromptStyle
from app.services.summary.runner import try_run_summary
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.db.session_db import SessionDB
from app.storage.session_storage import SessionStorage
from app.utils.pdf import generate_session_pdf
from app.api.dependencies.auth import get_current_user
import requests

router = APIRouter()
session_db = SessionDB()
session_storage = SessionStorage()

@router.get("/presets")
def list_summary_presets(current_user: dict = Depends(get_current_user)):
    """
    Returns the list of available summary styles (for the UI dropdown).
    """
    return {"presets": [{"key": k.value, "label": v} for k, v in PROMPT_LABELS.items()]}

class GenerateBody(BaseModel):
    preset: PromptStyle

# POST: (re)generate summary with a chosen preset (idempotent)
@router.post("/{session_id}/generate")
def generate_summary(session_id: str, body: GenerateBody, current_user: dict = Depends(get_current_user)):
    """
    Force-generate (or re-generate) a summary with a specific preset.
    Prerequisites: transcript & emotions must be completed.

    Idempotent behavior:
    - Always persist the new preset.
    - Reset summary_status -> 'not_started' (optionally clear URL).
    - Trigger try_run_summary().
    - Return current DB state (processing/completed) instead of failing
      just because try_run_summary() returned False.
    """
    session = session_db.get_session(session_id)
    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    if session.get("transcript_status") != "completed" or session.get("emotion_breakdown_status") != "completed":
        raise HTTPException(status_code=409, detail="Prerequisites not ready (transcript/emotions)")

    # 1) Persist preset + reset status (optional: clear old URL to avoid stale UI)
    session_db.update_session(session_id, {
        "summary_preset": body.preset.value,
        "summary_status": "not_started",
        # "summary_url": None,   # uncomment if you prefer to hide old summary during regen
        "processing_error": None,
    })

    # 2) Try to run now (may return False even if state moved to processing/completed)
    _ = try_run_summary(session_id)

    # 3) Read fresh state and respond idempotently
    s2 = session_db.get_session(session_id)
    st = s2.get("summary_status")
    if st in ("processing", "completed"):
        return {
            "status": st,
            "preset": body.preset.value,
            "summary_url": s2.get("summary_url"),
        }
    if st == "failed":
        raise HTTPException(status_code=500, detail=f"Summary failed: {s2.get('processing_error')}")
    if st == "not_started":
        # Unexpected: trigger didn't start; expose reason if recorded
        raise HTTPException(status_code=500, detail=f"Summary did not start. error={s2.get('processing_error')}")

    # Fallback (shouldn't reach here)
    raise HTTPException(status_code=500, detail=f"Unexpected summary status: {st}")


# GET: text summary of a session
@router.get("/{session_id}")
def get_summary(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)
    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Summary not found or access denied")

    summary_status = session.get("summary_status")
    summary_blob = session.get("summary_url")

    # Include error for easier debugging/UX
    error = session.get("processing_error")

    if summary_status != "completed" or not summary_blob:
        return {
            "status": summary_status,
            "data": None,
            "error": error,
        }

    try:
        summary_url = session_storage.generate_sas_url(summary_blob)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")

    return {
        "status": "completed",
        "data": summary_url,
        "error": None,
    }


# GET: download summary as PDF
@router.get("/{session_id}/download")
def download_summary_pdf(session_id: str, current_user: dict = Depends(get_current_user)):
    session = session_db.get_session(session_id)

    if not session or session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    summary_blob = session.get("summary_url")
    if not summary_blob:
        raise HTTPException(status_code=404, detail="Summary not yet generated")

    try:
        summary_url = session_storage.generate_sas_url(summary_blob)
        summary_text = requests.get(summary_url).text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")

    # Use the session metadata and summary text to generate the PDF
    pdf_path = generate_session_pdf({
        "title": session.get("title"),
        "created_at": session.get("created_at"),
        "duration": session.get("duration"),
        "participants": session.get("participants"),
        "summary": summary_text
    })

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"session-{session_id}.pdf")