---
phase: quick-260826-dc0-dashboard-calendar-day
plan: 01
subsystem: analytics
tags: [timezone, zoneinfo, sqlalchemy, jinja2, dashboard, send-logs, dst]

# Dependency graph
requires:
  - phase: 04 (аналитика отправок)
    provides: "модуль app/application/analytics/send_analytics.py как единственный источник агрегатов журнала (D-35), скользящее окно плиток (D-02), отсечка периода today по локальной полуночи (D-30)"
  - phase: 06 (админский «Обзор»)
    provides: "общесистемная ветка send_metrics(user_id=None) и запрет второй агрегации в страничном модуле админки (D-39)"
provides:
  - "local_day_start_utc — единственный на проект экземпляр правила «локальная полночь читателя», переведённой в UTC"
  - "MetricsBounds — объявленная пара окон сводки с несимметричными границами (текущее включающее с обеих сторон, предыдущее полуоткрытое сверху)"
  - "sliding_window_bounds / local_day_bounds — два строителя окон при одной формуле агрегации"
  - "send_metrics принимает готовые границы вместо ширины окна; умолчания у bounds нет"
  - "плитки дашборда считают календарные сутки читателя, подпись первой — «Отправок сегодня»"
affects: [dashboard, history, admin-overview, billing-month-axis]

# Actuals (#2632)
actuals:
  tokens: 77000   # chars/4 по восьми правленым файлам целиком (309 483 симв.); та же
                  # шкала, что у estimate.raw_tokens: 65000. По одному диффу вышло бы
                  # 20 000 — цифра не сопоставима с оценкой и здесь не записана.
  tasks: 3
  commits: 4

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Пара окон как ОБЪЯВЛЕННЫЙ объект (MetricsBounds) вместо ширины: форма выражает и календарные сутки, и скользящее окно, а формула агрегации остаётся одна"
    - "Стенная арифметика зоны (local_dt - timedelta(days=1)) для границ, устойчивых к переходу на летнее время — приём, разделённый с current_month_bounds_utc"
    - "AST-свидетель единственности правила: разбор тела конкретной функции вместо поиска подстроки по модулю"

key-files:
  created: []
  modified:
    - app/application/analytics/send_analytics.py
    - app/pages/dashboard.py
    - app/pages/admin.py
    - app/routes/history.py
    - app/templates/dashboard.html
    - tests/test_application/test_send_analytics.py
    - tests/test_application/test_admin_uses_analytics.py
    - tests/test_pages/test_dashboard.py

key-decisions:
  - "D-02 отменён для плиток дашборда осознанно: вопрос дашборда есть «сколько ушло СЕГОДНЯ», и известная цена (в 00:10 плитка почти нулевая) принята пользователем"
  - "Граница суток берётся в зоне читателя и возвращается В UTC: граница в зоне читателя сравнилась бы с sent_at как другой момент на SQLite и как верный на PostgreSQL"
  - "База дельты — вчера ДО ЭТОГО ЖЕ ВРЕМЕНИ, а не вчерашние сутки целиком: иначе по утрам стрелка вечно красная"
  - "Область изменения — только дашборд: API-сводка истории (30 суток) и админский «Обзор» сохранили скользящее окно и прежние числа"
  - "Умолчания у send_metrics(bounds=...) нет: умолчание вернуло бы скрытый выбор окна внутрь функции счёта"

patterns-established:
  - "Одно правило — один экземпляр, и единственность машинно засвидетельствована: _period_cutoff('today') вызывает local_day_start_utc, а AST-тест запрещает возврат собственного replace(hour=...)"
  - "Тест, меняющий поведение, обязан УТВЕРЖДАТЬ и старое поведение рядом: те же две записи скользящим окном дают два, календарным — один"
  - "Страничные посевы времени считаются ОТ ГРАНИЦЫ окна, а не от now минус часы: посев от now флаковый в ночные часы"

requirements-completed: [QUICK-DASH-CALENDAR-DAY]

coverage:
  - id: D1
    description: "Плитки дашборда считают календарные сутки читателя: отправка за час до его локальной полуночи в плитку «Отправок сегодня» не входит, отправка ровно в полночь — входит"
    requirement: "QUICK-DASH-CALENDAR-DAY"
    verification:
      - kind: e2e
        ref: "tests/test_pages/test_dashboard.py#test_the_dashboard_tile_counts_the_readers_calendar_day"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_the_calendar_day_window_leaves_yesterday_evening_out"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_local_midnight_belongs_to_the_current_day"
        status: pass
    human_judgment: false
  - id: D2
    description: "База стрелок-дельт — вчерашние сутки до этого же времени, верхняя граница полуоткрытая"
    requirement: "QUICK-DASH-CALENDAR-DAY"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_yesterday_is_counted_only_up_to_the_current_time"
        status: pass
    human_judgment: false
  - id: D3
    description: "Правило локальной полуночи существует в одном экземпляре; дашборд и фильтр «Сегодня» в истории берут одну границу"
    requirement: "QUICK-DASH-CALENDAR-DAY"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_the_dashboard_day_and_the_today_filter_share_one_boundary"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_the_today_cutoff_has_no_second_copy_of_local_midnight"
        status: pass
    human_judgment: false
  - id: D4
    description: "Числа соседей не изменились: GET /api/history/stats и админский «Обзор» продолжают считать скользящим окном"
    verification:
      - kind: unit
        ref: "uv run pytest tests/test_application/test_admin_uses_analytics.py tests/test_pages/test_admin_panel.py tests/test_routes -q"
        status: pass
    human_judgment: false
  - id: D5
    description: "Переход на летнее время не сдвигает границу суток; пользователь без зоны режется по UTC-полуночи"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_the_day_boundary_survives_a_dst_transition"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_a_reader_without_a_timezone_is_cut_at_utc_midnight"
        status: pass
    human_judgment: false
  - id: D6
    description: "Живой дашборд пользователя в UTC+3, открытый утром, показывает в плитке «Отправок сегодня» только сегодняшние отправки"
    verification: []
    human_judgment: true
    rationale: "Проверка требует боевого пользователя с непустым журналом и ненулевой зоной в конкретный час суток; suite закрепляет ту же истину на посевах, но не подтверждает, что на экране читается именно она."

# Metrics
duration: 95min
completed: 2026-08-26
status: complete
---

# Quick 260826-dc0: плитки дашборда за календарные сутки — Summary

**Плитки дашборда переведены со скользящих 24 часов на календарные сутки читателя (от его локальной полуночи до момента запроса), дельта считается от вчерашнего отрезка той же длины, а граница суток теперь рождается в одном хелпере на дашборд и на фильтр «Сегодня» в истории.**

## Performance

- **Duration:** ~95 мин (включая полный прогон suite — 24 мин)
- **Tasks:** 3 из 3
- **Files modified:** 8
- **Commits:** 4 (RED → GREEN → тесты → проза)

## Accomplishments

- **Плитки считают «сегодня», а не «последние 24 часа».** Человек в UTC+3, открывший дашборд в два часа ночи, больше не видит в плитке отправки вчерашнего вечера. D-02, выбиравший здесь скользящее окно, отменён ОСОЗНАННО: его довод («в 00:10 счётчик почти нулевой») не опровергнут, а признан известной и принятой ценой — и записан именно так в трёх местах, а не вычеркнут молча.
- **Расхождение по полуночи закрыто в обе стороны.** Докстринг модуля называл дефект «дашборд считал от одной полуночи, история — от другой». Теперь границу обоим отдаёт `local_day_start_utc`; `_period_cutoff("today")` его вызывает и собственной копии `replace(hour=0, ...)` не держит. Единственность засвидетельствована машинно — разбором дерева тела функции, а не поиском строки (та же подстрока законно живёт в `current_month_bounds_utc`).
- **Форма окна стала объявленной, а форк формулы не заведён.** `MetricsBounds` несёт четыре момента с несимметричными границами; строителей два (`sliding_window_bounds`, `local_day_bounds`), а восемь условных агрегатов и один round-trip остались ровно одни. Дашборд и админский «Обзор» различаются объектом границ, а не веткой внутри запроса.
- **Числа соседей не сдвинулись ни на единицу.** `GET /api/history/stats` (30 суток) и «Обзор» (`user_id=None`) считают прежним скользящим окном; во всех тестах соседей правились только аргументы вызова, ни одно ожидаемое число не тронуто.
- **Подпись плитки перестала врать:** «Отправок за сутки» → «Отправок сегодня». В час ночи за прежней подписью стоял один час, а не сутки.

## Task Commits

1. **Задача 1 (tracer, TDD): сквозная нить — календарные сутки доходят до плитки**
   - RED: `100fadb` (test) — красный сквозной тест страницы + тест формы `MetricsBounds`
   - GREEN: `d244fc9` (feat) — хелпер границы, объект границ, два строителя, новая сигнатура `send_metrics`, три вызывающих, подпись плитки
2. **Задача 2: семь истин календарного окна** — `fc4fd09` (test)
3. **Задача 3: закрывающий прогон и проза** — `f0563eb` (docs)

_Метаданные плана (SUMMARY/STATE) коммитит оркестратор — сюда не входят._

## Files Created/Modified

- `app/application/analytics/send_analytics.py` — `local_day_start_utc`, `MetricsBounds`, `sliding_window_bounds`, `local_day_bounds`; `send_metrics` принимает границы; предыдущее окно ограничено с двух сторон; `_period_cutoff("today")` переписан на вызов хелпера
- `app/pages/dashboard.py` — `bounds=local_day_bounds(user)`; комментарий называет отмену D-02 и её причину
- `app/pages/admin.py` — `bounds=sliding_window_bounds(now=now)`; докстринг «Обзора» больше не обещает совпадения цифры с пользовательским дашбордом
- `app/routes/history.py` — `bounds=sliding_window_bounds(window=STATS_WINDOW)`; поведение и числа прежние
- `app/templates/dashboard.html` — подпись `Отправок сегодня`; шапка блока приведена к календарному окну
- `tests/test_application/test_send_analytics.py` — семь новых тестов календарного окна + тест формы границ, 11 вызовов переведены на строитель, проза файла называет обе формы окна
- `tests/test_application/test_admin_uses_analytics.py` — 5 вызовов переведены на строитель, ожидаемые числа не тронуты
- `tests/test_pages/test_dashboard.py` — новый сквозной тест, посевы переведены на границу суток, подписи плиток обновлены

## Decisions Made

Все ключевые решения зафиксированы в CONTEXT.md до исполнения (Q1–Q4) и не пересматривались. Исполнительские решения в их рамках:

- **`local_day_bounds` делает собственный отложенный импорт `_get_timezone_for_user`.** Стенная арифметика вчерашних границ требует самой зоны, а не только готовой полуночи. P-1 это не нарушает: запрещена вторая копия ПРАВИЛА ПОЛУНОЧИ, а хелпер зоны и здесь остаётся единственным источником — тот же приём уже применён в `current_month_bounds_utc`.
- **Предыдущее окно получило явную нижнюю границу.** Прежний предикат `sent_at < current_start` работал лишь потому, что низ ставил внешний `where`. Для «вчера до этого же времени» этого мало: вчерашний вечер лежит внутри общего отбора, но за верхней границей предыдущего окна, и без пары границ утекал бы в базу дельты.
- **Вспомогательный `_reader(tz_name)` в тестах** — читатель без записи в БД. Границы считаются в Python (P-3), и поднимать сессию ради проверки арифметики значило бы платить за неё в каждом прогоне.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — недостающая правка] Три устаревших утверждения сверх перечисленных планом**

- **Найдено во время:** Задача 3 (сверка диффов на утверждения, которых код рядом не исполняет)
- **Проблема:** План перечислил шесть мест, где проза могла разойтись с кодом. Сверка нашла ещё три: (а) шапка блока в `app/templates/dashboard.html` объявляла окно плиток «СКОЛЬЗЯЩИЕ сутки от момента запроса (D-02)»; (б) комментарий секции календарного месяца в модуле обосновывал существование `current_month_bounds_utc` тем, что «плитки считают скользящие сутки»; (в) докстринг `send_metrics` в абзаце про классификацию ошибок звал плитку прежней подписью «Отправок за сутки».
- **Исправление:** все три приведены к факту. Абзац про классификацию ошибок в остальном не тронут — правился только литерал подписи, аргумент абзаца сохранён.
- **Файлы:** `app/templates/dashboard.html`, `app/application/analytics/send_analytics.py`
- **Проверка:** `grep -rn "скользящ\|за сутки\|24 час" app/ tests/` — оставшиеся вхождения относятся к админскому «Обзору» и блоку инцидентов, где скользящее окно сохранено намеренно (Q3) и утверждения остаются истинными
- **Коммит:** `f0563eb`

**2. [Rule 1 — баг в собственной правке] Слишком широкая механическая замена в тестах**

- **Найдено во время:** Задача 1, шаг 8
- **Проблема:** первая попытка заменить `now=NOW` на `bounds=sliding_window_bounds(now=NOW)` шла по подстроке `, now=NOW)` и задела 22 вызова вместо 11 — под замену попали `user_totals`, `paying_total` и другие функции, у которых параметр `now` остаётся законным.
- **Исправление:** правка откачена (`git checkout --` по двум файлам, коммит RED не затронут) и переделана регулярным выражением, адресованным именно вызовам `send_metrics`. Результат — ровно 11 и 5 замен, как и предписано планом.
- **Файлы:** `tests/test_application/test_send_analytics.py`, `tests/test_application/test_admin_uses_analytics.py`
- **Проверка:** обе суиты зелёные без правки ожидаемых чисел
- **Коммит:** вошло в `d244fc9`

---

**Total deviations:** 2 auto-fixed (1× Rule 2, 1× Rule 1)
**Impact on plan:** архитектура плана не менялась; обе правки — внутри объявленной области восьми файлов. Scope creep отсутствует: `git diff --stat` показывает ровно восемь файлов плана.

## Issues Encountered

- **RED-фаза задачи 1 краснела ошибкой импорта, а не утверждением.** План предписал брать границу в тесте тем же хелпером модуля (чтобы тест не держал копию правила), а хелпера на том дереве ещё не было. Осознанный размен: тест, считающий границу сам, был бы зелёным при разошедшейся копии. Разграничение старого и нового поведения закреплено иначе — тестом `test_the_calendar_day_window_leaves_yesterday_evening_out`, который на ОДНИХ И ТЕХ ЖЕ посевах утверждает `1` календарным окном и `2` скользящим: при откате правки он краснеет.
- **Флаковость посевов от `now`.** Два существовавших страничных теста сеяли от `now` минус один-три часа. После смены семантики такой посев уезжает за локальную полночь между 00:00 и 03:00 и краснел бы по расписанию. Оба переведены на посев от границы; причина записана в докстринг файла, чтобы следующий посев не завели по-старому.

## Verification Results

Полный прогон: `uv run pytest tests/ -q` → **1 failed, 2274 passed** за 24:26.

Единственный красный — **пред-существующий и не связанный с задачей**: `tests/test_planning/test_state_progress_matches_roadmap.py::test_the_machine_readable_progress_is_derived_from_the_roadmap` падает на расхождении счётчиков `progress.total_plans` / `progress.completed_plans` во frontmatter `.planning/STATE.md` (110) с выведенными из отметок `.planning/ROADMAP.md` (0). Ни одного файла приложения этот тест не читает; задачей он НЕ чинится (объявлено планом).

Гейты задач:

- `send_metrics` имеет ровно `['session', 'user_id', 'bounds']`, у `bounds` умолчания нет — OK
- `local_day_bounds` для `Europe/Moscow` и `now=2026-05-19T23:00Z` отдаёт объявленные четыре момента, все со смещением 0 — OK
- `grep -c "metric_tile('Отправок сегодня'" app/templates/dashboard.html` = 1 — OK
- `git status --porcelain -- app/pages/common.py app/pages/history.py app/models alembic` пуст — OK
- `graphify update .` отработал: 12 394 узла, 23 784 ребра, 706 сообществ

## Known Stubs

Отсутствуют. Заглушек, TODO/FIXME и пропущенных тестов правка не оставила; все восемь `<verify>`-шагов плана исполнены.

## Threat Flags

Новой поверхности безопасности не появилось. Изоляция по владельцу не тронута: `user_id` остался обязательным keyword-only без умолчания, и это закреплено пред-существующим `test_the_owner_of_a_summary_cannot_be_omitted_by_accident`. Негодное значение `users.timezone` по-прежнему даёт UTC ветвью `_get_timezone_for_user`, а не пятисотку (`test_a_reader_without_a_timezone_is_cut_at_utc_midnight`). Верхняя граница текущего окна сохранена — запись с `sent_at` в будущем плитку не завышает (`test_send_metrics_ignores_records_from_the_future`). Миграций и правок схемы задача не заводит.

## User Setup Required

None — внешней конфигурации не требуется.

## Next Phase Readiness

Готово. Открытых вопросов задача не оставляет.

Что стоит знать следующему, кто тронет этот модуль:

- Окон в модуле ДВА, и это не переходное состояние. `local_day_bounds` — для экранов с читателем; `sliding_window_bounds` — для операционных вопросов без читателя (админский «Обзор», API-сводка). Подмена одного другим не уронит ни один тест соседей автоматически — она сдвинет их числа, и P-4 запрещает подгонять ожидания под сдвиг.
- Граница суток рождается ТОЛЬКО в `local_day_start_utc`. Вторую копию ловит AST-тест `test_the_today_cutoff_has_no_second_copy_of_local_midnight`, но только внутри `_period_cutoff`: копия, заведённая в третьем месте, машинно не ловится.
- Квота месяца (`current_month_bounds_utc`) осталась вне области правки, но делит с новыми хелперами приём стенной арифметики — правка одного без другого разведёт два соседних правила.

## Self-Check: PASSED

- Все восемь правленых файлов существуют на диске
- Все четыре коммита (`100fadb`, `d244fc9`, `fc4fd09`, `f0563eb`) разрешаются в объекты типа `commit`
- Результат прогона взят из реального вывода `uv run pytest tests/ -q`, а не заявлен

---
*Quick task: 260826-dc0*
*Completed: 2026-08-26*
