"""
Seed script — populates demo data for ShopThread
Run: python3 seed.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent / ".env")

from app.core.supabase import supabase
from app.core.security import hash_password

# ── Demo vendor ──────────────────────────────────────────────
VENDOR_EMAIL = "demo@shopthread.com"
VENDOR_PASSWORD = "Demo1234!"

PRODUCTS = [
    {"name": "Gold Jhumka", "description": "Traditional gold plated jhumka earrings with intricate filigree work", "price": 1299, "inventory_count": 15, "variants": ["small", "medium", "large"]},
    {"name": "Oxidised Silver Chandbali", "description": "Antique oxidised silver chandbali earrings with pearl drops", "price": 899, "inventory_count": 8, "variants": ["small", "large"]},
    {"name": "Kundan Necklace Set", "description": "Bridal kundan necklace with matching earrings and maangtika", "price": 4999, "inventory_count": 3, "variants": ["standard"]},
    {"name": "Pearl Bangles Set", "description": "Set of 4 pearl and gold bangles, perfect for weddings", "price": 1599, "inventory_count": 12, "variants": ["2.4", "2.6", "2.8"]},
    {"name": "Meenakari Ring", "description": "Handcrafted meenakari ring with blue and green enamel work", "price": 699, "inventory_count": 20, "variants": ["6", "7", "8", "9"]},
    {"name": "Temple Gold Necklace", "description": "South Indian temple jewellery necklace with lakshmi motifs", "price": 3499, "inventory_count": 5, "variants": ["standard"]},
    {"name": "Silver Payal Set", "description": "Traditional silver anklet pair with ghungroo bells", "price": 799, "inventory_count": 10, "variants": ["standard"]},
]

DM_CONVERSATIONS = [
    {
        "buyer": "priya_sharma_jaipur",
        "messages": [
            {"role": "buyer", "content": "Hi! Mujhe woh gold jhumka chahiye, small size available hai?", "intent": {"message_type": "INQUIRY", "product_name": "gold jhumka", "variant": "small", "quantity": 1, "payment_readiness": "ASKING", "reply_needed": True, "extracted_language": "mixed"}},
            {"role": "buyer", "content": "Haan le leti hun, book kar do please", "intent": {"message_type": "ORDER", "product_name": "gold jhumka", "variant": "small", "quantity": 1, "payment_readiness": "READY", "reply_needed": True, "extracted_language": "mixed"}},
        ]
    },
    {
        "buyer": "meera_bridal_looks",
        "messages": [
            {"role": "buyer", "content": "Do you have kundan necklace sets for bridal?", "intent": {"message_type": "INQUIRY", "product_name": "kundan necklace", "variant": None, "quantity": 1, "payment_readiness": "ASKING", "reply_needed": True, "extracted_language": "en"}},
            {"role": "buyer", "content": "What is the price and can you share more photos?", "intent": {"message_type": "INQUIRY", "product_name": "kundan necklace", "variant": None, "quantity": 1, "payment_readiness": "UNKNOWN", "reply_needed": True, "extracted_language": "en"}},
            {"role": "buyer", "content": "I'll take it! Please book one set for me", "intent": {"message_type": "ORDER", "product_name": "kundan necklace", "variant": "standard", "quantity": 1, "payment_readiness": "READY", "reply_needed": True, "extracted_language": "en"}},
        ]
    },
    {
        "buyer": "sunita_kolkata_jewels",
        "messages": [
            {"role": "buyer", "content": "Bhaiya silver payal ka kya rate hai?", "intent": {"message_type": "INQUIRY", "product_name": "silver payal", "variant": None, "quantity": 1, "payment_readiness": "ASKING", "reply_needed": True, "extracted_language": "hi"}},
        ]
    },
    {
        "buyer": "divya_pune_fashion",
        "messages": [
            {"role": "buyer", "content": "I want to return the meenakari ring, it's too small", "intent": {"message_type": "RETURN", "product_name": "meenakari ring", "variant": None, "quantity": 1, "payment_readiness": "UNKNOWN", "reply_needed": True, "extracted_language": "en"}},
        ]
    },
    {
        "buyer": "ananya_mumbai_bride",
        "messages": [
            {"role": "buyer", "content": "Temple gold necklace kitne ka hai? Wedding ke liye chahiye", "intent": {"message_type": "INQUIRY", "product_name": "temple gold necklace", "variant": None, "quantity": 1, "payment_readiness": "ASKING", "reply_needed": True, "extracted_language": "mixed"}},
            {"role": "buyer", "content": "Book kar do 1 piece, payment bhej deti hun", "intent": {"message_type": "ORDER", "product_name": "temple gold necklace", "variant": "standard", "quantity": 1, "payment_readiness": "READY", "reply_needed": True, "extracted_language": "mixed"}},
        ]
    },
]

ORDER_STATUSES = ["DELIVERED", "SHIPPED", "CONFIRMED", "PENDING", "DELIVERED"]

def seed():
    print("🌱 Seeding ShopThread demo data...")

    # 1. Create or fetch demo vendor
    existing = supabase.table("vendors").select("id").eq("email", VENDOR_EMAIL).execute()
    if existing.data:
        vendor_id = existing.data[0]["id"]
        print(f"✓ Demo vendor exists: {vendor_id}")
    else:
        result = supabase.table("vendors").insert({
            "email": VENDOR_EMAIL,
            "password_hash": hash_password(VENDOR_PASSWORD),
            "full_name": "Priya Jewels",
            "instagram_handle": "priyajewels_official",
            "upi_id": "priyajewels@upi",
            "plan": "pro"
        }).execute()
        vendor_id = result.data[0]["id"]
        print(f"✓ Created demo vendor: {vendor_id}")

    # 2. Create products
    product_ids = {}
    for p in PRODUCTS:
        existing = supabase.table("products").select("id").eq("vendor_id", vendor_id).eq("name", p["name"]).execute()
        if existing.data:
            product_ids[p["name"]] = existing.data[0]["id"]
            print(f"  ✓ Product exists: {p['name']}")
        else:
            result = supabase.table("products").insert({**p, "vendor_id": vendor_id, "is_active": True}).execute()
            product_ids[p["name"]] = result.data[0]["id"]
            print(f"  ✓ Created product: {p['name']}")

    # 3. Create conversations and orders
    for i, conv_data in enumerate(DM_CONVERSATIONS):
        buyer = conv_data["buyer"]
        messages = conv_data["messages"]

        # Check if conversation exists
        existing = supabase.table("conversations").select("id").eq("vendor_id", vendor_id).eq("buyer_ig_handle", buyer).execute()
        if existing.data:
            print(f"  ✓ Conversation exists: @{buyer}")
            conv_id = existing.data[0]["id"]
        else:
            result = supabase.table("conversations").insert({
                "vendor_id": vendor_id,
                "buyer_ig_handle": buyer,
                "messages": messages
            }).execute()
            conv_id = result.data[0]["id"]
            print(f"  ✓ Created conversation: @{buyer}")

        # Create order for ORDER intents
        for msg in messages:
            if msg["intent"]["message_type"] == "ORDER":
                product_name = msg["intent"].get("product_name", "")
                matching_product = next((name for name in product_ids if product_name.lower() in name.lower()), None)
                product_id = product_ids.get(matching_product) if matching_product else None
                price = next((p["price"] for p in PRODUCTS if p["name"] == matching_product), 999)

                existing_order = supabase.table("orders").select("id").eq("vendor_id", vendor_id).eq("buyer_ig_handle", buyer).execute()
                if not existing_order.data:
                    order_result = supabase.table("orders").insert({
                        "vendor_id": vendor_id,
                        "product_id": product_id,
                        "buyer_ig_handle": buyer,
                        "variant": msg["intent"].get("variant"),
                        "quantity": msg["intent"].get("quantity", 1),
                        "amount": price,
                        "status": ORDER_STATUSES[i % len(ORDER_STATUSES)],
                        "payment_status": "PAID" if ORDER_STATUSES[i % len(ORDER_STATUSES)] in ["DELIVERED", "SHIPPED"] else "UNPAID"
                    }).execute()
                    print(f"  ✓ Created order for @{buyer}: {matching_product} ₹{price}")

    # 4. Log analytics events
    supabase.table("analytics_events").insert([
        {"vendor_id": vendor_id, "event_type": "DM_PROCESSED", "metadata": {"message_type": "ORDER", "buyer": "priya_sharma_jaipur"}},
        {"vendor_id": vendor_id, "event_type": "DM_PROCESSED", "metadata": {"message_type": "INQUIRY", "buyer": "sunita_kolkata_jewels"}},
        {"vendor_id": vendor_id, "event_type": "CATALOGUE_GENERATED", "metadata": {"jewellery_type": "earring"}},
        {"vendor_id": vendor_id, "event_type": "CATALOGUE_GENERATED", "metadata": {"jewellery_type": "necklace"}},
        {"vendor_id": vendor_id, "event_type": "ORDER_STATUS_UPDATED", "metadata": {"new_status": "SHIPPED"}},
    ]).execute()

    print(f"\n✅ Seed complete!")
    print(f"   Demo login: {VENDOR_EMAIL} / {VENDOR_PASSWORD}")
    print(f"   Vendor ID: {vendor_id}")

if __name__ == "__main__":
    seed()
