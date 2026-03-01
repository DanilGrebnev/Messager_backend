"""Модель таблицы message в базе данных."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Message(SQLModel, table=True):
    """
    Сообщение в чате.
    sender_id = None для системных сообщений (вход/выход участников).
    is_system — флаг для отличия системных сообщений от пользовательских.
    """

    id: int | None = Field(default=None, primary_key=True)
    chat_id: int = Field(foreign_key="chat.id", index=True)
    sender_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    text: str
    is_system: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )
