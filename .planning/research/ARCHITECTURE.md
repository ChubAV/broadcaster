# Architecture Research — v2.2 «Номера аккаунтов»

**Domain:** номер телефона собственного аккаунта мессенджера (TG / WA / MAX) в действующем brownfield-SaaS Broadcaster
**Researched:** 2026-10-08
**Confidence:** HIGH по точкам интеграции в коде приложения (всё прочитано по дереву `master` @ `f6d4b3e1`), HIGH по Telethon 1.42.0 и pymax 2.3.1 (прочитаны установленные исходники в `.venv`), LOW→MEDIUM по форме `creds.me.id` у Baileys 7 (сверено с исходником `validate-connection.ts`, классификатор источника даёт LOW, живой аккаунт не проверялся)

> Документ отвечает на вопрос «как фича встраивается в существующую систему»: что меняется, что создаётся заново, в каком порядке строить.
> Технологии выбраны в `STACK.md` (`phonenumberslite`, E.164, `String(16)`, `phone_is_manual`), продуктовые развилки разобраны в `FEATURES.md`. Здесь эти решения не пересматриваются, а раскладываются по слоям.

---

## Standard Architecture

### System Overview — где проходит номер

```
┌──────────────────────────────── ИСТОЧНИКИ НОМЕРА ─────────────────────────────────┐
│                                                                                   │
│  Telethon (в процессе web)       wa_worker (контейнер/аккаунт)  max_worker (то же)  │
│  qr_login.wait() → User.phone    sock.user.id | creds.json     client.me.contact   │
│  sign_in(password) → User.phone  GET /api/sessions/{id}/status  .phone (int)        │
│         │                           + "phone" (НОВОЕ)           + "phone" (НОВОЕ)   │
│         │                                │                          │               │
├─────────┼────────────────────────────────┼──────────────────────────┼───────────────┤
│         │           АДАПТЕРЫ  app/messengers/  (BaseMessenger)       │               │
│         │   TelegramUserMessenger   WhatsAppMessenger   MaxMessenger                 │
│         │   .get_own_phone() ─────── .get_own_phone() ── .get_own_phone()  (НОВОЕ)   │
│         │          ▲  (backfill)          ▲ (connect + backfill) ▲                  │
├─────────┼──────────┼────────────────────────┼─────────────────────┼─────────────────┤
│         ▼          │        ЕДИНСТВЕННЫЙ ПИСАТЕЛЬ НОМЕРА                             │
│  app/services/phone.py            app/application/accounts/phone.py  (НОВОЕ)       │
│  normalize_reported / _manual     record_reported_phone()  ← connect (ORM, новая строка)
│  format_phone / phone_label       fill_reported_phone()    ← backfill (условный UPDATE)
│                                   set_manual_phone()       ← POST правки            │
├────────────────────────────────────────────────────────────────────────────────────┤
│                         messenger_accounts.phone / .phone_is_manual  (ревизия 0023) │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                   ПОКАЗ                                             │
│  Jinja-глобалы phone_label(), account_label() (app/pages/common.py)                 │
│  ← 15+ шаблонных мест вместо '#' ~ account.id ; SyncStatusView.phone для опроса      │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Компонент | Что владеет | Статус |
|-----------|-------------|--------|
| `alembic/versions/0023_account_phone.py` | колонки `phone String(16) NULL`, `phone_is_manual Boolean NOT NULL DEFAULT false` (+ опционально CHECK) | **НОВЫЙ** |
| `app/models/messenger_account.py` | отображение двух колонок | ИЗМЕНЯЕТСЯ |
| `app/services/phone.py` | чистые функции: нормализация (из библиотеки / ручной ввод), форматирование, подпись «Номер неизвестен» | **НОВЫЙ** |
| `app/application/accounts/phone.py` | ПРАВИЛО ЗАПИСИ: автоисточник пишет только в пустое и не-ручное; ручной ввод пишет всегда; очистка сбрасывает признак | **НОВЫЙ** |
| `app/messengers/base.py` | `async def get_own_phone(self) -> str \| None` с умолчанием `None` (не абстрактный — по образцу `get_group_details`) | ИЗМЕНЯЕТСЯ |
| `app/messengers/telegram_user.py` | `QRAuthState.phone`; захват из возврата `qr_login.wait()` и `sign_in(password=)`; `complete_auth` отдаёт номер вместе со строкой сессии; `TelegramUserMessenger.get_own_phone()` | ИЗМЕНЯЕТСЯ |
| `app/messengers/whatsapp.py`, `max.py` | `get_own_phone()` — чтение `phone` из ответа `/status` (`.get`, поле может отсутствовать у старого образа) | ИЗМЕНЯЕТСЯ |
| `wa_worker/index.js` | `phone` в `/api/sessions/:id/status` — из `session.sock.user.id`, без сессии в памяти — из `creds.json` на томе | ИЗМЕНЯЕТСЯ (пересборка образа) |
| `max_worker/main.py` | `SessionState.me_phone` из `connected_client.me.contact.phone` в `on_start`; `phone` и `entered_phone` (`phone.txt`) в `/status` | ИЗМЕНЯЕТСЯ (пересборка образа) |
| `app/pages/accounts.py` | `_save_tg_account(..., phone)`; запись номера в `accounts_connect_wa_status` / `accounts_connect_max_status` в ТОМ ЖЕ коммите, что `status="syncing"`; новый POST правки | ИЗМЕНЯЕТСЯ |
| `app/application/accounts/dto.py`, `use_cases.py` | `SyncStatusView.phone` (карточка опроса не имеет объекта аккаунта) | ИЗМЕНЯЕТСЯ |
| `app/pages/common.py` | регистрация глобалов `phone_label`, `account_label` | ИЗМЕНЯЕТСЯ |
| шаблоны (см. таблицу ниже) | замена `'#' ~ account.id` на помощник | ИЗМЕНЯЮТСЯ |
| `app/templates/accounts/includes/phone_form.html` | ЕДИНСТВЕННЫЙ источник формы правки (страница + фрагмент успеха + фрагмент 422) | **НОВЫЙ** |
| `app/pages/notices.py` | код `ACCOUNT_PHONE_SAVED` (и, если нужно, `ACCOUNT_PHONE_CLEARED`) | ИЗМЕНЯЕТСЯ |
| `scripts/backfill_account_phones.py` | одноразовое дозаполнение | **НОВЫЙ** |
| `justfile` | `backfill-phones`, `prod-backfill-phones`; `wa-worker-build` в `prod-deploy` и `prod-hard-deploy` | ИЗМЕНЯЕТСЯ |

---

## Recommended Project Structure (только затрагиваемое)

```
alembic/versions/
└── 0023_account_phone.py              # НОВЫЙ: down_revision = "0022" (голова — 0022, а не 0021)
app/
├── models/messenger_account.py        # +phone, +phone_is_manual
├── services/phone.py                  # НОВЫЙ: normalize_reported, normalize_manual, format_phone, phone_label
├── application/accounts/
│   ├── phone.py                       # НОВЫЙ: record_reported_phone, fill_reported_phone, set_manual_phone
│   ├── dto.py                         # SyncStatusView.phone
│   └── use_cases.py                   # get_sync_status_view кладёт phone
├── messengers/
│   ├── base.py                        # get_own_phone() по умолчанию None
│   ├── telegram_user.py               # QRAuthState.phone, complete_auth → (session, phone)
│   ├── whatsapp.py / max.py           # get_own_phone() через /status
├── pages/
│   ├── accounts.py                    # захват в трёх мастерах + POST /accounts/{id}/phone
│   ├── common.py                      # globals phone_label / account_label
│   └── notices.py                     # ACCOUNT_PHONE_SAVED
└── templates/accounts/includes/phone_form.html   # НОВЫЙ
wa_worker/index.js                     # /status + phone
max_worker/main.py                     # on_start + /status + phone
scripts/backfill_account_phones.py     # НОВЫЙ
tests/
├── test_migrations/test_0023_account_phone.py    # НОВЫЙ
├── test_migrations/test_model_matches_head.py    # РАСШИРИТЬ на messenger_accounts
├── test_services/test_phone.py                   # НОВЫЙ
├── test_application/test_account_phone_rules.py  # НОВЫЙ
├── test_scripts/test_backfill_account_phones.py  # НОВЫЙ
└── test_templates/test_account_label_gate.py     # НОВЫЙ гейт: '#' ~ account.id вне admin/ запрещён
```

### Structure Rationale

- **Два модуля, а не один.** `app/services/phone.py` — чистые функции без базы: их зовут и шаблоны (через глобал), и обработчик формы, и скрипт. `app/application/accounts/phone.py` — правило записи, единственное место, где решается «можно ли автоисточнику писать». Иначе правило «ручное не затирается» живёт в трёх местах (мастер, скрипт, будущий писатель) и расходится молча. Слой `app/application/accounts/` уже существует и держит соседние правила (`group_resync.py`, `use_cases.py`).
- **Глобал Jinja, а не свойство модели.** Подпись «Номер неизвестен» — текст интерфейса, ему не место в ORM. Кроме того, у карточки опроса синхронизации объекта аккаунта нет вовсе (`sync_status_card.html` получает только `account_id`, `app/pages/accounts.py:1032`), а у карточки истории есть только `log.account_id`. Глобал от СТРОКИ номера (`phone_label(phone)`) работает во всех трёх случаях. Прецедент — `templates.env.globals["messenger_labels"]` (`app/pages/common.py:327`), заведённый ровно потому, что импортированные макросы не видят контекст вызывающего.
- **`get_own_phone()` на `BaseMessenger`.** Скрипт дозаполнения получает адаптер через уже существующий `create_messenger(account, settings)` (`app/services/messenger_factory.py`) и не ветвится по типу. Метод не абстрактный: так же устроен `get_group_details`, и тестовые подделки адаптеров не ломаются.

---

## Architectural Patterns

### Pattern 1: Один писатель номера с условием в самой записи

**What:** все три пути записи (подключение, дозаполнение, ручная правка) идут через `app/application/accounts/phone.py`. Автоисточник пишет при условии `phone IS NULL AND NOT phone_is_manual`. Ручной ввод пишет всегда и ставит `phone_is_manual = true`. Очистка (пустое поле) ставит `phone = NULL, phone_is_manual = false`, то есть возвращает аккаунт под автоисточник. Это поведение нужно записать в требование явно (`FEATURES.md`, строка про очистку).

**When to use:** всегда, когда номер пишется в базу.

**Trade-offs:** для мастеров подключения условие тривиально (строка новая, номера нет). Ценность проявляется в дозаполнении: оно длится минутами (подключение Telethon, старт контейнера до 30 с на аккаунт), и человек может вписать номер вручную, пока скрипт ждёт воркер. Чтение-сравнение-запись в Python проиграло бы эту гонку, условный `UPDATE … WHERE` не проигрывает.

**Example:**
```python
# app/application/accounts/phone.py
async def fill_reported_phone(session, account_id: int, raw) -> bool:
    phone = normalize_reported(raw)          # app/services/phone.py: "+" + цифры, 5–15 цифр
    if phone is None:
        return False
    result = await session.execute(
        update(MessengerAccount)
        .where(
            MessengerAccount.id == account_id,
            MessengerAccount.phone.is_(None),
            MessengerAccount.phone_is_manual.is_(False),
        )
        .values(phone=phone)
    )
    return result.rowcount == 1              # False = номер уже есть или ручной, это не ошибка


def record_reported_phone(account: MessengerAccount, raw) -> None:
    """Для новой строки в мастере подключения: тот же предикат, без отдельного запроса."""
    if account.phone is None and not account.phone_is_manual:
        account.phone = normalize_reported(raw)
```

**CHECK по канону проекта (решение планировщика):** `phone_is_manual = false OR phone IS NOT NULL` («ручной признак без номера невозможен»). Он соответствует тому, как построены `0021` и `0022`: инвариант в схеме, а не в соглашении. Цена — разделение по диалектам и `batch_alter_table(copy_from=…)` для SQLite, по образцу `0022_schedules_active_requires_next_run.py:247-272`. Без CHECK инвариант держит единственный писатель. Это допустимо, но тогда отказ от CHECK нужно записать решением.

### Pattern 2: Номер из того же ответа, где виден успех подключения

**What:** номер снимается в той же точке, где мастер узнаёт об успехе, и пишется в том же `commit()`, что `status`. Отдельный опрос «узнать номер потом» не заводится.

| Мастер | Точка успеха | Откуда номер | Цена |
|--------|--------------|--------------|------|
| TG QR | `_wait_for_qr` (`telegram_user.py:80`): `await state.qr_login.wait()` | возвращает `types.User` (Telethon 1.42.0, `tl/custom/qrlogin.py:115-117`) → `state.phone = user.phone` | 0 сетевых вызовов |
| TG 2FA | `submit_2fa` (`telegram_user.py:186`): `await state.client.sign_in(password=…)` | возвращает `User` (`client/auth.py:369` → `_on_login(user)` возвращает `user`) → `state.phone` | 0 вызовов |
| WA | `accounts_connect_wa_status` (`accounts.py:711`): `check_connection()` вернул `True` | `await messenger.get_own_phone()` → `/status.phone` | +1 HTTP к уже живому воркеру |
| MAX | `accounts_connect_max_status` (`accounts.py:955`): то же | `/status.phone`. Запасной вариант — номер, введённый в форме, он лежит в `account.credentials` ДО строки `account.credentials = session_id` | +1 HTTP |

**Передача номера TG из слоя адаптера в страницу.** Состояние QR-сессии снимает только `complete_auth`, одним `pop` без `await` между проверкой и снятием (`telegram_user.py:205-230`, правило «одно сканирование — один аккаунт»). Номер должен уезжать ТЕМ ЖЕ снятием: `complete_auth` возвращает `QrAuthResult(session_string, phone)` или `None`. Отдельный «прочитать номер до `complete_auth`» создал бы второе чтение состояния, которое переживает гонку двух опросов иначе, чем первое. Цена: 22 ссылки на `complete_auth` в трёх тестовых файлах. Альтернатива дешевле по тестам: положить `phone` в ответ `get_qr_status` при `success`. Тогда сломаются точные сравнения `== {"status": "success"}`, если они есть, и рядом с правилом одного снятия появится второй канал. Рекомендуется первое.

**MAX: номер затирается одной строкой.** `accounts.py:991` пишет `account.credentials = session_id` поверх номера, введённого в `accounts.py:924`. Если на запасной вариант будет решение владельца, его надо прочитать в локальную переменную ДО этой строки.

**Захват номера не имеет права уронить подключение.** Вызов `get_own_phone()` в WA/MAX-мастере оборачивается в `try/except Exception` с записью в журнал. Конкретная причина: тесты страниц подменяют `app.pages.accounts.WhatsAppMessenger` через `MagicMock` (`tests/test_pages/test_htmx_post_pairs.py:814`, `:883`, `tests/test_pages/test_htmx_preserved.py:411`). На таком двойнике `await messenger.get_own_phone()` поднимет `TypeError`, если тест не задал `AsyncMock`. В проде то же даст старый образ воркера или сетевой сбой.

### Pattern 3: Воркер отдаёт сырые цифры, приложение нормализует

**What:** воркеры добавляют поля в существующий `/status` и ничего не форматируют. Нормализация живёт в одном рантайме — Python-приложении (`STACK.md`, раздел «Нормализация»).

**wa_worker (`index.js:746`):**
```js
function ownPhone() {
    // В памяти — sock.user; без сессии — creds.json на томе (контейнер жив, сессия не загружена)
    let id = session?.sock?.user?.id;
    if (!id) {
        try {
            const creds = JSON.parse(fs.readFileSync(path.join(SESSIONS_DIR, String(ACCOUNT_ID), 'creds.json'), 'utf8'));
            id = creds?.me?.id;
        } catch (_) { /* нет файла — нет номера */ }
    }
    const decoded = id ? jidDecode(id) : null;          // "79991234567:12@s.whatsapp.net"
    return decoded?.server === 's.whatsapp.net' ? decoded.user : null;   // LID (@lid) — НЕ номер
}
// в обеих ветках /status: { connected, exists, syncState, phone: ownPhone() }
```
По исходнику Baileys (`configureSuccessfulPairing`) `me.id` берётся из `jid` узла `pair-success`, а LID лежит отдельно в `me.lid`. Проверка `server === 's.whatsapp.net'` нужна, чтобы при будущем переходе на LID воркер вернул `null`, а не идентификатор LID под видом номера.

**max_worker (`main.py:459`, `:989`):**
```python
# on_start
contact = getattr(getattr(connected_client, "me", None), "contact", None)
state.me_phone = str(contact.phone) if contact and contact.phone else None   # pymax: phone: int | None

# /status — обе ветки
"phone": session.me_phone if session else None,
"entered_phone": load_phone_from_disk() or None,      # phone.txt: ВВЕДЁН человеком, библиотекой не подтверждён
```
`sessions.phone` в SQLite-сессии pymax источником не является: у `WebClient` `config.phone=None`, и туда пишется `""` (`STACK.md`).

**Обратная совместимость обязательна.** Старый образ поля `phone` не отдаёт, и `get_own_phone()` возвращает `None` через `.get("phone")`. Приложение катится раньше образов или вместе с ними, но ни одна ветка не рассчитывает, что поле есть.

### Pattern 4: Ручная правка — один POST, одна форма, по образцу `profile_post`

**What:** `POST /accounts/{account_id}/phone` в `app/pages/accounts.py`. Форма живёт в одном экземпляре, в шапке экрана групп аккаунта (`account_groups/list.html`, блок `data-acct-head`). Это «страница аккаунта», и `FEATURES.md` её же называет «шапкой групп аккаунта».

**Почему не на карточке в списке.** Карточка аккаунта существует в ТРЁХ синхронных копиях (`accounts/list.html`, `accounts/partial_cards.html`, `accounts/partials/sync_status_card.html`). Их равенство держат правила вроде `test_accounts_three_files_dispatch_same_modal_event`, а `sync_status_card` перерисовывает карточку целиком каждые 5 с (`hx-swap="outerHTML"`). Форма внутри опрашиваемой карточки стиралась бы, пока человек набирает номер. Карточке достаточно показать номер, а при «Номер неизвестен» — ссылку «Указать номер» на экран групп.

**Скелет (повторяет `app/pages/profile.py:76-193`):**
```python
@router.post("/accounts/{account_id}/phone")
async def accounts_phone_update(request: Request, account_id: IdPath,
                                phone: str = Form(""),        # умолчание: отсутствующее поле → та же ветка 422
                                db=Depends(get_db), settings=Depends(get_settings)):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return await respond(request, redirect="/login")
    if not is_same_origin(request):                           # ORIGIN_CHECK_BOUNDARY: после прав, до чтения строки
        return Response(status_code=403)
    account = await _load_owned_account(...) if id_in_column(account_id) else None   # владелец в WHERE
    if account is None:
        return await respond(request, redirect="/accounts")   # чужой = несуществующий, один ответ
    ok, normalized, error = normalize_manual(phone)           # "" → очистка
    if ok:
        set_manual_phone(account, normalized); await db.commit()
        return await respond(request, redirect=f"/accounts/{account_id}/groups",
                             notice=notices.ACCOUNT_PHONE_SAVED, fragment=_saved)   # фрагмент + OOB заголовка
    return await respond_field_error(request, page=_page, fragment=_fragment)       # 422, эхо введённого
```
Фрагмент успеха перерисовывает форму. Через `hx-swap-oob` он заменяет `h2.acct-head__name` и `<title>`-зависимый заголовок шелла, если тот рисуется из `account_label`, иначе шапка покажет старый номер до перезагрузки. Эхо введённого значения в 422 безопасно только через автоэкранирование шаблона, `Markup(` и `|safe` запрещены гейтами (тот же довод, что `T-11-31` у формы MAX).

`_load_owned_account` живёт в `app/pages/account_groups.py:120`. Либо обработчик ставится в `account_groups.py` (форма на этом экране), либо в `accounts.py` пишется свой загрузчик с тем же `WHERE id AND user_id`. Импорт приватной функции между страничными модулями противоречит правилу гейта достижимости, описанному в докстринге `_group_counts` (`account_groups.py:170-176`). **Рекомендация:** обработчик в `account_groups.py`, рядом с формой и загрузчиком.

---

## Data Flow

### Поток 1. Подключение TG

```
POST qr-status ─► get_qr_status = success ─► complete_auth() ──► QrAuthResult(session, phone)
                                              (pop без await)          │
                                                                       ▼
                                   _save_tg_account(db, user, session, phone)
                                   MessengerAccount(..., phone=normalize_reported(phone))
                                   commit ─► шаг «Подключено»
```
`verify-2fa` проходит той же цепочкой: `submit_2fa` кладёт `state.phone`, `complete_auth` его отдаёт.

### Поток 2. Подключение WA / MAX

```
GET connect/*/status (htmx-опрос)
  └─ check_connection() == True
       ├─ try: raw = await messenger.get_own_phone()      # /status.phone (новый образ) | None (старый)
       │  except: log, raw = None
       ├─ [MAX] entered = account.credentials             # ДО перезаписи — запасной вариант, если решено
       ├─ record_reported_phone(account, raw or fallback)
       ├─ account.credentials = session_id; account.status = "syncing"
       └─ ОДИН commit ─► send_task(sync_*_groups) ─► «Подключено»
```
Номер обязан попасть в тот же коммит, что `syncing`. Первый же опрос `sync-status` рисует карточку из `SyncStatusView`, и номер, записанный позже, мигнул бы «Номер неизвестен».

### Поток 3. Показ

```
ORM MessengerAccount ──► phone_label(account.phone) ──► "+7 999 123-45-67" | "Номер неизвестен"
                    └──► account_label(account)     ──► "WhatsApp · +7 999 123-45-67"
SyncStatusView.phone ──► sync_status_card.html: phone_label(phone)
history: accounts_by_id[log.account_id].phone ──► history_card.html
admin: phone_label(account.phone) + mono('#' ~ account.id)
```

### Поток 4. Дозаполнение

```
just prod-backfill-phones [--dry-run] [--type wa] [--account-id N]
  └─ docker compose exec web uv run python scripts/backfill_account_phones.py
       SELECT … WHERE phone IS NULL AND NOT phone_is_manual AND status <> 'connecting'
       for account (последовательно):
          tg_user → TelegramUserMessenger(credentials).get_own_phone()   # connect/get_me/disconnect
          wa/max  → endpoint = start_container(id)  (вернёт живой, если уже запущен)
                    wait_for_container_ready(id)
                    [max] опрашивать /status до connected или таймаута (подключение асинхронно после /health)
                    raw = MessengerAdapter(bridge_url=endpoint, session_id).get_own_phone()
                    если контейнер запущен СКРИПТОМ — stop_container(id)
          dry-run → печать «был бы записан +7…»
          иначе   → fill_reported_phone()  (условный UPDATE, гонка с ручной правкой безопасна)
       итог: записано / нет номера у источника / сессия мертва / воркер недоступен / пропущено (ручной)
```

### Key Data Flows — подробности дозаполнения

1. **Где запускать.** Только внутри контейнера `web`. Там есть `/var/run/docker.sock` (`docker-compose.prod.yml:108`), сеть `broadcaster`, в которой имена `wa-worker-{id}` и `max-worker-{id}` разрешаются (`_container_endpoint` → `http://max-worker-12:3000`), `DATABASE_URL` и `TELEGRAM_API_ID/HASH`. С хоста имена контейнеров не разрешаются. Тома сессий (`broadcaster_wa_sessions`, `broadcaster_max_sessions`) в `web` НЕ смонтированы, поэтому номер достаётся только через HTTP воркера, а не чтением файлов.
2. **Остановленные контейнеры.** Явный `start_container` + `wait_for_container_ready` из `app/services/{wa,max}_container_manager.py` и `bridge_url=endpoint` у адаптера. Неявный путь через свойство `bridge_url` для MAX доверяет устаревшей записи `max:endpoint:{id}` в Redis без проверки контейнера (`app/messengers/max.py:25-34`, у WA это уже исправлено, `whatsapp.py:33-38`). Запуск WA-воркера с живой сессией возвращает HTTP только ПОСЛЕ `ensureSession` (`index.js:978-985`), поэтому первый `/status` уже окончательный. MAX-воркер поднимает HTTP сразу, а `create_client` подключается фоновой задачей, поэтому нужен опрос `/status` с таймаутом. Воркеры сами гасятся через `IDLE_SHUTDOWN_SEC=300`. Скрипт всё равно гасит контейнеры, которые поднял сам: при последовательном обходе со сроком около 30 с на аккаунт иначе одновременно живут около 10 контейнеров по 256 МБ.
3. **Мёртвые сессии.** Скрипт меняет ТОЛЬКО `phone`. `account.status` он не трогает, даже если Telethon ответил `AuthKeyUnregisteredError`: отвал аккаунта — область инцидентов админки (D-45.2), а не одноразовой команды. Отдельный риск у WA: запуск воркера на разлогиненной сессии приводит к `deleteSessionFiles()` (`index.js:300-311`). Это то же самое, что произошло бы при следующей отправке, но скрипт делает это раньше. Поэтому по умолчанию обходятся статусы `active` и `syncing`, а флаг `--include-inactive` расширяет обход осознанно.
4. **TG параллельно с пулом Celery.** Короткое подключение той же `StringSession` из `web`, пока `celery-worker-telegram` держит постоянное, уже происходит в `check_connection`, `get_groups` и синхронизации групп. Новый риск скрипт не вносит, но обходит аккаунты последовательно с паузой и ловит `FloodWaitError`, пропуская аккаунт.
5. **Флаг `--dry-run`.** Владелец назвал именно `--dry-run` (запись по умолчанию). Соседний `scripts/cleanup_schedules.py` устроен наоборот: dry-run по умолчанию, запись по `--apply`. Расхождение надо назвать владельцу. Если оставить формулировку владельца, рецепт `just` должен печатать первой строкой, в каком режиме идёт прогон.

---

## Шаблонные места — полный перечень (замер по дереву)

| Место | Сейчас | Станет | Контекст |
|-------|--------|--------|----------|
| `accounts/list.html:83, :116, :155` | `mono('#' ~ account.id)` | `mono(phone_label(account.phone))` | пользователь |
| `accounts/partial_cards.html:44, :71, :105` | то же | то же | пользователь |
| `accounts/partials/sync_status_card.html:56` | `mono('#' ~ account_id)` | `mono(phone_label(phone))`; обработчик `accounts.py:1032` передаёт `phone=view.phone` | пользователь, нужен `SyncStatusView.phone` |
| `account_groups/list.html:15` (`<title>`, `page_title`, `h2`) | `… ~ ' #' ~ account.id` | `account_label(account)` | пользователь |
| `ads/includes/sched_card.html:63-65` (макрос `account_label`, 3 вызова: сводка, `title` и подпись чипа) | `Канал #id` | тело макроса → глобал `account_label(account)`; макрос удалить, чтобы не было двух одноимённых помощников | пользователь |
| `history/list.html:46` (опции фильтра) | `acc.type ~ ' #' ~ acc.id` | `account_label(acc)` | пользователь |
| `history/includes/history_card.html:195` | `mono('Акк #' ~ log.account_id)` | номер по `accounts_by_id` из контекста. Карточка — макрос `history_card(log, user, detail_base_path)` без доступа к контексту, поэтому нужен параметр или поле на строке истории | пользователь, **в перечень оркестратора не входило** |
| `admin/user_history.html:27` | `acc.type ~ ' #' ~ acc.id` | `account_label(acc) ~ ' · #' ~ acc.id` | админ |
| `admin/user_detail.html:118` | `{{ acc.type }} #{{ acc.id }}` | номер + `#id` | админ |
| `admin/queue.html:84` | `Аккаунт #{{ entry.account.id }}` | номер + `#id` | админ |
| `admin/includes/queue_row.html:67` | `mono('#' ~ account.id)` | номер + `#id` | админ |
| `admin/includes/worker_row.html:75-77` | `mono('#' ~ account.id)` (ссылка в логи) | номер + `#id`; ссылка остаётся на `#id` (логи привязаны к id) | админ |
| `app/application/admin/incidents.py:267, :320` | f-строки «Аккаунт {id}» | по желанию: `DownAccountRow` + `phone`. Админ-текст на Python, вне шаблонов | админ, **в перечень оркестратора не входило** |
| `app/pages/history.py:290` (CSV-экспорт) | `group.account_id` | оставить или добавить колонку «Номер»: решение по составу экспорта (D-30 «файл = экран») | вне объёма по умолчанию |

**Ленивые связи.** `Schedule.account` объявлена с `lazy="raise"` (`app/models/schedule.py:71`). Шаблоны получают аккаунты отдельными списками (`accounts`, `all_accounts`), и помощник берёт номер только с уже загруженного объекта. Обращение к `schedule.account` в шаблоне поднимет исключение.

**Гейт против возврата.** Новое правило в `tests/test_templates/`: в шаблонах вне `admin/` нет выражений `'#' ~ <…>.id` и `' #' ~` по объектам аккаунта. `#` у `group_external_id` (`history/detail.html:54`, `history_card.html:196`) — это идентификатор группы, правило должно его пропускать. Форма гейта взята у существующих (разбор по исходнику, отрицательный контроль).

---

## Anti-Patterns

### Anti-Pattern 1: Номер в `credentials`

**What people do:** кладут номер в `credentials`, где у MAX он уже лежит до подключения.
**Why it's wrong:** у `credentials` три разных смысла: строка сессии TG, `session_id` WA и MAX, `"pending"`. MAX-мастер перезаписывает поле при подключении (`accounts.py:991`). Номер исчез бы ровно в момент успеха.
**Do this instead:** отдельная колонка `phone`. `credentials` остаётся секретом протокола.

### Anti-Pattern 2: Нормализация в воркерах

**What people do:** форматируют номер в `index.js` и `main.py`, «раз уж правим».
**Why it's wrong:** правила нормализации окажутся в трёх рантаймах, и правка любого требует пересборки образа. Ручной ввод нормализуется в Python и всё равно разойдётся с JS-версией.
**Do this instead:** воркер отдаёт сырые цифры, приложение делает `normalize_reported()`.

### Anti-Pattern 3: Форма правки на опрашиваемой карточке

**What people do:** ставят поле номера в карточку списка аккаунтов.
**Why it's wrong:** три синхронные копии карточки и её `outerHTML`-перерисовка каждые 5 с стирают ввод. Каждая новая форма в этом проекте двигает около десятка объявленных счётчиков гейтов (см. ниже). Три формы — тройная цена.
**Do this instead:** одна форма на экране групп аккаунта, на карточке только подпись и ссылка.

### Anti-Pattern 4: Скрипт через неявный `bridge_url`

**What people do:** `create_messenger(account).get_own_phone()` для WA и MAX без управления контейнером.
**Why it's wrong:** свойство `bridge_url` у MAX верит устаревшей записи Redis. Контейнеры, поднятые неявно, никто не гасит. Синхронные `wait_for_container_ready` и Docker SDK блокируют цикл событий внутри `async`-кода (для скрипта это терпимо, но таймаутом управлять нельзя).
**Do this instead:** явный `start_container` → `wait_for_container_ready` → адаптер с `bridge_url=endpoint` → `stop_container`, если контейнер поднял скрипт.

### Anti-Pattern 5: Выкат кода v2.2 без очереди ревизий

**What people do:** катят код v2.2 на бой, стоящий на `0012`/`0019`, «потому что миграция аддитивная».
**Why it's wrong:** ORM выписывает в `SELECT` ВСЕ отображённые колонки (довод `tests/test_migrations/test_model_matches_head.py`). Без колонки `phone` каждое чтение `messenger_accounts` поднимет `UndefinedColumn`: список аккаунтов, мастера, планировщик Celery, отправка. `0023` встаёт в хвост невыкаченной очереди `0013…0022` (D-26) и выкатывается только вместе с ней, с условием порядка R-08-06.
**Do this instead:** расширить `test_model_matches_head.py` на таблицу `messenger_accounts` (сейчас он сверяет только `payments`) и записать в требования вехи, что выкат v2.2 = выкат очереди до `0023`.

---

## Integration Points

### External Services

| Сервис | Паттерн интеграции | Замечания |
|--------|--------------------|-----------|
| Telegram (Telethon 1.42.0) | номер из возврата `qr_login.wait()` / `sign_in(password=)`, без лишних вызовов; для дозаполнения — `get_me().phone` | `User.phone` — цифры без `+`. Анонимные номера Fragment `+888…` — валидный случай (`STACK.md`) |
| WhatsApp (Baileys 7.0.0-rc14, в `wa_worker`) | `/status.phone` из `sock.user.id` либо `creds.json → me.id` | Возвращать только при `server === 's.whatsapp.net'`. Форма `me.id` подтверждена исходником, но не живым аккаунтом — проверить на стенде |
| MAX (pymax 2.3.1, в `max_worker`) | `/status.phone` из `client.me.contact.phone` (`int \| None`) | «Если возвращён API»: заполненность при QR-входе на живом аккаунте не проверена (`STACK.md`). `entered_phone` из `phone.txt` — запасной вариант по решению владельца |
| Docker Engine (через `docker.sock` в `web`) | `start_container` / `stop_container` / `wait_for_container_ready` | Только из контейнера `web` (DNS сети `broadcaster`) |

### Internal Boundaries

| Граница | Связь | Замечания |
|---------|-------|-----------|
| `pages/accounts.py` ↔ `messengers/telegram_user.py` | `complete_auth` → `QrAuthResult(session_string, phone)` | Меняется контракт: правятся 22 ссылки в 3 тестовых файлах |
| `pages/accounts.py` ↔ адаптеры WA/MAX | `get_own_phone()` после `check_connection()` | best-effort, `try/except` |
| адаптеры ↔ воркеры | HTTP `/api/sessions/{id}/status` + `phone` (+ `entered_phone` у MAX) | Аддитивно; старый образ даёт `None` |
| страницы/скрипт ↔ правило записи | `app/application/accounts/phone.py` | Единственное место предиката «ручное не затирается» |
| шаблоны ↔ данные | глобалы `phone_label`, `account_label` | Принимают строку и объект, работают и с ORM, и с DTO по `.phone` |
| `use_cases.get_sync_status_view` ↔ `sync_status_card.html` | `SyncStatusView.phone` | Без него карточка после первого опроса потеряет номер |
| `justfile` ↔ образы | `wa-worker-build` в `prod-deploy` и `prod-hard-deploy` | Сейчас деплой пересобирает только `max-worker` (`justfile:116-125`): правка `index.js` до боя не доедет |

### Гейты, которые сдвинет одна новая форма (бюджет планировщика)

Замер по дереву: каждый пункт ниже — объявленное число или замыкание, которое покраснеет от одного нового POST с формой. Исполнителю их нужно назвать поимённо и гнать вместе с целевым модулем (память проекта: `cross-cutting-gates-skipped-by-executors`).

| Гейт | Что сдвинется |
|------|---------------|
| `tests/test_pages/test_impersonation_gate.py` | `MUTATING_ROUTE_COUNT = 49` → 50; маршрут классифицируется в `FORBIDDEN_ROUTES` (с `forbid_when_impersonating`) или `ALLOWED_ROUTES` (с причиной). **Решение владельца:** может ли админ под чужой личностью править номер. Номер — подпись, а не учётные данные; правка профиля закрыта (D-22) по доводу «тихая правка влияет на рассылки», а номер на рассылки не влияет |
| `tests/test_pages/test_htmx_post_pairs.py` | новый обработчик через `respond()` обязан получить случай в `POST_PAIR_CASES`; адреса POST в тестах — только литералы; `PAIRED_302_ASSERTIONS_DECLARED = 191` сдвигается на каждое новое утверждение 302 |
| `tests/test_pages/test_htmx_gates.py` | `FRAGMENT_RESPONSE_HANDLERS_DECLARED = 25`, `DUAL_BRANCH_HANDLERS_DECLARED = 19`, `DUAL_BRANCH_PLACES_DECLARED = 20`, `TRANSITION_BRANCH_HANDLERS_DECLARED = 31`, `PUSH_URL_DECISIONS_DECLARED = 37` (каждой форме записывается решение `hx-push-url`, QUAL-04) |
| `tests/test_templates/test_degradation_pairs.py` | новый `*_degrades_without_htmx` → `HTMX_DEGRADATION_TESTS_DECLARED = 8` и соседние |
| `tests/test_templates/test_form_inventory.py`, `test_htmx_inventory.py` | инвентари форм и `hx-post` (49 мест письма → 50) |
| `tests/test_pages/test_notices_registry.py` | `DECLARED_CODES` + новый код `ACCOUNT_PHONE_SAVED` |
| `tests/test_migrations/test_model_matches_head.py` | расширить на `messenger_accounts` |
| `tests/test_pages/test_origin_guard_on_destructive_routes.py` | НЕ сдвинется (вселенная — только `*/delete`), но гард `is_same_origin` ставится всё равно, чтобы не пополнять долг WR-06 |

Это главный довод держать в вехе **ровно один** новый POST и **ровно одну** форму.

---

## Suggested Build Order

| # | Фаза | Состав | Зависит от | Пересборка образов |
|---|------|--------|------------|--------------------|
| 1 | **Схема и правило записи** | `0023` (+ тест ревизии по образцу `test_0014_sync_result_columns.py`), модель, `app/services/phone.py`, `app/application/accounts/phone.py`, расширение `test_model_matches_head.py` | — | нет |
| 2 | **Показ** | глобалы `phone_label`/`account_label`, 15+ шаблонных мест, `SyncStatusView.phone`, карта аккаунтов для `history_card`, админские «номер + `#id`», гейт против `'#' ~ account.id` | 1 | нет |
| 3 | **Ручная правка** | `POST /accounts/{id}/phone`, `phone_form.html`, код уведомления, ссылка «Указать номер» с карточки, все гейты из таблицы выше | 1, 2 (фрагмент успеха перерисовывает подпись помощником фазы 2) | нет |
| 4 | **Захват при подключении** | TG: `QRAuthState.phone`, `complete_auth → QrAuthResult`, `_save_tg_account(phone)`. WA/MAX: `/status.phone` в обоих воркерах, `get_own_phone()` в адаптерах, запись в мастерах в одном коммите со `syncing`. `wa-worker-build` в деплой-рецепты | 1 | **да** (wa, max) |
| 5 | **Дозаполнение** | `scripts/backfill_account_phones.py`, `just backfill-phones` / `prod-backfill-phones`, тесты скрипта (`tests/test_scripts/` — образец `test_recompress_attachments.py`) | 1, 4 (`get_own_phone()` и номер в `/status` нового образа) | использует образы фазы 4 |

**Обоснование порядка.**
- Фаза 1 первая: её колонки читает всё остальное, а ORM-модель без ревизии ломает каждое чтение таблицы.
- Фазы 2–3 раньше 4: они не зависят от воркеров и пересборки образов, но сразу закрывают цель вехи. Пользователь видит «Номер неизвестен» вместо `#id` и может вписать номер сам. Если захват WA/MAX упрётся в живой стенд (форма `me.id`, заполненность `me.contact.phone`), выход через ручную правку уже есть.
- Фазу 4 можно делить: TG (без образов, проверяется юнит-тестами) отдельно от WA/MAX (пересборка и проверка на живом аккаунте). Если фазы 2–3 и TG-часть 4 идут параллельно, они не конфликтуют по файлам, кроме `app/pages/accounts.py`, поэтому лучше последовательно.
- Фаза 5 последняя: она переиспользует `get_own_phone()` фазы 4 и имеет смысл только на боевом стенде ПОСЛЕ выката новых образов и очереди ревизий до `0023`.

**Research flags.**
- Фаза 4 (WA/MAX): **нужна проверка на живом аккаунте**. Форма `sock.user.id` у Baileys 7 подтверждена только исходником (классификатор — LOW), заполненность `me.contact.phone` у pymax при QR-входе не проверена вовсе. Ручной обход стенда как критерий приёмки.
- Фаза 5: нужен прогон `--dry-run` на копии или на бою с журналом итога до записи. Отдельно проверить поведение на остановленных контейнерах и на разлогиненной WA-сессии.
- Фазы 1–3: стандартные паттерны проекта (`0014`/`0022`, `profile_post`, глобалы `common.py`), отдельное исследование не нужно. Основной риск — бюджет гейтов, а не техника.

---

## Scaling Considerations

| Масштаб | Что учесть |
|---------|------------|
| десятки аккаунтов (сегодня) | последовательное дозаполнение за минуты; без индекса на `phone` |
| сотни аккаунтов | дозаполнение около 30 с на WA/MAX-аккаунт при холодном контейнере: часы. Флаги `--type`, `--account-id`, `--limit` позволяют идти порциями; гасить поднятые скриптом контейнеры обязательно (256 МБ каждый) |
| тысячи | поиск по номеру в админке потребовал бы индекса на `phone`; сейчас не нужен |

**Первое узкое место** — память хоста при дозаполнении (контейнеры), а не база.

---

## Open Questions (для требований и владельца)

1. **Админ под чужой личностью — может ли править номер?** От ответа зависит классификация в `test_impersonation_gate.py`. Рекомендация: разрешить с записанной причиной («подпись, не учётные данные, на доставку не влияет»).
2. **MAX: номер, введённый в форме подключения, — запасной источник или нет?** Если да, то с `phone_is_manual = false` (ввод не подтверждён библиотекой, но и не правка после подключения). Читается из `account.credentials` до строки `accounts.py:991`, при дозаполнении — из `entered_phone` воркера.
3. **`--dry-run` против `--apply`.** Владелец назвал `--dry-run`, соседний скрипт безопасен по умолчанию. Назвать расхождение и спросить.
4. **CHECK `phone_is_manual → phone IS NOT NULL`.** По канону проекта инвариант ставится в схему. Цена — `batch_alter_table` для SQLite-тестов.
5. **Админ-инциденты и CSV-экспорт истории** — расширять номером или оставить `id`. В перечень оркестратора не входили, по умолчанию вне объёма.

---

## Sources

- Код репозитория `master` @ `f6d4b3e1` (2026-10-08): `app/pages/accounts.py` (`:290`, `:375`, `:516`, `:711`, `:841`, `:955`, `:1010`), `app/messengers/{telegram_user,whatsapp,max,base,telegram_pool}.py`, `app/services/{max,wa}_container_manager.py`, `app/services/messenger_factory.py`, `app/application/accounts/{dto,use_cases}.py`, `app/pages/{profile,account_groups,common,notices}.py`, `wa_worker/index.js`, `max_worker/main.py`, `docker-compose.prod.yml`, `justfile`, `alembic/versions/0014*`, `0022*`, `tests/test_migrations/test_model_matches_head.py`, `tests/test_pages/test_{impersonation_gate,htmx_post_pairs,htmx_gates,origin_guard_on_destructive_routes}.py` — HIGH
- Telethon 1.42.0, установленный исходник: `telethon/tl/custom/qrlogin.py:68-117` (`wait()` возвращает `User`), `telethon/client/auth.py:369,385` — HIGH
- pymax (maxapi-python 2.3.1), установленный исходник: `pymax/app.py:155` (`self.me = response.profile`), `pymax/types/domain/profile.py` (`contact: User`), `pymax/types/domain/user.py:71` (`phone: int | None`), `pymax/client_web.py:55` (`phone=None`) — HIGH
- Baileys `src/Utils/validate-connection.ts`, `configureSuccessfulPairing`: `me: { id: jid, name: bizName, lid }`, где `jid` берётся из узла `device` в `pair-success` — https://raw.githubusercontent.com/WhiskeySockets/Baileys/v7.0.0-rc.9/src/Utils/validate-connection.ts — LOW по классификатору (сверено с кодом, живым аккаунтом не проверено)
- Обзор LID/PN-адресации Baileys — https://www.mintlify.com/WhiskeySockets/Baileys/core/whatsapp-ids, https://github.com/WhiskeySockets/Baileys/issues/2414 — LOW
- Соседние исследования вехи: `.planning/research/STACK.md`, `.planning/research/FEATURES.md`

---
*Architecture research for: номера телефонов аккаунтов мессенджеров в Broadcaster (v2.2)*
*Researched: 2026-10-08*
