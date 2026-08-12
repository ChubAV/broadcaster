# Phase 3: Группы аккаунта - Research

**Researched:** 2026-08-12
**Domain:** Brownfield server-rendered UI (FastAPI + Jinja2 + HTMX/Alpine) + одна правка в диспетчере рассылок + миграция Alembic
**Confidence:** HIGH — все ключевые утверждения проверены чтением исходников в этой сессии; внешних библиотек фаза не добавляет.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Судьба раздела «Группы»

- **D-01:** Глобальный раздел `/groups` сносится целиком: страницы, паршалы, bulk-операции, фильтры и пункт «Группы» в навигации. `/groups` отвечает редиректом на «Аккаунты». Закрывает отложенное решение Фазы 1 (D-11: пункт был оставлен временно именно до этой фазы). — **Reversibility:** costly — снос шаблонов, роутов и их тестов; возврат означает восстановление раздела заново.
- **D-02:** Экран групп аккаунта живёт на `/accounts/{id}/groups`, `active_page=accounts`, вход — с экрана «Аккаунты» (клик по аккаунту).
- **D-03:** Состав экрана — макет плюс строка поиска по имени (у TG-аккаунта могут быть сотни чатов). Фильтры по мессенджеру/активности, статистика отправок по группе и bulk-операции старого раздела не переносятся.
- **D-04:** Длинные списки — бесконечная прокрутка сентинел-паттерном Фазы 1 (по 30 за запрос). Счётчик «N активных из M групп» считается отдельным запросом, а не по загруженной странице.

#### Семантика «отключено»

- **D-05:** Выключенная группа **пропускается при отправке**: диспетчеризация не ставит задачи отправки для групп с `is_active=false`, даже если группа уже входит в расписания. Тумблер обратим — состав расписаний не меняется, включение возобновляет рассылку. — **Reversibility:** costly — условие уходит в боевой пайплайн диспетчеризации, откат означает повторную проверку тестов диспетчеризации.
- **D-06:** Пропуск тихий: записей в `SendLog` не создаётся, след — только structlog. История отражает реальные попытки отправки; новый статус журнала не вводится.
- **D-07:** В карточке расписания в редакторе объявления выключенные группы **видны только если уже выбраны в этом расписании** — с пометкой «отключена» (чекбокс недоступен для новых). Пользователь видит, почему группа из расписания не получает рассылку; список выбора не захламляется.
- **D-08:** Тумблер срабатывает мгновенно, без панели подтверждения — действие полностью обратимо. Показ «в N расписаниях» в подписи группы — на усмотрение исполнителя.

#### Синхронизация и её результат

- **D-09:** Результат синка — сводка-плашка на экране, не покидая его: «найдено N, новых M, обновлено имён K» или текст ошибки. Для WA/MAX (фоновый синк через Celery) статус добирается самоостанавливающимся опросом — паттерн экрана аккаунтов из Фазы 1 (план 01-06). Результат последнего синка хранится на аккаунте и виден при перезаходе.
- **D-10:** Синк — полная переинвентаризация: **ручно удалённые группы возвращаются** при следующем синке (как новые, включённые, без старых связей с расписаниями). Так говорит пустое состояние макета («запустите синхронизацию, чтобы подтянуть чаты заново»). Если группа не нужна — её выключают, а не удаляют. Томбстоуны не вводятся.
- **D-11:** Синк обновляет имена существующих групп. Группы, которые мессенджер больше не вернул, помечаются («не найдена при синке»), но **не удаляются автоматически** — удаление остаётся решением пользователя. `is_active` синком не трогается.
- **D-12:** Миграция схемы: `MessengerAccount` получает `last_synced_at` и результат последнего синка (счётчики/ошибка — точная форма за планировщиком). Шапка «последняя синхронизация N назад» из макета становится честной. **Per-group кнопка синка ↻ из макета НЕ делается** — протокола синхронизации одной группы у воркеров не существует, а протоколы не трогаем (прецедент: Фаза 2 D-17 выкинула выдуманный прогресс-бар макета). Остаётся одна кнопка «Синхронизировать всё».

#### Ручное добавление — отменено

- **D-13:** Ручного добавления групп **не будет**: GRP-08 снято решением владельца (2026-08-11, при обсуждении фазы). CTA «Добавить группу» из макета (строка ~1491) не реализуется. Требуется согласованная правка: ROADMAP.md — цель и критерий 3 фазы (убрать «добавить группу аккаунта вручную»), REQUIREMENTS.md — GRP-08 в Out of Scope с причиной. — **Reversibility:** reversible — решение о невключении; возврат возможен отдельной фазой.
- **D-14:** Вместе с отменой GRP-08 удаляется `POST /api/groups` — единственный вход ручного создания группы: UI-потребителя у него нет, а владение `account_id` он не проверяет (дыра класса CR-01 Фазы 2 закрывается удалением входа). Судьба остальных JSON-маршрутов групп (`GET`, `DELETE`, `PATCH toggle`) — за планировщиком: проверить потребителей и либо оставить с выравниванием поведения, либо снести как мёртвые.

### Claude's Discretion

- Точная форма сводки синка (плашка/тост, состав счётчиков) и форма пометки «не найдена при синке» (бейдж, цвет).
- Подпись строки группы: в макете «N участников», но источника данных в модели нет — заменить имеющимися данными или опустить.
- Показ «в N расписаниях» в подписи группы (D-08).
- Взаимодействие поиска с бесконечной прокруткой (по образцу существующих списочных страниц).
- Мобильная раскладка экрана в пределах брейкпоинтов макета (860/900/1080px); адаптивность — критерий приёмки фазы.
- Судьба `GET/DELETE/PATCH /api/groups` (см. D-14).
- Куда именно встраивается пропуск выключенных групп: выборка при диспетчеризации или фильтр при постановке задач — что даст более простой и тестируемый срез.

### Deferred Ideas (OUT OF SCOPE)

- **Статистика отправок по группе** (попытки/успехи/последняя отправка со старого /groups) — уходит вместе с разделом; возвращать имеет смысл после Фазы 4, где появляются агрегации по `SendLog`.
- **Bulk-операции над группами** (массовое отключение/удаление) — не переносятся; при реальной потребности — отдельная задача.
- **Синк одной группы** — требует расширения протоколов воркеров; вне v2.0.
- **Ручное добавление группы (GRP-08)** — отменено владельцем, не отложено: снять с roadmap (D-13). Если потребность вернётся — отдельная фаза с собственным обсуждением форматов ID и валидации.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GRP-04 | Пользователь может открыть экран групп конкретного messenger-аккаунта | Новая страница `/accounts/{id}/groups` — точный образец: `groups_list`/`groups_partial` из `app/pages/groups.py` (сентинел-прокрутка, поиск, проверка владельца); шелл-паттерны Фазы 1; вход — клик по аккаунту в `accounts/list.html`; макет строки — design unpacked ~906–964 |
| GRP-05 | Пользователь может включать и отключать отдельные группы аккаунта | Переиспользование `groups_toggle` (POST-форма + макрос `toggle`, паттерн 01-04); эффект D-05 — фильтр в `collect_due_schedules` (per-group цикл, строка 120); пометка в редакторе — `app/pages/ads.py:216-226` + `sched_card.html:63,151-158` |
| GRP-06 | Пользователь может удалить группу из списка аккаунта | Переиспользование `groups_delete` (уже вычищает `group_ids` расписаний через `ScheduleRepository.remove_group_ids`, `app/repositories/schedule.py:41-53`); панель подтверждения — паттерн Фазы 1 (модалка вне подменяемого элемента) |
| GRP-07 | Пользователь может повторно синхронизировать группы аккаунта и увидеть результат синхронизации | Существующий вход `POST /accounts/{id}/sync-groups` (`app/pages/accounts.py:737-804`); фоновые `sync_wa_groups`/`sync_max_groups` (`app/worker/tasks.py:250-451`); самоостанавливающийся опрос — `sync_status_card.html`; миграция 0014 для `last_synced_at` + результата (D-12) |
| GRP-08 | ~~Ручное добавление группы~~ — **снято D-13** | Правка ROADMAP.md (критерий 3, заголовок фазы в списке, Goal) + REQUIREMENTS.md (GRP-08 → Out of Scope + traceability); удаление `POST /api/groups` (D-14) и каскад по ~9 файлам тестов, сеющим группы через него |
</phase_requirements>

## Summary

Фаза почти целиком внутрикодовая: ни одной новой зависимости, ни одного нового внешнего сервиса. Всё, что нужно построить, уже имеет проверенный прецедент в этом репозитории: список с бесконечной прокруткой и поиском (Фаза 1, `groups`/`accounts`), самоостанавливающийся HTMX-опрос статуса синка (план 01-06, `sync_status_card.html`), тумблер в POST-форме (план 01-04), новое условие в боевом диспетчере (Фаза 2 D-01 — пропуск черновиков, с развёрнутым комментарием прямо в `collect_due_schedules`). Основная работа — новый экран `/accounts/{id}/groups`, снос глобального `/groups`, доработка WA/MAX-синка с «only-add» до «переинвентаризация с результатом», миграция `0014` и пропуск `is_active=false` при диспетчеризации.

Три открытия, которые изменят оценку объёма планировщиком. Первое: `POST /api/groups` (удаляемый по D-14) — это seeding-хелпер как минимум девяти файлов тестов (`test_e2e`, `test_schedules*`, `test_limits`, `test_history`, `test_account_deletion_schedules`, `test_groups` и др.) — его удаление тянет за собой переделку посева групп в тестах (фикстура/ORM-вставка). Тарифного лимита на группы при этом не существует (тест `test_create_groups_no_limit` прямо документирует его отсутствие) — с удалением входа ничего не теряется. Второе: пометка «не найдена при синке» (D-11) требует места хранения — в `Group` его нет (есть только `last_error`/`error_at` — это ошибки отправки), значит миграция 0014 затрагивает и `groups`, а не только `messenger_accounts`. Третье: счётчика у пункта «Группы» в навигации нет (`count_key: None` в `NAV_ITEMS`) — «удаление счётчика» из CONTEXT.md сводится к удалению одной строки списка.

**Primary recommendation:** строить экран копированием живых паттернов Фазы 1 (не с макета «в лоб»), пропуск D-05 ставить в per-group цикл `collect_due_schedules` (строка 120) по образцу и с тем же стилем комментария, что D-01, а миграцию 0014 проектировать сразу на обе таблицы: `messenger_accounts.last_synced_at` + результат синка и маркер «не найдена» на `groups`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Экран групп аккаунта (GRP-04) | Frontend Server (Jinja2 pages, `app/pages/`) | — | Серверный рендеринг — зафиксировано PROJECT.md; SPA вне скоупа |
| Toggle/Delete группы (GRP-05/06) | Frontend Server (POST-формы) | Database (UPDATE/DELETE + чистка `group_ids`) | Базовый путь без JS — правило Фазы 2 D-09; HTMX/Alpine — прогрессивное улучшение |
| Пропуск выключенных при рассылке (D-05) | Backend worker (`app/application/scheduling/`) | — | Диспетчеризация живёт в use case `collect_due_schedules`; воркеры/протоколы не трогаются |
| Синк TG (синхронный) | Frontend Server (обработчик `sync-groups`) | Messenger adapter (Telethon, не меняется) | TG-синк уже выполняется в обработчике страницы через `get_dialogs` |
| Синк WA/MAX (фоновый) | Backend worker (Celery `sync_wa_groups`/`sync_max_groups`) | Frontend Server (опрос статуса) | Celery-таска пишет в БД; экран добирает статус самоостанавливающимся опросом |
| Результат синка (D-09/D-12) | Database (`messenger_accounts` + `groups`) | Frontend Server (плашка) | Результат «виден при перезаходе» ⇒ персистентен, не in-memory |
| Пометка «отключена» в редакторе (D-07) | Frontend Server (`app/pages/ads.py` + `sched_card.html`) | — | Выборка групп для редактора и разметка карточки — серверные |
| Правки ROADMAP/REQUIREMENTS (D-13) | Docs (`.planning/`) | — | Согласованная правка двух документов + traceability |

## Standard Stack

### Core (существующий, ничего не добавляется)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI + Jinja2 | in repo | страницы и паршалы | весь UI проекта; PROJECT.md фиксирует стек [VERIFIED: pyproject/CLAUDE.md] |
| SQLAlchemy async + Alembic | in repo | модель + миграция 0014 | все 13 ревизий в `alembic/versions/`, head = `0013_ad_status.py` [VERIFIED: ls alembic/versions] |
| htmx + Alpine (вендорены) | in repo | опрос синка, прокрутка, панели | Фаза 1: внешних ресурсов 0, build-шага нет [CITED: 01-04/01-06 SUMMARY] |
| Celery + Redis | in repo | фоновый синк WA/MAX | существующие таски `sync_wa_groups`/`sync_max_groups` [VERIFIED: app/worker/tasks.py:342-451] |
| structlog | in repo | след тихого пропуска (D-06) | `logger = structlog.get_logger(__name__)` — паттерн tasks.py [VERIFIED: app/worker/tasks.py:29] |
| pytest + aiosqlite | in repo | суита 895 зелёных | conftest: `client`, `db_session`, `auth_headers` [CITED: .planning/codebase/TESTING.md, REQUIREMENTS.md:243] |

### Supporting / Alternatives Considered

Не применимо: фаза не выбирает библиотеки. **Установка пакетов не требуется** — `npm install`/`uv add` в этой фазе быть не должно; появление установки в плане — красный флаг.

## Package Legitimacy Audit

Фаза не устанавливает внешних пакетов. Проверка легитимности не требуется.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
Пользователь
  │ клик по аккаунту на /accounts
  ▼
GET /accounts/{id}/groups  (app/pages/account_groups.py — новый модуль или accounts.py)
  ├─ владение: MessengerAccount.user_id == user.id  (404/redirect иначе)
  ├─ страница: шапка аккаунта + плашка результата последнего синка (из БД, D-09)
  ├─ счётчик «N активных из M» — отдельный COUNT-запрос (D-04)
  └─ список: 30 строк + сентинел ──► GET /accounts/{id}/groups/partial?offset&search
                                        (протаскивает search в сентинел — паттерн 01-04)

Строка группы:
  ├─ POST /accounts/{id}/groups/{gid}/toggle ──► UPDATE is_active ──► redirect назад (D-08: без подтверждения)
  └─ POST /accounts/{id}/groups/{gid}/delete ──► панель подтверждения (вне строки)
        └─► ScheduleRepository.remove_group_ids + DELETE ──► redirect назад

Кнопка «Синхронизировать всё»:
  POST /accounts/{id}/sync-groups (существующий вход, редирект меняется на новый экран)
    ├─ TG: синхронно Telethon get_dialogs ──► переинвентаризация ──► результат в БД ──► redirect (плашка видна сразу)
    └─ WA/MAX: status='syncing' + Celery sync_wa_groups/sync_max_groups
          └─ экран: блок статуса с hx-trigger="every 5s" ТОЛЬКО при status=='syncing'
               (самоостанавливающийся опрос — дословный паттерн sync_status_card.html)
          └─ таска: переинвентаризация ──► last_synced_at + результат в БД ──► status='active'|'sync_failed'

Диспетчер (каждую минуту):
  collect_due_schedules (app/application/scheduling/use_cases.py)
    └─ per-group цикл (строка 120): группы с is_active=False ПРОПУСКАЮТСЯ (D-05)
         └─ след: structlog, БЕЗ SendLog (D-06)
```

### Recommended Project Structure

```
app/pages/account_groups.py            # НОВЫЙ роутер: страница, паршал, toggle, delete (или секция в accounts.py — решает планировщик)
app/templates/account_groups/
├── list.html                          # экран: шапка аккаунта, плашка синка, линейка счётчика, список, сентинел
├── partial_cards.html                 # страница прокрутки (идентичная строка — правило Фазы 1)
├── includes/group_row.html            # макрос строки (прецедент 01-04: строка живёт в макросе)
└── partials/sync_result.html          # блок статуса/результата синка с условным hx-get (образец sync_status_card.html)
alembic/versions/0014_account_sync_result.py   # миграция D-12 (+ маркер D-11 на groups)
УДАЛЯЮТСЯ: app/templates/groups/ (3 файла), маршруты /groups* из app/pages/groups.py
           (кроме redirect-а /groups → /accounts), POST /api/groups
```

### Pattern 1: Самоостанавливающийся опрос (D-09) — переносится дословно

Главный артефакт плана 01-06. Условие с HTMX-атрибутами стоит ВНУТРИ открывающего тега; опрос прекращается тем, что очередной ответ приходит без атрибутов:

```jinja
{# Source: app/templates/accounts/partials/sync_status_card.html:46 [VERIFIED] #}
<div data-row id="account-row-{{ account_id }}"{% if status == 'syncing' %} hx-get="/accounts/{{ account_id }}/sync-status" hx-trigger="every 5s" hx-swap="outerHTML"{% endif %} style="--cols: {{ ACCOUNT_COLS }}">
```

Четыре инварианта из 01-06 SUMMARY: условие внутри тега; id и hx-get на одном элементе, заменяемом целиком; ответ — той же раскладки, что список; опрос объявлен только в ветке `syncing`. Обязательна парная страховка тестами: «опрос есть при syncing» + «опроса НЕТ при не-syncing» (образцы: `test_sync_polling_stops`, `test_sync_polling_continues_while_syncing`, `test_accounts_polling_only_on_syncing_row`).

### Pattern 2: Тумблер в POST-форме (D-08, GRP-05)

```jinja
{# Source: 01-04 SUMMARY (паттерн подтверждён в groups/includes/group_row.html) #}
<form method="post" action="/accounts/{{ account.id }}/groups/{{ g.id }}/toggle" x-data x-on:change="$el.submit()">
  {{ toggle(name='is_active', checked=g.is_active, id='group-toggle-' ~ g.id) }}
</form>
```

Событие `change` всплывает к форме; без Alpine форма остаётся настоящей POST-формой (тесты `*_degrades_without_alpine` — правило Фазы 2 D-09: базовый путь без JS).

### Pattern 3: Сентинел бесконечной прокрутки с протаскиванием поиска (D-03/D-04)

```jinja
{# Source: app/templates/groups/list.html:98 [VERIFIED] — форма переносится, /groups заменяется новым маршрутом #}
<div hx-get="/groups/partial?offset={{ next_offset }}&limit=30{% for k, v in (filter_params|default({})).items() %}&{{ k }}={{ v|string|urlencode }}{% endfor %}" hx-trigger="revealed" hx-swap="outerHTML" class="empty__hint">Загрузка...</div>
```

`filter_params` для нового экрана — только `search` (D-03: фильтры не переносятся). Счётчик «N активных из M» — отдельные `COUNT`-запросы, не длина загруженной страницы (D-04).

### Pattern 4: Новое условие в диспетчере — по прецеденту D-01 Фазы 2 (D-05/D-06)

Место: per-group цикл `collect_due_schedules`. Рекомендация — фильтр на этапе формирования задач (не в WHERE выборки расписаний): семантика группового пропуска не влияет на `next_run_at` расписания (оно продолжает продвигаться), а фильтр в цикле даёт простой и тестируемый срез — тесты кладутся рядом с `tests/test_application/test_collect_due_draft.py`.

```python
# Source: app/application/scheduling/use_cases.py:120-144 [VERIFIED] — текущий цикл:
#   for group_id in schedule.group_ids or []:
#       task = DispatchTask(...)
#       if account.type in ("wa", "max"):
#           group = await session.get(Group, group_id)
#           ...
# Рекомендуемый срез (D-05): перед созданием DispatchTask —
#   group = await session.get(Group, group_id)
#   if group is not None and not group.is_active:
#       logger.info("group_skipped_inactive", group_id=group_id, schedule_id=schedule.id)
#       continue    # D-06: тихо — без SendLog
```

Замечание для планировщика: для WA/MAX группа уже загружается `session.get(Group, group_id)`; для TG — нет. Единый `session.get` перед ветвлением по типу (identity map SQLAlchemy сделает повторный `get` в WA/MAX-ветке бесплатным) или один batch-запрос активных id на расписание — оба варианта в пределах дискреции («выборка при диспетчеризации или фильтр при постановке задач»). Комментарий в коде обязан объяснить «почему здесь» — стиль файла задан комментарием D-01 (строки 81-91).

### Pattern 5: Переинвентаризация при синке (D-10/D-11) — замена only-add

Текущий синк (все три пути) — only-add: `if g["id"] not in seen: session.add(Group(...))` [VERIFIED: app/pages/accounts.py:789-801, app/worker/tasks.py:288-300, 390-399]. Новая логика в одном общем хелпере (три места вызова — page-обработчик TG и две Celery-таски):

1. загрузить существующие группы аккаунта map по `group_external_id`;
2. для пришедших: новых — добавить (is_active=True по умолчанию модели), существующих — обновить `name` при отличии (счётчик «обновлено имён»);
3. для не пришедших: проставить маркер «не найдена при синке» (НЕ удалять, `is_active` не трогать);
4. для пришедших с ранее стоявшим маркером — маркер снять;
5. записать на аккаунт `last_synced_at` + счётчики/ошибку.

**Общий хелпер — обязательная рекомендация:** сейчас блок синка скопирован трижды с посимвольными расхождениями; расширение логики втрое в трёх местах — источник тихих расхождений (WA-копия и MAX-копия уже разошлись бы при правке).

### Anti-Patterns to Avoid

- **Per-group кнопка ↻ из макета (строка ~948 unpacked)** — НЕ реализуется (D-12): протокола синка одной группы у воркеров нет.
- **CTA «Добавить группу» (строка ~1491)** — НЕ реализуется (D-13).
- **HTMX-атрибуты опроса вне условия по статусу** — вечный опрос каждые 5 с на каждой вкладке (T-06-01, план 01-06).
- **Фильтр `is_active` групп в WHERE выборки расписаний** — не то место: расписание активно, пропускается группа; WHERE-фильтр здесь вообще невозможен (`group_ids` — JSON-список на расписании).
- **Мгновенный «×» удаления из макета** — заменяется панелью подтверждения (правило Фазы 1); панель — ВНЕ элемента, заменяемого опросом (урок sync_status_card, T-11-04).
- **Запись SendLog при пропуске выключенной группы** — прямо запрещено D-06.
- **Правка протоколов wa_worker/max_worker/Telethon** — жёсткая рамка milestone.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Чистка `group_ids` расписаний при удалении группы | свой обход расписаний | `ScheduleRepository.remove_group_ids` [VERIFIED: app/repositories/schedule.py:41-53] | уже учитывает JSON-колонку и владение через join с Ad |
| Опрос статуса фонового синка | WebSocket/SSE/setInterval | условные HTMX-атрибуты (Pattern 1) | паттерн закреплён тестами Фазы 1, самоостанавливается |
| Строка списка/карточка/тумблер/бейдж/пустое состояние/модалка | новая разметка | макросы `components/` (13 файлов: toggle, badge, button, modal, empty_state, filters, …) [VERIFIED: ls app/templates/components] | дизайн-система Фазы 1; `app.css` закрыт для новых классов, кроме санкционированных |
| Иконка/цвет мессенджера, аватар-инициалы | свои SVG | `includes/messenger_icon.html` + `.avatar` (приём 01-04/01-06) | ветка else макроса несёт utility-классы — не вызывать для неизвестного типа |
| Форматирование «последняя синхронизация N назад» | свой JS | `format_datetime_for_user` глобал [VERIFIED: app/pages/common.py:149-165] — либо серверный «N назад»-хелпер рядом | таймзона пользователя уже решена |

**Key insight:** в этом репозитории «стандартная библиотека» — это его собственная Фаза 1. Любой элемент экрана, собранный мимо макросов, провалит `test_list_page_no_utility_classes` / `test_no_unsafe_escaping` и ревью.

## Runtime State Inventory

Фаза включает снос раздела и миграцию схемы; проверены категории:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `groups.is_active` уже в живой схеме (с 0001/0004); новые колонки — миграция `0014` | Alembic ревизия; данных мигрировать не нужно (новые колонки nullable) |
| Live service config | Нет — воркеры WA/MAX конфигурируются через Redis-очереди, имена очередей не меняются | none |
| OS-registered state | Нет — деплой через Docker Compose, cron/beat расписания Celery не ссылаются на `/groups` | none |
| Secrets/env vars | Нет — ни один ключ не ссылается на раздел групп | none |
| Build artifacts | Нет — build-шага нет (htmx/Alpine вендорены) | none |
| **Внешние ссылки на `/groups`** | Редиректы в обработчиках `app/pages/accounts.py` (sync-groups, retry-sync возвращают на `/groups` [VERIFIED: accounts.py:734,756,759,804]); возможные закладки пользователей | D-01: `/groups` отвечает 302 на `/accounts` — закладки живы; редиректы обработчиков перенаправить на новый экран |

## Common Pitfalls

### Pitfall 1: Удаление POST /api/groups рушит посев ~9 файлов тестов
**What goes wrong:** `POST /api/groups` — де-факто seeding-хелпер тестов: `tests/test_e2e.py`, `test_routes/test_schedules.py`, `test_schedules_api_ownership.py`, `test_schedules_toggle_detached.py`, `test_schedules_api_null.py`, `test_limits.py`, `test_history.py`, `test_routes/test_groups.py`, `test_application/test_account_deletion_schedules.py`, `test_pages/test_schedules_detached_account.py` [VERIFIED: grep по tests/]. Удаление входа без переделки посева — красная суита.
**How to avoid:** отдельная задача плана: conftest-фикстура/хелпер прямой ORM-вставки `Group` (через `db_session`), затем механическая замена вызовов. `test_create_groups_no_limit` (документирует отсутствие лимита на группы) удаляется вместе с входом — enforcement-точки лимита за ним нет [VERIFIED: tests/test_routes/test_limits.py:15-16 «No limit on groups», billing_service.py не содержит функций лимита групп].
**Warning signs:** план «удалить POST /api/groups» одной строкой без списка затронутых тестов.

### Pitfall 2: Целевая база на ревизии 0012 — очередь миграций растёт
**What goes wrong:** blocker из STATE.md: прод не выкатил `0013_ad_status`; новая `0014` встаёт в очередь. До выката прода плашка «последняя синхронизация» и маркеры D-11 не наблюдаемы в живой системе.
**How to avoid:** миграция 0014 — только additive nullable-колонки (без backfill, без NOT NULL), чтобы выкат `0012→0014` был одним безопасным прыжком. Код обязан переживать `last_synced_at IS NULL` (показ «синхронизация ещё не выполнялась»).
**Warning signs:** дефолты NOT NULL или data-migration в 0014; UAT-критерии, проверяемые только на проде.

### Pitfall 3: Переинвентаризация × три копии синка
**What goes wrong:** логика синка скопирована в трёх местах (TG в `accounts.py:780-803`, WA в `tasks.py:278-304`, MAX в `tasks.py:380-403`). Реализация D-10/D-11/D-12 в каждой копии отдельно гарантирует расхождение (прецедент: `partial_cards.html` не знал про MAX — автофикс 01-06).
**How to avoid:** единый хелпер переинвентаризации (например, `app/application/accounts/` рядом с существующими use cases), принимающий session, account, `fetched: list[{"id","name"}]` и возвращающий счётчики; три места вызывают его.
**Warning signs:** план с тремя задачами «поменять синк в TG/WA/MAX» без общего модуля.

### Pitfall 4: Пропуск D-05 ломает существующие тесты диспетчеризации
**What goes wrong:** `tests/test_application/`, `tests/test_worker/`, `tests/test_worker_tasks.py` сеют группы и ждут задач; группы по умолчанию `is_active=True` (`default=True` в модели), но тесты, создающие Group напрямую с выключенным флагом или мокающие session.get, могут повести себя иначе. Также `session.get(Group, ...)` для TG-пути — новый запрос в цикле: тест с мок-сессией без групп в identity map упадёт неожиданно.
**How to avoid:** сначала RED-тесты нового поведения (активная — задача есть, выключенная — задачи нет, для всех трёх типов), затем правка; полный прогон 895 обязателен. TDD-режим включён в конфиге (`tdd_mode: true`).
**Warning signs:** правка `collect_due_schedules` в одной задаче с вёрсткой экрана.

### Pitfall 5: Экран показывает группы, а «активных из M» считает по странице
**What goes wrong:** D-04 прямо требует отдельный запрос; соблазн посчитать по загруженным 30 строкам даёт враньё на аккаунтах с сотнями чатов.
**How to avoid:** два скалярных COUNT (total, active) в обработчике страницы; паршал прокрутки счётчик не трогает.

### Pitfall 6: D-07 — редактор объявления теряет выключенные-но-выбранные группы
**What goes wrong:** `app/pages/ads.py:216-226` грузит для редактора только `Group.is_active == True` [VERIFIED, verbatim: `select(Group).where(Group.user_id == user.id, Group.is_active == True)`]; `sched_card.html:63` фильтрует по аккаунту: `{%- set account_groups = groups | selectattr('account_id', 'equalto', s.account_id) | list if s.account_id else [] -%}` [VERIFIED]. Если просто убрать фильтр is_active — список выбора захламится (нарушение D-07); если оставить — выбранная-но-выключенная группа молча исчезает из карточки, и «выбрано N из M» врёт.
**How to avoid:** страница передаёт активные + те неактивные, чьи id входят в `group_ids` расписаний этого объявления; шаблон помечает неактивные («отключена», чекбокс `disabled` только для НЕвыбранных — выбранную можно снять). Внимание: `group_ids` расписания и рендер `chosen` (`sched_card.html:66`) уже есть.
**Warning signs:** правка только шаблона без правки выборки, или наоборот.

### Pitfall 7: Снос `/groups` тянет за собой параметризации общих тестов
**What goes wrong:** раздел groups прошит в `tests/test_pages/test_responsive_markup.py` (SECTION_URLS/MIGRATED_SECTIONS), `test_htmx_preserved.py` (infinite scroll chain), `test_shell.py` (навигация), `test_templates/test_components.py`; плюс собственные `test_pages/test_groups.py`, `test_routes/test_groups_bulk.py` [VERIFIED: grep tests/]. Слепое удаление роутов роняет десятки тестов.
**How to avoid:** задача сноса включает: удаление параметризаций/веток `_seed_section` для groups, перенос поведенческих проверок (toggle ownership, delete чистит расписания) на новый экран, добавление нового раздела в общие параметризации (новый экран обязан пройти `test_list_page_has_responsive_primitives`-класс проверок).

### Pitfall 8: Плашка результата синка внутри заменяемого опросом элемента
**What goes wrong:** урок T-11-04 (01-06): элемент, заменяемый `hx-swap="outerHTML"`, приносит с каждым ответом свои дочерние блоки; панель подтверждения/плашка внутри него дублируется или исчезает.
**How to avoid:** плашка результата и панели подтверждения живут вне подменяемого блока статуса; подменяемый блок — минимальный.

## Code Examples

### Существующий контракт toggle/delete (переносится на новые маршруты)

```python
# Source: app/pages/groups.py:228-267 [VERIFIED] — суть:
# toggle: select(Group).where(Group.id == group_id, Group.user_id == user.id)
#         group.is_active = not group.is_active; commit; redirect
# delete: та же выборка; ScheduleRepository(db).remove_group_ids(user.id, {group.id});
#         db.delete(group); commit; redirect
# Для нового экрана добавить в WHERE: Group.account_id == account_id (маршрут вложен в аккаунт),
# и redirect на /accounts/{account_id}/groups.
```

### Вход синка и его текущие редиректы (меняются на новый экран)

```python
# Source: app/pages/accounts.py:737-804 [VERIFIED] — POST /accounts/{account_id}/sync-groups
# - владение: MessengerAccount.id == account_id AND user_id == user.id
# - guard: if account.status == "syncing": redirect (повторный запуск не ставится)
# - tg_user: синхронно get_groups() -> only-add -> commit -> RedirectResponse("/groups")
# - wa/max: (в connect-flow и retry-sync) status="syncing" + celery.send_task(...)
# Все RedirectResponse(url="/groups") в этом файле (строки 734, 756, 759, 804) должны
# перенаправляться на /accounts/{account_id}/groups.
```

### Статусы аккаунта (для веток экрана и опроса)

```python
# Source: app/models/messenger_account.py:19 [VERIFIED, verbatim]:
#   status: Mapped[str] = mapped_column(String(20), default="disconnected")
# Наблюдаемые значения по коду [VERIFIED: accounts.py:622,636,680,726; tasks.py:302,311,323]:
#   "disconnected" | "connecting" | "syncing" | "sync_failed" | "active"
# Ветки sync_status_card.html: 'active' / 'sync_failed' / 'syncing' — образец для нового блока.
```

### Модель Group — что есть и чего нет

```python
# Source: app/models/group.py:12-29 [VERIFIED, verbatim ключевые колонки]:
#   is_active: Mapped[bool] = mapped_column(Boolean, default=True)
#   last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
#   error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
# НЕТ: количества участников (подпись макета «N участников» — данных нет, D-03/дискреция),
#      маркера «не найдена при синке» (нужен D-11), unique constraint на (account_id, group_external_id)
#      — дедупликация app-level через set существующих external_id.
# last_error/error_at — про ошибки ОТПРАВКИ (use_cases.py:305-306), НЕ переиспользовать под D-11.
```

### Миграция 0014 — рекомендуемая форма (дискреция планировщика в пределах D-12)

```python
# По конвенции файлов alembic/versions/ (head: 0013_ad_status.py [VERIFIED: ls]):
# 0014_sync_result_and_group_missing.py — только additive nullable:
#   messenger_accounts.last_synced_at   DateTime(timezone=True), nullable
#   messenger_accounts.last_sync_result Text, nullable   # JSON-строка: {"found":N,"new":M,"renamed":K,"missing":J,"error":null}
#   groups.missing_since                DateTime(timezone=True), nullable  # D-11: NULL = найдена; ставится/снимается синком
# Text с JSON-строкой, а не sa.JSON: тесты на SQLite in-memory, прод на PostgreSQL —
# Text работает одинаково в обоих; парсинг в page-обработчике с защитой от мусора.
```

## State of the Art

Не применимо в классическом смысле — фаза не выбирает технологии. Внутрипроектная «актуальность»:

| Old Approach (сносится) | Current Approach (эта фаза) | Основание |
|--------------------------|------------------------------|-----------|
| Глобальный `/groups` с фильтрами, статистикой, bulk | `/accounts/{id}/groups` с поиском и тумблером | D-01…D-04 |
| `is_active` — декоративный флаг | пропуск при диспетчеризации | D-05 |
| Синк only-add без результата | переинвентаризация + результат на аккаунте | D-09…D-12 |
| `POST /api/groups` без проверки владения `account_id` | вход удалён | D-14 |
| Браузерный `confirm()`/bulk `alert` в скрипте групп | панель подтверждения Фазы 1 | правило Фазы 1 |

## Project Constraints (from CLAUDE.md)

- Команды через `just` / `uv`: тесты — `uv run pytest tests/ -v` (`just test`), миграция — `just migrate "описание"` / `just upgrade`.
- Тесты: SQLite in-memory (`sqlite+aiosqlite:///:memory:`), полная схема на тест, фикстуры `client`, `db_session`, `auth_headers` из `tests/conftest.py`.
- Стек зафиксирован: FastAPI + SQLAlchemy async + Celery/Redis + Jinja2; SPA и правка протоколов отправки — вне скоупа.
- graphify: для вопросов по кодовой базе — `graphify query` прежде чтения файлов; после правок кода — `graphify update .` (AST-only).
- Никаких внешних CDN-ресурсов (htmx/Alpine вендорены, Tailwind удалён).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Форма хранения результата синка — Text-колонка с JSON-строкой `{found,new,renamed,missing,error}` | Code Examples / миграция | Низкий: D-12 отдаёт «точную форму за планировщиком»; альтернативы (отдельные int-колонки) равноценны — решает планировщик |
| A2 | Маркер D-11 — колонка `groups.missing_since` (nullable DateTime) | Pattern 5 / миграция | Низкий: возможен bool `is_missing`; DateTime даёт бесплатную подпись «не найдена с …» |
| A3 | Пропуск D-05 ставится в per-group цикл `collect_due_schedules`, а не в `dispatch_send_tasks` | Pattern 4 | Низкий: CONTEXT явно отдаёт выбор среза исполнителю; цикл — единственное место, где группа уже адресуется поштучно и рядом лежат тесты test_application |
| A4 | `GET/DELETE/PATCH /api/groups` можно снести как мёртвые: потребители — только тесты (grep по app/templates и app/static вхождений не дал) | Summary / D-14 | Средний: внешние API-клиенты вне репозитория не исключены; продукт — SaaS с web-UI, публичного API-контракта в документах нет. Планировщику: подтвердить у владельца или оставить GET/PATCH с выравниванием владения |
| A5 | Строка входа «клик по аккаунту» на /accounts потребует правки `accounts/list.html`/`partial_cards.html`/`sync_status_card.html` синхронно (разметка строки задублирована посимвольно) | Architecture | Низкий: зафиксировано в 01-06 SUMMARY («правится одна — синхронно правится вторая» + третья копия в sync_status_card) |

## Open Questions

1. **Судьба `GET/DELETE/PATCH /api/groups` (D-14, дискреция).**
   - Известно: UI-потребителей нет; потребители — только тесты [VERIFIED: grep].
   - Неясно: существуют ли внешние интеграции.
   - Рекомендация: снести все три вместе с POST (наименьшая поверхность, класс CR-01 закрыт целиком); тесты `test_routes/test_groups.py` переписать на новые страничные маршруты. Если планировщик оставляет — обязательное выравнивание: проверка `account_id`-владения на каждом входе.
2. **Куда положить новый роутер: секция в `app/pages/accounts.py` (уже 819 строк) или новый `app/pages/account_groups.py`.**
   - Рекомендация: новый модуль + `app/templates/account_groups/`; регистрация роутера в `app/main.py` по образцу остальных. STRUCTURE.md фиксирует правило добавления страниц.
3. **Показ «в N расписаниях» в подписи (D-08, дискреция).** Данные считаются как в старом `_get_group_stats` (обход JSON `group_ids` в Python — `app/pages/groups.py:50-56`). Дёшево для страницы в 30 строк; рекомендация — показывать: это объясняет пользователю последствия удаления.

## Environment Availability

Фаза не вводит внешних зависимостей: используется существующий стек (PostgreSQL/Redis/Celery в проде, SQLite in-memory в тестах, uv/just локально). Alembic-миграция на целевую базу — за владельцем (см. Pitfall 2: прод на ревизии `0012`). Отдельный аудит инструментов не требуется.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (httpx AsyncClient, aiosqlite in-memory) |
| Config file | `tests/conftest.py` (фикстуры `client`, `db_session`, `auth_headers`); pytest.ini/секции pyproject не обнаружено |
| Quick run command | `uv run pytest tests/test_pages/<file>.py -x -q` |
| Full suite command | `uv run pytest tests/ -q` (текущая база: 895 passed) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GRP-04 | Экран показывает только группы этого аккаунта; чужой аккаунт — недоступен | integration | `uv run pytest tests/test_pages/test_account_groups.py -x -q` | ❌ Wave 0 |
| GRP-04 | Адаптивные примитивы + отсутствие utility-классов + сентинел с search | integration | `uv run pytest tests/test_pages/test_responsive_markup.py -x -q` (новая секция) | ✅ файл есть, секция — Wave 0 |
| GRP-05 | Toggle: своя переключается, чужая — нет; форма деградирует без Alpine | integration | `uv run pytest tests/test_pages/test_account_groups.py -x -q` | ❌ Wave 0 |
| GRP-05/D-05 | Диспетчер не ставит задач для is_active=False (tg/wa/max); ставит после включения; SendLog не пишется | unit/integration | `uv run pytest tests/test_application/test_collect_due_inactive_group.py -x -q` | ❌ Wave 0 |
| GRP-05/D-07 | Выключенная-но-выбранная группа видна в карточке расписания с пометкой; невыбранная выключенная — не видна | integration | `uv run pytest tests/test_pages/test_editor_schedules.py -x -q` (дополнение) | ✅ файл есть |
| GRP-06 | Delete чистит group_ids расписаний; панель подтверждения в разметке | integration | `uv run pytest tests/test_pages/test_account_groups.py -x -q` | ❌ Wave 0 |
| GRP-07 | Переинвентаризация: новые добавлены, имена обновлены, пропавшие помечены, is_active не тронут; результат записан на аккаунт | unit | `uv run pytest tests/test_application/test_group_resync.py -x -q` | ❌ Wave 0 |
| GRP-07 | Опрос: hx-атрибуты только при syncing; останавливается | integration | по образцу `test_htmx_preserved.py::test_sync_polling_*` | ✅ образцы есть |
| D-01 | `/groups` — 302 на `/accounts`; пункта «Группы» нет в навигации | integration | `uv run pytest tests/test_pages/test_shell.py -x -q` (правка) | ✅ файл есть |
| D-13 | ROADMAP/REQUIREMENTS согласованы | manual-only | просмотр диффа двух документов | — (docs) |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/<затронутая директория> -x -q`
- **Per wave merge:** `uv run pytest tests/ -q`
- **Phase gate:** полный прогон зелёный (≥895 минус удалённые с разделом, плюс новые) перед `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_pages/test_account_groups.py` — GRP-04/05/06 (страница, владение, toggle, delete, поиск, сентинел)
- [ ] `tests/test_application/test_collect_due_inactive_group.py` — D-05/D-06 (образец: `test_collect_due_draft.py`)
- [ ] `tests/test_application/test_group_resync.py` — D-10/D-11/D-12 (хелпер переинвентаризации)
- [ ] conftest-хелпер посева групп через ORM — замена `POST /api/groups` в ~9 файлах (Pitfall 1)
- [ ] Framework install: не требуется

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (не меняется) | существующая cookie-сессия, `get_user_from_cookie` |
| V3 Session Management | no (не меняется) | — |
| V4 Access Control | **yes — главная категория фазы** | владение на КАЖДОМ входе (правило Фазы 2): страница, паршал, toggle, delete, sync — `WHERE user_id == user.id AND account_id == {id}`; поведенческие тесты «чужое не переключается» (образец `test_groups_toggle_route_unchanged`) |
| V5 Input Validation | yes | `offset ge=0`, `limit ge=1 le=100` (существующий контракт паршалов), `search` — параметризованный `ilike`, urlencode в сентинеле |
| V6 Cryptography | no | — |

### Known Threat Patterns for этого стека

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| IDOR: чужой `account_id`/`group_id` в URL | Elevation of Privilege | двойной WHERE (user + account) на всех 5+ новых входах; RED-тесты владения до реализации |
| Удаление входа с дырой владения (`POST /api/groups` не проверял `account_id`) | Elevation of Privilege | D-14 — само удаление и есть митигация; если GET/PATCH остаются — выравнивание владения |
| XSS через имена групп из мессенджера (недоверенный внешний ввод!) | Tampering | Jinja2 autoescape, готовая разметка макросам не передаётся; `test_no_unsafe_escaping` обходит все шаблоны |
| Вечный опрос статуса (DoS на своих же серверах) | Denial of Service | условные hx-атрибуты + парные тесты остановки (T-06-01, план 01-06) |
| Повторный запуск синка при `status=='syncing'` | DoS / гонка | существующий guard в `accounts_sync_groups` (accounts.py:758) переносится на новый вход |
| Инъекция в LIKE-поиске | Tampering | SQLAlchemy `ilike` с параметром (существующая форма `_build_groups_query` — `pattern = f"%{...}%"` как bind-параметр, не конкатенация SQL) |
| CSRF на POST-формах | Tampering | статус-кво проекта: cookie-сессия без CSRF-токенов; новые формы не хуже существующих — новых поверхностей класса не добавляется; фиксить общесистемно — вне фазы (отметить в SECURITY-заметках плана) |

## Sources

### Primary (HIGH confidence — прочитано в этой сессии)
- `app/application/scheduling/use_cases.py` (весь файл) — точка D-05, прецедент D-01
- `app/pages/groups.py`, `app/pages/accounts.py:620-819`, `app/pages/ads.py:195-254`, `app/pages/common.py:90-169`
- `app/worker/tasks.py:1-140, 240-451` — dispatch и оба фоновых синка
- `app/models/group.py`, `app/models/messenger_account.py`, `app/routes/groups.py`, `app/repositories/group.py`, `app/repositories/schedule.py:41-53`
- `app/templates/accounts/partials/sync_status_card.html`, `app/templates/ads/includes/sched_card.html:140-170`, `app/templates/groups/list.html:98`
- `design/new_broadcaster_design.unpacked.html:900-969, 1485-1496, 1820-1857` — канонический макет экрана
- `.planning/phases/01-interfeysnyy-fundament/01-04-SUMMARY.md`, `01-06-SUMMARY.md` — паттерны и их инварианты
- `.planning/ROADMAP.md:179-195`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `03-CONTEXT.md`
- graphify-out граф — ориентация (запросы «group sync toggle…», «schedule dispatch…», «billing limit groups»); граф частично STALE — использовался только для навигации, все утверждения перепроверены чтением файлов

### Secondary / Tertiary
- Нет: внешние источники не требовались (нулевые новые зависимости).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — стек существующий, установка пакетов не требуется
- Architecture: HIGH — все паттерны имеют работающие прецеденты в репо с тестами; точки правки прочитаны построчно
- Pitfalls: HIGH — тестовый фоллаут D-14 и параметризации проверены grep-ом; блокер миграции — из STATE.md
- Дискреционные формы (A1–A3): MEDIUM — решает планировщик, риски низкие

**Research date:** 2026-08-12
**Valid until:** 2026-09-11 (стабильно: brownfield, зависит только от собственного репозитория; инвалидируется любым мержем, трогающим `app/pages/groups.py`, `collect_due_schedules` или синк-таски)
