from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from app.api.admin import router as admin_router
from app.api.read import router as read_router
from app.api.ui import router as ui_router
from app.core.config import settings
from app.core.logging import init_logging
from app.db.sqlite_persistence import start_sqlite_persistence, stop_sqlite_persistence


init_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_sqlite_persistence()
    try:
        yield
    finally:
        stop_sqlite_persistence()


app = FastAPI(title=settings.api_title, version="1.0.0", lifespan=lifespan)

app.include_router(read_router)
app.include_router(admin_router)
app.include_router(ui_router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
