---
phase: 02-obyavleniya-i-raspisaniya
plan: 10
subsystem: api
tags: [fastapi, starlette, uploads, regex, layering, pytest, tdd, dos]

# Dependency graph
requires:
  - phase: 02-02
    provides: "own_image_keys, INACCESSIBLE_IMAGE_MESSAGE, форма ключа вложения и серверный лимит"
  - phase: 02-08
    provides: "контракт автосохранения, маршрутизация ad_id из тела, хелперы tests/test_pages/test_ads_editor.py"
  - phase: 02-09
    provides: "образец нейтрального модуля правил (app/services/schedule_rules.py) и защита от нестрокового значения в _clean_times"
provides:
  - "app/services/image_keys.py — единственное место, где определены форма ключа вложения и правило владения им"
  - "Точное сопоставление ключа (fullmatch без якорей) и сравнение префикса как строки"
  - "UPLOAD_CHUNK_SIZE и потоковое чтение тела загрузки с прерыванием на первом превышении предела"
  - "Отказ 400 на файловую часть в поле вложений вместо ошибки 500"
  - "ad_status — параметр обработчика с именем на проводе `status`, снятое затенение модуля ответов"
  - "Регрессия объёма чтения: обёртка над UploadFile.read, измеряющая размер порций"
affects: [02-11, 02-12, 02-VERIFICATION, 02-REVIEW, ads-editor, uploads]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
# Same estimateTokens scale (chars/4 over the realized diff), never a harness token count.
actuals:
  tokens: 35369
  tasks: 3
  commits: 4

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Правило, нужное двум слоям, живёт в НЕЙТРАЛЬНОМ модуле — второй случай после app/services/schedule_rules.py, и теперь это образец, а не разовое решение"
    - "Предел размера применяется ПО МЕРЕ ЧТЕНИЯ: ограничивается принимаемое, а не только сохраняемое"
    - "Тест на предел ресурса измеряет ПОТРЕБЛЕНИЕ, а не код ответа: код 400 возвращается и на дефектном коде"
    - "Значение поля формы проверяется на тип ДО строковой операции; несоответствие — отказ, а не отбрасывание"
    - "Имя параметра обработчика не затеняет имён модуля; имя на проводе сохраняется алиасом"

key-files:
  created:
    - app/services/image_keys.py
  modified:
    - app/pages/ads.py
    - app/routes/ads.py
    - app/routes/uploads.py
    - tests/test_pages/test_ads_image_ownership.py
    - tests/test_pages/test_ads_editor.py
    - tests/test_routes/test_uploads.py

key-decisions:
  - "Форма ключа сопоставляется `fullmatch` по образцу БЕЗ якорей: якорь `$` в Python совпадает и непосредственно перед завершающим переводом строки, поэтому снять `$` мало — нужно сменить и метод сопоставления"
  - "Префикс сравнивается со СТРОКОВЫМ представлением user_id, а первый разряд образца сделан ненулевым: две независимые преграды одному и тому же `007/…`, потому что ключ обязан быть ровно тем, что выдала загрузка"
  - "Порядок проверок в upload_image изменён намеренно: при потоковом чтении предел неизбежно срабатывает раньше, чем содержимое целиком доступно для распознавания. Оба отказа — 400, ни один вход не стал мягче"
  - "Файловая часть в поле вложений даёт ОТКАЗ, а не отбрасывание: молча выброшенная часть сохранила бы объявление без вложений — та же причина, по которой own_image_keys отказывает"
  - "Тест WR-02 измеряет объём чтения, а не код ответа: утверждение `400` зелено и на дефектном коде, где предел проверяется после полной буферизации тела"
  - "Обёртка чтения кладётся на starlette.datastructures.UploadFile, а класс, пришедший в обработчик, ИЗМЕРЯЕТСЯ: подкласс FastAPI передаёт размер в базовый метод явно, и на нём «вызов без аргумента» стал бы неразличим"
  - "Порог счётчика проверяется по атрибуту class САМОГО счётчика: те же имена классов есть в узловой сборке, и проверка по всей странице зелена при любом пороге"

patterns-established:
  - "Красная фаза фиксируется отдельным коммитом и проверяется прогоном, СУЖЁННЫМ по именам; наблюдённый исход каждого падения вносится в SUMMARY"
  - "Тесты, красной фазы не имеющие, объявляются стражами в самом файле теста, а не только в плане"
  - "Регрессия на предел ресурса оборачивает точку потребления записывающей обёрткой и утверждает объём, а не исход"

requirements-completed: [ADS-05]

coverage:
  - id: D1
    description: "Ключ вложения с завершающим переводом строки отклоняется на всех четырёх входах записи Ad.images и не попадает в базу (WR-01, T-02G-12)"
    requirement: "ADS-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_key_with_trailing_newline_is_refused[page-create]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_key_with_trailing_newline_is_refused[page-update]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_key_with_trailing_newline_is_refused[api-create]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_key_with_trailing_newline_is_refused[api-update]"
        status: pass
    human_judgment: false
  - id: D2
    description: "Ключ с ведущим нулём в префиксе отклоняется на тех же четырёх входах: `007/…` больше не принимается за `7/…` (WR-01, T-02G-12)"
    requirement: "ADS-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_key_with_leading_zero_prefix_is_refused[page-create]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_key_with_leading_zero_prefix_is_refused[page-update]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_key_with_leading_zero_prefix_is_refused[api-create]"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_key_with_leading_zero_prefix_is_refused[api-update]"
        status: pass
    human_judgment: false
  - id: D3
    description: "Ужесточение формы не превратилось в отказ по всему классу: корректный собственный ключ по-прежнему принимается на всех четырёх входах"
    requirement: "ADS-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_own_key_is_accepted_on_every_entrance"
        status: pass
    human_judgment: false
  - id: D4
    description: "Предел размера загрузки применяется ПО МЕРЕ ЧТЕНИЯ: обработчик не запрашивает содержимое без ограничения размера, и суммарно прочитанное не превышает предел более чем на одну порцию (WR-02, T-02G-13)"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_uploads.py#test_oversized_upload_is_not_buffered_whole"
        status: pass
      - kind: unit
        ref: "tests/test_routes/test_uploads.py#test_read_measurement_targets_the_class_the_handler_receives"
        status: pass
    human_judgment: false
  - id: D5
    description: "Текст и код отказа по размеру не изменились: `File size exceeds {N}MB limit`, код 400, в хранилище ничего не уходит"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_uploads.py#test_oversized_upload_is_refused_with_size_message"
        status: pass
    human_judgment: false
  - id: D6
    description: "Правило ключа живёт в одном месте, от которого зависят оба слоя: JSON-API объявлений больше не импортирует из страничного (WR-04, T-02G-16)"
    verification:
      - kind: other
        ref: "grep -v '^#' app/routes/ads.py | grep -c 'app.pages.ads' == 0"
        status: pass
      - kind: other
        ref: "python -c \"import sys, app.routes.ads; assert 'app.pages.ads' not in sys.modules and 'app.pages.common' not in sys.modules\""
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_ads.py (полный модуль — JSON-вход берёт правило из нейтрального модуля)"
        status: pass
    human_judgment: false
  - id: D7
    description: "Многочастный POST на /ads/{id}/edit с полем `images` в виде файловой части отвечает 400, а не 500, и список ключей объявления не меняется (WR-03, T-02G-14)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_editor.py#test_multipart_file_part_in_images_is_refused"
        status: pass
    human_judgment: false
  - id: D8
    description: "Переименование параметра сняло затенение имени модуля ответов, не изменив контракт провода: поле `status` принимается под тем же именем и меняет состояние только на значение из словаря (WR-08, T-02G-15)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_editor.py#test_status_field_keeps_its_wire_name"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_editor.py#test_explicit_save_publishes_autosave_does_not"
        status: pass
    human_judgment: false
  - id: D9
    description: "Граница лимита вложений закрыта с обеих сторон: ровно `max_images_per_ad` сохраняется, на единицу больше — 400 и Ad.images не меняется (ADS-05)"
    requirement: "ADS-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_editor.py#test_attachment_limit_is_a_closed_boundary"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_ads_create_accepts_exactly_the_limit"
        status: pass
    human_judgment: false
  - id: D10
    description: "Порог предупреждения счётчика выбирается по наличию вложений (CAPTION_LIMIT против девяти десятых TEXT_LIMIT) и ни один порог не блокирует сохранение и не обрезает текст (UI-SPEC E1 `overflow`)"
    requirement: "ADS-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_editor.py#test_counter_threshold_follows_the_presence_of_attachments"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_editor.py#test_editor_counter_is_server_rendered"
        status: pass
    human_judgment: false

# Metrics
duration: 35min
completed: 2026-08-11
status: complete
---

# Phase 02 Plan 10: Закрытие предупреждений код-ревью Summary

**Правило ключа вложения поднято в нейтральный `app/services/image_keys.py`, сопоставляется точно и сравнивает префикс как строку; предел загрузки прерывает чтение вместо проверки после полной буферизации тела; файловая часть в поле вложений отвечает отказом, а не пятисотым**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-08-11T06:45:00Z
- **Completed:** 2026-08-11T07:20:00Z
- **Tasks:** 3
- **Files created:** 1
- **Files modified:** 6

## Accomplishments

- **WR-01 закрыт двумя независимыми преградами.** Образец был заякорен `^…$` и сопоставлялся методом `match`; якорь `$` в Python совпадает и непосредственно перед завершающим переводом строки, поэтому `"{user_id}/{32 hex}_a.png\n"` проходил проверку владения и ложился в `Ad.images` дословно — оттуда он попадает в адрес изображения, в карточку, в историю и в адаптеры мессенджеров. Теперь якорей нет, сопоставление идёт `fullmatch`, префикс сравнивается со строковым представлением `user_id`, а первый разряд образца ненулевой.
- **WR-02 закрыт по существу, и это подтверждено измерением.** `content = await file.read()` материализовал всё тело до того, как предел вообще проверялся: `max_image_size_mb` ограничивал СОХРАНЯЕМОЕ, а не ПРИНИМАЕМОЕ, и любой аутентифицированный клиент заставлял ASGI-воркер удерживать в памяти тело произвольного размера. Чтение идёт порциями по 64 КБ и прерывается на первом же превышении. Тест меряет ОБЪЁМ ЧТЕНИЯ, а не код ответа: утверждение «400» зелено и на дефектном коде.
- **WR-04 закрыт с проверяемым следствием.** `app/routes/ads.py` больше не импортирует из страничного слоя; после `import app.routes.ads` ни `app.pages.ads`, ни `app.pages.common` в `sys.modules` не появляются — окружение Jinja, глобалы изображений и шесть модулей моделей ушли из графа импорта JSON-API.
- **WR-03 воспроизведён отдельным красным коммитом и закрыт им же.** Многочастный запрос с файловой частью в поле `images` давал `AttributeError: 'UploadFile' object has no attribute 'strip'` → 500. Теперь — отказ 400 с тем же текстом, что у прочих отказов по вложениям.
- **WR-08 снят без изменения контракта провода.** Параметр `status` затенял импортированный модуль ответов FastAPI на всё тело `ads_update`; переименован в `ad_status` с `alias="status"`.
- **Все три воспроизводимых дефекта закрыты тестами, которые падали ДО правки.** Тест и исправление не написаны в одном движении ни разу — ровно то, ради чего этот прогон закрытия пробелов существует.

## Task Commits

1. **Task 1 (RED): тесты воспроизводят форму ключа и полную буферизацию тела** — `2332b8d` (test)
2. **Task 2 (GREEN): нейтральный модуль правила ключа и потоковый предел загрузки** — `45c2c13` (feat)
3. **Task 3 (RED): файловая часть в поле вложений** — `7425531` (test)
4. **Task 3 (GREEN): отказ на файловую часть и снятие затенения имени** — `de3ebba` (fix)

REFACTOR-коммита нет: перенос правила в нейтральный модуль — сама суть GREEN-задачи, чистить после неё было нечего.

## TDD Gate Compliance

| Gate | Commit | Статус |
|---|---|---|
| RED (задачи 1–2) | `2332b8d` (`test(02-10): …`) | ✓ Девять утверждений упали на текущем коде |
| GREEN (задача 2) | `45c2c13` (`feat(02-10): …`) | ✓ Те же девять зелёные; 108 тестов прогона верификации зелёные |
| RED (задача 3) | `7425531` (`test(02-10): …`) | ✓ Отдельным коммитом ДО правки `app/pages/ads.py` |
| GREEN (задача 3) | `de3ebba` (`fix(02-10): …`) | ✓ Полная суита 877 passed |

Красные фазы проверены прогонами, СУЖЁННЫМИ по именам (`-k`), а не кодом возврата конвейера `pytest | grep`: код возврата конвейера принадлежит `grep` и «проходил» бы на любом падении модуля. Наблюдённые исходы — по существу дефекта, ни одного постороннего имени в сводке:

| Тест | Исход на коде ДО правки |
|---|---|
| `test_key_with_trailing_newline_is_refused[page-create]` | `assert 302 == 400` |
| `test_key_with_trailing_newline_is_refused[page-update]` | `assert 302 == 400` |
| `test_key_with_trailing_newline_is_refused[api-create]` | `assert 201 == 400` |
| `test_key_with_trailing_newline_is_refused[api-update]` | `assert 200 == 400` |
| `test_key_with_leading_zero_prefix_is_refused[page-create]` | `assert 302 == 400` |
| `test_key_with_leading_zero_prefix_is_refused[page-update]` | `assert 302 == 400` |
| `test_key_with_leading_zero_prefix_is_refused[api-create]` | `assert 201 == 400` |
| `test_key_with_leading_zero_prefix_is_refused[api-update]` | `assert 200 == 400` |
| `test_oversized_upload_is_not_buffered_whole` | `assert None not in [None]` — единственный вызов чтения сделан БЕЗ аргумента размера |
| `test_multipart_file_part_in_images_is_refused` | `assert 500 == 400`, причина — `AttributeError: 'UploadFile' object has no attribute 'strip'` (`app/pages/ads.py:313`) |

Стражи, красной фазы не имеющие и за воспроизведение дефекта не выданные: `test_oversized_upload_is_refused_with_size_message` (1 passed на текущем коде), `test_own_key_is_accepted_on_every_entrance`, `test_status_field_keeps_its_wire_name`, `test_attachment_limit_is_a_closed_boundary`, `test_counter_threshold_follows_the_presence_of_attachments`. Ранее зелёные тесты модуля загрузок на красной фазе не тронуты: `-k "safe_filename or sniff_image or stays_inside_user_prefix or stores_sniffed"` — **20 passed**.

## Files Created/Modified

- **`app/services/image_keys.py` (новый)** — `_IMAGE_KEY_PATTERN` (без якорей, первый разряд префикса ненулевой), `INACCESSIBLE_IMAGE_MESSAGE` и `own_image_keys`. Комментарии, объясняющие, почему отказ оформлен исключением, а не молчаливым отбрасыванием, перенесены дословно. Модуль не импортирует ни страничный слой, ни маршруты.
- **`app/pages/ads.py`** — определения заменены импортом из нейтрального модуля (прежние имена остались доступными, четыре точки вызова не переписаны); `import re` удалён как ставший ненужным; отбор значений поля вложений проверяет тип и отказывает на нестроковом; параметр формы `status` переименован в `ad_status` с `alias="status"`.
- **`app/routes/ads.py`** — импорт правила из `app.services.image_keys`; комментарий называет причину направления зависимости.
- **`app/routes/uploads.py`** — `UPLOAD_CHUNK_SIZE`; потоковое чтение с накоплением и прерыванием на первом превышении; распознавание типа переехало НИЖЕ проверки размера, и комментарий объясняет, почему это неизбежно и что именно становится наблюдаемым.
- **`tests/test_pages/test_ads_image_ownership.py`** — `ENTRANCES`, хелпер `_write_images` (четыре входа записи `Ad.images` за одним интерфейсом) и три параметризованных теста.
- **`tests/test_routes/test_uploads.py`** — фикстуры `oversize_settings` и `recorded_reads`, хелпер `make_oversized_png_bytes`, три теста.
- **`tests/test_pages/test_ads_editor.py`** — `_counter_class`; четыре теста (один красный, три стража).

## Decisions Made

- **Снять якорь `$` — недостаточно; нужен и метод.** `re.match` сопоставляет с начала, но не требует конца, поэтому одна лишь смена образца оставила бы дыру. Взято и то, и другое: образец без якорей плюс `fullmatch`.
- **Две преграды одному `007/…`.** Префикс сравнивается со строкой И первый разряд образца ненулевой. Избыточность намеренная: инвариант звучит как «ключ — ровно то значение, которое загрузка выдала ЭТОМУ вызывающему», и обе преграды выражают его с разных сторон.
- **Порядок проверок в `upload_image` изменён.** При потоковом чтении предел неизбежно срабатывает раньше, чем содержимое целиком доступно для распознавания. Следствие наблюдаемо: тело, которое одновременно превышает предел и не является изображением, получает отказ по размеру, а не по типу. Оба отказа — 400, оба действующих утверждения распознавания подают тела в пределах лимита и продолжают проверять именно тип.
- **Файловая часть — отказ, а не отбрасывание.** Отбрасывание сохранило бы объявление БЕЗ вложений, то есть превратило бы кривой запрос в «успешное сохранение без картинки» — ровно та причина, по которой `own_image_keys` отказывает.
- **Тест на предел ресурса меряет потребление.** Иначе он зелен на дефектном коде: 400 возвращается и после того, как всё тело уже в памяти. Допуск — одна порция сверх предела: превышение обнаруживает ровно тот блок, который его создал, и размер этой порции берётся из самих записанных вызовов, а не из литерала.

## Deviations from Plan

### 1. [Rule 3 — Blocking] Красная фаза задачи 1 сперва падала по инфраструктурной причине

- **Найдено при:** Task 1, первый сужённый прогон
- **Проблема:** все восемь параметризаций падали с `sqlalchemy.exc.MissingGreenlet`, а не воспроизведением дефекта. Причина: хелпер `_write_images` обращался к `owner.id` ПОСЛЕ собственного `db_session.expire_all()`, и обращение уходило в ленивую подгрузку вне greenlet-а. Красная фаза, падающая по постороннему поводу, не отличает «мой тест воспроизвёл дефект» от «сломалось что-то другое» — тот же класс пустого гейта, который этот прогон и устраняет (тот же дефект встречался в плане 02-08).
- **Исправление:** идентификатор снимается в начале хелпера и дальше используется вместо живого ORM-объекта.
- **Файлы:** `tests/test_pages/test_ads_image_ownership.py`
- **Проверка:** повторный прогон дал `assert 302 == 400` / `201 == 400` / `200 == 400` — отказ по существу дефекта.
- **Committed in:** `2332b8d` (в составе коммита задачи 1)

### 2. [Rule 1 — Bug] Предпосылка плана о классе `UploadFile` оказалась ложной

- **Найдено при:** Task 2, полный прогон верификации задачи
- **Проблема:** план требовал подтвердить, что `fastapi.UploadFile` — тот же класс, что `starlette.datastructures.UploadFile`, и написанный на красной фазе страж это утверждал. В установленной версии (FastAPI 0.129.0) это НЕ так: `fastapi.UploadFile` — подкласс, и он переопределяет `read`, передавая размер в базовый метод ЯВНО. Страж падал.
- **Исправление:** применён предусмотренный самим планом запасной путь — оборачивается тот класс, который обработчик получает фактически. Обёртка остаётся на базовом классе (его метод в конечном счёте вызывают оба), а факт «в обработчик пришёл именно базовый» теперь ИЗМЕРЯЕТСЯ: обёртка записывает класс каждого вызова, и тест это утверждает. Без этого различие «вызов без аргумента» и «`read(-1)`» на подклассе исчезло бы, и измерение дефекта осталось бы зелёным при полностью забуференном теле. Страж переименован в `test_read_measurement_targets_the_class_the_handler_receives` и утверждает верное: отношение подкласса.
- **Файлы:** `tests/test_routes/test_uploads.py`
- **Проверка:** `test_oversized_upload_is_not_buffered_whole` записывает класс каждого чтения и утверждает `{StarletteUploadFile}`; на красной фазе тот же механизм дал `[None]`, то есть различие сохранялось.
- **Committed in:** `45c2c13`

### 3. [Rule 1 — Bug] Проверка порога счётчика была бы вакуумной по всей странице

- **Найдено при:** Task 3, первый прогон стражей
- **Проблема:** утверждение `"counter--warn" in html` зелено при ЛЮБОМ пороге: те же имена классов встречаются в узловой сборке счётчика, которая живёт в том же файле шаблона. Первый вариант теста упал на `"counter--over" not in html` — и упал бы он ровно потому, что мерил присутствие скрипта, а не выбор порога.
- **Исправление:** добавлен `_counter_class`, извлекающий значение `class` у САМОГО счётчика (атрибут стоит перед `id`, поэтому элемент отыскивается назад от якоря); все три утверждения порога переведены на него.
- **Файлы:** `tests/test_pages/test_ads_editor.py`
- **Проверка:** с вложениями класс счётчика несёт `counter--warn`, без вложений — не несёт, при одном и том же тексте в 1500 символов, лежащем между двумя порогами.
- **Committed in:** `de3ebba`

---

**Total deviations:** 3 auto-fixed (2 bug, 1 blocking)
**Impact on plan:** ни одна задача не пропущена и не расширена. Все три отклонения — про честность гейтов: два теста, написанные по букве плана, ничего бы не измеряли, и это обнаружено до того, как они были выданы за доказательство.

## Issues Encountered

- Требование ADS-05 в `.planning/REQUIREMENTS.md` НЕ отмечено выполненным намеренно: `requirements ready-ids` отвечает `0/1 requirement(s) ready` — тот же идентификатор объявляют планы 02-11 и 02-12, у которых SUMMARY ещё нет. Отметка появится, когда завершится последний из объявляющих его планов.
- Полный прогон суиты занимает ~9,5 минут (877 passed).

## Known Stubs

None. Сканирование изменённых файлов на `TODO`/`FIXME`/`placeholder`/`xfail`/`.skip(`/«coming soon» — 0 совпадений. Пропущенных тестов и невыполненных проверок план не оставил: все `<verify>` обеих задач и все `acceptance_criteria` прогнаны.

## Threat Flags

Новой поверхности сверх зарегистрированной в `<threat_model>` плана не появилось. Все пять зарегистрированных угроз закрыты и покрыты регрессией: T-02G-12 (форма ключа) — D1/D2, T-02G-13 (отказ в обслуживании через буферизацию тела, severity `high`) — D4, T-02G-14 (файловая часть в поле вложений) — D7, T-02G-15 (затенение имени) — D8, T-02G-16 (инверсия зависимости) — D6. T-02G-SC не применим: пакетов план не устанавливал, `pyproject.toml` и `uv.lock` не изменены.

Отдельно отмечено как НЕ закрытое здесь: тело загрузки по-прежнему полностью буферизуется разборщиком многочастного запроса Starlette (`SpooledTemporaryFile`, сброс на диск после 1 МБ) ДО того, как обработчик получает управление. План ограничивал потребление ПАМЯТИ ОБРАБОТЧИКОМ, и ровно это измерено; предел на уровне ASGI-разборщика — отдельная поверхность, в `files_modified` плана не входящая.

## User Setup Required

None — внешних сервисов, переменных окружения и миграций схемы этот план не затрагивает.

## Next Phase Readiness

- **Планы 02-11 и 02-12 разблокированы:** правило ключа вложения лежит в одном месте, и любой новый вход обязан взять его оттуда.
- **Изменение наблюдаемого поведения загрузки:** тело, которое одновременно превышает предел размера и не является изображением, теперь получает отказ по размеру, а не по типу. Оба ответа — 400; откат вернул бы буферизацию произвольного тела в памяти воркера.
- **Открыто для конца фазы:** ADS-05 ждёт завершения планов 02-11 и 02-12, объявляющих тот же идентификатор.
- **Блокеров нет.**

## Self-Check: PASSED

- Файлы на диске: `app/services/image_keys.py`, `app/pages/ads.py`, `app/routes/ads.py`, `app/routes/uploads.py`, `tests/test_pages/test_ads_image_ownership.py`, `tests/test_pages/test_ads_editor.py`, `tests/test_routes/test_uploads.py` — все найдены.
- Коммиты в истории ветки: `2332b8d`, `45c2c13`, `7425531`, `de3ebba` — все найдены.
- Удалений отслеживаемых файлов ни в одном коммите плана нет (`git diff --diff-filter=D 2332b8d~1..HEAD` пуст); неотслеживаемых файлов после прогона не осталось.
- Полная суита: **877 passed**, 0 failed.

---
*Phase: 02-obyavleniya-i-raspisaniya*
*Completed: 2026-08-11*
