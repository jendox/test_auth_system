from fastapi import Depends

from src.auth.models import Permission, UserPermissions
from src.auth.repositories import PermissionRepository, get_permissions_repo
from src.users.repositories import UserRepository, get_user_repo

__all__ = (
    "ManageUserPermissionsUseCase",
    "manage_user_permissions_use_case",
)


class ManageUserPermissionsUseCase:
    """
    Use case for managing user permissions.

    Handles business logic for reading and modifying user permissions
    with proper validation and existence checks.
    """

    def __init__(
        self,
        permission_repo: PermissionRepository,
        user_repo: UserRepository,
    ):
        self._permissions_repo = permission_repo
        self._user_repo = user_repo

    async def _check_user_exists(self, user_id: int):
        await self._user_repo.get_by_id(user_id)

    async def read_user_permissions(self, user_id: int) -> list[Permission]:
        """
        Retrieve all permissions for a specific user.

        Combines role-based permissions and individual user permissions
        into a comprehensive permissions set.

        Args:
            user_id: ID of the user to read permissions for

        Returns:
            List of permissions assigned to the user

        Raises:
            UserNotFound: If the user doesn't exist
        """
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
    ) -> None:
        """
        Grant or revoke a specific permission for a user.

        Allows administrators to override role-based permissions
        with individual user permissions.

        Args:
            user_id: ID of the user to modify permissions for
            permission_name: Name of the permission to set
            granted: Boolean indicating whether to grant or revoke the permission
            granted_by: ID of the user performing the permission change

        Raises:
            UserNotFound: If the target user doesn't exist
            PermissionNotFound: If the specified permission doesn't exist
        """
        await self._check_user_exists(user_id)
        await self._permissions_repo.set_user_permission(
            user_id, permission_name, granted, granted_by,
        )


def manage_user_permissions_use_case(
    permission_repo: PermissionRepository = Depends(get_permissions_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> ManageUserPermissionsUseCase:
    """
    Dependency injection function to get ManageUserPermissionsUseCase instance.

    Args:
        permission_repo: Permission repository instance injected by FastAPI
        user_repo: User repository instance injected by FastAPI

    Returns:
        ManageUserPermissionsUseCase instance configured with dependencies
    """
    return ManageUserPermissionsUseCase(permission_repo, user_repo)
