from fastapi import Depends
from pydantic import EmailStr

from src.token_manager import TokenManager, get_token_manager


class Notifier:
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager

    async def send_email_confirmation(self, user_id: int, email: EmailStr) -> str:
        token = self.token_manager.create_email_confirmation_token(user_id)
        # TODO: make full email confirmation link
        print(f"Please follow the link: {token}")
        return token


def get_notifier(
    token_manager: TokenManager = Depends(get_token_manager),
) -> Notifier:
    return Notifier(token_manager)
