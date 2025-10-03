import typing
import uuid
from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

if typing.TYPE_CHECKING:
    from src.db.models import UserEntity, UserSessionEntity


class PermissionAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"


class UserRole(BaseModel):
    id: int
    name: str
    description: str

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )


class Permission(BaseModel):
    resource_type: str
    action: PermissionAction


class UserPermissions(BaseModel):
    permissions: list[Permission]

    @classmethod
    def from_dict(cls, perm_dict: dict[str, list[str]]) -> Self:
        return cls(
            permissions=[
                Permission(
                    resource_type=resource_type.lower(),
                    action=PermissionAction(action),
                ) for resource_type, actions in perm_dict.items() for action in actions
            ],
        )

    def has_permission(self, resource_type: str, action: PermissionAction) -> bool:
        return any(
            permission.resource_type == resource_type.lower() and permission.action == action
            for permission in self.permissions
        )


class AuthenticatedUser(BaseModel):
    id: int
    email: str
    is_active: bool = True
    role: UserRole
    permissions: UserPermissions | None = None

    @classmethod
    def from_entity(cls, user_entity: "UserEntity") -> Self:
        return cls(
            id=user_entity.id,
            email=user_entity.email,
            role=UserRole(
                id=user_entity.role_id,
                name=user_entity.role.name,
                description=user_entity.role.description,
            ),
        )

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )


class UserSession(BaseModel):
    id: uuid.UUID
    is_revoked: bool
    expires_at: int

    @classmethod
    def from_entity(cls, session: "UserSessionEntity") -> Self:
        return cls(
            id=session.id,
            is_revoked=session.is_revoked,
            expires_at=session.expires_at,
        )

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )
