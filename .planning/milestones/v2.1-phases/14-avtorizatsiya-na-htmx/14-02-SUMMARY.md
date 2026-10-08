---
phase: 14-avtorizatsiya-na-htmx
plan: 02
subsystem: auth
tags: [htmx, fastapi, jinja2, response-layer, registration, 422, tdd]

requires:
  - phase: 14-avtorizatsiya-na-htmx
    provides: "14-01 — `AUTH_SCREENS`, `_screen_builders`, `step_response.html`, якорь `#auth-step`, `RESPONSE_LAYER_EXITS`, ветка пар `FULL_LOAD`, личность `ANONYMOUS`"
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "`respond_field_error` (422 на обоих транспортах), граница сборщика `_fragment_builder_names` (план 11-09)"
provides:
  - "`respond_screen` — выход смены экрана: 200 на обоих транспортах, страница без htmx, фрагмент с ним; общее тело `_respond_by_transport` с `respond_field_error`"
  - "`register_send_code` и `register_resend_code` на выходах слоя: 422 — тот же экран, 200 — экран сменился (D-03)"
  - "экраны `register` и `register_verify` в `AUTH_SCREENS`; включаемые шаблоны `register_step.html`, `register_verify_step.html`"
  - "форма адреса и форма повтора кода через `form_wrapper` в `#auth-step` (innerHTML); повтор перерисовывает обе формы одним токеном"
  - "ветка пар `SCREEN` (200 + страница / 200 + фрагмент с `<title>` верхним узлом), 4 случая регистрации"
  - "гейты знают `respond_screen`: семейство выходов, передача фрагмента, граница сборщика, признак деградации разметочного гейта"
affects: [14-03, 14-04, 14-05, 14-06, 14-07]

actuals:
  tokens: 23082
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "смена экрана: page, fragment = _screen_builders(request, screen, **ctx); return await respond_screen(request, page=page, fragment=fragment)"
    - "экран с двумя формами на одном токене: вся разметка экрана в якоре, форма повтора подменяет СОДЕРЖИМОЕ якоря целиком (D-06)"
    - "драйвер пар: утверждение 302 внутри ветвей, ждущих перенаправления; ветка SCREEN утверждает 200 на обеих половинах"

key-files:
  created:
    - app/templates/auth/includes/register_step.html
    - app/templates/auth/includes/register_verify_step.html
  modified:
    - app/pages/htmx.py
    - app/pages/auth.py
    - app/templates/auth/register.html
    - app/templates/auth/register_verify.html
    - tests/test_pages/test_auth_transport.py
    - tests/test_pages/test_htmx_response_layer.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_registration.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Выход смены экрана — отдельная функция `respond_screen`, а не параметр кода у `respond_field_error`: гейты различают выходы по имени"
  - "Литерал 422 остаётся ключевым аргументом внутри `respond_field_error`, поэтому гейт мест 422 (`SERVER_SIDE_VALIDATION_RESPONSES = 2`) не двигается"
  - "`_hands_a_fragment` засчитывает фрагмент у `respond_screen`, но НЕ у `respond_field_error`: фрагмент ошибки поля — та же форма, а не смена экрана"
  - "У случаев пар ветки SCREEN `landing` пуст: у экрана нет адреса, сличать заголовок перехода не с чем"

patterns-established:
  - "Экран кода: форма подтверждения — обычная форма до 14-03, форма повтора — `form_wrapper` в `#auth-step`"
  - "Посев пар регистрации: уникальный адрес на каждый вызов посева (счётчик модуля), иначе вторая половина попадает в минуту между кодами"

requirements-completed: [SIGN-01, SIGN-02]

coverage:
  - id: D1
    description: "Выход `respond_screen`: 200 на обоих транспортах, ровно один сборщик, свежий `HTMLResponse` без фоновой задачи и без заголовков перехода; потоковый ответ без тела — `ValueError`"
    requirement: SIGN-02
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_a_screen_change_answers_200_with_the_page_without_htmx_and_the_fragment_with_it"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_a_field_error_answers_422_with_the_page_without_htmx_and_the_fragment_with_it"
        status: pass
    human_judgment: false
  - id: D2
    description: "Занятый адрес — 422, «Этот email уже зарегистрирован», адрес в `value=`; с htmx первый узел `<title>Регистрация — Broadcaster</title>`"
    requirement: SIGN-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_taken_email_keeps_the_address_and_answers_422_on_both_transports"
        status: pass
    human_judgment: false
  - id: D3
    description: "Новый адрес — 200 и экран кода на обоих транспортах; токен скрытым полем; с htmx без `<!DOCTYPE`, `<title>` экрана кода первым узлом, без `HX-Location`/`HX-Redirect`/`HX-Push-Url`; «код уже отправлен» — 200 с прежним текстом"
    requirement: SIGN-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_the_registration_email_step_answers_the_code_screen_on_both_transports"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_repeated_email_step_within_a_minute_lands_on_the_code_screen"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports (4 случая регистрации)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Повтор кода — 200, «Новый код отправлен на вашу почту.», ровно два скрытых `token` с одним значением; раньше минуты — 422 с присланным токеном; устаревшая ссылка — 200 и экран начала"
    requirement: SIGN-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_resending_the_code_redraws_both_forms_with_one_token"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_resending_within_a_minute_answers_422_on_the_code_screen"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_resending_with_a_stale_link_returns_to_the_start_of_registration"
        status: pass
    human_judgment: false
  - id: D5
    description: "Форма адреса и форма повтора рождены `form_wrapper` с целью `#auth-step` и `innerHTML`; форма подтверждения — обычный POST (окно до 14-03)"
    requirement: SIGN-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_the_code_screen_carries_the_resend_form_into_the_anchor"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py (83 passed)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Гейты узнают `respond_screen`: переведённый, отдающий фрагмент, сборщики не собственные выходы; числа поставлены прогоном"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_handler_answering_only_by_a_screen_change_is_converted_and_hands_a_fragment"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py (53 passed)"
        status: pass
    human_judgment: false
  - id: D7
    description: "В браузере регистрация показывает экран кода без перезагрузки, адресная строка остаётся `/register`, вкладка меняет заголовок; настоящее письмо с кодом приходит"
    requirement: SIGN-01
    verification: []
    human_judgment: true
    rationale: "Поведение браузера (заголовок вкладки, адресная строка, подмена без перезагрузки) и доставка настоящего письма сервером не измеряются — ручной UAT фазы (критерий 4, D-02)"

duration: 39min
completed: 2026-09-22
status: complete
plan_head_before: 7dcb084a44a7f72ff410cb9e22fa73118ca17564
commits: 3
---

# Phase 14 Plan 02: Регистрация «почта → экран кода» и повтор кода на фрагментах — Summary

**Новый выход слоя `respond_screen` (200 на обоих транспортах, общее тело с `respond_field_error`) переводит шаг адреса регистрации и повтор кода на постоянный якорь `#auth-step`: занятый адрес и повтор раньше минуты — 422 на том же экране, смена экрана — 200 со страницей без JS и фрагментом с `<title>` верхним узлом, токен шага только скрытым полем обеих форм.**

## Performance

- **Duration:** 39 min
- **Started:** 2026-09-22T12:38:49Z
- **Completed:** 2026-09-22T13:17:55Z
- **Tasks:** 2
- **Files modified:** 12 (2 новых, 10 изменённых), ровно объявленные планом

## Accomplishments
- `app/pages/htmx.py`: `respond_screen` и закрытый `_respond_by_transport`. `respond_field_error` сохранил сигнатуру и докстринг и отдаёт тело через помощник с `status_code=422` (литерал на месте). В шапке модуля появилась строка «седьмой вид».
- `app/pages/auth.py`: записи `register` и `register_verify` в `AUTH_SCREENS`; шесть прежних возвратов `TemplateResponse` в двух обработчиках сняты (D-14). Запросы, минута, срок, `secrets.randbelow` (4 места), письмо и тексты не тронуты (D-15).
- Шаблоны: `register_step.html` и `register_verify_step.html` — единственные источники разметки экранов. Страницы `register.html` и `register_verify.html` сведены к `extends` + `title` + одно включение, блока подзаголовка в них нет.
- Гейты: `RESPONSE_LAYER_EXITS` + `respond_screen`; `_hands_a_fragment` и `_fragment_builder_names` знают выход; двухшаговый контроль. Числа поставлены прогоном: `NOT_YET_CONVERTED_COUNT` 9 → 7, `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 17 → 19, `POST_PAIR_CASES_DECLARED` 59 → 63, `PAIRED_302_ASSERTIONS_DECLARED` 176 → 176 (неподвижность записана), `MACRO_DEFINITION_SITES_CALLERS_DECLARED` 25 → 27, `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` 10 → 12, `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` 20 → 22.

## Task Commits

1. **Задача 1: регистрация «почта → экран кода» и повтор кода, выход смены экрана.** RED `e471bdf0` (test), GREEN `481d5a9b` (feat).
2. **Задача 2: перечни.** `bd204d63` (test: record).

**Plan metadata:** коммит `docs(14-02)` с этим файлом; STATE/ROADMAP — отдельным коммитом записи.

## TDD Gate Compliance

| Задача | RED commit | Красное утверждение (дословно из прогона) | GREEN commit |
|---|---|---|---|
| 1 | `e471bdf0` | `assert 200 == 422` в `test_a_taken_email_keeps_the_address_and_answers_422_on_both_transports`. Вывод `uv run pytest tests/test_pages/test_auth_transport.py -q -p no:randomly -k taken_email` содержит строку `FAILED tests/test_pages/test_auth_transport.py::test_a_taken_email_keeps_the_address_and_answers_422_on_both_transports`, итог `1 failed, 14 deselected` и литерал `assert 200 == 422` — все три совпадения `<tdd_notes>` | `481d5a9b` |

- RED-улика проверена штатным вербом: `check tdd-red-evidence` → `RED_EVIDENCE_OK` (`target_test_failed`). Запись собрана из `--junit-xml` того же прогона и перегнана в TAP скриптом в scratchpad (не закоммичен).
- На RED-коммите красны все 8 новых правил, ни одно не зелено заранее. Причины по месту: `assert 200 == 422` (занятый адрес, повтор раньше минуты), `'<!DOCTYPE' not in …` (шаг адреса на htmx), первый узел не `<title>` (повтор, «код уже отправлен», устаревшая ссылка), форма повтора не из макроса. Правило слоя падает с `ImportError: cannot import name 'respond_screen'` внутри тела теста, а не при сборе модуля.
- Задача 2 не `tdd="true"`. Её контроль всё равно снят в три шага, и каждое расширение показало зубы до правки: (1) до пополнения семейства — `обработчик, отвечающий выходом смены экрана, не признан переведённым`; (2) до `_hands_a_fragment` — `передача фрагмента выходу смены экрана не засчитана`; (3) до `_fragment_builder_names` — `сборщики, поданные выходу смены экрана именем, объявлены собственными выходами обработчика: HTMLResponse()`.
- Гейт-валидация истории: `test(14-02)` (2 коммита) и `feat(14-02)` (1) есть. `refactor(14-02)` нет, он не требовался.

## Tests outside the plan's named set

Проверено поиском вызывающих `/register/send-code` и `/register/resend-code` и разметки двух экранов по `tests/`: `test_trial.py`, `test_access_lifecycle.py` и `test_reset_code_source.py` ходят только по успеху (200 остался 200). `test_shell.py` открывает `GET /register`. Прогнаны `tests/test_templates` целиком, `test_shell.py`, `test_responsive_markup.py`, `test_https_asset_scheme.py`, `test_access_lifecycle.py`, `test_reset_code_source.py`, `test_password_reset.py`, `test_blocked_user.py`, `test_htmx_response_contract.py`, `tests/test_e2e.py` и `tests/test_routes/test_auth.py`: **667 passed, 0 failed** (14:06). Вне названных планом покраснело только правило, которое план называет сам: `test_send_code_rejects_existing_email` (200 → 422, D-03, летопись «Фаза 14, план 14-02»).

Прогон гейтов волны (последняя команда `<verify>` задачи 2, 14 модулей): **400 passed, 0 failed** (3:05). `uv run python -m compileall -q app main.py tests` отработал без вывода; `graphify update .` выполнен.

## Files Created/Modified
- `app/pages/htmx.py`: `respond_screen`, `_respond_by_transport`, строка шапки о седьмом виде выхода
- `app/pages/auth.py`: две записи реестра экранов, перевод `register_send_code` и `register_resend_code`
- `app/templates/auth/includes/register_step.html`: экран начала регистрации
- `app/templates/auth/includes/register_verify_step.html`: экран кода (две формы на одном токене)
- `app/templates/auth/register.html`, `register_verify.html`: страницы = включение экрана
- `tests/test_pages/test_auth_transport.py`: 7 правил регистрации
- `tests/test_pages/test_htmx_response_layer.py`: правило выхода смены экрана
- `tests/test_pages/test_htmx_gates.py`: семейство, признак фрагмента, граница сборщика, контроль, сдвиги перечней
- `tests/test_pages/test_htmx_post_pairs.py`: ветка `SCREEN`, посевы, 4 случая, летописи
- `tests/test_pages/test_registration.py`: 200 → 422 (D-03)
- `tests/test_templates/test_htmx_markup_gates.py`: признак деградации, вызывающие, три числа

## Decisions Made
- Решения, отданные планом на усмотрение исполнителя, приняты так, как план их записал (имя выхода, общий помощник, подача сборщиков именем).
- Текст отказа `_respond_by_transport` называет оба выхода (`respond_field_error` / `respond_screen`), как требует план.

## Deviations from Plan

### Оформление и замеры (поведение не менялось)

**1. [Замер] Два обработчика вышли из отставания ещё до пополнения семейства**
- **Found during:** задача 2
- **Issue:** `NOT_YET_CONVERTED_COUNT` покраснел 9 → 7 на первом прогоне после GREEN, до того как `respond_screen` вошёл в `RESPONSE_LAYER_EXITS`. Оба обработчика зовут и `respond_field_error`, который уже в семействе.
- **Fix:** правка не потребовалась. Факт записан в летописи числа, чтобы движение не приписывалось пополнению. Зубы пополнения держит двухшаговый контроль на синтетическом обработчике, который зовёт только `respond_screen`.
- **Committed in:** `bd204d63`

**2. [Замер] Пополнение `DEGRADATION_MARKERS` сегодня не зеленит ни одного правила**
- **Found during:** задача 2
- **Issue:** `FRAGMENT_ROUTES_DECLARED` без пополнения не покраснел по той же причине (оба маршрута достигают `respond_field_error`).
- **Fix:** пополнение сделано по плану, с летописью «замер, а не пополнение ради красного». Оно нужно обработчикам 14-03…14-05, которые будут отвечать только сменой экрана.
- **Committed in:** `bd204d63`

**3. [Оформление] Лишние утверждения в правилах `<behavior>`**
- В правило «код уже отправлен» добавлена проверка `<title>` первым узлом на половине htmx. Без неё правило было бы зелено на дереве до правки: старый обработчик отдавал страницу 200 с тем же текстом. В правило повтора добавлены текст успеха и `<title>`. Ни одно утверждение `<behavior>` не снято.

**4. [Процесс] Один read-only вызов `git stash list`**
- В проверочной команде задачи 1 случайно оказался `git stash list`. Он только читает список и ничего не меняет (стека не трогает, ничего не применяет). Больше `git stash` не вызывался.

---

**Total deviations:** 4 (2 замера, 1 оформление, 1 процессная оговорка). **Impact:** поведение и объём — как в плане; 12 файлов, ни одного сверх объявленных.

## Issues Encountered
- Прогноз плана «`PAIRED_302_ASSERTIONS_DECLARED` не двигается» совпал с замером: 176 → 176. Неподвижность записана строкой летописи.
- `SERVER_SIDE_VALIDATION_RESPONSES` (гейт мест 422) не покраснел: литерал `status_code=422` остался ключевым аргументом в `respond_field_error`, а в помощнике стоит имя `status_code`.

## Known Stubs

None. Оба экрана получают данные от обработчиков. Пустой `email` на `GET /register` — нормальное начальное состояние поля.

## Threat Flags

None. Новых поверхностей сверх `<threat_model>` нет. T-14-03 закрыт автоэкранированием эха адреса через макрос `field` (фильтра безопасной разметки нет), T-14-07 — правилом «заголовков перехода нет» в `test_auth_transport.py` и в правиле выхода, T-14-15 — отказом `ValueError` на потоковом ответе.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 14-03 (подтверждение кода и завершение регистрации) садится на готовое: `respond_screen`, ветку пар `SCREEN`, экран `register_verify` в реестре. Ему остаются перевод формы подтверждения на `form_wrapper` (сейчас это обычная форма, окно названо в шаблоне), эхо кода и синхронизация двух форм.
- SIGN-01 и SIGN-02 НЕ отмечены Complete: их объявляют планы 14-03…14-07, у которых ещё нет SUMMARY (`requirements.ready-ids`).

---
*Phase: 14-avtorizatsiya-na-htmx*
*Completed: 2026-09-22*

## Self-Check: PASSED
