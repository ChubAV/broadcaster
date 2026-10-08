---
phase: 14-avtorizatsiya-na-htmx
verified: 2026-10-08T06:16:48Z
status: passed
score: 13/13 must-haves verified  # 12 VERIFIED + 1 PASSED (override) — SC4 по подписи владельца
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
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-OWNER-DECISIONS-2026-10-06.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml"
  - ".planning/todos/pending/classify-420-prohibitions-outside-phase-10.md"
  - ".planning/todos/pending/send-code-status-reveals-account.md"
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
  - "tests/test_planning/test_the_walkthrough_cannot_self_certify.py"
  - "tests/test_templates/test_htmx_markup_gates.py"
covered_digest: "v3:sha256:665f42786c4be900bb75753c13582c9201941d9449ea4f0659eee8b6165da3a4"

# Отпечаток КРУГА 5 (2026-10-08) посчитан штатным вербом gsd-core 1.16 `verification.fingerprint`
# и скопирован из его вывода дословно. Передано 45 путей — тот же список, что в кругах 3 и 4. Верб
# добавил 14 PLAN/SUMMARY фазы, итого 59; сверено поимённо скриптом в scratchpad (`lost: set()`,
# дублей 0). Второй вызов, с одноразовым дублем первого пути, дал те же 59 файлов и то же значение
# (I-R4-02 подтверждена повторно). Прежнее значение `v3:sha256:d55cf413…` ошибкой не было: оно
# устарело по правке `14-UAT.md` (feabd7fb — проверки 8 и 9 → `skipped`, абзац решения владельца).
# `14-UAT.md` и `.planning/REQUIREMENTS.md` ОСТАЮТСЯ в списке намеренно: и перевод SIGN-01…03 в
# `Complete`, и любая правка записи обхода (в том числе по Q7) обязаны делать этот вердикт
# устаревшим. Сам `14-VERIFICATION.md` с подписанным блоком `overrides` верб в покрытие не берёт.
# Улики круга вне дерева покрытию не подлежат и названы в теле: журнал сессии оркестратора
# `~/.claude/projects/-source-broadcaster/de9e5bcb-….jsonl` (вопросы 05:57:42Z и 06:02:20Z, ответы
# 06:00:09Z и 06:02:49Z) и журнал контейнера `nginx-broadcaster` за окно 2026-10-07T16:27Z…2026-10-08T06:09Z.
#
# --- Летописи круга 4, круга 3, круга 2 и круга 1 — перенесены ДОСЛОВНО, записи своего дня ---
#
# Отпечаток КРУГА 4 (2026-10-08) посчитан штатным вербом gsd-core 1.16 `verification.fingerprint`
# и скопирован из его вывода дословно. Передано 45 путей (тот же список, что в круге 3: к нему этот
# круг ничего не добавляет и из него ничего не снимает), верб добавил 14 PLAN/SUMMARY фазы, итого 59;
# сверено поимённо скриптом в scratchpad (`lost: set()`). Поручение предупреждало, что верб молча
# теряет ПЕРВЫЙ путь, и велело передать первым одноразовый дубль. Так и сделано, и для замера верб
# вызван второй раз, уже без дубля: оба вызова дали 59 файлов и одно и то же значение. Дефект на
# gsd-core 1.16 не воспроизводится (I-R4-02). `14-UAT.md` ОСТАЁТСЯ в списке намеренно. Прежнее
# значение `v3:sha256:8b0c2b00…` ошибкой не было — оно устарело по правке `14-UAT.md` (f447c5ed).
# Улики круга вне дерева покрытию не подлежат и названы в теле: журнал сессии оркестратора
# `~/.claude/projects/-source-broadcaster/de9e5bcb-….jsonl` и журналы контейнеров стенда
# (`web-broadcaster`, `nginx-broadcaster`) за окно 2026-10-07T16:27Z…2026-10-08T05:46Z.
#
# --- Летописи круга 3, круга 2 и круга 1 — перенесены ДОСЛОВНО, записи своего дня ---
#
# Отпечаток КРУГА 3 (2026-10-07T15:58Z) посчитан штатным вербом gsd-core 1.16
# `verification.fingerprint` и скопирован из его вывода дословно. Ни один путь не потерян:
# передано 45, верб добавил 14 PLAN/SUMMARY фазы, итого 59; сверено поимённо скриптом в
# scratchpad (`lost: set()`). Список = список круга 2 (55) плюс четыре файла, на которые
# этот круг ОПИРАЕТ вердикт: оба todo (`classify-420-prohibitions-outside-phase-10.md` —
# адресат пункта 10 и отсрочки 1; `send-code-status-reveals-account.md` — адресат починки
# по Q4), `15-OWNER-DECISIONS-2026-10-06.md` (запись решения владельца об адресате) и
# `tests/test_planning/test_the_walkthrough_cannot_self_certify.py` (граница правила
# самозаверения, на которой стоит W-R3-01). `14-UAT.md` ОСТАЁТСЯ в списке намеренно: любая
# правка записи обхода обязана сделать этот вердикт устаревшим. Две улики круга вне дерева
# покрытию не подлежат и названы в теле: журналы сессий оркестратора
# (`~/.claude/projects/-source-broadcaster/{e571cfb6,5237445f}-….jsonl`) и журналы
# контейнеров стенда (`web-broadcaster`, `nginx-broadcaster`). Прежнее значение
# `v3:sha256:617245a7…` ошибкой не было — устарело по правкам `14-UAT.md` (f63a3c49) и
# `14-SECURITY.md` (9cce13ea).
#
# --- Летописи круга 2 и круга 1 — перенесены ДОСЛОВНО, записи своего дня ---
#
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
backstop_abstentions: 0  # круг 5 — SC4 PASSED (override); воздержание снято РЕШЕНИЕМ владельца, не наблюдением
overrides_applied: 1  # круг 5 — override 1 накрывает истину SC4; override 2 истину не накрывает (см. ниже)
# круги 1–4, запись своего дня дословно: `backstop_abstentions: 1  # SC4 — ⚠️ insufficient_spec; круг 1 → круг 2: открыто (обход не проводился)`, `overrides_applied: 0`
decision_coverage:  # перемерено 2026-10-07 `check.decision-coverage-verify` — тот же итог, что в круге 1
  honored: 15
  total: 15
  not_honored: []
# круг 3: `backstop_abstentions` — по-прежнему 1, SC4 открыт: запись обхода 2026-10-07 наблюдения
# не несёт (W-R3-01). `decision_coverage` перемерено в круге 3 (`check.decision-coverage-verify`
# с явным путём к 14-CONTEXT.md) — 15/15, `not_honored: []`.
# круг 4: `backstop_abstentions` — по-прежнему 1, SC4 открыт. Запись обхода 2026-10-08 (f447c5ed)
# несёт заявление владельца «я все проверил» без единого наблюдённого признака. По правилу D-02 и
# по тексту самого файла такая отметка закрытием не считается; засчитать её может только решение
# владельца (Q6). `decision_coverage` перемерено в круге 4: 15/15, `not_honored: []`.
# круг 5: `backstop_abstentions` 1 → 0. SC4 теперь PASSED (override): владелец `chubav` подписал
# запись `overrides` (ответ 2026-10-08T06:02:49Z, запись 06:03:27Z; Q6, ветвь (б)). Это РЕШЕНИЕ, а не
# наблюдение. В отметках обхода по-прежнему нет ни одного наблюдённого признака, а стенд этой машины
# за окно 2026-10-07T16:27Z…2026-10-08T06:09Z не видел ни одного запроса обхода. `overrides_applied: 1`:
# override 1 накрывает истину SC4 (совпадение текста 100%). Override 2 не накрывает ни одну из 13
# истин — его предмет проверки 8 и 9 и находки UI WARNING 2/3. Он применён как подписанное основание
# `resolution` пунктов человеку 8 и 9 и в счёт не входит. `decision_coverage` перемерено в круге 5:
# 15/15, `not_honored: []`. Правило закрытия D-02 владелец ослабил только для Фазы 14. Гейт покрытия
# решений меряет поставленные артефакты, поэтому его итог от этого не меняется.

overrides:
  # Подписано владельцем 2026-10-08T06:03:27Z в `/gsd-verify-work 14` (ответ на Q6, вариант (б) верификатора круга 4).
  # Решение владельца, а НЕ наблюдение. Стенд этой машины запросов обхода в окне 2026-10-07T16:27Z…2026-10-08T05:46Z не видел (круг 4).
  - must_have: "SC4. Вход, регистрация, подтверждение почты и восстановление пароля проходят в браузере целиком"
    reason: "Заявление владельца «я все проверил» по проверкам 1–7 `14-UAT.md` без наблюдённых признаков (f447c5ed). Правило D-02 («отметка без наблюдённого признака закрытием не считается») для Фазы 14 ослаблено владельцем явным решением. Пункты human_verification 1–7 закрываются этим решением, а не наблюдением"
    accepted_by: "chubav"
    accepted_at: "2026-10-08T06:03:27Z"
    covers: "SC4 и human_verification 1–7 (проверки обхода 1–7). НЕ покрывает проверки 8 и 9"
  - must_have: "UAT проверки 8 и 9 — фокус и объявление после подмены; вторая кнопка экрана кода в полёте (14-UI-REVIEW WARNING 2 и 3)"
    reason: "Владелец отказался от наблюдения проверок 8 и 9; значения не записаны. Находки 14-UI-REVIEW WARNING 2 и WARNING 3 остаются ОТКРЫТЫМИ и не наблюдёнными; в `14-UAT.md` у проверок `result: skipped` с причиной"
    accepted_by: "chubav"
    accepted_at: "2026-10-08T06:03:27Z"
    covers: "human_verification 8 и 9 — отказ от наблюдения; находки UI WARNING 2/3 не закрыты"
re_verification:
  round: 5
  previous_status: human_needed
  previous_score: 12/13
  previous_round_record:  # круг 4 — его блок `re_verification` ДОСЛОВНО (сдвинут на два пробела) под реквизитами круга 4
    verified: 2026-10-08T05:50:52Z
    report_commit: 97b35cfc
    tree: f447c5ed
    covered_digest: "v3:sha256:d55cf413d341bbd4509e051af8e6d1948064ca1882f4f5fe9cf6b9349565e7ba"
    covered_files_count: 59
    backup: "/tmp/claude-1000/-source-broadcaster/de9e5bcb-8120-4312-a510-6c1b1de2dbd7/scratchpad/14-VERIFICATION.pre-round5.md"
    backup_note: "копия файла на bae74ab7, то есть отчёт круга 4 плюс внесённые оркестратором поля Q6 и блок `overrides`; отчёт круга 4 сам по себе — 97b35cfc"
    round: 4
    previous_status: human_needed
    previous_score: 12/13
    previous_round_record:  # круг 3 — его блок `re_verification` ДОСЛОВНО (сдвинут на два пробела) под реквизитами круга 3
      verified: 2026-10-07T15:58:55Z
      report_commit: 93e1d4d2
      tree: 9cce13ea
      covered_digest: "v3:sha256:8b0c2b00eda5eefb7c450e7cc50a2be8ac7d12a4d5c73859281ea7ff2de61147"
      covered_files_count: 59
      backup: "/tmp/claude-1000/-source-broadcaster/de9e5bcb-8120-4312-a510-6c1b1de2dbd7/scratchpad/14-VERIFICATION.pre-round4.md"
      round: 3
      previous_status: human_needed
      previous_score: 12/13
      previous_round_record:  # круг 2 — его блок `re_verification` ДОСЛОВНО (сдвинут на два пробела) под реквизитами круга 2
        verified: 2026-10-07T12:31:06Z
        report_commit: cbbcc5e9
        tree: ec41dcef
        covered_digest: "v3:sha256:617245a760d52dcb8a469e52e4dfd94ab805b2e1369c6d7503538eb74b3d466f"
        covered_files_count: 55
        backup: "/tmp/claude-1000/-source-broadcaster/e571cfb6-41a3-4d6e-a625-61385c368bcd/scratchpad/14-VERIFICATION.pre-round3.md"
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
      why_stale: "покрытые файлы изменились после круга 2: `14-UAT.md` (f63a3c49 — обход «пройден заново», шапка `complete`, девять отметок заполнены) и `14-SECURITY.md` (9cce13ea — перепринятие R-14-02). Круг 2 сам внёс `14-UAT.md` в покрытие, чтобы заполнение отметок сделало вердикт устаревшим"
      what_changed:
        - "С `cbbcc5e9` ровно два коммита, оба только под `.planning/`: `git diff --name-only cbbcc5e9..HEAD` — 14-SECURITY.md, 14-UAT.md, todos/pending/send-code-status-reveals-account.md"
        - "Вне `.planning/` с `feaa701f` не изменилось НИЧЕГО: `git diff --name-only feaa701f..HEAD -- . ':!.planning'` — 0 строк. Продуктовый код и правила фазы — те же, что в круге 2"
        - "14-UAT.md: `status: human_needed` → `testing` → `complete`; девять `result: pass` → `[pending]` (с `history:`) → `pass`; девять таблиц отметок заполнены одной шаблонной строкой; `## Summary` — `passed: 9`"
        - "14-SECURITY.md: основание строки реестра T-14-09/T-14-31/T-14-32 и строки R-14-02 исправлено (оракул 422/200), абзац-летопись; уровень, диспозиция, статус, `threats_open: 0` — без изменений"
        - "REQUIREMENTS.md (в `cbbcc5e9`, после записи отчёта круга 2): SIGN-01…03 → `[ ]` / `Pending`, летопись `:64` — исполнение Q1"
      premise_checked: "обход 2026-10-07 — запись проверена по первичным уликам (журнал сессии, журналы стенда, форма отметок): наблюдения не несёт → пункты 1–9 `still_required`; `passed` не выводится (W-R3-01, Q5)"
      gaps_closed: []  # блока `gaps` не было ни в одном круге
      gaps_remaining: []
      regressions: []  # кода не меняли; 27 именованных правил — PASS
      carried_items_closed:
        - "human_verification 10 / Q3 / отсрочка 1 (адресат) — адресат записан владельцем 2026-10-06 (457b354f), подтверждён ответом на Q3; круг 2 его не нашёл"
        - "W-R2-02 / Q4 — R-14-02 перепринят с исправленным основанием (9cce13ea)"
        - "W-R2-03 / Q1 — SIGN-01…03 возвращены в `Pending` (cbbcc5e9); правило записей зелено"
    why_stale: "покрытый `14-UAT.md` изменён после круга 3 (f447c5ed): обход перезапущен, затем снова объявлен `complete`. Круг 2 внёс файл обхода в покрытие именно для того, чтобы любая правка записи обхода делала вердикт устаревшим"
    what_changed:
      - "С `93e1d4d2` ровно один коммит — `f447c5ed` (2026-10-08T05:43:56Z): `git diff --name-only 93e1d4d2..HEAD` — только `14-UAT.md`, +42/−20"
      - "Вне `.planning/` с `ec41dcef` не изменилось НИЧЕГО: `git diff --name-only ec41dcef..HEAD -- . ':!.planning'` — 0 строк"
      - "14-UAT.md: абзац 2026-10-07T16:28:14Z отзывает `complete` от f63a3c49 (решение владельца «Restart walkthrough») и цитирует прежний шаблон отметок; база шага 7.2 `master` → `fd69a26a`; девять `result: pass` с `reported:` — словами владельца дословно; девять строк отметок; шапка `complete`; `## Summary` — `passed: 9`"
      - "Каждая строка отметки называет то, чего в ней нет: «дата наблюдения не названа», «не названы» (браузер / ОС), «Признаков шагов N.1–N.k владелец не назвал; оркестратор их не дописывал». У проверок 8 и 9 то же сказано и о ЗНАЧЕНИЯХ"
    premise_checked: "запись обхода 2026-10-08 сверена с первичными уликами: журналом сессии de9e5bcb (вопросы оркестратора и ответы владельца с метками времени) и журналами стенда за окно 16:27Z–05:46Z. Шаблона больше нет, отметки — слова владельца дословно, и о пропусках запись говорит честно. Но наблюдённого признака в ней нет ни одного, а просьбу назвать признаки владелец трижды оставил без ответа. → пункты 1–9 `still_required`, засчитать заявление закрытием может только решение владельца (W-R4-01, W-R4-02, Q6)"
    gaps_closed: []  # блока `gaps` не было ни в одном круге
    gaps_remaining: []
    regressions: []  # кода не меняли; 27 именованных правил — PASS (16.96 с)
    carried_items_closed:
      - "W-R3-03 — база шага 7.2 исправлена в записи (`14-UAT.md:302`: «с деревом до фазы `fd69a26a`… не `master`»); `fd69a26a` — родитель первого коммита плана 14-01 `ca66794f` (замерено). Сверялись ли промежутки с этой базой, запись не говорит (см. пункт 7)"
      - "W-R3-01 — в ФОРМЕ: шаблона оркестратора больше нет, вариант «Chrome + Firefox / Linux» не подставлен, отметка несёт только слова владельца. По существу находка перешла в W-R4-01"
  why_stale: "покрытый `14-UAT.md` изменён после круга 4 (feabd7fb): у проверок 8 и 9 `pass` → `skipped` с причиной «отказ владельца», `## Summary` 9/0 → 7/2, абзац решения владельца 2026-10-08T06:03:27Z над `## Current Test`"
  what_changed:
    - "С `97b35cfc` ровно четыре коммита, все только под `.planning/`: dce39090, d886e4c4, feabd7fb, bae74ab7; `git diff --name-only 97b35cfc..HEAD` — `14-UAT.md`, `14-VERIFICATION.md`"
    - "Вне `.planning/` с `ec41dcef` не изменилось НИЧЕГО: `git diff --name-only ec41dcef..HEAD -- . ':!.planning'` — 0 строк"
    - "14-VERIFICATION.md (dce39090, d886e4c4, bae74ab7 — правки оркестратора по ответам владельца): поля Q6 `owner_answer`, `owner_answer_followup`, `owner_decision_final`; блок `overrides` из двух записей (accepted_by chubav, accepted_at 2026-10-08T06:03:27Z, у каждой `covers`). Вердикт, счёт и прочие поля круга 4 не тронуты: `git diff 97b35cfc..HEAD` по файлу — +16 строк, удалённых 0"
    - "14-UAT.md (feabd7fb): проверки 8 и 9 — `result: skipped`, `reason` с отказом владельца, строка `history:` о прежнем `pass` (W-R4-02); строки отметок 8 и 9 не правились; проверки 1–7 — `pass` со словами владельца, как в f447c5ed; `updated: 2026-10-08T06:03:56.887Z`"
  premise_checked: "решение владельца сверено с первичной записью, журналом сессии de9e5bcb. 05:57:42Z вопрос Q6 с тремя вариантами → 06:00:09Z «Назову признаки». 06:00:23Z просьба о признаках проверки 1 → 06:01:16Z «все мы закончили», 06:01:56Z «закрой фазу 14». 06:02:20Z вопрос «Override». Его текст называет, что запишется под именем владельца: «проверки 1–7 засчитаны по вашему заявлению без признаков, и правило D-02 для фазы 14 ослаблено вами». Вариант «Подписываю, 8–9 — отказ» называет последствие: «Находки UI WARNING 2 и 3 остаются открытыми и не наблюдёнными». 06:02:49Z — ответ «Подписываю, 8–9 — отказ». Запись `overrides` совпадает с вопросом, на который дан ответ, и не шире его. Решение — не наблюдение: признаков в отметках по-прежнему нет, и стенд запросов обхода не видел (замер продлён до 06:09Z)"
  gaps_closed: []  # блока `gaps` не было ни в одном круге
  gaps_remaining: []
  regressions: []  # кода не меняли; 27 именованных правил — PASS (17.65 с)
  carried_items_closed:
    - "Q6 — решён владельцем: ветвь (б), подписанный `overrides` (ответ 06:02:49Z, запись 06:03:27Z). SC4 → PASSED (override); пункты человеку 1–7 → discharged по override 1"
    - "W-R4-01 — закрыта РЕШЕНИЕМ владельца. Правило D-02 «отметка без наблюдённого признака закрытием не считается» он для Фазы 14 ослабил явно, поэтому шапка `complete` поверх заявлений больше не противоречит правилу, действующему для фазы. Наблюдённых признаков по-прежнему нет — это записано"
    - "W-R4-02 — закрыта: проверки 8 и 9 переписаны из `pass` в `skipped` с причиной (feabd7fb), прежний `pass` сохранён строкой `history:`. Пункты человеку 8 и 9 → discharged по override 2 (отказ от наблюдения). Находки UI WARNING 2 и 3 — ОТКРЫТЫ и не наблюдены"

deferred:
  - truth: "23 `must_haves.prohibitions` across plans 14-01…14-07 stand at `status: flagged-unverified`, `verification: none` — no machine enforcement reads them"
    addressed_in: "Phase 15"
    evidence: "Phase 15 success criterion 6: «Запреты планов ПЕРЕПИСАНЫ ОДНИМ ПРИБОРОМ, и по каждому принято решение… Критерий закрыт, когда (а) в дереве есть ОДИН исполняемый прибор переписи… и (б) по каждому запрету его перечня стои́т ЛИБО предъявленное машинное принуждение, ЛИБО явное человеческое разрешение»"
    round_2_status: open
    round_2_addressed_in: "НЕ НАЗНАЧЕН — Фаза 15 закрыла только половину (а)"
    round_2_evidence: "(а) прибор есть: `scripts/prohibitions_census.py`, реестр `15-prohibitions-registry.yaml` несёт все 23 строки 14-01#0…14-07#2; `tests/test_planning/test_plan_prohibitions_census.py` — 109 passed (круг 2). (б) решения НЕТ: все 23 строки — `class: unclassified`, `disposition: unresolved`; D-02 Фазы 15 ограничил область решений Фазой 10 (321), фазы 07–09 и 11–14 «прибор перечисляет и явно помечает неразобранными»; 15-CONTEXT §Deferred: «Адресат не назначен — требует решения владельца при планировании следующей вехи». Отсрочка на Фазу 15 тем самым НЕ исполнена — маршрутизировано владельцу (human_verification 10, owner_questions Q3)"
    round_3_status: open
    round_3_addressed_in: "бэклог следующей вехи (после v2.1) — todo `.planning/todos/pending/classify-420-prohibitions-outside-phase-10.md`, решение владельца `chubav` 2026-10-06 (коммит 457b354f; `15-OWNER-DECISIONS-2026-10-06.md:25`), подтверждено ответом на Q3 2026-10-07T15:46:14Z"
    round_3_evidence: "перемерено в круге 3: 23 строки реестра 14-01#0…14-07#2 — все `unclassified` / `unresolved` и входят в 420 строк todo (07 — 31, 08 — 24, 09 — 153, 11 — 68, 12 — 22, 13 — 8, 14 — 23 = 329; 15 — 91). Запись круга 2 «адресат НЕ НАЗНАЧЕН» была ошибкой круга 2: todo существовал с 2026-10-06 (I-R3-01). Отсрочка остаётся ОТКРЫТОЙ (решения по строкам нет, принуждения нет), но адресат у неё есть"
    round_4_status: open
    round_4_evidence: "без изменений с круга 3: реестр Фазы 15 и todo `classify-420…` не правились (`git diff --name-only 93e1d4d2..HEAD` — только 14-UAT.md). Адресат есть, решений по 23 строкам нет; ни один запрет не засчитан зелёным"
    round_5_status: open
    round_5_evidence: "без изменений с круга 4: реестр Фазы 15 и todo `classify-420…` не правились (`git diff --name-only 97b35cfc..HEAD` — только 14-UAT.md и 14-VERIFICATION.md). Подписанный `overrides` запретов не касается; ни один запрет не засчитан зелёным, и вердикт `passed` их не поглощает — они остаются отсрочкой с записанным адресатом"
  - truth: "Cross-origin (`is_same_origin`) guard absent on nine of ten auth POST handlers — CR-01"
    addressed_in: "Owner-recorded deferral, 14-CONTEXT.md §Deferred Ideas (not a numbered later phase)"
    evidence: "14-CONTEXT.md §Deferred Ideas: «Проверка источника запроса на формах входа и регистрации. Сегодня у девяти форм `is_same_origin` нет, защита — только `SameSite=Lax`. Подделка входа… — отдельная работа по безопасности, не транспорт.» Also named out-of-boundary at 14-CONTEXT.md:32."
    round_2_status: open
    round_2_evidence: "перемерено 2026-10-07: `app/pages/auth.py` — 10 `@router.post`, `is_same_origin` вызывается ОДИН раз (`:691`, возврат). Риск принят владельцем как T-14-08 / R-14-01 (14-SECURITY.md; аудит: «CR-01 — это T-14-08 в своей общей форме… остаётся действительным»). Адресат-фаза по-прежнему не назначен"
    round_3_status: open
    round_3_evidence: "перемерено в круге 3: 10 `@router.post`, `is_same_origin` — один вызов (`auth.py:691`); код не менялся. Риск T-14-08 / R-14-01 в силе; с 2026-10-07 14-SECURITY.md прямо называет CR-01 условием достижимости оракула R-14-02 со стороннего сайта. Адресат-фаза по-прежнему не назначен"
    round_4_status: open
    round_4_evidence: "код не менялся (diff вне `.planning/` с `ec41dcef` пуст): в `app/pages/auth.py` по-прежнему 10 `@router.post` и один вызов `is_same_origin` (`:691`). Риск T-14-08 / R-14-01 в силе, адресат-фаза не назначен"
    round_5_status: open
    round_5_evidence: "код не менялся; перемерено в круге 5: в `app/pages/auth.py` 10 `@router.post` и один вызов `is_same_origin` (`:691`). Риск T-14-08 / R-14-01 в силе, адресат-фаза не назначен"
  - truth: "`hx-push-url` на формах авторизации — решение Фазы 15 (D-08 этой фазы)"
    addressed_in: "Phase 15"
    evidence: "D-08 этой фазы + критерий 3 Фазы 15 («По КАЖДОЙ форме принято и записано решение о `hx-push-url` по конвенции трёх случаев…»)"
    round_2_status: closed
    round_2_evidence: "15-FORM-DECISIONS.md строки 35–44 — решение по всем десяти формам (шесть экранов кода — второй случай, атрибута нет; вход и возврат — третий; завершение регистрации и новый пароль — третий, ветвь владельца `case-three-server-header`, chubav, 2026-09-24); `grep hx-push-url` по app/templates/auth/, auth_base.html, form_wrapper.html — 0; правила `test_push_url_decisions_cover_every_post_handler`, `…_every_write_place_resolves_to_a_decided_handler`, `…_zero_in_markup_is_a_decision_not_a_gap`, `…_dual_branch_handlers_are_case_three` — PASS (круг 2)"
    round_3_status: closed
    round_3_evidence: "без изменений с круга 2: разметка авторизации и 15-FORM-DECISIONS.md не менялись"
    round_4_status: closed
    round_4_evidence: "без изменений: разметка авторизации и 15-FORM-DECISIONS.md не менялись"
    round_5_status: closed
    round_5_evidence: "без изменений: разметка авторизации и 15-FORM-DECISIONS.md не менялись"

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
    round_3_status: closed  # без изменений; изъян CR-02 в коде остаётся по решению владельца (`verified_at` — только `auth.py:408, :443, :916, :950`, перемерено)
    round_4_status: closed  # без изменений; код не менялся, `verified_at` — те же четыре строки
    round_5_status: closed  # без изменений; код не менялся, `verified_at` — те же четыре строки (`auth.py:408, :443, :916, :950`, перемерено)

flagged_prohibitions: 23 # all `verification: none` / `status: flagged-unverified`; never counted green — deferred to Phase 15 SC6
# круг 2: всё ещё 23, открыто. Фаза 15 их ПЕРЕПИСАЛА (реестр, 23 строки), но НЕ РЕШИЛА (D-02 —
# область решений только Фаза 10). Адресат не назначен → human_verification 10, owner_questions Q3.
# круг 3: всё ещё 23, открыто, но С АДРЕСАТОМ — бэклог следующей вехи (todo classify-420…, решение
# владельца 2026-10-06, подтверждено ответом на Q3). Ни один запрет не засчитан зелёным.
# круг 4: всё ещё 23, открыто, адресат тот же (бэклог следующей вехи). Реестр и todo не правились.
# круг 5: всё ещё 23, открыто, адресат тот же. Подписанный `overrides` запретов не касается. Вердикт
# `passed` их НЕ поглощает молча: они названы здесь, в отсрочке 1 и в пункте человеку 10 (адресат
# записан владельцем). Итог круга читается как «passed с 23 помеченными запретами».

human_verification:
  # Сверка с 14-UAT.md (9 проверок) — один пункт на проверку; пункт 10 — решение владельца по
  # запретам. Круг 1 → круг 2: 7 пунктов → 10; все 7 прежних открыты (таблицы отметок пусты),
  # проверка 6 UAT (менеджер паролей) в списке круга 1 отсутствовала — добавлена.
  # Круг 3: у каждого пункта ровно одно из двух состояний — `state: still_required` либо
  # `state: discharged` с названной уликой (`resolution:` — поле, по которому машинерия gsd-core
  # считает пункт закрытым). Итог: 1–9 still_required, 10 discharged. Общее основание пунктов 1–9 —
  # §«Обход 2026-10-07» в теле и W-R3-01.
  # Круг 4: `state_evidence` у пунктов 1–10 — улика круга 3, перенесена ДОСЛОВНО. Улика круга 4 —
  # в соседнем поле `round_4_state_evidence`. Итог круга 4 тот же: 1–9 still_required, 10
  # discharged. Изменилось основание пунктов 1–9. Записи шаблона больше нет; есть заявление
  # владельца без признаков, которое по правилу D-02 закрытием не считается, а ослабить правило
  # может только владелец (Q6). Общее основание — §«Обход 2026-10-07…08» в теле, W-R4-01 и W-R4-02.
  # Круг 5: пункты 1–9 переведены в `state: discharged` с полем `resolution:`. Оба основания
  # ПОДПИСАНЫ владельцем (`overrides`, ответ 2026-10-08T06:02:49Z, запись 06:03:27Z): пункты 1–7
  # закрыты override 1 (заявление без признаков, D-02 ослаблено для Фазы 14), пункты 8–9 — override 2
  # (отказ от наблюдения). Закрытие — РЕШЕНИЕ, а не наблюдение. Прежнее состояние сохранено полем
  # `round_4_state: still_required`; `state_evidence` и `round_4_state_evidence` перенесены дословно;
  # улика круга 5 — в поле `round_5_state_evidence`. Пункт 10 — без изменений. Открытых пунктов 0.
  - test: "UAT проверка 1 (круг 1 — п.1). Полный вход в браузере: открыть `/login`, ввести неверный пароль, затем верный"
    expected: "Неверный пароль перерисовывает карточку БЕЗ перезагрузки, email остаётся в поле, заголовок вкладки — «Вход — Broadcaster»; верный пароль уводит в кабинет ПОЛНОЙ загрузкой, cookie `access_token` сменилась"
    why_human: "Рантайм подмены htmx, заголовок вкладки и смена cookie сервером не измеряются — суита не исполняет JS ни строчки (ROADMAP критерий 4, D-02)"
    state: discharged
    state_evidence: "Отметка проверки 1 (f63a3c49) — шаблон оркестратора «наблюдены признаки шагов 1.1–1.5 так, как они записаны…; подтверждено словом «pass»»; своих слов наблюдения нет. Девять «pass» даны за 94 с (15:38:47–15:40:21Z), через 48 с после выбора «Пройти обход заново» (15:37:59Z); заявления о более раннем обходе нет. Боевой стенд за 2026-10-07: ни одного `POST /login` с 422 (шаг 1.1 его порождает обязательно), один `POST /login` 204 в 13:54:46Z без предшествующего отказа"
    round_4_state_evidence: "Отметка проверки 1 (f447c5ed) — слова владельца дословно «закрой все по тесту 1 я все проверил» (2026-10-08T05:40:33Z); в той же строке записано, что дата наблюдения и браузер не названы, а признаков шагов 1.1–1.5 и значения `access_token` владелец не назвал. Это ответ на прямую просьбу 2026-10-07T16:29:44Z назвать стенд, браузер, признаки 1.1–1.3 и первые символы `access_token` до и после. Стенд этой машины за окно 16:27Z–05:46Z: ни одного `POST /login` — ни 422 (шаг 1.1), ни 204 (шаг 1.4)"
    round_4_state: still_required
    resolution: "Решение владельца, не наблюдение: override 1 (chubav, 2026-10-08T06:03:27Z) засчитал закрытием заявление «закрой все по тесту 1 я все проверил»; правило D-02 для Фазы 14 ослаблено владельцем явно. Наблюдённых признаков (1.1–1.5, значение `access_token`) в отметке нет"
    round_5_state_evidence: "Ответ «Подписываю, 8–9 — отказ» (журнал de9e5bcb, 06:02:49Z) на вопрос 06:02:20Z, текст которого называл последствие для проверок 1–7 дословно. Отметка проверки 1 не менялась с f447c5ed. Стенд за окно 2026-10-07T16:27Z…2026-10-08T06:09Z: 0 `POST /login` любого статуса"
  - test: "UAT проверка 2 (круг 1 — п.2, первая половина). Регистрация: `/register` → новый адрес → экран кода; затем короткий и годный пароль на завершении"
    expected: "Экран кода приезжает без перезагрузки, адресная строка остаётся `/register`, вкладка — «Подтверждение email — Broadcaster»; короткий пароль оставляет имя; завершение уводит в кабинет полной загрузкой с пробным сроком"
    why_human: "Рантайм подмены, адресная строка и заголовок вкладки — только в браузере"
    state: discharged
    state_evidence: "Отметка проверки 2 — тот же шаблон, своих слов нет (см. п.1). Боевой стенд за 2026-10-07: 27 `POST /register/send-code` — все с устаревших клиентов (Chrome 43/45, Android 4.4, Windows 8.1) и полностраничным ответом; ни одного `POST /register/complete` (шаг 2.4)"
    round_4_state_evidence: "Отметка проверки 2 — «закрой все по тесту 2 я все проверил» (05:41:09Z); признаков 2.1–2.4 нет, стенд и браузер не названы. Стенд за окно: ни одного `POST /register/complete` (шаг 2.4). 33 `POST /register/send-code` за окно пришли с устаревших клиентов полностраничным ответом — это сторонний трафик I-R4-01, а не подмена htmx"
    round_4_state: still_required
    resolution: "Решение владельца, не наблюдение: override 1 (chubav, 2026-10-08T06:03:27Z) засчитал закрытием заявление «закрой все по тесту 2 я все проверил»; D-02 для Фазы 14 ослаблено владельцем явно. Признаков 2.1–2.4 в отметке нет"
    round_5_state_evidence: "Ответ «Подписываю, 8–9 — отказ» (06:02:49Z). Отметка не менялась с f447c5ed. Стенд за окно: 0 `POST /register/complete`; 34 `POST /register/send-code` — сторонний трафик I-R4-01 (полностраничные ответы устаревшим клиентам), не обход"
  - test: "UAT проверка 3 (круг 1 — п.2, вторая половина). Подтверждение почты НАСТОЯЩИМ письмом: код из реального ящика, неверный код, повтор, F5 на шаге"
    expected: "Письмо доходит; неверный код — «Неверный код. Осталось попыток: N» и набранный код в поле; повтор присылает новое письмо, обе формы живы; F5 возвращает к началу пути (D-08)"
    why_human: "Доставка настоящего письма (D-02: код из базы подставлять запрещено; правило останова) и рантайм подмены"
    state: discharged
    state_evidence: "Отметка проверки 3 — тот же шаблон. Проверка требует двух настоящих писем (3.1, 3.3) — ответ «pass» на неё дан через 7 с после ответа на проверку 2. Боевой стенд за 2026-10-07: ни одного `POST /register/verify` и `/register/resend-code`. Правило останова D-02 не позволяет закрыть пункт иначе, чем наблюдением доставки"
    round_4_state_evidence: "Отметка проверки 3 — «закрой все по тесту 3 я все проверил» (05:41:34Z); признаков 3.1–3.5 нет. Предмет проверки — доставка ДВУХ настоящих писем, наблюдаемая только наблюдателем (правило останова D-02). Стенд за окно: ни одного `POST /register/verify` и `/register/resend-code`"
    round_4_state: still_required
    resolution: "Решение владельца, не наблюдение: override 1 (chubav, 2026-10-08T06:03:27Z) засчитал закрытием заявление «закрой все по тесту 3 я все проверил»; D-02, включая его правило останова о настоящем письме, для Фазы 14 ослаблено владельцем явно. Доставка двух настоящих писем не наблюдена и не названа"
    round_5_state_evidence: "Ответ «Подписываю, 8–9 — отказ» (06:02:49Z). Отметка не менялась с f447c5ed. Стенд за окно: 0 `POST /register/verify` и `/register/resend-code`"
  - test: "UAT проверка 4 (круг 1 — п.3). Восстановление пароля целиком: `/forgot-password` → код из письма → новый пароль → `/login` с плашкой → вход новым паролем"
    expected: "Плашка «Пароль успешно изменён. Войдите с новым паролем.» видна на `/login` и переживает ошибку входа старым паролем; вход новым паролем проходит"
    why_human: "Доставка письма и визуальное подтверждение плашки области уведомления шелла"
    state: discharged
    state_evidence: "Отметка проверки 4 — тот же шаблон; письмо восстановления. Боевой стенд за 2026-10-07: ни одного запроса к `/forgot-password/*` (ни `send-code`, ни `verify`, ни `reset`)"
    round_4_state_evidence: "Отметка проверки 4 — «закрой все по тесту 4 я все проверил» (05:41:47Z); признаков 4.1–4.5 нет. Стенд за окно: ни одного запроса к `/forgot-password/*`"
    round_4_state: still_required
    resolution: "Решение владельца, не наблюдение: override 1 (chubav, 2026-10-08T06:03:27Z) засчитал закрытием заявление «закрой все по тесту 4 я все проверил»; D-02 для Фазы 14 ослаблено владельцем явно. Признаков 4.1–4.5 в отметке нет"
    round_5_state_evidence: "Ответ «Подписываю, 8–9 — отказ» (06:02:49Z). Отметка не менялась с f447c5ed. Стенд за окно: 0 запросов к `/forgot-password/*`"
  - test: "UAT проверка 5 (круг 1 — п.4). Возврат из-под чужой личности: «ВЕРНУТЬСЯ В АДМИНА» из полосы"
    expected: "Адресная строка `/admin`, заголовок вкладки — админки, полосы имперсонации нет, cookie без признака действующего лица"
    why_human: "Смена cookie личности и заголовок вкладки через границу шеллов в живом браузере (D-12)"
    state: discharged
    state_evidence: "Отметка проверки 5 — тот же шаблон. Боевой стенд за 2026-10-07: ни одного `POST /impersonation/stop`; `/admin` — только 404 сканеров"
    round_4_state_evidence: "Отметка проверки 5 — «закрой все по тесту 5 я все проверил» (05:42:02Z); признаков 5.1–5.5 нет. Стенд за окно: ни одного `POST /impersonation/stop`; запросы к `/admin…` — один 404 сканера"
    round_4_state: still_required
    resolution: "Решение владельца, не наблюдение: override 1 (chubav, 2026-10-08T06:03:27Z) засчитал закрытием заявление «закрой все по тесту 5 я все проверил»; D-02 для Фазы 14 ослаблено владельцем явно. Признаков 5.1–5.5 в отметке нет"
    round_5_state_evidence: "Ответ «Подписываю, 8–9 — отказ» (06:02:49Z). Отметка не менялась с f447c5ed. Стенд за окно: 0 `POST /impersonation/stop`"
  - test: "UAT проверка 6 (в круге 1 НЕ было — добавлено при сверке). Менеджер паролей в Chrome и Firefox на чистом профиле, база сравнения — путь без JS"
    expected: "Пять наблюдений RESEARCH Находки 7: предложение сохранить пароль после верного входа и завершения регистрации, обновить — после нового пароля, нет предложения на 422; регрессия относительно пути без JS выносится владельцу, а не глушится"
    why_human: "Эвристики сохранения пароля — свойство браузера (A1–A3), сервером не измеряются ни одним утверждением"
    state: discharged
    state_evidence: "Отметка проверки 6 — тот же шаблон. Проверка — пять наблюдений в ДВУХ браузерах на чистых профилях плюс база без JS (вход, завершение регистрации, новый пароль — новые ящики в каждом браузере); ответ «pass» дан через 6 с после ответа на проверку 5. Наблюдения по каждому браузеру не названы"
    round_4_state_evidence: "Отметка проверки 6 — «закрой все по тесту 6 я все проверил» (05:42:24Z); признаков 6.1–6.5 нет. Не названы ни браузеры (проверка требует двух, на чистых профилях), ни итог базы без JS — а от него зависит, есть ли регрессия, которую надо вынести владельцу"
    round_4_state: still_required
    resolution: "Решение владельца, не наблюдение: override 1 (chubav, 2026-10-08T06:03:27Z) засчитал закрытием заявление «закрой все по тесту 6 я все проверил»; D-02 для Фазы 14 ослаблено владельцем явно. Браузеры и итог базы без JS не названы, поэтому вопрос о регрессии менеджера паролей владельцу не вынесен — владелец закрыл его сам"
    round_5_state_evidence: "Ответ «Подписываю, 8–9 — отказ» (06:02:49Z). Отметка не менялась с f447c5ed. Стенд за окно: 0 `POST /login`, 0 `POST /register/complete`, 0 запросов к `/forgot-password/*` — ни одного из трёх путей, где менеджер паролей предлагает сохранение"
  - test: "UAT проверка 7 (круг 1 — п.7). Карточка авторизации на 375px и на десктопе, во всех семи экранах"
    expected: "Подзаголовок сразу под брендом, промежутки как до фазы, индикатор у кнопки; читаема ли иерархия (все тексты тела 13px, заголовочного элемента нет ни на одном экране)"
    why_human: "Визуальное суждение; дев-сервер во время ревизии не отвечал, скриншотов нет (14-UI-REVIEW Pillars 2/4/5, A4)"
    state: discharged
    state_evidence: "Отметка проверки 7 — тот же шаблон. Сверх общего основания: шаг 7.2 «сравнить промежутки с веткой `master`» сегодня сравнивает дерево С САМИМ СОБОЙ — код фазы в `master` (5b3b91c5 — предок `origin/master`), признак «промежутки как до фазы» этим шагом больше не наблюдаем; база сравнения — дерево до фазы `fd69a26a` (W-R3-03)"
    round_4_state_evidence: "Отметка проверки 7 — «закрой все по тесту 7 я все проверил» (05:42:39Z); признаков 7.1–7.4 нет. База шага 7.2 в записи исправлена на `fd69a26a` (W-R3-03 закрыта в записи), но сверялись ли с ней промежутки и на каких ширинах — не сказано"
    round_4_state: still_required
    resolution: "Решение владельца, не наблюдение: override 1 (chubav, 2026-10-08T06:03:27Z) засчитал закрытием заявление «закрой все по тесту 7 я все проверил»; D-02 для Фазы 14 ослаблено владельцем явно. Сверка промежутков с `fd69a26a` и ширины не названы"
    round_5_state_evidence: "Ответ «Подписываю, 8–9 — отказ» (06:02:49Z). Отметка не менялась с f447c5ed. Визуальная проверка обязательного следа в журнале стенда не оставляет; против неё улики нет"
  - test: "UAT проверка 8 (круг 1 — п.5). Клавиатурный проход по экрану кода после 422: нажать Tab сразу после неверного кода; то же со скринридером и на экране входа"
    expected: "Наблюдаемо, куда попадает фокус после `hx-swap=\"innerHTML\"` в `#auth-step` и объявляется ли смена экрана"
    why_human: "В дереве шаблонов авторизации нет ни `autofocus`, ни `tabindex`, ни `aria-live` (машинно подтверждено и в круге 2 — 0 совпадений); КУДА при этом попадает фокус и что слышит скринридер — наблюдение, не грепа (14-UI-REVIEW WARNING 2)"
    state: discharged
    state_evidence: "Отметка проверки 8 — тот же шаблон. Сверх общего основания: проверка спрашивает ЗНАЧЕНИЕ («куда встаёт фокус», «объявляется ли смена экрана», шаг 8.3 — «записать, какой»), а «наблюдены так, как записаны» значения не несёт; скринридер не назван. Даже подтверждённый обход этот пункт без значений не закроет (W-R3-02)"
    round_4_state_evidence: "Отметка проверки 8 — «я все проверил закрой тест 8» (05:43:14Z); запись прямо говорит, что значений 8.1–8.3 (куда встал фокус, что объявил скринридер, какой скринридер) владелец не назвал. За 22 с до ответа, в 05:42:52Z, оркестратор предупредил: «я все проверил» этот пункт «не закроет даже формально», и без значений тест будет записан пропущенным. Записан `pass` «по вашему решению». W-R3-02 в силе. Предмет проверки — ЗНАЧЕНИЕ, поэтому пункт не закрывается и ветвью (б) Q6: закрыть его могут только значения или явный отказ владельца от проверки (W-R4-02)"
    round_4_state: still_required
    resolution: "Решение владельца, не наблюдение: override 2 (chubav, 2026-10-08T06:03:27Z) — отказ от наблюдения проверки 8. Значение (куда встаёт фокус после Tab, что объявляет скринридер и какой) не записано. Находка 14-UI-REVIEW WARNING 2 остаётся ОТКРЫТОЙ и ненаблюдённой; в `14-UAT.md` — `result: skipped` с причиной (feabd7fb)"
    round_5_state_evidence: "Ответ «Подписываю, 8–9 — отказ» (06:02:49Z) на вопрос, где вариант описан так: «От наблюдения 8 и 9 отказываетесь, и это записывается. Находки UI WARNING 2 и 3 остаются открытыми и не наблюдёнными». Механизма по-прежнему нет: `autofocus`/`tabindex`/`aria-live` в шаблонах авторизации — 0 (перемерено). Предикат `phase uat-passed 14` читает этот `skipped` как блокер — W-R5-01, Q7"
  - test: "UAT проверка 9 (круг 1 — п.6). На экране кода нажать «Отправить код повторно», пока «Подтвердить» в полёте"
    expected: "Наблюдаемо, выглядит ли вторая кнопка живой при отброшенном `hx-sync` запросе; действие не теряется"
    why_human: "`hx-disabled-elt=\"find button[type=submit]\"` гасит кнопку ТОЛЬКО своей формы; запрос отбрасывается `hx-sync` (доказано `test_both_code_forms_ride_the_anchor_and_drop_a_second_request`, PASS в круге 2), но видимость этого — суждение глазами (14-UI-REVIEW WARNING 3)"
    state: discharged
    state_evidence: "Отметка проверки 9 — тот же шаблон. Сверх общего основания: шаг 9.1 спрашивает ЗНАЧЕНИЕ («выглядит ли вторая кнопка живой, появляется ли у неё индикатор») — ответа в записи нет (W-R3-02). Шаг 9.2 (отброс второго запроса) машинно доказан правилом `test_both_code_forms_ride_the_anchor_and_drop_a_second_request` — PASS в круге 3"
    round_4_state_evidence: "Отметка проверки 9 — «я все проверил закрой тест 9» (05:43:35Z); значения 9.1 (выглядела ли вторая кнопка живой, был ли у неё индикатор) нет, хотя вопрос оркестратора называл его прямо. W-R3-02 в силе. Шаг 9.2 машинно доказан правилом `test_both_code_forms_ride_the_anchor_and_drop_a_second_request` — PASS в круге 4. Закрыть пункт могут только значение 9.1 или явный отказ владельца от проверки (W-R4-02)"
    round_4_state: still_required
    resolution: "Решение владельца, не наблюдение: override 2 (chubav, 2026-10-08T06:03:27Z) — отказ от наблюдения проверки 9. Значение 9.1 (выглядит ли вторая кнопка живой, есть ли у неё индикатор) не записано. Находка 14-UI-REVIEW WARNING 3 остаётся ОТКРЫТОЙ и ненаблюдённой; в `14-UAT.md` — `result: skipped` с причиной (feabd7fb)"
    round_5_state_evidence: "Ответ «Подписываю, 8–9 — отказ» (06:02:49Z). Шаг 9.2 (отброс второго запроса) машинно доказан правилом `test_both_code_forms_ride_the_anchor_and_drop_a_second_request` — PASS в круге 5. Предикат `phase uat-passed 14` читает этот `skipped` как блокер — W-R5-01, Q7"
  - test: "НЕ проверка обхода — решение владельца. 23 запрета планов 14-01…14-07 (`flagged-unverified`, `verification: none`): назначить адресата и/или принять по каждому решение (принуждение правилом либо явное разрешение)"
    expected: "У каждой из 23 строк реестра `15-prohibitions-registry.yaml` (14-01#0…14-07#2) — диспозиция, поставленная по ответу владельца, либо записанный адресат следующей вехи"
    why_human: "Запреты уровня суждения (ADR-550): помеченный запрет не поглощается вердиктом молча; Фаза 15 их переписала, но решать запретила себе сама (D-02). Назначить адресата может только владелец"
    state: discharged
    resolution: "Адресат записан владельцем: `.planning/todos/pending/classify-420-prohibitions-outside-phase-10.md` (`addressee: бэклог следующей вехи (после v2.1)`, создан 2026-10-06, коммит 457b354f, запись решения `15-OWNER-DECISIONS-2026-10-06.md:25`); владелец подтвердил его ответом на Q3 2026-10-07T15:46:14Z. Ожидание пункта «…либо записанный адресат следующей вехи» исполнено второй ветвью"
    state_evidence: "Замер круга 3: 23 строки реестра фазы 14 (14-01#0…14-07#2) — все `unclassified` / `unresolved`, все входят в 420 строк todo. Реестр не правился (D-02 Фазы 15). Запреты остаются непринуждёнными — `flagged_prohibitions: 23`, отсрочка 1 открыта; закрыт пункт «назначить адресата», а не сами запреты"
    round_4_state_evidence: "Без изменений: адресат тот же, todo `classify-420…` и реестр не правились. Пункт остаётся закрытым по `resolution`"
    round_5_state_evidence: "Без изменений: адресат тот же, todo `classify-420…` и реестр не правились. Пункт закрыт по `resolution` с круга 3"

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
    owner_answer: "«Вернуть в Pending (Рекомендуется)»"
    answered_at: 2026-10-07T15:28:22Z
    answered_where: "сессия оркестратора 5237445f, вопрос после круга 2"
    executed: "cbbcc5e9 — `.planning/REQUIREMENTS.md:60-62` `[ ]`, `:160-162` `Pending`, летопись отметок `:64`; текст требований не тронут"
    round_3_check: "Подтверждено чтением. Правило `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` зелено при вердикте круга 3 (§Self-check). Вторая половина рекомендации — обход до `/gsd-complete-milestone` — по существу НЕ исполнена: см. Q2, Q5, W-R3-01. Верификатор REQUIREMENTS.md не правил; вердикт не `passed`, поэтому отметки и не просятся"
    round_4_check: "SIGN-01…03 по-прежнему `[ ]` / `Pending` (`REQUIREMENTS.md:60-62`, `:160-162`). Вердикт круга 4 — `human_needed`, поэтому правило записей зелено (§Self-check). Отметки не просятся"
    round_5_check: "Вердикт круга 5 — `passed`. SIGN-01…03 стоят `[ ]` / `Pending` (`REQUIREMENTS.md:60-62`, `:160-162`). Правило `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` одностороннее: `Pending` при `passed` его не краснит (§Self-check), а перевод в `[x]` / `Complete` оно теперь допускает. Верификатор REQUIREMENTS.md не правил. Отметки ставит закрытие фазы (`phase.complete`), а закрытие стоит за предикатом обхода — Q7. `REQUIREMENTS.md` входит в покрытие, поэтому перевод отметок сделает этот вердикт устаревшим; пересчитывать — штатным вербом"
  - id: Q2
    question: "В `14-UAT.md` раздел `## Tests` несёт `result: pass` / `reported: \"pass\"` у всех девяти проверок, `## Summary` — `passed: 9`, `Current Test` — `[testing complete]`; абзац отзыва в шапке того же файла говорит «Обход Фазы 14 глазами НЕ ПРОВОДИЛСЯ» и эти поля оставил нетронутыми намеренно. Оставить их или вернуть в `[pending]`?"
    verifier_recommendation: "Вернуть девять `result` в `[pending]`, `passed: 9` → `pending: 9` и `Current Test` в нетерминальное — правкой ЧЕЛОВЕКА или по его прямому указанию: это снятие неподтверждённой записи, а не заполнение. Правило самозаверения считает только таблицы отметок и сегодня зелено, поэтому само расхождение не поймает. Верификатор файл не правил"
    decision_owner: chubav
    owner_answer: "«Сброшу при обходе (Рекомендуется)» (15:28:22Z); затем в `/gsd-verify-work 14` — «Пройти обход заново (Recommended)» и предусловия «Всё готово» (15:37:59Z), девять ответов «pass» (15:38:47–15:40:21Z; восьмой набран «pas»), отметки «pass = признаки из таблицы» (15:39:07Z), «Chrome+Firefox / Linux, chubav» (15:40:48Z)"
    answered_at: 2026-10-07T15:28:22Z
    answered_where: "сессии оркестратора 5237445f и e571cfb6 (журналы `~/.claude/projects/-source-broadcaster/*.jsonl`, прочитаны только метки времени и тексты ответов)"
    executed: "f63a3c49 — девять `result` возвращены в `[pending]` (прежнее значение — строкой `history:`), затем снова `pass`; девять таблиц отметок заполнены одной шаблонной строкой оркестратора; шапка `complete`, `## Summary` — `passed: 9`, абзац 2026-10-07 о начале обхода заново"
    round_3_check: "СНЯТИЕ неподтверждённой записи исполнено (строки `history:` на месте). ЗАПОЛНЕНИЕ наблюдения не несёт: 94 с на девять проверок с двумя настоящими письмами, двумя браузерами, скринридером и 375px; заявления о более раннем обходе нет; стенд не видел запросов обхода. → W-R3-01, Q5; human_verification 1–9 — still_required. Файл обхода верификатор не правил"
  - id: Q3
    question: "23 запрета Фазы 14 переписаны прибором Фазы 15, но не решены (D-02 Фазы 15). Кто адресат?"
    verifier_recommendation: "Назначить адресатом раунд решений по запретам следующей вехи тем же прибором и тем же порядком D-03/D-04 Фазы 15 (классы → решения). Входная улика для него — в теле, §Deferred Items, п.1: у 10 из 23 в дереве уже есть правила, на которых можно ЗАМЕРИТЬ принуждение; остальные 13 — процессные и уровня суждения (D-15, «число ставится прогоном», «текст критерия не переписан»)"
    decision_owner: chubav
    owner_answer: "«Да, это ответ (Recommended)» — todo `classify-420-prohibitions-outside-phase-10` засчитан ответом"
    answered_at: 2026-10-07T15:46:14Z
    answered_where: "`/gsd-execute-phase 14`, сессия e571cfb6"
    executed: "Новых записей не потребовалось: адресат записан 2026-10-06 (457b354f; `15-OWNER-DECISIONS-2026-10-06.md:25`). Реестр не правился — строки вне Фазы 10 полей решения не несут (D-02 Фазы 15)"
    round_3_check: "Перемерено: 23 строки 14-xx ⊂ 420 `unclassified`/`unresolved`. Круг 2 этот todo пропустил (I-R3-01). human_verification 10 — discharged; отсрочка 1 — открыта с адресатом"
  - id: Q4
    question: "R-14-02 (14-SECURITY.md) принят с основанием «тексты переехали дословно (D-15) — фаза различимость ответов не создавала». Замер круга 2 это основание опровергает в части КОДОВ ответа (WR-03): до фазы оба исхода отправки кода отвечали 200, после — 422/200. Перепринять с исправленным основанием или направить на починку?"
    verifier_recommendation: "Перепринять явно с исправленным основанием (фаза СОЗДАЛА однобитовый оракул по строке статуса на `/forgot-password/send-code` и `/register/send-code`, и при CR-01 он достижим со стороннего сайта) и приписать починку к той же отсроченной работе по перечислению адресов (14-CONTEXT §Deferred). Вердикт фазы это не меняет: 422 на ошибке — само предметное решение D-03"
    decision_owner: chubav
    owner_answer: "«Перепринять, исправив основание (Recommended)»"
    answered_at: 2026-10-07T15:46:14Z
    answered_where: "`/gsd-execute-phase 14`, сессия e571cfb6"
    executed: "9cce13ea — 14-SECURITY.md: основание строки реестра угроз T-14-09/T-14-31/T-14-32 и строки R-14-02 (chubav, 2026-10-07) называет созданный фазой однобитовый оракул 422/200; абзац-летопись с прежней формулировкой и датой 2026-09-22; новый todo `send-code-status-reveals-account` (addressee — отложенная работа по перечислению адресов). Уровень medium, `accept`, `closed (accepted)`, `threats_open: 0` — без изменений"
    round_3_check: "Подтверждено чтением и замером: `auth.py:311` (регистрация, занятый адрес → 422), `:818` (восстановление, неизвестный → 422); 200 на известном — `:841` (ветка ограничения частоты) и `:876` (основной выход). Запись называет только `:841` — I-R3-02, суть верна. Правила, закрепляющие оба 422, — PASS в круге 3"
  - id: Q5
    question: "Запись обхода 2026-10-07 (f63a3c49): девять «pass» даны за 94 с, через 48 с после выбора «Пройти обход заново»; отметки — шаблон «наблюдены признаки шагов… так, как они записаны», собственных слов наблюдения нет; боевой стенд за день не видел ни одного запроса, который проверки 1, 3, 4, 5 порождают обязательно. Проводился ли обход глазами — где (стенд с рабочим SMTP), когда и кем?"
    verifier_recommendation: "Если обход проводился раньше (до `/gsd-verify-work 14`, на другом стенде) — сказать это СВОИМИ СЛОВАМИ на прямой вопрос, как в Фазе 13 («все было на живом стенде…»), назвав стенд и день; для проверок 8 и 9 вписать наблюдённые значения (куда встал фокус и что сказал скринридер; выглядела ли вторая кнопка живой), шаг 7.2 сверить с деревом до фазы (`fd69a26a`), а не с `master`. Если не проводился — вернуть шапку `14-UAT.md` в нетерминальное состояние (строки `history:` сохранить) и пройти обход. После любого из двух — перепроверить фазу. Верификатор файл обхода не правил и `passed` на этой записи не выносит"
    decision_owner: chubav
    owner_answer: "«Restart walkthrough (Recommended)» (2026-10-07T16:27:41Z; описание варианта: «Each mark gets only what you describe in your own words: what you saw, on which setup, and the value for checks 8/9»). Через 66 с — «pass» на проверку 1 (16:28:47Z); оркестратор отметку не поставил и попросил признаки (16:28:53Z, по-русски — 16:29:44Z). Дальше 13 ч 11 мин молчания, затем девять ответов за 3 мин 2 с (2026-10-08T05:40:33Z–05:43:35Z): «закрой все по тесту N я все проверил» (1–7), «я все проверил закрой тест N» (8, 9). На вопрос 05:44:12Z владелец выбрал «Запустить сейчас», а не «Сначала дописать признаки»"
    answered_at: 2026-10-08T05:43:35Z
    answered_where: "`/gsd-verify-work 14`, сессия de9e5bcb (журнал `~/.claude/projects/-source-broadcaster/de9e5bcb-….jsonl`; прочитаны метки времени, ответы владельца и вопросы, на которые они даны)"
    executed: "f447c5ed — `14-UAT.md`: отзыв `complete` от f63a3c49 (абзац 16:28:14Z), база 7.2 → `fd69a26a`, девять `result: pass` со словами владельца в `reported:`, девять строк отметок со словами владельца дословно и с прямой записью о том, что не названо; шапка `complete`"
    round_4_check: "Q5 спрашивал, проводился ли обход, где, когда и кем. Ответ: «я все проверил» — обход заявлен, наблюдатель chubav. Где и когда — не сказано, хотя спрошено прямо и трижды. Вторая ветвь рекомендации (вернуть шапку в нетерминальное состояние и пройти обход) начата перезапуском, но закончена заявлением, а не обходом с признаками. Временного возражения круга 3 больше нет: окно в 13 ч допускает настоящий обход. Возражение стенда ослабло: обход мог идти на другом стенде (на стенде этой машины за окно запросов обхода 0). Осталось одно: в записи нет ни одного наблюдённого признака. По D-02 такая запись закрытием не считается → W-R4-01, W-R4-02, Q6. Файл обхода верификатор не правил"
  - id: Q6
    question: "Девять отметок `14-UAT.md` (f447c5ed) несут ваши слова «я все проверил». В них же прямо записано, что признаков шагов, стенда, браузера, дня наблюдения, а для проверок 8 и 9 — значений вы не назвали, хотя оркестратор просил их трижды (16:28:53Z, 16:29:44Z, 05:44:12Z). Правило D-02 и сам файл под каждой таблицей говорят: «отметка без наблюдённого признака закрытием не считается». Засчитать ли ваше заявление закрытием проверок 1–7 вопреки этому правилу? И что делать с проверками 8 и 9, чей предмет — значение, а не подтверждение?"
    verifier_recommendation: "(а) РЕКОМЕНДУЮ: назвать признаки своими словами, по строке на проверку — стенд и день, браузер, что увидели. Для 1.5 — первые символы `access_token` до и после; для 8 — куда встал фокус, что сказал скринридер и какой это скринридер; для 9.1 — выглядела ли вторая кнопка живой. Тогда следующий круг закроет пункты 1–9 и SC4 без оговорок. (б) Если признаков не будет, но обход вы действительно прошли, — подпишите это явным решением: запись `overrides` с `accepted_by`/`accepted_at` и основанием «заявление владельца без признаков; D-02 для Фазы 14 ослаблено владельцем». Тогда SC4 и пункты 1–7 пройдут как PASSED (override), с записью, что стенд этой машины запросов обхода не видел. Для 8 и 9 заявление значения не создаёт: либо значения, либо явный отказ от проверки. При отказе находки UI WARNING 2 и 3 остаются открытыми и ненаблюдёнными, и это тоже записывается. (в) Если обход не проводился — вернуть шапку `14-UAT.md` в нетерминальное состояние, строки `history:` сохранить. На нынешней записи верификатор `passed` не выносит и файл обхода не правит"
    decision_owner: chubav
    raised_in: "круг 4, 2026-10-08"
    owner_answer: "(а) «Назову признаки» — выбор владельца `chubav` в `/gsd-verify-work 14`, 2026-10-08T06:00:17Z; признаки собираются по строке на проверку и вписываются в отметки `14-UAT.md` его словами"
    owner_decision_final: "2026-10-08T06:03:27Z — владелец подписал вариант (б): override для SC4/проверок 1–7, отказ от наблюдения 8 и 9 (см. `overrides`)"
    owner_answer_followup: "2026-10-08T06:01:23Z — на просьбу назвать признаки проверки 1 владелец ответил «все мы закончили»; признаки не названы, сессия завершена. Q6 остаётся открытым: пункты 1–9 still_required до признаков или явного решения (б)/(в)"
    round_5_check: "Решение подтверждено первичной записью: вопрос 06:02:20Z → ответ 06:02:49.661Z «Подписываю, 8–9 — отказ» (журнал de9e5bcb). `accepted_at` записи (06:03:27Z) на 38 с позже ответа; это время записи, а не ответа (I-R5-01). Решение предшествует записи, суть не меняется. Поле `owner_answer_followup` с фразой «Q6 остаётся открытым» — запись своего дня (06:01:23Z); её сменило `owner_decision_final`, поле перенесено дословно. Override применён: SC4 → PASSED (override), пункты 1–9 → discharged. Q6 закрыт"
  - id: Q7
    question: "Ваш отказ от проверок 8 и 9 записан в `14-UAT.md` как `result: skipped` с причиной «Отказ владельца…». Штатный предикат закрытия фазы (`gsd-tools phase uat-passed 14`; его читает `/gsd-verify-work` перед переводом фазы в ROADMAP и STATE) такой пропуск не пропускает. Не блокирует он только `skipped`, чья причина начинается с `Deferred follow-up:`, — то есть отложенную работу, записанную в разделе `## Deferred Follow-Ups`. Простой отказ для предиката — непройденная проверка. Поэтому даже при вердикте `passed` фаза штатно не закроется: блокеры «test 8 (skipped)», «test 9 (skipped)». Как записать проверки 8 и 9?"
    verifier_recommendation: "(а) РЕКОМЕНДУЮ, если находки UI WARNING 2 и 3 когда-нибудь должны быть разобраны: записать отказ как отложенную работу. У проверок 8 и 9 — причина с префиксом `Deferred follow-up:` и вашими словами; раздел `## Deferred Follow-Ups` с двумя записями (`test`, `idea`, `deferred_at`); по желанию — перенос в бэклог ROADMAP `999.x` штатным шагом `/gsd-verify-work`. Смысл решения при этом меняется: «смотреть не буду» становится «посмотрим позже», и у обеих находок появляется адресат. Поэтому это ваше решение, а не правка формы. (б) Назвать два значения сейчас: куда встаёт фокус после Tab и что говорит скринридер (и какой); выглядит ли вторая кнопка живой. Тогда 8 и 9 → `pass` со значениями, а находки подтверждаются или снимаются. (в) Оставить отказ как есть. Вердикт останется `passed`, но фаза штатным путём не закроется; закрывать её в обход предиката я не рекомендую. Любая ветвь, которая правит `14-UAT.md`, по замыслу делает этот вердикт устаревшим. Кругу 6 останется только сверить правку"
    decision_owner: chubav
    raised_in: "круг 5, 2026-10-08"
    owner_answer: "(а) «Отложить на потом» — выбор владельца `chubav` в `/gsd-verify-work 14`, 2026-10-08T06:19:28Z. Исполнено: у проверок 8 и 9 `14-UAT.md` причина `Deferred follow-up: …` + раздел `## Deferred Follow-Ups`; бэклог ROADMAP — Phase 999.1 (тест 8, UI WARNING 2) и 999.2 (тест 9, UI WARNING 3)"
---

# Phase 14: Авторизация на htmx — Verification Report

**Phase Goal:** неверный код или пароль перестаёт стирать заполненную форму — заявленный выигрыш вехи именно в ОШИБКЕ, а не в успехе
**Verified:** 2026-10-08T06:16:48Z (круг 5; круг 4 — 2026-10-08T05:50:52Z; круг 3 — 2026-10-07T15:58:55Z; круг 2 — 2026-10-07T12:31:06Z; круг 1 — 2026-09-23T08:15:00Z)
**Status:** passed — 13/13, из них **1 PASSED (override)**: SC4 закрыт подписанным РЕШЕНИЕМ владельца, а не наблюдением
**Re-verification:** Да — КРУГ 5. HEAD `bae74ab7`. Повод: вердикт круга 4 прочитался `stale`, потому что изменился покрытый `14-UAT.md`. Блока `gaps` не было ни в одном круге, поэтому по букве шага 0 это снова прогон в полном объёме: все 13 истин перепроверены прогоном, а не перенесены. Тело отчёта круга 4 перенесено целиком в §Приложение — запись круга 4, отчёты кругов 3, 2 и 1 — в свои приложения, как и прежде. Все четыре — дословно.

**Что изменилось с круга 4 (замерено, а не взято из поручения).**
- `git log 97b35cfc..HEAD` — четыре коммита: `dce39090`, `d886e4c4`, `feabd7fb`, `bae74ab7` (2026-10-08T06:00:18Z…06:03:57Z).
- `git diff --name-only 97b35cfc..HEAD` — только `14-UAT.md` (+15/−7) и `14-VERIFICATION.md` (+16/−0: поля Q6 и блок `overrides`).
- `git diff --name-only ec41dcef..HEAD -- . ':!.planning'` — **0 строк**: ни продуктовый код, ни правила с круга 2 не менялись.

**Чего не наследую и что проверил сам.** Слова поручения «владелец выбрал „Подписываю, 8–9 — отказ“» сверены с первичной записью — журналом сессии de9e5bcb. Я прочитал оба вопроса оркестратора целиком, со всеми вариантами и их описаниями, и ответы владельца с метками времени. Без текста вопроса не понять, под чем именно стоит подпись (§Решение владельца 2026-10-08). Блок `overrides` перенесён побайтово; его `covers` не расширены и не сужены.

**Method.** Goal-backward; must-haves — те же четыре критерия ROADMAP и истины фронтматтера семи планов. Улики круга:
- **Прогон.** 27 именованных правил одним вызовом `pytest` — **27 passed, 357 deselected за 17.65 с** (те же 25 правил круга 2 и два правила записи Q4). После записи отчёта — `tests/test_planning` целиком (§Self-check).
- **Чтение дерева.** Номера строк выписаны в таблицах.
- **Штатные вербы gsd-core 1.16.** `phase uat-passed 14`, `verification.status`, `check.decision-coverage-verify`, `verification.fingerprint`, `audit-uat`; разбор правила предиката — `bin/lib/uat-predicate.cjs:59-69`, `:570-590`.
- **Две первичные улики вне дерева, только чтение.**
  - Журнал сессии оркестратора de9e5bcb за 05:56Z–06:05Z: вопросы, варианты, ответы.
  - Журнал контейнера `nginx-broadcaster` за окно 2026-10-07T16:27Z…2026-10-08T06:09Z (окно круга 4, продлённое до этого круга). Сняты только агрегированные счёты маршрутов авторизации; IP-адреса не печатались, ничего не запускалось и не менялось.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence (круг 5) |
|---|-------|--------|----------|
| 1 | **SC1 / SIGN-02.** Неверный код или пароль перерисовывает форму С СОХРАНЕНИЕМ введённого: 422 + эхо в `value=`; свойство создаёт СЕРВЕР | ✓ VERIFIED | Код не менялся (diff вне `.planning/` с `ec41dcef` пуст). ПРОГОН круга 5: правила 1–4, 22 (трасер входа), 24 — PASS |
| 2 | **SC2 / SIGN-01.** Все 9 форм авторизации идут через `hx-post` и остаются рабочими без JS | ✓ VERIFIED | Прогон: правила 5–7, 10 — PASS; `form_wrapper(` в `app/templates/auth/` — 9 (перемерено) |
| 3 | **SC3 / SIGN-03.** Успех авторизации уходит `HX-Redirect` через границу шеллов; `HX-Location` — по летописи | ✓ VERIFIED | По летописи — разбор §Criterion 3 круга 2 в силе, источник не менялся. Прогон: правила 8–9, 13–15, 19–21 — PASS |
| 4 | **SC4.** Вход, регистрация, подтверждение почты и восстановление пароля проходят в браузере целиком | **PASSED (override)** | **Решение, а не наблюдение.** Кодом критерий не проверяется (`verification: backstop` у всех семи планов), и наблюдением он не доказан: в отметках обхода нет ни одного наблюдённого признака, а стенд этой машины за окно 2026-10-07T16:27Z…2026-10-08T06:09Z не видел ни одного запроса обхода. Override: «Заявление владельца «я все проверил» по проверкам 1–7 `14-UAT.md` без наблюдённых признаков (f447c5ed). Правило D-02 … для Фазы 14 ослаблено владельцем явным решением» — accepted by `chubav` on 2026-10-08T06:03:27Z (ответ 06:02:49Z). Совпадение `must_have` с истиной — 100%. Улики против поведения нет; машинная половина зелена (27/27) |
| 5 | Враждебный ввод возвращается в `value=` ТОЛЬКО экранированным, на обоих транспортах | ✓ VERIFIED | Прогон: правила 2 и 24 — PASS |
| 6 | Пароль не возвращается НИКОГДА — ни в `value=`, ни в теле, ни в контексте шаблона | ✓ VERIFIED | Прогон: правила 1, 11 — PASS |
| 7 | Отказ 422 не несёт cookie сессии ни на одном транспорте; заблокированный с ВЕРНЫМ паролем получает 422 с `BLOCKED_LOGIN_ERROR` | ✓ VERIFIED | Прогон: правила 1, 12 — PASS |
| 8 | Смена экрана — 200 на обоих транспортах; подписанный токен шага едет ТОЛЬКО скрытым полем | ✓ VERIFIED | Прогон: правила 3, 4, 23 — PASS |
| 9 | Возврат из-под чужой личности: три ветки, cookie перезаписана НА ЭТОМ ЖЕ ответе, следующий `GET /admin` отдаёт админку | ✓ VERIFIED (behaviour-dependent — доказано прогоном, не присутствием) | Прогон круга 5: правила 13–15 — PASS |
| 10 | Восстановление пароля под чужой личностью остаётся запрещённым на ВСЕХ четырёх шагах, на обоих транспортах | ✓ VERIFIED (behaviour-dependent) | Прогон: правила 16–17 — PASS |
| 11 | Счётчик отставания вехи — ИМЕНОВАННЫЙ НОЛЬ, доказанный НЕ ВАКУУМНЫМ | ✓ VERIFIED | Прогон: правило 10 — PASS |
| 12 | Реестр `AUTH_SCREENS` накрывает ВСЕ семь страниц второго шелла; заголовок фрагмента и заголовок страницы сличаются | ✓ VERIFIED | Прогон: правила 18 и 25 — PASS |
| 13 | Записи фазы приведены в объявленную форму: летописи критериев 2 и 3, строки Research, SIGN-03, рамки вехи; окно 63 переведено ЗАМЕРОМ; артефакт обхода размечен | ✓ VERIFIED | Истина плана 14-07 — о ПОСТАВЛЕННОЙ им разметке. Летописи не менялись. Артефакт обхода и сегодня несёт `checks_declared: 9`, 9 разделов, 9 таблиц, предусловия П-1…П-7 и правило останова; шаг 7.2 — база `fd69a26a` |

**Score:** 13/13 truths verified — 12 ✓ VERIFIED и 1 PASSED (override); 0 present-but-behaviour-unverified; воздержаний бэкстопа 0 (было 1 — снято решением владельца). Круг 4 → круг 5: двенадцать истин — те же статусы, тем же прогоном. Изменилась ровно одна, SC4: из ⚠️ `insufficient_spec` в PASSED (override). Причина — подпись владельца, нового наблюдения нет.

**Override 2 в счёт не входит.** Его `must_have` («UAT проверки 8 и 9 — фокус и объявление после подмены; вторая кнопка экрана кода в полёте (14-UI-REVIEW WARNING 2 и 3)») не совпадает ни с одной из 13 истин даже наполовину. Его предмет — пункты человеку 8 и 9 и находки UI-ревизии. Поэтому он применён как подписанное основание `resolution` этих двух пунктов, а не как истина. `overrides_applied: 1`.

### Решение владельца 2026-10-08 — что оно закрывает и чего не закрывает

Это главный предмет круга: от него зависит, вправе ли вердикт стать `passed`.

**Первичная запись (журнал сессии de9e5bcb).**

| Время (UTC) | Событие |
|---|---|
| 05:57:42 | Вопрос Q6 с тремя вариантами: «Назову признаки» (рекомендация), «Подпишу override для 1–7», «Вернуть UAT в testing» |
| 06:00:09 | Ответ: **«Назову признаки»** (dce39090) |
| 06:00:23 | Оркестратор просит признаки проверки 1: стенд и день, браузер, что стало с формой, причина отказа заблокированному, первые символы `access_token` до и после |
| 06:01:16 | «все мы закончили» (d886e4c4 — признаки не названы) |
| 06:01:56 | «закрой фазу 14» |
| 06:02:20 | Вопрос «Override»: «Закрыть фазу 14 сейчас можно только вашим явным подписанным решением (override): верификатор не считает «закрой» таким решением. В отчёт под вашим именем запишется вот что: проверки 1–7 засчитаны по вашему заявлению без признаков, и правило D-02 для фазы 14 ослаблено вами. Как поступить с проверками 8 и 9?» Варианты: **«Подписываю, 8–9 — отказ»** («…Находки UI WARNING 2 и 3 остаются открытыми и не наблюдёнными. Дальше: статус passed (override), SIGN-01…03 отмечаются выполненными, фаза закрывается в ROADMAP и STATE»), «Подписываю, 8–9 назову», «Не подписываю» |
| 06:02:49 | Ответ: **«Подписываю, 8–9 — отказ»** |
| 06:03:57 | Коммиты `feabd7fb` (обход) и `bae74ab7` (`overrides`, Q6) |

**Суждение верификатора о подписи.** Слово «закрой» круг 4 подписью не считал: в нём нет ни признания, что признаков не будет, ни принятия последствия. Ответ 06:02:49Z — другое дело, в нём есть и то и другое. Вопрос сам назвал, что запишется под именем владельца: заявление без признаков, ослабленное D-02 и отказ от 8 и 9 с открытыми находками. Был и вариант не подписывать. Правило D-02 — правило самого владельца, и ослабить его вправе только он; он это и сделал, явно. Поэтому верификатор принимает обе записи `overrides` как действующие решения в их собственных `covers`, не шире.

**Что решение закрывает.**
- **SC4** — PASSED (override). Запись 1 называет SC4 текстом критерия.
- **Пункты человеку 1–7** — `discharged`, `resolution` — override 1.
- **Пункты человеку 8–9** — `discharged`, `resolution` — override 2 (отказ от наблюдения).
- **W-R4-01** — закрыта решением: шапка `complete` поверх заявлений больше не противоречит правилу, действующему для Фазы 14.
- **W-R4-02** — закрыта: у проверок 8 и 9 теперь `skipped` с причиной, прежний `pass` сохранён строкой `history:`.

**Чего решение НЕ закрывает и не должно закрывать.**
- **Наблюдения нет.** В девяти отметках по-прежнему ни одного наблюдённого признака. Стенд этой машины за окно 2026-10-07T16:27Z…2026-10-08T06:09Z не видел ни одного `POST /login` и ни одного запроса к `/register/verify`, `/register/resend-code`, `/register/complete`, `/forgot-password/*` или `POST /impersonation/stop`. 34 `POST /register/send-code` — сторонний трафик I-R4-01. Обход мог идти на другом стенде, но какой это был стенд, не сказано. Отчёт фиксирует это как есть: SC4 закрыт РЕШЕНИЕМ, а не наблюдением.
- **Находки UI WARNING 2 и 3** — ОТКРЫТЫ и не наблюдены, как и записано в `covers` второй записи. Ни подтверждены, ни сняты. Блокерами они не стали ни в одном круге: ни одна не опровергает истину фазы.
- **Предикат закрытия фазы.** `gsd-tools phase uat-passed 14` и после записи этого отчёта будет блокировать проверки 8 и 9. Блокером он не считает только `skipped`, чья причина начинается с `Deferred follow-up:` (`uat-predicate.cjs:69`, `:576`). Отказ таким не является — W-R5-01, Q7.
- **23 помеченных запрета** решение не затрагивает: они остаются отсрочкой 1 с адресатом. Итог круга читается как «passed с 23 помеченными запретами».

**Граница поступка.** Ни `14-UAT.md`, ни `REQUIREMENTS.md` верификатор не правил. Блок `overrides` перенесён побайтово.

### Required Artifacts

| Artifact | Expected | Status | Details (круг 5) |
|---|---|---|---|
| `app/pages/htmx.py`, `app/pages/auth.py`, `app/main.py` | Выходы слоя; 10 обработчиков; реестр экранов | ✓ VERIFIED | Без изменений с круга 2 (diff вне `.planning/` с `ec41dcef` пуст) |
| `app/templates/auth/**`, `auth_base.html`, `base.html`, `components/*`, `includes/*` | Разметка экранов, якорь, макросы | ✓ VERIFIED | Без изменений |
| `tests/test_pages/*`, `tests/test_templates/test_htmx_markup_gates.py` | Правила фазы | ✓ VERIFIED | Без изменений; 27 именованных правил — PASS |
| `.planning/phases/14-…/14-UAT.md` | Артефакт обхода критерия 4 | ✓ VERIFIED как артефакт · запись приёмки — 7 `pass` по решению владельца, 2 `skipped` (отказ) | Разметка на месте; предикат обхода блокирует 8 и 9 — W-R5-01 |
| `.planning/phases/14-…/14-SECURITY.md` | Реестр угроз | ✓ VERIFIED | Не менялся с круга 3; `threats_open: 0` |

Таблицы трёх уровней (артефакты, связи, поток данных) — в §Приложение — запись круга 2. Источник не менялся, поэтому их выводы в силе. Ни одного MISSING, STUB или ORPHANED.

### Key Link Verification

Все семь связей круга 2 — ✓ WIRED; прогон их правил (1, 13, 15, 16–17, 19–21, 8–9) в круге 5 — PASS. Файлы источника не менялись.

### Data-Flow Trace (Level 4)

Шесть цепочек круга 2 — ✓ FLOWING (эхо email, двух кодов и имени; подписанный токен; намеренно пустой пароль по D-04). Источник не менялся.

### Behavioural Spot-Checks

**Круг 5: 27 именованных правил одним вызовом `pytest` — 27 passed, 357 deselected, за 17.65 с** (`-k` по 27 именам в шести модулях правил фазы, `-p no:cacheprovider -p no:randomly`). Это те же 25 правил таблицы круга 2 (номера 1–25 — как в приложении круга 2) и правила 26–27 записи Q4 (приложение круга 3). Суита целиком НЕ перезапускалась. Полный прогон 4084 passed взят входом: вне `.planning/` с `ec41dcef` не изменилось ничего (замерено).

Независимые замеры круга 5:

| Measurement | Command | Result |
|---|---|---|
| Коммиты после круга 4 | `git log 97b35cfc..HEAD` | 4: `dce39090`, `d886e4c4`, `feabd7fb`, `bae74ab7` |
| Изменённые файлы после круга 4 | `git diff --name-only 97b35cfc..HEAD` | `14-UAT.md`, `14-VERIFICATION.md` |
| Изменения вне `.planning/` с `ec41dcef` | `git diff --name-only ec41dcef..HEAD -- . ':!.planning'` | **0** |
| Решение владельца | журнал сессии de9e5bcb, 05:57Z–06:05Z | вопрос 06:02:20Z → «Подписываю, 8–9 — отказ» 06:02:49.661Z |
| Запросы обхода на стенде | `docker logs --since 2026-10-07T16:27Z nginx-broadcaster`, агрегат маршрутов авторизации | `GET /register` 35, `POST /register/send-code` 34, `GET /login` 23; `POST /login`, `/register/verify`, `/register/resend-code`, `/register/complete`, `/forgot-password/*`, `POST /impersonation/stop` — **0** |
| Предикат обхода | `gsd-tools phase uat-passed 14 --raw` (до записи отчёта) | `passed: false`; блокеры `14-UAT.md: test 8 (skipped)`, `test 9 (skipped)`, `verification status=human_needed` (вердикт круга 4, тогда `stale`) |
| Правило пропуска в предикате | чтение `bin/lib/uat-predicate.cjs:59-69`, `:570-590` | проходят только `pass`/`passed`, `skipped` с причиной `Deferred follow-up:…` и `issue` с подтверждённо закрытым пробелом; «a plain or non-deferral skipped — still blocks» |
| Механизм фокуса | `grep -rnE 'autofocus\|tabindex\|aria-live' app/templates/auth/ app/templates/auth_base.html` | 0 — UI WARNING 2 по-прежнему в силе |
| `is_same_origin` | `grep -n is_same_origin app/pages/auth.py`; `grep -c '@router.post'` | импорт + `:691` из 10 |
| `verified_at` | `grep -n verified_at app/pages/auth.py` | `:408, :443, :916, :950` |
| Покрытие решений | `check.decision-coverage-verify <phaseDir> 14-CONTEXT.md` | 15/15, `not_honored: []` |
| Долговые метки | `grep -E 'TBD\|FIXME\|XXX'` по 45 переданным покрытым файлам | 0 |
| Верб отпечатка | `verification.fingerprint` с дублем первого пути и без него | оба: 59 файлов, `v3:sha256:665f4278…` — потери первого пути нет |

### Probe Execution

Проб в дереве нет, и фаза их не объявляла (`find scripts -path '*/tests/probe-*.sh'` → 0). Шаг пропущен по отсутствию предмета, как в кругах 1–4.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| **SIGN-01** | 14-01…14-07 | 9 форм авторизации идут через htmx | ✓ SATISFIED (машинно); рантайм подмены — по решению владельца (SC4, override) | Истина 2; правила 5–7. Остаток — пункты человеку 1–5, закрытые override 1 |
| **SIGN-02** | 14-01…14-05, 14-07 | Неверный код или пароль перерисовывает форму с сохранением введённого | ✓ SATISFIED | Истины 1, 5, 6, 7; правила 1–4, 11–12, 22, 24. **Цель фазы достигнута сервером** |
| **SIGN-03** | 14-01, 14-03, 14-05, 14-06, 14-07 | Успех — `HX-Redirect`; `HX-Location` — у возврата (по летописи) | ✓ SATISFIED | Истина 3; правила 8–9, 13–15, 19–21 |

**Записи требований.** `REQUIREMENTS.md:60-62` — `[ ]`, `:160-162` — `Pending`, летопись `:64` — без изменений с круга 3. Правило `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` одностороннее: при вердикте `passed` оно зелено и с `Pending`, а перевод в `Complete` теперь допускает. Верификатор требований не правил. Отметки ставит закрытие фазы (`phase.complete`), а закрытие стоит за предикатом обхода (Q7). Сирот нет: прослеживаемость относит к Фазе 14 ровно SIGN-01…03, и все три заявлены планами.

### Decision Coverage

15/15 отслеживаемых решений `14-CONTEXT.md` опознаны, `not_honored: []`. Перемерено в круге 5 (с явным путём к CONTEXT.md). Владелец ослабил D-02 только в части правила закрытия обхода и только для Фазы 14 — запись 1 `overrides`. Поставленные планами артефакты D-02 (предусловия П-1…П-7, правило останова, девять таблиц отметок) на месте.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` в 45 переданных покрытых файлах круга 5, включая `14-UAT.md` | — | **Ноль.** Гейт долговых меток зелёный |
| — | — | Отключённые тесты, пустые реализации, статические возвраты | — | Ноль; код и правила не менялись с круга 2 |

### Findings Handed Over By Hand (code review and UI review)

Счёт: 15 находок, **закрыто 2, открыто 13** — как в кругах 2–4. Код не менялся, поэтому ни одна находка не закрылась. Поимённая таблица с уликами — в §Приложение — запись круга 3. В круге 5 изменилась только запись двух находок:

| ID | Круг 4 | Круг 5 |
|---|---|---|
| **UI WARNING 2** — ни фокуса, ни живой области после свопа | ОТКРЫТА; значение проверки 8 не названо (W-R4-02) | **ОТКРЫТА, НЕ НАБЛЮДЕНА — по решению владельца.** От наблюдения проверки 8 владелец отказался (override 2). Механизма по-прежнему нет (0 совпадений). Адресата у находки нет — Q7 (а) даёт его |
| **UI WARNING 3** — вторая кнопка живая на экранах кода | ОТКРЫТА; значение 9.1 не названо (W-R4-02) | **ОТКРЫТА, НЕ НАБЛЮДЕНА — по решению владельца** (override 2). Отброс второго запроса — PASS (правило 23) |

**Ни одна из этих находок не опровергает истину фазы**, поэтому ни одна не поднята до 🛑 Blocker. Открытые предупреждения вердикту `passed` не мешают: правило 1 шага 9 срабатывает только на блокерах.

### Findings Of Round 4 — State In Round 5

| ID | Круг 4 | Круг 5 — состояние и улика |
|---|---|---|
| **W-R4-01** — шапка `complete` поверх отметок, которые по D-02 закрытием не считаются | ⚠️ Warning → Q6 | **ЗАКРЫТА РЕШЕНИЕМ ВЛАДЕЛЬЦА.** D-02 для Фазы 14 ослаблено явно (override 1, ответ 06:02:49Z). Признаков по-прежнему нет — записано в SC4 и в `resolution` пунктов 1–7 |
| **W-R4-02** — проверки 8 и 9 записаны `pass` без значения | ⚠️ Warning → Q6 | **ЗАКРЫТА.** `14-UAT.md:150-153`, `:157-160` — `result: skipped`, `reason` с отказом, `history:` прежнего `pass` (feabd7fb). Новая сторона того же места — W-R5-01 |
| **I-R4-01** — сторонние `POST /register/send-code` с устаревших клиентов | ℹ️ → владельцу | **ОТКРЫТА, продолжается:** 34 за окно 16:27Z–06:09Z (в круге 4 было 33) |
| **I-R4-02** — верб отпечатка первый путь не теряет | ℹ️ → оркестратору | Подтверждена повторно (с дублем и без — одно значение) |
| **I-R3-02** — R-14-02 и todo называют 200 строкой `:841`, основной выход — `:876` | ℹ️ → оркестратору | **ОТКРЫТА.** `14-SECURITY.md` и todo не правились |
| **I-R3-04** | ℹ️ | Слита с I-R4-01 |
| **I-R2-02** — устаревшие записи (`STATE.md:29`, строка T-14-19 `14-SECURITY.md:59`) | ℹ️ | **ОТКРЫТА.** Файлы не правились. При закрытии фазы оркестратору стоит переписать `STATE.md:29` («верификация `passed` (12/13), обход человека 9/9 без находок») по факту: 13/13 с одним override, 7 по решению, 2 отказа |
| **I-R2-04** — вербы `verify.artifacts` / `verify.key-links` не разбирают строковые блоки планов | ℹ️ | **ОТКРЫТА** — планы не менялись |

### New Findings Of Round 5

| ID | Finding | Severity | Evidence | Route |
|---|---|---|---|---|
| **W-R5-01** | Отказ от проверок 8 и 9 записан простым `skipped` с причиной «Отказ владельца…». Штатный предикат закрытия фазы `phase uat-passed` такой пропуск блокирует: проходят только `skipped` с причиной `Deferred follow-up:…`. Поэтому при вердикте `passed` `/gsd-verify-work` фазу в ROADMAP и STATE не переведёт («phase advancement is blocked»). Описание варианта, который подписал владелец, обещало обратное: «статус passed (override), SIGN-01…03 отмечаются выполненными, фаза закрывается». Вердикт верен; не сходится обещанное последствие с правилом инструмента | ⚠️ Warning (запись приёмки; истину не затрагивает) | `phase uat-passed 14 --raw` — блокеры `test 8 (skipped)`, `test 9 (skipped)`; `uat-predicate.cjs:69`, `:576`; `verify-work.md:702-716`; журнал de9e5bcb 06:02:20Z | **Q7** — владельцу |
| **I-R5-01** | `accepted_at` обеих записей `overrides`, `owner_decision_final` Q6 и обе причины `skipped` в `14-UAT.md` стоят на 2026-10-08T06:03:27Z, а ответ владельца в журнале — 06:02:49.661Z, на 38 с раньше. Это время записи, а не ответа; решение предшествует записи. Для подписи несущественно, но кто будет сличать запись с журналом, увидит расхождение | ℹ️ Info | журнал de9e5bcb; `overrides[*].accepted_at`; `14-UAT.md:151`, `:158` | Оркестратору — на усмотрение; верификатор подписанный блок не правит |

### Self-check (после записи отчёта)

| Check | Command | Result |
|---|---|---|
| Вердикт читается владельцем статуса | `gsd-tools query verification.status <phaseDir> --pick status` | `passed`, код 0 (до записи — `stale`); `next_action: «Verification passed — continue.»`, маршрута нет |
| Отпечаток | `gsd-tools query verification.fingerprint <phaseDir> <45 путей>` и тот же вызов с дублем первого пути | 59 покрытых файлов (45 + 14 PLAN/SUMMARY), потерянных путей 0, дублей 0; оба вызова — `v3:sha256:665f4278…`; `covered_digest` скопирован из вывода дословно |
| Фронтматтер разбирается | `yaml.safe_load` блока между разделителями | ок: `status: passed`, `score` 13/13, `overrides_applied: 1`, `backstop_abstentions: 0`; 10 пунктов человеку — все `discharged`, у каждого `resolution`; 7 вопросов (Q1–Q7); 3 отсрочки (open, open, closed); блок `re_verification` круга 4 вложен под `previous_round_record`, круги 3 и 2 — под ним |
| Подписанный блок `overrides` | сравнение 13 строк блока с резервной копией | **побайтово тот же**; `covers` не тронуты |
| Разборщик пунктов человеку | `gsd-tools query audit-uat --raw` | `14-VERIFICATION.md` в выдаче нет (вердикт `passed`, открытых пунктов 0). У `14-UAT.md` — `status: complete`, два пункта `skipped_unresolved` (тесты 8 и 9) — W-R5-01 |
| Предикат обхода | `gsd-tools phase uat-passed 14 --raw` и `--require-verification` | оба `passed: false`; блокеры — только `14-UAT.md: test 8 (skipped)`, `test 9 (skipped)`. Блокер вердикта (`verification status=human_needed`) снят этим отчётом → Q7 |
| Перенос записи — по значениям | `carry_check_r5.py`: каждое поле фронтматтера резервной копии `14-VERIFICATION.pre-round5.md` против нового файла (`re_verification` круга 4 — против `previous_round_record`) | расхождений **0** сверх девяти объявленных: `human_verification[0…8].state` `still_required` → `discharged`, прежнее значение — в `round_4_state` у каждого (сверено). Все прочие поля `deferred`, `escalations`, `human_verification`, `human_verification_round_1`, `owner_questions` Q1–Q6 (с `owner_answer`, `owner_answer_followup`, `owner_decision_final`), `decision_coverage`, `flagged_prohibitions`, `overrides` равны прежним; новые поля только добавлены |
| Перенос записи — по строкам | тот же скрипт: каждая непустая строка копии (1851 строка) против нового файла | потеряна **одна** строка, намеренно: финальная подпись круга 4 переехала в конец §Приложение — запись круга 4 как «Подпись круга 4: …». Сверх неё заменены: шапка круга 4 (`verified`/`status`/`score`/`covered_files`/`covered_digest`), две строки счётчиков (прежний текст сохранён комментарием дословно) и девять строк `state:`. Блок `re_verification` круга 4 — со сдвигом на два пробела, заголовки тела круга 4 — понижены с меткой «[круг 4]», остальное побайтово |
| Правила записей | `uv run pytest tests/test_planning -q -p no:cacheprovider` | **208 passed** за 15.61 с, включая `test_requirement_completion_follows_verification.py` (SIGN-01…03 `Pending` при `passed` — правило одностороннее, зелено) и `test_the_walkthrough_cannot_self_certify.py` |

### Advisory (New Scope, Unevidenced)

Нет. Узкий гейт улик (#3304) этому кругу формально не применим: блока `gaps` не было ни в одном круге, и шаг 0 ведёт прогон в полном объёме. Каждая новая находка несёт детерминированную улику: вывод штатного верба, номер строки правила, метку времени первичной записи. Ни одна не 🛑 Blocker и ни одна не опровергает истину фазы.

### Escalation — решение владельца, которое я не вправе принять за него

Эскалация CR-02 / WR-07 **закрыта** с круга 2 и не переоткрывается. Развилку круга 4, Q6, владелец решил подписью. Развилка круга 5 — **Q7**: как записать отказ от проверок 8 и 9, чтобы штатный предикат закрытия фазы его принял. На вердикт ответ не влияет — он `passed` при любой ветви. Но от него зависит, закроется ли фаза штатно. Решить это может только владелец. Перезапись «смотреть не буду» в «посмотрим позже» (`Deferred follow-up:`) меняет смысл его подписи и даёт находкам UI WARNING 2 и 3 адресата. Это не правка формы, которую оркестратор вправе сделать сам.

### Deferred Items

Круг 4 → круг 5: три пункта. **Открыто 2, закрыто 1** — без изменений. Ни одна отсрочка не адресована более поздней фазе вехи: Фаза 15 закрыта, позже неё в вехе фаз нет. Обе открытые несут адресата, записанного владельцем (отсрочка 1), или запись владельца об отсрочке (отсрочка 2). Вердикта они не меняют.

| # | Item | Круг 4 | Круг 5 — состояние и улика |
|---|---|---|---|
| 1 | 23 запрета планов 14-01…14-07 — `flagged-unverified` / `verification: none` | ОТКРЫТ, адресат есть | **ОТКРЫТ, АДРЕСАТ ТОТ ЖЕ** — бэклог следующей вехи (todo `classify-420…`). Не засчитан зелёным: «passed с 23 помеченными запретами» |
| 2 | CR-01 — гард источника запроса на девяти формах | ОТКРЫТ; риск принят (R-14-01) | **ОТКРЫТ.** Код не менялся: 1 вызов из 10 (`:691`). Адресат-фаза не назначен |
| 3 | `hx-push-url` на формах авторизации | ЗАКРЫТ Фазой 15 | **ЗАКРЫТ** — без изменений |

### Human Verification Required

**Нет открытых пунктов.** Круг 5: все десять пунктов `discharged`. Пункты 1–9 закрыты подписанным решением владельца, а не наблюдением; пункт 10 закрыт с круга 3 адресатом. Поимённые основания — во фронтматтере: `resolution`, `round_5_state_evidence`; прежние `state_evidence` и `round_4_state_evidence` сохранены рядом.

| # | Пункт | Круг 4 | Круг 5 | Основание |
|---|---|---|---|---|
| 1 | Полный вход в браузере — UAT 1 | still_required | discharged | override 1 — заявление без признаков, D-02 ослаблено |
| 2 | Регистрация до экрана кода и завершение — UAT 2 | still_required | discharged | override 1 |
| 3 | Подтверждение почты настоящим письмом — UAT 3 | still_required | discharged | override 1; доставка писем не наблюдена |
| 4 | Восстановление пароля целиком — UAT 4 | still_required | discharged | override 1 |
| 5 | Возврат из-под чужой личности — UAT 5 | still_required | discharged | override 1 |
| 6 | Менеджер паролей — UAT 6 | still_required | discharged | override 1; база без JS не названа |
| 7 | Карточка на 375px и на десктопе — UAT 7 | still_required | discharged | override 1 |
| 8 | Фокус и объявление после свопа — UAT 8 | still_required | discharged | override 2 — отказ; UI WARNING 2 открыта |
| 9 | Вторая кнопка на экранах кода — UAT 9 | still_required | discharged | override 2 — отказ; UI WARNING 3 открыта |
| 10 | Решение владельца по 23 запретам | discharged | discharged | адресат — бэклог следующей вехи (с круга 3) |

Сверка с правилом «overrides не подавляют пункты человеку». Пункты 1–9 закрыл не верификатор, обойдя человека. Их закрыл сам человек, который должен был наблюдать: по 1–7 — своим заявлением и подписью, по 8–9 — подписанным отказом. Улики наблюдения у них нет, и это записано в каждом `resolution`.

### Owner Questions

Полные формулировки, рекомендации, ответы и места исполнения — во фронтматтере `owner_questions`.

- **Q1** — SIGN-01…03. Исполнено в круге 3; в круге 5 отметки по-прежнему `Pending`. Перевод в `Complete` правило теперь допускает, ставит его закрытие фазы (за Q7).
- **Q2** — `result: pass` ×9 при отозванном обходе. Исполнено в круге 3; в круге 5 у 8 и 9 — `skipped` с причиной.
- **Q3** — адресат 23 запретов. Закрыт в круге 3; пункт 10 discharged.
- **Q4** — R-14-02. Исполнено в круге 3; I-R3-02 открыта.
- **Q5** — проводился ли обход глазами. Ответ круга 4 — заявление без признаков; в круге 5 его засчитала подпись владельца (Q6).
- **Q6** — **решён владельцем** (06:02:49Z): ветвь (б), `overrides` — 1–7 по заявлению, D-02 ослаблено; 8–9 — отказ. Применён: SC4 → PASSED (override), пункты 1–9 → discharged.
- **Q7 (новый, единственный открытый)** — как записать отказ от 8 и 9, чтобы штатный предикат закрытия фазы его принял. **Рекомендация:** (а) отложенная работа `Deferred follow-up:` с адресатом для UI WARNING 2/3; иначе (б) два значения сейчас; иначе (в) оставить отказ — вердикт `passed`, но фаза штатно не закроется.

### Gaps Summary

**Изъянов, блокирующих достижение цели, не найдено** — ни в одном из пяти кругов.

Цель фазы — «неверный код или пароль перестаёт стирать заполненную форму» — **истинна в дереве, и истинной её делает СЕРВЕР**:
- 422 стоит литералом в `respond_field_error`;
- эхо едет параметром в автоэкранирующий шаблон;
- путь без JS получает ту же страницу прямо в ответ на POST.

В круге 5 это снова подтверждено прогоном 27 именованных правил со значимыми утверждениями на обоих транспортах — на дереве, где вне `.planning/` с круга 2 не изменилось ничего.

**Почему теперь `passed`.**
- Правило 1 (`gaps_found`) не срабатывает: ни одна истина не FAILED, ни один артефакт не MISSING или STUB, ни одна связь не NOT_WIRED, блокеров нет.
- Правило 2 (`human_needed`) больше не срабатывает: открытых пунктов человеку 0. Пункты 1–9 закрыл сам владелец подписанным решением — круг 4 называл эту ветвь (б) Q6 и её последствие заранее. Пункт 10 закрыт с круга 3.
- 12 истин ✓ VERIFIED прогоном, SC4 — PASSED (override). Счёт 13/13 включает один override. В нём нет утверждения, что обход наблюдён.

**Что `passed` здесь НЕ означает.** Это не «обход наблюдён». Ни одного наблюдённого признака в записи обхода нет, стенд этой машины запросов обхода не видел, проверки 8 и 9 не проводились по отказу, находки UI WARNING 2 и 3 открыты. Двадцать три запрета не засчитаны зелёным. Всё это названо выше. Вердикт держится на машинной половине и на подписи владельца, и каждая из двух опор записана под своим именем.

**Что осталось за пределами вердикта.** Q7: штатный предикат не закроет фазу, пока отказ от 8 и 9 записан простым `skipped` (W-R5-01).

## Приложение — запись круга 4 дословно

Тело отчёта круга 4 (коммит `97b35cfc`, дерево `f447c5ed`, 2026-10-08T05:50:52Z) перенесено ЦЕЛИКОМ и ДОСЛОВНО как запись своего дня, а не как действующий вердикт. Единственное механическое преобразование — то же, что круги 2–4 применили к записям предыдущих кругов. Строки заголовков (`#`…`####`) переписаны в жирный текст с меткой «[круг 4]», чтобы разборщики пунктов человеку (`src/uat.cts`) не собрали их второй раз. Все прочие строки совпадают побайтово; это проверено скриптом при сборке, см. §Self-check. Действующие состояния каждого пункта — в разделах круга 5 выше. Подпись круга 4 перенесена в конец этого приложения.

**[круг 4] Phase 14: Авторизация на htmx — Verification Report**

**Phase Goal:** неверный код или пароль перестаёт стирать заполненную форму — заявленный выигрыш вехи именно в ОШИБКЕ, а не в успехе
**Verified:** 2026-10-08T05:50:52Z (круг 4; круг 3 — 2026-10-07T15:58:55Z; круг 2 — 2026-10-07T12:31:06Z; круг 1 — 2026-09-23T08:15:00Z)
**Status:** human_needed
**Re-verification:** Да — КРУГ 4. HEAD `f447c5ed`. Повод: вердикт круга 3 прочитался `stale`, потому что изменился покрытый `14-UAT.md`. Блока `gaps` не было ни в одном круге, поэтому по букве шага 0 это снова прогон в полном объёме: все 13 истин перепроверены прогоном, а не перенесены. Тело отчёта круга 3 перенесено целиком в §Приложение — запись круга 3, отчёты кругов 2 и 1 — в свои приложения, как и прежде. Все три — дословно.

**Что изменилось с круга 3 (замерено, а не взято из поручения).**
- `git log 93e1d4d2..HEAD` — ровно один коммит: `f447c5ed` (2026-10-08T05:43:56Z).
- `git diff --name-only 93e1d4d2..HEAD` — только `.planning/phases/14-avtorizatsiya-na-htmx/14-UAT.md` (+42/−20).
- `git diff --name-only ec41dcef..HEAD -- . ':!.planning'` — **0 строк**: ни продуктовый код, ни правила с круга 2 не менялись.

**Чего не наследую.** Ни `state_evidence` круга 3, ни его `human_needed`, ни шапки `complete` в файле обхода, ни формулировок поручения. Слова поручения «владелец отказался назвать признаки» сверены с первичной записью: журналом сессии de9e5bcb. Из него взяты метки времени, ответы владельца и тексты вопросов, на которые они даны. Без вопроса не понять, на что именно ответил владелец. Итог круга — `human_needed`, и стоит он на собственной улике круга. Это не воздержание: запись обхода я рассмотрел и счёл, что наблюдения она не несёт и что засчитать её закрытием вправе только владелец (§Обход 2026-10-07…08, Q6).

**Method.** Goal-backward; must-haves — те же четыре критерия ROADMAP и истины фронтматтера семи планов. Улики круга:
- **Прогон.** 27 именованных правил одним вызовом `pytest` — **27 passed за 16.96 с**: те же 25 правил круга 2 и два правила записи Q4. После записи отчёта — `tests/test_planning` целиком (§Self-check).
- **Чтение дерева.** Номера строк выписаны в таблицах.
- **Две первичные улики вне дерева, только чтение.**
  - Журнал сессии оркестратора de9e5bcb: метки времени, ответы владельца, вопросы оркестратора.
  - Журналы контейнеров стенда `web-broadcaster` и `nginx-broadcaster` за окно 2026-10-07T16:27Z…2026-10-08T05:46Z. Сняты только агрегированные счёты маршрутов авторизации и семейство клиента; IP-адреса не печатались, ничего не запускалось и не менялось.

**[круг 4] Goal Achievement**

**[круг 4] Observable Truths**

| # | Truth | Status | Evidence (круг 4) |
|---|-------|--------|----------|
| 1 | **SC1 / SIGN-02.** Неверный код или пароль перерисовывает форму С СОХРАНЕНИЕМ введённого: 422 + эхо в `value=`; свойство создаёт СЕРВЕР | ✓ VERIFIED | Код не менялся (diff вне `.planning/` с `ec41dcef` пуст). ПРОГОН круга 4: правила 1–4, 22 (трасер входа), 24 — PASS |
| 2 | **SC2 / SIGN-01.** Все 9 форм авторизации идут через `hx-post` и остаются рабочими без JS | ✓ VERIFIED | Прогон: правила 5–7, 10 — PASS |
| 3 | **SC3 / SIGN-03.** Успех авторизации уходит `HX-Redirect` через границу шеллов; `HX-Location` — по летописи | ✓ VERIFIED | По летописи — разбор §Criterion 3 круга 2 в силе, источник не менялся. Прогон: правила 8–9, 13–15, 19–21 — PASS |
| 4 | **SC4.** Вход, регистрация, подтверждение почты и восстановление пароля проходят в браузере целиком | ⚠️ `insufficient_spec` (backstop abstention) | **НЕ проверяется кодом и НЕ доказано наблюдением.** `verification: backstop` у всех семи планов, единственный канал — обход человека. Запись 2026-10-08 (`f447c5ed`) несёт заявление владельца «я все проверил» без единого наблюдённого признака, и сама запись это признаёт. По D-02 такая отметка закрытием не считается; ослабить правило вправе только владелец — Q6. Истина не FAILED: улики против поведения нет, машинная половина зелена (27/27) |
| 5 | Враждебный ввод возвращается в `value=` ТОЛЬКО экранированным, на обоих транспортах | ✓ VERIFIED | Прогон: правила 2 и 24 — PASS |
| 6 | Пароль не возвращается НИКОГДА — ни в `value=`, ни в теле, ни в контексте шаблона | ✓ VERIFIED | Прогон: правила 1, 11 — PASS |
| 7 | Отказ 422 не несёт cookie сессии ни на одном транспорте; заблокированный с ВЕРНЫМ паролем получает 422 с `BLOCKED_LOGIN_ERROR` | ✓ VERIFIED | Прогон: правила 1, 12 — PASS |
| 8 | Смена экрана — 200 на обоих транспортах; подписанный токен шага едет ТОЛЬКО скрытым полем | ✓ VERIFIED | Прогон: правила 3, 4, 23 — PASS |
| 9 | Возврат из-под чужой личности: три ветки, cookie перезаписана НА ЭТОМ ЖЕ ответе, следующий `GET /admin` отдаёт админку | ✓ VERIFIED (behaviour-dependent — доказано прогоном, не присутствием) | Прогон круга 4: правила 13–15 — PASS |
| 10 | Восстановление пароля под чужой личностью остаётся запрещённым на ВСЕХ четырёх шагах, на обоих транспортах | ✓ VERIFIED (behaviour-dependent) | Прогон: правила 16–17 — PASS |
| 11 | Счётчик отставания вехи — ИМЕНОВАННЫЙ НОЛЬ, доказанный НЕ ВАКУУМНЫМ | ✓ VERIFIED | Прогон: правило 10 — PASS |
| 12 | Реестр `AUTH_SCREENS` накрывает ВСЕ семь страниц второго шелла; заголовок фрагмента и заголовок страницы сличаются | ✓ VERIFIED | Прогон: правила 18 и 25 — PASS |
| 13 | Записи фазы приведены в объявленную форму: летописи критериев 2 и 3, строки Research, SIGN-03, рамки вехи; окно 63 переведено ЗАМЕРОМ; артефакт обхода размечен | ✓ VERIFIED | Истина плана 14-07 — о ПОСТАВЛЕННОЙ им разметке. Летописи не менялись. Артефакт обхода и сегодня несёт `checks_declared: 9`, 9 разделов, 9 таблиц, предусловия П-1…П-7 и правило останова; шаг 7.2 исправлен на базу `fd69a26a`. Заполнение 2026-10-08 — предмет W-R4-01, а не провал истины плана |

**Score:** 12/13 truths verified (0 present-but-behaviour-unverified; 1 backstop abstention routed to human). Круг 3 → круг 4: тот же счёт и те же статусы истин. Изменилось основание пунктов человеку 1–9. Шаблонной записи больше нет. Вместо неё — заявление владельца без признаков, и засчитать его закрытием может только сам владелец.

**[круг 4] Обход 2026-10-07…08 — что эта запись закрывает и чего не закрывает**

Это главный предмет круга: от него зависит, переходит ли SC4 из воздержания в VERIFIED и закрываются ли пункты 1–9.

**Что записано.** `14-UAT.md` после `f447c5ed`:
- абзац 2026-10-07T16:28:14Z: объявление `complete` от f63a3c49 отозвано по решению владельца («Restart walkthrough»), прежний шаблон отметок процитирован дословно. Последняя фраза абзаца: «Отметку теперь пишет только то, что владелец назвал своими словами: что увидел, на каком стенде, в каком браузере, а для проверок 8 и 9 — значение»;
- шаг 7.2: база сравнения — дерево до фазы `fd69a26a`, а не `master` (`:302`);
- шапка `status: complete`, `updated: 2026-10-08T05:43:56Z`; девять `result: pass`, у каждого `reported:` со словами владельца и строка `history:`; `## Summary` — `passed: 9`;
- в каждой из девяти таблиц одна строка: `| 2026-10-08 (дата заявления; дата наблюдения не названа) | не названы | chubav | слова владельца дословно: «закрой все по тесту N я все проверил». Признаков шагов N.1–N.k … владелец не назвал; оркестратор их не дописывал |`. У проверок 8 и 9 в строке сверх того перечислены неназванные ЗНАЧЕНИЯ.

Три счёта правила самозаверения сходятся: `checks_declared` 9, разделов 9, таблиц 9, заполнено 9. Правило зелено. Но, как записано в его шапке, оно утверждает единственное: «ЗАПИСЬ о прохождении не шире собственных отметок». Значит, судить, несут ли отметки наблюдение, — дело верификатора.

**Первичные улики (журнал сессии de9e5bcb: метки времени, ответы владельца, вопросы оркестратора).**

| Время (UTC) | Событие |
|---|---|
| 2026-10-07 16:27:02 | Запущен `/gsd-verify-work 14` (после `/clear`) |
| 16:27:37 → 16:27:41 | Вопрос «How do you want to proceed?» → **«Restart walkthrough (Recommended)»**. Описание выбранного варианта: «Each mark gets only what you describe in your own words: what you saw, on which setup, and the value for checks 8/9» |
| 16:28:42 → 16:28:47 | Чекпойнт проверки 1 → «pass» (через 66 с после выбора перезапуска) |
| 16:28:53 | Оркестратор держит проверку 1 в `[pending]` и просит своими словами: дату, стенд, браузер, признаки 1.1–1.3, первые символы `access_token` до и после. И добавляет: «If you haven't actually done these steps yet, say so» |
| 16:29:24 → 16:29:44 | «задай вопрос по русски» → та же просьба по-русски |
| — | **13 ч 11 мин без ответа** |
| 2026-10-08 05:40:33 | «закрой все по тесту 1 я все проверил» |
| 05:41:09 · :34 · :47 · 05:42:02 · :24 · :39 | Проверки 2–7 — «закрой все по тесту N я все проверил». Перед каждым ответом оркестратор пишет: «Напишите, что увидели своими словами» |
| 05:42:52 | Перед проверкой 8 оркестратор: «Ответ «я все проверил» этот пункт не закроет даже формально (W-R3-02). Без значений я запишу тест 8 как пропущенный с причиной» |
| 05:43:14 | «я все проверил закрой тест 8» → записан `pass` «по вашему решению» |
| 05:43:35 | «я все проверил закрой тест 9» (в вопросе значение 9.1 названо прямо) |
| 05:43:56 | Коммит `f447c5ed` |
| 05:44:12 → 05:44:20 | Вопрос оркестратора: «Сначала дописать признаки» (стенд и браузер, `access_token`, фокус и скринридер, вид второй кнопки) или «Запустить сейчас»? → **«Запустить сейчас»** |

**Стенд.** Журнал боевого стенда этой машины за окно 2026-10-07T16:27Z…2026-10-08T05:46Z:
- **0** `POST /login` любого статуса — проверка 1 (шаги 1.1, 1.3, 1.4) и шаги 6.1–6.2 порождают его обязательно;
- **0** запросов `/register/verify`, `/register/resend-code`, `/register/complete` — проверки 2, 3, 6;
- **0** запросов `/forgot-password/*` — проверки 4 и 6.4;
- **0** `POST /impersonation/stop` — проверка 5; к `/admin…` — один 404 сканера;
- 33 `POST /register/send-code` — все 200, полностраничные (~6.2 КБ), с устаревших клиентов (IE 7–11, Chrome 35–45, Android 4–5, iPad iOS 8), без продолжения. Это сторонний трафик I-R3-04, продолжившийся в окне (I-R4-01), а не обход.

**Что изменилось против круга 3 — и что нет.**

| Основание круга 3 | Круг 4 |
|---|---|
| Отметки — шаблон оркестратора, своих слов нет | **Снято.** Отметки несут только слова владельца дословно, оркестратор ничего не дописал, вариант «Chrome + Firefox / Linux» не подставлен. Запись честно перечисляет, чего в ней нет |
| 94 с на девять проверок, через 48 с после «пройти заново» — физически невозможно | **Снято.** Между просьбой о признаках и ответом прошло 13 ч 11 мин. Настоящий обход в таком окне возможен. Три минуты на девять ответов — темп отчёта, а не обхода |
| Стенд не видел запросов проверок 1, 3, 4, 5 | **Ослабло.** В окне этот стенд тоже не видел ни одного запроса обхода. Но обход мог идти на другом стенде, а какой стенд — владелец не сказал |
| Нет заявления, что обход проводился | **Снято.** «я все проверил» — заявление владельца, его собственными словами, девять раз |
| Нет ни одного наблюдённого признака | **ОСТАЛОСЬ — и теперь это записано в самих отметках.** На прямую просьбу назвать признаки (16:28:53, 16:29:44, перед каждым чекпойнтом, 05:44:12) владелец признаков не назвал. На последний вопрос он выбрал «Запустить сейчас» вместо «Сначала дописать признаки» |
| Проверки 8 и 9 без значения (W-R3-02) | **ОСТАЛОСЬ.** Оркестратор предупредил, что «я все проверил» их не закроет даже формально; записан `pass` |
| База 7.2 — `master` (W-R3-03) | **Снято в записи** — `fd69a26a`. Сверялись ли с ней промежутки, не сказано |

**Суждение верификатора.** Заявление «я все проверил» — улика того, что владелец считает обход пройденным. Улики того, ЧТО он увидел, в нём нет. Признак, по которому D-02 и сам файл отличают закрытую проверку от незакрытой, — наблюдённый признак. Под каждой из девяти таблиц написано: «отметка без наблюдённого признака закрытием не считается». Владелец сам выбрал перезапуск на этом условии: «Each mark gets only what you describe in your own words: what you saw, on which setup». По этому правилу ни одна из девяти отметок закрытием не считается, и шапка `complete` поверх них шире собственных отметок по существу, хотя не по числу строк (W-R4-01).

Я не утверждаю, что обхода не было, и не обвиняю владельца. Против поведения улики нет, машинная половина зелена. Но правило «отметка требует признака» — правило самого владельца (D-02). Отменить его для Фазы 14 вправе только он, и не молча, а явным решением с подписью. Слово «закрой» таким решением я не считаю: в нём нет ни признания, что признаков не будет, ни принятия последствия. Поэтому развилка вынесена владельцу вопросом Q6, а не решена мною ни в одну сторону.

**Проверки 8 и 9 — отдельно.** Их предмет — ЗНАЧЕНИЕ, а не подтверждение: куда встаёт фокус и что слышит скринридер; выглядит ли вторая кнопка живой. От значения зависит судьба находок UI WARNING 2 и 3: подтвердить их или снять. «Я все проверил» значения не несёт. Даже если владелец ослабит D-02 для проверок 1–7 (ветвь (б) Q6), пункты 8 и 9 этим не закроются. Закрыть их могут только значения либо явный отказ владельца от проверки, при котором обе находки остаются открытыми и ненаблюдёнными (W-R4-02).

**Сличение с прецедентом Фазы 13** (`passed` на «pass» без детализации признаков):

| | Фаза 13 | Фаза 14, круг 4 |
|---|---|---|
| Слова владельца | СВОИ, на прямой вопрос: «все было на живом стенде с реальными аккаунтами telegram» — названы стенд и предмет | СВОИ: «я все проверил». Стенд, день, браузер и предмет не названы |
| Ответ на просьбу о признаках | Дан (стенд, аккаунты) | Не дан; на последний вопрос выбран «Запустить сейчас» вместо «Сначала дописать признаки» |
| Окружение в отметке | «Chrome 152 / macOS 15», «Александр» — названо наблюдателем | «не названы» |
| Значения там, где проверка их требует | — | Нет (8, 9) |
| Улика против | Нет | Слабая: стенд этой машины за окно запросов обхода не видел |

Прецедент Фазы 13 принимал наблюдение, названное своими словами. Здесь своими словами названо заявление, а не наблюдение. Поэтому прецедент переносится только наполовину: заявление есть, наблюдения нет.

**Вывод по пунктам.** Пункты 1–9 — `still_required`. Пункт 10 — `discharged`, без изменений. Самый дешёвый честный путь закрытия — ветвь (а) Q6: по строке признаков на проверку. Если обход действительно пройден, это минута на проверку.

**Граница поступка.** `14-UAT.md` верификатор не правил ни строкой. Шапку `complete` и `result: pass` не трогал. Вернуть их, подтвердить признаками или подписать отказ от правила — решение владельца (Q6).

**[круг 4] Required Artifacts**

| Artifact | Expected | Status | Details (круг 4) |
|---|---|---|---|
| `app/pages/htmx.py`, `app/pages/auth.py`, `app/main.py` | Выходы слоя; 10 обработчиков; реестр экранов | ✓ VERIFIED | Без изменений с круга 2 (diff вне `.planning/` с `ec41dcef` пуст) |
| `app/templates/auth/**`, `auth_base.html`, `base.html`, `components/*`, `includes/*` | Разметка экранов, якорь, макросы | ✓ VERIFIED | Без изменений |
| `tests/test_pages/*`, `tests/test_templates/test_htmx_markup_gates.py` | Правила фазы | ✓ VERIFIED | Без изменений; 27 именованных правил — PASS |
| `.planning/phases/14-…/14-UAT.md` | Артефакт обхода критерия 4 | ✓ VERIFIED как артефакт (разметка на месте, 7.2 исправлен) · ⚠️ запись наблюдения — W-R4-01, W-R4-02 | Предмет §Обход 2026-10-07…08 |
| `.planning/phases/14-…/14-SECURITY.md` | Реестр угроз | ✓ VERIFIED | Не менялся с круга 3; `threats_open: 0` |

Таблицы трёх уровней (артефакты, связи, поток данных) — в §Приложение — запись круга 2. Источник не менялся, поэтому их выводы в силе. Ни одного MISSING, STUB или ORPHANED.

**[круг 4] Key Link Verification**

Все семь связей круга 2 — ✓ WIRED; прогон их правил (1, 13, 15, 16–17, 19–21, 8–9) в круге 4 — PASS. Файлы источника не менялись.

**[круг 4] Data-Flow Trace (Level 4)**

Шесть цепочек круга 2 — ✓ FLOWING (эхо email, двух кодов и имени; подписанный токен; намеренно пустой пароль по D-04). Источник не менялся.

**[круг 4] Behavioural Spot-Checks**

**Круг 4: 27 именованных правил одним вызовом `pytest` — 27 passed, 357 deselected, за 16.96 с** (`-k` по 27 именам в шести модулях правил фазы, `-p no:cacheprovider`). Это те же 25 правил таблицы круга 2 (номера 1–25 — как в приложении круга 2) и правила 26–27 записи Q4 (приложение круга 3). Суита целиком НЕ перезапускалась. Полный прогон 4084 passed взят входом: вне `.planning/` с `ec41dcef` не изменилось ничего (замерено).

Независимые замеры круга 4:

| Measurement | Command | Result |
|---|---|---|
| Коммиты после круга 3 | `git log 93e1d4d2..HEAD` | 1: `f447c5ed` |
| Изменённые файлы после круга 3 | `git diff --name-only 93e1d4d2..HEAD` | только `14-UAT.md` (+42/−20) |
| Изменения вне `.planning/` с `ec41dcef` | `git diff --name-only ec41dcef..HEAD -- . ':!.planning'` | **0** |
| База шага 7.2 | `git log --reverse fd69a26a..5b3b91c5`; `merge-base --is-ancestor fd69a26a 5b3b91c5` | `fd69a26a` — родитель первого коммита плана 14-01 `ca66794f` («test(14-01): add failing tracer…»); предок — да |
| Ответы владельца | журнал сессии de9e5bcb | 9 заявлений за 3 мин 2 с (05:40:33–05:43:35Z), через 13 ч 11 мин после просьбы о признаках; признаков 0 |
| Запросы обхода на стенде | `docker logs web-broadcaster`/`nginx-broadcaster`, агрегат за 16:27Z–05:46Z | 0 запросов проверок 1–6; 33 сторонних `send-code` |
| Покрытие решений | `check.decision-coverage-verify <phaseDir> 14-CONTEXT.md` | 15/15, `not_honored: []` |
| Долговые метки | `grep -E 'TBD\|FIXME\|XXX'` по 59 покрытым файлам | 0 |
| Верб отпечатка | `verification.fingerprint` с дублем первого пути и без него | оба: 59 файлов, одно значение — потери первого пути нет (I-R4-02) |
| Предикат обхода | `gsd-tools phase uat-passed 14` | `passed: false` (вердикт `stale` до записи этого отчёта) |

**[круг 4] Probe Execution**

Проб в дереве нет, и фаза их не объявляла (`find scripts -path '*/tests/probe-*.sh'` → 0). Шаг пропущен по отсутствию предмета, как в кругах 1–3.

**[круг 4] Requirements Coverage**

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| **SIGN-01** | 14-01…14-07 | 9 форм авторизации идут через htmx | ✓ SATISFIED (машинно); рантайм подмены — за человеком | Истина 2; правила 5–7. Остаток — §Human Verification 1–5 |
| **SIGN-02** | 14-01…14-05, 14-07 | Неверный код или пароль перерисовывает форму с сохранением введённого | ✓ SATISFIED | Истины 1, 5, 6, 7; правила 1–4, 11–12, 22, 24. **Цель фазы достигнута сервером** |
| **SIGN-03** | 14-01, 14-03, 14-05, 14-06, 14-07 | Успех — `HX-Redirect`; `HX-Location` — у возврата (по летописи) | ✓ SATISFIED | Истина 3; правила 8–9, 13–15, 19–21 |

**Записи требований.** `REQUIREMENTS.md:60-62` — `[ ]`, `:160-162` — `Pending`, летопись `:64` — без изменений с круга 3. Запись совпадает с вердиктом `human_needed`, и правило записей зелено (§Self-check). Сирот нет: прослеживаемость относит к Фазе 14 ровно SIGN-01…03, и все три заявлены планами.

**[круг 4] Decision Coverage**

15/15 отслеживаемых решений `14-CONTEXT.md` опознаны, `not_honored: []`. Перемерено в круге 4 (с явным путём к CONTEXT.md).

**[круг 4] Anti-Patterns Found**

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` в 59 покрытых файлах круга 4, включая `14-UAT.md` | — | **Ноль.** Гейт долговых меток зелёный |
| — | — | Отключённые тесты, пустые реализации, статические возвраты | — | Ноль; код и правила не менялись с круга 2 |

**[круг 4] Findings Handed Over By Hand (code review and UI review)**

Счёт: 15 находок, **закрыто 2, открыто 13** — как в кругах 2 и 3. Код не менялся, поэтому ни одна находка не закрылась и ни одна запись не изменилась. Поимённая таблица с уликами — в §Приложение — запись круга 3. В круге 4 изменилась только запись двух находок:

| ID | Круг 3 | Круг 4 |
|---|---|---|
| **UI WARNING 2** — ни фокуса, ни живой области после свопа | ОТКРЫТА; наблюдение не записано (W-R3-02) | **ОТКРЫТА.** Механизма по-прежнему нет. Значение проверки 8 не названо и после прямой просьбы, хотя записан `pass` (W-R4-02). Находка не подтверждена и не снята |
| **UI WARNING 3** — вторая кнопка живая на экранах кода | ОТКРЫТА; видимость не записана (W-R3-02) | **ОТКРЫТА.** Отброс второго запроса — PASS (правило 23). Значение 9.1 не названо (W-R4-02) |

**Ни одна из этих находок не опровергает истину фазы**, поэтому ни одна не поднята до 🛑 Blocker.

**[круг 4] Findings Of Round 3 — State In Round 4**

| ID | Круг 3 | Круг 4 — состояние и улика |
|---|---|---|
| **W-R3-01** — запись обхода f63a3c49 шире улики: шаблон оркестратора, своих слов нет | ⚠️ Warning → Q5 | **ЗАКРЫТА ПО ФОРМЕ, ПО СУЩЕСТВУ ПЕРЕШЛА В W-R4-01.** Шаблон отозван (абзац 16:28:14Z), отметки несут слова владельца дословно, подставленных вариантов нет. Наблюдённого признака по-прежнему нет — теперь это записано в самих отметках |
| **W-R3-02** — проверки 8 и 9 просят ЗНАЧЕНИЕ | ⚠️ Warning → Q5 | **ОТКРЫТА** → W-R4-02. Значения не названы; записан `pass` |
| **W-R3-03** — база шага 7.2 `master` сравнивает дерево с самим собой | ⚠️ Warning → Q5 | **ЗАКРЫТА В ЗАПИСИ:** `14-UAT.md:302` — `fd69a26a`, родитель первого коммита 14-01 (замерено). Наблюдение по шагу не названо — это уже пункт 7 |
| **I-R3-01** — ошибка круга 2 об адресате отсрочки 1 | ℹ️ (исправлено) | Закрыта в круге 3 |
| **I-R3-02** — R-14-02 и todo называют 200 строкой `:841` (ветка частоты), основной выход — `:876` | ℹ️ → оркестратору | **ОТКРЫТА.** `14-SECURITY.md:122` и todo `:17` не правились |
| **I-R3-03** — место ответа R-14-02 названо верно | ℹ️ | Без изменений |
| **I-R3-04** — сторонние `POST /register/send-code` с устаревших клиентов | ℹ️ → владельцу | **ОТКРЫТА, продолжается:** ещё 33 в окне круга 4 (I-R4-01) |
| **I-R2-02** — устаревшие записи вне поручения (`STATE.md:29`, строка T-14-19 `14-SECURITY.md`) | ℹ️ | **ОТКРЫТА.** T-14-19 (`14-SECURITY.md:59`) по-прежнему пишет «`status: testing`, девять пустых таблиц отметок, девять `result: [pending]`». `STATE.md:29` по-прежнему пишет «верификация `passed` (12/13), обход человека 9/9 без находок» |
| **I-R2-04** — вербы `verify.artifacts` / `verify.key-links` не разбирают строковые блоки планов | ℹ️ | **ОТКРЫТА** — планы не менялись |

**[круг 4] New Findings Of Round 4**

| ID | Finding | Severity | Evidence | Route |
|---|---|---|---|---|
| **W-R4-01** | Шапка `complete` и девять `result: pass` стоят поверх отметок, которые по правилу самого файла закрытием не считаются. Под каждой таблицей написано: «отметка без наблюдённого признака закрытием не считается». Абзац 16:28:14Z требует: «что увидел, на каком стенде, в каком браузере». А каждая строка отметки сама говорит: «Признаков шагов … владелец не назвал». Запись честна, но противоречит себе: шапка терминальна, а отметки по её же правилу не закрывают проверок. Правило самозаверения зелено по построению — оно считает строки, а не признаки | ⚠️ Warning (запись приёмки; SC4 остаётся воздержанием) | `14-UAT.md:2`, `:46-56`, `:169` и т.д., строки отметок `:173`, `:195`, `:220`, `:245`, `:268`, `:293`, `:315`, `:337`, `:359`; журнал de9e5bcb — три прямые просьбы о признаках | Q6 |
| **W-R4-02** | Проверки 8 и 9 записаны `pass` без значения, вопреки предупреждению оркестратора за 22 с до ответа: «не закроет даже формально… запишу тест 8 как пропущенный с причиной». Проверка, предмет которой — значение, без значения не «пройдена» ни в каком смысле. Честной записью был бы `skipped` с причиной либо явный отказ владельца от проверки. Находки UI WARNING 2 и 3 потому не подтверждены и не сняты | ⚠️ Warning | `14-UAT.md:142-152`, `:337`, `:359`; журнал de9e5bcb 05:42:52Z, 05:43:14Z, 05:43:28Z | Q6 (значения или явный отказ) |
| **I-R4-01** | Продолжение I-R3-04. За 13 ч окна круга 4 на стенд пришло ещё 33 `POST /register/send-code` с устаревших клиентов (IE 7–11, Chrome 35–45, Android 4–5, iPad iOS 8). Все 200, полностраничные, без продолжения на `/register/verify`. Каждый такой запрос отправляет письмо на чужой адрес | ℹ️ Info (вне объёма фазы; ограничение частоты и перечисление адресов — давний долг 14-CONTEXT §Deferred) | Агрегат журналов `nginx-broadcaster` за окно; IP не печатались | Владельцу на усмотрение |
| **I-R4-02** | Поручение называло известным дефектом то, что верб `verification.fingerprint` молча теряет ПЕРВЫЙ путь. На gsd-core 1.16.0 это не воспроизводится. С дублем первым и без него верб вернул 59 файлов и одно и то же значение. Дубль он просто сводит. Запись памяти о дефекте помечает его исправленным в 1.16 — замер с ней совпадает | ℹ️ Info (инструмент) | `fp_r4.json`, `fp_r4_nodup.json` в scratchpad; `lost: set()`, `dups: 0` | Оркестратору — снять оговорку из поручений |

**[круг 4] Self-check (после записи отчёта)**

| Check | Command | Result |
|---|---|---|
| Вердикт читается владельцем статуса | `gsd-tools query verification.status <phaseDir> --pick status` | `human_needed`, код 0 (до записи — `stale`); маршрут — `/gsd-verify-work 14` |
| Отпечаток | `gsd-tools query verification.fingerprint <phaseDir> <дубль> <45 путей>` | 59 покрытых файлов (45 + 14 PLAN/SUMMARY), потерянных путей 0; без дубля — то же значение (I-R4-02); `covered_digest` скопирован из вывода дословно |
| Фронтматтер разбирается | `yaml.safe_load` блока между разделителями | ок: 10 пунктов человеку (9 `still_required`, 1 `discharged` с `resolution`), 6 вопросов (Q1–Q5 + Q6), 3 отсрочки (open, open, closed), блок `re_verification` круга 3 вложен под `previous_round_record`, круг 2 — под ним |
| Разборщик пунктов человеку видит ровно открытые | `gsd-tools query audit-uat --raw` | у `14-VERIFICATION.md` — `status: human_needed`, `items: 9` (проверки 1–9); пункт 10 закрыт по `resolution` |
| Предикат обхода | `gsd-tools phase uat-passed 14 --raw` | `passed: false`; `blockers: ["14-VERIFICATION.md: verification status=human_needed"]`. Все девять `result: pass` предикат читает как проходящие: он видит поле `result`, а не признаки (W-R4-01) |
| Перенос записи — по значениям | скрипт сравнивает каждое поле фронтматтера резервной копии `14-VERIFICATION.pre-round4.md` с новым файлом (`re_verification` круга 3 — с `previous_round_record`) | расхождений **0**: все прежние поля `deferred`, `escalations`, `human_verification` (включая `state_evidence` и `resolution`), `human_verification_round_1`, `owner_questions` Q1–Q5, `decision_coverage`, `flagged_prohibitions` равны прежним; новые поля только добавлены |
| Перенос записи — по строкам | тот же скрипт сверяет каждую непустую строку копии (1407 строк) с новым файлом | потеряна **одна** строка, намеренно: финальная подпись круга 3 переехала в конец §Приложение — запись круга 3 как «Подпись круга 3: …». Сверх неё заменены только шапка круга 3 (`verified`/`score`/`covered_files`/`covered_digest`) и строка `re_verification:`. Блок `re_verification` круга 3 — со сдвигом на два пробела, заголовки тела круга 3 — понижены с меткой «[круг 3]», остальное побайтово |
| Правила записей | `uv run pytest tests/test_planning -q -p no:cacheprovider` | **208 passed** за 16.10 с, включая `test_requirement_completion_follows_verification.py` (SIGN-01…03 `Pending` при `human_needed`) и `test_the_walkthrough_cannot_self_certify.py` (зелено по построению — W-R4-01) |

**[круг 4] Advisory (New Scope, Unevidenced)**

Нет. Узкий гейт улик (#3304) этому кругу формально не применим: блока `gaps` не было ни в одном круге, и шаг 0 ведёт прогон в полном объёме. Каждая новая находка несёт детерминированную улику: замер, прогон, чтение с номерами строк или метку времени первичной записи. Ни одна не 🛑 Blocker и ни одна не опровергает истину фазы.

**[круг 4] Escalation — решение владельца, которое я не вправе принять за него**

Эскалация CR-02 / WR-07 **закрыта** с круга 2 и не переоткрывается. Развилка круга 4 — вопрос **Q6**: засчитывается ли заявление владельца без признаков закрытием обхода. Решить её может только владелец, потому что правило «отметка требует признака» — его собственное (D-02). В отличие от Q5 круга 3, от этого ответа вердикт зависит. Ветвь (а) с признаками и значениями даёт следующему кругу основание для `passed`. Ветвь (б) тоже даёт `passed`, но через подписанные `overrides`, если владелец явно откажется и от проверок 8 и 9. Ветвь (в) оставляет `human_needed` до обхода.

**[круг 4] Deferred Items**

Круг 3 → круг 4: три пункта. **Открыто 2, закрыто 1** — без изменений.

| # | Item | Круг 3 | Круг 4 — состояние и улика |
|---|---|---|---|
| 1 | 23 запрета планов 14-01…14-07 — `flagged-unverified` / `verification: none` | ОТКРЫТ, адресат есть | **ОТКРЫТ, АДРЕСАТ ТОТ ЖЕ** — бэклог следующей вехи (todo `classify-420…`). Реестр и todo не правились |
| 2 | CR-01 — гард источника запроса на девяти формах | ОТКРЫТ; риск принят (R-14-01) | **ОТКРЫТ.** Код не менялся: 1 вызов из 10 (`:691`). Адресат-фаза не назначен |
| 3 | `hx-push-url` на формах авторизации | ЗАКРЫТ Фазой 15 | **ЗАКРЫТ** — без изменений |

Отсрочки статус не меняют. Запреты зелёными не засчитаны (`flagged_prohibitions: 23`).

**[круг 4] Human Verification Required**

Круг 4: **десять пунктов, у каждого ровно одно состояние.** 1–9 — `still_required`, 10 — `discharged`. Поимённые улики — во фронтматтере (`round_4_state_evidence`; `state_evidence` круга 3 сохранено рядом). Общее основание пунктов 1–9 — §Обход 2026-10-07…08.

**Как закрыть пункты 1–9 одним ответом (ветвь (а) Q6).** По строке на проверку, своими словами:
- стенд и день, браузер и ОС;
- что увидели на шагах. Для 1.5 — первые символы `access_token` до и после. Для 8 — куда встал фокус после Tab, что объявил скринридер и какой это скринридер. Для 9.1 — выглядела ли вторая кнопка живой, был ли у неё индикатор.

**Предусловия (D-02, `14-UAT.md` §Предусловия):** рабочий SMTP на стенде; ящики П-2/П-3; админ и пользователь; чистые Chrome и Firefox; выключаемый JS; экраны 375px и десктоп. **Правило останова:** письма не доходят → обход останавливается, вопрос владельцу; код из базы не подставляется.

**[круг 4] 1. Полный вход в браузере — UAT проверка 1 — still_required**

**Test:** Открыть `/login`, ввести неверный пароль, затем верный; войти заблокированным.
**Expected:** Неверный пароль перерисовывает карточку БЕЗ перезагрузки, email остаётся, вкладка — «Вход — Broadcaster»; верный — кабинет ПОЛНОЙ загрузкой, `access_token` сменилась.
**Why human:** Рантайм подмены, заголовок вкладки и смена cookie сервером не измеряются. **Круг 4:** заявление без признаков и без значения `access_token` (W-R4-01).

**[круг 4] 2. Регистрация до экрана кода и завершение — UAT проверка 2 — still_required**

**Test:** `/register` → новый адрес → экран кода; на завершении — короткий, затем годный пароль.
**Expected:** Экран кода без перезагрузки, адрес `/register`, вкладка меняет заголовок; короткий пароль оставляет имя; завершение — кабинет полной загрузкой с пробным сроком.
**Why human:** Рантайм подмены, адресная строка, вкладка. **Круг 4:** W-R4-01.

**[круг 4] 3. Подтверждение почты настоящим письмом — UAT проверка 3 — still_required**

**Test:** Код из РЕАЛЬНОГО ящика; неверный код; «Отправить код повторно»; F5 на шаге.
**Expected:** Письмо доходит, неверный код оставляет набранное, повтор присылает новое письмо, F5 возвращает к началу.
**Why human:** Доставка настоящего письма (D-02). **Круг 4:** W-R4-01; доставка двух писем не названа.

**[круг 4] 4. Восстановление пароля целиком — UAT проверка 4 — still_required**

**Test:** `/forgot-password` → код из письма → новый пароль → `/login` → старый пароль → новый пароль.
**Expected:** Плашка «Пароль успешно изменён. Войдите с новым паролем.» на `/login` переживает ошибку формы; вход новым паролем проходит.
**Why human:** Доставка письма, плашка шелла. **Круг 4:** W-R4-01.

**[круг 4] 5. Возврат из-под чужой личности — UAT проверка 5 — still_required**

**Test:** Под чужой личностью нажать «ВЕРНУТЬСЯ В АДМИНА».
**Expected:** Адрес `/admin`, вкладка админки, полосы нет, cookie без действующего лица.
**Why human:** Смена cookie и заголовка через границу шеллов (D-12). **Круг 4:** W-R4-01.

**[круг 4] 6. Менеджер паролей — UAT проверка 6 — still_required**

**Test:** Пять наблюдений в Chrome и Firefox на чистом профиле; база — путь без JS.
**Expected:** Предложение сохранить/обновить пароль там, где оно есть без JS; регрессия — владельцу.
**Why human:** Эвристики браузера. **Круг 4:** W-R4-01; браузеры и итог базы без JS не названы.

**[круг 4] 7. Карточка на 375px и на десктопе — UAT проверка 7 — still_required**

**Test:** Семь экранов на узком и широком экране; промежутки сверить с деревом ДО фазы (`fd69a26a`).
**Expected:** Подзаголовок под брендом, промежутки как до фазы, индикатор у кнопки, без горизонтальной прокрутки.
**Why human:** Визуальное суждение. **Круг 4:** W-R4-01; база 7.2 в записи исправлена (W-R3-03 закрыта), наблюдение не названо.

**[круг 4] 8. Фокус и объявление после свопа — UAT проверка 8 — still_required**

**Test:** На экране кода ввести неверный код, нажать Tab; то же со скринридером и на экране входа.
**Expected:** ЗАПИСАНО, куда встал фокус и что объявил скринридер (шаг 8.3 — «записать, какой»).
**Why human:** Механизма нет; куда при этом попадает фокус — только наблюдение. **Круг 4:** значение не названо, записан `pass` (W-R4-02). Ветвью (б) Q6 не закрывается — только значением или явным отказом.

**[круг 4] 9. Вторая кнопка на экранах кода — UAT проверка 9 — still_required**

**Test:** Нажать «Отправить код повторно», пока «Подтвердить» в полёте.
**Expected:** ЗАПИСАНО, выглядит ли вторая кнопка живой и есть ли у неё индикатор (9.1); отброс второго запроса (9.2) доказан машиной.
**Why human:** Видимость — суждение глазами. **Круг 4:** значение 9.1 не названо (W-R4-02). Ветвью (б) Q6 не закрывается.

**[круг 4] 10. Решение владельца по 23 запретам — discharged**

**Test:** Назначить адресата и/или принять решение по 23 запретам (14-01#0…14-07#2).
**Expected:** У каждой строки — диспозиция либо записанный адресат следующей вехи.
**Why human:** Помеченный запрет уровня суждения не поглощается вердиктом молча. **Закрыт в круге 3 второй ветвью** (адресат — бэклог следующей вехи); в круге 4 без изменений. Сами запреты остаются непринуждёнными — отсрочка 1.

**[круг 4] Owner Questions**

Полные формулировки, рекомендации, ответы и места исполнения — во фронтматтере `owner_questions`.

- **Q1** — SIGN-01…03 при `human_needed`. Исполнено в круге 3 (`cbbcc5e9`); в круге 4 без изменений, правило записей зелено.
- **Q2** — `result: pass` ×9 при отозванном обходе. Исполнено в круге 3; в круге 4 снятие повторено (абзац 16:28:14Z), заполнение снова без признаков → W-R4-01.
- **Q3** — адресат 23 запретов. Закрыт в круге 3; пункт 10 discharged.
- **Q4** — R-14-02. Исполнено в круге 3 (`9cce13ea`); I-R3-02 открыта.
- **Q5** — проводился ли обход глазами, где, когда и кем. **Ответ (2026-10-07T16:27Z…2026-10-08T05:44Z):** перезапуск обхода, затем девять заявлений «я все проверил». Где и когда — не сказано, хотя спрошено трижды. **Исполнено:** `f447c5ed`. Временное возражение круга 3 снято, возражение стенда ослабло. Признаков нет → Q6.
- **Q6 (новый)** — засчитать ли заявление без признаков закрытием проверок 1–7 вопреки D-02 и что делать с проверками 8 и 9. **Рекомендация:** (а) по строке признаков на проверку, с значениями для 8 и 9; иначе (б) явное подписанное решение `overrides` для 1–7 плюс значения или явный отказ для 8 и 9; иначе (в) вернуть шапку обхода в нетерминальное состояние.

**[круг 4] Gaps Summary**

**Изъянов, блокирующих достижение цели, не найдено** — ни в одном из четырёх кругов.

Цель фазы — «неверный код или пароль перестаёт стирать заполненную форму» — **истинна в дереве, и истинной её делает СЕРВЕР**:
- 422 стоит литералом в `respond_field_error`;
- эхо едет параметром в автоэкранирующий шаблон;
- путь без JS получает ту же страницу прямо в ответ на POST.

В круге 4 это снова подтверждено прогоном 27 именованных правил со значимыми утверждениями на обоих транспортах — на дереве, где вне `.planning/` с круга 2 не изменилось ничего.

**Почему `human_needed`, а не `passed` и не `gaps_found`.**
- Правило 1 (`gaps_found`) не срабатывает: ни одна истина не FAILED, ни один артефакт не MISSING или STUB, ни одна связь не NOT_WIRED, блокеров нет.
- Срабатывает правило 2: девять пунктов человеку `still_required`. Это воздержание бэкстопа по SC4 и девять проверок обхода, в записи которых нет ни одного наблюдённого признака (W-R4-01). У проверок 8 и 9 сверх того нет значения (W-R4-02).
- `passed` на этой записи без решения владельца вывести нельзя. Под каждой таблицей файла стоит его же правило: «отметка без наблюдённого признака закрытием не считается». Владелец сам выбрал перезапуск на этом условии. Отменить правило вправе он, а не я, — Q6.
- Выбор `human_needed` — не уход от суждения. Суждение вынесено: в записи есть заявление, но нет наблюдения. Ветвь, на которой заявление станет закрытием, принадлежит владельцу.

Что закрыто в этом круге: W-R3-03 (база шага 7.2 в записи) и W-R3-01 в форме (шаблона больше нет). Что сдвинулось: два из трёх оснований круга 3 против записи обхода сняты (время, отсутствие заявления), третье (стенд) ослабло. Осталось одно — признаков нет.

Подпись круга 4: _Verified: 2026-10-08T05:50:52Z (круг 4; круг 3 — 2026-10-07T15:58:55Z; круг 2 — 2026-10-07T12:31:06Z; круг 1 — 2026-09-23T08:15:00Z)_
_Verifier: Claude (gsd-verifier)_

## Приложение — запись круга 3 дословно

Тело отчёта круга 3 (коммит `93e1d4d2`, дерево `9cce13ea`, 2026-10-07T15:58:55Z) перенесено ЦЕЛИКОМ и ДОСЛОВНО как запись своего дня, а не как действующий вердикт. Единственное механическое преобразование — то же, что круги 2 и 3 применили к записям предыдущих кругов. Строки заголовков (`#`…`####`) переписаны в жирный текст с меткой «[круг 3]», чтобы разборщики пунктов человеку (`src/uat.cts`) не собрали их второй раз. Все прочие строки совпадают побайтово; это проверено скриптом при сборке, см. §Self-check. Действующие состояния каждого пункта — в разделах круга 4 выше. Подпись круга 3 перенесена в конец этого приложения.

**[круг 3] Phase 14: Авторизация на htmx — Verification Report**

**Phase Goal:** неверный код или пароль перестаёт стирать заполненную форму — заявленный выигрыш вехи именно в ОШИБКЕ, а не в успехе
**Verified:** 2026-10-07T15:58:55Z (круг 3; круг 2 — 2026-10-07T12:31:06Z; круг 1 — 2026-09-23T08:15:00Z)
**Status:** human_needed
**Re-verification:** Да — КРУГ 3. HEAD `9cce13ea`. Повод: вердикт круга 2 прочитался `stale`, потому что изменились покрытые `14-UAT.md` и `14-SECURITY.md`. Ни в одном круге блока `gaps` не было, поэтому по букве шага 0 это снова прогон в полном объёме: все 13 истин перепроверены, а не перенесены. Отчёт круга 2 перенесён целиком в §Приложение — запись круга 2, отчёт круга 1 — в §Приложение — запись круга 1. Оба дословно.

**Что изменилось с круга 2 (замерено, а не взято из поручения).**
- `git log cbbcc5e9..HEAD` — ровно два коммита: `f63a3c49` (обход) и `9cce13ea` (ответ на Q4).
- `git diff --name-only cbbcc5e9..HEAD` — только `.planning/`: 14-SECURITY.md, 14-UAT.md и новый todo.
- `git diff --name-only feaa701f..HEAD -- . ':!.planning'` — **0 строк**: ни продуктовый код, ни правила с круга 2 не менялись.

**Чего не наследую.** Ни `human_needed` круга 2, ни `complete` из шапки обхода, ни формулировок поручения. Ответы владельца, переданные оркестратором, сверены с первичными записями: журналы сессий, коммиты, файлы. Итог круга — `human_needed`, и стоит он на собственной улике этого круга. Это не воздержание от суждения: я рассмотрел запись обхода и счёл, что наблюдения она не несёт (§Обход 2026-10-07).

**Method.** Goal-backward; must-haves — те же четыре критерия ROADMAP и истины фронтматтера семи планов. Улики круга:
- **Прогон.** 27 именованных правил одним вызовом `pytest` — 27 passed за 17.30 с: 25 правил круга 2 плюс два правила, на которые опирается запись Q4. После записи отчёта — `tests/test_planning` целиком (§Self-check).
- **Чтение дерева.** Номера строк выписаны в таблицах.
- **Две первичные улики вне дерева, только чтение.**
  - Журналы сессий оркестратора: из них взяты только метки времени и тексты ответов владельца.
  - Журналы контейнеров стенда `web-broadcaster` и `nginx-broadcaster`: из них сняты только агрегированные счёты маршрутов авторизации за 2026-10-07 и семейство клиента. IP-адреса не печатались, ничего не запускалось и не менялось.

**[круг 3] Goal Achievement**

**[круг 3] Observable Truths**

| # | Truth | Status | Evidence (круг 3) |
|---|-------|--------|----------|
| 1 | **SC1 / SIGN-02.** Неверный код или пароль перерисовывает форму С СОХРАНЕНИЕМ введённого: 422 + эхо в `value=`; свойство создаёт СЕРВЕР | ✓ VERIFIED | Код с круга 2 не менялся (diff вне `.planning/` с `feaa701f` пуст). ПРОГОН круга 3: правила 1–4, трасер входа, правило 24 — PASS |
| 2 | **SC2 / SIGN-01.** Все 9 форм авторизации идут через `hx-post` и остаются рабочими без JS | ✓ VERIFIED | Перемерено: `grep -rn 'form_wrapper(' app/templates/auth/` → 9. Прогон: правила 5–7, 10 — PASS |
| 3 | **SC3 / SIGN-03.** Успех авторизации уходит `HX-Redirect` через границу шеллов; `HX-Location` — по летописи | ✓ VERIFIED | По летописи — разбор §Criterion 3 круга 2 в силе, источник не менялся. Прогон: правила 8–9, 13–15, 19–21 — PASS |
| 4 | **SC4.** Вход, регистрация, подтверждение почты и восстановление пароля проходят в браузере целиком | ⚠️ `insufficient_spec` (backstop abstention) | **НЕ проверяется кодом и НЕ доказано наблюдением.** `verification: backstop` у всех семи планов. Единственный канал — обход человека. Его запись 2026-10-07 (`14-UAT.md`, `status: complete`, 9 заполненных отметок) рассмотрена в §Обход 2026-10-07: наблюдения она не несёт (W-R3-01). Истина не FAILED — улики против поведения нет, машинная половина зелена; она не доказана |
| 5 | Враждебный ввод возвращается в `value=` ТОЛЬКО экранированным, на обоих транспортах | ✓ VERIFIED | Прогон: правила 2 и 24 — PASS |
| 6 | Пароль не возвращается НИКОГДА — ни в `value=`, ни в теле, ни в контексте шаблона | ✓ VERIFIED | Прогон: правила 1, 11 — PASS |
| 7 | Отказ 422 не несёт cookie сессии ни на одном транспорте; заблокированный с ВЕРНЫМ паролем получает 422 с `BLOCKED_LOGIN_ERROR` | ✓ VERIFIED | Прогон: правила 1, 12 — PASS |
| 8 | Смена экрана — 200 на обоих транспортах; подписанный токен шага едет ТОЛЬКО скрытым полем | ✓ VERIFIED | Код не менялся; прогон правил 3, 4, 23 (экран кода на обоих транспортах) — PASS. Решение 15-FORM-DECISIONS §3 в силе |
| 9 | Возврат из-под чужой личности: три ветки, cookie перезаписана НА ЭТОМ ЖЕ ответе, следующий `GET /admin` отдаёт админку | ✓ VERIFIED (behaviour-dependent — доказано прогоном, не присутствием) | Прогон круга 3: правила 13–15 — PASS |
| 10 | Восстановление пароля под чужой личностью остаётся запрещённым на ВСЕХ четырёх шагах, на обоих транспортах | ✓ VERIFIED (behaviour-dependent) | Прогон: правила 16–17 — PASS |
| 11 | Счётчик отставания вехи — ИМЕНОВАННЫЙ НОЛЬ, доказанный НЕ ВАКУУМНЫМ | ✓ VERIFIED | Прогон: правило 10 — PASS; модуль гейтов не менялся с круга 2 |
| 12 | Реестр `AUTH_SCREENS` накрывает ВСЕ семь страниц второго шелла; заголовок фрагмента и заголовок страницы сличаются | ✓ VERIFIED | Прогон: правила 18 и 25 — PASS |
| 13 | Записи фазы приведены в объявленную форму: летописи критериев 2 и 3, строки Research, SIGN-03, рамки вехи; окно 63 переведено ЗАМЕРОМ; артефакт обхода размечен | ✓ VERIFIED | Истина плана 14-07 о ПОСТАВЛЕННОЙ им разметке: летописи и окно 63 не менялись с круга 2. Артефакт обхода и сегодня несёт 9 проверок, 9 таблиц, предусловия и правило останова. Его жизненный цикл после плана (`testing` → `complete` → `human_needed` → `testing` → `complete`) — дело других процессов. Сегодняшнее заполнение — находка W-R3-01, а не провал истины плана |

**Score:** 12/13 truths verified (0 present-but-behaviour-unverified; 1 backstop abstention routed to human). Круг 2 → круг 3: тот же счёт и те же статусы истин. Изменились состояния пунктов человеку: пункт 10 закрыт, пункты 1–9 по-прежнему открыты, но уже по другой причине — запись обхода есть, наблюдения в ней нет.

**[круг 3] Обход 2026-10-07 — что эта запись закрывает и чего не закрывает**

Это главный предмет круга: от него зависит, переходит ли SC4 из воздержания в VERIFIED и закрываются ли пункты 1–9.

**Что записано.** `14-UAT.md` после `f63a3c49`:
- шапка `status: complete`;
- девять `result: pass`, у каждого строка `history:` с прежним значением;
- `## Summary` — `passed: 9`;
- в каждой из девяти таблиц отметок одна строка: `| 2026-10-07 | Chrome + Firefox / Linux | chubav | наблюдены признаки шагов N.1–N.k так, как они записаны в таблице шагов проверки N; подтверждено владельцем словом «pass» в `/gsd-verify-work 14` |`.

Три счёта сходятся: `checks_declared` 9, разделов 9, таблиц 9, заполнено 9. Поэтому правило самозаверения зелено. Но само правило в шапке говорит, чего оно не доказывает: «Он НЕ утверждает, что обход ПРОЙДЕН… утверждает единственное: ЗАПИСЬ о прохождении не шире собственных отметок». Значит, заполнены ли отметки НАБЛЮДЕНИЕМ — суждение верификатора, а не правила.

**Первичные улики (журналы сессий оркестратора, только метки времени и ответы владельца):**

| Время (UTC) | Событие | Источник |
|---|---|---|
| 2026-10-06 09:15:27 | Владелец на вопрос об обходе Фазы 14 выбирает «Пройти обход позже» | сессия 5613219b |
| 2026-10-07 15:28:22 | После круга 2: «Вернуть в Pending», про `result: pass` ×9 — «Сброшу при обходе» | сессия 5237445f |
| 15:36:47 | Запущен `/gsd-verify-work 14` (после `/clear`) | сессия e571cfb6 |
| 15:37:59 | «Пройти обход заново (Recommended)»; предусловия П-1…П-7 — «Всё готово» | e571cfb6 |
| 15:38:47 | Проверка 1 — «pass» | e571cfb6 |
| 15:39:07 | Форма отметок — «pass = признаки из таблицы» | e571cfb6 |
| 15:39:22 · :29 · :34 · :40 · 15:40:00 · :05 · :13 · :21 | Проверки 2–9 — «pass» (восьмая набрана «pas»): 8 ответов за 59 с, в среднем 7 с на проверку | e571cfb6 |
| 15:40:48 | «Chrome+Firefox / Linux, chubav» — вариант, предложенный оркестратором | e571cfb6 |
| 15:41:27 | Коммит `f63a3c49` «complete UAT — 9 passed, 0 issues» | git |

Ни в одной сессии 2026-10-06…07 нет заявления владельца, что обход был проведён раньше. Ответ 15:37:59 — выбор «пройти обход **заново**», то есть начать его в этот момент.

**Стенд.** На этой машине работает боевой стенд (`web-broadcaster`, `nginx-broadcaster`; образ с кодом фазы — `POST /login` отвечает 204 по пути `HX-Redirect`). Его журнал за 2026-10-07 (00:00–15:50Z):
- **0** `POST /login` с 422 — проверка 1 и шаг 6.2 порождают его обязательно;
- **0** запросов `/register/verify`, `/register/resend-code`, `/register/complete` — проверки 2, 3, 6;
- **0** запросов `/forgot-password/*` — проверки 4 и 6.4;
- **0** `POST /impersonation/stop` — проверка 5.

27 `POST /register/send-code` за день пришли с клиентов Chrome 43/45 на Android 4.4 и Windows 8.1 и получили полностраничный ответ (6251 байт). Это не подмена htmx, а сторонний трафик. Единственный такой запрос в окне обхода, 15:35:29Z, — тоже он.

**Что это доказывает и чего не доказывает.** Журнал стенда НЕ опровергает обход на ДРУГОМ стенде: владелец уже проверял «на другом сервере» в Фазе 11. Но он снимает единственное доступное подтверждение. Временная линия весит больше. Проверки 3 и 4 требуют доставки настоящих писем; проверка 6 — пяти наблюдений в двух браузерах на чистых профилях плюс базы без JS; проверка 8 — скринридера; проверка 7 — двух ширин экрана на семи экранах. Ответы на них даны с шагом 5–20 с, через 48 с после решения начать обход заново. Пройти девять проверок в этом окне физически нельзя. Сказать «проводилось раньше» владелец не сказал.

**Сличение с прецедентом Фазы 13**, где вердикт `passed` встал на «pass» без детализации признаков:

| | Фаза 13 (`13-UAT.md`, канонизация 2026-09-21) | Фаза 14 (`14-UAT.md`, 2026-10-07) |
|---|---|---|
| Слова владельца о наблюдении | СВОИ, на прямой вопрос приёмки: «все было на живом стенде с реальными аккаунтами telegram» | Нет; «pass» ×9 и выбор вариантов, сформулированных оркестратором |
| Окружение в отметке | «Chrome 152 / macOS 15», «Александр» — названо наблюдателем | «Chrome + Firefox / Linux» — вариант из предложенных |
| Время | — | 94 с на девять проверок, 48 с после «пройти заново» |
| История этого обхода | — | Тот же «pass» ×9 уже записывался (54ebbf56) и был ОТОЗВАН владельцем: «Обход Фазы 14 глазами НЕ ПРОВОДИЛСЯ» |
| Улика против | Нет | Стенд без единого запроса проверок 1, 3, 4, 5 |

Прецедент Фазы 13 принимал ЛИЧНОЕ подтверждение наблюдения. Здесь его нет, а улики против есть. Поэтому прецедент не переносится.

**Вывод по пунктам.** Пункты 1–9 — `still_required`. Это не обвинение и не провал истины: улики, что поведение неверно, нет, машинная половина зелена (27/27). Вывод о ЗАПИСИ: ни одна из девяти отметок не несёт наблюдения, которое я могу приписать проведённому обходу. У трёх пунктов есть второе, независимое основание, и оно останется даже после подтверждения владельцем:
- **проверки 8 и 9** спрашивают ЗНАЧЕНИЕ: куда встал фокус и что сказал скринридер; выглядела ли вторая кнопка живой. «Наблюдены так, как записаны» значения не несёт (W-R3-02);
- **шаг 7.2** сравнивает с `master`, в котором код фазы уже есть, — то есть дерево само с собой (W-R3-03).

Закрыть пункты 1–9 может один прямой ответ владельца своими словами или обход — Q5.

**Граница поступка.** `14-UAT.md` верификатор не правил ни строкой. Шапку `complete` и `result: pass` не трогал. Вернуть их в нетерминальное состояние или подтвердить — решение владельца (Q5).

**[круг 3] Required Artifacts**

| Artifact | Expected | Status | Details (круг 3) |
|---|---|---|---|
| `app/pages/htmx.py`, `app/pages/auth.py`, `app/main.py` | Выходы слоя; 10 обработчиков; реестр экранов | ✓ VERIFIED | Без изменений с круга 2 (diff вне `.planning/` пуст); 10 `@router.post` перемерено |
| `app/templates/auth/**`, `auth_base.html`, `base.html`, `components/*`, `includes/*` | Разметка экранов, якорь, макросы | ✓ VERIFIED | Без изменений; 9 `form_wrapper(` перемерено |
| `tests/test_pages/*`, `tests/test_templates/test_htmx_markup_gates.py` | Правила фазы | ✓ VERIFIED | Без изменений; 27 именованных правил — PASS |
| `.planning/phases/14-…/14-UAT.md` | Артефакт обхода критерия 4 | ✓ VERIFIED как артефакт (разметка на месте) · ⚠️ запись наблюдения — W-R3-01 | Предмет §Обход 2026-10-07 |
| `.planning/phases/14-…/14-SECURITY.md` | Реестр угроз; ответ на Q4 | ✓ VERIFIED | R-14-02 перепринят с исправленным основанием; `threats_open: 0` |

Подробные таблицы трёх уровней (артефакты, связи, поток данных) — в §Приложение — запись круга 2. Источник с тех пор не менялся, поэтому их выводы в силе без пересмотра. Ни одного MISSING, STUB или ORPHANED.

**[круг 3] Key Link Verification**

Все семь связей круга 2 — ✓ WIRED; прогон их правил (1, 13, 15, 16–17, 19–21, 8–9) в круге 3 — PASS. Строки источника те же: файлы не менялись.

**[круг 3] Data-Flow Trace (Level 4)**

Шесть цепочек круга 2 — ✓ FLOWING (эхо email, двух кодов и имени; подписанный токен; намеренно пустой пароль по D-04). Источник не менялся.

**[круг 3] Behavioural Spot-Checks**

**Круг 3: 27 именованных правил одним вызовом `pytest` по идентификаторам узлов — 27 passed за 17.30 с** (`-p no:randomly -p no:cacheprovider`). Это 25 правил таблицы круга 2 (номера 1–25 те же, что в приложении) и два правила, на которые опирается запись Q4:

| # | Proves | Named rule | Result (круг 3) |
|---|---|---|---|
| 1–25 | См. таблицу круга 2 (§Приложение — запись круга 2, Behavioural Spot-Checks) | те же 25 идентификаторов узлов | ✓ 25 PASS |
| 26 | 422 на неизвестном адресе восстановления (оракул R-14-02, ветка «неизвестен») | `tests/test_pages/test_auth_transport.py::test_an_unknown_email_keeps_the_address_and_answers_422_on_both_transports` | ✓ PASS |
| 27 | 422 на занятом адресе регистрации (оракул R-14-02, ветка «занят») | `tests/test_pages/test_registration.py::test_send_code_rejects_existing_email` | ✓ PASS |

Суита целиком НЕ перезапускалась. Полный прогон оркестратора — 4084 passed на `feaa701f` — взят входом, а не доказательством. С `feaa701f` вне `.planning/` не изменилось ничего (замерено).

Независимые замеры круга 3:

| Measurement | Command | Result |
|---|---|---|
| Коммиты после круга 2 | `git log cbbcc5e9..HEAD` | 2: `f63a3c49`, `9cce13ea` |
| Изменения вне `.planning/` с `feaa701f` | `git diff --name-only feaa701f..HEAD -- . ':!.planning'` | **0** |
| Код фазы в `master` | `git merge-base --is-ancestor 5b3b91c5 origin/master` | да (основание W-R3-03) |
| Формы авторизации | `grep -rn 'form_wrapper(' app/templates/auth/` | 9 |
| `is_same_origin` | `grep -n is_same_origin app/pages/auth.py` | импорт + `:691` из 10 `@router.post` |
| `verified_at` | `grep -n verified_at app/pages/auth.py` | `:408, :443, :916, :950` |
| `autofocus`/`tabindex`/`aria-live` | `grep -rnE … app/templates/auth/ auth_base.html` | 0 |
| `error=` у макроса поля | `grep -rn 'field(' app/templates/auth/ \| grep -c 'error='` | 0 |
| Выходы `forgot_password_send_code` | чтение `auth.py:790-880` | 422 — `:818`; 200 — `:841` (частота), `:876` |
| Реестр запретов | `yaml.safe_load` реестра, отбор по плану | 23 строки 14-xx, все `unclassified`/`unresolved`; всего таких 420 |
| Покрытие решений | `check.decision-coverage-verify <phaseDir> 14-CONTEXT.md` | 15/15, `not_honored: []` |
| Долговые метки | `grep -E 'TBD\|FIXME\|XXX'` по 45 покрытым файлам | 0 |
| Время ответов обхода | журнал сессии e571cfb6 | 9 «pass» за 94 с (15:38:47–15:40:21Z) |
| Запросы обхода на стенде | `docker logs web-broadcaster`/`nginx-broadcaster`, агрегат за 2026-10-07 | 0 запросов проверок 1, 3, 4, 5 |

**[круг 3] Probe Execution**

Проб в дереве нет и фазой не объявлено (`find scripts -path '*/tests/probe-*.sh'` → 0). Шаг пропущен по отсутствию предмета. Без изменений с кругов 1–2.

**[круг 3] Requirements Coverage**

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| **SIGN-01** | 14-01…14-07 | 9 форм авторизации идут через htmx | ✓ SATISFIED (машинно); рантайм подмены — за человеком | Истина 2; правила 5–7. Остаток — §Human Verification 1–5 |
| **SIGN-02** | 14-01…14-05, 14-07 | Неверный код или пароль перерисовывает форму с сохранением введённого | ✓ SATISFIED | Истины 1, 5, 6, 7; правила 1–4, 11–12, 22, 24. **Цель фазы достигнута сервером** |
| **SIGN-03** | 14-01, 14-03, 14-05, 14-06, 14-07 | Успех — `HX-Redirect`; `HX-Location` — у возврата (по летописи) | ✓ SATISFIED | Истина 3; правила 8–9, 13–15, 19–21 |

**Записи требований.** `REQUIREMENTS.md:60-62` — `[ ]`, `:160-162` — `Pending`, летопись `:64` — исполнение Q1 (`cbbcc5e9`). Эта запись совпадает с вердиктом круга `human_needed`, и правило записей зелено (§Self-check). Отметки не ставлю и не прошу: вердикт не `passed`. Сирот нет: прослеживаемость `:160-162` и сводка `:506` относят к Фазе 14 ровно SIGN-01…03, и все три заявлены планами.

**[круг 3] Decision Coverage**

15/15 отслеживаемых решений `14-CONTEXT.md` опознаны, `not_honored: []`. Перемерено в круге 3. Оговорка: верб без явного пути к CONTEXT.md отвечает `skipped: CONTEXT.md missing`, с явным путём — 15/15. Это поведение верба, не фазы.

**[круг 3] Anti-Patterns Found**

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` в 45 покрытых файлах круга 3, включая 14-UAT.md, 14-SECURITY.md и оба todo | — | **Ноль.** Гейт долговых меток зелёный |
| — | — | Отключённые тесты, пустые реализации, статические возвраты | — | Ноль; код и правила не менялись с круга 2 |

**[круг 3] Findings Handed Over By Hand (code review and UI review)**

Счёт: 15 находок. В круге 2 закрыто 2 и открыто 13; в круге 3 — так же, **закрыто 2, открыто 13**. Код не менялся, поэтому ни одна открытая находка не закрылась. У WR-03 изменилась запись: риск перепринят с исправленным основанием, и у починки появился адресат. Полные улики круга 2 по каждой строке — в приложении.

| ID | Severity in review | Круг 2 | Круг 3 — состояние и улика |
|---|---|---|---|
| **CR-01** — девять из десяти POST без `is_same_origin` | Critical, pre-existing | ОТКРЫТА; отсрочка 2; T-14-08 / R-14-01 | **ОТКРЫТА.** Перемерено: 1 вызов из 10 (`:691`) |
| **CR-02** — подтверждённый токен восстановления воспроизводим | Critical, pre-existing | ЗАКРЫТА решением владельца (T-14-21, R-14-03) | **ЗАКРЫТА** (без изменений). Изъян в коде по решению: `verified_at` — `:408, :443, :916, :950` |
| **WR-07 / CR-02 (следствие)** | Warning | ЗАКРЫТА (летопись у правила, 81894644) | **ЗАКРЫТА** (без изменений); правило 21 — PASS |
| **WR-01** — `register_verify` / `register_resend_code` без `purpose` | Warning | ОТКРЫТА | **ОТКРЫТА.** `:394`, `:474` — только `if not payload:` |
| **WR-02** — пути страницы и фрагмента не делят контекст | Warning | ОТКРЫТА (латентная) | **ОТКРЫТА** (латентная); правило 7 — PASS |
| **WR-03** — оракул кодов 422/200 на отправке кода | Warning | ОТКРЫТА; W-R2-02, Q4 | **ОТКРЫТА в коде, риск перепринят**: R-14-02 с исправленным основанием (9cce13ea); адресат починки — todo `send-code-status-reveals-account` |
| **WR-04** — сбой отправки письма выдаётся за успех | Warning | ОТКРЫТА | **ОТКРЫТА** — код не менялся |
| **WR-05** — четыре скопированных тела выдачи кода | Warning | ОТКРЫТА | **ОТКРЫТА** — код не менялся |
| **WR-06** — магическое `6` длины пароля | Warning | ОТКРЫТА | **ОТКРЫТА** — код не менялся; STATE.md:27 держит её до закрытия вехи |
| **IN-01** — `_respond_by_transport` теряет заголовки | Info | ОТКРЫТА | **ОТКРЫТА** — код не менялся |
| **IN-02** — страж пароля ловит только ключ `password` | Info | ОТКРЫТА | **ОТКРЫТА** — код не менялся |
| **IN-03** — `created_at.replace(tzinfo=…)` | Info | ОТКРЫТА | **ОТКРЫТА** — код не менялся |
| **UI WARNING 1** — 422 не помечает поле | Warning | ОТКРЫТА | **ОТКРЫТА.** `error=` — 0 (перемерено) |
| **UI WARNING 2** — ни фокуса, ни живой области после свопа | Warning | ОТКРЫТА; пункт человеку 8 | **ОТКРЫТА.** 0 совпадений; наблюдение не записано — пункт 8 still_required (W-R3-02) |
| **UI WARNING 3** — вторая кнопка живая на экранах кода | Warning | ОТКРЫТА; пункт человеку 9 | **ОТКРЫТА.** Отброс — PASS; видимость не записана — пункт 9 still_required (W-R3-02) |

**Ни одна из этих находок не опровергает истину фазы**, поэтому ни одна не поднята до 🛑 Blocker. Основание то же, что в кругах 1–2.

**[круг 3] Findings Of Round 2 — State In Round 3**

| ID | Круг 2 | Круг 3 — состояние и улика |
|---|---|---|
| **W-R2-01** — `14-UAT.md` противоречит сам себе (шапка `human_needed`, отметки пусты, `result: pass` ×9) | ⚠️ Warning → Q2 | **ЗАКРЫТА ПО ФОРМЕ, ПО СУЩЕСТВУ ПЕРЕШЛА В W-R3-01.** Противоречия полей больше нет: шапка `complete`, 9 отметок, `result: pass` ×9, `history:` у каждого. Согласованность достигнута заполнением, которое наблюдения не несёт |
| **W-R2-02** — основание R-14-02 опровергнуто в части кодов | ⚠️ Warning → Q4 | **ЗАКРЫТА** ответом на Q4: перепринятие с исправленным основанием (9cce13ea); проверено чтением и замером. Остаток — I-R3-02 |
| **W-R2-03** — правило записей красное при `Complete` + `human_needed` | ⚠️ Warning → Q1 | **ЗАКРЫТА** ответом на Q1: SIGN-01…03 → `Pending` (cbbcc5e9); правило зелено при вердикте круга 3 (§Self-check) |
| **I-R2-01** — запреты Фазы 14 не решены, отсрочка 1 без адресата | ℹ️ → Q3 | **ЗАКРЫТА в части адресата:** адресат записан 2026-10-06 (I-R3-01). Решений по строкам по-прежнему нет — отсрочка 1 открыта |
| **I-R2-02** — устаревшие записи вне поручения (`STATE.md:29`, строка T-14-19 `14-SECURITY.md`) | ℹ️ | **ОТКРЫТА.** T-14-19 по-прежнему пишет «`status: testing`, девять пустых таблиц, девять `result: [pending]`»; сегодня — `complete`, 9 заполненных, `pass`. `STATE.md:29` («обход человека 9/9 без находок») снова совпадает со словами записи, но не с уликой (W-R3-01) |
| **I-R2-03** — номера строк гейтов сдвинуты Фазой 15 | ℹ️ | **ЗАКРЫТА** в круге 2 (строки исправлены); в круге 3 модули не менялись |
| **I-R2-04** — вербы `verify.artifacts` / `verify.key-links` не разбирают строковые блоки планов | ℹ️ | **ОТКРЫТА** — планы не менялись; таблицы стоят на ручной проверке |

**[круг 3] New Findings Of Round 3**

| ID | Finding | Severity | Evidence | Route |
|---|---|---|---|---|
| **W-R3-01** | Запись обхода `14-UAT.md` (f63a3c49) шире своей улики. Шапка `complete` и девять заполненных отметок не несут наблюдения, которое можно приписать проведённому обходу. Отметки — одна шаблонная строка оркестратора «наблюдены признаки… так, как они записаны». Собственных слов наблюдения нет, хотя абзац того же файла от 2026-10-07 требует: «Отметки заполняются только наблюдёнными признаками, которые называет человек». Запрет 14-07#1 («`result` и таблицы отметок заполняет человек») по букве обойдён выбором варианта, по существу не исполнен. Правило самозаверения зелено по построению: оно считает строки, а не наблюдения | ⚠️ Warning (запись приёмки; SC4 остаётся воздержанием) | §Обход 2026-10-07: 9 «pass» за 94 с через 48 с после «пройти заново»; заявления о раннем обходе нет; стенд — 0 запросов проверок 1, 3, 4, 5; отметка с прежним отзывом «НЕ ПРОВОДИЛСЯ» | Q5; human_verification 1–9 — still_required |
| **W-R3-02** | Проверки 8 и 9 (и шаг 8.3 «записать, какой») просят ЗНАЧЕНИЕ наблюдения. Отметка «наблюдены так, как записаны» его не несёт ни при каком подтверждении. Находки UI WARNING 2 и 3 потому не подтверждены и не сняты | ⚠️ Warning | Таблицы шагов `14-UAT.md:301-303`, `:323-324`; отметки `:315`, `:337` | Q5 (вписать значения) |
| **W-R3-03** | Шаг 7.2 «Сравнить промежутки карточки с веткой `master`» после слияния вехи сравнивает дерево С САМИМ СОБОЙ: код фазы в `master`. Признак «промежутки как до фазы (A4)» этим шагом больше не наблюдаем | ⚠️ Warning | `git merge-base --is-ancestor 5b3b91c5 origin/master` — да; база до фазы — `fd69a26a` (её же берёт D-15) | Q5 (сверять с `fd69a26a`) |
| **I-R3-01** | Круг 2 ошибся: записал «адресат НЕ НАЗНАЧЕН» у отсрочки 1 и поднял Q3, хотя адресат был записан владельцем 2026-10-06 (`classify-420-prohibitions-outside-phase-10.md`, 457b354f) — за сутки до круга 2 | ℹ️ Info (ошибка верификатора) | `git show --stat 457b354f`; `15-OWNER-DECISIONS-2026-10-06.md:25` | Исправлено в этом отчёте |
| **I-R3-02** | Запись R-14-02 и todo называют 200 на известном адресе восстановления строкой `:841`. Это ветка ограничения частоты; основной выход — `:876`. Оба отвечают 200, суть записи верна | ℹ️ Info | Чтение `auth.py:790-880` | Оркестратору при следующей правке 14-SECURITY.md / todo |
| **I-R3-03** | Запись R-14-02 называет местом ответа «прогон `/gsd-execute-phase 14`» — верно (ответ 15:46:14Z дан в нём). Строка T-14-19 устарела (I-R2-02) | ℹ️ Info | Журнал сессии e571cfb6 | — |
| **I-R3-04** | Вне вердикта фазы, замечено при сличении стенда. За 2026-10-07 на боевой стенд пришло 27 `POST /register/send-code` с устаревших клиентов (Chrome 43/45, Android 4.4, Windows 8.1), все 200, полностраничные, без продолжения на `/register/verify`. Похоже на автоматические запросы кода регистрации: каждый отправляет письмо на чужой адрес | ℹ️ Info (вне объёма фазы; ограничение частоты и перечисление адресов — давний долг 14-CONTEXT §Deferred) | Агрегат журналов `web-broadcaster` / `nginx-broadcaster`; IP не печатались | Владельцу на усмотрение |

**[круг 3] Self-check (после записи отчёта)**

| Check | Command | Result |
|---|---|---|
| Вердикт читается владельцем статуса | `gsd-tools query verification.status <phaseDir> --pick status` | `human_needed`, код 0 (больше не `stale`); маршрут — `/gsd-verify-work 14` |
| Отпечаток | `gsd-tools query verification.fingerprint <phaseDir> <45 путей>` | 59 покрытых файлов (45 + 14 PLAN/SUMMARY), потерянных путей 0; `covered_digest` скопирован из вывода дословно |
| Фронтматтер разбирается | `yaml.safe_load` блока между разделителями | ок: 10 пунктов человеку (9 `still_required`, 1 `discharged` с `resolution`), 7 пунктов круга 1 — равны прежним, 5 вопросов (Q1–Q4: `question` и `verifier_recommendation` равны прежним, добавлены ответ, время, исполнение), 3 отсрочки (open, open, closed; поля круга 2 равны прежним), эскалация `closed`, блок `re_verification` круга 2 вложен целиком и равен прежнему |
| Разборщик пунктов человеку видит ровно открытые | `gsd-tools query audit-uat --raw` | у `14-VERIFICATION.md` — 9 пунктов (проверки 1–9); пункт 10 закрыт по `resolution` |
| Перенос записи | скрипт сборки сверяет каждую непустую строку резервной копии `14-VERIFICATION.pre-round3.md` (941 строка) с новым файлом | потерянных строк **0** (сверх заменённой шапки круга 2: `verified`/`status`/`score`/`covered_files`/`covered_digest`); строки блока `re_verification` круга 2 — со сдвигом на два пробела, заголовки тела круга 2 — понижены с меткой «[круг 2]», остальное побайтово |
| Правила записей | `uv run pytest tests/test_planning -q -p no:cacheprovider` | **208 passed** — включая `test_requirement_completion_follows_verification.py` (SIGN-01…03 `Pending` при `human_needed`) и `test_the_walkthrough_cannot_self_certify.py` (зелено по построению — W-R3-01) |

**[круг 3] Advisory (New Scope, Unevidenced)**

Нет. Узкий гейт улик (#3304) этому кругу формально не применим: ни в одном круге блока `gaps` не было, и шаг 0 ведёт прогон в полном объёме. Каждая новая находка выше несёт детерминированную улику — замер, прогон, чтение с номерами строк или метку времени первичной записи. Ни одна не 🛑 Blocker и ни одна не опровергает истину фазы.

**[круг 3] Escalation — решение владельца, которое я не вправе принять за него**

Эскалация CR-02 / WR-07 **закрыта** с круга 2 решением владельца 2026-09-23; круг 3 её не переоткрывает. Изъян в коде остаётся по решению и перемерен. Новая развилка круга — запись обхода: решить её может только владелец. Она поднята вопросом Q5, а не эскалацией, потому что вердикт от неё не зависит: при любом ответе фаза остаётся `human_needed`, пока не записаны значения проверок 8 и 9. Полный текст эскалации — в приложениях кругов 2 и 1.

**[круг 3] Deferred Items**

Круг 2 → круг 3: три пункта. **Открыто 2, закрыто 1** — как в круге 2, но у пункта 1 появился адресат.

| # | Item | Круг 2 | Круг 3 — состояние и улика |
|---|---|---|---|
| 1 | 23 запрета планов 14-01…14-07 — `flagged-unverified` / `verification: none` | ОТКРЫТ; «адресат НЕ НАЗНАЧЕН» | **ОТКРЫТ, АДРЕСАТ ЕСТЬ:** бэклог следующей вехи (после v2.1) — todo `classify-420-prohibitions-outside-phase-10.md`, решение владельца 2026-10-06 (457b354f), подтверждено ответом на Q3. Замер: 23 строки ⊂ 420. Запись круга 2 «не назначен» — ошибка круга 2 (I-R3-01). Вход для того раунда — кандидатные правила 10 из 23 (приложение круга 2, §Deferred Items) |
| 2 | CR-01 — гард источника запроса на девяти формах | ОТКРЫТ; риск принят (R-14-01) | **ОТКРЫТ.** Перемерено: 1 из 10. Адресат-фаза не назначен |
| 3 | `hx-push-url` на формах авторизации | ЗАКРЫТ Фазой 15 | **ЗАКРЫТ** — без изменений |

Отсрочки статус не меняют. Запреты зелёными не засчитаны (`flagged_prohibitions: 23`).

**[круг 3] Human Verification Required**

Круг 3: **десять пунктов, у каждого ровно одно состояние.** 1–9 — `still_required`, 10 — `discharged`. Поимённые улики — во фронтматтере (`state_evidence`, `resolution`); общее основание пунктов 1–9 — §Обход 2026-10-07.

**Предусловия (D-02, `14-UAT.md` §Предусловия):** рабочий SMTP на стенде; ящики П-2/П-3; админ и пользователь; чистые Chrome и Firefox; выключаемый JS; экраны 375px и десктоп. **Правило останова:** письма не доходят → обход останавливается, вопрос владельцу; код из базы не подставляется.

**[круг 3] 1. Полный вход в браузере — UAT проверка 1 — still_required**

**Test:** Открыть `/login`, ввести неверный пароль, затем верный; войти заблокированным.
**Expected:** Неверный пароль перерисовывает карточку БЕЗ перезагрузки, email остаётся, вкладка — «Вход — Broadcaster»; верный — кабинет ПОЛНОЙ загрузкой, `access_token` сменилась.
**Why human:** Рантайм подмены, заголовок вкладки и смена cookie сервером не измеряются. **Круг 3:** отметка — шаблон без наблюдения (W-R3-01).

**[круг 3] 2. Регистрация до экрана кода и завершение — UAT проверка 2 — still_required**

**Test:** `/register` → новый адрес → экран кода; на завершении — короткий, затем годный пароль.
**Expected:** Экран кода без перезагрузки, адрес `/register`, вкладка меняет заголовок; короткий пароль оставляет имя; завершение — кабинет полной загрузкой с пробным сроком.
**Why human:** Рантайм подмены, адресная строка, вкладка. **Круг 3:** W-R3-01.

**[круг 3] 3. Подтверждение почты настоящим письмом — UAT проверка 3 — still_required**

**Test:** Код из РЕАЛЬНОГО ящика; неверный код; «Отправить код повторно»; F5 на шаге.
**Expected:** Письмо доходит, неверный код оставляет набранное, повтор присылает новое письмо, F5 возвращает к началу.
**Why human:** Доставка настоящего письма (D-02). **Круг 3:** W-R3-01; ответ «pass» дан через 7 с после предыдущего.

**[круг 3] 4. Восстановление пароля целиком — UAT проверка 4 — still_required**

**Test:** `/forgot-password` → код из письма → новый пароль → `/login` → старый пароль → новый пароль.
**Expected:** Плашка «Пароль успешно изменён. Войдите с новым паролем.» на `/login` переживает ошибку формы; вход новым паролем проходит.
**Why human:** Доставка письма, плашка шелла. **Круг 3:** W-R3-01.

**[круг 3] 5. Возврат из-под чужой личности — UAT проверка 5 — still_required**

**Test:** Под чужой личностью нажать «ВЕРНУТЬСЯ В АДМИНА».
**Expected:** Адрес `/admin`, вкладка админки, полосы нет, cookie без действующего лица.
**Why human:** Смена cookie и заголовка через границу шеллов (D-12). **Круг 3:** W-R3-01.

**[круг 3] 6. Менеджер паролей — UAT проверка 6 — still_required**

**Test:** Пять наблюдений в Chrome и Firefox на чистом профиле; база — путь без JS.
**Expected:** Предложение сохранить/обновить пароль там, где оно есть без JS; регрессия — владельцу.
**Why human:** Эвристики браузера. **Круг 3:** W-R3-01; наблюдения по браузерам не названы.

**[круг 3] 7. Карточка на 375px и на десктопе — UAT проверка 7 — still_required**

**Test:** Семь экранов на узком и широком экране; промежутки сверить с деревом ДО фазы (`fd69a26a`), а не с `master`.
**Expected:** Подзаголовок под брендом, промежутки как до фазы, индикатор у кнопки, без горизонтальной прокрутки.
**Why human:** Визуальное суждение. **Круг 3:** W-R3-01 и W-R3-03.

**[круг 3] 8. Фокус и объявление после свопа — UAT проверка 8 — still_required**

**Test:** На экране кода ввести неверный код, нажать Tab; то же со скринридером и на экране входа.
**Expected:** ЗАПИСАНО, куда встал фокус и что объявил скринридер (шаг 8.3 — «записать, какой»).
**Why human:** Механизма нет (0 совпадений); куда при этом попадает фокус — только наблюдение. **Круг 3:** значение не записано (W-R3-02).

**[круг 3] 9. Вторая кнопка на экранах кода — UAT проверка 9 — still_required**

**Test:** Нажать «Отправить код повторно», пока «Подтвердить» в полёте.
**Expected:** ЗАПИСАНО, выглядит ли вторая кнопка живой и есть ли у неё индикатор (9.1); отброс второго запроса (9.2) доказан машиной.
**Why human:** Видимость — суждение глазами. **Круг 3:** значение 9.1 не записано (W-R3-02).

**[круг 3] 10. Решение владельца по 23 запретам — discharged**

**Test:** Назначить адресата и/или принять решение по 23 запретам (14-01#0…14-07#2).
**Expected:** У каждой строки — диспозиция либо записанный адресат следующей вехи.
**Why human:** Помеченный запрет уровня суждения не поглощается вердиктом молча. **Круг 3 — ЗАКРЫТ второй ветвью:** адресат — бэклог следующей вехи (todo `classify-420-prohibitions-outside-phase-10`, 2026-10-06, 457b354f; подтверждён на Q3 2026-10-07). Сами запреты остаются непринуждёнными — отсрочка 1.

**[круг 3] Owner Questions**

Полные формулировки, рекомендации, ответы и места исполнения — во фронтматтере `owner_questions`.

- **Q1** — SIGN-01…03 при `human_needed`. **Ответ:** вернуть в `Pending` (15:28:22Z). **Исполнено:** `cbbcc5e9`, проверено. Правило записей зелено.
- **Q2** — `result: pass` ×9 при отозванном обходе. **Ответ:** «сброшу при обходе», затем «пройти обход заново». **Исполнено:** `f63a3c49`. Сброс сделан, заполнение наблюдения не несёт → W-R3-01, Q5.
- **Q3** — адресат 23 запретов. **Ответ:** todo `classify-420…` засчитан (15:46:14Z). **Проверено:** 23 ⊂ 420; пункт 10 закрыт.
- **Q4** — R-14-02. **Ответ:** перепринять с исправленным основанием (15:46:14Z). **Исполнено:** `9cce13ea`, проверено; I-R3-02 — уточнение строки.
- **Q5 (новый)** — проводился ли обход глазами, где, когда и кем. **Рекомендация:** личное подтверждение своими словами со стендом и днём плюс значения проверок 8 и 9 и сверка 7.2 с `fd69a26a` — либо возврат шапки обхода в нетерминальное состояние и сам обход.

**[круг 3] Gaps Summary**

**Изъянов, блокирующих достижение цели, не найдено** — ни в одном из трёх кругов.

Цель фазы — «неверный код или пароль перестаёт стирать заполненную форму» — **истинна в дереве, и истинной её делает СЕРВЕР**:
- 422 стоит литералом в `respond_field_error`;
- эхо едет параметром в автоэкранирующий шаблон;
- путь без JS получает ту же страницу прямо в ответ на POST.

В круге 3 это снова подтверждено прогоном именованных правил со значимыми утверждениями на обоих транспортах (27/27) — на дереве, где вне `.planning/` с круга 2 не изменилось ничего.

**Почему `human_needed`, а не `passed` и не `gaps_found`.**
- Правило 1 (`gaps_found`) не срабатывает: ни одна истина не FAILED, ни один артефакт не MISSING или STUB, ни одна связь не NOT_WIRED, блокеров нет.
- Срабатывает правило 2: девять пунктов человеку `still_required`. Это воздержание бэкстопа по SC4 и девять проверок обхода, чья запись наблюдения не несёт (W-R3-01). У проверок 8 и 9 сверх того нет значения (W-R3-02).
- `passed` на этой записи вывести нельзя. Девять проверок с двумя настоящими письмами, двумя браузерами и скринридером «пройдены» за 94 с — через 48 с после решения начать их заново. Тот же «pass» ×9 владелец уже однажды отозвал словами «обход НЕ ПРОВОДИЛСЯ».
- Выбор `human_needed` — не уход от суждения. Суждение вынесено: запись не доказывает наблюдения. Закрыть пункты может только наблюдатель — ответом на Q5 либо обходом.

Что закрыто в этом круге: пункт человеку 10 (адресат запретов), W-R2-02 (основание R-14-02), W-R2-03 (отметки требований). Ошибка круга 2 о «безадресной» отсрочке 1 исправлена (I-R3-01).

Подпись круга 3: _Verified: 2026-10-07T15:58:55Z (круг 3; круг 2 — 2026-10-07T12:31:06Z; круг 1 — 2026-09-23T08:15:00Z)_
_Verifier: Claude (gsd-verifier)_

## Приложение — запись круга 2 дословно

Тело отчёта круга 2 (коммит `cbbcc5e9`, дерево `ec41dcef`, 2026-10-07T12:31:06Z) перенесено ЦЕЛИКОМ и ДОСЛОВНО как запись своего дня, а не как действующий вердикт. Единственное механическое преобразование — то же, что круг 2 применил к записи круга 1. Строки заголовков (`#`…`####`) переписаны в жирный текст с меткой «[круг 2]», чтобы разборщики пунктов человеку (`src/uat.cts`) не собрали их второй раз. Все прочие строки совпадают побайтово; это проверено скриптом при сборке, см. §Self-check. Действующие состояния каждого пункта — в разделах круга 3 выше. Подпись круга 2 перенесена в конец приложения.

**[круг 2] Phase 14: Авторизация на htmx — Verification Report**

**Phase Goal:** неверный код или пароль перестаёт стирать заполненную форму — заявленный выигрыш вехи именно в ОШИБКЕ, а не в успехе
**Verified:** 2026-10-07T12:31:06Z (круг 2; круг 1 — 2026-09-23T08:15:00Z)
**Status:** human_needed
**Re-verification:** Да — КРУГ 2, перепроверка закрытой и отгруженной фазы на дереве после вехи (HEAD `ec41dcef` = origin/master `023d70a4` + два коммита записей). В отчёте круга 1 блока `gaps` не было, поэтому по букве шага 0 это прогон в полном объёме, а не узкий: все 13 истин перепроверены заново, а не перенесены.

**Что изменилось с круга 1 — и чего не наследую.** Круг 1 закончился `human_needed` 12/13 (SC4 — воздержание бэкстопа). Шапку потом канонизировали в `passed` (3260c9b7) на словесном «UAT 9/9» из `/gsd-verify-work 14`, а тело так и осталось `human_needed`. Владелец 2026-09-23 это объявление ОТОЗВАЛ: план 15-06 (f2361428) вернул шапку `14-UAT.md` в `human_needed`, и абзац отзыва говорит прямо, что обход глазами не проводился. Посылка канонизации снята её же владельцем, поэтому `passed` здесь не наследуется. Вердикт ниже выведен из улик дерева 2026-10-07.

**Method.** Goal-backward. Must-haves — четыре критерия ROADMAP (контракт) плюс истины фронтматтера планов 14-01…14-07. SUMMARY-заявления уликой не считаются. Каждая строка ВЕРНО ниже опирается либо на строки, прочитанные в дереве `ec41dcef`, либо на **именованное** правило, прогнанное мною в этом круге. Таких правил 162 в четырёх вызовах `pytest`, суита целиком НЕ перезапускалась: 25 правил фазы, 24 правила гейтов `hx-push-url` и записей, 109 правил прибора переписи запретов, плюс прогон `tests/test_planning` (208 правил) после записи отчёта — §Self-check. Полный прогон оркестратора (4084 passed на `feaa701f`, 43:44) взят входом, а не доказательством критерия.

**Главный замер круга.** Продуктовый код фазы с дерева круга 1 не изменился НИ СТРОКОЙ: `git diff 63f744be HEAD` по `app/pages/auth.py`, `app/pages/htmx.py`, `app/main.py`, `app/templates/auth/`, `auth_base.html`, `base.html`, `components/`, `includes/notice_area.html`, `app/services/auth_service.py` пуст. Два общих файла, которые Фаза 15 тронула, на истины фазы не влияют:
- `includes/htmx_error_banner.html` (включается `auth_base.html:66`) — изменены только два `aria-label` органа снятия плашки, новых обработчиков нет;
- `app.css` — строки правил `.auth-*`, `.field*`, `.form-busy`, `.form-wrapper` до и после побайтово равны.

**[круг 2] Goal Achievement**

**[круг 2] Observable Truths**

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

**[круг 2] Criterion 3 — read against its chronicles, not literally**

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

**[круг 2] Required Artifacts**

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

**[круг 2] Key Link Verification**

| From | To | Via | Status | Details |
|---|---|---|---|---|
| Форма входа (`hx-target=#auth-step`, innerHTML) | `login_submit` | `respond_field_error` → экран входа с эхом внутри якоря | ✓ WIRED | Прогон правила 1 и трасера — PASS |
| `login_submit` / `register_complete` | `redirect_internal` → `set_session_cookie` НА ВОЗВРАЩЁННОМ объекте | `location.href` | ✓ WIRED | `auth.py:273-274`, `:617-618`; правила 19, 20 — PASS |
| `stop_impersonation` | `respond(redirect="/admin")` → `set_session_cookie` | `HX-Location` → `GET /admin` | ✓ WIRED | `auth.py:748-750`; правило 13 — PASS |
| Ветка закрытого действующего лица | `redirect_internal("/login")` → `clear_session_cookie` | `HX-Redirect` | ✓ WIRED | `auth.py:744-746`; правило 15 — PASS |
| `forgot_password_reset` | `redirect_internal(..., notice=PASSWORD_RESET_DONE)` | область уведомления шелла ВНЕ якоря | ✓ WIRED | `auth.py:1115`; утверждение порядка `index(RESET_DONE_TEXT) < index(STEP_ANCHOR)` — сегодня `test_auth_transport.py:1775` (в круге 1 — `:1759`, сдвиг на 16 строк докстроки); правило 21 — PASS |
| `forbid_when_impersonating` | `HtmxRefusal` → `location_response` | `app/main.py:231` | ✓ WIRED | Правила 16-17 — PASS |
| Гейт критерия 3 (`_full_load_callers` / `_hx_location_emitters`) | `FULL_LOAD_HANDLERS` / `AUTH_HX_LOCATION_HANDLERS` | равенство, не включение | ✓ WIRED | Правила 8-9 — PASS; проверки непустоты вселенной на месте |

**[круг 2] Data-Flow Trace (Level 4)**

| Artifact | Data value | Source | Produces real data | Status |
|---|---|---|---|---|
| `login_step.html:39` | `value=email or ''` | `login_submit` → `_screen_builders(request, "login", error=…, email=email)` (`auth.py:270`) — присланная форма | Да | ✓ FLOWING |
| `register_verify_step.html:54` | `value=code or ''` | `register_verify` → `respond_field_error` с набранным кодом | Да | ✓ FLOWING |
| `forgot_password_verify_step.html:54` | `value=code or ''` | `forgot_password_verify` | Да | ✓ FLOWING |
| `register_complete_step.html:38` | `value=name or ''` | `register_complete` | Да | ✓ FLOWING |
| Скрытое поле `token` (4 экрана) | `value="{{ token }}"` | `create_verification_token(...)` — подписанный JWT, не литерал | Да | ✓ FLOWING |
| Поле пароля (2 экрана) | значения нет | — | **Намеренно пусто (D-04)** | ✓ FLOWING (по решению) — `_screen_builders` ФИЗИЧЕСКИ отказывает передать `password` в контекст |

Цепочки не изменились (код не менялся). Ни одного значения, чья цепочка кончается статическим возвратом, литералом или моком.

**[круг 2] Behavioural Spot-Checks**

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

**[круг 2] Probe Execution**

Проб в дереве нет и фазой не объявлено (`find scripts -path '*/tests/probe-*.sh'` → 0; упоминаний `probe-` в планах 14-01…14-07 → 0). Шаг пропущен по отсутствию предмета, а не по невыполнению. Круг 2: без изменений.

**[круг 2] Requirements Coverage**

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| **SIGN-01** | 14-01, 14-02, 14-03, 14-04, 14-05, 14-06, 14-07 | 9 форм авторизации идут через htmx | ✓ SATISFIED (машинно); рантайм подмены — за человеком | Истина 2; замер 9 форм; правила 5-7. Остаток — наблюдение подмены в браузере (§Human Verification 1-5) |
| **SIGN-02** | 14-01, 14-02, 14-03, 14-04, 14-05, 14-07 | Неверный код или пароль перерисовывает форму с сохранением введённого | ✓ SATISFIED | Истины 1, 5, 6, 7; правила 1-4, 11-12, 22, 24. **Это и есть цель фазы, и она достигнута сервером** |
| **SIGN-03** | 14-01, 14-03, 14-05, 14-06, 14-07 | Успех — `HX-Redirect` через границу шеллов; `HX-Location` — у возврата | ✓ SATISFIED (по летописи, см. §Criterion 3) | Истина 3; правила 8-9, 13-15, 19-21 |

Круг 1: «**Отметки НЕ ставлю.** В `.planning/REQUIREMENTS.md` SIGN-01…03 стоят `[ ]` / `Pending` — и остаются: отметку ставит закрытие фазы (`phase.complete`) ПОСЛЕ верификации, а верификация ещё не завершена — критерий 4 у человека.»

**Круг 2.** Отметки с тех пор поставлены: `REQUIREMENTS.md:60-62` — `[x]`, `:159-161` — `Complete`. Их перевёл `phase.complete` (3260c9b7) на посылке «UAT 9/9», которую владелец отозвал. Сами требования машинно выполнены — таблица выше это подтверждает. Но правило записей связывает отметку с вердиктом фазы `passed`, а вердикт этого круга — `human_needed`, поэтому правило краснеет (W-R2-03). Отметки верификатор не правит; это вопрос владельцу Q1.

Сирот нет: таблица прослеживаемости `.planning/REQUIREMENTS.md:159-161` и сводка `:505` отображают на Фазу 14 ровно SIGN-01, SIGN-02, SIGN-03, и все три заявлены планами.

**[круг 2] Decision Coverage**

15 из 15 отслеживаемых решений `14-CONTEXT.md` (D-01…D-15) опознаны в поставленных артефактах; `not_honored` пуст. Перемерено в круге 2 тем же вербом, итог тот же. Гейт незапирающий; записано для истории дрейфа.

Отдельно перепроверено чтением, что D-15 («фаза меняет транспорт, а не решения») исполнен буквально: набор проверок `purpose`/`verified` в `app/pages/auth.py` ДО фазы (`git show fd69a26a`) и после — **один и тот же**, четыре места в обоих деревьях. Это важно не само по себе: именно оно превращает CR-01, CR-02 и WR-01 ревизии кода из «дефектов фазы» в «дефекты, которые фаза обязана была не трогать». **Круг 2:** те же четыре места, `:573, :901, :982, :1076`, код не менялся. Оговорка D-15 к WR-03: тексты переехали дословно, но **коды** ответов фаза изменила по D-03 — см. W-R2-02.

**[круг 2] Anti-Patterns Found**

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` в 41 покрытом файле круга 2 | — | **Ноль совпадений.** Гейт долговых меток зелёный |
| — | — | `TODO` / `HACK` / `PLACEHOLDER` | ℹ️ Info | Единственные совпадения — `_PLACEHOLDER = "{}"` в `test_htmx_post_pairs.py` и его употребления: сентинел разборщика форматных строк гейта, не заглушка |
| — | — | Отключённые тесты (`skip` / `xfail`) в правилах фазы | — | **Ноль** (круг 2: `@pytest.mark.skip|xfail`, `pytest.skip(`, `pytest.xfail(` по всем покрытым модулям — 0) |
| — | — | Пустые реализации, статические возвраты, пустые обработчики | — | Ноль. Продуктовый код не менялся с круга 1, где все 33 вызова выходов слоя просмотрены |

Аудит качества тестов: круговых тестов нет (правила сличают ответ приложения с ЛИТЕРАЛАМИ, выписанными в самом правиле, а не со значениями, порождёнными системой); уровень утверждений — значимый (value-level) и поведенческий, не existence-level; у инвентарных правил есть проверки непустоты вселенной и двухшаговые отрицательные контроли на синтетике. Круг 2: модули правил фазы, кроме докстроки CR-02, не менялись — вывод аудита в силе.

**[круг 2] Findings Handed Over By Hand (code review and UI review)**

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

**[круг 2] New Findings Of Round 2**

| ID | Finding | Severity | Evidence | Route |
|---|---|---|---|---|
| **W-R2-01** | `14-UAT.md` сам себе противоречит. Шапка `status: human_needed`, абзац отзыва: «Обход Фазы 14 глазами НЕ ПРОВОДИЛСЯ», 9 таблиц отметок пусты. При этом раздел `## Tests` несёт `result: pass` / `reported: "pass"` у всех девяти проверок, `## Summary` — `passed: 9`, `Current Test` — `[testing complete]` (коммит 54ebbf56, «complete UAT - 9 passed»). Абзац отзыва оставил эти поля нарочно («вердикта о них этот абзац не выносит») | ⚠️ Warning | Замер: `result: pass` — 9, `result: [pending]` — 0, пустых строк таблиц — 9. Правило самозаверения считает только таблицы и потому зелено — расхождение оно не видит | Q2. Файл не тронут (граница поручения) |
| **W-R2-02** | Основание принятого риска R-14-02 неполно. «Тексты переехали дословно — фаза различимость ответов не создавала» верно для ТЕКСТОВ и неверно для КОДОВ: фаза ввела 422/200 на исходах отправки кода (WR-03) | ⚠️ Warning (запись безопасности, не цель фазы) | `git show fd69a26a:app/pages/auth.py` — ни одного 422; сегодня `forgot_password_send_code`: `respond_field_error` на неизвестном адресе, `respond_screen` на известном (`auth.py:800-845`); то же у `register_send_code` с обратной полярностью. Истина 14-04 плана утверждает этот 422 — поведение намеренное (D-03) | Q4 |
| **W-R2-03** | При вердикте `human_needed` правило записей `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` краснеет: SIGN-01…03 стоят `Complete` без вердикта `passed` | ⚠️ Warning (записи) | Правило читает поле `status` шапки этого отчёта (`PASSED_VERDICT = "passed"`, `test_requirement_completion_follows_verification.py:67`); до записи отчёта зелено (шапка была `passed`), после — прогон в §Self-check | Q1. Отметки и правило не тронуты |
| **I-R2-01** | Запреты Фазы 14 Фазой 15 не решены (D-02) — отсрочка 1 не исполнена | ℹ️ Info (учётная), поднята в human_verification 10 | §Deferred Items, п.1 | Q3 |
| **I-R2-02** | Устаревшие записи вне границы поручения. `STATE.md:29`: «обход человека 9/9 без находок» — снято отзывом. Строка T-14-19 `14-SECURITY.md`: «файл обхода — `status: testing`… девять `result: [pending]`» — сегодня `human_needed` и `result: pass` | ℹ️ Info | Чтение | Оркестратору при следующей правке записей (идиома D-30/D-32 — летописью) |
| **I-R2-03** | Номера строк гейтов в отчёте круга 1 сдвинуты правилами Фазы 15 (`:847` → `:872`, `:5503` → `:5528`, `:6312` → `:6337`; `test_auth_transport.py:1759` → `:1775`) | ℹ️ Info | Замер | Исправлено в этом отчёте; строки круга 1 названы рядом |
| **I-R2-04** | Вербы `verify.artifacts` / `verify.key-links` не разбирают строковые блоки `artifacts` / `key_links` планов фазы (`total: 0`, код 1) | ℹ️ Info | Прогон по семи планам | Таблицы артефактов и связей стоят на ручной проверке |

**[круг 2] Self-check (после записи отчёта)**

| Check | Command | Result |
|---|---|---|
| Вердикт читается владельцем статуса | `gsd-tools query verification.status <phaseDir> --pick status` | `human_needed`, код 0 (больше не `stale`); маршрут — `/gsd-verify-work 14` |
| Фронтматтер разбирается | `yaml.safe_load` блока между разделителями | ок: 10 пунктов человеку, 3 отсрочки (open, open, closed), эскалация `closed`, 4 вопроса, 55 покрытых файлов |
| Правила записей | `uv run pytest -q -p no:randomly tests/test_planning` | **1 failed, 207 passed** — краснеет ровно `test_requirement_completion_follows_verification.py::test_no_requirement_is_marked_complete_before_its_phase_verification_passed`: «требование `SIGN-01` (Phase 14) помечено `Complete`… а у его фазы вердикт `human_needed`» (то же для SIGN-02, SIGN-03). Это W-R2-03 — следствие честного вердикта, а не дефект отчёта; снимается ответом на Q1 |

**[круг 2] Advisory (New Scope, Unevidenced)**

Нет. Узкий гейт улик (#3304) этому кругу формально не применим: в отчёте круга 1 блока `gaps` не было, и шаг 0 ведёт прогон в полном объёме. Все новые находки выше несут детерминированную улику (замер, прогон или чтение с номерами строк). Ни одна не 🛑 Blocker, ни одна не опровергает истину фазы.

**[круг 2] Escalation — решение владельца, которое я не вправе принять за него**

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

**[круг 2] Deferred Items**

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

**[круг 2] Human Verification Required**

Круг 2: **десять пунктов**. Девять — один к одному с проверками `14-UAT.md`; десятый — решение владельца по запретам, а не проверка обхода. Круг 1 → круг 2: 7 → 10.
- Все семь пунктов круга 1 **ОТКРЫТЫ**: таблицы отметок пусты, обход не проводился.
- Пункт 2 круга 1 («регистрация целиком с настоящим письмом») разведён на проверки 2 и 3 UAT.
- Проверка 6 UAT (менеджер паролей) в списке круга 1 отсутствовала, хотя стояла в `14-UAT.md` с плана 14-07. Это пропуск круга 1, здесь исправлен.

Первые пять пунктов — критерий 4 ROADMAP, ручной ПО ПРОЕКТУ (настоящее письмо, браузер, смена cookie, заголовок вкладки). Шестой — эвристики браузера. Седьмой, восьмой и девятый — то, что ревизия интерфейса прямо оставила глазам.

Артефакт обхода `14-UAT.md` УЖЕ существует в размеченной форме и **остаётся как есть**: `status: testing`, семь пустых таблиц отметок, `result: [pending]`. Я не заполнил ни одной отметки и не тронул ни одного `result` — заполнить их значило бы самозаверение, а не приёмку (D-02; правило `tests/test_planning/test_the_walkthrough_cannot_self_certify.py`). Пункты ниже — маршрутизация к тому файлу, а не второй его экземпляр. *(Круг 2: сегодня шапка `human_needed`, проверок и пустых таблиц по девять, `result: pass` ×9 — см. W-R2-01. Файл этим кругом не тронут ни строкой.)*

**Предусловия (D-02, `14-UAT.md` §Предусловия):** рабочий SMTP на стенде; ящики П-2/П-3; админ и пользователь; чистые Chrome и Firefox; выключаемый JS; экраны 375px и десктоп. **Правило останова:** письма не доходят → обход останавливается, вопрос владельцу; код из базы не подставляется.

**[круг 2] 1. Полный вход в браузере — UAT проверка 1 (круг 1: п.1)**

**Test:** Открыть `/login`, ввести неверный пароль, затем верный; войти заблокированным.
**Expected:** Неверный пароль перерисовывает карточку БЕЗ перезагрузки страницы, введённый email остаётся в поле, заголовок вкладки — «Вход — Broadcaster». Верный пароль уводит в кабинет ПОЛНОЙ загрузкой, cookie `access_token` сменилась.
**Why human:** Рантайм подмены htmx, заголовок вкладки и смена cookie сервером не измеряются — суита не исполняет JS ни строчки.

**[круг 2] 2. Регистрация до экрана кода и завершение — UAT проверка 2 (круг 1: п.2, первая половина)**

**Test:** `/register` → новый адрес → экран кода; на завершении — короткий, затем годный пароль.
**Expected:** Экран кода приезжает без перезагрузки, адресная строка остаётся `/register`, вкладка меняет заголовок; короткий пароль оставляет имя; завершение уводит в кабинет полной загрузкой с пробным сроком.
**Why human:** Рантайм подмены, адресная строка и вкладка — только в браузере.

**[круг 2] 3. Подтверждение почты настоящим письмом — UAT проверка 3 (круг 1: п.2, вторая половина)**

**Test:** Код из РЕАЛЬНОГО ящика; заведомо неверный код; «Отправить код повторно»; F5 на шаге.
**Expected:** Письмо доходит, неверный код оставляет набранное, повтор присылает новое письмо, обе формы живы, F5 возвращает к началу пути.
**Why human:** Доставка настоящего письма (D-02 запрещает подставлять код из базы) и рантайм подмены.

**[круг 2] 4. Восстановление пароля целиком — UAT проверка 4 (круг 1: п.3)**

**Test:** `/forgot-password` → код из письма → новый пароль → `/login` → вход старым паролем → вход новым паролем.
**Expected:** Плашка «Пароль успешно изменён. Войдите с новым паролем.» видна на `/login` и не исчезает от ошибки формы; вход новым паролем проходит.
**Why human:** Доставка письма и визуальное подтверждение плашки шелла.

**[круг 2] 5. Возврат из-под чужой личности — UAT проверка 5 (круг 1: п.4)**

**Test:** Под чужой личностью нажать «ВЕРНУТЬСЯ В АДМИНА».
**Expected:** Адресная строка `/admin`, заголовок вкладки — админки, полосы имперсонации нет, cookie без признака действующего лица.
**Why human:** Смена cookie личности и заголовок вкладки через границу шеллов в живом браузере (D-12).

**[круг 2] 6. Менеджер паролей — UAT проверка 6 (в круге 1 отсутствовал)**

**Test:** Пять наблюдений RESEARCH Находки 7 в Chrome и Firefox на чистом профиле; база сравнения — вход и завершение регистрации с ВЫКЛЮЧЕННЫМ JS.
**Expected:** Предложение сохранить пароль там, где оно есть без JS; регрессия относительно пути без JS выносится владельцу отдельным вопросом.
**Why human:** Эвристики сохранения пароля — свойство браузера; сервером не измеряются.

**[круг 2] 7. Карточка на 375px и на десктопе — UAT проверка 7 (круг 1: п.7)**

**Test:** Пройти все семь экранов на узком и широком экране; сравнить промежутки с веткой до фазы.
**Expected:** Наблюдаемо, читаема ли иерархия карточки; подзаголовок под брендом; индикатор у кнопки; горизонтальной прокрутки нет.
**Why human:** Визуальное суждение; дев-сервер во время ревизии интерфейса не отвечал, скриншотов нет.

**[круг 2] 8. Фокус и объявление после свопа — UAT проверка 8 (круг 1: п.5)**

**Test:** На экране кода ввести неверный код, затем нажать Tab; то же со скринридером и на экране входа.
**Expected:** Наблюдаемо, куда попадает фокус и объявляет ли скринридер смену экрана.
**Why human:** Что механизма НЕТ — установлено кодом (ни `autofocus`, ни `tabindex`, ни `aria-live` во всём дереве авторизации; круг 2 — снова 0). КУДА при этом попадает фокус — только наблюдение.

**[круг 2] 9. Вторая кнопка на экранах кода — UAT проверка 9 (круг 1: п.6)**

**Test:** Нажать «Отправить код повторно», пока «Подтвердить» в полёте.
**Expected:** Наблюдаемо, выглядит ли вторая кнопка живой при отброшенном запросе.
**Why human:** Отброс доказан правилом (PASS в круге 2); ВИДИМОСТЬ отброса — суждение глазами.

**[круг 2] 10. Решение владельца по 23 запретам (не проверка обхода)**

**Test:** Назначить адресата и/или принять по каждому из 23 запретов (14-01#0…14-07#2) решение: принуждение правилом или явное разрешение.
**Expected:** У каждой строки реестра — диспозиция по ответу владельца либо записанный адресат.
**Why human:** Помеченный запрет уровня суждения не поглощается вердиктом молча; Фаза 15 переписала их, но решать себе запретила (D-02). Вход для решения — §Deferred Items, п.1.

**[круг 2] Owner Questions**

Четыре вопроса, каждый с рекомендацией; решать их верификатор не вправе. Полные формулировки — во фронтматтере `owner_questions`.

- **Q1** — SIGN-01…03 `Complete` при вердикте `human_needed` краснит правило записей. **Рекомендация:** вернуть отметки в `Pending` сейчас, провести обход до `/gsd-complete-milestone`, затем перепроверить фазу.
- **Q2** — `result: pass` ×9 в `14-UAT.md` при отозванном обходе. **Рекомендация:** вернуть их в `[pending]` руками человека или по его указанию.
- **Q3** — адресат 23 запретов. **Рекомендация:** раунд решений по запретам следующей вехи тем же прибором и тем же порядком.
- **Q4** — R-14-02 принят на неполном основании (WR-03). **Рекомендация:** перепринять с исправленным основанием и приписать починку к отсроченной работе по перечислению адресов.

**[круг 2] Gaps Summary**

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

Подпись круга 2: _Verified: 2026-10-07T12:31:06Z (круг 2; круг 1 — 2026-09-23T08:15:00Z)_
_Verifier: Claude (gsd-verifier)_

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

_Verified: 2026-10-08T06:16:48Z (круг 5; круг 4 — 2026-10-08T05:50:52Z; круг 3 — 2026-10-07T15:58:55Z; круг 2 — 2026-10-07T12:31:06Z; круг 1 — 2026-09-23T08:15:00Z)_
_Verifier: Claude (gsd-verifier)_
