---
phase: 02-obyavleniya-i-raspisaniya
plan: 07
subsystem: frontend
tags: [jinja2, fastapi, css, filters, htmx, russian-plurals, idor]

# Dependency graph
requires:
  - phase: 02-06
    provides: "Сводный список без создания: действие шапки на /ads, действие строки в редактор"
  - phase: 02-05
    provides: "`[data-sched-list]`, примитивы .chip / .kv раздела 8, `sched_count_label`, `_is_complete`"
  - phase: 02-03
    provides: "`Ad.status` и `AD_STATUS_DRAFT` — источник признака черновика"
  - phase: 02-02
    provides: "Правило «клиентским данным не верят» — образец для связки по владельцу"
  - phase: 02-01
    provides: "Базовая линия суиты и страховочная сетка SC-3"
provides:
  - "Сводный список расписаний карточками: объявление, канал, ИМЕНА групп, дни, времена, ближайший запуск"
  - "Полоса фильтров по каналу и состоянию плюс поиск по объявлению и времени запуска"
  - "Два различимых пустых состояния и полоса фильтров, живущая при пустом списке"
  - "Пометка «Объявление в черновике» и «отправок не будет» для расписаний черновиков"
  - "`_group_names_for` — разрешение имён групп ОДНИМ запросом со связкой по владельцу"
affects: []

actuals:
  tokens: 63000
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Триада списочного раздела (страница, фрагмент, макрос карточки) правится ОДНИМ заходом: Jinja не сообщает о пропавшем параметре макроса, и страница отвечает 200, рендеря пустоту"
    - "Сентинел бесконечной прокрутки проверяется на ПОБАЙТОВОЕ совпадение вместе с отступом строки, а не на совпадение по смыслу"
    - "Идентификаторы из JSON-массива превращаются в имена ОДНИМ запросом со связкой по владельцу; идентификатор без совпадения не рендерится пустой строкой, и остаток «и ещё K» считается по РАЗРЕШЁННЫМ именам"
    - "Неизвестное значение фильтра отсекается СЕРВЕРОМ до запроса и приводит к варианту «Все»: разметка точкой принуждения не является"
    - "Два пустых состояния различаются признаком «фильтр применён», а не вторым запросом «есть ли что-нибудь вообще»"
    - "Предикат поиска по JSON-массиву вычисляется в Python одним запросом на страницу — по образцу подсчёта расписаний в app/pages/groups.py, а не переносимым SQL, которого у проекта нет"

key-files:
  created:
    - tests/test_pages/test_schedules_list.py
  modified:
    - app/pages/schedules.py
    - app/static/css/app.css
    - app/templates/schedules/list.html
    - app/templates/schedules/partial_cards.html
    - app/templates/schedules/includes/schedule_row.html
    - tests/test_pages/test_responsive_markup.py
    - tests/test_pages/test_htmx_preserved.py
    - tests/test_templates/test_components.py
    - .planning/REQUIREMENTS.md
  deleted: []

key-decisions:
  - "Фильтрация, поиск и счётчик найденных реализованы СЕРВЕРНО в Задаче 1, хотя план назвал полосу фильтров работой Задачи 2: полоса, не отбирающая ничего, была бы заглушкой в терминах самого плана, а Задаче 2 запрещено трогать .py"
  - "Поиск по времени запуска вычисляется в Python: переносимого SQL-предиката «подстрока внутри элемента JSON-массива» у проекта нет, и app/pages/groups.py по той же причине считает расписания по группам в Python"
  - "Остаток «и ещё K» считается по РАЗРЕШЁННЫМ именам, а не по длине массива идентификаторов: иначе карточка обещала бы группы, показать которые нечем"
  - "Случай «ни одно имя не разрешилось» назван словами («группы недоступны»), а не пустотой: удалённая группа обязана отличаться от расписания без групп"
  - "Ключи «Группы · Время · След. запуск» внутри карточки заменили подписи ячеек: у карточки нет шапки колонок, которую подпись компенсировала, и обещание SC-5 переехало, а не исчезло"
  - "Удаление снято с карточки сводного списка (D-18) — три переписи признали снятие уменьшением объявленных чисел, ни одно утверждение не ослаблено"
  - "Бейджи вынесены отдельной строкой под шапку: «Объявление в черновике» длиннее остатка строки на 320px и в шапке вытолкнул бы тумблер"
  - "`sched_count_label` импортируется из карточки редактора, а не объявляется заново: второе правило русских числительных разъехалось бы с первым"

patterns-established:
  - "Тест, потерявший субъект вместе с примитивом раздела, переписывается на то же обещание в новой форме и остаётся в том же файле — счёт тестовых функций не уменьшается"
  - "Перепись мест (удалений, подтверждений, шаблонов с шапкой) при сознательном снятии правится ЧИСЛОМ и комментарием «почему», а не ослаблением предиката"

requirements-completed: [SCH-04, SCH-05]

coverage:
  - id: D1
    description: "Сводный список показывает каждое расписание с объявлением, каналом, ИМЕНАМИ групп, днями и временем (SCH-04, SC-4)"
    requirement: SCH-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_summary_card_renders_group_names"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_card_renders_data"
        status: pass
    human_judgment: false
  - id: D2
    description: "Группы показаны ИМЕНАМИ, а не только числом; остаток свёрнут в «и ещё K»"
    requirement: SCH-04
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_summary_card_folds_the_remainder_into_a_count"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_schedules_list.py#test_item_carries_group_names_and_the_remainder"
        status: pass
    human_judgment: false
  - id: D3
    description: "Имена групп разрешаются ОДНИМ запросом со связкой по владельцу (T-02-34, T-02-38)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_summary_page_resolves_group_names_in_one_query (30 расписаний → ≤1 запрос к группам)"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_foreign_group_name_never_becomes_a_card_value"
        status: pass
      - kind: other
        ref: "grep 'select(Group.id, Group.name)' app/pages/schedules.py → условие Group.user_id == user_id в том же where"
        status: pass
    human_judgment: false
  - id: D4
    description: "Идентификатор без группы не превращается в пустое имя и не роняет страницу"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_schedules_list.py#test_unresolved_group_id_does_not_become_an_empty_name"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_missing_group_does_not_break_the_page"
        status: pass
    human_judgment: false
  - id: D5
    description: "Расписание включается и ставится на паузу из списка; маршрут не изменён (SCH-05, SC-4)"
    requirement: SCH-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_toggle_route_unchanged"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_toggle_from_the_list_leaves_a_foreign_schedule_alone (T-02-37)"
        status: pass
      - kind: other
        ref: "app/templates/schedules/includes/schedule_row.html — форма POST /schedules/{id}/toggle, перехват на ФОРМЕ, макрос toggle без атрибутов событий"
        status: pass
    human_judgment: false
  - id: D6
    description: "Отказ переключения возвращает карточку в прежнее состояние — тумблер не показывает непринятого"
    requirement: SCH-05
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_refused_toggle_leaves_the_card_in_its_previous_state"
        status: pass
    human_judgment: false
  - id: D7
    description: "Список открывается пояснением, что создание и настройка живут на странице объявления"
    verification:
      - kind: other
        ref: "grep 'Создание и настройка расписаний — на странице объявления' app/templates/schedules/list.html → 1"
        status: pass
    human_judgment: false
  - id: D8
    description: "Расписание объявления-черновика помечено, и в ячейке запуска стоит «отправок не будет» (UI-SPEC E13 partial)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_draft_ad_schedule_is_marked_and_promises_no_sends"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_published_ad_schedule_carries_no_draft_marker (парный)"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_schedules_list.py#test_draft_ad_marks_its_schedule (сравнение с константой, не с литералом)"
        status: pass
    human_judgment: false
  - id: D9
    description: "Полосы прогресса отправок в карточке нет (D-17)"
    verification:
      - kind: other
        ref: "grep -c 'progress' app/templates/schedules/includes/schedule_row.html → 0; в app/static/css/app.css → 8, значение до правки"
        status: pass
    human_judgment: false
  - id: D10
    description: "Два пустых состояния различаются; полоса фильтров рендерится и при пустом списке (UI-SPEC E13/E14 empty)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_empty_state_without_schedules_points_at_the_ads"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_empty_state_with_no_matches_offers_to_reset_the_filters"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_filter_bar_renders_when_the_list_is_empty"
        status: pass
    human_judgment: false
  - id: D11
    description: "Счётчик найденных склоняется по-русски (1 / 2-4 / 5+)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_result_count_is_declined (три параметра: 1 / 3 / 5)"
        status: pass
    human_judgment: false
  - id: D12
    description: "Неизвестное значение фильтра приводит к варианту «Все», а не к ошибке страницы (T-02-35)"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_schedules_list.py#test_unknown_filter_value_falls_back_to_all (6 параметров)"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_unknown_filter_value_does_not_break_the_page (4 параметра)"
        status: pass
    human_judgment: false
  - id: D13
    description: "Фильтры и поиск ОТБИРАЮТ, а не украшают"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_channel_filter_narrows_the_list"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_state_filter_narrows_the_list"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_search_matches_the_ad_title_and_the_launch_time"
        status: pass
    human_judgment: false
  - id: D14
    description: "Поисковый термин возвращается пользователю ТЕКСТОМ (T-02-36)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedules_list.py#test_hostile_search_term_is_rendered_as_text"
        status: pass
    human_judgment: false
  - id: D15
    description: "Инвариант бесконечной прокрутки сохранён и проверен на ВТОРОЙ странице выдачи"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_chain[schedules] (offset=30 несёт следующий сентинел)"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_keeps_filters[schedules] (фильтр едет в URL сентинела)"
        status: pass
      - kind: other
        ref: "diff сентинелов list.html и partial_cards.html → различий нет (побайтово, включая отступ строки)"
        status: pass
    human_judgment: false
  - id: D16
    description: "Список карточный на всех ширинах; таблично-строчной обработки ячеек нет"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_summary_list_is_card_based"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_card_names_each_value + test_schedules_partial_names_each_value"
        status: pass
    human_judgment: false
  - id: D17
    description: "Удаления в карточке сводного списка нет; путь удаления жив в редакторе (D-18)"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_summary_list_offers_no_deletion"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedule_delete_uses_modal_and_a_real_form_in_the_editor"
        status: pass
      - kind: other
        ref: "grep -c '/delete' app/templates/schedules/includes/schedule_row.html → 0"
        status: pass
    human_judgment: false
  - id: D18
    description: "Длинный заголовок обрезается в одну строку, полное значение в подсказке, тумблер и переход сохраняют позиции; 320px, 200 символов"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_card_title_truncates_instead_of_pushing_controls (правило CSS и подсказка в шаблоне)"
        status: pass
    human_judgment: true
    rationale: "Backstop-строка must_haves. Правило написано под неё (min-width: 0, nowrap, ellipsis у .sched-item__title; бейджи вынесены из шапки), и наличие правила закреплено тестом по исходнику — но ВИЗУАЛЬНАЯ проверка на 320px с заголовком в 200 символов не выполнена: `<human-check>` требует стенда."
  - id: D19
    description: "Граф проекта обновлён `graphify update .`"
    verification: []
    human_judgment: true
    rationale: "НЕ ВЫПОЛНЕНО в worktree сознательно: `graphify-out/` в `.gitignore` (строки 54-56), каталога в worktree нет вовсе, и полная пересборка была бы выброшена вместе с одноразовым каталогом. Приёмочный критерий `git status --porcelain graphify-out/` показывает изменения НЕВЫПОЛНИМ по построению — игнорируемый путь не появляется в выводе никогда. Шаг вынесен в «User Setup Required»."

# Metrics
duration: 61min
completed: 2026-08-10
status: complete
---

# Phase 02 Plan 07: Сводный список расписаний — Summary

**`/schedules` стал тем, чем его называет цель фазы: карточный обзор с именами групп вместо их количества, поиском, двумя осями фильтрации и работающим тумблером — а всё, что разрушает или создаёт, из него ушло; суита выросла с 800 до 838 тестов.**

---

## Performance

- **Duration:** ~61 min
- **Started:** 2026-08-10T16:11Z
- **Completed:** 2026-08-10T17:12Z
- **Tasks:** 3 (Задача 1 — по циклу RED → GREEN)
- **Files:** 9 изменено, 1 создан, 0 удалено
- **Suite:** 800 → **838 passed** (+38)

## Accomplishments

- **SCH-04 прочитан буквально, и это стоило отдельного запроса.** Строка показывала «N групп»; требование и критерий приёмки 4 перечисляют группы наравне с объявлением, каналом, днями и временем — то есть просят СОДЕРЖАНИЕ. Имена разрешаются одним запросом на всю страницу со связкой по владельцу; тест на тридцати расписаниях утверждает, что число запросов по числу расписаний не растёт.
- **Связка по владельцу здесь не формальность.** `Schedule` не имеет собственного `user_id`, а идентификаторы групп лежат внутри записи JSON-массивом: достаточно сохранить СВОЁ расписание с чужим идентификатором, чтобы имя чужой группы отрисовалось в карточке (T-02-34). Запрос ограничен `Group.user_id`, и это закреплено тестом, который сеет чужую группу и требует её отсутствия.
- **Идентификатор, которому не нашлось группы, не превращается ни в пустое имя, ни в завышенный остаток.** Остаток «и ещё K» считается по РАЗРЕШЁННЫМ именам: иначе карточка обещала бы группы, показать которые нечем. Случай «не разрешилось ни одно» назван словами — «группы недоступны», а не пустотой, неотличимой от расписания без групп.
- **Полоса фильтров сделана органом управления, а не украшением.** План отнёс её к Задаче 2 (шаблоны), но шаблонная задача не имеет права трогать `.py`, а полоса, ничего не отбирающая, — заглушка ровно того класса, который этот же план запрещает. Отбор по каналу, состоянию и поиску реализован серверно в Задаче 1 и закреплён тремя тестами «сужает выдачу», а не «присутствует в разметке».
- **Два пустых состояния различаются без второго запроса.** «Расписаний пока нет» и «Расписания не найдены» разводит признак «фильтр применён» — набор фильтров сам отвечает на вопрос, была ли выдача отобрана.
- **Триада переверстана одним заходом, и сентинел совпадает ПОБАЙТОВО.** До правки строки сентинела в `list.html` и `partial_cards.html` отличались отступом — то есть приёмочный критерий плана на них не сходился уже на входе. Теперь обе строки написаны без отступа и совпадают, включая цикл проброса фильтров, появившийся в этом плане.
- **Инварианты Волны 2 не тронуты.** `_owns_ad_and_account`, `own_image_keys` и `sniff_image` не правились ни строкой; проверка владения на маршруте переключения закреплена в новом файле отдельным тестом перекрёстной изоляции (T-02-37).

## Task Commits

1. **Задача 1: данные карточки** — `157e011` (test, RED) → `572d705` (feat, GREEN)
2. **Задача 2: перевёрстка триады** — `f0e93b5`
3. **Задача 3: регрессии SCH-04 и SCH-05** — `0e4438a`

## Files Created/Modified

**Создано:**
- `tests/test_pages/test_schedules_list.py` — 38 тестов: слой данных (имена групп, владелец, признак черновика, значения фильтров) и слой разметки (состав карточки, оба пустых состояния, склонения, отбор, экранирование, переключение)

**Изменено (приложение):**
- `app/pages/schedules.py` — `SUMMARY_GROUP_NAMES`, `CHANNEL_FILTER_VALUES`, `STATE_FILTER_VALUES`, `_clean_choice`, `_filter_params`, `_time_matching_ids`, `_group_names_for`, `_summary_query`, `_summary_count_query`, `_apply_filters`; `_build_schedule_items` получил имена групп и признак черновика; оба страничных обработчика переведены на общий каркас запроса
- `app/static/css/app.css` — третья половина раздела 8: `.sched-lead`, `.sched-count`, `.sched-item`, `.sched-item__head`, `.sched-item__title`, `.sched-item__tags`, `.sched-item__days`, `.sched-item__meta`; `[data-sched-list]` ПЕРЕИСПОЛЬЗОВАН, а не объявлен заново
- `app/templates/schedules/includes/schedule_row.html` — строка таблицы заменена карточкой; `DAY_NAMES` сохранена (её импортирует карточка редактора); удаление и панель подтверждения сняты
- `app/templates/schedules/list.html` — пояснение о переезде, полоса фильтров, счётчик со склонением, контейнер карточек, два пустых состояния
- `app/templates/schedules/partial_cards.html` — остался фрагментом: импорт, цикл, сентинел (8 строк)

**Изменено (тесты):** `test_responsive_markup.py`, `test_htmx_preserved.py`, `test_templates/test_components.py` — разбор ниже.

**Изменено (планирование):** `.planning/REQUIREMENTS.md` — SCH-04 и SCH-05 отмечены выполненными на обеих поверхностях (чекбоксы и таблица прослеживаемости).

## Как переехал каждый потерявший субъект тест

Ни одна тестовая функция не удалена. Девять падений после перевёрстки разобраны поимённо:

| Было | Стало | Субъект |
|---|---|---|
| `test_list_page_has_responsive_primitives[schedules]` — раздел в перечне `data-row` | раздел выведен из перечня; добавлен `test_schedules_summary_list_is_card_based` — ПОЛОЖИТЕЛЬНОЕ утверждение о собственном примитиве списка | заменён равноценным |
| `test_schedules_delete_uses_modal` | `test_schedules_summary_list_offers_no_deletion` — утверждение инвертировано под D-18 | инвертирован намеренно |
| `test_schedules_delete_form_degrades_without_alpine` | `test_schedule_delete_uses_modal_and_a_real_form_in_the_editor` — оба прежних утверждения (панель И настоящая форма) на новом месте | сохранён, место сменилось |
| `test_schedules_cell_labels_present` | `test_schedules_card_names_each_value` — каждое значение названо ключом «ключ — значение» | сохранён, форма сменилась |
| `test_schedules_partial_labels_present` | `test_schedules_partial_names_each_value` — то же во фрагменте прокрутки | сохранён, форма сменилась |
| `test_schedules_row_keeps_grid_area_marker` | `test_schedules_card_title_truncates_instead_of_pushing_controls` — то же обещание «молча ломается раскладка на узкой ширине», но про признак, который его несёт СЕЙЧАС | заменён равноценным |
| `test_rowhead_pages_all_have_a_parametrization_entry` | вход `schedules/list.html` снят, число объявленных 9 → 8 | перепись обновлена |
| `test_row_templates_without_header_are_accounted_for` | вход `schedules/includes/schedule_row.html` снят, число объявленных 9 → 8 | перепись обновлена |
| `test_rowhead_titles_are_covered_by_labels[schedules/list.html]` | прогон ушёл вместе со входом таблицы | параметризация |

**Итог по числу функций:** `test_responsive_markup.py` 113 → 112 функций при 9 снятых прогонах и 7 новых/переписанных — фактически +1 функция и −1 параметризованный прогон таблицы `ROWHEAD_PAGES`. Ни одного обещания не потеряно, каждое названо в таблице выше.

## Decisions Made

1. **Фильтры, поиск и счётчик реализованы серверно в Задаче 1.** План отнёс полосу фильтров к Задаче 2, чьи `<files>` — только шаблоны. Полоса без серверного отбора отвечала бы 200 и не делала ничего: это заглушка того самого класса, который план запрещает (D-17, «полоса прогресса показывает выдуманный процент»). Работа выполнена в файле, объявленном Задачей 1, объём плана не расширен.

2. **Поиск по времени запуска вычисляется в Python.** `times_of_day` — JSON-массив, и переносимого предиката «подстрока внутри элемента массива» у проекта нет. Приведение JSON к тексту средствами SQL проверить нечем: суита ходит в SQLite, а прод — PostgreSQL, и молчаливое расхождение здесь стоило бы неработающего поиска в бою. Взят приём, уже применённый в `app/pages/groups.py` для подсчёта расписаний по группам: один запрос, и только при непустом поиске.

3. **Ключи «Группы · Время · След. запуск» внутри карточки.** Подписи ячеек (`data-cell-label`) существовали, чтобы компенсировать шапку колонок, скрывающуюся на 860px. У карточки шапки нет вовсе — компенсировать нечего, но обещание SC-5 «понятно, что означает каждое значение» осталось. Оно исполнено строками «ключ — значение» на существующем примитиве `.kv`: новых классов под то же самое не заведено.

4. **Бейджи вынесены строкой ниже шапки.** «Объявление в черновике» — 21 символ; в шапке на 320px он вытолкнул бы тумблер или сам оказался бы обрезан. Строка бейджей переносится свободно, а шапка остаётся нерасторжимой: заголовок обрезается первым, тумблер и «Открыть объявление» сохраняют позиции — ровно то, чего требует held-out состояние.

5. **`sched_count_label` импортируется из карточки редактора.** Второе правило русских числительных разъехалось бы с первым, и «1 расписаний» появилось бы ровно в одном из двух мест. Цикла импортов нет: `sched_card.html` импортирует `DAY_NAMES` из `schedule_row.html`, а `schedule_row.html` не импортирует ничего из редактора.

6. **`[data-sched-list]` переиспользован, а не объявлен заново.** Контейнер объявлен планом 02-05 для секции редактора; промежуток 16 между карточками одинаков в обоих местах, и второе объявление того же имени разъехалось бы с первым.

7. **Ячейки дней сводного списка — тот же примитив `.chip` с модификатором размера и `cursor: default`.** В редакторе день выбирается, здесь — показывается; отдельного набора правил под ту же форму не заводится (UI-SPEC: «one primitive, three sizes via modifier»).

8. **Три переписи правятся числом, а не предикатом.** Снятие удаления из сводного списка уменьшило перечень строчных удалений (13 → 12 мест), число импортёров панели (10 → 9), различных имён события (7 → 6) и мест подтверждения (16 → 15). Каждое изменение сопровождено комментарием «почему»; предикаты не тронуты, поэтому молчаливое исчезновение места по-прежнему краснеет.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 — Missing critical functionality] Полоса фильтров без серверного отбора**

- **Найдено:** при разборе Задачи 2 до начала работ
- **Проблема:** план требует в `list.html` поиск, два выбора и действия «Применить»/«Сбросить», а также счётчик найденных и различение двух пустых состояний, — но `app/pages/schedules.py` не принимал ни одного параметра фильтрации, не считал найденных и не знал, был ли отбор. Шаблонная задача файл обработчика править не может. Полоса, отправляющая GET, на который сервер не реагирует, — заглушка: страница отвечает 200, а фильтр не действует.
- **Исправление:** `_clean_choice`, `_filter_params`, `_time_matching_ids`, `_summary_query`, `_summary_count_query`, `_apply_filters` в `app/pages/schedules.py` (файл Задачи 1); оба страничных обработчика приняли `channel`, `state`, `search`.
- **Проверка:** `test_channel_filter_narrows_the_list`, `test_state_filter_narrows_the_list`, `test_search_matches_the_ad_title_and_the_launch_time` — утверждают ОТСУТСТВИЕ невыбранного, а не присутствие выбранного.
- **Committed in:** `572d705`

---

**2. [Rule 3 — Blocking] Приёмочный критерий побайтового сентинела не сходился ДО правки**

- **Найдено:** в Задаче 2, при первой проверке критерия
- **Проблема:** критерий сравнивает `grep`-выдачу целыми строками, а строка сентинела в `list.html` несла отступ в два пробела, тогда как в `partial_cards.html` — ноль. То есть требование плана не выполнялось уже на входе, и «сохранить как есть» означало бы оставить его невыполненным.
- **Исправление:** обе строки написаны без отступа и совпадают побайтово, включая появившийся в этом плане цикл проброса фильтров. Комментарий об инвариантах уточнён словом «ПОБАЙТОВО, включая отступ строки».
- **Committed in:** `f0e93b5`

---

**3. [Rule 3 — Blocking] Три переписи и параметризация разошлись со снятием**

- **Найдено:** в Задаче 2, прогоном `tests/test_templates` и `test_responsive_markup.py`
- **Проблема:** девять падений в двух файлах, не объявленных `files_modified` для Задачи 2 (`tests/test_templates/test_components.py` не объявлен планом вовсе). Все — следствия двух сознательных решений плана: сводный список перестал быть таблицей и перестал предлагать удаление.
- **Исправление:** переписи правятся числами с комментарием «почему»; тесты, потерявшие субъект, переписаны на то же обещание в новой форме (таблица выше).
- **Почему это не ослабление:** ни один предикат не изменён. Проверка «в каждом месте удаления стоит настоящая форма» по-прежнему обходит все объявленные места и краснеет на потере формы; проверка «шаблон с шапкой колонок несёт подписи ячеек» по-прежнему краснеет на новом неподписанном шаблоне.
- **Committed in:** `f0e93b5`

---

**4. [Область] `.planning/REQUIREMENTS.md` — таблица прослеживаемости**

- **Найдено:** после отметки требований штатной командой
- **Проблема:** `requirements.mark-complete` отметил чекбоксы SCH-04 и SCH-05, но вернул `table_unmatched` для обоих: строки таблицы прослеживаемости остались `Pending`. Файл противоречил бы сам себе — требование выполнено в одном месте и не выполнено в соседнем.
- **Исправление:** строки таблицы приведены к `Complete (2026-08-10)`, как у ADS-04…ADS-06.
- **Committed in:** коммит документации плана

---

**Total deviations:** 4 (1 Rule 2 — missing critical functionality, 2 Rule 3 — blocking, 1 расширение области на одну таблицу)
**Impact on plan:** объём работ не расширен. Отклонение 1 — следствие границы между задачами плана, проходящей поперёк одной возможности; 2 — расхождение критерия с состоянием файлов до правки; 3 — прямое следствие двух решений самого плана.

## Issues Encountered

1. **Задача 3 объявлена `tdd="true"`, но её субъект создан Задачей 2.** План ставит перевёрстку раньше закрепляющих её тестов, поэтому цикла RED → GREEN у Задачи 3 быть не может: тесты написаны после своего субъекта и являются РЕГРЕССИОННЫМИ, а не ведущими. Названо прямо, чтобы «гейты соблюдены» не читалось там, где их не было. Задача 1 исполнена настоящим циклом RED → GREEN.
2. **Часть поведений Задачи 1 непроверяема на HTML до Задачи 2.** «Карточка содержит имена групп» на слое Задачи 1 — это состав элемента, приходящего в шаблон; сама отрисовка появляется только с новым макросом. Поэтому RED Задачи 1 утверждает данные (`_group_names_for`, `_build_schedule_items`), а разметку закрепляет Задача 3. Один тест (`test_missing_group_does_not_break_the_page`) по этой причине сужен до «страница переживает идентификатор без группы», а отрисовка оставшегося имени вынесена в `test_summary_card_renders_group_names`.
3. **Линтера в проекте по-прежнему нет** (`ruff` не входит ни в зависимости, ни в dev-группу). Неиспользуемых импортов после правки нет: из `app/pages/schedules.py` ничего не удалялось, добавленные `func`, `or_` и `AD_STATUS_DRAFT` используются.
4. **`-p no:logging` ломает четыре теста мессенджеров.** Промежуточные прогоны шли с этим флагом ради читаемости вывода, и он отключает фикстуру `caplog`. Итоговая проверка выполнена ровно командой плана, без флага.

## Known Stubs

**Заглушек нет.** Каждый элемент сводного списка подключён к настоящим данным и закреплён тестом: имена групп приходят из `Group.name`, признак черновика — из `Ad.status`, дни и времена — из полей записи, счётчик — из отдельного запроса по тому же набору условий, фильтры отбирают. Пустые состояния показываются по реальному отсутствию данных.

Отдельно названо и НЕ является заглушкой: **полосы прогресса отправок нет** — это сознательный отказ показывать выдуманный процент (D-17), а не незавершённая работа.

TODO/FIXME, пропущенных тестов (`skip`/`todo`) в изменённых файлах нет.

**Неисполненные проверки — две, обе записаны в `coverage` с `human_judgment: true` и пустым списком verification:**
- `D18` — `<human-check>` Задачи 3 (визуальная проверка на 320px). Требует стенда; невозможна до применения ревизии `0013` (решение пользователя `defer` из 02-03).
- `D19` — `graphify update .`. Не выполнено в worktree сознательно, см. «User Setup Required».

Записи в `.planning/WINDOWS.md` не добавлялись: файла в проекте нет, а перечисленное выше — не дефекты кода, а работа, требующая среды, которой у исполнителя нет.

## Threat Flags

Новой security-релевантной поверхности вне `<threat_model>` плана не появилось: новых маршрутов, путей аутентификации, доступа к файлам и изменений схемы нет. Состав маршрутов `app/pages/schedules.py` прежний — шесть; `app/routes/schedules.py` не тронут ни строкой.

| Угроза | Диспозиция | Исполнение |
|---|---|---|
| T-02-34 (чужое имя группы в карточке) | mitigate | Запрос имён связан по `Group.user_id`; идентификатор без совпадения в имя не превращается. Закреплено `test_foreign_group_name_never_becomes_a_card_value` |
| T-02-35 (испорченное значение фильтра роняет страницу) | mitigate | `_clean_choice` отсекает неизвестное ДО запроса и даёт вариант «Все». Закреплено шестью unit- и четырьмя integration-параметрами |
| T-02-36 (поисковый термин отражён пользователю) | mitigate | Автоэкранирование Jinja; термин возвращается только в значение поля полосы фильтров. Закреплено `test_hostile_search_term_is_rendered_as_text` |
| T-02-37 (переключение чужого расписания) | mitigate | Маршрут и его проверка владения не тронуты. Закреплено `test_toggle_from_the_list_leaves_a_foreign_schedule_alone` и `test_schedules_toggle_route_unchanged` |
| T-02-38 (запрос имён на каждое расписание) | mitigate | Один запрос на страницу; закреплено счётом операторов на выдаче из тридцати расписаний |
| T-02-SC (установка пакетов) | accept | Пакеты не устанавливались; `pyproject.toml` и `uv.lock` не менялись |

## TDD Gate Compliance

- **Задача 1** исполнена настоящим циклом RED → GREEN, гейты видны в `git log` парой `test(...)` → `feat(...)`. RED `157e011`: сбор модуля падал с `ImportError: cannot import name 'SUMMARY_GROUP_NAMES'` — назначенная причина. GREEN `572d705`: 18 passed. Правило fail-fast соблюдено: четыре теста первого прогона падали по ошибке ТЕСТА (не зарегистрированный фикстурой пользователь), а не кода, и были исправлены до вывода о реализации.
- **Задача 2** объявлена планом как `type="auto"` без `tdd`: она переверстывает шаблоны, и поведенческого утверждения до реализации у неё нет; её проверка — прогон инвариантов бесконечной прокрутки и компонентов.
- **Задача 3** объявлена `tdd="true"`, но её цикл ВЫРОЖДЕН по построению плана: субъект создан Задачей 2, поэтому написанные здесь тесты — регрессионные, зелёные с первого прогона. Гейта `test(...)` → `feat(...)` у неё нет и быть не могло; коммит `0e4438a` — `test(...)` без парного `feat(...)`. Названо явно, а не выдано за соблюдённый гейт.

REFACTOR-коммитов нет: после GREEN чистить было нечего.

## Verification

| Проверка | Результат |
|---|---|
| `uv run pytest tests/ -q` | ✅ **838 passed** (базовая линия 800 + 38) |
| Проверочная команда Задачи 1 (3 файла) | ✅ 129 passed |
| Проверочная команда Задачи 2 (3 цели) | ✅ 61 + 112 passed |
| `uv run pytest tests/test_pages/test_schedule_creation_path_exists.py -q` | ✅ 1 passed — путь создания расписания жив в финальном коммите фазы |
| `diff` сентинелов `list.html` и `partial_cards.html` | ✅ различий нет (побайтово, включая отступ) |
| `grep -rc 'SCHEDULE_COLS\|SCHEDULE_COLUMNS' app/templates/schedules/` | ✅ `0` во всех трёх файлах |
| `grep -c 'sched-item'` в `schedule_row.html` | ✅ `6` (требуется ≥ 1) |
| `grep -c 'row_open'` в `schedule_row.html` | ✅ `0` |
| `grep -c 'progress'` в `schedule_row.html` | ✅ `0` |
| `grep -c '/delete'` в `schedule_row.html` | ✅ `0` — удаление живёт только в редакторе (D-18) |
| `grep -c 'Создание и настройка расписаний — на странице объявления'` | ✅ `1` |
| `grep -c 'filters('` в `list.html` | ✅ `1` — макрос переиспользован, а не форкнут |
| `wc -l app/templates/schedules/partial_cards.html` | ✅ `8` (требуется ≤ 10) |
| `grep -c 'Group.name' app/pages/schedules.py` | ✅ `1` (требуется ≥ 1), рядом — `Group.user_id == user_id` |
| `grep -c 'AD_STATUS_DRAFT' app/pages/schedules.py` | ✅ `2`; строковых литералов состояния — `0` |
| `grep -c 'progress' app/static/css/app.css` | ✅ `8` — не увеличился |
| Селекторы `[data-sched-list]`, `.sched-item`, `.sched-item__days` в `app.css` | ✅ присутствуют |
| `git diff --stat pyproject.toml uv.lock` | ✅ пусто — новых зависимостей нет |
| `git diff --stat app/messengers/ app/routes/` | ✅ пусто — протоколы отправки и JSON-API не тронуты |
| `git diff --stat .planning/STATE.md .planning/ROADMAP.md` | ✅ пусто — общие артефакты оркестратора не тронуты |
| `git diff --diff-filter=D` по всей ветке | ✅ пусто — ни один файл не удалён |
| Миграции / живая база | ✅ не запускались: `alembic` и `just upgrade` не вызывались, `.env` не читался |
| `<human-check>` Задачи 3 | ⛔ **НЕ ВЫПОЛНЕН** — требует стенда (см. `coverage` D18) |
| `graphify update .` | ⛔ **НЕ ВЫПОЛНЕН** в worktree — обоснование в `coverage` D19 и ниже |

## User Setup Required

**Один шаг, унаследованный от правила проекта.**

`./CLAUDE.md` требует запускать `graphify update .` после правок кода, и фаза изменила модель, страничный слой, домен и шаблоны — граф устарел. В worktree шаг НЕ выполнен сознательно:

- `graphify-out/` перечислен в `.gitignore` (строки 54-56), поэтому приёмочный критерий плана «`git status --porcelain graphify-out/` показывает изменения» невыполним по построению: игнорируемый путь в этом выводе не появляется никогда;
- каталога `graphify-out/` в worktree нет вовсе — это была бы полная пересборка (~59 МБ по комментарию в `.gitignore`), выброшенная вместе с одноразовым каталогом при снятии worktree.

**Действие для человека:** выполнить `graphify update .` в основном рабочем каталоге. То же указание стояло в `02-05-SUMMARY.md` и остаётся невыполненным.

Остаётся в силе ограничение из `02-03-SUMMARY.md`: ревизия `0013` не применена ни к какой живой базе решением пользователя. Автоматическая суита от этого не зависит; ручная проверка сводного списка на стенде до её применения невозможна — по этой же причине не выполнен `<human-check>` Задачи 3.

## Next Phase Readiness

**Фаза 2 закрыта по составу требований:** ADS-04…ADS-08 и SCH-04, SCH-05 отмечены выполненными. Оба требования этого плана закрыты тестами, а не намерением.

**Что осталось открытым и кем это подхватывается:**
- **Два `<human-check>` фазы** (`02-05` D18 и `02-07` D18) не выполнены и требуют стенда с применённой ревизией `0013`. Это единственный оставшийся блокер визуальной приёмки фазы.
- **Инлайновая ошибка сохранения в карточке** — открытая строка UI-SPEC E7 с плана 02-05; сводного списка не касается.
- **Разовая чистка чужих значений в `Ad.images`** (T-02-10) — задел бэклога из плана 02-02, вне границы фазы.
- **Мягкая посадка для закладок на снесённые адреса** (T-02-31) — решение D-14 не переоткрывается без данных из логов.

**Задел, сознательно не сделанный здесь:**
- **Постраничная навигация сводного списка** осталась бесконечной прокруткой: UI-SPEC E13 `overflow` прямо называет полосу фильтров инструментом управления объёмом, а пагинацию — не вводимой в этой фазе.
- **Поиск по имени группы.** Плейсхолдер обещает две оси — объявление и время запуска, — и ровно две реализованы. Третья ось потребовала бы того же приёма в Python по уже разрешённым именам и в контракт копирайтинга не входит.

## Self-Check: PASSED

Проверено на диске и в истории git, а не по памяти:

**Файл создан** — `tests/test_pages/test_schedules_list.py` присутствует, 38 тестовых функций.

**Файлы изменены** — все девять присутствуют и содержат заявленные строки: `_group_names_for` и `SUMMARY_GROUP_NAMES` в `app/pages/schedules.py`, `.sched-item` в `app/static/css/app.css`, `sched-item` в `schedule_row.html`, «Создание и настройка расписаний — на странице объявления» в `list.html`, `[x] **SCH-04**` в `REQUIREMENTS.md`.

**Коммиты существуют** — `157e011`, `572d705`, `f0e93b5`, `0e4438a`; все на ветке `worktree-agent-ad65943f685f77bf4`, база `4ffa19c` не переписана.

**Полная суита** — 838 passed на коммите `0e4438a`, командой плана без флагов.

**Удалённых файлов нет** — `git diff --diff-filter=D --name-only 4ffa19c HEAD` пуст.

**Общие артефакты оркестратора не тронуты** — `git diff --stat` по `.planning/STATE.md` и `.planning/ROADMAP.md` пуст.

**Не выполнено намеренно (не дефект, оба названы выше):** `<human-check>` Задачи 3 и `graphify update .`.

---
*Phase: 02-obyavleniya-i-raspisaniya*
*Completed: 2026-08-10*
