from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.services.factory import get_services_api
from app.core.config import AppConfig

log = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = AppConfig()

    try:
        app.state = type("S", (), {})()
        app.state.services = get_services_api(cfg, reload=True)
        log.info("App wired successfully")
        yield
    except Exception as e:
        log.exception("Wiring failed: %s", e)
        raise
    finally:
        log.info("App shutdown complete")