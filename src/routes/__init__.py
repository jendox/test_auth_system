from .admin import router as admin_router
from .auth import router as auth_router
from .mock import router as mock_router
from .users import router as user_router

__all__ = ("get_routers",)


def get_routers():
    return admin_router, auth_router, mock_router, user_router
