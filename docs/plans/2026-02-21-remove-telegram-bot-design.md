# Design: Remove Telegram Bot from Broadcaster

**Date:** 2026-02-21
**Status:** Approved

## Goal

Remove Telegram Bot API (`tg_bot`) support entirely. Keep only Telegram Userbot (`tg_user`) and WhatsApp (`wa`).

## Files to Delete

- `app/messengers/telegram_bot.py` — Bot adapter (aiogram-based)
- `app/templates/accounts/connect_tg_bot.html` — Bot connection template
- `tests/test_messengers/test_telegram_bot.py` — Bot tests

## Files to Modify

1. **`app/worker/tasks.py`** — Remove `TelegramBotMessenger` import and `tg_bot` branch from `get_messenger()` factory
2. **`app/routes/pages.py`** — Remove `GET /accounts/connect/tg_bot` and `POST /accounts/connect/tg_bot` routes
3. **`app/templates/accounts/list.html`** — Remove "Подключить TG бота" button and `tg_bot` type display condition
4. **`app/templates/schedules/form.html`** — Remove `tg_bot` condition from account type display
5. **`app/templates/groups/list.html`** — Remove `tg_bot` condition from messenger type display
6. **Tests** — Remove test cases that create `tg_bot` accounts
7. **Model/route comments** — Update `# tg_bot, tg_user, wa` → `# tg_user, wa`

## Database Migration

Alembic data-only migration: `DELETE FROM messenger_accounts WHERE type = 'tg_bot'` — cascade deletes will handle related groups/schedules via FK.

## Dependencies

Remove `aiogram` package from project dependencies.
