import json
import httpx
from app.services.meta_ai import chat, generate_image
from app.core.supabase import supabase
from app.core.config import settings

BASE_URL = "https://api.meta.ai/v1"
HEADERS = {
    "Authorization": f"Bearer {settings.META_API_KEY}",
    "Content-Type": "application/json"
}

COPY_PROMPT = """You are a product copywriter for an Indian jewellery brand.

Product name: {product_name}
Jewellery details: {details}

Generate product copy and return ONLY a valid JSON object:
{{
  "title": "compelling product title under 60 chars",
  "description": "150 word product description highlighting craftsmanship and occasion",
  "captions_en": [
    "Instagram caption 1 with emojis and hashtags",
    "Instagram caption 2 with emojis and hashtags",
    "Instagram caption 3 with emojis and hashtags"
  ],
  "captions_hi": [
    "Hindi Instagram caption 1 with emojis",
    "Hindi Instagram caption 2 with emojis",
    "Hindi Instagram caption 3 with emojis"
  ]
}}"""

async def identify_jewellery(image_url: str, product_name: str, product_description: str) -> dict:
    """Use Muse Wonder to identify jewellery type from image, with product name as fallback context"""
    
    IDENTIFY_PROMPT = f"""You are a jewellery expert AI. This is a product image of: "{product_name}".
Analyze the jewellery and return ONLY a valid JSON object:
{{
  "jewellery_type": "earring|necklace|ring|bracelet|anklet|maangtika|other",
  "style": "traditional|contemporary|fusion|bridal|casual",
  "material": "gold|silver|oxidised|kundan|meenakari|pearl|stone|mixed",
  "color": "primary color description",
  "occasion": "daily|wedding|festival|party|office",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}}"""

    async with httpx.AsyncClient(timeout=60) as client:
        payload = {
            "model": "muse-wonder-1.0",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": IDENTIFY_PROMPT}
                ]
            }]
        }
        response = await client.post(f"{BASE_URL}/chat/completions", headers=HEADERS, json=payload)

        if response.status_code != 200:
            print(f"Muse Wonder error: {response.status_code} - using product name as context")
            # Fallback: derive from product name using Muse Spark
            fallback_prompt = f"""You are a jewellery expert. The product is called "{product_name}". {product_description}
            
Return ONLY a valid JSON object:
{{
  "jewellery_type": "earring|necklace|ring|bracelet|anklet|maangtika|other",
  "style": "traditional|contemporary|fusion|bridal|casual",
  "material": "gold|silver|oxidised|kundan|meenakari|pearl|stone|mixed",
  "color": "primary color description",
  "occasion": "daily|wedding|festival|party|office",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}}"""
            fallback = await chat(
                model="muse-spark-1.3",
                messages=[{"role": "user", "content": fallback_prompt}],
                json_mode=True
            )
            try:
                start = fallback.find("{")
                end = fallback.rfind("}") + 1
                return json.loads(fallback[start:end])
            except:
                pass
            return {
                "jewellery_type": "earring", "style": "traditional",
                "material": "gold", "color": "golden",
                "occasion": "festival", "keywords": [product_name.lower(), "handmade", "indian"]
            }

        raw = response.json()["choices"][0]["message"]["content"]
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            return json.loads(raw[start:end])
        except:
            return {
                "jewellery_type": "earring", "style": "traditional",
                "material": "gold", "color": "golden",
                "occasion": "festival", "keywords": [product_name.lower(), "handmade", "indian"]
            }

async def segment_image(image_url: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{BASE_URL}/images/segmentation",
            headers=HEADERS,
            json={"model": "sam-3.1", "image_url": image_url, "output_format": "png_transparent"}
        )
        if response.status_code == 200:
            return response.json().get("segmented_url", image_url)
        print(f"SAM 3.1 error: {response.status_code} - {response.text}")
        return image_url

async def generate_lifestyle_images(details: dict, vendor_id: str, product_name: str) -> list:
    prompts = [
        f"Professional product photography of {product_name}, {details.get('material', 'gold')} {details.get('color', 'golden')}, pure white background, studio lighting, high resolution",
        f"Lifestyle photo of Indian woman wearing {product_name}, {details.get('style', 'traditional')} Indian style, soft natural lighting, elegant, {details.get('occasion', 'festival')} occasion",
        f"Aesthetic flat lay of {product_name}, {details.get('material', 'gold')} finish, arranged on silk fabric, warm tones, overhead shot, Instagram worthy"
    ]
    urls = []
    for prompt in prompts:
        try:
            url = await generate_image(prompt, vendor_id)
            urls.append(url)
            print(f"Image generated: {url[:60]}...")
        except Exception as e:
            print(f"Image generation failed: {e}")
    return urls

async def process_catalogue(
    vendor_id: str,
    product_id: str,
    image_url: str,
    product_name: str = "jewellery",
    product_description: str = ""
) -> dict:
    pack_result = supabase.table("content_packs").insert({
        "vendor_id": vendor_id,
        "product_id": product_id,
        "raw_image_url": image_url,
        "status": "PROCESSING"
    }).execute()
    pack_id = pack_result.data[0]["id"]

    try:
        # Step 1: Identify jewellery with Muse Wonder + product context
        details = await identify_jewellery(image_url, product_name, product_description)
        print(f"Identified: {details}")

        # Step 2: Segment with SAM 3.1
        segmented_url = await segment_image(image_url)

        # Step 3: Generate lifestyle images with Muse Image
        lifestyle_urls = await generate_lifestyle_images(details, vendor_id, product_name)
        print(f"Generated {len(lifestyle_urls)} images")

        # Step 4: Generate copy with Muse Spark
        copy_raw = await chat(
            model="muse-spark-1.3",
            messages=[{"role": "user", "content": COPY_PROMPT.format(
                product_name=product_name,
                details=json.dumps(details)
            )}],
            json_mode=True
        )
        try:
            start = copy_raw.find("{")
            end = copy_raw.rfind("}") + 1
            copy = json.loads(copy_raw[start:end])
        except:
            copy = {
                "title": product_name,
                "description": f"Handcrafted {product_name} with exquisite detailing.",
                "captions_en": [f"Beautiful {product_name} ✨ #handmade #jewellery"],
                "captions_hi": [f"सुंदर {product_name} ✨ #हस्तनिर्मित"]
            }

        supabase.table("content_packs").update({
            "segmented_image_url": segmented_url,
            "lifestyle_urls": lifestyle_urls,
            "title": copy.get("title"),
            "description": copy.get("description"),
            "captions_en": copy.get("captions_en", []),
            "captions_hi": copy.get("captions_hi", []),
            "status": "READY"
        }).eq("id", pack_id).execute()

        supabase.table("analytics_events").insert({
            "vendor_id": vendor_id,
            "event_type": "CATALOGUE_GENERATED",
            "metadata": {"pack_id": pack_id, "jewellery_type": details.get("jewellery_type"), "product_name": product_name}
        }).execute()

        return {
            "pack_id": pack_id,
            "details": details,
            "segmented_url": segmented_url,
            "lifestyle_urls": lifestyle_urls,
            "copy": copy,
            "status": "READY"
        }

    except Exception as e:
        print(f"CatalogueForge error: {e}")
        supabase.table("content_packs").update({"status": "FAILED"}).eq("id", pack_id).execute()
        raise e
