# Telegram Userbot: Pyrogram -> Telethon + QR Auth

## Summary

Replace Pyrogram-based Telegram userbot with Telethon, using QR code authentication instead of phone+SMS flow.

## Motivation

SMS codes are unreliable (not arriving). QR code auth is faster and more reliable for users.

## Decisions

- **Full replacement**: Remove Pyrogram entirely, use only Telethon
- **No backward compat**: Existing tg_user accounts need reconnection
- **StringSession**: Store session as string in `MessengerAccount.credentials`
- **QR in web UI**: Show QR code on page with JS polling for status
- **No TelegramAuthSession model needed**: Use in-memory state for QR flow

## Architecture

### Dependencies
- Remove: `pyrogram`, `tgcrypto`
- Add: `telethon`, `qrcode[pil]`

### Messenger Adapter (`app/messengers/telegram_user.py`)
Full rewrite. Class `TelegramUserMessenger(BaseMessenger)`:
- Constructor: `session_string`, `api_id`, `api_hash`
- Creates `TelegramClient(StringSession(session_string), api_id, api_hash)`
- `send_message()` - text and photos via `client.send_message()` / `client.send_file()`
- `get_groups()` - `client.get_dialogs()`, filter groups/supergroups
- `check_connection()` - `client.get_me()`

### QR Auth Flow
In-memory store `_qr_sessions: dict[str, QRAuthState]` with 5-min TTL.

Functions:
- `start_qr_auth(api_id, api_hash)` -> creates client, calls `client.qr_login()`, returns `(session_id, qr_url)`
- `get_qr_status(session_id)` -> checks state (waiting/needs_2fa/success/expired/error)
- `refresh_qr(session_id)` -> recreate expired QR via `qr_login.recreate()`
- `submit_2fa(session_id, password)` -> enter 2FA password
- `complete_auth(session_id)` -> returns `StringSession` string, cleans up

### API Routes (in `pages.py`)
Replace phone+code flow:
- `GET /accounts/connect/tg_user` - page with QR code
- `POST /accounts/connect/tg_user/start-qr` - start QR auth, returns session_id + QR image (base64 PNG)
- `GET /accounts/connect/tg_user/qr-status?session_id=X` - JSON status
- `POST /accounts/connect/tg_user/verify-2fa` - 2FA password input
- Remove old endpoints: send-code, verify, resend-code

### Web UI (Jinja2)
Page `/accounts/connect/tg_user`:
1. Button "Start connection" -> POST start-qr
2. Show QR code as `<img>` (base64)
3. JS polls qr-status every 3 seconds
4. On `needs_2fa` -> show password field
5. On `success` -> redirect to accounts list
6. On `expired` -> button to refresh QR

### Worker
Update `get_messenger()` factory to create Telethon-based `TelegramUserMessenger`.

### Unchanged
- `MessengerAccount` model (type="tg_user", credentials=session_string)
- `Group`, `Schedule`, `SendLog` models
- Group sync logic (calls `messenger.get_groups()`)
- Celery worker flow
- Billing
