# app/main.py
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router as api_router
from app.bootstrap.wire_db import wire_db
from app.settings.logging import setup_logging
from app.settings.config import AppConfig

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    config = AppConfig()
    app.state.config = config
    wire_db(app, config)
    # wire_storage(app, config)
    # wire_services(app, config)
    yield

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
