from __future__ import annotations

from app.logic.dialogueDNA.adapters.capability_adapters import RepoSessionUpdater, StorageArtifactWriter
from app.logic.dialogueDNA.events.subscribers.blob_artifacts import BlobArtifactsSubscriber
from app.logic.dialogueDNA.events.subscribers.db_progress import DBProgressSubscriber
from app.logic.dialogueDNA.interfaces.capabilities import PipelineContext
from app.logic.dialogueDNA.reporter import PipelineReporter
from app.state.app_states import DatabaseState, StorageState


class ReporterFactory:
    def __init__(self, database: DatabaseState, storage: StorageState):
        self.database = database
        self.storage = storage

    def for_session(
        self,
        session_id: str,
        *,
        inline_save: bool = False,
        dispatch: str = "thread",
        base_prefix: str = "sessions"
    ) -> PipelineReporter:

        reporter = PipelineReporter(dispatch=dispatch)

        sessions = RepoSessionUpdater(self.database.sessions_repo)

        reporter.subscribe(DBProgressSubscriber(inline_save=inline_save),
                      PipelineContext(session_id=session_id, sessions=sessions))

        artifacts = StorageArtifactWriter(self.storage.client)

        reporter.subscribe(BlobArtifactsSubscriber(base_prefix=base_prefix),
                      PipelineContext(session_id=session_id, sessions=sessions, artifacts=artifacts))

        return reporter
