---
phase: quick-260826-9vv-dashboard-drops-activity-block
plan: 01
subsystem: ui
tags: [jinja2, fastapi, css, sqlalchemy, pytest, dashboard, analytics]

# Dependency graph
requires:
  - phase: quick-260826-6jq
    provides: приём снятия блока дашборда с переносом утверждений в тесты-запреты
provides:
  - Дашборд без карточки «Активность за неделю» на всех четырёх слоях блока
  - Путь рендера `/dashboard` без потокового чтения недельного окна `send_logs`
  - Модуль аналитики без секций «Heatmap активности» и «Столбцы активности за неделю»
  - Четыре положительных запрета на возврат блока: разметка, шаблоны, стили, модуль
affects: [dashboard, send_analytics, responsive-markup-tests]

actuals:
  tokens: 20000
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Признаки снятого блока сведены в один модульный кортеж, читаемый всеми тестами-запретами"
    - "Запреты снятых тестов переезжают поимённо в новые тесты, а не исчезают с предметом"

key-files:
  created: []
  modified:
    - app/templates/dashboard.html
    - app/templates/dashboard/includes/activity_chart.html (удалён)
    - app/static/css/app.css
    - app/pages/dashboard.py
    - app/application/analytics/send_analytics.py
    - tests/test_pages/test_dashboard.py
    - tests/test_pages/test_responsive_markup.py
    - tests/test_application/test_send_analytics.py

key-decisions:
  - "Обе секции аналитики сняты целиком (полный объём плана по решению владельца): после снятия карточки у них не осталось ни одного потребителя, а обещание «раскладка остаётся доступной Фазе 6» истекло невыполненным — Фаза 6 закрыта с вехой v2.0"
  - "Признаки блока сведены в ACTIVITY_CHART_MARKERS: три теста-запрета проверяют разные поверхности, но предмет у них один, и разъехавшиеся списки дали бы дырявый запрет"
  - "Три утверждения снятых тестов переехали поимённо: запрет инлайн-заливки (D-06) — в запрет по разметке, два запрета на возврат сетки 7×24 — в запрет по стилям"
  - "Комментарий раздела в app.css назван прозой, без скобочных селекторов: тест переписи шапок ищет два имени в атрибутных скобках по сырому тексту стилей и покраснел бы на объяснении"
  - "Пара `{% set next_label, next_href = next_step %}` в dashboard.html оставлена: её читает второй потребитель — пустое состояние ближайших отправок"

patterns-established:
  - "Тест-запрет по модулю проверяет объекты через hasattr, а не текст файла: объяснение снятия в комментарии запрет не краснит"
  - "Тест-запрет обязан утверждать и живых соседей: запрет, прошедший на снесённой заодно поверхности, запретом не является"

requirements-completed: [QUICK-DASH-ACTIVITY-REMOVE]

coverage:
  - id: D1
    description: "На `/dashboard` нет ни одного признака карточки «Активность за неделю» при засеянной отправке, а плитки, пара блоков и опрос ленты живы"
    requirement: "QUICK-DASH-ACTIVITY-REMOVE"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_the_dashboard_carries_no_weekly_activity_block"
        status: pass
    human_judgment: false
  - id: D2
    description: "Шаблон макроса графика удалён с диска, его разметки нет ни в одном шаблоне дашборда, живой сосед по каталогу на месте"
    requirement: "QUICK-DASH-ACTIVITY-REMOVE"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_the_activity_chart_template_is_gone"
        status: pass
    human_judgment: false
  - id: D3
    description: "В app.css не осталось правил графика и правил снятой прежде сетки 7×24, при этом живы правила пары дашборда и строки ленты"
    requirement: "QUICK-DASH-ACTIVITY-REMOVE"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_the_dashboard_activity_chart_left_no_css_behind"
        status: pass
    human_judgment: false
  - id: D4
    description: "Модуль аналитики потерял пять имён снятых секций и сохранил четыре живые функции; путь рендера дашборда больше не стримит недельное окно send_logs"
    requirement: "QUICK-DASH-ACTIVITY-REMOVE"
    verification:
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_the_module_no_longer_carries_the_weekly_activity_surface"
        status: pass
      - kind: integration
        ref: "uv run pytest tests/ -q (2265 passed, 1 pre-existing failure)"
        status: pass
    human_judgment: false

duration: 40min
completed: 2026-08-26
status: complete
---

# Quick 260826-9vv: дашборд без блока «Активность за неделю» Summary

**Карточка недельной активности снята со всех четырёх слоёв блока вместе с обеими секциями модуля аналитики, кроме неё никем не читанными: путь рендера `/dashboard` перестал стримить недельное окно `send_logs` батчами по 1000 записей на каждой загрузке страницы.**

## Performance

- **Duration:** ~40 min (из них 24 min — полный прогон набора)
- **Started:** 2026-08-26T07:17:00Z
- **Completed:** 2026-08-26T07:57:13Z
- **Tasks:** 3
- **Files modified:** 8 (один из них удалён)

## Accomplishments

- Со страницы `/dashboard` снята карточка «Активность за неделю»: разметка блока, импорт макроса, шаблон макроса (удалён файл), раздел правил в стилях и сбор данных в модуле маршрута.
- Модуль аналитики потерял ровно две секции — «Heatmap активности» и «Столбцы активности за неделю» (216 строк): `SHORT_WEEKDAYS`, `HEATMAP_YIELD_PER`, `HeatmapView`, `activity_heatmap`, `CHART_BUCKETS_PER_DAY`, `CHART_BUCKET_HOURS`, `ActivityChartView`, `activity_chart`. Вместе с ними ушёл импорт `tzinfo`.
- Снятие объявлено четырьмя положительными запретами (разметка, шаблоны, стили, модуль), а не молчаливо.
- Ни одно утверждение снятых тестов не потеряно: запрет инлайн-заливки (D-06) и два запрета на возврат сетки 7×24 переехали поимённо в новые тесты.
- Полный прогон: 2265 passed, 1 failed — пред-существующий красный `tests/test_planning/test_state_progress_matches_roadmap.py` (запись 9 в `.planning/WINDOWS.md`), не чинился.

## Task Commits

1. **Задача 1: снять карточку со всех четырёх слоёв блока** — `2b7b07a` (feat)
2. **Задача 2: снять тесты снятого блока, сохранить их утверждения, объявить запрет** — `f1fb436` (test)
3. **Задача 3: снять из модуля аналитики две секции, потерявшие потребителя** — `c5fa5d3` (refactor)

**Plan metadata:** передаётся оркестратору (докс-коммит исполнителем не делается).

## Files Created/Modified

- `app/templates/dashboard.html` — снят блок графика (строки 137-150) и импорт его макроса; на месте блока оставлено объяснение снятия с именами четырёх тестов-запретов. Атрибут общей шапки в объяснении НЕ упомянут — перепись шапок страницы по-прежнему видит ровно два вхождения.
- `app/templates/dashboard/includes/activity_chart.html` — **удалён** (64 строки). Три соседа по каталогу живы.
- `app/static/css/app.css` — снят раздел правил графика и его отдельное правило пониженной анимации (строки 1448-1490); объяснение написано прозой, без единого скобочного селектора.
- `app/pages/dashboard.py` — снят сбор недельной активности, ключ контекста `chart_view`, два имени из импорта модуля аналитики и импорт `_get_timezone_for_user` (сама функция в `app/pages/common.py` не тронута — её зовут форматирование времени и сам модуль аналитики).
- `app/application/analytics/send_analytics.py` — сняты обе секции (285-500) и `tzinfo` из импорта; на месте оставлено объяснение с причиной и именем запрета. Всё ниже границы не тронуто.
- `tests/test_pages/test_dashboard.py` — `test_dashboard_empty_grid_is_replaced_by_an_empty_state` переименован в `test_dashboard_empty_blocks_lead_to_connecting_a_channel` (утверждение про первую ветвь D-40 сохранено); из теста «всё заведено» снято утверждение про пустой график.
- `tests/test_pages/test_responsive_markup.py` — сняты три теста графика и импорт `CHART_BUCKETS_PER_DAY`; переписан `test_dashboard_blocks_share_one_head_without_a_divider`; добавлены `ACTIVITY_CHART_MARKERS` и три теста-запрета.
- `tests/test_application/test_send_analytics.py` — сняты секция свёртки в столбцы, секция раскладки часов, тест сетки на записи из будущего и пять имён из импорта; добавлен `test_the_module_no_longer_carries_the_weekly_activity_surface`.

## Decisions Made

- **Полный объём плана исполнен по решению владельца:** обе секции аналитики сняты вместе с их юнит-тестами. Пред-полётный grep-гейт задачи 3 отработал: потребителей снимаемых имён вне двух правленых файлов не нашлось — оставшиеся вхождения это ИМЕНА тестов-запретов в комментариях (`test_the_activity_chart_template_is_gone`) и перечень имён внутри самого запрета, то есть предмет запрета, а не его потребитель.
- **Объяснения снятия оставлены на всех трёх поверхностях** (шаблон, стили, модуль) и написаны так, чтобы не краснить существующие тесты по сырому тексту: в `dashboard.html` не назван атрибут общей шапки и нет разметки элементов таблицы, в `app.css` нет ни одного скобочного селектора.
- **Признаки блока сведены в `ACTIVITY_CHART_MARKERS`** — один кортеж на три теста-запрета, по образцу `WORKER_LIST_MARKERS` задачи 260826-6jq.
- **Тест шаблонов проверяет и `dashboard.html`**, а не только каталог `app/templates/dashboard/`: разбор идёт через `_markup_without_comments`, поэтому объяснение снятия запрет не краснит, а покрытие получается тем же, что у прецедента с перечнем воркеров.

## Deviations from Plan

None — план исполнен как написан. Правки сделаны по указанным строкам, границы соблюдены, ни один файл вне восьми перечисленных в `files_modified` не тронут (`git diff --stat` против базы показывает ровно восемь).

## Issues Encountered

- **Висячая ссылка в комментарии ниже границы.** `app/application/analytics/send_analytics.py:287-288` (после правки) в объяснении пометок причин ссылается на «подписи рядов heatmap» — на секцию, снятую этой задачей. Строка лежит НИЖЕ границы 501, которую план запретил трогать, поэтому она оставлена как есть. Правка на один абзац комментария; кандидат в следующую уборку, ссылка ничего не ломает и ни одним тестом не читается.
- **Секция тестов опустела вместо «остаться при одном соседе».** План ожидал, что после снятия двух тестов в секции `# --- План 04-04 ---` останется сосед; фактически в ней стояли ровно эти два теста. Секция переименована в заголовок запрета и заполнена новым тестом-запретом — смысла плана это не меняет.

## User Setup Required

None.

## Next Phase Readiness

- Дашборд собирает ровно три чтения: плитки, ближайшие отправки и ленту. Самое дорогое чтение экрана снято.
- Пред-существующий красный `tests/test_planning/test_state_progress_matches_roadmap.py` остаётся открытым (запись 9 в `.planning/WINDOWS.md`) — он про расхождение `ROADMAP.md` и `STATE.md` после архивации вехи и к этой задаче отношения не имеет.

## Self-Check: PASSED

- `app/templates/dashboard/includes/activity_chart.html` — подтверждено удалённым.
- Коммиты `2b7b07a`, `f1fb436`, `c5fa5d3` — найдены в `git log`.
- `git diff --stat` против базы `40de9a7` — ровно 8 файлов плана, ни одного сверх.
- `grep -rn "activity_chart\|activity_heatmap\|HeatmapView\|ActivityChartView\|CHART_BUCKET" app/ tests/` — вне имён самих тестов-запретов ничего.
- `uv run pytest tests/ -q` — 2265 passed, 1 failed (пред-существующий, не чинился).
- `graphify update .` — отработал (12342 узла, 23640 рёбер).

---
*Quick task: 260826-9vv*
*Completed: 2026-08-26*
