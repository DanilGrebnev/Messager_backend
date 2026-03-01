"""
Менеджер WebSocket-соединений с Redis Pub/Sub.
Обеспечивает доставку сообщений в реальном времени.
Redis используется как шина между серверами — при масштабировании
на несколько экземпляров Uvicorn сообщения дойдут до всех пользователей.
"""

import json

from fastapi import WebSocket
from redis.asyncio import Redis

from app.config import settings


class ConnectionManager:
    """
    Управляет активными WebSocket-соединениями пользователей.
    Каждый пользователь подписывается на свой Redis-канал "user:{id}".
    Отправка сообщений идёт через Redis publish, а не напрямую в сокет,
    что делает систему горизонтально масштабируемой.
    """

    def __init__(self) -> None:
        self.active_connections: dict[int, WebSocket] = {}
        self.pubsubs: dict[int, object] = {}
        self.redis: Redis = Redis.from_url(settings.REDIS_URL)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """
        Принимает WebSocket-соединение, сохраняет его и подписывает
        пользователя на персональный Redis-канал для получения сообщений.
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        pubsub = self.redis.pubsub()  # type: ignore[reportUnknownMemberType]
        await pubsub.subscribe(f"user:{user_id}")
        self.pubsubs[user_id] = pubsub

    async def disconnect(self, user_id: int) -> None:
        """Удаляет соединение и отписывается от Redis-канала."""
        self.active_connections.pop(user_id, None)
        pubsub = self.pubsubs.pop(user_id, None)
        if pubsub:
            await pubsub.unsubscribe(f"user:{user_id}")  # type: ignore[reportUnknownMemberType]
            await pubsub.close()  # type: ignore[reportUnknownMemberType]

    async def send_to_user(self, user_id: int, message: dict[str, object]) -> None:
        """Публикует сообщение в Redis-канал конкретного пользователя."""
        await self.redis.publish(f"user:{user_id}", json.dumps(message, default=str))

    async def send_to_chat(
        self,
        participant_ids: list[int],
        sender_id: int | None,
        message: dict[str, object],
    ) -> None:
        """
        Рассылает сообщение всем участникам чата, кроме отправителя.
        Используется как для обычных сообщений, так и для событий (read_update).
        """
        for uid in participant_ids:
            if uid != sender_id:
                await self.send_to_user(uid, message)

    async def listen(self, user_id: int) -> None:
        """
        Фоновая задача: слушает Redis-канал пользователя и пересылает
        входящие сообщения в его WebSocket-соединение.
        Работает до тех пор, пока соединение активно.
        """
        pubsub = self.pubsubs.get(user_id)
        if not pubsub:
            return
        async for raw_message in pubsub.listen():  # type: ignore[reportUnknownMemberType]
            if raw_message["type"] == "message":  # type: ignore[reportUnknownMemberType]
                ws = self.active_connections.get(user_id)
                if ws:
                    data = json.loads(raw_message["data"])  # type: ignore[reportUnknownMemberType]
                    await ws.send_json(data)


# Глобальный экземпляр менеджера — используется во всём приложении
manager = ConnectionManager()
