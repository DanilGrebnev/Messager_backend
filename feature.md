# Messager — реализованные фичи

## Инфраструктура
- Docker Compose: PostgreSQL, pgAdmin, Redis
- Конфигурация через `.env` + pydantic-settings
- Асинхронное подключение к БД (asyncpg + SQLAlchemy)
- Alembic для миграций БД
- Pyright (strict mode) для статической типизации
- UV как пакетный менеджер
- CORS middleware для клиентского доступа

## Пользователи (`app/user/`)
- Модель `User`: id, username, email, hashed_password
- `POST /users/registration` — регистрация с хешированием пароля (bcrypt)
- `GET /users/{user_id}` — получение пользователя по id
- `GET /users/search?q=...&by=username|email` — поиск пользователей

## Аутентификация (`app/auth/`)
- JWT-токены (PyJWT): access (15 мин) + refresh (30 дней)
- `POST /auth/login` — вход по email + пароль, возвращает access_token + refresh_token
- `POST /auth/refresh` — обновление пары токенов по refresh_token
- Dependency `get_current_user` / `CurrentUser` — защита эндпоинтов
- Автологин при перезагрузке страницы через refresh token (localStorage)

## Чаты (`app/chat/`)
- Модель `Chat`: id, name, created_at
- Модель `ChatParticipant`: id, chat_id, user_id, role (admin/member), last_read_message_id
- `GET /chats` — список всех чатов текущего пользователя с участниками и счётчиком непрочитанных (unread_count)
- `POST /chats` — создание чата:
  - Личный (1 user_id) — дедупликация, оба участника member
  - Групповой (2+ user_ids) — создатель = admin, автоимя "Чат {username}"
- `PATCH /chats/{chat_id}` — изменение названия (только admin)
- `POST /chats/{chat_id}/members` — добавление участника (только admin)
- `DELETE /chats/{chat_id}/members/{user_id}` — удаление участника (только admin)
- `POST /chats/{chat_id}/leave` — выход из чата (member)
- `POST /chats/{chat_id}/read` — отметка сообщений как прочитанных + рассылка read_update через WS

## Сообщения (`app/message/`)
- Модель `Message`: id, chat_id, sender_id, text, is_system, created_at
- `GET /chats/{chat_id}/messages` — история сообщений чата с вычисленным полем `is_read`:
  - Приватный чат: прочитано = `last_read_message_id` собеседника >= id сообщения
  - Групповой чат: прочитано = хотя бы один участник (кроме отправителя) прочитал
- Системные сообщения (is_system=True, sender_id=null):
  - "{username} покинул чат"
  - "Пользователь {username} удалён из чата"
  - "{username} добавлен в чат"

## Real-time (WebSocket + Redis)
- WebSocket endpoint `/ws?token=...`
- Redis Pub/Sub для доставки сообщений между серверами
- Персональный PubSub-канал для каждого пользователя
- `ConnectionManager`: управление подключениями, `send_to_chat` рассылает всем участникам
- Клиент отправляет `{chat_id, text}`, сервер сохраняет в БД и рассылает
- Событие `read_update`: отправляется при прочтении сообщений, обновляет галочки у отправителя в реальном времени
- Поддержка двух типов WS-событий: отправка сообщения и отметка прочтения

## Клиент (`client/index.html`)
- React (CDN) — одностраничное приложение
- Авторизация: вход / регистрация
- Автологин при перезагрузке (refresh token в localStorage)
- Кнопка «Выход» для выхода из аккаунта
- Сайдбар: список чатов, поиск пользователей (по имени / email)
- Кнопка создания группового чата (модальное окно с выбором контактов)
- В приватных чатах не показывается количество участников
- Индикатор непрочитанных сообщений (badge) на каждом чате в сайдбаре
- Чат: история сообщений, отправка в реальном времени
- Галочки прочтения на отправленных сообщениях: ✓ (отправлено), ✓✓ (прочитано, зелёные)
- Автоматическая отметка прочтения при открытии чата и получении сообщений в активном чате
- Обновление галочек в реальном времени через WS-событие read_update
- Системные сообщения отображаются курсивом по центру
- В групповых чатах отображается имя отправителя
- Автозагрузка чатов при логине из БД
- Подробные комментарии ко всей логике (JS и Python)
