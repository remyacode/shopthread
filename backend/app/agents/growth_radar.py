import json
from app.services.meta_ai import chat
from app.core.supabase import supabase

WEEKLY_BRIEF_PROMPT = """You are GrowthRadar, an AI business intelligence agent for an Instagram jewellery seller.

Here is the seller's data for this week:
{data}

Generate a concise, actionable weekly intelligence brief. Return ONLY a valid JSON object:
{{
  "headline": "one sentence summary of the week",
  "top_insights": [
    "insight 1 — specific and actionable",
    "insight 2 — specific and actionable",
    "insight 3 — specific and actionable"
  ],
  "best_seller": {{
    "product": "product name or null",
    "reason": "why it performed well"
  }},
  "dead_inventory": [
    "product name with zero orders"
  ],
  "buyer_signals": [
    "what buyers are asking for that you don't have"
  ],
  "action_this_week": [
    "specific action 1 to take this week",
    "specific action 2 to take this week"
  ],
  "revenue_summary": {{
    "total": number,
    "orders": number,
    "avg_order_value": number
  }}
}}"""

async def generate_weekly_brief(vendor_id: str) -> dict:
    """Generate a weekly intelligence brief using real vendor data"""

    # Fetch orders this week
    orders = supabase.table("orders")\
        .select("*, products(name)")\
        .eq("vendor_id", vendor_id)\
        .order("created_at", desc=True)\
        .execute()

    # Fetch conversations
    conversations = supabase.table("conversations")\
        .select("messages")\
        .eq("vendor_id", vendor_id)\
        .execute()

    # Fetch products
    products = supabase.table("products")\
        .select("name, price, inventory_count")\
        .eq("vendor_id", vendor_id)\
        .eq("is_active", True)\
        .execute()

    # Fetch analytics events
    events = supabase.table("analytics_events")\
        .select("event_type, metadata")\
        .eq("vendor_id", vendor_id)\
        .order("occurred_at", desc=True)\
        .limit(100)\
        .execute()

    # Aggregate order data
    total_revenue = sum(float(o.get("amount", 0)) for o in (orders.data or []))
    total_orders = len(orders.data or [])
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    # Product performance
    product_order_counts: dict = {}
    for order in (orders.data or []):
        product_name = order.get("products", {}).get("name") if order.get("products") else None
        if product_name:
            product_order_counts[product_name] = product_order_counts.get(product_name, 0) + 1

    # Extract DM intents
    dm_intents = []
    for conv in (conversations.data or []):
        for msg in (conv.get("messages") or []):
            if msg.get("intent"):
                dm_intents.append(msg["intent"])

    # Build data summary for Muse Spark
    data_summary = {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "product_performance": product_order_counts,
        "active_products": [p["name"] for p in (products.data or [])],
        "low_inventory": [p["name"] for p in (products.data or []) if p.get("inventory_count", 0) < 3],
        "dm_count": len(conversations.data or []),
        "dm_intents_summary": {
            "orders": len([i for i in dm_intents if i.get("message_type") == "ORDER"]),
            "inquiries": len([i for i in dm_intents if i.get("message_type") == "INQUIRY"]),
            "returns": len([i for i in dm_intents if i.get("message_type") == "RETURN"]),
        },
        "content_packs_generated": len([e for e in (events.data or []) if e.get("event_type") == "CATALOGUE_GENERATED"])
    }

    # Generate brief with Muse Spark
    brief_raw = await chat(
        model="muse-spark-1.3",
        messages=[{"role": "user", "content": WEEKLY_BRIEF_PROMPT.format(data=json.dumps(data_summary, indent=2))}],
        json_mode=True
    )

    try:
        start = brief_raw.find("{")
        end = brief_raw.rfind("}") + 1
        brief = json.loads(brief_raw[start:end])
    except:
        brief = {
            "headline": f"Week summary: {total_orders} orders, ₹{total_revenue:.0f} revenue",
            "top_insights": [
                f"Total revenue this period: ₹{total_revenue:.0f}",
                f"Average order value: ₹{avg_order_value:.0f}",
                f"Total DM conversations: {len(conversations.data or [])}"
            ],
            "best_seller": {"product": max(product_order_counts, key=product_order_counts.get) if product_order_counts else None, "reason": "Most ordered product"},
            "dead_inventory": [],
            "buyer_signals": [],
            "action_this_week": ["Keep posting product content", "Follow up with pending orders"],
            "revenue_summary": {"total": total_revenue, "orders": total_orders, "avg_order_value": avg_order_value}
        }

    # Log analytics
    supabase.table("analytics_events").insert({
        "vendor_id": vendor_id,
        "event_type": "WEEKLY_BRIEF_GENERATED",
        "metadata": {"orders": total_orders, "revenue": total_revenue}
    }).execute()

    return {
        "brief": brief,
        "raw_data": data_summary
    }

async def get_metrics(vendor_id: str) -> dict:
    """Get real-time metrics for the dashboard"""
    orders = supabase.table("orders")\
        .select("amount, status, payment_status, created_at")\
        .eq("vendor_id", vendor_id)\
        .execute()

    conversations = supabase.table("conversations")\
        .select("id, last_message_at")\
        .eq("vendor_id", vendor_id)\
        .execute()

    products = supabase.table("products")\
        .select("id")\
        .eq("vendor_id", vendor_id)\
        .eq("is_active", True)\
        .execute()

    total_revenue = sum(float(o.get("amount", 0)) for o in (orders.data or []) if o.get("payment_status") == "PAID")
    total_orders = len(orders.data or [])
    pending_orders = len([o for o in (orders.data or []) if o.get("status") == "PENDING"])
    active_products = len(products.data or [])
    total_conversations = len(conversations.data or [])

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "active_products": active_products,
        "total_conversations": total_conversations
    }
