"""Гейт единственного писателя номера (D-13, PHONE-02).

ЗАЧЕМ. Правило, ради которого существует признак «указан вручную», одно: номер,
который пользователь ввёл сам, автоматический источник не затирает (D-07). Модуль
`app/application/accounts/phone.py` держит его условной записью — одним оператором
UPDATE «записать, если номера нет и он не ручной». Но правило держится, только пока
писатель ОДИН. Мастер подключения Фазы 19, скрипт дозаполнения Фазы 20 или форма
Фазы 18 со своей записью в колонку обходят модуль разом и возвращают пару
«прочитать — проверить в Python — записать», в промежуток которой ручной номер
затирается (тест гонки `tests/test_application/test_account_phone_race.py`). Ни
один тест модуля-писателя такого обхода не заметит: обход живёт в другом файле.
Поэтому этот гейт краснит суиту на любой записи номера вне модуля-писателя.

ВСЕЛЕННАЯ — `app/**/*.py` и `scripts/**/*.py`, ОБХОДОМ каталогов, а не перечнем:
модуль, добавленный следующей фазой, попадает под гейт сам. Вне вселенной, и это
решение, а не забывчивость:
- `alembic/` — ревизия описывает схему, а не пишет номер аккаунта;
- `tests/` — тесты сеют строки напрямую, это их работа;
- `max_worker/` — пишет `phone` в `SessionState` воркера (`max_worker/main.py`,
  `self.phone`, `state.phone`), то есть в память процесса, а не в базу.

ПОЧЕМУ РАЗБОР `ast`, А НЕ ПОИСК СТРОКИ. В `app/pages/accounts.py` три законных
вызова с `phone=`: `render(..., phone=...)`, `_max_step_markup(..., phone=...)` и
`messenger.start_session(phone=...)` — номер из формы MAX уходит в разметку и в
воркер, а не в колонку. Наивный предикат «любой `phone=`» покраснел бы на всех трёх
(замер разведки), и автор следующего плана снял бы гейт как шумный. Предикат судит
только формы, которые действительно пишут в колонку.

ВИДЫ ЗАПИСИ, КОТОРЫЕ ГЕЙТ ЛОВИТ:
1. присваивание атрибуту `phone` / `phone_is_manual` (`=`, `+=`, аннотированное);
2. именованный аргумент `phone` / `phone_is_manual` в вызове `values(...)`,
   `update(...)`, `insert(...)` или `MessengerAccount(...)`.

ЦЕНА СТРОГОСТИ ВТОРОГО ВИДА. Имя `update` берётся по последнему звену вызова,
поэтому `some_dict.update(phone=x)` тоже покраснеет, хотя в колонку не пишет. Это
осознанно: отличить `dict.update` от `sqlalchemy.update` по исходнику без типов
нельзя, а ложное срабатывание здесь снимается переименованием ключа, тогда как
пропущенный второй писатель снимается только потерей ручного номера у пользователя.

ДО РЕЕСТРА ИСКЛЮЧЕНИЙ модуль-писатель пропускается обходом целиком — он и есть
единственный законный писатель. Поимённый реестр с причиной заменит этот пропуск.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Каталоги вселенной гейта. Множество файлов ВЫВОДИТСЯ их обходом.
WRITER_TREES = ("app", "scripts")

# Единственный законный писатель номера (D-12, D-13).
PHONE_WRITER_MODULE = "app/application/accounts/phone.py"

# Колонки номера в `messenger_accounts` (ревизия 0023).
PHONE_COLUMNS = frozenset({"phone", "phone_is_manual"})

# Вызовы, именованный аргумент которых пишет колонку: Core-операторы и конструктор
# модели. Имя берётся по последнему звену (`func.id` или `func.attr`).
WRITE_CALL_NAMES = frozenset({"values", "update", "insert", "MessengerAccount"})

KIND_ASSIGNMENT = "присваивание"
KIND_KEYWORD = "именованный аргумент"


def writer_sources(root: Path) -> list[Path]:
    """Все исходники вселенной гейта под `root` — ОБХОДОМ, а не перечнем.

    Параметр `root`, а не жёсткий путь, затем, чтобы обход можно было натравить на
    синтетическое дерево в `tmp_path` и доказать, что подложенный файл им находится.
    """
    found: list[Path] = []
    for tree in WRITER_TREES:
        base = root / tree
        if base.is_dir():
            found.extend(base.rglob("*.py"))
    return sorted(found)


def phone_write_offences(source: str, path: str) -> list[str]:
    """Записи номера в исходнике — строками «`путь:строка` — вид — предмет».

    Чистая функция над текстом: исключения реестра здесь НЕ применяются, поэтому ею
    же доказывается, что в самом модуле-писателе запись видна.
    """
    tree = ast.parse(source, filename=path)
    found: list[tuple[int, int, str, str]] = []

    def record(node: ast.AST, kind: str, subject: str) -> None:
        found.append((node.lineno, node.col_offset, kind, subject))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for attribute in _assigned_attributes(target):
                    record(attribute, KIND_ASSIGNMENT, ast.unparse(attribute))
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            for attribute in _assigned_attributes(node.target):
                record(attribute, KIND_ASSIGNMENT, ast.unparse(attribute))
        elif isinstance(node, ast.Call):
            name = _call_name(node)
            if name in WRITE_CALL_NAMES:
                for keyword in node.keywords:
                    if keyword.arg in PHONE_COLUMNS:
                        record(keyword, KIND_KEYWORD, f"{name}({keyword.arg}=…)")

    return [
        f"{path}:{line} — {kind} — {subject}"
        for line, _column, kind, subject in sorted(found)
    ]


def _assigned_attributes(target: ast.AST) -> list[ast.Attribute]:
    """Атрибуты номера среди целей присваивания, включая распаковку кортежа.

    Цель-имя (`phone: Mapped[...] = mapped_column(...)` в теле класса модели) не
    судится: это объявление колонки, а не запись в неё.
    """
    if isinstance(target, ast.Attribute):
        return [target] if target.attr in PHONE_COLUMNS else []
    if isinstance(target, (ast.Tuple, ast.List)):
        return [item for element in target.elts for item in _assigned_attributes(element)]
    if isinstance(target, ast.Starred):
        return _assigned_attributes(target.value)
    return []


def _call_name(call: ast.Call) -> str | None:
    """Последнее звено имени вызова: `update(...)` → `update`, `stmt.values(...)` → `values`."""
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def tree_offences(root: Path) -> tuple[list[Path], list[str]]:
    """Обход дерева и находки по всем файлам, кроме модуля-писателя."""
    sources = writer_sources(root)
    offences: list[str] = []
    for file in sources:
        relative = file.relative_to(root).as_posix()
        if relative == PHONE_WRITER_MODULE:
            continue
        offences.extend(phone_write_offences(file.read_text(encoding="utf-8"), relative))
    return sources, offences


def _plant(root: Path, relative: str, source: str) -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return target


def test_a_planted_phone_write_outside_the_writer_reddens_the_gate(tmp_path):
    """ТРАСЕР: присваивание номера в файле, о котором гейт не знал, краснит его.

    Без этого контроля живое правило зелено и при пустом обходе, и при предикате,
    не находящем ничего, — то есть проверяло бы ничто.
    """
    _plant(
        tmp_path,
        "app/pages/planted.py",
        "def save(account, x):\n"
        "    account.phone = '+79991234567'\n",
    )

    sources, offences = tree_offences(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in sources] == [
        "app/pages/planted.py"
    ], "обход синтетического дерева не нашёл подложенный файл"
    assert offences, (
        "подложенная запись номера не найдена: присваивание `account.phone` в "
        "app/pages/planted.py гейт пропустил"
    )
    assert any(
        offence.startswith(f"app/pages/planted.py:2 — {KIND_ASSIGNMENT}")
        for offence in offences
    ), f"находка не называет файл, строку и вид: {offences}"


ASSIGNMENT_CASES = [
    pytest.param("account.phone = x\n", "account.phone", id="assign-phone"),
    pytest.param(
        "account.phone_is_manual = True\n",
        "account.phone_is_manual",
        id="assign-phone-is-manual",
    ),
    pytest.param("obj.phone += x\n", "obj.phone", id="augassign-phone"),
    pytest.param("acc.phone: str = x\n", "acc.phone", id="annassign-phone"),
]


@pytest.mark.parametrize(("source", "subject"), ASSIGNMENT_CASES)
def test_an_assignment_to_a_phone_attribute_is_a_write(source, subject):
    offences = phone_write_offences(source, "app/x.py")

    assert offences == [f"app/x.py:1 — {KIND_ASSIGNMENT} — {subject}"], (
        f"присваивание `{subject}` гейт не нашёл: {offences}"
    )


KEYWORD_CASES = [
    pytest.param(
        "stmt = update(MessengerAccount).where(MessengerAccount.id == 1).values(phone=x)\n",
        ["values(phone=…)"],
        id="update-values-phone",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values(phone_is_manual=True)\n",
        ["values(phone_is_manual=…)"],
        id="insert-values-phone-is-manual",
    ),
    pytest.param(
        "account = MessengerAccount(user_id=1, phone=x)\n",
        ["MessengerAccount(phone=…)"],
        id="model-constructor-phone",
    ),
    pytest.param(
        "stmt = stmt.values(phone=None, phone_is_manual=False)\n",
        ["values(phone=…)", "values(phone_is_manual=…)"],
        id="values-both-columns",
    ),
]


@pytest.mark.parametrize(("source", "subjects"), KEYWORD_CASES)
def test_a_phone_keyword_in_a_write_call_is_a_write(source, subjects):
    offences = phone_write_offences(source, "app/x.py")

    assert offences == [
        f"app/x.py:1 — {KIND_KEYWORD} — {subject}" for subject in subjects
    ], f"именованный аргумент номера в пишущем вызове гейт не нашёл: {offences}"


def test_no_phone_write_outside_the_writer_in_the_live_tree():
    """Живое дерево: ни одной записи номера вне модуля-писателя.

    Антивакуум в том же правиле: обход видит больше пятидесяти файлов, видит сам
    модуль-писатель, и предикат без исключения находит в нём настоящую запись —
    иначе ноль находок ничего бы не значил.
    """
    sources, offences = tree_offences(PROJECT_ROOT)
    walked = {path.relative_to(PROJECT_ROOT).as_posix() for path in sources}
    writer_source = (PROJECT_ROOT / PHONE_WRITER_MODULE).read_text(encoding="utf-8")
    writer_writes = [
        offence
        for offence in phone_write_offences(writer_source, PHONE_WRITER_MODULE)
        if f" — {KIND_KEYWORD} — " in offence
    ]

    assert len(sources) > 50, (
        f"обход `app/` и `scripts/` дал {len(sources)} файлов — гейт проверяет "
        "почти ничто, и его зелень ничего не значит"
    )
    assert PHONE_WRITER_MODULE in walked, (
        f"обход ({len(sources)} файлов) не видит модуль-писатель {PHONE_WRITER_MODULE}"
    )
    assert len(writer_writes) >= 1, (
        f"предикат без исключения нашёл в модуле-писателе {len(writer_writes)} "
        f"записей второго вида при {len(sources)} обойдённых файлах — он слеп к "
        "настоящей условной записи, и ноль находок на дереве ничего не значит"
    )
    assert offences == [], (
        f"запись номера вне {PHONE_WRITER_MODULE} (обойдено {len(sources)} файлов, "
        f"в модуле-писателе без исключения {len(writer_writes)} записей) — второй "
        "писатель обходит условную запись, и ручной номер снова затирается (D-13):\n"
        + "\n".join(f"  {offence}" for offence in offences)
    )
