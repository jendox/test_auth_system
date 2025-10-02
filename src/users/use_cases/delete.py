from fastapi import Depends

from src.users.repository import UserRepository, get_user_repo


class DeleteUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def __call__(self, user_id: int) -> int | None:
        await self.user_repo.mark_as_inactive(user_id)


def get_delete_user_use_case(
    user_repo: UserRepository = Depends(get_user_repo),
) -> DeleteUserUseCase:
    return DeleteUserUseCase(user_repo)
