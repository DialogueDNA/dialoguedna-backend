# Constants for supabase
# Database config for Supabase
from enum import Enum


class StrEnum(str, Enum):
    """
    Backport of Python 3.11's StrEnum.
    Acts like both str and Enum.
    """

    def __str__(self) -> str:
        return str(self.value)

# === Table Constants ===
AUTH_TABLE_NAME = "auth"

# ====== Table Columns ======
AUTH_COLUMN_UNIQUE_ID = "id"

# === Table Constants ===
SESSIONS_TABLE_NAME = "sessions"

# ====== Table Columns ======
class SessionColumn(StrEnum):
    session_id = "id"
    user_id = "user_id"
    title = "title"
    session_status = "session_status"
    metadata_status = "metadata_status"
    audio_file_status = "audio_file_status"
    transcript_status = "transcript_status"
    emotion_breakdown_status = "emotion_breakdown_status"
    summary_status = "summary_status"
    audio_file_url = "audio_file_url"
    transcript_url = "transcript_url"
    emotion_breakdown_url = "emotion_breakdown_url"
    summary_url = "summary_url"
    duration = "duration"
    participants = "participants"
    language = "language"
    source = "source"
    is_favorite = "is_favorite"
    tags = "tags"
    created_at = "created_at"
    updated_at = "updated_at"
    processing_error = "processing_error"

class SessionStatus(StrEnum):
    """Canonical session processing states (string-valued for easy JSON/DB usage)."""
    not_started = "not_started"
    queued = "queued"
    stopped = "stopped"
    progressing = "progressing"
    completed = "completed"
    failed = "failed"

