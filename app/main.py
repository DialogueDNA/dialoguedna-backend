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
from app.api import endpoints

app = FastAPI(title="DialogueDNA Backend")

app.include_router(endpoints.router)
