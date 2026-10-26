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

ЧТО ПРОВЕРЯЕТСЯ (каждое правило модуля названо ниже; перечни сверяет правило
`test_the_parity_docstring_names_what_it_checks`).
* Построение (`test_both_gates_take_the_binding_grammar_and_carriers_from_one_module`): оба
  модуля гейтов ввозят `tests.phone_gate_grammar` и держат его имена
  `REQUIRED_SHARED_NAMES` (`module_bindings`, `REFERENCE_CARRIERS`, `BINDING_FORMS`,
  `reference_arguments`, `iterable_elements`, `getattr_literal` и семантику обёртки
  носителя `carrier_wrapper_bindings`, `applied_wrapper`, `named_wrappers`,
  `is_carrier_wrapper` — ревью WR-24, план 16-37; применения обёртки, вызванной и поданной,
  рекурсивно, `wrapper_applications` — ревью WR-26, решение владельца О-16 (а), свойство 3;
  один читатель имени связанного
  `reading_name` — ревью WR-28, решение владельца О-18 (а), свойство 2: гейт писателя с
  плана 16-42, гейт приватности с плана 16-43) теми же объектами; на
  верхнем уровне модуля гейта нет функции с именем из `GRAMMAR_FUNCTIONS` — грамматика
  связывания (`binding_pairs`, `module_bindings`, `getattr_as_attribute`) И семантика
  носителя ссылки `CARRIER_SEMANTICS` (`getattr_literal`, `iterable_elements`, `expanded_arguments`,
  `forwarded_arguments`, `elementwise_arguments`, `literal_keyword_arguments`,
  `reference_arguments`, `carrier_wrapper_bindings`, `applied_wrapper`, `named_wrappers`,
  `is_carrier_wrapper`, `wrapper_applications`, `reading_name`), каждое имя с подчёркиванием и
  без, — и присваивания таблицы
  с именем из `GRAMMAR_TABLES` (`ELEMENTWISE_CARRIERS`, `REFERENCE_CARRIERS`,
  `BINDING_FORMS`, `LITERAL_CONTAINER_WRAPPERS`, `UNJUDGED_ELEMENT`, выведенная планом
  16-34 `REFERENCE_KEYWORDS`, построчные носители `ROW_CARRIERS` — ревью CR-02 / WR-25, план
  16-38; `UNJUDGED_ELEMENT` и `ROW_CARRIERS` — и с подчёркиванием): названные точки не
  переопределены. Копию под другим
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
* Сторож таблиц носителей (`test_the_elementwise_and_row_carriers_name_the_installed_apis`, ревью
  CR-02 / WR-25, план 16-38): `ELEMENTWISE_CARRIERS | ROW_CARRIERS` общего модуля — ровно
  публичные методы с `map` в имени у объектов установленного stdlib `MAP_CARRIER_OWNERS`
  (`multiprocessing.pool.Pool`, `concurrent.futures.Executor`, `itertools`), и таблицы не
  пересекаются: подъём Python с новым таким методом краснит суиту.
* Поведение (`test_both_gates_agree_on_every_binding_form_identification_and_carrier`): на каждой
  ячейке «форма `BINDING_FORMS` × значение опознания × прямой вызов и каждый носитель
  `REFERENCE_CARRIERS`» оба гейта находят — писатель запись номера с API значения из таблицы
  гейта писателя `API_IDENTIFICATION_CALLS` (своей таблицы API здесь нет, план 16-44), приватность
  номер в журнале. Ячейку обоих гейтов собирает одна функция
  `binding_form_source` общего модуля; своей сборки исходников здесь нет.
* Словарь седьмого круга (`test_the_shared_dictionary_holds_the_round_seven_axes`, план 16-39):
  девять строк `REFERENCE_CARRIERS` — поданная обёртка, обёртка в обёртке, именованная обёртка
  (вызов, передача, передача с аргументами, getattr-вариант), `starmap`, `apply_async` и место
  не-литеральной итерируемой у `map` (`ReferenceCarrier.last`), — так что по построению
  регрессия `147f5e46` краснит матрицу гейта писателя и это правило, регрессия `c6953017` —
  матрицу гейта приватности и это правило; матрица другого гейта на каждом из этих коммитов
  зелёная (ревью IN-18, решение владельца О-19: замер верификатора раунда 8 — 48 и 36 из 60
  ячеек строки на 12 формах × 5 значениях; замер плана 16-44 режимом `run.sh --rows` на
  таблицах HEAD — 52 и 39 из 78 на 13 формах × 6 значениях).
* Словарь восьмого круга (`test_the_shared_dictionary_holds_the_round_eight_axes`, ревью WR-28,
  решение владельца О-18 (а), свойство 3; план 16-44): форма `getattr-read` — чтение имени
  getattr-строкой, значение опознания `methodcaller-receiver` у обоих гейтов на одной позиции и
  полнота таблицы `API_IDENTIFICATION_CALLS` гейта писателя, — так что возврат чтения имени только
  у `Name` / `Attribute` (класс WR-28) краснит обе матрицы и правило-паритет.
* Словарь девятого круга (`test_the_shared_dictionary_holds_the_round_nine_axes`, ревью CR-04, WR-30, верификация
  раунда 9; решение владельца О-20 (а), свойство 6; план 16-49): пять форм коллизии видов (`collision-module` и
  соседи: одно последнее имя связано с соперником другого вида — поле `IdentificationValue.rival`, у приватности
  вызываемое журнала, у писателя пишущий API, — и со значением опознания) и три формы чтения через объект модуля
  (`module-object-getattr` и соседи), соперник у каждого значения обоих гейтов, значение `receiver` (связанное имя
  — получатель, применение — его метод, поле `IdentificationValue.method`) на одной позиции у обоих гейтов с API
  `__setattr__` в таблице `API_IDENTIFICATION_CALLS` и носители `carrier-name-bound-to-a-rival` /
  `executor-name-bound-to-a-rival` (последнее имя вызова носителя связано с соперником), — так что возврат закрытия
  толкований после опознанного вызова (класс CR-04) и потеря получателя, прочитанного через объект модуля (класс
  WR-30), краснят матрицы и правило-паритет. Класс коллизии имени носителя матрицы и правило-паритет держат для
  соперников словаря — `print` у приватности, `update` у писателя — и для написаний объекта модуля
  `sys.modules[__name__]` и `me = sys.modules[__name__]`; соперников других видов (`getattr`, `operator.methodcaller`,
  `methodcaller(…)` под именем носителя) и прочие написания объекта модуля словарь не собирает — эти конструкции
  запрещены каналом (О-23 (а), свойство 1; правило `test_every_dynamic_construct_case_is_banned_by_both_gates`).
  Летопись: до плана 16-53 абзац относил к матрицам весь класс коллизии имени носителя (ревью IN-22). Мера «база ↔ HEAD» партии раунда 9 сверила каждый GREEN с родителем и итог — с базой партии
  `d31d86db`, с `fb8fef72`, `1c243203` и `2f8c1656` по наличию находки и по их числу на корпусе из своих источников и
  чужих корпусов ревьюера и верификатора (29 941 ячейка, verify-r9 sha256 `5c6c4527…`); свойства гейтов шире этого
  корпуса этот абзац не утверждает (ревью IN-21).
* Место значения `partial` (`test_the_partial_value_place_is_pinned_by_a_privacy_row`, ревью
  IN-20, решение владельца О-19, план 16-43): у `partial` с одним позиционным аргументом (номером)
  места `last` нет по выбору словаря — его ячейка `map-named-iterable` равна ячейке `map`, — и
  форму `list(map(functools.partial(logger.info, "x %s"), account.phones))` держит строка
  `NEGATIVE_CONTROLS` `partial-log-reference-mapped-over-a-phone-attribute` гейта приватности с
  одной находкой; докстринг `ReferenceCarrier` называет эту строку, D-17 относит только к
  получателю `methodcaller`, а у `partial` называет выбор словаря.
* Формы вне грамматики (`test_both_gates_leave_the_same_forms_out_of_the_grammar`,
  `OUT_OF_GRAMMAR_BINDING_FORMS`): ни один гейт не разрешает их
  связывание, и у каждой формы есть причина. Сравнивается связывание, а не сырое число
  находок: гейт писателя находит запись и там, где значение несёт её само
  (`methodcaller` со всеми аргументами записи), поэтому ячейка сверяется с базой — той
  же ячейкой, где имя на месте вызова ничем не связано; находка сверх базы значила бы,
  что гейт связывание разрешил (план 16-27, заметки волне 2).
* Канал запрета динамических конструкций (план 16-53; решение владельца О-23 (а), свойство 1). Обещание гейтов
  сужено до «в коде нет конструкции, которую гейт не умеет судить»: конструкции динамического чтения или вызова —
  объект модуля, пространство имён, исполнение текста, отложенный вызов по имени, отражение атрибутов, служебный
  протокол, вычисленный SQL — запрещённые конструкции закрытого перечня девяти видов `DYNAMIC_CONSTRUCT_KINDS`, и
  гейт краснеет на самой конструкции, а не на опознанном написании. Канал один — функция общего модуля `dynamic_construct_findings` (она в
  `REQUIRED_SHARED_NAMES`: оба гейта держат её тем же объектом); оба гейта судят ею свои живые деревья — правила
  `test_no_dynamic_construct_in_the_python_trees` гейта приватности (`app/`, `scripts/`, `max_worker/`) и
  `test_no_dynamic_construct_in_the_writer_trees` гейта писателя (`app/`, `scripts/`); законные исключения — реестр
  `DYNAMIC_CONSTRUCT_EXCEPTIONS` общего модуля (шесть записей замера с причиной, потолок
  `DYNAMIC_CONSTRUCT_EXCEPTIONS_CEILING`, подъём — решение владельца); запись снимает только закреплённые за ней
  конструкции — текст (`DynamicConstruct.text`) и число по таблице `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS` общего модуля
  (по одной у каждой из шести записей на дереве `19c99ffb`), лишняя и недостающая краснят правило реестра. Летопись —
  ревью WR-38 (верификация раунда 11, advisory 3; решение владельца О-25 (а), свойство 6; план 16-59): до плана 16-59
  ключ `<путь>::<владелец>::<вид>` снимал ВСЕ конструкции своего вида у владельца, а правило реестра краснило только
  запись без конструкций, и вторая `getattr(self.session, op)(…)` в `BaseRepository.update` проходила канал и предикат
  молча. Правила этого модуля: трасер
  `test_a_planted_module_object_read_reddens_both_gates` — скрипт с чтением журнала через объект модуля, подложенный в
  синтетическое дерево, краснит правило живых деревьев обоих гейтов одной функцией общего модуля;
  `test_every_dynamic_construct_case_is_banned_by_both_gates` — каждая строка таблицы видов `DYNAMIC_CONSTRUCT_CASES`
  (формы CR-05, WR-32, WR-33, V10-1, V10-2 и прочие написания) краснит гейты своего поля `gates` ожидаемым видом;
  `test_a_judgeable_twin_is_not_banned` — судимый двойник `JUDGEABLE_TWINS` не краснит ни один гейт;
  `test_the_dynamic_construct_tables_cover_every_kind` — у каждого из девяти видов не одно написание;
  `test_the_dynamic_construct_exceptions_are_named_and_under_their_ceiling` и его контроль
  `test_a_seventh_dynamic_construct_exception_reddens_the_ceiling` — реестр правдив (файл дерева гейта, владелец,
  конструкция вида, причина) и под потолком; трасер `test_an_extra_construct_in_an_exempt_owner_is_red` (ревью WR-38,
  решение владельца О-25 (а), свойство 6; план 16-59) — вторая конструкция того же вида в теле исключённого владельца
  `BaseRepository.update`, новая `getattr(self.session, op)(…)` или повтор закреплённой, краснит правило живых деревьев
  обоих гейтов; `test_every_dynamic_construct_exception_pins_its_construct_texts` и его контроль
  `test_a_missing_or_extra_pinned_construct_reddens_the_registry_rule` — закрепление реестра правдиво в обе стороны;
  `test_the_parity_docstring_names_the_ban_channel_truthfully` — этот
  пункт, пункт о словаре девятого круга и комментарий-шапка канала общего модуля правдивы.
* Тексты, на которых держатся закрытия ревью (ревью IN-19 и IN-18, решение владельца О-19, план
  16-44): `test_the_parity_docstring_names_what_it_checks` — этот докстринг называет каждое имя
  `REQUIRED_SHARED_NAMES`, `CARRIER_SEMANTICS`, `GRAMMAR_TABLES` (без вариантов с подчёркиванием),
  каждый объект `MAP_CARRIER_OWNERS` и каждое правило модуля, перечни выведены из объектов модуля;
  `test_the_dictionary_chronicles_name_which_matrix_each_regression_reddens` — комментарии строк
  `named-wrapper-bound-handed` и `map-named-iterable` общего модуля, абзац этого докстринга о
  словаре седьмого круга и летописи словаря седьмого круга шапок обоих гейтов разводят, какая
  регрессия какую матрицу краснит; `test_the_dictionary_chronicles_name_what_the_measure_compared` (ревью IN-21,
  решение владельца О-20 (а), свойство 7, план 16-49) — летописи словаря восьмого и девятого круга шапок обоих гейтов
  называют, что мера «база ↔ HEAD» сверяла (корпус, его оси, размеры, sha256), и не записывают итог меры свойством
  гейтов шире корпуса.
"""

from __future__ import annotations

import ast
import inspect
import re
from collections import Counter
from pathlib import Path
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
    # Один канал запрета динамических конструкций у обоих гейтов (план 16-53; О-23 (а), свойство 1).
    | {"dynamic_construct_findings"}
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


def _writer_finds(source: str, call: str) -> bool:
    """Гейт писателя находит ровно одну запись `KIND_SETATTR`, называющую API `call` и `phone`.

    API значения берётся из таблицы гейта писателя `API_IDENTIFICATION_CALLS` (план 16-44):
    своей таблицы API это правило не держит.
    """
    offences = writer.phone_write_offences(source, "scripts/x.py")
    if len(offences) != 1:
        return False
    _location, kind, subject = offences[0].split(" — ", 2)
    return kind == writer.KIND_SETATTR and call in subject and "phone" in subject


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


# Формы словаря девятого круга (ревью CR-04, WR-30, верификация раунда 9, 2026-10-20; решение владельца О-20 (а),
# свойство 6; план 16-49): коллизия видов — одно последнее имя связано с соперником другого вида (`{rival}`) и со
# значением опознания (`{value}`) — и чтение имени через объект модуля.
ROUND_NINE_COLLISION_FORMS = (
    "collision-module",
    "collision-in-function",
    "collision-rebound",
    "collision-other-init",
    "collision-class-body",
)
ROUND_NINE_MODULE_OBJECT_FORMS = ("module-object-getattr", "module-object-attribute", "module-object-bound")
MODULE_OBJECT = "sys.modules[__name__]"


def _probe_tree(template: str) -> ast.Module:
    """Шаблон формы с заместителями мест: значение, соперник, подмена — имена, место `{use}` — вызов."""
    for place, probe in (("{value}", "VALUE_PROBE"), ("{rival}", "RIVAL_PROBE"), ("{decoy}", "DECOY_PROBE")):
        template = template.replace(place, probe)
    return ast.parse(template.replace("{use}", "USE_PROBE()"))


def _bound_names(tree: ast.Module, probe: str) -> set[str]:
    """Последние имена целей присваиваний, чьё значение — заместитель `probe` (`f`, `self.f` → `f`)."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name) and node.value.id == probe:
            names |= {name for target in node.targets if (name := grammar.reading_name(target)) is not None}
    return names


def _round_nine_form_problems() -> list[str]:
    """Чем словарь не держит формы девятого круга: строки, место соперника, общее имя, чтение через объект модуля."""
    problems: list[str] = []
    forms = {form.id: form for form in grammar.BINDING_FORMS}
    for form_id in (*ROUND_NINE_COLLISION_FORMS, *ROUND_NINE_MODULE_OBJECT_FORMS):
        if form_id not in forms:
            problems.append(f"в `BINDING_FORMS` нет формы `{form_id}`")
    for form_id in ROUND_NINE_COLLISION_FORMS:
        form = forms.get(form_id)
        if form is None:
            continue
        if "{rival}" not in form.template:
            problems.append(f"у формы `{form_id}` нет места соперника `{{rival}}`")
            continue
        tree = _probe_tree(form.template)
        rival_names, value_names = _bound_names(tree, "RIVAL_PROBE"), _bound_names(tree, "VALUE_PROBE")
        read = grammar.reading_name(ast.parse(form.ref, mode="eval").body)
        if not rival_names & value_names or read not in rival_names & value_names:
            problems.append(f"форма `{form_id}` связывает соперника ({sorted(rival_names)}) и значение "
                            f"({sorted(value_names)}) не под тем последним именем, что читает ссылка `{form.ref}`")
        probe = grammar.IdentificationValue("probe", "probe_fn", "(first)")
        try:
            grammar.binding_form_source(form, probe, None)
        except AssertionError:
            pass
        else:
            problems.append(f"`binding_form_source` собрал форму `{form_id}` у значения без соперника — вакуум")
    for form_id in ROUND_NINE_MODULE_OBJECT_FORMS:
        form = forms.get(form_id)
        if form is None:
            continue
        tree = _probe_tree(form.template)
        owners = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign) and ast.unparse(node.value) == MODULE_OBJECT
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        ref = ast.parse(form.ref, mode="eval").body
        owner = ref.args[0] if isinstance(ref, ast.Call) and ref.args else getattr(ref, "value", None)
        via_module = owner is not None and (ast.unparse(owner) == MODULE_OBJECT or ast.unparse(owner) in owners)
        if not via_module or grammar.reading_name(ref) not in _bound_names(tree, "VALUE_PROBE"):
            problems.append(f"ссылка формы `{form_id}` — `{form.ref}` — не читает имя значения через `{MODULE_OBJECT}`")
    return problems


def _round_nine_rival_problems() -> list[str]:
    """Чем значения опознания обоих гейтов не держат соперника: пусто или соперник не другого вида."""
    problems: list[str] = []
    writer_names = set(writer.WRITE_CALL_NAMES) | {parameter.call for parameter in writer.JUDGED_PARAMETERS}
    for side, values in (("писателя", writer.API_IDENTIFICATION_VALUES), ("приватности", privacy.LOG_IDENTIFICATION_VALUES)):
        for value in values:
            rival = getattr(value, "rival", "")
            if not rival:
                problems.append(f"у значения `{value.id}` гейта {side} нет соперника (`IdentificationValue.rival`)")
                continue
            node = ast.parse(rival, mode="eval").body
            if side == "приватности" and not privacy._is_log_callable(node):
                problems.append(f"соперник `{rival}` значения `{value.id}` гейта приватности — не вызываемое журнала")
            if side == "писателя" and grammar.reading_name(node) not in writer_names:
                problems.append(f"соперник `{rival}` значения `{value.id}` гейта писателя — не пишущий API")
    return problems


# Значение и носители словаря девятого круга (ревью WR-30, CR-04 / KC; решение владельца О-20 (а), свойство 6;
# план 16-49): значение, у которого связанное имя — получатель, а применение — его метод, и носители, чьё последнее
# имя вызова связано в модуле с соперником.
ROUND_NINE_VALUE = "receiver"
ROUND_NINE_METHODS = {"writer": "__setattr__", "privacy": "info"}
ROUND_NINE_CARRIERS = {"carrier-name-bound-to-a-rival": "to_thread", "executor-name-bound-to-a-rival": "run_in_executor"}


def _round_nine_value_problems() -> list[str]:
    """Чем словарь не держит значение `receiver`, поле `method` и носители с соперником под своим именем."""
    problems: list[str] = []
    writer_ids = [value.id for value in writer.API_IDENTIFICATION_VALUES]
    privacy_ids = [value.id for value in privacy.LOG_IDENTIFICATION_VALUES]
    for side, ids in (("писателя", writer_ids), ("приватности", privacy_ids)):
        if not ids or ids[-1] != ROUND_NINE_VALUE:
            problems.append(f"у гейта {side} значение `{ROUND_NINE_VALUE}` — не последнее значение опознания: {ids}")
    direct = next(form for form in grammar.BINDING_FORMS if form.id == "direct")
    for side, gate, values in (
        ("writer", "писателя", writer.API_IDENTIFICATION_VALUES),
        ("privacy", "приватности", privacy.LOG_IDENTIFICATION_VALUES),
    ):
        value = next((value for value in values if value.id == ROUND_NINE_VALUE), None)
        if value is None:
            continue
        method = getattr(value, "method", "")
        if method != ROUND_NINE_METHODS[side]:
            problems.append(f"метод значения `{ROUND_NINE_VALUE}` гейта {gate} — `{method}`, ожидался "
                            f"`{ROUND_NINE_METHODS[side]}` (`IdentificationValue.method`)")
        applied = ast.parse(f"f{value.call}", mode="eval").body
        arguments = [ast.unparse(argument) for argument in applied.args]
        if side == "privacy":
            if not privacy._is_factory_call(ast.parse(value.value, mode="eval").body):
                problems.append(f"значение `{ROUND_NINE_VALUE}` гейта приватности — не вызов фабрики журнала: `{value.value}`")
            if not any("phone" in argument for argument in arguments):
                problems.append(f"номер значения `{ROUND_NINE_VALUE}` гейта приватности не в аргументах применения: {value.call}")
        elif "'phone'" not in arguments and '"phone"' not in arguments:
            problems.append(f"колонка `\"phone\"` значения `{ROUND_NINE_VALUE}` гейта писателя не в аргументах применения: "
                            f"{value.call}")
        source = grammar.binding_form_source(direct, value, None)
        if f".{ROUND_NINE_METHODS[side]}(" not in source:
            problems.append(f"ячейка прямого вызова значения `{ROUND_NINE_VALUE}` гейта {gate} не зовёт метод: {source!r}")
    calls = getattr(writer, "API_IDENTIFICATION_CALLS", {})
    if calls.get(ROUND_NINE_VALUE) != ROUND_NINE_METHODS["writer"]:
        problems.append(f"`API_IDENTIFICATION_CALLS` у `{ROUND_NINE_VALUE}` — {calls.get(ROUND_NINE_VALUE)!r}, ожидалось "
                        f"`{ROUND_NINE_METHODS['writer']}`")
    carriers = {carrier.id: carrier for carrier in grammar.REFERENCE_CARRIERS}
    for carrier_id, name in ROUND_NINE_CARRIERS.items():
        carrier = carriers.get(carrier_id)
        if carrier is None:
            problems.append(f"в `REFERENCE_CARRIERS` нет строки `{carrier_id}`")
            continue
        template = carrier.template.replace("{rival}", "RIVAL_PROBE")
        tree = ast.parse(template.format(ref="REF", args="A", positional="A", keywords="{}"))
        bound = _bound_names(tree, "RIVAL_PROBE")
        called = {
            grammar.reading_name(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)
        }
        if name not in bound or name not in called:
            problems.append(f"шаблон `{carrier_id}` не связывает последнее имя вызова носителя `{name}` с `{{rival}}`: "
                            f"`{carrier.template}`")
    return problems


def test_the_shared_dictionary_holds_the_round_nine_axes():
    """Словарь матриц и паритета держит оси девятого круга: коллизию видов и чтение через объект модуля.

    Словарь подменял имя только значением того же вида (`decoy`), поэтому ни обе матрицы, ни это правило, ни корпус
    меры «база ↔ HEAD» партии раунда 8 не собирали ячейку, где одно последнее имя связано с вызываемым журнала и с
    `methodcaller`: регрессия `a77263ad` (CR-04) прошла суиту и меру зелёными, а получатель журнала, прочитанный
    через объект модуля (WR-30), был вне словаря (ревью CR-04, WR-30, верификация раунда 9, 2026-10-20). Правило
    держит (а) пять форм коллизии видов (`collision-module`, `collision-in-function`, `collision-rebound`,
    `collision-other-init`, `collision-class-body`): у каждой — место соперника `{rival}`, связанное под тем же
    последним именем, что `{value}`, и то же имя читает ссылка формы; у значения без соперника
    `binding_form_source` поднимает `AssertionError` (вакуум, как у `{decoy}`); (б) три формы чтения через объект
    модуля (`module-object-getattr`, `module-object-attribute`, `module-object-bound`) — ссылка читает имя значения
    через `sys.modules[__name__]` или имя, связанное с ним; (в) соперника у КАЖДОГО значения обоих гейтов
    (`IdentificationValue.rival`): у приватности — вызываемое журнала, у писателя — пишущий API
    (`WRITE_CALL_NAMES` или `JUDGED_PARAMETERS`); (г) значение `receiver` у обоих гейтов на последней позиции —
    связанное имя получатель, применение — его метод (`IdentificationValue.method`): у приватности вызов фабрики
    журнала с методом `info` и номером в аргументах применения, у писателя `__setattr__` с колонкой `"phone"` в
    аргументах; ячейка прямого вызова зовёт метод; `API_IDENTIFICATION_CALLS["receiver"]` — `__setattr__`; (д) строки
    `REFERENCE_CARRIERS` `carrier-name-bound-to-a-rival` и `executor-name-bound-to-a-rival`: шаблон связывает
    последнее имя вызова носителя (`to_thread`, `run_in_executor`) с `{rival}`. Решение владельца О-20 (а), свойство
    6; план 16-49.
    """
    problems = _round_nine_form_problems() + _round_nine_rival_problems() + _round_nine_value_problems()

    assert not problems, "словарь матриц и паритета не держит ось девятого круга:\n" + "\n".join(
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
    `getattr`-строка, `partial`, `methodcaller`, `methodcaller-receiver`) × прямой вызов и
    каждый носитель `REFERENCE_CARRIERS`. Гейт писателя судит ячейку со значением
    `API_IDENTIFICATION_VALUES` и ждёт в находке API этого значения из
    `API_IDENTIFICATION_CALLS` гейта писателя, гейт приватности — с `LOG_IDENTIFICATION_VALUES`
    того же `id`; обе собирает `binding_form_source`. Промахи делятся на расхождение гейтов
    (одна сторона ловит, другая — нет) и общий пропуск.
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
        writer_found = _writer_finds(
            grammar.binding_form_source(form, writer_value, carrier), writer.API_IDENTIFICATION_CALLS[writer_value.id]
        )
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


def _module_tree() -> ast.Module:
    return ast.parse(Path(__file__).read_text(encoding="utf-8"))


def test_the_parity_docstring_names_what_it_checks():
    """Докстринг правила-паритета называет ровно то, что модуль проверяет (ревью IN-19, решение владельца О-19).

    Закрытие IN-15 держалось на том, что раздел «ЧТО ПРОВЕРЯЕТСЯ» называет каждую проверяемую точку;
    партия раунда 7 добавила `wrapper_applications`, `ROW_CARRIERS` и сторожа stdlib, а перечень не
    дописала (верификация раунда 8). Перечни здесь выводятся из объектов самого модуля, а не из
    констант правила: докстринг (пробелы схлопнуты) называет в обратных кавычках каждое имя
    `REQUIRED_SHARED_NAMES`, каждое имя `CARRIER_SEMANTICS`, каждое имя `GRAMMAR_TABLES` без ведущего
    подчёркивания, каждый объект `MAP_CARRIER_OWNERS` и каждое правило модуля — функцию `test_*`
    верхнего уровня его исходника, и это правило тоже (план 16-44).
    """
    tree = _module_tree()
    doc = " ".join((ast.get_docstring(tree) or "").split())
    rules = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]
    assert len(rules) >= 10, f"правил модуля {len(rules)} — меньше 10: сверка проверяет почти ничто"
    checked = {
        "REQUIRED_SHARED_NAMES": sorted(REQUIRED_SHARED_NAMES),
        "CARRIER_SEMANTICS": list(CARRIER_SEMANTICS),
        "GRAMMAR_TABLES": sorted(name for name in GRAMMAR_TABLES if not name.startswith("_")),
        "MAP_CARRIER_OWNERS": list(MAP_CARRIER_OWNERS),
        "правила модуля": rules,
    }
    unnamed = [f"  {source}: `{name}`" for source, names in checked.items() for name in names if f"`{name}`" not in doc]

    assert not unnamed, (
        "докстринг правила-паритета называет меньше, чем модуль проверяет (ревью IN-19):\n" + "\n".join(unnamed)
    )


# Регрессии партии раунда 6 и матрица, которую каждая краснит (ревью IN-18, решение владельца О-19):
# строка словаря седьмого круга, которая её держит, и матрица — по замеру верификатора раунда 8 и
# режима `--rows` инструмента сверки плана 16-44.
REGRESSION_MATRICES = (
    ("147f5e46", "матрицу гейта писателя", "named-wrapper-bound-handed"),
    ("c6953017", "матрицу гейта приватности", "map-named-iterable"),
)


def _row_comment(lines: list[str], row: str) -> str:
    """Комментарий `#` прямо над строкой `REFERENCE_CARRIERS` с `id` `row` (пробелы схлопнуты)."""
    index = next((i for i, line in enumerate(lines) if f'"{row}"' in line and "ReferenceCarrier" in "".join(
        lines[max(0, i - 1) : i + 1])), None)
    if index is None:
        return ""
    if "ReferenceCarrier(" not in lines[index]:
        index -= 1
    comment: list[str] = []
    for line in reversed(lines[:index]):
        if not line.strip().startswith("#"):
            break
        comment.append(line.strip().lstrip("#").strip())
    return " ".join(" ".join(reversed(comment)).split())


def _chronicle(flat: str, heading: str) -> str:
    """Абзац летописи шапки гейта: от заголовка до следующей летописи или раздела шапки."""
    start = flat.find(heading)
    if start < 0:
        return ""
    ends = [
        index
        for marker in ("Летопись", "РЕЕСТР ИСКЛЮЧЕНИЙ", "ЧТО КРАСНИТ")
        if (index := flat.find(marker, start + len(heading))) >= 0
    ]
    return flat[start : min(ends, default=len(flat))]


def _pairs_regression_with_matrix(text: str, commit: str, matrix: str) -> bool:
    """В тексте коммит регрессии стоит рядом со своей матрицей: матрица — не дальше 160 знаков после
    коммита, и между ними нет коммита другой регрессии."""
    others = [other for other, _matrix, _row in REGRESSION_MATRICES if other != commit]
    for match in re.finditer(re.escape(commit), text):
        window = text[match.end() : match.end() + 160]
        position = window.find(matrix)
        if position >= 0 and not any(other in window[:position] for other in others):
            return True
    return False


def test_the_dictionary_chronicles_name_which_matrix_each_regression_reddens():
    """Летописи словаря седьмого круга разводят, какая регрессия какую матрицу краснит (ревью IN-18, О-19).

    Замер верификатора раунда 8 на 60 ячейках строки (12 форм × 5 значений): на предикатах
    `147f5e46` строка `named-wrapper-bound-handed` красна у гейта писателя (48) и зелёная у гейта
    приватности (0) — своего поглощения у гейта приватности не было; на `c6953017` строка
    `map-named-iterable` красна у гейта приватности (36). Комментарий строки и летописи говорили
    «краснят обе матрицы» — верно только в совокупности. Правило держит: комментарий над
    `named-wrapper-bound-handed` в исходнике общего модуля называет «матрицу гейта писателя» и
    `147f5e46`, не говорит «обе матрицы», а гейт приватности называет только зелёным; комментарий
    над `map-named-iterable` называет «матрицу гейта приватности» и `c6953017`; абзац этого
    докстринга о словаре седьмого круга и абзацы «Летопись словаря седьмого круга» шапок обоих
    гейтов называют `147f5e46` рядом с «матрицу гейта писателя», `c6953017` — рядом с «матрицу
    гейта приватности» и не говорят «краснят обе матрицы» (план 16-44).
    """
    problems: list[str] = []
    lines = inspect.getsource(grammar).splitlines()
    for commit, matrix, row in REGRESSION_MATRICES:
        comment = _row_comment(lines, row)
        if not comment:
            problems.append(f"над строкой `{row}` общего модуля нет комментария")
            continue
        for needle in (matrix, commit):
            if needle not in comment:
                problems.append(f"комментарий строки `{row}` не называет «{needle}»")
        if "обе матрицы" in comment:
            problems.append(f"комментарий строки `{row}` говорит «обе матрицы»")
    bound_comment = _row_comment(lines, REGRESSION_MATRICES[0][2])
    for sentence in _sentences(bound_comment):
        if "гейта приватности" in sentence and "зелён" not in sentence:
            problems.append(f"комментарий строки `{REGRESSION_MATRICES[0][2]}` относит её к матрице гейта "
                            f"приватности: «{sentence}»")
    doc = " ".join((ast.get_docstring(_module_tree()) or "").split())
    start = doc.find("Словарь седьмого круга")
    parity_paragraph = doc[start : doc.find("* ", start)] if start >= 0 else ""
    texts = {
        "абзац докстринга паритета о словаре седьмого круга": parity_paragraph,
        "летопись словаря седьмого круга шапки гейта писателя": _chronicle(
            " ".join((writer.__doc__ or "").split()), "Летопись словаря седьмого круга"),
        "летопись словаря седьмого круга шапки гейта приватности": _chronicle(
            " ".join((privacy.__doc__ or "").split()), "Летопись словаря седьмого круга"),
    }
    for title, text in texts.items():
        if not text:
            problems.append(f"нет текста: {title}")
            continue
        for commit, matrix, _row in REGRESSION_MATRICES:
            if not _pairs_regression_with_matrix(text, commit, matrix):
                problems.append(f"{title}: `{commit}` не стоит рядом с «{matrix}»")
        if "краснят обе матрицы" in text:
            problems.append(f"{title}: говорит «краснят обе матрицы»")

    assert not problems, (
        "летописи словаря не разводят, какая регрессия какую матрицу краснит (ревью IN-18):\n"
        + "\n".join(f"  {problem}" for problem in problems)
    )


# Фраза-итог летописей словаря восьмого круга обеих шапок на `1163ae39` (ревью IN-21, верификация раунда 9): итог меры
# записан свойством гейтов, и замер раунда 9 его опроверг — у приватности `a77263ad` против родителя и базы (CR-04),
# у писателя две подачи через получатель против `2f8c1656` (WR-31, не класс WR-24).
REFUTED_MEASURE_CLAIM = "число находок у обоих гейтов не меньше, чем у родителя и у базы"
# Что летопись словаря восьмого круга называет вместо итога: корпус меры партии раунда 8.
EIGHTH_MEASURE_NEEDLES = ("64 483", "fd55d467", "корпус")
# Что называет летопись словаря девятого круга: план, строки словаря, корпус меры партии раунда 9 и решения владельца.
NINTH_MEASURE_NEEDLES = ("16-49", "collision", "module-object", "receiver", "29 941", "5c6c4527", "О-20 (а)", "О-21 (а)")


def test_the_dictionary_chronicles_name_what_the_measure_compared():
    """Летописи словаря называют, что мера сверяла, а не свойство гейтов шире корпуса (ревью IN-21; О-20 (а), свойство 7).

    Летописи словаря восьмого круга обеих шапок записывали итог меры «база ↔ HEAD» партии раунда 8 свойством гейтов —
    «число находок у обоих гейтов не меньше, чем у родителя и у базы», — а мера сверяла корпус из словаря и
    самопроверок исполнителей, где не было ни коллизии имени, ни метода чужого объекта, ни двух подач через получатель;
    замер раунда 9 нашёл на этих осях регрессию `a77263ad` (CR-04) и давнее слияние двух подач (WR-31). Правило
    держит: в шапке КАЖДОГО гейта абзац «Летопись словаря восьмого круга» (через `_chronicle_segment` модуля гейта)
    называет корпус меры — «64 483», «fd55d467», «корпус» — и не содержит опровергнутой фразы-итога (её текст —
    константа `REFUTED_MEASURE_CLAIM`, строки шапок на `1163ae39`); абзац «Летопись словаря девятого круга» называет
    план 16-49, строки словаря девятого круга (`collision`, `module-object`, `receiver`), корпус меры партии раунда 9
    (29 941 чужая ячейка, sha256 корпуса верификатора `5c6c4527…`), решения владельца О-20 (а), О-21 (а) и той же
    фразы-итога не содержит. Решение владельца О-20 (а), свойство 7; план 16-49.
    """
    problems: list[str] = []
    for title, module in (("писателя", writer), ("приватности", privacy)):
        flat = " ".join((module.__doc__ or "").split())
        eighth = module._chronicle_segment(flat, "Летопись словаря восьмого круга")
        ninth = module._chronicle_segment(flat, "Летопись словаря девятого круга")
        if not eighth:
            problems.append(f"в шапке гейта {title} нет «Летопись словаря восьмого круга»")
        if not ninth:
            problems.append(f"в шапке гейта {title} нет «Летопись словаря девятого круга»")
        for heading, text, needles in (
            ("восьмого", eighth, EIGHTH_MEASURE_NEEDLES),
            ("девятого", ninth, NINTH_MEASURE_NEEDLES),
        ):
            if not text:
                continue
            for needle in needles:
                if needle not in text:
                    problems.append(f"летопись словаря {heading} круга шапки гейта {title} не называет «{needle}»")
            if REFUTED_MEASURE_CLAIM in text:
                problems.append(f"летопись словаря {heading} круга шапки гейта {title} утверждает итог меры свойством "
                                f"гейтов: «{REFUTED_MEASURE_CLAIM}»")

    assert not problems, (
        "летописи словаря не называют, что мера сверяла (ревью IN-21):\n" + "\n".join(f"  {problem}" for problem in problems)
    )


# --- Канал запрета динамических конструкций (план 16-53; решение владельца О-23 (а), свойство 1) -----------------

# Сквозной срез: скрипт дозаполнения Фазы 20, читающий журнал через объект модуля (класс CR-05). Восемь строк;
# вызов — восьмая.
PLANTED_DYNAMIC_SCRIPT = "scripts/phone_backfill_dynamic.py"
PLANTED_DYNAMIC_SOURCE = (
    "import logging\n"
    "import sys\n"
    "\n"
    "lg = logging.getLogger(__name__)\n"
    "\n"
    "\n"
    "def backfill(account):\n"
    '    getattr(sys.modules[__name__], "lg").info("x %s", account.phone)\n'
)
PLANTED_DYNAMIC_LINE = 8


def test_a_planted_module_object_read_reddens_both_gates(tmp_path):
    """ТРАСЕР канала запрета: подложенное чтение журнала через объект модуля краснит оба гейта одной функцией.

    В синтетическом дереве — `scripts/phone_backfill_dynamic.py` с `getattr(sys.modules[__name__], "lg").info(…)`;
    `dynamic_construct_scan` каждого гейта (`privacy` — над `app/`, `scripts/`, `max_worker/`, `writer` — над
    `app/`, `scripts/`) даёт ровно одну находку на строке вызова вида «объект модуля» (узел атрибута `modules`).
    Функция канала у обоих гейтов — один объект общего модуля `dynamic_construct_findings`.
    """
    assert len(PLANTED_DYNAMIC_SOURCE.splitlines()) == PLANTED_DYNAMIC_LINE, "подложенный скрипт не восьмистрочный"
    planted = tmp_path / PLANTED_DYNAMIC_SCRIPT
    planted.parent.mkdir(parents=True)
    planted.write_text(PLANTED_DYNAMIC_SOURCE, encoding="utf-8")

    assert privacy.dynamic_construct_findings is writer.dynamic_construct_findings is grammar.dynamic_construct_findings, (
        "функция канала запрета у гейтов — не один объект общего модуля"
    )
    found: dict[str, list[str]] = {}
    for title, module in (("приватности", privacy), ("писателя", writer)):
        paths, offences = module.dynamic_construct_scan(tmp_path)
        assert planted in paths, f"обход гейта {title} не видит подложенный скрипт: {paths}"
        found[title] = offences
    location = f"{PLANTED_DYNAMIC_SCRIPT}:{PLANTED_DYNAMIC_LINE} — "
    reddened = [
        title
        for title, offences in found.items()
        if len(offences) == 1 and offences[0].startswith(location) and grammar.DYNAMIC_KIND_MODULE_OBJECT in offences[0]
    ]

    assert reddened == ["приватности", "писателя"], (
        "подложенное чтение журнала через объект модуля не краснит правило живых деревьев обоих гейтов: "
        f"{found}"
    )


# Гейты канала по имени поля `DynamicConstructCase.gates`.
DYNAMIC_CONSTRUCT_GATES: dict[str, ModuleType] = {"privacy": privacy, "writer": writer}

# Нижние пределы таблиц канала: написаний на вид и двойников (истина 4 плана 16-53).
DYNAMIC_CASES_PER_KIND = 3
JUDGEABLE_TWINS_FLOOR = 20


def _scan_planted(module: ModuleType, root: Path, source: str) -> list[str]:
    """Находки канала гейта `module` над синтетическим деревом `root` с единственным файлом `app/x.py`."""
    planted = root / "app" / "x.py"
    planted.parent.mkdir(parents=True, exist_ok=True)
    planted.write_text(source, encoding="utf-8")
    paths, offences = module.dynamic_construct_scan(root)
    assert planted in paths, f"обход канала не видит подложенный `app/x.py`: {paths}"
    return offences


@pytest.mark.parametrize("case", [pytest.param(case, id=case.id) for case in grammar.DYNAMIC_CONSTRUCT_CASES])
def test_every_dynamic_construct_case_is_banned_by_both_gates(tmp_path, case):
    """Каждая строка `DYNAMIC_CONSTRUCT_CASES` краснит каждый гейт поля `gates` находкой ожидаемого вида."""
    assert case.kind in grammar.DYNAMIC_CONSTRUCT_KINDS, f"вид строки `{case.id}` вне перечня: {case.kind}"
    assert case.gates and set(case.gates) <= set(DYNAMIC_CONSTRUCT_GATES), f"гейты строки `{case.id}`: {case.gates}"
    missed = {}
    for gate in case.gates:
        offences = _scan_planted(DYNAMIC_CONSTRUCT_GATES[gate], tmp_path, case.source)
        if not any(f" — {case.kind} — " in offence for offence in offences):
            missed[gate] = offences

    assert not missed, (
        f"строка таблицы видов не краснит гейт ожидаемым видом «{case.kind}» (`{case.id}`): {missed}"
    )


@pytest.mark.parametrize("twin", [pytest.param(twin, id=twin.id) for twin in grammar.JUDGEABLE_TWINS])
def test_a_judgeable_twin_is_not_banned(tmp_path, twin):
    """Судимый двойник `JUDGEABLE_TWINS` не даёт ни одной находки канала ни у одного гейта."""
    found = {gate: _scan_planted(module, tmp_path, twin.source) for gate, module in DYNAMIC_CONSTRUCT_GATES.items()}

    assert not any(found.values()), f"канал краснеет на судимом двойнике `{twin.id}`: {found}"


def test_the_dynamic_construct_tables_cover_every_kind():
    """Таблицы канала: девять видов, у каждого не меньше трёх написаний, двойников не меньше двадцати, `id` уникальны."""
    per_kind = Counter(case.kind for case in grammar.DYNAMIC_CONSTRUCT_CASES)
    ids = Counter(row.id for row in (*grammar.DYNAMIC_CONSTRUCT_CASES, *grammar.JUDGEABLE_TWINS))
    problems = [
        f"вид «{kind}»: написаний {per_kind[kind]}"
        for kind in grammar.DYNAMIC_CONSTRUCT_KINDS
        if per_kind[kind] < DYNAMIC_CASES_PER_KIND
    ]
    problems += [f"вид строки вне перечня: «{kind}»" for kind in per_kind if kind not in grammar.DYNAMIC_CONSTRUCT_KINDS]
    problems += [f"`id` повторён: {row_id}" for row_id, count in ids.items() if count > 1]
    if len(grammar.DYNAMIC_CONSTRUCT_KINDS) != 9:
        problems.append(f"видов {len(grammar.DYNAMIC_CONSTRUCT_KINDS)}, а не девять")
    if len(grammar.JUDGEABLE_TWINS) < JUDGEABLE_TWINS_FLOOR:
        problems.append(f"двойников {len(grammar.JUDGEABLE_TWINS)} — меньше {JUDGEABLE_TWINS_FLOOR}")

    assert not problems, "таблицы канала запрета держат вид одним написанием или меньше:\n" + "\n".join(
        f"  {problem}" for problem in problems
    )


def _qualified_owners(tree: ast.Module) -> set[str]:
    """Квалифицированные имена всех `def` / `class` модуля через точку и `<module>`."""
    owners = {"<module>"}
    pending: list[tuple[ast.AST, str]] = [(tree, "")]
    while pending:
        node, prefix = pending.pop()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{child.name}"
                owners.add(name)
                pending.append((child, f"{name}."))
            else:
                pending.append((child, prefix))
    return owners


def _dynamic_exception_problems(
    registry: dict[str, str], ceiling: int, pinned: dict[str, tuple[str, ...]] | None = None
) -> list[str]:
    """Чем реестр исключений канала неправдив: число выше потолка, нет файла дерева гейта, владельца, конструкции,
    причины, закрепления — или закреплённые тексты расходятся с конструкциями владельца.

    `pinned` — таблица закреплённых текстов; при `None` помощник читает `grammar.DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS` в
    момент вызова (не значением по умолчанию при определении), так что подмена таблицы в контроле видна. У каждой записи
    множество текстов (`DynamicConstruct.text`) конструкций её вида у владельца сверяется с закреплённым с числом:
    лишняя конструкция и недостающая закреплённая — проблемы (ревью WR-38, план 16-59). Один помощник у правил реестра
    и закрепления и у их контролей: контроли доказывают, что правила краснеют на записи сверх потолка, на устаревшей
    записи, на лишней и на недостающей конструкции.
    """
    if pinned is None:
        pinned = grammar.DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS
    problems: list[str] = []
    if len(registry) > ceiling:
        problems.append(f"записей {len(registry)} — выше потолка {ceiling}: подъём потолка — решение владельца")
    trees = set(privacy.PYTHON_TREES) | set(writer.WRITER_TREES)
    judged = privacy.BANNED_GETATTR_NAMES | writer.BANNED_GETATTR_NAMES
    for key, reason in registry.items():
        parts = key.split("::")
        if len(parts) != 3:
            problems.append(f"`{key}`: ключ не вида `<путь>::<владелец>::<вид>`")
            continue
        path, owner, kind = parts
        if not reason.strip():
            problems.append(f"`{key}`: причина пуста")
        if kind not in grammar.DYNAMIC_CONSTRUCT_KINDS:
            problems.append(f"`{key}`: вид «{kind}» вне перечня")
        file = privacy.PROJECT_ROOT / path
        if path.split("/", 1)[0] not in trees or not file.is_file():
            problems.append(f"`{key}`: файла нет в деревьях гейтов")
            continue
        source = file.read_text(encoding="utf-8")
        if owner not in _qualified_owners(ast.parse(source)):
            problems.append(f"`{key}`: владельца `{owner}` в файле нет")
            continue
        texts = Counter(
            found.text
            for found in grammar.dynamic_construct_findings(source, path, judged_names=judged)
            if grammar.dynamic_construct_key(found) == key
        )
        if not texts:
            problems.append(f"`{key}`: запись устарела — конструкции вида «{kind}» у владельца нет")
        if key not in pinned:
            problems.append(f"`{key}`: закрепления нет — `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS` не называет запись")
            continue
        expected = Counter(pinned[key])
        problems += [
            f"`{key}`: лишняя конструкция у исключённого владельца — `{text}`" + (f" (×{count})" if count > 1 else "")
            for text, count in (texts - expected).items()
        ]
        problems += [
            f"`{key}`: запись устарела — нет закреплённой конструкции `{text}`" + (f" (×{count})" if count > 1 else "")
            for text, count in (expected - texts).items()
        ]
    return problems


def test_the_dynamic_construct_exceptions_are_named_and_under_their_ceiling():
    """Реестр `DYNAMIC_CONSTRUCT_EXCEPTIONS` правдив и не растёт молча (истина 5 плана 16-53; D-13, D-17).

    Каждая запись называет существующий файл дерева гейта, существующего владельца и хотя бы одну конструкцию
    названного вида у него, причина непуста, записей не больше потолка `DYNAMIC_CONSTRUCT_EXCEPTIONS_CEILING`. С плана
    16-59 (ревью WR-38) запись снимает только закреплённые конструкции — текст и число по
    `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS`; тексты конструкций владельца с числом равны закреплённым, лишняя и недостающая
    краснят это правило и правило `test_every_dynamic_construct_exception_pins_its_construct_texts`.
    """
    registry = grammar.DYNAMIC_CONSTRUCT_EXCEPTIONS
    problems = _dynamic_exception_problems(registry, grammar.DYNAMIC_CONSTRUCT_EXCEPTIONS_CEILING)

    assert registry, "реестр исключений канала пуст: замер планирования назвал шесть живых исключений"
    assert not problems, "реестр исключений канала запрета неправдив:\n" + "\n".join(f"  {p}" for p in problems)


def test_a_seventh_dynamic_construct_exception_reddens_the_ceiling():
    """Контроль правила реестра: седьмая синтетическая запись — сверх потолка и устаревшая — краснит его."""
    seventh = f"app/pages/accounts.py::_connect_status::{grammar.DYNAMIC_KIND_TEXT_EXECUTION}"
    registry = {**grammar.DYNAMIC_CONSTRUCT_EXCEPTIONS, seventh: "синтетическая седьмая запись контроля"}
    problems = _dynamic_exception_problems(registry, grammar.DYNAMIC_CONSTRUCT_EXCEPTIONS_CEILING)

    assert any("выше потолка" in problem for problem in problems), (
        f"седьмая запись реестра не краснит потолок {grammar.DYNAMIC_CONSTRUCT_EXCEPTIONS_CEILING}: {problems}"
    )
    assert any(seventh in problem and "устарела" in problem for problem in problems), (
        f"запись без живой конструкции не краснит правило реестра: {problems}"
    )


# Исключённый владелец трасера WR-38 (план 16-59): общий путь записи репозитория. Строка его тела, после которой
# правило подкладывает в памяти вторую конструкцию того же вида; файл на диске не меняется.
EXEMPT_OWNER_PATH = "app/repositories/base.py"
EXEMPT_OWNER_KEY = f"{EXEMPT_OWNER_PATH}::BaseRepository.update::{grammar.DYNAMIC_KIND_COMPUTED_ATTRIBUTE}"
EXEMPT_OWNER_ANCHOR = "setattr(entity, field, value)"


def _plant_after_anchor(source: str, anchor: str, lines: tuple[str, ...]) -> tuple[str, int]:
    """`source` с `lines`, вставленными тем же отступом сразу после единственной строки `anchor`; номер последней."""
    rows = source.splitlines(keepends=True)
    at = [i for i, row in enumerate(rows) if row.strip() == anchor]
    assert len(at) == 1, f"строка `{anchor}` в `{EXEMPT_OWNER_PATH}` не единственна: строки {[i + 1 for i in at]}"
    indent = rows[at[0]][: len(rows[at[0]]) - len(rows[at[0]].lstrip())]
    planted = rows[: at[0] + 1] + [f"{indent}{line}\n" for line in lines] + rows[at[0] + 1 :]
    return "".join(planted), at[0] + 1 + len(lines)


@pytest.mark.parametrize(
    ("planted_lines", "expected_text"),
    [
        pytest.param(
            ('op = kwargs.pop("op", "add")', "getattr(self.session, op)(type(entity), [kwargs])"),
            "getattr(self.session, op)",
            id="a-new-construct-of-the-same-kind",
        ),
        pytest.param((EXEMPT_OWNER_ANCHOR,), EXEMPT_OWNER_ANCHOR, id="the-pinned-construct-repeated"),
    ],
)
def test_an_extra_construct_in_an_exempt_owner_is_red(tmp_path, planted_lines, expected_text):
    """ТРАСЕР WR-38 (план 16-59; О-25 (а), свойство 6; О-23 (а), свойство 1; D-13, D-17): вторая конструкция того же
    вида в теле исключённого владельца — находка канала у обоих гейтов, а не молчание реестра.

    Живой `app/repositories/base.py` с подложенными в тело `BaseRepository.update` строками (новая
    `getattr(self.session, op)(…)` — вычисленный вызов любого API сессии, в том числе `bulk_update_mappings`, — или
    повтор закреплённой `setattr(entity, field, value)`, ось числа) кладётся в синтетическое дерево; правило живых
    деревьев каждого гейта (`dynamic_construct_scan`: канал `dynamic_construct_findings` и `exempt_dynamic_constructs`)
    даёт ровно одну находку вида «вычисленное имя атрибута» на подложенной строке. До плана 16-59 ключ записи
    реестра снимал ВСЕ конструкции своего вида у владельца — 0 находок у обоих гейтов.
    """
    live = (privacy.PROJECT_ROOT / EXEMPT_OWNER_PATH).read_text(encoding="utf-8")
    source, planted_line = _plant_after_anchor(live, EXEMPT_OWNER_ANCHOR, planted_lines)
    planted = tmp_path / EXEMPT_OWNER_PATH
    planted.parent.mkdir(parents=True)
    planted.write_text(source, encoding="utf-8")

    location = f"{EXEMPT_OWNER_PATH}:{planted_line} — "
    found: dict[str, list[str]] = {}
    for title, module in (("приватности", privacy), ("писателя", writer)):
        paths, offences = module.dynamic_construct_scan(tmp_path)
        assert planted in paths, f"обход гейта {title} не видит подложенный владелец: {paths}"
        found[title] = offences
    reddened = [
        title
        for title, offences in found.items()
        if len(offences) == 1
        and offences[0].startswith(location)
        and f"— {grammar.DYNAMIC_KIND_COMPUTED_ATTRIBUTE} — {expected_text}" in offences[0]
    ]

    assert reddened == ["приватности", "писателя"], (
        "конструкция в теле исключённого владельца снята реестром молча (WR-38): ключ "
        f"`{EXEMPT_OWNER_KEY}` снимает больше закреплённого; находки гейтов: {found}"
    )


def test_every_dynamic_construct_exception_pins_its_construct_texts():
    """Закрепление реестра правдиво (ревью WR-38; О-25 (а), свойство 6; план 16-59; D-13, D-17).

    Ключи `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS` — ровно ключи `DYNAMIC_CONSTRUCT_EXCEPTIONS`, и у каждой записи
    множество текстов конструкций её вида у владельца на живом дереве с числом равно закреплённому: помощник
    `_dynamic_exception_problems` проблем не называет.
    """
    registry = grammar.DYNAMIC_CONSTRUCT_EXCEPTIONS
    pinned = grammar.DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS
    problems = _dynamic_exception_problems(registry, grammar.DYNAMIC_CONSTRUCT_EXCEPTIONS_CEILING)

    assert set(pinned) == set(registry), (
        "ключи закрепления не равны ключам реестра: "
        f"лишние {sorted(set(pinned) - set(registry))}, без закрепления {sorted(set(registry) - set(pinned))}"
    )
    assert not problems, "закрепление реестра исключений канала неправдиво:\n" + "\n".join(f"  {p}" for p in problems)


def test_a_missing_or_extra_pinned_construct_reddens_the_registry_rule(monkeypatch):
    """Контроль закрепления (ревью WR-38; план 16-59): лишняя и недостающая закреплённая конструкция краснят правило.

    Таблица `DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS` подменена копией: у записи `BaseRepository.update` закреплён лишний
    текст, которого у владельца нет («запись устарела»), у записи `update_schedule` закрепление пусто — живая
    `setattr(schedule, field, value)` становится «лишней конструкцией у исключённого владельца». Помощник
    `_dynamic_exception_problems` читает таблицу в момент вызова и называет обе проблемы; прежний исход седьмой записи —
    «выше потолка» и «устарела» — не меняется.
    """
    planted_text = "getattr(self.session, op)(type(entity), [kwargs])"
    schedule_key = f"app/routes/schedules.py::update_schedule::{grammar.DYNAMIC_KIND_COMPUTED_ATTRIBUTE}"
    schedule_text = "setattr(schedule, field, value)"
    pinned = dict(grammar.DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS)
    pinned[EXEMPT_OWNER_KEY] = (*pinned[EXEMPT_OWNER_KEY], planted_text)
    pinned[schedule_key] = ()
    monkeypatch.setattr(grammar, "DYNAMIC_CONSTRUCT_EXCEPTION_TEXTS", pinned)
    registry = grammar.DYNAMIC_CONSTRUCT_EXCEPTIONS
    problems = _dynamic_exception_problems(registry, grammar.DYNAMIC_CONSTRUCT_EXCEPTIONS_CEILING)
    missing = [p for p in problems if EXEMPT_OWNER_KEY in p and "запись устарела" in p and planted_text in p]
    extra = [p for p in problems if schedule_key in p and "лишняя конструкция" in p and schedule_text in p]

    assert missing and extra, (
        "закрепление реестра не краснит лишнюю и недостающую конструкцию (WR-38): "
        f"недостающая {missing}, лишняя {extra}; проблемы помощника: {problems}"
    )
    seventh = f"app/pages/accounts.py::_connect_status::{grammar.DYNAMIC_KIND_TEXT_EXECUTION}"
    seventh_problems = _dynamic_exception_problems(
        {**registry, seventh: "синтетическая седьмая запись контроля"}, grammar.DYNAMIC_CONSTRUCT_EXCEPTIONS_CEILING
    )
    assert any("выше потолка" in problem for problem in seventh_problems), seventh_problems
    assert any(seventh in problem and "устарела" in problem for problem in seventh_problems), seventh_problems


# Правила канала запрета этого модуля (план 16-53): абзац канала докстринга называет каждое.
BAN_CHANNEL_RULES = (
    "test_a_planted_module_object_read_reddens_both_gates",
    "test_every_dynamic_construct_case_is_banned_by_both_gates",
    "test_a_judgeable_twin_is_not_banned",
    "test_the_dynamic_construct_tables_cover_every_kind",
    "test_the_dynamic_construct_exceptions_are_named_and_under_their_ceiling",
    "test_a_seventh_dynamic_construct_exception_reddens_the_ceiling",
    "test_an_extra_construct_in_an_exempt_owner_is_red",
    "test_every_dynamic_construct_exception_pins_its_construct_texts",
    "test_a_missing_or_extra_pinned_construct_reddens_the_registry_rule",
    "test_the_parity_docstring_names_the_ban_channel_truthfully",
)
BAN_CHANNEL_DOC_NEEDLES = ("О-23 (а)", "запрещённ", "`dynamic_construct_findings`", "`DYNAMIC_CONSTRUCT_EXCEPTIONS`")
NINTH_DICTIONARY_NEEDLES = ("`print`", "`update`", "`sys.modules[__name__]`", "`me = sys.modules[__name__]`")
# Фраза абзаца словаря девятого круга до плана 16-53 (ревью IN-22): класс шире словаря.
REFUTED_NINTH_DICTIONARY_CLAIM = (
    "толкование псевдонима, закрывающее путь носителя (коллизия имени носителя), краснят матрицы"
)
BAN_CHANNEL_HEADER = "# --- Канал запрета динамических конструкций"
BAN_CHANNEL_HEADER_NEEDLES = (
    "О-23 (а)",
    "свойство 1",
    "в коде нет конструкции, которую гейт не умеет судить",
    "исключения",
    "потолок",
)


def _doc_bullet(doc: str, heading: str) -> str:
    """Пункт докстринга, начатый строкой `* <heading>`, до следующего пункта (пробелы схлопнуты)."""
    lines = doc.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(f"* {heading}")), None)
    if start is None:
        return ""
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("* ")), len(lines))
    return " ".join(" ".join(lines[start:end]).split())


def _comment_block(source: str, header: str) -> str:
    """Комментарий-шапка, начатая строкой `header`: подряд идущие строки `#` (пробелы схлопнуты)."""
    lines = source.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(header)), None)
    if start is None:
        return ""
    block: list[str] = []
    for line in lines[start:]:
        if not line.startswith("#"):
            if block and not line.strip():
                continue
            break
        block.append(line.lstrip("#").strip())
    return " ".join(" ".join(block).split())


def test_the_parity_docstring_names_the_ban_channel_truthfully():
    """Тексты канала правдивы (план 16-53; О-23 (а), свойства 1, 4, 5; ревью IN-22).

    Докстринг этого модуля: пункт о канале называет «О-23 (а)», запрет, `dynamic_construct_findings`,
    `DYNAMIC_CONSTRUCT_EXCEPTIONS` и каждое правило канала `BAN_CHANNEL_RULES`; пункт о словаре девятого круга называет
    соперников словаря `print` и `update` и два написания объекта модуля и не содержит прежней фразы о классе
    `REFUTED_NINTH_DICTIONARY_CLAIM`. Комментарий-шапка канала общего модуля называет решение, свойство 1, обещание,
    исключения и потолок.
    """
    doc = ast.get_docstring(_module_tree()) or ""
    channel = _doc_bullet(doc, "Канал запрета динамических конструкций")
    ninth = _doc_bullet(doc, "Словарь девятого круга")
    header = _comment_block(Path(grammar.__file__).read_text(encoding="utf-8"), BAN_CHANNEL_HEADER)
    problems = [f"пункт канала не называет «{needle}»" for needle in BAN_CHANNEL_DOC_NEEDLES if needle not in channel]
    problems += [f"пункт канала не называет правило `{rule}`" for rule in BAN_CHANNEL_RULES if f"`{rule}`" not in channel]
    problems += [f"пункт словаря девятого круга не называет {needle}" for needle in NINTH_DICTIONARY_NEEDLES
                 if needle not in ninth]
    if not ninth or REFUTED_NINTH_DICTIONARY_CLAIM in " ".join(doc.split()):
        problems.append(f"докстринг утверждает прежнюю фразу о классе: «{REFUTED_NINTH_DICTIONARY_CLAIM}»")
    problems += [f"шапка канала общего модуля не называет «{needle}»" for needle in BAN_CHANNEL_HEADER_NEEDLES
                 if needle not in header]

    assert not problems, (
        "докстринг паритета утверждает класс шире словаря или не называет канал:\n"
        + "\n".join(f"  {problem}" for problem in problems)
    )
