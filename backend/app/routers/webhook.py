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
        # Instagram Business Account ID that received the DM
        ig_account_id = str(entry.get("id", ""))

        # Find vendor by Instagram Page ID
        vendor_result = supabase.table("vendors")\
            .select("id, instagram_page_id, instagram_connected")\
            .eq("instagram_page_id", ig_account_id)\
            .eq("instagram_connected", True)\
            .execute()

        if not vendor_result.data:
            print(f"No vendor found for Instagram account: {ig_account_id}")
            continue

        vendor_id = vendor_result.data[0]["id"]

        # Process each DM
        for messaging in entry.get("messaging", []):
            sender_id = messaging.get("sender", {}).get("id")
            message_text = messaging.get("message", {}).get("text")

            if not sender_id or not message_text:
                continue

            # Skip messages from the vendor themselves
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
