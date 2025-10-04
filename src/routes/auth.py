from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.auth.exceptions import AuthenticationError, TokenNotFound
from src.auth.models import UserSession
from src.auth.security import get_user_session
from src.auth.use_cases import (
    LoginUseCase,
    LogoutUseCase,
    RefreshUseCase,
    get_login_use_case,
    get_logout_use_case,
    get_refresh_use_case,
)
from src.routes.shemas import LoginRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    path="/login",
    summary="User login",
    description="Authenticate user with email and password to obtain access and refresh tokens.",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "accessToken": {
                            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "createdAt": 1759433609,
                            "expiresAt": 1759434809,
                        },
                        "refreshToken": {
                            "token": "MlcQcgkhQwfr-ddiTzVXqDmhAXRlQhA...",
                            "expiresAt": 1759520009,
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid credentials.",
                    },
                },
            },
        },
    },
)
async def login(
    login_request: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case),
) -> TokenResponse:
    try:
        token_pair = await use_case(login_request)
        return TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
        )
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )


@router.post(
    path="/refresh",
    summary="Refresh access token",
    description="Obtain new access token using valid refresh token.",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Tokens successfully refreshed",
            "content": {
                "application/json": {
                    "example": {
                        "accessToken": {
                            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "createdAt": 1759437209,
                            "expiresAt": 1759438409,
                        },
                        "refreshToken": {
                            "token": "NlcQcgkhQwfr-ddiTzVXqDmhAXRlQhB...",
                            "expiresAt": 1759523609,
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired refresh token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid or expired refresh token.",
                    },
                },
            },
        },
    },
)
async def refresh_token(
    payload: RefreshRequest,
    use_case: RefreshUseCase = Depends(get_refresh_use_case),
) -> TokenResponse:
    try:
        token_pair = await use_case(payload.refresh_token)
        return TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
        )
    except TokenNotFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )


@router.post(
    path="/logout",
    summary="User logout",
    description="Invalidate user session and revoke refresh token.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Successfully logged out",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Successfully logged out.",
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid or expired authentication token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid authentication token.",
                    },
                },
            },
        },
    },
)
async def logout(
    user_session: UserSession = Depends(get_user_session),
    use_case: LogoutUseCase = Depends(get_logout_use_case),
):
    await use_case(user_session.id)
    return {"detail": "Successfully logged out."}
