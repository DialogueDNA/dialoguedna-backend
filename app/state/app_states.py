# app/state/app_states.py
from dataclasses import dataclass
from typing import Optional, Any

from app.database.registry import GatewayRegistry
from app.ports.db.domains.user_defaults_repo import UserDefaultsRepo
from app.ports.services.audio.enhancer import AudioEnhancer
from app.ports.services.audio.separator import AudioSeparator
from app.ports.services.emotions.audio_analyzer import AudioEmotionAnalyzer
from app.ports.services.emotions.mixed_analyzer import MixedEmotionAnalyzer
from app.ports.services.emotions.text_analyzer import TextEmotionAnalyzer
from app.ports.services.transcription import Transcriber
from app.ports.storage.blob_storage import BlobStorage
from app.ports.db.domains.users_repo import UsersRepo
from app.ports.db.domains.sessions_repo import SessionsRepo


# ========================================= Database State =========================================
@dataclass
class DatabaseState:
    gateway_registry: Optional[GatewayRegistry] = None
    users_repo: Optional[UsersRepo] = None
    sessions_repo: Optional[SessionsRepo] = None
    users_default_repo: Optional[UserDefaultsRepo] = None


# ========================================= Storage State =========================================
@dataclass
class StorageState:
    client: Optional[BlobStorage] = None
    azure_blob_service: Optional[Any] = None
    azure_account_key: Optional[str] = None


# ========================================= Services State =========================================

# === Audio Utils ===
@dataclass
class AudioUtilsState:
    audio_enhancer: Optional[AudioEnhancer] = None
    audio_separator: Optional[AudioSeparator] = None

# === Transcription ===
@dataclass
class TranscriptionState:
    transcriber: Optional[Transcriber] = None

# === Emotion Analysis ===
@dataclass
class EmotionAnalysisState:
    by_text: Optional[TextEmotionAnalyzer] = None
    by_audio: Optional[AudioEmotionAnalyzer] = None
    mixed: Optional[MixedEmotionAnalyzer] = None

# === Summarization ===
@dataclass
class SummarizationState:
    summarizer: Optional[Transcriber] = None

# === Services ===
@dataclass
class ServicesState:
    audio_utils: AudioUtilsState = AudioUtilsState()
    transcription: TranscriptionState = TranscriptionState()
    emotion_analysis: EmotionAnalysisState = EmotionAnalysisState()
    summarization: SummarizationState = SummarizationState()

# ========================================= Application State =========================================
@dataclass
class AppState:
    database: DatabaseState = DatabaseState()
    storage: StorageState = StorageState()
    services: ServicesState = ServicesState()

