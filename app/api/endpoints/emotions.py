from fastapi import APIRouter, Depends, HTTPException
from app.core.config import supabase
from app.api.dependencies.auth import get_current_user

router = APIRouter()

@router.get("/{session_id}")
def get_emotions(session_id: str, current_user: dict = Depends(get_current_user)):
    result = supabase.table("sessions") \
        .select("emotion_breakdown") \
        .eq("id", session_id) \
        .eq("user_id", current_user["id"]) \
        .single() \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found")

    return result.data["emotion_breakdown"]

