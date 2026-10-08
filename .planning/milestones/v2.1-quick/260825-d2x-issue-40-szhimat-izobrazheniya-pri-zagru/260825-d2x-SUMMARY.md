---
phase: quick-issue-40-compress-on-upload-and-serve-thumbnails
plan: 01
subsystem: api
tags: [pillow, images, s3, jinja2, fastapi, uploads, thumbnails]

requires:
  - phase: quick-260825-abl (issue #39)
    provides: "Приём сужен до JPEG и PNG по сигнатуре содержимого — эта задача опирается на него и не расширяет"
provides:
  - "app/services/images.py — сжатие на входе (длинная сторона ≤ 1920, JPEG q85) и миниатюра (≤ 480, q75) за ОДНО декодирование"
  - "Явный потолок числа точек MAX_DECODED_PIXELS, снимаемый с заголовка ДО распаковки пикселей"
  - "thumb_key() — производный ключ под приставкой, которую own_image_keys пройти не может"
  - "thumb_image_url — четвёртый шаблонный глобал, терпящий и ключи, и полные адреса из SendLog"
  - "components/thumb.html — единственный способ показать вложение: миниатюра плюс объявленный запасной адрес"
affects: [uploads, ads-editor, history, admin-history, messengers-delivery]

actuals:
  tokens: 35173
  tasks: 3
  commits: 9

tech-stack:
  added: ["pillow>=11.3.0 (объявлена явно; в дерево зависимостей НЕ входит впервые — уже была транзитивной через qrcode[pil], версия 12.1.1 не сдвинулась)"]
  patterns:
    - "Декодирование недоверенного файла допускается только за явным потолком числа точек, снятым с заголовка"
    - "Счётная работа внутри async-обработчика выносится asyncio.to_thread — воркер один"
    - "Производный ключ объекта живёт под приставкой, которую образец хранимого ключа не может сопоставить"
    - "Шаблонный глобал, зависящий от настроек, читает модульную переменную в момент вызова, а не замыкает значение"

key-files:
  created:
    - app/services/images.py
    - app/templates/components/thumb.html
    - tests/test_services/test_images.py
    - tests/test_services/test_image_keys.py
  modified:
    - app/routes/uploads.py
    - app/services/image_keys.py
    - app/pages/common.py
    - app/templates/ads/form.html
    - app/templates/ads/includes/preview.html
    - app/templates/ads/includes/ad_card.html
    - app/templates/history/detail.html
    - app/templates/admin/user_history_detail.html
    - tests/test_routes/test_uploads.py
    - tests/test_pages/test_ads_editor.py
    - tests/test_templates/test_components.py
    - tests/test_pages/test_responsive_markup.py
    - pyproject.toml

key-decisions:
  - "Оригинал не сохраняется ни под каким ключом — в бакет уходит только произведённое приложением (D-2)"
  - "PNG без НАСТОЯЩЕЙ альфы пережимается в JPEG, признак снимается с фактического канала, а не с имени режима (D-4)"
  - "Расширение ключа приводится к сохранённому формату БЕЗУСЛОВНО — на него опирается Telethon (P-5)"
  - "Провал сохранения миниатюры не проваливает запрос: механизм отката всё равно обязан существовать ради старых ключей (P-7)"
  - "Откат объявлен на самом элементе img (data-full + однократный onerror), а не проверкой существования объекта в S3 (P-8)"
  - "Режим изображения нормализуется ДО уменьшения: Pillow не применяет качественный фильтр к палитре"
  - "Шаблонные глобалы изображений перестали замыкать базовый URL по значению — Jinja кеширует модуль шаблона и замораживал его"

patterns-established:
  - "Потолок ресурса проверяется на метаданных, а не на результате: заявленные размеры сверяются до load()"
  - "Производный объект хранилища получает префикс, выбранный так, чтобы НЕ проходить проверку владения"
  - "Второй объект загрузки необязателен для успеха запроса, если у интерфейса уже есть путь без него"

requirements-completed: [ISSUE-40]

coverage:
  - id: D1
    description: "Загруженное изображение сжимается до длинной стороны 1920 (JPEG q85), меньшее не увеличивается"
    requirement: ISSUE-40
    verification:
      - kind: unit
        ref: "tests/test_services/test_images.py#test_large_image_is_reduced_to_the_delivery_limit"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_images.py#test_small_image_is_never_upscaled"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_uploads.py#test_stored_image_is_reduced_to_the_delivery_limit"
        status: pass
    human_judgment: false
  - id: D2
    description: "Одна загрузка даёт ровно два объекта — сжатую версию и миниатюру; оригинала среди них нет"
    requirement: ISSUE-40
    verification:
      - kind: integration
        ref: "tests/test_routes/test_uploads.py#test_upload_stores_exactly_the_delivery_image_and_its_thumbnail"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_uploads.py#test_original_bytes_reach_no_object_at_all"
        status: pass
    human_judgment: false
  - id: D3
    description: "Ключ из ответа проходит own_image_keys; ключ миниатюры она отвергает"
    requirement: ISSUE-40
    verification:
      - kind: integration
        ref: "tests/test_routes/test_uploads.py#test_returned_key_still_passes_the_ownership_check"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_image_keys.py#test_a_thumbnail_key_is_not_a_storable_attachment"
        status: pass
    human_judgment: false
  - id: D4
    description: "Декомпрессионная бомба отвергается 400 до обращения к хранилищу; EXIF применён к пикселям и снят с байтов"
    requirement: ISSUE-40
    verification:
      - kind: unit
        ref: "tests/test_services/test_images.py#test_image_over_the_pixel_ceiling_is_refused"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_images.py#test_exif_section_is_stripped_from_stored_bytes"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_uploads.py#test_upload_rejects_a_decompression_bomb_before_touching_storage"
        status: pass
    human_judgment: false
  - id: D5
    description: "Все пять мест показа запрашивают миниатюру и несут запасной полноразмерный адрес"
    requirement: ISSUE-40
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_thumbnail_macro_is_the_only_way_an_attachment_is_shown"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_editor.py#test_editor_tile_asks_for_the_thumbnail_and_declares_a_fallback"
        status: pass
    human_judgment: false
  - id: D6
    description: "Вложение, загруженное ДО этой задачи, всё ещё показывается: браузер переключается на полноразмерный адрес после одного холостого запроса"
    verification: []
    human_judgment: true
    rationale: "Проверяемое — поведение БРАУЗЕРА на отсутствующем объекте в реальном бакете. Тест удостоверяет, что элемент несёт оба адреса и однократный переключатель, но что переключение действительно происходит и картинка появляется, видно только глазами на боевом хранилище со старым ключом."

duration: 95min
completed: 2026-08-25
status: complete
---

# Quick 260825-d2x (issue #40): сжатие при загрузке и миниатюры для интерфейса

**`POST /api/uploads/image` за одно декодирование кладёт в S3 сжатую версию (длинная сторона ≤ 1920, JPEG q85) и её миниатюру (≤ 480, q75), оригинал не сохраняется вовсе, а все пять мест показа запрашивают миниатюру и умеют откатиться на полноразмерный адрес там, где её нет.**

## Performance

- **Duration:** ~95 min
- **Tasks:** 3 из 3
- **Files modified:** 18 (4 создано, 14 изменено)
- **Commits:** 9 (по циклу красный тест → реализация)

## Accomplishments

- **Обе половины issue закрыты одним проходом по файлу.** Один декод — два кодирования: миниатюра строится из уже уменьшенной картинки, исходные байты второй раз не разбираются.
- **Снят класс уязвимости, который задача сама и открывала.** Проект до этого сознательно не открывал недоверенный файл декодером. Запрет снят, но взамен введён потолок `MAX_DECODED_PIXELS = 30_000_000`, снимаемый с ЗАГОЛОВКА до `load()`, `draft()` для JPEG и перехват `DecompressionBombError` вторым рубежом.
- **Побочно закрыта утечка, которой в issue не было.** До этой задачи снимок с телефона уезжал в ПУБЛИЧНЫЙ бакет вместе с координатами съёмки и серийным номером камеры. Теперь EXIF применяется к пикселям и в сохранённые байты не переносится (T-Q40-05).
- **Миниатюра не может стать вложением.** Приставка `thumbs/` выбрана так, что образец ключа объявления её не сопоставляет; закреплено именованной регрессией, а не рассуждением.
- **Пользователь перестал читать неправду об отказе.** `uploadFile()` теперь показывает `detail` сервера: отказ по числу точек и по размеру тела больше не выглядят жалобой на формат.

## Task Commits

1. **Task 1: Сжатие и миниатюра как чистые функции** — `79ebe3f` (test) → `0a0abe1` (feat) → `40aa459` (refactor) → `0b08907` (fix)
2. **Task 2: Эндпоинт — два объекта вместо одного** — `2fca06c` (test) → `f0a2eb0` (feat)
3. **Task 3: Интерфейс запрашивает миниатюру** — `bad5054` (test) → `1c9c258` (feat) → `62fae50` (test, инвентарь библиотеки)

## Files Created/Modified

- `app/services/images.py` — потолок до декодирования, `draft()` для JPEG, EXIF в пиксели и прочь из байтов, правило формата по фактической альфе, миниатюра из уже уменьшенной картинки.
- `app/services/image_keys.py` — `THUMB_KEY_PREFIX` и идемпотентный `thumb_key()`.
- `app/routes/uploads.py` — подготовка в потоке, приведение расширения к сохранённому формату, два сохранения, свой текст отказа по потолку; абзац шапки про неприменение декодера переписан.
- `app/pages/common.py` — глобал `thumb_image_url`, глобал `THUMB_KEY_PREFIX`, базовый URL переведён на чтение в момент вызова.
- `app/templates/components/thumb.html` — единственный макрос показа вложения.
- Пять файлов-потребителей переведены на макрос; ссылки в истории и админке по-прежнему ведут на полноразмерный объект.

## Decisions Made

Все решения владельца (D-1…D-6) и планировщика (P-1…P-9) выполнены как написано. Два решения принято по ходу, оба — следствия обнаруженных дефектов, см. «Deviations».

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Шаблонные глобалы изображений замерзали в кешированном модуле Jinja**

- **Found during:** Task 3
- **Issue:** `_bind_image_url_globals` создавал лямбды, ЗАМЫКАЮЩИЕ базовый URL по значению. Jinja кеширует `Template._module`: модуль библиотечного шаблона создаётся при первом импорте, и в его снимок попадают объекты глобалов, бывшие там на тот момент. Следующий `create_app` переписывал `env.globals` мимо снимка. Наблюдалось так: страница списка объявлений отдавала `src="/thumbs/u1/photo.jpg"` — адрес без хоста, — хотя `env.globals` в тот же момент отдавал правильный. Расхождение молчаливое, без единого исключения. Дефект существовал до задачи; макрос `thumb` лишь стал первым потребителем, у которого он проявился.
- **Fix:** базовый URL переведён в модульную переменную, глобалы читают её В МОМЕНТ ВЫЗОВА. Снимок держит ту же функцию, а она смотрит на текущее значение. Контракт D-21 не изменён: URL по-прежнему приезжает из настроек приложения, по-прежнему выигрывает последний `create_app`.
- **Files modified:** `app/pages/common.py`
- **Verification:** `tests/test_pages/test_ads_editor.py` — 45 тестов, включая три упавших на этом дефекте.
- **Committed in:** `1c9c258`
- **Побочный эффект, названный отдельно:** этим же исправлен открытый пункт `full-suite-ads-editor-order-pollution` — `test_image_base_url_comes_from_app_settings` был красным в полном прогоне ровно по этой причине и теперь зелёный. Пункт можно закрывать.

**2. [Rule 1 — Bug] Палитровое изображение уменьшалось ближайшим соседом**

- **Found during:** Task 1 (найдено при разборе собственного кода после GREEN)
- **Issue:** Pillow ВСЕГДА берёт ближайшего соседа для режимов `P` и `1` — интерполировать номера цветов в палитре бессмысленно. Логотип, уменьшенный так с 2400 px до 1920 и далее до 480, приходит с рваными краями. То есть задача, затеянная ради вида и веса картинок, портила бы ровно те, у которых палитра и заведена. Рядом стояли ещё две мелочи: подкладывание альфы строило ДВЕ полные RGBA-копии кадра, а полутоновый JPEG приводился к RGB, утраивая вес.
- **Fix:** режим нормализуется ОДИН раз до уменьшения (`_normalise_mode`): RGBA при сохраняемой альфе, иначе RGB с белой подложкой, `L` сохраняется как есть.
- **Files modified:** `app/services/images.py`, `tests/test_services/test_images.py`
- **Verification:** новые `test_palette_image_leaves_the_palette_before_it_is_resized`, `test_grayscale_jpeg_is_not_inflated_to_three_channels`; весь файл службы (31) и маршрута (54) зелёные.
- **Committed in:** `0b08907`

**3. [Rule 3 — Blocking] Двусторонние инвентари библиотеки компонентов**

- **Found during:** Task 3 (полный прогон)
- **Issue:** `test_billing_component_library_did_not_grow` и `test_template_inventory` пинуют число файлов в `components/` ДВАЖДЫ, чтобы новый компонент не вошёл в библиотеку молча.
- **Fix:** оба числа подняты 14 → 15 ТЕМ ЖЕ коммитом, что и файл, с объяснением, какой файл пятнадцатый и зачем он. Правки задним числом не делалось — комментарий на обоих местах прямо это запрещает.
- **Files modified:** `tests/test_pages/test_responsive_markup.py`
- **Committed in:** `62fae50`

---

**Total deviations:** 3 auto-fixed (2 × Rule 1, 1 × Rule 3)
**Impact on plan:** Ни одна правка не расширяет предмет задачи. Две первые — дефекты, которые эта задача либо обнажила, либо внесла бы, не будь исправлена; третья — предусмотренная авторами инвентаря процедура. Границы соблюдены: `app/messengers/`, `wa_worker/`, `max_worker/` не тронуты ни строкой, `own_image_keys` и форма ключа `Ad.images` не менялись.

## Issues Encountered

**Тесты службы изображений стоили 36 с на прогон.** Поэлементный обход 4000×3000 на чистом Python — десятки секунд каждого прогона суиты ради данных, от которых нужно единственное свойство: не сжиматься в ноль. Построитель переведён на набор картинки вставками плитки 64×64 (`40aa459`), стоимость перестала зависеть от разрешения: 36 с → 13 с.

**`make_jpeg_bytes()` в тестах маршрута отдаёт недекодируемые байты.** Для проверок `sniff_image` этого хватало, для HTTP-пути — больше нет. Построитель НЕ удалён: класс входа «сигнатура верна, картинки нет» никуда не делся, изменился ответ на него, и это закреплено собственным тестом `test_upload_rejects_signature_without_a_decodable_image`.

## Known Stubs

Нет. Заглушек, пустых значений в сторону интерфейса и невыполненных `<verify>` не осталось.

## Deferred Issues

**`test_the_machine_readable_progress_is_derived_from_the_roadmap` — красный ДО задачи и остаётся красным.**

`progress.total_plans` и `progress.completed_plans` во frontmatter `.planning/STATE.md` записаны как 110/110, а из отметок `.planning/ROADMAP.md` выводится 0/0. Ни один из трёх участвующих файлов этой задачей не менялся (`git diff HEAD -- .planning/` пуст), числа в отказе совпадают с числами на базовом коммите — то есть тест был красным до первого коммита issue #40. Это расхождение учётных файлов планирования, а не кода; «подгонка» поля STATE.md попутным коммитом отключила бы проверку, которая ровно это расхождение и ловит. Записано в `deferred-items.md` рядом с этим файлом.

Полный прогон итогового дерева: **2235 passed, 1 failed** — этот самый тест и
никакой другой. Тот же прогон без `tests/test_planning` даёт **0 failed**.

## Threat Flags

Нет. Новой сетевой поверхности, новых путей аутентификации и изменений схемы задача не вносит. Единственная новая поверхность — декодирование недоверенного файла — заявлена в `<threat_model>` плана как T-Q40-01 и закрыта потолком.

## User Setup Required

Нет. Новых переменных окружения и внешних настроек не появилось. `pillow` в образ входит не впервые — она уже стояла транзитивно через `qrcode[pil]`, версия (12.1.1) не сдвинулась, `uv.lock` изменился ровно двумя строками объявления.

## Next Phase Readiness

- Уже сохранённые объекты не переписаны и не переименованы — сжатие действует на входе и только вперёд. У старых вложений миниатюры нет, и интерфейс это переживает штатно.
- Отдельной работой своего размера остаётся построитель миниатюр по требованию для старых ключей (план вынес его в `<non_goals>` сознательно) и правило жизненного цикла бакета для префикса `thumbs/` — приставка выбрана в том числе ради него.

## Self-Check: PASSED

- Четыре созданных файла кода и оба артефакта планирования существуют на диске.
- Все девять названных коммитов найдены в `git log`.
- Полный прогон суиты на итоговом дереве: **2235 passed, 1 failed** — единственный
  красный — `test_the_machine_readable_progress_is_derived_from_the_roadmap`,
  разобранный выше в «Deferred Issues» как красный ДО задачи и не относящийся к
  её файлам.

---
*Quick task: 260825-d2x (GitHub issue #40)*
*Completed: 2026-08-25*
