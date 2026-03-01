"""Pydantic-схемы для сообщений: создание и формат ответа."""

from datetime import datetime

from sqlmodel import SQLModel


class MessageCreate(SQLModel):
    """Запрос на создание сообщения (используется в WebSocket)."""

    chat_id: int
    text: str


class MessageRead(SQLModel):
    """
    Формат сообщения в ответе API.
    is_read — вычисляемое поле: прочитано ли сообщение получателем(ями).
    """

    id: int
    chat_id: int
    sender_id: int | None
    text: str
    is_system: bool
    is_read: bool
    created_at: datetime
