from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status

from src.admin.use_cases import (
    DeleteUserUseCase,
    ManageUserPermissionsUseCase,
    get_delete_user_use_case,
    manage_user_permissions_use_case,
)
from src.auth.exceptions import InsufficientPermissions, PermissionNotFound
from src.auth.models import AuthenticatedUser, PermissionAction, UserPermissions, UserSession
from src.auth.permissions_decorator import require_permission
from src.auth.security import get_current_user, get_user_permissions, get_user_session
from src.routes.shemas import ReadUserPermissionsResponse, SetPermissionRequest
from src.users.exceptions import AdminDeletion, UserNotFound

router = APIRouter(prefix="/admin", tags=["Administrator"])


@router.get(
    path="/user-permissions/{user_id}",
    summary="Get user permissions",
    description="Retrieve all permissions for a specific user including role-based and individual permissions.",
    response_model=ReadUserPermissionsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "User permissions retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "userId": 1,
                        "permissions": [
                            {
                                "resourceType": "user",
                                "action": "read",
                            },
                            {
                                "resourceType": "user",
                                "action": "update",
                            },
                            {
                                "resourceType": "order",
                                "action": "create",
                            },
                        ],
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied. Required: user:read permission.",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with id '999' does not exist",
                    },
                },
            },
        },
    },
)
@require_permission("user", PermissionAction.READ)
async def read_user_permissions(
    _: UserSession = Depends(get_user_session),
    permissions: UserPermissions = Depends(get_user_permissions),
    use_case: ManageUserPermissionsUseCase = Depends(manage_user_permissions_use_case),
    user_id: int = Path(gt=0),
) -> ReadUserPermissionsResponse:
    permissions = await use_case.read_user_permissions(user_id)
    return ReadUserPermissionsResponse(
        user_id=user_id,
        permissions=permissions,
    )


@router.put(
    path="/user-permissions/{user_id}",
    summary="Update user permissions",
    description="Grant or revoke specific permissions for a user. Overrides role-based permissions.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "User permissions updated successfully",
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied. Required: user:update permission.",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User or permission not found",
            "content": {
                "application/json": {
                    "examples": {
                        "UserNotFound": {
                            "value": {
                                "detail": "User with id '999' does not exist",
                            },
                        },
                        "PermissionNotFound": {
                            "value": {
                                "detail": "Permission order_manage not found",
                            },
                        },
                    },
                },
            },
        },
    },
)
@require_permission("user", PermissionAction.UPDATE)
async def write_user_permissions(
    payload: SetPermissionRequest,
    user_id: int = Path(gt=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    permissions: UserPermissions = Depends(get_user_permissions),
    use_case: ManageUserPermissionsUseCase = Depends(manage_user_permissions_use_case),
):
    try:
        await use_case.set_user_permission(
            user_id, payload.permission_name, payload.granted, current_user.id,
        )
        return {"description": "User permissions updated successfully"}
    except (UserNotFound, PermissionNotFound) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    path="/user-delete/{user_id}",
    summary="Delete user",
    description="""Delete user by ID.\n
        - Deleting other users requires 'user:delete' permission\n
        - Admin users cannot be deleted""",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "User successfully deleted",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User deleted successfully.",
                    },
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Insufficient permissions to delete other users",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Insufficient permissions to delete other users.",
                    },
                },
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User not found.",
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Delete user failed due to business logic constraint",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot delete admin user.",
                    },
                },
            },
        },
    },
)
async def delete(
    user_id: int = Path(gt=0),
    permissions: UserPermissions = Depends(get_user_permissions),
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
):
    try:
        await use_case(user_id, permissions)
        return {"detail": "User deleted successfully."}
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    except AdminDeletion:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete admin user.",
        )
    except InsufficientPermissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete other users.",
        )
