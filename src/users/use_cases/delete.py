import uuid

from fastapi import Depends

from src.auth.repositories import UserSessionRepository, get_user_session_repo
from src.users.repositories import UserRepository, get_user_repo

__all__ = (
    "DeleteMeUseCase",
    "get_delete_me_use_case",
)


class DeleteMeUseCase:
    """
    Use case for deleting current user accounts.

    Handles business logic for user deletion with proper authorization checks.
    """
    def __init__(self, user_repo: UserRepository, session_repo: UserSessionRepository):
        self._user_repo = user_repo
        self._session_repo = session_repo

    async def __call__(self, user_id: int, session_id: uuid.UUID):
        await self._user_repo.mark_as_inactive(user_id)
        await self._session_repo.revoke(session_id)


def get_delete_me_use_case(
    user_repo: UserRepository = Depends(get_user_repo),
    user_session_repo: UserSessionRepository = Depends(get_user_session_repo),
) -> DeleteMeUseCase:
    """
    Dependency injection function to get DeleteMeUserCase instance.

    Args:
        user_repo: User repository instance injected by FastAPI
        user_session_repo: User session repository instance injected by FastAPI

    Returns:
        DeleteMeUserCase instance configured with user repository
    """
    return DeleteMeUseCase(user_repo, user_session_repo)
