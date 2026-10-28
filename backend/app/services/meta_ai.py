import httpx
from app.core.config import settings

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

async def generate_image(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{BASE_URL}/images/generations",
            headers=HEADERS,
            json={"model": "muse-image-1.0", "prompt": prompt, "n": 1}
        )
        response.raise_for_status()
        return response.json()["data"][0]["url"]
