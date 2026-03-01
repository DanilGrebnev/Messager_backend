"""Pydantic-схемы для чатов: создание, обновление, ответы и управление участниками."""

from datetime import datetime

from sqlmodel import SQLModel

from app.user.schemas import UserRead


class ChatCreate(SQLModel):
    """Запрос на создание чата. user_ids — список ID приглашаемых пользователей."""

    user_ids: list[int]
    name: str | None = None


class ChatUpdate(SQLModel):
    """Запрос на обновление названия чата (только для админа)."""

    name: str


class AddMember(SQLModel):
    """Запрос на добавление участника в чат."""

    user_id: int


class MarkRead(SQLModel):
    """Запрос на отметку сообщений как прочитанных до указанного message_id."""

    message_id: int


class ParticipantRead(SQLModel):
    """
    Данные участника чата в ответе API.
    Включает last_read_message_id для вычисления статуса прочтения на клиенте.
    """

    user: UserRead
    role: str
    last_read_message_id: int | None


class ChatRead(SQLModel):
    """
    Полные данные чата в ответе API.
    unread_count — количество непрочитанных сообщений для текущего пользователя.
    """

    id: int
    name: str | None
    created_at: datetime
    participants: list[ParticipantRead]
    unread_count: int
