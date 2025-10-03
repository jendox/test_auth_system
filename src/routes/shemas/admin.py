from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from src.auth.models import Permission


class ReadUserPermissionsResponse(BaseModel):
    user_id: int
    permissions: list[Permission]

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
    permission_name: str
    granted: bool

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
