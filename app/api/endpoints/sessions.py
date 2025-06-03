from fastapi import APIRouter, Depends, HTTPException
from app.core.config import supabase
from app.api.dependencies.auth import get_current_user

router = APIRouter()

# GET: all sessions for current user
@router.get("/")
def get_sessions(current_user: dict = Depends(get_current_user)):
    response = supabase.table("sessions").select("*").eq("user_id", current_user["id"]).execute()
    return response.data