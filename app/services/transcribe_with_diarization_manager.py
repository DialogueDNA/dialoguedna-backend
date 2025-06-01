import requests
import time
import os
from urllib.parse import urlparse
from pathlib import Path
from app.core.config import SPEECH_KEY, REGION ,AZURE_CONTAINER_URL,AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME
from app.storage.azure.blob.azure_blob_service import AzureBlobService
from app.storage.azure.blob.azure_blob_uploader import AzureUploader


class TranscribeAndDiarizeManager:
    def __init__(self, output_dir: Path = None, uploader=None):
        self.output_dir = output_dir or Path("temp_uploads")
        self.uploader = uploader or AzureUploader()
        os.makedirs(self.output_dir, exist_ok=True)
        self.output_dir = output_dir or Path("temp_uploads")
        self.azure = AzureBlobService()
        os.makedirs(self.output_dir, exist_ok=True)

    def create_transcription_job(self, sas_url: str, name="MyTranscription"):
        url = f"https://{REGION}.api.cognitive.microsoft.com/speechtotext/v3.1/transcriptions"
        headers = {
            "Ocp-Apim-Subscription-Key": SPEECH_KEY,
            "Content-Type": "application/json"
        }

        # ✅ פשוט השתמש ב־sas_url כמו שהוא
        print("📨 Sent job with URL:", sas_url)

        body = {
            "contentUrls": [sas_url],
            "locale": "en-US",
            "displayName": name,
            "properties": {
                "diarizationEnabled": True,
                "wordLevelTimestampsEnabled": True,
                "punctuationMode": "DictatedAndAutomatic",
                "profanityFilterMode": "Masked"
            }
        }

        response = requests.post(url, headers=headers, json=body)
        return response.json()

    def poll_until_complete(self, job_data: dict):
        headers = {"Ocp-Apim-Subscription-Key": SPEECH_KEY}
        transcription_url = job_data.get("self")

        if not transcription_url:
            raise ValueError("❌ No transcription URL returned in job_data")

        while True:
            response = requests.get(transcription_url, headers=headers)

            try:
                data = response.json()
            except Exception:
                print("❌ Failed to parse JSON:", response.text)
                raise

            status = data.get("status")
            print("⏳ Status:", status)

            if status in ["Succeeded", "Failed"]:
                print("📦 Final status data:", data)
                return data

            time.sleep(5)

    def fetch_transcription_file(self, files_url: str):
        headers = {"Ocp-Apim-Subscription-Key": SPEECH_KEY}
        response = requests.get(files_url, headers=headers)
        files = response.json().get("values", [])
        for file in files:
            if file["kind"] == "Transcription":
                content_url = file["links"]["contentUrl"]
                return requests.get(content_url).json()
        return None

    def generate_transcript_path(self, audio_url: str) -> Path:
        parsed = urlparse(audio_url)
        stem = Path(parsed.path).stem
        return self.output_dir / f"{stem}_transcript.txt"

    def save_transcript(self, transcription_json: dict, output_path: Path):
        phrases = transcription_json.get("recognizedPhrases", [])
        with open(output_path, "w", encoding="utf-8") as f:
            for phrase in phrases:
                speaker = phrase.get("speaker", "?")
                text = phrase.get("nBest", [{}])[0].get("display", "")
                f.write(f"Speaker {speaker}: {text}\n")

    def transcribe(self, blob_path: str, session_id: str) -> str:
        """
        Transcribes the given blob audio file and returns the new transcript blob path.
        """
        # 🔑 Generate a secure SAS URL for the Azure Speech API
        sas_url = self.azure.generate_sas_url(blob_path)

        print("📤 Creating transcription job...")
        job_data = self.create_transcription_job(sas_url)
        print("📦 job_data:", job_data)

        result_data = self.poll_until_complete(job_data)
        if result_data.get("status") != "Succeeded":
            raise Exception("Transcription job failed.")

        # 📥 Fetch result
        files_url = result_data["links"]["files"]
        result_json = self.fetch_transcription_file(files_url)
        if not result_json:
            raise Exception("No transcription result returned.")

        # 💾 Save to local file
        output_path = self.output_dir / f"{session_id}_transcribe_with_diarization.txt"
        self.save_transcript(result_json, output_path)

        # ☁️ Upload transcript to Azure
        transcript_blob = f"{session_id}/transcribe_with_diarization.txt"
        print(f"☁️ Uploading transcript to Azure as {transcript_blob}...")
        self.azure.upload_file(output_path, transcript_blob)

        print("✅ Transcript uploaded successfully.")
        return transcript_blob
