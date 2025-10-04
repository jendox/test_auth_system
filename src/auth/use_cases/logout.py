from uuid import UUID

from fastapi import Depends

from src.auth.repositories import UserSessionRepository, get_user_session_repo

__all__ = (
    "LogoutUseCase",
    "get_logout_use_case",
)


class LogoutUseCase:
    """
    Use case for user logout process.

    Handles the business logic for terminating user sessions
    by revoking the session identifier.
    """

    def __init__(
        self,
        user_session_repo: UserSessionRepository,
    ):
        self._user_session_repo = user_session_repo

    async def __call__(self, session_id: UUID) -> None:
        await self._user_session_repo.revoke(session_id)


def get_logout_use_case(
    user_session_repo: UserSessionRepository = Depends(get_user_session_repo),
) -> LogoutUseCase:
    """
    Dependency injection function to get LogoutUseCase instance.

    Args:
        user_session_repo: User session repository instance injected by FastAPI

    Returns:
        LogoutUseCase instance configured with session repository
    """
    return LogoutUseCase(user_session_repo)
