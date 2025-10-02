import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.auth.models import PermissionAction
from src.db.base_models import TimestampedBase


class UserEntity(TimestampedBase):
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
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(200))
    resource_type_id: Mapped[int] = mapped_column(ForeignKey("resource_types.id"))
    action: Mapped[str] = mapped_column(String(6), Enum(PermissionAction))

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
    __tablename__ = "resource_types"

    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(String(200), nullable=True)

    permissions: Mapped[list["PermissionEntity"]] = relationship(back_populates="resource_type")


class RolePermissionEntity(TimestampedBase):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(ForeignKey("user_roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)

    role: Mapped["UserRoleEntity"] = relationship(back_populates="role_permissions")
    permission: Mapped["PermissionEntity"] = relationship(back_populates="role_permissions")


class UserPermissionEntity(TimestampedBase):
    __tablename__ = "user_permissions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)
    granted: Mapped[bool] = mapped_column(Boolean, default=True)
    granted_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)

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
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_revoked: Mapped[bool] = mapped_column(default=False)
    expires_at: Mapped[int]

    user: Mapped["UserEntity"] = relationship(
        back_populates="sessions",
    )
    refresh_token: Mapped["RefreshTokenEntity"] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class RefreshTokenEntity(TimestampedBase):
    __tablename__ = "refresh_tokens"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_sessions.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[int]
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    session: Mapped["UserSessionEntity"] = relationship(
        back_populates="refresh_token",
        lazy="selectin",
    )
