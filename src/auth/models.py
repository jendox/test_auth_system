import typing
import uuid
from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

if typing.TYPE_CHECKING:
    from src.db.models import UserEntity, UserSessionEntity


class PermissionAction(str, Enum):
    """
    Enumeration of possible actions that can be performed on resources.

    Represents CRUD operations plus management capabilities for access control.
    """
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"


class UserRole(BaseModel):
    """Model representing a user role in the system."""
    id: int
    """Unique identifier for the role"""
    name: str
    """Role name identifier"""
    description: str
    """Human-readable role description"""

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )


class Permission(BaseModel):
    """Model representing a single permission grant."""
    resource_type: str
    """Type of resource the permission applies to"""
    action: PermissionAction
    """Action allowed on the resource"""


class UserPermissions(BaseModel):
    """Container for a user's complete set of permissions.

    Combines role-based permissions with individual user permissions
    for comprehensive access control.
    """
    permissions: list[Permission]
    """List of permission grants for the user"""

    @classmethod
    def from_dict(cls, perm_dict: dict[str, list[str]]) -> Self:
        """
        Create UserPermissions instance from permission dictionary.

        Args:
            perm_dict: Dictionary mapping resource types to allowed actions

        Returns:
            UserPermissions instance with structured permission objects
        """
        return cls(
            permissions=[
                Permission(
                    resource_type=resource_type.lower(),
                    action=PermissionAction(action),
                ) for resource_type, actions in perm_dict.items() for action in actions
            ],
        )

    def has_permission(self, resource_type: str, action: PermissionAction) -> bool:
        """
        Check if user has specific permission for a resource and action.

        Args:
            resource_type: Type of resource to check permission for
            action: Action to check permission for

        Returns:
            True if user has the requested permission, False otherwise
        """
        return any(
            permission.resource_type == resource_type.lower() and permission.action == action
            for permission in self.permissions
        )


class AuthenticatedUser(BaseModel):
    """Model representing an authenticated user with complete profile information.

    Contains user identity, role, and permissions for use in request processing.
    """
    id: int
    """User's unique identifier"""
    name: str
    """User's full name"""
    email: str
    """User's email address"""
    is_active: bool = True
    """Account activation status"""
    role: UserRole
    """User's assigned role"""
    permissions: UserPermissions | None = None
    """User's complete permission set (optional)"""

    @classmethod
    def from_entity(cls, user_entity: "UserEntity") -> Self:
        """
        Create AuthenticatedUser from database UserEntity.

        Args:
            user_entity: Database entity representing the user

        Returns:
            AuthenticatedUser instance populated from entity data
        """
        return cls(
            id=user_entity.id,
            email=user_entity.email,
            name=user_entity.name or "",
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
    """Model representing a user authentication session.

    Tracks session state and expiration for security management.
    """
    id: uuid.UUID
    """Unique session identifier (UUID)"""
    is_revoked: bool
    """Whether the session has been revoked"""
    expires_at: int
    """Session expiration timestamp"""
    user_id: int
    """Unique user identifier"""

    @classmethod
    def from_entity(cls, session: "UserSessionEntity") -> Self:
        """
        Create UserSession from database UserSessionEntity.

        Args:
            session: Database entity representing the session

        Returns:
            UserSession instance populated from entity data
        """
        return cls(
            id=session.id,
            is_revoked=session.is_revoked,
            expires_at=session.expires_at,
            user_id=session.user_id,
        )

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        alias_generator=to_camel,
    )
