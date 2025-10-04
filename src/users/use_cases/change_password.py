from fastapi import Depends

from src.auth.exceptions import AuthenticationError
from src.core import security
from src.users.repositories import UserRepository, get_user_repo

__all__ = (
    "ChangePasswordUseCase",
    "get_change_password_use_case",
)


class ChangePasswordUseCase:
    """
    Use case for changing user password.

    Handles business logic for password change with current password verification
    and secure password hashing.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: security.PasswordHasher,
    ):
        self._user_repo = user_repo
        self._pass_hasher = password_hasher

    async def _verify_current_password(self, user_id: int, current_password: str) -> None:
        user = await self._user_repo.get_by_id(user_id)
        try:
            self._pass_hasher.verify_password(current_password, user.hashed_password)
        except security.InvalidCredentials:
            raise AuthenticationError()

    async def __call__(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> None:
        await self._verify_current_password(user_id, current_password)
        hashed_password = self._pass_hasher.hash_password(new_password)
        await self._user_repo.update_password(user_id, hashed_password)


def get_change_password_use_case(
    user_repo: UserRepository = Depends(get_user_repo),
    password_hasher: security.PasswordHasher = Depends(security.get_argon2_password_hasher),
) -> ChangePasswordUseCase:
    """
    Dependency injection function to get ChangePasswordUseCase instance.

    Args:
        user_repo: User repository instance injected by FastAPI
        password_hasher: Password hasher instance injected by FastAPI

    Returns:
        ChangePasswordUseCase instance configured with dependencies
    """
    return ChangePasswordUseCase(user_repo, password_hasher)
