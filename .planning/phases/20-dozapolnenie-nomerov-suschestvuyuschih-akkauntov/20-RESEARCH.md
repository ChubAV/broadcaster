# Phase 20: Дозаполнение номеров существующих аккаунтов - Research

**Researched:** 2026-11-23
**Domain:** разовая административная команда `just` (скрипт в `scripts/`): опрос источника номера у аккаунтов TG / WA / MAX без номера, запись только единым писателем Фазы 16, итог по исходам в маскированном виде
**Confidence:** HIGH по коду (писатель, менеджеры контейнеров, воркеры WA/MAX, Telethon 1.42.0, PyMax 2.5.0 в образе, гейты Фазы 16 — всё прочитано в этой сессии, предикаты гейтов прогнаны на пробных исходниках); MEDIUM по поведению Telegram (официальная страница утверждает одно, боевой замер показывает другое, см. A1); **LOW по трём вещам, которые без боевого прогона не измерить**: что именно отвечает `/status` боевых воркеров (запрещено вызывать), сколько у владельца спящих WA/MAX-аккаунтов (запрещено читать базу), отдаёт ли сервер MAX номер при восстановлении сессии из `session.db` (путь в коде один и тот же, ответ сервера не измерялся)

**Как читать метки.** `[ЗАМЕР: команда]` — прогнано в этой сессии, результат приведён; `[ПРОЧИТАНО: путь:строки]` — файл открыт `Read`/`sed` в этой сессии, значение процитировано дословно; `[ВЫВОД]` — следствие из двух прочитанных мест; `[ОЦЕНКА]` — суждение без прогона; `[CITED: url]` — официальная документация, открыта в этой сессии; `[ASSUMED]` — знание из обучения, не проверенное (собрано в «Assumptions Log»). Рабочее дерево репозитория не менялось: `git status --short` на конец исследования — только `?? .dockerignore`, как на старте. Боевой стенд читался только разрешёнными командами (`docker ps`, `docker inspect --format` по State/RestartCount/Image, `docker images`, `docker logs --tail`/полный `docker logs` через маску цифр, `docker run --rm --network none --entrypoint sh` по исходникам внутри образа без томов). Ни один контейнер не запускался, не останавливался и не получал `exec`; к сессиям TG/WA/MAX, к HTTP воркеров, к боевой базе и к томам обращений не было. Ни номер, ни JID, ни строка сессии в файл не записаны.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Уже заперто роадмапом, требованиями и решениями прошлых фаз (не пересматривать)
- **D-01:** Номер пишет **только** `fill_reported_phone` из `app/application/accounts/phone.py` (единый писатель Фазы 16, условный `UPDATE … WHERE phone IS NULL AND NOT phone_is_manual`). Своя запись в колонку мимо писателя краснит гейт единственного писателя и `phone_guard`. Признак «указан вручную» скрипт не ставит никогда. Повторный прогон ничего не меняет, а ручной номер, введённый во время прогона, не затирается: это следует из условной записи и проверяется тестом (критерий 2).
- **D-02:** Исходы итога строятся на `PhoneWrite`: `WRITTEN` → «заполнено», `KEPT` → «ручной / уже заполнен», `UNPARSEABLE` и «источник вернул пусто» → «номера нет», `MISSING` → аккаунт удалён во время прогона (отдельная строка итога, не «ручной»: ревью WR-05 Фазы 16). Плюс исходы до писателя: «сессия мертва», «воркер недоступен» (критерий 1). К ним добавляется «занят» (D-08).
- **D-03:** Источники номера переиспользуются из Фазы 19. **WA/MAX:** поле `phone` ответа `/status` воркера (`get_own_phone()` в `app/messengers/whatsapp.py` и `app/messengers/max.py`, `reported_phone_from_status` в `app/messengers/base.py`). Старый образ без поля даёт «номера нет», а не ошибку. **TG:** `connect` → `is_user_authorized` → `get_me()`, `User.phone` (`reported_phone_of` в `app/messengers/telegram_user.py`). Нормализацию делает писатель, источник номер не форматирует.
- **D-04:** **WA/MAX: по умолчанию только работающие воркеры** (PHONE-19, решение владельца, уже закрытое роадмапом). Остановленный контейнер поднимается только по явному флагу и гасится после опроса. Без флага такой аккаунт получает исход «воркер недоступен».
- **D-05:** **TG** опрашивается строго последовательно, изнутри боевого контейнера (`docker compose … exec -T web`), без `start()`, без приёма обновлений, с `disconnect` в `finally` (PHONE-20, критерий 5).
- **D-06:** **`--dry-run`** показывает, что было бы записано, ничего не пишет и не поднимает ни одного контейнера. Тест: ноль вызовов `start_container`, ноль изменённых строк (PHONE-18, критерий 3). Флаг подъёма остановленных под `--dry-run` игнорируется или отвергается, выбирает планировщик. Контейнер подниматься не должен ни в каком случае.
- **D-07:** Номера в выводе скрипта и в журналах только маскированы или заменены признаком наличия (PHONE-21). Гейты номера Фазы 16 называются поимённо в `<automated>` каждого плана: `tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`, `tests/test_application/test_phone_single_writer_gate.py`. Новый файл-писатель (скрипт) должен пройти гейт единственного писателя и гейт приватности как полноправный участник, без нового изъятия.

#### Поведение по умолчанию (решение владельца, 2026-11-23)
- **D-08:** **Без флагов скрипт пишет**, «посмотреть» включается флагом `--dry-run`, как в PHONE-18 и критерии 1. Соседние скрипты (`collect_group_info.py`, `recompress_attachments.py`) устроены наоборот: по умолчанию только показывают, пишут по `--apply`. Здесь это осознанно не повторяется, требование не переписывается. — **Reversibility:** reversible — флаг и умолчание живут в одном скрипте.
  - Рецепты `just` и строка помощи скрипта должны прямо говорить, что запуск без флагов **пишет**, чтобы администратор, привыкший к соседним скриптам, не ошибся.

#### Telegram во время идущей рассылки (решение владельца, 2026-11-23)
- **D-09:** **Занятые TG-аккаунты пропускаются.** Если по аккаунту сейчас идёт рассылка (Celery держит сессию в `TelegramPool` или выполняет отправку), скрипт к его сессии не подключается. Аккаунт получает отдельный исход итога **«занят, повторите позже»**. Повторный прогон его доберёт. Это защита в коде, а не только инструкция «запускать в окно без рассылок».
  - Как распознать «занят» (активная отправка по расписаниям, признак в Redis, блокировка аккаунта, живой клиент пула в другом процессе), выбирает разведка и планировщик. Признак должен быть наблюдаем из контейнера `web`, а не из памяти процесса Celery.
  - Разведка обязана ответить, безопасно ли второе подключение той же сессии в принципе (тот же IP хоста, разные контейнеры) или только когда рассылка не идёт. Если безопасно всегда, исход «занят» всё равно остаётся для активной отправки, а условие сужается до неё.
  - Тест: занятый аккаунт не получает ни одного вызова подключения, исход «занят» попадает в итог, номер не пишется.

#### Принято по умолчанию при делегировании (владелец, 2026-11-23: два вопроса, остальное — по умолчаниям)
- **D-10:** Имя скрипта и рецептов: `scripts/backfill_account_phones.py`, `just backfill-phones` (локально) и `just prod-backfill-phones` (через `docker compose -f docker-compose.prod.yml exec -T web`), как в разведке вехи (`.planning/research/SUMMARY.md`, «Phase 5: Дозаполнение»). *Обоснование:* имя уже названо в записях вехи. Пара «локальный + prod» повторяет соседние рецепты.
- **D-11:** Флаги: `--dry-run`; флаг подъёма остановленных WA/MAX (имя, например `--wake`, выбирает планировщик); фильтры `--type` (tg_user / wa / max), `--account-id`, `--limit`, как в разведке вехи. *Обоснование:* фильтры позволяют сначала прогнать один аккаунт на бою.
- **D-12:** Какие аккаунты обходятся: все без номера и без признака «вручную». Ручные и заполненные отсеиваются выборкой, а писатель повторно страхует от гонки. Статус аккаунта фильтром не служит: для WA/MAX решает «воркер работает» (D-04), для TG — наличие строки сессии. Статус скрипт не меняет никогда (критерий 1). *Обоснование:* исход «сессия мертва» в критерии предполагает, что такие аккаунты опрашиваются и честно классифицируются.
- **D-13:** Вывод: по строке на аккаунт (`#id`, тип, исход, маска номера при «заполнено»), затем итог-счётчики по исходам. Маска — помощником маскирования Фазы 16, своей маски нет. *Обоснование:* по строкам администратор видит, какой аккаунт добрать вручную.
- **D-14:** Транзакцией владеет скрипт. Запись каждого аккаунта коммитится сразу, сбой одного аккаунта не откатывает уже записанные и не останавливает прогон: исключение по аккаунту становится его исходом. *Обоснование:* разовая команда на живой базе, частичный успех ценнее отката. Повторный прогон идемпотентен.
- **D-15:** Код выхода: 0, если прогон дошёл до конца, даже при исходах «номера нет», «воркер недоступен», «занят». Не 0 только при сбое самого прогона (база, аргументы). *Обоснование:* исходы — штатная классификация, а не ошибка.
- **D-16:** Поднятый по флагу контейнер гасится в `finally`, даже при сбое опроса. Контейнер, который уже работал, скрипт не гасит никогда. *Обоснование:* критерий 4.
- **D-17:** Давний дефект `check_connection()` (отозванную TG-сессию считает подключённой) тесты фазы **не закрепляют** как норму. «Сессия мертва» у TG определяется по `is_user_authorized()` / ошибке авторизации, а не по `check_connection()`.

#### Вопросы разведке (`--research-phase` обязателен, пометка роадмапа)
- **R-1:** Источник номера WA/MAX при дозаполнении. Основной путь — `/status` работающего воркера. Подъём по флагу и его побочные эффекты: вход в мессенджер, синк групп, `deleteSessionFiles()` на старте WA при разлогиненной сессии. Нужно понять, может ли подъём по флагу удалить файлы сессии и как этого избежать. Запасной путь — офлайн-чтение `creds.json` одноразовым контейнером с томом `:ro`: оценить и выбрать, нужен ли он вообще.
- **R-2:** MAX. Годится ли `phone.txt` воркера (номер из формы подключения, D-10 Фазы 19: запасной автоматический источник) как запасной источник дозаполнения, если `/status` номер не отдал. Писать его только через `fill_reported_phone`, без признака «вручную».
- **R-3:** TG. Безопасность второго подключения к сессии, которую держит `TelegramPool` в Celery, и наблюдаемый из `web` признак «занят» (D-09).
- **R-4:** Прогон `--dry-run` на копии боевой базы (из пометки роадмапа): как его провести, не трогая боевые контейнеры.

### Claude's Discretion
- Внутреннее устройство скрипта: функции по типам мессенджеров, перечисление исходов (enum), форма строк вывода.
- Имя флага подъёма остановленных и поведение этого флага под `--dry-run` (D-06).
- Таймауты ожидания готовности поднятого контейнера (переиспользовать `wait_for_container_ready`).
- Тест-стенд: моки `start_container` / HTTP-клиента / Telethon по образцу `tests/test_scripts/test_recompress_attachments.py` и тестов писателя Фазы 16.

### Deferred Ideas (OUT OF SCOPE)
- Обновление уже известного автономера (сейчас любой автоисточник пишет только в пустое) — v2+, вместе с возможным `phone_source` (перенесено из Фазы 19).
- Починка `check_connection()` для отозванной TG-сессии — вне вехи (D-17).
- Периодическое (по расписанию) дозаполнение вместо разовой команды — не просили, вне вехи.

*Reviewed Todos (not folded):* `max-worker-pymax-2-5-0-upgrade.md` совпал только по ключевому слову «max»; переход уже сделан (quick-261123-bgc, `d373515e`); в область фазы не входит.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PHONE-17 | администратор одной командой `just` дозаполняет номера аккаунтов без номера; ручные и уже заполненные не трогаются; повторный прогон ничего не меняет; в конце итог по исходам | Писатель `fill_reported_phone` и `PhoneWrite` (B1); выборка колонками, не сущностями (B1, Pitfall 12); классификация `/status` (A6); карта исходов TG (A3); `justfile` (B4); форма вывода, прошедшая предикаты гейтов (B6) |
| PHONE-18 | `--dry-run` показывает, что было бы записано, ничего не пишет и не поднимает контейнеры | Что `--dry-run` делает с TG и что на самом деле затрагивает «копия базы» (A7); запрет `--wake` под `--dry-run`; писатель в `--dry-run` не вызывается (A7); тест «ноль `start_container`, ноль изменённых строк» (Validation) |
| PHONE-19 | по умолчанию опрашиваются только работающие воркеры WA/MAX; остановленные поднимаются только по явному флагу и гасятся после опроса | Ловушка адаптеров: `bridge_url` сам будит воркер (B2, Pitfall 1); «работает» — по Docker, а не по Redis (B3); `deleteSessionFiles()` и подъём (A4); MAX поднимает HTTP сразу, но `connected:false` долго (A5); защита очередью и `finally` (A4) |
| PHONE-20 | TG опрашиваются последовательно, изнутри боевого контейнера, без риска разлогинить сессию (`AuthKeyDuplicatedError`) | Механика AuthKeyDuplicated и общий IP (A1); `receive_updates=False`, `connect` без `start()`, что нельзя писать назад (A2); `TelegramPool` не используется нигде, сигнал «занят» из `web` (A2); ошибки Telethon и их исходы (A3) |
| PHONE-21 | номера не попадают в журналы и в вывод скрипта в открытом виде (сквозное правило, закрыто в Фазе 16) | Что судят гейты и какой должна быть форма `print` (B6); у скриптов нет маски на исполнении (B6); границы О-26 (часть C) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

`[ПРОЧИТАНО: /source/broadcaster/CLAUDE.md, .claude/CLAUDE.md]`. Исполнимые указания, действующие для планировщика:
- Пользовательские команды — через `just` (`just test` = `uv run pytest tests/ -v`; рецепты `just run`, `just migrate`, `just prod-*`). Новые рецепты фазы обязаны следовать форме соседних (`*args`, `{{ args }}`).
- Стек: Python 3.12, `uv`, FastAPI + SQLAlchemy async (PostgreSQL), Celery/Redis. Тесты — `sqlite+aiosqlite:///:memory:` с полной схемой на каждый тест; фикстуры `client`, `db_session`, `auth_headers` из `tests/conftest.py`.
- Исследование кода начинается с `graphify query` / `graphify explain` / `graphify path` (граф `graphify-out/graph.json` есть); после правок кода — `graphify update .` (AST, без стоимости). Правило перенесено на каждый запуск исполнителя.
- `scripts/` — каталог административных скриптов (`cleanup_schedules`, образец оформления — `collect_group_info.py`, `recompress_attachments.py`).
- Ничего из `just prod-*` исследователь не запускал; план обязан считать боевой прогон отдельным шагом владельца после выката (деплой-гейт).

## Summary

Фаза — один скрипт и два рецепта `just`; новых библиотек, маршрутов, форм, миграций нет. Нужные узлы уже есть: писатель с условной записью (`fill_reported_phone`, исходы `WRITTEN`/`KEPT`/`MISSING`/`UNPARSEABLE`), менеджеры контейнеров с `list_worker_containers` / `start_container` / `stop_container` / `wait_for_container_ready`, разбор поля `phone` (`reported_phone_from_status`), `reported_phone_of` для Telethon, маска `mask_phone`. Главная работа фазы — не «как получить номер», а «как не навредить»: пять находок ниже меняют план.

**Пять находок, которых нет в CONTEXT.md и в разведке вехи.**
1. **Адаптеры сами будят воркеры.** `WhatsAppMessenger(session_id=…)` и `MaxMessenger(session_id=…)` без явного `bridge_url` на первом же `_url(...)` зовут `ensure_wa_container` / `ensure_max_container`, а те — `start_container`. Схема из разведки вехи (`create_messenger(account, settings)` и `get_own_phone()`) нарушила бы PHONE-19 и PHONE-18 молча, на каждом остановленном аккаунте. Адрес надо брать у Docker (`list_worker_containers` → `running`) и передавать адаптеру явно, а ещё лучше опрашивать `/status` собственным запросом: `get_own_phone()` схлопывает любой отказ в `None`, поэтому «воркер недоступен», «сессия мертва» и «номера нет» им не различить (A6, B2).
2. **`TelegramPool` не используется нигде.** Предпосылка D-09 «Celery держит сессию в `TelegramPool`» неверна: класс объявлен и упомянут только в своём тесте. Celery открывает клиента Telethon на каждую отправку и закрывает в `finally`; в `celery-worker-telegram` стоит `--concurrency=4`. Сигнал «занят» поэтому не может быть состоянием пула; наблюдаемый из `web` сигнал — `celery.control.inspect()` (`active` + `reserved`) плюс очередь `telegram` в Redis; при неответе — «занят» (A2).
3. **Условие `AuthKeyDuplicated` — не «два разных IP».** Официальная страница Telegram: ошибка выдаётся, когда авторизованная сессия шлёт запросы «from two separate TCP connections, from the same or different IP addresses». Текст в Telethon («two different IP addresses») неточен, а запись разведки вехи «с одного хоста риск низкий» — не подтверждена. Одновременно боевой замер: за ~1,5 часа 482 отправки двух TG-аккаунтов, 243 пары задач одного аккаунта пересеклись во времени (шаг 1 с), и ни одного `AuthKeyDuplicated` в логах трёх контейнеров. Вывод: безопасным второе подключение гарантированно не является, на практике объём отправок его переносит; последовательность, пропуск занятых и короткое соединение остаются обязательными (A1).
4. **Спящий WA/MAX — это почти все аккаунты, и «остановленный» значит «удалённый».** Сейчас на хосте работают 4 воркера (2 WA, 2 MAX). Выходящие по `IDLE_SHUTDOWN_SEC=300` контейнеры удаляет `cleanup_exited_containers()` каждые 15 с, поэтому запасной путь «забрать `creds.json` из остановленного контейнера через `get_archive`» (STACK.md:168) не работает; офлайн остаётся только томом `:ro`. Без `--wake` скрипт заполнит лишь работающие. На WA воркер поднимается и подключается к WhatsApp ДО того, как открывает HTTP, а на MAX — наоборот: HTTP сразу, `connected:false` ещё десятки секунд (A4, A5).
5. **Формулировка Фазы 16 D-01 про «номер MAX в `credentials`» устарела.** После подключения MAX `credentials` перезаписывается `str(account.id)` (`app/pages/accounts.py:1046`; так было уже в первом коммите UI MAX), поэтому у подключённых аккаунтов переносить нечего; число формы живёт только в `phone.txt` воркера. Это вопрос владельцу (O-3), а не работа по умолчанию (часть C).

**Primary recommendation:** один файл `scripts/backfill_account_phones.py` с ядром `run(...)`, в которое внедряются источники (список работающих воркеров, запрос `/status`, подъём/ожидание/остановка, опрос TG, признак «занят»), чтобы тесты не касались ни Docker, ни Telegram, ни сети. Запись — только `fill_reported_phone` (в `--dry-run` писатель не вызывается вовсе, исход предсказывается чтением). WA/MAX — только по адресу, который дал Docker; TG — строго по одному, `receive_updates=False`, `connect` → `is_user_authorized` → `get_me`, `disconnect` в `finally`, пропуск занятых, ошибки Telethon разбираются по классам. Печать — только строки той формы, которую уже прошли гейты (B6). Четыре плана по волнам (раздел «Волны и планы»).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Запуск разовой команды администратором | Хост: `just` → `docker compose exec -T web` | — | PHONE-20: TG только изнутри боевого контейнера; `web` уже монтирует `/var/run/docker.sock` (`docker-compose.prod.yml:108`) и несёт `.env` с `DATABASE_URL`, `REDIS_URL`, `TELEGRAM_API_*` |
| Выборка аккаунтов без номера, итог | API / Backend (скрипт в `web`) | Database / Storage | Чтение колонок `id, type, credentials, status` без загрузки сущностей |
| Запись номера | Application: `fill_reported_phone` | Database | единственный писатель D-01; условие в самом `UPDATE` |
| Определение «воркер работает» | Docker daemon (через SDK) | — | Redis-ключ `wa:endpoint:*` живёт с TTL 420 с и переживает контейнер; Docker — первоисточник |
| Номер WA/MAX | Воркер-контейнер (`/status`) | Docker (подъём по флагу) | поле `phone` Фазы 19; сессия в воркере |
| Номер TG | Сеть Telegram (Telethon-клиент в процессе скрипта) | — | у TG нет воркера; строка сессии в `messenger_accounts.credentials` |
| Признак «TG занят» | Celery-брокер (Redis) и воркер `telegram` | `web` как читатель | `inspect` по pidbox + список `telegram`; в процессе Celery ничего менять не нужно |
| Маскирование вывода | Application-сервис `app/services/phone.py::mask_phone` | Гейт приватности | у процессов `scripts/` маски на исполнении нет — единственный рубеж статический гейт (B6) |

## Standard Stack

### Core (уже в проекте, пины прочитаны; новых пакетов нет)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Telethon | 1.42.0 | клиент TG: `TelegramClient(StringSession(...), api_id, api_hash, receive_updates=False)` | `[ПРОЧИТАНО: uv.lock:2040-2041]` `name = "telethon"` / `version = "1.42.0"`; в `pyproject.toml:30` — `"telethon>=1.37.0"`; параметр `receive_updates` есть в `.venv/.../telethon/client/telegrambaseclient.py:263` (`receive_updates: bool = True,`) |
| docker (SDK) | 7.1.0 | `list_worker_containers`, `start_container`, `stop_container` | `[ПРОЧИТАНО: uv.lock:784-785]`; уже под менеджерами `app/services/*_container_manager.py` |
| httpx | 0.28.1 | запрос `/status` воркера и `/health` | `[ПРОЧИТАНО: uv.lock:1038-1039]`; ту же `httpx` использует `wait_for_container_ready` |
| redis (py) | 6.4.0 | длина очереди `wa:queue:*` / `max:queue:*`, список `telegram` | `[ПРОЧИТАНО: uv.lock:1926-1927]`; синхронный клиент `redis.from_url(settings.redis_url)` как в `app/worker/tasks.py` |
| celery | 5.6.2 | `celery.control.inspect()` для «занят» | `[ПРОЧИТАНО: uv.lock:411-412]`; приложение `app.worker.celery_app.celery` уже ввозится страницами `web` (`app/pages/accounts.py:1051`) |
| phonenumberslite | 9.0.41 | нормализация и маска (внутри `app/services/phone.py`) | `[ПРОЧИТАНО: uv.lock:1399-1400]`; скрипт зовёт только `normalize_reported`, `mask_phone` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest / pytest-asyncio | 9.0.2 / ≥1.3.0 | тесты скрипта | `[ЗАМЕР: .venv/bin/python -m pytest --version]` → `pytest 9.0.2`; образец — `tests/test_scripts/test_recompress_attachments.py` |
| just | 1.45.0 | рецепты | `[ЗАМЕР: just --version]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `/status` работающего воркера, подъём по флагу | офлайн-чтение `creds.json` одноразовым контейнером с томом `:ro` | только WA; новая точка работы с секретами (приватные ключи в `creds.json`), монтирование боевого тома, новый вход образа. Для MAX источника на диске нет. Не нужен в этой фазе (A4) |
| собственный запрос `/status` в скрипте | `get_own_phone()` адаптеров | `get_own_phone()` возвращает `str\|None` и не отличает «недоступен» от «нет номера» (B2). Разбор поля — всё равно `reported_phone_from_status` |
| `inspect` + очередь для «занят» | новый Redis-ключ «TG в работе» на стороне отправки | правка боевого пути отправки ради одного скрипта; обосновано только если `inspect` окажется ненадёжным (A2) |

**Installation:** новых зависимостей нет. **Version verification:** пины прочитаны из `uv.lock` (строки выше); `npm`/`pip index` не запускались, потому что ничего не ставится.

## Package Legitimacy Audit

Фаза не устанавливает внешних пакетов (скрипт и рецепты на уже закреплённых `telethon`, `docker`, `httpx`, `redis`, `celery`, `phonenumberslite`). Проверка `package-legitimacy` не требуется.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | — | новых пакетов нет |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Ответы на вопросы разведки (часть A: внешняя неопределённость)

### A1. Telegram: механика `AuthKeyDuplicated`, IP и сеть контейнеров (вопрос (b), R-3, D-09)

- **Что говорит Telegram.** `[CITED: core.telegram.org/api/errors, раздел 406]`: «An exception to this is the AUTH_KEY_DUPLICATED error, which is only emitted if any of the non-media DC detects that an authorized session is sending requests in parallel from two separate TCP connections, from the same or different IP addresses.» Далее: «opening additional parallel main sessions (i.e. multiple session_ids over the same authorization key, or multiple TCP connections to the main DC) is what triggers this error»; сервер может разрешить несколько параллельных основных сессий, объявив `tmp_sessions` > 1 («When tmp_sessions is absent or ≤ 1, a single main session must be used»); «If the client receives an AUTH_KEY_DUPLICATED error, the session was already invalidated by the server and the user must generate a new auth key and login again.» Страница скачана и прочитана целиком, цитаты дословные.
- **Что говорит Telethon 1.42.0.** `[ПРОЧИТАНО: .venv/lib/python3.12/site-packages/telethon/errors/rpcerrorlist.py:149-152]`: текст ошибки «The authorization key (session file) was used under two different IP addresses simultaneously, and can no longer be used. Use the same session exclusively, or use different sessions». Класс `AuthKeyDuplicatedError(AuthKeyError)`, а `[ПРОЧИТАНО: telethon/errors/rpcbaseerrors.py:86-92]` `class AuthKeyError(RPCError)` с `code = 406`. То есть это **не** `UnauthorizedError`: `get_me()` его не глотает (A3). Telethon `tmp_sessions` в логике клиента не использует: поле читается только в типе `auth.Authorization` (`telethon/tl/types/auth.py:18, 25`), клиент всегда открывает одну основную сессию на своё соединение.
- **Вывод по условию.** Формулировка «только два разных IP» (Telethon, PITFALLS.md:115, SUMMARY.md:158 помечено LOW) официальной страницей не подтверждена: параллельные TCP-соединения с одного IP тоже названы. `[ВЫВОД]`
- **Боевой замер того, как это переносится сегодня.** `[ЗАМЕР: docker logs broadcaster-celery-worker-telegram-1 через sed -E 's/[0-9]{7,}/<n>/g', разбор событий celery_task_start / send_ok / send_failed по task_id и account_id, печать только агрегатов]`: окно с `2026-11-23T09:50Z` (старт контейнера), 482 отправки по 2 TG-аккаунтам, у обоих аккаунтов есть пересекающиеся по времени пары задач (шаг 1 с, пары с совпадающей секундой включены): 243 пары. `[ЗАМЕР: grep -ci "AuthKeyDuplicated|AUTH_KEY_DUPLICATED" по полным логам]`: `broadcaster-celery-worker-telegram-1` 0 из 1696 строк, `web-broadcaster` 0 из 1504, `celery-worker-default-broadcaster` 0 из 2831. Ограничения замера: окно ~1,5 ч (Loki не опрашивался), разрешение 1 с. Причина переносимости (сервер объявил `tmp_sessions` > 1 или определение мягче документированного) не измерена `[ASSUMED]`.
- **Итог для плана.** Второе подключение к сессии аккаунта — тот же шаблон, что уже делает каждая параллельная отправка, но официально не безопасный; последствие при ошибке необратимо (ключ убит, пользователь сканирует QR заново, расписания простаивают). Поэтому D-09 остаётся в силе в узком виде: **не подключаться, пока по аккаунту идёт рассылка** (A2); последовательность и `finally` — обязательны. Остаточный риск, который код закрыть не может: окно между проверкой «не занят» и `connect()`, и подключения, инициируемые пользователем из `web` (синхронизация групп TG, `app/pages/accounts.py:1339`) — они невидимы для `inspect`.
- **Один ли IP у Celery и `web`.** `[ПРОЧИТАНО: docker-compose.prod.yml:159-161]` `networks:` / `default:` / `name: broadcaster` — один пользовательский bridge у `web`, `celery-worker-telegram`, `celery-worker-default` (общий якорь `x-app-base`, у `web` нет `network_mode`). `[ЗАМЕР: docker network inspect broadcaster --format 'driver={{.Driver}} ipv6={{.EnableIPv6}} internal={{.Internal}}']` → `driver=bridge ipv6=false internal=false`; `enable_ipv6` в compose-файлах не задан (`grep -n ipv6 docker-compose*.yml` пусто). У хоста есть IPv6-маршрут по умолчанию (по RA), но сеть контейнеров IPv6 не имеет, и Telethon по умолчанию ходит по IPv4: `[ПРОЧИТАНО: telethon/client/telegrambaseclient.py:245]` `use_ipv6: bool = False,`. Все контейнеры выходят через один NAT хоста, то есть с одного адреса IPv4. `[ВЫВОД]` (адрес на выходе из контейнера не измерялся: `exec` запрещён). Версия «один контейнер на v6, другой на v4» исключена.

### A2. Telegram: хранение сессии, `receive_updates`, `TelegramPool`, сигнал «занят» (вопрос (c))

- **Как сессия попадает в Telethon.** `[ПРОЧИТАНО: app/messengers/telegram_user.py:329-333]`: `TelegramClient(StringSession(session_string), api_id, api_hash)`, строка — `account.credentials` (`app/services/messenger_factory.py`: `session_string=account.credentials`). Файла сессии нет. `[ПРОЧИТАНО: telethon/sessions/string.py:31-70]`: `StringSession.__init__` на непустой строке с первым символом не `'1'` поднимает `ValueError('Not a valid string')`, дальше `struct.unpack`/`base64` могут поднять свои ошибки; **пустая** строка (`if string:` ложно) даёт пустую сессию, и `connect()` начнёт выпуск нового ключа авторизации на DC по умолчанию. `StringSession.save()` возвращает строку и ничего никуда не пишет; `connect()` зовёт `session.save()` и игнорирует результат. Поэтому скрипт обязан до подключения отсеивать строки `credentials`, которые не разбираются (у незавершённых WA-строк в `credentials` лежит `"pending"`, `app/pages/accounts.py:700`; такие же заглушки возможны у любого типа, поэтому проверка нужна и для TG) → «сессия мертва» без обращения к сети.
- **Что скрипт не пишет назад никогда.** Строку сессии (`client.session.save()` в базу не кладётся), `credentials`, `session_data`, `status`, `last_synced_at`, `last_sync_result`; единственная запись — `phone` через писатель. Новый ключ авторизации, если Telethon его вдруг выпустит, остаётся в памяти процесса.
- **`receive_updates=False` в 1.42.0 существует** `[ПРОЧИТАНО: telegrambaseclient.py:205-211, 263, 385]`: «Turning this off means that Telegram will not send updates at all so event handlers, conversations, and QR login will not work.» Механика: `[ПРОЧИТАНО: telegrambaseclient.py:600-601]` («`if self._no_updates:` / `req = functions.InvokeWithoutUpdatesRequest(req)`») инициализирующий запрос оборачивается в `InvokeWithoutUpdatesRequest`, и `[ПРОЧИТАНО: telethon/client/users.py:59-65]` каждый последующий запрос — тоже. Боевая отправка (`TelegramClient(StringSession(...), api_id, api_hash)`) этого не делает: получает обновления.
- **`connect()` в 1.42.0 — не «только соединение».** `[ПРОЧИТАНО: telegrambaseclient.py:605-608]`: если `self._message_box.is_empty()` (у свежего клиента на `StringSession` — всегда), `connect()` сам зовёт `await self.get_me()` и при пользователе — `_on_login(me)`, а `[ПРОЧИТАНО: telethon/client/auth.py:385-405]` `_on_login` делает `GetStateRequest` и `GetDifferenceRequest`. Следствия: (а) `connect()` уже авторизуется и может сам поднять `AuthKeyDuplicatedError` (не `get_me()` после него); (б) последующий `get_me()` — второй такой же вызов (дёшево); (в) `is_user_authorized()` `[ПРОЧИТАНО: users.py:207-227]` берёт кеш `_authorized`, который `_on_login` уже выставил `True`, и лишнего запроса не делает; на неавторизованной сессии делает один `GetStateRequest` и возвращает `False` на ЛЮБОЙ `RPCError`.
- **`TelegramPool` не используется.** `[ЗАМЕР: grep -rn "TelegramPool\|telegram_pool" app/ scripts/ --include=*.py]`: совпадения только внутри `app/messengers/telegram_pool.py` (определение и собственные журналы); экземпляров нет ни в `app/worker/`, ни в `app/pages/`. Упоминается лишь в `tests/test_telegram_pool.py`. Подтверждает и PITFALLS.md:115 («`TelegramPool` в коде объявлен, но не используется»). Боевая отправка: `[ПРОЧИТАНО: app/application/scheduling/use_cases.py:422-448]` `messenger = messenger_factory(account, settings)` → `await messenger.send_message(...)`, а `[ПРОЧИТАНО: telegram_user.py:367-369, 440-444]` `send_message` делает `await self.client.connect()` … `finally: … await self.client.disconnect()`. Клиент живёт секунды.
- **Что наблюдаемо из `web`.**
  - Очередь Celery: `[ПРОЧИТАНО: app/worker/celery_app.py:75-76]` `"app.worker.tasks.send_telegram_message": {"queue": "telegram"}`; `[ПРОЧИТАНО: celery_app.py:100]` `worker_prefetch_multiplier=1,`; `[ПРОЧИТАНО: docker-compose.prod.yml:127]` `--queues=telegram --concurrency=4`; `[ПРОЧИТАНО: app/worker/tasks.py:246-251]` `@shared_task(name="app.worker.tasks.send_telegram_message", bind=True, rate_limit="20/m")` и `def send_telegram_message(self, ad_id, group_id, account_id, schedule_id)`; постановка — `apply_async(args=[task.ad_id, task.group_id, task.account_id, task.schedule_id], queue="telegram")` (`tasks.py:96-100`). `acks_late` не задан, умолчание `False` `[ПРОЧИТАНО: celery/app/defaults.py:261]`: сообщение подтверждается при старте задачи, и **выполняющаяся** задача в Redis-очереди уже не лежит.
  - `celery.control.inspect(timeout=…)`: `[ПРОЧИТАНО: celery/worker/request.py:671-675]` `info(self, safe=False)` отдаёт `'args': self._args if not safe else self._argsrepr`; `Inspect.active(safe=None)` и `reserved(safe=None)` (`celery/app/control.py:136, 168`) возвращают словарь «воркер → список задач» (`reserved` — «not including scheduled/active», то есть предзагруженные). Номер аккаунта — `args[2]`. Широковещание по pidbox через тот же Redis работает из любого контейнера с тем же брокером; `web` ввозит `celery` уже сегодня.
  - Список `telegram` в Redis: заголовок сообщения протокола 2 несёт `argsrepr`. `[ЗАМЕР: Celery('x').amqp.as_task_v2('tid','app.worker.tasks.send_telegram_message', args=[13,1017,20,41]).headers]` → ключи содержат `'argsrepr'` и `'task'`, `argsrepr == '[13, 1017, 20, 41]'`. Форма самого JSON сообщения в Redis (`{"body":…,"headers":{…}}`) здесь не измерена `[ASSUMED]` — планировщику доказать тестом на настоящей полезной нагрузке kombu или не читать список, ограничившись `inspect`.
  - DB-сигналов нет: `SendLog` пишется после отправки; блокировки аккаунта и ключа «TG в работе» не существует. `[ЗАМЕР: grep по app/ на redis-клиентов]` — Redis используют `config`, `admin`, `max`/`whatsapp`-адаптеры, менеджеры контейнеров, `billing_cache`, `ops_state`, `tasks`, `celery_app`; для TG ключей нет.
- **Рекомендуемое правило «занят» (без правок боевого пути).** Аккаунт занят, если в снимке `inspect().active()` ∪ `inspect().reserved()` есть задача `app.worker.tasks.send_telegram_message` с `args[2] == account_id`, ИЛИ в списке `telegram` есть сообщение с таким же `args[2]`. **Не удалось определить** (`inspect` вернул `None` — ни один воркер не ответил, ошибка Redis, нечитаемое сообщение) → «занят» (отказ в закрытую: цена ошибки необратима, цена пропуска — повторный прогон). Снимок брать на каждый аккаунт заново (одно широковещание ≈ таймаут `inspect`), чтобы окно «проверили — подключились» было коротким. `scheduled()` не нужен: ни `countdown`, ни `eta`, ни автоповторов у задачи нет.
- **Минимальная добавка на стороне отправки, если `inspect` не подойдёт** (в рекомендацию не входит): Redis-ключ `tg:inflight:{account_id}` (счётчик с TTL), заводимый в `send_telegram_message` вокруг `_send_message`. Цена: правка боевого пути отправки (шапка `app/worker/celery_app.py` прямо называет такие правки «названной ценой»), тесты `tests/test_worker/test_tasks.py`, выкат Celery; и он всё равно не видит подключений из `web`. Отклонено как избыточное.

### A3. Telegram: что делает `--dry-run`, и карта исходов (вопрос (a), D-17)

- **`--dry-run` и TG.** Чтобы показать «что было бы записано», номер надо получить, а у TG источник — живая сессия: `connect` + `get_me()`. Это не запись в базу и не запуск контейнера (критерий 3 соблюдён буквально), но это то же подключение с тем же риском, что у боевого прогона. Рекомендация: в `--dry-run` TG опрашивается **так же, как в боевом режиме** (последовательно, с пропуском занятых, `receive_updates=False`, `finally`), записи нет; перед опросом печатается строка-баннер «РЕЖИМ ПРОСМОТРА: Telegram и работающие воркеры будут опрошены, запись выключена». Вариант «в `--dry-run` TG не опрашивать» отбрасывает критерий 3 для TG. Администратору, которому нужен совсем бесконтактный просмотр, служит фильтр `--type wa` / `--type max` (D-11).
- **Что `--dry-run` не должен делать.** Не звать писатель даже внутри отката: оператор `UPDATE` держал бы блокировку строки до `rollback`, а тест «ноль изменённых строк» перестал бы быть доказательством отсутствия записи. Исход предсказывается чтением той же строки (`phone IS NULL AND NOT phone_is_manual`) плюс `normalize_reported`; расхождение с боевым прогоном возможно только в гонке, и это допустимо для просмотра.
- **Ошибки Telethon не равны `is_user_authorized() == False`.** `[ПРОЧИТАНО: users.py:219-227]` `except errors.RPCError: self._authorized = False` — `AuthKeyDuplicatedError` (406), `FloodWaitError`, `SessionRevokedError` и т. д. схлопываются в `False`. D-17 («по `is_user_authorized()` / ошибке авторизации») поэтому надо исполнять разбором исключений вокруг `connect()` и `get_me()`, а не одним булевым:

| Наблюдение | Исход | Примечание |
|---|---|---|
| `credentials` пусто или не разбирается как `StringSession` (`ValueError`, `struct.error`, `binascii.Error`) | сессия мертва | без подключения |
| признак «занят» (A2) | занят | без подключения; номер не пишется |
| `connect()` поднял `AuthKeyError` (в том числе `AuthKeyDuplicatedError`) | сессия мертва | сервер уже отозвал ключ; в строке — имя класса, не текст исключения |
| `connect()` / `get_me()` поднял `OSError`, `TimeoutError`, `ConnectionError`, `FloodWaitError` | воркер недоступен | у TG воркера нет: общая «источник недоступен», в строке — класс исключения |
| `is_user_authorized()` вернул `False` или `get_me()` вернул `None` | сессия мертва | `get_me()` на `UnauthorizedError` возвращает `None` (`users.py:177-178`) |
| `get_me()` дал `User`, `reported_phone_of(me)` → `None` | номера нет | `reported_phone_of` тотальна (`telegram_user.py:62-76`) |
| `User` с номером | писатель | `WRITTEN` → заполнено, `KEPT` → ручной / уже заполнен, `MISSING` → удалён во время прогона, `UNPARSEABLE` → номера нет |

  В журнал и в вывод — только имя класса исключения, как это делает Фаза 19 (`self.log.warning("get_own_phone_failed", error_type=type(exc).__name__)`): `str(exc)` у `httpx` и Telethon может нести адрес и тело ответа.
- **Не использовать** `check_connection()` (D-17): `[ПРОЧИТАНО: telegram_user.py:472-479]` `await self.client.connect(); await self.client.get_me(); return True` — отозванная сессия даёт `True`. Тесты фазы этого поведения не закрепляют.

### A4. WhatsApp: что делает `deleteSessionFiles()`, подъём по флагу, состояния воркера (вопрос (f), R-1)

- **`deleteSessionFiles()` не вызывается «на старте безусловно».** `[ПРОЧИТАНО: wa_worker/index.js:153-159]` функция `rmSync` каталога сессии аккаунта. Вызовов два: `[ПРОЧИТАНО: index.js:302-314]` в обработчике `connection === 'close'`: `const unrecoverable = [DisconnectReason.loggedOut, DisconnectReason.forbidden, 405];` и `if (unrecoverable.includes(statusCode)) { … session = null; deleteSessionFiles(); … }` (не при `intentionalClose`), и `index.js:421` внутри `destroySession()` (маршрут `DELETE /api/sessions/:id`). Коды: `[ПРОЧИТАНО: node_modules/@whiskeysockets/baileys/lib/Types/index.js:15-24 в образе]` `loggedOut = 401`, `forbidden = 403`; значения 405 в перечне нет — `[ЗАМЕР: grep -rn "405" lib]` по Baileys rc14 ничего не нашёл; `[CITED: github.com/WhiskeySockets/Baileys, обсуждения #1939, #999, #1242 (результаты поиска)]` — 405 в таких обсуждениях это «Connection Failure» с причинами «несовместимая версия WA Web» и «блокировка адреса хоста»; детали не проверялись `[ASSUMED]`.
- **Может ли подъём по флагу уничтожить ещё живую сессию.** На старте `main()` вызывает `ensureSession()`, если на диске есть `creds.json` (`index.js:980-988`), та создаёт сокет по существующим данным. Файлы стираются, если WhatsApp ответил на это подключение 401 (сессия уже отозвана), 403 (бан) или 405. Для 401/403 стирается то, что и так мертво; для 405 — теоретически валидная сессия при несовместимой версии или блокировке адреса. Но это **тот же путь, которым идёт любая плановая отправка** в спящий аккаунт (`ensure_wa_container` → `start_container`): флаг не вводит нового класса риска, он применяет его к аккаунтам, у которых плановых отправок может не быть. `[ВЫВОД]` Версию воркер берёт свежую: `fetchLatestBaileysVersion()` на старте (`index.js:949-955`).
- **Как флаг этого избегает (рекомендация).** (1) Будить только по явному флагу, последовательно, по одному; (2) перед подъёмом — длина очереди `wa:queue:{id}` / `max:queue:{id}` равна нулю (иначе боевой менеджер сам разбудит воркера, а гасить его после этого нельзя); (3) будить только аккаунты `status == "active"` (для `connecting`/`disconnected`/`sync_failed` подъём бессмыслен, а у MAX может запустить вход по QR) — это сужение D-12 только на пути подъёма, не на пути по умолчанию; (4) после опроса гасить `stop_container` только если контейнер подняли мы И очередь по-прежнему пуста; (5) под `--dry-run` флаг отвергается ошибкой аргументов (код 2), а не молча игнорируется; (6) в справке флага — слова «это вход в WhatsApp/MAX; воркер сам удалит файлы сессии, если мессенджер ответит 401/403/405». Полный отказ от WA под флагом потребовал бы переписать PHONE-19 («остановленные поднимаются только по явному флагу»), поэтому оставлен вопросом владельцу (O-1).
- **Состояние воркера и ответ `/status`.** `[ПРОЧИТАНО: index.js:746-766]`: при `!session` — `res.json({ connected: false, exists, syncState: null })` (поля `phone` нет вовсе); при живом объекте сессии — `{ connected: session.isConnected, exists: true, syncState: session.syncState, phone: ownPhoneFromMe(session.sock?.user, { isPnUser, jidDecode }) }`. `[ПРОЧИТАНО: baileys/lib/Socket/socket.js:931-933 в образе]` `get user() { return authState.creds.me; }` — живое чтение, значит `phone` у восстановленной сессии может быть непустым ещё до `connection: 'open'`.
- **Порядок старта WA: HTTP поднимается ПОСЛЕ сессии.** `[ПРОЧИТАНО: index.js:980-993]`: `await ensureSession()` стоит до `app.listen(...)`; а `ensureSession` ждёт `readyPromise`, который решается на `open`, отвергается на невосстановимом отключении и **не решается вовсе** на восстановимых отключениях (`index.js:315-337` создаёт новый сокет, а `readyPromise` первого остаётся висеть). Живой пример: `[ЗАМЕР: docker logs wa-worker-48, только имена событий]` в последнем запуске цепочка `worker_starting > wa_version > redis_connected > endpoint_registered > session_autoloading > session_loading > disconnected > reconnecting (×5) > max_reconnect_reached > reconnect_failed` — и **ни `consumer_started`, ни `http_server_started`**: контейнер `Up` 2 суток по Docker, HTTP не слушает (код причин — 408 timedOut, `"reason":"timedOut","statusCode":408`). Следствия: (а) «контейнер running» не означает «HTTP отвечает»; (б) `wait_for_container_ready` на WA ждёт установления сессии и должен получать окно больше 30 с по умолчанию; (в) в висящем воркере нет и цикла простоя, поэтому осиротевший воркер сам не гаснет.
- **Фоновый синк групп.** `[ПРОЧИТАНО: index.js:164-174, 285-289]`: на `open` стартует `startGroupSync()` с `INITIAL_DELAY = 30000` — если опросить и погасить за 30 с, `groupFetchAllParticipating` не успеет вызваться. Подключение `Browsers.ubuntu('Broadcaster')` — связанное устройство, видимое владельцу телефона.
- **Остановка сохраняет файлы.** `[ПРОЧИТАНО: index.js:674-683]` `gracefulShutdown`: «Close Baileys socket (keep session files on disk)», `session.sock.end()` при `intentionalClose = true`.
- **«Остановленный» контейнер обычно уже удалён.** `[ПРОЧИТАНО: app/worker/tasks.py:653-687, 682]` `manage_wa_containers` вызывает `cleanup_exited_containers()`; `[ПРОЧИТАНО: celery_app.py:83-86]` расписание `"manage-wa-containers": {… "schedule": 15.0,}`; `[ПРОЧИТАНО: wa_container_manager.py:119-131]` `cleanup_exited_containers` удаляет все `exited` с меткой роли. Запасной путь STACK.md:168 (`container.get_archive('/app/sessions/<id>/creds.json')` у остановленного контейнера) работает только в 15-секундном окне; для спящих аккаунтов нереален.
- **Офлайн-чтение `creds.json` — нужно ли.** Решение: **не нужно в этой фазе.** Доводы: (1) подъём по флагу — путь, которым боевая система и так идёт на каждой плановой отправке; (2) офлайн-путь это одноразовый контейнер с монтированием боевого тома `broadcaster_wa_sessions` (`SESSIONS_VOLUME`, `wa_container_manager.py:17`) и чтением файла с приватными ключами, новый вход образа или команда, новые тесты и гейты на «секрет не выходит наружу»; (3) работает только для WA, у MAX номера на диске нет (A5); (4) выигрыш — отсутствие входа в WhatsApp у спящих аккаунтов, но владелец сам принял подъём по флагу (PHONE-19). Если первый боевой прогон `--wake` на WA покажет удалённые сессии, вернуться к офлайн-пути отдельным решением. Вопрос владельцу — O-1 (вариант в).
- **Единичное окно подъёма (рекомендуемая последовательность).** Для WA: `start_container(account_id)` → `wait_for_container_ready(account_id, timeout=90.0)` → один `GET /api/sessions/{id}/status` → классификация (A6) → `stop_container(account_id)` в `finally` (если подняли мы и очередь пуста). Для MAX: `start_container(account_id)` → `wait_for_container_ready` → опрос `/status` каждые ~2 с до `connected: true` или до предела ~90 с → `stop_container` в `finally`.

### A5. MAX после PyMax 2.5.0: восстановление сессии и `phone.txt` (вопрос (e), R-2)

- **Источник номера в воркере.** `[ПРОЧИТАНО: max_worker/main.py:224-239]` `own_phone_of(client)` читает `client.me.contact.phone` и принимает только положительный `int` (`"Source: ``client.me.contact.phone`` of pymax 2.5.0 (``types/domain/user.py``), filled by the LOGIN answer before ``on_start`` runs."`). Захват — в `on_start` (`main.py:472-493`): `state.own_phone = own_phone_of(connected_client)` выполняется ДО `state.is_connected = True`, поэтому ответ `connected: true` уже содержит окончательный `phone` (гонки «подключён, но номера ещё нет» у MAX нет).
- **Заполняется ли `client.me` при восстановлении сессии из `session.db`.** Да, по коду: `[ПРОЧИТАНО: pymax/app.py:97-199 в образе broadcaster-max-worker:latest]` ветка «saved session» (`session_data` найдена) пропускает аутентификацию по QR (`if not session_data:` …), затем в обоих случаях исполняется `login_response, login2_response = await self.login()` и присваивание `self.me = login2_response.profile` / `self.me = login_response.profile`. Модель: `[ПРОЧИТАНО: pymax/types/domain/user.py:71]` `phone: int | None = None`, docstring «Телефон пользователя, если возвращен API». Образ: `[ЗАМЕР: docker run --rm --network none --entrypoint sh broadcaster-max-worker:latest -c 'python -c "import pymax;print(pymax.__version__)"']` → `2.5.0`. Не измерено (запрещено вызывать воркеры): что в этом ответе сервер MAX присылает `contact.phone` именно при входе по токену; при QR-входе присылает (ответ A3 Фазы 19, `19-UAT.md`, «MAX отдаёт номер при QR-входе»). Один и тот же LOGIN-ответ в обоих случаях — основание считать, что присылает и здесь `[ОЦЕНКА]`. Подтверждается первым боевым шагом `--dry-run --account-id 19` на уже работающем `max-worker-19` (запущен на образе PyMax 2.5.0 `[ЗАМЕР: docker inspect]` в `11:01Z`, восстановил сессию из `session.db`).
- **Особенность восстановления с отозванным токеном.** `[ПРОЧИТАНО: .planning/quick/261123-bgc-…/261123-bgc-SUMMARY.md, строка про relogin]` «revoked token + `relogin` -> restart auth (`base.py:205-236`)`»: воркер удаляет строку сессии и показывает QR; `/status` тогда `connected:false` без `phone`. Это «сессия мертва», а не «воркер недоступен», но по `/status` от «подключается ещё» его не отличить (A6).
- **Порядок старта MAX: HTTP сразу.** `[ПРОЧИТАНО: main.py:906-934]` `lifespan`: `await create_client(phone)` возвращается сразу (`asyncio.create_task(_run_client(...))`, `main.py:500-505`), `consumer_task` стартует следом, FastAPI отвечает на `/health` и `/status` немедленно; `/status` до `on_start` — `{ connected: false, exists: true, syncState: null, phone: null }` (`main.py:1022-1033`). Скрипту после подъёма MAX нужен ограниченный опрос, а не одиночный GET; одиночный дал бы «номера нет» на каждом свежеподнятом воркере (PITFALLS.md, ловушка 6).
- **Группы и побочные эффекты подъёма MAX.** `on_start` запускает `_safe_group_sync()` сразу (`main.py:495-498`, без 30-секундной задержки, как у WA). Побочный эффект на базу отсутствует (воркер в неё не пишет), нагрузка — сетевая.
- **`phone.txt`.** `[ПРОЧИТАНО: main.py:305-317]` `save_phone_to_disk(phone)` пишет `(d / "phone.txt").write_text(phone.strip())`; `load_phone_from_disk()` читает обратно; пишется в `create_client`, если `phone` непустой (`main.py:445-446`) — то есть это **число формы подключения**, а не номер сессии. Воркер его не отдаёт: `main.py:199-202` «The form number (self.phone) is never served: the owner decided that a typed number must not pass for a reported one (OQ1).» Тест Фазы 19 (`19-UAT.md`, проверка 2): ввёл один номер, отсканировал QR другим аккаунтом — в списке показан номер сканировавшего.
- **Годится ли `phone.txt` как запасной источник дозаполнения.** Решение: **нет.** (1) Прочитать его можно только с тома `broadcaster_max_sessions` (воркер не отдаёт) — либо новое поле `/status` (правка воркера, пересборка образа, выкат ради запасного пути), либо монтирование тома с `session.db` (токены); (2) число формы не проверено и по замеру Фазы 19 может быть чужим; (3) запись пойдёт как автоматический номер (без признака «вручную») и, как отметило ревью 19 (IN-03), никогда не исправится, так как автоисточники пишут только в пустое — Фаза 20 растиражировала бы этот остаточный дефект на все старые аккаунты MAX; (4) уцелевшие работающие/поднятые воркеры отдают настоящий номер через `client.me`. Вопрос владельцу — O-2.

### A6. Классификация ответа `/status` WA/MAX (вопрос (d))

Скрипт делает свой запрос `GET {endpoint}/api/sessions/{account_id}/status` (адрес — от Docker, B3; таймаут соединения ~3 с, общий ~10 с; один запрос на аккаунт, у MAX — серия до `connected: true`), тело разбирает `reported_phone_from_status` (`app/messengers/base.py:16-35`: словарь → непустая строка как есть или целое > 0 строкой, `bool` целым не считается, прочее `None`). `get_own_phone()` для этого не годится: `[ПРОЧИТАНО: whatsapp.py:155-163, max.py:146-154]` любой отказ — не-200, не-JSON, нет поля, сбой транспорта — возвращает `None` и тем самым смешивает «недоступен» и «нет номера».

| Наблюдение | Исход | Живой пример на 2026-11-23 |
|---|---|---|
| контейнера нет или он не `running`, флага подъёма нет (или статус не `active`) | воркер недоступен | подавляющее большинство аккаунтов (работают 4 воркера) |
| `running`, но запрос не прошёл: отказ в соединении, таймаут, не-200, не-JSON, не словарь | воркер недоступен | `wa-worker-48` (HTTP не слушает, см. A4) |
| 200, `connected` не `true`, `exists` ложно | сессия мертва | `wa-worker-21`: в последнем запуске нет `session_autoloading` (на диске нет `creds.json`), каждая задача падает с «WhatsApp session not available» |
| 200, `connected` не `true`, `exists` истинно | воркер недоступен (связь с мессенджером не установлена; у WA — цикл переподключения, у MAX — вход/QR; отличить «ещё подключается» от «нужен QR» по этому ответу нельзя, строка итога несёт слово «не подключён») | — |
| 200, `connected: true`, в теле нет ключа `phone` | номера нет, заметка «образ воркера без поля phone» | `wa-worker-48`, если бы HTTP отвечал: контейнер запущен 2026-11-20, то есть до коммита `babfe18f` (2026-11-22, поле `phone` в WA-воркере), и идёт на образе, отличном от нового `aa71b18b8028` `[ВЫВОД]` |
| 200, `connected: true`, `phone` пустой или мусор | номера нет | — |
| 200, `connected: true`, годный `phone` | писатель → заполнено / ручной или уже заполнен / удалён во время прогона / номера нет | `max-worker-19`, `max-worker-28` (образ PyMax 2.5.0, оба работают; значение `/status` не измерялось) |

Заметка по `connected`: рекомендуется требовать `connected: true` (как Фаза 19: номер читается только после `check_connection()` с `connected: true`), хотя для WA `phone` бывает и без него (A4). Альтернатива — принимать `phone` и при `connected: false`: даёт больше заполненных строк на сессиях в цикле переподключения, но размывает смысл «сессия мертва»; решение за планировщиком (Open Questions, группа (б)).

### A7. Прогон `--dry-run` «на копии боевой базы» (вопрос (a), R-4)

Копия базы **не изолирует** скрипт: изолирует окружение. Что затрагивает прогон на копии на самом деле (при прежнем окружении боевого `web` или хоста с боевым `.env`):
1. **Строки сессий TG.** `credentials` у `tg_user` — это `StringSession`, то есть сам ключ авторизации. Копия переносит секреты с боевого хоста; запуск скрипта с другого адреса, пока Celery шлёт с боевого — буквально «два разных IP одновременно» (A1) и необратимая потеря ключа.
2. **Рабочие контейнеры.** Идентификаторы аккаунтов в копии совпадают с боевыми, имена `wa-worker-<id>` / `max-worker-<id>` разрешаются в сети `broadcaster`, а `docker.sock` скрипт берёт из окружения: `list_worker_containers`/`start_container`/`/status` дойдут до настоящих воркеров.
3. **Redis и Celery.** `REDIS_URL` из того же `.env` — признак «занят» и очереди читаются боевые.
4. **Telegram.** Сеть наружу у контейнера по умолчанию есть.

**Процедура, если владелец всё же хочет копию (вариант (б) вопроса O-4).** Изолированный проект compose с отдельной сетью (без `broadcaster`), Postgres из дампа ТОЛЬКО таблицы `messenger_accounts` (+ `alembic_version`), сразу после восстановления `UPDATE messenger_accounts SET credentials = ''` ДО первого запуска скрипта; контейнер скрипта без монтирования `/var/run/docker.sock`, с `REDIS_URL` на недоступный адрес, `TELEGRAM_API_ID=0` и без выхода наружу. Ожидаемый результат: все TG → «сессия мертва» (пустая строка отсеивается до подключения), все WA/MAX → «воркер недоступен» (Docker недоступен — для такого прогона скрипт должен считать это исходом по аккаунту, а не аварией прогона; решение планировщика). Проверка «ничего не записано»: до и после `SELECT count(*), count(phone), md5(string_agg(coalesce(phone,''), ',' ORDER BY id))`. **Чего копия измерить не может:** реальные исходы источников и время опроса. Они видны только на боевом `web` командой `--dry-run --account-id <один>`, а это боевой шаг после выката и вне критериев фазы. Рекомендация — не копировать боевую базу вовсе (O-4, вариант а): выбор, объём, формат вывода и «ноль записей» уже доказываются тестами на синтетических данных, а настоящие исходы — первым боевым `--dry-run --account-id`.

## Интеграционные точки в репозитории (часть B)

### B1. Писатель Фазы 16 — как сегодня
`[ПРОЧИТАНО: app/application/accounts/phone.py:92-108, 111-157]`: `class PhoneWrite(enum.Enum)` — `WRITTEN = "written"`, `KEPT = "kept"`, `MISSING = "missing"`, `UNPARSEABLE = "unparseable"`. `fill_reported_phone(session, account_id, raw) -> PhoneWrite`: мусор → `UNPARSEABLE` без обращения к базе; иначе `_fill_if_unknown`: `await session.flush()` вне разрешения, затем один `UPDATE … WHERE id == :id AND phone IS NULL AND phone_is_manual IS false` под `writer_scope()` с `synchronize_session=False, autoflush=False`; `rowcount == 1` → `WRITTEN`, иначе проба существования `select(exists().where(MessengerAccount.id == account_id))` → `KEPT` или `MISSING`. Писатель **не коммитит** (`phone.py:59`: «не коммитит: транзакцией владеет вызывающий … скрипт Фазы 20»): скрипту нужен `await session.commit()` после каждого аккаунта (D-14) и `rollback` при исключении, чтобы сессия оставалась рабочей. Нормализатор `normalize_reported` публичный (`app/services/phone.py:346`). Объект, загруженный в ту же сессию, после записи устаревает: выборку делать колонками (`select(MessengerAccount.id, MessengerAccount.type, MessengerAccount.credentials, MessengerAccount.status)`), не сущностями — тогда нет грязных объектов, нет риска, что ORM выдаст второй UPDATE, и строка сессии TG не висит в памяти дольше нужного.

### B2. Адаптеры WA/MAX сегодня — ловушка пробуждения
`[ПРОЧИТАНО: app/messengers/whatsapp.py:68-84]`: `__init__(self, bridge_url=None, session_id="")`, `self._bridge_url = bridge_url.rstrip("/") if bridge_url else None`; свойство `bridge_url`: если адрес не задан — `endpoint = ensure_wa_container(int(self.session_id))`. `[ПРОЧИТАНО: whatsapp.py:25-43]` `ensure_wa_container` вызывает `start_container(account_id)` и `wait_for_container_ready`. У MAX то же: `[ПРОЧИТАНО: app/messengers/max.py:25-34, 59-75]` `ensure_max_container` → `start_container(account_id)` (если нет ключа `max:endpoint:{id}` в Redis). `_url()` берёт `self.bridge_url`, поэтому **любой** вызов метода адаптера без явного `bridge_url` (`create_messenger`, `get_own_phone()`) на остановленном аккаунте поднимает контейнер. Тест в `tests/test_messengers/test_whatsapp.py:7-23` закрепляет именно это поведение (`mock_start_container.assert_called_once_with(42)`). Для скрипта: адаптер создавать только с `bridge_url`, взятым у Docker для работающего контейнера, а лучше не создавать вовсе (A6). Разведка вехи (`ARCHITECTURE.md:105`: «получает адаптер через уже существующий `create_messenger(account, settings)` и не ветвится по типу») этого не учла.

### B3. Менеджеры контейнеров
`[ПРОЧИТАНО: app/services/wa_container_manager.py:13-19]`: `WA_WORKER_IMAGE = "broadcaster-wa-worker:latest"`, `CONTAINER_PREFIX = "wa-worker-"`, `CONTAINER_LABEL = "broadcaster.role=wa-worker"`, `NETWORK_NAME = "broadcaster"`, `SESSIONS_VOLUME = "broadcaster_wa_sessions"`, `DEFAULT_PORT = 3000`; MAX — `[ПРОЧИТАНО: max_container_manager.py:13-19]` `MAX_WORKER_IMAGE = "broadcaster-max-worker:latest"`, `CONTAINER_PREFIX = "max-worker-"`, `CONTAINER_LABEL = "broadcaster.role=max-worker"`, `SESSIONS_VOLUME = "broadcaster_max_sessions"`. Функции в обоих модулях с одинаковой формой: `list_worker_containers() -> list[dict]` (`all=True`, поля `account_id`, `name`, `status`, `short_id`), `get_container_endpoint(account_id)` (`running` → `http://{name}:3000`, иначе `None`), `start_container(account_id)` (MAX — `start_container(account_id, phone="")`; на существующем `running` возвращает адрес, на остановленном `remove(force=True)` и пересоздаёт), `stop_container(account_id) -> bool` (`stop(timeout=10)` + `remove()`), `wait_for_container_ready(account_id, *, timeout=30.0, interval=1.0)` — опрос `/health`, **синхронный** (`time.sleep`, `httpx.get`): в async-скрипте звать через `asyncio.to_thread` или принять блокировку цикла (скрипт последовательный). «Работает» определять одним вызовом `list_worker_containers()` на тип (карта `account_id → status == "running"`), а не Redis-ключами `wa:endpoint:*`/`max:endpoint:*` (TTL 420 с, `tasks.py:676`, переживают контейнер). Для WA/MAX-аккаунта подъём — те же `start_container(account_id)` без `phone` (как `ensure_container_for_pending_work`, `max_container_manager.py:167-187`).

### B4. `justfile`, Dockerfile, compose
`[ПРОЧИТАНО: justfile:161-175]` пары рецептов: `collect-group-info *args:` → `uv run python scripts/collect_group_info.py {{ args }}` и `prod-collect-group-info *args:` → `docker compose -f docker-compose.prod.yml exec web uv run python scripts/collect_group_info.py {{ args }}`; такая же пара у `recompress-attachments`. Существующие боевые рецепты идут **без `-T`**; D-10 требует `exec -T`. `[ЗАМЕР: just --dry-run prod-collect-group-info --x]` → `docker compose -f docker-compose.prod.yml exec web uv run python scripts/collect_group_info.py --x`. Образ `web` собирается с `COPY . .` (`Dockerfile:20`), `.dockerignore` не исключает `scripts/` (`.git`, `.pytest_cache`, `graphify-out`, `.planning`, `**/__pycache__`), а код в контейнер **не монтируется**: новый скрипт попадёт в боевой `web` только после пересборки образа приложения (деплой-гейт владельца). Рецепт локальный `backfill-phones` на хосте читает `.env` хоста: если `DATABASE_URL` указывает на боевую базу, TG пойдёт с чужого адреса (A1) — см. Open Questions (б), защита «TG только в контейнере».

### B5. Другие потребители тех же гейтов и общие счётчики
`[ПРОЧИТАНО: tests/test_services/test_log_masking.py:609-612, 657-664, 666-677]`: `_measure_scripts` обходит `scripts/*.py` и краснит, если файл ввозит или зовёт `setup_logging`; правило `test_the_processes_without_setup_logging_are_measured_and_named` — новый скрипт `setup_logging` не импортирует. `[ПРОЧИТАНО: tests/test_planning/test_plan_prohibitions_census.py:4002-4009]` `YAML_DIRECT_IMPORTERS` и `YAML_SCAN_DIRECTORIES = ("app", "scripts", "tests")`: скрипт `yaml` не импортирует. `tests/test_planning/test_executed_plans_kept_their_scope.py:228,238` перечисляет `scripts/` и `justfile` как «продукт» для коммитов исполненных планов прошлых фаз — исторически, новое не краснит. Прямых гейтов над `justfile` нет (`grep -rn "justfile" tests/` находит только `conftest.py` в комментарии и перечень выше). Объявленные числа маршрутов/форм (`MUTATING_ROUTE_COUNT`, `WRITE_FORM_PLACES`, `PAIRED_302_ASSERTIONS_DECLARED`, `FRAGMENT_RESPONSE_HANDLERS_DECLARED` и др., таблица B11 в `19-RESEARCH.md`) не сдвинутся: фаза не добавляет ни POST, ни `<form>`, ни OOB. Число планов реестра запретов `test_plan_prohibitions_census.py` реагирует на новые ПЛАНЫ с `prohibitions` — прогнать `tests/test_planning/` после записи планов.

### B6. Гейты номера: что судят и какой должна быть форма скрипта (вопрос (g), D-07)

Все четыре рубежа прочитаны; предикаты прогнаны на пробном исходнике (см. «Измеренные формы»).

| Гейт | Вселенная | Что краснит в скрипте | Исключения |
|---|---|---|---|
| Приватность `tests/test_phone_privacy_gate.py` (`test_no_number_reaches_a_python_log_call_in_the_live_trees`, строка 5336; `test_no_dynamic_construct_in_the_python_trees`, 5352; `test_every_gate_tree_is_walked`, 5981) | `[ПРОЧИТАНО: :826,829]` `GATE_TREES = ("app", "scripts", "wa_worker", "max_worker")`, `PYTHON_TREES = ("app", "scripts", "max_worker")` — `scripts/` внутри | любой вызов журнала, **включая `print`**, у которого в аргументах: имя/атрибут/именованный аргумент/ключ словаря, содержащие `phone` (`_mentions_phone`: `"phone" in name.lower()`, кроме `phone_set` булевой формы); строка, похожая на номер; вызов `mask_phone(...)` **вне** `print` под `scripts/` | `[ПРОЧИТАНО: :836,839]` `PHONE_LOG_EXCEPTIONS: dict[str, str] = {}`, потолок `PHONE_LOG_EXCEPTIONS_CEILING = 0` — нового изъятия нет и не будет |
| Единственный писатель `tests/test_application/test_phone_single_writer_gate.py` (`test_no_phone_write_outside_the_writer_in_the_live_tree`, 3891; `test_no_dynamic_construct_in_the_writer_trees`, 3927; `test_the_runtime_guard_is_entered_only_by_the_writer`, 9242) | `[ПРОЧИТАНО: :925]` `WRITER_TREES = ("app", "scripts")` обходом `rglob("*.py")` — новый файл попадает сам | запись колонок `phone`/`phone_is_manual` любой из восьми форм (`values`/`update`/`insert`/конструктор `MessengerAccount(...)` с этими ключами, `setattr`, `set_committed_value`, `flag_modified`, `bulk_*`, `ordered_values`, присваивание атрибуту…); ссылка на `phone_guard`/`writer_scope`/`_WRITER_ACTIVE` вне писателя; динамические конструкции | `[ПРОЧИТАНО: :1348-1353]` `PHONE_WRITER_EXCEPTIONS` ровно одна запись — `PHONE_WRITER_MODULE = "app/application/accounts/phone.py"` |
| Паритет `tests/test_phone_gates_parity.py` | модули самих гейтов | к содержимому скрипта не относится; краснеет, только если кто-то правит общую грамматику `tests/phone_gate_grammar.py` | — |
| Защита на исполнении `app/models/phone_guard.py` | любой процесс, ввозящий `app.models` | запись колонок номера вне `writer_scope()` (ORM-событие, `before_cursor_execute` на классе `Engine`) отказывает `PhoneWriteOutsideWriter` | границы О-26 — часть C |

Следствия для скрипта:
- **Чтение колонки разрешено** (`select(...).where(MessengerAccount.phone.is_(None), MessengerAccount.phone_is_manual.is_(False))`). Конструктор `MessengerAccount(...)`, `update(...)`, `.values(...)`, присваивания атрибутам номера и прочие записи — нет.
- **`print` — единственный вывод, и он единственный рубеж.** `[ПРОЧИТАНО: app/services/log_masking.py:89-93]` («ГРАНИЦА»): «`print` … судит статический гейт приватности»; «процессы, не вызывающие `setup_logging` … скрипты `scripts/` … там статический гейт приватности — единственный рубеж». Маски на исполнении у скриптов нет.
- **Форма строки.** `[ПРОЧИТАНО: tests/test_phone_privacy_gate.py:1854-1857]` внутри вызова журнала `if isinstance(node, ast.Call) and _callee_name(node.func) == MASK_FUNCTION: if not mask_for_a_reader: found.append(…); continue` — для `print` под `scripts/` (`mask_for_a_reader = in_scripts and _is_print(call)`, строка 1910) вызов `mask_phone(...)` пропускается целиком, аргументы не судятся; всё прочее в аргументах `print` судится. Поэтому: переменная с номером называется без слова `phone` (`reported`, `e164`, `masked`), `mask_phone(...)` стоит прямо в `print` или результат кладётся в переменную без `phone` в имени, в тексте строки нет цифр, похожих на номер.
- **Динамика запрещена** (девять видов `DYNAMIC_CONSTRUCT_KINDS`: `getattr(x, "строка")` с именем запрещённой роли, `setattr`, `globals()`, `vars()`, `__import__`, `importlib`, `eval`/`exec`, `operator.methodcaller`/`attrgetter`, `functools.partial(getattr, …)`, `def __getattr__`, `sys.modules[__name__]`). Выбор по типу — явный `if/elif` или словарь функций, не `getattr(module, name)`. Тип `Outcome` — `enum.Enum`, доступ `Outcome.FILLED` (не `getattr`).
- **Без новых изъятий** — это и есть критерий D-07: ни одна запись в `PHONE_LOG_EXCEPTIONS`, `PHONE_WRITER_EXCEPTIONS`, `DYNAMIC_CONSTRUCT_EXCEPTIONS`.

**Измеренные формы.** `[ЗАМЕР: .venv/bin/python, импорт tests.test_phone_privacy_gate / tests.test_application.test_phone_single_writer_gate, функции python_log_offences, phone_write_offences, dynamic_construct_findings над пробным исходником под виртуальным путём scripts/backfill_account_phones.py]`:
- Пробный исходник (выборка колонок с `.where(MessengerAccount.phone.is_(None), MessengerAccount.phone_is_manual.is_(False))`, `reported = reported_phone_from_status(body)`, `e164 = normalize_reported(reported)`, `print(f"#{account_id} {kind} {Outcome.NO_NUMBER.value}")`, `print(f"#{account_id} {kind} было бы заполнено {mask_phone(e164)}")`, `written = await fill_reported_phone(session, account_id, reported)` с последующим `print(... {Outcome.FILLED.value} {mask_phone(e164)})`, `enum.Enum`, `argparse` с `--dry-run`) → **`privacy offences: []`, `writer offences : []`, `dynamic : []`**.
- Контроль-отрицание (пять строк: `print(f"#{account.id} {account.phone}")`, `print(f"#{account.id} {phone}")`, `print(f"{mask_phone(e164)} {phone}")`, `print("+7 999 123-45-67")`, `print(reported_phone)`; присваивание `account.phone = …`) → privacy: пять находок на строках 7, 8, 9, 10, 12 (видов «имя» ×4 и «литерал»), writer: `присваивание — account.phone`. То есть предикаты не вакуумны на этой форме.
- Базовая линия гейтов: `[ЗАМЕР: .venv/bin/python -m pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly]` → **1161 passed, 1 warning in 65.39s**. Писатель: `tests/test_application/test_account_phone_writer.py` + `test_account_phone_race.py` → 31 passed за 1,38 с. `tests/test_services/test_log_masking.py -k without_setup_logging` → 1 passed. `tests/test_planning` → 218 passed, 2 skipped за 21,71 с. Образец теста скрипта `tests/test_scripts/test_recompress_attachments.py` → 22 passed за 5,12 с.

### B7. Тестовые образцы (вопрос (h))
- **Скрипт как модуль.** `[ПРОЧИТАНО: tests/test_scripts/test_recompress_attachments.py:24-26]` `sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))` и `import recompress_attachments as script`; база — фикстура `db_session` (`tests/conftest.py:44-56`: `sqlite+aiosqlite:///:memory:`, `expire_on_commit=False`); доказательства действия — журналы двойников, а не счётчики отчёта (`test_a_dry_run_writes_nothing`, строка 191). Образец «нулевой записи» — тот же приём: двойник считает вызовы.
- **Аккаунты.** `tests/account_label_support.py::seed_account(session, user_id, type_="tg_user", *, phone=None, manual_phone=None, stored_as_is=None, status="active", account_id=None) -> int` (строки 48-60): `phone` пишется писателем, `manual_phone` — `set_manual_phone`, у аккаунта `credentials="creds"` (для TG-тестов `credentials` понадобится править выборкой тестового двойника, а не `seed_account`).
- **Гонка.** `tests/test_application/test_account_phone_race.py:97-100`: файловая база `create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'race.db'}")` и независимые сессии через `async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)` — на `:memory:` каждая сессия получает свою базу, поэтому тест «ручной номер введён во время прогона» (критерий 2) строить на файловой базе: источник-двойник во время «опроса» зовёт `set_manual_phone` через вторую сессию, затем скрипт зовёт `fill_reported_phone` и обязан получить `KEPT`.
- **Подмена контейнеров и HTTP.** `tests/test_messengers/test_whatsapp.py:7-23`: `@patch("app.services.wa_container_manager.start_container")` и соседи; `:51, :265` — `patch("app.messengers.whatsapp.get_http_client", return_value=client)`. Для скрипта проще внедрение: функции источников — аргументы `run(...)`, тест подаёт двойники и проверяет `start_container` через счётчик вызовов.
- **Telethon.** `tests/test_messengers/test_telegram_user.py:37-45`: `patch("app.messengers.telegram_user.TelegramClient")` и `AsyncMock`; для скрипта — свой патч `TelegramClient` в модуле скрипта и двойник, у которого `connect`/`get_me`/`is_user_authorized`/`disconnect` — `AsyncMock`, а `start` — `AsyncMock` с `assert_not_called()`; счётчик одновременных подключений (инкремент в `connect`, декремент в `disconnect`) доказывает «строго последовательно» лучше, чем порядок вызовов.

## Architecture Patterns

### System Architecture Diagram

```
 администратор                       хост                         контейнер web (бой)
 just prod-backfill-phones  ──►  docker compose exec -T web  ──►  uv run python scripts/backfill_account_phones.py [--dry-run] [--wake] [--type T] [--account-id N] [--limit K]
                                                                             │
                                                                             ▼
                                  ┌───────────── выборка (колонки, не сущности) ─────────────┐
                                  │ SELECT id, type, credentials, status FROM messenger_accounts │
                                  │ WHERE phone IS NULL AND NOT phone_is_manual [+ фильтры]   │
                                  └───────────────────────────┬────────────────────────────────┘
                                                              │ по одному аккаунту, строго последовательно
                         ┌──────────────────┬─────────────────┴──────────────────┐
                         ▼                  ▼                                     ▼
                   type == "wa"       type == "max"                         type == "tg_user"
                         │                  │                                     │
          list_worker_containers()   list_worker_containers()          credentials разбирается?  нет ─► сессия мертва
          (один вызов на тип)        (один вызов на тип)                          │ да
                         │                  │                           «занят»? inspect(active+reserved) ∪ очередь telegram
           running?  нет ─► [--wake и active и очередь пуста? ─ нет ─► воркер недоступен]            │ занят / не удалось узнать ─► занят
                         │            да: start_container → wait_for_container_ready               │ нет
                         ▼                  ▼                                                       ▼
                GET {endpoint}/api/sessions/{id}/status                      TelegramClient(StringSession, receive_updates=False)
                (+ MAX: ограниченный опрос до connected:true)                connect → is_user_authorized → get_me
                         │                  │                                разбор исключений по классам; disconnect в finally
                         └──────────┬───────┘                                                       │
                                    ▼                                                                │
                    классификация (A6): недоступен / сессия мертва / номера нет / номер ◄───────────┘
                                    │ номер (reported)
                                    ▼
              --dry-run? да ─► предсказание чтением (писатель НЕ вызывается) ─► печать «было бы …» + mask_phone
                         нет ─► fill_reported_phone(session, id, reported) ─► commit
                                   WRITTEN / KEPT / MISSING / UNPARSEABLE ─► исход + mask_phone при WRITTEN
                                    │
        finally: stop_container(id) — только если подняли мы и очередь по-прежнему пуста
                                    ▼
                  итог: счётчики по исходам; код выхода 0, если прогон дошёл до конца
```

### Recommended Project Structure
```
scripts/
└── backfill_account_phones.py   # ЕДИНСТВЕННЫЙ новый файл кода: разбор аргументов, run(...), источники
tests/test_scripts/
└── test_backfill_account_phones.py   # новый (Wave 0): ядро, классификация, подъём, TG, вывод, текст рецептов
justfile                              # +2 рецепта: backfill-phones, prod-backfill-phones
```
Файла-помощника в `app/` не нужно: всё, что скрипту нужно от приложения, уже экспортировано (`fill_reported_phone`, `PhoneWrite`, `normalize_reported`, `mask_phone`, `reported_phone_from_status`, `reported_phone_of`, менеджеры контейнеров). Скрипт не правит ни одного файла в `app/`, `wa_worker/`, `max_worker/`, поэтому ни одно покрытое отпечатками решение Фаз 16–19 не устаревает.

### Pattern 1: ядро с внедряемыми источниками (TDD-единица)
**What:** `async def run(session_factory, args, sources) -> RunSummary`, где `sources` — набор функций: `list_running(kind) -> dict[int, bool]`, `fetch_status(endpoint, account_id) -> StatusReply`, `start(kind, id) -> endpoint|None`, `wait_ready(kind, id) -> bool`, `stop(kind, id)`, `queue_len(kind, id) -> int`, `poll_telegram(session_string) -> TelegramReply`, `is_busy(account_id) -> bool|None`. Боевой `main()` подставляет настоящие, тесты — двойники. Так «ноль вызовов `start_container`» проверяется счётчиком двойника, а «последовательно» — счётчиком одновременных подключений.
**When to use:** вся логика, кроме argparse и `asyncio.run`.
**Example** (проверено предикатами гейтов; имена из прочитанных модулей):
```python
# Source: пробный исходник A/B6 (импорты — app/application/accounts/phone.py, app/messengers/base.py, app/services/phone.py)
from app.application.accounts.phone import PhoneWrite, fill_reported_phone
from app.messengers.base import reported_phone_from_status
from app.services.phone import mask_phone, normalize_reported

async def handle(session, account_id, kind, body, dry_run):
    reported = reported_phone_from_status(body)
    e164 = normalize_reported(reported)
    if e164 is None:
        print(f"#{account_id} {kind} {Outcome.NO_NUMBER.value}")
        return Outcome.NO_NUMBER
    if dry_run:
        print(f"#{account_id} {kind} было бы заполнено {mask_phone(e164)}")
        return Outcome.FILLED
    written = await fill_reported_phone(session, account_id, reported)
    await session.commit()
    ...
```

### Pattern 2: WA/MAX — адрес только от Docker, подъём в `try/finally`
**What:** карта `list_worker_containers()` по типу; для `running` — `endpoint = f"http://{name}:3000"`; для остановленного и при `--wake` (статус `active`, очередь `llen` равна 0) — `start_container` → `wait_for_container_ready` → опрос → в `finally` остановка только если подняли мы и `llen` по-прежнему 0.
**When to use:** обе ветки WA/MAX. Не создавать `WhatsAppMessenger`/`MaxMessenger` без `bridge_url`.

### Pattern 3: TG — один клиент за раз, ошибки по классам, `finally`
**What:** клиент создаётся внутри `try` (конструктор `StringSession` сам может бросить `ValueError`), `disconnect` в `finally` с защитой от второй ошибки (как `telegram_user.py:440-444`).
**Example:**
```python
# Source: Telethon 1.42.0 (telegrambaseclient.py:263 receive_updates; users.py:177 get_me; users.py:207 is_user_authorized)
client = None
try:
    client = TelegramClient(StringSession(session_string), api_id, api_hash, receive_updates=False)
    await client.connect()                       # внутри уже get_me + GetState + GetDifference (auth.py:385-405)
    if not await client.is_user_authorized():    # ловит любой RPCError -> False
        return TelegramReply.dead()
    me = await client.get_me()                   # None на UnauthorizedError
    ...
finally:
    if client is not None:
        try:
            await client.disconnect()
        except Exception:
            pass
```

### Pattern 4: «занят» без правок отправки
**What:** `inspect = celery.control.inspect(timeout=…)`; `busy = {t["args"][2] for t in tasks(active ∪ reserved) if t["name"] == "app.worker.tasks.send_telegram_message"}`; плюс разбор списка `telegram`; `None` вместо снимка → «занят».

### Anti-Patterns to Avoid
- **`create_messenger(...)`/адаптер без `bridge_url` для WA/MAX** — будит воркер (B2).
- **`asyncio.gather` / параллельный опрос TG** — второе соединение одной сессии (A1).
- **`client.start()`** — интерактивный `input()` в `exec -T` (зависание/EOF) и приём обновлений.
- **`check_connection()` как «сессия жива»** — D-17.
- **Вызов писателя внутри отката ради `--dry-run`** — A3.
- **Печать `str(exc)`, `repr(reply)`, тела ответа воркера** — несёт чужие данные; только имя класса.
- **Загрузка сущностей `MessengerAccount` в сессию скрипта** — грязные объекты и строка сессии TG в памяти; выборка колонок.
- **Одна транзакция на весь прогон** — нарушает D-14.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Запись номера и защита ручного | свой UPDATE, «прочитал — решил — записал» | `fill_reported_phone` | условие внутри оператора; гонка проверена `test_account_phone_race.py` |
| Нормализация и E.164 | регулярки по номеру | `normalize_reported`, `mask_phone` | граница автопути (400 из 558 принятых значений недействительны) названа в шапке; маска закрывает WR-03 |
| Разбор поля `phone` из `/status` | `body["phone"]` | `reported_phone_from_status` | отвергает `bool`, нецелые, не-словари |
| Работает ли воркер, подъём, остановка, ожидание | `docker ps` через `subprocess`, свой `/health`-цикл | `list_worker_containers`, `start_container`, `stop_container`, `wait_for_container_ready` | метки роли, сеть, том, лимит памяти, политика перезапуска заданы в одном месте |
| Занят ли TG-аккаунт | свой Redis-ключ в боевом пути | `celery.control.inspect()` + список `telegram` | не трогает путь отправки |
| Счёт исходов | словари с «магическими» строками | `enum.Enum` + `collections.Counter` | перечень исходов закрыт, итог печатается в порядке перечисления |
| Сессия БД | свой engine | `get_engine(settings.database_url)`, `get_session_factory(engine)` (`app/database.py:80-85`) | `expire_on_commit=False`, `pool_pre_ping=True` |

**Key insight:** вся хитрость фазы — в границах (что НЕ вызывать), а не в вызовах; любой «удобный» адаптер приложения несёт скрытый побочный эффект (подъём контейнера, `get_me()` с приёмом обновлений), которого у одноразовой административной команды быть не должно.

## Common Pitfalls

### Pitfall 1: `get_own_phone()` и `create_messenger` будят остановленные воркеры
**What goes wrong:** на остановленном аккаунте скрипт поднимает контейнер, входит в WhatsApp/MAX, а `--dry-run` нарушает PHONE-18.
**Why it happens:** `bridge_url` — свойство с побочным эффектом (B2).
**How to avoid:** адрес — только от Docker; тест: подмена `start_container` и `ensure_*_container` с `assert_not_called()` на сценарии «воркер остановлен, флага нет» и на `--dry-run`.
**Warning signs:** в списке `docker ps` во время прогона растёт число `wa-worker-*`.

### Pitfall 2: «недоступен» принят за «номера нет»
**What goes wrong:** `get_own_phone()` и `None` на отказ дают «номера нет» у воркера, который просто не слушает (`wa-worker-48`), и администратор считает аккаунт безнадёжным.
**How to avoid:** собственный запрос `/status` и таблица A6; тест на каждую строку таблицы.

### Pitfall 3: `is_user_authorized() == False` читают как «сессия мертва»
**What goes wrong:** `FloodWaitError`, `AuthKeyDuplicatedError` схлопываются в `False`.
**How to avoid:** исключения вокруг `connect()`/`get_me()` разбирать по классам (A3); `FloodWaitError` — «недоступен», `AuthKeyError` — «мертва» с именем класса.

### Pitfall 4: пустая или битая строка сессии TG
**What goes wrong:** `StringSession("")` даёт пустую сессию — `connect()` выпустит новый ключ; `StringSession("pending")` бросает `ValueError`.
**How to avoid:** отсев по разбору `StringSession(credentials)` до сети; тест на `""`, `"pending"`, обрезанную строку — ноль обращений к `TelegramClient.connect`.

### Pitfall 5: гонка «подъём и очередь»
**What goes wrong:** во время нашего подъёма появилась плановая задача; воркер взял её, а наш `finally` убил контейнер посреди отправки.
**How to avoid:** до подъёма `llen` очереди нулевой; перед остановкой — снова нулевой; ненулевой — контейнер не трогать (боевой менеджер ведёт его сам, а простой его погасит).

### Pitfall 6: разный порядок старта WA и MAX
**What goes wrong:** WA — HTTP только после установления сессии (нет `connected`-периода, но нет и HTTP при зависании), MAX — HTTP сразу и `connected:false` долго. Один одинаковый «подождать `/health` 30 с и спросить раз» ошибочен для обоих.
**How to avoid:** WA — окно `wait_for_container_ready(timeout≈90)` и один запрос; MAX — ограниченный опрос до `connected: true`; обе ветки при исчерпании окна — «воркер недоступен» и остановка.

### Pitfall 7: печать с `phone` в имени или литералом
**What goes wrong:** гейт приватности краснит суиту; хуже — единственный рубеж обойдён.
**How to avoid:** форма строки B6; переменные `reported`/`e164`/`masked`; тест на захват `capsys`: ни одной последовательности из 7+ цифр в выводе, маска присутствует (антивакуум).

### Pitfall 8: нет пересборки образа `web`
**What goes wrong:** `just prod-backfill-phones` — «No such file» или старый код: скрипт не смонтирован, он в образе (`COPY . .`).
**How to avoid:** порядок выката (часть C, пункт (viii)): образ приложения → образы воркеров → перезапуск работающих воркеров → прогон; в выводе баннер версии не нужен, нужен текст в плане владельца.

### Pitfall 9: смешанный парк воркеров
**What goes wrong:** воркер на образе до Фазы 19 (`wa-worker-48`) без поля `phone` даёт «номера нет» даже при `connected: true`.
**How to avoid:** в строке итога заметка «образ воркера без поля phone» (ключ `phone` в теле отсутствует); в тексте для владельца — прогон после перезапуска работающих воркеров (`STATE.md:652`).

### Pitfall 10: осиротевший поднятый контейнер
**What goes wrong:** обрыв ssh-сессии (`docker compose exec` без tty) убивает Python без `finally`; WA-воркер, висящий в `ensureSession`, сам не гаснет (нет цикла простоя).
**How to avoid:** устойчиво к `KeyboardInterrupt`/`CancelledError` (тот же `finally`); в тексте рецепта — запускать порциями (`--limit`, `--type`, `--account-id`) и после обрыва проверить `just wa-workers` / `just max-workers`.

## Code Examples

### Классификация ответа `/status` (по таблице A6)
```python
# Source: wa_worker/index.js:746-766, max_worker/main.py:1014-1033, app/messengers/base.py:16-35
def classify_status(body: object) -> tuple[Outcome | None, object]:
    if not isinstance(body, dict):
        return Outcome.UNREACHABLE, None
    if body.get("connected") is not True:
        return (Outcome.DEAD_SESSION if body.get("exists") is False else Outcome.UNREACHABLE), None
    reported = reported_phone_from_status(body)
    if reported is None:
        return Outcome.NO_NUMBER, None          # note: "phone" not in body -> образ без поля
    return None, reported                        # дальше писатель
```

### Подъём WA по флагу с гарантированной остановкой
```python
# Source: app/services/wa_container_manager.py:30-175
started = False
try:
    if not running and wake and status_is_active and queue_len(kind, account_id) == 0:
        endpoint = start_container(account_id)         # MAX: start_container(account_id)
        started = endpoint is not None
        if not started or not await asyncio.to_thread(wait_for_container_ready, account_id, timeout=90.0):
            return Outcome.UNREACHABLE
    ...
finally:
    if started and queue_len(kind, account_id) == 0:
        await asyncio.to_thread(stop_container, account_id)
```

### Рецепты (формы соседних; текст, прямо говорящий «пишет по умолчанию» — D-08)
```
# Backfill missing account numbers (WRITES by default; add --dry-run to preview)
backfill-phones *args:
    uv run python scripts/backfill_account_phones.py {{ args }}

# Backfill missing account numbers in prod Docker (WRITES by default; add --dry-run to preview)
prod-backfill-phones *args:
    docker compose -f docker-compose.prod.yml exec -T web uv run python scripts/backfill_account_phones.py {{ args }}
```

## Runtime State Inventory

> Фаза — разовое заполнение данных существующих записей (миграция данных без переименования). Пять категорий, явно.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `messenger_accounts.phone` и `phone_is_manual` — после ревизии 0023 у **каждой** существующей строки `phone IS NULL`, `phone_is_manual = false` (`16-CONTEXT.md` D-01). Сколько строк по типам — не измерено (базу читать запрещено). У подключённых MAX `credentials = str(account.id)` (`accounts.py:1046`), число формы осталось только в `phone.txt` воркера | **миграция данных** — делает сам скрипт, строка за строкой, без изменения `status`; переноса `credentials` нет (O-3) |
| Live service config | Redis: `wa:endpoint:{id}` / `max:endpoint:{id}` (TTL 420 с, `tasks.py:676, 713`), `wa:queue:{id}` / `max:queue:{id}`, `wa:active_accounts` / `max:active_accounts`; брокер Celery (список `telegram`). Воркеры WA/MAX: на сейчас 4 работают (`wa-worker-21` без файлов сессии, `wa-worker-48` на образе до Фазы 19 и без HTTP, `max-worker-19`, `max-worker-28`) | **ничего не править**; скрипт читает очереди и `inspect`; гасит только поднятое им самим |
| OS-registered state | нет: ни cron, ни systemd, ни Task Scheduler для этой команды; запуск — вручную владельцем. Проверено: `justfile` — единственное место рецептов, `docker-compose.prod.yml` не получает нового сервиса | none — verified by чтение `justfile`, `docker-compose.prod.yml` |
| Secrets/env vars | скрипт читает `DATABASE_URL`, `REDIS_URL`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` из `.env` контейнера `web` (`x-app-base: env_file: .env`); имена не меняются. **Сторонняя находка (вне фазы):** строка `worker_starting` воркера WA печатает `redisUrl` с паролем в журнал контейнера (`wa_worker/index.js:946`) — виден в `docker logs wa-worker-*` и, вероятно, в Loki | в план фазы не входит; вынести владельцу как отдельный вопрос безопасности |
| Build artifacts / installed packages | образ приложения должен быть пересобран, чтобы в `web` появился скрипт (`COPY . .`, код не монтируется); образы воркеров `broadcaster-wa-worker:latest` / `broadcaster-max-worker:latest` пересобраны сегодня (`aa71b18b8028` 06:19Z, `e734363be9dd` 09:49Z), но `wa-worker-48` идёт на более старом образе | выкат — деплой-гейт владельца; скрипту нужен порядок «образ → воркеры → перезапуск работающих → прогон» |

## Долги, адресованные Фазе 20 вне CONTEXT.md (часть C)

Свёртка `grep -rn "Фаз[ыуеа] 20\|Фазой 20\|Фазу 20\|Phase 20\|скрипт Фазы 20\|дозаполн"` по `phases/16-*`, `17-*`, `18-*`, `19-*`, `STATE.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `research/` (ложные срабатывания «фазы 2026-…» отброшены) дала по файлам: `research/PITFALLS.md` 14, `SUMMARY.md` 12, `STACK.md` 10, `ARCHITECTURE.md` 10, `16-RESEARCH.md` 10, `16-VERIFICATION.md` 9, `16-VALIDATION.md` 8, `REQUIREMENTS.md` 8, `STATE.md` 7, `ROADMAP.md` 4, `16-SECURITY.md` 4, `16-CONTEXT.md` 4, `16-REVIEW.md` 2, `19-REVIEW.md` 2, `19-CONTEXT.md` 2, `19-RESEARCH.md` 3, ещё три-четыре строки в `17-*`/`18-*` и десятки в планах и сводках `16-xx` (контракт писателя). Строки `16-xx-PLAN.md`/`SUMMARY.md` описывают те же формы подложенного скрипта, что и `16-VALIDATION.md` (трассеры гейтов), и отдельных долгов не несут.

| Долг | Диспозиция | Доказательство | Что делает план |
|---|---|---|---|
| **(i) `STATE.md:788` «Принятые границы финального раунда 12» (О-26)**: DML внутри CTE (CR-09), имя таблицы/колонки в другом регистре (WR-40), `INSERT OR REPLACE` SQLite (IN-29), форма `raw-dbapi-sql-from-a-parameter`, маска наполовину (WR-41) и знак в одной позиции (WR-42), `--loglevel` Celery (IN-28); адресат — «писатели и ревью фаз 17–20 (мастер Фазы 19, скрипт Фазы 20)» | **open, not load-bearing; именованная граница, не работа** | `[ПРОЧИТАНО: app/models/phone_guard.py:102-141]` «ГРАНИЦА, НАЗВАННАЯ ПРЯМО» — каждая форма названа; «DML внутри CTE … В `app/` и `scripts/` `.cte(` и `add_cte` нет; граница принята владельцем (О-26) и передана будущей фазе». `[ПРОЧИТАНО: app/services/log_masking.py:112-115]` WR-41/WR-42 — «принятые границы ревью раунда 12 (О-26 …; суд не расширен)». `[ЗАМЕР: grep -rn "\.cte(\|add_cte\|exec_driver_sql\|INSERT OR REPLACE\|prefix_with" app/ scripts/ --include=*.py]` без шапок гейтов — пусто. Гейты зелёные (1161 passed) | Скрипт сам не использует ни одной из этих форм (`.cte(`, `add_cte`, `text()`/`exec_driver_sql`/сырой DBAPI по колонкам номера, `INSERT OR REPLACE`/`prefix_with`, таблица/колонка в другом регистре). WR-41/WR-42 до скрипта не доходят: он печатает `mask_phone(normalize_reported(...))`, то есть только нормализованный E.164; неразбираемое значение даёт «номера нет» без маски. Суд гейтов не расширять (решение О-26). В «Validation» — не новый тест, а проверка, что `grep` выше остаётся пустым |
| **(ii) `16-REVIEW.md:231` скрытый дефект MISSING против WRITTEN для явных `id`** (писатель выдавал ожидающую строку за удалённую); адресаты — мастер Фазы 19 и скрипт Фазы 20 | **closed** | `[ПРОЧИТАНО: phone.py:124-139]` `_fill_if_unknown` начинается с `await session.flush()` ВНЕ `writer_scope()`, оператор идёт с `execution_options(synchronize_session=False, autoflush=False)` — это и есть исправление из «Fix» ревью (`WR-43`, план 16-61). `[ЗАМЕР: pytest tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py]` → 31 passed; в сводке `19-RESEARCH.md` (часть C) названы коммиты `73461de8`, `c31e077a`, `39c04a34` и тест `test_a_row_pending_insert_with_a_known_id_is_written` | Для скрипта недостижимо: он зовёт писатель по `id` строки, уже существующей в базе и закоммиченной, одной сессией с коммитом на аккаунт. Опора: исход `MISSING` — отдельная строка итога (D-02), не «ручной» |
| **(iii) `19-REVIEW.md:100-101` (IN-03): введённый в форму номер MAX хранится с `phone_is_manual = False`, поэтому дозаполнение Фазы 20 никогда его не исправит**; ревьюер предложил записать это в заметках Фазы 20 | **open, owner-decided residual, not load-bearing** (следует решению владельца OQ1 / D-10 Фазы 19; прямо названо ревью) | `[ПРОЧИТАНО: 19-REVIEW.md:96-101]` «a typo or someone else's number can never be corrected by the Phase 20 backfill or a later reported value. Only an explicit manual edit fixes it. … Optionally record the "typed number is not auto-correctable" consequence in the Phase 20 notes.» Соответствует deferred «обновление уже известного автономера — v2+ вместе с `phone_source`» (CONTEXT) | Кода нет. Записать следствие в строку помощи/шапку скрипта одной фразой (аккаунт с уже заполненным номером, в том числе введённым в форму MAX, скрипт не трогает и не исправляет) и в итог: исход «ручной / уже заполнен» объединяет оба случая. Правку комментария воркера `max_worker/main.py:199-202` (предложена ревью) **не** брать: она потребует пересборки образа MAX |
| **(iv) `16-CONTEXT.md` D-01 и комментарий `app/models/messenger_account.py:81-82`: «MAX, чей введённый номер лежит в `credentials` (переносит его дозаполнение Фазы 20, а не ревизия)»** | **open, load-bearing для объёма** (запись Фазы 16 поручает Фазе 20 то, чего CONTEXT.md Фазы 20 не содержит) | `[ПРОЧИТАНО: app/pages/accounts.py:1042-1048]`: `entered_phone = account.credentials`, … `account.credentials = session_id`, `account.status = "syncing"` — после подключения `credentials` MAX равен `str(account.id)`. `[ЗАМЕР: git show 84f414d6~1:app/pages/accounts.py]` перед Фазой 19 строка `account.credentials = session_id` уже была (первый коммит UI MAX `ba63893c` тоже её содержал), то есть у всех подключённых аккаунтов MAX число формы из `credentials` потеряно **давно**; остаётся `phone.txt` воркера (A5). Незавершённые аккаунты `connecting` хранят число формы в `credentials` (E.164 с плана 19-06) | Не переносить по умолчанию (число формы не проверено, A5). Решение за владельцем — O-3. Править комментарий модели в этой фазе **нельзя без последствий**: файл Фазы 16 покрыт отпечатками верификации (память `post-close-code-fix-owner-attested-digest`) — отметить в записи фазы как известное устаревание, правку не брать |
| **(v) `16-SECURITY.md:94` T-16-44 / шапка `app/services/phone.py`**: «Фаза 20 строит на этом скрипт» — автопуть принимает значения, которые метаданные считают возможными, в том числе недействительные (400 из 558) | **closed** (мера — шапка и тест) | `[ПРОЧИТАНО: app/services/phone.py:37-57]` «⚠️ ГРАНИЦА ПРАВИЛА АВТОПУТИ (названа, а не выдана за покрытие …)» — граница автопути; тест `test_the_module_header_names_the_auto_path_boundary_with_its_measurement` | Формулировки вывода — «заполнено», не «проверено/подтверждено»; сообщения не утверждают, что записанное значение — настоящий номер |
| **(vi) `16-SECURITY.md:67` T-16-25 / WR-05**: отсутствие строки не должно выдаваться за «оставлено» | **closed** | `phone.py:142-145` проба существования; `PhoneWrite.MISSING` | отдельная строка итога «удалён во время прогона» (D-02); тест: аккаунт удаляется между выборкой и записью |
| **(vii) `16-VERIFICATION.md:424` процессы Celery и маска номера для «Фаз 18–20»** | **closed / не относится** | `app/worker/celery_app.py` (шапка о `setup_logging` процесса Celery, CR-06); скрипт работает в `web`, не в Celery | none |
| **(viii) `STATE.md:652`, `ROADMAP.md:110`, `STACK.md:217` порядок выката**: дозаполнение только после пересборки обоих образов воркеров и перезапуска работающих контейнеров в окно без рассылок | **open (операционный), вне критериев фазы** | `[ЗАМЕР: docker inspect]` `wa-worker-48` запущен 2026-11-20 (до коммита `babfe18f` от 2026-11-22) на образе, отличном от нового `aa71b18b8028` — смешанный парк существует прямо сейчас `[ВЫВОД]` | План — заметка «Порядок» для владельца (в справке рецепта и в плане документации), в строке итога — заметка про образ без поля `phone` (Pitfall 9). Сам скрипт этот порядок не проверяет |
| **(ix) `research/SUMMARY.md:84, 94` и `ARCHITECTURE.md:437`**: «по умолчанию — только работающие контейнеры **и `active`**»; число формы MAX «при дозаполнении — из `entered_phone` воркера» | **расхождение с CONTEXT, закрыто решением владельца D-12 (статус не фильтр)**, вторая часть — R-2 | CONTEXT D-12 против SUMMARY.md:84 | Следовать CONTEXT D-12 на пути по умолчанию; статус `active` применять только к пути подъёма (A4, группа (б)); R-2 решён в A5 и вынесен как O-2 |
| `18-CONTEXT.md:21` / `REQUIREMENTS.md:73` «перенос ручного номера при переподключении» | **не адресовано Фазе 20** (Out of Scope вехи: переподключение создаёт новую строку) | `REQUIREMENTS.md:73` | none |
| `19-CONTEXT.md` D-15 / `19-RESEARCH.md:39` «номер дозаполнит Фаза 20 или ручная правка» (MAX: опрос статуса раньше `on_start`) | **closed в рамках фазы** | у MAX `own_phone` ставится ДО `is_connected = True` (A5); скрипт опрашивает до `connected: true` | Это и есть случай, ради которого аккаунты MAX с `phone IS NULL` попадают в дозаполнение |

**Открытых долгов, которые требуют решения владельца до планирования:** один — (iv), вынесен как O-3 (вместе с O-1, O-2, O-4, порождёнными самим исследованием).

## Волны и планы (рекомендация)

Один файл кода, поэтому волны последовательные (четыре плана, каждый `type: tdd`: на `type: execute` TDD-гейт инертен — память `tdd-review-gate-inert-on-type-execute`):
- **20-01 (волна 1): ядро.** `Outcome` (`FILLED`, `KEPT`, `NO_NUMBER`, `DEAD_SESSION`, `UNREACHABLE`, `BUSY`, `ACCOUNT_GONE`, плюс исход сбоя по аккаунту, D-14), выборка колонок, `run(...)` с внедрением источников, запись `fill_reported_phone` + коммит на аккаунт, `--dry-run` без вызова писателя, итог со счётчиками, коды выхода. Тесты критериев 1–3 на двойниках источников; гонка (критерий 2) на файловой базе; гейты B6.
- **20-02 (волна 2): источник WA/MAX.** Карта `running` по `list_worker_containers`, свой запрос `/status`, таблица A6, подъём по флагу, опрос MAX, остановка в `finally` с проверкой очереди, отказ `--wake` под `--dry-run`. Тесты критерия 4 и «ноль `start_container`».
- **20-03 (волна 3): источник TG.** Разбор `StringSession` до сети, `receive_updates=False`, порядок `connect → is_user_authorized → get_me`, карта ошибок A3, признак «занят» (`inspect` + очередь, отказ в закрытую), последовательность (счётчик одновременных подключений), `finally`. Тесты критерия 5 и D-09.
- **20-04 (волна 4): оболочка.** Разбор аргументов (`--dry-run`, флаг подъёма, `--type`, `--account-id`, `--limit`), строка помощи и рецепты `justfile` с явным «пишет по умолчанию» (D-08), текст рецепта `exec -T web`, защита «TG только в контейнере» (если принята), порядок выката и окно запуска в тексте для владельца, прогон всех гейтов и `tests/test_planning/`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2, pytest-asyncio ≥ 1.3.0 `[ЗАМЕР: .venv/bin/python -m pytest --version]` |
| Config file | `pyproject.toml` (pytest в dev-зависимостях); специального конфига фазы нет |
| Quick run command | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly` |
| Full suite command | `just test` (≈46 мин, 6143 passed на закрытии Фазы 19; гнать с таймаутом 5400 с — память `regression-gate-duplicates-post-merge-suite`) |
| Gates (named in every plan, D-07) | `uv run pytest tests/test_phone_privacy_gate.py tests/test_phone_gates_parity.py tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly` — **1161 passed за 65,39 с** `[ЗАМЕР]` |
| Writer + masking | `uv run pytest tests/test_application/test_account_phone_writer.py tests/test_application/test_account_phone_race.py tests/test_services/test_log_masking.py -k "phone or without_setup_logging" -q -p no:randomly` |
| Records | `uv run pytest tests/test_planning -q -p no:randomly` — **218 passed, 2 skipped за 21,71 с** `[ЗАМЕР]`; прогонять явно (память `orchestrator-gate-catches-records-defects`: исполнители их отключают) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PHONE-17 | выборка отсекает ручные и заполненные; заполняет пустые; статус не меняется | unit (`db_session`) | `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly -k "selection or fills or status_unchanged"` | ❌ Wave 0 |
| PHONE-17 | повторный прогон ничего не меняет | unit | `… -k idempotent` | ❌ Wave 0 |
| PHONE-17 | ручной номер, введённый во время опроса, не затёрт (файловая база, две сессии) | integration | `… -k manual_entered_during_the_run` | ❌ Wave 0 |
| PHONE-17 | итог: все исходы (заполнено / ручной / номера нет / сессия мертва / воркер недоступен / занят / удалён во время прогона) в счётчиках и по строке на аккаунт | unit | `… -k summary` | ❌ Wave 0 |
| PHONE-18 | `--dry-run`: ноль вызовов `start_container`, ноль вызовов писателя, строки базы не изменились (снимок до/после) | unit | `… -k dry_run` | ❌ Wave 0 |
| PHONE-18 | `--wake` вместе с `--dry-run` отвергается (`SystemExit` 2), ни одного вызова источника | unit | `… -k wake_with_dry_run` | ❌ Wave 0 |
| PHONE-19 | по умолчанию остановленный воркер → «воркер недоступен», `start_container` не вызван; работающий опрошен | unit | `… -k default_polls_only_running` | ❌ Wave 0 |
| PHONE-19 | с флагом: подъём → ожидание → опрос → остановка; остановка в `finally` при сбое опроса; уже работавший контейнер не гасится; очередь не пуста → ни подъёма, ни остановки; статус не `active` → не будится | unit | `… -k "wake"` | ❌ Wave 0 |
| PHONE-19 | классификация A6: каждая строка таблицы (нет ключа `phone`, `null`, мусор, `connected:false` при `exists` ложь/истина, не-200, не-JSON, таймаут) | unit (параметризация) | `… -k classify_status` | ❌ Wave 0 |
| PHONE-19 | адаптеры не создаются без `bridge_url` (ни `ensure_wa_container`, ни `ensure_max_container` не вызваны) | unit | `… -k never_wakes_through_adapters` | ❌ Wave 0 |
| PHONE-20 | TG строго по одному: счётчик одновременных подключений ≤ 1; `start` не вызван; клиент построен с `receive_updates=False`; `disconnect` ждётся в `finally` при исключении | unit | `… -k telegram_sequential` | ❌ Wave 0 |
| PHONE-20 | занятый аккаунт: ноль вызовов `connect`, исход «занят», номер не пишется; «не удалось определить» → «занят» | unit | `… -k telegram_busy` | ❌ Wave 0 |
| PHONE-20 | карта ошибок A3 (`""`, `"pending"`, `AuthKeyDuplicatedError`, `FloodWaitError`, `get_me() is None`, `is_user_authorized() is False`); `check_connection` не вызывается (D-17) | unit | `… -k telegram_outcomes` | ❌ Wave 0 |
| PHONE-20 | рецепт `prod-backfill-phones` содержит `exec -T web`, а локальный — нет `docker compose` | unit (чтение `justfile`) | `… -k recipes` | ❌ Wave 0 |
| PHONE-21 | вывод (`capsys`) не содержит ни одной цепочки из 7 и более цифр; строка «заполнено» содержит маску `mask_phone`; антивакуум: хотя бы одна строка «заполнено» проверена | unit | `… -k output_masks` | ❌ Wave 0 |
| PHONE-21 | гейты | gates | команда «Gates» выше | ✅ есть |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/test_scripts/test_backfill_account_phones.py -q -p no:randomly` (секунды) + команда «Gates» для любой задачи, трогающей файл скрипта (≈65 с).
- **Per wave merge:** «Gates» + «Writer + masking» + `tests/test_planning` + `tests/test_scripts/ -q -p no:randomly`.
- **Phase gate:** полная суита `just test` зелёная (таймаут 5400 с, память `regression-gate-duplicates-post-merge-suite`) до `/gsd-verify-work`; `grep -rn "\.cte(\|add_cte\|exec_driver_sql\|INSERT OR REPLACE\|prefix_with" app/ scripts/` без шапок гейтов — пусто.

### Wave 0 Gaps
- [ ] `tests/test_scripts/test_backfill_account_phones.py` — все строки таблицы выше (новый; `tests/test_scripts/__init__.py` уже есть)
- [ ] фикстура файловой базы с двумя независимыми сессиями (по образцу `tests/test_application/test_account_phone_race.py:97-100`) — для теста критерия 2
- [ ] двойник Telethon-клиента со счётчиком одновременных подключений и `start` с `assert_not_called()`
- [ ] Framework install: не нужен (pytest и pytest-asyncio в проекте)

Правила исполнения, не относящиеся к тестам фазы, но обязательные для планов: TDD-RED-гейт нельзя писать как `test $? -ne 0` (память `red-gate-inversion-false-greens`: «зеленеет вакуумом»); гейт перед коммитом — только через `&&` (память `check-gate-before-commit-in-chains`); таймаут регрессионного гейта 5400 с (`regression-gate-duplicates-post-merge-suite`); ID угроз в планах уникальны сквозным счётчиком (память `threat-id-uniqueness-gate`); в диспетчеризацию исполнителей добавить `tests/test_planning` и `tests/test_pages/test_htmx_post_pairs.py` поимённо (память `cross-cutting-gates-skipped-by-executors`; число 302-утверждений фаза не сдвигает).

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | команда запускается администратором на хосте (`docker compose exec`), HTTP-маршрута нет; доступ к хосту и `docker.sock` — вне приложения |
| V3 Session Management | no | веб-сессий нет; **сессии мессенджеров** — предмет защиты (V6/V8): строка сессии TG не печатается и не пишется назад |
| V4 Access Control | да (узко) | скрипт управляет только контейнерами с меткой роли `broadcaster.role=wa-worker|max-worker` через менеджеры; гасит только поднятые им самим; к чужим контейнерам не обращается |
| V5 Input Validation | да | тело `/status` воркера — недоверенный JSON: `reported_phone_from_status` + `normalize_reported`; `argparse` с `type=int` и `choices` для `--type`; номер аккаунта из выборки базы, не из аргументов без проверки |
| V6 Cryptography | no | криптографию не пишем; ключ авторизации TG — только в памяти процесса |
| V7/V8 Error handling, logging, data protection | да (главное) | PHONE-21: только `mask_phone` в `print`, имя класса исключения вместо текста; гейт приватности — единственный рубеж у скриптов; номер, JID, строка сессии, тело ответа воркера в вывод не попадают |

### Known Threat Patterns for {Python-скрипт в `web` + Docker SDK + Telethon + воркеры}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Потеря ключа авторизации TG из-за второго подключения (необратимо) | Denial of Service | последовательность; пропуск занятых; отказ в закрытую при неопределённом «занят»; `receive_updates=False`; `disconnect` в `finally`; запуск только в боевом контейнере (A1, A2) |
| Подъём воркера = вход связанного устройства / удаление файлов сессии на 401/403/405 | Tampering / DoS | подъём только по флагу; очередь пуста; статус `active`; `finally` остановка; запрет под `--dry-run` (A4) |
| Второй писатель номера затирает ручной | Tampering | только `fill_reported_phone`; гейт единственного писателя; `phone_guard` на исполнении (B6) |
| Номер/строка сессии в выводе, журнале, текстах исключений | Information Disclosure | форма `print` из B6; имена без `phone`; `credentials` не печатается; `str(exc)` не печатается |
| Копия боевой базы с секретами вне боевого периметра | Information Disclosure | не делать (O-4 а) либо обнулить `credentials` до первого запуска и изолировать сеть (A7) |
| Доверие числу формы MAX как номеру аккаунта | Spoofing | не использовать `phone.txt` (A5, O-2) |
| **Сторонняя находка:** `redisUrl` с паролем в журнале `worker_starting` WA-воркера | Information Disclosure | вне фазы; предложить владельцу отдельную задачу (в `docker logs wa-worker-*` значение видно целиком; в этот отчёт не переписано) |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `just` | рецепты, `just --dry-run` | ✓ | 1.45.0 | — |
| `uv` | `uv run pytest`, `uv run python` | ✓ | 0.12.1 | `.venv/bin/python -m pytest` (так мерились базовые линии) |
| Python (venv) | тесты, предикаты гейтов | ✓ | 3.12.13 | — |
| Docker daemon + `docker compose` | боевой прогон (`web`), чтение метаданных | ✓ | Docker 29.7.1, Compose v5.3.1 | — |
| `docker.sock` в `web` | `list_worker_containers`, подъём | ✓ (в compose) | `docker-compose.prod.yml:108` | — |
| Telegram / WhatsApp / MAX сессии | боевой прогон | ✗ (по правилам исследования не использовались) | — | боевой шаг владельца после выката |
| Redis `web`-стороны | очередь, `inspect` | не проверялось (читать брокер запрещено) | — | в тестах — двойники |

**Missing dependencies with no fallback:** нет для разработки и тестов.
**Missing dependencies with fallback:** боевые источники недоступны исследованию — компенсируются двойниками и первым боевым `--dry-run --account-id`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Условие `AuthKeyDuplicated` читалось как «два разных IP» (Telethon, разведка вехи) | Официальная страница: параллельные TCP-соединения с одним ключом, «from the same or different IP addresses» | страница прочитана 2026-11-23 | «тот же хост» защитой не считается (A1) |
| `connect()` читалось как «только соединение» | в Telethon 1.42.0 `connect()` сам делает `get_me` + `GetState` + `GetDifference` на пустом `_message_box` | 1.42.0, `telegrambaseclient.py:605-608` | исключения авторизации приходят из `connect()` |
| PyMax 2.3.1 не подключается (websocket сменился) | PyMax 2.5.0, `Contact.phone: int \| None` | quick-261123-bgc, `d373515e`, 2026-11-23 | MAX отдаёт номер через `client.me` и при восстановлении |

**Deprecated/outdated:** запись `ARCHITECTURE.md:105` про `create_messenger` для скрипта; `STACK.md:168` про `get_archive` у остановленного контейнера; комментарий `messenger_account.py:81-82` про перенос из `credentials`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Причина, по которой боевые параллельные отправки одного аккаунта не дают `AuthKeyDuplicated`, — сервер объявляет `tmp_sessions` > 1 или определение мягче документированного | A1 | если второе подключение всё же опасно при другом шаблоне (дольше, с `get_dialogs`), уверенность «короткое подключение безопасно» ложна; защита («занят», последовательность) всё равно требуется |
| A2 | Формат сообщения kombu в Redis хранит `headers.argsrepr` как в локально собранном протоколе 2 | A2 | разбор списка `telegram` не сработает; остаётся `inspect` (тестом на настоящей полезной нагрузке или отказом от чтения списка) |
| A3 | Код 405 у Baileys — «Connection Failure» из-за версии WA Web или блокировки адреса | A4 | если 405 приходит и на валидной сессии по иной причине, риск удаления файлов при подъёме выше названного |
| A4 | Сервер MAX присылает `contact.phone` в ответе на вход по токену так же, как при QR-входе | A5 | `max-worker-*` на восстановленных сессиях отвечают `phone: null` → «номера нет» по всем старым MAX; видно на первом боевом `--dry-run --account-id 19` |
| A5 | Число спящих WA/MAX-аккаунтов велико (сегодня работают 4 воркера); точное число не измерено | Summary, A4 | если спящих мало, флаг подъёма почти не нужен |
| A6 | Обрыв `docker compose exec` (ssh) завершает Python без `finally` | Pitfall 10 | если процесс переживает, осиротевших контейнеров не будет |
| A7 | `/.dockerenv` существует внутри контейнеров Docker (для защиты «TG только в контейнере», если её примут) | Open Questions (б) | защита по маркеру не сработает; тогда рецепт передаёт явный флаг |
| A8 | `inspect().active()` отвечает за ≤ 2 с под нагрузкой `celery-worker-telegram` | A2 | таймаут слишком мал → часть ответов «не удалось определить» → «занят»; прогон медленнее, но безопасен |

## Open Questions

### Вопросы владельцу (задаст оркестратор; ответы вернуть в этот файл)

1. **Будить ли остановленные WhatsApp-воркеры по флагу?** Сейчас работает 4 воркера, остальные аккаунты WA/MAX без флага получат «воркер недоступен». Подъём WhatsApp — вход связанного устройства «Broadcaster» (его видит владелец телефона); если WhatsApp ответит на этот вход «разлогинен» (401), «запрещено» (403) или 405, воркер сам удалит файлы сессии. Это тот же путь, которым идёт любая плановая рассылка в спящий аккаунт, но флаг применяет его и к аккаунтам без рассылок. Варианты: **(а) (рекомендуется)** флаг будит и WA, и MAX: по одному, только аккаунты в статусе «активен», только при пустой очереди, с предупреждением в справке; **(б)** флаг будит только MAX, WA-аккаунты без работающего воркера остаются без номера до ручного ввода; **(в)** вместо подъёма WA читать номер из файла сессии одноразовым контейнером с боевым томом только на чтение (новый код и работа с секретными ключами, потребует отдельного плана).
2. **Использовать ли для MAX номер, который человек вводил в форму подключения (лежит в файле `phone.txt` воркера), если воркер номер не отдал?** Этот номер никем не проверен (в проверке Фазы 19 человек ввёл один номер, а отсканировал другим аккаунтом), прочесть его можно только монтированием тома с сессиями MAX, и записанный как автоматический он больше не исправится (автоисточники пишут только в пустое). Варианты: **(а) (рекомендуется)** нет; такие аккаунты остаются «номера нет» до ручного ввода или до подъёма воркера по флагу; **(б)** да, записывать как автоматический номер (после этого его может исправить только ручная правка).
3. **Переносить ли «номер из формы» MAX из поля `credentials` в колонку номера?** Фаза 16 (D-01) поручила это дозаполнению, но измерено: после подключения MAX поле `credentials` перезаписывается номером аккаунта (так было всегда), поэтому у подключённых аккаунтов переносить нечего; число лежит в `credentials` только у аккаунтов в статусе «подключается», и оно не проверено. Варианты: **(а) (рекомендуется)** не переносить; считать запись Фазы 16 устаревшей (комментарий модели не правим: файл покрыт отпечатками верификации Фазы 16); **(б)** переносить для аккаунтов MAX в статусе «подключается» как автоматический номер.
4. **Делать ли прогон `--dry-run` на копии боевой базы?** Копия не изолирует скрипт: в ней строки сессий Telegram (это сами ключи доступа), те же номера аккаунтов, а окружение боевое; запуск с другого адреса при работающей рассылке может необратимо убить ключ Telegram. Варианты: **(а) (рекомендуется)** копию не делать: корректность выборки, вывода и «ноль записей» доказывают тесты на синтетических данных, а настоящие исходы владелец смотрит первым боевым `--dry-run --account-id <один>` после выката; **(б)** копия только таблицы аккаунтов в изолированной сети без доступа к Docker и Redis, с обнулёнными `credentials` до первого запуска (процедура в A7; покажет только объём и формат, реальных исходов не покажет); **(в)** копия «как есть» — не рекомендуется.

### Усмотрение планировщика (рекомендации)

1. **Имя флага подъёма и поведение под `--dry-run`:** `--wake`; под `--dry-run` отвергать ошибкой аргументов (код 2), а не молча игнорировать: молчаливое «игнорирование» сбивает с толку, а отказ ничего не стоит (D-06 разрешает оба).
2. **Транспорт `/status`:** запрос самого скрипта (`httpx.AsyncClient`, таймаут соединения ~3 с, общий ~10 с) + `reported_phone_from_status`; адаптеры и `get_own_phone()` не использовать (B2, A6). Новый метод на адаптерах не заводить: он лежит под гейтами `app/` и тестами Фазы 19.
3. **`connected: true` как условие приёма `phone`:** требовать (как Фаза 19). Допустимая альтернатива — принимать `phone` у WA и при `connected: false`, пока объект сессии жив (`sock.user` берётся из `creds.me`); даёт больше заполненных строк, но размывает «сессия мертва».
4. **Окна ожидания:** WA — `wait_for_container_ready(account_id, timeout=90.0)` и один запрос; MAX — после `wait_for_container_ready` опрос `/status` каждые ~2 с до `connected: true` или ~90 с. `wait_for_container_ready` синхронна — вызывать через `asyncio.to_thread`.
5. **Пауза между TG-аккаунтами:** короткая (≈1 с) — не для защиты ключа, а против `FloodWait` на длинных прогонах; `FloodWaitError` — «недоступен», прогон идёт дальше.
6. **Отказ в закрытую для «занят»:** `inspect` вернул `None`, ошибка Redis, нечитаемое сообщение очереди → «занят». Строка итога так и пишет («занят, повторите позже; статус рассылки не определён»), чтобы администратор видел причину, а не гадал.
7. **Защита «TG только в боевом контейнере»:** рекомендуется: TG опрашивается только если рецепт `prod-backfill-phones` передал явный флаг (например, `--telegram-from-container`), а при запуске без него TG-аккаунты получают строку «Telegram не опрашивался вне боевого контейнера» (в итоге — «воркер недоступен»). Это защита от запуска локального рецепта с `.env`, указывающим на боевую базу (два адреса, A1). Альтернатива — проверка `/.dockerenv` (A7 `[ASSUMED]`): проще, но хрупче. Если планировщик сочтёт защиту лишней — оставить хотя бы текст справки.
8. **Если Docker недоступен** (`docker.from_env()` падает — копия без `docker.sock`): считать исходом по каждому WA/MAX-аккаунту («воркер недоступен»), а не аварией прогона; для боевого `web` это не штатный случай, но тогда сводка скажет об этом сама.
9. **Порядок аккаунтов и фильтры:** сортировка по `id`; `--limit K` режет после фильтров по числу **обработанных** аккаунтов; `--type` допускает повтор (`append`), чтобы исключить TG без отдельного флага.
10. **Подъём только для `status == "active"`** (сужение D-12 для пути подъёма, A4); если планировщик считает это противоречием D-12 — вынести владельцу.
11. **Баннер режима:** первая строка вывода — режим (`РЕЖИМ ПРОСМОТРА` / `РЕЖИМ ЗАПИСИ`) и числа кандидатов по типам; D-08 требует, чтобы запись по умолчанию была названа прямо.

## Sources

### Primary (HIGH confidence)
- Прочитанный исходник репозитория: `app/application/accounts/phone.py`, `app/services/{wa,max}_container_manager.py`, `app/messengers/{base,whatsapp,max,telegram_user,telegram_pool}.py`, `app/services/messenger_factory.py`, `app/worker/{tasks,celery_app}.py`, `app/application/scheduling/use_cases.py`, `app/pages/accounts.py`, `app/models/{messenger_account,phone_guard}.py`, `app/services/{phone,log_masking}.py`, `wa_worker/{index,own_phone}.js`, `max_worker/main.py`, `docker-compose.prod.yml`, `Dockerfile`, `.dockerignore`, `justfile`, `scripts/*.py`.
- Гейты и тесты: `tests/test_phone_privacy_gate.py`, `tests/test_application/test_phone_single_writer_gate.py`, `tests/test_phone_gates_parity.py`, `tests/test_services/test_log_masking.py`, `tests/test_planning/*`, `tests/test_scripts/test_recompress_attachments.py`, `tests/account_label_support.py`, `tests/conftest.py`.
- Telethon 1.42.0 (`.venv/lib/python3.12/site-packages/telethon`, пин `uv.lock:2040-2041`): `client/telegrambaseclient.py`, `client/users.py`, `client/auth.py`, `client/updates.py`, `errors/rpcerrorlist.py`, `errors/rpcbaseerrors.py`, `sessions/string.py`.
- Celery 5.6.2 (`.venv/.../celery`): `worker/request.py`, `app/control.py`, `app/defaults.py`; локальная сборка сообщения протокола 2.
- Образы в Docker без сети и томов: Baileys 7.0.0-rc14 (`lib/Socket/socket.js`, `lib/Types/index.js` в `broadcaster-wa-worker:latest`), PyMax 2.5.0 (`pymax/app.py`, `types/domain/user.py` в `broadcaster-max-worker:latest`).
- Боевая сторона, только чтение: `docker ps`, `docker inspect --format`, `docker images`, `docker network inspect --format` (флаги драйвера/IPv6), `docker logs` (через маску цифр; агрегаты).
- `[CITED: https://core.telegram.org/api/errors]` — раздел 406 `AUTH_KEY_DUPLICATED` (скачан и прочитан).

### Secondary (MEDIUM confidence)
- `[CITED: https://core.telegram.org/api/datacenter]` — раздел параллельных сессий, `tmp_sessions` (результат поиска, страница целиком не читалась).
- `[CITED: https://docs.telethon.dev/en/stable/quick-references/faq.html]` — «use a different session for each place»; про `AuthKeyDuplicatedError` на странице нет.
- Обсуждения Baileys о 405 «Connection Failure» (`github.com/WhiskeySockets/Baileys` #1939, #999, #1242) — по заголовкам и выдержкам результатов поиска.

### Tertiary (LOW confidence)
- Предположения A1–A8 из «Assumptions Log».

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — все пины прочитаны, новых пакетов нет.
- Architecture: HIGH — каждое звено прочитано в коде; ловушка адаптеров и мёртвый `TelegramPool` подтверждены `grep`/чтением.
- Pitfalls: HIGH по WA/TG/гейтам (измерено или прочитано), MEDIUM по поведению Telegram (расхождение официальной страницы и боевого замера) и MAX (ответ сервера при восстановлении не измерялся).
- Валидация: HIGH — базовые линии прогнаны (1161 / 31 / 218+2 / 22), предикаты гейтов проверены на положительном и отрицательном примерах.

**Research date:** 2026-11-23
**Valid until:** 2026-12-23 для кода и гейтов (пока не сменится Фаза 16–19); для поведения Telegram и WhatsApp — пересмотреть после первого боевого прогона (`--dry-run --account-id`).
