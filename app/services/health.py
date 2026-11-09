"""Implement database readiness logic outside the HTTP route layer."""

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceUnavailableException
from app.repositories.health import verify_database_connection

logger = logging.getLogger(__name__)


async def check_database(session: AsyncSession) -> None:
    """Execute a minimal query and map database failures to a safe 503 error."""
    try:
        await verify_database_connection(session)
    except SQLAlchemyError as exc:
        # Do not log the driver message: connection errors can contain private host data.
        logger.warning("Database readiness check failed")
        raise ServiceUnavailableException("Database is unavailable") from exc
