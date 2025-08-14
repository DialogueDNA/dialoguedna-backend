import uuid
from typing import Optional
from fastapi import UploadFile

from app.database.session_db import SessionDB
from app.services.transcription.factory import make_transcriber
from app.storage.session_storage import SessionStorage

from app.services.emotions.emotioner import Emotioner
from app.services.summary.summarizer import Summarizer
from app.services.summary.prompts import PromptStyle

import app.core.constants.db.supabase_constants as db_constants

class DialogueProcessor:
    def __init__(self):
        self.session_db = SessionDB()
        self.session_storage = SessionStorage()

        self.transcriber = make_transcriber("whisperx")
        self.emotion_analyzer = Emotioner()
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
        audio_blob_path = audio_path or self._saved_audio_path

        if not audio_blob_path:
            raise ValueError("No audio path provided or saved for processing.")

        print(f"📥 Processing audio: {audio_blob_path}")

        # ----------------------------- Session Initialization -----------------------------
        self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_STATUS, "processing")

        # ----------------------------- Transcription -----------------------------
        self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_TRANSCRIPT_STATUS, "processing")

        try:
            transcript_json = self.transcriber.transcribe(audio_blob_path)
            transcript_blob_path = self.session_storage.store_transcript(session_id, transcript_json)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_TRANSCRIPT_URL, transcript_blob_path)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_TRANSCRIPT_STATUS, db_constants.SESSION_STATUS_COMPLETED)
            print("✅ Transcription complete.")
        except Exception as e:
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_TRANSCRIPT_STATUS, db_constants.SESSION_STATUS_FAILED)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_STATUS, db_constants.SESSION_STATUS_FAILED)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_PROCESSING_ERROR, str(e))
            print(f"❌ Transcription failed: {e}")
            return

        # ----------------------------- More Metadata Identification -----------------------------

        try:
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_PARTICIPANTS, self.transcriber.participants)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_DURATION, self.transcriber.duration_seconds)
        except Exception as e:
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_STATUS, db_constants.SESSION_STATUS_FAILED)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_PROCESSING_ERROR, str(e))
            print(f"Set participants in sessions DB failed: {e}")
            return

        # ----------------------------- Emotion Analysis -----------------------------
        self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_EMOTION_BREAKDOWN_STATUS, db_constants.SESSION_STATUS_PROGRESSING)

        try:
            emotion_json = self.emotion_analyzer.get_emotions(transcript_json)
            emotion_blob = self.session_storage.store_emotions(session_id, emotion_json)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_EMOTION_BREAKDOWN_URL, emotion_blob)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_EMOTION_BREAKDOWN_STATUS, db_constants.SESSION_STATUS_COMPLETED)
            print("✅ Emotion complete.")
        except Exception as e:
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_EMOTION_BREAKDOWN_STATUS, db_constants.SESSION_STATUS_FAILED)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_STATUS, db_constants.SESSION_STATUS_FAILED)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_PROCESSING_ERROR, str(e))
            print(f"❌ Emotion failed: {e}")
            return

        # ----------------------------- Summarization -----------------------------
        self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_SUMMARY_STATUS, db_constants.SESSION_STATUS_PROGRESSING)

        try:
            summary_text = self.summarizer.summarize(transcript_json, emotion_json, PromptStyle.EMOTIONAL_STORY)
            summary_blob = self.session_storage.store_summary(session_id, summary_text)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_SUMMARY_URL, summary_blob)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_SUMMARY_STATUS, db_constants.SESSION_STATUS_COMPLETED)
            print("✅ Summarization complete.")
        except Exception as e:
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_SUMMARY_STATUS, db_constants.SESSION_STATUS_FAILED)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_STATUS, db_constants.SESSION_STATUS_FAILED)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_PROCESSING_ERROR, str(e))
            print(f"❌ Summarization failed: {e}")
            return

        # ----------------------------- Saving Session Status -----------------------------
        try:
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_STATUS, db_constants.SESSION_STATUS_COMPLETED)
            print("✅ Processing complete and saved to DB.")
        except Exception as e:
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_STATUS, db_constants.SESSION_STATUS_FAILED)
            self.session_db.set_status(session_id, db_constants.SESSIONS_COLUMN_PROCESSING_ERROR, str(e))
            print(f"❌ Failed to save session data: {e}")