"""Роутер пользователей: регистрация, поиск и получение по ID."""

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from app.database import SessionDep
from app.user.models import User
from app.user.schemas import UserCreate, UserRead
from app.user.utils import PasswordService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/registration", response_model=UserRead)
async def create_user(
    user_data: UserCreate,
    session: SessionDep,
):
    """
    Регистрация нового пользователя.
    Хеширует пароль, сохраняет пользователя в БД и возвращает его публичные данные.
    """
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=PasswordService.hash_password(user_data.password),
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/search", response_model=list[UserRead])
async def search_users(
    session: SessionDep,
    q: str = Query(min_length=1),
    by: str = Query(default="username", pattern="^(username|email)$"),
):
    """
    Поиск пользователей по подстроке в username или email.
    Параметр `by` определяет поле для поиска.
    """
    column = User.username if by == "username" else User.email
    result = await session.execute(
        select(User).where(column.contains(q))  # type: ignore[union-attr]
    )
    return list(result.scalars().all())


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    session: SessionDep,
):
    """Получение пользователя по ID. Возвращает 404, если не найден."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


