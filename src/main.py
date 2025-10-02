from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

import config
from src.db.database import Database
from src.routes import auth_router, user_router


@asynccontextmanager
async def lifespan(__: FastAPI) -> AsyncIterator[dict[str, Any]]:
    settings = config.AppSettings.load()
    db = Database(settings.database.url)
    try:
        yield {
            "app_settings": settings,
            "db": db,
        }
    finally:
        await db.aclose()


app = FastAPI(
    title="Test Auth System for EM",
    lifespan=lifespan,
)

app.include_router(user_router)
app.include_router(auth_router)
