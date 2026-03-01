"""
Конфигурация приложения.
Загружает переменные окружения из .env файла через pydantic-settings
и предоставляет единый объект settings для всего приложения.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Класс настроек приложения. Все поля автоматически заполняются
    из переменных окружения (или .env файла). Если переменная
    отсутствует и нет значения по умолчанию — приложение не запустится.
    """

    # Параметры подключения к PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    # Секретные ключи для JWT-токенов (access и refresh)
    JWT_SECRET: str
    JWT_REFRESH_SECRET: str

    # URL подключения к Redis (используется для Pub/Sub в WebSocket)
    REDIS_URL: str

    @property
    def db_url(self) -> str:
        """Формирует строку подключения к PostgreSQL для asyncpg-драйвера."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


# Единственный экземпляр настроек, импортируется во всех модулях
settings = Settings()  # type: ignore[call-arg]
