from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.base_repository import BaseDBRepository
from src.db.database import get_db_session

__all__ = (
    "UserRoleRepository",
    "get_user_role_repo",
)

from src.db.models import UserRoleEntity
from src.users.exceptions import UserRoleNotFound


class UserRoleRepository(BaseDBRepository):
    """Repository for user role operations."""

    async def get_id_by_name(self, role_name: str) -> int:
        user_role = await self._session.scalar(
            select(UserRoleEntity)
            .where(UserRoleEntity.name == role_name),
        )
        if user_role is None:
            raise UserRoleNotFound(f"User role '{role_name}' not found")
        return user_role.id


def get_user_role_repo(
    session: AsyncSession = Depends(get_db_session),
) -> UserRoleRepository:
    """
    Dependency injection function to get UserRoleRepository instance.

    Args:
        session: Database session injected by FastAPI

    Returns:
        UserRoleRepository instance configured with database session
    """
    return UserRoleRepository(session)
