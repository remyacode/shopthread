import hmac
import hashlib
import json
from fastapi import APIRouter, Request, HTTPException, Query
from app.core.config import settings
from app.core.supabase import supabase
from app.agents.order_weave import process_dm

router = APIRouter(prefix="/webhook", tags=["webhook"])

@router.get("/instagram")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/instagram")
async def receive_webhook(request: Request):
    # Verify signature — security check on every incoming request
    signature = request.headers.get("X-Hub-Signature-256", "")
    body = await request.body()

    expected = "sha256=" + hmac.new(
        settings.META_APP_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(body)
    print(f"Webhook received: {json.dumps(payload, indent=2)}")

    for entry in payload.get("entry", []):
        ig_account_id = str(entry.get("id", ""))

        vendor_result = supabase.table("vendors")\
            .select("id, instagram_page_id, instagram_connected")\
            .eq("instagram_page_id", ig_account_id)\
            .eq("instagram_connected", True)\
            .execute()

        if not vendor_result.data:
            print(f"No vendor found for Instagram account: {ig_account_id}")
            continue

        vendor_id = vendor_result.data[0]["id"]

        for messaging in entry.get("messaging", []):
            sender_id = messaging.get("sender", {}).get("id")
            message_text = messaging.get("message", {}).get("text")

            if not sender_id or not message_text:
                continue

            if sender_id == ig_account_id:
                continue

            print(f"DM from {sender_id} to vendor {vendor_id}: {message_text}")

            try:
                result = await process_dm(
                    vendor_id=vendor_id,
                    buyer_handle=sender_id,
                    message=message_text
                )
                print(f"OrderWeave result: {result['intent']['message_type']} — {result.get('reply', '')[:50]}")
            except Exception as e:
                print(f"OrderWeave error: {e}")

    return {"status": "ok"}

@router.get("/vendors/list")
async def list_vendors():
    """Return all vendors for the simulator dropdown."""
    result = supabase.table("vendors")\
        .select("id, full_name, instagram_handle, instagram_page_id, instagram_connected")\
        .execute()
    return [
        {
            "id": r["id"],
            "name": r["full_name"],
            "handle": r.get("instagram_handle") or "",
            "instagram_page_id": r.get("instagram_page_id") or "",
            "connected": r.get("instagram_connected") or False
        }
        for r in (result.data or [])
    ]

@router.post("/simulate-dm")
async def simulate_dm(request: Request):
    """Demo-only endpoint — simulates an incoming Instagram DM."""
    body = await request.json()
    sender_id = body.get("sender_id", "demo_buyer_123")
    message_text = body.get("message")
    ig_account_id = body.get("ig_account_id", "")
    vendor_id = body.get("vendor_id", "")

    if not message_text:
        raise HTTPException(status_code=400, detail="message required")

    # Look up vendor by vendor_id first, then ig_account_id
    vendor = None
    if vendor_id:
        r = supabase.table("vendors").select("id").eq("id", vendor_id).execute()
        if r.data:
            vendor = r.data[0]
    if not vendor and ig_account_id:
        r = supabase.table("vendors").select("id").eq("instagram_page_id", ig_account_id).execute()
        if r.data:
            vendor = r.data[0]
    # Fallback to default demo vendor
    if not vendor:
        r = supabase.table("vendors").select("id").eq("instagram_page_id", "17841471928395278").execute()
        if r.data:
            vendor = r.data[0]
    if not vendor:
        raise HTTPException(status_code=404, detail="No vendor found")

    result = await process_dm(
        vendor_id=vendor["id"],
        buyer_handle=sender_id,
        message=message_text
    )

    return {
        "sender_id": sender_id,
        "message": message_text,
        "reply": result.get("reply", ""),
        "intent": result.get("intent", {})
    }
