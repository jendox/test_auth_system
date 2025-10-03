from fastapi import Depends

from src.auth.models import UserPermissions
from src.auth.repositories.permissions_repo import PermissionRepository, get_permissions_repo
from src.users.repository import UserRepository, get_user_repo


class ManageUserPermissionsUseCase:
    def __init__(
        self,
        permission_repo: PermissionRepository,
        user_repo: UserRepository,
    ):
        self._permissions_repo = permission_repo
        self._user_repo = user_repo

    async def _check_user_exists(self, user_id: int):
        await self._user_repo.get_by_id(user_id)

    async def read_user_permissions(self, user_id: int):
        await self._check_user_exists(user_id)
        permissions = await self._permissions_repo.get_all_user_permissions(user_id)
        user_permissions = UserPermissions.from_dict(permissions)
        return user_permissions.permissions

    async def set_user_permission(
        self,
        user_id: int,
        permission_name: str,
        granted: bool,
        granted_by: int,
    ):
        await self._check_user_exists(user_id)
        await self._permissions_repo.set_user_permission(
            user_id, permission_name, granted, granted_by,
        )


def manage_user_permissions_use_case(
    permission_repo: PermissionRepository = Depends(get_permissions_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> ManageUserPermissionsUseCase:
    return ManageUserPermissionsUseCase(permission_repo, user_repo)
