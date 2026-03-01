"""
WebSocket-эндпоинт для обмена сообщениями в реальном времени.
Поддерживает два типа входящих событий:
— отправка сообщения: { chat_id, text }
— отметка прочтения: { type: "read", chat_id, message_id }
"""

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import select

from app.auth.utils import JWTService
from app.chat.models import ChatParticipant
from app.database import async_session
from app.message.manager import manager
from app.message.models import Message

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str) -> None:
    """
    Основной WebSocket-хендлер.
    1. Аутентификация через JWT-токен из query-параметра.
    2. Регистрация соединения в ConnectionManager.
    3. Запуск фоновой задачи listen() для приёма сообщений из Redis.
    4. Цикл обработки входящих JSON-сообщений от клиента.
    """
    user_id = JWTService.decode_access_token(token)
    if user_id is None:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await manager.connect(user_id, websocket)
    listen_task = asyncio.create_task(manager.listen(user_id))

    try:
        while True:
            data = await websocket.receive_json()

            # Обработка события "прочитано" — обновляем БД и рассылаем read_update
            if data.get("type") == "read":
                chat_id = data.get("chat_id")
                message_id = data.get("message_id")
                if not chat_id or not message_id:
                    continue

                async with async_session() as session:
                    cp_result = await session.execute(
                        select(ChatParticipant).where(
                            ChatParticipant.chat_id == chat_id,
                            ChatParticipant.user_id == user_id,
                        )
                    )
                    cp = cp_result.scalar_one_or_none()
                    if cp is None:
                        continue

                    # Обновляем только вперёд (нельзя уменьшить)
                    if cp.last_read_message_id is None or message_id > cp.last_read_message_id:
                        cp.last_read_message_id = message_id
                        session.add(cp)
                        await session.commit()

                    # Рассылаем read_update другим участникам чата
                    p_result = await session.execute(
                        select(ChatParticipant.user_id).where(
                            ChatParticipant.chat_id == chat_id
                        )
                    )
                    participant_ids = [row[0] for row in p_result.all()]

                await manager.send_to_chat(
                    participant_ids=participant_ids,
                    sender_id=user_id,
                    message={
                        "type": "read_update",
                        "chat_id": chat_id,
                        "user_id": user_id,
                        "last_read_message_id": message_id,
                    },
                )
                continue

            # Обработка обычного сообщения
            chat_id = data.get("chat_id")
            text = data.get("text")

            if not chat_id or not text:
                await websocket.send_json({"error": "chat_id and text are required"})
                continue

            async with async_session() as session:
                # Проверяем, что отправитель — участник чата
                participant = await session.execute(
                    select(ChatParticipant).where(
                        ChatParticipant.chat_id == chat_id,
                        ChatParticipant.user_id == user_id,
                    )
                )
                if participant.scalar_one_or_none() is None:
                    await websocket.send_json({"error": "You are not in this chat"})
                    continue

                # Сохраняем сообщение в БД
                message = Message(
                    chat_id=chat_id,
                    sender_id=user_id,
                    text=text,
                )
                session.add(message)
                await session.commit()
                await session.refresh(message)

                # Получаем список участников для рассылки
                participants_result = await session.execute(
                    select(ChatParticipant.user_id).where(
                        ChatParticipant.chat_id == chat_id
                    )
                )
                participant_ids = [row[0] for row in participants_result.all()]

            msg_data = {
                "id": message.id,
                "chat_id": message.chat_id,
                "sender_id": message.sender_id,
                "text": message.text,
                "is_system": False,
                "created_at": message.created_at,
            }

            # Рассылаем сообщение всем участникам кроме отправителя
            await manager.send_to_chat(
                participant_ids=participant_ids,
                sender_id=user_id,
                message=msg_data,
            )

            # Подтверждаем отправителю
            await websocket.send_json({"status": "sent", "message_id": message.id})

    except WebSocketDisconnect:
        pass
    finally:
        listen_task.cancel()
        await manager.disconnect(user_id)
