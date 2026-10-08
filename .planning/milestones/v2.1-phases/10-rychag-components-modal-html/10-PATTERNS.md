# Phase 10: Рычаг `components/modal.html` — Pattern Map

**Mapped:** 2026-09-02
**Files analyzed:** 17 (2 шаблона-рычага, 1 новый шаблон ответа, 8 обработчиков, 6 файлов гейтов/записей)
**Analogs found:** 16 / 17 (одному файлу — новому шаблону ответа — аналог найден дословный)

Разведки у фазы нет (ROADMAP: «Research: не требуется»), поэтому источник образцов —
ТОЛЬКО отгруженный код Фазы 9. Все выдержки ниже сняты с рабочего дерева 2026-09-02.

---

## File Classification

| Файл (правится / заводится) | Роль | Поток данных | Ближайший аналог | Качество |
|---|---|---|---|---|
| `app/templates/components/modal.html` | component (Jinja-макрос) | request-response | `app/templates/components/form_wrapper.html:130-140` | exact (сличение — предмет D-16) |
| `app/templates/includes/notice_area.html` | component (shell include) | — | сам себе (правка `tabindex` на `:77`) | self |
| `app/templates/ads/partials/sched_delete_response.html` *(новый)* | template (OOB-ответ) | fragment / OOB | `app/templates/account_groups/partials/delete_response.html` | exact |
| `app/pages/schedules.py::schedules_delete` (`:788`) | route handler | fragment + OOB | `app/pages/account_groups.py::…delete` (`:743-813`) | exact |
| `app/pages/accounts.py::accounts_delete` (`:985`) | route handler | request-response → `HX-Location` | `app/pages/account_groups.py:495` / `:743` | exact |
| `app/pages/ads.py::ads_delete` (`:716`) | route handler | request-response → `HX-Location` | там же | exact |
| `app/pages/history.py::history_retry` (`:826`) | route handler | request-response + `?notice=` | `app/pages/account_groups.py:495` | exact |
| `app/pages/admin.py::admin_restart_worker` (`:867`) | route handler | request-response + `?notice=` | там же | exact |
| `app/pages/admin.py::admin_drop_task` (`:1061`) | route handler | request-response + `?result=` (D-07) | там же | role-match (адрес несёт ЧУЖОЙ ключ) |
| `app/pages/admin.py::admin_impersonate` (`:1670`) | route handler | request-response + **cookie** | `app/pages/auth.py:514-517` (`impersonation_stop`) | role-match |
| `app/pages/admin.py::admin_delete_user` (`:1818`) | route handler | request-response → `HX-Location` | `app/pages/account_groups.py:495` | exact |
| `app/templates/ads/includes/sched_card.html` | template (карточка) | fragment target | `app/templates/account_groups/includes/group_row.html:340-346` | exact |
| `app/templates/ads/form.html:194-199` | template (контейнер + счётчик) | OOB side-area | `account_groups/partials/count_rule_oob.html` | exact |
| `tests/test_templates/test_components.py` | test (gate, числа + JS-исполнение) | сам себе (`:1609`, `:912-914`, `:1158`) | self |
| `tests/test_templates/test_htmx_markup_gates.py` | test (gate, числа + перечни изъятий) | `DISABLED_ELT_EXCEPTIONS_DECLARED` (`:2796`) | self |
| `tests/test_pages/test_htmx_gates.py` | test (gate, счётчик прогресса) | `NOT_YET_CONVERTED_COUNT` (`:283`) | self |
| `tests/test_templates/test_htmx_inventory.py:177` | test (gate, число) | self | self |

---

## Pattern Assignments

### 1. `app/templates/components/modal.html` (component, рычаг)

**Аналог формы-обёртки для сличения D-16:** `app/templates/components/form_wrapper.html:130-140`

```jinja
{% macro form_wrapper(action, target=None, swap=None, trigger=None, disabled_elt='find button[type=submit]', sync=None) -%}
<form method="post" action="{{ action }}" hx-post="{{ action }}"
      {%- if target %} hx-target="{{ target }}" hx-swap="{{ swap or 'outerHTML' }}"
      {%- else %} hx-swap="none"{% endif %}
      {%- if trigger %} hx-trigger="{{ trigger }}"{% endif %}
      {%- if sync %} hx-sync="{{ sync }}"{% endif %}
      {%- if disabled_elt %} hx-disabled-elt="{{ disabled_elt }}"{% endif %} hx-indicator="find .form-busy">
  {%- if caller is defined %}{{ caller() }}{% endif %}
  <span class="form-busy" aria-hidden="true"></span>
</form>
{%- endmacro %}
```

Набор свойств качества, который гейт D-16 обязан слицать: `hx-post="{{ action }}"`
(посимвольно равен `action`), `hx-swap="none"`, `hx-disabled-elt="find button[type=submit]"`,
`hx-indicator="find .form-busy"`, узел `<span class="form-busy" aria-hidden="true"></span>`.
Различия, которые гейт обязан ДОПУСКАТЬ (выписаны в D-16): порядок узлов и имя класса формы.

**Сегодняшнее состояние рычага** (`modal.html:269` — сигнатура, `:280-289` — форма):

```jinja
{% macro modal(id, title, action, confirm_label, body=None, cancel_label="Отмена", confirm_variant="danger", method="post", hx_post=false, hx_include=None) -%}
    <form class="modal__form" method="{{ method }}" action="{{ action }}"
          x-on:submit="if (sending) { $event.preventDefault(); return; } sending = true"
          {%- if hx_post %} x-on:htmx:after-request="sending = false" hx-post="{{ action }}" hx-swap="none" hx-disabled-elt="find button[type=submit]" hx-indicator="find .form-busy"{% if hx_include %} hx-include="{{ hx_include }}"{% endif %}{% endif %}>
      {%- if body %}<p class="modal__text">{{ body }}</p>{% endif %}
      {%- if caller is defined %}{{ caller() }}{% endif %}
      {%- if hx_post %}<span class="form-busy" aria-hidden="true"></span>{% endif %}
```

Целевое состояние (D-14, D-15): снять `hx_post=false, hx_include=None` из сигнатуры;
условие `{% if hx_post %}` внутри тега исчезает целиком (это и есть `CONDITIONAL_PLACES` 2 → 1);
узел `form-busy` печатается безусловно; `x-on:htmx:after-request` получает ветвь D-12.

**Объект `x-data` — предмет D-10/D-11/D-12** (`modal.html:270-278`):

```javascript
open: false,
opener: null,
sending: false,
show() { this.sending = false; this.opener = document.activeElement; this.open = true; document.documentElement.classList.add('is-modal-open'); this.$nextTick(() => this.$refs.cancel.focus()); },
hide() { if (!this.open) return; this.open = false; document.documentElement.classList.remove('is-modal-open'); const back = this.opener; this.opener = null; if (back && back.focus) this.$nextTick(() => back.focus()); },
destroy() { if (this.open) { this.open = false; document.documentElement.classList.remove('is-modal-open'); } },
```

Три точки правки, названные CONTEXT дословно:
- `hide()` — `if (back && back.focus)` заменяется на проверку `isConnected` (Landmine 2);
  ветвь «открывателя в документе нет» приземляет фокус на `#notice`.
- `destroy()` — сюда же добавляется приземление фокуса (Landmine 1); страж `if (this.open)`
  сохраняется, он и есть различитель «снос закрытой соседки фокус не трогает».
- атрибут формы — `x-on:htmx:after-request="sending = false; if ($event.detail.successful) hide()"` (D-12).

**Приземление фокуса** — `app/templates/includes/notice_area.html:77`:

```jinja
<div id="notice" role="status" aria-live="polite">{% if notice and notice.variant != 'error' %}{{ alert(notice.text, notice.variant) }}{% endif %}</div>
<div id="notice-alert" role="alert" aria-live="assertive">{% if notice and notice.variant == 'error' %}{{ alert(notice.text, notice.variant) }}{% endif %}</div>
```

`tabindex="-1"` вписывается в первый `div` (D-11; форма — на усмотрение планировщика).

---

### 2. Восемь обработчиков (route handler, request-response → `HX-Location`)

**Аналог — единственный сегодняшний потребитель `respond()`:** `app/pages/account_groups.py`.
Весь проект использует слой ответа ТОЛЬКО из этого файла (`:322, :326, :447, :495, :584, :679, :743, :813`).

**Механизм** (`app/pages/htmx.py:305-367`, читать вместе с докстрингом):

```python
async def respond(
    request: Request,
    *,
    redirect: str,
    notice: str | None = None,
    fragment: Callable[[], Awaitable[Response]] | None = None,
) -> Response:
    ...
    if notice is not None:
        _require_registered_notice(notice)

    if not is_htmx(request):
        return RedirectResponse(url=_with_notice(redirect, notice), status_code=302)

    if fragment is None:
        return location_response(_with_notice(redirect, notice))

    _with_notice(redirect, notice)          # адрес деградации проверяется и на ветви фрагмента

    response = await fragment()
    if notice is None:
        return response
    return _glue_notice(response, notice)
```

```python
def location_response(location: str) -> Response:
    return Response(
        status_code=204, headers={HX_LOCATION_HEADER: _local_path(location)}
    )
```

**Форма вызова для семи маршрутов ветки `HX-Location`** (аналог — `account_groups.py:495`):

```python
return await respond(request, redirect=screen_url)                 # без кода исхода
return await respond(request, redirect=screen_url, notice=notices.SOME_CODE)   # с кодом
```

Сегодняшняя форма, которую вызов замещает, — например `app/pages/admin.py:926`:

```python
return RedirectResponse(url=f"{location}?notice={notices.WORKER_NO_CONTAINER}", status_code=302)
```

⚠️ `?notice=` НЕ клеится в строку адреса руками: код едет параметром `notice=`,
`_with_notice()` собирает адрес сам. Для `admin_drop_task` — обратное (D-07):
`?result=` остаётся ЧАСТЬЮ строки `redirect=`, а `notice=None`:

```python
return await respond(request, redirect=f"/admin/queue?result={code}")
```

**Ловушка cookie (D-05, `admin_impersonate`, `app/pages/admin.py:1755-1756`):**

```python
    response = RedirectResponse(url="/dashboard", status_code=302)
    set_session_cookie(response, token, settings)
```

Тот же приём стоит в `app/pages/auth.py:514-517` (`impersonation_stop`) — cookie
навешена на ВОЗВРАЩАЕМЫЙ объект. `location_response()` собирает НОВЫЙ `Response(204)`,
поэтому `set_session_cookie` обязан примениться к результату `respond()`, а не к
выброшенному `RedirectResponse`. `set_session_cookie` — единственная функция установки
(план 06-02), собственный `set_cookie` здесь запрещён.

**Скрытое поле контекста (D-02)** — живой прецедент `app/pages/schedules.py:215-238`:

```python
def _editor_redirect(form_data, ad_id: int | None, schedule_id: int | None = None):
    if form_data.get("return_to") == RETURN_TO_EDITOR and ad_id is not None:
        url = f"/ads/{ad_id}/edit"
        if schedule_id is not None:
            url += f"?sched={schedule_id}#sched-{schedule_id}"
        return RedirectResponse(url=url, status_code=302)
    return RedirectResponse(url="/schedules", status_code=302)
```

Функция сегодня возвращает ОТВЕТ. Переводя `schedules_delete` на `respond()`, надо взять
из неё АДРЕС (строку), а форму ответа отдать `respond()` — иначе получатся два решения об
одной форме ответа, ровно то, что запрещает докстринг `account_groups.py:432` и `:606`.

---

### 3. `app/pages/schedules.py::schedules_delete` — единственный фрагментный путь (D-09)

**Аналог — дословный:** `app/pages/account_groups.py:743-813` (хвост обработчика удаления группы):

```python
        active_groups, total_groups = await _group_counts(db, user.id, account_id)
        html = templates.env.get_template(
            "account_groups/partials/delete_response.html"
        ).render(
            group_id=group_id,
            active_groups=active_groups,
            total_groups=total_groups,
        )
        return HTMLResponse(html)

    # `notice` НЕ передаётся (D-10): исход виден по исчезнувшей строке и по
    # счётчику, а плашка на каждый успех превратила бы обратную связь в шум.
    return await respond(request, redirect=screen_url, fragment=_fragment)
```

Копировать надо: замыкание `_fragment` внутри обработчика, рендер шаблона через
`templates.env.get_template(...).render(...)`, `HTMLResponse`, отсутствие `notice` на
успехе (D-03), и ветвление «список опустел → `respond()` БЕЗ `fragment`» (D-04).

**Шаблон ответа — аналог `app/templates/account_groups/partials/delete_response.html:99-101`:**

```jinja
<div id="group-row-{{ group_id }}" hx-swap-oob="delete"></div>
<div id="group-del-{{ group_id }}" hx-swap-oob="delete"></div>
{% include "account_groups/partials/count_rule_oob.html" %}
```

Три несущих свойства файла-образца (все выписаны в его шапке, строки 1-98):
- **тело плоское**, узлы — прямые дети файла: `allowNestedOobSwaps: false` в блоке конфигурации;
- **узлы безусловны**, ветви по факту удаления нет — иначе наличие узла стало бы признаком удаления;
- **линейка счётчика ВКЛЮЧАЕТСЯ**, а не копируется — вторая копия разошлась бы молча,
  и инвентарь `OOB_BLOCKS` считает ФАЙЛЫ.

Для расписания соответствие: `#sched-{{ s.id }}` (снос карточки) + `#sched-del-{{ s.id }}`
(снос панели) + область счётчика.

**Цель сноса строки** — `app/templates/ads/includes/sched_card.html:112`:

```jinja
<article data-sched-card id="sched-{{ s.id }}">
```

**Побочная область (линейка счётчика)** — `app/templates/ads/form.html:194-199`:

```jinja
        {{ mono(sched_count_label(editor.schedules_count), variant='muted', upper=true) }}
        <div data-sched-list>
```

⚠️ `id` у линейки СЕГОДНЯ НЕТ — по D-12 Фазы 9 долгоживущая область обязана получить
постоянную обёртку с `id` и подмену `innerHTML:#id` (это в «Claude's Discretion»).

**Форма-триггер и блочный вызов панели** — `sched_card.html:253-277`:

```jinja
    <form method="post" action="/schedules/{{ s.id }}/delete"
          x-data x-on:submit.prevent="$dispatch('modal-open-sched-del-{{ s.id }}')">
      <input type="hidden" name="return_to" value="editor">
      {{ button('УДАЛИТЬ РАСПИСАНИЕ', variant='danger', icon='trash') }}
    </form>
...
{% call modal(id='sched-del-' ~ s.id,
              title='Удалить расписание?',
              action='/schedules/' ~ s.id ~ '/delete',
              confirm_label='Удалить',
              method="post",
              body=parts | join(' · ') if parts else 'Не заполнено') %}
  <input type="hidden" name="return_to" value="editor">
{% endcall %}
```

⚠️ Форма-ТРИГГЕР `hx-post` не получает никогда (D-03 Фазы 9) — тексты и подписи
переносятся дословно (`<specifics>`). Единственный сегодняшний носитель `hx_post=true` —
`app/templates/account_groups/includes/group_row.html:345`, и после D-14 аргумент
снимается оттуда тоже.

---

## Shared Patterns

### Инвентарный гейт СОБСТВЕННЫМ ЧИСЛОМ (D-13 Фазы 8)
**Источник:** `tests/test_templates/test_htmx_markup_gates.py:1815`, `:1869`, `:1889`
**Применять к:** каждому числу таблицы CONTEXT

```python
# Ноль объявлялся ИМЕНОВАННОЙ КОНСТАНТОЙ и до появления первой цели — ровно
# затем, чтобы правила существования цели и границы клиентского состояния не
# были вакуумно зелёными навсегда. Прецедент формы — SERVER_SIDE_VALIDATION_RESPONSES.
HX_TARGETS = 1
```

Форма записи: комментарий объясняет ПОЧЕМУ число именно такое → **ЛЕТОПИСЬ ЧИСЛА**
отдельной строкой с фазой, планом и источником движения. Образец летописи —
`tests/test_templates/test_htmx_inventory.py:179-182`:

```python
# ЛЕТОПИСЬ ЧИСЛА: 22 → 22, Фаза 9, план 09-05 — пересчитано ОБХОДОМ после
# переезда сентинела в единый источник. Минус два места (две копии разметки),
# плюс два (две ветки одного макроса, одна из них — место ответа удаления).
# ЛЕТОПИСЬ ЧИСЛА: 22 → 21, Фаза 9, план 09-13, решение владельца `keyset` — …
```

⚠️ `FRAGMENT_ROUTES_DECLARED` (`test_htmx_markup_gates.py:879`) несёт прямое требование к
способу: число ставится **прогоном покрасневшего правила**, а не вычитанием в уме.

### Перечень изъятий с обоснованием на запись + счёт ЧИСЛОМ (форма D-08)
**Источник:** `tests/test_templates/test_htmx_markup_gates.py:2686-2796` (`DISABLED_ELT_EXCEPTIONS`
+ `DISABLED_ELT_EXCEPTIONS_DECLARED = 2`), `:2855-2882` (`MACRO_BORN_EXCEPTIONS` + `…_DECLARED = 1`)

```python
# ЛЕТОПИСЬ: 0 → 1, Фаза 9, план 09-03 (форма автосохранения редактора
# объявлений — единственное сегодняшнее место отправки вне компонентного
# макроса). Фаза 12 (FETCH-01), переводящая её на макрос-обёртку, обязана
# опустить число до нуля.
MACRO_BORN_EXCEPTIONS_DECLARED = 1
```

Два свойства формы, обязательные для изъятия D-08: обоснование **называет фазу-снимателя**
и **называет условие снятия** («изъятие снимается только вместе с курсором»).

### Счётчик прогресса вехи
**Источник:** `tests/test_pages/test_htmx_gates.py:199` (`NOT_YET_CONVERTED`), `:283`

```python
# ⚠️ ЭТО УБЫВАЮЩЕЕ ЧИСЛО, А НЕ СПИСОК НАРУШЕНИЙ. Оно есть машинный счётчик
# прогресса вехи: каждая следующая фаза снимает отсюда обработчики и опускает
# `NOT_YET_CONVERTED_COUNT`. Тестов на него ДВА, и у каждого движения свой текст
# отказа — один текст на два разных события лгал бы в одном из них.
NOT_YET_CONVERTED: frozenset[str] = frozenset(
    {
        "app/pages/accounts.py::accounts_connect_tg_user_start_qr",
        ...
```

Ключи — `путь/файл.py::имя_функции`. Снимаются восемь; летопись обязана назвать
восемь обработчиков **СЛОВАМИ, а не ключами перечня** (`<specifics>`), иначе грепом
снятие зеленеет на собственном комментарии.

### Два счёта РАЗНЫХ множеств (прямое основание D-18)
**Источник:** `tests/test_templates/test_components.py:912-914` и `:1158`

```python
MODAL_IMPORTERS = 11
MODAL_EVENT_NAMES = 9
MODAL_PLACES = 18
```

```python
# MODAL_IMPORTERS (это ЦЕЛОЕ ЧИСЛО файлов со строкой "components/modal.html",
# включая сам компонент) здесь МНОЖЕСТВО ИМЁН, поэтому напрямую сравнивать их
# нельзя — отношение между двумя счётами утверждается ниже.
MODAL_CONSUMERS = frozenset({...})   # 10 записей
```

Каждая запись `MODAL_CONSUMERS` сопровождается комментарием «N-й вход добавлен планом XX-YY»
с обоснованием размещения. Новый счёт «отдаёт фрагмент» (D-18) пишется по этой же форме.

### Исполняющее покрытие `x-data` (образец для D-10/D-11/D-12)
**Источник:** `tests/test_templates/test_components.py:1563-1650`

```python
def _run_modal_lifecycle(expression: str, scenario: str) -> dict:
    payload = json.dumps(
        {"expression": expression, "scenario": scenario, "lock": SCROLL_LOCK_CLASS}
    )
    assert MODAL_LIFECYCLE_HARNESS.count("__PAYLOAD__") == 1, (...)
    return run_node_script(MODAL_LIFECYCLE_HARNESS.replace("__PAYLOAD__", payload))
```

Оснастка уже есть: `tests.conftest.run_node_script` — единственный запуск на проект,
`MODAL_LIFECYCLE_HARNESS` со стаб-документом, `_modal_xdata_expression(_modal_block())`
достаёт объект прямо из шаблона. Новая ветвь `hide()` и приземление фокуса покрываются
добавлением **сценария** в гарнир, без новой оснастки.

Обязательная структура правил (уже стоит на `scroll-lock`): несущее правило +
положительный контроль (`test_the_panel_raises_the_scroll_lock_when_it_opens`) +
проверка собственного состояния (`test_the_teardown_of_a_closed_panel_keeps_an_open_sibling_locked`) +
отрицательный контроль (`test_control_negative_…`) + идемпотентность (`repeat_matches`).
⚠️ `pytest.skip` при отсутствии интерпретатора ЗАПРЕЩЁН (WARN-4).

### Пара `htmx_client` (GATE-01, восемь маршрутов — восемь пар)
**Источник:** `tests/conftest.py:70-90`

```python
@pytest.fixture
async def htmx_client(client):
    """Клиент, приходящий ТАК ЖЕ, как приходит браузер с включённым JavaScript.
    ⚠️ ФИКСТУРА ВОЗВРАЩАЕТ ТОТ ЖЕ ОБЪЕКТ КЛИЕНТА, ЧТО И `client`, И ЭТО
    НЕСУЩЕЕ СВОЙСТВО, А НЕ ЭКОНОМИЯ. Благодаря ему она СКЛАДЫВАЕТСЯ с
    `authed_client` / `expired_client` / `admin_client` их совместным запросом
    """
```

Форма пары: без заголовка → 302 и `Location`; с заголовком → 204,
`response.headers["HX-Location"]` и `assert "<!DOCTYPE" not in response.text`.
Для `admin_impersonate` пара ТРОЙНАЯ (`<specifics>`): 302 + cookie / 204 + заголовок + cookie.

### Гард наследования панели
**Источник:** `tests/test_templates/test_components.py:1192` (`test_modal_guard_is_inherited_by_every_consumer`),
`:1243` (`test_modal_site_inventory`)

```python
PANEL_MARKUP_MARKERS = ("modal__form", "modal__actions", "modal__panel")
```

`test_modal_site_inventory` сходится ТРЕМЯ счётами: импортёры (файлы со строкой
`components/modal.html`), имена события, прямой счёт вхождений имени события по всем
шаблонам КРОМЕ самого компонента. Компонент исключён: два его вхождения — слушатель
макроса и пример из шапки. Именно поэтому
`app/templates/accounts/partials/sync_status_card.html` (диспетчеризация без импорта)
не ломает счёт. Оба правила при снятии `hx_post` **не должны двинуться** — это и есть
проверка того, что D-14 не тронул инвентарь.

---

## No Analog Found

| Файл | Роль | Поток | Причина |
|---|---|---|---|
| гейт сличения свойств качества `modal.html` ↔ `form_wrapper.html` (D-16) | test | markup-compare | В проекте нет ни одного правила, сличающего НАБОРЫ атрибутов двух макросов между собой. Ближайшее по духу — счёт числом (`HX_POST_PLACES`, `test_htmx_markup_gates.py:132`) и разборщик `_macro_callers` (`:2800+`), но сама операция сличения заводится впервые. Форма — за планировщиком (Claude's Discretion). |

---

## Что измерено попутно и меняет вход планировщика

- **`respond()` сегодня зовут ТОЛЬКО из `app/pages/account_groups.py`.** Для восьми
  обработчиков это будет первый вызов слоя ответа в их файлах — импорт
  `from app.pages.htmx import respond` заводится в `accounts.py`, `ads.py`,
  `schedules.py`, `history.py`, `admin.py` впервые.
- **`HX-Location` в `app/` пишется ровно из одного места** — `app/pages/htmx.py:38,146`.
  Это и есть `HX_HEADER_WRITES = 2` (второе — `_notice_oob`/`refuse`); восемь маршрутов
  число НЕ двигают, что и утверждает CONTEXT.
- **`impersonation/stop` (`app/pages/auth.py:514`) сегодня отдаёт обычный
  `RedirectResponse(302)`, а не `HX-Location`.** Прецедент D-05 записан вехой (SIGN-03),
  но В КОДЕ его нет — планировщик не должен искать там образец заголовка. Образец,
  который там ЕСТЬ и нужен, — пара «`RedirectResponse` + `set_session_cookie(response, …)`»,
  то есть ровно та связка, которую D-05 обязан переселить на 204.
- **Вызовов `modal(` в шаблонах — 14 строк в 11 файлах** (`history/includes/history_card.html`
  оборачивает свой в макрос `retry_modal`, который зовут `history_card.html:229` и
  `history/detail.html:100`). Это подтверждает D-17: числу «16» не соответствует ни одно
  считаемое по файлам множество.
- **Блочных вызовов (`{% call modal(...) %}`) три:** `account_groups/includes/group_row.html:340`,
  `ads/includes/sched_card.html:267`, `admin/queue.html:143` — все три уже несут скрытые
  поля в слоте, то есть механизм D-02 отгружен трижды, а не дважды.

## Metadata

**Область поиска аналогов:** `app/templates/components/`, `app/templates/*/partials/`,
`app/templates/*/includes/`, `app/pages/`, `tests/test_templates/`, `tests/test_pages/`, `tests/conftest.py`
**Файлов прочитано целевыми выдержками:** 17
**Дата съёма выдержек:** 2026-09-02
