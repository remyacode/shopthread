import json
from app.services.meta_ai import chat
from app.core.supabase import supabase

INTENT_PROMPT = """You are OrderWeave, an AI agent for an Instagram jewellery shop.

A buyer sent this message: "{message}"

Extract the order intent and return ONLY a valid JSON object with these fields:
{{
  "message_type": "ORDER" | "INQUIRY" | "PAYMENT" | "RETURN" | "OTHER",
  "product_name": "name of product mentioned or null",
  "variant": "size/color/type mentioned or null",
  "quantity": number or 1,
  "payment_readiness": "READY" | "ASKING" | "UNKNOWN",
  "reply_needed": true or false,
  "extracted_language": "en" | "hi" | "mixed"
}}

Rules:
- If buyer says price, cost, kitna, rate -> message_type is INQUIRY
- If buyer says want, chahiye, book, order, le lena -> message_type is ORDER
- If buyer says paid, sent, bhej diya -> message_type is PAYMENT
- If buyer says return, wapas, refund -> message_type is RETURN
- quantity defaults to 1 if not mentioned
"""

REPLY_PROMPT = """You are a friendly Instagram jewellery shop assistant for Priya Jewels.

Conversation so far:
{history}

Latest buyer message: "{message}"
Intent detected: {intent}
Shop UPI ID: {upi_id}
Order ID: {order_id}
Amount: ₹{amount}

Write a warm, friendly reply in the same language as the buyer (Hindi, English, or mixed Hinglish).
If it's an ORDER with payment_readiness READY or ASKING, include the UPI payment link:
upi://pay?pa={upi_id}&pn=ShopThread&am={amount}&cu=INR&tn=Order-{order_id}

IMPORTANT: Read the full conversation above. Do not repeat questions already asked. 
If buyer already confirmed they want to order, proceed to payment — do not ask again.
Keep it short — max 3 sentences. Sound like a real shop owner, not a bot.
"""

async def process_dm(vendor_id: str, buyer_handle: str, message: str) -> dict:
    # Step 1: Extract intent using Muse Spark
    intent_raw = await chat(
        model="muse-spark-1.3",
        messages=[{"role": "user", "content": INTENT_PROMPT.format(message=message)}],
        json_mode=True
    )

    try:
        intent = json.loads(intent_raw)
    except json.JSONDecodeError:
        intent = {
            "message_type": "OTHER",
            "product_name": None,
            "variant": None,
            "quantity": 1,
            "payment_readiness": "UNKNOWN",
            "reply_needed": True,
            "extracted_language": "en"
        }

    # Step 2: Store conversation
    existing = supabase.table("conversations")\
        .select("id, messages")\
        .eq("vendor_id", vendor_id)\
        .eq("buyer_ig_handle", buyer_handle)\
        .execute()

    if existing.data:
        conv = existing.data[0]
        messages = conv["messages"] or []
        messages.append({"role": "buyer", "content": message, "intent": intent})
        supabase.table("conversations")\
            .update({"messages": messages, "last_message_at": "now()"})\
            .eq("id", conv["id"])\
            .execute()
        conv_id = conv["id"]
    else:
        messages = [{"role": "buyer", "content": message, "intent": intent}]
        result = supabase.table("conversations").insert({
            "vendor_id": vendor_id,
            "buyer_ig_handle": buyer_handle,
            "messages": messages
        }).execute()
        conv_id = result.data[0]["id"]

    # Step 3: Create order if intent is ORDER
    order_id = None
    amount = 0

    if intent["message_type"] == "ORDER":
        # Look up product price if product mentioned
        if intent.get("product_name"):
            products = supabase.table("products")\
                .select("id, price")\
                .eq("vendor_id", vendor_id)\
                .ilike("name", f"%{intent['product_name']}%")\
                .execute()
            if products.data:
                amount = float(products.data[0]["price"])
                product_id = products.data[0]["id"]
            else:
                amount = 0
                product_id = None
        else:
            product_id = None

        order_result = supabase.table("orders").insert({
            "vendor_id": vendor_id,
            "product_id": product_id,
            "buyer_ig_handle": buyer_handle,
            "variant": intent.get("variant"),
            "quantity": intent.get("quantity", 1),
            "amount": amount,
            "status": "PENDING",
            "payment_status": "UNPAID"
        }).execute()
        order_id = order_result.data[0]["id"][:8].upper()

    # Step 4: Get vendor UPI ID
    vendor = supabase.table("vendors")\
        .select("upi_id")\
        .eq("id", vendor_id)\
        .single()\
        .execute()
    upi_id = vendor.data.get("upi_id", "shopthread@upi")

    # Step 5: Generate reply using Muse Spark
    # Build conversation history string
    history_lines = []
    for m in messages[:-1]:  # exclude current message
        role = "Buyer" if m["role"] == "buyer" else "Shop"
        history_lines.append(f"{role}: {m['content']}")
    history = "\n".join(history_lines) if history_lines else "(this is the first message)"

    reply = await chat(
        model="muse-spark-1.3",
        messages=[{
            "role": "user",
            "content": REPLY_PROMPT.format(
                message=message,
                intent=json.dumps(intent),
                upi_id=upi_id,
                order_id=order_id or "N/A",
                amount=amount,
                history=history
            )
        }]
    )

    # Step 6: Log analytics event
    supabase.table("analytics_events").insert({
        "vendor_id": vendor_id,
        "event_type": "DM_PROCESSED",
        "metadata": {
            "message_type": intent["message_type"],
            "buyer": buyer_handle,
            "order_id": order_id,
            "language": intent.get("extracted_language")
        }
    }).execute()

    return {
        "intent": intent,
        "order_id": order_id,
        "reply": reply,
        "conv_id": conv_id
    }
