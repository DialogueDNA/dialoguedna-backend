from fastapi import APIRouter
from .get import router as get_sessions_router
from .post import router as post_sessions_router
from .delete import router as delete_sessions_router
from app.api.routers.sessions.output.transcript.get import router as transcript_router
from app.api.routers.sessions.output.transcript.rebuild import router as transcript_router
from app.api.routers.sessions.output.emotions.get import router as emotions_router
from app.api.routers.sessions.output.emotions.rebuild import router as emotions_router
from app.api.routers.sessions.output.summary.get import router as summary_router
from app.api.routers.sessions.output.summary.rebuild import router as summary_router
from app.api.routers.sessions.output.audio.get import router as audio_router


router = APIRouter()
router.include_router(get_sessions_router,      prefix="/api/sessions", tags=["sessions"])
router.include_router(post_sessions_router,     prefix="/api/sessions", tags=["sessions"])
router.include_router(delete_sessions_router,   prefix="/api/sessions", tags=["sessions"])
router.include_router(transcript_router,        prefix="/api/sessions", tags=["sessions"])
router.include_router(emotions_router,          prefix="/api/sessions", tags=["sessions"])
router.include_router(summary_router,           prefix="/api/sessions", tags=["sessions"])
router.include_router(audio_router,             prefix="/api/sessions", tags=["sessions"])

