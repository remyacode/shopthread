import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.dependencies import get_current_vendor
from app.core.supabase import supabase

router = APIRouter(prefix="/instagram", tags=["instagram"])

GRAPH_API = "https://graph.facebook.com/v21.0"
BACKEND_URL = "https://shopthread-api-272991473117.us-central1.run.app"

@router.get("/connect")
async def connect_instagram(vendor: dict = Depends(get_current_vendor)):
    oauth_url = (
        f"https://www.facebook.com/dialog/oauth"
        f"?client_id={settings.META_APP_ID}"
        f"&redirect_uri={BACKEND_URL}/instagram/callback"
        f"&scope=instagram_basic,instagram_manage_messages,pages_show_list,pages_messaging"
        f"&state={vendor['id']}"
        f"&response_type=code"
    )
    return {"oauth_url": oauth_url}

@router.get("/callback")
async def instagram_callback(
    code: str = Query(...),
    state: str = Query(...)
):
    vendor_id = state

    async with httpx.AsyncClient() as client:
        token_res = await client.get(
            f"{GRAPH_API}/oauth/access_token",
            params={
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "redirect_uri": f"{BACKEND_URL}/instagram/callback",
                "code": code
            }
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_res.text}")

        short_token = token_res.json()["access_token"]

        long_token_res = await client.get(
            f"{GRAPH_API}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "fb_exchange_token": short_token
            }
        )
        long_token = long_token_res.json().get("access_token", short_token)

        pages_res = await client.get(
            f"{GRAPH_API}/me/accounts",
            params={
                "access_token": long_token,
                "fields": "id,name,access_token,instagram_business_account"
            }
        )
        pages_data = pages_res.json()
        pages = pages_data.get("data", [])

        if not pages:
            raise HTTPException(
                status_code=400,
                detail=f"No Facebook Pages found. pages_response={pages_data}"
            )

        page = None
        for p in pages:
            if p.get("instagram_business_account"):
                page = p
                break

        if page is None:
            page_names = [p.get("name", p["id"]) for p in pages]
            raise HTTPException(
                status_code=400,
                detail=f"Found pages [{', '.join(page_names)}] but none linked to Instagram Business Account."
            )

        page_id = page["id"]
        page_token = page["access_token"]
        ig_account_id = page["instagram_business_account"]["id"]

        ig_info_res = await client.get(
            f"{GRAPH_API}/{ig_account_id}",
            params={"fields": "id,username", "access_token": page_token}
        )
        ig_handle = ig_info_res.json().get("username", "priyajewels_official")

        supabase.table("vendors").update({
            "instagram_page_id": ig_account_id,
            "instagram_access_token": page_token,
            "instagram_handle": ig_handle,
            "instagram_connected": True
        }).eq("id", vendor_id).execute()

        await client.post(
            f"{GRAPH_API}/{page_id}/subscribed_apps",
            params={
                "subscribed_fields": "messages,messaging_postbacks",
                "access_token": page_token
            }
        )

    return RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard?instagram=connected")

@router.get("/status")
async def instagram_status(vendor: dict = Depends(get_current_vendor)):
    return {
        "connected": vendor.get("instagram_connected", False),
        "instagram_page_id": vendor.get("instagram_page_id"),
        "handle": vendor.get("instagram_handle")
    }

@router.delete("/disconnect")
async def disconnect_instagram(vendor: dict = Depends(get_current_vendor)):
    supabase.table("vendors").update({
        "instagram_page_id": None,
        "instagram_access_token": None,
        "instagram_connected": False
    }).eq("id", vendor["id"]).execute()
    return {"status": "disconnected"}
