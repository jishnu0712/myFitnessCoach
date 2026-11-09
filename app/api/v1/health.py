"""Expose liveness and PostgreSQL readiness checks for API operators."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.services.health import check_database

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    summary="Check API health",
    description="Confirm that the API process is responsive.",
)
async def get_health() -> dict[str, object]:
    """Return a lightweight liveness response without requiring PostgreSQL."""
    return {"success": True, "data": {"status": "healthy"}}


@router.get(
    "/db",
    summary="Check database health",
    description="Run a lightweight query to confirm PostgreSQL is reachable.",
    responses={503: {"description": "The database is unavailable"}},
)
async def get_database_health(
    session: AsyncSession = Depends(get_db_session),  # noqa: B008
) -> dict[str, object]:
    """Return readiness only when the configured PostgreSQL connection works."""
    await check_database(session)
    return {"success": True, "data": {"status": "healthy"}}
