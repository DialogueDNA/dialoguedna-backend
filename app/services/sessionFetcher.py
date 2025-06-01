from app.services.azure_fetcher import AzureFetcher
from app.core.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME

class SessionFetcher:
    def __init__(self):
        self.fetcher = AzureFetcher(
            connection_string=AZURE_STORAGE_CONNECTION_STRING,
            container_name=AZURE_CONTAINER_NAME
        )

    def get_transcript(self, session_id: str) -> str:
        blob_name = f"sessions/{session_id}/transcript"
        return self._generate_url(blob_name)

    def get_summary(self, session_id: str) -> str:
        blob_name = f"sessions/{session_id}/summary"
        return self._generate_url(blob_name)

    def get_emotions(self, session_id: str) -> str:
        blob_name = f"sessions/{session_id}/emotions.json"
        return self._generate_url(blob_name)

    def get_status(self, session_id: str) -> str:
        blob_name = f"sessions/{session_id}/status.json"
        return self._generate_url(blob_name)

    def get_audio(self, session_id: str) -> str:
        blob_name = f"sessions/{session_id}/audio.wav"
        return self._generate_url(blob_name)

    def _generate_url(self, blob_name: str) -> str:
        try:
            return self.fetcher.generate_sas_url(blob_name)
        except Exception as e:
            raise RuntimeError(f"Failed to generate SAS URL for '{blob_name}': {str(e)}")
