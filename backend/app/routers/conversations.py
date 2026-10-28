from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_vendor
from app.core.supabase import supabase

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("/")
async def get_conversations(vendor: dict = Depends(get_current_vendor)):
    result = supabase.table("conversations")\
        .select("*")\
        .eq("vendor_id", vendor["id"])\
        .order("last_message_at", desc=True)\
        .execute()
    return result.data

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, vendor: dict = Depends(get_current_vendor)):
    result = supabase.table("conversations")\
        .select("*")\
        .eq("id", conversation_id)\
        .eq("vendor_id", vendor["id"])\
        .single()\
        .execute()
    return result.data
