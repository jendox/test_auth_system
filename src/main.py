from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from src import config, routes
from src.db.database import Database


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

for router in routes.get_routers():
    app.include_router(router)
