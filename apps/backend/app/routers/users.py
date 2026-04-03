from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from apps.backend.app.deps import get_current_user
from apps.backend.app.models import User
from apps.backend.app.schemas.auth import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
