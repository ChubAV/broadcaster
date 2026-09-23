---
phase: 14-avtorizatsiya-na-htmx
verified: 2026-09-23T08:15:00Z
status: human_needed
score: 12/13 must-haves verified
covered_files:
  - ".planning/REQUIREMENTS.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-01-PLAN.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-01-SUMMARY.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-02-PLAN.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-02-SUMMARY.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-03-PLAN.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-03-SUMMARY.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-04-PLAN.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-04-SUMMARY.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-05-PLAN.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-05-SUMMARY.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-06-PLAN.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-06-SUMMARY.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-07-PLAN.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-07-SUMMARY.md"
  - "app/pages/auth.py"
  - "app/pages/htmx.py"
  - "app/static/css/app.css"
  - "app/templates/auth/forgot_password.html"
  - "app/templates/auth/forgot_password_reset.html"
  - "app/templates/auth/forgot_password_verify.html"
  - "app/templates/auth/includes/forgot_password_reset_step.html"
  - "app/templates/auth/includes/forgot_password_step.html"
  - "app/templates/auth/includes/forgot_password_verify_step.html"
  - "app/templates/auth/includes/login_step.html"
  - "app/templates/auth/includes/register_complete_step.html"
  - "app/templates/auth/includes/register_step.html"
  - "app/templates/auth/includes/register_verify_step.html"
  - "app/templates/auth/includes/step_response.html"
  - "app/templates/auth/login.html"
  - "app/templates/auth/register.html"
  - "app/templates/auth/register_complete.html"
  - "app/templates/auth/register_verify.html"
  - "app/templates/auth_base.html"
  - "app/templates/base.html"
  - "tests/test_pages/test_auth_transport.py"
  - "tests/test_pages/test_blocked_user.py"
  - "tests/test_pages/test_htmx_gates.py"
  - "tests/test_pages/test_htmx_post_pairs.py"
  - "tests/test_pages/test_htmx_response_layer.py"
  - "tests/test_pages/test_hx_location_destinations.py"
  - "tests/test_pages/test_impersonation.py"
  - "tests/test_pages/test_notices_channel.py"
  - "tests/test_pages/test_password_reset.py"
  - "tests/test_pages/test_registration.py"
  - "tests/test_templates/test_htmx_markup_gates.py"
covered_digest: "v1:sha256:7ba78b7ee26ef21e5cb55790cb64216b0a6261e72643112df4352c329c051fec"
behavior_unverified: 0
backstop_abstentions: 1
overrides_applied: 0
decision_coverage:
  honored: 15
  total: 15
  not_honored: []
deferred:
  - truth: "23 `must_haves.prohibitions` across plans 14-01…14-07 stand at `status: flagged-unverified`, `verification: none` — no machine enforcement reads them"
    addressed_in: "Phase 15"
    evidence: "Phase 15 success criterion 6: «Запреты планов ПЕРЕПИСАНЫ ОДНИМ ПРИБОРОМ, и по каждому принято решение… Критерий закрыт, когда (а) в дереве есть ОДИН исполняемый прибор переписи… и (б) по каждому запрету его перечня стои́т ЛИБО предъявленное машинное принуждение, ЛИБО явное человеческое разрешение»"
  - truth: "Cross-origin (`is_same_origin`) guard absent on nine of ten auth POST handlers — CR-01"
    addressed_in: "Owner-recorded deferral, 14-CONTEXT.md §Deferred Ideas (not a numbered later phase)"
    evidence: "14-CONTEXT.md §Deferred Ideas: «Проверка источника запроса на формах входа и регистрации. Сегодня у девяти форм `is_same_origin` нет, защита — только `SameSite=Lax`. Подделка входа… — отдельная работа по безопасности, не транспорт.» Also named out-of-boundary at 14-CONTEXT.md:32."
escalations:
  - id: CR-02 / WR-07
    question: "Does the password-reset token replay belong in Phase 14's verdict or in a named follow-up?"
    verifier_recommendation: "Follow-up, with a named obligation recorded now — see §Escalation below."
    decision_owner: chubav
    status: awaiting_human_decision
flagged_prohibitions: 23 # all `verification: none` / `status: flagged-unverified`; never counted green — deferred to Phase 15 SC6
human_verification:
  - test: "Полный вход в браузере: открыть `/login`, ввести неверный пароль, затем верный"
    expected: "Неверный пароль перерисовывает карточку БЕЗ перезагрузки, email остаётся в поле, заголовок вкладки — «Вход — Broadcaster»; верный пароль уводит в кабинет ПОЛНОЙ загрузкой, cookie `access_token` сменилась"
    why_human: "Рантайм подмены htmx, заголовок вкладки и смена cookie сервером не измеряются — суита не исполняет JS ни строчки (ROADMAP критерий 4, D-02)"
  - test: "Регистрация целиком с НАСТОЯЩИМ письмом: `/register` → код из реального ящика → имя и пароль → кабинет"
    expected: "Экран кода приезжает без перезагрузки, адресная строка остаётся `/register`, письмо с кодом доходит, неверный код оставляет набранное, завершение уводит в кабинет полной загрузкой"
    why_human: "Доставка настоящего письма (D-02: код из базы подставлять запрещено) и рантайм подмены"
  - test: "Восстановление пароля целиком: `/forgot-password` → код из письма → новый пароль → `/login` с плашкой → вход новым паролем"
    expected: "Плашка «Пароль успешно изменён. Войдите с новым паролем.» видна на `/login`, вход новым паролем проходит"
    why_human: "Доставка письма и визуальное подтверждение плашки области уведомления шелла"
  - test: "Возврат из-под чужой личности: «ВЕРНУТЬСЯ В АДМИНА» из полосы"
    expected: "Адресная строка `/admin`, заголовок вкладки — админки, полосы имперсонации нет, cookie без признака действующего лица"
    why_human: "Смена cookie личности и заголовок вкладки через границу шеллов в живом браузере (D-12)"
  - test: "Клавиатурный проход по экрану кода после 422: нажать Tab сразу после неверного кода"
    expected: "Наблюдаемо, куда попадает фокус после `hx-swap=\"innerHTML\"` в `#auth-step`"
    why_human: "В дереве шаблонов авторизации нет ни `autofocus`, ни `tabindex`, ни `aria-live` (машинно подтверждено); КУДА при этом попадает фокус и что слышит скринридер — наблюдение, не грепа (14-UI-REVIEW WARNING 2)"
  - test: "На экране кода нажать «Отправить код повторно», пока «Подтвердить» в полёте"
    expected: "Наблюдаемо, выглядит ли вторая кнопка живой при отброшенном `hx-sync` запросе"
    why_human: "`hx-disabled-elt=\"find button[type=submit]\"` гасит кнопку ТОЛЬКО своей формы; запрос отбрасывается `hx-sync` (доказано `test_both_code_forms_ride_the_anchor_and_drop_a_second_request`), но видимость этого — суждение глазами (14-UI-REVIEW WARNING 3)"
  - test: "Карточка авторизации на 375px и на десктопе, во всех семи экранах"
    expected: "Наблюдаемо, читаема ли иерархия карточки (все тексты тела 13px, заголовочного элемента нет ни на одном из семи экранов)"
    why_human: "Визуальное суждение; дев-сервер во время ревизии не отвечал, скриншотов нет (14-UI-REVIEW Pillars 2/4/5)"
---

# Phase 14: Авторизация на htmx — Verification Report

**Phase Goal:** неверный код или пароль перестаёт стирать заполненную форму — заявленный выигрыш вехи именно в ОШИБКЕ, а не в успехе
**Verified:** 2026-09-23T08:15:00Z
**Status:** human_needed
**Re-verification:** No — initial verification (no prior `14-VERIFICATION.md` existed on disk; confirmed before writing)

**Method.** Goal-backward. The must-haves below are the four ROADMAP Success Criteria (the contract, non-negotiable) merged with the plan-frontmatter truths of 14-01…14-07 that add detail the criteria do not carry. Nothing here is taken from a SUMMARY.md claim: every VERIFIED row is backed either by lines I read in the source tree at HEAD `63f744be`, or by a **named** test I ran myself in this pass (21 rules, three invocations — never the suite). The orchestrator's full-suite measurement (3605 passed at `e9f31fd0`) is treated as an input, not as proof of any criterion: a green suite proves what the suite asserts, and the column «proved by» below names which rule proves what.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | **SC1 / SIGN-02.** Неверный код или пароль перерисовывает форму С СОХРАНЕНИЕМ введённого: 422 + эхо в `value=`; свойство создаёт СЕРВЕР | ✓ VERIFIED | Сервер: `login_submit` (`app/pages/auth.py:269-271`) на ошибке зовёт `respond_field_error`, тот — `_respond_by_transport(..., status_code=422)` (`app/pages/htmx.py:903-957, 996-1021`); эхо приходит параметром в шаблон (`login_step.html:39` — `value=email or ''`, `register_verify_step.html:54` — `value=code or ''`, `register_complete_step.html:38` — `value=name or ''`). Проверено ПРОГОНОМ четырёх именованных правил (см. §Behavioural Spot-Checks 1-4); утверждения значимого уровня — `assert f'value="{email}"' in …` на ОБОИХ транспортах, `test_auth_transport.py:185,203` |
| 2 | **SC2 / SIGN-01.** Все 9 форм авторизации идут через `hx-post` и остаются рабочими без JS | ✓ VERIFIED | `grep -rn 'form_wrapper(' app/templates/auth/` → РОВНО 9 вызовов (login 1, register 1, register_verify 2, register_complete 1, forgot_password 1, forgot_password_verify 2, forgot_password_reset 1); десятая — `base.html:89` (возврат, основной шелл, вне девятки — летопись критерия 2). Без JS держится ПОСТРОЕНИЕМ: макрос печатает `method="post" action="{{ action }}" hx-post="{{ action }}"` одной строкой (`components/form_wrapper.html:188`), разойтись им негде. Прогон: правила 5-7 и 10 §Spot-Checks |
| 3 | **SC3 / SIGN-03.** Успех авторизации уходит `HX-Redirect` через границу шеллов; `HX-Location` — по летописи | ✓ VERIFIED | Читано ПО ЛЕТОПИСИ (ROADMAP + REQUIREMENTS SIGN-03), а не буквально — см. §Criterion 3 ниже. Источник подтверждает летопись построчно: `redirect_internal` у `:273` (вход), `:617` (завершение регистрации), `:1115` (новый пароль); три ветки возврата — `:716` `HX-Location /dashboard`, `:744` `HX-Redirect /login` + `clear_session_cookie`, `:748` `HX-Location /admin` + `set_session_cookie` на ВОЗВРАЩЁННОМ объекте; второй отправитель `HX-Location` — `forbid_when_impersonating` на `:790, :886, :966, :1058` через `location_response` в `app/main.py:231`. Прогон: правила 8-9 §Spot-Checks |
| 4 | **SC4.** Вход, регистрация, подтверждение почты и восстановление пароля проходят в браузере целиком | ⚠️ `insufficient_spec` (backstop abstention) | **НЕ проверяется кодом и здесь НЕ проверено.** Все семь планов пометили соответствующую истину `verification: backstop` — это и есть тег воздержания честного верификатора. Артефакт обхода `14-UAT.md` существует в размеченной форме (`checks_declared: 7`, семь `## Проверка N`, семь ПУСТЫХ `### Отметка`, `status: testing`, `result: [pending]`); заполнять его я не вправе — это было бы самозаверением. Маршрутизировано в §Human Verification |
| 5 | Враждебный ввод возвращается в `value=` ТОЛЬКО экранированным, на обоих транспортах | ✓ VERIFIED | Экранирование — окружения шаблонов; ни `\|safe`, ни `Markup(` на пути эха нет. Правило утверждает ОБА направления: `assert HOSTILE not in response.text` И `assert f'value="{HOSTILE_ESCAPED}"' in response.text` (`test_auth_transport.py:229-234`) — «не пришло сырым» отдельно от «эхо вообще есть». Прогон: правило 2 |
| 6 | Пароль не возвращается НИКОГДА — ни в `value=`, ни в теле, ни в контексте шаблона | ✓ VERIFIED | Отказ стоит у ЕДИНСТВЕННОГО входа в экран: `_screen_builders` поднимает `ValueError`, если в контексте есть ключ `password` (`app/pages/auth.py:211-215`), и текст отказа значения не подставляет — пароль не уйдёт даже трассировкой. Пары на транспортах утверждают `WRONG_PASSWORD not in …text` (`:186, :204`). Прогон: правила 1, 11 |
| 7 | Отказ 422 не несёт cookie сессии ни на одном транспорте; заблокированный с ВЕРНЫМ паролем получает 422 с `BLOCKED_LOGIN_ERROR` | ✓ VERIFIED | Порядок «пароль → блокировка → cookie» в источнике не тронут (`auth.py:260-271`); токен создаётся ПОСЛЕ ветки ошибки (`:272`). Прогон: правила 1, 12 (`test_a_blocked_user_is_refused_with_422_and_no_cookie_on_both_transports`) |
| 8 | Смена экрана — 200 на обоих транспортах; подписанный токен шага едет ТОЛЬКО скрытым полем, не адресом | ✓ VERIFIED | `respond_screen` → `_respond_by_transport(..., 200)` (`htmx.py:960-993`); токен — `<input type="hidden" name="token">` в `register_verify_step.html:53,64`, `forgot_password_verify_step.html:53,64`, `register_complete_step.html:37`, `forgot_password_reset_step.html:33`. В `redirect_internal`/`respond` токен не передаётся ни разу (все 33 вызова выходов слоя просмотрены). Деградация — страница прямо в ответ на POST, не редирект: `built = await (fragment if is_htmx(request) else page)()` (`htmx.py:1010`) |
| 9 | Возврат из-под чужой личности: три ветки, cookie перезаписана НА ЭТОМ ЖЕ ответе, следующий `GET /admin` отдаёт админку | ✓ VERIFIED (behaviour-dependent — доказано прогоном, не присутствием) | Истина о ПЕРЕХОДЕ СОСТОЯНИЯ: присутствия `set_session_cookie` рядом с заголовком мало — cookie на выброшенном объекте дала бы зелёный тест при молча несостоявшемся возврате. Правило написано ТРОЙНЫМ и утверждает последствие: 204 + `HX-Location: /admin`, `access_token` в `set-cookie` ЭТОГО ответа, признак действующего лица в токене отсутствует, следующий `GET /admin` → 200, полоса имперсонации исчезла (`test_impersonation.py:1710-1743`). Прогон: правила 13-15 |
| 10 | Восстановление пароля под чужой личностью остаётся запрещённым на ВСЕХ четырёх шагах, на обоих транспортах | ✓ VERIFIED (behaviour-dependent) | Истина об ОТСУТСТВИИ побочного действия: зависимость `forbid_when_impersonating` стоит на `:790, :886, :966, :1058` (все четыре шага), фаза её не трогала. Прогон: правила 16-17 — обе пары утверждают 204 + `HX-Location` на htmx-пути, 403 без него, и что состояние не изменилось |
| 11 | Счётчик отставания вехи — ИМЕНОВАННЫЙ НОЛЬ, доказанный НЕ ВАКУУМНЫМ | ✓ VERIFIED | `NOT_YET_CONVERTED_COUNT = 0` (`test_htmx_gates.py:847`), перечень объявлен пустым, а не удалён. Ноль, который мог бы означать сломанный разборщик, отделён отдельным правилом: ТЕМ ЖЕ прогоном обход находит непустую вселенную POST-обработчиков и находит отставание на синтетическом дереве. Прогон: правило 10 (`test_the_named_zero_of_the_backlog_is_not_a_broken_scanner`) |
| 12 | Реестр `AUTH_SCREENS` накрывает ВСЕ семь страниц второго шелла; заголовок фрагмента и заголовок страницы сличаются | ✓ VERIFIED | Семь записей в `AUTH_SCREENS` (`auth.py:139-179`) против семи файлов `app/templates/auth/*.html` — соответствие 1:1 по именам. `<title>` стоит ВЕРХНИМ узлом ответа-фрагмента (`step_response.html`), разметка экрана включается страницей и фрагментом ОДНИМ файлом. Прогон: правило 18 (`test_the_shell_leaves_the_subtitle_to_every_screen`) |
| 13 | Записи фазы приведены в объявленную форму: летописи критериев 2 и 3, строки Research, SIGN-03, рамки вехи; окно 63 переведено ЗАМЕРОМ; артефакт обхода размечен | ✓ VERIFIED | Летописи на месте: ROADMAP §Фаза 14 (критерии 2, 3, строка Research), `REQUIREMENTS.md:60` (SIGN-03), `PROJECT.md:80` и `:254`. Тексты критериев и требований НЕ ПЕРЕПИСАНЫ — летопись стои́т рядом (идиома D-30/D-32) — проверено чтением. Окно 63 `.planning/WINDOWS.md:80` — `waived` с причиной-летописью; его замер **перепроверен мною независимо**: мест голого `Response(status_code=403)` в `app/pages/` — 14 (пятнадцатое вхождение грепа — строка докстринга `htmx.py:9`), `OWN_RESPONSE_EXITS_DECLARED = 14` (`test_htmx_gates.py:5503`) — сходится. `14-UAT.md`: `checks_declared: 7`, семь `## Проверка`, семь `### Отметка`, `status: testing` |

**Score:** 12/13 truths verified (0 present-but-behaviour-unverified; 1 backstop abstention routed to human).

Две истины (9 и 10) зависят от ПОВЕДЕНИЯ — переход состояния и отсутствие побочного действия, — и присутствием символов они бы не закрывались. Обе закрыты прогоном именованных правил, а не грепом; ни одна строка счёта 12/13 не поставлена на присутствии.

### Criterion 3 — read against its chronicles, not literally

Критерий 3 буквально говорит «`HX-Location` остаётся ТОЛЬКО у `/impersonation/stop`, не пересекающего границу шеллов». Буквальное чтение дало бы ДВА расхождения. Оба названы летописью плана 14-07 ЗАРАНЕЕ и подтверждены мною в источнике:

| Буквальная посылка | Что в дереве | Где названо |
|---|---|---|
| «`/impersonation/stop` не пересекает границу шеллов» | Верно для ДВУХ веток из трёх. Третья — действующего лица нет в базе либо оно заблокировано — уходит `HX-Redirect` на `/login` (`auth.py:744`) со снятием cookie, то есть ЧЕРЕЗ границу | ROADMAP летопись критерия 3 (б); REQUIREMENTS SIGN-03; D-12 |
| «`HX-Location` — ТОЛЬКО у возврата» | Второй отправитель существует: отказ `forbid_when_impersonating` на четырёх шагах восстановления (`auth.py:790, :886, :966, :1058`) → `HtmxRefusal` → `location_response` (`app/main.py:224-231`). Живёт ВНЕ модуля авторизации | ROADMAP летопись критерия 3 (в); D-13 |

Машинное правило `test_hx_location_in_the_auth_module_belongs_to_the_return_only` утверждает равенство `{stop_impersonation}` внутри `app/pages/auth.py` и второго отправителя НЕ ВИДИТ ПО ПОСТРОЕНИЮ — вселенная правила есть модуль авторизации. Эта граница названа в шапке гейта, а не оставлена читателю. Правило и три его двухшаговых отрицательных контроля стоят в дереве (`test_htmx_gates.py:6312-6484`).

**Вывод:** расхождения нет. Критерий 3 засчитан по летописи, и этот абзац стои́т здесь ровно затем, чтобы следующий читатель не открыл ложный изъян.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `app/pages/htmx.py` | `redirect_internal`, `respond_screen`, `_respond_by_transport`, `respond_field_error` | ✓ VERIFIED | `:413`, `:960`, `:996`, `:903` — все четыре существенны (не заглушки), у каждой развёрнутый контракт и путь деградации; все вызываются из `auth.py` |
| `app/pages/auth.py` | 10 обработчиков на выходах слоя; `AuthScreen`, `AUTH_SCREENS`, `AUTH_STEP_RESPONSE_TEMPLATE`, `_screen_markup`, `_screen_builders` | ✓ VERIFIED | 33 вызова выходов слоя по 10 обработчикам; ни один обработчик не собирает собственный ответ помимо слоя, кроме именованного 403 (`:704`, изъятие D-01) |
| `app/templates/auth/includes/step_response.html` | `<title>` верхним узлом + включение экрана | ✓ VERIFIED | Ровно два узла: `<title>{{ screen_title }}</title>` и `{% include screen_template %}` |
| `app/templates/auth/includes/*_step.html` (7) | Единственные источники разметки экранов, эхо в `value=` | ✓ VERIFIED | Семь файлов, по одному на экран; все включаются И страницей, И `step_response.html` — второй копии разметки нет |
| `app/templates/auth_base.html` | Постоянный якорь `#auth-step` ПОСЛЕ областей уведомления, без переходного блока подзаголовка | ✓ VERIFIED | `:62` — `{% include "includes/notice_area.html" %}`, `:67` — `<div id="auth-step" class="auth-step">`. Порядок правильный, и он несущий: иначе исход смены пароля стирался бы первой же ошибкой формы |
| `app/templates/base.html` | Форма возврата через `form_wrapper` без цели | ✓ VERIFIED | `:89` — `form_wrapper(action='/impersonation/stop')` без `target` → макрос печатает `hx-swap="none"` |
| `tests/test_pages/test_auth_transport.py` | Сквозные пары на обоих транспортах | ✓ VERIFIED | 40 правил; утверждения значимого уровня (value-level), не existence-level |
| `tests/test_pages/test_htmx_gates.py` | Именованный ноль, гейт критерия 3, `OWN_RESPONSE_EXITS` | ✓ VERIFIED | `NOT_YET_CONVERTED_COUNT = 0` (`:847`), `OWN_RESPONSE_EXITS_DECLARED = 14` (`:5503`), гейт критерия 3 с тремя контролями (`:6312-6484`) |
| `.planning/ROADMAP.md`, `REQUIREMENTS.md`, `PROJECT.md`, `WINDOWS.md`, `14-UAT.md` | Летописи, окно 63, артефакт обхода | ✓ VERIFIED | См. истину 13 |

Ни одного MISSING, ни одного STUB, ни одного ORPHANED.

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Форма входа (`hx-target=#auth-step`, innerHTML) | `login_submit` | `respond_field_error` → экран входа с эхом внутри якоря | ✓ WIRED | Ломается — ошибка молча не перерисовывает форму либо стирает введённое. Замкнуто прогоном правила 1 |
| `login_submit` / `register_complete` | `redirect_internal` → `set_session_cookie` НА ВОЗВРАЩЁННОМ объекте | `location.href` | ✓ WIRED | `auth.py:273-274`, `:617-618` — cookie ставится на объект, полученный ИЗ выхода, а не на отдельно собранный. Это и есть Landmine фазы; замкнуто правилами 3 и 19 (`…leaves_by_a_full_load_with_the_cookie…`), которые утверждают cookie на ТОМ ЖЕ ответе и открывшийся кабинет |
| `stop_impersonation` | `respond(redirect="/admin")` → `set_session_cookie` | `HX-Location` → `GET /admin` | ✓ WIRED | `auth.py:748-750`; тройное правило (прогон 13) утверждает заголовок, cookie без признака действующего лица И фактически открывшуюся админку |
| Ветка закрытого действующего лица | `redirect_internal("/login")` → `clear_session_cookie` | `HX-Redirect` | ✓ WIRED | `auth.py:744-746`; прогон 15 |
| `forgot_password_reset` | `redirect_internal(..., notice=PASSWORD_RESET_DONE)` | область уведомления шелла ВНЕ якоря | ✓ WIRED | `auth.py:1115`; правило утверждает не только заголовок, но и что текст исхода стои́т ДО якоря (`index(RESET_DONE_TEXT) < index(STEP_ANCHOR)`, `test_auth_transport.py:1759`) — иначе исход стёрся бы первой ошибкой входа |
| `forbid_when_impersonating` | `HtmxRefusal` → `location_response` | `app/main.py:231` | ✓ WIRED | Четыре шага восстановления; прогоны 16-17 |
| Гейт критерия 3 (`_full_load_callers` / `_hx_location_emitters`) | `FULL_LOAD_HANDLERS` / `AUTH_HX_LOCATION_HANDLERS` | равенство, не включение | ✓ WIRED | Прогоны 8-9; у обоих правил есть проверка непустоты вселенной — на пустом замере они бы не позеленели |

### Data-Flow Trace (Level 4)

| Artifact | Data value | Source | Produces real data | Status |
|---|---|---|---|---|
| `login_step.html:39` | `value=email or ''` | `login_submit` → `_screen_builders(request, "login", error=…, email=email)` (`auth.py:270`) — присланная форма | Да | ✓ FLOWING |
| `register_verify_step.html:54` | `value=code or ''` | `register_verify` → `respond_field_error` с набранным кодом | Да | ✓ FLOWING |
| `forgot_password_verify_step.html:54` | `value=code or ''` | `forgot_password_verify` | Да | ✓ FLOWING |
| `register_complete_step.html:38` | `value=name or ''` | `register_complete` | Да | ✓ FLOWING |
| Скрытое поле `token` (4 экрана) | `value="{{ token }}"` | `create_verification_token(...)` — подписанный JWT, не литерал | Да | ✓ FLOWING |
| Поле пароля (2 экрана) | значения нет | — | **Намеренно пусто (D-04)** | ✓ FLOWING (по решению) — не заглушка: `_screen_builders` ФИЗИЧЕСКИ отказывает передать `password` в контекст |

Ни одного значения, чья цепочка кончается статическим возвратом, литералом или моком.

### Behavioural Spot-Checks

21 именованных правила, три вызова `pytest`. Суита целиком НЕ перезапускалась — её зелёный прогон (3605 passed, `e9f31fd0`) взят входом от оркестратора. Ниже — то, чего тот прогон не адресует поимённо: какое правило доказывает какой критерий.

| # | Proves | Named rule | Result |
|---|---|---|---|
| 1 | SC1 — эхо и 422 на входе | `test_auth_transport.py::test_a_wrong_password_redraws_the_login_screen_on_both_transports` | ✓ PASS |
| 2 | SC1 — экранирование | `::test_a_hostile_email_comes_back_escaped_on_both_transports` | ✓ PASS |
| 3 | SC1 — эхо кода регистрации | `::test_a_wrong_code_keeps_the_typed_code_and_answers_422_on_both_transports` | ✓ PASS |
| 4 | SC1 — эхо кода восстановления | `::test_a_wrong_recovery_code_keeps_the_typed_code_and_answers_422` | ✓ PASS |
| 5 | SC2 — деградация без JS | `test_htmx_markup_gates.py::test_every_such_form_keeps_its_method_and_action` | ✓ PASS |
| 6 | SC2 — все `hx-post` рождены макросом | `::test_every_htmx_post_is_born_of_a_component_macro` | ✓ PASS |
| 7 | SC2 — у каждого переведённого обработчика пара на обоих транспортах | `test_htmx_post_pairs.py::test_every_converted_handler_has_a_pair` | ✓ PASS |
| 8 | SC3 — ровно четыре вызывающих полной перезагрузки | `test_htmx_gates.py::test_only_the_named_auth_handlers_leave_by_a_full_load` | ✓ PASS |
| 9 | SC3 — `HX-Location` в модуле авторизации только у возврата | `::test_hx_location_in_the_auth_module_belongs_to_the_return_only` | ✓ PASS |
| 10 | Именованный ноль НЕ вакуумен | `::test_the_named_zero_of_the_backlog_is_not_a_broken_scanner` | ✓ PASS |
| 11 | Пароль не доезжает до контекста экрана | `test_auth_transport.py::test_the_screen_builders_refuse_a_password_in_the_context` | ✓ PASS |
| 12 | Заблокированный — 422 без cookie | `::test_a_blocked_user_is_refused_with_422_and_no_cookie_on_both_transports` | ✓ PASS |
| 13 | Возврат: заголовок + cookie + фактическая админка | `test_impersonation.py::test_the_return_over_htmx_keeps_both_the_location_and_the_admin_cookie` | ✓ PASS |
| 14 | Возврат без действующего лица — `/dashboard`, ни одного токена | `::test_the_return_without_an_actor_goes_to_the_dashboard_on_both_transports` | ✓ PASS |
| 15 | Закрытое действующее лицо — `HX-Redirect /login` со снятием cookie | `::test_a_closed_actor_is_logged_out_by_the_return_on_both_transports` | ✓ PASS |
| 16 | Отказ под чужой личностью на первых шагах восстановления | `test_auth_transport.py::test_the_first_recovery_steps_are_refused_under_another_identity_on_both_transports` | ✓ PASS |
| 17 | То же на последних шагах | `::test_the_last_recovery_steps_are_refused_under_another_identity_on_both_transports` | ✓ PASS |
| 18 | Шелл окончателен, подзаголовок печатает каждый экран | `::test_the_shell_leaves_the_subtitle_to_every_screen` | ✓ PASS |
| 19 | Завершение регистрации: cookie + пробный срок + кабинет | `::test_completing_registration_leaves_by_a_full_load_with_the_cookie_and_the_trial` | ✓ PASS |
| 20 | Вход: cookie на ответе 204 и открывшийся кабинет | `::test_a_right_password_leaves_by_a_full_load_with_the_cookie` | ✓ PASS |
| 21 | Новый пароль → `/login` с плашкой → вход новым паролем | `::test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice` | ✓ PASS |

**21/21 PASS.**

Независимые замеры (без pytest), выполненные мною в этом проходе:

| Measurement | Command | Result |
|---|---|---|
| Число форм авторизации | `grep -rn 'form_wrapper(' app/templates/auth/` | 9 — сходится с летописью критерия 2 |
| Десятая форма | `grep -n 'form_wrapper(' app/templates/base.html` | 1 (`:89`) — сходится |
| Мест голого 403 в страничном слое | `grep -rn 'Response(status_code=403)' app/pages/` | 15 вхождений, из них одно — строка докстринга (`htmx.py:9`) ⇒ **14 реальных**, сходится с замером окна 63 и с `OWN_RESPONSE_EXITS_DECLARED = 14` |
| `error=` передан макросу поля на экранах авторизации | `grep -rn 'field(' app/templates/auth/ \| grep -c 'error='` | **0** — подтверждает WARNING 1 ревизии интерфейса (см. ниже) |
| Покрытие решений CONTEXT | `gsd-tools query check.decision-coverage-verify` | **15/15 honored**, `not_honored: []` |

### Probe Execution

Проб в дереве нет и фазой не объявлено (`find scripts -path '*/tests/probe-*.sh'` → 0; упоминаний `probe-` в планах 14-01…14-07 → 0). Шаг пропущен по отсутствию предмета, а не по невыполнению.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| **SIGN-01** | 14-01, 14-02, 14-03, 14-04, 14-05, 14-06, 14-07 | 9 форм авторизации идут через htmx | ✓ SATISFIED (машинно); рантайм подмены — за человеком | Истина 2; замер 9 форм; правила 5-7. Остаток — наблюдение свопа в браузере (§Human Verification 1-4) |
| **SIGN-02** | 14-01, 14-02, 14-03, 14-04, 14-05, 14-07 | Неверный код или пароль перерисовывает форму с сохранением введённого | ✓ SATISFIED | Истины 1, 5, 6, 7; правила 1-4, 11-12. **Это и есть цель фазы, и она достигнута сервером** |
| **SIGN-03** | 14-01, 14-03, 14-05, 14-06, 14-07 | Успех — `HX-Redirect` через границу шеллов; `HX-Location` — у возврата | ✓ SATISFIED (по летописи, см. §Criterion 3) | Истина 3; правила 8-9, 13-15, 19-21 |

**Отметки НЕ ставлю.** В `.planning/REQUIREMENTS.md` SIGN-01…03 стоят `[ ]` / `Pending` — и остаются: отметку ставит закрытие фазы (`phase.complete`) ПОСЛЕ верификации, а верификация ещё не завершена — критерий 4 у человека. `requirements.ready-ids`, сообщающий их готовыми, авторитетом на отметку не является.

Сирот нет: `.planning/REQUIREMENTS.md:499` отображает на Фазу 14 ровно SIGN-01, SIGN-02, SIGN-03 — и все три заявлены планами.

### Decision Coverage

15 из 15 отслеживаемых решений `14-CONTEXT.md` (D-01…D-15) опознаны в поставленных артефактах; `not_honored` пуст. Гейт незапирающий; записано для истории дрейфа.

Отдельно перепроверено чтением, что D-15 («фаза меняет транспорт, а не решения») исполнен буквально: набор проверок `purpose`/`verified` в `app/pages/auth.py` ДО фазы (`git show fd69a26a`) и после — **один и тот же**, четыре места в обоих деревьях. Это важно не само по себе: именно оно превращает CR-01, CR-02 и WR-01 ревизии кода из «дефектов фазы» в «дефекты, которые фаза обязана была не трогать».

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` в файлах фазы | — | **Ноль совпадений.** Гейт долговых меток зелёный |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` | ℹ️ Info | Единственные совпадения — `_PLACEHOLDER = "{}"` в `test_htmx_post_pairs.py:2683` и три его употребления: это сентинел разборщика форматных строк гейта, не заглушка |
| — | — | Отключённые тесты (`skip` / `xfail`) в правилах фазы | — | **Ноль.** Ни одно требование не держится на отключённом правиле |
| — | — | Пустые реализации, статические возвраты, пустые обработчики | — | Ноль. 33 вызова выходов слоя — все с настоящим контекстом; ни одного `return None` / `return []` на пути ответа |

Аудит качества тестов: круговых тестов нет (правила сличают ответ приложения с ЛИТЕРАЛАМИ, выписанными в самом правиле, а не со значениями, порождёнными системой); уровень утверждений — значимый (value-level) и поведенческий, не existence-level; у инвентарных правил есть проверки непустоты вселенной и двухшаговые отрицательные контроли на синтетике.

### Findings Handed Over By Hand (code review and UI review)

Машинерия `--gaps` эти файлы не читает; они разобраны здесь поимённо, а не опущены.

| ID | Severity in review | Мой независимый вердикт | Классификация здесь |
|---|---|---|---|
| **CR-01** — девять из десяти POST-обработчиков авторизации без `is_same_origin` | Critical, pre-existing | **Подтверждено замером:** `app/pages/auth.py` — 10 `@router.post`, `is_same_origin` вызывается ОДИН раз (`:691`, возврат). Девять прочих страничных модулей применяют гард к своим изменяющим обработчикам. Суита это не видит: гард пропускает запрос без заголовков ПО ПОСТРОЕНИЮ, а тест-клиент их не шлёт | **НЕ изъян Фазы 14.** Записано ВЛАДЕЛЬЦЕМ в границе фазы ДО планирования: `14-CONTEXT.md:32` («защита входа от подделки запроса… см. Deferred») и §Deferred Ideas дословно («у девяти форм `is_same_origin` нет, защита — только `SameSite=Lax`… отдельная работа по безопасности, не транспорт»). Перевод экспозицию не изменил: формы и до фазы были POST-формами с теми же адресами. → `deferred` |
| **CR-02** — подтверждённый токен восстановления воспроизводим и самообновляем | Critical, pre-existing | **Подтверждено чтением и прогоном.** `forgot_password_reset` (`auth.py:1076-1115`) проверяет подпись, `verified` и `purpose`, но `code_record.verified_at` НЕ читает и НЕ гасит — `verified_at` читается/ставится только в двух обработчиках подтверждения (`:408, :443, :916, :950`). Токен — JWT на 30 минут (`auth_service.py:143-150`), состояния за ним нет. Ветка короткого пароля чеканит СВЕЖИЙ подтверждённый токен на каждом отказе (`:1097`) ⇒ держатель продлевает возможность неограниченно. Замер до/после фазы: набор проверок идентичен (`git show fd69a26a`) ⇒ предшествует фазе | **Предшествует фазе — НО см. §Escalation.** Правка здесь нарушила бы D-15 (фаза меняет транспорт, а не решения обработчика) |
| **WR-07 / CR-02 (следствие)** — новое правило фазы утверждает воспроизведение как правильное | Warning | **Подтверждено прогоном.** `test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice` (`test_auth_transport.py:1706-1770`) чеканит ОДИН токен на `:1717` и подаёт его ОБОИМ запросам (`:1721` и `:1736`), утверждая успех обоих (302, затем 204). Правило зелено — прогон 21. Предмет правила — паритет транспортов, но ПОБОЧНО оно закрепляет воспроизведение | **Это факт Фазы 14**, а не предшествующий: правило написано здесь. → §Escalation |
| **WR-01** — `register_verify` и `register_resend_code` не проверяют `purpose` | Warning | **Подтверждено и датировано:** четыре места проверки `purpose` до фазы (`fd69a26a:386, :636, :702, :781`) и четыре после (`:573, :901, :982, :1076`) — те же самые. Регистрационные шаги не проверяли и не проверяют | Предшествует фазе; D-15 запрещал трогать. Передаю дальше как известный остаток |
| **WR-02** — пути страницы и фрагмента не делят контекст шаблона | Warning | **Подтверждено чтением:** `_page()` идёт через `templates.TemplateResponse` (получает `request` и процессоры контекста), `_fragment()` — через `templates.env.get_template(...).render(...)` БЕЗ `request` (`auth.py:218-224`). РАЗМЕТКА при этом одна (тот же включаемый файл) — истина D-06 «разойтись негде» верна на уровне разметки и неполна на уровне контекста. Наблюдаемого расхождения сегодня нет: все семь экранов дают пару на обоих транспортах (прогон 7) | ⚠️ Латентный риск, не изъян: шаблон, который однажды позовёт `url_for`, сломается ТОЛЬКО на фрагменте. Стоит записи, не отката |
| **WR-03…WR-06, IN-01…IN-03** | Warning / Info | Не перепроверял построчно; ни один не касается истины фазы, и ни один не помечен ревизией как блокирующий | Передаю как есть |
| **UI WARNING 1** — 422 не помечает поле | Warning (UI 16/24, блокеров нет) | **Подтверждено замером:** макрос `field` умеет `error=` и печатает `aria-invalid="true"` (`components/field.html:21,37,53`), а экранов авторизации, передающих `error=`, — **ноль**. Ошибка рисуется только плашкой карточки | ⚠️ Warning. Критерий 1 требует СОХРАНЕНИЯ ВВЕДЁННОГО — и оно есть; пометки поля критерий не требует. Слабая половина выигрыша, не невыполненный критерий |
| **UI WARNING 2** — ни фокуса, ни живой области после свопа | Warning | **Подтверждено:** в дереве `app/templates/auth/` и `auth_base.html` нет ни `autofocus`, ни `tabindex`, ни `aria-live`. Что механизма НЕТ — решено кодом; КУДА попадает фокус — наблюдение | ⚠️ Warning + пункт человеку (§Human Verification 5) |
| **UI WARNING 3** — на экранах кода вторая кнопка остаётся живой | Warning | **Подтверждено:** `disabled_elt='find button[type=submit]'` (`form_wrapper.html:187`) ограничен своей формой. Но запрос НЕ уходит: обе формы несут `hx-sync="closest #auth-step:drop"` — доказано правилом `test_both_code_forms_ride_the_anchor_and_drop_a_second_request` | ⚠️ Warning, смягчённый: потери действия нет, есть невидимость отброса. Пункт человеку (§Human Verification 6) |

**Ни одна из этих находок не опровергает истину фазы, не ломает ключевую связь и не оставляет артефакт заглушкой.** Поэтому ни одна не поднята до 🛑 Blocker — и это сказано здесь прямо, вместе с основанием, а не умолчанием.

### Escalation — решение владельца, которое я не вправе принять за него

**Предмет.** CR-02 (воспроизведение подтверждённого токена восстановления) предшествует Фазе 14 и её решением D-15 был выведен из правки. Но правило `test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice`, написанное ПЛАНОМ 14-05, теперь **утверждает это воспроизведение зелёным**. Это уже факт Фазы 14: будущая правка, которая начнёт гасить `verified_at`, ПОКРАСНИТ правило этой фазы, и следующий исполнитель встретит красное правило без объяснения, почему оно вообще так написано.

**Вопрос владельцу:** отнести CR-02 к вердикту Фазы 14 (то есть открыть gap и править здесь) или к отдельной последующей работе?

**Моя рекомендация — ОТДЕЛЬНАЯ ПОСЛЕДУЮЩАЯ РАБОТА, с записанной сейчас обязанностью.** Основания, а не удобство:

1. Правка требует изменить РЕШЕНИЕ обработчика (гасить `verified_at`, перестать чеканить свежий токен на отказе) — ровно то, что D-15 этой фазы запретил дословно. Фаза, нарушившая собственное запертое решение в последнем шаге, обесценила бы и остальные четырнадцать.
2. Дефект предшествует фазе: замер `git show fd69a26a` показывает тот же набор проверок. Отнести его к вердикту Фазы 14 значило бы объявить изъяном фазы то, что она обязана была не трогать.
3. Цена отсрочки названа и ограничена: токен живёт 30 минут, и для злоупотребления нужен уже утёкший подтверждённый токен.

**Что должно быть записано ВМЕСТЕ с отсрочкой** (иначе отсрочка — умолчание, а не решение): у правила `test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice` должна встать летопись, называющая прямо, что повторное использование ОДНОГО токена в этом правиле есть свойство СЕГОДНЯШНЕГО обработчика, а не утверждаемое требование, и что правку CR-02 полагается сопроводить разведением двух токенов в этом правиле. Летопись — это одна правка в комментарии, и она не меняет ни одного утверждения.

**Того же решения ждёт CR-01** — хотя он уже отсрочен владельцем в `14-CONTEXT.md` §Deferred Ideas, и потому отсрочка у него не молчаливая.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|---|---|---|
| 1 | 23 запрета планов 14-01…14-07 стоят `flagged-unverified` / `verification: none` — машинного принуждения не имеет ни один | Phase 15 | Критерий 6 Фазы 15 дословно: «Запреты планов ПЕРЕПИСАНЫ ОДНИМ ПРИБОРОМ, и по каждому принято решение… (а) в дереве есть ОДИН исполняемый прибор переписи, чьё число воспроизводимо, и (б) по каждому запрету стои́т ЛИБО предъявленное машинное принуждение, ЛИБО явное человеческое разрешение» |
| 2 | CR-01 — гард источника запроса на девяти формах авторизации | Owner-recorded deferral (`14-CONTEXT.md` §Deferred Ideas), адресат-фаза не назначен | «Проверка источника запроса на формах входа и регистрации… отдельная работа по безопасности, не транспорт» |
| 3 | `hx-push-url` на формах авторизации | Phase 15 | D-08 этой фазы + критерий 3 Фазы 15 |

**Отсрочки статус не меняют.** Запреты я НЕ засчитываю зелёными: они помечены (`flagged_prohibitions: 23`) и остаются видимыми до Фазы 15. Ни один не поглощён молча вердиктом `passed` — вердикт и не `passed`.

### Human Verification Required

Семь пунктов. Первые четыре — критерий 4 ROADMAP, ручной ПО ПРОЕКТУ (настоящее письмо, браузер, смена cookie, заголовок вкладки); последние три — то, что ревизия интерфейса прямо оставила глазам.

Артефакт обхода `14-UAT.md` УЖЕ существует в размеченной форме и **остаётся как есть**: `status: testing`, семь пустых таблиц отметок, `result: [pending]`. Я не заполнил ни одной отметки и не тронул ни одного `result` — заполнить их значило бы самозаверение, а не приёмку (D-02; правило `tests/test_planning/test_the_walkthrough_cannot_self_certify.py`). Пункты ниже — маршрутизация к тому файлу, а не второй его экземпляр.

#### 1. Полный вход в браузере

**Test:** Открыть `/login`, ввести неверный пароль, затем верный.
**Expected:** Неверный пароль перерисовывает карточку БЕЗ перезагрузки страницы, введённый email остаётся в поле, заголовок вкладки — «Вход — Broadcaster». Верный пароль уводит в кабинет ПОЛНОЙ загрузкой, cookie `access_token` сменилась.
**Why human:** Рантайм подмены htmx, заголовок вкладки и смена cookie сервером не измеряются — суита не исполняет JS ни строчки.

#### 2. Регистрация целиком с настоящим письмом

**Test:** `/register` → адрес → код из РЕАЛЬНОГО ящика → имя и пароль → кабинет.
**Expected:** Экран кода приезжает без перезагрузки, адресная строка остаётся `/register`, письмо доходит, неверный код оставляет набранное, завершение уводит в кабинет полной загрузкой.
**Why human:** Доставка настоящего письма (D-02 запрещает подставлять код из базы) и рантайм подмены.

#### 3. Восстановление пароля целиком

**Test:** `/forgot-password` → код из письма → новый пароль → `/login` → вход новым паролем.
**Expected:** Плашка «Пароль успешно изменён. Войдите с новым паролем.» видна на `/login`, вход новым паролем проходит.
**Why human:** Доставка письма и визуальное подтверждение плашки шелла.

#### 4. Возврат из-под чужой личности

**Test:** Под чужой личностью нажать «ВЕРНУТЬСЯ В АДМИНА».
**Expected:** Адресная строка `/admin`, заголовок вкладки — админки, полосы имперсонации нет, cookie без признака действующего лица.
**Why human:** Смена cookie личности и заголовок вкладки через границу шеллов в живом браузере (D-12).

#### 5. Фокус и объявление после свопа

**Test:** На экране кода ввести неверный код, затем нажать Tab.
**Expected:** Наблюдаемо, куда попадает фокус и объявляет ли скринридер смену экрана.
**Why human:** Что механизма НЕТ — установлено кодом (ни `autofocus`, ни `tabindex`, ни `aria-live` во всём дереве авторизации). КУДА при этом попадает фокус — только наблюдение.

#### 6. Вторая кнопка на экранах кода

**Test:** Нажать «Отправить код повторно», пока «Подтвердить» в полёте.
**Expected:** Наблюдаемо, выглядит ли вторая кнопка живой при отброшенном запросе.
**Why human:** Отброс доказан правилом; ВИДИМОСТЬ отброса — суждение глазами.

#### 7. Карточка на 375px и на десктопе

**Test:** Пройти все семь экранов на узком и широком экране.
**Expected:** Наблюдаемо, читаема ли иерархия карточки.
**Why human:** Визуальное суждение; дев-сервер во время ревизии интерфейса не отвечал, скриншотов нет.

### Gaps Summary

**Изъянов, блокирующих достижение цели, не найдено.**

Цель фазы — «неверный код или пароль перестаёт стирать заполненную форму, и выигрыш именно в ОШИБКЕ» — **истинна в дереве, и истинной её делает СЕРВЕР**, а не разметка: код отказа 422 стои́т литералом в `respond_field_error`, эхо едет параметром в шаблон через автоэкранирующее окружение, а путь без JavaScript получает ту же страницу прямо в ответ на POST. Это подтверждено не присутствием символов, а прогоном именованных правил со значимыми утверждениями (`value="…"` в теле, пароль в теле отсутствует, cookie отсутствует) на ОБОИХ транспортах.

Что осталось и почему это не изъяны:

- **Критерий 4 у человека** — так задумано (D-02: настоящее письмо, настоящий браузер). Артефакт обхода готов и не тронут мною.
- **Три предупреждения ревизии интерфейса** касаются СИЛЫ выигрыша (поле не помечено красным, фокус никуда не ведётся, отброшенный клик невидим), а не его наличия. Введённое возвращается на всех семи экранах — это и есть критерий.
- **Две критические находки ревизии кода предшествуют фазе**, и обе перепроверены мною независимо в источнике и в дереве ДО фазы. CR-01 отсрочен владельцем письменно ещё до планирования. CR-02 — вынесен в §Escalation вместе с моей рекомендацией и с тем, что должно быть записано вместе с отсрочкой; молча он не опущен.
- **23 запрета планов без машинного принуждения** отсрочены критерием 6 Фазы 15 — адресатом названным и записанным, а не подразумеваемым.

Отметки SIGN-01…03 остаются `Pending`: их ставит закрытие фазы после того, как человек закроет обход.

---

_Verified: 2026-09-23T08:15:00Z_
_Verifier: Claude (gsd-verifier)_
