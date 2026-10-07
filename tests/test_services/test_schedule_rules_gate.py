"""ГЕЙТ ОГУЛЬНОГО ПЕРЕХВАТА В `app/services/schedule_rules.py` — по ТЕЛУ модуля, через `ast`.

ПРЕДМЕТ (находка 2 долга Фазы 10, D-18.2). Докстринг помощника
`next_run_or_none` обещал: «Запрет проверяется грепом по телу модуля» — и потому
не набирал имени запрещённой конструкции. Перезамер Фазы 15 показал, что
обещанного правила в дереве НЕТ: ни один модуль `tests/` не читал этот файл как
текст. Запрет был зелен вакуумом — объявлен, но не принуждён. Этот файл
заменяет обещание существующим принуждением.

ЧТО УТВЕРЖДАЕТСЯ. Ни один обработчик исключения в теле модуля не перехватывает
без указания типа (`except:`) и не перехватывает базовые типы (`Exception`,
`BaseException`); помощник перехватывает РОВНО имя объявленного перечня
`UNRUNNABLE_STORED_VALUE_ERRORS`, а не литеральный кортеж по месту; в перечне
ровно пять имён замера. Функции запрета принимают ИСХОДНИК ТЕКСТОМ, а не путь:
иначе контроли от вакуума ниже были бы невыразимы, и «зубы» правила пришлось бы
заявлять, а не показывать.

⚠️ РАСХОЖДЕНИЕ С ИДИОМОЙ ОБРАЗЦА — ОБЪЯВЛЕНО, А НЕ УНАСЛЕДОВАНО МОЛЧА.
`tests/test_pages/test_impersonation_gate.py::_declares_dependency` прямо
говорит, что обходит ОБЪЯВЛЕНИЕ обработчика, а не тело, и называет основание:
«обход тела посчитал бы упоминание в докстринге или комментарии». Этот гейт
обходит ИМЕННО ТЕЛО. Перешаг законен потому, что гейт читает УЗЛЫ дерева
(`ast.Try` / `ast.ExceptHandler`), а не строки: докстринг в дереве есть
строковая константа, комментария в дереве нет вовсе, и узлом обработчика
исключения ни то ни другое не становится — упоминание невидимо гейту ПО
ПОСТРОЕНИЮ, а не по договорённости. У образца предмет другой: там искомое —
ИМЯ зависимости, и имя в докстринге неотличимо от имени в теле по строке, но
отличимо по месту в дереве, поэтому образец и сузил обход до объявления. Здесь
искомое — сам УЗЕЛ перехвата, и сужать обход незачем. Доказательство не
заявлено, а исполнено: правило разности (тест 4) утверждает, что обход по
ТЕКСТУ модуля находит упоминания конструкции в докстринге, а обход по дереву
не находит ни одного.

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ. Зелёный цвет означает ровно две вещи: в теле
модуля нет огульного перехвата, и помощник перехватывает ровно объявленный
перечень из пяти имён. Он НЕ означает, что перечень ПОЛОН: его пять имён — замер
шести форм испорченной строки, и седьмая форма может прийти с новым типом
исключения; такая находка ЗАПИСЫВАЕТСЯ, а не закрывается расширением перечня
(расширение «на всякий случай» есть та же болезнь, что огульный перехват). Он
НЕ означает, что помощника спрашивают все вызывающие — это предмет правил
страничного слоя (`tests/test_pages/test_editor_schedules.py`,
`tests/test_schedules_out_of_domain_resume.py`). И он не говорит НИЧЕГО о
проверке расписаний к отправке в `app/application/scheduling/use_cases.py`,
которая логирует и пробрасывает, так что одна испорченная строка обрывает всю
партию рассылки: это ПРЕДСУЩЕСТВУЮЩИЙ дефект WR-03, записанный отложенным и
этой фазе не вменяемый. Правила, закрепляющего сегодняшний обрыв партии как
норму, здесь нет намеренно — день починки покраснил бы его, и починка выглядела
бы поломкой этой фазы.
"""

import ast
import re
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "services" / "schedule_rules.py"
)
HELPER_NAME = "next_run_or_none"
DECLARED_LIST_NAME = "UNRUNNABLE_STORED_VALUE_ERRORS"

# Базовые типы, перехват которых равен огульному: под ними лежит всё, что
# помощник обязан пропустить наверх, — отказ СУБД, отказ сети, ошибка
# программиста.
BASE_EXCEPTION_NAMES = frozenset({"Exception", "BaseException"})

# ⚠️ ЧИСЛО ИМЁН ПЕРЕЧНЯ ОБЪЯВЛЕНО ЛИТЕРАЛОМ, А НЕ ВЫВЕДЕНО (идиома SP-1).
# Перечень, опустевший молча, оставил бы правило перехвата зелёным ровно тогда,
# когда защита исчезла; выросший молча — проглотил бы то, что обязан пропустить.
UNRUNNABLE_STORED_VALUE_ERROR_NAMES_DECLARED = 5

# Текстовая форма запрещённой конструкции — ТОЛЬКО для правила разности (тест 4).
FORBIDDEN_FORM_TEXT_RE = re.compile(r"\bexcept(?:\s+(?:Exception|BaseException))?\s*:")


def _module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _module_except_handlers(source: str) -> list[ast.ExceptHandler]:
    """Все обработчики исключения тела — обходом `ast.Try` по дереву исходника."""
    handlers: list[ast.ExceptHandler] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            handlers.extend(node.handlers)
    return handlers


def _caught_type_name(expression: ast.expr) -> str | None:
    """Имя перехватываемого типа: `Name` или последний член `Attribute`."""
    if isinstance(expression, ast.Name):
        return expression.id
    if isinstance(expression, ast.Attribute):
        return expression.attr
    return None


def _enclosing_functions(source: str) -> dict[int, str]:
    """Строка обработчика → имя объемлющей функции, для отказа, называющего место."""
    places: dict[int, str] = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for inner in ast.walk(node):
                if isinstance(inner, ast.ExceptHandler):
                    places.setdefault(inner.lineno, node.name)
    return places


def _blanket_catch_offences(source: str) -> list[str]:
    """Огульные перехваты тела: без типа либо базового типа — строка и что перехвачено."""
    places = _enclosing_functions(source)
    offences: list[str] = []
    for handler in _module_except_handlers(source):
        where = f"строка {handler.lineno} ({places.get(handler.lineno, '<модуль>')})"
        if handler.type is None:
            offences.append(f"{where}: перехват без указания типа")
            continue
        caught = (
            handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
        )
        for expression in caught:
            name = _caught_type_name(expression)
            if name in BASE_EXCEPTION_NAMES:
                offences.append(f"{where}: перехват базового типа {name}")
    return offences


def _helper_catches_other_than_the_declared_list(source: str) -> list[str]:
    """Обработчики помощника, перехватывающие НЕ имя объявленного перечня."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == HELPER_NAME:
            wrong = []
            handlers = [
                handler
                for inner in ast.walk(node)
                if isinstance(inner, ast.Try)
                for handler in inner.handlers
            ]
            if not handlers:
                return [f"{HELPER_NAME}: ни одного обработчика исключения"]
            for handler in handlers:
                if not (
                    isinstance(handler.type, ast.Name)
                    and handler.type.id == DECLARED_LIST_NAME
                ):
                    shown = ast.unparse(handler.type) if handler.type else "<без типа>"
                    wrong.append(f"строка {handler.lineno}: перехвачено {shown}")
            return wrong
    return [f"в исходнике нет функции {HELPER_NAME}"]


def _declared_list_names(source: str) -> list[str]:
    """Имена в кортеже `UNRUNNABLE_STORED_VALUE_ERRORS` уровня модуля."""
    for node in ast.parse(source).body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == DECLARED_LIST_NAME
                for target in node.targets
            )
            and isinstance(node.value, ast.Tuple)
        ):
            return [_caught_type_name(element) or "?" for element in node.value.elts]
    return []


def _text_mentions_of_the_forbidden_form(source: str) -> int:
    """Вхождения запрещённой конструкции в ТЕКСТ модуля — докстринги включительно."""
    return len(FORBIDDEN_FORM_TEXT_RE.findall(source))


# --- Утверждения о модуле ------------------------------------------------------


def test_no_blanket_catch_in_the_schedule_rules_body():
    """Тест 1: ни один обработчик тела не перехватывает огульно."""
    offences = _blanket_catch_offences(_module_source())

    assert offences == [], (
        "в теле app/services/schedule_rules.py огульный перехват — он проглотил "
        f"бы отказ СУБД, отказ сети и ошибку программиста: {offences}"
    )


def test_the_helper_catches_exactly_the_declared_list_by_name():
    """Тест 2: помощник перехватывает ИМЯ перечня, а не литеральный кортеж по месту.

    Кортеж по месту можно было бы расширить незаметно для правила, стерегущего
    сам перечень (тест 3).
    """
    wrong = _helper_catches_other_than_the_declared_list(_module_source())

    assert wrong == [], (
        f"{HELPER_NAME} перехватывает не {DECLARED_LIST_NAME}: {wrong}"
    )


def test_the_declared_list_holds_exactly_the_measured_names():
    """Тест 3: в перечне ровно объявленное число имён замера, и перечень не пуст."""
    names = _declared_list_names(_module_source())

    assert UNRUNNABLE_STORED_VALUE_ERROR_NAMES_DECLARED > 0
    assert len(names) == UNRUNNABLE_STORED_VALUE_ERROR_NAMES_DECLARED, (
        f"в {DECLARED_LIST_NAME} {len(names)} имён, объявлено "
        f"{UNRUNNABLE_STORED_VALUE_ERROR_NAMES_DECLARED}: {names}. Новая форма "
        f"отказа записывается НАХОДКОЙ, а не закрывается расширением перечня"
    )
    assert not set(names) & BASE_EXCEPTION_NAMES, names


def test_the_text_walk_sees_the_docstring_and_the_tree_walk_does_not():
    """Тест 4: машинное доказательство, что гейт читает тело, а не текст.

    Обход по ТЕКСТУ находит запрещённую конструкцию в докстринге помощника, где
    она теперь названа прямо; обход по дереву не находит ни одной. Утверждаются
    оба числа и их разность отдельно: при нуле текстовых вхождений правило
    ничего бы не доказывало — докстринг молчал бы, и разность совпала бы с нулём
    по пустоте.
    """
    source = _module_source()
    text_mentions = _text_mentions_of_the_forbidden_form(source)
    tree_offences = len(_blanket_catch_offences(source))

    assert text_mentions > 0, (
        "докстринг модуля не называет запрещённую конструкцию — причина молчать "
        "снята гейтом по дереву, а назвать её так и не назвали"
    )
    assert tree_offences == 0, tree_offences
    assert text_mentions - tree_offences == text_mentions > 0, (
        f"разность обходов {text_mentions - tree_offences}: текст {text_mentions}, "
        f"дерево {tree_offences}"
    )


def test_the_helper_docstring_names_its_enforcing_rule():
    """Докстринг помощника называет принуждающее правило и несёт летопись оговорки.

    Прежняя вынужденная оговорка снята, а не вычеркнута молча: на её месте —
    имя этого файла, способ принуждения и формула летописи D-30/D-32.
    """
    tree = ast.parse(_module_source())
    helper = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == HELPER_NAME
    )
    docstring = ast.get_docstring(helper) or ""

    assert "tests/test_services/test_schedule_rules_gate.py" in docstring
    assert "ПРОГНОЗ НЕ БЫЛ ОШИБКОЙ — ОН УСТАРЕЛ" in docstring
    assert "поэтому имя запрещённой конструкции здесь и не набирается" not in docstring


# --- Контроли от вакуума -------------------------------------------------------
#
# ⚠️ ЗАПРЕТ ОГУЛЬНОГО ПЕРЕХВАТА ИСТИНЕН НА МОДУЛЕ БЕЗ ЕДИНОГО `try` И ПРОЙДЁТ НА
# СЛОМАННОМ РАЗБОРЕ. Поэтому зубы правила показаны на синтетических исходниках
# (отрицательные контроли), а его зрение — на неизменённом модуле
# (положительный контроль: обработчиков найдено больше нуля).

SYNTHETIC_BARE_CATCH = '''
def swallow_everything(schedule):
    try:
        return schedule.moment()
    except:
        return None
'''

SYNTHETIC_BASE_TYPE_CATCH = '''
def swallow_programmer_errors(schedule):
    try:
        return schedule.moment()
    except (ValueError, Exception):
        return None
'''

SYNTHETIC_LITERAL_TUPLE_HELPER = '''
UNRUNNABLE_STORED_VALUE_ERRORS = (ValueError,)

def next_run_or_none(schedule):
    try:
        return schedule.moment()
    except (ValueError, TypeError, KeyError):
        return None
'''


def test_control_bare_catch_in_a_synthetic_source_is_named():
    """Тест 5: перехват без типа краснеет и НАЗЫВАЕТ функцию и строку."""
    offences = _blanket_catch_offences(SYNTHETIC_BARE_CATCH)

    assert len(offences) == 1, offences
    assert "swallow_everything" in offences[0], offences
    assert "строка 5" in offences[0], offences


def test_control_base_type_catch_does_not_pass_as_a_named_type():
    """Тест 6: `Exception` — даже в кортеже с узким типом — не «указанный» тип."""
    offences = _blanket_catch_offences(SYNTHETIC_BASE_TYPE_CATCH)

    assert offences == [
        "строка 5 (swallow_programmer_errors): перехват базового типа Exception"
    ], offences


def test_control_literal_tuple_in_the_helper_is_flagged():
    """Кортеж по месту вместо имени перечня краснеет правилом теста 2."""
    wrong = _helper_catches_other_than_the_declared_list(
        SYNTHETIC_LITERAL_TUPLE_HELPER
    )

    assert wrong == ["строка 7: перехвачено (ValueError, TypeError, KeyError)"], wrong


def test_control_the_unchanged_module_is_silent_and_seen():
    """Тест 7: на неизменённом модуле гейт молчит — и молчит, ВИДЯ обработчики.

    Без утверждения «найдено больше нуля» зелень гейта означала бы лишь, что
    разбор не нашёл ни одного `try`.
    """
    source = _module_source()
    handlers = _module_except_handlers(source)

    assert len(handlers) > 0, "разбор не нашёл в модуле ни одного обработчика"
    assert _blanket_catch_offences(source) == []
    assert _helper_catches_other_than_the_declared_list(source) == []
