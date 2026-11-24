---
phase: 18-ruchnaya-pravka-nomera
plan: 07
subsystem: ui
tags: [css-grid, display-contents, accessibility, refactor, phone-form, tdd, gap-closure]

requires:
  - phase: 18-ruchnaya-pravka-nomera
    provides: "правила формы номера и тест строки шапки (18-02, 18-04), phone_error_response.html (18-08), phone_focus и параметр autofocus макроса field (18-05)"
provides:
  - "раскладка формы номера сеткой: подпись над рядом «поле | кнопка», подсказка под ним, ошибка ещё ниже на всю ширину; кнопка растянута по высоте поля"
  - "на ≤400 px один столбец, кнопка сразу под полем, до подсказки и ошибки"
  - "_phone_form_context: единственное место шести ключей включаемой формы номера (страница, страница 422, оба фрагмента)"
  - "_screen_context с ключевыми-только параметрами, account_id берётся из account.id"
  - "утверждение maxlength поля номера как инварианта 2 * MANUAL_INPUT_MAX_CHARS и > MANUAL_INPUT_MAX_CHARS"
affects: [verify-work-18, phase-18-verification]

actuals:
  tokens: 4200
  tasks: 2
  commits: 3

plan_head_before: ab62fb9bab4b771a323c1612d848bf4c1f0f7279
plan_head_after: 69b0e1c195f6799fd1bf6409bd015a70307b25af

tech-stack:
  added: []
  patterns:
    - "подпись поля display: contents делает детей макроса field ячейками сетки формы; связь подпись-поле остаётся атрибутом for"
    - "один помощник контекста включаемого шаблона вместо ключей, набираемых руками в каждом вызывающем"
    - "предел браузера утверждается через константу сервера (инвариант «двойной запас»), а не литералом"

key-files:
  created: []
  modified:
    - app/static/css/app.css
    - tests/test_pages/test_responsive_markup.py
    - app/pages/account_groups.py
    - tests/test_pages/test_account_phone_form.py

key-decisions:
  - "Сетка вместо выравнивания по низу: совет ревью (flex-start плюс отступ кнопки) отвергнут, потому что высота подписи берётся из normal межстрочного интервала, а кнопка (40 px) и поле (~45 px) разные"
  - "Узкая раскладка в отдельном блоке @media (max-width: 400px) рядом с правилами формы, а не в одном из трёх прежних блоков с тем же условием: правило читается рядом с базовым"
  - "Общий макрос field и прочие формы не тронуты: все правила адресованы [data-acct-phone]; git diff БАЗА..HEAD по components/field.html пуст (код 0)"
  - "account_id внутри _screen_context берётся из account.id; отдельный ключ account_id в литерале словаря снят, его ставит _phone_form_context"

patterns-established:
  - "Ложное утверждение прежнего плана помечается «СНЯТО планом» с причиной (замер обхода), текст прежнего абзаца не стирается"

requirements-completed: [PHONE-09]

coverage:
  - id: D1
    description: "Кнопка «Сохранить» по тексту CSS стоит в одном ряду с полем (область input button), растянута по высоте поля, подпись над рядом, подсказка и ошибка под ним; на ≤400 px один столбец и кнопка сразу под полем; фиксированных ширин у правил формы нет"
    requirement: "PHONE-09"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_the_save_button_shares_the_row_of_the_phone_input"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_the_phone_form_takes_its_own_row_in_the_account_head"
        status: pass
    human_judgment: true
    rationale: "Суита читает текст CSS и не рендерит страницу: совпадение верха и низа кнопки с полем (getBoundingClientRect), положение на 1280, 900, 375 и 320 px в обычном состоянии и после 422, отсутствие обрезки, имя поля в дереве доступности DevTools и фокус по щелчку на подпись подтверждает только обход человеком (/gsd-verify-work 18)"
  - id: D2
    description: "Контекст экрана групп собирает _screen_context с ключевыми-только параметрами; шесть ключей формы номера ставит один помощник _phone_form_context для страницы, страницы 422 и обоих фрагментов; поведение и числа гейтов прежние"
    requirement: "PHONE-09"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_phone_form.py (24 passed)"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py, tests/test_templates, tests/test_pages/test_htmx_gates.py, tests/test_pages/test_htmx_post_pairs.py и телефонные гейты — 2554 passed"
        status: pass
    human_judgment: false
  - id: D3
    description: "maxlength поля номера утверждается инвариантом int(maxlength) == 2 * MANUAL_INPUT_MAX_CHARS и > MANUAL_INPUT_MAX_CHARS, константа из app.services.phone"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_phone_form.py#test_the_screen_carries_the_phone_form_in_the_account_head"
        status: pass
    human_judgment: false

duration: 95min
completed: 2026-11-22
status: complete
---

# Phase 18 Plan 07: Кнопка «Сохранить» в ряду поля и чистка формы номера Summary

**Форма номера раскладывается CSS-сеткой (подпись над рядом «поле | кнопка», подсказка и ошибка под ним, на ≤400 px кнопка сразу под полем), контекст экрана групп и ключи формы собирают `_screen_context` с ключевыми-только параметрами и один `_phone_form_context`, а `maxlength` утверждается инвариантом двойного запаса.**

## Performance

- **Duration:** ~95 min (в основном ожидание общего замка pytest; прогоны 9 и 12 минут)
- **Tasks:** 2 (трассер в цикле RED -> GREEN; чистка отдельным коммитом refactor)
- **Files modified:** 4 (создано 0)

## Accomplishments

- **WR-01 (D-11).** Правило `[data-acct-phone] .form-wrapper` — `display: grid` с областями «label label» / «input button» / «hint hint», столбцы `minmax(0, 1fr) auto`, зазоры 7 px и 8 px; `[data-acct-phone] .field { display: contents }`; кнопка — `grid-area: button; align-self: stretch` (верх и низ — по полю); ошибка — `grid-column: 1 / -1` (ниже подсказки, без пустой строки при её отсутствии). Блок `@media (max-width: 400px)`: один столбец, области «label» / «input» / «button» / «hint», `justify-self: start` у кнопки. Прежний абзац комментария про переносящийся ряд помечен «СНЯТО планом 18-07 (WR-01)» с причиной по замеру обхода.
- **IN-02.** `_phone_form_context(account_id, *, value, error, focus)` — единственное место шести ключей (`account_id`, `phone_value`, `phone_error`, `example_phone`, `phone_maxlength`, `phone_focus`): литерал `_screen_context`, `_page` (`context.update`), `_error_fragment`, `_saved`. `_screen_context` получил ключевые-только параметры (`request, db, settings, user, account, term`); `account_id = account.id`; `screen_title` — в литерале. Присваиваний `context["phone_*"] =` после литерала больше нет (8 на старте, 0 после).
- **IN-03.** `assert field["maxlength"] == "64"` заменён на `int(field["maxlength"]) == 2 * MANUAL_INPUT_MAX_CHARS` и `> MANUAL_INPUT_MAX_CHARS`; константа — из `app.services.phone`.

## RED / GREEN по задачам

Улики RED — в `.gsd/tdd-evidence/18-07/` (самоигнорируемый каталог, уходит вместе с worktree; запись здесь — долговременная).

| Задача | RED (цель, причинный литерал) | Семантическая оценка | GREEN |
|--------|-------------------------------|----------------------|-------|
| 1 (трассер) | `test_the_save_button_shares_the_row_of_the_phone_input`, три совпадения в выводе: строка `FAILED tests/test_pages/test_responsive_markup.py::test_the_save_button_shares_the_row_of_the_phone_input`, итог `2 failed`, литерал `кнопка «Сохранить» не в ряду поля: у формы нет display: grid`; второй красный — переписанный `test_the_phone_form_takes_its_own_row_in_the_account_head` | цель исполнена и упала на плановом утверждении (форма всё ещё `display: flex; flex-wrap: wrap; align-items: flex-end`); ошибок импорта, сбора и фикстур нет; `gsd_run check tdd-red-evidence` на JUnit-записи — `RED_EVIDENCE_OK`, `target_test_failed` | `6c676471` |
| 2 | не RED-цикл: тип `auto`, рефакторинг без смены поведения; отрицательный контроль IN-03 вместо RED (ниже) | — | — |

REFACTOR (`69b0e1c1`) — задача 2 целиком (по плану: поведение не меняется, держит существующая суита и контроль IN-03).

### Отрицательный контроль IN-03 (дословный отказ)

Временно `PHONE_FIELD_MAXLENGTH = MANUAL_INPUT_MAX_CHARS` в `app/pages/account_groups.py`; тест `test_the_screen_carries_the_phone_form_in_the_account_head` красный:

```
E       AssertionError: assert 32 == (2 * 32)
E        +  where 32 = int('32')
FAILED tests/test_pages/test_account_phone_form.py::test_the_screen_carries_the_phone_form_in_the_account_head
1 failed, 23 deselected
```

Правка снята до коммита (в `git diff` строки `PHONE_FIELD_MAXLENGTH` нет, в коммит вошёл только рефакторинг).

## Task Commits

1. **Задача 1: кнопка «Сохранить» в ряду поля (трассер)** — RED `2f12aeac` (test), GREEN `6c676471` (feat)
2. **Задача 2: `_screen_context` и `_phone_form_context`, `maxlength` из константы** — `69b0e1c1` (refactor)

**Plan metadata:** коммит `docs(18-07)` с этим файлом (хэш — в возврате исполнителя)

## TDD Gate Compliance

`test(18-07)` `2f12aeac` предшествует `feat(18-07)` `6c676471` (потомок); `refactor(18-07)` `69b0e1c1` следует за ними. RED -> GREEN в порядке предков, нарушений нет. У задачи 2 своего test/feat нет по плану (тип `auto`, рефакторинг).

## Files Created/Modified

- `app/static/css/app.css` — правила сетки формы номера, блок `@media (max-width: 400px)`, переписанный комментарий (прежний абзац помечен снятым, не стёрт)
- `tests/test_pages/test_responsive_markup.py` — тест `test_the_save_button_shares_the_row_of_the_phone_input`, помощники `_media_block_with` и `_area_rows`, перечень `PHONE_FORM_SELECTORS`; переписан `test_the_phone_form_takes_its_own_row_in_the_account_head`
- `app/pages/account_groups.py` — `_phone_form_context`, `_screen_context` с ключевыми-только параметрами, четыре вызова через помощник
- `tests/test_pages/test_account_phone_form.py` — утверждение `maxlength` через `MANUAL_INPUT_MAX_CHARS`

## Decisions Made

См. `key-decisions` во frontmatter. Плановые решения (сетка вместо отступа кнопки, один столбец на ≤400 px, адресация только `[data-acct-phone]`, ключи формы — одним помощником в том же модуле) выполнены как заданы.

## Deviations from Plan

### Auto-fixed Issues

None.

### Прочие отклонения

**1. [Тракт трассера] Ручная часть `<verify>` трассера не остановила исполнение**
- **Found during:** Задача 1 (трассерный гейт обратной связи)
- **Issue:** `HUMAN_VERIFY_MODE=end-of-phase`, трассер несёт `<human-check>` — строгая цепочка говорит «STOP -> checkpoint:human-verify». Но проверка человека — геометрия и дерево доступности в браузере на 1280, 900, 375 и 320 px (`/gsd-verify-work 18`, «Manual-Only» в 18-VALIDATION.md), её нельзя выполнить посреди исполнения без обхода с засевом данных, а `must_haves` плана отводит её обходу после фазы (`verification: backstop`). Так же поступил план 18-04.
- **Fix:** автоматические `<verify>` трассера прогнаны и зелены (1193 passed на расширенном наборе), расширение (задача 2) начато без остановки; задача 2 не зависит от геометрии (другие файлы) и откатывается отдельным коммитом.
- **Files modified:** нет
- **Committed in:** —

**2. План: полный `tests/test_pages` не запускался.** План просит в последнем плане раунда прогнать `uv run pytest tests/test_pages -q -p no:randomly` (~27 мин); заметки оркестратора запрещают исполнителю гонять большие каталоги и оставляют полный прогон после слияния. Прогнаны модули плана и перекрёстные гейты (см. Verification).

**Total deviations:** 0 auto-fixed, 2 процедурных (трассер, объём прогона). **Impact:** код и тесты исполнены как в плане.

## Issues Encountered

- Охранная оболочка рабочего дерева отказывала в составных командах (heredoc, цепочки с `git`, `cd ... && git`) — команды разбивались на простые, правки CSS и Python шли инструментом Edit.
- Прогоны под общим замком pytest шли 9 и 12 минут (ожидание замка плюс сами наборы).
- `ruff` в окружении не запускался (как в 18-04); проверка стиля не выполнена, `compileall` зелёный.

## Verification

- Целевой `-k "phone_form or save_button or account_label or manual_mark or scroll_padding or head_actions"` на `test_responsive_markup.py` — 9 passed (до GREEN: 2 failed, как задумано).
- После задачи 1: `test_responsive_markup`, `test_shell`, `tests/test_templates`, `test_account_groups`, `test_htmx_post_pairs`, `test_htmx_gates`, `test_account_phone_form`, `test_impersonation_gate`, `test_notices_registry` — **1193 passed**.
- После задачи 2 (все три прогона `<verify>` плана плюс перекрёстные гейты оркестратора; `tests/test_templates`, htmx-гейты, `test_account_groups`, `test_account_label_groups`, `test_impersonation`, `test_identifier_bounds`, `test_origin_guard_on_destructive_routes`, `test_write_path_invariants`, `test_htmx_validation_sink`, `test_hx_location_destinations`, три телефонных гейта и `test_phone_writer_runtime_guard`, `test_shell`, `test_responsive_markup`, `test_impersonation_gate`, `test_notices_registry`) — **2554 passed**, отказов по объявленным числам нет: `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 26, `PUSH_URL_DECISIONS_DECLARED` 38, `PAIRED_302_ASSERTIONS_DECLARED` 193, `POST_PAIR_CASES_DECLARED` 79, `OOB_BLOCKS` 25 не сдвинуты. В `tests/test_pages/test_account_phone_form.py` утверждений `status_code == 302` по-прежнему два.
- Приёмка: `grep -c "grid-area: button" app.css` = 1 (HEAD 0); `grep -c '"input button"' app.css` = 1 (HEAD 0); `git diff --quiet ab62fb9b..HEAD -- app/templates/components/field.html` — код 0 (общий макрос не правился); `def _phone_form_context` = 1, `_phone_form_context(` = 5; присваиваний `context["phone_*"] =` — 0 (на старте, после 18-05, было 8, БАЗА `ab62fb9b`); `field["maxlength"] == "64"` = 0 (было 1); `MANUAL_INPUT_MAX_CHARS` в тестовом файле = 3 (было 0).
- `python -m compileall -q app main.py tests` — чисто; `graphify update .` — выполнено.
- `tests/test_planning` гоняется после метаданного коммита (см. возврат исполнителя).

## Ручная половина (не доказана машинно — для `/gsd-verify-work 18`)

Ни одно утверждение о геометрии не заявлено доказанным: суита читает текст CSS. Остаётся человеку, в Chrome, на экране групп аккаунта:

- 1280 и 900 px, обычное состояние и после ввода `abc` (422): кнопка справа от поля, `top` и `bottom` кнопки совпадают с полем (±1 px, `getBoundingClientRect`), подсказка и ошибка под рядом, кнопка после 422 на месте.
- 375 и 320 px: поле, кнопка, подсказка и ошибка столбцом, кнопка сразу под полем и выше подсказки, не сдвигается после 422, ничего не обрезано, горизонтальной прокрутки нет.
- DevTools -> Accessibility для `#phone`: вычисленное имя «Номер телефона…», на 422 — вместе с текстом ошибки (T-18-23); щелчок мышью по подписи ставит фокус в поле.

## Known Stubs

None.

## Threat Flags

None — новых сетевых точек, путей авторизации и схем нет. T-18-23 (раскладка рвёт связь подписи и поля) снят тем, что связь — атрибут `for="phone"` макроса `field`, а не раскладка; проверка дерева доступности ручная (выше). T-18-24 (рефакторинг перепутал аккаунт или пользователя) закрыт ключевыми-только параметрами (позиционный вызов — `TypeError`) и `account_id` из `account.id` проверенного владельцем аккаунта; тесты неотличимости чужого аккаунта и адреса формы зелёные.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Все планы gap-раунда 18-04…18-08 исполнены; осталось слияние волны, полный `tests/test_pages` после слияния и обход `/gsd-verify-work 18` (ручная половина WR-01, 18-04, 18-05, 18-08).
- Записи PHONE-08…PHONE-11 в REQUIREMENTS.md не тронуты (`requirements mark-complete` не запускался: вердикт фазы ещё не `passed`).

---
*Phase: 18-ruchnaya-pravka-nomera*
*Completed: 2026-11-22*

## Self-Check: PASSED

Файлы `app/static/css/app.css`, `tests/test_pages/test_responsive_markup.py`, `app/pages/account_groups.py`, `tests/test_pages/test_account_phone_form.py` изменены и закоммичены; коммиты `2f12aeac`, `6c676471`, `69b0e1c1` найдены в истории ветки; удалений файлов нет; рабочее дерево чисто до SUMMARY.
