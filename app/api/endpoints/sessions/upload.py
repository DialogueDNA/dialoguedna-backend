from fastapi import UploadFile, File, Form, HTTPException, Depends, BackgroundTasks, APIRouter
from app.services.facade import DialogueProcessor
from app.db.session_db import SessionDB
from app.api.dependencies.auth import get_current_user
from app.services.summary.prompts import PromptStyle
from app.services.summary.runner import try_run_summary

router = APIRouter()
processor = DialogueProcessor()
session_db = SessionDB()

@router.post("/")
async def create_session(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    summary_preset: str | None = Form(None),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]

    # ✅ Upload file and get session_id + blob path
    try:
        session_id, audio_path = processor.upload_audio_file(file=file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio upload failed: {str(e)}")

    # ✅ Create session record in DB
    new_session = {
        "id": session_id,
        "user_id": user_id,
        "title": title,
        "metadata_status": "completed",
        "language": "not_started",
        "duration": None,
        "participants": [],
        "source": "web",
        "is_favorite": False,
        "tags": [],
        "audio_file_status": "completed",
        "audio_file_url": audio_path,
        "transcript_status": "not_started",
        "transcript_url": None,
        "emotion_breakdown_status": "not_started",
        "emotion_breakdown_url": None,
        "summary_status": "not_started",
        "summary_url": None,
        "summary_preset": None,
        "session_status": "processing",
        "processing_error": None,
    }

    # Validate and store preset if provided
    if summary_preset:
        try:
            preset_enum = PromptStyle(summary_preset)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid summary_preset")
        new_session["summary_preset"] = preset_enum.value

    try:
        session_db.create_session(new_session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session record: {str(e)}")

    # ✅ Start background processing
    background_tasks.add_task(
        processor.process_audio,
        session_id=session_id,
        audio_path=audio_path
    )

    # Soft-trigger (in case pipeline races and completes super-fast)
    if new_session["summary_preset"]:
        try_run_summary(session_id)

    return {"session_id": session_id}