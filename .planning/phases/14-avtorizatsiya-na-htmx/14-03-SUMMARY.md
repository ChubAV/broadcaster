---
phase: 14-avtorizatsiya-na-htmx
plan: 03
subsystem: auth
tags: [htmx, fastapi, jinja2, response-layer, registration, 422, hx-redirect, tdd]

requires:
  - phase: 14-avtorizatsiya-na-htmx
    provides: "14-01: `redirect_internal`, `AUTH_SCREENS`, `_screen_builders`, `step_response.html`, якорь `#auth-step`, ветка пар `FULL_LOAD`, личность `ANONYMOUS`"
  - phase: 14-avtorizatsiya-na-htmx
    provides: "14-02: `respond_screen`, экраны `register` / `register_verify`, ветка пар `SCREEN`, посев пар регистрации с уникальным адресом"
provides:
  - "`register_verify` на выходах слоя: неверный, истёкший или исчерпанный код — 422 с набранным кодом и прежним токеном; устаревшая ссылка — 200 и экран начала; верный код — 200 и экран имени и пароля"
  - "`register_complete` на выходах слоя: короткий пароль — 422 с именем и без пароля; устаревшая ссылка и адрес, занятый к завершению, — 200 и экран начала; успех — 302 / 204 + `HX-Redirect: /dashboard`, cookie на возвращённом объекте после `start_trial`"
  - "экран `register_complete` в `AUTH_SCREENS`; `register_complete_step.html` — единственный источник разметки экрана"
  - "обе формы экрана кода на `form_wrapper` с целью `#auth-step` и `hx-sync=\"closest #auth-step:drop\"`; окно 14-02 закрыто"
  - "пары: 2 случая `SCREEN` подтверждения, успех завершения вторым случаем `FULL_LOAD` с cookie, 2 случая `SCREEN` завершения"
affects: [14-04, 14-05, 14-06, 14-07]

actuals:
  tokens: 17901
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "эхо кода на экране кода: `_screen_builders(request, \"register_verify\", email=…, token=…, code=code, error=…)` → `respond_field_error`"
    - "полная загрузка с cookie после пробного срока: `start_trial` → `commit` → `response = await redirect_internal(request, redirect=\"/dashboard\")` → `set_session_cookie(response, …)`"
    - "синхронизация двух форм одного якоря: `sync='closest #auth-step:drop'` на обоих вызовах `form_wrapper`"

key-files:
  created:
    - app/templates/auth/includes/register_complete_step.html
  modified:
    - app/pages/auth.py
    - app/templates/auth/register_complete.html
    - app/templates/auth/includes/register_verify_step.html
    - tests/test_pages/test_auth_transport.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_registration.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Адрес, занятый к завершению регистрации, отвечает 200 через `respond_screen`, а не 422: экран меняется на начало регистрации, и это решает критерий D-03 (RESEARCH Open Question 3). Оговорка записана в докстринге `register_complete`"
  - "Пароль не попадает в контекст экрана завершения. Ответ 422 короткого пароля передаёт только `email`, новый подтверждённый токен, `name` и текст ошибки (D-04)"
  - "Цена синхронизации двух форм принята, как записано в Pitfall 10 RESEARCH: ответ повтора кода подменяет якорь и стирает недонабранный код. Параметр `include` не используется"

patterns-established:
  - "Посев пар, чей успех расходует состояние (код помечается подтверждённым, адрес становится занятым), берёт уникальный адрес на каждую половину пары"

requirements-completed: [SIGN-01, SIGN-02, SIGN-03]

coverage:
  - id: D1
    description: "Неверный код — 422 на обоих транспортах, «Неверный код. Осталось попыток: 4», набранный код в `value=`, присланный токен скрытым полем; с htmx первый узел `<title>Подтверждение email — Broadcaster</title>`; исчерпанный код — 422 с прежним текстом и тем же эхом"
    requirement: SIGN-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_wrong_code_keeps_the_typed_code_and_answers_422_on_both_transports"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_an_exhausted_code_answers_422_with_the_typed_code"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_registration.py#test_verify_code_wrong"
        status: pass
    human_judgment: false
  - id: D2
    description: "Верный код — 200 и экран имени и пароля: страница без htmx, фрагмент с `<title>Завершение регистрации — Broadcaster</title>` первым узлом и одним подтверждённым токеном, без заголовков перехода; устаревшая ссылка — 200 и экран начала"
    requirement: SIGN-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_right_code_opens_the_name_and_password_screen_on_both_transports"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_stale_link_on_the_code_step_returns_to_the_start_of_registration"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports (2 случая подтверждения)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Короткий пароль — 422, текст дословно, имя в `value=`, строки пароля в теле нет, один новый подтверждённый токен; адрес, занятый к завершению, — 200, «Этот email уже зарегистрирован», экран начала, cookie нет"
    requirement: SIGN-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_short_password_keeps_the_name_and_answers_422_without_the_password"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_taken_address_at_completion_returns_to_the_start_with_200"
        status: pass
    human_judgment: false
  - id: D4
    description: "Завершение без htmx — 302 на `/dashboard` с cookie; с htmx — 204, `HX-Redirect: /dashboard`, без `HX-Location`, пустое тело, cookie на этом же ответе; строка подписки заведена; следующий `GET /dashboard` — 200 для нового пользователя"
    requirement: SIGN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_completing_registration_leaves_by_a_full_load_with_the_cookie_and_the_trial"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[register_complete-завершение регистрации — успех]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_trial.py#test_the_page_registration_path_starts_the_trial"
        status: pass
    human_judgment: false
  - id: D5
    description: "Враждебные код и имя возвращаются экранированными (`&#34;&gt;&lt;script&gt;…`) в `value=` на обоих транспортах и ни разу не приходят сырыми"
    requirement: SIGN-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_hostile_code_and_name_come_back_escaped"
        status: pass
    human_judgment: false
  - id: D6
    description: "Обе формы экрана кода рождены `form_wrapper` с `hx-target=\"#auth-step\"`, `hx-swap=\"innerHTML\"` и `hx-sync=\"closest #auth-step:drop\"`; форма завершения — `form_wrapper` в тот же якорь"
    requirement: SIGN-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_both_code_forms_ride_the_anchor_and_drop_a_second_request"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py (83 passed)"
        status: pass
    human_judgment: false
  - id: D7
    description: "Перечни поставлены прогоном: отставание 7 → 5, фрагментные обработчики 19 → 21, пары 63 → 68, утверждения 302 176 → 181, вызывающие 27 → 28, параметрические 12 → 13, блоки вызова 22 → 24"
    verification:
      - kind: unit
        ref: "прогон гейтов волны (последняя команда `<verify>` задачи 2, 15 модулей): 415 passed"
        status: pass
    human_judgment: false
  - id: D8
    description: "В браузере путь «почта → код из настоящего письма → имя и пароль → кабинет» проходит целиком; неверный код оставляет набранное в поле; cookie сменилась на завершении"
    requirement: SIGN-03
    verification: []
    human_judgment: true
    rationale: "Поведение браузера (подмена якоря, заголовок вкладки, переход по HX-Redirect, сохранение пароля) и доставка настоящего письма тестами не измеряются. Это ручной UAT фазы (критерий 4, D-02)"

duration: 34min
completed: 2026-09-22
status: complete
plan_head_before: 5b537da7cf5470936ceb903b9394ba873960dea3
commits: 3
---

# Phase 14 Plan 03: Регистрация «код → имя и пароль → кабинет» на фрагментах — Summary

**Подтверждение кода и завершение регистрации отвечают через выходы слоя за якорем `#auth-step`. Неверный код и короткий пароль дают 422 на том же экране, набранный код и имя остаются в поле, пароль не возвращается. Завершение уходит полной загрузкой: 302 без htmx, 204 + `HX-Redirect: /dashboard` с ним, cookie стоит на возвращённом объекте после пробного срока. Обе формы экрана кода переведены на макрос с `hx-sync="closest #auth-step:drop"`.**

## Performance

- **Duration:** 34 min
- **Started:** 2026-09-22T14:02:26Z
- **Completed:** 2026-09-22T14:36:11Z
- **Tasks:** 2
- **Files modified:** 9 (1 новый, 8 изменённых). Это ровно файлы, объявленные планом

## Accomplishments
- `app/pages/auth.py`: запись `register_complete` в `AUTH_SCREENS`. В `register_verify` сняты четыре возврата `TemplateResponse`, в `register_complete` сняты три `TemplateResponse` и один `RedirectResponse` (D-14). Не тронуты запрос кода, счёт попыток с `commit` до ответа, отметка подтверждения, порядок «пользователь → `start_trial` → `commit` → cookie» (комментарий D-B перенесён) и все тексты (D-15).
- `register_complete_step.html` — единственный источник разметки экрана. Страница `register_complete.html` сведена к `extends` + `title` + одно включение. Блока `auth_subtitle` в ней больше нет: подзаголовок печатает сам экран.
- `register_verify_step.html`: форма подтверждения — блочный вызов `form_wrapper` с `value=code or ''` в поле кода. Обе формы получили `sync='closest #auth-step:drop'`. Абзац шапки об окне 14-02 не стёрт, к нему дописана летопись закрытия окна и оговорка о цене синхронизации.
- Гейты сдвинуты прогоном: `NOT_YET_CONVERTED_COUNT` 7 → 5, `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 19 → 21, `POST_PAIR_CASES_DECLARED` 63 → 68, `PAIRED_302_ASSERTIONS_DECLARED` 176 → 181, `MACRO_DEFINITION_SITES_CALLERS_DECLARED` 27 → 28, `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` 12 → 13, `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` 22 → 24. У каждого числа летопись «Фаза 14, план 14-03» с дословным выводом отказа.

## Task Commits

1. **Задача 1: регистрация «код → имя и пароль → кабинет», обе формы экрана кода на макросе.** RED `9dc41bf6` (test), GREEN `6bfe61ac` (feat).
2. **Задача 2: перечни.** `0585d145` (test: record).

**Plan metadata:** коммит `docs(14-03)` с этим файлом; STATE/ROADMAP идут отдельным коммитом записи.

## TDD Gate Compliance

| Задача | RED commit | Красное утверждение (дословно из прогона) | GREEN commit |
|---|---|---|---|
| 1 | `9dc41bf6` | `assert 200 == 422` в `test_a_wrong_code_keeps_the_typed_code_and_answers_422_on_both_transports`. Вывод `uv run pytest tests/test_pages/test_auth_transport.py -q -p no:randomly -k wrong_code_keeps` содержит все три совпадения `<tdd_notes>`: строку `FAILED tests/test_pages/test_auth_transport.py::test_a_wrong_code_keeps_the_typed_code_and_answers_422_on_both_transports`, итог `1 failed, 23 deselected` и литерал `assert 200 == 422` | `6bfe61ac` |

- RED-улика проверена штатным вербом: `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` (`target_test_failed`). Запись собрана из `--junit-xml` того же прогона и перегнана в TAP скриптом в scratchpad. Скрипт не закоммичен.
- На RED-коммите красны все 9 новых правил, заранее зелёных среди них нет. Причины по месту:
  - `assert 200 == 422`: неверный код, исчерпанный код, короткий пароль;
  - `'<!DOCTYPE' not in …`: верный код на htmx;
  - первый узел не `<title>`: устаревшая ссылка, адрес занят к завершению;
  - нет экранированного `value=`: враждебный ввод;
  - `assert 302 == 204`: завершение на htmx;
  - нет `hx-post="/register/verify"` на теге: две формы.
- Правила «устаревшая ссылка» и «адрес занят» без htmx уже зелёные на старом дереве: старый обработчик отдавал ту же страницу с кодом 200. Красными их делает половина htmx, утверждение `<title>` первым узлом (тот же приём, что в 14-02). Половина без htmx в RED не засчитана.
- Гейт-валидация истории: есть `test(14-03)` (2 коммита) и `feat(14-03)` (1). `refactor(14-03)` нет, он не понадобился.

## Tests outside the plan's named set

Поиск вызывающих `/register/verify`, `/register/complete` и разметки двух экранов по `tests/` нашёл только `test_access_lifecycle.py`, `test_cookie_flags.py`, `test_trial.py` и `test_impersonation_gate.py`, помимо названных планом. В `tests/conftest.py` помощников страничной регистрации нет: там только `/api/auth/register`. Все эти модули ходят без признака htmx и по успеху. 302 завершения остался 302, 200 верного кода остался 200.

Отдельно прогнаны `tests/test_templates` целиком, `tests/test_e2e.py`, `tests/test_routes/test_auth.py`, `test_shell.py`, `test_responsive_markup.py`, `test_https_asset_scheme.py`, `test_reset_code_source.py`, `test_password_reset.py`, `test_blocked_user.py`, `test_htmx_response_contract.py`, `test_impersonation.py`, `test_confirm_delete_transport.py`, `test_origin_guard_on_destructive_routes.py`, `test_access_gate.py`, `test_free_access.py`, `test_billing_subscription.py` и `test_asset_version.py`. Итог: **836 passed, 0 failed** (16:15). Вне названных планом не покраснело ни одно правило. Покраснело только `test_verify_code_wrong` (200 → 422, D-03, летопись «Фаза 14, план 14-03»), а его план называет сам.

Прогон гейтов волны (последняя команда `<verify>` задачи 2, 15 модулей): **415 passed, 0 failed** (3:06). `uv run python -m compileall -q app main.py tests` отработал без вывода. `graphify update .` выполнен.

## Files Created/Modified
- `app/pages/auth.py`: запись реестра экранов, перевод `register_verify` и `register_complete`, докстринги с оговоркой D-03
- `app/templates/auth/includes/register_complete_step.html`: экран имени и пароля
- `app/templates/auth/register_complete.html`: страница = включение экрана
- `app/templates/auth/includes/register_verify_step.html`: форма подтверждения на макросе, `hx-sync` на обеих формах, летопись окна
- `tests/test_pages/test_auth_transport.py`: 9 правил плана, докстринг правила 14-02 о форме подтверждения
- `tests/test_pages/test_htmx_gates.py`: отставание, фрагментные обработчики
- `tests/test_pages/test_htmx_post_pairs.py`: ключи, 5 посевов, 5 случаев, два числа
- `tests/test_pages/test_registration.py`: 200 → 422 (D-03)
- `tests/test_templates/test_htmx_markup_gates.py`: оба кортежа вызывающих, три числа

## Decisions Made
- Решения, отданные планом на усмотрение исполнителя, приняты так, как план их записал: занятый адрес на завершении — 200 (критерий D-03), `sync` без `include`.
- В правила `<behavior>` добавлены утверждения, которые план не называет. Ни одно утверждение `<behavior>` не снято:
  - «пароля нет» и «один подтверждённый токен» (он разбирается `decode_verification_token`);
  - «cookie нет» на ответе «адрес занят»;
  - «заголовков перехода нет» у смены экрана;
  - `<span class="user-name">` в кабинете после завершения.

## Deviations from Plan

### Оформление и замеры (поведение не менялось)

**1. [Замер] Утверждения 302 покраснели только после снятия ключа из отставания**
- **Found during:** задача 2
- **Issue:** первый прогон после GREEN не покраснил `test_the_number_of_paired_302_assertions_is_the_declared_one`. Вселенная правила исключает обработчики из `NOT_YET_CONVERTED`, а `register_complete` оставался там до правки гейтов.
- **Fix:** правка не потребовалась. После снятия ключей прогон дал `утверждений 302 о переведённых обработчиках 181, объявлено 176`. Разбор вселенной скриптом в scratchpad назвал пять записей: `test_access_lifecycle.py:108`, `test_auth_transport.py:1023`, `test_cookie_flags.py:187`, `test_registration.py:160`, `test_trial.py:99`. Прогноз плана «+4 прежних плюс новые» совпал.
- **Committed in:** `0585d145`

**2. [Оформление] Порядок записей в кортежах вызывающих**
- **Found during:** задача 2
- **Issue:** запись, дописанная после `register_verify_step.html`, дала отказ «объявленные вызывающие разошлись с измеренными». Кортеж сличается с измеренным в алфавитном порядке.
- **Fix:** запись `register_complete_step.html` стоит перед `register_step.html` в обоих кортежах. Числа поставлены после этого, в два прогона: сначала `28, объявлено 27`, затем `13, объявлено 12`.
- **Committed in:** `0585d145`

**3. [Замер] Критерий приёмки `await start_trial(` = 1 зелен и до правки**
- Это критерий сохранности, а не движения: вызов пробного срока стоял в обработчике и раньше. Его зубы держит правило `test_completing_registration_leaves_by_a_full_load_with_the_cookie_and_the_trial` (строка подписки и `GET /dashboard` → 200). Остальные критерии на дереве до правки красны: `TemplateResponse` 4 → 0, `redirect_internal` 0 → 1, `sync='closest #auth-step:drop'` 0 → 2, `value=code` 0 → 1, новый файл экрана завершения.

**4. [Процесс] Критерии, которые считают прозу летописи**
- Критерии `grep -c 'Фаза 14, план 14-03'` и `grep -c 'AUTH_REGISTER_COMPLETE'` считают текст летописи и имя ключа. Оба до правки дают 0 и растут только вместе с записью, поэтому своей прозой они не зеленеют.

---

**Total deviations:** 4 (2 замера, 1 оформление, 1 процессная оговорка). **Impact:** поведение и объём совпадают с планом: 9 файлов, ни одного сверх объявленных. `git stash` не вызывался ни разу.

## Issues Encountered
- Гейт мест 422 (`SERVER_SIDE_VALIDATION_RESPONSES = 2`) не покраснел: литерал `status_code=422` по-прежнему стоит только внутри `respond_field_error`.
- Контроль `test_control_positive_the_untouched_source_tree_keeps_every_gate_green` краснел вместе с перечнями и позеленел той же правкой. Отдельного сдвига он не требовал.

## Known Stubs

None. Экран завершения получает `email`, `token` и `name` от обработчика. Пустое поле пароля намеренно (D-04).

## Threat Flags

None. Новых поверхностей сверх `<threat_model>` нет:
- T-14-03: автоэкранирование и правило враждебного ввода на обоих транспортах;
- T-14-04: пароль не передаётся в контекст, правило «строки пароля нет»;
- T-14-06: cookie на объекте `redirect_internal`, тройное утверждение с `GET /dashboard` и пара `FULL_LOAD` с `sets_session_cookie=True`;
- T-14-16: счёт попыток прежний, правило «Осталось попыток: 4» на отдельном адресе каждой половины;
- T-14-17: `hx-sync` на обеих формах и `hx-disabled-elt` макроса.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Регистрация переведена целиком. 14-04 (восстановление «почта → экран кода» и повтор кода) опирается на те же `respond_screen`, `respond_field_error`, ветку `SCREEN` и приём эха кода. Экран кода восстановления сразу получает обе формы на макросе с тем же `sync`.
- В отставании остались 5 обработчиков: `stop_impersonation` и четыре шага восстановления пароля.
- SIGN-01, SIGN-02 и SIGN-03 НЕ отмечены Complete. Их объявляют и планы 14-04…14-07, у которых ещё нет SUMMARY (`requirements.ready-ids`).

---
*Phase: 14-avtorizatsiya-na-htmx*
*Completed: 2026-09-22*

## Self-Check: PASSED
