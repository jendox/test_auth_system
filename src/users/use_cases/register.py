from fastapi import Depends

from src.core.security import PasswordHasher, get_argon2_password_hasher
from src.routes.shemas.user import RegisterRequest
from src.users.repositories import UserRepository, get_user_repo

__all__ = (
    "RegisterUserUseCase",
    "get_register_user_use_case",
)

from src.users.repositories.user_role import UserRoleRepository, get_user_role_repo


class RegisterUserUseCase:
    """
    Use case for user registration.

    Handles the business logic for creating new user accounts
    with secure password hashing.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        user_role_repo: UserRoleRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._user_role_repo = user_role_repo
        self._pass_hasher = password_hasher

    async def __call__(self, user_data: RegisterRequest) -> int:
        hashed_password = self._pass_hasher.hash_password(user_data.new_password)
        role_id = await self._user_role_repo.get_id_by_name(user_data.user_role)
        user_id = await self._user_repo.create(user_data.email, hashed_password, role_id, user_data.name)
        return user_id


def get_register_user_use_case(
    user_repo: UserRepository = Depends(get_user_repo),
    user_role_repo: UserRoleRepository = Depends(get_user_role_repo),
    password_hasher: PasswordHasher = Depends(get_argon2_password_hasher),
) -> RegisterUserUseCase:
    """
    Dependency injection function to get RegisterUserUseCase instance.

    Args:
        user_repo: User repository instance injected by FastAPI
        user_role_repo: User role repository instance injected by FastAPI
        password_hasher: Password hasher instance injected by FastAPI

    Returns:
        RegisterUserUseCase instance configured with dependencies
    """
    return RegisterUserUseCase(user_repo, user_role_repo, password_hasher)
