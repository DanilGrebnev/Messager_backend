"""
Утилиты аутентификации: создание/валидация JWT-токенов и FastAPI-зависимость
для получения текущего пользователя из заголовка Authorization.
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.database import SessionDep
from app.user.models import User

# Схема извлечения токена из заголовка «Authorization: Bearer <token>»
security = HTTPBearer()

# Время жизни токенов
ACCESS_TOKEN_EXPIRE = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRE = timedelta(days=30)


class JWTService:
    """Сервис для работы с JWT: создание и декодирование access/refresh токенов."""

    @staticmethod
    def create_access_token(user_id: int) -> str:
        """
        Создаёт короткоживущий access-токен (15 мин).
        Payload содержит sub (user_id) и type="access".
        """
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRE,
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")  # type: ignore[reportUnknownMemberType]

    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """
        Создаёт долгоживущий refresh-токен (30 дней).
        Используется для получения новой пары токенов без повторного ввода пароля.
        """
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRE,
        }
        return jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm="HS256")  # type: ignore[reportUnknownMemberType]

    @staticmethod
    def decode_access_token(token: str) -> int | None:
        """
        Декодирует access-токен и возвращает user_id.
        Проверяет type="access" для защиты от подмены refresh-токеном.
        Возвращает None при любой ошибке валидации.
        """
        try:
            payload: dict[str, object] = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])  # type: ignore[reportUnknownMemberType]
            if payload.get("type") != "access":
                return None
            return int(str(payload["sub"]))
        except (jwt.InvalidTokenError, KeyError, ValueError):
            return None

    @staticmethod
    def decode_refresh_token(token: str) -> int | None:
        """
        Декодирует refresh-токен и возвращает user_id.
        Использует отдельный секретный ключ JWT_REFRESH_SECRET.
        """
        try:
            payload: dict[str, object] = jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=["HS256"])  # type: ignore[reportUnknownMemberType]
            if payload.get("type") != "refresh":
                return None
            return int(str(payload["sub"]))
        except (jwt.InvalidTokenError, KeyError, ValueError):
            return None


async def get_current_user(
    session: SessionDep,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    FastAPI-зависимость: извлекает access-токен из заголовка Authorization,
    декодирует его и возвращает объект User из БД.
    Бросает 401 если токен невалидный или пользователь не найден.
    """
    user_id = JWTService.decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# Аннотированный тип для инъекции текущего пользователя: current_user: CurrentUser
CurrentUser = Annotated[User, Depends(get_current_user)]
