# Phase 3: Группы аккаунта - Pattern Map

**Mapped:** 2026-08-12
**Files analyzed:** 18 (new/modified)
**Analogs found:** 16 / 18

Все пути ниже — от корня репозитория `/source/broadcaster`. Номера строк — на момент маппинга.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app/pages/account_groups.py` (NEW) | page router | request-response + CRUD | `app/pages/groups.py` (весь файл) | exact |
| `app/templates/account_groups/list.html` (NEW) | template (page) | request-response | `app/templates/groups/list.html` | exact |
| `app/templates/account_groups/partial_cards.html` (NEW) | template (fragment) | request-response | `app/templates/groups/partial_cards.html` | exact |
| `app/templates/account_groups/includes/group_row.html` (NEW) | template (macro) | request-response | `app/templates/groups/includes/group_row.html` | exact |
| `app/templates/account_groups/partials/sync_result.html` (NEW) | template (polled fragment) | polling / request-response | `app/templates/accounts/partials/sync_status_card.html` | exact |
| `app/application/accounts/group_resync.py` (NEW helper, D-10/D-11) | application use case | batch / transform | `app/application/accounts/use_cases.py` + inline-синк `app/pages/accounts.py:780-803` | role-match |
| `app/models/messenger_account.py` (MOD: `last_synced_at`, `last_sync_result`) | model | — | `app/models/group.py:23-29` (nullable Text + tz DateTime) | exact |
| `app/models/group.py` (MOD: `missing_since`) | model | — | `app/models/group.py:24-26` (`error_at`) | exact |
| `alembic/versions/0014_*.py` (NEW) | migration | — | `alembic/versions/0013_ad_status.py` | exact |
| `app/application/scheduling/use_cases.py` (MOD: D-05 skip) | application use case | event-driven / batch | тот же файл, D-01 блок строки 81-104 | exact (self-analog) |
| `app/pages/accounts.py` (MOD: redirects, sync entry, entry link) | page router | request-response | тот же файл 737-804 | exact (self-analog) |
| `app/worker/tasks.py` (MOD: WA/MAX resync через хелпер) | worker task | event-driven | `_sync_wa_groups_async` 250-339 | exact (self-analog) |
| `app/pages/ads.py` (MOD: D-07 выборка групп) | page router | CRUD | тот же файл 216-226 | exact (self-analog) |
| `app/templates/ads/includes/sched_card.html` (MOD: пометка «отключена») | template (macro) | request-response | тот же файл 146-158 (group-pick) | exact (self-analog) |
| `app/pages/common.py` (MOD: удалить nav item «Группы») | config | — | `app/pages/common.py:108-117` | exact |
| `app/pages/groups.py` (DEL → redirect stub) | page router | request-response | `accounts_delete` redirect-стиль | role-match |
| `app/routes/groups.py` (DEL / trim per D-14) | API router | CRUD | — | n/a (удаление) |
| `tests/test_pages/test_account_groups.py` (NEW) | test | — | `tests/test_pages/test_schedules_list.py` | exact |
| `tests/test_application/test_collect_due_inactive_group.py` (NEW) | test | — | `tests/test_application/test_collect_due_draft.py` | exact |
| `tests/test_application/test_group_resync.py` (NEW) | test | — | `tests/test_application/test_collect_due_draft.py` (in-file engine fixture) | role-match |
| conftest-хелпер посева групп (MOD `tests/conftest.py`) | test fixture | — | `tests/conftest.py:33-46` (`db_session`) + `_seed_account` в `test_schedules_list.py` | role-match |

---

## Pattern Assignments

### `app/pages/account_groups.py` (page router, request-response + CRUD)

**Analog:** `app/pages/groups.py` (полный контракт страницы + паршала + toggle/delete)

**Imports / module preamble** (`app/pages/groups.py:1-16`):
```python
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.pages.common import check_is_admin, get_user_from_cookie, templates
from app.repositories.schedule import ScheduleRepository

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30
```
Регистрация роутера — по образцу `app/main.py:24,84` (`from app.routes.groups import router as groups_router` / `app.include_router(groups_router)`); для страниц роутеры включаются там же.

**Auth pattern — на КАЖДОМ входе** (`groups.py:135-137`, повторяется в 178-180, 235-237, 255-257):
```python
user = await get_user_from_cookie(request, db, settings)
if not user:
    return RedirectResponse(url="/login", status_code=302)
```

**Ownership двойным WHERE** — сейчас проверяется только `user_id`; фаза добавляет `account_id`. Владение аккаунтом — образец `accounts.py:748-756`:
```python
result = await db.execute(
    select(MessengerAccount).where(
        MessengerAccount.id == account_id,
        MessengerAccount.user_id == user.id,
    )
)
account = result.scalar_one_or_none()
if not account or account.type not in ("tg_user", "wa", "max"):
    return RedirectResponse(url="/groups", status_code=302)   # ← цель меняется на /accounts
```

**Query-builder + поиск** (`groups.py:107-118`) — из него переносится только ветка `search` (D-03):
```python
def _build_groups_query(Group, user_id, account_id, ...):
    q = select(Group).where(Group.user_id == user_id)
    if account_id is not None:
        q = q.where(Group.account_id == account_id)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        q = q.where(Group.name.ilike(pattern))
    return q.order_by(Group.id)
```

**Паршал прокрутки — контракт параметров и `limit+1`** (`groups.py:121-165`):
```python
@router.get("/groups/partial", response_class=HTMLResponse)
async def groups_partial(
    request: Request,
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    search: str | None = Query(None),
    # D-15: параметр компоновки принимается и игнорируется — см. app/pages/ads.py
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    ...
    result = await db.execute(q.offset(offset).limit(limit + 1))
    rows = list(result.scalars().all())
    has_next = len(rows) > limit
    groups = rows[:limit]
    return templates.TemplateResponse("groups/partial_cards.html", {
        "request": request, "user": user, "groups": groups,
        "has_next": has_next, "next_offset": offset + limit,
        "filter_params": _filter_params(...),
    })
```

**Контекст страницы** (`groups.py:203-225`) — ключи `active_page`, `is_admin`, `has_next`, `next_offset`, `filter_params`, `filter_search`. Для новой страницы `active_page` = `"accounts"` (D-02).

**Toggle / Delete — переносятся дословно, с добавлением `Group.account_id == account_id` в WHERE и новым redirect-таргетом** (`groups.py:228-267`):
```python
@router.post("/groups/{group_id}/toggle")
async def groups_toggle(...):
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.user_id == user.id)
    )
    group = result.scalar_one_or_none()
    if group:
        group.is_active = not group.is_active
        await db.commit()
    return RedirectResponse(url="/groups", status_code=302)

@router.post("/groups/{group_id}/delete")
async def groups_delete(...):
    ...
    if group:
        schedule_repo = ScheduleRepository(db)
        await schedule_repo.remove_group_ids(user.id, {group.id})   # чистка group_ids расписаний
        await db.delete(group)
        await db.commit()
    return RedirectResponse(url="/groups", status_code=302)
```

**Счётчик «в N расписаниях» (D-08)** — переносится из `_get_group_stats` (`groups.py:50-56`), остальную статистику (SendLog) НЕ переносить (Deferred):
```python
sched_r = await db.execute(select(Schedule.group_ids))
sched_counts: dict[int, int] = {gid: 0 for gid in group_ids}
for row in sched_r:
    for gid in row.group_ids or []:
        if gid in sched_counts:
            sched_counts[gid] += 1
```
⚠ Аналог не фильтрует расписания по владельцу — на новом экране добавить join/фильтр по пользователю (правило Фазы 2).

**Счётчики «N активных из M» (D-04)** — аналога нет; два скалярных COUNT в обработчике страницы, `func` уже импортирован (`groups.py:3`). Паршал их не трогает.

**Репозиторий вместо ad-hoc select (опция):** `app/repositories/group.py:11-27` уже даёт `list_by_account(account_id, user_id)` и `get_external_ids(account_id, user_id)` — готовые скоуп-по-аккаунту запросы.

---

### `app/templates/account_groups/list.html` (template, page)

**Analog:** `app/templates/groups/list.html`

**Imports + shell-контракт** (`groups/list.html:1-24`):
```jinja
{% extends "base.html" %}
{% from "components/button.html" import button, link_button %}
{% from "components/card.html" import card_open, card_close %}
{% from "components/empty_state.html" import empty_state %}
{% from "components/field.html" import field %}
{% from "components/filters.html" import filters %}
{% from "components/modal.html" import modal %}
{% from "components/toggle.html" import toggle %}

{% block title %}Группы — Broadcaster{% endblock %}
{% block page_title %}Группы{% endblock %}
{% block page_actions %}
<form method="post" action="/accounts/{{ acc.id }}/sync-groups">
  {{- button('Синхр.', variant='ghost', icon='refresh', title='...') -}}
</form>
{% endblock %}
```

**Поиск через макрос `filters`** (`groups/list.html:34-47`) — из него остаётся ОДНО поле + две кнопки (D-03):
```jinja
{% call filters('groups-filters', action='/groups') %}
  {{ field(name="search", label='Поиск', value=filter_search or '', placeholder='Название группы', id='filter-search') }}
  {{ button('Применить', variant='primary') }}
  {{ link_button('Сбросить', '/groups', variant='ghost') }}
{% endcall %}
```

**Сентинел бесконечной прокрутки + проброс фильтров** (`groups/list.html:89-99`) — инварианты в комментарии обязаны переехать вместе с кодом:
```jinja
{# Инварианты бесконечной прокрутки:
   - сентинел остаётся ПОСЛЕДНИМ элементом внутри ТОГО ЖЕ контейнера, что и строки;
   - разметка сентинела здесь и в partial_cards.html ИДЕНТИЧНА;
   - цикл проброса фильтров переносится ДОСЛОВНО с приведением к строке и urlencode (T-04-01). #}
{% for group in groups %}{{ group_row(group, ...) }}{% endfor %}
{% if has_next %}
<div hx-get="/groups/partial?offset={{ next_offset }}&limit=30{% for k, v in (filter_params|default({})).items() %}&{{ k }}={{ v|string|urlencode }}{% endfor %}" hx-trigger="revealed" hx-swap="outerHTML" class="empty__hint">Загрузка...</div>
{% endif %}
```

**Пустое состояние** (`groups/list.html:101-104`) — макрос `empty_state(title, hint=None, action_label=None, action_href=None)`:
```jinja
{{ empty_state('Нет групп', hint='Группы синхронизируются из подключённых аккаунтов мессенджеров') }}
```

**Anti-pattern из аналога — НЕ переносить:** блок bulk-действий и `<script>` (`groups/list.html:54-85, 106-152`) — bulk снят (D-03).

---

### `app/templates/account_groups/includes/group_row.html` (template macro)

**Analog:** `app/templates/groups/includes/group_row.html`

**Макросная форма и контракт параметров** (строки 1-31): импортируемый шаблон не видит контекста вызывающего — все данные приходят параметрами; `GROUP_COLS`/`GROUP_COLUMNS` — единственный источник раскладки. ⚠ Новый экран — карточные строки, а не `data-row`-таблица (UI-SPEC responsive), поэтому `row_open/cell/rowhead` заменяются собственной разметкой секции CSS; сам приём «строка живёт в макросе, имена — явные параметры» сохраняется.

**Тумблер в POST-форме (D-08)** (строки 61-69) — переносится с заменой маршрута:
```jinja
{#- Событие change всплывает от чекбокса к форме, поэтому обработчик висит на
    форме, а макрос toggle остаётся без собственных атрибутов событий. -#}
<form method="post" action="/groups/{{ group.id }}/toggle" x-data x-on:change="$el.submit()">
  {{- toggle(name='is_active', checked=group.is_active, id='group-toggle-' ~ group.id,
             title='Приостановить' if group.is_active else 'Возобновить') -}}
</form>
```

**Удаление: форма-триггер + перехват на самой форме (деградация без Alpine)** (строки 70-76):
```jinja
{#- Перехват отправки навешен на САМУ форму, а не заменил её кнопкой-триггером
    вне формы: без Alpine перехват не навешивается, и форма уходит POST-ом
    на прежний маршрут (WR-04, T-12-04). -#}
<form method="post" action="/groups/{{ group.id }}/delete"
      x-data x-on:submit.prevent="$dispatch('modal-open-group-del-{{ group.id }}')">
  {{- button('Удалить', variant='ghost', icon='trash', title='Удалить группу') -}}
</form>
```

**Панель подтверждения — РЯДОМ со строкой, вне неё** (строки 79-93):
```jinja
{{ modal(id='group-del-' ~ group.id,
         title='Удалить группу?',
         action='/groups/' ~ group.id ~ '/delete',
         confirm_label='Удалить',
         method="post",
         body=group.name) }}
```
Сигнатура: `modal(id, title, action, confirm_label, body=None, cancel_label="Отмена", confirm_variant="danger", method="post")` (`components/modal.html:49`).

**Экранирование недоверенного имени** (строки 11-14, 36-38): `<span data-grow>{{ group.name }}</span>` — обычный вывод, готовая разметка макросам не передаётся.

**Прочие сигнатуры макросов, нужные строке (проверены):**
`avatar(name, size=30, title=None)`, `toggle(name, checked, label, value, disabled, id, title)`, `mono(text, variant='muted', upper=false, title=None)`, `badge(...)`, `button(label, variant, type, name, value, icon, disabled, title, extra_class)`, `link_button(label, href, ...)`, `btn_icon(name)`, `alert(message, variant='error')`, `empty_state(title, hint, action_label, action_href)`, `filters(id, action=None, method='get', open_on_desktop=true, label='Фильтры')`.

---

### `app/templates/account_groups/partials/sync_result.html` (polled fragment)

**Analog:** `app/templates/accounts/partials/sync_status_card.html`

**Самоостанавливающийся опрос — условие ВНУТРИ открывающего тега** (строка 46):
```jinja
<div data-row id="account-row-{{ account_id }}"{% if status == 'syncing' %} hx-get="/accounts/{{ account_id }}/sync-status" hx-trigger="every 5s" hx-swap="outerHTML"{% endif %} style="--cols: {{ ACCOUNT_COLS }}">
```

**Комментарий-инвариант, который обязан переехать** (строки 1-13):
```jinja
{# МЕХАНИЗМ ОСТАНОВКИ ОПРОСА. Команды «стоп» у опроса нет: он прекращается тем,
   что очередной ответ приходит БЕЗ атрибутов запроса и триггера — они обёрнуты
   условием по статусу прямо в открывающем теге ниже. ... (T-06-01).
   Парные тесты test_sync_polling_stops и test_sync_polling_continues_while_syncing
   в tests/test_pages/test_htmx_preserved.py — спецификация этого файла. #}
```

**Правило «панель/плашка вне подменяемого элемента»** (строки 18-28) — прямой источник Pitfall 8: этот файл НЕ эмитит модалку, её эмитят `list.html`/`partial_cards.html`; закреплено `test_accounts_three_files_dispatch_same_modal_event`.

**Ветвление по статусу** (строки 51/69/85): `'active'` / `'sync_failed'` / `'syncing'` — тот же словарь для нового блока.

**Серверный рендер паршала опроса из обработчика** (`app/pages/accounts.py:661-693`):
```python
@router.get("/accounts/{account_id}/sync-status", response_class=HTMLResponse)
async def accounts_sync_status(request, account_id, layout: str | None = Query(None), db=..., settings=...):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return _connect_status("notice", "Не авторизован")
    view = await get_sync_status_view(db, user.id, account_id)   # application-слой
    if view is None:
        return _connect_status("notice", "Аккаунт не найден")
    if view.status in ("active", "sync_failed", "syncing"):
        html = templates.env.get_template("accounts/partials/sync_status_card.html").render(
            account_id=account_id, status=view.status, ...)
        return HTMLResponse(html)
    return HTMLResponse("")
```

---

### `app/application/accounts/group_resync.py` (application use case, переинвентаризация)

**Analogs:** `app/pages/accounts.py:780-803` (TG only-add), `app/worker/tasks.py:278-304` (WA), стиль модуля — `app/application/accounts/use_cases.py:1-40`.

**Стиль модуля application-слоя** (`use_cases.py:1-14`):
```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.application.accounts.dto import AccountInfo, SyncStatusView
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
```
DTO для результата синка кладутся рядом, в `app/application/accounts/dto.py` (там уже живут `AccountInfo`, `SyncStatusView`).

**Текущий only-add, который хелпер заменяет** (`accounts.py:780-803`, посимвольный близнец — `tasks.py:278-304`):
```python
existing = await db.execute(
    select(Group.group_external_id).where(
        Group.account_id == account_id,
        Group.user_id == user.id,
    )
)
existing_ids = {row[0] for row in existing}
seen = set(existing_ids)
for g in fetched_groups:
    if g["id"] not in seen:
        seen.add(g["id"])
        db.add(Group(user_id=user.id, account_id=account_id,
                     messenger_type=messenger_type,
                     group_external_id=g["id"], name=g.get("name") or g["id"]))
await db.commit()
```
Три копии (TG в `accounts.py`, WA в `tasks.py:278-304`, MAX в `tasks.py:~380-403`) — в одну функцию `(session, account, fetched) -> counters` (Pitfall 3).

**Готовый запрос существующих внешних id** — `app/repositories/group.py:20-27` `get_external_ids(account_id, user_id)`.

**Логирование результата в воркере** (`tasks.py:252, 304`):
```python
log = logger.bind(account_id=account_id)
log.info("sync_complete", total_groups=len(groups), new_groups=new_count)
```

**Guard повторного запуска и переходы статуса** (`tasks.py:273-276, 302, 310-312`):
```python
account = await session.get(MessengerAccount, account_id)
if not account or account.status != "syncing":
    log.info("sync_skipped", reason="account_not_syncing", status=account.status if account else None)
    return
...
account.status = "active"      # успех
account.status = "sync_failed" # ошибка/таймаут
```

---

### `app/models/messenger_account.py` + `app/models/group.py` (models)

**Analog:** `app/models/group.py:22-29` — форма nullable-колонок с tz-aware datetime:
```python
is_active: Mapped[bool] = mapped_column(Boolean, default=True)
last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```
Новые колонки идут ровно этой формой: `messenger_accounts.last_synced_at: Mapped[datetime | None]`, `messenger_accounts.last_sync_result: Mapped[str | None] = mapped_column(Text, nullable=True)`, `groups.missing_since: Mapped[datetime | None]`.
⚠ `last_error`/`error_at` — про ошибки ОТПРАВКИ (`scheduling/use_cases.py:305-306`), под D-11 не переиспользовать.
`MessengerAccount` (`messenger_account.py:9-22`) — ORM-relationship'ов не объявляет; связь Group→account держится голым `ForeignKey`. Новых relationship не заводить.

---

### `alembic/versions/0014_*.py` (migration)

**Analog:** `alembic/versions/0013_ad_status.py` (head)

**Шапка ревизии — docstring с обоснованием + плоские `revision`/`down_revision`** (строки 1-25):
```python
"""ads.status вместо ads.is_active
...
Revision ID: 0013
Revises: 0012
"""
from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"

# Литералы выписаны здесь, а не импортированы из app.constants: ревизия обязана
# описывать схему на СВОЙ момент времени.
```
Для 0014: `revision = "0014"`, `down_revision = "0013"`.

**Тело — `op.add_column` / симметричный `downgrade`** (строки 27-58):
```python
def upgrade():
    op.add_column("ads", sa.Column("status", sa.String(20), server_default=..., nullable=False))
    op.create_index("ix_ads_status", "ads", ["status"])

def downgrade():
    op.drop_index("ix_ads_status", table_name="ads")
    op.drop_column("ads", "status")
```
⚠ Отличие для 0014 (Pitfall 2): только **additive nullable**, без `server_default` NOT NULL и без data-migration — прод на 0012, прыжок 0012→0014 обязан быть безопасным.

---

### `app/application/scheduling/use_cases.py` (MOD — D-05 skip)

**Analog (self):** блок D-01 в том же файле, строки 81-104 — эталон стиля комментария «почему условие стоит именно здесь»:
```python
# D-01: расписание объявления-черновика к отправке не выбирается.
#
# Условие стоит В ЭТОЙ ВЕТКЕ, а не в WHERE запроса выше, и это не
# стилистический выбор. Фильтр в WHERE тоже не создал бы задачи, но
# оставил бы next_run_at в прошлом — ... (T-02-12).
if (not ad or not account or account.status != "active"
        or effective_ad_status(ad) == AD_STATUS_DRAFT):
    schedule.next_run_at = compute_next_run_at(...)
    continue
```

**Точка врезки D-05 — per-group цикл** (строки 120-144, verbatim начало):
```python
for group_id in schedule.group_ids or []:
    task = DispatchTask(
        type=account.type, ad_id=schedule.ad_id, group_id=group_id,
        account_id=schedule.account_id, schedule_id=schedule.id,
    )
    # Populate WA-specific fields for Redis per-account queues
    if account.type in ("wa", "max"):
        group = await session.get(Group, group_id)
        if group:
            ...
    tasks_to_dispatch.append(task)
```
Врезка ставится ПЕРЕД созданием `DispatchTask`; `session.get(Group, group_id)` поднимается выше ветвления (для WA/MAX повторный `get` бесплатен — identity map). Без `SendLog` (D-06), след — `logger.info(...)` в стиле `tasks.py:29` (`logger = structlog.get_logger(__name__)`).

---

### `app/pages/ads.py` + `app/templates/ads/includes/sched_card.html` (MOD — D-07)

**Выборка групп редактора** (`ads.py:216-226`, verbatim):
```python
groups = list((await db.execute(
    select(Group)
    .where(Group.user_id == user.id, Group.is_active == True)  # noqa: E712
    .order_by(Group.id)
)).scalars().all())
```
Меняется на «активные + неактивные, чьи id входят в `group_ids` расписаний этого объявления».

**Разметка выбора групп** (`sched_card.html:146-158`) — сюда добавляется mono-пометка «отключена»:
```jinja
<span class="field__label">ГРУППЫ · выбрано {{ chosen | length }} из {{ account_groups | length }}</span>
...
<div class="group-pick">
  {%- for group in account_groups %}
  <label class="group-pick__row" title="{{ group.name }}">
    <input class="group-pick__box" type="checkbox" name="group_ids" value="{{ group.id }}"
           {% if group.id in chosen %}checked{% endif %}>
    <span class="group-pick__name">{{ group.name }}</span>
    <span class="group-pick__count">{{ group.group_external_id }}</span>
  </label>
  {%- endfor %}
</div>
```
Фильтр по аккаунту и `chosen` (строки 63, 66):
```jinja
{%- set account_groups = groups | selectattr('account_id', 'equalto', s.account_id) | list if s.account_id else [] -%}
{%- set chosen = s.group_ids or [] -%}
```

---

### `app/pages/accounts.py` (MOD — redirects, вход синка, ссылка «Настроить группы»)

**Целевые строки redirect'ов** (`accounts.py:734, 756, 759, 804`) — все `RedirectResponse(url="/groups", status_code=302)` → `/accounts/{account_id}/groups`.

**Guard повторного синка** (`accounts.py:758-759`) — переносится на новый вход:
```python
if account.status == "syncing":
    return RedirectResponse(url="/groups", status_code=302)
```

**Постановка фоновой таски** (`accounts.py:726-732`):
```python
account.status = "syncing"
await db.commit()
from app.worker.celery_app import celery
task_name = "app.worker.tasks.sync_max_groups" if account.type == "max" else "app.worker.tasks.sync_wa_groups"
celery.send_task(task_name, args=[account.id])
```

**Ссылка входа на строке аккаунта** (`accounts/list.html:58, 72, 134`) — три синхронизируемые копии разметки строки (list.html, includes/partial_cards.html, partials/sync_status_card.html); образец действия внутри строки:
```jinja
<form method="POST" action="/accounts/{{ account.id }}/delete" x-data x-on:submit.prevent="$dispatch('modal-open-acc-del-{{ account.id }}')">
```
Новая ссылка «Настроить группы» — `link_button('Настроить группы', '/accounts/' ~ account.id ~ '/groups', variant='ghost')` в тех же трёх файлах.

---

### `app/pages/common.py` (MOD — навигация)

**Строка на удаление** (`common.py:111`):
```python
{"key": "groups", "label": "Группы", "href": "/groups", "count_key": None},
```
Счётчика у пункта нет (`count_key: None`) — правка ровно в одну строку списка `NAV_ITEMS` (108-117).

**Формат времени для шапки «N назад»** (`common.py:149-165`) — глобал `format_datetime_for_user(value, user, fmt)`, зарегистрирован в `templates.env.globals`; таймзона пользователя решена (`_get_timezone_for_user`, 137-146).

---

### `app/routes/groups.py` (DEL per D-14)

**Файл целиком** (87 строк) — четыре входа `/api/groups`: `create_group` (31-45, без проверки владения `account_id` — дыра CR-01), `list_groups` (48-55), `delete_group` (58-71), `toggle_group` (74-86). Регистрация — `app/main.py:24, 84`. `delete_group` уже вызывает `ScheduleRepository.remove_group_ids` — поведение, которое обязано остаться в страничном `delete`.

---

### `tests/test_pages/test_account_groups.py` (test)

**Analog:** `tests/test_pages/test_schedules_list.py`

**Docstring-контракт файла** (строки 1-17) — тест начинается объяснением, ЧТО именно закрепляется каждым слоем.

**Импорты и фикстурная база** (строки 19-35):
```python
import pytest
from httpx import AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.user import User
```

**Посев через ORM (образец замены `POST /api/groups`, Pitfall 1)** (строки 52-70):
```python
async def _user(db: AsyncSession) -> User:
    return (await db.execute(select(User).where(User.email == "testuser@test.com"))).scalar_one()

async def _seed_account(db: AsyncSession, type_: str = "wa") -> MessengerAccount:
    user = await _user(db)
    ...
```
Фикстуры conftest: `db_session` (`tests/conftest.py:33-46`, in-memory SQLite + `Base.metadata.create_all`), `client` (48-56, `ASGITransport` + `dependency_overrides`), `auth_headers` (58-70), `authed_client` (72+, cookie — страничные маршруты читают КУКУ, не Bearer).

**Проверка HTMX-инвариантов** — `tests/test_pages/test_htmx_preserved.py` (`_sentinel_offset()` :140, `test_infinite_scroll_chain` :158, `test_sync_polling_stops` / `test_sync_polling_continues_while_syncing`) — новый экран добавляется в те же цепочки.

---

### `tests/test_application/test_collect_due_inactive_group.py` (test)

**Analog:** `tests/test_application/test_collect_due_draft.py`

**Докстринг задаёт «ключевое утверждение файла»** (строки 1-15) — для D-05 ключевое утверждение симметрично: задача не создана, а `next_run_at` расписания продолжает двигаться.

**Локальный движок + хелперы** (строки 17-46):
```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.application.scheduling.use_cases import collect_due_schedules
from app.database import Base
from app.models.group import Group
...
ALL_DAYS = [0, 1, 2, 3, 4, 5, 6]
TWO_TIMES = ["00:30", "12:30"]

async def _allow_everything(session, user_id: int, action: str):
    return True, "ok"

def _as_utc(value: datetime) -> datetime:
    """SQLite не хранит смещение — восстанавливаем UTC для сравнения."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
```

**Посев одного просроченного расписания** (строки 48-60+):
```python
user = User(email="draft@test.com", password_hash="x", name="U")
session.add(user); await session.commit()
ad = Ad(user_id=user.id, title="T", text="Body", images=[], status=ad_status)
account = MessengerAccount(user_id=user.id, type="tg_user", credentials="sess", status="active")
session.add_all([ad, account]); await session.commit()
```

---

## Shared Patterns

### Authentication + ownership (применять ко ВСЕМ новым входам: страница, паршал, toggle, delete, sync)
**Source:** `app/pages/groups.py:135-137` (auth) + `app/pages/accounts.py:748-756` (владение аккаунтом)
```python
user = await get_user_from_cookie(request, db, settings)
if not user:
    return RedirectResponse(url="/login", status_code=302)

result = await db.execute(
    select(MessengerAccount).where(
        MessengerAccount.id == account_id,
        MessengerAccount.user_id == user.id,
    )
)
account = result.scalar_one_or_none()
```
Групповые запросы — двойной WHERE: `Group.user_id == user.id, Group.account_id == account_id`.

### Валидация параметров паршала
**Source:** `app/pages/groups.py:124-131` — `offset: int = Query(0, ge=0)`, `limit: int = Query(PAGE_SIZE, ge=1, le=100)`, `layout` принимается и игнорируется (D-15); `search` — bind-параметр `ilike` (`groups.py:116-117`), не конкатенация.

### Redirect-after-POST (PRG)
**Source:** `app/pages/groups.py:245, 267`; `app/pages/accounts.py:734, 817` — все POST-обработчики возвращают `RedirectResponse(url=..., status_code=302)`, никакого JSON.

### Прогрессивное улучшение (базовый путь без JS)
**Source:** `groups/includes/group_row.html:61-76` — перехват висит на самой форме (`x-data x-on:change="$el.submit()"` / `x-on:submit.prevent="$dispatch(...)"`), без Alpine остаётся настоящая POST-форма. Закрепляется тестами `*_degrades_without_alpine`.

### Структурное логирование
**Source:** `app/worker/tasks.py:29, 252, 275, 304` — `logger = structlog.get_logger(__name__)`, `log = logger.bind(account_id=account_id)`, события snake_case с kwargs (`sync_complete`, `sync_skipped`). Пропуск D-05 логируется тем же стилем: `logger.info("group_skipped_inactive", group_id=..., schedule_id=...)`.

### Экранирование недоверенного ввода
**Source:** `groups/includes/group_row.html:11-14, 79-87` — имена групп приходят из мессенджера; в макросы уходит текст, не разметка; проверяется `test_no_unsafe_escaping`.

### Комментарий-инвариант рядом с хрупким местом
**Source:** `accounts/partials/sync_status_card.html:1-28`, `scheduling/use_cases.py:81-91`, `groups/list.html:89-95` — в этом репозитории комментарий, объясняющий «почему здесь и что сломается иначе», плюс ссылка на парный тест — часть паттерна, а не украшение. Переносится вместе с кодом.

---

## No Analog Found

| File / element | Role | Data Flow | Reason |
|------|------|-----------|--------|
| Счётчик «N активных из M» (два COUNT в обработчике страницы, D-04) | page router (часть `account_groups.py`) | request-response | Ни одна списочная страница не считает отдельные агрегаты вне загруженной страницы; `func` и `case` используются только в `_get_group_stats` по SendLog. Форма — из RESEARCH (Pitfall 5) |
| Русские склонения счётчиков («1 активная из 1 группы») | template filter/helper | transform | В репозитории есть только частный случай `chosen \| length ~ ' групп'` (`sched_card.html:79`) — общего хелпера склонений нет. Новый хелпер по UI-SPEC |
| Хелпер «последняя синхронизация N назад» | utility | transform | Есть только абсолютное форматирование `format_datetime_for_user` (`common.py:149-165`); относительного формата в репо нет |
| Секция CSS карточных строк экрана (`[data-acct-head]`, `.count-rule`, `[data-group-row]`, `.icon-btn`) | style | — | Списочные экраны сделаны `data-row`-сеткой (`components/table.html`); карточные строки этого экрана — новая нумерованная секция `app.css` по UI-SPEC. Ближайший стилевой прецедент — секция «Выбор групп» (`app.css:1440-1475`, строки-флажки 40px) |
| Парсинг JSON-результата синка «с защитой от мусора» | utility | transform | В репо нет прецедента чтения JSON-строки из Text-колонки (`Schedule.group_ids`/`Ad.images` — нативные JSON-колонки) |

---

## Metadata

**Analog search scope:** `app/pages/`, `app/routes/`, `app/templates/` (groups, accounts, ads, components), `app/models/`, `app/repositories/`, `app/application/`, `app/worker/`, `alembic/versions/`, `tests/`
**Files read for excerpts:** 17
**Orientation:** `graphify query` (groups/toggle/delete/sentinel subgraph) — граф помечен STALE, все цитаты перепроверены чтением файлов
**Pattern extraction date:** 2026-08-12
