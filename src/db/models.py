import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.auth.models import PermissionAction
from src.db.base_models import TimestampedBase

__all__ = (
    "UserEntity",
    "UserRoleEntity",
    "PermissionEntity",
    "ResourceTypeEntity",
    "RolePermissionEntity",
    "UserPermissionEntity",
    "UserSessionEntity",
    "RefreshTokenEntity",
)


class UserEntity(TimestampedBase):
    """
    Entity representing a user in the system.

    Stores user account information, authentication details, and relationships
    to roles, permissions, and sessions.

    Attributes:
        name: User's full name
        email: User's email address (unique)
        hashed_password: Securely hashed password
        is_active: Account activation status
        role_id: Reference to user's role
    """
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(32), nullable=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(default=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("user_roles.id"))
    # Relationships
    role: Mapped["UserRoleEntity"] = relationship(
        back_populates="users",
    )
    user_permissions: Mapped[list["UserPermissionEntity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UserPermissionEntity.user_id",
    )
    sessions: Mapped[list["UserSessionEntity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    granted_permissions: Mapped[list["UserPermissionEntity"]] = relationship(
        back_populates="granter",
        foreign_keys="UserPermissionEntity.granted_by",
    )


class UserRoleEntity(TimestampedBase):
    """
    Entity representing user roles in the system.

    Defines role-based access control groups with descriptive information.

    Attributes:
        name: Unique role identifier
        description: Human-readable role description
    """
    __tablename__ = "user_roles"

    name: Mapped[str] = mapped_column(String(32), unique=True)
    description: Mapped[str] = mapped_column(String(200))
    # Relationships
    users: Mapped[list["UserEntity"]] = relationship(back_populates="role")
    role_permissions: Mapped[list["RolePermissionEntity"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )


class PermissionEntity(TimestampedBase):
    """
    Entity representing individual permissions in the system.

    Defines granular access controls for specific resources and actions.

    Attributes:
        name: Unique permission identifier
        description: Human-readable permission description
        resource_type_id: Reference to resource type
        action: Type of operation allowed (CRUD)
    """
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(200))
    resource_type_id: Mapped[int] = mapped_column(ForeignKey("resource_types.id"))
    action: Mapped[str] = mapped_column(String(6), Enum(PermissionAction))
    # Relationships
    role_permissions: Mapped[list["RolePermissionEntity"]] = relationship(
        back_populates="permission",
        cascade="all, delete-orphan",
    )
    user_permissions: Mapped[list["UserPermissionEntity"]] = relationship(
        back_populates="permission",
        cascade="all, delete-orphan",
    )
    resource_type: Mapped["ResourceTypeEntity"] = relationship(back_populates="permissions")


class ResourceTypeEntity(TimestampedBase):
    """
    Entity representing types of resources in the system.

    Categorizes different business objects that permissions can be applied to.

    Attributes:
        name: Unique resource type identifier
        description: Human-readable resource type description
    """
    __tablename__ = "resource_types"

    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(String(200), nullable=True)
    # Relationships
    permissions: Mapped[list["PermissionEntity"]] = relationship(back_populates="resource_type")


class RolePermissionEntity(TimestampedBase):
    """
    Junction entity linking roles to permissions.

    Implements many-to-many relationship between roles and permissions
    for role-based access control.

    Attributes:
        role_id: Reference to user role
        permission_id: Reference to permission
    """
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(ForeignKey("user_roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)
    # Relationships
    role: Mapped["UserRoleEntity"] = relationship(back_populates="role_permissions")
    permission: Mapped["PermissionEntity"] = relationship(back_populates="role_permissions")


class UserPermissionEntity(TimestampedBase):
    """
    Junction entity for user-specific permission grants.

    Allows granting or revoking individual permissions to specific users
    beyond their role-based permissions.

    Attributes:
        user_id: Reference to user
        permission_id: Reference to permission
        granted: Boolean flag indicating permission status
        granted_by: Reference to user who granted the permission
    """
    __tablename__ = "user_permissions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)
    granted: Mapped[bool] = mapped_column(Boolean, default=True)
    granted_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    # Relationships
    user: Mapped["UserEntity"] = relationship(
        back_populates="user_permissions",
        foreign_keys=[user_id],
    )
    permission: Mapped["PermissionEntity"] = relationship(
        back_populates="user_permissions",
    )
    granter: Mapped["UserEntity"] = relationship(
        back_populates="granted_permissions",
        foreign_keys=[granted_by],
    )


class UserSessionEntity(TimestampedBase):
    """
    Entity representing user authentication sessions.

    Tracks active user sessions with expiration and revocation status.

    Attributes:
        id: Unique session identifier (UUID)
        user_id: Reference to user
        is_revoked: Session revocation status
        expires_at: Session expiration timestamp
    """
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_revoked: Mapped[bool] = mapped_column(default=False)
    expires_at: Mapped[int]
    # Relationships
    user: Mapped["UserEntity"] = relationship(
        back_populates="sessions",
    )
    refresh_token: Mapped["RefreshTokenEntity"] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class RefreshTokenEntity(TimestampedBase):
    """
    Entity representing refresh tokens for session management.

    Stores hashed refresh tokens with expiration and revocation status
    for secure token rotation.

    Attributes:
        session_id: Reference to user session
        token_hash: Securely hashed refresh token
        expires_at: Token expiration timestamp
        is_revoked: Token revocation status
    """
    __tablename__ = "refresh_tokens"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_sessions.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[int]
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    session: Mapped["UserSessionEntity"] = relationship(
        back_populates="refresh_token",
        lazy="selectin",
    )
