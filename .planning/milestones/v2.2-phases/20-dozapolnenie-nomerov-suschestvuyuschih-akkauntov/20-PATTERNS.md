# Фаза 20: Дозаполнение номеров существующих аккаунтов - карта образцов

**Составлено:** 2026-11-23
**Файлов проанализировано:** 4 (3 новых, 1 изменяемый)
**Образцы найдены:** 4 / 4 (все пути проверены `git ls-files`, все отслеживаются)

Источник набора файлов: CONTEXT D-10 (имена скрипта и рецептов), RESEARCH «Summary» и «Волны и планы» (один скрипт, два рецепта, тест). RESEARCH прямо говорит: правок в `app/`, миграций, маршрутов, шаблонов нет. Отвергнутые владельцем варианты (читатель `creds.json`, читатель `phone.txt`, монтирование тома сессий, перенос `credentials`, копия боевой базы) образцов не получают.

## Классификация файлов

| Новый/изменяемый файл | Роль | Поток данных | Ближайший образец | Качество |
|---|---|---|---|---|
| `scripts/backfill_account_phones.py` | скрипт-утилита (CLI, ядро `run(...)` с внедряемыми источниками) | batch + request-response (HTTP `/status`, Telethon, Docker SDK) | `scripts/recompress_attachments.py` (форма) + `scripts/collect_group_info.py` (аргументы, фильтры) | role-match |
| `tests/test_scripts/test_backfill_account_phones.py` | test | batch, двойники источников | `tests/test_scripts/test_recompress_attachments.py` + `tests/test_application/test_account_phone_race.py` (файловая база) | role-match |
| `justfile` (рецепты `backfill-phones`, `prod-backfill-phones`) | config | - | пара `collect-group-info` / `prod-collect-group-info` (justfile:161-167), пара `recompress-attachments` (169-175) | exact (кроме `-T`) |

## Назначения образцов

### `scripts/backfill_account_phones.py` (скрипт, batch)

**Образец:** `scripts/recompress_attachments.py`

**Шапка и импорты** (строки 34-64): `argparse`, `asyncio`, `sys`, `dataclass`, `Path`, затем `sys.path.insert` ДО импортов `app`:
```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import get_settings
from app.database import get_engine, get_session_factory
```
К ним добавить (пути проверены): `from app.application.accounts.phone import PhoneWrite, fill_reported_phone`; `from app.services.phone import mask_phone, normalize_reported`; `from app.messengers.base import reported_phone_from_status`; `from app.messengers.telegram_user import reported_phone_of`; `from app.models.messenger_account import MessengerAccount`. `setup_logging` НЕ импортировать (гейт `test_log_masking` измеряет `scripts/*.py`, RESEARCH B5). `yaml` не импортировать.

**Ядро с внедрением источников** (recompress, строки 94-110, 296-313): `Protocol` источников + `async def recompress_attachments(session, store, *, apply)`; перехват `Exception` на ОДИН элемент, ошибка становится строкой итога, прогон не падает (строки 306-311). Для Фазы 20: `run(session, sources, *, dry_run, ...)`, исключение по аккаунту -> исход «сбой по аккаунту» + `await session.rollback()` (D-14), успешная запись -> `await session.commit()` после КАЖДОГО аккаунта (писатель не коммитит, phone.py:59).

**Счётчики итога** (строки 136-165): `@dataclass Report` + рендер обходом кортежа/перечисления (строки 341-345), а не дублированным списком. Здесь `enum.Enum` `Outcome` (`FILLED`, `KEPT`, `NO_NUMBER`, `DEAD_SESSION`, `UNREACHABLE`, `BUSY`, `ACCOUNT_GONE`, сбой) и итог обходом `for outcome in Outcome`. Доступ только `Outcome.X`, без `getattr` (динамика краснит гейт, RESEARCH B6).

**main и точка входа** (строки 379-419): собственная фабрика сессии, `engine.dispose()` в конце, `asyncio.run(main(...))`:
```python
async def main(apply: bool) -> None:
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)
    async with session_factory() as session:
        ...
    print(format_report(report, apply=apply))
    await engine.dispose()
```
Отличие, зафиксированное D-08: у соседей флаг `--apply` и сухой прогон по умолчанию; здесь ОБРАТНО, `--dry-run`, а без флагов скрипт ПИШЕТ. Строка `help` и docstring шапки обязаны сказать это прямо. Код выхода 0 при дошедшем до конца прогоне (D-15), ненулевой только при сбое базы/аргументов.

**Аргументы и фильтры** (`scripts/collect_group_info.py:1-30`): шапка-usage со всеми формами вызова, фильтр `--type` (`tg_user` / `wa` / `max`, `choices=`), `--user-id` у соседа, здесь `--account-id`, `--limit`, `--dry-run`, флаг подъёма (например `--wake`; под `--dry-run` отвергать через `parser.error(...)`, это не журнал и гейт его не судит, privacy gate :4895).

**Выборка колонками, не сущностями** (RESEARCH B1, образец `select(Ad.images)` в recompress:180):
```python
select(MessengerAccount.id, MessengerAccount.type,
       MessengerAccount.credentials, MessengerAccount.status).where(
    MessengerAccount.phone.is_(None),
    MessengerAccount.phone_is_manual.is_(False))
```
Чтение колонок номера гейт писателя разрешает; запись (`update`, `.values`, присваивание, `MessengerAccount(...)`) краснит.

**Запись:** только `fill_reported_phone(session, account_id, raw)` (phone.py:148-157), которая возвращает `PhoneWrite`. Карта (D-02): `WRITTEN` -> заполнено, `KEPT` -> ручной/уже заполнен, `UNPARSEABLE` и пусто -> номера нет, `MISSING` -> аккаунт удалён (отдельная строка). Под `--dry-run` писатель не вызывать вовсе; исход предсказывать чтением и `normalize_reported`.

**Источник WA/MAX** (`app/services/wa_container_manager.py`, зеркало в `max_container_manager.py`):
- `list_worker_containers()` (строки 103-116) возвращает `[{"account_id", "name", "status", "short_id"}]`; «работает» = `status == "running"`, один вызов на тип. Redis-ключи `*:endpoint:*` для этого не годятся (TTL 420 с).
- Адрес: `http://{name}:3000` (`_container_endpoint`, строка 147; `DEFAULT_PORT = 3000`).
- Подъём по флагу: `start_container(account_id)` (строка 30; у MAX с `phone=""` по умолчанию), `wait_for_container_ready(account_id, timeout=30.0)` (строки 151-170; СИНХРОННАЯ, `time.sleep` + `httpx.get`: звать через `asyncio.to_thread`), `stop_container(account_id)` (строка 85) в `finally`; уже работавший контейнер не гасить никогда (D-16).
- ЛОВУШКА (RESEARCH B2): адаптеры `WhatsAppMessenger` / `MaxMessenger` без явного `bridge_url` сами будят воркер через `ensure_*_container`. Не использовать `create_messenger` и `get_own_phone()`. Свой запрос `/status` по адресу из Docker, затем разбор:
```python
# app/messengers/base.py:16-37
def reported_phone_from_status(body: object) -> str | None: ...
```
Разбор поля `phone` брать оттуда; старый образ без поля = «номера нет», не ошибка.

**Источник TG** (`app/messengers/telegram_user.py`):
- Строка 329-333: `TelegramClient(StringSession(session_string), api_id, api_hash)`. Для скрипта добавить `receive_updates=False` (Telethon 1.42.0, параметр есть), не вызывать `start()`.
- `reported_phone_of(user)` (строки 62-76) тотальна: `None` на любой неожиданности, формат не правит.
- Порядок: проверка строки сессии БЕЗ сети (`StringSession(...)` в `try`, `ValueError`/`struct.error`/`binascii.Error` -> «сессия мертва»), затем `connect` -> `is_user_authorized` -> `get_me`, `disconnect` в `finally`, строго последовательно. Карта ошибок: RESEARCH A3 (таблица, строки 180-188). `AuthKeyError` -> «сессия мертва»; `OSError`/`TimeoutError`/`FloodWaitError` -> «источник недоступен». В строку исхода идёт имя класса исключения, не текст (текст может нести номер).
- Не опираться на `check_connection()` (D-17).
- «Занят» (D-09): `celery.control.inspect()` `active` + `reserved`, `args[2] == account_id`, задача `app.worker.tasks.send_telegram_message`; ответа нет -> «занят» (RESEARCH A2). `TelegramPool` не используется, на него не ссылаться.

**Форма `print` (проходит гейты, RESEARCH B6, измерено на пробном исходнике):**
```python
print(f"#{account_id} {kind} {Outcome.NO_NUMBER.value}")
print(f"#{account_id} {kind} {Outcome.FILLED.value} {mask_phone(e164)}")
```
Правила: имена с подстрокой `phone` в аргументах `print` запрещены (`reported`, `e164`, `masked`); `mask_phone(...)` допустим только прямо внутри `print` под `scripts/` (privacy_gate.py:1910); цифр, похожих на номер, в литералах нет; `PHONE_LOG_EXCEPTIONS`, `PHONE_WRITER_EXCEPTIONS`, `DYNAMIC_CONSTRUCT_EXCEPTIONS` не трогать (потолок 0). Маска `mask_phone(stored: str)` -> `+7 *** ***-**-67` (`app/services/phone.py:407`).

---

### `tests/test_scripts/test_backfill_account_phones.py` (test, batch)

**Образец:** `tests/test_scripts/test_recompress_attachments.py`

**Импорт скрипта как модуля** (строки 24-26):
```python
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import backfill_account_phones as script  # noqa: E402
```
По образцу, `# noqa: E402` у импортов `app` после вставки пути.

**Подход:** проверяется ядро `run(...)`, а не боевой прогон; доказательство действия даёт журнал двойника (счётчик вызовов), не счётчик отчёта (см. docstring образца, строки 1-12, и `test_a_dry_run_writes_nothing`, строка 191). Для D-06: двойник `start_container` с нулём вызовов и нулём изменённых строк. Для D-05: счётчик одновременных подключений (инкремент в `connect`, декремент в `disconnect`), `start` как `AsyncMock` с `assert_not_called()`. Для D-09: у занятого аккаунта ноль вызовов `connect`.

**База:** фикстура `db_session` (`tests/conftest.py:44-56`, `sqlite+aiosqlite:///:memory:`). Аккаунты: `tests/account_label_support.py::seed_account(session, user_id, type_=..., phone=..., manual_phone=..., status=...)` (строки 48-60; `credentials="creds"`, для TG-тестов со строкой сессии править двойником выборки).

**Гонка (критерий 2)** — образец `tests/test_application/test_account_phone_race.py:85-110`: файловая база и независимые сессии, потому что на `:memory:` каждая сессия получает свою базу:
```python
engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'race.db'}")
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```
Источник-двойник во время «опроса» вызывает `set_manual_phone` через вторую сессию; затем скрипт зовёт `fill_reported_phone` и обязан получить `KEPT`; ручной номер не затёрт.

**Подмена Telethon:** `tests/test_messengers/test_telegram_user.py:37-45` — `patch("app.messengers.telegram_user.TelegramClient")` с `AsyncMock`; для скрипта патчить `TelegramClient` в модуле скрипта.

**Не закреплять давний дефект** (память `phase-tests-can-pin-preexisting-defects`, D-17): тест «сессия мертва» строить на `is_user_authorized() == False` / `AuthKeyError`, не на `check_connection()`.

**Обязательно в `<automated>` каждого плана:** `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, `tests/test_application/test_phone_single_writer_gate.py` (базовая линия 1161 passed, ~65 с), плюс `tests/test_planning/` после записи планов (RESEARCH B5). Из памяти проекта: называть в диспетчеризации `test_htmx_post_pairs` и прочие сквозные гейты; планы `type: tdd`.

---

### `justfile` (config)

**Образец:** строки 161-175.
```
# Collect group info in prod Docker (dry-run by default)
prod-collect-group-info *args:
    docker compose -f docker-compose.prod.yml exec web uv run python scripts/collect_group_info.py {{ args }}
```
Новые рецепты в той же форме `*args` / `{{ args }}`, с комментарием над рецептом:
```
# Backfill missing account phones. WRITES BY DEFAULT; pass --dry-run to preview
backfill-phones *args:
    uv run python scripts/backfill_account_phones.py {{ args }}

# Backfill missing account phones in prod Docker. WRITES BY DEFAULT; pass --dry-run to preview
prod-backfill-phones *args:
    docker compose -f docker-compose.prod.yml exec -T web uv run python scripts/backfill_account_phones.py {{ args }}
```
Отличия от образца (решения владельца): `exec -T` (D-10; у соседей без `-T`), и комментарий говорит «пишет по умолчанию» (D-08), тогда как у соседей «dry-run by default». Прямых гейтов над `justfile` нет (RESEARCH B5). Код в `web` не монтируется: скрипт попадёт в боевой контейнер только после пересборки образа (деплой-гейт владельца, RESEARCH B4).

---

## Общие паттерны

### Единственный писатель номера
**Источник:** `app/application/accounts/phone.py:111-157` (условный `UPDATE … WHERE phone IS NULL AND phone_is_manual IS false` под `writer_scope()`).
**Применять:** к скрипту целиком. Ни своего `UPDATE`, ни ссылки на `phone_guard`/`writer_scope`, ни присваивания колонкам номера, ни признака «вручную».

### Транзакция принадлежит вызывающему
**Источник:** `phone.py:59` (писатель не коммитит). Скрипт: `commit` на аккаунт, `rollback` при исключении; повторный прогон идемпотентен.

### Итог по исходам обходом перечисления
**Источник:** `scripts/recompress_attachments.py:341-345` (рендер обходом кортежа причин).

### Нет `setup_logging`, вывод только `print` в маскированной форме
**Источник:** `app/services/log_masking.py:89-93` (у скриптов единственный рубеж — статический гейт приватности); `tests/test_services/test_log_masking.py:609-677` (скрипт `setup_logging` не импортирует).

## Образцов нет

| Что | Роль | Причина |
|---|---|---|
| Признак «TG занят» через `celery.control.inspect()` | утилита | в `app/` и `scripts/` нет вызовов `inspect()`; брать RESEARCH A2. Импорт приложения Celery как `app/pages/accounts.py:1051` (`app.worker.celery_app.celery`) |
| Опрос TG-клиента с `receive_updates=False` | источник | ближайшая конструкция `telegram_user.py:329-333` получает обновления; параметр добавляется по RESEARCH A2 |

## Метаданные

**Область поиска образцов:** `scripts/`, `tests/test_scripts/`, `app/application/accounts/`, `app/messengers/`, `app/services/*_container_manager.py`, `justfile`, три гейта номера.
**Дата извлечения:** 2026-11-23
