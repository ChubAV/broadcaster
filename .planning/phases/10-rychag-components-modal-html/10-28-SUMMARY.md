---
phase: 10-rychag-components-modal-html
plan: 28
subsystem: api
tags: [fastapi, pydantic, validation, identifiers, ast-gate, htmx]

requires:
  - phase: 10-rychag-components-modal-html
    provides: "план 10-24 — нейтральный модуль `app/pages/identifiers.py` (`ID_MAX`, `IdPath`, `IdForm`, `OptionalIdForm`), модуль суиты `tests/test_pages/test_identifier_bounds.py`, восьмая запись реестра расхождения и разрешение псевдонимов границы по всему дереву `app/`"
  - phase: 10-rychag-components-modal-html
    provides: "план 10-22 — реестр `VALIDATION_REFUSAL_DIVERGENCES` и три его правила (полноты, обоснований, авторства)"
  - phase: 10-rychag-components-modal-html
    provides: "план 10-18 — семья ЧЕТЫРЁХ маршрутов подтверждённого удаления, сведённая под общий гард"
provides:
  - "пятнадцать идентификаторов ПУТИ четырёх продуктовых страничных модулей под общей границей `IdPath`"
  - "два идентификатора, приезжающих ПАРАМЕТРОМ ЗАПРОСА, под той же величиной: курсор постраничного вывода групп (верхняя граница) и признак раскрытого расписания редактора (обе)"
  - "матрица «вход → снятый код» на СЕМНАДЦАТЬ входов в `tests/test_pages/test_identifier_bounds.py`: отказ вне диапазона, смежность на границе, антивакуум на живой величине — каждое правило по ВСЕМУ перечню и с перечислением ВСЕХ несогласных строк"
  - "девять записей реестра расхождения (с девятой по семнадцатую) с ИЗМЕРЕННОЙ достижимостью каждого входа и `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 17`"
  - "третья строка летописи объявленного числа реестра с основанием счёта ВХОДОВ, а не исходов, и с названным составом того, что в рост не вошло"
  - "НАХОДКА: признак раскрытого расписания до сравнения по колонке НЕ ДОЕЗЖАЕТ — закрыт по объявленному предмету, и разница записана"
affects: [10-29, 10-30, 10-31, 10-32, Фаза 11]

actuals:
  tokens: 13333
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "МАТРИЦА ВХОДОВ вместо образца: правило сличает отображение «вход → снятый код» целиком и называет ВСЕ несогласные строки, поэтому чинится одним кругом, а не по одному входу за круг"
    - "СВЕЖИЙ ПОСЕВ НА КАЖДЫЙ ВХОД антивакуума: перечень с необратимыми входами при общем посеве начал бы утверждать о ПОРЯДКЕ, а не о границе"
    - "ВЫБОР ВЕТКИ ПОСЕВОМ, А НЕ ЗАГЛУШКОЙ: состояние и тип посеянной строки уводят обработчик в детерминированную ветку до обращения к внешней системе, и это записано у посева, а не оставлено читателю"
    - "ЗАКРЫТИЕ ПО ОБЪЯВЛЕННОМУ ПРЕДМЕТУ с НАЗВАННОЙ разницей: параметр, объявленный идентификатором, но не доезжающий до сравнения по колонке, закрывается всё равно — и основание отличается от основания прослеженного пути ПРЯМО, а не сглаживается"

key-files:
  created: []
  modified:
    - app/pages/account_groups.py
    - app/pages/accounts.py
    - app/pages/ads.py
    - app/pages/history.py
    - tests/test_pages/test_identifier_bounds.py
    - tests/test_pages/test_htmx_gates.py

key-decisions:
  - "Идентификаторы, приезжающие ПАРАМЕТРОМ ЗАПРОСА, закрыты вместе с идентификаторами адреса, а не отложены: разведение их по способу передачи было бы разведением по ВНЕШНЕМУ признаку — ровно тот дефект, который ревизия предъявила на адресах"
  - "Курсор и признак раскрытого расписания закрыты по РАЗНЫМ основаниям, и разница записана у каждого: курсор ДОЕЗЖАЕТ до сравнения по колонке (`Group.id > after_id`), признак — НЕ ДОЕЗЖАЕТ (сличается с уже загруженным составом в памяти) и закрыт по ОБЪЯВЛЕННОМУ предмету"
  - "Реестр вырос на ДЕВЯТЬ, а не на шесть: ревизия воспроизвела отказ на шести МАРШРУТАХ, но два из них несут по два ограниченных идентификатора адреса, а один закрыт планом 10-24. Тот же счёт ВХОДОВ вместо ИСХОДОВ, которым перечень вырос до семи вместо пяти на первом круге"
  - "Достижимость каждого из девяти входов измерена ЧТЕНИЕМ РАЗМЕТКИ, и обоснования пар входов одного маршрута называют РАЗНЫЕ СЕГМЕНТЫ одного адреса и разный ИСТОЧНИК величины — контекст экрана против отрисованной строки; строка разметки у пары общая ПО ПОСТРОЕНИЮ, и это записано как замер, а не обойдено выдумыванием различия"
  - "Решение о законности расхождения формы отказа с запертым D-01 планом НЕ ЧЕКАНИТСЯ: состояние всех девяти новых записей — «ЖДЁТ ВЛАДЕЛЬЦА» (прецедент окна 51, унаследован от плана 10-24)"

patterns-established:
  - "Различие ОДНОГО адреса на ДВА входа обосновывается ИСТОЧНИКОМ величины, а не строкой файла: строка у них общая по построению, и требование различать их путём со строкой пришлось бы удовлетворять выдумкой"
  - "Внутриплановый долг закрытого перечня полноты меряется отдельной командой с проверкой ВЛАДЕНИЯ каждой жалобой, и разность долгов между задачами сличается с числом новых входов — то есть закрытие долга проверяется, а не обещается"

requirements-completed: [FORM-06]

coverage:
  - id: D1
    description: "Все четыре маршрута семьи подтверждённого удаления (аккаунт, объявление, группа аккаунта, расписание) отвечают отказом ВАЛИДАЦИИ на величине вне диапазона колонки — семья перестала быть закрытой для одного своего члена из четырёх"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_refuses_a_value_outside_the_column"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_ads_delete_refuses_a_value_no_driver_can_hold_with_a_validation_refusal (маршрут удаления объявления, закрыт планом 10-24)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Тумблер группы аккаунта и правка объявления, названные ревизией поимённо, отвечают тем же отказом валидации"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_refuses_a_value_outside_the_column"
        status: pass
    human_judgment: false
  - id: D3
    description: "Повтор отправки из журнала отвечает отказом валидации на негодной величине — шестой воспроизведённый ревизией маршрут закрыт"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_refuses_a_value_outside_the_column"
        status: pass
    human_judgment: false
  - id: D4
    description: "Идентификаторы, приезжающие параметром запроса (курсор постраничного вывода групп и признак раскрытого расписания), закрыты той же границей; пустое значение признака остаётся законным"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_refuses_a_value_outside_the_column"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_the_editor_without_the_schedule_flag_is_not_a_validation_refusal"
        status: pass
    human_judgment: false
  - id: D5
    description: "Смежность границы показана на КАЖДОМ из семнадцати входов, а не на образце: величина, равная границе, отказом валидации не отвергается"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_admits_the_value_at_the_column"
        status: pass
    human_judgment: false
  - id: D6
    description: "Живые величины по-прежнему работают на КАЖДОМ закрытом входе — антивакуум прогнан по всему перечню со свежим посевом на каждый вход"
    requirement: "FORM-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_identifier_bounds.py#test_every_bounded_input_still_admits_a_live_value"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/ -q -m \"not planning\" → 2854 passed, 28 deselected (35:24), rc=0"
        status: pass
    human_judgment: false
  - id: D7
    description: "Реестр расхождения вырос РОВНО на число новых ограниченных входов POST-обработчиков (8 → 17), и рост снят прогоном замера, а не сложен в уме"
    requirement: "FORM-06"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_the_number_of_validation_refusal_divergences_is_declared"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_every_framework_bounded_input_is_declared_as_a_divergence"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_every_validation_refusal_divergence_carries_a_non_empty_rationale"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_gates.py#test_control_a_shortened_exception_list_reddens_the_completeness_rule"
        status: pass
      - kind: other
        ref: "uv run python -c \"... complaints(declared[:8]) ...\" → девять жалоб с девятью именами; на боевом перечне ноль"
        status: pass
    human_judgment: false
  - id: D8
    description: "Поведение БОЕВОГО драйвера (PostgreSQL/asyncpg) на неограниченном входе"
    verification: []
    human_judgment: true
    rationale: "НЕ НАБЛЮДАЕТСЯ И НАБЛЮДАТЬ НЕ МОЖЕТ: у суиты драйвер один (`sqlite+aiosqlite:///:memory:`). Отказ ставит ГРАНИЦА ПРИЛОЖЕНИЯ — до драйвера дело не доходит, — поэтому зелёное здесь о боевом драйвере не говорит ничего. Предмет окна 39 реестра `.planning/WINDOWS.md`, и оно остаётся ОТКРЫТЫМ. Унаследовано от плана 10-24 дословно"
  - id: D9
    description: "Законность расхождения формы отказа валидации с запертым D-01 на девяти новых POST-входах"
    verification: []
    human_judgment: true
    rationale: "РЕШЕНИЕ ПРИНАДЛЕЖИТ ВЛАДЕЛЬЦУ, А НЕ ПЛАНУ И НЕ ИСПОЛНИТЕЛЮ: изъятие из запертого D-01 чеканит владелец (прецедент D-08 записан им самим на этапе обсуждения). План обеспечил ВИДИМОСТЬ расхождения — девять записей с ценой, измеренной достижимостью, условием снятия и состоянием «ЖДЁТ ВЛАДЕЛЬЦА», — и правило авторства машинно не даёт превратить это состояние в «решено» без ссылки на `D-NN` либо закрытое окно. Верификатор обязан ВОЗДЕРЖАТЬСЯ, а не проставить молчаливый проход"

duration: 1h 47m
completed: 2026-09-08
status: complete
---

# Phase 10 Plan 28: Граница величины идентификатора на всех продуктовых модулях Summary

**Пятнадцать идентификаторов пути и два идентификатора, приезжающих параметром запроса, в четырёх продуктовых страничных модулях встали под общую границу `IdPath`/`ID_MAX`: шесть воспроизведённых ревизией маршрутов отвечают `422` вместо `500`/`302`, смежность и антивакуум показаны на КАЖДОМ из семнадцати входов, реестр расхождения вырос 8 → 17 с измеренной достижимостью каждой записи.**

## Performance

- **Duration:** 1h 47m
- **Started:** 2026-09-08T11:05:00Z
- **Completed:** 2026-09-08T12:52:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- **Семья подтверждённого удаления перестала быть закрытой для одного своего члена из четырёх.** Удаление аккаунта, удаление группы аккаунта и удаление расписания встали рядом с удалением объявления, закрытым планом 10-24: все четыре отвечают отказом ВАЛИДАЦИИ на величине вне диапазона колонки. Отказ стои́т ДО тела обработчика, поэтому гард происхождения (`is_same_origin`), который ревизия назвала НЕДОСТИЖИМЫМ на негодной величине, перестал им быть.
- **Закрыты и остальные два маршрута, названные ревизией поимённо** — тумблер группы и правка объявления, — плюс повтор отправки из журнала: все шесть воспроизведённых исходов `CR-01` пятого круга на продуктовой стороне.
- **Идентификаторы, приезжающие ПАРАМЕТРОМ ЗАПРОСА, закрыты той же границей, и это не расширение объёма, а его честная граница.** Курсор постраничного вывода групп уезжает операндом сравнения SQL по колонке идентификатора; признак раскрытого расписания объявлен идентификатором расписания. Оставить их значило бы повторить ровно тот дефект, который ревизия предъявила: семья закрыта для тех своих членов, на которые смотрели.
- **Матрица вместо образца.** Семнадцать входов × три величины вне диапазона = 51 строка отказа, 17 проверок смежности на границе, 17 живых величин со СВЕЖИМ посевом на каждую. Каждое правило называет ВСЕ несогласные строки, а не первую.
- **Реестр расхождения 8 → 17** — девять записей с ИЗМЕРЕННОЙ чтением разметки достижимостью, объявленное число поставлено прогоном покрасневшего правила, внутриплановый долг закрыт ВНУТРИ этого же плана и сличён числом между задачами.
- **Полная суита зелена:** `2854 passed, 28 deselected` за 35:24, rc=0.

## Task Commits

1. **Задача 1 (RED): матрица входов двух модулей** — `dc2f01e` (test)
2. **Задача 1 (GREEN): семья подтверждённого удаления закрыта для всех членов** — `8877135` (feat)
3. **Задача 2 (RED): пять входов редактора и журнала в ту же матрицу** — `42f9943` (test)
4. **Задача 2 (GREEN): правка объявления, редактор, журнал и признак расписания** — `caa5e10` (feat)
5. **Задача 3: реестр расхождения 8 → 17** — `8c745df` (feat)

**Plan metadata:** см. финальный `docs(10-28)` коммит.

## Files Created/Modified

- `app/pages/account_groups.py` — семь идентификаторов пути через общий `IdPath` (страница групп, постраничный вывод, состояние синхронизации, тумблер и удаление группы — у двух последних по ДВА идентификатора) плюс ВЕРХНЯЯ граница курсора постраничного вывода с записанным основанием.
- `app/pages/accounts.py` — четыре идентификатора пути через тот же псевдоним (состояние синхронизации, повтор синхронизации, синхронизация групп, удаление аккаунта).
- `app/pages/ads.py` — `ads_edit` и `ads_update` объявляют `ad_id` через `IdPath`; признак раскрытого расписания получил ОБЕ границы с записанной находкой; удаление объявления второго псевдонима НЕ получило.
- `app/pages/history.py` — `history_detail` и `history_retry` объявляют `log_id` через `IdPath`.
- `tests/test_pages/test_identifier_bounds.py` — матрица на семнадцать входов, три правила по всему перечню и правило пустого признака расписания (+445 строк).
- `tests/test_pages/test_htmx_gates.py` — девять записей реестра, `VALIDATION_REFUSAL_DIVERGENCES_DECLARED = 17`, третья строка летописи (+217 строк, удалённых строк внутри блока прежних восьми записей — НОЛЬ).

## Красный ДО правки — НАБЛЮДЁН ДВАЖДЫ, А НЕ ПРЕДПОЛОЖЕН

### Красный задачи 1 (до правки сигнатур двух модулей), дословно

```
E       AssertionError: ГРАНИЦА ВЕЛИЧИНЫ ИДЕНТИФИКАТОРА СТОИ́Т НЕ НА ВСЕХ ВХОДАХ. Несогласных строк 35 из 36:
E           app/pages/account_groups.py::GET /accounts/{account_id}/groups → адрес account_id ← 2147483648 = 302 (ожидалось 422; GET /accounts/2147483648/groups)
E           app/pages/account_groups.py::GET /accounts/{account_id}/groups → адрес account_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /accounts/99999999999999999999999999/groups)
E           app/pages/account_groups.py::GET /accounts/{account_id}/groups → адрес account_id ← 0 = 302 (ожидалось 422; GET /accounts/0/groups)
E           app/pages/account_groups.py::GET /accounts/{account_id}/groups/partial → адрес account_id ← 2147483648 = 302 (ожидалось 422; GET /accounts/2147483648/groups/partial)
E           app/pages/account_groups.py::GET /accounts/{account_id}/groups/partial → адрес account_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /accounts/99999999999999999999999999/groups/partial)
E           app/pages/account_groups.py::GET /accounts/{account_id}/groups/partial → адрес account_id ← 0 = 302 (ожидалось 422; GET /accounts/0/groups/partial)
E           app/pages/account_groups.py::GET /accounts/{account_id}/groups/partial → запрос after_id ← 2147483648 = 200 (ожидалось 422; GET /accounts/1/groups/partial?after_id=2147483648)
E           app/pages/account_groups.py::GET /accounts/{account_id}/groups/partial → запрос after_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /accounts/1/groups/partial?after_id=99999999999999999999999999)
E           app/pages/account_groups.py::GET /accounts/{account_id}/groups/sync-status → адрес account_id ← 2147483648 = 200 (ожидалось 422; GET /accounts/2147483648/groups/sync-status)
E           app/pages/account_groups.py::GET /accounts/{account_id}/groups/sync-status → адрес account_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /accounts/99999999999999999999999999/groups/sync-status)
E           app/pages/account_groups.py::GET /accounts/{account_id}/groups/sync-status → адрес account_id ← 0 = 200 (ожидалось 422; GET /accounts/0/groups/sync-status)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес account_id ← 2147483648 = 302 (ожидалось 422; POST /accounts/2147483648/groups/1/toggle)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес account_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /accounts/99999999999999999999999999/groups/1/toggle)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес account_id ← 0 = 302 (ожидалось 422; POST /accounts/0/groups/1/toggle)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес group_id ← 2147483648 = 302 (ожидалось 422; POST /accounts/1/groups/2147483648/toggle)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес group_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /accounts/1/groups/99999999999999999999999999/toggle)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес group_id ← 0 = 302 (ожидалось 422; POST /accounts/1/groups/0/toggle)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес account_id ← 2147483648 = 302 (ожидалось 422; POST /accounts/2147483648/groups/1/delete)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес account_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /accounts/99999999999999999999999999/groups/1/delete)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес account_id ← 0 = 302 (ожидалось 422; POST /accounts/0/groups/1/delete)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес group_id ← 2147483648 = 302 (ожидалось 422; POST /accounts/1/groups/2147483648/delete)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес group_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /accounts/1/groups/99999999999999999999999999/delete)
E           app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес group_id ← 0 = 302 (ожидалось 422; POST /accounts/1/groups/0/delete)
E           app/pages/accounts.py::GET /accounts/{account_id}/sync-status → адрес account_id ← 2147483648 = 200 (ожидалось 422; GET /accounts/2147483648/sync-status)
E           app/pages/accounts.py::GET /accounts/{account_id}/sync-status → адрес account_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /accounts/99999999999999999999999999/sync-status)
E           app/pages/accounts.py::GET /accounts/{account_id}/sync-status → адрес account_id ← 0 = 200 (ожидалось 422; GET /accounts/0/sync-status)
E           app/pages/accounts.py::POST /accounts/{account_id}/retry-sync → адрес account_id ← 2147483648 = 302 (ожидалось 422; POST /accounts/2147483648/retry-sync)
E           app/pages/accounts.py::POST /accounts/{account_id}/retry-sync → адрес account_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /accounts/99999999999999999999999999/retry-sync)
E           app/pages/accounts.py::POST /accounts/{account_id}/retry-sync → адрес account_id ← 0 = 302 (ожидалось 422; POST /accounts/0/retry-sync)
E           app/pages/accounts.py::POST /accounts/{account_id}/sync-groups → адрес account_id ← 2147483648 = 302 (ожидалось 422; POST /accounts/2147483648/sync-groups)
E           app/pages/accounts.py::POST /accounts/{account_id}/sync-groups → адрес account_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /accounts/99999999999999999999999999/sync-groups)
E           app/pages/accounts.py::POST /accounts/{account_id}/sync-groups → адрес account_id ← 0 = 302 (ожидалось 422; POST /accounts/0/sync-groups)
E           app/pages/accounts.py::POST /accounts/{account_id}/delete → адрес account_id ← 2147483648 = 302 (ожидалось 422; POST /accounts/2147483648/delete)
E           app/pages/accounts.py::POST /accounts/{account_id}/delete → адрес account_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /accounts/99999999999999999999999999/delete)
E           app/pages/accounts.py::POST /accounts/{account_id}/delete → адрес account_id ← 0 = 302 (ожидалось 422; POST /accounts/0/delete)
E
E         Величина вне диапазона колонки обязана отвергаться ДО тела обработчика на КАЖДОМ входе, а не на том, куда смотрели (`CR-01` пятого круга ревизии)
```

**Тридцать пять из тридцати шести, а не тридцать шесть, и НЕСОГЛАСНАЯ ЗДЕСЬ ОДНА СТРОКА, КОТОРАЯ БЫЛА ЗЕЛЁНОЙ.** Курсор постраничного вывода на величине `0` уже отвечал `422` — у него с плана 09-13 стояла НИЖНЯЯ граница (`Query(None, ge=1)`). Это замер, а не совпадение: настоящий план добавил ему только ВЕРХНЮЮ. Красный, покрасневший бы во всех 36 строках, означал бы, что нижняя граница исчезла.

Причина `500` снята из журнала того же прогона и названа поимённо: `OverflowError: Python int too large to convert to SQLite INTEGER`, `app/pages/account_groups.py:123` (`_load_owned_account` → `await db.execute(...)`), пойманный собственной прослойкой проекта `app/middleware.py:27`.

### Красный задачи 2 (до правки сигнатур редактора и журнала), дословно

```
E       AssertionError: ГРАНИЦА ВЕЛИЧИНЫ ИДЕНТИФИКАТОРА СТОИ́Т НЕ НА ВСЕХ ВХОДАХ. Несогласных строк 15 из 51:
E           app/pages/ads.py::GET /ads/{ad_id}/edit → адрес ad_id ← 2147483648 = 302 (ожидалось 422; GET /ads/2147483648/edit)
E           app/pages/ads.py::GET /ads/{ad_id}/edit → адрес ad_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /ads/99999999999999999999999999/edit)
E           app/pages/ads.py::GET /ads/{ad_id}/edit → адрес ad_id ← 0 = 302 (ожидалось 422; GET /ads/0/edit)
E           app/pages/ads.py::GET /ads/{ad_id}/edit → запрос sched ← 2147483648 = 200 (ожидалось 422; GET /ads/1/edit?sched=2147483648)
E           app/pages/ads.py::GET /ads/{ad_id}/edit → запрос sched ← 99999999999999999999999999 = 200 (ожидалось 422; GET /ads/1/edit?sched=99999999999999999999999999)
E           app/pages/ads.py::GET /ads/{ad_id}/edit → запрос sched ← 0 = 200 (ожидалось 422; GET /ads/1/edit?sched=0)
E           app/pages/ads.py::POST /ads/{ad_id}/edit → адрес ad_id ← 2147483648 = 302 (ожидалось 422; POST /ads/2147483648/edit)
E           app/pages/ads.py::POST /ads/{ad_id}/edit → адрес ad_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /ads/99999999999999999999999999/edit)
E           app/pages/ads.py::POST /ads/{ad_id}/edit → адрес ad_id ← 0 = 302 (ожидалось 422; POST /ads/0/edit)
E           app/pages/history.py::GET /history/{log_id} → адрес log_id ← 2147483648 = 302 (ожидалось 422; GET /history/2147483648)
E           app/pages/history.py::GET /history/{log_id} → адрес log_id ← 99999999999999999999999999 = 500 (ожидалось 422; GET /history/99999999999999999999999999)
E           app/pages/history.py::GET /history/{log_id} → адрес log_id ← 0 = 302 (ожидалось 422; GET /history/0)
E           app/pages/history.py::POST /history/{log_id}/retry → адрес log_id ← 2147483648 = 302 (ожидалось 422; POST /history/2147483648/retry)
E           app/pages/history.py::POST /history/{log_id}/retry → адрес log_id ← 99999999999999999999999999 = 500 (ожидалось 422; POST /history/99999999999999999999999999/retry)
E           app/pages/history.py::POST /history/{log_id}/retry → адрес log_id ← 0 = 302 (ожидалось 422; POST /history/0/retry)
E
E         Величина вне диапазона колонки обязана отвергаться ДО тела обработчика на КАЖДОМ входе, а не на том, куда смотрели (`CR-01` пятого круга ревизии)
```

Пятнадцать несогласных из пятидесяти одной — ровно пять новых входов на три величины; тридцать шесть строк задачи 1 остались зелёными, то есть правка задачи 1 не откатилась и не была вытеснена.

## НАХОДКА: признак раскрытого расписания до сравнения по колонке НЕ ДОЕЗЖАЕТ

Прослеживание сделано, а не пропущено, и результат назван прямо. Параметр `sched` уходит в `_editor_context` под именем `selected_schedule_id` и сличается там с УЖЕ ЗАГРУЖЕННЫМ составом расписаний объявления В ПАМЯТИ:

```python
expanded_id = selected_schedule_id
if expanded_id is not None and expanded_id not in {s.id for s in schedules}:
    expanded_id = None
```

Операндом сравнения SQL он НЕ СТАНОВИТСЯ ни на одной ветке. Красный это подтвердил ЗАМЕРОМ, а не рассуждением: величина в двадцать шесть девяток дала `200`, а не `500`, — то есть до драйвера действительно не доехала (сравните с соседним курсором, который на той же величине дал `500`).

**Параметр закрыт ВСЁ РАВНО, и основание другое:** он объявлен ИДЕНТИФИКАТОРОМ РАСПИСАНИЯ, а идентификаторы этого проекта лежат в диапазоне колонки (`app/models/schedule.py` — тот же `Mapped[int]` без указания расширенной разрядности). То есть он закрыт по ОБЪЯВЛЕННОМУ ПРЕДМЕТУ, а не по прослеженному пути, и разница записана прямо у самого параметра. Молчаливое закрытие «на всякий случай» было бы записью шире дерева.

## Замеры, которых требуют критерии приёмки

### Число закрытых параметров ПУТИ — снято разбором сигнатур, а не сложено в уме

```
app/pages/account_groups.py → 7 ['account_groups_delete(account_id)', 'account_groups_delete(group_id)',
                                 'account_groups_page(account_id)', 'account_groups_partial(account_id)',
                                 'account_groups_sync_status(account_id)', 'account_groups_toggle(account_id)',
                                 'account_groups_toggle(group_id)']
app/pages/accounts.py       → 4 ['accounts_delete(account_id)', 'accounts_retry_sync(account_id)',
                                 'accounts_sync_groups(account_id)', 'accounts_sync_status(account_id)']
app/pages/ads.py            → 3 ['ads_delete(ad_id)', 'ads_edit(ad_id)', 'ads_update(ad_id)']
app/pages/history.py        → 2 ['history_detail(log_id)', 'history_retry(log_id)']
```

Задача 1 закрыла **11** (7 + 4), задача 2 — **4** (2 в `ads.py` + 2 в `history.py`). Третий параметр `ads.py` — `ads_delete(ad_id)` — закрыт планом 10-24 и настоящим планом не трогался. Итого закрыто планом **15 идентификаторов пути** и **2 параметра запроса**.

### Удаление объявления закрыто РОВНО ОДИН раз

Разбор сигнатуры `ads_delete`:

```
  request  → Name(id='Request', ctx=Load())
  ad_id    → Name(id='IdPath', ctx=Load())
  db       → Name(id='AsyncSession', ctx=Load())
  settings → Name(id='Settings', ctx=Load())
```

Ровно одна аннотация, и она общая (`IdPath`). Второй псевдоним на одном параметре был бы невидим при чтении и виден только замером.

### Матрица: сколько строк на маршрут с двумя идентификаторами

```
входов матрицы: 17
строк отказа (входы × величины вне диапазона): 51
проверок смежности НА границе: 17
проверок смежности ВЫШЕ границы на единицу: 17
прогонов живой величины: 17

  app/pages/account_groups.py: 8
  app/pages/accounts.py: 4
  app/pages/ads.py: 3
  app/pages/history.py: 2

маршруты с ДВУМЯ входами:
  app/pages/account_groups.py::GET /accounts/{account_id}/groups/partial: 2
  app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete: 2
  app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle: 2
  app/pages/ads.py::GET /ads/{ad_id}/edit: 2

входов по способу передачи:
  адрес: 15
  запрос: 2
  POST-входов: 9
  GET-входов: 8
```

Маршруты тумблера и удаления группы несут **по две** строки матрицы каждый — критерий приёмки требовал именно этого числа. Постраничный вывод и редактор объявления тоже несут по две, но у них второй вход есть ПАРАМЕТР ЗАПРОСА, а не второй идентификатор адреса.

### Антивакуум и смежность: три числа равны

Входов **17**, прогнанных живых величин **17**, проверок смежности **17 на границе** и **17 на границе плюс единица** (последние — часть 51 строки отказа). Каждая живая величина посеяна ЗАНОВО: четыре входа перечня необратимы (удаление аккаунта, удаление группы), и общий посев сделал бы исход зависимым от ПОРЯДКА перечня.

### Тела обработчиков не правились

Дифф относительно базы плана (`e9a32ad`), по каждому файлу:

```
app/pages/account_groups.py: всего 26 | сигнатуры 16 | импорт 1 | строки основания 9 | ОСТАЛЬНОЕ 0
app/pages/accounts.py:       всего  9 | сигнатуры  8 | импорт 1 | строки основания 0 | ОСТАЛЬНОЕ 0
app/pages/ads.py:            всего 30 | сигнатуры  6 | импорт 2 | строки основания 22 | ОСТАЛЬНОЕ 0
app/pages/history.py:        всего  5 | сигнатуры  4 | импорт 1 | строки основания 0 | ОСТАЛЬНОЕ 0
```

Изменённых строк вне сигнатур, импортов и строк основания — **ноль по каждому из четырёх файлов**.

### Внутриплановый долг правила полноты — назван числом и поимённо на каждом шаге

**После задачи 1 — семь жалоб, все семь есть POST-входы ДВУХ модулей задачи 1:**

```
жалоб правила полноты: 7
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес account_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес group_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес account_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес group_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/accounts.py::POST /accounts/{account_id}/delete → адрес account_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/accounts.py::POST /accounts/{account_id}/retry-sync → адрес account_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/accounts.py::POST /accounts/{account_id}/sync-groups → адрес account_id (псевдоним IdPath)
```

Ни одной жалобы иного вида: восьмая запись, заведённая планом 10-24, не задета. Долг закрывает задача 3 ЭТОГО ЖЕ плана.

**После задачи 2 — девять жалоб**, те же семь плюс `app/pages/ads.py::POST /ads/{ad_id}/edit → адрес ad_id` и `app/pages/history.py::POST /history/{log_id}/retry → адрес log_id`.

**Разность: 9 − 7 = 2, и она РАВНА числу новых POST-входов, ограниченных задачей 2** (правка объявления и повтор отправки; остальные три входа задачи 2 стоят на GET-маршрутах и в предмет реестра не входят). Эта же разность вошла в рост числа реестра.

### Реестр: число поставлено прогоном ПОКРАСНЕВШЕГО правила

Дословно, до сдвига числа (записи уже вписаны, объявленное число ещё `8`):

```
E       AssertionError: расхождений формы отказа валидации стало 17, а объявлено 8. Рост означает, что расхождение приняли, не назвав его решением; падение — что расхождение сняли, не тронув границы, то есть объявили инвариант исполненным при неизменившемся коде
E       assert 17 == 8
```

### Зубы правила полноты показаны на ДЕВЯТИ новых входах

Перечню подана укороченная копия без девяти новых записей; боевой перечень не правился ни на символ:

```
перечень укорочен до 8 записей — снято девять новых
жалоб правила полноты: 9
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес account_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/delete → адрес group_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес account_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/account_groups.py::POST /accounts/{account_id}/groups/{group_id}/toggle → адрес group_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/accounts.py::POST /accounts/{account_id}/delete → адрес account_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/accounts.py::POST /accounts/{account_id}/retry-sync → адрес account_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/accounts.py::POST /accounts/{account_id}/sync-groups → адрес account_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/ads.py::POST /ads/{ad_id}/edit → адрес ad_id (псевдоним IdPath)
НАЙДЕН ЗАМЕРОМ, НО НЕ ОБЪЯВЛЕН: app/pages/history.py::POST /history/{log_id}/retry → адрес log_id (псевдоним IdPath)

на БОЕВОМ перечне жалоб: 0
```

### Таблица «вход → путь разметки → строка», девять строк

| Вход (ключ реестра) | Путь разметки | Строка | Сегмент адреса / источник величины |
|---|---|---|---|
| `account_groups.py::POST …/toggle → адрес account_id` | `app/templates/account_groups/includes/group_row.html` | `193` | первый сегмент; из КОНТЕКСТА ЭКРАНА |
| `account_groups.py::POST …/toggle → адрес group_id` | `app/templates/account_groups/includes/group_row.html` | `193` | третий сегмент; из ОТРИСОВАННОЙ СТРОКИ (`group.id`) |
| `account_groups.py::POST …/delete → адрес account_id` | `app/templates/account_groups/includes/group_row.html` | `234` и `370` | первый сегмент; из контекста экрана |
| `account_groups.py::POST …/delete → адрес group_id` | `app/templates/account_groups/includes/group_row.html` | `234` и `370` | третий сегмент; из отрисованной строки |
| `accounts.py::POST /accounts/{id}/delete → адрес account_id` | `app/templates/accounts/partial_cards.html` | `59`, `87`, `116`, `138` | из `account.id` живой строки |
| `accounts.py::POST /accounts/{id}/retry-sync → адрес account_id` | `app/templates/accounts/partial_cards.html` | `84` | из `account.id`; форма показывается только в состоянии `sync_failed` |
| `accounts.py::POST /accounts/{id}/sync-groups → адрес account_id` | `app/templates/account_groups/list.html` | `85` | из `account_id` контекста ЭКРАНА ГРУПП — разметка НЕ в каталоге своего обработчика |
| `ads.py::POST /ads/{id}/edit → адрес ad_id` | `app/templates/ads/form.html` | `71` и `72` | `action` и `hx-post` формы редактора, одно выражение с `ad.id` |
| `history.py::POST /history/{id}/retry → адрес log_id` | `app/templates/history/includes/history_card.html` | `162` и `175` | форма-триггер и `action` панели подтверждения, из `log_id` записи |

**Достижимость из интерфейса измерена: НУЛЕВАЯ у всех ДЕВЯТИ, отличной от нулевой — НИ ОДНОЙ.** Каждая величина собирается СЕРВЕРОМ из живой строки либо из контекста экрана; редактируемого поля, из которого она приезжала бы, в разметке нет ни у одного входа.

**⚠️ ДВЕ ПАРЫ СТРОК ТАБЛИЦЫ ДЕЛЯТ ПУТЬ СО СТРОКОЙ, И ЭТО ЗАМЕР, А НЕ КОПИЯ.** См. раздел «Deviations», п. 4: критерий приёмки требовал таблицы БЕЗ повторов пути со строкой; у маршрутов с двумя идентификаторами адрес ОДИН, поэтому оба их идентификатора физически стоят в одной строке разметки. Различие между такими входами измерено ИСТОЧНИКОМ величины (контекст экрана против отрисованной строки) и СЕГМЕНТОМ адреса — и записано именно так, а не выдумано ради непохожести.

### Граница наблюдения названа честно (повторяется для обеих задач)

Все замеры выше наблюдают отказ **НА ГРАНИЦЕ ПРИЛОЖЕНИЯ**, до драйвера, и от драйвера не зависят. Поведения боевого PostgreSQL на НЕОГРАНИЧЕННОМ входе они не наблюдают: у суиты драйвер один (`sqlite+aiosqlite:///:memory:`). Это остаётся предметом **окна 39**, и оно ОТКРЫТО.

## Decisions Made

См. `key-decisions` во frontmatter. Дополнительно к ним:

- **Посев выбирает ВЕТКУ, а не подменяет модуль.** Аккаунт посеян типом `tg_user` в состоянии `syncing`, запись журнала — успешной. Это уводит `sync-groups`, `retry-sync` и `retry` в детерминированную ветку ДО обращения к мессенджеру и к брокеру очереди, то есть без подмены `sys.modules` и без сетевого вызова. Основание записано у самого посева, а не оставлено читателю: предмет антивакуума — ДОПУЩЕНА ли живая величина границей, и он наблюдается полностью; что тело делает дальше, наблюдают собственные суиты этих модулей (`tests/test_routes/test_sync_groups.py`, `tests/test_pages/test_history_retry.py` и прочие — прогнаны, зелены).
- **Удаления объявления в матрице НЕТ.** Оно закрыто планом 10-24 и проведено насквозь собственными правилами того же модуля суиты. Вторая строка матрицы на тот же вход не добавила бы ни одного наблюдения и увела бы счёт входов плана.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Команда `<verify>` задачи 1 целилась в несуществующий модуль суиты**

- **Найдено при:** Задача 1, прогон верификации
- **Проблема:** `uv run pytest tests/test_pages/test_account_groups.py tests/test_pages/test_accounts.py -q` → `ERROR: file or directory not found: tests/test_pages/test_accounts.py`. Модуля с таким именем в дереве НЕТ. Команда, оставленная как есть, дала бы `ненулевой код возврата` по причине, не имеющей отношения к предмету, а исправленная «убиранием несуществующего пути» измерила бы ПОЛОВИНУ объявленного предмета — правила `app/pages/accounts.py` остались бы непроверенными.
- **Исправление:** состав измерен, а не угадан: найдены ВСЕ модули суиты, обращающиеся к маршрутам `app/pages/accounts.py`, и прогнаны `tests/test_pages/test_account_groups.py`, `tests/test_routes/test_accounts.py`, `tests/test_routes/test_sync_groups.py`, `tests/test_routes/test_wa_sync_status.py`, `tests/test_application/test_account_deletion_schedules.py`, `tests/test_pages/test_origin_guard_on_destructive_routes.py`, `tests/test_pages/test_confirm_delete_transport.py` → **258 passed** (4:06).
- **Проверка:** зелёный прогон; предмет объявленной команды покрыт полностью и с запасом.
- **Коммит:** `8877135` (задача 1) — правки кода не потребовалось, изменилась только команда замера.

**2. [Rule 3 - Blocking] Команда `<verify>` задачи 2 целилась в несуществующий модуль суиты**

- **Найдено при:** Задача 2, прогон верификации
- **Проблема:** `tests/test_pages/test_ads.py` в дереве НЕТ (тот же класс дефекта, что и в п. 1).
- **Исправление:** прогнаны `tests/test_pages/test_ads_editor.py`, `test_ads_status.py`, `test_ads_image_ownership.py`, `test_history.py`, `test_history_retry.py`, `test_history_export.py` → **243 passed** (3:38).
- **Проверка:** зелёный прогон.
- **Коммит:** `caa5e10` (задача 2).

**3. [Rule 1 - Bug] Внутриплановый долг правила полноты краснит ДВА узла, а план снимал ОДИН**

- **Найдено при:** Задача 1, широкий прогон `tests/test_pages/`
- **Проблема:** план снимал ровно `test_every_framework_bounded_input_is_declared_as_a_divergence`, называя это «красным ПО ПОСТРОЕНИЮ». Замер показал, что тот же долг несёт ВТОРОЙ узел — `test_control_a_shortened_exception_list_reddens_the_completeness_rule`: его последнее утверждение (защита от протечки подмены) сличает БОЕВОЙ перечень с замером и потому краснеет ровно тогда же. Широкий прогон задачи 1 дал `1 failed, 1532 passed` вместо ожидаемого зелёного.
- **Исправление:** ничего не «чинилось» подгонкой — предмет измерен отдельной командой владения жалобами (см. раздел выше), а закрытие проверено ПРОГОНОМ: после задачи 3 `tests/test_pages/test_htmx_gates.py` целиком → **35 passed**, и полная суита `tests/ -m "not planning"` → **2854 passed, 28 deselected**, rc=0. Оба узла зелены.
- **Проверка:** прогон полной суиты, rc=0.
- **Коммит:** `8c745df` (задача 3).

**4. [Rule 1 - Bug] Критерий приёмки задачи 3 требовал таблицы БЕЗ повторов «путь + строка», а замер такой таблицы не даёт**

- **Найдено при:** Задача 3, сбор обоснований
- **Проблема:** маршруты тумблера и удаления группы несут по ДВА ограниченных идентификатора, но АДРЕС у маршрута один — оба идентификатора стоят в ОДНОЙ строке разметки (`group_row.html:193` у тумблера, `:234`/`:370` у удаления). Удовлетворить критерий буквально можно было бы только назначив каждой записи «свою» строку — то есть записав в реестр различие, которого в дереве нет.
- **Исправление:** записан ЗАМЕР, а не выдумка. Обоснования этих пар называют разные СЕГМЕНТЫ одного адреса и разный ИСТОЧНИК величины (идентификатор аккаунта приходит из контекста ЭКРАНА, идентификатор группы — из ОТРИСОВАННОЙ СТРОКИ), и у самого блока записей стои́т абзац, объясняющий, почему строка у пары общая ПО ПОСТРОЕНИЮ. В таблицу сводки добавлена колонка «сегмент адреса / источник величины», а расхождение с критерием названо здесь.
- **Проверка:** правило обоснований зелено (`test_every_validation_refusal_divergence_carries_a_non_empty_rationale`); девять обоснований различны и ни одно не повторяет другого.
- **Коммит:** `8c745df` (задача 3).

**5. [Rule 3 - Blocking] Широкий прогон `tests/test_pages/` задачи 2 объединён с финальным прогоном полной суиты**

- **Найдено при:** Задача 2, планирование прогонов
- **Проблема:** широкий прогон `tests/test_pages/` занимает ~30 минут, и его ЕДИНСТВЕННЫМ ожидаемым отказом на задаче 2 был тот же внутриплановый долг, уже измеренный отдельной командой с проверкой владения каждой жалобой (9 жалоб, все из четырёх модулей плана).
- **Исправление:** прогон задачи 2 объединён с финальным `uv run pytest tests/ -q -m "not planning"`, который покрывает `tests/test_pages/` ЦЕЛИКОМ и БЕЗ снятий, то есть измеряет строго больше. Результат: **2854 passed, 28 deselected** за 35:24, rc=0.
- **Проверка:** rc=0 полной суиты; ни один узел не снят.
- **Коммит:** `caa5e10` / `8c745df`.

---

**Total deviations:** 5 auto-fixed (2 блокирующих — несуществующие цели команд замера; 2 дефекта записи плана, найденные замером; 1 объединение прогонов).
**Impact on plan:** предмет плана не менялся ни на шаг. Два исправления вернули замеру предмет, который команды плана потеряли (несуществующие модули); два записали то, что замер показал вопреки тексту плана (второй узел долга; общая строка разметки у пары входов); одно сократило дублирующий прогон в пользу строго более широкого. Расширения объёма нет.

## Issues Encountered

- **`-p no:logging` в широком прогоне ломает два правила, которым нужен `caplog`.** На первом широком прогоне `tests/test_pages/` появились две ошибки `fixture 'caplog' not found` в `tests/test_pages/test_blocked_user.py`. Причина — МОЙ флаг `-p no:logging`, которым я глушил журнальный шум: он снимает плагин, дающий `caplog`. Проверено прогоном того же модуля без флага → **20 passed**. Дефекта в дереве нет; флаг из широких прогонов убран, финальная суита прогнана без него.
- Иных проблем не было. Гейтов аутентификации не возникало.

## User Setup Required

None — внешней конфигурации не требуется.

## Next Phase Readiness

- **Готово для плана 10-29** (административный модуль): форма закрытия входа доказана на четырёх продуктовых модулях, матрица расширяется дописыванием записи `_BoundedEntry`, а не переизобретением правил. Объявленное число реестра расхождения сдвинется 17 → 23 — предупреждение об этом стои́т в летописи числа.
- **Готово для плана 10-30** (гейт полноты границы по всему каталогу страничного слоя): гейт заводится ПОСЛЕ того, как закрыт админский модуль, иначе он краснел бы по построению всю волну 3.
- **Открытым остаётся окно 39** — поведение боевого драйвера на неограниченном входе. План сделал вопрос МЕНЕЕ важным (отказ ставится до драйвера на семнадцати входах вместо одного), но не ответил на него: второго драйвера у суиты нет.
- **Ждёт владельца решение о законности расхождения** формы отказа валидации с запертым D-01 на семнадцати входах реестра. План его не чеканит и чеканить не вправе; правило авторства машинно не даёт превратить «ЖДЁТ ВЛАДЕЛЬЦА» в «решено» без ссылки на `D-NN` либо закрытое окно.

---
*Phase: 10-rychag-components-modal-html*
*Completed: 2026-09-08*
