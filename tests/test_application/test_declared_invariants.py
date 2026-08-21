"""Машинный гейт на класс «объявление утверждает то, чего код рядом с ним не делает».

ПРЕДМЕТ. За этот класс фаза 05 получила раунды верификации 4, 5 и 6 подряд. Раунд 5
нашёл четыре экземпляра, раунд 6 — ещё три (в четырёх местах дерева), причём один из
них был написан планом 05-18 в том же прогоне, в котором план 05-19 закрывал
предыдущие. `Gaps Summary` раунда 6 сказал прямо: пока проверка остаётся чтением
глазами, седьмой раунд найдёт четвёртый экземпляр. Этот файл переводит проверку из
чтения глазами в прогон.

ЧТО ГЕЙТ ДОКАЗЫВАЕТ. У каждого объявления денежного пути, несущего утверждение, есть
НАЗВАННЫЙ ИСПОЛНЯЕМЫЙ СВИДЕТЕЛЬ: абзац называет имя теста, и имя резолвится в функцию,
объявленную в суите. Либо абзац записан в реестр долга с причиной.

ПОЧЕМУ ПРЕДМЕТ ВЫВОДИТСЯ ИЗ ТЕКСТА, А НЕ ИЗ МАРКЕРА. Первая редакция этого гейта
отбирала абзацы по маркеру `⚠️`. Отбор по маркеру не задержал бы НИ ОДНОГО из четырёх
мест находок раунда 6: ни одно из них маркера не несёт — маркер стоит в СОСЕДНЕМ
абзаце, отделённом пустой строкой. Гейт, отбирающий по разметке, слеп к новому абзацу,
разметки не несущему, — то есть к ровно тому событию, за которое фаза получила раунд 6.
Поэтому главный признак отбора выводится из САМОГО ТЕКСТА (заглавный прогон), а маркер
остаётся ВТОРЫМ слагаемым объединения: снятие маркера больше не выводит абзац из-под
проверки, а исход «снять пометку и разойтись» закрыт по построению.

ЧЕГО ГЕЙТ НЕ ДОКАЗЫВАЕТ — сказано здесь, а не только в плане, по образцу докстринга
`tests/test_migrations/test_model_matches_head.py`, который прямо называет, что о боевой
схеме не знает ничего.

* Он НЕ ЧИТАЕТ ТЕЛА ФУНКЦИИ и не сравнивает смысл абзаца с поведением. Абзац,
  называющий существующий, но НЕ ТОТ тест, гейт пропустит зелёным. Соответствие
  свидетеля предмету судится человеком — это объявленная граница средства, а не его
  дефект: претензия на большее была бы ровно тем классом, против которого он написан.
* Он НЕ СЧИТАЕТ записи реестра долга верными. Реестр он только ПЕРЕСЧИТЫВАЕТ: столько
  объявлений денежного пути сегодня не имеют исполняемого свидетеля.
* ХРАПОВИК ЛОВИТ ДОБАВЛЕНИЕ, А НЕ ПЕРЕФОРМУЛИРОВАНИЕ. Отпечаток записи берётся от
  текста абзаца, поэтому переписывание уже записанного абзаца выбивает запись из реестра
  и требует либо свидетеля, либо новой записи ВЗАМЕН старой. Число записей при такой
  замене не растёт, и храповик замену пропустит — видимой она остаётся только в диффе
  реестра. Против сценария, за который фаза получила раунд 6 (план 05-18 ДОБАВИЛ абзац),
  храповик работает: добавленный абзац даёт рост, и прогон краснеет.

ОБРАЗЕЦ ФОРМЫ — AST-ловушка порядка снятия признака живости
(`test_the_liveness_is_sampled_before_the_date_moves`, план 05-19): множество выводится
из свойства кода, а не выписывается списком; зубы доказываются негативными контролями
над СИНТЕТИЧЕСКИМИ исходниками, а не правкой настоящих файлов.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Маркер объявленного инварианта — ВТОРОЕ слагаемое отбора, а не его источник.
INVARIANT_MARKER = "⚠️"

# Порог заглавного прогона. Рабочее значение — два, и причина названа прогоном, а
# не вкусом: при пороге три из отбора выпадают ДВЕНАДЦАТЬ живых абзацев денежного
# пути, четверо из которых записаны долгом. Пример, снятый с живого дерева, —
# абзац `countdown_base` о публичности символа: его прогон есть слова «ТА ЖЕ», то
# есть ровно два. Повышение порога сузило бы предмет гейта молча.
#
# ⚠️ ПРЕЖНИЙ ПРИМЕР ЭТОГО АБЗАЦА УКАЗЫВАЛ НА МОДУЛЬ ПРАВИЛА ПЕРЕХОДА ТАРИФОВ,
# снятый планом 05.1-07 целиком. Пример ЗАМЕНЁН на живой, а не вычеркнут: довод
# без примера следующий читатель проверить не может и поднимет порог, решив, что
# число выбрано на глаз.
CAPITAL_RUN_THRESHOLD = 2

# Пакет денежного пути. Множество проверяемых модулей ВЫВОДИТСЯ обходом каталога:
# модуль, добавленный следующим планом, попадает под гейт сам.
BILLING_PACKAGE = PROJECT_ROOT / "app" / "application" / "billing"

# Модули денежного пути ВНЕ пакета. Выводить их неоткуда — их приходится называть,
# и молчание о них было бы дырой в гейте: денежный путь проходит через них.
EXTRA_CHECKED_MODULES = ("app/services/payment_service.py",)

TESTS_ROOT = PROJECT_ROOT / "tests"

LEDGER_PATH = Path(__file__).resolve().parent / "declared_invariants_without_witness.txt"

# ЗАПИСАННЫЙ ДОЛГ, А НЕ ЗАПАС. Величина равна фактическому числу записей реестра и
# может ТОЛЬКО СНИЖАТЬСЯ: запас есть место для нового ложного абзаца, то есть ровно
# та дыра, которую гейт закрывает.
#
# ⚠️ 37 → 21 ПЛАНОМ 05.1-07, И ПОНИЖЕНИЕ ПРИЕХАЛО ТЕМ ЖЕ КОММИТОМ, ЧТО УДАЛИЛ
# МОДУЛИ. Множество проверяемых модулей ВЫВОДИТСЯ обходом каталога, поэтому
# снятие двух модулей матрицы тарифов вынесло записи их абзацев из реестра САМО;
# разнеси удаление и понижение по двум планам — и прогон был бы красен в
# промежутке по причине, к предмету правки отношения не имеющей.
WITHOUT_WITNESS_CEILING = 21

LEDGER_SEPARATOR = "::"
FINGERPRINT_LENGTH = 60

TEST_NAME_PATTERN = re.compile(r"test_[a-z0-9_]+")

# Места находок раунда 6 — тройками «модуль, владелец, фрагмент».
# Ключ ТРОЙНОЙ, а не по фрагменту: фрагмент может встречаться в модуле дважды, и
# второе вхождение принадлежать другому владельцу. Фрагменты сняты с ЖИВОГО дерева
# после волн 18 и 19; владелец замене не подлежит.
#
# ⚠️ ИХ БЫЛО ЧЕТЫРЕ, СТАЛО ДВА, И УБЫЛЬ ЗДЕСЬ — СНЯТИЕ ПРЕДМЕТА, А НЕ ОСЛАБЛЕНИЕ
# ГЕЙТА (план 05.1-07). Тройка конвертации остатка по отношению цен и тройка
# правила перехода между тарифами ушли вместе со своими носителями: первая функция
# снята из модуля срока подписки, второй модуль удалён целиком, и держать ключ на
# несуществующем владельце значило бы краснить прогон по причине, к предмету
# правки отношения не имеющей. Тройки, чьи модуль и владелец ЖИВЫ, не
# тронуты ни одной буквой: их абзацы обязаны и дальше стоять в
# `_extend_subscription` ровно по одному разу.
ROUND_SIX_FINDINGS = (
    (
        "app/services/payment_service.py",
        "_extend_subscription",
        "ЧТО ИМЕННО ДЕЛАЕТ ПОДТВЕРЖДЁННЫЙ ПЛАТЁЖ",
    ),
    (
        "app/services/payment_service.py",
        "_extend_subscription",
        "ЧТО ПРОИСХОДИТ, КОГДА ОПЛАЧЕННЫЙ СРОК УЖЕ ИСТЁК",
    ),
)


@dataclass(frozen=True)
class Declaration:
    """Абзац объявления: путь модуля, владелец абзаца и его текст."""

    module: str
    owner: str
    text: str

    @property
    def fingerprint(self) -> str:
        return paragraph_fingerprint(self.text)

    @property
    def opening(self) -> str:
        return self.fingerprint


# --- признак отбора: три исполнимые части ----------------------------------------


def paragraph_words(paragraph: str) -> list[str]:
    """Часть 1 определения: СЛОВО есть элемент `str.split()`.

    Не «разделённые одним пробелом»: перенос строки внутри абзаца, табуляция и
    двойной пробел разделяют слова наравне с одинарным. Заголовки этих модулей
    регулярно переносятся на вторую строку докстринга, поэтому разница не
    умозрительна.
    """
    return paragraph.split()


def word_is_capital(word: str) -> bool:
    """Часть 2 определения: ЗАГЛАВНОЕ слово.

    У слова снимается вся пунктуация и разметка, из остатка берутся только буквенные
    символы, и требуется не менее двух таких букв, притом все заглавные. Отсюда:
    `add_one_month` не заглавно (и так же в обратных кавычках — кавычки снимает
    очистка); `Pro` не заглавно; токен `X-1` не заглавен (после очистки остаётся одна
    буква); `⚠️`, `*` и `—` не заглавны (буквенных символов ноль), поэтому маркер сам
    по себе прогона не образует и остаётся ОТДЕЛЬНЫМ признаком; «МЕСЯЦА,» и «МЕСЯЦА»
    — одно и то же слово; `WR-01` ЗАГЛАВНО (остаются `WR` — две заглавные буквы).
    """
    letters = [c for c in re.sub(r"[^\w]", "", word) if c.isalpha()]
    return len(letters) >= 2 and all(c.isupper() for c in letters)


def has_capital_run(paragraph: str, threshold: int = CAPITAL_RUN_THRESHOLD) -> bool:
    """Часть 3 определения: ПРОГОН при пороге `threshold`.

    Скользящее окно длины `threshold` по списку слов; абзац несёт прогон, если хотя
    бы у одного окна ВСЕ слова заглавны. Порог — ПАРАМЕТР, а не зашитая пара соседей:
    запись через пары даёт то же множество при пороге два, но на другой порог не
    обобщается вовсе.
    """
    words = paragraph_words(paragraph)
    if threshold <= 0 or len(words) < threshold:
        return False
    return any(
        all(word_is_capital(word) for word in words[index : index + threshold])
        for index in range(len(words) - threshold + 1)
    )


def paragraph_is_selected(
    paragraph: str, threshold: int = CAPITAL_RUN_THRESHOLD
) -> bool:
    """Отбор ведётся ОБЪЕДИНЕНИЕМ двух признаков, и ни один не сужает другого.

    (1) заглавный прогон — выводится из самого текста, поэтому новый абзац попадает
    под гейт без всякой разметки; (2) маркер объявленного инварианта — удерживает уже
    помеченное, поэтому снятие маркера не выводит абзац из-под проверки.
    """
    return has_capital_run(paragraph, threshold) or INVARIANT_MARKER in paragraph


def paragraph_fingerprint(paragraph: str) -> str:
    """Отпечаток абзаца: первые символы со схлопнутыми пробелами.

    Он читается человеком, ищется грепом и виден в диффе — иначе реестр долга был бы
    списком хешей, который никто не проверит.

    Хвостовой пробел снимается: обрезка по длине попадает в середину слова примерно
    в половине случаев, и запись реестра, оканчивающаяся пробелом, потерялась бы при
    разборе строки — то есть отпечаток не сошёлся бы сам с собой.
    """
    return " ".join(paragraph.split())[:FINGERPRINT_LENGTH].rstrip()


# --- разбор исходника на абзацы объявлений ----------------------------------------


def _owner_ranges(tree: ast.AST) -> list[tuple[int, int, str]]:
    ranges: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            end = getattr(node, "end_lineno", node.lineno) or node.lineno
            ranges.append((node.lineno, end, node.name))
    ranges.sort(key=lambda item: item[1] - item[0])
    return ranges


def _owner_of_line(ranges: list[tuple[int, int, str]], line: int) -> str:
    for start, end, name in ranges:
        if start <= line <= end:
            return name
    return "<module>"


def _docstring_declarations(module: str, tree: ast.AST) -> list[Declaration]:
    found: list[Declaration] = []
    owners: list[tuple[ast.AST, str]] = [(tree, "<module>")]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            owners.append((node, node.name))
    for node, owner in owners:
        docstring = ast.get_docstring(node)
        if not docstring:
            continue
        for paragraph in re.split(r"\n\s*\n", docstring):
            text = paragraph.strip()
            if text:
                found.append(Declaration(module=module, owner=owner, text=text))
    return found


def _comment_declarations(module: str, source: str, tree: ast.AST) -> list[Declaration]:
    ranges = _owner_ranges(tree)
    found: list[Declaration] = []
    block: list[str] = []
    block_line = 0
    for number, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        content = stripped[1:].strip() if stripped.startswith("#") else None
        if content:
            if not block:
                block_line = number
            block.append(content)
            continue
        if block:
            found.append(
                Declaration(
                    module=module,
                    owner=_owner_of_line(ranges, block_line),
                    text="\n".join(block),
                )
            )
            block = []
    if block:
        found.append(
            Declaration(
                module=module,
                owner=_owner_of_line(ranges, block_line),
                text="\n".join(block),
            )
        )
    return found


def parse_declarations(module: str, source: str) -> list[Declaration]:
    """Абзацы двух видов с указанием владельца: докстринги и блоки комментариев.

    Докстринги берутся по синтаксическому дереву — у модуля и у каждой функции и
    класса, деление пустой строкой. Блоки комментариев — подряд идущие строки,
    начинающиеся с решётки; пустая строка комментария разделяет блоки.
    """
    tree = ast.parse(source)
    return _docstring_declarations(module, tree) + _comment_declarations(
        module, source, tree
    )


# --- множество проверяемых модулей -------------------------------------------------


def billing_package_modules() -> list[str]:
    """Обход каталога пакета: все `.py`, кроме `__init__.py`."""
    return sorted(
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in BILLING_PACKAGE.glob("*.py")
        if path.name != "__init__.py"
    )


def checked_modules() -> list[str]:
    return billing_package_modules() + list(EXTRA_CHECKED_MODULES)


def module_declarations(module: str) -> list[Declaration]:
    return parse_declarations(module, (PROJECT_ROOT / module).read_text())


@lru_cache(maxsize=1)
def all_declarations() -> tuple[Declaration, ...]:
    found: list[Declaration] = []
    for module in checked_modules():
        found.extend(module_declarations(module))
    return tuple(found)


def selected_declarations(
    threshold: int = CAPITAL_RUN_THRESHOLD,
) -> tuple[Declaration, ...]:
    return tuple(
        item for item in all_declarations() if paragraph_is_selected(item.text, threshold)
    )


# --- резолвинг имён тестов ---------------------------------------------------------


@lru_cache(maxsize=1)
def declared_test_names() -> frozenset[str]:
    """Имена тестов, ОБЪЯВЛЕННЫЕ в суите, по синтаксическому дереву, а не грепом.

    Греп нашёл бы имя в строке докстринга и счёл бы его объявлением — то есть абзац
    мог бы «назвать свидетеля», процитировав самого себя.
    """
    names: set[str] = set()
    for path in sorted(TESTS_ROOT.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover - суита не содержит битых модулей
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    names.add(node.name)
    return frozenset(names)


def named_tests(paragraph: str) -> set[str]:
    return set(TEST_NAME_PATTERN.findall(paragraph))


# --- реестр долга ------------------------------------------------------------------


@dataclass(frozen=True)
class LedgerEntry:
    module: str
    owner: str
    fingerprint: str
    reason: str


def ledger_entries() -> list[LedgerEntry]:
    if not LEDGER_PATH.exists():
        return []
    entries: list[LedgerEntry] = []
    for line in LEDGER_PATH.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = [part.strip() for part in stripped.split(LEDGER_SEPARATOR)]
        if len(parts) != 4:
            raise AssertionError(
                f"строка реестра не разбирается на четыре части: {stripped!r}"
            )
        entries.append(LedgerEntry(*parts))
    return entries


def ledger_keys() -> set[tuple[str, str, str]]:
    return {(entry.module, entry.owner, entry.fingerprint) for entry in ledger_entries()}


def declaration_key(declaration: Declaration) -> tuple[str, str, str]:
    return (declaration.module, declaration.owner, declaration.fingerprint)


def render_ledger(reason: str) -> str:
    """Печать реестра по текущему дереву: базовый состав снимается одним прогоном."""
    lines = []
    for declaration in declarations_without_witness():
        lines.append(
            f" {LEDGER_SEPARATOR} ".join(
                (
                    declaration.module,
                    declaration.owner,
                    declaration.fingerprint,
                    reason,
                )
            )
        )
    return "\n".join(lines)


# --- сам гейт ----------------------------------------------------------------------


def declarations_without_witness(
    declarations: tuple[Declaration, ...] | None = None,
    names: frozenset[str] | None = None,
    keys: set[tuple[str, str, str]] | None = None,
) -> list[Declaration]:
    """Отобранные абзацы, не назвавшие существующего теста и не записанные в реестр."""
    declarations = selected_declarations() if declarations is None else declarations
    names = declared_test_names() if names is None else names
    keys = ledger_keys() if keys is None else keys
    orphans: list[Declaration] = []
    for declaration in declarations:
        if any(name in names for name in named_tests(declaration.text)):
            continue
        if declaration_key(declaration) in keys:
            continue
        orphans.append(declaration)
    return orphans


def _report(orphans: list[Declaration]) -> str:
    return "\n".join(
        f"  {item.module} :: {item.owner} :: {item.opening}" for item in orphans
    )


def _synthetic(source: str, module: str = "app/application/billing/synthetic.py"):
    return tuple(
        item
        for item in parse_declarations(module, source)
        if paragraph_is_selected(item.text)
    )


# --- основной гейт -----------------------------------------------------------------


def test_every_declared_invariant_names_an_executable_witness():
    """Каждый отобранный абзац называет существующий тест либо записан в реестр долга."""
    orphans = declarations_without_witness()
    assert not orphans, (
        "объявления денежного пути без исполняемого свидетеля и без записи в реестр "
        f"({len(orphans)}):\n" + _report(orphans)
    )


# --- негативные и позитивный контроли ----------------------------------------------

_SYNTHETIC_WITHOUT_TEST = '''"""Заголовок модуля.

ОТВЕТ СОВПАДАЕТ С `next_expiry` ТОЧНО, А НЕ ПРИБЛИЗИТЕЛЬНО.
"""
'''

_SYNTHETIC_UNKNOWN_TEST = '''"""Заголовок модуля.

ОТВЕТ СОВПАДАЕТ С `next_expiry` ТОЧНО. Закреплено
`test_this_witness_was_never_written_and_never_will_be`.
"""
'''

_SYNTHETIC_EXISTING_TEST = '''"""Заголовок модуля.

ПОРЯДОК ОТНОСИТЕЛЬНО `next_expiry` — ПРАВИЛО, А НЕ ОФОРМЛЕНИЕ. Закреплено
`test_the_liveness_is_sampled_before_the_date_moves`.
"""
'''

# Форма `WR-01` дословно: ложный абзац БЕЗ МАРКЕРА, набранный заглавным заголовком,
# а маркер стоит в СОСЕДНЕМ абзаце через пустую строку — ровно та геометрия, что в
# `subscription_period.py`, где находка раунда 6 и ближайший маркер разделены пустой
# строкой.
_SYNTHETIC_UNMARKED = '''"""Заголовок модуля.

ДЛИНА МЕСЯЦА БЕРЁТСЯ У `add_one_month` ОТ ТОЙ ЖЕ БАЗЫ, А НЕ КОНСТАНТОЙ 30.
Константа разошлась бы с `next_expiry` в феврале и в декабре.

⚠️ ПРЕДУСЛОВИЕ: ЦЕНА СТРОГО БОЛЬШЕ НУЛЯ. Закреплено
`test_the_liveness_is_sampled_before_the_date_moves`.
"""
'''


def test_the_helper_reports_a_declaration_that_names_no_test():
    """Негативный контроль 1: абзац, не называющий ни одного теста, краснит гейт."""
    declarations = _synthetic(_SYNTHETIC_WITHOUT_TEST)
    assert declarations, "помощник обязан отобрать синтетический абзац"
    orphans = declarations_without_witness(declarations, declared_test_names(), set())
    assert len(orphans) == 1
    assert "next_expiry" in orphans[0].text


def test_the_helper_reports_a_declaration_naming_a_test_that_does_not_exist():
    """Негативный контроль 2: имя есть, но не резолвится — гейт краснеет."""
    declarations = _synthetic(_SYNTHETIC_UNKNOWN_TEST)
    assert declarations
    orphans = declarations_without_witness(declarations, declared_test_names(), set())
    assert len(orphans) == 1
    assert "test_this_witness_was_never_written_and_never_will_be" in orphans[0].text


def test_the_helper_reports_an_unmarked_declaration_in_the_shape_of_the_round_six_finding():
    """Негативный контроль 3: ложный абзац БЕЗ МАРКЕРА краснит гейт.

    Первые два контроля предполагают абзац уже помеченным и потому проверяют
    резолвинг, а не ОХВАТ. Относительно предмета раунда 6 они тавтологичны: все четыре
    места находок маркера не несут. Красноту на непомеченном абзаце проверяет только
    этот контроль.
    """
    declarations = _synthetic(_SYNTHETIC_UNMARKED)
    unmarked = [item for item in declarations if INVARIANT_MARKER not in item.text]
    assert unmarked, "непомеченный абзац обязан быть отобран заглавным прогоном"
    orphans = declarations_without_witness(declarations, declared_test_names(), set())
    assert any(INVARIANT_MARKER not in item.text for item in orphans), (
        "гейт обязан краснеть на непомеченном ложном абзаце — иначе его предмет слеп "
        "к тому самому событию, за которое фаза получила раунд 6"
    )


def test_the_helper_accepts_a_declaration_naming_an_existing_test():
    """Позитивный контроль: без него негативные не отличали бы работу от красноты всегда."""
    assert "test_the_liveness_is_sampled_before_the_date_moves" in declared_test_names()
    declarations = _synthetic(_SYNTHETIC_EXISTING_TEST)
    assert declarations
    orphans = declarations_without_witness(declarations, declared_test_names(), set())
    assert not orphans, _report(orphans)


# --- свидетель охвата --------------------------------------------------------------


def test_the_selection_covers_the_round_six_findings():
    """Каждое ПЕРЕЖИВШЕЕ место находок раунда 6 ОТОБРАНО и в реестре ОТСУТСТВУЕТ.

    Утверждение «гейт задержал бы находки раунда 6» вносится в исполняемый контракт
    здесь, а не повторяется прозой. Ключ тройной: фрагмент может встречаться в модуле
    дважды, и второе вхождение принадлежать другому владельцу.

    ⚠️ ПЕРЕЧЕНЬ СОКРАТИЛСЯ С ЧЕТЫРЁХ ТРОЕК ДО ДВУХ, И ЭТО СНЯТИЕ НОСИТЕЛЯ, А НЕ
    ПОБЛАЖКА. Два места находок жили в коде, который план 05.1-07 удалил вместе с
    матрицей тарифов; обоснование убыли стоит над самой константой. Тест держит
    ровно то же, что и держал: каждая ЖИВАЯ тройка обязана быть найдена в модуле
    РОВНО ОДИН раз, быть отобранной гейтом и не иметь записи в реестре долга.
    """
    keys = ledger_keys()
    for module, owner, fragment in ROUND_SIX_FINDINGS:
        matches = [
            item
            for item in module_declarations(module)
            if item.owner == owner and fragment in item.text
        ]
        assert len(matches) == 1, (
            f"фрагмент {fragment!r} у владельца {owner} в {module} найден "
            f"{len(matches)} раз — ожидалась ровно одна находка"
        )
        declaration = matches[0]
        assert paragraph_is_selected(declaration.text), (
            f"место находки раунда 6 не отобрано гейтом: {module} :: {owner} :: "
            f"{declaration.opening}"
        )
        assert declaration_key(declaration) not in keys, (
            f"место находки раунда 6 ушло в реестр долга: {module} :: {owner}"
        )


# --- полнота множества проверяемых модулей -----------------------------------------


def test_the_checked_set_covers_every_module_of_the_billing_package():
    """Опечатка в пути дала бы гейт, проверяющий пустое множество и зелёный всегда."""
    package = billing_package_modules()
    assert package, "обход пакета дал пустой перечень — гейт проверял бы ничто"
    checked = set(checked_modules())
    missing = [module for module in package if module not in checked]
    assert not missing, f"модули пакета вне проверяемого множества: {missing}"
    for module in checked:
        assert (PROJECT_ROOT / module).exists(), f"проверяемый модуль не существует: {module}"
    assert all_declarations(), "разбор дал ноль абзацев — гейт проверял бы ничто"


# --- храповик реестра --------------------------------------------------------------


def test_the_ledger_does_not_exceed_its_ceiling():
    """Потолок объявлен константой и может ТОЛЬКО СНИЖАТЬСЯ: рост краснит прогон."""
    entries = ledger_entries()
    assert len(entries) <= WITHOUT_WITNESS_CEILING, (
        f"реестр долга вырос: записей {len(entries)}, потолок "
        f"{WITHOUT_WITNESS_CEILING}. Новый абзац без свидетеля обязан получить "
        "свидетеля, а не запись в реестр"
    )


def test_the_ledger_holds_no_dead_entry():
    """Мёртвая запись краснит прогон: записанный долг обязан УМЕНЬШАТЬСЯ."""
    live = {declaration_key(item) for item in selected_declarations()}
    dead = [
        entry
        for entry in ledger_entries()
        if (entry.module, entry.owner, entry.fingerprint) not in live
    ]
    assert not dead, "записи реестра не резолвятся ни в один отобранный абзац:\n" + "\n".join(
        f"  {entry.module} :: {entry.owner} :: {entry.fingerprint}" for entry in dead
    )


def test_the_ledger_holds_no_marked_paragraph():
    """Помеченный абзац и место находки раунда 6 в реестр попасть не имеют права."""
    entries = ledger_entries()
    keys = {(entry.module, entry.owner, entry.fingerprint) for entry in entries}

    marked = [
        item
        for item in selected_declarations()
        if INVARIANT_MARKER in item.text and declaration_key(item) in keys
    ]
    assert not marked, "помеченные абзацы ушли в реестр долга:\n" + _report(marked)

    for module, owner, fragment in ROUND_SIX_FINDINGS:
        for item in module_declarations(module):
            if item.owner == owner and fragment in item.text:
                assert declaration_key(item) not in keys, (
                    f"место находки раунда 6 записано долгом: {module} :: {owner}"
                )
