---
phase: 14-avtorizatsiya-na-htmx
verified: 2026-10-07T12:31:06Z
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
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-SECURITY.md"
  - ".planning/phases/14-avtorizatsiya-na-htmx/14-UAT.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml"
  - "app/main.py"
  - "app/pages/auth.py"
  - "app/pages/htmx.py"
  - "app/services/auth_service.py"
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
  - "app/templates/components/field.html"
  - "app/templates/components/form_wrapper.html"
  - "app/templates/includes/htmx_error_banner.html"
  - "app/templates/includes/notice_area.html"
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
covered_digest: "v3:sha256:617245a760d52dcb8a469e52e4dfd94ab805b2e1369c6d7503538eb74b3d466f"

# Отпечаток КРУГА 2 (2026-10-07) посчитан штатным вербом gsd-core 1.16
# `verification.fingerprint` и скопирован из его вывода дословно. Ни один путь не потерян:
# передано 41, верб добавил 14 PLAN/SUMMARY фазы, итого 55; сверено поимённо скриптом в
# scratchpad. Список шире списка круга 1 (46): добавлены файлы, на которые этот круг ОПИРАЕТ
# вердикт, — `app/main.py`, `app/services/auth_service.py`, `components/field.html`,
# `components/form_wrapper.html`, `includes/htmx_error_banner.html`, `includes/notice_area.html`,
# `14-UAT.md` (заполнение отметок обязано сделать вердикт устаревшим), `14-SECURITY.md`
# (ответ на эскалацию) и реестр запретов Фазы 15 (состояние отсрочки 1). Прежнее значение
# `v1:sha256:740a47e9…` ошибкой не было — устарело по правкам Фазы 15 (см. `re_verification`).
#
# --- Летописи круга 1 — перенесены ДОСЛОВНО, записи своего дня ---
#
# Отпечаток ПЕРЕСЧИТАН 2026-09-23 ВТОРОЙ РАЗ — после закрытия фазы обходом
# (`/gsd-verify-work 14`, 9/9, находок 0). Прежнее значение (…4ddf5b09…) ошибкой не
# было: из 46 покрытых файлов изменился РОВНО один, `.planning/REQUIREMENTS.md`, и
# правка в нём чисто учётная — `phase.complete` перевёл SIGN-01, SIGN-02 и SIGN-03 из
# `[ ]` в `[x]` и из `Pending` в `Complete` в таблице прослеживаемости (6 строк,
# `git diff .planning/REQUIREMENTS.md`). Пересчёт ДОКАЗАН воспроизведением: на старом
# содержимом того же файла `computeCoveredDigest` по полному списку из 46 путей даёт
# ровно …4ddf5b09…, после восстановления нового содержимого sha256 файла совпала
# побайтово. Считано ТОЙ ЖЕ функцией, какой проверяющий меряет устаревание, и по
# ПОЛНОМУ списку — верб `verification.fingerprint` молча теряет первый путь.
# Граница поступка: тронут ТОЛЬКО отпечаток. `score`, `verified` и `covered_files`
# не тронуты; `status` переведён в `passed` отдельным поступком канонизации —
# верификация ждала ровно ручного обхода, и обход закрыт человеком 9 из 9.
#
# Отпечаток ПЕРЕСЧИТАН 2026-09-23 после `/gsd-secure-phase 14`. Прежнее значение
# (…7ba78b7e…) ошибкой не было — оно устарело: из 46 покрытых файлов изменился РОВНО
# один, `tests/test_pages/test_auth_transport.py`, и в нём — только докстрока правила
# `test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice` (летопись
# CR-02 по решению владельца; строк кода вне докстроки изменено 0, доказано
# `git diff 65b313bc..HEAD`). Граница поступка: пересчитан ТОЛЬКО отпечаток той же
# функцией `computeCoveredDigest`, какой считает проверяющий устаревание; `status`,
# `score`, `verified` и `covered_files` не тронуты — вердикт остаётся `human_needed`
# и ждёт ручного обхода. Пересчёт есть арифметика над разрешённой правкой, а не
# новое суждение верификатора.
#
# --- Летопись круга 2 к первой летописи выше ---
# Её посылка «обход закрыт человеком 9 из 9» ОТОЗВАНА владельцем `chubav` 2026-09-23
# (исполнено планом 15-06, коммит f2361428 от 2026-09-24): шапка `14-UAT.md` —
# `status: human_needed`, девять таблиц «Отметка о закрытии» пусты, абзац отзыва
# дословно: «Обход Фазы 14 глазами НЕ ПРОВОДИЛСЯ». Поэтому `status: passed` круга 1
# этим кругом НЕ унаследован; вердикт выведен заново из улик дерева 2026-10-07.

behavior_unverified: 0
backstop_abstentions: 1  # SC4 — ⚠️ insufficient_spec; круг 1 → круг 2: открыто (обход не проводился)
overrides_applied: 0
decision_coverage:  # перемерено 2026-10-07 `check.decision-coverage-verify` — тот же итог, что в круге 1
  honored: 15
  total: 15
  not_honored: []

re_verification:
  round: 2
  previous_status: "frontmatter `passed` (канонизация 3260c9b7, 2026-09-23 15:35Z, на посылке «UAT 9/9»); тело отчёта `human_needed` (65b313bc)"
  previous_score: 12/13
  previous_round_record:
    verified: 2026-09-23T08:15:00Z
    report_commit: 65b313bc
    tree: 63f744be
    status_canonicalized_by: 3260c9b7
    covered_digest: "v1:sha256:740a47e9fa6e00d45fbac8f45def06dc68bc4bd009676eec70f19d5fd9bb5ee9"
    covered_files_count: 46
    backup: "/tmp/claude-1000/-source-broadcaster/5237445f-ef32-49eb-8249-b51037b7bd3a/scratchpad/14-VERIFICATION.pre-round.md"
  why_stale: "покрытые файлы изменились после закрытия круга: REQUIREMENTS.md; 14-02…14-06-PLAN.md (только перенумерация угроз, feaa701f); app.css и четыре модуля гейтов (дописаны Фазой 15)"
  what_changed:
    - "Продуктовый код фазы — НОЛЬ строк: `git diff 63f744be HEAD` по app/pages/auth.py, app/pages/htmx.py, app/main.py, app/templates/auth/, auth_base.html, base.html, components/, includes/notice_area.html, app/services/auth_service.py пуст (замер круга 2)"
    - "includes/htmx_error_banner.html (его включает auth_base.html:66): изменены ТОЛЬКО два aria-label органа снятия плашки (планы 15-07/15-19); новых обработчиков нет"
    - "app.css: правила `.auth-*`, `.field*`, `.form-busy`, `.form-wrapper` побайтово те же; Фаза 15 тронула токен `--focus-ring`, отступ `.failure-stack > .alert` и плитку медиа"
    - "test_auth_transport.py: +16 строк докстроки правила CR-02 (81894644), кода 0; прочие модули правил фазы — без правок; модули гейтов выросли правилами Фазы 15 (номера строк сдвинуты, значения констант фазы те же)"
    - "14-UAT.md: объявление `complete` отозвано (f2361428); 14-SECURITY.md: перенумерация угроз T-14-22…34 (feaa701f), принятие T-14-21/R-14-03"
  premise_withdrawn: "обход человека 9/9 — отозван владельцем; `passed` круга 1 не наследуется"
  gaps_closed: []  # в круге 1 блока `gaps` не было
  gaps_remaining: []
  regressions: []  # регрессий кода нет; расхождения ЗАПИСЕЙ — см. W-R2-01…03 в теле
  carried_items_closed:
    - "Эскалация CR-02 / WR-07 — решена владельцем 2026-09-23 (T-14-21 closed (accepted), R-14-03; летопись правила 81894644)"
    - "Отсрочка 3 (`hx-push-url` на формах авторизации) — закрыта Фазой 15, критерий 3 (15-FORM-DECISIONS.md, строки 35–44; правила `test_push_url_*` зелены)"

deferred:
  - truth: "23 `must_haves.prohibitions` across plans 14-01…14-07 stand at `status: flagged-unverified`, `verification: none` — no machine enforcement reads them"
    addressed_in: "Phase 15"
    evidence: "Phase 15 success criterion 6: «Запреты планов ПЕРЕПИСАНЫ ОДНИМ ПРИБОРОМ, и по каждому принято решение… Критерий закрыт, когда (а) в дереве есть ОДИН исполняемый прибор переписи… и (б) по каждому запрету его перечня стои́т ЛИБО предъявленное машинное принуждение, ЛИБО явное человеческое разрешение»"
    round_2_status: open
    round_2_addressed_in: "НЕ НАЗНАЧЕН — Фаза 15 закрыла только половину (а)"
    round_2_evidence: "(а) прибор есть: `scripts/prohibitions_census.py`, реестр `15-prohibitions-registry.yaml` несёт все 23 строки 14-01#0…14-07#2; `tests/test_planning/test_plan_prohibitions_census.py` — 109 passed (круг 2). (б) решения НЕТ: все 23 строки — `class: unclassified`, `disposition: unresolved`; D-02 Фазы 15 ограничил область решений Фазой 10 (321), фазы 07–09 и 11–14 «прибор перечисляет и явно помечает неразобранными»; 15-CONTEXT §Deferred: «Адресат не назначен — требует решения владельца при планировании следующей вехи». Отсрочка на Фазу 15 тем самым НЕ исполнена — маршрутизировано владельцу (human_verification 10, owner_questions Q3)"
  - truth: "Cross-origin (`is_same_origin`) guard absent on nine of ten auth POST handlers — CR-01"
    addressed_in: "Owner-recorded deferral, 14-CONTEXT.md §Deferred Ideas (not a numbered later phase)"
    evidence: "14-CONTEXT.md §Deferred Ideas: «Проверка источника запроса на формах входа и регистрации. Сегодня у девяти форм `is_same_origin` нет, защита — только `SameSite=Lax`. Подделка входа… — отдельная работа по безопасности, не транспорт.» Also named out-of-boundary at 14-CONTEXT.md:32."
    round_2_status: open
    round_2_evidence: "перемерено 2026-10-07: `app/pages/auth.py` — 10 `@router.post`, `is_same_origin` вызывается ОДИН раз (`:691`, возврат). Риск принят владельцем как T-14-08 / R-14-01 (14-SECURITY.md; аудит: «CR-01 — это T-14-08 в своей общей форме… остаётся действительным»). Адресат-фаза по-прежнему не назначен"
  - truth: "`hx-push-url` на формах авторизации — решение Фазы 15 (D-08 этой фазы)"
    addressed_in: "Phase 15"
    evidence: "D-08 этой фазы + критерий 3 Фазы 15 («По КАЖДОЙ форме принято и записано решение о `hx-push-url` по конвенции трёх случаев…»)"
    round_2_status: closed
    round_2_evidence: "15-FORM-DECISIONS.md строки 35–44 — решение по всем десяти формам (шесть экранов кода — второй случай, атрибута нет; вход и возврат — третий; завершение регистрации и новый пароль — третий, ветвь владельца `case-three-server-header`, chubav, 2026-09-24); `grep hx-push-url` по app/templates/auth/, auth_base.html, form_wrapper.html — 0; правила `test_push_url_decisions_cover_every_post_handler`, `…_every_write_place_resolves_to_a_decided_handler`, `…_zero_in_markup_is_a_decision_not_a_gap`, `…_dual_branch_handlers_are_case_three` — PASS (круг 2)"

escalations:
  - id: CR-02 / WR-07
    question: "Does the password-reset token replay belong in Phase 14's verdict or in a named follow-up?"
    verifier_recommendation: "Follow-up, with a named obligation recorded now — see §Escalation below."
    decision_owner: chubav
    status: awaiting_human_decision  # круг 1, запись своего дня
    round_2_status: closed
    decided_on: 2026-09-23
    decision: "Follow-up (рекомендация принята): изъян принят риском, починка — отдельной задачей вне Фазы 14"
    evidence: "14-SECURITY.md: T-14-21 `closed (accepted)`, раздел «Вне реестра планирования: T-14-21 (CR-02)», R-14-03 (chubav, 2026-09-23); летопись у правила `test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice` (`tests/test_pages/test_auth_transport.py:1706`, докстрока, коммит 81894644) — названная обязанность записана. Изъян в коде остаётся по решению: `verified_at` по-прежнему читается/пишется только `:408, :443, :916, :950`"

flagged_prohibitions: 23 # all `verification: none` / `status: flagged-unverified`; never counted green — deferred to Phase 15 SC6
# круг 2: всё ещё 23, открыто. Фаза 15 их ПЕРЕПИСАЛА (реестр, 23 строки), но НЕ РЕШИЛА (D-02 —
# область решений только Фаза 10). Адресат не назначен → human_verification 10, owner_questions Q3.

human_verification:
  # Сверка с 14-UAT.md (9 проверок) — один пункт на проверку; пункт 10 — решение владельца по
  # запретам. Круг 1 → круг 2: 7 пунктов → 10; все 7 прежних открыты (таблицы отметок пусты),
  # проверка 6 UAT (менеджер паролей) в списке круга 1 отсутствовала — добавлена.
  - test: "UAT проверка 1 (круг 1 — п.1). Полный вход в браузере: открыть `/login`, ввести неверный пароль, затем верный"
    expected: "Неверный пароль перерисовывает карточку БЕЗ перезагрузки, email остаётся в поле, заголовок вкладки — «Вход — Broadcaster»; верный пароль уводит в кабинет ПОЛНОЙ загрузкой, cookie `access_token` сменилась"
    why_human: "Рантайм подмены htmx, заголовок вкладки и смена cookie сервером не измеряются — суита не исполняет JS ни строчки (ROADMAP критерий 4, D-02)"
  - test: "UAT проверка 2 (круг 1 — п.2, первая половина). Регистрация: `/register` → новый адрес → экран кода; затем короткий и годный пароль на завершении"
    expected: "Экран кода приезжает без перезагрузки, адресная строка остаётся `/register`, вкладка — «Подтверждение email — Broadcaster»; короткий пароль оставляет имя; завершение уводит в кабинет полной загрузкой с пробным сроком"
    why_human: "Рантайм подмены, адресная строка и заголовок вкладки — только в браузере"
  - test: "UAT проверка 3 (круг 1 — п.2, вторая половина). Подтверждение почты НАСТОЯЩИМ письмом: код из реального ящика, неверный код, повтор, F5 на шаге"
    expected: "Письмо доходит; неверный код — «Неверный код. Осталось попыток: N» и набранный код в поле; повтор присылает новое письмо, обе формы живы; F5 возвращает к началу пути (D-08)"
    why_human: "Доставка настоящего письма (D-02: код из базы подставлять запрещено; правило останова) и рантайм подмены"
  - test: "UAT проверка 4 (круг 1 — п.3). Восстановление пароля целиком: `/forgot-password` → код из письма → новый пароль → `/login` с плашкой → вход новым паролем"
    expected: "Плашка «Пароль успешно изменён. Войдите с новым паролем.» видна на `/login` и переживает ошибку входа старым паролем; вход новым паролем проходит"
    why_human: "Доставка письма и визуальное подтверждение плашки области уведомления шелла"
  - test: "UAT проверка 5 (круг 1 — п.4). Возврат из-под чужой личности: «ВЕРНУТЬСЯ В АДМИНА» из полосы"
    expected: "Адресная строка `/admin`, заголовок вкладки — админки, полосы имперсонации нет, cookie без признака действующего лица"
    why_human: "Смена cookie личности и заголовок вкладки через границу шеллов в живом браузере (D-12)"
  - test: "UAT проверка 6 (в круге 1 НЕ было — добавлено при сверке). Менеджер паролей в Chrome и Firefox на чистом профиле, база сравнения — путь без JS"
    expected: "Пять наблюдений RESEARCH Находки 7: предложение сохранить пароль после верного входа и завершения регистрации, обновить — после нового пароля, нет предложения на 422; регрессия относительно пути без JS выносится владельцу, а не глушится"
    why_human: "Эвристики сохранения пароля — свойство браузера (A1–A3), сервером не измеряются ни одним утверждением"
  - test: "UAT проверка 7 (круг 1 — п.7). Карточка авторизации на 375px и на десктопе, во всех семи экранах"
    expected: "Подзаголовок сразу под брендом, промежутки как до фазы, индикатор у кнопки; читаема ли иерархия (все тексты тела 13px, заголовочного элемента нет ни на одном экране)"
    why_human: "Визуальное суждение; дев-сервер во время ревизии не отвечал, скриншотов нет (14-UI-REVIEW Pillars 2/4/5, A4)"
  - test: "UAT проверка 8 (круг 1 — п.5). Клавиатурный проход по экрану кода после 422: нажать Tab сразу после неверного кода; то же со скринридером и на экране входа"
    expected: "Наблюдаемо, куда попадает фокус после `hx-swap=\"innerHTML\"` в `#auth-step` и объявляется ли смена экрана"
    why_human: "В дереве шаблонов авторизации нет ни `autofocus`, ни `tabindex`, ни `aria-live` (машинно подтверждено и в круге 2 — 0 совпадений); КУДА при этом попадает фокус и что слышит скринридер — наблюдение, не грепа (14-UI-REVIEW WARNING 2)"
  - test: "UAT проверка 9 (круг 1 — п.6). На экране кода нажать «Отправить код повторно», пока «Подтвердить» в полёте"
    expected: "Наблюдаемо, выглядит ли вторая кнопка живой при отброшенном `hx-sync` запросе; действие не теряется"
    why_human: "`hx-disabled-elt=\"find button[type=submit]\"` гасит кнопку ТОЛЬКО своей формы; запрос отбрасывается `hx-sync` (доказано `test_both_code_forms_ride_the_anchor_and_drop_a_second_request`, PASS в круге 2), но видимость этого — суждение глазами (14-UI-REVIEW WARNING 3)"
  - test: "НЕ проверка обхода — решение владельца. 23 запрета планов 14-01…14-07 (`flagged-unverified`, `verification: none`): назначить адресата и/или принять по каждому решение (принуждение правилом либо явное разрешение)"
    expected: "У каждой из 23 строк реестра `15-prohibitions-registry.yaml` (14-01#0…14-07#2) — диспозиция, поставленная по ответу владельца, либо записанный адресат следующей вехи"
    why_human: "Запреты уровня суждения (ADR-550): помеченный запрет не поглощается вердиктом молча; Фаза 15 их переписала, но решать запретила себе сама (D-02). Назначить адресата может только владелец"

human_verification_round_1:  # круг 1 — ДОСЛОВНО (7 пунктов); все 7 открыты в круге 2
  - test: "Полный вход в браузере: открыть `/login`, ввести неверный пароль, затем верный"
    expected: "Неверный пароль перерисовывает карточку БЕЗ перезагрузки, email остаётся в поле, заголовок вкладки — «Вход — Broadcaster»; верный пароль уводит в кабинет ПОЛНОЙ загрузкой, cookie `access_token` сменилась"
    why_human: "Рантайм подмены htmx, заголовок вкладки и смена cookie сервером не измеряются — суита не исполняет JS ни строчки (ROADMAP критерий 4, D-02)"
    round_2_state: open  # → human_verification круга 2, UAT 1; отметка в 14-UAT.md пуста
  - test: "Регистрация целиком с НАСТОЯЩИМ письмом: `/register` → код из реального ящика → имя и пароль → кабинет"
    expected: "Экран кода приезжает без перезагрузки, адресная строка остаётся `/register`, письмо с кодом доходит, неверный код оставляет набранное, завершение уводит в кабинет полной загрузкой"
    why_human: "Доставка настоящего письма (D-02: код из базы подставлять запрещено) и рантайм подмены"
    round_2_state: open  # → human_verification круга 2, UAT 2+3; отметка в 14-UAT.md пуста
  - test: "Восстановление пароля целиком: `/forgot-password` → код из письма → новый пароль → `/login` с плашкой → вход новым паролем"
    expected: "Плашка «Пароль успешно изменён. Войдите с новым паролем.» видна на `/login`, вход новым паролем проходит"
    why_human: "Доставка письма и визуальное подтверждение плашки области уведомления шелла"
    round_2_state: open  # → human_verification круга 2, UAT 4; отметка в 14-UAT.md пуста
  - test: "Возврат из-под чужой личности: «ВЕРНУТЬСЯ В АДМИНА» из полосы"
    expected: "Адресная строка `/admin`, заголовок вкладки — админки, полосы имперсонации нет, cookie без признака действующего лица"
    why_human: "Смена cookie личности и заголовок вкладки через границу шеллов в живом браузере (D-12)"
    round_2_state: open  # → human_verification круга 2, UAT 5; отметка в 14-UAT.md пуста
  - test: "Клавиатурный проход по экрану кода после 422: нажать Tab сразу после неверного кода"
    expected: "Наблюдаемо, куда попадает фокус после `hx-swap=\"innerHTML\"` в `#auth-step`"
    why_human: "В дереве шаблонов авторизации нет ни `autofocus`, ни `tabindex`, ни `aria-live` (машинно подтверждено); КУДА при этом попадает фокус и что слышит скринридер — наблюдение, не грепа (14-UI-REVIEW WARNING 2)"
    round_2_state: open  # → human_verification круга 2, UAT 8; отметка в 14-UAT.md пуста
  - test: "На экране кода нажать «Отправить код повторно», пока «Подтвердить» в полёте"
    expected: "Наблюдаемо, выглядит ли вторая кнопка живой при отброшенном `hx-sync` запросе"
    why_human: "`hx-disabled-elt=\"find button[type=submit]\"` гасит кнопку ТОЛЬКО своей формы; запрос отбрасывается `hx-sync` (доказано `test_both_code_forms_ride_the_anchor_and_drop_a_second_request`), но видимость этого — суждение глазами (14-UI-REVIEW WARNING 3)"
    round_2_state: open  # → human_verification круга 2, UAT 9; отметка в 14-UAT.md пуста
  - test: "Карточка авторизации на 375px и на десктопе, во всех семи экранах"
    expected: "Наблюдаемо, читаема ли иерархия карточки (все тексты тела 13px, заголовочного элемента нет ни на одном из семи экранов)"
    why_human: "Визуальное суждение; дев-сервер во время ревизии не отвечал, скриншотов нет (14-UI-REVIEW Pillars 2/4/5)"
    round_2_state: open  # → human_verification круга 2, UAT 7; отметка в 14-UAT.md пуста
owner_questions:
  - id: Q1
    question: "SIGN-01…03 стоят `[x]` / `Complete` (их перевёл `phase.complete` на посылке «UAT 9/9», которую владелец отозвал), а вердикт фазы — `human_needed`. Правило `tests/test_planning/test_requirement_completion_follows_verification.py::test_no_requirement_is_marked_complete_before_its_phase_verification_passed` при таком сочетании краснеет. Что делать?"
    verifier_recommendation: "Сейчас вернуть SIGN-01…03 в `[ ]` / `Pending` (правка записей оркестратором с согласия владельца, текст требований не трогать) — запись совпадёт с отзывом владельца; провести обход `14-UAT.md` до `/gsd-complete-milestone` (STATE.md:27 его уже называет) и после него перепроверить фазу. Выбрать `passed` ради зелени правила верификатор не вправе: машинная половина требований выполнена, но вердикт фазы держит критерий 4"
    decision_owner: chubav
  - id: Q2
    question: "В `14-UAT.md` раздел `## Tests` несёт `result: pass` / `reported: \"pass\"` у всех девяти проверок, `## Summary` — `passed: 9`, `Current Test` — `[testing complete]`; абзац отзыва в шапке того же файла говорит «Обход Фазы 14 глазами НЕ ПРОВОДИЛСЯ» и эти поля оставил нетронутыми намеренно. Оставить их или вернуть в `[pending]`?"
    verifier_recommendation: "Вернуть девять `result` в `[pending]`, `passed: 9` → `pending: 9` и `Current Test` в нетерминальное — правкой ЧЕЛОВЕКА или по его прямому указанию: это снятие неподтверждённой записи, а не заполнение. Правило самозаверения считает только таблицы отметок и сегодня зелено, поэтому само расхождение не поймает. Верификатор файл не правил"
    decision_owner: chubav
  - id: Q3
    question: "23 запрета Фазы 14 переписаны прибором Фазы 15, но не решены (D-02 Фазы 15). Кто адресат?"
    verifier_recommendation: "Назначить адресатом раунд решений по запретам следующей вехи тем же прибором и тем же порядком D-03/D-04 Фазы 15 (классы → решения). Входная улика для него — в теле, §Deferred Items, п.1: у 10 из 23 в дереве уже есть правила, на которых можно ЗАМЕРИТЬ принуждение; остальные 13 — процессные и уровня суждения (D-15, «число ставится прогоном», «текст критерия не переписан»)"
    decision_owner: chubav
  - id: Q4
    question: "R-14-02 (14-SECURITY.md) принят с основанием «тексты переехали дословно (D-15) — фаза различимость ответов не создавала». Замер круга 2 это основание опровергает в части КОДОВ ответа (WR-03): до фазы оба исхода отправки кода отвечали 200, после — 422/200. Перепринять с исправленным основанием или направить на починку?"
    verifier_recommendation: "Перепринять явно с исправленным основанием (фаза СОЗДАЛА однобитовый оракул по строке статуса на `/forgot-password/send-code` и `/register/send-code`, и при CR-01 он достижим со стороннего сайта) и приписать починку к той же отсроченной работе по перечислению адресов (14-CONTEXT §Deferred). Вердикт фазы это не меняет: 422 на ошибке — само предметное решение D-03"
    decision_owner: chubav
---

# Phase 14: Авторизация на htmx — Verification Report

**Phase Goal:** неверный код или пароль перестаёт стирать заполненную форму — заявленный выигрыш вехи именно в ОШИБКЕ, а не в успехе
**Verified:** 2026-10-07T12:31:06Z (круг 2; круг 1 — 2026-09-23T08:15:00Z)
**Status:** human_needed
**Re-verification:** Да — КРУГ 2, перепроверка закрытой и отгруженной фазы на дереве после вехи (HEAD `ec41dcef` = origin/master `023d70a4` + два коммита записей). В отчёте круга 1 блока `gaps` не было, поэтому по букве шага 0 это прогон в полном объёме, а не узкий: все 13 истин перепроверены заново, а не перенесены.

**Что изменилось с круга 1 — и чего не наследую.** Круг 1 закончился `human_needed` 12/13 (SC4 — воздержание бэкстопа). Шапку потом канонизировали в `passed` (3260c9b7) на словесном «UAT 9/9» из `/gsd-verify-work 14`, а тело так и осталось `human_needed`. Владелец 2026-09-23 это объявление ОТОЗВАЛ: план 15-06 (f2361428) вернул шапку `14-UAT.md` в `human_needed`, и абзац отзыва говорит прямо, что обход глазами не проводился. Посылка канонизации снята её же владельцем, поэтому `passed` здесь не наследуется. Вердикт ниже выведен из улик дерева 2026-10-07.

**Method.** Goal-backward. Must-haves — четыре критерия ROADMAP (контракт) плюс истины фронтматтера планов 14-01…14-07. SUMMARY-заявления уликой не считаются. Каждая строка ВЕРНО ниже опирается либо на строки, прочитанные в дереве `ec41dcef`, либо на **именованное** правило, прогнанное мною в этом круге. Таких правил 162 в четырёх вызовах `pytest`, суита целиком НЕ перезапускалась: 25 правил фазы, 24 правила гейтов `hx-push-url` и записей, 109 правил прибора переписи запретов, плюс прогон `tests/test_planning` (208 правил) после записи отчёта — §Self-check. Полный прогон оркестратора (4084 passed на `feaa701f`, 43:44) взят входом, а не доказательством критерия.

**Главный замер круга.** Продуктовый код фазы с дерева круга 1 не изменился НИ СТРОКОЙ: `git diff 63f744be HEAD` по `app/pages/auth.py`, `app/pages/htmx.py`, `app/main.py`, `app/templates/auth/`, `auth_base.html`, `base.html`, `components/`, `includes/notice_area.html`, `app/services/auth_service.py` пуст. Два общих файла, которые Фаза 15 тронула, на истины фазы не влияют:
- `includes/htmx_error_banner.html` (включается `auth_base.html:66`) — изменены только два `aria-label` органа снятия плашки, новых обработчиков нет;
- `app.css` — строки правил `.auth-*`, `.field*`, `.form-busy`, `.form-wrapper` до и после побайтово равны.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence (круг 2) |
|---|-------|--------|----------|
| 1 | **SC1 / SIGN-02.** Неверный код или пароль перерисовывает форму С СОХРАНЕНИЕМ введённого: 422 + эхо в `value=`; свойство создаёт СЕРВЕР | ✓ VERIFIED | Сервер не менялся: `login_submit` (`app/pages/auth.py:269-271`) на ошибке зовёт `respond_field_error`, тот — `_respond_by_transport(..., status_code=422)` (`app/pages/htmx.py:903-957, 996-1021`); эхо — параметром в шаблон (`login_step.html:39`, `register_verify_step.html:54`, `register_complete_step.html:38`). ПРОГОН круга 2: правила 1-4 и трасер `test_the_login_path_walks_from_a_wrong_password_to_the_dashboard` — PASS; утверждения значимого уровня (`value="{email}"` на ОБОИХ транспортах, `test_auth_transport.py:185,203` — строки до правки докстроки, не сдвинуты) |
| 2 | **SC2 / SIGN-01.** Все 9 форм авторизации идут через `hx-post` и остаются рабочими без JS | ✓ VERIFIED | Перемерено: `grep -rn 'form_wrapper(' app/templates/auth/` → РОВНО 9; десятая — `base.html:89`. Без JS держится ПОСТРОЕНИЕМ макроса (`components/form_wrapper.html:188`, файл не менялся). Прогон: правила 5-7 и 10 — PASS |
| 3 | **SC3 / SIGN-03.** Успех авторизации уходит `HX-Redirect` через границу шеллов; `HX-Location` — по летописи | ✓ VERIFIED | Читано ПО ЛЕТОПИСИ (§Criterion 3). Строки источника те же, что в круге 1 (код не менялся): `redirect_internal` у `:273`, `:617`, `:1115`; три ветки возврата `:716`, `:744`, `:748`; второй отправитель `HX-Location` — `forbid_when_impersonating` на `:790, :886, :966, :1058` через `location_response` (`app/main.py:231`). Прогон: правила 8-9 — PASS |
| 4 | **SC4.** Вход, регистрация, подтверждение почты и восстановление пароля проходят в браузере целиком | ⚠️ `insufficient_spec` (backstop abstention) | **НЕ проверяется кодом и НЕ проверено.** Все семь планов пометили истину `verification: backstop`. Круг 2: `14-UAT.md` — `status: human_needed`, `checks_declared: 9`, 9 разделов `## Проверка`, 9 таблиц «Отметка о закрытии», **все 9 ПУСТЫ** (замер: 9 пустых строк таблиц), абзац отзыва — «Обход Фазы 14 глазами НЕ ПРОВОДИЛСЯ». Строки `result: pass` раздела `## Tests` наблюдением не являются (их снял отзыв владельца) — см. W-R2-01, Q2. Маршрутизировано в §Human Verification |
| 5 | Враждебный ввод возвращается в `value=` ТОЛЬКО экранированным, на обоих транспортах | ✓ VERIFIED | Прогон: правило 2 и `test_a_hostile_code_and_name_come_back_escaped` — PASS; оба направления (`HOSTILE not in` И `value="{HOSTILE_ESCAPED}"`, `test_auth_transport.py:229-234`) |
| 6 | Пароль не возвращается НИКОГДА — ни в `value=`, ни в теле, ни в контексте шаблона | ✓ VERIFIED | `_screen_builders` поднимает `ValueError` на ключе `password` (`auth.py:211-215`, без изменений). Прогон: правила 1, 11 — PASS |
| 7 | Отказ 422 не несёт cookie сессии ни на одном транспорте; заблокированный с ВЕРНЫМ паролем получает 422 с `BLOCKED_LOGIN_ERROR` | ✓ VERIFIED | Порядок «пароль → блокировка → cookie» (`auth.py:260-272`) не менялся. Прогон: правила 1, 12 — PASS |
| 8 | Смена экрана — 200 на обоих транспортах; подписанный токен шага едет ТОЛЬКО скрытым полем | ✓ VERIFIED | `respond_screen` (`htmx.py:960-993`) и скрытые поля четырёх экранов — без изменений с круга 1, где просмотрены все 33 вызова выходов слоя; путь деградации — `htmx.py:1010`. Решение Фазы 15 «у шага нет собственного адреса — токен только скрытым полем» (15-FORM-DECISIONS §3) это подтверждает независимо |
| 9 | Возврат из-под чужой личности: три ветки, cookie перезаписана НА ЭТОМ ЖЕ ответе, следующий `GET /admin` отдаёт админку | ✓ VERIFIED (behaviour-dependent — доказано прогоном, не присутствием) | Истина о ПЕРЕХОДЕ СОСТОЯНИЯ; тройное правило утверждает последствие (`test_impersonation.py:1710-1743`, модуль не менялся). Прогон круга 2: правила 13-15 — PASS |
| 10 | Восстановление пароля под чужой личностью остаётся запрещённым на ВСЕХ четырёх шагах, на обоих транспортах | ✓ VERIFIED (behaviour-dependent) | Зависимость на `:790, :886, :966, :1058`. Прогон: правила 16-17 — PASS |
| 11 | Счётчик отставания вехи — ИМЕНОВАННЫЙ НОЛЬ, доказанный НЕ ВАКУУМНЫМ | ✓ VERIFIED | `NOT_YET_CONVERTED_COUNT = 0` — сегодня `test_htmx_gates.py:872` (в круге 1 — `:847`; строки сдвинуты правилами Фазы 15, значение то же). Прогон: правило 10 — PASS |
| 12 | Реестр `AUTH_SCREENS` накрывает ВСЕ семь страниц второго шелла; заголовок фрагмента и заголовок страницы сличаются | ✓ VERIFIED | Семь записей `AUTH_SCREENS` (`auth.py:139-179`) против семи `app/templates/auth/*.html`. Прогон: правило 18 и `test_every_converted_screen_title_matches_its_page` — PASS |
| 13 | Записи фазы приведены в объявленную форму: летописи критериев 2 и 3, строки Research, SIGN-03, рамки вехи; окно 63 переведено ЗАМЕРОМ; артефакт обхода размечен | ✓ VERIFIED | Летописи на месте: ROADMAP `:701`, `:703`, `:705`; `REQUIREMENTS.md:63` (SIGN-03); `PROJECT.md:80` и `:258` (в круге 1 — `:254`, сдвиг). Окно 63 `.planning/WINDOWS.md:80` — `waived`; замер перепроверен: голого `Response(status_code=403)` в `app/pages/` — 15 вхождений, из них одно строка докстринга `htmx.py:9` ⇒ 14; `OWN_RESPONSE_EXITS_DECLARED = 14` (сегодня `test_htmx_gates.py:5528`, в круге 1 — `:5503`). Артефакт обхода размечен: 9 проверок, 9 пустых таблиц, предусловия и правило останова на месте, шапка нетерминальна. ⚠️ Разметка с тех пор изменилась ДРУГИМИ процессами, а не планом 14-07: 7 → 9 проверок (круг 1), `testing` → `complete` → `human_needed` (обход, отзыв), `result: [pending]` → `result: pass` (обход). Последнее расходится с отзывом — это отдельная находка W-R2-01, вердикта истины плана она не меняет |

**Score:** 12/13 truths verified (0 present-but-behaviour-unverified; 1 backstop abstention routed to human). Круг 1 → круг 2: тот же счёт и те же статусы истин. Изменился вердикт фазы: шапка была `passed` и снята, тело было и осталось `human_needed`.

Две истины (9 и 10) зависят от ПОВЕДЕНИЯ — переход состояния и отсутствие побочного действия, — и присутствием символов они бы не закрывались. Обе закрыты прогоном именованных правил в ЭТОМ круге, а не грепом и не переносом из круга 1.

### Criterion 3 — read against its chronicles, not literally

Критерий 3 буквально говорит «`HX-Location` остаётся ТОЛЬКО у `/impersonation/stop`, не пересекающего границу шеллов». Буквальное чтение дало бы ДВА расхождения. Оба названы летописью плана 14-07 ЗАРАНЕЕ и подтверждены мною в источнике:

| Буквальная посылка | Что в дереве | Где названо |
|---|---|---|
| «`/impersonation/stop` не пересекает границу шеллов» | Верно для ДВУХ веток из трёх. Третья — действующего лица нет в базе либо оно заблокировано — уходит `HX-Redirect` на `/login` (`auth.py:744`) со снятием cookie, то есть ЧЕРЕЗ границу | ROADMAP летопись критерия 3 (б); REQUIREMENTS SIGN-03; D-12 |
| «`HX-Location` — ТОЛЬКО у возврата» | Второй отправитель существует: отказ `forbid_when_impersonating` на четырёх шагах восстановления (`auth.py:790, :886, :966, :1058`) → `HtmxRefusal` → `location_response` (`app/main.py:224-231`). Живёт ВНЕ модуля авторизации | ROADMAP летопись критерия 3 (в); D-13 |

Машинное правило `test_hx_location_in_the_auth_module_belongs_to_the_return_only` утверждает равенство `{stop_impersonation}` внутри `app/pages/auth.py` и второго отправителя НЕ ВИДИТ ПО ПОСТРОЕНИЮ — вселенная правила есть модуль авторизации. Эта граница названа в шапке гейта, а не оставлена читателю. Правило и три его двухшаговых отрицательных контроля стоят в дереве (`test_htmx_gates.py:6312-6484` в круге 1).

**Круг 2.** Номера строк сдвинуты правилами Фазы 15, дописанными выше. Сегодня гейт стоит на `test_htmx_gates.py:6337-6520`:
- `test_only_the_named_auth_handlers_leave_by_a_full_load` — `:6337`;
- `test_every_full_load_address_is_a_literal_local_path` — `:6362`;
- `test_hx_location_in_the_auth_module_belongs_to_the_return_only` — `:6379`;
- три контроля — `:6408`, `:6447`, `:6485`.

Строки `auth.py` и `app/main.py` в таблице выше не сдвинулись: эти файлы не менялись. Правила 8-9 — PASS в этом круге.

**Вывод:** расхождения нет. Критерий 3 засчитан по летописи, и этот абзац стои́т здесь ровно затем, чтобы следующий читатель не открыл ложный изъян.

### Required Artifacts

| Artifact | Expected | Status | Details (круг 2) |
|---|---|---|---|
| `app/pages/htmx.py` | `redirect_internal`, `respond_screen`, `_respond_by_transport`, `respond_field_error` | ✓ VERIFIED | `:413`, `:960`, `:996`, `:903` — без изменений с круга 1 (diff пуст); все вызываются из `auth.py` |
| `app/pages/auth.py` | 10 обработчиков на выходах слоя; `AuthScreen`, `AUTH_SCREENS`, `AUTH_STEP_RESPONSE_TEMPLATE`, `_screen_markup`, `_screen_builders` | ✓ VERIFIED | 10 `@router.post`; diff пуст; ни один обработчик не собирает собственный ответ помимо слоя, кроме именованного 403 (`:704`, изъятие D-01) |
| `app/templates/auth/includes/step_response.html` | `<title>` верхним узлом + включение экрана | ✓ VERIFIED | Без изменений |
| `app/templates/auth/includes/*_step.html` (7) | Единственные источники разметки экранов, эхо в `value=` | ✓ VERIFIED | Без изменений |
| `app/templates/auth_base.html` | Постоянный якорь `#auth-step` ПОСЛЕ областей уведомления | ✓ VERIFIED | `:62` — `notice_area.html`, `:67` — `<div id="auth-step" class="auth-step">`; без изменений |
| `app/templates/base.html` | Форма возврата через `form_wrapper` без цели | ✓ VERIFIED | `:89` — без изменений |
| `tests/test_pages/test_auth_transport.py` | Сквозные пары на обоих транспортах | ✓ VERIFIED | 40 правил; с круга 1 — только +16 строк докстроки правила CR-02 (81894644) |
| `tests/test_pages/test_htmx_gates.py` | Именованный ноль, гейт критерия 3, `OWN_RESPONSE_EXITS` | ✓ VERIFIED | `:872`, `:5528`, `:6337-6520` (сдвиги от правил Фазы 15; значения фазы те же) |
| `.planning/ROADMAP.md`, `REQUIREMENTS.md`, `PROJECT.md`, `WINDOWS.md`, `14-UAT.md` | Летописи, окно 63, артефакт обхода | ✓ VERIFIED | См. истину 13 и W-R2-01 |

Ни одного MISSING, ни одного STUB, ни одного ORPHANED. Вербы `verify.artifacts` и `verify.key-links` по всем семи планам дают `total: 0` с кодом 1. Причина: блоки `artifacts` и `key_links` у планов фазы — строки, а не объекты `{path, provides}`. Верб их не разбирает, поэтому эти таблицы стоят на ручной проверке трёх уровней, а не на его вердикте (I-R2-04).

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Форма входа (`hx-target=#auth-step`, innerHTML) | `login_submit` | `respond_field_error` → экран входа с эхом внутри якоря | ✓ WIRED | Прогон правила 1 и трасера — PASS |
| `login_submit` / `register_complete` | `redirect_internal` → `set_session_cookie` НА ВОЗВРАЩЁННОМ объекте | `location.href` | ✓ WIRED | `auth.py:273-274`, `:617-618`; правила 19, 20 — PASS |
| `stop_impersonation` | `respond(redirect="/admin")` → `set_session_cookie` | `HX-Location` → `GET /admin` | ✓ WIRED | `auth.py:748-750`; правило 13 — PASS |
| Ветка закрытого действующего лица | `redirect_internal("/login")` → `clear_session_cookie` | `HX-Redirect` | ✓ WIRED | `auth.py:744-746`; правило 15 — PASS |
| `forgot_password_reset` | `redirect_internal(..., notice=PASSWORD_RESET_DONE)` | область уведомления шелла ВНЕ якоря | ✓ WIRED | `auth.py:1115`; утверждение порядка `index(RESET_DONE_TEXT) < index(STEP_ANCHOR)` — сегодня `test_auth_transport.py:1775` (в круге 1 — `:1759`, сдвиг на 16 строк докстроки); правило 21 — PASS |
| `forbid_when_impersonating` | `HtmxRefusal` → `location_response` | `app/main.py:231` | ✓ WIRED | Правила 16-17 — PASS |
| Гейт критерия 3 (`_full_load_callers` / `_hx_location_emitters`) | `FULL_LOAD_HANDLERS` / `AUTH_HX_LOCATION_HANDLERS` | равенство, не включение | ✓ WIRED | Правила 8-9 — PASS; проверки непустоты вселенной на месте |

### Data-Flow Trace (Level 4)

| Artifact | Data value | Source | Produces real data | Status |
|---|---|---|---|---|
| `login_step.html:39` | `value=email or ''` | `login_submit` → `_screen_builders(request, "login", error=…, email=email)` (`auth.py:270`) — присланная форма | Да | ✓ FLOWING |
| `register_verify_step.html:54` | `value=code or ''` | `register_verify` → `respond_field_error` с набранным кодом | Да | ✓ FLOWING |
| `forgot_password_verify_step.html:54` | `value=code or ''` | `forgot_password_verify` | Да | ✓ FLOWING |
| `register_complete_step.html:38` | `value=name or ''` | `register_complete` | Да | ✓ FLOWING |
| Скрытое поле `token` (4 экрана) | `value="{{ token }}"` | `create_verification_token(...)` — подписанный JWT, не литерал | Да | ✓ FLOWING |
| Поле пароля (2 экрана) | значения нет | — | **Намеренно пусто (D-04)** | ✓ FLOWING (по решению) — `_screen_builders` ФИЗИЧЕСКИ отказывает передать `password` в контекст |

Цепочки не изменились (код не менялся). Ни одного значения, чья цепочка кончается статическим возвратом, литералом или моком.

### Behavioural Spot-Checks

**Круг 2: 25 именованных правил одним вызовом `pytest` по идентификаторам узлов — 25 passed за 16.62 с** (`-p no:randomly`). В выборку вошли 21 правило круга 1 и четыре правила, на которые этот отчёт ссылается дополнительно:
- `test_the_login_path_walks_from_a_wrong_password_to_the_dashboard`;
- `test_both_code_forms_ride_the_anchor_and_drop_a_second_request`;
- `test_a_hostile_code_and_name_come_back_escaped`;
- `test_every_converted_screen_title_matches_its_page`.

Суита целиком НЕ перезапускалась.

| # | Proves | Named rule | Result (круг 2) |
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
| 22 | Трасер входа — от неверного пароля до кабинета | `::test_the_login_path_walks_from_a_wrong_password_to_the_dashboard` | ✓ PASS |
| 23 | Отброс второго запроса на экране кода (UI WARNING 3) | `::test_both_code_forms_ride_the_anchor_and_drop_a_second_request` | ✓ PASS |
| 24 | Экранирование кода и имени | `::test_a_hostile_code_and_name_come_back_escaped` | ✓ PASS |
| 25 | `<title>` фрагмента = `<title>` страницы | `::test_every_converted_screen_title_matches_its_page` | ✓ PASS |

**25/25 PASS.** Отдельными вызовами в этом круге:
- четыре правила `test_push_url_*` с `tests/test_planning/test_the_walkthrough_cannot_self_certify.py` и `tests/test_planning/test_requirement_completion_follows_verification.py` — **24 passed**. Записи замерены ДО записи этого отчёта, когда шапка ещё читалась `passed`;
- `tests/test_planning/test_plan_prohibitions_census.py` — **109 passed**;
- после записи отчёта — `tests/test_planning` целиком, итог в §Self-check и W-R2-03.

Независимые замеры (без pytest), выполненные мною в этом круге:

| Measurement | Command | Result |
|---|---|---|
| Продуктовый код с круга 1 | `git diff --stat 63f744be HEAD -- app/pages/auth.py app/pages/htmx.py app/main.py app/templates/auth/ app/templates/auth_base.html app/templates/base.html app/templates/components/ app/templates/includes/notice_area.html app/services/auth_service.py` | **пусто** |
| Общие файлы, тронутые Фазой 15 | `git diff 63f744be HEAD -- includes/htmx_error_banner.html app.css` | плашка: 2 `aria-label`; правила `.auth-*`/`.field*`/`.form-*` — идентичны |
| Число форм авторизации | `grep -rn 'form_wrapper(' app/templates/auth/` | 9 |
| Десятая форма | `grep -n 'form_wrapper(' app/templates/base.html` | 1 (`:89`) |
| Мест голого 403 | `grep -rn 'Response(status_code=403)' app/pages/` | 15, из них одно — докстринг ⇒ 14 |
| `is_same_origin` в модуле авторизации | `grep -n is_same_origin app/pages/auth.py` | импорт + один вызов (`:691`) из 10 `@router.post` |
| `verified_at` в модуле авторизации | `grep -n verified_at app/pages/auth.py` | `:408, :443, :916, :950` — у сброса нет (CR-02 по-прежнему в коде) |
| `error=` передан макросу поля на экранах авторизации | `grep -rn 'field(' app/templates/auth/ \| grep -c 'error='` | **0** (UI WARNING 1 в силе) |
| `autofocus` / `tabindex` / `aria-live` | `grep -rnE … app/templates/auth/ auth_base.html` | **0** (UI WARNING 2 в силе) |
| `hx-push-url` на формах авторизации | `grep -rn hx-push-url app/templates/auth/ auth_base.html form_wrapper.html` | 0 — согласно решению Фазы 15 |
| Покрытие решений CONTEXT | `gsd-tools query check.decision-coverage-verify` | **15/15 honored**, `not_honored: []` |
| Коммиты сводок | `gsd-tools query verify.commits` (27 хешей из семи SUMMARY) | `all_valid: true`, 27/27 |

### Probe Execution

Проб в дереве нет и фазой не объявлено (`find scripts -path '*/tests/probe-*.sh'` → 0; упоминаний `probe-` в планах 14-01…14-07 → 0). Шаг пропущен по отсутствию предмета, а не по невыполнению. Круг 2: без изменений.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| **SIGN-01** | 14-01, 14-02, 14-03, 14-04, 14-05, 14-06, 14-07 | 9 форм авторизации идут через htmx | ✓ SATISFIED (машинно); рантайм подмены — за человеком | Истина 2; замер 9 форм; правила 5-7. Остаток — наблюдение подмены в браузере (§Human Verification 1-5) |
| **SIGN-02** | 14-01, 14-02, 14-03, 14-04, 14-05, 14-07 | Неверный код или пароль перерисовывает форму с сохранением введённого | ✓ SATISFIED | Истины 1, 5, 6, 7; правила 1-4, 11-12, 22, 24. **Это и есть цель фазы, и она достигнута сервером** |
| **SIGN-03** | 14-01, 14-03, 14-05, 14-06, 14-07 | Успех — `HX-Redirect` через границу шеллов; `HX-Location` — у возврата | ✓ SATISFIED (по летописи, см. §Criterion 3) | Истина 3; правила 8-9, 13-15, 19-21 |

Круг 1: «**Отметки НЕ ставлю.** В `.planning/REQUIREMENTS.md` SIGN-01…03 стоят `[ ]` / `Pending` — и остаются: отметку ставит закрытие фазы (`phase.complete`) ПОСЛЕ верификации, а верификация ещё не завершена — критерий 4 у человека.»

**Круг 2.** Отметки с тех пор поставлены: `REQUIREMENTS.md:60-62` — `[x]`, `:159-161` — `Complete`. Их перевёл `phase.complete` (3260c9b7) на посылке «UAT 9/9», которую владелец отозвал. Сами требования машинно выполнены — таблица выше это подтверждает. Но правило записей связывает отметку с вердиктом фазы `passed`, а вердикт этого круга — `human_needed`, поэтому правило краснеет (W-R2-03). Отметки верификатор не правит; это вопрос владельцу Q1.

Сирот нет: таблица прослеживаемости `.planning/REQUIREMENTS.md:159-161` и сводка `:505` отображают на Фазу 14 ровно SIGN-01, SIGN-02, SIGN-03, и все три заявлены планами.

### Decision Coverage

15 из 15 отслеживаемых решений `14-CONTEXT.md` (D-01…D-15) опознаны в поставленных артефактах; `not_honored` пуст. Перемерено в круге 2 тем же вербом, итог тот же. Гейт незапирающий; записано для истории дрейфа.

Отдельно перепроверено чтением, что D-15 («фаза меняет транспорт, а не решения») исполнен буквально: набор проверок `purpose`/`verified` в `app/pages/auth.py` ДО фазы (`git show fd69a26a`) и после — **один и тот же**, четыре места в обоих деревьях. Это важно не само по себе: именно оно превращает CR-01, CR-02 и WR-01 ревизии кода из «дефектов фазы» в «дефекты, которые фаза обязана была не трогать». **Круг 2:** те же четыре места, `:573, :901, :982, :1076`, код не менялся. Оговорка D-15 к WR-03: тексты переехали дословно, но **коды** ответов фаза изменила по D-03 — см. W-R2-02.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` в 41 покрытом файле круга 2 | — | **Ноль совпадений.** Гейт долговых меток зелёный |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` | ℹ️ Info | Единственные совпадения — `_PLACEHOLDER = "{}"` в `test_htmx_post_pairs.py` и его употребления: сентинел разборщика форматных строк гейта, не заглушка |
| — | — | Отключённые тесты (`skip` / `xfail`) в правилах фазы | — | **Ноль** (круг 2: `@pytest.mark.skip|xfail`, `pytest.skip(`, `pytest.xfail(` по всем покрытым модулям — 0) |
| — | — | Пустые реализации, статические возвраты, пустые обработчики | — | Ноль. Продуктовый код не менялся с круга 1, где все 33 вызова выходов слоя просмотрены |

Аудит качества тестов: круговых тестов нет (правила сличают ответ приложения с ЛИТЕРАЛАМИ, выписанными в самом правиле, а не со значениями, порождёнными системой); уровень утверждений — значимый (value-level) и поведенческий, не existence-level; у инвентарных правил есть проверки непустоты вселенной и двухшаговые отрицательные контроли на синтетике. Круг 2: модули правил фазы, кроме докстроки CR-02, не менялись — вывод аудита в силе.

### Findings Handed Over By Hand (code review and UI review)

Машинерия `--gaps` эти файлы не читает; они разобраны здесь поимённо, а не опущены.

У каждой находки ровно одно из двух состояний: **ОТКРЫТА** (перезаявлена кругом 2) или **ЗАКРЫТА** с названной уликой.

**Счёт.** Круг 1 вёл 9 строк, причём WR-03…WR-06 и IN-01…IN-03 шли одной групповой строкой без перепроверки. Круг 2 развёл их поимённо: 15 находок, **закрыто 2** (CR-02, WR-07 — решением владельца), **открыто 13**. Ни одна не опровергает истину фазы.

| ID | Severity in review | Вердикт круга 1 | Круг 2 — состояние и улика |
|---|---|---|---|
| **CR-01** — девять из десяти POST-обработчиков авторизации без `is_same_origin` | Critical, pre-existing | Подтверждено замером; НЕ изъян Фазы 14 — отсрочено владельцем до планирования (`14-CONTEXT.md:32`, §Deferred Ideas) → `deferred` | **ОТКРЫТА.** Перемерено: 10 `@router.post`, `is_same_origin` — один вызов (`:691`). Риск принят как T-14-08 / R-14-01 (14-SECURITY.md); адресат-фаза не назначен. Отсрочка 2 |
| **CR-02** — подтверждённый токен восстановления воспроизводим и самообновляем | Critical, pre-existing | Подтверждено чтением и прогоном; предшествует фазе (`git show fd69a26a`); правка нарушила бы D-15 → §Escalation | **ЗАКРЫТА** решением владельца: T-14-21 `closed (accepted)`, R-14-03 (chubav, 2026-09-23). Изъян в коде ОСТАЁТСЯ по этому решению: `verified_at` читается/пишется только `:408, :443, :916, :950`; ветка короткого пароля чеканит свежий токен (`:1097`). Починка — отдельная задача без адресата |
| **WR-07 / CR-02 (следствие)** — новое правило фазы утверждает воспроизведение как правильное | Warning | Подтверждено прогоном: один токен на два запроса; факт Фазы 14 → §Escalation | **ЗАКРЫТА** решением владельца: у правила поставлена летопись (`test_auth_transport.py:1706`, докстрока, 81894644), называющая повтор свойством сегодняшнего обработчика и обязывающая развести токены при починке CR-02. Перемерено: токен по-прежнему один (`:1733`), его подают оба запроса (`:1736`, `:1751`) — это и есть принятое состояние, а не невыполненная правка. Правило 21 — PASS |
| **WR-01** — `register_verify` и `register_resend_code` не проверяют `purpose` | Warning | Предшествует фазе; D-15 запрещал трогать; передано как известный остаток | **ОТКРЫТА.** Перемерено: `:394` и `:474` — только `if not payload:`; проверки `purpose` — `:573, :901, :982, :1076` |
| **WR-02** — пути страницы и фрагмента не делят контекст шаблона | Warning | ⚠️ Латентный риск, не изъян | **ОТКРЫТА** (латентная). Код не менялся; наблюдаемого расхождения нет (правило 7 — PASS) |
| **WR-03** — разделение кодов «адрес известен / неизвестен» превращает перечисление в машинный оракул | Warning | «Не перепроверял построчно… передаю как есть» | **ОТКРЫТА — и перепроверена впервые.** Это факт ФАЗЫ 14, а не предшествующий: `forgot_password_send_code` на неизвестном адресе — `respond_field_error` (422), на известном — `respond_screen` (200); до фазы оба исхода — `TemplateResponse` (200), `status_code=422` в `fd69a26a:app/pages/auth.py` — 0 вхождений. Основание принятия R-14-02 «фаза различимость ответов не создавала» в части кодов этим опровергнуто → W-R2-02, Q4 |
| **WR-04** — сбой отправки письма проглатывается и выдаётся за успех | Warning | Передано как есть | **ОТКРЫТА.** Код не менялся (diff пуст) |
| **WR-05** — четыре скопированных тела выдачи кода | Warning | Передано как есть | **ОТКРЫТА.** Код не менялся |
| **WR-06** — минимальная длина пароля — магическое `6` в пяти местах | Warning | Передано как есть | **ОТКРЫТА.** Код не менялся. STATE.md:27 держит её в списке до закрытия вехи |
| **IN-01** — `_respond_by_transport` молча теряет заголовки сборщика | Info | Передано как есть | **ОТКРЫТА.** Код не менялся |
| **IN-02** — страж пароля в `_screen_builders` ловит только ключ `password` | Info | Передано как есть | **ОТКРЫТА.** Код не менялся (`auth.py:211-215`) |
| **IN-03** — `created_at.replace(tzinfo=…)` читается как преобразование | Info | Передано как есть | **ОТКРЫТА.** Код не менялся |
| **UI WARNING 1** — 422 не помечает поле | Warning (UI 16/24, блокеров нет) | Подтверждено замером: `error=` — 0 вызовов. Слабая половина выигрыша, не невыполненный критерий | **ОТКРЫТА.** Перемерено: 0. 14-UI-REVIEW.md оставлен владельцем как есть |
| **UI WARNING 2** — ни фокуса, ни живой области после свопа | Warning | Механизма нет — решено кодом; КУДА фокус — наблюдение → человеку | **ОТКРЫТА.** Перемерено: 0 совпадений. Пункт человеку — §Human Verification 8 (UAT проверка 8) |
| **UI WARNING 3** — на экранах кода вторая кнопка остаётся живой | Warning | Смягчено: запрос отбрасывается `hx-sync`; видимость — человеку | **ОТКРЫТА.** Правило отброса — PASS в круге 2. Пункт человеку — §Human Verification 9 (UAT проверка 9) |

**Ни одна из этих находок не опровергает истину фазы, не ломает ключевую связь и не оставляет артефакт заглушкой.** Поэтому ни одна не поднята до 🛑 Blocker — и это сказано здесь прямо, вместе с основанием, а не умолчанием.

### New Findings Of Round 2

| ID | Finding | Severity | Evidence | Route |
|---|---|---|---|---|
| **W-R2-01** | `14-UAT.md` сам себе противоречит. Шапка `status: human_needed`, абзац отзыва: «Обход Фазы 14 глазами НЕ ПРОВОДИЛСЯ», 9 таблиц отметок пусты. При этом раздел `## Tests` несёт `result: pass` / `reported: "pass"` у всех девяти проверок, `## Summary` — `passed: 9`, `Current Test` — `[testing complete]` (коммит 54ebbf56, «complete UAT - 9 passed»). Абзац отзыва оставил эти поля нарочно («вердикта о них этот абзац не выносит») | ⚠️ Warning | Замер: `result: pass` — 9, `result: [pending]` — 0, пустых строк таблиц — 9. Правило самозаверения считает только таблицы и потому зелено — расхождение оно не видит | Q2. Файл не тронут (граница поручения) |
| **W-R2-02** | Основание принятого риска R-14-02 неполно. «Тексты переехали дословно — фаза различимость ответов не создавала» верно для ТЕКСТОВ и неверно для КОДОВ: фаза ввела 422/200 на исходах отправки кода (WR-03) | ⚠️ Warning (запись безопасности, не цель фазы) | `git show fd69a26a:app/pages/auth.py` — ни одного 422; сегодня `forgot_password_send_code`: `respond_field_error` на неизвестном адресе, `respond_screen` на известном (`auth.py:800-845`); то же у `register_send_code` с обратной полярностью. Истина 14-04 плана утверждает этот 422 — поведение намеренное (D-03) | Q4 |
| **W-R2-03** | При вердикте `human_needed` правило записей `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` краснеет: SIGN-01…03 стоят `Complete` без вердикта `passed` | ⚠️ Warning (записи) | Правило читает поле `status` шапки этого отчёта (`PASSED_VERDICT = "passed"`, `test_requirement_completion_follows_verification.py:67`); до записи отчёта зелено (шапка была `passed`), после — прогон в §Self-check | Q1. Отметки и правило не тронуты |
| **I-R2-01** | Запреты Фазы 14 Фазой 15 не решены (D-02) — отсрочка 1 не исполнена | ℹ️ Info (учётная), поднята в human_verification 10 | §Deferred Items, п.1 | Q3 |
| **I-R2-02** | Устаревшие записи вне границы поручения. `STATE.md:29`: «обход человека 9/9 без находок» — снято отзывом. Строка T-14-19 `14-SECURITY.md`: «файл обхода — `status: testing`… девять `result: [pending]`» — сегодня `human_needed` и `result: pass` | ℹ️ Info | Чтение | Оркестратору при следующей правке записей (идиома D-30/D-32 — летописью) |
| **I-R2-03** | Номера строк гейтов в отчёте круга 1 сдвинуты правилами Фазы 15 (`:847` → `:872`, `:5503` → `:5528`, `:6312` → `:6337`; `test_auth_transport.py:1759` → `:1775`) | ℹ️ Info | Замер | Исправлено в этом отчёте; строки круга 1 названы рядом |
| **I-R2-04** | Вербы `verify.artifacts` / `verify.key-links` не разбирают строковые блоки `artifacts` / `key_links` планов фазы (`total: 0`, код 1) | ℹ️ Info | Прогон по семи планам | Таблицы артефактов и связей стоят на ручной проверке |

### Self-check (после записи отчёта)

| Check | Command | Result |
|---|---|---|
| Вердикт читается владельцем статуса | `gsd-tools query verification.status <phaseDir> --pick status` | `human_needed`, код 0 (больше не `stale`); маршрут — `/gsd-verify-work 14` |
| Фронтматтер разбирается | `yaml.safe_load` блока между разделителями | ок: 10 пунктов человеку, 3 отсрочки (open, open, closed), эскалация `closed`, 4 вопроса, 55 покрытых файлов |
| Правила записей | `uv run pytest -q -p no:randomly tests/test_planning` | **1 failed, 207 passed** — краснеет ровно `test_requirement_completion_follows_verification.py::test_no_requirement_is_marked_complete_before_its_phase_verification_passed`: «требование `SIGN-01` (Phase 14) помечено `Complete`… а у его фазы вердикт `human_needed`» (то же для SIGN-02, SIGN-03). Это W-R2-03 — следствие честного вердикта, а не дефект отчёта; снимается ответом на Q1 |

### Advisory (New Scope, Unevidenced)

Нет. Узкий гейт улик (#3304) этому кругу формально не применим: в отчёте круга 1 блока `gaps` не было, и шаг 0 ведёт прогон в полном объёме. Все новые находки выше несут детерминированную улику (замер, прогон или чтение с номерами строк). Ни одна не 🛑 Blocker, ни одна не опровергает истину фазы.

### Escalation — решение владельца, которое я не вправе принять за него

> **Круг 2: ЗАКРЫТО.** Владелец (`chubav`) ответил 2026-09-23 по рекомендации ниже — «отдельная последующая работа с записанной сейчас обязанностью»:
> - T-14-21 `closed (accepted)` и R-14-03 в `14-SECURITY.md`;
> - раздел «Вне реестра планирования: T-14-21 (CR-02)» там же;
> - летопись у правила `test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice` (`tests/test_pages/test_auth_transport.py:1706`, коммит 81894644). Это ровно то, что абзац «Что должно быть записано ВМЕСТЕ с отсрочкой» ниже требовал. Повторно вопрос не задаётся.
>
> Остаток: починка CR-02 адресата не имеет, изъян в коде измерен на месте (см. CR-02 выше). Текст круга 1 ниже — запись своего дня.

**Предмет.** CR-02 (воспроизведение подтверждённого токена восстановления) предшествует Фазе 14 и её решением D-15 был выведен из правки. Но правило `test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice`, написанное ПЛАНОМ 14-05, теперь **утверждает это воспроизведение зелёным**. Это уже факт Фазы 14: будущая правка, которая начнёт гасить `verified_at`, ПОКРАСНИТ правило этой фазы, и следующий исполнитель встретит красное правило без объяснения, почему оно вообще так написано.

**Вопрос владельцу:** отнести CR-02 к вердикту Фазы 14 (то есть открыть gap и править здесь) или к отдельной последующей работе?

**Моя рекомендация — ОТДЕЛЬНАЯ ПОСЛЕДУЮЩАЯ РАБОТА, с записанной сейчас обязанностью.** Основания, а не удобство:

1. Правка требует изменить РЕШЕНИЕ обработчика (гасить `verified_at`, перестать чеканить свежий токен на отказе) — ровно то, что D-15 этой фазы запретил дословно. Фаза, нарушившая собственное запертое решение в последнем шаге, обесценила бы и остальные четырнадцать.
2. Дефект предшествует фазе: замер `git show fd69a26a` показывает тот же набор проверок. Отнести его к вердикту Фазы 14 значило бы объявить изъяном фазы то, что она обязана была не трогать.
3. Цена отсрочки названа и ограничена: токен живёт 30 минут, и для злоупотребления нужен уже утёкший подтверждённый токен.

**Что должно быть записано ВМЕСТЕ с отсрочкой** (иначе отсрочка — умолчание, а не решение): у правила `test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice` должна встать летопись, называющая прямо, что повторное использование ОДНОГО токена в этом правиле есть свойство СЕГОДНЯШНЕГО обработчика, а не утверждаемое требование, и что правку CR-02 полагается сопроводить разведением двух токенов в этом правиле. Летопись — это одна правка в комментарии, и она не меняет ни одного утверждения.

**Того же решения ждёт CR-01** — хотя он уже отсрочен владельцем в `14-CONTEXT.md` §Deferred Ideas, и потому отсрочка у него не молчаливая. *(Круг 2: для CR-01 отдельного решения не потребовалось — владелец принял его риском как T-14-08 / R-14-01 при `/gsd-secure-phase 14`; отсрочка 2 ниже.)*

### Deferred Items

Круг 1 → круг 2: три пункта → три пункта. **Открыто 2, закрыто 1.**

| # | Item | Addressed In (круг 1) | Evidence (круг 1) | Круг 2 — состояние и улика |
|---|---|---|---|---|
| 1 | 23 запрета планов 14-01…14-07 стоят `flagged-unverified` / `verification: none` — машинного принуждения не имеет ни один | Phase 15 | Критерий 6 Фазы 15 дословно: «Запреты планов ПЕРЕПИСАНЫ ОДНИМ ПРИБОРОМ, и по каждому принято решение… (а) в дереве есть ОДИН исполняемый прибор переписи, чьё число воспроизводимо, и (б) по каждому запрету стои́т ЛИБО предъявленное машинное принуждение, ЛИБО явное человеческое разрешение» | **ОТКРЫТ; адресат НЕ НАЗНАЧЕН.** Половина (а) исполнена: реестр `15-prohibitions-registry.yaml` несёт 23 строки 14-01#0…14-07#2, правило переписи — 109 passed. Половина (б) для Фазы 14 НЕ исполнена: все 23 — `unclassified` / `unresolved`. D-02 Фазы 15 (`15-CONTEXT.md:38-44`): «область решений — Фаза 10 (321)… остальные (фазы 07–09, 11–14) прибор перечисляет и явно помечает неразобранными»; §Deferred: «Адресат не назначен — требует решения владельца при планировании следующей вехи». Отсрочка на Фазу 15 не исполнилась и потому выведена в human_verification 10 и Q3 |
| 2 | CR-01 — гард источника запроса на девяти формах авторизации | Owner-recorded deferral (`14-CONTEXT.md` §Deferred Ideas), адресат-фаза не назначен | «Проверка источника запроса на формах входа и регистрации… отдельная работа по безопасности, не транспорт» | **ОТКРЫТ.** Перемерено: гард у 1 из 10. Риск принят (T-14-08 / R-14-01); адресат-фаза по-прежнему не назначен |
| 3 | `hx-push-url` на формах авторизации | Phase 15 | D-08 этой фазы + критерий 3 Фазы 15 | **ЗАКРЫТ** Фазой 15. `15-FORM-DECISIONS.md` строки 35–44: решение по каждой из десяти форм. Экраны кода — второй случай; вход и возврат — третий; завершение регистрации и новый пароль — третий, ветвь владельца `case-three-server-header` (chubav, 2026-09-24). Атрибута в разметке нет (0); правила `test_push_url_*` — PASS |

**Отсрочки статус не меняют.** Запреты я НЕ засчитываю зелёными: они помечены (`flagged_prohibitions: 23`) и остаются видимыми до Фазы 15. Ни один не поглощён молча вердиктом `passed` — вердикт и не `passed`. *(Круг 2: «до Фазы 15» не сбылось — см. п.1; запреты видимы и сегодня, вердикт снова не `passed`.)*

**Вход для Q3 — кандидатные правила, НЕ диспозиции.** Ставить диспозицию в реестре может только ответ владельца; ниже — где в дереве уже стоят правила, на которых принуждение можно ЗАМЕРИТЬ. Имена правил проверены, перечисленные прогнаны в этом круге.

У 10 из 23 кандидат есть:

| Строка реестра | Запрет | Кандидатное правило |
|---|---|---|
| 14-01#0, 14-03#0, 14-05#0 | пароль не возвращается | `test_the_screen_builders_refuse_a_password_in_the_context`, `test_a_short_password_keeps_the_name_and_answers_422_without_the_password`, `test_a_short_new_password_answers_422_without_echo_on_both_transports`. Слова «ни в журнале» ни одно не покрывает |
| 14-01#1 | 422 без cookie | `test_a_blocked_user_is_refused_with_422_and_no_cookie_on_both_transports` |
| 14-01#2 | смена личности только полной загрузкой | `test_only_the_named_auth_handlers_leave_by_a_full_load` |
| 14-04#0, 14-05#1 | восстановление под чужой личностью запрещено | `test_the_first_recovery_steps_are_refused_under_another_identity_on_both_transports`, `test_the_last_recovery_steps_are_refused_under_another_identity_on_both_transports` |
| 14-06#0 | токен не выпускается без действующего лица и закрытой учётной записи | `test_the_return_without_an_actor_goes_to_the_dashboard_on_both_transports`, `test_a_closed_actor_is_logged_out_by_the_return_on_both_transports` |
| 14-06#1 | форма отказа по источнику — голый 403 | `test_a_cross_origin_return_is_refused_with_a_bare_403_on_both_transports` |
| 14-07#1 | машинная улика обхода — не приёмка | `tests/test_planning/test_the_walkthrough_cannot_self_certify.py`. Поля `result` оно не видит — W-R2-01 |

Остальные 13 — процессные и уровня суждения, без кандидатного правила:
- D-15 — 14-01#3, 14-02#1, 14-03#1;
- «число ставится прогоном», шесть строк с одним `statement_digest` `c283ade07311`;
- токен не в адресе — 14-02#0, 14-04#1;
- 14-07#0 и 14-07#2.

### Human Verification Required

Круг 2: **десять пунктов**. Девять — один к одному с проверками `14-UAT.md`; десятый — решение владельца по запретам, а не проверка обхода. Круг 1 → круг 2: 7 → 10.
- Все семь пунктов круга 1 **ОТКРЫТЫ**: таблицы отметок пусты, обход не проводился.
- Пункт 2 круга 1 («регистрация целиком с настоящим письмом») разведён на проверки 2 и 3 UAT.
- Проверка 6 UAT (менеджер паролей) в списке круга 1 отсутствовала, хотя стояла в `14-UAT.md` с плана 14-07. Это пропуск круга 1, здесь исправлен.

Первые пять пунктов — критерий 4 ROADMAP, ручной ПО ПРОЕКТУ (настоящее письмо, браузер, смена cookie, заголовок вкладки). Шестой — эвристики браузера. Седьмой, восьмой и девятый — то, что ревизия интерфейса прямо оставила глазам.

Артефакт обхода `14-UAT.md` УЖЕ существует в размеченной форме и **остаётся как есть**: `status: testing`, семь пустых таблиц отметок, `result: [pending]`. Я не заполнил ни одной отметки и не тронул ни одного `result` — заполнить их значило бы самозаверение, а не приёмку (D-02; правило `tests/test_planning/test_the_walkthrough_cannot_self_certify.py`). Пункты ниже — маршрутизация к тому файлу, а не второй его экземпляр. *(Круг 2: сегодня шапка `human_needed`, проверок и пустых таблиц по девять, `result: pass` ×9 — см. W-R2-01. Файл этим кругом не тронут ни строкой.)*

**Предусловия (D-02, `14-UAT.md` §Предусловия):** рабочий SMTP на стенде; ящики П-2/П-3; админ и пользователь; чистые Chrome и Firefox; выключаемый JS; экраны 375px и десктоп. **Правило останова:** письма не доходят → обход останавливается, вопрос владельцу; код из базы не подставляется.

#### 1. Полный вход в браузере — UAT проверка 1 (круг 1: п.1)

**Test:** Открыть `/login`, ввести неверный пароль, затем верный; войти заблокированным.
**Expected:** Неверный пароль перерисовывает карточку БЕЗ перезагрузки страницы, введённый email остаётся в поле, заголовок вкладки — «Вход — Broadcaster». Верный пароль уводит в кабинет ПОЛНОЙ загрузкой, cookie `access_token` сменилась.
**Why human:** Рантайм подмены htmx, заголовок вкладки и смена cookie сервером не измеряются — суита не исполняет JS ни строчки.

#### 2. Регистрация до экрана кода и завершение — UAT проверка 2 (круг 1: п.2, первая половина)

**Test:** `/register` → новый адрес → экран кода; на завершении — короткий, затем годный пароль.
**Expected:** Экран кода приезжает без перезагрузки, адресная строка остаётся `/register`, вкладка меняет заголовок; короткий пароль оставляет имя; завершение уводит в кабинет полной загрузкой с пробным сроком.
**Why human:** Рантайм подмены, адресная строка и вкладка — только в браузере.

#### 3. Подтверждение почты настоящим письмом — UAT проверка 3 (круг 1: п.2, вторая половина)

**Test:** Код из РЕАЛЬНОГО ящика; заведомо неверный код; «Отправить код повторно»; F5 на шаге.
**Expected:** Письмо доходит, неверный код оставляет набранное, повтор присылает новое письмо, обе формы живы, F5 возвращает к началу пути.
**Why human:** Доставка настоящего письма (D-02 запрещает подставлять код из базы) и рантайм подмены.

#### 4. Восстановление пароля целиком — UAT проверка 4 (круг 1: п.3)

**Test:** `/forgot-password` → код из письма → новый пароль → `/login` → вход старым паролем → вход новым паролем.
**Expected:** Плашка «Пароль успешно изменён. Войдите с новым паролем.» видна на `/login` и не исчезает от ошибки формы; вход новым паролем проходит.
**Why human:** Доставка письма и визуальное подтверждение плашки шелла.

#### 5. Возврат из-под чужой личности — UAT проверка 5 (круг 1: п.4)

**Test:** Под чужой личностью нажать «ВЕРНУТЬСЯ В АДМИНА».
**Expected:** Адресная строка `/admin`, заголовок вкладки — админки, полосы имперсонации нет, cookie без признака действующего лица.
**Why human:** Смена cookie личности и заголовок вкладки через границу шеллов в живом браузере (D-12).

#### 6. Менеджер паролей — UAT проверка 6 (в круге 1 отсутствовал)

**Test:** Пять наблюдений RESEARCH Находки 7 в Chrome и Firefox на чистом профиле; база сравнения — вход и завершение регистрации с ВЫКЛЮЧЕННЫМ JS.
**Expected:** Предложение сохранить пароль там, где оно есть без JS; регрессия относительно пути без JS выносится владельцу отдельным вопросом.
**Why human:** Эвристики сохранения пароля — свойство браузера; сервером не измеряются.

#### 7. Карточка на 375px и на десктопе — UAT проверка 7 (круг 1: п.7)

**Test:** Пройти все семь экранов на узком и широком экране; сравнить промежутки с веткой до фазы.
**Expected:** Наблюдаемо, читаема ли иерархия карточки; подзаголовок под брендом; индикатор у кнопки; горизонтальной прокрутки нет.
**Why human:** Визуальное суждение; дев-сервер во время ревизии интерфейса не отвечал, скриншотов нет.

#### 8. Фокус и объявление после свопа — UAT проверка 8 (круг 1: п.5)

**Test:** На экране кода ввести неверный код, затем нажать Tab; то же со скринридером и на экране входа.
**Expected:** Наблюдаемо, куда попадает фокус и объявляет ли скринридер смену экрана.
**Why human:** Что механизма НЕТ — установлено кодом (ни `autofocus`, ни `tabindex`, ни `aria-live` во всём дереве авторизации; круг 2 — снова 0). КУДА при этом попадает фокус — только наблюдение.

#### 9. Вторая кнопка на экранах кода — UAT проверка 9 (круг 1: п.6)

**Test:** Нажать «Отправить код повторно», пока «Подтвердить» в полёте.
**Expected:** Наблюдаемо, выглядит ли вторая кнопка живой при отброшенном запросе.
**Why human:** Отброс доказан правилом (PASS в круге 2); ВИДИМОСТЬ отброса — суждение глазами.

#### 10. Решение владельца по 23 запретам (не проверка обхода)

**Test:** Назначить адресата и/или принять по каждому из 23 запретов (14-01#0…14-07#2) решение: принуждение правилом или явное разрешение.
**Expected:** У каждой строки реестра — диспозиция по ответу владельца либо записанный адресат.
**Why human:** Помеченный запрет уровня суждения не поглощается вердиктом молча; Фаза 15 переписала их, но решать себе запретила (D-02). Вход для решения — §Deferred Items, п.1.

### Owner Questions

Четыре вопроса, каждый с рекомендацией; решать их верификатор не вправе. Полные формулировки — во фронтматтере `owner_questions`.

- **Q1** — SIGN-01…03 `Complete` при вердикте `human_needed` краснит правило записей. **Рекомендация:** вернуть отметки в `Pending` сейчас, провести обход до `/gsd-complete-milestone`, затем перепроверить фазу.
- **Q2** — `result: pass` ×9 в `14-UAT.md` при отозванном обходе. **Рекомендация:** вернуть их в `[pending]` руками человека или по его указанию.
- **Q3** — адресат 23 запретов. **Рекомендация:** раунд решений по запретам следующей вехи тем же прибором и тем же порядком.
- **Q4** — R-14-02 принят на неполном основании (WR-03). **Рекомендация:** перепринять с исправленным основанием и приписать починку к отсроченной работе по перечислению адресов.

### Gaps Summary

**Изъянов, блокирующих достижение цели, не найдено** — ни в круге 1, ни в круге 2.

Цель фазы — «неверный код или пароль перестаёт стирать заполненную форму, и выигрыш именно в ОШИБКЕ» — **истинна в дереве, и истинной её делает СЕРВЕР**, а не разметка:
- код отказа 422 стои́т литералом в `respond_field_error`;
- эхо едет параметром в шаблон через автоэкранирующее окружение;
- путь без JavaScript получает ту же страницу прямо в ответ на POST.

Это подтверждено не присутствием символов, а прогоном именованных правил со значимыми утверждениями (`value="…"` в теле, пароль в теле отсутствует, cookie отсутствует) на ОБОИХ транспортах. В круге 2 — повторным прогоном на дереве `ec41dcef`, где продуктовый код фазы не изменился ни строкой.

Что осталось и почему это не изъяны:

- **Критерий 4 у человека** — так задумано (D-02: настоящее письмо, настоящий браузер). Артефакт обхода готов и не тронут мною. *(Круг 2: обход так и не проведён — владелец сам отозвал объявление о нём; 9 таблиц отметок пусты.)*
- **Три предупреждения ревизии интерфейса** касаются СИЛЫ выигрыша (поле не помечено красным, фокус никуда не ведётся, отброшенный клик невидим), а не его наличия. Введённое возвращается на всех семи экранах — это и есть критерий.
- **Две критические находки ревизии кода предшествуют фазе**, и обе перепроверены мною независимо в источнике и в дереве ДО фазы. CR-01 отсрочен владельцем письменно ещё до планирования. CR-02 — вынесен в §Escalation вместе с моей рекомендацией и с тем, что должно быть записано вместе с отсрочкой; молча он не опущен. *(Круг 2: CR-02 закрыт решением владельца — риск принят, летопись стоит; CR-01 принят риском и остаётся открытой отсрочкой.)*
- **23 запрета планов без машинного принуждения** отсрочены критерием 6 Фазы 15 — адресатом названным и записанным, а не подразумеваемым. *(Круг 2: Фаза 15 их переписала, но не решила — D-02. Адресата больше нет; вопрос Q3 владельцу.)*

Отметки SIGN-01…03 остаются `Pending`: их ставит закрытие фазы после того, как человек закроет обход. *(Круг 2: отметки поставлены на отозванной посылке — Q1.)*

**Почему `human_needed`, а не `passed` и не `gaps_found`.** Ни одна истина не FAILED, ни один артефакт не MISSING/STUB, ни одна связь не NOT_WIRED, блокеров нет — правило 1 (`gaps_found`) не срабатывает. Срабатывает правило 2: открыты десять пунктов человеку. Это воздержание бэкстопа по критерию 4, девять проверок обхода и 23 помеченных запрета без решения. `passed` с ними недопустим, и посылка, на которой круг 1 канонизировали в `passed`, отозвана самим владельцем.

## Приложение — запись круга 1 дословно

Тело отчёта круга 1 (коммит `65b313bc`, дерево `63f744be`, 2026-09-23T08:15:00Z) перенесено ДОСЛОВНО как запись своего дня, а не как действующий вердикт. Заголовки понижены до жирного текста с меткой «[круг 1]», чтобы разборщики пунктов человеку (`src/uat.cts`) не собрали эти пункты второй раз. Действующие состояния каждого пункта — в разделах круга 2 выше.

Шапка круга 1:

**Verified:** 2026-09-23T08:15:00Z
**Re-verification:** No — initial verification (no prior `14-VERIFICATION.md` existed on disk; confirmed before writing)

**Method.** Goal-backward. The must-haves below are the four ROADMAP Success Criteria (the contract, non-negotiable) merged with the plan-frontmatter truths of 14-01…14-07 that add detail the criteria do not carry. Nothing here is taken from a SUMMARY.md claim: every VERIFIED row is backed either by lines I read in the source tree at HEAD `63f744be`, or by a **named** test I ran myself in this pass (21 rules, three invocations — never the suite). The orchestrator's full-suite measurement (3605 passed at `e9f31fd0`) is treated as an input, not as proof of any criterion: a green suite proves what the suite asserts, and the column «proved by» below names which rule proves what.

**[круг 1] Goal Achievement**

**[круг 1] Observable Truths**

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

**[круг 1] Criterion 3 — read against its chronicles, not literally**

Критерий 3 буквально говорит «`HX-Location` остаётся ТОЛЬКО у `/impersonation/stop`, не пересекающего границу шеллов». Буквальное чтение дало бы ДВА расхождения. Оба названы летописью плана 14-07 ЗАРАНЕЕ и подтверждены мною в источнике:

| Буквальная посылка | Что в дереве | Где названо |
|---|---|---|
| «`/impersonation/stop` не пересекает границу шеллов» | Верно для ДВУХ веток из трёх. Третья — действующего лица нет в базе либо оно заблокировано — уходит `HX-Redirect` на `/login` (`auth.py:744`) со снятием cookie, то есть ЧЕРЕЗ границу | ROADMAP летопись критерия 3 (б); REQUIREMENTS SIGN-03; D-12 |
| «`HX-Location` — ТОЛЬКО у возврата» | Второй отправитель существует: отказ `forbid_when_impersonating` на четырёх шагах восстановления (`auth.py:790, :886, :966, :1058`) → `HtmxRefusal` → `location_response` (`app/main.py:224-231`). Живёт ВНЕ модуля авторизации | ROADMAP летопись критерия 3 (в); D-13 |

Машинное правило `test_hx_location_in_the_auth_module_belongs_to_the_return_only` утверждает равенство `{stop_impersonation}` внутри `app/pages/auth.py` и второго отправителя НЕ ВИДИТ ПО ПОСТРОЕНИЮ — вселенная правила есть модуль авторизации. Эта граница названа в шапке гейта, а не оставлена читателю. Правило и три его двухшаговых отрицательных контроля стоят в дереве (`test_htmx_gates.py:6312-6484`).

**Вывод:** расхождения нет. Критерий 3 засчитан по летописи, и этот абзац стои́т здесь ровно затем, чтобы следующий читатель не открыл ложный изъян.

**[круг 1] Required Artifacts**

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

**[круг 1] Key Link Verification**

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Форма входа (`hx-target=#auth-step`, innerHTML) | `login_submit` | `respond_field_error` → экран входа с эхом внутри якоря | ✓ WIRED | Ломается — ошибка молча не перерисовывает форму либо стирает введённое. Замкнуто прогоном правила 1 |
| `login_submit` / `register_complete` | `redirect_internal` → `set_session_cookie` НА ВОЗВРАЩЁННОМ объекте | `location.href` | ✓ WIRED | `auth.py:273-274`, `:617-618` — cookie ставится на объект, полученный ИЗ выхода, а не на отдельно собранный. Это и есть Landmine фазы; замкнуто правилами 3 и 19 (`…leaves_by_a_full_load_with_the_cookie…`), которые утверждают cookie на ТОМ ЖЕ ответе и открывшийся кабинет |
| `stop_impersonation` | `respond(redirect="/admin")` → `set_session_cookie` | `HX-Location` → `GET /admin` | ✓ WIRED | `auth.py:748-750`; тройное правило (прогон 13) утверждает заголовок, cookie без признака действующего лица И фактически открывшуюся админку |
| Ветка закрытого действующего лица | `redirect_internal("/login")` → `clear_session_cookie` | `HX-Redirect` | ✓ WIRED | `auth.py:744-746`; прогон 15 |
| `forgot_password_reset` | `redirect_internal(..., notice=PASSWORD_RESET_DONE)` | область уведомления шелла ВНЕ якоря | ✓ WIRED | `auth.py:1115`; правило утверждает не только заголовок, но и что текст исхода стои́т ДО якоря (`index(RESET_DONE_TEXT) < index(STEP_ANCHOR)`, `test_auth_transport.py:1759`) — иначе исход стёрся бы первой ошибкой входа |
| `forbid_when_impersonating` | `HtmxRefusal` → `location_response` | `app/main.py:231` | ✓ WIRED | Четыре шага восстановления; прогоны 16-17 |
| Гейт критерия 3 (`_full_load_callers` / `_hx_location_emitters`) | `FULL_LOAD_HANDLERS` / `AUTH_HX_LOCATION_HANDLERS` | равенство, не включение | ✓ WIRED | Прогоны 8-9; у обоих правил есть проверка непустоты вселенной — на пустом замере они бы не позеленели |

**[круг 1] Data-Flow Trace (Level 4)**

| Artifact | Data value | Source | Produces real data | Status |
|---|---|---|---|---|
| `login_step.html:39` | `value=email or ''` | `login_submit` → `_screen_builders(request, "login", error=…, email=email)` (`auth.py:270`) — присланная форма | Да | ✓ FLOWING |
| `register_verify_step.html:54` | `value=code or ''` | `register_verify` → `respond_field_error` с набранным кодом | Да | ✓ FLOWING |
| `forgot_password_verify_step.html:54` | `value=code or ''` | `forgot_password_verify` | Да | ✓ FLOWING |
| `register_complete_step.html:38` | `value=name or ''` | `register_complete` | Да | ✓ FLOWING |
| Скрытое поле `token` (4 экрана) | `value="{{ token }}"` | `create_verification_token(...)` — подписанный JWT, не литерал | Да | ✓ FLOWING |
| Поле пароля (2 экрана) | значения нет | — | **Намеренно пусто (D-04)** | ✓ FLOWING (по решению) — не заглушка: `_screen_builders` ФИЗИЧЕСКИ отказывает передать `password` в контекст |

Ни одного значения, чья цепочка кончается статическим возвратом, литералом или моком.

**[круг 1] Behavioural Spot-Checks**

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

**[круг 1] Probe Execution**

Проб в дереве нет и фазой не объявлено (`find scripts -path '*/tests/probe-*.sh'` → 0; упоминаний `probe-` в планах 14-01…14-07 → 0). Шаг пропущен по отсутствию предмета, а не по невыполнению.

**[круг 1] Requirements Coverage**

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| **SIGN-01** | 14-01, 14-02, 14-03, 14-04, 14-05, 14-06, 14-07 | 9 форм авторизации идут через htmx | ✓ SATISFIED (машинно); рантайм подмены — за человеком | Истина 2; замер 9 форм; правила 5-7. Остаток — наблюдение свопа в браузере (§Human Verification 1-4) |
| **SIGN-02** | 14-01, 14-02, 14-03, 14-04, 14-05, 14-07 | Неверный код или пароль перерисовывает форму с сохранением введённого | ✓ SATISFIED | Истины 1, 5, 6, 7; правила 1-4, 11-12. **Это и есть цель фазы, и она достигнута сервером** |
| **SIGN-03** | 14-01, 14-03, 14-05, 14-06, 14-07 | Успех — `HX-Redirect` через границу шеллов; `HX-Location` — у возврата | ✓ SATISFIED (по летописи, см. §Criterion 3) | Истина 3; правила 8-9, 13-15, 19-21 |

**Отметки НЕ ставлю.** В `.planning/REQUIREMENTS.md` SIGN-01…03 стоят `[ ]` / `Pending` — и остаются: отметку ставит закрытие фазы (`phase.complete`) ПОСЛЕ верификации, а верификация ещё не завершена — критерий 4 у человека. `requirements.ready-ids`, сообщающий их готовыми, авторитетом на отметку не является.

Сирот нет: `.planning/REQUIREMENTS.md:499` отображает на Фазу 14 ровно SIGN-01, SIGN-02, SIGN-03 — и все три заявлены планами.

**[круг 1] Decision Coverage**

15 из 15 отслеживаемых решений `14-CONTEXT.md` (D-01…D-15) опознаны в поставленных артефактах; `not_honored` пуст. Гейт незапирающий; записано для истории дрейфа.

Отдельно перепроверено чтением, что D-15 («фаза меняет транспорт, а не решения») исполнен буквально: набор проверок `purpose`/`verified` в `app/pages/auth.py` ДО фазы (`git show fd69a26a`) и после — **один и тот же**, четыре места в обоих деревьях. Это важно не само по себе: именно оно превращает CR-01, CR-02 и WR-01 ревизии кода из «дефектов фазы» в «дефекты, которые фаза обязана была не трогать».

**[круг 1] Anti-Patterns Found**

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` в файлах фазы | — | **Ноль совпадений.** Гейт долговых меток зелёный |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` | ℹ️ Info | Единственные совпадения — `_PLACEHOLDER = "{}"` в `test_htmx_post_pairs.py:2683` и три его употребления: это сентинел разборщика форматных строк гейта, не заглушка |
| — | — | Отключённые тесты (`skip` / `xfail`) в правилах фазы | — | **Ноль.** Ни одно требование не держится на отключённом правиле |
| — | — | Пустые реализации, статические возвраты, пустые обработчики | — | Ноль. 33 вызова выходов слоя — все с настоящим контекстом; ни одного `return None` / `return []` на пути ответа |

Аудит качества тестов: круговых тестов нет (правила сличают ответ приложения с ЛИТЕРАЛАМИ, выписанными в самом правиле, а не со значениями, порождёнными системой); уровень утверждений — значимый (value-level) и поведенческий, не existence-level; у инвентарных правил есть проверки непустоты вселенной и двухшаговые отрицательные контроли на синтетике.

**[круг 1] Findings Handed Over By Hand (code review and UI review)**

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

**[круг 1] Escalation — решение владельца, которое я не вправе принять за него**

**Предмет.** CR-02 (воспроизведение подтверждённого токена восстановления) предшествует Фазе 14 и её решением D-15 был выведен из правки. Но правило `test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice`, написанное ПЛАНОМ 14-05, теперь **утверждает это воспроизведение зелёным**. Это уже факт Фазы 14: будущая правка, которая начнёт гасить `verified_at`, ПОКРАСНИТ правило этой фазы, и следующий исполнитель встретит красное правило без объяснения, почему оно вообще так написано.

**Вопрос владельцу:** отнести CR-02 к вердикту Фазы 14 (то есть открыть gap и править здесь) или к отдельной последующей работе?

**Моя рекомендация — ОТДЕЛЬНАЯ ПОСЛЕДУЮЩАЯ РАБОТА, с записанной сейчас обязанностью.** Основания, а не удобство:

1. Правка требует изменить РЕШЕНИЕ обработчика (гасить `verified_at`, перестать чеканить свежий токен на отказе) — ровно то, что D-15 этой фазы запретил дословно. Фаза, нарушившая собственное запертое решение в последнем шаге, обесценила бы и остальные четырнадцать.
2. Дефект предшествует фазе: замер `git show fd69a26a` показывает тот же набор проверок. Отнести его к вердикту Фазы 14 значило бы объявить изъяном фазы то, что она обязана была не трогать.
3. Цена отсрочки названа и ограничена: токен живёт 30 минут, и для злоупотребления нужен уже утёкший подтверждённый токен.

**Что должно быть записано ВМЕСТЕ с отсрочкой** (иначе отсрочка — умолчание, а не решение): у правила `test_a_new_password_leaves_for_the_login_by_a_full_load_with_the_notice` должна встать летопись, называющая прямо, что повторное использование ОДНОГО токена в этом правиле есть свойство СЕГОДНЯШНЕГО обработчика, а не утверждаемое требование, и что правку CR-02 полагается сопроводить разведением двух токенов в этом правиле. Летопись — это одна правка в комментарии, и она не меняет ни одного утверждения.

**Того же решения ждёт CR-01** — хотя он уже отсрочен владельцем в `14-CONTEXT.md` §Deferred Ideas, и потому отсрочка у него не молчаливая.

**[круг 1] Deferred Items**

| # | Item | Addressed In | Evidence |
|---|---|---|---|
| 1 | 23 запрета планов 14-01…14-07 стоят `flagged-unverified` / `verification: none` — машинного принуждения не имеет ни один | Phase 15 | Критерий 6 Фазы 15 дословно: «Запреты планов ПЕРЕПИСАНЫ ОДНИМ ПРИБОРОМ, и по каждому принято решение… (а) в дереве есть ОДИН исполняемый прибор переписи, чьё число воспроизводимо, и (б) по каждому запрету стои́т ЛИБО предъявленное машинное принуждение, ЛИБО явное человеческое разрешение» |
| 2 | CR-01 — гард источника запроса на девяти формах авторизации | Owner-recorded deferral (`14-CONTEXT.md` §Deferred Ideas), адресат-фаза не назначен | «Проверка источника запроса на формах входа и регистрации… отдельная работа по безопасности, не транспорт» |
| 3 | `hx-push-url` на формах авторизации | Phase 15 | D-08 этой фазы + критерий 3 Фазы 15 |

**Отсрочки статус не меняют.** Запреты я НЕ засчитываю зелёными: они помечены (`flagged_prohibitions: 23`) и остаются видимыми до Фазы 15. Ни один не поглощён молча вердиктом `passed` — вердикт и не `passed`.

**[круг 1] Human Verification Required**

Семь пунктов. Первые четыре — критерий 4 ROADMAP, ручной ПО ПРОЕКТУ (настоящее письмо, браузер, смена cookie, заголовок вкладки); последние три — то, что ревизия интерфейса прямо оставила глазам.

Артефакт обхода `14-UAT.md` УЖЕ существует в размеченной форме и **остаётся как есть**: `status: testing`, семь пустых таблиц отметок, `result: [pending]`. Я не заполнил ни одной отметки и не тронул ни одного `result` — заполнить их значило бы самозаверение, а не приёмку (D-02; правило `tests/test_planning/test_the_walkthrough_cannot_self_certify.py`). Пункты ниже — маршрутизация к тому файлу, а не второй его экземпляр.

**[круг 1] 1. Полный вход в браузере**

**Test:** Открыть `/login`, ввести неверный пароль, затем верный.
**Expected:** Неверный пароль перерисовывает карточку БЕЗ перезагрузки страницы, введённый email остаётся в поле, заголовок вкладки — «Вход — Broadcaster». Верный пароль уводит в кабинет ПОЛНОЙ загрузкой, cookie `access_token` сменилась.
**Why human:** Рантайм подмены htmx, заголовок вкладки и смена cookie сервером не измеряются — суита не исполняет JS ни строчки.

**[круг 1] 2. Регистрация целиком с настоящим письмом**

**Test:** `/register` → адрес → код из РЕАЛЬНОГО ящика → имя и пароль → кабинет.
**Expected:** Экран кода приезжает без перезагрузки, адресная строка остаётся `/register`, письмо доходит, неверный код оставляет набранное, завершение уводит в кабинет полной загрузкой.
**Why human:** Доставка настоящего письма (D-02 запрещает подставлять код из базы) и рантайм подмены.

**[круг 1] 3. Восстановление пароля целиком**

**Test:** `/forgot-password` → код из письма → новый пароль → `/login` → вход новым паролем.
**Expected:** Плашка «Пароль успешно изменён. Войдите с новым паролем.» видна на `/login`, вход новым паролем проходит.
**Why human:** Доставка письма и визуальное подтверждение плашки шелла.

**[круг 1] 4. Возврат из-под чужой личности**

**Test:** Под чужой личностью нажать «ВЕРНУТЬСЯ В АДМИНА».
**Expected:** Адресная строка `/admin`, заголовок вкладки — админки, полосы имперсонации нет, cookie без признака действующего лица.
**Why human:** Смена cookie личности и заголовок вкладки через границу шеллов в живом браузере (D-12).

**[круг 1] 5. Фокус и объявление после свопа**

**Test:** На экране кода ввести неверный код, затем нажать Tab.
**Expected:** Наблюдаемо, куда попадает фокус и объявляет ли скринридер смену экрана.
**Why human:** Что механизма НЕТ — установлено кодом (ни `autofocus`, ни `tabindex`, ни `aria-live` во всём дереве авторизации). КУДА при этом попадает фокус — только наблюдение.

**[круг 1] 6. Вторая кнопка на экранах кода**

**Test:** Нажать «Отправить код повторно», пока «Подтвердить» в полёте.
**Expected:** Наблюдаемо, выглядит ли вторая кнопка живой при отброшенном запросе.
**Why human:** Отброс доказан правилом; ВИДИМОСТЬ отброса — суждение глазами.

**[круг 1] 7. Карточка на 375px и на десктопе**

**Test:** Пройти все семь экранов на узком и широком экране.
**Expected:** Наблюдаемо, читаема ли иерархия карточки.
**Why human:** Визуальное суждение; дев-сервер во время ревизии интерфейса не отвечал, скриншотов нет.

**[круг 1] Gaps Summary**

**Изъянов, блокирующих достижение цели, не найдено.**

Цель фазы — «неверный код или пароль перестаёт стирать заполненную форму, и выигрыш именно в ОШИБКЕ» — **истинна в дереве, и истинной её делает СЕРВЕР**, а не разметка: код отказа 422 стои́т литералом в `respond_field_error`, эхо едет параметром в шаблон через автоэкранирующее окружение, а путь без JavaScript получает ту же страницу прямо в ответ на POST. Это подтверждено не присутствием символов, а прогоном именованных правил со значимыми утверждениями (`value="…"` в теле, пароль в теле отсутствует, cookie отсутствует) на ОБОИХ транспортах.

Что осталось и почему это не изъяны:

- **Критерий 4 у человека** — так задумано (D-02: настоящее письмо, настоящий браузер). Артефакт обхода готов и не тронут мною.
- **Три предупреждения ревизии интерфейса** касаются СИЛЫ выигрыша (поле не помечено красным, фокус никуда не ведётся, отброшенный клик невидим), а не его наличия. Введённое возвращается на всех семи экранах — это и есть критерий.
- **Две критические находки ревизии кода предшествуют фазе**, и обе перепроверены мною независимо в источнике и в дереве ДО фазы. CR-01 отсрочен владельцем письменно ещё до планирования. CR-02 — вынесен в §Escalation вместе с моей рекомендацией и с тем, что должно быть записано вместе с отсрочкой; молча он не опущен.
- **23 запрета планов без машинного принуждения** отсрочены критерием 6 Фазы 15 — адресатом названным и записанным, а не подразумеваемым.

Отметки SIGN-01…03 остаются `Pending`: их ставит закрытие фазы после того, как человек закроет обход.

Подпись круга 1: _Verified: 2026-09-23T08:15:00Z_

---

_Verified: 2026-10-07T12:31:06Z (круг 2; круг 1 — 2026-09-23T08:15:00Z)_
_Verifier: Claude (gsd-verifier)_
