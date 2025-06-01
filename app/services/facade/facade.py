import uuid
from typing import Optional
from fastapi import UploadFile

from app.storage.session_storage import SessionStorage
from app.services.diarizer import Diarizer
from app.services.emotions_analysis_manager import EmotionsAnalysisManager
from app.db.session_db import SessionDB
from app.services.summarizer import Summarizer
from app.services.transcribe_with_diarization_manager import TranscribeAndDiarizeManager

class DialogueProcessor:
    def __init__(self):
        self.session_storage = SessionStorage()
        self.session_db = SessionDB()
        self.transcriber = TranscribeAndDiarizeManager()
        self.diarizer = Diarizer()
        self.emotion_analyzer = EmotionsAnalysisManager()
        self.summarizer = Summarizer()
        self._saved_audio_path = None
        self.session_id = None

    def upload_audio_file(self, file: UploadFile) -> tuple[str, str]:
        if not file:
            raise ValueError("File must be provided.")

        # 🆔 Generate a unique session ID
        session_id = str(uuid.uuid4())

        # ☁️ Upload audio and return blob path
        blob_path = self.session_storage.store_audio(session_id, file)

        # 🔐 Store for later use (e.g., in process_audio)
        self.session_id = session_id
        self._saved_audio_path = blob_path

        return session_id, blob_path

    def process_audio(self, session_id: str, audio_path: Optional[str] = None):
        path_to_use = audio_path or self._saved_audio_path
        if not path_to_use:
            raise ValueError("No audio path provided or saved for processing.")

        print(f"📥 Processing audio: {path_to_use}")
        self.session_db.set_status(session_id, "transcript_status", "processing")

        try:
            transcript_blob_name = self.transcriber.transcribe(path_to_use, session_id)
            # transcript_blob = self.session_storage.store_transcript(session_id, transcript_blob_name)
            self.session_db.set_status(session_id, "transcript_url", transcript_blob_name)
            self.session_db.set_status(session_id, "transcript_status", "completed")
            print("✅ Transcription complete.")
        except Exception as e:
            self.session_db.set_status(session_id, "transcript_status", "failed")
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"❌ Transcription failed: {e}")
            return

        self.session_db.set_status(session_id, "emotion_breakdown_status", "processing")

        try:
            emotion_json = self.emotion_analyzer.analyze(transcript_blob, session_id)
            emotion_blob = self.session_storage.store_emotions(session_id, emotion_json)
            self.session_db.set_status(session_id, "emotion_breakdown_url", emotion_blob)
            self.session_db.set_status(session_id, "emotion_breakdown_status", "completed")
            print("✅ Emotion complete.")
        except Exception as e:
            self.session_db.set_status(session_id, "emotion_breakdown_status", "failed")
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"❌ Emotion failed: {e}")
            return

        speaker_ids = list(emotion_json.keys())

        try:
            self.session_db.set_status(session_id, "participants", list(set(speaker_ids)))
        except Exception as e:
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"Set participants in sessions DB failed: {e}")
            return

        self.session_db.set_status(session_id, "summary_status", "processing")

        try:
            summary_text = self.summarizer.generate(transcript_blob, emotion_json, speaker_ids)
            summary_blob = self.session_storage.store_summary(session_id, summary_text)
            self.session_db.set_status(session_id, "summary_url", summary_blob)
            self.session_db.set_status(session_id, "summary_status", "completed")
            print("✅ Summarization complete.")
        except Exception as e:
            self.session_db.set_status(session_id, "summary_status", "failed")
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"❌ Summarization failed: {e}")
            return

        try:
            self.session_db.set_status(session_id, "session_status", "completed")
            print("✅ Processing complete and saved to DB.")
        except Exception as e:
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"❌ Failed to save session data: {e}")
