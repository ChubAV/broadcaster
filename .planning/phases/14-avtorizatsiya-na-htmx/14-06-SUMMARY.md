---
phase: 14-avtorizatsiya-na-htmx
plan: 06
subsystem: auth
tags: [htmx, fastapi, jinja2, response-layer, impersonation, hx-location, hx-redirect, csrf, tdd]

requires:
  - phase: 14-avtorizatsiya-na-htmx
    provides: "14-01 — `redirect_internal`, семейство `RESPONSE_LAYER_EXITS`, ветка пар `FULL_LOAD`; 14-02 — `respond_screen`, ветка `SCREEN`; 14-05 — `NOTICE_WRITE_PLACES = 0` в страничном слое, окончательный шелл, отставание в 1 ключ"
  - phase: 10-rychag-components-modal-html
    provides: "D-05: прецедент `admin_impersonate` — cookie на ВОЗВРАЩЁННОМ ответе 204 с `HX-Location`"
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: "D-08: прецедент именованного изъятия «голый 403 на провале сверки источника»; реестр `OWN_RESPONSE_EXITS` и три его правила (полнота, обоснования, авторство)"
provides:
  - "`stop_impersonation` на выходах слоя: успех — 204 + `HX-Location: /admin` с cookie без признака действующего лица на том же ответе; «действующего лица нет» — `HX-Location: /dashboard` без единого токена; закрытое либо исчезнувшее действующее лицо — 204 + `HX-Redirect: /login` со снятием cookie через границу шеллов (D-12)"
  - "отказ по источнику у возврата — прежний голый 403 на ОБОИХ транспортах, объявленный записью `OWN_RESPONSE_EXITS` в состоянии `DECISION_OWNER_D01_F14` (D-01)"
  - "форма возврата в полосе `base.html` — `form_wrapper` без цели (`hx-swap=\"none\"`), класс прижатия на обёртке `.impersonation-back`"
  - "гейт критерия 3: `FULL_LOAD_CALL`, `AUTH_MODULE`, `FULL_LOAD_HANDLERS`, `AUTH_HX_LOCATION_HANDLERS`, помощники `_full_load_calls` / `_full_load_callers` / `_hx_location_emitters` / `_local_literal_complaints`, три правила и три двухшаговых контроля"
  - "ИМЕНОВАННЫЙ НОЛЬ отставания вехи: `NOT_YET_CONVERTED` пуст и не удалён, `NOT_YET_CONVERTED_COUNT = 0`, доказанный не вакуумным правилом `test_the_named_zero_of_the_backlog_is_not_a_broken_scanner`"
  - "`/admin` в карте назначений перехода; пара возврата; `base.html` среди вызывающих макроса"
affects: [14-07]

actuals:
  tokens: 24970
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "возврат личности на слое ответа: `response = await respond(request, redirect=\"/admin\")` → `set_session_cookie(response, …)` на ЭТОМ ЖЕ объекте; ветка смены шелла — `redirect_internal` + `clear_session_cookie` на возвращённом объекте"
    - "форма шелла без цели подмены: блочный `form_wrapper(action=…)` внутри `<div>`-обёртки, несущей класс раскладки, — тег формы печатает макрос, и своего класса у него нет"
    - "именованный ноль убывающего счётчика: перечень объявлен пустым (форма `NEVER_RESPONDS`), а ноль доказан правилом, которое ТЕМ ЖЕ прогоном находит непустую вселенную и находит отставание на синтетическом дереве"

key-files:
  created: []
  modified:
    - app/pages/auth.py
    - app/templates/base.html
    - tests/test_pages/test_impersonation.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_templates/test_htmx_markup_gates.py

key-decisions:
  - "Исчезнувшее действующее лицо подаётся правилу собранным вручную токеном, а не удалением строки администратора: удаление унесло бы подписку и посев, которыми живут соседние утверждения того же теста, и правило краснело бы по ЧУЖОЙ причине"
  - "Запись возврата в `OWN_RESPONSE_EXITS` поставлена в СВОЁ состояние `DECISION_OWNER_D01_F14`, а не в `DECISION_OWNER_D08`: абзацы у D-08 прямо называют `stop_impersonation` обработчиком, которого D-08 не называет ни множеством, ни именем. Та же граница, которую соблюдала запись Фазы 12 (`DECISION_OWNER_D15`)"
  - "Ноль отставания доказан ОТДЕЛЬНЫМ правилом, а не летописью: «переведены все» и «разбор сломался» приходят в счётчик одним и тем же числом, и с опустевшим перечнем различить их было бы нечем"
  - "`base.html` внесён только в кортеж вызывающих макроса, но НЕ в перечень параметрических целей: цели у формы возврата нет намеренно — любой её исход есть переход"

patterns-established:
  - "Гейт требования роадмапа, у которого есть ВТОРОЙ отправитель вне вселенной правила, называет свою границу в шапке группы прямо — иначе зелёное правило читалось бы как доказательство более широкого утверждения, чем то, которое оно проверяет"

requirements-completed: []

coverage:
  - id: D1
    description: "Успех возврата на пути htmx: 204, `HX-Location: /admin`, без `HX-Redirect`, тело пустое, cookie БЕЗ признака действующего лица на ТОМ ЖЕ ответе; следующий `GET /admin` — 200, полоса имперсонации с `/dashboard` исчезла"
    requirement: SIGN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_return_over_htmx_keeps_both_the_location_and_the_admin_cookie"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_return_rewrites_the_cookie_with_the_same_attribute_set"
        status: pass
    human_judgment: false
  - id: D2
    description: "Возврат без действующего лица: без htmx — 302 на `/dashboard`, с htmx — 204 и `HX-Location: /dashboard`; `access_token` не выдаётся ни на одном транспорте"
    requirement: SIGN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_return_without_an_actor_goes_to_the_dashboard_on_both_transports"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[stop_impersonation-возврат из-под чужой личности — действующего лица нет]"
        status: pass
    human_judgment: false
  - id: D3
    description: "Закрытое либо исчезнувшее действующее лицо: без htmx — 302 на `/login`, с htmx — 204 и `HX-Redirect: /login` без `HX-Location`; снятие cookie набором атрибутов установки плюс нулевой срок; админка после этого не открывается"
    requirement: SIGN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_a_closed_actor_is_logged_out_by_the_return_on_both_transports"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_a_blocked_actor_is_logged_out_by_the_return_not_re_admitted"
        status: pass
    human_judgment: false
  - id: D4
    description: "Чужой источник: 403, пустое тело, ни одного `access_token` в `set-cookie` и ни одного заголовка с приставкой `HX-` — на ОБОИХ транспортах (D-01)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_a_cross_origin_return_is_refused_with_a_bare_403_on_both_transports"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_origin_guard_on_destructive_routes.py (полный модуль)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Форма возврата рождена макросом: `hx-post=\"/impersonation/stop\"` и `hx-swap=\"none\"` на теге, форма внутри `<div class=\"impersonation-back\">`; без JS остаётся настоящей формой POST"
    requirement: SIGN-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_return_form_rides_the_macro_and_swaps_nothing"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_impersonation.py#test_the_return_control_is_a_real_post_form"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py (полный модуль, 84 passed)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Критерий 3 — машинное правило: вызывающие выхода полной перезагрузки РАВНЫ четырём названным, адрес каждого — литерал локального пути, отправители `HX-Location` в модуле авторизации РАВНЫ `{stop_impersonation}`; у каждого правила двухшаговый отрицательный контроль"
    requirement: SIGN-03
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_only_the_named_auth_handlers_leave_by_a_full_load"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_every_full_load_address_is_a_literal_local_path"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_hx_location_in_the_auth_module_belongs_to_the_return_only"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_fifth_full_load_caller_reddens_the_criterion_three_gate"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_bare_respond_in_the_login_reddens_the_hx_location_gate"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_computed_full_load_address_reddens_the_literal_rule"
        status: pass
    human_judgment: false
  - id: D7
    description: "Именованный ноль отставания вехи: `NOT_YET_CONVERTED` пуст и не удалён, `NOT_YET_CONVERTED_COUNT = 0`, и ноль доказан НЕ ВАКУУМНЫМ — тем же прогоном вселенная POST-обработчиков непуста, а отставание находится на синтетическом дереве"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_named_zero_of_the_backlog_is_not_a_broken_scanner"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_backlog_matches_the_declared_count"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_lookalike_exit_name_does_not_convert_a_handler"
        status: pass
    human_judgment: false
  - id: D8
    description: "Перечни поставлены прогоном: отставание 1 → 0, собственные выходы 13 → 14, пары 76 → 77, утверждения 302 184 → 188, назначения перехода 77 → 79 с `/admin` в карте, вызывающие макроса 31 → 32, блоки вызова 28 → 29"
    verification:
      - kind: unit
        ref: "прогон гейтов волны (последняя команда `<verify>` задачи 3, 13 модулей): 718 passed, 0 failed"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/ -q -p no:randomly — 3605 passed, 0 failed"
        status: pass
    human_judgment: false
  - id: D9
    description: "В браузере «ВЕРНУТЬСЯ В АДМИНА» приводит в админку без перезагрузки документа: адресная строка `/admin`, вкладка — заголовок админки, полосы нет, cookie без признака действующего лица"
    requirement: SIGN-03
    verification: []
    human_judgment: true
    rationale: "Поведение браузера при `HX-Location` (подмена содержимого `body`, уход полосы вместе с ним, смена `<title>`, запись адреса в историю) тестами не измеряется: клиент суиты заголовок перехода не исполняет. Это ручной UAT фазы — критерий 4, D-12"

duration: 81min
completed: 2026-09-22
status: complete
plan_head_before: e012ac40192523f71b7bf0489ddab88f1422ef05
commits: 5
---

# Phase 14 Plan 06: Возврат из-под чужой личности на слое ответа — Summary

**Последний обработчик вехи переведён. Возврат отвечает через выходы слоя: успех — 204 и `HX-Location: /admin` с перевыпущенной cookie без признака действующего лица на ТОМ ЖЕ объекте ответа; «действующего лица нет» — `HX-Location: /dashboard` без единого токена; закрытое или исчезнувшее действующее лицо — 204 и `HX-Redirect: /login` со снятием cookie, единственная ветка возврата, уходящая через границу шеллов. Отказ по чужому источнику остался ГОЛЫМ 403 на обоих транспортах — именованное изъятие решением владельца D-01, объявленное записью реестра в собственном состоянии. Форма возврата в полосе шелла рождена макросом без цели подмены. Критерий 3 стал машинным правилом с тремя двухшаговыми контролями, а счётчик отставания вехи дошёл до ИМЕНОВАННОГО НУЛЯ, доказанного не вакуумным.**

## Performance

- **Duration:** 81 min
- **Started:** 2026-09-22T18:14:32Z
- **Completed:** 2026-09-22T19:35:40Z
- **Tasks:** 3
- **Files modified:** 7 — РОВНО файлы, объявленные планом. Ни одного файла сверх набора: ни один регистр вне плана прогоном не покраснел

## Accomplishments

- `app/pages/auth.py`: `stop_impersonation` снял оба `RedirectResponse` (D-14) и отвечает тремя выходами слоя. Порядок проверок, тексты, атрибуты cookie, журнальная запись `impersonation_stop` и все прежние абзацы докстринга не тронуты (D-15, D-30/D-32); дописаны два абзаца — о трёх ветках на пути htmx и о несущем порядке «ответ слоя → cookie на тот же объект». Сверка источника осталась ПЕРВОЙ, её комментарий дополнен основанием изъятия.
- `app/templates/base.html`: форма возврата — блочный `form_wrapper(action='/impersonation/stop')` внутри `<div class="impersonation-back">`. Комментарий «ВОЗВРАТ — НАСТОЯЩАЯ ФОРМА POST» не стёрт, к нему дописана летопись: требование ИСПОЛНЯЕТСЯ теперь макросом, `method` и `action` печатает он же. Правило `app.css` не менялось — класс прижатия переехал с тега формы на обёртку.
- `tests/test_pages/test_impersonation.py`: пять правил — тройная пара успеха, обе половины «нет действующего лица», три исхода закрытого и исчезнувшего лица, отказ по источнику на обоих транспортах, форма из макроса. Помощники модуля (`_enter`, `_stop`, `_session_cookies`, `_cookie_attrs`, `_act_of`, `RETURN_FORM`, `HTMX_REQUEST`) переиспользованы, а не скопированы.
- `tests/test_pages/test_htmx_gates.py`: гейт критерия 3 (четыре константы, четыре помощника, три правила, три двухшаговых контроля), запись `OWN_RESPONSE_EXITS` возврата с собственным состоянием решения, именованный ноль с антивакуумным правилом.
- Числа сдвинуты ПРОГОНОМ покрасневшего правила, у каждого летопись «Фаза 14, план 14-06» с дословным выводом: `NOT_YET_CONVERTED_COUNT` 1 → 0, `OWN_RESPONSE_EXITS_DECLARED` 13 → 14, `POST_PAIR_CASES_DECLARED` 76 → 77, `PAIRED_302_ASSERTIONS_DECLARED` 184 → 188, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 77 → 79, `MACRO_DEFINITION_SITES_CALLERS_DECLARED` 31 → 32, `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` 28 → 29.

## Task Commits

1. **Задача 1: три ветки возврата, отказ по источнику, форма возврата из макроса.** RED `53dce76f` (test), GREEN `0e4d9bbc` (feat).
2. **Задача 2: гейт критерия 3, запись собственного выхода, именованный ноль.** `61cd74d3` (test: гейт с контролями), `b68a02c1` (test: record — перечни и числа).
3. **Задача 3: пара возврата, `/admin` в карте назначений, форма полосы среди вызывающих макроса.** `a860f6fe` (test: record).

**Plan metadata:** коммит `docs(14-06)` с этим файлом; STATE/ROADMAP идут отдельным коммитом записи.

## TDD Gate Compliance

| Задача | RED commit | Красное утверждение (дословно из прогона) | GREEN commit |
|---|---|---|---|
| 1 | `53dce76f` | `assert 200 == 204` в `test_the_return_over_htmx_keeps_both_the_location_and_the_admin_cookie`. Вывод `uv run pytest tests/test_pages/test_impersonation.py -q -p no:randomly -k return_over_htmx` содержит все три совпадения `<tdd_notes>`: строку `FAILED tests/test_pages/test_impersonation.py::test_the_return_over_htmx_keeps_both_the_location_and_the_admin_cookie`, итог `1 failed, 43 deselected` и причинный литерал `assert 200 == 204` | `0e4d9bbc` |
| 2 | `0e4d9bbc` (см. оговорку ниже) | `число непереведённых обработчиков стало 0, а в файле записано 1. ЕСЛИ ЧИСЛО УПАЛО — ЭТО ПРОГРЕСС ВЕХИ, а не поломка` / `assert 0 == 1` в `test_the_backlog_matches_the_declared_count` | `b68a02c1` |

- RED-улика ОБЕИХ задач проверена штатным вербом: `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` (`target_test_failed`, exit 1). Запись собрана из `--junit-xml` того же прогона и перегнана в TAP скриптом в scratchpad; скрипт не закоммичен. ⚠️ Верб принимает имя цели только в том виде, в каком оно стоит описанием строки TAP: пара `classname.name` из junit даёт `no_target_test_failure`, а `# tests N` в сводке TAP обязателен — без него вердикт `zero_tests_discovered`.
- **ЧЕСТНАЯ ОГОВОРКА ПО ЗАДАЧЕ 2: отдельного RED-коммита у неё нет, и это НЕ пропуск дисциплины, а отказ изготовить RED руками.** Правила, которые задача 2 чинит, покраснели от ПРОДУКТОВОЙ правки задачи 1 и были красны на коммите `0e4d9bbc` — пять штук: `test_the_three_sets_do_not_overlap`, `test_the_backlog_matches_the_declared_count`, `test_control_positive_the_untouched_source_tree_keeps_every_gate_green`, `test_every_own_response_exit_of_a_converted_handler_is_declared`, `test_control_a_shortened_own_response_list_reddens_the_completeness_rule`. Написать вместо них «красный» тест значило бы либо объявить заведомо неверную константу (`FULL_LOAD_HANDLERS` без возврата), либо сослаться на несуществующий помощник и получить `INVALID_RED` по загрузке модуля. Улика снята с дерева `0e4d9bbc` ДО единой правки `test_htmx_gates.py`.
- **Шесть новых правил гейта критерия 3 зелены с первого прогона, и в RED они НЕ ЗАСЧИТАНЫ.** Это правила о ГОТОВОМ состоянии дерева: возврат уже был переведён задачей 1, а `FULL_LOAD_HANDLERS` и `AUTH_HX_LOCATION_HANDLERS` описывают именно его. Их зубы доказывают ТРИ ДВУХШАГОВЫХ КОНТРОЛЯ, каждый из которых сперва утверждает зелень нетронутого дерева и лишь затем роняет правило подменой — то есть «ловит» и «ловит ТОЛЬКО нарушение» доказаны порознь. Коммит `61cd74d3` оставлен отдельным ровно затем, чтобы гейт родился на дереве, где перечни ещё КРАСНЫ, а не вместе с их починкой.
- **Правило отказа по источнику (`test_a_cross_origin_return_is_refused_with_a_bare_403_on_both_transports`) зелено уже на RED-коммите `53dce76f`, и это ожидаемо.** Оно стережёт РЕШЕНИЕ ВЛАДЕЛЬЦА (D-01: форма отказа не меняется переводом), а не новое поведение. В RED оно не засчитано — красных на `53dce76f` было четыре из пяти. Его зубы: отсутствие ЛЮБОГО заголовка с приставкой `HX-` и отсутствие cookie на обоих транспортах — оба утверждения покраснели бы, утащи перевод отказ в слой ответа «заодно».
- Гейт-валидация истории: `test(14-06)` — 4 коммита, `feat(14-06)` — 1. `refactor(14-06)` нет: он не понадобился.

## Именованный ноль — чем доказано, что это не вакуум

`NOT_YET_CONVERTED_COUNT = 0` — самое опасное число вехи: «переведены все» и «разбор сломался и не нашёл никого» приходят в правило ОДНИМ И ТЕМ ЖЕ числом. Пока в перечне оставался хоть один ключ, разницу ловил сам перечень. С пустым перечнем ловить её нечем, поэтому вместе с нулём заведено правило `test_the_named_zero_of_the_backlog_is_not_a_broken_scanner`, снимающее ТЕМ ЖЕ ПРОГОНОМ обе половины доказательства:

1. **Вселенная обхода непуста** — `_post_handlers(_pages_sources())` находит POST-обработчиков страничного слоя больше одного, то есть разбор дерева работает. Это же подтверждают соседние числа того же прогона: `POST_HANDLERS`, `_converted`, `OWN_RESPONSE_EXITS` (14 записей, найденных ЗАМЕРОМ по тому же дереву).
2. **На дереве, где отставанию ЕСТЬ ЧТО НАЙТИ, то же выражение его находит** — синтетическому обработчику `a_route_written_past_the_response_layer`, отвечающему `HTMLResponse` мимо слоя, `_backlog` возвращает его ключ.

Третий свидетель того же прогона — прежний контроль `test_control_a_lookalike_exit_name_does_not_convert_a_handler`: он независимо утверждает `key in _backlog(sources)` на обработчике с похожим именем выхода. То есть непустое отставание на синтетике видят ДВА разных правила одного прогона.

Кроме того, ноль не «держится тем, что работа кончилась»: его держат `test_the_backlog_never_grows` (число не поднимается) и замыкающее правило полноты `_unclassified` (любой новый POST-обработчик мимо слоя не попадёт ни в одно из трёх множеств и покраснит прогон). Оба записаны летописью у самого числа.

## Границы правил, названные прямо

- **У буквального текста критерия 3 есть ВТОРОЙ отправитель `HX-Location`**, и он живёт ВНЕ модуля авторизации: отказ зависимости `forbid_when_impersonating` на четырёх шагах восстановления уходит `location_response` из обработчика `HtmxRefusal` (`app/main.py`, `app/dependencies.py`). Гейт его не видит ПО ПОСТРОЕНИЮ — вселенная правила есть модуль авторизации, — и это записано в шапке группы, чтобы зелёное правило не читалось как доказательство более широкого утверждения. Летопись у критерия 3 и SIGN-03 ставит план 14-07 (D-13, RESEARCH Находка 6).
- **Третья ветка возврата пересекает границу шеллов**, и посылка критерия 3 «не пересекающего границу» верна для двух веток из трёх. Оговорка записана в докстринге обработчика и в летописи числа отставания; текст критерия не переписан (это тоже 14-07).
- **В реестр пар вошёл ОДИН случай из четырёх исходов возврата.** Успех и закрытое действующее лицо требуют cookie ИМПЕРСОНАЦИИ, которой у обхода нет, и утверждены ТРОЙНЫМИ парами в `test_impersonation.py`; отказ по источнику отвечает голым 403 на обоих транспортах, а третьей формы ответа у обхода нет. Обе границы выписаны у посева и в летописи числа.

## Files Created/Modified

- `app/pages/auth.py` — импорт `respond`; `stop_impersonation` на трёх выходах слоя, комментарий изъятия у сверки источника, два новых абзаца докстринга
- `app/templates/base.html` — импорт `form_wrapper`; форма возврата из макроса внутри обёртки прижатия, летопись у прежнего комментария
- `tests/test_pages/test_impersonation.py` — пять правил возврата (+348 строк)
- `tests/test_pages/test_htmx_gates.py` — гейт критерия 3 с контролями, запись `OWN_RESPONSE_EXITS`, `DECISION_OWNER_D01_F14`, `LIFTING_CONDITION_OWN_RESPONSE_RETURN`, именованный ноль с антивакуумным правилом
- `tests/test_pages/test_htmx_post_pairs.py` — ключ `AUTH_STOP_IMPERSONATION`, посев и случай, два числа
- `tests/test_pages/test_hx_location_destinations.py` — `/admin` в карте назначений, число 77 → 79
- `tests/test_templates/test_htmx_markup_gates.py` — `base.html` в кортеже вызывающих, два числа

## Decisions Made

- Решения, отданные планом на усмотрение исполнителя, приняты так, как план их записал: `respond` без фрагмента для двух веток, `redirect_internal` для третьей, `hx-swap="none"` через отсутствие цели у макроса, класс прижатия на обёртке.
- В правила `<behavior>` добавлены утверждения, которых план не называет; ни одно утверждение `<behavior>` не снято:
  - «`HX-Redirect` нет» у успеха и «`HX-Location` нет» у ветки выхода — ответ с двумя заголовками перехода уехал бы по первому, и второй не исполнился бы молча;
  - «тело пустое» у всех трёх веток на пути htmx;
  - у ветки выхода — сравнение НАБОРА атрибутов снятия с набором установки плюс отдельная проверка нулевого срока: набор, взятый умолчаниями, браузер с установкой не сопоставит;
  - у формы возврата — что она стои́т ВНУТРИ обёртки прижатия, а не просто рядом.
- Правило отказа по источнику утверждает отсутствие ЛЮБОГО заголовка с приставкой `HX-`, а не отсутствие конкретных двух: изъятие D-01 требует голого кода, и перечисление имён оставило бы лазейку третьему заголовку.

## Deviations from Plan

### Дополнения (поведение плана не менялось)

**1. [Rule 2 — недостающее критичное] Заведено правило `test_the_named_zero_of_the_backlog_is_not_a_broken_scanner`**
- **Found during:** задача 2
- **Issue:** план требует ИМЕНОВАННОГО нуля с летописью, но летопись — проза: она не отличает «переведены все» от «обход ослеп». С опустевшим перечнем машинного свидетеля этой разницы в файле не осталось ни одного.
- **Fix:** заведено отдельное правило, снимающее обе половины доказательства ТЕМ ЖЕ прогоном (непустая вселенная; отставание найдено на синтетическом дереве). Летопись числа ссылается на него по имени.
- **Files modified:** `tests/test_pages/test_htmx_gates.py`
- **Verification:** `uv run pytest tests/test_pages/test_htmx_gates.py -q -p no:randomly` — 60 passed
- **Committed in:** `b68a02c1`

**2. [Оформление] Задача 2 разделена на ДВА коммита вместо одного**
- **Found during:** задача 2
- **Issue:** план называет задачу 2 `tdd="true"`, а её RED пришёл от продуктовой правки задачи 1 (см. «TDD Gate Compliance»). Слить гейт критерия 3 и починку перечней в один коммит значило бы родить машинное правило на дереве, где перечни уже зелены, — и никто не увидел бы, что гейт краснеть УМЕЕТ.
- **Fix:** `61cd74d3` заводит гейт с контролями на КРАСНОМ дереве; `b68a02c1` чинит перечни. Оба — `test(14-06)`, потому что правки только в тестах.
- **Committed in:** `61cd74d3`, `b68a02c1`

**3. [Замер] Прогноз числа пар совпал, прогноз утверждений 302 — уточнён замером**
- План ждал у `PAIRED_302_ASSERTIONS_DECLARED` «+2 прежних утверждения 302 о возврате плюс новые». Замер дал 184 → 188: ровно 2 прежних (`test_impersonation.py:421`, `:1648`) плюс 2 новых (`:1761`, `:1846`). Половины деградации УСПЕХА среди новых нет — она живёт в прежнем правиле `:421`, и второе утверждение о том же исходе было бы его копией. Это записано в летописи отдельной строкой, иначе число читалось бы как «перевод дал четыре новых».
- **Committed in:** `a860f6fe`

**4. [Замер] Критерии приёмки на дереве до правки**
- Критерии задачи 1 до правки красны все: `RedirectResponse` 2 → 0, `await respond(request, redirect="/admin")` 0 → 1, `await redirect_internal(request, redirect="/login")` 0 → 1, `await respond(request, redirect="/dashboard")` 0 → 1, `form_wrapper(action='/impersonation/stop')` 0 → 1, `<div class="impersonation-back">` 0 → 1. Зелёным до правки был ровно один — `Response(status_code=403)` равен `1`, и это ПРЕДМЕТ критерия, а не вакуум: он утверждает СОХРАННОСТЬ изъятия (D-01), и покраснел бы, утащи перевод отказ в слой.
- Критерии задачи 2 до правки красны все: именованный ноль (`n == frozenset() and c == 0` — код 1), запись `entry=…::stop_impersonation` 0 → 1, `DECISION_OWNER_D01_F14` 0 → 1, `FULL_LOAD_HANDLERS` 0 → 1, `AUTH_HX_LOCATION_HANDLERS` 0 → 1. Критерий «перечень объявлен, а не удалён» (`^NOT_YET_CONVERTED: frozenset` = 1) зелен и ДО, и ПОСЛЕ — он утверждает сохранность объявления, то есть краснеет ровно на том событии, ради которого написан (удалении перечня).
- Критерии задачи 3 до правки: `"/admin": "admin/overview.html"` 0 → 1, `AUTH_STOP_IMPERSONATION` 0 → 2. Три критерия летописи (`Фаза 14, план 14-06` в трёх файлах) считают ПРОЗУ и до правки равны нулю; своей прозой они не зеленеют, потому что растут только вместе с записью числа.

---

**Total deviations:** 4 (1 дополнение правилом, 1 оформление, 2 замера). Ни одного файла сверх семи, объявленных планом. **Impact:** поведение совпадает с планом; дополнение усиливает доказательство нуля, а не меняет объём. `git stash` не вызывался ни разу.

## Tests outside the plan's named set

Правка `base.html` задевает КАЖДУЮ страницу основного шелла, поэтому прогон гейтов волны (последняя команда `<verify>` задачи 3, 13 модулей, включая `test_shell.py`, `test_htmx_inventory.py`, `test_htmx_markup_security.py`, `test_impersonation_gate.py`, `test_identifier_bounds.py`, `test_htmx_preserved.py`) сделан ДО шага метаданных: **718 passed, 0 failed** (15:17).

**Полный прогон суиты сделан ОДИН раз, как требует `<verification>` плана:** `uv run pytest tests/ -q -p no:randomly`, старт **2026-09-22T18:52:37Z** (вне ночного окна 00:00–05:00 UTC админ-обзора — известный шум CONTEXT §Landmines не мог сработать и не сработал), конец 19:32:17Z: **3605 passed, 0 failed, 1053 warnings in 2370.32s (0:39:30)**. `tests/test_planning` в прогон входит. **Ни одного покрасневшего правила вне набора плана прогон не показал** — в отличие от 14-05, где такое правило нашлось одно.

Прочие прогоны: задача 1, первая команда `<verify>` (`test_impersonation.py` + `test_origin_guard_on_destructive_routes.py` + `test_cookie_flags.py`) — 64 passed; задача 2 — `test_htmx_gates.py` 60 passed; задача 3, первая команда — 183 passed. `uv run python -m compileall -q app main.py tests` отработал без вывода. `graphify update .` выполнен: 23009 узлов, 39647 рёбер, 1249 сообществ.

## Issues Encountered

- Верб RED-улики потребовал двух подгонок формата TAP (описание строки — БАРЕ имя теста, а не `classname.name`; обязательная сводка `# tests N` по форме `node:test`). Обе записаны выше, чтобы следующий план не повторял подбор.
- Гейт мест 422 (`SERVER_SIDE_VALIDATION_RESPONSES`) не покраснел: возврат кода 422 не выдаёт ни в одной ветке.
- Контроль `test_control_positive_the_untouched_source_tree_keeps_every_gate_green` и `test_control_a_shortened_own_response_list_reddens_the_completeness_rule` краснели вместе с перечнями и позеленели той же правкой; отдельного сдвига не требовали.

## Known Stubs

None. Все три ветки возврата и отказ по источнику отвечают настоящими данными; форма возврата получает адрес литералом.

## Threat Flags

None. Новых поверхностей сверх `<threat_model>` нет:

- **T-14-10** (подделка формы возврата): сверка источника осталась ПЕРВОЙ, форма отказа не изменилась, правило утверждает голый 403 без тела, без cookie и без единого заголовка `HX-*` на обоих транспортах; модуль `test_origin_guard_on_destructive_routes.py` зелен.
- **T-14-11** (администратор остаётся под чужой личностью): cookie ставится на ВОЗВРАЩЁННЫЙ ответ `respond`; тройная пара утверждает заголовок, cookie без признака действующего лица и ФАКТИЧЕСКИ открывшуюся админку с исчезнувшей полосой.
- **T-14-12** (заблокированный выходит со свежим токеном): ветка сохранена целиком, `clear_session_cookie` на ответе `redirect_internal`; правило утверждает снятие набором атрибутов установки и закрытую админку на ОБОИХ транспортах, плюс отдельным шагом — исчезнувшее действующее лицо.
- **T-14-01** (открытый редирект): все четыре адреса выходов — литералы; заведено машинное правило `test_every_full_load_address_is_a_literal_local_path` с контролем на вычисленном адресе, отвергающее и `//host`.
- **T-14-18** (изъятие без решения): запись стои́т в состоянии `DECISION_OWNER_D01_F14`, называющем `D-01`; правило авторства `_DECISION_REFERENCE` зелено, правило обоснований находит в условии снятия и «Фаза 11», и «ВЛАДЕЛЬЦУ».

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Все десять обработчиков вехи переведены, счётчик отставания — именованный ноль, у каждого есть пара, критерий 3 — машинное правило. Код фазы закончен.
- **14-07 остаются ровно записи:** летописи ROADMAP, REQUIREMENTS и PROJECT (включая обе оговорки к буквальному тексту критерия 3 — третья ветка возврата и второй отправитель `HX-Location` вне модуля авторизации), окно 63 реестра замером и артефакт ручного обхода `14-UAT.md` с настоящими письмами (D-02).
- **Окно 63 к замеру готово:** после этой записи все голые 403 страничного слоя живут во вселенной `OWN_RESPONSE_EXITS` (14 записей), и обработчиков, чей собственный отказ виден счётчику отставания, а не реестру, не осталось — счётчик пуст. Замер и решение о переводе окна `open` → `waived` принадлежат 14-07.
- SIGN-01, SIGN-02 и SIGN-03 НЕ отмечены Complete: их объявляет и план 14-07, у которого ещё нет SUMMARY (`requirements.ready-ids`).

---
*Phase: 14-avtorizatsiya-na-htmx*
*Completed: 2026-09-22*
