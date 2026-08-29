# Phase 9: Пилот на `account_groups` — сквозной контракт формы — Pattern Map

**Mapped:** 2026-08-29
**Files analyzed:** 13 (3 новых, 10 правимых)
**Analogs found:** 13 / 13 (аналог есть у каждого; у семи файлов аналог — они сами)

Перечень файлов НЕ выводился заново: он взят из `09-CONTEXT.md` §Integration Points и
подтверждён `09-RESEARCH.md` (§2.4, §4.4, §5.1, §5.3, Code Examples). Ниже — только
классификация, выбор аналога и **дословные выдержки**, которые планировщик кладёт в
`<read_first>` и `<action>`.

---

## File Classification

| Файл фазы | Роль | Поток данных | Ближайший аналог | Качество совпадения |
|---|---|---|---|---|
| `app/templates/components/<обёртка>.html` (**NEW**) | компонентный макрос, блочный вызов `{% call %}` | request-response (печатает `<form>`) | `app/templates/components/modal.html` (блочный макрос с `caller`), `components/toggle.html` (сигнатура) | exact |
| `app/templates/account_groups/partials/<toggle_response>.html` (**NEW**) | фрагмент ответа, плоский, OOB верхнего уровня | request-response | `app/templates/ads/includes/autosave_response.html` | exact |
| `app/templates/account_groups/partials/<delete_response>.html` (**NEW**) | фрагмент ответа, `hx-swap="none"`, всё OOB | request-response | `ads/includes/autosave_response.html` (сосед по каталогу — `account_groups/partials/sync_result.html`) | exact |
| `app/templates/account_groups/partials/<count_rule_oob>.html` (**NEW**, если счётчик выносится одним источником) | OOB-включение долгоживущей области | request-response | `app/templates/includes/notice_oob.html` | exact |
| `app/templates/account_groups/includes/group_row.html` (MODIFY) | макрос строки, 3 вызова после фазы | request-response | **сам себе** (комментарии несут WHY для D-05/D-06/D-07/D-02/D-08) | self |
| `app/templates/account_groups/list.html` (MODIFY, D-12) | побочная область `innerHTML:#id` | request-response | `app/templates/includes/notice_area.html` (идиома «узел есть всегда») | exact |
| `app/templates/components/modal.html` (MODIFY, D-01) | shared-компонент, 16 потребителей | request-response | **сам себе** (идиома умолчания-литерала `method="post"`, `{%- if body %}`) | self |
| `app/pages/account_groups.py` (MODIFY) | route handlers | request-response | `app/pages/htmx.py::respond` (контракт), `app/pages/accounts.py::_connect_status` (рендер фрагмента) | role-match |
| `app/static/css/app.css` (MODIFY) | stylesheet | — | `app.css:1696-1711` (реакция на `.htmx-request`), `app.css:712` (`.btn[disabled]`) | partial ⚠️ форму селектора копировать НЕЛЬЗЯ, см. ниже |
| `app/templates/includes/htmx_error_banner.html:75` (MODIFY, D-16) | отгруженный артефакт Фазы 8 | — | **сам себе** | self |
| `tests/test_pages/test_account_groups.py` (MODIFY) | route spec | `tests/conftest.py:65-102` (`htmx_client`) + пара D-16 Фазы 8 | exact |
| `tests/test_templates/test_htmx_markup_gates.py` (MODIFY) | инвентарный гейт | **сам себе** + `tests/test_pages/test_impersonation_gate.py` (перечень с числом) | exact |
| `tests/test_pages/test_htmx_gates.py` (MODIFY) | инвентарный гейт | **сам себе** (`:235`, `:688`, `:709`) | self |
| `tests/test_templates/test_components.py` (MODIFY) | component gate | **сам себе** (`COMPONENT_CALLS`, `:576-596`) | self |

---

## Shared Patterns (сквозные — применять во ВСЕХ соответствующих планах)

### SP-1. Идиома «перечень исключений с обоснованием + отдельное утверждение ЧИСЛА»

**Встречается в фазе ЧЕТЫРЕ раза:** пара G-11 (`ID_IN_TWO_ROLES_BY_DESIGN`), исключения
`hx-disabled-elt` (D-06), исключения «рождён макросом» (D-03), места определения
компонентных макросов (`MACRO_DEFINITION_SITES`, RESEARCH §2.5β). Форма одна и та же —
берётся отсюда, **не изобретается заново на каждом сайте**.

**Источник:** `tests/test_pages/test_impersonation_gate.py`

Форма записи — словарь `ключ → причина`, с шапкой-комментарием, объясняющей, почему
перечень выписан руками (`:170-182`):

```python
# которого D-23 отказывается: новый маршрут попал бы сюда молча. Здесь у каждого
# элемента написано, ПОЧЕМУ он разрешён, и добавление нового требует написать
# причину — то есть принять решение.
ALLOWED_ROUTES = {
    "app/pages/auth.py::stop_impersonation": (
        "ВОЗВРАТ из-под чужой личности — единственный путь назад; закрыть его "
        "значило бы запереть администратора в чужой учётной записи навсегда"
    ),
    "app/pages/account_groups.py::account_groups_toggle": "ВКЛЮЧЕНИЕ/ВЫКЛЮЧЕНИЕ группы — разрешено поимённо (D-22)",
}
```

Число — **отдельной константой с собственным комментарием** (`:89-97`):

```python
# ⚠️ ЧИСЛО ИЗМЕНЯЮЩИХ МАРШРУТОВ ВЫПИСАНО ОТДЕЛЬНЫМ УТВЕРЖДЕНИЕМ НАМЕРЕННО. Оно
# будет меняться, и каждое его изменение обязано быть ОСОЗНАННЫМ: беззвучно
# выросшее число означает, что маршрут появился, а решения о нём никто не
# принимал. Перечни ниже поймали бы это и сами, но по числу видно СРАЗУ, что
# именно произошло.
MUTATING_ROUTE_COUNT = 49
```

Три обязательных теста (третий — несущий, RESEARCH §1.3):

1. **Обоснование непусто** — `test_every_allowed_route_carries_a_reason` (`:715-729`):

```python
def test_every_allowed_route_carries_a_reason():
    """У каждого разрешённого маршрута написана ПРИЧИНА, а не пустая строка.

    Перечень, у которого не написано, почему кто-то в него входит, через фазу
    превращается в «наверное, забыли», и следующая фаза читает его как список
    без основания.
    """
    unexplained = {
        key for key, reason in ALLOWED_ROUTES.items() if not reason.strip()
    }
    assert not unexplained, (
        "разрешённый маршрут не снабжён причиной:\n  "
        + "\n  ".join(sorted(unexplained))
    )
```

2. **Число утверждается отдельно** — `test_the_number_of_mutating_routes_is_the_declared_one` (`:589-608`):

```python
    assert len(routes) == MUTATING_ROUTE_COUNT, (
        f"изменяющих маршрутов стало {len(routes)}, а выписано "
        f"{MUTATING_ROUTE_COUNT}: маршрут появился или исчез — обнови число "
        f"вместе с решением о нём"
    )
```

3. **Каждая запись перечня ФАКТИЧЕСКИ находится в конфликте** — форма
   `test_the_three_sets_do_not_overlap` (`:687-711`): перечень не имеет права содержать
   устаревшую запись, которая молча погасит будущее настоящее нарушение.

```python
    assert not (forbidden & allowed), (
        f"маршрут объявлен и запрещённым, и разрешённым: {forbidden & allowed}"
    )
```

**Что новые четыре сайта копируют структурно:** словарь `str → str`, шапка «почему
перечень, а не автоматический вывод», отдельная константа числа с ⚠️-комментарием, три
теста. **Что легитимно отличается:** ключ — не маршрут, а идентификатор / путь шаблона;
третье утверждение формулируется как «запись лежит в пересечении `_swap_target_ids &
_oob_target_ids`» / «файл лежит в `components/` и внутри `{% macro %}`»
(`test_every_macro_definition_site_is_a_component`, RESEARCH §2.5).

---

### SP-2. Контроль зубов правила («ГРУППА КОНТРОЛЯ»)

**Каждое новое правило гейта обязано иметь контроль, иначе оно зелено по построению.**

**Источник:** `tests/test_templates/test_htmx_markup_gates.py:1383-1434` — шапка раздела и
`_tree_with`:

```python
# --- ГРУППА КОНТРОЛЯ ---------------------------------------------------------
#
# Зубы гейта ДОКАЗЫВАЮТСЯ, а не заявляются. Каждый случай ниже подаёт обходу
# изменённую копию дерева шаблонов во временном каталоге и требует, чтобы
# правило на ней покраснело. Настоящее дерево при этом не трогается ни одним
# байтом: подстановки применяются к прочитанным исходникам, а пишется копия.
#
# ⚠️ ПОДСТАНОВКА ОБЯЗАНА ДОКАЗАТЬ, ЧТО ОНА ЧТО-ТО ИЗМЕНИЛА, И ЧТО ИЗМЕНИЛА
# ИМЕННО ТО. Контроль, чей образец в шаблоне не нашёлся, «проходит» на
# нетронутом дереве и утверждает ровно ничего — то есть притворяется
# доказательством зубов, не будучи им.


class Substitution(NamedTuple):
    template: str
    old: str
    new: str
```

Готовый образец контроля (`:1554-1566`) — форма для новых:

```python
def test_control_negative_one_id_in_two_roles_reddens_the_gate(tmp_path: Path) -> None:
    """Один идентификатор объявлен и целью подмены, и внеполосной целью."""
    root = _tree_with(
        tmp_path,
        Substitution(
            FORM, FORM_CLOSE, 'hx-swap="none"\n          hx-target="#ad-preview">'
        ),
    )
    assert _offenders_id_in_two_roles(_all_templates(root)), (
        "идентификатор оказался в двух ролях сразу, и G-11 этого не заметил — "
        "узел подменялся бы дважды за один ответ"
    )
```

**Копируется:** имя `test_control_negative_<что>_reddens_the_gate`, `tmp_path`,
`_tree_with(...Substitution...)`, `assert _offenders_...(_all_templates(root))` с текстом
отказа, называющим ПОСЛЕДСТВИЕ. **Отличается:** новые правила D-08 (голый `x-data` внутри
свапаемого шаблона), «рождён макросом», `hx-disabled-elt`, индикатор — каждому свой
`Substitution`. RESEARCH §1.3: правку существующего контроля `:1554` фаза **не требует** —
он подставляет `#ad-preview`, которого нет в перечне исключений.

---

### SP-3. Парный тест `htmx_client` (D-16 Фазы 8)

**Источник:** `tests/conftest.py:65-102`

```python
@pytest_asyncio.fixture
async def htmx_client(client):
    ...
    ⚠️ `follow_redirects=True` ЗДЕСЬ — ЧАСТЬ ПРЕДМЕТА ПРОВЕРКИ (умолчание
    проекта — `False`). ... поэтому тест, ожидающий 204 с заголовком перехода,
    не может случайно позеленеть на редиректе: редирект придёт к нему кодом 200
    и телом чужой страницы.
    """
    client.headers["HX-Request"] = "true"
    client.follow_redirects = True
    return client
```

Форма пары — RESEARCH §Canonical paired-test form; несущая половина второй половины —
`assert "<!DOCTYPE" not in response.text`; первая половина обязана звать
`follow_redirects=False` явно.

---

### SP-4. Комментарий объясняет ПОЧЕМУ, и называет ЦЕНУ обеих границ

Плотность задана `components/modal.html:1-79` (79 строк докстринга на 30 строк разметки) и
`account_groups/includes/group_row.html:54-71`. Образец «называю цену обеих границ» —
`includes/notice_area.html:14-23`. Новый макрос-обёртка, класс индикатора в `app.css`
(порог 300 мс) и каждая запись перечней SP-1 обязаны держать эту плотность.

---

## Pattern Assignments

### 1. `app/templates/components/<обёртка>.html` — **NEW** (компонентный макрос, `{% call %}`)

**Аналог:** `app/templates/components/modal.html` (единственный блочный макрос проекта),
`components/toggle.html` (короткая сигнатура + докстринг «Импорт:»).

**Шапка и строка импорта** (`toggle.html:1-6` — минимальная годная форма):

```jinja
{# Тумблер по knob-паттерну макета (D-13, D-14).
   Настоящий checkbox внутри label: состояние читается формой и скринридером,
   а не имитируется атрибутом.
   Импорт: {% from "components/toggle.html" import toggle %} #}

{% macro toggle(name, checked=false, label=None, value='1', disabled=false, id=None, title=None) -%}
```

**Совместимость с блочным и не-блочным вызовом** (`modal.html:113-114`) — **обязательна**,
иначе `test_macros_take_no_context` упадёт на прямом вызове:

```jinja
      {%- if body %}<p class="modal__text">{{ body }}</p>{% endif %}
      {%- if caller is defined %}{{ caller() }}{% endif %}
```

**Умолчание-литерал в двойных кавычках** (`modal.html:81-83` + `:92`) — приём, спасающий
G-3 (RESEARCH §2.5 γ1):

```jinja
{# Значения по умолчанию записаны двойными кавычками намеренно: метод формы
   должен быть виден в файле дословно как method="post" — модалка не имеет
   права незаметно съехать на GET. #}
{% macro modal(id, title, action, confirm_label, body=None, cancel_label="Отмена", confirm_variant="danger", method="post") -%}
```

**Что копируется структурно:** файл в `components/`, начинается с `{#`, содержит
`{% macro `, без `with context`, без `|safe`/`Markup(`, ветка `caller is defined`,
докстринг с «Импорт:».
**Что легитимно отличается:** макрос печатает `<form>` сам (GATE-07 не даёт вернуть строку
атрибутов), `method="post"` — литерал, `action` и `hx-post` печатают **одно и то же
выражение `{{ action }}`** (G-4 сравнивает сырые строки), селекторы `hx-disabled-elt` /
`hx-indicator` обязаны нести префикс `find ` (RESEARCH §5.2). Скелет — RESEARCH §5.1.

**Регистрация в гейте компонентов** (`tests/test_templates/test_components.py:576-596`) —
новый макрос **не попадёт в перечень сам**:

```python
COMPONENT_CALLS = [
    ("components/toggle.html", "toggle", (), {"name": "x"}),
    ("components/modal.html", "modal", (), MODAL_ARGS),
]
```

Рамка, под которую файл попадает автоматически (`:613-623`):

```python
def test_components_are_documented_macros():
    files = sorted((TEMPLATES_DIR / "components").glob("*.html"))
    assert len(files) >= 11
    for path in files:
        body = path.read_text(encoding="utf-8")
        assert body.lstrip().startswith("{#"), path.name
        assert "{% macro " in body, path.name
```

---

### 2. `account_groups/partials/<toggle_response>.html` — **NEW** (фрагмент + OOB)

**Аналог:** `app/templates/ads/includes/autosave_response.html` (единственный шипнутый
шаблон ответа с OOB).

**Шапка, перечисляющая цели поимённо, и плоское тело** (`autosave_response.html:1-21, 34`):

```jinja
{# Ответ автосохранения (D-06): ОДИН запрос обновляет предпросмотр, сводку и
   индикатор состояния.

   Основного места подмены у этого ответа НЕТ: форма несёт `hx-swap="none"`,
   ... Всё приезжает внеполосно, по трём идентификаторам:

     id="ad-preview"         — рамка предпросмотра;
     ...
   Ответ НЕ содержит формы объявления — это и есть проверяемое свойство
   (tests/test_pages/test_ads_editor.py). #}
<div id="ad-preview" hx-swap-oob="true">{% include "ads/includes/preview.html" %}</div>
<div id="ad-summary" hx-swap-oob="true">{% include "ads/includes/summary.html" %}</div>
{% set oob = true %}{% include "ads/includes/autosave.html" %}
<input type="hidden" id="ad-id-field" name="ad_id" value="{{ ad.id if ad else '' }}" hx-swap-oob="true">
```

**Копируется:** шапка, называющая цели по `id` и проверяемое свойство ответа; узлы —
**прямые дети файла, без общей обёртки** (`allowNestedOobSwaps: false`, RESEARCH §4.4(2));
третий вызов того же макроса вместо второй копии разметки (`list.html:188`,
`partial_cards.html:12` — уже два вызова).
**Отличается:** `hx-swap-oob="true"` (подмена узла) допустима только для собственных узлов
фрагмента; **долгоживущая область счётчика идёт `innerHTML:#…`** (D-12, см. §4);
`group_row(..., with_modal=false)` — иначе `outerHTML` принесёт вторую панель
(RESEARCH §4.4(1), Pitfall 1).

**Признак OOB, собранный веткой шаблонизатора** — прецедент, что обход это умеет
(`ads/includes/autosave.html:20-28`):

```jinja
   Элемент несёт признак внеполосной подмены сам (`hx-swap-oob`, когда вызывающий
   шаблон выставил `oob`), а не через обёртку: aria-live обязан жить на самом
   озвучиваемом элементе.
<span id="autosave-indicator" class="autosave{% if failed %} autosave--error{% endif %}"
      aria-live="polite" role="status"{% if oob is defined and oob %} hx-swap-oob="true"{% endif %}>
```

⚠️ Pitfall 11: **условный блок в инвентаре ровно один** (`test_htmx_markup_gates.py:1245-1252`) —
новые OOB-узлы объявляют `hx-swap-oob` **безусловно**.

**Сосед по каталогу** `account_groups/partials/sync_result.html:18-34` — источник четырёх
инвариантов свапаемого блока; п. 3 дословно предупреждает о задвоении панели:

```jinja
   3. Блок МИНИМАЛЕН: бейдж статуса и строка выполнения, и ничего более.
      Плашка результата, панели подтверждения и список групп в него НЕ входят.
      Элемент, заменяемый целиком, приносит с каждым ответом свои дочерние
      блоки: ... вложенная панель подтверждения дала бы две панели с одинаковым
      идентификатором — событие открывало бы обе, а Tab уходил бы в невидимую
      копию (T-11-04).
   4. Разметка ответа и разметка первичной отрисовки — ОДИН файл.
```

---

### 3. `account_groups/partials/<delete_response>.html` — **NEW** (`hx-swap="none"`, всё OOB)

**Аналог:** тот же `autosave_response.html` (единственный ответ проекта без основной цели
свапа — его шапка прямо объясняет, почему цели нет).

**Копируется:** плоскость, шапка «основного места подмены НЕТ и вот почему».
**Отличается:** узлы — `hx-swap-oob="delete"` по собственному `id` (тело пустое); ответ
**одинаков** для найденной и не найденной группы (D-04). Готовая заготовка —
RESEARCH §Code Examples «Шаблон ответа удаления».

Прецедент формулировки «ответ одинаков, повтор безвреден» лежит в самом обработчике
(`app/pages/account_groups.py:374-377`) и переезжает дословно:

```python
    # Ответ ОДИНАКОВ и для найденной, и для ненайденной группы: это делает
    # повторный запрос безвредным (кнопка «назад», повторная отправка формы) и
    # не сообщает, какие идентификаторы заняты чужими группами.
```

---

### 4. Побочная область счётчика (D-12): `list.html` (MODIFY) + OOB-включение (**NEW**)

**Аналог — идиома, а не разметка:** `app/templates/includes/notice_oob.html` +
`includes/notice_area.html`. Это ЕДИНСТВЕННЫЙ шипнутый образец «постоянный узел с `id` +
подмена СОДЕРЖИМОГО», и D-12 объявлен формой на всю веху — брать надо отсюда.

**Обоснование подмены содержимого** (`notice_oob.html:10-15`) — абзац переносится по
смыслу в комментарий обёртки счётчика:

```jinja
   ⚠️ ПОДМЕНЯЕТСЯ СОДЕРЖИМОЕ ОБЛАСТИ, А НЕ ЕЁ УЗЕЛ, И РАЗНИЦА НЕ
   КОСМЕТИЧЕСКАЯ (T-08-21). Подмена узла УНОСИТ область из документа и ставит
   на её место присланный узел. Область уведомления живёт в шелле и обязана
   пережить любое число ответов: унесённая один раз, она лишает цели ВСЕ
   последующие — и молча, потому что о ненайденной цели свопа браузер не
   сообщает ничем.
```

**Сама форма OOB-узла** (`notice_oob.html:43-47`) — узел верхнего уровня, селектор
`innerHTML:#id`:

```jinja
{% if notice.variant == 'error' -%}
<div hx-swap-oob="innerHTML:#notice-alert">{{ alert(notice.text, notice.variant) }}</div>
{%- else -%}
<div hx-swap-oob="innerHTML:#notice">{{ alert(notice.text, notice.variant) }}</div>
{%- endif %}
```

**«Узел существует ВСЕГДА, даже пустой»** (`notice_area.html:40-48`) — ровно то, что
D-12 требует от `.count-rule`, и абзац, объясняющий, почему пустой `div` нельзя снести:

```jinja
   ⚠️ УЗЕЛ ОБЛАСТИ СУЩЕСТВУЕТ ВСЕГДА, ДАЖЕ ПУСТОЙ, И ЭТО ПРАВИЛУ ВЫШЕ НЕ
   ПРОТИВОРЕЧИТ. Правило относится к ПЛАШКЕ, а не к области. Внеполосная
   подмена (includes/notice_oob.html) целится в область ПО ИДЕНТИФИКАТОРУ, и
   узла, которого нет в документе, она не найдёт: ответ приедет, содержимое
   подменять будет нечего, и молчать об этом браузер будет так же, как молчит о
   ненайденной цели любого другого свопа. Поэтому узел стабилен, а плашек в нём
   при отсутствии кода нет ни одной. Абзац написан затем, чтобы следующий
   читатель, увидев пустой div в отрендеренном документе, не снял его как мусор
   и не сломал этим свою же подмену.
```

**Место правки — `app/templates/account_groups/list.html:161-175`** (сегодня линейка
условна и при нуле групп не рендерится вовсе):

```jinja
{#- Линейка-разделитель над списком. Числа приходят ДВУМЯ выделенными запросами
    подсчёта (D-04) и не зависят от того, сколько строк успело загрузиться.
    При нуле групп линейка не рендерится вовсе: «0 активных из 0 групп» — это
    не сообщение, сообщение несёт пустое состояние (UI-SPEC E3 empty).
    ... -#}
{% if total_groups %}
<div class="count-rule">
  {{ mono(active_groups ~ ' ' ~ plural_ru(active_groups, 'активная', 'активные', 'активных') ~
          ' из ' ~ total_groups ~ ' ' ~ plural_ru(total_groups, 'группы', 'групп', 'групп')) }}
  <span class="count-rule__line" aria-hidden="true"></span>
  {{ mono('ВЫКЛЮЧЕННЫЕ ГРУППЫ ПРОПУСКАЮТСЯ ПРИ РАССЫЛКЕ', upper=true) }}
</div>
{% endif %}
```

**Копируется:** внешний `<div id=…>` безусловен, внутренность остаётся под `{% if
total_groups %}` — заготовка в RESEARCH §Code Examples «Постоянная обёртка счётчика».
**Отличается:** тексты линейки переносятся **дословно** (CONTEXT §Specific Ideas).
⚠️ Pitfall 10: правка не имеет права расщепить сентинел — обёртка `hx-get` не несёт
(`list.html:189` — сентинел; `test_sentinel_markup_is_identical_in_both_templates`).
⚠️ `.count-rule` — flex с `margin: 0 0 12px` (`app.css:2182-2185`); лишний блочный уровень
проверяется UI-ревью.

---

### 5. `account_groups/includes/group_row.html` (MODIFY) — аналог самому себе

**Читать целиком (110 строк).** Комментарии — единственный носитель WHY для D-05/D-06/D-07.

**Форма тумблера сегодня** (`:54-77`) — правится D-05 (снятие `x-on:change`), D-07 (условие
`window.htmx`), заворачивается в `{% call form_wrapper(...) %}`:

```jinja
  {#- Событие change всплывает от чекбокса к форме, поэтому обработчик висит на
      САМОЙ форме, а макрос toggle остаётся без собственных атрибутов событий.
      ...
      Но перехвата на форме для базового пути НЕДОСТАТОЧНО. Внутри формы —
      единственный элемент, чекбокс; кнопки отправки нет, а неявная отправка по
      Enter спецификацией для формы без submit-кнопки ... не предусмотрена.
      ...
      `<noscript>` тут не годится: он спасает от выключенного JS, но не от
      единственного реального сценария — JS включён, а Alpine не загрузился. -#}
  <form method="post" action="/accounts/{{ account_id }}/groups/{{ group.id }}/toggle"
        x-data x-on:change="$el.submit()">
    {{- toggle(name='is_active', checked=group.is_active, id='group-toggle-' ~ group.id,
               title='Отключить' if group.is_active else 'Включить') -}}
    <span x-init="$el.remove()">{{- button('Применить', variant='ghost') -}}</span>
  </form>
```

⚠️ Абзац «кнопки отправки нет» — **дословное основание записи D-06** в перечне исключений
`hx-disabled-elt`. Обоснование обязано дополнительно назвать цену (RESEARCH §4.3: фокус
после свапа уходит на `<body>`).

**Форма-триггер удаления** (`:78-88`) — **НЕ трогается** (D-03), она же единственное, что
удерживает G-4 зелёным (Pitfall 8):

```jinja
  <form method="post" action="/accounts/{{ account_id }}/groups/{{ group.id }}/delete"
        x-data x-on:submit.prevent="$dispatch('modal-open-group-del-{{ group.id }}')">
    {{- button('Удалить', variant='ghost', icon='trash', title='Удалить группу') -}}
  </form>
```

**Панель СНАРУЖИ строки** (`:89-109`) — граница, которую фаза не двигает; основание D-02 и D-08:

```jinja
</div>
{#- Панель подтверждения стоит РЯДОМ со строкой, а не внутри неё: панель
    позиционируется фиксированно, а внутри строки-карточки стала бы её колонкой.
    Панель обязана лежать и вне любого элемента, заменяемого подменой, — иначе
    после первой же подмены их станет две с одним идентификатором (T-11-04).
    ...
    method="post" передан явно, хотя совпадает с умолчанием макроса: маршрут и
    метод удаления — контракт с обработчиком, и он обязан читаться грепом по
    этому файлу, а не только по отрендеренной странице. -#}
{{ modal(id='group-del-' ~ group.id,
         title='Удалить группу?',
         action='/accounts/' ~ account_id ~ '/groups/' ~ group.id ~ '/delete',
         confirm_label='Удалить',
         method="post",
         body=group.name ~ ' — группа исчезнет из всех расписаний; следующая синхронизация вернёт её как новую') }}
```

**Сигнатура макроса** (`:31`) — точка добавления `with_modal=true` (RESEARCH §4.4(1)):

```jinja
{% macro group_row(group, account_id, schedules_count=0, user=None) -%}
<div data-group-row id="group-row-{{ group.id }}"{% if not group.is_active %} class="group-row--off"{% endif %}>
```

Докстринг макроса (`:7-12`) объясняет, почему параметры явные и чем ловится опечатка —
образец для комментария нового параметра:

```jinja
   Это МАКРОС: импортированные шаблоны Jinja контекста вызывающего не получают,
   поэтому `group`, `account_id`, `schedules_count` и `user` — явные параметры.
   Ошибка в имени параметра проявится не исключением, а ПУСТОЙ строкой при
   валидной странице (200), поэтому отрисовка реальных данных закреплена
   тестами ...
```

**Тексты подписей** (`:38-52`) — переносятся во фрагмент **дословно** (CONTEXT §Specifics):
`'в ' ~ schedules_count ~ …`, `'не в расписаниях'`, `'не найдена при синке'`.

---

### 6. `app/templates/components/modal.html` (MODIFY, D-01) — аналог самому себе

**Точка правки — `:111-112`** (форма панели, сегодня без htmx-атрибутов):

```jinja
    <form class="modal__form" method="{{ method }}" action="{{ action }}"
          x-on:submit="if (sending) { $event.preventDefault(); return; } sending = true">
```

**Идиома опционального параметра с сохранённым умолчанием** — уже есть в этом же файле
(`:113`): `{%- if body %}<p class="modal__text">{{ body }}</p>{% endif %}` — при
`body=None` разметка не меняется ни на символ. Новые параметры D-01 копируют ровно эту
форму (**умолчание = сегодняшняя разметка**), сигнатура пополняется в `:92`.

**Докстринг** (`:54-64`) снимает половину работы D-14 — новой CSS для видимости
блокировки не нужно:

```jinja
   Защита от повторной отправки (E6 loading). ... Видимость состояния обеспечивает
   уже отгруженное правило `.btn[disabled]` (app/static/css/app.css) — новой CSS и
   новых классов контракт не требует. Кнопка ОТКАЗА не блокируется ничем: отмена
   разрушительного действия не имеет права быть труднее его подтверждения.
```

⚠️ RESEARCH §2.2/Pitfall 6: правка роняет **четыре** правила гейта разом
(G-3 `method="{{ method }}"`, извлекаемость адреса, существование маршрута, `len(paths)==2`).
Разрешение — SP-1 (`MACRO_DEFINITION_SITES`) + γ1 для метода. Планировать вместе с гейтом,
не отдельным коммитом.

---

### 7. `app/pages/account_groups.py` (MODIFY) — оба обработчика на `respond()`

**Аналог контракта:** `app/pages/htmx.py::respond` (`:305-311` — сигнатура, `:352-359` — ветвление):

```python
async def respond(
    request: Request,
    *,
    redirect: str,
    notice: str | None = None,
    fragment: Callable[[], Awaitable[Response]] | None = None,
) -> Response:
```

```python
    if not is_htmx(request):
        return RedirectResponse(url=_with_notice(redirect, notice), status_code=302)

    if fragment is None:
        return location_response(_with_notice(redirect, notice))
```

Ветка `fragment is None` — готовый механизм D-09 и D-13, писать нечего.

**Аналог рендера фрагмента:** `app/pages/accounts.py:47-50` (шипнутая форма «маршрут
возвращает фрагмент»):

```python
def _connect_status(macro: str, *args) -> HTMLResponse:
    """Рендерит макрос ответа опроса подключения через окружение Jinja2."""
    module = templates.env.get_template(_CONNECT_STATUS).module
    return HTMLResponse(str(getattr(module, macro)(*args)))
```

Вариант того же приёма для шаблона-файла уже есть в правимом модуле
(`account_groups.py:294-296`) — **предпочесть его, он в том же файле**:

```python
    html = templates.env.get_template(
        "account_groups/partials/sync_result.html"
    ).render(account_id=account_id, status=account.status)
    return HTMLResponse(html)
```

**Что сохраняется дословно** в обоих обработчиках — тройной `WHERE` и его комментарий
(`:311-322`), инверсия вместо установки (`:325-328`), комментарий D-05 (`:330-332`),
`ScheduleRepository(...).remove_group_ids` (`:366-371`):

```python
    # ТРОЙНОЙ WHERE. Проверка владельца одна не закрывает вход: свою группу
    # можно адресовать через свой ЖЕ, но другой аккаунт, и связка «группа
    # принадлежит именно этому аккаунту» перестала бы удерживаться (T-03-02).
    result = await db.execute(
        select(Group).where(
            Group.id == group_id,
            Group.user_id == user.id,
            Group.account_id == account_id,
        )
    )
```

**Что обязано измениться:** ⚠️ Pitfall 7 / RESEARCH §5.7 — `RedirectResponse(url="/login")`
(`:309`, `:347`) и финальные `RedirectResponse(...)` (`:332`, `:377`) обязаны уйти из
**обоих** обработчиков целиком: `_builds_own_redirect` смотрит на всё тело функции.
Замена — `return await respond(request, redirect="/login")`.

**Переиспользование счётчиков** (`_schedule_counts`, `:78-107`; два выделенных `COUNT`,
`:130-161`) — «Don't Hand-Roll»: второй экземпляр правила владения разъедется с первым.

---

### 8. `app/static/css/app.css` (MODIFY) — класс индикатора

**Аналог по ИДЕЕ, но НЕ по форме селектора:** `app.css:1696-1711`.

```css
/* Индикатор автосохранения ------------------------------------------------- */
/* Состояние «идёт запрос» выражено классом, который htmx вешает на инициатора
   запроса САМ (.htmx-request на форме объявления): собственного таймера и
   собственного состояния в JavaScript нет (D-05), рассинхрон невозможен. */
.autosave { ... }
.autosave--busy, #ad-form.htmx-request .autosave { color: var(--text-secondary); }
.autosave__busy, .autosave__error { display: none; }
#ad-form.htmx-request .autosave__idle { display: none; }
#ad-form.htmx-request .autosave__busy { display: inline; }
```

**Копируется:** заголовок раздела с чертой, комментарий-обоснование над правилом, идея
«CSS реагирует на класс, который вешает рантайм».
**⚠️ НЕ копируется (Pitfall 3, 4; RESEARCH §5.2-5.3):**
- селектор обязан быть **составным** (`.<класс>.htmx-request`), а не потомковым — `tn()`
  вешает класс на сам узел индикатора, найденный `hx-indicator`;
- имя класса **не** `htmx-indicator` — рантайм дописывает свой стиль после `app.css`;
- переключается **`opacity` + `visibility`**, а не `display` (`display` без
  `allow-discrete` задержку игнорирует), и `transition-delay` вешается на состояние
  «запрос идёт», а не на покой;
- порог 300 мс записывается **с комментарием, называющим цену обеих границ** (мигание на
  150 мс против «кнопка не сработала» на 500 мс) — CONTEXT §Specifics. Готовый текст
  комментария — RESEARCH §5.3.

**Второй прецедент, снимающий работу** (`app.css:712`) — новой CSS для блокировки не нужно:

```css
.btn[disabled] { opacity: .45; cursor: not-allowed; }
```

---

### 9. `app/templates/includes/htmx_error_banner.html:75` (MODIFY, D-16) — одна строка

**Аналог — сам файл.** Текущая строка 75:

```jinja
<div id="htmx-failure-network" hidden>{{ alert('Запрос не дошёл до сервера. Проверьте соединение и попробуйте ещё раз.', 'error') }}</div>
```

**Правится ТОЛЬКО текст**: дополнение обязано говорить о расхождении экрана с сервером и
**не повторять** «попробуйте ещё раз» (CONTEXT §Specifics). Соседняя строка 74 и `<script>`
(`:76-86`) не трогаются: третий встроенный обработчик покрасил бы
`test_only_known_non_dialog_submit_handlers_remain`.

---

### 10. `tests/test_pages/test_account_groups.py` (MODIFY) — аналог самому себе + SP-3

**Помощники, уже написанные и переиспользуемые** (`:40-71`):

```python
GROUP_ROW_RE = re.compile(r'id="group-row-(\d+)"')
SENTINEL_RE = re.compile(r'hx-get="([^"]*/groups/partial\?[^"]*)"')

def _row_html(html: str, group_id: int) -> str:
    """Разметка ОДНОЙ строки списка целиком, от её `<div` до парного `</div>`.

    Нужна для утверждения «панель подтверждения лежит ВНЕ строки»: подстрочный
    поиск по всей странице такого различить не может — идентификатор панели
    есть на странице в обоих случаях.
    """
```

⚠️ `_row_html` — **прецедент счётчика глубины по отрендеренному HTML**, названный
RESEARCH §4.1 как основание варианта D-08b; для правила D-08a он не нужен, но при выборе
D-08b форму брать отсюда.

**Тест, который обязан быть переписан (Pitfall 9), — `:479`:**

```python
    assert 'method="post"' in opening.lower(), "форма тумблера не POST"
    assert "x-on:change" in opening, "перехват отправки навешен не на саму форму"
```

D-05 снимает `x-on:change` → утверждение переезжает на `hx-trigger="change"`. **Вторая
половина теста (`:488-491`) сохраняется дословно** — она про путь без Alpine:

```python
    assert re.search(r'<button[^>]*type="submit"', body), (
        "в форме тумблера нет элемента, отправляющего её без JS: "
        "при неподнявшемся Alpine группу нельзя ни включить, ни выключить"
    )
```

**Новые пары** — по SP-3 и RESEARCH §Canonical paired-test form; перечень требуемых —
RESEARCH §Wave 0 Gaps / Phase Requirements → Test Map.

---

### 11. `tests/test_templates/test_htmx_markup_gates.py` (MODIFY) — аналог самому себе + SP-1 + SP-2

**Форма объявления инвентарного числа с летописью** (`:100-110`, `:925-943`):

```python
# Уменьшение объявленного числа допустимо и означает СОЗНАТЕЛЬНОЕ снятие места,
# записанное следующей записью этой летописи. Молчаливое исчезновение краснеет.

# Мест отправки htmx сегодня ОДНО — форма редактора объявлений. ...
HX_POST_PLACES = 1
```

```python
# Целей подмены в проекте сегодня НЕ ОБЪЯВЛЕНО НИ ОДНОЙ. Ноль объявляется
# ИМЕНОВАННОЙ КОНСТАНТОЙ, а не выводится из пустого множества: без числа
# правила существования цели и границы клиентского состояния были бы вакуумно
# зелёными навсегда, и первая же цель, добавленная Фазой 9, вошла бы в проект
# ни одним правилом не проверенной. Прецедент формы — SERVER_SIDE_VALIDATION_RESPONSES.
HX_TARGETS = 0

# Внеполосных блоков шесть: три собирает ответ автосохранения редактора
# объявлений, четвёртый — индикатор состояния, чей признак выставляется ВЕТКОЙ
# ШАБЛОНИЗАТОРА внутри открывающего тега ..., и два — внеполосная форма уведомления,
# заведённая планом 08-04.
OOB_BLOCKS = 6

# Узлов с признаком клиентского состояния двадцать четыре. ...
CLIENT_STATE_NODES = 24
```

**Что копируется:** правка числа идёт **вместе с правкой комментария-летописи** — новое
число обязано перечислять, из чего оно складывается (три места `hx-post`, одна цель, девять
OOB-блоков). **Что добавляется:** четыре перечня по SP-1, новые правила по D-03/D-06/D-08,
контроль на каждое новое правило по SP-2.

⚠️ **Восьмое движущееся число, в таблице CONTEXT.md отсутствующее** (RESEARCH §3):
`test_both_branches_of_the_editor_action_are_extracted` (`:899-918`) — литерал
`len(paths) == 2` внутри тела теста, станет `3`. Константой не объявлен, поэтому грепом по
именам не находится.

---

### 12. `tests/test_pages/test_htmx_gates.py` (MODIFY) — аналог самому себе

**Перечень + число + ДВА теста на одно число** (`:185-235`) — образец «счётчика прогресса
вехи», о котором CONTEXT §Specifics требует говорить как о движении, а не о правке теста:

```python
# ⚠️ ЭТО УБЫВАЮЩЕЕ ЧИСЛО, А НЕ СПИСОК НАРУШЕНИЙ. Оно есть машинный счётчик
# прогресса вехи: каждая следующая фаза снимает отсюда обработчики и опускает
# `NOT_YET_CONVERTED_COUNT`. Тестов на него ДВА, и у каждого движения свой текст
# отказа — один текст на два разных события лгал бы в одном из них.
NOT_YET_CONVERTED: frozenset[str] = frozenset(
    {
        "app/pages/account_groups.py::account_groups_toggle",
        "app/pages/account_groups.py::account_groups_delete",
        ...
    }
)

# То же число константой. Утверждений на него ДВА, и они про РАЗНЫЕ события:
# рост означает регрессию, падение означает прогресс вехи.
NOT_YET_CONVERTED_COUNT = 36
```

Текст отказа второго теста **уже написан под эту фазу** (`:709-724`) — читать перед правкой:

```python
    assert len(backlog) == NOT_YET_CONVERTED_COUNT, (
        f"число непереведённых обработчиков стало {len(backlog)}, а в файле "
        f"записано {NOT_YET_CONVERTED_COUNT}. ЕСЛИ ЧИСЛО УПАЛО — ЭТО ПРОГРЕСС "
        "ВЕХИ, а не поломка: опустите NOT_YET_CONVERTED_COUNT до "
        f"{len(backlog)}, снимите переведённые обработчики из "
        "NOT_YET_CONVERTED и запишите это прогрессом в сводке фазы. ..."
    )
```

**Действие:** снять две записи `account_groups.py::…` из `NOT_YET_CONVERTED`, опустить
`NOT_YET_CONVERTED_COUNT` 36 → 34. `HX_HEADER_WRITES = 2` и `POST_HANDLERS = 36` не двигать.

---

## No Analog Found

| Файл / приём | Роль | Почему аналога нет | Чем заменяется |
|---|---|---|---|
| Класс индикатора с порогом `transition-delay` | stylesheet | Единственный прецедент (`app.css:1696-1711`) переключает `display`, порога не имеет и селектор у него потомковый — форму брать нельзя | RESEARCH §5.3 (готовое правило CSS с комментарием) |
| Правило гейта «внутри цели свапа только голый `x-data`» (D-08) | gate rule | Действующий GATE-06 вложенности не считает и объявляет это своей границей | RESEARCH §4.1, вариант **D-08a** + контроль по SP-2 |
| Правило «каждый `hx-post` рождён макросом» (D-03) | gate rule | Мест `hx-post` сегодня одно, обхода по «рождению» нет | SP-1 (перечень исключений: редактор объявлений — Фаза 12) + SP-2 |
| Утверждение «OOB-узлы стоят на ВЕРХНЕМ уровне ответа» | test | Прецедента нет: `allowNestedOobSwaps: false` до этой фазы предмета не имел | RESEARCH §4.4(2) — текстовая проверка по телу ответа |

---

## Metadata

**Область поиска аналогов:** `app/templates/components/`, `app/templates/account_groups/`,
`app/templates/ads/includes/`, `app/templates/includes/`, `app/pages/`, `app/static/css/`,
`tests/test_pages/`, `tests/test_templates/`, `tests/conftest.py`.
**Прочитано файлов:** 18 (плюс два документа фазы).
**Дата извлечения:** 2026-08-29.
