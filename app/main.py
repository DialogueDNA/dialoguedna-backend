"""
main.py

Entry point of the DialogueDNA backend service.
Initializes FastAPI, loads environment, adds middleware, and registers routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.endpoints import router as api_router

load_dotenv()

app = FastAPI(title="DialogueDNA Backend")

# CORS middleware (customize origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["https://your-frontend-domain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all API routers
app.include_router(api_router)
