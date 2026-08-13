# Phase 4: Дашборд и история — Research

**Researched:** 2026-08-13
**Domain:** Server-rendered аналитика отправок (FastAPI + SQLAlchemy async + Jinja2), HTMX-опрос, потоковый CSV-экспорт, постановка повтора в боевую очередь Celery/Redis
**Confidence:** HIGH (почти всё проверено чтением исходников и исполнением кода в этой сессии; внешних зависимостей фаза не вводит)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Скопировано дословно из `.planning/phases/04-dashbord-i-istoriya/04-CONTEXT.md` §Implementation Decisions.

**Метрики за сутки (DASH-01)**
- **D-01:** Четыре плитки дашборда показывают **только отправки**: «Отправок за сутки», «Успешно», «Ошибок», «Групп охвачено». Счётчики сущностей (объявления/аккаунты/группы) остаются в сайдбаре через `nav_counts` и плитками не дублируются. Нынешний состав `stats` в `app/pages/dashboard.py` заменяется целиком.
- **D-02:** «Сутки» — **скользящие 24 часа** (`now - 24h`), не календарный день. Заодно чинится текущий расчёт `sent_today` (`app/pages/dashboard.py:54`), который берёт UTC-полночь и для пользователя в UTC+3 отсчитывает «сегодня» с трёх ночи.
- **D-03:** На плитке делается **дельта** («к предыдущим суткам»), **спарклайн из макета не делается** — 12 столбиков дублируют heatmap ниже на той же странице. Прецедент отбрасывания макетного элемента: Фаза 2 D-17, Фаза 3 D-12.
- **D-04:** Плитки, heatmap и ближайшие отправки считаются **только при загрузке страницы**. Живая только лента (DASH-03) — опрос агрегатов был бы самой дорогой частью страницы.

**Живая лента (DASH-03)**
- **D-05:** Источник ленты — **только `SendLog`**. Смешанная лента макета (переподключение воркера, синк группы, активация расписания, flood-wait) не воспроизводится: источника этих событий в БД нет, а заводить таблицу событий — отдельная фаза.
- **D-06:** Обновление — **HTMX-опрос** (`hx-trigger="every Ns"`) на паршале ленты, вендоренный htmx 1.9.10. SSE отклонён: требует долгоживущего соединения на вкладку, правки nginx (`proxy_buffering off`) и класса тестов, которого в проекте нет.
- **D-07:** Частота 15–30 с, **бессрочно** — без автостопа. Запрос дешёвый (LIMIT 10 по индексу `sent_at`), а самоостанавливающийся опрос сделал бы ленту тихо мёртвой на открытой вкладке.
- **D-08:** Строка ленты — как в макете (строки 436–442): точка статуса, текст события, «N назад» через существующий `time_ago_for_user`; 6–10 строк. Строка кликабельна и ведёт в запись истории — поэтому `/history/{id}` сохраняется (D-24).

**Активность за неделю (DASH-04)**
- **D-09:** Делается **настоящий heatmap 7×24** (строки — дни недели, колонки — часы), а не бар-чарт из 28 столбцов, как в макете (строки 447–462).
- **D-10:** Раскладка по дням и часам — **в таймзоне пользователя**, не в UTC.
- **D-11:** Ячейка считает **все отправки** за час; насыщенность цвета — относительно самого горячего часа окна. Ошибки отдельной шкалой не выделяются.
- **D-12:** Окно — **последние 7 суток** (скользящее). Подписи дней следуют окну, а не фиксированному ПН–ВС.

**Ближайшие отправки (DASH-02)**
- **D-13:** **Одно расписание = одна строка** с подписью «N групп · Канал».
- **D-14:** Показываются **ближайшие 5–8** по `Schedule.next_run_at`, без ограничения по времени вперёд.
- **D-15:** Расписания, которые **не выстрелят**, показываются с пометкой причины: «объявление в черновике» (Фаза 2 D-01), «аккаунт отключён», «все группы выключены» (Фаза 3 D-05).
- **D-16:** Клик по строке ведёт **в редактор объявления**.

**Повтор отправки (HIST-04)**
- **D-17:** Повтор отправляет **текущий контент объявления** из БД, а не снапшот из журнала. Переиспользует `send_message_once` (`app/application/scheduling/use_cases.py:215`) без правок.
- **D-18:** Повтор ставится **в очередь Celery** тем же таском, что и боевая рассылка (`send_telegram_message`, `app/worker/tasks.py:224`). UI отвечает «поставлено в очередь». — **Reversibility:** costly.
- **D-19:** Повторять можно **только неуспешные** записи — `fail` и `account_disconnected`. Кнопка не рендерится у успешных, и сервер проверяет то же самое.
- **D-20:** Баланс сообщений за повтор **списывается как обычно**. Биллинг не правится.
- **D-21:** Если объявления, группы или аккаунта больше нет в БД — **кнопка недоступна с объяснением**, проверка выполняется **до постановки в очередь**.
- **D-22:** Новая запись **никак не связана** с исходной. Колонка `retried_from_id` не вводится.
- **D-23:** Защита от повторного нажатия — **общая панель подтверждения** с настоящей формой POST (макрос `components/modal.html`).

**История: экспорт, фильтры, ошибка (HIST-01…03)**
- **D-24:** Страница записи `GET /history/{log_id}` (`history/detail.html`) **сохраняется и переверстывается**.
- **D-25:** Экспорт — **CSV с BOM UTF-8**. Стандартный модуль `csv`, новых зависимостей нет; XLSX отклонён.
- **D-26:** Файл отдаётся **синхронно `StreamingResponse`** курсором по БД, обычной ссылкой `GET /history/export` с теми же query-фильтрами, что и список. Работает без JS.
- **D-27:** Жёсткий потолок **~50 000 строк** с явным сообщением «сузьте период», а не тихая обрезка.
- **D-28:** Колонки экспорта — время, канал, аккаунт, группа, заголовок объявления, статус, текст ошибки, `task_id`. **Снапшот тела объявления не включается.**
- **D-29:** Фильтры истории — **чипсы из макета** (строки 810–824) для статуса, канала и периода; переиспользуется макрос чипсов Фазы 2 (D-17). **Фильтр по аккаунту остаётся** и реализуется `select`'ом рядом с чипсами.
- **D-30:** Варианты периода: **сегодня / 7д / 30д / всё**. Произвольный диапазон дат не делается.
- **D-31:** Над списком показывается **точное число найденного** отдельным `COUNT` с теми же фильтрами.
- **D-32:** Текст ошибки **всегда развёрнут** в строке у неуспешных записей; длинный обрезается по высоте с раскрытием.
- **D-33:** Кнопка копирования кладёт в буфер **диагностический блок**: время, канал, группа, объявление, `task_id` и текст ошибки.
- **D-34:** Базовый путь копирования без JS — **`user-select: all`** на блоке ошибки; сама кнопка без Alpine не рендерится.

**Сквозное**
- **D-35:** Агрегации живут в **одном модуле аналитики отправок** с чистыми функциями (метрики за окно, heatmap, лента, ближайшие отправки, счётчик истории). Его зовут и дашборд, и история, а в Фазе 6 — админка.
- **D-36:** Добавляется **составной индекс `(user_id, sent_at)`** на `send_logs` отдельной ревизией Alembic. ⚠️ Ревизия встаёт в очередь за невыкаченной `0013`. — **Reversibility:** reversible.
- **D-37:** **Кэша агрегатов нет.** Считаем на каждый рендер.
- **D-38:** **Один запрос на блок**: метрики — один, heatmap — один, ближайшие — один, лента — один.
- **D-39:** Пустые состояния — **поблочные**. Плитки видны всегда (нули — честный ответ), а heatmap, лента и ближайшие отправки заменяются `empty_state` со своим текстом.
- **D-40:** Пустое состояние ведёт **по тому, чего не хватает**: нет аккаунта → «Подключить аккаунт»; есть аккаунт, нет объявлений → «Создать объявление»; есть объявления, нет расписаний → «Настроить расписание».
- **D-41:** Пустой результат фильтров в истории — **отдельный текст** «Ничего не найдено · измените фильтры или период» с кнопкой «СБРОСИТЬ».

### Claude's Discretion

- Точное значение частоты опроса ленты в пределах 15–30 с и число строк в пределах 6–10.
- Точный порог потолка экспорта в окрестности 50 000 и формулировка предупреждения.
- Формулировки пометок причин у ближайших отправок (D-15) и форма их отображения (бейдж, приглушение строки).
- Цветовая шкала heatmap (число ступеней, дискретная или непрерывная), подписи осей, поведение подсказки на ячейке.
- Мобильная раскладка дашборда в пределах брейкпоинтов макета (860/900/1080px), включая то, как heatmap 7×24 ведёт себя на 320px.
- Имена макросов и файлов новых компонентов (ячейка heatmap, плитка метрики с дельтой, строка ленты).
- Судьба JSON-API `app/routes/history.py` (`GET /stats`, `GET ""`) — проверить потребителей и либо выровнять, либо снести.
- Обращение со старыми записями, у которых `messenger_type` или `group_id` равны `NULL`.
- Порядок объявления маршрутов: `GET /history/export` обязан быть объявлен до `GET /history/{log_id}`.

### Deferred Ideas (OUT OF SCOPE)

- **Таблица событий (Event/ActivityLog)** для смешанной ленты макета (D-05).
- **SSE вместо опроса** (D-06).
- **Произвольный диапазон дат в фильтрах истории** (D-30).
- **Асинхронный экспорт через Celery с выкладкой в S3** (D-26).
- **Колонка `retried_from_id` и цепочки повторов** (D-22).
- **Повтор успешной отправки / ручная отправка из истории** (D-19).
- **Снапшот как источник повтора** (D-17).
- **Статистика отправок по группе** (Фаза 3).
- **Прогресс-бар отправок в карточке расписания** (Фаза 2 D-17).
- **Кэш агрегатов дашборда** (D-37).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DASH-01 | Пользователь видит метрики отправок за последние сутки | §Pattern 1 (модуль аналитики), §Pattern 2 (одна выборка на два окна через `case`), §Pitfall 1 (UTC-полночь), §Pitfall 3 (`account_disconnected` — тоже ошибка) |
| DASH-02 | Пользователь видит список ближайших запланированных отправок | §Pattern 5 (`lazy="raise"` требует явных join), §Pitfall 6 (причины D-15 не считаются одним запросом — `group_ids` это JSON) |
| DASH-03 | Пользователь видит живую ленту последних событий отправки | §Pattern 3 (бессрочный опрос htmx), §Pitfall 4 (`load_shell_context` на каждый тик), §Code Examples |
| DASH-04 | Пользователь видит heatmap активности отправок за неделю | §Pattern 4 (бакетирование в Python, а не в SQL), §Pitfall 2 (диалектная ловушка `strftime`/`date_trunc`), §Pitfall 5 (naive datetime на SQLite) |
| DASH-05 | Пользователь видит, какие воркеры его аккаунтов сейчас онлайн | §Standard Stack — **уже реализовано** в `base.html:107-112` из `get_shell_context`; фаза только переиспользует |
| HIST-01 | Пользователь может фильтровать историю по каналу, статусу и периоду | §Pattern 6 (единственное определение фильтров, два импортёра), §Pitfall 8 (макроса чипсов не существует) |
| HIST-02 | Пользователь может увидеть текст ошибки неуспешной отправки и скопировать его | §Pitfall 9 (`navigator.clipboard` недоступен по HTTP), §Open Question 1 (`[data-longtext]` запрещает раскрытие) |
| HIST-03 | Пользователь может выгрузить отфильтрованную историю в файл экспорта | §Pattern 7 (StreamingResponse + сессия жива), §Pitfall 7 (потолок считается ДО начала потока), §Security (CSV formula injection) |
| HIST-04 | Пользователь может повторить отправку из записи истории | §Pattern 8 (диспетчеризация на три канала, а не только Telegram), §Pitfall 10 (гейта баланса нет), §Pitfall 11 (нет серверной идемпотентности) |
</phase_requirements>

---

## Summary

Фаза 4 — это **аналитический слой поверх уже существующих таблиц** плюс **одно новое действие рядом с боевым пайплайном**. Никаких новых внешних зависимостей: `csv` — стандартная библиотека, htmx 1.9.10 и Alpine 3.13.3 уже вендорены, стек FastAPI 0.129.0 / SQLAlchemy 2.0.46 / Jinja2 3.1.6 / Celery 5.6.2 зафиксирован в `pyproject.toml`. Основная работа — правильные запросы и правильная граница модуля.

Три вещи ломают фазу тише всего, и все три проверены в этой сессии. **Первая — диалект.** Тестовая суита идёт по `sqlite+aiosqlite`, бой — по PostgreSQL, а группировка по часу и дню (D-09, D-10) — единственное место фазы, где эти два диалекта расходятся необратимо: `func.strftime` работает на SQLite и падает на PostgreSQL, `date_trunc`/`extract` — наоборот. Ветка «под PostgreSQL» тестами не исполнится ни разу и обнаружится на деплое — ровно тем способом, который отдельно разобран в докстринге ревизии 0015 про `MIN(boolean)`. Отсюда прескрипция: **бакетирование heatmap делается в Python над проекцией `sent_at`, а не выражением в `GROUP BY`.** Дополнительно проверено: SQLite отдаёт `DateTime(timezone=True)` **naive**, PostgreSQL — aware, поэтому нормализация `tzinfo` обязательна в самом модуле аналитики, а не в шаблоне.

**Вторая — D-18 покрывает только Telegram.** `send_telegram_message` — вход одного канала из трёх; WhatsApp и MAX диспетчеризуются `rpush`-ем полной полезной нагрузки в Redis-очереди `wa:queue:{account_id}` / `max:queue:{account_id}` (`app/worker/tasks.py:50-158`), и `SendLog` для них пишет `process_wa_results` / `process_max_results`. Повтор, поставленный через `send_telegram_message`, для WA/MAX-записи просто не сработает. Правильная точка переиспользования — `dispatch_send_tasks()`, которая уже маршрутизирует по `account.type`; вызывать её нужно из нового Celery-таска, а не из HTTP-обработчика (внутри синхронный `redis` клиент).

**Третья — потоковый экспорт живёт ровно потому, что FastAPI 0.129.0 закрывает `Depends(get_db)` ПОСЛЕ отправки тела.** Это проверено по исходнику установленного пакета (`fastapi/routing.py:101-106`: `await response(scope, receive, send)` стоит внутри `async with AsyncExitStack() as request_stack`, а `dependencies/utils.py:636` кладёт генераторные зависимости именно в этот стек). В версиях 0.106–0.127 стек закрывался до отправки, и тот же код давал бы `MissingGreenlet`/закрытую сессию посреди файла. `pyproject.toml:16` уже требует `fastapi>=0.129.0` — этот пин становится несущим и его нельзя ослаблять. При этом тестовая суита эту границу не проверяет вовсе: `conftest.py:54` подменяет `get_db` **не генератором** (`lambda: db_session`), то есть teardown-а в тестах нет и регрессия по времени закрытия сессии автотестами не ловится.

**Primary recommendation:** завести `app/application/analytics/send_analytics.py` с пятью чистыми async-функциями (метрики окна, heatmap, лента, ближайшие отправки, счётчик/фильтры истории), **перенести туда же** `_apply_history_filters` / `_history_filter_params` из `app/pages/history.py` (у них уже два импортёра — история и админка), и сделать так, чтобы список, счётчик (D-31) и экспорт (D-26) звали одну и ту же функцию фильтрации. Повтор (HIST-04) реализовать новым Celery-таском `retry_send`, который переиспользует `dispatch_send_tasks` для всех трёх каналов; HTTP-обработчик делает только проверки владения, пригодности (D-19/D-21) и баланса, после чего зовёт `celery.send_task(...)` по уже существующему в проекте образцу (`app/pages/accounts.py:736-738`).

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Агрегации по `SendLog` (метрики, heatmap, лента, счётчик) | Application (`app/application/analytics/`) | Database | Чистые функции над сессией; их зовёт и дашборд, и история, и Фаза 6 — ни один из этих потребителей не имеет права владеть определением (D-35) |
| Определение фильтров истории | Application (`app/application/analytics/`) | — | Сегодня определение лежит в `app/pages/history.py` и импортируется админкой (`app/pages/admin.py:11-12`). Экспорт обязан звать то же самое — иначе HIST-03 перестаёт быть правдой |
| Рендер плиток / heatmap / ленты / карточки истории | Frontend Server (Jinja2 макросы) | — | D-13 Фазы 1: компоненты — макросы через `{% import %}`; build-шаг запрещён (D-02 Фазы 1) |
| Периодическое обновление ленты | Browser (htmx `every Ns`) | Frontend Server (паршал) | D-06; SPA исключён жёсткими рамками milestone |
| Копирование диагностического блока | Browser (Alpine) | — | Прогрессивное улучшение поверх `user-select: all` (D-33/D-34) |
| Потоковая выгрузка CSV | Frontend Server (`StreamingResponse`) | Database (курсор) | D-26; работает без JS обычной ссылкой |
| Постановка повтора в очередь | Application → Queue (Celery/Redis) | Worker | D-18; HTTP-обработчик не имеет права держать соединение на время работы мессенджера |
| Фактическая отправка при повторе | Worker (`send_message_once` / wa-worker / max-worker) | — | Протоколы отправки не трогаются (жёсткие рамки milestone) |
| «Воркеры онлайн» (DASH-05) | Frontend Server (`get_shell_context`) | Database | Фаза 1 D-19: источник — `MessengerAccount.status`, Docker SDK на рендере не вызывается **ни при каких условиях** |

---

## Standard Stack

Фаза **не вводит ни одной новой зависимости**. Всё нужное уже установлено и закреплено.

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `fastapi` | 0.129.0 (`>=0.129.0`) | Маршруты, `StreamingResponse`, `Depends(get_db)` | `[VERIFIED: uv run python -c "import fastapi"` → `0.129.0`; `pyproject.toml:16]`. Пин `>=0.129.0` несущий для D-26 — см. §Pattern 7 |
| `starlette` | 0.52.1 | `StreamingResponse`, `Jinja2Templates` | `[VERIFIED: uv run python; app/pages/__init__.py:33-35 явно ссылается на 0.52.1]` |
| `sqlalchemy[asyncio]` | 2.0.46 (`>=2.0.46`) | Все агрегации, `AsyncSession.stream()` | `[VERIFIED: uv run python; pyproject.toml:26]` |
| `jinja2` | 3.1.6 | Макросы плиток / heatmap / строк ленты | `[VERIFIED: uv run python; pyproject.toml:19]` |
| `celery[redis]` | 5.6.2 | Постановка повтора (HIST-04) | `[VERIFIED: uv run python; pyproject.toml:13]` |
| `alembic` | 1.18.4 | Ревизия 0016 (D-36) | `[VERIFIED: uv run alembic --version]` |
| `csv` (stdlib) | Python 3.12.13 | Экспорт (D-25) | `[VERIFIED: pyproject requires-python; uv run python --version]`. D-25 явно запрещает новые зависимости |
| `zoneinfo` (stdlib) | Python 3.12.13 | Таймзона пользователя для heatmap (D-10) | `[VERIFIED: app/pages/common.py:3,140-149]` — уже используется |

### Supporting (вендоренные, без пакетного менеджера)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| htmx | 1.9.10 | Опрос ленты (D-06), бесконечная прокрутка истории | `[VERIFIED: grep -o 'version:"[0-9.]*"' app/static/js/htmx.min.js` → `version:"1.9.10"]` |
| Alpine.js | 3.13.3 | Панель подтверждения повтора, кнопка копирования | `[VERIFIED: grep -o 'version:"[0-9.]*"' app/static/js/alpine.min.js` → `version:"3.13.3"]` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| HTMX-опрос ленты | SSE / WebSocket | Отклонено D-06: долгоживущее соединение на вкладку, `proxy_buffering off` в nginx, класса тестов нет |
| Бакетирование heatmap в Python | `GROUP BY strftime(...)` / `date_trunc(...)` | **Не переносимо между SQLite и PostgreSQL.** Ветка под PostgreSQL не исполняется тестами ни разу — прецедент дефекта описан в `alembic/versions/0015_groups_unique_account_external.py:80-87` |
| `StreamingResponse` для CSV | Celery + S3 | Отклонено D-26: новый таск, экран статуса, уборка файлов |
| CSV | XLSX (`openpyxl`) | Отклонено D-25: новая зависимость + память |
| Кэш агрегатов | Redis (`app/services/billing_cache.py` — образец) | Отклонено D-37: инвалидация из воркера на каждую отправку |

**Installation:** ничего устанавливать не нужно. Проверка окружения — `just sync`.

---

## Package Legitimacy Audit

**Фаза не устанавливает ни одного внешнего пакета.** Экспорт (D-25) использует стандартный модуль `csv`, таймзоны (D-10) — стандартный `zoneinfo`. Все прочие библиотеки уже присутствуют в `pyproject.toml` и установлены в `.venv` — их версии подтверждены исполнением интерпретатора в этой сессии (см. таблицу выше).

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| — | — | — | — | — | — | Новых пакетов нет |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

> Если планировщик обнаружит, что какой-то из планов всё же требует новой зависимости, гейт `package-legitimacy check` обязан быть пройден до записи пакета в план.

---

## Project Constraints (from CLAUDE.md)

Извлечено из `/source/broadcaster/CLAUDE.md` и `/source/broadcaster/.claude/CLAUDE.md`.

| Директива | Как проверяется в этой фазе |
|-----------|------------------------------|
| Python 3.12, управление через `uv` | Все команды — `uv run ...`; добавление зависимости — `just add` (в этой фазе не нужно) |
| Команды через `just` | Тесты — `just test`; миграция — `just migrate "описание"`, накат — `just upgrade` |
| Стек: FastAPI + SQLAlchemy async (PostgreSQL) + Celery/Redis + Jinja2 | Ни один пункт фазы не выходит за него; SPA исключён |
| Тесты: `sqlite+aiosqlite:///:memory:`, полная схема на тест, фикстуры `client`/`db_session`/`auth_headers` | **Прямое следствие для D-09/D-10**: агрегации обязаны работать на обоих диалектах (см. §Pitfall 2) |
| `app/routes/` — JSON-API, `app/pages/` — server-rendered HTML | Экспорт и повтор — страничные маршруты (`app/pages/history.py`), не JSON-API |
| `app/application/` — DDD use cases, `app/domain/` — интерфейсы репозиториев | Модуль аналитики (D-35) кладётся в `app/application/analytics/` — по образцу `app/application/scheduling/` и `app/application/accounts/` |
| graphify: после правки кода — `graphify update .` | Финальный шаг фазы; граф в `graphify-out/` |
| graphify: для вопросов о кодовой базе сначала `graphify query` | Соблюдено при подготовке этого документа |

**Дополнительные ограничения проекта, действующие как CLAUDE.md** (из `.planning/PROJECT.md` §Constraints и жёстких рамок milestone v2.0):
- Протоколы отправки Telegram/WhatsApp/MAX **не трогаются**.
- Build-шага нет; внешних CDN-ресурсов — ноль.
- Только тёмная тема (Фаза 1 D-10).
- Адаптивность — критерий приёмки фазы, а не отдельная задача.

---

## Architecture Patterns

### System Architecture Diagram

```
                    ┌──────────────────── БРАУЗЕР ────────────────────┐
                    │                                                  │
   GET /dashboard ──┤  дашборд (полная страница)                       │
                    │    ├─ плитки метрик + дельта   ← один запрос     │
                    │    ├─ ближайшие отправки       ← один запрос(+1) │
                    │    ├─ heatmap 7×24             ← один поток      │
                    │    └─ живая лента ┐                              │
                    │                   │ htmx every 15–30s, бессрочно │
   GET /dashboard/feed ◄────────────────┘  (D-06, D-07)                │
                    │                                                  │
   GET /history ────┤  чипсы-ссылки (статус/канал/период) + select акк. │
                    │    ├─ счётчик найденного      ← COUNT, те же фильтры
                    │    ├─ карточки data-hrow       ← LIMIT 30 + revealed
                    │    ├─ «ЭКСПОРТ CSV →» ──────────────┐            │
                    │    └─ кнопка «Повторить» (только fail / account_disconnected)
                    └───────────────────────┬─────────────┼────────────┘
                                            │             │
   POST /history/{id}/retry ────────────┐   │             │ GET /history/export
                                        │   │             │  (объявить ДО /history/{log_id}!)
┌──────────────── FastAPI (app/pages/) ─┼───┼─────────────┼──────────────────────┐
│                                        │   │             │                      │
│  load_shell_context (на КАЖДЫЙ         │   │             │                      │
│  страничный маршрут, ~4 запроса)       │   │             │                      │
│         │                              │   │             │                      │
│         ▼                              ▼   ▼             ▼                      │
│   ┌───────────────────────────────────────────────────────────────────────┐    │
│   │   app/application/analytics/send_analytics.py   (D-35, публичный      │    │
│   │   контракт для Фазы 6)                                                │    │
│   │   • send_metrics(session, user_id, now)        → 4 счётчика + дельты  │    │
│   │   • activity_heatmap(session, user_id, now,tz) → сетка 7×24           │    │
│   │   • recent_feed(session, user_id, limit)       → строки ленты         │    │
│   │   • upcoming_sends(session, user_id, now, n)   → расписания + причины  │    │
│   │   • apply_history_filters / history_filter_params / history_count     │    │
│   └───────────────────────────┬───────────────────────────────────────────┘    │
│                               │                                                │
│   проверки повтора (D-19,D-21): владение · статус · ad/group/account есть ·    │
│   баланс (check_balance_cached) → celery.send_task("...retry_send")            │
└───────────────────────────────┼───────────────────────────────┬────────────────┘
                                │                               │
                                ▼                               ▼
                    ┌────── PostgreSQL ──────┐        ┌────── Celery / Redis ──────┐
                    │ send_logs (user_id,    │        │ app.worker.tasks.retry_send│
                    │   sent_at) ← ИНДЕКС    │        │        │                    │
                    │   0016 (D-36)          │        │        ▼                    │
                    │ schedules.next_run_at  │        │ dispatch_send_tasks()       │
                    │ groups / ads /         │        │   ├ tg_user → Celery queue  │
                    │ messenger_accounts     │        │   │   "telegram"            │
                    └────────────────────────┘        │   ├ wa  → rpush wa:queue:N  │
                                                      │   └ max → rpush max:queue:N │
                                                      └────────────┬────────────────┘
                                                                   ▼
                                                      новая запись SendLog
                                                      (send_message_once ИЛИ
                                                       process_wa/max_results)
```

Ключевое чтение диаграммы: **обе страницы входят в один и тот же модуль аналитики** (заметка ROADMAP), а **повтор не создаёт второго пути отправки** — он вливается в ту же `dispatch_send_tasks`, которой пользуется боевой планировщик.

### Recommended Project Structure

```
app/
├── application/
│   └── analytics/
│       ├── __init__.py
│       └── send_analytics.py        # D-35: пять чистых функций + фильтры истории
├── pages/
│   ├── dashboard.py                 # переписывается целиком (D-01…D-16) + маршрут ленты
│   └── history.py                   # + /history/export, + счётчик, + POST повтора
├── worker/
│   └── tasks.py                     # + retry_send; + извлечённый build_dispatch_task
├── templates/
│   ├── dashboard.html               # переверстка по макету 383–464
│   ├── dashboard/
│   │   ├── partial_feed.html        # паршал опроса (имя обязано содержать "partial")
│   │   └── includes/
│   │       ├── metric_tile.html     # плитка с дельтой (макет 387–392, без спарклайна)
│   │       ├── feed_row.html        # строка ленты (макет 436–442)
│   │       ├── upcoming_row.html    # ближайшая отправка (макет 410–423)
│   │       └── heatmap.html         # сетка 7×24 (D-09)
│   └── history/
│       ├── list.html                # чипсы + линейка счётчика + ЭКСПОРТ CSV
│       ├── partial_cards.html
│       ├── detail.html
│       └── includes/history_card.html   # + блок ошибки, копирование, повтор
└── static/css/app.css               # + правила heatmap, плитки с дельтой, чипсов-ссылок

alembic/versions/0016_send_logs_user_sent_at.py   # D-36, down_revision = "0015"
tests/test_migrations/test_0016_send_logs_user_sent_at.py
```

**Почему `app/application/analytics/`, а не `app/repositories/send_log.py`:** репозиторий в проекте — CRUD одной сущности (`app/repositories/send_log.py` целиком про `SendLog`), а агрегации фазы соединяют `SendLog` + `Schedule` + `Ad` + `Group` + `MessengerAccount`. Прецедент ровно такой формы уже есть: `app/application/scheduling/use_cases.py` (`collect_due_schedules(session, *, now, check_limit)`) и `app/application/accounts/group_resync.py` (`apply_group_resync(session, account, groups, messenger_type=...)`) — обе принимают `AsyncSession` первым позиционным и всё остальное keyword-only.

### Pattern 1: Модуль аналитики — чистые функции над сессией (D-35)

**What:** пять async-функций, принимающих `AsyncSession` и явные параметры, возвращающих датаклассы. Ни одна не читает `Request`, `Settings` через глобал и ничего не пишет в БД.
**When to use:** любая агрегация по отправкам в этой и следующих фазах.

```python
# app/application/analytics/send_analytics.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.send_log import SendLog

# Единственный источник значений статуса журнала на проект.
# [VERIFIED: app/application/scheduling/use_cases.py:246,274,292,334 —
#  status="fail" / "account_disconnected" / "ok"; те же три ветки в
#  app/templates/history/includes/history_card.html:40-43]
STATUS_OK = "ok"
STATUS_FAIL = "fail"
STATUS_ACCOUNT_DISCONNECTED = "account_disconnected"
FAILED_STATUSES = (STATUS_FAIL, STATUS_ACCOUNT_DISCONNECTED)


@dataclass(slots=True)
class SendMetrics:
    total: int
    ok: int
    failed: int
    groups: int
    total_prev: int
    ok_prev: int
    failed_prev: int
    groups_prev: int
```

**Почему `slots=True`:** так объявлен `DispatchTask` (`app/application/scheduling/use_cases.py:35`) — тот же приём, тот же слой.

### Pattern 2: Метрики и дельта — ОДИН запрос на два окна (D-01, D-02, D-38)

**What:** окно берётся шириной 48 часов, а разделение «текущие сутки / предыдущие» делается условными агрегатами. Один round-trip вместо двух.
**When to use:** любая плитка «значение + дельта к предыдущему периоду».

```python
async def send_metrics(
    session: AsyncSession, *, user_id: int, now: datetime | None = None,
    window: timedelta = timedelta(hours=24),
) -> SendMetrics:
    now = now or datetime.now(timezone.utc)
    cur_start = now - window          # D-02: СКОЛЬЗЯЩИЕ сутки, не UTC-полночь
    prev_start = now - window * 2

    cur = SendLog.sent_at >= cur_start
    row = (await session.execute(
        select(
            func.sum(case((cur, 1), else_=0)).label("total"),
            func.sum(case((cur & (SendLog.status == STATUS_OK), 1), else_=0)).label("ok"),
            func.sum(case((cur & SendLog.status.in_(FAILED_STATUSES), 1), else_=0)).label("failed"),
            func.count(func.distinct(case((cur, SendLog.group_id)))).label("groups"),
            func.sum(case((~cur, 1), else_=0)).label("total_prev"),
            # ... те же три для предыдущего окна
        ).where(SendLog.user_id == user_id, SendLog.sent_at >= prev_start)
    )).one()
    ...
```

`func.sum(case(...))` и `func.count(func.distinct(...))` **проверены исполнением на `sqlite+aiosqlite` в этой сессии** — оба возвращают корректные значения. `func.sum` над пустым набором отдаёт `NULL`, поэтому все значения обязаны проходить через `int(x or 0)` (тот же приём, что `app/pages/common.py:339`).

### Pattern 3: Бессрочный опрос ленты (D-06, D-07)

**What:** `hx-trigger="every 20s"` на **стабильном контейнере**, паршал приходит в `innerHTML` (умолчание htmx).
**When to use:** живые данные, которые обязаны обновляться, пока вкладка открыта.

htmx-семантика подтверждена документацией: `every <timing>` шлёт GET по интервалу и кладёт ответ в `innerHTML` элемента; **остановить опрос со стороны сервера можно кодом HTTP 286**; фильтр в квадратных скобках допустим и ставится **после** объявления опроса (`every 1s [someConditional]`). `[CITED: github.com/bigskysoftware/htmx — www/content/attributes/hx-trigger.md, www/content/docs.md]`

**Почему `innerHTML`, а не `outerHTML` — вопреки конвенции проекта.** Все существующие опросы проекта самоостанавливающиеся и построены на `hx-swap="outerHTML"` с условными атрибутами (`app/templates/accounts/partials/sync_status_card.html:46`, `app/templates/account_groups/partials/sync_result.html:50`) — исчезновение атрибутов **и есть** механизм остановки, что прямо закреплено тестом `test_sync_polling_stops` (`tests/test_pages/test_htmx_preserved.py:232-245`). Для D-07 нужен ровно обратный результат. При `outerHTML` забытые в паршале `hx-get`/`hx-trigger` убьют ленту **молча** — страница выглядит исправной, а данные замерли. При `innerHTML` на стабильном контейнере атрибуты не покидают DOM в принципе, и такой отказ невозможен по построению.

Если планировщик всё же выберет `outerHTML` ради единообразия — **парный тест обязателен** (по образцу Фазы 1): один утверждает, что паршал сам несёт `hx-get` и `hx-trigger`, второй — что страница их несёт. Один тест без пары зеленеет вакуумно.

### Pattern 4: Heatmap — бакетирование в Python, не в SQL (D-09…D-12)

**What:** SQL отдаёт только `sent_at` в окне; раскладку по `(день, час)` делает Python в таймзоне пользователя.
**When to use:** любая группировка по календарным единицам в этом проекте.

```python
async def activity_heatmap(
    session: AsyncSession, *, user_id: int, now: datetime, tz: ZoneInfo, days: int = 7,
) -> list[list[int]]:
    window_start = now - timedelta(days=days)
    grid = [[0] * 24 for _ in range(days)]

    result = await session.stream(
        select(SendLog.sent_at)
        .where(SendLog.user_id == user_id, SendLog.sent_at >= window_start)
        .execution_options(yield_per=1000)
    )
    local_origin = window_start.astimezone(tz)
    async for (sent_at,) in result:
        # SQLite отдаёт naive, PostgreSQL — aware. Нормализация ОБЯЗАТЕЛЬНА,
        # тот же приём, что format_datetime_for_user (app/pages/common.py:161-162).
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        local = sent_at.astimezone(tz)
        offset_hours = int((local - local_origin).total_seconds() // 3600)
        if 0 <= offset_hours < days * 24:
            grid[offset_hours // 24][local.hour] += 1
    return grid
```

Три свойства, каждое проверено:
1. `AsyncSession.stream()` работает и на `aiosqlite` **(исполнено в этой сессии: `s.stream(select(SendLog.id))` вернул все строки)**, и на asyncpg — где `yield_per` включает настоящий server-side cursor. `[CITED: docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html — AsyncSession.stream, AsyncResult.yield_per, partitions]` Память — O(размер батча), а не O(окна).
2. Проекция `select(SendLog.sent_at)` вместо ORM-сущности: не создаётся ни одного объекта `SendLog`, identity map не растёт.
3. **Все 12 поддерживаемых таймзон — с фиксированным смещением, DST нет ни у одной.** Проверено исполнением над `app.constants.VALID_TIMEZONES`: смещения в январе/апреле/июле/октябре 2026 совпадают для каждой зоны (Москва +3:00, Калининград +2:00, …, Камчатка +12:00, UTC 0). Значит границы дней и часов в локальном времени не «схлопываются» и не «раздваиваются» — краевых случаев DST в этой фазе нет.

**Подписи дней (D-12) следуют окну.** Ряд `i` — это сутки, начинающиеся в `local_origin + i дней`; подпись берётся из `local_origin + timedelta(days=i)`, а не из фиксированного «ПН…ВС» макета.

### Pattern 5: Ближайшие отправки — `lazy="raise"` требует явных join (D-13…D-16)

**What:** выборка расписаний с объявлением и аккаунтом одним запросом через явные `join`, без обращения к relationship-атрибутам.
**When to use:** любое чтение `Schedule` вне `collect_due_schedules`.

```python
stmt = (
    select(Schedule, Ad, MessengerAccount)
    .join(Ad, Schedule.ad_id == Ad.id)
    .outerjoin(MessengerAccount, Schedule.account_id == MessengerAccount.id)
    .where(
        Ad.user_id == user_id,
        Schedule.is_active.is_(True),
        Schedule.next_run_at.isnot(None),
    )
    .order_by(Schedule.next_run_at.asc())
    .limit(limit)
)
```

`Schedule.ad` и `Schedule.account` объявлены `lazy="raise"` `[VERIFIED: app/models/schedule.py:23-24 — `ad = relationship("Ad", lazy="raise")`, `account = relationship("MessengerAccount", lazy="raise")`]`. Обращение к ним без `joinedload` поднимает исключение — в `collect_due_schedules` именно поэтому стоит `.options(joinedload(Schedule.ad), joinedload(Schedule.account))` (`use_cases.py:66`). Выбор сущностей в `select(...)` вместо `joinedload` здесь предпочтительнее: значения нужны все, а `unique()` при этом не требуется.

`outerjoin` для аккаунта обязателен: `Schedule.account_id` — nullable с `ondelete="SET NULL"` `[VERIFIED: app/models/schedule.py:16-20 и комментарий «при удалении messenger-аккаунта расписание сохраняется и отвязывается (issue #35)»]`. Внутренний join потерял бы ровно те строки, ради которых написан D-15 («аккаунт отключён»).

**Принадлежность расписания идёт через `Ad.user_id`, а не через `Schedule.user_id`** — колонки `user_id` у `Schedule` нет `[VERIFIED: app/models/schedule.py:12-36 — id, ad_id, account_id, group_ids, days_of_week, times_of_day, timezone, is_active, next_run_at, created_at]`; то же обоснование выписано в `app/pages/common.py:289-290`.

### Pattern 6: Одно определение фильтров истории на трёх потребителей (HIST-01, HIST-03, D-31)

**What:** `apply_history_filters(query, ...)` и `history_filter_params(...)` переезжают из `app/pages/history.py` в модуль аналитики и получают публичные имена; их зовут список, паршал, счётчик, экспорт и админка.
**When to use:** обязательно — иначе HIST-03 («выгружен именно отфильтрованный результат») перестаёт быть проверяемым утверждением.

Сегодня определение единственное, но лежит в страничном слое и импортируется как приватное имя из другого страничного модуля:

```python
# app/pages/admin.py:11-12  [VERIFIED]
    _apply_history_filters,
    _history_filter_params,
```

Переезд обязан быть **поведенчески нулевым**: сигнатура `(query, status, messenger_type, account_id, period)` и семантика сохраняются дословно, иначе покраснеют `test_infinite_scroll_keeps_filters` (`tests/test_pages/test_htmx_preserved.py:209`) и `test_history_filters_survive_pagination` (`tests/test_pages/test_responsive_markup.py:547`). Единственное расширение — вариант периода `today` (D-30), которого сейчас нет: текущая реализация знает только `7d` и `30d` `[VERIFIED: app/pages/history.py:53-58]`.

⚠️ **`today` — единственный фильтр фазы, зависящий от таймзоны пользователя.** «Сегодня» обязан отсчитываться от локальной полуночи (`datetime.now(tz).replace(hour=0,...)` → в UTC), иначе повторится дефект D-02. Фильтрация по `account_id` идёт через `Group.account_id` и работает только потому, что запрос уже содержит `outerjoin(Group)` `[VERIFIED: app/pages/history.py:46-52, 80-85]` — экспорт обязан строить тот же `outerjoin`, иначе фильтр по аккаунту тихо развалится.

### Pattern 7: Потоковый CSV с BOM (D-25, D-26, D-27, D-28)

**What:** `StreamingResponse` над async-генератором, который тянет строки курсором и отдаёт закодированные байты.
**When to use:** экспорт истории.

```python
@router.get("/history/export")            # ← ОБЪЯВИТЬ ДО GET /history/{log_id}
async def history_export(request: Request, ..., db: AsyncSession = Depends(get_db)):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Потолок ПРОВЕРЯЕТСЯ ДО начала потока: как только первый байт ушёл,
    # сменить код ответа уже нельзя.
    total = await history_count(db, user_id=user.id, ...)
    if total > EXPORT_ROW_CAP:
        return RedirectResponse(url="/history?export=too_many&...", status_code=302)

    async def rows():
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL,
                            lineterminator="\r\n")
        yield codecs.BOM_UTF8                 # D-25: BOM для Excel (b"\xef\xbb\xbf")
        writer.writerow(HEADER)
        yield _flush(buf)
        result = await db.stream(stmt.execution_options(yield_per=500))
        async for log, group in result:
            writer.writerow(_csv_row(log, group, user))
            yield _flush(buf)

    return StreamingResponse(
        rows(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="history-export.csv"'},
    )
```

**Почему сессия переживает поток — и почему это несущий факт.** В FastAPI 0.129.0 отправка ответа стоит **внутри** стека, в котором лежат генераторные зависимости:

```python
# .venv/.../fastapi/routing.py:101-106   [VERIFIED — прочитано в этой сессии]
async with AsyncExitStack() as request_stack:
    scope["fastapi_inner_astack"] = request_stack
    async with AsyncExitStack() as function_stack:
        scope["fastapi_function_astack"] = function_stack
        response = await f(request)
    await response(scope, receive, send)
```

```python
# .venv/.../fastapi/dependencies/utils.py:636-638   [VERIFIED]
            use_astack = request_astack
            if sub_dependant.scope == "function":
                use_astack = function_astack
```

`get_db` объявлен обычной генераторной зависимостью без `scope="function"` `[VERIFIED: app/dependencies.py:18-22]`, значит попадает в `request_astack`, который закрывается **после** `await response(...)`. В FastAPI 0.106–0.127 стек закрывался до отправки — тот же код тогда рвал бы сессию посреди файла. **`pyproject.toml:16` (`fastapi>=0.129.0`) становится несущим ограничением фазы.**

⚠️ **Тесты этой границы не проверяют.** `conftest.py:54` подменяет `get_db` на `lambda: db_session` — это не генератор, teardown-а нет вовсе, и время закрытия сессии в суите не наблюдается. Регрессию поймает только ручной прогон на боевом стеке. Планировщику стоит выписать этот факт прямо в план.

**Экранирование формул — не опция.** См. §Security Domain.

**Разделитель.** Требование D-25 — читаемость в Excel. BOM решает кодировку, но не разделитель: русская локаль Excel берёт разделитель списка из системных настроек (`;`), и файл с запятыми открывается одной колонкой. `;` вместе с `QUOTE_MINIMAL` — практичный выбор; строгий RFC 4180 с запятой тоже допустим, но тогда обещание «Excel открывает нормально» выполняется только наполовину. **Вынесено в Open Question 2.**

### Pattern 8: Повтор — одна диспетчеризация на три канала (HIST-04, D-17, D-18)

**What:** HTTP-обработчик проверяет и ставит задачу; Celery-таск собирает `DispatchTask` и зовёт существующую `dispatch_send_tasks`.
**When to use:** обязательно — иначе повтор работает только для Telegram.

Страничный слой (образец уже есть в проекте):

```python
# app/pages/history.py
@router.post("/history/{log_id}/retry")
async def history_retry(request: Request, log_id: int, ...):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    log = await db.get(SendLog, log_id)
    if not log or log.user_id != user.id:                    # владение на входе
        return RedirectResponse(url="/history", status_code=302)
    if log.status not in FAILED_STATUSES:                    # D-19, сервер не верит клиенту
        return RedirectResponse(url="/history", status_code=302)

    reason = await retry_precheck(db, log, user)             # D-21, ДО очереди
    if reason:
        return RedirectResponse(url=f"/history?retry_error={reason}", status_code=302)

    # Локальный импорт — тот же приём, что в accounts (позволяет подмену в тестах).
    from app.worker.celery_app import celery
    celery.send_task("app.worker.tasks.retry_send", args=[log.id, user.id])
    return RedirectResponse(url="/history?retry=queued", status_code=302)
```

`[VERIFIED: app/pages/accounts.py:736-738 — `from app.worker.celery_app import celery` / `celery.send_task(task_name, args=[account.id])`]` — единственный способ, которым страничный слой этого проекта ставит задачи. Ни `.delay()`, ни `.apply_async()` в `app/pages/`, `app/routes/`, `app/services/` не встречаются ни разу.

**Почему нельзя обойтись `send_telegram_message` (правка к D-18).** Диспетчеризация разветвляется по типу аккаунта:

```python
# app/worker/tasks.py:62-75  [VERIFIED]
    for task in tasks_to_dispatch:
        if task.type == "tg_user":
            tg_tasks.append(task)
        elif task.type == "wa":
            wa_tasks_by_account.setdefault(task.account_id, []).append(task)
        elif task.type == "max":
            max_tasks_by_account.setdefault(task.account_id, []).append(task)
    for task in tg_tasks:
        send_telegram_message.apply_async(
            args=[task.ad_id, task.group_id, task.account_id, task.schedule_id],
            queue="telegram",
        )
```

WA и MAX не проходят через Celery-таск вовсе: их полезная нагрузка кладётся `rpush`-ем в `wa:queue:{account_id}` / `max:queue:{account_id}` вместе с `ad_text`, `ad_title`, `ad_images` (уже развёрнутыми в полные URL), `group_external_id`, `group_name` (`tasks.py:93-107`, `132-146`), а `SendLog` для них пишут `process_wa_results` / `process_max_results`. Повтор WA-записи через `send_telegram_message` попал бы в `send_message_once`, где `messenger_factory` построил бы WhatsApp-адаптер и пошёл бы синхронным путём мимо контейнера аккаунта — то есть по второму, непроверенному маршруту, что жёсткие рамки milestone прямо запрещают.

**Побочное требование:** заполнение WA/MAX-полей `DispatchTask` живёт инлайном в `collect_due_schedules` (`use_cases.py:186-201`). Чтобы у повтора и планировщика было **одно** определение, этот кусок надо вынести в общий хелпер (`build_dispatch_task(ad, group, account, schedule_id, settings)`) и вызывать из обоих мест. Это та же дисциплина «однажды поправят две из трёх», ради которой в проекте заведён `group_resync` (`app/worker/tasks.py:268-281`).

**Вывод `account_id`.** У `SendLog` колонки `account_id` **нет** `[VERIFIED: app/models/send_log.py:12-31 — id, user_id, schedule_id, ad_id, group_id, ad_title, ad_text, ad_images, group_name, messenger_type, task_id, status, error_message, sent_at]`. Аккаунт выводится через `Group.account_id` — ровно так, как это уже делают страницы (`app/pages/history.py:98`: `"account_id": group.account_id if group else None`). Это и есть корень D-21: Фаза 3 D-10 возвращает удалённую группу синком **новой строкой с новым id**, поэтому `SendLog.group_id` старой записи может указывать в никуда.

**`schedule_id`.** У `SendLog` он nullable и **не является внешним ключом** (ревизия `0005_sendlog_remove_fk_add_snapshots`), поэтому «висячее» значение безвредно — это снапшот. Но `DispatchTask.schedule_id` типизирован как `int` (`use_cases.py:41`), а `send_message_once(..., schedule_id: int)` пишет его в новую запись. Планировщику надо решить, что подставлять при `log.schedule_id is None` (кандидат: `0`, и это стоит назвать в плане, а не оставить на исполнителя).

### Anti-Patterns to Avoid

- **`GROUP BY` по календарной единице средствами диалекта.** `func.strftime('%H', ...)` зеленеет в суите и падает на PostgreSQL; `date_trunc`/`extract` — наоборот. В `app/` **нет ни одного** вызова `strftime`, `date_trunc`, `extract`, `julianday` в SQL-выражениях (проверено grep-ом: все совпадения — это Python-side `datetime.strftime` в шаблонах и `app/pages/common.py:165`). Первое такое выражение станет первым непереносимым местом проекта.
- **Docker SDK ради DASH-05.** Запрещено Фазой 1 D-19 и явно проговорено в докстринге `get_shell_context` (`app/pages/common.py:266-270`): «синхронный Docker SDK, он блокирует event loop на рендере каждой страницы, а в тестах сокет Docker недоступен».
- **Второй расчёт «воркеры онлайн».** Индикатор уже отрисован шеллом (`app/templates/base.html:107-112`, `data-sessions-online`). Дублирование в теле дашборда завело бы два источника одного числа.
- **Возврат `send_message_once` в HTTP-обработчик.** Держит запрос на время работы мессенджера; flood-wait его убьёт (D-18).
- **`innerHTML` / `outerHTML` / `insertAdjacentHTML` / `document.write` в клиентском коде.** По проекту их ноль, и это проверяется по исходнику (Фаза 2, established patterns). Кнопка копирования (D-33) обязана строить узлы DOM или обходиться без разметки вовсе.
- **`<table>`, `<td>`, `<thead>` в новых шаблонах.** `test_template_inventory` (`tests/test_pages/test_responsive_markup.py:1856-1878`) утверждает, что элементов таблицы в проекте не осталось ни одного. Heatmap 7×24 — это CSS Grid, не таблица.
- **Обрезка текста ошибки.** `[data-longtext]` документирован как «ни усечения, ни многоточия, ни скрытия за раскрытием» (`app/static/css/app.css:1003-1012`) — см. Open Question 1.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| «Воркеры онлайн» (DASH-05) | Свой запрос по `MessengerAccount` / вызов Docker | `get_shell_context()` → `sessions_online` / `sessions_total`, уже отрисованные в `base.html:107-112` | Публичный контракт Фазы 1 D-19; Фаза 6 обязана его же переиспользовать |
| «N назад» в ленте (D-08) | Свой расчёт разницы | `time_ago_for_user(value, user)` (`app/pages/common.py:198-230`, глобал Jinja) | Уже решает naive-даты, будущие моменты («только что») и русские склонения |
| Форматирование даты в таймзоне | `value.strftime(...)` в шаблоне | `format_datetime_for_user(value, user, fmt)` (глобал) | Нормализует naive→UTC и переводит в зону пользователя |
| Русские числительные («5 групп») | Тернарники в шаблоне | `plural_ru(count, one, few, many)` (`app/pages/common.py:171-192`, глобал) | Правило 11–14 и хвост %10 уже выписаны один раз |
| Подтверждение повтора (D-23) | Свой диалог / `confirm()` | `{% from "components/modal.html" import modal %}` | Гард повторной отправки, ловушка фокуса, Esc, начальный фокус на «Отмена» уже внутри; собственная панель краснеет в `test_every_modal_site_has_cancel_and_escape` |
| Пустые состояния (D-39, D-40, D-41) | Своя разметка | `{% from "components/empty_state.html" import empty_state %}` — сигнатура `(title, hint=None, action_label=None, action_href=None)` | `action_label`/`action_href` — ровно то, что нужно D-40 |
| Бейджи статуса / иконки канала | Свои спаны | `components/badge.html`, `includes/messenger_icon.html` | Уже используются `history_card.html:35-43` |
| Фильтрация истории | Второй набор `where` в экспорте | `apply_history_filters(...)` — одна функция на список, паршал, счётчик, экспорт, админку | HIST-03 иначе недоказуем |
| Постановка задачи в очередь | Прямой `redis.rpush` из веб-процесса | `celery.send_task(...)` → `dispatch_send_tasks(...)` | Внутри `dispatch_send_tasks` — **синхронный** `redis` клиент (`tasks.py:52,79,118`); в async-обработчике он блокирует event loop |
| Проверка лимита отправок | Своё чтение баланса | `check_balance_cached(session, user_id, "send")` (`app/services/billing_cache.py:28`) | Именно её зовёт планировщик перед диспетчеризацией (`use_cases.py:111`) |
| Списание за повтор | Свой `deduct_message` | Ничего не делать — `send_message_once` списывает при `ok` (`use_cases.py:351-355`) | D-20: биллинг не правится |
| Стриминг больших выборок | `.all()` + срез в Python | `session.stream(stmt.execution_options(yield_per=N))` | server-side cursor на asyncpg; на aiosqlite API идентичен (проверено исполнением) |

**Key insight:** почти всё, что нужно этой фазе на уровне представления, Фазы 1–3 уже построили и **закрепили инвентаризационными тестами**. Самописная копия любого из перечисленных компонентов не просто дублирует код — она краснит существующий тест, который специально написан, чтобы такую копию поймать (`test_modal_site_inventory`, `test_no_utility_classes_anywhere`, `test_template_inventory`). Дешевле переиспользовать.

---

## Common Pitfalls

### Pitfall 1: «Сутки» от UTC-полуночи

**What goes wrong:** метрика «за сутки» у пользователя в UTC+3 начинает отсчёт с 03:00 местного времени, и вечерняя рассылка попадает не в те сутки.
**Why it happens:** прямой перенос текущего кода. `[VERIFIED: app/pages/dashboard.py:54-56 — `today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)`]`
**How to avoid:** D-02 — скользящие `now - 24h`. Для фильтра «сегодня» (D-30) — локальная полночь через `_get_timezone_for_user(user)`.
**Warning signs:** в коде фазы появилось `.replace(hour=0`.
**Note:** ровно тот же дефект живёт в админке (`app/pages/admin.py:62-63`) — это Фаза 6, но модуль аналитики делает его починку однострочной.

### Pitfall 2: Диалектная ловушка в агрегации по времени

**What goes wrong:** `GROUP BY strftime('%Y-%m-%d %H', sent_at)` даёт зелёную суиту и `ProgrammingError` в бою; `date_trunc` — наоборот.
**Why it happens:** тесты идут только по SQLite (`conftest.py:21,38`), боевая база — PostgreSQL. Ветка «под PostgreSQL» не исполняется никогда.
**How to avoid:** §Pattern 4 — бакетирование в Python. Ни одного диалект-специфичного SQL-выражения в `app/` сегодня нет; не заводить первое.
**Warning signs:** `func.strftime`, `func.date_trunc`, `func.extract`, `func.to_char`, `func.julianday` в новом коде.
**Precedent:** `alembic/versions/0015_groups_unique_account_external.py:80-87` — «Тестовая суита идёт по SQLite и оба этих дефекта пропускает, а боевая база — PostgreSQL, и ревизия оборвалась бы прямо на деплое».

### Pitfall 3: «Ошибок» считается только по `status == "fail"`

**What goes wrong:** отправки, не ушедшие из-за отвалившегося аккаунта, не попадают в счётчик ошибок, а «Успешно + Ошибок» не сходится с «Отправок за сутки».
**Why it happens:** статусов три, а не два.
**How to avoid:** `SendLog.status.in_(("fail", "account_disconnected"))`. `[VERIFIED: app/application/scheduling/use_cases.py:246 (`status="fail"`), :274 (`status="fail"`), :292 (`status="account_disconnected"`), :334 (`status = "ok" if result.get("ok") else "fail"`); те же три ветки отрисовываются в app/templates/history/includes/history_card.html:40-43]`
**Warning signs:** сумма плиток «Успешно» и «Ошибок» меньше плитки «Отправок за сутки».
**Смежное:** тот же перечень нужен D-19 (что можно повторять) и фильтру статусов (D-29). Он обязан быть выписан **один раз** в модуле аналитики.

### Pitfall 4: Опрос ленты тянет за собой весь контекст шелла

**What goes wrong:** каждый тик опроса стоит не одного дешёвого запроса, а пяти.
**Why it happens:** `pages_router` объявлен как `APIRouter(dependencies=[Depends(load_shell_context)])` `[VERIFIED: app/pages/__init__.py:41]`, и зависимость висит на **каждом** страничном маршруте, включая паршалы. `get_shell_context` делает четыре round-trip: счётчики (шесть скалярных подзапросов одним запросом), подписка, баланс, сумма транзакций `[VERIFIED: app/pages/common.py:275-339]`.
**How to avoid:** три варианта, назвать выбор в плане —
  (а) принять цену (≈5 запросов × вкладка ÷ 20 с);
  (б) объявить маршрут ленты на отдельном роутере, включённом прямо в `app.include_router(...)` в `app/main.py`, минуя `load_shell_context` — паршал не наследует `base.html` и контекст шелла ему не нужен;
  (в) короткое замыкание внутри `load_shell_context` по пути запроса.
Вариант (б) чище всего и не меняет ни одного существующего маршрута.
**Warning signs:** нагрузка на БД растёт линейно от числа открытых вкладок дашборда, а не от действий пользователей. `.planning/codebase/CONCERNS.md:56-59` уже фиксирует однородную проблему («A background loop executes several aggregate queries every 30 seconds in every web process»).

### Pitfall 5: Naive datetime из SQLite

**What goes wrong:** `TypeError: can't subtract offset-naive and offset-aware datetimes` в тестах — или, хуже, в бою смещение применяется дважды.
**Why it happens:** проверено исполнением в этой сессии: на `sqlite+aiosqlite` колонка `DateTime(timezone=True)` возвращается как `datetime.datetime(2026, 8, 13, 13, 13, 25, 12464)` с `tzinfo=None`; на PostgreSQL/asyncpg — aware.
**How to avoid:** в модуле аналитики нормализовать при чтении: `if v.tzinfo is None: v = v.replace(tzinfo=timezone.utc)` — тот же приём, что `app/pages/common.py:161-162` и `:216-217`.
**Warning signs:** тест зеленеет, а heatmap в бою смещён на величину таймзоны.
**Сопутствующее (проверено):** сравнение aware-datetime в `WHERE` на SQLite **работает** (`count` вернул все 5 посеянных строк) — нормализация нужна только на стороне Python.

### Pitfall 6: Причины D-15 нельзя посчитать тем же запросом

**What goes wrong:** пометка «все группы выключены» либо не появляется, либо появляется ценой запроса на каждую строку.
**Why it happens:** состав групп расписания хранится JSON-списком `Schedule.group_ids` `[VERIFIED: app/models/schedule.py:26 — `group_ids: Mapped[list] = mapped_column(JSON, default=list)`]`, и join по его элементам не построить ни в одном из двух диалектов — это прямо разобрано в `use_cases.py:127-133` и в `alembic/versions/0015_...py:156-171`.
**How to avoid:** после выборки ≤8 строк собрать объединение всех `group_ids` и одним `select(Group.id, Group.is_active).where(Group.id.in_(ids))` получить флаги, дальше решать в Python. Это второй запрос на блок — **осознанное отступление от D-38**, которое надо назвать в плане, а не протащить молча. Альтернатива (отказаться от третьей причины) хуже: без неё блок «Ближайшие отправки» покажет отправку, которой не будет.
**Warning signs:** в коде появился `for schedule in schedules: await session.get(Group, ...)` — N+1.

### Pitfall 7: Потолок экспорта проверяется после начала потока

**What goes wrong:** пользователь получает файл со статусом 200, внутри которого лежит текст ошибки, — или обрезанный файл без единого признака обрезки (ровно то, что D-27 запрещает).
**Why it happens:** у `StreamingResponse` статус и заголовки уходят до первого `yield`. Изменить их после уже нельзя.
**How to avoid:** `history_count(...)` с теми же фильтрами вызывается **до** конструирования `StreamingResponse`. Тот же `COUNT` уже нужен для D-31 — вызов один, потребителя два.
**Warning signs:** проверка `if rows_written > CAP` внутри генератора.

### Pitfall 8: Макроса чипсов, на который ссылается D-29, не существует

**What goes wrong:** план поручает «переиспользовать макрос чипсов Фазы 2», исполнитель его не находит и либо изобретает свой, либо теряет требование.
**Why it happens:** Фаза 2 D-17 говорит «Макрос сворачиваемых фильтров существует с Фазы 1 (`01-04-PLAN.md`) и переиспользуется» — речь про `components/filters.html`, а не про чипсы. `[VERIFIED: .planning/phases/02-obyavleniya-i-raspisaniya/02-CONTEXT.md:60,120]`
**Что есть на самом деле** (проверено):
  - `components/filters.html:24` — макрос `filters(id, action=None, method='get', open_on_desktop=true, label='Фильтры')`, сворачиваемая обёртка с настоящей формой;
  - CSS-примитив `.chip` / `.chip-set` / `.chip__input` / `.chip__label` / `.chip--on` (`app/static/css/app.css:1373-1410`), где `.chip__input` — визуально скрытый **настоящий** input («работает с клавиатуры и уходит без JavaScript»);
  - потребители примитива: `ads/includes/sched_card.html:149-155,203-206` (radio/checkbox) и `schedules/includes/schedule_row.html:110` (только показ, `.chip--on`);
  - **макроса `chips(...)` в `app/templates/components/` нет** — там ровно 13 файлов, все перечислены: alert, avatar, badge, button, card, empty_state, field, filters, modal, mono, progress, table, toggle.
**How to avoid:** решить форму явно. Рекомендация: чипсы статуса / канала / периода — **ссылки** `<a class="chip" href="/history?...">` с `.chip--on` на активной. Базовый путь без JS — один клик вместо «выбрать + Применить»; фильтр по аккаунту (D-29) остаётся `select_field` внутри `filters(...)` с кнопкой.
**⚠️ Если заводится новый файл в `components/`** — `test_template_inventory` утверждает `len(components) == 13` (`tests/test_pages/test_responsive_markup.py:1880-1881`) и его надо обновить в том же плане.

### Pitfall 9: Кнопка копирования молча не работает по HTTP

**What goes wrong:** пользователь жмёт «Копировать», ничего не происходит, в консоли `Cannot read properties of undefined (reading 'writeText')`.
**Why it happens:** `navigator.clipboard` доступен только в secure context (HTTPS либо `localhost`/`127.0.0.1`); на любом другом origin он `undefined` по спецификации. `[CITED: bobbyhadz.com/blog/navigator-clipboard-is-undefined-in-javascript; developer.mozilla.org Clipboard API — secure context]` Развёртывание проекта допускает HTTP-режим: `docker-compose.prod.yml:39-42` выбирает `nginx.conf.template` (HTTPS + 301) **или** `nginx-http.conf.template` (только `listen 80`).
**How to avoid:** D-34 уже даёт базовый путь — `user-select: all` на блоке ошибки. Кнопка обязана (1) проверять `navigator.clipboard && window.isSecureContext` перед вызовом и (2) не бросать исключение, когда его нет. Фолбэк `document.execCommand('copy')` через временный `textarea` — рабочий, но требует создания узла DOM (разрешено: узлами, не `innerHTML`).
**Warning signs:** в разметке `x-on:click="navigator.clipboard.writeText(...)"` без охраны.

### Pitfall 10: Повтор обходит гейт баланса

**What goes wrong:** пользователь с исчерпанным лимитом отправляет через повтор столько, сколько у него неудачных записей.
**Why it happens:** гейт стоит в планировщике, а не в отправке. `[VERIFIED: app/application/scheduling/use_cases.py:111-121 — `checked_users[user_id] = await check_limit(session, user_id, "send")`, и при `not allowed` расписание пропускается]`. `send_message_once` лимита не проверяет вовсе, а `deduct_message` возвращает `False` при нулевом балансе `[VERIFIED: app/services/billing_service.py:50-52]` — **и этот `False` игнорируется** (`use_cases.py:354`: `await deduct_message(session, ad.user_id)` без проверки результата). То есть отправка уже произошла, а списания не было.
**How to avoid:** вызвать `check_balance_cached(db, user.id, "send")` в предпроверке повтора (D-21 и так требует проверок «до постановки в очередь») и отказать с объяснением.
**Warning signs:** в предпроверке повтора нет ни одного упоминания биллинга.

### Pitfall 11: У повтора нет серверной идемпотентности

**What goes wrong:** двойное нажатие / повтор POST по F5 / кнопка «назад» → две отправки в чужую группу. Отозвать нельзя.
**Why it happens:** гард D-23 — **клиентский** (`sending` в Alpine, `components/modal.html:96,105`), и докстринг макроса это признаёт прямо: «Без поднявшегося Alpine гарда НЕТ… Защитой от повторной отправки на этом пути служит идемпотентность самих маршрутов удаления». У удаления идемпотентность есть по природе; у отправки её нет.
**How to avoid:** минимум — PRG (редирект после POST, как во всех маршрутах проекта) плюс внутрипроцессная заявка по образцу `_claim_sync_slot` (`app/pages/accounts.py:747-761`) с ключом `log_id`. Ограничение того приёма (реестр на процесс, не переживает несколько воркеров) в проекте уже описано и принято. Celery-уровневый `rate_limit="20/m"` у `send_telegram_message` (`tasks.py:222`) от двойного клика не защищает.
**Warning signs:** в плане нет ни одного упоминания того, что происходит при двух POST подряд.

### Pitfall 12: `GET /history/export` объявлен после `GET /history/{log_id}`

**What goes wrong:** запрос `/history/export` уходит в `history_detail` с `log_id="export"` → `422`.
**Why it happens:** FastAPI сопоставляет маршруты в порядке объявления.
**How to avoid:** объявить `export` выше — ровно так, как это уже сделано для `/history/partial` (строка 62) относительно `/history/{log_id}` (строка 125) `[VERIFIED: app/pages/history.py]`.
**Warning signs:** тест на экспорт получает 422 вместо CSV.

### Pitfall 13: Инвентаризационные тесты краснеют от новой разметки

**What goes wrong:** план сделан, код работает, суита красная в местах, не связанных с фазой.
**Why it happens:** Фазы 1–3 закрепили состав разметки счётными утверждениями. Все значения проверены в этой сессии:

| Тест | Файл:строка | Текущее значение | Что его сдвинет |
|------|-------------|------------------|-----------------|
| `test_modal_site_inventory` | `tests/test_templates/test_components.py:799-801`, `:1107` | `MODAL_IMPORTERS = 8`, `MODAL_EVENT_NAMES = 5`, `MODAL_PLACES = 14` | Панель подтверждения повтора (D-23) |
| `test_template_inventory` | `tests/test_pages/test_responsive_markup.py:1880-1881` | `len(components) == 13` | Новый файл в `templates/components/` |
| `test_template_inventory` | там же, `:1873-1878` | элементов таблицы — ноль | `<table>` в heatmap |
| `test_every_page_template_extends_a_shell` | `:1888-1914` | шаблон раздела обязан `{% extends %}` | Новый паршал без слова `partial` в имени |
| `test_only_known_non_dialog_submit_handlers_remain` | `test_components.py:666, :884` | `KNOWN_SUBMIT_HANDLER_FILES = {"accounts/connect_max.html"}` | Второй встроенный `x-on:submit` |
| `test_no_utility_classes_anywhere` / `..._in_python_handlers` | `test_responsive_markup.py:1649, :1668` | ноль utility-классов | Классы вида `mt-2`, `flex-1` в шаблонах **и в Python** |
| `test_no_rendered_page_calls_browser_dialog` | `:2927` | ноль `confirm()`/`alert()` | Браузерный диалог у повтора |

**How to avoid:** каждый план, трогающий разметку, обновляет соответствующую константу **в том же плане**.

---

## Runtime State Inventory

Фаза не является переименованием/рефакторингом/миграцией имён, но она **добавляет схемное изменение и новый путь в боевую очередь**, поэтому категории заполнены явно.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `send_logs` — единственная таблица, к которой добавляется индекс (D-36). Данные не переписываются, колонки не добавляются (D-22). | Только `create_index` в ревизии 0016 |
| Live service config | Redis-очереди `wa:queue:{account_id}`, `max:queue:{account_id}`, множества `wa:active_accounts` / `max:active_accounts`, ключи `wa:endpoint:{id}` / `max:endpoint:{id}` `[VERIFIED: app/worker/tasks.py:80,108,120,147,453,459,494]` — повтор WA/MAX кладёт задачу в те же очереди тем же форматом. Новых ключей не вводится. | Ничего; менять формат полезной нагрузки нельзя — его читают `wa_worker/` и max-worker |
| OS-registered state | Ничего — проверено: фаза не регистрирует задач ОС, не трогает `beat_schedule` (`app/worker/celery_app.py:29-54`), новых периодических задач не вводит (D-04, D-37) | None |
| Secrets/env vars | Ничего — новых переменных окружения фаза не требует. Параметр частоты опроса (D-07) и потолок экспорта (D-27) — константы модуля, не настройки | None |
| Build artifacts | Ничего — build-шага в проекте нет (Фаза 1 D-02); `asset_version` пересчитывается от `mtime` файла `app/static/css/app.css` при импорте `app/pages/common.py:76-88`, то есть правка CSS автоматически ломает кеш браузера | None |

**Отдельно — состояние выката миграций** (⚠️ блокер из STATE.md):

| Ревизия | Файл | Накачена на целевую БД? |
|---------|------|-------------------------|
| 0012 | `0012_schedules_account_id_nullable_set_null.py` | да (текущее состояние прода) |
| 0013 | `0013_ad_status.py` | **нет** |
| 0014 | `0014_sync_result_and_group_missing.py` | нет |
| 0015 | `0015_groups_unique_account_external.py` | нет |
| 0016 (новая, D-36) | — | нет |

`[VERIFIED: uv run alembic heads` → `0015 (head)`; `ls alembic/versions/`; `.planning/STATE.md:86]`

Следствия для планировщика:
1. Новая ревизия обязана быть `revision = "0016"`, `down_revision = "0015"`.
2. **Запросы фазы обязаны быть корректны без индекса.** Индекс — оптимизация, не предусловие; пока 0013–0016 не выкачены, дашборд и история работают на существующих одиночных индексах `user_id` и `sent_at` `[VERIFIED: app/models/send_log.py:13,30]`.
3. `alembic upgrade head` на боевой базе прогонит **четыре** ревизии, одна из которых (0015) удаляет строки и берёт `ACCESS EXCLUSIVE` на `groups`. Это решение владельца, а не Фазы 4 — план не должен его принимать за пользователя.
4. `send_logs` — самая растущая таблица системы (строка на каждую отправку), поэтому `CREATE INDEX` на PostgreSQL возьмёт `SHARE`-блокировку, блокирующую запись. Тот же размен разобран в `alembic/versions/0015_...py:44-55` вместе с готовым следующим шагом (`CREATE INDEX CONCURRENTLY` в ревизии без транзакции). Ревизия 0016 обязана назвать этот размен в докстринге.

---

## Code Examples

### Строка ленты: паршал с бессрочным опросом (D-06, D-07, D-08)

```jinja
{# app/templates/dashboard.html — стабильный контейнер несёт опрос #}
<div id="dash-feed"
     hx-get="/dashboard/feed"
     hx-trigger="every 20s">
  {% include "dashboard/partial_feed.html" %}
</div>
```

```jinja
{# app/templates/dashboard/partial_feed.html — ТОЛЬКО строки, без атрибутов опроса #}
{% from "dashboard/includes/feed_row.html" import feed_row %}
{% if rows %}
  {% for row in rows %}{{ feed_row(row, user) }}{% endfor %}
{% else %}
  {{ empty_state('Отправок пока нет', hint='Здесь появятся события ваших рассылок') }}
{% endif %}
```

```jinja
{# app/templates/dashboard/includes/feed_row.html — макет строки 436–442 #}
{% macro feed_row(row, user=None) -%}
<a data-feedrow href="/history/{{ row.id }}" data-status="{{ row.status }}">
  <span data-dot></span>
  <span data-grow>{{ row.ad_title }} → {{ row.group_name }}</span>
  {{ mono(time_ago_for_user(row.sent_at, user), 'muted') }}
</a>
{%- endmacro %}
```

Три свойства: строка кликабельна и ведёт в запись истории (D-08) обычной ссылкой — без JS; `time_ago_for_user` — существующий глобал; атрибуты опроса живут на контейнере и подмену переживают.

**Проверка htmx-семантики:** «To make an element poll a URL at regular intervals, use the `every` syntax with the `hx-trigger` attribute… Polling can be stopped from a server response by returning the HTTP response code 286.» `[CITED: github.com/bigskysoftware/htmx — www/content/docs.md]`

### Постановка повтора: Celery-таск на все три канала (HIST-04)

```python
# app/worker/tasks.py
@shared_task(name="app.worker.tasks.retry_send", bind=True, max_retries=0)
def retry_send(self, log_id: int, user_id: int):
    """Повтор неуспешной отправки. ВТОРОГО пути отправки не создаёт:
    собирает DispatchTask и отдаёт его той же dispatch_send_tasks,
    которой пользуется планировщик."""
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async def _run():
        try:
            async with session_factory() as session:
                log = await session.get(SendLog, log_id)
                if not log or log.user_id != user_id:
                    logger.warning("retry_send_rejected", log_id=log_id)
                    return
                group = await session.get(Group, log.group_id) if log.group_id else None
                ad = await session.get(Ad, log.ad_id) if log.ad_id else None
                account = (
                    await session.get(MessengerAccount, group.account_id) if group else None
                )
                if not ad or not group or not account or account.status != "active":
                    logger.warning("retry_send_stale", log_id=log_id)
                    return
                task = build_dispatch_task(          # ОБЩИЙ хелпер с collect_due_schedules
                    ad=ad, group=group, account=account,
                    schedule_id=log.schedule_id or 0, settings=settings,
                )
            await dispatch_send_tasks([task])        # tg → Celery, wa/max → Redis
        finally:
            await engine.dispose()

    asyncio.run(_run())
```

Форма таска (собственный engine, `asyncio.run`, `finally: await engine.dispose()`) скопирована с `check_schedules` `[VERIFIED: app/worker/tasks.py:243-265]` — иначе воркер утечёт соединениями.

### Тест страничного маршрута, который ставит задачу в Celery

```python
# Установленный образец — tests/test_routes/test_wa_sync_status.py:193-194 [VERIFIED]
with patch.dict(sys.modules, {"app.worker.celery_app": MagicMock()}):
    resp = await client.post(f"/history/{log_id}/retry")
```

Работает именно потому, что импорт `celery` в обработчике **локальный** (`app/pages/accounts.py:736`). Если исполнитель поднимет импорт наверх модуля, подмена перестанет работать и тест будет пытаться достучаться до Redis.

### Ревизия 0016 (D-36)

```python
"""Составной индекс (user_id, sent_at) на send_logs

Все запросы дашборда и истории — это «мои записи в окне времени»
(app/application/analytics/send_analytics.py). Одиночные индексы
ix_send_logs_user_id и ix_send_logs_sent_at существуют по отдельности
(app/models/send_log.py:13,30) и заставляют планировщик выбирать один
из двух, отбрасывая половину селективности.

РАЗМЕН ПО БЛОКИРОВКАМ. На PostgreSQL CREATE INDEX берёт SHARE-блокировку,
блокирующую запись в send_logs на время построения, а send_logs —
самая растущая таблица системы. Тот же размен разобран в ревизии 0015.
Альтернатива — CREATE INDEX CONCURRENTLY в ревизии без транзакции —
остаётся готовым следующим шагом, если окно станет заметным.

Revision ID: 0016
Revises: 0015
"""
from alembic import op

revision = "0016"
down_revision = "0015"

INDEX_NAME = "ix_send_logs_user_id_sent_at"


def upgrade():
    op.create_index(INDEX_NAME, "send_logs", ["user_id", "sent_at"])


def downgrade():
    op.drop_index(INDEX_NAME, table_name="send_logs")
```

Имя индекса следует конвенции SQLAlchemy `ix_<table>_<col>`, которую проверяет существующий тест `test_upgrade_creates_status_index` для `ix_ads_status` `[VERIFIED: tests/test_migrations/test_0013_ad_status.py:136-149]`.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Дашборд = счётчики сущностей + «Последние отправки» | Метрики отправок с дельтой + heatmap + живая лента + ближайшие отправки | Эта фаза (D-01…D-16) | `stats` в `app/pages/dashboard.py:65-70` заменяется целиком |
| Зависимости с `yield` закрываются **до** отправки ответа (FastAPI 0.106–0.127) | Закрываются **после** (`request_astack`); появилось `scope="function"` для старого поведения | FastAPI ≥0.128 | Потоковый экспорт из `Depends(get_db)` стал корректным. Пин `fastapi>=0.129.0` — несущий |
| `Result.stream_results` / ручные курсоры | `execution_options(yield_per=N)` = `stream_results` + `Result.yield_per()`, задаёт и размер партиции | SQLAlchemy 1.4.x → 2.0 | Один флаг вместо трёх; работает и на aiosqlite, и на asyncpg |
| `hx-swap="outerHTML"` с условными атрибутами как единственный вид опроса в проекте | Добавляется бессрочный опрос на стабильном контейнере | Эта фаза (D-07) | Механизм остановки (исчезновение атрибутов) здесь не применяется намеренно |
| Глобальный раздел «Группы» с собственной статистикой отправок | Группы живут на экране аккаунта; статистика отложена «до Фазы 4» | Фаза 3 (D-01) | Модуль аналитики делает её дешёвой, но в границу фазы она не входит |

**Deprecated/outdated:**
- `SendLogRepository.get_stats(user_id, days=30)` (`app/repositories/send_log.py:14-29`) — считает `total/success/fail` за 30 дней, знает только два статуса из трёх (`account_disconnected` теряется). Единственный потребитель — JSON-маршрут `GET /api/history/stats` (`app/routes/history.py:34-41`). Его судьба — Claude's Discretion; рекомендация: снести вместе с `GET /api/history` по образцу Фазы 3 D-14 (JSON-маршруты групп), предварительно проверив `wa_worker/`, `wa_bridge/` и `scripts/` на потребителей.
- htmx 1.9.10 — обновление до 2.x отложено с Фазы 1 «отдельной задачей после v2.0» (`02-CONTEXT.md:161`). Фаза 4 остаётся на 1.9.10.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Excel в русской локали требует `;` как разделитель, иначе CSV с BOM открывается одной колонкой | §Pattern 7, Open Question 2 | Пользователь получает файл, который «не открывается нормально» — прямое невыполнение духа D-25. Проверяется только вручную на реальном Excel |
| A2 | Частота опроса 20 с и 8 строк ленты — разумная точка внутри вилок D-07/D-08 | §Pattern 3 | Слишком часто — лишняя нагрузка (усилено Pitfall 4); слишком редко — «real-time» перестаёт быть правдой |
| A3 | Потолок экспорта 50 000 строк не мешает реальным пользователям | §Pattern 7 | Активный пользователь упирается в потолок на «всё время» — но D-27 явно требует предупреждения вместо тихой обрезки, так что отказ будет виден |
| A4 | Целевая PostgreSQL-база выдержит `CREATE INDEX` на `send_logs` без заметного окна недоступности записи | §Runtime State Inventory | Если таблица велика — окно блокировки записи в бою. Реального размера `send_logs` в этой сессии измерить нельзя (боевой БД нет) |
| A5 | Ни один внешний потребитель не зависит от `GET /api/history` и `GET /api/history/stats` | §State of the Art | Снос сломает неизвестного клиента. Требует grep-а по `wa_worker/`, `wa_bridge/`, `scripts/`, `monitoring/` перед решением |
| A6 | `schedule_id=0` — приемлемая подстановка при `SendLog.schedule_id is None` для повтора | §Pattern 8 | В журнале появится `schedule_id=0`, которого нет ни в одном расписании. Альтернатива — сделать поле `DispatchTask.schedule_id` опциональным, что трогает планировщик |
| A7 | Внутрипроцессная заявка (`_claim_sync_slot`-подобная) достаточна против двойного повтора | §Pitfall 11 | При нескольких uvicorn-воркерах гонка остаётся. Ограничение уже принято проектом для синхронизации (Фаза 3), но там цена ошибки — лишний синк, а здесь — необратимая отправка в чужую группу |

---

## Open Questions

1. **`[data-longtext]` документирован как «ни усечения, ни многоточия, ни скрытия за раскрытием» — а D-32 требует «длинный обрезается по высоте с раскрытием».**
   - Что известно: комментарий CSS дословен (`app/static/css/app.css:1003-1006`), примитив используется в `history_card.html:54` и на странице записи, а его свойство закреплено тестами `test_history_detail_shows_error_text` (`:587`) и `test_admin_history_escapes_error_text` (`:1512`).
   - Что неясно: правится ли сам примитив или заводится соседний.
   - Рекомендация: **не трогать `[data-longtext]`**, а добавить модификатор (напр. `data-longtext="mono" data-clamp`) только для карточки списка. Страница записи (D-24) и админская история сохраняют полный текст без раскрытия — иначе гарантия «единственное, по чему пользователь понимает, почему его реклама не ушла» теряется в двух местах ради одного.

2. **Разделитель CSV: `,` (RFC 4182) или `;` (русский Excel)?**
   - Что известно: BOM решает кодировку, но не разделитель; D-25 обосновывает BOM именно «Excel открывает кириллицу кракозябрами».
   - Что неясно: чем пользователи открывают файл — Excel, Google Sheets (понимает оба), 1С, скриптами.
   - Рекомендация: `;` — он выполняет намерение D-25 целиком. Решение стоит подтвердить у владельца, потому что оно видимо пользователю.

3. **Второй запрос в блоке «Ближайшие отправки» (флаги групп) — приемлемое отступление от D-38?**
   - Что известно: одним запросом это не считается в принципе (§Pitfall 6), и без него третья причина D-15 нереализуема.
   - Рекомендация: принять как названное отступление и выписать его в плане; запрос ограничен группами ≤8 показываемых строк.

4. **Куда включить маршрут паршала ленты — в `pages_router` (с `load_shell_context`) или мимо него?**
   - Что известно: цена — ~4 лишних запроса на каждый тик каждой вкладки (§Pitfall 4).
   - Рекомендация: мимо, отдельным роутером в `app/main.py`. Требует проверки, что паршал действительно не читает `request.state.shell`.

5. **Судьба `app/routes/history.py` (`GET /stats`, `GET ""`) — выровнять или снести?**
   - Что известно: `get_stats` знает два статуса из трёх и жёстко берёт 30 дней; прецедент сноса мёртвых JSON-маршрутов есть (Фаза 3 D-14, `app/routes/groups.py` целиком).
   - Рекомендация: снести после grep-а по потребителям (A5). Если оставлять — переключить на модуль аналитики, иначе в проекте будет два разных ответа на вопрос «сколько было ошибок».

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `uv` | Все команды проекта | ✓ | 0.12.1 | — |
| `just` | Рецепты `test`, `migrate`, `upgrade` | ✓ | 1.45.0 | Прямые `uv run` |
| Python 3.12 (в `.venv`) | Приложение | ✓ | 3.12.13 | — |
| `alembic` (через `uv run`) | Ревизия 0016 (D-36) | ✓ | 1.18.4, head `0015` | — |
| pytest + pytest-asyncio | Вся верификация | ✓ | pytest 9.0.2, pytest-asyncio ≥1.3.0 | — |
| SQLite (`aiosqlite`) | Тестовая суита | ✓ | in-memory, схема через `Base.metadata.create_all` | — |
| Node.js | `design/unpack.js` (пересборка распакованного макета) | ✓ | v22.22.1 | Распакованная копия уже есть в репозитории |
| Docker (клиент) | `just dev` / `just prod-*` | ✓ (клиент 29.7.1) | демон в этой среде не проверялся | Локальный запуск `just run` |
| PostgreSQL (`psql`) | Боевой прогон агрегаций и ревизии 0016 | ✗ | — | **Fallback отсутствует.** Проверка переносимости SQL достигается тем, что диалект-специфичных выражений не пишется вовсе (§Pitfall 2) |
| Redis (`redis-cli`) | Celery-брокер для HIST-04 | ✗ | — | В тестах Celery подменяется `patch.dict(sys.modules, {"app.worker.celery_app": MagicMock()})` — установленный образец `tests/test_routes/test_wa_sync_status.py:193` |
| Браузер / e2e-раннер | Рантайм Alpine (панель повтора, кнопка копирования), рантайм htmx (опрос) | ✗ | — | **Fallback отсутствует.** Ручная проверка — блокер уровня проекта (STATE.md:88) |

**Missing dependencies with no fallback:**
- **PostgreSQL** — переносимость агрегаций доказывается конструктивно (не писать диалектный SQL), а не прогоном. Это ужесточает §Pitfall 2 из рекомендации в требование.
- **Браузерных/e2e-тестов нет.** Три новых рантайм-поведения фазы (бессрочный опрос, гард повторной отправки в панели, кнопка копирования) автотестами не проверяются. Компенсация — разметочные тесты (атрибуты присутствуют / отсутствуют) плюс явные пункты UAT.

**Missing dependencies with fallback:**
- **Redis** — подмена модуля Celery в тестах, установленный образец есть.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio ≥1.3.0 (strict mode: конфигурационного файла нет, каждый async-тест помечен `@pytest.mark.asyncio`) |
| Config file | none — ни `pytest.ini`, ни `[tool.pytest.ini_options]` в `pyproject.toml`; фикстуры в `tests/conftest.py` |
| Quick run command | `uv run pytest tests/test_pages/ tests/test_application/ -q` |
| Full suite command | `just test` (= `uv run pytest tests/ -v`) |
| Baseline | **1094 теста собирается** (`uv run pytest tests/ -q --collect-only`, эта сессия) |
| DB | `sqlite+aiosqlite:///:memory:`, полная схема на тест (`conftest.py:38-40`) |
| Fixtures | `client`, `authed_client`, `admin_client`, `db_session`, `auth_headers`, `test_settings`, `seed_group` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DASH-01 | Четыре плитки считают отправки за скользящие 24 ч; `account_disconnected` попадает в «Ошибок»; дельта считается к предыдущим суткам | unit | `uv run pytest tests/test_application/test_send_analytics.py -x` | ❌ Wave 0 |
| DASH-01 | Плитка «Групп охвачено» не считает записи с `group_id IS NULL` дважды и не падает на них | unit | `uv run pytest tests/test_application/test_send_analytics.py -k groups -x` | ❌ Wave 0 |
| DASH-01 | Дашборд рендерит четыре новые плитки и **не** рендерит старые счётчики сущностей | integration | `uv run pytest tests/test_pages/test_dashboard.py -k metrics -x` | ❌ Wave 0 |
| DASH-02 | Ближайшие отправки отсортированы по `next_run_at`, не поднимают `lazy="raise"`, показывают причину для черновика / отвязанного аккаунта / выключенных групп | integration | `uv run pytest tests/test_pages/test_dashboard.py -k upcoming -x` | ❌ Wave 0 |
| DASH-03 | Страница несёт `hx-get` + `hx-trigger="every ...s"`; паршал отдаёт строки; **опрос не самоостанавливается** (парный тест) | integration | `uv run pytest tests/test_pages/test_htmx_preserved.py -k feed -x` | ⚠️ файл есть, тестов ленты нет |
| DASH-03 | Строка ленты — ссылка на `/history/{id}` (работает без JS) | integration | `uv run pytest tests/test_pages/test_dashboard.py -k feed_row -x` | ❌ Wave 0 |
| DASH-04 | Heatmap раскладывает отправки по локальному часу пользователя (UTC+3 vs UTC даёт разные ячейки); работает на naive-датах SQLite | unit | `uv run pytest tests/test_application/test_send_analytics.py -k heatmap -x` | ❌ Wave 0 |
| DASH-04 | Сетка 7×24 отрисована без элементов таблицы и без utility-классов | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -k heatmap -x` | ⚠️ файл есть |
| DASH-05 | Дашборд показывает `sessions_online` из `get_shell_context`; в пути рендера дашборда нет обращения к Docker | integration | `uv run pytest tests/test_pages/test_shell.py -k sessions -x` | ⚠️ файл есть |
| HIST-01 | Чипсы статуса/канала/периода меняют выборку; `today` считается от локальной полуночи; фильтры переживают пагинацию | integration | `uv run pytest tests/test_pages/test_history.py -k filters -x` | ❌ Wave 0 |
| HIST-01 | Существующая гарантия не сломана переносом фильтров в модуль аналитики | regression | `uv run pytest tests/test_pages/test_htmx_preserved.py::test_infinite_scroll_keeps_filters -x` | ✅ |
| HIST-02 | Текст ошибки виден в карточке списка целиком и экранирован | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -k error_text -x` | ✅ (расширить) |
| HIST-02 | Кнопка копирования не рендерится без Alpine и не ломает страницу | integration | `uv run pytest tests/test_pages/test_history.py -k copy_degrades -x` | ❌ Wave 0 |
| HIST-03 | Экспорт отдаёт CSV с BOM, теми же фильтрами, что список, и тем же числом строк, что счётчик D-31 | integration | `uv run pytest tests/test_pages/test_history_export.py -x` | ❌ Wave 0 |
| HIST-03 | `GET /history/export` не перехватывается `GET /history/{log_id}` | integration | `uv run pytest tests/test_pages/test_history_export.py -k route_order -x` | ❌ Wave 0 |
| HIST-03 | Превышение потолка даёт объяснение, а не обрезанный файл | integration | `uv run pytest tests/test_pages/test_history_export.py -k cap -x` | ❌ Wave 0 |
| HIST-03 | Поле, начинающееся с `=`/`+`/`-`/`@`, экранировано (formula injection) | unit | `uv run pytest tests/test_pages/test_history_export.py -k formula -x` | ❌ Wave 0 |
| HIST-04 | Кнопка повтора не рендерится у `ok`; POST по `ok`-записи отклоняется сервером | integration | `uv run pytest tests/test_pages/test_history_retry.py -k eligible -x` | ❌ Wave 0 |
| HIST-04 | Повтор чужой записи отклоняется (владение на входе) | integration | `uv run pytest tests/test_pages/test_history_retry.py -k ownership -x` | ❌ Wave 0 |
| HIST-04 | При отсутствии ad/group/account задача **не** ставится в очередь и запись в журнал не пишется (D-21) | integration | `uv run pytest tests/test_pages/test_history_retry.py -k precheck -x` | ❌ Wave 0 |
| HIST-04 | Повтор WA-записи маршрутизируется в Redis-очередь, а не в Celery-очередь `telegram` | unit | `uv run pytest tests/test_worker_tasks.py -k retry -x` | ⚠️ файл есть |
| HIST-04 | Исчерпанный баланс отклоняет повтор до очереди | integration | `uv run pytest tests/test_pages/test_history_retry.py -k balance -x` | ❌ Wave 0 |
| D-36 | Ревизия 0016 создаёт индекс, downgrade его снимает, история остаётся одной линией | unit | `uv run pytest tests/test_migrations/test_0016_send_logs_user_sent_at.py -x` | ❌ Wave 0 |
| Сквозное | Инвентаризации (модалки, компоненты, utility-классы) сходятся после правок | regression | `uv run pytest tests/test_templates/test_components.py tests/test_pages/test_responsive_markup.py -q` | ✅ (обновить константы) |
| Сквозное | Адаптивность: дашборд и история без utility-классов, без таблиц, наследуют шелл | regression | `uv run pytest tests/test_pages/test_responsive_markup.py -q` | ✅ |
| **Не автоматизируется** | Опрос действительно тикает бессрочно в открытой вкладке | manual UAT | — | браузерных тестов нет (STATE.md:88) |
| **Не автоматизируется** | Панель подтверждения повтора не даёт отправить дважды при живом Alpine | manual UAT | — | там же |
| **Не автоматизируется** | CSV открывается в Excel без кракозябр и одной колонкой | manual UAT | — | Excel в среде нет |
| **Не автоматизируется** | Сессия БД переживает поток экспорта на боевом стеке | manual | — | `conftest.py:54` подменяет `get_db` не генератором |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_application/ tests/test_pages/test_dashboard.py tests/test_pages/test_history.py -q` (< 30 с)
- **Per wave merge:** `uv run pytest tests/test_pages/ tests/test_templates/ tests/test_application/ tests/test_migrations/ -q`
- **Phase gate:** `just test` зелёный целиком (baseline 1094 + новые) до `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_application/test_send_analytics.py` — покрывает DASH-01, DASH-04 (окна, три статуса, таймзона, naive-даты)
- [ ] `tests/test_pages/test_dashboard.py` — покрывает DASH-01, DASH-02, DASH-03 (страница целиком; сейчас у дашборда нет собственного файла тестов)
- [ ] `tests/test_pages/test_history.py` — покрывает HIST-01, HIST-02 (сейчас тесты истории размазаны по `test_responsive_markup.py` и `test_htmx_preserved.py`)
- [ ] `tests/test_pages/test_history_export.py` — покрывает HIST-03 целиком
- [ ] `tests/test_pages/test_history_retry.py` — покрывает HIST-04 целиком
- [ ] `tests/test_migrations/test_0016_send_logs_user_sent_at.py` — покрывает D-36; каркас копируется с `tests/test_migrations/test_0013_ad_status.py` (файловая SQLite, синхронный тест, штамп стартовой ревизии)
- [ ] Расширение `tests/test_pages/test_htmx_preserved.py` — **парные** тесты бессрочного опроса ленты
- [ ] Обновление констант `MODAL_IMPORTERS` / `MODAL_EVENT_NAMES` / `MODAL_PLACES` (`tests/test_templates/test_components.py:799-801`) и `len(components)` (`tests/test_pages/test_responsive_markup.py:1881`)
- Установка фреймворка не требуется: pytest и pytest-asyncio уже в `pyproject.toml:38-39`.

---

## Security Domain

`workflow.security_enforcement: true`, `security_asvs_level: 1`.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | нет (новых входов аутентификации фаза не вводит) | `get_user_from_cookie` на каждом маршруте — существующий контракт |
| V3 Session Management | нет | JWT в httpOnly cookie, без изменений |
| V4 Access Control | **да** | Владение проверяется на **каждом** входе: `/history/{id}` (`log.user_id != user.id` — уже есть, `app/pages/history.py:137`), новый POST повтора, новый `GET /history/export` (фильтр `SendLog.user_id == user.id` обязателен в базовом запросе экспорта, как в `history.py:83`), паршал ленты |
| V5 Input Validation | **да** | Значения чипсов (`status`, `messenger`, `period`) приходят из query и попадают в `WHERE` — SQLAlchemy параметризует, инъекции нет, но неизвестное значение должно давать «фильтр не применён», а не 500. `account_id` уже проходит через `_parse_account_id` (`history.py:19-25`). `log_id` — типизированный `int` (FastAPI отвергает нечисло 422 до обработчика) |
| V6 Cryptography | нет | Фаза криптографии не касается |
| V7 Error Handling & Logging | **да** | Текст стороннего исключения показывается владельцу — принято как риск (см. ниже) |
| V12 Files & Resources | **да** | CSV-экспорт: имя файла, `Content-Disposition`, formula injection |
| V13 API & Web Service | **да** | Порядок маршрутов, отсутствие CSRF-защиты у POST повтора |

### Known Threat Patterns for FastAPI + Jinja2 + Celery/Redis + CSV

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| **CSV formula injection** — поля `ad_title`, `group_name`, `error_message` попадают в файл; значения приходят от пользователя и от стороннего мессенджера. Поле, начинающееся с `=`, `+`, `-`, `@`, `\t`, `\r`, интерпретируется Excel/LibreOffice как формула и может дать выполнение (DDE) на машине получателя | Tampering / Elevation | Префиксовать `'` перед такими полями (или начинать значение с пробела). **Это новая для проекта угроза** — экспорта до сих пор не существовало. Обязательна к реализации и к именованному тесту |
| **Раскрытие текста стороннего исключения** — `SendLog.error_message` хранит сырой ответ мессенджера и может содержать внутренние адреса, идентификаторы сессий, фрагменты запроса. D-32/D-33 показывают его всегда и кладут в буфер | Information Disclosure | Тот же класс, что R-03-09 (`.planning/phases/03-gruppy-akkaunta/03-SECURITY.md`), принятый владельцем как severity **medium**. Текст виден **только владельцу записи** (V4 держит границу). Осознанное принятие; в отчёте фазы риск надо переоформить явно, а не унаследовать молча |
| **XSS через данные мессенджера** — имя группы и текст ошибки приходят извне | Tampering | Jinja2 автоэкранирует; закреплено `test_admin_history_escapes_error_text` (`:1512`) и `test_admin_groups_info_escapes_external_name` (`:1269`). Новые макросы обязаны выводить значения обычным `{{ }}`, без `|safe` |
| **CSRF на POST повтора** — действие необратимо (отправка в чужую группу), а аутентификация идёт cookie; CSRF-токенов в проекте нет ни у одной формы | Spoofing | Существующее состояние проекта (13 мест удаления через POST-формы без токена). Фаза не имеет права ухудшить его, но и не обязана чинить в одиночку. **Назвать явно в SECURITY фазы**: цена ошибки здесь выше, чем у удаления — удаление обратимо документально, отправка нет |
| **Отсутствие серверной идемпотентности повтора** — двойной POST даёт две необратимые отправки | Repudiation / Tampering | PRG + внутрипроцессная заявка по образцу `_claim_sync_slot`; см. §Pitfall 11 |
| **Обход тарифного лимита через повтор** — гейт `check_balance_cached` стоит только в планировщике | Elevation of Privilege | Вызвать `check_balance_cached(db, user.id, "send")` в предпроверке; см. §Pitfall 10 |
| **DoS дорогим экспортом** — `GET /history/export` без фильтров тянет всю историю | Denial of Service | Потолок D-27, проверяемый **до** начала потока; плюс `yield_per` держит память O(батч), а не O(выборки) |
| **Усиление нагрузки бессрочным опросом** — вкладка, оставленная открытой, тикает вечно | Denial of Service | Осознанное решение D-07. Смягчение — вынести паршал из-под `load_shell_context` (§Pitfall 4) и/или фильтр `every Ns [document.visibilityState==='visible']` (htmx поддерживает фильтр после объявления опроса, но он **требует включённого eval** — проверить, не конфликтует ли с политиками; CSP-заголовков в проекте нет) |
| **Открытый редирект через `return_to`** | Tampering | Фаза новых параметров возврата не вводит; редиректы — на литеральные `/history`, `/dashboard` |

---

## Sources

### Primary (HIGH confidence — прочитано/исполнено в этой сессии)

Исходники приложения:
- `app/pages/dashboard.py` (109 строк), `app/pages/history.py` (227), `app/pages/common.py` (365), `app/pages/__init__.py` (53), `app/pages/accounts.py:700-770`, `app/pages/admin.py:11-12,62`
- `app/models/send_log.py`, `app/models/schedule.py`, `app/models/group.py:1-45`, `app/models/messenger_account.py:1-40`
- `app/application/scheduling/use_cases.py` (374), `app/worker/tasks.py` (759), `app/worker/celery_app.py` (71)
- `app/repositories/send_log.py`, `app/services/billing_service.py:39-63`, `app/services/billing_cache.py:28-55`
- `app/dependencies.py`, `app/constants.py`, `app/main.py:79-86`
- `app/templates/base.html` (129), `dashboard.html` (53), `history/list.html` (57), `history/includes/history_card.html` (66), `components/{modal,filters,empty_state}.html`
- `app/static/css/app.css:1003-1045, 1373-1415`, `app/static/js/{htmx,alpine}.min.js` (только строки версии)
- `alembic/versions/0015_groups_unique_account_external.py` (235), листинг `alembic/versions/`
- `tests/conftest.py` (172), `tests/test_pages/test_responsive_markup.py` (структура + ключевые тесты), `tests/test_pages/test_htmx_preserved.py:232-385`, `tests/test_templates/test_components.py:666,799-801,884-940,1107-1143`, `tests/test_migrations/test_0013_ad_status.py`, `tests/test_routes/test_wa_sync_status.py:168-207`
- `design/new_broadcaster_design.unpacked.html:360-474, 800-884`
- `nginx/nginx.conf.template`, `nginx/nginx-http.conf.template`, `docker-compose.prod.yml:29-42`, `justfile`, `pyproject.toml`

Исходники установленных зависимостей (несущий факт §Pattern 7):
- `.venv/lib/python3.12/site-packages/fastapi/routing.py:92-121`
- `.venv/lib/python3.12/site-packages/fastapi/dependencies/utils.py:565-649`
- `.venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py`

Исполненные проверки:
- версии: `fastapi 0.129.0`, `starlette 0.52.1`, `sqlalchemy 2.0.46`, `jinja2 3.1.6`, `celery 5.6.2`, `alembic 1.18.4`, `pytest 9.0.2`, Python 3.12.13
- `uv run alembic heads` → `0015 (head)`
- `uv run pytest tests/ -q --collect-only` → **1094 tests collected**
- собственный скрипт-зонд по `sqlite+aiosqlite`: naive `sent_at` (`tzinfo=None`), aware-сравнение в `WHERE` работает, `func.sum(case(...))` / `func.count(func.distinct(...))` работают, `session.stream()` работает, `func.strftime` работает (и потому опасен)
- перебор `app.constants.VALID_TIMEZONES` через `zoneinfo` → все 12 зон с фиксированным смещением, DST нет ни у одной

Планирование:
- `.planning/phases/04-dashbord-i-istoriya/04-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/config.json`
- `.planning/phases/02-obyavleniya-i-raspisaniya/02-CONTEXT.md:60,120,125,156`
- `.planning/codebase/CONCERNS.md:56-69`
- `CLAUDE.md`, `.claude/CLAUDE.md`

### Secondary (MEDIUM confidence — официальная документация через Context7)

- `github.com/bigskysoftware/htmx` — `www/content/docs.md`, `www/content/attributes/hx-trigger.md`: синтаксис `every <timing>`, HTTP 286 как остановка опроса, фильтры после объявления опроса, умолчание swap = `innerHTML`
- `docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html` и `/core/connections.html`: `AsyncSession.stream`, `AsyncResult.yield_per`, `Result.partitions`, `execution_options.yield_per` = `stream_results` + server-side cursor

### Tertiary (LOW confidence — веб-поиск, помечено для проверки)

- Clipboard API вне secure context (`navigator.clipboard` = `undefined` по HTTP), фолбэк через `document.execCommand('copy')` — bobbyhadz.com, MDN-производные материалы. Само правило secure-context — платформенный факт; конкретная форма фолбэка требует ручной проверки в браузере
- Поведение Excel в русской локали при разделителе `,` vs `;` — общее знание, в этой сессии не воспроизводилось (A1)

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — новых пакетов нет, все версии подтверждены исполнением интерпретатора и `pyproject.toml`
- Architecture: **HIGH** — все интеграционные точки, сигнатуры, `lazy="raise"`, отсутствие `account_id` у `SendLog`, ветвление `dispatch_send_tasks` и порядок закрытия exit-стека FastAPI прочитаны в исходниках этой сессии
- Pitfalls: **HIGH** для 1–8, 10–13 (каждый подтверждён строкой кода или исполнением); **MEDIUM** для 9 (правило secure-context надёжно, форма фолбэка — веб-источник)
- Validation architecture: **HIGH** — baseline 1094 теста измерен, образцы подмены Celery и файловой миграции прочитаны
- Security: **MEDIUM–HIGH** — угрозы выведены из прочитанного кода; formula injection и обход гейта баланса — новые для проекта и подтверждены отсутствием соответствующего кода

**Research date:** 2026-08-13
**Valid until:** 2026-09-12 (30 дней — стек зафиксирован, внешних быстро движущихся зависимостей фаза не вводит). Пересмотреть раньше, если: изменится минимальная версия FastAPI (ломает §Pattern 7), выкатятся ревизии 0013–0015 на бой (снимает часть §Runtime State Inventory) или появится e2e-инфраструктура (меняет §Validation Architecture).
