"""
Точка входа FastAPI-приложения.
Здесь создаётся экземпляр приложения, подключаются middleware и все роутеры.
"""

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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Автоматический запуск миграций Alembic при старте приложения."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    yield


app = FastAPI(title="Messager API", lifespan=lifespan)

# CORS — разрешаем запросы с любого домена (для разработки).
# В production стоит указать конкретные origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров: каждый модуль регистрирует свои эндпоинты
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(message_router)
app.include_router(ws_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Health-check эндпоинт для проверки работоспособности сервера."""
    return {"status": "ok"}