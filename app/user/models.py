"""Модель таблицы users в базе данных."""

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    Пользователь приложения.
    Хранит учётные данные: логин, email и хеш пароля.
    """

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    hashed_password: str