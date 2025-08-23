from __future__ import annotations
import json
from typing import Any, Mapping, Optional, Dict, List

from app.interfaces.storage.blob_storage import BlobStorage
from app.logic.dialogueDNA.interfaces.capabilities import SessionUpdater, ArtifactWriter

# Wrap a repo to expose only "update"
class RepoSessionUpdater(SessionUpdater):
    def __init__(self, sessions_repo):
        self._repo = sessions_repo
    def update(self, session_id: str, updates: Mapping[str, Any]) -> Any:
        return self._repo.update(session_id, dict(updates))

# Wrap a blob client to expose only "put_json_get_url"
class StorageArtifactWriter(ArtifactWriter):
    def __init__(self, blob_storage: BlobStorage):
        self.blob_storage = blob_storage

    def put_json_get_url(self, container: str, blob: str, some_json: List[Dict[str, Any]]) -> Optional[str]:
        data = json.dumps(some_json, ensure_ascii=False).encode("utf-8")
        self.blob_storage.upload(container=container, blob=blob, data=data)
        return None
