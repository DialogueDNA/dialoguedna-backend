from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.session import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer, default=0)
    participants = Column(Text, nullable=True)
    audio_blob_url = Column(Text, nullable=False)
    transcript = Column(Text, nullable=True)
    status = Column(String, default="uploaded")

    user = relationship("User", back_populates="sessions")
    emotions = relationship("Emotion", back_populates="session")