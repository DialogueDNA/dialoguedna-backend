import uuid

from fastapi import UploadFile, File, Form, HTTPException, Depends, BackgroundTasks, APIRouter
from app.api.dependencies.auth import get_current_user
from app.services.facade import DialogueProcessor
from app.services.sessionDB import SessionDB
from app.core import config

router = APIRouter()
processor = DialogueProcessor()
session_db = SessionDB()
AZURE_CONTAINER_NAME = config.AZURE_CONTAINER_NAME


@router.post("/")
async def create_session(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]

    # 🆔 Create session ID manually for folder naming (not saved unless upload succeeds)
    session_id = str(uuid.uuid4())

    # Force audio file extension to always be '.wav', ignoring uploaded filename
    blob_name = f"AZURE_CONTAINER_NAME/{session_id}/audio.wav"
    try:
        audio_path = processor.upload_audio_file_in_db(file=file, blob_name=blob_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio upload failed: {str(e)}")

    # ✅ Create session record in DB
    new_session = {
        "id": session_id,  # use our manually created session ID
        "user_id": user_id,
        "title": title,
        "metadata_status": "not started",
        "language": "not started",
        "duration": None,
        "participants": [],
        "source": "web",
        "is_favorite": False,
        "tags": [],
        "audio_file_status": "completed",
        "audio_file_url": audio_path,
        "transcript_status": "not started",
        "transcript_url": None,
        "emotion_breakdown_status": "not started",
        "emotion_breakdown_url": None,
        "summary_status": "not started",
        "summary_url": None,
        "session_status": "Processing",
        "processing_error": None,
    }

    try:
        session_db.create_session(new_session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session record: {str(e)}")

    # ✅ Start async background processing
    background_tasks.add_task(
        processor.process_audio,
        session_id=session_id,
        audio_path=audio_path
    )

    return {"session_id": session_id}
