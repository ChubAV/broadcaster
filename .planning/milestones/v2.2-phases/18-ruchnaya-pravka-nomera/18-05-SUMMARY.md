---
phase: 18-ruchnaya-pravka-nomera
plan: 05
subsystem: ui
tags: [jinja2, htmx, autofocus, accessibility, phone-form, tdd]

requires:
  - phase: 18-ruchnaya-pravka-nomera
    provides: "форма номера (18-02), страница групп аккаунта (18-03), phone_error_response.html и OOB_BLOCKS 25 (18-08)"
provides:
  - "булев параметр autofocus общего макроса field (умолчание — разметка прежних полей не меняется)"
  - "ключ контекста phone_focus: False при обычном показе, True в трёх ответах на отправку формы номера"
  - "подсказка под полем номера называет последствие очистки; на ветке ошибки пример под полем один"
affects: [18-07, 18-verify-work]

actuals:
  tokens: 21000
  tasks: 2
  commits: 4

plan_head_before: cb3d6129a8e818dbd56561100ad182ca9bfd2977
plan_head_after: f5d68a25922cf828d86c9a0b01d3e7c870422e49

tech-stack:
  added: []
  patterns:
    - "autofocus в разметке ответа вместо JS: рантайм htmx фокусирует [autofocus] в подменённом содержимом"
    - "параметр общего макроса с умолчанием, не меняющим разметку прежних потребителей"

key-files:
  created: []
  modified:
    - app/templates/components/field.html
    - app/templates/account_groups/includes/phone_form.html
    - app/pages/account_groups.py
    - tests/test_pages/test_account_phone_form.py

key-decisions:
  - "Фокус возвращается атрибутом autofocus в ответе, а не JS и не id кнопки: кнопку на время запроса отключает hx-disabled-elt, отключённая кнопка фокус теряет"
  - "phone_focus истинен только в ответах на отправку формы (успех с JS, 422 с JS, страница 422); обычный показ и посадка после перехода фокус не отнимают (T-18-21, отличие от CR-01)"
  - "На ветке ошибки подсказка теряет предложение с примером, если текст ошибки уже содержит example_phone; тексты PhoneError (контракт Фазы 16) не менялись"

patterns-established:
  - "Подсказка собирается в шаблоне из двух предложений; условие ветки ошибки — 'текст ошибки содержит пример'"

requirements-completed: [PHONE-09, PHONE-10]

coverage:
  - id: D1
    description: "После ответа на отправку формы номера (успех с JS, 422 с JS, страница 422 без JS) у поля name=phone стоит autofocus"
    requirement: PHONE-09
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_phone_form.py#test_the_answer_to_a_submission_puts_focus_back_into_the_field"
        status: pass
    human_judgment: false
  - id: D2
    description: "Обычный показ экрана и посадка после перехода без JS не несут autofocus нигде в теле"
    requirement: PHONE-09
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_phone_form.py#test_the_plain_screen_never_autofocuses_the_field"
        status: pass
    human_judgment: false
  - id: D3
    description: "Подсказка под полем говорит, что очищенное поле и «Сохранить» стирают номер; текста PHONE_ERROR_BLANK на странице нет"
    requirement: PHONE-10
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_phone_form.py#test_the_hint_tells_that_a_cleared_field_erases_the_number"
        status: pass
    human_judgment: false
  - id: D4
    description: "На ответе с ошибкой (страница 422 и фрагмент 422) пример номера под полем один, предложение о стирании на месте"
    requirement: PHONE-10
    verification:
      - kind: unit
        ref: "tests/test_pages/test_account_phone_form.py#test_an_error_answer_names_the_example_once"
        status: pass
    human_judgment: false
  - id: D5
    description: "В браузере после «Сохранить» и после 422 document.activeElement — поле #phone, экран при обычном открытии фокус не отнимает, читалка озвучивает ошибку вместе с именем поля, подсказка читаема"
    verification: []
    human_judgment: true
    rationale: "Суита не исполняет JS: фокус в живом браузере, речь читалки и читаемость текста оценивает только человек (/gsd-verify-work 18)"

duration: 38min
completed: 2026-11-22
status: complete
---

# Phase 18 Plan 05: Focus and hint of the phone form Summary

**Фокус возвращается в поле номера после любого ответа на отправку (булев `autofocus` в макросе `field` + флаг `phone_focus`), подсказка называет стирание номера очисткой поля и не повторяет пример рядом с текстом ошибки.**

## Performance

- **Duration:** 38 min
- **Started:** 2026-11-22T07:44:00Z
- **Completed:** 2026-11-22T08:22:00Z
- **Tasks:** 2 (TDD: 2 цикла RED -> GREEN, REFACTOR не понадобился)
- **Files modified:** 4

## Accomplishments

- UI-P1 / IN-01: у `field` появился булев параметр `autofocus` (по умолчанию печатает ничего — разметка прежних полей не изменилась ни на символ, подтверждено 2553 зелёными тестами экранов, использующих макрос). Форма номера передаёт `autofocus=phone_focus`; обработчик ставит `phone_focus=False` в `_screen_context` и `True` в `_page`, `_error_fragment`, `_saved`.
- UI-P3 / D-09 / D-11: подсказка «Пример: +7 999 123-45-67. Чтобы стереть номер, очистите поле и нажмите «Сохранить».»; подтверждения нет, `PHONE_ERROR_BLANK` форма по-прежнему не показывает.
- OBS-422 (часть «пример дважды»): на ветке ошибки, когда текст ошибки содержит `example_phone`, подсказка оставляет только предложение о стирании — пример под полем один, на обоих транспортах.

## TDD Gate Compliance

Задача 1 (трассер):
- **RED** `ac31aa8e`: `test_the_answer_to_a_submission_puts_focus_back_into_the_field` упал на утверждении «успех с JS: после ответа фокус не возвращается в поле номера» (литерал из плана есть в отчёте). Запуск: `uv run pytest tests/test_pages/test_account_phone_form.py -q -p no:randomly --junit-xml=...` — `1 failed, 20 passed`. `gsd-tools check tdd-red-evidence` на JUnit-записи: `RED_EVIDENCE_OK`, `target_test_failed`. Семантическая оценка: целевой тест исполнился и упал на планируемом утверждении по нужной причине (у поля в ответе нет `autofocus`), не из-за сбора, импорта или фикстуры. Охранный тест `test_the_plain_screen_never_autofocuses_the_field` зелёный уже на RED — он закрепляет отсутствие регрессии (T-18-21), а не новое поведение.
- **GREEN** `ad2ad815`: 21 passed.

Задача 2:
- **RED** `3cf5d7fd`: три красных — `test_the_hint_tells_that_a_cleared_field_erases_the_number` (в отчёте литерал `Чтобы стереть номер`) и `test_an_error_answer_names_the_example_once[not_a_number|too_long]` (сообщение «пример номера под полем повторён»). `1`-й тест: `check tdd-red-evidence` — `RED_EVIDENCE_OK`. Семантическая оценка: тесты исполнились, упали на планируемых утверждениях (нет предложения о стирании; пример встречается дважды).
- **GREEN** `f5d68a25`: 24 passed.
- REFACTOR: не требовался. Порядок коммитов `test` -> `feat` на каждую задачу соблюдён. Улики RED лежат в игнорируемом `.gsd/tdd-evidence/18-05/` (удаляются вместе с worktree; эта запись — долговременная).

## Task Commits

1. **Task 1: фокус возвращается в поле после ответа (трассер)** — `ac31aa8e` (test), `ad2ad815` (feat)
2. **Task 2: подсказка о стирании и один пример рядом с ошибкой** — `3cf5d7fd` (test), `f5d68a25` (feat)

**Plan metadata:** коммит `docs(18-05)` со сводкой (следует за этой записью).

## Files Created/Modified

- `app/templates/components/field.html` — параметр `autofocus` (булев, по умолчанию ложный), атрибут печатается последним.
- `app/templates/account_groups/includes/phone_form.html` — `autofocus=phone_focus`, подсказка из двух предложений с веткой ошибки, шапка: ключ `phone_focus`, отличие от CR-01, D-09/D-11/OBS-422.
- `app/pages/account_groups.py` — ключ `phone_focus` в `_screen_context` (False) и в трёх ответах на отправку (True); докстринги дополнены.
- `tests/test_pages/test_account_phone_form.py` — 4 новых теста (+ параметризация), новых утверждений `status_code == 302` нет (их по-прежнему два).

## Decisions Made

См. `key-decisions` во frontmatter. Плановые решения (autofocus вместо JS и id кнопки; условие ветки ошибки «текст содержит пример»; подтверждения нет) выполнены как заданы.

## Deviations from Plan

None - plan executed exactly as written. Единственная мелочь вне перечня: первая редакция комментария в шапке `field.html` дословно содержала `autofocus=false` и давала счёт 2 вместо 1 по критерию приёмки; формулировка комментария изменена до GREEN-коммита, поведение не затронуто.

## Issues Encountered

- Охранная оболочка рабочего дерева отказывала в составных командах (heredoc, цепочки с `git`) — команды разбивались на простые.
- Гейтовые прогоны долгие (576 и 696 с); шли в фоне под `flock` на общем замке.

## Verification

- `tests/test_pages/test_account_phone_form.py` — 24 passed.
- Задача 1, прогон 2-3 плана плюс кросс-гейты оркестратора (`tests/test_templates`, `test_ads_image_upload`, `test_profile`, `test_auth_transport`, `test_account_groups`, `test_shell`, `test_htmx_gates`, `test_htmx_post_pairs`, `test_phone_privacy_gate`, `test_responsive_markup`, `test_impersonation_gate`, `test_notices_registry`) — 1584 passed.
- Гейтовая команда волны после задачи 2 (шаблоны, htmx-гейты, post_pairs, identifier_bounds, account_groups, account_label_groups, notices_registry, write_path_invariants, origin_guard, validation_sink, hx_location_destinations, privacy/parity, single_writer, writer_runtime_guard, responsive_markup, shell, impersonation, ads_image_upload, profile, auth_transport) — 2553 passed.
- `python -m compileall -q app main.py tests` — чисто; `graphify update .` — выполнено.
- Приёмка: `autofocus=phone_focus` в phone_form.html = 1; `autofocus=false` в field.html = 1; `phone_focus` в account_groups.py = 5 (>= 4); `status_code == 302` в тестовом файле = 2; `PHONE_ERROR_BLANK` в phone.py на месте.
- `tests/test_planning` гоняется оркестратором после метаданных (см. отчёт возврата).

## Known Stubs

None.

## Threat Flags

None - новых сетевых точек, путей авторизации или схем нет. T-18-21 (кража фокуса) закрыт: `autofocus` только в ответах на отправку этой формы, охранный тест `test_the_plain_screen_never_autofocuses_the_field`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ручная половина (UI-P1, OBS-422): после «Сохранить» и 422 `document.activeElement` — поле `#phone`, пример на 422 один, фокус у открывшего экран не отнимается, читалка озвучивает ошибку с именем поля — подтверждается только обходом человеком (`/gsd-verify-work 18`).
- PHONE-09 и PHONE-10 оставлены `Pending` в REQUIREMENTS.md намеренно (вердикт фазы не `passed`).
- План 18-07 (волна 6) правит те же `app/pages/account_groups.py` и `tests/test_pages/test_account_phone_form.py` — этот план закончен до него.

## Self-Check: PASSED

---
*Phase: 18-ruchnaya-pravka-nomera*
*Completed: 2026-11-22*
