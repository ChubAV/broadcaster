---
phase: quick-260825-hnf-recompress-legacy-attachments
plan: 01
subsystem: uploads
tags: [pillow, aiobotocore, s3, maintenance-script, image-compression, thumbnails]

requires:
  - phase: quick-260825-d2x (issue #40)
    provides: "prepare_upload, DELIVERY_MAX_EDGE, THUMB_MAX_EDGE, MAX_DECODED_PIXELS, thumb_key — сжатие и миниатюра на маршруте загрузки"
  - phase: issue #39
    provides: "сужение приёма до JPEG/PNG и правило «расширение живёт внутри ключа»"
provides:
  - "scripts/recompress_attachments.py — разовый скрипт обслуживания: dry-run по умолчанию, --apply для записи"
  - "app/services/s3.py: read_object_head (диапазонное чтение + полный размер), read_object, object_exists, put_object_bytes, open_s3_client"
  - "app/services/images.py: probe_image и rebuild_stored_image — соседний вход БЕЗ смены формата"
  - "justfile: recompress-attachments и prod-recompress-attachments"
affects: [uploads, storage-cleanup, telegram-delivery, attachment-history]

actuals:
  tokens: 31000
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Соседний вход в модуль вместо переписывания существующего: prepare_upload остался нетронут, рядом появился rebuild_stored_image с другим контрактом формата"
    - "Дисциплина трафика: диапазонное чтение заголовка решает, стоит ли выкачивать тело"
    - "Прохибиции проверяются чтением ИСХОДНИКА, а не отсутствием прохода по ветке"
    - "Двухуровневая запись в хранилище: примитив над открытым клиентом + обёртка, открывающая клиента"

key-files:
  created:
    - scripts/recompress_attachments.py
    - tests/test_scripts/__init__.py
    - tests/test_scripts/test_recompress_attachments.py
  modified:
    - app/services/s3.py
    - app/services/images.py
    - tests/test_services/test_s3.py
    - tests/test_services/test_images.py
    - justfile

key-decisions:
  - "D-1 исполнено дословно: единственный источник ключей — Ad.images; обратного разбора публичного адреса в ключ в коде нет ни одной строкой, SKIP_REASONS содержит ровно четыре причины"
  - "Формат существующего объекта сохраняется всегда (target_format = probe.format): PNG остаётся PNG даже без альфы — прямая противоположность prepare_upload на том же входе"
  - "Пережатый объект пишется только при строгом уменьшении; иначе учитывается в not_shrunk, который НЕ входит в разбор пропусков"
  - "Имя примитива записи — put_object_bytes, а не put_object: второе затенило бы одноимённый метод клиента aiobotocore в том же модуле"
  - "Отсутствие объекта — None/False; любой другой отказ хранилища поднимается наружу, иначе недоступный бакет отчитался бы строкой «работы нет»"

patterns-established:
  - "Протокол AttachmentStore: ядро прогона не знает, работает оно с боевым клиентом или с двойником в памяти — и удаляющего метода в протоколе нет по построению"
  - "Журналы двойника (head_reads / reads / puts) как предмет утверждений о ДЕЙСТВИИ там, где счётчики отчёта недоказательны"

requirements-completed: [TODO-LEGACY-IMAGES]

coverage:
  - id: D1
    description: "Объект сверх предела доставки пережимается под ТЕМ ЖЕ ключом, его миниатюра ложится под thumb_key; формат и расширение не меняются"
    requirement: "TODO-LEGACY-IMAGES"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_recompress_attachments.py#test_an_oversized_attachment_is_rebuilt_under_the_same_key"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_images.py#test_a_stored_png_without_alpha_is_rebuilt_as_png"
        status: pass
    human_judgment: false
  - id: D2
    description: "Разбор пропусков состоит РОВНО из четырёх причин (D-1), отчёт рендерится обходом SKIP_REASONS, неподдерживаемый формат назван примерами ключей"
    requirement: "TODO-LEGACY-IMAGES"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_recompress_attachments.py#test_the_skip_breakdown_has_exactly_four_reasons"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_recompress_attachments.py#test_an_unsupported_format_survives_the_run_untouched"
        status: pass
    human_judgment: false
  - id: D3
    description: "Дисциплина трафика: полностью пропущенный объект стоит одного диапазонного чтения и ни одного полного; объект сверх потолка пикселей не выкачивается; короткий заголовок даёт один откат на полное чтение"
    requirement: "TODO-LEGACY-IMAGES"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_recompress_attachments.py#test_a_skipped_object_costs_one_ranged_read_and_no_full_read"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_recompress_attachments.py#test_an_image_over_the_pixel_ceiling_is_skipped_without_a_full_read"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_recompress_attachments.py#test_a_short_header_falls_back_to_one_full_read"
        status: pass
    human_judgment: false
  - id: D4
    description: "Идемпотентность: второй подряд прогон с --apply не выполняет ни одной записи в хранилище"
    requirement: "TODO-LEGACY-IMAGES"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_recompress_attachments.py#test_a_second_apply_run_writes_nothing"
        status: pass
    human_judgment: false
  - id: D5
    description: "Прохибиции: скрипт ничего не удаляет, не ходит в мессенджеры, не закрепляет транзакцию; Ad.images и SendLog.ad_images равны до и после прогона"
    requirement: "TODO-LEGACY-IMAGES"
    verification:
      - kind: unit
        ref: "tests/test_scripts/test_recompress_attachments.py#test_the_script_source_declares_no_destructive_storage_call"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_recompress_attachments.py#test_the_run_never_touches_the_database"
        status: pass
      - kind: unit
        ref: "tests/test_scripts/test_recompress_attachments.py#test_the_script_never_commits_a_transaction"
        status: pass
    human_judgment: false
  - id: D6
    description: "Боевой сухой прогон: оператор читает отчёт (объём до/после, экономия в процентах, четыре счётчика, примеры ключей неподдерживаемого формата) и по нему принимает решение о запуске с записью"
    verification: []
    human_judgment: true
    rationale: "Перезапись объекта на месте необратима (T-QH-02), а строка «формат не поддерживается» с примерами ключей может оказаться первым обнаружением объявлений, которые уже сегодня не отправляются в Telegram. Решение о --apply принадлежит человеку и принимается по отчёту, а не заранее. Прогон против боевого бакета исполнителю прямо запрещён."

duration: 26min
completed: 2026-08-25
status: complete
---

# Quick 260825-hnf: Скрипт обслуживания «сжать и создать превью» Summary

**Вложения, загруженные до issue #40, теперь можно пережать и снабдить миниатюрами задним числом — не сменив ни одного ключа, ни одного расширения и не тронув ни одной строки в базе.**

## Performance

- **Duration:** ~26 min
- **Tasks:** 3 из 3
- **Files modified:** 8 (3 создано, 5 изменено)
- **Tests added:** 34 (22 на скрипт, 10 на новые чтения хранилища, 12 на соседний вход images.py — из них 2 параметризованы)

## Accomplishments

- **Разовый скрипт обслуживания** `scripts/recompress_attachments.py`: сухой прогон по умолчанию, запись только по `--apply`, отчёт, по которому решение о записи можно принять, а не угадать.
- **Два независимых решения по каждому объекту** — пережимать тогда и только тогда, когда длинная сторона больше `DELIVERY_MAX_EDGE`; строить миниатюру тогда и только тогда, когда `thumbs/{ключ}` отсутствует. Обе половины независимости закрыты отдельными тестами.
- **Дисциплина трафика**: за пропущенный объект платятся только первые 64 КиБ. Полное тело читается лишь у тех, по кому решена работа; объект сверх потолка пикселей не выкачивается вовсе.
- **Соседний вход в `app/services/images.py`**, не трогающий `prepare_upload`: формат существующего объекта сохраняется, потому что расширение живёт внутри уже розданного ключа.
- **Единственный писатель в S3 не изменил поведения**: `test_upload_file_to_s3` остался зелёным без единой правки, хотя тело `upload_file_to_s3` теперь делегирует новому примитиву.

## Task Commits

1. **Task 1 (tracer, TDD): сквозной путь — пережатый объект под тем же ключом плюс миниатюра**
   - `15adf3b` (test — RED)
   - `55516f3` (feat — GREEN)
2. **Task 2 (TDD): отчёт — четыре причины пропуска, группа ошибок, дисциплина трафика** — `1da8457` (test)
3. **Task 3 (TDD): идемпотентность, прохибиции, модульное покрытие новых чтений** — `16d68d5` (test)

_Реализация задач 2 и 3 приземлилась в коммите задачи 1 — разбор в «Deviations» ниже._

## Files Created/Modified

- `scripts/recompress_attachments.py` — ядро прогона: `AttachmentStore` (протокол из четырёх методов, удаляющего среди них нет по построению), `S3AttachmentStore` над одним открытым клиентом, `collect_attachment_keys`, `recompress_attachments`, `Report`, `format_report`, `main`.
- `app/services/s3.py` — `HEAD_READ_BYTES`, `ObjectHead`, `open_s3_client`, `put_object_bytes`, `read_object_head`, `read_object`, `object_exists`; `upload_file_to_s3` переведён на делегацию без изменения сигнатуры.
- `app/services/images.py` — `ImageProbe`, `probe_image`, `RebuiltImage`, `rebuild_stored_image`. Существующие абзацы шапки и `prepare_upload` не тронуты.
- `justfile` — `recompress-attachments` и `prod-recompress-attachments`, оба передают аргументы насквозь.
- `tests/test_scripts/test_recompress_attachments.py`, `tests/test_scripts/__init__.py` — новый пакет тестов.
- `tests/test_services/test_s3.py` — покрытие новых чтений на двойнике клиента; изменена ровно одна существующая строка (список импортов), тело `test_upload_file_to_s3` не тронуто.
- `tests/test_services/test_images.py` — 12 тестов на соседний вход, включая именованную регрессию `test_a_stored_png_without_alpha_is_rebuilt_as_png`.

## Decisions Made

- **`bytes_before` / `bytes_after` накапливаются только по объектам, ВЗЯТЫМ В РАБОТУ.** Складывать в «до» вес пропущенных объектов значило бы показать экономию в долях процента от всего бакета и утопить в ней настоящий результат. У объекта, чья пересборка не уменьшила его, в «после» идёт исходный размер.
- **Вес миниатюр — отдельная строка отчёта, а не вычет из экономии.** Миниатюра есть новые байты в хранилище; сложить её с экономией значило бы отчитаться прибылью за расход.
- **Потолок примеров неподдерживаемого формата (`UNSUPPORTED_EXAMPLES_LIMIT = 10`) назван в самом тексте отчёта**, чтобы усечённый список не читался как полный.
- **Пустой объект отличён от отсутствующего.** Диапазон `bytes=0-65535` на нулевой длине неудовлетворим, и хранилище отвечает отказом `InvalidRange`; `read_object_head` превращает его в `ObjectHead(b"", 0)`, а не в `None`.

## Deviations from Plan

### 1. [Rule 3 — Порядок исполнения] Реализация задач 2 и 3 приземлилась в коммите задачи 1

- **Found during:** Task 1 (tracer).
- **Issue:** План отводил задаче 1 усечённый `Report` (`scanned`, `processed`, `bytes_before`, `bytes_after`, `thumb_bytes_added`), а полный разбор пропусков и группу ошибок — задаче 2. Я написал `SKIP_REASONS`, `skips`, `unsupported_examples`, `not_shrunk` и `errors` сразу в задаче 1, потому что порядок решений в ядре без них не выражается: ветка «пропустить и не читать тело» есть ровно то место, где счётчик и выставляется, и разложить одну ветку на два коммита можно было бы только заведением временной заглушки.
- **Fix:** Ничего не откатывалось. Коммиты задач 2 и 3 несут ТЕСТЫ, которые это поведение закрепляют; RED-фаза у них поэтому оказалась частичной — из одиннадцати тестов задачи 2 при первом прогоне упал один (см. пункт 2), остальные зазеленели сразу.
- **Impact:** Дисциплина атомарных коммитов сохранена, дисциплина RED→GREEN — частично нарушена для задач 2 и 3. Поведение при этом не осталось непроверенным: каждое утверждение задач 2 и 3 имеет свой тест, и каждый тест был прогнан.

### 2. [Rule 1 — Bug] Тест `test_a_rebuilt_object_that_grew_is_not_written` ссылался на неимпортированное имя

- **Found during:** Task 2.
- **Issue:** Двойник кодировщика строил `script.RebuiltImage`, но скрипт `RebuiltImage` не импортирует — ему хватает того, что возвращает `rebuild_stored_image`. Внутри двойника поднимался `AttributeError`, его перехватывала защита «прогон не падает на одном ключе», и тест падал с пустым журналом записей вместо ожидаемой одной.
- **Fix:** `RebuiltImage` импортирован в тест из `app.services.images` напрямую; в тест добавлено утверждение `report.errors == []`, чтобы этот класс отказа впредь называл себя, а не маскировался под «ничего не записано». Импортировать `RebuiltImage` в сам скрипт ради теста было бы неиспользуемым импортом.
- **Files modified:** `tests/test_scripts/test_recompress_attachments.py`.
- **Committed in:** `1da8457`.

### 3. [Rule 2 — Missing coverage] Тесты соседнего входа положены в `tests/test_services/test_images.py`

- **Issue:** `<files>` задачи 1 и `files_modified` во frontmatter этот файл не перечисляют, но `<behavior>` требует именованную регрессию `test_a_stored_png_without_alpha_is_rebuilt_as_png` на `rebuild_stored_image`, а `<verify>` задачи 1 прогоняет именно `tests/test_services/test_images.py`.
- **Fix:** Тесты соседнего входа дописаны отдельным разделом в конец существующего файла — рядом с `test_png_without_real_alpha_becomes_jpeg`, противоположностью которого новая регрессия и является. Соседство здесь несёт смысл: два теста на одном входе с разными ожиданиями читаются как расхождение №1, а разнесённые по файлам читались бы как противоречие.

---

**Total deviations:** 3 (1 порядок исполнения, 1 auto-fixed bug, 1 добавленное покрытие). Ни одна прохибиция `<non_goals>` не смягчена, ни одно locked decision не пересмотрено.

## Issues Encountered

- **Отчёт `git diff` по `pyproject.toml` и `uv.lock` пуст** — новых установок пакетов не было, как и предсказывал `<package_legitimacy>`.
- **Полная суита прогнана целиком: `2280 passed, 1 failed` за 23 мин 47 с.** Единственное падение —
  `tests/test_planning/test_state_progress_matches_roadmap.py::test_the_machine_readable_progress_is_derived_from_the_roadmap`,
  и оно ПРЕДСУЩЕСТВУЮЩЕЕ и вне объёма задачи: тест сверяет поле `progress` во
  frontmatter `.planning/STATE.md` (записано 110/110) со счётом, выводимым из отметок
  `.planning/ROADMAP.md` (выводится 0/0). Ни одного из этих двух файлов задача не
  касалась — `git diff 91572b4..HEAD -- .planning/` показывает единственный файл, эту
  самую сводку. Чинить его исполнителю прямо запрещено условиями задачи («Do NOT modify
  or commit `.planning/STATE.md`», «Do NOT update `.planning/ROADMAP.md`»), поэтому
  падение здесь НАЗВАНО, а не устранено: расхождение принадлежит оркестратору, который
  обновляет `STATE.md` после слияния.

## Verification

| Проверка | Команда | Результат |
|---|---|---|
| Скрипт, соседний вход, хранилище | `uv run pytest tests/test_scripts/ tests/test_services/test_s3.py tests/test_services/test_images.py -q` | 75 passed |
| Маршрут загрузки и форма ключа | `uv run pytest tests/test_routes/test_uploads.py tests/test_services/test_image_keys.py -q` | 59 passed |
| Потребители адреса объекта | `uv run pytest tests/test_pages/test_attachment_history_integrity.py tests/test_templates -q` | 56 passed |
| Четыре причины, не пять | `uv run python -c "... assert len(m.SKIP_REASONS) == 4"` | ok |
| Рецепты объявлены | `test "$(grep -cE '^(prod-)?recompress-attachments ' justfile)" = "2"` | ok |
| Справка скрипта | `uv run python scripts/recompress_attachments.py --help` | ok |
| Байт-компиляция | `uv run python -m compileall -q app main.py tests scripts` | ok |
| Зависимости не тронуты | `git diff --quiet -- pyproject.toml uv.lock` | ok |
| Полная суита | `uv run pytest tests/ -q` | 2280 passed, 1 failed (падение предсуществующее и вне объёма — разбор в «Issues Encountered») |

## Known Stubs

Нет. Все ветки скрипта реализованы и покрыты; заглушек, заготовок и `TODO` в новом коде нет.

## Threat Flags

Новой поверхности сверх той, что разобрана в `<threat_model>` плана, не появилось. Отдельно стоит назвать одно наблюдение, которое план предвидел, а прогон сделает измеримым: строка отчёта «формат не поддерживается» с примерами ключей есть ОТДЕЛЬНЫЙ латентный дефект — такие объявления уже сегодня не уходят в Telegram, и этот прогон может обнаружить их первым. Реакция на них — не задача этого скрипта.

## User Setup Required

**Требуется действие оператора перед любым запуском с записью** (`<human-check>` задачи 3, не выполнен исполнителем намеренно — прогон против боевого бакета исполнителю запрещён):

1. Запустить сухой прогон на боевых настройках: `just recompress-attachments`
2. Прочитать отчёт целиком: число объектов к обработке, объём до и расчётный после, экономию в процентах, четыре счётчика пропуска и примеры ключей неподдерживаемого формата.
3. Только после этого — и только если отчёт устраивает — запустить `just recompress-attachments --apply` (или `just prod-recompress-attachments --apply` внутри боевой композиции).

Перезапись объекта на месте НЕОБРАТИМА: прежних байтов после неё нет (T-QH-02). Скрипт при этом ничего не удаляет и в базу не пишет, поэтому цена ошибки ограничена качеством пережатых картинок, а не потерей ссылок.

## Next Phase Readiness

- Закрыт последний открытый хвост issue #40: сжатие и миниатюры перестали быть привилегией новых загрузок.
- Побочно закрыт T-Q40-05 для пережатых объектов: EXIF снимается тем же `_encode`, что и на загрузке, — координаты съёмки и серийный номер камеры перестают лежать по прямой публичной ссылке.
- Оставшиеся хвосты, СОЗНАТЕЛЬНО не тронутые здесь: чистка осиротевших объектов бакета (отдельная задача — у удаления другая цена ошибки) и судьба объектов формата вне JPEG/PNG (их отчёт назовёт, но чинить их — не задача скрипта сжатия).

---
*Quick task: 260825-hnf*
*Completed: 2026-08-25*

## Self-Check: PASSED

Все восемь заявленных файлов существуют на диске; все четыре заявленных коммита
присутствуют в истории ветки. Расхождений между текстом сводки и состоянием
репозитория не обнаружено.
