from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel

from src.routes.shemas.user import PASSWORD_MAX_LENGTH
from src.token_manager import AccessToken, RefreshToken


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=PASSWORD_MAX_LENGTH)
    remember_me: bool = Field(default=False, description="Set the session TTL to 14 days")

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        extra="forbid",
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "Qwerty!123",
                    "rememberMe": True,
                },
            ],
        },
    )


class TokenResponse(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken

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
    refresh_token: str = Field(description="Valid refresh token to obtain new access token")

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        extra="forbid",
        alias_generator=to_camel,
    )
