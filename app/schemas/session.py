from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class SessionBase(BaseModel):
    title: str
    date: Optional[datetime] = None
    duration_minutes: Optional[int] = 0
    participants: List[str] = []

class SessionCreate(SessionBase):
    audio_blob_url: str

class SessionRead(SessionBase):
    id: str
    user_id: str
    audio_blob_url: str
    transcript: Optional[str] = None
    status: str

    class Config:
        orm_mode = True