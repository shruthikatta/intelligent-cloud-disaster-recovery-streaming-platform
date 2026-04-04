from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.database import get_db
from apps.backend.app.deps import get_current_user
from apps.backend.app.models import User, Video, WatchHistory
from apps.backend.app.schemas.video import VideoOut, WatchProgress

router = APIRouter(prefix="/watch", tags=["watch"])


@router.get("/continue", response_model=list[VideoOut])
async def continue_watching(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[Video]:
    result = await session.execute(
        select(Video)
        .join(WatchHistory, WatchHistory.video_id == Video.id)
        .where(WatchHistory.user_id == user.id)
        .order_by(WatchHistory.updated_at.desc())
    )
    return list(result.scalars().all())


@router.post("/progress")
async def save_progress(
    body: WatchProgress,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    v = await session.get(Video, body.video_id)
    if not v:
        raise HTTPException(status_code=404, detail="Video not found")
    r = await session.execute(
        select(WatchHistory).where(
            WatchHistory.user_id == user.id,
            WatchHistory.video_id == body.video_id,
        )
    )
    wh = r.scalar_one_or_none()
    if wh:
        wh.progress_sec = body.progress_sec
    else:
        wh = WatchHistory(user_id=user.id, video_id=body.video_id, progress_sec=body.progress_sec)
        session.add(wh)
    await session.commit()
    return {"ok": True}
