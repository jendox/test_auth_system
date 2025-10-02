import re
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field, field_validator
from pydantic.alias_generators import to_camel
from pydantic_core.core_schema import ValidationInfo

from src.core.base_types import OptionalStr

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
    new_password: Annotated[PasswordStr, BeforeValidator(_validate_password)]
    confirm_password: PasswordStr

    @field_validator("confirm_password", mode="after")
    @classmethod
    def _validate_confirm_password(cls, value: str, info: ValidationInfo) -> str:
        password = info.data.get("new_password")
        if password != value:
            raise ValueError("Passwords do not match.")
        return value


class RegisterRequest(PasswordConfirmationMixin):
    name: OptionalStr = Field(max_length=32)
    email: EmailStr = Field(max_length=254)

    model_config = ConfigDict(
        extra="forbid",
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "name": "Name",
                    "email": "user@example.com",
                    "newPassword": "Qwerty!234",
                    "confirmPassword": "Qwerty!234",
                },
            ],
        },
    )


class RegisterResponse(BaseModel):
    id: int
    email: EmailStr
    message: OptionalStr

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
    token: str = Field(description="Verification token sent to user's email")
