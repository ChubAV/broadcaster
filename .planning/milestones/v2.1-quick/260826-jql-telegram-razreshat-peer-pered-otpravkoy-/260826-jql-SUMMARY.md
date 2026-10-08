---
phase: quick-260826-jql-telegram-resolve-peer
plan: 01
subsystem: messengers
tags: [telegram, telethon, peer-resolution, send, error-messages]

# Dependency graph
requires: []
provides:
  - "TelegramUserMessenger._resolve_peer — разрешение группы в сущность telethon с одним прогревом кэша диалогов"
  - "PEER_UNREACHABLE_MESSAGE — единый русский текст потери доступа к группе, уезжающий на экран истории отправок"
  - "PeerUnreachableError — тип, отличающий потерю доступа от прочих ValueError в теле отправки"
  - "Одиночная картинка уходит не списком, минуя альбомную ветку telethon и запрос messages.uploadMedia"
affects: [telegram, отправка объявлений, история отправок, синхронизация групп]

actuals:
  tokens: 9510
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Разрешение peer один раз за отправку, до ветвления по типу содержимого"
    - "Пользовательский текст ошибки — модульная константа, а не str(e); текст библиотеки остаётся в логе"

key-files:
  created: []
  modified:
    - app/messengers/telegram_user.py
    - tests/test_messengers/test_telegram_user.py

key-decisions:
  - "Peer разрешается ОДИН раз до ветвления на картинки/текст: разрешение внутри веток дало бы до трёх прогревов кэша на одну отправку"
  - "Прогрев кэша ограничен одним get_dialogs() и одной повторной попыткой — иначе навсегда потерянная группа, получающая отправку по расписанию, стала бы источником FloodWait на аккаунте"
  - "PeerUnreachableError заведён собственным типом вместо except ValueError: широкая ветка выдала бы негодный идентификатор группы за потерю доступа"
  - "Наружу уходит константа PEER_UNREACHABLE_MESSAGE, а не str(e): result[\"error\"] — надпись на экране истории отправок, а не строка лога"
  - "Одиночная картинка передаётся не списком — вторая независимая мера, убирающая messages.uploadMedia с пути самого частого случая"

patterns-established:
  - "Проверка адресата отправки через `is` с объектом подменённого get_input_entity: фикстура отдаёт AsyncMock, поэтому проверка «не число» была бы зелёной и на сломанном коде"
  - "Границы диапазонов закрепляются на самой границе (1 против 2), а не на дальнем значении (3)"

requirements-completed: [QUICK-TG-RESOLVE-PEER]

coverage:
  - id: D1
    description: "Во все три точки отправки (send_file, откат после ForbiddenError, текстовая ветка) уходит разрешённая сущность, а не голое число"
    requirement: QUICK-TG-RESOLVE-PEER
    verification:
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_send_file_receives_a_resolved_peer_not_a_bare_id"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_the_text_path_sends_to_a_resolved_peer"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_the_forbidden_media_fallback_also_uses_the_resolved_peer"
        status: pass
    human_judgment: false
  - id: D2
    description: "Холодный кэш сущностей прогревается ровно одним get_dialogs(), попыток разрешения ровно две"
    requirement: QUICK-TG-RESOLVE-PEER
    verification:
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_a_cold_entity_cache_is_warmed_exactly_once"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_a_peer_that_stays_unresolved_reads_as_a_lost_group"
        status: pass
    human_judgment: false
  - id: D3
    description: "PeerIdInvalidError и неразрешимый peer дают один ответ: ok=False, no_retry=True, error равен PEER_UNREACHABLE_MESSAGE без английского текста telethon"
    requirement: QUICK-TG-RESOLVE-PEER
    verification:
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_peer_id_invalid_is_not_reported_to_the_user_in_english"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_a_peer_that_stays_unresolved_reads_as_a_lost_group"
        status: pass
    human_judgment: false
  - id: D4
    description: "Одна картинка уходит одиночным файлом, две и три — списком соответствующей длины"
    requirement: QUICK-TG-RESOLVE-PEER
    verification:
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_send_message_with_image"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_two_images_still_go_as_an_album"
        status: pass
      - kind: unit
        ref: "tests/test_messengers/test_telegram_user.py#test_send_message_with_multiple_images"
        status: pass
    human_judgment: false
  - id: D5
    description: "В боевом окружении объявление с одной картинкой доходит до реальной Telegram-группы, а группа без доступа показывает в истории отправок русский текст"
    verification: []
    human_judgment: true
    rationale: "Дефект воспроизводится только против живого сервера Telegram: с AsyncMock-клиентом голое число проходит молча, а 400 PEER_ID_INVALID приходит от сервера, которого в тестах нет. Юнит-тесты закрепляют форму запроса, но не факт доставки."

# Metrics
duration: 8min
completed: 2026-08-26
status: complete
---

# Quick 260826-jql: разрешение peer перед отправкой в Telegram Summary

**Объявление с картинками больше не падает на `messages.uploadMedia`: peer разрешается через `get_input_entity` один раз за отправку с одним прогревом кэша диалогов, одиночная картинка уходит не списком, а недоступная группа сообщает о себе по-русски и без повторов.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-08-26T14:39:49Z
- **Completed:** 2026-08-26T14:47:57Z
- **Tasks:** 3 из 3
- **Files modified:** 2

## Accomplishments

- **Причина дефекта устранена в корне.** Клиент создаётся заново на каждую отправку, а `StringSession.save()` хранит только dc_id, адрес и `auth_key` — соответствий `id → access_hash` в строке сессии нет. Кэш сущностей у свежего клиента пуст, и telethon угадывал тип peer по знаку числа (`-100…` → `PeerChannel` с до-разрешением через `channels.getChannels(access_hash=0)`). Эту догадку сервер и отвергал. Теперь `_resolve_peer` разрешает группу явно, и разрешённая сущность уходит во все три точки отправки.
- **Потолок обращений к Telegram поставлен явно.** Прогрев холодного кэша стоит ровно один `get_dialogs()` и ровно одну повторную попытку. Без потолка навсегда потерянная группа, которой расписание шлёт отправку раз за разом, стала бы постоянным источником лишних запросов и приблизила бы FloodWait на аккаунте пользователя.
- **Английский текст telethon убран с экрана пользователя.** Оба исхода потери доступа — отказ сервера `PeerIdInvalidError` и неразрешимый peer после прогрева — возвращают одну константу `PEER_UNREACHABLE_MESSAGE` с `no_retry: True`. Диагностика осталась в `log.warning("send_peer_invalid", ...)`.
- **Вторая независимая мера: одиночная картинка не списком.** Список уводил telethon в альбомную ветку `_send_album`, где первым запросом идёт `messages.uploadMedia` — тот самый, что получал 400. Одиночный файл идёт через `messages.sendMedia` и `uploadMedia` не будит вовсе.
- **Тесты проверены на зубы мутацией.** Каждая из трёх точек отправки была по очереди возвращена к `int(group_id)`; каждый раз краснел ровно свой тест. Это тот самый разрыв связи, который в бою заметен не был бы: с `AsyncMock`-клиентом голое число проходит молча.

## Task Commits

1. **Задача 1 (tracer, TDD): разрешённый peer во всех трёх точках отправки** — `d45ffb5` (test, RED) → `f031c40` (feat, GREEN)
2. **Задача 2 (TDD): одна картинка уходит одиночным файлом** — `f57088e` (test, RED) → `7202ecd` (feat, GREEN)
3. **Задача 3: закрывающий прогон и сверка объявлений с кодом** — `731080c` (docs)

**Plan metadata:** оставлено оркестратору (docs-артефакты этим исполнителем не коммитятся).

## Files Created/Modified

- `app/messengers/telegram_user.py` — добавлены `PEER_UNREACHABLE_MESSAGE`, `PeerUnreachableError`, метод `TelegramUserMessenger._resolve_peer`; импорт `PeerIdInvalidError`; подстановка `peer` в три точки отправки; ветка `except (PeerIdInvalidError, PeerUnreachableError)` между веткой запретов и catch-all; вычисление `payload` для границы «одна картинка / альбом».
- `tests/test_messengers/test_telegram_user.py` — семь новых тестов и один переписанный; helper `_http_client_returning_image_bytes()`.

## Decisions Made

Все решения приняты планом и исполнены как написано; их перечень — в `key-decisions` frontmatter. Собственных решений исполнителя, меняющих замысел, не было.

Одно решение о форме, не оговорённое планом: вспомогательная функция `_http_client_returning_image_bytes()` заведена вместо третьего повторения шести строк настройки `httpx`-мока. Существующий `test_send_message_with_multiple_images` намеренно НЕ переведён на неё — задача 2 разрешала править только `test_send_message_with_image`, и трогать зелёный соседний тест ради единообразия значило бы выйти за границы плана.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Ссылка в комментарии указывала на строку, которой рядом нет**

- **Found during:** Задача 3 (закрывающая сверка объявлений с кодом)
- **Issue:** Комментарий над `PEER_UNREACHABLE_MESSAGE` ссылался на `app/application/scheduling/use_cases.py:483`, объясняя, что значение уезжает в `group.last_error`. Номер строки взят из текста плана. На деле по строке 483 стоит `if result.get("no_retry"):`, а присваивание `group.last_error = error` живёт строкой ниже, на 484.
- **Fix:** Ссылка исправлена на `use_cases.py:484`.
- **Files modified:** `app/messengers/telegram_user.py`
- **Verification:** `grep -n "group.last_error = error" app/application/scheduling/use_cases.py` → 484.
- **Committed in:** `731080c`

---

**Total deviations:** 1 auto-fixed (1× Rule 1).
**Impact on plan:** Нулевой для поведения — правка целиком в комментарии. Найдена ровно тем гейтом задачи 3, который и заведён под расхождение объявлений с кодом: ссылка на строку, которой рядом нет, — то же самое расхождение, что и неверное утверждение в докстринге.

## Issues Encountered

**RED-фаза задачи 1 упиралась в ошибку импорта, а не в поведение.** Тесты импортируют `PEER_UNREACHABLE_MESSAGE`, которого на исходном дереве ещё нет, поэтому прогон падал на сборе тестов целиком — красный сигнал был, но он ничего не говорил о самом дефекте. Чтобы RED был честным, в модуль временно (без коммита) добавлена одна строка с константой-заглушкой: прогон показал шесть падений именно на утверждениях `is` и на текстах отказа, то есть на реальном поведении. После этого заглушка снята, и красный зафиксирован коммитом `d45ffb5` в исходном виде.

**Проверка тестов на зубы.** `key_links` плана предупреждает, что разрыв связи в любой ОДНОЙ из трёх точек отправки возвращает исходный дефект незаметно. Поэтому после GREEN каждая точка по очереди возвращалась к `int(group_id)`: краснели `test_send_file_receives_a_resolved_peer_not_a_bare_id`, `test_the_forbidden_media_fallback_also_uses_the_resolved_peer` и (вместе с `test_a_cold_entity_cache_is_warmed_exactly_once`) `test_the_text_path_sends_to_a_resolved_peer` — по одному тесту на точку. Мутации откачены, коммитов не оставили.

**⚠️ Дефект инструментария GSD, не связанный с задачей, но требующий внимания.** Вызов `gsd-tools query state.record-session` на этом проекте портит `.planning/STATE.md`: он молча сносит из frontmatter весь блок `progress` (`total_phases`, `completed_phases`, `total_plans`, `completed_plans`, `percent`) и подменяет `current_phase_name: ""` прозаической фразой, выдернутой из тела документа, попутно переставляя ключи. Потеря `progress` не косметическая — на него смотрят команды, считающие готовность вехи, а тело того же STATE.md продолжает утверждать 7/7 фаз и 110/110 планов, то есть файл начинает противоречить сам себе.

Правка отката: изменение STATE.md, сделанное обработчиком, откачено (`git checkout -- .planning/STATE.md`), и поля сессии проставлены вручную — блок `progress`, `current_phase: null` и `current_phase_name: ""` при этом сохранены в исходном виде. Результат сверен парсером YAML. Оркестратору стоит знать, что автоматический вызов того же обработчика воспроизведёт порчу.

## Известные ограничения

**Стабов, заглушек и пропущенных тестов задача не оставила.** `grep` по правленым файлам на `TODO`, `FIXME`, `skip`, `placeholder` — пусто.

**Один невыполнимый здесь гейт — боевая проверка (`<human-check>` задачи 3).** Юнит-тесты закрепляют ФОРМУ запроса, но не факт доставки: 400 PEER_ID_INVALID приходит от живого сервера Telegram, которого в тестах нет, а `AsyncMock`-клиент принимает и голое число молча. Проверить в бою нужно две вещи:

1. Объявление с ОДНОЙ картинкой уходит в реальную Telegram-группу.
2. Объявление в группу, из которой аккаунт удалён, оставляет в истории отправок русский текст про потерю доступа, а не английскую строку telethon.

Пункт записан как `D5` с `human_judgment: true` в блоке `coverage`.

## Проверка границ

- Дифф от коммита плана (`e953f2c`) по путям `app tests alembic pyproject.toml uv.lock` — ровно два файла плана и ни одного сверх них.
- `get_groups`, `get_group_details`, `check_connection` и блок QR-авторизации не тронуты.
- `app/application/scheduling/use_cases.py` и `app/services/schedule_rules.py` не изменены ни байтом.
- Автопересинхронизация и автодеактивация группы НЕ введены: `grep` по адаптеру на `sync_groups`, `is_active`, `missing_since`, `session.commit` даёт единственное попадание — упоминание `group.last_error` в комментарии.
- Миграций нет, зависимостей не добавлено.

## Проверка объявлений (задача 3)

Три утверждения, которые легко пережили бы правку и стали неверными, сверены с кодом, причём на уровне AST, а не подстрок (комментарии в файле упоминают `get_dialogs` трижды, и `grep` их не различает):

| Утверждение | Чем сверено | Итог |
|---|---|---|
| «прогрев ровно один раз» | AST-обход `_resolve_peer`: `get_dialogs` — 1 вызов, `get_input_entity` — 2 | верно |
| «во все три точки уходит peer» | перечисление точек отправки: `send_file(peer, …)`, откат `send_message(peer, …)`, текстовая `send_message(peer, …)`; единственный `int(group_id)` остался в `_resolve_peer` | верно |
| «uploadMedia не вызывается при одной картинке» | `payload = files[0] if len(files) == 1 else files` | верно |

Проверены и оба внешних утверждения о telethon 1.42.0, на которых стоит вся правка: `_send_album` действительно вызывает `messages.UploadMediaRequest` первым запросом (`telethon/client/uploads.py:540`), а `PeerIdInvalidError` действительно наследует `BadRequestError` (400), а не `ForbiddenError` (403) — то есть пересечения с веткой запретов нет и порядок веток безразличен.

## Verification Results

| Гейт | Результат |
|---|---|
| `uv run pytest tests/test_messengers/ tests/test_services/test_messenger_factory.py tests/test_routes/test_sync_groups.py -q` | **95 passed** (базовая линия до правки — 88) |
| `uv run pytest tests/test_messengers/test_telegram_user.py -q` | 23 passed (16 существующих + 7 новых) |
| Сбор шести регрессий задачи 1 | ровно 6 |
| Сбор трёх тестов границы картинок | ровно 3 |
| Публичные символы (`PEER_UNREACHABLE_MESSAGE`, `PeerUnreachableError`, `_resolve_peer`) | на месте |
| Дифф от коммита плана по `app tests alembic pyproject.toml uv.lock` | ровно два файла плана |
| `uv run python -m compileall -q app main.py tests` | без ошибок |
| `graphify update .` | отработал (12439 узлов, 23828 рёбер) |
| `<human-check>` боевой отправки | **не выполнен** — требует живого Telegram, см. `D5` |

## TDD Gate Compliance

Обе TDD-задачи прошли последовательность гейтов полностью, и это видно в истории:

- Задача 1: `d45ffb5` (**test**, RED) → `f031c40` (**feat**, GREEN). Фаза REFACTOR не понадобилась.
- Задача 2: `f57088e` (**test**, RED) → `7202ecd` (**feat**, GREEN). Фаза REFACTOR не понадобилась.

Ни один тест не проходил неожиданно на фазе RED: все шесть тестов задачи 1 и переписанный `test_send_message_with_image` краснели до правки кода. `test_two_images_still_go_as_an_album` зелёный с самого начала намеренно — это регрессионный сторож границы, а не тест новой функциональности; он держит поведение, которое обязано было пережить правку.

## Threat Flags

Новых поверхностей безопасности вне реестра `<threat_model>` не появилось. Правка не добавляет ни сетевых точек входа, ни путей авторизации, ни обращений к файловой системе, ни изменений схемы. Три митигации реестра реализованы и закреплены тестами: T-jql-01 (константа вместо `str(e)`), T-jql-02 (потолок прогрева), T-jql-03 (`no_retry` на обеих ветках потери доступа).

## Next Phase Readiness

Правка готова к выкату вместе с остальным кодом. Отдельных миграций и настроек она не требует.

⚠️ Два замечания к выкату:

1. **Боевая проверка (`D5`) не выполнена и должна пройти после выката.** До неё утверждение «объявления с картинками снова уходят» подтверждено только формой запроса, но не доставкой.
2. **Наследуется прежний блокер репозитория:** очередь ревизий Alembic `0013`…`0020` не выкачена на боевую базу (D-26, см. `STATE.md`). Эта задача миграций не добавляет, но выкат кода и выкат очереди неотделимы.

Отдельно стоит отметить, что текст `PEER_UNREACHABLE_MESSAGE` советует пользователю пересинхронизировать группы аккаунта — то есть предполагает, что кнопка синхронизации ему доступна и работает. Автоматическая пересинхронизация по этой ошибке намеренно НЕ введена (граница задачи); если в будущем захочется её завести, естественное место — потребитель ответа в `app/application/scheduling/use_cases.py`, а не адаптер.

## Self-Check: PASSED

Утверждения этого файла сверены с диском, а не приняты на веру:

- Файлы на месте: `app/messengers/telegram_user.py`, `tests/test_messengers/test_telegram_user.py`, сам SUMMARY.
- Все пять коммитов существуют в истории: `d45ffb5`, `f031c40`, `f57088e`, `7202ecd`, `731080c` — и стоят ровно в том порядке test → feat → test → feat → docs, который заявлен в разделе TDD Gate Compliance.
- Удалённых файлов в диффе от коммита плана нет (`git diff --diff-filter=D` пуст) — правка ничего не снесла попутно.
- Неотслеживаемых артефактов правка не оставила: единственный `??` в `git status` — этот SUMMARY, который коммитит оркестратор. `graphify-out/` в `.gitignore`.

---
*Quick task: 260826-jql-telegram-razreshat-peer-pered-otpravkoy*
*Completed: 2026-08-26*
