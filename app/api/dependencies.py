"""Shared HTTP dependencies for authenticated API routes."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.users import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """Resolve the bearer token to a persisted account or return HTTP 401."""
    if credentials is None:
        raise UnauthorizedException("Authentication required")
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise UnauthorizedException("Invalid or expired access token")
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise UnauthorizedException("Invalid or expired access token")
    return user
