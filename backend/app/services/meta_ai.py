import httpx
import uuid
from app.core.config import settings
from app.services.storage import upload_base64_image

BASE_URL = "https://api.meta.ai/v1"

HEADERS = {
    "Authorization": f"Bearer {settings.META_API_KEY}",
    "Content-Type": "application/json"
}

async def chat(model: str, messages: list, json_mode: bool = False) -> str:
    payload = {
        "model": model,
        "messages": messages
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{BASE_URL}/chat/completions",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

async def transcribe_audio(audio_url: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{BASE_URL}/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.META_API_KEY}"},
            json={"model": "muse-voice-transcribe-1.0", "url": audio_url}
        )
        response.raise_for_status()
        return response.json()["text"]

async def generate_image(prompt: str, vendor_id: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{BASE_URL}/images/generations",
            headers=HEADERS,
            json={
                "model": "muse-image-1.0",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024"
            }
        )
        if response.status_code != 200:
            print(f"Muse Image error: {response.status_code} - {response.text}")
            raise Exception(f"Muse Image failed: {response.text}")

        data = response.json()
        item = data["data"][0]

        if "url" in item:
            return item["url"]

        if "b64_json" in item:
            filename = f"{uuid.uuid4()}.webp"
            url = await upload_base64_image(item["b64_json"], filename, vendor_id)
            return url

        raise Exception(f"Unexpected Muse Image response: {data}")
