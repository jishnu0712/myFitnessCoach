"""Create the async SQLAlchemy engine and provide request-scoped sessions."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield a session and ensure its resources are released after a request.

    The dependency does not commit automatically: transaction boundaries belong
    to the service or repository operation that knows whether work succeeded.
    """
    async with SessionFactory() as session:
        yield session
