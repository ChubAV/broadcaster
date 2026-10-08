---
phase: 14-avtorizatsiya-na-htmx
plan: 05
subsystem: auth
tags: [htmx, fastapi, jinja2, response-layer, password-reset, 422, hx-redirect, notices, tdd]

requires:
  - phase: 14-avtorizatsiya-na-htmx
    provides: "14-04 — экраны `forgot_password` и `forgot_password_verify` в `AUTH_SCREENS`, включаемые шаблоны восстановления, ключи пар восстановления; 14-03 — приём эха кода и обеих форм экрана кода на макросе; 14-02 — `respond_screen`, ветка `SCREEN`; 14-01 — `redirect_internal`, якорь `#auth-step`, ветка `FULL_LOAD`, личность `ANONYMOUS`"
  - phase: 08-uvedomleniya
    provides: "реестр исходов `app/pages/notices.py` (`PASSWORD_RESET_DONE`) и область уведомления шелла ВНЕ якоря"
provides:
  - "`forgot_password_verify` на выходах слоя: неверный, истёкший или исчерпанный код — 422 с набранным кодом и прежним токеном; устаревшая ссылка — 200 и экран начала восстановления; верный код — 200 и экран нового пароля с подтверждённым токеном"
  - "`forgot_password_reset` на выходах слоя: короткий пароль — 422 без эха пароля с новым подтверждённым токеном; устаревшая ссылка и исчезнувший пользователь — 200 и экран начала; успех — 302 / 204 + `HX-Redirect: /login?notice=password_reset_done`, cookie сессии не выдаётся"
  - "экран `forgot_password_reset` в `AUTH_SCREENS` (семь записей); `forgot_password_reset_step.html` — единственный источник разметки экрана нового пароля"
  - "обе формы экрана кода восстановления на `form_wrapper` с целью `#auth-step` и `hx-sync=\"closest #auth-step:drop\"`; окно 14-04 закрыто"
  - "шелл окончателен: переходного блока подзаголовка в `auth_base.html` нет, каждый из семи экранов печатает подзаголовок сам"
  - "пары: 2 случая `SCREEN` подтверждения, успех нового пароля третьим случаем `FULL_LOAD` без cookie, 2 случая `SCREEN` нового пароля"
affects: [14-06, 14-07]

actuals:
  tokens: 20482
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "полная загрузка с кодом исхода: `return await redirect_internal(request, redirect=\"/login\", notice=notices.PASSWORD_RESET_DONE)` — адрес литералом, код из реестра; область уведомления шелла стоит ВНЕ якоря и переживает следующую ошибку формы"
    - "последнее место ручной склейки `?notice=` в страничном слое снято: счётчик `NOTICE_WRITE_PLACES` 1 → 0"

key-files:
  created:
    - app/templates/auth/includes/forgot_password_reset_step.html
  modified:
    - app/pages/auth.py
    - app/templates/auth_base.html
    - app/templates/auth/forgot_password_reset.html
    - app/templates/auth/includes/forgot_password_verify_step.html
    - tests/test_pages/test_auth_transport.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_password_reset.py
    - tests/test_pages/test_notices_channel.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Исчезнувший пользователь отвечает 200 через `respond_screen`, а не 422: экран меняется на начало восстановления — тот же критерий D-03, по которому 14-03 решил «адрес занят к завершению». Оговорка записана в докстринге `forgot_password_reset`"
  - "Пароль не попадает в контекст экрана нового пароля: ответ 422 передаёт только `email`, новый подтверждённый токен и текст ошибки (D-04). Правило утверждает отсутствие строки пароля в теле на обоих транспортах"
  - "Успех смены пароля НЕ выдаёт cookie сессии: человек входит новым паролем сам. Правило утверждает отсутствие `access_token` во всех заголовках `set-cookie` обеих половин"
  - "`NOTICE_WRITE_PLACES` 1 → 0 — правило вне набора плана. Ноль объявлен ЯВНО и не вакуумен: тем же прогоном обход находит место записи вне страничного слоя (`app/dependencies.py`)"

patterns-established:
  - "Экран-хвост цепочки, уходящий полной загрузкой на чужой экран с кодом исхода, утверждается одним правилом целиком: 302 / 204, отсутствие cookie, отрисовка кода ДО якоря и вход новым паролем"

requirements-completed: []

coverage:
  - id: D1
    description: "Неверный код восстановления — 422 на обоих транспортах, «Неверный код. Осталось попыток: 4», набранный код в `value=`, присланный токен скрытым полем; исчерпанный — 422 с прежним текстом и тем же эхом; с htmx первый узел `<title>Код подтверждения — Broadcaster</title>`"
    requirement: SIGN-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_wrong_recovery_code_keeps_the_typed_code_and_answers_422"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_password_reset.py#test_verify_wrong_code"
        status: pass
    human_judgment: false
  - id: D2
    description: "Верный код — 200 и экран нового пароля: страница без htmx, фрагмент с `<title>Новый пароль — Broadcaster</title>` первым узлом, `hx-post=\"/forgot-password/reset\"`, один подтверждённый токен, без заголовков перехода"
    requirement: SIGN-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_right_recovery_code_opens_the_new_password_screen"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports (2 случая подтверждения)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Короткий новый пароль — 422, текст дословно, строки пароля в теле нет, один новый подтверждённый токен восстановления; устаревшая ссылка и исчезнувший пользователь — 200 и экран начала с прежними текстами"
    requirement: SIGN-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_short_new_password_answers_422_without_echo_on_both_transports"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_stale_recovery_links_return_to_the_start_with_200"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_vanished_user_returns_to_the_start_of_recovery_with_200"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_password_reset.py#test_reset_short_password"
        status: pass
    human_judgment: false
  - id: D4
    description: "Новый пароль без htmx — 302 на `/login?notice=password_reset_done`; с htmx — 204, `HX-Redirect` тем же адресом, без `HX-Location`, пустое тело; cookie сессии нет ни на одном; `/login` с этим кодом рисует «Пароль успешно изменён. Войдите с новым паролем.» ДО якоря; вход новым паролем — 302 на `/dashboard`"
    requirement: SIGN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[forgot_password_reset-новый пароль — успех]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_password_reset.py#test_complete_password_reset"
        status: pass
    human_judgment: false
  - id: D5
    description: "Под чужой личностью подтверждение кода и новый пароль: без htmx 403, с htmx 204 + `HX-Location: /dashboard?notice=impersonation_forbidden` без тела; хеш пароля пользователя прежний"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_the_last_recovery_steps_are_refused_under_another_identity_on_both_transports"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py (4 шага восстановления, 403 без htmx)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Обе формы экрана кода восстановления рождены `form_wrapper` с `hx-target=\"#auth-step\"`, `hx-swap=\"innerHTML\"` и `hx-sync=\"closest #auth-step:drop\"`; форма нового пароля — `form_wrapper` в тот же якорь"
    requirement: SIGN-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_both_recovery_code_forms_ride_the_anchor_and_drop_a_second_request"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py (83 passed)"
        status: pass
    human_judgment: false
  - id: D7
    description: "Шелл окончателен: `auth_subtitle` нет ни в `auth_base.html`, ни в одной странице `auth/*.html`; в `AUTH_SCREENS` семь записей, и их страницы — ровно множество `app/templates/auth/*.html`; `/login`, `/register`, `/forgot-password` несут ровно один непустой подзаголовок"
    requirement: SIGN-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_the_shell_leaves_the_subtitle_to_every_screen"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py, tests/test_pages/test_responsive_markup.py, tests/test_templates (полный прогон)"
        status: pass
    human_judgment: false
  - id: D8
    description: "Перечни поставлены прогоном: отставание 3 → 1, фрагментные обработчики 23 → 25, пары 71 → 76, утверждения 302 181 → 184, вызывающие 30 → 31, параметрические 15 → 16, блоки вызова 26 → 28, места записи кода исхода 1 → 0"
    verification:
      - kind: unit
        ref: "прогон гейтов волны (последняя команда `<verify>` задачи 2, 14 модулей): 679 passed"
        status: pass
    human_judgment: false
  - id: D9
    description: "В браузере восстановление с кодом из настоящего письма доходит до `/login` с плашкой об изменении пароля, и вход новым паролем проходит"
    requirement: SIGN-03
    verification: []
    human_judgment: true
    rationale: "Поведение браузера (подмена якоря без перезагрузки, заголовок вкладки, переход по HX-Redirect, сохранение пароля менеджером) и доставка настоящего письма тестами не измеряются. Это ручной UAT фазы (критерий 4, D-02)"

duration: 46min
completed: 2026-09-22
status: complete
plan_head_before: 6c095bbc3071c54eded8fde2f740226b254287aa
commits: 3
---

# Phase 14 Plan 05: Восстановление «код → новый пароль → вход с уведомлением» на фрагментах — Summary

**Подтверждение кода восстановления и новый пароль отвечают через выходы слоя за якорем `#auth-step`. Неверный код и короткий пароль дают 422 на том же экране: набранный код возвращается в поле, пароль не возвращается никогда. Успех уходит полной загрузкой на `/login` с кодом исхода — 302 без htmx, 204 + `HX-Redirect` с ним, cookie сессии не выдаётся, — и плашку «Пароль успешно изменён» рисует область уведомления шелла ВНЕ якоря. Обе формы экрана кода переведены на макрос с `hx-sync`, шелл освобождён от переходного блока подзаголовка: все семь экранов печатают его сами.**

## Performance

- **Duration:** 46 min
- **Started:** 2026-09-22T16:40:58Z
- **Completed:** 2026-09-22T17:27:21Z
- **Tasks:** 2
- **Files modified:** 11 (1 новый, 10 изменённых). Десять — ровно файлы, объявленные планом; одиннадцатый (`test_notices_channel.py`) — счётчик вне набора плана, найденный прогоном соседних модулей

## Accomplishments
- `app/pages/auth.py`: запись `forgot_password_reset` в `AUTH_SCREENS` — в реестре все семь экранов второго шелла. В `forgot_password_verify` сняты четыре возврата `TemplateResponse`, в `forgot_password_reset` — три `TemplateResponse` и один `RedirectResponse` (D-14). Не тронуты зависимость отказа под чужой личностью, запрос кода, счёт попыток с `commit` до ответа, отметка подтверждения, выдача подтверждённого токена с `purpose="password_reset"`, хеширование пароля и все тексты (D-13, D-15). Комментарий FOUND-05 над выходом успеха сохранён и дополнен строкой о полной загрузке на пути htmx (D-10).
- `forgot_password_reset_step.html` — единственный источник разметки экрана нового пароля; страница `forgot_password_reset.html` сведена к `extends` + `title` + одно включение, блока `auth_subtitle` в ней больше нет.
- `forgot_password_verify_step.html`: форма подтверждения — блочный вызов `form_wrapper` с `value=code or ''`; обе формы получили `sync='closest #auth-step:drop'`. Абзац шапки об окне 14-04 не стёрт, к нему дописана летопись закрытия окна и оговорка о цене синхронизации.
- `auth_base.html`: переходный блок подзаголовка снят вместе со своим абзацем разметки; якорь содержит только блок содержимого. Прежний абзац шапки о переходном блоке не стёрт, к нему дописана летопись снятия. Правило CSS `.auth-subtitle` не менялось — подзаголовок экрана по-прежнему визуально под брендом.
- Гейты сдвинуты прогоном, у каждого числа летопись «Фаза 14, план 14-05» с дословным выводом: `NOT_YET_CONVERTED_COUNT` 3 → 1, `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 23 → 25, `POST_PAIR_CASES_DECLARED` 71 → 76, `PAIRED_302_ASSERTIONS_DECLARED` 181 → 184, `MACRO_DEFINITION_SITES_CALLERS_DECLARED` 30 → 31, `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` 15 → 16, `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` 26 → 28, `NOTICE_WRITE_PLACES` 1 → 0.

## Task Commits

1. **Задача 1: восстановление «код → новый пароль → вход с уведомлением», обе формы экрана кода на макросе, шелл без переходного блока.** RED `1584ef20` (test), GREEN `5b3b91c5` (feat).
2. **Задача 2: перечни и прежние утверждения об ошибках кода и пароля.** `4eda0ee0` (test: record).

**Plan metadata:** коммит `docs(14-05)` с этим файлом; STATE/ROADMAP идут отдельным коммитом записи.

## TDD Gate Compliance

| Задача | RED commit | Красное утверждение (дословно из прогона) | GREEN commit |
|---|---|---|---|
| 1 | `1584ef20` | `assert 200 == 422` в `test_a_short_new_password_answers_422_without_echo_on_both_transports`. Вывод `uv run pytest tests/test_pages/test_auth_transport.py -q -p no:randomly -k short_new_password` содержит все три совпадения `<tdd_notes>`: строку `FAILED tests/test_pages/test_auth_transport.py::test_a_short_new_password_answers_422_without_echo_on_both_transports`, итог `1 failed, 39 deselected` и литерал `assert 200 == 422` | `5b3b91c5` |

- RED-улика проверена штатным вербом: `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` (`target_test_failed`, exit 1). Запись собрана из `--junit-xml` того же прогона и перегнана в TAP скриптом в scratchpad. Скрипт не закоммичен.
- На RED-коммите красны 8 из 9 новых правил (`8 failed`). Причины по месту:
  - `assert 200 == 422`: короткий новый пароль, неверный код восстановления;
  - `'<!DOCTYPE' not in …`: верный код на htmx;
  - первый узел не `<title>`: устаревшая ссылка (оба адреса), исчезнувший пользователь;
  - `assert 302 == 204`: новый пароль на htmx;
  - нет `hx-post="/forgot-password/verify"` на теге: обе формы экрана кода;
  - `'auth_subtitle' not in …`: шелл.
- **Правило отказа под чужой личностью (`test_the_last_recovery_steps_are_refused_under_another_identity_on_both_transports`) зелено уже на RED-коммите, и это ожидаемо, а не заранее готовая фича** — тот же случай, что и в 14-04. Зависимость отказа уже отвечает двумя транспортами, план её не трогает (D-13). В RED оно не засчитано. Его зубы: годные токены (отказ обязан стоять ДО разбора токена), 204 + `HX-Location` + пустое тело и «хеш пароля пользователя прежний».
- Половины без htmx у правил «устаревшая ссылка» и «исчезнувший пользователь» зелены на старом дереве: старый обработчик отдавал ту же страницу с кодом 200. Красными их делает половина htmx (`<title>` первым узлом). Половина без htmx в RED не засчитана.
- Гейт-валидация истории: есть `test(14-05)` (2 коммита) и `feat(14-05)` (1). `refactor(14-05)` нет, он не понадобился.

## Tests outside the plan's named set

Поиск `/forgot-password` и `forgot_password` по `tests/` нашёл, помимо модулей плана, только `test_impersonation.py`, `test_impersonation_gate.py`, `test_reset_code_source.py` и `test_shell.py`. Помощников восстановления в `tests/conftest.py` нет. Правка шелла задевает КАЖДУЮ страницу авторизации, поэтому отдельно прогнаны все правила оболочки, отзывчивости и разметки.

Прогнаны: `tests/test_templates` целиком, `tests/test_e2e.py`, `tests/test_routes/test_auth.py`, `test_responsive_markup.py`, `test_https_asset_scheme.py`, `test_blocked_user.py`, `test_htmx_response_contract.py`, `test_confirm_delete_transport.py`, `test_origin_guard_on_destructive_routes.py`, `test_access_gate.py`, `test_free_access.py`, `test_asset_version.py`, `test_registration.py`, `test_cookie_flags.py`, `test_notices_channel.py`, `test_access_lifecycle.py`, `test_trial.py`. Итог: **601 passed, 1 failed** (4:46). Покраснело ровно одно правило вне набора плана — `test_notices_channel.py::test_the_number_of_notice_writers_is_the_declared_one` (см. Deviations 1). После его сдвига модуль даёт **57 passed**.

`test_impersonation.py` и `test_shell.py` прогнаны первой командой `<verify>` задачи 1 вместе с `test_auth_transport.py`: **324 passed, 0 failed** (12:17). Задача 2, первая команда: **144 passed** (1:36). Прогон гейтов волны (последняя команда `<verify>` задачи 2, 14 модулей): **679 passed, 0 failed** (14:34). `uv run python -m compileall -q app main.py tests` отработал без вывода. `graphify update .` выполнен.

Полного прогона суиты план не содержит; его делает оркестратор после возврата — на дереве, включающем эти коммиты.

## Files Created/Modified
- `app/pages/auth.py`: запись реестра экранов, перевод `forgot_password_verify` и `forgot_password_reset`, докстринги с оговорками D-03, D-04, D-10, D-13
- `app/templates/auth/includes/forgot_password_reset_step.html`: экран нового пароля (новый файл)
- `app/templates/auth/forgot_password_reset.html`: страница = включение экрана
- `app/templates/auth/includes/forgot_password_verify_step.html`: форма подтверждения на макросе с эхом кода, `hx-sync` на обеих формах, летопись закрытия окна
- `app/templates/auth_base.html`: якорь без переходного блока подзаголовка, летопись снятия
- `tests/test_pages/test_auth_transport.py`: 9 правил плана, летопись окна 14-04
- `tests/test_pages/test_htmx_gates.py`: отставание, фрагментные обработчики
- `tests/test_pages/test_htmx_post_pairs.py`: два ключа, 5 посевов, 5 случаев, два числа
- `tests/test_templates/test_htmx_markup_gates.py`: оба кортежа вызывающих, `reason`, три числа
- `tests/test_pages/test_password_reset.py`: 200 → 422 в двух правилах (D-03)
- `tests/test_pages/test_notices_channel.py`: `NOTICE_WRITE_PLACES` 1 → 0 (вне набора плана)

## Decisions Made
- Решения, отданные планом на усмотрение исполнителя, приняты так, как план их записал: исчезнувший пользователь — 200 (критерий D-03), `sync` без `include`, адрес `/login` литералом.
- В правила `<behavior>` добавлены утверждения, которые план не называет. Ни одно утверждение `<behavior>` не снято:
  - «строки нового пароля нет» и «один подтверждённый токен восстановления» (он разбирается `decode_verification_token` с проверкой `purpose`) у устаревшей ссылки, исчезнувшего пользователя и короткого пароля;
  - «заголовков перехода нет» у смены экрана на верном коде;
  - страница/фрагмент (`<!DOCTYPE`) на обеих половинах правил кода и короткого пароля;
  - «хеш пароля прежний» читается ОТДЕЛЬНЫМ запросом колонки, а не из кэша сессии.
- Правило шелла утверждает не только отсутствие блока, но и то, что реестр экранов накрывает РОВНО множество страниц `auth/*.html`: иначе «ни одна страница блок не объявляет» было бы зелено вакуумом для страницы вне реестра.

## Deviations from Plan

### Оформление и замеры (поведение не менялось)

**1. [Замер, файл вне набора плана] `NOTICE_WRITE_PLACES` 1 → 0**
- **Found during:** задача 2, прогон соседних модулей
- **Issue:** `test_notices_channel.py::test_the_number_of_notice_writers_is_the_declared_one` отказал: «мест записи в страничном слое 0, а объявлено 1: {'app/dependencies.py': 1}». Новый пароль был ПОСЛЕДНИМ местом, где адрес с кодом исхода склеивался руками в страничном слое; теперь его собирает `redirect_internal`.
- **Fix:** число сдвинуто ПРОГОНОМ покрасневшего правила, летопись «Фаза 14, план 14-05» с дословным выводом. Ноль объявлен явно и не вакуумен: тем же прогоном обход находит место записи вне страничного слоя (`app/dependencies.py`), то есть выражение по-прежнему видит запись там, где она есть. Правило осиротевших кодов зелено: `PASSWORD_RESET_DONE` по-прежнему упоминается константой реестра в обработчике.
- **Files modified:** `tests/test_pages/test_notices_channel.py`
- **Verification:** `uv run pytest tests/test_pages/test_notices_channel.py -q -p no:randomly` — 57 passed
- **Committed in:** `4eda0ee0`

**2. [Замер] Третье утверждение 302 пришло не от перевода**
- **Found during:** задача 2
- **Issue:** план ждал «+1 прежнее плюс новые», прогон дал 181 → 184. Разбор вселенной скриптом в scratchpad назвал три записи: `test_password_reset.py:165` (прежнее, новый пароль), `test_auth_transport.py:1724` (новое, новый пароль) и `test_auth_transport.py:1768` — утверждение 302 ВХОДА новым паролем.
- **Fix:** правка не потребовалась. Третья запись вошла во вселенную не переводом этого плана, а новым правилом о давно переведённом входе (план 14-01), и это записано в летописи числа отдельной строкой — иначе число выглядело бы как «перевод дал три».
- **Committed in:** `4eda0ee0`

**3. [Оформление] Порядок записей в кортежах вызывающих**
- **Found during:** задача 2
- **Issue:** кортежи сличаются в алфавитном порядке, а `forgot_password_reset_step.html` встаёт ПЕРЕД `forgot_password_step.html`.
- **Fix:** запись поставлена на своё место в обоих кортежах. Числа поставлены по порядку отказов: сначала `спрятано вызывающих 31, объявлено 30`, затем `спрятано вызывающих 16, объявлено 15`, отдельно `блоков вызова разобрано 28, объявлено 26`. Текст `reason` параметрической записи пополнен абзацем о шестнадцатом вызывающем с замером G-9 / G-11 / G-12 (1 / 0 / 0).
- **Committed in:** `4eda0ee0`

**4. [Замер] Критерии сохранности и критерии, считающие прозу летописи**
- Критерии задачи 1 на дереве до правки красны все: `TemplateResponse` 4 → 0 и 3 → 0, `redirect_internal(...)` 0 → 1, `auth_subtitle` 1 → 0 в шелле и 1 → 0 страниц, `sync='closest #auth-step:drop'` 0 → 2. Зелёных до правки среди них нет.
- Критерии задачи 2 до правки тоже красны: ключей отставания 3 → 1, `AUTH_FORGOT_RESET` 0 → 4, `Фаза 14, план 14-05` 0 → 5, `forgot_password_reset_step.html` в гейте разметки 0 → 6. Два последних считают прозу летописи и имя ключа, но растут только вместе с записью, поэтому своей прозой не зеленеют.

---

**Total deviations:** 4 (3 замера, 1 оформление). Из них одна — правка файла вне десяти объявленных планом (`test_notices_channel.py`), вынужденная и записанная выше. **Impact:** поведение совпадает с планом; сверх объявленного тронут один тестовый файл, продуктовый код — ровно объявленный. `git stash` не вызывался ни разу.

## Issues Encountered
- Гейт мест 422 (`SERVER_SIDE_VALIDATION_RESPONSES`) не покраснел: литерал `status_code=422` по-прежнему стоит только внутри `respond_field_error`.
- Контроли `test_control_positive_the_untouched_source_tree_keeps_every_gate_green` (гейты), `test_control_positive_the_untouched_tree_keeps_every_gate_green` (разметка) и `test_control_negative_an_undeclared_fragment_handler_reddens_the_gate` краснели вместе с перечнями и позеленели той же правкой. Отдельного сдвига они не требовали.

## Known Stubs

None. Экран нового пароля получает `email`, `token` и текст ошибки от обработчика. Пустое поле пароля намеренно (D-04).

## Threat Flags

None. Новых поверхностей сверх `<threat_model>` нет:
- T-14-13: зависимость отказа не тронута, правило на обоих транспортах с проверкой «хеш пароля прежний»;
- T-14-04: пароль не передаётся в контекст (сборщики его не примут), правило «строки пароля нет» на трёх исходах;
- T-14-01: код исхода из реестра, адрес `/login` литералом, сборка адреса — `redirect_internal` → `_with_notice` → `_local_path`; ручных склеек `?notice=` в страничном слое не осталось вовсе;
- T-14-16: счёт попыток и лимит прежние, правило «Осталось попыток: 4» и «код истёк или превышено число попыток» на отдельных адресах.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Восстановление пароля переведено целиком, все семь экранов второго шелла — включаемые шаблоны, шелл окончателен. 14-06 остаётся один обработчик отставания — возврат из-под чужой личности (`stop_impersonation`), и критерий 3 с перечнем всех вызывающих полную перезагрузку.
- Летописи ROADMAP / REQUIREMENTS / PROJECT, окно 63 и `14-UAT.md` — за 14-07, как объявляет §artifacts_this_phase_produces.
- SIGN-01, SIGN-02 и SIGN-03 НЕ отмечены Complete: их объявляют и планы 14-06/14-07, у которых ещё нет SUMMARY (`requirements.ready-ids`).

---
*Phase: 14-avtorizatsiya-na-htmx*
*Completed: 2026-09-22*

## Self-Check: PASSED
