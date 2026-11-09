"""Contain the minimal PostgreSQL query used by the readiness check."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def verify_database_connection(session: AsyncSession) -> None:
    """Run a no-side-effect query to confirm the session can reach PostgreSQL."""
    await session.execute(text("SELECT 1"))
