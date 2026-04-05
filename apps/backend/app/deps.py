from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.database import get_db
from apps.backend.app.models import User
from apps.backend.app.security import decode_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    sub = decode_token(creds.credentials)
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await session.execute(select(User).where(User.email == sub))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_optional_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    if not creds:
        return None
    sub = decode_token(creds.credentials)
    if not sub:
        return None
    result = await session.execute(select(User).where(User.email == sub))
    return result.scalar_one_or_none()
