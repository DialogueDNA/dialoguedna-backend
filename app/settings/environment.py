import os
from dotenv import load_dotenv

# === Load from .env file ===
load_dotenv()

# --- Core ---
DB_BACKEND = os.getenv("DB_BACKEND", "supabase").lower()
USERS_DB_BACKEND = os.getenv("USERS_DB_BACKEND", DB_BACKEND).lower()
SESSIONS_DB_BACKEND = os.getenv("SESSIONS_DB_BACKEND", DB_BACKEND).lower()

# === Azure Speech-to-Text credentials ===
AZURE_SPEECH_KEY = os.getenv("SPEECH_KEY")
AZURE_REGION = os.getenv("REGION")
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

# === Huggingface ===
HUGGINGFACE_WHISPERX_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

# Optional overrides
DEVICE = os.getenv("DEVICE")  # "cuda" | "cpu" | "mps" | None
WHISPERX_MODEL_SIZE = os.getenv("WHISPERX_MODEL_SIZE", "large-v2")
WHISPERX_COMPUTE_TYPE = os.getenv("WHISPERX_COMPUTE_TYPE", "int8")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
