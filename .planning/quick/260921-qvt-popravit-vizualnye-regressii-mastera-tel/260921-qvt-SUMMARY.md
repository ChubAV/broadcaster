---
phase: quick-260921-qvt-tg-wizard-visual-regressions
plan: 01
subsystem: ui
status: complete
tags: [telegram, wizard, css, htmx, regression]
requires: []
provides:
  - "Внутренняя колонка connect-step__form на шаге пароля 2FA (UI-1)"
  - "Правило .connect-step--center .connect-step__actions { justify-content: center } (UI-2)"
  - "Подпись span.connect-step__busy «Загрузка...» с показом по button[type=submit][disabled] (UI-3)"
  - "Регрессия tests/test_templates/test_tg_connect_step_layout.py"
affects: [accounts/connect/tg_user]
tech-stack:
  added: []
  patterns:
    - "Показ состояния запроса через атрибут disabled цели блокировки hx-disabled-elt и комбинатор ~, без JS"
key-files:
  created:
    - tests/test_templates/test_tg_connect_step_layout.py
  modified:
    - app/templates/accounts/includes/tg_connect_step.html
    - app/static/css/app.css
decisions:
  - "Подпись загрузки мастера TG показывается по атрибуту disabled кнопки отправки (цель блокировки form_wrapper по умолчанию), а не по классу запроса htmx: индикатор обёртки уводит класс на узел точки"
  - "Подпись скрыта через display: none, поэтому порога 300 мс у неё нет; порог D-15 остаётся у точки индикатора"
requirements-completed: [QUICK-13-UI-1, QUICK-13-UI-2, QUICK-13-UI-3]
metrics:
  duration: "15 min"
  started: "2026-09-21T19:48:20Z"
  completed: "2026-09-21T20:03:00Z"
  tasks: 2
  files: 3
actuals:
  tokens: 4900
  tasks: 2
  commits: 2
plan_head_before: 316e7e956fa04d02da5d77efda8f982b98f47b27
coverage:
  - id: D1
    description: "UI-1: поле «Пароль 2FA» и «Подтвердить» лежат во внутренней колонке connect-step__form с промежутком шага (14px) на первом показе и на 422"
    requirement: QUICK-13-UI-1
    verification:
      - kind: unit
        ref: "tests/test_templates/test_tg_connect_step_layout.py#test_the_password_step_keeps_its_field_and_button_in_one_column"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_tg_user_auth.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "UI-2: ряд «Обновить QR-код» / «Отмена» на шаге «QR-код истёк» центрирован правилом .connect-step--center .connect-step__actions"
    requirement: QUICK-13-UI-2
    verification:
      - kind: unit
        ref: "tests/test_templates/test_tg_connect_step_layout.py#test_a_centered_step_centers_the_actions_nested_in_its_form"
        status: pass
    human_judgment: false
  - id: D3
    description: "UI-3: span.connect-step__busy «Загрузка...» после «Отмена» на старте, ошибке и qr_expired; показ по button[type=submit][disabled]; других шагов подпись не касается"
    requirement: QUICK-13-UI-3
    verification:
      - kind: unit
        ref: "tests/test_templates/test_tg_connect_step_layout.py#test_start_and_refresh_show_a_busy_label_while_the_button_is_disabled"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_tg_connect_step_layout.py#test_no_other_step_carries_the_busy_label"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_tg_connect_step_layout.py#test_the_busy_label_is_keyed_on_the_disabled_button_not_on_the_form"
        status: pass
    human_judgment: false
  - id: D4
    description: "Зрительная приёмка в живом браузере на /accounts/connect/tg_user: (1) «Загрузка...» справа от «Отмена», пока кнопка отключена, и исчезает с ответом; (2) пара кнопок qr_expired по центру; (3) промежуток между полем 2FA и «Подтвердить», в том числе после 422. Отметки ставит владелец."
    verification: []
    human_judgment: true
---

# Phase quick-260921-qvt Plan 01: Visual regressions in the Telegram QR wizard, summary

Three fixes in the Telegram QR wizard. The 2FA step now puts its field and button in an inner `connect-step__form` column, so the 14px gap is back. The actions row on centered steps is centered inside the stretched form. The start and refresh steps show a "Загрузка..." label, keyed purely in CSS on the `disabled` attribute that htmx sets on the submit button. No script was added.

## What was done

- **Task 1 (UI-1, UI-2), commit `85e84ca3`.**
  - `tg_connect_step.html`, `password` branch: the `session_id` hidden field stays the first child of the form. The `field(...)` call (arguments unchanged) and the `connect-step__actions` row now sit inside a new `<div class="connect-step__form">`.
  - Added a paragraph to the comment explaining why the layout box has to come from the inner node, following the MAX step. The macro's form class is named in words, not as a literal.
  - `app.css`: added `.connect-step--center .connect-step__actions { justify-content: center; }` right after `.connect-step__actions`, with a comment.
- **Task 2 (UI-3), commit `aaaee309`.**
  - Added `<span class="connect-step__busy">Загрузка...</span>` as the last child of the actions row in the start/error branch and in the `qr_expired` branch.
  - The start/error branch has a comment covering three facts: the label keys on `disabled` from the default block target; there is no script (D-11, D-12); the text is the removed script's original label, restored verbatim (D-09).
  - `app.css`: added `.connect-step__busy { display: none; font-size: var(--fs-md); color: var(--text-secondary); }` and `.connect-step__actions > button[type="submit"][disabled] ~ .connect-step__busy { display: inline; }`.
  - The comment on these rules covers DD-1 to DD-3. It names the indicator rules in words, without quoting any `CSS_*` substitution anchor.

Unchanged: `form_wrapper` calls and their arguments, the `waiting` branch and its poller, `connect_tg_user.html`, `app/pages/accounts.py`, `components/form_wrapper.html`, and `.planning/phases/13-*/`. `git diff --name-only 316e7e95 HEAD` lists exactly the three files in `files_modified`.

## TDD: RED and GREEN

All runs used `--junit-xml` into the session scratchpad.

**RED, task 1** (`red1.xml`: tests=3, failures=3):
- `test_the_password_step_keeps_its_field_and_button_in_one_column[None]` and `[Неверный пароль 2FA.]` both failed on assertion (a): `AssertionError: у формы пароля нет ровно одной внутренней колонки div.connect-step__form: промежуток колонки шага до детей тега формы не доходит (UI-1)` / `assert 0 == 1`.
- `test_a_centered_step_centers_the_actions_nested_in_its_form` failed on the rule assertion, after its structural assertions had already passed: `AssertionError: нет правила `.connect-step--center .connect-step__actions`: ряд внутри растянутой формы остаётся у левого края (UI-2)` / `assert None is not None`.

**GREEN, task 1** (`green1.xml`): the new regression file plus `tests/test_routes/test_tg_user_auth.py`, 59 passed, 0 failed. The tracer gate re-ran `<verify>`, which passed.

**RED, task 2** (`red2.xml`: tests=10, failures=4):
- `test_start_and_refresh_show_a_busy_label_while_the_button_is_disabled[start-None]`, `[error-Ошибка]` and `[qr_expired-None]` all failed with `AssertionError: в ряду действий нет ровно одной span.connect-step__busy (UI-3)` / `assert 0 == 1`. The `hx-disabled-elt` assertion before it had already passed.
- `test_the_busy_label_is_keyed_on_the_disabled_button_not_on_the_form` failed on (a): `AssertionError: нет базового правила `.connect-step__busy`` / `assert None is not None`.
- `test_no_other_step_carries_the_busy_label` (3 cases) passed before the change, as planned, because it guards scope. The task 1 tests (3) stayed green.

**GREEN, task 2**: the regression file has 10 tests (5 functions, parametrized), all passing.

## Gate sweep on the final tree (HEAD `aaaee309`)

| Command | Result |
|---|---|
| `pytest` on the 8 files (the layout regression, `test_tg_user_auth`, `test_htmx_markup_gates`, `test_htmx_inventory`, `test_components`, `test_htmx_gates`, `test_htmx_post_pairs`, `test_hx_location_destinations`) | 390 passed, exit 0, 152 s |
| `pytest tests/test_pages/test_responsive_markup.py -k connect` | 2 passed, exit 0 |
| `pytest tests/test_pages/test_shell.py` (in the background) | 245 passed, exit 0, 703 s. This is the first `~` selector in app.css, and the shell's parser handled it. |
| `pytest tests/test_planning/` | 44 passed, exit 0 |
| `graphify update .` | exit 0 (`graphify-out/` is not versioned) |

No gate registry, count or set was changed: `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED = 19`, `POLLING_CASES`, `STEP_MARKS` and the declared indicator set are all as they were.

## Rendered markup (`_tg_step_markup`, abridged)

```
== start / error
<form ... class="form-wrapper" ... hx-disabled-elt="find button[type=submit]" hx-indicator="find .form-busy">
    <div class="connect-step__actions">
      <button class="btn btn--primary" type="submit">…Начать подключение | Начать заново…</button>
      <a class="btn btn--ghost" href="/accounts">…Отмена…</a>
      <span class="connect-step__busy">Загрузка...</span>
    </div>
  <span class="form-busy" aria-hidden="true"></span>
</form>
== qr_expired
<form ... action="/accounts/connect/tg_user/refresh-qr" ...>
      <input type="hidden" name="session_id" value="s">
      <div class="connect-step__actions">
        <button ... type="submit">…Обновить QR-код…</button>
        <a class="btn btn--ghost" href="/accounts">…Отмена…</a>
        <span class="connect-step__busy">Загрузка...</span>
      </div>
  <span class="form-busy" aria-hidden="true"></span>
</form>
== password
<form ... action="/accounts/connect/tg_user/verify-2fa" ...>
      <input type="hidden" name="session_id" value="s">
      <div class="connect-step__form">
        <label class="field" for="password">… <input … name="password" id="password" value="" …></label>
        <div class="connect-step__actions">
          <button ... type="submit">…Подтвердить…</button>
        </div>
      </div>
  <span class="form-busy" aria-hidden="true"></span>
</form>
```

## Deviations from Plan

None. The plan was executed as written. The line numbers, selectors and helper signatures given in `<interfaces>` all matched the code at 316e7e95.

## Known Stubs

None.

## Human verification

The live-browser check is item D4 in `coverage` (`human_judgment: true`, empty `verification`). The machine checks above confirm the markup and style rules. They do not stand in for accepting the visual result.

## Self-Check: PASSED

- FOUND: tests/test_templates/test_tg_connect_step_layout.py
- FOUND: app/templates/accounts/includes/tg_connect_step.html (modified)
- FOUND: app/static/css/app.css (modified)
- FOUND: 85e84ca3
- FOUND: aaaee309
