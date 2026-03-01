"""
Модуль подключения к базе данных.
Создаёт асинхронный движок SQLAlchemy и фабрику сессий.
Предоставляет FastAPI-зависимость SessionDep для инъекции сессии в эндпоинты.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Асинхронный движок — управляет пулом соединений к PostgreSQL
engine = create_async_engine(settings.db_url, echo=False)

# Фабрика сессий: каждый вызов async_session() создаёт новую сессию.
# expire_on_commit=False — объекты остаются доступны после commit без повторного запроса
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Генератор-зависимость для FastAPI.
    Открывает сессию БД на время обработки запроса и автоматически закрывает её.
    """
    async with async_session() as session:
        yield session


# Аннотированный тип для удобной инъекции сессии: session: SessionDep
SessionDep = Annotated[AsyncSession, Depends(get_session)]