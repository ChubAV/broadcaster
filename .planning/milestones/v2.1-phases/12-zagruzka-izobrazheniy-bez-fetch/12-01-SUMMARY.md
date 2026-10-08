---
phase: 12-zagruzka-izobrazheniy-bez-fetch
plan: 01
subsystem: ui
tags: [htmx, multipart, fastapi, jinja2, s3, image-upload]

# Dependency graph
requires:
  - phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
    provides: слой ответа `respond()` с обязательным путём деградации (FOUND-04) и отказ зависимости 204 + `HX-Location` (FOUND-07)
  - phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
    provides: макрос `components/form_wrapper.html`, идиома «постоянная обёртка + innerHTML», перечни исключений разметочных гейтов
  - phase: 11-massovyy-perevod-razdelov-pisma
    provides: форма объявления на htmx, реестр пар транспортов `test_htmx_post_pairs.py`
provides:
  - "`app/services/image_upload.py` — не-транспортная половина загрузки: распознавание типа по содержимому, нормализация имени, приведение расширения, порционное чтение, запись объекта и миниатюры"
  - "`POST /ads/images` внутри `ads_router` — страничный маршрут загрузки, отвечающий фрагментом полосы вложений"
  - "`ads/includes/media_strip.html` — единственный источник разметки полосы (плитки, скрытые поля ключей с `form=\"ad-form\"`, строки отказа)"
  - "`ads/includes/media_upload_form.html` — форма загрузки на макросе-обёртке, составной запрос без единой строки JS"
  - "Параметры `encoding` и `include` у макроса `form_wrapper`"
  - "Глобал шаблонов `upload_field` — единственное объявление имени файлового поля доезжает до разметки значением"
affects: [12-02, 12-03, 12-04, 12-05, 13-fetch-02, 15-fetch-03]

# Actuals (#2632)
actuals:
  tokens: 73000
  tasks: 2
  commits: 4
  plan_head_before: c1f8e2ecd6809a01bbc5e9ad66902efa6d389951

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Сервис отдаёт `Accepted | Rejected` вместо `HTTPException`: форму ответа выбирает страничный слой (D-04)"
    - "Предел числа частей составного запроса задаётся явно: `request.form(max_files=…, max_fields=…)` (G-3)"
    - "Имя поля формы объявлено ОДИН раз в сервисе и доезжает до разметки глобалом, а не литералом"

key-files:
  created:
    - app/services/image_upload.py
    - app/templates/ads/includes/media_strip.html
    - app/templates/ads/includes/media_upload_form.html
    - tests/test_pages/test_ads_image_upload.py
  modified:
    - app/pages/ads.py
    - app/pages/common.py
    - app/templates/components/form_wrapper.html
    - tests/test_pages/test_impersonation_gate.py
    - tests/test_templates/test_htmx_markup_gates.py
    - tests/test_pages/test_htmx_gates.py
    - tests/test_pages/test_htmx_post_pairs.py
    - tests/test_pages/test_hx_location_destinations.py
    - tests/test_pages/test_origin_guard_on_destructive_routes.py

key-decisions:
  - "Целевым тестом улики RED выбран `test_upload_is_closed_by_the_router_access_gate`: он покраснел УТВЕРЖДЕНИЕМ о поведении (404 вместо 204), тогда как два соседних теста краснели импортом ещё не существующего модуля — а импорт не есть доказательство отсутствия поведения (#3770)"
  - "Комментарий про зависимость доступа роутера вынесен НАД объявлением обработчика: критерий 3 проверяется срезом текста самого обработчика, и имя зависимости внутри него неотличимо от переписанного гейта для машинной сверки"
  - "Имя файлового поля названо в тестовом модуле ЛИТЕРАЛОМ: ввезённая константа утверждала бы имя саму о себе и зеленела бы ровно тогда, когда браузер со старым именем получал бы отказ"
  - "Текст отказа по размеру перенесён дословно английской f-строкой: его читает человек и сегодня (через `uploadFile()`), и смена формулировки заодно с механизмом смешала бы два изменения в одном"
  - "Запись `app/routes/uploads.py::upload_image` в перечне имперсонации НЕ снята: окно сосуществования двух входов закрывает план 12-05 вместе с переездом суиты в 1099 строк"

patterns-established:
  - "Улика RED для pytest собирается механическим переводчиком из ВЫВОДА прогона (приём плана 10-56), а не набирается руками"
  - "Инвентарное число ставится прогоном покрасневшего правила и дописывается пронумерованной строкой летописи — включая записи «ДВИЖЕНИЯ НЕТ»"

requirements-completed: [FETCH-01]

coverage:
  - id: D1
    description: "Годный PNG, посланный на `/ads/images` с признаком htmx, даёт 200 и фрагмент полосы: плитка с миниатюрой плюс скрытое поле `name=\"images\"` с `form=\"ad-form\"`"
    requirement: FETCH-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_image_upload.py#test_one_image_over_htmx_returns_the_strip_fragment"
        status: pass
    human_judgment: false
  - id: D2
    description: "Тот же адрес БЕЗ признака htmx отвечает 302 на `/ads/new` — путь деградации заполнен честно (FOUND-04, D-02)"
    requirement: FETCH-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_image_upload.py#test_upload_without_htmx_redirects_to_the_editor"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_post_pairs.py#test_every_pair_case_answers_both_transports[ads_images_upload-загрузка вложения — запрос без файловых частей]"
        status: pass
    human_judgment: false
  - id: D3
    description: "Маршрут заведён внутри `ads_router` с уже висящей `Depends(require_access)`; отказ доступа едет 204 + `HX-Location`, а гейта в теле обработчика нет (критерий 3, D-01)"
    requirement: FETCH-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_image_upload.py#test_upload_is_closed_by_the_router_access_gate"
        status: pass
      - kind: unit
        ref: "awk '/^async def ads_images_upload/,/^@router/' app/pages/ads.py | grep -c 'require_access' → 0"
        status: pass
    human_judgment: false
  - id: D4
    description: "Не-транспортная логика живёт в `app/services/image_upload.py` с дословно перенесёнными комментариями-обоснованиями; порядок «отказ по размеру ВЫШЕ распознавания типа» сохранён и наблюдаем"
    requirement: FETCH-01
    verification:
      - kind: unit
        ref: "grep -n 'max_bytes' → строка 304 МЕНЬШЕ grep -n 'sniff_image(content)' → строка 335; grep -c 'WebP|CR-02|WR-02|issue #40' ≥ 1 каждый"
        status: pass
    human_judgment: false
  - id: D5
    description: "Число частей составного запроса ограничено явно (`request.form(max_files=…, max_fields=…)`) — второй рубеж, которого у приложения не было вовсе (G-3, ASVS V12)"
    requirement: FETCH-01
    verification:
      - kind: unit
        ref: "grep -c 'MAX_UPLOAD_PARTS' app/pages/ads.py → 2"
        status: pass
    human_judgment: false
  - id: D6
    description: "Форма загрузки рождена макросом `form_wrapper`, `hx-indicator=\"find .form-busy\"` приезжает от макроса, отступление цели блокировки записано поимённо (критерий 4, D-09)"
    requirement: FETCH-01
    verification:
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_htmx_post_is_born_of_a_component_macro"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_htmx_markup_gates.py#test_every_disabled_elt_exception_is_actually_an_exception"
        status: pass
    human_judgment: false
  - id: D7
    description: "В браузере выбор файла поднимает признак «идёт запрос», и плитка появляется без перезагрузки страницы"
    requirement: FETCH-01
    verification: []
    human_judgment: true
    rationale: "Подключение полосы и формы к странице редактора делает план 12-03; до него живого экрана с этой формой не существует, и признак «идёт запрос» человеку показать негде. Ручной обход фазы — единственное место, где это наблюдаемо."

# Metrics
duration: 1h 44m
completed: 2026-09-18
status: complete
---

# Phase 12 Plan 01: Сквозной срез загрузки изображения Summary

**Одна картинка проходит путь целиком — составной запрос htmx, страничный маршрут внутри `ads_router`, перенесённый сервис `image_upload`, хранилище — и возвращается фрагментом полосы с плиткой и скрытым полем ключа, несущим `form="ad-form"`.**

## Performance

- **Duration:** 1h 44m (из них 75 минут — два полных прогона суиты по 37 минут)
- **Started:** 2026-09-18T16:27:21Z
- **Completed:** 2026-09-18T18:12:00Z
- **Tasks:** 2 из 2
- **Files modified:** 13 (4 созданы, 9 правлены)

## Accomplishments

- **Не-транспортная логика переехала в `app/services/image_upload.py` дословно** — вместе с комментариями-обоснованиями про WebP в Telethon и Baileys, про GIF, про `Photo(path=...)` в MAX, про вектор CR-02, про снятый запрет декодирования и issue #40, про WR-02. Две ссылки, устаревшие переездом, правлены ВМЕСТЕ с переносом и помечены как правленые; остальные не тронуты ни на символ.
- **`POST /ads/images` заведён внутри `ads_router`** — критерий 3 закрыт СУЩЕСТВУЮЩЕЙ зависимостью: ни строки гейта в теле, отказ доступа едет 204 с заголовком перехода.
- **Форма ответа — всегда 200 с фрагментом полосы** (D-04), и фрагмент собирается из единственного источника разметки `ads/includes/media_strip.html`, который со плана 12-03 будет включать и страница редактора.
- **Форма загрузки шлёт составной запрос без единой строки JS** — макрос-обёртка получил параметры `encoding` и `include`, а умолчания оставили разметку остальных сорока шести форм вехи байт-в-байт прежней.
- **У приложения появился второй рубеж на число частей запроса** (`MAX_UPLOAD_PARTS = 64`): Starlette ограничивает размером только НЕфайловые части, и до этой фазы партия из тысячи файлов разбиралась бы целиком.

## Task Commits

1. **Задача 1, RED: падающие тесты фрагмента полосы** — `abe9bf4` (test)
2. **Задача 1, GREEN: сервис, маршрут, шаблон полосы** — `82cc55a` (feat)
3. **Задача 2: форма загрузки на макросе-обёртке** — `839bbe1` (feat)
4. **Инвентарные числа, найденные ПОЛНЫМ прогоном** — `71c3788` (test)

REFACTOR-коммита нет, и это записано, а не умолчано: после GREEN улучшать было нечего — перенос дословный, а транспортный обработчик уже написан по форме соседнего `ads_create`.

## Files Created/Modified

- `app/services/image_upload.py` — распознавание типа по содержимому, нормализация имени, приведение расширения, `store_upload`, `Accepted`/`Rejected`, `UPLOAD_FILE_FIELD`, `MAX_UPLOAD_PARTS`, `upload_limit_message`
- `app/pages/ads.py` — обработчик `ads_images_upload` и нульарный сборщик `_media_strip_fragment`
- `app/templates/ads/includes/media_strip.html` — единственный источник разметки полосы; узел `#media-tray`
- `app/templates/ads/includes/media_upload_form.html` — форма загрузки соседом полосы, без кнопки отправки
- `app/templates/components/form_wrapper.html` — параметры `encoding` и `include`
- `app/pages/common.py` — глобал `upload_field`
- `tests/test_pages/test_ads_image_upload.py` — пара транспортов и фрагмент полосы (3 теста)
- Пять гейт-файлов суиты — инвентарные числа и поимённые записи (см. «Deviations»)

## Decisions Made

Пять решений вынесены во frontmatter (`key-decisions`). Ни одно из четырнадцати запертых решений `12-CONTEXT.md` не пересмотрено; D-13 соблюдён: каждое движение инвентарного числа записано строкой летописи с пометкой «Фаза 12, план 12-01», включая две записи «ДВИЖЕНИЯ НЕТ».

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Улика RED переведена в форму проверяющего механическим адаптером**

- **Found during:** Задача 1, шаг персистирования улики RED
- **Issue:** `gsd-tools check tdd-red-evidence` разбирает TAP (`# tests`, `# fail`, `not ok N - имя`), которого pytest не печатает ни при каком наборе ключей, а плагина TAP в дереве нет. Запись, набранная руками, УТВЕРЖДАЛА бы прогон вместо того, чтобы его ПЕРЕНОСИТЬ.
- **Fix:** заведён переводчик `red_record.py` в рабочем каталоге сессии (в дерево НЕ вносится, приём плана 10-56): он ИСПОЛНЯЕТ команду и собирает запись ИЗ ЕЁ ВЫВОДА — имена из строк `FAILED …::имя`, числа из итоговой строки.
- **Verification:** `check tdd-red-evidence` → `RED_EVIDENCE_OK` / `target_test_failed`; прогон дал `3 failed`, целевой тест покраснел утверждением `assert 404 == 204`.
- **Committed in:** `abe9bf4`

**2. [Rule 3 — Blocking] Гейт имперсонации: новый маршрут объявлен поимённо**

- **Found during:** Задача 1, `<verify>` (правило названо разведкой как G-7 — ТРЕТИЙ перечень, которого критерий 3 не называет)
- **Issue:** обход требует, чтобы КАЖДОЕ изменяющее объявление маршрута стояло либо в перечне запрещённого, либо в `ALLOWED_ROUTES` с причиной; новый маршрут ронял три правила.
- **Fix:** запись `"app/pages/ads.py::ads_images_upload": "загрузка картинки объявления"` внесена; `MUTATING_ROUTE_COUNT` 49 → 50 прогоном покрасневшего правила. Старая запись `app/routes/uploads.py::upload_image` НЕ снята — окно сосуществования названо комментарием и закрывается планом 12-05.
- **Verification:** `tests/test_pages/test_access_gate.py tests/test_pages/test_impersonation_gate.py` → 35 passed (тот же базовый счёт, что до работ).
- **Committed in:** `82cc55a`

**3. [Rule 3 — Blocking] Комментарий о зависимости доступа вынесен над объявлением обработчика**

- **Found during:** Задача 1, сверка `<acceptance_criteria>`
- **Issue:** критерий «гейт не переписан в теле» проверяется срезом `awk '/^async def ads_images_upload/,/^@router/' | grep -c 'require_access'` — и упоминание имени зависимости в ДОКСТРИНГЕ обработчика давало 1 вместо 0.
- **Fix:** абзац-обоснование перенесён выше декоратора; в докстринге осталась ссылка на него без имени зависимости. Знание не потеряно, а сдвинуто на строку.
- **Verification:** срез возвращает `0`; три теста модуля зелены.
- **Committed in:** `82cc55a`

**4. [Rule 3 — Blocking] Четыре перечня разметочных гейтов получили нового вызывающего**

- **Found during:** Задача 2, `<verify>`
- **Issue:** форма загрузки — новый вызывающий макроса-обёртки с целью подмены и пустой целью блокировки; четыре правила покраснели одновременно.
- **Fix:** вызывающий объявлен поимённо в `MACRO_DEFINITION_SITES_CALLERS`, `PARAMETRIC_SWAP_TARGETS` и `DISABLED_ELT_EXCEPTIONS`; числа `UNREACHABLE_TARGET_CALL_BLOCKS_MEASURED` 14 → 15, `MACRO_DEFINITION_SITES_CALLERS_DECLARED` 22 → 23, `PARAMETRIC_SWAP_TARGETS_CALLERS_DECLARED` 7 → 8 — все прогоном покрасневшего правила. Три снимаемых правила (G-9, G-11, G-12) проверены ЗАМЕРОМ, а не положены: цель печатается страницей безусловно, внеполосного узла с этим идентификатором в дереве нет, признака клиентского состояния — ноль вхождений.
- **Verification:** `test_htmx_markup_gates.py` + `test_components.py` → 171 passed.
- **Committed in:** `839bbe1`

**5. [Rule 3 — Blocking] Пять инвентарных чисел, видимых ТОЛЬКО полному прогону**

- **Found during:** проверка плана (`uv run pytest tests/ -q`) — девять красных правил в четырёх файлах, которых быстрые прогоны затронутых файлов по построению не видят (G-10)
- **Issue:** новый POST-обработчик страничного слоя двигает вторую, независимую меру того же множества (`PAGE_POST_HANDLERS_MEASURED`), счёт фрагментных обработчиков, реестр пар транспортов и карту назначений заголовка перехода.
- **Fix:** `POST_HANDLERS` 36 → 37, `FRAGMENT_RESPONSE_HANDLERS` +ключ и число 12 → 13, `POST_PAIR_CASES` +два случая и число 48 → 50, `PAIRED_302_ASSERTIONS_DECLARED` 158 → 159, `HX_LOCATION_DESTINATION_CALLS_DECLARED` 72 → 73, `PAGE_POST_HANDLERS_MEASURED` 36 → 37. Каждое — прогоном покрасневшего правила, каждое — со строкой летописи.
- **Verification:** повторный ПОЛНЫЙ прогон: `3415 passed, 0 failed, 2246.08s`, код выхода 0 (базовый прогон до работ — `3410 passed`; прибавка пять — три теста нового модуля и два случая пары).
- **Committed in:** `71c3788`

---

**Total deviations:** 5 auto-fixed (все Rule 3 — блокирующие: без них правила суиты красны).
**Impact on plan:** ни одна правка не ослабила правило. Четыре из пяти — записи инвентаря, требуемые D-13 самим планом; пятая — форма улики RED. Расширения объёма нет.

## TDD Gate Compliance

| Gate | Коммит | Статус |
|------|--------|--------|
| RED | `abe9bf4` `test(12-01)` | ✓ улика проверена: `check tdd-red-evidence` → `RED_EVIDENCE_OK` / `target_test_failed` |
| GREEN | `82cc55a` `feat(12-01)` | ✓ RED предшествует GREEN; три теста модуля зелены |
| REFACTOR | — | не заводился: улучшать после GREEN было нечего, и отсутствие необязательного этапа записано, а не умолчано |

Гейт `execute-mvp-tdd` (TDD_MODE=true) проверен перед шагом реализации задачи 1: коммит `test(12-01)` существует и трогает `tests/`, улика RED признана намеренной, `feat(12-01)`-коммита до него нет. Гейт НЕ сработал.

⚠️ **Целевым тестом улики выбран не первый тест модуля, и это решение, а не удобство.** Два теста из трёх краснели в RED-фазе `ModuleNotFoundError` от подмены записи в хранилище — модуля сервиса ещё не существовало. Такое покраснение есть сбой ЗАГРУЗКИ, а не утверждение о поведении, и правило #3770 отвергает его как `fixture_or_load_failure`. Третий тест — гейт доступа — подмены не требует вовсе и покраснел настоящим утверждением: `assert 404 == 204`. Он и назван целевым.

## Known Stubs

Плановые, названные планом ПОИМЁННО как недостающая половина среза, а не как принятое решение (`<scope_note>` плана):

| Что | Файл | Почему сейчас нет | Кто закрывает |
|---|---|---|---|
| Сверка принадлежности присланных ключей (`own_image_keys`) и расчёт свободных мест | `app/pages/ads.py::ads_images_upload` | срез несёт архитектуру целиком и ровно один путь по ней; последним рубежом владения остаётся СОХРАНЕНИЕ объявления, которое фаза не двигает | план 12-04 |
| Полоса и форма загрузки не подключены к странице редактора | `app/templates/ads/form.html` | подключение снимает клиентскую сборку плиток и роняет гейты безопасности редактора, которым нужна своя задача | план 12-03 |
| Старый модуль `app/routes/uploads.py` и его суита в 1099 строк остаются на месте | `app/routes/uploads.py` | снять раньше значило бы покраснить 1099 строк утверждений, которым ещё нечем заменить предмет | план 12-05 |

## Threat Flags

Новой поверхности, не названной `<threat_model>` плана, не появилось. Меры по трём `mitigate`-угрозам, которые задача обязана была применить, применены и наблюдаемы: тип берётся по содержимому (T-12-01), сегменты пути отбрасываются `safe_filename` (T-12-02), порционное чтение прерывается на первом превышении (T-12-03), число частей ограничено явно (T-12-04), маршрут закрыт зависимостью роутера (T-12-06).

## Issues Encountered

- **Полный прогон суиты стоит 37 минут, и цена эта подтвердилась дважды** (2227 с до работ, 2246 с после). Оба прогона плану были нужны: первый нашёл девять красных правил, второй подтвердил зелёное дерево. Быстрые прогоны затронутых файлов этих правил не видят по построению — это и есть причина, по которой G-10 требует обе меры.
- **Нестабильный `test_image_base_url_comes_from_app_settings`** прошёл в обоих полных прогонах и в одиночном. Как и в базовом замере, это наблюдение прогонов, а не вывод «нестабильность исчезла».

## User Setup Required

None — внешних сервисов задача не настраивает и ни одного пакета не устанавливает.

## Next Phase Readiness

- Готово для 12-02 (потолок тела запроса в шаблонах nginx) — работа независима и ни одного файла этого плана не трогает.
- Готово для 12-03 (подключение полосы и формы к странице редактора): единственный источник разметки есть, идентификатор `#media-tray` для внеполосной цели заведён и объяснён.
- ⚠️ Планам 12-03 и 12-04 придётся двигать те же инвентарные числа: `FRAGMENT_RESPONSE_HANDLERS` не тронется, а `OOB_BLOCKS` 19 → 20 и записи вызывающих — да. Числа ставить ПРОГОНОМ покрасневшего правила и закладывать полный прогон суиты в каждую задачу.

---
*Phase: 12-zagruzka-izobrazheniy-bez-fetch*
*Completed: 2026-09-18*

## Self-Check: PASSED

- Файлы `key-files.created` существуют на диске: `app/services/image_upload.py`, `app/templates/ads/includes/media_strip.html`, `app/templates/ads/includes/media_upload_form.html`, `tests/test_pages/test_ads_image_upload.py` — четыре из четырёх.
- Коммиты `abe9bf4`, `82cc55a`, `839bbe1`, `71c3788` найдены в `git log --oneline --all`; измеренный счёт `git rev-list --count c1f8e2e..HEAD` — 4, и он же записан во frontmatter.
- Все `<acceptance_criteria>` обеих задач перепрогнаны после последней правки: 7 из 7 у задачи 1, 6 из 6 у задачи 2.
- `<verification>` плана исполнена целиком: полный прогон `3415 passed`, код выхода 0; `compileall` молчит; `graphify update .` выполнен (21310 узлов).
