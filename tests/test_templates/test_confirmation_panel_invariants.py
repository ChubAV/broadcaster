"""Запреты Фазы 10 о ПОВЕДЕНИИ панели подтверждения, которые суита не держала целиком.

Предмет (план 15-24, решение владельца Г-1 «Правила сейчас», класс ответа
`require-enforcement` — план 15-12, D-04). Девять строк реестра запретов
класса `product-invariant` говорят о поведении панели
`app/templates/components/modal.html`. По каждой сперва искалось действующее
правило, и оно засчитывалось, только если краснело на синтетическом нарушении
ИМЕННО этой формулировки (замеры — в `15-24-SUMMARY.md`). Здесь стоят правила
на то, чего действующие правила НЕ держали. Каждое правило называет в
докстринге тождество своего запрета:

* `10-35#1` — выражение `x-on:htmx:after-request` формы панели не правится:
  `test_the_panel_after_request_expression_is_the_declared_literal`;
* `10-02#1` — второе определение успеха по коду ответа не заводится:
  `test_the_panel_closing_branch_reads_no_response_code`;
* `10-27#0` — ветвь условия (дизъюнкт транспорта перехода) не удаляется,
  выбрана пометка: `test_the_transport_branch_of_the_panel_condition_stays_with_its_note`;
* `10-07#0` — кнопка отказа не выпадает из обхода по клавише табуляции:
  `test_the_cancel_button_stays_in_the_tab_traversal`;
* `10-07#1` — клиентская отмена летящего запроса не вводится:
  `test_no_client_side_abort_of_a_request_in_flight`;
* `10-13#1` — штатное действие не сносит молча работающий клиентский слой
  (ветка фрагмента): `test_no_template_declares_a_top_level_binding_in_an_inline_script`.

У каждого правила есть контроль на синтетической копии: копия с нарушением
названа, исправное дерево — нет. Разборщики принимают исходник ПАРАМЕТРОМ по
образцу `_all_templates(directory)`: иначе показать зубы правила можно было бы
только словами.

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ (D-16). Рантайм здесь не исполняется: ни htmx, ни
клиентский фреймворк, ни браузер. Правила читают исходники шаблонов с
вырезанными комментариями Jinja и HTML и файлы сценариев
`app/static/js/`, кроме вендоренных (`VENDORED_JS_FILES`). Поведение панели на
реальных формах события исполняют правила `tests/test_templates/test_components.py`,
а переисполнение скрипта экрана-цели — правила
`tests/test_pages/test_hx_location_destinations.py`. Этот модуль их не
повторяет и не заменяет, он закрывает остаток. Что человек видит на экране —
предмет ручного обхода, а не этого файла. Отдельно по строкам:
* `10-07#0`: утверждаются атрибуты тега кнопки отказа и селектор перечислителя
  фокусируемых узлов ловушки фокуса. Что браузер действительно ставит фокус на
  кнопку при нажатии Tab, не утверждается.
* `10-07#1`: утверждается отсутствие форм записи отмены (`htmx:abort`,
  `.abort(`, `AbortController`, стратегии `abort`/`replace` у `hx-sync`) в
  шаблонах и несвендоренных сценариях. Вызов, собранный из строк во время
  исполнения, разбором исходника не виден.
* `10-13#1`: утверждается отсутствие объявлений `const`/`let`/`class` верхнего
  уровня в инлайн-скриптах ЛЮБОГО шаблона. Правило читает шаблоны по одному, а
  не собранную страницу, и о том, какие шаблоны рантайм подменяет повторно, не
  судит: оно строже, чем нужно, и это сознательно.
"""

import re
from pathlib import Path

from tests.test_pages.test_hx_location_destinations import _top_level_bindings_of_template
from tests.test_templates.test_components import VENDORED_JS_FILES
from tests.test_templates.test_htmx_markup_gates import _all_templates, _strip_comments

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = PROJECT_ROOT / "app" / "templates"
STATIC_JS_DIR = PROJECT_ROOT / "app" / "static" / "js"
PANEL_TEMPLATE = "components/modal.html"


def _panel_source() -> str:
    """Исходник шаблона панели с дерева, БЕЗ вырезания комментариев."""
    return (TEMPLATES_DIR / PANEL_TEMPLATE).read_text(encoding="utf-8")


# --- ВЫРАЖЕНИЕ ЗАВЕРШЕНИЯ ЗАПРОСА ФОРМЫ ПАНЕЛИ --------------------------------

AFTER_REQUEST_ATTR_RE = re.compile(r'x-on:htmx:after-request\s*=\s*"([^"]*)"')

# ⚠️ ЛИТЕРАЛ СНЯТ С ДЕРЕВА 2026-09-25 (план 15-24), а не набран по памяти.
# Летопись: выражение получило нынешний вид в плане 10-05 (второй дизъюнкт,
# транспорт перехода; основание — `10-05-SUMMARY.md`), и план 10-35 записал
# запрет его правки: «D-12 НЕ ПЕРЕОТКРЫВАЕТСЯ». Запись исходника, а не
# отрисовки: `&amp;&amp;` стоит в шаблоне так, и сличение посимвольное.
# Правка литерала ВМЕСТЕ с шаблоном есть снятие запрета `10-35#1`. Такое
# решение принимает владелец, исполнитель его не принимает.
PANEL_AFTER_REQUEST_EXPRESSION = (
    "sending = false; if ($event.detail.successful || ($event.detail.xhr "
    "&amp;&amp; $event.detail.xhr.getResponseHeader('HX-Location'))) hide()"
)


def _panel_after_request_expressions(source: str) -> list[str]:
    """Все выражения завершения запроса в исходнике БЕЗ комментариев.

    Комментарий шаблона панели сам цитирует прежнюю форму атрибута
    (`x-on:htmx:after-request="sending = false"`). Правило, читающее исходник с
    комментариями, нашло бы два выражения и судило бы цитату.
    """
    return AFTER_REQUEST_ATTR_RE.findall(_strip_comments(source))


def _after_request_expression_offences(source: str) -> list[str]:
    """Жалобы на выражение завершения запроса формы панели в поданном исходнике."""
    found = _panel_after_request_expressions(source)
    if len(found) != 1:
        return [
            f"выражений завершения запроса в шаблоне панели {len(found)}, а не одно: "
            f"{found!r}"
        ]
    if found[0] != PANEL_AFTER_REQUEST_EXPRESSION:
        return [
            "выражение завершения запроса формы панели ПРАВЛЕНО: "
            f"в шаблоне {found[0]!r}, объявлено {PANEL_AFTER_REQUEST_EXPRESSION!r}"
        ]
    return []


def test_the_panel_after_request_expression_is_the_declared_literal():
    """`10-35#1`: выражение `x-on:htmx:after-request` формы панели не правится.

    Действующее правило `test_the_panel_stays_open_when_the_server_refused_on_either_transport`
    держит половину запрета «панель при отказе остаётся ОТКРЫТОЙ». Половину
    «выражение не правится» оно не держит: правка, сохранившая открытость на
    отказе, у него зелена (запись меры покрытия плана 15-13). Эта половина
    утверждается здесь посимвольным равенством объявленному литералу.
    """
    offences = _after_request_expression_offences(_panel_source())
    assert not offences, (
        "D-12 ПЕРЕОТКРЫТ: " + "; ".join(offences) + ". Правка выражения, "
        "закрывающего панель, есть отмена чужого записанного решения боковым "
        "следствием (запрет 10-35#1)"
    )


def test_control_an_edited_after_request_expression_is_named():
    """Контроль `10-35#1`: две правки копии названы, дерево — нет.

    Первая правка сохраняет поведение (лишний пробел), вторая закрывает панель
    безусловно. Обе обязаны быть названы: запрет говорит о правке выражения, а
    не только о правке, меняющей исход.
    """
    source = _panel_source()
    assert source.count(PANEL_AFTER_REQUEST_EXPRESSION) == 1, (
        "литерал в исходнике панели не найден ровно один раз — подстановка "
        "контроля стала бы молчаливой"
    )
    assert _after_request_expression_offences(source) == []

    for edited in (
        PANEL_AFTER_REQUEST_EXPRESSION.replace("; if", ";  if"),
        "sending = false; hide()",
    ):
        copy = source.replace(PANEL_AFTER_REQUEST_EXPRESSION, edited)
        offences = _after_request_expression_offences(copy)
        assert offences and "ПРАВЛЕНО" in offences[0], (
            f"правка выражения на {edited!r} не названа: {offences!r}"
        )


# --- ВТОРОЕ ОПРЕДЕЛЕНИЕ УСПЕХА ПО КОДУ ОТВЕТА (10-02#1) -----------------------

# Чтение кода ответа или состояния запроса. Чтение ЗАГОЛОВКА (`getResponseHeader`)
# сюда не входит: дизъюнкт транспорта опознаёт транспорт, а не исход
# (`10-05-SUMMARY.md`, именованное изъятие по транспорту).
RESPONSE_CODE_READ_RE = re.compile(r"\.status(?:Text)?\b|\breadyState\b")


def _response_code_reads(expression: str) -> list[str]:
    """Обращения к коду ответа в поданном выражении."""
    return RESPONSE_CODE_READ_RE.findall(expression)


def test_the_panel_closing_branch_reads_no_response_code():
    """`10-02#1`: ветвь закрытия не заводит второго определения успеха по коду ответа.

    Действующее правило `test_the_panel_closes_only_on_a_successful_exchange`
    требует, чтобы выражение читало признак успешности события. Условие по коду
    ответа, дописанное РЯДОМ с признаком
    (`$event.detail.successful && $event.detail.xhr.status < 300`), у него
    зелено (замер плана 15-24). Здесь утверждается вторая половина запроса:
    кода ответа выражение не читает вовсе.
    """
    for expression in _panel_after_request_expressions(_panel_source()):
        reads = _response_code_reads(expression)
        assert not reads, (
            f"ветвь закрытия панели читает код ответа {reads}: в проекте "
            "завелось второе определение успеха, которое молча разойдётся с "
            "правилами `responseHandling` блока конфигурации Фазы 7 (запрет "
            f"10-02#1); выражение: {expression!r}"
        )


def test_control_a_status_condition_beside_the_event_flag_is_named():
    """Контроль `10-02#1`: условие по коду рядом с признаком события названо."""
    live = PANEL_AFTER_REQUEST_EXPRESSION
    assert _response_code_reads(live) == []

    beside = live.replace(
        "$event.detail.successful ||",
        "($event.detail.successful &amp;&amp; $event.detail.xhr.status &lt; 300) ||",
    )
    assert beside != live
    assert _response_code_reads(beside) == [".status"]

    instead = live.replace("$event.detail.successful", "$event.detail.xhr.status &lt; 400")
    assert _response_code_reads(instead) == [".status"]


# --- ВЕТВЬ ТРАНСПОРТА ПЕРЕХОДА И ЕЁ ПОМЕТКА (10-27#0) -------------------------

# Дизъюнкт условия закрытия, о котором говорит запрет, — дословно, как в исходнике.
PANEL_TRANSPORT_BRANCH = (
    "|| ($event.detail.xhr &amp;&amp; $event.detail.xhr.getResponseHeader('HX-Location'))"
)

# Заголовок пометки, выбранной планом 10-27 вместо удаления ветви. Сличается
# только заголовок: тело пометки правилось позднейшими планами (10-46 сменил
# форму ссылок), и его истинность стережёт
# `test_the_transition_response_is_assembled_in_one_declared_place`.
PANEL_TRANSPORT_BRANCH_NOTE = "ВТОРОЙ ДИЗЪЮНКТ УСЛОВИЯ ЗАКРЫТИЯ ПАНЕЛИ"


def _transport_branch_offences(source: str) -> list[str]:
    """Жалобы на ветвь транспорта и её пометку в поданном исходнике панели."""
    offences = []
    expressions = _panel_after_request_expressions(source)
    if not any(PANEL_TRANSPORT_BRANCH in expression for expression in expressions):
        offences.append(
            f"в условии закрытия панели нет ветви транспорта {PANEL_TRANSPORT_BRANCH!r}; "
            f"выражения: {expressions!r}"
        )
    note_at = source.find(PANEL_TRANSPORT_BRANCH_NOTE)
    form_at = source.find('<form class="modal__form"')
    if note_at == -1 or form_at == -1 or note_at > form_at:
        offences.append(
            f"пометки ветви («{PANEL_TRANSPORT_BRANCH_NOTE}») перед формой панели нет"
        )
    return offences


def test_the_transport_branch_of_the_panel_condition_stays_with_its_note():
    """`10-27#0`: ветвь условия НЕ УДАЛЯЕТСЯ, выбрана пометка.

    Действующее правило `test_the_panel_closes_on_the_location_transport`
    краснеет, если дизъюнкт удалить. Замена его другим условием, которое
    закрывает панель на том же транспорте (например, по коду 204), у него
    зелена, хотя ветвь удалена (замер плана 15-24). Здесь утверждается сама
    ветвь, дословно, и пометка, выбранная вместо удаления.
    """
    offences = _transport_branch_offences(_panel_source())
    assert not offences, (
        "ветвь условия закрытия панели удалена или лишилась пометки (запрет "
        "10-27#0): " + "; ".join(offences)
    )


def test_control_a_replaced_branch_or_a_removed_note_is_named():
    """Контроль `10-27#0`: копия без ветви и копия без пометки названы."""
    source = _panel_source()
    assert _transport_branch_offences(source) == []
    assert source.count(PANEL_TRANSPORT_BRANCH) == 1

    replaced = source.replace(
        PANEL_TRANSPORT_BRANCH,
        "|| ($event.detail.xhr &amp;&amp; $event.detail.xhr.status === 204)",
    )
    assert any("нет ветви" in o for o in _transport_branch_offences(replaced))

    unnoted = source.replace(PANEL_TRANSPORT_BRANCH_NOTE, "ПРИМЕЧАНИЕ")
    assert any("пометки" in o for o in _transport_branch_offences(unnoted))


# --- КНОПКА ОТКАЗА В ОБХОДЕ ПО TAB (10-07#0) ----------------------------------

CANCEL_MARKER = 'x-ref="cancel"'

# Атрибуты, выводящие элемент из обхода по Tab помимо отключённости и
# `tabindex` (их держит `test_the_cancel_button_stays_available_while_the_dismissal_is_gated`).
# Имя атрибута — целиком, с привязкой клиентского фреймворка или без неё.
CANCEL_OUT_OF_TRAVERSAL_RE = re.compile(
    r"\s(?:x-bind:|:)?(inert|hidden|x-show|x-if)(?=[\s=>])"
)

# Перечислитель фокусируемых узлов ловушки фокуса (`items()` объекта `x-data`).
TRAP_SELECTOR_RE = re.compile(r"items\(\)\s*\{[^}]*?querySelectorAll\('([^']*)'\)")

# Ветвь селектора, которой отвечает кнопка отказа: `<button type="button">` без
# отключённости. Ветвь с уточнением типа или класса её не накрывает.
CANCEL_MATCHING_BRANCH_RE = re.compile(r"^button(?::not\(\[disabled\]\))?$")


def _cancel_tag(source: str) -> str:
    """Открывающий тег кнопки отказа из исходника без комментариев."""
    stripped = _strip_comments(source)
    at = stripped.index(CANCEL_MARKER)
    start = stripped.rindex("<button", 0, at)
    return stripped[start : stripped.index(">", start) + 1]


def _cancel_traversal_offences(source: str) -> list[str]:
    """Жалобы: чем кнопка отказа выпадает из обхода по Tab в поданном исходнике."""
    offences = []
    tag = _cancel_tag(source)
    for name in CANCEL_OUT_OF_TRAVERSAL_RE.findall(tag):
        offences.append(f"у кнопки отказа атрибут {name!r}: {tag!r}")

    selectors = TRAP_SELECTOR_RE.findall(_strip_comments(source))
    if len(selectors) != 1:
        offences.append(f"перечислителей ловушки фокуса {len(selectors)}, а не один")
    elif not any(
        CANCEL_MATCHING_BRANCH_RE.match(branch.strip())
        for branch in selectors[0].split(",")
    ):
        offences.append(
            "перечислитель ловушки фокуса не накрывает кнопку отказа: "
            f"{selectors[0]!r} — Tab внутри панели её обходит"
        )
    return offences


def test_the_cancel_button_stays_in_the_tab_traversal():
    """`10-07#0`: кнопка отказа не выпадает из обхода по клавише табуляции.

    Действующее правило `test_the_cancel_button_stays_available_while_the_dismissal_is_gated`
    держит отключённость, признак занятости и `tabindex`. Атрибут `inert` и
    перечислитель ловушки фокуса, переставший накрывать кнопку, у него зелены
    (замер плана 15-24). А Tab внутри панели ведёт именно ловушка
    (`x-on:keydown.tab.prevent`): кнопка вне её перечня недостижима с клавиатуры.
    """
    offences = _cancel_traversal_offences(_panel_source())
    assert not offences, (
        "кнопка отказа выпала из обхода по Tab — отмена стала труднее "
        "подтверждения (запрет 10-07#0): " + "; ".join(offences)
    )


def test_control_an_inert_cancel_or_a_narrowed_trap_is_named():
    """Контроль `10-07#0`: `inert`, `hidden` и суженный перечислитель названы."""
    source = _panel_source()
    assert _cancel_traversal_offences(source) == []

    anchor = f'type="button" {CANCEL_MARKER}'
    assert source.count(anchor) == 1
    for attr in (" inert", " hidden", ' x-show="!sending"'):
        copy = source.replace(anchor, anchor + attr)
        assert any("атрибут" in o for o in _cancel_traversal_offences(copy)), attr

    narrowed = source.replace(
        "querySelectorAll('a[href], button:not([disabled]), ",
        "querySelectorAll('a[href], button[type=submit]:not([disabled]), ",
    )
    assert narrowed != source
    assert any("не накрывает" in o for o in _cancel_traversal_offences(narrowed))


# --- КЛИЕНТСКАЯ ОТМЕНА ЛЕТЯЩЕГО ЗАПРОСА (10-07#1) -----------------------------

ABORT_FORMS_RE = re.compile(r"htmx:abort|\.abort\s*\(|\bAbortController\b")

# Значение синхронизации запроса: атрибут `hx-sync` и именованный аргумент
# `sync` макроса-обёртки формы (`components/form_wrapper.html`).
SYNC_VALUE_RE = re.compile(r"""(?:\bhx-sync|\bsync)\s*=\s*(["'])(.*?)\1""")

# Стратегии, прерывающие летящий запрос (документация htmx, `hx-sync`).
ABORTING_SYNC_STRATEGIES = frozenset({"abort", "replace"})


def _sync_strategy(value: str) -> str:
    """Стратегия синхронизации: слово после последнего двоеточия.

    Значение без двоеточия (`closest form`) — стратегия по умолчанию, `drop`.
    """
    if ":" not in value:
        return "drop"
    tail = value.rsplit(":", 1)[1].split()
    return tail[0] if tail else ""


def _script_sources(directory: Path | None = None) -> list[tuple[str, str]]:
    """Несвендоренные файлы сценариев парами «имя — исходник»."""
    root = STATIC_JS_DIR if directory is None else directory
    if not root.exists():
        return []
    return [
        (path.relative_to(root).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(root.rglob("*.js"))
        if path.name not in VENDORED_JS_FILES
    ]


def _client_abort_offences(
    templates: list[tuple[str, str]], scripts: list[tuple[str, str]]
) -> list[str]:
    """Жалобы: места клиентской отмены летящего запроса."""
    offences = []
    for name, source in templates:
        stripped = _strip_comments(source)
        for form in ABORT_FORMS_RE.findall(stripped):
            offences.append(f"{name}: {form}")
        for _, value in SYNC_VALUE_RE.findall(stripped):
            if _sync_strategy(value) in ABORTING_SYNC_STRATEGIES:
                offences.append(f"{name}: синхронизация {value!r}")
    for name, source in scripts:
        for form in ABORT_FORMS_RE.findall(source):
            offences.append(f"static/js/{name}: {form}")
    return offences


def test_no_client_side_abort_of_a_request_in_flight():
    """`10-07#1`: клиентская отмена летящего запроса НЕ вводится вместо гейта.

    Действующего правила нет: имён с `abort` в суите ноль (замер планирования
    плана 15-24). Отмена была бы ложью другого рода: сервер к моменту обрыва
    мог уже выполнить необратимое действие.
    """
    offences = _client_abort_offences(_all_templates(), _script_sources())
    assert not offences, (
        "в шаблонах или сценариях появилась клиентская отмена летящего запроса "
        "(запрет 10-07#1): " + "; ".join(offences)
    )


def test_control_every_abort_form_is_named_and_drop_is_not():
    """Контроль `10-07#1`: каждая форма отмены названа, `this:drop` и очередь — нет."""
    violating = [
        ("a.html", '<form hx-post="/x" hx-sync="closest form:abort"></form>'),
        ("b.html", "{% call form_wrapper(action='/x', sync='this:replace') %}{% endcall %}"),
        ("c.html", "<div x-on:click=\"$dispatch('htmx:abort')\"></div>"),
        ("d.html", "<script>(function () { var c = new AbortController(); })();</script>"),
    ]
    named = _client_abort_offences(violating, [("e.js", "xhr.abort();")])
    assert [o.split(":", 1)[0] for o in named] == [
        "a.html", "b.html", "c.html", "d.html", "static/js/e.js"
    ], named

    precise = [
        ("f.html", '<form hx-post="/x" hx-sync="this:drop"></form>'),
        ("g.html", "{% call form_wrapper(action='/x', sync='this:queue last') %}{% endcall %}"),
        ("h.html", "{# hx-sync=\"closest form:abort\" #}"),
    ]
    assert _client_abort_offences(precise, []) == []


# --- ОБЪЯВЛЕНИЯ ВЕРХНЕГО УРОВНЯ В ЛЮБОМ ШАБЛОНЕ (10-13#1) ---------------------


def _top_level_binding_offences(templates: list[tuple[str, str]]) -> list[str]:
    """Жалобы: объявления верхнего уровня в инлайн-скриптах поданных шаблонов."""
    return [
        f"{name}:{line}: {keyword} {binding}"
        for name, source in templates
        for line, keyword, binding in _top_level_bindings_of_template(source)
    ]


def test_no_template_declares_a_top_level_binding_in_an_inline_script():
    """`10-13#1`: штатное действие не сносит молча работающий клиентский слой.

    Действующие правила `test_the_editor_script_survives_a_second_execution_in_the_same_realm`
    и `test_no_transition_destination_declares_a_top_level_binding_inline` держат
    ветку перехода: экран-цель заголовка `HX-Location` и его цепь шаблонов.
    Фрагмент, подменяемый повторно, у них зелен: `const` в инлайн-скрипте
    `accounts/partials/connect_status.html` не краснит ни одно из них (замер
    плана 15-24). Второе исполнение такого фрагмента падает ранней ошибкой
    языка, и единственным следом остаётся строка в консоли. Здесь то же
    свойство утверждается для ВСЕХ шаблонов дерева.
    """
    offences = _top_level_binding_offences(_all_templates())
    assert not offences, (
        "инлайн-скрипт шаблона объявляет имя на верхнем уровне: второе "
        "исполнение после подмены узла упадёт ранней ошибкой языка и молча "
        "снесёт клиентский слой (запрет 10-13#1): " + "; ".join(offences)
    )


def test_control_a_top_level_binding_in_a_fragment_is_named():
    """Контроль `10-13#1`: `const` в фрагменте назван, обёрнутый — нет."""
    named = _top_level_binding_offences(
        [("partials/x.html", "<div></div>\n<script>const PROBE = 1;</script>\n")]
    )
    assert len(named) == 1 and "PROBE" in named[0], named

    wrapped = _top_level_binding_offences(
        [("partials/y.html", "<script>(function () { const PROBE = 1; })();</script>")]
    )
    assert wrapped == []
