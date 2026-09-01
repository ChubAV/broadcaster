---
phase: 09-pilot-na-account-groups-skvoznoy-kontrakt-formy
reviewed: 2026-09-01T04:40:00Z
depth: standard
files_reviewed: 24
files_reviewed_list:
  - app/pages/account_groups.py
  - app/static/css/app.css
  - app/templates/account_groups/includes/count_rule.html
  - app/templates/account_groups/includes/group_row.html
  - app/templates/account_groups/includes/sentinel.html
  - app/templates/account_groups/list.html
  - app/templates/account_groups/partial_cards.html
  - app/templates/account_groups/partials/count_rule_oob.html
  - app/templates/account_groups/partials/delete_response.html
  - app/templates/account_groups/partials/toggle_response.html
  - app/templates/components/form_wrapper.html
  - app/templates/components/modal.html
  - app/templates/includes/htmx_error_banner.html
  - app/templates/includes/notice_area.html
  - app/templates/includes/notice_oob.html
  - tests/test_pages/test_account_groups.py
  - tests/test_pages/test_history_retry.py
  - tests/test_pages/test_htmx_gates.py
  - tests/test_pages/test_htmx_preserved.py
  - tests/test_pages/test_responsive_markup.py
  - tests/test_pages/test_shell.py
  - tests/test_templates/test_components.py
  - tests/test_templates/test_htmx_inventory.py
  - tests/test_templates/test_htmx_markup_gates.py
findings:
  critical: 2
  warning: 5
  info: 0
  total: 7
status: issues_found
---

# Фаза 09: отчёт код-ревью

**Reviewed:** 2026-09-01T04:40:00Z
**Depth:** standard
**Files Reviewed:** 24
**Status:** issues_found

## Summary

Прочитаны все 24 файла области, диапазон `e819824..HEAD` (30 коммитов, планы 09-13 … 09-16).
Ревизия велась по предмету круга закрытия: границы `keyset`-курсора, добавка
`scroll-lock`, присвоение состояния тумблера, скрытое поле строки поиска у обеих
форм удаления, перевод маршрута порции на слой ответа.

Форма курсора (`keyset`) выдерживает разбор: пустой список, последняя страница,
удалённый `after_id`, конкурентная вставка — сентинел рисуется только при
непустой выборке (`account_groups.py:227-228, 264`), `Group.id > after_id`
остаётся корректной границей и тогда, когда пограничной строки нет, а
`ge=1`-ограничение отсекает вырожденный ключ до базы. Тройной `WHERE` на месте
на всех трёх входах. Инъекций, утечек секретов и обхода авторизации не найдено.

Найдено два блокера и пять предупреждений. **Оба блокера — дефекты САМОГО
КОНТРАКТА, а не местные помарки**, то есть ровно тот класс, который Фазы 10-15
унаследуют десятикратно:

1. `scroll-lock`, введённый планом 09-13, **не снимается никогда** на
   htmx-пути удаления — панель уносится внеполосным узлом, `hide()` не
   вызывается, и `<html class="is-modal-open">` остаётся с `overflow: hidden`.
   Экран, весь смысл которого — бесконечная прокрутка, после первого же
   удаления перестаёт прокручиваться. Признак отказа МОЛЧАЛИВЫЙ: 200/204,
   чистая консоль. Добавка отгружена с НУЛЁМ покрытия.
2. Ответ тумблера перерисовывает строку с ПУСТОЙ строкой поиска в скрытом поле
   формы-триггера — то есть **своими руками отменяет починку WR-03**, которую
   план 09-15 сделал двумя коммитами раньше, на любой уже переключённой строке.

Замечания WR-02 … WR-05 и IN-01 … IN-03 прошлого круга повторно не заводились:
проверено, что предмет каждого закрыт. Известные и записанные отступления
(`NOT_YET_CONVERTED_COUNT` считает только POST, шесть литералов `limit=3*` на
соседних экранах, `overrides_applied: 0`, DEF-09-01) как новые находки не
выставляются — более серьёзного следствия ни у одного из них не обнаружено.

## Structural Findings (fallow)

Блок `<structural_findings>` вызывающим не передавался — структурного предпрохода
у этого ревью нет. Раздел оставлен пустым намеренно, чтобы нарративные находки
ниже не выдавались за структурный субстрат.

## Narrative Findings (AI reviewer)

### Critical Issues

#### CR-01: `scroll-lock` не снимается на htmx-пути удаления — экран остаётся НЕПРОКРУЧИВАЕМЫМ навсегда

**File:** `app/templates/components/modal.html:208-209`, `app/static/css/app.css:956-959`, `app/templates/account_groups/partials/delete_response.html:100`

**Issue:**
Признак поднимается ТОЛЬКО в `show()` и снимается ТОЛЬКО в `hide()`:

```js
show() { ... document.documentElement.classList.add('is-modal-open'); ... },
hide() { if (!this.open) return; ... document.documentElement.classList.remove('is-modal-open'); ... },
```

Других мест нет — проверено обходом всего дерева:
`grep -rn "is-modal-open" app/ tests/` даёт ровно две строки в `modal.html` и
одно правило в `app.css`.

На htmx-пути удаления группы панель НЕ СКРЫВАЕТСЯ, а УДАЛЯЕТСЯ из документа
внеполосным узлом `delete_response.html:100`:

```html
<div id="group-del-{{ group_id }}" hx-swap-oob="delete"></div>
```

`hide()` при этом не вызывается вовсе — **это уже записано в самом компоненте**
(`modal.html:22-30`: «панель не скрывается, а УДАЛЯЕТСЯ из документа внеполосным
узлом ответа: hide() не вызывается вовсе»). Абзац написан про потерю фокуса, а
добавка `scroll-lock` плана 09-13 повесила на тот же `hide()` ВТОРОЕ, куда более
дорогое обязательство и этот абзац не прочитала. Alpine пользовательский
`hide()` при сносе поддерева не зовёт: он вызывает только `destroy` объекта
`x-data`, а такого метода у компонента нет.

Итог: `<html>` остаётся с классом, а правило
`.is-modal-open, .is-modal-open body { overflow: hidden; }` — в силе. После
ПЕРВОГО успешного удаления группы страница не прокручивается ничем.

**Задеты ОБЕ ветки ответа удаления, а не одна:**

* ветка фрагмента (`account_groups.py:778`) — документ остаётся тот же, класс
  остаётся на нём;
* ветка перехода (`account_groups.py:708`, 204 + `HX-Location`) — **тоже**,
  потому что `HX-Location` НЕ перезагружает документ. Проверено по вендоренному
  рантайму (`app/static/js/htmx.min.js`, 2.0.10): ветка `HX-Location` кончается
  вызовом `Nn("get", e, s)`, тогда как соседние ветки того же блока —
  `HX-Redirect` → `Q.location.href=`, `HX-Refresh` → `Q.location.reload()`.
  Контраст прямой: перезагрузки в этой ветке нет, элемент `<html>` переживает
  переход вместе с классом.

**Цена именно на этом экране максимальна.** Экран построен на бесконечной
прокрутке; при `overflow: hidden` на `<html>` и `body` условие
`hx-trigger="revealed"` сентинела (`sentinel.html:74`) не срабатывает больше
никогда — остаток списка становится недостижимым. Признак отказа тот самый
молчаливый, ради поимки которого пилот и брался: статус успешный, консоль
чистая, линейка счётчика честная.

**Покрытия нет вовсе.** `grep -rn "is-modal-open\|scroll-lock" tests/` даёт одну
строку — и та КОММЕНТАРИЙ в `tests/test_pages/test_history_retry.py:1437`,
объясняющий, что добавка сломала чужой тест длиной окна. Ни разметочного, ни
поведенческого правила у добавки нет (см. WR-03).

**Наследование.** `modal.html` — общий компонент шестнадцати мест
подтверждения; Фаза 10 (FORM-06) раздаёт им `hx_post`. Дефект уедет во все
шестнадцать разом.

**Fix:** снимать признак при СНОСЕ узла, а не только при закрытии. Alpine 3.13.3
вызывает `destroy` объекта `x-data` при удалении поддерева (проверено по
`app/static/js/alpine.min.js`: `destroy&&R(e…)`), поэтому минимальная правка —
одно поле в `modal.html:204-212`:

```js
x-data="{
  open: false,
  ...
  show() { ... document.documentElement.classList.add('is-modal-open'); ... },
  hide() { if (!this.open) return; ... document.documentElement.classList.remove('is-modal-open'); ... },
  destroy() { if (this.open) { this.open = false; document.documentElement.classList.remove('is-modal-open'); } },
  ...
}"
```

Проверка `if (this.open)` обязательна: без неё снос ЛЮБОЙ закрытой панели
(например, соседней строки) снимал бы блокировку у открытой.

Правило обязано быть поведенческим, а не разметочным: разметочное зеленело бы
на наличии строки `classList.remove`, которая в `hide()` и так есть.

---

#### CR-02: ответ тумблера СТИРАЕТ строку поиска из формы удаления — починка WR-03 отменяется на любой переключённой строке

**File:** `app/pages/account_groups.py:533-542`, `app/templates/account_groups/partials/toggle_response.html:29`, `app/templates/account_groups/includes/group_row.html:53,203`

**Issue:**
`toggle_response.html:29` зовёт макрос строки без `filter_search`:

```jinja
{{ group_row(group, account_id, schedules_count, with_modal=false) }}
```

а обработчик тумблера (`account_groups.py:415-423`) поля `search` не принимает
ВОВСЕ, то есть передать его и не мог бы. Умолчание параметра — пустая строка
(`group_row.html:53`), и она печатается в скрытое поле формы-триггера
(`group_row.html:203`).

**Измерено прогоном, а не выведено чтением.** Посев: аккаунт, четыре группы,
страница запрошена с `?search=Альфа`.

Страница отдаёт (оба места удаления):

```html
<input type="hidden" name="search" value="Альфа">
<input type="hidden" name="search" value="Альфа">
```

Ответ тумблера по htmx на ту же строку отдаёт:

```html
<form method="post" action="/accounts/1/groups/3/delete"
      x-data x-on:submit.prevent="$dispatch('modal-open-group-del-3')">
    <input type="hidden" name="search" value="">
```

**Следствие — ровно тот дефект, который план 09-15 закрыл двумя коммитами
раньше** (WR-03, `c38b3cd`/`2385428`), возвращённый на любую строку, которую
человек переключил. Мир достижим и назван самой фазой поимённо — «Alpine мёртв,
htmx жив» (зеркало мира из обоснования WR-02, `account_groups.py:474-480`): при
мёртвом Alpine `x-on:submit.prevent` не навешивается, форма-триггер уходит
обычным POST-ом, и на сервер приезжает `search=""`. Дальше — оба следствия,
названные в `group_row.html:191-199` как содержание WR-03:

* `_screen_url(account_id, None)` (`account_groups.py:696`) собирает адрес БЕЗ
  фильтра — человек приземляется на неотфильтрованный список;
* `_current_listing_has_a_row` (`account_groups.py:698`) спрашивает про ВЕСЬ
  аккаунт вместо той выдачи, которую человек видел, — то есть починка WR-06 на
  этом пути сработать не может в принципе: удалив единственную найденную строку,
  человек остаётся перед ПУСТОЙ КАРТОЧКОЙ, ИЗ КОТОРОЙ НЕТ ВЫХОДА.

**Ни одно правило этого не ловит, и это проверяемо.**
`test_both_delete_forms_post_the_same_field_names` и
`test_the_trigger_form_body_lands_on_the_filtered_listing`
(`tests/test_pages/test_account_groups.py:5428-5476`) читают РАЗМЕТКУ СТРАНИЦЫ.
Ответа тумблера не читает ни одно из них: `grep -n "search" ` по тестам тумблера
не даёт ни одного вхождения. Правило равенства наборов полей объявлено «держащим»
симметрию двух форм, но третье место отрисовки той же формы — ответ тумблера — в
его предмет не входит.

**Fix:** довести строку поиска до ответа тумблера так же, как до ответа
удаления — скрытым полем формы тумблера и параметром обработчика:

```python
# app/pages/account_groups.py
async def account_groups_toggle(
    ...,
    is_active: str | None = Form(None),
    search: str | None = Form(None),
    ...
):
    term = _clean_search(search)
    ...
    html = templates.env.get_template(
        "account_groups/partials/toggle_response.html"
    ).render(..., filter_search=term or "")
```

```jinja
{# group_row.html, внутри form_wrapper тумблера #}
<input type="hidden" name="search" value="{{ filter_search }}">
```

```jinja
{# toggle_response.html #}
{{ group_row(group, account_id, schedules_count, user,
             with_modal=false, filter_search=filter_search) }}
```

и расширить `test_both_delete_forms_post_the_same_field_names` на ТРЕТЬЕ место
отрисовки строки — ответ тумблера, — иначе правило продолжит утверждать
симметрию, которой нет.

---

### Warnings

#### WR-01: адрес приземления тумблера собирается литералом и ТЕРЯЕТ строку поиска

**File:** `app/pages/account_groups.py:466,548`

**Issue:**
Оба выхода обработчика тумблера строят адрес f-строкой:

```python
return await respond(request, redirect=f"/accounts/{account_id}/groups")
```

а не помощником `_screen_url`, который для того и заведён. Докстринг помощника
(`account_groups.py:68-74`) утверждает прямым текстом: «адрес после действия и
адрес после перезагрузки обязаны приходить из одного источника, иначе они
разъедутся молча». У тумблера они разъехались.

**Измерено прогоном:** POST без признака htmx на
`/accounts/1/groups/3/toggle` со страницы `?search=Альфа` даёт
`302 → Location: /accounts/1/groups`. Человек без htmx, выключивший группу в
отфильтрованном списке, выбрасывается на неотфильтрованный — и не узнаёт, куда
делся его поиск.

Корень тот же, что у CR-02: форма тумблера (`group_row.html:176-182`) скрытого
поля строки поиска не несёт, а обработчик его не принимает. То есть WR-03 был
закрыт для ОДНОЙ из двух форм экрана, и вторая осталась с тем же изъяном —
поимённо это нигде не записано.

**Fix:** принять `search: str | None = Form(None)` в `account_groups_toggle`,
провести его через `_clean_search`, и оба выхода перевести на
`_screen_url(account_id, term)`; форме тумблера добавить то же скрытое поле.
Обе правки — часть одного изменения с CR-02.

---

#### WR-02: комментарий строки утверждает, что обработчик ИНВЕРТИРУЕТ `is_active` — форма снята планом 09-15

**File:** `app/templates/account_groups/includes/group_row.html:151-154`

**Issue:**

```jinja
⚠️ СЕРВЕРНОЙ ЗАЩИТОЙ ЭТО НЕ ЯВЛЯЕТСЯ (PAY-02) И ЕЮ НЕ ОБЪЯВЛЯЕТСЯ.
Идемпотентность держит сам обработчик: он ИНВЕРТИРУЕТ `is_active` одной
строкой под тройным ограничением, поэтому и дошедшее второе нажатие
второй записи не создаёт.
```

Обработчик инверсии больше не делает: `account_groups.py:510` —
`group.is_active = is_active is not None`. План 09-15 переписал обоснование в
питоновском докстринге по правилу летописи фазы (`account_groups.py:491-500`:
«прежнее обоснование не вычёркивается, а называется описывающим снятую форму»),
а этот абзац не тронул — `git diff e819824..HEAD -- app/templates/account_groups/includes/group_row.html`
показывает, что строки 151-154 в круге закрытия не менялись ни на символ.

Это не стилистика. Абзац стоит ровно над вызовом `form_wrapper` с
`disabled_elt=''` и является ЗАПИСАННЫМ ОБОСНОВАНИЕМ снятия клиентской
блокировки: читатель Фазы 10, решающий тот же вопрос для сорока шести
оставшихся форм, прочтёт здесь свойство, которого у кода нет. Хуже того, довод
«инверсия не создаёт второй записи» слабее того, что даёт присвоение
(идемпотентность в полном смысле), — то есть проза занижает реальную гарантию
и одновременно называет её не тем механизмом.

**Fix:** привести абзац к той же форме летописи, что и питоновский докстринг:

```jinja
⚠️ СЕРВЕРНОЙ ЗАЩИТОЙ ЭТО НЕ ЯВЛЯЕТСЯ (PAY-02) И ЕЮ НЕ ОБЪЯВЛЯЕТСЯ.
Идемпотентность держит сам обработчик: он ПРИСВАИВАЕТ `is_active`
присланное значение одной строкой под тройным ограничением, поэтому и
дошедшее второе то же тело не создаёт записи И не двигает состояния.
До плана 09-15 здесь стояло «он ИНВЕРТИРУЕТ `is_active`» — утверждение было
верно для СВОЕЙ формы и снято вместе с ней (WR-02).
```

---

#### WR-03: добавка `scroll-lock` отгружена с нулевым покрытием

**File:** `app/static/css/app.css:947-959`, `app/templates/components/modal.html:208-209`

**Issue:**
`grep -rn "is-modal-open\|scroll-lock" tests/` возвращает РОВНО ОДНУ строку —
комментарий в `tests/test_pages/test_history_retry.py:1437`, объясняющий, что
добавка удлинила выражение Alpine и уронила чужой тест. То есть единственное,
чем суита отреагировала на новое поведение, — это ущерб, который оно нанесло
соседнему правилу.

У добавки нет ни разметочного утверждения (что признак печатается и снимается),
ни поведенческого (что после ответа удаления признака на документе не
остаётся). Именно отсутствие второго и оставило CR-01 незамеченным.

Это прямо противоречит стандарту, который тот же круг закрытия применяет к
собственным правилам — `tests/test_pages/test_account_groups.py:4155-4158`:
«Правило, у которого контроля нет, доказывает ровно ничего: красным оно не
бывало никогда, и отличить его зубы от его слепоты нечем».

**Fix:** завести поведенческое правило вместе с починкой CR-01 — оно и есть
единственный способ отличить починку от её видимости:

```python
async def test_the_scroll_lock_never_survives_a_fragment_delete(...):
    """После htmx-удаления на документе не остаётся признака блокировки прокрутки."""
    # 1. страница: признака нет
    # 2. панель снята внеполосным узлом ответа — узел `hx-swap-oob="delete"`
    #    на `#group-del-N` присутствует
    # 3. в компоненте есть путь снятия признака ПРИ СНОСЕ узла, а не только в hide()
```

Разметочная половина обязана проверять наличие ветви снятия при сносе
(`destroy`), а не вхождение строки `classList.remove` — второе зеленеет на
`hide()`, который на этом пути не вызывается.

---

#### WR-04: окно панели повтора расширено до соседней строки — два из трёх утверждений теста стали удовлетворимы чужой разметкой

**File:** `tests/test_pages/test_history_retry.py:1443-1446`

**Issue:**

```python
following = re.compile(r'id="history-retry-\d+"').search(html, start + 1)
panel = html[start : following.start() if following else len(html)]
assert 'method="post"' in panel, panel[:400]
assert f'action="/history/{log.id}/retry"' in panel, panel[:400]
assert 'type="submit"' in panel, panel[:400]
```

Граница окна теперь — СЛЕДУЮЩАЯ панель, а между панелью N и панелью N+1 в
разметке лежит строка N+1 со своей формой-триггером повтора. Утверждения
`method="post"` и `type="submit"` с этого момента удовлетворимы разметкой
СОСЕДНЕЙ строки, а не проверяемой панели: панель, потерявшая форму, оставит их
зелёными. Пинается только третье утверждение — оно несёт `log.id`.

Правка была вынужденной (прежние 2000 символов сломала добавка `scroll-lock`,
см. WR-03), но замена сместила границу НАРУЖУ панели, тогда как предмет теста —
«эта панель несёт настоящую форму». Комментарий над правкой формулирует намерение
верно («эта панель, и не соседняя»), а реализация ему не соответствует.

**Fix:** резать окно по собственной форме панели, а не по следующей панели:

```python
form_start = html.find('<form class="modal__form"', start)
assert form_start != -1, "у панели подтверждения повтора нет формы"
form_end = html.find("</form>", form_start)
panel = html[form_start:form_end]
```

Тогда все три утверждения говорят об одной и той же форме.

---

#### WR-05: инлайн-сценарий плашек отказа перерегистрирует свои обработчики на каждом переходе `HX-Location`

**File:** `app/templates/includes/htmx_error_banner.html:78-88`

**Issue:**
`allowScriptTags` в проекте остаётся умолчанием `true` — это сказано прямым
текстом в `app/templates/includes/htmx_config.html:87` и подтверждено тем, что
мета-блок конфигурации (`htmx_config.html:120-126`) его не переопределяет;
в вендоренном рантайме умолчание видно как `allowScriptTags:true`. Переход по
`HX-Location` (`app/pages/htmx.py:133-149`, ветка удаления
`account_groups.py:708`) не перезагружает документ, а забирает страницу
запросом и вклеивает её в документ — значит инлайн-сценарий этого файла
исполняется ЗАНОВО и вызывает `document.body.addEventListener` ещё раз.

Сегодня оба обработчика идемпотентны (`removeAttribute('hidden')`), поэтому
видимого отказа нет — но число слушателей на общем `document.body` растёт с
каждым переходом внутри сессии, а канал этот — общий для обеих оболочек и для
всех сорока семи форм вехи.

⚠️ Остаточная неопределённость называется прямо: накопление слушателей верно при
условии, что элемент `body` переживает подмену (умолчание htmx —
`innerHTML` по `document.body`). Если бы подменялся сам узел `body`, накопления
не было бы, но повторное исполнение сценария осталось бы. Настраивается это
одним замером в браузере — счётчиком регистраций, — и до замера утверждение
шире делать нельзя.

**Fix:** сделать регистрацию однократной по признаку на самом узле:

```html
<script>
  if (!document.body.dataset.htmxFailureWired) {
    document.body.dataset.htmxFailureWired = '1';
    document.body.addEventListener('htmx:responseError', function (event) { ... });
    document.body.addEventListener('htmx:sendError', function () { ... });
  }
</script>
```

Признак ставится на тот же узел, к которому вешаются слушатели, поэтому подмена
узла снимает и признак — регистрация происходит ровно один раз на живой `body`.

---

_Reviewed: 2026-09-01T04:40:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
