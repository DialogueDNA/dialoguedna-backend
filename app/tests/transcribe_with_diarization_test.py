from pathlib import Path
from app.services.archives.transcription import TranscribeAndDiarizeManager
from app.services.archives.infrastructure import AzureUploader
from app.core import config  # Make sure it loads from .env

def run_transcription():
    # Azure credentials
    connection_string = config.AZURE_STORAGE_CONNECTION_STRING
    container_name = config.AZURE_CONTAINER_NAME

    # Setup uploader and transcriber
    uploader = AzureUploader(connection_string=connection_string, container_name=container_name)
    output_dir = Path("temp_uploads")
    transcriber = TranscribeAndDiarizeManager(output_dir=output_dir, uploader=uploader)

    # ✅ Full SAS URL of the audio file
    sas_url = (
        "https://audiorecordstorage.blob.core.windows.net/sessions"
        "?sp=r&st=2025-05-31T17:55:00Z&se=2025-06-01T01:55:00Z&spr=https&sv=2024-11-04&sr=b&sig=FkWlx55BkzlP1%2FV5tT2piiaUpzidTdJbybqHKMYu%2B%2F0%3D"
    )
    session_id = "0e139d18-0266-4be1-b569-c46b34c9af82"

    try:
        print("🚀 Starting transcription...")
        result_sas_url = transcriber.transcribe(sas_url,session_id)
        print("✅ Transcription result uploaded to:")
        print(result_sas_url)
    except Exception as e:
        print("❌ Transcription failed:", str(e))





if __name__ == "__main__":
    run_transcription()
