---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 48
subsystem: testing
tags: [single-writer-gate, phone, ast, methodcaller, carrier-name-collision, place-count, base-head-diff, foreign-corpora, tdd]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "гейт писателя 16-01…16-45 (на 16-46 / 16-47 не правился); инструмент r9diff 16-46 / 16-47 (копия оркестратора)"
provides:
  - "место записи через получатель `methodcaller` — узел получателя в применении (WR-31): две подачи колонки — две находки; колонка литералом в `methodcaller` — одна"
  - "LITERAL_FORM_PLACES, literal_place_count_mismatch, правило строк по числу мест и правило-контроль test_the_writer_place_count_rule_reddens_a_receiver_write_merged_by_subject; трасер test_a_planted_backfill_with_two_receiver_writes_reddens_the_gate_twice; трасер 16-42 — место 11"
  - "суд каждого толкования вызова у гейта писателя: имя носителя, связанное с пишущим API или с partial над ним, и имя `partial`, связанное с пишущим API, — и псевдоним, и носитель ссылки"
  - "шапка гейта писателя: узел получателя, каждое толкование вызова, абзац цены с `to_thread = setattr`, Летопись WR-31"
  - "инструмент .pytest_cache/r9diff/ (gitignored): семейства (к9) «одно имя — две роли» на оси носителя и (к10) ось счёта у получателя, (к6) и (к7) целиком, ожидание строк из LITERAL_FORM_PLACES, самопроверка 16-48 (29 328 форм), kw_ext_evidence.py, d2_reclass.py, kw_ext_pairs.py, repaired_by.py"
affects: [16-49, 16-50]

actuals:
  tokens: 18200   # chars/4: отслеживаемый дифф 42 128 знаков (≈10 500) + своё в gitignored-инструменте ≈31 000 знаков (≈7 700)
  tasks: 3
  commits: 6      # git rev-list --count 5c7377cc..6d932a97 (до коммита сводки)
plan_head_before: 5c7377cc9d6e124f8ea152b82ac45e9670598719
plan_head_after: 6d932a97ad2863d1aff88a8715a318b9d43218b5

tech-stack:
  added: []
  patterns:
    - "Место находки записи через получатель — узел, где названа колонка: получатель-колонка в применении или литерал `methodcaller`"
    - "Каждое толкование вызова судится; одно место печатается один раз прежней дедупликацией (строка, столбец)"
    - "Корпус сверки растёт своим семейством «одно имя — две роли» и семейством оси счёта до доверия GREEN; самопроверка судится целиком на HEAD и на базе"

key-files:
  created: []
  modified:
    - tests/test_application/test_phone_single_writer_gate.py

key-decisions:
  - "Место варианта применения `methodcaller` — получатель, если `_phone_column(holder)` называет колонку, иначе литерал `methodcaller`; дедупликация не тронута"
  - "Ранний возврат `_referenced_calls` остаётся только у `getattr` (и у `methodcaller`); судимое имя и псевдоним `partial` судятся ещё и как носитель"
  - "Семейство (к6) закрыто целиком (заметка оркестратора 1): применённый `partial(…)(…)` — обёртка носителя и при `partial = setattr` — пятая строка и законный двойник сверх четырёх строк плана"
  - "Расширение цены kw на ось носителя (`kw_ext`) — 156 форм самопроверки, только соперники setattr / set_committed_value / flag_modified × носители to_thread, run_sync, Context.run, to_thread(*[…]); вынесено владельцу и верификатору раунда 10, строкой таблицы не закреплено"

patterns-established:
  - "Таблица числа мест строк писателя (`LITERAL_FORM_PLACES`) — как `NEGATIVE_CONTROL_PLACES` приватности, с правилом-контролем против слияния"
  - "run.sh-обёртка `.pytest_cache/checks/run_rc.sh` пишет код выхода и время рядом с выводом прогона"

requirements-completed: []   # PHONE-02 в requirements плана; отметку Complete не ставим — вердикт фазы gaps_found, учёт ведёт оркестратор (заметка 5)

coverage:
  - id: D1
    description: "WR-31: запись через получатель на узле получателя — три строки по две находки, контроль литерала одна, трасер две находки :11 и :14, трасер 16-42 — место 11; правило строк считает места, контроль ловит слияние; матрица 1 638 по одной"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write (4 строки WR-31) и #test_the_writer_place_count_rule_reddens_a_receiver_write_merged_by_subject"
        status: pass
      - kind: integration
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_backfill_with_two_receiver_writes_reddens_the_gate_twice"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t1_forms.py → OK {…: 2, …: 2, …: 2, …: 1} 1638"
        status: pass
    human_judgment: false
  - id: D2
    description: "Коллизия имени носителя с пишущим API: четыре строки плана и строка `partial`-имени — по одной находке, два законных двойника — ноль; (к6) 3 856 и (к9) 14 503 — ноль неверных"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write (5 строк) и #test_a_legitimate_phone_mention_is_not_a_write (2 строки)"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_rows.py → OK 4; .pytest_cache/checks/kfam_judge.py → k6 / k9 wrong=0"
        status: pass
    human_judgment: false
  - id: D3
    description: "Шапка гейта писателя: узел получателя, каждое толкование вызова, `to_thread = setattr` в окне цены (+277), Летопись WR-31; правило шапки держит эти места"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t3_header.py → OK"
        status: pass
    human_judgment: false
  - id: D4
    description: "Сверка «база ↔ HEAD» r9diff: DIFF по трём GREEN и BASE 0 / 0, HEAD_WRONG=0, OPEN_REGRESSIONS=0, EXTERNAL HEAD defects=0, AGAINST 2f8c1656 0 / 0; самопроверка 29 328 форм — 0 неверных на HEAD, 6 617 на базе"
    verification:
      - kind: other
        ref: "bash .pytest_cache/r9diff/run.sh 16-48 (rc=0, 2026-10-21 14:07–14:08 UTC) и run.sh --against 2f8c1656 (rc=0)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Расширение цены kw на ось носителя (`kw_ext`, 156 форм) — две находки на одном узле колонки при одной записи; принять как цену или чинить"
    verification:
      - kind: other
        ref: "uv run python .pytest_cache/r9diff/kw_ext_evidence.py → EVIDENCE kw_ext: findings=2 sets=1 (×3)"
        status: pass
    human_judgment: true
    rationale: "Пару «соперник под именем носителя и `methodcaller-receiver`» к цене kw отнесло планирование 16-48, а не владелец; принять её как цену или чинить решают владелец и верификатор раунда 10"

duration: 166min
completed: 2026-10-21
status: complete
---

# Phase 16 Plan 48: место записи через получатель `methodcaller` (WR-31), счёт мест таблицы писателя и суд каждого толкования вызова на оси носителя — Summary

**Гейт писателя ставит запись через получатель `methodcaller` на узел получателя в применении. Поэтому `f(MessengerAccount.phone)` дважды — это две находки, а колонка литералом в `methodcaller` по-прежнему даёт одну. Правило таблицы писателя считает места по `LITERAL_FORM_PLACES`, контроль ловит слияние находок по «вид, предмет». Вызов, чьё последнее имя связано в модуле с пишущим API (`to_thread = setattr`), с `partial` над ним, или имя `partial`, связанное с пишущим API, судится и как носитель поданной ссылки. Так закрыто всё семейство (к6). Чужие корпуса без дефектов вне названных цен: `defects` 126 → 0, `HEAD_WRONG` 2 007 → 0. Регрессий нет ни по одной оси: ни против родителей, ни против базы, ни против `2f8c1656`.**

## Performance

- **Duration:** ~166 мин
- **Started:** 2026-10-21T11:51:03Z
- **Completed:** 2026-10-21T14:37Z (до коммита сводки)
- **Tasks:** 3 (у каждой RED и GREEN; циклов самопроверки и дифференциальной регрессии не понадобилось)
- **Files modified:** 1 отслеживаемый (`tests/test_application/test_phone_single_writer_gate.py`, +400 / −27)

## Accomplishments

- **WR-31.** Вариант применения `methodcaller` стоит на получателе, если `_phone_column(holder)` называет колонку, иначе на литерале `methodcaller`. Три формы ревью (две строки, одна строка, блок `go` / `go2`) дают по две находки, контроль литерала — одну.
- **Подложенный скрипт.** `scripts/backfill_receiver_twice.py` даёт ровно две находки: `:11` и `:14`.
- **Трасер 16-42.** Его закрепка сменена по плану: 8 → 11, с летописью в докстринге.
- **Правило строк** сверяет число находок с `LITERAL_FORM_PLACES`. Правило-контроль доказывает, что слияние по «вид, предмет» его краснит.
- **Свойство 2 О-20 на оси носителя.** Ранний возврат `_referenced_calls` остался только у `getattr` (и у `methodcaller`). Применённый `partial(…)(…)` — обёртка носителя и при `partial = setattr`. Четыре строки плана и пятая (`partial`-имя) дают по одной находке, два законных двойника — ноль.
- **Шапка.** Названы узел получателя и каждое толкование вызова. В абзаце цены стоит `to_thread = setattr` (+277 в окне 600). Записана Летопись WR-31.
- **Инструмент r9diff вырос.** Добавлены семейства (к9) и (к10), (к6) и (к7) взяты целиком, ожидание строк таблицы берётся из `LITERAL_FORM_PLACES`. Самопроверка 16-48 — 29 328 форм. Добавлены улика `kw_ext` и разборы D2 / `REPAIRED`.

## Task Commits

1. **Задача 1 (трасер): RED** — `3b0d912f` (test)
2. **Задача 1: GREEN** — `36248d38` (feat)
3. **Задача 2: RED** — `4a192880` (test)
4. **Задача 2: GREEN** — `533eb042` (feat)
5. **Задача 3: RED** — `709e25d2` (test)
6. **Задача 3: GREEN** — `6d932a97` (feat)

**Plan metadata:** коммит этой сводки (`docs(16-48)`).

## TDD: RED и GREEN

**RED задачи 1** (`3b0d912f`). Прогон: `uv run pytest tests/test_application/test_phone_single_writer_gate.py -q -p no:randomly -k "two_receiver_writes or applied-twice or two-methods or place_count_rule or read_by_a_getattr_string_reddens" --junit-xml=.pytest_cache/gsd-red/16-48-t1.xml`, 12:00:46Z.
- Строка `FAILED tests/test_application/test_phone_single_writer_gate.py::test_a_planted_backfill_with_two_receiver_writes_reddens_the_gate_twice` есть.
- Последняя строка сводки: `6 failed, 1 passed, 597 deselected, 1 warning in 1.26s`. Упали трасер, три строки WR-31, правило-контроль и трасер 16-42.
- Причинный литерал «две подачи колонки через получатель `methodcaller` в двух методах — не две находки на строках применений» в выводе есть (2 вхождения). Фактический выход: `['scripts/backfill_receiver_twice.py:8 — запись атрибута по имени — MessengerAccount.phone.__set__(…)']`.
- `gsd check tdd-red-evidence .pytest_cache/gsd-red/16-48-t1.json` → `RED_EVIDENCE_OK` (`target_test_failed`; tests 7, fail 6, pass 1).
- Смысловая оценка: цель исполнилась и упала на утверждении о списке находок. Строки WR-31 упали на «мест 2, находок 1». Ошибок сбора, ввоза и фикстур нет.
- Закрепка, зелёная до GREEN: `methodcaller-literal-column-applied-twice`.
- Полный модуль писателя с паритетом на RED: `6 failed, 620 passed`.

**GREEN задачи 1** (`36248d38`): место варианта применения в `_phone_writes`.

**RED задачи 2** (`4a192880`). Прогон: `… -k "carries-a-writer" --junit-xml=.pytest_cache/gsd-red/16-48-t2.xml`, 12:36:18Z.
- Четыре строки `FAILED …::test_a_literal_write_form_is_a_write[carrier-name-bound-to-setattr-carries-a-writer-reference]` и ещё три.
- Последняя строка: `4 failed, 607 deselected, 1 warning in 1.00s`.
- Литерал сообщения правила строк задачи 1 «число находок не равно числу мест» есть (8 вхождений): «мест 1, находок 0».
- `RED_EVIDENCE_OK`.
- Строка сверх плана `partial-name-bound-to-setattr-wraps-a-writer-reference` проверена отдельным прогоном `… -k "partial-name-bound or carries-a-status or wraps-a-status" --junit-xml=.pytest_cache/gsd-red/16-48-t2b.xml` (12:36:28Z): `1 failed, 2 passed, 608 deselected`, `RED_EVIDENCE_OK`. Два законных двойника — закрепки.
- Полный модуль писателя с паритетом на RED: `5 failed, 628 passed`.

**GREEN задачи 2** (`533eb042`): ранние возвраты `_referenced_calls` и условие применения судимого вызова в `carried_writes` (`partial_names`).

**RED задачи 3** (`709e25d2`). Прогон: `… -k test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier --junit-xml=.pytest_cache/gsd-red/16-48-t3.xml`, 13:18:48Z.
- Строка `FAILED …::test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier` есть.
- Последняя строка: `1 failed, 610 deselected, 1 warning in 0.71s`.
- Литерал «шапка гейта писателя не называет общую грамматику связывания» есть (2 вхождения; в дереве до задачи `grep -c` = 1). Недостающих мест 5.
- `RED_EVIDENCE_OK`.

**GREEN задачи 3** (`6d932a97`): тексты шапки. «`to_thread = setattr`» стоит на +277 от «Цена — в сторону лишней находки» — ровно замер планирования.

## TDD Gate Compliance

В каждой задаче `test(16-48)` стоит перед своим `feat(16-48)`: `3b0d912f` → `36248d38`, `4a192880` → `533eb042`, `709e25d2` → `6d932a97`. `refactor` нет. Нарушений нет.

## Самопроверка исполнителя — композиция двух осей (задача 3; О-20 (а), свойства 2, 5, 8; О-21 (а), свойство 4)

Генератор — `.pytest_cache/r9diff/selfcheck_1648.py` (gitignored). Ячейки — `sc1648_cells.json`, sha256 `e4e30c3f203366941c7d0bf02b6767bc1a0af384fdda919c5b2a0c8a32fe321a`; это теперь `selfcheck_cells.json`. Суд — `judge.py` в отдельном процессе под общим `flock`. Прогон 2026-10-21 13:13–13:17 UTC; код предикатов — GREEN задачи 2 `533eb042` (GREEN задачи 3 предикатов не трогал); база — `5c7377cc`.

**Часть DW — ось счёта у записи через получатель:**
- значения: получатель-колонка `operator.methodcaller("__set__", account, x)` к `MessengerAccount.phone`, колонка литералом `operator.methodcaller("set_committed_value", account, "phone", x)` к `attributes`, два безопасных двойника `status`;
- 12 форм `BINDING_FORMS` (без `direct`);
- чтение: как в форме, getattr-строкой, getattr-строкой с умолчанием, цепочкой `g = <ссылка>`, через объект модуля `sys.modules[__name__].f` — у имени уровня модуля;
- раскладка двух применений: две строки, одна строка, два метода, прямо и подачей каждому из 20 носителей, две подачи одному носителю.

Ожидание — число узлов колонки: 2 у получателя-колонки, 1 у литерала, 0 у двойника.

**Часть WC — ось толкований вызова:**
- пишущий API под последним именем носителя: `setattr`, `update`, `set_committed_value`, `flag_modified`, `functools.partial(setattr, other)`;
- каждый носитель `REFERENCE_CARRIERS` и каждое последнее имя его шаблона;
- каждое значение `API_IDENTIFICATION_VALUES`;
- 13 форм `BINDING_FORMS`;
- колонка или двойник `status`.

Ожидание — 1 (0 у двойника). У пары «соперник `setattr` / `set_committed_value` / `flag_modified` и `methodcaller-receiver`» число цены — 2 (`kw_ext`, ниже). У `update` и `partial(setattr, other)` цены нет, ожидание строгое.

**Итого 29 328 форм** (≥ 10 000): DW 7 748, WC 21 580. Полный крест — **30 488**: DW 8 648, WC 21 840. Повторов исходника отброшено 1 160.

| Дерево | Форм | Неверных | `kw_ext` | Число находок (ожидание → найдено) |
|--------|------|----------|----------|-------------------------------------|
| HEAD `533eb042` | 29 328 | **0** | 156 | DW: 0→0 3 874, 1→1 1 937, 2→2 1 937; WC: 0→0 10 790, 1→1 10 634, 1→2 156 (цена) |
| контроль против вакуума: база `5c7377cc` | 29 328 | **6 617** | 156 | DW: 2→1 1 937 (WR-31); WC: 1→0 4 680 (коллизия имени носителя: `update` 1 040, `setattr` / `set_committed_value` / `flag_modified` по 988, `partial(setattr, other)` 676; имя `partial` 1 456 из них) |

**Найдено:** ничего, циклов самопроверки нет. Выборка 3 000 из 29 328 (seed 48) вошла в корпус сверки источником (е) `f-self-check`. Самопроверка 16-47 стала семейством `f-self-1647` — та же выборка 3 000 из 12 444, seed 47.

Свои семейства целиком на итоговом HEAD (`kfam_judge.py`, деревом `6d932a97`, 14:27Z):
- (к6) 3 856 — неверных 0, `kw_ext` 24;
- (к7) 3 480 — неверных 0;
- (к9) 14 503 — неверных 0, `kw_ext` 96;
- (к10) 756 — неверных 0.

На базе неверны: (к6) 804, (к9) 3 628, (к10) 240.

## Расширение цены `COST-KW` на ось носителя — не решение владельца

- **Что названо ценой.** Свойство 8 О-20 сделало названной ценой ТОЛЬКО пару «`functools.partial(setattr, other)` и `operator.methodcaller("__set__", …)` под одним именем». Это семейство `kw` верификатора: 280 чужих ячеек `x-v9::kw::*:partial-setattr:*:receiver` и одна ручная `x-v9h::x::KW-partial-setattr-dual`, в строке `COST kw=281`.
- **Что отнесло планирование.** Пару «пишущий API под последним именем носителя и `methodcaller-receiver`» к той же цене отнесло планирование 16-48. Довод — одинаковая механика: имя, связанное с пишущим API, судится и по последнему звену вызова. Свои ячейки этой пары инструмент считает отдельным числом `kw_ext`, а не `kw`. В `HEAD_WRONG`, `defects`, регрессии и `REPAIRED` они не входят.
- **Число ячеек.** В корпусе — строка `COST-OWN kw=203 attr=480 kw_ext=64`: (к6) 24, (к9) 26, `f-self-check` 14. В самопроверке целиком — **156 форм**; в (к6) целиком — 24, в (к9) целиком — 96. Пары «соперник × носитель» самопроверки, по 13 форм `BINDING_FORMS` у каждой:

  | Соперник под именем носителя | `to_thread` (`asyncio.to_thread`) | `run_sync` | `run` (`Context.run`) | `to_thread(*[…])` | Итого |
  |------------------------------|-----------------------------------|------------|-----------------------|-------------------|-------|
  | `setattr` | 13 | 13 | 13 | 13 | 52 |
  | `set_committed_value` | 13 | 13 | 13 | 13 | 52 |
  | `flag_modified` | 13 | 13 | 13 | 13 | 52 |

  Соперники `update` и `functools.partial(setattr, other)` пары не дают: у них одна находка, ожидание строгое. Носители с ссылкой не первым аргументом (`run_in_executor`, `Thread`, `Timer`, `enqueue`, `starmap`, `apply_async`, `map`, обёртки) пары тоже не дают: колонка не попадает на место имени атрибута у прочтения вызова как API.
- **Пример с двумя находками** (HEAD `6d932a97`, путь `scripts/x.py`), дословно:

  ```python
  import asyncio, contextvars, functools, operator
  from app.models.messenger_account import MessengerAccount
  from sqlalchemy.orm.attributes import set_committed_value
  f = operator.methodcaller("__set__", account, x)
  to_thread = setattr
  asyncio.to_thread(f, MessengerAccount.phone)
  ```

  Находки:
  - `scripts/x.py:6 — запись атрибута по имени — setattr(…, MessengerAccount.phone, …)`
  - `scripts/x.py:6 — запись атрибута по имени — MessengerAccount.phone.__set__(…)`

  На базе `5c7377cc` у той же ячейки тоже две находки, но на разных строках: `:4` (строка связывания) и `:6`. Число находок у этих 156 форм не изменилось (2 и на базе, и на HEAD), на один узел колонки они встали только с GREEN задачи 1.
- **Улика исполнения** (`.pytest_cache/r9diff/kw_ext_evidence.py`, по образцу `cost_evidence.py`). Ячейка исполняется с настоящей моделью `MessengerAccount`: объект транзиентный, без базы и без `.env`. События `set` колонки `phone` считает слушатель SQLAlchemy:

  ```
  EVIDENCE kw_ext: api=setattr findings=2 sets=1 phone='+79991234567'
  CONTROL kw_ext: api=setattr unapplied findings=0 sets=0
  EVIDENCE kw_ext: api=set_committed_value findings=2 sets=1 phone='+79991234567'
  CONTROL kw_ext: api=set_committed_value unapplied findings=0 sets=0
  EVIDENCE kw_ext: api=flag_modified findings=2 sets=1 phone='+79991234567'
  CONTROL kw_ext: api=flag_modified unapplied findings=0 sets=0
  CONTROL kw_ext: plain (без связывания имени носителя) findings=1 sets=1 phone='+79991234567'
  ```

  Запись одна, находок две. Контроль против вакуума слушателя: `methodcaller` без применения даёт ноль событий. Форма без связывания имени носителя даёт одну находку и одну запись.
- **Вынесено владельцу и верификатору раунда 10: принять как цену или чинить.** Строкой таблицы пара не закреплена. Шапка называет механику и то, что расширение вынесено этой сводкой.

## Сверка «база ↔ HEAD» (r9diff; пункт 10 договора `16-46-PLAN.md` `<scope_note>`; свойство 7 О-21 (а))

### Чужие входы

Копия оркестратора: `cp -a` трёх каталогов в `.pytest_cache/` (пути на удалённый worktree — только в старых журналах и отчётах, не в скриптах). `sha256sum -c --quiet MANIFEST.sha256` — 62 файла, совпадение (`INPUTS_OK files=62` в каждом прогоне). Корпуса — те же, что у 16-46 / 16-47:

| Файл | Байт | sha256 | Ячеек |
|------|------|--------|-------|
| `verify-r9/corpus.json` | 9 880 738 | `5c6c4527733eef1541fe88f144c1a4fd97e74907cfb401b32c8c32fba6acb7f5` | 20 769 |
| `verify-r9/hand.json` | 13 135 | `9812cb4780a8201c1abb6774ccf652e4d6a2e1e625f165078261600edb7afd69` | 39 |
| `review-r8/corpusK.json` | 2 639 220 | `2ee9e5f2998a3606527efaaf2c80197c631af9e0d058e3afbae843c13a08481b` | 6 600 |
| `review-r8/corpusKC.json` | 654 066 | `5ae59c54cfc0ca5058e3d45c634828397b6da9202860b073a05f4ed7b8c249f7` | 2 106 |
| `review-r8/hand.json` | 37 454 | `b1e6dc9f04c8d80581999488373437405dcf1db0fe28a94d5b6180cea0a8a0a4` | 115 |
| `review-r8/rows.json` | 98 393 | `761690482879a829f2a4da9f8ec8bfbb6402645f0b5909f647b53f428b47766e` | 312 |
| итого | | | **29 941** |

### Корпус итогового прогона

HEAD `6d932a97`, **130 352 ячейки**, `corpus.json` sha256 `f22ae9918d489b9d723292d21785a8318ca9e80f9b0e52d288a10bd23c7a545c`. Корпус вырос до доверия первому GREEN (заметка оркестратора 8): с первого `--precommit` — 127 345 ячеек (`7fe67b52…`), с RED задачи 2 — 127 352 (`d75bf0a5…`), с самопроверки — 130 352.

| Источник | Состав | Ячеек |
|----------|--------|-------|
| (а) строки таблиц | `LITERAL_FORM_CASES` 268 (ожидание — `LITERAL_FORM_PLACES`: три строки WR-31 по 2), `LEGITIMATE_CASES` 107, `NEGATIVE_CONTROLS` 173, `POSITIVE_CONTROLS` 61 | 609 |
| (б) матрица | `b-matrix` | 3 276 |
| (в) формы ревью | | 106 |
| (г) дифференциал раунда 7 | | 700 |
| (д) выборка самопроверок | 15 семейств по 2 000 (seed 42) | 30 000 |
| (ж) две подачи на одной строке | `g-double` | 3 276 |
| (з) безопасные двойники | `h-safe` | 6 552 |
| (е) `f-self-1644` | 20 000 из 66 690 | 20 000 |
| (е) `f-self-1646` | 6 000 из 84 750 | 6 000 |
| (е) `f-self-1647` (новое имя) | самопроверка 16-47: 3 000 из 12 444 (seed 47) — прежний `f-self-check` корпуса `e466e09e…` | 3 000 |
| (е) `f-self-check` | самопроверка 16-48: 3 000 из 29 328 (seed 48) | 3 000 |
| (и) чужие корпуса | шесть файлов целиком | 29 941 |
| (к1)…(к5), (к8) | как у 16-47: 3 000, 1 590, 600, 2 050, 3 000, 1 560 | 11 800 |
| (к6) | **целиком** (у 16-46 / 16-47 — 3 000 из 3 856) | 3 856 |
| (к7) | **целиком** (у 16-46 / 16-47 — 3 000 из 3 480) | 3 480 |
| **(к9) «одно имя — две роли» на оси носителя** (новое) | последнее имя вызова носителя связано с пишущим API (`setattr`, `update`, `set_committed_value`, `flag_modified`, `functools.partial(setattr, other)`) в четырёх местах (модуль, функция, тело класса, `self.<N> =` в чужом `__init__`) и в том же модуле: (а) носитель поданной ссылки — значение опознания × форма (`assign`, `getattr-read`) × колонка / двойник `status`; (б) законная роль — обычный метод чужого объекта `holder.<N>(1, 2)`, ноль; (в) ось счёта — две подачи на двух строках и на одной (2), API под тем же именем, поданный носителю `<N>` (одно место — 1); 4 000 из 14 503 (seed 46) | 4 000 |
| **(к10) ось счёта у получателя** (новое) | значение (получатель-колонка, колонка литералом, безопасный двойник) × форма `BINDING_FORMS` × раскладка: прямое применение и подача каждому носителю (2), три прямых применения (3), связанное имя под вторым именем, применённое один раз (1) — целиком | 756 |

**Не прогнано выборкой:**
- (д) — 11 119 725 форм полного перебора генераторов;
- `f-self-1644` — 46 690;
- `f-self-1646` — 78 750;
- `f-self-1647` — 9 444;
- `f-self-check` — 26 328 (самопроверка 16-48 прогнана целиком: 29 328 на HEAD и на базе);
- (к1) 6 000, (к5) 6 000;
- (к9) 10 503 (прогнано целиком отдельно — `kfam_judge.py`: 0 неверных на HEAD).

Строки таблиц, матрица, формы ревью, дифференциал, (ж), (з), чужие корпуса, (к2), (к3), (к4), (к6), (к7), (к8), (к10) — целиком.

### Строки итогового прогона

`bash .pytest_cache/r9diff/run.sh 16-48` под общим `flock`, HEAD `6d932a97`, 2026-10-21 14:05:43–14:06:53 UTC. Повтор через обёртку с кодом выхода — 14:07–14:08:20, **rc=0**, строки дословно те же. Вердикты взяты из кеша: тот же код судился в `--precommit` 13:24–14:05. Дословно, без строк `EXTERNAL-CELLS` и `CORPUS` (stderr):

```
INPUTS_OK files=62
CORPUS_SHA256=f22ae9918d489b9d723292d21785a8318ca9e80f9b0e52d288a10bd23c7a545c HEAD=6d932a97ad2863d1aff88a8715a318b9d43218b5
SELFTEST 1bebbbf7 -> c6953017: cells=3382 regressions=48 count_regressions=48 fixed=208 repaired_overcount=0 changed=256
SELFTEST 5e32c335 -> 147f5e46: cells=3382 regressions=56 count_regressions=56 fixed=193 repaired_overcount=0 changed=250
SELFTEST-COUNT a6c87597 -> 51d0d766: cells=3616 regressions=831 count_regressions=885 fixed=378 repaired_overcount=354 changed=1317
SELFTEST-CR04 e1d6587e -> a77263ad: cells=18221 regressions=1510 count_regressions=1510 fixed=0 repaired_overcount=0 changed=1510
REPRODUCE fb8fef72 K: cells=6600 mismatch=0
REPRODUCE fb8fef72 KC: cells=2106 mismatch=0
REPRODUCE e1d6587e K: cells=6600 mismatch=0
REPRODUCE e1d6587e KC: cells=2106 mismatch=0
REPRODUCE a77263ad K: cells=6600 mismatch=0
REPRODUCE a77263ad KC: cells=2106 mismatch=0
REPRODUCE 1c243203 K: cells=6600 mismatch=0
REPRODUCE dbc73537 K: cells=6600 mismatch=0
REPRODUCE dbc73537 KC: cells=2106 mismatch=0
DIFF 3b0d912f -> 36248d38: cells=130352 regressions=0 count_regressions=0 fixed=1888 repaired_overcount=0 changed=6396
DIFF 4a192880 -> 533eb042: cells=130352 regressions=0 count_regressions=0 fixed=2319 repaired_overcount=0 changed=2319
DIFF 709e25d2 -> 6d932a97: cells=130352 regressions=0 count_regressions=0 fixed=0 repaired_overcount=0 changed=0
BASE 5c7377cc -> HEAD 6d932a97: cells=130352 regressions=0 count_regressions=0 fixed=4207 repaired_overcount=0 changed=8715
EXTERNAL 5c7377cc: cells=29941 wrong=529 cost_kw=281 cost_attr=122 defects=126
EXTERNAL HEAD 6d932a97: cells=29941 wrong=403 cost_kw=281 cost_attr=122 defects=0
COST kw=281 attr=122
COST-OWN kw=203 attr=480 kw_ext=64
COST-ATTR-IDS n=122 sha256=deaa985492817b71e9c917fa4b79205c3e41de1c9da97d117fcdba0cb000b3da
EVIDENCE attr: file='+79991234567' log='' cell=class-body/print
EVIDENCE attr: file='+79991234567' log='' cell=class-body/logger.info
EVIDENCE attr: file='+79991234567' log='' cell=class-body/getattr-info
EVIDENCE attr: file='+79991234567' log='' cell=class-body/partial
EVIDENCE attr: file='+79991234567' log='' cell=class-body/logging.info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/print
EVIDENCE attr: file='+79991234567' log='' cell=other-init/logger.info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/getattr-info
EVIDENCE attr: file='+79991234567' log='' cell=other-init/partial
EVIDENCE attr: file='+79991234567' log='' cell=other-init/logging.info
HEAD_WRONG=0
OPEN_REGRESSIONS=0
```

- `SELFTEST` 48 / 56, `SELFTEST-COUNT` 885 и `SELFTEST-CR04` 1 510 — те же, что у 16-46 / 16-47.
- `REPRODUCE` — расхождений 0 во всех девяти строках.
- `fixed` по семействам:
  - `DIFF` задачи 1: `a-literal` 3, `f-self-1644` 493, `f-self-check` 194, `g-double` 252, (к10) 240, (к7) 580, `x-r8-X` 3, `x-v9-dw` 120, `x-v9-x` 3 — всего 1 888;
  - `DIFF` задачи 2: `a-literal` 5, `f-self-check` 481, (к6) 804, (к9) 1 029 — всего 2 319;
  - `DIFF` задачи 3 — `changed=0`: шапка предикатов не трогала;
  - `BASE` — сумма двух, 4 207.

**Чужие ячейки, расходящиеся с ожиданием** (обе оси):

| Ревизия | wrong | цена `kw` | цена `attr` | defects | по семействам |
|---------|-------|-----------|-------------|---------|---------------|
| база плана `5c7377cc` = родитель первого GREEN по коду | 529 | 281 | 122 | 126 | `x-v9-fp` 120, `x-v9-kw` 280, `x-v9-dw` 120, `x-r8-X` 4, `x-v9-x` 5 |
| GREEN задачи 1 `36248d38`, GREEN задачи 2 `533eb042`, GREEN задачи 3 `6d932a97` = HEAD | **403** | 281 | 122 | **0** | `x-v9-fp` 120 (цена `attr`), `x-v9-kw` 280 (цена `kw`), `x-r8-X` 1 и `x-v9-x` 2 (ручные формы цен `F1-base-shape`, `WR29-class-body-base-shape`, `KW-partial-setattr-dual`) |

Все 126 чужих дефектов базы — класс WR-31 (`x-v9-dw` 120, ручные `x-v9h::x::WR31-*` 3, `x-r8h::WR28-W-block`, `TW4`, `TW5`). Их исправил GREEN задачи 1. Коллизия имени носителя в чужих корпусах не встречалась, она есть только в своих (к6), (к9) и в самопроверке.

**`HEAD_WRONG` по адресатам:**
- на HEAD — **0**: `UNASSIGNED` нет, ни одной ячейки ни одного адресата;
- до плана (`run.sh 16-47` на базе) — 2 007: WR-31 1 358, (к6) 649;
- на базе под итоговым корпусом — 4 207, все этого плана:
  - WR-31: чужие 126, D2 745, (к7) 580, (к10) 240, строки таблицы 3, самопроверка DW 194;
  - коллизия имени носителя: (к6) 804, (к9) 1 029, строки таблицы 5, самопроверка WC 481.

**Регрессировавшие ячейки и закрывшие их коммиты:** нет. Ни один GREEN не дал регрессии ни по наличию, ни по числу; строк `REGRESSED` и `COUNT_REGRESSED` в `DIFF` и `BASE` нет. **`REPAIRED` в `DIFF` / `BASE` — 0**: план только добавлял находки.

### Прогоны «против»

`run.sh --against <ревизия>` под общим `flock` (обёртка `.pytest_cache/checks/run_against.sh`), HEAD `6d932a97`, корпус `f22ae991…`. В каждом `INPUTS_OK files=62`, четыре строки самопроверки — как выше, девять `REPRODUCE` с `mismatch=0`.

```
AGAINST 2f8c1656 -> HEAD 6d932a97: cells=130352 regressions=0 count_regressions=0 fixed=55122 repaired_overcount=1289 changed=49916
EXTERNAL 2f8c1656: cells=29941 wrong=14932 cost_kw=162 cost_attr=122 defects=14648
EXTERNAL HEAD 6d932a97: cells=29941 wrong=403 cost_kw=281 cost_attr=122 defects=0
AGAINST fb8fef72 -> HEAD 6d932a97: cells=130352 regressions=0 count_regressions=0 fixed=25178 repaired_overcount=67 changed=25458
EXTERNAL fb8fef72: cells=29941 wrong=5958 cost_kw=231 cost_attr=122 defects=5605
EXTERNAL HEAD 6d932a97: cells=29941 wrong=403 cost_kw=281 cost_attr=122 defects=0
AGAINST 1c243203 -> HEAD 6d932a97: cells=130352 regressions=0 count_regressions=1 fixed=35270 repaired_overcount=1442 changed=33351
EXTERNAL 1c243203: cells=29941 wrong=7944 cost_kw=231 cost_attr=122 defects=7591
EXTERNAL HEAD 6d932a97: cells=29941 wrong=403 cost_kw=281 cost_attr=122 defects=0
```

- **`2f8c1656`** — rc=0, 14:12:56Z, ноль по обеим осям. `REPAIRED` 1 289:
  - по гейтам: писатель 773, приватность 516;
  - по сдвигу: 1 278 — 2→1, 9 — 3→1, 2 — 1→0;
  - по семействам: (к7) 378, `f-self-1644` 274, `g-double` 252, `x-v9-dw` 90, `x-v9-dp` 70, `f-self-check` 58, `e-self-1642` 47, (к10) 99, `e-self-1641` 8, по 1–3 — прочие;
  - классы — прежние классы 16-44: одно место повторено (WR-24) и одна запись, судимая дважды (класс 16-42); 1→0 — законная строка `raw-sql-where-between-two-double-quoted-spans-is-a-filter` и `a-legitimate`.
- **`fb8fef72`** — rc=0, 14:19:15Z, ноль по обеим осям. `REPAIRED` 67, все у писателя: класс 16-42 — `e-self-1642` 60, `a-literal` 2, `c-review` 3, `x-v9-a` 2.
- **`1c243203`** — rc=1, 14:24:26Z: `count_regressions=1` — `x-r8h::T11c 4 -> 2`. Это не регрессия этого плана (отступление 5). `REPAIRED` 1 442: приватность 1 377, писатель 65.

### Переклассификация `REPAIRED` D2 против `2f8c1656`

Ячейки D2 писателя со значением `methodcaller-receiver` в корпусе — **745**: (ж) `g-double` 252 и (е) `f-self-1644` 493. Ожидание у всех — 2, число узлов колонки (пункт 6 договора). Разбор — `.pytest_cache/r9diff/d2_reclass.py`:

| Дерево | Находок у 745 ячеек | Верно | Класс группы против HEAD |
|--------|---------------------|-------|--------------------------|
| `fb8fef72` | 0 — 261, 1 — 484 | 0 | исправлены: 261 (0 → 2), 484 (1 → 2) |
| `1c243203` | 0 — 329, 1 — 416 | 0 | исправлены: 329 (0 → 2), 416 (1 → 2) |
| `2f8c1656` | 0 — 555, 2 — 190 | 190 | 190 — **не `REPAIRED`**, прежнее число (2 → 2); 555 — исправлены (0 → 2) |
| база `5c7377cc` | 1 — 745 | 0 | исправлены (1 → 2) |
| HEAD `6d932a97` | 2 — 745 | 745 | — |

- 190 ячеек с двумя находками на `2f8c1656` — ровно 190 ревьюера (16-REVIEW, WR-31). У 16-44 они стояли в `REPAIRED` против `2f8c1656`, теперь — нет.
- Ни одна ячейка D2 писателя `methodcaller-receiver` не стоит в `REPAIRED` ни против `2f8c1656`, ни против `1c243203`. Разбор `repaired_mr.py`: у писателя 0, а 139 и 361 ячеек с `methodcaller-receiver` в id — D2 **гейта приватности**. Там номер стоит в самом `methodcaller`, одно место, `exact 1` — прежняя починка WR-24 плана 16-44.
- Ожидание чужих корпусов не правилось. Изменены только свои ожидания: строки таблицы писателя по `LITERAL_FORM_PLACES` и новые семейства.

### Прогоны

| Прогон | HEAD / цель | Время (UTC) | Корпус | Строки | Выход |
|--------|-------------|-------------|--------|--------|-------|
| воспроизведение до правок: `run.sh 16-47` на базе | `5c7377cc` | 11:51–11:52 | 121 249, `e466e09e…` | ровно строки 16-47: `SELFTEST` 48 / 56, `SELFTEST-COUNT` 885, `SELFTEST-CR04` 1 510, `REPRODUCE` 0, `EXTERNAL HEAD … defects=126`, `COST kw=281 attr=122`, `HEAD_WRONG=2007`, `OPEN_REGRESSIONS=0` | 0 |
| `--precommit` до GREEN задачи 1 (корпус вырос: (к9), (к10), (к6) и (к7) целиком, строки по `LITERAL_FORM_PLACES`) | `3b0d912f` → WORKTREE | 12:12–12:33 | 127 345, `7fe67b52…` | `DIFF`, `BASE` 0 / 0, `fixed=1694`; `EXTERNAL WORKTREE … defects=0`; `HEAD_WRONG=1833` (к6 804, к9 1 029 — задача 2); `OPEN_REGRESSIONS=0` | 0 |
| `run.sh 16-48` после GREEN задачи 1 | `36248d38` | 12:34–12:35 | `7fe67b52…` | то же; `COST-OWN … kw_ext=50` | 0 |
| `--precommit` до GREEN задачи 2 | `4a192880` → WORKTREE | 12:44–13:12 | 127 352, `d75bf0a5…` | `DIFF` ×2, `BASE` 0 / 0; `HEAD_WRONG=0`; `OPEN_REGRESSIONS=0` | 0 |
| `run.sh 16-48` после GREEN задачи 2 | `533eb042` | 13:12–13:13 | `d75bf0a5…` | то же | 0 |
| `--precommit` до GREEN задачи 3 (корпус вырос: самопроверка 16-48, `f-self-1647`) | `709e25d2` → WORKTREE | 13:24–14:05 | 130 352, `f22ae991…` | `DIFF` ×3, `BASE` 0 / 0; `HEAD_WRONG=0`; `kw_ext=64`; `OPEN_REGRESSIONS=0` | 0 |
| `run.sh 16-48` итоговый (и повтор с кодом выхода) | `6d932a97` | 14:05–14:08 | `f22ae991…` | строки выше | 0 |
| `run.sh --against 2f8c1656` / `fb8fef72` / `1c243203` | `6d932a97` | 14:08–14:24 | `f22ae991…` | строки выше | 0 / 0 / 1 (отступление 5) |

Инструмент оставлен на месте:
- `.pytest_cache/r9diff/` — с `trees/`, `judged/`, `corpus.json`; `selfcheck_cells.json` — самопроверка 16-48, `selfcheck_cells_1647.json` — самопроверка 16-47;
- `.pytest_cache/r9diff-src/`;
- `.pytest_cache/r9-inputs/` — не правился.

16-49 стартует с этой копии.

## Гейты на итоговом дереве (под общим `flock`)

| Проверка | Итог | База (16-47 / оркестратор) |
|----------|------|----------------------------|
| задача 1, №1: писатель + паритет | 626 passed (после задачи 1); итог — 633 (611 + 22) | 620 |
| задача 1, №2 и задача 2: прежние строки `1163ae39` | `OK 259 105 268 107` | — |
| задача 1, №3: формы WR-31, таблица мест, матрица | `OK {…: 2, …: 2, …: 2, …: 1} 1638` | — |
| задача 1, №4: приватность | 298 passed | 298 |
| задача 2, №1: три модуля гейтов | 931 passed | 918 |
| задача 2, №2: строки коллизии имени носителя | `OK 4` | — |
| задача 3, №2: места шапки | `OK` | — |
| задача 3, №3: quick run фазы | **1335 passed** | 1322 |
| задача 3, №4: сквозные гейты + `test_logging_config` | 576 passed + 3 passed (двумя командами) | 576 + 3 |
| задача 3, №5: `run.sh 16-48 && run.sh --against 2f8c1656` | обе rc=0, строки выше | — |
| оба гейта и паритет поимённо | 931 passed | 918 |
| гейт писателя отдельно | 611 passed | 598 |
| живое дерево писателя | `OK 6 104` (тот же набор мест; реестр — ровно `app/application/accounts/phone.py`) | `OK 6 104` |
| живые деревья приватности | «app: файлов 100, вызовов 225, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0» | то же |
| `tests/test_application` | 896 passed | 883 |
| `compileall -q app main.py tests` | выход 0 | 0 |
| `scripts/prohibitions_census.py --check` | выход 0, «реестр: 894 строк, биекция с переписью — согласие» | 894 |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| `tests/test_planning` | гонится после коммита этой сводки (заметка оркестратора 5) | 218 / 2 skipped |

Числа плана — проекции, замер главнее:
- писатель — 611 против 609 плана;
- quick run — 1 335 против 1 333;
- `tests/test_application` — 896.

Сверх плана две строки (отступление 1): +13 правил против +11.

Полная суита (`just test`, ≈45–60 мин) не гонялась: её гонит пост-мердж гейт оркестратора. `graphify update .` не запускался — его делает оркестратор после слияния. `graphify query` гонялся с `--graph /source/broadcaster/graphify-out/graph.json`.

## Decisions Made

- **Место варианта применения.** Варианту применения `methodcaller` отдаётся `holder`, если получатель называет колонку, иначе прежнее место литерала. И `ast.copy_location` атрибута, и `_synthetic_call` берут это место. Дедупликация та же: два узла — две находки по (строка, столбец, вид), одно место по двум путям — одна. Подтверждение — (к10) «второе имя, применённое один раз» (1) и `same-api-handed` (к9) (1).
- **Ранний возврат `_referenced_calls`.** У псевдонима `partial` — применения плюс путь носителя. У судимого имени — путь носителя. У `getattr` — по-прежнему только применения. Новой дедупликации нет.
- **Имя `partial`, связанное с пишущим API.** Применённый `partial(…)(…)` — обёртка носителя, а не только «применение судимого вызова». Это то же «одно толкование закрывает другое», 202 ячейки (к6) из 3 856. Заметка оркестратора требует закрыть семейство целиком.
- **Ожидание строк таблицы писателя в корпусе.** Число мест строки берётся из `LITERAL_FORM_PLACES` дерева HEAD. Строка с несколькими местами судит вид, вызов и колонку у каждой находки (`all_kind`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — заметка оркестратора 1] Семейство (к6) закрыто целиком: пятая строка, законный двойник и третья правка предиката.**
- Найдено: задача 2 (прототип в `.pytest_cache/proto/`, полный суд корпуса 12:03Z). После двух правок плана в (к6) осталось 202 неверных ячейки. Все — имя `partial` из шаблонов носителей-обёрток, связанное с пишущим API: `partial = setattr` и `loop.run_in_executor(None, functools.partial(contextvars.copy_context().run, f), account, 'phone', x)`. Находок было ноль.
- Корень: в `carried_writes` условие «применение судимого вызова — не подача ссылки» отбрасывало применённую обёртку `partial(…)(…)`, потому что имя `partial` судимо (псевдоним API).
- Исправлено: условие не срабатывает, если имя внутреннего вызова — в `partial_names`. В `LITERAL_FORM_CASES` добавлена строка `partial-name-bound-to-setattr-wraps-a-writer-reference`, в `LEGITIMATE_CASES` — двойник `partial-name-bound-to-setattr-wraps-a-status-write`. RED — `4a192880`, GREEN — `533eb042`.
- Проверка: (к6) 3 856 и (к9) 14 503 — 0 неверных; прежние строки, матрица и живое дерево — прежний ответ.

**2. [Rule 2 — заметка оркестратора 8] Корпус вырос до доверия первому GREEN.**
- Добавлено в `kfam.py` / `corpus.py` / `judge.py`:
  - (к9) «одно имя — две роли» на оси носителя: законная роль — обычный метод чужого объекта; двойник `status`; ось счёта — две подачи и одно место двумя толкованиями;
  - (к10) — ось счёта у получателя;
  - (к6) и (к7) — целиком;
  - ожидание строк `a-literal` — из `LITERAL_FORM_PLACES`;
  - адресаты (к9), (к10), строк таблицы и самопроверки 16-48 в `ADDRESSEES`.
- Против вакуума: на базе (к9) неверны 3 628 из 14 503, (к10) — 240 из 756, (к6) — 804 из 3 856.

**3. [Rule 3 — инструмент] Самопроверка 16-47 переименована.**
- Она стала `selfcheck_cells_1647.json` и семейством `f-self-1647` (та же выборка 3 000, seed 47).
- Имя `selfcheck_cells.json` заняла самопроверка 16-48; у своего `f-self-check` seed 48.

**4. [План против замера] Числа переклассификации D2.**
- План: «против `fb8fef72` и `1c243203` — исправлены (1 → 2)».
- Замер:
  - `fb8fef72` — 484 из 1 → 2 и 261 из 0 → 2;
  - `1c243203` — 416 из 1 → 2 и 329 из 0 → 2;
  - `2f8c1656` — 190 прежние (2 → 2) и 555 из 0 → 2.
- Нули на старых деревьях — пропуск наличия (чтение getattr-строкой и др.), его закрыли планы раундов 7–8. Это исправление, не `REPAIRED`.

**5. [Находка вне объёма — адресат 16-49] `run.sh --against 1c243203` → `count_regressions=1`: `x-r8h::T11c 4 -> 2`, rc=1.**
- Ячейка гейта приватности: `w = functools.partial(asyncio.to_thread, logger.info, "x", kwargs={"phone": a.phone}); w()`, ожидание ревьюера `expect: null`. Этот план её не трогает: на базе `5c7377cc` и на HEAD вердикт тот же — 2 находки, отпечаток `a17d4bfba79e`.
- Ручная проверка (`.pytest_cache/checks/t11c.py`):
  - у `1c243203` четыре находки — две пары повторов `app/x.py:3 — имя — phone` и `… — phone=`;
  - у HEAD каждый текст стоит один раз.
- Это ровно класс WR-24 `REPAIRED` пункта 9 договора r9diff, ячейка там названа поимённо. `judge.py` правило пункта 9 для ячеек без точного ожидания не реализует: вердикт хранит число и отпечаток, а не тексты.
- Тот же `count_regressions=1` даст любой прогон против `1c243203` с этим инструментом, и на базе тоже. Закрывающий прогон 16-49 `--against 1c243203` обязан это учесть.
- Инструмент в этой части не правился, чтобы не менять формат кеша вердиктов (`deferred-items.md` не заводился — заметка 5).

### Замены команд (песочница worktree)

- Проверки `python -c` записаны дословно в `.pytest_cache/checks/*.py` и гнались с `PYTHONPATH=.`: `t1_rows.py`, `t1_forms.py`, `t2_rows.py`, `t3_header.py`, `writer_live.py`.
- Составные команды с `flock … bash` и `; echo $?` отклонены. Код выхода `run.sh` пишет обёртка `.pytest_cache/checks/run_rc.sh` (`run-<метка>.rc`). Три прогона `--against` идут подряд через `run_against.sh`.
- Конвейеры `sed` отклонены — разборы написаны скриптами (`wrong_by.py`, `show_cells.py`).
- Ожидание длинных прогонов — `flock -w 590 <lock> true`.
- Первый прогон до правок — `run.sh 16-47`: у 16-48 до первого `test(16-48)` нет базы.
- RED-улика собиралась `red_record.py` из файла параметров. Во время задачи 2 я сначала вписал в два файла параметров неверное `runStartedAt` (12:41 и 12:42). Обе записи пересобраны с настоящим временем из JUnit (12:36:17Z, 12:36:27Z); вердикт классификатора тот же (`RED_EVIDENCE_OK`).
- Задача 3, `<automated>` №4 (сквозные гейты и `test_logging_config` одной командой) — двумя командами: 576 + 3.

---

**Total deviations:** 5. Две правки по правилу 2 — заметки оркестратора 1 и 8. Одна правка инструмента по правилу 3. Одно расхождение плана с замером. Одна находка вне объёма с адресатом 16-49.
**Impact on plan:** гейт, шапка и заявления — по плану. Сверх плана — третья правка предиката (условие `carried_writes` у `partial`), две строки и закрытие (к6) целиком; без них семейство не было бы закрыто. Общий модуль `tests/phone_gate_grammar.py`, гейт приватности и модуль паритета не тронуты.

## Issues Encountered

- Разборы, запущенные параллельно с `run.sh --against`, падали на чтении `corpus.json`: каждый прогон пересобирает его из дерева HEAD. Повторены после прогонов. sha256 корпуса не изменился: `f22ae991…` в каждом прогоне.

## Known Stubs

Нет.

## Threat Flags

Нет: правка — тестовый гейт; новых сетевых точек, путей и схем нет. T-16-110 (WR-31) и T-16-111 (коллизия имени носителя) закрыты, как в плане. Расширение `kw_ext` вынесено разделом выше.

## Next Phase Readiness

- **Инструмент.** 16-49 стартует с копии `.pytest_cache/r9diff/`. `HEAD_WRONG=0`, `EXTERNAL HEAD … defects=0`; в чужих корпусах остались только `COST kw=281 attr=122`.
- **Закрывающий прогон 16-49 `--against 1c243203`** даст `count_regressions=1` на `x-r8h::T11c` (отступление 5). Нужна реализация правила WR-24 пункта 9 для `expect: null` в `judge.py` либо названная запись.
- **Словарь 16-49.** Формы этого плана в общий словарь не вписаны: форма коллизии видов, носитель с соперником под своим именем, место через получатель.
- **Шапка приватности.** Заявление «две разные подачи на одной строке — два узла — две находки, как у гейта писателя» (`tests/test_phone_privacy_gate.py:139-142`) теперь правда для значения `methodcaller-receiver`. Текст не правился.
- **Учёт.** Отметку PHONE-02 и учёт не трогали (заметка оркестратора 5). `kw_ext` — для владельца и верификатора раунда 10.

## Self-Check: PASSED

- Коммиты `3b0d912f`, `36248d38`, `4a192880`, `533eb042`, `709e25d2`, `6d932a97` — предки HEAD (`git log 5c7377cc..HEAD`, 6 коммитов).
- Файлы на месте: `tests/test_application/test_phone_single_writer_gate.py`, эта сводка, `.pytest_cache/r9diff/run.sh`, `selfcheck_1648.py`, `selfcheck_cells.json`, `selfcheck_cells_1647.json`, `kw_ext_evidence.py`, `d2_reclass.py`, `kw_ext_pairs.py`, `repaired_by.py`, `repaired_mr.py`.
- Удалений в коммитах нет: один файл, +400 / −27.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-21*
