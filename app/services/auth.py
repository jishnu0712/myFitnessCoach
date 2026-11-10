"""Orchestrate account registration, credential verification, and tokens."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.users import add_user, get_user_by_email


async def register_user(session: AsyncSession, email: str, password: str) -> User:
    """Create a regular user account and handle concurrent duplicate emails."""
    normalized_email = email.strip().lower()
    if await get_user_by_email(session, normalized_email) is not None:
        raise ConflictException("An account with this email already exists")

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        role="user",
    )
    add_user(session, user)
    try:
        await session.commit()
        await session.refresh(user)
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictException("An account with this email already exists") from exc
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> tuple[User, str]:
    """Verify credentials and return an account with a signed access token."""
    user = await get_user_by_email(session, email.strip().lower())
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedException("Invalid email or password")
    return user, create_access_token(user.id)
