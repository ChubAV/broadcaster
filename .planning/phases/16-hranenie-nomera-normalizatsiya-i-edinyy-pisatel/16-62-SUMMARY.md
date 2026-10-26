---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 62
subsystem: testing
tags: [phone-gates, single-writer, raw-sql, runtime-guard, header-truth, CR-08, O-25, O-26, tdd, tracer]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-58 — линия движка `before_cursor_execute` (`_refuse_unscoped_cursor`); 16-59 — `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS`; 16-61 — таблица измеренной границы защиты `GUARD_BOUNDARY_WRITES`"
provides:
  - "Таблица `RAW_SQL_BOUNDARY_FORMS` (`RawSqlForm`): десять форм сырого SQL с измеренным ответом предиката и канала; правило `test_a_raw_sql_form_has_its_measured_static_verdict`"
  - "Правило `test_the_unjudged_raw_sql_form_is_named_in_the_header`; пункт (6) «ГРАНИЦЫ ПРЕДИКАТА» — сырой SQL по замеру, форма `raw-dbapi-sql-from-a-parameter` названа границей с адресатом (ревью фаз 17–20)"
  - "Раздел «ЗАПРЕТ ДИНАМИКИ И ЗАЩИТА НА ИСПОЛНЕНИИ» по рубежам путей записи; `REFUTED_FIRST_RUNG_CLAIM` и «Летопись CR-08»; находка 16-55 и пункт (1) — летописью; закрепление реестра названо"
  - "Правило шапки `test_the_writer_gate_header_names_the_ban_and_the_runtime_guard` закрепляет новое утверждение и место прежней фразы в летописи"
affects: [16-64, "Фазы 17–20 (ревью: запись через сырое соединение DBAPI с текстом SQL из параметра не держит ни один рубеж)"]

actuals:
  tokens: 8794    # chars/4: git diff 05ba9334..77fd3de4 — 35 174 байта (wc -c); кириллица по 2 байта; оценка плана 60 000 включала чтение контекста
  tasks: 2
  commits: 4      # git rev-list --count 05ba9334..HEAD до коммита сводки
plan_head_before: 05ba9334c07062f69c77a823d19c8ef214a8902b
plan_head_after: 77fd3de473a01db027a8a525315203fbdd328824

tech-stack:
  added: []
  patterns:
    - "Таблица измеренной границы статического гейта: строка — ответ предиката и канала по замеру; сдвиг ответа — сигнал «граница сместилась», а не поломка"
    - "Снятая фраза шапки — константа `REFUTED_*` и «Летопись …» в разделе; правило требует, чтобы фраза стояла только в летописи"

key-files:
  created: []
  modified:
    - tests/test_application/test_phone_single_writer_gate.py

key-decisions:
  - "Ответ таблицы `RAW_SQL_BOUNDARY_FORMS` — замер, а не норма: все десять измеренных ответов совпали с таблицей `<scope_note>` плана (на `scripts/x.py` и `app/x.py` одинаково)"
  - "Сырое соединение DBAPI не добавлено видом канала: это расширение перечня `DYNAMIC_CONSTRUCT_KINDS`, решает владелец; форма названа границей с адресатом — ревью фаз 17–20 (О-26 (а)); вынести владельцу как повод расширить перечень — в диспозиции 16-64"
  - "Утверждение «держатель с `bulk_*` / соединением закрыт линией движка» записано по замеру исполнения этого плана (пять форм — отказ `_refuse_unscoped_cursor`), а не по механизму"
  - "Летописи внутри пунктов начинаются словом «Летопись» с заглавной только там, где их читает `_chronicle_segment` («Летопись CR-08», «Летопись находки 16-55»); в пункте (1) — строчная «летопись:», чтобы не рвать чужие отрезки"

patterns-established:
  - "Шапка гейта называет рубежи по путям записи: (а) DML через движок — защита первая, гейт второй; (б) текст SQL и сырое соединение — гейт единственный; (в) процесс без `app.models` и задача из `writer_scope()` — гейт и правило входа"

requirements-completed: [PHONE-02]   # копия requirements плана; REQUIREMENTS.md этот план не трогает (заметка 5 оркестратора)

coverage:
  - id: D1
    description: "Десять форм сырого SQL: ответ предиката и канала закреплён замером; форма без рубежа (`raw-dbapi-sql-from-a-parameter`, 0 и 0) названа в «ГРАНИЦЕ ПРЕДИКАТА» шапки рядом со словами «сырое соединение DBAPI» и «ревью фаз 17–20»"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_raw_sql_form_has_its_measured_static_verdict (10)"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_unjudged_raw_sql_form_is_named_in_the_header"
        status: pass
    human_judgment: false
  - id: D2
    description: "Раздел «ЗАПРЕТ ДИНАМИКИ И ЗАЩИТА НА ИСПОЛНЕНИИ» называет рубежи каждого пути; прежняя фраза `REFUTED_FIRST_RUNG_CLAIM` стоит только в «Летописи CR-08» рядом с CR-08, О-25 (а), 16-58, 553933d8"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_the_ban_and_the_runtime_guard"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_accept.py (критерий задачи 2 дословно) → OK"
        status: pass
    human_judgment: true
    rationale: "Правило сверяет имена и место фразы; правдивость прозы шапки относительно поведения рубежей судит верификатор финального раунда (О-26 (а))"
  - id: D3
    description: "Прежнее не ослаблено: AST определений модуля равен базе (`19c99ffb` и `05ba9334`), кроме правила шапки и пяти добавленных определений; живое дерево — 106 файлов, 0 находок, 6 сырых в писателе"
    requirement: PHONE-02
    verification:
      - kind: other
        ref: ".pytest_cache/checks/t2_astdefs.py (команда <verify> плана дословно) → OK 237 definitions"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/writer_live.py → OK 6 106 offences 0"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_application/test_phone_single_writer_gate.py tests/test_phone_gates_parity.py tests/test_phone_privacy_gate.py -q -p no:randomly → 1160 passed"
        status: pass
    human_judgment: false

duration: 21min
completed: 2026-10-26
status: complete
---

# Phase 16 Plan 62: шапка гейта писателя по рубежам и измеренная граница сырого SQL — Summary

**Таблица `RAW_SQL_BOUNDARY_FORMS` мерит предикат и канал на десяти формах сырого SQL. Единственная форма без рубежа — запись через сырое соединение DBAPI с текстом SQL из параметра — названа в пункте (6) «ГРАНИЦЫ ПРЕДИКАТА» с адресатом «ревью фаз 17–20». Раздел «ЗАПРЕТ ДИНАМИКИ И ЗАЩИТА НА ИСПОЛНЕНИИ» перечисляет рубежи по путям записи: у DML через движок защита первая, статический гейт второй, а у текста SQL и сырого соединения статический гейт — единственный рубеж. Прежняя фраза «первым рубежом» перенесена в «Летопись CR-08», и правило шапки закрепляет это новое место (CR-08; О-25 (а), свойство 5).**

## Performance

- **Duration:** ~21 мин
- **Started:** 2026-10-26T11:25:30Z
- **Completed:** 2026-10-26T11:46:06Z
- **Tasks:** 2, каждая по циклу RED → GREEN
- **Files modified:** 1 (`tests/test_application/test_phone_single_writer_gate.py`)

## Accomplishments

- `RawSqlForm` / `RAW_SQL_BOUNDARY_FORMS` — десять форм (исходник с `from sqlalchemy import text`, суд на `scripts/x.py`) и правило `test_a_raw_sql_form_has_its_measured_static_verdict`. Если ответ сдвинется, сообщение правила: «граница сырого SQL сдвинулась — обновите строку `RAW_SQL_BOUNDARY_FORMS` и шапку (это не поломка, если рубеж стал строже)».
- `test_the_unjudged_raw_sql_form_is_named_in_the_header`: каждая строка с ответом 0 и 0 названа в «ГРАНИЦЕ ПРЕДИКАТА» шапки. В окне ±600 знаков от неё стоят «сырое соединение DBAPI» и «ревью фаз 17–20».
- В шапке появился пункт (6) «сырой SQL» по замеру таблицы. В разделе запрета переписан пункт «Защита на исполнении»: четыре линии, рубежи (а)/(б)/(в), `GUARD_BOUNDARY_WRITES`, «Летопись CR-08». Находка 16-55 переписана в прошедшем времени и снабжена замером и летописью. Пункт «Исключения» называет закрепление реестра `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS`. Фраза пункта (1) о пути за границей защиты заменена, прежняя сохранена летописью. Живое дерево замерено после партии раунда 11.
- `REFUTED_FIRST_RUNG_CLAIM` — прежняя фраза раздела дословно. Правило шапки вместо `"первым рубежом"` закрепляет шесть новых имён и требует, чтобы прежняя фраза стояла только в «Летописи CR-08» рядом с «CR-08», «О-25 (а)», «16-58» и «553933d8».

## Task Commits

1. **Задача 1 (трасер): десять форм сырого SQL, форма без рубежа в шапке**
   - RED `8f598ba3` — `test(16-62): add measured raw SQL boundary table and a failing header rule for the unjudged form`
   - GREEN `ab44de1a` — `feat(16-62): name the unjudged raw DBAPI form in the predicate boundary by measurement`
   - Гейт трасера: интерактивный прогон, `end-of-phase`, у трасера только `<automated>`. Обе команды `<verify>` перезапущены и зелёные (16 passed; 3 passed, канал 106 / 0). Переход к расширению.
2. **Задача 2: раздел запрета по рубежам, летопись CR-08, правило шапки**
   - RED `ff975166` — `test(16-62): require the ban section to name rungs per path and hold the refuted first-rung phrase only in a CR-08 chronicle`
   - GREEN `77fd3de4` — `feat(16-62): name the rungs of each write path in the ban section and move the refuted first-rung phrase into a CR-08 chronicle`

Коммитов REFACTOR нет. Для 16-64 (CR-08): GREEN — `ab44de1a`, `77fd3de4`.

## TDD: RED-улики (три совпадения + классификатор)

Улики лежат в `.pytest_cache/gsd-red/t{1,2}-red.{xml,out,json}` (gitignored). Обе записи `{command, exitCode, targetTest, output, …}` поданы в `check tdd-red-evidence` и вернули `RED_EVIDENCE_OK` / `target_test_failed`.

| Задача | Команда (`-k`) | `FAILED …::<цель>` | Последняя строка | Причинный литерал | Семантическая оценка |
|---|---|---|---|---|---|
| 1 | `unjudged_raw_sql_form` | `FAILED tests/test_application/test_phone_single_writer_gate.py::test_the_unjudged_raw_sql_form_is_named_in_the_header` | `1 failed, 671 deselected, 1 warning in 0.84s` | «форма сырого SQL без рубежа не названа в границе шапки» (нет «`raw-dbapi-sql-from-a-parameter`») | Цель исполнилась и упала на своём утверждении. Десять строк таблицы на RED зелёные: это закрепки замера. Весь модуль на RED: `1 failed, 671 passed` |
| 2 | `names_the_ban_and_the_runtime_guard` | `FAILED …::test_the_writer_gate_header_names_the_ban_and_the_runtime_guard` | `1 failed, 671 deselected, 1 warning in 0.82s` | «шапка гейта писателя не называет запрет динамики и защиту на исполнении» | Не хватало ровно шести новых имён, «Летописи CR-08», и прежняя фраза стояла вне летописи. Сбоев сбора, ввоза и фикстур нет |

## Таблица `RAW_SQL_BOUNDARY_FORMS`: измеренные ответы

Зонд `.pytest_cache/checks/raw_sql_probe.py`. Ответ на `scripts/x.py` и `app/x.py` одинаков. **Все десять ответов совпали с таблицей `<scope_note>` плана**, расхождений «план ↔ замер» нет.

| id | предикат | канал | находка |
|---|---|---|---|
| `text-literal-through-the-session` | 1 | 0 | вид 5, «сырой SQL», стр. 5 |
| `exec-driver-sql-literal` | 1 | 0 | вид 5, стр. 6 |
| `raw-dbapi-literal` | 1 | 0 | вид 5, стр. 7 |
| `text-of-a-module-constant` | 1 | 1 | вид 5 на константе; канал «вычисленный текст SQL» на `text(SQL)` |
| `text-of-a-concatenation` | 0 | 1 | канал на `text('…' + col + '…')` |
| `text-of-a-parameter` | 0 | 1 | канал на `text(sql)` |
| `raw-dbapi-module-constant` | 1 | 0 | вид 5 на константе `phone_is_manual = 1` |
| `raw-dbapi-sql-from-a-parameter` | **0** | **0** | нет. Граница, пункт (6) |
| `exec-driver-sql-module-constant` | 1 | 1 | вид 5 на константе; канал на `conn.exec_driver_sql(Q, (x, i))` |
| `sqlite3-stdlib-literal` | 1 | 0 | вид 5, стр. 9 |

Живое дерево сырого соединения не использует. В коде `app/` и `scripts/` найдено 0 вхождений `get_raw_connection`, `driver_connection` и `sqlite3`. Единственное совпадение `app/models/phone_guard.py:113` — текст шапки. `dbapi_connection` в `app/database.py` — имя параметра слушателя подключения.

**Замер держателя 16-55 / CR-08 под защитой.** Зонд `.pytest_cache/checks/holder_probe.py`: SQLite в памяти, синхронный движок, ввезён `app.models`. Проверены пять форм: `setattr(self, "f", s.bulk_update_mappings)`, `setattr(self, "f", s.bulk_insert_mappings)`, `setattr(B, "w", staticmethod(s.bulk_update_mappings))`, держатель `lambda`, `setattr(self, "f", s.connection().execute)` с `update(MessengerAccount.__table__)….values(fields)`. Все пять — `REFUSED by _refuse_unscoped_cursor`, строка `(None, False)`, строк с номером 0. На этом замере стоит фраза шапки «с плана 16-58 отказывает линией движка».

## Сверка определений с базой (заметка оркестратора 9)

Команда `<verify>` плана записана дословно в `.pytest_cache/checks/t2_astdefs.py` (против `19c99ffb`) и выдала `OK 237 definitions`. Расширенный вариант `.pytest_cache/checks/t2_astdefs_vs.py` проверен против `05ba9334` и против `19c99ffb` (копии `git show <rev>:… > .pytest_cache/checks/base_*_writer_gate.py`); оба раза вывод одинаков:

- база — 237 определений, итог — 242;
- **changed:** `test_the_writer_gate_header_names_the_ban_and_the_runtime_guard`, только оно;
- **removed:** нет;
- **added:** `RawSqlForm`, `=RAW_SQL_BOUNDARY_FORMS`, `=REFUTED_FIRST_RUNG_CLAIM`, `test_a_raw_sql_form_has_its_measured_static_verdict`, `test_the_unjudged_raw_sql_form_is_named_in_the_header`;
- прочие выражения верхнего уровня (ввозы и т. п.) равны базе; докстринг модуля изменён, как и задумано;
- итог: **`OK`**. Предикаты, канал, `LITERAL_FORM_CASES`, `LEGITIMATE_CASES`, `ROUND_TEN_BANNED_FORMS`, `NAMED_COST_MECHANISM_CASES`, матрицы и `PHONE_WRITER_EXCEPTIONS` AST-равны базе.

## Проверки — счёт рядом с базой

| Проверка | База (оркестратор, `05ba9334`) | Итог плана |
|---|---|---|
| `tests/test_application/test_phone_single_writer_gate.py` | 661 (53 с) | 672 (+10 строк, +1 правило), 54,7 с |
| `-k raw_sql` (`<verify>` задачи 1, порог ≥ 11) | — | 16 passed: 10 строк, правило шапки и 5 прежних правил `raw_sql` |
| гейт писателя + паритет + гейт приватности (`<verify>` задачи 2, порог ≥ 1160) | 661 + 143 + 345 = 1149 | **1160 passed** (76,5 с) |
| живые строки (`-s -k "live_tree or live_trees or dynamic_construct_in_the or entered_only_by_the_writer"`) | приватность `app` 102/227, `scripts` 4/68, `max_worker` 2/93, находок 0; канал приватности 108 / 0; JS `wa_worker` 1/68 / 0; канал писателя 106 / 0 | те же строки дословно, 6 passed |
| писатель вживую (`writer_live.py`) | `OK 6 106 offences 0` | `OK 6 106 offences 0` |
| сквозные гейты (htmx post pairs, htmx gates, templates, declared invariants) | 576 | 576 passed (164 с) |
| `scripts/prohibitions_census.py --check` | exit 0, 934 строки | exit 0, 934 строки, биекция |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 | 110 passed |
| `compileall -q app main.py tests` | exit 0 | exit 0 |
| набор фазы (12 путей `<verification>`) | — (база не замерялась) | 1769 passed (103,8 с) |
| `tests/test_planning` | 218 passed, 2 skipped | прогон после коммита сводки (заметка 5); итог — в финальном сообщении исполнителя |

## Files Created/Modified

- `tests/test_application/test_phone_single_writer_gate.py` — изменены шапка (пункт (6), раздел запрета, пункт (1), живое дерево) и правило шапки; добавлены `RawSqlForm`, `RAW_SQL_BOUNDARY_FORMS`, `REFUTED_FIRST_RUNG_CLAIM` и два правила.

## Decisions Made

См. `key-decisions`. Главное: каждое новое утверждение шапки опирается на замер. Таблица сырого SQL проверена зондом и правилом, путь держателя — зондом под защитой, живое дерево — `writer_live.py` и правилами живых деревьев. Прежние фразы не стёрты, а перенесены в летописи с причиной.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - текст] «Сырое соединение DBAPI» с заглавной не находилось правилом**
- **Found during:** задача 1, GREEN
- **Issue:** первая редакция пункта (6) начинала предложение словами «Сырое соединение DBAPI», а правило ищет «сырое соединение DBAPI» с учётом регистра.
- **Fix:** формулировка стала такой: «Запись через сырое соединение DBAPI …». Правило не ослаблялось.
- **Committed in:** `ab44de1a`

**2. [Rule 2 - честность шапки] Замер держателя 16-55 под защитой**
- **Found during:** задача 2
- **Issue:** план велит написать, что держатель с `bulk_*` или соединением «с плана 16-58 отказывает линией движка», но среди строк модуля защиты нет формы с держателем `setattr` и литеральным именем.
- **Fix:** добавлен зонд `holder_probe.py` на пяти формах держателя из ревью CR-08. Все пять отказывают на `_refuse_unscoped_cursor`, и шапка ссылается на этот замер.
- **Files modified:** нет (зонд gitignored, в `.pytest_cache/checks/`)

**3. [Текст] Раздел запрета дополнен сверх плана**
- Пункт «Защита на исполнении» разбит на рубежи (а) DML через движок, (б) текст SQL и сырое соединение, (в) процесс без `app.models` и задача из `writer_scope()`. Последний рубеж взят из шапки защиты (16-61, IN-24), чтобы раздел не умалчивал путь, названный защитой.
- Во «Летописи CR-08» прежняя фраза приведена с хвостом «(виды 2–6 и запрет конструкции), для путей ORM — вторым», то есть целиком. Константа хранит только начало, ровно как в плане.
- Пункт «Живое дерево» дополнен замером после партии раунда 11.
- **Committed in:** `77fd3de4`

### Подстановки команд (та же логика, те же утверждения)

- Однострочники `python -c` (критерий задачи 1, `<verify>` AST-сверки и критерий задачи 2) записаны дословно в `.pytest_cache/checks/{t1_accept,t2_astdefs,t2_accept}.py` и исполнены с `PYTHONPATH=.`. Выводы: `OK`, `OK 237 definitions`, `OK`.
- Сверка AST, кроме базы плана `19c99ffb`, проведена и против `05ba9334` (заметка 9) с явными списками changed / removed / added (`t2_astdefs_vs.py`).
- `-k names_the_ban_and_the_runtime_guard` и `-k unjudged_raw_sql_form` — как в плане. Улики JUnit XML собраны в `.pytest_cache/gsd-red/`.
- Все pytest и тяжёлые скрипты шли под общим `flock`.
- `tests/test_planning` из `<verify>` задачи 2 — после коммита сводки (заметка 5), а не до GREEN.
- `graphify update .` в рабочем дереве не запускался: граф обновит оркестратор после слияния. Ориентация шла через `graphify query … --graph /source/broadcaster/graphify-out/graph.json`.
- Полный `just test` не запускался: это пост-мерж гейт оркестратора.

---

**Total deviations:** 3 (1 текстовая правка по Rule 1, 1 замер по Rule 2, 1 текстовое дополнение) плюс названные подстановки.
**Impact on plan:** правка затронула один файл плана. Ни одна прежняя строка или утверждение не ослаблены и не удалены. AST определений равен базе, кроме разрешённого планом.

## Issues Encountered

Нет. `app/`, общая грамматика, паритет, гейт приватности, модуль защиты, реестр запретов и записи `.planning/` (кроме этой сводки) не тронуты.

## Known Stubs

Нет.

## Threat Flags

Новых поверхностей нет. T-16-144 (mitigate) закрыт разделом по рубежам, «Летописью CR-08» и правилом шапки. T-16-145 (accept) записан пунктом (6) с адресатом и строкой `raw-dbapi-sql-from-a-parameter`; живое дерево сырого соединения не использует.

## Deferred

Нет, `deferred-items.md` не создавался. Для 16-64: форму `raw-dbapi-sql-from-a-parameter` вынести владельцу как повод расширить перечень видов канала (решение О-23 (а), свойство 1). Это решение владельца, а не отложенная работа этого плана.

## User Setup Required

None — внешних сервисов нет.

## Next Phase Readiness

- 16-64 записывает GREEN CR-08: `ab44de1a`, `77fd3de4`. Он может цитировать `RAW_SQL_BOUNDARY_FORMS`, `REFUTED_FIRST_RUNG_CLAIM`, «Летопись CR-08» и пункт (6).
- Ревью фаз 17–20: запись через сырое соединение DBAPI с текстом SQL из параметра не держит ни один рубеж. Строка таблицы краснеет, как только предикат или канал начнут её ловить.

## Self-Check: PASSED

- FOUND: `tests/test_application/test_phone_single_writer_gate.py`, эта сводка.
- FOUND (предки HEAD): `8f598ba3`, `ab44de1a`, `ff975166`, `77fd3de4`.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-26*
