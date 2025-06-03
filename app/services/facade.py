from typing import Optional

from fastapi import UploadFile

from app.services.db_loader import DBLoader
from app.services.diarizer import Diarizer
from app.services.emotion_analyzer import EmotionAnalyzer
from app.services.emotions_analysis_manager import EmotionsAnalysisManager
from app.services.sessionDB import SessionDB
from app.services.summarizer import Summarizer
from app.services.transcribe_with_diarization_manager import TranscribeAndDiarizeManager
from app.services.transcriber import Transcriber


class DialogueProcessor:
    def __init__(self):
        self.DBLoader = DBLoader()
        self.session_db = SessionDB()
        #self.transcriber = Transcriber()
        self.transcriber = TranscribeAndDiarizeManager()
        self.diarizer = Diarizer()
        self.emotion_analyzer = EmotionsAnalysisManager()
        self.summarizer = Summarizer()
        self._saved_audio_path = None

    def upload_audio_file_in_db(
        self,
        audio_path: Optional[str] = None,
        file: Optional[UploadFile] = None
    ) ->  tuple[str, str]:

        if file:
            self.session_id, self._saved_audio_path = self.DBLoader.load_audio_from_file(file)

        elif audio_path:
            self.session_id = None
            self._saved_audio_path = self.DBLoader.load_audio(audio_path)
        else:
            raise ValueError("Either 'audio_path' or 'file' must be provided.")

        return self.session_id, self._saved_audio_path


    def process_audio(self, session_id: str, audio_path: Optional[str] = None):
        path_to_use = audio_path or self._saved_audio_path
        if not path_to_use:
            raise ValueError("No audio path provided or saved for processing.")

        try:
            print(f"📥 Processing audio: {path_to_use}")

            self.session_db.set_status(session_id, "transcript_status", "processing")
            #transcriber_sas_url, speaker_ids, transcriber_blob_name = self.transcriber.transcribe(path_to_use,session_id)
            audio_blob_name, transcriber_sas_url, speaker_ids,transcriber_blob_name= self.transcriber.transcribe(path_to_use,session_id)
            print("✅ Transcription complete.")
            self.session_db.set_status(session_id, "transcript_status", "completed")

            self.session_db.set_status(session_id, "emotion_breakdown_status", "processing")
            # speaker_segments = self.diarizer.identify(path_to_use)
            emotions_url,emotions_blob_name = self.emotion_analyzer.analyze(transcriber_sas_url,session_id)
            print("✅ Diarization and emotion analysis complete.")
            self.session_db.set_status(session_id, "emotion_breakdown_status", "completed")

            #change summery with amal
            self.session_db.set_status(session_id, "summary_status", "processing")
            summary = self.summarizer.generate(transcriber_sas_url, emotions_url, speaker_ids)
            print("✅ Summarization complete.")
            self.session_db.set_status(session_id, "summary_status", "completed")

            print("✅ Transcription, diarization, emotion analysis, and summarization complete.")

            self.session_db.update_session(session_id, {
                "audio_file_url": audio_blob_name,
                "transcript": transcriber_blob_name,
                "participants": list(set(speaker_ids)),
                "emotion_breakdown": emotions_blob_name,
                "summary": summary,
                "status": "Ready",
                "processing_error": None
            })

            print("✅ Processing complete and saved to DB.")

        except Exception as e:
            print(f"❌ Processing failed: {e}")
            self.session_db.set_status(session_id, "Error", str(e))
