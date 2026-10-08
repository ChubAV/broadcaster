# Stack Research — v2.2 «Номера аккаунтов»

**Domain:** номер телефона собственного аккаунта мессенджера (Telegram / WhatsApp / MAX) в действующем SaaS Broadcaster
**Researched:** 2026-10-08
**Confidence:** HIGH для Telethon и Baileys (проверено по установленному и скачанному исходнику), MEDIUM для MAX (тип поля проверен по исходнику, заполнение сервером при QR-входе — не проверено)

## Вердикт в одну строку

Нужна ровно **одна** новая зависимость — `phonenumberslite==9.0.41`, и только для ручного ввода и показа номера.
Номер из всех трёх библиотек достаётся существующими API без обновления версий; обновлять Telethon,
Baileys и pymax в этой вехе НЕ нужно и нельзя (рамка «протоколы отправки не трогаем»).
Главная стоимость вехи — не библиотеки, а **пересборка двух образов воркеров** (`wa_worker`, `max_worker`):
приложение не видит томов сессий, и номер WA/MAX можно получить только через HTTP воркера.

## Recommended Stack

### Core Technologies (без изменений версий — только новые вызовы)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Telethon | 1.42.0 (lock; PyPI latest 1.45.0) | номер TG-аккаунта: `User.phone` | Поле есть в схеме TL с незапамятных версий; `qr_login.wait()` и `sign_in(password=)` уже ВОЗВРАЩАЮТ `User` — дополнительный сетевой вызов не нужен. Обновление ради номера не требуется |
| @whiskeysockets/baileys | 7.0.0-rc14 (npm `latest` на 2026-10-08; `legacy` = 6.7.24) | номер WA-аккаунта: `sock.user.id` / `creds.me.id` | Проверено по исходнику rc14: `me.id` — это PN JID, LID лежит отдельно в `me.lid` (см. раздел «API по библиотекам») |
| maxapi-python (`pymax`) | 2.3.1 (пин в `max_worker/requirements.txt`; PyPI latest 2.4.1) | номер MAX-аккаунта: `client.me.contact.phone` | `Profile.contact: User`, `User.phone: int \| None`. Обновление до 2.4.1 вне объёма — протокол MAX хрупок, пин держим |
| SQLAlchemy 2 + Alembic | как в проекте | колонки `phone`, `phone_is_manual` на `messenger_accounts` | Ревизия **`0023`** (последняя в репозитории — `0022_schedules_active_requires_next_run.py`, а не `0021`) |
| Jinja2 | как в проекте | единый помощник подписи аккаунта | Регистрировать в `app/pages/common.py` рядом с прочими `templates.env.globals[...]` |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **phonenumberslite** | **9.0.41** (опубликован 2026-10-08, тот же номер, что у полного `phonenumbers`) | разбор ручного ввода (`8 (999) 123-45-67` → `+79991234567`), проверка «похоже на номер», показ в международном формате (`+7 999 123-45-67`, `+7 701 123 4567` для KZ, `+998 90 123 45 67`) | Только в двух местах: (1) нормализация ручного ввода, (2) форматирование при показе. НЕ использовать для проверки номеров, пришедших из библиотек |

Почему `phonenumberslite`, а не `phonenumbers`: API `parse` / `format_number` / `is_possible_number`
идентичен, отсутствуют только геокодер, оператор и часовые пояса, которые нам не нужны.
Колесо 473 КБ против 2,6 МБ. Импортируется тем же именем модуля `phonenumbers`
(проверено: `uv run --with phonenumberslite==9.0.41`).

Почему вообще библиотека, а не регулярка: клиенты — малый бизнес и агентства СНГ, и одна только
зона `+7` — это и Россия, и Казахстан с разной группировкой цифр. Ручной ввод приходит в виде
`8 999 …` (национальный префикс РФ), `+7 …`, `7…`. Самописный формат получится правильным
для РФ и неправильным для всех остальных; таблицы планов нумерации по странам — это и есть libphonenumber.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `just wa-worker-build` | пересборка образа WA-воркера после правки `/status` | Уже есть рецепт. Без пересборки старые контейнеры номер не отдают, и приложение обязано это переживать (поле отсутствует ⇒ «Номер неизвестен») |
| `just max-worker-build` | то же для MAX | Рецепт есть, и `just prod-deploy` / `prod-hard-deploy` его вызывают (`justfile:107`, `:119`). ⚠️ **`wa-worker-build` ни один деплой-рецепт НЕ вызывает** — правка `wa_worker/index.js` не доедет до боя через `just prod-deploy`. Либо добавить `just wa-worker-build` в оба деплой-рецепта (рекомендуется — это одна строка), либо записать ручной шаг в порядок выката |
| новый рецепт `just backfill-phones *args` | обёртка над `uv run python scripts/backfill_account_phones.py` | `--dry-run` прокидывать аргументом, по образцу `prod-cleanup-schedules` |

## Installation

```bash
# Основное приложение — единственная новая зависимость
uv add "phonenumberslite==9.0.41"

# max_worker и wa_worker — новых зависимостей НЕТ, только пересборка образов
just wa-worker-build
just max-worker-build
```

## API по библиотекам (что именно вызывать)

### Telethon 1.42.0 — HIGH (проверено по `.venv/.../telethon`)

- Тип: `telethon.tl.types.User.phone: Optional[str]` — цифры **без `+`**, например `"79991234567"`.
- **QR-вход (новые аккаунты)** — `app/messengers/telegram_user.py`:
  - `_wait_for_qr`: `await state.qr_login.wait()` **возвращает `User`** (`tl/custom/qrlogin.py:114-117`:
    `user = resp.authorization.user; await self._client._on_login(user); return user`). Сейчас результат
    отбрасывается. Нужно: `user = await state.qr_login.wait(); state.phone = user.phone`.
  - `submit_2fa`: `await state.client.sign_in(password=...)` тоже возвращает `User` через `_on_login`.
    Нужно: `user = await ...; state.phone = getattr(user, "phone", None)`.
  - Добавить поле `phone: str | None = None` в `QRAuthState`; `complete_auth` отдаёт его вместе со
    строкой сессии (сейчас возвращает только `str | None`) — сигнатура меняется, проверить оба
    вызова в `app/pages/accounts.py` (`_save_tg_account` — единственное место записи, параметр `phone` добавить туда).
  - Клиент жив до `complete_auth` (там `disconnect`) — доп. `get_me()` не нужен.
- **Существующие аккаунты (дозаполнение)**: `TelegramClient(StringSession(credentials), api_id, api_hash)`
  → `await client.connect()` → `me = await client.get_me()` → `me.phone if me else None`.
  `get_me()` возвращает `None`, если сессия не авторизована (отозвана) — это «Номер неизвестен», не ошибка.
  Шаблон уже есть в `TelegramUserMessenger.check_connection` (`:423-436`), где `get_me()` вызывается и выбрасывается.
- Возможен `phone is None` (теоретически у ботов; у пользовательского self-аккаунта практически всегда есть).

### Baileys 7.0.0-rc14 — HIGH (проверено по тарболу `npm pack @whiskeysockets/baileys@7.0.0-rc14`)

Опасение «в v7 `me.id` может оказаться LID» **опровергнуто исходником**:

1. `lib/Utils/validate-connection.js:139-192` (`configureSuccessfulPairing`): `jid = deviceNode.attrs.jid`,
   `lid = deviceNode.attrs.lid` → `me: { id: jid, name: bizName, lid }`. ID и LID — разные поля.
2. `lib/Socket/socket.js:764` при `success`: `creds.update { me: { ...creds.me, lid: node.attrs.lid } }` — обновляется только `lid`.
3. `lib/Socket/socket.js:770-773`: `const myPN = authState.creds.me.id; storeLIDPNMappings([{ lid: myLID, pn: myPN }])` — сама библиотека трактует `me.id` как номер.
4. `generateLoginNode` (`validate-connection.js:56-62`): `username: +user` из `jidDecode(creds.me.id)` — логин
   при повторном подключении отправляет номер; если бы там был LID, вход бы не работал.
5. `sock.user` — геттер `return authState.creds.me` (`socket.js:931`).

Формат: `"79991234567:12@s.whatsapp.net"` (номер, `:` устройство, сервер). Извлекать **не** `split(':')`,
а экспортируемыми помощниками Baileys (они же учитывают суффикс агента `_`):

```js
import { jidDecode, isPnUser } from '@whiskeysockets/baileys';
const meId = session?.sock?.user?.id;               // после connection === 'open'
const phone = meId && isPnUser(meId) ? jidDecode(meId)?.user ?? null : null;
```

- Где взять в `wa_worker/index.js`: в `connection === 'open'` (`:269`) `sock.user.id` уже определён
  (пара `pair-success` → `creds.update` → рестарт 515 → `open`).
- **Без живого соединения**: `useMultiFileAuthState` пишет `<SESSIONS_DIR>/<ACCOUNT_ID>/creds.json`
  (`JSON.stringify(creds, BufferJSON.replacer)`), поле `me` — обычные строки `{ id, name, lid }`.
  Воркер может отдать номер из `creds.json`, даже когда сокет не поднят — это делает дозаполнение WA
  дешёвым и не требует сканирования QR.
- `isPnUser` — это переименованный `isJidUser` из v6 (миграция v7), в rc14 есть: `jid-utils.js:65`.

### pymax (maxapi-python 2.3.1) — тип HIGH, наличие значения MEDIUM

- `client.me` → `Profile | None` (`pymax/base.py:52`, заполняется в `app.py:155` из ответа `login`).
- `Profile.contact: User` (`types/domain/profile.py`). У `User` поле **`phone: int | None = None`**
  (`types/domain/user.py:71`) — **целое число**, без `+`, например `79991234567`.
- `phone: str` на `user.py:17` — это **другой класс**, `ContactInfo` (контакт телефонной книги для
  `import_contacts`), к собственному профилю отношения не имеет. Догадка оркестратора уточнена: брать
  `client.me.contact.phone` (int), приводить `str(...)`.
- Докстринг: «Телефон пользователя, **если возвращен API**». Поле опционально — сервер MAX может
  его не прислать. При QR-входе (`WebClient`) это не проверено на живом аккаунте → флаг для фазы.
- Где взять в `max_worker/main.py`: в `on_start` (`:463`) — `connected_client.me.contact.phone`; хранить
  в `SessionState` и отдавать в `/api/sessions/{id}/status` (`:989`).
- **Тупики, которые выглядят как источник, но им не являются**:
  - `session.db`, таблица `sessions.phone` — у `WebClient` `config.phone=None` (`client_web.py:55`),
    pymax пишет туда `""`. Пусто всегда.
  - `phone.txt` в каталоге сессии и `MessengerAccount.credentials` до подключения — это номер,
    **введённый пользователем** в форме подключения MAX (`app/pages/accounts.py:924`), не проверенный
    библиотекой. Решение «считать ли его ручным» — за требованиями, не за стеком (см. ниже).

## Нормализация и хранение

| Решение | Значение | Почему |
|---------|----------|--------|
| Формат хранения | E.164-строка `"+79991234567"` | Единая форма для трёх источников (TG `str` без `+`, WA цифры из JID, MAX `int`) и ручного ввода; сортируется и сравнивается как строка |
| Тип колонки | `String(16)`, `nullable=True` | E.164 — максимум 15 цифр + `+`. `NULL` = «Номер неизвестен» |
| Признак ручного | `phone_is_manual: bool`, `NOT NULL`, `server_default=false()` | Требование «ручное не затирается» превращается в одно условие записи: авто-запись обновляет строку только при `phone_is_manual IS FALSE` (и дозаполнение — только при `phone IS NULL AND NOT phone_is_manual`). Признак в схеме, а не в соглашении кода |
| Уникальность | **НЕ** вводить | Повторное подключение того же номера создаёт второй `MessengerAccount` (TG-мастер всегда `db.add`); уникальный индекс уронил бы подключение |
| Авто-номер из библиотеки | `"+" + digits`, без `is_valid_number` | Номер подтверждён мессенджером. Метаданные libphonenumber отстают и отвергают реальные номера: проверено — анонимный номер Fragment `+888…` даёт `is_possible=False, is_valid=False`. Проверять только «5–15 цифр» |
| Ручной ввод | `phonenumbers.parse(text, "RU")` → `is_possible_number` → `format_number(..., E164)` | Регион `RU` по умолчанию превращает `8 (999) 123-45-67` в `+79991234567`; ввод с `+` разбирается по своей стране. `is_possible_number` (длина), а не `is_valid_number` (диапазоны) — по той же причине отставания метаданных |
| Показ | `format_number(parse(e164, None), INTERNATIONAL)`, при ошибке разбора — сырое значение | `+7 999 123-45-67`. Падение форматирования никогда не роняет страницу |

Размещение: новый модуль `app/services/phone.py` с тремя функциями (`normalize_reported(raw: str | int | None)`,
`normalize_manual(text: str)`, `format_phone(e164: str | None)`) + один глобал/фильтр Jinja в
`app/pages/common.py` для подписи аккаунта (сейчас `#id` собирается в ~15 местах шаблонов без помощника).
Воркеры нормализацией **не** занимаются — отдают сырые цифры, единственная точка правил — приложение.

## Точки интеграции (где стек касается кода)

| Место | Что меняется | Пересборка |
|-------|--------------|------------|
| `app/models/messenger_account.py` + `alembic/versions/0023_*.py` | колонки `phone`, `phone_is_manual` | нет |
| `app/messengers/telegram_user.py` | `QRAuthState.phone`, захват из `qr_login.wait()` и `sign_in(password=)`; помощник `get_own_phone()` для дозаполнения | нет |
| `app/pages/accounts.py` | `_save_tg_account(..., phone)`; запись номера при подключении WA/MAX по ответу `/status` | нет |
| `wa_worker/index.js` `/api/sessions/:id/status` | `phone` из `sock.user.id`, а без сессии в памяти — из `creds.json` | **да** |
| `max_worker/main.py` `/api/sessions/{id}/status` | `phone` из `client.me.contact.phone` | **да** |
| `app/messengers/whatsapp.py`, `app/messengers/max.py` | чтение `phone` из ответа `/status` (отсутствует у старого образа ⇒ `None`) | нет |
| `scripts/backfill_account_phones.py` + `justfile` | одноразовое дозаполнение, `--dry-run` | нет |

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `phonenumberslite` | `phonenumbers` (полный) | Если позже понадобится страна/оператор номера в админке (`geocoder`, `carrier`) — заменить пакет, код не меняется |
| `phonenumberslite` | Без библиотеки: только цифры + `+`, показ как есть | Если владелец решит, что ручной ввод принимается только в международном формате с `+` и красивое форматирование не нужно. Тогда новых зависимостей ноль, но `8 999…` придётся отвергать сообщением |
| `phone_is_manual: bool` | `phone_source: str` (`auto` / `manual` / `backfill`) | Если нужна диагностика происхождения номера в админке; стоит лишнего словаря значений и гейта на него |
| Номер через `/status` воркера | Чтение `creds.json` / `session.db` из приложения | Только если смонтировать тома `wa_sessions`/`max_sessions` в контейнеры приложения — сейчас они смонтированы ТОЛЬКО в динамические воркеры (`wa_container_manager.py:63`, `max_container_manager.py:68`), а для MAX `session.db` номера и не содержит |
| Номер через `/status` воркера | `docker` SDK `container.get_archive('/app/sessions/<id>/creds.json')` из скрипта дозаполнения | Запасной путь для WA, если пересборку образа нельзя выкатить до дозаполнения: `docker.sock` уже смонтирован в `web`, пакет `docker>=7.1.0` уже в зависимостях. Работает и на остановленном контейнере, но не на удалённом |
| `pydantic`-валидация в обработчике формы | `pydantic-extra-types` `PhoneNumber` | Не нужен: формы аккаунтов — `Form(...)`-поля страничных обработчиков, а тип тянет тот же `phonenumbers` плюс ещё один пакет |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `sock.user.id.split(':')[0]` / регулярка по JID | Не учитывает суффикс агента `_` и сервер `@lid`; молча вернёт LID-цифры, если когда-нибудь попадётся LID | `jidDecode(id)?.user` при `isPnUser(id)` |
| `me.lid` / `Contact.phoneNumber` своего аккаунта | `lid` — не номер; `phoneNumber` у `Contact` есть только когда `id` — LID (миграция v7) — у собственного `me` его нет | `creds.me.id` |
| pymax `session.db` → `sessions.phone` | У `WebClient` всегда `""` | `client.me.contact.phone` |
| `ContactInfo.phone` (pymax) | Класс для импорта телефонной книги, не профиль | `Profile.contact.phone` (`int`) |
| `phonenumbers.is_valid_number` для номеров из библиотек | Отвергает реальные номера (Fragment `+888`, новые диапазоны) — аккаунт останется «без номера» при известном номере | Длина 5–15 цифр; `is_possible_number` только для ручного ввода |
| Обновление Telethon до 1.45 / pymax до 2.4.1 / Baileys ради номера | Не нужно (API уже есть), а риск для доставки реальный | Текущие пины |
| Уникальный индекс по `phone` | Ломает повторное подключение того же номера | Без ограничения; дубли видны в админке рядом с `#id` |
| Хранение номера в `credentials` / `session_data` | `credentials` — это сессия (TG) или `session_id` (WA/MAX) и затирается при подключении (так сейчас теряется MAX-номер) | Отдельная колонка |
| Отдельный `phonenumbers` в `max_worker` / `wa_worker` (`libphonenumber-js`) | Дублирование правил нормализации в трёх рантаймах | Воркер отдаёт сырые цифры, нормализует приложение |

## Stack Patterns by Variant

**Если воркер старого образа (поля `phone` в `/status` нет):**
- Считать номер неизвестным, не падать и не писать `NULL` поверх уже известного номера.
- Потому что выкат образов WA/MAX и приложения не атомарен, а живые контейнеры аккаунтов пересоздаются не сразу.

**Если дозаполнение WA-аккаунта, у которого воркер не запущен:**
- Поднять воркер штатным `ensure_wa_container` и спросить `/status` — номер придёт из `creds.json` без сканирования.
- Потому что WA хранит `me` на диске; соединение с WhatsApp для этого не обязательно.

**Если дозаполнение MAX-аккаунта:**
- Номер есть только после успешного `login` (`client.me`), то есть воркер должен подключиться к MAX.
- Потому что ни `session.db`, ни что-либо ещё на диске собственного номера MAX не хранит.

**Если дозаполнение TG-аккаунта:**
- Последовательно, по одному клиенту за раз, с обработкой `FloodWaitError`; `get_me() is None` ⇒ «неизвестен».
- Потому что строка сессии одновременно используется воркером Celery `telegram`; параллельные подключения одной сессии рискуют `AuthKeyDuplicatedError`.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| phonenumberslite 9.0.41 | Python ≥ 2.5 (чистый Python, без нативных расширений) | Совместим с Python 3.12 и образом приложения; в `uv.lock` сейчас нет ни `phonenumbers`, ни `phonenumberslite`, ни `pydantic-extra-types` — конфликта нет |
| phonenumberslite | phonenumbers | **Не ставить оба**: модуль один и тот же (`phonenumbers`), пакеты перетирают друг друга |
| Telethon 1.42.0 | `User.phone`, `QRLogin.wait() -> User` | Стабильное API; 1.45.0 не требуется |
| Baileys 7.0.0-rc14 | `jidDecode`, `isPnUser` из корня пакета | `isJidUser` из v6 в v7 переименован в `isPnUser` |
| maxapi-python 2.3.1 | `Profile.contact.phone: int \| None` | Тип в 2.4.1 не проверялся — пин не меняем |

## Открытые вопросы для требований / фаз

1. **MAX: приходит ли `contact.phone` при QR-входе `WebClient`** — проверить на живом аккаунте в фазе подключения MAX. Если нет — MAX-номер возможен только вручную.
2. **Номер, введённый в форме подключения MAX** — считать его ручным (`phone_is_manual=True`) или автоматическим до подтверждения библиотекой? Влияет на правило «не затирать». Рекомендация стека: писать как авто (`phone_is_manual=False`), чтобы `client.me.contact.phone` мог его подтвердить или исправить.
3. **Порядок выката**: миграция `0023` + код приложения (терпимый к отсутствию поля) → пересборка образов → дозаполнение. Дозаполнение до пересборки даст по WA/MAX «неизвестен» у всех. Образ WA штатным `just prod-deploy` сейчас не пересобирается (см. Development Tools).

## Sources

- `.venv/lib/python3.12/site-packages/telethon` (1.42.0) — `tl/custom/qrlogin.py:109-117`, `client/auth.py:385-407`, `client/users.py:144-178`, `tl/types/__init__.py` (`User.phone: Optional[str]`) — HIGH
- `.venv/lib/python3.12/site-packages/pymax` (2.3.1) — `types/domain/user.py`, `types/domain/profile.py`, `base.py:52`, `app.py:96-157`, `client_web.py:55`, `session/store.py` — HIGH
- `npm pack @whiskeysockets/baileys@7.0.0-rc14` — `lib/Utils/validate-connection.js`, `lib/Socket/socket.js:729-790,931`, `lib/WABinary/jid-utils.js`, `lib/Utils/use-multi-file-auth-state.js`; `npm view` dist-tags (`latest: 7.0.0-rc14`) — HIGH
- Context7 `/whiskeysockets/baileys.wiki-site` — миграция v7: LID/PN, `Contact.id` + `phoneNumber`/`lid`, `isJidUser` → `isPnUser` — MEDIUM (подтверждено исходником → HIGH)
- Context7 `/daviddrysdale/python-phonenumbers` — `parse`, `format_number`, `NumberParseException` — MEDIUM (подтверждено пробным запуском 9.0.41 → HIGH)
- PyPI JSON API — `phonenumbers`/`phonenumberslite` 9.0.41 (2026-10-08), Telethon 1.45.0, maxapi-python 2.4.1 — HIGH
- [PyMax на DeepWiki](https://deepwiki.com/MaxApiTeam/PyMax) — общий обзор WebClient/Client; про `phone` профиля ничего не сообщает — LOW
- Код проекта: `app/messengers/telegram_user.py`, `wa_worker/index.js`, `max_worker/main.py`, `app/pages/accounts.py`, `docker-compose.prod.yml` (тома сессий не смонтированы в приложение), `alembic/versions/` (последняя `0022`)

---
*Stack research for: номера телефонов аккаунтов мессенджеров (v2.2)*
*Researched: 2026-10-08*
