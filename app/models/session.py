from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class SessionDB(BaseModel):
    id: UUID
    user_id: UUID

    title: Optional[str]
    audio_file_url: Optional[str]
    transcript_url: Optional[str]
    emotion_breakdown_url: Optional[Dict[str, Any]]
    summary_url: Optional[str]

    duration: Optional[float]
    participants: Optional[str]

    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    language: Optional[str]
    source: Optional[str]
    processing_error: Optional[str]
    is_favorite: Optional[bool]
    tags: Optional[str]

    audio_file_status: Optional[str]
    transcript_status: Optional[str]
    emotion_breakdown_status: Optional[str]
    summary_status: Optional[str]
    metadata_status: Optional[str]
    session_status: Optional[str]

    transcription_backend: Optional[str]
    transcription_params: Optional[Dict[str, Any]]

    emotion_backend: Optional[str]
    emotion_params: Optional[Dict[str, Any]]

    summarizer_backend: Optional[str]
    summarizer_params: Optional[Dict[str, Any]]
