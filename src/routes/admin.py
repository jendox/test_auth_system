from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status

from src.admin.use_case import ManageUserPermissionsUseCase, manage_user_permissions_use_case
from src.auth.exceptions import PermissionNotFound
from src.auth.models import AuthenticatedUser, PermissionAction, UserPermissions, UserSession
from src.auth.permissions_decorator import require_permission
from src.auth.security import get_current_user, get_user_permissions, get_user_session
from src.routes.shemas.admin import ReadUserPermissionsResponse, SetPermissionRequest
from src.users.repository import UserNotFound

router = APIRouter(prefix="/admin", tags=["Administrator"])


@router.get(
    path="/user-permissions/{user_id}",
    response_model=ReadUserPermissionsResponse,
    status_code=status.HTTP_200_OK,
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
    status_code=status.HTTP_204_NO_CONTENT,
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
    except (UserNotFound, PermissionNotFound) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
