from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.dependencies import get_current_vendor
from app.core.supabase import supabase

router = APIRouter(prefix="/products", tags=["products"])

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    inventory_count: int = 0
    variants: list = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    inventory_count: Optional[int] = None
    variants: Optional[list] = None
    is_active: Optional[bool] = None

@router.post("/", status_code=201)
async def create_product(body: ProductCreate, vendor: dict = Depends(get_current_vendor)):
    result = supabase.table("products").insert({
        "vendor_id": vendor["id"],
        "name": body.name,
        "description": body.description,
        "price": body.price,
        "inventory_count": body.inventory_count,
        "variants": body.variants,
        "is_active": True
    }).execute()
    return result.data[0]

@router.get("/")
async def get_products(vendor: dict = Depends(get_current_vendor)):
    result = supabase.table("products")\
        .select("*")\
        .eq("vendor_id", vendor["id"])\
        .order("created_at", desc=True)\
        .execute()
    return result.data

@router.get("/{product_id}")
async def get_product(product_id: str, vendor: dict = Depends(get_current_vendor)):
    result = supabase.table("products")\
        .select("*")\
        .eq("id", product_id)\
        .eq("vendor_id", vendor["id"])\
        .single()\
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Product not found")
    return result.data

@router.patch("/{product_id}")
async def update_product(
    product_id: str,
    body: ProductUpdate,
    vendor: dict = Depends(get_current_vendor)
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = supabase.table("products")\
        .update(updates)\
        .eq("id", product_id)\
        .eq("vendor_id", vendor["id"])\
        .execute()
    return result.data[0]

@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: str, vendor: dict = Depends(get_current_vendor)):
    supabase.table("products")\
        .update({"is_active": False})\
        .eq("id", product_id)\
        .eq("vendor_id", vendor["id"])\
        .execute()
