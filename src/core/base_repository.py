from sqlalchemy.ext.asyncio import AsyncSession


class BaseDBRepository:  # noqa: B903
    def __init__(self, session: AsyncSession):
        self._session = session
