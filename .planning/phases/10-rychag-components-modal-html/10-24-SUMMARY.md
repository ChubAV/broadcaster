---
phase: 10-rychag-components-modal-html
plan: 24
subsystem: api
tags: [fastapi, pydantic, validation, ast-gate, identifiers, htmx]

requires:
  - phase: 10-rychag-components-modal-html
    provides: "план 10-12 — граница величины идентификатора на одном файле (`ID_MAX` и три псевдонима в `app/pages/schedules.py`)"
  - phase: 10-rychag-components-modal-html
    provides: "план 10-22 — реестр `VALIDATION_REFUSAL_DIVERGENCES` и правила полноты, обоснований, авторства"
provides:
  - "нейтральный модуль `app/pages/identifiers.py`: `ID_MAX`, `IdPath`, `IdForm`, `OptionalIdForm` — граница объявлена ОДИН раз на проект"
  - "`POST /ads/{ad_id}/delete` отвечает отказом ВАЛИДАЦИИ на величине выше границы колонки int4, а не отказом обработчика"
  - "модуль суиты `tests/test_pages/test_identifier_bounds.py`: сквозной прогон одного маршрута, смежность границы с обеих сторон, антивакуум, неотличимость повтора"
  - "правило единственности объявления границы во всём `app/` (разбор дерева) плюс два контроля — второе объявление краснит, проза вердикта не меняет"
  - "восьмая запись реестра расхождения и `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 8` с летописью числа"
  - "разрешение псевдонимов границы ПО ВСЕМУ дереву `app/` в `_framework_bounded_post_inputs` — замер перестал быть слепым к ограничению, приехавшему ввозом"
affects: [10-28, 10-29, 10-30, 10-31, 10-32, Фаза 11]

actuals:
  tokens: 8280
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "нейтральный модуль общего представления: страничные слои зависят от него, он — ни от одного из них (та же форма, что у `app/services/image_keys.py` и `app/services/schedule_rules.py`)"
    - "переезд объявления БЕЗ переименования потребителей: имя остаётся доступным по прежнему пути импорта, и суита не правится ни на символ"
    - "правило единственности по РАЗБОРУ ДЕРЕВА, а не по строкам: комментарий с числом не имеет права ронять утверждение и не имеет права заменять собой объявление"

key-files:
  created:
    - app/pages/identifiers.py
    - tests/test_pages/test_identifier_bounds.py
  modified:
    - app/pages/ads.py
    - app/pages/schedules.py
    - tests/test_pages/test_htmx_gates.py

key-decisions:
  - "`promote`, а не `add-alongside`: общее представление границы повышено в первичное, прежнее частное понижено до именованных псевдонимов. Вторая копия числа в соседнем файле разошлась бы с первой молча — тот класс отказа, за который фаза получила круги ревизии 3, 4 и 5"
  - "переезд сделан ПЕРЕНОСОМ ОБЪЯВЛЕНИЯ, а не переименованием потребителей: `ID_MAX` ввозится в `app/pages/schedules.py` и остаётся доступным по прежнему пути, поэтому два модуля суиты не правились"
  - "решение о законности расхождения с запертым D-01 планом НЕ ЧЕКАНИТСЯ: состояние восьмой записи — «ЖДЁТ ВЛАДЕЛЬЦА» (прецедент окна 51)"
  - "замер `_framework_bounded_post_inputs` разрешает псевдонимы по всему дереву `app/`, а не внутри модуля: охват ВХОДОВ не расширен, расширено только место поиска ОБЪЯВЛЕНИЯ псевдонима"

patterns-established:
  - "Летопись МЕСТА рядом с летописью ИМЕНИ: переехавшее объявление несёт абзац о том, что прежнее место не было ошибкой, и называет поимённо источник расхождения"
  - "Внутриплановый долг закрытого перечня полноты называется ЧИСЛОМ и закрывается ВНУТРИ того же плана, а не переносится в следующий"

requirements-completed: [FORM-06]

coverage:
  - id: D1
    description: "Граница величины идентификатора объявлена в проекте РОВНО ОДИН раз, в модуле, не зависящем ни от одного страничного"
    requirement: "FORM-06"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_identifier_bounds.py#test_the_identifier_bound_is_declared_exactly_once_in_the_whole_app"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_identifier_bounds.py#test_control_negative_a_second_declaration_reddens_the_uniqueness_rule"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_identifier_bounds.py#test_control_the_uniqueness_rule_does_not_read_prose"
        status: pass
      - kind: other
        ref: "uv run python -c \"import ast,pathlib,sys; ...\" — модуль границы не импортирует ни `app.pages.*`, ни `app.models.*` (rc=0)"
        status: pass
    human_judgment: false
  - id: D2
    description: "`POST /ads/{ad_id}/delete` отвечает отказом валидации выше границы колонки и НЕ отвечает им на самой границе; живое объявление по-прежнему удаляется"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_ads_delete_refuses_a_value_no_driver_can_hold_with_a_validation_refusal"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_ads_delete_draws_the_column_boundary_on_both_of_its_sides"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_ads_delete_still_removes_a_live_advert_of_its_owner"
        status: pass
    human_judgment: false
  - id: D3
    description: "Повтор отвергнутого запроса неотличим от первого — граница есть чистая функция запроса"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_a_repeated_refused_request_is_indistinguishable_from_the_first"
        status: pass
    human_judgment: false
  - id: D4
    description: "Три прежних псевдонима страничного модуля расписаний строятся из общей границы, а прежние импортирующие модули суиты не правились и зелены"
    requirement: "FORM-06"
    verification:
      - kind: other
        ref: "uv run python -c \"... print(ID_MAX is i.ID_MAX, ScheduleIdPath is i.IdPath, AdIdForm is i.IdForm, AccountIdForm is i.OptionalIdForm)\" → True True True True"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/test_pages/test_editor_schedules.py tests/test_pages/test_confirm_delete_transport.py -q → 120 passed"
        status: pass
    human_judgment: false
  - id: D5
    description: "Реестр расхождения формы отказа валидации вырос на объявленное число 7 → 8, запись несёт все пять полей и ждущее состояние решения"
    requirement: "FORM-06"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_number_of_validation_refusal_divergences_is_declared"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_every_framework_bounded_input_is_declared_as_a_divergence"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_shortened_exception_list_reddens_the_completeness_rule"
        status: pass
    human_judgment: false
  - id: D6
    description: "Одновременные запросы с негодной величиной отвергаются независимо друг от друга (ребро `concurrency` зонда покрытия)"
    verification: []
    human_judgment: true
    rationale: "СТРУКТУРНЫЙ МАРКЕР `backstop`, объявленный самим планом. Машинно проверяемо только ОТСУТСТВИЕ изменяемого состояния уровня модуля в `app/pages/identifiers.py` (модуль объявляет четыре имени и ни одного изменяемого контейнера); что два ПАРАЛЛЕЛЬНЫХ запроса не влияют один на другой, суита без процесса не наблюдает. Верификатор обязан ВОЗДЕРЖАТЬСЯ, а не проставить молчаливый проход"
  - id: D7
    description: "Поведение БОЕВОГО драйвера (PostgreSQL/asyncpg) на неограниченном входе"
    verification: []
    human_judgment: true
    rationale: "НЕ НАБЛЮДАЕТСЯ И НАБЛЮДАТЬ НЕ МОЖЕТ: у суиты драйвер один (`sqlite+aiosqlite:///:memory:`). Отказ ставит ГРАНИЦА ПРИЛОЖЕНИЯ — до драйвера дело не доходит, — поэтому зелёное здесь о боевом драйвере не говорит ничего. Предмет окна 39 реестра, и оно остаётся ОТКРЫТЫМ"

duration: 1h 23m
completed: 2026-09-08
status: complete
---

# Phase 10 Plan 24: Граница величины идентификатора — свойство проекта, а не одного файла — Summary

**Граница величины идентификатора (`ID_MAX` = 2147483647) переехала из страничного модуля расписаний в нейтральный `app/pages/identifiers.py`, объявлена там РОВНО ОДИН раз на весь `app/` под машинным правилом единственности, и доказана ОДНИМ маршрутом насквозь: `POST /ads/{ad_id}/delete` отвечает `422` вместо `500` на величине выше границы колонки int4.**

## Performance

- **Duration:** 1h 23m
- **Started:** 2026-09-08T06:27:44Z
- **Completed:** 2026-09-08T07:50:56Z
- **Tasks:** 3
- **Files modified:** 5 (2 создано, 3 правлено)

## Accomplishments

- **Граница перестала быть свойством одного файла.** `app/pages/identifiers.py` объявляет `ID_MAX`, `IdPath`, `IdForm`, `OptionalIdForm` и не импортирует ни `app.pages.*`, ни `app.models.*` — зависимость идёт только в одну сторону. Разбор дерева всего `app/` находит РОВНО ОДНО присваивание величины границы, и владелец его назван путём.
- **Один маршрут проведён насквозь.** `POST /ads/2147483648/delete` и `POST /ads/<26 девяток>/delete` отвечают `422`; `POST /ads/2147483647/delete` — `302` (величина в диапазоне лежит, и что с ней дальше — дело владения строкой); `POST /ads/0/delete` — `422`. Отказ стои́т ДО тела обработчика, поэтому гард происхождения (`is_same_origin`) перестал быть недостижимым на негодной величине.
- **Прежние импортирующие не тронуты.** Имя `ID_MAX` осталось доступным по пути `app.pages.schedules`, два модуля суиты, ввозящие его оттуда, не правились ни на символ и зелены (120 passed).
- **Реестр расхождения вырос на объявленное число 7 → 8** с летописью числа, и внутриплановый долг правила полноты закрыт ВНУТРИ этого же плана.
- **Замер реестра перестал быть слепым к ограничению, приехавшему ввозом** — иначе переезд границы обнулил бы измеренную вселенную правила полноты (см. Deviations, п. 2).

## Task Commits

1. **Задача 1 (RED): красное правило границы** — `c436bd1` (test)
2. **Задача 1 (GREEN): нейтральный модуль и один маршрут насквозь** — `4a83278` (feat)
3. **Задача 2: страничный модуль перестал держать свою копию числа** — `ed9d032` (feat)
4. **Задача 3: реестр расхождения 7 → 8** — `a96758f` (feat)

## Files Created/Modified

- `app/pages/identifiers.py` — НОВЫЙ нейтральный модуль границы. Четыре основания перенесены ДОСЛОВНО (предмет границы есть КОЛОНКА; псевдонимов ТРИ, потому что различается способ передачи; нижняя граница — единица; граница стои́т на границе приложения), летопись имени `_AD_ID_MAX` → `ID_MAX` переехала целиком, дописана летопись МЕСТА.
- `app/pages/ads.py` — `ads_delete` объявляет `ad_id` через `IdPath`; тело обработчика не тронуто ни одной строкой.
- `app/pages/schedules.py` — три псевдонима стали именованными псевдонимами общих; собственного объявления величины больше нет; сняты осиротевшие импорты `Annotated`, `Form`, `Path`.
- `tests/test_pages/test_identifier_bounds.py` — НОВЫЙ модуль суиты: 7 правил (сквозное отображение, антивакуум, неотличимость повтора, единственность объявления и два её контроля).
- `tests/test_pages/test_htmx_gates.py` — восьмая запись реестра, `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 8` с летописью, и разрешение псевдонимов по всему дереву `app/`.

## Красный ДО правки — НАБЛЮДЁН, А НЕ ПРЕДПОЛОЖЕН

Прогон правила пункта 2 `<behavior>` на дереве ДО шагов (1)…(4), дословно:

```
E       AssertionError: величина, не влезающая ни в один драйвер, доехала до тела обработчика (снято → '500'; ожидалось → '422'). Предмет — граница ПРИЛОЖЕНИЯ: значение вне диапазона колонки обязано отвергаться ДО тела обработчика, а не ронять запрос драйвером (`CR-01` пятого круга ревизии)
E       assert '500' == '422'
E
E         - 422
E         + 500

tests/test_pages/test_identifier_bounds.py:108: AssertionError
=========================== short test summary info ============================
FAILED tests/test_pages/test_identifier_bounds.py::test_ads_delete_refuses_a_value_no_driver_can_hold_with_a_validation_refusal
1 failed, 1 warning in 1.39s
```

Причина `500` снята из журнала того же прогона и названа поимённо:
`OverflowError: Python int too large to convert to SQLite INTEGER`, `app/pages/ads.py:776` (`await db.execute(...)`), пойманный собственной прослойкой проекта `app/middleware.py:27`.

## Красный правила единственности — ПОКАЗАН МУТАЦИЕЙ

В `app/pages/schedules.py` временно вписано второе присваивание той же величины, прогон, вывод дословно, мутация снята:

```
E       AssertionError: объявлений величины границы (2147483647) во всём `app/` не одно, а 2, либо владелец её не `app/pages/identifiers.py`. НАЙДЕНЫ ВСЕ места: ['app/pages/identifiers.py:65 → ID_MAX', 'app/pages/schedules.py:1242 → _MUTATION_SECOND_BOUND']. Вторая копия числа расходится с первой МОЛЧА при первой же правке колонки — ровно тот класс отказа (`запись шире дерева`), за который фаза получила круги ревизии 3, 4 и 5. Величина объявляется в `app/pages/identifiers.py`, а потребители ввозят её оттуда
E       assert (2 == 1)
E        +  where 2 = len(['app/pages/identifiers.py:65 → ID_MAX', 'app/pages/schedules.py:1242 → _MUTATION_SECOND_BOUND'])
```

Отказ называет ОБА места, а не первое. Мутация снята; `git diff --stat` после снятия показал только правки задачи 2.

## Долг реестра внутри плана — НАЗВАН ЧИСЛОМ

Прогон жалоб правила полноты ПОСЛЕ задачи 2, дословно:

```
жалоб правила полноты: 1
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/ads.py::POST /ads/{ad_id}/delete → адрес ad_id (псевдоним IdPath)
RC=0 — долг реестра равен ровно одному входу
```

Ровно одна жалоба, ровно на вход, ограниченный задачей 1. Долг закрыт задачей 3 ЭТОГО ЖЕ плана, не следующим планом и не следующей волной.

## Зубы правила полноты на новом входе — ПОКАЗАНЫ УКОРОЧЕННЫМ ПЕРЕЧНЕМ

```
перечень укорочен: 8 → 7
 * НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/ads.py::POST /ads/{ad_id}/delete → адрес ad_id (псевдоним IdPath)
боевой перечень после контроля: []
```

## Ключ новой записи — СНЯТ ПРОГОНОМ ЗАМЕРА, А НЕ НАБРАН ПО ПАМЯТИ

```
измерено входов: 8
  app/pages/ads.py::POST /ads/{ad_id}/delete → адрес ad_id → IdPath
  app/pages/schedules.py::POST /schedules/new → форма account_id → AccountIdForm
  app/pages/schedules.py::POST /schedules/new → форма ad_id → AdIdForm
  app/pages/schedules.py::POST /schedules/{schedule_id}/delete → адрес schedule_id → ScheduleIdPath
  app/pages/schedules.py::POST /schedules/{schedule_id}/edit → адрес schedule_id → ScheduleIdPath
  app/pages/schedules.py::POST /schedules/{schedule_id}/edit → форма account_id → AccountIdForm
  app/pages/schedules.py::POST /schedules/{schedule_id}/edit → форма ad_id → AdIdForm
  app/pages/schedules.py::POST /schedules/{schedule_id}/toggle → адрес schedule_id → ScheduleIdPath
жалоб: 0
```

## Замеры прежних имён — ОБА ПРИВЕДЕНЫ

- `grep -c "ScheduleIdPath" tests/test_pages/test_editor_schedules.py`: **ДО (HEAD) = 3**, **ПОСЛЕ (дерево) = 3**. Ни один из трёх псевдонимов не переименован.
- Ни один файл суиты, ввозящий `ID_MAX`, не правился: `git status --short` на коммите задачи 2 не содержал ни `tests/test_pages/test_editor_schedules.py`, ни `tests/test_pages/test_confirm_delete_transport.py`.
- Удалённых строк в `tests/test_pages/test_htmx_gates.py` на коммите задачи 3 — **ровно одна**, и это сама строка `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 7`. Прежние семь записей не правились.

## Decisions Made

1. **`promote`, а не `add-alongside`.** Общее представление повышено в первичное; прежнее частное понижено до именованных псевдонимов. Ветвь `add-alongside` отвергнута с названным последствием: вторая копия числа `2147483647` в соседнем файле разошлась бы с первой молча. Решение подкреплено МАШИННЫМ ПРИНУЖДЕНИЕМ — правилом единственности, а не намерением.
2. **Переезд переносом объявления, а не переименованием потребителей.** `ID_MAX` ввозится в `app/pages/schedules.py` и остаётся доступным по прежнему пути. Цена отката названа планом величиной (два модуля суиты), и переезд её не заплатил.
3. **Решение о законности расхождения с D-01 НЕ ЧЕКАНИТСЯ.** Изъятие из запертого решения принадлежит владельцу (прецедент окна 51); состояние восьмой записи — `DECISION_WAITS_FOR_THE_OWNER`.
4. **Замер разрешает псевдонимы по всему дереву `app/`.** Охват ВХОДОВ не расширен — он по-прежнему есть POST-обработчики поданных исходников; расширено только место поиска ОБЪЯВЛЕНИЯ псевдонима (см. Deviations, п. 2).

## Deviations from Plan

### Auto-fixed Issues

**1. [Правило 3 — Блокер] Команда проверки задачи 1 указывала на несуществующий файл суиты**

- **Найдено при:** Задача 1 (прогон `<verify>`)
- **Проблема:** `<verify>` задачи 1 требует `uv run pytest tests/test_pages/test_ads.py ...`. Файла `tests/test_pages/test_ads.py` в дереве НЕТ. Команда завершалась кодом 0, собрав НОЛЬ правил, — то есть гейт, поставленный ловить регрессию маршрута удаления объявления, был вакуумно-зелёным по построению.
- **Исправление:** подставлены действующие модули суиты маршрутов объявлений: `test_ads_editor.py`, `test_ads_status.py`, `test_ads_image_ownership.py`, а также `test_origin_guard_on_destructive_routes.py` (гард происхождения — прямой сосед правки) вместе с названным планом `test_confirm_delete_transport.py`.
- **Замер:** `150 passed`.
- **Committed in:** `4a83278`

**2. [Правило 3 — Блокер] Замер `_framework_bounded_post_inputs` был слеп к ограничению, приехавшему ВВОЗОМ**

- **Найдено при:** Задача 2 (прогон команды долга реестра)
- **Проблема:** замер собирал таблицу псевдонимов ВНУТРИ модуля — только из присваиваний вида `X = Annotated[int, Path(ge=..., le=...)]`. После переезда `ScheduleIdPath = IdPath` перестало быть таким присваиванием, а `IdPath` в `app/pages/ads.py` приезжает импортом. Прогон дал **НОЛЬ измеренных входов при семи объявленных**: семь жалоб «ОБЪЯВЛЕН, НО ЗАМЕРОМ НЕ НАЙДЕН» на ВЕРНОМ дереве. Цена названа двумя следствиями: (1) правило полноты краснело бы на верном дереве; (2) что хуже — измеренная вселенная стала бы ПУСТОЙ, и в направлении «найден замером, но не объявлен» правило зеленело бы вакуумом навсегда, а любой будущий обработчик, ограниченный общим псевдонимом, остался бы для него невидим.
- **Исправление:** разрешение псевдонимов вынесено в отдельный проход по `{**_app_sources(), **sources}` и доведено до НЕПОДВИЖНОЙ ТОЧКИ (ввоз ввезённого имени — законная цепочка, и один проход разрешил бы её только при удачном порядке файлов). Охват ВХОДОВ не менялся. Основание записано абзацем у самого замера.
- **Замер:** измерено входов 8, жалоб 1 (ровно долг задачи 1), после задачи 3 — 0.
- **Committed in:** `ed9d032`

**3. [Правило 3 — Блокер] Критерий приёмки задачи 1 требовал текста, которого `inspect.signature` не печатает**

- **Найдено при:** Задача 1 (проверка критериев приёмки)
- **Проблема:** критерий требует, чтобы вывод `inspect.signature(m.ads_delete)` по параметру `ad_id` содержал `Annotated`, `ge=1` и `le=2147483647`. Фактический вывод — `ad_id: Annotated[int, Path(PydanticUndefined)]`: `repr` объекта `fastapi.params.Path` границ не несёт ни при каком состоянии дерева, они лежат в `.metadata` как `[Ge(ge=1), Le(le=2147483647)]`.
- **Исправление:** подставлена проверка, читающая ИЗМЕРЕННЫЕ границы из аннотации, а не полагающаяся на `repr`. Вывод: `ad_id: Annotated[int, Path(ge=1, le=2147483647)]` — содержит все три искомые подстроки, и содержит их ЗАМЕРОМ.
- **Committed in:** `4a83278`

**4. [Правило 2 — Недостающее критичное] Правило единственности получило ПОСТОЯННЫЕ контроли, а не только разовую мутацию**

- **Найдено при:** Задача 2, пункт (5)
- **Проблема:** план требует показать зубы правила разовой мутацией на диске и привести красный в сводку. Разовый показ живёт в сводке, а не в дереве: правило, чьи зубы никто не стережёт, деградирует до вакуумно-зелёного молча — записанный опыт окна 29.
- **Исправление:** мутация на диске выполнена и красный приведён выше ДОСЛОВНО, но, сверх того, заведены два ПОСТОЯННЫХ контроля на копии дерева в памяти: `test_control_negative_a_second_declaration_reddens_the_uniqueness_rule` (второе объявление обязано краснить и обязано назвать ОБА места) и `test_control_the_uniqueness_rule_does_not_read_prose` (комментарий и докстринг с числом вердикта менять не имеют права). Форма взята у действующих контролей `test_editor_schedules.py` и `test_htmx_gates.py`.
- **Committed in:** `ed9d032`

**5. [Правило 3 — Блокер] Осиротевшие импорты в `app/pages/schedules.py`**

- **Найдено при:** Задача 2
- **Проблема:** после переезда `Annotated`, `Form` и `Path` перестали употребляться в файле — каждое встречалось ровно один раз, в собственной строке импорта.
- **Исправление:** сняты. `Query` оставлен (10 употреблений).
- **Committed in:** `ed9d032`

---

**Total deviations:** 5 auto-fixed (4 × Правило 3 «блокер», 1 × Правило 2 «недостающее критичное»)
**Impact on plan:** предмета плана ни одно отступление не сдвинуло. Три из пяти — починка ПРОВЕРОК плана, оказавшихся вакуумными или неисполнимыми на действующем дереве (несуществующий файл суиты, `repr` без границ, слепой замер); два — гигиена и укрепление зубов. Расширения охвата нет: замер по-прежнему берёт POST-обработчики страничного слоя, реестр по-прежнему закрытый перечень полноты.

## Issues Encountered

**Правило полноты и его контроль краснеют ПО ПОСТРОЕНИЮ между задачей 1 и задачей 3, и узлов таких ДВА, а не один.** План назвал и снял из широкого прогона задачи 2 ОДИН узел (`test_every_framework_bounded_input_is_declared_as_a_divergence`). Замер показал ВТОРОЙ с тем же основанием: `test_control_a_shortened_exception_list_reddens_the_completeness_rule` последним утверждением требует, чтобы БОЕВОЙ перечень не давал ни одной жалобы, — а между задачей 1 и задачей 3 он даёт ровно одну, ту самую внутриплановую. Оба узла закрыты задачей 3 в этом же плане; после неё `tests/test_pages/test_htmx_gates.py` — **35 passed**, снятых узлов не осталось.

**Два `ERROR` в широком прогоне задачи 2 оказались артефактом флага прогона, а не дефектом.** `tests/test_pages/test_blocked_user.py::test_the_login_refusal_is_journaled_with_the_user_id` и `::test_the_json_refusal_is_journaled_with_the_user_id` падали с `fixture 'caplog' not found`, потому что прогон шёл с `-p no:logging` (флаг гасил и плагин, дающий `caplog`). Прогон того же модуля без флага: **20 passed**. Дерева это не касается.

## Итоговые прогоны

- `uv run pytest tests/test_pages/test_identifier_bounds.py tests/test_pages/test_editor_schedules.py tests/test_pages/test_confirm_delete_transport.py tests/test_pages/test_htmx_gates.py -q` → **162 passed**
- `uv run pytest tests/test_pages/ -q` (ВЕСЬ страничный слой, БЕЗ единого снятого узла) → **1526 passed**, 0 failed, 0 errors
- `uv run python -m compileall -q app main.py tests` → **rc=0**

## Known Stubs

Нет. Заглушек, мешающих достижению цели плана, не заведено; ни одно правило не помечено пропускаемым.

## Что этот план НЕ закрывает

- **Окно 39 реестра — поведение боевого драйвера на неограниченном входе.** Основание — ОТСУТСТВИЕ ВТОРОГО ДРАЙВЕРА У СУИТЫ. План сделал вопрос МЕНЕЕ важным (отказ ставится до драйвера), но не ответил на него. Окно ОТКРЫТО.
- **Окно 45 реестра — полнота границы по всему страничному слою.** Закрывает план 10-30. Ограничен ОДИН маршрут из двадцати семи, и снимать окно на этом основании значило бы закрыть его замером одной двадцать седьмой.
- **Ребро `ordering` зонда покрытия** — ЯВНОЕ ДОПУЩЕНИЕ. Предмет наблюдается только рантаймом разметки; пятая партия его не трогает, основание третьей партии наследуется без пересмотра.
- **Расхождение восьмой записи с запертым D-01** — сделано ВИДИМЫМ, но не решено: снятие есть работа Фазы 11 по роадмапу, а вопрос законности до тех пор принадлежит владельцу.

## User Setup Required

None — внешней конфигурации план не требует.

## Next Phase Readiness

- **Готово для планов 10-28, 10-29 и 10-30:** нейтральный модуль границы стои́т, замер реестра видит ограничение, приехавшее ввозом (без этого планы 10-28/10-29 заводили бы записи о входах, которых их замер не находит), правило единственности стережёт расползание копий числа.
- **Предупреждение следующим планам партии:** `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 8` есть СЕРЕДИНА партии, а не её итог — 10-28 сдвигает число до 17, 10-29 до 23. Летопись числа это говорит прямым текстом.
- **Блокеров нет.**

## Self-Check: PASSED

- `app/pages/identifiers.py` — FOUND
- `tests/test_pages/test_identifier_bounds.py` — FOUND
- Коммиты `c436bd1`, `4a83278`, `ed9d032`, `a96758f` — все FOUND
- Все `<acceptance_criteria>` трёх задач перепрогнаны; все `<verify>` плана перепрогнаны (с тремя замещениями, названными в Deviations)

---
*Phase: 10-rychag-components-modal-html*
*Completed: 2026-09-08*
