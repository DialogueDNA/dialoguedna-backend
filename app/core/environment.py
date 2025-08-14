import os
from dotenv import load_dotenv

# === Load from .env file ===
load_dotenv()


# ============================ Authentication Settings ============================
AUTH_JWT_ALG = os.getenv("AUTH_JWT_ALG", "HS256")             # HS256 | RS256
AUTH_JWT_SECRET = os.getenv("AUTH_JWT_SECRET")                # HS256
AUTH_JWT_PUBLIC_KEY = os.getenv("AUTH_JWT_PUBLIC_KEY")        # RS256
AUTH_JWKS_URL = os.getenv("AUTH_JWKS_URL")                    # RS256
AUTH_JWT_ISS = os.getenv("AUTH_JWT_ISS")                      # Issuer of the JWT, e.g., "https://example.com/"
AUTH_JWT_AUD = os.getenv("AUTH_JWT_AUD", "authenticated")     # Audience of the JWT, e.g., "authenticated" or "api"


# ============================ Database Settings ============================
DB_ADAPTER = os.getenv("DATABASE", "supabase").lower() # supabase | sqlite | postgresql

# === Superbase Settings ===
SUPABASE_URL = os.getenv("SUPABASE_URL") # Supabase URL, e.g., "https://your-project.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Supabase service role key, used for server-side operations
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET") # JWT secret for Supabase, used for signing tokens

# === Database Domain Settings ===
USERS_DB_BACKEND = os.getenv("USERS_DB_BACKEND", DB_ADAPTER).lower() # Default: "supabase"
SESSIONS_DB_BACKEND = os.getenv("SESSIONS_DB_BACKEND", DB_ADAPTER).lower() # Default: "supabase"
USER_DEFAULTS_DB_BACKEND = os.getenv("USER_DEFAULTS_DB_BACKEND", DB_ADAPTER).lower() # Default: "supabase"


# ============================ Storage Settings ============================
STORAGE_ADAPTER = os.getenv("STORAGE", "azure_blob").lower() # azure_blob | local

# === Azure Blob Storage credentials ===
AZURE_BLOB_CONN_STR = os.getenv("AZURE_BLOB_CONN_STR", "") # Azure Blob Storage connection string, e.g., "DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=your-azure-account-key;EndpointSuffix=core.windows.net"
AZURE_BLOB_ACCOUNT = os.getenv("AZURE_BLOB_ACCOUNT", "") # Azure Blob Storage account name, e.g., "myaccount"
AZURE_BLOB_KEY = os.getenv("AZURE_BLOB_KEY", "") # Azure Blob Storage account key, e.g., "your-azure-account-key"
AZURE_BLOB_PUBLIC_BASE = os.getenv(
    "AZURE_BLOB_PUBLIC_BASE",
    f"https://{AZURE_BLOB_ACCOUNT}.blob.core.windows.net" if AZURE_BLOB_ACCOUNT else ""
) # Public base URL for Azure Blob Storage, e.g., "https://myaccount.blob.core.windows.net"

# === Local Storage core ===
LOCAL_STORAGE_ROOT = os.getenv("LOCAL_STORAGE_ROOT", "./.storage") # Local storage root directory


# ============================ AI Settings ============================

# ================ Transcription Settings ================
TRANSCRIPTION_ADAPTER = os.getenv("TRANSCRIPTION_ADAPTER", "azure_speech_to_text")  # key in TRANSCRIPTION_PLUGINS

# === Azure Speech-to-Text credentials ===
AZURE_SPEECH_KEY = os.getenv("SPEECH_KEY") # e.g., "your-azure-speech-key"
AZURE_REGION = os.getenv("REGION") # e.g., "eastus", "westus2"
AZURE_SPEECH_LOCALE = os.getenv("SPEECH_LOCALE")  # Optional locale for transcription, e.g., "en-US"

# ================ Emotion Analysis Settings ================

# === Text Emotion Model ===
# This is the model used for text-based emotion analysis.
# Default: "j-hartmann/emotion-english-distilroberta-base"
TEXT_EMOTION_MODEL_NAME = os.getenv("TEXT_EMOTION_ADAPTER", "j_hartmann") # j_hartmann
J_HARTMANN_MODEL_NAME = os.getenv("J_HARTMANN_MODEL_NAME", "j-hartmann/emotion-english-distilroberta-base") # j-hartmann/emotion-english-distilroberta-base | j-hartmann/emotion-english-distilbert-base | ...
TEXT_EMOTION_TOP_K = int(os.getenv("TEXT_EMOTION_TOP_K", "0") or 0) or None # 0 | None | K (int) - Top-K emotions to return, 0 means all, None means top emotion

# === Audio Emotion Model ===
# This is the model used for audio-based emotion analysis.
# Default: "superb/hubert-large-superb-er"
AUDIO_EMOTION_MODEL_NAME = os.getenv("AUDIO_EMOTION_ADAPTER", "superb/hubert-large-superb-er") # superb/hubert-large-superb-er | superb/wav2vec2-large-superb-er | ...
AUDIO_TARGET_SR = int(os.getenv("AUDIO_TARGET_SR", "16000")) # Target sample rate for audio emotion analysis, e.g., 16000 Hz

# === Fusion Emotion Model ===
# This is the model used for fusing text and audio emotion scores.
# Default: "weights"
FUSION_EMOTION_MODEL_NAME = os.getenv("FUSION_EMOTION_ADAPTER", "adaptive")  # adaptive|weights|...
FUSION_AUDIO_WEIGHT = float(os.getenv("FUSION_AUDIO_WEIGHT", "0.6")) # Weight for audio emotion scores, e.g., 0.6
FUSION_TEXT_WEIGHT  = float(os.getenv("FUSION_TEXT_WEIGHT", "0.4")) # Weight for text emotion scores, e.g., 0.4

# === Enhancer Model ===
ENABLE_AUDIO_ENHANCER = os.getenv("ENABLE_ENHANCER", "false").lower() == "true"
AUDIO_ENHANCER_MODEL_NAME = os.getenv("AUDIO_ENHANCER_ADAPTER", "rnnoise")  # none|rnnoise|demucs|cmgan

# RNNoise Enhancer Settings
RNNOISE_ENHANCER_STRENGTH = os.getenv("RNNOISE_ENHANCER_STRENGTH", "medium")  # light|medium|strong

# === Separation Model ===
ENABLE_AUDIO_SEPARATION = os.getenv("ENABLE_SEPARATION", "false").lower() == "true" # Enable or disable audio separation
AUDIO_SEPARATOR_MODEL_NAME = os.getenv("AUDIO_SEPARATION_ADAPTER", "sepformer") # sepformer|demucs|spleeter
SEPFORMER_MODEL_NAME = os.getenv("SEPFORMER_MODEL_NAME", "speechbrain/sepformer-whamr") # Default: speechbrain/sepformer-whamr

# ============================ Summarization Generation Settings ============================
SUMMARIZER_ADAPTER = os.getenv("SUMMARIZATION_ADAPTER", "azure_openai")  # key in SUMMARIZATION_PLUGINS

# === Azure OpenAI ===
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") # Azure OpenAI API key, e.g., "your-azure-openai-api-key"
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT") # Azure OpenAI endpoint, e.g., "https://your-openai-resource.openai.azure.com/"
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT") # Azure OpenAI deployment name, e.g., "gpt-35-turbo"
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION") # Azure OpenAI API version, e.g., "2023-05-15"

# === Summarization LLM knobs ===
AZURE_OPENAI_TEMPERATURE = float(os.getenv("SUMMARIZER_TEMPERATURE", "0.2")) # Temperature for summarization, e.g., 0.2
AZURE_OPENAI_MAX_OUTPUT_TOKENS = int(os.getenv("SUMMARIZER_MAX_OUTPUT_TOKENS", "700")) # Maximum output tokens for summarization, e.g., 700

# ============================ Optional Overrides ============================

DEVICE = os.getenv("DEVICE")  # "cuda" | "cpu" | "mps" | None
WHISPERX_MODEL_SIZE = os.getenv("WHISPERX_MODEL_SIZE", "large-v2") # "tiny" | "base" | "small" | "medium" | "large-v1" | "large-v2"
WHISPERX_COMPUTE_TYPE = os.getenv("WHISPERX_COMPUTE_TYPE", "int8") # "int8" | "float16" | "float32"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO") # "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"

# === Huggingface ===
HUGGINGFACE_WHISPERX_TOKEN = os.getenv("HUGGINGFACE_TOKEN") # Huggingface token for WhisperX, if needed