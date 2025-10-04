from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from starlette.responses import JSONResponse

from src.auth.exceptions import AuthenticationError
from src.auth.models import AuthenticatedUser, UserSession
from src.auth.security import get_current_user, get_user_session
from src.notifier import Notifier, get_notifier
from src.routes.shemas import (
    ChangePasswordRequest,
    ConfirmEmailRequest,
    GetMeResponse,
    RegisterRequest,
    RegisterResponse,
    UpdateProfileRequest,
)
from src.token_manager import TokenVerificationError
from src.users.exceptions import AdminDeletion, UserAlreadyActivated, UserAlreadyExists, UserRoleNotFound
from src.users.use_cases import (
    ChangePasswordUseCase,
    ConfirmEmailUseCase,
    DeleteMeUseCase,
    RegisterUserUseCase,
    UpdateProfileUseCase,
    get_change_password_use_case,
    get_confirm_email_use_case,
    get_delete_me_use_case,
    get_register_user_use_case,
    get_update_profile_use_case,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    path="/me",
    summary="Get current user profile",
    description="Retrieve the current authenticated user's profile information.",
    response_model=GetMeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "User profile retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "1",
                        "email": "user@example.com",
                        "first_name": "John",
                        "role": "user",
                        "is_active": True,
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated",
                    },
                },
            },
        },
    },
)
async def get_me(
    user: AuthenticatedUser = Depends(get_current_user),
):
    return GetMeResponse(**user.model_dump())


@router.delete(
    path="/me",
    summary="Delete user profile",
    description="Delete current user's profile.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Profile deleted successfully",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated.",
                    },
                },
            },
        },
    },
)
async def delete_me(
    user_session: UserSession = Depends(get_user_session),
    use_case: DeleteMeUseCase = Depends(get_delete_me_use_case),
):
    try:
        await use_case(user_session.user_id, user_session.id)
    except AdminDeletion:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete admin user",
        )


@router.put(
    path="/me",
    summary="Update user profile",
    description="Update current user's profile information such as name.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Profile updated successfully",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated.",
                    },
                },
            },
        },
    },
)
async def update_profile(
    payload: UpdateProfileRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    use_case: UpdateProfileUseCase = Depends(get_update_profile_use_case),
):
    await use_case(user.id, payload.name)


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
        status.HTTP_400_BAD_REQUEST: {
            "description": "User role doesn't exist",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User role 'superboss' not found.",
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
    except UserRoleNotFound as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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


@router.put(
    path="/me/password",
    summary="Change user password",
    description="Change current user's password with current password verification.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Password changed successfully",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Invalid password or validation error",
            "content": {
                "application/json": {
                    "example": {
                        "WeakPassword": {
                            "value": {
                                "detail": "Password must contain at least one uppercase letter.",
                            },
                        },
                        "InvalidPassword": {
                            "value": {
                                "detail": "Current password is incorrect.",
                            },
                        },
                    },
                },
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated.",
                    },
                },
            },
        },
    },
)
async def change_password(
    payload: ChangePasswordRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    use_case: ChangePasswordUseCase = Depends(get_change_password_use_case),
):
    try:
        await use_case(user.id, payload.current_password, payload.new_password)
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Current password is incorrect.",
        )
