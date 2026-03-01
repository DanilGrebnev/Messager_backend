"""
Точка входа FastAPI-приложения.
Здесь создаётся экземпляр приложения, подключаются middleware и все роутеры.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routers import router as auth_router
from app.chat.router import router as chat_router
from app.message.router import router as message_router
from app.message.websocket import router as ws_router
from app.user.routers import router as user_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Автоматический запуск миграций Alembic при старте приложения."""
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
    except Exception:
        logger.exception("Alembic migration failed")
    yield


app = FastAPI(title="Messager API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

api_prefix = "/api"
app.include_router(user_router, prefix=api_prefix)
app.include_router(auth_router, prefix=api_prefix)
app.include_router(chat_router, prefix=api_prefix)
app.include_router(message_router, prefix=api_prefix)
app.include_router(ws_router, prefix=api_prefix)


@app.get("/")
async def root() -> dict[str, str]:
    """Health-check эндпоинт для проверки работоспособности сервера."""
    return {"status": "ok"}