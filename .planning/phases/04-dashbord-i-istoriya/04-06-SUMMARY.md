---
phase: 04-dashbord-i-istoriya
plan: 06
subsystem: ui
tags: [jinja2, fastapi, filters, history, css, progressive-enhancement]

requires:
  - phase: 04-dashbord-i-istoriya
    provides: "плана 04-01: apply_history_filters / history_filter_params / history_count / HISTORY_PERIODS и константы статусов журнала в app/application/analytics/send_analytics.py"
  - phase: 04-dashbord-i-istoriya
    provides: "плана 04-05: конвенции паршала и инвариант «разметка сентинела на странице и в паршале идентична»"
  - phase: 01-interfejsnyj-fundament
    provides: "CSS-примитив .chip / .chip-set / .chip--on, примитив линейки .count-rule, макросы mono / empty_state / filters / select_field, глобал plural_ru"
provides:
  - "Макрос filter_chips — группа чипсов-ссылок для одной оси фильтрации истории"
  - "STATUS_CHIPS / MESSENGER_CHIPS / PERIOD_CHIPS и _clean_choice в app/pages/history.py — единственный источник допустимых значений осей раздела"
  - "history_total в контексте списка истории — точное число найденного тем же набором фильтров (опора потолка выгрузки плана 04-08)"
  - "Собственный файл тестов раздела: tests/test_pages/test_history.py"
  - "CSS-модификатор чипса-ссылки поверх примитива .chip и полоса групп .chip-bar"
affects: [04-08, 04-10, phase-6-admin]

actuals:
  tokens: 43049
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Чипс-ссылка вместо чипса-поля: один клик без кнопки «Применить» и работоспособность при выключенном JavaScript"
    - "Наборы значений осей объявлены обработчиком и из них же строятся допустимые множества отсечки — нарисованное и принимаемое не могут разойтись"
    - "Скрытые поля соседних осей внутри формы выпадающего списка: форма отправляет только свои поля и без них сбросила бы чипсы"
    - "Связь двух перечней одного домена закрепляется ТЕСТОМ, а не импортом, когда перечни описывают разные экраны"

key-files:
  created:
    - app/templates/history/includes/filter_chips.html
    - tests/test_pages/test_history.py
  modified:
    - app/pages/history.py
    - app/templates/history/list.html
    - app/static/css/app.css

key-decisions:
  - "Шаблон чипсов положен в history/includes/, а не в components/: инвентаризация библиотеки фиксирует 13 файлов, и файл, положенный туда, сдвинул бы под своё появление ровно ту проверку, которая ловит молчаливое пополнение библиотеки"
  - "Мусорное значение оси отсекается СЕРВЕРОМ (_clean_choice), а не применяется буквально: применённый мусор давал бы пустой список без единого активного чипса"
  - "Линейка счётчика собрана существующим примитивом .count-rule — новых CSS-правил линейки не заведено вопреки букве плана"
  - "Значения канала связаны с осью расписаний тестом, а не импортом: ось расписаний описывает другой экран"
  - "Перечни значений уходят только в шаблон списка, не в паршал: паршал чипсов не рисует"

patterns-established:
  - "Чипс опознаётся в тестах по АТРИБУТУ (data-chipset/data-chip), а не по подписи: тест на подписи краснеет на копирайтинге, а не на потерянном фильтре"
  - "Пустое состояние фильтров и пустое состояние раздела закрепляются ПАРОЙ тестов: одиночный зеленеет на реализации, заменившей текст везде"

requirements-completed: []

coverage:
  - id: D1
    description: "Статус, канал и период выбираются чипсами одним действием без кнопки «Применить» (D-29), и выбор меняет выборку"
    requirement: "HIST-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_status_chip_filters_the_list"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_messenger_chip_filters_the_list"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_account_disconnected_chip_filters_the_list"
        status: pass
    human_judgment: false
  - id: D2
    description: "Чипсы — обычные ссылки: смена фильтра работает при выключенном JavaScript"
    requirement: "HIST-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_chips_are_links_and_need_no_javascript"
        status: pass
    human_judgment: false
  - id: D3
    description: "Чипсы статуса покрывают все три значения журнала, включая отключённый аккаунт; чипсы канала — все три канала проекта"
    requirement: "HIST-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_status_chips_cover_all_three_journal_statuses"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_messenger_chips_cover_all_three_channels"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history.py#test_messenger_chips_match_the_channel_axis_of_the_project"
        status: pass
    human_judgment: false
  - id: D4
    description: "Фильтр по аккаунту сохранён выпадающим списком рядом с чипсами и переживает смену чипса (D-29)"
    requirement: "HIST-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_account_dropdown_survives_a_chip_switch"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_account_filter_cannot_reach_another_users_records"
        status: pass
    human_judgment: false
  - id: D5
    description: "Варианты периода — сегодня, 7 дней, 30 дней, всё время; произвольного диапазона нет, «сегодня» отсчитывается от локальной полуночи пользователя (D-30)"
    requirement: "HIST-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_period_chips_cover_four_options"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_period_today_cuts_at_user_local_midnight"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_history.py#test_period_chips_cover_every_period_the_module_knows"
        status: pass
    human_judgment: false
  - id: D6
    description: "Переход по чипсу сохраняет остальные активные фильтры, а вариант «все» снимает только свою ось; активный чипс размечен и он в группе один"
    requirement: "HIST-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_chip_link_keeps_the_other_filters"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_all_chip_drops_only_its_own_filter"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_active_chip_is_marked_and_the_others_are_not"
        status: pass
    human_judgment: false
  - id: D7
    description: "Неизвестное значение оси в адресе не роняет страницу и не применяется (T-04-23); полоса чипсов не остаётся без активного варианта"
    requirement: "HIST-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_unknown_filter_values_do_not_break_the_page"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_unknown_filter_value_leaves_the_all_chip_active"
        status: pass
    human_judgment: false
  - id: D8
    description: "Запись со старым пустым значением канала не совпадает ни с одним чипсом конкретного канала и остаётся видимой при варианте «все»"
    requirement: "HIST-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_record_without_messenger_survives_the_all_chip"
        status: pass
    human_judgment: false
  - id: D9
    description: "Над списком показывается точное число найденного отдельным запросом с теми же фильтрами, и оно совпадает с числом записей полной выборки тех же фильтров (D-31)"
    requirement: "HIST-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_counter_matches_the_full_selection_of_the_same_filters"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_counter_counts_beyond_the_first_page"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_counter_follows_the_filters"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_counter_shows_the_number_of_found_records"
        status: pass
    human_judgment: false
  - id: D10
    description: "Счётчик не считает чужих записей: условие владения стоит в базовом запросе счётчика (T-04-22)"
    requirement: "HIST-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_counter_ignores_other_users"
        status: pass
      - kind: unit
        ref: "tests/test_application/test_send_analytics.py#test_history_count_ignores_other_users"
        status: pass
    human_judgment: false
  - id: D11
    description: "Пустой результат фильтров даёт отдельный текст со сбросом, отличный от текста «отправок вообще нет» (D-41)"
    requirement: "HIST-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_empty_filter_result_differs_from_the_empty_journal"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_history.py#test_empty_journal_keeps_the_old_text"
        status: pass
    human_judgment: false
  - id: D12
    description: "Активный набор фильтров переживает бесконечную прокрутку — разметка сентинела на странице и в паршале идентична"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_history.py#test_infinite_scroll_sentinel_is_identical_in_page_and_partial"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_keeps_filters"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_history_filters_survive_pagination"
        status: pass
    human_judgment: false
  - id: D13
    description: "Новый файл шаблона положен вне каталога компонентов — инвентаризация библиотеки компонентов не сдвинута"
    verification:
      - kind: unit
        ref: "tests/test_pages/test_history.py#test_filter_chips_template_lives_outside_the_component_library"
        status: pass
      - kind: unit
        ref: "tests/test_pages/test_responsive_markup.py#test_template_inventory"
        status: pass
    human_judgment: false
  - id: D14
    description: "Раздел истории пригоден к использованию на мобильных ширинах: полоса чипсов переносится, а не прокручивается горизонтально"
    verification: []
    human_judgment: true
    rationale: "Браузерных/e2e-тестов в проекте нет, медиазапросы автотестами не исполняются. Тот же пункт чекпоинта плана 04-10, что и у плиток из 04-01, двух блоков из 04-04 и ленты из 04-05"

duration: 62 min
completed: 2026-08-14
status: complete
---

# Phase 4 Plan 06: Чипсы фильтров истории и точное число найденного Summary

**Фильтры истории переехали с четырёх выпадающих списков и кнопки «Применить» на три полосы чипсов-ссылок, работающих одним кликом и при выключенном JavaScript; над списком встало точное число найденного тем же набором фильтров, а пустой результат фильтров получил собственный текст со сбросом.**

## Performance

- **Duration:** 62 min
- **Started:** 2026-08-14T09:32:00Z
- **Completed:** 2026-08-14T10:34:00Z
- **Tasks:** 2
- **Files modified:** 5 (2 создано, 3 изменено)

## Accomplishments

- **Фильтр стал одним действием, а не двумя.** Прежний экран требовал выбрать значение в списке и нажать «Применить»; чипс — обычная ссылка, поэтому переход происходит одним кликом и не зависит от JavaScript. Существующие потребители примитива `.chip` с настоящими полями ввода (редактор расписаний) остались нетронутыми: там форма и нужна.
- **Закрыт дефект «отфильтровать отключённый аккаунт нечем».** Прежний список статусов знал два значения из трёх и терял `account_disconnected` — единственный статус, по которому видно, что отправка не ушла из-за отвалившегося аккаунта, а не из-за мессенджера. Набор чипсов СОБИРАЕТСЯ из констант модуля аналитики, поэтому четвёртый статус, заведённый там, здесь упадёт по `KeyError`, а не потеряется молча.
- **Каналов стало три.** Прежний список знал Telegram и WhatsApp; MAX, существующий в проекте с Фазы 2, отфильтровать было невозможно. Совпадение набора с осью канала сводного списка расписаний закреплено тестом.
- **Мусор в адресе больше не выбирает ничего.** Значение вне допустимого набора отсекается сервером до применения фильтров: страница отдаёт 200, отсечка не применяется, и активным остаётся вариант «все». Прежнее поведение (буквально применить `status=не-такой-статус`) давало пустой список без единого отмеченного чипса — экран, по которому не прочитать, что произошло.
- **Число над списком — обещание, а не украшение.** Считается отдельным запросом тем же набором фильтров и сравнивается в тесте с длиной ПОЛНОЙ выборки, построенной независимо от `history_count`. Именно это сравнение делает проверяемым обещание плана 04-08 «выгружен именно отфильтрованный результат».
- **Два пустых состояния разведены (D-41).** «Ничего не найдено. Измените фильтры или период» со сбросом — при активных фильтрах; прежнее «Здесь появятся отправки по вашим расписаниям» — при пустом журнале. Свойство закреплено ПАРОЙ тестов: одиночный зеленел бы на реализации, заменившей старый текст новым везде.
- **У раздела появился собственный файл тестов** — 30 тестов. Существующие тесты истории в разметочном файле и в файле сохранности HTMX не перенесены и не продублированы: два теста одного свойства расходятся при первой правке, и красным оказывается тот, который правили последним.

## Task Commits

Обе задачи исполнены как TDD-пары «красный набор → реализация»:

1. **Task 1 RED — чипсы и их устойчивость к мусору** — `9343aa2` (test)
2. **Task 1 GREEN — чипсы-ссылки для статуса, канала и периода** — `dc10907` (feat)
3. **Task 2 RED — счётчик найденного и пустой результат фильтров** — `8d4b09a` (test)
4. **Task 2 GREEN — линейка счётчика и два пустых состояния** — `4141f30` (feat)

## Files Created/Modified

- `app/templates/history/includes/filter_chips.html` — макрос `filter_chips(options, active, base_params, param_name, base_path)`: группа чипсов-ссылок, адрес собирается из действующих фильтров с подменой одного значения
- `tests/test_pages/test_history.py` — 30 тестов раздела: наборы значений трёх осей, признак активности, сохранение соседних фильтров, устойчивость к мусору, изоляция по владельцу, счётчик и два пустых состояния
- `app/pages/history.py` — перечни `STATUS_CHIPS`/`MESSENGER_CHIPS`/`PERIOD_CHIPS`, отсечка `_clean_choice` в обоих обработчиках, вызов `history_count` в списке
- `app/templates/history/list.html` — полоса чипсов с кнопкой сброса, выпадающий список аккаунта со скрытыми полями соседних осей, линейка счётчика, разведённые пустые состояния
- `app/static/css/app.css` — модификатор чипса-ссылки поверх примитива `.chip` и полоса групп `.chip-bar`

## Decisions Made

- **Шаблон лежит в `history/includes/`, а не в `components/`.** Инвентаризация библиотеки компонентов фиксирует число файлов ровно 13, и тринадцатый файл, положенный туда, потребовал бы правки константы в том же плане — то есть сдвинул бы под своё появление ровно ту проверку, которая ловит молчаливое пополнение библиотеки. Макрос обслуживает один раздел; второй потребитель (история пользователя в админке, Фаза 6) станет поводом для переезда.
- **Форма выбрана ссылками, а не полями ввода.** Поле ввода внутри формы даёт «выбрать плюс применить» — два действия, из которых второе при выключенном JavaScript обязательно. Ссылка даёт тот же результат одним переходом. Примитив `.chip` при этом не переписан: у него оба состояния выражены через `:has(.chip__input:…)`, и для ссылки добавлены три правила, берущие состояние с самого элемента.
- **Три правила CSS существуют ради перебивания базового `a`.** Селектор `a:hover` (0-1-1) сильнее `.chip--on` (0-1-0): без них наведение на ВЫБРАННЫЙ чипс перекрашивало бы его в цвет ссылки — то есть выбранный чипс переставал бы выглядеть выбранным ровно в тот момент, когда на него смотрят. Собственных цветов не заведено, значения те же, что у примитива.
- **Скрытые поля соседних осей внутри формы аккаунта обязательны.** Форма отправляет только свои поля, поэтому без них применение выбора аккаунта сбрасывало бы три чипсовые оси разом — молча, с 200 и исправным на вид экраном.
- **Мусорное значение оси отсекается СЕРВЕРОМ.** Разметка точкой принуждения не является; допустимые множества строятся из тех же перечней, из которых рисуются чипсы, поэтому нарисованное и принимаемое разойтись не могут в принципе. Период отсекается той же дорогой, хотя модуль аналитики и сам не применяет отсечку по неизвестному периоду: без этого мусорный период доехал бы до адреса чипса и до сентинеля прокрутки как действующий фильтр.
- **Значения канала связаны с осью расписаний тестом, а не импортом.** Ось расписаний описывает ДРУГОЙ экран, и импорт объявил бы одну ось определением другой. Разойтись им при этом нельзя: канал у проекта один, и чипс, отбирающий по значению, которого не пишет ни один аккаунт, не отберёт ничего никогда.
- **Старая запись с пустым каналом видна только при варианте «все» и из «всех» не скрывается.** Это настоящая отправка, случившаяся до того, как канал стали писать в журнал. Спрятанная, она исчезла бы из истории навсегда и не сошлась бы ни с одним счётчиком. Решение выписано в докстринге макроса и закреплено тестом.
- **Линейка счётчика при нуле записей не рендерится.** «0 записей» — не сообщение; сообщение несёт пустое состояние. Тот же приём, что у линейки экрана групп аккаунта.
- **Перечни значений уходят только в шаблон списка.** Паршал прокрутки чипсов не рисует и получает лишь активные значения, которые едут в адресе сентинеля.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Форма аккаунта сбрасывала бы чипсовые оси**

- **Found during:** Task 1 (перевёрстка секции фильтров)
- **Issue:** План оставляет выпадающий список аккаунта внутри существующей обёртки фильтров с кнопкой «Применить», а три оси выносит в чипсы-ссылки ВНЕ формы. HTML-форма отправляет только свои поля, поэтому нажатие «Применить» отправило бы один `account_id` и сбросило бы статус, канал и период разом. Отказ молчалив: 200, исправный на вид экран и незаметно расширившаяся выдача — ровно тот класс потери фильтра, от которого раздел уже защищён в сентинеле прокрутки.
- **Fix:** В форму добавлены три скрытых поля с текущими значениями осей; причина выписана комментарием рядом. Свойство закреплено тестом `test_account_dropdown_survives_a_chip_switch`, который проверяет и обратное направление — что выбор аккаунта доезжает до адреса чипса.
- **Files modified:** app/templates/history/list.html
- **Verification:** `test_account_dropdown_survives_a_chip_switch` — passed
- **Committed in:** dc10907

**2. [Rule 2 - Missing Critical] Мусорное значение оси оставляло бы полосу чипсов без активного варианта**

- **Found during:** Task 1 (написание теста устойчивости к мусору)
- **Issue:** Блок `<behavior>` требует «ответ 200, фильтр не применён» для неизвестного значения ЛЮБОЙ оси, но буквальная реализация применяет `status=не-такой-статус` как условие `SendLog.status == 'не-такой-статус'`. Страница отдаёт 200 и пустой список, в котором ни один чипс не отмечен активным: по такому экрану не прочитать, применён фильтр или сломался раздел. Модуль аналитики сам защищает только период.
- **Fix:** Заведена `_clean_choice` по образцу оси канала сводного списка расписаний: значение вне допустимого набора становится «фильтр не применён». Отсечка стоит в ОБОИХ обработчиках раздела, иначе мусор доезжал бы до сентинеля прокрутки как действующий фильтр. Допустимые множества строятся из тех же перечней, из которых рисуются чипсы.
- **Files modified:** app/pages/history.py
- **Verification:** `test_unknown_filter_values_do_not_break_the_page`, `test_unknown_filter_value_leaves_the_all_chip_active` — passed
- **Committed in:** dc10907

### Отступления от буквы плана (не автопочинка)

**3. Правил CSS для линейки счётчика не добавлено — линейка собрана существующим примитивом.** План предписывает «добавить правила линейки счётчика: mono-подписи, разделительная линия на всю оставшуюся ширину, перенос на узких ширинах». Ровно этот примитив в проекте уже есть — `.count-rule` / `.count-rule__line`, заведённый линейкой экрана групп аккаунта, и он делает буквально перечисленное: заполняющая черта забирает свободное место, а на узкой ширине правая часть переносится под число. Второй набор правил того же смысла разошёлся бы с первым при первой правке. Место под ссылку выгрузки (план 04-08) при этом готово: черта уже отдаёт ей ширину.

**4. Наборы значений прокинуты только в шаблон списка, а не «в шаблон списка и паршала».** Паршал бесконечной прокрутки чипсов не рисует — он подменяет порцию записей и сентинел. Перечни, положенные в его контекст, были бы неиспользуемыми ключами, а активные значения фильтров он и так получает: они едут в адресе сентинеля. Требование плана «прокинуть активные значения фильтров» в паршале выполнялось и до этого плана.

**5. У макроса пятый параметр `base_path` со значением по умолчанию.** Сигнатура плана — `filter_chips(options, active, base_params, param_name)`; она сохранена целиком, добавленный параметр необязателен. Без него путь раздела пришлось бы вписать в макрос константой, и история пользователя в админке (Фаза 6) не смогла бы переиспользовать макрос, не переписав его.

---

**Total deviations:** 2 auto-fixed (обе — Rule 2, недостающая критичная функциональность) + 3 задокументированных отступления от буквы плана
**Impact on plan:** Обе автопочинки обязательны для корректности: без первой раздел терял бы три фильтра по нажатию кнопки, без второй мусор в адресе давал бы неотличимый от поломки экран. Объём не расширен: ни одного символа сверх перечисленных в «Artifacts this phase produces» не заведено, новых CSS-классов заведён один (`.chip-bar` с модификатором сброса).

## Issues Encountered

None — откатов не было; красных прогонов, кроме двух запланированных фаз RED, не случилось.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None — заглушек не заведено. Чипсы читают настоящие перечни значений журнала, счётчик считает настоящим запросом, пустые состояния наступают только при действительно пустом наборе. Правая часть линейки счётчика пуста НАМЕРЕННО и заглушкой не является: пустая ссылка не рендерится, разметки-обманки под неё не заведено, место готовит раскладка (план 04-08 ставит туда ссылку выгрузки).

## Next Phase Readiness

- **Готово для 04-08 (выгрузка):** `history_total` считается тем же набором фильтров, что и список, и это закреплено тестом прямого сравнения с полной выборкой. Потолок экспорта может опираться на это число, не заводя своего счёта. Место под ссылку выгрузки в линейке готово раскладкой.
- **Готово для Фазы 6 (история пользователя в админке):** макрос принимает `base_path` параметром, поэтому админка зовёт его со своим путём, не заводя копии. Перечни значений и `_clean_choice` живут в `app/pages/history.py` и импортируются оттуда — админка уже импортирует из этого модуля `_parse_account_id`.
- **Открыто для 04-10 (чекпоинт):** адаптивность полосы чипсов на узких ширинах автотестами не подтверждается — медиазапросы в тестах не исполняются. Пункт уходит в тот же чекпоинт, что и плитки из 04-01, два блока из 04-04 и лента из 04-05.
- **HIST-01 в REQUIREMENTS.md не отмечен НАМЕРЕННО:** тот же идентификатор объявляют планы 04-08 и 04-10, у которых сводок ещё нет. Отметка сейчас показала бы требование закрытым, пока последний объявивший его план ещё идёт.
- **Не тронуто намеренно:** разметка сентинела бесконечной прокрутки в обоих файлах; `app/pages/admin.py` и его шаблоны истории; JSON-API `app/routes/history.py` (выравнивается планом 04-10). Граф `graphify-out/` в этом worktree отсутствует, поэтому `graphify update .` не выполнялся — граф обновляется в основном рабочем дереве после слияния.

## Self-Check: PASSED

- Оба созданных файла присутствуют на диске: `app/templates/history/includes/filter_chips.html`, `tests/test_pages/test_history.py`.
- Все четыре коммита задач присутствуют в истории ветки: `9343aa2`, `dc10907`, `8d4b09a`, `4141f30`.
- Критерии приёмки перепроверены командами: `macro filter_chips` в новом шаблоне — есть; `app/templates/components/` содержит ровно 13 файлов; `filter_chips(` в `history/list.html` — ровно 3 вызова; `history_count(` в `app/pages/history.py` — есть; `name="account_id"` в списке — есть.
- Прогоны: `tests/test_pages/test_history.py` — 30 passed; `tests/test_pages/test_htmx_preserved.py::test_infinite_scroll_keeps_filters` — 3 passed; `tests/test_pages/ tests/test_templates/` — **641 passed**; вся суита `uv run pytest tests/ -q` — **1248 passed** (было 1218: +30 новых, ни одного снятого).
- Гейты TDD соблюдены на обеих задачах: коммит `test(...)` предшествует коммиту `feat(...)`, оба присутствуют дважды. Обе фазы RED состоялись по-настоящему — первая падала на ImportError отсутствующих перечней, вторая давала 7 падений из 30.
- Невакуумность ключевых утверждений: тесты двух пустых состояний написаны ПАРОЙ (одиночный зеленел бы на реализации, заменившей текст везде); тест счётчика посеян 35 записями при странице в 30, поэтому реализация `logs|length` на нём краснеет; тест сравнения с полной выборкой строит выборку независимо от `history_count` и утверждает непустоту ожидаемого набора.
- Новых поверхностей вне `<threat_model>` не появилось: ни одного маршрута не заведено, оба обработчика раздела остались под гардом входа, условие владения стоит до применения фильтров, значения фильтров печатаются в адреса обычным `urlencode`, а подписи — обычным экранированным выводом Jinja.

---
*Phase: 04-dashbord-i-istoriya*
*Completed: 2026-08-14*
