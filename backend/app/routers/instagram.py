import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.core.dependencies import get_current_vendor
from app.core.supabase import supabase

router = APIRouter(prefix="/instagram", tags=["instagram"])

GRAPH_API = "https://graph.facebook.com/v21.0"

@router.get("/connect")
async def connect_instagram(vendor: dict = Depends(get_current_vendor)):
    """Generate Instagram OAuth URL for vendor to authorize"""
    oauth_url = (
        f"https://www.facebook.com/dialog/oauth"
        f"?client_id={settings.META_APP_ID}"
        f"&redirect_uri={settings.FRONTEND_URL}/api/instagram/callback"
        f"&scope=instagram_basic,instagram_manage_messages,pages_manage_metadata,pages_show_list"
        f"&state={vendor['id']}"
        f"&response_type=code"
    )
    return {"oauth_url": oauth_url}

@router.get("/callback")
async def instagram_callback(
    code: str = Query(...),
    state: str = Query(...)
):
    """Handle OAuth callback — exchange code for access token"""
    vendor_id = state

    async with httpx.AsyncClient() as client:
        # Exchange code for short-lived token
        token_res = await client.get(
            f"{GRAPH_API}/oauth/access_token",
            params={
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "redirect_uri": f"{settings.FRONTEND_URL}/api/instagram/callback",
                "code": code
            }
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_res.text}")
        
        short_token = token_res.json()["access_token"]

        # Exchange for long-lived token (60 days)
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

        # Get Instagram Business Account ID
        pages_res = await client.get(
            f"{GRAPH_API}/me/accounts",
            params={"access_token": long_token}
        )
        pages = pages_res.json().get("data", [])

        if not pages:
            raise HTTPException(status_code=400, detail="No Facebook Pages found. Please connect a Facebook Page linked to your Instagram Business account.")

        # Use first page
        page = pages[0]
        page_id = page["id"]
        page_token = page["access_token"]

        # Get Instagram Business Account linked to this page
        ig_res = await client.get(
            f"{GRAPH_API}/{page_id}",
            params={
                "fields": "instagram_business_account",
                "access_token": page_token
            }
        )
        ig_data = ig_res.json()
        ig_account_id = ig_data.get("instagram_business_account", {}).get("id")

        if not ig_account_id:
            raise HTTPException(status_code=400, detail="No Instagram Business account linked to this Facebook Page.")

        # Save to vendor
        supabase.table("vendors").update({
            "instagram_page_id": ig_account_id,
            "instagram_access_token": page_token,
            "instagram_connected": True
        }).eq("id", vendor_id).execute()

        # Subscribe page to webhook
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
    """Check if vendor has connected Instagram"""
    return {
        "connected": vendor.get("instagram_connected", False),
        "instagram_page_id": vendor.get("instagram_page_id"),
        "handle": vendor.get("instagram_handle")
    }

@router.delete("/disconnect")
async def disconnect_instagram(vendor: dict = Depends(get_current_vendor)):
    """Disconnect Instagram from vendor account"""
    supabase.table("vendors").update({
        "instagram_page_id": None,
        "instagram_access_token": None,
        "instagram_connected": False
    }).eq("id", vendor["id"]).execute()
    return {"status": "disconnected"}
