from dataclasses import dataclass
from typing import Optional, Any

from app.database.gateways.registry import GatewayRegistry
from app.interfaces.db.domains.user_defaults_repo import UserDefaultsRepo
from app.interfaces.services.audio.enhancer import AudioEnhancer
from app.interfaces.services.audio.separator import AudioSeparator
from app.interfaces.services.emotions.audio import EmotionAudioAnalyzer
from app.interfaces.services.emotions.mixed import EmotionMixedAnalyzer
from app.interfaces.services.emotions.text import EmotionTextAnalyzer
from app.interfaces.services.summary import Summarizer
from app.interfaces.services.transcription import Transcriber
from app.interfaces.storage.blob_storage import BlobStorage
from app.interfaces.db.domains.users_repo import UsersRepo
from app.interfaces.db.domains.sessions_repo import SessionsRepo


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
class AudioState:
    enhancer: Optional[AudioEnhancer] = None
    separator: Optional[AudioSeparator] = None

# === Transcription ===
@dataclass
class TranscriptionState:
    transcriber: Transcriber = None

# === Emotion Analysis ===
@dataclass
class EmotionAnalysisState:
    by_text: EmotionTextAnalyzer = None
    by_audio: EmotionAudioAnalyzer = None
    mixed: Optional[EmotionMixedAnalyzer] = None

# === Summarization ===
@dataclass
class SummarizationState:
    summarizer: Summarizer = None

# === Services ===
@dataclass
class ServicesState:
    audio: AudioState = AudioState()
    transcription: TranscriptionState = TranscriptionState()
    emotion_analysis: EmotionAnalysisState = EmotionAnalysisState()
    summarization: SummarizationState = SummarizationState()

# ========================================= Application State =========================================
@dataclass
class AppState:
    database: DatabaseState = DatabaseState()
    storage: StorageState = StorageState()
    services: ServicesState = ServicesState()

