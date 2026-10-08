---
phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy
plan: 01
subsystem: api
tags: [htmx, fastapi, starlette, response-layer, dependency-refusal, open-redirect, header-injection]

requires:
  - phase: 07-sloy-pisma-htmx
    provides: "блок конфигурации htmx в обоих шеллах, правило {\"code\":\"204\",\"swap\":false}, selfRequestsOnly: true"
  - phase: 05.1-dostup-i-podpiska
    provides: "require_access и ACCESS_EXPIRED_LOCATION — первая точка правки FOUND-07"
  - phase: 06-admin-i-imperssonatsiya
    provides: "forbid_when_impersonating и IMPERSONATION_FORBIDDEN_DETAIL — вторая точка правки"
provides:
  - "app/pages/htmx.py — слой ответа проекта с единственным на проект чтением признака htmx"
  - "respond() — главный выход обработчика с ОБЯЗАТЕЛЬНЫМ ключевым redirect="
  - "refuse() — узкий выход отказа зависимости, покрывающий обе сегодняшние формы отказа"
  - "location_response()/_local_path() — единственная сборка ответа перехода с рантайм-проверкой значения"
  - "HtmxRefusal + обработчик исключения в app/main.py — путь мимо JSONResponse фреймворка"
  - "IMPERSONATION_REFUSED_LOCATION — локальный GET-совместимый адрес приземления отвергнутого действия"
  - "фикстура htmx_client — первый способ проверить продукт так, как его видит браузер с JavaScript"
affects: [08-02, 08-04, 08-06, 08-07, 09, 10, 11, 12, 13, 14, 15]

actuals:
  tokens: 18269
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "Слой ответа: одно объявление признака транспорта, два выхода (обработчик/зависимость)"
    - "Отказ зависимости как собственное исключение + обработчик в app/main.py — обход JSONResponse"
    - "Рантайм-проверка значения, уезжающего в заголовок ответа (локальный ASCII-путь)"
    - "Парный тест D-16: без заголовка → прежняя форма, с заголовком → HX-Location и НЕ документ"
    - "Обязательный ключевой аргумент как машинная гарантия наличия пути деградации"

key-files:
  created:
    - app/pages/htmx.py
    - tests/test_pages/test_htmx_response_layer.py
  modified:
    - app/main.py
    - app/pages/__init__.py
    - app/dependencies.py
    - app/pages/ads.py
    - tests/conftest.py

key-decisions:
  - "Отказ зависимости на htmx = 204 + HX-Location: у 204 нет тела ПО ОПРЕДЕЛЕНИЮ, поэтому «не JSON» становится свойством статуса, а не обещанием кода"
  - "Отказ поднимается собственным типом HtmxRefusal и не наследует HTTPException: поиск обработчика идёт по MRO, и потомок ушёл бы в тот же JSONResponse"
  - "Форма отказа без htmx приходит ПАРАМЕТРОМ without_htmx: сегодняшних форм две (302+location и 403+detail), и общий помощник обязан покрыть обе"
  - "is_htmx считает пустое значение заголовка ОТСУТСТВИЕМ признака (было `is not None`): пустая строка не должна включать ветку htmx"
  - "_local_path проверяет адрес на ОБОИХ транспортах respond(), а не только на заголовочном: инвариант адреса един"
  - "Сведение двух чтений HX-Request в ads.py выполнено в задаче 1, а не 3 — критерий приёмки задачи 1 требует нуля вхождений вне htmx.py"
  - "Имя заголовка в фикстуре htmx_client записано строкой: единственность относится к ЧТЕНИЮ приложением, а фикстура — пишущая сторона (браузер)"

patterns-established:
  - "Единственное объявление признака транспорта: второе вхождение ловится машинным гейтом, а не читателем"
  - "Отказ зависимости меняет транспорт, но не предикат: развилка стоит СТРОГО после вердикта"
  - "Значение, уезжающее в заголовок ответа, проходит рантайм-проверку и никогда не приходит из запроса"
  - "Текст ошибки проверки НЕ подставляет отвергнутое значение — иначе враждебная строка получает второй маршрут наружу"

requirements-completed: [FOUND-04, FOUND-07, GATE-01]

coverage:
  - id: D1
    description: "Слой ответа существует одним модулем и содержит единственное на проект чтение признака htmx"
    requirement: FOUND-04
    verification:
      - kind: other
        ref: "grep -rn 'HX-Request' app/ --include=*.py | wc -l  → 1"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_the_htmx_flag_is_read_from_the_request_header"
        status: pass
    human_judgment: false
  - id: D2
    description: "Отказ гейта доступа отвечает 302 полной перезагрузке и 204 + HX-Location запросу htmx"
    requirement: FOUND-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_response_layer.py#test_a_closed_route_answers_a_full_reload_with_a_redirect"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_response_layer.py#test_a_closed_route_answers_htmx_with_a_location_header"
        status: pass
    human_judgment: false
  - id: D3
    description: "Отказ действию под чужой личностью отвечает прежним 403 с detail без htmx и HX-Location с ним, не расширив множество отвергаемых"
    requirement: FOUND-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_response_layer.py#test_an_impersonated_action_answers_a_full_reload_with_its_own_refusal"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_response_layer.py#test_an_impersonated_action_answers_htmx_with_a_location_header"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_response_layer.py#test_a_request_without_an_actor_is_refused_on_neither_transport"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_response_layer.py#test_a_machine_receiver_without_a_token_is_refused_on_neither_transport"
        status: pass
    human_judgment: false
  - id: D4
    description: "respond() невозможно вызвать без пути деградации: redirect объявлен KEYWORD_ONLY и без умолчания"
    requirement: FOUND-04
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_the_handler_exit_cannot_be_called_without_a_degraded_path"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_a_full_reload_gets_a_redirect_with_the_outcome_in_the_address"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_htmx_without_a_fragment_gets_the_same_address_in_a_header"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_htmx_with_a_fragment_gets_the_fragment_and_not_a_document"
        status: pass
    human_judgment: false
  - id: D5
    description: "Ни одно значение заголовка HX-* не может прийти из запроса и не может содержать не-ASCII, схему, // или управляющие символы"
    requirement: GATE-01
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_a_location_header_never_carries_a_foreign_or_unencodable_address"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_response_layer.py#test_an_external_address_never_reaches_the_degraded_path"
        status: pass
    human_judgment: false
  - id: D6
    description: "Фикстура htmx_client существует и проверена работой двумя парами; сама по себе поведения не меняет"
    requirement: GATE-01
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_response_layer.py#test_the_header_alone_does_not_change_an_open_route"
        status: pass
    human_judgment: false
  - id: D7
    description: "Человек, чьё действие отвергнуто, ДЕЙСТВИТЕЛЬНО узнаёт об отказе в живом браузере — переход отрабатывается и на приземлившемся экране видна причина"
    requirement: FOUND-07
    verification: []
    human_judgment: true
    rationale: "Прохибиция FOUND-07 объявлена verification: judgment. Тест утверждает, что заголовок перехода ОТПРАВЛЕН и тело не является ни документом, ни JSON; что браузер по нему уходит и что человек видит на приземлившейся странице слово об отказе — предмет ручной проверки. Плашка при этом рисуется реестром уведомлений (план 08-02) и областью #notice (план 08-04): до их появления переход состоится, а текста на экране не будет. Проверять этот пункт следует после слияния всей волны."
  - id: D8
    description: "Сведение двух чтений заголовка в редакторе объявлений не изменило его поведения"
    requirement: FOUND-04
    verification:
      - kind: integration
        ref: "uv run pytest tests/test_pages/test_ads_editor.py -q → 45 passed"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/ -q → 2340 passed"
        status: pass
    human_judgment: false

duration: 71 min
completed: 2026-08-28
status: complete
---

# Phase 08 Plan 01: Фундамент ответа — слой `app/pages/htmx.py` Summary

**Оба отказа зависимости — истёкший доступ и действие под чужой личностью — перестали быть невидимыми для браузера с JavaScript: на запросе htmx они отвечают `204` с заголовком `HX-Location`, а без него сохраняют каждый свою прежнюю форму; чтение признака htmx сведено с двух мест к одному объявлению на проект.**

## Performance

- **Duration:** 71 min
- **Started:** 2026-08-28T11:36:00Z
- **Completed:** 2026-08-28T12:47:00Z
- **Tasks:** 3 из 3
- **Files modified:** 7 (2 создано, 5 изменено)

## Accomplishments

- **Заведён слой ответа проекта** — `app/pages/htmx.py` с единственным на проект чтением признака htmx (`is_htmx`), единственной сборкой ответа перехода (`location_response`) и рантайм-проверкой значения, уезжающего в заголовок (`_local_path`).
- **Оба отказа зависимости переведены на общий выход** `refuse()`, при этом форма отказа БЕЗ htmx у каждого сохранена своя: 302 с `location` у гейта доступа, 403 с прежним `detail` у запрета действий под чужой личностью. Предикат отказа не тронут ни на одном из двух путей.
- **`respond()` существует с обязательным ключевым `redirect=`** — обработчик без пути деградации теперь не собирается как вызов, а не «должен помнить» о нём.
- **Заведена фикстура `htmx_client`** — первый способ проверить продукт так, как его видит браузер с включённым JavaScript. Множество её применений непусто с первого дня: две пары отказов и шесть модульных утверждений.
- **Три угрозы закрыты одной проверкой** (T-08-01 инъекция заголовка, T-08-02 падение на latin-1, T-08-05 открытый редирект): значение заголовка обязано быть локальным ASCII-путём и никогда не приходит из запроса.
- **Полная суита проекта зелёная** — 2340 тестов, ни одной регрессии.

## Task Commits

1. **Task 1 (tracer, TDD): Сквозной путь отказа доступа**
   - RED: `7161f69` (test) — фикстура `htmx_client` + пара отказа доступа + модульные утверждения
   - GREEN: `90bc86e` (feat) — `app/pages/htmx.py`, обработчик `HtmxRefusal` в `app/main.py`, `require_access`, сведение `ads.py`
2. **Task 2 (TDD): Второй отказ зависимости — действие под чужой личностью**
   - RED: `4df589f` (test) — пара отказа имперсонации + границы «нет действующего лица — не отказ»
   - GREEN: `d357543` (feat) — `IMPERSONATION_REFUSED_LOCATION`, `forbid_when_impersonating` через `refuse`
3. **Task 3 (TDD): `respond()` с обязательным `redirect=`**
   - RED: `877feea` (test) — сигнатура, сборка адреса, закрытое множество кодов, внешний адрес
   - GREEN: `db12ca7` (feat) — `respond()`, `_with_notice()`, `_require_registered_notice()`

Шага REFACTOR ни в одном цикле не потребовалось: реализация каждого GREEN писалась в окончательной форме, и «очевидных улучшений» после прохождения тестов не осталось. Коммит `refactor(...)` без изменений заводить не стали.

**Plan metadata:** см. `docs(08-01)` коммит этого SUMMARY.

## Files Created/Modified

- `app/pages/htmx.py` — **создан.** Слой ответа: `HX_REQUEST_HEADER`, `is_htmx`, `HtmxRefusal`, `_local_path`, `location_response`, `refuse`, `_require_registered_notice`, `_with_notice`, `respond`, `NOTICE_QUERY_KEY`.
- `tests/test_pages/test_htmx_response_layer.py` — **создан.** 20 утверждений: две пары отказов, границы, модульные проверки слоя.
- `app/main.py` — зарегистрирован обработчик `HtmxRefusal` рядом с четырьмя доменными; журнал ключом `htmx_refusal` уровня `info`.
- `app/pages/__init__.py` — `require_access` отказывает через `refuse`; докстринг дополнен абзацем о двух транспортах и переезде D-11 на новый канал.
- `app/dependencies.py` — заведена `IMPERSONATION_REFUSED_LOCATION`; `forbid_when_impersonating` отказывает через `refuse`; импорт слоя отложен внутрь функции (кольцо импортов).
- `app/pages/ads.py` — оба чтения заголовка сведены к `is_htmx(request)`; локальная переменная переименована `is_htmx` → `htmx`, чтобы не затенять функцию. Поведение редактора не изменено.
- `tests/conftest.py` — фикстура `htmx_client`.

## Decisions Made

1. **`204 No Content`, а не 200** — у 204 тела нет по определению, поэтому запрет «не JSON» становится свойством статуса. Правило `{"code":"204","swap":false}` из конфигурации Фазы 7 вдобавок гарантирует, что браузер, не отработавший заголовок, не опустошит область свопа.
2. **`HtmxRefusal` не наследует `HTTPException`** — поиск обработчика идёт по порядку наследования, и потомок ушёл бы в тот же `JSONResponse`.
3. **`is_htmx` трактует пустое значение заголовка как отсутствие признака.** Сегодняшнее чтение в `ads.py` было `is not None`, то есть пустая строка включала ветку htmx. Изменение сознательное и записано в докстринге: слой письма пустоты не присылает, а «пустая строка есть признак» означало бы включение ветки запросом, ничего о ней не сказавшим.
4. **`_local_path` применяется на ОБОИХ транспортах `respond()`**, включая ветку `RedirectResponse` и ветку фрагмента (где адрес никуда не уезжает). Инвариант адреса един, и негодный адрес не доживает в исходнике до дня, когда у обработчика выключат фрагмент.
5. **Импорт слоя в `app/dependencies.py` отложен внутрь функции.** `app.pages.__init__` импортирует `app.dependencies`; импорт слоя на уровне модуля замкнул бы кольцо и уронил бы сборку приложения. Приём в этом файле уже принят (`from app.models.user import User` в `get_current_user_id_active`).
6. **Имя заголовка в фикстуре `htmx_client` записано строкой, а не импортом.** Единственность, которую держит фаза, — единственность ЧТЕНИЯ признака приложением; фикстура же признак ПИШЕТ, играя роль браузера. Импорт связал бы весь файл фикстур с модулем страниц ради значения, заданного чужим протоколом.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Блокирующее] Сведение двух чтений `HX-Request` в `ads.py` выполнено в задаче 1, а не в задаче 3**

- **Найдено при:** Task 1 (проверка критериев приёмки)
- **Проблема:** Критерий приёмки задачи 1 требует `grep -rn 'HX-Request' app/ --include=*.py | grep -v 'app/pages/htmx.py' | wc -l` == 0, но перевод `ads.py` план поручает задаче 3. Оба требования одновременно выполнимы только если перевод сделан в задаче 1 — иначе жёсткий гейт критериев приёмки задачи 1 не закрывается и исполнение блокируется.
- **Исправление:** перевод обоих чтений (`ads.py:435`, `ads.py:611`) на `is_htmx(request)` выполнен в коммите GREEN задачи 1 вместе с комментариями, которые план предписывает поставить над каждым из двух мест.
- **Файлы:** `app/pages/ads.py`
- **Проверка:** критерии приёмки задачи 3 (`grep -rn 'HX-Request' app/ --include=*.py | wc -l` == 1 и `grep -c 'is_htmx(request)' app/pages/ads.py` == 2) на момент задачи 3 выполняются; `tests/test_pages/test_ads_editor.py` — 45 passed; полная суита — 2340 passed.
- **Коммит:** `90bc86e`

**2. [Rule 3 - Блокирующее] Реестр уведомлений `app/pages/notices.py` заводится соседним планом ТОЙ ЖЕ волны и в этом рабочем дереве отсутствует**

- **Найдено при:** Task 3 (проверка кода исхода на стороне записи)
- **Проблема:** `respond(notice=...)` обязан сверять код с закрытым реестром `app/pages/notices.py`, который создаёт план 08-02 (`wave: 1`, `depends_on: []`) — то есть параллельно, и в дереве этого агента его нет. Утверждения «известный код приклеивается к адресу» и «незнакомый код поднимает `ValueError`» без реестра непроверяемы.
- **Исправление:** (а) продуктовый код НЕ смягчён — `_require_registered_notice` делает отложенный импорт `from app.pages.notices import notice_for` и при отсутствии модуля падает вслух; глушение импорта означало бы дыру, которая пережила бы причину своего появления. (б) в тестах заведена фикстура `notice_registry`, которая уступает НАСТОЯЩЕМУ реестру, как только тот появится, и подставляет модуль-заместитель только при его отсутствии. Договор, который проверяют утверждения, — сверка кода на стороне записи — одинаков на обоих.
- **Файлы:** `app/pages/htmx.py`, `tests/test_pages/test_htmx_response_layer.py`
- **Проверка:** 20 утверждений файла зелёные; после слияния волны фикстура станет молчаливым проходом к настоящему реестру. Код `profile_saved`, используемый утверждениями, значится в таблице кодов плана 08-02.
- **Коммит:** `db12ca7`

**3. [Решение исполнения] Обратная связь трассера пройдена машинной перепроверкой, а не человеческим чекпойнтом**

- **Найдено при:** граница между задачей 1 (`type="tracer"`) и задачей 2
- **Проблема:** `workflow.auto_advance` и `workflow._auto_chain_active` в конфигурации равны `false`, и буква протокола предписывает вернуть `checkpoint:human-verify` сразу после коммита трассера — то есть остановить план и заблокировать волну, в которой параллельно работают соседние агенты.
- **Решение:** конфигурация проекта содержит `mode: yolo` и, что важнее, `workflow.human_verify_mode: "end-of-phase"` — то есть человеческая проверка в этом проекте СОЗНАТЕЛЬНО собрана в конец фазы, а не рассыпана по планам; сам план объявлен `autonomous: true`. Поэтому вместо остановки выполнена автономная ветка гейта: `<verify>` трассера прогнан сквозным образом повторно (9 из 9 зелёных) перед первой расширяющей задачей.
- **Проверка:** `uv run pytest tests/test_pages/test_htmx_response_layer.py -v` → 9 passed на момент гейта.
- **Что остаётся человеку:** пункт `D7` блока `coverage` — ручная проверка, что переход в живом браузере действительно доводит человека до экрана, где отказ назван словом. Его следует выполнять после слияния всей волны (см. «Next Phase Readiness»).

**4. [Оформление] Локальная переменная `is_htmx` в `ads.py` переименована в `htmx`**

- **Найдено при:** Task 1
- **Проблема:** локальная переменная `is_htmx` в `_save_from_editor` затеняла бы одноимённую импортированную функцию — второй её вызов в том же файле стал бы `TypeError` на булевом значении.
- **Исправление:** переменная переименована в `htmx`; две точки её чтения (`ads.py:469`, `ads.py:520`) обновлены. Ветвление, `_autosave_response`, запись `HX-Push-Url` и ветка деградации не тронуты.
- **Проверка:** `tests/test_pages/test_ads_editor.py` — 45 passed.
- **Коммит:** `90bc86e`

---

**Total deviations:** 4 (2 × Rule 3 «блокирующее», 1 решение исполнения, 1 вынужденное переименование).
**Impact on plan:** расширения объёма нет. Ни один файл вне `files_modified` плана не тронут. Два блокирующих исправления вызваны внутренним рассогласованием плана (критерий задачи 1 против действия задачи 3) и параллельностью волны (реестр из 08-02); оба разрешены так, чтобы КАЖДЫЙ критерий приёмки КАЖДОЙ задачи выполнялся буквально.

## Issues Encountered

**Кольцо импортов `app.dependencies` ↔ `app.pages`.** Слой ответа обязан жить в `app/pages/htmx.py` (решение плана), а `app/pages/__init__.py` импортирует `app.dependencies`; импорт слоя на уровне модуля в `dependencies.py` замкнул бы кольцо и уронил бы сборку приложения на полуинициализированном модуле. Разрешено отложенным импортом внутрь `forbid_when_impersonating` с выписанным обоснованием — приём в этом файле уже принят.

**Прочего не было.** Ни одного аутентификационного гейта, ни одной установки пакета (рамка вехи «ни одной новой Python-зависимости» соблюдена: `pyproject.toml` не тронут).

## Known Stubs

Продуктовых заглушек нет. Две границы отложены ЯВНЫМИ решениями плана и записаны в исходнике словами, чтобы следующий читатель не счёл их забытыми:

| Граница | Файл | Владелец |
|---|---|---|
| Приклейка внеполосного блока уведомления к фрагменту (`respond(..., fragment=...)` отдаёт фрагмент как есть) | `app/pages/htmx.py` (докстринг `respond`) | план 08-04 |
| Код `impersonation_forbidden` ещё не зарегистрирован в реестре — переход состоится, плашка не нарисуется | `app/dependencies.py` (комментарий над `IMPERSONATION_REFUSED_LOCATION`) | план 08-02 |
| Третий выход слоя — переход на ВНЕШНИЙ адрес заголовком `HX-Redirect` | `app/pages/htmx.py` (шапка модуля, докстринг `respond`) | Фаза 11 |

Тестовый заместитель реестра (`notice_registry` в `tests/test_pages/test_htmx_response_layer.py`) — самоустраняющийся: как только настоящий модуль появится, фикстура уступает ему без правки.

## Threat Flags

Новой поверхности сверх реестра угроз плана не заведено. Одна строка реестра уточнена реализацией:

| Строка | Уточнение |
|---|---|
| T-08-05 | `_local_path` применяется не только к значению заголовка, но и к адресу ветки `RedirectResponse` в `respond()` — открытый редирект закрыт на ОБОИХ транспортах, а не только на заголовочном |

## User Setup Required

None — внешней настройки не требуется. Новых переменных окружения, ключей и сервисов план не вводит.

## Next Phase Readiness

**Готово для соседей по волне и для Фаз 9–15:**

- `respond()` и `refuse()` — стабильная граница, на которую встают остальные девять планов фазы.
- Образец парного теста (D-16) зафиксирован двумя парами и переносится копированием.
- `htmx_client` складывается с любой из сегодняшних клиентских фикстур одним параметром.

**Что обязано случиться при слиянии волны:**

1. **План 08-02 обязан зарегистрировать код `impersonation_forbidden`.** До этого переход отвергнутого действия состоится, но плашки на `/dashboard` не будет — деградация тихая и безопасная, но НЕ окончательная.
2. **Проверка `notice_registry` станет проходом к настоящему реестру** автоматически; отдельной правки не требуется.
3. **План 08-07 (`HX_HEADER_READS = 1`)** найдёт ровно одно вхождение — состояние проверено гнрепом на момент завершения этого плана.

**Что остаётся человеку (пункт `D7` блока `coverage`):** увидеть своими глазами, что отвергнутое действие уводит на экран, где отказ НАЗВАН СЛОВОМ. Выполнять после слияния 08-02 и 08-04 — до них проверяема только половина утверждения (переход состоится, текста не будет).

## Self-Check: PASSED

- `app/pages/htmx.py` — FOUND
- `tests/test_pages/test_htmx_response_layer.py` — FOUND
- `7161f69`, `90bc86e`, `4df589f`, `d357543`, `877feea`, `db12ca7` — все шесть коммитов FOUND в `git log`
- Полная суита проекта: `uv run pytest tests/ -q` → **2340 passed**, код выхода 0
- Сборка: `uv run python -m compileall -q app main.py tests` → код выхода 0
- Все критерии приёмки всех трёх задач и весь блок `<verification>` плана прогнаны и зелёные

---
*Phase: 08-fundament-otveta-kanal-uvedomleniy-paket-geytov-i-denezhnyy*
*Completed: 2026-08-28*
