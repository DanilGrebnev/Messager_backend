"""Роутер сообщений: получение истории чата с вычислением статуса прочтения."""

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.auth.utils import CurrentUser
from app.chat.models import ChatParticipant
from app.database import SessionDep
from app.message.models import Message
from app.message.schemas import MessageRead

router = APIRouter(prefix="/chats", tags=["Messages"])


@router.get("/{chat_id}/messages", response_model=list[MessageRead])
async def get_chat_messages(
    chat_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> list[MessageRead]:
    """
    Возвращает все сообщения чата с вычисленным полем is_read.
    Правила определения is_read:
    — Приватный чат (2 участника): сообщение прочитано, если
      last_read_message_id другого участника >= id сообщения.
    — Групповой чат: сообщение прочитано, если хотя бы один участник
      (кроме отправителя) имеет last_read_message_id >= id сообщения.
    — Системные сообщения всегда is_read = True.
    """
    # Проверяем, что текущий пользователь — участник чата
    participant = await session.execute(
        select(ChatParticipant).where(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.user_id == current_user.id,
        )
    )
    if participant.scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="You are not in this chat")

    # Загружаем всех участников с их позициями прочтения
    cp_result = await session.execute(
        select(ChatParticipant).where(ChatParticipant.chat_id == chat_id)
    )
    all_participants = cp_result.scalars().all()

    # Загружаем сообщения
    result = await session.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at)  # type: ignore[arg-type]
    )
    messages = result.scalars().all()

    is_private = len(all_participants) == 2

    output: list[MessageRead] = []
    for msg in messages:
        if msg.is_system:
            is_read = True
        elif is_private:
            # В приватном чате проверяем last_read_message_id другого участника
            other = next(
                (p for p in all_participants if p.user_id != msg.sender_id), None
            )
            is_read = (
                other is not None
                and other.last_read_message_id is not None
                and msg.id is not None
                and other.last_read_message_id >= msg.id
            )
        else:
            # В групповом чате — хотя бы один участник (кроме отправителя) прочитал
            is_read = any(
                p.last_read_message_id is not None
                and msg.id is not None
                and p.last_read_message_id >= msg.id
                for p in all_participants
                if p.user_id != msg.sender_id
            )

        output.append(
            MessageRead(
                id=msg.id,  # type: ignore[arg-type]
                chat_id=msg.chat_id,
                sender_id=msg.sender_id,
                text=msg.text,
                is_system=msg.is_system,
                is_read=is_read,
                created_at=msg.created_at,
            )
        )

    return output
