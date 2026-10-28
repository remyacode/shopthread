from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.dependencies import get_current_vendor
from app.core.supabase import supabase
from app.agents.catalogue_forge import process_catalogue

router = APIRouter(prefix="/catalogue", tags=["catalogue"])

class CatalogueRequest(BaseModel):
    product_id: str
    image_url: str

@router.post("/generate")
async def generate_catalogue(body: CatalogueRequest, vendor: dict = Depends(get_current_vendor)):
    # Fetch product name to pass as context
    product = supabase.table("products")\
        .select("name, description")\
        .eq("id", body.product_id)\
        .eq("vendor_id", vendor["id"])\
        .single()\
        .execute()
    
    if not product.data:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await process_catalogue(
        vendor_id=vendor["id"],
        product_id=body.product_id,
        image_url=body.image_url,
        product_name=product.data["name"],
        product_description=product.data.get("description", "")
    )
    return result

@router.get("/")
async def get_content_packs(vendor: dict = Depends(get_current_vendor)):
    result = supabase.table("content_packs")\
        .select("*, products(name)")\
        .eq("vendor_id", vendor["id"])\
        .order("created_at", desc=True)\
        .execute()
    return result.data

@router.get("/{pack_id}")
async def get_content_pack(pack_id: str, vendor: dict = Depends(get_current_vendor)):
    result = supabase.table("content_packs")\
        .select("*, products(name)")\
        .eq("id", pack_id)\
        .eq("vendor_id", vendor["id"])\
        .single()\
        .execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Content pack not found")
    return result.data
