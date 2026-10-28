from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.dependencies import get_current_vendor
from app.core.supabase import supabase
from app.agents.order_weave import process_dm

router = APIRouter(prefix="/orders", tags=["orders"])

class TestDMRequest(BaseModel):
    buyer_handle: str
    message: str

class UpdateOrderStatus(BaseModel):
    status: str

@router.post("/test-dm")
async def test_dm(body: TestDMRequest, vendor: dict = Depends(get_current_vendor)):
    """Test OrderWeave with a manual DM — used when webhook is not available"""
    result = await process_dm(
        vendor_id=vendor["id"],
        buyer_handle=body.buyer_handle,
        message=body.message
    )
    return result

@router.get("/")
async def get_orders(vendor: dict = Depends(get_current_vendor)):
    result = supabase.table("orders")\
        .select("*, products(name)")\
        .eq("vendor_id", vendor["id"])\
        .order("created_at", desc=True)\
        .execute()
    return result.data

@router.get("/{order_id}")
async def get_order(order_id: str, vendor: dict = Depends(get_current_vendor)):
    result = supabase.table("orders")\
        .select("*, products(name)")\
        .eq("id", order_id)\
        .eq("vendor_id", vendor["id"])\
        .single()\
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Order not found")
    return result.data

@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: str,
    body: UpdateOrderStatus,
    vendor: dict = Depends(get_current_vendor)
):
    valid_statuses = ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"]
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
    
    result = supabase.table("orders")\
        .update({"status": body.status})\
        .eq("id", order_id)\
        .eq("vendor_id", vendor["id"])\
        .execute()
    
    supabase.table("analytics_events").insert({
        "vendor_id": vendor["id"],
        "event_type": "ORDER_STATUS_UPDATED",
        "metadata": {"order_id": order_id, "new_status": body.status}
    }).execute()
    
    return result.data[0]
