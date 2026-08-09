---
phase: 01-interfeysnyy-fundament
plan: 05
subsystem: ui
tags: [jinja2, macros, design-system, css-grid, htmx, infinite-scroll, filters, responsive]

# Dependency graph
requires: ["01-01", "01-02", "01-03", "01-04"]
provides:
  - "history/includes/history_card.html::history_card(log, user=None, detail_base_path='/history') — бывший include, теперь макрос"
  - "dashboard/includes/recent_send_card.html::recent_send_card(log, user=None, cols=RECENT_COLS) — то же"
  - "Базовые правила примитива [data-hrow] в app.css: медиазапросы Плана 01 наконец имеют что перестраивать"
  - "Разметочная конвенция data-area=\"meta\" на блоке метаданных записи истории — опора исправленного медиазапроса 1080px"
  - "[data-longtext] / [data-longtext=\"mono\"] — текст, который обязан читаться целиком (ошибка отправки, текст объявления)"
  - "[data-hlist], [data-thumbs], [data-metrics], [data-metric-value], [data-stack], [data-form], [data-identity]* — примитивы разделов История/Дашборд/Профиль"
  - "tests/test_pages/test_responsive_markup.py — история в общей параметризации через CLEAN_SECTIONS"
affects: [06-admin-vorkery, 07-tarify, 08-svodnaya-proverka]

actuals:
  tokens: 25209
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Собственный адаптивный примитив раздела выражается атрибутом (data-hrow) и областями сетки (data-area), а не классом на каждый блок"
    - "Цветной акцент по статусу приходит атрибутом data-status, а не инлайн-стилем: селекторов по подстроке style в проекте больше нет"
    - "Раскладка «подпись → значение» на странице детали собрана из row_open/cell с параметром cols — новых классов под страницу не заводится"
    - "messenger_icon вызывается только для известных типов ('tg_user', 'wa', 'max'): ветка else несёт utility-класс"

key-files:
  created: []
  modified:
    - app/static/css/app.css
    - app/templates/history/list.html
    - app/templates/history/includes/history_card.html
    - app/templates/history/partial_cards.html
    - app/templates/history/detail.html
    - app/templates/dashboard.html
    - app/templates/dashboard/includes/recent_send_card.html
    - app/templates/profile.html
    - app/templates/admin/user_history.html
    - app/templates/admin/history_partial_cards.html
    - tests/test_pages/test_responsive_markup.py
  deleted: []

key-decisions:
  - "Базовые правила [data-hrow] пришлось ДОБАВИТЬ: в app.css существовали только медиазапросные, перестраивать было нечего"
  - "Статусный акцент записи истории — атрибут data-status, а не инлайн-стиль: файл не должен содержать ни одного селектора по подстроке style"
  - "Комментарий в app.css, цитировавший старый селектор по подстроке инлайн-стиля, переписан: критерий приёмки грепает файл целиком и не отличает комментарий от правила"
  - "Два admin-шаблона правятся вне files_modified: они включают history_card, и после перевода в макрос отрисовали бы ПУСТЫЕ записи при статусе 200"
  - "История НЕ входит в MIGRATED_SECTIONS: этот список проверяет примитив data-row, а у истории собственный data-hrow. Введён CLEAN_SECTIONS"
  - "Тесты трёх задач написаны одним RED-коммитом: они живут в одном файле и делят общий сидер _seed_send_log"

patterns-established:
  - "Раздел с собственным адаптивным примитивом описывает его БАЗОВЫЕ правила сам, а медиазапросы остаются за Планом 01"
  - "Текст из внешней системы, который пользователь обязан прочитать целиком, выводится через [data-longtext] — перенос вместо обрезки"

requirements-completed: [UI-04, UI-05, UI-06]

coverage:
  - id: D1
    description: "Записи истории отрисовываются примитивом data-hrow"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_history_uses_hrow_primitive"
        status: pass
    human_judgment: false
  - id: D2
    description: "Блок метаданных записи истории размечен атрибутом data-area=\"meta\" — исправленному медиазапросу 1080px есть на чём сработать"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_history_meta_marked_by_attribute"
        status: pass
      - kind: command
        ref: "grep -c 'style\\*=' app/static/css/app.css → 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "Запись истории отрисовывает реальные данные, а не пустоту после перевода include в макрос"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_history_card_renders_data"
        status: pass
    human_judgment: false
  - id: D4
    description: "Бесконечная прокрутка истории подгружает вторую страницу и сохраняет фильтры канала, статуса и периода"
    requirement: "UI-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_history_filters_survive_pagination"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_chain"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_keeps_filters"
        status: pass
    human_judgment: false
  - id: D5
    description: "Страница детали отправки показывает текст ошибки неуспешной отправки целиком, без усечения"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_history_detail_shows_error_text"
        status: pass
      - kind: command
        ref: "grep -c 'truncate' app/templates/history/detail.html → 0"
        status: pass
    human_judgment: false
  - id: D6
    description: "Страница детали успешной отправки открывается и не содержит utility-классов"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_history_detail_renders_for_successful_send"
        status: pass
    human_judgment: false
  - id: D7
    description: "Utility-классы удалённого фреймворка отсутствуют в выдаче истории, дашборда и профиля"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_list_page_no_utility_classes"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_dashboard_no_utility_classes"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_profile_no_utility_classes"
        status: pass
    human_judgment: false
  - id: D8
    description: "Дашборд отрисовывается в новом шелле и его карточка недавней отправки показывает реальные данные"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_dashboard_no_utility_classes"
        status: pass
    human_judgment: false
  - id: D9
    description: "Форма профиля сохраняет метод, маршрут, все атрибуты name и выбор таймзоны; сохранение настроек работает"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_profile_form_contract"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_profile.py#test_profile_get_renders_form_for_authenticated_user"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_profile.py#test_profile_post_updates_timezone"
        status: pass
      - kind: command
        ref: "grep -o 'name=\"[a-z_]*\"' app/templates/profile.html | sort -u — набор до и после совпал (name=\"timezone\")"
        status: pass
    human_judgment: false
  - id: D10
    description: "Тело страницы профиля собрано из компонентов — сквозной срез Плана 01 доведён до конца страницы, а не только до шелла"
    requirement: "UI-04"
    verification:
      - kind: command
        ref: "grep -c 'components/field.html' app/templates/profile.html → 1; utility-классов → 0"
        status: pass
    human_judgment: true
    rationale: "Тип проверки в плане — backstop: автотест доказывает, что тело собрано из макросов библиотеки, но «выглядит как одна система с остальными разделами» — судейское решение, вынесено в end-of-phase human-check"
  - id: D11
    description: "Перестроение записи истории в одну колонку на 1080px: блок метаданных получает верхнюю границу вместо левой и теряет левый отступ"
    verification: []
    human_judgment: true
    rationale: "Медиазапрос живёт только в браузере; автотест доказывает наличие опоры (data-hrow + data-area=\"meta\") и отсутствие селектора по подстроке инлайн-стиля, но не факт перестроения на конкретной ширине"
  - id: D12
    description: "Все существующие тесты остаются зелёными"
    verification:
      - kind: command
        ref: "uv run pytest tests/ -q → 476 passed (было 466)"
        status: pass
    human_judgment: false

# Metrics
duration: 28min
completed: 2026-08-09
status: complete
---

# Phase 01 Plan 05: Разделы «История», «Дашборд» и «Профиль» — Summary

**Семь шаблонов трёх разделов собраны заново на дизайн-системе, история получила собственный адаптивный примитив `data-hrow` вместе с недостающими базовыми правилами, а текст ошибки отправки перестал быть обрезанной строкой и выводится целиком.**

## Performance

- **Duration:** ~28 min
- **Started:** 2026-08-09T12:00Z
- **Completed:** 2026-08-09T12:28Z
- **Tasks:** 3 (все три TDD; общий RED-коммит на файл тестов)
- **Files:** 11 изменённых файлов, +660 / −238 строк
- **Тесты:** 466 → 476 (+10)

## Task Commits

1. **RED: тесты истории, дашборда и профиля** — `f90f1bd` (test)
2. **Задача 1: раздел «История» на примитиве data-hrow** — `cfdd12a` (feat)
3. **Задача 2: страница детали отправки, полный текст ошибки** — `47bfc47` (feat)
4. **Задача 3: каркас дашборда и профиль** — `6a176ec` (feat)

## Accomplishments

- **У примитива `data-hrow` появились базовые правила.** План 01 перенёс в `app.css` медиазапросы 1080px и 860px, перестраивающие `[data-hrow]` и его `[data-area="meta"]`, но самого примитива в файле не было — ни `display`, ни `grid-template-areas`. Медиазапросы полтора плана перестраивали то, чего не существует. Здесь примитив описан целиком: сетка `'head meta' / 'body meta' / 'err err'`, поверхность, радиус, левый акцент.
- **Селектор адаптива получил опору.** Блок метаданных размечен `data-area="meta"`; исправленное Планом 01 правило 1080px теперь совпадает и меняет левую границу на верхнюю. Проверяется `test_history_meta_marked_by_attribute`.
- **Последний след селектора по подстроке инлайн-стиля вычищен.** `grep -c 'style\*=' app/static/css/app.css` → 0 (было 1 — в комментарии).
- **Текст ошибки отправки виден целиком.** Раньше он выводился в списке классом усечения, а на странице детали — мелким однострочным блоком. Теперь и там, и там это `[data-longtext="mono"]`: перенос по словам и по символам, никакого многоточия и никакого раскрытия.
- **Три include без параметров переведены в макросы** (`history_card`, `recent_send_card`) — и вместе с ними починены два admin-шаблона, которые иначе молча отрисовали бы пустые записи.
- **Сквозной срез Плана 01 доведён до конца страницы профиля:** шелл был доказан там ещё Планом 01, теперь тело страницы тоже собрано из макросов библиотеки.
- **Регрессий нет:** 476 тестов зелёные.

## Разметка записи истории — Фаза 4 будет её расширять

```jinja
{% from "history/includes/history_card.html" import history_card %}
{{ history_card(log, user, detail_base_path='/history') }}
```

```html
<article data-hrow data-status="ok|fail|account_disconnected" id="history-row-{id}">
  <div data-area="head">иконка мессенджера · время · бейдж статуса · Акк #N · #external_id</div>
  <div data-area="body"><span data-grow>заголовок объявления</span><span data-secondary>→ группа</span></div>
  <div data-area="err">подпись · <span data-longtext="mono">полный текст ошибки</span></div>
  <div data-area="meta">ID · task_id · «Подробнее»</div>
</article>
```

Области сетки на широком экране: `'head meta' 'body meta' 'err err'`. На 1080px и уже — одна колонка `'head' 'body' 'meta' 'err'`, и `[data-area="meta"]` меняет левую границу на верхнюю (правило раздела 2 `app.css`, принадлежит Плану 01).

**Что Фаза 4 добавит сюда, не ломая разметки:** копирование `task_id` одним действием и повтор отправки (HIST-04) — обе кнопки становятся в `[data-area="meta"]` рядом с «Подробнее»; экспорт CSV и счётчик записей — над списком `[data-hlist]`.

## Добавленные правила `app.css` (раздел 5)

Дополнение файла прямо санкционировано `<flagged_assumptions>` плана. Все значения — токены раздела 1; ни одного нового захардкоженного цвета, радиуса или кегля.

**История:** `[data-hlist]`, `[data-hrow]`, `[data-hrow]:hover`, `[data-hrow][data-status="ok"|"fail"|"account_disconnected"]`, `[data-hrow] > [data-area="head"|"body"|"err"|"meta"]`, `[data-hrow] [data-area="head"] svg`, `[data-hrow] [data-area="body"] > [data-grow]`, `[data-hrow] [data-area="body"] > [data-secondary]`

**Читаемый целиком текст:** `[data-longtext]`, `[data-longtext="mono"]`

**Изображения объявления на детали:** `[data-thumbs]`, `[data-thumbs] img`

**Дашборд:** `[data-metrics]`, `[data-metric-value]`

**Общее:** `[data-stack]`, `[data-form]`, `[data-form] > .field`, `[data-identity]`, `[data-identity-meta]`, `[data-identity-name]`

Плюс дополнение `prefers-reduced-motion`: `[data-hrow]` гасит переход и подъём при наведении.

Ни одного нового **класса** не добавлено: все примитивы выражены атрибутами, как того требует конвенция фазы. Раскладка таблиц по-прежнему приходит параметром `cols` в `--cols` — новых классов на раздел нет ни у истории, ни у детали, ни у дашборда.

## Decisions Made

### Базовые правила `[data-hrow]` пришлось написать здесь

План описывал задачу как «разметить блок метаданных атрибутом». Фактически отсутствовал весь примитив: `grep -n 'hrow' app.css` до правки возвращал четыре строки, и все четыре — внутри медиазапросов. Без `display: grid` и `grid-template-areas` правило 1080px переопределяло несуществующую сетку. Написать базовые правила было единственным способом выполнить критерий «исправленный медиазапрос срабатывает».

### Статусный акцент — атрибут `data-status`, а не инлайн-стиль

В макете левая граница записи красится подставленным в инлайн-стиль цветом. Повторить это значило бы вернуть в проект ровно тот приём, из-за которого сломался селектор адаптива. Взяты три атрибутных правила на токенах `--ok` / `--danger` / `--warn`.

### Комментарий в `app.css` переписан, потому что его читает греп

Критерий приёмки `grep -c 'style\*=' app/static/css/app.css == 0` падал на **комментарии** Плана 01, который цитировал удалённый селектор дословно. Правила такого в файле не было. Комментарий переписан описанием вместо цитаты: смысл сохранён, греп зелёный, и будущая проверка «не вернулся ли селектор» не даёт ложного срабатывания.

### История не входит в `MIGRATED_SECTIONS`

Этот список параметризует `test_list_page_has_responsive_primitives`, который утверждает наличие `data-row`. Строка `data-hrow` подстроку `data-row` не содержит, и добавление истории туда сломало бы тест. Введён `CLEAN_SECTIONS = MIGRATED_SECTIONS + ["history"]` — им параметризуется только проверка на utility-классы. Планы 06-08 дописывают свои разделы в тот список, который соответствует их примитиву.

### `select_field` не трогался — и хрупкие утверждения профиля не сломались

План предупреждал о проверках на порядок атрибутов элемента выбора (`<option value="X" selected`). Порядок зафиксирован в `components/field.html` ещё Планом 02 и закреплён его собственным тестом. Достаточно было вызвать макрос как есть: `tests/test_pages/test_profile.py` и `tests/test_routes/test_schedules_profile_timezone.py` прошли **без единой правки**. Подпись «Профиль» тоже сохранена — её рендерит шапка шелла из `NAV_ITEMS`, то есть она же является пунктом навигации по D-11.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Два admin-шаблона отрисовали бы пустые записи истории**

- **Found during:** Задача 1
- **Issue:** `history/includes/history_card.html` включался не только историей пользователя, но и `admin/user_history.html` (строка 54) и `admin/history_partial_cards.html` (строка 2). После перевода файла в макрос `{% include %}` продолжил бы работать — и отдавать ПУСТУЮ строку: файл, состоящий из определения макроса, при включении не рендерит ничего. Обе страницы вернули бы 200 с пустым списком отправок. Это ровно тот молчаливый отказ, от которого предостерегает сам план, только на страницах, которых он не перечислял.
- **Fix:** Оба места переведены на вызов макроса `{{ history_card(log, user, detail_base_path) }}` с импортом наверху. Остальная разметка admin-шаблонов не трогалась — их полная миграция принадлежит Плану 08.
- **Files modified:** `app/templates/admin/user_history.html`, `app/templates/admin/history_partial_cards.html`
- **Verification:** полная суита зелёная, включая тесты admin-истории.
- **Committed in:** `cfdd12a`

**2. [Rule 3 - Blocker] Критерий приёмки падал на комментарии Плана 01**

- **Found during:** Задача 1 (проверка критериев)
- **Issue:** `grep -c 'style\*=' app/static/css/app.css` возвращал 1. Единственное вхождение — комментарий, дословно цитировавший удалённый селектор макета. Критерий грепает файл целиком и не отличает комментарий от правила.
- **Fix:** Комментарий переписан описанием («искал в атрибуте style фрагмент с именем области сетки») и дополнен запретом на возвращение такого селектора.
- **Files modified:** `app/static/css/app.css`
- **Verification:** `grep -c 'style\*=' app/static/css/app.css` → 0.
- **Committed in:** `cfdd12a`

### Расхождения с буквой плана (не автофиксы)

**1. Три RED-теста в одном коммите.** План предполагает RED на задачу; все новые тесты живут в одном файле и делят сидер `_seed_send_log`, поэтому RED-гейт сделан один на плане (`f90f1bd`, 6 падающих тестов). Порядок RED → GREEN для каждой задачи сохранён: Задача 1 закрыла 3 из 6, Задача 2 — ещё 1, Задача 3 — оставшиеся 2. Следствие: `just test` после Задач 1 и 2 возвращал ненулевой код именно на тестах ещё не начатых задач (473 и 474 passed соответственно), и обнулился после Задачи 3 — 476 passed.

**2. Появились примитивы, которых нет в `<artifacts_produced>`:** `[data-hlist]`, `[data-longtext]`, `[data-thumbs]`, `[data-metrics]`, `[data-metric-value]`, `[data-stack]`, `[data-form]`, `[data-identity]*`. Без них у страниц не остаётся никакого оформления: Tailwind удалён, а `app.css` до этого плана не содержал ни правил записи истории, ни сетки плиток, ни блока читаемого целиком текста. План это предвидел (`<flagged_assumptions>`: «`app.css` может дополняться правилами записи истории»); фактический объём оказался шире одной записи, потому что план охватывает три раздела.

**3. Иконка мессенджера вызывается только для известных типов.** Не `{% if item.messenger_type %}`, как в Плане 04, а `{% if log.messenger_type in ('tg_user', 'wa', 'max') %}`. Причина строже: `messenger_type` в `SendLog` — свободная строка снимка, и непустое неизвестное значение (например, старый тип из истории) провалилось бы в ветку `else`, несущую `text-gray-500`. Проверка на непустоту такой случай не ловит, проверка на вхождение — ловит.

**4. Размер иконки мессенджера в записи истории задан правилом CSS, а не параметром `size`.** `messenger_icon` кладёт значение `size` в `class` у `<svg>`, а классы размеров принадлежали удалённому фреймворку. В строках таблицы Планы 03-04 обходили это классом `.avatar` (круглая подложка 30px); в шапке записи истории 30px — слишком крупно, поэтому размер задан селектором `[data-hrow] [data-area="head"] svg`, а `size` передан пустым. На странице детали и на дашборде оставлен прежний приём с `.avatar` — там размер уместен.

**5. Кнопка возврата на странице детали переехала в шапку шелла.** План просил «кнопку возврата через `link_button`» и «заголовок раздела перенести в блоки шапки шелла». Ссылка «К истории» стоит в `{% block page_actions %}` рядом с заголовком: отдельная ссылка над карточкой дублировала бы навигацию, которая теперь есть в шелле.

**6. Раскладка страницы детали собрана из `row_open` / `cell`, а не из нового класса.** Пары «подпись → значение» — это те же строки-таблицы с двумя колонками; раскладка приходит параметром `cols`. Так критерий «no new per-section CSS classes (use the `cols` parameter)» выполняется буквально.

---

**Total deviations:** 2 автофикса (1 молчаливая поломка admin-страниц, 1 заблокированный критерий приёмки) + 6 задокументированных расхождений.
**Impact on plan:** Скоупкрипа нет. Расхождения — следствие фактов кодовой базы, которых план не знал (№2, №3, №4 и оба автофикса), и буквального выполнения его же критериев (№5, №6).

## Issues Encountered

- **`[data-hrow]` полтора плана существовал только в медиазапросах.** Это не опечатка Плана 01, а следствие разделения владения файлом: медиазапросы переносились дословно из макета блоком, а базовые правила примитива макет держит в инлайн-стилях каждой записи, то есть переносить их было неоткуда. Урок для Планов 06-08: если медиазапрос ссылается на примитив, стоит проверить, что базовое правило примитива в файле есть.
- **Комментарий может уронить критерий приёмки.** Греп по файлу не отличает документацию от кода. Цитировать в комментарии запрещённую конструкцию дословно — значит поставить мину под собственный критерий.
- **`messenger_icon` остаётся последним носителем utility-классов.** Ветка `else` несёт `text-gray-500`, ветки с `show_label=true` — `text-gray-700`. Планам 06-08: вызывать только с `show_label=false` и только для известных типов.
- **Базовая суита в этом воркtree — 466, как и оставил План 04.** 25 задокументированных `.env`-зависимых падений не воспроизводятся: `.env` в воркtree нет. Ни один из четырёх перечисленных во вводных файлов не правился.

## Known Stubs

Нет. Все три раздела подключены к живым данным: записи истории, фильтры, бесконечная прокрутка, страница детали со снимками отправки, счётчики дашборда, последние отправки и форма профиля читают реальные поля и ходят по прежним маршрутам.

**Осознанно отложено (не заглушка):**

- **Содержательное наполнение дашборда — Фаза 4.** Метрики за сутки с динамикой, ближайшие отправки, живая лента, heatmap активности и индикатор воркеров на самом дашборде относятся к DASH-01…DASH-05. Спарклайны и heatmap-ячейки как компоненты сознательно не созданы. Это граница, зафиксированная ROADMAP, а не сокращение объёма Фазы 1.
- **Копирование текста ошибки одним действием и повтор отправки из записи истории — Фаза 4 (HIST-04).** Правило этой фазы — «новый вид, старые действия». Место под обе кнопки в разметке есть: `[data-area="meta"]`.
- **Экспорт CSV и счётчик записей над списком истории** присутствуют в макете, но требований Фазы 1 не имеют — не делались.
- **Admin-раздел истории остаётся на Tailwind-разметке** (шапка, фильтры, контейнер списка) — это План 08. Здесь исправлены только два места вызова `history_card`, иначе admin-страницы отдавали бы пустые записи.
- **Индикация успешного сохранения профиля.** Обработчик перенаправляет на `/profile?saved=1`, и ни старый, ни новый шаблон этот параметр не показывает. Поведение перенесено как есть; макрос `alert` для этого уже готов.

## Threat Flags

Новых поверхностей за пределами `<threat_model>` не появилось. Статус митигаций:

| Threat ID | Статус | Чем закрыт |
|-----------|--------|-----------|
| T-05-01 | mitigated | Текст ошибки выводится обычным экранированным выводом Jinja2; ни один макрос не принимает готовую разметку, `\|safe` не используется. Обход всех шаблонов делает `test_no_unsafe_escaping` Плана 02; полнота вывода закреплена `test_history_detail_shows_error_text` на строке со спецсимволами и точкой с запятой |
| T-05-02 | mitigated | Обработчик `history_detail` не менялся: проверка `log.user_id != user.id` с редиректом на месте, правились только шаблоны. Регрессия ловится полной суитой |
| T-05-03 | mitigated | Цикл проброса фильтров перенесён дословно вместе с `\|string\|urlencode`; сентинел идентичен в `list.html` и `partial_cards.html`. Закрыт `test_history_filters_survive_pagination` (два фильтра + смещение строго больше 30) и `test_infinite_scroll_keeps_filters` Плана 03 |
| T-05-04 | mitigated | `method="post"`, `action="/profile"` и `name="timezone"` перенесены дословно; набор `grep -o 'name="[a-z_]*"'` совпал до и после. Реальное сохранение проверяет `test_profile_post_updates_timezone` |
| T-05-05 | accept | Состав отображаемых полей на странице детали не изменился; добавлена только видимая целиком форма подачи текста ошибки |
| T-05-SC | mitigated | Ни одной установки пакета: ни npm, ни pip. Новых зависимостей нет; записей `[ASSUMED]` / `[SUS]` / `[SLOP]` нет |

## User Setup Required

None — внешняя конфигурация не требуется.

## Next Phase Readiness

**Готово к Плану 06 (админка и воркеры):**

- `history_card(log, user, detail_base_path)` вызывается дословно; `detail_base_path` уже используется админкой и передаётся из контекста обработчика.
- `admin/user_history.html` и `admin/history_partial_cards.html` уже вызывают макрос — Плану 08 остаётся переверстать их собственную разметку (шапку, фильтры, контейнер). Блок фильтров там — третий и последний потребитель макроса `filters`.
- `tests/test_pages/test_responsive_markup.py` принимает новые разделы двумя списками: `MIGRATED_SECTIONS` — для разделов на `data-row`, `CLEAN_SECTIONS` — для проверки на utility-классы независимо от примитива.
- `[data-longtext]` готов везде, где требуется показать недоверенный текст целиком.
- `[data-metrics]` / `[data-metric-value]` переиспользуемы для сводок лимитов Плана 07.

**Открытые пункты, требующие человека (end-of-phase):**

- `/history` на ширине около 1000px: запись перестраивается в одну колонку, блок метаданных получает верхнюю границу вместо левой и не остаётся с лишним левым отступом (D11).
- `/history` с применённым фильтром: прокрутить до подгрузки второй страницы — подгруженные записи соответствуют фильтру (доказана форма ответа, не поведение прокрутки).
- `/dashboard` и `/profile`: обе страницы в новом тёмном шелле, панели и поля выглядят как одна система с остальными разделами (D10).
- Смена таймзоны в профиле: значение сохраняется и подставляется при повторном открытии (серверный эффект доказан автотестом, визуальная часть — нет).
- Страница детали неуспешной отправки в браузере: длинная строка ошибки переносится и читается целиком, горизонтальной прокрутки не появляется.

## Self-Check: PASSED

- Все 8 заявленных шаблонов и таблица стилей на диске: `history/list.html`, `history/includes/history_card.html`, `history/partial_cards.html`, `history/detail.html`, `dashboard.html`, `dashboard/includes/recent_send_card.html`, `profile.html`, `static/css/app.css`.
- Все 4 заявленных коммита в истории: `f90f1bd`, `cfdd12a`, `47bfc47`, `6a176ec`.
- `grep -c 'data-hrow' app/templates/history/includes/history_card.html` → 1; `grep -c 'data-area="meta"'` → 2.
- `grep -c '{% macro '` в `history_card.html` и `recent_send_card.html` → 1 в каждом.
- `grep -c 'include "history/includes/history_card.html"' app/templates/history/list.html` → 0.
- `grep -c 'components/filters.html' app/templates/history/list.html` → 1.
- `filter_params`, `hx-trigger="revealed"`, `hx-swap="outerHTML"` → по 1 в `history/list.html` и `history/partial_cards.html`; `layout=cards` → 0 в обоих.
- `grep -rc 'bg-white\|text-gray\|rounded-lg\|border-gray\|hidden sm:'` по трём файлам списка истории → 0 во всех; то же с `lg:` по `dashboard.html`, `profile.html`, `recent_send_card.html` → 0 во всех; по `history/detail.html` → 0.
- `grep -c 'truncate' app/templates/history/detail.html` → 0.
- `grep -c 'style\*=' app/static/css/app.css` → 0.
- `grep -o 'name="[a-z_]*"' app/templates/profile.html | sort -u` → `name="timezone"` — совпадает с набором до правки.
- Внешних ссылок (`http://` / `https://`) в изменённых шаблонах → 0.
- Удалённых файлов в плане нет: `git diff --name-status` показывает только `M`.
- `uv run pytest tests/ -q` → **476 passed** (было 466).

---
*Phase: 01-interfeysnyy-fundament*
*Completed: 2026-08-09*
