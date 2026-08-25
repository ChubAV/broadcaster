---
phase: 06-admin-panel
plan: 01
subsystem: ui
tags: [fastapi, jinja2, redis, htmx-free-navigation, ops, admin]

requires:
  - phase: 01-shell
    provides: "Контракт «страница → шелл»: заголовок раздела по active_page, признак is-active в сайдбаре, базовый путь без JS"
  - phase: 05.1-access
    provides: "Форма ленивого модульного клиента Redis и его подмены в суите (app/services/billing_cache.py, tests/test_billing_cache.py)"
provides:
  - "app/services/ops_state.py — публичная точка чтения оперативного состояния из Redis для веб-процесса"
  - "Возрастной предикат свежести heartbeat и порог MAX_HEARTBEAT_STALE_SEC = 90, переиспользованный из max_container_manager"
  - "worker_liveness(): живость и глубина очереди всех аккаунтов одним pipeline, четыре состояния (online/idle/offline/unknown)"
  - "ADMIN_TABS — единственное объявление перечня шести подразделов админ-панели"
  - "Шесть достижимых маршрутов подразделов с вкладками-ссылками, работающими при выключенном JS"
  - "Подраздел «Воркеры» на живых данных с ДВУМЯ независимыми колонками состояния"
  - "Примитив вкладок подраздела [data-subtabs] / .subtab в app.css"
  - "Снесённая поверхность справочника групп и записанный частичный вердикт ADMIN-02"
affects: [06-05-workers-infra, 06-07-queue, 06-08-logs, 06-09-users, 06-10-overview, 06-11-payments]

actuals:
  # 122 640 символов реализованного диффа / 4. Шкала та же, что у `estimate`
  # плана (78 000), и это НЕ счётчик токенов раннера. Значение не округлено в
  # сторону оценки: приукрашенное число испортило бы каждую следующую.
  tokens: 31000
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Подраздел админ-панели = маршрут, а не состояние экрана: вкладки — ссылки без HTMX/Alpine"
    - "Живость воркера = сравнение ВОЗРАСТА heartbeat с порогом, никогда не EXISTS"
    - "Ленивая ИМЕНОВАННАЯ точка получения клиента Redis как единственная точка подмены в суите"
    - "Сводка по всем аккаунтам одним pipeline вместо запроса на строку"

key-files:
  created:
    - app/services/ops_state.py
    - app/templates/admin/includes/_tabs.html
    - app/templates/admin/includes/worker_row.html
    - app/templates/admin/workers.html
    - app/templates/admin/queue.html
    - app/templates/admin/logs.html
    - app/templates/admin/payments.html
    - tests/test_services/test_ops_state.py
    - tests/test_pages/test_admin_panel.py
  modified:
    - app/pages/admin.py
    - app/templates/admin/overview.html
    - app/templates/admin/users.html
    - app/static/css/app.css
    - tests/test_pages/test_shell.py
    - tests/test_pages/test_responsive_markup.py
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Порог свежести heartbeat взят из уже объявленного MAX_HEARTBEAT_STALE_SEC = 90, а не заведён новым числом: дискреционные «около 60 секунд» закрыты существующим значением"
  - "worker_liveness сама зовёт _get_redis, а не принимает клиент параметром — иначе «неизвестно» при недоступном Redis было бы невыразимо внутри сервиса"
  - "Признак активной вкладки — свой атрибут data-subtab-active, а не is-active сайдбара и не aria-current нижних табов: чужие признаки уже заняты шеллом"
  - "Примитив вкладок назван [data-subtabs], а не [data-tabs]: последний занят мобильной нижней навигацией шелла и утащил бы вкладки вниз экрана"
  - "Вкладки переносятся по строкам, а не прокручиваются горизонтально: на 375px прокручиваемая полоса прятала бы последние подразделы"
  - "Строка телеграм-аккаунта печатает прочерк в колонке «Воркер» с подписью «величина ещё не определена» — выдуманный бейдж читался бы как измеренное состояние"
  - "Шаблон вкладок обходит ADMIN_TABS циклом, а не выписывает шесть ссылок: второй копии подписей в проекте не заводится (см. деривацию 1)"

patterns-established:
  - "Каркас подраздела: extends base.html → include admin/includes/_tabs.html → содержимое; заголовок рисует шапка шелла по active_page"
  - "Пустое состояние нового подраздела несёт ЧЕСТНУЮ подпись «раздел наполняется», а не данные-заглушки макета"
  - "Разделение «состояние сессии из базы» и «живость воркера из Redis» на две независимые колонки — сводить нельзя"

requirements-completed: [ADMIN-03, ADMIN-07]

coverage:
  - id: D1
    description: "Шесть подразделов админ-панели достижимы отдельными маршрутами: 200 администратору, 403 постороннему"
    requirement: ADMIN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_six_subsections_answer_the_admin"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_six_subsections_denied_for_regular_user"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#ADMIN_SHELL_ROUTES (обход шелла по шести адресам)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Переключение подраздела работает при выключенном JS: вкладки — шесть ссылок без HTMX и Alpine"
    requirement: ADMIN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_subsection_navigation_degrades_without_js"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_tabs_render_six_real_links"
        status: pass
      - kind: unit
        ref: "grep -Ec 'hx-|x-on:|x-data' app/templates/admin/includes/_tabs.html == 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "Текущий подраздел отмечен ровно один раз, раздел «Админ-панель» подсвечен в сайдбаре на всех шести адресах"
    requirement: ADMIN-03
    verification:
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_active_subsection_is_marked_exactly_once"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_admin_section_stays_highlighted_in_the_sidebar"
        status: pass
    human_judgment: false
  - id: D4
    description: "Живость воркера читается сравнением ВОЗРАСТА heartbeat с порогом 90 с: стухший ключ без TTL читается мёртвым, heartbeat из будущего — несвежим"
    requirement: ADMIN-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_stale_heartbeat_without_ttl_reads_dead"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_future_heartbeat_reads_stale_not_just_now"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_non_numeric_and_missing_heartbeat_read_stale_without_raising"
        status: pass
    human_judgment: false
  - id: D5
    description: "Простой и отказ различены честно: пустая очередь без heartbeat — «простаивает», непустая — «отключён»"
    requirement: ADMIN-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_stale_heartbeat_with_empty_queue_is_idle_not_offline"
        status: pass
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_stale_heartbeat_with_pending_queue_is_offline"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_workers_subsection_shows_idle_account_row"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_workers_subsection_shows_offline_only_with_pending_queue"
        status: pass
    human_judgment: false
  - id: D6
    description: "Недоступный Redis не роняет подраздел: 200 и состояние «неизвестно» вместо ложного отказа (T-06-02)"
    requirement: ADMIN-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_liveness_summary_returns_unknown_when_redis_unavailable"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_admin_panel.py#test_workers_subsection_survives_unavailable_redis"
        status: pass
    human_judgment: false
  - id: D7
    description: "Docker при рендере подраздела не вызывается — утверждение снято разбором исходника по синтаксическому дереву (T-06-03)"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_admin_panel.py#test_no_docker_client_on_the_render_path"
        status: pass
      - kind: unit
        ref: "grep -Ec 'docker|_get_docker_client' app/pages/admin.py == 0"
        status: pass
    human_judgment: false
  - id: D8
    description: "Сводка живости уходит ОДНИМ round-trip с корректными именами ключей обоих каналов"
    requirement: ADMIN-07
    verification:
      - kind: unit
        ref: "tests/test_services/test_ops_state.py#test_liveness_summary_uses_single_pipeline_round_trip"
        status: pass
    human_judgment: false
  - id: D9
    description: "Экраны справочника групп снесены, хранилище цело, ни один шаблон и ни один маршрут не ведёт на снесённый адрес (D-05)"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_admin_panel.py#test_groups_info_gone_from_templates_and_routes"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_admin_panel.py#test_groups_info_gone_but_its_storage_survived"
        status: pass
    human_judgment: false
  - id: D10
    description: "Частичный вердикт ADMIN-02 записан в реестре требований с датой и основанием, строка прослеживаемости сохранена"
    verification:
      - kind: manual_procedural
        ref: "grep -n 'ADMIN-02' .planning/REQUIREMENTS.md — четыре вхождения: дерево, строка прослеживаемости, счётчик Partial, журнал изменений"
        status: pass
    human_judgment: false
  - id: D11
    description: "Все шесть подразделов пригодны к использованию на ширине 375 пикселей: горизонтального переполнения нет, вкладки достижимы"
    verification: []
    human_judgment: true
    rationale: "Истина объявлена планом как `verification: backstop` — вёрстка на реальной ширине проверяется глазами. Автоматика закрывает соседнее: примитив строки, подписи ячеек и отсутствие utility-классов держатся сеткой test_responsive_markup.py, а перенос вкладок по строкам вместо горизонтальной прокрутки исключает переполнение конструктивно. Само отсутствие переполнения на 375px в браузере не измерено."

duration: 2h 5m
completed: 2026-08-22
status: complete
---

# Phase 6 Plan 01: Каркас админ-панели и трассирующий срез «Воркеры» Summary

**Админ-панель стала шестью настоящими маршрутами со вкладками-ссылками, работающими без JS, а подраздел «Воркеры» доведён до конца через все слои фазы — от нового сервиса чтения Redis с возрастным предикатом свежести heartbeat до строки с двумя независимыми колонками состояния.**

## Performance

- **Duration:** 2h 5m (включая два полных прогона суиты по ~19 минут)
- **Started:** 2026-08-22T05:30Z (приблизительно; первый коммит 05:51:38Z)
- **Completed:** 2026-08-22T07:35Z
- **Tasks:** 3 из 3
- **Files modified:** 20 (9 создано, 8 изменено, 3 удалено)

## Accomplishments

- **Три архитектурных решения фазы закреплены на одной строке одного подраздела — до того, как от них начали зависеть двенадцать остальных планов.** Подраздел есть маршрут (проверено отсутствием клиентских библиотек в разметке вкладок), Docker при рендере не зовётся (проверено разбором синтаксического дерева, а не наблюдением), у сервиса есть ленивая ИМЕНОВАННАЯ точка подмены (без неё подраздел был бы непроверяем на суите без внешних служб).
- **Живость воркера измеряется сравнением ВОЗРАСТА heartbeat с порогом 90 секунд, а не существованием ключа.** Это и есть предмет трассера: у WA-воркера heartbeat пишется без TTL и удаляется только при штатном завершении, поэтому убитый жёстко воркер оставляет ключ навсегда — проверка `EXISTS` показывала бы мёртвый воркер живым бессрочно, и именно в аварии, ради которой подраздел открывают.
- **Простой отделён от отказа честно (D-08).** Состояний три плюс неизвестность: «в работе» — heartbeat свеж; «простаивает» — несвеж И очередь пуста (штатное состояние, воркер уходит сам через 300 секунд); «отключён» — несвеж И очередь непуста; «неизвестно» — сломан наблюдатель, а не воркер.
- **Экраны справочника групп снесены с вердиктом, а не молча.** Основание — факт: у таблицы нет производителя, метод записи репозитория не вызывается ниоткуда в приложении. Хранилище (таблица, модель, репозиторий, ревизия `0011`) не тронуто намеренно, а частичный вердикт ADMIN-02 записан в реестре требований с датой, основанием и СОХРАНЁННОЙ строкой прослеживаемости.

## Task Commits

1. **Задача 1: Сервис оперативного состояния (TDD)** — `61f82c9` (test, RED) → `c0dd6ab` (feat, GREEN)
2. **Задача 2: Трассирующий срез — шесть маршрутов, вкладки и «Воркеры»** — `67bcd6a` (feat, tracer)
3. **Задача 3: Снос справочника групп и частичный вердикт ADMIN-02** — `66ccd82` (feat)

_REFACTOR-коммита у задачи 1 нет: реализация после GREEN не потребовала правки — модуль скопирован по форме уже существующего `billing_cache.py`._

## Files Created/Modified

- `app/services/ops_state.py` — единственная точка чтения оперативного состояния из Redis для веб-процесса: ленивый `_get_redis()`, возрастной предикат `_is_fresh()`, порог `MAX_HEARTBEAT_STALE_SEC = 90`, сводка `worker_liveness()` одним pipeline
- `app/pages/admin.py` — `ADMIN_TABS` (единственное объявление перечня), `_admin_context()`, пять новых обработчиков подразделов; сняты два обработчика справочника групп и импорт его репозитория
- `app/templates/admin/includes/_tabs.html` — вкладки шести подразделов ссылками, обходом `ADMIN_TABS`
- `app/templates/admin/includes/worker_row.html` — строка воркера с двумя независимыми колонками состояния и объяснением выбора слов
- `app/templates/admin/workers.html` — подраздел «Воркеры» на примитиве строки-таблицы
- `app/templates/admin/{queue,logs,payments}.html` — каркасы с честным пустым состоянием
- `app/templates/admin/overview.html` — переименован из `dashboard.html`; добавлены вкладки, снята кнопка-вход в справочник
- `app/templates/admin/users.html` — добавлены вкладки (единственная правка; шаблон переписывает план 06-09)
- `app/static/css/app.css` — примитив `[data-subtabs]` / `.subtab`
- `tests/test_services/test_ops_state.py` — 12 тестов сервиса, ни один не требует поднятого Redis
- `tests/test_pages/test_admin_panel.py` — 17 тестов каркаса, трассера и страховочной сетки сноса
- `tests/test_pages/test_shell.py`, `tests/test_pages/test_responsive_markup.py` — перечни админских адресов и таблицы параметризации приведены к шести подразделам
- `.planning/REQUIREMENTS.md` — частичный вердикт ADMIN-02, пересчитанные счётчики v1, строка журнала изменений

**Удалены:** `app/templates/admin/groups_info.html`, `app/templates/admin/group_info_detail.html`, `tests/test_pages/test_admin_groups_info.py`.

## Decisions Made

Все решения перечислены в `key-decisions` фронтматтера. Два требуют развёрнутого обоснования:

**Гейт трассера пройден автоматически, а не чекпойнтом владельца.** Конфигурация проекта несёт `mode: yolo` при `workflow.auto_advance: false`, план — `autonomous: true`, а исполнитель работает в изолированном worktree и с человеком взаимодействовать не может. Гейт исполнен в автономной форме, объявленной протоколом: `<verify>` трассера прогнан целиком после его коммита и ДО первой расширяющей работы — три команды, все зелёные (`test_admin_panel.py` 15 тестов, срез `-k "tabs or degrades or no_docker_on_render"` 3 теста, `test_shell.py` + `test_admin.py` 135 тестов). Задача 3 начата только после этого.

**Порог свежести не заведён новым числом.** Дискреционное «около 60 секунд» из обсуждения закрыто уже объявленным `MAX_HEARTBEAT_STALE_SEC = 90` из `max_container_manager.py`. Второе число на вопрос «жив ли воркер» разошлось бы с первым молча.

## Deviations from Plan

### 1. [Rule 3 — Блокирующее] Критерий приёмки `grep -c 'href' _tabs.html >= 6` невыполним одновременно с правилом единственного объявления перечня

- **Найдено при:** Задача 2
- **Проблема:** критерий считает СТРОКИ файла, содержащие `href`. Шаблон, обходящий `ADMIN_TABS` циклом, содержит ровно одну такую строку. Выписать шесть ссылок литералами значило бы завести вторую копию подписей и адресов — прямо против текста задачи («Перечень объявляется ОДИН раз и читается и обработчиками, и разметкой вкладок»), против `key_links` (`pattern: _tabs.html`) и против объявленного риска «вторая копия разъехалась бы с первой молча».
- **Решение:** сохранено правило единственного объявления (несущее решение, подтверждённое двумя другими местами плана), а утверждение критерия перенесено на СТРОГО БОЛЕЕ СИЛЬНУЮ проверку по ОТДАННОЙ разметке: `test_tabs_render_six_real_links` требует ровно шесть якорей `<a class="subtab" href="...">` с адресами, поэлементно равными `ADMIN_TABS`, плюс присутствие всех шести подписей. Греп по файлу проверял бы наличие шести строк с `href` где угодно, включая закомментированные; тест проверяет шесть настоящих ссылок в настоящей выдаче.
- **Файлы:** `app/templates/admin/includes/_tabs.html`, `tests/test_pages/test_admin_panel.py`
- **Проверка:** `uv run pytest tests/test_pages/test_admin_panel.py -k tabs` — зелёный; `grep -Ec 'hx-|x-on:|x-data' app/templates/admin/includes/_tabs.html` = 0
- **Коммит:** `67bcd6a`

### 2. [Rule 1 — Дефект] Критерий `grep -Ec 'docker' app/pages/admin.py == 0` роняла собственная докстрока обработчика

- **Найдено при:** Задача 2
- **Проблема:** докстрока `admin_workers` ссылалась на имя теста `test_no_docker_on_render`, и страховочный греп считал это вхождение. Ровно тот дефект, о котором предупреждает сам план: «поиск считает вхождение и в комментарии, и в докстринге».
- **Решение:** ссылка переписана на файл теста без имени клиента контейнеров; рядом поставлено объяснение, ПОЧЕМУ имя не выписывается — иначе следующий автор вернёт его обратно.
- **Файлы:** `app/pages/admin.py`
- **Проверка:** `grep -Eic 'docker' app/pages/admin.py` = 0 (проверено и без учёта регистра)
- **Коммит:** `67bcd6a`

### 3. [Rule 3 — Блокирующее] Сетка адаптивной вёрстки не знала о новых шаблонах и роняла два теста

- **Найдено при:** Задача 2
- **Проблема:** `test_rowhead_pages_all_have_a_parametrization_entry` и `test_row_templates_without_header_are_accounted_for` требуют, чтобы КАЖДЫЙ новый шаблон с шапкой колонок и каждый макрос строки были названы поимённо. `admin/workers.html` и `admin/includes/worker_row.html` в перечнях отсутствовали — по построению этих тестов, а не по ошибке.
- **Решение:** оба файла внесены в таблицы параметризации с классом причины; заведено наполнение `admin_workers`, посевающее ТЕЛЕГРАМ-аккаунт намеренно — у него нет отдельного воркера, поэтому сводка живости не делает ни одного обращения к Redis и проверка вёрстки не зависит от внешней службы.
- **Файлы:** `tests/test_pages/test_responsive_markup.py`
- **Проверка:** `uv run pytest tests/test_pages/test_responsive_markup.py -k "rowhead or row_templates"` — 10 тестов зелёные
- **Коммит:** `67bcd6a`

### 4. [Rule 3 — Блокирующее] Счётчики тех же таблиц после сноса справочника вернулись к прежним числам

- **Найдено при:** Задача 3
- **Проблема:** оба теста утверждают ЧИСЛО объявленных шаблонов. Задача 2 подняла его с 6 до 7, задача 3 сносом справочника вернула к 6 — итог совпал с исходным, и правка выглядела бы как её отсутствие.
- **Решение:** числа возвращены к 6, но рядом записано, что совпадение есть арифметика ДВУХ разных шагов (+1 «Воркеры», −1 справочник), а не отсутствие изменений. Без этой записи следующий автор прочитал бы неизменное число как «таблицу не трогали».
- **Файлы:** `tests/test_pages/test_responsive_markup.py`
- **Проверка:** те же 10 тестов сетки — зелёные
- **Коммит:** `66ccd82`

### 5. [Rule 3 — Блокирующее] Посевная функция справочника и её импорт осиротели после удаления тестов

- **Найдено при:** Задача 3
- **Проблема:** `_seed_group_info` и импорт модели `GroupInfo` в `test_responsive_markup.py` остались без единого потребителя — план прямо требует удалить функцию в этом случае.
- **Решение:** функция и импорт сняты, на их месте записано, ЧТО именно снесено и что хранилище цело (репозиторий по-прежнему покрыт `tests/test_repositories/test_group_info.py`).
- **Файлы:** `tests/test_pages/test_responsive_markup.py`
- **Проверка:** `uv run pytest tests/test_pages/test_responsive_markup.py` — 244 теста зелёные (вместе с `test_shell.py`)
- **Коммит:** `66ccd82`

### 6. [Rule 2 — Недостающее критическое] Обход диалогов не знал о пяти новых адресах

- **Найдено при:** Задача 3
- **Проблема:** `DIALOG_SWEEP_ADMIN_URLS` терял адрес справочника и оставался бы с одним админским адресом — новые подразделы не проверялись бы на вызовы системного диалога вовсе.
- **Решение:** место снесённого адреса заняли четыре новых подраздела.
- **Файлы:** `tests/test_pages/test_responsive_markup.py`
- **Проверка:** `test_no_rendered_page_calls_browser_dialog` — зелёный
- **Коммит:** `66ccd82`

---

**Всего дериваций:** 6 автоисправлений (Rule 1 — 1, Rule 2 — 1, Rule 3 — 4).
**Влияние на план:** пять из шести — механическое приведение существующих машинных гейтов проекта к новому составу файлов, то есть работа, которую план предполагал, но поимённо не перечислил. Единственная содержательная — деривация 1: критерий приёмки заменён строго более сильной проверкой, потому что в исходной форме он противоречил несущему решению того же плана. Расширения объёма нет.

## Issues Encountered

**Один тест полной суиты падает по причине, не связанной с этим планом, и НЕ исправлен намеренно.**

`tests/test_pages/test_ads_editor.py::test_image_base_url_comes_from_app_settings` падает в полном прогоне и проходит в одиночку и в паре с любым из файлов этого плана. Дефект — порядко-зависимый: глобалы шаблонов (`get_image_url` / `s3_public_url`) живут модульной переменной и перепривязываются каждым `create_app`, поэтому длинный прогон оставляет привязку от чужого приложения.

**Причастность плана исключена измерением, а не рассуждением.** Отказ воспроизведён на наборе из пяти файлов, НИ ОДИН из которых этим планом не правился (`test_access_gate`, `test_access_lifecycle`, `test_account_groups`, `test_admin_groups_info`, `test_ads_editor`) и до внесения правок задачи 3 — то есть он существовал в проекте до плана и переживёт его откат.

Правка лежит в `app/pages/common.py` и в фикстурах `test_ads_editor.py` — вне предмета плана 06-01, поэтому по границе области действия не исполнена. **Следствие:** критерий приёмки задачи 3 `just test` завершается кодом 0 НЕ выполнен — суита даёт `1 failed, 1784 passed`. Все остальные критерии всех трёх задач выполнены.

### Deferred Issues

| Что | Где | Почему отложено |
|-----|-----|-----------------|
| Порядко-зависимое падение `test_image_base_url_comes_from_app_settings` в полном прогоне | `app/pages/common.py` (глобалы шаблонов модульной переменной), `tests/test_pages/test_ads_editor.py` (фикстура `cdn_client`) | Пре-существующий дефект изоляции в файлах, которых план не касается. Воспроизведён без единого файла этого плана |

_Запись сделана здесь, а не в общем `deferred-items.md` фазы: план исполнялся в изолированном worktree параллельно с соседними планами фазы, и одновременное создание общего файла несколькими агентами дало бы конфликт слияния. Реестр `.planning/WINDOWS.md` в проекте отсутствует — попытка записи в него вернула бы «леджер отсутствует»._

## Known Stubs

Заглушек, мешающих достижению цели плана, нет. Три подраздела намеренно поставлены каркасом, и это записано в самом плане как разделение работы, а не как долг:

| Место | Что | Кто закрывает |
|-------|-----|---------------|
| `app/templates/admin/queue.html` | Честное пустое состояние «Подраздел наполняется» вместо содержимого очереди | План 06-07 |
| `app/templates/admin/logs.html` | То же для журнала служб | План 06-08 |
| `app/templates/admin/payments.html` | То же для платежей | План 06-11 |
| `app/templates/admin/overview.html` | Четыре существующие плитки оставлены как есть | План 06-10 |
| `app/templates/admin/includes/worker_row.html` | Прочерк в колонке «Воркер» у телеграм-аккаунта с подписью «величина ещё не определена» | План 06-05 (чекпойнт владельца назначает честную подпись) |

Ни одна из этих поверхностей не показывает выдуманных чисел: прохибиция плана о данных-заглушках макета закреплена тестом `test_no_mockup_placeholder_numbers_reached_the_subsections`.

## Threat Flags

Новой поверхности за пределами `<threat_model>` плана не введено. Три митигации реестра исполнены и закреплены тестами: T-06-01 (зависимость администратора на всех шести маршрутах, 403 постороннему), T-06-02 (недоступный Redis → «неизвестно», 200), T-06-03 (Docker при рендере не вызывается, разбор синтаксического дерева).

## User Setup Required

None — внешних служб план не добавляет, пакетов не устанавливает, миграций не требует.

## Next Phase Readiness

**Готово к использованию соседними планами фазы:**

- `app/services/ops_state.py` — точка чтения оперативного состояния. План 06-05 расширяет её инфраструктурным блоком и перезапуском, планы 06-07 и 06-10 читают глубину очереди.
- `ADMIN_TABS` и `admin/includes/_tabs.html` — каркас, в который планы 06-07, 06-08, 06-09, 06-10 и 06-11 вносят содержимое своих подразделов. Перечень править не нужно: он полон.
- Приём подмены `app.services.ops_state._get_redis` в суите — образец для любого плана фазы, читающего Redis.

**Что нужно знать соседям:**

- `[data-tabs]` ЗАНЯТ мобильной навигацией шелла. Вкладки подраздела живут на `[data-subtabs]`.
- Признак активной вкладки — `data-subtab-active`, и тест утверждает, что он встречается на странице ровно один раз. Второй такой атрибут уронит `test_active_subsection_is_marked_exactly_once`.
- Любой новый шаблон с шапкой колонок обязан быть внесён в `ROWHEAD_PAGES`, а любой новый макрос строки — в `ROW_TEMPLATES_WITHOUT_HEADER` (`test_responsive_markup.py`), иначе сетка краснеет с числом.

**Блокеров нет.** Единственная незакрытая позиция — пре-существующее порядко-зависимое падение одного теста суиты, описанное выше; оно не связано с админ-панелью и не блокирует ни один план фазы.

---
*Phase: 06-admin-panel*
*Completed: 2026-08-22*

## Self-Check: PASSED

- Все девять созданных файлов присутствуют на диске (`ls` по перечню `key-files.created` — ни одного `MISSING`).
- Все пять коммитов плана присутствуют в истории ветки: `61f82c9`, `c0dd6ab`, `67bcd6a`, `66ccd82`, `23f8042`.
- Три удалённых файла отсутствуют, три файла хранилища (`app/models/group_info.py`, `app/repositories/group_info.py`, `alembic/versions/0011_add_group_info_table.py`) на месте.
- Критерии приёмки всех трёх задач перепроверены; невыполненными остаются два, оба описаны выше с основанием: `grep -c href` у шаблона вкладок (деривация 1, заменён более сильной проверкой) и `just test` кодом 0 (пре-существующее падение вне предмета плана).
