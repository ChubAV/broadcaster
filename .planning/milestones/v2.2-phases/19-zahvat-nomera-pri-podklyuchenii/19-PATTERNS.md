# Фаза 19: Захват номера при подключении - карта образцов

**Составлено:** 2026-11-22
**Файлов проанализировано:** 22 (production 11, тесты 11)
**Образцов найдено:** 18 / 20 строк таблицы классификации (22 файла; две строки объединяют несколько файлов; два файла частично без образца: `wa_worker/own_phone.js`, подсказка в шаблоне)

Все цитируемые пути проверены `git ls-files` (tracked). `wa_bridge/` не цель. Образцов в зеркалах `.gsd/capabilities` нет.

## Классификация файлов

| Новый / изменяемый файл | Роль | Поток данных | Ближайший образец | Качество |
|---|---|---|---|---|
| `app/messengers/telegram_user.py` (`QRAuthState.own_phone`, `QrAuthResult`, `reported_phone_of`, `complete_auth`) | service | request-response | он же (`complete_auth`, `submit_2fa`, `_wait_for_qr`) | exact (правка на месте) |
| `app/pages/accounts.py` `_save_tg_account` + два вызова | controller | CRUD | `_save_tg_account` (:302-319) + `account_groups.py:543` (журнал без номера) | exact |
| `app/pages/accounts.py` `accounts_connect_wa_status` / `_max_status` | controller | request-response | `accounts_connect_wa_status` (:724-773) + `payment_service.py:429` (savepoint) | exact |
| `app/pages/accounts.py` `accounts_connect_max_start` | controller | request-response | `accounts_connect_max_start` (:892-915) + `account_groups.py:520-540` (`PhoneError` -> 422) | exact |
| `app/messengers/base.py` (`reported_phone_from_status`) | utility | transform | `check_connection` разбор тела (`max.py:126-133`) | role-match |
| `app/messengers/whatsapp.py`, `app/messengers/max.py` (`get_own_phone`) | service | request-response | `check_connection` в `max.py:126-133` | exact |
| `app/application/accounts/…` (по желанию, capture-помощник) | service | CRUD | `fill_reported_phone` в `app/application/accounts/phone.py` + `subscription_service.py:100` | role-match |
| `wa_worker/own_phone.js` (NEW) | utility | transform | нет JS-образца с DI; рецепт в RESEARCH Pattern 3 | no analog |
| `wa_worker/index.js` (`/status`, импорт `isPnUser`, `jidDecode`) | controller | request-response | он же, :746-762 | exact |
| `max_worker/main.py` (`own_phone_of`, `SessionState.own_phone`, `on_start`, `/status`) | service | event-driven | он же, :459-480, :989-1005 | exact |
| `justfile` (`prod-deploy`, `prod-hard-deploy`, `prod-build`, `wa-worker-build *args`) | config | batch | `max-worker-build *args` (justfile:149-151) | exact |
| `app/templates/accounts/includes/max_connect_step.html` (`hint=`) | component | request-response | `components/field.html` (макрос `field`, `hint=`) | role-match |
| `tests/test_messengers/test_telegram_user.py` | test | request-response | `test_complete_auth` (:391-399) | exact |
| `tests/test_routes/test_tg_user_auth.py` | test | request-response | `_ScannableQRLogin`, `_seed_2fa_state` (:118-195) | exact |
| `tests/test_worker/test_wa_worker_own_phone.py` (NEW) | test | transform | `tests/test_pages/test_shell.py` (`run_node_script`, :2402) | role-match |
| `tests/test_worker/test_max_worker.py` | test | request-response | `install_fake_client` (:120-130) | exact |
| `tests/test_max_worker_deployment.py` (или новый) | test | batch | сам файл (`dry_run`, :8-25) | exact |
| `tests/test_messengers/test_whatsapp.py`, `test_max.py` | test | request-response | `test_check_connection_connected` (:186) | exact |
| `tests/test_pages/test_max_connect_transport.py` | test | request-response | сам файл (`max_bridge`, :48-60) | exact |
| `tests/test_pages/test_connect_phone_capture.py` (NEW) | test | request-response | `test_max_connect_transport.py::max_bridge` + `tests/account_label_support.py::seed_account` | role-match |

## Назначение образцов

### `app/messengers/telegram_user.py` (service, request-response; план 19-01)

**Образец:** он же. `QRAuthState` (:27-40, датакласс, импорт `field` уже есть: `from dataclasses import dataclass, field`).

**Точки правки (строки до правки):**
- `_wait_for_qr` :86-90: `await state.qr_login.wait()` отбрасывает `User`. Взять `user = await state.qr_login.wait()` и `state.own_phone = reported_phone_of(user)`.
- `submit_2fa` :196: `await state.client.sign_in(password=password)` отбрасывает `User`. То же.
- `complete_auth` :205-231: инвариант «между проверкой и `pop` нет `await`»:
```python
state = _owned(session_id, user_id)
if not state or state.status != "success":
    return None
_qr_sessions.pop(session_id, None)
...
session_string = state.session_string
```
Номер снять с `state` синхронно сразу после `pop`, до `await state.client.disconnect()`; вернуть `QrAuthResult(session_string, phone)` (None, если нет `session_string`, как сегодня).

**Приватность:** `own_phone: str | None = field(default=None, repr=False)` и `QrAuthResult.phone` тоже `repr=False` (датакласс печатает поля). Рецепт: RESEARCH Pattern 1.

### `app/pages/accounts.py` `_save_tg_account` (controller, CRUD; план 19-01)

**Образец:** :302-319 (сегодня `db.add(MessengerAccount(..., status="active")); await db.commit()`). Вызывающие: :437-439 и :600-602 (`session_string = await complete_auth(...)`; `if session_string: await _save_tg_account(db, user, session_string)`). Заменить на `result = await complete_auth(...)`.

**Писатель (из `app/application/accounts/phone.py:200-213`):** объект обязан быть в сессии до вызова, иначе `ValueError(ACCOUNT_NOT_IN_SESSION)`:
```python
account = MessengerAccount(user_id=user.id, type="tg_user", credentials=result.session_string, status="active")
db.add(account)
outcome = await record_reported_phone(db, account, result.phone)
structlog.get_logger().info("tg_phone_captured", account_id=account.id, outcome=outcome.value)
await db.commit()   # номер и status="active" в одном коммите (D-01)
```
Журнал образец (без значения, только признак/исход): `app/pages/account_groups.py:543` `logger.info("account_phone_saved", account_id=account_id, phone_set=saved is not None)`. Если `UNPARSEABLE`, `account.id` может быть `None`: журналировать после коммита (`expire_on_commit=False`).

### `app/pages/accounts.py` WA/MAX опросчики (controller, request-response; план 19-05)

**Образец:** `accounts_connect_wa_status` :724-773. Вставка между `is_connected = await messenger.check_connection()` и `account.credentials = session_id`:
```python
is_connected = await messenger.check_connection()
if is_connected:
    account.credentials = session_id
    account.status = "syncing"
    await db.commit()
    from app.worker.celery_app import celery
    celery.send_task("app.worker.tasks.sync_wa_groups", args=[account.id])
```
Тот же вид у `accounts_connect_max_status` (:968-1019, `sync_max_groups`). Номер читать ДО перезаписи `credentials` (для MAX запас лежит в `account.credentials`).

**Savepoint-образец (чтобы сбой захвата не ломал подключение):** `app/services/subscription_service.py:100-107`:
```python
async with db.begin_nested():
    db.add(Subscription(...))
    await db.flush()
```
и `app/services/payment_service.py:429-431`. Обёртка: `try: async with db.begin_nested(): fill_reported_phone(...)` (при `UNPARSEABLE` второй вызов с номером формы); `except Exception:` лог `warning("phone_capture_failed", account_id=...)` без `str(e)`. Рецепт: RESEARCH Pattern 2. Общий `except Exception` опросчика (:769-772) превращает исключение в «Ошибка соединения» и строка зависает `connecting`, поэтому собственный `except` обязателен.

### `app/pages/accounts.py` `accounts_connect_max_start` (controller; план 19-05)

**Образец:** :892-915 (пустое поле -> `respond_field_error(request, page=_page, fragment=_fragment)` с `MAX_EMPTY_PHONE_ERROR`). Заменить условие `if not phone:` на разбор:
```python
try:
    e164 = normalize_manual(submitted)
except PhoneError as exc:
    error = str(exc)
```
`_page` / `_fragment` остаются вложенными функциями, поданными по имени, вызов один (гейты `test_htmx_gates.py`). `account.credentials = e164` (:930) и `credentials=e164` (:936), `messenger.start_session(phone=e164)` (:950). Образец перехвата `PhoneError` в 422 того же стиля: `app/pages/account_groups.py:520-540` (`respond_field_error(request, page=_page, fragment=_error_fragment)`). Ввод в текст ошибки не подставлять.

### `app/messengers/{whatsapp,max}.py` + `base.py` (service, request-response; план 19-05)

**Образец:** `max.py:126-133` (одинаков в `whatsapp.py:136-143`):
```python
async def check_connection(self) -> bool:
    client = get_http_client()
    try:
        response = await client.get(self._url("status"))
        return response.status_code == 200 and response.json().get("connected", False)
    except Exception as e:
        self.log.warning("check_connection_failed", error=str(e))
        return False
```
`get_own_phone()` по той же форме (второй `GET status`), `None` на любое отклонение; в журнал значение не писать. Общий чистый разбор `reported_phone_from_status(body)` (принимает `str`/`int > 0` не `bool`, иначе `None`) положить в `base.py`. `check_connection` не менять (тесты закрепляют `check_connection_failed`).

### `wa_worker/own_phone.js` (NEW, utility, transform; план 19-02)

**Образца нет** (JS-модулей с внедрением зависимостей в `wa_worker/` нет). Использовать рецепт из RESEARCH Pattern 3: `ownPhoneFromMe(me, { isPnUser, jidDecode })`, без верхнеуровневого импорта Baileys, сбой -> `null`, никакого `split(':')`. Пакет `"type": "module"`.

### `wa_worker/index.js` (controller, request-response; план 19-02)

**Образец:** :746-762 (синхронный обработчик). Импорт :8: `import makeWASocket, { useMultiFileAuthState, fetchLatestBaileysVersion, DisconnectReason, Browsers } from '@whiskeysockets/baileys';` добавить `isPnUser, jidDecode` и `import { ownPhoneFromMe } from './own_phone.js';`. Ответ с сессией:
```js
res.json({
    connected: session.isConnected,
    exists: true,
    syncState: session.syncState,
    phone: ownPhoneFromMe(session.sock?.user, { isPnUser, jidDecode }),
});
```
Ответ «нет сессии» (:757-758) без поля. Не логировать `me` / `sock.user` (гейт приватности). `BAILEYS_LOG_LEVEL` не трогать.

### `max_worker/main.py` (service, event-driven; план 19-03)

**Образец `on_start`** (:459-480): `state.is_connected = True` идёт первой строкой, затем `ready_event.set()` и запуск синка. Захват номера вставить в `try/except` ДО `state.is_connected = True`:
```python
@client.on_start()
async def on_start(connected_client):
    state.is_connected = True
    state.initializing = False
    ...
    state.ready_event.set()
```
`SessionState` (:205-215): добавить `self.own_phone: str | None = None` рядом с `self.phone: str = ""` (форма; наружу не отдавать). `/status` (:989-1005): в ветке с сессией добавить `"phone": session.own_phone`. `own_phone_of(client)` через `getattr`-цепочку (у `FakeWebClient` нет `.me`), `bool` и `<= 0` отсекать; рецепт RESEARCH Pattern 4.

### `justfile` (config, batch; план 19-04)

**Образец:** `max-worker-build *args:` (:149-151) `docker build {{ args }} --build-arg ... -t broadcaster-max-worker:latest ./max_worker`. `wa-worker-build:` (:137-138) стал `wa-worker-build *args:` с `docker build {{ args }} -t broadcaster-wa-worker:latest ./wa_worker`. Вставить `just wa-worker-build` рядом с `just max-worker-build` в `prod-deploy` (:117-118), `prod-hard-deploy` (с `--no-cache`, :104-106) и `prod-build` (:128-130): сборка ДО строки `label=broadcaster.role=wa-worker` (остановка WA идёт раньше MAX).

### `app/templates/accounts/includes/max_connect_step.html` (component; план 19-05)

**Образец:** макрос `field` в `app/templates/components/field.html:12` умеет `hint=` (:31). Добавить `hint='…'` к вызову `field(name="phone", ... placeholder='+7 999 123-45-67', required=true, autocomplete='tel')`. `action="/accounts/connect/max/start"` и `method="POST"` не менять (закреплено `test_responsive_markup.py`).

## Тесты

### `tests/test_messengers/test_telegram_user.py`
**Образец:** :385-399 `test_complete_auth` (`QRAuthState(client=mock_client, user_id=OWNER, session_string="saved_session_123", status="success")`, `result = await complete_auth(...)`, `assert result == "saved_session_123"`). Править сознательно под `QrAuthResult`; добавить `reported_phone_of`: str -> str; `None`, `""`, `MagicMock`, число -> `None`; `repr(state)` без цифр. Тесты `check_connection()` TG не добавлять (D-08).

### `tests/test_routes/test_tg_user_auth.py`
**Образец:** `_ScannableQRLogin.wait` (:125-126) возвращает `None`: заставить возвращать `SimpleNamespace(phone="79990001122")`. `_seed_2fa_state(session_id, *, owner, sign_in=None)` (:183-195): `sign_in=AsyncMock(return_value=SimpleNamespace(phone="…"))`. Утверждения: аккаунт `active`, `phone == "+7…"`, `phone_is_manual is False`; `client.get_me.assert_not_called()`; фабрика клиента и `connect` по одному разу. Гонки :1272-1326 не трогать.

### `tests/test_worker/test_wa_worker_own_phone.py` (NEW)
**Образец:** `run_node_script(source) -> dict` (`tests/conftest.py:412`, вердикт — последняя строка stdout JSON, нет Node -> `pytest.fail`), пример вызова `tests/test_pages/test_shell.py:2402, 2621` (`from tests.conftest import run_node_script`). Скрипт `import("file:///…/wa_worker/own_phone.js")` с подставными `isPnUser`/`jidDecode`, повторяющими rc14 (`jid-utils.js:30-58, :65`); четыре входа + `me` не объект; правило «`package.json` пинует `7.0.0-rc14`»; гарнир не печатает номер.

### `tests/test_worker/test_max_worker.py`
**Образец:** `install_fake_client(monkeypatch, worker)` (:120-130); `FakeWebClient` без `.me`; `state = await worker.create_client(...)`, `await client.start_handler(client)` (`test_create_client_uses_webclient_contract`, :345-358). Для нового: `client.me = SimpleNamespace(contact=SimpleNamespace(phone=79991234567))`, затем `await worker.get_session_status("42")`; кейсы `None` / без `.me` / `me=None` / `bool` / `0`; тест «нет цифр в журнале» (`caplog`).

### `tests/test_max_worker_deployment.py`
**Образец:** `dry_run(recipe)` (:8-15, `subprocess.run(["just","--dry-run",recipe], ...)`), `assert_max_build_precedes_worker_teardown` (:22-25, `output.index("just max-worker-build") < output.index('label=broadcaster.role=max-worker')`). Зеркало для WA: `prod-deploy`, `prod-hard-deploy` (`just wa-worker-build --no-cache`), `prod-build`, `dry_run("wa-worker-build --no-cache")` даёт `docker build --no-cache -t broadcaster-wa-worker:latest ./wa_worker`. Опорная строка для WA: `label=broadcaster.role=wa-worker`.

### `tests/test_messengers/test_whatsapp.py`, `test_max.py`
**Образец:** `test_check_connection_connected` / `_disconnected` / `_bridge_down` (`test_whatsapp.py:186, 203, 218`). `get_own_phone`: новая форма, старая (без `phone`), мусор, не 200, исключение.

### `tests/test_pages/test_max_connect_transport.py`
**Образец:** контекст `max_bridge(*, start_session=None, get_qr=None)` (:48-60: `patch("app.pages.accounts.MaxMessenger")` + подмена `asyncio.sleep` с `HANDSHAKE_WAIT = 5`). Править: литерал :35 `EMPTY_PHONE_ERROR` заменить импортом `PHONE_ERROR_BLANK` (старый литерал — префикс), `test_a_hostile_phone_never_reaches_the_response_raw` (:209) переписать под 422 с эхом; добавить `8 999 123 45 67` и `+7 999 123-45-67` (`credentials` нормализован), `abc`/пустое -> 422, `start_session` не вызван.

### `tests/test_pages/test_connect_phone_capture.py` (NEW)
**Образцы:** `max_bridge` (подмена `MaxMessenger`), `patch("app.pages.accounts.WhatsAppMessenger")`, подмена `celery.send_task` (импорт внутри функции: `from app.worker.celery_app import celery`). Сев известного номера: `tests/account_label_support.py::seed_account(session, user_id, type_, *, phone=…, manual_phone=…, stored_as_is=…, status=…, account_id=…)` (:48-87; прямой `MessengerAccount(phone=…)` откажет `phone_guard`). Кейсы: «ввёл A, отсканировал B -> B», «MAX не отдал -> A без пометки», старая форма `/status`, WA LID -> неизвестен, `fill_reported_phone` бросает -> всё равно `syncing` + Celery, пустое поверх известного не пишется.

## Общие образцы

### Единственный писатель номера
**Источник:** `app/application/accounts/phone.py` (`record_reported_phone` :~195-213, `fill_reported_phone`). **Применять:** `_save_tg_account` (record), опросчики WA/MAX (fill). Никаких `account.phone = …`. Коммитит обработчик.

### Журнал без номера (PHONE-21)
**Источник:** `app/pages/account_groups.py:543`. **Применять:** все новые вызовы журнала: только `account_id`, `outcome.value`, `phone_set` булевым; без `str(e)`. Переменные номера именовать с `phone`. Гейты в `<automated>` каждого плана: `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, `tests/test_application/test_phone_single_writer_gate.py`, плюс `tests/test_pages/test_htmx_post_pairs.py`, `test_htmx_gates.py`, `test_impersonation_gate.py`, `test_money_perimeter_gate.py`, `tests/test_planning`.

### Savepoint вокруг побочной записи
**Источник:** `app/services/subscription_service.py:100-107`, `app/services/payment_service.py:429-431`. **Применять:** обёртка захвата в обоих опросчиках.

### Один файл, строго последовательно
`app/pages/accounts.py` правят 19-01 (TG) и 19-05 (WA/MAX/форма) строго по очереди.

## Образца нет

| Файл | Роль | Поток | Причина |
|---|---|---|---|
| `wa_worker/own_phone.js` | utility | transform | В `wa_worker/` нет модулей с внедрением зависимостей и нет тестов; использовать RESEARCH Pattern 3 |
| `hint=` в `max_connect_step.html` | component | request-response | Образца подсказки в этом шаблоне нет; сигнатура макроса `field` — `components/field.html:12, :31` |

## Метаданные

**Область поиска образцов:** `app/messengers/`, `app/pages/`, `app/services/`, `app/application/accounts/`, `wa_worker/`, `max_worker/`, `justfile`, `tests/`.
**Дата извлечения:** 2026-11-22
