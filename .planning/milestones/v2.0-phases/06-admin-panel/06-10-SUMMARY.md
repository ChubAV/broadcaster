---
phase: 06-admin-panel
plan: 10
subsystem: ui
tags: [admin, overview, incidents, analytics, jinja2, sqlalchemy, tdd]

requires:
  - phase: 06-admin-panel
    plan: 04
    provides: "Пять признаков инцидента, их условия снятия, адреса «куда чинить», порядок и потолок; контракт входа живости ЗНАЧЕНИЯМИ (WorkerLiveness)"
  - phase: 06-admin-panel
    plan: 07
    provides: "app/services/ops_state.queue_page / telegram_queue_depth; telegram_lag_seconds и подпись величины времени канала брокера в queue.html"
  - phase: 06-admin-panel
    plan: 09
    provides: "app/application/admin/users_query.py и страничный модуль админки в редакции подраздела «Пользователи»"
  - phase: 04-dashbord-i-istoriya
    provides: "Модуль аналитики отправок как ЕДИНСТВЕННОЕ место агрегаций журнала (D-35); send_metrics с восемью числами одним round-trip"
  - phase: 05.1-ploskaya-podpiska
    provides: "access_axis_clause и перевод правила доступа в язык запроса на стороне слоя данных"
provides:
  - "send_metrics с областью счёта параметром: user_id=None считает по всему сервису (D-39), параметр остаётся обязательным"
  - "last_send_at — момент последней отправки по каналу как агрегат журнала внутри модуля аналитики"
  - "app/application/admin/overview_stats.py — люди, платящие, выручка, счета карточки и колонки списка"
  - "paying_subscription_clauses — три условия платящей подписки одним объявлением в слое данных"
  - "app/templates/admin/includes/queue_time.html — величина времени очереди ОДНИМ определением на «Очередь» и «Обзор»"
  - "app/templates/admin/includes/incident_row.html — строка инцидента с подписью вида, тоном и переходом «Чинить →»"
  - "Машинный свидетель: страничный модуль админки не строит агрегирующих выражений вовсе"
affects: [06-11-payments, 06-14-mobile-acceptance]

actuals:
  # 113 615 символов реализованного диффа / 4. Шкала та же, что у `estimate`
  # плана (70 000), и это НЕ счётчик токенов раннера. Значение не подтянуто к
  # оценке: план ПЕРЕоценил объём вдвое с лишним, и записать это надо честно.
  # Причина переоценки видна задним числом: две из трёх задач легли на уже
  # существующие формы (модуль аналитики умел считать оба окна одним запросом,
  # модуль признаков отдавал готовый к показу блок), и изобретать пришлось
  # только переходник живости и раскладку строки инцидента.
  tokens: 28400
  tasks: 3
  commits: 6

tech-stack:
  added: []
  patterns:
    - "Область счёта поднимается до параметра модуля, а не дублируется второй функцией рядом; параметр при этом остаётся ОБЯЗАТЕЛЬНЫМ — умолчание сделало бы общесистемную выдачу достижимой по забывчивости"
    - "Запрет второй агрегации переведён из правила для человека в свойство кода: страничный модуль не импортирует конструктор SQL-функций вовсе"
    - "Копирайт, обязанный совпасть на двух поверхностях, живёт ОДНИМ макросом, а не двумя одинаковыми строками"
    - "Переходник между формой сервиса и формой прикладного модуля пишется у ПОТРЕБИТЕЛЯ — так суита прикладного модуля остаётся без внешних служб"
    - "Сумма по нескольким источникам равна None, если хотя бы один не прочитан: частичная сумма выглядит измеренной, ею не будучи"

key-files:
  created:
    - app/application/admin/overview_stats.py
    - app/templates/admin/includes/incident_row.html
    - app/templates/admin/includes/queue_time.html
    - tests/test_application/test_admin_uses_analytics.py
  modified:
    - app/application/analytics/send_analytics.py
    - app/repositories/user.py
    - app/pages/admin.py
    - app/templates/admin/overview.html
    - app/templates/admin/queue.html
    - app/static/css/app.css
    - tests/test_pages/test_admin_panel.py
    - .planning/WINDOWS.md

key-decisions:
  - "Область счёта у send_metrics — обязательный keyword типа int | None, а НЕ `= None`: расширение не имеет права сделать общесистемную выдачу достижимой по забывчивости (T-04-01)"
  - "Из app/pages/admin.py вынесены ВСЕ агрегаты, а не только счёт отправок: свойство «модуль не импортирует func» проверяемо, а «модуль не заводит второй счёт отправок» — нет"
  - "Три условия платящей подписки объявлены в app/repositories/user.py, а не в прикладном модуле: признак льготы читает в app/application ровно один файл, и это машинный гейт проекта"
  - "Подпись величины времени очереди вынесена в общий макрос: байт-в-байт совпадение двух поверхностей держится структурой, а не дисциплиной"
  - "Адрес вида failure_spike НЕ переопределён вопреки сомнению: D-48 предписывает «Историю с фильтром» буквально, и молчаливая подмена адреса была бы отменой решения владельца исполнителем"

patterns-established:
  - "Слово в подписи, выведенное из константы («за неделю» ← timedelta(days=7)), закрепляется тестом на равенство: число в копирайт не копируется, но и слово не имеет права разойтись с ним"
  - "Утверждение о существовании адреса проверяется против МНОЖЕСТВА ЖИВЫХ МАРШРУТОВ приложения, а не против объявления, из которого адрес взят"
  - "Отсчёт в интеграционном тесте берётся ДО посева, а не выписывается числом: вписанная константа проверяла бы состав фикстуры, а не правило отбора"

requirements-completed: [ADMIN-03, ADMIN-11]

coverage:
  - id: D1
    description: "Общесистемный счёт отправок живёт ВНУТРИ модуля аналитики; пользовательский контракт не изменился ни одним полем"
    requirement: ADMIN-03
    verification:
      - kind: unit
        ref: "tests/test_application/test_admin_uses_analytics.py#test_the_systemwide_count_sums_every_user"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_admin_uses_analytics.py#test_the_single_user_contract_is_unchanged_by_the_generalisation"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_admin_uses_analytics.py#test_the_systemwide_count_keeps_the_single_round_trip"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_admin_uses_analytics.py#test_the_previous_window_covers_the_same_users_as_the_current_one"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_admin_uses_analytics.py#test_an_empty_journal_gives_zeroes_and_not_an_exception"
        status: pass
    human_judgment: false
  - id: D2
    description: "Изоляция по владельцу пережила обобщение: область счёта нельзя опустить по забывчивости (T-04-01)"
    requirement: ADMIN-03
    verification:
      - kind: unit
        ref: "tests/test_application/test_admin_uses_analytics.py#test_the_owner_of_a_summary_cannot_be_omitted_by_accident"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_other_users_records_are_invisible"
        status: pass
    human_judgment: false
  - id: D3
    description: "Второй агрегации в страничном модуле админки нет, и «Обзор» зовёт модуль аналитики — разбором синтаксического дерева"
    requirement: ADMIN-03
    verification:
      - kind: unit
        ref: "tests/test_application/test_admin_uses_analytics.py#test_the_admin_pages_module_builds_no_aggregate_over_the_send_journal"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_admin_uses_analytics.py#test_the_overview_handler_calls_the_analytics_module"
        status: pass
      - kind: unit
        ref: "grep -Ec 'func\\.count|func\\.sum' app/pages/admin.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "Плитка платящих считается БЕЗ льготных: три условия, а не два (D-38), и выручка считается по тому же числу"
    requirement: ADMIN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_overview_paying_tile_leaves_the_comped_user_out"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_overview_revenue_caption_is_the_payers_times_the_price"
        status: pass
    human_judgment: false
  - id: D5
    description: "Показатель ошибок берётся за скользящие сутки, дельта приезжает тем же обращением, и число совпадает с дашбордом пользователя (D-40)"
    requirement: ADMIN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_overview_errors_tile_takes_the_rolling_day_and_its_delta"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_overview_error_number_matches_the_users_own_dashboard"
        status: pass
    human_judgment: false
  - id: D6
    description: "Плитка задач суммирует три источника; недоступный Redis даёт прочерк с названной причиной, а не ноль"
    requirement: ADMIN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_overview_queue_tile_sums_the_three_sources"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_overview_queue_tile_says_unknown_and_not_zero_when_redis_is_down"
        status: pass
    human_judgment: false
  - id: D7
    description: "«Обзор» и «Очередь» называют одно число одними словами — сравнение ДОСЛОВНОЕ"
    requirement: ADMIN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_overview_names_the_queue_time_exactly_as_the_queue_subsection_does"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_telegram_queue_block_names_exactly_what_its_number_measures"
        status: pass
    human_judgment: false
  - id: D8
    description: "Блок инцидентов печатает только сломанное сейчас: пустое состояние валидно, порядок по свежести, потолок называет себя, строк о возврате в строй нет (D-44, D-46)"
    requirement: ADMIN-11
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_incident_board_says_nothing_is_broken_when_nothing_is"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_incident_rows_come_freshest_first"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_a_capped_incident_board_names_its_own_ceiling"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_incident_board_carries_no_recovery_rows"
        status: pass
    human_judgment: false
  - id: D9
    description: "Каждая строка несёт подпись вида и переход; все пять адресов ведут по маршрутам, ЖИВЫМ в приложении"
    requirement: ADMIN-11
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_a_raised_incident_prints_a_row_with_time_text_and_a_link"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_every_incident_kind_has_a_label_a_tone_and_a_living_route"
        status: pass
    human_judgment: true
    rationale: >-
      Тест доказывает, что каждому из пяти адресов соответствует ЖИВОЙ маршрут
      приложения — то есть 404 по строке инцидента невозможен. Он НЕ доказывает,
      что администратор, придя по адресу, увидит именно свой инцидент. У вида
      `failure_spike` это сомнительно и записано отдельно: адрес ведёт в раздел
      истории САМОГО администратора, а признак считает весь сервис (см. «Открытые
      вопросы» ниже и запись 2 реестра `.planning/WINDOWS.md`). Выбор между буквой
      D-48 и `/admin/logs?level=error` — решение владельца, а не исполнителя.
  - id: D10
    description: "Стык 06-04 ↔ 06-01/06-05 закрыт переходником на стороне потребителя; модуль признаков по-прежнему не знает ни одного клиента внешней службы"
    requirement: ADMIN-11
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_a_stuck_worker_incident_comes_from_the_liveness_values"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_admin_panel.py#test_the_incident_module_still_knows_no_client_of_an_external_service"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_incidents.py#test_the_module_imports_no_client_of_an_external_service"
        status: pass
    human_judgment: false
  - id: D11
    description: "Недоступный Redis не роняет «Обзор» и даёт частичную картину, НАЗВАННУЮ частичной"
    requirement: ADMIN-11
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_an_unreachable_redis_gives_a_partial_incident_board_that_says_so"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_overview_answers_two_hundred_with_an_unreachable_redis"
        status: pass
    human_judgment: false
  - id: D12
    description: "Подраздел пригоден к использованию на 375px: строка инцидента переносится, текст читается целиком, горизонтальной прокрутки нет"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_admin_no_utility_classes"
        status: pass
    human_judgment: true
    rationale: >-
      Браузерного харнесса в проекте нет. Перенос и отсутствие фиксированных
      ширин проверены арифметикой по CSS и сплошным обходом шаблонов, но
      фактическая читаемость экрана на 375px — критерий приёмки фазы, и он
      снимается глазами (план 06-14).

duration: 79 min
completed: 2026-08-23
status: complete
---

# Phase 6 Plan 10: Наполнение «Обзора» Summary

**Четыре измеренных показателя сервиса и блок текущих инцидентов со ссылкой «куда чинить» у каждой строки; запрет второй агрегации отправок переведён из правила для человека в свойство кода — страничный модуль админки больше не импортирует конструктор SQL-функций вовсе.**

## Performance

- **Duration:** 79 min
- **Started:** 2026-08-23T00:40Z
- **Completed:** 2026-08-23T01:59Z
- **Tasks:** 3
- **Files modified:** 12 (4 создано, 8 изменено)

## Accomplishments

- **Модуль аналитики научился считать по системе — внутри себя.** Область счёта поднята до параметра `send_metrics`: `user_id=None` означает «весь сервис». Восемь условных агрегатов, оба окна одним обращением и защита от пустых значений остались ОБЩИМИ, поэтому первая же правка формулы придёт на обе области сразу. Отдельная функция рядом продублировала бы всё перечисленное.
- **Изоляция по владельцу пережила обобщение.** До этого плана T-04-01 держалась на том, что ветки «все пользователи» в модуле НЕТ вовсе. Ветка появилась — и держать изоляцию теперь может ровно одно: параметр остался ОБЯЗАТЕЛЬНЫМ (`user_id: int | None` без умолчания). С `= None` вызов, у которого владельца просто забыли передать, вернул бы пользователю чужие числа и напечатал бы их на его собственном дашборде — без исключения, без пятисотки и без единого красного теста.
- **Запрет второй агрегации стал машинным.** Из `app/pages/admin.py` вынесены ВСЕ агрегаты — не только счёт отправок: люди, платящие и выручка ушли в новый `app/application/admin/overview_stats.py`, счета карточки пользователя и колонка списка — туда же, момент последней отправки по каналу — в модуль аналитики, которому он и принадлежит по D-35. Итог проверяем одной фразой: страничный модуль админки не импортирует `func`, и добавить туда агрегат нельзя, не уронив тест.
- **Четыре плитки печатают измеренное.** Люди (всего и прирост за неделю по моменту регистрации) · платящие БЕЗ льготных с подписью MRR через общий денежный глобал · задачи в очереди суммой трёх источников · ошибки за скользящие сутки с дельтой, тон которой инвертирован атрибутом от вызывающего.
- **Число ошибок «Обзора» доказанно совпадает с числом дашборда.** Не «должно совпадать» — тест сажает оба экрана на одну популяцию и сравнивает напечатанные значения. Это и есть причина, по которой окно суточное, а не часовое из макета.
- **«Обзор» и «Очередь» называют одно число одними словами**, и держится это не дисциплиной: подпись живёт ОДНИМ макросом (`admin/includes/queue_time.html`), который импортируют оба подраздела. Тест вытаскивает подпись из разметки «Очереди» регулярным выражением и ищет её ДОСЛОВНО в разметке «Обзора».
- **Блок инцидентов показывает только сломанное сейчас.** Пустое состояние говорит и «всё в порядке», и «список чистит себя сам»; потолок называет себя числом из константы модуля; строк о возврате в строй нет ни в выдаче, ни в исходниках шаблонов.
- **Стык, флагированный планом 06-04, закрыт на стороне потребителя.** Переходник от формы сервиса (`{"queue_depth": int|None, "worker": str}`) к форме модуля (`WorkerLiveness(queue_depth, heartbeat_fresh)`) написан в `app/pages/admin.py`. Модуль признаков по-прежнему не знает ни Redis, ни Docker, ни сервиса оперативного состояния — и его суита из 28 тестов по-прежнему идёт на SQLite без единой поднятой службы.
- **Недоступный Redis даёт частичную картину, НАЗВАННУЮ частичной.** Аккаунт, о котором наблюдатель не сказал ничего, из отображения выпадает, а вызывающий получает признак неполноты и печатает плашку. Подстановка «живой» спрятала бы настоящий отказ, «мёртвый» — подняла бы инцидент на исправном воркере; обе были бы догадкой, поданной как измерение.
- **26 новых тестов** (8 в новом файле, 18 в суите админ-панели), все зелёные.

## Task Commits

1. **Задача 1: общесистемный счёт и машинный свидетель** — `c673988` (test, RED) → `9b00306` (feat, GREEN)
2. **Задача 2: четыре плитки «Обзора»** — `686cd54` (test, RED) → `d4d9e19` (feat, GREEN)
3. **Задача 3: блок инцидентов** — `d88bfb5` (test, RED) → `81af9c4` (feat, GREEN)

## Files Created/Modified

- `app/application/admin/overview_stats.py` — люди, платящие, выручка, счета карточки, колонка списка (новый, 165 строк)
- `app/templates/admin/includes/incident_row.html` — строка инцидента: точка тона, время следа, подпись вида, текст, переход (новый)
- `app/templates/admin/includes/queue_time.html` — величина времени очереди ОДНИМ определением на два подраздела (новый)
- `tests/test_application/test_admin_uses_analytics.py` — восемь тестов: общесистемный счёт, инвариант пользовательского случая, разбор дерева (новый)
- `app/application/analytics/send_analytics.py` — область счёта параметром; `last_send_at`
- `app/repositories/user.py` — `paying_subscription_clauses`: три условия платящей подписки
- `app/pages/admin.py` — обработчик «Обзора», снимок оперативного состояния, переходник живости; `func` больше не импортируется
- `app/templates/admin/overview.html` — четыре плитки и блок инцидентов
- `app/templates/admin/queue.html` — подпись времени переведена на общий макрос
- `app/static/css/app.css` — атрибутные правила строки инцидента и точки тона
- `tests/test_pages/test_admin_panel.py` — 18 тестов плиток и блока
- `.planning/WINDOWS.md` — запись 2 (адрес вида `failure_spike`)

## Decisions Made

- **Область счёта — обязательный keyword `int | None`, а не `= None`.** D-39 приводил `user_id: int | None = None` ПРИМЕРОМ формы; выбрана форма без умолчания. Причина названа в докстринге функции и закреплена тестом: разница между молчаливой общесистемной выдачей и явной — ровно отсутствие умолчания.
- **Вынесены ВСЕ агрегаты страничного модуля, а не только счёт отправок.** Свойство «модуль не заводит второй счёт отправок» проверяемо только угадыванием имён; свойство «модуль не импортирует `func`» проверяется одной строкой и не зависит от фантазии автора теста. Побочно закрыт критерий плана `grep -Ec 'func\.count|func\.sum' app/pages/admin.py` = 0, который иначе не сходился бы: в модуле жили счета аккаунтов, объявлений и групп, к предмету плана отношения не имеющие.
- **Три условия платящей подписки объявлены в `app/repositories/user.py`, а не в прикладном модуле.** Первая редакция положила их в `overview_stats.py` и уронила машинный гейт проекта `test_the_free_access_flag_is_read_in_exactly_one_place_of_the_decision`: признак льготы читает в `app/application/` РОВНО ОДИН файл — предикат доступа. Прецедент дословный и записан над осью доступа админского списка: SQL-выражения по нашим таблицам — работа слоя данных, а не прикладного модуля. Ослаблять гейт ради удобной раскладки файлов нельзя.
- **Подпись величины времени вынесена в общий макрос вместо второй одинаковой строки.** Требование «байт-в-байт» дисциплиной не держится: поправили бы формулировку в одном подразделе — и администратор увидел бы на двух экранах две на вид разные величины. Порог тревожного тона (`600`) переехал туда же из литерала в разметке.
- **Адрес вида `failure_spike` НЕ переопределён.** D-48 предписывает «Историю с фильтром» буквально, и подмена адреса на `/admin/logs?level=error` была бы отменой решения владельца исполнителем. Сомнение записано, а не исполнено (см. ниже).
- **Слово «за неделю» в подписи закреплено тестом на равенство константы неделе.** Число в копирайт не копируется — значит в подписи стоит слово, и цена решения ровно одна: слово не меняется вместе с константой. Тест и есть эта цена, уплаченная вперёд.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Безопасность] Область счёта оставлена обязательным параметром вопреки букве «становится НЕОБЯЗАТЕЛЬНЫМ»**

- **Found during:** Задача 1
- **Issue:** План и D-39 описывают расширение как «идентификатор пользователя становится необязательным». Буквальная форма `user_id: int | None = None` делает общесистемную выдачу достижимой ПО ЗАБЫВЧИВОСТИ: `send_metrics(session)` вернул бы сумму по всем пользователям, и напечатал бы её пользовательский дашборд. До этого плана изоляция (T-04-01) держалась на отсутствии ветки «все пользователи»; ветка появляется, и удержать изоляцию может только обязательность параметра.
- **Fix:** `user_id: int | None` объявлен keyword-only БЕЗ умолчания. Все существующие вызовы передают владельца именем и не изменились; общесистемный вызов передаёт `None` явно.
- **Files modified:** `app/application/analytics/send_analytics.py`
- **Verification:** `test_the_owner_of_a_summary_cannot_be_omitted_by_accident`; суита модуля аналитики (60 тестов) и `tests/test_pages -k dashboard` зелёные
- **Committed in:** `9b00306`

**2. [Rule 3 - Блокер] Условия платящей подписки перенесены из прикладного модуля в слой данных**

- **Found during:** Задача 1 (прогон `tests/test_application` после первой редакции)
- **Issue:** Первая редакция объявила `paying_clauses` в `app/application/admin/overview_stats.py`. Прогон уронил машинный гейт проекта: признак `has_free_access` имеет право читать в `app/application/` ровно один файл — предикат доступа. Гейт существует затем, чтобы правило доступа не разошлось по двум выражениям.
- **Fix:** Тройка условий объявлена `paying_subscription_clauses` в `app/repositories/user.py` — там же, где живёт перевод правила доступа в язык запроса, и по той же записанной причине.
- **Files modified:** `app/repositories/user.py`, `app/application/admin/overview_stats.py`
- **Verification:** `tests/test_application` и `tests/test_repositories` — 261 зелёный
- **Committed in:** `9b00306`

**3. [Rule 2 - Устойчивость] Непригодная цена доступа не роняет «Обзор»**

- **Found during:** Задача 2
- **Issue:** Выручка считается умножением цены из настройки на число платящих. Цена хранится строкой формата платёжного API, и мусор в настройке уронил бы `Decimal(...)` исключением — то есть увёл бы весь подраздел в 500 из-за одной переменной окружения.
- **Fix:** `monthly_revenue` возвращает исходную строку как есть, если она не разбирается или не конечна. Приём и его причина дословно те же, что у `format_amount`, через который значение проходит следом: выдуманный ноль в денежной подписи — правдоподобная ложь, а исходная строка хотя бы называет себя странной.
- **Files modified:** `app/application/admin/overview_stats.py`
- **Verification:** `test_the_overview_revenue_caption_is_the_payers_times_the_price`
- **Committed in:** `d4d9e19`

### Отклонения от критериев приёмки плана

**`grep -Ec 'has_free_access' app/pages/admin.py` не меньше 1 — критерий ВЫПОЛНЯЕТСЯ (значение 3), но не тем выражением, которое имел в виду план.** Три вхождения — предсуществующие, из подраздела «Пользователи». Выражение отбора платящих в страничном модуле НЕ стоит и стоять не может: оно уронило бы машинный гейт единственного чтения признака (см. отклонение 2). Настоящее доказательство третьего условия — `test_the_overview_paying_tile_leaves_the_comped_user_out`, который сажает трёх пользователей в трёх разных состояниях и утверждает, что прибавился РОВНО ОДИН.

---

**Total deviations:** 3 auto-fixed (Rule 2 ×2, Rule 3 ×1) + 1 уточнение критерия
**Impact on plan:** Ни одно отклонение не расширяет предмет. Первые два усиливают уже действующие в проекте машинные гарантии, третье закрывает отказ, который случился бы только у пользователя.

## Issues Encountered

**`just test` не зелёный: один предсуществующий красный тест вне предмета плана.**

Полный прогон — `1 failed, 2007 passed`. Красный — `tests/test_pages/test_ads_editor.py::test_image_base_url_comes_from_app_settings`, порядковая зависимость суиты, воспроизводящаяся на базовом коммите фазы. Заведён планом 06-04 в `.planning/phases/06-admin-panel/deferred-items.md` и в реестр `.planning/WINDOWS.md` (запись 1, статус open). План его не чинит по границе предмета: ни рендера объявлений, ни настроек S3 он не трогает.

Остальные команды `<verification>` плана зелёные:
- `uv run pytest tests/test_application/test_admin_uses_analytics.py -q` — 8 passed
- `uv run pytest tests/test_application/test_incidents.py -q` — 28 passed
- `uv run pytest tests/test_pages/test_admin_panel.py -q` — 83 passed
- `uv run pytest tests/test_pages -q -k dashboard` — зелёный, пользовательский дашборд не изменился
- `uv run pytest tests/test_pages/test_responsive_markup.py tests/test_templates tests/test_application -q` — 425 passed

## Известные заглушки

Нет. Заглушек, пропущенных тестов и незапущенных проверок план не оставил.

## Открытые вопросы (решение владельца)

**Адрес вида `failure_spike` ведёт в раздел истории САМОГО администратора.**

`INCIDENT_DESTINATIONS[failure_spike] = "/history?status={status}"`. Маршрут живой — тест `test_every_incident_kind_has_a_label_a_tone_and_a_living_route` находит его среди маршрутов приложения, и 404 по строке инцидента невозможен. Но `/history` показывает отправки того, кто на неё смотрит, тогда как признак всплеска считает ВЕСЬ сервис: администратор, нажавший «Чинить →», увидит свои собственные неудачные отправки, а не те, из-за которых поднялся инцидент.

Адрес НЕ изменён этим планом намеренно: D-48 предписывает «отказы → «История» с фильтром» буквально, и подмена его на `/admin/logs?level=error` (подраздел отгружен планом 06-08 и отвечает на общесистемный вопрос прямо) была бы отменой решения владельца исполнителем. Записано в `.planning/WINDOWS.md` (запись 2, статус open) и отражено в `coverage: D9` как предмет человеческого суждения — ровно там, где план 06-04 его и оставил (его собственное `coverage: D7` прямо отложило проверку адресов до отгрузки подразделов).

## User Setup Required

None — внешних служб план не касается, установок пакетов нет, миграций нет.

## Next Phase Readiness

- «Обзор» закрывает критерий 1 фазы (ключевые показатели) и критерий 5 (инциденты на «Обзоре»).
- ADMIN-03 закрыт второй половиной: каркас подразделов дал план 06-01, наполнение — этот. ADMIN-11 закрыт второй половиной: вычисление признаков дал план 06-04, показ — этот.
- **Для плана 06-11 («Платежи»):** `app/application/admin/overview_stats.py` заведён и готов принять величины раздела платежей; агрегатов в `app/pages/admin.py` больше нет, и добавление их туда роняет прогон — новые счёты обязаны идти в прикладной слой.
- **Для плана 06-14 (ручная приёмка на 375px):** строка инцидента — четвёртый примитив перечня фазы; она переносится по `flex-wrap`, текст уходит в `overflow-wrap: anywhere`, переход прижат `margin-left: auto` и на узкой ширине уезжает на вторую строку, а не за край. Проверяется глазами вместе с остальными пятью подразделами.
- **Требует решения владельца** вопрос адреса `failure_spike` (см. выше).

## Self-Check: PASSED

- `app/application/admin/overview_stats.py` — FOUND
- `app/templates/admin/includes/incident_row.html` — FOUND
- `app/templates/admin/includes/queue_time.html` — FOUND
- `tests/test_application/test_admin_uses_analytics.py` — FOUND
- Коммиты `c673988`, `9b00306`, `686cd54`, `d4d9e19`, `d88bfb5`, `81af9c4` — FOUND
- Критерии приёмки перепрогнаны: `func.count|func.sum` в `app/pages/admin.py` — 0; `send_metrics` в обработчике «Обзора» — найден; `format_amount` в `overview.html` — 1; заглушек макета — 0; `восстановлен` в `overview.html` и `incident_row.html` — 0 и 0; `href` в `incident_row.html` — 1; `-k overview` собирает 11 тестов (при требовании ≥8), `-k incident` — 9 (при требовании ≥8), новый файл — 8 (при требовании ≥7)

---
*Phase: 06-admin-panel*
*Completed: 2026-08-23*
