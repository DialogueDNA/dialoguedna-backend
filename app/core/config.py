import os
from pathlib import Path
from datetime import datetime

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
SPEECH_KEY = "AmFKUg1B7O2ku2m5BQQK5eZPue87iZ2edheA40OWleMpgMS2QPeHJQQJ99BCAC5RqLJXJ3w3AAAYACOGoEoF"
REGION = "westeurope"

# === Azure Blob Storage (Uploader) ===
AZURE_STORAGE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=https;"
    "AccountName=audiorecordstorage;"
    "AccountKey=DefaultEndpointsProtocol=https;AccountName=audiorecordstorage;AccountKey=6vXouIVzstwea0nV+9Y1oDv2WMHA9rlNA+tJQ2qvqB9C3z1VskWkDM7bOxyRmddzbUI8Y8z59yp5+ASt6TyDCQ==;EndpointSuffix=core.windows.net;"
    "EndpointSuffix=core.windows.net"
)
AZURE_CONTAINER_NAME = "audiofiles"


# === Text-based emotion model ===
TEXT_EMOTION_MODEL = "j-hartmann/emotion-english-distilroberta-base"
TOP_K_EMOTIONS = None  # You can set to 3, 5, etc. if needed

# === Azure OpenAI for Summary Generation ===
AZURE_OPENAI_API_KEY = "7r2jiEu4LHMrMQP4Q7CS1hlbR5wRF35XZyhJPMrSYhw0CY8TB0JMJQQJ99BCACfhMk5XJ3w3AAAAACOGyJoH"
AZURE_OPENAI_ENDPOINT = "https://yarde-m8o9xwi0-swedencentral.cognitiveservices.azure.com/"
#AZURE_OPENAI_DEPLOYMENT = "gpt-4-32k"
AZURE_OPENAI_DEPLOYMENT = "gpt-4.1"
AZURE_OPENAI_API_VERSION = "2025-01-01-preview"


# === Audio settings ===
SAMPLE_RATE = 16000
CHUNK_DURATION_SEC = 5
OVERLAP_DURATION_SEC = 1.5


