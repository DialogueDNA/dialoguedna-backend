# app/services/transcription/models/azure_speech_stt.py
from __future__ import annotations
from typing import Any, Optional
import time
import requests
import logging

from app.storage.azure.blob.azure_blob_service import AzureBlobService
from app.settings.environment import AZURE_SPEECH_KEY, AZURE_REGION

log = logging.getLogger("app.transcription.azure")

class AzureSpeechTranscriber:
    def __init__(
        self,
        speech_key: str = AZURE_SPEECH_KEY,
        region: str = AZURE_REGION,
        locale: str = "en-US",
        diarization_enabled: bool = True,
        azure_blob: Optional[AzureBlobService] = None,
    ) -> None:
        self.speech_key = speech_key
        self.region = region
        self.locale = locale
        self.diarization_enabled = diarization_enabled
        self.azure_blob = azure_blob or AzureBlobService()
        self._language: str | None = None
        self._duration_ms: int | None = None
        self._phrases: list[dict[str, Any]] | None = None

    def transcribe(self, audio_blob_path: str) -> list[dict[str, Any]]:
        sas_url = self.azure_blob.generate_sas_url(audio_blob_path)

        log.info("Creating Azure STT transcription job...")
        job = self._create_transcription_job(sas_url)
        log.debug("Job data: %s", job)

        result = self._poll_until_complete(job)
        if result.get("status") != "Succeeded":
            log.error("Azure STT job failed: %s", result)
            raise RuntimeError("Azure STT job did not succeed.")

        files_url = result["links"]["files"]
        transcription_json = self._fetch_transcription_file(files_url)
        log.debug("Transcription JSON: %s", transcription_json)

        if not transcription_json:
            raise RuntimeError("Azure STT returned no transcription JSON.")

        self._phrases = transcription_json.get("recognizedPhrases", [])
        self._duration_ms = transcription_json.get("durationMilliseconds")
        self._language = transcription_json.get("locale")

        return self._format_transcript_as_json(self._phrases)

    def _create_transcription_job(self, sas_url: str, name: str = "TranscriptionJob") -> dict:
        url = f"https://{self.region}.api.cognitive.microsoft.com/speechtotext/v3.1/transcriptions"
        headers = {"Ocp-Apim-Subscription-Key": self.speech_key, "Content-Type": "application/json"}
        body = {
            "contentUrls": [sas_url],
            "locale": self.locale,
            "displayName": name,
            "properties": {
                "diarizationEnabled": self.diarization_enabled,
                "wordLevelTimestampsEnabled": True,
                "punctuationMode": "DictatedAndAutomatic",
                "profanityFilterMode": "Masked",
            },
        }
        log.debug("Sending Azure STT job with SAS URL: %s", sas_url)
        return requests.post(url, headers=headers, json=body).json()

    def _poll_until_complete(self, job_data: dict) -> dict:
        headers = {"Ocp-Apim-Subscription-Key": self.speech_key}
        transcription_url = job_data.get("self")
        if not transcription_url:
            raise ValueError("Azure STT: missing 'self' URL in job response.")

        while True:
            resp = requests.get(transcription_url, headers=headers)
            data = resp.json()
            status = data.get("status")
            log.info("Azure STT job status: %s", status)
            if status in {"Succeeded", "Failed"}:
                return data
            time.sleep(5)

    def _fetch_transcription_file(self, files_url: str) -> dict | None:
        headers = {"Ocp-Apim-Subscription-Key": self.speech_key}
        files = requests.get(files_url, headers=headers).json().get("values", [])
        for f in files:
            if f.get("kind") == "Transcription":
                return requests.get(f["links"]["contentUrl"]).json()
        return None

    @staticmethod
    def _format_transcript_as_json(phrases: list[dict[str, Any]]) -> list[dict[str, Any]]:
        lines: list[dict[str, Any]] = []
        for p in phrases:
            speaker = p.get("speaker", "?")
            text = (p.get("nBest", [{}])[0] or {}).get("display", "")
            start_ms = p.get("offsetMilliseconds", 0)
            dur_ms = p.get("durationMilliseconds", 0)
            lines.append({
                "speaker": speaker,
                "text": text,
                "start_time": round(start_ms / 1000, 2),
                "end_time": round((start_ms + dur_ms) / 1000, 2),
            })
        return lines

    @property
    def transcript_language(self) -> str | None:
        return self._language

    @property
    def duration_milliseconds(self) -> int | None:
        return self._duration_ms
