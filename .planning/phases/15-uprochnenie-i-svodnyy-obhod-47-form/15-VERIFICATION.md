---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
verified: 2026-09-24T19:40:00Z
status: gaps_found
score: "6/8 roadmap truths verified (1 failed, 1 human); 151/157 plan truths verified (6 routed to human)"
covered_files:
  - ".planning/REQUIREMENTS.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-01-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-01-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-02-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-02-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-03-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-03-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-04-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-04-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-05-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-05-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-06-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-06-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-07-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-07-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-08-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-08-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-09-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-09-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-10-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-10-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-11-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-11-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-12-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-12-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-13-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-13-SUMMARY.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-14-PLAN.md"
  - ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-14-SUMMARY.md"
  - "app/pages/accounts.py"
  - "app/pages/ads.py"
  - "app/pages/schedules.py"
  - "app/services/schedule_rules.py"
  - "app/static/css/app.css"
  - "app/templates/accounts/list.html"
  - "app/templates/accounts/partial_cards.html"
  - "app/templates/ads/list.html"
  - "app/templates/ads/partial_cards.html"
  - "app/templates/includes/htmx_error_banner.html"
  - "app/templates/schedules/list.html"
  - "app/templates/schedules/partial_cards.html"
  - "scripts/prohibitions_census.py"
  - "tests/test_pages/test_account_groups.py"
  - "tests/test_pages/test_ads_editor.py"
  - "tests/test_pages/test_billing_section.py"
  - "tests/test_pages/test_editor_schedules.py"
  - "tests/test_pages/test_htmx_gates.py"
  - "tests/test_pages/test_htmx_post_pairs.py"
  - "tests/test_pages/test_responsive_markup.py"
  - "tests/test_pages/test_shell.py"
  - "tests/test_planning/test_plan_prohibitions_census.py"
  - "tests/test_services/test_schedule_rules_gate.py"
  - "tests/test_templates/test_banner_dismiss.py"
  - "tests/test_templates/test_degradation_pairs.py"
  - "tests/test_templates/test_form_inventory.py"
  - "tests/test_templates/test_htmx_inventory.py"
  - "tests/test_templates/test_htmx_markup_gates.py"
  - "tests/test_templates/test_markup_literal_inventory.py"
# Отпечаток снят официальным помощником `computeCoveredDigest(root, files)` из
# `.claude/gsd-core/bin/lib/verification.cjs` над ПОЛНЫМ списком из 58 путей выше
# (не вербом `verification.fingerprint`, который теряет первый путь).
covered_digest: "v1:sha256:bbce2b1d7a5b6c92b0267696be56b9c25874621449d6e00ebfcf618a7e3b5771"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Критерий 6 ROADMAP, половина (б): по каждому запрету перечня прибора стоит ЛИБО предъявленное машинное принуждение, ЛИБО явное человеческое разрешение с машинно читаемой областью (`permit_scope`)"
    status: failed
    reason: "В области решений (Фаза 10, 321 запрет; сужение до Фазы 10 — D-02) 85 запретов не несут ни принуждения, ни разрешения: 27 `unresolved`/`declared-rule-absent` (объявили `verification: test`, правила в дереве нет; разрешение класса их по D-05 не закрывает) и 58 `unresolved`/`enforcement-required` (класс `product-invariant`, ответ владельца `require-enforcement`, адресат работы не назначен). Ещё 9 запретов `product-invariant` принуждены лишь частично: их непокрытая часть не принуждена и не разрешена. Планы 15-13 закрепили критерий в ОСЛАБЛЕННОЙ форме «решён ИЛИ названа причина»; это форма плана, а не текст критерия, и сужать критерий ROADMAP план не вправе. Прибор сам докладывает остаток: `scripts/prohibitions_census.py --breakdown` → `unresolved: 85` в области решений."
    artifacts:
      - path: ".planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml"
        issue: "85 строк Фазы 10 с `disposition: unresolved` (причины: declared-rule-absent 27, enforcement-required 58); 9 строк `product-invariant` с `partially-enforced`"
      - path: "tests/test_planning/test_plan_prohibitions_census.py"
        issue: "закрывающее правило `test_the_closing_rule_of_criterion_6_every_phase_10_row_is_decided_or_names_its_reason` утверждает безусловную (ослабленную) форму; сильной формы («ни одного unresolved») нет"
    missing:
      - "Решение владельца по каждому из трёх путей закрытия остатка: (1) написать правила принуждения для 58 запретов `product-invariant` и 27 запретов D-05 — адресат (фаза/веха) не назначен; (2) явное разрешение с `permit_scope` там, где владелец готов разрешить; (3) принять отступление записью `overrides:` в этом файле (форма — ниже в отчёте)"
      - "Назначить адресата работы по `product-invariant` (68 не принуждены целиком: 58 без правила, 1 находка D-05 `10-50#3`, 9 частично)"
      - "Решить судьбу 27 находок D-05: писать правила или принять объявление `verification: test` без правила (снимать дескриптор в исполненных планах запрещено их же запретами)"
      - "⚠️ Для планировщика закрытия (WR-04, 15-REVIEW.md): любой новый файл `.planning/phases/*/[0-9]*-PLAN.md` с блоком `must_haves.prohibitions` или statement-first `truths` ПОКРАСИТ `tests/test_planning/test_plan_prohibitions_census.py` (литералы `PROHIBITIONS_DECLARED_AT_PHASE_15 = 697`, `TRUTHS_AT_PHASE_15`, `NAIVE_LINE_NET_AT_PHASE_15`, биекция с реестром и `rows_declared`). Каждый план закрытия обязан пересеять реестр (`--seed-registry`) и завести НОВЫЙ литерал под своим именем, а не править литерал Фазы 15; либо сначала сузить вселенную гейта до фиксированного набора планов. Исполнители отбирают `tests/test_planning/` вон — поломку увидит только полный прогон оркестратора"
advisory:
  - finding: "WR-01 (15-REVIEW.md): правка из редактора молча гасит работающее расписание на второй линии (`schedules.py`, ветка `next_run is None` → `is_active = False` без notice); политика расходится с тумблером и с JSON-API; два правила фазы (`test_malformed_stored_form_on_the_second_line_lands_one_outcome`, `test_malformed_stored_days_str_form_goes_the_same_way`) закрепляют это как норму"
    category: other
    reason: "Ветка достижима только при отказе первой линии (санитайзеры). Ни один must_have 15-08 не нарушен (пятисотки нет, путь восстановления возвращён), но правило фазы закрепляет спорную политику — класс «тесты фазы закрепляют дефект». Решение: выбрать одну политику на три входа и переписать два правила под notice"
    evidence_status: "code read; not reproduced as a user-visible failure"
  - finding: "WR-02 (15-REVIEW.md): `test_malformed_stored_values_are_asked_through_the_helper_in_the_editor_save` требует ровно один прямой вызов `compute_next_run_at` и именно в `schedules_create` — правило запрещает дать create ту же вторую линию, что update"
    category: other
    reason: "Закрепляет предсуществующую асимметрию; по духу задевает запрет 15-08 #3 («правило о непочиненном — только под маркером characterisation»). Решение: ослабить до «ни один обработчик страниц не зовёт вычислитель напрямую» вместе с починкой create"
    evidence_status: "code read"
  - finding: "WR-03 (15-REVIEW.md): четыре новые пары GATE-10 (`test_accounts_delete_confirm_degrades_without_htmx`, `test_ads_delete_confirm_degrades_without_htmx`, `test_admin_user_delete_confirm_degrades_without_htmx`, `test_editor_ad_delete_confirm_degrades_without_htmx`) не утверждают ни удаления сущности, ни точного `Location`"
    category: other
    reason: "Подтверждено чтением `test_responsive_markup.py` (тест `test_ads_delete_confirm_degrades_without_htmx`): после POST проверяются только 302/303, отсутствие HX-Location, 200 и `<!DOCTYPE`. Критерий 4 (счёт пар, без переименований) исполнен; сила пар слабее заявленной. Пара оплаты сделана правильно (точный `location`)"
    evidence_status: "code read"
  - finding: "WR-04 (15-REVIEW.md): литералы переписи с именем Фазы 15 покраснят `just test` на первом же новом плане в `.planning/phases/`, включая планы закрытия гэпов"
    category: architectural
    reason: "Прямо касается закрытия гэпа критерия 6 — вынесено и в `gaps[0].missing`"
    evidence_status: "code read (`scripts/prohibitions_census.py` вселенная `.planning/phases/*/[0-9]*-PLAN.md`)"
  - finding: "IN-01 (15-REVIEW.md): `verification: null` читается как отсутствие ключа (`scripts/prohibitions_census.py`), вопреки собственному докстрингу"
    category: other
    reason: "Info; сегодня такого значения в дереве нет"
    evidence_status: "none provided"
  - finding: "IN-02 (15-REVIEW.md): испорченный реестр падает трассой, а не `CensusError`/строкой `ОТКАЗ:`"
    category: other
    reason: "Info; касается только ручной порчи реестра"
    evidence_status: "none provided"
  - finding: "IN-03 (15-REVIEW.md): два разных `_split_top_level` в `test_htmx_gates.py` и `test_htmx_markup_gates.py`"
    category: other
    reason: "Info; риск молчаливого расхождения двух разборщиков"
    evidence_status: "none provided"
  - finding: "IN-04 (15-REVIEW.md): комментарии указывают номерами строк (`app.css` «строки 1255-1258»; устаревшее основание в `test_editor_schedules.py`)"
    category: other
    reason: "Info; сдвинется первой правкой выше"
    evidence_status: "none provided"
  - finding: "IN-05 (15-REVIEW.md): сеть литерала размера страницы ловит только `limit=<цифра>`"
    category: other
    reason: "Info; `limit={{ 30 }}`, `hx-vals` с числом, `<input name=limit value=30>` сеть не видит"
    evidence_status: "none provided"
  - finding: "IN-06 (15-REVIEW.md): PyYAML остаётся необъявленной зависимостью (транзитивно через `uvicorn[standard]`), у неё новый потребитель"
    category: other
    reason: "Info; риск назван в докстринге модуля"
    evidence_status: "none provided"
  - finding: "UI-REVIEW 17/24 (15-UI-REVIEW.md), приоритет 1: снятие плашки клавиатурой роняет фокус на `<body>`; орган по-прежнему объявляется флажком — «ролевая» половина D-18.3 не починена и НЕ записана принятым следствием"
    category: other
    reason: "D-18 вводил все три находки Фазы 10 в область фазы; план 15-07 закрыл имя и место, но не роль и не внешность. Починка требует НОВОГО решения владельца (ветвь A запрещает новый обработчик). Либо починить, либо записать принятым следствием рядом со смещением второй плашки"
    evidence_status: "code read; rendering not observed"
  - finding: "UI-REVIEW приоритет 2: вторая плашка остаётся смещённой после снятия первой органом (известное открытое следствие, сторож `test_boundary_the_open_banner_top_consequence_is_guarded_not_fixed`)"
    category: other
    reason: "Записано и передано вехе; этой фазой не чинилось намеренно"
    evidence_status: "recorded in app.css and gate"
  - finding: "UI-REVIEW приоритет 3: замена `limit=30` на `limit={{ page_size }}` завела молчаливый путь отказа — пропавший ключ контекста даёт `limit=`, 422, а обработчик плашки на 422 выходит рано; сентинел висит «Загрузка...» навсегда"
    category: other
    reason: "Латентно: все шесть рендеров сегодня отдают `page_size` (правило `test_the_page_size_in_the_context_is_the_module_constant`). Варианты: убрать `&limit=` из шести сентинелов или рендерить под StrictUndefined"
    evidence_status: "reproduced by the UI auditor (422 on `limit=`)"
  - finding: "UI-REVIEW пункты 4-8: молчаливая смена часового пояса при сохранении испорченной строки; контраст обвода фокуса ~2.6:1 < 3:1 (оценка); устаревшая арифметика шага стопки (346 → 322 px); порядок слов в доступных именах; `Загрузка...` без `role=status`"
    category: other
    reason: "WARNING/minor; ни один не блокирует поток"
    evidence_status: "code read; contrast is an sRGB estimate"
human_verification:
  - test: "Сводный обход `15-UAT.md`: владелец заполняет девять таблиц «Отметка о закрытии» и поля `result` (D-17). Пункты 1-8 — сверка названных записей Фаз 7-11 (D-15); пункт 3, шаги 3.2-3.4 — приземление фокуса на location-пути глазами; пункт 9 — 12 мест условной сборки `hx-*` и 6 ветвей `form_wrapper` в объявленном приоритете"
    expected: "Девять отметок заполнены наблюдёнными признаками (дата, браузер/ОС, наблюдатель); шапка переведена в терминальное состояние только после этого"
    why_human: "Суита не исполняет JS; правило `test_the_walkthrough_cannot_self_certify.py` запрещает самозаверение; отметку ставит только тот, кто наблюдал"
  - test: "Пять наблюдений органа снятия плашки (`15-UAT.md` У-8), окно 1280 px, двойная авария"
    expected: "Обвод фокуса виден и контрастен; пробел снимает плашку; текст не сталкивается с крестиком; два имени различимы на слух; вторая плашка смещена не хуже известного"
    why_human: "Движка раскладки и дерева доступности в суите нет; `app.css` запрещает объявлять отрисовку пройденной по зелени правил. UI-REVIEW оценил контраст обвода ~2.6:1 — проверить на реальном экране"
  - test: "Backstop-утверждения без явного теста (insufficient_spec): независимость от порядка/чистота гейта пар (15-03), запрета FETCH-03 (15-04), реестра `hx-push-url` (15-11), предъявления правил по `ast` (15-13); «чтение из одного снимка дерева» (15-06)"
    expected: "Человек принимает структурную улику (функции берут отображение параметром, контроли на подменённых словарях) или заказывает правило порядка по образцу `test_modal_linkage_counts_are_a_pure_function_of_the_passed_mapping`"
    why_human: "Утверждения помечены `verification: backstop`; присутствие и связность их не доказывают, а плагина случайного порядка в окружении нет — прогон в ином порядке не наблюдался"
  - test: "Обзор 47 запретов планов Фазы 15 (все judgment-tier, `flagged-unverified`); отдельно флагированы 15-14 #1 (буква «MUST NOT писать `result`» нарушена: `result: [pending]` ×9 по указанию оркестратора, вердикта нет) и 15-08 #3 (дух: WR-01/WR-02 — правила фазы закрепляют спорное поведение)"
    expected: "Владелец принимает или отклоняет две флагированные позиции"
    why_human: "Неавторитетный вердикт LLM-судьи; prohibition judgment-tier требует человеческого разрешения"
  - test: "Открытые вопросы владельцу, переданные планом 15-14: (1) запись «27 → 29 файлов с любой формой» (15-02); (2) самопротиворечие `14-UAT.md` — тело `result: pass` ×9 против решения #4 «обход глазами не делался» (15-06); (3) оставить или снять четыре `OOB_TARGET_EXCEPTIONS` (15-09, цена снятия — 13 правил, 9 держат D-04-A); (4) адресаты: принуждение `product-invariant`, 376 запретов вне Фазы 10, 27 объявленных-но-отсутствующих правил (15-13)"
    expected: "Решение владельца по каждому или записанная новая отсрочка с адресатом"
    why_human: "Решения закреплены за владельцем; исполнители их намеренно не принимали"
---

# Phase 15: Упрочнение и сводный обход 47 форм — Verification Report

**Phase Goal:** цель вехи закрыта инвентарями, а не ощущением: 47 из 47, `fetch(` == 0, девять пунктов ручного UAT закрыты поимённо
**Verified:** 2026-09-24T19:40:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Итог в трёх строках

- Машинная половина цели достигнута: 49 мест письма в 27 файлах сведены гейтом равенства (летопись 47 → 49 записана в двух местах одним текстом), `fetch(` в шаблонах 0 и держится ЗАПРЕТОМ, решение `hx-push-url` записано по каждому месту, пары деградации 5 из 5, прибор переписи запретов один и воспроизводим.
- **Критерий 6 (б) не достигнут:** 85 из 321 запрета Фазы 10 не несут ни принуждения, ни разрешения. План 15-13 закрепил ослабленную форму критерия («решён или названа причина»). Это единственный блокер, и его остаток создан решениями владельца (`require-enforcement`) и находкой D-05, а не ошибкой исполнения. Закрыть можно правилами, разрешениями или записью отступления.
- Девять пунктов ручного UAT — акт человека: `15-UAT.md` размечен верно, все отметки пусты по замыслу (D-17). Они вынесены в human verification и провалом исполнения не считаются.

## Goal Achievement

### Observable Truths (контракт ROADMAP)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Любое действие письма без перезагрузки: все места письма идут через `hx-post`, инвентарь сведён числом, ни одна форма не осталась вне контракта (машинно, сводный обход) | ✓ VERIFIED | `tests/test_templates/test_form_inventory.py`: `WRITE_FORM_PLACES = 49`, `WRITE_FORM_FILES = 27`, разбивка 29/18/2, изъятия поимённо (GET-поиск `ads/list.html#0`, `components/filters.html#0`), правило «ни один вызывающий `filters` не переопределяет `method`»; 24 passed. Независимый греп: 29 вызовов `{% call form_wrapper %}` в 22 файлах, 24 сырых `<form` (18 триггеров + 2 с `hx-post` + 2 GET + провайдер макроса + упоминание в комментарии). 18 триггеров связаны с формой модалки четырьмя счётами (`MODAL_TRIGGER_FORMS = 18`, 12 passed в группе связки). Летопись 47 → 49 стоит в ROADMAP §Phase 15 и у FORM-01 — сравнил строки, идентичны без фразы перекрёстной ссылки. Текст FORM-01 не тронут: в `REQUIREMENTS.md` за фазу 0 удалённых строк. |
| 2 | `fetch(` в `app/templates/` == 0, закрыто способом греп-гейта | ✓ VERIFIED | `grep -rn "fetch(" app/templates/` → 0. `test_fetch_prohibition_forbids_manual_request_assembly_in_templates` утверждает `assert not found` (отсутствие, а не равенство числу) и непустоту вселенной; контроли: синтетический `fetch(`, точность сети по четырём похожим формам. 16 passed. ℹ️ Имени `test_no_manual_fetch_remains`, названного критерием и GATE-08, в дереве нет; расхождение записано летописью в `REQUIREMENTS.md` (GATE-08) и в самом модуле, наличие функции-запрета утверждается по `ast`. |
| 3 | По КАЖДОЙ форме записано решение `hx-push-url` по конвенции трёх случаев; гейт запрещает атрибут на маршрутах «изменяет данные»; сводка в артефактах | ✓ VERIFIED | `PUSH_URL_DECISIONS` (37 обработчиков) в `tests/test_pages/test_htmx_gates.py`; `test_push_url_every_write_place_resolves_to_a_decided_handler` связывает все 49 мест; `test_push_url_zero_in_markup_is_a_decision_not_a_gap`; `test_push_url_forbidden_on_places_of_changes_data_handlers` с контролями; сторож `DEF-09-04` (G-2 на GET не расширен). 27 passed. Греп: `hx-push-url` в шаблонах 0; реальный отправитель `HX-Push-Url` один (`app/pages/ads.py:783`), ещё два упоминания в прозе. Сводка: `15-FORM-DECISIONS.md` (`status: subject`, 49 мест, 19 дуальных → ветвь владельца `case-three-server-header`). |
| 4 | `*_degrades_without_alpine` получили ПАРНЫЕ `*_degrades_without_htmx`, без переименований (машинно, счёт пар) | ✓ VERIFIED | `tests/test_templates/test_degradation_pairs.py`: `DEGRADATION_PAIRS_DECLARED = 5`, предикат пары объявлен до первого числа; 15 passed. Сравнил имена на `ed82f990` (старт фазы) и HEAD: удалённых 0, добавленных 5; 10 тестов `degrades_without` в трёх файлах проходят. ⚠️ WR-03: четыре пары удаления не утверждают ни удаления, ни точного `Location` (advisory). |
| 5a | Слепая зона условной сборки: либо форма запрещена гейтом, либо проверена глазами; границы каждого гейта выписаны в докстринге его файла | ✓ VERIFIED | `CONDITIONAL_HX_POST_SITES: dict[str, str] = {}` с оговоркой «ИМЕНОВАННЫЙ НОЛЬ» (`test_htmx_markup_gates.py:8180-8186`), контроль синтетическим `{% if x %}hx-post="/y"{% endif %}`; инвентарь настоящей слепой зоны `CONDITIONAL_HX_SITES_OUTSIDE_MACRO = 12` + 6 ветвей макроса. 39 passed в группах. Абзац «чего не утверждает» есть во всех шести новых модулях и в заголовках групп трёх расширенных; докстринг модуля `test_htmx_markup_gates.py` называет слепую зону (раздел «ЧЕГО ГЕЙТ НЕ ВИДИТ»). |
| 5b | Девять именованных пунктов ручного UAT закрыты поимённо | ? HUMAN | `15-UAT.md`: `status: human_needed`, `checks_declared: 9`, 9 разделов проверок, 9 пустых таблиц отметок, `result: [pending]` ×9. Записи Фаз 7-11, которыми по D-15 принимаются пункты 1-8, на месте (нашёл названные разделы в `07/08/09/10/11-UAT.md`) — это машинная улика, а не отметка. Отметки заполняет только владелец (D-17). |
| 6a | Критерий 6 (а): в дереве ОДИН исполняемый прибор переписи, чьё число воспроизводимо | ✓ VERIFIED | `scripts/prohibitions_census.py --check` → exit 0; 697 элементов на 156 планах (07:31 08:24 09:153 10:321 11:68 12:22 13:8 14:23 15:47); «реестр: 697 строк, биекция с переписью — согласие». Модуль `test_plan_prohibitions_census.py` (64 правила) утверждает биекцию, воспроизводство 650 на 142 планах и четырёх исторических сетей 374/76/57/38. Порядок D-03 соблюдён: прибор 15-01, классы 15-12, решения 15-13. |
| 6b | Критерий 6 (б): по каждому запрету перечня — ЛИБО предъявленное принуждение, ЛИБО явное разрешение с `permit_scope` | ✗ FAILED | `--breakdown` по области решений (321): enforced 2, partially-enforced 32, permitted 202, **unresolved 85** (declared-rule-absent 27, enforcement-required 58). У 85 нет ни принуждения, ни разрешения. Закрывающее правило утверждает ослабленную форму «решён или названа причина». См. Gaps. |

**Score:** 6/8 истин ROADMAP (1 провалена, 1 за человеком); 151/157 истин планов (6 переданы человеку: 5 backstop без явной улики + 1 отрисовка), 0 present-behavior-unverified.

### Истины планов (сводно)

| План | Истин | Статус | Опора |
|---|---:|---|---|
| 15-01 прибор переписи | 13 | ✓ 13 | 34+ правил модуля переписи; backstop чистоты — `test_the_order_of_sources_does_not_move_the_identities` |
| 15-02 инвентарь 49/27 | 9 | ✓ 9 | `test_form_inventory.py` 24 passed; летопись и «27 → 29 нет» в докстринге |
| 15-03 пары деградации | 11 | ✓ 10, ? 1 | 15 + 10 passed; backstop порядка без явного правила → человеку |
| 15-04 запрет FETCH-03 | 9 | ✓ 8, ? 1 | 16 passed; инвентарь `onerror` = 1 (`components/thumb.html#0`); backstop чистоты → человеку |
| 15-05 запрет условного `hx-post` | 11 | ✓ 11 | 39 passed в группах; летописи 4 → 3 классов и 8 → 6 ветвей |
| 15-06 входное условие | 9 | ✓ 8, ? 1 | `14-UAT.md` `status: human_needed`, отметки пусты; `REQUIREMENTS.md` +6/-0 за фазу; backstop «снимок» → человеку |
| 15-07 орган снятия | 10 | ✓ 9, ? 1 | `test_banner_dismiss.py` 20 passed; два разных `aria-label`; `padding-right: 38px` выведен из коробки; отрисовка → человеку (У-8) |
| 15-08 CR-01 обоими корнями | 13 | ✓ 13 | `schedules_update`: `profile_tz`/`stored_tz` из `VALID_TIMEZONES`, вызов `next_run_or_none(schedule)`; `-k "malformed_stored or idle_editor"` 33 passed; `test_schedule_rules_gate.py` 9 passed |
| 15-09 литерал `limit=30`, OOB | 11 | ✓ 11 | греп `limit=30` в шаблонах → 0; `test_markup_literal_inventory.py` 12 passed; `OOB_TARGET_EXCEPTIONS_DECLARED = 4` с диспозицией «перезаписано» |
| 15-10 связка D-07 | 9 | ✓ 9 | четыре счёта по 18; `test_modal_linkage_counts_are_a_pure_function_of_the_passed_mapping` |
| 15-11 `hx-push-url` | 14 | ✓ 13, ? 1 | 27 passed; GATE-07 держит правило `test_every_header_write_has_a_safe_right_operand`; backstop чистоты реестра → человеку |
| 15-12 классы | 12 | ✓ 12 | 11 классов, `DISPOSITIONS_DECLARED = 4`, `class_decisions` (10 permit-class + 1 require-enforcement); `test_the_gate_never_calls_the_draft_classifier` |
| 15-13 диспозиции | 13 | ✓ 12, ? 1 | каждая строка решена либо несёт причину; `15-PROHIBITIONS-SUBJECT.md` 321 строка, `status: subject`; backstop порядка `ast` → человеку |
| 15-14 обход и летопись | 13 | ✓ 13 | три счёта `15-UAT.md` сходятся; летопись в двух местах идентична; полная суита — замер оркестратора (см. ниже) |

⚠️ Истины планов сошлись, а критерий 6 ROADMAP нет. Это ровно тот случай, когда задачи исполнены, а цель пропущена: план 15-13 записал свою истину в ослабленной форме (явно назвав её условной), а текст критерия ROADMAP не ослаблен никакой записью отступления.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `scripts/prohibitions_census.py` | единственный прибор переписи | ✓ VERIFIED | `--check` exit 0, `--breakdown` воспроизводит числа сводок |
| `.../15-prohibitions-registry.yaml` | 697 строк, класс и диспозиция полями | ✓ VERIFIED | биекция подтверждена прибором; 321 строка Фазы 10 с классом |
| `tests/test_planning/test_plan_prohibitions_census.py` | принуждающая половина | ✓ VERIFIED | входит в прогон `tests/test_planning/` (см. ниже) |
| `.../15-PROHIBITIONS-SUBJECT.md` | человеческий реестр, `status: subject` | ✓ VERIFIED | `prohibitions_permitted: 202`, `prohibitions_partially_enforced: 32`, остаток числами |
| `tests/test_templates/test_form_inventory.py` | инвентарь 49/27 | ✓ VERIFIED | 24 passed |
| `tests/test_templates/test_degradation_pairs.py` | счёт пар | ✓ VERIFIED | 15 passed |
| `tests/test_templates/test_htmx_inventory.py` (группы FETCH-03, атрибутов-обработчиков) | запрет и инвентарь | ✓ VERIFIED | 16 passed |
| `tests/test_templates/test_htmx_markup_gates.py` (условный `hx-post`, слепая зона, связка) | три группы | ✓ VERIFIED | 39 passed |
| `tests/test_pages/test_htmx_gates.py` (группа `hx-push-url`) | реестр трёх случаев, запрет D-13 | ✓ VERIFIED | 27 passed |
| `.../15-FORM-DECISIONS.md` | сводка решений | ✓ VERIFIED | 49 мест, 19 спорных с ответом владельца полями |
| `tests/test_templates/test_markup_literal_inventory.py` | отсутствие литерала | ✓ VERIFIED | 12 passed |
| `tests/test_templates/test_banner_dismiss.py`, `htmx_error_banner.html`, `app.css` | различимые имена, компенсация | ✓ VERIFIED | 20 passed |
| `tests/test_services/test_schedule_rules_gate.py`, `app/pages/schedules.py`, `app/services/schedule_rules.py` | CR-01, гейт по `ast` | ✓ VERIFIED | 9 + 33 passed; код прочитан |
| `.../15-UAT.md` | девять пунктов, пустые отметки, раздел улики | ✓ VERIFIED (как артефакт) | отметки пусты по замыслу — см. Human Verification |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| перепись (живой разбор планов) | реестр YAML | биекция по тождеству «путь + индекс» | ✓ WIRED | прибор: «биекция с переписью — согласие» |
| объявленные 49/27 | живой обход `app/templates/**/*.html` | равенство, не порог | ✓ WIRED | контроли 50-го места и снятого вызова краснеют |
| 18 форм-триггеров | форма `components/modal.html` с `hx-post` | четыре независимых счёта | ✓ WIRED | места не слиты: инвентарь по-прежнему 49 |
| реестр `hx-push-url` | инвентарь 49 мест | каждое место → решённый обработчик | ✓ WIRED | `test_push_url_every_write_place_resolves_to_a_decided_handler` |
| `schedules_update` | `next_run_or_none` | вызов вместо прямого вычислителя | ✓ WIRED | прочитано в коде; правило по `ast` |
| `PAGE_SIZE` модулей | шесть шаблонов | `page_size` в контексте обоих обработчиков | ✓ WIRED | греп `limit=30` → 0; правило контекста зелено |
| класс ↔ ответ владельца ↔ диспозиция «разрешено» | реестр | `permit_scope` = имя класса | ✓ WIRED | `ключей разрешения в строках реестра: 202` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| шесть сентинелов порций | `page_size` | `PAGE_SIZE` модуля (`ads.py`, `accounts.py`, `schedules.py`) через контекст страницы и порции | да — правило ловит контекст шпионом и сверяет с константой | ✓ FLOWING (латентный путь 422 при пропавшем ключе — UI-REVIEW, advisory) |
| `schedules_update` зона | `tz` | форма → проверка `VALID_TIMEZONES` → `stored_tz` → `profile_tz` → `UTC` | да — правило читает записанную зону из СУБД | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| Шесть новых модулей фазы | `uv run pytest -q tests/test_templates/{test_form_inventory,test_degradation_pairs,test_markup_literal_inventory,test_banner_dismiss}.py tests/test_services/test_schedule_rules_gate.py` | 80 passed | ✓ PASS |
| Запрет FETCH-03 и инвентарь атрибутов | `... test_htmx_inventory.py -k "fetch_prohibition or inline_event or manual"` | 16 passed | ✓ PASS |
| Условный `hx-post`, слепая зона, связка | `... test_htmx_markup_gates.py -k "conditional or modal_linkage or ..."` | 39 passed | ✓ PASS |
| `hx-push-url` и обработчиковая половина FORM-01 | `... test_htmx_gates.py -k "push_url or backlog or named_zero"` | 27 passed | ✓ PASS |
| Пары деградации (5 + 5) | `... test_billing_section.py test_responsive_markup.py test_ads_editor.py -k degrades_without` | 10 passed | ✓ PASS |
| CR-01 на четвёртом входе | `... test_editor_schedules.py -k "malformed_stored or idle_editor"` | 33 passed | ✓ PASS |
| Пять модулей в порядке по умолчанию | `uv run pytest -q` (form_inventory, degradation_pairs, htmx_inventory, htmx_markup_gates, htmx_gates) | 275 passed | ✓ PASS |
| Прибор переписи | `uv run python scripts/prohibitions_census.py --check` | exit 0, биекция согласна | ✓ PASS |
| Каталог записи после записи этого отчёта | `uv run pytest tests/test_planning/ -q` | см. раздел «Прогон после записи» | ✓ PASS |

**Полная суита.** Сам не гонял (запрет повторного полного прогона). Замер оркестратора: дерево `a0e58c2a` после плана 15-14 — `3867 passed, 0 failed`. Проверил, что после `a0e58c2a` менялись только `.planning/WINDOWS.md`, `15-REVIEW.md`, `15-UI-REVIEW.md`, `15-VALIDATION.md` — код и тесты не тронуты. Отказ волны 1 (пара 302 на `test_billing_section.py:706`) починен коммитом `4cd2d45c`; `deferred-items.md` помечен `resolved`.

### Probe Execution

Step 7c: SKIPPED — фаза не объявляет probe-скриптов, а `scripts/*/tests/probe-*.sh` в дереве нет. Исполняемый прибор фазы (`scripts/prohibitions_census.py --check`) прогнан выше.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| FORM-01 | 15-02, 15-10, 15-14 | любое действие письма без перезагрузки — все формы через `hx-post` | ✓ SATISFIED (машинная часть) | истина 1; рантайм — пункты 3/5 обхода, принятые записью по D-15 |
| FETCH-03 | 15-04, 15-06 | `fetch(` в `app/templates/` == 0 | ✓ SATISFIED | истина 2 |
| QUAL-04 | 15-11 | решение `hx-push-url` по каждой форме по конвенции трёх случаев | ✓ SATISFIED | истина 3; верность в браузере — пункт 7, запись Фазы 11 |
| GATE-09 | 15-05, 15-06, 15-07, 15-09, 15-14 | девять пунктов ручного UAT закрыты | ? NEEDS HUMAN | артефакт готов, отметки пусты по D-17 |
| GATE-10 | 15-03, 15-09 | парные `*_degrades_without_htmx` без переименований | ✓ SATISFIED | истина 4 (WR-03 — advisory) |
| `критерий-6` (не ID `REQUIREMENTS.md`) | 15-01, 15-12, 15-13 | долг Фазы 10: прибор + решение по каждому запрету | ✗ BLOCKED (половина б) | истина 6b |
| `долг-D-18` (не ID `REQUIREMENTS.md`) | 15-08 (и 15-07 по D-18.3) | три находки Фазы 10 | ✓ SATISFIED с оговоркой | D-18.1 и D-18.2 закрыты; D-18.3 — имя и место закрыты, роль и внешность не починены и не записаны принятыми (advisory UI-REVIEW) |

Сирот нет: таблица состояний `REQUIREMENTS.md` относит к Фазе 15 ровно пять ID (FORM-01, QUAL-04, FETCH-03, GATE-09, GATE-10), и каждый объявлен хотя бы одним планом. Все пять — `Pending`/`[ ]`; этот отчёт отметок не ставил.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | `TBD` / `FIXME` / `XXX` в добавленных строках 29 файлов кода и тестов фазы | — | не найдено ни одного |
| — | — | `TODO` / `HACK` в добавленных строках | — | не найдено ни одного |
| `tests/test_pages/test_responsive_markup.py` | 3492 и др. | слабое утверждение исхода (WR-03) | ⚠️ Warning | пары не отличают холостую ветвь от удаления |
| `tests/test_pages/test_editor_schedules.py` | 4393-4518 | правила закрепляют спорную политику (WR-01, WR-02) | ⚠️ Warning | будущая починка покраснит правила фазы |
| `tests/test_planning/test_plan_prohibitions_census.py` | 125-162 | литералы с именем фазы над растущей вселенной (WR-04) | ⚠️ Warning | покраснит полный прогон на первом плане закрытия |

`CONDITIONAL_HX_POST_SITES = {}`, `MODAL_TRIGGER_ACTION_FROM_PAGES_SITES = {}`, `MODAL_OPEN_CALLS_OUTSIDE_SUBMIT_SITES = {}` — именованные нули с контролями от вакуума, не заглушки.

### Prohibitions (must-NOT, ADR-550)

47 запретов в планах Фазы 15, все judgment-tier (`flagged-unverified`, без `verification: test`) — **unverified-prohibition, human review recommended**. Неавторитетный вердикт LLM-судьи: нарушений по существу не нашёл. Отдельно флагированы две позиции:

- **15-14 #1** («MUST NOT писать `result`»): буква нарушена. В `15-UAT.md` девять раз стоит `result: [pending]`, по указанию оркестратора и по форме, которую ходит `/gsd-verify-work`. Вердикта не написано ни одного.
- **15-08 #3** (правило о непочиненном — только под маркером `characterisation`): по букве запрет касается только WR-03 Фазы 10. По духу его задевают WR-01 и WR-02: правила фазы закрепляют политику «гасить молча» и асимметрию `schedules_create`.

Остальные запреты сверены выборочно, и нарушений не нашёл:
- полей `permit_*` без ответа владельца нет;
- переименований тестов деградации нет (сверка имён `ed82f990..HEAD`);
- текст требований не правлен (0 удалённых строк);
- регистраций обработчика в файле плашки по-прежнему 3;
- G-2 на GET не расширен;
- литерал `limit=30` заменён значением контекста, второй носитель числа не заведён.

### Human Verification Required

#### H1 — Сводный обход `15-UAT.md` (GATE-09, критерий 5)

**Test:** владелец проходит девять пунктов и заполняет таблицы отметок и `result`. Пункты 1-8 — сверка названных записей Фаз 7-11. Пункт 3, шаги 3.2-3.4 — приземление фокуса на location-пути, смотреть глазами. Пункт 9 — 12 мест условной сборки в объявленном порядке: 2 места вооружения опроса, 2 внеполосных, 8 каскадных; плюс 6 ветвей `form_wrapper`.
**Expected:** девять отметок с наблюдённым признаком, датой, браузером/ОС и наблюдателем. Шапка переходит в терминальное состояние только после этого.
**Why human:** JS в суите не исполняется. Самозаверение запрещено правилом `test_the_walkthrough_cannot_self_certify.py`. Этот отчёт ни одной клетки не заполнял.

#### H2 — Пять наблюдений органа снятия плашки (У-8)

**Test:** окно 1280 px, двойная авария (500 и обрыв сети).
**Expected:**
- обвод фокуса виден и контрастен;
- пробел снимает плашку;
- текст не сталкивается с крестиком;
- два имени различимы на слух;
- вторая плашка смещена не хуже известного.
**Why human:** движка раскладки в суите нет. UI-REVIEW оценил контраст обвода примерно в 2.6:1, то есть ниже 3:1; это оценка, а не наблюдение.

#### H3 — Backstop-утверждения без явного правила (insufficient_spec)

**Test:** принять структурную улику или заказать правило порядка для пяти утверждений:
- чистота и независимость от порядка гейта пар (15-03);
- то же для запрета FETCH-03 (15-04);
- то же для реестра `hx-push-url` (15-11);
- то же для предъявления правил по `ast` (15-13);
- «чтение из одного снимка» (15-06).

**Expected:** решение человека.
**Why human:** присутствие функции с параметром-отображением само по себе улики не даёт. Плагина случайного порядка в окружении нет, поэтому прогон в ином порядке не наблюдался. Для 15-01 и 15-10 явные правила есть, и эти утверждения засчитаны.

#### H4 — Обзор запретов планов (judgment-tier)

**Test:** принять или отклонить две флагированные позиции: 15-14 #1 и 15-08 #3.
**Why human:** вердикт LLM-судьи неавторитетен.

#### H5 — Открытые вопросы владельцу, переданные планом 15-14

1. Нужна ли запись «27 → 29 файлов с любой формой» (15-02).
2. Самопротиворечие `14-UAT.md`: в теле `result: pass` ×9, а решение #4 говорит «обход глазами не делался» (15-06).
3. Оставить или снять четыре `OOB_TARGET_EXCEPTIONS` (15-09).
4. Адресаты по плану 15-13:
   - принуждение `product-invariant`;
   - 376 запретов вне Фазы 10;
   - 27 объявленных, но отсутствующих правил.
5. Роль и внешность органа снятия (половина D-18.3): починить или записать принятым следствием.

### Gaps Summary

**Один блокер, корень один — критерий 6 (б).**

Прибор переписи есть и воспроизводим, половина (а) закрыта. Решения по каждому из 321 запрета Фазы 10 записаны построчно. Но критерий ROADMAP требует у КАЖДОГО запрета либо принуждения, либо разрешения с `permit_scope`, а 85 запретов не несут ни того, ни другого:
- **58** — класс `product-invariant`. Владелец сам выбрал `require-enforcement`, правил нет, адресат работы не назначен.
- **27** — объявили `verification: test`, а правила в дереве нет. По D-05 разрешение класса их не закрывает.

Ещё у 9 запретов `product-invariant` принуждение только частичное.

План 15-13 честно назвал свою истину ослабленной формой и записал остаток числом. Однако план не вправе сужать критерий ROADMAP, и записи отступления (`overrides:`) нет.

Более поздней фазы в вехе нет: Фаза 15 последняя, `.planning/phases/` кончается на 15. Поэтому отложить гэп некуда (Step 9b).

**Если это отступление намеренно** (владелец считает решение `require-enforcement` плюс названный остаток достаточным закрытием критерия), принять его можно записью в шапку этого файла:

```yaml
overrides:
  - must_have: "Критерий 6 ROADMAP, половина (б): по каждому запрету перечня прибора стоит ЛИБО предъявленное машинное принуждение, ЛИБО явное человеческое разрешение с машинно читаемой областью (`permit_scope`)"
    reason: "Остаток 85 (58 require-enforcement по решению владельца + 27 находок D-05) назван числом и причиной в реестре; адресат работы — {назвать фазу/веху}"
    accepted_by: "chubav"
    accepted_at: "{ISO timestamp}"
```

⚠️ Отчёт переписывается целиком при каждой верификации. Подписанный блок `overrides` надо сохранять явным указанием в промпте следующей верификации.

**Для планировщика закрытия (WR-04).** Любой новый план в `.planning/phases/` с блоком запретов покраснит `tests/test_planning/test_plan_prohibitions_census.py`. Планировщик закрытия гэпов `REVIEW.md` не читает, поэтому предупреждение продублировано в `gaps[0].missing`.

Прочие находки — advisory (WR-01…WR-04, IN-01…IN-06, UI-REVIEW 17/24), ни одна не блокирует цель.

### Прогон после записи

`uv run pytest tests/test_planning/ -q` на дереве с этим отчётом (2026-09-24): **108 passed**, 0 failed, 5.42 s. Отпечаток `covered_digest` пересчитан из списка шапки после записи и совпал.

---

_Verified: 2026-09-24T19:40:00Z_
_Verifier: Claude (gsd-verifier)_
