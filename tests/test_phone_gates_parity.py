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
* Построение: оба модуля гейтов ввозят `tests.phone_gate_grammar` и не определяют на
  верхнем уровне своей грамматики (`binding_pairs`, `_binding_pairs`, `module_bindings`,
  `getattr_as_attribute`) и своих таблиц (`REFERENCE_KEYWORDS`, `ELEMENTWISE_CARRIERS`,
  `REFERENCE_CARRIERS`, `BINDING_FORMS`); ввезённые объекты — те же объекты общего
  модуля; `id` значений опознания (`API_IDENTIFICATION_VALUES`,
  `LOG_IDENTIFICATION_VALUES`) совпадают по порядку.
* Поведение: на каждой ячейке «форма `BINDING_FORMS` × значение опознания × прямой вызов
  и каждый носитель `REFERENCE_CARRIERS`» оба гейта находят — писатель запись номера,
  приватность номер в журнале. Ячейку обоих гейтов собирает одна функция
  `binding_form_source` общего модуля; своей сборки исходников здесь нет.
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
)

# Имена общего модуля, которые обязан держать (ввозом) каждый гейт — тем же объектом.
REQUIRED_SHARED_NAMES = frozenset(
    {"module_bindings", "REFERENCE_CARRIERS", "BINDING_FORMS"}
    | {"reference_arguments", "iterable_elements", "getattr_literal"}
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
    """Построение паритета: общий модуль ввезён, своих копий грамматики и носителей нет.

    Паритет держится по построению, пока грамматика и перечень носителей определены
    один раз — в `tests/phone_gate_grammar.py`. Вторая копия в модуле гейта (свой
    `_binding_pairs`, свой перечень носителей) — та асимметрия, на которой открывались
    круги WR-14 и WR-17 (решение владельца О-12 (а)).
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
