from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class TranscriptRow(BaseModel):
    speaker: Optional[str] = None
    text: str
    start: Optional[float] = None
    end: Optional[float] = None

class EmotionRow(BaseModel):
    speaker: Optional[str] = None
    start: Optional[float] = None
    end: Optional[float] = None
    text: Optional[Dict[str, float]] = None
    audio: Optional[Dict[str, float]] = None
    fused: Optional[Dict[str, float]] = None

class SummaryDTO(BaseModel):
    text: Optional[str] = None
    bullets: Optional[List[str]] = None

class SessionDTO(BaseModel):
    id: str
    title: str
    transcript: List[TranscriptRow] = Field(default_factory=list)
    emotions: List[EmotionRow] = Field(default_factory=list)
    summary: SummaryDTO = SummaryDTO()
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None
    created_at: Optional[str] = None  # let DB fill if you prefer timestamp

class SessionCreateRequest(BaseModel):
    title: str

class SessionListResponse(BaseModel):
    sessions: List[SessionDTO]

class SessionResponse(BaseModel):
    session: SessionDTO

class TranscriptResponse(BaseModel):
    transcript: List[TranscriptRow]

class EmotionsResponse(BaseModel):
    emotions: List[EmotionRow]

class SummaryResponse(BaseModel):
    summary: SummaryDTO

class UpdateMetadata(BaseModel):
    title: str

class DeleteResponse(BaseModel):
    deleted: bool
