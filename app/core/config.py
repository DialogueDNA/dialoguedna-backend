import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# === Load from .env file ===
load_dotenv()

# === Base project paths ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONVERSATION_ROOT = PROJECT_ROOT / "conversation_session"

# Timestamp for current run
TIMESTAMP = datetime.now().strftime("session_%Y-%m-%d_%H-%M-%S")
SESSION_DIR = CONVERSATION_ROOT / TIMESTAMP

# Subdirectories inside session
RECORDINGS_DIR = SESSION_DIR / "recording"
TRANSCRIPTS_DIR = SESSION_DIR / "processed" / "transcripts"
EMOTIONS_TEXT_DIR = SESSION_DIR / "processed" / "transcript_emotion_text"
SUMMARY_DIR = SESSION_DIR / "outputs" / "summary"

# === Azure Speech-to-Text credentials ===
SPEECH_KEY = os.getenv("SPEECH_KEY")
REGION = os.getenv("REGION")
AZURE_CONTAINER_URL = os.getenv("AZURE_CONTAINER_URL")

# === Azure Blob Storage ===
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")

# === Text-based emotion model ===
TEXT_EMOTION_MODEL = os.getenv("TEXT_EMOTION_MODEL", "j-hartmann/emotion-english-distilroberta-base")
TOP_K_EMOTIONS = os.getenv("TOP_K_EMOTIONS")  # can convert to int later if needed

# === Azure OpenAI for Summary Generation ===
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# === Superbase ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# === Audio settings ===
SAMPLE_RATE = 16000
CHUNK_DURATION_SEC = 5
OVERLAP_DURATION_SEC = 1.5