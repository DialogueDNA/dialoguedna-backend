# Constants for supabase
# Database configuration for Supabase

# === Table Constants ===
AUTH_TABLE_NAME = "auth"

# ====== Table Columns ======
AUTH_COLUMN_UNIQUE_ID = "id"

# === Table Constants ===
SESSIONS_TABLE_NAME = "sessions"

# ====== Table Columns ======
SESSIONS_COLUMN_UNIQUE_ID = "id"
SESSIONS_COLUMN_USER_ID = "user_id"
SESSIONS_COLUMN_TITLE= "title"
SESSIONS_COLUMN_METADATA_STATUS = "metadata_status"
SESSIONS_COLUMN_AUDIO_FILE_URL = "audio_file_url"
SESSIONS_COLUMN_AUDIO_FILE_STATUS = "audio_file_status"
SESSIONS_COLUMN_TRANSCRIPT_URL = "transcript_url"
SESSIONS_COLUMN_TRANSCRIPT_STATUS = "transcript_status"
SESSIONS_COLUMN_EMOTION_BREAKDOWN_URL = "emotion_breakdown_url"
SESSIONS_COLUMN_EMOTION_BREAKDOWN_STATUS = "emotion_breakdown_status"
SESSIONS_COLUMN_SUMMARY_URL = "summary_url"
SESSIONS_COLUMN_SUMMARY_STATUS = "summary_status"
SESSIONS_COLUMN_STATUS = "session_status"
SESSIONS_COLUMN_DURATION = "duration"
SESSIONS_COLUMN_PARTICIPANTS = "participants"
SESSIONS_COLUMN_LANGUAGE = "language"
SESSIONS_COLUMN_SOURCE = "source"
SESSIONS_COLUMN_IS_FAVORITE = "is_favorite"
SESSIONS_COLUMN_TAGS = "tags"
SESSIONS_COLUMN_CREATED_AT = "created_at"
SESSIONS_COLUMN_UPDATED_AT = "updated_at"
SESSIONS_COLUMN_PROCESSING_ERROR = "processing_error"

# ========= Session Processing errors values =========
SESSION_STATUS_NOT_STARTED = "not_started"
SESSION_STATUS_QUEUED = "queued"
SESSION_STATUS_PROGRESSING = "progressing"
SESSION_STATUS_COMPLETED = "completed"
SESSION_STATUS_FAILED = "failed"
