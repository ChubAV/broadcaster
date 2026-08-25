# Phase 4: Дашборд и история - Pattern Map

**Mapped:** 2026-08-13
**Files analyzed:** 19 new/modified files
**Analogs found:** 18 / 19

Все выдержки ниже прочитаны из исходников в этой сессии. Номера строк — на момент маппинга.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app/application/analytics/__init__.py` | package init | — | `app/application/accounts/__init__.py` | exact |
| `app/application/analytics/send_analytics.py` (new) | service / use-case | batch aggregation + streaming read | `app/application/accounts/group_resync.py` + `app/application/scheduling/use_cases.py` | exact |
| `app/pages/dashboard.py` (rewrite) | controller (page) | request-response | `app/pages/history.py` (`history_list`) | exact |
| `app/pages/dashboard.py` → `GET /dashboard/feed` (new partial route) | controller (partial) | polled request-response | `app/pages/history.py:62 history_partial` + `app/pages/accounts.py` sync-status route | exact |
| `app/pages/history.py` → `GET /history/export` (new) | controller | streaming file-I/O | `app/pages/history.py:155 history_list` (filters) — **нет аналога стриминга** | role-match |
| `app/pages/history.py` → `POST /history/{id}/retry` (new) | controller | command → queue | `app/pages/accounts.py:715-741` (`retry-sync`, `celery.send_task`) + `_claim_sync_slot:750-760` | exact |
| `app/pages/history.py` (счётчик D-31, чипсы, миграция фильтров в analytics) | controller | CRUD/read | себя же, `_apply_history_filters:46-59` | exact |
| `app/worker/tasks.py` → `retry_send` (new task) | worker task | event-driven → queue | `app/worker/tasks.py:243-265 check_schedules` | exact |
| `app/worker/tasks.py` → `build_dispatch_task` (extract) | utility | transform | `app/application/scheduling/use_cases.py:179-202` (инлайн) + `group_resync` как прецедент выноса | exact |
| `app/templates/dashboard.html` (rewrite) | template (page) | render | `app/templates/history/list.html` | exact |
| `app/templates/dashboard/partial_feed.html` (new) | template (partial) | polled render | `app/templates/history/partial_cards.html` | exact |
| `app/templates/dashboard/includes/metric_tile.html` (new) | template (macro) | render | `app/templates/dashboard.html:22-39` (`data-metrics` + `card_open`/`mono`) | role-match |
| `app/templates/dashboard/includes/feed_row.html` (new) | template (macro) | render | `app/templates/history/includes/history_card.html` | exact |
| `app/templates/dashboard/includes/upcoming_row.html` (new) | template (macro) | render | `app/templates/accounts/partials/sync_status_card.html` (строка `data-row`) | role-match |
| `app/templates/dashboard/includes/heatmap.html` (new) | template (macro) | render | `.day-grid` / `.chip` в `app.css:1407-1412` | partial |
| `app/templates/history/list.html` (rewrite) | template (page) | render | себя же + `components/filters.html` | exact |
| `app/templates/history/includes/history_card.html` (edit: ошибка, копирование, повтор) | template (macro) | render | себя же + `components/modal.html` | exact |
| `app/templates/history/detail.html` (rework) | template (page) | render | `history/list.html` | exact |
| `app/static/css/app.css` (+heatmap, +дельта, +чипсы-ссылки) | stylesheet | — | `app.css:1372-1412` (примитив `.chip`) | exact |
| `alembic/versions/0016_send_logs_user_sent_at.py` (new) | migration | DDL | `alembic/versions/0015_groups_unique_account_external.py` | exact |
| `tests/test_migrations/test_0016_send_logs_user_sent_at.py` (new) | test | — | `tests/test_migrations/test_0013_ad_status.py` | exact |

---

## Pattern Assignments

### `app/application/analytics/send_analytics.py` (service, batch aggregation)

**Analog A (форма модуля, докстринг-контракт):** `app/application/accounts/group_resync.py`
**Analog B (сигнатура, датакласс):** `app/application/scheduling/use_cases.py`

**Imports pattern** (`group_resync.py:31-42`):
```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.accounts.dto import GroupResyncResult
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
```

**Сигнатура функции слоя application** (`group_resync.py:128-135`) — сессия первым позиционным, всё остальное keyword-only:
```python
async def apply_group_resync(
    session: AsyncSession,
    account: MessengerAccount,
    fetched: Sequence[Mapping[str, Any]],
    *,
    messenger_type: str,
    allow_full_wipe: bool = False,
) -> GroupResyncResult:
```
То же у `collect_due_schedules` (`use_cases.py:51-56`):
```python
async def collect_due_schedules(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    check_limit,
) -> list[DispatchTask]:
    if now is None:
        now = datetime.now(timezone.utc)
```
→ функции модуля аналитики: `send_metrics(session, *, user_id, now=None, window=...)`, `activity_heatmap(session, *, user_id, now, tz, days=7)`, `recent_feed(session, *, user_id, limit)`, `upcoming_sends(session, *, user_id, now, limit)`, `history_count(session, *, user_id, ...)`.

**Датакласс возврата** (`use_cases.py:35-48`) — `slots=True`:
```python
@dataclass(slots=True)
class DispatchTask:
    type: str
    ad_id: int
    group_id: int
    account_id: int
    schedule_id: int
    # WA-specific fields (populated for type="wa")
    user_id: int | None = None
    ad_text: str | None = None
    ...
```

**Докстринг-контракт «почему хелпер один» + прохибиции** (`group_resync.py:1-29`, сокращённо) — образец того, как оформляется публичный модуль, у которого несколько потребителей:
```python
"""Полная переинвентаризация состава групп аккаунта — одна на все три пути.

ПОЧЕМУ ХЕЛПЕР ОДИН. До этой фазы блок синхронизации был скопирован в трёх
местах ... копии уже разошлись посимвольно ...

ЧЕГО ХЕЛПЕР НЕ ДЕЛАЕТ (D-11, прохибиция плана):
- не удаляет строк ...
- не коммитит: транзакцией управляет вызывающий ...
"""
```
→ `send_analytics.py` обязан выписать: не читает `Request`, ничего не пишет в БД, не коммитит, не знает про Jinja; контракт публичен для Фазы 6.

**Аггрегация «много счётчиков за один round-trip»** — образец `get_shell_context` (`app/pages/common.py:276-312`):
```python
counts = (
    await db.execute(
        select(
            select(func.count()).select_from(Ad)
            .where(Ad.user_id == user.id).scalar_subquery().label("ads"),
            ...
            select(func.count()).select_from(MessengerAccount)
            .where(MessengerAccount.user_id == user.id,
                   MessengerAccount.status == "active")
            .scalar_subquery().label("sessions_online"),
        )
    )
).one()
```
и нормализация `NULL` (`common.py:339`): `used = int(await db.scalar(used_stmt) or 0)`.

**Нормализация naive datetime** — копировать дословно из `common.py:161-162` / `:216-217`:
```python
if value.tzinfo is None:
    value = value.replace(tzinfo=timezone.utc)
tz = _get_timezone_for_user(user)
local = value.astimezone(tz)
```
(SQLite отдаёт `DateTime(timezone=True)` naive — см. RESEARCH §Pitfall 5. Бакетирование heatmap делается в Python, диалектных SQL-функций не заводить.)

**Фильтры истории — переносятся ДОСЛОВНО** из `app/pages/history.py:46-59`:
```python
def _apply_history_filters(query, status, messenger_type, account_id, period):
    if status:
        query = query.where(SendLog.status == status)
    if messenger_type:
        query = query.where(SendLog.messenger_type == messenger_type)
    if account_id is not None:
        query = query.where(Group.account_id == account_id)
    if period == "7d":
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        query = query.where(SendLog.sent_at >= cutoff)
    elif period == "30d":
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        query = query.where(SendLog.sent_at >= cutoff)
    return query
```
и `_history_filter_params` (`history.py:28-43`). Импортёр за пределами модуля уже есть — `app/pages/admin.py:11-12`; переезд обязан обновить его импорт. Фильтр по аккаунту работает только при `outerjoin(Group)` — экспорт обязан строить тот же join.

---

### `app/pages/dashboard.py` (controller, request-response) — переписывается целиком

**Analog:** `app/pages/history.py:155-226` (`history_list`)

**Imports + router** (`history.py:1-16`):
```python
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.send_log import SendLog
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30
```

**Auth/guard на входе** (`history.py:166-168`, тот же в каждом страничном обработчике):
```python
user = await get_user_from_cookie(request, db, settings)
if not user:
    return RedirectResponse(url="/login", status_code=302)
```

**Ответ страницы** (`history.py:207-226`) — `active_page` и `is_admin` обязательны:
```python
return templates.TemplateResponse(
    "history/list.html",
    {
        "request": request,
        "user": user,
        "is_admin": check_is_admin(user, settings),
        "logs": logs,
        ...
        "active_page": "history",
    },
)
```

**Что удаляется** — текущий блок `stats` и расчёт UTC-полуночи (`dashboard.py:54-70`), дефект D-02:
```python
today_start = datetime.now(timezone.utc).replace(
    hour=0, minute=0, second=0, microsecond=0
)
```
**Что переиспользуется как затравка ленты** (`dashboard.py:73-96`) — форма запроса и маппинг строк:
```python
recent_query = (
    select(SendLog, Group)
    .outerjoin(Group, SendLog.group_id == Group.id)
    .where(SendLog.user_id == user.id)
    .order_by(SendLog.sent_at.desc())
    .limit(10)
)
recent_result = await db.execute(recent_query)
recent_sends = [
    {"id": r.id, "ad_title": r.ad_title or "—", "group_name": r.group_name or "—",
     "account_id": group.account_id if group else None, "status": r.status,
     "messenger_type": r.messenger_type, "sent_at": r.sent_at}
    for r, group in recent_result
]
```
(`account_id` выводится через `Group.account_id` — колонки в `SendLog` нет, см. `app/models/send_log.py:12-31`.)

**DASH-05 — ничего не писать.** `get_shell_context` уже отдаёт `sessions_online`/`sessions_total` (`common.py:259-271, 362-363`), шелл их рисует. Докстринг явно запрещает Docker SDK на рендере.

**Маршрут ленты и `load_shell_context`.** Все страничные роутеры включены в `pages_router` с зависимостью на каждый маршрут (`app/pages/__init__.py:41`):
```python
router = APIRouter(dependencies=[Depends(load_shell_context)])
```
Вариант (б) из RESEARCH §Pitfall 4 — отдельный роутер, включённый в `app/main.py:79-86` рядом с `app.include_router(history_router)`, минуя `pages_router`.

---

### `app/pages/history.py` — `GET /history/export` (controller, streaming file-I/O)

**Analog по фильтрам/владению:** `history_list` (см. выше). **Аналога стриминга в проекте нет** — см. §No Analog Found.

**Порядок объявления** — образец уже в файле: `/history/partial` объявлен на строке 62, `/history/{log_id}` — на 125. `export` встаёт выше `{log_id}` по той же причине.

**Пробрасывание фильтров в URL** (`history/list.html:49`) — экспорт-ссылка строится тем же циклом:
```jinja
{% for k, v in (filter_params|default({})).items() %}&{{ k }}={{ v|string|urlencode }}{% endfor %}
```

---

### `app/pages/history.py` — `POST /history/{log_id}/retry` (controller, command → queue)

**Analog:** `app/pages/accounts.py:715-741` (`retry-sync`) и `_claim_sync_slot:747-771`

**Постановка задачи — единственная форма в проекте** (`accounts.py:736-738`), импорт ЛОКАЛЬНЫЙ (это то, что позволяет подменить его в тесте):
```python
# Dispatch background Celery task to poll bridge and save groups
from app.worker.celery_app import celery
task_name = "app.worker.tasks.sync_max_groups" if account.type == "max" else "app.worker.tasks.sync_wa_groups"
celery.send_task(task_name, args=[account.id])

# Повторный запуск нажимают с экрана групп аккаунта — туда же и возвращаем.
return RedirectResponse(url=f"/accounts/{account_id}/groups", status_code=302)
```

**Гард двойного нажатия (Pitfall 11)** — `accounts.py:747-771`:
```python
_SYNC_IN_FLIGHT: set[int] = set()

def _claim_sync_slot(account_id: int) -> bool:
    """Занимает заявку ... Функция СИНХРОННАЯ и не содержит ни одного `await`
    намеренно: между проверкой и добавлением не должно быть точки переключения
    задач, иначе гонка вернётся ровно туда, откуда её убирают."""
    if account_id in _SYNC_IN_FLIGHT:
        return False
    _SYNC_IN_FLIGHT.add(account_id)
    return True

def _release_sync_slot(account_id: int) -> None:
    _SYNC_IN_FLIGHT.discard(account_id)   # discard, а не remove
```
Ключ для повтора — `log_id`; освобождение — в `finally`.

**Владение на входе** (`history.py:136-138`):
```python
log = await db.get(SendLog, log_id)
if not log or log.user_id != user.id:
    return RedirectResponse(url="/history", status_code=302)
```

---

### `app/worker/tasks.py` — `retry_send` (worker task, event-driven)

**Analog:** `app/worker/tasks.py:243-265` (`check_schedules`) — форма таска копируется целиком:
```python
@shared_task(name="app.worker.tasks.check_schedules", bind=True)
def check_schedules(self):
    settings = get_settings()
    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    async def _run():
        try:
            logger.info("celery_task_start", task_name=self.name, task_id=self.request.id)
            async with session_factory() as session:
                await check_schedules_async(session)
        except Exception as e:
            logger.error("check_schedules_error", error=str(e), exc_info=True)
            raise
        finally:
            await engine.dispose()

    asyncio.run(_run())
```

**Точка вливания — `dispatch_send_tasks`, а не `send_telegram_message`** (`tasks.py:50-75`):
```python
async def dispatch_send_tasks(tasks_to_dispatch: list[DispatchTask]) -> None:
    """Dispatch tasks: Telegram to Celery queue, WhatsApp to Redis per-account queues."""
    import json
    import redis as redis_lib
    from uuid import uuid4
    settings = get_settings()
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
WA/MAX уходят `rpush`-ем полного payload в `wa:queue:{account_id}` / `max:queue:{account_id}` (`tasks.py:93-108`, `132-147`) — формат менять нельзя, его читает `wa_worker/`. Redis-клиент **синхронный** (`tasks.py:79,118`) → вызывать только из воркера.

---

### `app/worker/tasks.py` / `use_cases.py` — `build_dispatch_task` (utility, transform)

**Analog (код, который выносится):** `app/application/scheduling/use_cases.py:179-202`
```python
task = DispatchTask(
    type=account.type,
    ad_id=schedule.ad_id,
    group_id=group_id,
    account_id=schedule.account_id,
    schedule_id=schedule.id,
)
# Populate WA-specific fields for Redis per-account queues.
if account.type in ("wa", "max"):
    task.user_id = ad.user_id
    task.ad_text = ad.text
    task.ad_title = ad.title
    if ad.images:
        from app.services.s3 import get_image_url
        from app.config import get_settings
        s3_public_url = get_settings().s3_public_url
        task.ad_images = [get_image_url(img, s3_public_url) for img in ad.images]
    else:
        task.ad_images = ad.images
    task.group_external_id = group.group_external_id
    task.group_name = group.name
```
**Analog (прецедент и обоснование выноса):** `group_resync.py:1-11` («однажды поправят две из трёх») и `tasks.py:268-276` — комментарий «ОДНА реализация на два канала».

---

### `app/templates/dashboard.html` + `dashboard/includes/*.html` (templates, render)

**Analog структуры страницы:** `app/templates/history/list.html:1-14`
```jinja
{% extends "base.html" %}
{% from "components/button.html" import button, link_button %}
{% from "components/empty_state.html" import empty_state %}
{% from "components/field.html" import select_field %}
{% from "components/filters.html" import filters %}
{% from "history/includes/history_card.html" import history_card %}

{% block title %}История — Broadcaster{% endblock %}

{# Контракт «страница → шелл» (План 01): заголовок раздела рендерит шапка
   шелла, собственного заголовка у страницы нет — он бы задвоился. #}
{% block page_title %}История отправок{% endblock %}

{% block content %}
```

**Analog плитки метрики** (текущий `dashboard.html:22-30`) — обёртка `data-metrics` сохраняется, содержимое плитки уезжает в макрос + дельта:
```jinja
<div data-metrics>
  {{ card_open() }}
    {{ mono('Объявления', 'muted', upper=true) }}
    <span data-metric-value>{{ stats.active_ads }}</span>
  {{ card_close() }}
```

**Analog макроса-строки** (`history/includes/history_card.html:25-49`) — докстринг «почему макрос, а не include», параметры явные, глобалы форматирования:
```jinja
{% from "components/badge.html" import badge %}
{% from "components/mono.html" import mono %}
{% from "includes/messenger_icon.html" import messenger_icon %}

{% macro history_card(log, user=None, detail_base_path='/history') -%}
<article data-hrow{% if log.status %} data-status="{{ log.status }}"{% endif %} id="history-row-{{ log.id }}">
  <div data-area="head">
    {%- if log.messenger_type in ('tg_user', 'wa', 'max') -%}
      {{ messenger_icon(log.messenger_type, size='', show_label=false) }}
    {%- endif -%}
    {{- mono(format_datetime_for_user(log.sent_at, user, '%d.%m %H:%M'), 'bright') -}}
    {%- if log.status == 'ok' -%}{{ badge('OK', 'success') }}
    {%- elif log.status == 'fail' -%}{{ badge('Ошибка', 'danger') }}
    {%- elif log.status == 'account_disconnected' -%}{{ badge('Отключён', 'warning') }}
    {%- else -%}{{ badge(log.status, 'neutral') }}{%- endif -%}
```
→ `feed_row` копирует: `data-status` на корне, `mono(...)` для времени, `time_ago_for_user(row.sent_at, user)` как глобал, ссылка на `/history/{{ row.id }}`.

**Блок ошибки, который правит D-32/D-33** (`history_card.html:51-56`):
```jinja
{%- if log.error_message %}
<div data-area="err">
  {{- mono('Текст ошибки', 'danger', upper=true) -}}
  <span data-longtext="mono">{{ log.error_message }}</span>
</div>
{%- endif %}
```

**Analog паршала опроса** (`history/partial_cards.html:1-7`) — паршал не расширяет шелл, имя содержит `partial`:
```jinja
{# Следующая порция записей истории. Сентинел ИДЕНТИЧЕН сентинелу list.html:
   правится один — синхронно правится второй. #}
{% from "history/includes/history_card.html" import history_card %}
{% for log in logs %}{{ history_card(log, user, detail_base_path|default('/history')) }}{% endfor %}
```

**Analog атрибутов опроса** (`accounts/partials/sync_status_card.html:46`) — **важно:** здесь опрос самоостанавливающийся через `outerHTML` + условные атрибуты; Фаза 4 берёт `hx-trigger="every Ns"` **без** условия и на стабильном контейнере (`innerHTML`, D-07):
```jinja
<div data-row id="account-row-{{ account_id }}"{% if status == 'syncing' %} hx-get="/accounts/{{ account_id }}/sync-status" hx-trigger="every 5s" hx-swap="outerHTML"{% endif %} style="--cols: {{ ACCOUNT_COLS }}">
```
Докстринг того же файла (строки 1-12) — образец того, как объясняется механизм остановки; паршал ленты обязан объяснить обратное решение.

---

### `app/templates/history/list.html` — чипсы-фильтры + линейка счётчика + экспорт

**Analog обёртки фильтров** (`components/filters.html:24-34`) — остаётся для `select` аккаунта:
```jinja
{% macro filters(id, action=None, method='get', open_on_desktop=true, label='Фильтры') -%}
<section class="filters{% if not open_on_desktop %} filters--collapsed{% endif %}" id="{{ id }}"
         x-data="{ open: false }" x-bind:class="open ? 'filters--open' : ''">
```
Текущее применение (`list.html:20-35`) — `select_field` × 4 + `button('Применить')` + `link_button('Сбросить', '/history')`. Статус/канал/период переезжают в чипсы-ссылки.

**Analog чипса — CSS-примитив, макроса нет** (`app.css:1378-1405`):
```css
.chip-set { display: flex; flex-wrap: wrap; gap: 8px; min-width: 0; }
.chip {
  position: relative;
  display: inline-flex; align-items: center; justify-content: center; gap: 4px;
  min-width: 0; max-width: 100%; height: 44px; padding: 0 12px;
  border-radius: var(--r-lg);
  background: var(--surface-input); border: 1px solid var(--border-input);
  color: var(--text-secondary); font-size: var(--fs-lg);
}
.chip:has(.chip__input:checked), .chip--on {
  color: var(--text); border-color: var(--accent);
  background: color-mix(in oklab, var(--accent) 14%, transparent);
}
```
Существующие потребители — `ads/includes/sched_card.html`, `schedules/includes/schedule_row.html:110` (`.chip--on` без input). Чипсы-ссылки истории — `<a class="chip {% if active %}chip--on{% endif %}" href="/history?...">`.

**Analog сетки для heatmap** (`app.css:1407-1412`) — `.day-grid` уже задаёт форму «7 ячеек фиксированного размера, переносящихся»; heatmap 7×24 — CSS Grid по тому же принципу, **не `<table>`**.

**Analog пустого состояния** (`components/empty_state.html:4-9`) — `action_label`/`action_href` закрывают D-40:
```jinja
{% macro empty_state(title, hint=None, action_label=None, action_href=None) -%}
<div class="empty">
  <span class="empty__title">{{ title }}</span>
  {%- if hint %}<span class="empty__hint">{{ hint }}</span>{% endif -%}
  {%- if action_label and action_href %}<a class="btn btn--primary empty__action" href="{{ action_href }}">...{% endif -%}
</div>
```
Текущее применение — `list.html:53-54`.

---

### `alembic/versions/0016_send_logs_user_sent_at.py` (migration, DDL)

**Analog:** `alembic/versions/0015_groups_unique_account_external.py` — докстринг ревизии обязан назвать размен по блокировкам (строки 44-55 и 80-87 там же: «Тестовая суита идёт по SQLite и оба этих дефекта пропускает, а боевая база — PostgreSQL»).
`revision = "0016"`, `down_revision = "0015"`, имя индекса по конвенции `ix_send_logs_user_id_sent_at`. Текущие индексы (`app/models/send_log.py:13,25,30`): `user_id`, `task_id`, `sent_at` — по отдельности; составного нет.

### `tests/test_migrations/test_0016_send_logs_user_sent_at.py` (test)

**Analog:** `tests/test_migrations/test_0013_ad_status.py` — единственный миграционный тест в проекте, копируется целиком.

**Фикстура** (`:77-102`):
```python
@pytest.fixture
def db_at_0012(tmp_path: Path, monkeypatch) -> tuple[Config, Path]:
    """База со схемой ревизии 0012, одной строкой и штампом 0012."""
    db_path = tmp_path / "migration.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(ADS_TABLE_AT_0012)
        conn.execute("INSERT INTO ads (...) VALUES (...)")
        conn.commit()
    finally:
        conn.close()

    url = f"sqlite+aiosqlite:///{db_path}"
    # env.py предпочитает DATABASE_URL любому значению из alembic.ini.
    monkeypatch.setenv("DATABASE_URL", url)

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("sqlalchemy.url", url)
    command.stamp(config, "0012")
    return config, db_path
```
**Проверка индекса** (`:136-148`) — прямой шаблон для 0016:
```python
def test_upgrade_creates_status_index(db_at_0012):
    config, db_path = db_at_0012
    command.upgrade(config, "0013")
    assert (
        _scalar(db_path,
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name='ix_ads_status'")
        == "ix_ads_status"
    )
```
Ключевые свойства (докстринг `:1-32`): файловая SQLite вместо `:memory:`, тест **синхронный** (env.py вызывает `asyncio.run`), стартовая точка ставится `command.stamp`, целевая ревизия называется по имени, а не `head`. Для 0016 стартовая точка — `0015`, фикстура сама создаёт таблицу `send_logs` в состоянии 0015.

---

## Shared Patterns

### Аутентификация страничного маршрута
**Source:** `app/pages/history.py:166-168`
**Apply to:** все новые маршруты — `/dashboard`, `/dashboard/feed`, `/history/export`, `POST /history/{id}/retry`
```python
user = await get_user_from_cookie(request, db, settings)
if not user:
    return RedirectResponse(url="/login", status_code=302)
```

### Владение на каждом входе
**Source:** `app/pages/history.py:136-138`
**Apply to:** retry, export, detail, feed — «клиентским данным не верят»
```python
log = await db.get(SendLog, log_id)
if not log or log.user_id != user.id:
    return RedirectResponse(url="/history", status_code=302)
```

### PRG и редирект-ответ на команду
**Source:** `app/pages/accounts.py:741`
**Apply to:** `POST /history/{id}/retry`, отказ экспорта по потолку
```python
return RedirectResponse(url=f"/accounts/{account_id}/groups", status_code=302)
```

### Панель подтверждения необратимого действия
**Source:** `app/templates/components/modal.html:84,103-110`; call-site — `account_groups/includes/group_row.html:104-109`
**Apply to:** кнопка «Повторить» в карточке истории (D-23)
```jinja
{% macro modal(id, title, action, confirm_label, body=None, cancel_label="Отмена", confirm_variant="danger", method="post") -%}
...
<form class="modal__form" method="{{ method }}" action="{{ action }}"
      x-on:submit="if (sending) { $event.preventDefault(); return; } sending = true">
  {%- if body %}<p class="modal__text">{{ body }}</p>{% endif %}
  <div class="modal__actions">
    <button class="btn btn--ghost" type="button" x-ref="cancel" x-on:click="hide()">...</button>
    <button class="btn btn--{{ confirm_variant }}" type="submit" x-bind:disabled="sending" x-bind:aria-busy="sending">...</button>
  </div>
</form>
```
Call-site:
```jinja
{{ modal(id='group-del-' ~ group.id,
         title='Удалить группу?',
         action='/accounts/' ~ account_id ~ '/groups/' ~ group.id ~ '/delete',
         confirm_label='Удалить',
         method="post",
         body=group.name ~ ' — группа исчезнет из всех расписаний; ...') }}
```
Форма-триггер рядом с кнопкой (`sync_status_card.html:74`):
```jinja
<form method="POST" action="/accounts/{{ account_id }}/delete" x-data x-on:submit.prevent="$dispatch('modal-open-acc-del-{{ account_id }}')">
  {{- button('Удалить', variant='ghost', icon='trash', title='Удалить аккаунт') -}}
</form>
```
⚠️ Гард `sending` — клиентский; серверная защита — `_claim_sync_slot`-подобная заявка (см. выше). Панель эмитится **вне** заменяемого HTMX-элемента (`sync_status_card.html:18-28`).

### Форматирование дат и склонений (глобалы Jinja)
**Source:** `app/pages/common.py:152-233`
**Apply to:** лента, плитки, ближайшие отправки, карточка истории, экспорт
- `format_datetime_for_user(value, user, fmt)` — нормализует naive→UTC, переводит в зону пользователя
- `time_ago_for_user(value, user)` — «N назад», «только что» для будущего, пустая строка для `None`
- `plural_ru(count, one, few, many)` — «N групп»
- `_get_timezone_for_user(user)` — `ZoneInfo` или UTC (нужен heatmap и фильтру `today`)

### Постановка Celery-задачи из страничного слоя
**Source:** `app/pages/accounts.py:736-738` — локальный импорт обязателен (тест подменяет `sys.modules`)
```python
from app.worker.celery_app import celery
celery.send_task(task_name, args=[account.id])
```

### Проброс фильтров через URL
**Source:** `app/templates/history/list.html:49` и `partial_cards.html:6` (разметка ИДЕНТИЧНА в обоих файлах)
```jinja
{% for k, v in (filter_params|default({})).items() %}&{{ k }}={{ v|string|urlencode }}{% endfor %}
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `app/pages/history.py` → `GET /history/export` (тело генератора) | controller | streaming file-I/O | В проекте нет ни одного `StreamingResponse` и ни одного вызова `session.stream(...)`. Планировщику брать шаблон из RESEARCH §Pattern 7; несущее ограничение `fastapi>=0.129.0` (`pyproject.toml:16`) выписать в план. Тесты границу закрытия сессии не проверяют (`conftest.py:54` подменяет `get_db` на `lambda: db_session`) |
| `app/templates/dashboard/includes/heatmap.html` | template | render | Сетки 7×24 в проекте нет; ближайшее — `.day-grid`/`.chip` (`app.css:1407-1412`) как принцип «фиксированные ячейки с переносом». `<table>` запрещён `test_template_inventory` |
| Кнопка копирования диагностического блока (Alpine) | template + JS | browser | Существующих применений `navigator.clipboard` в проекте нет; `innerHTML`/`insertAdjacentHTML` — ноль по проекту. Строить узлами DOM, охранять `window.isSecureContext` (RESEARCH §Pitfall 9) |
| Модуль аналитики как таковой | service | batch aggregation | Форма модуля есть (`group_resync`, `use_cases`), но агрегирующего модуля в проекте нет. `SendLogRepository.get_stats` (`app/repositories/send_log.py:14-29`) — не аналог: два статуса из трёх, окно 30 дней, единственный потребитель — JSON `GET /api/history/stats` |

---

## Metadata

**Analog search scope:** `app/pages/`, `app/application/`, `app/worker/`, `app/models/`, `app/templates/`, `app/static/css/`, `alembic/versions/`, `tests/test_migrations/`
**Files read for excerpts:** 18
**Pattern extraction date:** 2026-08-13
