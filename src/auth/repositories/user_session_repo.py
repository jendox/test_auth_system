import uuid

from fastapi import Depends
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import UserSessionNotFound
from src.core.base_repository import BaseDBRepository
from src.core.utils import get_iat_exp_timestamps
from src.db.database import get_db_session
from src.db.models import UserSessionEntity

__all__ = (
    "UserSessionRepository",
    "get_user_session_repo",
)


class UserSessionRepository(BaseDBRepository):
    """
    Repository for user session database operations.

    Handles creation, retrieval, and management of user authentication sessions
    with proper validation and revocation capabilities.
    """

    async def create(self, user_id: int, expires_at: int) -> uuid.UUID:
        """
        Create a new user session.

        Args:
            user_id: ID of the user to create session for
            expires_at: Expiration timestamp for the session

        Returns:
            UUID: Unique identifier of the created session
        """
        user_session = UserSessionEntity(
            id=uuid.uuid4(),
            user_id=user_id,
            expires_at=expires_at,
        )
        self._session.add(user_session)
        await self._session.commit()
        return user_session.id

    async def get_active(self, session_id: uuid.UUID) -> UserSessionEntity:
        """
        Retrieve an active user session by its ID.

        Validates that the session exists, is not revoked, and has not expired.

        Args:
            session_id: UUID of the session to retrieve

        Returns:
            UserSessionEntity: The active session entity

        Raises:
            UserSessionNotFound: If session doesn't exist or is invalid
        """
        now, __ = get_iat_exp_timestamps()
        stmt = (
            select(UserSessionEntity)
            .where(
                and_(
                    UserSessionEntity.id == session_id,
                    UserSessionEntity.is_revoked.is_(False),
                    UserSessionEntity.expires_at > now,
                ),
            )
        )
        session = await self._session.scalar(stmt)
        if session is None:
            raise UserSessionNotFound("User session not found")
        return session

    async def revoke(self, session_id: uuid.UUID) -> bool:
        """
        Revoke a user session by marking it as revoked.

        Args:
            session_id: UUID of the session to revoke

        Returns:
            bool: True if session was found and revoked, False otherwise
        """
        stmt = (
            update(UserSessionEntity)
            .where(UserSessionEntity.id == session_id)
            .values(is_revoked=True)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0


def get_user_session_repo(
    session: AsyncSession = Depends(get_db_session),
) -> UserSessionRepository:
    """
    Dependency injection function to get UserSessionRepository instance.

    Args:
        session: Database session injected by FastAPI

    Returns:
        UserSessionRepository instance configured with database session
    """
    return UserSessionRepository(session)
