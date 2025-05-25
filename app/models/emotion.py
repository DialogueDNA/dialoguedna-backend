from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from app.db.session import Base

class Emotion(Base):
    __tablename__ = "emotions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    timestamp_seconds = Column(Integer, nullable=False)
    emotion = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)

    session = relationship("Session", back_populates="emotions")