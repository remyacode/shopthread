from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_vendor
from app.agents.growth_radar import generate_weekly_brief, get_metrics

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/metrics")
async def get_dashboard_metrics(vendor: dict = Depends(get_current_vendor)):
    return await get_metrics(vendor["id"])

@router.get("/weekly-brief")
async def get_weekly_brief(vendor: dict = Depends(get_current_vendor)):
    return await generate_weekly_brief(vendor["id"])
