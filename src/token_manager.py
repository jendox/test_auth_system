import secrets
import uuid
from datetime import timedelta
from enum import Enum
from typing import Any
from uuid import UUID

import jose.exceptions
from jose import jwt
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from starlette.requests import Request

from config import AppSettings, JWTSettings
from src.core.base_types import OptionalStr
from src.core.utils import get_iat_exp_timestamps


class TokenVerificationError(Exception): ...


REFRESH_TOKEN_LENGTH = 64


class TokenPurpose(str, Enum):
    """
    Enum for defining the purpose of a token.
    Used in payloads to prevent misuse of tokens in incorrect contexts.
    """
    ACCESS = "access"
    REFRESH = "refresh"
    EMAIL_CONFIRMATION = "email_confirmation"
    # PASSWORD_RESET = "password_reset"


class TokenPayload(BaseModel):
    sub: str
    sid: OptionalStr
    iat: int
    exp: int
    jti: OptionalStr
    role: OptionalStr
    purpose: TokenPurpose = Field(default=TokenPurpose.ACCESS)
    fingerprint: OptionalStr

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class AccessToken(BaseModel):
    token: str
    type: str = "bearer"
    created_at: int
    expires_at: int

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )


class RefreshToken(BaseModel):
    token: str
    expires_at: int

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )


class TokenPair(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )


class TokenManager:
    def __init__(self, jwt_settings: JWTSettings) -> None:
        self.secret_key = jwt_settings.secret_key
        self.algorithm = jwt_settings.algorithm
        self.email_confirm_ttl = jwt_settings.email_confirmation_ttl
        self.access_token_ttl = jwt_settings.access_token_ttl
        self.refresh_token_ttl = jwt_settings.refresh_token_ttl

    def create_email_confirmation_token(self, user_id: int) -> str:
        iat, exp = get_iat_exp_timestamps(timedelta(days=self.email_confirm_ttl))
        payload = TokenPayload(
            sub=str(user_id), iat=iat, exp=exp, purpose=TokenPurpose.EMAIL_CONFIRMATION,
        )
        token = self._encode(payload)
        return token

    def verify_email_confirmation_token(self, token: str) -> int:
        payload = self.decode_token(token)
        if payload.purpose != TokenPurpose.EMAIL_CONFIRMATION:
            raise TokenVerificationError(f"Invalid token purpose: {payload.purpose.value}")
        return int(payload.sub)

    def make_access_token_payload(
        self,
        user_id: int,
        user_role: str,
        session_id: UUID,
        sid: str | None = None,
        fingerprint: str | None = None,
    ) -> TokenPayload:
        iat, exp = get_iat_exp_timestamps(timedelta(seconds=self.access_token_ttl))
        return TokenPayload(
            sub=str(user_id),
            sid=sid or str(session_id),
            iat=iat,
            exp=exp,
            jti=str(uuid.uuid4()),
            role=user_role,
            purpose=TokenPurpose.ACCESS,
            fingerprint=fingerprint,
        )

    def create_access_token(self, payload: TokenPayload) -> AccessToken:
        token = self._encode(payload)
        return AccessToken(token=token, created_at=payload.iat, expires_at=payload.exp)

    def verify_access_token(self, token: str) -> TokenPayload:
        payload = self.decode_token(token)
        if payload.purpose != TokenPurpose.ACCESS:
            raise TokenVerificationError(f"Invalid token purpose: {payload.purpose.value}")
        return payload

    def create_refresh_token(self, token_ttl: int | None = None) -> RefreshToken:
        token = secrets.token_urlsafe(REFRESH_TOKEN_LENGTH)
        days = token_ttl or self.refresh_token_ttl
        iat, exp = get_iat_exp_timestamps(timedelta(days=days))
        return RefreshToken(token=token, expires_at=exp)

    def get_token_pair(
        self,
        user_id: int,
        user_role: str,
        session_id: UUID,
        refresh_token_ttl: int | None = None,
    ) -> TokenPair:
        payload = self.make_access_token_payload(user_id, user_role, session_id)
        access_token = self.create_access_token(payload)
        refresh_token = self.create_refresh_token(refresh_token_ttl)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def decode_token(self, token: str, fingerprint: str | None = None) -> TokenPayload:
        try:
            payload = TokenPayload(**self._decode(token))
            if fingerprint and fingerprint != payload.fingerprint:
                raise TokenVerificationError("Token fingerprint mismatch")
            return payload
        except jose.exceptions.JWTError as e:
            raise TokenVerificationError(e)

    def _encode(self, payload: TokenPayload) -> str:
        return jwt.encode(payload.to_dict(), self.secret_key.get_secret_value(), self.algorithm)

    def _decode(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self.secret_key.get_secret_value(), [self.algorithm])


def get_token_manager(
    request: Request,
) -> TokenManager:
    settings: AppSettings = request.state.app_settings
    return TokenManager(settings.jwt)
