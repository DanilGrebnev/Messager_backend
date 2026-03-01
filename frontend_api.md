# Frontend API

Базовый URL: `http://localhost:8000`

Все защищённые эндпоинты требуют заголовок:

```
Authorization: Bearer <access_token>
```

---

## Auth

### POST /auth/login

Вход в систему. Возвращает пару JWT-токенов.

**Тело запроса:**

```json
{
  "email": "user@example.com",
  "password": "mypassword"
}
```

**Ответ 200:**

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Ошибки:** `400` — неверный email или пароль.

---

### POST /auth/refresh

Обновление пары токенов по действующему refresh-токену (ротация).

**Тело запроса:**

```json
{
  "refresh_token": "eyJ..."
}
```

**Ответ 200:**

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Ошибки:** `401` — невалидный refresh-токен или пользователь не найден.

---

## User

### POST /users/registration

Регистрация нового пользователя. Авторизация **не требуется**.

**Тело запроса:**

```json
{
  "email": "user@example.com",
  "username": "john",
  "password": "mypassword"
}
```

**Ответ 200:**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john"
}
```

---

### GET /users/check-email?email={email}

Проверка уникальности email. Авторизация **не требуется**.

| Параметр | Тип    | Обязательный | Описание            |
| -------- | ------ | ------------ | ------------------- |
| `email`  | string | да           | Email для проверки  |

**Ответ 200:**

```json
{ "is_unique": true }
```

`is_unique: true` — email свободен, `false` — уже занят.

---

### GET /users/search?q={query}&by={field}

Поиск пользователей по подстроке. Авторизация **не требуется**.

| Параметр | Тип    | Обязательный | Описание                                       |
| -------- | ------ | ------------ | ---------------------------------------------- |
| `q`      | string | да           | Подстрока для поиска (минимум 1 символ)        |
| `by`     | string | нет          | Поле поиска: `username` (по умолчанию) или `email` |

**Ответ 200:**

```json
[
  { "id": 1, "email": "user@example.com", "username": "john" },
  { "id": 2, "email": "john2@example.com", "username": "johnny" }
]
```

---

### GET /users/{user_id}

Получение пользователя по ID. Авторизация **не требуется**.

**Ответ 200:**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john"
}
```

**Ошибки:** `404` — пользователь не найден.

---

## Chat

> Все эндпоинты чатов требуют **авторизацию** (заголовок `Authorization: Bearer <access_token>`).

### GET /chats

Список всех чатов текущего пользователя.

**Ответ 200:**

```json
[
  {
    "id": 1,
    "name": null,
    "created_at": "2026-03-01T12:00:00",
    "participants": [
      {
        "user": { "id": 1, "email": "a@example.com", "username": "alice" },
        "role": "member",
        "last_read_message_id": 42
      },
      {
        "user": { "id": 2, "email": "b@example.com", "username": "bob" },
        "role": "member",
        "last_read_message_id": 40
      }
    ],
    "unread_count": 3
  }
]
```

- `name: null` — приватный чат (имя отображать как username собеседника).
- `unread_count` — количество непрочитанных сообщений для текущего пользователя.

---

### POST /chats

Создание чата.

**Тело запроса:**

```json
{
  "user_ids": [2],
  "name": null
}
```

| Поле       | Тип        | Описание                                                                 |
| ---------- | ---------- | ------------------------------------------------------------------------ |
| `user_ids` | int[]      | ID пользователей (текущий добавляется автоматически)                     |
| `name`     | string\|null | `null` для приватного чата, строка для группового (или авто-имя если не задано) |

**Логика:**
- 1 user_id + name=null → **приватный** чат (дедупликация — если уже существует, вернётся существующий).
- 2+ user_ids или name задан → **групповой** чат (создатель = admin).

**Ответ 200:** объект `ChatRead` (как в GET /chats).

**Ошибки:** `400` — пустой `user_ids`.

---

### PATCH /chats/{chat_id}

Обновление названия чата. Только **admin**.

**Тело запроса:**

```json
{
  "name": "Новое название"
}
```

**Ответ 200:** объект `ChatRead`.

**Ошибки:** `403` — не участник или не admin. `404` — чат не найден.

---

### POST /chats/{chat_id}/members

Добавление участника. Только **admin**.

**Тело запроса:**

```json
{
  "user_id": 5
}
```

**Ответ 200:** объект `ChatRead` (обновлённый список участников).

**Ошибки:** `400` — пользователь уже в чате. `403` — не admin. `404` — пользователь не найден.

---

### DELETE /chats/{chat_id}/members/{user_id}

Удаление участника из чата. Только **admin**. Админ не может удалить себя.

**Ответ 200:** объект `ChatRead`.

**Ошибки:** `400` — попытка удалить себя (admin). `403` — не admin. `404` — участник не найден.

---

### POST /chats/{chat_id}/leave

Выход текущего пользователя из чата. Админ **не может** покинуть чат.

**Тело запроса:** отсутствует.

**Ответ 200:**

```json
{ "status": "ok" }
```

**Ошибки:** `400` — admin не может выйти. `404` — не участник.

---

### POST /chats/{chat_id}/read

Отметка сообщений как прочитанных. Обновляет позицию только вперёд.

**Тело запроса:**

```json
{
  "message_id": 42
}
```

**Ответ 200:**

```json
{ "status": "ok" }
```

Побочный эффект: рассылает `read_update` другим участникам через WebSocket.

**Ошибки:** `403` — не участник.

---

## Message

> Требуется **авторизация**.

### Как работают сообщения — сводка для фронтенда

| Действие | Способ | Описание |
| -------- | ------ | -------- |
| Загрузить историю | `GET /chats/{chat_id}/messages` | HTTP-запрос, возвращает все сообщения с полем `is_read` |
| Отправить сообщение | WebSocket `{ chat_id, text }` | Отправитель получает `{ status: "sent", message_id }` |
| Получить новое сообщение | WebSocket (входящее) | Приходит `{ id, chat_id, sender_id, text, is_system, created_at }` |
| Отметить прочитанным | WebSocket `{ type: "read", chat_id, message_id }` | Обновляет позицию прочтения в БД |
| Узнать о прочтении | WebSocket (входящее) | Приходит `{ type: "read_update", chat_id, user_id, last_read_message_id }` |
| Системное сообщение | WebSocket (входящее) | Приходит `{ id, chat_id, sender_id: null, text, is_system: true, created_at }` |

Подробные форматы WebSocket-событий — в разделе [WebSocket](#websocket) ниже.

---

### GET /chats/{chat_id}/messages

История сообщений чата (отсортировано по `created_at`).

**Ответ 200:**

```json
[
  {
    "id": 1,
    "chat_id": 1,
    "sender_id": 2,
    "text": "Привет!",
    "is_system": false,
    "is_read": true,
    "created_at": "2026-03-01T12:00:00"
  },
  {
    "id": 2,
    "chat_id": 1,
    "sender_id": null,
    "text": "alice добавлен в чат",
    "is_system": true,
    "is_read": true,
    "created_at": "2026-03-01T12:01:00"
  }
]
```

- `sender_id: null` + `is_system: true` — системное сообщение.
- `is_read` — вычисляется сервером:
  - Приватный чат: `last_read_message_id` собеседника >= id сообщения.
  - Групповой чат: хотя бы один участник (кроме отправителя) прочитал.
  - Системные сообщения: всегда `true`.

**Ошибки:** `403` — не участник.

---

## WebSocket

### ws://localhost:8000/ws?token={access_token}

Подключение для обмена сообщениями в реальном времени. Токен передаётся как query-параметр.

`access_token` — это значение из ответа `POST /auth/login` (или `POST /auth/refresh`), поле `access_token`.

При невалидном токене соединение закрывается с кодом `4001`.

---

### Отправка сообщения (клиент → сервер)

```json
{
  "chat_id": 1,
  "text": "Привет!"
}
```

**Ответ от сервера отправителю:**

```json
{
  "status": "sent",
  "message_id": 42
}
```

**Событие у получателей (сервер → клиент):**

```json
{
  "id": 42,
  "chat_id": 1,
  "sender_id": 2,
  "text": "Привет!",
  "is_system": false,
  "created_at": "2026-03-01T12:00:00"
}
```

---

### Отметка прочтения (клиент → сервер)

```json
{
  "type": "read",
  "chat_id": 1,
  "message_id": 42
}
```

**Событие у других участников (сервер → клиент):**

```json
{
  "type": "read_update",
  "chat_id": 1,
  "user_id": 2,
  "last_read_message_id": 42
}
```

---

### Системные сообщения (сервер → клиент)

Приходят при добавлении/удалении/выходе участника:

```json
{
  "id": 43,
  "chat_id": 1,
  "sender_id": null,
  "text": "alice добавлен в чат",
  "is_system": true,
  "created_at": "2026-03-01T12:02:00"
}
```
