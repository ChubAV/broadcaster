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

Второй предмет (план 15-25, то же решение Г-1) — УСТРОЙСТВО рычага и мест
подтверждения: десять строк того же класса. Замеры — в `15-25-SUMMARY.md`.
Здесь правила на непокрытый остаток:

* `10-01#2` — `hx-confirm` не вводится: `test_no_template_carries_hx_confirm`;
* `10-01#0` — форма-триггер признака отправки htmx не получает (глаголы кроме
  `hx-post` и `hx-boost`): `test_no_confirmation_trigger_form_carries_an_htmx_send_attribute`;
* `10-01#1` — панель снаружи любой цели подмены, по всем вызовам панели:
  `test_every_confirmation_panel_lives_outside_every_swap_target`;
* `10-01#4` — второго пустого состояния редактора во фрагменте нет:
  `test_the_editor_empty_state_is_never_instantiated_in_a_fragment`;
* `10-01#5`, `10-03#2` (ключ из позиции строки) — `id` панели выбран сервером:
  `test_every_panel_id_is_a_value_the_server_chose`;
* `10-02#2`, `10-09#3` — у макроса панели ни параметра площадки, ни новых
  параметров: `test_the_panel_macro_takes_exactly_its_declared_inputs`.
* `10-09#2` — область настойчивых уведомлений не получает программной
  фокусируемости: `test_the_alert_region_never_becomes_programmatically_focusable`.

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
* `10-01#0`: `hx-boost` назван в ЛЮБОМ шаблоне, а не только у предков
  триггеров: предка через цепь включений разбор по тексту не собирает. Правило
  строже предмета, сегодня атрибутов ноль.
* `10-01#1`: цепь предков панели собирается по тексту шаблонов — места вызова
  макроса, включения и блок раскладки. Шаблон, который никто не включает и не
  зовёт (ответ маршрута), — корень цепи; где его разметка ляжет на клиенте,
  правило не судит. Цели, названные кодом Python (`HX-Retarget`), и селекторы
  кроме `#id` (`closest`, `find`) не разбираются — сегодня тех и других ноль.
* `10-01#4`: фрагменты — строки `ads/partials/*.html` модуля маршрутов
  расписаний; шаблон, собранный из строки иначе, не виден.
* `10-01#5`: утверждается ФОРМА выражения `id` — литеральная основа, цепочка
  атрибутов с концом `.id` и позиция строки. Что за именем `.id` стоит
  первичный ключ, а не поле пользователя с таким именем, не утверждается.
* `10-02#2`, `10-09#3`: входы макроса — сигнатура исходника, `kwargs`/`varargs`
  собранного макроса и имена контекста шаблона. Глобал окружения Jinja,
  заведённый ради панели, этим правилом не виден.
* `10-09#2`: утверждаются атрибуты тега области во всех шаблонах и отсутствие
  обращений к ней по идентификатору вне тега и селектора подмены содержимого.
  Идентификатор, собранный сценарием из частей во время исполнения, не виден.
"""

import ast
import re
from pathlib import Path
from typing import NamedTuple

from jinja2 import meta

from tests.test_pages.test_hx_location_destinations import _top_level_bindings_of_template
from tests.test_templates.test_components import (
    ENV,
    MODAL_COMPONENT,
    MODAL_PLACES,
    MODAL_SIGNATURE_RE,
    VENDORED_JS_FILES,
)
from tests.test_templates.test_htmx_markup_gates import (
    MODAL_LINKAGE_UNIVERSE_FLOOR,
    MODAL_OPEN_EVENT_INDIRECTIONS,
    MODAL_OPEN_EVENT_NAMES_CALLED,
    MODAL_TRIGGER_FORMS,
    _all_templates,
    _id_stem,
    _modal_calls,
    _modal_trigger_forms,
    _scan_to_close,
    _split_top_level,
    _string_literal,
    _strip_comments,
)

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


# =============================================================================
# ГРУППА ПЛАНА 15-25: УСТРОЙСТВО РЫЧАГА И МЕСТ ПОДТВЕРЖДЕНИЯ
# =============================================================================


# --- `hx-confirm` НЕ ВВОДИТСЯ (10-01#2) ---------------------------------------

HX_CONFIRM_RE = re.compile(r"(?<![\w-])(?:data-)?hx-confirm\b")


def _hx_confirm_offences(templates: list[tuple[str, str]]) -> list[str]:
    """Жалобы: атрибут `hx-confirm` (в обоих написаниях) в поданных шаблонах."""
    return [
        f"{name}: {found}"
        for name, source in templates
        for found in HX_CONFIRM_RE.findall(_strip_comments(source))
    ]


def test_no_template_carries_hx_confirm():
    """`10-01#2`: `hx-confirm` не вводится — он вызывает браузерный `confirm()`.

    Браузерный диалог выброшен в v2.0 вместе с четырнадцатью местами, его заменила
    панель `components/modal.html`. Действующего правила не было: замер
    оркестратора 2026-09-25 не нашёл ни одного правила, которое краснело бы на
    атрибуте. Атрибут ищется в обоих написаниях (`hx-confirm`, `data-hx-confirm`)
    по всем шаблонам дерева с вырезанными комментариями.
    """
    templates = _all_templates()
    # АНТИВАКУУМ: пустой обход дал бы зелёный цвет соблюдённого правила.
    assert len(templates) > MODAL_LINKAGE_UNIVERSE_FLOOR, (
        f"обойдено шаблонов {len(templates)} — правило зеленело бы вакуумом"
    )
    offences = _hx_confirm_offences(templates)
    assert not offences, (
        "в шаблоне появился `hx-confirm`: подтверждение ушло бы в браузерный "
        "`confirm()` в обход панели (запрет 10-01#2): " + "; ".join(offences)
    )


def test_control_hx_confirm_is_named_in_both_spellings_and_not_in_comments():
    """Контроль `10-01#2`: оба написания названы с файлом, комментарии — нет."""
    violating = [
        ("a.html", '<button hx-post="/x" hx-confirm="Точно удалить?">Удалить</button>'),
        ("b.html", '<form method="post" action="/x" data-hx-confirm="Точно?"></form>'),
    ]
    named = _hx_confirm_offences(violating)
    assert [o.split(":", 1)[0] for o in named] == ["a.html", "b.html"], named

    precise = [
        ("c.html", "{# hx-confirm выброшен в v2.0 #}<div></div>"),
        ("d.html", "<!-- hx-confirm --><div></div>"),
        ("e.html", '<div data-confirmed="1" x-confirm="x"></div>'),
    ]
    assert _hx_confirm_offences(precise) == []


# --- ФОРМА-ТРИГГЕР НЕ ПОЛУЧАЕТ ПРИЗНАКА ОТПРАВКИ HTMX (10-01#0) ---------------

# Признак отправки — ЛЮБОЙ атрибут, с которым htmx шлёт запрос сам: пять глаголов
# в обоих написаниях и `hx-boost`, превращающий обычную отправку формы в запрос
# htmx. Действующее правило `test_the_trigger_form_never_carries_the_htmx_post`
# (`tests/test_pages/test_editor_schedules.py`) сличает подстроку `hx-post`, и
# замер плана 15-25 показал: `hx-delete` и `hx-boost` на теге триггера у него
# зелены.
HTMX_SEND_ATTR_RE = re.compile(
    r"(?<![\w-])((?:data-)?hx-(?:get|post|put|patch|delete|boost))\s*="
)
HX_BOOST_RE = re.compile(r"(?<![\w-])((?:data-)?hx-boost)\s*=")


def _trigger_send_offences(sources: dict[str, str]) -> list[str]:
    """Жалобы: признак отправки на форме-триггере и `hx-boost` где угодно в дереве.

    Формы-триггеры берутся счётом I гейта связки (`_modal_trigger_forms`), а не
    своим обходом. `hx-boost` наследуется формами-потомками, а предок формы может
    стоять в другом шаблоне цепи включений, которую разбор по тексту не собирает.
    Поэтому `hx-boost` назван в ЛЮБОМ шаблоне: это строже, чем нужно, и
    сознательно. Сегодня в дереве его ноль.
    """
    offences = [
        f"{key}: {attr}"
        for key, site in sorted(_modal_trigger_forms(sources).items())
        for attr in HTMX_SEND_ATTR_RE.findall(site.tag)
    ]
    for name, source in sorted(sources.items()):
        for attr in HX_BOOST_RE.findall(_strip_comments(source)):
            offences.append(f"{name}: {attr} (наследуется формами-потомками)")
    return offences


def test_no_confirmation_trigger_form_carries_an_htmx_send_attribute():
    """`10-01#0`: форма-ТРИГГЕР признака отправки htmx не получает НИКОГДА.

    Триггер с признаком слал бы запрос ВМЕСТО открытия панели, то есть выполнял
    бы необратимое действие без подтверждения. Действующее правило держит
    `hx-post` и `data-hx-post`. Здесь — остальные глаголы и `hx-boost`.
    """
    sources = dict(_all_templates())
    triggers = _modal_trigger_forms(sources)
    # АНТИВАКУУМ И СВЯЗЬ С ИНВЕНТАРЁМ: триггеров ровно столько, сколько мест
    # подтверждения насчитывает инвентарь панели. Оба числа ввезены.
    assert len(triggers) == MODAL_TRIGGER_FORMS == MODAL_PLACES, (
        f"форм-триггеров {len(triggers)}, объявлено {MODAL_TRIGGER_FORMS}, мест "
        f"подтверждения {MODAL_PLACES} — правило судило бы не те формы"
    )
    offences = _trigger_send_offences(sources)
    assert not offences, (
        "форма-триггер получила признак отправки htmx — подтверждённое действие "
        "ушло бы на сервер ВМЕСТО открытия панели (запрет 10-01#0): "
        + "; ".join(offences)
    )


def test_control_every_send_attribute_on_a_trigger_is_named():
    """Контроль `10-01#0`: глагол на триггере и `hx-boost` на предке названы.

    Точность: форма ПАНЕЛИ с `hx-post` триггером не является (у неё нет
    перехвата отправки), и тот же триггер без признака не назван.
    """
    trigger = (
        '<form method="post" action="/x/{{ x.id }}/delete"{extra} x-data '
        "x-on:submit.prevent=\"$dispatch('modal-open-x-del-{{ x.id }}')\"></form>"
    )
    for extra, expected in (
        (' hx-delete="/x/{{ x.id }}/delete"', "hx-delete"),
        (' data-hx-put="/x"', "data-hx-put"),
        (' hx-get="/x"', "hx-get"),
    ):
        named = _trigger_send_offences({"s/row.html": trigger.replace("{extra}", extra)})
        assert named == [f"s/row.html#0: {expected}"], named

    boosted = _trigger_send_offences(
        {"s/page.html": '<div hx-boost="true">' + trigger.replace("{extra}", "") + "</div>"}
    )
    assert boosted == ["s/page.html: hx-boost (наследуется формами-потомками)"], boosted

    precise = {
        "s/row.html": trigger.replace("{extra}", ""),
        "s/panel.html": '<form class="modal__form" method="post" action="/x" hx-post="/x"></form>',
        "s/note.html": '{# hx-boost="true" на теле был бы бедой #}<div></div>',
    }
    assert _trigger_send_offences(precise) == []


# --- ПАНЕЛЬ СТОИТ СНАРУЖИ ЛЮБОЙ ЦЕЛИ ПОДМЕНЫ (10-01#1) ------------------------
#
# ⚠️ ПРЕДМЕТ — ПРЕДКИ КОРНЯ ПАНЕЛИ В СОБРАННОЙ СТРАНИЦЕ, А НЕ В ОДНОМ ФАЙЛЕ.
# Панель почти везде вызывается на верхнем уровне макроса карточки, а карточка —
# внутри контейнера страницы, который её зовёт. Поэтому цепь предков собирается
# через места вызова макроса, места включения шаблона и блок раскладки, от
# которой шаблон наследует. Цепь кончается на странице раскладки либо на шаблоне,
# который никто не включает и не зовёт (фрагмент ответа).
#
# ЦЕЛЬ ПОДМЕНЫ — узел, чью разметку ответ СНОСИТ: стратегии `innerHTML`,
# `outerHTML`, `delete`, `textContent` и внеполосное `true`. Стратегии вставки
# (`beforeend` и соседние) детей цели не трогают, и панель внутри такой цели
# живёт: так стоят панели расписаний внутри `#sched-list`, куда создание
# вставляет новую карточку в конец. Умолчание `hx-swap` в проекте — `innerHTML`
# (`includes/htmx_config.html` его не переопределяет).

PANEL_MACRO = "modal"
DESTROYING_SWAPS = frozenset({"innerHTML", "outerHTML", "delete", "textContent", "true"})
VOID_ELEMENTS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
     "param", "source", "track", "wbr"}
)
MARKUP_TOKEN_RE = re.compile(
    r"<(?P<close>/?)(?P<tag>[a-zA-Z][\w-]*)"
    r"(?P<attrs>(?:[^>\"'{]|\"[^\"]*\"|'[^']*'|\{\{.*?\}\}|\{%.*?%\}|\{)*)>"
    r"|\{%-?\s*(?P<kw>macro|endmacro|block|endblock|call|include)\b(?P<rest>.*?)-?%\}"
    r"|(?<![\w.])(?P<name>\w+)\s*\(",
    re.S,
)
OPEN_TAG_RE = re.compile(
    r"<[a-zA-Z][\w-]*(?:[^>\"'{]|\"[^\"]*\"|'[^']*'|\{\{.*?\}\}|\{%.*?%\}|\{)*>", re.S
)
EXTENDS_RE = re.compile(r"\{%-?\s*extends\s+[\"']([^\"']+)[\"']")
FROM_IMPORT_RE = re.compile(r"\{%-?\s*from\s+[\"']([^\"']+)[\"']\s+import\s+([^%]*?)-?%\}")
ID_ATTR_RE = re.compile(r"\sid=\"([^\"]*)\"")
REQUEST_ATTR_RE = re.compile(r"(?<![\w-])(?:data-)?hx-(?:get|post|put|patch|delete)\s*=")
JINJA_OUTPUT_RE = re.compile(r"\{\{.*?\}\}", re.S)
WRAPPER_TARGET_LITERAL_RE = re.compile(r"[\"'](#[^\"']*)[\"'](\s*~)?")


class PanelSite(NamedTuple):
    """Место в шаблоне: вызов или включение, его макрос, блок и открытые предки."""

    kind: str
    name: str
    macro: str | None
    block: str | None
    ancestors: tuple[str, ...]


def _attr(tag: str, name: str) -> str | None:
    found = re.search(rf"(?<![\w-])(?:data-)?{re.escape(name)}\s*=\s*\"([^\"]*)\"", tag)
    return found.group(1) if found else None


def _id_skeleton(value: str) -> str:
    """Скелет идентификатора: каждое `{{ … }}` — `{}`."""
    return JINJA_OUTPUT_RE.sub("{}", value)


def _scan_template(source: str) -> tuple[list[PanelSite], dict[str, tuple[str, ...]], list[str]]:
    """Места вызовов и включений, открытые предки блоков раскладки, ошибки разбора.

    Предки считаются от начала ближайшей рамки — макроса или блока: всё, что
    открыто выше неё, к месту вызова макроса отношения не имеет.
    """
    text = _strip_comments(source)
    stack: list[str] = []
    frames: list[tuple[str, str, int]] = []
    sites: list[PanelSite] = []
    blocks: dict[str, tuple[str, ...]] = {}
    problems: list[str] = []
    for token in MARKUP_TOKEN_RE.finditer(text):
        if token.group("tag"):
            tag = token.group("tag").lower()
            if token.group("close"):
                if stack and re.match(rf"<{re.escape(tag)}\b", stack[-1], re.I):
                    stack.pop()
                else:
                    problems.append(f"</{tag}> не закрывает открытый узел")
            elif tag not in VOID_ELEMENTS and not token.group("attrs").rstrip().endswith("/"):
                stack.append(token.group(0))
            continue
        keyword = token.group("kw")
        if keyword in ("macro", "block"):
            name = re.match(r"\s*(\w+)", token.group("rest")).group(1)
            if keyword == "block":
                blocks[name] = tuple(stack)
            frames.append((keyword, name, len(stack)))
            continue
        if keyword in ("endmacro", "endblock"):
            if frames:
                frames.pop()
            continue
        macro = next((name for kind, name, _ in reversed(frames) if kind == "macro"), None)
        block = next((name for kind, name, _ in reversed(frames) if kind == "block"), None)
        local = tuple(stack[frames[-1][2] if frames else 0 :])
        if keyword == "call":
            called = re.match(r"\s*(\w+)\s*\(", token.group("rest"))
            if called:
                sites.append(PanelSite("call", called.group(1), macro, block, local))
        elif keyword == "include":
            included = re.match(r"\s*[\"']([^\"']+)[\"']", token.group("rest"))
            if included:
                sites.append(PanelSite("include", included.group(1), macro, block, local))
        elif token.group("name"):
            if text[: token.start()].rstrip().endswith("macro"):
                continue
            sites.append(PanelSite("call", token.group("name"), macro, block, local))
    return sites, blocks, problems


def _imports_macro(sources: dict[str, str], importer: str, owner: str, macro: str) -> bool:
    if importer == owner:
        return True
    return any(
        found.group(1) == owner
        and macro in [part.strip() for part in found.group(2).split(",")]
        for found in FROM_IMPORT_RE.finditer(_strip_comments(sources[importer]))
    )


def _panel_chains(sources: dict[str, str]) -> tuple[list[tuple[str, str, tuple[str, ...]]], list[str]]:
    """Цепи предков каждой панели: (шаблон вызова, корень цепи, предки сверху вниз)."""
    scanned = {name: _scan_template(source) for name, source in sources.items()}
    problems = [f"{name}: {p}" for name, (_, _, found) in scanned.items() for p in found]

    def upward(owner: str, macro: str | None, block: str | None, below: tuple[str, ...], seen):
        key = (owner, macro)
        if key in seen:
            problems.append(f"{owner}: цикл вызовов через {macro}")
            return []
        parents: list[tuple[str, str | None, str | None, tuple[str, ...]]] = []
        for name, (sites, _, _) in scanned.items():
            for site in sites:
                if macro and site.kind == "call" and site.name == macro and _imports_macro(
                    sources, name, owner, macro
                ):
                    parents.append((name, site.macro, site.block, site.ancestors))
                if not macro and site.kind == "include" and site.name == owner:
                    parents.append((name, site.macro, site.block, site.ancestors))
        layout = EXTENDS_RE.search(_strip_comments(sources[owner]))
        if not macro and block and layout:
            if layout.group(1) not in scanned or block not in scanned[layout.group(1)][1]:
                problems.append(f"{owner}: блок {block} не найден в раскладке {layout.group(1)}")
            else:
                parents.append((layout.group(1), None, None, scanned[layout.group(1)][1][block]))
        if not parents:
            return [(owner, below)]
        chains = []
        for name, parent_macro, parent_block, ancestors in parents:
            chains += upward(name, parent_macro, parent_block, ancestors + below, seen | {key})
        return chains

    found: list[tuple[str, str, tuple[str, ...]]] = []
    for name, (sites, _, _) in scanned.items():
        if name == MODAL_COMPONENT:
            continue
        for site in sites:
            if site.kind == "call" and site.name == PANEL_MACRO:
                for root, ancestors in upward(name, site.macro, site.block, site.ancestors, frozenset()):
                    found.append((name, root, ancestors))
    return found, problems


def _destroying_targets(sources: dict[str, str]) -> set[str]:
    """Скелеты идентификаторов узлов, чью разметку ответ сносит.

    Три источника: внеполосные узлы (`hx-swap-oob`), атрибут `hx-target` на любом
    теге и аргумент `target` вызовов макроса-обёртки формы (умолчание его подмены
    при заданной цели — `outerHTML`, по исходнику `components/form_wrapper.html`).
    """
    targets: set[str] = set()
    for name, source in sources.items():
        text = _strip_comments(source)
        for tag in OPEN_TAG_RE.findall(text):
            oob = _attr(tag, "hx-swap-oob")
            if oob is not None:
                strategy, _, selector = oob.partition(":")
                own = ID_ATTR_RE.search(tag)
                node = selector[1:] if selector.startswith("#") else (own.group(1) if own else None)
                if strategy.split()[0] in DESTROYING_SWAPS and node:
                    targets.add(_id_skeleton(node))
            target = _attr(tag, "hx-target")
            swap = (_attr(tag, "hx-swap") or "innerHTML").split() or ["innerHTML"]
            if target and target.startswith("#") and swap[0] in DESTROYING_SWAPS:
                targets.add(_id_skeleton(target[1:]))
        for call in re.finditer(r"(?<![\w.])form_wrapper\s*\(", text):
            if text[: call.start()].rstrip().endswith("macro"):
                continue
            close = _scan_to_close(text, call.end())
            arguments = {}
            for part in _split_top_level(text[call.end() : close], ","):
                key, separator, value = part.partition("=")
                if separator:
                    arguments[key.strip()] = value.strip()
            if "target" not in arguments:
                continue
            swap = _string_literal(arguments.get("swap", "'outerHTML'"))
            if swap is not None and swap.split()[0] not in DESTROYING_SWAPS:
                continue
            for literal in WRAPPER_TARGET_LITERAL_RE.finditer(arguments["target"]):
                targets.add(literal.group(1)[1:] + ("{}" if literal.group(2) else ""))
    return targets


def _swap_target_reason(tag: str, targets: set[str]) -> str | None:
    """Почему предок — цель подмены; `None` — не цель."""
    own = ID_ATTR_RE.search(tag)
    if own and _id_skeleton(own.group(1)) in targets:
        return f"его id `{_id_skeleton(own.group(1))}` — цель подмены"
    swap = (_attr(tag, "hx-swap") or "innerHTML").split() or ["innerHTML"]
    if REQUEST_ATTR_RE.search(tag) and _attr(tag, "hx-target") is None and swap[0] in DESTROYING_SWAPS:
        return f"он сам цель своего запроса (`hx-swap` {swap[0]})"
    return None


def _panel_place_offences(sources: dict[str, str]) -> list[str]:
    """Жалобы: панель внутри узла, который ответ сносит; ошибки разбора цепей."""
    chains, problems = _panel_chains(sources)
    targets = _destroying_targets(sources)
    offences = list(problems)
    for caller, root, ancestors in chains:
        for tag in ancestors:
            reason = _swap_target_reason(tag, targets)
            if reason:
                opening = re.sub(r"\s+", " ", tag)[:80]
                offences.append(f"{caller} (цепь до {root}): панель внутри {opening} — {reason}")
    return offences


def test_every_confirmation_panel_lives_outside_every_swap_target():
    """`10-01#1`: панель не переезжает внутрь удаляемой карточки, она СНАРУЖИ любой цели подмены.

    Действующее правило `test_confirm_panel_lives_outside_the_row`
    (`tests/test_pages/test_account_groups.py`) видит один экран и одну цель —
    строку группы. Замер плана 15-25: панель перезапуска воркера, перенесённая
    внутрь контейнера опроса `#admin-workers`, у него зелена. Здесь свойство
    утверждается для всех вызовов панели и всех целей подмены дерева.
    """
    sources = dict(_all_templates())
    chains, problems = _panel_chains(sources)
    # АНТИВАКУУМ: цепи есть, их вызовы — те же, что видит гейт связки, и каждая
    # основа имени события, зовомая триггерами мест подтверждения, стоит у
    # проверенной панели. Перечень основ ввезён, а не переписан.
    assert not problems, "разбор цепей панели разошёлся с разметкой: " + "; ".join(problems)
    callers = {caller for caller, _, _ in chains}
    assert chains and callers == {name for name, _ in _modal_calls(sources)}, (
        f"панели найдены в {sorted(callers)}, гейт связки видит вызовы в "
        f"{sorted({name for name, _ in _modal_calls(sources)})}"
    )
    stems = {
        _id_stem(arguments["id"], sources)
        for name, arguments in _modal_calls(sources)
        if name in callers and "id" in arguments
    }
    assert stems == MODAL_OPEN_EVENT_NAMES_CALLED, (
        f"основы проверенных панелей {sorted(stems)} разошлись с основами, "
        f"которые зовут триггеры: {sorted(MODAL_OPEN_EVENT_NAMES_CALLED)}"
    )
    assert _destroying_targets(sources), "целей подмены не найдено — правило вакуумно"

    offences = _panel_place_offences(sources)
    assert not offences, (
        "панель подтверждения стоит ВНУТРИ узла, который ответ сносит: подмена "
        "унесёт открытую панель вместе с состоянием клиента (запрет 10-01#1): "
        + "; ".join(offences)
    )


def test_control_a_panel_inside_a_swap_target_is_named_and_beside_it_is_not():
    """Контроль `10-01#1`: цель обёртки, внеполосный узел и контейнер опроса названы.

    Цепь проходит через макрос карточки, как на живых экранах. Точность: панель
    рядом с целью и панель внутри цели ВСТАВКИ (`beforeend`) не названы.
    """
    row = (
        '{% from "components/modal.html" import modal %}'
        "{% macro row(x) %}<article id=\"row-{{ x.id }}\"><p>{{ x.id }}</p>"
        "{{ modal(id='x-del-' ~ x.id, title='t', action='/x', confirm_label='c') }}"
        "</article>{% endmacro %}"
    )
    page = (
        '{% from "s/row.html" import row %}'
        "{% call form_wrapper(action='/x', target='#row-' ~ x.id) %}{% endcall %}"
        '<div data-list>{{ row(x) }}</div>'
    )
    named = _panel_place_offences({"s/row.html": row, "s/page.html": page})
    assert len(named) == 1 and "row-{}" in named[0] and named[0].startswith("s/row.html"), named

    oob = {
        "s/page.html": "<div id=\"box\">{{ modal(id='y', title='t', action='/y', confirm_label='c') }}</div>",
        "s/response.html": '<div id="box" hx-swap-oob="true"></div>',
    }
    assert any("`box`" in o for o in _panel_place_offences(oob)), _panel_place_offences(oob)

    polled = {
        "s/page.html": '<div id="poll" hx-get="/p" hx-trigger="every 5s">'
        "{{ modal(id='z', title='t', action='/z', confirm_label='c') }}</div>"
    }
    assert any("сам цель своего запроса" in o for o in _panel_place_offences(polled))

    precise = {
        "s/row.html": row.replace("</article>{% endmacro %}", "{% endmacro %}").replace(
            "<p>{{ x.id }}</p>", "<p>{{ x.id }}</p></article>"
        ),
        "s/page.html": page,
        "s/list.html": "{% call form_wrapper(action='/n', target='#list', swap='beforeend') %}{% endcall %}"
        "<div id=\"list\">{{ modal(id='w', title='t', action='/w', confirm_label='c') }}</div>",
    }
    assert _panel_place_offences(precise) == [], _panel_place_offences(precise)


# --- ВТОРОГО ПУСТОГО СОСТОЯНИЯ РЕДАКТОРА ВО ФРАГМЕНТЕ НЕТ (10-01#4) ----------

EDITOR_TEMPLATE = "ads/form.html"
EDITOR_EMPTY_STATE_TEXT = "Расписаний пока нет — объявление не будет отправляться"
SCHEDULE_ROUTES_MODULE = PROJECT_ROOT / "app" / "pages" / "schedules.py"
SCHEDULE_FRAGMENT_TEMPLATE_RE = re.compile(r"ads/partials/[\w/]+\.html")
TEMPLATE_EDGE_RE = re.compile(r"\{%-?\s*(?:include|from|import)\s+[\"']([^\"']+)[\"']")
EMPTY_STATE_CALL_RE = re.compile(r"(?<![\w.])empty_state\s*\(\s*(?:'([^']*)'|\"([^\"]*)\")?")
EMPTY_CLASS_RE = re.compile(r"class=\"(?:[^\"]*\s)?empty(?:\s[^\"]*)?\"")
EMPTY_STATE_COMPONENT = "components/empty_state.html"

# Пустые состояния, которые шаблоны фрагментов редактора печатают законно, с
# первым аргументом. ⚠️ СНЯТО С ДЕРЕВА 2026-09-25 (план 15-25): замыкание трёх
# фрагментов маршрутов расписаний по включениям и ввозам дало одно такое место —
# карточка расписания без подключённого аккаунта. Пустого состояния СПИСКА
# расписаний среди них нет, и появиться оно не имеет права.
EDITOR_FRAGMENT_EMPTY_STATES: dict[str, tuple[str, ...]] = {
    "ads/includes/sched_card.html": ("Сначала подключите аккаунт мессенджера",),
}


def _schedule_fragment_roots(module_source: str) -> list[str]:
    """Шаблоны, которые маршруты расписаний отдают фрагментом: строки модуля по AST."""
    return sorted(
        {
            node.value
            for node in ast.walk(ast.parse(module_source))
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and SCHEDULE_FRAGMENT_TEMPLATE_RE.fullmatch(node.value)
        }
    )


def _template_closure(roots: list[str], sources: dict[str, str]) -> list[str]:
    """Корни и всё, что они включают и откуда ввозят, транзитивно."""
    seen: list[str] = []
    pending = list(roots)
    while pending:
        name = pending.pop(0)
        if name in seen or name not in sources:
            continue
        seen.append(name)
        pending += TEMPLATE_EDGE_RE.findall(_strip_comments(sources[name]))
    return seen


def _editor_empty_state_offences(sources: dict[str, str], module_source: str) -> list[str]:
    """Жалобы: второй экземпляр пустого состояния редактора во фрагменте."""
    offences = []
    for name in _template_closure(_schedule_fragment_roots(module_source), sources):
        if name == EMPTY_STATE_COMPONENT:
            continue
        text = _strip_comments(sources[name])
        calls = tuple(
            (single if single is not None else double)
            for single, double in EMPTY_STATE_CALL_RE.findall(text)
        )
        if calls != EDITOR_FRAGMENT_EMPTY_STATES.get(name, ()):
            offences.append(f"{name}: пустые состояния {calls!r}")
        if EMPTY_CLASS_RE.search(text):
            offences.append(f"{name}: разметка пустого состояния собрана вручную")
    owners = sorted(
        name for name, source in sources.items()
        if EDITOR_EMPTY_STATE_TEXT in _strip_comments(source)
    )
    if owners != [EDITOR_TEMPLATE]:
        offences.append(f"текст пустого состояния редактора стоит в {owners}")
    return offences


def test_the_editor_empty_state_is_never_instantiated_in_a_fragment():
    """`10-01#4`: второй экземпляр пустого состояния редактора во фрагменте не заводится.

    Вторую половину запрета («опустевший список закрывается `HX-Location`»)
    держит действующее правило `test_the_last_schedule_goes_to_location`
    (`tests/test_pages/test_editor_schedules.py`). Первую оно не держит: замер
    плана 15-25 — пустое состояние, дописанное в узел счётчика
    `ads/partials/sched_delete_response.html` под условием нуля, у 653 правил
    трёх модулей и гейтов страниц зелено. Фрагменты берутся из модуля маршрутов
    расписаний разбором AST, их включения и ввозы — замыканием.
    """
    sources = dict(_all_templates())
    module_source = SCHEDULE_ROUTES_MODULE.read_text(encoding="utf-8")
    roots = _schedule_fragment_roots(module_source)
    # АНТИВАКУУМ: фрагменты найдены и существуют; владелец текста его несёт;
    # замыкание дошло до объявленного законного места.
    assert roots and all(root in sources for root in roots), roots
    assert set(EDITOR_FRAGMENT_EMPTY_STATES) <= set(_template_closure(roots, sources))
    assert EDITOR_EMPTY_STATE_TEXT in _strip_comments(sources[EDITOR_TEMPLATE])

    offences = _editor_empty_state_offences(sources, module_source)
    assert not offences, (
        "пустое состояние редактора заведено вторым экземпляром во фрагменте — "
        "две отрисовки одной ветки разойдутся молча (запрет 10-01#4): "
        + "; ".join(offences)
    )


def test_control_a_second_editor_empty_state_in_a_fragment_is_named():
    """Контроль `10-01#4`: вызов, текст и ручная разметка названы; дерево — нет."""
    sources = dict(_all_templates())
    module_source = SCHEDULE_ROUTES_MODULE.read_text(encoding="utf-8")
    assert _editor_empty_state_offences(sources, module_source) == []

    fragment = "ads/partials/sched_delete_response.html"
    for addition, expected in (
        ("{% if schedules_count == 0 %}{{ empty_state('Нет расписаний') }}{% endif %}", fragment),
        (EDITOR_EMPTY_STATE_TEXT, "текст пустого состояния"),
        ('<div class="empty"><span class="empty__title">Пусто</span></div>', "вручную"),
    ):
        changed = dict(sources)
        changed[fragment] = sources[fragment] + addition
        named = _editor_empty_state_offences(changed, module_source)
        assert any(expected in offence for offence in named), (addition, named)


# --- `id` ПАНЕЛИ — ВЕЛИЧИНА, ВЫБРАННАЯ СЕРВЕРОМ (10-01#5, 10-03#2) ------------
#
# `id` подставляется в ИМЯ атрибута `x-on:modal-open-{{ id }}.window`, а имена
# атрибутов не экранируются ничем. Требование к вызывающему: `id` собран из
# литеральной основы и величин, которые выбрал сервер, — первичного ключа
# (цепочка атрибутов, кончающаяся `.id`) или позиции строки (`loop.index0`).
# Ключ панели очереди приходит через макрос `queue_drop_modal_id` (косвенное имя
# ввезено из гейта связки, `MODAL_OPEN_EVENT_INDIRECTIONS`), панель повтора
# отправки — через параметр макроса `retry_modal`. Обе дороги разбираются до
# места, где величина выбрана.

SERVER_ID_TERM_RE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\.id")
ROW_POSITION_TERM_RE = re.compile(r"loop\.index0?")
ID_STEM_LITERAL_RE = re.compile(r"[a-z0-9-]*")
MACRO_DEFINITION_RE = re.compile(
    r"\{%-?\s*macro\s+(\w+)\s*\((.*?)\)\s*-?%\}(.*?)\{%-?\s*endmacro", re.S
)
JINJA_TAG_RE = re.compile(r"\{%.*?%\}", re.S)
TERM_CALL_RE = re.compile(r"(\w+)\s*\((.*)\)", re.S)
RESOLUTION_DEPTH = 4


class MacroDefinition(NamedTuple):
    template: str
    name: str
    params: tuple[str, ...]
    body: str
    start: int
    end: int


def _macro_definitions(sources: dict[str, str]) -> list[MacroDefinition]:
    found = []
    for template, source in sources.items():
        text = _strip_comments(source)
        for match in MACRO_DEFINITION_RE.finditer(text):
            params = tuple(
                part.split("=", 1)[0].strip()
                for part in _split_top_level(match.group(2), ",")
                if part.strip()
            )
            found.append(
                MacroDefinition(template, match.group(1), params, match.group(3), match.start(), match.end())
            )
    return found


def _bind(arguments: str, params: tuple[str, ...]) -> dict[str, str]:
    """Аргументы вызова, привязанные к именам параметров (позиционные и именованные)."""
    bound: dict[str, str] = {}
    position = 0
    for part in _split_top_level(arguments, ","):
        if not part.strip():
            continue
        key, separator, value = part.partition("=")
        if separator and re.fullmatch(r"\s*[A-Za-z_]\w*\s*", key) and not value.startswith("="):
            bound[key.strip()] = value.strip()
        elif position < len(params):
            bound[params[position]] = part.strip()
            position += 1
    return bound


def _call_sites(sources: dict[str, str], definitions: list[MacroDefinition], owner: str, name: str):
    """Места вызова макроса `name` из шаблона `owner`: (шаблон, аргументы, объемлющий макрос)."""
    sites = []
    for template, source in sources.items():
        if not _imports_macro(sources, template, owner, name):
            continue
        text = _strip_comments(source)
        for call in re.finditer(rf"(?<![\w.]){re.escape(name)}\s*\(", text):
            if text[: call.start()].rstrip().endswith("macro"):
                continue
            close = _scan_to_close(text, call.end())
            enclosing = next(
                (
                    d for d in definitions
                    if d.template == template and d.start < call.start() < d.end
                ),
                None,
            )
            sites.append((template, text[call.end() : close], enclosing))
    return sites


def _unchosen_terms(
    expression: str,
    enclosing: MacroDefinition | None,
    sources: dict[str, str],
    definitions: list[MacroDefinition],
    routes: list[str],
    depth: int = 0,
) -> list[str]:
    """Слагаемые выражения `id`, не сводящиеся к выбранной сервером величине."""
    if depth > RESOLUTION_DEPTH:
        return [f"`{expression}` — разбор глубже {RESOLUTION_DEPTH} уровней"]
    unchosen = []
    for part in _split_top_level(expression, "~"):
        term = part.strip()
        literal = _string_literal(term)
        if literal is not None:
            if not ID_STEM_LITERAL_RE.fullmatch(literal):
                unchosen.append(f"литерал {term}")
            continue
        if SERVER_ID_TERM_RE.fullmatch(term) or ROW_POSITION_TERM_RE.fullmatch(term):
            continue
        call = TERM_CALL_RE.fullmatch(term)
        if call and call.group(1) in MODAL_OPEN_EVENT_INDIRECTIONS.values():
            (definition,) = [d for d in definitions if d.name == call.group(1)]
            routes.append("косвенное имя")
            bound = _bind(call.group(2), definition.params)
            body = JINJA_TAG_RE.sub("", definition.body)
            if not ID_STEM_LITERAL_RE.fullmatch(JINJA_OUTPUT_RE.sub("", body).strip()):
                unchosen.append(f"тело {definition.name} печатает не только основу")
            for output in JINJA_OUTPUT_RE.findall(body):
                head, dot, rest = output[2:-2].strip().partition(".")
                if head not in bound:
                    unchosen.append(f"{definition.name}: `{output}` не из параметров")
                    continue
                unchosen += _unchosen_terms(
                    bound[head] + dot + rest, enclosing, sources, definitions, routes, depth + 1
                )
            continue
        if enclosing is not None and term in enclosing.params:
            routes.append("параметр макроса")
            sites = _call_sites(sources, definitions, enclosing.template, enclosing.name)
            if not sites:
                unchosen.append(f"`{term}` — у макроса {enclosing.name} нет вызовов")
            for template, arguments, outer in sites:
                value = _bind(arguments, enclosing.params).get(term)
                if value is None:
                    unchosen.append(f"{template}: {enclosing.name} зовётся без `{term}`")
                    continue
                unchosen += [
                    f"{template}: {found}"
                    for found in _unchosen_terms(value, outer, sources, definitions, routes, depth + 1)
                ]
            continue
        unchosen.append(f"`{term}`")
    return unchosen


def _panel_id_offences(sources: dict[str, str]) -> tuple[list[str], int, list[str]]:
    """Жалобы, число разобранных вызовов панели и пройденные дороги разбора."""
    definitions = _macro_definitions(sources)
    (component,) = [d for d in definitions if d.template == MODAL_COMPONENT and d.name == PANEL_MACRO]
    offences: list[str] = []
    routes: list[str] = []
    checked = 0
    for template, arguments, enclosing in _call_sites(sources, definitions, MODAL_COMPONENT, PANEL_MACRO):
        if template == MODAL_COMPONENT:
            continue
        checked += 1
        expression = _bind(arguments, component.params).get("id")
        if expression is None:
            offences.append(f"{template}: панель вызвана без `id`")
            continue
        for term in _unchosen_terms(expression, enclosing, sources, definitions, routes):
            offences.append(f"{template}: id `{expression}` — {term}")
    return offences, checked, routes


def test_every_panel_id_is_a_value_the_server_chose():
    """`10-01#5` и ключевая половина `10-03#2`: `id` панели выбран сервером.

    `10-01#5`: требование к вызывающему `modal()` не ослабляется. `10-03#2`: ключ
    панели очереди собран из ПОЗИЦИИ строки, перевести его на идентификатор задачи
    нельзя (решение безопасности WR-04). Действующее правило
    `test_a_queue_task_id_never_reaches_a_dom_identifier`
    (`tests/test_pages/test_admin_panel.py`) держит одно место из восемнадцати,
    и только на враждебной величине. Замер плана 15-25: ключ из идентификатора
    задачи, пропущенного через `urlencode` и срезку `%` и `/`, у него зелен
    (347 правил трёх модулей). Здесь каждый вызов панели разобран до величины.
    """
    sources = dict(_all_templates())
    offences, checked, routes = _panel_id_offences(sources)
    # АНТИВАКУУМ: разобраны все вызовы, которые видит гейт связки, и обе
    # непрямые дороги пройдены хотя бы раз.
    assert checked == len(_modal_calls(sources)) > 0, (
        f"разобрано вызовов панели {checked}, гейт связки видит {len(_modal_calls(sources))}"
    )
    assert {"косвенное имя", "параметр макроса"} <= set(routes), routes
    assert not offences, (
        "`id` панели собран не из величины, выбранной сервером: он станет ИМЕНЕМ "
        "атрибута, а имена атрибутов не экранируются (запреты 10-01#5, 10-03#2): "
        + "; ".join(offences)
    )


def test_control_an_unchosen_panel_id_is_named_on_every_road():
    """Контроль `10-01#5`/`10-03#2`: прямой вызов, косвенное имя и параметр макроса.

    Точность: ключ из первичного ключа и позиции строки не назван.
    """
    component = (
        '{% macro modal(id, title, action, confirm_label, body=None) -%}'
        '<div x-on:modal-open-{{ id }}.window="show()"></div>{%- endmacro %}'
    )
    queue_macro = (
        "{%- macro queue_drop_modal_id(account, index) -%}"
        "queue-drop-{{ account.id }}-{{ index }}{%- endmacro -%}"
    )
    retry = (
        '{% from "components/modal.html" import modal %}'
        "{% macro retry_modal(log_id) -%}{{ modal(id='h-' ~ log_id, title='t', action='/h', "
        "confirm_label='c') }}{%- endmacro %}"
    )

    def offences(page: str, retry_call: str = "{{ retry_modal(log.id) }}") -> list[str]:
        return _panel_id_offences(
            {
                MODAL_COMPONENT: component,
                "s/row.html": queue_macro,
                "s/retry.html": retry,
                "s/detail.html": '{% from "s/retry.html" import retry_modal %}' + retry_call,
                "s/page.html": '{% from "components/modal.html" import modal %}'
                '{% from "s/row.html" import queue_drop_modal_id %}' + page,
            }
        )[0]

    clean = (
        "{% for row in rows %}{% call modal(id=queue_drop_modal_id(entry.account, loop.index0), "
        "title='t', action='/q', confirm_label='c') %}{% endcall %}{% endfor %}"
        "{{ modal(id='acc-del-' ~ account.id, title='t', action='/a', confirm_label='c') }}"
    )
    assert offences(clean) == []

    named = offences(clean.replace("account.id,", "account.name,"))
    assert len(named) == 1 and "`account.name`" in named[0], named
    sanitized = "row.task_id|urlencode|replace('%', '')|replace('/', '')"
    named = offences(clean.replace("loop.index0", sanitized))
    assert len(named) == 1 and "task_id" in named[0], named
    named = offences(clean, retry_call="{{ retry_modal(log.group_name) }}")
    assert len(named) == 1 and "log.group_name" in named[0], named


# --- ВХОДЫ МАКРОСА ПАНЕЛИ — ОБЪЯВЛЕННАЯ СИГНАТУРА, И ТОЛЬКО ОНА (10-02#2, 10-09#3)
#
# ⚠️ ЛИТЕРАЛ СНЯТ С ДЕРЕВА 2026-09-25 (план 15-25), а не набран по памяти.
# Летопись: план 10-09 снял параметр глагола формы (`WR-03`, рядом с сигнатурой в
# `components/modal.html` стоит его пометка), план 10-02 запретил параметр
# площадки приземления, и план 10-09 запретил вводить новые параметры взамен
# снятого. Правка литерала ВМЕСТЕ с макросом есть снятие этих запретов, а такое
# решение принимает владелец.
MODAL_MACRO_SIGNATURE = (
    'id, title, action, confirm_label, body=None, cancel_label="Отмена", '
    'confirm_variant="danger"'
)


def _panel_input_offences(source: str) -> list[str]:
    """Жалобы: входы макроса панели в поданном исходнике шаблона сверх объявленных.

    Три дороги, по которым параметр возвращается под другим именем: сигнатура
    исходника; имена `kwargs`/`varargs` в теле, с которыми собранный макрос
    принимает ЛЮБЫЕ лишние аргументы, не меняя сигнатуры; имя контекста шаблона,
    которое тело читает, но нигде не объявляет.
    """
    offences = []
    declared = MODAL_SIGNATURE_RE.search(_strip_comments(source))
    written = re.sub(r"\s+", " ", declared.group(1)).strip() if declared else None
    if written != MODAL_MACRO_SIGNATURE:
        offences.append(f"сигнатура {written!r}, объявлена {MODAL_MACRO_SIGNATURE!r}")
    compiled = getattr(ENV.from_string(source).module, PANEL_MACRO)
    names = tuple(part.split("=", 1)[0].strip() for part in MODAL_MACRO_SIGNATURE.split(", "))
    if tuple(compiled.arguments) != names:
        offences.append(f"собранный макрос принимает {compiled.arguments}, объявлено {names}")
    if compiled.catch_kwargs or compiled.catch_varargs:
        offences.append("тело читает `kwargs`/`varargs` — макрос принимает лишние аргументы")
    undeclared = meta.find_undeclared_variables(ENV.parse(source))
    if undeclared:
        offences.append(f"тело читает имена контекста {sorted(undeclared)}")
    return offences


def test_the_panel_macro_takes_exactly_its_declared_inputs():
    """`10-02#2`, `10-09#3`: ни параметра площадки, ни новых параметров у макроса панели.

    Действующие правила держат не это. Четвёртый счёт инвентаря
    (`test_modal_site_inventory`) и счёт IV связки утверждают, что вызывающие
    передают ПОДМНОЖЕСТВО сигнатуры, и с сигнатурой, выросшей вместе с
    вызывающими, согласны. `test_the_focus_landing_is_declared_once_and_called_twice`
    считает литерал площадки в отрисовке с умолчаниями, и параметр с умолчанием
    `'notice'` у него зелен (замер плана 15-25).
    """
    source = (TEMPLATES_DIR / MODAL_COMPONENT).read_text(encoding="utf-8")
    offences = _panel_input_offences(source)
    assert not offences, (
        "у макроса панели появился вход сверх объявленной сигнатуры — решение, "
        "принимаемое один раз на все места, стало решением каждого вызова "
        "(запреты 10-02#2, 10-09#3): " + "; ".join(offences)
    )


def test_control_a_returned_parameter_is_named_on_every_road():
    """Контроль `10-02#2`/`10-09#3`: лишний параметр, `kwargs` и имя контекста названы."""
    source = (TEMPLATES_DIR / MODAL_COMPONENT).read_text(encoding="utf-8")
    assert _panel_input_offences(source) == []
    signature = 'confirm_variant="danger")'
    landing = "const home = document.getElementById('notice');"
    assert source.count(signature) == 1 and source.count(landing) == 1, (
        "места подстановки контроля не найдены ровно по одному разу"
    )

    with_parameter = source.replace(signature, 'confirm_variant="danger", landing="notice")').replace(
        landing, "const home = document.getElementById('{{ landing }}');"
    )
    assert any("сигнатура" in o for o in _panel_input_offences(with_parameter))

    with_kwargs = source.replace(
        landing, "const home = document.getElementById('{{ kwargs.get(\"landing\", \"notice\") }}');"
    )
    assert any("kwargs" in o for o in _panel_input_offences(with_kwargs))

    with_context = source.replace(landing, "const home = document.getElementById('{{ panel_landing }}');")
    assert any("panel_landing" in o for o in _panel_input_offences(with_context))


# --- НАСТОЙЧИВАЯ ОБЛАСТЬ УВЕДОМЛЕНИЙ НЕ ФОКУСИРУЕТСЯ (10-09#2) ----------------

ALERT_REGION_ID = "notice-alert"
FOCUSABILITY_ATTR_RE = re.compile(
    r"(?<![\w-])(?:x-bind:|:)?(tabindex|contenteditable|autofocus)\b", re.I
)
ALERT_REGION_TAG_RE = re.compile(
    r"<[a-zA-Z][\w-]*(?:[^>\"']|\"[^\"]*\"|'[^']*')*\sid=\"notice-alert\""
    r"(?:[^>\"']|\"[^\"]*\"|'[^']*')*>",
    re.S,
)
ALERT_REGION_OOB_SELECTOR_RE = re.compile(r"hx-swap-oob=\"[A-Za-z]+:#notice-alert\"")


def _alert_region_offences(
    templates: list[tuple[str, str]], scripts: list[tuple[str, str]]
) -> tuple[list[str], int]:
    """Жалобы и число тегов настойчивой области в поданных шаблонах.

    Законных упоминаний идентификатора области два вида: атрибут `id` её тега и
    селектор внеполосной подмены СОДЕРЖИМОГО (`innerHTML:#notice-alert`). Любое
    другое упоминание — обращение сценария к узлу по идентификатору, то есть
    дорога, по которой признак фокусируемости ставится в обход тега.
    """
    offences = []
    regions = 0
    for name, source in templates:
        text = _strip_comments(source)
        tags = ALERT_REGION_TAG_RE.findall(text)
        regions += len(tags)
        for tag in tags:
            for attr in FOCUSABILITY_ATTR_RE.findall(tag):
                offences.append(f"{name}: тег области несёт `{attr}`")
        allowed = len(tags) + len(ALERT_REGION_OOB_SELECTOR_RE.findall(text))
        mentioned = text.count(ALERT_REGION_ID)
        if mentioned > allowed:
            offences.append(
                f"{name}: к области обращаются по идентификатору вне тега и "
                f"селектора подмены ({mentioned - allowed})"
            )
    for name, source in scripts:
        if ALERT_REGION_ID in source:
            offences.append(f"static/js/{name}: сценарий обращается к области")
    return offences, regions


def test_the_alert_region_never_becomes_programmatically_focusable():
    """`10-09#2`: область настойчивых уведомлений НЕ получает программной фокусируемости.

    Действующее правило `test_the_landing_region_exists_in_the_shell_of_both_apps`
    (`tests/test_templates/test_components.py`) читает тег области в
    `includes/notice_area.html` и краснеет на `tabindex` в нём. Внеполосную
    подмену области узлом держат гейты долгоживущих областей
    `tests/test_templates/test_htmx_markup_gates.py`. Сценарий, ставящий
    `tabIndex` узлу по идентификатору, у обоих зелен (замер плана 15-25: строка в
    `show()` панели). Здесь тег области утверждается во ВСЕХ шаблонах, а
    обращение к области по идентификатору — вне тега и селектора подмены.
    """
    offences, regions = _alert_region_offences(_all_templates(), _script_sources())
    assert regions == 1, f"тегов настойчивой области {regions}, а не один — правило вакуумно"
    assert not offences, (
        "настойчивая область уведомлений может стать фокусируемой — площадок "
        "приземления станет две (запрет 10-09#2): " + "; ".join(offences)
    )


def test_control_a_focusable_alert_region_is_named_on_every_road():
    """Контроль `10-09#2`: атрибут тега, привязка и сценарий названы; подмена содержимого — нет."""
    region = '<div id="notice-alert" role="alert" aria-live="assertive"{extra}></div>'
    for extra in (' tabindex="-1"', ' x-bind:tabindex="-1"', ' :tabindex="-1"'):
        named, _ = _alert_region_offences([("a.html", region.replace("{extra}", extra))], [])
        assert len(named) == 1 and "tabindex" in named[0], named
    scripted = region.replace("{extra}", "") + (
        "<div x-data=\"{ go() { document.getElementById('notice-alert').tabIndex = -1; } }\"></div>"
    )
    named, _ = _alert_region_offences([("b.html", scripted)], [])
    assert len(named) == 1 and "по идентификатору" in named[0], named
    named, _ = _alert_region_offences([], [("c.js", "document.getElementById('notice-alert')")])
    assert named == ["static/js/c.js: сценарий обращается к области"], named

    precise = [
        ("d.html", region.replace("{extra}", "")),
        ("e.html", '<div hx-swap-oob="innerHTML:#notice-alert">текст</div>'),
        ("f.html", "{# notice-alert в комментарии #}"),
    ]
    assert _alert_region_offences(precise, []) == ([], 1)
