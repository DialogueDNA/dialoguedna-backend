from __future__ import annotations

from app.bootstrap.services.wire_services import wire_services
from app.bootstrap.wire_app import wire_app

"""
app/services/factory.py

Scalable, plugin-driven factory for wiring the application services.

Key ideas:
- **Zero `if/else` dispatch**: selection is done via registries (dict lookups) and exceptions.
- **Composable builders**: each service has a small builder that can be swapped via plugins.
- **Thread-safe singleton per-config**: heavy resources (models, clients) are reused.

This module returns a ready-to-use `ServicesAPI` instance that exposes high-level
operations while keeping the wiring decoupled and testable.
"""

from dataclasses import dataclass
from threading import RLock
from typing import Callable, Dict, Optional

from app.services.authz import AuthZ
from app.core.config import AppConfig
from app.state.app_states import DatabaseState, StorageState, TranscriptionState, ServicesState, AppState
from app.bootstrap.database.wire_database import wire_database
from app.bootstrap.storage.wire_storage import wire_storage
from app.services.transcription.plugins import TRANSCRIBER_PLUGINS as T_PLUGINS, TranscriberPlugin  # backend -> builder
from app.services.emotions.emotioner import Emotioner
from app.services.summary.summarizer import Summarizer
from app.services.api import ServicesAPI
from app.ports.services.transcription.transcriber import Transcriber


# =============================== Internal types ===============================

@dataclass(frozen=True)
class ServicesBundle:
    """
    Immutable container of the wired services. This is kept small on purpose.
    """

    transcriber: Transcriber
    emotioner: Emotioner
    summarizer: Summarizer

    api: ServicesAPI


# =============================== Factory ===============================

class ServicesFactory:
    """
    Thread-safe, cache-per-config factory.

    - The cache key is derived from the minimal set of choices that influence
      the built graph (DB backend(s), storage backend, transcriber backend).
    - No `if/else` branching: lookups are performed through registries and
      missing entries raise explicit errors.
    """

    _lock: RLock = RLock()
    _cache: Dict[str, ServicesBundle] = {}

    @classmethod
    def get(cls, cfg: AppConfig, *, reload: bool = False) -> ServicesBundle:
        """
        Build (or fetch from cache) the wired services for the given config.

        Args:
            cfg: Application config.
            reload: When True, rebuilds and overwrites any cached instance.

        Returns:
            ServicesBundle with an initialized `ServicesAPI`.
        """
        key = cls._cache_key(cfg)
        with cls._lock:
            try:
                return cls._cache[key] if not reload else cls._rebuild(cfg, key)
            except KeyError:
                return cls._rebuild(cfg, key)

    # ---------- internals ----------

    @staticmethod
    def _cache_key(cfg: AppConfig) -> str:
        """
        Deterministic string that captures the service selection surface.
        """
        # Avoid referencing optional configs that may be commented out.
        t_backend = cfg.services.transcription.main_transcripter
        db = cfg.database.main_database
        st = cfg.storage.main_storage
        return f"database={db}|storage={st}|transcriber={t_backend}"

    @classmethod
    def _rebuild(cls, cfg: AppConfig, key: str) -> ServicesBundle:
        """
        Rebuild the full dependency graph for the given config.
        """

        # Application state
        app = AppState()

        # Wire infrastructure
        wire_app(app, cfg)

        # Optional user defaults loader (safe if repo is not present)
        def load_user_defaults(user_id: str) -> dict:
            try:
                data = db.user_defaults_repo.get(user_id)  # type: ignore[attr-defined]
            except AttributeError:
                data = None
            return data or {}

        # RBAC
        authz = AuthZ(policy=cfg.policy.POLICY)

        logic = DialogueDNALogic(
            database=app.database,
            storage=app.storage,
            services=app.services,
        )

        api = ServicesAPI(
            logic=logic,
            load_user_defaults=load_user_defaults,
            authz=authz,
        )

        bundle = ServicesBundle(
            api=api,
            transcriber=logic.transcriber,
            emotioner=logic.emotioner,
            summarizer=logic.summarizer,
        )

        cls._cache[key] = bundle
        return bundle


# =============================== Public entry points ===============================

def get_services_api(cfg: AppConfig, *, reload: bool = False) -> ServicesAPI:
    """
    Convenience function: returns only the high-level API.
    """
    return ServicesFactory.get(cfg, reload=reload).api
