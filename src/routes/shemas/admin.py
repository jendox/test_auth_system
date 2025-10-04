from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from src.auth.models import Permission

__all__ = (
    "ReadUserPermissionsResponse",
    "SetPermissionRequest",
)


class ReadUserPermissionsResponse(BaseModel):
    """Response model for reading user permissions."""
    user_id: int
    """Unique identifier of the user"""
    permissions: list[Permission]
    """List of permissions assigned to the user"""

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        extra="forbid",
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "userId": 1,
                    "permissions": "",
                },
            ],
        },
    )


class SetPermissionRequest(BaseModel):
    """Request model for setting user permissions."""
    permission_name: str
    """Name of the permission to set"""
    granted: bool
    """Boolean flag indicating if permission is granted or revoked"""

    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        extra="forbid",
        alias_generator=to_camel,
        json_schema_extra={
            "examples": [
                {
                    "permissionName": "order_update",
                    "granted": True,
                },
            ],
        },
    )
