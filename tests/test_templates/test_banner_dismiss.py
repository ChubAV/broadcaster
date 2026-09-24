"""Гейт ОРГАНА СНЯТИЯ плашек отказа: два различимых доступных имени (план 15-07).

ПОВОД — находка 3 долга Фазы 10 (запись D-18.3,
``.planning/phases/10-rychag-components-modal-html/deferred-items.md``
§«Приёмка Фазы 10 — решение владельца 2026-09-14»). Дерево доступности
объявляет орган снятия как ``checkbox "Скрыть сообщение"``, и это имя
встречается ДВАЖДЫ — при двойной аварии в порядке обхода стоя́т два
неразличимых доступных имени (WCAG 4.1.2). Это та половина находки, которую
машина может закрыть и обязана закрыть; остальное названо ниже поимённо и
оставлено человеку.

ЛЕТОПИСЬ ЗАМЕРА ДОСТУПНЫХ ИМЁН (идиома D-30/D-32: прежнее состояние названо, а
не вычеркнуто). ``aria-label="Скрыть сообщение"`` встречался ДВАЖДЫ —
``app/templates/includes/htmx_error_banner.html:300`` (узел
``htmx-failure-server``) и ``:301`` (узел ``htmx-failure-network``); замер
2026-09-23, перезамер планирования Фазы 15 подтвердил обе координаты (Ф-19
``15-RESEARCH.md``). Запись долга D-18.3 называет это «при двойной аварии
стоя́т два неразличимых доступных имени». Снято правкой плана ``15-07``,
задача 1: два значения атрибута разведены ПО ПРЕДМЕТУ своей заготовки —
«Скрыть сообщение об отказе сервера» и «Скрыть сообщение об обрыве связи».
Прежнее значение ошибкой не было — оно было одним на две заготовки, и
неразличимость возникала только при ДВОЙНОЙ аварии; поэтому оно названо здесь,
а не вычеркнуто.

ПОЧЕМУ ПО ПРЕДМЕТУ, А НЕ ПО НОМЕРУ. Нумерация («Скрыть сообщение 1» / «2»)
неравенство строк прошла бы, а человеку на слух не сказала бы ничего. Поэтому
правило ниже утверждает не только НЕРАВЕНСТВО двух строк, но и СООТВЕТСТВИЕ
имени предмету своего узла: два разных, но перепутанных имени неравенство
прошли бы, а соответствие — нет.

ГРАНИЦА СРАВНЕНИЯ (кодировка). Шаблон читается как UTF-8, и имена сличаются
ТОЧНЫМ равенством строк кодовых точек — без нормализации Юникода и без
приведения регистра. Различие узкого неразрывного пробела и обычного здесь
считается РАЗЛИЧИЕМ: нормализация молча склеивала бы строки, которые в
разметке разные, и правило стало бы утверждать о другом тексте, чем тот, что
приходит в браузер. ⚠️ Цена этой границы названа: два имени, различающиеся
ТОЛЬКО видом пробела, прошли бы правило различимости, хотя скринридер прочтёт
их одинаково. От этого стережёт не правило различимости, а правило
соответствия предмету: признаки аварий («отказе сервера», «обрыве связи») суть
разные СЛОВА, и совпасть на слух два имени, каждое из которых несёт свой
признак и не несёт чужого, не могут.

ЛЕТОПИСЬ ЧИСЛА ПРАВИЛ ``.failure-stack``: 6 → 4 → 5 (идиома D-30/D-32). Носитель
числа ОДИН — этот файл: план 15-05 своего литерала не заводит и адресата
называет (``tests/test_templates/test_htmx_markup_gates.py``, граница
FAILURE_STACK_SELECTOR_BOUNDARY_NOTE), чтобы двух носителей одного числа не
возникло.

- «6» — запись долга D-18.3 и ``15-CONTEXT.md``: «компенсации ``padding-right``
  нет ни в одном из шести правил ``failure-stack``».
- «4» — перезамер планирования Фазы 15 (Ф-19 ``15-RESEARCH.md``), снят ЧТЕНИЕМ
  ФАЙЛА, а не вычитанием: селекторы ``app.css:1259, 1263, 1266, 1330``.
- «5» — правка плана ``15-07``, задача 2: добавлен ПЯТЫЙ селектор — блок
  компенсации перекрытия ``.failure-stack > .alert``.

ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ: на момент своей записи он был верным, и
правится не он, а числа, которые он пережил. Записи разведки
(``.planning/research/*``) НЕ ПРАВЯТСЯ. ⚠️ Утверждение записи долга
«компенсации нет ни в одном из шести» верно ПО СУЩЕСТВУ — её не было ни в
одном из ЧЕТЫРЁХ; расходится число, не вывод.

ПОЧЕМУ ОЖИДАНИЯ ВЫПИСАНЫ ЗДЕСЬ, А НЕ ВЫВЕДЕНЫ ИЗ ПРОВЕРЯЕМОГО ШАБЛОНА — дословно
по ``tests/test_templates/test_htmx_inventory.py:63-67``: тест, считающий
ожидание по коду в момент прогона, согласится с любой правкой и молча переживёт
исчезновение органа.

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ. Зелёный цвет здесь означает ровно одно: органов
снятия два, у каждого своё доступное имя, и имя соответствует предмету своего
узла. Он НЕ означает, что скринридер действительно прочтёт их различимо: дерева
доступности в суите нет, браузерного привода нет ни одного. Он НЕ означает, что
орган виден, щёлкается мышью или отвечает на пробел. И он НЕ означает, что
заготовка скрывается: скрытие выражено объявлением таблицы стилей, и его
отрисовка есть предмет глаз. Сам файл стилей запрещает подмену дословно
(``app/static/css/app.css:1255-1258``): «объявлять их пройденными по зелени
правил НЕЛЬЗЯ — окно 77 журнала записывает, чем такая подмена уже обошлась
фазе».
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import NamedTuple

from tests.test_templates.test_htmx_markup_gates import (
    APP_CSS,
    TEMPLATES_DIR,
    _all_templates,
    _app_css,
    _css_rules,
    _declaration,
    _strip_comments,
)

# --- ОБЪЯВЛЕННЫЕ ОЖИДАНИЯ ------------------------------------------------------

# Шаблон заготовок относительно каталога шаблонов.
BANNER_TEMPLATE = "includes/htmx_error_banner.html"

# Класс органа снятия. Совпадает с тем, что ищет гейт шелла
# (`FAILURE_BANNER_DISMISS_CLASS`, tests/test_pages/test_shell.py); выписан
# здесь, а не импортирован, потому что предмет этого файла — ДОСТУПНОЕ ИМЯ, и
# импорт связал бы два гейта за пределами их общего предмета.
BANNER_DISMISS_CLASS = "banner-dismiss"

# Класс узла заготовки: орган снятия принадлежит ближайшему открытому до него
# узлу этого класса.
BANNER_NODE_CLASS = "failure-stack"

# Органов снятия в дереве — ровно два, по одному на заготовку. Антивакуумное
# `> 0` утверждается отдельно: орган, исчезнувший молча, оставил бы правило
# различимости зелёным ровно тогда, когда органов не стало.
BANNER_DISMISS_CONTROLS = 2

# Узел заготовки → доступное имя его органа снятия (план 15-07, задача 1).
BANNER_DISMISS_ACCESSIBLE_NAMES: dict[str, str] = {
    "htmx-failure-server": "Скрыть сообщение об отказе сервера",
    "htmx-failure-network": "Скрыть сообщение об обрыве связи",
}

# Узел заготовки → признак СВОЕЙ аварии, который обязан стоять в имени его
# органа. Текст первой заготовки говорит «Действие не выполнено…» (сервер
# ответил отказом), второй — «Запрос не дошёл до сервера…» (связь оборвалась).
BANNER_DISMISS_SUBJECT_MARKS: dict[str, str] = {
    "htmx-failure-server": "отказе сервера",
    "htmx-failure-network": "обрыве связи",
}

# Регистраций обработчика в файле заготовок — снято ДО правки плана 15-07
# (`grep -o 'addEventListener(' … | wc -l` → 3, 2026-09-24). Рост этого числа
# отменил бы ветвь `A` решения владельца 2026-09-13 («снятие без регистрации»)
# и потребовал бы НОВОГО решения владельца.
BANNER_SCRIPT_HANDLER_REGISTRATIONS = 3

# Порог непустоты вселенной обхода: шаблонов в дереве больше пятидесяти.
TEMPLATE_UNIVERSE_FLOOR = 50

_TAG_RE = re.compile(r"<(div|input)\b[^>]*>", re.IGNORECASE)
_ID_RE = re.compile(r'\bid="([^"]*)"')
_CLASS_RE = re.compile(r'\bclass="([^"]*)"')
_ARIA_LABEL_RE = re.compile(r'\baria-label="([^"]*)"')
_HANDLER_REGISTRATION = "addEventListener("


class DismissControl(NamedTuple):
    """Орган снятия: узел заготовки, которому он принадлежит, и текст его тега."""

    owner: str
    tag: str


# --- РАЗБОРЩИКИ (принимают ИСХОДНИК ТЕКСТОМ, а не путь) ------------------------


def _banner_source(directory: Path | None = None) -> str:
    """Исходник шаблона заготовок из обхода дерева (UTF-8, как читает обход).

    Обход — ОБЩИЙ `_all_templates` гейтов разметки; своего обхода каталога не
    заводится.
    """
    for rel, source in _all_templates(directory):
        if rel == BANNER_TEMPLATE:
            return source
    return ""


def _classes(tag: str) -> list[str]:
    match = _CLASS_RE.search(tag)
    return match.group(1).split() if match else []


def _banner_dismiss_controls(source: str) -> list[DismissControl]:
    """Органы снятия в исходнике, каждый — с узлом заготовки, которому принадлежит.

    Принимает ИСХОДНИК ТЕКСТОМ: иначе контроли на синтетическом исходнике
    невыразимы. Комментарии вырезаются общим `_strip_comments` — докстринг
    шаблона называет доступное имя словами, и правило, читающее прозу,
    краснело бы на объяснении, а не на разметке.
    """
    controls: list[DismissControl] = []
    owner = ""
    for match in _TAG_RE.finditer(_strip_comments(source)):
        tag = match.group(0)
        classes = _classes(tag)
        if match.group(1).lower() == "div" and BANNER_NODE_CLASS in classes:
            id_match = _ID_RE.search(tag)
            owner = id_match.group(1) if id_match else ""
        elif match.group(1).lower() == "input" and BANNER_DISMISS_CLASS in classes:
            controls.append(DismissControl(owner, tag))
    return controls


def _accessible_names(controls: list[DismissControl]) -> dict[str, str | None]:
    """Узел заготовки → доступное имя его органа (None — имени нет вовсе)."""
    names: dict[str, str | None] = {}
    for control in controls:
        match = _ARIA_LABEL_RE.search(control.tag)
        names[control.owner] = match.group(1) if match else None
    return names


def _distinctness_findings(source: str) -> tuple[str, ...]:
    """Расхождения различимости. Пусто — у каждого органа своё непустое имя.

    Сравнение — ТОЧНОЕ, по кодовым точкам (`Counter` над строками как есть):
    без нормализации и без приведения регистра — граница названа в докстринге
    модуля.
    """
    findings: list[str] = []
    controls = _banner_dismiss_controls(source)
    labelled: list[tuple[str, str]] = []
    for control in controls:
        match = _ARIA_LABEL_RE.search(control.tag)
        if match is None or match.group(1) == "":
            findings.append(
                f"#{control.owner or '<узел без id>'}: у органа снятия НЕТ "
                "доступного имени (`aria-label` отсутствует или пуст)\n"
                f"      получено: {control.tag}\n"
                "      следствие: вспомогательная технология назовёт его "
                "«флажок» и ничем больше — пустое имя не есть «различимое»"
            )
            continue
        labelled.append((control.owner, match.group(1)))
    for name, count in sorted(Counter(label for _owner, label in labelled).items()):
        if count > 1:
            owners = [owner for owner, label in labelled if label == name]
            findings.append(
                f"доступное имя «{name}» ПОВТОРЯЕТСЯ {count} раз(а) — у узлов "
                f"{', '.join('#' + o for o in owners)}\n"
                "      следствие: при двойной аварии в порядке обхода стоя́т два "
                "неразличимых доступных имени (WCAG 4.1.2)"
            )
    return tuple(findings)


def _subject_findings(source: str) -> tuple[str, ...]:
    """Расхождения ПРЕДМЕТА: имя каждого органа несёт признак СВОЕЙ аварии и не чужой."""
    findings: list[str] = []
    names = _accessible_names(_banner_dismiss_controls(source))
    for owner, mark in BANNER_DISMISS_SUBJECT_MARKS.items():
        name = names.get(owner)
        if name is None:
            findings.append(f"#{owner}: органа снятия с доступным именем нет — сличать не с чем")
            continue
        if mark not in name:
            findings.append(
                f"#{owner}: доступное имя «{name}» НЕ несёт признака своей аварии "
                f"«{mark}»"
            )
        for other, other_mark in BANNER_DISMISS_SUBJECT_MARKS.items():
            if other != owner and other_mark in name:
                findings.append(
                    f"#{owner}: доступное имя «{name}» стои́т НЕ НА СВОЁМ узле — оно "
                    f"несёт признак «{other_mark}» аварии узла #{other}"
                )
    return tuple(findings)


def _handler_registrations(source: str) -> int:
    """Число регистраций обработчика в исходнике без комментариев."""
    return _strip_comments(source).count(_HANDLER_REGISTRATION)


# --- ПРАВИЛА -------------------------------------------------------------------


def test_the_two_dismiss_controls_have_distinct_accessible_names() -> None:
    """Доступные имена органов снятия попарно различны (WCAG 4.1.2).

    Множество имён имеет длину, равную числу органов; совпадение двух имён
    краснит правило и называет повторившееся значение.
    """
    source = _banner_source()
    findings = _distinctness_findings(source)

    assert findings == (), f"{BANNER_TEMPLATE}:\n" + "\n".join(
        f"  — {line}" for line in findings
    )
    names = [name for name in _accessible_names(_banner_dismiss_controls(source)).values()]
    assert len(set(names)) == len(names), f"имена органов не различны: {names}"


def test_the_dismiss_control_count_and_names_are_declared() -> None:
    """Органов снятия ровно `BANNER_DISMISS_CONTROLS`, и перечень равен объявленному."""
    assert BANNER_DISMISS_CONTROLS > 0, "объявлено ноль органов — правило различимости вакуумно"
    controls = _banner_dismiss_controls(_banner_source())

    assert len(controls) > 0, (
        f"в {BANNER_TEMPLATE} не найдено НИ ОДНОГО органа снятия — правило "
        "различимости зеленело бы на пустом перечне"
    )
    assert len(controls) == BANNER_DISMISS_CONTROLS, (
        f"органов снятия {len(controls)}, объявлено {BANNER_DISMISS_CONTROLS}: "
        f"{[c.owner for c in controls]}"
    )
    assert _accessible_names(controls) == BANNER_DISMISS_ACCESSIBLE_NAMES, (
        "перечень «узел заготовки → доступное имя» разошёлся с объявленным\n"
        f"      получено:  {_accessible_names(controls)}\n"
        f"      ожидалось: {BANNER_DISMISS_ACCESSIBLE_NAMES}"
    )


def test_each_dismiss_control_is_a_checkbox_without_a_text_node() -> None:
    """Каждый орган — `<input type="checkbox">` класса `banner-dismiss` без текстового узла.

    Элемент `<input>` пустой по построению: доступное имя приходит ТОЛЬКО из
    `aria-label`, поэтому его повтор и есть повтор ДОСТУПНОГО ИМЕНИ, а не
    совпадение служебного атрибута.
    """
    source = _strip_comments(_banner_source())
    controls = _banner_dismiss_controls(_banner_source())
    assert controls, "органов снятия нет — разбирать форму не у чего"
    for control in controls:
        assert control.tag.lower().startswith("<input"), control.tag
        assert 'type="checkbox"' in control.tag, (
            f"#{control.owner}: орган не есть флажок — получено {control.tag}"
        )
        assert BANNER_DISMISS_CLASS in _classes(control.tag), control.tag
    assert "</input" not in source.lower(), (
        "в исходнике заготовок есть закрывающий тег `</input>` — у органа "
        "появился текстовый узел, и доступное имя могло прийти не из `aria-label`"
    )


def test_each_accessible_name_names_its_own_failure() -> None:
    """Имя каждого органа несёт признак СВОЕЙ аварии, и ни одно не стоит на чужом узле.

    Неравенство двух строк прошли бы и два перепутанных имени; соответствие
    «узел ↔ признак в имени» — нет. Отказ называет, какое имя стои́т не на
    своём узле.
    """
    findings = _subject_findings(_banner_source())

    assert findings == (), f"{BANNER_TEMPLATE}:\n" + "\n".join(
        f"  — {line}" for line in findings
    )


def test_no_handler_registration_is_added_to_the_banner_file() -> None:
    """Регистраций обработчика в файле заготовок — ровно объявленное число.

    Ветвь `A` решения владельца 2026-09-13 («снятие без регистрации») остаётся
    в силе: правка плана 15-07 касается только двух значений `aria-label`.
    """
    found = _handler_registrations(_banner_source())

    assert found == BANNER_SCRIPT_HANDLER_REGISTRATIONS, (
        f"регистраций обработчика в {BANNER_TEMPLATE}: {found}, объявлено "
        f"{BANNER_SCRIPT_HANDLER_REGISTRATIONS} (снято ДО правки плана 15-07)\n"
        "      следствие: новая регистрация отменяет ветвь `A` решения владельца "
        "2026-09-13 и требует НОВОГО решения владельца"
    )


# --- КОНТРОЛИ ОТ ВАКУУМА -------------------------------------------------------


_SYNTHETIC_NODE = (
    '<div id="{owner}" class="failure-stack" hidden>'
    '<input type="checkbox" id="{owner}-close" class="banner-dismiss"{label}>'
    "текст</div>\n"
)


def _synthetic(*nodes: tuple[str, str | None]) -> str:
    return "".join(
        _SYNTHETIC_NODE.format(
            owner=owner, label="" if label is None else f' aria-label="{label}"'
        )
        for owner, label in nodes
    )


def test_control_repeated_accessible_names_redden() -> None:
    """Два органа с ОДИНАКОВЫМИ именами — правило краснеет и называет повтор."""
    source = _synthetic(
        ("htmx-failure-server", "Скрыть сообщение"),
        ("htmx-failure-network", "Скрыть сообщение"),
    )

    findings = _distinctness_findings(source)

    assert findings, "правило различимости зелено на двух одинаковых именах — гейт слеп"
    assert any("«Скрыть сообщение» ПОВТОРЯЕТСЯ 2" in line for line in findings), (
        f"отказ не назвал повторившееся значение: {findings}"
    )


def test_control_a_control_without_an_accessible_name_reddens() -> None:
    """Орган БЕЗ `aria-label` — правило краснеет и называет узел без имени."""
    source = _synthetic(
        ("htmx-failure-server", "Скрыть сообщение об отказе сервера"),
        ("htmx-failure-network", None),
    )

    findings = _distinctness_findings(source)

    assert findings, "правило различимости зелено на органе без имени — пустое читается «различимым»"
    assert any("#htmx-failure-network" in line and "НЕТ доступного имени" in line
               for line in findings), f"отказ не назвал узел без имени: {findings}"


def test_control_the_untouched_tree_is_a_nonempty_universe() -> None:
    """На необойдённом дереве вселенная непуста, и оба правила молчат НЕ на пустоте."""
    templates = _all_templates(TEMPLATES_DIR)
    assert len(templates) > TEMPLATE_UNIVERSE_FLOOR, (
        f"шаблонов в обходе {len(templates)}, не больше {TEMPLATE_UNIVERSE_FLOOR}"
    )
    source = _banner_source()
    assert source, f"шаблона {BANNER_TEMPLATE} в обходе нет"
    assert len(_banner_dismiss_controls(source)) == BANNER_DISMISS_CONTROLS
    assert _distinctness_findings(source) == ()
    assert _subject_findings(source) == ()


def test_control_exact_code_point_comparison_is_not_normalised() -> None:
    """Сличение по кодовым точкам: узкий неразрывный пробел ≠ обычный.

    Граница кодировки из докстринга модуля, показанная, а не заявленная:
    разборщик не нормализует строки, поэтому два имени, различающиеся только
    видом пробела, для него РАЗНЫЕ.
    """
    source = _synthetic(
        ("htmx-failure-server", "Скрыть сообщение"),
        ("htmx-failure-network", "Скрыть сообщение"),
    )

    assert _distinctness_findings(source) == (), (
        "имена с узким и обычным пробелом приравнены — сравнение нормализует строки"
    )


# =============================================================================
# Задача 2 плана 15-07: КОМПЕНСАЦИЯ ПЕРЕКРЫТИЯ ОБЪЯВЛЕНА ВЕЛИЧИНОЙ ИЗ ЗАМЕРА
# =============================================================================
#
# ПОВОД (запись долга D-18.3). Коробка органа снятия занимает 885→909 при
# содержимом `.alert`, кончающемся на 900: перекрытие 15 px, и компенсации
# `padding-right` не было ни в одном правиле `failure-stack`. ⚠️ Нарисованная
# половина замерена четвёртым обходом и оказалась у́же объявленной: видимого
# столкновения текста с крестиком НЕТ (снимок 2026-09-14, окно 1280 px). Блок
# компенсации поэтому объявляется ПО ЗАМЕРУ КОРОБКИ, а не по наблюдённому
# столкновению, — и утверждается ОБЪЯВЛЕНИЕ, а не отрисовка.
#
# ЛЕТОПИСЬ ЧИСЛА ПРАВИЛ `.failure-stack` (6 → 4 → 5) — в докстринге модуля.
#
# ⚠️ ПЕРЕСБОРКА `asset_version` — ОЖИДАЕМОЕ СЛЕДСТВИЕ, А НЕ ПОЛОМКА (FOUND-03):
# правка `app.css` сдвигает `?v=` на теге стилей, потому что версия выводится из
# байтов охвата (`app/pages/common.py`, `_compute_asset_version`).

STACK_CLASS_SELECTOR = f".{BANNER_NODE_CLASS}"

# Правил, чей селектор несёт класс стопки, — ровно пять; перечень выписан, а не
# выведен (основание — докстринг модуля).
FAILURE_STACK_RULES = 5
FAILURE_STACK_SELECTORS: tuple[str, ...] = (
    ".failure-stack",
    ".failure-stack + .failure-stack",
    ".failure-stack[hidden] + .failure-stack",
    ".failure-stack:has(> .banner-dismiss:checked)",
    ".failure-stack > .alert",
)

# Селектор блока компенсации: содержимое заготовки ПО КЛАССУ стопки, без адреса
# заготовки (`_selector_lifts_banner` требует ровно одного блока подъёма).
CLEARANCE_SELECTOR = ".failure-stack > .alert"
CLEARANCE_PROPERTY = "padding-right"

# Селектор коробки органа, из которой читаются слагаемые величины.
DISMISS_BOX_SELECTOR = f".{BANNER_DISMISS_CLASS}"

# Зазор между правым краем текста и коробкой органа. ⚠️ Рамка `.alert` (1px)
# в сумму НЕ входит нарочно: она лишь прибавляет пиксель к видимому зазору, и
# сумма остаётся наименьшей величиной, которая точно не перекрывается.
BANNER_DISMISS_CLEARANCE_GAP_PX = 8

# Объявленная компенсация: ширина органа (24px) + его отступ справа (6px) + зазор
# (8px) = 38px. Равенство этой сумме ЧИТАЕТСЯ из `.banner-dismiss` той же
# таблицы правилом ниже: правка коробки органа немедленно его краснит.
BANNER_DISMISS_CLEARANCE_PX = 38

# Блоков, ОБЪЯВЛЯЮЩИХ `--failure-banner-top`, — снято ДО правки плана 15-07
# (`app.css:1259, 1263, 1266` — роли base / offset / reset `_stack_blocks`).
BANNER_TOP_VARIABLE = "--failure-banner-top"
BANNER_TOP_VARIABLE_BLOCKS = 3

# Порог длины исходника для положительного контроля: правила молчат не на пустоте.
APP_CSS_LINE_FLOOR = 1000

_PX_RE = re.compile(r"^(-?\d+(?:\.\d+)?)px$")


def _px(value: str | None) -> float | None:
    match = _PX_RE.match(value.strip()) if value else None
    return float(match.group(1)) if match else None


def _failure_stack_selectors(css: str) -> tuple[str, ...]:
    """Селекторы правил, несущие класс стопки, в порядке файла (CSS без комментариев)."""
    return tuple(selector for selector, _body in _css_rules(css) if STACK_CLASS_SELECTOR in selector)


def _clearance_declaration(css: str) -> str | None:
    """Значение отступа справа у содержимого заготовки, объявленное по классу стопки."""
    for selector, body in _css_rules(css):
        if selector == CLEARANCE_SELECTOR:
            return _declaration(body, CLEARANCE_PROPERTY)
    return None


def _dismiss_box_metrics(css: str) -> dict[str, float | None]:
    """Ширина и отступ справа коробки органа, ПРОЧИТАННЫЕ из блока `.banner-dismiss`."""
    for selector, body in _css_rules(css):
        if selector == DISMISS_BOX_SELECTOR:
            return {"width": _px(_declaration(body, "width")), "right": _px(_declaration(body, "right"))}
    return {"width": None, "right": None}


def _banner_top_blocks(css: str) -> tuple[str, ...]:
    """Селекторы блоков, ОБЪЯВЛЯЮЩИХ величину `--failure-banner-top` (не читающих её)."""
    return tuple(
        selector for selector, body in _css_rules(css) if _declaration(body, BANNER_TOP_VARIABLE) is not None
    )


def _clearance_findings(css: str) -> tuple[str, ...]:
    """Расхождения компенсации. Пусто — объявлена и равна выведенной из замера величине."""
    declared = _clearance_declaration(css)
    if declared is None:
        return (
            f"объявления `{CLEARANCE_SELECTOR} {{ {CLEARANCE_PROPERTY}: … }}` в таблице НЕТ — "
            "компенсации перекрытия органом снятия не объявлено",
        )
    metrics = _dismiss_box_metrics(css)
    if metrics["width"] is None or metrics["right"] is None:
        return (
            f"коробка органа `{DISMISS_BOX_SELECTOR}` не читается: получено {metrics} — "
            "вывести величину компенсации не из чего",
        )
    derived = metrics["width"] + metrics["right"] + BANNER_DISMISS_CLEARANCE_GAP_PX
    findings: list[str] = []
    if derived != BANNER_DISMISS_CLEARANCE_PX:
        findings.append(
            f"объявленная `BANNER_DISMISS_CLEARANCE_PX = {BANNER_DISMISS_CLEARANCE_PX}` разошлась с "
            f"выводом из коробки органа: width {metrics['width']:g} + right {metrics['right']:g} + "
            f"зазор {BANNER_DISMISS_CLEARANCE_GAP_PX} = {derived:g}"
        )
    if _px(declared) != derived:
        findings.append(
            f"`{CLEARANCE_SELECTOR}`: объявлено `{CLEARANCE_PROPERTY}: {declared}`, а выведенная из "
            f"замера коробки величина — {derived:g}px (width {metrics['width']:g} + right "
            f"{metrics['right']:g} + зазор {BANNER_DISMISS_CLEARANCE_GAP_PX})"
        )
    return tuple(findings)


def test_failure_stack_rule_count_is_declared() -> None:
    """Правил класса стопки ровно `FAILURE_STACK_RULES`, перечень — объявленный (летопись 6 → 4 → 5)."""
    assert FAILURE_STACK_RULES > 0, "объявлено ноль правил стопки — утверждение вакуумно"
    assert len(FAILURE_STACK_SELECTORS) == FAILURE_STACK_RULES
    found = _failure_stack_selectors(_app_css())

    assert len(found) > 0, "правил класса стопки в таблице НЕТ — разбор ослеп"
    assert found == FAILURE_STACK_SELECTORS, (
        "перечень правил `.failure-stack` разошёлся с объявленным\n"
        f"      получено ({len(found)}):  {found}\n"
        f"      ожидалось ({FAILURE_STACK_RULES}): {FAILURE_STACK_SELECTORS}"
    )


def test_the_overlap_clearance_is_declared() -> None:
    """Содержимое заготовки объявляет отступ справа, равный `BANNER_DISMISS_CLEARANCE_PX`."""
    declared = _clearance_declaration(_app_css())

    assert declared is not None, (
        f"объявления `{CLEARANCE_SELECTOR} {{ {CLEARANCE_PROPERTY}: … }}` нет — компенсация "
        "перекрытия органом снятия не объявлена"
    )
    assert _px(declared) == BANNER_DISMISS_CLEARANCE_PX, (
        f"`{CLEARANCE_SELECTOR}`: `{CLEARANCE_PROPERTY}: {declared}`, объявлено "
        f"{BANNER_DISMISS_CLEARANCE_PX}px"
    )


def test_the_clearance_is_derived_from_the_dismiss_box() -> None:
    """Величина ВЫВЕДЕНА: равна ширине органа + его отступу справа + зазору, прочитанным из CSS."""
    findings = _clearance_findings(_app_css())

    assert findings == (), "app.css:\n" + "\n".join(f"  — {line}" for line in findings)


def test_no_block_declaring_the_banner_top_is_added() -> None:
    """Блоков, объявляющих `--failure-banner-top`, — ровно снятое ДО правки число."""
    found = _banner_top_blocks(_app_css())

    assert len(found) == BANNER_TOP_VARIABLE_BLOCKS, (
        f"блоков, объявляющих `{BANNER_TOP_VARIABLE}`, {len(found)}, объявлено "
        f"{BANNER_TOP_VARIABLE_BLOCKS}: {found}\n"
        "      следствие: `_stack_blocks` отнёс бы новый блок к роли смещения, и правила "
        "стопки плана 10-56 покраснели бы за ФОРМУ правки"
    )


def test_the_clearance_block_declares_no_display_mode_and_no_banner_address() -> None:
    """Блок компенсации не объявляет способа отображения и не несёт адреса заготовки."""
    bodies = [body for selector, body in _css_rules(_app_css()) if selector == CLEARANCE_SELECTOR]

    assert len(bodies) == 1, f"блоков `{CLEARANCE_SELECTOR}` {len(bodies)}, а не один"
    assert _declaration(bodies[0], "display") is None, (
        f"`{CLEARANCE_SELECTOR}` объявляет способ отображения — блок попал бы во вселенную "
        "`test_no_banner_rule_declares_a_display_mode_that_shows`"
    )
    assert _declaration(bodies[0], BANNER_TOP_VARIABLE) is None
    assert "htmx-failure" not in CLEARANCE_SELECTOR


def test_control_a_stylesheet_without_the_clearance_block_reddens() -> None:
    """Синтетический CSS без блока компенсации — правило называет отсутствующее объявление."""
    css = _app_css()
    block = f"{CLEARANCE_SELECTOR} {{ {CLEARANCE_PROPERTY}: {BANNER_DISMISS_CLEARANCE_PX}px; }}"
    assert css.count(block) == 1, (
        f"блок {block!r} встречается {css.count(block)} раз(а), а не один — подмена меняет не то место"
    )
    changed = css.replace(block, "")
    assert changed != css

    findings = _clearance_findings(changed)

    assert findings, "правило компенсации зелено на таблице без блока — гейт слеп"
    assert any("НЕТ" in line and CLEARANCE_PROPERTY in line for line in findings), (
        f"отказ не назвал отсутствующее объявление: {findings}"
    )


def test_control_an_understated_clearance_by_one_pixel_reddens() -> None:
    """Компенсация, заниженная на 1 px, — правило называет расхождение с выведенной величиной."""
    css = _app_css()
    exact = f"{CLEARANCE_PROPERTY}: {BANNER_DISMISS_CLEARANCE_PX}px;"
    assert css.count(exact) == 1, f"{exact!r} встречается {css.count(exact)} раз(а), а не один"
    changed = css.replace(exact, f"{CLEARANCE_PROPERTY}: {BANNER_DISMISS_CLEARANCE_PX - 1}px;")

    findings = _clearance_findings(changed)

    assert findings, "правило вывода зелено на величине, заниженной на 1 px — подобранное число прошло"
    assert any(f"{BANNER_DISMISS_CLEARANCE_PX - 1}px" in line and f"{BANNER_DISMISS_CLEARANCE_PX}px" in line
               for line in findings), f"отказ не назвал расхождение: {findings}"


def test_control_the_real_stylesheet_is_not_empty_and_the_rules_are_silent() -> None:
    """На необойдённом файле оба правила молчат, и молчат НЕ на пустоте."""
    lines = APP_CSS.read_text(encoding="utf-8").count("\n")
    assert lines > APP_CSS_LINE_FLOOR, f"в таблице стилей {lines} строк, не больше {APP_CSS_LINE_FLOOR}"
    css = _app_css()
    assert _clearance_findings(css) == ()
    assert len(_banner_top_blocks(css)) == BANNER_TOP_VARIABLE_BLOCKS
