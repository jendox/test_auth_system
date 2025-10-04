from fastapi import Depends
from pydantic import EmailStr

from src.token_manager import TokenManager, get_token_manager

__all__ = (
    "Notifier",
    "get_notifier",
)


class Notifier:
    """Notification service for sending various types of notifications.

    Currently implements email confirmation functionality as a stub
    for the test assignment.

    Attributes:
        token_manager: Token manager for generating confirmation tokens
    """

    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager

    async def send_email_confirmation(self, user_id: int, email: EmailStr) -> str:
        """
        Send email confirmation message to user (stub implementation).

        In a real implementation, this would send an actual email with
        confirmation link containing the token.

        Args:
            user_id: ID of the user to send confirmation to
            email: Email address of the user

        Returns:
            Email confirmation token that would be included in confirmation link
        """
        token = self.token_manager.create_email_confirmation_token(user_id)
        # send confirmation email
        return token


def get_notifier(
    token_manager: TokenManager = Depends(get_token_manager),
) -> Notifier:
    """
    Dependency injection function to get Notifier instance.

    Args:
        token_manager: Token manager instance injected by FastAPI

    Returns:
        Notifier instance configured with token manager
    """
    return Notifier(token_manager)
