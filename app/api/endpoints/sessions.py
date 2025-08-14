from fastapi import APIRouter, Depends
from app.core.config import supabase
from app.api.dependencies.auth import get_current_user
from app.core.constants.db.supabase_constants import SESSIONS_TABLE_NAME, SESSIONS_COLUMN_USER_ID, \
    AUTH_COLUMN_UNIQUE_ID

router = APIRouter()

# GET: all sessions for current user
@router.get("/")
def get_sessions(current_user: dict = Depends(get_current_user)):
    response = supabase.table(SESSIONS_TABLE_NAME).select("*").eq(SESSIONS_COLUMN_USER_ID, current_user[AUTH_COLUMN_UNIQUE_ID]).execute()
    return response.data