from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import uuid, os

from app.db.session import get_db
from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.emotion import Emotion
from app.schemas.session import SessionRead
from app.schemas.emotion import EmotionRead
from app.api.dependencies import get_current_user

from app.services.azure_uploader import AzureUploader
import os

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../../temp_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/sessions/upload", response_model=SessionRead)
def upload_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # Init uploader (ideally only once)
    uploader = AzureUploader(
        connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
        container_name="audiofiles"
    )

    # Save file to Azure and get SAS URL
    temp_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[-1]}"
    blob_url = uploader.upload_file_and_get_sas(file.file, temp_filename)

    session = SessionModel(
        user_id=current_user.id,
        title="New Session",
        participants="",
        duration_minutes=0,
        audio_blob_url=blob_url,
        status="uploaded"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session

@router.get("/sessions", response_model=List[SessionRead])
def get_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(SessionModel).filter(SessionModel.user_id == current_user.id).all()

@router.get("/sessions/{session_id}/emotions", response_model=List[EmotionRead])
def get_emotions(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(SessionModel).filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db.query(Emotion).filter_by(session_id=session_id).all()
