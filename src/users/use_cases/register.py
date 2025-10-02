from fastapi import Depends

from src.core.security import PasswordHasher, get_password_hasher
from src.routes.shemas.user import RegisterRequest
from src.users.repository import UserRepository, get_user_repo


class RegisterUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._pass_hasher = password_hasher

    async def __call__(self, user_data: RegisterRequest) -> int:
        hashed_password = self._pass_hasher.hash_password(user_data.new_password)
        user_id = await self._user_repo.create(user_data.email, hashed_password, user_data.name)
        return user_id


def get_register_user_use_case(
    user_repo: UserRepository = Depends(get_user_repo),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_repo, password_hasher)
