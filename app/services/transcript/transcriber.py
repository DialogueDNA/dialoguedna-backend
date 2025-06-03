from typing import Any, Optional

import requests
import time
from app.core.config import SPEECH_KEY, REGION
from app.storage.azure.blob.azure_blob_service import AzureBlobService

class Transcriber:
    def __init__(self):
        self._number_of_participants = None
        self._participants = None
        self._language = None
        self._duration_sec = None
        self._duration_ms = None
        self._phrases = None
        self._azure = AzureBlobService()

    @property
    def transcript_language(self) -> str | None:
        return self._language

    @property
    def duration_seconds(self) -> float | None:
        return self._duration_sec

    @property
    def duration_milliseconds(self) -> float | None:
        return self._duration_ms

    @property
    def recognized_phrases(self) -> list[dict] | None:
        return self._phrases

    @property
    def participants(self) -> list:
        return sorted({f"Speaker {p.get('speaker', '?')}" for p in self._phrases})

    @property
    def number_of_participants(self) -> int:
        return len(self.participants)

    def transcribe(self, audio_path: str) -> list[dict[str, Any]]:
        """
        Transcribes the given blob audio file and returns the new transcript blob path.
        """
        # 🔑 Generate a secure SAS URL for the Azure Speech API
        sas_url = self._azure.generate_sas_url(audio_path)

        print("📤 Creating transcription job...")
        job_data = self.create_transcription_job(sas_url)
        print("📦 job_data:", job_data)

        result_data = self.poll_until_complete(job_data)
        if result_data.get("status") != "Succeeded":
            raise Exception("Transcription job failed.")

        # 📥 Fetch result
        files_url = result_data["links"]["files"]
        transcription_json = self.fetch_transcription_file(files_url)
        print("📥 Result JSON:", transcription_json)
        if not transcription_json:
            raise Exception("No transcription result returned.")

        self._phrases = transcription_json.get("recognizedPhrases", [])
        self._duration_ms = transcription_json.get("durationMilliseconds")
        self._duration_sec = round(self._duration_ms / 1000, 2) if self._duration_ms else None
        self._language = transcription_json.get("locale")
        return self.format_transcript_as_json()

    def create_transcription_job(self, sas_url: str, name="MyTranscription"):
        url = f"https://{REGION}.api.cognitive.microsoft.com/speechtotext/v3.1/transcriptions"
        headers = {
            "Ocp-Apim-Subscription-Key": SPEECH_KEY,
            "Content-Type": "application/json"
        }

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

    def format_transcript_as_text(self) -> str:
        lines = []
        for phrase in self._phrases:
            speaker = phrase.get("speaker", "?")
            text = phrase.get("nBest", [{}])[0].get("display", "")
            lines.append(f"Speaker {speaker}: {text}")
        return "\n".join(lines)

    def format_transcript_as_json(self) -> list[dict]:
        """
        Convert Azure transcription result into a list of structured transcript lines.

        Each line contains:
        - speaker: Speaker label or "?"
        - text: Spoken text from that line
        - start_time: Time the utterance started (in seconds)
        - end_time: Time the utterance ended (in seconds)
        """
        lines = []

        for phrase in self._phrases:
            speaker = phrase.get("speaker", "?")
            text = phrase.get("nBest", [{}])[0].get("display", "")

            start_ms = phrase.get("offsetMilliseconds", 0)
            duration_ms = phrase.get("durationMilliseconds", 0)
            start_sec = round(start_ms / 1000, 2)
            end_sec = round((start_ms + duration_ms) / 1000, 2)

            lines.append({
                "speaker": speaker,
                "text": text,
                "start_time": start_sec,
                "end_time": end_sec
            })

        return lines