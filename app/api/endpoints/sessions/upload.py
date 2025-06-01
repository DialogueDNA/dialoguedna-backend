from fastapi import UploadFile, File, Form, HTTPException, Depends, BackgroundTasks, APIRouter
from app.api.dependencies.auth import get_current_user
from app.services.facade import DialogueProcessor
from app.services.sessionDB import SessionDB
from app.services.audio_duration import get_audio_duration


router = APIRouter()
processor = DialogueProcessor()
session_db = SessionDB()

@router.post("/")
async def create_session(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]

    # ✅ Upload file using the processor, returns Azure SAS URL
    try:
        #audio_duration = get_audio_duration(file)
        session_id, audio_path = processor.upload_audio_file_in_db(file=file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio upload failed: {str(e)}")

    # ✅ Create session record in DB
    new_session = {
        "id": session_id,
        "user_id": user_id,
        "title": title,
        "metadata_status": "not_started",
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
        "session_status": "processing",
        "processing_error": None,
    }

    try:
        session_id = session_db.create_session(new_session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session record: {str(e)}")

    # ✅ Start async background processing
    background_tasks.add_task(
        processor.process_audio,
        session_id=session_id,
        audio_path=audio_path
    )

    return {"session_id": session_id}
