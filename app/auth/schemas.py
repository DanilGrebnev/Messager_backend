"""Pydantic-схемы для аутентификации: запросы на вход, обновление токенов и ответ с токенами."""

from sqlmodel import SQLModel


class LoginRequest(SQLModel):
    """Запрос на вход: email и пароль."""

    email: str
    password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "grebnevdanil60@gmail.com",
                    "password": "htczte2101",
                }
            ]
        }
    }


class TokenResponse(SQLModel):
    """Ответ с парой JWT-токенов: access (короткоживущий) и refresh (долгоживущий)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(SQLModel):
    """Запрос на обновление пары токенов с помощью действующего refresh_token."""

    refresh_token: str