import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.core.dependencies import get_current_vendor
from app.core.supabase import supabase

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
MAX_SIZE_MB = 10

@router.post("/product-image")
async def upload_product_image(
    file: UploadFile = File(...),
    vendor: dict = Depends(get_current_vendor)
):
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Use JPEG, PNG or WebP.")
    
    # Read file
    contents = await file.read()
    
    # Validate file size
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File too large. Max {MAX_SIZE_MB}MB.")
    
    # Upload to Supabase Storage
    filename = f"{uuid.uuid4()}.{file.content_type.split('/')[-1]}"
    path = f"{vendor['id']}/uploads/{filename}"
    
    supabase.storage.from_("catalogue-images").upload(
        path=path,
        file=contents,
        file_options={"content-type": file.content_type}
    )
    
    public_url = supabase.storage.from_("catalogue-images").get_public_url(path)
    
    return {"url": public_url, "filename": filename}
