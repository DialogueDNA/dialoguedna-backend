from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, conlist

# =============== DTOs ===============

ProcessingStatus = Literal["not_started", "queued", "processing", "completed", "failed"]

class SessionDTO(BaseModel):
    id: str
    title: str

    session_status: Optional[str] = None
    audio_status: Optional[str] = None
    transcript_status: Optional[str] = None
    emotion_status: Optional[str] = None
    summary_status: Optional[str] = None

    audio_url: Optional[str] = None
    transcript_url: Optional[str] = None
    emotions_url: Optional[str] = None
    summary_url: Optional[str] = None

    duration: Optional[float] = None
    participants: Optional[List[str]] = None
    language: Optional[str] = None

    created_at: Optional[datetime] = None

class ArtifactAccess(BaseModel):
    object_path: str
    access_url: str
    expires_at: datetime

class ArtifactDTO(BaseModel):
    status: ProcessingStatus
    result: Optional[ArtifactAccess]

# =============== Sessions Responses ===============

class SessionListResponse(BaseModel):
    sessions: List[SessionDTO]

class SessionResponse(BaseModel):
    session: SessionDTO

class SessionCreateRequest(BaseModel):
    title: str

# =============== Artifacts Responses ===============

class AudioResponse(BaseModel):
    audio: ArtifactDTO

class TranscriptResponse(BaseModel):
    transcript: ArtifactDTO

class AnalyzedEmotionsResponse(BaseModel):
    analyzed_emotions: ArtifactDTO

class SummaryResponse(BaseModel):
    summary: ArtifactDTO

class BulkDeleteRequest(BaseModel):
    session_ids: conlist(str, min_length=1) = Field(..., description="IDs to delete")
    delete_blobs: bool = Field(False, description="Also delete storage blobs")

