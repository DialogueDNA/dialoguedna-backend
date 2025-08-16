from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.bootstrap.wire_app import wire_app
from app.core.config import AppConfig
from app.logic.dialogue_dna import DialogueDNALogic

log = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app_state = wire_app(AppConfig())
        app.state.app = app_state
        app.state.logic = DialogueDNALogic(app_state)
        log.info("App wired successfully")
        yield
    except Exception as e:
        log.exception("Wiring failed: %s", e)
        raise
    finally:
        log.info("App shutdown complete")