from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.dependencies import get_current_vendor
from app.core.supabase import supabase
from app.agents.fulfillment_watch import get_dm_notification, process_return_request, check_stale_shipments

router = APIRouter(prefix="/shipments", tags=["shipments"])

class CreateShipment(BaseModel):
    order_id: str
    tracking_id: Optional[str] = None
    carrier: Optional[str] = None

class UpdateShipment(BaseModel):
    status: str
    tracking_id: Optional[str] = None

class ReturnRequest(BaseModel):
    order_id: str
    buyer_handle: str
    message: str

@router.post("/", status_code=201)
async def create_shipment(body: CreateShipment, vendor: dict = Depends(get_current_vendor)):
    # Verify order belongs to vendor
    order = supabase.table("orders")\
        .select("id, buyer_ig_handle, products(name)")\
        .eq("id", body.order_id)\
        .eq("vendor_id", vendor["id"])\
        .single()\
        .execute()
    
    if not order.data:
        raise HTTPException(status_code=404, detail="Order not found")

    result = supabase.table("shipments").insert({
        "order_id": body.order_id,
        "vendor_id": vendor["id"],
        "tracking_id": body.tracking_id,
        "carrier": body.carrier,
        "status": "PENDING"
    }).execute()

    # Update order status
    supabase.table("orders")\
        .update({"status": "CONFIRMED"})\
        .eq("id", body.order_id)\
        .execute()

    # Generate buyer notification
    product_name = order.data["products"]["name"] if order.data.get("products") else "your order"
    notification = await get_dm_notification(
        order_id=body.order_id,
        new_status="CONFIRMED",
        product_name=product_name
    )

    return {
        "shipment": result.data[0],
        "buyer_notification": notification
    }

@router.get("/")
async def get_shipments(vendor: dict = Depends(get_current_vendor)):
    result = supabase.table("shipments")\
        .select("*, orders(id, buyer_ig_handle, amount, products(name))")\
        .eq("vendor_id", vendor["id"])\
        .order("created_at", desc=True)\
        .execute()
    return result.data

@router.patch("/{shipment_id}")
async def update_shipment(
    shipment_id: str,
    body: UpdateShipment,
    vendor: dict = Depends(get_current_vendor)
):
    valid_statuses = ["PENDING", "PACKED", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "FAILED"]
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status")

    shipment = supabase.table("shipments")\
        .select("*, orders(id, buyer_ig_handle, products(name))")\
        .eq("id", shipment_id)\
        .eq("vendor_id", vendor["id"])\
        .single()\
        .execute()

    if not shipment.data:
        raise HTTPException(status_code=404, detail="Shipment not found")

    updates = {"status": body.status, "last_updated": "now()"}
    if body.tracking_id:
        updates["tracking_id"] = body.tracking_id

    supabase.table("shipments").update(updates).eq("id", shipment_id).execute()

    # Sync order status
    order_status_map = {
        "SHIPPED": "SHIPPED",
        "DELIVERED": "DELIVERED"
    }
    if body.status in order_status_map:
        supabase.table("orders")\
            .update({"status": order_status_map[body.status]})\
            .eq("id", shipment.data["order_id"])\
            .execute()

    # Generate buyer notification
    product_name = shipment.data["orders"]["products"]["name"] if shipment.data.get("orders") and shipment.data["orders"].get("products") else "your order"
    notification = await get_dm_notification(
        order_id=shipment.data["order_id"],
        new_status=body.status,
        product_name=product_name,
        tracking_id=body.tracking_id or shipment.data.get("tracking_id", "")
    )

    supabase.table("analytics_events").insert({
        "vendor_id": vendor["id"],
        "event_type": "SHIPMENT_UPDATED",
        "metadata": {"shipment_id": shipment_id, "new_status": body.status}
    }).execute()

    return {
        "shipment": {**shipment.data, **updates},
        "buyer_notification": notification
    }

@router.post("/return")
async def handle_return(body: ReturnRequest, vendor: dict = Depends(get_current_vendor)):
    result = await process_return_request(
        vendor_id=vendor["id"],
        order_id=body.order_id,
        buyer_handle=body.buyer_handle,
        message=body.message
    )
    return result

@router.get("/stale")
async def get_stale_shipments(vendor: dict = Depends(get_current_vendor)):
    return await check_stale_shipments(vendor["id"])
