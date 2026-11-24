---
phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
plan: 64
subsystem: planning-records
tags: [review-disposition, cr-06, cr-07, cr-08, wr-36, wr-37, wr-38, wr-39, in-23, in-24, in-25, O-25, O-26, prohibitions-census, records, truths-map]
status: complete

requires:
  - phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel
    provides: "16-57 — получатель Celery `setup_logging` (`d0c777be`); 16-58 — линия движка и суд нового объекта по значениям (`a75f30be`, `f4ee8a3b`, `db8f0d67`); 16-59 — закрепление реестра канала (`65f6f5fe`, `06f46a81`); 16-60 — стоимость, свёртка и шапка маски (`8e06c203`, `20dc5717`, `5f3cb073`, `2189a1e5`, `443be2b8`, `442aec1b`); 16-61 — сравнение у `set`, писатель без автосброса, граница защиты (`c278d839`, `c31e077a`, `39c04a34`); 16-62 — шапка писателя по рубежам и граница сырого SQL (`ab44de1a`, `77fd3de4`); 16-63 — шапка приватности о маске (`45bd5667`, `fb80ea82`)"
provides:
  - "`16-REVIEW-DISPOSITION.md`: десять находок повторного ревью раунда 10 — `fixed`; 26 вхождений хешей в обратных кавычках, 19 различных, каждый — предок `HEAD` с темой `feat(<план>)` строки; `open: 0`, `total: 72`"
  - "Пункт D6 сводки 16-56 получил исход в клетке CR-08 по решению владельца О-25 (а), свойство 6; строка WR-33 не менялась"
  - "62 прежние строки (56 `fixed`, 5 `deferred`, 1 `skipped`) и их записи frontmatter байт в байт равны `19c99ffb` (sha256 строк «69d6d4da…» на обоих деревьях), метка «(not in the current review)» у всех 62"
  - "Карта истин раунда 11 (18, 28, 131, 139, 159, 168, 180, 181, 183, 185) и таблица запретов, вердикт которых меняет партия, — в этой сводке для раунда 12 (О-26 (а))"
  - "Четыре предмета партии, не являющиеся находками ревью, записаны отдельным разделом: форма `raw-dbapi-sql-from-a-parameter` с вопросом владельцу, формы с началом вне грамматики маски, число «22 разделителя» в шапке маски, отказ 16-60 от предела серии в три разделителя"
affects: [16-review-round-11, 16-verification-round-12, "human_verification 1 (сверка вердиктов запретов)", "ревью фаз 17–20"]

actuals:
  tokens: 5522    # chars/4 по дифу записи диспозиций 2091627f..dd6f03c5 (22 088 знаков, wc -m), без этой сводки
  tasks: 2
  commits: 2      # git rev-list --count 2091627f..HEAD до коммита сводки
plan_head_before: 2091627f49062039e40f22b340ae3d3ba01b9f69
plan_head_after: dd6f03c58446e2dd7c4c66241f599ba88e5dfa7d

tech-stack:
  added: []
  patterns:
    - "Клетка `fixed` нескольких планов: в обратных кавычках — только GREEN планов, чью тему проверка допускает для строки; GREEN другого плана, коммиты теста, RED и вердикт ревизии — в «ёлочках»"
    - "Наблюдение партии о правдивости шапки, которое правит не этот план, названо в клетке исправленной находки как не исправленное и переданное ревью, а не отдельной строкой"

key-files:
  created:
    - .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-64-SUMMARY.md
  modified:
    - .planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md

key-decisions:
  - "D6 сводки 16-56 — исход по О-25 (а), свойство 6: `fixed` у WR-33 верен для собственных форм находки; соседняя дыра (держатель `setattr` с литеральным именем и запись мимо событий ORM) — CR-08, закрытая линией движка 16-58; строка WR-33 не меняется"
  - "IN-24 — `fixed`, а не `skipped`: владелец назвал исход «поправить фразу шапки защиты», исправляющий коммит — `39c04a34` (`feat(16-61)`)"
  - "Клетка WR-39 называет число «22 разделителя» в шапке маски не исправленным и переданным ревью: перечень верен, число нет (замер этого плана — 18 и U+FF0B); `app/` план не правил"
  - "Клетка CR-07 называет то, что ограничивает стоимость в построенном коде (граница по цифрам 7…15 и бюджет судов 64), и отступ 16-60 от предела «три разделителя»"
  - "Реестр запретов не изменился — коммита реестра нет: строки планов 16-57…16-64 засеял оркестратор при планировании (934 строки)"

patterns-established: []

requirements-completed: ["диспозиция-ревью-16"]  # копия поля requirements плана; `requirements.mark-complete` не запускался (заметка 5 оркестратора)

coverage:
  - id: D1
    description: "Десять находок раунда 10 — `fixed`; каждый хеш в обратных кавычках — коммит, предок `HEAD`, тема `feat(<план>)` строки; 26 вхождений, 19 различных; ни одной `open`; frontmatter равен таблице, `open: 0`, `total: 72`"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: ".pytest_cache/checks/t1_disp_1664.py (дословный `python -c` задачи 1) → OK на `d0e93f77` и после коммита"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_disp_1664.py (дословный `python -c` задачи 2) → OK 26 commits на `dd6f03c5`"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/t2_noopen_1664.py (критерий приёмки задачи 2 дословно) → OK"
        status: pass
      - kind: other
        ref: ".pytest_cache/checks/cell_hashes_1664.py → occurrences 26 distinct 19 BAD []; «ёлочки» — коммиты; `|` в клетках нет"
        status: pass
    human_judgment: false
  - id: D2
    description: "62 прежние строки и их записи frontmatter байт в байт равны `19c99ffb`; порядок строк прежний; дифф против `19c99ffb` — ровно 42 строки ndiff (21 −, 21 +)"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: ".pytest_cache/checks/t2_bytes_1664.py → BYTES OK, sha256 62 строк 69d6d4da04f9… на обоих деревьях"
        status: pass
    human_judgment: false
  - id: D3
    description: "Клетка CR-08 называет D6 сводки 16-56 и его исход по О-25 (а), свойство 6"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: ".pytest_cache/checks/t2_disp_1664.py → утверждение «D6» и «О-25 (а)» в клетке CR-08"
        status: pass
    human_judgment: true
    rationale: "Наличие слов проверено; правдивость «соседняя дыра закрыта линией движка» опирается на зонд держателей 16-62 (5 форм) и строки защиты 16-58, её судит верификатор раунда 12"
  - id: D4
    description: "Карта истин раунда 11 и таблица запретов, вердикт которых меняет партия, с хешами и именами правил"
    requirement: "диспозиция-ревью-16"
    verification: []
    human_judgment: true
    rationale: "Карта — формулировки, которые судит раунд 12 (О-26 (а)); таблица запретов — вход акта владельца `human_verification` 1; это суждение, а не замер"
  - id: D5
    description: "Реестр пересеян штатно (не изменился, 934 строки), `--check` — код 0; `tests/test_planning` — 218 passed, 2 skipped после каждого коммита учёта"
    requirement: "диспозиция-ревью-16"
    verification:
      - kind: other
        ref: "uv run python scripts/prohibitions_census.py --seed-registry / --check → «реестр не изменился: 934 строк», rc 0; «реестр: 934 строк, биекция с переписью — согласие», rc 0"
        status: pass
      - kind: unit
        ref: "uv run pytest tests/test_planning -q -p no:randomly → 218 passed, 2 skipped (на `d0e93f77` и на `dd6f03c5`)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Четыре предмета партии вне находок ревью записаны: `raw-dbapi-sql-from-a-parameter` и вопрос владельцу, формы с началом вне грамматики, число «22 разделителя», отказ от предела «три»"
    verification: []
    human_judgment: true
    rationale: "Вопрос о новом виде канала — решение владельца; дефект числа в шапке — для ревью, следующего за этой волной"

duration: 26min
completed: 2026-10-26
---

# Phase 16 Plan 64: Диспозиции повторного ревью раунда 10 и карта истин раунда 11 Summary

**Все десять находок повторного ревью раунда 10 — `fixed` по решению владельца О-25 (а). Каждую закрывают проверенные GREEN-коммиты партии 16-57…16-63: 19 различных хешей, 26 вхождений, у каждого тема `feat(<план>)` строки. Пункт D6 сводки 16-56 получил исход в клетке CR-08: соседняя дыра WR-33 — это CR-08, закрытая линией движка. 62 прежние строки байт в байт равны `19c99ffb`. Карта истин раунда 11 и таблица запретов записаны для раунда 12. Число «22 разделителя» в шапке маски перемерено (18 и U+FF0B), названо и передано ревью.**

## Performance

- **Duration:** около 26 мин (из них около 10 — обязательное чтение; время начала записано после него)
- **Started:** 2026-10-26T12:39:33Z (запись; чтение контекста — с ~12:30Z)
- **Completed:** 2026-10-26T12:56Z
- **Tasks:** 2 (трасер + 1)
- **Files modified:** 1 (`16-REVIEW-DISPOSITION.md`) и эта сводка; реестр запретов не изменился

## Accomplishments

- **CR-06 (задача 1, трасер).** Строка `fixed` с GREEN 16-57 `d0c777be` (получатель сигнала `celery.signals.setup_logging`), шапкой маски 16-60 `5f3cb073` и шапкой приватности 16-63 `45bd5667`, `fb80ea82`. В «ёлочках» стоят: коммит теста механизма «377a9b50», маска 16-52 «535c4f20», «0e74bf6c» (в воркерах её снимал Celery) и вердикт раунда 11 «553933d8». `open: 10 → 9`. После коммита гейт трасера заново прогнал `<verify>`: `OK`, затем 218 passed, 2 skipped.
- **Остальные девять (задача 2).**
  - CR-07: 16-60 `8e06c203` и шапка `5f3cb073`, `2189a1e5`, `442aec1b`. Названо, что стоимость держат граница по цифрам и бюджет судов. Отступ от предела «три разделителя» назван с числом «504».
  - CR-08: 16-58 `a75f30be`, `f4ee8a3b`, `db8f0d67` и 16-62 `ab44de1a`, `77fd3de4`. Здесь же исход D6.
  - WR-36: 16-58 `f4ee8a3b` и шапка `db8f0d67`.
  - WR-37: 16-61 `c278d839` и шапка `39c04a34`.
  - WR-38: 16-59 `65f6f5fe`, `06f46a81`.
  - WR-39: 16-60 `20dc5717` и строки границы `5f3cb073`, `443be2b8`. Названо число «22» шапки, не исправленное и переданное ревью.
  - IN-23: 16-61 `c31e077a` и шапка `39c04a34`.
  - IN-24: 16-61 `39c04a34`.
  - IN-25: 16-60 `20dc5717`.
- **Frontmatter:** десять `disposition: fixed`, `open: 0`, `total: 72`. Заголовки, тяжести и `recorded` прежние.
- **Реестр запретов:** штатный засев, файл не изменился, `--check` — код 0.

## Task Commits

1. **Задача 1 (трасер): CR-06 — `fixed`** — `d0e93f77` (`docs(16-64): record CR-06 as fixed by the Celery setup_logging receiver and the measured mask headers`)
2. **Задача 2: девять строк `fixed`, D6, прежние строки байт в байт** — `dd6f03c5` (`docs(16-64): record CR-07, CR-08, WR-36…WR-39, IN-23…IN-25 as fixed by the round-eleven batch and resolve D6 of 16-56`)

Коммита реестра нет: засев его не изменил.

**Plan metadata:** коммит этой сводки (`docs(16-64): complete …`).

## Хеши клеток (проверены до записи и после)

Каждый хеш проверен тремя способами:
- `git cat-file -e <хеш>^{commit}` завершается кодом 0;
- `git merge-base --is-ancestor <хеш> HEAD` завершается кодом 0;
- `git log -1 --format=%s` начинается с `feat(<план>)`.

До записи — `.pytest_cache/checks/t0_hashes_1664.py`: 19 GREEN и 25 прочих (коммиты теста, RED, 16-51, 16-52, вердикт раунда 11), `BAD []`. После записи — `cell_hashes_1664.py`: 26 вхождений, 19 различных, `BAD []`. Каждый хеш в «ёлочках» — тоже коммит.

| План | GREEN (полный хеш) | Тема (начало) | В строках |
|------|--------------------|---------------|-----------|
| 16-57 | d0c777beff1b042d359e76e085094a875c0e2167 | `feat(16-57): mask phone numbers in Celery worker, beat and pool children via setup_logging signal` | CR-06 |
| 16-58 | a75f30befcdf98a4450ea57c25216d12d6540d0f | `feat(16-58): refuse a phone write past ORM events at the cursor on the Engine class` | CR-08 |
| 16-58 | f4ee8a3b91ea39626a2d79080d460b2b48545a78 | `feat(16-58): judge a new account by its values in the before_flush line` | CR-08, WR-36 |
| 16-58 | db8f0d672ae97297a8594287555221a8ad58798b | `feat(16-58): name four guard lines and the measured engine-line boundary in the header` | CR-08, WR-36 |
| 16-59 | 65f6f5fefb143656af5157bd66e8592515b3d993 | `feat(16-59): pin construct texts and count per ban-channel exception (WR-38)` | WR-38 |
| 16-59 | 06f46a81475ca70d4e43372e0adf6761fed2c1ae | `feat(16-59): registry rule checks pinned construct texts and count both ways (WR-38)` | WR-38 |
| 16-60 | 8e06c203f322571924c37a4c15b27fea1ad9de78 | `feat(16-60): bound the log mask candidate and judge budget …` | CR-07 |
| 16-60 | 20dc5717b2d9e2826efd3f6b9cf38e09194289ab | `feat(16-60): fold the characters the normalizer reads in a number and mask dict messages …` | WR-39, IN-25 |
| 16-60 | 5f3cb0735a21b6207090686e3661c8e197680eb9 | `feat(16-60): name where the log mask stands and where it does not, its cost and budget …` | CR-06, CR-07, WR-39 |
| 16-60 | 2189a1e5f2067857821dc6dd77b3e138c0475912 | `feat(16-60): state the measured mask cost range in the header …` | CR-07 |
| 16-60 | 443be2b8e22111bd9c1558021e0b320eb24b8c9c | `feat(16-60): name split numbers whose start is outside the mask grammar …` | WR-39 |
| 16-60 | 442aec1baf8de4a41b5cfe97a19e58a0d93010ab | `feat(16-60): state the request-path cost range measured with the warmed-client window …` | CR-07 |
| 16-61 | c278d83952618005ac00bd25d16b4f2b28a31727 | `feat(16-61): compare the set event with the loaded value …` | WR-37 |
| 16-61 | c31e077af250eb959628c6f1701e93d312884547 | `feat(16-61): run the writer UPDATE statements without autoflush under the writer scope` | IN-23 |
| 16-61 | 39c04a3437be8d71f875dfa68ccd65cf28a841bb | `feat(16-61): name the set comparison, writer autoflush and the measured guard boundary …` | WR-37, IN-23, IN-24 (у CR-08 — в «ёлочках») |
| 16-62 | ab44de1a959286bcee6a64a2aafd9d8dc2a49c7a | `feat(16-62): name the unjudged raw DBAPI form in the predicate boundary by measurement` | CR-08 |
| 16-62 | 77fd3de473a01db027a8a525315203fbdd328824 | `feat(16-62): name the rungs of each write path in the ban section …` | CR-08 (у WR-38 — в «ёлочках») |
| 16-63 | 45bd5667ff904a2ff5f72f2dcf0e6bc482d17b85 | `feat(16-63): name where the log mask stands and where it does not in the privacy header …` | CR-06 |
| 16-63 | fb80ea82d571a5147dc7fb3ec615559a2961c45b | `feat(16-63): chronicle CR-06, WR-39, CR-07 and say the static gate's line of defence per process` | CR-06 (у CR-07, WR-38, WR-39 — в «ёлочках») |

Вхождения по строкам: CR-06 — 4, CR-07 — 4, CR-08 — 5, WR-36 — 2, WR-37 — 2, WR-38 — 2, WR-39 — 3, IN-23 — 2, IN-24 — 1, IN-25 — 1. Всего 26, различных 19. Нижняя граница приёмки — 13.

**Сверка «сводка ↔ git» (заметка 1 оркестратора).** Каждый хеш, который называют сводки 16-57…16-63 и заметка оркестратора, есть в git с той же темой. Расхождений хешей нет. Задача 2 плана 16-57 — коммит теста «377a9b50», поэтому он стоит в «ёлочках». Одно расхождение сводки с кодом, а не с git: сводка 16-60 (`provides` и D2) называет `_FOLDED_SEPARATORS` «22 разделителя + U+FF0B», а код держит 18 разделителей и U+FF0B (раздел ниже, предмет (в)).

## Шестьдесят две прежние строки — байт в байт (заметка 5 оркестратора)

`t2_bytes_1664.py` сравнивает текущий файл с `git show 19c99ffb:<путь>`. До плана файл на базе равнялся `19c99ffb`: `git diff --quiet 19c99ffb HEAD -- <файл>` вернул код 0.

- **Строки таблицы.** Прежних строк 62: 56 `fixed`, 5 `deferred` (IN-01…IN-05), 1 `skipped` (WR-35). Ни одна не отличается, порядок прежний. sha256 их конкатенации — «69d6d4da04f9c3d4cb56cbe046318274688065cf5f32494e90b154c9f4361bee» на обоих деревьях. Метка «(not in the current review)» стоит у всех 62.
- **Frontmatter.** Блоки 62 прежних находок байт в байт прежние. У десяти новых изменилась только `disposition`; заголовки и тяжести прежние (утверждение `<verify>` задачи 2).
- **Полный дифф против `19c99ffb`.** Ровно 42 строки ndiff (21 −, 21 +): десять строк таблицы, десять строк `disposition:` и `open: 10 → 0`.

## Карта истин раунда 11 (О-25 (а), О-26 (а): раунд 12 судит, делает ли защита то, что обещает её шапка)

Хеши — GREEN планов-закрывателей, проверенные выше. Правила взяты из сводок исполнителей.

| Истина | Прежняя формулировка (суть, раунд 11) | Закрывает (GREEN) | Правила, закрепляющие новую формулировку | Что судит раунд 12 |
|--------|----------------------------------------|-------------------|-------------------------------------------|--------------------|
| 18, 168 | шапка гейта писателя называет защиту и её границу; «для путей за границей статический гейт остаётся первым рубежом» | 16-58 — линия движка (`a75f30be`, `f4ee8a3b`, `db8f0d67`); 16-62 — шапка по рубежам и `RAW_SQL_BOUNDARY_FORMS` (`ab44de1a`, `77fd3de4`) | `test_a_planted_backfill_with_a_list_of_rows_is_refused_and_the_writer_writes`, `test_the_engine_line_stands_on_the_engine_class`, `test_the_guard_module_names_what_it_refuses_and_its_boundary`, `test_a_raw_sql_form_has_its_measured_static_verdict` (10 строк), `test_the_unjudged_raw_sql_form_is_named_in_the_header`, `test_the_writer_gate_header_names_the_ban_and_the_runtime_guard` (прежняя фраза — `REFUTED_FIRST_RUNG_CLAIM`, только в «Летописи CR-08») | шапка писателя называет рубежи каждого пути по замеру: у DML через движок защита первая, гейт второй; у текста SQL и сырого соединения гейт — единственный рубеж; у процесса без `app.models` и задачи из `writer_scope()` — гейт и правило входа; прежняя фраза — летописью; форма без рубежа (`raw-dbapi-sql-from-a-parameter`) названа с адресатом «ревью фаз 17–20» |
| 28, 131, 159, 180 | маска — в любом процессе с `setup_logging`, граница шапок правдива | 16-57 — Celery (`d0c777be`); 16-60 — свёртка, процессы без `setup_logging`, шапка (`20dc5717`, `5f3cb073`, `443be2b8`); 16-63 — шапка приватности (`45bd5667`, `fb80ea82`) | `test_a_celery_worker_prints_a_mask_not_a_number`, `test_celery_beat_prints_a_mask_not_a_number`, `test_a_prefork_pool_child_keeps_the_mask`, `test_the_worker_neither_hijacks_the_root_nor_redirects_print`, `test_control_without_the_receiver_the_worker_prints_the_number` (коммит теста «377a9b50»), `test_every_character_the_normalizer_reads_in_a_number_is_folded_or_named`, `test_the_processes_without_setup_logging_are_measured_and_named`, `test_the_masking_module_names_what_it_masks_and_its_boundary`, `test_the_privacy_gate_header_names_the_measured_mask_boundary`, `test_the_privacy_gate_header_names_the_ban_and_the_runtime_mask` | маска стоит в вебе, воркерах Celery, `beat` и дочерних процессах пула — правила над настоящими процессами; граница названа таблицами модулей маски (`PROCESSES_WITHOUT_SETUP_LOGGING` — 5, `MASK_BOUNDARY_CHARACTERS` — 9, `MASK_BOUNDARY_SUBSTRINGS` — 11), шапка приватности сверена с ними при вызове; держатели «только маски» сказаны по процессам — в процессах без `setup_logging` их не держит ничто |
| 139, 181 | запись вне писателя отказывает на исполнении, граница защиты правдива | 16-58 (`a75f30be`, `f4ee8a3b`, `db8f0d67`); 16-61 — сравнение у `set`, автосброс, `GUARD_BOUNDARY_WRITES` (`c278d839`, `c31e077a`, `39c04a34`) | `test_a_foreign_write_is_refused` (34 строки), `test_a_legitimate_write_passes` (16), `test_a_write_whose_values_cannot_be_judged_is_refused_closed` (3), `test_a_new_account_is_judged_by_its_values_before_the_flush`, `test_a_foreign_pending_change_is_not_flushed_under_the_writer_scope`, `test_a_named_boundary_of_the_guard_is_measured_and_named` (4 строки) | пути DML через движок (`bulk_*`, соединение, Core, upsert, лёгкая таблица) отказывают на курсоре; законные пути, включая `merge` неизменного аккаунта, проходят; граница защиты — строки исполнения `GUARD_BOUNDARY_WRITES`, каждую называет шапка; цена — отказ в закрытую |
| 183 | шапки правдивы об обещании и границе | 16-58 (`db8f0d67`), 16-59 (`06f46a81` — граница закрепления в шапке «ИСКЛЮЧЕНИЯ»), 16-60 (`5f3cb073`, `2189a1e5`, `443be2b8`, `442aec1b`), 16-61 (`39c04a34`), 16-62 (`ab44de1a`, `77fd3de4`), 16-63 (`45bd5667`, `fb80ea82`) | правила шапок из строк выше; `test_every_dynamic_construct_exception_pins_its_construct_texts` | каждая шапка называет границу, закреплённую правилом исполнения или замера. **Известный дефект для этой истины:** шапка `app/services/log_masking.py` (строка 31) называет «22 разделителя», а сворачивает 18 и U+FF0B — перечень верен, число нет (предмет (в) ниже); раунд 12 судит его как неправду шапки |
| 185 | стоимость маски ограничена | 16-60 (`8e06c203`; шапка `5f3cb073`, `2189a1e5`, `442aec1b`) | `test_a_long_split_field_is_masked_in_bounded_time` (8 000 знаков в 0,25 с), `test_a_long_split_request_path_is_logged_in_bounded_time` (1 801 и 7 999 знаков через `setup_logging` и `RequestIdMiddleware`), `test_the_mask_judges_at_most_the_budget_per_field`, `test_beyond_the_budget_a_candidate_is_masked_closed` | стоимость ограничена так, как построено: кандидат — 7…15 цифр с нарастающим счётом; края цепочки считаются один раз на поле; бюджет `MASK_JUDGMENT_BUDGET` (64) судов на вызов, сверх него — отказ в закрытую (T-16-140). Длина серии разделителей НЕ ограничена: предел «три», записанный в плане 16-60, напечатал бы «504» номера, которые база маскировала. Угроза названа (T-16-137) |

**Advisory 1 раунда 11 — названная цена, не дефект.** Плоское толкование гейта писателя по последнему звену: `f = set_committed_value` и `self.f = logger.info` дают находку и на вызове журнала. Это названная цена шапки писателя. Партия предикаты не правила. Адресат — ревью фаз 17–20 (О-26 (а)), починки нет.

**Форма `raw-dbapi-sql-from-a-parameter` — названная граница.** Запись через сырое соединение DBAPI с текстом SQL из параметра: предикат 0, канал 0, мимо движка. Она названа пунктом (6) «ГРАНИЦЫ ПРЕДИКАТА» шапки гейта писателя (16-62, `ab44de1a`). Адресат тот же — ревью фаз 17–20. Живое дерево сырого соединения не использует.

## Запреты, вердикт которых меняет партия (для `human_verification` 1 — сверка владельцем)

| Запрет | Вердикт раунда 11 | Что меняет партия (GREEN) |
|--------|-------------------|---------------------------|
| 16-04 №1 (номер не в журнал даже маской) | соблюдён в живом дереве; средство неполно (CR-06) | маска стоит в Celery, `beat` и пуле — 16-57 `d0c777be`; граница по замеру — 16-60 `5f3cb073`, 16-63 `45bd5667`, `fb80ea82` |
| 16-06 №1 (нет записи в обход писателя) | соблюдён в живом дереве; средство неполно (CR-08) | линия движка на курсоре — 16-58 `a75f30be`, `f4ee8a3b`; рубежи по путям — 16-62 `77fd3de4` |
| 16-51 №3 (не отказывать законной записи) | соблюдён в живом дереве (WR-37) | `merge` неизменного аккаунта проходит — 16-61 `c278d839`; цена `merge` поверх истёкшей копии названа (`39c04a34`) |
| 16-52 №2 (процессор не роняет запись) | соблюдён по букве (CR-07 — время) | стоимость ограничена, сверх бюджета — отказ в закрытую — 16-60 `8e06c203` |
| 16-54 №2, 16-55 №2 | соблюдены по букве | шапки правдивы по замеру — 16-62 `ab44de1a`, `77fd3de4`; 16-63 `45bd5667`, `fb80ea82` |

Прочие запреты фазы партия не затрагивает.

## Предметы партии, не являющиеся находками ревью (заметка 2 оркестратора)

Строк диспозиции для них нет, и ID находок им не присваиваются.

**(а) Форма без рубежа `raw-dbapi-sql-from-a-parameter` и вопрос владельцу (16-62).** Предикат 0, канал 0. Названа пунктом (6) границы шапки гейта писателя с адресатом «ревью фаз 17–20». Сводка 16-62 поднимает **вопрос владельцу: оправдывает ли эта форма новый вид в перечне канала** (`DYNAMIC_CONSTRUCT_KINDS`, О-23 (а), свойство 1). Этот план вопроса не решает. Это решение владельца, а не отложенная работа.

**(б) Формы с началом вне грамматики маски (16-60).** `8)999)123)45)67` и `(999123) 45 67` нормализатор читает как номер, а маска не маскирует — и на базе тоже. В корпусе 16-60 таких голых форм 100 (`8)…`, `8))…`, `(dddddd) …`). 16-60 назвал их строками `MASK_BOUNDARY_SUBSTRINGS` (`eight-before-closing-bracket`, `six-digit-bracket-start`) и пунктом границы шапки (`443be2b8`). Грамматику ASCII он не расширял: расширение изменило бы ответ маски на ASCII (сверка 20 000 строк). Шапка приватности называет обе формы (16-63).

**(в) Шапка маски называет «22 разделителя», а сворачивает 18 и U+FF0B.** Нашёл 16-63, подтвердил оркестратор на слитом дереве, перемерил этот план (`.pytest_cache/checks/fold_count_1664.py`, только чтение):
- строка 31 `app/services/log_masking.py`: «22 разделителя — пробелы U+00A0 (NBSP), U+200B, U+2060, U+3000, тире U+00AD, U+2010, …»;
- `_FOLDED_SEPARATORS` держит 19 записей: 18 разделителей (U+00A0, U+200B, U+2060, U+3000, U+00AD, U+2010, U+2011, U+2012, U+2013, U+2014, U+2015, U+2053, U+2212, U+223C, U+30FC, U+FF0D, U+FF08, U+FF09) и U+FF0B;
- остальные четыре из 22 замера планирования — U+FF0E, U+FF0F, U+FF3B, U+FF3D — знаки границы `MASK_BOUNDARY_CHARACTERS` (9 знаков), они не сворачиваются.

Перечень верен, число неверно. Это неправда шапки, ровно тот класс, который судит раунд 12. То же число стоит в сводке 16-60 (`provides`, D2). Файл вне файлов этого плана, `app/` не правился. Адресат — ревью кода, следующее за этой волной. Клетка WR-39 называет дефект не исправленным и переданным ревью.

**(г) 16-60 отступил от плана: серии разделителей не ограничены тремя.** Предел «не больше трёх разделителей подряд» напечатал бы 504 номера, которые база маскирует и нормализатор читает (`+7    999    123    45    67` и т. п.; корпус 16-60, серия > 3: 572 читаемые формы, база маскирует 504). Стоимость держат граница по цифрам (7…15), предвычисление краёв и бюджет судов 64 с отказом в закрытую. Так записаны клетка CR-07 и строка истины 185.

## Реестр запретов (заметка 5 оркестратора)

- `uv run python scripts/prohibitions_census.py --seed-registry` → «реестр не изменился: 934 строк», код 0. Строки планов 16-57…16-64 засеял оркестратор при планировании; у фазы 16 — 193 элемента.
- `--check` → «реестр: 934 строк, биекция с переписью — согласие», код 0.
- Шапку реестра и формулировки запретов планов 16-01…16-64 я не правил.

## Гейты на итоговом дереве (`dd6f03c5`, под общим `flock`)

| Прогон | Итог | База |
|--------|------|------|
| `<automated>` задачи 1 (`t1_disp_1664.py`) | `OK` (после коммита `d0e93f77` — повтор гейта трасера `OK`) | — |
| `<automated>` задачи 2 (`t2_disp_1664.py`) | `OK 26 commits` | ≥ 13 |
| ни одной `open` (`t2_noopen_1664.py`) | `OK` | — |
| байт в байт против `19c99ffb` (`t2_bytes_1664.py`) | `BYTES OK` | — |
| `prohibitions_census.py --check` | код 0, 934 строки | код 0, 934 |
| `tests/test_planning` (до каждого коммита учёта и после него) | **218 passed, 2 skipped** (на `d0e93f77` и на `dd6f03c5`) | 218 passed, 2 skipped |
| `tests/test_planning/test_plan_prohibitions_census.py` | 110 passed | 110 |
| оба гейта и паритет | 1161 passed | — |
| живые деревья `-s -k "live_tree or live_trees or dynamic_construct_in_the"` | 5 passed. Приватность — «app: файлов 102, вызовов 227, scripts: файлов 4, вызовов 68, max_worker: файлов 2, вызовов 93; находок 0». Канал приватности — 108 файлов, 0 находок. JS — «wa_worker: файлов 1, вызовов 68; находок 0». Канал писателя — 106 файлов, 0 находок | те же |
| набор фазы (12 путей `<verification>`) | **1770 passed** | — |
| сквозные гейты (`test_htmx_post_pairs`, `test_htmx_gates`, `tests/test_templates`, `test_declared_invariants`) | **576 passed** | 576 |

Код план не трогал. Прогоны подтверждают, что после волн 1–3 сдвигов нет. Полный `just test` не запускался: его гонит пост-мерж гейт оркестратора.

## Files Created/Modified

- `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md`:
  - десять строк таблицы;
  - десять записей `disposition` во frontmatter;
  - `open: 0`.
- `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-64-SUMMARY.md` — эта сводка.
- Реестр запретов не изменился.

## Decisions Made

- **В клетках названо больше GREEN, чем минимум `<scope_note>`, и только с допустимыми темами.**
  - CR-07: шапка `5f3cb073` и два уточнения замером, `2189a1e5` и `442aec1b`.
  - WR-36: шапка `db8f0d67`, где снят довод «оператора не порождает».
  - WR-37, IN-23: шапка `39c04a34`.
  - WR-39: строки границы `5f3cb073` и `443be2b8`.
  - Каждый из них закрывает часть истины «шапка правдива».
- **GREEN чужого плана — в «ёлочках».**
  - В строке CR-08 — `GUARD_BOUNDARY_WRITES` 16-61 «39c04a34».
  - В строках CR-07 и WR-39 — летописи шапки приватности 16-63 «fb80ea82».
  - В строке WR-38 — закрепление, названное в шапках 16-62 «77fd3de4» и 16-63 «fb80ea82».
- **D6.** Исход записан словами решения владельца О-25 (а), свойство 6. Строку WR-33 план не трогал: проверка байт в байт это подтверждает.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - честность записи] Клетка WR-39 называет не исправленное число «22 разделителя»**
- **Found during:** задача 2 (сверка со сводками 16-60 и 16-63 и заметкой 2 (в) оркестратора)
- **Issue:** форма клетки WR-39 в `<scope_note>` («свёртка знаков…; строки границы») не говорила, что шапка маски называет неверное число свёрнутых разделителей. Без оговорки `fixed` читался бы как «шапка правдива целиком».
- **Fix:** клетка называет число, замер (18 и U+FF0B) и то, что дефект не исправлен и передан ревью. `app/` не правился. Новой строки и ID нет.
- **Files modified:** `16-REVIEW-DISPOSITION.md`
- **Verification:** `t2_disp_1664.py` → `OK 26 commits`; `cell_hashes_1664.py` → `BAD []`, `|` в клетках нет
- **Committed in:** `dd6f03c5`

### Подстановки исполнения (по требованию оркестратора)

- Каждая `uv run python -c "…"` из `<verify>` и `<acceptance_criteria>` записана дословно в файлы `.pytest_cache/checks/`: `t1_disp_1664.py`, `t2_disp_1664.py`, `t2_noopen_1664.py`. Исполнены они `PYTHONPATH=. uv run python <файл>` с той же логикой и теми же `assert`. Сверх плана: `t0_hashes_1664.py`, `cell_hashes_1664.py`, `t2_bytes_1664.py`, `fold_count_1664.py` (только чтение).
- Девять строк задачи 2 правил сценарий `.pytest_cache/checks/apply_1664.py`, а не Edit по строке. Так меняются ровно названные строки, их записи `disposition` и `open:`. Каждая замена утверждает единственность совпадения.
- Журнал базы плана — `.pytest_cache/gsd-plan-head-before-16-64`, а не каталог git рабочего дерева: тот лежит под `/source/broadcaster/.git` (заметка 3). `commits` измерен `git rev-list --count 2091627f..HEAD` = 2.
- Песочница отказала в составной команде с подстановкой `$(…)` вокруг git. Команды разбиты на простые.
- **Честная оговорка о цепочке задачи 1.** `pytest … | tail -3 && git commit` передавал дальше код `tail`, а не pytest. Прогон был зелёным (218 passed, 2 skipped), поэтому коммит законен. Но защита `&&` в той команде не действовала. С задачи 2 все цепочки идут под `set -o pipefail`.
- `uv run` создал `.venv` в рабочем дереве; каталог gitignored.
- `graphify update .` не запускался: кода план не менял, граф пересобирает оркестратор.
- В `.planning/WINDOWS.md` ничего не записано (заметка 5): мои записи — только диспозиции, реестр и эта сводка. Предметы (а)–(г) переданы этой сводкой и финальным сообщением.

---

**Total deviations:** 1 auto-fixed (Rule 2 — честность клетки) плюс названные подстановки.
**Impact on plan:** нет расширения объёма. Файл правок — ровно `16-REVIEW-DISPOSITION.md`; реестр не изменился.

## Issues Encountered

None.

## Known Stubs

Нет.

## Threat Flags

Нет. Новой поверхности нет: изменён только журнал диспозиций.
- T-16-147 закрыта проверками выше: 72 строки, хеши-предки с темой `feat(<план>)`, D6, байт в байт.
- T-16-148 закрыта штатным засевом и `--check` с кодом 0.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Все 72 находки ревью фазы 16 разобраны. Партия раунда 11 записана целиком.
- Следующее:
  - ревью кода после волны: предмет (в) — число «22» в шапке маски;
  - полный `just test` (около 46 мин, таймаут 5400 с);
  - `/gsd-verify-work` финального раунда 12 по карте истин выше;
  - `/gsd-validate-phase 16` — строки партии раунда 11 в `16-VALIDATION.md` стоят `⬜ pending`.
- **Владельцу:** вопрос (а) — новый вид канала для `raw-dbapi-sql-from-a-parameter`. Таблица запретов выше — вход `human_verification` 1.

---
*Phase: 16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel*
*Completed: 2026-10-26*

## Self-Check: PASSED

- FOUND: `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-REVIEW-DISPOSITION.md`, `.planning/phases/16-hranenie-nomera-normalizatsiya-i-edinyy-pisatel/16-64-SUMMARY.md`
- FOUND (ancestors of HEAD): `d0e93f77`, `dd6f03c5`; все 19 GREEN клеток (таблица хешей выше)
