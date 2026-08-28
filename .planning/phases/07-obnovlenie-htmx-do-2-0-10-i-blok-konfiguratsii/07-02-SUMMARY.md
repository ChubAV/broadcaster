---
phase: 07-obnovlenie-htmx-do-2-0-10-i-blok-konfiguratsii
plan: 02
subsystem: infra
tags: [cache-busting, hashlib, sha256, jinja2, static-assets, tdd]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "своя статика вместо CDN, `_static_dir`, глобал `asset_version` и шесть мест `{{ asset_version }}` в шаблонах"
provides:
  - "`_compute_asset_version(root=_static_dir)` — версия статики по СОДЕРЖИМОМУ охвата, а не по времени изменения одного `app.css`"
  - "`_asset_scope(root)` — детерминированно отсортированный охват (`.css` + `.js`), общий для расчёта и для инвентарного гейта"
  - "`ASSET_SCOPE_SUFFIXES`, `ASSET_VERSION_LEN` — состав охвата и длина дайджеста вынесены константами модуля"
  - "Инвентарный гейт состава охвата: пустой glob и незаявленный четвёртый вендоренный файл роняют тест с именем расхождения"
affects: [замена вендоренных рантаймов, любая будущая фаза, привозящая четвёртый .js или .css в app/static]

actuals:
  tokens: 17444
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Версия статики = хеш содержимого охвата с относительным путём в основании (D-06, D-07)"
    - "Инвентарный гейт состава: ожидание выписано в тесте, обход зовётся из продуктового кода"

key-files:
  created:
    - tests/test_pages/test_asset_version.py
  modified:
    - app/pages/common.py

key-decisions:
  - "Основание расчёта — sha256 по «относительный путь + длина содержимого + байты», усечённый до 12 символов; mtime не читается ни в одной точке (D-07)"
  - "Обрамление вклада файла длиной содержимого, а не только разделителем NUL: имя файла NUL содержать не может, а содержимое — может, и без длины пара «путь/байты» становится неоднозначной"
  - "Пустой охват — ОТДЕЛЬНАЯ ветка деградации в `dev`, а не хеш пустой строки: стабильный хеш ничего неотличим от исправного расчёта"
  - "`root` принят параметром со значением по умолчанию `_static_dir` — единственная причина параметра — проверяемость на временном каталоге (D-08)"
  - "Тест формы значения выписывает длину 12 ЧИСЛОМ, а не берёт её из `ASSET_VERSION_LEN`: иначе молчаливое изменение длины проехало бы"

patterns-established:
  - "Помощник охвата — один на расчёт и на гейт: второй независимый обход разъехался бы с расчётом молча"
  - "Летопись состава над инвентарной константой (по образцу `ROW_DELETE_PLACES` в `test_components.py`)"

requirements-completed: [FOUND-03]

coverage:
  - id: D1
    description: "Подмена байтов ЛЮБОГО файла охвата (таблица стилей или скрипт) меняет значение `asset_version` — вернувшийся пользователь не остаётся на старом рантайме против сервера на контракте 2.x"
    requirement: FOUND-03
    verification:
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_script_byte_change_changes_version"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_stylesheet_byte_change_changes_version"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_fourth_script_file_changes_version"
        status: pass
    human_judgment: false
  - id: D2
    description: "Изменение ТОЛЬКО времени модификации версию НЕ меняет: два контейнера из одного дерева отдают одинаковый `?v=`, деплой без правок статики не сбрасывает кеш"
    requirement: FOUND-03
    verification:
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_utime_only_change_keeps_version"
        status: pass
    human_judgment: false
  - id: D3
    description: "Расчёт детерминирован: порядок обхода файловой системы на значение не влияет, охват сортируется по относительному пути, переименование без правки байтов версию меняет"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_version_is_deterministic_across_calls"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_filesystem_creation_order_does_not_affect_version"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_scope_is_sorted_by_relative_path"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_rename_without_byte_change_changes_version"
        status: pass
    human_judgment: false
  - id: D4
    description: "Пустой охват и ошибка чтения дают одно явное `dev`, а не хеш по нулю или по части файлов; форма значения — ровно 12 строчных шестнадцатеричных символов либо `dev`"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_empty_scope_degrades_to_dev"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_missing_root_degrades_to_dev"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_version_form_is_twelve_lowercase_hex_or_dev"
        status: pass
    human_judgment: false
  - id: D5
    description: "Шрифты (`.woff2`) вне охвата: файл шрифта в каталоге статики версию не меняет"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_woff2_font_is_outside_scope"
        status: pass
    human_judgment: false
  - id: D6
    description: "Инвентарный гейт состава охвата: пустой glob и незаявленный четвёртый вендоренный файл роняют тест с именем расхождения"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_inventory_scope_matches_declared_files"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_asset_version.py#test_inventory_real_asset_version_is_not_degraded"
        status: pass
      - kind: manual_procedural
        ref: "живая проверка: `app/static/js/vendor.min.js` добавлен → гейт красный с текстом «нашёл 4, ожидалось 3 … незаявленные: ['js/vendor.min.js']»; файл удалён → зелёный"
        status: pass
    human_judgment: false
  - id: D7
    description: "Модульное ограничение `common.py` сохранено: расчёт остаётся на импорте, глобал остаётся строкой, конструирования `Settings` на импорте не добавлено"
    verification:
      - kind: other
        ref: "grep -c 'get_settings\\|Settings(' app/pages/common.py → 2 (величина, пришпиленная планом)"
        status: pass
      - kind: other
        ref: "uv run python -c \"from app.pages.common import templates; ... re.fullmatch(r'[0-9a-f]{12}', v)\" → 7c62e8380268"
        status: pass
    human_judgment: false
  - id: D8
    description: "Шесть мест `{{ asset_version }}` в шаблонах пережили правку — менялся способ расчёта, не способ доставки"
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_pages -q → 1193 passed"
        status: pass
      - kind: integration
        ref: "just test → 2302 passed"
        status: pass
    human_judgment: false

# Metrics
duration: 1h 14m
completed: 2026-08-27
status: complete
---

# Phase 07 Plan 02: Версия статики по содержимому охвата Summary

**`asset_version` перестал означать «когда собирали» и стал означать «что отдаётся»: sha256 по содержимому всех `.css` и `.js` каталога статики вместо `mtime` одного `app.css`, с явной деградацией в `dev` и инвентарным гейтом состава охвата.**

## Performance

- **Duration:** 1h 14m
- **Started:** 2026-08-27T07:44:24Z
- **Completed:** 2026-08-27T08:58:26Z
- **Tasks:** 2
- **Files modified:** 2 (1 создан, 1 изменён)

## Accomplishments

- **FOUND-03 закрыт:** подмена байтов любого вендоренного скрипта меняет `?v=` на всех шести тегах. До правки версия бралась от `mtime` файла `app/static/css/app.css`, и замена `htmx.min.js` её не трогала — вернувшийся браузер исполнял старый рантайм против сервера, говорящего на новом контракте.
- **Обратный конец того же перехода:** правка ТОЛЬКО времени модификации версию не меняет — два контейнера, собранные из одного дерева в разное время, отдают одинаковый `?v=`, а деплой без правок статики перестал сбрасывать кеш всем.
- **Деградация сделана отличимой:** пустой охват выведен в отдельную ветку и даёт `dev`, а не стабильный хеш пустой строки, который был бы неотличим от исправного расчёта.
- **Инвентарный гейт (D-09):** состав охвата объявлен множеством из трёх путей и утверждается вызовом того же помощника, что и расчёт; четвёртый вендоренный файл и опустевший охват роняют тест с именем расхождения.
- **Плана вели тесты:** все 12 поведений приехали красными до первой строки расчёта (RED → GREEN), а не подтвердились задним числом.

## Task Commits

1. **Задача 1 — RED: красные тесты расчёта** — `6a98f3f` (test)
2. **Задача 1 — GREEN: расчёт по содержимому охвата** — `4e9edc2` (feat)
3. **Задача 2 — инвентарный гейт состава охвата** — `e5cd91a` (test)

REFACTOR-коммита нет: реализация после GREEN — двадцать строк без дублирования и без очевидных улучшений, а рефактор ради галочки менял бы код, не меняя ничего.

_TDD-плану положено 2-3 коммита; третий здесь — не REFACTOR, а отдельная задача 2, которая правит только тесты._

## Files Created/Modified

- `app/pages/common.py` — новый `import hashlib`; константы `ASSET_SCOPE_SUFFIXES`, `ASSET_VERSION_LEN`, `_ASSET_VERSION_DEGRADED`; новый помощник `_asset_scope(root)`; переписанное тело и докстринг `_compute_asset_version(root=_static_dir)`; восьмистрочный комментарий над регистрацией глобала, закрытый строкой про отсутствие конструирования `Settings` на импорте.
- `tests/test_pages/test_asset_version.py` — создан, 245 строк: 12 поведенческих тестов на временных каталогах + 2 теста инвентарного гейта по настоящему `app/static`.

## Decisions Made

- **Обрамление вклада файла длиной содержимого.** Хеш собирается как `f"{rel}\0{len(body)}\0"` + байты. Одного разделителя NUL было бы мало: имя файла NUL содержать не может, а содержимое — может, и без длины разные наборы файлов теоретически дают один поток байтов. Длина снимает неоднозначность даром.
- **`_asset_scope()` возвращает относительные posix-пути, а не объекты пути.** Гейт утверждает ровно то, что попадает в хеш, и сообщение об отказе называет файл в той же форме, в какой он входит в расчёт.
- **Форма значения в тесте выписана числом 12.** Собрать регулярное выражение из `common.ASSET_VERSION_LEN` было бы короче, но тогда молчаливое изменение длины дайджеста проехало бы — а длина видна в каждом отрендеренном документе и потому есть часть контракта.
- **REFACTOR-фаза пропущена сознательно** (см. «Task Commits»).

## Deviations from Plan

None - plan executed exactly as written.

Отдельно отмечается то, что отступлением НЕ является: план заранее записал «Поправку к роадмапу» — критерий 3 Фазы 7 дословно говорит «считает mtime JS», тогда как решение D-07, принятое позже роадмапа, отвергает mtime в пользу хеша содержимого. Исполнитель следовал плану и D-07; число `mtime` не читается ни в одной точке реализации (`os.utime` встречается только в тесте 4, где ПРАВИТ метку времени, доказывая, что расчёт её не читает). Однострочную правку самого роадмапа вносит закрывающий фазу шаг, а не этот план.

## Issues Encountered

- **Прогон `tests/test_pages` занимает ~20 минут, полная суита ~25.** Причина — bcrypt в фикстурах пользователей, усугублённая тем, что параллельный агент волны 1 гонял свою суиту на той же машине. Не отказ: оба прогона завершились кодом 0 (`ps` показывал состояние `R` и растущее CPU-время, то есть счёт, а не зависание). Учесть при планировании будущих фаз: `<verify>` с полной суитой стоит четверти часа.
- Первая попытка ограничить прогон флагом `--timeout=0` упёрлась в отсутствие `pytest-timeout`. Пакет НЕ ставился (установка пакетов планом не предусмотрена, а Rule 3 её исключает); флаг просто снят.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- FOUND-03 закрыт целиком и в других планах фазы не появляется.
- Замена `htmx.min.js` планом 07-01 (та же волна 1) состав охвата не меняет — меняются байты файла, а не имя, — поэтому инвентарный гейт после слияния волны остаётся зелёным, а значение версии закономерно меняется. Пересечения `files_modified` между планами 07-01 и 07-02 нет ни в одной точке.
- Шесть мест `{{ asset_version }}` в шаблонах не тронуты: менялся способ расчёта, не способ доставки.
- `graphify update .` прогнан после последней правящей код задачи, как требует `./CLAUDE.md`: 12851 узлов, 24298 рёбер.

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED | `6a98f3f` `test(07-02)` | Pass — 12 тестов краснеют по сигнатуре и отсутствию помощника, не по сбору файла |
| GREEN | `4e9edc2` `feat(07-02)` | Pass — 12/12 зелёных минимальной реализацией |
| REFACTOR | — | Не потребовался (см. «Task Commits») |

Последовательность RED → GREEN соблюдена: `test(07-02)` предшествует `feat(07-02)` в истории.

## Known Stubs

None — заглушек, пропущенных тестов и непрогнанных `<verify>` в плане не осталось.

## Threat Flags

None — новой сетевой, авторизационной или схемной поверхности план не заводит. Файловый обход идёт от фиксированной модульной базы пути, значений из запроса не принимает и исполняется один раз на импорте.

## Verification Log

| Проверка | Результат |
|---|---|
| `uv run pytest tests/test_pages/test_asset_version.py -q -x` | 14 passed |
| `uv run pytest tests/test_pages -q` | 1193 passed (0:20:42), exit 0 |
| `just test` | 2302 passed (0:24:56), exit 0 |
| `uv run python -m compileall -q app main.py tests` | exit 0 |
| `grep -c 'import hashlib' app/pages/common.py` | 1 |
| `grep -c 'ASSET_VERSION_LEN' app/pages/common.py` | 2 (≥2) |
| `grep -Ec 'def _compute_asset_version\(root' app/pages/common.py` | 1 |
| `grep -c 'get_settings\|Settings(' app/pages/common.py` | 2 (пришпилено планом) |
| `-k utime` / `-k empty` / `-k rename` / `-k woff2` | по 1 passed каждый |
| `grep -c 'ASSET_GLOB_FILES' tests/…/test_asset_version.py` | 5 (≥2) |
| `css/app.css` / `js/htmx.min.js` / `js/alpine.min.js` в тесте | по 3 вхождения каждый (≥1) |
| `-k inventory` | 2 passed |
| Четвёртый `.js` роняет гейт с именем файла | Да: «нашёл 4, ожидалось 3 … незаявленные: ['js/vendor.min.js']»; после удаления — зелёный |
| Глобал `asset_version` на настоящем каталоге | `7c62e8380268` — не `dev`, форма соблюдена |
| `graphify update .` | 12851 узлов, 24298 рёбер |

## Self-Check: PASSED

- `app/pages/common.py` — FOUND
- `tests/test_pages/test_asset_version.py` — FOUND
- Коммиты `6a98f3f`, `4e9edc2`, `e5cd91a` — FOUND в `git log --all`

---
*Phase: 07-obnovlenie-htmx-do-2-0-10-i-blok-konfiguratsii*
*Completed: 2026-08-27*
