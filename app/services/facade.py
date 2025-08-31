import uuid
import logging
logger = logging.getLogger(__name__)

from typing import Optional
from fastapi import UploadFile

from app.db.session_db import SessionDB
from app.storage.session_storage import SessionStorage

from app.services.transcript.transcriber import Transcriber
from app.services.emotions.emotion_controller import EmotionController
from app.services.summary.summarizer import Summarizer
from app.services.summary.prompts import PromptStyle

from app.services.audio.processor.audio_processor import AudioProcessor

class DialogueProcessor:
    def __init__(self):
        self.session_db = SessionDB()
        self.session_storage = SessionStorage()

        #new by Yarden
        self.audio_processor = AudioProcessor()

        self.transcriber = Transcriber()

        #todo: do it right now analysis only from text ans the merge..
        self.emotion_analyzer = EmotionController()
        self.summarizer = Summarizer()

        self._saved_audio_path = None
        self.session_id = None

    async def upload_audio_file(self, file: UploadFile) -> tuple[str, str]:
        if not file:
            raise ValueError("File must be provided.")

        #new by Yarden
        # 🎙️ Prepare audio (convert if needed)
        ready_path, meta = await self.audio_processor.prepare(file)

        # 🆔 Generate a unique session ID
        session_id = str(uuid.uuid4())

        # ☁️ Upload audio and return blob path
        blob_path = self.session_storage.store_audio(session_id, ready_path)

        # 🔐 Store for later use (e.g., in process_audio)
        self.session_id = session_id
        self._saved_audio_path = blob_path

        #new by Yarden
        # 📝 Log audio details
        logger.info(
            f"Audio uploaded (session={session_id}): "
            f"codec={meta['codec']}, sr={meta['sample_rate']}, "
            f"channels={meta['channels']}, duration={meta['duration_sec']:.1f}s, "
            f"converted={meta['was_converted']} reason={meta['reason']}"
        )

        #new by Yarden
        # 🧹 Cleanup temp file
        try:
            ready_path.unlink(missing_ok=True)
        except Exception:
            pass

        return session_id, blob_path

    def process_audio(self, session_id: str, audio_path: Optional[str] = None):
        audio_blob_path = audio_path or self._saved_audio_path

        if not audio_blob_path:
            raise ValueError("No audio path provided or saved for processing.")

        print(f"📥 Processing audio: {audio_blob_path}")

        # ----------------------------- Session Initialization -----------------------------
        self.session_db.set_status(session_id, "summary_status", "processing")

        # ----------------------------- Transcription -----------------------------
        self.session_db.set_status(session_id, "transcript_status", "processing")

        try:
            transcript_json = self.transcriber.transcribe(audio_blob_path)
            transcript_blob_path = self.session_storage.store_transcript(session_id, transcript_json)
            self.session_db.set_status(session_id, "transcript_url", transcript_blob_path)
            self.session_db.set_status(session_id, "transcript_status", "completed")
            print("✅ Transcription complete.")
        except Exception as e:
            self.session_db.set_status(session_id, "transcript_status", "failed")
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"❌ Transcription failed: {e}")
            return

        # ----------------------------- More Metadata Identification -----------------------------

        try:
            self.session_db.set_status(session_id, "participants", self.transcriber.participants)
            self.session_db.set_status(session_id, "duration", self.transcriber.duration_seconds)
        except Exception as e:
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"Set participants in sessions DB failed: {e}")
            return

        # ----------------------------- Emotion Analysis -----------------------------
        self.session_db.set_status(session_id, "emotion_breakdown_status", "processing")

        try:
            emotion_json = self.emotion_analyzer.get_emotions(transcript=transcript_json, audio_path=audio_blob_path)
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

        # ----------------------------- Summarization -----------------------------
        self.session_db.set_status(session_id, "summary_status", "processing")

        try:
            summary_text = self.summarizer.summarize(transcript_json, emotion_json, PromptStyle.EMOTIONAL_STORY)
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

        # ----------------------------- Saving Session Status -----------------------------
        try:
            self.session_db.set_status(session_id, "session_status", "completed")
            print("✅ Processing complete and saved to DB.")
        except Exception as e:
            self.session_db.set_status(session_id, "session_status", "failed")
            self.session_db.set_status(session_id, "processing_error", str(e))
            print(f"❌ Failed to save session data: {e}")