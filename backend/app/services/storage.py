import base64
from app.core.supabase import supabase

async def upload_base64_image(b64_data: str, filename: str, vendor_id: str) -> str:
    """Upload base64 image to Supabase Storage and return public URL"""
    image_bytes = base64.b64decode(b64_data)
    path = f"{vendor_id}/{filename}"
    
    supabase.storage.from_("catalogue-images").upload(
        path=path,
        file=image_bytes,
        file_options={"content-type": "image/webp"}
    )
    
    result = supabase.storage.from_("catalogue-images").get_public_url(path)
    return result
