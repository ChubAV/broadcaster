---
phase: 01-interfeysnyy-fundament
plan: 02
subsystem: ui
tags: [jinja2, macros, design-system, alpinejs, css-tokens, accessibility, auth]

# Dependency graph
requires: ["01-01"]
provides:
  - "12 макросов библиотеки компонентов в app/templates/components/"
  - "Контракт сигнатур макросов — Планы 03-08 вызывают их дословно"
  - "Раздел 4 app.css: семантические классы компонентов на токенах Плана 01"
  - "Базовые (не-медиазапросные) правила [data-rowhead] / [data-row] / [data-grow] с раскладкой через --cols"
  - "components/modal.html — диалог подтверждения с ловушкой фокуса, готов к применению в Плане 03"
  - "app/templates/auth_base.html — второй шелл проекта, блоки title / auth_subtitle / content"
  - "Паттерн тестирования: прямой рендер макроса через templates.env без HTTP"
affects: [03-htmx-etalon, 04-dashboard, 05-istoriya, 06-admin-vorkery, 07-tarify, 08-svodnaya-proverka]

actuals:
  tokens: 20545
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Макрос принимает только текст, числа и булевы; композиция разметки — через парные обёртки и {% call %}"
    - "Раскладка сетки приходит пользовательским свойством --cols, а не новым классом на каждый раздел"
    - "Импорт компонентов в принятом в проекте стиле {% from ... import ... %}, без with context"
    - "Прямой рендер макроса с пустым контекстом как способ поймать зависимость от контекста вызывающего шаблона"

key-files:
  created:
    - app/templates/components/button.html
    - app/templates/components/field.html
    - app/templates/components/card.html
    - app/templates/components/badge.html
    - app/templates/components/table.html
    - app/templates/components/empty_state.html
    - app/templates/components/toggle.html
    - app/templates/components/progress.html
    - app/templates/components/mono.html
    - app/templates/components/avatar.html
    - app/templates/components/alert.html
    - app/templates/components/modal.html
    - app/templates/auth_base.html
    - tests/test_templates/__init__.py
    - tests/test_templates/test_components.py
  modified:
    - app/static/css/app.css
    - app/templates/auth/login.html
    - app/templates/auth/register.html
    - app/templates/auth/register_verify.html
    - app/templates/auth/register_complete.html
    - app/templates/auth/forgot_password.html
    - app/templates/auth/forgot_password_verify.html
    - app/templates/auth/forgot_password_reset.html
    - tests/test_pages/test_shell.py

key-decisions:
  - "Начальный фокус в модалке ставится на ОТМЕНУ, а не на подтверждение: удаление не должно срабатывать по Enter"
  - "Сигнатура field расширена maxlength / minlength / pattern / inputmode / align — иначе экраны кода и пароля не собираются макросом"
  - "Раскладка колонок таблицы приходит через --cols, потому что планам разделов запрещено добавлять классы в app.css"
  - "cell поддерживает блочный вызов {% call %} — сложное содержимое строится в вызывающем шаблоне, а не передаётся HTML-строкой"
  - "Ловушка фокуса написана вручную: в вендоренной сборке Alpine 3.13.3 нет плагина focus, а новых зависимостей D-02 не допускает"

patterns-established:
  - "Прямой рендер макроса: templates.env.get_template(path).module.<macro>(...) — HTTP не нужен"
  - "Хелперы тестов с параметром name делаются positional-only, иначе конфликтуют с параметром name самих макросов"
  - "Значения из request вычисляются в вызывающем шаблоне и приходят в макрос параметром"

requirements-completed: [UI-04]
requirements-advanced: [UI-01, UI-02, UI-06]

coverage:
  - id: D1
    description: "12 макросов библиотеки рендерятся напрямую через окружение Jinja и выдают непустую разметку"
    requirement: "UI-04"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_macros_take_no_context"
        status: pass
    human_judgment: false
  - id: D2
    description: "badge принимает вариант явным параметром и выдаёт разный класс для success / warning / danger / neutral"
    requirement: "UI-04"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_badge_variants"
        status: pass
    human_judgment: false
  - id: D3
    description: "field выдаёт input с переданными name, id, type, required, autocomplete, placeholder и value"
    requirement: "UI-04"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_field_renders_all_attrs"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_field_value_roundtrip"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_field_extra_attrs"
        status: pass
    human_judgment: false
  - id: D4
    description: "Макросы таблицы выдают адаптивные примитивы data-rowhead, data-row и data-grow"
    requirement: "UI-06"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_table_macros_emit_responsive_primitives"
        status: pass
    human_judgment: false
  - id: D5
    description: "Ни один шаблон проекта не отключает экранирование вывода"
    verification:
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_no_unsafe_escaping"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_badge_escapes_input"
        status: pass
      - kind: unit
        ref: "tests/test_templates/test_components.py#test_modal_escapes_title"
        status: pass
    human_judgment: false
  - id: D6
    description: "Все 7 экранов авторизации рендерятся через auth_base.html и не содержат сайдбара"
    requirement: "UI-02"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_auth_shell"
        status: pass
    human_judgment: false
  - id: D7
    description: "GET /login, /register и /forgot-password возвращают 200 и содержат признак auth-шелла; внешних хостов нет"
    requirement: "UI-01"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_auth_shell"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_auth_pages_no_external_cdn"
        status: pass
    human_judgment: false
  - id: D8
    description: "Сценарии регистрации и восстановления пароля проходят до конца — четыре шаблона без GET-роута не сломаны"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_registration.py"
        status: pass
      - kind: integration
        ref: "tests/test_pages/test_password_reset.py"
        status: pass
    human_judgment: false
  - id: D9
    description: "Формы входа и регистрации сохраняют method post и все прежние атрибуты name у полей"
    verification:
      - kind: integration
        ref: "tests/test_pages/test_shell.py#test_login_form_contract"
        status: pass
    human_judgment: false
  - id: D10
    description: "Модальное окно закрывается по Esc и возвращает фокус на элемент, который его открыл"
    verification: []
    human_judgment: true
    rationale: "Поведение ловушки фокуса и возврата фокуса живёт в браузере: автотест доказывает семантику разметки (role, aria-modal, type кнопки отмены), но не порядок обхода Tab. Тип проверки — backstop, вынесен в end-of-phase human-check"
  - id: D11
    description: "Auth-экраны выглядят как одна система с остальным приложением: тёмный фон, центральная карточка, кириллица набрана IBM Plex Sans"
    verification: []
    human_judgment: true
    rationale: "Компоновка придумана (макет auth-экраны не покрывает), соответствие визуальному языку — судейское решение"

# Metrics
duration: 16min
completed: 2026-08-09
status: complete
---

# Phase 01 Plan 02: Библиотека компонентов и экраны авторизации — Summary

**12 Jinja-макросов дизайн-системы с параметрами вместо контекста, раздел 4 `app.css` целиком на токенах Плана 01, модальное подтверждение с ловушкой фокуса и второй шелл проекта, на который переехали все семь экранов авторизации.**

## Performance

- **Duration:** ~16 min
- **Started:** 2026-08-09T10:14:37Z
- **Completed:** 2026-08-09T10:30:29Z
- **Tasks:** 3 (все три — TDD, RED-коммит перед реализацией у Задач 1 и 3)
- **Files:** 24 изменённых файла, +1154 / −253 строки

## Accomplishments

- **Библиотека собрана и доказана без HTTP.** 12 макросов, 25 тестов прямого рендера. В проекте не было ни одного теста, рендерящего шаблон напрямую — паттерн введён здесь.
- **Экраны авторизации сняты с костыля.** Семь шаблонов перестали переопределять блок тела основного шелла, чтобы обойти его проверку `{% if user %}`; у них теперь собственный шелл. Имя блока `body` в `base.html` сохранено — его переопределение может вернуться.
- **Utility-классы вырезаны из auth полностью.** −252 строки Tailwind-разметки заменены вызовами макросов; `grep` по `bg-gray|text-gray|rounded-lg|border-gray` в `app/templates/auth/` возвращает 0.
- **Модалка спроектирована с нуля.** Ни в приложении, ни в макете прецедента нет: во всём макете ноль оверлеев, единственный `position:fixed` — нижние табы. Подтверждения сегодня делает браузерный диалог.
- **Регрессий нет:** 435 тестов зелёные (было 405; +25 компонентных, +5 auth-тестов шелла).

## Task Commits

1. **Задача 1 (RED): тесты библиотеки макросов** — `2fe947b` (test)
2. **Задача 1 (GREEN): 11 макросов и семантические классы** — `f1fe268` (feat)
3. **Задача 2: модальное подтверждение (D-18)** — `26af7fb` (feat)
4. **Задача 3 (RED): тесты auth-шелла** — `9e2c5a6` (test)
5. **Задача 3 (GREEN): auth_base.html и 7 экранов** — `2765bfc` (feat)

## Итоговые сигнатуры 12 макросов

**Планы 03-08 вызывают их дословно.** Имена параметров — контракт; расхождение проявится не исключением, а пустой отрисовкой.

| Файл | Макрос | Сигнатура |
|------|--------|-----------|
| `button.html` | `button` | `button(label, variant='primary', type='submit', name=None, value=None, icon=None, disabled=false, title=None, extra_class=None)` |
| `button.html` | `link_button` | `link_button(label, href, variant='primary', icon=None, title=None, extra_class=None)` |
| `field.html` | `field` | `field(name, label=None, type='text', value='', required=false, placeholder=None, autocomplete=None, id=None, hint=None, error=None, maxlength=None, minlength=None, pattern=None, inputmode=None, align=None, disabled=false, readonly=false, step=None, min=None, max=None)` |
| `field.html` | `textarea_field` | `textarea_field(name, label=None, value='', rows=6, required=false, placeholder=None, id=None, hint=None, error=None, maxlength=None, disabled=false)` |
| `field.html` | `select_field` | `select_field(name, label=None, options=None, selected=None, id=None, required=false, hint=None, error=None, disabled=false)` |
| `card.html` | `card_open` | `card_open(title=None, subtitle=None, extra_class=None, id=None)` |
| `card.html` | `card_close` | `card_close()` |
| `badge.html` | `badge` | `badge(label, variant='neutral', mono=true, title=None)` |
| `table.html` | `rowhead` | `rowhead(columns=None, cols=None)` |
| `table.html` | `row_open` | `row_open(cols=None, extra_class=None, id=None)` |
| `table.html` | `row_close` | `row_close()` |
| `table.html` | `cell` | `cell(text=None, grow=false, mono=false, muted=false, area=None, title=None)` |
| `empty_state.html` | `empty_state` | `empty_state(title, hint=None, action_label=None, action_href=None)` |
| `toggle.html` | `toggle` | `toggle(name, checked=false, label=None, value='1', disabled=false, id=None, title=None)` |
| `progress.html` | `progress` | `progress(percent, label=None, variant='accent')` |
| `mono.html` | `mono` | `mono(text, variant='muted', upper=false, title=None)` |
| `avatar.html` | `avatar` | `avatar(name, size=30, title=None)` |
| `alert.html` | `alert` | `alert(message, variant='error')` |
| `modal.html` | `modal` | `modal(id, title, action, confirm_label, body=None, cancel_label="Отмена", confirm_variant="danger", method="post")` |

**Значения `variant` по компонентам:**

- `button` / `link_button`: `primary` · `ghost` · `danger`
- `badge`: `success` · `warning` · `danger` · `info` · `neutral`
- `alert`: `error` · `success` · `warning` · `info`
- `progress`: `accent` · `ok` · `warn` · `danger`
- `mono`: `muted` · `bright` · `accent` · `ok` · `warn` · `danger`

**Значения `icon` (текстовые имена, не разметка):** `plus` · `trash` · `check` · `arrow-right` · `pencil` · `refresh`. Тонкие SVG из макета, `stroke-width: 2.4`. Heroicons из `includes/icons.html` остаются там, где уже вписаны; `messenger_icon` переиспользуется как есть.

**Импорт — в принятом в проекте стиле:**

```jinja
{% from "components/field.html" import field %}
```

`with context` не используется нигде: он запрещён D-13 и вдобавок отключает кэширование импорта.

**Три приёма, без которых библиотеку применят неправильно:**

1. **Композиция вместо HTML-строк.** `card_open` / `card_close` и `row_open` / `row_close` — парные обёртки, содержимое пишется между ними. `cell` дополнительно поддерживает блочный вызов: `{% call cell(grow=true) %}…{% endcall %}`. Ни один макрос не принимает готовую разметку параметром.
2. **Раскладка колонок — параметр `cols`.** `rowhead(cols='minmax(180px,2.4fr) 1fr 1fr 92px')` кладёт значение в пользовательское свойство `--cols`; то же значение передаётся каждому `row_open`. Так у каждого раздела своя сетка, и планам 03-08 не нужно добавлять классы в `app.css`.
3. **Данные из `request` вычисляются в вызывающем шаблоне.** `login.html` считает `{% set password_reset_done = request.query_params.get('reset') == 'success' %}` и передаёт результат в `alert` параметром — внутри макроса `request` недоступен.

**Открытие модалки** — событием окна, поэтому кнопка-триггер может стоять где угодно:

```jinja
<button type="button" x-data x-on:click="$dispatch('modal-open-del-{{ ad.id }}')">Удалить</button>
{{ modal(id='del-' ~ ad.id, title='Удалить объявление?',
         action='/ads/' ~ ad.id ~ '/delete', confirm_label='Удалить') }}
```

## Полный список добавленных классов `app.css`

Раздел 4 файла. Все цвета, радиусы и кегли — через токены Плана 01; новых захардкоженных значений нет.

**Кнопки:** `.btn`, `.btn--primary`, `.btn--ghost`, `.btn--danger`, `.btn--block`, `.btn__label`, `.btn__icon`

**Поля:** `.field`, `.field--invalid`, `.field__label`, `.field__input`, `.field__input--area`, `.field__input--select`, `.field__input--center`, `.field__hint`, `.field__error`

**Карточка:** `.card`, `.card__head`, `.card__title`, `.card__subtitle`, `.card__body`

**Бейдж:** `.badge`, `.badge--mono`, `.badge--success`, `.badge--warning`, `.badge--danger`, `.badge--info`, `.badge--neutral`

**Пустое состояние:** `.empty`, `.empty__title`, `.empty__hint`, `.empty__action`

**Тумблер:** `.toggle`, `.toggle__input`, `.toggle__track`, `.toggle__knob`, `.toggle__label`

**Прогресс:** `.progress`, `.progress__label`, `.progress__track`, `.progress__bar`, `.progress--ok`, `.progress--warn`, `.progress--danger`

**Mono-метка:** `.mono`, `.mono--upper`, `.mono--muted`, `.mono--bright`, `.mono--accent`, `.mono--ok`, `.mono--warn`, `.mono--danger`

**Сообщения:** `.alert`, `.alert--error`, `.alert--success`, `.alert--warning`, `.alert--info`

**Строка-таблица (UI-06):** `[data-rowhead]`, `[data-row]`, `[data-row]:hover`, `[data-grow]`, `.cell`, `.cell--mono`, `.cell--muted`

**Модалка:** `.modal`, `.modal__overlay`, `.modal__panel`, `.modal__title`, `.modal__form`, `.modal__text`, `.modal__actions`

**Auth-шелл:** `[data-auth-shell]`, `.auth-card`, `.auth-brand`, `.auth-brand__mark`, `.auth-brand__name`, `.auth-subtitle`, `.auth-note`, `.auth-form`, `.auth-form--secondary`, `.auth-form__row`, `.auth-foot`

**Изменённое правило Плана 01:** `.avatar` переведён с фиксированных `30px` на `var(--avatar-size, 30px)`. Шелл вызывает класс без свойства и получает те же макетные 30px из фолбэка; макрос `avatar(name, size=…)` ставит свойство. Это единственная правка чужого правила.

**Два дополнения к `prefers-reduced-motion`:** `.progress__bar` / `.toggle__knob` и `.modal__panel` — анимации и переходы гасятся.

## Decisions Made

### Начальный фокус в модалке — на «Отмене»

Панель открывается с фокусом на кнопке отмены, а не на подтверждении. Причина в прямом запрете плана: подтверждение удаления не должно срабатывать по Enter и отмена не должна быть труднее подтверждения. `<button type="button">` по Enter вызывает клик, а не отправку формы, — поэтому такой начальный фокус закрывает оба требования одним решением. Кнопка отмены дополнительно вынесена первой в порядке обхода.

### Ловушка фокуса написана вручную

В вендоренной сборке Alpine 3.13.3 (`app/static/js/alpine.min.js`) есть только ядро; плагина focus с директивой перехвата в ней нет. Новых зависимостей D-02 не допускает, поэтому обход Tab реализован в `x-data` модалки: собирается список видимых фокусируемых элементов панели и Tab/Shift+Tab закольцовываются по нему. Возврат фокуса — через `document.activeElement`, снятый в момент открытия: так вызывающему шаблону не нужно передавать ссылку на элемент-триггер.

### Раскладка таблицы — через `--cols`, а не через классы

План запрещает планам разделов добавлять классы в `app.css`, но у каждого раздела своя сетка колонок. Значение `grid-template-columns` приходит текстовым параметром `cols` и попадает в пользовательское свойство; базовое правило читает `var(--cols, minmax(0, 1fr))`. Альтернатива — по классу на раздел — нарушила бы границу владения файлом.

### `cell` поддерживает блочный вызов

В макете «растущая» ячейка содержит аватар и название, то есть композицию, а не строку. Передавать её параметром значило бы принимать готовый HTML — прямой запрет плана. Поэтому `cell` рендерит `caller()`, когда вызван как `{% call %}`: разметку строит вызывающий шаблон, и она проходит обычное экранирование.

### `select_field` сохраняет порядок атрибутов

Существующие тесты проекта проверяют подстроку `<option value="X" selected`. Порядок атрибутов в макросе зафиксирован именно таким и закреплён тестом `test_textarea_and_select_fields`, чтобы будущая правка макроса не сломала `tests/test_pages/test_profile.py` и `tests/test_routes/test_schedules_profile_timezone.py`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Хелпер тестов конфликтовал с параметром `name` макросов**

- **Found during:** Задача 1 (GREEN)
- **Issue:** Хелпер `render(path, name, *args, **kwargs)` принимал имя макроса параметром `name`. Все вызовы вида `render("components/field.html", "field", name="email")` падали с `TypeError: render() got multiple values for argument 'name'` — у макросов библиотеки есть собственный параметр `name`. Ошибка была в тесте, а не в реализации, но блокировала 7 тестов.
- **Fix:** Параметры хелпера помечены positional-only (`def render(path, macro_name, /, *args, **kwargs)`). Покрытие не ослаблено — наоборот, теперь через хелпер можно передавать любые имена параметров макросов.
- **Files modified:** `tests/test_templates/test_components.py`
- **Verification:** 20 тестов Задачи 1 зелёные.
- **Committed in:** `f1fe268`

### Задокументированные расширения плана (не автофиксы)

**Сигнатура `field` расширена шестью атрибутами.** План перечислял `type / name / id / required / autocomplete / placeholder / label / value` и прямо разрешал: «Если чего-то не хватает — расширять `field`, а не писать разметку мимо компонента». Экраны кода подтверждения требуют `maxlength`, `pattern`, `inputmode`, экраны пароля — `minlength`; добавлены также `align` (центрированное моноширинное поле кода), `readonly`, `step`, `min`, `max` под будущие числовые поля Планов 04-07.

**Отступление от буквы D-13.** Решение говорит `{% import %}`, все 25 существующих импортов проекта написаны как `{% from ... import ... %}`. План явно предписал следовать кодовой базе — так и сделано.

**Значения по умолчанию модалки записаны двойными кавычками.** `method="post"` в сигнатуре макроса — намеренно, чтобы метод формы был виден в файле дословно и модалка не могла незаметно съехать на GET. Проверяется критерием приёмки.

**Атрибут `name` в вызовах макросов на auth-экранах записан двойными кавычками** (`field(name="email", …)`) — по той же причине: контракт с обработчиком должен читаться грепом по разметке, а не только через отрендеренную страницу.

**Добавлены классы, которых не было в `<artifacts_produced>`:** `.btn__label`, `.btn__icon`, `.btn--block`, `.field__input--area/--select/--center`, `.field--invalid`, `.card__head/__title/__subtitle/__body`, `.badge--mono`, `.empty__title/__hint/__action`, `.toggle__input/__track/__knob/__label`, `.progress__label/__track`, `.progress--ok/--warn/--danger`, `.mono--*`, `.alert--warning/--info`, `.cell/.cell--mono/.cell--muted`, `.modal__form`, `.modal__text`, весь блок auth-шелла. Все — следствие требования «инлайн-стили макета в шаблоны не копировать»: каждому элементу разметки нужно имя.

---

**Total deviations:** 1 автофикс (баг в тестовом хелпере) + 5 задокументированных расширений.
**Impact on plan:** Скоупкрипа нет. Расширения либо прямо санкционированы текстом плана, либо необходимы для выполнения его же критериев приёмки.

## Issues Encountered

- **`color-mix()` для полупрозрачных фонов бейджей и сообщений.** Токены статусов заданы в `oklch`, а бейджу нужен тот же цвет с ~12% непрозрачности. Захардкодить hex запрещено, добавлять по токену на каждую пару «статус × прозрачность» — раздуть `:root` вдвое. Взят `color-mix(in oklab, var(--ok) 12%, transparent)`: значение остаётся производным от токена. Поддержка — Chrome 111+, Safari 16.2+, Firefox 113+; при отсутствии поддержки фон просто не отрисуется, текст и граница останутся читаемыми.
- **Существующая карточка объявления пока не мигрирована.** `ads/includes/ad_card.html` остаётся на Tailwind-классах и браузерном диалоге подтверждения. Это работа Плана 03, где карточка переедет на макросы и станет первым потребителем модалки.

## Known Stubs

Нет. Все 12 макросов реализованы полностью и покрыты тестами прямого рендера; все семь auth-экранов работают на живых обработчиках.

**Осознанно неполным остаётся оформление старых страниц** — прямо принятый компромисс D-06: `base.html` не подключает Tailwind, старая разметка разделов ссылается на классы, которых нет. Критерий D-07 требует работоспособности после каждого плана, а не визуальной законченности. Разделы мигрируют Планами 03-07.

**Модалка не имеет потребителя до Плана 03** — это зафиксировано самим планом как пара «компонент здесь, применение в Плане 03», а не как заглушка: компонент полностью функционален и покрыт пятью тестами.

## Threat Flags

Новых поверхностей за пределами `<threat_model>` не появилось. Статус митигаций:

| Threat ID | Статус | Чем закрыт |
|-----------|--------|-----------|
| T-02-01 | mitigated | Параметры макросов — только текст, числа и булевы. `test_no_unsafe_escaping` обходит все 46 шаблонов проекта и падает на признаках отключённого экранирования; `test_badge_escapes_input` и `test_modal_escapes_title` проверяют экранирование поведенчески |
| T-02-02 | mitigated | `name`, `method="post"` и `action` перенесены дословно; `test_login_form_contract` + зелёные `test_registration.py` и `test_password_reset.py`, проходящие сценарии до конца |
| T-02-03 | mitigated | `auth_base.html` не рендерит навигацию и не читает `is_admin`; `grep -c 'data-side'` и `grep -c 'data-nav'` по нему → 0; `test_auth_shell` проверяет это на отрендеренной выдаче |
| T-02-04 | mitigated | Внутри панели остаётся прежняя форма POST с прежним маршрутом; `test_modal_renders_form_action` проверяет `method` и `action` внутри тега `form`, `test_modal_does_not_reuse_browser_dialog` — что браузерный диалог не переиспользуется |
| T-02-05 | accept | Тексты сообщений перенесены дословно, новых подробностей не добавлено |
| T-02-SC | mitigated | Ни одного `npm install` / нового Python-пакета. Ловушка фокуса написана вручную именно чтобы не тянуть плагин Alpine |

## User Setup Required

None — внешняя конфигурация не требуется.

## Next Phase Readiness

**Готово к Плану 03 (htmx-эталон на разделе объявлений):**

- 12 макросов с зафиксированными сигнатурами; вызывать дословно по таблице выше.
- `app.css` закрыт для дописывания: начиная с Плана 03 файл только потребляется.
- Модалка ждёт первого потребителя — подтверждения удаления объявления в `ads/includes/ad_card.html`. При подключении: заменить `onsubmit` с браузерным диалогом на кнопку-триггер с `$dispatch('modal-open-del-<id>')`, форму оставить как есть.
- Маппинг «статус домена → вариант бейджа» пишется в вызывающем шаблоне: `badge('Активно', 'success')` / `badge('Пауза', 'neutral')` для объявлений. Единого enum статусов в проекте нет, и это сознательно.

**Открытые пункты, требующие человека (end-of-phase):**

- Модалка: Esc, ловушка фокуса по Tab, возврат фокуса на открывшую кнопку — проверяется только в браузере и только после подключения потребителя в Плане 03.
- Визуальная сверка трёх auth-экранов с GET-роутом и одного экрана из POST-сценария (`register_verify`): компоновка придумана, соответствие визуальному языку — судейское решение.

**Что учесть Планам 04 и 07:** `progress` уже умеет варианты `ok` / `warn` / `danger` и сам ограничивает `percent` диапазоном 0..100 — виджету квоты и сводкам лимитов не нужно повторять эту арифметику.

## Self-Check: PASSED

- Все 15 созданных файлов существуют на диске: 12 в `app/templates/components/`, `app/templates/auth_base.html`, `tests/test_templates/__init__.py`, `tests/test_templates/test_components.py`.
- Все 5 заявленных коммитов присутствуют в истории: `2fe947b`, `f1fe268`, `26af7fb`, `9e2c5a6`, `2765bfc`.
- `ls app/templates/components/*.html | wc -l` → 12.
- `grep -rl 'with context' app/templates/components/ | wc -l` → 0.
- `grep -c 'confirm(' app/templates/components/modal.html` → 0.
- `grep -rc 'extends "base.html"' app/templates/auth/ | grep -v ':0' | wc -l` → 0; `block body` → 0; `extends "auth_base.html"` → 7 файлов.
- `grep -rc 'bg-gray\|text-gray\|rounded-lg\|border-gray' app/templates/auth/ | grep -v ':0' | wc -l` → 0.
- Внешних CDN-ссылок в `app/templates/` и `app/static/css/app.css` → 0.
- `uv run pytest tests/ -q` → 435 passed.

---
*Phase: 01-interfeysnyy-fundament*
*Completed: 2026-08-09*
