"""Регрессия выкладки шага мастера Telegram по QR: UI-1…UI-3 из `13-UI-REVIEW.md`.

Причина всех трёх дефектов одна. В Фазе 13 каждый шаг с действием переехал
внутрь макроса-обёртки формы. Макрос печатает тег формы, у которого одно
правило — контекст позиционирования, поэтому flex-выкладка колонки шага
(промежуток 14px, центрирование) до детей формы больше не доходит.

⚠️ КАЖДОЕ УТВЕРЖДЕНИЕ О ПРАВИЛЕ СТИЛЕЙ ИДЁТ В ПАРЕ С УТВЕРЖДЕНИЕМ О СТРУКТУРЕ,
КОТОРУЮ ОНО АДРЕСУЕТ (прецедент задачи 260826-ojg). Правило без адресуемой
разметки зеленело бы вакуумно, разметка без правила — тоже: страница отдаёт
200 одинаково с правкой и без неё.

Стили читаются разборщиком гейта `test_htmx_markup_gates.py` — второго
разборщика здесь не заводится.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser

import pytest

from app.pages.accounts import _tg_step_markup
from tests.test_templates.test_htmx_markup_gates import _app_css, _css_rules, _declaration

_VOID_TAGS = frozenset({"input", "img", "br", "hr", "meta", "link"})


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str | None]
    children: list["_Node"] = field(default_factory=list)
    text: str = ""

    @property
    def classes(self) -> set[str]:
        return set((self.attrs.get("class") or "").split())

    def iter(self):
        yield self
        for child in self.children:
            yield from child.iter()

    def find_all(self, tag: str | None = None, cls: str | None = None) -> list["_Node"]:
        return [
            node
            for node in self.iter()
            if node is not self
            and (tag is None or node.tag == tag)
            and (cls is None or cls in node.classes)
        ]


class _TreeBuilder(HTMLParser):
    """Дерево узлов отрисованного шага: тег, атрибуты, дети, собственный текст."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root", {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in _VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(_Node(tag, dict(attrs)))

    def handle_endtag(self, tag):
        if tag in _VOID_TAGS:
            return
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].text += data


def _tree(**kwargs) -> _Node:
    builder = _TreeBuilder()
    builder.feed(_tg_step_markup(**kwargs))
    builder.close()
    return builder.root


def _step_form(root: _Node) -> _Node:
    forms = root.find_all("form")
    assert len(forms) == 1, f"в шаге ожидается одна форма, найдено {len(forms)}"
    return forms[0]


def _rule(selector: str) -> str | None:
    """Тело ПОСЛЕДНЕГО правила, чей селектор ТОЧНО равен ``selector``."""
    body = None
    for rule_selector, rule_body in _css_rules(_app_css()):
        if rule_selector.strip() == selector:
            body = rule_body
    return body


@pytest.mark.parametrize("password_error", [None, "Неверный пароль 2FA."])
def test_the_password_step_keeps_its_field_and_button_in_one_column(password_error):
    """UI-1: поле 2FA и «Подтвердить» лежат во внутренней колонке с промежутком шага."""
    root = _tree(step="password", session_id="s", password_error=password_error)
    forms = [f for f in root.find_all("form") if (f.attrs.get("action") or "").endswith("/verify-2fa")]
    assert len(forms) == 1, "нет формы подтверждения пароля 2FA"
    form = forms[0]

    columns = [c for c in form.children if c.tag == "div" and "connect-step__form" in c.classes]
    assert len(columns) == 1, (
        "у формы пароля нет ровно одной внутренней колонки div.connect-step__form: "
        "промежуток колонки шага до детей тега формы не доходит (UI-1)"
    )
    column = columns[0]

    kids = column.children
    assert [k.tag for k in kids] == ["label", "div"], f"дети колонки: {[k.tag for k in kids]}"
    label, actions = kids
    assert "field" in label.classes
    assert any(n.attrs.get("name") == "password" for n in label.find_all("input"))
    assert "connect-step__actions" in actions.classes
    assert any(b.attrs.get("type") == "submit" for b in actions.find_all("button"))

    for child in form.children:
        assert not (child.tag == "label" and "field" in child.classes), "поле осталось прямым ребёнком формы"
        assert "connect-step__actions" not in child.classes, "ряд действий остался прямым ребёнком формы"

    hidden = [
        n for n in form.find_all("input")
        if n.attrs.get("type") == "hidden" and n.attrs.get("name") == "session_id"
    ]
    assert len(hidden) == 1, "идентификатор сессии обязан уходить телом POST (D-06)"

    column_rule = _rule(".connect-step__form")
    step_rule = _rule(".connect-step")
    assert column_rule is not None and step_rule is not None
    assert _declaration(column_rule, "display") == "flex"
    assert _declaration(column_rule, "flex-direction") == "column"
    assert _declaration(column_rule, "gap") == _declaration(step_rule, "gap")


def test_a_centered_step_centers_the_actions_nested_in_its_form():
    """UI-2: ряд «Обновить QR-код» / «Отмена» центрирован под текстом шага."""
    root = _tree(step="qr_expired", session_id="s")
    steps = root.find_all("div", "connect-step")
    assert len(steps) == 1
    step = steps[0]
    assert {"connect-step", "connect-step--center"} <= step.classes

    assert not any("connect-step__actions" in c.classes for c in step.children), (
        "ряд действий — прямой ребёнок шага: правило центрирования было бы ни к чему"
    )
    form = _step_form(step)
    assert form in step.children
    assert form.find_all("div", "connect-step__actions"), "ряд действий не лежит в форме шага"

    body = _rule(".connect-step--center .connect-step__actions")
    assert body is not None, (
        "нет правила `.connect-step--center .connect-step__actions`: ряд внутри "
        "растянутой формы остаётся у левого края (UI-2)"
    )
    assert _declaration(body, "justify-content") == "center"


BUSY_CLASS = "connect-step__busy"
BUSY_TEXT = "Загрузка..."
BUSY_SHOWN_SELECTOR = '.connect-step__actions > button[type="submit"][disabled] ~ .connect-step__busy'


@pytest.mark.parametrize(("step", "error"), [("start", None), ("error", "Ошибка"), ("qr_expired", None)])
def test_start_and_refresh_show_a_busy_label_while_the_button_is_disabled(step, error):
    """UI-3: подпись «Загрузка...» стоит после кнопки отправки, которую htmx отключает."""
    root = _tree(step=step, session_id="s", error=error)
    form = _step_form(root)
    assert form.attrs.get("hx-disabled-elt") == "find button[type=submit]", (
        "подпись держится на `disabled` кнопки отправки — форма обязана сохранить "
        "умолчание цели блокировки обёртки"
    )
    rows = form.find_all("div", "connect-step__actions")
    assert len(rows) == 1
    kids = rows[0].children

    buttons = [i for i, k in enumerate(kids) if k.tag == "button" and k.attrs.get("type") == "submit"]
    labels = [i for i, k in enumerate(kids) if k.tag == "span" and BUSY_CLASS in k.classes]
    assert len(buttons) == 1, "в ряду действий нет кнопки отправки"
    assert len(labels) == 1, f"в ряду действий нет ровно одной span.{BUSY_CLASS} (UI-3)"
    assert kids[labels[0]].text.strip() == BUSY_TEXT
    assert labels[0] > buttons[0], (
        "подпись обязана стоять ПОСЛЕ кнопки: комбинатор последующего соседа "
        "находит только более поздних соседей"
    )
    assert len(root.find_all(cls=BUSY_CLASS)) == 1, "во всей отрисовке шага подпись одна"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"step": "password", "session_id": "s"},
        {"step": "waiting", "session_id": "s", "qr_code": "data:image/png;base64,AA"},
        {"step": "connected"},
    ],
    ids=["password", "waiting", "connected"],
)
def test_no_other_step_carries_the_busy_label(kwargs):
    """Объём UI-3: подпись только у старта/ошибки и обновления QR."""
    assert BUSY_CLASS not in _tg_step_markup(**kwargs)


def test_the_busy_label_is_keyed_on_the_disabled_button_not_on_the_form():
    """UI-3: показ держит `disabled` кнопки, а не класс запроса рантайма."""
    resting = _rule(f".{BUSY_CLASS}")
    assert resting is not None, f"нет базового правила `.{BUSY_CLASS}`"
    assert _declaration(resting, "display") == "none"
    assert _declaration(resting, "font-size") == "var(--fs-md)"
    assert _declaration(resting, "color") == "var(--text-secondary)"

    shown = _rule(BUSY_SHOWN_SELECTOR)
    assert shown is not None, f"нет правила показа `{BUSY_SHOWN_SELECTOR}`"
    assert _declaration(shown, "display") == "inline"

    # Класс запроса рантайма садится на узел индикатора обёртки, а не на форму:
    # правило по нему не сработало бы никогда.
    offenders = [
        selector
        for selector, _ in _css_rules(_app_css())
        if f".{BUSY_CLASS}" in selector and "htmx-request" in selector
    ]
    assert offenders == [], f"селекторы подписи завязаны на класс запроса: {offenders}"
