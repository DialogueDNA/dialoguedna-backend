from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.application.facade import ApplicationFacade
from app.bootstrap.wire_app import wire_app
from app.core.config import AppConfig

log = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app_state = wire_app(AppConfig())
        app.state.api = ApplicationFacade(app_state)
        log.info("App wired successfully")
        yield
    except Exception as e:
        log.exception("Wiring failed: %s", e)
        raise
    finally:
        log.info("App shutdown complete")