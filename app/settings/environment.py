import os
from dotenv import load_dotenv

# === Load from .env file ===
load_dotenv()

# ============================ Core ============================
DB_BACKEND = os.getenv("DB_BACKEND", "supabase").lower()
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "azure_blob").lower()


# ============================ Database Settings ============================

# === Superbase Settings ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# === Database Domain Settings ===
USERS_DB_BACKEND = os.getenv("USERS_DB_BACKEND", DB_BACKEND).lower()
SESSIONS_DB_BACKEND = os.getenv("SESSIONS_DB_BACKEND", DB_BACKEND).lower()


# ============================ Storage Settings ============================

# === Azure Blob Storage credentials ===
AZURE_BLOB_CONN_STR = os.getenv("AZURE_BLOB_CONN_STR", "")
AZURE_BLOB_ACCOUNT = os.getenv("AZURE_BLOB_ACCOUNT", "")
AZURE_BLOB_KEY = os.getenv("AZURE_BLOB_KEY", "")
AZURE_BLOB_PUBLIC_BASE = os.getenv(
    "AZURE_BLOB_PUBLIC_BASE",
    f"https://{AZURE_BLOB_ACCOUNT}.blob.core.windows.net" if AZURE_BLOB_ACCOUNT else ""
)

# === Local Storage settings ===
LOCAL_STORAGE_ROOT = os.getenv("LOCAL_STORAGE_ROOT", "./.storage")


# ============================ AI Settings ============================

# === Azure Speech-to-Text credentials ===
AZURE_SPEECH_KEY = os.getenv("SPEECH_KEY")
AZURE_REGION = os.getenv("REGION")
AZURE_CONTAINER_URL = os.getenv("AZURE_CONTAINER_URL")

# === Text-based emotion model ===
TEXT_EMOTION_MODEL = os.getenv("TEXT_EMOTION_MODEL", "j-hartmann/emotion-english-distilroberta-base")
TOP_K_EMOTIONS = os.getenv("TOP_K_EMOTIONS")  # can convert to int later if needed

# === Azure OpenAI for Summary Generation ===
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# === Huggingface ===
HUGGINGFACE_WHISPERX_TOKEN = os.getenv("HUGGINGFACE_TOKEN")


# ============================ Optional Overrides ============================

DEVICE = os.getenv("DEVICE")  # "cuda" | "cpu" | "mps" | None
WHISPERX_MODEL_SIZE = os.getenv("WHISPERX_MODEL_SIZE", "large-v2")
WHISPERX_COMPUTE_TYPE = os.getenv("WHISPERX_COMPUTE_TYPE", "int8")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
