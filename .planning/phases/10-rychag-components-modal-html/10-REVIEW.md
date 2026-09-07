---
phase: 10-rychag-components-modal-html
reviewed: 2026-09-07T20:45:00Z
depth: standard
files_reviewed: 35
files_reviewed_list:
  - app/pages/account_groups.py
  - app/pages/accounts.py
  - app/pages/admin.py
  - app/pages/ads.py
  - app/pages/common.py
  - app/pages/history.py
  - app/pages/htmx.py
  - app/pages/schedules.py
  - app/templates/account_groups/includes/group_row.html
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/ads/form.html
  - app/templates/ads/includes/ad_card.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/includes/sched_count_rule.html
  - app/templates/ads/partials/sched_delete_response.html
  - app/templates/components/form_wrapper.html
  - app/templates/components/modal.html
  - app/templates/history/includes/history_card.html
  - app/templates/includes/notice_area.html
  - tests/test_pages/test_confirm_delete_transport.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_response_layer.py
  - tests/test_pages/test_hx_location_destinations.py
  - tests/test_pages/test_impersonation.py
  - tests/test_pages/test_notices_channel.py
  - tests/test_pages/test_origin_guard_on_destructive_routes.py
  - tests/test_planning/test_planning_gates_are_independent_of_the_live_verdict.py
  - tests/test_planning/test_requirement_completion_follows_verification.py
  - tests/test_planning/test_the_walkthrough_cannot_self_certify.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
findings:
  critical: 1
  warning: 7
  info: 4
  total: 12
status: issues_found
---

# Phase 10: Code Review Report (fifth round)

**Reviewed:** 2026-09-07
**Depth:** standard
**Files Reviewed:** 35 (8 page-layer modules, 12 templates, 15 suite modules)
**Status:** issues_found

## Summary

The fourth batch (plans 10-17…10-23) does what it says on the four routes it
names: `is_same_origin` now stands on `accounts_delete`, `account_groups_delete`,
`ads_delete` and `schedules_delete`; `ID_MAX` bounds five inputs of
`app/pages/schedules.py`; `_editor_url` takes a computed predicate instead of
re-reading `return_to`; the `#sched-count` markup has one source.

The review therefore went after two things: what the batch **generalised to one
module and did not generalise to its siblings**, and what the record asserts that
the code does not execute. Both produced findings.

The headline is CR-01, which is **reproduced, not inferred**: the identical
"out-of-range identifier answers with a handler failure" defect the phase closed
as `CR-01`/`CR-02` on `schedules.py` is still live on the other three confirmed
deletion routes, on the group toggle and on the ad editor POST. On production
PostgreSQL the threshold is 2 147 483 648 — far below the value the suite's
SQLite tolerates — so the suite cannot see the production failure even if a case
were added naively.

Recorded closures (`WR-03` validation-refusal transport, `WR-04` empty landing
region, `WR-02`/`WR-05` static `#sched-count` target, the guard's admitted
no-header boundary) are **not** re-reported. Where I dispute a recorded decision
it is labelled as a challenge (WR-04, WR-05 below).

---

## Critical Issues

### CR-01: Out-of-range identifiers still answer 500 on three of four deletion routes — the phase generalised the fix to one module only

**Files:**
- `app/pages/ads.py:735` (`ads_delete`, `ad_id: int`)
- `app/pages/accounts.py:997` (`accounts_delete`, `account_id: int`)
- `app/pages/account_groups.py:595-596` (`account_groups_delete`, `account_id: int`, `group_id: int`)
- `app/pages/account_groups.py:423-424` (`account_groups_toggle`)
- `app/pages/ads.py` (`ads_update`, `POST /ads/{ad_id}/edit`)
- `app/pages/history.py` (`history_retry`, `POST /history/{log_id}/retry`)
- Gate scope: `tests/test_pages/test_editor_schedules.py:2023` (`UNBOUNDED_ROUTE_CASES` — schedules only)

**Issue:**

`app/pages/schedules.py:73-96` declares `ID_MAX = 2_147_483_647` with an explicit,
correct rationale: the value is the **upper bound of the identifier COLUMN**, the
three models involved (`Ad`, `Schedule`, `MessengerAccount`) all declare the same
plain `Mapped[int]` primary key, and a value outside it "cannot belong to any row
on either of the project's two drivers"; letting it reach the driver ends in
HTTP 500 on a well-formed POST.

Every word of that rationale applies verbatim to `Ad.id`, `MessengerAccount.id`,
`Group.id` and `SendLog.id` on the sibling routes — and none of them is bounded.
The phase's own plan 10-18 grouped exactly these four handlers into one family
("маршруты подтверждённого удаления пользовательских данных") for the origin
guard, then plan 10-12 bounded one member of that family and left the other three.

Measured on the current tree (cookie-authed page client, in-memory SQLite):

```
POST /ads/99999999999999999999999999/delete                  -> 500
POST /accounts/99999999999999999999999999/delete             -> 500
POST /accounts/1/groups/99999999999999999999999999/delete    -> 500
POST /accounts/1/groups/99999999999999999999999999/toggle    -> 500
POST /schedules/99999999999999999999999999/delete            -> 422   <- bounded
POST /history/99999999999999999999999999/retry               -> 500
POST /ads/99999999999999999999999999/edit                    -> 500
```

Underlying cause confirmed directly:

```
>>> await db.execute(select(Ad).where(Ad.id == 99999999999999999999999999))
RAISED: OverflowError  Python int too large to convert to SQLite INTEGER
```

**Production is strictly worse than the test bed.** The primary keys are
`INTEGER` (int4) on PostgreSQL, so `2147483648` — a value SQLite accepts
silently — raises `DataError: integer out of range` in asyncpg and ends in the
same 500. A regression case written against the suite's SQLite would have to use
a value above 2^63 to go red, i.e. the suite cannot observe the production
boundary at all. This is precisely why `ID_MAX` was pinned to the *column*
bound in `schedules.py`, and precisely why the same constant must guard the
siblings.

Additionally, the guard that *is* present is downstream of the crash on
`account_groups_delete`: the origin refusal at `account_groups.py:691` is never
reached for an out-of-range `group_id`, because FastAPI's `int` coercion succeeds
and the failure happens later in SQLAlchemy — an unauthenticated-origin caller
can therefore still drive the route to a 500.

**Fix:**

Move the bound and its three aliases out of `app/pages/schedules.py` into a
neutral module (both the page layer and any future JSON route depend on it, it
depends on neither), then apply them at the application boundary on every page
route that takes an identifier:

```python
# app/pages/identifiers.py  (new, neutral)
from typing import Annotated
from fastapi import Form, Path

# Верхняя граница КОЛОНКИ идентификатора (int4) — одна на проект, а не на файл.
ID_MAX = 2_147_483_647

IdPath = Annotated[int, Path(ge=1, le=ID_MAX)]
IdForm = Annotated[int, Form(ge=1, le=ID_MAX)]
OptionalIdForm = Annotated[int | None, Form(ge=1, le=ID_MAX)]
```

```python
# app/pages/ads.py
async def ads_delete(request: Request, ad_id: IdPath, ...):

# app/pages/accounts.py
async def accounts_delete(request: Request, account_id: IdPath, ...):

# app/pages/account_groups.py
async def account_groups_delete(request: Request, account_id: IdPath, group_id: IdPath, ...):
async def account_groups_toggle(request: Request, account_id: IdPath, group_id: IdPath, ...):
```

Then widen the gate so the next unbounded input cannot appear silently. Today
`test_no_schedule_route_answers_with_a_handler_failure_on_an_out_of_range_identifier`
iterates a hand-written five-entry list scoped to one module; replace the list
with an `ast` walk of the whole of `app/pages/`, in the shape the phase already
uses in `test_origin_guard_on_destructive_routes.py`:

> every route handler in `app/pages/` that declares an `int`-typed path
> parameter must declare it through the bounded alias; the count of such
> parameters is asserted against a declared number so a broken parser greens on
> the empty set.

Note that `ID_MAX`'s own docstring already claims the bound covers "все три
идентификатора, участвующие в маршрутах этого файла" — leave that wording alone
but delete the implication (carried by the `CR-02` retraction block at
`schedules.py:340-357`) that the *route family* is closed: it is closed for one
of its four members.

---

## Warnings

### WR-01: `history.py` still carries the consumer count that `common.py` retracted by measurement in this same batch

**File:** `app/pages/history.py:913-916`

**Issue:** The batch's plan 10-18 explicitly retracted the "three consumers" claim
in `app/pages/common.py:707-717`, naming the measurement:

> ЗАМЕР (2026-09-05, `grep -rn 'is_same_origin' app/`) дал ЧЕТЫРЕ
> файла-потребителя и ДЕВЯТЬ мест вызова … план 10-18 … довёл число до ВОСЬМИ
> файлов и тринадцати мест вызова

The identical claim survives untouched three files away, inside a function this
phase edited:

```python
# app/pages/history.py:913-916
# Гард источника — ОБЩИЙ на проект (app/pages/common.py). Здесь он жил
# приватной копией с плана 04-10: тогда потребитель был один. С появлением
# форм оплаты потребителей стало три, и копия правила означала бы, что
# правку одного гарда придётся не забыть повторить в другом.
```

Re-measured on the current tree: **8 files, 13 call sites** —
`accounts.py:1031`, `account_groups.py:691`, `ads.py:773`, `billing.py:305`,
`admin.py:903/1100/1637/1738/1819/1867`, `auth.py:476`, `history.py:917`,
`schedules.py:1066`. The comment is off by a factor of four. This is the phase's
own declared defect class (the record asserting more than the code carries), left
in place by the very plan that retracted its twin.

**Fix:** replace the count with the pointer the retraction already established —
the two gates hold completeness, not a list:

```python
# Гард источника — ОБЩИЙ на проект (app/pages/common.py). Здесь он жил
# приватной копией с плана 04-10; копия снята планом 05-04. Числа
# потребителей здесь НЕ ведутся — их держат гейты полноты, названные в
# докстринге самого гарда: перечень, который надо не забыть исправить,
# забывают (доказано этой самой строкой, разошедшейся вчетверо).
```

### WR-02: the four new guard blocks claim "before any database access" while two reads have already happened

**Files:** `app/pages/accounts.py:1025-1030`, `app/pages/ads.py:767-772`,
`app/pages/account_groups.py:686-690`, `app/pages/schedules.py:1060-1065`

**Issue:** All four carry the same header, verbatim:

> СВЕРКА ИСТОЧНИКА — ПОСЛЕ ПРАВ И ДО ЛЮБОГО ОБРАЩЕНИЯ К БАЗЕ

The guard runs after `get_user_from_cookie(...)`, which issues `db.get(User, sub)`
(`app/pages/common.py:574`) and, when a token carries an actor, a second
`db.get(User, actor_id)` (`common.py:579`). So a cross-origin POST with a stolen
cookie still costs one or two primary-key reads before it is refused. The
*intended* claim ("before the target row is read") is true and worth keeping; the
written claim is false, and it is replicated four times, which is exactly how the
`is_same_origin` consumer list drifted in the first place.

**Fix:** state the true boundary and stop repeating it four times — put it once
next to `is_same_origin` and reference it:

```python
# СВЕРКА ИСТОЧНИКА — ПОСЛЕ ПРАВ И ДО ЧТЕНИЯ ЦЕЛЕВОЙ СТРОКИ. Чтение субъекта
# (и действующего лица) к этому моменту уже произошло внутри
# get_user_from_cookie: сверка стоит выше ВЫБОРКИ ПРЕДМЕТА, а не выше базы
# вообще. Отказ по происхождению не имеет права стать признаком
# существования строки.
```

### WR-03: the new gate justifies itself with a false statement about the project's cookie policy

**File:** `tests/test_pages/test_origin_guard_on_destructive_routes.py:310-320`
(docstring of `test_every_destructive_route_checks_the_origin`)

**Issue:** The rationale reads:

> …одна политика браузера без единого рубежа за ней … **Правило продукта не
> имеет права зависеть от умолчания, которое продукт не выставляет и не
> проверяет.**

The product *does* set it, explicitly and in one place:

```python
# app/pages/auth.py:88-95
return {
    ...
    "samesite": "lax",
    "secure": settings.cookie_secure,
}
```

`_session_cookie_attrs` is the single source for both `set_session_cookie` and
`clear_session_cookie`, so `SameSite=Lax` is a declared product attribute, not a
browser default the project is riding on. The conclusion (defence in depth is
still right) survives; the stated *fact* does not, and it is the load-bearing
sentence of the gate that admits requests carrying neither header. A reader who
believes the docstring will over-estimate what the guard buys.

**Fix:**

```
⚠️ ПОЧЕМУ ЭТОГО НЕ ЗАМЕНЯЕТ `samesite="lax"`. Признак ВЫСТАВЛЕН продуктом
явно и в одном месте (`app/pages/auth.py`, `_session_cookie_attrs`), и
межсайтовый POST он действительно не пропускает. Довод гарда — не
«умолчание не выставлено», а ГЛУБИНА: политика cookie есть ОДИН рубеж, она
снимается сменой набора атрибутов в одной строке и не различает
одноимённый источник иной схемы или иного порта, который эта функция
пропускает по записанному решению. Серверная сверка есть второй рубеж, а не
замена первому.
```

### WR-04: gate G-2 is blind to the response the batch introduced — `Response(status_code=403)` is a second, unrecorded response decision inside converted handlers

**Files:** `tests/test_pages/test_htmx_gates.py:650-679` (`_builds_own_redirect`),
`app/pages/htmx.py:1-9` (module docstring), the four guard sites listed in WR-02

**Issue:** `app/pages/htmx.py` opens with

> Слой ответа: **единственное место, где приложение решает, ЧЕМ отвечать.**

and G-2 (`test_no_converted_handler_builds_its_own_redirect`) exists to keep that
true: "у переведённого обработчика НЕ остаётся второго решения о форме ответа".

Its detector only recognises `RedirectResponse(...)`, `status_code=302` and
`status.HTTP_302_*`. The batch added, inside four handlers that are on the
response layer, a raw

```python
return Response(status_code=403)
```

which is a second, independent decision about the response form, invisible to the
gate. Behaviourally the consequence is small but real: on the htmx transport an
empty 403 is not swapped by the runtime, `x-on:htmx:after-request` sees
`successful === false` and leaves the confirmation panel open with no message —
the human sees a dead button. That transport-shaped divergence is the same class
the response layer was built to abolish.

This is **not** covered by the recorded `WR-03` closure: that registry
(`VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 7`,
`tests/test_pages/test_htmx_gates.py:2570`) is scoped to *framework validation
refusals*, and an application-authored 403 is not one.

**Fix (pick one, but pick explicitly):**

1. Widen the detector so the gate can see it, and add the four sites to a named
   divergence registry with grounds, in the same shape as the validation-refusal
   registry:

```python
def _builds_own_response(function: ast.AST) -> bool:
    for node in ast.walk(function):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            if name in {"RedirectResponse", "Response", "JSONResponse", "PlainTextResponse"}:
                return True
    return False
```

2. Or route the refusal through the layer so there is genuinely one exit, e.g.
   `raise HtmxRefusal(...)` / `respond(request, redirect=..., notice=...)` with a
   registry code for "источник запроса не подтверждён".

Silently keeping both the "single place" claim and four exits that bypass it is
the option to avoid.

### WR-05 (challenge to a recorded decision): the CSRF guard's universe is `/delete` + admin; 23 of 36 mutating page routes are covered by neither the guard nor any completeness gate

**Files:** `app/pages/common.py:695-751` (the "РАМКИ" and "ГЕЙТОВ ПОЛНОТЫ ТЕПЕРЬ
ДВА" paragraphs), `tests/test_pages/test_origin_guard_on_destructive_routes.py:38-40`

**Issue:** I am not re-reporting the guard's admitted no-header boundary. I am
challenging the *completeness claim* the batch wrote around it.

`is_same_origin`'s docstring states its subject as "изменяющий запрос" and cites
ASVS L1 V4.2.2 — protection of **state-changing** requests — then says
completeness is held by two machine gates. Measured universes of those gates:

* `test_every_mutating_admin_route_checks_the_origin` — all mutating routes of `app/pages/admin.py`;
* `test_every_destructive_route_checks_the_origin` — POST + path suffix exactly `/delete`, admin module exempted.

Their union covers 13 of the 36 POST handlers the sibling gate itself counts
(`POST_HANDLERS = 36`, `test_htmx_gates.py:153`). The 23 outside include:

| route | effect of a forged cross-site POST |
|---|---|
| `POST /ads/{ad_id}/edit` | rewrites the body/images of an ad that is then broadcast to the user's groups |
| `POST /schedules/{schedule_id}/toggle` | arms or disarms a broadcast |
| `POST /schedules/{schedule_id}/edit`, `/schedules/new` | rewrites/creates a broadcast schedule |
| `POST /accounts/{id}/groups/{gid}/toggle` | changes which groups receive ads |
| `POST /accounts/{id}/sync-groups`, `/retry-sync` | drives messenger side effects |
| `POST /profile` | rewrites profile fields |

Rewriting the content that gets broadcast is not obviously less serious than
deleting it, yet the `/delete` suffix is what decides membership. `SameSite=Lax`
(WR-03) does carry these today — which is why this is a WARNING and not a
BLOCKER — but that is exactly the single-rubicon argument the batch rejected for
the four routes it did guard. The record as written ("полноту держат ДВА
МАШИННЫХ ГЕЙТА") reads, against a docstring whose declared subject is *all*
state-changing requests, as though the surface were closed. It is closed for
`/delete` + admin.

**Fix:** either widen the second gate's criterion from "path ends in `/delete`"
to "handler is a POST route in `app/pages/` that commits" (with a named,
counted exemption list for the auth/registration routes, which cannot carry the
guard), or — cheaper and honest — bound the claim in `common.py`:

```
⚠️ ГРАНИЦА ВСЕЛЕННЫХ ОБОИХ ГЕЙТОВ НАЗВАНА ЧИСЛОМ. Вместе они накрывают 13
изменяющих маршрутов страничного слоя из 36 (замер `ast` по `app/pages/`,
2026-09-07): ВСЕ изменяющие админки и POST-маршруты с путём на `/delete`.
Остальные 23 — правка объявления, тумблеры расписания и группы, синхронизация,
профиль, вход и регистрация — серверного рубежа НЕ несут и держатся
`samesite="lax"`. Это принятое состояние вехи 2.1, а не свойство полноты:
перевод «правило продукта не зависит от одной политики браузера» на них
отложен фазой N с основанием X.
```

### WR-06: the out-of-band notice path (`_glue_notice` / `_notice_oob`) has no production caller, while `respond()`'s docstring presents it as a closed guarantee

**File:** `app/pages/htmx.py:209-283`, `app/pages/htmx.py:355-361`

**Issue:** `respond()` declares:

> ⚠️ КОД ИСХОДА ДОЕЗЖАЕТ И НА ВЕТКЕ ФРАГМЕНТА — ВНЕПОЛОСНЫМ БЛОКОМ … **Граница
> закрыта** … Без этого исход действия был бы виден только тому, кто получил
> редирект, — то есть каналом пользовался бы лишь один из двух транспортов.

Measured: every call in `app/` that passes `fragment=` passes `notice=None`
(`account_groups.py:589`, `account_groups.py:826`, `schedules.py:1263`), and no
call passes both. `_glue_notice`, `_notice_oob`, `NOTICE_OOB_TEMPLATE` and
`app/templates/includes/notice_oob.html` are reachable from the test suite only.
So the sentence describes a capability, not a behaviour: on the fragment
transport the outcome channel is used by zero handlers, and "граница закрыта" is
false as a statement about the running product.

Two secondary defects in the same block, both currently unreachable but both
waiting for the first real caller:

* `_glue_notice` does not check the status code. A fragment answering `204`/`304`
  would get a body appended and a `content-length` header, producing a protocol
  violation rather than a loud failure. The function is careful about media type
  and about recomputing length — status is the third invariant of the same rule.
* `response.body = ...` mutates a response object the caller may already have
  registered background tasks or headers on; it is safe today only because all
  three fragment builders return a freshly constructed `HTMLResponse`.

**Fix:** narrow the claim to what runs, and keep the mechanism honest:

```
⚠️ КОД ИСХОДА СПОСОБЕН ДОЕХАТЬ И НА ВЕТКЕ ФРАГМЕНТА — ВНЕПОЛОСНЫМ БЛОКОМ, НО
СЕГОДНЯ ЭТИМ НЕ ПОЛЬЗУЕТСЯ НИ ОДИН ОБРАБОТЧИК: все три фрагментных вызова
подают `notice=None` (D-03, плашки на успех нет). Механизм заведён и покрыт
суитой заранее; ПОВЕДЕНИЕМ он станет с первым фрагментом, несущим отказ.
```

and add the status guard next to the media-type guard in `_glue_notice`:

```python
if response.status_code in (204, 205, 304) or response.status_code < 200:
    raise ValueError(
        "внеполосный блок нельзя приклеить к ответу без тела по определению "
        f"статуса ({response.status_code}): ответ ушёл бы с телом, которого "
        "его статус запрещает"
    )
```

### WR-07: the new planning gates couple `just test` to `.planning/*.md` and to template anchors

**Files:** `tests/test_planning/test_the_walkthrough_cannot_self_certify.py:45-52,
696-762`, `tests/test_planning/test_planning_gates_are_independent_of_the_live_verdict.py`,
`tests/test_planning/test_requirement_completion_follows_verification.py`

**Issue:** ~2 200 lines of new suite code assert over `.planning/` markdown and,
in `test_every_walkthrough_anchor_exists_in_its_source_template`, over
`app/templates`. Two concrete coupling consequences:

* `WALKTHROUGH_ANCHORS_DECLARED = 20`: renaming a DOM id or a CSS hook in
  `app/templates` reddens a **planning-document** gate. A frontend change and a
  documentation change are now the same failure, and the failure names the wrong
  artefact.
* `MARKED_FORM_EXEMPT_DECLARED = 11`, `DECLARED_COUNT_EXEMPT_DECLARED = 12`,
  `TERMINAL_STATES_DECLARED = 2`, `WALKTHROUGH_ANCHORS_DECLARED = 20`: four
  hand-maintained counts over documents that the workflow edits routinely, so
  the product suite goes red on ordinary bookkeeping. That is the pressure that
  gets a whole directory added to `--ignore`, taking the real gates with it.

This is a maintainability judgement, not a correctness one — the project does
treat planning artefacts as source. But the anchor rule in particular reaches
*out of* `.planning/` into product templates, which none of the other planning
gates do.

**Fix:** move `test_every_walkthrough_anchor_exists_in_its_source_template` out
of `tests/test_planning/` into `tests/test_templates/`, where a template rename
reddening it names the artefact the reader actually changed; and mark the
`tests/test_planning/` package with a pytest marker (`@pytest.mark.planning`)
so the product suite and the record suite can be run and diagnosed separately
without either being deleted.

---

## Info

### IN-01: `is_same_origin` compares `None == None` when both sides are hostless

**File:** `app/pages/common.py:753-759`

`urlsplit("null").hostname` is `None` (browsers send `Origin: null` from
sandboxed iframes, `data:` documents and some cross-origin redirect chains). If
`request.url.hostname` were also `None` — no `Host` header and no `server` in the
ASGI scope — the comparison yields `True` and the request is admitted through the
`Origin` branch rather than through the documented no-header branch. Not
reachable behind the project's nginx, but it is a silent widening of a boundary
the module documents precisely.

**Fix:**

```python
origin = request.headers.get("origin")
if origin:
    origin_host = urlsplit(origin).hostname
    return origin_host is not None and origin_host == request.url.hostname
```

### IN-02: dead disjunct in the modal's after-request handler

**File:** `app/templates/components/modal.html:716`

```
if ($event.detail.successful || ($event.detail.xhr && $event.detail.xhr.getResponseHeader('HX-Location'))) hide()
```

The runtime marks 2xx/3xx — including the `204` that `location_response()`
returns — as `successful`, so the second disjunct can only fire on a 4xx/5xx that
also carries `HX-Location`, which nothing in the tree produces. The extra term
reads as though the 204 transition path needed special handling; it does not.
Either delete it or annotate it as a deliberate belt-and-braces for a future
refusal-with-redirect.

### IN-03: `is_same_origin` is 7 lines of code under 86 lines of docstring, six of which are retraction chains

**File:** `app/pages/common.py:666-759`

The D-30/D-32 "record, do not erase" idiom is sound, but this docstring now
contains three separate paragraphs about the *same* retracted consumer list
(`⚠️ РАМКИ`, `⚠️ ПРЕЖНЕЕ ПЕРЕЧИСЛЕНИЕ…`, `⚠️ ПЕРЕЧЕНЬ ПОТРЕБИТЕЛЕЙ ЗДЕСЬ БОЛЬШЕ НЕ
ВЕДЁТСЯ`), two of which say the same thing with different wording. WR-01 shows
the practical cost: a reader who has to hold three overlapping retractions in
mind is exactly the reader who misses the fourth copy living in another file.
Consider collapsing superseded retractions of one predicate into a single dated
entry once the finding that produced them is closed.

### IN-04: `_ad_id_from_form`'s docstring carries two live retractions of its own paragraphs

**File:** `app/pages/schedules.py:277-380`

103 lines of docstring over 6 lines of code, containing `(г) ⚠️⚠️ ОПРОВЕРГНУТО
(CR-02)` inside a list whose item `(д)` corrects it, plus a separate `⚠️⚠️
ОПРОВЕРГНУТО (CR-01)` near the top that forward-references "верная формулировка в
конце докстринга". A reader has to hold two corrections and their ordering to
learn one fact: the helper bounds a context field, not the route. Same
observation as IN-03 — the idiom is right, the accumulation is now costing more
than it records.

---

## Verified and not reported

For the record, so the next round does not re-litigate them:

* Ownership scoping on all four deletion routes is correct — `delete_account`
  filters on `MessengerAccount.user_id`, `ads_delete` on `Ad.user_id`,
  `account_groups_delete` keeps the triple `WHERE`, `schedules_delete` joins
  `Ad.user_id`; `_ad_has_a_schedule` and `_ad_schedule_count` both scope by
  `Ad.user_id`, so the `WR-02` counter case cannot cross a privilege boundary.
* `_local_path` correctly rejects scheme-relative, backslash, control-character
  and non-ASCII redirect targets on both transports, including the anchor-aware
  `_with_notice` path added by this batch.
* The `modal(id=...)` attribute-name contract holds: all 14 call sites pass
  server-chosen integers, including `queue_drop_modal_id` (`queue-drop-{id}-{index}`).
* `body=ad.title` and the `parts | join(' · ')` panel body are attribute/text
  positions under Jinja autoescape — no XSS.
* The `destroy()` / `hide()` focus-return pair is correct for the OOB-delete
  path: htmx swaps before `htmx:afterRequest`, so the panel's listener is already
  gone and Alpine's `destroy()` is what actually lands focus.
* The `is_same_origin` no-header admission, the raw-body validation refusal
  (`WR-03`), the always-empty landing region (`WR-04`) and the static
  `#sched-count` target (`WR-02`/`WR-05`) are recorded closures and are not
  re-reported.

---

_Reviewed: 2026-09-07_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
