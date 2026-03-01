"""Роутер аутентификации: вход по email/пароль и обновление JWT-токенов."""

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.auth.schemas import LoginRequest, RefreshRequest, TokenResponse
from app.auth.utils import JWTService
from app.database import SessionDep
from app.user.models import User
from app.user.utils import PasswordService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    session: SessionDep,
) -> TokenResponse:
    """
    Вход в систему по email и паролю.
    Ищет пользователя по email, проверяет пароль через bcrypt
    и возвращает пару access + refresh токенов.
    """
    result = await session.execute(select(User).where(User.email == login_data.email))
    user = result.scalars().first()

    if user is None or not PasswordService.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    return TokenResponse(
        access_token=JWTService.create_access_token(user.id),  # type: ignore[arg-type]
        refresh_token=JWTService.create_refresh_token(user.id),  # type: ignore[arg-type]
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    session: SessionDep,
) -> TokenResponse:
    """
    Обновление пары токенов по действующему refresh-токену.
    Позволяет клиенту оставаться авторизованным без повторного ввода пароля.
    Выдаёт новый access + новый refresh (ротация токенов).
    """
    user_id = JWTService.decode_refresh_token(data.refresh_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return TokenResponse(
        access_token=JWTService.create_access_token(user.id),  # type: ignore[arg-type]
        refresh_token=JWTService.create_refresh_token(user.id),  # type: ignore[arg-type]
    )