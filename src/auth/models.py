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


class Permission(BaseModel):
    id: int
    name: str
    description: str
    resource_type: str
    action: PermissionAction

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )


class UserRole(BaseModel):
    id: int
    name: str
    description: str

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )


class UserPermission(BaseModel):
    permission: Permission
    granted: bool


class AuthenticatedUser(BaseModel):
    id: int
    email: str
    is_active: bool = True
    role: UserRole
    permissions: list[UserPermission]

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
            permissions=[
                UserPermission(
                    permission=Permission(
                        id=p.permission_id,
                        name=p.permission.name,
                        description=p.permission.description,
                        resource_type=p.permission.resource_type.name,
                        action=PermissionAction(p.permission.action),
                    ),
                    granted=p.granted,
                )
                for p in user_entity.user_permissions],
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


class AuthenticatedContext(BaseModel):
    user: AuthenticatedUser
    session: UserSession

    @classmethod
    def from_entities(
        cls,
        user: "UserEntity",
        session: "UserSessionEntity",
    ) -> Self:
        return cls(
            user=AuthenticatedUser.from_entity(user),
            session=UserSession.from_entity(session),
        )

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )
