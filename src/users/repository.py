import sqlalchemy.exc
from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.database import get_db_session
from src.db.models import UserEntity, UserPermissionEntity, UserRoleEntity


class UserAlreadyExists(Exception): ...


class UserNotFound(Exception): ...


class UserAlreadyActivated(Exception): ...


class AdminDeletion(Exception): ...


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        email: EmailStr,
        hashed_password: str,
        name: str | None,
    ) -> int:
        user = UserEntity(
            email=email,
            hashed_password=hashed_password,
            name=name,
        )
        try:
            self._session.add(user)
            await self._session.commit()
            return user.id
        except sqlalchemy.exc.IntegrityError:
            raise UserAlreadyExists(f"User with email '{email}' already exists.")

    async def get_by_email(self, email: EmailStr) -> UserEntity:
        stmt = (
            select(UserEntity)
            .options(
                selectinload(UserEntity.role).selectinload(UserRoleEntity.role_permissions),
                selectinload(UserEntity.user_permissions).selectinload(UserPermissionEntity.permission),
            )
            .where(UserEntity.email == str(email))
        )
        user = await self._session.scalar(stmt)
        if user is None:
            raise UserNotFound(f"User with email '{email}' does not exist")
        return user

    async def get_by_id(self, user_id: int) -> UserEntity:
        stmt = (
            select(UserEntity)
            .options(
                selectinload(UserEntity.role).selectinload(UserRoleEntity.role_permissions),
                selectinload(UserEntity.user_permissions).selectinload(UserPermissionEntity.permission),
            )
            .where(UserEntity.id == user_id)
        )
        user = await self._session.scalar(stmt)
        if user is None:
            raise UserNotFound(f"User with id '{user_id}' does not exist")
        return user

    async def mark_as_active(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        if user.is_active:
            raise UserAlreadyActivated(f"User with id '{user_id}' already activated")
        user.is_active = True
        await self._session.commit()

    async def mark_as_inactive(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        if user.role.name == "admin":
            raise AdminDeletion("Admin deletion forbidden")
        user.is_active = False
        await self._session.commit()


def get_user_repo(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session)
