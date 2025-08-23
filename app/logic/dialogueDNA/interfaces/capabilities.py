from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Mapping, Any, Optional, List, Dict


# ---- Minimal write capability for sessions ----
class SessionUpdater(Protocol):
    def update(self, session_id: str, updates: Mapping[str, Any]) -> Any: ...

# ---- Minimal artifact writer for blobs ----
class ArtifactWriter(Protocol):
    def put_json_get_url(self, container: str, blob: str, some_json: List[Dict[str, Any]]) -> Optional[str]: ...

# ---- Per-run context with only the least privileges needed ----
@dataclass(frozen=True)
class PipelineContext:
    session_id: str
    sessions: SessionUpdater                      # required
    artifacts: Optional[ArtifactWriter] = None    # optional
