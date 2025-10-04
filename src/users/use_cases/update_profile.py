from fastapi import Depends

from src.users.repositories import UserRepository, get_user_repo

__all__ = (
    "UpdateProfileUseCase",
    "get_update_profile_use_case",
)


class UpdateProfileUseCase:
    """
    Use case for updating user profile information.

    Handles business logic for modifying user profile data
    with proper validation and authorization.
    """

    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def __call__(self, user_id: int, user_name: str):
        await self._user_repo.update_name(user_id, user_name)


def get_update_profile_use_case(
    user_repo: UserRepository = Depends(get_user_repo),
) -> UpdateProfileUseCase:
    """
    Dependency injection function to get UpdateProfileUseCase instance.

    Args:
        user_repo: User repository instance injected by FastAPI

    Returns:
        UpdateProfileUseCase instance configured with user repository
    """
    return UpdateProfileUseCase(user_repo)
