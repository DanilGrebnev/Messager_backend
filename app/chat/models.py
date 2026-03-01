"""Модели таблиц chat и chatparticipant в базе данных."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Chat(SQLModel, table=True):
    """
    Чат (приватный или групповой).
    name = None для приватных чатов (имя вычисляется на клиенте).
    Для групповых чатов name задаётся при создании.
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None)
    )


class ChatParticipant(SQLModel, table=True):
    """
    Участник чата. Связывает пользователя с чатом.
    role: "admin" (создатель группового чата) или "member".
    last_read_message_id: ID последнего прочитанного сообщения —
    используется для подсчёта непрочитанных и отображения галочек.
    """

    id: int | None = Field(default=None, primary_key=True)
    chat_id: int = Field(foreign_key="chat.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    role: str = Field(default="member")
    last_read_message_id: int | None = Field(default=None)
