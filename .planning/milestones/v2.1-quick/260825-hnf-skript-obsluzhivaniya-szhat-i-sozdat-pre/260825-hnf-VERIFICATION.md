---
phase: quick-260825-hnf-recompress-legacy-attachments
verified: 2026-08-25T00:00:00Z
status: human_needed
score: 14/14 must-haves verified
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Оператор запускает сухой прогон на боевых настройках: `just recompress-attachments` (или `just prod-recompress-attachments` внутри боевой композиции) и читает отчёт ЦЕЛИКОМ."
    expected: "Отчёт печатается без падения и содержит: число просмотренных ключей, число объектов, взятых в работу, объём «до», расчётный объём «после», экономию в процентах, строку «Добавлено миниатюрами», четыре именованных счётчика пропуска, примеры ключей неподдерживаемого формата (если такие есть), строку `not_shrunk` и группу ошибок. Завершается строкой о том, что записей не было."
    why_human: "Плановый `<human-check>` задачи 3. Требует боевых учётных данных S3 и боевой базы; исполнителю и верификатору прогон против боевого бакета прямо запрещён. Дополнительно: это ПЕРВОЕ исполнение шва `main()` → `S3AttachmentStore` → настоящий клиент `aiobotocore` — единственный участок, который автоматические тесты покрыть не могут (двойник в памяти проверяет ядро, подменённый `AioSession` — чтения по отдельности, но не их стык с реальным бакетом)."
  - test: "Решение о запуске `--apply` принимается ПО отчёту сухого прогона, а не заранее."
    expected: "Если строка «формат не поддерживается» ненулевая — примеры ключей разобраны отдельно ДО записи: такие объявления уже сегодня не уходят в Telegram, и этот прогон может обнаружить дефект первым. Запуск с записью — только если объём экономии и число объектов в отчёте устраивают."
    why_human: "Перезапись объекта на месте необратима (T-QH-02): прежних байтов после неё нет. Это решение принадлежит человеку по построению, программной проверке не подлежит."
---

# Quick 260825-hnf: Скрипт обслуживания «сжать и создать превью» Verification Report

**Task Goal:** скрипт обслуживания: сжать и создать превью для вложений, загруженных до issue #40
**Verified:** 2026-08-25
**Status:** human_needed
**Re-verification:** No — initial verification
**Diff base:** `91572b4..HEAD` (commits `15adf3b`, `55516f3`, `1da8457`, `16d68d5`, `1348668`, merge `8838179`)

## Goal Achievement

### Observable Truths

| # | Truth (must_haves) | Status | Evidence |
|---|--------------------|--------|----------|
| 1 | Множество ключей выводится ТОЛЬКО из `Ad.images` (D-1); обратного разбора адреса в ключ нет ни одной строкой | ✓ VERIFIED | `collect_attachment_keys` выполняет `select(Ad.images)` и ничего больше (`scripts/recompress_attachments.py:176`). Собственный grep по скрипту на `urlparse`/`rsplit`/`split(`/`get_image_url`/`s3_public_url`/`SendLog` — НИ ОДНОГО совпадения. Тест `test_history_only_keys_are_never_collected` — passed |
| 2 | Прогон без `--apply` не кладёт в хранилище ни одного объекта | ✓ VERIFIED | Обе записи в `_process_key` стоят под `if apply:` (строки `await store.put(key, …)` и `await store.put(thumb_key(key), …)`); других вызовов `put` в скрипте нет. `test_a_dry_run_writes_nothing` — passed (`store.puts == []`, при этом `bytes_before > 0`, `bytes_after > 0`) |
| 3 | Объект сверх `DELIVERY_MAX_EDGE` после `--apply` лежит под ТЕМ ЖЕ ключом с длинной стороной ровно `DELIVERY_MAX_EDGE` — если пересборка строго меньше; иначе объект прежний и учтён в `not_shrunk` | ✓ VERIFIED | `test_an_oversized_attachment_is_rebuilt_under_the_same_key` — passed: `store.puts[0][0] == KEY` посимвольно, `max(open_bytes(delivery).size) == DELIVERY_MAX_EDGE`. Условная половина: `test_a_rebuilt_object_that_grew_is_not_written` — passed (`not_shrunk == 1`, `store.objects[KEY] == original`, ни один счётчик пропуска не тронут). Код: `if len(rebuilt.delivery) < len(content)` — строгое сравнение перед записью |
| 4 | Формат не меняется никогда: PNG остаётся PNG, JPEG остаётся JPEG, расширение внутри ключа не переписывается | ✓ VERIFIED | `app/services/images.py`: `target_format = source_format` (без единой ветки на смену). Ключ записи — тот же объект `key`, ключ миниатюры — `thumb_key(key)` (приставка `thumbs/`, расширение сохраняется). `test_a_stored_png_without_alpha_is_rebuilt_as_png` и `test_a_stored_jpeg_stays_jpeg` — passed; первый есть прямая противоположность существующему `test_png_without_real_alpha_becomes_jpeg` в том же файле |
| 5 | Пережатие и миниатюра — ДВА независимых решения по одному объекту | ✓ VERIFIED | `needs_resize = probe.long_edge > DELIVERY_MAX_EDGE` и `needs_thumbnail = not await store.object_exists(thumb_key(key))` вычисляются раздельно и в решение друг друга не входят. Обе половины: `test_a_thumbnail_is_built_for_an_image_within_the_limit` (одна запись — только `thumb_key`, исходный объект байт в байт прежний) и `test_an_image_over_the_limit_with_a_thumbnail_is_only_re_encoded` (одна запись — только исходный ключ) — обе passed |
| 6 | У каждого объекта, взятого в работу, после `--apply` существует `thumbs/{ключ}` | ✓ VERIFIED | `test_the_thumbnail_is_built_under_the_derived_key` — passed (`thumb_key(KEY) in store.objects`). Разбор ветвей: миниатюра строится тогда и только тогда, когда её нет; ветка «не строим» достижима только при уже существующем объекте `thumbs/{ключ}` — то есть постусловие выполняется в обоих случаях |
| 7 | Объект формата вне пары JPEG/PNG переживает прогон нетронутым и назван в отчёте примером ключа | ✓ VERIFIED | `test_an_unsupported_format_survives_the_run_untouched` — passed: настоящий GIF, `store.puts == []`, `store.objects[gif_key] == original`, счётчик = 1, `gif_key in report.unsupported_examples` И `gif_key in script.format_report(report)`. Потолок примеров `UNSUPPORTED_EXAMPLES_LIMIT = 10` назван в самом тексте отчёта |
| 8 | Объект, заявляющий больше `MAX_DECODED_PIXELS`, не декодируется, не выкачивается целиком и не пишется | ✓ VERIFIED | `probe_image` сверяет `width * height > MAX_DECODED_PIXELS` между `Image.open()` и возвратом — распаковки пикселей между ними нет; вторая проверка повторена на полных байтах в `rebuild_stored_image`. `test_an_image_over_the_pixel_ceiling_is_skipped_without_a_full_read` — passed: `store.reads == []`, `store.puts == []`, счётчик = 1 |
| 9 | Полное тело читается ТОЛЬКО при решении о работе; полностью пропущенный объект стоит одного диапазонного чтения и ни одного полного | ✓ VERIFIED | `test_a_skipped_object_costs_one_ranged_read_and_no_full_read` — passed (`len(head_reads) == 1`, `reads == []`). Порядок в `_process_key`: `head_bytes` → `probe_image` → два решения → `if not needs_resize and not needs_thumbnail: return` СТОИТ ДО первого `store.read`. Названное исключение — плановый откат на полное чтение при коротком заголовке (см. «Наблюдения», п. 1) |
| 10 | Разбор пропусков содержит РОВНО ЧЕТЫРЕ причины: `len(SKIP_REASONS) == 4`, ключи счётчиков совпадают с кортежем | ✓ VERIFIED | `SKIP_REASONS` — кортеж из четырёх констант; `Report.skips` инициализируется обходом этого же кортежа; `format_report` рендерит разбор обходом кортежа, а не перечислением строк. `test_the_skip_breakdown_has_exactly_four_reasons` — passed. Пятой причины «адрес не разобрался в ключ» в коде нет: обратного разбора нет (см. truth 1) |
| 11 | Скрипт не фиксирует ни одной транзакции БД; `Ad.images` и `SendLog.ad_images` равны до и после | ✓ VERIFIED | Собственный grep по скрипту на `commit`/`flush`/`session.add`/`session.delete` — НИ ОДНОГО совпадения. `test_the_run_never_touches_the_database` — passed (значения снимаются из НОВОЙ выборки после `expire_all()`); `test_the_script_never_commits_a_transaction` — passed |
| 12 | Второй подряд `--apply` не выполняет ни одной записи | ✓ VERIFIED | `test_a_second_apply_run_writes_nothing` — passed: база из трёх объявлений, покрывающая все ветки; первый прогон пишет (утверждается непустой журнал, иначе тест беспредметен), журнал очищается, второй прогон даёт `puts == []`, `processed == 0`, `errors == []` |
| 13 | Ни один путь не вызывает удаляющий метод хранилища и не импортирует адаптеры мессенджеров | ✓ VERIFIED | Протокол `AttachmentStore` объявляет ровно четыре метода, удаляющего среди них нет по построению. Собственный grep на `delete`/`remove_object`/`abort_multipart`/`messengers` по `scripts/recompress_attachments.py` — НИ ОДНОГО совпадения. `test_the_script_source_declares_no_destructive_storage_call` и `test_the_script_source_declares_no_messenger_import` — passed |
| 14 | `test_upload_file_to_s3` остаётся зелёным БЕЗ правок | ✓ VERIFIED | `git diff 91572b4..HEAD -- tests/test_services/test_s3.py`: внутри теста НИ ОДНОЙ изменённой строки — изменён только блок импортов файла и дописан новый раздел после теста. Утверждения `client.put_object.assert_called_once_with(Bucket=…, Key=…, Body=…, ContentType=…)` сохранены дословно; тест passed |

**Score:** 14/14 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/recompress_attachments.py` | Скрипт: dry-run по умолчанию, `--apply`, два решения, отчёт с четырьмя причинами | ✓ VERIFIED | 419 строк. Содержит `SKIP_REASONS`, `AttachmentStore`, `S3AttachmentStore`, `collect_attachment_keys`, `_process_key`, `recompress_attachments`, `Report`, `format_report`, `main`, `argparse --apply` (`action="store_true"`, умолчание False). Импортируется тестами и исполняется (`--help` отработал) |
| `app/services/s3.py` | Диапазонное чтение с полным размером, полное чтение, проверка существования, общий клиент | ✓ VERIFIED | `HEAD_READ_BYTES = 65_536`, `ObjectHead`, `open_s3_client`, `put_object_bytes`, `read_object_head`, `read_object`, `object_exists`. Все вызываются из `S3AttachmentStore`; `upload_file_to_s3` делегирует `put_object_bytes` без изменения сигнатуры |
| `app/services/images.py` | Соседний вход: разбор заголовка с потолком, пересборка БЕЗ смены формата | ✓ VERIFIED | `ImageProbe`, `probe_image`, `RebuiltImage`, `rebuild_stored_image` дописаны отдельным разделом; `prepare_upload` и шапка модуля не тронуты (диff — чистое добавление 153 строк в конец) |
| `tests/test_scripts/test_recompress_attachments.py` | Четыре причины, трафик, идемпотентность, прохибиции | ✓ VERIFIED | 604 строки, 22 теста. `FakeStore` с тремя журналами (`head_reads`/`reads`/`puts`), настоящие байты Pillow. `test_a_second_apply_run_writes_nothing` присутствует и зелёный |
| `tests/test_services/test_s3.py` | Модульное покрытие новых чтений; прежний тест записи не переписан | ✓ VERIFIED | 10 новых тестов (Content-Range, откат на ContentLength, InvalidRange → пустой объект, отсутствие → None/False, отказ не проглатывается, `put_object_bytes`). Тело `test_upload_file_to_s3` не тронуто |
| `justfile` | Два рецепта по образцу `collect-group-info` | ✓ VERIFIED | `recompress-attachments *args` и `prod-recompress-attachments *args`, оба с комментарием-описанием, оба пробрасывают `{{ args }}`. `grep -cE '^(prod-)?recompress-attachments '` = 2 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| Сбор ключей | `Ad.images` — ЕДИНСТВЕННЫЙ источник (D-1) | `select(Ad.images)` | ✓ WIRED | Другого источника в файле нет; `SendLog` не импортируется |
| Решение о пережатии | `probe_image` → `DELIVERY_MAX_EDGE` / `MAX_DECODED_PIXELS` | импорт из `app.services.images` | ✓ WIRED | `probe.long_edge > DELIVERY_MAX_EDGE`; `ImageTooLarge` перехватывается ДО полного чтения |
| Решение о миниатюре | `thumb_key` + `object_exists` | `not await store.object_exists(thumb_key(key))` | ✓ WIRED | Ключ миниатюры выводится, а не сочиняется (`test_the_thumbnail_is_built_under_the_derived_key`) |
| `read_object_head` | `probe_image` | `head.body` подаётся в `probe_image` до `store.read` | ✓ WIRED | В этом весь смысл дисциплины трафика; порядок утверждён тестом на журналы |
| Запись | `put_object_bytes` под ТЕМ ЖЕ ключом и `thumb_key(ключ)` | `S3AttachmentStore.put` | ✓ WIRED | Оба вызова под `if apply:` |
| `upload_file_to_s3` | `put_object_bytes` | делегация внутри `open_s3_client` | ✓ WIRED | Сигнатура и наблюдаемые аргументы `client.put_object` не изменились — доказано зелёным `test_upload_file_to_s3` без правок |

### Data-Flow Trace (Level 4)

| Artifact | Data | Source | Real data | Status |
|----------|------|--------|-----------|--------|
| `collect_attachment_keys` | список ключей | `select(Ad.images)` — настоящий запрос к БД | ✓ | ✓ FLOWING |
| `_process_key` | `head.body` | `read_object_head` → `client.get_object(Range=…)` | ✓ | ✓ FLOWING |
| `_process_key` | `content` | `read_object` → `client.get_object` | ✓ | ✓ FLOWING |
| `rebuild_stored_image` | `delivery` / `thumbnail` | настоящее декодирование/кодирование Pillow (тесты открывают результат обратно и читают его размеры и формат) | ✓ | ✓ FLOWING |
| `format_report` | все числа отчёта | поля `Report`, накопленные ядром | ✓ | ✓ FLOWING |
| `main` | настройки хранилища | `get_settings()` — имена полей сверены с `app/config.py` (`s3_endpoint_url`, `s3_access_key`, `s3_secret_key`, `s3_region`, `s3_bucket_name`, `database_url`) и с их употреблением в `app/routes/uploads.py` | ✓ (статически) | ⚠️ шов с настоящим бакетом исполняется впервые оператором — см. human_verification |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Скрипт, соседний вход, хранилище | `uv run pytest tests/test_scripts/ tests/test_services/test_s3.py tests/test_services/test_images.py -q` | 75 passed | ✓ PASS |
| Потребители ключа и адреса не сломаны | `uv run pytest tests/test_routes/test_uploads.py tests/test_services/test_image_keys.py tests/test_pages/test_attachment_history_integrity.py -q` | 62 passed | ✓ PASS |
| Именованные инварианты (идемпотентность, БД, трафик, ключ, сухой прогон, D-1) | `pytest -k "second_apply_run_writes_nothing or never_touches_the_database or costs_one_ranged_read or rebuilt_under_the_same_key or dry_run_writes_nothing or history_only_keys"` | 6 passed | ✓ PASS |
| Справка скрипта | `uv run python scripts/recompress_attachments.py --help` | usage + `--apply` с умолчанием «сухой прогон» | ✓ PASS |
| Рецепты объявлены | `grep -cE '^(prod-)?recompress-attachments ' justfile` | 2 | ✓ PASS |
| Зависимости не тронуты | `git diff --stat 91572b4..HEAD -- pyproject.toml uv.lock` | пусто | ✓ PASS |
| Боевой сухой прогон | — | не выполнялся: боевой бакет верификатору запрещён | ? SKIP → human |

### Probe Execution

Проектных probe-скриптов (`scripts/*/tests/probe-*.sh`) в репозитории нет; план их не объявляет. Шаг неприменим.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| TODO-LEGACY-IMAGES | 260825-hnf-PLAN.md | Вложения, загруженные до issue #40, остаются несжатыми навсегда | ✓ SATISFIED (машинная часть) | Все четыре критерия раздела «Проверяемо закрыто, когда» заметки закрыты тестами: идемпотентность (truth 12), неизменность `Ad.images` (truth 11), существование `thumbs/{ключ}` (truth 6), нетронутость чужого формата с именованием в отчёте (truth 7). Регистр `.planning/REQUIREMENTS.md` этого ID не содержит — идентификатор принадлежит заметке `todos/pending/`, а не реестру; не орфан |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | `TODO`/`FIXME`/`XXX`/`TBD`/`HACK`/`PLACEHOLDER` во всех восьми изменённых файлах | — | НИ ОДНОГО совпадения |

Заглушек, пустых обработчиков и захардкоженных возвратов не обнаружено. Единственный широкий перехват (`except Exception` в `recompress_attachments`) — плановое требование «прогон из сотен объектов не падает на одном»; он не молчит, а пишет строку в `report.errors` с названным ключом, и это утверждено тестом `test_a_missing_object_is_reported_as_an_error_not_as_a_skip`.

### Locked Decisions Compliance

| Decision | Status | Evidence |
|----------|--------|----------|
| D-1: только живые вложения; обратный разбор адреса в ключ — VIOLATION | ✓ СОБЛЮДЕНО | Единственный источник — `select(Ad.images)`; в скрипте нет ни `urlparse`, ни `rsplit`, ни `split(`, ни `get_image_url`, ни импорта `SendLog` |
| D-1: `SKIP_REASONS` — четырёхэлементный кортеж; пятая причина — VIOLATION | ✓ СОБЛЮДЕНО | `len(SKIP_REASONS) == 4`, ключи `Report.skips` выводятся из того же кортежа, отчёт рендерится его обходом. `not_shrunk` вынесен ОТДЕЛЬНЫМ полем с комментарием, объясняющим, почему он не пятая причина, и тест `test_a_rebuilt_object_that_grew_is_not_written` утверждает, что ни один из четырёх счётчиков при этом не менялся |
| Условность truth 3 (только при строгом уменьшении) | ✓ УЧТЕНО, не засчитано как дефект | Квалификация признана намеренной; обе половины покрыты отдельными тестами |

### Deviations Judgment

| # | Deviation | Judgment |
|---|-----------|----------|
| 1 | Реализация задач 2 и 3 приземлилась в коммите задачи 1 (`55516f3`) | ПРИЕМЛЕМО, с оговоркой. Довод исполнителя проверяем: ветка «пропустить и не читать тело» есть ровно то место, где выставляется счётчик, и разнести её на два коммита без временной заглушки нельзя. Цена уплачена дисциплиной RED→GREEN, а не покрытием: каждое утверждение задач 2 и 3 имеет свой тест, все 22 теста скрипта прогнаны мной заново и зелёные. На достижение цели не влияет |
| 2 | Rule-1 auto-fix: тест ссылался на несуществующий `script.RebuiltImage` | ПРИЕМЛЕМО и УЛУЧШАЕТ. Импортировать `RebuiltImage` в сам скрипт значило бы завести неиспользуемый импорт ради теста. Добавленное в тот же тест утверждение `report.errors == []` — не косметика: именно оно не даёт этому классу отказа впредь маскироваться под «ничего не записано» (без него `AttributeError` внутри двойника съедался бы защитой «прогон не падает на одном ключе», и тест зеленел бы по неверной причине) |
| 3 | Тесты соседнего входа положены в `tests/test_services/test_images.py`, которого нет в `<files>` | ПРИЕМЛЕМО. Файл прямо назван в `<verify><automated>` задачи 1 — расхождение внутри самого плана, а не отступление от него. Покрытие ГЕНУИННОЕ, а не косметическое: 10 тестов, среди них именованная плановая регрессия `test_a_stored_png_without_alpha_is_rebuilt_as_png`, сохранение прозрачности палитрового PNG, снятие EXIF (T-QH-05) и повторная проверка потолка на ПОЛНЫХ байтах. Соседство с противоположным `test_png_without_real_alpha_becomes_jpeg` несёт смысл: два теста на одном входе с разными ожиданиями читаются как расхождение №1 |

### Наблюдения (не дефекты)

1. **Откат на полное чтение при коротком заголовке — названное исключение из truth 9.** Объект неподдерживаемого формата ВЕСОМ БОЛЬШЕ 64 КиБ будет выкачан целиком, прежде чем попадёт в счётчик «формат не поддерживается»: разбор частичного тела не отличает «формат чужой» от «маркер размеров не поместился». Это прямое требование плана (задача 2, п. 3: «Неудача при ЧАСТИЧНОМ теле — ровно одно полное чтение и повторный разбор») и цена, уплаченная за то, чтобы исправный снимок не объявлялся битым (`test_a_short_header_falls_back_to_one_full_read`). Утверждение truth 9 о «ровно одном диапазонном чтении» относится к обычному пропуску (в пределах + миниатюра есть) и в этом виде доказано.
2. **Заметка `todos/pending/legacy-images-are-never-compressed.md` осталась в `pending`.** Каталога `todos/done/` в проекте нет вовсе, а критерии закрытия заметки включают боевой прогон — то есть перенос был бы преждевременным до выполнения human-check. Не дефект.
3. **`tests/test_planning/test_state_progress_matches_roadmap.py` падает на этом дереве.** Подтверждено как ПРЕДСУЩЕСТВУЮЩЕЕ и вне объёма: `git diff 91572b4..HEAD -- .planning/STATE.md .planning/ROADMAP.md` пуст. Задаче не приписывается, не чинится.

### Gaps Summary

Пробелов, блокирующих достижение цели, не обнаружено. Все четырнадцать `must_haves`, все шесть артефактов, все шесть ключевых связей и все одиннадцать инвариантов задания подтверждены исходниками и зелёными тестами, прогнанными заново, а не заявлениями сводки. Ни одна прохибиция раздела `<non_goals>` не нарушена; оба следствия D-1 (отсутствие обратного разбора адреса и четырёхэлементный `SKIP_REASONS`) соблюдены дословно.

Остаётся ровно одно, чего программная проверка дать не может: боевой сухой прогон и принятое по его отчёту решение о `--apply`. Это плановый `<human-check>`, сознательно не выполненный исполнителем, и он же — первое исполнение шва `main()` → `S3AttachmentStore` → настоящий клиент хранилища. Поэтому статус `human_needed`, а не `passed`.

---

_Verified: 2026-08-25_
_Verifier: Claude (gsd-verifier)_
