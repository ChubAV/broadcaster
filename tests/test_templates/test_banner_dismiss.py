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
    TEMPLATES_DIR,
    _all_templates,
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
