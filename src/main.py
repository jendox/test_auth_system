from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from src import config, routes
from src.db.database import Database


@asynccontextmanager
async def lifespan(__: FastAPI) -> AsyncIterator[dict[str, Any]]:
    """
    Lifespan context manager for FastAPI application.

    Handles application startup and shutdown events, including
    database connection management and settings initialization.

    Yields:
        Dictionary containing application dependencies (settings, database)
    """
    settings = config.AppSettings.load()
    db = Database(settings.database.async_postgres_url)
    try:
        yield {
            "app_settings": settings,
            "db": db,
        }
    finally:
        await db.aclose()


app = FastAPI(
    title="Test Auth System for EM",
    description="""
        Custom Authentication and Authorization System

        A comprehensive backend application implementing a custom authentication
        and authorization system with the following features:

        ## User Management
        - User registration with email, name, and password
        - Login/logout functionality with session management
        - Profile updates and soft deletion (account deactivation)
        - JWT-based token authentication with refresh tokens

        ## Authorization System
        - Role-based access control (RBAC) with custom permission rules
        - Fine-grained permissions for business objects (CRUD operations)
        - Administrative API for managing access rules and user roles
        - Proper HTTP status codes (401 Unauthorized, 403 Forbidden)

        ## Security Features
        - Secure password hashing
        - JWT token validation with fingerprinting
        - Session management and revocation
        - Email confirmation for user verification

        ## Business Objects
        - Mock endpoints demonstrating access control to business resources
        - Permission-based resource access with owner restrictions

        The system provides a complete foundation for managing user identities
        and controlling access to application resources without relying on
        built-in framework authentication systems.
        """,
    lifespan=lifespan,
)

for router in routes.get_routers():
    app.include_router(router)
