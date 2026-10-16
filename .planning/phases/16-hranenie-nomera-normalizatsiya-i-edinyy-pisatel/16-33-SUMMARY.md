---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 33
subsystem: testing
tags: [ast, phone, single-writer-gate, raw-sql, sqlite, sqlalchemy-core, tdd, wr-21, wr-22, wr-23]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "гейт писателя после плана 16-31 (506 правил, 197 / 86 строк), вид 5 (а) / (б) кодом на нулевой глубине (16-28), матрицы `COLUMN_NAMINGS` × `COLUMN_CONTEXTS` и `NAME_POSITIONS` (16-22, 16-28)"
provides:
  - "одинарная кавычка — четвёртый вид кавычки идентификатора SQLite: `_SQL_QUOTE`, `_sql_visible` / `_sql_scan` (однословный `'…'` виден, `''` внутри — кавычка литерала)"
  - "виды 5 (в) / (г) судятся по видимому SQL; голова допускает кавычку вплотную (`_SQL_HEAD_GAP`)"
  - "ключевые слова `UPDATE` / `SET` / `WHERE` — по разбору отрезков `_sql_scan`, а не по соседним символам"
  - "`COLUMN_CONSTRUCTORS` = column, literal_column, Column, ColumnClause; `COLUMN_NAME_KEYWORDS` с `name`; строки `COLUMN_NAMINGS` (3) и `NAME_POSITIONS` (2)"
  - "трасер `test_a_planted_backfill_with_a_single_quoted_identifier_reddens_the_gate`, правило шапки `test_the_writer_gate_header_names_four_quote_kinds_and_every_column_constructor`; 18 строк `LITERAL_FORM_CASES`, 6 строк `LEGITIMATE_CASES`"
affects: [16-34, 16-35, phase-18, phase-19, phase-20]

actuals:
  tokens: 8760
  tasks: 3
  commits: 10
plan_head_before: 3ffd946e6f9939cf9cc3249df5b063196fc1b484
plan_head_after: 6fbc414c39c7e33bf1deeac710684563c9c56b44

tech-stack:
  added: []
  patterns:
    - "Что слово SQL в кавычках, решает разбор отрезков (границы однословных отрезков из `_sql_scan`), а не соседние символы"
    - "Голова оператора и таблица — по видимому SQL; отрезок предмета находки берётся из исходного текста по позициям совпадения"
    - "Класс конструктора колонки — ось: новое имя в `COLUMN_CONSTRUCTORS` держат обе матрицы через строки `COLUMN_NAMINGS` и `NAME_POSITIONS`"

key-files:
  created: []
  modified:
    - tests/test_application/test_phone_single_writer_gate.py

key-decisions:
  - "Однословный отрезок в любой из четырёх кавычек — идентификатор и судится; многословный и с `''` внутри — литерал и гаснет (критерий 16-28, распространённый на `'…'`)"
  - "Ключевое слово `UPDATE` / `SET` / `WHERE` считается словом в кавычках, только если оно ровно однословный отрезок по разбору `_sql_scan`: окрестность по соседним символам (план) пропускала `SET\"phone\"=` и `\"messenger_accounts\"SET\"phone\"` и принимала фильтр `'n'WHERE'phone'` за запись (самопроверка, заходы 1 и 2)"
  - "Голова (в) / (г): между последним словом и таблицей — пробел или кавычка вплотную (`_SQL_HEAD_GAP`): `INTO'messenger_accounts'` на SQLite пишет"
  - "Цена однословной строки-значения `'phone'` — по замеру: находка только при `=` за ней на нулевой глубине `SET` (`CASE WHEN 'phone' = kind`, `SET note = 'phone' = kind`); `SET note = 'phone'`, `WHERE status = 'phone'`, CTE, скобки — ноль"

patterns-established:
  - "Самопроверка лексики SQL: каждый вид 5 × каждая кавычка × комментарий `/* */` и `-- ⏎` (с пробелами и вплотную) в каждом зазоре и во всех сразу × стык без пробела у кавычки × регистр × три формы Python"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "Скрипт дозаполнения с `UPDATE messenger_accounts SET 'phone' = :p WHERE id = :i` в синтетическом `scripts/` краснит гейт писателя с файлом, строкой и видом; у оператора ровно одна находка"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_backfill_with_a_single_quoted_identifier_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Три формы WR-21, три формы WR-22 и десять форм самопроверки лексики SQL — строки LITERAL_FORM_CASES по одной находке вида «сырой SQL»; однословная строка-значение, комментарий в голове чужой таблицы и три фильтра за `WHERE` у кавычки — ноль"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_legitimate_phone_mention_is_not_a_write"
        status: pass
    human_judgment: false
  - id: D3
    description: "`sa.Column(\"phone\")`, `ColumnClause(\"phone\")`, `Column(name=\"phone\")` — находки в каждом из 714 контекстов и в каждой из 12 позиций имени; две формы WR-23 — строки; `sa.Column(\"title\")` — ноль"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_every_column_naming_in_every_judged_context_is_a_write"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_every_column_naming_nested_in_every_name_position_is_a_write"
        status: pass
    human_judgment: false
  - id: D4
    description: "Шапка называет четыре вида кавычек SQLite, видимый SQL у (в) / (г), четыре конструктора и `name=`, цену однословной строки по замеру, летопись WR-21 / WR-22 / WR-23; заявление прежнее"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_four_quote_kinds_and_every_column_constructor"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
    human_judgment: false
  - id: D5
    description: "Живое дерево — 0 судимых находок в 104 файлах, в писателе 6 сырых (5 × именованный аргумент + 1 × запись атрибута по имени), реестр — ровно модуль-писатель; 190 / 84 строк 4cd68671 и 197 / 86 строк 16-31 — на месте"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_no_phone_write_outside_the_writer_in_the_live_tree"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_exception_registry_names_only_the_writer_module"
        status: pass
    human_judgment: false

duration: 49min
completed: 2026-10-16
status: complete
---

# Phase 16 Plan 33: Лексика SQL и класс конструктора колонки в гейте писателя — Summary

**Одинарная кавычка SQLite — четвёртый вид кавычки идентификатора, голова видов 5 (в) / (г) судится по видимому SQL, а ключевое слово SQL — по разбору отрезков в кавычках. `Column` / `ColumnClause` и `name=` — в таблицах конструктора колонки. Самопроверка прошла 217 332 формы под заявлением и нашла два класса промахов (1 008 и 24 формы, на SQLite каждая пишет колонку); оба закрыты циклами RED/GREEN.**

## Performance

- **Duration:** ≈49 мин
- **Started:** 2026-10-16T09:41:27Z
- **Completed:** 2026-10-16T10:30:49Z
- **Tasks:** 3 (плюс 2 цикла самопроверки)
- **Files modified:** 1

## Accomplishments

- Лексика SQL (WR-21, WR-22):
  - `_SQL_QUOTE` несёт `'`. `_sql_visible` оставляет видимым однословный `'…'`. `''` внутри литерала — кавычка, а не конец, поэтому `'it''s'` гаснет целиком. Незакрытая `'` гасит хвост, как прежде.
  - `_sql_visible` теперь обёртка над `_sql_scan`. Тот же разбор возвращает и границы однословных отрезков в кавычках.
  - `_raw_sql_write` и `_raw_sql_subject` ищут `RAW_SQL_PHONE_WRITE` в видимом SQL. Отрезок для предмета находки берётся из исходного текста по позициям.
  - Голова (в) / (г) допускает кавычку вплотную к таблице (`_SQL_HEAD_GAP`): `INTO'messenger_accounts'`, `COPY"…"`, ``INTO TABLE`…` ``.
  - `UPDATE` / `SET` / `WHERE` — ключевые слова, если слово не является ровно однословным отрезком в кавычках по разбору `_sql_scan`.
- Класс конструктора колонки (WR-23):
  - `COLUMN_CONSTRUCTORS = {"column", "literal_column", "Column", "ColumnClause"}`;
  - `COLUMN_NAME_KEYWORDS = {"text", "key", "name"}`;
  - строки `COLUMN_NAMINGS`: `column-class`, `column-clause-class`, `column-class-name-keyword` (39 наименований);
  - строки `NAME_POSITIONS`: `column-class`, `column-clause-class` (12 позиций).
- Правила и строки:
  - трасер `test_a_planted_backfill_with_a_single_quoted_identifier_reddens_the_gate`;
  - правило шапки `test_the_writer_gate_header_names_four_quote_kinds_and_every_column_constructor`;
  - строки `LITERAL_FORM_CASES` (18): 6 — WR-21 / WR-22, 2 — WR-23, 10 — самопроверка;
  - строки `LEGITIMATE_CASES` (6): 3 по плану и 3 из самопроверки.
- Шапка:
  - вид 3 называет `Column(…)` (имя позицией или `name=`) и `ColumnClause(…)`;
  - вид 5 называет четыре вида кавычек («все четыре»), видимый SQL у (в) / (г) и разбор `_sql_scan` для ключевых слов;
  - цена однословной строки-значения названа по замеру;
  - дописана летопись шестого круга (WR-21 / WR-22 / WR-23, заходы 1–2 самопроверки, О-14 (а) с отвергнутыми (а′) и (б));
  - заявление и «ГРАНИЦА ПРЕДИКАТА» прежние, ни одна форма этого круга в границе не названа.

## Task Commits

1. **Задача 1 (трасер): одинарные кавычки, видимый SQL у (в) / (г)** — `4c286ab3` (test, RED), `e478c8c2` (feat, GREEN).
2. **Задача 2: класс конструктора колонки** — `111d39c4` (test, RED), `8aba9962` (feat, GREEN).
3. **Самопроверка, цикл 1: ключевое слово вплотную к кавычке** — `f6aa7205` (test, RED), `e72a8e53` (feat, GREEN).
4. **Самопроверка, цикл 2: ключевое слово между двумя отрезками в кавычках** — `1e65ce71` (test, RED), `c5e82453` (feat, GREEN).
5. **Задача 3: шапка** — `ac55d689` (test, RED), `6fbc414c` (feat, GREEN).

**Plan metadata:** коммит `docs(16-33)` с этой сводкой.

Гейт трасера после задачи 1: режим `end-of-phase`, у трасера только проверки `<automated>`. Все три команды `<verify>` прогнаны повторно и дали зелёный итог: `515 passed`, `OK 7 4`, `OK 6 104`. После этого план перешёл к задаче 2.

## RED-улики (три совпадения + классификатор)

Каждый RED снят прогоном с `--junit-xml` в `.pytest_cache/gsd-red/` (gitignored, не закоммичено). По каждому есть строка `FAILED …::<цель>`, итоговая строка `N failed` и причинный литерал. Верб `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` на всех пяти записях.

| Цикл | Цель | Итог | Причинный литерал | Семантика |
|------|------|------|-------------------|-----------|
| Задача 1 | `test_a_planted_backfill_with_a_single_quoted_identifier_reddens_the_gate` | `1 failed, 514 deselected` | «идентификатор SQLite в одинарных кавычках не опознан» | Цель исполнилась, `tree_offences` обошёл ровно подложенный файл и вернул `[]`. Весь модуль: 7 failed (трасер + 6 строк WR-21 / WR-22), законные строки зелёные. |
| Задача 2 | `test_every_column_naming_in_every_judged_context_is_a_write[column-class]` | `6 failed, 517 deselected` (`-k "column and (class or clause)"`) | «наименование колонки не опознано» | 714 из 714 контекстов и 117 из 117 форм позиции дали `[]`. Весь модуль: 17 failed, потому что 10 прежних позиций тоже вкладывают 3 новых наименования. |
| Цикл 1 | `test_a_literal_write_form_is_a_write[raw-sql-set-tight-single-quoted-phone]` | `8 failed, 523 deselected` (`-k tight`) | «дала 0 находок вместо одной» | 7 строк записи дали `[]`, законный фильтр `WHERE'phone'` дал находку. |
| Цикл 2 | `test_a_literal_write_form_is_a_write[raw-sql-keyword-between-two-double-quoted-identifiers]` | `5 failed, 531 deselected` (`-k between`) | «дала 0 находок вместо одной» | 3 строки записи дали `[]`, 2 законных фильтра дали находку. |
| Задача 3 | `test_the_writer_gate_header_names_four_quote_kinds_and_every_column_constructor` | `1 failed, 536 deselected` | «шапка гейта писателя не называет четыре вида кавычек SQLite и каждый конструктор колонки» | 6 недостающих мест: фраза «все четыре», прежнее «все три», `_sql_visible` в виде 5, `` `Column( ``, `` `ColumnClause( ``, `name=` в виде 3. |

## Самопроверка исполнителя (задача 3; урок 16-12, 16-17, 16-22, 16-28, 16-31; О-14 (а))

Скрипт `.pytest_cache/1633_selfcheck.py` лежит в gitignored-каталоге worktree и в репозиторий не коммитится. Он однопроцессный и потоковый и работает под общим `flock`. Скрипт подаёт `phone_write_offences(…, "scripts/x.py")` композицию форм:
- под заявлением — ровно одна находка ожидаемого вида; у (а) / (б) предмет называет `phone`, у конструктора — вызов контекста и `phone`;
- у законных форм — ноль находок.

**Ось лексики SQL** (100 908 форм под заявлением на итоговом заходе):
- **Виды 5:**
  - (а) `SET` первым, не первым, после однословного `'where'`; таблица в кавычках × колонка;
  - (б) строчный конструктор первым и не первым; таблица в кавычках;
  - (в) головы `INSERT INTO`, `INSERT OR REPLACE INTO`, `INSERT OR IGNORE INTO`, `INSERT IGNORE INTO`, `REPLACE INTO`, `UPSERT INTO`, `MERGE INTO`;
  - (г) `COPY … (колонки) FROM STDIN`, `COPY … FROM '<файл>'`, `LOAD DATA INFILE … INTO TABLE`, `LOAD DATA LOCAL INFILE … INTO TABLE … (колонки)`.
- **Колонки (8):** `phone`, `"phone"`, `` `phone` ``, `[phone]`, `'phone'`, `phone_is_manual`, `'phone_is_manual'`, `PHONE`.
- **Таблицы (8):** без кавычек, в каждой из четырёх кавычек, `public . messenger_accounts`, `"public" . "messenger_accounts"`, `'main' . 'messenger_accounts'`.
- **Разделители в КАЖДОМ зазоре между токенами и во всех сразу:** `/* x */` с пробелами и вплотную, `-- x⏎` с пробелами и вплотную; стык без пробела там, где на нём не два словесных символа (`SET'phone'=`, `INTO"…"(`); без комментария. По каждому зазору — перед и после каждого слова головы, между головой и таблицей, в `SET` перед и после колонки.
- **Регистр:** как есть и нижний.
- **Формы Python:** константа `SQL = "…"`, `s.execute(text("…"), {"p": p})`, склейка `+`, разрезанная посередине.
- **Законные контроли** (13 188 форм, ноль обязателен):
  - однословная строка-значение в `SET` и в `WHERE`;
  - фильтр `'phone' = :number` / `"phone" = :number` за `WHERE`;
  - значение в каждой кавычке, за ним `WHERE` и колонка номера в каждом написании (фильтр);
  - комментарий в голове вставки в чужую таблицу (`groups`, `'groups'`);
  - многословный литерал с `phone = …`; литерал с `''` внутри;
  - `COPY … TO`; фильтр по номеру; `SELECT` с фильтром и с `'phone'`;
  - подзапрос-фильтр в `SET`.

**Ось класса конструктора** (116 424 формы под заявлением):
- **Перебор:** `column`, `literal_column`, `Column`, `ColumnClause` × префикс (без, `sa.`, `sqlalchemy.`) × связывание имени (позицией, `text=`, `name=`, `*[…]`, `**{"text": …}`, `**{"name": …}`) × колонка (`phone`, `phone_is_manual`):
  - в каждом из 714 `COLUMN_CONTEXTS` — 102 816 форм;
  - вложенным в каждую из 12 `NAME_POSITIONS` в трёх контекстах правила композиции — 5 184;
  - конструктором как позицией над каждым из 39 `COLUMN_NAMINGS` в тех же трёх контекстах — 8 424.
- **Контроль:** колонка `"title"` в каждом контексте — 51 408 форм, ноль обязателен.

| Заход | HEAD, время (UTC) | Подано под заявлением (SQL / конструктор) | `[]` / не та находка | Кратных | Законные с находкой | Закрыто коммитами |
|-------|-------------------|-------------------------------------------|----------------------|---------|---------------------|-------------------|
| 1 | `8aba9962`, 2026-10-16 09:54–09:57 | 168 900 (52 476 / 116 424) | **1 008** — один класс: ключевое слово ВПЛОТНУЮ к кавычке идентификатора. `SET"phone"=`, `` SET`phone`= ``, `UPDATE'messenger_accounts'`: окрестность ключевых слов по одной стороне считала слово «в кавычках». `INTO"messenger_accounts"`, `INTO'…'`, `COPY"…"`, ``TABLE`…` ``: голова требовала `\s+`. Конструктор — 0. | 0 | **24** — `WHERE'phone' = :number` / `WHERE"phone" = :number`: `WHERE` не опознан, фильтр стал записью | `f6aa7205` / `e72a8e53` |
| 2 | `f6aa7205` + GREEN цикла 1 (закоммичен без изменений как `e72a8e53`), 10:01–10:04 | 168 900 | **24** — ключевое слово МЕЖДУ двумя отрезками в кавычках: `'messenger_accounts'SET"phone"=1`, `` 'messenger_accounts'SET`phone`=1 `` | 0 | 0 | `1e65ce71` / `c5e82453` |
| 3 | `1e65ce71` + GREEN цикла 2 (закоммичен без изменений как `c5e82453`), 10:08–10:12 | **217 332** (100 908 / 116 424) — добавлены семейства этого класса: таблица в кавычках × колонка у (а) и (б), значение в кавычках + `WHERE` + колонка в кавычках среди законных | **0** | **0** | **0** | — |
| итог | `6fbc414c`, 10:21–10:25 | **217 332** (100 908 / 116 424); законных 64 596 (13 188 / 51 408) | **0** | **0** | **0** | — |

Итого под заявлением на итоговом дереве 217 332 формы. Это больше порога плана в 20 000.

По осям на итоговом заходе:
- SQL по разделителю: без комментария 1 584; по 20 604 на каждый из четырёх видов комментария; стык без пробела 16 908.
- SQL по форме Python: по 33 636 на каждую.
- Конструктор: по 25 704 на каждый класс в 714 контекстах; по 34 272 на префикс; по 17 136 на связывание имени.

**Замер записи** (SQLite 3.53.1 в памяти, своя таблица `messenger_accounts`, скрипт `.pytest_cache/1633_sqlprobe.py`; базы проекта не касался).

Пишут колонку:
- `SET 'phone' = :p`, `SET'phone'=:p`, `SET"phone"=:p`, `` SET`phone`=:p ``;
- `SET ('phone', flag) = (:p, 1)`;
- `INSERT INTO 'messenger_accounts'`, `INSERT INTO'messenger_accounts'(…)`, `INSERT INTO"messenger_accounts"(…)`, `REPLACE INTO'messenger_accounts'(…)`;
- `INSERT /* x */ INTO`, `INSERT/**/INTO/**/messenger_accounts(…)`, `INSERT OR /* x */ REPLACE INTO`;
- `UPDATE 'messenger_accounts' SET 'phone' = :p`, `UPDATE'messenger_accounts' SET phone`;
- `UPDATE"messenger_accounts"SET"phone"=:p`, `UPDATE'messenger_accounts'SET'phone'=:p`, `` UPDATE`messenger_accounts`SET`phone`=:p ``;
- `SET note = 'where', phone = :p`.

Не пишут номер:
- `SET note = 'phone' WHERE id = 1`, `SET note = 'phone = 1'`;
- `CASE WHEN 'phone' = kind`, `SET note = 'phone' = kind`;
- `WHERE'phone'= :p`, `SET note='z'WHERE'phone'=:p`, `SET note="z"WHERE"phone"=:p`.

**Замер цены однословной строки** (итоговое дерево). Краснеют только формы, где за `'phone'` на нулевой глубине `SET` стоит `=`: `SET kind = CASE WHEN 'phone' = kind THEN 1 ELSE 0 END` и `SET note = 'phone' = kind`. Это та же цена, что прежняя у `CASE WHEN phone = :p`; на SQLite номер прежний. Ноль у форм:
- `SET note = 'phone' WHERE id = 1`, `SET note = 'phone', flag = 1`;
- `WHERE status = 'phone'`;
- CTE с `WHERE status = 'phone'` перед `UPDATE`;
- `SET flag = ('phone' = kind)`;
- `SELECT 'phone' = kind`.

Цена названа в абзаце цены вида 5 шапки.

## Files Created/Modified

- `tests/test_application/test_phone_single_writer_gate.py`:
  - `_SQL_QUOTE` с `'`, `_SQL_HEAD_GAP`, `RAW_SQL_PHONE_WRITE` по видимому SQL;
  - `_SQL_UPDATE` / `_SQL_SET` / `_SQL_WHERE` — голые `\b…\b`, а признак «в кавычках» даёт разбор `_sql_scan`;
  - `_sql_visible` → `_sql_scan`;
  - `_raw_sql_write`, `_raw_sql_subject`, `_raw_sql_set_writes`;
  - `COLUMN_CONSTRUCTORS`, `COLUMN_NAME_KEYWORDS`, докстринг `_phone_column`;
  - строки `COLUMN_NAMINGS`, `NAME_POSITIONS`, `LITERAL_FORM_CASES`, `LEGITIMATE_CASES`;
  - трасер, правило шапки, шапка.

## Decisions Made

- **Признак «слово в кавычках» — по разбору отрезков, а не по окрестности символов.** План требовал добавить `'` в окрестность `_SQL_UPDATE` / `_SQL_SET` / `_SQL_WHERE`. GREEN задачи 1 так и сделал. Самопроверка показала, что окрестность ошибается в обе стороны:
  - по одной стороне она не видит `SET"phone"=` (заход 1);
  - по двум сторонам она принимает `"messenger_accounts"SET"phone"` за `"SET"` и фильтр `'n'WHERE'phone'` — за `'WHERE'` (заход 2).
  
  Различить эти случаи может только разбор отрезков. Поэтому `_sql_scan` возвращает границы однословных отрезков, и ключевое слово пропускается, только если оно ровно такой отрезок. Однословный `'where'` по-прежнему не ключевое слово, как требует план.
- **`''` внутри `'…'` — кавычка литерала.** Иначе `'it''s'` распался бы на два однословных видимых отрезка. Так велит и пункт действия задачи 1 («`''` внутри — гаснет пробелами»).
- **Предмет (г) называет таблицу.** Строки `raw-sql-copy-tight-double-quoted-table` и `raw-sql-load-data-tight-backtick-table` ждут `messenger_accounts`, а не `phone`, как прежние `raw-sql-copy-from` и `raw-sql-load-data`. Предмет режется на 60 символах, и колонку (г) он называть не обязан.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ключевое слово вплотную к кавычке идентификатора и голова без пробела перед таблицей**
- **Found during:** задача 3, самопроверка, заход 1.
- **Issue:** 1 008 форм под заявлением давали `[]`: `SET"phone"=:p`, `` SET`phone`= ``, `UPDATE'messenger_accounts'`, `INTO'messenger_accounts'`, `INTO"…"`, `COPY"…"`, ``INTO TABLE`…` ``. Каждая на SQLite пишет колонку. Фильтр `WHERE'phone' = :number` давал находку (24 формы). Класс `"`, `` ` `` существовал с 16-28 и 16-12; `'` добавилась в этом плане.
- **Fix:** ключевое слово «в кавычках» только при кавычках с обеих сторон; `_SQL_HEAD_GAP` в голове (в) / (г). 7 строк `LITERAL_FORM_CASES`, 1 строка `LEGITIMATE_CASES`.
- **Files modified:** `tests/test_application/test_phone_single_writer_gate.py`.
- **Verification:** гейт писателя `531 passed`; заход 2 — 24 остатка того же класса (п. 2).
- **Committed in:** `f6aa7205` (RED), `e72a8e53` (GREEN).

**2. [Rule 1 - Bug] Ключевое слово между двумя отрезками в кавычках**
- **Found during:** задача 3, самопроверка, заход 2.
- **Issue:** `'messenger_accounts'SET"phone"=1` и подобные давали `[]` (24 формы). Правило «кавычки с обеих сторон» не отличает `"t"SET"c"` от `"SET"`, а `'n'WHERE'phone'` — от `'WHERE'`.
- **Fix:**
  - `_sql_visible` разделён: разбор `_sql_scan` возвращает видимый SQL и границы однословных отрезков;
  - `_raw_sql_set_writes` пропускает ключевое слово, только если оно ровно такой отрезок;
  - окрестность у `_SQL_UPDATE` / `_SQL_SET` / `_SQL_WHERE` снята.
  
  3 строки `LITERAL_FORM_CASES`, 2 строки `LEGITIMATE_CASES`.
- **Files modified:** `tests/test_application/test_phone_single_writer_gate.py`.
- **Verification:** гейт писателя `536 passed`; заходы 3 и итоговый — 0 / 0 / 0 на 217 332 формах.
- **Committed in:** `1e65ce71` (RED), `c5e82453` (GREEN).

**3. [Rule 1 - Bug] Ожидание предмета у двух моих строк (г)**
- **Found during:** цикл 1, GREEN.
- **Issue:** строка `raw-sql-load-data-tight-backtick-table` из RED-коммита `f6aa7205` ждала `phone` в предмете. Гейт форму нашёл, но предмет режется на 60 символах, и `phone` в него не попал.
- **Fix:** две строки (г) этого цикла ждут `messenger_accounts`, как прежние строки (г). Вид, число находок и сама форма прежние; в RED обе строки падали на `[]`.
- **Committed in:** `e72a8e53`.

**4. [Rule 2 - Missing critical] Правило шапки проверяет одинарную кавычку в самой фразе о кавычках**
- **Found during:** задача 3, RED.
- **Issue:** в шапке уже было «строковый литерал `'…'`», и проверка «`'…'` где-то в шапке» проходила вакуумно.
- **Fix:** правило ищет `` `'…'` `` в отрезке от «Кавычки идентификатора» до «все четыре».
- **Committed in:** `ac55d689` (RED, до GREEN).

### Отклонения чисел план → замер (замер побеждает, строки не снимались)

| Что | План | Замер | Почему |
|-----|------|-------|--------|
| гейт писателя после задачи 1 | ≥ 513 | 515 | база 506 (16-31), а не 504 |
| гейт писателя после задачи 2 | ≥ 521 | 523 | то же |
| гейт писателя итог | ≥ 522 | 537 | +10 строк записи и +4 законных (циклы 1–2, сверх строк плана) |
| строки на итоговом дереве (4cd68671 / 16-31 / итог) | 190 84 → прежние | `OK 190 84 197 86 215 92` | +18 / +6 этого плана |
| оба гейта и паритет | 723 на базе | 754 | +31 у гейта писателя |
| quick run фазы | 1127 на базе | 1158 | то же |
| `tests/test_application` | 791 на базе | 822 | то же |
| наименования / позиции | `OK 39 12` | `OK 39 12` | — |
| писатель / дерево | `OK 6 104` | `OK 6 104` | — |
| самопроверка | ≥ 20 000 | 217 332 | — |

---

**Total deviations:** 4 исправлены автоматически (3 — Rule 1, 1 — Rule 2), плюс расхождения чисел, описанные выше.
**Impact on plan:** все правки — в единственном файле плана. Реестр, заявление, прежние строки и общий модуль не тронуты.

## Замены команд (песочница worktree, хост)

- **Критерий приёмки задачи 1** (`git show` внутри `python -c`): эталоны сохранены простыми командами — `git show 4cd68671:… > .pytest_cache/1633_base_writer_gate.py` и копия файла на старте плана (`3ffd946e`) в `.pytest_cache/1633_head_writer_gate.py`. Та же логика сравнения исполнена скриптом `.pytest_cache/1633_rows_check.py` по обоим эталонам:
  - итог `OK 190 84 197 86 215 92` — первые два числа по 4cd68671, вторые по 16-31, третьи — итоговое дерево;
  - ни одна строка не потеряна.
- **RED задачи 2:** `-k "column and (class or clause)"` под `flock` песочница отвергла. Тот же выбор исполнен скриптом `.pytest_cache/1633_red_t2.sh` под тем же `flock`.
- **Составные команды** с несколькими `uv run python -c` песочница отвергла. Каждая команда `<automated>` прогнана отдельным вызовом с тем же текстом.
- **Самопроверка:** HEAD передаётся скрипту аргументом, без вызова `git` из Python.
- **Полная суита** (~5112 тестов, ~46 мин) не гонялась: её гонит пост-мердж гейт оркестратора на слитом дереве.
- **`graphify update .`** не запускался: граф обновит оркестратор после слияния. Ориентация шла по `graphify query … --graph /source/broadcaster/graphify-out/graph.json` (только чтение).
- **`.planning/WINDOWS.md` и `deferred-items.md`** не писались (orchestrator_notes 5). Отложенного нет: каждая найденная форма закрыта в плане, а общий модуль ни одна из них не потребовала.

## Гейты на итоговом дереве (`6fbc414c`, 2026-10-16, под `flock`)

- **Task-1 `<automated>`:** #1 — гейт писателя `537 passed`; #2 — `OK 7 4`; #3 — `OK 6 104` (в писателе 5 × `KIND_KEYWORD` + 1 × `KIND_SETATTR`, реестр — ровно писатель, 104 файла, находок 0).
- **Task-2 `<automated>`:** #2 — `OK 39 12`; #3 — `OK 6 104`.
- **Task-3 `<automated>`:** #2 — фразы шапки `OK`; #3 — quick run фазы `1158 passed`.
- **Критерии приёмки:**
  - `grep -c` правила трасера = 1; `WR-21` = 16, `WR-22` = 12, `WR-23` = 14;
  - живое дерево и реестр — `OK`;
  - `git log --format=%h 4c286ab3^..HEAD -- tests/phone_gate_grammar.py` — пусто (общий модуль планом не тронут; первый коммит плана — `4c286ab3`);
  - модуль гейта компилируется с `-W error::SyntaxWarning`.
- **Оба гейта и паритет поимённо:** `754 passed`.
- **`tests/test_application`:** `822 passed`.
- **Сквозные гейты** `test_htmx_post_pairs.py`, `test_htmx_gates.py`, `tests/test_templates`, `test_declared_invariants.py`: `576 passed` (2 мин 38 с). `tests/test_logging_config.py`: `3 passed`.
- **`uv run python -m compileall -q app main.py tests`:** код выхода 0.
- **`scripts/prohibitions_census.py --check`:** код выхода 0, «реестр: 837 строк, биекция с переписью — согласие». `tests/test_planning/test_plan_prohibitions_census.py`: `110 passed`.
- **`tests/test_planning`** гонится после коммита этой сводки; число — в финальном сообщении исполнителя.

## TDD Gate Compliance

- **RED:** `test(16-33)` — `4c286ab3`, `111d39c4`, `f6aa7205`, `1e65ce71`, `ac55d689`.
- **GREEN:** `feat(16-33)` — `e478c8c2`, `8aba9962`, `e72a8e53`, `c5e82453`, `6fbc414c`.
- **REFACTOR:** не понадобился.
- Каждый RED предшествует своему GREEN; нарушений нет.

## Issues Encountered

Нет: каждый промах самопроверки закрыт в плане.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

План 16-34 переводит гейт писателя на общую семантику носителя из 16-32. Блок ввоза и помощники носителя этот план не трогал. Правки лексики SQL и конструктора колонки живут вне функций носителя и с ними не пересекаются.

План 16-35 пишет строки диспозиции WR-21…WR-23:
- для WR-21 / WR-22 — что самопроверка нашла ещё ключевое слово вплотную к кавычке и между отрезками (заходы 1–2);
- для WR-23 — что `name=` вошёл в общий набор имён конструктора и поиска (цена названа в комментарии к `COLUMN_NAME_KEYWORDS`).

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-16*

## Self-Check: PASSED

- FOUND: tests/test_application/test_phone_single_writer_gate.py
- FOUND (ancestors of HEAD): 4c286ab3, e478c8c2, 111d39c4, 8aba9962, f6aa7205, e72a8e53, 1e65ce71, c5e82453, ac55d689, 6fbc414c
- `tests/test_planning` после коммита сводки (`01a4c242`): `218 passed, 2 skipped`
