# Phase 15: Упрочнение и сводный обход 47 форм — Pattern Map

**Mapped:** 2026-09-23
**Files analyzed:** 14 (5 новых файлов, 5 новых групп в существующих файлах, 4 участка правки кода)
**Analogs found:** 14 / 14 (аналог найден для каждого; качество совпадения — в таблице)

Все координаты ниже **перезамерены в этом сеансе** и относятся к git-tracked
исходникам рабочего дерева. Расхождения с тем, что записано в CONTEXT.md и в
записи долга Фазы 10, названы разделом «Расхождения с записью» — они не сглажены.

---

## File Classification

| Новый / правимый файл | Роль | Поток данных | Ближайший аналог | Качество |
|---|---|---|---|---|
| `tests/test_planning/test_plan_prohibitions_census.py` | инвентарный гейт над записью | file-I/O + transform (YAML) | `tests/test_planning/test_the_walkthrough_cannot_self_certify.py` (форма модуля каталога) + `tests/test_templates/test_htmx_inventory.py` (форма инвентаря) | role-match (точного аналога-переписи нет) |
| `tests/test_templates/test_form_inventory.py` | инвентарный гейт над разметкой | file-I/O (обход шаблонов) | `tests/test_templates/test_htmx_inventory.py` | **exact** |
| `tests/test_templates/test_degradation_pairs.py` | гейт суиты о себе | transform (`ast` над `tests/`) | `tests/test_pages/test_impersonation_gate.py` (разбор `ast` + объявленные границы) | role-match |
| `15-PROHIBITIONS-SUBJECT.md` | артефакт-реестр решений | документ | `.planning/phases/10-rychag-components-modal-html/10-PROHIBITIONS-SUBJECT.md` | **exact** |
| `15-UAT.md` | артефакт ручного обхода | документ | `.planning/phases/13-.../13-UAT.md` (заполненные отметки) | **exact по форме**, ⚠️ у образца 5 таблиц, нужно 9 |
| группа FETCH-03 в `tests/test_templates/test_htmx_inventory.py` | запрет (речевой акт ≠ счётчик) | file-I/O | тот же файл, группа `MANUAL_FETCH_*` (:1108-1201) | **exact** (дом объявлен самим файлом) |
| группы D-07 / условный `hx-post` / 12 мест в `tests/test_templates/test_htmx_markup_gates.py` | гейты разметки | file-I/O | `test_modal_site_inventory` (`test_components.py:1632`) — связка несколькими счётами | **exact** |
| группа `hx-push-url` в `tests/test_pages/test_htmx_gates.py` | гейт слоя ответа | transform (`ast` над `app/pages/`) | тот же файл: `FRAGMENT_RESPONSE_HANDLERS` (:1934) + `_DECLARED` (:2305) | **exact** |
| гейт огульного `except` в `tests/test_services/` | гейт продукта по `ast` | transform | `tests/test_pages/test_impersonation_gate.py` (`_mutating_routes`, :454) | role-match |
| CR-01 тест в `tests/test_pages/test_editor_schedules.py` | integration | request-response | `tests/test_schedules_out_of_domain_resume.py` (`MALFORMED_STORED_FORMS`, :116) + `tests/test_pages/test_schedules_poisoned_row.py` | **exact** |
| `app/pages/schedules.py` — `schedules_update` | обработчик | request-response | `schedules_create` (тот же файл, :1079-1082) и `schedules_toggle` (:1469) | **exact, аналог в том же файле** |
| `app/templates/includes/htmx_error_banner.html` + `app/static/css/app.css` | разметка + CSS | — | те же файлы, соседние объявления `.banner-dismiss` (:1318-1330) | exact |
| шесть шаблонов с `limit=30` | разметка | — | пара «список + partial_cards» уже парная по построению | exact |
| `app/templates/components/thumb.html:34` | макрос разметки | — | `app/templates/components/form_wrapper.html:186` (атрибуты по построению макроса) | partial |

---

## Pattern Assignments

### Канонический образец фазы: `tests/test_templates/test_htmx_inventory.py` (1454 строки)

Ф-16 верна: это единственный модуль дерева, несущий **все пять форм** сразу. Все пять
перезамерены дословно.

#### Форма 1 — объявленный литерал вместо порога «хотя бы одно» (:44-60)

```python
class HxGetSite(NamedTuple):
    """Шаблон, несущий места ``hx-get`` одного механизма.

    places — ОЖИДАЕМОЕ число мест в этом шаблоне, а не порог «хотя бы одно».
    ...  Порог
    «хотя бы одно» растворил бы потерю одной из двух веток подключения: экран
    остался бы зелёным, опрашивая состояние только в одной из них.
    """

    template: str
    places: int
```

Обоснование выписывания литерала ЗДЕСЬ, а не вывода из источника (:63-67):

```python
# ЛЕТОПИСЬ ЧИСЕЛ. Перечни ниже выписаны ЗДЕСЬ, а не выведены из проверяемых
# шаблонов: тест, считающий ожидание по коду в момент прогона, согласится с
# любой правкой и молча переживёт исчезновение места — ровно тот отказ, ради
# которого инвентарные гейты в проекте и заведены (прецедент формулировки —
# tests/test_pages/test_access_gate.py:40-43).
```

#### Форма 2 — летопись (:69-87, :1082-1107)

Форма записи, обязательная по D-09, дословно:

```python
# ПОПРАВКА РАЗБИВКИ 10/10/2 → 12/8/2 (планирование Фазы 7 против счёта по
# файлам). ... Счёт по файлам дал 12 / 8 / 2 при той же СУММЕ 22: сумма была
# верна, разбивка — нет. Принята величина, полученная счётом, а не перенесённая
# из ожидания; гейт, написанный по CONTEXT.md, был бы красным в момент
# написания. Поправка записана здесь ПЕРВОЙ записью летописи именно как
# поправка: тихо выписать верные числа значило бы стереть свидетельство о том,
# что ожидание разошлось с кодом ...
```

И вторая запись летописи — с указанием, ЧЕМ снято число (`:1092-1103`):

```python
# ЛЕТОПИСЬ ЧИСЛА: 5 → 0, Фаза 13, план 13-01 — ... ⚠️ НОЛЬ В ШАБЛОНАХ ВЕХИ
# ДОСТИГНУТ ЭТОЙ ФАЗОЙ, НО ОТДЕЛЬНОЕ ПРАВИЛО «В ШАБЛОНАХ НОЛЬ» — ПРЕДМЕТ ФАЗЫ 15
# (FETCH-03), А НЕ ЭТОЙ: здесь ноль стоит ИМЕНОВАННЫМ числом убывающего
# счётчика, а не утверждением-запретом.
# Число поставлено ПРОГОНОМ ПОКРАСНЕВШЕГО ПРАВИЛА, дословно: ...
```

⚠️ **Дом FETCH-03 объявлен самим файлом.** Запрет ложится сюда, рядом со счётчиком,
и его летопись обязана сослаться на эту запись.

#### Форма 3 — названная граница «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» (:19-34)

```python
ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ. Зелёный цвет здесь означает ровно одно: разметка
СУЩЕСТВУЕТ, мест 22, и они распределены по трём механизмам как 12 / 8 / 2. Он НЕ
означает, что хоть одно из 22 мест сработало на рантайме 2.0.10: суита не
исполняет ни строчки JS и ни одной страницы не рендерит браузером. ...
Читатель, дошедший до зелёного цвета и остановившийся на нём, прочитал половину;
вторая половина живёт по названному пути.
```

Шапка того же файла прямо называет Фазу 15 наследницей (:13-17) — это цитировать в
докстринге каждого нового прибора фазы.

#### Форма 4 — потолок, чьё имя мешает его поднять (:1071-1111)

```python
# ПОЧЕМУ ПОТОЛОК ОБЪЯВЛЕН ОТДЕЛЬНОЙ ВЕЛИЧИНОЙ. Убывающий счётчик имеет ровно
# один способ выродиться: седьмое место краснит первый тест, и починить это
# можно, подняв `MANUAL_FETCH_PLACES` до семи. ... Потолок с именем фазы поднять
# незаметно нельзя: чтобы разрешить себе семь, придётся переписать величину,
# чьё имя утверждает, чему она была равна в Фазе 8, — то есть солгать в
# опознаваемом месте.
MANUAL_FETCH_CEILING_AT_PHASE_08 = 0
MANUAL_FETCH_PLACES = 0
```

Проверка потолка вынесена в чистую функцию, чтобы контроль мог подать ей гипотезу
(`_ceiling_offence`, :1148-1156) — **это несущий приём: копировать вместе с потолком.**

```python
def _ceiling_offence(declared: int, ceiling: int) -> str:
    """Пустая строка, если объявленное число не превысило потолок фазы."""
    if declared <= ceiling:
        return ""
    return (...)
```

#### Форма 5 — ноль, доказанный от вакуума (:1312-1454)

⚠️ **Поправка к заданию:** контроли этого файла **НЕ используют `tmp_path`.** Они
подменяют СЛОВАРЬ ИСХОДНИКОВ (`_template_sources()`), и файл называет это несущим
решением (`:713-723`). Для приборов над разметкой копировать надо именно эту форму —
`tmp_path` здесь лишний и завёл бы файловые операции там, где их нет.

Отрицательный контроль роста (:1312-1332):

```python
def test_control_negative_a_seventh_manual_fetch_reddens_the_growth_gate() -> None:
    """ЧТО ДОКАЗЫВАЕТ: седьмое место ручной сборки запроса гейт ВИДИТ."""
    key = "dashboard.html"
    sources = _template_sources()

    changed = dict(sources)
    changed[key] = sources[key] + (
        "\n<script>fetch('/dashboard/a-call-some-future-phase-will-add');</script>\n"
    )
    assert changed[key] != sources[key], "подмена ничего не изменила"

    found = _manual_fetch_places(changed)

    assert len(found) == MANUAL_FETCH_PLACES + 1, (...)
    assert not len(found) <= MANUAL_FETCH_PLACES, (
        "утверждение «не выросло» осталось истинным при выросшем числе — "
        "счётчик зелен по построению"
    )
```

Контроль на СИНТЕТИЧЕСКОМ ключе — форма для нулей фазы, чей предмет в дереве
отсутствует (условный `hx-post`, `hx-push-url`) (:1351-1361):

```python
    key = "synthetic/one_manual_fetch.html"
    sources = _template_sources()
    assert key not in sources, "синтетический шаблон совпал по имени с настоящим"

    with_one = dict(sources)
    with_one[key] = "<script>fetch('/synthetic/a-call-a-fragment-will-replace');</script>\n"
    declared = len(_manual_fetch_places(with_one))
    assert declared == MANUAL_FETCH_PLACES + 1, (...)
```

Контроль на объявление, а не на факт (:1386-1401) — **обязателен у каждого потолка**:

```python
def test_control_negative_raising_the_declared_ceiling_reddens_the_gate() -> None:
    """ЧТО ДОКАЗЫВАЕТ: ПОТОЛОК НЕ ПОДНЯТЬ МОЛЧА. ..."""
    assert _ceiling_offence(CEILING + 1, CEILING), (...)
    assert _ceiling_offence(CEILING - 1, CEILING) == "", (
        "гейт покраснел на ОПУЩЕННОМ числе — путь вниз есть прогресс вехи ..."
    )
```

Положительные контроли — **вот где живёт «обход не пуст»** (:1437-1454):

```python
def test_control_positive_the_untouched_tree_keeps_both_gates_green() -> None:
    """ЧТО ДОКАЗЫВАЕТ: на НЕИЗМЕНЁННОМ дереве обе группы молчат. ..."""
    sources = _template_sources()

    assert len(sources) > 50, (
        f"обход нашёл всего {len(sources)} шаблонов — обе группы могли сойтись "
        f"на пустоте"
    )
```

И контроль пустого дерева (:1404-1434) — доказывает, что правило не роняет сборку
там, где искать нечего, И что утверждение о числе на пустоте законно краснеет.

**Что копировать в каждый новый файл фазы:** формы 1, 3 и 5 — минимум; формы 2 и 4
там, где есть число с историей (инвентарь 47 → 49; неразобранные запреты).

---

### `tests/test_planning/test_plan_prohibitions_census.py` (инвентарный гейт над записью, YAML)

**Аналог формы модуля:** `tests/test_planning/test_the_walkthrough_cannot_self_certify.py`
**Аналог формы инвентаря:** `test_htmx_inventory.py` (выше)

Маркер и его обоснование (`:51-55`) — копировать дословно вместе с комментарием:

```python
# Предмет модуля — ЗАПИСЬ проекта, а не его продукт. Основание маркера, его
# граница годности и запрет выключать каталог — `tests/test_planning/__init__.py`;
# само имя объявлено хуком в `tests/conftest.py`.
pytestmark = pytest.mark.planning
```

Все шесть модулей каталога несут `pytestmark` (`__init__.py:3` требует это буквально) —
проверено: `test_planning_gates_are_independent_of_the_live_verdict.py:52`,
`test_requirement_completion_follows_verification.py:51`,
`test_deferred_items_are_idempotent.py:36`, `test_the_walkthrough_stand_is_seedable.py:93`,
`test_state_progress_matches_roadmap.py:50`, `test_the_walkthrough_cannot_self_certify.py:51`.

Абзац о D-33 (обязателен, `:30-36`) — форма, повторённая во всех четырёх модулях:

```python
ПОЧЕМУ ЭТО НЕ ОТМЕНА РЕШЕНИЯ D-33. Решение D-33 отказало машинному гейту на ПРОЗЕ
операционного документа с названной причиной: отличить «константу величины, которую
документ не может держать истинной» от законного числа того же документа машине нечем.
Здесь предмет ДРУГОЙ: ДВА машинно читаемых поля ... и ОДНО объявленное между ними
соответствие. Суждения этот предмет не требует, поэтому D-33 настоящим модулем НЕ
ПЕРЕОТКРЫВАЕТСЯ и НЕ ОТМЕНЯЕТСЯ; документная половина по-прежнему судится человеком.
```

Запрет литерала сегодняшнего незакрытого состояния (`:23-28`) — **это ровно то, что
запрещает утверждать `unresolved == 329`:**

```python
⚠️ ЛИТЕРАЛА НЕПРОЙДЕННОГО СОСТОЯНИЯ ЗДЕСЬ НЕТ ВОВСЕ, И ЭТО НЕСУЩЕЕ РЕШЕНИЕ. Правило,
знающее имя того состояния, в котором дерево находится СЕГОДНЯ, зеленело бы ровно при
условии, что фаза не достигла цели, — дословно тот блокер, который четвёртый круг
верификации нашёл у соседнего модуля каталога. Нетерминальность выражается ОТРИЦАНИЕМ
принадлежности объявленному перечню, а не именем; полное распределение значений поля
состояния по дереву записано в сводке плана 10-20, а не в исходнике.
```

Форма «перечень вместо одного литерала», снятая ЗАМЕРОМ (`:66-73`) — прямой образец для
перечня диспозиций `enforced` / `permitted` / `unresolved`:

```python
TERMINAL_WALKTHROUGH_STATES = frozenset({"complete", "passed"})
...
TERMINAL_STATES_DECLARED = 2
```

Форма «изъятие, запертое числом» (`:88-106`) — образец для 329 неразобранных **без**
утверждения их числа:

```python
# ⚠️ ИЗЪЯТИЕ ЗАПЕРТО ЧИСЛОМ, ПОЭТОМУ ОНО НЕ УМЕЕТ РАСТИ МОЛЧА: артефакт, у которого
# таблицы отметок СНЯЛИ, увеличит число изъятых и покраснит прогон.
MARKED_FORM_EXEMPT_DECLARED = 11
...
# ⚠️ ПЕРЕЧИСЛЯТЬ ИЗЫМАЕМОЕ СПИСКОМ ПУТЕЙ ЗАПРЕЩЕНО: список путей не переживёт ни
# переезда артефакта в архив, ни появления нового, — а признак самого артефакта
# переживёт и то и другое.
```

Форма «разборщик принимает ИСХОДНИК ТЕКСТОМ, а не путём» (`:181-187`) — обязательна,
иначе контроль зубов невыразим:

```python
def walkthrough_counts(source: str) -> WalkthroughCounts:
    """Разборщик артефакта обхода. ИСХОДНИК ПРИХОДИТ ТЕКСТОМ, а не путём.

    Без параметра-исходника контроль зубов был бы невыразим, и зубы правила
    пришлось бы ЗАЯВЛЯТЬ вместо того, чтобы их ПОКАЗЫВАТЬ, — идиома каталога,
    записанная у обоих соседних модулей по той же причине.
    """
```

Форма dataclass со «признаком «не объявлено», а не нулём» (`:117-131`) — прямо нужна
переписи, чтобы «дескриптора нет» не слилось с `verification: none`:

```python
@dataclass(frozen=True)
class WalkthroughCounts:
    """...
    `declared_checks` — объявленное шапкой число проверок либо `None` — ПРИЗНАК
    «не объявлено», а не ноль: ноль означал бы «объявлено ноль проверок», и
    смешение этих двух вещей изъяло бы артефакт из правила молча.
    """
```

**Прецедент `import yaml` в каталоге:** `tests/test_planning/test_state_progress_matches_roadmap.py:45`
(голый импорт без защиты) — подтверждено.

---

### `tests/test_templates/test_form_inventory.py` (инвентарь 49/27 + реестр `hx-push-url`)

**Аналог:** `test_htmx_inventory.py` целиком (формы 1-5 выше).

**Обязательный импорт помощников, а не свой обход** — `tests/test_templates/test_htmx_markup_gates.py`:

```python
# :342 — каталог ПАРАМЕТРОМ; :365 — порядок вырезания значим
def _all_templates(directory: Path | None = None) -> list[tuple[str, str]]: ...

def _strip_comments(source: str) -> str:
    """Исходник без Jinja- и HTML-комментариев.

    Порядок вырезания значим: сначала Jinja, потом HTML — Jinja исполняется
    раньше, и HTML-комментарий, лежащий внутри ``{# … #}``, до браузера не
    доходит вовсе.
    """
    return HTML_COMMENT.sub("", JINJA_COMMENT.sub("", source))
```

**Две величины разными путями из одного источника** (`:375-392`) — форма, которой
инвентарь 49 обязан следовать, чтобы «ошибка разбора границ тега» отличалась от
«пропажи разметки»:

```python
def _sites(templates: list[tuple[str, str]], tag_re: re.Pattern[str]) -> list[Site]: ...

def _attribute_count(templates: list[tuple[str, str]], attr_re: re.Pattern[str]) -> int:
    """Число вхождений атрибута — независимо от разбора границ тега.

    Считается по тому же исходнику без комментариев, что и теги, но БЕЗ разбора
    тегов. Две величины, полученные разными путями из одного источника,
    сверяются отдельным тестом: расхождение означает ошибку разбора границ, а
    не пропажу разметки.
    """
```

**Что считать формой письма** — `app/templates/components/form_wrapper.html:186`
(перезамерено, макрос раздаёт `hx-post` ПО ПОСТРОЕНИЮ):

```jinja
{% macro form_wrapper(action, target=None, swap=None, trigger=None, disabled_elt='find button[type=submit]', sync=None, encoding=false, include=None) -%}
<form method="post" action="{{ action }}" hx-post="{{ action }}" class="form-wrapper"
      {%- if target %} hx-target="{{ target }}" hx-swap="{{ swap or 'outerHTML' }}"
      {%- else %} hx-swap="none"{% endif %}
      {%- if trigger %} hx-trigger="{{ trigger }}"{% endif %}
      {%- if sync %} hx-sync="{{ sync }}"{% endif %}
      {%- if encoding %} hx-encoding="multipart/form-data" enctype="multipart/form-data"{% endif %}
      {%- if include %} hx-include="{{ include }}"{% endif %}
      {%- if disabled_elt %} hx-disabled-elt="{{ disabled_elt }}"{% endif %} hx-indicator="find .form-busy">
```

⚠️ **Здесь же лежат те самые 12 мест условной сборки прочих `hx-*` (Ф-08):** в теле
макроса ветвей `{%- if %}` шесть (`hx-target`/`hx-swap`, `hx-swap="none"`, `hx-trigger`,
`hx-sync`, `hx-encoding`+`enctype`, `hx-include`, `hx-disabled-elt`). Гейт 12 мест
обязан считать их **вместе** с местами вне макроса, а `hx-post` и `hx-indicator` —
безусловны, что и делает правило «условный `hx-post` == 0» законно пустым.

---

### Новые группы в `tests/test_templates/test_htmx_markup_gates.py` — связка D-07

**Аналог формы:** `tests/test_templates/test_components.py:1632-1662` — связка,
доказанная НЕСКОЛЬКИМИ независимыми счётами, а не одним обходом:

```python
MODAL_IMPORTERS = 11      # test_components.py:1096
MODAL_EVENT_NAMES = 9     # :1097
MODAL_PLACES = 18         # :1098


def test_modal_site_inventory():
    """Инвентаризация мест подтверждения сходится ЧЕТЫРЬМЯ счётами.

    Счёт по импортёрам до числа мест дойти не может в принципе: файл подмены
    статуса панель сознательно не импортирует. Поэтому третий счёт — ПРЯМОЙ:
    сумма вхождений имени события открытия по всем шаблонам, КРОМЕ самого
    компонента. ...

    ⚠️ ЧЕТВЁРТЫЙ СЧЁТ ПРИБАВЛЕН ФАЗОЙ 10 (план 10-01, D-14): множество ИМЁН
    ИМЕНОВАННЫХ АРГУМЕНТОВ, передаваемых вызывающими по всем шаблонам, есть
    ПОДМНОЖЕСТВО имён сигнатуры макроса. ...
    """
```

⚠️ **Подтверждено: счётов ЧЕТЫРЕ, а не три** (CONTEXT.md §Reusable Assets говорит «тремя
счётами» — устарело, Ф-20 права). Гейт связки строить на этой форме.

**Второй узел связки** — `app/templates/components/modal.html`: тег открывается на
**805**, `hx-post` стоит на **807** (CONTEXT.md называет 805 — это строка открытия тега,
атрибут строкой ниже):

```jinja
    <form class="modal__form" method="post" action="{{ action }}"
          x-on:submit="if (sending) { $event.preventDefault(); return; } sending = true"
          x-on:htmx:after-request="..." hx-post="{{ action }}" hx-swap="none" hx-disabled-elt="find button[type=submit]" hx-indicator="find .form-busy">
```

---

### Новая группа в `tests/test_pages/test_htmx_gates.py` — `hx-push-url` (дом по Ф-13)

Дом верен: перечень «изменяет данные» живёт **здесь**, а не в пакете разметки.
Перезамерено:

| Величина | Строка |
|---|---|
| `HX_HEADER_WRITES = 6` | `tests/test_pages/test_htmx_gates.py:273` |
| `FRAGMENT_RESPONSE_HANDLERS: frozenset[str] = frozenset(` | `:1934` |
| `FRAGMENT_RESPONSE_HANDLERS_DECLARED = 25` | `:2305` |
| `NOT_YET_CONVERTED_COUNT = 0` | `:847` |

Форма «именованного нуля» из этого же файла (`:1510` и далее) — цитируется RESEARCH.md
дословно и остаётся образцом для нуля `hx-push-url`.

⚠️ Поправка: `FRAGMENT_RESPONSE_HANDLERS` в `app/` **не** объявлен — он целиком
принадлежит суите. Плану нельзя ссылаться на него как на продуктовую константу.

---

### Именованный реестр изъятий — `tests/test_pages/test_account_groups.py`

**Это образец для реестра решений по запретам и для любого перечня изъятий фазы.**
Все четыре координаты из задания **подтверждены**.

Живая форма — запись с обоснованием и назначенной фазой (`:4916-4934`):

```python
OOB_TARGET_EXCEPTIONS: dict[str, OobTargetException] = {
    "group-row-{group_id}": OobTargetException(
        where_printed="app/templates/account_groups/partials/delete_response.html",
        assigned_phase="Фаза 15 — Упрочнение и сводный обход 47 форм",
        reason=("СНЯТИЕ СТРОКИ УДАЛЁННОЙ ГРУППЫ. " + _IDLE_DELETE_REASON),
    ),
    "group-del-{group_id}": OobTargetException(..., assigned_phase="Фаза 15 ...", ...),
}
```

⚠️ **Обе записи назначены ИМЕННО Фазе 15** — планировщик обязан знать, что этот реестр
адресован текущей фазе, а CONTEXT.md его не перечисляет.

Число — отдельной константой, с летописью, снятой ИЗМЕРЕНИЕМ (`:4936-4952`):

```python
# ⚠️ ЧИСЛО ВЫПИСАНО ОТДЕЛЬНОЙ КОНСТАНТОЙ НАМЕРЕННО (второе утверждение идиомы
# SP-1). Беззвучно выросшее означает, что внеполосный узел с иногда
# отсутствующей целью завёлся, а решения о нём никто не принимал; беззвучно
# упавшее — что отступление закрыто, и это обязано быть записано строкой
# летописи, а не обнаружено через фазу.
#
# ЛЕТОПИСЬ:
#   0 → 0, Фаза 9, план 09-14, задача 3 (RED) — перечень объявлен ПУСТЫМ
#     намеренно, чтобы поведенческое утверждение ниже покраснело ... Число
#     ставится ИЗМЕРЕНИЕМ, а не арифметикой плана.
#   0 → 2, Фаза 9, план 09-14, задача 3 (GREEN) — прогон назвал `group-row-N` и
#     `group-del-N`. ...
OOB_TARGET_EXCEPTIONS_DECLARED = 2
```

Отдельно утверждаемое число + антивакуум (`:4984-5000`):

```python
def test_the_number_of_oob_target_exceptions_is_the_declared_one():
    """ПЕРВОЕ утверждение идиомы SP-1: число записей — объявленное.

    Оно же антивакуум: перечень, опустевший молча, оставил бы правило ниже
    зелёным ровно тогда, когда узлов с отсутствующей целью не стало, — и
    неотличимым от перечня, чьи записи тихо отменили.
    """
    assert len(OOB_TARGET_EXCEPTIONS) == OOB_TARGET_EXCEPTIONS_DECLARED, (...)
    assert OOB_TARGET_EXCEPTIONS_DECLARED > 0, (...)
```

Форма «закрыто летописью, а не удалено молча» (`:3635`, `:3637-3648`, `:3703-3707`) —
**обязательна для любого запрета Фазы 10, который окажется снятым, а не разрешённым:**

```python
INCLUDE_TARGET_EXCEPTIONS: dict[str, IncludeTargetException] = {}   # :3635

# ⚠️ ЗАПИСЬ `group-list-sentinel` ЗАКРЫТА ПЛАНОМ 09-13, А НЕ УДАЛЕНА МОЛЧА, И
# ПРЕЖНИЙ ЕЁ ТЕКСТ СОХРАНЁН НИЖЕ ЦЕЛИКОМ. ПРЕДМЕТ СНЯТ, А НЕ ОТЛОЖЕН: ...
# Назначенная фаза обязана увидеть, ЧТО именно ей назначалось и почему это
# перестало существовать, — иначе закрытие неотличимо от тихой отмены.
# --- ПРЕЖНИЙ ТЕКСТ ЗАПИСИ, СОХРАНЁННЫЙ ДОСЛОВНО ---------------------------
# INCLUDE_TARGET_EXCEPTIONS: dict[str, IncludeTargetException] = { ... }
# --- КОНЕЦ СОХРАНЁННОГО ТЕКСТА --------------------------------------------
#   1 → 0, Фаза 9, план 09-13, задача 4 — ПРЕДМЕТ СНЯТ, А НЕ ОТЛОЖЕН: ...
INCLUDE_TARGET_EXCEPTIONS_DECLARED = 0                              # :3707
```

---

### `tests/test_degradation_pairs.py` и гейт `except` — форма разбора по `ast`

**Аналог:** `tests/test_pages/test_impersonation_gate.py`. Координаты D-16
**подтверждены все четыре: 373, 456, 631, 696.**

Граница «обходится объявление, а не тело» (`:371-375`):

```python
    ⚠️ ОБХОДИТСЯ НЕ ВСЯ ФУНКЦИЯ, А ТОЛЬКО ЕЁ ОБЪЯВЛЕНИЕ: умолчания параметров и
    аргумент `dependencies=` декоратора. Обход тела посчитал бы упоминание в
    докстринге или комментарии — то есть зеленел бы на маршруте, где про запрет
    только НАПИСАНО.
```

Приём второго уровня — граница НАЗВАНА и форма, которую гейт не видит, отдельным
правилом ЗАПРЕЩЕНА (`:456-476`):

```python
    ⚠️ НАЗВАННЫЕ ГРАНИЦЫ РАЗБОРЩИКА — их две, и обе выписаны здесь, а не
    оставлены на догадку читателя (WR-08 ревизии фазы 6):

    1. `router.add_api_route(handler, methods=[...])` — объявление ВЫЗОВОМ, а не
       декоратором — разборщику не видно ... Форма поэтому ЗАПРЕЩЕНА в
       обоих слоях отдельным утверждением
       (`test_no_route_is_declared_in_a_form_the_gate_cannot_see`): гейт,
       который чего-то не видит, обязан требовать, чтобы этого и не было.

    2. Изменяющим считается только маршрут изменяющего МЕТОДА. ... Это ПРИНЯТАЯ
       граница: расширение множества на `GET` втянуло бы в перечни все читающие
       маршруты продукта ...
```

Довод «по дереву, а не по строке» (`:628-632`, `:695-698`) — тот самый, которым Ф-18
обосновывает `ast` для гейта `except`:

```python
    Утверждение снимается по дереву, а не по строке: маршрут, у которого про
    запрет написано в докстринге, зависимости не несёт.
```

**Предмет гейта `except`** — `app/services/schedule_rules.py`, перезамерено:
`UNRUNNABLE_STORED_VALUE_ERRORS` объявлен на **:145-152**, `next_run_or_none` — **:155**,
докстринг-фантом — **:175-181** (⚠️ CONTEXT.md говорит 175-181, RESEARCH.md 175-179;
фраза «Запрет проверяется грепом по телу модуля, поэтому имя запрещённой конструкции
здесь и не набирается» стоит на **:178-179**). Ф-18 подтверждена дословно.

**Замер пар деградации (перезамер этого сеанса, `ast`-независимый греп по `def test`):**

| Основа | Файл |
|---|---|
| `test_the_only_payment_left_is_a_real_form_degrades_without_alpine` | `tests/test_pages/test_billing_section.py` |
| `test_accounts_delete_form_degrades_without_alpine` | `tests/test_pages/test_responsive_markup.py` |
| `test_ads_delete_form_degrades_without_alpine` | `tests/test_pages/test_responsive_markup.py` |
| `test_admin_user_delete_form_degrades_without_alpine` | `tests/test_pages/test_responsive_markup.py` |
| `test_editor_delete_form_degrades_without_alpine` | `tests/test_pages/test_ads_editor.py` |
| `test_editor_delete_degrades_without_htmx` | `tests/test_pages/test_editor_schedules.py` |
| `test_toggle_degrades_without_htmx` | `tests/test_pages/test_account_groups.py` |
| `test_delete_degrades_without_htmx` | `tests/test_pages/test_account_groups.py` |

5 alpine / 3 htmx — Ф-14 и Ф-09 подтверждены. ⚠️ **Плюс два имени, которых ни один из
перечней не считает:** `test_subsection_navigation_degrades_without_js`
(`test_admin_panel.py`) и `test_the_delete_degrades_without_the_rendered_rows_field`
(`test_account_groups.py`). Объявляемый предикат пары обязан сказать, входят они в
вселенную или изъяты, — иначе перечень пяти основ литералом окажется неполон по
собственному образцу имени.
⚠️ И ближайшая к паре пара — `editor_delete_form` (alpine, редактор объявлений) против
`editor_delete` (htmx, редактор расписаний): основы **похожи, но предметы разные экраны.**
Предикат «совпадение основы» объявил бы их парой ошибочно.

---

### CR-01 — `app/pages/schedules.py` (⚠️ координаты записи долга НЕВЕРНЫ)

**Перезамер `ast` этого сеанса подтверждает Ф-17 полностью:**

| Обработчик | Строки |
|---|---|
| `schedules_partial` | 803-874 |
| `schedules_list` | 878-938 |
| `schedules_create` | 973-1177 |
| **`schedules_update`** | **1181-1356** |
| `schedules_toggle` | 1360-1574 |
| `schedules_delete` | 1578-1854 |

**Записанные в CONTEXT.md D-18.1 координаты `1049-1070` попадают внутрь
`schedules_create`.** Исполнитель, пошедший по ним буквально, правил бы ПОЧИНЕННЫЙ
обработчик. `read_first` плана обязан указывать **`app/pages/schedules.py:1181-1356`**.

**Дефект в новых координатах — `:1278-1280`:**

```python
    tz = form_data.get("timezone", schedule.timezone)
    if tz not in VALID_TIMEZONES:
        tz = schedule.timezone
```

Далее `schedule.timezone = tz` (**:1286**) и `compute_next_run_at(..., tz_name=tz)`
(**:1290-1292**, внутри ветви `else` на `:1289-1296`). ⚠️ Ф-17 называет `:1291` и `:1296`
— перезамер даёт `schedule.timezone = tz` на **1286** и вызов `compute_next_run_at`
открывающимся на **1290**. Разница в пять строк; строки 1278-1280 (сам дефект) совпали
точно.

**Аналог починки — в том же файле, `schedules_create:1079-1082`:**

```python
    profile_tz = user.timezone if user.timezone in VALID_TIMEZONES else "UTC"
    tz = form_data.get("timezone", profile_tz)
    if tz not in VALID_TIMEZONES:
        tz = profile_tz
```

**Аналог второй половины — `schedules_toggle:1462-1470`,** с готовым комментарием,
объясняющим ПОЧЕМУ помощник:

```python
            # ⚠️ ОТКАЗ РАСЧЁТА ОПОЗНАЁТСЯ ПО СОБЫТИЮ, А НЕ ПО ОДНОМУ ЕГО
            # ЗНАЧЕНИЮ (CR-01, перезамер 2026-09-12): на пяти формах из шести
            # вычислитель сообщает о неисполнимости ИСКЛЮЧЕНИЕМ ...
            next_run = next_run_or_none(schedule)
            if next_run is None:
                # Строка НЕ ТРОГАЕТСЯ ВОВСЕ ...
```

**Две задачи, не одна** (Ф-17): откат на `profile_tz` возвращает путь восстановления;
`next_run_or_none` убирает пятисотку. Ни одна из них не заменяет другую.

**Вселенная проверки — НЕ там, где искал бы исполнитель.** `MALFORMED_STORED_FORMS`
живёт в **`tests/test_schedules_out_of_domain_resume.py:116`** (корень `tests/`, НЕ
`tests/test_pages/`). Форма перечня (`:103-165`):

```python
@dataclass(frozen=True)
class MalformedStoredForm:
    """Одна форма СОХРАНЁННОЙ строки, неисполнимой по значениям."""

    label: str
    description: str
    days_of_week: list = field(default_factory=list)
    times_of_day: list = field(default_factory=list)
    timezone: str = "UTC"
    measured: str = ""          # ← ЗАМЕРЕННЫЙ текст отказа, не предсказанный


MALFORMED_STORED_FORMS: list[MalformedStoredForm] = [
    MalformedStoredForm(label="times-abc", ..., measured="ValueError: invalid literal for int() ..."),
    ...
    MalformedStoredForm(label="tz-mars-phobos",
        description="незнакомая зона: timezone='Mars/Phobos'",
        days_of_week=[1], times_of_day=["10:00"], timezone="Mars/Phobos",
        measured="ZoneInfoNotFoundError: No time zone found with key Mars/Phobos"),
    MalformedStoredForm(label="days-str-1", ..., measured="None — ЕДИНСТВЕННЫЙ исход, закрытый прошлой партией"),
]
```

`tz-mars-phobos` — ровно форма CR-01. **Тест фазы обязан импортировать этот перечень, а
не заводить свой.**

**Второй аналог — засев и порча строки напрямую через `db_session`:**
`tests/test_pages/test_schedules_poisoned_row.py` (шапка `:1-22` объявляет линии защиты
и образец засева: `tests/test_pages/test_schedules_list.py`). Это готовый образец
integration-теста CR-01 в `tests/test_pages/test_editor_schedules.py`.

---

### `15-PROHIBITIONS-SUBJECT.md`

**Аналог:** `.planning/phases/10-rychag-components-modal-html/10-PROHIBITIONS-SUBJECT.md`
(467 строк). Форма шапки (`:1-36`) — копировать дословно вместе с ⚠️-комментариями:

```yaml
---
phase: 10
slug: rychag-components-modal-html
# ⚠️ `status: subject` — ЭТО ПРЕДМЕТ РЕШЕНИЯ, А НЕ ВЕРДИКТ. Поля вердикта здесь НЕТ НАМЕРЕННО, и
# ни одно его имя не набрано даже комментарием: исполнитель, поставивший такое поле сам, вынес бы
# вердикт вместо владельца.
status: subject
prohibitions_seventh_batch: 39
measured: 2026-09-10
# ⚠️ ПОЛЯ НИЖЕ ЗАВОДИТ ОТВЕТ ВЛАДЕЛЬЦА и идут они сверх шапки замера и после неё.
permit_branch: permit-with-record
permitted_by: chubav
permitted_on: 2026-09-10
permit_basis: 10-PROHIBITIONS-SUBJECT.md
permit_scope: seventh-batch-only
permit_applies_to_phase: false
permit_applies_to_milestone: false
permit_covers_plans: ["10-35", ...]
permit_covers_prohibitions: 39
prohibitions_unresolved_total: 200
# ⚠️ РАЗРЕШЕНИЕ НЕ ЕСТЬ СОБЛЮДЕНИЕ.
prohibitions_fully_enforced: 0
---
```

⚠️ **`permit_scope` уже имеет прецедент значения-области** (`seventh-batch-only`) —
D-04 требует писать сюда **имя класса предмета**, и форма это выдерживает.

**Форма построчной таблицы (`:118-...`) — ровно то, что требует D-04
«каждый запрет получает свою строку»:**

```
| План | Текст запрета (сокращённо) | Дескриптор | Итог | Имя правила |
|---|---|---|---|---|
| 10-35 | ТРЕТИЙ ОБРАБОТЧИК НЕ ЗАВОДИТСЯ: ... | `test` | принуждается частично | `test_the_failure_banner_registers_its_handlers_once_per_body` (`tests/test_pages/test_shell.py:2321`) — ... половина «файл не правится ни на строку» не покрыта ничем |
| 10-35 | `env(safe-area-inset-top)` НЕ ДОПИСЫВАЕТСЯ | `none` | не принуждается — по построению | правила с таким предметом в дереве нет; запись без дескриптора принуждения не имеет по построению |
```

⚠️ **Итог «принуждается частично» — четвёртое значение, которого нет в трёх диспозициях
схемы RESEARCH.md** (`enforced` / `permitted` / `unresolved`). Прецедент показывает,
что честная перепись D-05 («по 61 запрету с `verification: test` предъявляется
существование теста») почти наверняка родит именно этот четвёртый исход. Планировщик
обязан объявить его в перечне диспозиций либо сказать, почему он туда не входит.

Форма сличения «названо планом против снято замером» (`:86-96`) — прямой образец для
летописи 47 → 49 в артефакте:

```
| Величина | Названо планом | Снято замером | Расхождение |
| Седьмая партия, всего | 39 | 39 | нет |
```

---

### `15-UAT.md`

**Аналог с ЗАПОЛНЕННЫМИ отметками:** `.planning/phases/13-.../13-UAT.md`.

Шапка (`:1-19`) — машинно читаемые поля, которые читает правило самозаверения:

```yaml
---
status: complete
phase: 13-master-podklyucheniya-telegram-po-qr-na-fragmentah
requirement: FETCH-02
checks_declared: 5
walkthrough:
  date: 2026-09-21
  browser: "Chrome 152"
  os: "macOS 15"
  observer: "Александр"
  stand: "живой стенд, реальные аккаунты Telegram (слова владельца)"
  checks_marked: [1, 2, 3, 4, 5]
  divergences: 0
  marks_closed_by_owner_attestation: >-
    ЛЕТОПИСЬ ЗАКРЫТИЯ, ТРИ ХОДА. ...
---
```

Форма таблицы отметки (`13-UAT.md:92-100`) — **побайтово эта, включая курсивную
оговорку и колонки:**

```markdown
### Отметка о закрытии проверки 1

*(заполняет человек на приёмке; отметка без наблюдённого признака закрытием не считается)*

| Дата | Браузер / ОС | Кто наблюдал | Наблюдённый признак |
|---|---|---|---|
| 2026-09-21 | Chrome 152 / macOS 15 | Александр | ПОДТВЕРЖДЕНО ЛИЧНОЕ НАБЛЮДЕНИЕ владельцем ... ответ на пункт — `pass`, расхождений с ожидаемым нет. Признаки шагов 1.1–1.4 наблюдателем НЕ ДЕТАЛИЗИРОВАНЫ — клетка несёт подтверждение наблюдения, а не его описание, и это названо, а не сглажено |

---
```

⚠️ **Поправка к заданию:** у `13-UAT.md` **пять** таблиц «Отметка о закрытии»
(`checks_declared: 5`), а не девять. Копируется **форма таблицы и форма шапки**; число
таблиц определяется числом пунктов Фазы 15 (девять), и `checks_declared` обязан ему
равняться.

**Правило, которым `15-UAT.md` будет судиться** —
`tests/test_planning/test_the_walkthrough_cannot_self_certify.py`. Оно читает **ровно
эти образцы** (`:107-113`):

```python
_FRONTMATTER_FENCE = "---"
_STATE_FIELD_RE = re.compile(r"^status:\s*(?P<value>[^\s#]+)\s*$")
_DECLARED_CHECKS_RE = re.compile(r"^checks_declared:\s*(?P<value>\d+)\s*$")
_CHECK_SECTION_RE = re.compile(r"^##\s+Проверка\s+\d+", re.M)
_MARK_HEADING_RE = re.compile(r"^###\s+Отметка\b")
```

и считает строку заполненной так (`:174-180`):

```python
def _row_is_filled(row: str) -> bool:
    """Строка отметки ЗАПОЛНЕНА, если хоть одна её клетка несёт непробельное. ..."""
    return any(cell.strip() for cell in row.strip("|").split("|"))
```

**Следствия для `15-UAT.md`, снятые с исходника правила, а не с прозы:**
1. Терминальные состояния — только `{"complete", "passed"}` (`:73`). Нетерминальное
   состояние законно и правило не роняет.
2. Подзаголовок обязан начинаться `### Отметка` (`:112`); разделы проверок — `## Проверка N`
   (`:111`), иначе артефакт попадёт в изъятие правила трёх счётов (`:106`).
3. Первые две строки таблицы (шапка и разделитель) отбрасываются **по положению**
   (`_mark_table_rows`, `:150-172`) — значит таблица обязана быть сплошной, без пустых
   строк между шапкой и данными, и заканчиваться заголовком или `---`.
4. Раздел машинной улики надо ставить **под** `---` или под собственным заголовком:
   любая таблица непосредственно под `### Отметка` будет прочитана как отметка.

---

### Орган снятия плашки (D-18.3) — перезамер

**Разметка** — `app/templates/includes/htmx_error_banner.html:300` и `:301`
(две заготовки, оба `aria-label="Скрыть сообщение"`):

```html
<div id="htmx-failure-server" class="failure-stack" hidden><input type="checkbox" id="htmx-failure-server-close" class="banner-dismiss" aria-label="Скрыть сообщение">{{ alert('Действие не выполнено. ...', 'error') }}</div>
<div id="htmx-failure-network" class="failure-stack" hidden><input type="checkbox" id="htmx-failure-network-close" class="banner-dismiss" aria-label="Скрыть сообщение">{{ alert('Запрос не дошёл до сервера. ...', 'error') }}</div>
```

**CSS** — `app/static/css/app.css`, перезамер подтверждает Ф-19, а не запись долга:

| Селектор | Строка |
|---|---|
| `.failure-stack` | 1259 |
| `.failure-stack + .failure-stack` | 1263 |
| `.failure-stack[hidden] + .failure-stack` | 1266 |
| `.failure-stack:has(> .banner-dismiss:checked)` | 1330 |
| `.banner-dismiss` | 1318 |
| `.banner-dismiss::before { content: "\00d7" }` | 1327 |
| `.banner-dismiss:hover` | 1328 |
| `.banner-dismiss:focus-visible { outline: 2px solid var(--focus-ring); outline-offset: 2px; }` | **1329 — правило СУЩЕСТВУЕТ** |

⚠️ **`.failure-stack` селекторов ЧЕТЫРЕ, а не шесть** (CONTEXT.md D-18.3 и задание
говорят «шесть правил `failure-stack`»). Утверждение «`padding-right` нет ни в одном»
верно — его нет ни в одном из четырёх. Число в артефакт фазы переносить нельзя без
летописи 6 → 4.
⚠️ **`:focus-visible` уже объявлен** — машинная половина пункта 2 `human_verification`
закрывается гейтом по CSS; видимость обвода глазом и работа пробела остаются человеку
(`app.css:1255-1258` это запрещает объявлять по зелени правил).

---

### Побочные правки разметки

**Шесть мест `limit=30` — все шесть подтверждены построчно:**

| Файл:строка | Форма |
|---|---|
| `app/templates/ads/list.html:61` | `hx-get="/ads/partial?offset={{ next_offset }}&limit=30{% for k, v in ... %}"` |
| `app/templates/ads/partial_cards.html:7` | та же строка дословно |
| `app/templates/schedules/list.html:66` | `after_id={{ next_after_id }}&limit=30...` |
| `app/templates/schedules/partial_cards.html:12` | та же строка дословно |
| `app/templates/accounts/partial_cards.html:146` | `offset={{ next_offset }}&limit=30` |
| `app/templates/accounts/list.html:203` | та же строка дословно |

Идиома: **пара «страница + partial_cards» несёт ОДНУ И ТУ ЖЕ строку** — правка обязана
идти в обе половины пары одним ходом (образец обоснования —
`test_htmx_inventory.py:89-93`: «мест 12, а экранов ручного обхода 6»).

**`app/templates/components/thumb.html:30-35`** — единственный **атрибут-обработчик
события** в шаблонах:

```jinja
{% macro thumb(value, class='', lazy=false, alt='') -%}
<img src="{{ thumb_image_url(value) }}" data-full="{{ resolve_image_url(value) }}"
     {%- if class %} class="{{ class }}"{% endif %}
     {%- if lazy %} loading="lazy"{% endif %} alt="{{ alt }}"
     onerror="this.onerror=null;this.src=this.dataset.full">
{%- endmacro %}
```

⚠️ Грубый греп `onerror` по `app/templates/` даёт **два** вхождения: это и
`components/modal.html:234` — упоминание внутри Jinja-комментария. Гейт обязан
вырезать комментарии `_strip_comments()` ДО счёта, иначе объявит два места там, где
атрибут один. Ровно ловушка Ф-11 (`ads/form.html:275`), только на другом атрибуте.

---

## Shared Patterns

### 1. Маркеры pytest — регистрация УЖЕ ЕСТЬ, новых не нужно
**Источник:** `tests/conftest.py:485-497`
**Применять к:** всем новым модулям фазы

```python
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "planning: правила, чей предмет есть ЗАПИСЬ проекта (`.planning/`), а не его "
        "продукт; заведён для РАЗДЕЛЬНОГО ПРОГОНА И ДИАГНОЗА, а не для отключения",
    )
    config.addinivalue_line(
        "markers",
        "characterisation: правило ОПИСЫВАЕТ сегодняшнее поведение, признанное "
        "дефектным и записанное открытым окном, — его зелёный цвет НЕ ЕСТЬ "
        "утверждение о правильности, а красный при починке предмета означает "
        "«перепиши слепок», а не «откати починку»",
    )
```

⚠️ **Поправка к заданию: `characterisation` УЖЕ зарегистрирован** (`:492-497`). Правки
`conftest.py` фаза не требует ни для `planning`, ни для `characterisation`. План,
закладывающий такую правку, делал бы лишнюю работу.
И там же, `:478-482`, стоит запрет выключать каталог записи — цитировать при любом
`-m` в командах плана:

```python
# ... Добавление каталога в
# игнорируемые ЗАПРЕЩЕНО прохибицией плана 10-26 — и то же утверждение стои́т в
# `tests/test_planning/__init__.py`, потому что читатель приходит с обеих сторон.
```

### 2. Обход шаблонов и вырезание комментариев
**Источник:** `tests/test_templates/test_htmx_markup_gates.py:342` (`_all_templates`),
`:365` (`_strip_comments`), `:375` (`_sites`), `:387` (`_attribute_count`)
**Применять к:** `test_form_inventory.py`, обеим новым группам `test_htmx_markup_gates.py`,
группе FETCH-03, гейтам разметки органа снятия
Свой `rglob` и своё `re.sub` **не писать** — каталог параметром существует именно для
контролей от вакуума.

### 3. Сеть ручной сборки запроса
**Источник:** `tests/test_templates/test_htmx_inventory.py:708-710`
**Применять к:** группе FETCH-03

```python
# Ручная сборка запроса в шаблоне. Точка перед именем отсечена просмотром назад:
# вызов-метод чужого объекта ручной сборкой запроса не является.
MANUAL_FETCH_CALL = re.compile(r"(?<![-\w.])fetch\s*\(")
```

### 4. Ключ = путь + порядковый номер, а не текст
**Источник:** `test_htmx_inventory.py:726-736` и `:1127-1132`
**Применять к:** всем инвентарям фазы, включая тождество запрета (файл плана + индекс в
блоке) и 49 мест письма

> ⚠️ КЛЮЧ — ПУТЬ ФАЙЛА ПЛЮС ПОРЯДКОВЫЙ НОМЕР ВХОЖДЕНИЯ, А НЕ ТЕКСТ ТЕГА, И ЭТО
> ЕДИНСТВЕННОЕ МЕСТО, ГДЕ ГЕЙТ МОГ БЫ ПОТЕРЯТЬ ФРАГМЕНТ БЕСШУМНО. ... Ключ по тексту
> схлопнул бы их в одну запись, и решение о втором не принимал бы никто.

Это же и есть машинный довод против группировки запретов по тексту (D-04, Ф-02).

### 5. Абзац «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ»
**Источники:** `test_htmx_inventory.py:19-34`, `test_impersonation_gate.py:456-476`,
`test_the_walkthrough_cannot_self_certify.py:13-22`
**Применять к:** докстрингу **каждого** нового файла фазы (D-16), и сверх того —
называть, чего гейт не видит, И **отдельным правилом запрещать невидимую форму**
(приём второго уровня из `test_impersonation_gate.py`).

### 6. Прогон и его входное условие
**Источник:** `CLAUDE.md §Commands`, `.planning/codebase/TESTING.md:16`
**Применять к:** всем планам

Быстрый прогон: `uv run pytest tests/test_planning/ tests/test_templates/ -q`.
Гейт фазы: `just test`.
⚠️ **`just test` КРАСЕН сегодня без вклада фазы** —
`test_no_walkthrough_declares_itself_passed_with_empty_marks` падает на `14-UAT.md`
(9 таблиц, 0 заполненных). Закрыть может только человек, и правило само запрещает
заполнить отметки ради зелени. Это **входное условие**, а не отказ фазы.
После правок кода — `graphify update .`

---

## No Analog Found

| Файл | Роль | Поток | Основание |
|---|---|---|---|
| — | — | — | Аналог нашёлся для каждого артефакта фазы |

Но два предмета **не имеют аналога по СУЩЕСТВУ**, при наличии аналога по форме, и это
надо сказать прямо:

1. **Чтение `must_haves.prohibitions` планов.** Ни один модуль `tests/` такого не
   делает (D-06 подтверждён). Форма приходит от
   `test_the_walkthrough_cannot_self_certify.py` (разбор полей шапки `.planning/`-артефакта),
   но YAML-разбор блока `must_haves` — новый предмет. Единственный прецедент такого
   разбора в проекте — **не тест, а артефакт**: `10-PROHIBITIONS-SUBJECT.md:58-70`
   («Frontmatter каждого из 47 планов фазы разобран YAML-разбором, из него взят блок
   `must_haves.prohibitions`»), то есть разбор был ОДНОРАЗОВЫМ и в дереве не остался.
   Прибор фазы — первый исполняемый носитель этого разбора.
2. **Гейт на ТЕЛЕ продуктового модуля по `ast`.** `test_impersonation_gate.py` и
   `test_access_gate.py` разбирают **объявления** (декораторы, параметры) и прямо
   объявляют, что тела не касаются (`:371-375`). Гейт огульного `except` обязан
   обходить ИМЕННО тело (`ast.Try` / `ast.ExceptHandler`) — то есть перешагивает
   названную границу образца. Это надо объявить в его докстринге как расхождение с
   идиомой и обосновать, а не унаследовать молча.

---

## Расхождения с записью — сводка (то, что план обязан унести)

| Что записано | Что замерено сейчас | Где |
|---|---|---|
| `app/pages/schedules.py:1049-1070` (`schedules_update`) | `schedules_update` = **1181-1356**; 1049-1070 внутри `schedules_create` | `ast`-разбор файла |
| трасса `:1067` → `:1291` / `:1296` (Ф-17) | дефект `:1278-1280`, запись зоны `:1286`, `compute_next_run_at` открывается `:1290` | чтение файла |
| «шесть правил `failure-stack`» | **четыре** селектора: 1259, 1263, 1266, 1330 | `app/static/css/app.css` |
| «`MODAL_PLACES` сходится тремя счётами» | **четырьмя** (четвёртый — план 10-01) | `test_components.py:1632-1648` |
| «контроли на `tmp_path` (`:1312-1400`)» | контроли подменяют **словарь исходников**, `tmp_path` не используется | `test_htmx_inventory.py:1312-1454` |
| «`characterisation` регистрируется в `conftest.py:485`» | **уже зарегистрирован** там же, `:492-497` | `tests/conftest.py` |
| «Фаза 13 UAT — девять заполненных отметок» | **пять** (`checks_declared: 5`); форма таблицы та, что нужна | `13-UAT.md:1-19, 92-100` |
| «`MODAL_PLACES`... второй узел `modal.html:805`» | тег открыт на **805**, `hx-post` на **807** | `components/modal.html` |
| «вселенная `MALFORMED_STORED_FORMS` существует» (без пути) | `tests/test_schedules_out_of_domain_resume.py:116` — **корень `tests/`**, не `test_pages/` | грep по `tests/` |
| три диспозиции реестра (`enforced`/`permitted`/`unresolved`) | у образца есть четвёртая — **«принуждается частично»**, и она доминирует | `10-PROHIBITIONS-SUBJECT.md:120-137` |
| «единственный `onerror` в шаблонах» | атрибут один (`thumb.html:34`), но грубый грep даёт **2** — второе в комментарии `modal.html:234` | грep по `app/templates/` |
| 5 alpine / 3 htmx | подтверждено, **плюс два имени формы `_degrades_without_*`**, не попавших ни в один перечень | грep `def test` по `tests/` |

---

## Metadata

**Analog search scope:** `tests/test_planning/`, `tests/test_templates/`, `tests/test_pages/`,
`tests/test_services/`, корень `tests/`, `app/pages/`, `app/services/`, `app/templates/`,
`app/static/css/`, `.planning/phases/10-*`, `.planning/phases/13-*`
**Files scanned:** 24 (из них прочитаны построчно 13)
**Tracked-source gate:** пройден — `git ls-files` подтвердил каждый названный путь;
зеркал установки в этом дереве нет
**Orientation:** `graphify query` (граф от 2026-09-22, устарел для файлов, правленных позже —
все координаты перезамерены чтением)
**Pattern extraction date:** 2026-09-23
