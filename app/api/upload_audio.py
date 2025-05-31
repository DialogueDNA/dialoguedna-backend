from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import os
import uuid
from app.services.azure_uploader import AzureUploader
from app.core import config


router = APIRouter()

# Define temporary upload directory
UPLOAD_FOLDER = Path("temp_uploads")

# Initialize AzureUploader with connection string and container name
azure_uploader = AzureUploader(
    connection_string=config.AZURE_STORAGE_CONNECTION_STRING,
    container_name=config.AZURE_CONTAINER_NAME
)


# DEBUG: Print the connection string to verify
print(f"DEBUG: AZURE_CONNECTION_STRING = {config.AZURE_STORAGE_CONNECTION_STRING}")

@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """
    Endpoint that receives an audio file, uploads it to Azure Blob Storage,
    and returns a SAS URL for accessing the uploaded file.
    """

    session_id = str(uuid.uuid4())

    try:
        print(f"📥 Received file: {file.filename}")

        # Use the helper function to save, convert, upload, and get SAS URL
        sas_url = azure_uploader.handle_upload_file(
            file=file,
            upload_folder=UPLOAD_FOLDER,
            session_id=session_id
        )

        print(f"✅ Upload successful. SAS URL: {sas_url}")
        return {"status": "success", "sas_url": sas_url}

    except Exception as e:
        # Log and return any errors that occur
        print("❌ Error during upload:", str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
