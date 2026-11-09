"""Create and expose the FastAPI application and its process lifecycle."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Configure process logging and release shared resources at shutdown.

    Database schema creation is intentionally absent; Alembic owns all schema changes.
    """
    settings = get_settings()
    configure_logging(settings.log_level)
    yield
    # The async engine is disposed by the application lifespan, not per request.
    from app.core.database import engine

    await engine.dispose()


def create_app() -> FastAPI:
    """Build the FastAPI application and register API routes and error handlers."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description="A modular API foundation for a personal fitness application.",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.include_router(api_router)
    register_exception_handlers(application)
    return application


app = create_app()
