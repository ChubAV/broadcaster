---
phase: 01-interfeysnyy-fundament
plan: 03
subsystem: ui
tags: [htmx, jinja2, macros, design-system, infinite-scroll, polling, modal, dead-code]

# Dependency graph
requires: ["01-01", "01-02"]
provides:
  - "tests/test_pages/test_htmx_preserved.py — страховочная сетка всех живых HTMX-взаимодействий (UI-05)"
  - "tests/test_pages/test_responsive_markup.py — засеян разделом объявлений, Планы 04-08 дописывают свои (UI-06)"
  - "Эталон списочной страницы: page_title / page_actions + card_open → rowhead → строки → сентинел → card_close"
  - "Эталонная форма сентинела бесконечной прокрутки без параметра компоновки"
  - "ads/includes/ad_card.html::ad_card(ad, user=None, cols=AD_COLS) — карточка-макрос с явными параметрами"
  - "AD_COLS / AD_COLUMNS — раскладка колонок раздела как единый источник для шапки и строк"
  - "Первое применение components/modal.html — подтверждение удаления объявления (D-18)"
  - "Параметр компоновки принимается и игнорируется во всех шести обработчиках партиалов"
affects: [04-dashboard, 05-istoriya, 06-admin-vorkery, 07-tarify, 08-svodnaya-proverka]

actuals:
  tokens: 51000
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Страховочная сетка пишется и зеленеет ДО правок разметки, а не после"
    - "Цепочка бесконечной прокрутки проверяется на ВТОРОЙ странице выдачи, а не на первой"
    - "Парный тест на продолжение опроса против вакуумного зеленения теста на остановку"
    - "Смещение сентинела извлекается регулярным выражением, утверждается отношение «больше»"
    - "Раскладка колонок раздела живёт рядом с макросом строки, а не дублируется в шапке"

key-files:
  created:
    - tests/test_pages/test_htmx_preserved.py
    - tests/test_pages/test_responsive_markup.py
  modified:
    - app/pages/ads.py
    - app/pages/accounts.py
    - app/pages/groups.py
    - app/pages/schedules.py
    - app/pages/history.py
    - app/templates/ads/list.html
    - app/templates/ads/form.html
    - app/templates/ads/includes/ad_card.html
    - app/templates/ads/partial_cards.html
    - tests/test_pages/test_shell.py
    - tests/test_routes/test_wa_sync_status.py
  deleted:
    - app/templates/ads/partial_rows.html
    - app/templates/accounts/partial_rows.html
    - app/templates/accounts/partials/sync_status_row.html
    - app/templates/groups/partial_rows.html
    - app/templates/schedules/partial_rows.html
    - app/templates/history/partial_rows.html

key-decisions:
  - "ad_card принимает user параметром: format_datetime_for_user — глобал, но user приходит из запроса и макросу недоступен"
  - "Выдержка текста объявления сохранена отдельной колонкой — раздел меняет вид, а не состав показанных данных"
  - "Якорь строки аккаунта существует только у статуса syncing: тест якорей сеет MAX-аккаунт, иначе экран подключения WhatsApp редиректит"
  - "method=\"post\" передаётся в модалку явно, хотя совпадает с умолчанием: контракт удаления обязан читаться грепом по файлу карточки"
  - "Модалка выводится рядом со строкой, а не внутри неё: панель фиксирована, внутри сетки строки стала бы её колонкой"

patterns-established:
  - "Списочная страница: page_title / page_actions в шелле, card_open → rowhead(cols=SECTION_COLS) → макрос строки → сентинел → card_close"
  - "Сентинел — последний элемент ВНУТРИ того же контейнера, что и строки; идентичен в list.html и partial_cards.html"
  - "Кнопка-триггер модалки: <button type=\"button\" x-data x-on:click=\"$dispatch('modal-open-<id>')\">"
  - "SECTION_COLS объявляется рядом с макросом строки и импортируется страницей для шапки колонок"

requirements-completed: [UI-04, UI-05]
requirements-advanced: [UI-06]

coverage:
  - id: D1
    description: "Второй запрос партиала списка возвращает следующий сентинел со смещением строго больше запрошенного"
    requirement: "UI-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_chain"
        status: pass
    human_judgment: false
  - id: D2
    description: "Фильтры протаскиваются во вторую страницу выдачи — параметры фильтрации присутствуют в URL следующего сентинела"
    requirement: "UI-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_infinite_scroll_keeps_filters"
        status: pass
    human_judgment: false
  - id: D3
    description: "Ответ статуса синхронизации не содержит атрибутов опроса, когда статус не равен syncing, и содержит их при syncing"
    requirement: "UI-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_sync_polling_stops"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_sync_polling_continues_while_syncing"
        status: pass
    human_judgment: false
  - id: D4
    description: "Якоря подмены на месте и несут запрос обновления: строка аккаунта, статус подключения WhatsApp и MAX"
    requirement: "UI-05"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_swap_anchors_present"
        status: pass
    human_judgment: false
  - id: D5
    description: "Шесть недостижимых шаблонов удалены, ни один роутер на них не ссылается"
    verification:
      - kind: command
        ref: "grep -rc '_rows.html' app/pages/ | grep -v ':0' | wc -l → 0"
        status: pass
      - kind: command
        ref: "grep -rc 'if layout ==' app/pages/ | grep -v ':0' | wc -l → 0"
        status: pass
    human_judgment: false
  - id: D6
    description: "Запрос партиала без параметра компоновки возвращает 200, как и запрос с ним в прежней форме"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_htmx_preserved.py#test_partial_without_layout_param_ok"
        status: pass
    human_judgment: false
  - id: D7
    description: "Страница объявлений отрисована из компонентов дизайн-системы и содержит адаптивные примитивы"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_list_page_has_responsive_primitives"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_list_page_no_utility_classes"
        status: pass
    human_judgment: false
  - id: D8
    description: "Карточка-макрос отрисовывает реальные данные объявления, а не пустоту"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_ads_card_renders_data"
        status: pass
    human_judgment: false
  - id: D9
    description: "Удаление объявления подтверждается модальным окном; маршрут, метод и проверка владельца не изменились"
    requirement: "UI-04"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_ads_delete_uses_modal"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_responsive_markup.py#test_ads_delete_route_unchanged"
        status: pass
    human_judgment: false
  - id: D10
    description: "Заголовок и CTA раздела живут в шапке шелла, страница не рендерит собственный заголовок"
    requirement: "UI-06"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_ads_head_contract"
        status: pass
    human_judgment: false
  - id: D11
    description: "Сентинел остаётся последним элементом внутри того же контейнера, что и карточки"
    verification: []
    human_judgment: true
    rationale: "Тип проверки — backstop: положение элемента в потоке относительно контейнера доказывается прокруткой в браузере, автотест видит только присутствие сентинела в теле ответа"
  - id: D12
    description: "Перестроение строк в карточное представление на ширине меньше 860px и работа модалки в браузере"
    verification: []
    human_judgment: true
    rationale: "Медиазапросы и ловушка фокуса живут только в браузере; вынесено в end-of-phase human-check вместе с открытыми пунктами Планов 01 и 02"

# Metrics
duration: 22min
completed: 2026-08-09
status: complete
---

# Phase 01 Plan 03: HTMX-эталон и миграция раздела «Объявления» — Summary

**15 автотестов зафиксировали все живые HTMX-взаимодействия ДО первой правки разметки, после чего удалена недостижимая половина адаптива (6 шаблонов, 269 строк, 6 ветвлений) и раздел «Объявления» собран заново на дизайн-системе с модальным подтверждением удаления.**

## Performance

- **Duration:** ~22 min
- **Tasks:** 3 (Задачи 1 и 3 — TDD, у Задачи 3 отдельный RED-коммит)
- **Files:** 19 изменённых файлов, +599 / −402 строки
- **Тесты:** 435 → 456 (+21: 15 страховочных, 5 адаптивных, 1 контракт шапки)

## Task Commits

1. **Задача 1: страховочная сетка живых HTMX-взаимодействий** — `6ec30a8` (test)
2. **Задача 2: удаление недостижимой строчной компоновки (D-15)** — `d76692b` (refactor)
3. **Задача 3 (RED): адаптивные примитивы и контракт шапки** — `4ad009c` (test)
4. **Задача 3 (GREEN): раздел «Объявления» и первое применение модалки** — `3f06994` (feat)

## Итоговая форма сентинела бесконечной прокрутки

**Планы 04-08 повторяют это дословно.** Разметка идентична в `ads/list.html` и `ads/partial_cards.html`:

```jinja
{% if has_next %}
<div hx-get="/ads/partial?offset={{ next_offset }}&limit=30" hx-trigger="revealed" hx-swap="outerHTML" class="empty__hint">Загрузка...</div>
{% endif %}
```

Четыре инварианта, каждый из которых ломается молча:

1. **Сентинел — последний элемент ВНУТРИ того же контейнера, что и строки.** Он заменяет сам себя (`hx-swap="outerHTML"`) и приносит вместе со следующей порцией новый сентинел. Вынести его наружу или завернуть список в дополнительный контейнер — значит порвать цепочку так, что первый экран останется правильным.
2. **`list.html` и `partial_cards.html` содержат идентичный сентинел.** Правится один — синхронно правится второй.
3. **Цель подмены неявная (сам сентинел).** Атрибута явной цели в проекте нет нигде; добавлять его нельзя — проверять это нечем и незачем.
4. **Параметр компоновки из URL ушёл.** После Задачи 2 он ничего не выбирает. Разделы с фильтрами дополнительно протаскивают их циклом — см. `groups/partial_cards.html`:
   `{% for k, v in (filter_params|default({})).items() %}&{{ k }}={{ v|string|urlencode }}{% endfor %}`.

## Итоговая структура списочной страницы

**Эталон для Планов 04-08.** `app/templates/ads/list.html`:

```jinja
{% extends "base.html" %}
{% from "components/button.html" import link_button %}
{% from "components/card.html" import card_open, card_close %}
{% from "components/table.html" import rowhead %}
{% from "components/empty_state.html" import empty_state %}
{% from "ads/includes/ad_card.html" import ad_card, AD_COLS, AD_COLUMNS %}

{% block title %}Объявления — Broadcaster{% endblock %}
{% block page_title %}Объявления{% endblock %}
{% block page_actions %}{{ link_button('Создать', '/ads/new', icon='plus') }}{% endblock %}

{% block content %}
{% if ads %}
{{ card_open() }}
  {{ rowhead(columns=AD_COLUMNS, cols=AD_COLS) }}
  {% for ad in ads %}{{ ad_card(ad, user) }}{% endfor %}
  {% if has_next %}<div hx-get="…" hx-trigger="revealed" hx-swap="outerHTML" class="empty__hint">Загрузка...</div>{% endif %}
{{ card_close() }}
{% else %}
{{ empty_state('Объявлений пока нет', hint='…', action_label='Создать объявление', action_href='/ads/new') }}
{% endif %}
{% endblock %}
```

Что здесь принципиально:

- **Заголовок и CTA раздела — блоки шелла, а не разметка страницы.** Собственный заголовок из тела удалён, иначе он задваивается с шапкой. Проверяется `test_ads_head_contract`: `<h1>` на странице ровно один, и он внутри `<header data-head>`.
- **`SECTION_COLS` объявляется рядом с макросом строки и импортируется страницей.** Так шапка колонок и строки физически не могут разъехаться. Для объявлений: `AD_COLS = 'minmax(180px,2.2fr) minmax(0,1.6fr) 96px 104px 116px 104px 168px'`, `AD_COLUMNS = ['Объявление', 'Текст', 'Отправок', 'Расписаний', 'Создано', 'Статус', '']`.
- **Пустое состояние — `empty_state`, а не своя вёрстка.**
- **Ни одного нового класса в `app.css`.** Файл закрыт для дописывания с Плана 03; раскладка приходит через `cols` → `--cols`.

## Карточка как макрос

```jinja
{% macro ad_card(ad, user=None, cols=AD_COLS) %}
```

`ad` стал явным параметром: импортированные шаблоны Jinja контекста вызывающего не получают, и прежний `{% include %}` внутри `{% for %}` в макрос напрямую не переводится. `user` тоже приходит параметром — `format_datetime_for_user` доступен как глобал окружения, но его второй аргумент (пользователь с таймзоной) — данные запроса, а не глобал.

Дата создания переведена с прямого `strftime` на общий глобал: раньше карточка форматировала дату мимо хелпера, игнорируя таймзону пользователя.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Существующий тест проверял формулировку удаляемой ветки**

- **Found during:** Задача 2 (полная суита после удаления шаблонов)
- **Issue:** `test_sync_status_active_shows_groups` утверждал наличие строки «Загружено 3 групп». Эта формулировка жила только в `accounts/partials/sync_status_row.html` — том самом недостижимом из интерфейса шаблоне, который Задача 2 удаляет. После схлопывания ответ всегда карточный, а карточка показывает подпись «Групп» и число соседними элементами.
- **Fix:** Утверждение переведено на карточную выдачу регулярным выражением `Групп</span>\s*<span[^>]*>\s*3\s*</span>` — проверяется и подпись, и само число, то есть покрытие не ослаблено.
- **Files modified:** `tests/test_routes/test_wa_sync_status.py`
- **Verification:** 7 тестов файла зелёные, полная суита 450 на момент фикса.
- **Committed in:** `d76692b`

**2. [Rule 2 - Missing critical] Поведенческой проверки удаления объявления не существовало**

- **Found during:** Задача 3
- **Issue:** Угроза T-03-02 (Elevation of Privilege) помечена как `mitigate` с обоснованием «маршрут, метод POST и серверная проверка владельца остаются прежними». Ни одного теста, который бы это доказывал, в проекте не было: `grep` по `tests/` находил только проверки разметки. Митигация существовала на словах.
- **Fix:** Добавлен `test_ads_delete_route_unchanged` — POST по маршруту удаляет своё объявление и НЕ удаляет чужое (объявление другого владельца остаётся в БД).
- **Files modified:** `tests/test_pages/test_responsive_markup.py`
- **Verification:** тест зелёный; T-03-02 закрыт поведенчески, а не декларативно.
- **Committed in:** `3f06994`

**3. [Rule 3 - Blocking] Литеральный критерий приёмки ловил упоминание в комментарии**

- **Found during:** Задача 1
- **Issue:** Критерий `grep -c 'hx-target' tests/test_pages/test_htmx_preserved.py == 0` падал из-за пояснения в docstring, которое называло отсутствующий атрибут, объясняя, почему про него нечего утверждать. Ровно тот же случай, что автофикс №3 Плана 01-01.
- **Fix:** Формулировка перефразирована на «атрибут явной цели подмены». Смысл сохранён, критерий выполняется.
- **Files modified:** `tests/test_pages/test_htmx_preserved.py`
- **Verification:** `grep -c 'hx-target'` → 0.
- **Committed in:** `6ec30a8`

### Расхождения с буквой плана (не автофиксы)

**Сигнатура карточки — `ad_card(ad, user=None, cols=AD_COLS)`, а не `ad_card(ad, image_url=None)`.** Параметр `image_url` не нужен: `get_image_url` — глобал окружения Jinja, макросу он доступен напрямую, и передавать вычисленный URL параметром значило бы дублировать вызов в каждом месте использования. Взамен появились два параметра, без которых карточка неполна: `user` (иначе дата уходит мимо таймзоны пользователя) и `cols` (раскладка колонок, одна и та же для шапки и строк). Критерий приёмки `{% macro ad_card(ad` выполняется.

**Якорь строки аккаунта проверяется на MAX-аккаунте, а не на WA.** План предполагал, что `/accounts` содержит якорь `account-row-<id>` у любого аккаунта. Фактически якорь существует только у аккаунта со статусом `syncing` — у остальных статусов замене неоткуда взяться, и это правильно. Но синхронизирующийся WA-аккаунт заставляет `/accounts/connect/wa` отдать редирект, а этот экран проверяется в том же тесте. Поэтому сеется MAX-аккаунт: якорь строки берётся с него, а экран подключения WhatsApp остаётся доступен.

**Якорь MAX проверяется на ответе POST, а не GET.** План говорит «выдачи `/accounts/connect/wa` и `/accounts/connect/max`». GET `/accounts/connect/max` отдаёт шаг ввода телефона — якоря опроса на нём нет и не должно быть; шаг QR достигается отправкой формы на `/accounts/connect/max/start`. Тест бьёт туда, где якорь действительно живёт.

**Колонок в строке семь, а не пять.** Прежняя карточка показывала выдержку текста объявления (`ad.text[:80]`). Правило фазы — «новый вид, старые действия»; молча убрать показываемые данные значило бы менять не только вид. Выдержка сохранена отдельной колонкой.

**Изображение объявления отрисовывается классом `.avatar`.** Собственного класса под миниатюру в `app.css` нет, а файл закрыт для дописывания с Плана 03. `.avatar` даёт 30-пиксельный круг из существующих токенов. Ограничение: без `object-fit` неквадратное изображение будет сжато по одной оси. Это косметика, и её место — в Фазе 2, которая переделывает экран объявления под вложения (D-06).

**`method="post"` передан в модалку явно.** Значение совпадает с умолчанием макроса, но маршрут и метод удаления — контракт с обработчиком, и он обязан читаться грепом по файлу карточки. Это тот же приём, что План 02 применил к `field(name="email", …)`.

---

**Total deviations:** 3 автофикса (1 баг, 1 недостающая критичная проверка, 1 блокирующий) + 5 задокументированных расхождений.
**Impact on plan:** Скоупкрипа нет. Все расхождения — следствие фактов кодовой базы, которых план не знал, либо требований самого плана.

## Issues Encountered

- **Пересчёт числа шаблонов сошёлся точно.** `find app/templates -type f | wc -l` → **55**, как и предсказывал критерий приёмки (48 исходных − 6 удалённых + 13 добавленных Планом 01-02).
- **Порядок операции Задачи 2 оказался не формальностью.** Схлопывание ветвлений до удаления файлов означало, что после каждого шага приложение оставалось работоспособным, а полная суита — прогоняемой. Обратный порядок сломал бы шесть обработчиков одновременно.
- **Базовая суита в этом воркtree — 435, а не 433.** Расхождение с вводными: `.env` в воркtree нет, поэтому 25 задокументированных `.env`-зависимых падений не воспроизводятся. Ни один из четырёх перечисленных файлов не правился, кроме одной строки в `test_wa_sync_status.py`, вынужденной удалением шаблона (автофикс №1).

## Known Stubs

Нет. Раздел «Объявления» полностью подключён к живым данным: список, статистика отправок и расписаний, статус, дата создания и изображение читают реальные поля модели; удаление ходит по прежнему маршруту.

**Осознанно неполным остаётся оформление остальных разделов** — прямо принятый компромисс D-06: `base.html` не подключает Tailwind, и разметка ещё не мигрированных разделов ссылается на классы, которых нет. Разделы мигрируют Планами 04-07.

**`ads/form.html` будет переделан Фазой 2** (черновики, вложения, встроенные расписания) — компромисс D-06, зафиксированный планом заранее. Здесь экран переведён на макросы целиком, потому что без Tailwind старая разметка осталась бы без стилей.

## Threat Flags

Новых поверхностей за пределами `<threat_model>` не появилось. Статус митигаций:

| Threat ID | Статус | Чем закрыт |
|-----------|--------|-----------|
| T-03-01 | mitigated | Параметры `ad_card` — только данные модели; готовая разметка не передаётся. Autoescape не отключается; `test_no_unsafe_escaping` Плана 02 обходит все шаблоны проекта, включая новые |
| T-03-02 | mitigated | Маршрут, `method="post"` и серверная проверка владельца не тронуты. **Закрыт поведенчески:** `test_ads_delete_route_unchanged` доказывает, что чужое объявление не удаляется (автофикс №2) |
| T-03-03 | mitigated | Условность HTMX-атрибутов по статусу сохранена дословно; парные `test_sync_polling_stops` и `test_sync_polling_continues_while_syncing` не дают тесту на остановку зазеленеть вакуумно |
| T-03-04 | mitigated | Обработчики партиалов не менялись в части выборки — правился только выбор шаблона; фильтрация по владельцу на месте, полная суита зелёная |
| T-03-05 | accept | `offset` / `limit` остались как были (`ge=0`, `ge=1, le=100`); фаза их не меняет |
| T-03-SC | mitigated | Ни одной установки пакета: ни npm, ни pip. Новых зависимостей план не вводит |

## User Setup Required

None — внешняя конфигурация не требуется.

## Next Phase Readiness

**Готово к Планам 04-08:**

- Форма сентинела и структура списочной страницы зафиксированы выше — повторять дословно, не переизобретать.
- Модалка получила первого потребителя и работает в связке с Alpine: кнопка-триггер `x-on:click="$dispatch('modal-open-<id>')"`, форма внутри панели с прежним маршрутом и методом.
- Параметр компоновки во всех шести обработчиках партиалов **принимается и игнорируется** — удалять его из сигнатур нельзя, пока живы открытые вкладки со старыми URL.
- `app.css` остаётся закрытым для дописывания: раскладка раздела задаётся `SECTION_COLS` через `cols` → `--cols`.
- `tests/test_pages/test_responsive_markup.py` засеян: добавление раздела — это одна строка в `SECTION_URLS` и одно значение в двух параметризациях.

**Открытые пункты, требующие человека (end-of-phase):**

- Прокрутка `/ads` до подгрузки второй страницы: новые строки появляются без перезагрузки, фильтры не сбрасываются, сентинел не «залипает». Автотест доказывает форму ответа, но не положение элемента в потоке (D11).
- Перестроение строк в карточное представление на ширине меньше 860px.
- Модалка удаления в браузере: открытие, Esc, ловушка фокуса по Tab, возврат фокуса на кнопку-триггер, «Отмена» закрывает без удаления. Это же закрывает открытый пункт D10 Плана 02, у которого до сих пор не было потребителя.
- Сжатие неквадратной миниатюры объявления в круге `.avatar` — оценить, терпимо ли до Фазы 2.

## Self-Check: PASSED

- Оба созданных файла на диске: `tests/test_pages/test_htmx_preserved.py`, `tests/test_pages/test_responsive_markup.py`.
- Все шесть удалённых шаблонов отсутствуют; `find app/templates -type f | wc -l` → 55.
- Все 4 заявленных коммита в истории: `6ec30a8`, `d76692b`, `4ad009c`, `3f06994`.
- `grep -rc 'if layout ==' app/pages/ | grep -v ':0' | wc -l` → 0; `grep -rc '_rows.html' app/pages/ | grep -v ':0' | wc -l` → 0.
- `grep -c 'hx-target' tests/test_pages/test_htmx_preserved.py` → 0; `grep -rc 'hx-target' app/templates/ads/` → 0 во всех четырёх файлах.
- `grep -c 'layout=cards'` в `ads/list.html` и `ads/partial_cards.html` → 0; `hx-trigger="revealed"` и `hx-swap="outerHTML"` присутствуют в обоих.
- `grep -rc 'bg-white\|text-gray\|rounded-lg\|border-gray\|lg:' app/templates/ads/ | grep -v ':0' | wc -l` → 0; импорты из `components/` в 3 файлах раздела.
- `grep -c 'onsubmit'` и `grep -c 'strftime'` в `ad_card.html` → 0; `components/modal.html` и `method="post"` присутствуют.
- Внешних CDN-ссылок в `app/templates/ads/` → 0.
- `just test` → **456 passed**.

---
*Phase: 01-interfeysnyy-fundament*
*Completed: 2026-08-09*
