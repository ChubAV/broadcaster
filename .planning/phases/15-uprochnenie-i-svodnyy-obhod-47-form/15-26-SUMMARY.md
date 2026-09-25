---
phase: 15-uprochnenie-i-svodnyy-obhod-47-form
plan: 26
subsystem: testing
tags: [prohibitions-census, registry, record-mode, origin-guard, identifier-bound, pagination, session-cookie, write-path, criterion-6, g-1, d-05, d-16, pytest, ast]

requires:
  - phase: 15-uprochnenie-i-svodnyy-obhod-47-form
    provides: "план 15-24 — протокол строки; планы 15-24/15-25 — образец замера двумя мутациями; план 15-22 — режим `--record`"
  - phase: 10-rychag-components-modal-html
    provides: "двенадцать запретов `product-invariant` о серверной стороне письма; гейты гарда происхождения, границы идентификатора, слоя ответа"
provides:
  - "десять из двенадцати строк группы «серверная сторона письма» — `enforced`; у каждой правило, покрасневшее на мутации дерева по формулировке ИМЕННО этой строки"
  - "модуль `tests/test_pages/test_write_path_invariants.py`: 7 правил, 7 контролей, `ORIGIN_GUARD_REFUSAL`, `ORIGIN_GUARD_HEADERS`, `SESSION_COOKIE_SETTER`"
  - "две строки (`10-18#3`, `10-22#0`) переданы чекпойнту плана 15-32 поимённо, с замером"
affects: [15-27, 15-28, 15-29, 15-30, 15-31, 15-32, 15-33, критерий-6]

actuals:
  tokens: 14846
  tasks: 2
  commits: 3
plan_head_before: d73ea5fc62a23514a292e49782e48b90dda081a4

tech-stack:
  added: []
  patterns:
    - "Правило места вызова гарда: обращение к гарду узнаётся по имени ввоза (с псевдонимом и через модуль-владелец) и относится к ближайшему объемлющему обработчику маршрута"
    - "Поведенческое правило формы ответа сличает ответ на негодное поле с ответом на тот же запрос БЕЗ поля, на обоих транспортах; сличитель вынесен функцией, и контроль подаёт ему синтетические наблюдения"

key-files:
  created:
    - tests/test_pages/test_write_path_invariants.py
  modified:
    - .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml

key-decisions:
  - "15-26: `10-31#3` держат действующие правила `test_notices_surface.py` целиком — снятие приклейки внеполосного блока краснит пять правил модуля"
  - "15-26: шесть строк (`10-18#0`, `10-18#1`, `10-25#3`, `10-32#3`, `10-08#2`, `10-12#3`) записаны действующим правилом, покрасневшим на прямом нарушении, плюс новым правилом на форму, на которой действующее зелено; три (`10-03#5`, `10-28#1`, `10-29#1`) — только новым: все действующие правила на замеренном нарушении зелены"
  - "15-26: `10-22#0` передан чекпойнту 15-32 как ЗАМЕЩЁННЫЙ — формулировка «граница НЕ переносится внутрь обработчиков» отменена решением D-07 Фазы 11 (план 11-02), и в дереве 18 обработчиков маршрутов зовут `id_in_column` (23 вызова)"
  - "15-26: `10-18#3` передан чекпойнту 15-32 как КРАСНЫЙ НА ДЕРЕВЕ — второе место параметра кода исхода в адресе приземления: литерал `IMPERSONATION_REFUSED_LOCATION` (`app/dependencies.py:323`), дефект WR-03 ревизии Фазы 8, не исправленный; правило с изъятием для него закрепило бы дефект"
  - "15-26: форма отказа гарда объявлена литералом `ORIGIN_GUARD_REFUSAL = \"return Response(status_code=403)\"`, снятым со всех 14 мест вызова; её выбрал владелец (D-08 Фазы 11, D-01 Фазы 14), и смена формы — новое решение владельца вместе с литералом"

patterns-established:
  - "Для строки о ГРАНИЦЕ предиката замер идёт двумя путями: правкой самого предиката (держит действующий контроль) и правкой места вызова (приписанное условие, чтение заголовка рядом) — второе требует правила места"

requirements-completed: []

coverage:
  - id: D1
    description: "Строка `10-31#3` записана `enforced` двумя правилами `test_notices_surface.py`, покрасневшими на снятии приклейки внеполосного блока в `respond`"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_notices_surface.py#test_a_fragment_answer_carries_the_notice_out_of_band"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_notices_surface.py#test_a_non_html_fragment_refuses_the_glue_instead_of_corrupting_it"
        status: pass
    human_judgment: false
  - id: D2
    description: "Модуль `test_write_path_invariants.py`: 7 правил и 7 контролей; каждое новое правило покраснело на мутации дерева (10 мутаций), RED-верб `RED_EVIDENCE_OK` на всех десяти; девять строк записаны `enforced`"
    requirement: "критерий-6"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_write_path_invariants.py (13 passed)"
        status: pass
      - kind: other
        ref: "node .claude/gsd-core/bin/gsd-tools.cjs check tdd-red-evidence <запись> → RED_EVIDENCE_OK ×10"
        status: pass
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --check → «реестр: 741 строк, биекция с переписью — согласие»"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/test_pages/ tests/test_templates/ tests/test_planning/ -q -p no:randomly → 2563 passed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Передача `10-18#3` и `10-22#0` чекпойнту 15-32 и верность суждения «правило держит ВЕСЬ предмет формулировки» по десяти записанным строкам"
    verification: []
    human_judgment: true
    rationale: "Замещение `10-22#0` решением D-07 и выбор между правкой литерала и именованным изъятием у `10-18#3` — решения владельца. Выбор синтетического нарушения «ИМЕННО этой формулировки» — суждение исполнителя, полноту перечня способов нарушения машина не выводит (D-33 плана 15-13)"

duration: 73min
completed: 2026-09-25
status: complete
---

# Phase 15 Plan 26: Принуждение двенадцати запретов серверной стороны письма Summary

**Десять из двенадцати запретов `product-invariant` о серверной стороне письма записаны в реестре `enforced`: гард происхождения (место, форма отказа, граница «без обоих заголовков»), cookie сессии, величины порции, негодное поле контекста удаления расписания, внеполосный код исхода. `10-31#3` держат действующие правила. Шесть строк держатся действующим правилом плюс новым, три — только новым. Новые правила собраны в `tests/test_pages/test_write_path_invariants.py` (7 правил, 7 контролей), и каждое покраснело на мутации дерева. `10-22#0` (формулировку заменило решение D-07 Фазы 11) и `10-18#3` (правило по формулировке красно на дереве из-за неисправленного дефекта WR-03 Фазы 8) переданы плану 15-32. `app/` не правился.**

## Performance

- **Duration:** 73 min (из них 35 мин — прогон проверки уровня плана)
- **Started:** 2026-09-25T16:31:55Z
- **Completed:** 2026-09-25T17:45:11Z
- **Tasks:** 2
- **Files modified:** 2 (новый модуль правил, реестр)

## Таблица строк: правило → замер направления → строка отказа → запись

Каждый замер — временная правка файла дерева, прогон, `git checkout -- <файл>`, затем `git diff --exit-code -- app/` пуст. Проверял это драйвер в scratchpad после каждой мутации, и каждый раз было `clean=True`. Команда прогона: `uv run pytest -q -p no:randomly --junit-xml=… <файл>[::<правило>] …`. Мутации m1–m9 проверяли действующие правила, r1–r7 — новые, на тех же мутациях.

| Строка | Правило(а) записи | Мутация дерева | Строка отказа | Запись |
|---|---|---|---|---|
| `10-03#5` собственный `set_cookie` в обработчике входа под пользователем не заводится | **новое** `test_write_path_invariants.py::test_the_session_cookie_is_set_only_by_its_single_setter` | m4: в `admin_impersonate` вызов `set_session_cookie(response, token, settings)` заменён на `response.set_cookie(key="access_token", value=token, path="/", httponly=True, samesite="lax", secure=settings.cookie_secure)` — тот же набор атрибутов | **действующие: `67 passed`** (`test_impersonation.py`, `test_cookie_flags.py`, `test_impersonation_gate.py`); новое (r1) — `FAILED …::test_the_session_cookie_is_set_only_by_its_single_setter`, «app/pages/admin.py:1884 (admin_impersonate): собственный `.set_cookie(` мимо `set_session_cookie`» | задача 2, `enforced` |
| `10-08#2` граница величины не вводится отказом обработчика на негодное поле | `test_confirm_delete_transport.py::test_an_unusable_ad_id_never_reaches_the_database`; **новое** `…::test_an_unusable_context_field_answers_as_an_absent_one_on_both_transports` | m5: после разбора поля в `schedules_delete` — `return Response(status_code=400)`, если поле `ad_id` непусто и отброшено; m5b: то же, только без `HX-Request` | m5: `5 failed` — четыре параметра действующего («…получило ТРЕТЬЮ форму ответа…») и правило адреса; **m5b: `275 passed`** (`test_confirm_delete_transport.py`, `test_htmx_post_pairs.py`, `test_editor_schedules.py`), так как действующее ходит только транспортом htmx; новое на m5b (r6) — «без htmx / ad_id='-1': (400, None, None) вместо (302, '/schedules', None)», на m5 (r6b) — то же на htmx: «(400, None, None) вместо (204, None, '/schedules')» | задача 2, `enforced` |
| `10-12#3` отбрасывание негодного поля контекста не отменяется и не подменяется отказом, само действие не теряется | `test_confirm_delete_transport.py::test_the_landing_screen_is_never_assembled_from_a_rejected_context_field`; **новое** `…::test_an_unusable_context_field_never_costs_the_deletion_itself` | m5 (отказ); m6: удаление в `schedules_delete` пропускается, если поле `ad_id` непусто и отброшено, ответ прежний | m5: действующее `FAILED`; **m6: `190 passed`** (`test_confirm_delete_transport.py`, `test_editor_schedules.py`) — соседний модуль шлёт поле только на несуществующую строку; новое (r7) — «без htmx / ad_id='9999999999999999999999999': строка осталась; …» по всем восьми парам | задача 2, `enforced` |
| `10-18#0` гард не на маршрутах чтения и не на всём `app/pages/` | `test_origin_guard_on_destructive_routes.py::test_the_boundary_of_both_gate_universes_is_declared_by_number`; **новое** `…::test_the_origin_guard_is_called_only_inside_post_route_handlers` | m2c: гард в `profile_post` (ещё один POST); m2: гард в `ads_partial` (`GET /ads/partial`); m2b: промежуточный слой в `create_app`, зовущий гард на каждый POST | m2c: действующее `FAILED`, «ЧИСЛО МЕСТ ВЫЗОВА ГАРДА РАЗОШЛОСЬ С ДЕРЕВОМ — … зовут гард 15 (объявлено 14)»; **m2: `14 passed`, m2b: `13 passed`** (модуль гарда и реестр собственных выходов); новое: r2 — «app/pages/ads.py:223 (ads_partial): гард в обработчике маршрута чтения `ads_partial` (GET)», r2b — «app/main.py:91 (_origin_everywhere): гард вне обработчика маршрута» | задача 2, `enforced` |
| `10-18#1` форма отказа гарда не изобретается заново | `test_htmx_gates.py::test_every_own_response_exit_of_a_converted_handler_is_declared`; **новое** `…::test_every_origin_guard_site_answers_the_refusal_of_the_existing_consumers` | m3: в `accounts_delete` отказ `Response(status_code=400)`; m3c: `Response(status_code=403, content="cross-site request refused")` | m3: действующее `FAILED`, «ВИД СБОРКИ РАЗОШЁЛСЯ С ЗАМЕРОМ: app/pages/accounts.py::accounts_delete объявлен как 'Response(status_code=403)', а измерен как 'Response(status_code=400)'»; **m3c: `14 passed`**: вид сборки учитывает только имя вызова и код; новое (r3) — «ветка отказа `return Response(status_code=403, content='cross-site request refused')` вместо `return Response(status_code=403)`» | задача 2, `enforced` |
| `10-25#3`, `10-32#3` граница «без обоих заголовков пропускается» не пересматривается | `test_origin_guard_on_destructive_routes.py::test_control_a_request_with_neither_header_still_passes`; **новое** `…::test_no_origin_guard_site_re_examines_the_headerless_boundary` | m1: последний `return True` предиката `is_same_origin` → `return False`; m1b: условие места вызова в `accounts_delete` → `not is_same_origin(request) or "origin" not in request.headers` | m1: действующее `FAILED`, «запрос без обоих заголовков отвергнут — сужение ветви источника задело объявленную границу…»; **m1b: `13 passed`** (модуль гарда и реестр собственных выходов; поведенческие правила маршрута на m1b не прогонялись); новое (r4) — «условие отказа не есть ровно `not is_same_origin(<запрос>)`; … заголовок `origin` читается мимо гарда» | задача 2, `enforced` (обе строки) |
| `10-28#1` смещение и размер порции не ограничиваются границей идентификатора | **новое** `…::test_no_pagination_value_is_limited_by_the_identifier_bound` | m8: `ads_partial` — `offset: int = Query(0, ge=0, le=ID_MAX)` | **`test_identifier_bounds.py`: `21 passed`**: изъятие считает число величин порции, а не их границу; новое (r5) — «app/pages/ads.py::ads_partial(offset: int): объявление несёт границу идентификатора» | задача 2, `enforced` |
| `10-29#1` то же в админском модуле | **новое** то же правило | m9: `admin_user_history_partial` — то же плюс ввоз `ID_MAX` | **`21 passed`**; новое (r5b) — «app/pages/admin.py::admin_user_history_partial(offset: int): объявление несёт границу идентификатора» | задача 2, `enforced` |
| `10-31#3` механизм внеполосного кода исхода на фрагментной ветке не удаляется | `test_notices_surface.py::test_a_fragment_answer_carries_the_notice_out_of_band`; `…::test_a_non_html_fragment_refuses_the_glue_instead_of_corrupting_it` | m7: в `respond` `return _glue_notice(response, notice)` → `return response` | `5 failed, 56 passed` (`test_notices_surface.py`, `test_htmx_response_layer.py`): «внеполосного блока с текстом записи в теле нет — исход действия снова невидим тому, кто остался на странице»; «DID NOT RAISE <class 'ValueError'>» | задача 1, `enforced` |
| `10-18#3` сборка адреса приземления без второго экземпляра | — | — | см. «Передано плану 15-32» | **передано 15-32** |
| `10-22#0` граница идентификатора не переносится внутрь обработчиков | — | — | см. «Передано плану 15-32» | **передано 15-32** |

## Передано плану 15-32

**1. `10-22#0` — формулировка замещена.**
- Формулировка: «граница величины идентификатора НЕ переносится внутрь обработчиков: план 10-12 свёл её к ОДНОМУ владельцу на все пять входов, и перенос внутрь пяти обработчиков развёл бы одно правило на пять мест…».
- Чем замещена: решение D-07 Фазы 11 (`11-CONTEXT.md`, «Границы `ge=`/`le=` в аннотациях `Path()`/`Form()` страничных POST-обработчиков переносятся ВНУТРЬ обработчиков»; исполнено планом 11-02). То же записано в самом дереве: `app/pages/identifiers.py`, абзац «ПОКОЛЕНИЕ АБЗАЦА ВЫШЕ … ОПРОВЕРГНУТО решением D-07 Фазы 11, план 11-02: граница там уезжает ВНУТРЬ обработчика (`id_in_column`)».
- Замер (разбор `ast` по `app/`, scratchpad): **18 обработчиков маршрутов зовут `id_in_column`, всего 23 вызова** (`account_groups` ×2 обработчика, `accounts` ×3, `admin` ×6, `ads` ×2, `history` ×1, `schedules` ×4). Правило по формулировке («проверки границы в обработчиках нет») красно на всех 18.
- Уцелевшая половина — один владелец величины и один помощник проверки («помощник … один на проект», D-07). Кандидаты на неё: `test_the_identifier_bound_is_declared_exactly_once_in_the_whole_app` и `test_every_post_identifier_is_checked_before_its_first_use`. Этим планом на мутации они НЕ замерялись, и строка не записана. Решение за владельцем: снять формулировку как замещённую (D-30/D-32) либо переформулировать её в «один владелец величины и помощника».

**2. `10-18#3` — правило по формулировке красно на дереве.**
- Формулировка: «сборка адреса приземления НЕ получает второго экземпляра: параметр кода исхода собирается ОДНИМ местом, и второе место разошлось бы с первым при первой же правке — основание записано докстрингом самой сборки».
- Что нарушено: помимо `_with_notice` (`app/pages/htmx.py`, «ЕДИНСТВЕННАЯ его сборка») параметр кода исхода в адресе приземления набран руками ещё в одном месте: `app/dependencies.py:323` — `IMPERSONATION_REFUSED_LOCATION = "/dashboard?notice=impersonation_forbidden"`. Основание формулировки относится к нему прямо: смена `NOTICE_QUERY_KEY` оставила бы литерал позади.
- Это **дефект, названный ревизией**: `08-REVIEW.md`, WR-03 («код исхода в `IMPERSONATION_REFUSED_LOCATION` — сырой литерал, не проверяемый в рантайме»). Там же предложена правка через `f"/dashboard?{NOTICE_QUERY_KEY}={IMPERSONATION_FORBIDDEN}"`. Правка не внесена: литерал стоит с Фазы 8 и старше плана 10-18.
- Замер (разбор `ast`, scratchpad): мест параметра кода исхода в адресе — **2**: `app/dependencies.py:323 (<уровень модуля>)` и `app/pages/htmx.py:763 (_with_notice)`. Кандидаты планирования (`test_htmx_response_layer.py:457`, `:475`) — поведенческие правила `respond`, и единственности места они не держат.
- Почему не записано: правило строго по формулировке покраснело бы на дереве. Правило с изъятием для литерала закрепило бы дефект WR-03 как норму. Правило, смотрящее только на вычисляемые сборки, держало бы меньше формулировки. Решение за владельцем: (а) правка литерала через `_with_notice` или `NOTICE_QUERY_KEY` (это правка продукта, вне этого плана), после неё правило единственного места; (б) именованное изъятие решением владельца.

## Accomplishments

- Задача 1: направление замерено по всем двенадцати строкам. `10-31#3` записан `enforced` двумя правилами `test_notices_surface.py`. У девяти строк найдена форма нарушения, на которой действующие правила зелены, и эти строки переданы задаче 2. У двух строк замерено основание передачи плану 15-32.
- Задача 2: новый модуль `tests/test_pages/test_write_path_invariants.py` — 7 правил и 7 контролей. Модуль ввозит разборщики `test_identifier_bounds.py` (`_app_sources`, `_catalogue_sources`, `_route_declarations`, `bounded_alias_names`, `catalogue_parameters`, `PAGINATION_EXCLUSION_*`, `FIRST_USE_CHECK_HELPER`), константы гарда из `test_origin_guard_on_destructive_routes.py` (`ORIGIN_GUARD`, `ORIGIN_GUARD_CALL_SITES_MEASURED`, `ADMIN_MODULE`) и перечень негодных величин из `test_confirm_delete_transport.py`. Своих перечней мест, величин и обхода каталога модуль не заводит. Докстринг составлен по форме D-16: предмет с тождествами строк и «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» по каждой строке.
- Реестр: у `product-invariant` было `enforced 21 / partially-enforced 8 / unresolved 41`, стало `31 / 8 / 31`. Сумма по диспозициям области решений — 321, биекция в согласии. Дифф реестра — ровно 10 строк.

## Task Commits

1. **Задача 1: замер направления по действующим правилам** — `dd2482ff` (chore): `10-31#3` записан `enforced`.
2. **Задача 2: новые правила серверной стороны** — `1c60e0e4` (test): модуль правил. `acb7a788` (chore): девять строк записаны `enforced`.

**Plan metadata:** коммит сводки `docs(15-26)`, следом коммит учёта STATE/ROADMAP.

## TDD

План `type: execute` при `workflow.tdd_mode: true`: гейт TDD на таком плане инертен. Продукт по плану не правится, поэтому цикла «красный тест → правка продукта → зелёный» здесь нет. **RED каждой строки измерен так, как требует владелец (Г-1): правило засчитано, только если покраснело на нарушении формулировки своей строки.**

- **Действующие правила:** мутации m1–m9 и m2b, m2c, m3c, m5b (таблица). Каждая отменена `git checkout -- <файл>`, и после каждой `git diff --exit-code -- app/` пуст.
- **Новые правила:** десять прогонов r1–r7 (r2b, r5b, r6b — вторые формы) на тех же мутациях дерева. Цель каждого прогона — только новое правило. Каждый дал `FAILED tests/test_pages/test_write_path_invariants.py::<правило>`, строку `1 failed, 1 warning`, `exit=1`; причинные литералы — в таблице. Прогоны писали `--junit-xml`. Одноразовый скрипт scratchpad (`junit2red.py`, не в дереве) перевёл их в запись `{command, exitCode, targetTest, output}` с выводом в форме node:test TAP. `check tdd-red-evidence` дал `RED_EVIDENCE_OK` (`target_test_failed`) на всех десяти. Первый вызов верба с относительным путём дал `INVALID_RED (unreadable_record)`: верб искал запись от корня проекта. С абсолютным путём все десять — `RED_EVIDENCE_OK`.
- **Контроли на синтетике** (в модуле): у пяти статических правил копия боевого файла с нарушением названа, а боевое дерево — нет. Это `admin.py` с собственным `set_cookie` и с заголовком `Set-Cookie`, записанным руками; `ads.py` с гардом на GET; `main.py` с промежуточным слоем под псевдонимом ввоза; `accounts.py` с 403 с телом; `accounts.py` с приписанным условием и с отдельной проверкой `Sec-Fetch-Site`; `ads.py` и `admin.py` с `le=ID_MAX` у смещения. У двух поведенческих правил контроль подаёт сличителям синтетические наблюдения: отказ 400 на одном транспорте, базовый ответ-отказ 422, оставшаяся строка, несостоявшееся базовое удаление. Все контроли зелены.
- Коммит `test(15-26)` предшествует записям второй задачи. Коммита `feat(15-26)` нет: продукт не правился. REFACTOR не было.

## Files Created/Modified

- `tests/test_pages/test_write_path_invariants.py` — новый модуль правил группы (971 строка).
- `.planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml` — поля меры покрытия у 10 строк, записаны только через `--record`.

## Decisions Made

См. `key-decisions`. Кратко:
- Правило места гарда строже предмета. Оно не принимает гард нигде, кроме тела POST-обработчика маршрута: ни в промежуточном слое, ни в зависимости, ни переданным значением. Сегодня все 14 обращений стоят в POST-обработчиках. Антивакуум сверяет их число с `ORIGIN_GUARD_CALL_SITES_MEASURED`, и второй копии числа нет.
- Правило границы «без обоих заголовков» запрещает читать `Origin`/`Sec-Fetch-Site` где-либо, кроме самого гарда. Пересмотр границы на месте вызова возможен любым условием по этим заголовкам, и приписанное к вердикту условие — лишь одна из форм.
- Поведенческие правила поля контекста не сравнивают ответ с записанными кодами, а сличают его с ответом на тот же запрос без поля. Предмет формулировки — неотличимость по величине поля. Утверждений `status_code == 302` в модуле нет, поэтому счётные гейты страниц не сдвинулись.
- Величина `1_0` из перечня соседнего модуля исключена: коэрция принимает её как 10, это величина в диапазоне колонки, и граница её не касается. Исключение названо в докстринге модуля. Строки этой группы поведения `1_0` не утверждают и не закрепляют.
- Для `10-18#3` правило не написано вовсе. Правило только на вычисляемые сборки держало бы меньше формулировки, а правило с изъятием литерала закрепило бы дефект WR-03 (см. «Передано плану 15-32»).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Шесть строк записаны действующим правилом ВМЕСТЕ с новым**
- **Found during:** задача 1
- **Issue:** у `10-18#0`, `10-18#1`, `10-25#3`, `10-32#3`, `10-08#2`, `10-12#3` действующее правило краснело на прямом нарушении. На второй форме того же нарушения оно было зелено: гард на GET и промежуточным слоем, 403 с телом, приписанное условие, отказ только без htmx, потерянное удаление.
- **Fix:** по протоколу строки при частичном покрытии — новое правило на остаток и запись с обоими правилами.
- **Files modified:** модуль правил, реестр
- **Commit:** `1c60e0e4`, `acb7a788`

**2. [Rule 1 - Bug] Разбор поведенческого правила читал поле истёкшего объекта сессии**
- **Found during:** задача 2, до первого прогона
- **Issue:** после `expire_all()` в проверке «строка осталась» чтение `ad.id` в асинхронной сессии ушло бы в ленивую загрузку и упало бы не по причине правила.
- **Fix:** посев возвращает число, а не объект: `_seed_schedule(db, ad_id) -> int`.
- **Files modified:** `tests/test_pages/test_write_path_invariants.py` (до коммита)
- **Commit:** `1c60e0e4`

**3. [Rule 4 → передача, не отклонение] Две строки не записаны**
- `10-18#3` и `10-22#0` переданы чекпойнту 15-32 шагом 5 протокола строки (раздел выше). Продукт не правился, формулировки не облегчались.

---

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 1 в правиле до коммита); 2 строки переданы чекпойнту по протоколу
**Impact on plan:** записи несут только правила, чей красный замерен. Правка продукта не понадобилась, ни одна формулировка не облегчена.

## Issues Encountered

- Кандидаты планирования для `10-28#1`/`10-29#1` («искать изъятие величин порции в гейте границы») нашлись, но держат они иное. `PAGINATION_EXCLUSION_NAMES` изымает величины порции из вселенной и считает их число. Граница, поставленная смещению, число не двигает (m8, m9: `21 passed`).
- Правило `10-25#3` на m1b прогонялось против модуля гарда и реестра собственных выходов (`13 passed`). Поведенческие правила `accounts_delete`, шлющие запрос без заголовков, на m1b не прогонялись. Отказ по отсутствию заголовка покрасил бы их по следствию, но не по названной причине.
- Проверка уровня плана (`tests/test_pages/` целиком) шла 35 мин.

## Verification

- `uv run pytest tests/test_pages/test_write_path_invariants.py -q -p no:randomly` → `13 passed`.
- `uv run pytest tests/test_pages/test_write_path_invariants.py tests/test_pages/test_htmx_gates.py tests/test_pages/test_htmx_post_pairs.py tests/test_pages/test_hx_location_destinations.py -q -p no:randomly` → `197 passed`.
- Проверка уровня плана: `uv run pytest tests/test_pages/ tests/test_templates/ tests/test_planning/ -q -p no:randomly` → `2563 passed`, `EXIT=0` (2127.88 с). Туда входят все модули, чьи обработчики замерялись: гард, граница идентификатора, транспорт удаления, слой ответа, уведомления, имперсонация, cookie, редактор расписаний, а также гейты пар, переходов и `tests/test_templates/` с парами деградации.
- `<verify>` задачи 1 на исходном дереве (`d73ea5fc`) → `148 passed`. Модули задачи 1 реестр не читают и вошли в прогон уровня плана.
- `uv run pytest tests/test_planning/ -q -p no:randomly` → `140 passed` (после каждой группы записей).
- `uv run python scripts/prohibitions_census.py --check` → «реестр: 741 строк, биекция с переписью — согласие»; `--breakdown` → `product-invariant: enforced 31 (3), partially-enforced 8 (8), unresolved 31 (1)`, «сумма по диспозициям области решений: 321».
- `--list --phase 10 --class product-invariant`: десять строк группы несут `disposition=enforced`, `10-18#3` и `10-22#0` — `unresolved` (переданы 15-32).
- `grep -c 'ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ'` → `1`. `git diff --exit-code -- app/` → пусто, `git diff d73ea5fc..HEAD --name-only -- app/` → 0 файлов.
- Счётные гейты не сдвинулись. В модуле нет утверждений `status_code == 302`, вызовов целей перехода и имён `*_degrades_without_htmx`. `PAIRED_302_ASSERTIONS_DECLARED` 191, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 81, `DEGRADATION_PAIRS_DECLARED` 5, и гейты зелены. Нового `import yaml` нет.
- `graphify update .` выполнен после правки кода.
- **Подмена полного прогона названа:** полную суиту (`just test`, около 40 мин) по указанию оркестратора запускает сам оркестратор после этого плана. Здесь её заменяют каталоги `tests/test_pages/`, `tests/test_templates/` и `tests/test_planning/` целиком. Окна в WINDOWS.md для этого не открыто.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Планы 15-27…15-31 проходят свои группы тем же протоколом. Образец этого плана: для запрета о ГРАНИЦЕ предиката замерять не только правку предиката, но и правку места вызова, а для поведенческой строки — второй транспорт и живую строку вместо несуществующей.
- Остаток `product-invariant`: 8 частичных строк и 31 неразобранная (`enforcement-required`), из них две этого плана переданы 15-32 с замером.
- Требование `критерий-6` не отмечалось, вердикт фазы не выносился.

## Self-Check: PASSED

- FOUND: tests/test_pages/test_write_path_invariants.py, .planning/phases/15-uprochnenie-i-svodnyy-obhod-47-form/15-prohibitions-registry.yaml
- FOUND commits: dd2482ff, 1c60e0e4, acb7a788 (ledger `d73ea5fc..HEAD` = 3 на момент записи сводки)

---
*Phase: 15-uprochnenie-i-svodnyy-obhod-47-form*
*Completed: 2026-09-25*
