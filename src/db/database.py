from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from starlette.requests import Request

__all__ = (
    "Database",
    "get_db_session",
)


class Database:
    """
    Database connection manager for async SQLAlchemy operations.

    Handles engine creation, session management, and connection cleanup
    for PostgreSQL database with asyncpg driver.
    """

    def __init__(self, url: str):
        self.url = url
        self.engine: AsyncEngine | None = None
        self.async_session_local: AsyncSession | None = None

    def init_async_session_maker(self):
        """Initialize async session factory with database engine."""
        self.engine = create_async_engine(url=self.url, future=True)
        self.async_session_local = async_sessionmaker(bind=self.engine, expire_on_commit=False)

    async def aclose(self) -> None:
        """Close database engine and cleanup connections."""
        if self.engine is not None:
            await self.engine.dispose()

    @asynccontextmanager
    async def get_db_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for database sessions with automatic cleanup.

        Yields:
            AsyncSession: Database session for transaction operations

        Raises:
            Exception: Any exception during session usage triggers rollback
        """
        if self.async_session_local is None:
            self.init_async_session_maker()
        async with self.async_session_local() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


async def get_db_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Args:
        request: FastAPI request object containing database instance

    Yields:
        AsyncSession: Database session for request lifecycle
    """
    db: Database = request.state.db
    async with db.get_db_session() as session:
        yield session
