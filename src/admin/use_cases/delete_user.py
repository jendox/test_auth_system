from fastapi import Depends

from src.auth.exceptions import InsufficientPermissions
from src.auth.models import PermissionAction, UserPermissions
from src.users.repositories import UserRepository, get_user_repo

__all__ = (
    "DeleteUserUseCase",
    "get_delete_user_use_case",
)


class DeleteUserUseCase:
    """
    Use case for deleting user accounts.

    Handles business logic for user deletion with proper authorization checks.
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def __call__(
        self,
        user_id: int,
        permissions: UserPermissions,
    ) -> None:
        if permissions.has_permission("user", PermissionAction.DELETE):
            return await self.user_repo.mark_as_inactive(user_id)
        raise InsufficientPermissions()


def get_delete_user_use_case(
    user_repo: UserRepository = Depends(get_user_repo),
) -> DeleteUserUseCase:
    """
    Dependency injection function to get DeleteUserUseCase instance.

    Args:
        user_repo: User repository instance injected by FastAPI

    Returns:
        DeleteUserUseCase instance configured with user repository
    """
    return DeleteUserUseCase(user_repo)
