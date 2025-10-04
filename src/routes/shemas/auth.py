from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel

from src.routes.shemas.user import PASSWORD_MAX_LENGTH
from src.token_manager import AccessToken, RefreshToken

__all__ = (
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
)


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr
    """User's email address"""
    password: str = Field(max_length=PASSWORD_MAX_LENGTH)
    """User's password"""
    remember_me: bool = Field(default=False, description="Set the session TTL to 14 days")
    """Flag to extend session duration to 14 days"""

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        extra="forbid",
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "Qwerty!234",
                    "rememberMe": True,
                },
            ],
        },
    )


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    access_token: AccessToken
    """Access token for API authorization"""
    refresh_token: RefreshToken
    """Refresh token for obtaining a new access token"""

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        extra="forbid",
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "accessToken": {
                        "token": "eyJhbGciOiJIUzI1Ni...",
                        "type": "bearer",
                        "createdAt": 1759433609,
                        "expiresAt": 1759434809,
                    },
                    "refreshToken": {
                        "token": "MlcQcgkhQwfr-ddiTz...",
                        "expiresAt": 1759520009,
                    },
                },
            ],
        },
    )


class RefreshRequest(BaseModel):
    """Request model for token refresh."""
    refresh_token: str
    """Valid refresh token to obtain new access token"""

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        extra="forbid",
        alias_generator=to_camel,
    )
