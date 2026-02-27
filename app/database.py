from collections.abc import AsyncGenerator 
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import Annotated
from fastapi import Depends

from app.config import settings

engine = create_async_engine(settings.db_url, echo=True)

async_session = async_sessionmaker(engine, 
    class_=AsyncSession, 
    expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]