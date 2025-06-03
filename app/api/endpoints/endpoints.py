"""
endpoints.py

Defines the API endpoints for the DialogueDNA backend.

POST /analyze:
- Accepts an audio file upload
- Runs full processing: transcription, diarization, emotion analysis, and summary
- Returns structured JSON with results
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
import uuid
from app.services.coordinator.facade import DialogueProcessor

router = APIRouter()
processor = DialogueProcessor()

TEMP_DIR = "../temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/analyze")
async def analyze_audio(file: UploadFile = File(...)):
    try:
        # Save uploaded file to a temporary path
        file_ext = os.path.splitext(file.filename)[-1]
        temp_filename = f"{uuid.uuid4()}{file_ext}"
        temp_path = os.path.join(TEMP_DIR, temp_filename)

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the file using the facade
        result = processor.process_audio(temp_path)

        # Optionally delete the file afterwards
        os.remove(temp_path)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/uploadAudioFile")
async def upload_audio(file: UploadFile = File(...)):
    try:
        # Save uploaded file to a temporary path
        file_ext = os.path.splitext(file.filename)[-1]
        temp_filename = f"{uuid.uuid4()}{file_ext}"
        temp_path = os.path.join(TEMP_DIR, temp_filename)

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process the file using the facade
        result = processor.upload_audio_file_in_db(temp_path)

        # Optionally delete the file afterwards
        os.remove(temp_path)

        return JSONResponse(
            content={"sas_url": result},
            media_type="application/json"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
