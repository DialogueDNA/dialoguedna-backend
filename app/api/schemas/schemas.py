from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class TranscriptRowDTO(BaseModel):
    speaker: Optional[str] = None
    text: str
    start: Optional[float] = None
    end: Optional[float] = None

class TranscriptDTO(BaseModel):
    transcript: List[TranscriptRowDTO]

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
    audio_status: Optional[str] = None
    audio_url: Optional[str] = None
    transcript_status: Optional[str] = None
    transcript_url: Optional[str] = None
    emotion_status: Optional[str] = None
    emotions_url: Optional[str] = None
    summary_status: Optional[str] = None
    summary_url: Optional[str] = None
    duration: Optional[float] = None
    participants: Optional[List[str]] = None
    language: Optional[str] = None
    created_at: Optional[str] = None

class SessionCreateRequest(BaseModel):
    title: str

class SessionListResponse(BaseModel):
    sessions: List[SessionDTO]

class SessionResponse(BaseModel):
    session: SessionDTO

class TranscriptResponse(BaseModel):
    transcript: List[TranscriptRowDTO]

class EmotionsResponse(BaseModel):
    emotions: List[EmotionRow]

class SummaryResponse(BaseModel):
    summary: SummaryDTO

class UpdateMetadata(BaseModel):
    title: str

class DeleteResponse(BaseModel):
    deleted: bool
