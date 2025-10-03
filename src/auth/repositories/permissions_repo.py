from typing import Any

from fastapi import Depends
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import PermissionNotFound
from src.core.base_repository import BaseDBRepository
from src.db.database import get_db_session
from src.db.models import (
    PermissionEntity,
    ResourceTypeEntity,
    RolePermissionEntity,
    UserEntity,
    UserPermissionEntity,
    UserRoleEntity,
)


def _permission_dict_from_result(result: Result[Any]) -> dict[str, list[str]]:
    permissions = {}
    for resource_type, action in result.all():
        if resource_type not in permissions:
            permissions[resource_type] = []
        permissions[resource_type].append(action)

    return permissions


def _apply_user_permissions(
    role_permissions: dict[str, list[str]],
    user_permissions: Result[tuple[str, str, bool]],
) -> dict[str, list[str]]:
    final_permissions = role_permissions.copy()

    for resource_type, action, granted in user_permissions:
        if resource_type not in final_permissions:
            final_permissions[resource_type] = []
        if granted:
            if action not in final_permissions[resource_type]:
                final_permissions[resource_type].append(action)
        elif action in final_permissions[resource_type]:
            final_permissions[resource_type].remove(action)
    return final_permissions


class PermissionRepository(BaseDBRepository):
    async def get_all_user_permissions(self, user_id: int):
        role_perm_stmt = (
            select(ResourceTypeEntity.name, PermissionEntity.action)
            .select_from(UserEntity)
            .join(UserRoleEntity, UserRoleEntity.id == UserEntity.role_id)
            .join(RolePermissionEntity, RolePermissionEntity.role_id == UserRoleEntity.id)
            .join(PermissionEntity, PermissionEntity.id == RolePermissionEntity.permission_id)
            .join(ResourceTypeEntity, ResourceTypeEntity.id == PermissionEntity.resource_type_id)
            .where(UserEntity.id == user_id)
        )
        role_perm_result = await self._session.execute(role_perm_stmt)
        user_perm_stmt = (
            select(
                ResourceTypeEntity.name.label("resource_type"),
                PermissionEntity.action.label("action"),
                UserPermissionEntity.granted.label("granted"),
            )
            .select_from(UserPermissionEntity)
            .join(PermissionEntity, PermissionEntity.id == UserPermissionEntity.permission_id)
            .join(ResourceTypeEntity, ResourceTypeEntity.id == PermissionEntity.resource_type_id)
            .where(UserPermissionEntity.user_id == user_id)
        )
        user_permissions_result = await self._session.execute(user_perm_stmt)
        role_permissions = _permission_dict_from_result(role_perm_result)
        return _apply_user_permissions(role_permissions, user_permissions_result)

    async def set_user_permission(
        self,
        user_id: int,
        permission_name: str,
        granted: bool,
        granted_by: int,
    ):
        permission = await self._session.scalar(
            select(PermissionEntity).where(PermissionEntity.name == permission_name),
        )
        if permission is None:
            raise PermissionNotFound(f"Permission {permission_name} not found")
        user_permission: UserPermissionEntity | None = await self._session.scalar(
            select(UserPermissionEntity).where(UserPermissionEntity.permission_id == permission.id),
        )
        if user_permission is not None:
            user_permission.granted = granted
            user_permission.granted_by = granted_by
        else:
            self._session.add(
                UserPermissionEntity(
                    user_id=user_id,
                    permission_id=permission.id,
                    granted=granted,
                    granted_by=granted_by,
                ),
            )
        await self._session.commit()


def get_permissions_repo(
    session: AsyncSession = Depends(get_db_session),
) -> PermissionRepository:
    return PermissionRepository(session)
