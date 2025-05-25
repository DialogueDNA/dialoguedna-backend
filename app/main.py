"""
main.py

This is the entry point of the DialogueDNA backend service.
It initializes the FastAPI app and includes the API router.

Responsibilities:
- Create and configure the FastAPI app
- Include routers from app.api
- Set up any global middlewares or startup events (in the future)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.sessions import router as sessions_router
from app.api.endpoints.uploads import router as uploads_router

load_dotenv()

app = FastAPI(title="DialogueDNA Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
app.include_router(uploads_router, prefix="/upload", tags=["upload"])

