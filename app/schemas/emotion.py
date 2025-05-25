from pydantic import BaseModel

class EmotionBase(BaseModel):
    timestamp_seconds: int
    emotion: str
    confidence: float

class EmotionCreate(EmotionBase):
    session_id: str

class EmotionRead(EmotionBase):
    id: int
    session_id: str

    class Config:
        orm_mode = True