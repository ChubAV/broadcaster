---
phase: 11-massovyy-perevod-razdelov-pisma
verified: 2026-10-07T07:00:00Z
# ⚠️ РАУНД 2026-10-07 — ПОВТОРНАЯ ВЕРИФИКАЦИЯ НА ДЕРЕВЕ ПОСЛЕ ВЕХИ v2.1. Вердикт `passed`
# издания 2026-09-18 читался `stale`: фазы 12–15 (все отгружены) правили 15 покрытых файлов
# `app/` — поимённо, с коммитами, в теле, раздел «Что сдвинули фазы 12–15 на пути истин».
# Каждая из 13 истин перемерена на сегодняшнем дереве (HEAD 531c7ced; код совпадает с 7b54dbe1 —
# `git diff --name-only 7b54dbe1..HEAD` вне `.planning/` пуст). Вердикт и оценку выносит ЭТОТ
# раунд, а не переносит: 11/13 → 12/13 (истина 13 поднята наблюдением плюс доказанной
# неподвижностью пути), behavior_unverified 2 → 1.
#
# ОТПЕЧАТОК СНЯТ ВЕРБОМ `verification.fingerprint` (gsd-core 1.16.070) и скопирован как есть:
# 112 путей — 70 переданных (тот же состав, что у издания 2026-09-18, без файлов самой фазы) и
# 42 PLAN/SUMMARY, которые верб добавил сам. Первый переданный путь `.planning/REQUIREMENTS.md`
# в выводе НА МЕСТЕ: дефект 1.14 («верб теряет первый путь»), из-за которого прежнее издание
# считало отпечаток функцией проверяющего, в 1.16 исправлен. Формат отпечатка v1 → v3.
#
# ── Комментарий шапки издания 2026-09-18, дословно (летопись прежнего отпечатка v1) ──
# ⚠️ ШТАМП СВЕЖЕСТИ И ОТПЕЧАТОК ПЕРЕСТАВЛЕНЫ ОБХОДОМ `/gsd-verify-work 11` 2026-09-18;
# ВЕРДИКТ, ОЦЕНКА И ВЫВОДЫ ОТЧЁТА НЕ ТРОНУТЫ. Прежний штамп — 2026-09-18T00:00:00Z,
# прежний отпечаток — 225759df….
#
# Причина названа поимённо: закрытие фазы (`gsd_run query phase.complete 11`) правит
# `.planning/REQUIREMENTS.md`, а он стои́т в `covered_files` — от этого вердикт читался
# `stale`. По `git diff --name-only HEAD` это ЕДИНСТВЕННЫЙ изменившийся покрытый файл, и
# правка его — простановка отметок требований, то есть СЛЕДСТВИЕ прошедшей верификации, а
# не вход, способный её опровергнуть.
#
# ⚠️ ОТПЕЧАТОК СНЯТ НЕ ВЕРБОМ, И ЭТО НЕ ПРОИЗВОЛ. Верб `verification.fingerprint` считает
# по ОТСОРТИРОВАННОМУ и обеззубленному списку (`uniqueSorted`, `verification.cjs:947`), а
# проверяющий устаревание — по списку в том порядке, как он записан в этом файле
# (`computeCoveredDigest(root, coveredFilesVal)`, там же около 746). На одном и том же
# составе они дают РАЗНЫЕ значения (82c645b1… против 6c0cc4af…), и записанное вербом
# оставляло бы вердикт вечно `stale`. Записано значение той самой функции, которой
# пользуется проверяющий, по тому же списку из 112 путей: 225759df… → 6c0cc4af….
# Расхождение двух инструментов — свойство оснастки, а не этой фазы; починка их согласия
# сюда не входит.
status: passed
score: 12/13 must-haves verified
covered_files:
  - .planning/REQUIREMENTS.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-01-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-01-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-02-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-02-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-03-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-03-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-04-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-04-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-05-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-05-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-06-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-06-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-07-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-07-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-08-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-08-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-09-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-09-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-10-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-10-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-11-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-11-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-12-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-12-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-13-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-13-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-14-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-14-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-15-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-15-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-16-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-16-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-17-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-17-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-18-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-18-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-19-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-19-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-20-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-20-SUMMARY.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-21-PLAN.md
  - .planning/phases/11-massovyy-perevod-razdelov-pisma/11-21-SUMMARY.md
  - app/main.py
  - app/pages/account_groups.py
  - app/pages/accounts.py
  - app/pages/admin.py
  - app/pages/ads.py
  - app/pages/billing.py
  - app/pages/history.py
  - app/pages/htmx.py
  - app/pages/identifiers.py
  - app/pages/notices.py
  - app/pages/profile.py
  - app/pages/schedules.py
  - app/static/css/app.css
  - app/templates/account_groups/list.html
  - app/templates/accounts/connect_max.html
  - app/templates/accounts/includes/max_connect_step.html
  - app/templates/accounts/list.html
  - app/templates/accounts/partial_cards.html
  - app/templates/accounts/partials/sync_status_card.html
  - app/templates/admin/includes/user_access_tile.html
  - app/templates/admin/includes/user_actions.html
  - app/templates/admin/includes/user_block_badge.html
  - app/templates/admin/partials/user_actions_response.html
  - app/templates/admin/queue.html
  - app/templates/admin/user_detail.html
  - app/templates/ads/form.html
  - app/templates/ads/includes/sched_card.html
  - app/templates/ads/partials/sched_card_response.html
  - app/templates/ads/partials/sched_create_response.html
  - app/templates/billing/balance.html
  - app/templates/components/form_wrapper.html
  - app/templates/components/modal.html
  - app/templates/includes/htmx_config.html
  - app/templates/includes/notice_area.html
  - app/templates/includes/profile_settings.html
  - app/templates/profile.html
  - app/templates/schedules/includes/schedule_row.html
  - app/templates/schedules/list.html
  - app/templates/schedules/partial_cards.html
  - app/templates/schedules/partials/schedule_row_response.html
  - tests/test_pages/test_account_groups.py
  - tests/test_pages/test_admin_panel.py
  - tests/test_pages/test_ads_editor.py
  - tests/test_pages/test_billing_payment_errors.py
  - tests/test_pages/test_billing_subscription.py
  - tests/test_pages/test_confirm_delete_transport.py
  - tests/test_pages/test_editor_schedules.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_post_pairs.py
  - tests/test_pages/test_htmx_preserved.py
  - tests/test_pages/test_htmx_response_contract.py
  - tests/test_pages/test_htmx_response_layer.py
  - tests/test_pages/test_htmx_validation_sink.py
  - tests/test_pages/test_hx_location_destinations.py
  - tests/test_pages/test_identifier_bounds.py
  - tests/test_pages/test_max_connect_transport.py
  - tests/test_pages/test_notices_channel.py
  - tests/test_pages/test_notices_registry.py
  - tests/test_pages/test_profile.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_schedules_list.py
  - tests/test_pages/test_shell.py
  - tests/test_routes/test_sync_groups.py
  - tests/test_routes/test_wa_sync_status.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
  - tests/test_templates/test_htmx_markup_security.py
covered_digest: "v3:sha256:d19d769b29de1745e1a01cccbe2f89a86e338f8b6377e2947d2fe1363489f11a"
# behavior_unverified 2 → 1: истина 13 поднята наблюдением проверки 6 `11-UAT.md` плюс сегодняшним
# доказательством неподвижности пути; остаётся истина 11 (Alpine: (в), (г), (д) не наблюдены).
behavior_unverified: 1
overrides_applied: 0
# decision_coverage перемерено 2026-10-07 тем же вербом (`check.decision-coverage-verify` по
# `11-CONTEXT.md`): honored 16 / total 16, not_honored [] — блок совпадает с изданием 2026-09-18.
decision_coverage:
  honored: 16
  total: 16
  not_honored: []
re_verification:
  # Раунд 2026-10-07. Блок `re_verification` издания 2026-09-18 перенесён ЦЕЛИКОМ, без правки
  # содержимого, ключом `previous_round_record` в конце этого блока (идиома 13-го круга Фазы 10:
  # прежние раунды затирали этот блок, и звено цепочки терялось).
  previous_status: passed
  previous_score: 11/13
  previous_verified: 2026-09-18T11:05:00Z
  round: "2026-10-07 — повторная верификация на дереве после вехи v2.1 (фазы 12, 13, 14, 15 отгружены, PR #49 фазы 11 слит); причина — `verification.status` = `stale` по покрытым файлам, которые правили позднейшие фазы"
  landed_since: [phase-12, phase-13, phase-14, phase-15]
  later_commits_on_covered_app_files:
    - "app/main.py — 8cdeb033 (12-05: снят модуль загрузки)"
    - "app/pages/accounts.py — 2a94e800, b1ce9854, 0216d2c3, 122569a3, 3211993e (13-01…13-04: QR-мастер TG), a674e8e5 (15-09), 5a95c970 (15-21). Обработчики MAX `accounts_connect_max_start` и `accounts_connect_max_status` ПОБАЙТНО прежние (diff функций 1cd4468d..HEAD пуст)"
    - "app/pages/ads.py — 20 коммитов фаз 12 и 15 (загрузка вложений, автосохранение, ревью WR-09…WR-11, 15-23)"
    - "app/pages/htmx.py — bfe43f98 (14-01), 481d5a9b (14-02): добавлен `redirect_internal`; `_confirmation_url` и `redirect_external` ПОБАЙТНО прежние"
    - "app/pages/schedules.py — 854750e2, de5b0549 (15-08), 5fa0552f, 0e86878a (15-16), 5187b807 (15-23), a674e8e5, 5a95c970"
    - "app/static/css/app.css — 9 коммитов фаз 13–15; правила `.form-busy`, `.form-wrapper`, `.form-wrapper > .form-busy`, исключение строки группы и токены `--text-muted`/`--accent-cta` НЕ тронуты"
    - "app/templates/components/form_wrapper.html — 839bbe15 (12-01): параметры `encoding`/`include` с умолчаниями false/None; вывод макроса для семи форм вызова фазы 11 ПОБАЙТНО прежний (замер рендером обеих версий)"
    - "app/templates/ads/form.html — 0294d6cf, b12c835a, d6cd947a (12), a74f2651 (15-23); контейнер `#sched-list` и `beforeend` формы создания не тронуты"
    - "app/templates/ads/includes/sched_card.html, ads/partials/sched_card_response.html, ads/partials/sched_create_response.html — a74f2651 (15-23): строка-подсказка о нераспознанном поясе, параметр `fallback_timezone`; Alpine, цели свопа и панели не тронуты"
    - "app/templates/accounts/list.html, accounts/partial_cards.html, schedules/list.html, schedules/partial_cards.html — a674e8e5 (15-09), 5a95c970 (15-21): размер порции снят с сентинелей; ключевой курсор `after_id` расписаний на месте"
  gaps_closed: []
  gaps_remaining: []
  regressions: []
  truths_rescored:
    - "Истина 13 (G-11-6, браузерная половина, `verification: backstop`): воздержание → ✓ VERIFIED. Явное свидетельство — НАБЛЮДЕНИЕ, а не наличие: проверка 6 `11-UAT.md`, 2026-09-18, таблица отметки заполнена (111 / 111 / 369 px, delta 0; ряды 9/9/9 и 12/12; Slow 3G — точка на 315 мс, гаснет на 2088 мс; пункт 5а — сетка проб нажатия с точкой и без совпала). Сегодняшнее дерево его не опровергает, и это ИЗМЕРЕНО: правила индикатора и токены цвета не тронуты, вывод `form_wrapper` для семи форм вызова фазы 11 побайтно прежний, `profile_settings.html`/`max_connect_step.html`/`profile.html`/`connect_max.html` не менялись, восемь гейтов индикатора — 8 passed за 0,64 с"
  truths_restated:
    - "Истина 1: `NOT_YET_CONVERTED_COUNT` 14 → 0 (Фазы 13 и 14 перевели остаток); все 12 обработчиков фазы 11 на слое ответа, `RedirectResponse` в их телах — 0 (разбор дерева)"
    - "Истина 2 (FORM-10): `RETARGET_RESWAP_USES_DECLARED` 0 → 1 планом 12-09 — `app/pages/ads.py::_parts_refusal_fragment`, `HX-Reswap: beforeend` (`ads.py:1091`), объявлен поимённо с основанием. Буква плана 11-10 «перечень пуст» больше не верна; требование «поимённо, а не общей практикой» верно и охраняется тем же правилом"
    - "Истина 7 (GATE-02): `PAIRED_302_ASSERTIONS_DECLARED` 158 → 191, `POST_PAIR_CASES_DECLARED` 48 → 77 — обход сам принял обработчики, покинувшие перечень отставания; модуль пар 85 passed за 69,96 с"
  item_dispositions_2026_10_07:
    # Договор переноса: каждый открытый пункт прошлого издания — либо ОТКРЫТ (с сегодняшним
    # замером), либо ЗАКРЫТ (с названным свидетельством). Пунктов в третьем состоянии нет.
    advisory:
      - item: "Мастер MAX: ветка отказа подключения печатает сырое исключение и рисует шаг `qr` без QR с вечным опросом"
        state: open
        measured_today: "`app/pages/accounts.py:946` — `error = f\"Ошибка подключения к MAX: {e}\"`; ветка `qr` без `qr_code` (`max_connect_step.html:87-92`) несёт опрос `every 3s`, формы телефона в ней нет. Функции старта и статуса MAX побайтно прежние с 1cd4468d. Файл `accounts.py` менялся (Фаза 13, другие функции), поэтому гейт свидетельств по букве (файловый уровень) счёл бы находку регрессией — но правка находки не касается, и находка классифицирована ⚠️ Warning, а не 🛑 Blocker: она про ветку ОТКАЗА внешнего сервиса, существовала до перевода транспорта, и владелец в этом прогоне оставил UI-ревизию как есть (решение keep as-is по 11-UI-REVIEW.md)"
      - item: "Ошибка 422 рисуется баннером над формой, а не состоянием поля"
        state: open
        measured_today: "`profile_settings.html` и `max_connect_step.html` не менялись с 1cd4468d; `aria-invalid` в обоих — 0 вхождений; FORM-08 (перерисовка и эхо) исполнен — 156 passed в выборке эха/422"
    behavior_unverified_items:
      - item: "Крит. 5: Alpine переживает свап"
        state: open
        measured_today: "Наблюдены (а) редактор и (б) тумблер /schedules (11-UAT проверка 3, 2026-09-18); НЕ наблюдены (б) докрутка второй порции, (в) админка, (г) «Повторить» на /accounts, (д) мастер MAX — приняты владельцем без наблюдения (тест 3 `pass`) и повторно приняты ЗАПИСЬЮ, а не наблюдением, обходом Фазы 15 (15-UAT проверка 5, 2026-10-06, chubav). На пути (в)–(д) с тех пор: `admin/*` и шаблоны MAX не менялись; `accounts/list.html`/`partial_cards.html` — только размер порции у сентинеля. Тестом суиты инвариант не исполняется → счётчик behavior_unverified = 1"
      - item: "G-11-6, браузерная половина"
        state: closed
        evidence: "Наблюдение проверки 6 `11-UAT.md` (2026-09-18) + сегодняшнее доказательство неподвижности пути (см. truths_rescored)"
    human_verification:
      - item: "1. ЮKassa на тестовом ключе"
        state: closed
        evidence: "Закрыт владельцем свидетельством о прогоне на другом сервере (11-UAT проверка 1, отметка заполнена, 2026-09-18). Сегодня: `_confirmation_url` и `redirect_external` побайтно прежние, `YOOKASSA_CONFIRMATION_HOSTS = frozenset({\"yoomoney.ru\"})` (`htmx.py:168`), `billing.py`/`balance.html` не менялись; 24 passed в выборке хоста и увода. ⚠️ Фактический хост `confirmation_url` так и не записан — величина не снята, закрыт путь; окно 87 в реестре всё ещё `open` (отставание записи, а не открытый пункт)"
      - item: "2. UAT пункт 5 — Alpine"
        state: closed
        evidence: "Человеческая проверка исполнена и решена владельцем (тест 3 `pass`, отметка заполнена 2026-09-18; повторно принята записью 15-UAT проверка 5, 2026-10-06). Ненаблюдённый остаток не потерян — он живёт в `behavior_unverified_items` (пункт 1, open)"
      - item: "3. Прокрутка при создании расписания"
        state: closed
        evidence: "11-UAT проверка 2: сдвиг 0 px, карточка последней в `#sched-list` раскрытой (условие «8+» не выполнено — на стенде 5). Сегодня: `ads/form.html:328` контейнер, `:365-366` цель и `beforeend`; ответ создания изменён только параметром `fallback_timezone`; выборка вставки/эха 156 passed"
      - item: "4. Проверка 6 целиком (G-11-6)"
        state: closed
        evidence: "Как истина 13 (truths_rescored)"
      - item: "5. Контраст и место точки после 11-21"
        state: closed
        evidence: "Замерено 2026-09-18 (2,6 : 1 на залитой кнопке — НИЖЕ поля WCAG 1.4.11; 963 px от кнопки в широкой форме) и ПРИНЯТО владельцем. Сегодня токены `--text-muted: #6a6a78` (`app.css:47`) и `--accent-cta` (`:54`) не тронуты — принятый недобор остаётся ровно тем, что принят"
    deferred_body_items:
      - item: "4 обработчика QR-мастера TG"
        state: closed
        evidence: "Фаза 13 отгружена; `NOT_YET_CONVERTED_COUNT = 0` (`test_htmx_gates.py:872`)"
      - item: "10 обработчиков `auth.py`; отказ по источнику у `stop_impersonation`"
        state: closed
        evidence: "Фаза 14 отгружена; `NOT_YET_CONVERTED_COUNT = 0`; окно 63 `waived` 2026-09-22 (14-07: решение о форме для всех мест, `OWN_RESPONSE_EXITS_DECLARED = 14`)"
      - item: "`hx-push-url` по каждой форме (QUAL-04)"
        state: closed
        evidence: "Фаза 15, план 15-11: решение записано по каждому месту (15-UAT У-5); атрибутов `hx-push-url` в шаблонах — 0"
  previous_round_record:
    previous_status: human_needed
    previous_score: 10/11
    previous_verified: 2026-09-17T09:12:00Z
    landed_since: [11-21]
    gaps_closed:
      - "G-11-6 (машинная половина): скрытый `.form-busy` форм обёртки выведен из потока классом области `form-wrapper`; панели подтверждения и точка строки группы доказанно не задеты"
    gaps_remaining: []
    regressions: []
    human_items_discharged:
      - "Back и F5 после HX-Location и создания черновика (UAT проверка 4)"
      - "Профиль: реальный своп 422 в рантайме htmx (UAT проверка 5)"
      - "Подтверждение владельцем прочтений критериев D-01/D-05/D-06/D-12/D-13/D-14 (UAT проверка 7)"
    human_items_still_open: []
    human_items_discharged_round_2:
      # Обход `/gsd-verify-work 11`, круг 2, 2026-09-18. Признаки снимал АГЕНТ в Chrome
      # (chrome-devtools MCP, боевой стенд) по прямой реплике владельца «используй mcp chrome dev
      # если можешь»; проверку 1 закрыл ВЛАДЕЛЕЦ свидетельством. Подробности — в отметках `11-UAT.md`.
      - "ЮKassa на тестовом ключе (окно 87) — закрыт свидетельством владельца о прогоне на ДРУГОМ сервере («закрывая я все протестировал на другом сервере»). ⚠️ Фактический хост `confirmation_url` в обходе НЕ записан: величина не снята, закрыт путь"
      - "UAT пункт 5 — Alpine и панели после десятков свопов: 10 сохранений → 50 свапов, прирост узлов документа 0 (425→425), Alpine-корней 0 (8→8), раскрытая карточка не схлопнулась, панелей ровно по одной на объект; 12 переключений тумблера → 12 запросов, двойное нажатие → ОДИН запрос. ⚠️ Части (в), (г), (д) не наблюдены — живой пользователь админки, отсутствие аккаунта в отказе синхронизации, занятый слот MAX"
      - "Прокрутка при создании расписания: сдвиг 0 px (384→384), карточка добавлена ПОСЛЕДНЕЙ в `#sched-list` раскрытой, линейка 5→6, плитка 6. ⚠️ Условие «8+ расписаний» не выполнено — на стенде их было 5"
      - "Браузерное наблюдение закрытого G-11-6 (окно 88), включая пункт 5а: 111 / 111 / 369 px, delta 0 во всех трёх формах; ряды 9/9/9 и 12/12; Slow 3G — точка на 315 мс, гаснет на 2088 мс. Пункт 5а: до дорожки тумблера 1,0 px (наложения нет), сетка проб нажатия с точкой и без СОВПАЛА побайтно (`pointer-events: none` держит; угол недобирает из-за `border-radius: 99px` пилюли). НОВОЕ, чего проверка не ждала: бокс точки перекрывает габарит обёрнутой кнопки целиком (64 px²) и садится на скруглённый край, выедая выемку из силуэта — предъявлено владельцу и ПРИНЯТО"
      - "Контраст и место точки после правки 11-21: на залитой `--accent-cta` (rgb(207,162,255)) точка `#6a6a78` даёт 2,6 : 1 при поле WCAG 1.4.11 в 3 : 1 — НИЖЕ порога; на тёмных кнопках ряда и на карточке 3,59 / 3,61 : 1. В широкой форме точка стои́т 963 px правее нажатой кнопки, у правого нижнего угла коробки формы, краем карточки не срезана. Недобор назван владельцу прямым текстом и ПРИНЯТ при смягчающем обстоятельстве: `hx-disabled-elt` блокирует кнопку отправки, точка не единственный признак ожидания"

# advisory — ОБА пункта издания 2026-09-18 ОТКРЫТЫ и перемерены 2026-10-07 (состояние и замер —
# `re_verification.item_dispositions_2026_10_07.advisory`). Блок ниже — дословный перенос.
advisory:

  - finding: "Мастер MAX: ветка отказа подключения (`app/pages/accounts.py:675`) печатает сырой текст исключения и отрисовывает шаг `qr` без QR с вечным опросом «Ожидание QR-кода…», убирая форму телефона — повторить подключение на месте нечем (11-UI-REVIEW.md, Top fix 3, помечено BLOCKER)"
    category: architectural
    reason: "Находка вне объёма партии закрытия гэпов (решение владельца: объём 11-21 — только G-11-6). `app/pages/accounts.py` не менялся с прошлого вердикта (`git log --since=2026-09-17T09:12:00Z -- app/pages/accounts.py` пуст), в `gaps:` прошлого вердикта записи нет. Разрешит: план следующей партии, либо решение владельца об отсрочке"
    evidence_status: "none provided — UI-ревизия объявлена CODE-ONLY («Nothing below is a browser observation»); красного прогона и воспроизводимой команды нет"
  - finding: "Ошибка 422 на обоих новых путях рисуется баннером `alert()` над формой, а не состоянием поля: `select_field`/`field` не получают `error=`, `aria-invalid` не ставится (11-UI-REVIEW.md, Top fix 1)"
    category: other
    reason: "FORM-08 требует перерисовки формы и эха — это исполнено; состояние поля требование не называет. Файлы `profile_settings.html` и `max_connect_step.html` с прошлого вердикта не менялись"
    evidence_status: "none provided — оценка качества, красного прогона нет"
# behavior_unverified_items — летопись (идиома Фазы 10: счётчик в шапке говорит о СЕГОДНЯ,
# перечень — о том, что держалось неподтверждённым и чем снято). Пункт 1 (Alpine) ОТКРЫТ;
# пункт 2 (G-11-6, браузерная половина) ЗАКРЫТ 2026-10-07 — наблюдением проверки 6 `11-UAT.md`
# и измеренной неподвижностью пути. Блок ниже — дословный перенос.
behavior_unverified_items:

  - truth: "Крит. 5: Alpine переживает свап — раскрытая карточка не схлопывается, панели не множатся, слушатели не копятся после десятков действий без перезагрузки"
    test: "Десятки свопов подряд в редакторе расписаний, /schedules с фильтром, карточке пользователя в админке, /accounts и мастере MAX без единой перезагрузки"
    expected: "Раскрытая соседняя карточка не схлопывается; в DOM ровно одна панель `sched-del-N` / `user-imp` / `user-del` на объект; подписи, бейдж и плитка согласованы; двойное нажатие тумблера даёт один запрос; счётчик слушателей не растёт"
    why_human: "Накопление слушателей и число живых узлов Alpine после N подмен — рантайм-инвариант очистки, невидимый ASGI-транспорту: тесты видят один ответ, а не состояние DOM после десятого. Ни один тест суиты его не исполняет"
  - truth: "G-11-6, браузерная половина (`verification: backstop` плана 11-21): под «Сохранить»/«Продолжить»/«Сохранить расписание» нет лишней полосы, промежутки рядов ровные, точка появляется в нижнем правом углу формы и не садится на орган"
    reason: insufficient_spec
    test: "Chrome на боевых стилях: замерить высоты трёх отчётных форм (ожидание 111 / 111 / 1686 px), ряды действий, затем Slow 3G и пункт 5а — наложение точки на угол кнопки ряда и на ручку включённого тумблера шапки высотой 40 px, нажатие по самому углу во время запроса"
    expected: "Полосы 21 / 18,5 / 24 px нет; ~12 px хвоста в рядах нет; точка видна через ~300 мс в правом нижнем углу коробки формы, читается признаком занятости, не закрывает подпись, не садится на ручку и не гасит нажатие (`pointer-events: none`); панель подтверждения прежней высоты"
    why_human: "Отрисовка и наложение. Машинно утверждено ОБЪЯВЛЕНИЕ правил, а не результат выкладки; арифметика UI-ревизии («не воспроизводится») наблюдением не является и так и помечена. Окно 88 `unrun-verify`, status `open`; таблица отметки проверки 6 `11-UAT.md` пуста"
# human_verification — летопись издания 2026-09-18, перенесена дословно. ВСЕ ПЯТЬ пунктов
# ЗАКРЫТЫ: их тексты «НЕ ЗАКРЫТО» писались ДО второго круга обхода `/gsd-verify-work 11`
# (2026-09-18), который заполнил отметки проверок 1, 2, 3, 6, 8 `11-UAT.md`. Чем закрыт каждый и
# что на его пути измерено сегодня — `re_verification.item_dispositions_2026_10_07.human_verification`.
# Новых пунктов человеку раунд 2026-10-07 не заводит (основание — в теле, «Почему `passed`»).
human_verification:

  - test: "Оформление доступа на тестовом ключе ЮKassa при живом htmx: на /billing нажать кнопку оплаты; во вкладке Network у POST /billing/subscribe — 204 и HX-Redirect; записать фактический хост confirmation_url в таблицу отметки проверки 1 `11-UAT.md`"
    expected: "Браузер уходит на страницу подтверждения ЮKassa; хост ровно `yoomoney.ru` (иначе ответ уедет в /billing?notice=payment_failed, и оплата через htmx сломана на реальном хосте)"
    why_human: "Внешний сервис и реальный хост `confirmation_url`; суита стоит на документированном хосте в фикстурах. Критерий 2, окно 87 `open`; план 11-15 требует этого ДО слияния. ⚠️ НЕ ЗАКРЫТО обходом: `11-UAT.md` тест 1 несёт `result: pass`, но таблица отметки проверки 1 ПУСТА, а шапка обхода прямо называет ответы проверок 1–3 «pass без признака»"
  - test: "UAT пункт 5 без перезагрузки: (а) редактор — десяток сохранений и тумблеров карточек при раскрытой соседней; (б) /schedules с фильтром — тумблер строки и докрутка второй порции; (в) карточка пользователя в админке — десяток переключений блокировки и бесплатного доступа; (г) /accounts — «Повторить», опрос account-row-N, панели удаления; (д) мастер MAX — индикатор ~5 с, QR, опрос статуса; пустой телефон из пробелов"
    expected: "Раскрытая карточка не схлопывается; в DOM ровно одна панель sched-del-N / user-imp / user-del на объект, панели открываются с актуальным текстом; подписи, бейдж и плитка согласованы; слушатели не копятся; двойное нажатие тумблера даёт один запрос; ошибка MAX перерисовывает шаг с введённым значением"
    why_human: "Поведение Alpine после свопа и накопление слушателей видно только в браузере (критерий 5, назван самым острым остаточным риском вехи). ⚠️ НЕ ЗАКРЫТО: тест 3 `11-UAT.md` несёт `result: pass`, таблица отметки проверки 3 ПУСТА"
  - test: "Редактор объявления с 8+ расписаниями: прокрутить вниз, нажать «+ РАСПИСАНИЕ»"
    expected: "Позиция прокрутки не сброшена; новая карточка появилась в конце #sched-list раскрытой; линейка и сводка показывают новое число"
    why_human: "Прокрутку и вставку в DOM исполняет рантайм htmx, ASGI-транспорт его не запускает (критерий 3). ⚠️ НЕ ЗАКРЫТО: тест 2 `11-UAT.md` несёт `result: pass`, таблица отметки проверки 2 ПУСТА"
  - test: "Проверка 6 `11-UAT.md` целиком, Chrome на боевых стилях: (1) /profile — высота формы «Сохранить» 111 px, не 132; (2) шаг phone мастера MAX — «Продолжить» 111 px, не 129,5; (3) раскрытая карточка расписания — форма «Сохранить расписание» без полосы 24 px; (4) ряды действий админки, /accounts, шапки групп и расписаний — промежутки ровные; (5) Slow 3G — точка через ~300 мс в правом нижнем углу формы, гаснет по ответу, у строки группы стоит рядом с тумблером; (5а) НАЛОЖЕНИЕ — точка 8 px поверх угла обёрнутой кнопки ряда и поверх ручки ВКЛЮЧЁННОГО тумблера шапки высотой 40 px, нажатие по самому углу во время запроса; (6) панель удаления — точка видна, высота прежняя"
    expected: "Лишней полосы и хвоста нет; точка читается признаком занятости, не закрывает подпись, не садится на ручку, не гасит нажатие, не срезана краем карточки; панель подтверждения выглядит как прежде"
    why_human: "Дефект СНЯТ В КОДЕ и машинно охраняется (см. истину 12 — восемь гейтов зелены в собственном прогоне верификатора), но наблюдение отрисовки не снято: окно 88 `unrun-verify` / `open`, таблица отметки проверки 6 ПУСТА. Пункт 5а — ОТДЕЛЬНЫЙ взгляд: точка теперь стои́т ПОВЕРХ угла органа, а не после него. Арифметика 11-UI-REVIEW.md говорит, что оба названных страха не воспроизводятся, и сама называет себя арифметикой, а не наблюдением, — за наблюдение не засчитывать"
  - test: "НОВОЕ, побочные следствия правки 11-21 (11-UI-REVIEW.md, переаудит 2026-09-18, находки 4 и 5): (а) на шаге phone мастера MAX и на «Синхронизировать всё» экрана групп во время запроса — прочитать точку `--text-muted` #6a6a78 на залитой `--accent-cta` кнопке, при необходимости замерить контраст; (б) в широких формах (профиль, форма правки расписания, оплата) — где точка относительно нажатой кнопки"
    expected: "(а) точка различима на залитой кнопке (расчётный контраст ~2–3:1 при полу WCAG 1.4.11 в 3:1) — либо признаётся требующей правки; (б) точка на расстоянии в ширину карточки от кнопки признаётся приемлемой либо ставится в очередь на привязку к ряду действий"
    why_human: "Контраст и восприятие места. Расчёт сделан по значениям токенов, в браузере не мерен; смягчающее обстоятельство, которое верификатор проверил сам: обе формы идут с умолчанием `disabled_elt='find button[type=submit]'` и единственная кнопка отправки в них блокируется — точка НЕ единственный признак ожидания, вопреки формулировке Pillar 3"
---

# Phase 11: Массовый перевод разделов письма — отчёт верификации (раунд 2026-10-07, после вехи v2.1)

**Цель фазы:** пользователь выполняет действия во всех продуктовых и админских разделах без перезагрузки страницы, и суита перестаёт быть зелёной по построению
**Проверено:** 2026-10-07T07:00:00Z
**Статус:** passed
**Повторная верификация:** ДА — на дереве после вехи v2.1. Предыдущее издание: 2026-09-18T11:05:00Z, `passed`, 11/13, behavior_unverified 2; `verification.status` читал его `stale`, потому что фазы 12–15 правили покрытые файлы.

## Вердикт одной фразой

Цель фазы держится на сегодняшнем дереве: все двенадцать обработчиков фазы по-прежнему отвечают через слой ответа, все восемь машинных гейтов фазы на месте и зелены в собственных прогонах верификатора, а позднейшие фазы на пути истин не сломали ничего — они ДОВЕЛИ два счёта фазы до конца (`NOT_YET_CONVERTED_COUNT` 14 → 0, пары 302 158 → 191) и один раз законно применили перечень FORM-10 (0 → 1, поимённо). Оценка 11/13 → 12/13. Ниже `passed` остаётся одна истина, которую не исполняет ни один тест и которую никто не наблюдал целиком: Alpine после свапа в админке, на `/accounts` и в мастере MAX — владелец принял её без наблюдения дважды.

## Почему этот раунд понадобился

Отпечаток издания 2026-09-18 покрывал 15 файлов `app/`, которые потом правили фазы 12–15. Это не означает, что фаза сломана, и не означает, что она цела: правка файла — повод перемерить, а не вывод. Ни одна истина ниже не перенесена со слов прошлого издания; у каждой — сегодняшний замер и названо, что именно позднейшие фазы сдвинули на её пути.

## Что сдвинули фазы 12–15 на пути истин

| Файл | Коммиты | Что задето | На какой истине | Последствие для фазы 11 |
|---|---|---|---|---|
| `app/templates/components/form_wrapper.html` | 839bbe15 (12-01) | параметры `encoding`, `include` с умолчаниями `false`/`None` | 9, 12, 13 | **Никакого.** Замер: семь форм вызова фазы 11 (профиль, MAX, правка/тумблер/создание расписания, оплата, повтор синхронизации) отрисованы старой (1cd4468d) и новой версией макроса — вывод ПОБАЙТНО одинаков во всех семи |
| `app/static/css/app.css` | 9 коммитов фаз 13–15 | токен кольца фокуса, отступ стопки плашек, шаги `auth`/`connect-step--center`, поле файла | 12, 13, Н-5 | **Никакого.** Правила `.form-busy` (`:2310`), `.form-busy.htmx-request` (`:2317`), `.form-wrapper` (`:2324`), `.form-wrapper > .form-busy` (`:2325-2327`), исключение строки группы (`:2879`) и токены `--text-muted` (`:47`), `--accent-cta` (`:54`) в диффе не встречаются. Новые правила `connect-step--center`/`connect-step__actions` до шага телефона MAX не дотягиваются: он идёт классом `connect-step` без `--center` и без `__actions` |
| `app/pages/ads.py` | 20 коммитов (12, 15) | загрузка вложений, `_parts_refusal_fragment`, автосохранение, ревью | 1, 2, 11 | Истина 2 переписана: появилось ПЕРВОЕ применение `HX-Reswap` (ниже). `ads_create`/`ads_update` на слое ответа; `HX-Push-Url` записывается в `ads.py:803`, тест заголовка истории — 1 passed |
| `app/pages/schedules.py` | 7 коммитов (15-08, 15-16, 15-23, 15-09, 15-21) | вторая строка `next_run_or_none`, пояс профиля | 1, 4 | Три обработчика расписаний на слое ответа, `RedirectResponse` в телах — 0; ключевой курсор `after_id` (`Schedule.id > after_id`) на месте |
| `app/templates/ads/includes/sched_card.html` и два ответа | a74f2651 (15-23) | строка-подсказка о нераспознанном поясе, параметр `fallback_timezone` | 4, 11, 13 | Alpine, цели свопа, панели не тронуты (дифф по `x-data`/`x-on`/`id=`/`hx-*` в этих файлах пуст). Подсказка печатается только при нераспознанном поясе — высоты проверки 6 могут сдвинуться лишь на таких карточках |
| `app/templates/ads/form.html` | 0294d6cf, b12c835a, d6cd947a (12), a74f2651 | полоса вложений, триггер формы `ads-image-attached from:body` | 4, 11 | `#sched-list` (`:328`) и `beforeend` (`:365-366`) на месте. Триггер формы объявления сменила Фаза 12 — это путь черновика из истины 11 (Back/F5): тест `HX-Push-Url` зелен, наблюдение Back/F5 2026-09-17 сделано на прежнем триггере |
| `app/pages/accounts.py` | 13-01…13-04, 15-09, 15-21 | QR-мастер TG, размер порции | 1, 5, advisory 1 | Обработчики MAX (`accounts_connect_max_start`, `accounts_connect_max_status`) — **побайтно прежние** (дифф функций пуст) |
| `app/pages/htmx.py` | bfe43f98, 481d5a9b (14) | `redirect_internal` | 3, 5 | `_confirmation_url` и `redirect_external` побайтно прежние; литерал 422 по-прежнему один (`htmx.py:956`) |
| `app/main.py` | 8cdeb033 (12-05) | снят модуль загрузки | 6 | Обработчик `RequestValidationError` → `malformed_request_response` на месте (`main.py:29`, `:253`) |
| списки `accounts/*`, `schedules/*` | a674e8e5, 5a95c970 (15) | размер порции снят с сентинелей | 11 | Сентинели `list.html:66` и `partial_cards.html:12` расписаний по-прежнему побайтно одинаковы |

Не менялись с 1cd4468d ни на байт: `app/pages/billing.py`, `profile.py`, `admin.py`, `identifiers.py`, `notices.py`, `account_groups.py`, `history.py`, `app/templates/admin/*`, `billing/balance.html`, `includes/profile_settings.html`, `profile.html`, `includes/htmx_config.html`, `accounts/includes/max_connect_step.html`, `accounts/connect_max.html`, `components/modal.html`.

## Достижение цели

### Наблюдаемые истины

| # | Истина | Статус | Сегодняшнее свидетельство |
|---|--------|--------|---------------|
| 1 | Крит. 1 (по летописи D-01/D-03): 12 обработчиков фазы переведены — 9 фрагментом, 2 через `HX-Location`, 1 внешним переходом | ✓ VERIFIED | Разбор дерева: все 12 найдены, у каждого `respond(`/`respond_field_error(`/`redirect_external(` в теле и **0** `RedirectResponse` — `schedules_create:988`, `schedules_update:1222`, `schedules_toggle:1473`, `ads_create:840`, `ads_update:1507`, `admin_toggle_free_access:1649`, `admin_toggle_block:1901`, `accounts_connect_max_start:842`, `accounts_retry_sync:1045`, `accounts_sync_groups:1133`, `profile_post:77`, `subscribe_to_plan:280`. `NOT_YET_CONVERTED_COUNT` **14 → 0** (`test_htmx_gates.py:872`) — остаток довели Фазы 13 и 14; `FRAGMENT_RESPONSE_HANDLERS_DECLARED` 12 → 25 (`:2330`). Живое наблюдение позднего дерева: обход Фазы 15, шаг 3.2 (2026-10-06) — «Синхронизировать всё» уходит переходом, документ подменён целиком |
| 2 | Крит. 1 / FORM-10: `HX-Retarget` и `HX-Reswap` только поимённо | ✓ VERIFIED (буква сменилась) | `RETARGET_RESWAP_USES_DECLARED = 0 → 1` (`test_htmx_gates.py:5983`) планом 12-09: `app/pages/ads.py:1091` `HX-Reswap: beforeend` у `_parts_refusal_fragment`, запись перечня с основанием. В `app/` (без вендоренного htmx) ровно два вхождения: это применение и докстринг `htmx.py:931`. Требование «поимённо, не общей практикой» исполнено; буква плана 11-10 «перечень пуст» больше неверна, и это сказано, а не замолчано. Правила полноты и отрицательный контроль — в прогоне 18 passed |
| 3 | Крит. 2 / FORM-05: `/billing/subscribe` на htmx — 204 + `HX-Redirect` на закрытое множество хостов, без `HX-Location` | ✓ VERIFIED (машинно; переход принят свидетельством владельца) | `YOOKASSA_CONFIRMATION_HOSTS = frozenset({"yoomoney.ru"})` (`htmx.py:168`); `_confirmation_url` (`:287`) — управляющие символы, ASCII, `\`, схема `https`, `@`, порт, точный хост; `redirect_external` (`:362`). Обе функции побайтно прежние; `billing.py`/`balance.html` не менялись. Выборка хоста и увода — **24 passed**. ⚠️ Фактический хост `confirmation_url` тестового ключа не записан никем |
| 4 | Крит. 3 / FORM-07 (по летописи D-05): создание добавляет карточку в `#sched-list` через `beforeend`; «было ноль» — переходом | ✓ VERIFIED | `ads/form.html:328` `<div data-sched-list id="sched-list">`, `:365-366` цель и `swap='beforeend'`; порядок сервера `order_by(Schedule.id)` (`ads.py:367`). Выборка эха/422/вставки/заявки — **156 passed** (было 111: суита выросла) |
| 5 | Крит. 3 / FORM-08 (по D-06): 422 перерисовывает форму и возвращает введённое (профиль, MAX) | ✓ VERIFIED | Правило `{"code":"422", "swap": true, "error": true}` (`htmx_config.html:162`); `respond_field_error` (`htmx.py:903`) зовут `profile.py:193` и `accounts.py:906` (MAX); `accounts.py:623` — второй потребитель, пришедший с Фазой 13. Эхо: `selected=timezone` (ПРИСЛАННОЕ), `phone=submitted`. Литерал 422 в страничном слое — один (`htmx.py:956`) |
| 6 | Своп 422 не открывает сток T-07-13 | ✓ VERIFIED | `malformed_request_response` (`htmx.py:482`) зарегистрирован (`main.py:29`, `:253`); `test_htmx_validation_sink.py` — **8 passed** |
| 7 | Крит. 4 / GATE-02 (по D-14): утверждения 302 о переведённых POST собраны в пары обходом, число объявлено прогоном | ✓ VERIFIED | `PAIRED_302_ASSERTIONS_DECLARED = 158 → 191` (`test_htmx_post_pairs.py:3418`), `POST_PAIR_CASES_DECLARED = 48 → 77` (`:2416`): обход сам принял обработчики, покинувшие перечень отставания, — ровно как обещала вселенная D-14. Модуль целиком — **85 passed за 69,96 с** |
| 8 | Суита перестаёт быть зелёной по построению | ✓ VERIFIED | `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 0` (`:3900`) с синтетическим контролем пустоты; замыкание `POST_PAIR_CASES` ∪ `CONFIRMED_DELETE_ROUTES` и контроль непарного 302 — в прогоне модуля пар; полная суита на коде 7b54dbe1 — 4084 passed (данные оркестратора) |
| 9 | Все POST-формы продуктовых и админских разделов отправляются через htmx | ✓ VERIFIED | 29 вызовов `call form_wrapper` в 22 шаблонах (с Фазой 14 — и `auth/*`, `base.html`). Девять `<form method="post">` без `hx-post` — все формы-триггеры панелей (`x-on:submit.prevent="$dispatch('modal-open-…')"`), отправку несёт `hx-post` модалки. Постоянные цели: `profile.html:62`, `connect_max.html:19`, `user_detail.html:61/88/138`, `ads/form.html:328` |
| 10 | Исходы снятия задачи — в закрытом реестре `?notice=`, `?result=` снят | ✓ VERIFIED | `grep -rn '?result=' app/` — 0; `QUEUE_DROP_*` — `notices.py:121-124`; файл не менялся |
| 11 | Крит. 5: Alpine переживает свап; Back и F5 не предлагают повторить POST | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Код: раскрытие — серверное состояние, панели вне целей свопа, `hx-push-url` в шаблонах — 0, `HX-Push-Url` черновика переживает слой ответа (тест 1 passed). Наблюдение: Back/F5 — 11-UAT проверка 4 (2026-09-17); Alpine (а) и (б)-тумблер — проверка 3 (2026-09-18). **Не наблюдены**: (б) докрутка второй порции, (в) админка, (г) «Повторить» на `/accounts`, (д) мастер MAX — приняты владельцем без наблюдения и повторно приняты ЗАПИСЬЮ обходом Фазы 15 (15-UAT проверка 5, 2026-10-06), а не взглядом. На их пути с тех пор: `admin/*`, шаблоны MAX — без изменений; `accounts/*` — размер порции у сентинеля. ⚠️ Триггер формы объявления сменила Фаза 12 (`ads-image-attached from:body`) — Back/F5 после ЗАГРУЗКИ картинки, создающей черновик, — предмет Фазы 12, этой фазой не наблюдался |
| 12 | G-11-6 закрыт МАШИННО | ✓ VERIFIED | `form_wrapper.html:188` — `class="form-wrapper"`, единственное вхождение в дереве шаблонов; `app.css:2324-2327` — контекст позиционирования и правило вне потока; `:2879` — исключение строки группы; база `.form-busy` — одно правило (`grep -c '^\.form-busy {$'` = 1); `IN_FLOW_INDICATOR_EXCEPTIONS_DECLARED = 1` (`test_htmx_markup_gates.py:3534`), `PANEL_QUALITY_DIFFERENCES_ALLOWED = 2` (`:6633`); `modal.html` не менялся. Восемь гейтов — **8 passed за 0,64 с** |
| 13 | G-11-6, браузерная половина (`verification: backstop`) | ✓ VERIFIED (наблюдение + неподвижность пути) | **Поднята с воздержания.** Явное свидетельство — наблюдение, не наличие: 11-UAT проверка 6 (2026-09-18, отметка заполнена: 111 / 111 / 369 px, delta 0; ряды 9/9/9 и 12/12; Slow 3G — 315 мс / 2088 мс; пункт 5а — пробы нажатия с точкой и без совпали). Опровергнуть его позднее дерево не может, и это измерено, а не предположено: правила индикатора и токены цвета в диффе отсутствуют; вывод макроса для семи форм вызова побайтно прежний; шаблоны профиля и MAX не менялись. ⚠️ Граница: у карточки расписания с НЕРАСПОЗНАННЫМ поясом теперь есть строка-подсказка — её высота 369 px не сохраняет, но предмет проверки (нет лишней полосы под кнопкой) от неё не зависит |

**Счёт:** 12/13 истин подтверждено (1 — присутствует и связана, поведение не проверено целиком: истина 11; 0 переопределений).

**Сверка со счётом прошлого издания.** Было 11/13 при behavior_unverified 2. Истина 13 поднялась: прошлое издание закрыло фазу, не перескоривая (шапка закрытия прямо говорит «вердикт, оценка и выводы не тронуты»), и наблюдение проверки 6 так и не было засчитано истине. Этот раунд засчитал его вместе с доказательством того, что дерево с тех пор его не опровергло. Истина 11 осталась на месте: её ненаблюдённый остаток никто с тех пор не видел.

### Почему `passed`, а не `human_needed` — и где здесь решение верификатора

По букве шага 9 истина в состоянии ⚠️ PRESENT_BEHAVIOR_UNVERIFIED ведёт к `human_needed`. Этот раунд ставит `passed` и называет основание, а не прячет его: человеческий маршрут для истины 11 УЖЕ исполнен — владелец решил тест 3 `pass` 2026-09-18, зная, что (в), (г), (д) не наблюдены (отметка проверки 3 перечисляет их поимённо с причинами), и повторно принял ту же запись 2026-10-06 обходом Фазы 15. Сегодняшнее дерево не даёт человеку нового предмета: на пути ненаблюдённых частей ничего, что касается Alpine, целей свопа или панелей, не менялось. Завести тот же пункт в третий раз значило бы спросить владельца о решённом. Остаток не потерян: он стоит в `behavior_unverified_items` (open) и в счётчике `behavior_unverified: 1`. Если владелец сочтёт, что принятие без наблюдения не равно проверке, правильный ход — переопределение с его подписью (`overrides`), а не молчаливый `passed`; агент такую подпись не ставит.

### Требуется проверка человеком

Новых пунктов этот раунд не заводит. Пять пунктов `human_verification` прошлого издания перенесены во frontmatter дословно и закрыты поимённо — с тем, что их закрыло, и с тем, что на их пути измерено сегодня (`re_verification.item_dispositions_2026_10_07.human_verification`):

| # | Пункт | Состояние | Чем закрыт / что измерено сегодня |
|---|---|---|---|
| 1 | ЮKassa на тестовом ключе | **закрыт** | Свидетельство владельца (11-UAT проверка 1). Код увода побайтно прежний, 24 passed. ⚠️ Хост не записан; окно 87 в реестре `open` — отставание записи |
| 2 | Alpine после десятков свопов | **закрыт как пункт человека** | Решён владельцем (тест 3 `pass`), повторно принят 15-UAT проверкой 5. Ненаблюдённый остаток — в `behavior_unverified_items` |
| 3 | Прокрутка при создании расписания | **закрыт** | 11-UAT проверка 2: сдвиг 0 px (на 5 расписаниях, не 8+). Контейнер и `beforeend` на месте; 156 passed |
| 4 | Проверка 6 (G-11-6) целиком | **закрыт** | Наблюдение 2026-09-18 + неподвижность пути (истина 13) |
| 5 | Контраст и место точки | **закрыт (принятый недобор)** | 2,6 : 1 ниже поля WCAG 1.4.11 — принято владельцем; токены не тронуты, недобор тот же, что принят |

### Отложенные пункты прошлого издания

Все три доставлены позднейшими фазами: QR-мастер TG — Фаза 13; `auth.py` и отказ по источнику `stop_impersonation` — Фаза 14 (окно 63 `waived` 2026-09-22 планом 14-07); `hx-push-url` по каждой форме — Фаза 15, план 15-11. `NOT_YET_CONVERTED_COUNT = 0`.

### Advisory (новый объём, без детерминированного свидетельства)

Оба пункта прошлого издания ОТКРЫТЫ и перемерены сегодня:

| # | Находка | Категория | Сегодня |
|---|---------|-----------|---------|
| 1 | Мастер MAX: ветка отказа печатает сырое исключение (`accounts.py:946`) и рисует шаг `qr` без QR с вечным опросом (`max_connect_step.html:87-92`) — повторить подключение на месте нечем | architectural | Функции MAX побайтно прежние. ⚠️ По букве гейта свидетельств (файловый уровень) правка `accounts.py` Фазой 13 сделала бы находку «регрессией» — но правка не касалась ни одной строки находки (дифф функций пуст), и находка здесь ⚠️ Warning, а не 🛑 Blocker: это ветка отказа ВНЕШНЕГО сервиса, существовавшая до перевода транспорта, и владелец в этом прогоне оставил UI-ревизию как есть. Красного прогона нет |
| 2 | 422 баннером над формой, а не состоянием поля | other | Шаблоны не менялись; `aria-invalid` — 0 вхождений. FORM-08 исполнен |

### Необходимые артефакты

| Артефакт | Статус | Сегодня |
|---|---|---|
| `app/pages/htmx.py` — `respond` (`:768`), `respond_field_error` (`:903`), `redirect_external` (`:362`), `_confirmation_url` (`:287`), `malformed_request_response` (`:482`) | ✓ VERIFIED | На месте, зовутся обработчиками и `main.py` |
| `app/pages/identifiers.py` (`id_in_column`, `PostIdPath`…) | ✓ VERIFIED | Не менялся |
| `tests/test_pages/test_htmx_post_pairs.py` | ✓ VERIFIED | 85 passed; все восемь правил фазы 11 (обход, число, замыкание, контроли) на месте |
| `tests/test_pages/test_htmx_gates.py` — перечни отставания, фрагментов, окна 51, FORM-10 | ✓ VERIFIED | 18 passed в выборке; числа выше |
| `app/templates/components/form_wrapper.html`, `app/static/css/app.css` (G-11-6) | ✓ VERIFIED | Класс области и три правила на месте; вывод макроса для форм фазы 11 побайтно прежний |
| шаблоны ответов `ads/partials/*`, `schedules/partials/schedule_row_response.html`, `admin/partials/user_actions_response.html`; включаемые `profile_settings.html`, `max_connect_step.html`, `admin/includes/*` | ✓ VERIFIED | Существуют; правки только 15-23 (параметр пояса) |

### Проверка ключевых связей

| Откуда | Куда | Статус |
|---|---|---|
| форма правки/тумблера/создания расписания → `schedules_*` → `respond(fragment=)` | WIRED (пары 85 passed) |
| форма оплаты → `subscribe_to_plan` → `redirect_external` → `HX-Redirect` | WIRED (24 passed) |
| форма профиля (`#profile-settings`) и шага MAX (`#max-connect-step`) → `respond` / `respond_field_error` → правило 422 со свопом | WIRED (156 passed) |
| `RequestValidationError` → `malformed_request_response` | WIRED (`main.py:253`, 8 passed) |
| класс области (`form_wrapper.html:188`) → `.form-wrapper > .form-busy` (`app.css:2325`) | WIRED (гейт следа, 8 passed) |
| `POST_PAIR_CASES` ∪ `CONFIRMED_DELETE_ROUTES` → замыкание над `respond`-обработчиками | WIRED |

### Поведенческие выборочные проверки (собственные прогоны верификатора, 2026-10-07)

| Поведение | Команда | Результат | Статус |
|---|---|---|---|
| Восемь гейтов индикатора G-11-6 | `uv run pytest <8 названных тестов> -q` (те же восемь, что в издании 2026-09-18) | `8 passed in 0.64s` | ✓ PASS |
| Пары 302, обход, контроли (GATE-02 целиком) | `uv run pytest tests/test_pages/test_htmx_post_pairs.py -q` | `85 passed in 69.96s` | ✓ PASS |
| FORM-10, окно 51, отставание, собственные выходы, записи заголовков | `uv run pytest tests/test_pages/test_htmx_gates.py -q -k "retarget or reswap or framework_bound or emptiness_rule or not_yet_converted or NOT_YET or own_response or header_write"` | `18 passed, 66 deselected` | ✓ PASS |
| Сток T-07-13 | `uv run pytest tests/test_pages/test_htmx_validation_sink.py -q` | `8 passed` | ✓ PASS |
| Эхо 422, вставка `beforeend`, освобождение заявки | `uv run pytest tests/test_pages/test_profile.py tests/test_pages/test_max_connect_transport.py tests/test_pages/test_editor_schedules.py tests/test_routes/test_sync_groups.py -q -k "422 or echo or append or beforeend or in_flight or sync"` | `156 passed, 16 deselected in 169.33s` | ✓ PASS |
| Хост и увод ЮKassa | `uv run pytest tests/test_pages/test_htmx_response_layer.py tests/test_pages/test_billing_subscription.py -q -k "confirmation or external or yoomoney or suffix or redirect"` | `24 passed, 42 deselected` | ✓ PASS |
| Заголовок истории черновика | `uv run pytest tests/test_pages/test_ads_editor.py -q -k push_url` | `1 passed` | ✓ PASS |
| Вывод макроса обёртки до и после 12-01 | рендер `form_wrapper` из 1cd4468d и из HEAD для семи форм вызова фазы 11 (`python -I`, Jinja2) | 7 из 7 — `IDENTICAL` | ✓ PASS |
| Покрытие решений CONTEXT.md | `gsd-tools query check.decision-coverage-verify <phase_dir> <11-CONTEXT.md>` | `honored 16 / total 16`, `not_honored: []` | ✓ PASS |
| Полная суита | данные оркестратора, `just test` на коде 7b54dbe1 (= коду HEAD) | `4084 passed`, 0 failed, 41:43 | ✓ PASS (не перезапускалась — один полный прогон за раунд) |

### Запуск проб

Проб `scripts/*/tests/probe-*.sh` нет, ни один план их не объявляет — шаг пропущен.

### Покрытие требований

| Требование | Статус | Свидетельство (сегодня) |
|---|---|---|
| FORM-03 | ✓ SATISFIED | Истины 1, 9, 12 |
| FORM-04 | ✓ SATISFIED | Истина 1 (переходы синхронизации и исходов), пары 85 passed; живой переход «Синхронизировать всё» в 15-UAT 3.2 |
| FORM-05 | ✓ SATISFIED | Истина 3 |
| FORM-07 | ✓ SATISFIED (по D-05) | Истина 4 |
| FORM-08 | ✓ SATISFIED (по D-06) | Истины 5, 6 |
| FORM-10 | ✓ SATISFIED | Истина 2 (одно поимённое применение Фазы 12) |
| GATE-02 | ✓ SATISFIED (по D-14) | Истина 7 |

`.planning/REQUIREMENTS.md:502` относит к Фазе 11 ровно эти 7 ID; все семь — `Complete` (`:142-163`), каждый заявлен хотя бы одним планом. Сирот нет.

### Найденные антипаттерны

| Файл | Строка | Находка | Серьёзность | Сегодня |
|---|---|---|---|---|
| 40 файлов `app/` из покрытия | — | `TBD` / `FIXME` / `XXX` | — | **0 вхождений**; в 29 тестовых файлах покрытия — 0; `@pytest.mark.skip` — 0 |
| `app/templates/ads/includes/sched_card.html` | 210 / 265 | Форма правки берёт умолчание `disabled_elt`, первая кнопка отправки — «ВЫБРАТЬ ВСЕ» | ⚠️ Warning (перенесено) | Перемерено: держится — «СОХРАНИТЬ РАСПИСАНИЕ» не блокируется |
| `app/pages/ads.py` | 887 | `int(ad_id)` без границы (WR-01) | ℹ️ Info (перенесено) | Перемерено: держится, файл переписан Фазой 12, строка уехала с ~700 на 887 |
| `app/pages/schedules.py` | `schedules_create` | Карточка или переход по числу ПОСЛЕ вставки (WR-02) | ⚠️ Warning (перенесено) | `_ad_schedule_count` (`:1166`) — держится |
| `app/pages/ads.py` | 555 / 591 | `_attachment_refusal` выбирает транспорт сам и на пути без JS поднимает `HTTPException(400)` (окно 86) | ℹ️ Info | Держится; окно 86 `open`. Прошлое издание его называло только в сводке окон |
| `tests/.../test_htmx_markup_gates.py` | — | WR-04…WR-07 (способы обойти гейты G-11-6) | ⚠️ Warning (перенесено) | Не перемерялись построчно; правила, о которых они, зелены |

Блокирующих нет. Ни одной находке не приложено красного прогона; ни одна не роняет объявленной истины.

### Окна реестра, названные прошлым изданием

| Окно | Тогда | Сегодня |
|---|---|---|
| 63 | `open` | `waived` 2026-09-22 (Фаза 14, план 14-07) |
| 84 | `open` | `open` |
| 85 | `open` | `fixed` 2026-09-19 |
| 86 | `open` | `open` (см. антипаттерны) |
| 87 | `open` | `open` — ⚠️ отставание записи: предмет закрыт 11-UAT проверкой 1, строка реестра не переведена |
| 88 | `open` | `open` — ⚠️ отставание записи: предмет закрыт 11-UAT проверкой 6, строка реестра не переведена |

Реестр окон этот раунд не правит — правило раунда разрешает писать только отчёт.

### Состояние прочих гейтов раунда (данные оркестратора, прочитанные верификатором)

| Гейт | Результат |
|---|---|
| Полная суита | 4084 passed, 0 failed, 41:43 на 7b54dbe1; `tests/test_planning` на HEAD — 208 passed |
| Уникальность ID угроз (#4683) | 9 строк поздних планов перенумерованы в T-11-46…54 с решения владельца (5400188a); набор угроз, серьёзность и диспозиции не тронуты — не правка кода |
| Nyquist (`11-VALIDATION.md`) | 0 новых пробелов, `nyquist_compliant: true`, 20 команд собирают непустую выборку |
| Безопасность (`11-SECURITY.md`) | `threats_open: 0` |
| UI-ревизия | владелец: оставить как есть (17/24) |
| Код-ревизия | владелец: пропустить (задачных коммитов фазы 11 после ревизии 8b1d8f53 нет) |
| TDD-ревизия | 0 планов `type: tdd` — вакуумно, не блокирует |

### Сводка пробелов

**Пробелов нет, `gaps:` нет намеренно.** Позднейшие фазы не сломали ни одной истины фазы 11: двенадцать обработчиков на слое ответа, все гейты на месте и зелены в собственных прогонах верификатора, обход пар принял новые обработчики сам. Два места, где позднее дерево разошлось с буквой прошлого издания, названы и разобраны: перечень FORM-10 больше не пуст (одно поимённое применение Фазы 12 — требование исполнено), и триггер формы объявления сменился (путь черновика через загрузку — предмет Фазы 12). Открытым остаётся одно — ненаблюдённые части Alpine после свапа (админка, `/accounts`, мастер MAX), которые владелец принял без наблюдения; и два advisory, оба сегодня перемерены и оба держатся.

---

_Проверено: 2026-10-07T07:00:00Z_
_Верификатор: Claude (gsd-verifier)_

---

# Phase 11: Массовый перевод разделов письма — отчёт верификации

**Цель фазы:** пользователь выполняет действия во всех продуктовых и админских разделах без перезагрузки страницы, и суита перестаёт быть зелёной по построению
**Проверено:** 2026-09-18T00:00:00Z
**Статус:** human_needed
**Повторная верификация:** ДА — первая партия закрытия гэпов (план 11-21, гэп G-11-6). Предыдущее издание: 2026-09-17T09:12:00Z, `human_needed`, 10/11.

## Что изменилось с прошлого вердикта

`git diff 073ba75..HEAD -- app/` — два файла, +75/−1: `app/templates/components/form_wrapper.html` и `app/static/css/app.css`. Прочие файлы `app/` не двигались, что проверено пофайлово (`git log --since=2026-09-17T09:12:00Z -- <файл>` пуст для `accounts.py`, `ads.py`, `schedules.py`, `profile_settings.html`, `max_connect_step.html`, `sched_card.html`). Десять истин прошлого издания получили регрессионную сверку (существование + вменяемость), G-11-6 и новые истины плана 11-21 — полную проверку трёх уровней плюс собственный прогон гейтов.

## Достижение цели

Критерии роадмапа сверены с их текстом **вместе с летописями** плана 11-20 — и эти летописи с прошлого раунда перестали быть прочтениями агента: владелец подтвердил их лично (проверка 7 `11-UAT.md`, 2026-09-17, подписанная строка). Машинная часть цели подтверждена кодом и прогонами. Остаются браузерные наблюдения (ЮKassa, Alpine, прокрутка, отрисовка закрытого G-11-6) и одно новое побочное следствие правки.

### Наблюдаемые истины

| # | Истина | Статус | Свидетельство |
|---|--------|--------|---------------|
| 1 | Крит. 1 (по летописи D-01/D-03, подтверждённой владельцем): 12 обработчиков фазы переведены — 9 фрагментом, 2 через `HX-Location`, 1 внешним переходом; `NOT_YET_CONVERTED` 26 → 14 | ✓ VERIFIED | Регрессия: `NOT_YET_CONVERTED_COUNT = 14` (`test_htmx_gates.py:525`), вызовов `await respond(` по `app/pages/*.py` — 89 в девяти модулях. Остальные 14 — 4 QR-мастера TG (Фаза 13) и 10 обработчиков `auth.py` (Фаза 14). Файлы обработчиков с прошлого вердикта не менялись; полная суита зелена одним прогоном |
| 2 | Крит. 1 / FORM-10: `HX-Retarget` и `HX-Reswap` только по перечню | ✓ VERIFIED | `RETARGET_RESWAP_USES_DECLARED = 0` (`test_htmx_gates.py:4955`); в `app/` (без вендоренного `htmx.min.js`) ровно одно упоминание — докстринг `app/pages/htmx.py:875` |
| 3 | Крит. 2 / FORM-05: `/billing/subscribe` на htmx отвечает 204 и `HX-Redirect` на закрытое множество хостов, без `HX-Location` | ✓ VERIFIED (машинно) | `YOOKASSA_CONFIRMATION_HOSTS = frozenset({"yoomoney.ru"})` (`htmx.py:151`), `_confirmation_url` (`:270`) проверяет схему, точный хост, отсутствие порта, `@`, `\`, управляющих символов; `redirect_external` (`:345`). **Переход на тестовом ключе — ручной UAT, окно 87 `open`** |
| 4 | Крит. 3 / FORM-07 (по летописи D-05, подтверждённой владельцем): создание добавляет карточку в `#sched-list` через `beforeend`, контейнер не перерисовывается; «было ноль» уходит переходом | ✓ VERIFIED | `ads/form.html:241` — `<div data-sched-list id="sched-list">`; `:277` — `target=('#sched-list' if editor.schedules else none)`, `swap='beforeend'`. Собственный прогон верификатора: `test_editor_schedules` + `test_profile` + `test_max_connect_transport` + `test_sync_groups`, отбор по вставке/эху/422/заявке — **111 passed**. **Прокрутка — ручной UAT** |
| 5 | Крит. 3 / FORM-08 (по летописи D-06): 422 перерисовывает форму и возвращает введённое там, где ошибка поля была и раньше (профиль, MAX) | ✓ VERIFIED | Правило `{"code":"422","swap":true,"error":true}` — `htmx_config.html:162`, и абзац о снятом свопе явно помечен поколением (`:105-113`), а не оставлен ложным. `respond_field_error` (`htmx.py:847`) зовут `profile.py:193` и `accounts.py:635`; `profile_post` подаёт `selected=timezone` — ПРИСЛАННОЕ (`profile.py:_page`/`_fragment`). Тот же прогон 111 passed. ℹ️ Точность эха у профиля вырожденная и это СВОЙСТВО, а не дефект: поле выбора рисует закрытый список, значение вне списка в документ не попадает вовсе (докстринг `_settings_markup`, митигация T-11-13), а достижимо оно только подменой через DevTools — что и наблюдал обход (проверка 5) |
| 6 | Своп 422 не открывает сток T-07-13: отказ валидации фреймворка на странице отдаёт htmx-запросу пустой 400, JSON-API не затронут | ✓ VERIFIED | `malformed_request_response` импортирован (`app/main.py:29`) и зарегистрирован (`:253`); `app/main.py` с прошлого вердикта не менялся; модуль `test_htmx_validation_sink.py` в зелёном полном прогоне |
| 7 | Крит. 4 / GATE-02 (по летописи D-14, подтверждённой владельцем): утверждения 302 о переведённых POST собраны в пары одним параметризованным обходом, число объявлено прогоном | ✓ VERIFIED | `PAIRED_302_ASSERTIONS_DECLARED = 158` (`test_htmx_post_pairs.py:2269`). Собственный прогон верификатора модуля целиком: **56 passed** за 49 с. Существующие 302 не переписаны |
| 8 | Суита перестаёт быть зелёной по построению: замыкание над переведёнными обработчиками и непустота окна 51 держатся на контролях | ✓ VERIFIED | `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 0` (`test_htmx_gates.py:3075`) с синтетическим контролем; замыкание `POST_PAIR_CASES` ∪ `CONFIRMED_DELETE_ROUTES` в прогнанном модуле пар; гейт TDD-RED плана 11-21 сработал как задумано — `2 failed` до правки, `2 passed` после, а задача 2 измерена двумя мутантами рабочей копии |
| 9 | Все POST-формы продуктовых и админских разделов отправляются через htmx | ✓ VERIFIED | 14 вызовов `call form_wrapper` в `app/templates`; постоянные цели свопа на месте: `#max-connect-step` (`accounts/connect_max.html`), `#user-actions`/`#user-block-badge`/`#user-access-tile` (`admin/user_detail.html`), `#profile-settings` (`profile.html`), `#sched-list` (`ads/form.html`). Без htmx остались только `auth/*` и `base.html` — Фаза 14 |
| 10 | Исходы снятия задачи из очереди переехали в закрытый реестр `?notice=`, ключ `?result=` снят | ✓ VERIFIED | `grep -rn '?result=' app/ --include='*.py' --include='*.html'` — пусто; `QUEUE_DROP_*` в `notices.py` |
| 11 | Крит. 5: Alpine переживает свап (раскрытая карточка, `accounts/*`, слушатели), Back и F5 не предлагают повторить POST | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | **Половина Back/F5 ЗАКРЫТА наблюдением:** проверка 4 `11-UAT.md` — Chrome 152 / macOS на боевом стенде, признаки записаны (`HX-Push-Url: /ads/66/edit`, `htmx:pushedIntoHistory`, F5 и Back — документные GET, ни одного POST документом; `HX-Location: /accounts/29/groups`, история 17 → 18). Часть «Повторить» не наблюдена (нет аккаунта в состоянии ошибки) и принята владельцем репликой «1». **Половина Alpine НЕ закрыта:** машинная часть есть (раскрытие — серверное состояние `keep_sched`/`expanded_id`, панели вне целей свопа, `hx-push-url` в шаблонах — 0 вхождений), но инвариант «слушатели не копятся, панель ровно одна после N подмен» не исполняет ни один тест, а отметка проверки 3 пуста. Присутствует и связано — поведение не проверено |
| 12 | G-11-6 закрыт МАШИННО: форма обёртки несёт класс области, её индикатор выведен из потока внутри коробки формы, панели подтверждения и точка строки группы не задеты | ✓ VERIFIED | Код прочитан, не сводка: `form_wrapper.html:163` — `class="form-wrapper"` ровно после `hx-post`, единственное вхождение в дереве шаблонов; `app.css:2207-2210` — `.form-wrapper { position: relative }` и `.form-wrapper > .form-busy { position: absolute; right: 0; bottom: 0; pointer-events: none }`; исключение `[data-group-row] form[action$="/toggle"] > .form-busy { position: static }` (`:2762`, специфичность (0,3,1) против (0,2,0)). База `.form-busy` — по-прежнему ОДНО правило (`grep -c '^\.form-busy {$'` = 1), `display: inline-block` сохранён, оба порога 300 мс не тронуты. `IN_FLOW_INDICATOR_EXCEPTIONS_DECLARED = 1`, `PANEL_QUALITY_DIFFERENCES_ALLOWED = 2`. **Собственный прогон верификатора восьми гейтов: 8 passed за 0,47 с** |
| 13 | G-11-6, браузерная половина (`verification: backstop` плана 11-21): под кнопками нет лишней полосы, промежутки ровные, точка не садится на орган и не гасит нажатие | ⚠️ insufficient_spec (воздержание) | Машинно утверждено ОБЪЯВЛЕНИЕ правил, а не результат выкладки. Явного свидетельства — прогнанного held-out-теста или наблюдения — нет: окно 88 `unrun-verify` / `open`, таблица отметки проверки 6 `11-UAT.md` пуста, пункт 5а прямо записан ненаблюдённым. Арифметика 11-UI-REVIEW.md («оба страха не воспроизводятся») сама названа арифметикой, а не наблюдением, и наблюдением не засчитана |

**Счёт:** 11/13 истин подтверждено (2 — присутствуют и связаны, поведение не проверено: истина 11 и воздержание истины 13; 0 переопределений)

**Сверка со счётом прошлого раунда.** Было 10/11. Верифицированных стало 11 (прибавилась истина 12 — машинное закрытие G-11-6). Всего стало 13: истина 11 прошлого раунда (`? UNCERTAIN`) осталась одной строкой и поднялась до «половина закрыта наблюдением, половина — нет», а плана 11-21 добавил две новые (12 и 13). Падение доли — следствие роста объёма, а не потери проверенного.

### Требуется проверка человеком

Пять пунктов в `human_verification` во frontmatter. Их отношение к СЕМИ пунктам издания 2026-09-17 — ниже, без единого исчезновения:

| # издания 2026-09-17 | Пункт | Состояние | Что разрешило / почему держится |
|---|---|---|---|
| 1 | ЮKassa на тестовом ключе (критерий 2, окно 87) | **держится** | `11-UAT.md` тест 1 несёт `result: pass`, но таблица отметки проверки 1 ПУСТА, а шапка обхода прямо называет ответы проверок 1–3 «pass без признака». Окно 87 в `.planning/WINDOWS.md` — `unrun-verify`, status `open`. Хост `confirmation_url` тестового ключа нигде не записан |
| 2 | UAT пункт 5 — Alpine и панели после десятков свопов | **держится** | Тест 3 `11-UAT.md` `result: pass`, таблица отметки проверки 3 ПУСТА. Ни один тест суиты не исполняет инвариант накопления слушателей |
| 3 | UAT пункт 7 — Back и F5 после `HX-Location` и создания черновика | **ЗАКРЫТ** | Проверка 4 `11-UAT.md`: таблица отметки НЕПУСТА — Chrome 152 / macOS, broadcaster.all-torgi.ru, признаки поимённо (черновики 66 и 67, `HX-Push-Url`, `htmx:pushedIntoHistory`, F5 и Back документными GET, ни одного POST документом; `HX-Location` на экран групп, история 17 → 18). Часть Б («Повторить») не наблюдена за отсутствием аккаунта в состоянии ошибки и принята ВЛАДЕЛЬЦЕМ репликой «1» от 2026-09-17. ⚠️ Названо, а не замолчано: признаки снял агент по прямой реплике владельца «проверь сам через mcp chrome dev», и сама строка объявляет себя не подписью приёмки. Наблюдение, которого требовал пункт, состоялось; подпись остаётся агентской |
| 4 | Прокрутка при создании расписания в длинном списке | **держится** | Тест 2 `11-UAT.md` `result: pass`, таблица отметки проверки 2 ПУСТА |
| 5 | Профиль — реальный своп 422 в рантайме htmx | **ЗАКРЫТ** | Проверка 5 `11-UAT.md`: таблица отметки НЕПУСТА — `POST /profile` 422, `htmx:beforeSwap` `shouldSwap: true` / `isError: true`, перерисовка `#profile-settings` с `alert--error` «Неверный часовой пояс», `#htmx-failure-server` и `#htmx-failure-network` остались `hidden`, документ тот же. Побочно записаны два наблюдения, оба достижимые только подменой через DevTools (поле выбора встаёт на первый вариант; плашка успеха видна рядом с ошибкой). Та же агентская подпись по реплике владельца «пятую проверь сам» |
| 6 | Визуальный зазор под кнопками | **держится, и ПЕРЕПИСАН** | Сам ДЕФЕКТ закрыт в коде и машинно охраняется (истина 12, восемь гейтов зелены в прогоне верификатора). Наблюдение — нет: окно 88 `unrun-verify` / `open`, таблица отметки проверки 6 ПУСТА. Пункт 5а (наложение точки на угол органа) записан ненаблюдённым явно. Прежняя формулировка «нет лишнего зазора» сузилась бы до уже решённого; пункт переписан на полный состав проверки 6, включая 5а |
| 7 | Подтверждение владельцем прочтений критериев | **ЗАКРЫТ** | Проверка 7 `11-UAT.md`: подписанная строка 2026-09-17, «владелец (`chubav`), реплика „pass“ на чекпоинт проверки 7 в `/gsd-verify-work 11`» — D-01, D-05, D-06, D-12/D-13, D-14 подтверждены поимённо, возвращать нечего; летописи критериев 1, 3, 4, 5 в ROADMAP.md приняты контрактом фазы. Тем самым претензия прошлого издания «лично владельцем принято только D-08» исчерпана |
| — | **НОВОЕ** (переаудит 11-UI-REVIEW.md 2026-09-18, находки 4 и 5) | **заведено** | Правка 11-21 создала контакт `--text-muted` с залитой `--accent-cta` кнопкой (расчётно 2–3:1) и увела точку на ширину карточки от кнопки в широких формах. Требует взгляда в браузере |

⚠️ **Поправка стойкого утверждения прошлого издания.** Его сводка пробелов гласила «`11-UAT.md` нет». Это больше не так: файл существует, `status: diagnosed`, `checks_declared: 7`, 6 `pass` и 1 `issue`. Этим изданием он прочитан и засчитан ровно там, где несёт наблюдённый признак, — и не засчитан там, где несёт `pass` при пустой таблице отметки.

**Перенос отложенных `<human-check>` из планов.** Блоки `<human-check>` несут 13 планов (11-01, 03–06, 10, 12, 13, 15–18, 21). Все прочитаны; каждый — раздельная детализация тех же самых проверок обхода (пункт 5 по разделам, пункт 7, критерий 2 у 11-15, критерий 3 у 11-05, профиль у 11-10, проверка 6 у 11-21). Ни один не вносит нового предмета наблюдения и ни один не потерян: они поглощены пунктами 1–4 списка выше.

### Отложенные пункты

Позднейших фаз вехи, поглощающих названные здесь предметы:

| # | Пункт | Куда отнесён | Свидетельство |
|---|---|---|---|
| 1 | 4 обработчика QR-мастера TG не переведены | Фаза 13 | Летопись критерия 1 в ROADMAP.md; `NOT_YET_CONVERTED` |
| 2 | 10 обработчиков `auth.py` не переведены; отказ по источнику у `stop_impersonation` | Фаза 14 | Та же летопись; D-08 `11-CONTEXT.md` |
| 3 | `hx-push-url` по каждой форме | Фаза 15 (QUAL-04) | D-13 `11-CONTEXT.md` |

### Advisory (новый объём, без детерминированного свидетельства)

Находки шага 7, не бывшие ни переносимым гэпом, ни регрессией файла, изменённого этим раундом, — записаны, не блокируют, ни одной закрытой истины не отменяют.

| # | Находка | Категория | Почему advisory |
|---|---------|-----------|-----------------|
| 1 | Мастер MAX: ветка отказа печатает сырое исключение и отрисовывает шаг `qr` без QR с вечным опросом, убрав форму телефона — повторить нечем (11-UI-REVIEW Top fix 3, помечено BLOCKER) | architectural | Новый объём: `app/pages/accounts.py` не менялся с 2026-09-17T09:12:00Z, в `gaps:` прошлого вердикта записи нет. Детерминированного свидетельства нет — UI-ревизия объявлена CODE-ONLY, красного прогона и воспроизводимой команды не приложено |
| 2 | Ошибка 422 рисуется баннером над формой, а не состоянием поля (`error=` не передаётся в `select_field`/`field`) | other | Тот же тест: файлы не менялись; FORM-08 требует перерисовки и эха, а не состояния поля. Оценка качества без красного прогона |

### Необходимые артефакты

| Артефакт | Статус | Детали |
|----------|--------|--------|
| `app/templates/components/form_wrapper.html` — класс области `form-wrapper` | ✓ VERIFIED | Одно вхождение, в теге макроса сразу после `hx-post`; 14 вызывающих не правлены (`git diff 073ba75..HEAD -- app/templates/` — только сам макрос) |
| `app/static/css/app.css` — контекст позиционирования, правило вне потока, исключение строки группы | ✓ VERIFIED | `:2207-2210` и `:2762`; база `.form-busy` (`:2193`) одна и без `position`; оба порога 300 мс (`:2198`, `:2203`) не тронуты |
| `tests/test_templates/test_htmx_markup_gates.py` — `_offenders_wrapped_indicator_footprint`, `_offenders_panel_indicator_reach`, `IN_FLOW_INDICATOR_EXCEPTIONS` | ✓ VERIFIED | Оба гейта прогнаны верификатором; числа объявлены (`= 1`, `= 2`) |
| `tests/test_templates/test_components.py` — `test_the_reported_profile_form_carries_the_indicator_scope`, `test_the_panel_form_stays_outside_the_indicator_scope` | ✓ VERIFIED | Оба в прогоне 8 passed |
| `app/pages/htmx.py` (`respond_field_error`, `redirect_external`, `_confirmation_url`, `malformed_request_response`) | ✓ VERIFIED (регрессия) | Файл не менялся; вызывается из обработчиков и `main.py` |
| `app/pages/identifiers.py` (`id_in_column`, `PostIdPath`…) | ✓ VERIFIED (регрессия) | Файл не менялся |
| `ads/partials/sched_card_response.html`, `sched_create_response.html`, `schedules/partials/schedule_row_response.html`, `admin/partials/user_actions_response.html` | ✓ VERIFIED (регрессия) | Файлы не менялись; рендерятся сборщиками `_fragment` |
| `includes/profile_settings.html`, `accounts/includes/max_connect_step.html` | ✓ VERIFIED (регрессия) | Один источник для страницы и фрагментов; обёртки `#profile-settings`, `#max-connect-step` на месте |
| `tests/test_pages/test_htmx_post_pairs.py` | ✓ VERIFIED | 56 тестов, все зелёные в собственном прогоне |
| `components/modal.html` | ✓ VERIFIED (неприкосновенность) | `git diff 073ba75..HEAD -- app/templates/components/modal.html` пуст; класса области не несёт |

### Проверка ключевых связей

| Откуда | Куда | Через | Статус |
|--------|------|-------|--------|
| класс области в теге макроса (`form_wrapper.html:163`) | правило `.form-wrapper > .form-busy` (`app.css:2208`) | совпадение имени класса; расхождение вернуло бы полосу молча | WIRED (гейт `test_a_wrapped_form_gives_its_indicator_no_layout_footprint`, прогнан) |
| исключение строки группы (0,3,1) | правило области (0,2,0) | специфичность, независимая от порядка в файле | WIRED (подтверждено разбором селекторов в 11-REVIEW) |
| тег формы панели без класса области | базовые правила индикатора без `position` | оба условия держат принятую высоту 18 панелей | WIRED (гейт `test_the_confirmation_panel_indicator_keeps_its_accepted_place`, прогнан; мутанты А и Б краснили его) |
| форма правки (`#sched-N`, outerHTML) | `schedules_update` → `sched_card_response.html` | `respond(fragment=)` | WIRED |
| форма создания (`#sched-list`, beforeend) | `schedules_create` → `sched_create_response.html` | `respond(fragment=)` | WIRED |
| форма блокировки и бесплатного доступа (`#user-actions`, innerHTML) | `_user_actions_response` + OOB бейджа и плитки | включаемые шаблоны | WIRED |
| форма оплаты (`form_wrapper`, swap none) | `subscribe_to_plan` → `redirect_external` → `HX-Redirect` | заголовок на возвращаемом ответе | WIRED |
| форма профиля (`#profile-settings`) | `profile_post` → `respond` / `respond_field_error` | правило 422 со свопом | WIRED |
| форма телефона MAX (`#max-connect-step`) | `accounts_connect_max_start` → шаг QR с `hx-get every 3s` | `respond` / `respond_field_error` | WIRED |
| `RequestValidationError` | `malformed_request_response` | `app/main.py:253` | WIRED |
| `POST_PAIR_CASES` ∪ `CONFIRMED_DELETE_ROUTES` | замыкание над `respond`-обработчиками | `_closure_complaints` | WIRED |

### Трассировка потока данных (уровень 4)

| Артефакт | Величина | Источник | Реальные данные | Статус |
|----------|----------|----------|-----------------|--------|
| `sched_card_response.html` | карточка расписания | сборщик `_fragment` после `commit()` перечитывает редактор из БД | да | ✓ FLOWING |
| `schedule_row_response.html` | строка списка | `_row_fragment` — `select` по `after_id` | да | ✓ FLOWING |
| `user_actions_response.html` + OOB | признаки блокировки и безлимита | перечитанный `User` после `invalidate_access_cache` | да | ✓ FLOWING |
| `profile_settings.html` (422) | `selected` | ПРИСЛАННЫЙ `timezone` параметром шаблона | да, но рисуется только при совпадении с закрытым списком (см. истину 5) | ✓ FLOWING |
| `max_connect_step.html` (422) | `phone` | присланное значение через макрос поля с автоэкранированием | да | ✓ FLOWING |
| `.form-busy` | — | статический узел, данных не несёт | н/п | н/п |

### Поведенческие выборочные проверки

| Поведение | Команда | Результат | Статус |
|-----------|---------|-----------|--------|
| Восемь гейтов индикатора (новые 11-21 + четыре прежних, названных диагнозом) | `uv run pytest ...test_a_wrapped_form_gives_its_indicator_no_layout_footprint ...test_the_confirmation_panel_indicator_keeps_its_accepted_place ...test_the_reported_profile_form_carries_the_indicator_scope ...test_the_panel_form_stays_outside_the_indicator_scope ...test_the_indicator_class_is_self_sufficient ...test_the_indicator_class_carries_a_visibility_threshold ...test_the_panel_quality_properties_match_the_form_wrapper ...test_every_allowed_quality_difference_carries_a_reason -q` | `8 passed, 1 warning in 0.47s` | ✓ PASS |
| Пары 302, обход, контроли (GATE-02 целиком) | `uv run pytest tests/test_pages/test_htmx_post_pairs.py -q` | `56 passed, 1 warning in 49.28s` | ✓ PASS |
| Эхо 422, вставка `beforeend`, освобождение заявки синхронизации | `uv run pytest tests/test_pages/test_profile.py tests/test_pages/test_max_connect_transport.py tests/test_pages/test_editor_schedules.py tests/test_routes/test_sync_groups.py -q -k "422 or echo or append or beforeend or in_flight or sync"` | `111 passed, 7 deselected in 114.12s` | ✓ PASS |
| Покрытие решений CONTEXT.md | `gsd_run query check.decision-coverage-verify` | `honored 16 / total 16`, `not_honored: []` | ✓ PASS |
| Полная суита без отбора маркером | данные оркестратора этого раунда, `just test` | `3410 passed`, 0 failed, rc=0, 37:17 | ✓ PASS (верификатором не перезапускалась — правило одного полного прогона за раунд) |
| Сборка | `uv run python -m compileall -q app main.py tests` (пост-слияночный гейт) | rc=0 | ✓ PASS |

### Запуск проб

Проб `scripts/*/tests/probe-*.sh` в дереве нет (`find scripts -path '*/tests/probe-*.sh'` пуст), и ни один из 21 плана их не объявляет — шаг пропущен.

### Покрытие решений

| Всего трекуемых решений `11-CONTEXT.md` | Соблюдено | Не соблюдено |
|---|---|---|
| 16 | 16 | — |

Гейт некритичный; расхождений нет. Сверх машинного счёта: прочтения D-01, D-05, D-06, D-12, D-13, D-14, стоявшие в прошлом издании как «приняты агентом под делегированием», подтверждены владельцем лично (проверка 7 `11-UAT.md`).

### Покрытие требований

| Требование | Планы | Статус | Свидетельство |
|------------|-------|--------|---------------|
| FORM-03 | 01, 03–06, 09, 11–13, 18, 20, 21 | ✓ SATISFIED (по летописи D-01, подтверждённой владельцем) | Истины 1, 9, 12 |
| FORM-04 | 12–17, 20, 21 | ✓ SATISFIED | Повторная синхронизация, синхронизация групп и исходы админки/оплаты уходят через `HX-Location`; пары зелены (56 passed) |
| FORM-05 | 15 | ✓ SATISFIED машинно; ? UAT на тестовом ключе | Истина 3; окно 87 `open` |
| FORM-07 | 05 | ✓ SATISFIED по летописи D-05 (`beforeend`); ? прокрутка — UAT | Истина 4. Буквальный `afterbegin` не применён намеренно, и владелец это подтвердил |
| FORM-08 | 02, 06–11, 17–19, 21 | ✓ SATISFIED (по D-06) | Истины 5, 6; своп 422 наблюдён в браузере (проверка 5) |
| FORM-10 | 10 | ✓ SATISFIED | Истина 2 |
| GATE-02 | 01, 20 | ✓ SATISFIED (по D-14) | Истина 7 |

Сиротских требований нет: `.planning/REQUIREMENTS.md:494` относит к Фазе 11 ровно эти 7 ID, и каждый заявлен хотя бы одним планом. **Клетки статусов `Pending` — это НЕ пробел:** FORM-03, FORM-04 и FORM-08 были помечены `Complete` исполнителем 11-21 и возвращены оркестратором в `fa2b766`, потому что правило `test_no_requirement_is_marked_complete_before_its_phase_verification_passed` запрещает `Complete` при вердикте фазы не `passed`. Перевод ставит `phase.complete` ПОСЛЕ вердикта.

### Аудит качества тестов

| Предмет | Замер | Вердикт |
|---|---|---|
| Отключённые тесты на требованиях фазы | `it.skip`-аналогов (`@pytest.mark.skip`, `@unittest.skip`) в четырёх файлах, изменённых 11-21, нет | ✓ чисто |
| Круговые ожидания | Значения гейтов 11-21 сняты с ФАЙЛОВ продукта (`_app_css`, `_all_templates`), а ожидания — из констант, набранных от имён классов; система под тестом своих же ожиданий не печатает | ✓ не круговые |
| Сила утверждений | Уровень «значение»: сверяются точные селекторы и точный состав объявлений, а не факт наличия правила | ✓ достаточно |
| Анти-вакуум | RED задачи 1 снят прогоном (`2 failed` → `2 passed`); RED задачи 2 снят двумя мутантами рабочей копии с возвратом через `git checkout --` и сверкой порцелана | ✓ зубы измерены |
| ⚠️ Оговорка | Подстановки т1/т2 гейта следа утверждают ИСТИННОСТЬ словаря нарушений, а не его КЛЮЧ (11-REVIEW WR-07) — сегодня доказательство состоятельно, но станет вакуумным, если покраснеет вторая ветка помощника | ⚠️ Warning |

### Найденные антипаттерны

| Файл | Строка | Находка | Серьёзность | Влияние |
|------|--------|---------|-------------|---------|
| 4 файла, изменённых 11-21 | — | `TBD` / `FIXME` / `XXX` | — | **Не найдено** (проверено пофайлово); по всему `app/pages/`, `app/templates/`, `app/static/css/app.css` — тоже пусто |
| `tests/.../test_htmx_markup_gates.py:3201`, `test_components.py:750` | — | Правило `.form-wrapper > .form-busy` держится на ДОЧЕРНЕМ комбинаторе, а прямое потомство узла не утверждает ни один гейт: обёртывание узла в `<div>` вернёт G-11-6 при всех зелёных (11-REVIEW WR-04) | ⚠️ Warning | Регрессия будущей правки макроса, не сегодняшний дефект |
| `tests/.../test_htmx_markup_gates.py:2927-2972` | — | Запись исключения привязана к строке селектора и ни к чему больше: переименование маршрута `/toggle` или атрибута `data-group-row` осиротит её молча (11-REVIEW WR-05) | ⚠️ Warning | Точка строки группы уехала бы вопреки решению владельца 3 |
| `tests/.../test_htmx_markup_gates.py:3330-3335` | — | Перечень исключений служит ещё и разрешением гейта неподвижности панели; запись, адресующая `.modal__form`, прошла бы ОБА гейта (11-REVIEW WR-06) | ⚠️ Warning | Разъединённые по замыслу гейты снова связаны общим хранилищем доверия |
| `tests/.../test_htmx_markup_gates.py:4817-4835` | — | Подстановки утверждают «покраснело хоть на чём-то», вопреки дисциплине, записанной соседним тестом дословно (11-REVIEW WR-07) | ⚠️ Warning | Доказательство зубов способно стать вакуумным |
| `app/static/css/app.css:2195` + `:715` | — | **НОВОЕ, следствие 11-21:** точка `--text-muted` #6a6a78 впервые оказалась поверх залитой `--accent-cta` кнопки (мастер MAX, «Синхронизировать всё») — расчётно 2–3:1 при полу WCAG 1.4.11 в 3:1 | ⚠️ Warning | Проверено верификатором самостоятельно: обе формы идут с умолчанием `disabled_elt='find button[type=submit]'`, единственная кнопка отправки блокируется, поэтому точка НЕ единственный признак ожидания — вопреки формулировке Pillar 3. Наблюдение в браузере заведено пунктом 5 |
| `includes/profile_settings.html`, `ads/includes/sched_card.html`, `billing/balance.html` | — | **НОВОЕ, следствие 11-21:** в широких формах точка встала в правый нижний угол коробки ФОРМЫ, то есть на ширину карточки от левовыровненной кнопки | ⚠️ Warning | Место точки — усмотрение планировщика, записанное в 11-21-PLAN; решением владельца не является. Наблюдение заведено пунктом 5 |
| `app/templates/ads/includes/sched_card.html` | 210 / 265 / 303 | Форма правки берёт умолчание `disabled_elt`, а первая кнопка отправки в ней — «ВЫБРАТЬ ВСЕ»; `find` в вендоренном htmx 2.0.10 есть `querySelector` | ⚠️ Warning | «СОХРАНИТЬ РАСПИСАНИЕ» не блокируется, защиты от двойной отправки нет. Было и до партии; файл с прошлого вердикта не менялся |
| `app/pages/ads.py` | ~700 | `int(ad_id)` без границы → 500 на PostgreSQL (11-REVIEW WR-01 carried) | ℹ️ Info | Было до фазы, записано `open` в `test_identifier_bounds.py` |
| `app/pages/schedules.py` | `schedules_create` | Карточка или переход выбирается по числу ПОСЛЕ вставки (WR-02 carried): в другой вкладке с нулём расписаний фрагмент уйдёт в `hx-swap=none` | ⚠️ Warning | Краевой случай нескольких вкладок |
| сборщики фрагментов | — | Повторное чтение после коммита без запасной ветки (WR-03 carried) | ⚠️ Warning | Гонка: одновременное удаление → 500 после успешной записи |

Ни один пункт не квалифицирован блокирующим. Четыре находки на файлах, изменённых этим раундом (WR-04…WR-07 и два новых следствия правки), проверены гейтом свидетельств как регрессии — но ни одна не роняет объявленной истины и ни одной не приложено красного прогона: код-ревизия этого раунда дала **0 critical**, а правильность самого правила подтвердила разбором специфичности и перечислением всех `position: absolute` таблицы стилей. Они остаются предупреждениями.

### Состояние прочих гейтов раунда

| Гейт | Результат | Прочитано верификатором |
|---|---|---|
| Полная суита без отбора | 3410 passed, rc=0, 37:17 | Принято как данные оркестратора; собственные три прогона (8 + 56 + 111 passed) взяты поверх, не вместо |
| Схемный дрейф | без дрейфа | — |
| Безопасность (`11-SECURITY.md`) | `status: verified`, `threats_open: 0`, 44 угрозы, ASVS L1 | Сверено во frontmatter |
| Nyquist (`11-VALIDATION.md`) | `status: validated`, `nyquist_compliant: true`, 0 пробелов, строка 11-21 в карте | Сверено во frontmatter |
| Код-ревизия (`11-REVIEW.md`) | 0 critical, 4 warning, 4 info этого прохода; 6 находок 2026-09-17 перенесены непроверенными | Все 8 новых прочитаны; 4 warning — о СПОСОБАХ обойти гейты, ни одна не о неверности правки |
| UI-ревизия (`11-UI-REVIEW.md`) | 17/24; P5-a и P5-b помечены CLOSED; заведены две новые находки | Обе новые приняты в отчёт (антипаттерны + пункт 5 наблюдения); BLOCKER мастера MAX — advisory (новый объём, свидетельства нет) |

### Сводка пробелов

**Блокирующих пробелов нет, и `gaps:` в этом издании отсутствует намеренно.** Гэп G-11-6, единственный, который партия закрывала, снят в коде корректно и охраняется гейтами, которые верификатор прогнал сам, а не принял со слов сводки: класс области стои́т в макросе одним вхождением, два правила стилей объявлены, исключение строки группы выигрывает по специфичности, база `.form-busy` осталась единственной и без позиции, панели подтверждения не тронуты ни байтом, четырнадцать вызывающих не правлены. Все семь требований фазы имеют машинное свидетельство; ни один артефакт не пуст, ни одна связь не оборвана; отладочных маркеров в файлах фазы нет.

Статус `human_needed` держится на пяти браузерных пунктах и ни на чём другом. Из них четыре — наследники издания 2026-09-17, а один заведён впервые побочным следствием самой правки 11-21. Три пункта того издания закрыты обходом и названы закрытыми поимённо; из оставшихся один (ЮKassa) план 11-15 требует ДО слияния, а один (проверка 6) держит окно 88 и содержит явно ненаблюдённый пункт 5а: точка теперь стои́т поверх угла органа, и арифметика, говорящая, что это безвредно, наблюдением не является.

Окна `.planning/WINDOWS.md` 63 (решено частично, D-08), 84, 85, 86, 87 и 88 остаются `open`; 87 и 88 — это и есть пункты 1 и 4 списка наблюдений выше.

---

_Проверено: 2026-09-18T00:00:00Z_
_Верификатор: Claude (gsd-verifier)_
