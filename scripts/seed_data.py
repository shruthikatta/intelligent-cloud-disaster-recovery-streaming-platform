from __future__ import annotations

"""
Seed SQLite database with demo users and catalog.

Re-running is safe: demo users are upserted (passwords reset to seed values).
Catalog videos: new titles are inserted; existing titles get stream_url refreshed from
video_catalog.py (so broken demo CDN URLs can be fixed without wiping the DB).

Usage (repo root, venv active):
  PYTHONPATH=. python scripts/seed_data.py
"""


import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS))

from sqlalchemy import select, update

from video_catalog import CATALOG

from apps.backend.app.database import async_session_factory, engine
from apps.backend.app.demo_accounts import DEMO_ACCOUNTS
from apps.backend.app.models import User, Video, WatchHistory
from apps.backend.app.security import hash_password


async def seed() -> None:
    from apps.backend.app.database import Base

    Path("data").mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Upsert demo users so re-running seed adds new accounts (e.g. admin@) and resets demo passwords.
        for acct in DEMO_ACCOUNTS:
            result = await session.execute(select(User).where(User.email == acct["email"]))
            user = result.scalar_one_or_none()
            pw_hash = hash_password(acct["password"])
            if user is None:
                session.add(User(email=acct["email"], hashed_password=pw_hash))
            else:
                user.hashed_password = pw_hash
        await session.flush()

        for row in CATALOG:
            result = await session.execute(select(Video).where(Video.title == row["title"]))
            existing = result.scalar_one_or_none()
            if existing is not None:
                existing.stream_url = row["stream"]
                continue
            session.add(
                Video(
                    title=row["title"],
                    description=row["description"],
                    poster_url=row["poster"],
                    stream_url=row["stream"],
                    category=row["category"],
                    year=row["year"],
                    rating=row["rating"],
                    trending=row["trending"],
                )
            )
        await session.flush()

        # Fix rows that still reference the Cast sample bucket (403 in many environments).
        if CATALOG:
            await session.execute(
                update(Video)
                .where(Video.stream_url.like("%gtv-videos-bucket%"))
                .values(stream_url=CATALOG[0]["stream"])
            )

        demo_user = (
            await session.execute(select(User).where(User.email == "demo@streamvault.io"))
        ).scalar_one_or_none()
        first_videos = (await session.execute(select(Video).order_by(Video.id).limit(3))).scalars().all()
        if demo_user and first_videos:
            for vid in first_videos:
                wh = await session.execute(
                    select(WatchHistory).where(
                        WatchHistory.user_id == demo_user.id,
                        WatchHistory.video_id == vid.id,
                    )
                )
                if wh.scalar_one_or_none() is None:
                    session.add(
                        WatchHistory(
                            user_id=demo_user.id,
                            video_id=vid.id,
                            progress_sec=min(120 + vid.id * 30, 600),
                        )
                    )

        await session.commit()
    print("Seed complete. Demo accounts (see apps/backend/app/demo_accounts.py):")
    for a in DEMO_ACCOUNTS:
        print(f"  {a['email']} / {a['password']} — {a['label']}")


if __name__ == "__main__":
    asyncio.run(seed())
