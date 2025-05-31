from fastapi import APIRouter
from app.api.endpoints.sessions import router as sessions_router
# future: from app.api.endpoints.users import router as users_router
# future: from app.api.endpoints.analytics import router as analytics_router

router = APIRouter()
router.include_router(sessions_router)
# router.include_router(users_router)
# router.include_router(analytics_router)