from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status
from starlette.exceptions import HTTPException

from src.token_manager import TokenManager, TokenVerificationError, get_token_manager

from .exceptions import UserSessionNotFound
from .models import AuthenticatedUser, UserPermissions, UserSession
from .repositories.permissions_repo import PermissionRepository, get_permissions_repo
from .repositories.user_session_repo import UserSessionRepository, get_user_session_repo
from ..users.repository import UserRepository, get_user_repo


async def get_user_session(
    auth: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    token_manager: TokenManager = Depends(get_token_manager),
    session_repo: UserSessionRepository = Depends(get_user_session_repo),
) -> UserSession:
    try:
        payload = token_manager.verify_access_token(auth.credentials)
        session = await session_repo.get_active(UUID(payload.sid))
        return UserSession(
            id=session.id,
            is_revoked=session.is_revoked,
            expires_at=session.expires_at,
        )
    except (TokenVerificationError, UserSessionNotFound):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token or session expired.",
        )


async def get_user_permissions(
    auth: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    token_manager: TokenManager = Depends(get_token_manager),
    permission_repo: PermissionRepository = Depends(get_permissions_repo),
) -> UserPermissions:
    try:
        payload = token_manager.verify_access_token(auth.credentials)
        user_id = int(payload.sub)
        permissions = await permission_repo.get_all_user_permissions(user_id)
        return UserPermissions.from_dict(permissions)
    except TokenVerificationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    token_manager: TokenManager = Depends(get_token_manager),
    session_repo: UserSessionRepository = Depends(get_user_session_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> AuthenticatedUser:
    try:
        payload = token_manager.verify_access_token(auth.credentials)
        await session_repo.get_active(UUID(payload.sid))
        user = await user_repo.get_by_id(int(payload.sub))
        return AuthenticatedUser.from_entity(user)
    except (TokenVerificationError, UserSessionNotFound):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )
