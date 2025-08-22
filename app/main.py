from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import router as api_router
from app.core.logging import setup_logging
from app.state.lifespan import lifespan

setup_logging()

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
