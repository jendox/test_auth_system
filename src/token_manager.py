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

from src.config import AppSettings, JWTSettings
from src.core.base_types import OptionalStr
from src.core.utils import get_iat_exp_timestamps


class TokenVerificationError(Exception):
    """Exception raised when token verification fails."""


REFRESH_TOKEN_LENGTH = 64


class TokenPurpose(str, Enum):
    """
    Enum for defining the purpose of a token.
    Used in payloads to prevent misuse of tokens in incorrect contexts.
    """
    ACCESS = "access"
    REFRESH = "refresh"
    EMAIL_CONFIRMATION = "email_confirmation"


class TokenPayload(BaseModel):
    """Represents the payload data structure for JWT tokens."""
    sub: str
    """Subject identifier (typically user ID)"""
    sid: OptionalStr
    """Session identifier"""
    iat: int
    """Issued at timestamp"""
    exp: int
    """Expiration timestamp"""
    jti: OptionalStr
    """JWT ID (unique token identifier)"""
    role: OptionalStr
    """User role"""
    purpose: TokenPurpose = Field(default=TokenPurpose.ACCESS)
    """Intended use case for the token"""
    fingerprint: OptionalStr
    """Browser/device fingerprint for additional security"""

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class AccessToken(BaseModel):
    """Represents an access token with metadata."""
    token: str
    """The JWT access token string"""
    type: str = "bearer"
    """Token type (default: "bearer")"""
    created_at: int
    """Token creation timestamp"""
    expires_at: int
    """Token expiration timestamp"""

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )


class RefreshToken(BaseModel):
    """Represents a refresh token with metadata."""
    token: str
    """The refresh token string"""
    expires_at: int
    """Token expiration timestamp"""

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )


class TokenPair(BaseModel):
    """Represents a pair of access and refresh tokens."""
    access_token: AccessToken
    """The access token instance"""
    refresh_token: RefreshToken
    """The refresh token instance"""

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )


class TokenManager:
    """
    Manager class for handling token creation, verification, and management.

    Provides methods for creating and verifying various types of tokens
    including access tokens, refresh tokens, and email confirmation tokens.
    """

    def __init__(self, jwt_settings: JWTSettings) -> None:
        self.secret_key = jwt_settings.secret_key
        self.algorithm = jwt_settings.algorithm
        self.email_confirm_ttl = jwt_settings.email_confirmation_ttl
        self.access_token_ttl = jwt_settings.access_token_ttl
        self.refresh_token_ttl = jwt_settings.refresh_token_ttl

    def create_email_confirmation_token(self, user_id: int) -> str:
        """
        Create an email confirmation token for user verification.

        Args:
            user_id: The ID of the user to create the token for

        Returns:
            JWT token string for email confirmation
        """
        iat, exp = get_iat_exp_timestamps(timedelta(days=self.email_confirm_ttl))
        payload = TokenPayload(
            sub=str(user_id), iat=iat, exp=exp, purpose=TokenPurpose.EMAIL_CONFIRMATION,
        )
        token = self._encode(payload)
        return token

    def verify_email_confirmation_token(self, token: str) -> int:
        """
        Verify and decode an email confirmation token.

        Args:
            token: The JWT token string to verify

        Returns:
            User ID extracted from the token

        Raises:
            TokenVerificationError: If token purpose is invalid or verification fails
        """
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
        """
        Create a payload for access token with user and session information.

        Args:
            user_id: The ID of the user
            user_role: The role of the user
            session_id: Unique session identifier
            sid: Optional session ID string
            fingerprint: Optional browser/device fingerprint

        Returns:
            TokenPayload instance configured for access token
        """
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
        """
        Create an access token from a payload.

        Args:
            payload: The token payload to encode

        Returns:
            AccessToken instance containing the encoded token and metadata
        """
        token = self._encode(payload)
        return AccessToken(token=token, created_at=payload.iat, expires_at=payload.exp)

    def verify_access_token(self, token: str) -> TokenPayload:
        """
        Verify and decode an access token.

        Args:
            token: The JWT access token string to verify

        Returns:
            Decoded token payload

        Raises:
            TokenVerificationError: If token purpose is invalid or verification fails
        """
        payload = self.decode_token(token)
        if payload.purpose != TokenPurpose.ACCESS:
            raise TokenVerificationError(f"Invalid token purpose: {payload.purpose.value}")
        return payload

    def create_refresh_token(self, token_ttl: int | None = None) -> RefreshToken:
        """
        Create a cryptographically secure refresh token.

        Args:
            token_ttl: Optional time-to-live in days for the token

        Returns:
            RefreshToken instance with generated token and expiration
        """
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
        """
        Create a pair of access and refresh tokens for a user session.

        Args:
            user_id: The ID of the user
            user_role: The role of the user
            session_id: Unique session identifier
            refresh_token_ttl: Optional time-to-live for refresh token

        Returns:
            TokenPair instance containing both access and refresh tokens
        """
        payload = self.make_access_token_payload(user_id, user_role, session_id)
        access_token = self.create_access_token(payload)
        refresh_token = self.create_refresh_token(refresh_token_ttl)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def decode_token(self, token: str, fingerprint: str | None = None) -> TokenPayload:
        """
        Decode and verify a JWT token with optional fingerprint validation.

        Args:
            token: The JWT token string to decode
            fingerprint: Optional fingerprint to validate against token

        Returns:
            Decoded TokenPayload instance

        Raises:
            TokenVerificationError: If token is invalid, expired, or fingerprint mismatch
        """
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
    """
    Dependency function to get TokenManager instance from request.

    Args:
        request: The Starlette request object

    Returns:
        TokenManager instance configured with app settings
    """
    settings: AppSettings = request.state.app_settings
    return TokenManager(settings.jwt)
