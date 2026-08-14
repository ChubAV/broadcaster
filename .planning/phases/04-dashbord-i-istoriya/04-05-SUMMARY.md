---
phase: 04-dashbord-i-istoriya
plan: 05
subsystem: ui
tags: [htmx, jinja2, fastapi, sqlalchemy, polling, dashboard]

requires:
  - phase: 04-dashbord-i-istoriya
    provides: "плана 04-01: модуль app/application/analytics/send_analytics.py, константы статусов, конвенция «сессия первым позиционным, остальное keyword-only»"
  - phase: 04-dashbord-i-istoriya
    provides: "плана 04-04: блок «Ближайшие отправки» как левая половина пары, приём «строка целиком — ссылка», примитив [data-uprow]"
  - phase: 01-interfejsnyj-fundament
    provides: "get_shell_context с ключами sessions_online/sessions_total, макросы card_open/card_close, mono, empty_state, глобал time_ago_for_user, @keyframes pulse"
provides:
  - "recent_feed + FeedRow — последние отправки владельца проекцией колонок, самая свежая первой"
  - "Модуль app/pages/dashboard_feed.py: собственный роутер вне страничного, маршрут GET /dashboard/feed"
  - "FEED_LIMIT / FEED_POLL_SECONDS — единственный источник лимита строк и интервала опроса"
  - "Паршал dashboard/partial_feed.html и макрос feed_row; атрибуты разметки [data-feed]/[data-feedrow]/[data-feeddot]/[data-feedtext]"
  - "Первый в проекте БЕССРОЧНЫЙ опрос и пара тестов, закрепляющая его механизм"
  - "Регрессия DASH-05: индикатор воркеров читается из контракта шелла, второго источника нет"
affects: [04-06, 04-10, phase-6-admin]

actuals:
  tokens: 111369
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Бессрочный опрос: атрибуты на СТАБИЛЬНОМ контейнере, подмена ВНУТРЬ него — обратно трём самоостанавливающимся опросам проекта"
    - "Паршал частого опроса объявляется ВНЕ страничного роутера, чтобы не тянуть контекст шелла на каждый тик"
    - "Проверка «модуль не обращается к X» разбором синтаксического дерева, а не поиском подстроки: дерево отличает упоминание от обращения"
    - "Первичная отрисовка блока ТЕМ ЖЕ паршалом, что отдаёт маршрут опроса — блок не ждёт первого тика"

key-files:
  created:
    - app/pages/dashboard_feed.py
    - app/templates/dashboard/partial_feed.html
    - app/templates/dashboard/includes/feed_row.html
  modified:
    - app/application/analytics/send_analytics.py
    - app/pages/dashboard.py
    - app/main.py
    - app/templates/dashboard.html
    - app/static/css/app.css
    - tests/test_pages/test_dashboard.py
    - tests/test_pages/test_htmx_preserved.py
    - tests/test_pages/test_responsive_markup.py
    - tests/test_pages/test_shell.py
  deleted:
    - app/templates/dashboard/includes/recent_send_card.html

key-decisions:
  - "Соединения с groups в recent_feed НЕТ вопреки букве плана: все шесть значений строки — снимки самой записи журнала, и соединение осталось бы платой без покупки на маршруте, который вызывается каждые 20 секунд на каждой вкладке"
  - "Выбираются КОЛОНКИ, а не сущность SendLog: восемь ORM-объектов на каждый тик не нужны шаблону, которому нужны шесть значений"
  - "Пустое состояние ленты БЕЗ призыва к действию, в отличие от соседних блоков: призыв ведёт по счётчикам шелла, а контекста шелла у паршала нет и быть не должно"
  - "Контейнер ленты не обёрнут условием по наличию записей: обёрнутый, он не ожил бы у нового пользователя никогда"
  - "Машинная форма «опрос не самоостанавливается» — отсутствие Jinja-условия ВНУТРИ открывающего тега контейнера: у трёх самоостанавливающихся опросов условие стоит именно там"
  - "Проверка «нет обращения к Docker» построена на синтаксическом дереве, а не на поиске подстроки: контракт модуля аналитики ОБЪЯСНЯЕТ свой запрет, и поиск по тексту заставил бы снять из докстринга причину"
  - "dashboard.html выведен из таблицы ROWHEAD_PAGES вместе с блоком последних отправок: шапку колонок он больше не вызывает"

patterns-established:
  - "Пара тестов опроса пишется в ОБЕ стороны: тест присутствия атрибутов на странице и тест их отсутствия в паршале — одиночный зеленеет вакуумно"
  - "Тест на отсутствие обращения к внешней системе проверяет ИМПОРТЫ И ВЫЗОВЫ через ast, а не подстроку: иначе объяснение запрета нарушает запрет"
  - "Выход шаблона из инвентаризационного перечня оформляется комментарием со ссылкой на план ПЛЮС уменьшением объявленного числа"

requirements-completed: []

coverage:
  - id: D1
    description: "Маршрут паршала ленты объявлен вне страничного роутера и не тянет контекст шелла на каждый тик"
    requirement: "DASH-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_feed_does_not_load_the_shell_context"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_feed_response_is_a_fragment_not_a_page"
        status: pass
    human_judgment: false
  - id: D2
    description: "Лента отдаёт не более limit строк владельца по убыванию времени отправки; чужие записи не попадают (T-04-17)"
    requirement: "DASH-03"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_dashboard.py#test_recent_feed_returns_newest_first"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_dashboard.py#test_recent_feed_respects_the_limit"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_dashboard.py#test_recent_feed_row_carries_the_fields_of_the_record"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_dashboard.py#test_recent_feed_ignores_other_users"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_feed_requires_authentication"
        status: pass
    human_judgment: false
  - id: D3
    description: "Строка ленты — обычная ссылка в запись истории и работает без JavaScript (D-08)"
    requirement: "DASH-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_feed_row_links_to_the_history_record"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_dashboard.py#test_dashboard_feed_returns_rows"
        status: pass
    human_judgment: false
  - id: D4
    description: "Страница несёт адрес паршала и объявление интервала, а паршал не несёт ни одного атрибута опроса — парная половина (D-06, D-07)"
    requirement: "DASH-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_dashboard_feed_container_polls"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_dashboard_feed_partial_carries_no_polling_attributes"
        status: pass
    human_judgment: false
  - id: D5
    description: "Опрос не самоостанавливается: ветки, в которой атрибуты покидают DOM, в разметке нет"
    requirement: "DASH-03"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_dashboard_feed_polling_survives_an_empty_feed"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_preserved.py#test_dashboard_feed_polling_has_no_stop_branch"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_htmx_preserved.py#test_dashboard_feed_swaps_inside_the_container"
        status: pass
    human_judgment: false
  - id: D6
    description: "Существующий механизм остановки опроса на экране аккаунтов не тронут — три самоостанавливающихся опроса проекта остались зелёными"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_sync_polling_stops"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_sync_polling_continues_while_syncing"
        status: pass
    human_judgment: false
  - id: D7
    description: "Блок «Последние отправки» со страницы исчез, а шаблон его строки в проекте больше не достижим и снят с обоих инвентаризационных перечней"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_row_templates_without_header_are_accounted_for"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_rowhead_pages_all_have_a_parametrization_entry"
        status: pass
      - kind: other
        ref: "test ! -f app/templates/dashboard/includes/recent_send_card.html"
        status: pass
    human_judgment: false
  - id: D8
    description: "Дашборд показывает число воркеров онлайн из контракта шелла; число равно числу активных messenger-аккаунтов, ноль показывается, а не прячется (DASH-05)"
    requirement: "DASH-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_dashboard_shows_the_sessions_indicator"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_dashboard_sessions_number_counts_active_accounts"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_dashboard_sessions_number_is_zero_without_active_accounts"
        status: pass
    human_judgment: false
  - id: D9
    description: "В пути рендера дашборда нет обращения к Docker ни при каких условиях, и второго источника числа воркеров не появилось (T-04-21)"
    requirement: "DASH-05"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_dashboard_render_path_never_touches_docker"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_shell.py#test_dashboard_page_has_no_second_source_of_the_sessions_number"
        status: pass
    human_judgment: false
  - id: D10
    description: "Живым остаётся только лента: плитки, heatmap и ближайшие отправки считаются один раз при загрузке страницы и опросом не обновляются (D-04)"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_htmx_preserved.py#test_dashboard_feed_polling_has_no_stop_branch"
        status: pass
    human_judgment: true
    rationale: "Тест утверждает, что контейнер ленты в разметке ровно один, то есть второго носителя опроса на странице нет. Что именно НЕ обновляется, автотест не наблюдает: для этого нужно смотреть на живую вкладку. Пункт уходит в чекпоинт плана 04-10 вместе с самим тиканьем"
  - id: D11
    description: "Опрос действительно продолжает тикать в открытой вкладке за пределами нескольких интервалов"
    verification: []
    human_judgment: true
    rationale: "Backstop-труть самого плана: браузерных/e2e-тестов в проекте нет, и фактическое тиканье автотестами не воспроизводится. Машинная форма («ветки без атрибутов не существует») закреплена D5; наблюдение живой вкладки — ручная проверка плана 04-10"
  - id: D12
    description: "Живая лента читается на мобильных ширинах: текст события обрезается многоточием, подпись времени сохраняет позицию"
    verification: []
    human_judgment: true
    rationale: "Браузерных/e2e-тестов в проекте нет, медиазапросы автотестами не исполняются. Тот же пункт чекпоинта плана 04-10, что и у плиток из 04-01 и двух блоков из 04-04"

duration: 56 min
completed: 2026-08-14
status: complete
---

# Phase 4 Plan 05: Живая лента и закрепление DASH-05 Summary

**Лента последних отправок обновляется бессрочным опросом на стабильном контейнере — первый в проекте опрос, который не должен останавливаться, — её маршрут вынесен из-под страничного роутера и не платит четырьмя запросами контекста шелла за каждый тик, а строка целиком является обычной ссылкой в запись истории; число воркеров онлайн осталось при единственном источнике — контракте шелла Фазы 1.**

## Performance

- **Duration:** 56 min
- **Started:** 2026-08-14T08:05:11Z
- **Completed:** 2026-08-14T09:01:17Z
- **Tasks:** 3
- **Files modified:** 13 (3 создано, 9 изменено, 1 удалён)

## Accomplishments

- Живая лента отвечает на вопрос «что происходит прямо сейчас» без перезагрузки страницы: строки приезжают паршалом каждые 20 секунд, а первая отрисовка идёт ТЕМ ЖЕ паршалом на самой странице, поэтому блок не стоит пустым до первого тика.
- **Опрос не может остановиться по построению разметки, а не по договорённости.** Три существующих опроса проекта устроены обратно — они подменяют сам элемент, и исчезновение атрибутов из очередного ответа и есть их механизм остановки. Здесь подмена идёт ВНУТРЬ стабильного контейнера, атрибуты живут на нём и DOM не покидают; забытые в паршале атрибуты при таком устройстве ленту не убивают.
- Механизм закреплён ПАРОЙ тестов плюс двумя утверждениями по исходнику. Одиночный тест присутствия зеленел бы и у ленты, которая умрёт после первой подмены; одиночный тест отсутствия — на пустом ответе.
- Маршрут ленты объявлен ВНЕ страничного роутера (открытый вопрос 4 плана). Страничный роутер несёт загрузку контекста шелла зависимостью на каждом маршруте — четыре round-trip; при бессрочном опросе эта цена умножалась бы на число открытых вкладок и делилась на интервал (смягчение T-04-18). Условие корректности — «паршал не читает контекст шелла» — закреплено тестом-шпионом, причём парным внутри себя: он сначала проверяет, что шпион вообще срабатывает на самой странице.
- Блок «Последние отправки» снят вместе со своим шаблоном строки, и оба инвентаризационных перечня, где шаблон был назван, приведены в соответствие с уменьшением объявленного числа — молчаливое исчезновение шаблона по-прежнему краснеет.
- DASH-05 закреплён регрессией без единой строки нового прикладного кода: индикатор читается из `get_shell_context` Фазы 1, второго запроса по messenger-аккаунтам страница дашборда не делает, а обращения к Docker в пути рендера нет ни в одном из трёх модулей.
- 20 новых тестов (10 ленты, 5 опроса, 5 регрессии DASH-05) при двух снятых. Полная суита — **1218 passed**.

## Task Commits

Каждая задача исполнена как TDD-пара «красный набор → реализация»:

1. **Task 1 RED — тесты выборки и маршрута ленты** — `92c80ac` (test)
2. **Task 1 GREEN — маршрут и паршал вне страничного роутера** — `38e2631` (feat)
3. **Task 2 RED — парные тесты бессрочного опроса** — `210aaf2` (test)
4. **Task 2 GREEN — опрос на стабильном контейнере, снятие блока последних отправок** — `8f03168` (feat)
5. **Task 3 — регрессия DASH-05** — `40128bd` (test)

_Задача 3 объявлена планом закрепляющей, а не строительной: кода в приложении она не добавляет, поэтому её коммит один и помечен `test`. Фаза RED у неё состоялась по-настоящему — см. деviation 2._

## Files Created/Modified

- `app/application/analytics/send_analytics.py` — `FeedRow` и `recent_feed`: проекция шести колонок журнала по убыванию времени отправки
- `app/pages/dashboard_feed.py` — собственный роутер без зависимости шелла, маршрут `GET /dashboard/feed`, константы `FEED_LIMIT` и `FEED_POLL_SECONDS`
- `app/templates/dashboard/partial_feed.html` — паршал: только строки и пустое состояние, ни одного атрибута опроса
- `app/templates/dashboard/includes/feed_row.html` — макрос `feed_row`: точка статуса атрибутом, текст события фразой, «N назад» существующим глобалом; корень строки — ссылка `/history/{id}`
- `app/pages/dashboard.py` — блок `recent_sends` снят, в контекст уходят `feed` и `feed_poll_seconds`
- `app/main.py` — включение роутера ленты ДО страничного роутера
- `app/templates/dashboard.html` — блок «Живая лента» с пульсирующей точкой вместо блока «Последние отправки»; импорт снесённого макроса снят
- `app/static/css/app.css` — правила `[data-feedhead]`/`[data-feed]`/`[data-feedrow]`/`[data-feeddot]`/`[data-feedtext]`; пульсация — существующий `@keyframes pulse`
- `app/templates/dashboard/includes/recent_send_card.html` — **удалён**
- `tests/test_pages/test_dashboard.py` — 10 новых тестов ленты (было 26, стало 36)
- `tests/test_pages/test_htmx_preserved.py` — 5 новых тестов бессрочного опроса
- `tests/test_pages/test_responsive_markup.py` — снят вход дашборда из таблицы шапок и запись снесённого шаблона из перечня строк, оба числа уменьшены с комментарием-следом; снят `test_dashboard_cell_labels_present`
- `tests/test_pages/test_shell.py` — 5 тестов регрессии DASH-05

## Decisions Made

- **Соединения с `groups` в `recent_feed` нет.** План предписывал повторить форму запроса снесённого блока (`select(SendLog, Group)` с `outerjoin`). Тому блоку строка группы была нужна ради внешнего идентификатора группы и идентификатора аккаунта; ленте не нужна НИ ОДНА колонка `Group` — все шесть её значений суть снимки самой записи журнала. Соединение осталось бы платой без покупки на маршруте, который вызывается каждые 20 секунд на каждой открытой вкладке (T-04-18). Имя группы берётся из снимка `send_logs.group_name` — из того же поля, что печатает и карточка истории, поэтому второго ответа на один вопрос не заводится.
- **Выбираются колонки, а не сущность.** `select(SendLog.id, ...)` вместо `select(SendLog)`: восемь ORM-объектов с их identity map на каждый тик не нужны шаблону, которому нужны шесть значений. Приём тот же, что у потокового чтения окна heatmap в 04-04, и по той же причине — маршрут на горячем пути.
- **Пустое состояние ленты без призыва к действию.** У соседних блоков дашборда призыв ведёт по счётчикам шелла (D-40), но контекста шелла у паршала нет и быть не должно — ради этого маршрут и вынесен. Собственный призыв здесь отвечал бы на вопрос «что делать дальше» вслепую, то есть завёл бы второй ответ, причём худший.
- **Контейнер ленты не обёрнут условием по наличию записей.** Самый естественный способ случайно получить ленту, которая у нового пользователя не оживёт никогда: первую отправку он дождётся, а увидит её только после перезагрузки. Пустое состояние живёт ВНУТРИ паршала, вместе со строками, и подменяется вместе с ними.
- **Машинная форма «опрос не самоостанавливается» — отсутствие Jinja-условия ВНУТРИ открывающего тега контейнера.** У всех трёх самоостанавливающихся опросов проекта условие стоит именно там, и именно там оно делает атрибуты исчезающими; утверждение поэтому проверяет ту же точку разметки, а не пересказывает намерение прозой.
- **Точка статуса красится по значению атрибута, а неизвестный статус остаётся ВИДИМЫМ.** Нейтральная заливка по умолчанию честнее исчезнувшей точки: исчезнув, она сдвинула бы текст события относительно соседних строк, и строка читалась бы как сломанная вёрстка, а не как отправка с необычным статусом.
- **Пульсация точки — существующий `@keyframes pulse`.** Тот же, которым уже пульсирует индикатор сессий в шапке шелла. Второй анимации того же смысла в проекте не заводится; точка сделана псевдоэлементом, потому что это украшение подписи, а не узел, нужный программе чтения с экрана.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Четыре моих же теста выборки падали на отсутствующем пользователе**

- **Found during:** Task 1 (первый прогон GREEN)
- **Issue:** Тесты самой функции `recent_feed` страницу не поднимают, а владельца брали хелпером `_current_user`, который ищет `testuser@test.com`. Этого пользователя заводит фикстура регистрации, которую тянет только `authed_client` — то есть тесты, не запросившие клиента, падали с `NoResultFound`. Ошибка была в ТЕСТАХ: тянуть в них клиента ради побочного эффекта регистрации значило бы поднимать приложение там, где проверяется запрос.
- **Fix:** Заведён хелпер `_seed_user`, вставляющий владельца напрямую; четыре теста переведены на него. Рядом выписано, почему владелец заводится вставкой, а не фикстурой.
- **Files modified:** tests/test_pages/test_dashboard.py
- **Verification:** все 10 тестов ленты — passed
- **Committed in:** 38e2631

**2. [Rule 1 - Bug] Мой тест «нет обращения к Docker» краснел на докстринге, ОБЪЯСНЯЮЩЕМ этот запрет**

- **Found during:** Task 3 (первый прогон регрессии DASH-05)
- **Issue:** Первая редакция теста читала исходники пути рендера как ТЕКСТ и искала имя по подстроке — приём, уже применённый в проекте к запрету календарных функций диалекта. Но контракт модуля аналитики (Фаза 4, план 04-01) в своём докстринге прямо объясняет: «не вызывает Docker SDK и вообще ничего синхронно-блокирующего — он живёт на пути рендера страницы». Объяснение запрета само нарушало запрет. Тест на подстроке заставил бы снять из докстринга самое ценное — ПРИЧИНУ, — и следующая правка вернула бы обращение обратно, не встретив ни одного возражения.
- **Fix:** Проверка перестроена на разбор синтаксического дерева: собираются имена, которые модуль ИМПОРТИРУЕТ и ВЫЗЫВАЕТ, и уже среди них ищутся SDK и сервис управления контейнерами. Дерево различает упоминание и обращение, а запрещено именно обращение. Причина отказа от поиска по тексту выписана в докстринге хелпера — иначе следующая правка вернула бы прежний приём. Невакуумность проверена отдельно: на `app/services/wa_container_manager.py` тот же разбор даёт три совпадения.
- **Files modified:** tests/test_pages/test_shell.py
- **Verification:** `test_dashboard_render_path_never_touches_docker` — passed; ручная проверка на настоящем владельце Docker-обращений даёт совпадения
- **Committed in:** 40128bd

**3. [Rule 3 - Blocking] Снятие блока унесло у дашборда шапку колонок, а два инвентаризационных теста этого не знали**

- **Found during:** Task 2 (прогон `tests/test_pages/`)
- **Issue:** План предписал снять запись снесённого шаблона из перечня `ROW_TEMPLATES_WITHOUT_HEADER`, но блок последних отправок был ЕДИНСТВЕННЫМ местом дашборда, вызывавшим шапку колонок. Вместе с ним `dashboard.html` перестал быть шаблоном с шапкой — и остался входом в таблице параметризации `ROWHEAD_PAGES`, а `test_dashboard_cell_labels_present` продолжал требовать подписи колонок у строки, которой больше нет.
- **Fix:** Вход дашборда снят из таблицы, тест подписей колонок снят вместе со своим кортежем меток, оба объявленных числа уменьшены до шести. Каждое снятие оформлено комментарием со ссылкой на этот план — ровно в том жанре, в каком там уже оформлены выходы шаблонов групп и расписаний, и с той же оговоркой: уменьшение числа есть признание СОЗНАТЕЛЬНОГО снятия, а молчаливое исчезновение шаблона с шапкой по-прежнему краснеет.
- **Files modified:** tests/test_pages/test_responsive_markup.py
- **Verification:** `test_rowhead_pages_all_have_a_parametrization_entry`, `test_row_templates_without_header_are_accounted_for` — passed; `tests/test_pages/ tests/test_templates/` — 606 passed
- **Committed in:** 8f03168

### Отступления от буквы плана (не автопочинка)

**4. Форма запроса ленты отличается от предписанной.** План называл `select(SendLog, Group)` с `outerjoin(Group, ...)` «формой текущего блока последних отправок». Реализована проекция шести колонок без соединения — обоснование выписано в разделе «Decisions Made» и в докстринге функции: ленте не нужна ни одна колонка `Group`, а маршрут горячий. Прочие предписания запроса (владение по `SendLog.user_id`, сортировка по убыванию `sent_at`, `limit`) исполнены дословно.

**5. Подпись `real-time` и заголовок блока живут в собственной шапке, а не в `card_open(title=...)`.** Парный макрос карточки ставит подпись ПОД заголовком, а макет — на ту же строку справа. Прецедент ровно этого отступления уже создан блоком heatmap в 04-04, и здесь он повторён, а не изобретён заново: `[data-feedhead]` устроен как `[data-heathead]`.

---

**Total deviations:** 3 auto-fixed (2 bug, 1 blocking) + 2 задокументированных отступления от буквы плана
**Impact on plan:** Две автопочинки из трёх — починка собственных артефактов задачи, обнаруженная первыми же прогонами. Третья обязательна: без неё снятие блока оставило бы два инвентаризационных теста красными. Объём не расширен: ни одного символа сверх перечисленных в «Artifacts this phase produces» не заведено.

## Issues Encountered

None — откатов не было; красных прогонов, кроме двух запланированных фаз RED и трёх автопочинок выше, не случилось.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Готово для 04-06:** пара блоков макета («Ближайшие отправки» / «Живая лента») собрана целиком; приём «строка целиком — ссылка» переиспользован во второй раз и устоялся.
- **Готово для Фазы 6:** `recent_feed` принимает `user_id` и `limit` параметрами, поэтому админка зовёт ту же функцию с идентификатором просматриваемого пользователя, не заводя своей выборки. Устройство бессрочного опроса (атрибуты на стабильном контейнере, подмена внутрь) описано в паршале и в разметке страницы — второй такой опрос строится по образцу, а не заново.
- **Открыто для 04-10 (чекпоинт):** фактическое тиканье опроса в живой вкладке за пределами нескольких интервалов и адаптивность блока ленты автотестами не подтверждаются — оба пункта уходят в чекпоинт того же плана, что и плитки из 04-01 и два блока из 04-04. Туда же уходит наблюдение, что плитки, heatmap и ближайшие отправки при этом НЕ обновляются (D-04).
- **DASH-03 и DASH-05 в REQUIREMENTS.md не отмечены НАМЕРЕННО:** оба идентификатора объявлены также планом 04-10, у которого сводки ещё нет. Отметка до его завершения показала бы требование закрытым, пока последний объявивший его план ещё идёт.
- **Не тронуто намеренно:** `app/pages/__init__.py` не изменён — роутер ленты в страничный роутер не включается, и ни один существующий маршрут не тронут. Граф `graphify-out/` в этом worktree отсутствует, поэтому `graphify update .` не выполнялся — граф обновляется в основном рабочем дереве после слияния.

## Known Stubs

None — заглушек не заведено. Лента читает настоящий журнал отправок, пустое состояние наступает только при действительно пустом наборе, а индикатор воркеров читается из существующего контракта шелла без единой подставленной величины.

## Self-Check: PASSED

- Все три созданных файла присутствуют на диске: `app/pages/dashboard_feed.py`, `app/templates/dashboard/partial_feed.html`, `app/templates/dashboard/includes/feed_row.html`.
- Удалённый шаблон отсутствует: в `app/templates/dashboard/includes/` остались `feed_row.html`, `heatmap.html`, `metric_tile.html`, `upcoming_row.html`.
- Все пять коммитов задач присутствуют в истории ветки: `92c80ac`, `38e2631`, `210aaf2`, `8f03168`, `40128bd`.
- Критерии приёмки перепроверены командами: `@router.get("/dashboard/feed"`, `FEED_LIMIT`, `FEED_POLL_SECONDS` — есть; включение роутера ленты в `app/main.py` — есть; `app/pages/__init__.py` в изменённых файлах отсутствует; атрибутов опроса в `partial_feed.html` — ноль совпадений; `macro feed_row` и ссылка `/history/` в `feed_row.html` — есть; `hx-swap="outerHTML"` на контейнере ленты — нет; имя снесённого шаблона в `test_responsive_markup.py` встречается ровно один раз и только комментарием-следом.
- Прогоны: `tests/test_pages/test_dashboard.py -k feed` — 10 passed; `tests/test_pages/test_htmx_preserved.py` — 24 passed, включая оба существующих теста самоостановки опроса на экране аккаунтов; `tests/test_pages/test_shell.py` — 96 passed; `tests/test_pages/ tests/test_templates/` — 606 passed; вся суита `uv run pytest tests/ -q` — **1218 passed** (было 1200: +20 новых, −2 снятых).
- Гейты TDD соблюдены на обеих строительных задачах: коммит `test(...)` предшествует коммиту `feat(...)`, оба присутствуют дважды. У закрепляющей задачи 3 гейт RED состоялся внутри одного коммита и задокументирован деviation 2.
- Невакуумность ключевых утверждений проверена отдельно: тест-шпион контекста шелла сначала утверждает своё срабатывание на самой странице; тест обращений к Docker проверен на настоящем владельце этих обращений.
- Новых поверхностей вне `<threat_model>` не появилось: заведён ровно один маршрут, названный в модели угроз, он закрыт гардом входа и владением в запросе, а название объявления и имя группы выводятся обычным экранированным выводом Jinja.

---
*Phase: 04-dashbord-i-istoriya*
*Completed: 2026-08-14*
