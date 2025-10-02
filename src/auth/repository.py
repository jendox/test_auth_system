import uuid
from uuid import UUID

from fastapi import Depends
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from src.core.utils import get_iat_exp_timestamps
from src.db.database import get_db_session
from src.db.models import RefreshTokenEntity, UserEntity, UserSessionEntity


class TokenNotFound(Exception): ...


class UserSessionNotFound(Exception): ...


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        session_id: UUID,
        token_hash: str,
        expires_at: int,
    ) -> RefreshTokenEntity:
        token = RefreshTokenEntity(
            session_id=session_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(token)
        await self._session.commit()
        return token

    async def get(self, token_hash: str) -> RefreshTokenEntity:
        now, __ = get_iat_exp_timestamps()
        stmt = (
            select(RefreshTokenEntity)
            .where(RefreshTokenEntity.token_hash == token_hash)
        )
        token = await self._session.scalar(stmt)
        if token is None:
            raise TokenNotFound("Token not found")
        return token

    async def get_active_for_refresh(self, token_hash: str) -> RefreshTokenEntity:
        """
        Retrieve a refresh token with active session and user for token refresh operation.

        This method performs comprehensive validation to ensure both the refresh token
        and its associated user session are valid and active. It is specifically designed
        for use in the access token refresh flow (/refresh endpoint).

        Args:
            token_hash: The hashed refresh token string to lookup

        Returns:
            RefreshTokenEntity: The refresh token entity with loaded session and user relationships

        Raises:
            TokenNotFound: If no active token/session is found or validation fails

        Validation includes:
            - Refresh token exists and matches the hash
            - Refresh token is not revoked
            - Refresh token has not expired
            - Associated user session is not revoked
            - User session has not expired
            - User relationship is eagerly loaded for immediate access
        """
        now, __ = get_iat_exp_timestamps()
        stmt = (
            select(RefreshTokenEntity)
            .options(
                selectinload(RefreshTokenEntity.session)
                .selectinload(UserSessionEntity.user)
                .selectinload(UserEntity.role),
            )
            .join(RefreshTokenEntity.session)
            .where(
                and_(
                    RefreshTokenEntity.token_hash == token_hash,
                    RefreshTokenEntity.is_revoked.is_(False),
                    RefreshTokenEntity.expires_at > now,
                    UserSessionEntity.is_revoked.is_(False),
                    UserSessionEntity.expires_at > now,
                ),
            )
        )
        token = await self._session.scalar(stmt)
        if token is None:
            raise TokenNotFound("Token not found or invalid")
        return token

    async def revoke(self, token_hash: str) -> bool:
        """
        Revoke an active refresh token using UPDATE statement.

        Args:
            token_hash: The hashed refresh token to revoke

        Returns:
            bool: True if token was found and revoked, False otherwise
        """
        now, __ = get_iat_exp_timestamps()
        stmt = (
            update(RefreshTokenEntity)
            .where(
                and_(
                    RefreshTokenEntity.token_hash == token_hash,
                    RefreshTokenEntity.is_revoked.is_(False),
                    RefreshTokenEntity.expires_at > now,
                ),
            )
            .values(is_revoked=True)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0


def get_refresh_token_repo(
    session: AsyncSession = Depends(get_db_session),
) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


class UserSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, expires_at: int) -> UUID:
        user_session = UserSessionEntity(
            id=uuid.uuid4(),
            user_id=user_id,
            expires_at=expires_at,
        )
        self.session.add(user_session)
        await self.session.commit()
        return user_session.id

    async def get_active(self, session_id: UUID) -> UserSessionEntity:
        now, __ = get_iat_exp_timestamps()
        stmt = (
            select(UserSessionEntity)
            .options(
                joinedload(UserSessionEntity.user)
                .options(
                    selectinload(
                        UserEntity.role,
                    ),
                    selectinload(
                        UserEntity.user_permissions,
                    ),
                ),
            )
            .where(
                and_(
                    UserSessionEntity.id == session_id,
                    UserSessionEntity.is_revoked.is_(False),
                    UserSessionEntity.expires_at > now,
                ),
            )
        )
        session = await self.session.scalar(stmt)
        if session is None:
            raise UserSessionNotFound("User session not found")
        return session

    async def get_active_with_user(self, session_id: UUID) -> UserSessionEntity:
        now, __ = get_iat_exp_timestamps()
        stmt = (
            select(UserSessionEntity)
            .options(joinedload(UserSessionEntity.user))
            .where(
                and_(
                    UserSessionEntity.id == session_id,
                    UserSessionEntity.is_revoked.is_(False),
                    UserSessionEntity.expires_at > now,
                ),
            )
        )
        session = await self.session.scalar(stmt)
        if session is None:
            raise UserSessionNotFound("User session not found")
        return session

    async def revoke(self, session_id: UUID) -> bool:
        stmt = (
            update(UserSessionEntity)
            .where(UserSessionEntity.id == session_id)
            .values(is_revoked=True)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0


def get_user_session_repo(
    session: AsyncSession = Depends(get_db_session),
) -> UserSessionRepository:
    return UserSessionRepository(session)
