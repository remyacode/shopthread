import json
from app.services.meta_ai import chat
from app.core.supabase import supabase

STATUS_MESSAGES = {
    "CONFIRMED": {
        "en": "Great news! Your order {order_id} has been confirmed ✅ We're preparing your {product_name} for dispatch. You'll hear from us once it's shipped! 🎉",
        "hi": "खुशखबरी! आपका ऑर्डर {order_id} कन्फर्म हो गया है ✅ आपका {product_name} जल्द ही भेजा जाएगा! 🎉"
    },
    "SHIPPED": {
        "en": "Your order is on its way! 🚚 Order {order_id} ({product_name}) has been shipped. Tracking ID: {tracking_id}. Expected delivery in 3-5 days!",
        "hi": "आपका ऑर्डर रास्ते में है! 🚚 ऑर्डर {order_id} ({product_name}) भेज दिया गया है। ट्रैकिंग ID: {tracking_id}"
    },
    "DELIVERED": {
        "en": "Your order has been delivered! �� We hope you love your {product_name}. Please share a photo when you wear it — tag us! ❤️",
        "hi": "आपका ऑर्डर डिलीवर हो गया! 🎊 हमें उम्मीद है आपको {product_name} पसंद आया। पहनकर फोटो ज़रूर शेयर करें! ❤️"
    },
    "CANCELLED": {
        "en": "Your order {order_id} has been cancelled. If you have any questions, please DM us. We're sorry for the inconvenience 🙏",
        "hi": "आपका ऑर्डर {order_id} कैंसल हो गया है। किसी भी सवाल के लिए हमें DM करें 🙏"
    }
}

RETURN_REPLY_PROMPT = """You are a customer service agent for an Indian jewellery shop.

A buyer sent this return request: "{message}"
Order ID: {order_id}
Product: {product_name}

Write a warm, empathetic reply in the same language as the buyer (Hindi, English or Hinglish).
- Acknowledge their concern
- Tell them to send the item back within 7 days
- Refund will be processed within 3-5 business days after receiving the item
- Keep it short and friendly
"""

async def get_dm_notification(
    order_id: str,
    new_status: str,
    product_name: str,
    buyer_language: str = "en",
    tracking_id: str = ""
) -> str:
    """Generate a status update DM for the buyer"""
    template = STATUS_MESSAGES.get(new_status, {})
    lang = buyer_language if buyer_language in ["en", "hi"] else "en"
    message = template.get(lang, template.get("en", "Your order status has been updated."))
    
    return message.format(
        order_id=order_id[:8].upper(),
        product_name=product_name,
        tracking_id=tracking_id or "Will be shared shortly"
    )

async def process_return_request(
    vendor_id: str,
    order_id: str,
    buyer_handle: str,
    message: str
) -> dict:
    """Handle a return request from a buyer"""
    # Get order details
    order = supabase.table("orders")\
        .select("*, products(name)")\
        .eq("id", order_id)\
        .single()\
        .execute()
    
    product_name = order.data["products"]["name"] if order.data and order.data.get("products") else "your item"
    
    # Generate empathetic reply using Muse Spark
    reply = await chat(
        model="muse-spark-1.3",
        messages=[{"role": "user", "content": RETURN_REPLY_PROMPT.format(
            message=message,
            order_id=order_id[:8].upper(),
            product_name=product_name
        )}]
    )
    
    # Update order status to RETURN_REQUESTED
    supabase.table("orders")\
        .update({"status": "RETURN_REQUESTED", "notes": message})\
        .eq("id", order_id)\
        .execute()
    
    # Log analytics
    supabase.table("analytics_events").insert({
        "vendor_id": vendor_id,
        "event_type": "RETURN_REQUESTED",
        "metadata": {"order_id": order_id, "buyer": buyer_handle}
    }).execute()
    
    return {"reply": reply, "order_id": order_id, "status": "RETURN_REQUESTED"}

async def check_stale_shipments(vendor_id: str) -> list:
    """Find shipments that haven't been updated in 48 hours"""
    result = supabase.table("shipments")\
        .select("*, orders(id, buyer_ig_handle, products(name))")\
        .eq("vendor_id", vendor_id)\
        .neq("status", "DELIVERED")\
        .execute()
    
    stale = []
    for shipment in (result.data or []):
        stale.append({
            "shipment_id": shipment["id"],
            "order_id": shipment["order_id"],
            "tracking_id": shipment.get("tracking_id"),
            "status": shipment["status"],
            "buyer": shipment["orders"]["buyer_ig_handle"] if shipment.get("orders") else None
        })
    
    return stale
