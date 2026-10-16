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


def getattr_literal(node: ast.AST) -> tuple[ast.expr, str] | None:
    """`getattr(<obj>, "<строка>")` (и с умолчанием третьим аргументом) → (`<obj>`, строка), иначе `None`.

    Один читатель getattr-литерала обоих гейтов номера (план 16-32, ревью IN-15, О-15): до
    плана у гейта писателя и у гейта приватности было по своей копии, и копии расходились
    (у писателя — два и более аргументов и любые именованные, у приватности — два-три без
    именованных). Форма строгая, как у `getattr_as_attribute`: два или три позиционных
    аргумента (третий — значение по умолчанию), ни одного именованного, без звёздной
    распаковки, второй — строковая константа. Имя, вычисленное во время исполнения
    (`getattr(logger, name)`), — не литерал.
    """
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) in (2, 3)
        and not node.keywords
        and not any(isinstance(arg, ast.Starred) for arg in node.args)
        and isinstance(node.args[1], ast.Constant)
        and isinstance(node.args[1].value, str)
    ):
        return node.args[0], node.args[1].value
    return None


def getattr_as_attribute(value: ast.expr) -> ast.expr:
    """`getattr(<obj>, "<const>")` — как узел `Attribute(<obj>, "<const>")`, иначе как есть.

    Строка в `getattr` называет атрибут литералом так же, как точка: `bum =
    getattr(session, "bulk_update_mappings")` связывает `bum` с тем же
    `session.bulk_update_mappings` (ревью WR-14). Форма — `getattr_literal`; узел встаёт
    на место вызова (`ast.copy_location`), поэтому строка находки — настоящая.
    """
    literal = getattr_literal(value)
    if literal is None:
        return value
    owner, attribute = literal
    return ast.copy_location(ast.Attribute(value=owner, attr=attribute, ctx=ast.Load()), value)


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
    `{ref}` (ссылка), `{args}` (аргументы применения через запятую), `{positional}`
    (только позиционные аргументы применения) и `{keywords}` (литерал словаря именованных
    аргументов применения, `{}` — когда их нет): носитель, который подаёт аргументы
    кортежем и словарём (`threading.Thread(target={ref}, args=({positional},),
    kwargs={keywords})`), собирается из тех же аргументов, что и прочие (план 16-32).
    `element` — как поэлементный носитель (`ELEMENTWISE_CARRIERS`) оборачивает каждый
    аргумент применения: одноэлементным списком (`"[{}]"`, умолчание) или обёрткой
    итерируемой (`"list([{}])"`, ревью WR-19).
    """

    id: str
    name: str
    template: str
    element: str = "[{}]"


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


# --- Семантика носителя ссылки (план 16-32, ревью WR-19 / WR-20, IN-15; О-14 (а), О-15) ---
#
# Где в вызове стоит ссылка на функцию и какие аргументы носитель ей подаст. До плана
# 16-32 эта семантика жила двумя копиями — в гейте писателя (`_forwarded_arguments`,
# `_iterable_elements`, ветки `_referenced_calls`) и в гейте приватности
# (`_carried_log_calls`, свой `_iterable_elements`), и копии разошлись: гейт писателя ловил
# `to_thread(*[setattr, …])`, `partial(asyncio.to_thread, setattr)(…)` и `map(mc,
# list([…]))`, гейт приватности те же формы с журналом — нет (ревью WR-19); ссылку в
# именованном аргументе, кроме `fn=`, не ловил ни один (ревью WR-20). Функции ниже написаны
# по семантике гейта писателя — она полнее — и не знают ни журнала, ни пишущего API: что
# такое ссылка, решает предикат гейта (`is_reference`).

# Обёртки литерального контейнера: `list([…])`, `tuple((…))`, `set({…})`, `iter([…])` подают
# элементы своего единственного аргумента (тот же смысл, что у одноимённой таблицы гейта
# писателя).
LITERAL_CONTAINER_WRAPPERS = frozenset({"list", "tuple", "set", "iter"})

# Имя на месте элемента итерируемой, которую предикат не раскрывает (параметр, вызов):
# аргумент на этой позиции вне суда, как параметр функции, но позиция цела.
UNJUDGED_ELEMENT = "<элемент не-литерала>"


def expanded_arguments(items: list[ast.expr]) -> list[ast.expr | None]:
    """Элементы с раскрытой литеральной распаковкой: `*[a, b]` / `*(a, b)` → `a, b`.

    Распаковка не-литерала (`*rows`, `*build()`) — один `None` на её месте: сколько
    элементов она подаст, решает поток данных. Смысл `_expanded_arguments` гейта писателя
    (план 16-32 перенёс его в общий модуль, ревью WR-19).
    """
    found: list[ast.expr | None] = []
    for item in items:
        if isinstance(item, ast.Starred):
            if isinstance(item.value, (ast.List, ast.Tuple)):
                found.extend(expanded_arguments(list(item.value.elts)))
            else:
                found.append(None)
        else:
            found.append(item)
    return found


def forwarded_arguments(items: list[ast.expr]) -> list[ast.expr]:
    """Аргументы, которые носитель подаст ссылке: литеральная распаковка раскрыта, прочая — на месте.

    Тот же порядок и та же длина, что у `expanded_arguments`, но распаковка не-литерала
    остаётся узлом `Starred`, а не `None`: синтетический вызов получает её так же, как
    прямой (`await asyncio.to_thread(*[logger.info, "x %s", account.phone])` подаёт
    `logger.info` аргументы `"x %s", account.phone`). Смысл `_forwarded_arguments` гейта
    писателя (самопроверка исполнителя 16-22; ревью WR-19).
    """
    found: list[ast.expr] = []
    for item in items:
        if isinstance(item, ast.Starred) and isinstance(item.value, (ast.List, ast.Tuple)):
            found.extend(forwarded_arguments(list(item.value.elts)))
        else:
            found.append(item)
    return found


def iterable_elements(node: ast.expr) -> tuple[list[ast.expr], bool] | None:
    """Элементы литеральной итерируемой: (элементы, повторяется ли один элемент на каждой позиции).

    Список, кортеж, набор (литеральная `*`-распаковка раскрыта) — их элементы по позициям;
    comprehension и генератор — его элемент, одинаковый на каждой позиции; обёртка
    `LITERAL_CONTAINER_WRAPPERS` с одним позиционным аргументом (`list([logger])`) — элементы
    аргумента. Иначе — `None`: длину и элементы решает поток данных. Смысл
    `_iterable_elements` гейта писателя; копия гейта приватности обёртки не раскрывала, и
    `list(map(methodcaller("info", account.phone), list([logger])))` уходил мимо него (ревью
    WR-19, IN-15).
    """
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        elements = expanded_arguments(list(node.elts))
        if any(element is None for element in elements):
            return None
        return [element for element in elements if element is not None], False
    if isinstance(node, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
        return [node.elt], True
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in LITERAL_CONTAINER_WRAPPERS
        and len(node.args) == 1
        and not isinstance(node.args[0], ast.Starred)
        and not node.keywords
    ):
        return iterable_elements(node.args[0])
    return None


def elementwise_arguments(iterables: list[ast.expr]) -> list[list[ast.expr]]:
    """Аргументы каждого вызова функции поэлементного носителя (`map(fn, *iterables)`).

    `map` зовёт функцию с элементом КАЖДОЙ итерируемой на одной позиции и
    останавливается на самой короткой: литеральные список, кортеж и набор зипуются (одна
    позиция — один вызов), у comprehension и генератора — его элемент на каждой позиции,
    итерируемая не-литерал даёт на своей позиции имя `UNJUDGED_ELEMENT` (аргумент вне
    суда). Распаковка не-литерала `*rows` среди итерируемых обрывает перечень: сколько
    итерируемых она подаст, решает поток данных. Число вызовов — длина самой короткой
    литеральной итерируемой фиксированной длины, иначе один. Смысл `_elementwise_arguments`
    гейта писателя (план 16-27).
    """
    columns: list[tuple[list[ast.expr], bool] | None] = []
    for iterable in iterables:
        if isinstance(iterable, ast.Starred):
            break
        columns.append(iterable_elements(iterable))
    fixed = [len(column[0]) for column in columns if column is not None and not column[1]]
    count = min(fixed) if fixed else 1
    calls: list[list[ast.expr]] = []
    for position in range(count):
        arguments: list[ast.expr] = []
        for iterable, column in zip(iterables, columns):
            if column is None:
                arguments.append(
                    ast.copy_location(ast.Name(id=UNJUDGED_ELEMENT, ctx=ast.Load()), iterable)
                )
            else:
                elements, repeated = column
                arguments.append(elements[0] if repeated else elements[position])
        calls.append(arguments)
    return calls


class ReferenceArguments(NamedTuple):
    """Ссылка, найденная в вызове-носителе, и аргументы, которые носитель ей подаст.

    `reference` — узел-аргумент, на котором предикат гейта (`is_reference`) истинен;
    `args` — позиционные аргументы ссылки; `keywords` — именованные (синтетические
    `ast.keyword` стоят на месте своего ключа).
    """

    reference: ast.expr
    args: list[ast.expr]
    keywords: list[ast.keyword]


def _callee_name(node: ast.expr) -> str | None:
    """Последнее имя вызываемого: `Name.id`, `Attribute.attr` или строка `getattr(…, "…")`."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    literal = getattr_literal(node)
    return literal[1] if literal is not None else None


def _literal_named_pairs(mapping: ast.expr) -> list[tuple[str, ast.expr, ast.AST]] | None:
    """Пары «строковый ключ — значение — место» литерального словаря или `dict(ключ=…)`.

    Литеральный словарь — только со строковыми ключами и без `**`-распаковки внутри;
    `dict(…)` — без позиционных аргументов и без `**`. Иначе — `None`: что лежит в
    отображении, решает поток данных.
    """
    if isinstance(mapping, ast.Dict):
        pairs: list[tuple[str, ast.expr, ast.AST]] = []
        for key, value in zip(mapping.keys, mapping.values):
            if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                return None
            pairs.append((key.value, value, key))
        return pairs
    if (
        isinstance(mapping, ast.Call)
        and isinstance(mapping.func, ast.Name)
        and mapping.func.id == "dict"
        and not mapping.args
        and all(keyword.arg is not None for keyword in mapping.keywords)
    ):
        return [(keyword.arg, keyword.value, keyword) for keyword in mapping.keywords if keyword.arg]
    return None


def _literal_sequence(node: ast.expr) -> list[ast.expr] | None:
    """Элементы литерального кортежа или списка без звёздных элементов, иначе `None`."""
    if isinstance(node, (ast.Tuple, ast.List)) and not any(
        isinstance(element, ast.Starred) for element in node.elts
    ):
        return list(node.elts)
    return None


def literal_keyword_arguments(
    keywords: list[ast.keyword], skip: ast.expr | None = None
) -> tuple[list[ast.expr], list[ast.keyword]]:
    """Общее правило владельца О-14 (а): литеральные именованные аргументы вызова — аргументы ссылки.

    Ссылка, поданная носителю, получает и литеральные аргументы того же вызова — по
    форме значения, а не по ключу отдельного API (`args=`, `kwds=`, `initargs=`, `payload=`
    — ключи не перечисляются, ревью WR-20): литеральный кортеж или список без звёздных
    элементов — его элементы идут позиционными аргументами ссылки, в порядке исходника;
    литеральный словарь со строковыми ключами и `dict(ключ=…)` — именованными, каждый
    синтетический `ast.keyword` получает место своего ключа (`ast.copy_location`: правило
    имён читает `lineno` именованного аргумента); пары литерального `**{…}` / `**dict(…)` —
    как именованные аргументы, к ним то же правило; прочие — как есть (`name="x"`,
    `**opts`). Именованный аргумент, чьё значение — сама ссылка (`skip`), пропускается.
    Цена — в сторону лишней находки, а не пропуска: литеральный кортеж у ключа, который
    API ссылке не подаёт, судится тоже. Аргументы, пришедшие нелитералом (`args=row`,
    `kwargs=opts`), правило не раскрывает: это поток данных.
    """
    positional: list[ast.expr] = []
    named: list[ast.keyword] = []

    def take(arg: str | None, value: ast.expr, place: ast.AST) -> None:
        if value is skip:
            return
        sequence = _literal_sequence(value)
        if sequence is not None:
            positional.extend(sequence)
            return
        pairs = _literal_named_pairs(value)
        if pairs is not None:
            named.extend(
                ast.copy_location(ast.keyword(arg=key, value=pair_value), location)
                for key, pair_value, location in pairs
            )
            return
        named.append(ast.copy_location(ast.keyword(arg=arg, value=value), place))

    for keyword in keywords:
        if keyword.arg is None:
            pairs = _literal_named_pairs(keyword.value)
            if pairs is not None:
                for key, value, location in pairs:
                    take(key, value, location)
                continue
            if keyword.value is skip:
                continue
            named.append(keyword)
            continue
        take(keyword.arg, keyword.value, keyword)
    return positional, named


def _keyword_references(keywords: list[ast.keyword]) -> list[ast.expr]:
    """Значения именованных аргументов вызова в порядке исходника, с парами литерального `**{…}`."""
    values: list[ast.expr] = []
    for keyword in keywords:
        if keyword.arg is not None:
            values.append(keyword.value)
            continue
        pairs = _literal_named_pairs(keyword.value)
        if pairs is not None:
            values.extend(value for _key, value, _location in pairs)
    return values


def _carried_by(
    source: ast.Call,
    is_reference,
    outer_args: list[ast.expr],
    outer_keywords: list[ast.keyword],
) -> list[ReferenceArguments]:
    """Ссылки одного носителя `source` и их аргументы (с хвостом применения `outer_*`)."""
    forwarded = forwarded_arguments(list(source.args))
    reference: ast.expr | None = None
    after: list[ast.expr] = []
    positional_reference = False
    for index, argument in enumerate(forwarded):
        if not isinstance(argument, ast.Starred) and is_reference(argument):
            reference, after, positional_reference = argument, forwarded[index + 1 :], True
            break
    if reference is None:
        for value in _keyword_references(list(source.keywords)):
            if is_reference(value):
                reference, after = value, forwarded
                break
    if reference is None:
        return []
    literal_args, literal_keywords = literal_keyword_arguments(list(source.keywords), reference)
    applied_args, applied_keywords = literal_keyword_arguments(outer_keywords)
    keywords = literal_keywords + applied_keywords
    if positional_reference and _callee_name(source.func) in ELEMENTWISE_CARRIERS:
        return [
            ReferenceArguments(reference, elements + literal_args, keywords)
            for elements in elementwise_arguments(after + outer_args)
        ]
    return [
        ReferenceArguments(reference, after + literal_args + outer_args + applied_args, keywords)
    ]


def reference_arguments(call: ast.Call, is_reference, not_carriers) -> list[ReferenceArguments]:
    """Ссылки на функцию, которые вызов-носитель `call` подаёт дальше, и их аргументы.

    Носитель — ЛЮБОЙ вызов; что считать ссылкой, решает предикат гейта `is_reference`
    (ссылка на пишущий API у гейта писателя, вызываемое журнала у гейта приватности);
    `not_carriers` — последние имена применяемых вызовов, которые носителем не судятся
    (`getattr(…)(…)`, `methodcaller(…)(…)`: их применение — не подача ссылки). Правила:
    1. Применённая обёртка `X(…)(…)`, где последнее имя `X` не в `not_carriers`
       (`partial(asyncio.to_thread, logger.info)("x %s", account.phone)`,
       `partial(*[logger.info, …])()`), — носитель ссылок `X(…)`: ссылку ищут в аргументах
       `X`, аргументы применения идут следом. Сам `X(…)` вызывающий гейт носителем не
       судит — его судит применение. Если в `X(…)` ссылки нет, носитель — само применение
       со своими аргументами (`make_runner()(logger.info, …)`).
    2. Ссылка — первый слева позиционный аргумент (`forwarded_arguments`: литеральная
       распаковка `*[…]` / `*(…)` раскрыта), не `Starred`, с истинным `is_reference`; её
       аргументы — позиционные ЗА ней.
    3. Иначе — первый именованный аргумент (и пара литерального `**{…}`) с истинным
       `is_reference`, ЛЮБОЙ ключ (`fn=`, `target=`, `function=`, `initializer=`, выдуманный
       `job=`); её аргументы — все позиционные носителя.
    4. К аргументам добавляется общее правило `literal_keyword_arguments` над прочими
       именованными аргументами носителя, затем аргументы применения (у его именованных —
       то же правило).
    5. У носителя из `ELEMENTWISE_CARRIERS` при позиционной ссылке — по одному результату на
       каждую позицию `elementwise_arguments`.
    6. Нет ссылки — пустой список.
    Пустые `args` и `keywords` значат, что ссылке ничего не подано: судить нечего, и
    вызывающий гейт решает, считать ли это вызовом.
    """
    if isinstance(call.func, ast.Call) and _callee_name(call.func.func) not in not_carriers:
        found = _carried_by(call.func, is_reference, list(call.args), list(call.keywords))
        if found:
            return found
    return _carried_by(call, is_reference, [], [])


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
    носителя из `ELEMENTWISE_CARRIERS` каждый позиционный аргумент оборачивается по
    `carrier.element` (одноэлементный список или `list([…])`). Шаблон носителя получает
    места `{args}` (все аргументы через запятую), `{positional}` (только позиционные) и
    `{keywords}` (литерал словаря именованных, `{}` — когда их нет; план 16-32). Той же
    функцией собирают ячейки правило-матрица гейта писателя, матрица
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
        positional = [ast.unparse(argument) for argument in applied.args]
        if carrier.name in ELEMENTWISE_CARRIERS:
            positional = [carrier.element.format(argument) for argument in positional]
        named = [
            f"{keyword.arg}={ast.unparse(keyword.value)}"
            if keyword.arg is not None
            else f"**{ast.unparse(keyword.value)}"
            for keyword in applied.keywords
        ]
        keywords = ", ".join(
            f"{keyword.arg!r}: {ast.unparse(keyword.value)}"
            if keyword.arg is not None
            else f"**{ast.unparse(keyword.value)}"
            for keyword in applied.keywords
        )
        use = carrier.template.format(
            ref=ref,
            args=", ".join(positional + named),
            positional=", ".join(positional),
            keywords="{" + keywords + "}",
        )
    return form.template.format(value=value.value, use=use, decoy=value.decoy)
