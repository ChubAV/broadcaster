---
phase: 17-pokaz-nomera-na-vseh-ekranah
plan: 06
subsystem: ui
tags: [phone, history, csv-export, formula-injection, tdd, tracer]

requires:
  - phase: 17-pokaz-nomera-na-vseh-ekranah
    provides: "17-01: shown_phone, load_account_rows, seed_account; 17-04: history_account_label и карта load_account_rows в history_partial (второй вызов этого плана встаёт до потока)"
provides:
  - "app/pages/history.py: EXPORT_HEADER из девяти колонок, «Номер» сразу после «Аккаунт» (индекс 3); export_phone_cell(stored) -> str; export_row(log, group, user, *, phone=None)"
  - "history_export: карта номеров `phones` одним запросом load_account_rows(db, user.id) ДО db.stream(query) и до StreamingResponse("
  - "докстринг export_row: отступления D-09 (без «+») и D-16 (пусто вместо «Номер неизвестен», без #id), D-15 (нет аккаунта — пусто)"
  - "tests/test_pages/test_history_export.py: таблица PHONE_CELLS (15 строк), 4 сквозных теста, правило докстринга, переписанные позиции колонок"
affects: [17-07, 17-08, 17-09]

actuals:
  tokens: 5200
  tasks: 2
  commits: 4
plan_head_before: 8712cc044a036e1a5d9d0c3f3e9425bec7233b49
plan_head_after: 93da6930c6e21082deb90db2052e9d93d6dbb5ad

tech-stack:
  added: []
  patterns:
    - "Ячейка файла строится тем же правилом показа, что подпись экрана (shown_phone), затем снимается один «+» и значение проходит export_cell без исключений"
    - "Карта аккаунт → номер читается до открытия серверного курсора, а не внутри генератора"

key-files:
  created: []
  modified:
    - app/pages/history.py
    - tests/test_pages/test_history_export.py

key-decisions:
  - "RED первой задачи несёт не только заготовку export_phone_cell (`return \"\"`), но и вставку «Номер» в EXPORT_HEADER и параметр phone в export_row: без них целевой тест падал бы на ValueError в header.index, а не на утверждении `assert '' == '7 999 123-45-67'`"
  - "Утверждение «Номер» в тесте формул — по месту (`row[EXPORT_HEADER.index(\"Номер\")] == \"'=1+1\"`), а не `\"'=1+1\" in row`: то же значение уже приходит из ad_title, и проверка `in row` была бы вакуумной для ячейки номера"
  - "В тесте записи без группы номер передаётся (phone=\"+79991234567\"): пустая ячейка доказывает, что D-15 держится условием `if group`, а не отсутствием номера"

patterns-established:
  - "Табличные правила строки выгрузки находят ячейку по заголовку (`EXPORT_HEADER.index(...)`), а не по числу — вставка колонки больше не сдвигает их молча"

requirements-completed: [PHONE-07]

coverage:
  - id: D1
    description: "Файл /history/export несёт девять колонок; «Номер» сразу после «Аккаунт», идентификатор аккаунта остался на индексе 2; номер без ведущего «+» (7 999 123-45-67)"
    requirement: "PHONE-07"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history_export.py#test_export_carries_the_number_without_the_plus"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_export.py#test_export_header_has_nine_columns"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_export.py#test_export_carries_the_account_of_the_group"
        status: pass
    human_judgment: false
  - id: D2
    description: "Ячейка «Номер» обезврежена без исключений: =1+1, +=1, -5, @x, ++5 (снят ровно один знак); неразбираемое — как есть"
    requirement: "PHONE-07"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_history_export.py#test_export_phone_cell_table (15 строк PHONE_CELLS)"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_export.py#test_export_row_puts_the_phone_cell_after_the_account (15 строк)"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_export.py#test_export_cell_defuses_a_formula_in_every_value_bearing_column"
        status: pass
    human_judgment: false
  - id: D3
    description: "Нет номера — ячейка пустая (не «Номер неизвестен»), у двойников без #id; нет группы — пусты «Аккаунт» и «Номер»; чужой номер в файл не попадает"
    requirement: "PHONE-07"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history_export.py#test_export_leaves_the_number_cell_empty_for_an_account_without_one"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_export.py#test_export_does_not_add_the_twin_id_to_the_number_cell"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_export.py#test_export_leaves_account_and_number_empty_without_a_group"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history_export.py#test_export_never_carries_another_users_number"
        status: pass
    human_judgment: false
  - id: D4
    description: "Карта номеров читается до db.stream и до StreamingResponse(; потолок строк проверяется до ответа; чтение потоком сохранено"
    requirement: "PHONE-07"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_history_export.py#test_export_cap_is_checked_before_the_streaming_response"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history_export.py#test_export_reads_the_selection_as_a_stream"
        status: pass
    human_judgment: true
    rationale: "Структурные тесты проверяют порядок в исходнике, а не поведение серверного курсора: что вторая инструкция на сессии с открытым курсором db.stream обрывает выгрузку, на PostgreSQL не измерено (RESEARCH Pitfall 10, вывод без замера). Порядок до потока — страховка по построению, живую выгрузку на боевом драйвере проверит обход владельца"
  - id: D5
    description: "Отступления D-09 и D-16 от D-30 записаны причинами в докстринге export_row"
    requirement: "PHONE-07"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_history_export.py#test_the_export_row_docstring_names_both_departures_from_d30"
        status: pass
    human_judgment: false

duration: 22min
completed: 2026-11-20
status: complete
---

# Phase 17 Plan 06: Колонка «Номер» в CSV-выгрузке истории

**CSV-выгрузка `/history/export` получила девятую колонку «Номер» сразу после «Аккаунт»: номер строится правилом подписи экрана (`shown_phone`), без ведущего «+» (снят ровно один знак до `export_cell`), пуст у неизвестного номера и у записи без аккаунта, формулы обезврежены без исключений; карта номеров читается одним запросом до открытия потока.**

## Performance

- **Duration:** около 22 мин по часам хоста; бо́льшая часть — прогоны под общим замком pytest
- **Started:** 2026-11-20T19:02Z (ориентировочно: файл-датчик записан в 19:05:45Z)
- **Completed:** 2026-11-20T19:24Z
- **Tasks:** 2 (обе `tdd="true"`; первая — `type="tracer"`)
- **Files modified:** 2 (оба существовали; новых файлов нет)

## Accomplishments

- **Трассер (задача 1):** колонка `phone` → `load_account_rows(db, user.id)` → словарь `phones` → `export_row(..., phone=phones.get(group.account_id) if group else None)` → `export_phone_cell` → ячейка «Номер» файла. Номер `+79991234567` в файле — `7 999 123-45-67`; «Аккаунт» остаётся `str(account_id)` на индексе 2.
- **Таблица ячейки (задача 2):** 15 строк `PHONE_CELLS` (`None`, пусто, пробелы; четыре разбираемых номера; три неразбираемых; `=1+1`, `+=1`, `-5`, `@x`, `++5`, `+`) прогнаны и через `export_phone_cell`, и через `export_row` по месту. Срез знака — `removeprefix("+")`, `lstrip` не используется (на `++5` они расходятся).
- **Отступления от D-30 записаны причинами** в докстринге `export_row` (D-09, D-16, D-15) и закреплены правилом `test_the_export_row_docstring_names_both_departures_from_d30`.
- **Структурные правила порядка зелёные:** `history_count(` раньше `StreamingResponse(`, `.stream(` и `EXPORT_YIELD_PER` в теле обработчика; `load_account_rows(db, user.id)` встал после проверки потолка, до `query` и `body()`.
- **Журнал не тронут:** новых вызовов `logger` нет, `history_export_stream_failed` по-прежнему несёт только `user_id` (D-08).

## Что менялось в `app/pages/history.py`

| Имя | Состав |
|---|---|
| `EXPORT_HEADER` | девять колонок: «Время», «Канал», «Аккаунт», **«Номер»**, «Группа», «Заголовок объявления», «Статус», «Ошибка», «Идентификатор задачи» |
| `export_phone_cell(stored)` | `shown_phone(stored)`; `None` → `""`; иначе `export_cell(shown.removeprefix("+"))` |
| `export_row(log, group, user, *, phone=None)` | после ячейки аккаунта — `export_phone_cell(phone) if group else ""` |
| `history_export` | `phones = {row.id: row.phone for row in await load_account_rows(db, user.id)}` — после проверки потолка, до построения `query`, `body()` и `StreamingResponse(` |
| импорт | `shown_phone` из `app.services.account_label` |

Прочее в модуле (`history_account_label`, `acct_labels`, карточка) — работа 17-04, не тронуто; имена, нужные 17-07, на месте.

## Task Commits

1. **Задача 1 (tracer): номер в ячейке «Номер» файла**
   - RED `dcd22778` — `test(17-06): add failing test for the account number column in the history export`
   - GREEN `ac47cc22` — `feat(17-06): carry the account number in the history export after the account id`
2. **Задача 2: таблица ячейки, отступления записаны**
   - RED `21a965ae` — `test(17-06): add failing check for the export row docstring and the number cell table`
   - GREEN `93da6930` — `feat(17-06): record the D-09 and D-16 departures in the export row docstring`

REFACTOR-коммитов нет. **Plan metadata:** коммит `docs(17-06)` этой сводки.

## TDD Gate Compliance

RED (`test(17-06):`) предшествует GREEN (`feat(17-06):`) у обеих задач; каждый `feat` — потомок своего `test`. Нарушений нет. `refactor(17-06):` — 0.

### Улики RED (три совпадения: строка `FAILED`, итог с `failed`, причинный литерал)

Файлы улик (`.pytest_cache/gsd-red/`, вне git): `17-06-t1.{xml,log,json}`, `17-06-t2.{xml,log,json}`; запись собирает `.pytest_cache/checks/make_red_record.py`. Обе прошли `gsd-tools check tdd-red-evidence` → `RED_EVIDENCE_OK` / `target_test_failed`.

| Задача | `FAILED` | Итог | Причинный литерал | `semanticAssessment` |
|---|---|---|---|---|
| 1 | `FAILED tests/test_pages/test_history_export.py::test_export_carries_the_number_without_the_plus` | `1 failed, 48 passed` | `AssertionError: assert '' == '7 999 123-45-67'` | Цель выполнилась и упала на планируемом утверждении: запись посеяна, ответ 200, шапка содержит «Номер», ячейка пуста, потому что заготовка `export_phone_cell` возвращает `""`. Не ошибка сбора (заготовка с окончательной сигнатурой импортируется) и не фикстура. Остальные 48 — зелёные, включая четыре переписанных правила позиций (`row[6]`) |
| 2 | `FAILED tests/test_pages/test_history_export.py::test_the_export_row_docstring_names_both_departures_from_d30` | `1 failed, 83 passed` | `assert 'D-09' in 'Строка файла выгрузки для одной записи журнала …'` | Цель упала на планируемом утверждении: докстринг `export_row` D-09 не называл. **Таблица `PHONE_CELLS` и сквозные тесты зелёные при RED по построению** — логика задачи 1 уже верна, расхождений таблица не нашла (план это допускал: «логику править только если таблица найдёт расхождение»); они закрепляют поведение, которое ломается при правке (например `lstrip` вместо `removeprefix`) |

## Verification (замеры; базы — заметки оркестратора для bf7c5363 / 8712cc04)

| Проверка | База | Итог (93da6930) |
|---|---|---|
| `tests/test_pages/test_history_export.py` | 48 passed | **84 passed** (+36: 1 трассер, 30 строк двух параметризованных таблиц, правило докстринга, 4 сквозных; `test_export_header_has_eight_columns` переименован в `…nine…`, не добавлен) |
| `-k "number or nine or cap_is_checked or as_a_stream"` | — | 4 passed |
| Гейты номера (`test_phone_privacy_gate`, `test_phone_gates_parity`, `test_phone_single_writer_gate`) | 1161 passed | **1161 passed** |
| Сквозные (`tests/test_templates`, `test_htmx_gates`, `test_htmx_post_pairs`, `test_declared_invariants`) | 576 passed | **576 passed** |
| `test_history.py` + `test_account_label_history.py` + `test_history_retry.py` | 49 + 10 + 63 | **122 passed** |
| `prohibitions_census.py --check` | 953 строки, exit 0 | 953 строки, согласие, exit 0 |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| `tests/test_planning` (до коммита сводки) | 218 passed, 2 skipped | 218 passed, 2 skipped |
| `tests/test_planning` (после коммита сводки) | 218 passed, 2 skipped | 218 passed, 2 skipped |

Приёмочные проверки: `EXPORT_HEADER` — длина 9, `[2]=='Аккаунт'`, `[3]=='Номер'` (выход 0); `^def export_phone_cell` = 1; `removeprefix("+")` = 1; `lstrip("+")` = 0; `def test_export_header_has_eight_columns` = 0; докстринг содержит `D-09`, `D-16`, `D-15` (выход 0); `"++5"` = 1, `"=1+1"` = 3.

## Deviations from Plan

### Plan-vs-measured (измерение побеждает)

- **Состав RED-коммита задачи 1 шире «заготовки `return ""`».** План: «RED-коммит несёт `export_phone_cell` с окончательной сигнатурой и телом-заготовкой». Измерение: чтобы целевой тест падал на `assert '' == '7 999 123-45-67'`, а не на `ValueError` в `header.index("Номер")`, RED-коммит несёт ещё вставку «Номер» в `EXPORT_HEADER`, параметр `phone` в `export_row` и вызов заготовки из строки. Реализация — тело `export_phone_cell`, импорт `shown_phone`, карта и передача номера в генератор — в GREEN. Продуктовый результат тот же.
- **Таблица и сквозные тесты задачи 2 зелёные при RED** (разобрано в таблице улик). Красным был только тест докстринга — как и значится целью RED в плане.
- **Допущено расширение сверх перечня тестов плана:** `test_export_row_puts_the_phone_cell_after_the_account` (таблица `PHONE_CELLS` через `export_row`, по месту) и `test_export_never_carries_another_users_number` (T-17-19). Файлы — из `files_modified`.
- **Тест формул: утверждение по месту.** План: «ячейка начинается с апострофа». `"'=1+1" in row` не доказывает ничего про «Номер» — то же значение приходит из `ad_title`; проверка сделана по `EXPORT_HEADER.index("Номер")`.

### Auto-fixed Issues

Нет — правок вне плана не потребовалось. Файлы вне `files_modified` не менялись.

**Total deviations:** 0 auto-fixed; 4 plan-vs-measured (все описаны выше)
**Impact on plan:** продуктовый код и поведение — ровно по плану; названные заранее четыре красных правила переписаны (`:88` → девять колонок, `:257`, `:269`, `:465` → `row[6]`).

## Issues Encountered

- Прогоны pytest ждали общего замка; два набора (сквозные 125 с, история 104 с) уходили в фон, результат читался из журналов. Дефектов не вскрыто.
- Один вывод остаётся без замера, как и в RESEARCH: поведение второй инструкции на сессии с открытым курсором `db.stream` на PostgreSQL (D4 в `coverage`, `human_judgment: true`). Карта читается до потока, так что вопрос снят по построению.

## Substitutions (orchestrator notes)

- **Весь набор не запускался:** `just test` (~5852 теста, ~41 мин) не гонялся — его вызывает пост-слиянием оркестратор; вместо него — модуль плана, гейты номера, оба набора сквозных гейтов, тесты страниц истории, перепись запретов, `compileall`, `tests/test_planning`. Каждый прогон pytest шёл под `flock /source/broadcaster/.pytest_cache/gsd-orch/pytest.lock`.
- **`graphify update .` не запускался** (граф вне рабочего дерева, `graphify-out/` игнорируется git): перестроит оркестратор после слияния.
- **Правки файлов — через `Edit` и короткие `python3`-скрипты со строковой заменой** (песочница отказала составной команде `git rev-parse …` в одной строке; ячейки в `history.py` и тестах заменены `str.replace` с проверкой, что образец найден). Датчики `gsd-plan-head-before-17-06` и `gsd-spawn-toplevel` записаны в каталог git рабочего дерева отдельными простыми командами.
- **Рабочий файл улик:** `.pytest_cache/checks/make_red_record.py` — в игнорируемом `.pytest_cache/`.
- **Базы и бой не трогались:** `.env`, alembic, запуск приложения, живой Redis — не использовались. STATE.md, ROADMAP.md, REQUIREMENTS.md и реестр запретов не правились; `requirements.mark-complete` не вызывался.

## Known Stubs

Нет. Заготовка `export_phone_cell` из RED заменена реализацией в GREEN-коммите `ac47cc22`.

## Threat Flags

Нет новой поверхности. T-17-18 (формульная инъекция): каждая ячейка проходит `export_cell`, знак снимается ДО защиты, таблица `PHONE_CELLS` с `=1+1`, `+=1`, `-5`, `@x`, `++5`. T-17-19 (чужие номера): карта — `load_account_rows(db, user.id)`, номер подставляется по `group.account_id` записей самого пользователя; `test_export_hides_other_users_records` и новый `test_export_never_carries_another_users_number` зелёные. T-17-20 (вторая инструкция при открытом курсоре): карта до `db.stream(query)` и `StreamingResponse(`, структурные правила зелёные. Вызовов журнала с номером нет, гейты номера зелёные (1161).

## Next Phase Readiness

- Для 17-07: `history_account_label`, ключ `account_label` и макрос `history_card` не тронуты; в `history.py` изменены только блок выгрузки и импорт `shown_phone`.
- Для внешних таблиц пользователя: «Статус» и правее сдвинулись на одну колонку (`row[5]` → `row[6]`); «Аккаунт» на месте. Изменение формы файла — флаг `costly` плана, отдельного чекпойнта нет (решение «рядом» заперто D-05).

---
*Phase: 17-pokaz-nomera-na-vseh-ekranah*
*Completed: 2026-11-20*

## Self-Check: PASSED

- Изменённые файлы на месте: `app/pages/history.py`, `tests/test_pages/test_history_export.py`.
- Коммиты `dcd22778`, `ac47cc22`, `21a965ae`, `93da6930` — предки HEAD; `git rev-list --count 8712cc04..93da6930` = 4 = `commits` во frontmatter (без коммита сводки).
- Тема-гейты: 2 × `test(17-06):`, 2 × `feat(17-06):`, `refactor(17-06):` — 0.
