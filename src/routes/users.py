from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status
from starlette.responses import JSONResponse

from src.auth.exceptions import InsufficientPermissions
from src.auth.models import AuthenticatedUser, UserPermissions
from src.auth.security import get_current_user, get_user_permissions
from src.notifier import Notifier, get_notifier
from src.routes.shemas import ConfirmEmailRequest, RegisterRequest, RegisterResponse
from src.routes.shemas.user import GetMeResponse
from src.token_manager import TokenVerificationError
from src.users.repository import AdminDeletion, UserAlreadyActivated, UserAlreadyExists, UserNotFound
from src.users.use_cases.confirm_email import ConfirmEmailUseCase, get_confirm_email_use_case
from src.users.use_cases.delete import DeleteUserUseCase, get_delete_user_use_case
from src.users.use_cases.register import (
    RegisterUserUseCase,
    get_register_user_use_case,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    path="/me",
    summary="Get current user profile",
    description="Retrieve the current authenticated user's profile information.",
    response_model=GetMeResponse,
)
async def get_me(
    user: AuthenticatedUser = Depends(get_current_user),
):
    return GetMeResponse(**user.model_dump())


@router.post(
    path="",
    summary="Register new user",
    description="Register a new user account with email and password.",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "User successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "id": "1",
                        "email": "user@example.com",
                        "message": "Registration successful. Please check your email for verification.",
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "User already exists",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with email 'user@example.com' already exists.",
                    },
                },
            },
        },
    },
)
async def register(
    payload: RegisterRequest,
    use_case: RegisterUserUseCase = Depends(get_register_user_use_case),
    notifier: Notifier = Depends(get_notifier),
) -> RegisterResponse:
    try:
        user_id = await use_case(payload)
        token = await notifier.send_email_confirmation(user_id, payload.email)
        return RegisterResponse(
            id=user_id,
            email=payload.email,
            message=f"Registration successful. "
                    f"Please check your email for verification. Token={token}",
        )
    except UserAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    path="/confirm-email",
    summary="Confirm email address",
    description="Verify user's email address using the verification token sent to their email.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Confirmed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email address confirmed successfully.",
                    },
                },
            },
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Confirmation failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid or expired verification token.",
                    },
                },
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Confirmation failed",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email address already confirmed.",
                    },
                },
            },
        },
    },
)
async def confirm_registration(
    payload: ConfirmEmailRequest,
    use_case: ConfirmEmailUseCase = Depends(get_confirm_email_use_case),
) -> JSONResponse:
    try:
        await use_case(payload)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": "Email address confirmed successfully."},
        )
    except TokenVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    except UserAlreadyActivated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already confirmed.",
        )


@router.delete(
    path="/{user_id}",
    summary="Delete user",
    description="""Delete user by ID.\n
        - Users can delete their own account without special permissions\n
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
    user_id: int = Path(gt=0, description="User ID (must be positive integer)"),
    user: AuthenticatedUser = Depends(get_current_user),
    permissions: UserPermissions = Depends(get_user_permissions),
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
):
    try:
        await use_case(user_id, user.id, permissions)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except AdminDeletion:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete admin user",
        )
    except InsufficientPermissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete other users.",
        )
