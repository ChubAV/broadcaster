"""Правило-паритет гейтов номера: одна грамматика связывания и один перечень носителей ссылки.

ЗАЧЕМ. Гейт единственного писателя (`tests/test_application/
test_phone_single_writer_gate.py`, D-13) и гейт приватности номера
(`tests/test_phone_privacy_gate.py`, D-09 / D-17) решают один вопрос: какое имя модуль
связал с опознанным объектом — пишущим API или журналом — и какому вызову эту ссылку
подал. Пока у каждого гейта была своя грамматика и свой перечень носителей, ревью
находило форму, которую один гейт ловил, а другой нет: WR-14 — пишущий API, связанный
распаковкой, `:=`, `self.<x> =` в методе и `getattr`-строкой (гейт приватности эти формы
разбирал, гейт писателя — нет); WR-17 — ссылка на метод журнала, поданная
`asyncio.to_thread`, `loop.run_in_executor`, `map`, `Context.run` (гейт писателя ловил,
гейт приватности — нет). Решение владельца О-12 (а), 2026-10-13: заявления гейтов
прежние, оба гейта делят ОДНУ грамматику связывания и ОДИН перечень носителей ссылки —
модуль `tests/phone_gate_grammar.py`, — и расхождение гейтов краснит это правило.

ЧТО ПРОВЕРЯЕТСЯ.
* Построение: оба модуля гейтов ввозят `tests.phone_gate_grammar` и держат его имена
  `REQUIRED_SHARED_NAMES` (`module_bindings`, `REFERENCE_CARRIERS`, `BINDING_FORMS`,
  `reference_arguments`, `iterable_elements`, `getattr_literal` и семантику обёртки
  носителя `carrier_wrapper_bindings`, `applied_wrapper`, `named_wrappers`,
  `is_carrier_wrapper` — ревью WR-24, план 16-37; один читатель имени связанного
  `reading_name` — ревью WR-28, решение владельца О-18 (а), свойство 2: гейт писателя с
  плана 16-42, гейт приватности с плана 16-43) теми же объектами; на
  верхнем уровне модуля гейта нет функции с именем из `GRAMMAR_FUNCTIONS` — грамматика
  связывания (`binding_pairs`, `module_bindings`, `getattr_as_attribute`) И семантика
  носителя ссылки (`getattr_literal`, `iterable_elements`, `expanded_arguments`,
  `forwarded_arguments`, `elementwise_arguments`, `literal_keyword_arguments`,
  `reference_arguments`, `carrier_wrapper_bindings`, `applied_wrapper`, `named_wrappers`,
  `is_carrier_wrapper`, `reading_name`), каждое имя с подчёркиванием и без, — и присваивания таблицы
  с именем из `GRAMMAR_TABLES` (`ELEMENTWISE_CARRIERS`, `REFERENCE_CARRIERS`,
  `BINDING_FORMS`, `LITERAL_CONTAINER_WRAPPERS`, `UNJUDGED_ELEMENT`, выведенная планом
  16-34 `REFERENCE_KEYWORDS`): названные точки не переопределены. Копию под другим
  именем (`def _my_pairs(…)`, `MY_CARRIERS = …`) эта половина не видит по построению:
  её видит только поведенческая половина — и только на ячейках общего словаря.
  Правило-контроль `test_the_structural_half_reddens_a_redefined_grammar_point`
  доказывает, что структурная половина краснеет на каждом названном имени; `id`
  значений опознания (`API_IDENTIFICATION_VALUES`, `LOG_IDENTIFICATION_VALUES`)
  совпадают по порядку. Летопись — ревью IN-15 (верификация раунда 6, 2026-10-14): до
  плана 16-34 докстринг обещал, что копий нет вовсе, а правило сверяло четыре имени
  функций и четыре таблицы, и копии `_iterable_elements` / `_getattr_literal` жили в
  обоих гейтах; план 16-32 снял их у гейта приватности, план 16-34 — у гейта писателя,
  и имена семантики носителя вошли в `GRAMMAR_FUNCTIONS` (решение владельца О-15).
* Поведение: на каждой ячейке «форма `BINDING_FORMS` × значение опознания × прямой вызов
  и каждый носитель `REFERENCE_CARRIERS`» оба гейта находят — писатель запись номера,
  приватность номер в журнале. Ячейку обоих гейтов собирает одна функция
  `binding_form_source` общего модуля; своей сборки исходников здесь нет.
* Словарь седьмого круга (`test_the_shared_dictionary_holds_the_round_seven_axes`, план 16-39):
  девять строк `REFERENCE_CARRIERS` — поданная обёртка, обёртка в обёртке, именованная обёртка
  (вызов, передача, передача с аргументами, getattr-вариант), `starmap`, `apply_async` и место
  не-литеральной итерируемой у `map` (`ReferenceCarrier.last`), — так что регрессии
  `c6953017` и `147f5e46` краснят обе матрицы и это правило по построению.
* Место значения `partial` (`test_the_partial_value_place_is_pinned_by_a_privacy_row`, ревью
  IN-20, решение владельца О-19, план 16-43): у `partial` с одним позиционным аргументом (номером)
  места `last` нет по выбору словаря — его ячейка `map-named-iterable` равна ячейке `map`, — и
  форму `list(map(functools.partial(logger.info, "x %s"), account.phones))` держит строка
  `NEGATIVE_CONTROLS` `partial-log-reference-mapped-over-a-phone-attribute` гейта приватности с
  одной находкой; докстринг `ReferenceCarrier` называет эту строку, D-17 относит только к
  получателю `methodcaller`, а у `partial` называет выбор словаря.
* Формы вне грамматики (`OUT_OF_GRAMMAR_BINDING_FORMS`): ни один гейт не разрешает их
  связывание, и у каждой формы есть причина. Сравнивается связывание, а не сырое число
  находок: гейт писателя находит запись и там, где значение несёт её само
  (`methodcaller` со всеми аргументами записи), поэтому ячейка сверяется с базой — той
  же ячейкой, где имя на месте вызова ничем не связано; находка сверх базы значила бы,
  что гейт связывание разрешил (план 16-27, заметки волне 2).
"""

from __future__ import annotations

import ast
import inspect
import re
from collections import Counter
from types import ModuleType

import pytest

from tests import phone_gate_grammar as grammar
from tests import test_phone_privacy_gate as privacy
from tests.test_application import test_phone_single_writer_gate as writer

GRAMMAR_MODULE = "tests.phone_gate_grammar"

# Модули гейтов, которые обязаны делить общую грамматику.
GATE_MODULES: tuple[ModuleType, ...] = (writer, privacy)

# Семантика носителя ссылки общего модуля (план 16-32; ревью IN-15, О-15): имена,
# которые модуль гейта не переопределяет — ни так, ни с подчёркиванием.
CARRIER_SEMANTICS = (
    "getattr_literal",
    "iterable_elements",
    "expanded_arguments",
    "forwarded_arguments",
    "elementwise_arguments",
    "literal_keyword_arguments",
    "reference_arguments",
    # Семантика обёртки носителя (самопроверка исполнителя 16-34, заход 1; ревью CR-03,
    # WR-24, WR-26; решение владельца О-16 (а), свойство 5): оба гейта зовут эти функции
    # общего модуля — гейт писателя с планов 16-34 и 16-36, гейт приватности с плана 16-37,
    # который снял его копию (`_carrier_wrappers` с ручным применением, план 16-32).
    "carrier_wrapper_bindings",
    "applied_wrapper",
    "named_wrappers",
    "is_carrier_wrapper",
    "wrapper_applications",
    # Один читатель имени связанного в месте чтения (ревью WR-28, верификация раунда 8; решение
    # владельца О-18 (а), свойство 2): `f`, `self.f` и `getattr(self, "f")` читают одно имя `f`.
    # Гейт писателя зовёт его с плана 16-42, гейт приватности — с плана 16-43; своего читателя
    # имени (и копии с этим именем) модуль гейта не держит.
    "reading_name",
)

# Функции грамматики связывания И семантики носителя, которые модуль гейта не определяет
# сам (с подчёркиванием и без).
GRAMMAR_FUNCTIONS = frozenset(
    {"binding_pairs", "_binding_pairs", "module_bindings", "_module_bindings"}
    | {"getattr_as_attribute", "_getattr_as_attribute"}
    | {variant for name in CARRIER_SEMANTICS for variant in (name, f"_{name}")}
)

# Таблицы общего модуля, которые модуль гейта не присваивает сам. `REFERENCE_KEYWORDS` —
# закрытая таблица ключа ссылки, выведенная планом 16-34 (общее правило О-14 (а) судит
# любой именованный аргумент): модуль гейта не вправе завести её снова.
GRAMMAR_TABLES = frozenset(
    {"REFERENCE_KEYWORDS", "ELEMENTWISE_CARRIERS", "REFERENCE_CARRIERS", "BINDING_FORMS"}
    | {"LITERAL_CONTAINER_WRAPPERS", "UNJUDGED_ELEMENT", "_UNJUDGED_ELEMENT"}
    # Построчные носители (`starmap`, `starmap_async`) — одно правило обоих гейтов (ревью
    # CR-02 / WR-25, решение владельца О-16 (а), свойство 4, план 16-38).
    | {"ROW_CARRIERS", "_ROW_CARRIERS"}
)

# Объекты установленного stdlib, чьи методы с `map` в имени — носители, подающие функции
# элементы итерируемых (`multiprocessing.pool.Pool`, `concurrent.futures.Executor`, модуль
# `itertools`; замер stdlib 3.12, план 16-38).
MAP_CARRIER_OWNERS = ("multiprocessing.pool.Pool", "concurrent.futures.Executor", "itertools")

# Имена общего модуля, которые обязан держать (ввозом) каждый гейт — тем же объектом.
REQUIRED_SHARED_NAMES = frozenset(
    {"module_bindings", "REFERENCE_CARRIERS", "BINDING_FORMS"}
    | {"reference_arguments", "iterable_elements", "getattr_literal"}
    # Семантика обёртки носителя (ревью WR-24, решение владельца О-16 (а), свойство 5): оба
    # гейта держат эти функции общего модуля теми же объектами.
    | {"carrier_wrapper_bindings", "applied_wrapper", "named_wrappers", "is_carrier_wrapper"}
    # Применения обёртки — вызванной и поданной, рекурсивно (ревью WR-26, О-16 (а), свойство 3).
    | {"wrapper_applications"}
    # Один читатель имени связанного у обоих гейтов (ревью WR-28, О-18 (а), свойство 2; планы
    # 16-42 и 16-43).
    | {"reading_name"}
)

# Имя на месте вызова, которое ничем не связано: база сверки форм вне грамматики.
NEVER_BOUND_REF = "never_bound_fn"


def own_grammar_problems(tree: ast.Module) -> list[str]:
    """Чем модуль гейта нарушает общую грамматику: нет ввоза, своя функция, своя таблица."""
    problems: list[str] = []
    imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    imported |= {
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    }
    if GRAMMAR_MODULE not in imported:
        problems.append(f"не ввозит `{GRAMMAR_MODULE}`")
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in GRAMMAR_FUNCTIONS:
            problems.append(f"определяет свою функцию грамматики `{node.name}` (строка {node.lineno})")
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id in GRAMMAR_TABLES:
                problems.append(f"присваивает свою таблицу `{target.id}` (строка {node.lineno})")
    return problems


def _writer_finds(source: str) -> bool:
    """Гейт писателя находит ровно одну запись `KIND_SETATTR`, называющую API и `phone`."""
    offences = writer.phone_write_offences(source, "scripts/x.py")
    if len(offences) != 1:
        return False
    _location, kind, subject = offences[0].split(" — ", 2)
    return kind == writer.KIND_SETATTR and "set_committed_value" in subject and "phone" in subject


def _privacy_finds(source: str) -> bool:
    """Гейт приватности находит номер в журнале: находки непусты и называют `phone`."""
    offences = privacy.python_log_offences(source, "app/x.py")
    return bool(offences) and all("phone" in offence for offence in offences)


def _located_kinds(offences: list[str]) -> Counter[tuple[str, str]]:
    """Находки как мультимножество «место — вид»: предмет может называть имя на месте вызова."""
    return Counter(tuple(offence.split(" — ", 2)[:2]) for offence in offences)


def _resolves_binding(offences_of, form, value, carrier) -> bool:
    """Гейт разрешил связывание формы: находок ячейки больше, чем у базы с несвязанным именем."""
    cell = offences_of(grammar.binding_form_source(form, value, carrier))
    base = offences_of(grammar.binding_form_source(form._replace(ref=NEVER_BOUND_REF), value, carrier))
    return bool(_located_kinds(cell) - _located_kinds(base))


def test_both_gates_take_the_binding_grammar_and_carriers_from_one_module():
    """Построение паритета: общий модуль ввезён, названные точки грамматики не переопределены.

    Паритет держится по построению, пока грамматика, перечень носителей и семантика
    носителя определены один раз — в `tests/phone_gate_grammar.py`. Правило проверяет
    ровно названное: ввоз общего модуля; имена `REQUIRED_SHARED_NAMES` — те же объекты;
    на верхнем уровне модуля гейта нет функции с именем из `GRAMMAR_FUNCTIONS` и
    присваивания таблицы с именем из `GRAMMAR_TABLES`. Копию под другим именем оно не
    видит — её ловит только поведенческая половина на ячейках общего словаря (ревью IN-15,
    О-15). Вторая копия в модуле гейта (свой `_binding_pairs`, свой перечень носителей,
    свой `_iterable_elements`) — та асимметрия, на которой открывались круги WR-14, WR-17 и
    WR-19 (решение владельца О-12 (а)).
    """
    problems: list[str] = []
    for module in GATE_MODULES:
        tree = ast.parse(inspect.getsource(module))
        problems += [f"{module.__name__}: {problem}" for problem in own_grammar_problems(tree)]
        for name in sorted(REQUIRED_SHARED_NAMES - set(vars(module))):
            problems.append(f"{module.__name__}: не держит общее имя `{name}`")
        # Имя, которого в общем модуле нет (`_UNJUDGED_ELEMENT`, выведенный `REFERENCE_KEYWORDS`),
        # у гейта — тоже своя таблица, а не объект общего модуля.
        for name in sorted((GRAMMAR_TABLES | REQUIRED_SHARED_NAMES) & set(vars(module))):
            if getattr(module, name) is not getattr(grammar, name, None):
                problems.append(f"{module.__name__}: `{name}` — не объект общего модуля")
    writer_ids = [value.id for value in writer.API_IDENTIFICATION_VALUES]
    privacy_ids = [value.id for value in privacy.LOG_IDENTIFICATION_VALUES]
    if writer_ids != privacy_ids:
        problems.append(f"`id` значений опознания расходятся: писатель {writer_ids}, приватность {privacy_ids}")

    assert not problems, "гейты номера не делят одну грамматику связывания:\n" + "\n".join(
        f"  {problem}" for problem in problems
    )


def test_the_elementwise_and_row_carriers_name_the_installed_apis():
    """Сторож таблиц носителей: `ELEMENTWISE_CARRIERS | ROW_CARRIERS` — ровно методы с `map` stdlib.

    Какие носители поэлементны (`map`, `imap`, `imap_unordered`, `map_async` — функция
    получает элемент каждой итерируемой) и построчны (`starmap`, `starmap_async` — функция
    получает элементы каждой строки), решает одно правило общего модуля для обоих гейтов
    (ревью CR-02 / WR-25, решение владельца О-16 (а), свойство 4). До плана 16-38 таблица
    знала один `map`: `pool.imap(logger.info, …)` гейт приватности судил целиком, а
    `map(logger.info, …)` — поэлементно (правило противоречило себе внутри гейта), прочтение
    строк `starmap` было только у гейта писателя. Публичные методы с `map` в имени у
    `MAP_CARRIER_OWNERS` (`dir()`, без ведущего `_`) — ровно объединение таблиц, а таблицы не
    пересекаются: подъём Python, назвавший новый такой метод, краснит суиту, а не оставляет
    его гейтам неклассифицированным (по образцу сторожа асинхронных уровней structlog).
    """
    import concurrent.futures
    import itertools
    import multiprocessing.pool

    owners = (multiprocessing.pool.Pool, concurrent.futures.Executor, itertools)
    installed = {name for owner in owners for name in dir(owner) if "map" in name and not name.startswith("_")}
    elementwise = getattr(grammar, "ELEMENTWISE_CARRIERS", frozenset())
    rows = getattr(grammar, "ROW_CARRIERS", frozenset())

    assert installed, "у установленного stdlib не найдено ни одного метода с `map` — сверка вакуумна"
    assert installed == elementwise | rows and not (elementwise & rows), (
        "носитель с `map` не классифицирован как поэлементный или построчный: "
        f"установлено {sorted(installed)} ({', '.join(MAP_CARRIER_OWNERS)}), "
        f"нет в таблицах {sorted(installed - (elementwise | rows))}, "
        f"нет в stdlib {sorted((elementwise | rows) - installed)}, "
        f"в обеих таблицах {sorted(elementwise & rows)}"
    )


# Девять строк словаря седьмого круга (ревью CR-02, CR-03, WR-24, WR-25, WR-26; верификация
# раунда 7; решение владельца О-16 (а), свойство 6; план 16-39).
ROUND_SEVEN_CARRIERS = (
    "wrapper-handed",
    "wrapper-of-wrapper",
    "named-wrapper-called",
    "named-wrapper-handed",
    "named-wrapper-bound-handed",
    "named-wrapper-getattr",
    "starmap",
    "apply-async",
    "map-named-iterable",
)


def test_the_shared_dictionary_holds_the_round_seven_axes():
    """Словарь матриц и паритета держит оси седьмого круга и смысл места `last`.

    Ни одно правило суиты не краснело на регрессиях `c6953017` (CR-02: итерируемая
    поэлементного носителя у гейта приватности судилась поэлементно) и `147f5e46` (CR-03:
    обёртка под именем, переданная исполнителю, не судилась гейтом писателя): строки `map`
    словаря литеральны, именованной и поданной обёртки, `starmap` и `apply_async` в словаре не
    было. Матрицы зелёные и без этих строк, поэтому их удаление ничего бы не покраснило — это
    правило держит (а) девять `id` и не меньше 20 носителей; (б) у `map-named-iterable` поле
    `last` — выражение-не-литерал (не список, кортеж или набор), называющее `phone`; (в) смысл
    места: `binding_form_source` ставит `last` на место ПОСЛЕДНЕГО позиционного аргумента
    применения, когда их два и более, а у значения с одним позиционным (получатель
    `methodcaller`) места нет — аргументы прежние, получатель обязан быть опознан (D-17). Без
    места ячейка видела бы регрессию CR-02 только по литералу (решение владельца О-16 (а),
    свойство 6; план 16-39).
    """
    problems: list[str] = []
    carriers = {carrier.id: carrier for carrier in grammar.REFERENCE_CARRIERS}
    for carrier_id in ROUND_SEVEN_CARRIERS:
        if carrier_id not in carriers:
            problems.append(f"нет строки `{carrier_id}`")
    if len(grammar.REFERENCE_CARRIERS) < 20:
        problems.append(f"носителей {len(grammar.REFERENCE_CARRIERS)} — меньше 20")
    named_iterable = carriers.get("map-named-iterable")
    last = getattr(named_iterable, "last", "") if named_iterable is not None else ""
    if not last:
        problems.append("у `map-named-iterable` нет места не-литеральной итерируемой (`last`)")
    else:
        node = ast.parse(last, mode="eval").body
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            problems.append(f"`last` строки `map-named-iterable` — литерал: `{last}`")
        if "phone" not in last:
            problems.append(f"`last` строки `map-named-iterable` не называет `phone`: `{last}`")
    if named_iterable is not None and named_iterable.name not in grammar.ELEMENTWISE_CARRIERS:
        problems.append(f"`map-named-iterable` не поэлементный носитель: `{named_iterable.name}`")
    if named_iterable is not None and last:
        form = grammar.BINDING_FORMS[0]
        two = grammar.IdentificationValue("two", "probe_fn", "(first, second)")
        one = grammar.IdentificationValue("one", "probe_fn", "(receiver)")
        for value, expected in ((two, ["[first]", last]), (one, ["[receiver]"])):
            source = grammar.binding_form_source(form, value, named_iterable)
            calls = [
                node
                for node in ast.walk(ast.parse(source))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "map"
            ]
            got = [ast.unparse(argument) for argument in calls[0].args[1:]] if calls else None
            if got != expected:
                problems.append(f"ячейка `{value.id}`: аргументы `map` {got}, ожидалось {expected}")

    assert not problems, "словарь матриц и паритета не держит ось седьмого круга:\n" + "\n".join(
        f"  {problem}" for problem in problems
    )


# Форма словаря восьмого круга (ревью WR-28, верификация раунда 8; решение владельца О-18 (а),
# свойство 3; план 16-44): чтение имени getattr-строкой.
ROUND_EIGHT_FORM = "getattr-read"
ROUND_EIGHT_REF = 'getattr(self, "f")'


def _method_of(tree: ast.Module, predicate) -> str | None:
    """Имя метода класса, в теле которого есть узел, удовлетворяющий `predicate`."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(predicate(inner) for inner in ast.walk(node)):
                return node.name
    return None


def _round_eight_form_problems() -> list[str]:
    """Чем словарь не держит форму `getattr-read`: строка, ссылка, места связывания и чтения."""
    problems: list[str] = []
    form = next((form for form in grammar.BINDING_FORMS if form.id == ROUND_EIGHT_FORM), None)
    if form is None:
        return [f"в `BINDING_FORMS` нет формы `{ROUND_EIGHT_FORM}`"]
    if form.ref != ROUND_EIGHT_REF:
        problems.append(f"ссылка формы `{ROUND_EIGHT_FORM}` — `{form.ref}`, ожидалось `{ROUND_EIGHT_REF}`")
    template = form.template.replace("{value}", "VALUE_PROBE").replace("{use}", "USE_PROBE()")
    template = template.replace("{decoy}", "DECOY_PROBE")
    tree = ast.parse(template)

    def binds(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Assign)
            and any(ast.unparse(target) == "self.f" for target in node.targets)
            and isinstance(node.value, ast.Name)
            and node.value.id == "VALUE_PROBE"
        )

    def uses(node: ast.AST) -> bool:
        return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "USE_PROBE"

    bound_in, used_in = _method_of(tree, binds), _method_of(tree, uses)
    if bound_in != "__init__":
        problems.append(f"форма `{ROUND_EIGHT_FORM}` связывает `self.f = {{value}}` не в `__init__`: {bound_in}")
    if used_in is None or used_in == bound_in:
        problems.append(f"место `{{use}}` формы `{ROUND_EIGHT_FORM}` не в другом методе: {used_in}")
    probe = grammar.IdentificationValue("probe", "probe_fn", "(first)")
    source = grammar.binding_form_source(form, probe, None)
    if f"{ROUND_EIGHT_REF}(" not in source:
        problems.append(f"ячейка формы `{ROUND_EIGHT_FORM}` не читает имя getattr-строкой: {source!r}")
    return problems


# Значение опознания словаря восьмого круга (ревью WR-28; решение владельца О-18 (а), свойство 3;
# план 16-44): `methodcaller`, чья колонка приходит получателем, у гейта писателя и пара с тем же
# `id` у гейта приватности — `methodcaller` над журналом из вызова фабрики.
ROUND_EIGHT_VALUE = "methodcaller-receiver"


def _methodcaller_call(text: str) -> ast.Call | None:
    """Литеральный вызов `operator.methodcaller(…)` значения опознания, иначе `None`."""
    node = ast.parse(text, mode="eval").body
    if isinstance(node, ast.Call) and ast.unparse(node.func).split(".")[-1] == "methodcaller" and node.args:
        return node
    return None


def _round_eight_value_problems() -> list[str]:
    """Чем словарь не держит значение `methodcaller-receiver` и таблицу API значений писателя."""
    problems: list[str] = []
    writer_ids = [value.id for value in writer.API_IDENTIFICATION_VALUES]
    privacy_ids = [value.id for value in privacy.LOG_IDENTIFICATION_VALUES]
    for side, ids in (("писателя", writer_ids), ("приватности", privacy_ids)):
        if ROUND_EIGHT_VALUE not in ids:
            problems.append(f"у гейта {side} нет значения опознания `{ROUND_EIGHT_VALUE}`")
    if ROUND_EIGHT_VALUE in writer_ids and ROUND_EIGHT_VALUE in privacy_ids:
        if writer_ids.index(ROUND_EIGHT_VALUE) != privacy_ids.index(ROUND_EIGHT_VALUE):
            problems.append(f"значение `{ROUND_EIGHT_VALUE}` у гейтов на разных позициях: {writer_ids}, {privacy_ids}")
        writer_value = writer.API_IDENTIFICATION_VALUES[writer_ids.index(ROUND_EIGHT_VALUE)]
        call = _methodcaller_call(writer_value.value)
        if call is None or not (isinstance(call.args[0], ast.Constant) and call.args[0].value == "__set__"):
            problems.append(f"значение писателя `{ROUND_EIGHT_VALUE}` — не `methodcaller(\"__set__\", …)`: "
                            f"`{writer_value.value}`")
        if "MessengerAccount.phone" not in writer_value.call:
            problems.append(f"получатель значения писателя `{ROUND_EIGHT_VALUE}` не называет колонку "
                            f"`MessengerAccount.phone`: `{writer_value.call}`")
        privacy_value = privacy.LOG_IDENTIFICATION_VALUES[privacy_ids.index(ROUND_EIGHT_VALUE)]
        call = _methodcaller_call(privacy_value.value)
        if call is None or not any("phone" in ast.unparse(argument) for argument in call.args[1:]):
            problems.append(f"значение приватности `{ROUND_EIGHT_VALUE}` — не `methodcaller` над журналом с номером "
                            f"в своих аргументах: `{privacy_value.value}`")
        if "phone" in privacy_value.call:
            problems.append(f"получатель значения приватности `{ROUND_EIGHT_VALUE}` несёт номер: `{privacy_value.call}`")
    calls = getattr(writer, "API_IDENTIFICATION_CALLS", None)
    if not isinstance(calls, dict):
        problems.append("у гейта писателя нет таблицы `API_IDENTIFICATION_CALLS` (API каждого значения опознания)")
    else:
        unnamed = [value_id for value_id in writer_ids if not calls.get(value_id)]
        if unnamed:
            problems.append(f"`API_IDENTIFICATION_CALLS` не называет API значений {unnamed}")
        stray = sorted(set(calls) - set(writer_ids))
        if stray:
            problems.append(f"`API_IDENTIFICATION_CALLS` называет значения, которых нет в таблице: {stray}")
        if calls.get(ROUND_EIGHT_VALUE) != "__set__":
            problems.append(f"`API_IDENTIFICATION_CALLS` у `{ROUND_EIGHT_VALUE}` — {calls.get(ROUND_EIGHT_VALUE)!r}, "
                            "ожидалось `__set__`")
    return problems


def test_the_shared_dictionary_holds_the_round_eight_axes():
    """Словарь матриц и паритета держит оси восьмого круга: чтение имени getattr-строкой и
    `methodcaller` с получателем-колонкой.

    Ни одна форма `BINDING_FORMS` не читала связанное имя getattr-строкой, поэтому ни обе
    матрицы, ни это правило, ни корпуса самопроверок исполнителей раунда 7 (≈142 000 форм) такого
    чтения не собирали: `self.f = operator.methodcaller("__set__", account, x)` с
    `getattr(self, "f")(MessengerAccount.phone)` проходил оба гейта (ревью WR-28, верификация
    раунда 8). Правило держит (а) форму `getattr-read`: ссылка `getattr(self, "f")`, связывание
    `self.f = {value}` в `__init__`, место `{use}` — в другом методе, ячейка читает имя
    getattr-строкой; (б) значение опознания `methodcaller-receiver` у обоих гейтов на одной
    позиции: у писателя `methodcaller("__set__", …)`, применённый к получателю, называющему
    `MessengerAccount.phone` (иначе матрица этот вид не видит), у приватности — `methodcaller` над
    журналом, номер — в его аргументах; (в) таблицу `API_IDENTIFICATION_CALLS` гейта писателя —
    API, который называет находка ячейки, для КАЖДОГО значения опознания писателя (у
    `methodcaller-receiver` — `__set__`), без умолчания; её читают правило-матрица гейта писателя
    и это правило-паритет, своей копии здесь нет. Возврат чтения имени только у `Name` /
    `Attribute` (класс WR-28) краснит обе матрицы и правило-паритет на этой строке для каждого
    значения и носителя (решение владельца О-18 (а), свойство 3; план 16-44).
    """
    problems = _round_eight_form_problems() + _round_eight_value_problems()

    assert not problems, "словарь матриц и паритета не держит ось восьмого круга:\n" + "\n".join(
        f"  {problem}" for problem in problems
    )


# Строка гейта приватности, которая держит место не-литеральной итерируемой у значения `partial`
# (ревью IN-20, решение владельца О-19, план 16-43).
PARTIAL_VALUE_PLACE_ROW = "partial-log-reference-mapped-over-a-phone-attribute"


def _sentences(text: str) -> list[str]:
    """Предложения текста с схлопнутыми пробелами: граница — точка перед заглавной буквой."""
    return re.split(r"(?<=\.)\s+(?=[А-ЯЁA-Z])", " ".join(text.split()))


def test_the_partial_value_place_is_pinned_by_a_privacy_row():
    """Место не-литеральной итерируемой у значения `partial` держит строка гейта приватности, довод правдив.

    У значения `partial` (`functools.partial(logger.info, "x %s")` с `(account.phone)`) один
    позиционный аргумент — номер, и `binding_form_source` места `last` ему не даёт: ячейка
    `map-named-iterable` у этого значения совпадает с ячейкой `map`. Форму
    `list(map(functools.partial(logger.info, "x %s"), account.phones))` гейт ловит с плана 16-38
    (на `1c243203` — `[]`), но до плана 16-43 её не держали ни строка таблицы, ни ячейка матрицы, а
    докстринг `ReferenceCarrier` объяснял отсутствие места у `partial` правилом получателя D-17 —
    ложно: у `partial` единственный аргумент — номер, а не получатель (ревью IN-20, верификация
    раунда 8). Решение владельца О-19: довод исправлен, форма закреплена строкой. Правило держит
    (а) строку `PARTIAL_VALUE_PLACE_ROW` в `NEGATIVE_CONTROLS` гейта приватности: её исходник
    применяет `map` к `functools.partial(logger.info, …)` над не-литеральной итерируемой с
    `phone`, и гейт даёт ровно одну находку; (б) докстринг `ReferenceCarrier` называет `id`
    строки; (в) D-17 он называет в одном предложении с `methodcaller` и ни в одном — с `partial`,
    а у `partial` называет выбор словаря («по выбору словаря»).
    """
    problems: list[str] = []
    rows = {param.id: param.values for param in privacy.NEGATIVE_CONTROLS}
    row = rows.get(PARTIAL_VALUE_PLACE_ROW)
    if row is None:
        problems.append(f"в `NEGATIVE_CONTROLS` гейта приватности нет строки `{PARTIAL_VALUE_PLACE_ROW}`")
    else:
        path, source, _subject = row
        mapped = [
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "map"
            and node.args
            and isinstance(node.args[0], ast.Call)
            and ast.unparse(node.args[0].func).split(".")[-1] == "partial"
            and node.args[0].args
            and ast.unparse(node.args[0].args[0]) == "logger.info"
            and any(
                not isinstance(iterable, (ast.List, ast.Tuple, ast.Set)) and "phone" in ast.unparse(iterable)
                for iterable in node.args[1:]
            )
        ]
        if not mapped:
            problems.append(
                f"строка `{PARTIAL_VALUE_PLACE_ROW}` не применяет `map` к `functools.partial(logger.info, …)` "
                f"над не-литеральной итерируемой с `phone`: {source!r}"
            )
        offences = privacy.python_log_offences(source, path)
        if len(offences) != 1 or "phone" not in offences[0]:
            problems.append(f"строка `{PARTIAL_VALUE_PLACE_ROW}`: гейт дал не одну находку с `phone`: {offences}")
    doc = grammar.ReferenceCarrier.__doc__ or ""
    if PARTIAL_VALUE_PLACE_ROW not in " ".join(doc.split()):
        problems.append(f"докстринг `ReferenceCarrier` не называет строку `{PARTIAL_VALUE_PLACE_ROW}`")
    sentences = _sentences(doc)
    with_rule = [sentence for sentence in sentences if "D-17" in sentence]
    if not any("methodcaller" in sentence for sentence in with_rule):
        problems.append("докстринг `ReferenceCarrier` не называет D-17 в одном предложении с `methodcaller`")
    for sentence in with_rule:
        if "partial" in sentence:
            problems.append(f"докстринг `ReferenceCarrier` относит D-17 к `partial`: «{sentence}»")
    if not any("partial" in sentence and "по выбору словаря" in sentence for sentence in sentences):
        problems.append("докстринг `ReferenceCarrier` не называет у `partial` выбор словаря («по выбору словаря»)")

    assert not problems, (
        "место значения `partial` у `map` над не-литеральной итерируемой не закреплено строкой гейта "
        "приватности, или довод `ReferenceCarrier.last` ложен:\n" + "\n".join(f"  {problem}" for problem in problems)
    )


def test_the_structural_half_reddens_a_redefined_grammar_point():
    """Контроль структурной половины: переопределение КАЖДОЙ названной точки краснит её.

    Для каждого имени `GRAMMAR_FUNCTIONS` — синтетический модуль гейта, который ввозит
    `tests.phone_gate_grammar` и определяет на верхнем уровне функцию этого имени; для
    каждого имени `GRAMMAR_TABLES` — модуль с присваиванием этого имени. `own_grammar_problems`
    обязан назвать каждое: иначе структурная половина паритета молчит на копии, которую
    обещает видеть. Копию под ДРУГИМ именем эта половина не видит по построению — её видит
    только поведенческая половина, и только на ячейках общего словаря (ревью IN-15, О-15).
    """
    names = sorted(GRAMMAR_FUNCTIONS) + sorted(GRAMMAR_TABLES)
    assert len(names) >= 20, f"названных точек {len(names)} — меньше 20: контроль проверяет почти ничто"
    head = f"from {GRAMMAR_MODULE} import module_bindings\n\n\n"
    silent: list[str] = []
    for name in sorted(GRAMMAR_FUNCTIONS):
        problems = own_grammar_problems(ast.parse(f"{head}def {name}(node):\n    return node\n"))
        if not any(f"`{name}`" in problem for problem in problems):
            silent.append(f"  функция `{name}`: {problems}")
    for name in sorted(GRAMMAR_TABLES):
        problems = own_grammar_problems(ast.parse(f"{head}{name} = frozenset()\n"))
        if not any(f"`{name}`" in problem for problem in problems):
            silent.append(f"  таблица `{name}`: {problems}")
    clean = own_grammar_problems(ast.parse(f"{head}def unrelated(node):\n    return node\n"))

    assert not silent, (
        "структурная половина паритета не видит переопределённую точку грамматики:\n"
        + "\n".join(silent)
    )
    assert clean == [], f"структурная половина краснит модуль без переопределений: {clean}"


@pytest.mark.parametrize("form", [pytest.param(f, id=f.id) for f in grammar.BINDING_FORMS])
def test_both_gates_agree_on_every_binding_form_identification_and_carrier(form: grammar.BindingForm):
    """Поведение паритета: на каждой ячейке оба гейта находят — писатель запись, приватность номер.

    Ячейка — форма связывания × значение опознания (общий `id`: имя, атрибут,
    `getattr`-строка, `partial`, `methodcaller`) × прямой вызов и каждый носитель
    `REFERENCE_CARRIERS`. Гейт писателя судит ячейку со значением
    `API_IDENTIFICATION_VALUES`, гейт приватности — с `LOG_IDENTIFICATION_VALUES` того же
    `id`; обе собирает `binding_form_source`. Промахи делятся на расхождение гейтов (одна
    сторона ловит, другая — нет) и общий пропуск.
    """
    cells = [
        (writer_value, privacy_value, carrier)
        for writer_value, privacy_value in zip(
            writer.API_IDENTIFICATION_VALUES, privacy.LOG_IDENTIFICATION_VALUES, strict=True
        )
        for carrier in (None, *grammar.REFERENCE_CARRIERS)
    ]
    assert len(cells) >= 30, f"ячеек формы {len(cells)} — меньше 30: паритет проверяет почти ничто"
    only_writer: list[str] = []
    only_privacy: list[str] = []
    both_miss: list[str] = []
    for writer_value, privacy_value, carrier in cells:
        writer_found = _writer_finds(grammar.binding_form_source(form, writer_value, carrier))
        privacy_found = _privacy_finds(grammar.binding_form_source(form, privacy_value, carrier))
        cell = f"  {writer_value.id} / {carrier.name if carrier is not None else 'прямой вызов'}"
        if writer_found and not privacy_found:
            only_writer.append(cell)
        elif privacy_found and not writer_found:
            only_privacy.append(cell)
        elif not writer_found and not privacy_found:
            both_miss.append(cell)

    sections = [
        ("расхождение гейтов: писатель ловит, приватность — нет", only_writer),
        ("расхождение гейтов: приватность ловит, писатель — нет", only_privacy),
        ("общий пропуск", both_miss),
    ]
    assert not (only_writer or only_privacy or both_miss), (
        f"расхождение гейтов на форме `{form.id}` ({len(cells)} ячеек):\n"
        + "\n".join(f"{title} ({len(rows)}):\n" + "\n".join(rows) for title, rows in sections if rows)
    )


def test_both_gates_leave_the_same_forms_out_of_the_grammar():
    """Формы вне грамматики — одни и те же у обоих гейтов, и каждая с причиной.

    На каждой форме `OUT_OF_GRAMMAR_BINDING_FORMS` × каждое значение опознания × прямой
    вызов и каждый носитель ни один гейт не разрешает связывание: находок ячейки не больше,
    чем у базы, где имя на месте вызова ничем не связано (`never_bound_fn`). Сырое число
    находок не сравнивается: значение может нести запись само (`methodcaller` со всеми
    аргументами записи), и гейт писателя находит её у значения в ячейке и в базе одинаково.
    """
    assert grammar.OUT_OF_GRAMMAR_BINDING_FORMS, "форм вне грамматики нет — правило проверяет ничто"
    unreasoned = [form.id for form in grammar.OUT_OF_GRAMMAR_BINDING_FORMS if not form.reason.strip()]
    assert not unreasoned, f"форма вне грамматики без причины: {unreasoned}"

    def writer_offences(source: str) -> list[str]:
        return writer.phone_write_offences(source, "scripts/x.py")

    def privacy_offences(source: str) -> list[str]:
        return privacy.python_log_offences(source, "app/x.py")

    disagreements: list[str] = []
    resolved: list[str] = []
    cells = 0
    for form in grammar.OUT_OF_GRAMMAR_BINDING_FORMS:
        for writer_value, privacy_value in zip(
            writer.API_IDENTIFICATION_VALUES, privacy.LOG_IDENTIFICATION_VALUES, strict=True
        ):
            for carrier in (None, *grammar.REFERENCE_CARRIERS):
                cells += 1
                writer_resolves = _resolves_binding(writer_offences, form, writer_value, carrier)
                privacy_resolves = _resolves_binding(privacy_offences, form, privacy_value, carrier)
                cell = f"  {form.id} / {writer_value.id} / {carrier.name if carrier is not None else 'прямой вызов'}"
                if writer_resolves != privacy_resolves:
                    disagreements.append(
                        f"{cell}: писатель {'разрешил' if writer_resolves else 'не разрешил'}, "
                        f"приватность {'разрешила' if privacy_resolves else 'не разрешила'}"
                    )
                elif writer_resolves:
                    resolved.append(cell)

    assert not disagreements, (
        f"расхождение гейтов на формах вне грамматики ({cells} ячеек):\n" + "\n".join(disagreements)
    )
    assert not resolved, (
        "оба гейта разрешают связывание формы, записанной вне грамматики: таблица "
        "`OUT_OF_GRAMMAR_BINDING_FORMS` и границы гейтов лгут:\n" + "\n".join(resolved)
    )
