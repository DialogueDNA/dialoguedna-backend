from __future__ import annotations

import uuid
from typing import Dict, Optional, List

from app.application.queues import TaskQueue
from app.core.constants.db.supabase_constants import SessionColumn, SessionStatus
from app.core.constants.storage.azure_constants import MAIN_CONTAINER
from app.interfaces.logic.pipeline import PipelineInput
from app.interfaces.services.emotions import EmotionAnalyzerBundle
from app.interfaces.services.text import TextSegment
from app.logic.DialogueDNA.adapters.capability_adapters import StorageArtifactWriter, StorageArtifactReader
from app.logic.DialogueDNA.pipeline import DialogueDNAPipeline
from app.models.session import SessionDB
from app.state.app_states import AppState

from app.logic.DialogueDNA.reporter_factory import DialogueDNAPipelineReporterFactory

class ApplicationFacade:
    """
    Application Facade / Use-case layer for session workflows.
    Keeps domain (DialogueDNALogic) pure and orchestrates cross-cutting concerns
    like reporting, storage uploads, and DB status updates.
    """

    def __init__(self, app: AppState):
        self._app = app
        self._logic = DialogueDNAPipeline(app.services)
        self._reporter = DialogueDNAPipelineReporterFactory(app.database, app.storage)

        self._write = StorageArtifactWriter(app.storage.client)
        self._reader = StorageArtifactReader(app.storage.client)

    # ------------------------------------ Create ------------------------------------

    # ---------- Full Pipeline ----------

    def create_and_analyze(
            self,
            user_id: str,
            title: str,
            audio_local_path: str,
            *,
            inline_save: bool = False,
            dispatch: str = "thread",
            queue: TaskQueue
    )-> SessionDB | None:

        session_id, audio_blob_path = self.create_new_session(
            user_id=user_id,
            title=title,
            audio_local_path=audio_local_path
        )
        return self.analyze_session_dna(
            session_id=session_id,
            user_id=user_id,
            audio_path=audio_blob_path,
            inline_save=inline_save,
            dispatch=dispatch,
            queue=queue
        )

    def create_new_session(
            self,
            user_id: str,
            title: str,
            audio_local_path: str) -> tuple[str, str]:

        session_id = str(uuid.uuid4())

        blob_url: str = self._write.put_wav_path_get_url(
            container="sessions",
            blob="audio.wav",
            some_wav_path=audio_local_path
        )

        record = {
            SessionColumn.session_id: session_id,
            SessionColumn.user_id: user_id,
            SessionColumn.title: title,
            SessionColumn.audio_file_url: blob_url,
        }
        self._app.database.sessions_repo.create(record)
        return session_id, blob_url

    def analyze_session_dna(
            self,
            session_id: str,
            user_id: str,
            *,
            audio_path: str = None,
            inline_save: bool = False,
            dispatch: str = "thread",
            queue: TaskQueue = None,
    ) -> SessionDB | None:

        # If audio_path is None, try to find it in the database
        if not audio_path:
            session = self._app.database.sessions_repo.get_for_user(session_id=session_id, user_id=user_id)
            if not session:
                raise ValueError("Session not found")
            audio_path = session.get(SessionColumn.audio_file_url, None)
            if not audio_path:
                raise ValueError("Audio file path not found")

        if queue is None:
            # Analyze in synchronize way
            self._run_full_pipeline(
                session_id=session_id,
                audio_path=audio_path,
                inline_save=inline_save,
                dispatch=dispatch
            )
        else:
            #  Analyze in asynchronize way - Enqueue job (pure function signature -> serializable for external queues)
            queue.enqueue(
                self._run_full_pipeline,
                self._app,
                session_id,
                audio_path,
                inline_save,
                dispatch,
            )

        return self._app.database.sessions_repo.get_for_user(session_id, user_id)

    def _run_full_pipeline(
            self,
            session_id: str,
            audio_path: str,
            inline_save: bool,
            dispatch: str,
    ) -> None:

        # Build new session reporter
        reporter = self._reporter.for_session(
            session_id=session_id,
            inline_save=inline_save,
            dispatch=dispatch,
        )

        # Run DialogueDNA
        pipeline_results = self._logic.run(PipelineInput(audio=audio_path, reporter=reporter))

        # # (Optional) Final update in case we didn't provide reporter
        # patch = {
        #     "status": "ready",
        #     "transcript":
        #         [
        #             {
        #                 "writer": s.writer,
        #                 "text": s.text,
        #                 "start": s.start_time,
        #                 "end": s.end_time
        #             }
        #             for s in pipeline_results.transcription
        #         ]
        #         if inline_save else None,
        #     "emotions":
        #         [
        #             {
        #                 "whom": s.whom,
        #                 "start": s.start_time,
        #                 "end": s.end_time,
        #                 "text": s.text,
        #                 "audio": s.audio,
        #                 "mixed": s.mixed
        #             }
        #             for s in pipeline_results.emotion_analysis
        #         ]
        #         if inline_save else None,
        #     "summary":
        #         [
        #             {
        #                 "summary": pipeline_results.summarization.summary,
        #                 "bullets": pipeline_results.summarization.bullets,
        #                 "per_speaker": pipeline_results.summarization.per_speaker,
        #                 "usage": pipeline_results.summarization.usage,
        #             }
        #         ]
        #         if inline_save else None,
        # }
        #
        # # Remove nones from patch
        # patch = {k: v for k, v in patch.items() if v is not None}
        # if patch:
        #     self.app.database.sessions_repo.update(session_id, patch)

    # ------------------------------------ Update ------------------------------------

    # ---------- Rebuilders ----------

    # REBUILD: only transcript on existing audio
    def rebuild_transcript(self, *, session_id: str, user_id: str) -> str | None:

        audio_blob_path = self.get_audio_url(
            session_id=session_id,
            user_id=user_id
        )

        if not audio_blob_path:
            raise ValueError("Audio file path not found")

        # TODO: Download blob to temp file
        audio_local_path = audio_blob_path

        reporter = self._reporter.for_session(session_id=session_id)

        self._logic.transcribe(
            audio=audio_local_path,
            reporter=reporter
        )

        return self._app.database.sessions_repo.get_for_user(session_id, user_id).transcript_url

    # REBUILD: only emotions on existing audio and transcript
    def rebuild_emotions(self, *, session_id: str, user_id: str) -> str | None:

        audio_blob_path = self.get_audio_url(
            session_id=session_id,
            user_id=user_id
        )

        if not audio_blob_path:
            raise ValueError("Audio file path not found")

        # TODO: Download blob to temp file
        audio_local_path = audio_blob_path

        transcription_url = self.get_transcript_url(
            session_id=session_id,
            user_id=user_id
        )

        if not transcription_url:
            transcription_url = self.rebuild_transcript(
                session_id=session_id,
                user_id=user_id
            )

        try:
            transcription = self._reader.load_many(
                container=MAIN_CONTAINER,
                blob=transcription_url,
                cls=TextSegment
            )
        except Exception as e:
            raise ValueError("Failed to download transcription: {}".format(e))

        reporter = self._reporter.for_session(session_id=session_id)

        self._logic.analyze_emotions_on_transcript(
            audio=audio_local_path,
            transcription=transcription,
            reporter=reporter
        )

        return self._app.database.sessions_repo.get_for_user(session_id, user_id).emotion_breakdown_url

    # REBUILD: only summary on existing audio, transcript and emotions
    def rebuild_summary(self, *, session_id: str, user_id: str, style: str, max_token: Optional[int] = None,
                        language_hint: Optional[str] = None, inline_save: bool = False,
                        per_speaker: Optional[bool] = None, bullets: Optional[bool] = None,
                        metadata: Optional[Dict[str, str]] = None
                        ) -> SessionDB | None:

        analyzed_emotions_url = self.get_analyzed_emotions_url(
            session_id=session_id,
            user_id=user_id,
        )

        if not analyzed_emotions_url:
            analyzed_emotions_url = self.rebuild_emotions(
                session_id=session_id,
                user_id=user_id,
            )

        try:
            analyzed_emotions = self._reader.load_many(
                container=MAIN_CONTAINER,
                blob=analyzed_emotions_url,
                cls=EmotionAnalyzerBundle
            )
        except Exception as e:
            raise ValueError("Failed to download analyzed emotions: {}".format(e))

        self._logic.summarize(
            segments=analyzed_emotions,
            style=style,
            max_tokens=max_token,
            language=language_hint,
            per_speaker=per_speaker,
            bullets=bullets,
            metadata=metadata
        )

        return self._app.database.sessions_repo.get_for_user(session_id, user_id)

    # ------------------------------------ Read ------------------------------------

    def get_session(self, session_id: str, user_id: str):
        session = self._app.database.sessions_repo.get_for_user(session_id=session_id, user_id=user_id)

        if not session:
            raise ValueError("Session not found")

        return session

    def get_sessions(self, user_id: str) -> List[SessionDB] | None:
        return self._app.database.sessions_repo.list_for_user(user_id)

    def get_audio_url(self, session_id: str, user_id: str) -> str | None:
        session = self.get_session(session_id=session_id, user_id=user_id)

        audio_status: SessionStatus = session.get(SessionColumn.audio_file_status, None)

        if audio_status is not SessionStatus.completed:
            return None

        audio_file_url: str = session.get(SessionColumn.audio_file_url, None)

        if not audio_file_url:
            raise ValueError("audio file url not found")

        return audio_file_url

    def get_audio_view(self, session_id: str, user_id: str) -> dict:

        audio_status, audio_url = self.get_audio_url(session_id=session_id, user_id=user_id)

        sas_url, expires_at = self._app.storage.client.generate_read_sas_from_url(blob_url=audio_url)

        return {
            "status": audio_status,
            "result": {
                "blob_path": audio_url,
                "sas_url": sas_url,
                "expires_at": expires_at
            }
        }

    def get_transcript_url(self, session_id: str, user_id: str) -> tuple[SessionStatus, Optional[str]]:

        session = self.get_session(session_id=session_id, user_id=user_id)

        transcript_status: SessionStatus = session.get(SessionColumn.transcript_status, None)

        if transcript_status is not SessionStatus.completed:
            return transcript_status, None

        transcript_url: str = session.get(SessionColumn.transcript_url, None)

        if not transcript_url:
            raise ValueError("transcript url not found")

        return transcript_status, transcript_url

    def get_transcript_view(self, session_id: str, user_id: str) -> dict:

        transcript_status, transcript_url = self.get_transcript_url(session_id=session_id, user_id=user_id)

        sas_url, expires_at = self._app.storage.client.generate_read_sas_from_url(blob_url=transcript_url)

        return {
            "status": transcript_status,
            "result": {
                "blob_path": transcript_url,
                "sas_url": sas_url,
                "expires_at": expires_at
            }
        }

    def get_analyzed_emotions_url(self, session_id: str, user_id: str) -> tuple[SessionStatus, Optional[str]]:

        session = self.get_session(session_id=session_id, user_id=user_id)

        analyzed_emotions_status: SessionStatus = session.get(SessionColumn.emotion_breakdown_status, None)

        if analyzed_emotions_status is not SessionStatus.completed:
            return analyzed_emotions_status, None

        analyzed_emotions_url: str = session.get(SessionColumn.emotion_breakdown_url, None)

        if not analyzed_emotions_url:
            raise ValueError("analyzed emotions url not found")

        return analyzed_emotions_status, analyzed_emotions_url

    def get_analyzed_emotions_view(self, session_id: str, user_id: str) -> dict:

        analyzed_emotions_status, analyzed_emotions_url = self.get_analyzed_emotions_url(session_id=session_id, user_id=user_id)

        sas_url, expires_at = self._app.storage.client.generate_read_sas_from_url(blob_url=analyzed_emotions_url)

        return {
            "status": analyzed_emotions_status,
            "result": {
                "blob_path": analyzed_emotions_url,
                "sas_url": sas_url,
                "expires_at": expires_at
            }
        }

    def get_summary_url(self, session_id: str, user_id: str) -> tuple[SessionStatus, Optional[str]]:

        session = self.get_session(session_id=session_id, user_id=user_id)

        summary_status: SessionStatus = session.get(SessionColumn.summary_status, None)

        if summary_status is not SessionStatus.completed:
            return summary_status, None

        summary_url: str = session.get(SessionColumn.summary_url, None)

        if not summary_url:
            raise ValueError("analyzed emotions url not found")

        return summary_status, summary_url

    def get_summary_view(self, session_id: str, user_id: str) -> dict:

        summary_status, summary_url = self.get_summary_url(session_id=session_id, user_id=user_id)

        sas_url, expires_at = self._app.storage.client.generate_read_sas_from_url(blob_url=summary_url)

        return {
            "status": summary_status,
            "result": {
                "blob_path": summary_url,
                "sas_url": sas_url,
                "expires_at": expires_at
            }
        }

    # ------------------------------------ Delete ------------------------------------

    def delete_session(self, session_id: str, user_id: str):
        return self._app.database.sessions_repo.delete(session_id)

