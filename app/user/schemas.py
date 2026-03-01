"""Pydantic-схемы для пользователей: валидация входящих данных и формат ответов."""

from sqlmodel import SQLModel


class UserCreate(SQLModel):
    """Схема запроса на регистрацию нового пользователя."""

    email: str
    username: str
    password: str


class UserRead(SQLModel):
    """Схема ответа с публичными данными пользователя (без пароля)."""

    id: int
    email: str
    username: str