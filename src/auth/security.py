from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status
from starlette.exceptions import HTTPException

from src.token_manager import TokenManager, TokenVerificationError, get_token_manager

from .models import AuthenticatedContext
from .repository import UserSessionNotFound, UserSessionRepository, get_user_session_repo


async def get_authenticated_context(
    auth: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    token_manager: TokenManager = Depends(get_token_manager),
    session_repo: UserSessionRepository = Depends(get_user_session_repo),
) -> AuthenticatedContext:
    try:
        payload = token_manager.verify_access_token(auth.credentials)
        session = await session_repo.get_active(UUID(payload.sid))
        return AuthenticatedContext.from_entities(session.user, session)
    except (TokenVerificationError, UserSessionNotFound):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )
