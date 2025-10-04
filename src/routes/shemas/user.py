import re
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_core.core_schema import ValidationInfo

from src.auth.models import UserRole
from src.core.base_types import OptionalStr

__all__ = (
    "RegisterRequest",
    "RegisterResponse",
    "ConfirmEmailRequest",
    "GetMeResponse",
    "UpdateProfileRequest",
    "ChangePasswordRequest",
)

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 64


def _validate_password(value: str) -> str:
    if len(value) < PASSWORD_MIN_LENGTH:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Password must contain at least one special character.")
    return value


PasswordStr = Annotated[
    str,
    Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH),
]


class PasswordConfirmationMixin(BaseModel):
    """Mixin for password confirmation validation."""
    new_password: Annotated[PasswordStr, BeforeValidator(_validate_password)]
    """New password meeting security requirements"""
    confirm_password: PasswordStr
    """Password confirmation that must match new_password"""

    @field_validator("confirm_password", mode="after")
    @classmethod
    def _validate_confirm_password(cls, value: str, info: ValidationInfo) -> str:
        password = info.data.get("new_password")
        if password != value:
            raise ValueError("Passwords do not match.")
        return value


class RegisterRequest(PasswordConfirmationMixin):
    """Request model for user registration.

    Attributes:
        name: User's full name (optional)
        email: User's email address
        user_role: User's role
        new_password: Secure password for the account
        confirm_password: Password confirmation
    """
    name: OptionalStr = Field(max_length=32)
    """User's full name (optional)"""
    email: EmailStr = Field(max_length=254)
    """User's email address"""
    user_role: str = Field(max_length=32)
    """User's role"""

    model_config = ConfigDict(
        extra="forbid",
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "name": "John Leonard",
                    "email": "user@example.com",
                    "user_role": "user",
                    "newPassword": "Qwerty!234",
                    "confirmPassword": "Qwerty!234",
                },
            ],
        },
    )


class RegisterResponse(BaseModel):
    """Response model for user registration."""
    id: int
    """Unique identifier of the newly created user"""
    email: EmailStr
    """Registered email address"""
    message: OptionalStr
    """Optional success or informational message"""

    model_config = ConfigDict(
        extra="forbid",
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "email": "user@email.com",
                },
            ],
        },
    )


class ConfirmEmailRequest(BaseModel):
    """Request model for email confirmation."""
    token: str
    """Verification token sent to user's email"""


class GetMeResponse(BaseModel):
    """Response model for current user profile information."""
    id: int
    """User's unique identifier"""
    name: str
    """User's full name"""
    email: str
    """User's email address"""
    is_active: bool
    """Account activation status"""
    role: UserRole
    """User's role information"""

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "John",
                    "email": "user@email.com",
                    "isActive": True,
                    "role": {
                        "id": 1,
                        "name": "admin",
                        "description": "Administrator with full access",
                    },
                },
            ],
        },
    )


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""
    name: str = Field(max_length=32)
    """User's full name"""

    model_config = ConfigDict(
        extra="forbid",
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "name": "John Smith",
                },
            ],
        },
    )


class ChangePasswordRequest(PasswordConfirmationMixin):
    """
    Request model for changing user password.

    Attributes:
        current_password: User's current password for verification
        new_password: New secure password
        confirm_password: Password confirmation
    """
    current_password: str = Field(max_length=PASSWORD_MAX_LENGTH)
    """User's current password for verification"""

    model_config = ConfigDict(
        extra="forbid",
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "currentPassword": "Qwerty!234",
                    "newPassword": "NewQwerty!234",
                    "confirmPassword": "NewQwerty!234",
                },
            ],
        },
    )
