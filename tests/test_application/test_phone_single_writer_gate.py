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
   `update(...)`, `insert(...)` или `MessengerAccount(...)` — в том числе
   распаковкой литерала: `values(**{"phone": x})`, `MessengerAccount(**{…})`;
3. ключ словаря-аргумента `values(...)` — строка `"phone"` / `"phone_is_manual"`
   или атрибут `MessengerAccount.phone` (и словари внутри списка — многострочная
   вставка); отображение — `{…}` или вызов `dict(phone=…)`;
4. `setattr(obj, "phone", …)` / `set_committed_value(obj, "phone_is_manual", …)` —
   запись атрибута по имени в обход присваивания;
5. сырой SQL в строковой константе, НЕ являющейся докстрингом: `UPDATE … SET …
   phone… =` (присваивание в `SET` до `WHERE`) либо `INSERT INTO messenger_accounts`.
   Голое слово `phone_is_manual` в строке не судится — на нём покраснела бы
   константа условия CHECK модели (`MANUAL_REQUIRES_PHONE`).
6. ключ номера в строках `execute` / `bulk_update_mappings` /
   `bulk_insert_mappings` — словарь или `dict(...)`, поданный позиционно или
   аргументом `params=` / `mappings=`, прямо или внутри списка/кортежа:
   executemany по первичному ключу, естественная форма скрипта дозаполнения
   Фазы 20 (ревью WR-01);
7. ключ номера в литеральном отображении `set_` у `on_conflict_do_update` —
   upsert пишет колонку при конфликте (ревью WR-01).

ЦЕНА СТРОГОСТИ ВТОРОГО ВИДА. Имя `update` берётся по последнему звену вызова,
поэтому `some_dict.update(phone=x)` тоже покраснеет, хотя в колонку не пишет. Это
осознанно: отличить `dict.update` от `sqlalchemy.update` по исходнику без типов
нельзя, а ложное срабатывание здесь снимается переименованием ключа, тогда как
пропущенный второй писатель снимается только потерей ручного номера у пользователя.

ЦЕНА СТРОГОСТИ ШЕСТОГО ВИДА — та же по природе. `execute` судится по ключам строк,
а не по первому аргументу: иначе `stmt = update(MessengerAccount);
session.execute(stmt, rows)` прошёл бы. Поэтому параметр привязки `:phone` в
словаре у `execute` для ЧТЕНИЯ — `execute(text("… WHERE phone = :phone"),
{"phone": p})` — тоже краснеет; снимается переименованием параметра (`:number`).

ГРАНИЦА ПРЕДИКАТА, названная, чтобы её не приняли за покрытие: вне охвата только
значения, собранные во время исполнения, — `values(**fields)` и
`MessengerAccount(**fields)` с ИМЕНЕМ, `execute(stmt, rows)`, где строки собраны в
переменную, `setattr(obj, name, …)` с вычисленным именем, SQL из склейки
переменных. По исходнику они не определимы, и такие формы в коде записи номера
сами по себе повод для ревью. Всё, что видно литералом в исходнике, ловится.

Летопись границы: до плана 16-09 граница называлась теми же словами —
«значение, собранное во время исполнения», — но пять литеральных форм
(executemany по первичному ключу, `dict(...)`, `**{…}`, `set_` при конфликте,
`bulk_*_mappings`) проходили молча, хотя видны в исходнике; это была слепота
предиката, а не граница средства (ревью WR-01, 2026-10-08).

РЕЕСТР ИСКЛЮЧЕНИЙ `PHONE_WRITER_EXCEPTIONS` — поимённо, с причиной, и в нём ровно
модуль-писатель. Второй исключённый модуль есть второй писатель, поэтому
расширение реестра — решение владельца, а не правка ради зелени; состав реестра
закреплён отдельным правилом. Исключение снимает все виды, кроме первого, и
НИКОГДА не снимает вид 1: писатель пишет только операторами UPDATE и зеркалит значение
`set_committed_value`, а присваивание атрибуту сделало бы объект грязным, и ORM
выдала бы на коммите второй, безусловный UPDATE мимо условной записи. Это строже
буквы D-13 и проверяется контролем над исходником писателя с подложенным
присваиванием.
"""

from __future__ import annotations

import ast
import re
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

# Вызовы, пишущие атрибут по имени из второго позиционного аргумента.
NAMED_ATTRIBUTE_WRITERS = frozenset({"setattr", "set_committed_value"})

# Вызовы, чьи позиционные аргументы несут строки для executemany: словарь или
# список словарей по первичному ключу (ревью WR-01). Судятся ключи строк, а не
# первый аргумент: `stmt = update(...); session.execute(stmt, rows)` иначе прошёл бы.
ROW_MAPPING_CALL_NAMES = frozenset(
    {"execute", "bulk_update_mappings", "bulk_insert_mappings"}
)

# Именованные аргументы тех же вызовов, несущие строки: `execute(stmt, params=…)`,
# `bulk_update_mappings(mapper, mappings=…)` — та же литеральная форма, что позиционно.
ROW_MAPPING_KEYWORDS = frozenset({"params", "mappings"})

# Upsert: именованный аргумент `set_` пишет колонки при конфликте (ревью WR-01).
UPSERT_CALL_NAMES = frozenset({"on_conflict_do_update"})

# Пишущий SQL: присваивание колонки номера в `SET` (до `WHERE` — фильтр по номеру
# записью не является) либо любая вставка в таблицу аккаунтов.
RAW_SQL_PHONE_WRITE = re.compile(
    r"\bupdate\b[\s\S]*?\bset\b(?:(?!\bwhere\b)[\s\S])*?\bphone(?:_is_manual)?\b\s*="
    r"|\binsert\s+into\s+messenger_accounts\b",
    re.IGNORECASE,
)

KIND_ASSIGNMENT = "присваивание"
KIND_KEYWORD = "именованный аргумент"
KIND_DICT_KEY = "ключ словаря values"
KIND_SETATTR = "запись атрибута по имени"
KIND_RAW_SQL = "сырой SQL"
KIND_ROW_MAPPING = "ключ словаря строк"
KIND_UPSERT_SET = "set_ при конфликте"

# Реестр исключений: путь → причина. РОВНО ОДНА ЗАПИСЬ; см. шапку модуля.
PHONE_WRITER_EXCEPTIONS: dict[str, str] = {
    PHONE_WRITER_MODULE: (
        "единственный писатель номера (D-12, D-13): условные UPDATE автоисточника, "
        "запись и очистка ручного номера, зеркало set_committed_value"
    ),
}

# Виды, которые исключение реестра НЕ снимает никогда.
NEVER_EXEMPT_KINDS = frozenset({KIND_ASSIGNMENT})


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
    return [_format(path, write) for write in _phone_writes(source, path)]


def judged_offences(source: str, path: str) -> list[str]:
    """Находки, которые гейт судит: предикат плюс исключения реестра.

    В пути из реестра отбрасываются все виды, кроме присваивания; присваивание
    (вид 1) судится везде.
    """
    exempt = path in PHONE_WRITER_EXCEPTIONS
    return [
        _format(path, write)
        for write in _phone_writes(source, path)
        if not exempt or write[2] in NEVER_EXEMPT_KINDS
    ]


def _format(path: str, write: tuple[int, int, str, str]) -> str:
    line, _column, kind, subject = write
    return f"{path}:{line} — {kind} — {subject}"


def _phone_writes(source: str, path: str) -> list[tuple[int, int, str, str]]:
    """Записи номера видов шапки: (строка, столбец, вид, предмет), по порядку в файле."""
    tree = ast.parse(source, filename=path)
    docstrings = _docstring_nodes(tree)
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
                    elif keyword.arg is None:
                        # `values(**{"phone": x})`, `MessengerAccount(**dict(phone=x))`
                        for mapping in _literal_mappings(keyword.value):
                            for key, column in _mapping_phone_keys(mapping):
                                text = _mapping_key_text(key, column)
                                record(key, KIND_KEYWORD, f"{name}(**{text})")
            if name == "values":
                for key, column in _values_dict_keys(node):
                    record(key, KIND_DICT_KEY, f"values({_mapping_key_text(key, column)})")
            if name in ROW_MAPPING_CALL_NAMES:
                arguments = list(node.args) + [
                    keyword.value
                    for keyword in node.keywords
                    if keyword.arg in ROW_MAPPING_KEYWORDS
                ]
                for argument in arguments:
                    rows = isinstance(argument, (ast.List, ast.Tuple))
                    for mapping in _literal_mappings(argument):
                        for key, column in _mapping_phone_keys(mapping):
                            text = _mapping_key_text(key, column)
                            subject = f"{name}([{text}])" if rows else f"{name}({text})"
                            record(key, KIND_ROW_MAPPING, subject)
            if name in UPSERT_CALL_NAMES:
                for keyword in node.keywords:
                    if keyword.arg != "set_":
                        continue
                    for mapping in _literal_mappings(keyword.value):
                        for key, column in _mapping_phone_keys(mapping):
                            text = _mapping_key_text(key, column)
                            record(key, KIND_UPSERT_SET, f"{name}(set_={text})")
            if name in NAMED_ATTRIBUTE_WRITERS and len(node.args) >= 2:
                attribute = node.args[1]
                if (
                    isinstance(attribute, ast.Constant)
                    and attribute.value in PHONE_COLUMNS
                ):
                    record(node, KIND_SETATTR, f"{name}(…, {attribute.value!r}, …)")
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
            and RAW_SQL_PHONE_WRITE.search(node.value)
        ):
            snippet = " ".join(node.value.split())[:60]
            record(node, KIND_RAW_SQL, f"«{snippet}»")

    return sorted(found)


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Узлы-докстринги модуля, классов и функций: прозу о SQL гейт не судит."""
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                found.add(id(first.value))
    return found


def _values_dict_keys(call: ast.Call) -> list[tuple[ast.AST, str]]:
    """Ключи номера в позиционных отображениях `values(...)`, в том числе в списке.

    Отображение — `{...}` или `dict(...)`; список — многострочная вставка.
    """
    return [
        found
        for argument in call.args
        for mapping in _literal_mappings(argument)
        for found in _mapping_phone_keys(mapping)
    ]


def _literal_mappings(node: ast.expr) -> list[ast.expr]:
    """Литеральные отображения в узле: `{...}`, `dict(...)` и они же в списке/кортеже.

    Переменная, вызов другого имени, генератор — не литерал: такие строки собраны
    во время исполнения и лежат за объявленной границей предиката.
    """
    if isinstance(node, ast.Dict) or _is_dict_call(node):
        return [node]
    if isinstance(node, (ast.List, ast.Tuple)):
        return [
            item
            for item in node.elts
            if isinstance(item, ast.Dict) or _is_dict_call(item)
        ]
    return []


def _is_dict_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "dict"
    )


def _mapping_phone_keys(mapping: ast.expr) -> list[tuple[ast.AST, str]]:
    """Ключи номера в литеральном отображении: (узел для строки находки, колонка).

    У `{...}` — строковая константа или атрибут (`MessengerAccount.phone`) из
    `PHONE_COLUMNS`; у `dict(...)` — именованный аргумент из `PHONE_COLUMNS`.
    """
    found: list[tuple[ast.AST, str]] = []
    if isinstance(mapping, ast.Dict):
        for key in mapping.keys:
            if isinstance(key, ast.Constant) and key.value in PHONE_COLUMNS:
                found.append((key, key.value))
            elif isinstance(key, ast.Attribute) and key.attr in PHONE_COLUMNS:
                found.append((key, key.attr))
    elif _is_dict_call(mapping):
        for keyword in mapping.keywords:
            if keyword.arg in PHONE_COLUMNS:
                found.append((keyword, keyword.arg))
    return found


def _mapping_key_text(key: ast.AST, column: str) -> str:
    """Ключ номера в предмете находки: `{'phone': …}`, `{X.phone: …}`, `dict(phone=…)`."""
    if isinstance(key, ast.keyword):
        return f"dict({column}=…)"
    if isinstance(key, ast.Attribute):
        return f"{{{ast.unparse(key)}: …}}"
    return f"{{{column!r}: …}}"


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
    """Обход дерева и судимые находки по каждому файлу, писатель включительно."""
    sources = writer_sources(root)
    offences: list[str] = []
    for file in sources:
        relative = file.relative_to(root).as_posix()
        offences.extend(judged_offences(file.read_text(encoding="utf-8"), relative))
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


def test_a_planted_bulk_update_by_primary_key_reddens_the_gate(tmp_path):
    """ТРАСЕР WR-01: executemany по первичному ключу в синтетическом `scripts/`.

    ORM bulk UPDATE списком словарей — естественная форма скрипта дозаполнения
    Фазы 20, то есть ровно тот второй писатель, ради которого гейт существует (D-13).
    Подложенный файл находится тем же обходом, что и живое дерево.
    """
    _plant(
        tmp_path,
        "scripts/backfill_planted.py",
        "async def backfill(session, p):\n"
        '    await session.execute(update(MessengerAccount), [{"id": 1, "phone": p}])\n',
    )

    sources, offences = tree_offences(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in sources] == [
        "scripts/backfill_planted.py"
    ], "обход синтетического дерева не нашёл подложенный файл в `scripts/`"
    found = [
        offence
        for offence in offences
        if offence.startswith(f"scripts/backfill_planted.py:2 — {KIND_ROW_MAPPING} — ")
    ]
    assert found, (
        "executemany по первичному ключу не найден: "
        "`session.execute(update(MessengerAccount), [{'phone': p}])` в "
        f"scripts/backfill_planted.py гейт пропустил: {offences}"
    )
    assert all("execute" in offence and "phone" in offence for offence in found), (
        f"предмет находки не называет вызов `execute` и колонку `phone`: {found}"
    )


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


def test_a_raw_sql_phone_write_reddens_the_gate(tmp_path):
    """Сырой UPDATE в строковой константе синтетического `app/` краснит гейт."""
    _plant(
        tmp_path,
        "app/x.py",
        'SQL = "UPDATE messenger_accounts SET phone = :p WHERE id = :id"\n',
    )

    sources, offences = tree_offences(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in sources] == [
        "app/x.py"
    ], "обход синтетического дерева не нашёл подложенный файл"
    assert any(
        offence.startswith(f"app/x.py:1 — {KIND_RAW_SQL} — ") for offence in offences
    ), f"сырой SQL с номером не найден: {offences}"


DICT_KEY_CASES = [
    pytest.param(
        'stmt = update(MessengerAccount).values({"phone": x})\n',
        "values({'phone': …})",
        id="values-dict-string-key",
    ),
    pytest.param(
        "stmt = update(MessengerAccount).values({MessengerAccount.phone: x})\n",
        "values({MessengerAccount.phone: …})",
        id="values-dict-column-key",
    ),
    pytest.param(
        'stmt = stmt.values({"phone_is_manual": True})\n',
        "values({'phone_is_manual': …})",
        id="values-dict-phone-is-manual",
    ),
]


@pytest.mark.parametrize(("source", "subject"), DICT_KEY_CASES)
def test_a_phone_key_in_a_values_dict_is_a_write(source, subject):
    offences = phone_write_offences(source, "app/x.py")

    assert offences == [f"app/x.py:1 — {KIND_DICT_KEY} — {subject}"], (
        f"ключ номера в словаре `values(...)` гейт не нашёл: {offences}"
    )


SETATTR_CASES = [
    pytest.param(
        'setattr(account, "phone", x)\n',
        "setattr(…, 'phone', …)",
        id="setattr-phone",
    ),
    pytest.param(
        'set_committed_value(account, "phone_is_manual", True)\n',
        "set_committed_value(…, 'phone_is_manual', …)",
        id="set-committed-value-phone-is-manual",
    ),
]


@pytest.mark.parametrize(("source", "subject"), SETATTR_CASES)
def test_a_phone_attribute_written_by_name_is_a_write(source, subject):
    offences = phone_write_offences(source, "app/x.py")

    assert offences == [f"app/x.py:1 — {KIND_SETATTR} — {subject}"], (
        f"запись атрибута номера по имени гейт не нашёл: {offences}"
    )


RAW_SQL_CASES = [
    pytest.param(
        'stmt = text("update messenger_accounts set phone_is_manual = true")\n',
        id="text-update-lowercase",
    ),
    pytest.param(
        "SQL = \"INSERT INTO messenger_accounts (user_id, phone) "
        "VALUES (1, '+79991234567')\"\n",
        id="insert-into-messenger-accounts",
    ),
]


@pytest.mark.parametrize("source", RAW_SQL_CASES)
def test_a_raw_sql_phone_write_in_a_string_constant_is_a_write(source):
    offences = phone_write_offences(source, "app/x.py")

    assert len(offences) == 1 and offences[0].startswith(
        f"app/x.py:1 — {KIND_RAW_SQL} — "
    ), f"сырой SQL с номером в строковой константе гейт не нашёл: {offences}"


def test_an_upsert_set_of_a_phone_column_is_a_write():
    """`set_` у `on_conflict_do_update` пишет колонку при конфликте — это запись (WR-01)."""
    source = (
        "stmt = insert(MessengerAccount).values(user_id=1).on_conflict_do_update("
        'index_elements=["id"], set_={"phone": x})\n'
    )

    offences = phone_write_offences(source, "app/x.py")
    upserts = [offence for offence in offences if f" — {KIND_UPSERT_SET} — " in offence]

    assert upserts, f"set_ при конфликте с номером не найден: {offences}"
    assert len(offences) == 1 and offences[0].startswith(
        f"app/x.py:1 — {KIND_UPSERT_SET} — "
    ), f"upsert дал не ровно одну находку вида «{KIND_UPSERT_SET}»: {offences}"
    assert "on_conflict_do_update" in offences[0] and "phone" in offences[0], (
        f"предмет находки не называет `on_conflict_do_update` и `phone`: {offences}"
    )


# Литеральные формы записи из ревью WR-01: (исходник, вид, имя вызова, колонка).
# Каждая видна в исходнике, а до плана 16-09 проходила гейт молча.
LITERAL_FORM_CASES = [
    pytest.param(
        "async def f(session, p):\n"
        '    await session.execute(update(MessengerAccount), [{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="orm-bulk-update-by-pk",
    ),
    pytest.param(
        "stmt = update(MessengerAccount).values(dict(phone=x))\n",
        KIND_DICT_KEY,
        "values",
        "phone",
        id="values-dict-call",
    ),
    pytest.param(
        'stmt = update(MessengerAccount).values(**{"phone": x})\n',
        KIND_KEYWORD,
        "values",
        "phone",
        id="values-double-star-dict",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values(user_id=1).on_conflict_do_update("
        'index_elements=["id"], set_={"phone": x})\n',
        KIND_UPSERT_SET,
        "on_conflict_do_update",
        "phone",
        id="upsert-set-dict",
    ),
    pytest.param(
        "stmt = insert(MessengerAccount).values(user_id=1).on_conflict_do_update("
        'index_elements=["id"], set_=dict(phone_is_manual=True))\n',
        KIND_UPSERT_SET,
        "on_conflict_do_update",
        "phone_is_manual",
        id="upsert-set-dict-call",
    ),
    pytest.param(
        'session.bulk_update_mappings(MessengerAccount, [{"id": 1, "phone_is_manual": True}])\n',
        KIND_ROW_MAPPING,
        "bulk_update_mappings",
        "phone_is_manual",
        id="bulk-update-mappings",
    ),
    pytest.param(
        "session.bulk_insert_mappings(MessengerAccount, [dict(user_id=1, phone=p)])\n",
        KIND_ROW_MAPPING,
        "bulk_insert_mappings",
        "phone",
        id="bulk-insert-mappings",
    ),
    pytest.param(
        'account = MessengerAccount(**{"phone": x})\n',
        KIND_KEYWORD,
        "MessengerAccount",
        "phone",
        id="model-constructor-double-star",
    ),
    pytest.param(
        "async def f(session, stmt, p):\n"
        '    await session.execute(stmt, params=[{"id": 1, "phone": p}])\n',
        KIND_ROW_MAPPING,
        "execute",
        "phone",
        id="execute-params-keyword",
    ),
]


@pytest.mark.parametrize(("source", "kind", "call", "column"), LITERAL_FORM_CASES)
def test_a_literal_write_form_is_a_write(source, kind, call, column):
    offences = phone_write_offences(source, "app/x.py")

    assert len(offences) == 1, (
        f"литеральная форма записи `{call}(… {column} …)` дала {len(offences)} "
        f"находок вместо одной: {offences}"
    )
    _location, found_kind, subject = offences[0].split(" — ", 2)
    assert found_kind == kind, f"вид находки «{found_kind}», ожидался «{kind}»: {offences}"
    assert call in subject and column in subject, (
        f"предмет находки не называет вызов `{call}` и колонку `{column}`: {offences}"
    )


LEGITIMATE_CASES = [
    pytest.param(
        'return render(request, "x.html", phone=phone)\n', id="render-phone-kwarg"
    ),
    pytest.param(
        "async def f(client, phone):\n    await client.start_session(phone=phone)\n",
        id="start-session-phone-kwarg",
    ),
    pytest.param(
        '_max_step_markup(request, step="phone", phone=phone)\n',
        id="max-step-markup-phone-kwarg",
    ),
    pytest.param(
        "class MessengerAccount(Base):\n"
        "    phone: Mapped[str | None] = mapped_column(String(16), nullable=True)\n"
        "    phone_is_manual: Mapped[bool] = mapped_column(Boolean, default=False)\n",
        id="model-column-declaration",
    ),
    pytest.param(
        'MANUAL_REQUIRES_PHONE = "NOT (phone_is_manual AND phone IS NULL)"\n',
        id="check-condition-constant",
    ),
    pytest.param(
        "def fill(session):\n"
        '    """Пишет одним оператором UPDATE messenger_accounts SET phone = :p."""\n',
        id="docstring-with-update-set-phone",
    ),
    pytest.param(
        '"""Модуль: INSERT INTO messenger_accounts делает мастер."""\n',
        id="module-docstring-with-insert",
    ),
    pytest.param(
        "number = account.phone\n"
        "stmt = select(MessengerAccount).where(MessengerAccount.phone.is_(None))\n",
        id="read-and-filter-by-phone",
    ),
    pytest.param(
        'logger.info("account_connected", phone_set=account.phone is not None)\n',
        id="phone-set-flag-in-log",
    ),
    pytest.param(
        'SQL = "UPDATE groups SET title = :t WHERE phone = :p"\n',
        id="update-filtering-by-phone-in-where",
    ),
    pytest.param(
        'templates.TemplateResponse("accounts/connect_max.html", '
        '{"request": request, "phone": submitted})\n',
        id="templates-response-context-phone",
    ),
    pytest.param(
        "async def f(session):\n"
        "    await session.execute(\n"
        "        select(MessengerAccount).where(MessengerAccount.phone.is_(None))\n"
        "    )\n",
        id="execute-select-filter-by-phone",
    ),
    pytest.param(
        'render(request, "x.html", **{"phone": phone})\n',
        id="render-double-star-phone",
    ),
    pytest.param(
        "stmt = insert(Group).values(title=t).on_conflict_do_update(\n"
        '    index_elements=["id"], set_={"title": t}\n'
        ")\n",
        id="upsert-set-other-columns",
    ),
    pytest.param(
        'session.bulk_update_mappings(Group, [{"id": 1, "title": t}])\n',
        id="bulk-update-mappings-other-columns",
    ),
    pytest.param(
        "async def f(session):\n"
        "    await session.execute(\n"
        '        update(MessengerAccount), [{"id": 1, "status": "active"}]\n'
        "    )\n",
        id="execute-rows-without-phone",
    ),
]


@pytest.mark.parametrize("source", LEGITIMATE_CASES)
def test_a_legitimate_phone_mention_is_not_a_write(source):
    offences = phone_write_offences(source, "app/x.py")

    assert offences == [], (
        f"законное упоминание номера гейт счёл записью — шум снимет гейт: {offences}"
    )


def test_the_walk_leaves_max_worker_alembic_and_tests_outside(tmp_path):
    """`max_worker/`, `alembic/` и `tests/` вне вселенной: их записи не судятся."""
    planted_write = "def f(state):\n    state.phone = '+79991234567'\n"
    _plant(tmp_path, "max_worker/main.py", planted_write)
    _plant(tmp_path, "tests/x.py", planted_write)
    _plant(tmp_path, "alembic/versions/x.py", planted_write)
    _plant(tmp_path, "app/pages/clean.py", 'render(request, "x.html", phone=phone)\n')

    sources, offences = tree_offences(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in sources] == [
        "app/pages/clean.py"
    ], "обход вышел за `app/` и `scripts/` или не нашёл файл вселенной"
    assert offences == [], f"законный вызов в `app/` дал находку: {offences}"


def test_the_exception_registry_names_only_the_writer_module():
    """Реестр — ровно модуль-писатель с причиной; его записи не судятся, кроме присваивания.

    Второй исключённый модуль есть второй писатель: расширение реестра — решение
    владельца, а не правка ради зелени.
    """
    assert list(PHONE_WRITER_EXCEPTIONS) == [PHONE_WRITER_MODULE], (
        f"реестр исключений — не ровно модуль-писатель: {sorted(PHONE_WRITER_EXCEPTIONS)}"
    )
    assert PHONE_WRITER_EXCEPTIONS[PHONE_WRITER_MODULE].strip(), (
        "исключение модуля-писателя записано без причины"
    )
    writer_path = PROJECT_ROOT / PHONE_WRITER_MODULE
    assert writer_path.is_file(), f"исключён несуществующий файл {PHONE_WRITER_MODULE}"

    writer_source = writer_path.read_text(encoding="utf-8")
    raw = phone_write_offences(writer_source, PHONE_WRITER_MODULE)
    raw_kinds = {offence.split(" — ")[1] for offence in raw}

    assert {KIND_KEYWORD, KIND_SETATTR} <= raw_kinds, (
        f"в модуле-писателе предикат без исключения видит виды {sorted(raw_kinds)} — "
        "условный UPDATE и зеркало set_committed_value обязаны быть видны"
    )
    assert judged_offences(writer_source, PHONE_WRITER_MODULE) == [], (
        "записи модуля-писателя, кроме присваивания, судятся, хотя он в реестре"
    )


def test_control_an_assignment_inside_the_writer_module_still_reddens():
    """Присваивание атрибуту номера исключением не покрывается — даже в писателе.

    Писатель пишет только операторами UPDATE и зеркалит `set_committed_value`;
    присваивание сделало бы объект грязным, и ORM выдала бы на коммите второй,
    безусловный UPDATE мимо условной записи.
    """
    sneaked = "    account.phone = '+79990000000'"
    source = (
        (PROJECT_ROOT / PHONE_WRITER_MODULE).read_text(encoding="utf-8")
        + "\n\ndef _sneak(account):\n"
        + sneaked
        + "\n"
    )
    line = source.splitlines().index(sneaked) + 1

    assert judged_offences(source, PHONE_WRITER_MODULE) == [
        f"{PHONE_WRITER_MODULE}:{line} — {KIND_ASSIGNMENT} — account.phone"
    ], "присваивание номера в модуле-писателе прикрыто исключением"
