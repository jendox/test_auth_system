from uuid import UUID

from fastapi import Depends

from src.auth.repositories.refresh_token_repo import RefreshTokenRepository, get_refresh_token_repo
from src.core.utils import get_sha256hash
from src.token_manager import TokenManager, TokenPair, get_token_manager


class RefreshUseCase:
    def __init__(
        self,
        token_repo: RefreshTokenRepository,
        token_manager: TokenManager,
    ):
        self._token_repo = token_repo
        self._token_manager = token_manager

    async def _save_refresh_token(self, session_id: UUID, token: str, exp: int):
        token_hash = get_sha256hash(token)
        await self._token_repo.create(
            session_id=session_id,
            token_hash=token_hash,
            expires_at=exp,
        )

    async def __call__(self, token: str) -> TokenPair:
        token_hash = get_sha256hash(token)
        refresh_token = await self._token_repo.get_active_for_refresh(
            token_hash=get_sha256hash(token),
        )
        user = refresh_token.session.user
        token_pair = self._token_manager.get_token_pair(
            user.id, user.role.name, refresh_token.session_id,
        )
        await self._save_refresh_token(
            refresh_token.session_id, token_pair.refresh_token.token, token_pair.refresh_token.expires_at,
        )
        await self._token_repo.revoke(token_hash)
        return token_pair


def get_refresh_use_case(
    token_repo: RefreshTokenRepository = Depends(get_refresh_token_repo),
    token_manager: TokenManager = Depends(get_token_manager),
) -> RefreshUseCase:
    return RefreshUseCase(token_repo, token_manager)
