---
phase: 06-admin-panel
plan: 07
subsystem: ui
tags: [fastapi, jinja2, redis, celery, kombu, admin, ops, tdd]

requires:
  - phase: 06-admin-panel
    plan: 01
    provides: "app/services/ops_state.py — ленивый _get_redis как ЕДИНСТВЕННАЯ точка подмены Redis в суите; каркас шести подразделов и вкладки ADMIN_TABS"
  - phase: 06-admin-panel
    plan: 05
    provides: "Форма подраздела: страничный обработчик + сборщик контекста + блочная раскладка data-stack/data-blockhead; обработчик формы перезапуска как образец действия с гардом происхождения и закрытым множеством слов отказа"
  - phase: 01-interfeysnyy-fundament
    provides: "Общая панель подтверждения components/modal.html со слотом скрытых полей и гардом повторной отправки; примитивы [data-row] / cell() / rowhead()"
  - phase: 04-dashbord-i-istoriya
    provides: "normalize_utc — обязательное приведение момента перед всякой арифметикой над временем (SQLite отдаёт naive, PostgreSQL — aware)"
provides:
  - "app/application/admin/queue_rows.py — разбор тела задачи в строку подраздела: parse_delay_until с ЯВНЫМ каналом, queue_row_state (три состояния), queue_rows (потолок + признак), telegram_lag_seconds"
  - "QUEUE_ROW_CAP — потолок числа строк одной очереди с отдельным полем capped"
  - "ops_state.queue_page / telegram_queue_depth / drop_task — чтение очередей БЕЗ снятия и снятие одной задачи по идентификатору"
  - "DROP_REMOVED / DROP_MISSING / DROP_UNAVAILABLE — закрытое множество исходов снятия"
  - "app/templates/admin/includes/queue_row.html — строка очереди на тех же примитивах, что строка воркера"
  - "Страховочная сетка Ф-13: обход дерева, запрещающий передачу приоритета при постановке задач"
  - "[data-queue-row] .btn { min-height: 36px } — нажимаемость действия внутри строки (M3)"
affects: [06-08-logs, 06-10-overview, 06-11-payments]

actuals:
  # 117 993 символа реализованного диффа / 4. Шкала та же, что у `estimate`
  # плана (72 000), и это НЕ счётчик токенов раннера. Значение НЕ подтянуто к
  # оценке: план ПЕРЕоценил объём более чем вдвое, и записать это надо честно —
  # иначе следующая оценка ошибётся так же. Причина переоценки видна задним
  # числом: три задачи легли на уже существующие формы (сервис оперативного
  # состояния, форма подраздела, панель подтверждения), и изобретать пришлось
  # только разбор единиц времени.
  tokens: 29500
  tasks: 3
  commits: 7

tech-stack:
  added: []
  patterns:
    - "Разбор внешнего значения, зависящего от источника, принимает источник ЯВНЫМ аргументом без умолчания — умолчание делает молчаливо-ложную ветку достижимой по недосмотру"
    - "Двойник Redis в тестах держит НАСТОЯЩИЙ список: утверждение о снятии адресуется данным, а не факту вызова"
    - "Потолок перечня = константа + ОТДЕЛЬНОЕ поле срабатывания; вывод признака из длины объявил бы полный список усечённым"
    - "Необратимое действие адресуется идентификатором из формы, а точные байты удаляемого сервер берёт из СВОЕГО чтения"

key-files:
  created:
    - app/application/admin/queue_rows.py
    - app/templates/admin/includes/queue_row.html
    - tests/test_application/test_queue_rows.py
  modified:
    - app/services/ops_state.py
    - app/pages/admin.py
    - app/templates/admin/queue.html
    - app/static/css/app.css
    - tests/test_services/test_ops_state.py
    - tests/test_pages/test_admin_panel.py
    - tests/test_pages/test_responsive_markup.py
    - tests/test_templates/test_components.py

key-decisions:
  - "Величина канала telegram — время с ПОСЛЕДНЕЙ ЗАФИКСИРОВАННОЙ ОТПРАВКИ по журналу отправок, и подпись называет именно это; слово «лаг» из копирайт-контракта не использовано, потому что оно читается и как возраст самой старой задачи — величина, лежащая внутри конверта брокера и запрещённая к чтению решением D-14"
  - "При пустой очереди telegram величина не печатается вовсе: время с последней отправки на пустой очереди означает «работы не было», а не «работа стоит»"
  - "Снятие адресуется task_id, а не точным телом задачи (расхождение с Примером 5 исследования): тело несёт текст чужого объявления и может быть большим, а доверять клиенту байты удаляемого не нужно вовсе"
  - "Потолок чтения объявлен на единицу больше потолка показа: лишний прочитанный элемент — единственная улика усечения"
  - "Нечитаемое тело задачи считается отдельным полем unreadable и называется в разметке, а не пропускается молча"

patterns-established:
  - "Строка нового подраздела повторяет форму отгруженной строки соседнего подраздела дословно (примитив, cols, подписи по индексу), а не изобретает вторую"
  - "Инвентаризации проекта (адаптивная сетка, панель подтверждения) пополняются в том же коммите, что и новый шаблон: они существуют, чтобы новый файл краснел, а не растворялся"

requirements-completed: [ADMIN-08]

coverage:
  - id: D1
    description: "Отложенность задачи разбирается ПО КАНАЛУ: миллисекунды у WA, секунды у MAX; единая формула невозможна — канал обязателен"
    requirement: ADMIN-08
    verification:
      - kind: unit
        ref: "tests/test_application/test_queue_rows.py#test_wa_delay_until_written_in_milliseconds_reads_as_a_near_moment"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_queue_rows.py#test_max_delay_until_written_in_seconds_reads_as_a_near_moment"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_queue_rows.py#test_parse_delay_until_requires_the_channel_as_an_explicit_argument"
        status: pass
    human_judgment: false
  - id: D2
    description: "Свежепоставленная задача без полей повтора и отложенности рисуется ожиданием и не роняет разбор"
    requirement: ADMIN-08
    verification:
      - kind: unit
        ref: "tests/test_application/test_queue_rows.py#test_a_freshly_dispatched_task_reads_as_waiting"
        status: pass
    human_judgment: false
  - id: D3
    description: "Чтение очереди не снимает задачи; недоступный Redis возвращает признак, а не пустоту"
    requirement: ADMIN-08
    verification:
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_reading_a_queue_page_does_not_shorten_the_queue"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_an_unreachable_redis_is_named_and_not_shown_as_an_empty_queue"
        status: pass
    human_judgment: false
  - id: D4
    description: "Снятие удаляет РОВНО ОДНУ запись явной единицей, по идентификатору, байтами из своего чтения"
    requirement: ADMIN-08
    verification:
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_dropping_a_task_removes_exactly_one_entry_with_an_explicit_count"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_the_dropped_bytes_come_from_the_servers_own_read_not_from_the_form"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_dropping_a_queue_task_removes_exactly_one_and_comes_back"
        status: pass
    human_judgment: false
  - id: D5
    description: "Снятие не пишет в журнал отправок (D-18) и оставляет именованную строку журнала приложения"
    requirement: ADMIN-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_dropping_a_queue_task_writes_no_send_log_row"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_dropping_a_queue_task_leaves_a_named_application_log_line"
        status: pass
    human_judgment: false
  - id: D6
    description: "Форма снятия за правами администратора и за гардом происхождения запроса"
    requirement: ADMIN-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_dropping_a_queue_task_is_refused_to_an_outsider"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_dropping_a_queue_task_is_refused_when_it_comes_from_a_foreign_origin"
        status: pass
    human_judgment: false
  - id: D7
    description: "Действия, стирающего очередь целиком, нет ни в разметке, ни в маршрутах (D-17)"
    requirement: ADMIN-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_no_wholesale_queue_wipe_exists_in_the_markup_or_in_the_routes"
        status: pass
    human_judgment: false
  - id: D8
    description: "Подсчёт задач канала telegram остаётся полным: приоритет при постановке задач запрещён тестом (Ф-13)"
    requirement: ADMIN-08
    verification:
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_no_dispatch_call_in_the_project_passes_a_priority"
        status: pass
    human_judgment: false
  - id: D9
    description: "Потолок перечня называет себя; пустая очередь и недоступный Redis — разная разметка; ячейки несут подписи колонок на узких экранах"
    requirement: ADMIN-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_a_capped_queue_list_says_so_instead_of_just_showing_fewer_rows"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_an_empty_queue_and_an_unreachable_redis_are_different_markup"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_rowhead_titles_are_covered_by_labels[admin/queue.html]"
        status: pass
    human_judgment: false
  - id: D10
    description: "Подпись величины канала telegram называет ИМЕННО измеренное и не читается как возраст самой старой задачи"
    requirement: ADMIN-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_the_telegram_queue_block_names_exactly_what_its_number_measures"
        status: pass
    human_judgment: true
    rationale: "Тест закрепляет наличие подписи и отсутствие запрещённого прочтения буквой, но НЕ может ответить, отвечает ли выбранная величина на вопрос владельца. Планировщик флагировал это допущение явно: если под «лагом» D-14 понимался возраст самой старой задачи, величина выбрана не та — и это правка ROADMAP, а не исполнения."
  - id: D11
    description: "Подраздел пригоден к использованию на 375px: строки складываются без горизонтальной прокрутки, действие в строке нажимаемо"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_rowhead_titles_are_covered_by_labels[admin/queue.html]"
        status: pass
    human_judgment: true
    rationale: "Браузерного харнесса в проекте нет: подписи колонок и правило min-height проверены арифметикой по CSS и разбором разметки, но фактическая читаемость экрана на 375px — критерий приёмки фазы, и он снимается глазами."

duration: 78min
completed: 2026-08-22
status: complete
---

# Phase 06 Plan 07: Подраздел «Очередь» Summary

**Подраздел показывает, что ждёт отправки по трём каналам, разбирая отложенность задачи ПО КАНАЛУ (миллисекунды у WA, секунды у MAX), и даёт снять одну конкретную задачу по идентификатору — не имея кнопки, стирающей очередь целиком.**

## Performance

- **Duration:** 78 min
- **Started:** 2026-08-22T18:21:11Z
- **Completed:** 2026-08-22T19:39:08Z
- **Tasks:** 3
- **Files modified:** 12 (3 создано, 9 изменено)

## Accomplishments

- **Главная ловушка плана закрыта тестом, а не намерением.** WA пишет `_delay_until` в миллисекундах, MAX — в секундах; единая формула не падает, она рисует правдоподобную дату («до 55-го тысячелетия» либо «до 1970 года»). Канал стал ОБЯЗАТЕЛЬНЫМ аргументом разбора без умолчания, и оба случая закреплены тестами на настоящих телах задач, падающими по отдельности. Третий тест утверждает, что одно и то же число даёт по двум каналам РАЗНЫЕ годы — то есть адресован самой возможности единой формулы.
- **Чтение очереди ничего не снимает.** `LRANGE` диапазоном вместо `LPOP`; двойник Redis в тестах роняет тест при любом вызове снимающей команды, а утверждения адресованы содержимому списка, а не факту вызова.
- **Снятие удаляет ровно одну запись, найденную по идентификатору.** Форма несёт `task_id`, точные байты сервер берёт из своего чтения (T-06-DROP2); количество удаляемых — явная единица, а не вывод из уникальности uuid4. Записи в журнал отправок нет (D-18), след — именованная строка журнала приложения.
- **Величина канала брокера названа тем, что измерено.** Число задач читается длиной ключа без распаковки конверта; вторая величина — время с последней зафиксированной отправки по журналу отправок, и при пустой очереди она не печатается вовсе.
- **Три вещи, которые молчат, заставлены говорить:** сработавший потолок (`Показаны первые 50 задач из 57`), нечитаемое тело задачи, недоступный Redis. Каждая называет себя словами; пустая очередь и сломанный наблюдатель дают РАЗНУЮ разметку.
- **День, когда счёт очереди telegram перестанет быть полным, поймает тест.** Обход дерева по всем вызовам постановки задач запрещает передачу приоритета: с ненулевым приоритетом kombu раскладывает задачи по ключам с суффиксами, и подраздел начал бы недосчитывать без единого признака.

## Task Commits

1. **Задача 1: Разбор строки очереди** — `b33c521` (test, RED) → `364a24e` (feat, GREEN)
2. **Задача 2: Чтение очередей и снятие одной задачи** — `c94cb7b` (test, RED) → `c603076` (feat, GREEN)
3. **Задача 3: Подраздел «Очередь»** — `40f6701` (test, RED) → `5b73c4e` (feat, GREEN) → `73620c2` (test, инвентаризация панели подтверждения)

REFACTOR-коммитов нет: ни на одном из трёх циклов очевидного упрощения после GREEN не нашлось, а коммит ради коммита сообщал бы о работе, которой не было.

## Files Created/Modified

- `app/application/admin/queue_rows.py` — **создан.** Чистый разбор тела задачи: `parse_delay_until` (канал явным аргументом), `queue_row_state` (три состояния), `queue_rows` (потолок + признак), `telegram_lag_seconds`, `QUEUE_ROW_CAP`
- `app/services/ops_state.py` — `queue_page`, `telegram_queue_depth`, `drop_task`, `QueuePage`, три исхода снятия, `TELEGRAM_QUEUE_KEY`
- `app/pages/admin.py` — обработчик подраздела, обработчик формы снятия, `QUEUE_CHANNELS`, `QUEUE_DROP_RESULTS`, `QUEUE_READ_LIMIT`
- `app/templates/admin/queue.html` — три блока, плашки исхода и недоступности, панели подтверждения вне строк
- `app/templates/admin/includes/queue_row.html` — **создан.** Строка на тех же примитивах, что строка воркера
- `app/static/css/app.css` — `[data-queue-row] .btn { min-height: 36px }` (M3), голый `.btn` не тронут
- `tests/test_application/test_queue_rows.py` — **создан.** 12 тестов
- `tests/test_services/test_ops_state.py` — +8 тестов (27 в файле)
- `tests/test_pages/test_admin_panel.py` — +12 тестов подраздела
- `tests/test_pages/test_responsive_markup.py` — вход `admin/queue.html` в таблицу параметризации, строка очереди в перечень макросов без шапки, оба счётчика 6 → 7
- `tests/test_templates/test_components.py` — три счёта панели подтверждения 10/7/16 → 11/8/17

## Decisions Made

**1. Подпись величины канала telegram отступает от буквы копирайт-контракта — и это выбор в пользу его же правила.**
`06-UI-SPEC.md` § Очередь (S3) задаёт заголовок блока как `Telegram: {N} задач, лаг {M} с`. Слово «лаг» не использовано. Причина: оно читается двояко, и второе прочтение — «возраст самой старой задачи» — описывает величину, которая лежит ВНУТРИ конверта брокера и запрещена к чтению решением D-14. Подпись, допускающая прочтение, для которого в подразделе нет источника, была бы «измеренной на вид выдумкой» — ровно тем, что запрещает правило контракта «отсутствие величины называет причину» и требование самого плана («⚠️ ПОДПИСЬ ОБЯЗАНА НАЗЫВАТЬ ИМЕННО ЭТО»). Напечатано: `с последней отправки по каналу — {M} с`, с подсказкой, называющей источник (журнал отправок) и явно отрицающей второе прочтение. Правка контракта требуется — см. «Next Phase Readiness».

**2. Снятие адресуется идентификатором, а не точным телом.**
`06-RESEARCH.md` § Code Examples, Пример 5 показывает `drop_task(r, channel, account_id, raw_body)` — тело приходит из формы. Реализовано иначе, по указанию задачи 2 плана и реестра угроз (T-06-DROP2): форма несёт `task_id`, сервер читает страницу очереди сам и удаляет те байты, которые прочитал. Тело задачи содержит текст чужого объявления и может быть большим; кроме того, поле формы с точными байтами удаляемого — это доверие клиенту там, где его можно не оказывать вовсе.

**3. Потолок чтения на единицу больше потолка показа.**
`QUEUE_READ_LIMIT = QUEUE_ROW_CAP + 1`. Лишний элемент не печатается — он и есть улика усечения: без него «прочитано ровно 50» было бы неотличимо от «в очереди ровно 50», и признак `capped` пришлось бы выводить из длины, объявляя полный список усечённым.

**4. Нечитаемое тело задачи считается и называется.**
`QueuePage.unreadable` — отдельное поле. Битое тело не имеет права ни уронить подраздел (тогда одна задача спрятала бы все остальные), ни исчезнуть молча (тогда оно укоротило бы список ровно так же, как потолок). В разметке — своя строка с числом.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Инвентаризация адаптивной сетки не знала о новых шаблонах**

- **Found during:** Задача 3
- **Issue:** `tests/test_pages/test_responsive_markup.py` держит двустороннюю инвентаризацию: множество шаблонов с шапкой колонок обязано совпадать с таблицей параметризации, множество макросов строки без шапки — с названным перечнем. Оба новых файла в них отсутствовали, и обе проверки покраснели. Это сработавший, а не сломанный гард: он для того и написан, чтобы новый файл не растворялся.
- **Fix:** Добавлен вход `RowheadPage("admin/queue.html", …, ops_state=True)` с ожидаемой разностью подписей `frozenset()` (подписаны все четыре колонки) и своим наполнением `admin_queue`; `admin/includes/queue_row.html` внесён в перечень макросов строки первым классом причины. Оба счётчика подняты 6 → 7 с записанной причиной. Появилось новое поле входа `ops_state`: шапка подраздела рисуется только над непустой очередью, а очередь живёт в Redis — без подмены вход зеленел бы вакуумно, утверждая про вёрстку, которой на экране нет.
- **Files modified:** `tests/test_pages/test_responsive_markup.py`
- **Verification:** `uv run pytest tests/test_pages/test_responsive_markup.py -q` — 130 passed
- **Committed in:** `5b73c4e`

**2. [Rule 3 - Blocking] Инвентаризация панели подтверждения не знала о новом потребителе**

- **Found during:** Полный прогон суиты после задачи 3
- **Issue:** `tests/test_templates/test_components.py` сводит три независимых счёта панели подтверждения (импортёры, имена события, места применения). Снятие задачи добавило по единице к каждому, и обе проверки покраснели.
- **Fix:** `MODAL_IMPORTERS` 10 → 11, `MODAL_EVENT_NAMES` 7 → 8, `MODAL_PLACES` 16 → 17; `admin/queue.html` внесён в `MODAL_CONSUMERS` с причиной размещения (панель собирает страница, строка только диспетчеризует событие). Числа получены счётом по файлам после правки.
- **Files modified:** `tests/test_templates/test_components.py`
- **Verification:** `uv run pytest tests/test_templates/test_components.py -q` — 45 passed
- **Committed in:** `73620c2`

**3. [Rule 2 - Missing Critical] Признак нечитаемого тела задачи**

- **Found during:** Задача 2
- **Issue:** План не оговаривал, что делать с телом задачи, которое не разбирается как JSON. Тихий пропуск укоротил бы список ровно так же, как потолок, — то есть ответил бы «остальных задач нет»; исключение спрятало бы за одной битой задачей все остальные.
- **Fix:** Поле `QueuePage.unreadable` со счётом пропущенных, строка журнала и отдельная подпись в разметке.
- **Files modified:** `app/services/ops_state.py`, `app/templates/admin/queue.html`
- **Verification:** Покрыто разбором в `queue_page`; путь не роняет ни один из 27 тестов файла
- **Committed in:** `c603076`, `5b73c4e`

**4. [организационное] `telegram_lag_seconds` заведена в `queue_rows.py`, а не в файле, названном задачей**

- **Found during:** Задача 3
- **Issue:** Таблица артефактов плана допускает `telegram_lag()` в `app/services/ops_state.py` ЛИБО в `app/application/admin/queue_rows.py`, но перечень файлов задачи 3 ни того, ни другого не называет.
- **Fix:** Функция заведена в `queue_rows.py` — сервис оперативного состояния читает только Redis, и арифметика над моментом из БД в нём была бы не на месте. Файл входит в `files_modified` плана.
- **Files modified:** `app/application/admin/queue_rows.py`
- **Committed in:** `5b73c4e`

---

**Total deviations:** 4 (2 blocking, 1 missing critical, 1 организационное)
**Impact on plan:** Обе блокирующие правки — это СРАБОТАВШИЕ гарды проекта, а не поломки: они существуют, чтобы новый шаблон был назван, а не растворился. Расширения объёма нет.

## Issues Encountered

**Две клиентские фикстуры суиты наращивают ОДИН экземпляр клиента.** Первая редакция теста «200 админу и 403 постороннему» запрашивала `admin_client` и `authed_client` в одном тесте; вход посторонним подменяет cookie администратора, и утверждение про 200 проверяло бы права не того, кого называет. Тесты разведены по одному клиенту на тест, причина записана в докстроке.

**`grep`-критерии приёмки считают вхождения и в комментариях.** Критерий требует нуля вхождений признаков стирания очереди в `app/pages/admin.py` и `app/templates/admin/queue.html`, а объяснить отсутствие кнопки в этих же файлах надо. Объяснения переформулированы так, чтобы называть предмет, не набирая запрещённой строки, — тот же приём, которым план 06-01 закрыл объяснение отсутствия обращения к демону контейнеров.

## Known Stubs

Нет. Все напечатанные величины подключены к источникам; заглушек, нарисованных «до следующего плана», подраздел не содержит.

## Pre-existing Failures (не относятся к этому плану)

- `tests/test_pages/test_ads_editor.py::test_image_base_url_comes_from_app_settings` — известный дефект фазы, записан в `deferred-items.md`, воспроизводится на базовом коммите.
- `tests/test_planning/test_state_progress_matches_roadmap.py::test_the_machine_readable_progress_is_derived_from_the_roadmap` — `progress.completed_plans` в `STATE.md` записан как 99, а из отметок `ROADMAP.md` выводится 102. Расхождение существует НА БАЗОВОМ КОММИТЕ волны: ни `STATE.md`, ни `ROADMAP.md` этим планом не изменялись (исполнителю волны это прямо запрещено — оба файла принадлежат оркестратору). Приводить надо поле в `STATE.md`, и это работа оркестратора при закрытии волны.

## Threat Flags

Нет новой поверхности сверх объявленной в реестре угроз плана. Форма снятия — единственная изменяющая точка, и она закрыта проверкой прав, гардом происхождения и удалением одной записи по идентификатору из собственного чтения.

## User Setup Required

None — внешних служб подраздел не добавляет. Redis уже настроен проектом; его недоступность подраздел переживает плашкой.

## Next Phase Readiness

- **Требуется правка `06-UI-SPEC.md` § Copywriting Contract, S3** (или подтверждение владельца): строка «Заголовок TG-блока | `Telegram: {N} задач, лаг {M} с`» отгружена в виде, называющем измеренную величину явно. Если под «лагом» D-14 понимался возраст самой старой задачи, вопрос решается не правкой подписи, а правкой D-14 — этот возраст требует распаковки конверта брокера, которую то же решение запрещает. Планировщик флагировал допущение заранее; исполнение его не сняло, а только исполнило в самой честной из двух форм.
- `queue_page` и `QUEUE_ROW_CAP` готовы к переиспользованию плитой «Задач в очереди» подраздела «Обзор» (D-37, план 06-10): сумма трёх источников считается теми же тремя вызовами.
- `telegram_lag_seconds` — та же величина, что понадобится плите обзора; своей арифметики над временем плану 06-10 заводить не нужно.

## Self-Check: PASSED

- Созданные файлы существуют: `app/application/admin/queue_rows.py`, `app/templates/admin/includes/queue_row.html`, `tests/test_application/test_queue_rows.py`, `.planning/phases/06-admin-panel/06-07-SUMMARY.md`
- Все семь коммитов присутствуют в истории ветки: `b33c521`, `364a24e`, `c94cb7b`, `c603076`, `40f6701`, `5b73c4e`, `73620c2`
- `just test` — 1911 passed, 2 failed; оба падения ПРЕДСУЩЕСТВУЮЩИЕ и разобраны выше в разделе «Pre-existing Failures». До правок этого плана падало три (третье — инвентаризация панели подтверждения — было следствием плана и закрыто коммитом `73620c2`).

---
*Phase: 06-admin-panel*
*Completed: 2026-08-22*
