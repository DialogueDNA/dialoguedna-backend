# app/services/transcription/adapters/azure_speech_transcriptor.py
from __future__ import annotations
import time, requests, os
from typing import Optional, Any
from app.ports.services.transcription import Transcriber, TranscriptionSegmentInput

class AzureSpeechTranscriber(Transcriber):
    def __init__(self, *, key: str, region: str):
        self.key = key
        self.region = region

    def transcribe_file(self, path: str, *, locale: Optional[str] = None, speaker_diarization: bool = True) -> list[TranscriptionSegmentInput]:
        container = "uploads"
        blob = os.path.basename(path)
        with open(path, "rb") as f:
            self.storage.upload(container, blob, f, content_type="audio/wav")
        return self.transcribe_blob(container, blob, locale=locale, speaker_diarization=speaker_diarization)

    # REST helpers
    def _create_job(self, sas_url: str, *, locale: str, diarization: bool) -> dict[str, Any]:
        url = f"https://{self.region}.api.cognitive.microsoft.com/speechtotext/v3.1/transcriptions"
        headers = {"Ocp-Apim-Subscription-Key": self.key, "Content-Type": "application/json"}
        body = {
            "contentUrls": [sas_url],
            "locale": locale,
            "displayName": "TranscriptionJob",
            "properties": {
                "diarizationEnabled": bool(diarization),
                "wordLevelTimestampsEnabled": True,
                "punctuationMode": "DictatedAndAutomatic",
                "profanityFilterMode": "Masked",
            },
        }
        return requests.post(url, headers=headers, json=body).json()

    def _poll(self, job_url: str) -> dict[str, Any]:
        headers = {"Ocp-Apim-Subscription-Key": self.key}
        while True:
            data = requests.get(job_url, headers=headers).json()
            if data.get("status") in ("Succeeded", "Failed"):
                return data
            time.sleep(5)

    def _fetch_json(self, files_url: str) -> dict[str, Any]:
        headers = {"Ocp-Apim-Subscription-Key": self.key}
        files = requests.get(files_url, headers=headers).json().get("values", [])
        for f in files:
            if f["kind"] == "Transcription":
                return requests.get(f["links"]["contentUrl"]).json()
        raise RuntimeError("No Transcription file in result set")

    def _format_segments(self, payload: dict[str, Any]) -> list[TranscriptionSegmentInput]:
        out: list[TranscriptionSegmentInput] = []
        for p in payload.get("recognizedPhrases", []):
            start_ms = p.get("offsetMilliseconds", 0)
            dur_ms = p.get("durationMilliseconds", 0)
            out.append({
                "speaker": p.get("speaker", "?"),
                "text": (p.get("nBest", [{}])[0] or {}).get("display", ""),
                "start_time": round(start_ms / 1000, 2),
                "end_time": round((start_ms + dur_ms) / 1000, 2),
            })
        return out