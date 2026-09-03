---
phase: 10-rychag-components-modal-html
reviewed: 2026-09-03T13:10:00Z
depth: standard
files_reviewed: 23
files_reviewed_list:
  - app/pages/accounts.py
  - app/pages/admin.py
  - app/pages/ads.py
  - app/pages/history.py
  - app/pages/schedules.py
  - app/templates/account_groups/includes/group_row.html
  - app/templates/ads/form.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/includes/sched_count_rule.html
  - app/templates/ads/partials/sched_delete_response.html
  - app/templates/components/form_wrapper.html
  - app/templates/components/modal.html
  - app/templates/includes/notice_area.html
  - tests/test_pages/test_confirm_delete_transport.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_impersonation.py
  - tests/test_pages/test_notices_channel.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
findings:
  critical: 1
  warning: 5
  info: 2
  total: 8
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-09-03T13:10:00Z
**Depth:** standard
**Files Reviewed:** 23
**Status:** issues_found

## Summary

Second review round, after gap-closure plans 10-05..10-07. The round-1 Critical (CR-01: dead
`successful`-only branch on the `HX-Location` transport) is **closed and verified independently**,
not merely claimed:

* I re-traced the vendored runtime (`app/static/js/htmx.min.js`, 2.0.10). `Vn` (handleAjaxResponse)
  early-returns from the `HX-Location` branch — `if(T(n,/HX-Location:/i)){…Nn("get",e,s);return}` —
  and the single `e.successful=!a` assignment sits after it. `xhr.onload` then fires
  `ae(r,"htmx:afterRequest",T)` with the same `T`, whose `xhr` key is assigned at construction
  (`const T={xhr:g,target:u,…}`) and is therefore present on all four dispatch sites
  (`onload`/`onerror`/`onabort`/`ontimeout`). The shipped disjunct
  `$event.detail.successful || ($event.detail.xhr && $event.detail.xhr.getResponseHeader('HX-Location'))`
  is correct on all four, and matches the owner's `location-branch` decision. No status-range
  consolidation is recommended.
* The Node harness now feeds the *real* four event shapes rather than a synthesised
  `{detail:{successful:…}}`, and reproduces key-absence by absence rather than by `false`. The
  negative controls (`test_control_negative_the_successful_only_branch_is_dead_on_the_location_transport`,
  `…_an_unconditional_close_reddens_both_failure_transports`, `…_an_ungated_dismissal_reddens_the_gate`,
  `…_a_shifted_identifier_reddens_the_sameness_check`) genuinely discriminate — each pins a *different*
  observable than the rule it guards, so it cannot go green by construction.
* All nine routes reachable from a `modal()` call site answer through `respond()`; I re-enumerated
  every `modal(...)` caller and mapped every `action=` to its handler. No panel posts over htmx to a
  handler that still answers 302.
* All 253 + 190 tests in the phase's files pass on this tree.

What is **not** clean: one new helper introduced by this phase lets an unbounded integer from the
request body reach a SQL comparison and returns 500 — which is the exact failure class the module's
own contract (T-02-24 / T-02-25) forbids. Beyond that, the fragment/redirect fork in
`schedules_delete` is decided by a *different* predicate than the landing URL, so the two transports
can land on two different screens; and two prose contracts (in `modal.html` and `notice_area.html`)
assert behaviour the code does not have. In a codebase that treats comments as load-bearing
contracts, the last item is a defect class, not a nit.

---

## Critical Issues

### CR-01: `_ad_id_from_form` lets an unbounded integer reach a SQL comparison — 500 on a crafted POST

**File:** `app/pages/schedules.py:249-251` (helper), reached at `app/pages/schedules.py:942`
(`_ad_has_a_schedule`, definition at `:308-325`) and `:329-345` (`_ad_schedule_count`)

`_ad_id_from_form` coerces with a bare `int()`:

```python
try:
    return int(form_data.get("ad_id"))
except (TypeError, ValueError):
    return None
```

Its docstring justifies the coercion as sufficient — *"Коэрция к целому делает поле структурно
неспособным изменить адрес (T-02-23)"* and *"ВЕЛИЧИНА ПОДЧИНЕНА ТЕМ ЖЕ ПРАВИЛАМ, ЧТО И
`_expanded_from_form`, И ПО ТОЙ ЖЕ ПРИЧИНЕ"*. That analogy is exactly where the reasoning breaks:
`_expanded_from_form`'s result only ever lands in a URL string (`?sched=N`), it never reaches the
database. `_ad_id_from_form`'s result is fed straight into `Schedule.ad_id == ad_id`.

`int()` bounds the *type*, not the *magnitude*. Reproduced against the running app (probe removed
after measurement):

```
POST /schedules/999/delete   HX-Request: true
body: return_to=editor&ad_id=9999999999999999999999999

→ 500 {"detail":"Internal server error"}
OverflowError: Python int too large to convert to SQLite INTEGER
  app/pages/schedules.py:942  if not await _ad_has_a_schedule(db, user.id, ad_id):
  app/pages/schedules.py:319  await db.execute(...)
```

On PostgreSQL the same input raises `asyncpg` `DataError` (value out of int32 range) with the same
500. The path is reachable by any authenticated user (the fallback only engages when the addressed
schedule row is not found, which is the *normal* repeat/foreign-id path this phase deliberately made
reachable), and it directly violates the invariant `tests/test_pages/test_editor_schedules.py` states
in its own module docstring: *"прямой POST мимо браузера обязан давать отказ валидации, а не 500
(T-02-24, T-02-25)"*. It also breaks the phase's own indistinguishability property (T-10-01/T-10-07):
a 500 is a fourth, perfectly distinguishable response shape.

No data is damaged — the delete has already been skipped on this branch — but the handler answers
JSON 500 to a form POST, which is the same regression `accounts_sync_groups` documents at length as
unacceptable.

**Fix:** bound the magnitude in the coercion, where the docstring already claims the bound exists.

```python
# app/pages/schedules.py
# Верхняя граница — та же, что у колонки: значение вне диапазона не может
# принадлежать ни одной строке, поэтому отбрасывается ДО запроса, а не роняет
# его драйвером (T-02-24).
_INT32_MAX = 2_147_483_647


def _ad_id_from_form(form_data) -> int | None:
    try:
        value = int(form_data.get("ad_id"))
    except (TypeError, ValueError):
        return None
    if value < 1 or value > _INT32_MAX:
        return None
    return value
```

and add the crafted-input case to the transport gate, next to
`test_a_repeated_confirmed_delete_on_the_fragment_route_answers_the_same_shape`:

```python
@pytest.mark.parametrize("value", ["9" * 25, "-1", "0", "1e3", "1_0"])
async def test_an_unusable_ad_id_never_reaches_the_database(authed_client, value):
    r = await authed_client.post(
        "/schedules/999/delete",
        content=f"return_to=editor&ad_id={value}",
        headers={"Content-Type": "application/x-www-form-urlencoded", "HX-Request": "true"},
    )
    assert r.status_code != 500, f"значение {value!r} доехало до запроса и уронило обработчик"
```

---

## Warnings

### WR-01: `schedules_delete` forks fragment-vs-redirect on a different predicate than the landing URL — the two transports can land on two different screens

**File:** `app/pages/schedules.py:930-1008` (fork at `:942`, URL at `:938`), `app/pages/schedules.py:253-284`
(`_editor_url`)

`_editor_url` returns the editor URL **only** when `form_data.get("return_to") == RETURN_TO_EDITOR`;
otherwise `/schedules`. The fragment/redirect fork one line later asks a completely different
question — `_ad_has_a_schedule(db, user.id, ad_id)` — and never consults `return_to`. So a request
that carries a live `schedule_id` but no `return_to` gets:

* degradation transport → `302 Location: /schedules` (summary list);
* htmx transport → `200` with the **editor** fragment.

Measured on this tree (probe removed after measurement):

```
POST /schedules/{live_id}/delete   HX-Request: true   body: (empty)
→ 200
  <div id="sched-1" hx-swap-oob="delete"></div>
  <div id="sched-del-1" hx-swap-oob="delete"></div>
  <div hx-swap-oob="innerHTML:#sched-count">…1 расписание…</div>
```

None of those three targets exists on `/schedules` (`schedules/list.html` renders
`<p class="sched-count">`, not `#sched-count`), so the htmx client gets three unresolved OOB nodes —
two removals silently dropped with `htmx:oobErrorNoTarget` → `console.error`, and the counter node
lost — and the deleted row stays on screen. This is precisely the divergence class `_editor_url` was
introduced to make impossible: *"Два независимо собранных адреса разошлись бы молча, и путь
деградации уводил бы на сводный список там, где htmx-путь остаётся в редакторе"*. The address is now
built once, but the **branch** is still built twice.

The docstring at `:948-962` argues the branch is unreachable *from the UI* ("в
`app/templates/schedules/` форм удаления нет вовсе") — which I confirmed — but the guard is the
predicate, not the template inventory, and a crafted or field-stripped POST is exactly what the rest
of this module defends against.

**Fix:** make the fork read the same signal the address reads.

```python
# app/pages/schedules.py, in schedules_delete
returns_to_editor = form_data.get("return_to") == RETURN_TO_EDITOR
screen_url = _editor_url(form_data, ad_id)

if not returns_to_editor or not await _ad_has_a_schedule(db, user.id, ad_id):
    return await respond(request, redirect=screen_url)
```

and pin it with a rule next to the existing repeat rule:

```python
async def test_the_fragment_branch_needs_the_editor_flag(authed_client, ...):
    r = await authed_client.post(f"/schedules/{live.id}/delete", content="",
                                 headers={..., "HX-Request": "true"})
    assert r.status_code == 204 and r.headers["HX-Location"] == "/schedules", (
        "без признака возврата htmx-путь получил фрагмент редактора, а путь "
        "деградации ушёл бы на сводный список — две формы одного ответа"
    )
```

### WR-02: the focus-landing payoff documented in `notice_area.html` is unreachable on the transport it was chosen for

**File:** `app/templates/includes/notice_area.html:239-242, 257-258`; `app/templates/components/modal.html:616`
(`land`), `:631` (the close predicate)

`notice_area.html` states the cost/benefit of picking `#notice` as the landing pad:

> ЦЕНА ВЫБОРА НАЗЫВАЕТСЯ ПРЯМО … на УСПЕХЕ область ПУСТА … **На отказном пути он приземляется точно
> на текст отказа, и там выбор окупается целиком.**

Neither half of that sentence holds:

1. `land()` is only ever reached from `hide()` / `destroy()`, and `hide()` on the htmx path is gated
   by `$event.detail.successful || …HX-Location`. On a server refusal the panel deliberately **stays
   open** and `land()` never runs. There is no "refusal path" that lands.
2. Even for outcome codes that do ride a 204, the two error-variant codes a confirmation panel can
   emit — `worker_no_container` and `worker_restart_failed`, both `variant="error"` (verified against
   `app/pages/notices.py`) — render into `#notice-alert`, not `#notice`. `#notice-alert` deliberately
   carries no `tabindex` (asserted by `test_the_landing_region_exists_in_the_shell_of_both_apps`), so
   focus lands on an **empty** `#notice` while the text sits in the sibling region.
3. The same file scopes the whole decision to the fragment transport ("Площадка выбрана для
   ФРАГМЕНТНОГО пути"), and the only two fragment routes emit no notice at all by D-03. So on the one
   transport the pad was chosen for, `#notice` is empty by construction, always.

Behaviour is defensible; the recorded contract is not, and the next reader will "fix" the wrong side
of it.

**Fix:** replace the false clause with the measured one, e.g.

```
⚠️ ЦЕНА ВЫБОРА НАЗЫВАЕТСЯ ПРЯМО: на ФРАГМЕНТНОМ пути область ПУСТА ВСЕГДА — плашка
на успех не выдаётся вовсе (D-03), а на отказе панель не закрывается и приземления
не происходит. Фокус приезжает в осмысленное МЕСТО, но не в осмысленный ТЕКСТ, и
второго варианта у этого пути нет. Записи варианта 'error' едут в СОСЕДНЮЮ область
(#notice-alert), признака фокусируемости у неё нет намеренно, поэтому текстом
отказа площадка не станет ни на одном сегодняшнем маршруте.
```

### WR-03: `modal()` still takes a `method` parameter while `hx-post` is hardcoded — the only effect the parameter can have is to split the two transports

**File:** `app/templates/components/modal.html:608` (signature), `:629-631` (form tag)

```jinja
{% macro modal(id, …, method="post") -%}
<form class="modal__form" method="{{ method }}" action="{{ action }}"
      … hx-post="{{ action }}" …>
```

`hx-post` is a literal; `method` is a caller-settable parameter. A caller passing `method="get"`
would produce a form that GETs without JS and POSTs with htmx — a silent divergence between the two
paths, on a destructive action. Today no caller does (`group_row.html:363` passes `method="post"`,
the other 17 sites omit it), so the parameter is dead weight whose only reachable effect is the
defect.

`components/form_wrapper.html` guards exactly this with two named gates (G-3
`test_every_such_form_keeps_its_method_and_action`, G-4
`test_the_post_attribute_matches_the_action_character_for_character`). The panel — now an 18-site
lever — has an equivalent gate for `hx-post == action`
(`test_the_panel_quality_properties_match_the_form_wrapper` asserts
`values["hx-post"] == values["action"]`) but nothing binds the *verb*.
`test_modal_block_call_keeps_method_and_action` only checks the default rendering.

**Fix:** drop the parameter (it is now unused) and print the literal, matching `form_wrapper`:

```jinja
{% macro modal(id, title, action, confirm_label, body=None, cancel_label="Отмена", confirm_variant="danger") -%}
<form class="modal__form" method="post" action="{{ action }}"
```

then remove `method="post"` from `group_row.html:363` and add the verb to the quality-property set so
the pairing is machine-held rather than remembered.

### WR-04: the panel's `htmx:after-request` handler sits on the `<form>` and will fire for any htmx request raised from inside the block slot

**File:** `app/templates/components/modal.html:631` (handler), `:633` (`{{ caller() }}`)

htmx dispatches `htmx:after-request` / `htmx:afterRequest` with `bubbles: true`. The handler is bound
to the `<form>`, and `{{ caller() }}` renders the block slot **inside** that form. Any htmx-powered
element a future caller puts into the slot (a live search field, a dependent select, a "load more")
will bubble a successful `htmx:after-request` to the form and close the confirmation panel out from
under the user, mid-decision.

Today every slot holds only hidden inputs (`group_row.html:365`, `sched_card.html:282,291`,
`admin/queue.html:148`), so the defect is latent — but nothing forbids it, and the whole point of
this phase is that the macro now hands behaviour to 18 sites at once. The `hx-disabled-elt` /
`hx-include` inventories in `tests/test_templates/test_htmx_markup_gates.py` show the project already
knows how to gate slot contents.

**Fix:** either narrow the handler to the form's own request —

```jinja
x-on:htmx:after-request="if ($event.target !== $el) return; sending = false; …"
```

— or add a slot inventory alongside `_modal_call_kwargs` in `tests/test_templates/test_components.py`
that reddens on any `hx-` attribute appearing inside a `{% call modal(...) %}` body:

```python
def test_no_confirm_panel_slot_carries_a_request_of_its_own():
    offenders = [
        (rel, slot) for rel, slot in _modal_call_slots(_all_templates())
        if re.search(r'\shx-[a-z-]+\s*=', slot)
    ]
    assert not offenders, (
        "слот панели несёт СВОЙ htmx-запрос: его событие завершения всплывёт до "
        f"формы панели и закроет её на чужом обмене — {offenders}"
    )
```

### WR-05: the counter OOB node can overwrite `#sched-count` on the editor of a *different* ad, and the template's own harm inventory omits that case

**File:** `app/pages/schedules.py:964-1002` (`_fragment`),
`app/templates/ads/partials/sched_delete_response.html:73`

The `_fragment` docstring enumerates the harm of an id that resolves to a live node on the wrong
screen, and names exactly two nodes:

> Человек, у которого на экране открыт редактор объявления A, может послать удаление расписания,
> принадлежащего его же объявлению B: строка не найдена в выдаче этого экрана, но узлы снимут со
> страницы A ЖИВЫЕ `#sched-N` и `#sched-del-N`.

The response carries a **third** node. `schedules_count` is computed for the ad that owns the deleted
row (`_ad_schedule_count(db, user.id, ad_id)`), while `hx-swap-oob="innerHTML:#sched-count"` targets
whatever `#sched-count` is in the live document — i.e. ad A's counter gets ad B's number, and it
stays wrong until reload. The reader who trusts the enumeration will believe the counter is safe.

Not a privilege crossing (both ads belong to the same user) and not reachable from the UI, but the
prose is narrower than the behaviour, which is the failure mode this file explicitly guards against
elsewhere ("утверждение о безвредности сужено до правдивого").

**Fix:** extend the enumeration to the third node, and — better — make it structurally true by
closing WR-01, since with `return_to` gating the fork the mismatch can only arise from a hand-crafted
body:

```
… узлы снимут со страницы A ЖИВЫЕ `#sched-N` и `#sched-del-N`, а ТРЕТИЙ узел
перепишет линейку `#sched-count` числом расписаний объявления B: на экране A
встанет чужое число и переживёт запрос до перезагрузки.
```

---

## Info

### IN-01: the `xhr`-presence guard in the close predicate is unreachable in htmx 2.0.10 and no test discriminates it

**File:** `app/templates/components/modal.html:631`

`$event.detail.xhr && …` cannot be false on this runtime: `T` is built with `xhr: g` **before**
`xhr.send()`, and all four dispatch sites (`onload`, `onerror`, `onabort`, `ontimeout`) pass that same
object. The harness agrees — `EVENT_SHAPES.never_completed`
(`tests/test_templates/test_components.py:1858-1866`) also carries an `xhr`, so no shape exercises the
guard's false arm.

Keeping it as a version-drift shim is reasonable, but it is currently untested dead code presented as
a live protection. Either say so where it is written, or add a fifth shape (`{}`, no `xhr`) asserting
the predicate is falsy rather than throwing — that turns the guard from decoration into a measured
property.

### IN-02: two gate assertions measure the wrong thing (a phase name, and prose length)

**File:** `tests/test_pages/test_htmx_gates.py` (`test_every_offset_cursor_exception_carries_a_reason`),
`tests/test_templates/test_htmx_markup_gates.py` (`test_every_allowed_quality_difference_carries_a_reason`)

* `assert "Фаза 11" in exception.lifting_phase` hardcodes the lifting phase into the gate. When the
  exception is re-assigned (Phase 12, 13, …) the gate goes red for a reason unrelated to the property
  it guards, and the natural repair is to loosen it. Assert *non-empty and well-formed* instead
  (`re.fullmatch(r"Фаза \d+", …)`), and keep the specific phase in the record, not in the assertion.
* `assert len(entry.reason.strip()) >= 80` and `assert len(prop.protects.strip()) >= 80` measure
  characters. A padded sentence satisfies them exactly as well as a real justification. This is a
  documented house style, so it is recorded rather than argued — but it is worth knowing that these
  two assertions cannot fail on a bad reason, only on a short one.

---

_Reviewed: 2026-09-03T13:10:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
