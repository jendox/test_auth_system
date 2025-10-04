import sqlalchemy.exc
from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.base_repository import BaseDBRepository
from src.db.database import get_db_session
from src.db.models import UserEntity
from src.users.exceptions import AdminDeletion, UserAlreadyActivated, UserAlreadyExists, UserNotFound

__all__ = (
    "UserRepository",
    "get_user_repo",
)


class UserRepository(BaseDBRepository):
    """
    Repository for user data operations.

    Provides methods for creating, retrieving, and managing user accounts
    in the database.
    """

    async def create(
        self,
        email: EmailStr,
        hashed_password: str,
        role_id: int,
        name: str | None,
    ) -> int:
        """
        Create a new user account.

        Args:
            email: User's email address (must be unique)
            hashed_password: Securely hashed password
            role_id: User's role unique identifier
            name: User's full name (optional)


        Returns:
            ID of the newly created user

        Raises:
            UserAlreadyExists: If a user with the email already exists
        """
        user = UserEntity(
            email=email,
            hashed_password=hashed_password,
            name=name,
            role_id=role_id,
        )
        try:
            self._session.add(user)
            await self._session.commit()
            return user.id
        except sqlalchemy.exc.IntegrityError:
            raise UserAlreadyExists(f"User with email '{email}' already exists.")

    async def get_by_email(self, email: EmailStr) -> UserEntity:
        """
        Retrieve a user by email address.

        Args:
            email: Email address to search for

        Returns:
            UserEntity instance with role relationship loaded

        Raises:
            UserNotFound: If no user exists with the specified email
        """
        stmt = (
            select(UserEntity)
            .options(selectinload(UserEntity.role))
            .where(UserEntity.email == str(email))
        )
        user = await self._session.scalar(stmt)
        if user is None:
            raise UserNotFound(f"User with email '{email}' does not exist")
        return user

    async def get_by_id(self, user_id: int) -> UserEntity:
        """
        Retrieve a user by their unique identifier.

        Args:
            user_id: User ID to search for

        Returns:
            UserEntity instance with role relationship loaded

        Raises:
            UserNotFound: If no user exists with the specified ID
        """
        stmt = (
            select(UserEntity)
            .options(selectinload(UserEntity.role))
            .where(UserEntity.id == user_id)
        )
        user = await self._session.scalar(stmt)
        if user is None:
            raise UserNotFound(f"User with id '{user_id}' does not exist")
        return user

    async def mark_as_active(self, user_id: int) -> None:
        """
        Activate a user account.

        Args:
            user_id: ID of the user to activate

        Raises:
            UserNotFound: If user doesn't exist
            UserAlreadyActivated: If user is already active
        """
        user = await self.get_by_id(user_id)
        if user.is_active:
            raise UserAlreadyActivated(f"User with id '{user_id}' already activated")
        user.is_active = True
        await self._session.commit()

    async def mark_as_inactive(self, user_id: int) -> None:
        """
        Deactivate a user account (soft delete).

        Args:
            user_id: ID of the user to deactivate

        Raises:
            UserNotFound: If user doesn't exist
            AdminDeletion: If attempting to deactivate an admin user
        """
        user = await self.get_by_id(user_id)
        if user.role.name == "admin":
            raise AdminDeletion()
        user.is_active = False
        await self._session.commit()

    async def update_name(self, user_id: int, name: str) -> bool:
        """
        Update username information.

        Args:
            user_id: ID of the user to update
            name: New name for the user

        Returns:
            bool: True if name was updated, False otherwise
        """
        stmt = (
            update(UserEntity)
            .where(UserEntity.id == user_id)
            .values(name=name)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0

    async def update_password(self, user_id: int, hashed_password: str) -> bool:
        """
        Update hashed password.

        Args:
            user_id: ID of the user to update
            hashed_password: New password's hash

        Returns:
            bool: True if hashed_password was updated, False otherwise
        """
        stmt = (
            update(UserEntity)
            .where(UserEntity.id == user_id)
            .values(hashed_password=hashed_password)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount > 0


def get_user_repo(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    """
    Dependency injection function to get UserRepository instance.

    Args:
        session: Database session injected by FastAPI

    Returns:
        UserRepository instance configured with database session
    """
    return UserRepository(session)
