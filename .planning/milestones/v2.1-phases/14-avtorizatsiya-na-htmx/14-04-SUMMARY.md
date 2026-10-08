---
phase: 14-avtorizatsiya-na-htmx
plan: 04
subsystem: auth
tags: [htmx, fastapi, jinja2, response-layer, password-reset, 422, impersonation, tdd]

requires:
  - phase: 14-avtorizatsiya-na-htmx
    provides: "14-02 — `respond_screen`, ветка пар `SCREEN`, приём экрана кода с обычной формой подтверждения; 14-01 — `AUTH_SCREENS`, `_screen_builders`, `step_response.html`, якорь `#auth-step`, личность `ANONYMOUS`"
  - phase: 06-admin
    provides: "`forbid_when_impersonating` с двумя транспортами отказа (D-22), `IMPERSONATION_REFUSED_LOCATION`"
provides:
  - "`forgot_password_send_code` и `forgot_password_resend_code` на выходах слоя: 422 — тот же экран, 200 — экран сменился (D-03)"
  - "экраны `forgot_password` и `forgot_password_verify` в `AUTH_SCREENS`; включаемые шаблоны `forgot_password_step.html`, `forgot_password_verify_step.html`"
  - "форма адреса и форма повтора кода восстановления через `form_wrapper` в `#auth-step` (innerHTML); повтор перерисовывает обе формы одним токеном"
  - "правило отказа под чужой личностью на обоих транспортах для двух переведённых шагов, с проверкой «кода не заведено»"
  - "ключи пар `AUTH_FORGOT_SEND_CODE`, `AUTH_FORGOT_RESEND_CODE`, 3 случая ветки `SCREEN`"
affects: [14-05, 14-06, 14-07]

actuals:
  tokens: 15952
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "смена экрана восстановления: page, fragment = _screen_builders(request, 'forgot_password_verify', ...); return await respond_screen(...)"
    - "посев пар восстановления: пользователь ORM на уникальный адрес каждого вызова (счётчик модуля)"

key-files:
  created:
    - app/templates/auth/includes/forgot_password_step.html
    - app/templates/auth/includes/forgot_password_verify_step.html
  modified:
    - app/pages/auth.py
    - app/templates/auth/forgot_password.html
    - app/templates/auth/forgot_password_verify.html
    - tests/test_pages/test_auth_transport.py
    - tests/test_pages/test_password_reset.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Форма подтверждения кода восстановления оставлена обычной формой (окно до 14-05) по §scope_note плана, вопреки строке «Next Phase Readiness» сводки 14-03"
  - "Правило отказа под чужой личностью зелено уже на дереве до правки (зависимость не тронута, D-13); в RED оно не засчитано, красное несут шесть других правил"
  - "PAIRED_302_ASSERTIONS_DECLARED не двигается (181 → 181): у двух шагов нет исхода 302, неподвижность записана строкой летописи"

patterns-established:
  - "Экран кода восстановления: форма подтверждения — обычная форма до 14-05, форма повтора — `form_wrapper` в `#auth-step`"

requirements-completed: [SIGN-01, SIGN-02]

coverage:
  - id: D1
    description: "Неизвестный адрес — 422, «Пользователь с таким email не найден», адрес в `value=`; с htmx первый узел `<title>Забыли пароль — Broadcaster</title>`, без htmx — страница"
    requirement: SIGN-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_an_unknown_email_keeps_the_address_and_answers_422_on_both_transports"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_password_reset.py#test_send_code_unknown_email"
        status: pass
    human_judgment: false
  - id: D2
    description: "Известный адрес — 200 и экран кода на обоих транспортах; токен скрытым полем; с htmx `<title>Код подтверждения — Broadcaster</title>` первым узлом, форма повтора из макроса, форма подтверждения — настоящий POST, заголовков перехода нет; «код уже отправлен» — 200 на экране кода"
    requirement: SIGN-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_the_recovery_email_step_answers_the_code_screen_on_both_transports"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_a_repeated_recovery_step_within_a_minute_lands_on_the_code_screen"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports (3 случая восстановления)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Повтор кода восстановления — 200, «Новый код отправлен на вашу почту.», два скрытых `token` с одним значением; раньше минуты — 422 с присланным токеном; устаревшая ссылка — 200 и экран начала с «Ссылка устарела. Начните сброс пароля заново.»"
    requirement: SIGN-02
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_resending_the_recovery_code_redraws_both_forms_with_one_token"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_resending_the_recovery_code_within_a_minute_answers_422"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_resending_with_a_stale_recovery_link_returns_to_the_start"
        status: pass
    human_judgment: false
  - id: D4
    description: "Под чужой личностью `send-code` и `resend-code`: без htmx 403, с htmx 204 + `HX-Location: /dashboard?notice=impersonation_forbidden` без тела; строк кода восстановления не прибавилось"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_auth_transport.py#test_the_first_recovery_steps_are_refused_under_another_identity_on_both_transports"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_password_change_is_refused_under_another_identity"
        status: pass
    human_judgment: false
  - id: D5
    description: "Форма адреса и форма повтора рождены `form_wrapper` с целью `#auth-step`; гейты перечней сдвинуты прогоном"
    requirement: SIGN-01
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py (83 passed)"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py (53 passed)"
        status: pass
    human_judgment: false
  - id: D6
    description: "В браузере восстановление для существующего ящика показывает экран кода без перезагрузки, вкладка меняет заголовок; настоящее письмо с кодом приходит"
    requirement: SIGN-01
    verification: []
    human_judgment: true
    rationale: "Поведение браузера (подмена без перезагрузки, заголовок вкладки) и доставка настоящего письма сервером не измеряются — ручной UAT фазы (критерий 4, D-02)"

duration: 35min
completed: 2026-09-22
status: complete
plan_head_before: 65804ef564905292ef78574e785a4852e5d2c531
commits: 3
---

# Phase 14 Plan 04: Восстановление пароля «почта → экран кода» и повтор кода на фрагментах — Summary

**Шаг адреса восстановления и повтор кода отвечают через `respond_field_error` и `respond_screen` за якорем `#auth-step`. Неизвестный адрес и повтор раньше минуты дают 422 на том же экране с эхом, смена экрана — 200 со страницей без JS и фрагментом с `<title>` первым узлом. Токен восстановления едет только скрытым полем обеих форм. Отказ под чужой личностью утверждён на обоих транспортах: 403 без htmx, 204 + `HX-Location` с ним, кода не заводится.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-09-22T15:20:07Z
- **Completed:** 2026-09-22T15:56:00Z
- **Tasks:** 2
- **Files modified:** 10 (2 новых, 8 изменённых), ровно объявленные планом

## Accomplishments
- `app/pages/auth.py`: записи `forgot_password` и `forgot_password_verify` в `AUTH_SCREENS`. В `forgot_password_send_code` сняты три возврата `TemplateResponse`, в `forgot_password_resend_code` — три (D-14). Докстринги с оговорками D-03, D-06, D-13. Зависимость `forbid_when_impersonating`, запросы, минута, срок, `secrets.randbelow` (4 места), письмо, тексты и комментарий D-22 над блоком не тронуты (D-13, D-15).
- Шаблоны: `forgot_password_step.html` и `forgot_password_verify_step.html` — единственные источники разметки экранов. Страницы `forgot_password.html` и `forgot_password_verify.html` сведены к `extends` + `title` + одно включение. `forgot_password_verify` (страница) и `forgot_password_reset` (14-05) по-прежнему рисуют эти страницы готовыми `TemplateResponse` — через то же включение.
- Гейты сдвинуты прогоном, у каждого числа летопись «Фаза 14, план 14-04» с дословным выводом: `NOT_YET_CONVERTED_COUNT` 5 → 3, `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 21 → 23, `POST_PAIR_CASES_DECLARED` 68 → 71, `PAIRED_302_ASSERTIONS_DECLARED` 181 → 181 (неподвижность записана), `MACRO_DEFINITION_SITES_CALLERS_DECLARED` 28 → 30, `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` 13 → 15, `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` 24 → 26.

## Task Commits

1. **Задача 1: восстановление «почта → экран кода» и повтор кода, отказ под чужой личностью на htmx.** RED `86caa7cf` (test), GREEN `b298a635` (feat).
2. **Задача 2: перечни и прежнее утверждение об ошибке адреса.** `06b14791` (test: record).

**Plan metadata:** коммит `docs(14-04)` с этим файлом; STATE/ROADMAP — отдельным коммитом записи.

## TDD Gate Compliance

| Задача | RED commit | Красное утверждение (дословно из прогона) | GREEN commit |
|---|---|---|---|
| 1 | `86caa7cf` | `assert 200 == 422` в `test_an_unknown_email_keeps_the_address_and_answers_422_on_both_transports`. Вывод `uv run pytest tests/test_pages/test_auth_transport.py -q -p no:randomly -k unknown_email` содержит все три совпадения `<tdd_notes>`: строку `FAILED tests/test_pages/test_auth_transport.py::test_an_unknown_email_keeps_the_address_and_answers_422_on_both_transports`, итог `1 failed, 30 deselected` и литерал `assert 200 == 422` | `b298a635` |

- RED-улика проверена штатным вербом: `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` (`target_test_failed`). Запись собрана из `--junit-xml` того же прогона и перегнана в TAP скриптом в scratchpad. Скрипт не закоммичен.
- На RED-коммите красны 6 из 7 новых правил (`6 failed, 1 passed`). Причины по месту:
  - `assert 200 == 422`: неизвестный адрес, повтор раньше минуты;
  - `слою письма приехал целый документ`: шаг адреса на htmx;
  - первый узел не `<title>`: «код уже отправлен», повтор кода, устаревшая ссылка.
- Половины без htmx у правил «код уже отправлен», «повтор кода» и «устаревшая ссылка» зелены на старом дереве: старый обработчик отдавал ту же страницу с кодом 200. Красными их делает половина htmx (`<title>` первым узлом). Половина без htmx в RED не засчитана.
- **Правило отказа под чужой личностью (`..._refused_under_another_identity_on_both_transports`) зелено уже на RED-коммите, и это ожидаемо, а не заранее готовая фича.** План сам говорит: зависимость отказа уже отвечает двумя транспортами (D-13), правило только закрепляет её половину htmx на переведённых шагах. В RED оно не засчитано. Его зубы: 204 + `HX-Location` + пустое тело + «строк `password_reset` не прибавилось», при годном токене восстановления, чтобы отказ не сливался с «ссылка устарела».
- Гейт-валидация истории: есть `test(14-04)` (2 коммита) и `feat(14-04)` (1). `refactor(14-04)` нет, он не понадобился.

## Tests outside the plan's named set

Поиск `/forgot-password` и `forgot_password` по `tests/` нашёл, помимо модулей плана, только `test_shell.py`, `test_impersonation_gate.py` и `test_reset_code_source.py`. В `tests/conftest.py` помощников восстановления нет. `test_shell.py` открывает `GET /forgot-password`, `test_reset_code_source.py` ходит по успеху (200 остался 200), `test_impersonation.py` утверждает 403 четырёх шагов без htmx (403 остался 403).

Отдельно прогнаны `tests/test_templates` целиком, `tests/test_e2e.py`, `tests/test_routes/test_auth.py`, `test_shell.py`, `test_responsive_markup.py`, `test_https_asset_scheme.py`, `test_reset_code_source.py`, `test_password_reset.py`, `test_blocked_user.py`, `test_htmx_response_contract.py`, `test_impersonation.py`, `test_impersonation_gate.py`, `test_confirm_delete_transport.py`, `test_origin_guard_on_destructive_routes.py`, `test_access_gate.py`, `test_free_access.py`, `test_asset_version.py`, `test_registration.py` и `test_cookie_flags.py`. Итог: **853 passed, 0 failed** (16:17). Вне названных планом не покраснело ни одно правило. Покраснело только `test_send_code_unknown_email` (200 → 422, D-03, летопись «Фаза 14, план 14-04, D-03»), а его план называет сам.

Прогон гейтов волны (последняя команда `<verify>` задачи 2, 13 модулей): **453 passed, 0 failed** (3:57). Первая команда задачи 2: 139 passed. Задача 1: 76 passed. `uv run python -m compileall -q app main.py tests` отработал без вывода. `graphify update .` выполнен.

## Files Created/Modified
- `app/pages/auth.py`: две записи реестра экранов, перевод `forgot_password_send_code` и `forgot_password_resend_code`, докстринги
- `app/templates/auth/includes/forgot_password_step.html`: экран начала восстановления
- `app/templates/auth/includes/forgot_password_verify_step.html`: экран кода восстановления (две формы на одном токене, подтверждение — обычная форма до 14-05)
- `app/templates/auth/forgot_password.html`, `forgot_password_verify.html`: страницы = включение экрана
- `tests/test_pages/test_auth_transport.py`: 7 правил восстановления
- `tests/test_pages/test_password_reset.py`: 200 → 422 (D-03)
- `tests/test_pages/test_htmx_gates.py`: отставание, фрагментные обработчики
- `tests/test_pages/test_htmx_post_pairs.py`: ключи, 3 посева, 3 случая, два числа
- `tests/test_templates/test_htmx_markup_gates.py`: оба кортежа вызывающих, `reason`, три числа

## Decisions Made
- Конфликт объёма разрешён по плану. Сводка 14-03 говорит, что экран кода восстановления «сразу получает обе формы на макросе с тем же sync», но §scope_note плана 14-04 это запрещает. Форма подтверждения осталась обычной формой (`action="/forgot-password/verify"`), `hx-sync` и эха кода нет. Это окно 14-05, и оно названо в шапке шаблона.
- В правила `<behavior>` добавлены утверждения, которые план не называет. Ни одно утверждение `<behavior>` не снято:
  - `<title>` первым узлом на половине htmx у «код уже отправлен», повтора раньше минуты и повтора (без этого три правила были бы зелены до правки);
  - `name="token"` у «код уже отправлен»;
  - «форма подтверждения — настоящий POST» во фрагменте шага адреса;
  - годный токен восстановления в правиле отказа.

## Deviations from Plan

### Оформление и замеры (поведение не менялось)

**1. [Замер] Правило отказа под чужой личностью зелено до правки**
- **Found during:** задача 1 (RED)
- **Issue:** `6 failed, 1 passed` на RED-коммите: зелёное — правило отказа. Зависимость отказа уже отвечает двумя транспортами, план её не трогает (D-13).
- **Fix:** правка не потребовалась. В RED правило не засчитано, факт записан выше и в сообщении RED-коммита.
- **Committed in:** `86caa7cf`

**2. [Замер] Критерии сохранности зелены и до правки**
- `Depends(forbid_when_impersonating)` = 1 в каждом обработчике и `secrets.randbelow` = 4 — критерии сохранности, а не движения: на дереве до правки они те же. Движение держат `TemplateResponse` 3 → 0 в каждом обработчике и `target='#auth-step'` 0 → 1 в каждом новом шаблоне.
- Критерии задачи 2 до правки красны: `NOT_YET_CONVERTED` 2 → 0 ключей, `AUTH_FORGOT_SEND_CODE` 0 → 2, `Фаза 14, план 14-04` 0 → 5, `forgot_password_verify_step.html` в гейте разметки 0 → 6. Два последних считают прозу летописи, но растут только вместе с записью, так что своей прозой не зеленеют.

**3. [Замер] Утверждения 302 не двигаются**
- Прогноз плана «второе не двигается» совпал: `test_the_number_of_paired_302_assertions_is_the_declared_one` зелен на 181 после перевода и снятия ключей. Неподвижность записана строкой летописи.
- **Committed in:** `06b14791`

**4. [Оформление] Порядок записей в кортежах вызывающих**
- Кортежи сличаются в алфавитном порядке, поэтому обе записи восстановления стоят перед `login_step.html`. Числа поставлены по порядку отказов: сначала `спрятано вызывающих 30, объявлено 28` и `разобрано 26, объявлено 24`, затем `спрятано вызывающих 15, объявлено 13`. Текст `reason` параметрической записи пополнен абзацем о 14-м и 15-м вызывающих с замером G-9 / G-11 / G-12.
- **Committed in:** `06b14791`

---

**Total deviations:** 4 (3 замера, 1 оформление). **Impact:** поведение и объём совпадают с планом: 10 файлов, ни одного сверх объявленных. `git stash` не вызывался ни разу.

## Issues Encountered
- Гейт мест 422 (`SERVER_SIDE_VALIDATION_RESPONSES`) не покраснел: литерал `status_code=422` по-прежнему стоит только внутри `respond_field_error`.
- Контроль `test_control_positive_the_untouched_source_tree_keeps_every_gate_green` (гейты) и `test_control_positive_the_untouched_tree_keeps_every_gate_green` (разметка) краснели вместе с перечнями и позеленели той же правкой. Отдельного сдвига они не требовали.

## Known Stubs

None. Оба экрана получают данные от обработчиков. Пустой `email` на `GET /forgot-password` — нормальное начальное состояние поля.

## Threat Flags

None. Новых поверхностей сверх `<threat_model>` нет:
- T-14-13: зависимость отказа не тронута, правило на обоих транспортах с проверкой «кода не заведено»;
- T-14-03: эхо адреса автоэкранируется через макрос `field` (фильтра безопасной разметки нет), разметочный гейт безопасности зелен;
- T-14-07: токен только скрытым полем, правило «заголовков перехода нет» на смене экрана.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 14-05 (подтверждение кода восстановления и новый пароль) садится на готовое: экран `forgot_password_verify` в реестре, `forgot_password` для возврата на начало. Ему остаются перевод формы подтверждения на `form_wrapper` (сейчас это обычная форма, окно названо в шаблоне), эхо кода, `hx-sync` на обеих формах, экран `forgot_password_reset` и снятие переходного блока подзаголовка шелла.
- В отставании остались 3 обработчика: `stop_impersonation`, `forgot_password_verify`, `forgot_password_reset`.
- SIGN-01 и SIGN-02 НЕ отмечены Complete: их объявляют и планы 14-05…14-07, у которых ещё нет SUMMARY (`requirements.ready-ids`).

---
*Phase: 14-avtorizatsiya-na-htmx*
*Completed: 2026-09-22*

## Self-Check: PASSED
