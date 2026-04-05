from __future__ import annotations

"""StreamVault API — FastAPI entrypoint."""


from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.config.settings import get_settings

from apps.backend.app.database import Base, engine
from apps.backend.app.routers import admin, auth, health, users, videos, watch
from services.monitoring.metric_simulator import get_simulator


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("data").mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    get_simulator().start_background(interval_sec=3.0)
    yield
    get_simulator().stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="StreamVault API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(videos.router, prefix="/api")
    app.include_router(watch.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")
    return app


app = create_app()
