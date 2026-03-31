from __future__ import annotations

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.backend.app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(Text, default="")
    poster_url: Mapped[str] = mapped_column(String(1024))
    stream_url: Mapped[str] = mapped_column(String(1024))
    category: Mapped[str] = mapped_column(String(128), index=True)
    year: Mapped[int] = mapped_column(Integer, default=2024)
    rating: Mapped[float] = mapped_column(Float, default=4.0)
    trending: Mapped[bool] = mapped_column(Boolean, default=False)

    watches: Mapped[list["WatchHistory"]] = relationship(back_populates="video")
