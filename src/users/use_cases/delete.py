from fastapi import Depends

from src.auth.exceptions import InsufficientPermissions
from src.auth.models import PermissionAction, UserPermissions
from src.users.repository import UserRepository, get_user_repo


class DeleteUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def __call__(
        self,
        user_id: int,
        current_user_id: int,
        permissions: UserPermissions,
    ) -> str:
        if user_id == current_user_id:
            await self.user_repo.mark_as_inactive(user_id)
            return "Your account has been deleted."
        if permissions.has_permission("user", PermissionAction.DELETE):
            await self.user_repo.mark_as_inactive(user_id)
            return "User deleted successfully."
        raise InsufficientPermissions()


def get_delete_user_use_case(
    user_repo: UserRepository = Depends(get_user_repo),
) -> DeleteUserUseCase:
    return DeleteUserUseCase(user_repo)
