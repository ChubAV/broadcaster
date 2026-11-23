---
phase: quick-261123-bgc-max-worker-pymax-2-5-0
plan: 01
type: tdd
wave: 1
depends_on: []
files_modified:
  - max_worker/requirements.txt
  - pyproject.toml
  - uv.lock
  - max_worker/pymax_compat.py
  - max_worker/main.py
  - tests/test_worker/test_max_worker.py
autonomous: true
requirements:
  - QUICK-MAX-PYMAX-2-5-0

estimate:
  # НЕКАЛИБРОВАННАЯ ПРОЕКЦИЯ: estimate-calibration → sample_count 0, factor 1; confidence выведен, а не самооценён.
  tokens: 90000
  raw_tokens: 90000
  tasks: 2
  confidence: low

must_haves:
  truths:
    - "Код воркера ВЕТКИ на PyMax 2.5.0 получает QR входа MAX в одноразовом контейнере: проба печатает ровно строку `MAX_QR_PROBE result=qr_captured pymax=2.5.0 code=/probe/max_worker`. Та же проба на коде HEAD `a7897971` (пин 2.3.1) печатает `result=no_qr pymax=2.3.1` — сквозная RED-улика записана в SUMMARY. Ссылка QR нигде не печатается и не журналируется."
    - "Одна версия PyMax везде: `max_worker/requirements.txt` (образ), dev-группа `pyproject.toml` и `uv.lock` (тестовое окружение) закрепляют 2.5.0; `uv.lock` несёт sha256 колеса `20dcf9bfe658fd75434cc370f12c6a0114d85ee109309789c19174710cb8f479`, сверенный планировщиком с PyPI; кроме блока maxapi-python в `uv.lock` не сменилась ни одна версия пакета; `/health` отдаёт `pymax_version` = `2.5.0`."
    - "Каждая заплатка 2.3.1 решена по исходнику 2.5.0, а не догадкой: заплатки загрузки фото, вложения CONTACT и вложения STICKER СНЯТЫ (2.5.0 исправил дефект сам), и снятие закреплено тестами «нетронутая 2.5.0 принимает» в чистом интерпретаторе; заплатка размера кадра ОСТАВЛЕНА и переаудирована (2.5.0 по-прежнему ограничивает кадр 10 MiB, заплатка снимает предел) и закрыто отказывает на любой другой версии."
    - "Отправка и синхронизация на 2.5.0 доказаны настоящими сервисами библиотеки: отправка фото через НАСТОЯЩИЕ `MessageService`/`UploadService` 2.5.0 (подделаны только сокет MAX и HTTP загрузки) проходит для URL без `photoIds`, с `photoIds=` и с `photos=`, а двусмысленный ответ (две записи без имени фото) отвергается; синхронизация групп принимает чат с CONTACT без `contactId` и STICKER без `setId` на нетронутых моделях."
    - "Сессия живого аккаунта переживает переход на диске: `session.db` в точной схеме 2.3.1 воркер признаёт пригодной, НАСТОЯЩИЙ `SessionStore` 2.5.0 читает тот же token и device_id и добавляет столбец `user_agent` на месте без потери строки; параметры, которые воркер строит для легаси-сессии 1.x, принимает НАСТОЯЩИЙ `ExtraConfig` 2.5.0, и `relogin` у него по умолчанию истинен (отозванный токен → повторный вход через QR, а не падение воркера)."
    - "Сквозные гейты зелёные: `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, `tests/test_services/test_log_masking.py`, `tests/test_max_worker_deployment.py`, `tests/test_max_container_manager.py`; `graphify update .` прогнан после правок (правило `CLAUDE.md`)."
    - "SUMMARY содержит путь владельца (шаг 5 задачи) — пересборка образа MAX, проба собранного образа той же командой без монтирования кода, перезапуск воркеров, ожидаемое поведение аккаунта #19 (соединение по старому токену ИЛИ автоматический QR через relogin), затем `/gsd-verify-work 19` (W-1/W-2 и вопрос A3) — и запись о телеметрии 2.5.0 (`ExtraConfig.telemetry` по умолчанию включена) как о решении на усмотрение владельца."
  artifacts:
    - path: "max_worker/requirements.txt"
      provides: "Пин образа maxapi-python==2.5.0"
    - path: "pyproject.toml"
      provides: "Тот же пин в dev-группе (тестовое окружение)"
    - path: "uv.lock"
      provides: "Блок maxapi-python 2.5.0 с хэшем колеса, сверенным с PyPI (генерируется `uv add`, руками не правится)"
    - path: "max_worker/pymax_compat.py"
      provides: "AUDITED_PYMAX_VERSION = \"2.5.0\"; одна заплатка — размер кадра, переаудированная под 2.5.0"
    - path: "max_worker/main.py"
      provides: "Импорт и журнал только оставшейся заплатки; docstring/комментарии называют 2.5.0"
    - path: "tests/test_worker/test_max_worker.py"
      provides: "Контракт 2.5.0: версия и пины, решения по заплаткам, отправка фото на настоящих сервисах, перенос сессии 2.3.1 → 2.5.0"
  key_links:
    - from: "max_worker/requirements.txt"
      to: "max_worker/Dockerfile"
      via: "`pip install --no-cache-dir -r requirements.txt` — образ ставит ровно этот пин; проба повторяет ту же установку в одноразовом контейнере"
      pattern: "maxapi-python==2.5.0"
    - from: "max_worker/main.py"
      to: "max_worker/pymax_compat.py"
      via: "заплатка размера кадра применяется при импорте модуля воркера до создания WebClient; закрытый отказ на чужой версии роняет импорт, а не тихо расширяет шов"
      pattern: "apply_websocket_frame_size_compatibility"
    - from: "max_worker/main.py::create_client"
      to: "pymax.WebClient / ExtraConfig 2.5.0"
      via: "ExtraConfig(reconnect, log_level, url[, token, device_id]) + WorkerQrProvider.show_qr; session.db = session_dir()/session.db"
      pattern: "ExtraConfig\\(\\*\\*config_kwargs\\)"
---

<objective>
MAX-воркер снова подключается к MAX: переход с PyMax 2.3.1 на 2.5.0 (задача
`max-worker-pymax-2-5-0-upgrade`, шаги 1–4; шаг 5 — работа владельца, описывается в SUMMARY).

Purpose: с 2026-11-22T02:11Z ни один MAX-воркер на бою не подключается (живой аккаунт #19 стоит
в `waiting_for_session`, рассылки MAX не уходят), и обход W-1/W-2 фазы 19 заблокирован. Замеры
оркестратора: 2.3.1 не проходит ни со старым адресом, ни с явным `url=api.oneme.ru` (сервер
закрывает соединение `1000 OK`), 2.5.0 получает QR. Явный `url` уже в коде (`8f48e56a`) —
необходимое, но не достаточное условие.

Output: пин 2.5.0 в образе и в тестовом окружении; `max_worker/pymax_compat.py`, переаудированный
под 2.5.0; контрактные тесты 2.5.0 вместо закреплявших 2.3.1; сквозная проба QR кода ветки
в одноразовом контейнере; закреплённый перенос сессии; путь выката владельца в SUMMARY.

Почему главная задача касается шести путей и не делится: пин тестового окружения
(`pyproject.toml` + `uv.lock` — одна команда `uv add`), модуль заплаток, импорт в `main.py` и
тесты, закрепляющие 2.3.1, образуют атомарную зелёную единицу. Любой разрез оставляет красный
промежуточный коммит: на 2.3.1 переаудированная заплатка закрыто отказывает при импорте воркера,
а на 2.5.0 падают тесты пина 2.3.1 и тесты снятых заплаток. `uv.lock` генерируется, руками не правится.
</objective>

<execution_context>
@/source/broadcaster/.claude/gsd-core/workflows/execute-plan.md
@/source/broadcaster/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/todos/pending/max-worker-pymax-2-5-0-upgrade.md
@CLAUDE.md
@max_worker/pymax_compat.py
@max_worker/requirements.txt
@max_worker/Dockerfile
@tests/test_worker/test_max_worker.py

`max_worker/main.py` (1218 строк) читать участками: строки 31–45 (импорт и применение заплаток),
100–120 (журнал применения), 228–340 (сессия на диске: `own_phone_of`, `_read_session_compatibility`,
`has_reusable_session`), 404–530 (`WorkerQrProvider`, `create_client`, `_run_client`), 966–980 (`/health`).

## Факты 2.5.0, снятые планировщиком (2026-11-23)

Колесо `maxapi_python-2.5.0-py3-none-any.whl` скачано с PyPI, sha256 сверен с метаданными PyPI
(`20dcf9bfe658fd75434cc370f12c6a0114d85ee109309789c19174710cb8f479`), распаковано отдельно. После
`uv add` исполнитель ПЕРЕПРОВЕРЯЕТ каждый факт по установленному `.venv/lib/python3.12/site-packages/pymax/`
и записывает в SUMMARY «файл:строка → подтверждено/расходится».

- Транспорт: `pymax/transport/websocket.py:17-28` — `connect` передаёт `max_size=1024 * 1024 * 10`
  (10 MiB) на обеих ветках (с прокси и без), `origin=Origin("https://web.max.ru")`. WebClient
  использует именно этот транспорт (`pymax/client_web.py:78`). Замер `d549e7b3`: кадр входа
  большого аккаунта на бою — 2 700 284 байта.
- Загрузка фото: `pymax/api/uploads/service.py:100-101` — id фото из параметра `photos` ИЛИ
  `photoIds`; `:181-188` — без id принимается ровно одна запись результата, иначе ошибка. Это то
  же поведение, что у нашей заплатки (PR #107 вошёл в релиз).
- Вложения: `pymax/types/domain/attachments/` теперь пакет; `contact.py:18` —
  `contact_id: int | None = None`, `sticker.py:45` — `set_id: int | None = None`.
  `from pymax.types.domain.attachments import ContactAttachment, StickerAttachment` по-прежнему
  разрешается через `__init__`.
- `ExtraConfig` (`pymax/config.py:186+`): `url = "wss://api.oneme.ru/websocket"` (строка 256),
  `token`, `device_id: str | None`, `reconnect`, `log_level`, `relogin: bool = True`,
  `telemetry: bool = True` (строка 273). У 2.3.1 поля `relogin` нет.
- Телеметрия (`pymax/telemetry/service.py:145-155`): синтетические события навигации уходят
  опкодом `Opcode.LOG` по ТОМУ ЖЕ сокету MAX; третьих адресатов нет.
- Хранилище сессии (`pymax/session/store.py`): `SessionStore(work_dir, db_name="session.db")`;
  DDL `sessions` (строки 100–111) добавил столбец `user_agent TEXT`; `_ensure_column` мигрирует
  старую базу на месте (строка 119). Старая строка с `user_agent IS NULL` поддерживается
  (`pymax/app.py:88-96`, `resolve_session_user_agent`).
- Отозванный токен (`pymax/base.py:205-236`): `ApiError` недействительного токена при
  `relogin=True` → `relogin(start=False)` удаляет сохранённую сессию (`store.delete_session`) и
  заново проходит вход — у WebClient это QR через `qr_provider`.
- Свой номер: `pymax/types/domain/user.py:71` — `phone: int | None = None`, `Profile.contact: User` —
  источник `own_phone_of` не изменился.
- `WebClient(session_name, work_dir, extra_config, auth_flow, qr_provider)` (`pymax/client_web.py:34-41`);
  `QrHandler.show_qr(self, qr_url)` (`pymax/auth/providers.py:79`) не изменился.
- Зависимости 2.5.0 — те же девять имён, что у 2.3.1; нижние границы (`websockets>=16.0`,
  `aiohttp>=3.13.5`, …) уже выполнены в `uv.lock` (websockets 16.0, aiohttp 3.14.3, pydantic
  2.12.5, python-socks 2.8.2, qrcode 8.2, zstandard 0.25.0, aiosqlite 0.22.1, aiofiles 25.1.0,
  msgpack 1.2.1). Экстры `dishka`, `video` не ставятся.
- DDL `sessions` 2.3.1 — формат на диске у живых сессий (9 столбцов): `token TEXT NOT NULL PRIMARY KEY`,
  `device_id TEXT NOT NULL`, `phone TEXT NOT NULL`, `mt_instance_id TEXT NOT NULL DEFAULT ''`,
  `chats_sync`, `contacts_sync`, `drafts_sync`, `presence_sync` — все `INTEGER NOT NULL DEFAULT -1`,
  `config_hash TEXT NOT NULL DEFAULT ''`.

## Package Legitimacy Audit (планировщик, 2026-11-23; у быстрой задачи нет RESEARCH.md)

| Пакет | Версия | Вердикт | Улика |
|---|---|---|---|
| maxapi-python | 2.5.0 | [VERIFIED] | Тот же проект PyPI, что уже закреплён в `uv.lock` (2.3.1) и стоит в боевом образе; Homepage/Repository — `github.com/MaxApiTeam/PyMax`; колесо загружено 2026-10-25, sha256 `20dcf9bf…f479` сверен; версию и пакет назвал владелец в задаче. Новых пакетов среды исполнения нет: список зависимостей совпадает с 2.3.1 по именам. |

Пакетов [ASSUMED]/[SUS] нет — блокирующий чекпойнт легитимности не нужен. Если `uv add` добавит в
`uv.lock` хоть один НОВЫЙ пакет или сменит версию другого (гейт состава изменений `uv.lock` в задаче 1 краснеет) — остановиться: это
неаудированная установка; записать имя пакета и вернуться к оркестратору.

## Одноразовая проба QR (повторяет установку из Dockerfile, боевое не трогает)

Образ `broadcaster-max-worker:latest` (2.3.1) запускается с `--rm`; код ветки монтируется только
на чтение в `/probe/max_worker`; внутри контейнера `pip install --target /tmp/p -r` ставит ровно пин
ветки; модуль воркера импортируется (заплатки применяются), `create_client("")` идёт к MAX; через
45 с печатается одна строка-маркер и процесс завершается `os._exit(0)`. Временный `SESSIONS_DIR`
внутри контейнера, `ACCOUNT_ID=qr-probe`, Redis не нужен (`create_client` к нему не обращается),
томов боевых сессий нет. Код выхода не читать — 2.5.0 глотает `SystemExit` в `show_qr`; вердикт —
строка-маркер. Ссылку QR проба не печатает: в маркере только факт её наличия.
</context>

<tasks>

<task type="tracer" tdd="true">
  <name>Задача 1: Один путь — воркер ветки на PyMax 2.5.0 импортируется и получает QR MAX</name>
  <files>max_worker/requirements.txt, pyproject.toml, uv.lock, max_worker/pymax_compat.py, max_worker/main.py, tests/test_worker/test_max_worker.py</files>
  <behavior>
    - Контракт версии (вместо теста контракта 2.3.1): `pymax.__version__ == "2.5.0"`; у `WebClient` есть `session_name`, `work_dir`, `extra_config`, `qr_provider`; `ExtraConfig().url` равен константе воркера `MAX_WEBSOCKET_URL`; у `QrHandler.show_qr` единственный параметр после self — `qr_url`.
    - Пины согласованы (вместо теста пина 2.3.1): в `max_worker/requirements.txt` ровно одна строка `maxapi-python==2.5.0` и нет диапазонов `>=`; в dev-группе `pyproject.toml` тот же пин; блок `maxapi-python` в `uv.lock` — версия 2.5.0. Три источника сверяются друг с другом одним тестом.
    - `/health` отдаёт `pymax_version` = `2.5.0`.
    - Нетронутая 2.5.0 в ЧИСТОМ интерпретаторе (subprocess, без импорта `max_worker`): разбирает чат с вложением CONTACT без `contactId` и с STICKER без `setId` (полезная нагрузка — существующие фабрики теста); замещает три теста «нетронутая 2.3.1 отвергает».
    - Нетронутая 2.5.0 отправляет фото: настоящие `MessageService`/`UploadService` (существующий стенд `pymax_photo_send_harness`; подделаны только сокет и HTTP загрузки) — URL без `photoIds` с результатом из одной записи → токен этой записи; URL с `photoIds=777` → запись `777`; URL с `photos=777` и результатом из ДВУХ записей → запись `777`; URL без имени фото и результат из двух записей → `UploadError`. Тест «нетронутая 2.3.1 отвергает URL без photoIds» замещается.
    - Заплатка размера кадра в чистом интерпретаторе: нетронутый `WebSocketTransport.connect` 2.5.0 передаёт `max_size=10485760` на обеих ветках; после применения (первый вызов True, второй False) — `max_size=None`, `origin` по-прежнему `https://web.max.ru`, прокси передаётся; при подменённой версии (`pymax_compat.PYMAX_VERSION = "2.5.1"`) применение бросает `RuntimeError` с упоминанием обеих версий.
    - Импорт воркера в чистом интерпретаторе журналирует маркер применения заплатки размера кадра ровно один раз и ни одного маркера снятых заплаток.
    - Синхронизация групп с чатом CONTACT без `contactId` и STICKER без `setId` (существующие тесты `test_group_sync_accepts_pymax_chat_with_*`) зелёная на нетронутых моделях — тела не меняются.
  </behavior>
  <action>
    RED, сквозной (первый ход трассера): из корня checkout выполнить пробу QR из блока verify, заменив ожидаемую строку на чтение маркера (`grep -F 'MAX_QR_PROBE result='`), на НЕТРОНУТОМ коде HEAD — ожидается `MAX_QR_PROBE result=no_qr pymax=2.3.1 code=/probe/max_worker`. Строку записать в SUMMARY как сквозную RED-улику. Если маркера нет вовсе — это не RED, а сбой пробы: разобрать журнал `.pytest_cache/gsd-orch/max-qr-probe.log`, а не объявлять отказ измеренным.

    RED, контракт: переписать в `tests/test_worker/test_max_worker.py` тесты, закрепляющие 2.3.1, по блоку behavior. Удалить тесты снятых заплаток (идемпотентность и сохранение валидации заплаток CONTACT и STICKER, применение при импорте, закрытый отказ заплатки фото) — их смысл переходит в тесты «нетронутая 2.5.0 принимает/отвергает». Докстринг модуля теста и комментарии стенда фото («Real PyMax 2.3.1 …», «The shape PyMax 2.3.1 was written against») привести к 2.5.0. Импорты pymax держать внутри тел тестов (как сейчас), чтобы на 2.3.1 тесты падали утверждением, а не ошибкой сбора. Прогнать `uv run pytest tests/test_worker/test_max_worker.py -q --junit-xml=.pytest_cache/gsd-orch/bgc-red.xml` на текущем окружении 2.3.1: новые тесты обязаны краснеть AssertionError (или проваленным утверждением о коде возврата subprocess), не ImportError/ошибкой сбора — проверить по XML. Коммит `test(quick-261123-bgc): pin the PyMax 2.5.0 contract` — только если RED измерен: проверку и коммит связывать через `&&`, не через `;`.

    GREEN, зависимости: в `max_worker/requirements.txt` заменить строку пина maxapi-python на `maxapi-python==2.5.0` (прочие строки не трогать). Тестовое окружение — командой `uv add --dev "maxapi-python==2.5.0"` (правит строку dev-группы `pyproject.toml` и `uv.lock`, синхронизирует `.venv`); `uv.lock` руками не править. Если гейт состава изменений `uv.lock` называет что-либо кроме maxapi-python — остановиться (см. Package Legitimacy Audit). Перепроверить факты 2.5.0 из context по установленному пакету.

    GREEN, заплатки (`max_worker/pymax_compat.py`, решения приняты по исходнику 2.5.0): `AUDITED_PYMAX_VERSION = "2.5.0"`. Заплатку размера кадра ОСТАВИТЬ: замена `connect` по-прежнему передаёт `max_size=None`, тот же `Origin("https://web.max.ru")` и ту же развилку прокси; докстринг переписать — 2.5.0 поднял предел с 1 MiB до 10 MiB, но кадр входа несёт весь список чатов и растёт вместе с аккаунтом, а без предела работает бой сегодня; граница доверия прежняя (TLS до конечной точки MAX, разбор через валидированные модели). Заплатки CONTACT, STICKER и загрузки фото УДАЛИТЬ целиком вместе со вспомогательными функциями, логгером загрузки и ставшими ненужными импортами (`_relax_required_field`, `_ATTACHMENT_UNION_SCHEMAS`, `_resolve_photo_token`, `_upload_photo`, `_upload_logger`; импорты aiohttp, asyncio, HTTPStatus, urllib.parse, pydantic, модели и сервисы загрузок, вложения, Chat, LoginResponse, Message, если больше не используются). Докстринг модуля: «version-scoped shims for the audited PyMax 2.5.0»; одной фразой — что три заплатки 2.3.1 сняты, потому что 2.5.0 исправил дефект сам (фото: `photos`/`photoIds` и единственная запись; CONTACT/STICKER: поля необязательны).

    GREEN, воркер (`max_worker/main.py`): импортировать и применять только `apply_websocket_frame_size_compatibility`; удалить три константы `*_COMPATIBILITY_APPLIED` снятых заплаток и три строки их журнала (константа и журнал заплатки кадра остаются). Не оставлять в `main.py` комментариев с именами снятых функций. В докстринге `own_phone_of` назвать источник «pymax 2.5.0 (`types/domain/user.py`)». Комментарий у `config_kwargs` в `create_client` переписать: умолчание 2.5.0 совпадает с текущим адресом MAX, явный `url` оставлен, чтобы будущая смена умолчания библиотеки не увела воркер молча (тест `test_client_dials_the_current_max_websocket_host` держит это). `relogin` и `telemetry` явно НЕ передавать — остаются умолчания 2.5.0 (ровно та конфигурация, что получила QR в замере; `relogin` закрепит задача 2). Проверить `configure_logging` 2.5.0 (`pymax/logging.py`): если обработчики вешаются не только на логгеры `pymax`/`pymax.core`, дополнить список очистки в `create_client` и в модульном цикле — иначе ничего не менять. Прогнать тесты — зелёные. Прогнать пробу QR — маркер `result=qr_captured pymax=2.5.0`. Коммит `feat(quick-261123-bgc): move the MAX worker to PyMax 2.5.0` — через `&&` после зелёных гейтов.
  </action>
  <verify>
    <automated>uv run pytest tests/test_worker/test_max_worker.py -q</automated>
    <automated>mkdir -p .pytest_cache/gsd-orch && timeout 300 docker run --rm -w /probe -v "$PWD/max_worker:/probe/max_worker:ro" -e ACCOUNT_ID=qr-probe -e SESSIONS_DIR=/tmp/qr-probe-sessions -e PYTHONDONTWRITEBYTECODE=1 --entrypoint timeout broadcaster-max-worker:latest 240 python -c "import subprocess, sys, os, asyncio; subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', '--disable-pip-version-check', '--target', '/tmp/p', '-r', '/probe/max_worker/requirements.txt']); sys.path[:0] = ['/tmp/p', '/probe']; import max_worker.main as m; L = asyncio.new_event_loop(); asyncio.set_event_loop(L); s = L.run_until_complete(m.create_client('')); L.run_until_complete(asyncio.sleep(45)); print('MAX_QR_PROBE result=%s pymax=%s code=%s' % ('qr_captured' if s.qr_code else 'no_qr', m.pymax.__version__, os.path.dirname(m.__file__)), flush=True); os._exit(0)" > .pytest_cache/gsd-orch/max-qr-probe.log 2>&1; grep -Fx 'MAX_QR_PROBE result=qr_captured pymax=2.5.0 code=/probe/max_worker' .pytest_cache/gsd-orch/max-qr-probe.log</automated>
    <automated>test "$(grep -cFx 'maxapi-python==2.5.0' max_worker/requirements.txt)" -ge 1 && test "$(grep -cF '"maxapi-python==2.5.0"' pyproject.toml)" -ge 1 # [HEAD=0 EXPECT>=1] / [HEAD=0 EXPECT>=1]</automated>
    <automated>test "$(grep -c 20dcf9bfe658fd75434cc370f12c6a0114d85ee109309789c19174710cb8f479 uv.lock)" -ge 1 # [HEAD=0 EXPECT>=1]</automated>
    <automated>mkdir -p .pytest_cache/gsd-orch && git show a7897971:uv.lock > .pytest_cache/gsd-orch/uv.lock.head && uv run python -c "import tomllib, sys; load = lambda f: {p['name']: p.get('version') for p in tomllib.load(open(f, 'rb'))['package']}; a, b = load(sys.argv[1]), load('uv.lock'); ch = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k)); print('uv.lock changed:', ch); sys.exit(0 if ch == ['maxapi-python'] and b['maxapi-python'] == '2.5.0' else 1)" .pytest_cache/gsd-orch/uv.lock.head # [HEAD=changed:[] EXPECT=changed:[maxapi-python]@2.5.0]</automated>
    <automated>test "$(grep -cF 'AUDITED_PYMAX_VERSION = "2.5.0"' max_worker/pymax_compat.py)" -ge 1 && test "$(grep -cE 'def apply_(photo_upload|contact_attachment|sticker_attachment)_compatibility' max_worker/pymax_compat.py)" -eq 0 # [HEAD=0 EXPECT>=1] / [HEAD=3 EXPECT==0]</automated>
    <automated>test "$(grep -cE 'apply_(photo_upload|contact_attachment|sticker_attachment)_compatibility' max_worker/main.py)" -eq 0 && test "$(grep -cF 'pymax 2.5.0' max_worker/main.py)" -ge 1 # [HEAD=6 EXPECT==0] / [HEAD=0 EXPECT>=1]</automated>
  </verify>
  <done>Сквозная проба на HEAD дала `result=no_qr pymax=2.3.1` (RED, строка в SUMMARY), на ветке — `result=qr_captured pymax=2.5.0 code=/probe/max_worker`; контрактные тесты были RED утверждениями на 2.3.1 (`bgc-red.xml`) и зелёные на 2.5.0; пины трёх источников согласованы, хэш колеса в `uv.lock`, других версий пакетов `uv` не менял; в `pymax_compat.py` одна заплатка — размер кадра — с закрытым отказом на чужой версии; таблица «факт 2.5.0 → подтверждено/расходится» в SUMMARY; два коммита — test и feat.</done>
</task>

<task type="auto">
  <name>Задача 2: Сессия живого аккаунта переживает переход; сквозные гейты; путь выката владельца</name>
  <files>tests/test_worker/test_max_worker.py, max_worker/main.py</files>
  <action>
    Почему без `tdd="true"`: задача характеризует поведение сторонней библиотеки после перехода и производственного поведения не добавляет. Зубы тестов доказываются отрицательным контролем, а не RED до реализации. Если тест измерит настоящий дефект воркера, порядок TDD обязателен: красный тест — коммитом `test(...)`, правка `max_worker/main.py` — коммитом `fix(...)`.

    Тесты переноса сессии в `tests/test_worker/test_max_worker.py` (существующие помощники `create_session_db`, `install_fake_client`, фикстура `worker`; асинхронные — `@pytest.mark.asyncio`). (а) База в ТОЧНОЙ схеме 2.3.1 (DDL из 9 столбцов, перечисленный в context, — это формат живых сессий; строка token/device_id/phone с непустыми token и device_id) лежит по `worker.session_db_path()`. Воркер признаёт её: `has_reusable_session()` истинно до и после открытия базы библиотекой. НАСТОЯЩИЙ `pymax.session.store.SessionStore(work_dir=<каталог сессии>, db_name="session.db")`: `load_session()` возвращает тот же token и device_id, `user_agent` у результата — None. После этого `PRAGMA table_info(sessions)` содержит `user_agent`, строк ровно одна, `store.close()` вызван. (б) Легаси 1.x: при таблице `auth` воркер строит параметры (взять их у подделки `install_fake_client`, как это делает `test_client_dials_the_current_max_websocket_host[legacy-session]`). Эти же параметры принимает НАСТОЯЩИЙ `pymax.ExtraConfig(**kwargs)` без ошибки валидации, `token`/`device_id`/`url` сохраняются, `relogin is True`. (в) По исходнику 2.5.0 (`pymax/base.py`, `pymax/app.py`) проверить, что WebClient кладёт базу сессии в `work_dir/session_name` — тот же путь, что `session_db_path()` воркера, — и что легаси `device_id` из `ExtraConfig` доходит до сохраняемой сессии. Записать «файл:строка» в SUMMARY. Если путь или device_id расходятся — это дефект: тест, затем правка в `create_client`.

    Отрицательный контроль (записать в SUMMARY: вывод каждого прогона и восстановление): временно испортить фикстуру (а) — пустой token в строке — и убедиться, что тест краснеет утверждением о пригодности/токене; временно передать в (б) лишний ключ, которого `ExtraConfig` 2.5.0 не знает, и убедиться, что краснеет валидация (если `ExtraConfig` молча принимает лишние ключи, записать это и заменить контроль подменой `relogin=False`). Фикстуры вернуть до коммита.

    Сквозные гейты, читающие чужие исходники, и граф — по блоку verify; `graphify update .` (правило `CLAUDE.md`), код возврата — в SUMMARY. Полную суиту не гнать (~46 мин); суита записей `tests/test_planning/` вне области быстрой задачи.

    Путь владельца — в SUMMARY отдельным разделом, задачами не исполнять. (1) Пересборка образа: `just prod-build` или `just prod-deploy`. (2) Проба СОБРАННОГО образа до перезапуска воркеров: та же команда, что в задаче 1, но без монтирования кода и без pip — в `python -c` только импорт `max_worker.main`, `create_client('')`, ожидание 45 с и маркер; точную команду выписать. Ожидаемая строка — `MAX_QR_PROBE result=qr_captured pymax=2.5.0 code=/app/max_worker`. (3) Перезапуск MAX-воркеров. (4) Аккаунт #19: либо `connected` по старому токену (база мигрирует на месте), либо — если MAX отверг токен — `relogin` 2.5.0 удаляет строку сессии и воркер показывает QR; пересканировать. (5) `/gsd-verify-work 19` — W-1/W-2 и вопрос A3 (сообщает ли MAX номер сам). Отдельно — решение на усмотрение владельца: 2.5.0 по умолчанию шлёт синтетическую телеметрию навигации (`Opcode.LOG`) по тому же сокету MAX. Воркер оставил умолчание, потому что именно с ним замер получил QR. Отключение — `telemetry=False` в `config_kwargs`, отдельной задачей.

    Коммит тестов — `test(quick-261123-bgc): pin the 2.3.1 to 2.5.0 session transfer` — через `&&` после зелёных гейтов. Неотслеживаемый `.dockerignore` в корне не коммитить.
  </action>
  <verify>
    <automated>uv run pytest tests/test_worker/test_max_worker.py -q -k "session or legacy or relogin or health or pymax"</automated>
    <automated>uv run pytest tests/test_worker/test_max_worker.py tests/test_max_worker_deployment.py tests/test_max_container_manager.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_services/test_log_masking.py -q</automated>
    <automated>graphify update .</automated>
  </verify>
  <done>Тесты переноса (а) и (б) зелёные на 2.5.0, отрицательный контроль каждого краснел и откачен (выводы в SUMMARY); путь базы сессии и перенос легаси device_id подтверждены «файл:строка» либо исправлены тестом и правкой; сквозные гейты зелёные; `graphify update .` прогнан; в SUMMARY есть путь владельца с точной командой пробы собранного образа, ожидания по аккаунту #19 и запись о телеметрии.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| PyPI → образ MAX и тестовое окружение | Новая версия сторонней библиотеки входит в боевой образ (`pip install -r`) и в `.venv` (`uv`). |
| воркер ↔ MAX (WSS, TLS) | Рукопожатие, вход, кадры событий; PyMax 2.5.0 меняет протокол, `app_version` и добавляет телеметрию. |
| том сессий ↔ библиотека | `session.db` живых аккаунтов (token, device_id) открывает новая версия и мигрирует на месте. |
| одноразовый контейнер пробы ↔ хост/бой | Проба ходит к MAX с хоста стенда, где работают боевые воркеры. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-QUICK-BGC-01 | Tampering | maxapi-python 2.5.0 (цепочка поставки) | high | mitigate | Тот же проект PyPI, что уже закреплён; sha256 колеса сверен планировщиком с PyPI, задача 1 требует этот хэш в `uv.lock` (uv проверяет хэши при установке); гейт состава изменений `uv.lock` (сравнение карт «пакет → версия» с HEAD через tomllib: изменён ровно maxapi-python) ловит любой новый или сменившийся транзитивный пакет и останавливает задачу. Остаток: `pip install -r` в Dockerfile без хэшей — прежняя поза проекта, не расширяется. |
| T-QUICK-BGC-02 | Information Disclosure | Ссылка QR входа в выводе пробы | medium | mitigate | Проба печатает только факт наличия QR (`result=qr_captured`), ссылку — никогда; `WorkerQrProvider` ссылку не журналирует (без изменений); журнал пробы лежит в `.pytest_cache/` (не коммитится). |
| T-QUICK-BGC-03 | Information Disclosure | Телеметрия 2.5.0 (`ExtraConfig.telemetry=True`) | low | accept | Синтетические события навигации уходят опкодом `LOG` только в MAX по уже доверенному сокету; содержимое — синтетика и идентификаторы, которые у MAX и так есть; третьих адресатов нет (`pymax/telemetry/service.py`). Умолчание оставлено — с ним замер получил QR. Решение вынесено владельцу в SUMMARY. |
| T-QUICK-BGC-04 | Denial of Service | Заплатка размера кадра (`max_size=None`) | low | accept | Поведение боя не меняется (предел снят с `d549e7b3`); кадры идут от конечной точки MAX по TLS после рукопожатия и разбираются валидированными моделями; без заплатки большой аккаунт снова уйдёт в вечный цикл переподключения, когда кадр входа перерастёт 10 MiB. Закрытый отказ на чужой версии оставлен. |
| T-QUICK-BGC-05 | Tampering | `session.db` живых аккаунтов (миграция и relogin 2.5.0) | medium | mitigate | Задача 2 закрепляет тестом: схема 2.3.1 мигрирует на месте без потери token/device_id, а воркер видит базу пригодной. Путь базы и перенос легаси device_id сверены по исходнику. Удаление строки сессии при отозванном токене (`relogin`) — штатный путь к QR, ожидание записано владельцу. |
| T-QUICK-BGC-06 | Elevation of Privilege | Одноразовый контейнер пробы на хосте стенда | medium | mitigate | `--rm`, код ветки только на чтение, временный `SESSIONS_DIR` внутри контейнера, без томов сессий, без `REDIS_URL` (Redis не используется), без пересборки и перезапуска боевого; тег `:latest` не пересобирается; внутренний `timeout 240` и внешний `timeout 300` ограничивают время. |
| T-QUICK-BGC-07 | Information Disclosure | Номер аккаунта в журналах воркера | low | mitigate | `own_phone_of` и журналы номера не меняются; гейт приватности номера (`tests/test_phone_privacy_gate.py`, читает и `max_worker/`, и `scripts/`) и паритет гейтов входят в verify задачи 2. |
| T-QUICK-BGC-SC | Tampering | Установки pip/uv | high | mitigate | Гейт легитимности: аудит maxapi-python 2.5.0 — [VERIFIED] (таблица в context); пакетов [ASSUMED]/[SUS]/[SLOP] нет, поэтому блокирующего чекпойнта нет. Появление нового пакета в `uv.lock` останавливает задачу 1 до решения человека. |
</threat_model>

<verification>
- `uv run pytest tests/test_worker/test_max_worker.py tests/test_max_worker_deployment.py tests/test_max_container_manager.py tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_services/test_log_masking.py -q` — зелёный.
- Проба QR (verify задачи 1) — строка `MAX_QR_PROBE result=qr_captured pymax=2.5.0 code=/probe/max_worker`; RED-строка на HEAD записана.
- Пины трёх источников = 2.5.0, хэш колеса в `uv.lock`, иных смен версий в `uv.lock` нет.
- `git status --porcelain` после коммитов: нет изменений вне `files_modified`, кроме неотслеживаемого `.dockerignore` (был до задачи).
</verification>

<success_criteria>
- Код воркера ветки на PyMax 2.5.0 получает QR MAX (сквозная проба), а на коде HEAD — нет (записано).
- Заплатки 2.3.1 решены по исходнику 2.5.0: три сняты и закреплены тестами «нетронутая принимает», одна оставлена и переаудирована.
- Отправка фото и синхронизация групп доказаны на настоящих сервисах и моделях 2.5.0.
- Перенос сессии 2.3.1 → 2.5.0 закреплён тестом с отрицательным контролем.
- Сквозные гейты зелёные, граф обновлён.
- SUMMARY: RED/GREEN-улики пробы, таблица фактов 2.5.0, путь владельца (пересборка, проба собранного образа, перезапуск, аккаунт #19, `/gsd-verify-work 19`), запись о телеметрии.
</success_criteria>

<output>
Create `.planning/quick/261123-bgc-max-vorker-perehod-na-pymax-2-5-0-todo-m/261123-bgc-SUMMARY.md` when done
</output>
