import requests
import time
import os
import json
from urllib.parse import urlparse
from pathlib import Path
from Yarden_05_05_205.AppRun.config import SPEECH_KEY, REGION

class TranscribeAndDiarizeManager:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def create_transcription_job(self, audio_url: str, name="MyTranscription"):
        url = f"https://{REGION}.api.cognitive.microsoft.com/speechtotext/v3.1/transcriptions"
        headers = {
            "Ocp-Apim-Subscription-Key": SPEECH_KEY,
            "Content-Type": "application/json"
        }
        body = {
            "contentUrls": [audio_url],
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
        while True:
            response = requests.get(transcription_url, headers=headers)
            data = response.json()
            status = data.get("status")
            print("⏳ Status:", status)
            if status in ["Succeeded", "Failed"]:
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


    def transcribe(self, audio_url: str) -> Path:
        print("📤 Creating transcription job...")
        job_data = self.create_transcription_job(audio_url)
        result_data = self.poll_until_complete(job_data)

        if result_data.get("status") != "Succeeded":
            raise Exception("Transcription job failed.")

        files_url = result_data["links"]["files"]
        result_json = self.fetch_transcription_file(files_url)

        if not result_json:
            raise Exception("No transcription result returned.")

        output_path = self.generate_transcript_path(audio_url)
        self.save_transcript(result_json, output_path)
        return output_path
