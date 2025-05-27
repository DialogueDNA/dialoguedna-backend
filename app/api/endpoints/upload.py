from fastapi import UploadFile, File, Form, HTTPException, Depends, APIRouter
from app.core.config import supabase
from app.api.dependencies.auth import get_current_user
import uuid, time

router = APIRouter()

@router.post("/")
async def create_session(
    file: UploadFile = File(...),
    title: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    filename = f"{user_id}/{int(time.time())}-{uuid.uuid4()}-{file.filename}"
    file_bytes = await file.read()

    # ✅ Upload file to Supabase
    upload_response = supabase.storage.from_("audio-sessions").upload(filename, file_bytes)

    if not upload_response.path:
        raise HTTPException(status_code=500, detail="Upload to Supabase failed")

    # ✅ Use the returned path as the audio_file_url
    audio_path = upload_response.path

    new_session = {
        "user_id": user_id,
        "title": title,
        "audio_file_url": audio_path,
        "duration": None,
        "participants": [],
        "status": "uploaded",
        "language": None,
        "source": "web",
        "processing_error": None,
        "is_favorite": False,
        "tags": [],
        "transcript": None,
        "summary": None
    }

    insert = supabase.table("sessions").insert(new_session).execute()

    if not insert.data or "id" not in insert.data[0]:
        raise HTTPException(status_code=500, detail="Failed to create session record")

    return {"session_id": insert.data[0]["id"]}
