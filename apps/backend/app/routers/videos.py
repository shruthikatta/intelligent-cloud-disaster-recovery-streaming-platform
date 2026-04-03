from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.database import get_db
from apps.backend.app.models import Video
from apps.backend.app.schemas.video import VideoOut

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/trending", response_model=list[VideoOut])
async def trending(session: Annotated[AsyncSession, Depends(get_db)]) -> list[Video]:
    result = await session.execute(select(Video).where(Video.trending.is_(True)))
    return list(result.scalars().all())


@router.get("/search/live", response_model=list[VideoOut])
async def search_live(
    session: Annotated[AsyncSession, Depends(get_db)],
    term: str = Query(..., min_length=1),
) -> list[Video]:
    result = await session.execute(select(Video).where(Video.title.ilike(f"%{term}%")))
    return list(result.scalars().all())


@router.get("", response_model=list[VideoOut])
async def list_videos(
    session: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = None,
    q: str | None = None,
) -> list[Video]:
    stmt = select(Video)
    if category:
        stmt = stmt.where(Video.category == category)
    if q:
        stmt = stmt.where(Video.title.ilike(f"%{q}%"))
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{video_id}", response_model=VideoOut)
async def get_video(video_id: int, session: Annotated[AsyncSession, Depends(get_db)]) -> Video:
    result = await session.execute(select(Video).where(Video.id == video_id))
    v = result.scalar_one_or_none()
    if not v:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Not found")
    return v
