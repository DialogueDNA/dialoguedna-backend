"""
transcriber.py

Transcriber service using Azure Speech-to-Text with speaker diarization.

Responsibilities:
- Upload the audio file to Azure Blob Storage
- Create transcription job with diarization
- Poll until job is complete
- Download and return the final transcript
"""

from app.services.infrastructure.azure_uploader import AzureUploader
from app.services.transcription.transcribe_with_diarization_manager import TranscribeAndDiarizeManager
from app.core.config import (
    AZURE_STORAGE_CONNECTION_STRING,
    AZURE_CONTAINER_NAME,
    TRANSCRIPTS_DIR,
)

class Transcriber:
    def __init__(self):
        self.uploader = AzureUploader(
            connection_string=AZURE_STORAGE_CONNECTION_STRING,
            container_name=AZURE_CONTAINER_NAME
        )
        self.azure_transcriber = TranscribeAndDiarizeManager(output_dir=TRANSCRIPTS_DIR)

    # def transcribe(self, audio_path: str) -> str:
    #     """
    #     Uploads the audio file to Azure, transcribes it with diarization,
    #     and returns the transcript as plain text.
    #     """
    #     audio_path = Path(audio_path)
    #     print("☁️ Uploading audio to Azure...")
    #     sas_url = self.uploader.upload_file_and_get_sas(audio_path, blob_name=audio_path.name)
    #
    #     print("📝 Transcribing with Azure Speech Service...")
    #     transcript_path = self.azure_transcriber.transcribe(sas_url)
    #
    #     return transcript_path.read_text(encoding="utf-8")

