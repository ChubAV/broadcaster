---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 28
subsystem: testing
tags: [ast, phone, single-writer-gate, raw-sql, tdd, wr-15, wr-16]

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "гейт единственного писателя после плана 16-27 (общая грамматика связывания `tests/phone_gate_grammar.py`, `COLUMN_NAMINGS` × `COLUMN_CONTEXTS`, `RAW_SQL_PHONE_WRITE`, `LITERAL_FORM_CASES` 175 / `LEGITIMATE_CASES` 78)"
provides:
  - "композиционный `_phone_column`: имя в позиции имени индекса, поиска, конструктора и `getattr` — любое наименование колонки номера любой глубины; `getattr(X, \"<const>\")` — производная `X`"
  - "`NamePosition` / `NAME_POSITIONS` (10 позиций) и правило `test_every_column_naming_nested_in_every_name_position_is_a_write`; трасер `test_a_planted_backfill_with_a_nested_column_naming_reddens_the_gate`"
  - "вид 5 (а) и (б) кодом: `_raw_sql_set_writes` на нулевой глубине скобок (литералы, комментарии и кавычки не из одного слова пропускаются, `_sql_visible`); `RAW_SQL_PHONE_WRITE` — только (в) и (г); правило `test_a_raw_sql_write_after_a_subquery_in_set_is_a_write`"
  - "склейка `+` из одних констант судится один раз — у склейки"
affects: [16-29, 16-30, phase-18, phase-19, phase-20]

actuals:
  tokens: 13648
  tasks: 3
  commits: 9
plan_head_before: 922b915ffdceb6c45a9f5de3099e8bb997a591a4
plan_head_after: 5bf3e3f5787cf36dce3aa712d8c001f2248d83a0

tech-stack:
  added: []
  patterns:
    - "Ось композиции — таблица позиций имени `NAME_POSITIONS` с правилом «каждое наименование в каждой позиции», а не перечень вложенных форм"
    - "Сырой SQL с вложенностью судится кодом над «видимым» SQL (`_sql_visible`: длина и позиции прежние, литералы, комментарии и неоднословные кавычки — пробелы), а не регулярным выражением"
    - "Предмет находки называет колонку, даже если текст наименования её не показывает (`_naming_text`) или запись лежит за 60 символами начала оператора (`_raw_sql_subject`)"

key-files:
  created: []
  modified:
    - tests/test_application/test_phone_single_writer_gate.py

key-decisions:
  - "`_raw_sql_set_writes` возвращает список найденных записей (`phone =`, `(status, phone) =`), а не `bool`: проверки плана (`assert f(…)` / `assert not f(…)`) работают по истинности, а предмет находки называет запись, лежащую за 60 символами начала оператора"
  - "Идентификатор или строка в кавычках `\"…\"`, `` `…` ``, `[…]` с одним словом внутри видны как есть (могут быть колонкой номера), с иным содержимым — непрозрачны для структуры; ключевые слова `update` / `set` / `where` — не идентификатор в кавычках"
  - "Склейка `+` из одних строковых констант судится у самой склейки: она пишет, если пишет весь оператор или хотя бы одна константа; одна находка на оператор"
  - "Сравнение с колонкой номера на нулевой глубине `SET` (`CASE WHEN phone = :p …`) — цена строгости вида 5 (а), названа в шапке; так же судилось и до плана"

patterns-established:
  - "Самопроверка оси наименований — композиция глубины 1 в каждом контексте и глубины 2 в контексте каждой пары (вид, вызов), плюс позиции сверх таблицы и контроль чужой колонки"
  - "Самопроверка оси SQL — вид 5 × конструкция перед колонкой × голова оператора × хвост × форма Python (константа, склейка); законные контроли — с каждой конструкцией"

requirements-completed: [PHONE-02]

coverage:
  - id: D1
    description: "Скрипт дозаполнения с ключом `MessengerAccount.__table__.c[MessengerAccount.phone.key]` в синтетическом `scripts/` краснит гейт с файлом, строкой и видом"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_planted_backfill_with_a_nested_column_naming_reddens_the_gate"
        status: pass
    human_judgment: false
  - id: D2
    description: "Пять форм WR-15 — строки LITERAL_FORM_CASES, по одной находке ожидаемого вида; четыре новых строки COLUMN_NAMINGS держит матрица 714 контекстов"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_literal_write_form_is_a_write"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_every_column_naming_in_every_judged_context_is_a_write"
        status: pass
    human_judgment: false
  - id: D3
    description: "Правило композиции: каждое из 36 наименований в каждой из 10 позиций имени в трёх контекстах (ключ values, ключ строки bulk_update_mappings, имя setattr) — ровно одна находка"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_every_column_naming_nested_in_every_name_position_is_a_write"
        status: pass
    human_judgment: false
  - id: D4
    description: "Вид 5 (а) и (б) кодом на нулевой глубине: форма WR-16, литерал со словом where, кавычки phone_is_manual, строчный конструктор не первым, where в комментарии и в кавычках — находки; фильтр по номеру в WHERE и в подзапросе — ноль"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_raw_sql_write_after_a_subquery_in_set_is_a_write"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_a_legitimate_phone_mention_is_not_a_write"
        status: pass
    human_judgment: false
  - id: D5
    description: "Шапка: композиция наименований (вид 3), вид 5 кодом, граница и летопись пятого круга; заявление прежнее; правило шапки 16-27 зелено"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_the_writer_gate_header_names_the_shared_grammar_and_every_carrier"
        status: pass
      - kind: other
        ref: "plan 16-28 task 3 verify #2 (header phrases) — OK"
        status: pass
    human_judgment: false
  - id: D6
    description: "Живое дерево app/ + scripts/ — 104 файла, 0 судимых находок; в писателе 6 сырых; реестр — ровно писатель; 152 / 68 строк 33a31ee3 на месте"
    requirement: PHONE-02
    verification:
      - kind: unit
        ref: "tests/test_application/test_phone_single_writer_gate.py#test_no_phone_write_outside_the_writer_in_the_live_tree"
        status: pass
      - kind: other
        ref: "plan 16-28 verify (OK 6 104), rows check (OK 152 68 190 84)"
        status: pass
    human_judgment: false

duration: 43min
completed: 2026-10-14
status: complete
---

# Phase 16 Plan 28: Композиция наименований колонки и вид 5 сырого SQL кодом — Summary

**`_phone_column` гейта писателя теперь композиционен. Наименование колонки номера в позиции имени индекса, поиска, конструктора или `getattr` — любой глубины — тоже запись: `MessengerAccount.__table__.c[MessengerAccount.phone.key]`, `t.c.get(M.phone.key)`, `column(M.phone.key)`. `getattr(M.phone, "key")` судится как производная. Виды 5 (а) и (б) сырого SQL судит код `_raw_sql_set_writes`: он смотрит предложение `SET` на нулевой глубине скобок, поэтому подзапрос со своим `WHERE`, литерал, комментарий или кавычки перед колонкой запись больше не прячут, а фильтр по номеру записью по-прежнему не считается. Самопроверка композицией подала 360 154 формы и нашла два класса промахов; оба закрыты циклами RED/GREEN.**

## Performance

- **Duration:** ≈43 мин
- **Started:** 2026-10-14T10:13:22Z
- **Completed:** 2026-10-14T10:56Z
- **Tasks:** 3 (плюс 2 цикла самопроверки)
- **Files modified:** 1

## Accomplishments

- Ось «как названа колонка» (WR-15):
  - `_phone_column` принимает в позиции имени любое наименование колонки номера. Это касается индекса, поиска и конструктора (`COLUMN_CONSTRUCTORS`, `COLUMN_LOOKUP_METHODS`, `text=` / `key=`) и имени у `getattr`. `getattr(X, "<const>")` читается как `X.<const>` — производная, проверяется после прямых наименований.
  - Новые таблицы и правила: `NamePosition` / `NAME_POSITIONS` (10 позиций), правило композиции, трасер скрипта дозаполнения.
  - Новые строки: 4 в `COLUMN_NAMINGS` (теперь 36), 5 в `LITERAL_FORM_CASES`, 2 в `LEGITIMATE_CASES`.
- Сырой SQL (WR-16):
  - `_raw_sql_set_writes` режет предложение `SET` до `WHERE` / `;` на нулевой глубине или до скобки, уводящей глубину ниже нуля. На нулевой глубине он ищет присваивание колонки номера и строчный конструктор в любой позиции списка.
  - `_sql_visible` скрывает литералы `'…'`, комментарии `--` / `/* */` и кавычки не из одного слова.
  - `RAW_SQL_PHONE_WRITE` несёт только (в) и (г).
  - Новые строки: правило подзапроса, 10 строк `LITERAL_FORM_CASES` и 4 строки `LEGITIMATE_CASES`.
- Предмет находки называет колонку и тогда, когда её не видно в тексте наименования: `accounts.c["pho" + "ne"]` → `(колонка 'phone')`. Запись, лежащая за 60 символами начала оператора, дописывается в предмет через `…`.
- Шапка:
  - вид 3 — композиция и `getattr`-производная;
  - вид 5 — (а) и (б) кодом, фильтр не запись, цена строгости `CASE WHEN phone = …`;
  - «ГРАНИЦА ПРЕДИКАТА» — «названа литералом» включает производную `getattr`-строкой и вложенное наименование;
  - летопись пятого круга дописана.
- Заявление шапки прежнее. Реестр — ровно писатель. Живое дерево — 0 находок.

## Task Commits

1. **Задача 1 (трасер, WR-15)**: `b6573d45` (test, RED), `17ef8eb8` (feat, GREEN)
2. **Задача 2 (WR-16)**: `62c208d5` (test, RED), `a412c3c5` (feat, GREEN)
3. **Самопроверка, цикл 1 — `where` в кавычках и в комментарии SQL**: `6506296a` (test, RED), `5e826558` (feat, GREEN)
4. **Самопроверка, цикл 2 — две находки у оператора, разрезанного склейкой**: `04ec0d50` (test, RED), `6c6bbea2` (feat, GREEN)
5. **Задача 3 (шапка)**: `5bf3e3f5` (feat)

**Plan metadata:** коммит `docs(16-28)` с этой сводкой.

## RED-улики (три совпадения + классификатор)

Каждый RED снят прогоном с `--junit-xml` в `.pytest_cache/gsd-red/` (gitignored). По каждому циклу есть строка `FAILED …::<цель>`, итоговая строка `N failed` и причинный литерал. Верб `check tdd-red-evidence` вернул `RED_EVIDENCE_OK` на всех четырёх записях (`t1`, `t2`, `c1`, `c2`).

| Цикл | Цель | Итог | Причинный литерал | Семантика |
|------|------|------|-------------------|-----------|
| Задача 1 | `test_a_planted_backfill_with_a_nested_column_naming_reddens_the_gate` и `test_every_column_naming_nested_in_every_name_position_is_a_write[table-c-index]` (и ещё 9 позиций) | `11 failed, 467 deselected` | «колонка, названная внутри другого наименования, не опознана»; «наименование колонки внутри позиции имени не опознано» | цель исполнилась, гейт вернул `[]`. Промахов глубины 1 — 1 011 из 1 080: по 102 из 108 у `table-c-index`, `table-attribute-c-index`, `inspect-columns-index`, `getattr-name`; по 99 из 108 у пяти позиций поиска и конструктора; 108 из 108 у `getattr-derivative`. Полный прогон файла: ровно 20 новых строк красны, 458 зелёных |
| Задача 2 | `test_a_raw_sql_write_after_a_subquery_in_set_is_a_write` | `1 failed, 484 deselected` | «запись колонки в SET после подзапроса с WHERE не опознана» | регулярное выражение оборвало (а) на `where` подзапроса. Полный прогон: правило и 4 новые строки форм красны, 480 зелёных |
| Цикл 1 | `test_a_literal_write_form_is_a_write[raw-sql-backtick-identifier-with-where-before-phone]` (и ещё 4 строки форм и 2 законные) | `7 failed, 266 passed` | «дала 0 находок вместо одной» | `where` внутри кавычек или комментария обрывал `SET`; законные строки с текстом `phone = …` в строке в двойных кавычках и в комментарии давали находку |
| Цикл 2 | `test_a_literal_write_form_is_a_write[raw-sql-concatenation-with-a-write-in-each-part]` | `1 failed, 189 passed` | «дала 2 находок вместо одной» | константы склейки судились каждая у себя |

## Самопроверка исполнителя (задача 3; урок 16-12, 16-17, 16-22, 16-27; О-12 (а))

Скрипт `selfcheck28.py` лежит в scratchpad и в репозиторий не коммитится. Он однопроцессный и потоковый (собрал форму → осудил → посчитал) и работает под общим `flock`. Скрипт подаёт `phone_write_offences(…, "scripts/x.py")` **композицию**, а не перечень. Под заявлением он требует ровно одну находку ожидаемого вида, предмет которой называет вызов и `phone`. Для законных форм он требует ноль находок.

- **Ось A, глубина 1:** каждое из 36 наименований `COLUMN_NAMINGS` в каждой из 10 позиций `NAME_POSITIONS`, в КАЖДОМ из 714 контекстов `COLUMN_CONTEXTS` — 257 040 форм.
- **Ось A, глубина 2:** наименование в позиции, вложенной в позицию (10 × 10 × 36 = 3 600 наименований), в первом контексте каждой из 22 пар (вид, вызов) `COLUMN_CONTEXTS` — 79 200 форм. Пары покрывают все виды находки: ключ отображения `values` / `Query.update`, `**` у `values` и модели, ключ строки у каждого исполняющего и bulk-API, `set_` при конфликте и `on_duplicate_key_update`, пару `ordered_values`, перечень `from_select`, имя у каждого писателя по имени.
- **Ось A, позиции сверх таблицы:** `.columns[…]`, `__getitem__`, `.columns.get`, `get(key=…)`, `get_property(key=…)`, `__mapper__.get_property`, `column(*[…])`, `column(**{"text": …})`, `literal_column(text=…)`, `sa.column`, `getattr` с умолчанием, `getattr(t.c, …)`, `getattr(X, "name")`, `getattr(X, "key", None)`, `t.c[…].key`, `getattr(X, "property").key` — 16 позиций × 36 × 22 = 12 672 формы.
- **Ось A, контроль:** чужая колонка (`"title"`, `Group.title`, `Group.title.key`, `getattr(Group, "title")`, `groups.c.title`) в каждой позиции и в каждой из 22 пар — 1 100 форм, все обязаны дать ноль.
- **Ось SQL (а) / (б):**
  - перебор: 15 конструкций перед колонкой × 6 голов оператора × 3 хвоста (на `ON CONFLICT` — без хвоста) × 7 написаний колонки × 3 формы записи × 2 формы Python;
  - конструкции перед колонкой: подзапрос с `WHERE`, вложенный подзапрос, литералы `'a where b'`, `'somewhere'`, `'x) where (y'`, `'it''s where'`, `CASE WHEN`, вызов функции, `EXISTS (…)`, `"a where b"`, `[a where b]`, `` `a where b` ``, `/* where */`, `-- where`, либо ничего;
  - головы оператора: `UPDATE`, нижний регистр, схема в кавычках, `AS a`, CTE с `WHERE` перед `UPDATE`, `ON CONFLICT DO UPDATE SET`;
  - хвосты: ничего, `WHERE id`, `WHERE phone`;
  - написания колонки: `phone`, `"phone"`, `` `phone` ``, `[phone]`, `phone_is_manual`, `"phone_is_manual"`, `PHONE`;
  - формы записи: присваивание, строчный конструктор первым и не первым;
  - формы Python: `execute(text(…))` и склейка `+`, разрезанная посередине;
  - итого 10 080 форм.
- **Ось SQL (в) / (г):** `INSERT … SELECT … WHERE`, CTE с `WHERE` перед `INSERT`, `INSERT OR REPLACE`, `MERGE … USING (SELECT … WHERE …)`, `COPY … FROM`, `LOAD DATA` × 2 формы Python — 12 форм.
- **Ось SQL, законные контроли (ноль обязателен):** фильтр в `WHERE`; фильтр в подзапросе `SET`; оба вместе; `SELECT`; CTE-фильтр; литерал `'phone = 1'`; строчный конструктор со значением-подзапросом, фильтрующим по номеру; `EXISTS`-фильтр; `COPY … TO`; два оператора через `;`. И фильтр по номеру после каждой из 15 конструкций. Всего 50 форм.

| Заход | HEAD, время (UTC) | Форм подано | `[]` / не та находка под заявлением | Кратных | Законные с находкой | Закрыто коммитами |
|-------|-------------------|-------------|--------------------------------------|---------|---------------------|-------------------|
| SQL 1 | `a412c3c5`, 2026-10-14 10:26 | 10 142 | 3 360 — один класс: `where` внутри идентификатора или строки в кавычках (`` `a where b` ``, `[a where b]`, `"a where b"`) или внутри комментария SQL (`/* where */`, `-- where`) перед колонкой обрывал предложение `SET` (по 224 формы на конструкцию и форму записи). Замер на SQLite 3.53.1 в памяти, своя таблица: каждый из пяти операторов пишет колонку (`+7NEW`) | 1 — `MERGE INTO messenger_accounts … ` + `… UPDATE SET phone = :p`, разрезанный склейкой: по находке у каждой константы | 0 | `6506296a` / `5e826558` (цикл 1); `04ec0d50` / `6c6bbea2` (цикл 2) |
| A 1 | `a412c3c5`, 10:27–10:33 | 337 340 (257 040 + 79 200 + 1 100 контроль) | **0** | **0** | 0 | — |
| SQL 2 | `5e826558`, ≈10:35 | 10 142 | **0** | 1 (то же, что в заходе SQL 1) | 0 | `04ec0d50` / `6c6bbea2` |
| SQL 3 | `6c6bbea2`, ≈10:37 | 10 142 | **0** | **0** | 0 | — |
| A сверх | `6c6bbea2`, 10:38 | 12 672 | **0** | **0** | — | — |
| итог | `5bf3e3f5`, 10:40–10:48 | **360 154** (SQL 10 142; A: 257 040 + 79 200 + 1 100 + 12 672) | **0** | **0** | **0** | — |

Пояснение к циклу 2: две находки у такого оператора были и на базе `922b915f`. Константа `MERGE INTO messenger_accounts` пишет по (в), а константа `… UPDATE SET phone =` — по прежней альтернативе (а). Новый промах здесь не появился. Это кратная находка под заявлением, поэтому план закрыл её циклом.

Замер записи (SQLite 3.53.1 в памяти, своя таблица, `sqlprobe28.py`). Пишут колонку: `` SET `a where b` = 1, phone = :p ``, `SET [a where b] = 1, phone = :p`, `SET note = "a where b", phone = :p` (на SQLite `"a where b"` разрешился в колонку), `SET note = 1 /* where */, phone = :p`, `SET note = 1, -- where⏎phone = :p` и строчный конструктор после подзапроса. Не пишут: `SET note = "phone = 1"` (у SQLite это строка, номер прежний) и `SET note = 'n' /* phone = :p */ WHERE id = 1`.

## Files Created/Modified

- `tests/test_application/test_phone_single_writer_gate.py` (+614 / −48 по сумме диффа плана):
  - новый код: композиционный `_phone_column`, `_naming_text`, `_raw_sql_set_writes`, `_raw_sql_write`, `_raw_sql_subject`, `_sql_visible`, `_sql_set_clause_end`, `_sql_depth_zero`, `_sql_groups`, `_SQL_*`;
  - `RAW_SQL_PHONE_WRITE` без (а) и (б); склейка судится у себя;
  - `NamePosition` / `NAME_POSITIONS`; три правила и трасер;
  - строки: 4 в `COLUMN_NAMINGS`, 15 в `LITERAL_FORM_CASES` (175 → 190), 6 в `LEGITIMATE_CASES` (78 → 84);
  - шапка.

## Decisions Made

См. `key-decisions` во frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Предмет находки не называл колонку у вложенной склейки**
- **Found during:** задача 1 (разработка правила композиции)
- **Issue:** у ключа `accounts.c["pho" + "ne"]` предмет `values({accounts.c['pho' + 'ne']: …})` не содержит `phone`, а правило композиции и прежняя матрица требуют, чтобы предмет называл колонку.
- **Fix:** `_naming_text` дописывает `(колонка 'phone')`, когда текст наименования колонку не показывает. Помощник используют ключи отображений, имя у писателей по имени и дескриптор `__set__`. Прежние предметы не изменились: в них колонка видна.
- **Committed in:** `17ef8eb8`

**2. [Rule 1 — Bug] Предмет сырого SQL обрезался до записи**
- **Found during:** задача 2
- **Issue:** предмет — первые 60 символов оператора. У формы WR-16 `phone` стоит дальше, и строка `LITERAL_FORM_CASES` (колонка в предмете) не прошла бы.
- **Fix:** `_raw_sql_set_writes` возвращает список найденных записей, а не `bool`; проверки плана работают по истинности. `_raw_sql_subject` дописывает запись через `…`, если её нет в начале; с цикла 2 — и голову (в) / (г).
- **Committed in:** `a412c3c5`, `6c6bbea2`

**3. [Rule 2 — критично для заявления] Два класса промахов самопроверки**
- **Found during:** самопроверка задачи 3, заход SQL 1
- **Issue:** `where` в кавычках и в комментарии перед колонкой (3 360 форм) и две находки у оператора, разрезанного склейкой. Оба класса — вне перечня конструкций плана, оба подпадают под заявление; формы класса 1 пишут колонку на SQLite.
- **Fix:** два цикла RED/GREEN со строками `LITERAL_FORM_CASES` (6) и `LEGITIMATE_CASES` (2).
- **Committed in:** `6506296a`…`6c6bbea2`

**4. Сужение только в сторону не-записи (ни одна прежняя строка не ослаблена)**
- Прежнее выражение (а) краснело на тексте `phone =` внутри литерала (`SET name = 'phone = 1'`), комментария и строки в двойных кавычках. Колонку такой текст не пишет. Теперь он даёт ноль; две такие формы стали строками `LEGITIMATE_CASES`.
- Находка у склейки, константа которой писала сама, переехала с константы на саму склейку (та же строка у однострочной склейки). Предмет теперь берётся из всего оператора.
- Прежние 152 / 68 строк `33a31ee3` — прежний ответ: проверка `OK 152 68 190 84`.

**5. План против замера (замер побеждает)**

| Величина | В плане | Замер |
|----------|---------|-------|
| База гейта | 440 (после 16-27) | 456 (16-27 добавил 16 строк самопроверки) |
| Гейт после задачи 1 | ≥ 462 | 478 (456 + 22) |
| Гейт после задачи 2 | ≥ 469 | 485 (478 + 7) |
| Гейт итог | ≥ 469 | 493 (+ 8 строк циклов самопроверки) |
| Форм на позицию у правила композиции | ≥ 90 | 108 (36 × 3) |
| Промахи глубины 1 до GREEN | 876 из 960 на `33a31ee3` (32 наименования) | 1 011 из 1 080 на базе плана (36 наименований) |
| `LITERAL_FORM_CASES` / `LEGITIMATE_CASES` | +9 / +4 | +15 / +6 (+6 / +2 — циклы самопроверки) |
| Quick run фазы | 1 030 на базе | 1 067 |
| `tests/test_application` | 741 на базе | 778 |

**Total deviations:** 2 правки предмета находки (Rule 1), 2 цикла самопроверки (Rule 2), 1 расхождение чисел плана с базой волны 1.
**Impact:** заявление шапки не сужено, реестр прежний, общий модуль не тронут, прежние строки на месте.

### Подстановки окружения (песочница worktree, указания оркестратора)

- **Проверки `<verify>` в виде `python -c`** исполнены той же логикой из файлов в scratchpad (`verify_t1.py`, `verify_t2.py`, `verify_t3.py`, `rows_cmp.py`). Причина — песочница отказывает тексту с подстрокой `git` в слове `legit`. Скрипту вне корня нужен `PYTHONPATH=.` (у `-c` путь `''` есть сам).
- **«Ни одна строка не потеряна»:** базу `33a31ee3` сохранила простая команда `git show` в `.pytest_cache/gate_33a31ee3.py`, и с ней сравнивал `rows_cmp.py`.
- **Отбор законных строк в `-k`:** взято `phone_mention` вместо `legitimate`. Составные команды с `git` разбиты на отдельные вызовы.
- **`graphify update .` не запускался:** его выполняет оркестратор после слияния.
- **Полная суита (`just test`) не гналась:** по указанию оркестратора её гонят после слияния волны 2.

## Issues Encountered

- `-k` с id параметра через дефис (`raw-sql-…`) не отбирал строки. Отбор сделан по имени правила с фильтрацией вывода.
- Первый запуск проверочного скрипта из scratchpad упал на `ModuleNotFoundError: tests`. Причина — нет корня worktree в `sys.path`; повтор с `PYTHONPATH=.` прошёл. На гейт это не влияет.

## Gates on the final tree (`5bf3e3f5`, под общим `flock`)

| Гейт | Итог |
|------|------|
| `tests/test_application/test_phone_single_writer_gate.py` | 493 passed |
| quick run фазы (7 путей, `16-VALIDATION.md`) | 1067 passed |
| оба гейта поимённо (приватность + писатель) | 663 passed (170 + 493) |
| `tests/test_application` | 778 passed |
| сквозные (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) | 576 passed |
| `compileall -q app main.py tests` | exit 0 |
| `scripts/prohibitions_census.py --check` | exit 0 (реестр 819 строк, биекция) |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed |
| verify задачи 1: №2 / №3 | `OK 36 10` / `OK 6 104` |
| verify задачи 2: №2 / №3 / строки | `OK` / `OK 6 104` / `OK` |
| verify задачи 3: шапка / живое дерево и реестр | `OK` / `OK` (104 файла) |
| прежние строки против `33a31ee3` | `OK 152 68` (итог 190 / 84) |
| общий модуль: `git log --format=%h b6573d45^..HEAD -- tests/phone_gate_grammar.py` | пусто (первый коммит плана `b6573d45`) |
| `tests/test_planning` | после коммита сводки — в итоговом сообщении |

## Notes for the orchestrator (wave 2, 16-29)

- `tests/phone_gate_grammar.py` план не правил, и правка грамматики связывания ему не понадобилась. Гейт по-прежнему ввозит из общего модуля только имена, созданные 16-27.
- Новых имён уровня модуля, которые могли бы пересечься с правилами паритета 16-29, нет. Добавлены `NamePosition`, `NAME_POSITIONS`, `_NESTED_NAMING_CONTEXTS`, `_raw_sql_*`, `_sql_*`, `_SQL_*`, `_naming_text`. Имя `BINDING_FORMS` по-прежнему лишь ввезено.
- После слияния: оба гейта и `tests/test_phone_gates_parity.py` на объединённом дереве; живое дерево гейта писателя обязано дать 0 и 6 сырых в писателе.

## Known Stubs

Нет.

## Threat Flags

Нет: правка только в тестовом гейте, новых поверхностей нет.

## User Setup Required

Нет.

## Next Phase Readiness

Оси «как названа колонка» и сырого SQL гэпа 1 закрыты. Вместе с 16-27 (ось «как назван API») это весь гейт писателя. Отложенных пунктов нет. 16-30 цитирует WR-15 и WR-16 коммитами `feat(16-28)`: `17ef8eb8` (WR-15), `a412c3c5` (WR-16), циклы самопроверки `5e826558` и `6c6bbea2`.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-14*

## Self-Check: PASSED

- FOUND: `tests/test_application/test_phone_single_writer_gate.py`
- FOUND (ancestor of HEAD): b6573d45, 17ef8eb8, 62c208d5, a412c3c5, 6506296a, 5e826558, 04ec0d50, 6c6bbea2, 5bf3e3f5
- TDD gate: `test(16-28)` и `feat(16-28)` присутствуют в истории, каждый `feat` предварён своим `test`
- `tests/phone_gate_grammar.py` ни одним коммитом плана не тронут
