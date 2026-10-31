import json
from app.services.meta_ai import chat
from app.core.supabase import supabase

INTENT_PROMPT = """You are OrderWeave, an AI agent for an Instagram shop.

A buyer sent this message: "{message}"

Extract the order intent and return ONLY a valid JSON object with these fields:
{{
  "message_type": "ORDER" | "INQUIRY" | "PAYMENT" | "RETURN" | "OTHER",
  "product_name": "name of product mentioned or null",
  "variant": "size/color/type mentioned or null",
  "quantity": number or 1,
  "address": "delivery address if mentioned or null",
  "payment_readiness": "READY" | "ASKING" | "UNKNOWN",
  "reply_needed": true or false,
  "extracted_language": "en" | "hi" | "mixed"
}}

Rules:
- If buyer says price, cost, kitna, rate -> message_type is INQUIRY
- If buyer says want, chahiye, book, order, le lena -> message_type is ORDER
- If buyer says paid, sent, bhej diya -> message_type is PAYMENT
- If buyer says return, wapas, refund -> message_type is RETURN
- If buyer says yes, ok, confirm, haan, theek hai -> payment_readiness is READY
- quantity defaults to 1 if not mentioned
"""

REPLY_PROMPT = """You are a friendly Instagram shop assistant for {shop_name}.

Conversation so far:
{history}

Latest buyer message: "{message}"
Intent: {intent}
Your product catalogue: {products}
Collected so far — Variant: {variant} | Address: {address} | Order ID: {order_id} | Amount: ₹{amount} | UPI: {upi_id}

Follow this conversation flow strictly:

STEP 1 — Product match: Check if the buyer's request matches something in your catalogue. If yes, confirm it with the price warmly. If no match, apologise and list what you have.
STEP 2 — Variant: If the product has variants and variant is still null, ask the buyer for it (e.g. size, colour). Skip if not applicable.
STEP 3 — Address: If address is null, ask for the delivery address.
STEP 4 — Confirm order: Summarise — product, variant, address, price — and ask the buyer to confirm before payment.
STEP 5 — Payment: Only after buyer confirms, send the UPI payment link:
upi://pay?pa={upi_id}&pn=ShopThread&am={amount}&cu=INR&tn=Order-{order_id}

IMPORTANT:
- Read the full conversation above carefully. Do NOT repeat a question already answered.
- Move to the next step only when the current one is complete.
- Keep replies short (2-3 sentences max). Sound like a real shop owner, not a bot.
- Write in the same language as the buyer (English, Hindi, or Hinglish).
"""

async def process_dm(vendor_id: str, buyer_handle: str, message: str) -> dict:
    # Step 1: Extract intent
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
            "address": None,
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

    # Step 3: Get vendor info + product catalogue
    vendor = supabase.table("vendors")\
        .select("upi_id, full_name")\
        .eq("id", vendor_id)\
        .single()\
        .execute()
    upi_id = vendor.data.get("upi_id", "shopthread@upi")
    shop_name = vendor.data.get("full_name", "the shop")

    all_products = supabase.table("products")\
        .select("id, name, price, variants")\
        .eq("vendor_id", vendor_id)\
        .execute()
    products_list = [
        f"{p['name']} (₹{p['price']})" + (f" — variants: {', '.join(p['variants'])}" if p.get('variants') else "")
        for p in (all_products.data or [])
    ]
    products_str = "\n".join(products_list) if products_list else "No products listed yet."

    # Step 4: Extract collected info from full conversation history
    collected_variant = None
    collected_address = None
    collected_product_name = None
    for m in messages:
        if m.get("intent", {}).get("variant"):
            collected_variant = m["intent"]["variant"]
        if m.get("intent", {}).get("address"):
            collected_address = m["intent"]["address"]
        if m.get("intent", {}).get("product_name"):
            collected_product_name = m["intent"]["product_name"]

    # Step 5: Resolve product + amount from history
    product_name = collected_product_name or intent.get("product_name")
    amount = 0
    product_id = None
    if product_name and all_products.data:
        for p in all_products.data:
            if product_name.lower() in p["name"].lower() or p["name"].lower() in product_name.lower():
                amount = float(p["price"])
                product_id = p["id"]
                break

    # Step 6: Create order when buyer confirms AND we have variant + address + product
    order_id = None
    should_create_order = (
        intent.get("payment_readiness") == "READY" and
        collected_address and
        product_id
    )
    if should_create_order:
        order_result = supabase.table("orders").insert({
            "vendor_id": vendor_id,
            "product_id": product_id,
            "buyer_ig_handle": buyer_handle,
            "variant": collected_variant or intent.get("variant"),
            "quantity": intent.get("quantity", 1),
            "amount": amount,
            "status": "PENDING",
            "payment_status": "UNPAID"
        }).execute()
        order_id = order_result.data[0]["id"][:8].upper()

    # Step 7: Build history string
    history_lines = []
    for m in messages[:-1]:
        role = "Buyer" if m["role"] == "buyer" else "Shop"
        history_lines.append(f"{role}: {m['content']}")
    history = "\n".join(history_lines) if history_lines else "(this is the first message)"

    # Step 8: Generate reply
    reply = await chat(
        model="muse-spark-1.3",
        messages=[{
            "role": "user",
            "content": REPLY_PROMPT.format(
                shop_name=shop_name,
                message=message,
                intent=json.dumps(intent),
                products=products_str,
                variant=collected_variant or intent.get("variant") or "not yet collected",
                address=collected_address or intent.get("address") or "not yet collected",
                upi_id=upi_id,
                order_id=order_id or "N/A",
                amount=amount,
                history=history
            )
        }]
    )

    # Step 9: Save shop reply to conversation
    messages.append({"role": "shop", "content": reply})
    supabase.table("conversations")\
        .update({"messages": messages, "last_message_at": "now()"})\
        .eq("id", conv_id)\
        .execute()

    # Step 10: Log analytics
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
