---
phase: 02-obyavleniya-i-raspisaniya
plan: 05
subsystem: frontend
tags: [jinja2, css, fastapi, alpine, progressive-enhancement, validation]

# Dependency graph
requires:
  - phase: 02-01
    provides: "Страховочная сетка SC-3, рендер-тест редактора, `_env_file=None` в тестовых Settings"
  - phase: 02-02
    provides: "`_owns_ad_and_account` — владение `ad_id` и `account_id`; вызывается, а не переписывается"
  - phase: 02-03
    provides: "`Ad.status` и `app/constants.py`; старые страницы расписаний живы на `AD_STATUS_PUBLISHED`"
  - phase: 02-04
    provides: "Секция «Расписания» соседом формы объявления, раздел 8 app.css, `_editor_context`"
provides:
  - "Полный цикл расписания внутри редактора объявления: создание, изменение, переключение, удаление без ухода со страницы"
  - "Поле-ПРИЗНАК `return_to=editor`: адрес возврата строит сервер из проверенной на владение записи (защита от открытого редиректа)"
  - "D-08 на сервере: неполное расписание сохраняется выключенным и не может быть возобновлено"
  - "`_clean_ints` / `_clean_times` — фильтрация повторяющихся полей формы до приведения типов"
  - "Макрос `ads/includes/sched_card.html` и вторая половина раздела 8 app.css"
  - "Именованные кнопки отправки как единственный механизм пресетов дней, группового действия и работы со временами — один код на базовый и улучшенный путь"
  - "Параметр `?sched={id}` у `/ads/{id}/edit` — разворачивание карточки без JavaScript"
affects: [02-06, 02-07]

actuals:
  tokens: 27000
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Признак происхождения в форме + построение адреса редиректа на сервере из уже проверенной записи"
    - "Фильтрация повторяющихся полей формы ДО приведения типов: испорченное значение отбрасывается, остальные выживают"
    - "Пресеты и работа со списком — именованные кнопки отправки, обработанные СЕРВЕРОМ: базовый и улучшенный путь физически одни и те же"
    - "Одно определение неполноты (`_is_complete`) на четыре обработчика и на разметку карточки"
    - "`.chip` как один примитив в трёх размерах через модификатор, вместо трёх наборов правил"
    - "`populate_existing=True` вместо `expire_all()` там, где сессия теста общая с обработчиком"

key-files:
  created:
    - app/templates/ads/includes/sched_card.html
    - tests/test_pages/test_editor_schedules.py
  modified:
    - app/static/css/app.css
    - app/templates/ads/form.html
    - app/pages/schedules.py
    - app/pages/ads.py
    - tests/test_pages/test_schedule_ownership.py
    - tests/test_pages/test_responsive_markup.py
    - tests/test_templates/test_components.py

key-decisions:
  - "`account_id` на страничных маршрутах расписаний стал НЕОБЯЗАТЕЛЬНЫМ: при нескольких аккаунтах ни один не выбран заранее, и отказ формы 422 лишил бы пользователя единственного способа добавить карточку в редакторе"
  - "Правка полного расписания НЕ снимает ручную паузу: выключается только неполное (D-08). Иначе тумблер перестал бы что-либо значить"
  - "Блокировка возобновления расширена с «нет аккаунта» (issue #35) до полной неполноты: отвязанное расписание — частный случай"
  - "Пресеты дней, «ВЫБРАТЬ ВСЕ», «+ ВРЕМЯ» и «Убрать время» обрабатываются СЕРВЕРОМ, а не Alpine: одна ветка кода вместо двух, и без скрипта кнопка не превращается в заглушку"
  - "«+ ДОБАВИТЬ ПЕРВОЕ» — отдельная форма рядом с `empty_state`, а не действие макроса: макрос умеет только ссылку, а создание расписания обязано быть POST-ом"
  - "Имя события панели подтверждения — своё (`sched-del-`), а не общее со строкой сводного списка (`schedule-del-`)"
  - "`.group-pick__count` несёт внешний идентификатор группы, а не число участников: поля с числом участников у пользовательской группы в схеме нет, и выдуманное число было бы тем же дефектом, что запрещённая D-17 полоса прогресса"

patterns-established:
  - "Поле возврата в форме — ПРИЗНАК, не адрес: значение в редирект не попадает ни при каких условиях"
  - "Предикат заполненности объявляется один раз в обработчике и переиспользуется разметкой через тот же набор условий"
  - "Именованная кнопка отправки с `value` — способ передать «убрать вот это» без JavaScript (обобщение приёма `remove_image` из 02-04)"

requirements-completed: [ADS-07, ADS-08]

coverage:
  - id: D1
    description: "Расписание создаётся, изменяется и удаляется прямо в редакторе объявления (ADS-07, ADS-08, SC-3)"
    requirement: ADS-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_create_from_editor_returns_to_the_editor"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_update_from_editor_returns_to_the_editor"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_delete_from_editor_returns_to_the_editor_and_removes_the_schedule"
        status: pass
    human_judgment: false
  - id: D2
    description: "После сохранения или удаления пользователь остаётся в редакторе, а не на сводном списке"
    requirement: ADS-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_toggle_from_editor_returns_to_the_editor"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_create_without_the_editor_marker_still_goes_to_the_summary_list"
        status: pass
    human_judgment: false
  - id: D3
    description: "Каждое расписание сохраняется отдельным запросом сразу; клиентского состояния нет (D-07)"
    requirement: ADS-07
    verification:
      - kind: other
        ref: "app/templates/ads/includes/sched_card.html — у карточки собственные формы на /schedules/{id}/edit, /toggle, /delete; общего состояния в JavaScript в файле нет"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_editor_markup_has_no_nested_forms"
        status: pass
    human_judgment: false
  - id: D4
    description: "Неполное расписание сохраняется выключенным, с бейджем «Не заполнено» и подсказкой; тумблер недоступен (D-08)"
    requirement: ADS-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_schedule_without_groups_is_saved_disabled"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_schedule_without_days_is_saved_disabled"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_schedule_without_times_is_saved_disabled"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_schedule_without_account_is_saved_disabled"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_incomplete_schedule_cannot_be_switched_on"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_account_without_groups_says_so (тумблер размечен disabled)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Смена аккаунта очищает выбранные ранее группы; при пустом результате расписание выключается"
    requirement: ADS-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_changing_the_account_clears_the_previously_chosen_groups"
        status: pass
    human_judgment: false
  - id: D6
    description: "Значения времени вне формата ЧЧ:ММ отбрасываются до вычисления запуска — отказ валидации, а не 500 (T-02-24)"
    requirement: ADS-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_malformed_time_does_not_crash_and_is_dropped"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_malformed_time_on_update_does_not_crash"
        status: pass
    human_judgment: false
  - id: D7
    description: "Нечисловые и внедиапазонные значения в списках групп и дней не роняют обработчик (T-02-25)"
    requirement: ADS-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_non_numeric_group_and_day_values_do_not_crash"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_out_of_range_day_values_are_dropped"
        status: pass
    human_judgment: false
  - id: D8
    description: "Каждая карточка — самостоятельная форма ВНЕ формы объявления: вложенных форм нет"
    requirement: ADS-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_editor_markup_has_no_nested_forms"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_editor_schedule_section_is_a_sibling_of_the_ad_form"
        status: pass
    human_judgment: false
  - id: D9
    description: "Базовый путь без JavaScript: сохранение, удаление и разворачивание — настоящие формы и ссылки"
    requirement: ADS-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_schedule_delete_is_a_real_form"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_selected_schedule_is_the_expanded_one"
        status: pass
    human_judgment: false
  - id: D10
    description: "Пользователь без аккаунтов видит подсказку со ссылкой в раздел аккаунтов"
    requirement: ADS-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_user_without_accounts_is_offered_to_connect_one"
        status: pass
    human_judgment: false
  - id: D11
    description: "Единственный аккаунт выбран заранее; при нескольких не выбран ни один"
    requirement: ADS-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_add_schedule_form_preselects_a_single_account"
        status: pass
    human_judgment: false
  - id: D12
    description: "Пустое состояние называет последствие; счётчик считает все расписания и склоняется по-русски"
    requirement: ADS-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_editor_without_schedules_names_the_consequence"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_section_caption_is_declined (три параметра: 1 / 3 / 5)"
        status: pass
    human_judgment: false
  - id: D13
    description: "Карточка отрисовывает реальные данные, а не пустые строки; развёрнута ровно одна"
    requirement: ADS-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_editor_card_renders_data"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_selected_schedule_is_the_expanded_one"
        status: pass
    human_judgment: false
  - id: D14
    description: "Путь из редактора не обходит проверок владения `ad_id` и `account_id` (T-02-26)"
    requirement: ADS-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_editor_path_rejects_foreign_ad"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_editor_path_rejects_foreign_account"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_editor_path_rejects_swapping_in_a_foreign_ad"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_schedule_ownership.py#test_editor_path_cannot_delete_a_foreign_schedule"
        status: pass
    human_judgment: false
  - id: D15
    description: "Значение поля возврата не попадает в редирект — открытого редиректа нет (T-02-23)"
    requirement: ADS-08
    verification:
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_return_value_never_reaches_the_redirect_verbatim"
        status: pass
    human_judgment: false
  - id: D16
    description: "Полоса прогресса отправок в карточке расписания не появляется (D-17)"
    requirement: ADS-07
    verification:
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_editor_collapses_to_one_column_and_shrinks_day_cells"
        status: pass
      - kind: other
        ref: "grep -c 'progress' app/static/css/app.css → 8, значение до правки"
        status: pass
    human_judgment: false
  - id: D17
    description: "Оба пути создания расписания живы одновременно (D-16, SC-3)"
    requirement: ADS-07
    verification:
      - kind: integration
        ref: "tests/test_pages/test_schedule_creation_path_exists.py#test_schedule_creation_path_exists"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_editor_schedules.py#test_summary_list_keeps_working"
        status: pass
    human_judgment: false
  - id: D18
    description: "Шесть held-out состояний на 320px: обрезка имени аккаунта и группы, свёрнутая шапка при 7 днях и 6 временах, длинный заголовок в теле окна подтверждения, экранирование тела окна"
    requirement: ADS-08
    verification: []
    human_judgment: true
    rationale: "Backstop-строки must_haves. Правила раздела 8 написаны под них (min-width: 0 и обрезка многоточием у .sched-card__sum, .chip__label и .group-pick__name; nowrap на шапке), а экранирование тела окна обеспечено автоэкранированием Jinja — но НИ ОДНА из шести не закреплена автоматическим тестом. `<human-check>` Задачи 3 НЕ ВЫПОЛНЕН — см. «Не выполнено»."

# Metrics
duration: 41min
completed: 2026-08-10
status: complete
---

# Phase 02 Plan 05: Расписания в редакторе объявления — Summary

**Расписание настраивается целиком внутри редактора: карточка на расписание со своими формами вне формы объявления, полный цикл создания, изменения, переключения и удаления без ухода со страницы, неполное расписание сохраняется выключенным и не может быть включено, а значения, не приводящиеся к своему типу, отбрасываются до разбора — прямой POST мимо браузера теперь даёт отказ валидации вместо 500.**

---

## Performance

- **Duration:** ~41 min
- **Started:** 2026-08-10T13:38:02Z
- **Completed:** 2026-08-10T14:19:11Z
- **Tasks:** 3 (Задачи 2 и 3 — по циклу RED → GREEN)
- **Files modified:** 9 (2 создано, 7 изменено)
- **Suite:** 766 → **803 passed** (+37)

## Accomplishments

- **Поле возврата — признак, а не адрес, и это закреплено отдельным тестом.** `test_return_value_never_reaches_the_redirect_verbatim` посылает `return_to=https://evil.example/steal` и утверждает, что в `Location` нет ни домена, ни абсолютного адреса. Реализация, подставляющая значение поля в редирект, прошла бы все остальные тесты плана и провалила бы ровно этот — то есть открытый редирект (T-02-23) закрыт утверждением, а не намерением.
- **D-08 доведён от домена до интерфейса и до маршрута переключения.** Домен и раньше не мог выбрать неполное расписание к отправке (`compute_next_run_at` возвращает пустоту), но обработчик оставлял `is_active=True` — расписание выглядело активным и не отправляло ничего. Теперь неполнота выключает расписание на создании и на изменении, а возобновление отклоняется и на маршруте переключения: разметка с `disabled` — не точка принуждения, и прямой POST получает тот же отказ.
- **Блокировка возобновления обобщена, а не продублирована.** Правило issue #35 («отвязанное расписание нельзя возобновить») оказалось частным случаем D-08: отсутствие аккаунта — одна из четырёх незаполненностей. Второй ветки не заведено, `_is_complete` один на четыре обработчика и на разметку карточки.
- **Базовый путь и улучшенный — физически один и тот же код.** Пресеты дней, «ВЫБРАТЬ ВСЕ / СНЯТЬ ВСЕ», «+ ВРЕМЯ» и «Убрать время» сделаны именованными кнопками отправки, которые обрабатывает **сервер**. Alpine на них не навешен вовсе: расходиться нечему, и с выключенным скриптом ни одна кнопка не превращается в молчаливую заглушку.
- **Инварианты Волны 2 переиспользованы, а не переписаны.** `_owns_ad_and_account` вызывается на тех же четырёх местах и на том же шаге — до первой записи в модель. Четыре новых теста в `test_schedule_ownership.py` утверждают, что признак происхождения на проверку не влияет: он подконтролен отправителю ровно так же, как `ad_id` и `account_id`.
- **Структура редактора, заложенная 02-04, сохранена и проверена позиционно.** Секция расписаний осталась **соседом** формы объявления; тест утверждает и отсутствие вложенности (`_max_form_nesting == 1` в трёх состояниях страницы), и порядок: закрытие `#ad-form` идёт РАНЬШЕ формы добавления расписания. Признак `required` в редактор не возвращён.

## Task Commits

1. **Задача 1: макрос карточки и вторая половина раздела 8** — `c4d172f`
2. **Задача 2: страничные обработчики расписаний** — `2233446` (test, RED) → `ec01f31` (feat, GREEN)
3. **Задача 3: секция расписаний в редакторе** — `6c45c4e` (test, RED) → `f5cb8d4` (feat, GREEN)

## Files Created/Modified

**Создано:**
- `app/templates/ads/includes/sched_card.html` — макрос карточки с явными параметрами: свёрнутая шапка (иконка канала, сводка, бейдж, тумблер, «РАЗВЕРНУТЬ»), развёрнутое тело (аккаунт чипсами, группы строками, семь дней, ряд времён, «УДАЛИТЬ РАСПИСАНИЕ»), панель подтверждения соседом карточки; плюс макросы `sched_count_label` и `account_label`
- `tests/test_pages/test_editor_schedules.py` — 30 тестов, гейт плана 02-06

**Изменено:**
- `app/static/css/app.css` — вторая половина раздела 8: `[data-sched-list]`, `[data-sched-card]`, `.sched-card__head/__body/__sum/__expand/__block/__actions/__tz/__hint`, `.chip-set`, `.chip`, `.chip--on`, `.day-grid`, `.time-set`, `.time-pill`, `.group-pick*`; новых токенов нет, медиазапрос 400px не продублирован, селектора полосы прогресса не появилось
- `app/templates/ads/form.html` — заглушка секции заменена списком карточек, счётчиком со склонением и настоящей формой добавления
- `app/pages/schedules.py` — `RETURN_TO_EDITOR`, `_TIME_RE`, `_clean_times`, `_clean_ints`, `_is_complete`, `_editor_redirect`, `_apply_named_actions`, `_groups_of_account`; четыре обработчика переписаны на них
- `app/pages/ads.py` — `_editor_context` дополнена расписаниями, аккаунтами, группами и выбором развёрнутой карточки; у `/ads/{id}/edit` появился параметр `sched`
- `tests/test_pages/test_schedule_ownership.py` — 4 теста пути из редактора
- `tests/test_pages/test_responsive_markup.py` — 3 теста секции расписаний
- `tests/test_templates/test_components.py` — перепись мест подтверждения удаления 9/6/15 → 10/7/16

## Decisions Made

1. **`account_id` на страничных маршрутах стал необязательным.** При нескольких подключённых аккаунтах ни один не выбирается заранее (UI-SPEC E4 `zero-one-many`), а «+ РАСПИСАНИЕ» обязано создать карточку немедленно — иначе добавить расписание в редакторе стало бы невозможно. Схема это уже допускала: `account_id` nullable с `ON DELETE SET NULL` (issue #35), а `_owns_ad_and_account` с самого начала обрабатывает пустое значение как законное. Расписание без аккаунта по D-08 сохраняется выключенным, и проверка групп при пустом аккаунте даёт пустой список — ослабления проверок не произошло.

2. **Правка полного расписания не снимает ручную паузу.** Выключается только неполное. Обратное решение — «сохранил, значит включил» — молча возобновляло бы рассылку, поставленную пользователем на паузу, и тумблер перестал бы что-либо значить.

3. **Пресеты и работа со списками обрабатываются сервером, а не Alpine.** UI-SPEC называет их именованными кнопками отправки для базового пути. Оставить их только клиентскими значило бы, что без скрипта кнопка есть, а действия нет — заглушка, которую невозможно заметить. Серверная обработка даёт одну ветку кода вместо двух и круговой ответ, который сохраняет карточку развёрнутой через `?sched={id}`.

4. **«+ ВРЕМЯ» добавляет конкретное значение 09:00, а не пустую таблетку.** Пустая строка отбрасывается фильтром времён, и без JavaScript кнопка не оставляла бы после себя ничего видимого. Значение совпадает с умолчанием старой формы расписания.

5. **«+ ДОБАВИТЬ ПЕРВОЕ» — форма рядом с `empty_state`, а не действие макроса.** Макрос умеет только ссылку (`action_href`), а создание расписания обязано быть POST-ом. Форкать или расширять макрос запрещено правилом «макросы Фазы 1 переиспользуются без изменений», поэтому копия пустого состояния приходит из макроса, а действие стоит непосредственно за ним.

6. **Имя события панели подтверждения — своё (`sched-del-`).** Разметка сводного списка использует `schedule-del-`; общее имя открывало бы две панели одним событием, если обе разметки окажутся на одной странице. UI-SPEC называет ровно `sched-del-{id}`.

7. **`.group-pick__count` несёт внешний идентификатор группы.** UI-SPEC отводит этому месту счётчик участников, но поля с числом участников у пользовательской `Group` в схеме нет — оно живёт только в админском справочнике `GroupInfo`, не связанном с группой ключом. Показывать выдуманное число — тот же дефект, что запрещённая D-17 полоса прогресса. Место, кегль и поведение при переполнении сохранены.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Перепись мест подтверждения удаления в `tests/test_templates/test_components.py`**

- **Найдено:** во время Задачи 1
- **Проблема:** `test_modal_site_inventory` — трёхсчётная перепись панелей подтверждения по всем шаблонам. Карточка расписания принесла десятого импортёра, седьмое имя события и шестнадцатое место, и перепись перестала сходиться. Тест сделал ровно то, ради чего написан; ожидаемые числа обязаны признать появление сознательным. Файл в `files_modified` плана не значится.
- **Исправление:** `MODAL_IMPORTERS` 9 → 10, `MODAL_EVENT_NAMES` 6 → 7, `MODAL_PLACES` 15 → 16 с комментарием, почему имя события своё и почему место не входит в `ROW_DELETE_SITES`. Ни одно утверждение не ослаблено — изменены только объявленные числа.
- **Проверка:** `tests/test_templates` — 46 passed.
- **Committed in:** `c4d172f`

---

**2. [Rule 3 — Blocking] `account_id` стал необязательным полем формы**

- **Найдено:** во время Задачи 2 (RED: `test_schedule_without_account_is_saved_disabled` падал с 422)
- **Проблема:** `Form(...)` требовал аккаунт, а D-08 прямо перечисляет «не выбран аккаунт» среди состояний, которые обязаны СОХРАНЯТЬСЯ выключенными. Без правки «+ РАСПИСАНИЕ» при нескольких аккаунтах давало бы 422 вместо новой карточки.
- **Исправление:** `account_id: int | None = Form(None)` на создании и изменении. Маршрутов не добавлено и не убрано (`grep -c '@router\.'` = 8, как до правки), имена полей не изменены.
- **Проверка:** `tests/test_pages/test_schedule_ownership.py` (11 тестов), `tests/test_pages/test_schedules_detached_account.py`, `tests/test_routes/test_schedules_toggle_detached.py` — зелёные без правок.
- **Committed in:** `ec01f31`

---

**3. [Область] Серверная обработка пресетов, группового действия и работы со временами**

- **Найдено:** во время Задачи 1, при разметке развёрнутого тела
- **Проблема:** план требует в карточке пресеты «БУДНИ»/«КАЖДЫЙ ДЕНЬ», действие «ВЫБРАТЬ ВСЕ / СНЯТЬ ВСЕ», «+ ВРЕМЯ» и «Убрать время», а UI-SPEC называет их именованными кнопками отправки базового пути. Без серверной обработки такая кнопка отправляет форму и не делает ничего — заглушка, неотличимая от рабочей кнопки.
- **Исправление:** `_apply_named_actions` в `app/pages/schedules.py` — четыре необязательных поля (`days_preset`, `groups_preset`, `add_time`, `remove_time`), обрабатываемые обоими сохраняющими обработчиками. Alpine на эти кнопки не навешивается вовсе.
- **Committed in:** `ec01f31`

---

**4. [Область] `populate_existing=True` вместо `expire_all()` в тестах**

- **Найдено:** во время Задачи 2 (RED)
- **Проблема:** сессия теста — та же, что у обработчика (`dependency_overrides`), и после `expire_all()` часть атрибутов объекта из карты идентичности оставалась истёкшей: первое обращение уходило в ленивую загрузку вне greenlet-контекста, и тест падал `MissingGreenlet` вместо своего утверждения — то есть скрывал бы результат проверки.
- **Исправление:** `_reload` и `_all_schedules` в новом тестовом файле читают с `execution_options(populate_existing=True)`. Существующие тесты с `expire_all()` не тронуты.
- **Committed in:** `2233446`

---

**Total deviations:** 4 (2 Rule 3 — blocking, 2 расширения области)
**Impact on plan:** объём работ не расширен. Отклонения 1 и 2 — следствия перекрёстных переписей и жёсткой сигнатуры формы; 3 и 4 — следствия требования базового пути без JavaScript и общей сессии в тестовой фикстуре.

## Issues Encountered

1. **Требование «маршрутов и имён полей не менять» и требование «сохранять расписание без аккаунта» противоречат друг другу на уровне сигнатуры.** Разрешено сужением: маршруты, их состав и ИМЕНА полей действительно не изменились, изменилась обязательность одного поля. Альтернатива — фиктивный аккаунт-заглушка в форме — создала бы расписание, ссылающееся на несуществующий аккаунт.

2. **Пустое состояние «нет аккаунтов» существует в двух местах и это не дублирование.** На уровне секции оно отвечает на вопрос «почему я не могу добавить расписание», внутри карточки — «почему полоса чипсов пуста у уже существующего расписания». Второй случай возникает после удаления аккаунта (issue #35), когда карточки есть, а аккаунтов нет.

3. **Проверка «нет вложенных форм» не заменяет проверку положения секции.** Секция, уехавшая ВЫШЕ формы объявления, вложенных форм не создаёт, но ломает порядок чтения на ≤900px (D-14). Поэтому утверждений два: глубина вложенности и позиция закрытия `#ad-form` относительно формы добавления.

## Known Stubs

**Заглушек нет.** Каждая часть секции подключена к настоящим данным и закреплена тестом: карточки читают расписания объявления, чипсы — аккаунты пользователя, строки групп — активные группы выбранного аккаунта, времена и дни — поля записи. Пустые состояния показываются по реальному отсутствию данных, а не как плейсхолдеры.

Отдельно названо и НЕ является заглушкой: `.group-pick__count` показывает внешний идентификатор группы вместо числа участников — данных о числе участников у пользовательской группы в схеме нет (см. «Решения», п. 7). Это сознательный отказ показывать выдуманное число, а не незавершённая работа.

## Не выполнено

**`<human-check>` Задачи 3 НЕ ВЫПОЛНЕН.** Ручная проверка в браузере (полный цикл расписания без смены страницы, сворачивание и разворачивание карточки, шесть held-out состояний на 320px) требует запущенного стенда. Она невозможна до применения ревизии `0013`: модель спрашивает `ads.status`, которой в живой базе ещё нет — решение пользователя `defer`, зафиксированное планом 02-03. Пункт вынесен в `coverage` строкой `D18` с `human_judgment: true` и пустым списком проверок; считать его выполненным нельзя.

## Threat Flags

Новой security-релевантной поверхности вне `<threat_model>` плана не появилось: новых маршрутов, путей аутентификации, доступа к файлам и изменений схемы нет. Состав маршрутов `app/pages/schedules.py` прежний — восемь.

| Угроза | Реализация |
|---|---|
| T-02-23 | `_editor_redirect` строит адрес из `ad_id` уже проверенной на владение записи; значение поля используется ТОЛЬКО в сравнении с константой `RETURN_TO_EDITOR`. Закреплено `test_return_value_never_reaches_the_redirect_verbatim` |
| T-02-24 | `_clean_times` по регулярному выражению `^([01]\d\|2[0-3]):([0-5]\d)$` до вызова `compute_next_run_at`. Закреплено двумя тестами (создание и изменение) |
| T-02-25 | `_clean_ints` с диапазоном 0..6 для дней; непреобразуемые значения отбрасываются, остальные выживают. Закреплено двумя тестами |
| T-02-26 | `_owns_ad_and_account` на прежних местах и на прежнем шаге; признак происхождения на проверку не влияет. Закреплено четырьмя тестами в `test_schedule_ownership.py` |
| T-02-27 | Пустой результат проверки принадлежности групп выключает расписание и обнуляет время следующего запуска. Закреплено `test_changing_the_account_clears_the_previously_chosen_groups` |
| T-02-28 | Тело окна подтверждения собирается из данных и рендерится автоэкранированием Jinja; готовой разметки макросу не передаётся |

`T-02-SC` (`accept`) — пакеты не устанавливались, `pyproject.toml` и `uv.lock` не менялись.

## TDD Gate Compliance

Задачи 2 и 3 исполнены по циклу RED → GREEN, гейты видны в `git log` парами `test(...)` → `feat(...)`.

- **Задача 2.** RED `2233446`: 14 failed, 14 passed. Каждое падение проверено на назначенную причину: адрес редиректа `/schedules` вместо редактора, `is_active` True у неполного расписания, 422 на расписании без аккаунта, 500 на кривом времени и нечисловых идентификаторах, сохранённый день недели вне диапазона. Четырнадцать зелёных в RED — регрессионные контракты существующего поведения (редирект на сводный список без признака, проверки владения, полное расписание активно). GREEN `ec01f31`: 28 passed.
- **Задача 3.** RED `6c45c4e`: 8 failed, 135 passed — падала ровно разметка секции. Четыре утверждения были зелёными уже в RED намеренно: копия пустого состояния и склонение счётчика приехали заглушкой плана 02-04 и закрепляются как контракт, отсутствие вложенных форм — страховка на будущую разметку, правила адаптива — результат Задачи 1. GREEN `f5cb8d4`: 216 passed на всей проверочной команде задачи.

Правило fail-fast соблюдено: в каждом RED-прогоне проверялось, что тест падает по назначенной причине. Один случай был исправлен именно поэтому — `test_complete_schedule_is_saved_active_with_a_next_run` в первом RED-прогоне падал `MissingGreenlet`, то есть по ошибке ТЕСТА, а не кода (см. «Отклонения», п. 4).

Задача 1 объявлена планом как `type="auto"` без `tdd`: она создаёт таблицу стилей и шаблон-макрос, для которых поведенческого утверждения до реализации не существует; её проверка — компиляция шаблона и зелёные тесты компонентов.

REFACTOR-коммитов нет: после GREEN чистить было нечего ни в одной задаче.

## Verification

| Проверка | Результат |
|---|---|
| `uv run pytest tests/ -q` | ✅ **803 passed** (базовая линия 766 + 37 новых) |
| `uv run pytest tests/test_templates tests/test_pages/test_responsive_markup.py -q` (Задача 1) | ✅ 156 passed |
| Компиляция `ads/includes/sched_card.html` (Задача 1) | ✅ код 0 |
| Проверочная команда Задачи 2 (7 файлов) | ✅ 51 passed |
| Проверочная команда Задачи 3 (5 целей) | ✅ 216 passed |
| `grep -c 'progress' app/static/css/app.css` | ✅ `8` — не увеличился |
| `grep -c 'DAY_NAMES' app/templates/ads/includes/sched_card.html` | ✅ `5` (требуется > 0) |
| `grep -c "{% set DAY_NAMES" app/templates/ads/includes/sched_card.html` | ✅ `0` — карта импортируется, а не объявляется заново |
| `grep -c 'Убрать время' app/templates/ads/includes/sched_card.html` | ✅ `1` (требуется ≥ 1) |
| `grep -c 'Не заполнено' app/templates/ads/includes/sched_card.html` | ✅ `3` (требуется ≥ 1) |
| `grep -c 'compute_next_run_at' app/pages/schedules.py` | ✅ `5` (требуется ≥ 3) |
| `grep -c '@router\.' app/pages/schedules.py` | ✅ `8` — то же число, что до правки |
| `grep -c 'sched_card' app/templates/ads/form.html` | ✅ `2` (требуется ≥ 1) |
| `grep -c 'Расписаний пока нет' app/templates/ads/form.html` | ✅ `2` (требуется ≥ 1) |
| `grep -c 'is_active' app/templates/ads/form.html` | ✅ `0` |
| `uv run pytest tests/test_pages/test_schedule_creation_path_exists.py -q` | ✅ 1 passed — оба пути живы |
| `git diff --stat pyproject.toml uv.lock` | ✅ пусто — новых зависимостей нет |
| `git diff --stat app/messengers/` | ✅ пусто — протоколы отправки не тронуты |
| `git diff --stat .planning/STATE.md .planning/ROADMAP.md` | ✅ пусто — общие артефакты оркестратора не тронуты |
| `<human-check>` Задачи 3 | ⛔ **НЕ ВЫПОЛНЕН** — требует стенда с применённой ревизией 0013 |

## User Setup Required

**Ничего нового.** Внешние сервисы не настраиваются, пакеты не устанавливались, миграций план не заводит.

Остаётся в силе шаг из `02-03-SUMMARY.md`: ревизия `0013` не применена ни к какой живой базе решением пользователя. До её применения ручная проверка редактора на стенде невозможна. Автоматическая суита от этого не зависит.

Дополнительно (не блокирует): в основном рабочем каталоге стоит обновить граф знаний — `graphify update .`. В worktree это не сделано намеренно: `graphify-out/` в `.gitignore`, и сборка была бы выброшена вместе с одноразовым каталогом.

## Next Phase Readiness

**Готово для плана 02-06 (снос старых страниц, вторая половина D-16):**
- **Предусловие 02-06 выполнено:** `uv run pytest tests/test_pages/test_editor_schedules.py -q` — 30 passed. Новый путь настройки расписаний работает целиком.
- `SCHEDULE_CREATE_ACTIONS` в `tests/test_pages/test_schedule_creation_path_exists.py` править НЕ нужно: путь из редактора уходит на тот же `POST /schedules/new`, и сетка уже видит его формой в редакторе.
- **Что именно снимает 02-06 — только GET-страницы** `/schedules/new` и `/schedules/{id}/edit` вместе с `app/templates/schedules/form.html`. Обработчики `POST /schedules/new` и `POST /schedules/{id}/edit` обязаны остаться: на них ходит карточка редактора. Снос POST-маршрутов оборвал бы новый путь ровно в тот момент, когда старый уже удалён.
- `schedules/includes/schedule_row.html` тронуть придётся аккуратно: `DAY_NAMES` из него импортирует карточка редактора. Файл целиком уходит только в плане 02-07 вместе с перевёрсткой сводного списка — до тех пор карта дней живёт там.

**Готово для плана 02-07 (сводный список):**
- `[data-sched-list]` объявлен и уже используется секцией редактора — сводный список может опереться на тот же контейнер.
- `.chip`, `.day-grid`, `.time-pill`, `.group-pick` — общие примитивы раздела 8, не привязанные к редактору; ячейка дня сводного списка (40×32) потребует только модификатора размера.
- Комментарий Pitfall 12 в `schedules_toggle` переписан на неполноту вообще: путь восстановления теперь называется редактором объявления, а не исчезающей формой расписания.

**Задел, сознательно не сделанный здесь:**
- **Число участников группы в строке выбора.** Данных нет в `Group`; связать её с админским `GroupInfo` по паре (тип мессенджера, внешний идентификатор) — отдельное решение о модели, в границу этого плана не входившее.
- **Инлайновая ошибка сохранения внутри карточки.** UI-SPEC E7 `error` требует, чтобы отказ оставался в своей карточке. Сегодня отказ по владению уводит редиректом (прежнее поведение маршрута), и это не регрессия — но и не полная реализация строки контракта. Уместное место — план, который принесёт htmx-путь для карточек (D-07 «отдельным запросом сразу» выполнен формами, но без внеполосного ответа).
- **htmx на карточках расписаний.** Каждая карточка сохраняется отдельным запросом, как требует D-07, но запрос — обычная отправка формы с редиректом, а не внеполосный ответ. Работает и без JavaScript; ускорение — вопрос отдельного решения.

## Self-Check: PASSED

Проверено на диске и в истории git, а не по памяти:

**Файлы созданы** — оба присутствуют: `app/templates/ads/includes/sched_card.html`, `tests/test_pages/test_editor_schedules.py`.

**Коммиты существуют** — `c4d172f`, `2233446`, `ec01f31`, `6c45c4e`, `f5cb8d4`; все на ветке агента, база `b74e74b` не переписана.

**Полная суита** — 803 passed на коммите `f5cb8d4`.

**Общие артефакты оркестратора не тронуты** — `git diff --stat` по `.planning/STATE.md` и `.planning/ROADMAP.md` пуст.

**Не выполнено намеренно (не дефект):** `<human-check>` Задачи 3 — ручная визуальная проверка на стенде, невозможная до применения ревизии `0013` (решение пользователя `defer`, зафиксированное планом 02-03). Отмечено в `coverage` строкой `D18` и отдельным разделом «Не выполнено».

---
*Phase: 02-obyavleniya-i-raspisaniya*
*Completed: 2026-08-10*
