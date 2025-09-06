from __future__ import annotations

import uuid
from typing import Dict, Optional, List

from sqlalchemy.exc import NoResultFound

from app.application.queues import TaskQueue
from app.core.constants.db.supabase_constants import SessionColumn, SessionStatus
from app.core.constants.storage.azure_constants import MAIN_CONTAINER, SESSION_TRANSCRIPT_PATH, SESSION_SUMMARY_PATH, \
    SESSION_EMOTIONS_PATH, SESSION_AUDIO_PATH
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
            audio_path=audio_local_path,
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
        # Build new session reporter

        blob_url: str = self._write.put_wav_path_get_url(
            container="sessions",
            blob=f"{session_id}/audio.wav",
            some_wav_path=audio_local_path
        )

        record = {
            SessionColumn.session_id: session_id,
            SessionColumn.user_id: user_id,
            SessionColumn.title: title,
            SessionColumn.audio_file_status: SessionStatus.completed,
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
            self._delete_tmp_file(audio_path)
        else:
            #  Analyze in asynchronize way - Enqueue job (pure function signature -> serializable for external queues)
            queue.enqueue(
                self._run_full_pipeline,
                session_id,
                audio_path,
                inline_save,
                dispatch,
            )

            queue.enqueue(
                self._delete_tmp_file,
                audio_path
            )
        return self._app.database.sessions_repo.get_for_user(session_id, user_id)

    @staticmethod
    def _delete_tmp_file(file_path: str) -> None:
        import os
        try:
            os.remove(file_path)
        except Exception:
            pass

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

    def get_session(self, session_id: str, user_id: str) -> SessionDB:
        session: SessionDB = self._app.database.sessions_repo.get_for_user(session_id=session_id, user_id=user_id)

        if not session:
            raise ValueError("Session not found")

        return session

    def get_sessions(self, user_id: str) -> List[SessionDB] | None:
        return self._app.database.sessions_repo.list_for_user(user_id)

    def get_audio_url(self, session_id: str, user_id: str) -> tuple[SessionStatus, Optional[str]]:
        session = self.get_session(session_id=session_id, user_id=user_id)

        audio_status: SessionStatus = SessionStatus(session.audio_file_status)

        if audio_status is not SessionStatus.completed:
            return audio_status, None

        audio_file_url: str = session.audio_file_url

        if not audio_file_url:
            raise ValueError("audio file url not found")

        return audio_status, audio_file_url

    def get_audio_view(self, session_id: str, user_id: str) -> dict:

        audio_status, audio_url = self.get_audio_url(session_id=session_id, user_id=user_id)

        sas_url, expires_at = self._app.storage.client.generate_read_sas_from_url(blob_url=audio_url) if audio_url else (None, None)

        return {
            "status": audio_status,
            "result": {
                "blob_path": audio_url,
                "sas_url": sas_url,
                "expires_at": expires_at
            } if audio_url else None
        }

    def get_transcript_url(self, session_id: str, user_id: str) -> tuple[SessionStatus, Optional[str]]:

        session = self.get_session(session_id=session_id, user_id=user_id)

        transcript_status: SessionStatus = SessionStatus(session.transcript_status)

        if transcript_status is not SessionStatus.completed:
            return transcript_status, None

        transcript_url: str = session.transcript_url

        if not transcript_url:
            raise ValueError("transcript url not found")

        return transcript_status, transcript_url

    def get_transcript_view(self, session_id: str, user_id: str) -> dict:

        transcript_status, transcript_url = self.get_transcript_url(session_id=session_id, user_id=user_id)

        sas_url, expires_at = self._app.storage.client.generate_read_sas_from_url(blob_url=transcript_url) if transcript_url else (None, None)

        return {
            "status": transcript_status,
            "result": {
                "blob_path": transcript_url,
                "sas_url": sas_url,
                "expires_at": expires_at
            } if transcript_url else None
        }

    def get_analyzed_emotions_url(self, session_id: str, user_id: str) -> tuple[SessionStatus, Optional[str]]:

        session: SessionDB = self.get_session(session_id=session_id, user_id=user_id)

        analyzed_emotions_status: SessionStatus = SessionStatus(session.emotion_breakdown_status)

        if analyzed_emotions_status is not SessionStatus.completed:
            return analyzed_emotions_status, None

        analyzed_emotions_url: str = session.emotion_breakdown_url

        if not analyzed_emotions_url:
            raise ValueError("analyzed emotions url not found")

        return analyzed_emotions_status, analyzed_emotions_url

    def get_analyzed_emotions_view(self, session_id: str, user_id: str) -> dict:

        analyzed_emotions_status, analyzed_emotions_url = self.get_analyzed_emotions_url(session_id=session_id, user_id=user_id)

        sas_url, expires_at = self._app.storage.client.generate_read_sas_from_url(blob_url=analyzed_emotions_url) if analyzed_emotions_url else (None, None)

        return {
            "status": analyzed_emotions_status,
            "result": {
                "blob_path": analyzed_emotions_url,
                "sas_url": sas_url,
                "expires_at": expires_at
            } if analyzed_emotions_url else None
        }

    def get_summary_url(self, session_id: str, user_id: str) -> tuple[SessionStatus, Optional[str]]:

        session = self.get_session(session_id=session_id, user_id=user_id)

        summary_status: SessionStatus = SessionStatus(session.summary_status)

        if summary_status is not SessionStatus.completed:
            return summary_status, None

        summary_url: str = session.summary_url

        if not summary_url:
            raise ValueError("analyzed emotions url not found")

        return summary_status, summary_url

    def get_summary_view(self, session_id: str, user_id: str) -> dict:

        summary_status, summary_url = self.get_summary_url(session_id=session_id, user_id=user_id)

        sas_url, expires_at = self._app.storage.client.generate_read_sas_from_url(blob_url=summary_url) if summary_url else (None, None)

        return {
            "status": summary_status,
            "result": {
                "blob_path": summary_url,
                "sas_url": sas_url,
                "expires_at": expires_at
            } if summary_url else None
        }

    # ------------------------------------ Delete ------------------------------------

    def delete_session(self, session_id: str, user_id: str, delete_blobs: bool) -> bool:
        try:
            session = self._app.database.sessions_repo.get_for_user(session_id=session_id, user_id=user_id)
        except Exception:
            raise ValueError("Session not found in user's sessions list")

        if session is None:
            raise ValueError("Session not found in user's sessions list")

        if delete_blobs:
            # Collect known artifact URLs, tolerate missing fields
            def get_field(obj, name: str):
                if hasattr(obj, name):
                    return getattr(obj, name)
                if isinstance(obj, dict):
                    return obj.get(name)
                return None

            blobs = [
                get_field(session, SESSION_AUDIO_PATH),
                get_field(session, SESSION_TRANSCRIPT_PATH),
                get_field(session, SESSION_EMOTIONS_PATH),
                get_field(session, SESSION_SUMMARY_PATH),
            ]

            # Remove Nones/duplicates
            seen = set()
            blobs = [u for u in blobs if u and (u not in seen and not seen.add(u))]
            for blob in blobs:
                try:
                    self._app.storage.client.delete(container=MAIN_CONTAINER, blob=blob)
                except Exception:
                    # Best-effort: don't block DB deletion if a blob fails to delete.
                    # Consider logging here if you have a logger.
                    pass

        try:
            deleted = self._app.database.sessions_repo.delete(session_id)
        except Exception:
            raise ValueError("session id not found")

        return deleted

    def delete_sessions(self, session_ids: list[str], user_id: str, delete_blobs: bool = False) -> int:
        """
        Delete multiple sessions of a user. Returns the number of targeted sessions.
        If delete_blobs=True, also deletes referenced storage blobs.
        """
        sessions = self._app.database.sessions_repo.list_for_user(user_id=user_id)

        targets = {sid for sid in (session_ids or []) if sid}
        if not targets:
            return 0

        def get_field(obj, name: str):
            return getattr(obj, name, None) if hasattr(obj, name) else (
                obj.get(name) if isinstance(obj, dict) else None)

        to_delete_ids: list[str] = []
        if delete_blobs:
            urls: set[str] = set()

        for s in sessions:
            sid = str(get_field(s, "id"))
            if sid in targets:
                to_delete_ids.append(sid)
                if delete_blobs:
                    for key in ("audio_url", "transcript_url", "emotions_url", "summary_url"):
                        u = get_field(s, key)
                        if u:
                            urls.add(u)

        if not to_delete_ids:
            return 0

        for delete_id in to_delete_ids:
            self.delete_session(session_id=delete_id, user_id=user_id, delete_blobs=delete_blobs)

        return len(to_delete_ids)

