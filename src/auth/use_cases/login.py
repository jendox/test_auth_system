from datetime import timedelta
from uuid import UUID

from fastapi import Depends
from pydantic import EmailStr

from src.auth.exceptions import AuthenticationError
from src.auth.repositories.refresh_token_repo import RefreshTokenRepository, get_refresh_token_repo
from src.auth.repositories.user_session_repo import UserSessionRepository, get_user_session_repo
from src.core import security
from src.core.utils import get_iat_exp_timestamps, get_sha256hash
from src.routes.shemas.auth import LoginRequest
from src.token_manager import TokenManager, TokenPair, get_token_manager
from src.users.repository import UserNotFound, UserRepository, get_user_repo

REMEMBER_ME_REFRESH_TOKEN_TTL = 14  # 2 week session


class LoginUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        user_session_repo: UserSessionRepository,
        token_repo: RefreshTokenRepository,
        token_manager: TokenManager,
        password_hasher: security.PasswordHasher,
    ):
        self._user_repo = user_repo
        self._user_session_repo = user_session_repo
        self._token_repo = token_repo
        self._token_manager = token_manager
        self._pass_hasher = password_hasher

    async def _authenticate(
        self,
        email: EmailStr,
        password: str,
    ) -> tuple[int, str]:
        try:
            user = await self._user_repo.get_by_email(email)
            if not user.is_active:
                raise AuthenticationError("User account is disabled")
            self._pass_hasher.verify_password(password, user.hashed_password)
            return user.id, user.role.name
        except UserNotFound:
            raise AuthenticationError("User not found")
        except security.InvalidCredentials:
            raise AuthenticationError("Invalid password")

    def _get_refresh_token_ttl(self, remember_me: bool) -> int:
        return REMEMBER_ME_REFRESH_TOKEN_TTL if remember_me else self._token_manager.refresh_token_ttl

    async def _create_session(self, user_id: int, session_ttl: int):
        __, exp = get_iat_exp_timestamps(timedelta(days=session_ttl))
        return await self._user_session_repo.create(user_id, exp)

    async def _save_refresh_token(self, session_id: UUID, token: str, exp: int):
        token_hash = get_sha256hash(token)
        await self._token_repo.create(
            session_id=session_id,
            token_hash=token_hash,
            expires_at=exp,
        )

    async def __call__(
        self,
        credentials: LoginRequest,
    ) -> TokenPair:
        user_id, user_role = await self._authenticate(credentials.email, credentials.password)
        refresh_token_ttl = self._get_refresh_token_ttl(credentials.remember_me)
        session_id = await self._create_session(user_id, refresh_token_ttl)
        token_pair = self._token_manager.get_token_pair(user_id, user_role, session_id, refresh_token_ttl)
        await self._save_refresh_token(
            session_id, token_pair.refresh_token.token, token_pair.refresh_token.expires_at,
        )
        return token_pair


def get_login_use_case(
    user_repo: UserRepository = Depends(get_user_repo),
    user_session_repo: UserSessionRepository = Depends(get_user_session_repo),
    token_repo: RefreshTokenRepository = Depends(get_refresh_token_repo),
    token_manager: TokenManager = Depends(get_token_manager),
    password_hasher: security.PasswordHasher = Depends(security.get_password_hasher),
) -> LoginUseCase:
    return LoginUseCase(user_repo, user_session_repo, token_repo, token_manager, password_hasher)
