"""Database operations for account lookup and creation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Find one account by its normalized unique email address."""
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Find one account by its primary key."""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def add_user(session: AsyncSession, user: User) -> None:
    """Add a new account to the current transaction."""
    session.add(user)
