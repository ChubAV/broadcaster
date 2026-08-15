# Phase 2: Объявления и расписания — Pattern Map

**Mapped:** 2026-08-10
**Files analyzed:** 21 new/modified files
**Analogs found:** 19 / 21

Source of the file list: `02-CONTEXT.md` (D-01…D-21, §Integration Points), `02-RESEARCH.md`
(§Recommended Project Structure, §Runtime State Inventory), `02-UI-SPEC.md` (§Component Inventory).

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `alembic/versions/0013_ad_status.py` | migration | batch/DDL | `alembic/versions/0012_schedules_account_id_nullable_set_null.py` (+ `0003_add_is_blocked_to_users.py` for `server_default`) | exact |
| `app/models/ad.py` | model | CRUD | itself (`app/models/schedule.py` for string-status precedent) | exact |
| `app/pages/ads.py` (`ads_new`/`ads_create`/`ads_edit`/`ads_update`) | page route | request-response + partial update | `app/pages/ads.py:163-190` (current `ads_update`) + `app/pages/schedules.py:40-78` (`schedules_partial`, HTML-fragment response) | role-match |
| `app/pages/ads.py` — autosave POST returning OOB fragment | page route | partial update → HTML fragment | `app/pages/schedules.py:40-78` `schedules_partial` (only fragment-returning route in project) | role-match |
| `app/pages/schedules.py` (delete `schedules_new`/`schedules_edit`; keep list/partial/toggle/delete) | page route | CRUD | `app/pages/schedules.py:270-324` (`schedules_update` — the ownership+group-validation shape to copy into the editor) | exact |
| `app/pages/dashboard.py:33` | page route | read | itself — mechanical `Ad.is_active` → `Ad.status` | exact |
| `app/routes/ads.py` (`AdResponse`, `UpdateAdRequest`, `CreateAdRequest`) | JSON API schema | request-response | `app/routes/schedules.py:34-58` (`ScheduleResponse` shape) | role-match |
| `app/routes/schedules.py:67-73` (account ownership, D-20) | JSON API | request-response | `app/routes/schedules.py:66-73` itself (ad ownership via `get_by_id_and_user`) | exact |
| `app/routes/uploads.py` (CR-02 magic-byte sniff) | route | file-I/O | `app/routes/uploads.py:21-38` (`safe_filename` — the Phase-1 hardening pattern in the same file) | exact |
| `app/application/scheduling/use_cases.py` (D-01 draft skip) | domain use case | batch/query | `use_cases.py:68-75` (existing skip branch) | exact |
| `app/pages/common.py` (`s3_public_url` injection, D-21) | config/template glue | — | `app/pages/common.py:102-118` (`format_datetime_for_user` — a global that takes request data as a parameter instead of reaching for `get_settings()`) | role-match |
| `app/templates/ads/form.html` (rewritten editor) | template | request-response | itself (its `<script>` contract is test-locked) + `app/templates/schedules/form.html` (form layout, deleted afterwards) | exact |
| `app/templates/ads/includes/preview.html` | template fragment | — | `app/templates/schedules/partial_cards.html` (fragment include convention) | partial |
| `app/templates/ads/includes/summary.html` | template fragment | — | same | partial |
| `app/templates/ads/includes/autosave.html` | template fragment | — | **none** — no OOB/indicator precedent exists | none |
| `app/templates/ads/includes/sched_card.html` | template macro | — | `app/templates/schedules/includes/schedule_row.html` (macro + explicit params + per-row forms + modal) | role-match |
| `app/templates/ads/includes/ad_card.html` (status cell) | template macro | — | itself, lines 43-45 | exact |
| `app/templates/schedules/list.html` + `partial_cards.html` + `includes/schedule_row.html` (card rewrite) | template triad | — | `app/templates/ads/list.html` + `ads/partial_cards.html` + `ads/includes/ad_card.html` (the Phase-1 reference migration) | exact |
| `app/static/css/app.css` section 8 | stylesheet | — | sections 1-7 of the same file | exact |
| `tests/test_pages/test_ads_editor*.py` (new render tests) | test | request-response | `tests/test_pages/test_responsive_markup.py:260-278` (`test_schedules_card_renders_data`) | exact |
| `tests/test_migrations/test_0013_ad_status.py` (new) | test | DDL | **none** — no test in the suite touches Alembic | none |

---

## Pattern Assignments

### `alembic/versions/0013_ad_status.py` (migration, DDL)

**Analog:** `alembic/versions/0012_schedules_account_id_nullable_set_null.py`

**Revision header + docstring convention** (`0012:1-13`) — description first, then blank line,
then `Revision ID` / `Revises`; ids are **zero-padded strings**:

```python
"""schedules.account_id nullable + ON DELETE SET NULL

При удалении messenger-аккаунта расписание должно сохраняться и переходить
в статус «приостановлено», а не удаляться каскадом (issue #35).

Revision ID: 0012
Revises: 0011
"""
from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
```

**Dialect guard** (`0012:35-48`) — non-PostgreSQL dialects skip the unsupported step so the
revision stays importable (tests import migrations but never run them):

```python
    # Смена правила внешнего ключа поддерживается только на PostgreSQL
    # (прод по alembic.ini). На прочих диалектах шаг пропускается, чтобы
    # миграция оставалась импортируемой и применимой.
    if bind.dialect.name == "postgresql":
        ...
```

**Lossy-downgrade warning comment** (`0012:51-55`) — required style for this project; Plan 0013's
`downgrade` loses which ad was a draft and must carry the same warning:

```python
def downgrade():
    # ВНИМАНИЕ: откат необратимо теряет данные. Расписания, отвязанные от
    # удалённого аккаунта (account_id IS NULL), невозможно снова привязать —
    # аккаунта уже не существует, поэтому такие строки удаляются, чтобы
    # восстановить ограничение NOT NULL.
```

**Backfill-by-server_default pattern** — copy from `alembic/versions/0003_add_is_blocked_to_users.py:21-24`
(quoted in RESEARCH §Pattern 1); adding a NOT NULL column to a populated table is done with
`server_default`, never a separate `UPDATE`:

```python
    op.add_column(
        "users",
        sa.Column("is_blocked", sa.Boolean(), server_default="0", nullable=False),
    )
```

> **Note for the planner:** no test in `tests/` imports or runs Alembic (verified: zero matches).
> The `0013` `downgrade` path is uncovered by construction; the plan must add its own check.

---

### `app/models/ad.py` (model, CRUD)

**Analog:** itself. Current state (verbatim, `ad.py:9-22`):

```python
class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text)
    images: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

`is_active` is line 19 — the line the migration removes. `Boolean` becomes an unused import once
it goes. Status stays a plain `String(20)` (RESEARCH Pattern 1); the project has no `sa.Enum`.

---

### `app/pages/ads.py` (page route, request-response + partial update)

**Analog for the auth + ownership + redirect skeleton:** `app/pages/ads.py:163-190` (`ads_update`, verbatim):

```python
@router.post("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_update(
    request: Request,
    ad_id: int,
    title: str = Form(...),
    text: str = Form(...),
    is_active: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)

    form_data = await request.form()
    image_list = [v for v in form_data.getlist("images") if v.strip()]
    ad.title = title
    ad.text = text
    ad.images = image_list
    ad.is_active = is_active
    await db.commit()
    return RedirectResponse(url="/ads", status_code=302)
```

Everything to keep: cookie auth → `RedirectResponse("/login")`, ownership baked into the `WHERE`
(`Ad.id == ad_id, Ad.user_id == user.id`) rather than a post-hoc check, `request.form().getlist()`
for repeated fields, `await db.commit()`, 302 on the no-JS path.
Line 134 (`ads_create`) and line 184 (here) are the two WR-01 injection points for `own_image_keys`.
Line 188 (`ad.is_active = is_active`) is what D-02/D-04 delete.

**Analog for returning an HTML fragment instead of a redirect:** `app/pages/schedules.py:40-78`
(`schedules_partial`) — the only fragment-returning page route in the project. The shape is a normal
`templates.TemplateResponse` on a partial template with `"request"` and `"user"` in the context and
**no** `active_page` key (fragments do not re-render the shell):

```python
    return templates.TemplateResponse(
        "schedules/partial_cards.html",
        {
            "request": request,
            "user": user,
            "schedules": schedules,
            "has_next": has_next,
            "next_offset": offset + limit,
        },
    )
```

Full-page responses always add `"is_admin": check_is_admin(user, settings)` and `"active_page"`
(`ads.py:92-103`) — the autosave fragment response must **not**.

**Accepted-and-ignored query param convention** (`ads.py:46-50`) — the precedent for keeping a
parameter alive after its feature is removed; reuse it if `/schedules/new` needs a soft landing:

```python
    # D-15: параметр компоновки принимается и игнорируется. Строчная вёрстка
    # удалена как недостижимая, но у пользователей есть открытые вкладки, чьи
    # сентинелы всё ещё несут этот параметр в URL — удаление его из сигнатуры
    # превратило бы их подгрузку в ошибку валидации.
    layout: str | None = Query(None),
```

**Aggregate-enrichment pattern** for the editor's summary block (`ads.py:17-38`, `_enrich_ads_with_stats`):
one grouped `select(..., func.count())` per aggregate, results folded into a dict, then assigned as
ad-hoc attributes on the ORM objects. Copy this rather than N+1 lookups when the summary needs
schedule/send counts.

---

### `app/pages/schedules.py` (page route, CRUD)

**Analog:** `app/pages/schedules.py:270-324` (`schedules_update`) — this is the exact handler the
editor's per-schedule POST (D-07) must be shaped after.

**Ownership-through-Ad join** (`schedules.py:283-290`, verbatim) — `Schedule` has no `user_id`;
every schedule query joins `Ad`:

```python
    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        return RedirectResponse(url="/schedules", status_code=302)
```

**Repeated-field form contract** (`schedules.py:292-295`, verbatim) — field names are a hard
contract with the template; the editor's schedule card must emit exactly these names:

```python
    form_data = await request.form()
    group_ids = [int(g) for g in form_data.getlist("group_ids")]
    days_of_week = [int(d) for d in form_data.getlist("days_of_week")]
    times_of_day = [t for t in form_data.getlist("times_of_day") if t]
```

> `int(...)` here raises on non-numeric input, and `compute_next_run_at` raises on non-`HH:MM`
> times (RESEARCH Pitfall 9). D-13's "don't trust the client" rule applies: filter before parsing.

**Group-belongs-to-account validation** (`schedules.py:297-308`, verbatim) — silently drops
mismatched groups; D-08 additionally requires setting `is_active=False` when the result is empty:

```python
    # Validate that all groups belong to the selected account
    if group_ids:
        valid_groups = (
            await db.execute(
                select(Group.id).where(
                    Group.id.in_(group_ids),
                    Group.account_id == account_id,
                    Group.user_id == user.id,
                )
            )
        ).scalars().all()
        group_ids = [gid for gid in group_ids if gid in valid_groups]
```

**This is also the CR-01 site.** Note what is *missing* here and in `schedules_create`
(`schedules.py:166-215`): `ad_id` is taken from `Form(...)` and written straight to
`schedule.ad_id` (line 314) with no ownership query, and `account_id` (line 315) is never checked
against `MessengerAccount.user_id`. Both entries need the same
`select(...).where(..., user_id == user.id)` guard shown above.

**Toggle + `next_run_at` recomputation** (`schedules.py:344-361`, verbatim) — SCH-05 reuses this
route unchanged; the `resume_blocked` comment references the form page that D-14 deletes and must
be rewritten to point at the ad editor:

```python
    # issue #35: отвязанное расписание нельзя возобновить, пока пользователь не
    # привяжет аккаунт на форме редактирования. Пауза активного не блокируется.
    resume_blocked = (
        schedule is not None
        and not schedule.is_active
        and schedule.account_id is None
    )
    if schedule and not resume_blocked:
        schedule.is_active = not schedule.is_active
        if schedule.is_active:
            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name=schedule.timezone,
            )
        else:
            schedule.next_run_at = None
        await db.commit()
    return RedirectResponse(url="/schedules", status_code=302)
```

**Timezone-from-profile pattern** (`schedules.py:53-54`, repeated in `_build_schedule_items:28`):

```python
    tz_name = user.timezone if user.timezone in VALID_TIMEZONES else "UTC"
    tz = ZoneInfo(tz_name)
```

UI-SPEC makes the timezone a read-only mono caption in the schedule card — read it exactly this way.

**Deleted routes to remove wholesale (D-14):** `schedules_new` (`119-163`), `schedules_create`
(`166-215`, *after* its logic is re-homed), `schedules_edit` (`218-267`). Lines `131` and `240` are
the `Ad.is_active == True` filters that Pitfall 3 makes ordering-critical.

---

### `app/routes/schedules.py:67-73` (JSON API, request-response) — D-20

**Analog:** the ad check immediately above it, which is the shape the account check must copy:

```python
    ad_repo = AdRepository(db)
    ad = await ad_repo.get_by_id_and_user(data.ad_id, user_id)
    if ad is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ad not found",
        )
```

The JSON layer uses repositories (`AdRepository`, `ScheduleRepository`) and raises `HTTPException`;
the page layer uses raw `select()` and returns redirects. Do not mix the two conventions.

---

### `app/routes/uploads.py` (route, file-I/O) — CR-02

**Analog:** the Phase-1 hardening in the same file (`uploads.py:12-38`) — a module-level regex/table,
a small pure helper with a docstring explaining *why*, and a call site left otherwise untouched:

```python
# Клиентское имя файла из составного запроса полностью подконтрольно отправителю
# и участвует в построении ключа объекта: без нормализации сегменты пути в имени
# выводят ключ за префикс пользователя, то есть в чужую область того же хранилища.
_PATH_SEPARATORS = re.compile(r"[\\/]")
_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]")
MAX_FILENAME_LENGTH = 100
FALLBACK_FILENAME = "upload"


def safe_filename(filename: str | None) -> str:
    """Свести клиентское имя файла к безопасному звену ключа объекта.
    ...
    """
```

**The check being replaced** (`uploads.py:47-52`, verbatim) — client `Content-Type`:

```python
    # Validate file is an image
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )
```

**Rejection style to copy** (`uploads.py:56-61`) — `HTTPException(400, detail=...)`, size limit read
from `settings`, never hardcoded. The same rule applies to D-13: use
`settings.max_images_per_ad` (exists, currently unused — RESEARCH Pitfall 7), not a literal `10`.

**Key format that WR-01 validates against** (`uploads.py:63-67`, verbatim):

```python
    filename = f"{uuid4().hex}_{safe_filename(file.filename)}"
    key = f"{user_id}/{filename}"
```

`content` is already read at line 55 — the sniff needs no extra read, only a reordering of the
existing statements.

---

### `app/pages/common.py` (config glue) — D-21

**Analog:** `format_datetime_for_user` (`common.py:102-118`) — the one template global in this file
that takes request-scoped data as a **parameter** instead of reaching for `get_settings()`:

```python
def format_datetime_for_user(
    value: datetime | None,
    user: User | None,
    fmt: str = "%Y-%m-%d %H:%M",
) -> str:
    """Format datetime in user's timezone for display."""
```

**The three globals that break dependency override** (`common.py:36-38`, verbatim — all three,
not just line 38 as CONTEXT.md says):

```python
templates.env.globals["get_image_url"] = lambda key: get_image_url(key, get_settings().s3_public_url)
templates.env.globals["resolve_image_url"] = _resolve_image_url
templates.env.globals["s3_public_url"] = lambda: get_settings().s3_public_url
```

`_resolve_image_url` (`common.py:27-33`) is the third caller. The fix follows the
`format_datetime_for_user` shape: the base URL enters through the response context (like
`"user"`/`"is_admin"` in every `TemplateResponse` in `app/pages/*.py`), not through `get_settings()`.

**Test fixture analog for the leaking-`.env` half of the same defect:** `tests/conftest.py:12-26`
is the only fixture that neutralises SMTP (`smtp_host=""`); the fix is `Settings(_env_file=None, ...)`
applied to every module that builds its own `Settings`.

---

### `app/templates/ads/form.html` (template, rewritten editor)

**Analog:** itself — six tests in `tests/test_templates/test_ads_form_security.py` read this file
as **source text** (RESEARCH Pitfall 10), so the following must survive the rewrite *in this file*:

**Form action / dual-mode contract** (`form.html:18`, verbatim):

```jinja
  <form class="auth-form" method="post" action="{{ '/ads/' ~ ad.id ~ '/edit' if ad else '/ads/new' }}" id="ad-form">
```

**Macro import block** (`form.html:1-5`, verbatim) — Phase-1 macros only, no raw markup:

```jinja
{% extends "base.html" %}
{% from "components/button.html" import button, link_button %}
{% from "components/card.html" import card_open, card_close %}
{% from "components/field.html" import field, textarea_field %}
{% from "components/toggle.html" import toggle %}
```

**Shell contract** (`form.html:7-10`) — the page title and head action are shell blocks; the page
never renders its own `<h1>`:

```jinja
{% block title %}{{ 'Редактировать' if ad else 'Создать' }} объявление — Broadcaster{% endblock %}
{% block page_title %}{{ 'Редактировать объявление' if ad else 'Новое объявление' }}{% endblock %}
{% block page_actions %}{{ link_button('К объявлениям', '/ads', variant='ghost') }}{% endblock %}
```

**DOM-node construction pattern — the test-locked core** (`form.html:52-90`, abridged verbatim).
Keep `createElement` ≥ 3, `textContent`, `replaceChildren` ≥ 2, zero `innerHTML`/`outerHTML`/
`insertAdjacentHTML`/`document.write`, zero inline `onclick=` inside the script:

```javascript
const IMAGE_BASE_URL = '{{ s3_public_url() }}';
let imagePaths = {{ (ad.images | tojson) if ad and ad.images else '[]' }};

function renderImages() {
    const preview = document.getElementById('image-preview');
    const inputs = document.getElementById('image-inputs');
    preview.replaceChildren();
    inputs.replaceChildren();
    imagePaths.forEach((path, i) => {
        const url = path.startsWith('http') ? path : IMAGE_BASE_URL + '/' + path;
        const img = document.createElement('img');
        img.src = url;
        img.alt = '';
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.addEventListener('click', () => removeImage(i));
        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'images';
        hidden.value = path;
        inputs.appendChild(hidden);
    });
}
```

Note `IMAGE_BASE_URL` on line 53 uses bare `{{ s3_public_url() }}` inside JS quotes — the
Phase-1 review asks for `{{ s3_public_url() | tojson }}` **without** surrounding quotes.
Note also `form.html:26` and `:30` carry inline `onclick=` on *markup* (allowed by the current
tests, which only forbid it inside the `<script>` block); UI-SPEC replaces this drop zone with the
88×88 tile strip anyway.

**Upload call** (`form.html:98-107`) — `fetch('/api/uploads/image', {method:'POST', body: FormData})`
returning `{path}`; keep the endpoint and the response shape, replace `alert()` with the
UI-SPEC `alert(..., 'error')` copy.

**Toggle to delete** (`form.html:34-36`) — the `is_active` toggle removed by D-02/D-04.

---

### `app/templates/ads/includes/sched_card.html` (template macro)

**Analog:** `app/templates/schedules/includes/schedule_row.html` — the closest existing "one record,
its own forms, its own modal" unit.

**Macro-not-include convention + explicit params** (`schedule_row.html:1-15`, abridged verbatim):

```jinja
{# Строка расписания — по эталону ads/includes/ad_card.html (План 03).

   Это МАКРОС, а не include: импортированные шаблоны Jinja контекста
   вызывающего не получают, поэтому `item` и `user` — явные параметры. Ошибка в
   имени параметра проявится не исключением, а пустой строкой, поэтому
   отрисовка реальных данных закреплена тестом test_schedules_card_renders_data.

   Импорт: {% from "schedules/includes/schedule_row.html" import schedule_row, SCHEDULE_COLS %} #}
```

> The OOB fragments (`preview.html`, `summary.html`, `autosave.html`) are the exception: they are
> rendered by their own `TemplateResponse`/`{% include %}` and do receive context, so they may be
> includes. Anything called in a loop must be a macro with explicit parameters.

**Day-name map** (`schedule_row.html:26`, verbatim) — reuse, do not redeclare:

```jinja
{% set DAY_NAMES = {0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт', 4: 'Пт', 5: 'Сб', 6: 'Вс'} %}
```

**Toggle-as-form pattern** (`schedule_row.html:62-70`, verbatim) — the exact markup SCH-05 and the
editor card both reuse; the `change` event bubbles from the checkbox to the form, so the `toggle`
macro stays free of event attributes and the route survives with Alpine disabled:

```jinja
    {#- «Новый вид, старые действия»: маршрут, метод и серверные проверки
        владельца не тронуты — сменился только элемент управления. Событие
        change всплывает от чекбокса к форме, поэтому обработчик висит на
        форме, а макрос toggle остаётся без собственных атрибутов событий. -#}
    <form method="post" action="/schedules/{{ s.id }}/toggle" x-data x-on:change="$el.submit()">
      {{- toggle(name='is_active', checked=s.is_active, id='schedule-toggle-' ~ s.id,
                 title='Приостановить' if s.is_active else 'Возобновить') -}}
    </form>
```

**Delete-with-modal pattern** (`schedule_row.html:73-96`, verbatim) — a **real form** as the modal
trigger (never a bare button), with the modal placed as a sibling of the row, not inside it:

```jinja
    {#- Перехват отправки навешен на САМУ форму, а не заменил её кнопкой-триггером
        вне формы: без Alpine перехват не навешивается, и форма уходит POST-ом на
        прежний маршрут — ровно как до правки (WR-04, T-12-04). -#}
    <form method="post" action="/schedules/{{ s.id }}/delete"
          x-data x-on:submit.prevent="$dispatch('modal-open-schedule-del-{{ s.id }}')">
      {{- button('Удалить', variant='ghost', icon='trash', title='Удалить расписание') -}}
    </form>
...
{{ modal(id='schedule-del-' ~ s.id,
         title='Удалить расписание?',
         action='/schedules/' ~ s.id ~ '/delete',
         confirm_label='Удалить',
         method="post",
         body=item.ad_title) }}
```

**Line 71 is the link to rewrite** — `link_button('Изменить', '/schedules/' ~ s.id ~ '/edit', ...)`
becomes «Открыть объявление» → `/ads/{ad_id}/edit?sched={id}`.

---

### `app/templates/ads/includes/ad_card.html` (status cell, E15)

**Analog:** itself, `ad_card.html:43-45` (verbatim) — the exact three lines D-02/UI-SPEC E15 rewrite:

```jinja
  {%- call cell(label=AD_COLUMNS[5]) %}
    {%- if ad.is_active %}{{ badge('Активно', 'success') }}{% else %}{{ badge('Пауза', 'neutral') }}{% endif -%}
  {%- endcall %}
```

Target: `badge('Черновик', 'warning')` / `badge('Опубликовано', 'success')`, with an unrecognised
status falling back to «Черновик».

---

### `app/templates/schedules/{list,partial_cards}.html` + `includes/schedule_row.html` (card rewrite)

**Analog:** the Phase-1 ads triad; the current schedules triad shows the invariants that must
survive the table→card conversion.

**The infinite-scroll sentinel — byte-identical in two files** (`list.html:28` and
`partial_cards.html:6`, verbatim):

```jinja
  <div hx-get="/schedules/partial?offset={{ next_offset }}&limit=30" hx-trigger="revealed" hx-swap="outerHTML" class="empty__hint">Загрузка...</div>
```

with the invariant comment kept at `list.html:20-25`:

```jinja
  {# Инварианты бесконечной прокрутки (ломает переверстка, а не логика):
     - сентинел остаётся ПОСЛЕДНИМ элементом внутри ТОГО ЖЕ контейнера, что и
       строки: он заменяет сам себя и подтягивает следующий;
     - разметка сентинела здесь и в partial_cards.html ИДЕНТИЧНА — правится
       один, синхронно правится второй;
     - цель подмены неявная (сам сентинел), явной цели в проекте нет нигде. #}
```

**The partial file in full** (`schedules/partial_cards.html:1-2`) — a partial is the macro import
plus the loop, nothing else:

```jinja
{% from "schedules/includes/schedule_row.html" import schedule_row %}
{% for item in schedules %}{{ schedule_row(item, user) }}{% endfor %}
```

**What goes away:** `SCHEDULE_COLS` / `SCHEDULE_COLUMNS` (`schedule_row.html:24-25`), the
`rowhead(...)` call (`list.html:19`), and the `row_open`/`cell`/`row_close` imports — replaced by
`[data-sched-list]` / `.sched-item` per UI-SPEC.

**Head action + empty state to rewrite** (`list.html:14` and `:32-35`):

```jinja
{% block page_actions %}{{ link_button('Создать', '/schedules/new', icon='plus') }}{% endblock %}
...
{{ empty_state('Нет расписаний',
               hint='Создайте расписание, чтобы объявление уходило в группы по графику',
               action_label='Создать первое расписание',
               action_href='/schedules/new') }}
```

**Filter bar analog:** `components/filters.html:25` signature — block-call, never a parameter.
Live usages to copy from: `app/templates/groups/list.html`, `app/templates/history/list.html`.

```jinja
{% macro filters(id, action=None, method='get', open_on_desktop=true, label='Фильтры') -%}
```

```jinja
     {% call filters('groups-filters', action='/groups') %}
       {{ select_field(...) }}
       {{ button('Применить') }}
     {% endcall %}
```

---

### Tests

**Page-render test analog:** `tests/test_pages/test_responsive_markup.py:260-278`
(`test_schedules_card_renders_data`, verbatim) — the pattern for every new editor/list render test:
seed via `db_session`, request via `authed_client`, assert on **real data strings and route URLs**,
never on status alone:

```python
@pytest.mark.asyncio
async def test_schedules_card_renders_data(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Строка расписания отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    Перевод include в макрос теряет неявный контекст вызывающего шаблона:
    страница останется валидной и вернёт 200, а строки будут пустыми.
    """
    schedule = await _seed_schedule(db_session, ad_title="Расписание летней акции")

    response = await authed_client.get("/schedules")
    assert response.status_code == 200
    html = response.text
    assert "Расписание летней акции" in html
    assert "09:30" in html
    assert f"/schedules/{schedule.id}/edit" in html
    assert f"/schedules/{schedule.id}/toggle" in html
```

Line 276 (`/schedules/{id}/edit`) is one of the nine references RESEARCH lists as needing a rewrite.

**Cross-user isolation analog:** `test_responsive_markup.py:280-290` (`test_schedules_toggle_route_unchanged`)
seeds a foreign `Ad(user_id=own_user.id + 1000, ...)` and asserts the foreign record is untouched.
This is the shape for the CR-01/D-20 regression tests on both entries.

**Model test analog:** `tests/test_models/test_ad.py:6-33` — construct through `db_session`, commit,
`refresh`, assert field by field. Lines 33 and 58 (`assert ad.is_active is True`) become `status`
assertions in the same commit as the migration.

**Fixtures available** (`tests/conftest.py`): `test_settings`, `db_session` (in-memory SQLite,
`Base.metadata.create_all` — **migrations never run**), `client`, `auth_headers`,
`authed_client` (cookie-based; page routes need this, not `auth_headers`), `admin_client`.

**No analog for a migration test** — nothing in `tests/` references Alembic.

---

## Shared Patterns

### Page-route authentication + ownership
**Source:** `app/pages/ads.py:112-114` / `app/pages/schedules.py:283-290`
**Apply to:** every handler in `app/pages/ads.py` and `app/pages/schedules.py`

```python
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)
```

Ownership lives **in the `WHERE`**, not in a follow-up `if`. Schedules reach the user through
`.join(Ad, Schedule.ad_id == Ad.id)` because `Schedule` has no `user_id`.

### Full-page template context
**Source:** `app/pages/ads.py:92-103`
**Apply to:** every full-page route (fragments omit `is_admin` / `active_page`)

```python
    return templates.TemplateResponse(
        "ads/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "ads": ads,
            "has_next": has_next,
            "next_offset": PAGE_SIZE,
            "active_page": "ads",
        },
    )
```

### JSON-API authentication + error style
**Source:** `app/routes/schedules.py:61-73`
**Apply to:** `app/routes/ads.py`, `app/routes/schedules.py`, `app/routes/uploads.py`

`user_id: int = Depends(get_current_user_id)` + repository lookup + `raise HTTPException(status_code=..., detail=...)`.
Never redirects. Never raw `select()`.

### Progressive-enhancement markup rule
**Source:** `app/templates/schedules/includes/schedule_row.html:63-79`, `ads/includes/ad_card.html:46-58`
**Apply to:** every interactive control in new markup (D-09)

Every mutation is a real `<form method="post">` at its real route. Alpine/htmx attributes are
*added to* that form (`x-on:change="$el.submit()"`, `x-on:submit.prevent="$dispatch(...)"`,
`hx-post`), never a replacement for it. Tests named `*_degrades_without_alpine` check this.

### Client-side rendering rule
**Source:** `app/templates/ads/form.html:45-51` (the comment) and `:56-91` (the code)
**Apply to:** all new JS in the editor

Build DOM nodes and assign properties (`textContent`, `.value`, `.src`); `innerHTML`, `outerHTML`,
`insertAdjacentHTML`, `document.write` are at zero project-wide and asserted against the source text.

### Settings-derived limits
**Source:** `app/routes/uploads.py:56-61`
**Apply to:** D-13 attachment cap

Thresholds come from `settings.*` (`max_image_size_mb`, `max_images_per_ad`), never from a literal.

### "Why", not "what", comments in Russian
**Source:** every file quoted above
**Apply to:** all new code

Non-obvious decisions carry a comment naming the decision id (D-xx / CR-xx / issue #NN) and the
failure mode that motivated it. This is a strong, consistent project convention.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `app/templates/ads/includes/autosave.html` | template fragment | event-driven | No `hx-post`, `hx-swap-oob`, `hx-sync` or `HX-Push-Url` usage exists anywhere in the project — htmx is used only for `hx-get` + `revealed` sentinels. RESEARCH §Code Examples 2-3 is the only source; `tests/test_pages/test_htmx_preserved.py:22-23` explicitly records that no explicit swap target exists in the project, so OOB is being introduced, not copied. |
| `tests/test_migrations/test_0013_ad_status.py` | test | DDL | Nothing in `tests/` imports or runs Alembic; `tests/conftest.py:33` builds the schema with `Base.metadata.create_all`. The `upgrade`/`downgrade` round-trip has no precedent to copy. |

Partial-only analogs (planner should lean on `02-RESEARCH.md` §Code Examples for the missing half):

- `ads/includes/preview.html` / `summary.html` — the *fragment file* convention comes from
  `schedules/partial_cards.html`, but no server-rendered preview exists in the project.
- `app/static/css/app.css` section 8 — sections 1-7 give the numbering and comment style; every
  selector in UI-SPEC §Component Inventory is new.

---

## Metadata

**Analog search scope:** `app/pages/`, `app/routes/`, `app/models/`, `app/application/`,
`app/templates/{ads,schedules,components,includes}/`, `alembic/versions/`, `tests/`
**Files read in full:** `app/pages/ads.py`, `app/pages/common.py`, `app/pages/schedules.py`,
`app/models/ad.py`, `app/routes/uploads.py`, `app/templates/ads/form.html`,
`app/templates/schedules/list.html`, `app/templates/schedules/partial_cards.html`,
`app/templates/schedules/includes/schedule_row.html`,
`alembic/versions/0012_schedules_account_id_nullable_set_null.py`, `tests/conftest.py`
**Files read in part:** `app/routes/schedules.py`, `app/templates/ads/includes/ad_card.html`,
`app/templates/components/filters.html`, `tests/test_pages/test_responsive_markup.py`,
`tests/test_models/test_ad.py`
**Pattern extraction date:** 2026-08-10
