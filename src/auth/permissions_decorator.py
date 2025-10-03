from functools import wraps

from starlette import status
from starlette.exceptions import HTTPException

from src.auth.models import PermissionAction, UserPermissions


def require_permission(resource_type: str, action: PermissionAction):
    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            permissions: UserPermissions,
            **kwargs,
        ):
            if permissions.has_permission(resource_type, action):
                return await func(*args, permissions=permissions, **kwargs)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required: {resource_type}:{action.value} permission.",
            )

        return wrapper

    return decorator
