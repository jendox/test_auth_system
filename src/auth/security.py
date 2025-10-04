import uuid
from typing import cast

from fastapi import Depends
from fastapi.openapi.models import HTTPBase as HTTPBaseModel
from fastapi.security import HTTPAuthorizationCredentials, http
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request

from src.token_manager import TokenManager, TokenVerificationError, get_token_manager
from src.users.repositories import UserRepository, get_user_repo
from .exceptions import UserSessionNotFound
from .models import AuthenticatedUser, UserPermissions, UserSession
from .repositories import PermissionRepository, UserSessionRepository, get_permissions_repo, get_user_session_repo

__all__ = (
    "HTTPBearer",
    "get_user_session",
    "get_user_permissions",
    "get_current_user",
)


class HTTPBearer(http.HTTPBase):
    """
    Custom HTTP Bearer authentication scheme.

    Extends FastAPI's HTTPBase to provide Bearer token authentication
    with proper error handling and WWW-Authenticate headers.
    """

    async def __call__(self, request: Request):
        credentials = await super().__call__(request)
        model = cast(HTTPBaseModel, self.model)
        if credentials is None or credentials.scheme.lower() != model.scheme:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials


bearer = HTTPBearer(scheme="bearer", auto_error=False)


async def get_user_session(
    auth: HTTPAuthorizationCredentials = Depends(bearer),
    token_manager: TokenManager = Depends(get_token_manager),
    session_repo: UserSessionRepository = Depends(get_user_session_repo),
) -> UserSession:
    """
    Dependency to get active user session from Bearer token.

    Args:
        auth: HTTP authorization credentials containing Bearer token
        token_manager: Token manager for token verification
        session_repo: User session repository for session validation

    Returns:
        UserSession instance if session is valid and active

    Raises:
    HTTPException: 401 Unauthorized if token is invalid or session not found/expired
"""
    try:
        payload = token_manager.verify_access_token(auth.credentials)
        session = await session_repo.get_active(uuid.UUID(payload.sid))
        return UserSession.from_entity(session)
    except (TokenVerificationError, UserSessionNotFound):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token or session expired.",
        )


async def get_user_permissions(
    auth: HTTPAuthorizationCredentials = Depends(bearer),
    token_manager: TokenManager = Depends(get_token_manager),
    permission_repo: PermissionRepository = Depends(get_permissions_repo),
) -> UserPermissions:
    """
    Dependency to get all user permissions (check Bearer token).

    Args:
        auth: HTTP authorization credentials containing Bearer token
        token_manager: Token manager for token verification
        permission_repo: Permission repository for fetching user permissions

    Returns:
        UserPermissions instance containing user's permissions

    Raises:
        HTTPException: 401 Unauthorized if token is invalid
    """
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
    auth: HTTPAuthorizationCredentials = Depends(bearer),
    token_manager: TokenManager = Depends(get_token_manager),
    session_repo: UserSessionRepository = Depends(get_user_session_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> AuthenticatedUser:
    """
    Dependency to get current authenticated user from Bearer token.

    Args:
        auth: HTTP authorization credentials containing Bearer token
        token_manager: Token manager for token verification
        session_repo: User session repository for session validation
        user_repo: User repository for fetching user data

    Returns:
        AuthenticatedUser instance representing the current user

    Raises:
        HTTPException: 401 Unauthorized if token is invalid or session not found
    """
    try:
        payload = token_manager.verify_access_token(auth.credentials)
        await session_repo.get_active(uuid.UUID(payload.sid))
        user = await user_repo.get_by_id(int(payload.sub))
        return AuthenticatedUser.from_entity(user)
    except (TokenVerificationError, UserSessionNotFound):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )
