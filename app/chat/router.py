"""
Роутер чатов: CRUD операции, управление участниками,
отметка прочтения и отправка системных сообщений.
"""

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.auth.utils import CurrentUser
from app.chat.models import Chat, ChatParticipant
from app.chat.schemas import (
    AddMember,
    ChatCreate,
    ChatRead,
    ChatUpdate,
    MarkRead,
    ParticipantRead,
)
from app.database import SessionDep
from app.message.manager import manager
from app.message.models import Message
from app.user.models import User
from app.user.schemas import UserRead

router = APIRouter(prefix="/chats", tags=["Chats"])


async def _build_chat_read(
    session: SessionDep, chat: Chat, current_user_id: int
) -> ChatRead:
    """
    Собирает полный ответ ChatRead для одного чата:
    — список участников с их last_read_message_id
    — количество непрочитанных сообщений для current_user
    """
    result = await session.execute(
        select(ChatParticipant, User)
        .join(User, col(ChatParticipant.user_id) == col(User.id))
        .where(ChatParticipant.chat_id == chat.id)
    )
    rows = result.all()

    # Собираем участников и находим last_read_message_id текущего пользователя
    participants: list[ParticipantRead] = []
    my_last_read: int | None = None
    for cp, user in rows:
        participants.append(
            ParticipantRead(
                user=UserRead(id=user.id, email=user.email, username=user.username),  # type: ignore[arg-type]
                role=cp.role,
                last_read_message_id=cp.last_read_message_id,
            )
        )
        if user.id == current_user_id:
            my_last_read = cp.last_read_message_id

    # Считаем непрочитанные: сообщения с id > last_read_message_id (или все, если null)
    if my_last_read is not None:
        count_result = await session.execute(
            select(func.count()).select_from(Message).where(
                Message.chat_id == chat.id,
                col(Message.id) > my_last_read,
            )
        )
    else:
        count_result = await session.execute(
            select(func.count()).select_from(Message).where(
                Message.chat_id == chat.id,
            )
        )
    unread_count: int = count_result.scalar_one()

    return ChatRead(
        id=chat.id,  # type: ignore[arg-type]
        name=chat.name,
        created_at=chat.created_at,
        participants=participants,
        unread_count=unread_count,
    )


async def _get_participant(
    session: SessionDep, chat_id: int, user_id: int
) -> ChatParticipant | None:
    """Ищет запись участника по chat_id + user_id. Возвращает None если не найден."""
    result = await session.execute(
        select(ChatParticipant).where(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def _require_admin(
    session: SessionDep, chat_id: int, user_id: int
) -> ChatParticipant:
    """Проверяет, что пользователь является админом чата. Иначе — 403."""
    cp = await _get_participant(session, chat_id, user_id)
    if cp is None:
        raise HTTPException(status_code=403, detail="You are not in this chat")
    if cp.role != "admin":
        raise HTTPException(status_code=403, detail="Admin rights required")
    return cp


async def _send_system_message(
    session: SessionDep, chat_id: int, text: str
) -> Message:
    """
    Создаёт системное сообщение (например, "пользователь покинул чат"),
    сохраняет в БД и рассылает всем участникам через WebSocket.
    """
    msg = Message(chat_id=chat_id, sender_id=None, text=text, is_system=True)
    session.add(msg)
    await session.commit()
    await session.refresh(msg)

    participants_result = await session.execute(
        select(ChatParticipant.user_id).where(ChatParticipant.chat_id == chat_id)
    )
    participant_ids = [row[0] for row in participants_result.all()]
    await manager.send_to_chat(
        participant_ids=participant_ids,
        sender_id=None,
        message={
            "id": msg.id,
            "chat_id": chat_id,
            "sender_id": None,
            "text": text,
            "is_system": True,
            "created_at": msg.created_at,
        },
    )
    return msg


@router.get("", response_model=list[ChatRead])
async def get_my_chats(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[ChatRead]:
    """Возвращает все чаты текущего пользователя с участниками и счётчиком непрочитанных."""
    my_chat_ids_result = await session.execute(
        select(ChatParticipant.chat_id).where(
            ChatParticipant.user_id == current_user.id
        )
    )
    chat_ids = [row[0] for row in my_chat_ids_result.all()]
    if not chat_ids:
        return []

    chats_result = await session.execute(
        select(Chat).where(col(Chat.id).in_(chat_ids))
    )
    chats = chats_result.scalars().all()

    result: list[ChatRead] = []
    for chat in chats:
        result.append(await _build_chat_read(session, chat, current_user.id))  # type: ignore[arg-type]
    return result


@router.post("", response_model=ChatRead)
async def create_chat(
    data: ChatCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ChatRead:
    """
    Создание нового чата.
    Для приватного чата (2 участника, без имени) — проверяет существование,
    чтобы не создавать дубликаты. Для группового чата создатель получает роль admin.
    """
    if not data.user_ids:
        raise HTTPException(status_code=400, detail="user_ids must not be empty")

    all_user_ids = list(set(data.user_ids + [current_user.id]))  # type: ignore[operator]
    is_private = len(all_user_ids) == 2 and data.name is None

    # Для приватного чата ищем существующий чат между этими двумя пользователями
    if is_private:
        other_id = [uid for uid in all_user_ids if uid != current_user.id][0]
        existing = await session.execute(
            select(ChatParticipant.chat_id)
            .where(ChatParticipant.user_id == current_user.id)
        )
        my_chat_ids = {row[0] for row in existing.all()}

        if my_chat_ids:
            other_in = await session.execute(
                select(ChatParticipant.chat_id).where(
                    col(ChatParticipant.chat_id).in_(my_chat_ids),
                    ChatParticipant.user_id == other_id,
                )
            )
            shared = other_in.scalars().all()

            # Проверяем, что общий чат именно приватный (2 участника, без имени)
            for cid in shared:
                count_result = await session.execute(
                    select(ChatParticipant).where(ChatParticipant.chat_id == cid)
                )
                if len(count_result.all()) == 2:
                    chat = await session.get(Chat, cid)
                    if chat and chat.name is None:
                        return await _build_chat_read(session, chat, current_user.id)  # type: ignore[arg-type]

    # Имя группового чата по умолчанию — "Чат {username создателя}"
    name = data.name
    if not is_private and name is None:
        name = f"Чат {current_user.username}"

    chat = Chat(name=name)
    session.add(chat)
    await session.commit()
    await session.refresh(chat)

    for uid in all_user_ids:
        role = "admin" if uid == current_user.id and not is_private else "member"
        session.add(ChatParticipant(chat_id=chat.id, user_id=uid, role=role))  # type: ignore[arg-type]
    await session.commit()

    return await _build_chat_read(session, chat, current_user.id)  # type: ignore[arg-type]


@router.patch("/{chat_id}", response_model=ChatRead)
async def update_chat(
    chat_id: int,
    data: ChatUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ChatRead:
    """Обновление названия чата. Доступно только админу."""
    await _require_admin(session, chat_id, current_user.id)  # type: ignore[arg-type]
    chat = await session.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    chat.name = data.name
    await session.commit()
    await session.refresh(chat)
    return await _build_chat_read(session, chat, current_user.id)  # type: ignore[arg-type]


@router.post("/{chat_id}/members", response_model=ChatRead)
async def add_member(
    chat_id: int,
    data: AddMember,
    session: SessionDep,
    current_user: CurrentUser,
) -> ChatRead:
    """Добавление участника в чат. Доступно только админу. Рассылает системное сообщение."""
    await _require_admin(session, chat_id, current_user.id)  # type: ignore[arg-type]

    existing = await _get_participant(session, chat_id, data.user_id)
    if existing:
        raise HTTPException(status_code=400, detail="User already in chat")

    user = await session.get(User, data.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    session.add(ChatParticipant(chat_id=chat_id, user_id=data.user_id, role="member"))
    await session.commit()

    await _send_system_message(
        session, chat_id, f"{user.username} добавлен в чат"
    )

    chat = await session.get(Chat, chat_id)
    return await _build_chat_read(session, chat, current_user.id)  # type: ignore[arg-type]


@router.delete("/{chat_id}/members/{user_id}", response_model=ChatRead)
async def remove_member(
    chat_id: int,
    user_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> ChatRead:
    """Удаление участника из чата. Доступно только админу. Админ не может удалить себя."""
    await _require_admin(session, chat_id, current_user.id)  # type: ignore[arg-type]

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Admin cannot remove themselves")

    cp = await _get_participant(session, chat_id, user_id)
    if cp is None:
        raise HTTPException(status_code=404, detail="User not in chat")

    user = await session.get(User, user_id)
    username = user.username if user else "Unknown"

    await session.delete(cp)
    await session.commit()

    await _send_system_message(
        session, chat_id, f"Пользователь {username} удалён из чата"
    )

    chat = await session.get(Chat, chat_id)
    return await _build_chat_read(session, chat, current_user.id)  # type: ignore[arg-type]


@router.post("/{chat_id}/leave")
async def leave_chat(
    chat_id: int,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict[str, str]:
    """Выход из чата. Админ не может покинуть чат (нужно передать права)."""
    cp = await _get_participant(session, chat_id, current_user.id)  # type: ignore[arg-type]
    if cp is None:
        raise HTTPException(status_code=404, detail="You are not in this chat")

    if cp.role == "admin":
        raise HTTPException(
            status_code=400,
            detail="Admin cannot leave. Transfer admin rights first.",
        )

    await session.delete(cp)
    await session.commit()

    await _send_system_message(
        session, chat_id, f"Пользователь {current_user.username} покинул чат"
    )

    return {"status": "ok"}


@router.post("/{chat_id}/read")
async def mark_chat_read(
    chat_id: int,
    data: MarkRead,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict[str, str]:
    """
    Отметка сообщений как прочитанных.
    Обновляет last_read_message_id участника (только вперёд — нельзя уменьшить).
    Рассылает событие read_update остальным участникам через WebSocket,
    чтобы у них обновились галочки на сообщениях.
    """
    cp = await _get_participant(session, chat_id, current_user.id)  # type: ignore[arg-type]
    if cp is None:
        raise HTTPException(status_code=403, detail="You are not in this chat")

    # Обновляем только если новое значение больше текущего
    if cp.last_read_message_id is None or data.message_id > cp.last_read_message_id:
        cp.last_read_message_id = data.message_id
        session.add(cp)
        await session.commit()

    # Оповещаем других участников о прочтении
    participants_result = await session.execute(
        select(ChatParticipant.user_id).where(ChatParticipant.chat_id == chat_id)
    )
    participant_ids = [row[0] for row in participants_result.all()]

    await manager.send_to_chat(
        participant_ids=participant_ids,
        sender_id=current_user.id,  # type: ignore[arg-type]
        message={
            "type": "read_update",
            "chat_id": chat_id,
            "user_id": current_user.id,
            "last_read_message_id": data.message_id,
        },
    )

    return {"status": "ok"}
