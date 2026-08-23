---
phase: 06-admin-panel
reviewed: 2026-08-23T14:20:00Z
depth: standard
files_reviewed: 72
files_reviewed_list:
  - app/dependencies.py
  - app/main.py
  - app/pages/common.py
  - app/pages/auth.py
  - app/pages/admin.py
  - app/pages/billing.py
  - app/pages/history.py
  - app/pages/profile.py
  - app/pages/__init__.py
  - app/services/auth_service.py
  - app/services/loki_client.py
  - app/services/ops_state.py
  - app/application/admin/__init__.py
  - app/application/admin/incidents.py
  - app/application/admin/overview_stats.py
  - app/application/admin/payments_query.py
  - app/application/admin/queue_rows.py
  - app/application/admin/users_query.py
  - app/application/analytics/send_analytics.py
  - app/application/scheduling/use_cases.py
  - app/repositories/user.py
  - app/config.py
  - app/database.py
  - app/worker/celery_app.py
  - app/templates/base.html
  - app/templates/admin/user_detail.html
  - app/templates/admin/workers.html
  - app/templates/admin/queue.html
  - app/templates/admin/logs.html
  - app/templates/admin/users.html
  - app/templates/admin/overview.html
  - app/templates/admin/payments.html
  - app/templates/admin/includes/_tabs.html
  - app/templates/admin/includes/worker_row.html
  - app/templates/admin/includes/workers_partial.html
  - app/templates/admin/includes/queue_row.html
  - app/templates/admin/includes/queue_time.html
  - app/templates/admin/includes/log_row.html
  - app/templates/admin/includes/user_row.html
  - app/templates/admin/includes/incident_row.html
  - app/templates/admin/includes/payment_row.html
  - app/templates/components/filter_chips.html
  - app/templates/history/list.html
  - app/static/css/app.css
  - nginx/nginx.conf.template
  - docker-compose.prod.yml
  - .env.example
  - tests/test_pages/test_impersonation_gate.py
  - tests/test_pages/test_impersonation.py
  - tests/test_pages/test_access_gate.py
  - tests/test_pages/test_blocked_user.py
  - tests/test_pages/test_cookie_flags.py
  - tests/test_pages/test_reset_code_source.py
  - tests/test_services/test_auth_token.py
  - tests/test_services/test_loki_client.py
  - tests/test_services/test_ops_state.py
  - tests/test_application/test_incidents.py
  - tests/test_application/test_queue_rows.py
  - tests/test_application/test_admin_payments.py
  - tests/test_application/test_admin_uses_analytics.py
  - tests/test_pages/test_admin_panel.py
  - tests/test_pages/test_admin_users.py
  - tests/test_pages/test_admin_payments.py
  - tests/test_pages/test_filter_chips.py
  - tests/test_pages/test_history.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_shell.py
  - tests/test_repositories/test_user_repo.py
  - tests/test_templates/test_components.py
  - tests/test_admin.py
  - tests/test_application/__init__.py
  - tests/test_pages/__init__.py
findings:
  critical: 2
  warning: 10
  info: 4
  total: 16
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-08-23T14:20:00Z
**Depth:** standard
**Files Reviewed:** 72
**Status:** issues_found

## Summary

The phase's three interacting rules (impersonation, the route-dependency gate, effective
blocking) were traced end-to-end, and the arithmetic of the admin subsections was read
against its own declared invariants.

Two of the four areas flagged for a second pair of eyes came back clean:

- **Admin rights survive impersonation, and blocking behaves as decided.** `require_admin`
  (`app/dependencies.py:104-120`) branches on the actor before anything else, so a blocked
  subject does not cost the actor the admin panel; `get_user_from_cookie`
  (`app/pages/common.py:385-387`) refuses a blocked subject only when no actor is present.
  The three rules agree.
- **The Unicode `lower()`/`upper()` shim cannot reach PostgreSQL.** Verified empirically:
  `AsyncAdapt_asyncpg_connection` defines no `__getattr__` and no `create_function`, so
  `getattr(dbapi_connection, "create_function", None)` returns `None` and the listener
  returns before touching a production connection. The shim does work on SQLite
  (`lower('ИВАН') == 'иван'`). It has a narrower defect, recorded as WR-05.

The other two came back with defects, one of them severe:

**`forbid_when_impersonating` is bypassable on every route it protects on the page
surface — with a junk HTTP header, no credentials of any kind required.** The guard reads
the token credentials-first (bearer header, then cookie); the handlers it protects read
the cookie *only*. Sending `Authorization: Bearer <anything>` alongside the impersonation
cookie makes the guard see "no actor" while the handler still acts as the subject. This is
reproduced below against the exact route whose entry in the gate's own allow/deny table is
annotated "начало захвата учётной записи", and against the money router the phase declares
closed by default (CR-01).

Separately, the three most destructive admin actions — block, delete, grant free access —
carry no same-origin guard, while the three routes the phase newly wrote (restart, drop,
impersonate) all do (CR-02).

The rest is a long tail: a second, weaker expression of "who is an admin" in
`require_admin`; an unguarded parse of an external service's response on the page whose
whole design premise is "the source may be down"; untrusted queue data interpolated into an
HTML attribute *name*; and several places where the phase's own "one declaration per rule"
doctrine is stated in a comment but not held in the code.

The prompt-listed pre-existing failure
(`test_ads_editor.py::test_image_base_url_comes_from_app_settings`) is not reported.

## Critical Issues

### CR-01: The impersonation guard is bypassed by any `Authorization` header

**File:** `app/dependencies.py:243-294` (guard), `app/dependencies.py:185-224` (`_actor_id`),
`app/pages/common.py:339-387` (`get_user_from_cookie`)

**Issue:**
`_actor_id()` resolves the token in the order *parsed credentials → `Authorization` header →
cookie* (lines 213-224). Every route the guard protects on the page surface authenticates
through `get_user_from_cookie()`, which reads **the cookie and nothing else** (line 371).
The two disagree about what "the request's token" is.

Because `security = HTTPBearer(auto_error=False)` (line 12), any `Authorization: Bearer …`
header is handed to the guard as `credentials`, and because an unreadable token is
deliberately *not* a refusal (`decode_access_token` → `None` → `actor_id(None)` → `None`,
line 224), **the header does not have to be a valid token — it does not have to be a token
at all.** The guard returns without refusing at line 284; the handler proceeds under the
impersonated subject's cookie.

The refusal is not even logged, because the `logger.warning("impersonated_action_refused")`
at line 286 is never reached.

Reproduced against a live app (admin impersonating `victim@test.com`):

```
POST /forgot-password/send-code                                  -> 403   (guard fires)
POST /forgot-password/send-code  + "Authorization: Bearer zzz"   -> 200   (guard bypassed;
                                        password-reset code issued for the victim's account)

POST /profile                                                    -> 403
POST /profile                    + "Authorization: Bearer zzz"   -> 400   (handler reached)

POST /billing/subscribe                                          -> 403
POST /billing/subscribe          + "Authorization: Bearer zzz"   -> 302 /billing?error=payment
                                        (reached create_payment; in production this creates a
                                         real YooKassa intent in the subject's name)
```

Everything the gate declares forbidden on the page surface is reachable this way: all four
password-reset steps (`app/pages/auth.py:539,616,682,761` — i.e. account takeover, the case
the gate's own table calls out), `profile_post` (`app/pages/profile.py:42`), `history_retry`
(`app/pages/history.py:873` — an irreversible send into the subject's groups), and the whole
`money_router` (`app/pages/__init__.py:146`), which the phase documents as "закрыт целиком…
по умолчанию".

Admin-router handlers are *not* affected by the junk-header variant, because `require_admin`
→ `get_current_user` also reads the header first and 401s on garbage. That is precisely the
point: the codebase already resolves the token header-first everywhere except the page
authenticator, and the guard was written to match the wrong one.

`tests/test_pages/test_impersonation_gate.py` cannot catch this — it asserts only that the
dependency is *declared* on the route, never that it *fires*. Confirmed by measurement, not
inference: `test_impersonation_gate.py` and `test_impersonation.py` were run against the
code as submitted and report **44 passed**. The machine gate walks all 49 mutating routes,
finds the dependency correctly declared on every one it should be, and goes green — while
the bypass above works on all of them. The gate certifies declaration; the defect is in
enforcement, and nothing in the phase's 2 000-plus lines of impersonation tests looks there.

**Fix:** make the guard read the token from the same place, and only the same place, as the
handler it guards. The simplest correct form is to stop consulting bearer credentials for
page routes:

```python
def _actor_id(request: Request, credentials, settings) -> int | None:
    # ⚠️ ИСТОЧНИК ТОКЕНА ОБЯЗАН СОВПАДАТЬ С ИСТОЧНИКОМ ОБРАБОТЧИКА.
    # Страничные обработчики читают ТОЛЬКО cookie; гард, читавший сперва
    # заголовок, отключался присланным заголовком — любым, включая негодный.
    tokens = []
    if credentials is not None:
        tokens.append(credentials.credentials)
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        tokens.append(auth_header[7:])
    cookie = request.cookies.get("access_token")
    if cookie:
        tokens.append(cookie)
    # ЛЮБОЙ предъявленный носитель с признаком действующего лица — отказ.
    for token in tokens:
        found = actor_id(decode_access_token(token, settings.secret_key))
        if found is not None:
            return found
    return None
```

Checking *every* presented credential (rather than the first) closes the mismatch in both
directions and keeps the "missing token is not a refusal" property the YooKassa webhook
depends on. Add a regression test that sends a junk bearer header alongside an impersonation
cookie and asserts 403 — the gate's declaration test does not cover behaviour.

### CR-02: Block / delete / free-access admin actions have no CSRF guard

**File:** `app/pages/admin.py:1766-1789` (`admin_toggle_block`),
`app/pages/admin.py:1791-1811` (`admin_delete_user`),
`app/pages/admin.py:1572-1666` (`admin_toggle_free_access`);
forms at `app/templates/admin/user_detail.html:145,149,175`

**Issue:**
The three routes the phase newly wrote all call `is_same_origin(request)` before acting —
`admin_restart_worker` (line 899), `admin_drop_task` (line 1096), `admin_impersonate`
(line 1718) — and `admin_restart_worker`'s docstring states the rule explicitly: "новая
изменяющая форма админки без него МОЛЧА расширила бы принятую границу риска".

The three routes that actually destroy or seize things do not call it:

| route | guard | effect |
|---|---|---|
| `POST /admin/users/{id}/delete` | none | irreversible account deletion |
| `POST /admin/users/{id}/block` | none | locks a paying customer out of the product |
| `POST /admin/users/{id}/unlimited` | none | grants/revokes a paid resource |

Authentication is cookie-based with `samesite="lax"` (`app/pages/auth.py:88`), which permits
top-level cross-site **POST**… no — `lax` does block cross-site POST cookie transmission,
and that is the only thing standing between these routes and a one-click account wipe. It is
a single browser-policy default doing the job the codebase elsewhere assigns to an explicit
server-side check, with no defence in depth behind it, and the templates carry no CSRF token
either. `admin_delete_user` additionally received a `forbid_when_impersonating` dependency in
this phase (line 1796) — the handler was edited without the origin guard being added.

The asymmetry is also self-contradicting: `admin_impersonate` guards origin because "без
гарда сторонняя страница выписала бы себе токен имперсонации", yet the neighbouring route
that *deletes the user outright* does not.

**Fix:** apply the project's existing guard, in the same position (after auth, before any
read), to all three:

```python
@router.post("/users/{user_id}/delete")
async def admin_delete_user(request: Request, user_id: int, ...):
    # Гард происхождения — тот же и в той же позиции, что у соседних изменяющих
    # маршрутов админки: удаление НЕОБРАТИМО, и оно не имеет права быть
    # единственным изменяющим входом раздела без сверки источника.
    if not is_same_origin(request):
        return Response(status_code=403)
    ...
```

Then extend `tests/test_pages/test_admin_panel.py` with an AST assertion that *every*
`@router.post` in `app/pages/admin.py` calls `is_same_origin` — the same machine-gate form
the phase already uses for the container-API prohibition, so the next added route cannot
escape by omission.

## Warnings

### WR-01: `require_admin` lacks the empty-`admin_email` guard that `check_is_admin` has

**File:** `app/dependencies.py:111,118` vs `app/pages/common.py:421-426`

**Issue:** `check_is_admin` opens with `if not settings.admin_email: return False`.
`require_admin` — the dependency that actually gates all 16 admin routes — has no such
branch and compares `actor.email != settings.admin_email` directly. `admin_email` defaults
to `""` (`app/config.py`). On a deployment where `ADMIN_EMAIL` is unset, any user row whose
`email` is the empty string is an administrator on every `/admin` route, while the sidebar
link stays hidden because the page-side predicate says otherwise. Two expressions of one
rule that disagree in exactly the direction that grants access — the class of defect this
module's own comments are written to prevent.

Reachability is limited today (both registration paths reject an empty address in practice),
but the guard costs one line and the divergence is the actual finding.

**Fix:**
```python
async def require_admin(request, db, settings) -> "User":
    if not settings.admin_email:
        raise HTTPException(status_code=403, detail="Admin access required")
    ...
```
Better still: have both call one predicate so the rule cannot diverge again.

### WR-02: Returning from impersonation issues a full session without re-checking the actor

**File:** `app/pages/auth.py:488-500`

**Issue:** `stop_impersonation` reads `act` from the cookie, loads the actor, and mints a
**normal 24-hour token** for them (`create_access_token(admin.id, …)`, line 499) with no
check that the actor is still unblocked or still matches `settings.admin_email`. An
administrator who was blocked or de-privileged *during* a 60-minute impersonation window
walks out of it with a fresh full-lifetime session for the account that was revoked. It also
silently upgrades a 60-minute credential into a 1440-minute one on demand.

The docstring argues, correctly, that `require_admin` must not gate this route (otherwise
the actor is trapped). That argument does not extend to `is_blocked`: a blocked actor should
be returned to `/login`, exactly as the missing-actor branch already does at lines 490-496.

**Fix:**
```python
admin = await db.get(User, admin_id)
if admin is None or admin.is_blocked:
    # Учётной записи действующего лица больше нет либо она закрыта: вернуть
    # человека не к кому. Единственный честный исход — выход.
    response = RedirectResponse(url="/login", status_code=302)
    clear_session_cookie(response, settings)
    return response
```

### WR-03: A malformed Loki response 500s the Logs subsection

**File:** `app/services/loki_client.py:452-465` (loop), `app/services/loki_client.py:392-412`
(`_parse_stream`)

**Issue:** The module goes to great lengths to make "the source is unreachable" a normal
branch — the HTTP call and the `payload["data"]["result"]` lookup are each wrapped. The
**parse of the payload is not**. `for stream in streams: lines.extend(_parse_stream(stream))`
runs outside every `try`, and `_parse_stream` trusts the shape it is handed:

- `stream.get("stream")` → `AttributeError` if an element is not a dict
- `for value in stream.get("values")` → `TypeError` if `values` is not iterable
- `value[0], value[1]` → `IndexError` on a short entry
- `int(ts_ns)` → `ValueError` on a non-numeric timestamp

`streams` itself is only known to be *some* value at key `result`. Any of these takes
`/admin/logs` to a 500 through the generic handler in `app/main.py:226` — the page whose
docstring says "недоступность приходит ОТДЕЛЬНЫМ полем результата… не пустым списком".
A wrong-shaped answer is the same class of event as no answer, and it is handled differently.

**Fix:** move the parse inside the same failure branch:
```python
    try:
        lines: list[LogLine] = []
        for stream in streams:
            lines.extend(_parse_stream(stream))
    except (AttributeError, TypeError, ValueError, IndexError):
        # Ответ пришёл, но формы, о которой договаривались, в нём нет — это то же
        # «прочитать негде», что и молчание источника, а не пятисотка подраздела.
        logger.warning("loki_unreadable_answer", query=logql)
        return LogWindow(lines=[], capped=False, unavailable=True)
```

### WR-04: Queue task ids reach an HTML attribute *name* and an Alpine JS expression

**File:** `app/templates/admin/includes/queue_row.html:61-63`,
`app/templates/admin/queue.html:135`, `app/templates/components/modal.html:96`

**Issue:** `row.task_id` originates in a Redis queue body — data `queue_rows.py` explicitly
treats as foreign and possibly malformed (`_decode_task` accepts any JSON dict). It is
interpolated into two contexts Jinja autoescaping does **not** make safe:

1. an Alpine expression — `x-on:submit.prevent="$dispatch('modal-open-queue-drop-{{ account.id }}-{{ row.task_id }}')"`.
   Escaped `&#39;` is decoded by the HTML parser before Alpine evaluates the attribute as
   JavaScript, so a quote in `task_id` closes the string literal.
2. an **attribute name** — `x-on:modal-open-{{ id }}.window="show()"` in `modal.html:96`,
   where `id` is `'queue-drop-' ~ account.id ~ '-' ~ row.task_id`. Attribute names cannot be
   escaped at all; whitespace or `="` in the value injects new attributes into the admin's
   page.

`log_row.html` states the project's position — "Строка журнала — содержимое, пришедшее из
ЧУЖОГО процесса… автоэкранирование проекта включено сплошь" — which is true for text nodes
and false for these two slots.

Today `task_id` is a `uuid4` written by `dispatch_send_tasks`, so this is defence-in-depth
against anything that can write the queue, not a live exploit. It is still a real gap between
the stated model ("markup escapes it") and the code.

**Fix:** do not derive DOM identifiers from queue payloads. Key the modal on a value the
server controls — the row index, or a hash — and pass `task_id` only through the escaped
`<input type="hidden" value="…">` that already carries it:

```jinja
{%- set modal_key = account.id ~ '-' ~ loop.index0 -%}
<form method="post" action="/admin/queue/{{ account.id }}/drop"
      x-data x-on:submit.prevent="$dispatch('modal-open-queue-drop-{{ modal_key }}')">
```

### WR-05: The SQLite `lower()`/`upper()` override changes behaviour for non-text arguments

**File:** `app/database.py:11-45`

**Issue:** The listener replaces SQLite's built-in `lower`/`upper` for *every* connection
that exposes `create_function`, with `lambda value: value.lower() if value is not None else None`.
Verified behaviour change:

```
select lower(123)         builtin -> '123'    after override -> OperationalError
select upper(4.5)         builtin -> '4.5'    after override -> OperationalError
select lower(x'414243')   builtin -> 'abc'    after override -> b'abc'  (BLOB, not TEXT)
```

Two consequences. First, a function introduced to *remove* a SQLite/PostgreSQL divergence
introduces a new one for any expression that folds a numeric or blob value — and it fails
loudly at the DB layer, i.e. as a 500, rather than in the search feature that motivated it.
Second, the functions are registered **without `deterministic=True`**, so SQLite will refuse
them in index expressions, partial-index predicates, generated columns and `CHECK`
constraints; any future migration adding `CREATE INDEX … ON users (lower(email))` will fail
in the suite while working in production.

The listener is also attached to `Engine` globally, so it applies to every SQLite connection
in the process, not just the test engine it was written for.

**Fix:**
```python
def _fold(op):
    def _apply(value):
        if value is None:
            return None
        if not isinstance(value, str):
            # Встроенная функция SQLite приводит число к тексту; замена обязана
            # вести себя так же, иначе она чинит одно расхождение и заводит второе.
            value = str(value)
        return op(value)
    return _apply

create_function("lower", 1, _fold(str.lower), deterministic=True)
create_function("upper", 1, _fold(str.upper), deterministic=True)
```

### WR-06: Runtime `assert` used as a build-time invariant at module import

**File:** `app/worker/celery_app.py` (module level, immediately after the two constants)

**Issue:** `assert INFRA_HEARTBEAT_TTL_SEC == MAX_HEARTBEAT_STALE_SEC` executes at import of
`app.worker.celery_app`. Two problems, in opposite directions: under `python -O` the check
disappears entirely, so the invariant it documents is not enforced where it matters; and if
it ever *does* fire, it raises `AssertionError` at import, killing every Celery worker, the
beat process and anything else that imports the module — turning a constant mismatch into a
total outage of the send path.

**Fix:** derive rather than assert, so the values cannot diverge:
```python
# Срок жизни признака ВЫВЕДЕН из порога свежести, а не сверен с ним: выписанные
# порознь, они разошлись бы, а `assert` на импорте снимается ключом -O.
INFRA_HEARTBEAT_TTL_SEC = MAX_HEARTBEAT_STALE_SEC
INFRA_HEARTBEAT_INTERVAL_SEC = INFRA_HEARTBEAT_TTL_SEC // 3
```
If a check is preferred, raise an explicit exception in a test, not at import.

### WR-07: Unbounded reads on the `/admin` overview render path

**File:** `app/application/admin/incidents.py` (`unclosed_payments_stmt`, and the
`MessengerAccount` selection inside `collect_incidents`)

**Issue:** `collect_incidents` claims "ЧИСЛО ОБРАЩЕНИЙ К БАЗЕ НЕ ЗАВИСИТ ОТ ЧИСЛА НАЙДЕННЫХ
ИНЦИДЕНТОВ", which is true — but the number of **rows** does. `unclosed_payments_stmt()`
selects *every* non-terminal payment ever created, with no `LIMIT`; the down-account query
selects every account in a down state. `INCIDENT_LIST_CAP = 20` truncates the *display*
after all rows have been materialised in Python.

The stuck-payment set only grows: `detect_payment_stuck` exists precisely because cancelled
YooKassa intents are never closed, so this is a monotonically growing table read in full on
every render of the page administrators open during an outage. The phase caps every other
such read for exactly this reason (`WORKER_LIST_CAP`, `QUEUE_ROW_CAP`, `LOG_LINE_CAP`,
`PAYMENT_LIST_CAP`, `USERS_PAGE_SIZE`); this one is the exception, and the load lands on the
page whose whole purpose is to work when the system does not.

**Fix:** read `INCIDENT_LIST_CAP + 1` rows, ordered oldest-first, and surface the truncation
through the `capped` flag that `IncidentBoard` already carries:
```python
def unclosed_payments_stmt(limit: int = INCIDENT_LIST_CAP + 1):
    return (
        select(Payment.id, Payment.user_id, Payment.created_at)
        .where(unclosed_payment_clause())
        .order_by(Payment.created_at)
        .limit(limit)
    )
```

### WR-08: The impersonation AST gate has blind spots it does not declare

**File:** `tests/test_pages/test_impersonation_gate.py:243-260,306-336`

**Issue:** The gate is a load-bearing security control ("маршрут, добавленный будущей фазой…
роняет тест"), and its own limits are not written down. Four route shapes are invisible to it:

1. `ROUTE_DIRECTORIES` is globbed with `*.py`, not `**/*.py` (line 253) — a router placed in
   `app/routes/admin/` would never be scanned. All routers happen to be top-level today.
2. Only `@<bare_name>.<method>(...)` is recognised (lines 322-328). `@router.api_route(...,
   methods=["POST"])`, `router.add_api_route(...)`, and `@pkg.mod.router.post(...)` all pass
   the walk unseen.
3. `routes[route.key] = route` (line 335) keys on `module::handler`, so two mutating routes
   sharing a handler name in one module collapse into one entry — and `MUTATING_ROUTE_COUNT`
   would absorb it silently, since the count is taken from the same dict.
4. Only `MUTATING_METHODS = {post, put, patch, delete}` are considered. A state-changing
   `GET` is invisible; the project already has one (`GET /logout`, which clears the session
   cookie).

None is exploitable today. All four should be stated in the module docstring next to the
existing "зубы гейта доказаны" paragraph, and (1) is a one-character fix.

**Fix:** change the glob to `**/*.py`, key routes on `module::router::handler`, and add the
remaining two limits to the docstring as named accepted gaps.

### WR-09: Silent `except: pass` misclassifies the Celery worker's role

**File:** `app/worker/celery_app.py`, `start_worker_infra_heartbeat`

**Issue:**
```python
    queues = ()
    try:
        queues = tuple(sender.app.amqp.queues.keys())
    except Exception:
        pass
    _start_infra_heartbeat(_infra_service_for_queues(queues))
```
The swallow is total and unlogged. When it fires on the *telegram* worker, `queues` stays
empty, `_infra_service_for_queues` falls through to `INFRA_WORKER_DEFAULT`, and the process
starts writing the **wrong** heartbeat key. The Workers subsection then shows the Telegram
worker permanently offline *and* the default worker online twice over — a false alarm and a
false all-clear from one swallowed exception, on the block administrators consult during an
outage. Nothing in the logs would point at it.

**Fix:**
```python
    except Exception as e:
        log.warning("infra_heartbeat_queues_unreadable", error=str(e))
```
and consider failing closed to `WORKER_UNKNOWN` rather than to `worker-default`, on the same
grounds the module already gives for `_unknown()` in `ops_state.py`: a guess presented as a
measurement is worse than an admitted gap.

### WR-10: LIKE wildcards in the admin user search are not escaped

**File:** `app/application/admin/users_query.py:118-126`

**Issue:** `pattern = func.lower(f"%{text}%")` binds the search text as a parameter (no
injection), but `%` and `_` inside it retain their `LIKE` meaning. A search for `a_b` matches
`axb`; a search for `_` matches every user. The subsection's promise — "администратор ищет
КОНКРЕТНОГО человека" — is quietly false for any address containing an underscore, which is
common in email local parts.

**Fix:**
```python
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = func.lower(f"%{escaped}%")
    query = query.where(
        or_(
            func.lower(User.name).like(pattern, escape="\\"),
            func.lower(User.email).like(pattern, escape="\\"),
        )
    )
```

## Info

### IN-01: `INCIDENT_DESTINATIONS` is dead in production and disagrees with the code

**File:** `app/application/admin/incidents.py:99-105`;
`app/templates/admin/includes/incident_row.html:5-8`

**Issue:** No production code reads `INCIDENT_DESTINATIONS` — each `detect_*` builds `href`
from the `HREF_*` constants directly. Its only readers are two tests. Its `account_down`
entry is `"/admin/users/"`, which is not what `detect_account_down` emits
(`HREF_USER_CARD.format(user_id=…)` → `/admin/users/{id}`); the tests pass only because they
assert `href.startswith(prefix)`. Meanwhile `incident_row.html` documents it as the
production source of hrefs: "Адрес приезжает ГОТОВЫМ из прикладного модуля
(`INCIDENT_DESTINATIONS`)". That is a second declaration of the routing rule, divergent from
the first, described by a comment as the only one — the exact shape the module's other
docstrings are written to forbid.

**Fix:** either have the `detect_*` functions read `INCIDENT_DESTINATIONS[kind]` (making it
real and the comment true), or delete it and correct the template comment to name the
`HREF_*` constants.

### IN-02: Three admin handlers hand-roll the context that `_admin_context` exists to provide

**File:** `app/pages/admin.py:1370-1400` (`admin_user_detail`), `1401-1449`
(`admin_user_history`), `1536-1562` (`admin_user_history_detail`)

**Issue:** All three repeat `{"request": …, "user": admin, "is_admin": True, "active_page":
"admin", …}` inline instead of calling `_admin_context()`. The visible consequence is that
none of them passes `admin_tabs`/`admin_tab`, so drilling into a user drops the subsection
tab bar entirely — the navigation `_tabs.html` was built to keep consistent across six
subsections. The invisible consequence is five keys duplicated three times.

**Fix:** `{**_admin_context(request, admin, "users"), "target_user": target_user, …}` and
add `{% include "admin/includes/_tabs.html" %}` to `admin/user_detail.html`.

### IN-03: Fourth literal copy of a background colour that the project otherwise tokenises

**File:** `app/static/css/app.css:931`

**Issue:** `.subtab[data-subtab-active] { background: #15151d; }` joins three existing
copies (lines 582, 584, 648). The comment above it acknowledges the coupling — "Тот же
приподнятый фон, что у активного нижнего таба шелла" — and then re-types the value rather
than sharing it, in a file where every other colour is a `var(--…)`.

**Fix:** introduce `--surface-nav-active: #15151d;` alongside the other tokens and replace
all four literals.

### IN-04: Grafana is publicly proxied with a default password that `.env.example` never mentions

**File:** `nginx/nginx.conf.template:65-73`; `docker-compose.monitoring.yml:37`; `.env.example`

**Issue:** The HTTPS server block proxies `/grafana/` to the monitoring stack with no auth in
front of it, and `GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}` defaults to
`admin`. `.env.example` — which this phase edited, adding `COOKIE_SECURE` with a nine-line
explanation — documents neither `GRAFANA_ADMIN_PASSWORD` nor the exposure. A deployer who
follows the example file and raises monitoring publishes a Grafana admin console at
`https://<domain>/grafana/` with `admin`/`admin`, wired to a Loki datasource carrying the
application's logs.

This is pre-existing and outside the phase diff, but it sits in two files this phase edited
and directly concerns the operational surface the phase builds. Raised here rather than
silently left.

**Fix:** add `GRAFANA_ADMIN_PASSWORD=` to `.env.example` with the same "why this must be set"
treatment `COOKIE_SECURE` received, and drop the `:-admin` fallback so an unset value fails
the container start instead of opening it.

Also worth a one-line correction while in `nginx.conf.template`: the new HSTS comment claims
the header prevents the cookie from crossing the *first* request in plaintext. It does not —
HSTS is only consulted on subsequent navigations, and the first-request gap is closed by the
`return 301` at line 15, not by the header. The header is correct and correctly placed; the
stated reason is not.

---

_Reviewed: 2026-08-23T14:20:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
