from fastapi import APIRouter, Depends, HTTPException
from app.core.config import supabase
from app.api.dependencies.auth import get_current_user

router = APIRouter()

@router.get("/{session_id}")
def get_emotions(session_id: str, current_user: dict = Depends(get_current_user)):
    # Optional: check if the session exists and belongs to user
    session_check = supabase.table("sessions").select("id").eq("id", session_id).eq("user_id", current_user["id"]).single().execute()
    if not session_check.data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get emotion data for this session
    result = supabase.table("emotions").select("*").eq("session_id", session_id).execute()
    return result.data
