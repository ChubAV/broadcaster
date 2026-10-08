# API Coverage — Telethon 1.42.0, вход по QR-коду (`TelegramClient` + `QRLogin`)

> Full coverage by default. Opt-outs are explicit, reasoned decisions.

Фаза не заводит новой интеграции: вход по QR через Telethon существует до фазы
(`app/messengers/telegram_user.py`). Фаза меняет транспорт мастера и классификацию одного исхода
(`asyncio.TimeoutError` из `QRLogin.wait()` → статус `qr_expired`, D-03). Матрица фиксирует всю
поверхность QR-входа, которой касается мастер, и решение по каждой возможности.

| capability | decision | reason |
|---|---|---|
| TelegramClient.connect | INTEGRATE | |
| TelegramClient.qr_login | INTEGRATE | |
| QRLogin.url | INTEGRATE | |
| QRLogin.wait | INTEGRATE | |
| QRLogin.recreate | INTEGRATE | |
| TelegramClient.sign_in(password) | INTEGRATE | |
| StringSession.save | INTEGRATE | |
| TelegramClient.disconnect | INTEGRATE | |
| QRLogin.expires | OPT-OUT | not needed — `wait()` reads it internally for its timeout; the wizard shows no countdown and never refreshes on its own (D-02) |
| QRLogin.token | OPT-OUT | not needed — the QR image is rendered from `url`, the raw token has no consumer |
| qr_login(ignored_ids) | OPT-OUT | not needed — every scan connects a new account; excluding already-authorized ids is not a product requirement |
| account.GetPassword hint display | OPT-OUT | explicitly out of scope — the wizard shows no password hint today, and new UI texts are limited to D-02/D-03/D-04 (D-09) |
| TelegramClient.log_out for an authorized-but-unsaved session | OPT-OUT | explicitly out of scope — closing abandoned Telethon clients is a deferred idea in 13-CONTEXT.md |
