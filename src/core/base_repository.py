from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ("BaseDBRepository",)


class BaseDBRepository:  # noqa: B903
    """Base class for all database repositories.

    Attributes:
        _session: SQLAlchemy async session for database operations
    """

    def __init__(self, session: AsyncSession):
        self._session = session
