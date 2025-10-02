from fastapi import Depends

from src.routes.shemas import ConfirmEmailRequest
from src.token_manager import TokenManager, get_token_manager
from src.users.repository import UserRepository, get_user_repo


class ConfirmEmailUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        token_manager: TokenManager,
    ):
        self._user_repo = user_repo
        self._token_manager = token_manager

    async def __call__(self, user_data: ConfirmEmailRequest) -> None:
        user_id = self._token_manager.verify_email_confirmation_token(user_data.token)
        await self._user_repo.mark_as_active(user_id)


def get_confirm_email_use_case(
    user_repo: UserRepository = Depends(get_user_repo),
    token_manager: TokenManager = Depends(get_token_manager),
) -> ConfirmEmailUseCase:
    return ConfirmEmailUseCase(user_repo, token_manager)
