# Миграция WhatsApp Bridge: whatsapp-web.js → Baileys

**Дата:** 2026-02-24
**Статус:** Утверждён

## Мотивация

Замена whatsapp-web.js + Puppeteer/Chromium на Baileys для:
- Снижения потребления ресурсов (~50 MB вместо ~300+ MB RAM на сессию)
- Повышения стабильности (нет Puppeteer context errors, ProtocolError)
- Ускорения старта сессий (<1s вместо 5-15s)
- Упрощения инфраструктуры (нет Chromium, нет MongoDB)

## Подход

Drop-in замена в `wa_bridge/index.js`. REST API контракт сохраняется, Python-сторона (`app/messengers/whatsapp.py`) не меняется.

## Архитектура

### Что меняется

| Компонент | Было | Стало |
|-----------|------|-------|
| `wa_bridge/index.js` | whatsapp-web.js + Puppeteer | Baileys (чистый WebSocket) |
| `wa_bridge/package.json` | whatsapp-web.js, mongoose, wwebjs-mongo | @whiskeysockets/baileys@^6.7.0 |
| `wa_bridge/Dockerfile` | node + Chromium (~1+ GB) | node:20-slim (~100 MB) |
| Сессии | MongoDB GridFS (RemoteAuth) | Файловая система (useMultiFileAuthState) |
| docker-compose | mongo + 3 wa-bridge инстанса | 1 wa-bridge, volume wa_sessions |
| RAM лимит | 2G на инстанс | 512M |

### Что НЕ меняется

- `app/messengers/whatsapp.py` — Python HTTP клиент
- REST API эндпоинты и форматы запросов/ответов
- Celery-таски, модели, фронтенд
- Общая архитектура (Node.js microservice + Python main app)

## REST API (сохраняется)

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/sessions/:id/start` | Инициализация сессии |
| GET | `/api/sessions/:id/qr` | Получение QR-кода |
| GET | `/api/sessions/:id/status` | Статус подключения |
| POST | `/api/sessions/:id/send` | Отправка сообщения |
| GET | `/api/sessions/:id/groups` | Список групп |
| DELETE | `/api/sessions/:id` | Удаление сессии |
| GET | `/health` | Healthcheck |

## Session Lifecycle

1. **Start** — `useMultiFileAuthState('sessions/{id}')` + `makeWASocket()`. Если auth state есть — подключение без QR.
2. **QR** — из события `connection.update`, конвертируется в base64 через qrcode.
3. **Connected** — `connection: 'open'`, сессия в памяти.
4. **Idle timeout** (5 мин) — `sock.end()`, сессия остаётся на диске.
5. **ensureSession()** — при запросе загружает сессию из файлов обратно в память.
6. **Destroy** — `sock.logout()`, удаление папки сессии.

## Reconnect-логика

| DisconnectReason | Код | Действие |
|------------------|-----|----------|
| loggedOut | 401 | Удалить auth state, пометить disconnected |
| restartRequired | 428/515 | Автоматический reconnect |
| Прочие | * | Reconnect с exponential backoff (1s→30s, max 5 попыток) |

## Anti-ban меры

- `sendPresenceUpdate('composing')` перед отправкой
- Рандомная задержка 1.5-4 секунды
- Per-session rate limit: 8 сообщений/минуту
- `markOnlineOnConnect: false`

## Хранение сессий

- Путь: `sessions/{sessionId}/` (creds.json + Signal-ключи)
- Docker volume: `wa_sessions` → `/app/sessions`
- Персистентность: volume переживает рестарт контейнера

## Docker (production)

Убираем: mongo, wa-bridge-2, wa-bridge-3, mongodata volume.
Оставляем: 1 инстанс wa-bridge, добавляем volume wa_sessions.

## Зависимости (package.json)

```
Убираем: whatsapp-web.js, wwebjs-mongo, mongoose
Добавляем: @whiskeysockets/baileys@^6.7.0
Оставляем: express, qrcode, axios
```

## Версия Baileys

`@whiskeysockets/baileys@^6.7.0` — стабильная ветка. v7 (RC) не используем до финального релиза.
