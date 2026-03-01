# Messager

Мессенджер с поддержкой приватных и групповых чатов, WebSocket-сообщениями в реальном времени и JWT-аутентификацией.

## Стек

- **Backend:** FastAPI, SQLAlchemy (asyncpg), SQLModel, Alembic
- **БД:** PostgreSQL 17
- **Кэш/Pub-Sub:** Redis 7
- **Auth:** JWT (PyJWT), bcrypt
- **Пакетный менеджер:** uv

## Запуск (production)

Полный стек в Docker — БД, Redis и backend:

```bash
docker compose up
```

Если изменился код — пересобрать образ:

```bash
docker compose up --build
```

Приложение будет доступно на `http://localhost:8000`.

## Запуск (разработка)

1. Поднять инфраструктуру (Postgres, pgAdmin, Redis):

```bash
docker compose -f docker-compose.dev.yml up
```

2. Установить зависимости:

```bash
uv sync
```

3. Запустить приложение (миграции применяются автоматически при старте):

```bash
uv run uvicorn app.main:app --reload
```

Приложение будет доступно на `http://localhost:8000`.

## Переменные окружения

Создайте файл `.env` в корне проекта:

```env
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=messager_db

PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin

JWT_SECRET=super_secret_key
JWT_REFRESH_SECRET=super_refresh_secret_key

REDIS_URL=redis://localhost:6379
```

## Сервисы

| Сервис   | URL                     |
| -------- | ----------------------- |
| API      | http://localhost:8000    |
| Swagger  | http://localhost:8000/docs |
| pgAdmin  | http://localhost:5050    |
