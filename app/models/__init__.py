from app.db.session import Base, engine
from app.models.user import User
from app.models.session import Session
from app.models.emotion import Emotion

Base.metadata.create_all(bind=engine)