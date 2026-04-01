from __future__ import annotations

from pydantic import BaseModel, Field


class VideoOut(BaseModel):
    id: int
    title: str
    description: str
    poster_url: str
    stream_url: str
    category: str
    year: int
    rating: float
    trending: bool

    model_config = {"from_attributes": True}


class WatchProgress(BaseModel):
    video_id: int
    progress_sec: int = Field(ge=0)
