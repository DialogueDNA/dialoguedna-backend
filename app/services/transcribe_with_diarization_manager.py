import requests
import time
import os
import json
from urllib.parse import urlparse
from pathlib import Path
from app.core.config import SPEECH_KEY, REGION ,AZURE_CONTAINER_URL,AZURE_STORAGE_CONNECTION_STRING, AZURE_CONTAINER_NAME
from app.services.azure_uploader import AzureUploader
import re
from typing import List


class TranscribeAndDiarizeManager:
    def __init__(self, output_dir: Path = None, uploader=None):
        self.output_dir = output_dir or Path("temp_uploads")
        self.uploader = uploader or AzureUploader(
            connection_string=AZURE_STORAGE_CONNECTION_STRING,
            container_name=AZURE_CONTAINER_NAME
        )
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

    #
    # def transcribe(self, audio_url: str) -> Path:
    #     print("📤 Creating transcription job...")
    #     job_data = self.create_transcription_job(audio_url)
    #     result_data = self.poll_until_complete(job_data)
    #
    #     if result_data.get("status") != "Succeeded":
    #         raise Exception("Transcription job failed.")
    #
    #     files_url = result_data["links"]["files"]
    #     result_json = self.fetch_transcription_file(files_url)
    #
    #     if not result_json:
    #         raise Exception("No transcription result returned.")
    #
    #     output_path = self.generate_transcript_path(audio_url)
    #     self.save_transcript(result_json, output_path)
    #     return output_path

    def extract_speakers_from_transcript(transcript_text: str) -> List[str]:
        """
        Extracts a list of unique speaker labels from a transcript text.

        Parameters:
        - transcript_text (str): The full transcript text containing speaker lines.

        Returns:
        - List[str]: A list of unique speaker labels (e.g. ['Speaker 1', 'Speaker 2'])
        """
        # Find all lines starting with something like "Speaker 1:"
        matches = re.findall(r"Speaker \d+", transcript_text)

        # Remove duplicates by converting to a set, then sort
        unique_speakers = sorted(set(matches), key=lambda x: int(x.split()[-1]))

        return unique_speakers


    def transcribe(self,sas_url: str, session_id: str, container_sas_url: str = AZURE_CONTAINER_URL ,filename: str = "audio.wav") -> \
    tuple[str, list[str]]:

        # 🔍 Extract session_id from SAS URL
        print(container_sas_url)
        print(sas_url)
        print (session_id)

        #recordings_url = f"{container_sas_url.rstrip('/')}/{session_id}"

        #audio_path_in_container = f"{session_id}/{filename}"

        # 📤 Create transcription job
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

        # ☁️ Upload to Azure
        blob_name = f"{session_id}/transcribe_with_diarization.txt"
        print(f"☁️ Uploading transcript to Azure as {blob_name}...")
        sas_url = self.uploader.upload_file_and_get_sas(output_path, blob_name=blob_name)

        # 🧠 Extract speaker list from result
        with open(output_path, "r", encoding="utf-8") as f:
            transcript_text = f.read()

        speakers = self.extract_speakers_from_transcript(transcript_text)

        print("✅ Transcript uploaded successfully.")

        return sas_url, speakers




    #
    #
    # def extract_session_and_filename(self, sas_url: str):
    #     parsed = urlparse(sas_url)
    #     blob_path = parsed.path.lstrip("/")  # removes leading slash
    #
    #     parts = blob_path.split("/")
    #     if len(parts) < 3:
    #         raise ValueError(f"Invalid blob path in SAS URL: {blob_path}")
    #
    #     # parts = [container, session_id, filename]
    #     container = parts[0]
    #     session_id = parts[1]
    #     filename = "/".join(parts[2:])  # in case there are subfolders
    #
    #     return session_id, filename
    #

