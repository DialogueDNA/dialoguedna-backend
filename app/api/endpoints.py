"""
endpoints.py

Defines the API endpoints for the DialogueDNA backend.

POST /analyze:
- Accepts an audio file upload
- Runs full processing: transcription, diarization, emotion analysis, and summary
- Returns structured JSON with results
"""

"""
שליפת הsession מיניב. 
 
המרת האדוי ל.WAV 

המשך ניתוח.

העלאת הניתוחים לDB

"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import shutil
import os
import uuid
from fastapi import APIRouter
from app.api import upload_audio
from app.client.ClientsManager import ClientsManager
from app.services.facade import DialogueProcessor
from app.services.audio_converter import AudioConverter

router = APIRouter()
# Include the audio upload route
router.include_router(upload_audio.router)
processor = DialogueProcessor()
clients_manager = ClientsManager()

TEMP_DIR = "temp_uploads"
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

#
# @router.post("/upload-audio")
# async def upload_audio(
#     file: UploadFile = File(...),
#     client_name: str = Form(...),
#     session_name: str = Form(...)
# ):
#     # Get client and create session/audio directory
#     client = clients_manager.get_client(client_name)
#     session_audio_path = os.path.join(client.get_base_path(), session_name, "audio")
#     os.makedirs(session_audio_path, exist_ok=True)
#
#     # Temp file path (save original upload before conversion)
#     temp_path = os.path.join(session_audio_path, file.filename)
#     with open(temp_path, "wb") as temp_file:
#         content = await file.read()
#         temp_file.write(content)
#
#     # Convert to WAV and save as original.wav
#     output_path = os.path.join(session_audio_path, "original.wav")
#     try:
#         AudioConverter.convert_to_wav(temp_path, output_path)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
#
#     # Remove the original temp file
#     os.remove(temp_path)
#
#     return {"status": "success", "path": output_path}
#
