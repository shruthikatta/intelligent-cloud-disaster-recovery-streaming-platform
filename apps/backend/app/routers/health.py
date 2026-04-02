from __future__ import annotations

from fastapi import APIRouter

from shared.config.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "app_mode": s.app_mode,
        "primary_region": s.primary_region,
        "dr_region": s.dr_region,
    }
