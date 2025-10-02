from uuid import UUID

from fastapi import Depends

from src.auth.repository import (
    UserSessionRepository,
    get_user_session_repo,
)


class LogoutUseCase:
    def __init__(
        self,
        user_session_repo: UserSessionRepository,
    ):
        self._user_session_repo = user_session_repo

    async def __call__(self, session_id: UUID):
        await self._user_session_repo.revoke(session_id)


def get_logout_use_case(
    user_session_repo: UserSessionRepository = Depends(get_user_session_repo),
) -> LogoutUseCase:
    return LogoutUseCase(user_session_repo)
