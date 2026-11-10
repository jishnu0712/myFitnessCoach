"""Expose account registration, login, and current-user endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db_session
from app.models.user import User
from app.schemas.auth import AccessTokenResponse, LoginRequest, RegisterRequest, UserResponse
from app.services.auth import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    """Create a regular account; public registration cannot assign privileged roles."""
    user = await register_user(session, str(request.email), request.password)
    return {"success": True, "data": {"user": UserResponse.model_validate(user).model_dump()}}


@router.post("/login", response_model=dict[str, object])
async def login(
    request: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, object]:
    """Validate credentials and return an expiring bearer access token."""
    user, token = await authenticate_user(session, str(request.email), request.password)
    data = AccessTokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    ).model_dump()
    return {"success": True, "data": data}


@router.get("/me")
async def get_me(
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, object]:
    """Return the authenticated account without credential data."""
    return {"success": True, "data": {"user": UserResponse.model_validate(user).model_dump()}}
