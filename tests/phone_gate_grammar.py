"""Общая грамматика связывания и перечень носителей ссылки обоих гейтов номера.

ЗАЧЕМ ОДИН МОДУЛЬ. Гейт единственного писателя (`tests/test_application/
test_phone_single_writer_gate.py`, D-13) и гейт приватности номера
(`tests/test_phone_privacy_gate.py`, D-09 / D-17) решают один и тот же вопрос: какое
имя модуль связал с опознанным объектом — пишущим API или журналом — и куда эту
ссылку подал. Пока у каждого гейта была своя грамматика, они расходились: гейт
приватности разбирал распаковку кортежа, `:=` и `self.<x> =` в методе, а гейт
писателя — только `X = <имя>`; ревью WR-14 (2026-10-13) нашло пишущий API,
связанный ровно этими формами, и гейт писателя его пропускал. Решение владельца
О-12 (а), 2026-10-13: заявления гейтов прежние, оба гейта делят ОДНУ грамматику
связывания и ОДИН перечень носителей ссылки, а расхождение гейтов краснит
правило-паритет (`tests/test_phone_gates_parity.py`, план 16-29).

Модуль не тестовый: pytest собирает только `test_*.py`, а этот модуль зовут оба
гейта (`from tests.phone_gate_grammar import …`). Ввоза из `app/` здесь нет —
грамматика судит исходник, а не исполняет его.
"""

from __future__ import annotations

import ast
from typing import NamedTuple


class Binding(NamedTuple):
    """Одно связывание модуля: цель, значение и стоит ли оператор прямо в теле класса."""

    target: ast.expr
    value: ast.expr
    in_class_body: bool


def binding_pairs(target: ast.expr, value: ast.expr) -> list[tuple[ast.expr, ast.expr]]:
    """Пары «цель — значение» одного связывания.

    Кортеж или список на кортеж или список той же длины без `Starred` — попарно и
    рекурсивно: `w, touch = setattr, flag_modified` связывает `w` с `setattr` и
    `touch` с `flag_modified`. Цель с одной звёздной частью на литерал без звёзд —
    попарно позиции до звезды и после неё, звёздная часть получает список середины:
    `w, *rest = setattr, flag_modified, None` связывает `w` с `setattr`
    (самопроверка исполнителя 16-27). Распаковка не-литерала (`a, b = pair`) и литерал
    со звёздной распаковкой (`a, b = *pair, x`) — одна пара «кортеж — значение»: что в
    них лежит, решает поток данных.
    """
    if (
        isinstance(target, (ast.Tuple, ast.List))
        and isinstance(value, (ast.Tuple, ast.List))
        and not any(isinstance(elt, ast.Starred) for elt in value.elts)
    ):
        stars = [index for index, elt in enumerate(target.elts) if isinstance(elt, ast.Starred)]
        if not stars and len(target.elts) == len(value.elts):
            return [
                pair
                for sub_target, sub_value in zip(target.elts, value.elts)
                for pair in binding_pairs(sub_target, sub_value)
            ]
        if len(stars) == 1 and len(value.elts) >= len(target.elts) - 1:
            star = stars[0]
            tail = len(target.elts) - star - 1
            middle = value.elts[star : len(value.elts) - tail]
            starred = target.elts[star]
            assert isinstance(starred, ast.Starred)
            rest = ast.copy_location(ast.List(elts=list(middle), ctx=ast.Load()), value)
            pairs = list(zip(target.elts[:star], value.elts[:star]))
            pairs.append((starred.value, rest))
            pairs += list(zip(target.elts[star + 1 :], value.elts[len(value.elts) - tail :]))
            return [
                pair for sub_target, sub_value in pairs for pair in binding_pairs(sub_target, sub_value)
            ]
    return [(target, value)]


def getattr_as_attribute(value: ast.expr) -> ast.expr:
    """`getattr(<obj>, "<const>")` — как узел `Attribute(<obj>, "<const>")`, иначе как есть.

    Строка в `getattr` называет атрибут литералом так же, как точка: `bum =
    getattr(session, "bulk_update_mappings")` связывает `bum` с тем же
    `session.bulk_update_mappings` (ревью WR-14). Два или три позиционных аргумента
    (третий — значение по умолчанию) и ни одного именованного; узел встаёт на место
    вызова (`ast.copy_location`), поэтому строка находки — настоящая.
    """
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "getattr"
        and len(value.args) in (2, 3)
        and not value.keywords
        and not any(isinstance(arg, ast.Starred) for arg in value.args)
        and isinstance(value.args[1], ast.Constant)
        and isinstance(value.args[1].value, str)
    ):
        return ast.copy_location(
            ast.Attribute(value=value.args[0], attr=value.args[1].value, ctx=ast.Load()),
            value,
        )
    return value


def module_bindings(tree: ast.AST) -> list[Binding]:
    """Каждое связывание модуля `tree` — по грамматике, общей для обоих гейтов номера.

    Связывания: `ast.Assign` (каждая цель, кортеж на кортеж — попарно,
    `binding_pairs`), `ast.AnnAssign` со значением и оператор `:=` (`ast.NamedExpr`).
    Цель — любая: имя, атрибут любой глубины, в том числе `self.<x>` / `cls.<x>` в
    любом методе; `binding_name` даёт имя, под которым связанное зовут на месте
    вызова. Значение каждой пары — через `getattr_as_attribute`. `in_class_body` —
    оператор стоит прямо в теле `ClassDef` (такое имя зовут через `self.` / `cls.`).

    Область видимости плоская — весь модуль, без учёта функций и классов, как у
    прежних помощников обоих гейтов: имя, однажды связанное, судится в любой
    функции файла. Вне грамматики — цель `for` (элемент контейнера) и `with … as`
    (результат `__enter__`): `OUT_OF_GRAMMAR_BINDING_FORMS`.
    """
    class_body = {
        id(statement)
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        for statement in node.body
    }
    found: list[Binding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            in_class_body = id(node) in class_body
            for target in node.targets:
                found.extend(
                    Binding(sub_target, getattr_as_attribute(sub_value), in_class_body)
                    for sub_target, sub_value in binding_pairs(target, node.value)
                )
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            found.append(
                Binding(node.target, getattr_as_attribute(node.value), id(node) in class_body)
            )
        elif isinstance(node, ast.NamedExpr):
            found.append(Binding(node.target, getattr_as_attribute(node.value), False))
    return found


def binding_name(target: ast.expr) -> str | None:
    """Имя, под которым связанное зовут на месте вызова: `Name.id`, `Attribute.attr`, иначе `None`.

    `self.bum = …` зовут `self.bum(…)`, и последнее звено вызова — `bum`; имя в теле
    класса зовут через `self.` / `cls.` тем же последним звеном.
    """
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


class BindingForm(NamedTuple):
    """Форма связывания Python, которую грамматика разрешает.

    `template` — исходник с местами `{value}` (значение опознания) и `{use}`
    (выражение на месте вызова), у формы повторного связывания — ещё `{decoy}`
    (подменное значение того же вида, `IdentificationValue.decoy`); `ref` — как
    связанное имя названо на месте вызова (`f`, `self.f`, `cls.f`; у формы без
    связывания — `{value}`, само значение).
    """

    id: str
    template: str
    ref: str


# Оси B самопроверки 16-22 не было: кроме `X = …`, формы связывания в ней не
# перебирались, и пятый круг (ревью WR-14) открылся именно здесь. Каждая строка —
# форма, которую грамматика `module_bindings` разрешает; правило-матрица каждого
# гейта подаёт каждую форму с каждым значением опознания и носителем.
BINDING_FORMS: tuple[BindingForm, ...] = (
    BindingForm("direct", "{use}\n", "{value}"),
    BindingForm("assign", "f = {value}\n{use}\n", "f"),
    BindingForm("annotated", "f: object = {value}\n{use}\n", "f"),
    BindingForm("tuple-pair", "f, g = {value}, None\n{use}\n", "f"),
    BindingForm("walrus", "if (f := {value}):\n    {use}\n", "f"),
    BindingForm(
        "attribute-in-init",
        "class W:\n"
        "    def __init__(self):\n"
        "        self.f = {value}\n"
        "        {use}\n",
        "self.f",
    ),
    BindingForm(
        "attribute-in-method",
        "class W:\n"
        "    def __init__(self):\n"
        "        self.f = {value}\n"
        "\n"
        "    def run(self):\n"
        "        {use}\n",
        "self.f",
    ),
    BindingForm(
        "cls-attribute-in-classmethod",
        "class W:\n"
        "    @classmethod\n"
        "    def setup(cls):\n"
        "        cls.f = {value}\n"
        "\n"
        "    @classmethod\n"
        "    def run(cls):\n"
        "        {use}\n",
        "cls.f",
    ),
    BindingForm(
        "class-body",
        "class W:\n"
        "    f = {value}\n"
        "\n"
        "    def run(self):\n"
        "        {use}\n",
        "self.f",
    ),
    # Ось «сколько раз связано имя» (ревью WR-18, верификация раунда 6, 2026-10-14):
    # карты псевдонимов гейтов держали ОДНО связывание имени — первое в обходе или
    # первое по алфавиту, — и имя, связанное в модуле дважды, судилось по подмене.
    # Каждая форма ниже связывает одно имя с подменным значением того же вида
    # (`IdentificationValue.decoy`) и со значением опознания: в одной области, в обратной
    # очерёдности в двух функциях и в двух классах. Каждое связывание имени судится.
    BindingForm("rebound", "f = {decoy}\nf = {value}\n{use}\n", "f"),
    BindingForm(
        "rebound-reversed",
        "def a():\n"
        "    f = {value}\n"
        "    {use}\n"
        "\n"
        "\n"
        "def b():\n"
        "    f = {decoy}\n",
        "f",
    ),
    BindingForm(
        "rebound-across-classes",
        "class A:\n"
        "    def __init__(self):\n"
        "        self.f = {decoy}\n"
        "\n"
        "\n"
        "class B:\n"
        "    def __init__(self):\n"
        "        self.f = {value}\n"
        "\n"
        "    def run(self):\n"
        "        {use}\n",
        "self.f",
    ),
)


class OutOfGrammarForm(NamedTuple):
    """Форма связывания, которую грамматика НЕ разрешает, — с правдивой причиной."""

    id: str
    template: str
    ref: str
    reason: str


# Формы вне грамматики — одни и те же у обоих гейтов, и каждая названа в их границе.
OUT_OF_GRAMMAR_BINDING_FORMS: tuple[OutOfGrammarForm, ...] = (
    OutOfGrammarForm(
        "for-target-over-container",
        "for f in [{value}]:\n    {use}\n",
        "f",
        "цель `for` получает элемент контейнера, а не выражение: элемент контейнера — "
        "поток данных, который предикат не прослеживает",
    ),
    OutOfGrammarForm(
        "with-as",
        "with {value} as f:\n    {use}\n",
        "f",
        "`with … as f` связывает результат `__enter__`, а не выражение после `with`",
    ),
)


# Именованный параметр ССЫЛКИ на функцию: `fn` у `AsyncSession.run_sync` /
# `AsyncConnection.run_sync` — `(self, fn, *arg, **kw)`, замер `inspect.signature`,
# SQLAlchemy 2.0.46. У `asyncio.to_thread` и `functools.partial` ссылка
# позиционно-только (`partial(func=…)` и `to_thread(func=…)` падают `TypeError`,
# замер 2026-10-12), у `loop.run_in_executor` именованных аргументов нет вовсе
# (план 16-17, ревью WR-10). Перенесён из гейта писателя планом 16-27: перечень
# носителей и их ключ — общие для обоих гейтов (О-12 (а)).
REFERENCE_KEYWORDS = frozenset({"fn"})

# Носитель, который подаёт функции ЭЛЕМЕНТЫ итерируемых, а не сами итерируемые:
# функция получает элемент каждой итерируемой (`map(setattr, [account], ["phone"],
# [x])` зовёт `setattr(account, "phone", x)`).
ELEMENTWISE_CARRIERS = frozenset({"map"})


class ReferenceCarrier(NamedTuple):
    """Носитель ссылки: вызов, которому подают ссылку на функцию вместе с её аргументами.

    `name` — как носитель назван в шапках гейтов; `template` — выражение с местами
    `{ref}` (ссылка) и `{args}` (аргументы применения).
    """

    id: str
    name: str
    template: str


# Один перечень носителей ссылки обоих гейтов номера (решение владельца О-12 (а)).
# Это не закрытый список опознания — гейт писателя судит ссылку на пишущий API в
# любом вызове, — а общий словарь матриц, шапок и правила-паритета.
REFERENCE_CARRIERS: tuple[ReferenceCarrier, ...] = (
    ReferenceCarrier("run-sync", "run_sync", "session.run_sync({ref}, {args})"),
    ReferenceCarrier("to-thread", "to_thread", "asyncio.to_thread({ref}, {args})"),
    ReferenceCarrier(
        "run-in-executor", "run_in_executor", "loop.run_in_executor(None, {ref}, {args})"
    ),
    ReferenceCarrier("map", "map", "list(map({ref}, {args}))"),
    ReferenceCarrier(
        "context-run", "Context.run", "contextvars.copy_context().run({ref}, {args})"
    ),
)


class IdentificationValue(NamedTuple):
    """Значение опознания: выражение, которое называет судимый объект, и аргументы применения.

    `call` — аргументы в скобках, `(account, "phone", x)`; каждый гейт инстанцирует
    свою таблицу значений с общими `id`.

    `decoy` — безобидное значение ТОГО ЖЕ вида опознания, которое формы повторного
    связывания (`rebound*` в `BINDING_FORMS`) связывают с тем же именем (ревью WR-18,
    план 16-31): ошибка «судится одно связывание» видна, только когда подмена того же
    вида, что значение, — другой пишущий API, первый по алфавиту, у имени, атрибута и
    `getattr`-строки; `partial` над другим API; `methodcaller("noop")`. Умолчание —
    пустая строка: позиционное создание прежних строк не ломается, а форма с `{decoy}`
    при пустой подмене — вакуум, и `binding_form_source` его отвергает.
    """

    id: str
    value: str
    call: str
    decoy: str = ""


def binding_form_source(
    form: BindingForm | OutOfGrammarForm,
    value: IdentificationValue,
    carrier: ReferenceCarrier | None = None,
) -> str:
    """Исходник одной ячейки матрицы «форма связывания × значение опознания × носитель».

    Место `{use}` формы получает прямой вызов `ref + call` (при `carrier=None`) или
    выражение носителя: ссылка формы и аргументы `call`, разобранные через `ast`; у
    носителя из `ELEMENTWISE_CARRIERS` каждый аргумент подаётся одноэлементным
    списком. Той же функцией собирают ячейки правило-матрица гейта писателя, матрица
    гейта приватности, правило-паритет (план 16-29) и самопроверки исполнителей —
    ячейка одна и та же для обоих гейтов по построению.

    Место `{decoy}` формы повторного связывания получает `value.decoy` (план 16-31); у
    значения без подмены такая ячейка — вакуум, и функция поднимает `AssertionError`.
    """
    if "{decoy}" in form.template and not value.decoy:
        raise AssertionError(
            f"форма `{form.id}` связывает имя повторно, а у значения `{value.id}` нет "
            "подменного значения `decoy`: ячейка проверяла бы ничто"
        )
    ref = form.ref.format(value=value.value)
    if carrier is None:
        use = ref + value.call
    else:
        applied = ast.parse(f"f{value.call}", mode="eval").body
        assert isinstance(applied, ast.Call), value.call
        arguments = [ast.unparse(argument) for argument in applied.args]
        if carrier.name in ELEMENTWISE_CARRIERS:
            arguments = [f"[{argument}]" for argument in arguments]
        arguments += [
            f"{keyword.arg}={ast.unparse(keyword.value)}"
            if keyword.arg is not None
            else f"**{ast.unparse(keyword.value)}"
            for keyword in applied.keywords
        ]
        use = carrier.template.format(ref=ref, args=", ".join(arguments))
    return form.template.format(value=value.value, use=use, decoy=value.decoy)
