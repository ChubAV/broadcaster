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


def reading_name(node: ast.AST | None) -> str | None:
    """Имя, которым выражение `node` ЧИТАЕТ связанное: `Name.id`, `Attribute.attr`, строка getattr.

    Один читатель имени обоих гейтов номера (ревью WR-28, верификация раунда 8; решение
    владельца О-18 (а), свойство 2; план 16-42): `f`, `self.f` и `getattr(self, "f")` (и
    с умолчанием третьим аргументом — форма `getattr_literal`) читают одно имя `f`. У
    прочих узлов и у `None` — `None`. Ось «где прочитано имя» закрыта по оси целиком, а
    не по видам имени: до плана 16-42 getattr-строку читала только `named_wrappers` (имя
    обёртки, раунд 7), а имя, связанное с `operator.methodcaller`, гейт писателя читал
    своими проверками `Name` / `Attribute` — `self.f = operator.methodcaller("__set__",
    account, x)` с `getattr(self, "f")(MessengerAccount.phone)` уходил мимо (SQLite записал
    `+71`). Теперь имя обёртки, имя `methodcaller` и ссылку читает эта функция. Цель
    связывания читает `binding_name`, а не эта функция: цель не место чтения.

    Зовут её оба гейта по имени: гейт писателя — с плана 16-42, гейт приватности — с плана
    16-43 (`_methodcaller_calls`, псевдонимы обёртки ссылки, последнее имя вызываемого: до
    плана 16-43 `getattr(self, "f")(logger)` при `self.f = operator.methodcaller("info",
    "x %s", account.phone)` уходил мимо гейта приватности, и `logging` печатал номер).
    Правило-паритет требует её у обоих гейтов тем же объектом (`REQUIRED_SHARED_NAMES`,
    `CARRIER_SEMANTICS`).
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    literal = getattr_literal(node) if node is not None else None
    return literal[1] if literal is not None else None


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
    # Ось «где прочитано имя» (ревью WR-28, верификация раунда 8, 2026-10-19): в словаре не было
    # формы, которая читает связанное имя getattr-строкой, и ни обе матрицы, ни правило-паритет,
    # ни корпуса самопроверок исполнителей её не собирали — давний пропуск у `methodcaller`
    # (`self.f = operator.methodcaller("__set__", account, x)` с `getattr(self, "f")(…)`) проходил
    # оба гейта. Строка связывает имя в `__init__` и читает его getattr-строкой в другом методе;
    # возврат чтения имени только у `Name` / `Attribute` краснит обе матрицы и правило-паритет
    # (решение владельца О-18 (а), свойство 3; план 16-44).
    BindingForm(
        "getattr-read",
        "class W:\n"
        "    def __init__(self):\n"
        "        self.f = {value}\n"
        "\n"
        "    def run(self):\n"
        "        {use}\n",
        'getattr(self, "f")',
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


# Летопись ключа ссылки. До плана 16-34 здесь была закрытая таблица `REFERENCE_KEYWORDS =
# frozenset({"fn"})` — именованный параметр ССЫЛКИ `fn` у `AsyncSession.run_sync` /
# `AsyncConnection.run_sync` (`(self, fn, *arg, **kw)`, замер `inspect.signature`,
# SQLAlchemy 2.0.46; план 16-17, ревью WR-10; перенесена из гейта писателя планом 16-27).
# Ключ ссылки был один — `fn`, и `threading.Thread(target=setattr, args=(…))` проходил оба
# гейта (ревью WR-20). Общее правило О-14 (а) (владелец, 2026-10-16) судит ЛЮБОЙ
# именованный аргумент (`reference_arguments`), а не перечень ключей отдельных API, и
# таблица выведена целиком: из этого модуля, из ввоза обоих гейтов и из обязательных
# имён правила-паритета; в его `GRAMMAR_TABLES` имя осталось — модуль гейта не вправе
# завести таблицу снова.

# Носитель, который подаёт функции ЭЛЕМЕНТЫ итерируемых, а не сами итерируемые:
# функция получает элемент каждой итерируемой (`map(setattr, [account], ["phone"],
# [x])` зовёт `setattr(account, "phone", x)`). Построчный носитель подаёт функции элементы
# каждой СТРОКИ первой итерируемой позиционными аргументами (`starmap(setattr,
# [(account, "phone", x)])`). Какие носители поэлементны и построчны, решает одно правило
# для обоих гейтов (ревью CR-02 / WR-25, решение владельца О-16 (а), свойство 4, план
# 16-38): до плана таблица знала один `map`, и `pool.imap(logger.info, …)` гейт приватности
# судил целиком, а `map(logger.info, …)` — поэлементно; прочтение строк `starmap` было
# только у гейта писателя. Состав — замер stdlib 3.12: методы с `map` у
# `multiprocessing.pool.Pool`, `concurrent.futures.Executor` и модуля `itertools`; сторож
# правила-паритета `test_the_elementwise_and_row_carriers_name_the_installed_apis` краснит,
# когда установленный stdlib назовёт метод с `map`, которого нет ни в одной таблице.
ELEMENTWISE_CARRIERS = frozenset({"map", "imap", "imap_unordered", "map_async"})
ROW_CARRIERS = frozenset({"starmap", "starmap_async"})


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
    `last` — не-литеральная итерируемая, которая встаёт на место ПОСЛЕДНЕГО позиционного
    аргумента применения, когда их два и более (место «итерируемая не-литерал» у
    поэлементного носителя: `account.phones`; ревью CR-02, решение владельца О-16 (а),
    свойство 6, план 16-39). У значения-получателя места нет: единственный позиционный
    аргумент применения `methodcaller` — получатель, а получатель обязан быть опознан (D-17).
    У значения `partial` с одним позиционным аргументом (номером) места нет по выбору словаря,
    а не по правилу получателя: ячейка `map-named-iterable` у него совпадает с ячейкой `map`, а
    форму `list(map(functools.partial(logger.info, "x %s"), account.phones))` закрепляет строка
    `NEGATIVE_CONTROLS` `partial-log-reference-mapped-over-a-phone-attribute` гейта приватности,
    которую дерево `1c243203` не ловит, — возврат класса CR-02 на этом значении краснит суиту
    (ревью IN-20, решение владельца О-19, план 16-43). Пустая строка (умолчание) — места нет;
    прежние строки создаются позиционно без изменений.
    """

    id: str
    name: str
    template: str
    element: str = "[{}]"
    last: str = ""


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
    # Ось «как подана ссылка» (ревью WR-19 / WR-20, верификация раунда 6, 2026-10-14; план
    # 16-34): в словаре не было ни литеральной `*`-распаковки, ни применённой обёртки
    # носителя, ни обёртки итерируемой, ни ссылки в именованном аргументе — и матрицы с
    # правилом-паритетом этих форм не видели. Выдуманная пара ключей (`job=` / `payload=`)
    # доказывает, что общее правило О-14 (а) от имён ключей не зависит.
    ReferenceCarrier(
        "starred", "to_thread(*[…])", "asyncio.to_thread(*[{ref}, {positional}], **{keywords})"
    ),
    ReferenceCarrier(
        "partial-wrapped",
        "partial(to_thread, …)(…)",
        "functools.partial(asyncio.to_thread, {ref})({args})",
    ),
    ReferenceCarrier("map-wrapped-iterable", "map", "list(map({ref}, {args}))", "list([{}])"),
    ReferenceCarrier(
        "thread-target",
        "Thread(target=…, args=…)",
        "threading.Thread(target={ref}, args=({positional},), kwargs={keywords})",
    ),
    ReferenceCarrier(
        "timer-args",
        "Timer(…, args=…)",
        "threading.Timer(1.0, {ref}, args=({positional},), kwargs={keywords})",
    ),
    ReferenceCarrier(
        "invented-keyword",
        "enqueue(job=…, payload=…)",
        "scheduler.enqueue(job={ref}, payload=({positional},), options={keywords})",
    ),
    # Ось «где прочитано имя обёртки» (ревью CR-03, верификация раунда 7, 2026-10-18; решение
    # владельца О-16 (а), свойство 6; план 16-39): обёртку носителя под именем, связанную с
    # аргументами записи / журнала и ПЕРЕДАННУЮ исполнителю, а не вызванную, — дословное тело
    # `asyncio.to_thread` — гейт писателя после `147f5e46` не судил нигде (поглощение по любому
    # чтению), и ни одна ячейка словаря её не держала: регрессия прошла суиту зелёной. Строка
    # различает регрессию CR-03 в матрице гейта писателя и в правиле-паритете: на предикатах
    # `147f5e46` она краснит матрицу гейта писателя (замер верификатора раунда 8 — 48 из 60 ячеек
    # строки на 12 формах × 5 значениях; замер плана 16-44 режимом `run.sh --rows` на таблицах HEAD —
    # 52 из 78 на 13 формах × 6 значениях, красных на `147f5e46` и зелёных на его родителе), а матрица
    # гейта приватности на этом коммите зелёная (0 из 60, 0 из 78): своего поглощения у гейта
    # приватности не было (ревью IN-18, решение владельца О-19). Зелёная с плана 16-36.
    ReferenceCarrier(
        "named-wrapper-bound-handed",
        "w = partial(Context.run, …, args); run_in_executor(None, w)",
        "wrapped = functools.partial(contextvars.copy_context().run, {ref}, {args}); "
        "loop.run_in_executor(None, wrapped)",
    ),
    # Оси седьмого круга (ревью CR-02, WR-24, WR-25, WR-26, верификация раунда 7, 2026-10-18;
    # решение владельца О-16 (а), свойство 6; план 16-39): ни одна ячейка словаря не держала
    # обёртку под именем (вызов, передача, getattr-вариант), обёртку, поданную носителю, обёртку
    # в обёртке, `starmap`, `apply_async` и не-литеральную итерируемую у `map` — и регрессии
    # `c6953017` (CR-02) и `147f5e46` (CR-03) прошли суиту зелёными. Шаблоны однострочные (`;`):
    # место `{use}` формы связывания стоит на строке с её отступом, и составной оператор на одной
    # строке годится в любой форме `BINDING_FORMS`.
    ReferenceCarrier(
        "wrapper-handed",
        "run_in_executor(None, partial(Context.run, …), …)",
        "loop.run_in_executor(None, functools.partial(contextvars.copy_context().run, {ref}), {args})",
    ),
    ReferenceCarrier(
        "wrapper-of-wrapper",
        "partial(partial(Context.run, …))(…)",
        "functools.partial(functools.partial(contextvars.copy_context().run, {ref}))({args})",
    ),
    ReferenceCarrier(
        "named-wrapper-called",
        "w = partial(to_thread, …); w(…)",
        "wrapped = functools.partial(asyncio.to_thread, {ref}); wrapped({args})",
    ),
    ReferenceCarrier(
        "named-wrapper-handed",
        "w = partial(Context.run, …); run_in_executor(None, w, …)",
        "wrapped = functools.partial(contextvars.copy_context().run, {ref}); "
        "loop.run_in_executor(None, wrapped, {args})",
    ),
    ReferenceCarrier(
        "named-wrapper-getattr",
        'getattr(holder, "w")(…)',
        'holder.wrapped = functools.partial(asyncio.to_thread, {ref}); getattr(holder, "wrapped")({args})',
    ),
    ReferenceCarrier("starmap", "starmap", "list(itertools.starmap({ref}, [({positional},)]))"),
    ReferenceCarrier("apply-async", "apply_async", "pool.apply_async({ref}, ({positional},), {keywords})"),
    # Место не-литеральной итерируемой у поэлементного носителя: литерал — прежняя строка `map`,
    # имя с `phone` — эта строка. Она различает регрессию CR-02 в матрице гейта приватности и в
    # правиле-паритете: на предикатах `c6953017` она краснит матрицу гейта приватности (замер
    # верификатора раунда 8 — 36 из 60 ячеек строки на 12 формах × 5 значениях; замер плана 16-44
    # режимом `run.sh --rows` на таблицах HEAD — 39 из 78 на 13 формах × 6 значениях, красных на
    # `c6953017` и зелёных на его родителе), а матрица гейта писателя на этом коммите зелёная (0)
    # (ревью IN-18, решение владельца О-19).
    # Последний позиционный у гейта писателя — значение `x` (колонка остаётся литералом), у гейта
    # приватности — `account.phone` (номер уходит в не-литерал, и итерируемая судится целиком).
    # У значения с одним позиционным места нет: у `methodcaller` это получатель (D-17), у `partial`
    # — номер, и места нет по выбору словаря (ячейка равна ячейке `map`); форму `partial` над
    # `account.phones` держит строка `NEGATIVE_CONTROLS` `partial-log-reference-mapped-over-a-phone-attribute`
    # гейта приватности (ревью IN-20, решение владельца О-19, план 16-43).
    ReferenceCarrier("map-named-iterable", "map", "list(map({ref}, {args}))", "[{}]", "account.phones"),
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


def _verbatim_keywords(keywords: list[ast.keyword], skip: ast.expr) -> list[ast.keyword]:
    """Именованные аргументы вызова как есть, без ссылки `skip`: пары литерального `**{…}` — ключами."""
    found: list[ast.keyword] = []
    for keyword in keywords:
        if keyword.value is skip:
            continue
        if keyword.arg is None:
            pairs = _literal_named_pairs(keyword.value)
            if pairs is not None:
                found.extend(
                    ast.copy_location(ast.keyword(arg=key, value=value), location)
                    for key, value, location in pairs
                    if value is not skip
                )
                continue
        found.append(keyword)
    return found


def _spread_arguments(items: list[ast.expr]) -> tuple[list[ast.expr], list[ast.keyword]]:
    """Общее правило О-14 (а) над ПОЗИЦИОННЫМИ аргументами за ссылкой: литералы раскрыты.

    Литеральный кортеж или список без звёздных элементов — его элементы идут позиционными
    аргументами ссылки, литеральный словарь со строковыми ключами и `dict(ключ=…)` —
    именованными (место — ключ), прочие — как есть: `pool.apply_async(func, args, kwds)`
    подаёт функции `*args, **kwds` (самопроверка исполнителя 16-34, заход 1).
    """
    positional: list[ast.expr] = []
    named: list[ast.keyword] = []
    for item in items:
        sequence = _literal_sequence(item) if not isinstance(item, ast.Starred) else None
        if sequence is not None:
            positional.extend(sequence)
            continue
        pairs = _literal_named_pairs(item) if not isinstance(item, ast.Starred) else None
        if pairs is not None:
            named.extend(
                ast.copy_location(ast.keyword(arg=key, value=value), location)
                for key, value, location in pairs
            )
            continue
        positional.append(item)
    return positional, named


def _carried_by(
    source: ast.Call,
    is_reference,
    outer_args: list[ast.expr],
    outer_keywords: list[ast.keyword],
    every_reading: bool = False,
    keep_iterables: bool = False,
) -> list[ReferenceArguments]:
    """Ссылки одного носителя `source` и их аргументы (с хвостом применения `outer_*`)."""
    forwarded = forwarded_arguments(list(source.args))
    # (ссылка, позиционные аргументы за ней, позиционная ли) — первая позиционная, иначе
    # первая именованная; при `every_reading` — каждая позиционная и каждая именованная.
    candidates: list[tuple[ast.expr, list[ast.expr], bool]] = []
    for index, argument in enumerate(forwarded):
        if not isinstance(argument, ast.Starred) and is_reference(argument):
            candidates.append((argument, forwarded[index + 1 :], True))
            if not every_reading:
                break
    if not candidates or every_reading:
        for value in _keyword_references(list(source.keywords)):
            if is_reference(value):
                candidates.append((value, forwarded, False))
                if not every_reading:
                    break
    if every_reading:
        # Именованная ссылка — и без позиционных носителя: у применённой обёртки
        # `partial(threading.Thread, target=ref)(args=(…))` первый позиционный `partial` — сам
        # носитель, а не аргумент ссылки (самопроверка исполнителя 16-34, зонд захода 2).
        candidates += [
            (reference, [], False)
            for reference, after, positional in list(candidates)
            if not positional and after
        ]
    found: list[ReferenceArguments] = []

    def add(results: list[ReferenceArguments]) -> None:
        # Повтор отбрасывается только между прочтениями: равные позиции `map` одного
        # прочтения — разные вызовы.
        earlier = {_dump(known) for known in found}
        found.extend(result for result in results if _dump(result) not in earlier)

    for reference, after, positional_reference in candidates:
        literal_args, literal_keywords = literal_keyword_arguments(list(source.keywords), reference)
        applied_args, applied_keywords = literal_keyword_arguments(outer_keywords)
        keywords = literal_keywords + applied_keywords
        elementwise = positional_reference and _callee_name(source.func) in ELEMENTWISE_CARRIERS
        # Прочтения при `every_reading`: «как есть» (носитель подаёт ссылке свои именованные
        # аргументы без разбора — `run_sync(fn, *arg, **kw)`, `functools.partial`, — и ключ
        # литерального аргумента есть имя параметра ссылки: `mappings={…}`) — ПЕРВЫМ; общее
        # правило — следом; затем общее правило и над позиционными аргументами за ссылкой
        # (`_spread_arguments`: `pool.apply_async(func, (…), {…})`). Одно место — одна
        # находка у вызывающего гейта.
        readings: list[tuple[list[ast.expr], list[ast.keyword]]] = []
        if every_reading:
            readings.append(
                (
                    after + outer_args,
                    _verbatim_keywords(list(source.keywords), reference) + list(outer_keywords),
                )
            )
        readings.append((after + literal_args + outer_args + applied_args, keywords))
        if every_reading and not elementwise:
            spread_args, spread_keywords = _spread_arguments(after + outer_args)
            readings.append((spread_args + literal_args + applied_args, keywords + spread_keywords))
        for index, (own_args, own_keywords) in enumerate(readings):
            # `keep_iterables` (гейт приватности, ревью CR-02): итерируемые поэлементного
            # носителя подаются ссылке КАК ЕСТЬ — не-литерал самим выражением, comprehension
            # целиком с источником итерации, `*name` узлом `Starred`, — а не элементами.
            if elementwise and not keep_iterables:
                # `map`: позиционные за ссылкой — итерируемые; литеральные именованные
                # аргументы общего правила — хвостом (у прочтения «как есть» — нет).
                tail = [] if every_reading and index == 0 else literal_args
                results = [
                    ReferenceArguments(reference, elements + tail, own_keywords)
                    for elements in elementwise_arguments(after + outer_args)
                ]
            else:
                results = [ReferenceArguments(reference, own_args, own_keywords)]
            add(results)
        # Построчный носитель (`ROW_CARRIERS`) читается построчно у ОБОИХ гейтов, без флага
        # (ревью WR-25, план 16-38): получатель `methodcaller` у `starmap(mc, [(logger,)])`
        # лежит в строке. Литеральные кортежи прочих носителей — по-прежнему только под
        # `every_reading` (гейт писателя). Итерируемая целиком остаётся общим прочтением выше.
        rows = positional_reference and _callee_name(source.func) in ROW_CARRIERS
        tuples = (
            iterable_elements(after[0])
            if (every_reading or rows) and positional_reference and not elementwise and after
            and not isinstance(after[0], ast.Starred)
            else None
        )
        if tuples is not None:
            # `starmap(ref, [(…), (…)])`: функция получает элементы КАЖДОГО литерального
            # кортежа или списка первой итерируемой за ссылкой (самопроверка исполнителя
            # 16-34, зонд захода 2) — по результату на элемент.
            add(
                [
                    ReferenceArguments(reference, items, keywords)
                    for element in tuples[0]
                    if (items := _literal_sequence(element)) is not None
                ]
            )
    return found


def _dump(carried: ReferenceArguments) -> str:
    """Отпечаток аргументов результата: равные прочтения не повторяются."""
    return ast.dump(ast.Call(func=carried.reference, args=carried.args, keywords=carried.keywords))


def reference_arguments(
    call: ast.Call,
    is_reference,
    not_carriers,
    every_reading: bool = False,
    keep_iterables: bool = False,
) -> list[ReferenceArguments]:
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
    5. У носителя из `ELEMENTWISE_CARRIERS` (`map`, `imap`, `imap_unordered`, `map_async`) при
       позиционной ссылке — по одному результату на каждую позицию `elementwise_arguments`. У
       носителя из `ROW_CARRIERS` (`starmap`, `starmap_async`) при позиционной ссылке — сверх
       общего прочтения (итерируемая целиком) по результату на каждую литеральную строку
       первой итерируемой за ссылкой: элементы строки — позиционные аргументы ссылки. Это
       прочтение — у обоих гейтов, без флага (ревью WR-25, план 16-38). Обе таблицы — одно
       правило общего модуля, сверенное сторожем правила-паритета с установленным stdlib.
    6. Нет ссылки — пустой список.
    7. `every_reading=True` (гейт писателя, план 16-34; у него вид находки зависит от имени
       параметра и от того, какая из ссылок носителя — вызываемая) — каждое прочтение:
       (а) КАЖДАЯ позиционная и каждая именованная ссылка носителя, а не первая
       (`pool.call(MessengerAccount, rows, target=s.bulk_update_mappings)`: модель среди
       аргументов — тоже судимое имя); (б) ВПЕРЕДИ общего правила — прочтение «как есть»:
       именованные аргументы носителя и применения подаются ссылке без разбора (так их
       подают `run_sync(fn, *arg, **kw)` и `partial`: `mappings={"id": 1, "phone": p}` —
       строка executemany, а не `id=1, phone=p`); (в) общее правило и над ПОЗИЦИОННЫМИ
       аргументами за ссылкой (`_spread_arguments`: `pool.apply_async(func, (…), {…})`
       подаёт `*args, **kwds`); (г) элементы литеральных кортежей первой итерируемой за
       позиционной ссылкой и у носителя вне `ROW_CARRIERS`. Равные прочтения не повторяются;
       цена — в сторону лишней находки. Какое прочтение какому гейту нужно: гейту писателя —
       `every_reading` (вид его находки зависит от того, какая ссылка вызываемая и как
       поданы аргументы); гейту приватности — `keep_iterables` в правиле носителя и в
       применениях обёртки (правило 8: он судит имена итерируемых), построчное прочтение
       `ROW_CARRIERS` (правило 5) и `every_reading` в пути `methodcaller`: получатель
       `methodcaller` лежит там, где его подаёт прочтение, — в строке `starmap(mc,
       [(logger,)])`, в аргументах применения `partial(threading.Thread, target=mc)(args=
       (logger,))`, — и без этих прочтений формы уходили мимо гейта приватности, хотя гейт
       писателя те же формы ловил (ревью WR-25, верификация раунда 7; сверка «база ↔ HEAD»
       плана 16-38).
    8. `keep_iterables=True` (правило носителя гейта приватности, `_carried_log_calls`; ревью
       CR-02, решение владельца О-16 (а), свойство 4) — у носителя из `ELEMENTWISE_CARRIERS`
       ссылка получает итерируемые КАК ЕСТЬ, а не элементы правила 5: не-литерал — самим
       выражением (не `UNJUDGED_ELEMENT`), comprehension — целиком, с источником итерации,
       распаковка не-литерала `*name` — узлом `Starred`, и перечень ею не обрывается. Гейту
       писателя имя итерируемой безразлично — колонку оно не называет (граница (1) его шапки), —
       и он зовёт функцию без параметра: его ответ прежний. Гейт приватности судит именно
       имена (правило (б) D-17): до плана 16-38 общая функция гасила у `map` не-литеральную
       итерируемую, и `list(map(logger.info, account.phones))`, ловившийся на `c6953017^`,
       уходил мимо после коммита `c6953017` (16-32), который перевёл гейт на эту функцию.
    Пустые `args` и `keywords` значат, что ссылке ничего не подано: судить нечего, и
    вызывающий гейт решает, считать ли это вызовом.
    """
    if isinstance(call.func, ast.Call) and _callee_name(call.func.func) not in not_carriers:
        found = _carried_by(
            call.func,
            is_reference,
            list(call.args),
            list(call.keywords),
            every_reading,
            keep_iterables,
        )
        if found:
            return found
    return _carried_by(call, is_reference, [], [], every_reading, keep_iterables)


def carrier_wrapper_bindings(
    bindings: list[Binding], is_wrapper, nested: bool = False
) -> dict[str, list[ast.Call]]:
    """Имена, связанные с обёрткой носителя: «имя → обёртки» (самопроверка исполнителя 16-34).

    `w = functools.partial(asyncio.to_thread, setattr); w(account, "phone", x)` — то же
    применение `partial(…)(…)`, что и на месте, разделённое связыванием: ссылка — в
    аргументах обёртки, аргументы применения приходят с вызова `w(…)` (`applied_wrapper`).
    Что считать обёрткой, решает предикат гейта `is_wrapper` (вызов `partial` над носителем,
    в аргументах которого `reference_arguments` находит ссылку). Связывание — любой формой
    общей грамматики (`module_bindings`), цепочка `h = w` — тоже, до неподвижной точки;
    каждое связывание имени судится (ревью WR-18). Эту функцию зовут оба гейта — гейт
    писателя с плана 16-34, гейт приватности с плана 16-37 (ревью WR-24, решение владельца
    О-16 (а), свойство 5): до него гейт приватности держал свою копию неподвижной точки
    (`_carrier_wrappers`, самопроверка исполнителя 16-32, цикл 2), и копия расходилась с
    гейтом писателя.

    `nested=True` (ревью WR-26, план 16-36; О-16 (а), свойство 3): предикат зовётся
    `is_wrapper(value, found)` и видит уже найденные связывания — обёртка поверх обёртки
    под именем (`w2 = partial(asyncio.to_thread, w)`) становится обёрткой, как только `w`
    найдена; неподвижная точка — та же, рекурсивно, с защитой от цикла (имя, ещё не
    найденное, обёрткой не считается: `a = partial(to_thread, b); b = partial(ctx.run, a)`
    без пишущей ссылки — пусто). При `nested=False` предикат зовётся как прежде.
    """
    found: dict[str, list[ast.Call]] = {}
    changed = True
    while changed:
        changed = False
        for binding in bindings:
            name = binding_name(binding.target)
            if name is None:
                continue
            value = binding.value
            if isinstance(value, ast.Call):
                wrapper = is_wrapper(value, found) if nested else is_wrapper(value)
                values = [value] if wrapper else []
            elif isinstance(value, (ast.Name, ast.Attribute)):
                values = list(found.get(binding_name(value) or "", ()))
            else:
                values = []
            for wrapper in values:
                known = found.setdefault(name, [])
                if all(wrapper is not other for other in known):
                    known.append(wrapper)
                    changed = True
    return found


def applied_wrapper(call: ast.Call, wrapper: ast.Call) -> ast.Call:
    """Вызов `w(…)` имени, связанного с обёрткой, — как применение `wrapper(…)` на месте `call`."""
    return ast.copy_location(
        ast.Call(func=wrapper, args=list(call.args), keywords=list(call.keywords)), call
    )


def is_carrier_wrapper(
    value: ast.AST,
    partial_names,
    is_reference,
    not_carriers,
    known: dict[str, list[ast.Call]],
    _seen: frozenset[int] = frozenset(),
) -> bool:
    """Обёртка ли носителя `value` — общий рекурсивный предикат обоих гейтов (ревью WR-26; О-16 (а)).

    Обёртка носителя — вызов, последнее имя которого в `partial_names` (`functools.partial`
    и его псевдонимы в модуле), первым позиционным которого стоит НЕ ссылка (`is_reference`
    гейта: такой `partial` — псевдоним с привязанными аргументами, его гейт судит по-своему),
    и в аргументах которого `reference_arguments` находит ссылку ИЛИ другую обёртку —
    литералом (этот же предикат, рекурсивно: `partial(partial(ctx.run, setattr))`, глубина
    любая) или именем из `known` (обёртка под именем, уже найденная `carrier_wrapper_bindings`:
    `w2 = partial(asyncio.to_thread, w)`). Защита от цикла — по `id` узла (`_seen`). Свойства
    3 и 5 решения владельца О-16 (а): аргумент-обёртка раскрывается, и семантика обёртки
    живёт один раз — здесь; гейт даёт только имена `partial` и свой предикат ссылки. До плана
    16-36 у гейта писателя предикат обёртки знал только ссылку, и обёртку, обёрнутую ещё
    одним `partial` или поданную `partial` под именем, не видел ни один гейт.
    """
    if not isinstance(value, ast.Call) or id(value) in _seen:
        return False
    if _callee_name(value.func) not in partial_names:
        return False
    positional = expanded_arguments(list(value.args))
    if positional and positional[0] is not None and is_reference(positional[0]):
        return False
    seen = _seen | {id(value)}

    def carried(node: ast.expr) -> bool:
        if is_reference(node):
            return True
        if isinstance(node, ast.Call) and getattr_literal(node) is None:
            return is_carrier_wrapper(node, partial_names, is_reference, not_carriers, known, seen)
        return bool(named_wrappers(node, lambda _call: False, known))

    return bool(reference_arguments(value, carried, not_carriers))


def named_wrappers(node: ast.AST, is_wrapper, bound: dict[str, list[ast.Call]]) -> list[ast.Call]:
    """Обёртки носителя, которые называет выражение `node` (ревью CR-03, WR-26; О-16 (а)).

    Литеральный вызов, на котором предикат гейта `is_wrapper` истинен, — сама обёртка;
    имя (`Name.id`), атрибут (`Attribute.attr`) и getattr-строка (`getattr_literal`) —
    обёртки, связанные с этим именем (`bound`, отображение `carrier_wrapper_bindings`);
    иначе — пусто. Одна и та же функция судит обёртку и там, где её вызывают
    (`w(…)`, `self.w(…)`, `getattr(obj, "w")(…)`), и там, где её подают носителю. Имя
    читает общий читатель `reading_name` (ревью WR-28, план 16-42; О-18 (а), свойство 2) —
    тот же, что у имени `methodcaller` и у ссылки гейта писателя.
    """
    if isinstance(node, ast.Call) and is_wrapper(node):
        return [node]
    name = reading_name(node)
    return list(bound.get(name, ())) if name is not None else []


class WrapperApplication(NamedTuple):
    """Одно применение обёртки носителя: где её прочитали, какая она и как применена.

    `read` — узел, которым обёртка прочитана (вызываемое `w` / `self.w` / `getattr(obj,
    "w")` или ссылка, поданная носителю, — имя или сам литерал обёртки); `wrapper` — вызов
    `partial(<носитель>, …)`; `application` — синтетический вызов `applied_wrapper` на месте
    внешнего вызова, с аргументами, которые обёртке подаст внешний вызов.
    """

    read: ast.expr
    wrapper: ast.Call
    application: ast.Call


def wrapper_applications(
    call: ast.Call,
    wrappers_of,
    not_carriers,
    every_reading: bool = False,
    keep_iterables: bool = False,
) -> list[WrapperApplication]:
    """Применения обёрток носителя в вызове `call` — рекурсивно, с защитой от цикла.

    Ревью CR-03 и WR-26 (верификация раунда 7, 2026-10-16), решение владельца О-16 (а),
    свойства 2 и 3: обёртка носителя под именем судится ВЕЗДЕ, где её имя прочитано, а
    не только у вызова, и аргумент-обёртка раскрывается. До плана 16-36 гейт писателя
    судил обёртку под именем только у вызова `w(…)`, а поглощал её по любому чтению
    (коммит `147f5e46`): `func_call = partial(ctx.run, setattr, account, "phone", x);
    await loop.run_in_executor(None, func_call)` — дословное тело `asyncio.to_thread` —
    уходил мимо гейта; обёртку, поданную другому носителю (`run_in_executor(None,
    partial(ctx.run, setattr), account, "phone", x)`) или обёрнутую ещё одним `partial`,
    не ловил ни один гейт. `wrappers_of(node)` — обёртки, которые называет узел
    (`named_wrappers` с предикатом и отображением гейта). Применения:
    1. Вызываемое `call.func` называет обёртку — `w(…)`, `self.w(…)`, `getattr(obj,
       "w")(…)`: применение `applied_wrapper(call, w)`. Литеральный `partial(…)(…)` здесь
       не повторяется — его судит правило 1 `reference_arguments`.
    2. Обёртка, поданная носителю `call`, — каждая ссылка, которую `reference_arguments(call,
       <узел называет обёртку>, not_carriers, every_reading)` находит: позицией, `*[…]`,
       любым именованным аргументом, внутри применённого `X(…)(…)` (так раскрывается и
       `partial(<обёртка>)(…)`), литералом и именем: применение `applied_wrapper(<вызов
       «ссылка(аргументы ссылки)» на месте call>, w)`.
    3. Рекурсивно — применения каждого полученного применения (обёртка, поданная обёртке);
       обёртка, уже стоящая на пути, второй раз не раскрывается (защита от цикла по `id`).
    4. `keep_iterables=True` (гейт приватности; самопроверка исполнителя 16-38, заход 1) —
       обёртка, поданная поэлементному носителю, получает и элементы (правило 5
       `reference_arguments`), и итерируемые целиком (правило 8): у обёртки журнала,
       поданной `map` / `pool.imap` над не-литералом или comprehension, имя итерируемой с
       `phone` судится, как у `map(logger.info, account.phones)` (ревью CR-02); элементы
       остаются — из них путь `methodcaller` берёт получателя. Равные применения не
       повторяются.
    Вызывающий гейт судит каждое `application` как носитель, а `read` — как чтение имени
    обёртки, которое судится: одно место — одна находка.
    """
    found: list[WrapperApplication] = []

    def is_named(node: ast.expr) -> bool:
        return bool(wrappers_of(node))

    def handed_readings(node: ast.Call) -> list[ReferenceArguments]:
        readings = reference_arguments(node, is_named, not_carriers, every_reading)
        if keep_iterables:
            known = {_dump(carried) for carried in readings}
            readings += [
                carried
                for carried in reference_arguments(node, is_named, not_carriers, every_reading, True)
                if _dump(carried) not in known
            ]
        return readings

    def visit(node: ast.Call, path: frozenset[int]) -> None:
        own: list[WrapperApplication] = []
        callee = node.func
        if not isinstance(callee, ast.Call) or getattr_literal(callee) is not None:
            own += [
                WrapperApplication(callee, wrapper, applied_wrapper(node, wrapper))
                for wrapper in wrappers_of(callee)
            ]
        for carried in handed_readings(node):
            handed = ast.copy_location(
                ast.Call(
                    func=carried.reference,
                    args=list(carried.args),
                    keywords=list(carried.keywords),
                ),
                node,
            )
            own += [
                WrapperApplication(carried.reference, wrapper, applied_wrapper(handed, wrapper))
                for wrapper in wrappers_of(carried.reference)
            ]
        for item in own:
            if id(item.wrapper) in path:
                continue
            found.append(item)
            visit(item.application, path | {id(item.wrapper)})

    visit(call, frozenset())
    return found


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
    `carrier.element` (одноэлементный список или `list([…])`); у носителя с непустым
    `carrier.last` и двумя и более позиционными аргументами последний заменяется на
    `carrier.last` — место не-литеральной итерируемой (план 16-39; у одного позиционного
    места нет). Шаблон носителя получает
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
        if carrier.last and len(positional) >= 2:
            positional[-1] = carrier.last
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
