---
phase: 01-interfeysnyy-fundament
plan: 04
subsystem: ui
tags: [jinja2, macros, design-system, alpinejs, infinite-scroll, filters, htmx]

# Dependency graph
requires: ["01-01", "01-02", "01-03"]
provides:
  - "components/filters.html::filters(id, action, method, open_on_desktop, label) — сворачиваемый блок фильтров с блочным вызовом"
  - "app.css: .filters / .filters--collapsed / .filters--open / .filters__toggle / .filters__form"
  - "schedules/includes/schedule_row.html::schedule_row(item, user=None, cols=SCHEDULE_COLS)"
  - "groups/includes/group_row.html::group_row(group, stats=None, user=None, cols=GROUP_COLS)"
  - "Паттерн «тумблер вместо кнопки»: макрос toggle в прежней POST-форме, обработчик change на форме"
  - "tests/test_pages/test_responsive_markup.py — разделы ads / schedules / groups в общей параметризации"
affects: [05-istoriya, 06-admin-vorkery, 07-tarify, 08-svodnaya-proverka]

actuals:
  tokens: 22500
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Событие change всплывает от чекбокса к форме — обработчик вешается на форму, макрос toggle остаётся без атрибутов событий"
    - "Свёрнутость блока выражается классами и медиазапросом, а не привязкой класса к состоянию Alpine — тогда мигания при загрузке нет по построению"
    - "Скрытие без utility-классов: атрибут hidden там, где у элемента нет собственного правила display; инлайн-display там, где есть"
    - "SECTION_COLS живёт рядом с макросом строки и импортируется страницей для шапки колонок"

key-files:
  created:
    - app/templates/components/filters.html
    - app/templates/schedules/includes/schedule_row.html
    - app/templates/groups/includes/group_row.html
  modified:
    - app/static/css/app.css
    - app/templates/schedules/list.html
    - app/templates/schedules/partial_cards.html
    - app/templates/schedules/form.html
    - app/templates/groups/list.html
    - app/templates/groups/partial_cards.html
    - tests/test_pages/test_responsive_markup.py
  deleted: []

key-decisions:
  - "Пауза/возобновление переведены на toggle, а не на кнопку с иконкой: маршрут называется /toggle, и это единственное прочтение плана, при котором обе его фразы не противоречат друг другу"
  - "Тумблер отправляет форму обработчиком change на самой форме — макрос toggle не принимает атрибутов событий, а дублировать его разметку значило бы обойти библиотеку"
  - "Свёрнутость фильтров выражена классами, а не x-cloak: правильное состояние приходит с сервера, поэтому мигать нечему"
  - "Иконка мессенджера получает размер классом .avatar — тот же приём, что у миниатюры объявления в Плане 03; app.css закрыт для новых классов"
  - "Ветка «неизвестный мессенджер» в messenger_icon не вызывается: она несёт utility-классы, а у отвязанного расписания типа нет"
  - "Модальное подтверждение удаления в этот план не вводится: Плана 04 его не требует ни действием, ни критерием приёмки"

patterns-established:
  - "filters(id, action=None, method='get', open_on_desktop=true, label='Фильтры') вызывается блоком {% call %}"
  - "Массовое действие над списком: обёртка с x-on:change вокруг вызова toggle вместо ручной разметки чекбокса"

requirements-completed: [UI-04, UI-05, UI-06]

coverage:
  - id: D1
    description: "Страницы расписаний и групп содержат адаптивные примитивы data-row"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_list_page_has_responsive_primitives"
        status: pass
    human_judgment: false
  - id: D2
    description: "Utility-классы удалённого фреймворка отсутствуют в выдаче обоих разделов"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_list_page_no_utility_classes"
        status: pass
      - kind: command
        ref: "grep -rc 'bg-white|text-gray|rounded-lg|border-gray|hidden sm:|lg:' app/templates/groups/ app/templates/schedules/ → 0 во всех файлах"
        status: pass
    human_judgment: false
  - id: D3
    description: "Строки расписаний и групп отрисовывают реальные данные, а не пустоту после перевода include в макрос"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_card_renders_data"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_card_renders_data"
        status: pass
    human_judgment: false
  - id: D4
    description: "Бесконечная прокрутка обоих разделов подгружает вторую страницу выдачи"
    requirement: "UI-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_chain"
        status: pass
    human_judgment: false
  - id: D5
    description: "Фильтры групп доезжают до второй страницы выдачи и не сбрасываются"
    requirement: "UI-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_filters_survive_pagination"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_keeps_filters"
        status: pass
    human_judgment: false
  - id: D6
    description: "Тумблеры расписаний и групп меняют состояние через прежние маршруты и не трогают чужие записи"
    requirement: "UI-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_schedules_toggle_route_unchanged"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_toggle_route_unchanged"
        status: pass
    human_judgment: false
  - id: D7
    description: "Блок фильтров собран из общего макроса и приходит со свёрнутым состоянием в разметке"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_groups_filters_block_collapsible"
        status: pass
    human_judgment: false
  - id: D8
    description: "Форма расписания сохранила все атрибуты name, метод и маршрут отправки"
    requirement: "UI-04"
    verification:
      - kind: command
        ref: "grep -o 'name=\"[a-z_]*\"' app/templates/schedules/form.html | sort -u — набор до и после совпал"
        status: pass
      - kind: integration
        ref: "tests/test_routes/test_schedules.py + tests/test_pages/test_schedules_detached_account.py"
        status: pass
    human_judgment: false
  - id: D9
    description: "Выбранная таймзона подставляется в форму редактирования, порядок атрибутов элемента выбора не сломан"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_routes/test_schedules_profile_timezone.py#test_new_schedule_form_uses_user_timezone_by_default"
        status: pass
    human_judgment: false
  - id: D10
    description: "Сворачивание фильтров на мобильной ширине и отсутствие мигания при загрузке страницы"
    verification: []
    human_judgment: true
    rationale: "Медиазапрос и момент инициализации Alpine живут только в браузере; автотест доказывает, что свёрнутое состояние приходит с сервера классами, но не отсутствие кадра мигания"
  - id: D11
    description: "Работа тумблера в браузере: клик по дорожке отправляет форму и состояние переключается"
    verification: []
    human_judgment: true
    rationale: "Всплытие события change до формы и вызов form.submit() проверяются только в браузере; автотест доказывает маршрут, метод и серверный эффект"
  - id: D12
    description: "Перестроение строк расписаний и групп в карточное представление на ширине меньше 860px"
    verification: []
    human_judgment: true
    rationale: "Медиазапросы Плана 01; вынесено в end-of-phase human-check вместе с открытыми пунктами Планов 01-03"

# Metrics
duration: 25min
completed: 2026-08-09
status: complete
---

# Phase 01 Plan 04: Разделы «Расписания» и «Группы» — Summary

**Пять шаблонов двух самых интерактивных разделов собраны заново на дизайн-системе, последний сценарий Alpine вынесен в макрос `filters`, а сворачивание фильтров перестало зависеть от инициализации скрипта: правильное состояние теперь приходит с сервера классами.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-08-09T11:25Z
- **Completed:** 2026-08-09T11:50Z
- **Tasks:** 3 (Задачи 1 и 3 — TDD с отдельным RED-коммитом)
- **Files:** 10 изменённых файлов, +647 / −435 строк
- **Тесты:** 456 → 466 (+10)

## Task Commits

1. **Задача 1 (RED): примитивы и данные раздела расписаний** — `7242524` (test)
2. **Задача 1 (GREEN): раздел «Расписания» на дизайн-системе** — `cbb4c8b` (feat)
3. **Задача 2: форма расписания на макросах полей** — `214c33f` (feat)
4. **Задача 3 (RED): примитивы, фильтры и данные раздела групп** — `8db9215` (test)
5. **Задача 3 (GREEN): раздел «Группы» и макрос фильтров** — `2518669` (feat)

## Сигнатура макроса `filters` — Планы 05 и 08 вызывают её дословно

```jinja
{% from "components/filters.html" import filters %}

{% call filters('groups-filters', action='/groups') %}
  {{ select_field(name="messenger_type", label='Мессенджер', options=[...], selected=filter_messenger_type) }}
  {{ field(name="search", label='Поиск', value=filter_search or '') }}
  {{ button('Применить', variant='primary') }}
  {{ link_button('Сбросить', '/groups', variant='ghost') }}
{% endcall %}
```

`filters(id, action=None, method='get', open_on_desktop=true, label='Фильтры')`

- Содержимое приходит **блочным вызовом**, а не параметром: готовая разметка макросам библиотеки не передаётся.
- Макрос сам рендерит `<form>`; поля внутри — обычные вызовы `field` / `select_field`, значения вычисляются в вызывающем шаблоне (внутри макроса `request` недоступен).
- `id` даёт якорь `aria-controls`: форма получает `id="<id>-form"`.
- `open_on_desktop=false` схлопывает блок на **всех** ширинах — для разделов, где фильтры вторичны.

**Почему здесь нет `x-cloak`.** План просил проверить, что правило скрытия элементов с отложенной инициализацией применяется к новому макросу. Оказалось, что оно ему не нужно и вредно. Сегодня мигание возникало потому, что видимость задавалась привязкой класса к состоянию Alpine (`:class="filterOpen ? 'block' : 'hidden sm:block'"`): до инициализации класса нет — блок развёрнут даже на мобильной ширине. Новый макрос выражает свёрнутость **самой разметкой**: `.filters__form` скрыт медиазапросом `max-width: 860px`, а Alpine лишь добавляет `.filters--open` по нажатию. Правильное состояние приходит с сервера, мигать нечему. `x-cloak` на этот блок сделал бы хуже: он спрятал бы фильтры целиком до загрузки Alpine, то есть добавил бы мигание на десктопе, где его сейчас нет. Правило `[x-cloak]` остаётся в `app.css` и продолжает обслуживать модалку Плана 02.

## Добавленные классы `app.css`

Единственное дополнение файла в этом плане, прямо санкционированное `<flagged_assumptions>`. Цвета не вводятся вовсе: кнопка сворачивания — существующие `.btn .btn--ghost`, поля — существующий `.field`.

`.filters`, `.filters__toggle`, `.filters__form`, `.filters--collapsed`, `.filters--open`

Плюс два правила раскладки на существующих классах-потомках: `.filters__form .field { flex: 1 1 168px }` и `.filters__form .btn { flex: none }`.

## Раскладка колонок разделов

```
SCHEDULE_COLS   = 'minmax(180px,2.2fr) 128px minmax(110px,1fr) 104px 152px 96px 210px'
SCHEDULE_COLUMNS = ['Объявление', 'Группы', 'Дни', 'Время', 'Следующий запуск', 'Статус', '']

GROUP_COLS      = '28px minmax(180px,2.4fr) minmax(110px,1.2fr) 104px 96px 128px 96px 168px'
GROUP_COLUMNS   = ['', 'Группа', 'Идентификатор', 'Расписаний', 'Успех', 'Отправлено', 'Статус', '']
```

Объявлены рядом с макросом строки и импортируются страницей для шапки — разъехаться шапке и строкам не на чем.

## Тумблер вместо кнопки: как он отправляет прежний запрос

```jinja
<form method="post" action="/schedules/{{ s.id }}/toggle" x-data x-on:change="$el.submit()">
  {{ toggle(name='is_active', checked=s.is_active, id='schedule-toggle-' ~ s.id) }}
</form>
```

Событие `change` всплывает от чекбокса к форме, поэтому обработчик висит **на форме**, а макрос `toggle` вызывается как есть — ему не нужны атрибуты событий, которых в его сигнатуре нет. Альтернатива (продублировать разметку тумблера ради `onchange`) обошла бы библиотеку компонентов.

Маршрут, метод и серверная проверка владельца не тронуты: обработчик тела запроса не читает, он просто инвертирует флаг. Тем же приёмом сделано «Выбрать все» в массовых действиях групп — обёртка `<span x-data x-on:change="selectAllGroups()">` вокруг вызова `toggle`.

## Deviations from Plan

### Расхождения с буквой плана (не автофиксы)

**1. Пауза/возобновление — тумблер, а не кнопка с иконкой.** Текст плана содержит две несовместимые фразы: «Кнопки паузы, запуска, редактирования и удаления — через `button` с иконками» и «Тумблеры включения и паузы переводятся на макрос `toggle`». Выбрано прочтение, при котором обе выполнимы: состояние «активно/пауза» — это и есть тумблер (маршрут так и называется, `/toggle`), а `button` достаётся редактированию и удалению. При обратном прочтении пришлось бы либо рисовать две кнопки под один маршрут, либо ставить чекбокс, который без обработчика ничего не отправляет, — то самое молчаливое ломание, от которого предостерегает план.

**2. `icon_pause` / `icon_play` не переиспользуются.** Макрос `button` принимает **имя** иконки, а не разметку, и в его наборе (`plus` · `trash` · `check` · `arrow-right` · `pencil` · `refresh`) пауза и запуск отсутствуют. Расширять `button.html` этот план не вправе — файл принадлежит Плану 02 и в `files_modified` не заявлен. Редактирование получило `icon='pencil'`, удаление — `icon='trash'`, состояние — тумблер, у которого иконки нет по конструкции.

**3. Появились два файла, которых нет в `files_modified`:** `schedules/includes/schedule_row.html` и `groups/includes/group_row.html`. `list.html` и `partial_cards.html` обязаны нести идентичную строку; при дублировании разметки в двух файлах расхождение проявится только на второй странице выдачи. Это ровно тот паттерн, который План 03 зафиксировал как эталон (`ads/includes/ad_card.html` + `SECTION_COLS`). Критерии приёмки, гребущие по `list.html` и `partial_cards.html`, выполняются; вся директория каждого раздела чиста от utility-классов.

**4. Атрибут `data-type` у вариантов аккаунта в форме расписания удалён.** `select_field` не умеет атрибуты на отдельных вариантах. Перед удалением проверено грепом по `app/` и `tests/`: единственное вхождение — сама эта строка, ни один скрипт и ни один тест его не читают (фильтрация групп идёт по `value` элемента выбора и `data-account-id` обёртки группы).

**5. Иконка мессенджера получает размер классом `.avatar`.** `messenger_icon(size=…)` кладёт значение в `class` svg, а классы размеров принадлежали удалённому фреймворку; собственного класса под иконку в `app.css` нет, и файл закрыт для дописывания. Использован тот же обходной путь, что План 03 применил к миниатюре объявления. Ограничение то же: круглая подложка `.avatar` обрезает неквадратный логотип по краям.

**6. Ветка «неизвестный мессенджер» в `messenger_icon` не вызывается.** Она — единственное место макроса, несущее `text-gray-500`, а у отвязанного расписания (issue #35) тип аккаунта отсутствует. В строке расписания вызов обёрнут условием `{% if item.messenger_type %}`; иначе `/schedules` с отвязанным расписанием отдавал бы utility-класс в разметке, а тест на его отсутствие зеленел бы ровно до первого такого расписания у живого пользователя.

**7. Модальное подтверждение удаления не вводится.** Ни действие Задач 1 и 3, ни критерии приёмки, ни `<artifacts_produced>` его не требуют — удаление осталось на прежней POST-форме с браузерным диалогом. Это осознанно отложено, а не забыто: см. «Next Phase Readiness».

**8. Скрытие блоков в форме расписания сделано двумя разными способами.** Подсказки под списком групп прячутся штатным атрибутом `hidden` (у `.field__hint` нет собственного правила `display`, поэтому правило UA работает), а контейнер групп — инлайн-стилем `display`, потому что `.field { display: flex }` перебил бы атрибут. Иначе понадобился бы новый класс в закрытом `app.css`.

**9. Крючки скриптов переведены с классов на имена полей.** `.day-checkbox` заменён на `input[name="days_of_week"]`, обёртки групп сохранили `.group-item` и `data-account-id`, строки — `.group-checkbox`. Выборка по `name` устойчивее: имя поля — контракт с обработчиком, и оно закреплено критерием приёмки, а класс — нет.

### Auto-fixed Issues

**1. [Rule 1 - Bug] Собственный новый тест падал на ленивой подгрузке SQLAlchemy**

- **Found during:** Задача 1 (RED)
- **Issue:** `test_schedules_toggle_route_unchanged` использовал `db_session.expire_all()` + `session.get(...)` для перечитывания состояния после POST. На уже загруженном объекте это приводит к ленивой подгрузке вне greenlet-контекста: `MissingGreenlet: greenlet_spawn has not been called`. Ошибка была в тесте, а не в приложении, но маскировала бы результат проверки.
- **Fix:** Перечитывание переведено на `await db_session.refresh(obj)`.
- **Files modified:** `tests/test_pages/test_responsive_markup.py`
- **Verification:** тест зелёный; проверка сохранена в прежнем объёме — своё расписание переключается, чужое остаётся нетронутым.
- **Committed in:** `7242524`

**2. [Rule 2 - Missing critical] Митигации T-04-03 не существовало ни в одном тесте**

- **Found during:** Задача 1
- **Issue:** Угроза T-04-03 (Elevation of Privilege на маршрутах тумблеров) помечена `mitigate` с обоснованием «маршруты, методы и серверные проверки владельца не меняются». Ни одного теста, доказывающего это поведенчески, в проекте не было — существующие проверки касались только разметки. Тот же пробел, что автофикс №2 Плана 03.
- **Fix:** Добавлены `test_schedules_toggle_route_unchanged` и `test_groups_toggle_route_unchanged`: свой объект переключается, чужой остаётся в прежнем состоянии.
- **Files modified:** `tests/test_pages/test_responsive_markup.py`
- **Verification:** оба теста зелёные; T-04-03 закрыт поведенчески, а не декларативно.
- **Committed in:** `7242524`, `8db9215`

---

**Total deviations:** 2 автофикса (1 баг в собственном тесте, 1 недостающая критичная проверка) + 9 задокументированных расхождений.
**Impact on plan:** Скоупкрипа нет. Расхождения — следствие внутреннего противоречия в тексте плана (№1, №2), фактов кодовой базы, которых план не знал (№4, №5, №6, №8), и эталона, зафиксированного Планом 03 (№3).

## Issues Encountered

- **Ветка неизвестного мессенджера — тихая утечка utility-классов.** `messenger_icon` выглядит безопасным для переиспользования, но его последняя ветка несёт `text-gray-500`. Ловится только на данных, которых в тесте по умолчанию нет: отвязанное расписание. Планам 05-08 стоит помнить, что «переиспользуется как есть» у этого макроса означает «кроме ветки else».
- **`app.css` пришлось трогать при закрытом файле.** Дополнение санкционировано планом и ограничено пятью классами блока фильтров; ни одного нового захардкоженного цвета, радиуса или кегля не добавлено.
- **Базовая суита в этом воркtree — 456, как и оставил План 03.** 25 задокументированных `.env`-зависимых падений не воспроизводятся: `.env` в воркtree нет. Ни один из четырёх перечисленных во вводных файлов не правился.

## Known Stubs

Нет. Оба раздела подключены к живым данным: список, статистика групп, состояние расписаний, следующий запуск, фильтры и массовые действия читают реальные поля и ходят по прежним маршрутам.

**Осознанно отложено (не заглушка):**

- **Удаление расписания и группы подтверждается браузерным диалогом**, а не модалкой Плана 02. План 04 модалку не требует. Разрешается Планом 08 либо отдельной задачей — работа механическая: заменить `onsubmit="return confirm(…)"` на кнопку-триггер `$dispatch('modal-open-…')` и вызов `modal(...)` рядом со строкой, как сделано в `ads/includes/ad_card.html`.
- **Массовые действия групп** используют браузерные `alert` и `confirm` в скрипте страницы — по той же причине и с тем же путём решения.
- **`schedules/form.html` будет переделан Фазой 2** (настройка расписаний переезжает в редактор объявления — SCH-04, ADS-07). Компромисс D-06, зафиксированный планом заранее. Здесь форма переведена на макросы целиком, потому что без Tailwind старая разметка осталась бы без стилей.
- **Список групп в форме расписания потерял прокрутку** — прежний `max-h-60 overflow-y-auto` был utility-классом, а нового класса в закрытый `app.css` вводить нельзя. При большом числе групп блок станет длинным. Косметика, попадающая в переделку Фазы 2.

## Threat Flags

Новых поверхностей за пределами `<threat_model>` не появилось. Статус митигаций:

| Threat ID | Статус | Чем закрыт |
|-----------|--------|-----------|
| T-04-01 | mitigated | Цикл проброса фильтров перенесён дословно вместе с `\|string\|urlencode`; сентинел идентичен в `list.html` и `partial_cards.html`. Закрыт `test_groups_filters_survive_pagination` (фильтр + смещение строго больше 30) и `test_infinite_scroll_keeps_filters` Плана 03 |
| T-04-02 | mitigated | Название группы приходит в макрос параметром и выводится обычным экранированным выводом; готовая разметка ни одному макросу не передаётся. Обход всех шаблонов делает `test_no_unsafe_escaping` Плана 02 |
| T-04-03 | mitigated | **Закрыт поведенчески** (автофикс №2): `test_schedules_toggle_route_unchanged` и `test_groups_toggle_route_unchanged` доказывают, что чужая запись не переключается. Маршруты, методы и обработчики не тронуты |
| T-04-04 | mitigated | Обработчики не менялись вовсе — правились только шаблоны; фильтрация выборки по владельцу на месте, полная суита зелёная |
| T-04-05 | accept | `offset` / `limit` остались как были (`ge=0`, `ge=1, le=100`) |
| T-04-SC | mitigated | Ни одной установки пакета: ни npm, ни pip. Новых зависимостей нет |

## User Setup Required

None — внешняя конфигурация не требуется.

## Next Phase Readiness

**Готово к Плану 05 (история):**

- `filters` вызывается блоком; сигнатура выше. `history/list.html` (строки 10 и 13) и `admin/user_history.html` — оставшиеся два потребителя, третий закрыт здесь.
- Форма сентинела с протаскиванием фильтров повторяется дословно из `groups/list.html`.
- `tests/test_pages/test_responsive_markup.py` готов принимать разделы: добавление — это строка в `SECTION_URLS`, значение в `MIGRATED_SECTIONS` и ветка в `_seed_section`.
- Приём «тумблер в прежней POST-форме» переиспользуем везде, где действие меняет булев флаг.
- `[data-hrow]` и `[data-area="meta"]` из медиазапросов Плана 01 ждут именно историю — этот план их не занимал.

**Открытые пункты, требующие человека (end-of-phase):**

- `/groups` на ширине меньше 860px: блок фильтров свёрнут, не мигает при загрузке, разворачивается по нажатию (D10).
- Применить фильтр и прокрутить список до подгрузки второй страницы: подгруженные группы соответствуют фильтру (доказана форма ответа, не поведение прокрутки).
- Клик по тумблеру расписания и группы в браузере: форма отправляется, состояние переключается (D11).
- Перестроение строк обоих разделов в карточное представление на ширине меньше 860px (D12).
- Создание и редактирование расписания через форму: все поля видны, выбор групп фильтруется по аккаунту, дни и время сохраняются, значения подставляются при повторном открытии.

## Self-Check: PASSED

- Все три созданных файла на диске: `app/templates/components/filters.html`, `app/templates/schedules/includes/schedule_row.html`, `app/templates/groups/includes/group_row.html`.
- Все 5 заявленных коммитов в истории: `7242524`, `cbb4c8b`, `214c33f`, `8db9215`, `2518669`.
- `grep -c '{% macro filters' app/templates/components/filters.html` → 1; `grep -c '^\.filters' app/static/css/app.css` → 8.
- `grep -c 'layout=cards'` в четырёх файлах списков обоих разделов → 0; `hx-trigger="revealed"` и `hx-swap="outerHTML"` присутствуют в обоих файлах каждого раздела.
- `grep -c 'filter_params'` в `groups/list.html` и `groups/partial_cards.html` → 1 в каждом.
- `grep -rc 'hx-target' app/templates/groups/ app/templates/schedules/` → 0 во всех файлах.
- `grep -rc 'bg-white|text-gray|rounded-lg|border-gray|hidden sm:|lg:'` по `app/templates/groups/` и `app/templates/schedules/` → 0 во всех файлах.
- Набор `grep -o 'name="[a-z_]*"' app/templates/schedules/form.html | sort -u` совпал до и после правки: `account_id`, `ad_id`, `days_of_week`, `group_ids`, `times_of_day`, `timezone`.
- Внешних ссылок (`http://` / `https://`) в новых и изменённых шаблонах → 0.
- Удалённых файлов в плане нет: `git diff --name-status` показывает только `M` и `A`.
- `uv run pytest tests/ -q` → **466 passed** (было 456).

---
*Phase: 01-interfeysnyy-fundament*
*Completed: 2026-08-09*
