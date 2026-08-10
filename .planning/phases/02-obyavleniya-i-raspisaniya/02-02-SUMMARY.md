---
phase: 02-obyavleniya-i-raspisaniya
plan: 02
subsystem: security
tags: [fastapi, sqlalchemy, uploads, idor, content-sniffing, ownership]

requires:
  - phase: 02-obyavleniya-i-raspisaniya
    plan: 01
    provides: Зелёная базовая линия 662 passed — регрессию этого плана можно отличить от унаследованной
provides:
  - Определение типа загружаемого изображения по содержимому (`sniff_image`) — CR-02 закрыт
  - Проверка владения ключом вложения на всех четырёх входах записи (`own_image_keys`) — WR-01/T-10-04 закрыт
  - Серверный лимит числа вложений из `settings.max_images_per_ad` — D-13 исполнен
  - Проверка владения `ad_id` и `account_id` на обоих входах постановки расписания — CR-01/D-20 закрыт
  - Регрессионные тесты на каждую из трёх находок Фазы 1
affects: [02-04, 02-05, 02-06, 02-07]

actuals:
  tokens: 14600
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "Тип файла определяется по сигнатуре содержимого, клиентский заголовок не используется нигде, включая запись в хранилище"
    - "Правило доверия к клиентским данным живёт в одной функции и переиспользуется всеми входами записи"
    - "Владение проверяется запросом со связкой по `user_id`, а не выборкой строки с последующим сравнением"

key-files:
  created:
    - tests/test_pages/test_ads_image_ownership.py
    - tests/test_pages/test_schedule_ownership.py
  modified:
    - app/routes/uploads.py
    - app/pages/ads.py
    - app/routes/ads.py
    - app/pages/schedules.py
    - app/routes/schedules.py
    - tests/test_routes/test_uploads.py
    - tests/test_routes/test_ads.py
    - tests/test_routes/test_schedules.py

key-decisions:
  - "`sniff_image` написан руками без библиотеки: `python-magic` тянет `libmagic`, `imghdr` удалён в Python 3.13, `Pillow` доступна лишь транзитивно и добавила бы decompression bomb чинимому эндпоинту"
  - "В хранилище пишется распознанный тип, а не присланный клиентом: иначе объект отдавался бы браузеру с подконтрольным отправителю `Content-Type` и вектор CR-02 пережил бы проверку на входе"
  - "`own_image_keys` отказывает, а не отбрасывает значение молча: отбрасывание превратило бы подмену в «успешное сохранение без картинки»"
  - "Страничный слой отвечает на отказ по вложению `HTTPException(400)`, а не редиректом — редирект означал бы потерю данных без объяснения"
  - "Страничный слой отвечает на отказ по владению расписанием редиректом — там отказ означает «такой записи для вас нет», то есть навигацию, а не ошибку в данных"
  - "`exclude_unset` сохранён на JSON-обновлении объявления: отсутствие `images` не обнуляет вложения"
  - "Разовая чистка уже сохранённых чужих и внешних значений в `Ad.images` не делается — правка данных вне границы фазы (T-02-10)"

patterns-established:
  - "Определение типа загружаемого файла: таблица сигнатур модульной константой плюс маленькая чистая функция; клиентский заголовок не участвует ни в проверке, ни в записи"
  - "Единый источник правила доверия: функция валидации живёт в одном модуле и импортируется всеми слоями, чтобы страничный и JSON-вход не разъехались"
  - "Проверка владения запросом `select(Model.id).where(Model.id == x, Model.user_id == uid)`: «нет строки» и «строка чужая» дают один исход, ветку невозможно забыть"

requirements-completed: []

coverage:
  - id: D1
    description: "Тип загружаемого изображения определяется по содержимому; SVG под видом PNG отклоняется (CR-02, T-02-07)"
    verification:
      - kind: unit
        ref: "tests/test_routes/test_uploads.py#test_sniff_image_recognises_supported_formats (5 параметров)"
        status: pass
      - kind: unit
        ref: "tests/test_routes/test_uploads.py#test_sniff_image_rejects_non_images (8 параметров)"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_uploads.py#test_upload_rejects_svg_declared_as_png"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_uploads.py#test_upload_stores_sniffed_content_type_not_client_header"
        status: pass
      - kind: other
        ref: "grep -c 'file.content_type' app/routes/uploads.py → 0"
        status: pass
    human_judgment: false
  - id: D2
    description: "Форма ключа объекта хранилища не изменена"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_uploads.py#test_upload_key_stays_inside_user_prefix"
        status: pass
    human_judgment: false
  - id: D3
    description: "Владение ключом вложения проверяется на всех четырёх входах записи (WR-01/T-10-04, T-02-08)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_ads_create_rejects_key_outside_owner_prefix (6 параметров)"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_ads_update_rejects_foreign_key_and_leaves_ad_untouched"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_ads.py#test_create_ad_rejects_key_outside_owner_prefix (4 параметра)"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_ads.py#test_update_ad_rejects_foreign_key_and_leaves_ad_untouched"
        status: pass
    human_judgment: false
  - id: D4
    description: "Лимит числа вложений — серверное правило, порог из настройки (D-13, T-02-09)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_ads_create_rejects_more_attachments_than_limit"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_ads_create_accepts_exactly_the_limit"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_ads_image_ownership.py#test_limit_comes_from_settings_not_a_literal"
        status: pass
      - kind: other
        ref: "grep -nE '(>|<|=)\\s*10\\b' app/pages/ads.py → пусто"
        status: pass
    human_judgment: false
  - id: D5
    description: "Владение `ad_id` и `account_id` проверяется на страничном входе постановки расписания (CR-01, T-02-05)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_page_create_rejects_foreign_ad"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_page_create_rejects_foreign_account"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_page_update_rejects_swapping_in_foreign_ad"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_page_update_rejects_swapping_in_foreign_account"
        status: pass
    human_judgment: false
  - id: D6
    description: "Владение аккаунтом проверяется на JSON-входе постановки расписания (CR-01/D-20, T-02-06)"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_schedules.py#test_create_schedule_rejects_foreign_account"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_schedules.py#test_create_schedule_rejects_nonexistent_account"
        status: pass
    human_judgment: false
  - id: D7
    description: "Состав маршрутов JSON-API не изменён (D-15)"
    verification:
      - kind: other
        ref: "grep -c '@router\\.' app/routes/schedules.py → 5, столько же в базовом коммите 54be649"
        status: pass
    human_judgment: false
  - id: D8
    description: "Полная суита зелёная; новых зависимостей нет"
    verification:
      - kind: unit
        ref: "uv run pytest tests/ -q → 712 passed"
        status: pass
      - kind: other
        ref: "git diff --stat pyproject.toml uv.lock → пусто"
        status: pass
    human_judgment: false

duration: 34min
completed: 2026-08-10
status: complete
---

# Phase 2 Plan 02: Долги безопасности Фазы 1 Summary

**Три находки Фазы 1 закрыты одной сменой правила: клиентским данным на входе больше не верят — тип файла берётся из первых байтов, а `ad_id`, `account_id` и ключ вложения проверяются на владение запросом; суита выросла с 662 до 712 тестов.**

## Performance

- **Duration:** ~34 min
- **Started:** 2026-08-10T08:30:00Z
- **Completed:** 2026-08-10T09:04:06Z
- **Tasks:** 3 (все по циклу RED → GREEN)
- **Files modified:** 10 (2 создано, 8 изменено)

## Accomplishments

- **Гейт код-ревью Фазы 1 закрыт.** CR-01, CR-02 и WR-01/T-10-04 более не воспроизводятся, и каждая закрыта регрессионным тестом, а не разовой проверкой. `security_block_on: high` этой фазой больше не держится.
- **Все пять диспозиций `mitigate` из `<threat_model>` исполнены** — T-02-05, T-02-06 (Задача 3), T-02-07 (Задача 1), T-02-08, T-02-09 (Задача 2).
- **Вектор CR-02 закрыт на обоих концах, а не только на входе.** План требовал определять тип по содержимому; проверка показала, что этого мало: распознанный тип должен ещё и записываться в хранилище, иначе объект отдаётся браузеру с `Content-Type`, присланным отправителем, и SVG исполняется на origin хранилища уже на выдаче. Заголовок клиента теперь не используется в файле нигде (`grep` даёт 0).
- **Тест, фиксировавший уязвимость как поведение, переписан.** `test_update_ad_with_multiple_image_fields` утверждал, что ключ вне префикса владельца сохраняется. Теперь позитивный путь использует корректные ключи, а отказ закреплён отдельными тестами.
- **Суита 662 → 712 passed** (+50 тестов), полный прогон зелёный.

## Task Commits

1. **Задача 1 (RED): падающие тесты определения типа по содержимому** — `1c764ca` (test)
2. **Задача 1 (GREEN): `sniff_image` и перевод обработчика на содержимое** — `658a17b` (feat)
3. **Задача 2 (RED): падающие тесты владения ключом и лимита** — `e1e0dd0` (test)
4. **Задача 2 (GREEN): `own_image_keys` на четырёх входах** — `32c7ffc` (feat)
5. **Задача 3 (RED): падающие тесты владения `ad_id`/`account_id`** — `324dde5` (test)
6. **Задача 3 (GREEN): `_owns_ad_and_account` и проверка аккаунта на JSON-входе** — `27237b1` (feat)

REFACTOR-коммитов нет: после GREEN чистить было нечего ни в одной задаче.

## Files Created/Modified

**Создано:**
- `tests/test_pages/test_ads_image_ownership.py` — 13 тестов: шесть классов враждебного значения ключа (чужой префикс, внешний URL по http и https, traversal, ключ без префикса, неверный токен), отказ на обновлении без частичного изменения записи, лимит вложений сверху и на границе, чтение порога из настройки.
- `tests/test_pages/test_schedule_ownership.py` — 7 тестов перекрёстной изоляции: чужие `ad_id` и `account_id` на создании и на обновлении, плюс позитивные пути.

**Изменено:**
- `app/routes/uploads.py` — таблица сигнатур `_IMAGE_SIGNATURES`, чистая функция `sniff_image`, константа текста отказа; чтение содержимого поднято выше проверки типа; `content_type` для S3 берётся из результата распознавания.
- `app/pages/ads.py` — регулярка формы ключа `_IMAGE_KEY_PATTERN`, функция `own_image_keys`, подключённая в `ads_create` и `ads_update` до первой записи в модель.
- `app/routes/ads.py` — импорт `own_image_keys`, зависимость `Settings`, подключение в `create_ad` и `update_ad` с сохранением семантики `exclude_unset`.
- `app/pages/schedules.py` — асинхронный помощник `_owns_ad_and_account`, вызываемый в `schedules_create` и `schedules_update`.
- `app/routes/schedules.py` — проверка владения аккаунтом по форме уже стоявшей проверки объявления, 404 на чужой и на несуществующий.
- `tests/test_routes/test_uploads.py` — генераторы байтов JPEG/GIF/WebP, константа SVG, 18 новых тестов.
- `tests/test_routes/test_ads.py` — помощник `image_key`, фикстура `auth_user_id`, переписанный тест приёма чужого ключа, 5 новых тестов владения и лимита на JSON-входе.
- `tests/test_routes/test_schedules.py` — 2 теста владения аккаунтом на JSON-входе.

## Decisions Made

- **Библиотека распознавания типа не вводится.** Обоснование записано комментарием рядом с таблицей сигнатур: `python-magic` тянет системный `libmagic` в Docker-образ, `imghdr` удалён из stdlib в Python 3.13, `Pillow` присутствует лишь транзитивно через `qrcode[pil]`, а `Image.open()` на недоверенном файле добавил бы вектор decompression bomb ровно тому эндпоинту, который чинится. Новых зависимостей: ноль.
- **Слои отвечают на отказ по-разному, и это не непоследовательность.** Отказ по вложению — ошибка в данных: пользователь что-то ввёл, и это что-то не принято, поэтому `HTTPException(400)` на обоих слоях, иначе редирект отправил бы его на список без объяснения, почему правка исчезла. Отказ по владению расписанием — «такой записи для вас нет», то есть навигация, и страничный слой отвечает редиректом, как уже отвечает на чужое расписание строкой выше. Оба решения записаны комментариями «почему» в коде.
- **`own_image_keys` живёт в `app/pages/ads.py` и импортируется в `app/routes/ads.py`.** Направление импорта задано планом. Смысл — единственный источник правила: разъехавшись, слои оставили бы JSON-вход открытым для ровно той находки, что закрыта на форме.
- **Проверка владения — запросом, а не сравнением после выборки.** Тогда «строки нет» и «строка чужая» дают один исход, и ветку невозможно забыть. Форма скопирована с проверки групп, которая уже стояла в том же файле.
- **`account_id is None` пропускается без проверки** — отвязанное расписание после удаления аккаунта (`ON DELETE SET NULL`, issue #35) остаётся законным состоянием. На сегодняшних входах значение всегда непустое (`account_id: int = Form(...)` и `int` в схеме), но проверка написана так, чтобы переход к необязательному аккаунту в планах 02-05/02-06 не открыл дыру молча.
- **`requirements-completed` оставлен пустым.** Frontmatter плана объявляет `requirements: [ADS-05, ADS-07]`, но этот план не даёт ни прикрепления и удаления вложений в интерфейсе, ни настройки расписаний в редакторе — он лишь укрепляет пути записи. Владельцы — планы 02-04 и 02-05. `REQUIREMENTS.md` не изменялся.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Распознанный тип записывается в хранилище**

- **Found during:** Задача 1
- **Issue:** План требовал заменить проверку, опирающуюся на клиентский заголовок, и не упоминал строку 74, где тот же заголовок передавался в `upload_file_to_s3` как `content_type`. Проверка на входе отсекла бы SVG, но любой принятый файл лёг бы в S3 с `Content-Type`, выбранным отправителем, и отдавался бы браузеру с ним же — вектор CR-02 пережил бы фикс на выдаче. Критерий приёмки плана (`grep -c 'file.content_type'` → `0`) буквально этого и требует, то есть намерение плана шире его текста.
- **Fix:** `content_type=file.content_type` → `content_type=content_type` (результат `sniff_image`), с комментарием «почему».
- **Files modified:** `app/routes/uploads.py`
- **Verification:** `test_upload_stores_sniffed_content_type_not_client_header` — PNG, присланный с заголовком `image/svg+xml`, уходит в хранилище как `image/png`.
- **Committed in:** `658a17b`

---

**2. [Rule 3 - Blocking] Существующие тесты, использовавшие ключи не той формы, приведены к реальной форме ключа**

- **Found during:** Задача 2
- **Issue:** Помимо теста, названного планом, ключи произвольной формы (`img1.jpg`, `1/img1.jpg`, `old.jpg`) использовали ещё три теста в `tests/test_routes/test_ads.py`. После введения правила формы они падали бы кодом 400 — не из-за регрессии, а потому что их фикстуры никогда не соответствовали тому, что выдаёт `/api/uploads/image`.
- **Fix:** Введён помощник `image_key(user_id, name)`, строящий ключ ровно по форме из `app/routes/uploads.py`, и фикстура `auth_user_id`, читающая идентификатор владельца из БД вместо предположения о том, что он равен единице. Все фикстуры ключей переведены на них.
- **Files modified:** `tests/test_routes/test_ads.py`
- **Verification:** 36 passed на `test_ads_image_ownership.py`, `test_ads.py`, `test_ads_editor.py`.
- **Committed in:** `e1e0dd0`

---

**Total deviations:** 2 auto-fixed (1 missing critical functionality, 1 blocking)
**Impact on plan:** Обе правки в границах файлов, объявленных планом. Расширения объёма нет.

## Issues Encountered

- **Формулировка критерия приёмки Задачи 3 по `MessengerAccount.user_id` («не меньше 2 — создание и обновление») буквально предполагала дублирование проверки в двух обработчиках.** Проверка вынесена в общий помощник `_owns_ad_and_account`, поэтому `MessengerAccount.user_id` встречается в файле 3 раза, а не 2 — критерий выполнен и численно, и по намерению (оба обработчика покрыты), но покрытие обеспечено переиспользованием, а не копией. Дублировать запрос ради буквы критерия было бы вторым источником истины для правила владения.
- **`PATCH /api/ads/{id}` в природе не существует.** План говорит о «JSON-API create/update (`PATCH`/`PUT`)»; в `app/routes/ads.py` объявлен только `PUT`. Состав маршрутов не менялся (D-15), проверка подключена к существующему `PUT`.
- **`db_session.expire_all()` в тестах ломал доступ к `ad.id` после запроса.** Обращение к атрибуту истёкшего объекта запускает ленивую подгрузку в синхронном контексте и падает с `MissingGreenlet`. Идентификаторы захватываются в локальные переменные до истечения — это ограничение тестового стенда, а не продового кода.

## Known Stubs

Отсутствуют. Заглушек, TODO/FIXME, пропущенных тестов и неисполненных `<verify>` в изменённых файлах нет — сканирование `app/routes/uploads.py`, `app/pages/ads.py`, `app/routes/ads.py`, `app/pages/schedules.py`, `app/routes/schedules.py` и обоих новых тестовых файлов чисто.

## Остаточный риск и задел для бэклога (T-02-10)

Фикс WR-01 действует **только на записи**. Значения, сохранённые в `Ad.images` до него — чужие ключи и внешние URL, — остаются в БД и продолжают рендериться в карточках, истории и админке (`01-REVIEW.md:311-315`). Разовая чистка сознательно вынесена за границу фазы: это правка данных, а не интерфейса, и она требует отдельного решения.

Диагностический запрос для бэклога:

```sql
SELECT id FROM ads WHERE images::text LIKE '%http%';
```

Для полноты картины стоит также искать префиксы, не совпадающие с `user_id` владельца объявления, — внешним URL спектр не исчерпывается. Наличие таких строк в проде на момент фикса неизвестно (`02-RESEARCH.md` §Open Questions Q4).

## Threat Flags

Новой security-релевантной поверхности не появилось: план не добавляет ни маршрутов, ни путей аутентификации, ни доступа к файлам, ни изменений схемы. Состав маршрутов `app/routes/schedules.py` проверен против базового коммита — 5 и 5.

Диспозиции `<threat_model>`: T-02-05, T-02-06, T-02-07, T-02-08, T-02-09 — закрыты; T-02-10 — `accept`, зафиксирован разделом выше; T-02-SC — `accept`, пакеты не устанавливались.

## TDD Gate Compliance

Все три задачи исполнены по циклу RED → GREEN, гейты видны в git log парами `test(...)` → `feat(...)`.

- **Задача 1.** RED `1c764ca`: сбор модуля падал с `ImportError: cannot import name 'sniff_image'` — назначенная причина. GREEN `658a17b`: 31 passed.
- **Задача 2.** RED `e1e0dd0`: 18 failed, 13 passed — падали ровно утверждения владения и лимита, позитивные пути были зелёными уже в RED. GREEN `32c7ffc`: 36 passed.
- **Задача 3.** RED `324dde5`: 6 failed, 11 passed — падали ровно шесть утверждений владения. GREEN `27237b1`: 28 passed.

REFACTOR ни в одной задаче не потребовался, коммитов этого вида нет.

Правило fail-fast соблюдено: в каждом RED-прогоне проверялось, что тест падает по назначенной причине, а не по ошибке в самом тесте. Один случай был исправлен именно поэтому — `test_ads_update_accepts_own_keys` падал с `MissingGreenlet` вместо ожидаемого прохождения, и причина оказалась в тесте, а не в коде.

## User Setup Required

None — внешние сервисы не настраиваются, пакеты не устанавливались, миграций нет.

## Next Phase Readiness

- **Планы 02-04 и 02-05 переписывают ровно эти обработчики.** Правила доверия к клиентским данным теперь живут в двух функциях с тестами: `own_image_keys` (`app/pages/ads.py`) и `_owns_ad_and_account` (`app/pages/schedules.py`). При переделке экранов их надо **вызывать**, а не переписывать; регрессионные тесты покраснеют, если вызов потеряется.
- **Лимит вложений в интерфейсе обязан читаться из `settings.max_images_per_ad`.** Второго источника истины для десятки заводить нельзя — сервер уже отказывает по этому порогу, и расхождение с браузером даст отказ там, где интерфейс обещал успех.
- **При переходе к необязательному аккаунту расписания** (02-05/02-06) `_owns_ad_and_account` уже пропускает `None`, но входные схемы (`account_id: int`) придётся ослаблять осознанно.
- **Сетка SC-3 зелёная** — путь создания расписания жив.
- **ADS-05 и ADS-07 не закрыты** этим планом и в `REQUIREMENTS.md` не отмечены.

## Self-Check: PASSED

- `app/routes/uploads.py` — FOUND, содержит `def sniff_image`; `grep -c 'file.content_type'` → 0
- `app/pages/ads.py` — FOUND, содержит `def own_image_keys`; `max_images_per_ad` → 2 вхождения; захардкоженной десятки нет
- `app/routes/ads.py` — FOUND, `own_image_keys` → 3 вхождения
- `app/pages/schedules.py` — FOUND, `MessengerAccount.user_id` → 3, `Ad.user_id` → 9
- `app/routes/schedules.py` — FOUND, `@router.` → 5 (столько же в базовом коммите)
- `tests/test_pages/test_ads_image_ownership.py` — FOUND
- `tests/test_pages/test_schedule_ownership.py` — FOUND
- Коммит `1c764ca` — FOUND
- Коммит `658a17b` — FOUND
- Коммит `e1e0dd0` — FOUND
- Коммит `32c7ffc` — FOUND
- Коммит `324dde5` — FOUND
- Коммит `27237b1` — FOUND
- `uv run pytest tests/ -q` → 712 passed
- `git diff --stat pyproject.toml uv.lock` → пусто

---
*Phase: 02-obyavleniya-i-raspisaniya*
*Completed: 2026-08-10*
