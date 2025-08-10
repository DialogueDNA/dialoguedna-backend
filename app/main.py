# app/main.py
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router as api_router
from app.bootstrap.wire_db import wire_db
from app.bootstrap.wire_storage import wire_storage
from app.settings.logging import setup_logging
from app.settings.config import AppConfig
from app.state.types import DBState, StorageState

setup_logging()
log = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    config = AppConfig()
    app.state.config = config

    app.state.db = DBState()
    app.state.storage = StorageState()

    try:
        wire_db(app.state.db, config.db)
        wire_storage(app.state.storage, config.storage)
        # wire_services(app, config)

        log.info("App wired successfully")
        yield
    except Exception as e:
        log.exception("Wiring failed: %s", e)
        raise
    finally:
        log.info("App shutdown complete")

app = FastAPI(title="DialogueDNA Backend", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router)

# Healthcheck
@app.get("/health", tags=["meta"])
def health():
    return {"ok": True}
