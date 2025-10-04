from functools import wraps

from starlette import status
from starlette.exceptions import HTTPException

from src.auth.models import PermissionAction, UserPermissions

__all__ = (
    "require_permission",
)


def require_permission(resource_type: str, action: PermissionAction):
    """
    Decorator to enforce permission checks on route handlers.

    Verifies that the current user has the required permission
    before allowing access to the protected endpoint.

    Args:
        resource_type: Type of resource being accessed (e.g., 'user', 'order')
        action: Action being performed on the resource (e.g., CREATE, READ, UPDATE, DELETE)

    Returns:
        Decorator function that wraps the route handler
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(
            *args,
            permissions: UserPermissions,
            **kwargs,
        ):
            """
            Wrapper function that performs the permission check.

            Args:
                permissions: UserPermissions instance injected by FastAPI dependency
                *args: Positional arguments passed to the original function
                **kwargs: Keyword arguments passed to the original function

            Returns:
                Result of the original function if permission check passes

            Raises:
                HTTPException: 403 Forbidden if user lacks required permission
            """
            if permissions.has_permission(resource_type, action):
                return await func(*args, permissions=permissions, **kwargs)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required: {resource_type}:{action.value} permission.",
            )

        return wrapper

    return decorator
