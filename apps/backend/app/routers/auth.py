from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.database import get_db
from apps.backend.app.demo_accounts import DEMO_ACCOUNTS
from apps.backend.app.models import User
from apps.backend.app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from apps.backend.app.security import create_access_token, hash_password, verify_password
from shared.config.settings import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/demo-accounts")
async def demo_accounts() -> list[dict[str, str]]:
    """Returns seeded demo emails/passwords only in mock mode (for class demos). Empty in aws mode."""
    if get_settings().app_mode != "mock":
        return []
    return [dict(a) for a in DEMO_ACCOUNTS]


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, session: Annotated[AsyncSession, Depends(get_db)]) -> TokenResponse:
    existing = await session.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=body.email, hashed_password=hash_password(body.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    token = create_access_token(user.email)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: Annotated[AsyncSession, Depends(get_db)]) -> TokenResponse:
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.email)
    return TokenResponse(access_token=token)
