---
phase: 03-gruppy-akkaunta
plan: 06
subsystem: ui
tags: [fastapi, jinja2, htmx, polling, alert, css, tdd]

# Dependency graph
requires:
  - phase: 03-02
    provides: "Колонки `last_synced_at` / `last_sync_result` и защищённый парсер `parse_sync_result`"
  - phase: 03-04
    provides: "Все три пути синхронизации ЗАПОЛНЯЮТ результат, включая провальные ветки — плашке есть что показать"
  - phase: 03-05
    provides: "Карточка шапки `[data-acct-head]`, секция 9 `app.css`, экран со списком, поиском и удалением"
  - phase: 01-06
    provides: "Эталон самоостанавливающегося опроса `accounts/partials/sync_status_card.html` и четыре инварианта приёма"
provides:
  - "Действие «Синхронизировать всё» в шапке экрана — настоящая форма POST на существующий вход `/accounts/{id}/sync-groups`"
  - "Плашка результата последней ЗАВЕРШЁННОЙ синхронизации: сводка либо текст ошибки, читается из аккаунта"
  - "Шаблон `account_groups/partials/sync_result.html` — минимальный подменяемый блок статуса с условным опросом"
  - "Маршрут `GET /accounts/{id}/groups/sync-status` — цель опроса со своей проверкой владения"
  - "Бейдж статуса экрана стал ЖИВЫМ: во время фоновой синхронизации он обновляется опросом, а не застывает до перезагрузки"
affects: [03-07, 03-08]

actuals:
  tokens: 61000
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Второй самоостанавливающийся опрос проекта: атрибуты запроса и триггера объявлены ВНУТРИ открывающего тега под условием статуса, остановка доказывается ПАРОЙ тестов, а не одиночным"
    - "Разметка первичной отрисовки и разметка ответа опроса — ОДИН файл: страница включает тот же паршал, который отдаёт вход статуса, поэтому расхождение невозможно по построению"
    - "Живое состояние выносится из страницы в подменяемый блок целиком, а не дублируется: два экземпляра словаря статусов расходятся ровно тогда, когда состояние важнее всего"
    - "Утверждение «элемент лежит ВНЕ подменяемого блока» проверяется извлечением блока по парным тегам, а не подстрочным поиском по странице"
    - "Счётчики сводки печатаются через `|int`: испорченное сохранённое значение выводится числом, а не произвольной строкой"

key-files:
  created:
    - app/templates/account_groups/partials/sync_result.html
  modified:
    - app/pages/account_groups.py
    - app/templates/account_groups/list.html
    - app/static/css/app.css
    - tests/test_pages/test_account_groups.py
    - tests/test_pages/test_htmx_preserved.py

key-decisions:
  - "Бейдж статуса ПЕРЕЕХАЛ из шапки в подменяемый блок, а не продублировался в нём: два бейджа на экране — живой и застывший — разъезжались бы ровно во время синхронизации. Блок стоит внутри шапки на месте прежнего бейджа, поэтому контракт E1 («шапка несёт бейдж статуса») выполняется, а обновление приходит опросом"
  - "Отказ входа статуса — ПУСТОЙ ответ 200, а не редирект на /login: редирект вернул бы в подменяемый блок целую страницу входа, и опрос продолжился бы. Пустой ответ и не отдаёт разметки, и останавливает опрос вкладки с истёкшей сессией"
  - "Кнопка при выполнении НЕ отключается: повторную отправку отклоняет существующий guard `status == 'syncing'` обработчика. Отключение выглядело бы защитой, но ею не является — форму можно отправить и мимо страницы, — зато пользователь с зависшим статусом лишился бы способа повторить"
  - "Сегмент «не найдено N» гейтится приведённым к целому значением (`|int > 0`), а не истинностью: сохранённая строка «0» была бы истинной и напечатала бы «не найдено 0» — ровно то, что запрещено"
  - "Признак вращения значка несёт ФОРМА (`data-syncing`), а не свой класс кнопки: состояние принадлежит действию, а не оформлению, и правило переживает смену варианта кнопки"

patterns-established:
  - "Отрицательная половина парного теста начинается с ПОЛОЖИТЕЛЬНОГО утверждения (блок отрисован, бейдж на месте): без него «опроса нет» выполняется и на странице, где блока нет вовсе"
  - "Тест недостижимости входа утверждает КОНКРЕТНЫЙ ответ (200 + пустое тело), а не только отсутствие разметки: код 404 несуществующего маршрута удовлетворяет «разметки нет» и зеленит тест до появления входа"

requirements-completed: [GRP-07]

coverage:
  - id: D1
    description: "Пользователь запускает повторную синхронизацию кнопкой «Синхронизировать всё», не покидая экрана (GRP-07, D-09)"
    requirement: "GRP-07"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_header_carries_the_sync_form"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_sync_action_says_it_is_in_flight"
        status: pass
    human_judgment: false
  - id: D2
    description: "Сводка синка показывает найдено, новых и обновлено имён; «не найдено N» появляется только при значении больше нуля (D-09, E2 populated)"
    requirement: "GRP-07"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_success_plashka_prints_all_three_counters"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_success_plashka_omits_the_missing_segment_when_zero"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_success_plashka_shows_the_missing_segment_when_nonzero"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_plashka_renders_exactly_once"
        status: pass
    human_judgment: false
  - id: D3
    description: "Провал синхронизации показывает текст ошибки И следующий шаг вместо сводки; текст внешней системы экранируется (D-09, T-03-27, E2 error)"
    requirement: "GRP-07"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_error_plashka_names_the_error_and_the_next_step"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_error_text_from_the_worker_is_escaped"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_corrupt_stored_result_renders_no_plashka (5 видов мусора)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Результат последнего синка виден при перезаходе — читается из аккаунта, а не из памяти запроса (D-09)"
    requirement: "GRP-07"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_stored_result_survives_a_revisit"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_never_synced_account_renders_no_plashka"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_plashka_of_a_running_sync_keeps_the_previous_summary"
        status: pass
    human_judgment: false
  - id: D5
    description: "Фоновый синк WA и MAX добирается САМООСТАНАВЛИВАЮЩИМСЯ опросом: атрибуты присутствуют только в ветке выполнения и исчезают вместе с ней (D-09, T-03-26)"
    requirement: "GRP-07"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_account_groups_polling_continues_while_syncing"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_account_groups_polling_stops"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_account_groups_page_polls_only_while_syncing"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_page_polls_while_the_sync_is_running"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_page_declares_no_poll_outside_the_running_state (2 статуса)"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_status_endpoint_stops_the_poll_when_the_sync_ends (2 статуса)"
        status: pass
      - kind: other
        ref: "tests/test_pages/test_account_groups.py#test_polled_block_is_declared_exactly_once (объявление в исходнике одно)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Вход статуса проверяет аутентификацию и владение В СЕБЕ: чужой аккаунт и запрос без сессии разметки не получают (T-03-25)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_status_endpoint_of_a_foreign_account_leaks_nothing"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_status_endpoint_without_session_leaks_nothing"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_status_endpoint_accepts_the_layout_param"
        status: pass
    human_judgment: false
  - id: D7
    description: "Плашка результата и панели подтверждения живут ВНЕ подменяемого опросом элемента (Pitfall 8, T-11-04)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_confirm_panel_never_lives_inside_the_polled_block"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_result_plashka_never_lives_inside_the_polled_block"
        status: pass
    human_judgment: false
  - id: D8
    description: "Кнопки повторной синхронизации ОТДЕЛЬНОЙ группы на экране нет — протокола синхронизации одной группы у воркеров не существует (D-12)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_no_per_group_sync_action_on_the_screen"
        status: pass
    human_judgment: false
  - id: D9
    description: "Внешний вид шапки с двумя действиями, плашки и блока статуса на ширинах 320 / 860 / 1280: перенос действий на свою строку, перенос длинной строки ошибки внутри плашки, отсутствие горизонтальной прокрутки"
    verification:
      - kind: other
        ref: "tests/test_pages/test_account_groups.py#test_screen_has_its_own_css_section (наличие правил раздела 9)"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_account_groups.py#test_screen_has_no_utility_classes"
        status: pass
    human_judgment: true
    rationale: "Правила раскладки и переноса заданы и их наличие проверено автоматически, но визуальная приёмка на трёх ширинах — человеческое суждение. Сюда же относятся обе страховочные проверки плана (`verification: backstop`): имя аккаунта в 60 символов на 320px и строка ошибки воркера в 300 символов на 320px. Место проверки — UAT фазы; экран впервые собран целиком именно этим планом."

# Metrics
duration: 78 min
completed: 2026-08-12
status: complete
---

# Phase 03 Plan 06: Результат синхронизации на экране — Summary

**GRP-07 замкнут со стороны пользователя: синхронизация запускается кнопкой из шапки, её результат — сводка «найдено N, новых M, обновлено имён K» либо текст ошибки со следующим шагом — читается из аккаунта и потому переживает перезаход, а завершение фоновой синхронизации WA и MAX добирается опросом, который останавливает сам себя.**

## Performance

- **Duration:** 78 min
- **Tasks:** 2 (одна обычная, одна TDD — гейты RED/GREEN)
- **Files:** 6 (1 создан, 5 изменено)
- **Suite:** **1056 passed, 0 failed** (было 1024 на базе волны; прирост ровно на 32 новых теста плана)

## Что построено

| Артефакт | Содержание |
|---|---|
| Действие «Синхронизировать всё» | Настоящая форма POST на существующий вход `/accounts/{id}/sync-groups` в `.acct-head__actions`; при выполнении подпись «Синхронизация…» и вращающийся значок |
| Плашка результата | Макрос `alert`: сводка трёх счётчиков варианта успеха либо текст ошибки с инструкцией повтора варианта ошибки; вне подменяемого блока и вне панелей |
| `account_groups/partials/sync_result.html` | Минимальный подменяемый блок: бейдж статуса + строка «Синхронизация выполняется…», условный опрос, вежливое оповещение |
| `GET /accounts/{id}/groups/sync-status` | Цель опроса: аутентификация → владение → три известных статуса; всё остальное — пустой ответ |
| Разбор сохранённого результата | `parse_sync_result(account.last_sync_result)` в контексте страницы |
| Раздел 9 `app.css` | Раскладка блока статуса в шапке, вращение значка (+ отключение при `prefers-reduced-motion`), отступ и перенос текста плашки |

## Task Commits

1. **Задача 1 — плашка результата и действие запуска в шапке**
   - `84ba2ab` — feat: 75/75 зелёных (+17 тестов)
2. **Задача 2 — самоостанавливающийся опрос статуса (TDD)**
   - `10dcc6e` — test (RED): 15 падающих
   - `32052a4` — feat (GREEN): 87/87 + 19/19 зелёных

_Фазы REFACTOR не потребовалось: блок повторяет форму отгруженного эталона `accounts/partials/sync_status_card.html`, а вход статуса — форму его обработчика._

## Decisions Made

- **Бейдж статуса переехал в подменяемый блок, а не продублировался в нём.** Экран уже нёс бейдж в шапке (план 03-05). Выписать второй экземпляр словаря статусов внутри блока означало бы **два бейджа на одном экране** — один живой, обновляемый опросом, и один застывший до перезагрузки, — и расходились бы они ровно в тот момент, когда состояние важнее всего: во время синхронизации. Поэтому блок стоит **внутри шапки на месте прежнего бейджа**: контракт E1 («шапка несёт бейдж статуса, всё из уже загруженного аккаунта без дополнительных запросов») выполняется — на первичной отрисовке страница включает тот же паршал со статусом уже загруженного аккаунта, — а обновление приходит опросом. Импорт `badge` из `list.html` убран: он остался бы неиспользованным.
- **Отказ входа статуса — пустой ответ 200, а не редирект на `/login`.** Соседние маршруты экрана редиректят, и первым побуждением было повторить их форму. Но цель опроса — не страница, а **содержимое подменяемого элемента**: редирект (httpx и htmx его проследуют) вернул бы в блок статуса целую страницу входа, а опрос при этом продолжился бы. Пустой ответ решает обе задачи разом — разметки не отдаёт и опрос останавливает.
- **Кнопка при выполнении не отключается.** UI-SPEC описывает подпись и значок, но не `disabled`. Отключение выглядело бы защитой от повторного запуска, но ею не является: форму можно отправить и мимо страницы, поэтому настоящая защита — существующий серверный guard `status == 'syncing'`. Зато пользователь, у которого статус завис из-за упавшего воркера, при `disabled` лишился бы единственного способа повторить.
- **Сегмент «не найдено N» гейтится числом, а не истинностью.** Значение приводится `|int` и сравнивается с нулём. Проверка на истинность выглядит короче, но сохранённая строка `"0"` истинна — и напечатала бы «не найдено 0», ровно то, что запрещено контрактом. Тем же `|int` печатаются и три основных счётчика: испорченное значение выводится числом, а не произвольной строкой (E2 overflow).
- **Признак вращения значка несёт форма (`data-syncing`), а не свой класс кнопки.** Приём взят у соседнего правила раздела 9 (`[data-group-row] form[action$="/delete"] .btn:hover`): состояние принадлежит действию, а не оформлению, и правило переживает смену варианта кнопки. Второй анимации не заводится — переиспользуется `@keyframes orbit` раздела 2.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing critical] `app/static/css/app.css` не был в перечне файлов плана, но потребовался**

- **Found during:** Задачи 1 и 2
- **Issue:** три вещи, названные самим планом, без правил не существуют: «значок в состоянии вращения» (задача 1) — это анимация; у отгруженного `.alert` **нет собственных внешних отступов**, и плашка слиплась бы с соседними блоками, ломая вертикальный ритм в 12px; блок статуса, встав на место бейджа, перестал попадать под правило `[data-acct-head] > .badge`, то есть потерял бы раскладку в шапке.
- **Fix:** четыре правила в существующую секцию 9 — раскладка `[data-acct-sync]`, вращение значка под `[data-acct-head] form[data-syncing]`, отступ и перенос текста `[data-sync-plashka]`, и отдельный `@media (prefers-reduced-motion: reduce)` для анимации. Новых цветов, радиусов и кеглей не вводится; вращение переиспользует `@keyframes orbit` раздела 2.
- **Files modified:** `app/static/css/app.css` (+32 строки)
- **Committed in:** `84ba2ab`, `32052a4`

**2. [Rule 1 — Bug] Три собственных теста фазы RED зеленели вакуумно**

- **Found during:** Задача 2, первый прогон RED (до реализации): 9 падений и 3 прохода
- **Issue:** обе ветки `test_page_declares_no_poll_outside_the_running_state` утверждали только ОТСУТСТВИЕ опроса — а оно выполняется и на странице, где блока статуса нет вовсе, то есть тест зеленел бы, ничего не проверяя. `test_status_endpoint_of_a_foreign_account_leaks_nothing` проходил на **404 несуществующего маршрута**: «разметки статуса нет» верно и когда входа ещё не существует.
- **Fix:** обе отрицательные ветки начинаются теперь с положительного утверждения — блок отрисован и несёт бейдж своего статуса (`Активно` / `Ошибка синхронизации`), параметризация расширена ожидаемой подписью. Тест чужого аккаунта утверждает конкретный ответ: `200` и пустое тело. После правки — 12 падений из 12, то есть настоящий RED.
- **Files modified:** `tests/test_pages/test_account_groups.py` (внутри того же RED-коммита `10dcc6e`)

**3. [Rule 1 — Bug] Тест неавторизованного запроса падал на общем помощнике сидирования**

- **Found during:** Задача 2, первый прогон GREEN (86 прошли, 1 упал)
- **Issue:** `test_status_endpoint_without_session_leaks_nothing` сеял аккаунт помощником `_seed_account_with_result`, а тот ищет пользователя, которого создаёт **фикстура авторизации** — единственному тесту файла с неавторизованным клиентом она по построению не положена. Падение было `NoResultFound` в сидировании, то есть дефектом теста, а не реализации.
- **Fix:** владелец аккаунта заводится в самом тесте; причина зафиксирована в его докстринге, чтобы следующий автор не «починил» это возвратом к общему помощнику.
- **Files modified:** `tests/test_pages/test_account_groups.py`
- **Committed in:** `32052a4`

**Total deviations:** 3 auto-fixed (1 × Rule 2 — стили, 2 × Rule 1 — дефекты собственных тестов). Продуктовая логика деривации не потребовала; объём плана не расширен, решения D-09/D-12/D-13 не менялись.

## Issues Encountered

**Гейта checkpoint в плане нет** — обе задачи `type="auto"`, `autonomous: true`. Обе страховочные проверки (`verification: backstop`) — визуальные, на ширине 320px: имя аккаунта в 60 символов и строка ошибки воркера в 300 символов. Правила переноса для обеих заданы (`overflow-wrap: anywhere` у плашки, `text-overflow: ellipsis` у имени из плана 03-05), но приёмка отнесена к UAT фазы и зафиксирована строкой D9 в `coverage` с `human_judgment: true`: исполнитель работает изолированным агентом в worktree без канала к пользователю.

**Прочего нет.** Существующие тесты экрана аккаунтов, страховочной сетки HTMX, подтверждений и адаптивной разметки переживают правки без изменений: новый паршал не рисует строку (`data-row` в нём отсутствует), не эмитит панель подтверждения и не отключает автоэкранирование, поэтому ни одна инвентаризация шаблонов не сдвинулась.

## Known Stubs

Заглушек, мешающих цели плана, нет. Сознательно отложенное и осознанные границы:

| Что | Где | Почему и кто закрывает |
|-----|-----|------------------------|
| Строка идентичности «синхронизация идёт сейчас» опросом НЕ обновляется — она вне подменяемого блока и остаётся прежней до перезагрузки | `app/templates/account_groups/list.html` | Прямое следствие правила «блок минимален»: втянуть в него строку идентичности значило бы втянуть половину шапки. Бейдж статуса и строка «Синхронизация выполняется…» обновляются и несут состояние честно; строка идентичности говорит о ВРЕМЕНИ последнего синка, и её обновление требует значения `last_synced_at`, которого у обработчика опроса в контексте нет. Кандидат на отдельное решение при верификации фазы |
| Плашка результата опросом не обновляется: после завершения фоновой синхронизации сводка появится при следующей загрузке страницы | `app/templates/account_groups/list.html` | Так задумано контрактом: плашка отражает последнюю ЗАВЕРШЁННУЮ синхронизацию и обязана лежать вне подменяемого блока (Pitfall 8). Для TG-пути (синхронного) плашка приходит сразу — редирект перезагружает страницу |
| Пометка «не найдена при синке» рендерится, `missing_since` заполняется планом 03-02/03-04 | `app/templates/account_groups/includes/group_row.html` | Закрыто предыдущими планами волны; здесь только показ числа пропавших в сводке |

## Threat Flags

Новой поверхности сверх зафиксированной в `<threat_model>` плана не появилось. Отработка регистра:

| Threat ID | Disposition | Как закрыт |
|-----------|-------------|------------|
| T-03-25 | mitigate | Аутентификация и владение проверяются В САМОМ входе статуса (`get_user_from_cookie` → `_load_owned_account`), а не наследуются от страницы. Чужой `account_id` и запрос без сессии дают **пустой ответ 200** — по нему не отличить чужой аккаунт от несуществующего. Оба теста написаны ДО реализации и усилены утверждением о конкретном ответе |
| T-03-26 | mitigate | Атрибуты запроса, триггера и режима замены объявлены ТОЛЬКО в ветке `status == 'syncing'` — одним объявлением, что закреплено проверкой исходника (`hx-trigger` встречается ровно один раз). Остановка доказывается **парой** тестов на входе и **парой** на странице: одиночный тест присутствия зеленеет у вечного опроса, одиночный тест отсутствия — на пустом ответе |
| T-03-27 | mitigate | Текст ошибки уходит в `alert` обычным выводом под autoescape, готовая разметка макросу не передаётся; `<script>` в сохранённом результате приходит на страницу экранированным. Испорченное значение (5 видов мусора) даёт **отсутствие плашки и код 200**, а не исключение |
| T-03-28 | mitigate | Форма запуска ведёт на существующий вход с уже отгруженным guard-ом `status == 'syncing'`; подпись действия при выполнении отражает состояние («Синхронизация…»), кнопка не отключается сознательно — защита серверная, а не разметочная |

## Verification

| Проверка | Результат |
|---|---|
| `uv run pytest tests/test_pages/test_account_groups.py -q` | ✅ 87 passed |
| `uv run pytest tests/test_pages/test_htmx_preserved.py -q` | ✅ 19 passed |
| `uv run pytest tests/test_pages/ tests/test_templates/ -q` | ✅ 539 passed |
| `uv run pytest tests/test_pages/ tests/test_routes/ -q` | ✅ 651 passed |
| `uv run pytest tests/ -q` — суита не деградировала | ✅ **1056 passed, 0 failed** |
| `grep -c 'async def account_groups_sync_status(' app/pages/account_groups.py` | ✅ 1 |
| `grep -c 'hx-trigger' …/partials/sync_result.html` | ✅ **1** — единственное объявление опроса |
| `grep -q 'syncing' …/partials/sync_result.html` | ✅ объявление стоит под условием статуса |
| `grep -q 'group-del-' …/partials/sync_result.html` | ✅ не встречается — панели в блоке нет |
| `grep -q 'parse_sync_result' app/pages/account_groups.py` | ✅ |
| `grep -q 'sync-groups' app/templates/account_groups/list.html` | ✅ |
| `grep -c 'groups/[^"]*/sync' …/includes/group_row.html` | ✅ **0** — действия синхронизации отдельной группы в строке нет |
| `must_haves.artifacts` — минимальные размеры | ✅ `sync_result.html` 59 строк (мин. 20); `account_groups.py` несёт вход статуса и разбор результата |
| `key_links` — `groups/sync-status` и `parse_sync_result` | ✅ оба присутствуют |

## Success criteria

| Критерий | Результат |
|---|---|
| GRP-07 полностью: пользователь повторно синхронизирует группы и видит результат, не покидая экрана | ✅ |
| D-09 реализовано: сводка на экране, результат переживает перезаход, провал показывает ошибку и следующий шаг | ✅ |
| D-12 реализовано: кнопки синхронизации отдельной группы нет | ✅ |
| Опрос объявлен ровно в одном месте и только под условием статуса выполнения | ✅ |
| Плашка результата и панели подтверждения — вне подменяемого блока | ✅ |

## Открытые допущения (переданы дальше, не разрешены)

- Зондирование границ по **GRP-07** вернуло `unclassified` («review manually»). Допущение унаследовано от планов 03-02 и 03-04 и этим планом **не разрешалось**: категория границ требования остаётся открытым предположением планировщика и подлежит человеческому просмотру при верификации фазы.

## Next Phase Readiness

- **План 03-07** (снос глобального раздела `/groups`) получает экран, закрывающий требование целиком: просмотр, поиск, переключение, удаление и повторную синхронизацию с показом результата. Новых мест удаления и панелей подтверждения этот план не добавил, поэтому перечни `ROW_DELETE_SITES` / `MODAL_PLACES` при сносе уменьшаются ровно на числа, названные в 03-05.
- **Экран собран целиком** — визуальная приёмка на 320 / 860 / 1280 (строка D11 плана 03-05 и D9 этого плана) может выполняться на нём в окончательном виде.
- **Блокеров нет.** Миграций план не содержит; блокер выката ревизий `0013`/`0014` на целевую базу к нему не относится.

## Self-Check: PASSED

Проверено на диске и в git, а не по памяти:

- Созданный файл существует: `app/templates/account_groups/partials/sync_result.html` (59 строк)
- Все пять изменённых файлов присутствуют в `git diff --stat 4bb0ddc..HEAD`: `app/pages/account_groups.py`, `app/templates/account_groups/list.html`, `app/static/css/app.css`, оба тестовых файла
- Все три коммита плана присутствуют в истории ветки: `84ba2ab`, `10dcc6e`, `32052a4`
- Удалений файлов ни один коммит плана не содержит (`git diff --diff-filter=D` пуст для обоих); неотслеживаемых файлов не осталось
- Acceptance criteria обеих задач перепрогнаны поимённо — таблица «Verification» выше
- Общие артефакты не тронуты: `STATE.md` и `ROADMAP.md` этим планом не изменялись (worktree-режим, запись за оркестратором)

---
*Phase: 03-gruppy-akkaunta*
*Completed: 2026-08-12*
