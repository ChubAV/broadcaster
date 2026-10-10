"""Гейт приватности PHONE-21: номер аккаунта не попадает в журналы приложения и воркеров.

ЗАЧЕМ. Номер телефона — персональные данные. Всё, что код приложения и воркеров
кладёт в вызов журнала, уходит в stdout контейнера, оттуда в Loki и в Grafana, где
его читают операторы и где оно хранится по сроку хранения журналов, а не по сроку
жизни аккаунта. Фазы 17–20 вводят писателей номера (показ, ручная правка, захват
при подключении, дозаполнение), и у каждого из них под рукой и номер, и журнал.
Решение D-11: в журнал уходит только признак наличия `phone_set=True/False` и
`account_id` — номер не попадает туда НИ В КАКОМ ВИДЕ, даже маской.

ЧТО СЧИТАЕТСЯ ВЫЗОВОМ ЖУРНАЛА (Python, деревья `app/`, `scripts/`, `max_worker/`).
`print(...)` — в контейнере он уходит в тот же stdout, что и журнал; и `X.<метод>(...)`,
где метод — уровень журнала или `bind`/`new` (`LOG_METHODS`), а получатель `X` —
имя `logger`/`log`/`logging`/`_log`/`_logger` (и любое имя, оканчивающееся на
`_log`/`_logger`), атрибут с тем же окончанием (`self.log`), вызов фабрики
`get_logger(...)`/`getLogger(...)` или сам вызов журнала (`logger.bind(...).info`).
`bind` включён НАМЕРЕННО: `logger.bind(phone=x)` кладёт номер в каждую следующую
строку этого журнала. По той же причине вызовом журнала считается любой вызов с
именем `bind_contextvars` или `bound_contextvars`, а также привязки устаревшего
`structlog.threadlocal` — `bind_threadlocal`, `bound_threadlocal`, `tmp_bind`
(`CONTEXT_BINDERS`) — ПРИ ЛЮБОМ получателе: `structlog.contextvars.bind_contextvars(...)`,
голое имя после ввоза, менеджер `with structlog.contextvars.bound_contextvars(...)`,
`with tmp_bind(logger, ...)`; и вызов любого имени, под которым привязка ввезена в
модуль (`from structlog.contextvars import bind_contextvars as bind_ctx` → `bind_ctx(...)`,
`module_log_names`): привязанное значение уходит в каждую следующую строку журнала
запроса, задачи или потока. `unbind_*` и `clear_*` — нет, и под псевдонимом тоже: номера
они не кладут. `parser.error(...)` у argparse, `log.status` у записи `SendLog` и
`logging.getLogger(...).setLevel(...)` вызовом журнала не считаются.

Летопись: до плана 16-09 `structlog.contextvars.bind_contextvars(phone=…)` вызовом
журнала не считался — имени нет в `LOG_METHODS`, а получатель `structlog.contextvars`
не похож на журнал (ревью WR-02); проект при этом зовёт привязку в
`app/middleware.py` и `app/worker/tasks.py` — с ключами без номера, и они теперь
распознаются и не краснят. До плана 16-13 привязка распознавалась только по последнему
имени вызова: псевдоним ввоза и привязки `structlog.threadlocal` уходили мимо гейта
(ревью IN-06, верификация 2026-10-09, advisory; решение владельца О-6 — закрыть в этом
проходе).

ЧТО КРАСНИТ ГЕЙТ, внутри аргументов вызова журнала:
(а) строковая константа, похожая на номер (`PHONE_LIKE_LITERAL`: `+`-форма с
    разделителями и 7…15 цифрами; 11 цифр подряд с ведущей 7/8; русская разбивка
    `8 999 123-45-67` / `8 (999) 123-45-67`), включая постоянные части f-строк;
(б) имя переменной, атрибута, именованного аргумента или строковый ключ словаря,
    содержащие `phone`, — кроме самого признака `phone_set`. Значение `phone_set=`
    не судится, только если оно булевой формы: сравнение с `None` или `bool(...)`.
    `phone_set=account.phone` — сам номер под именем признака — краснит;
(в) вызов `mask_phone(...)` внутри вызова журнала — всегда (D-11), и внутри
    `print(...)` везде, кроме дерева `scripts/` (см. ниже).

ПОЧЕМУ РАЗБОР `ast`, А НЕ ПОИСК ПО ТЕКСТУ. Слово `phone` законно живёт в тексте
сообщений (`logger.info("max_phone_required")`), в комментариях и в коде вне
журнала (`state.phone = phone` у воркера MAX). Поиск по тексту краснел бы на них, и
следующий автор ослабил бы гейт; синтаксическое дерево отличает имя от строки и
аргумент журнала от присваивания рядом.

ПОЧЕМУ МАСКА РАЗРЕШЕНА ТОЛЬКО ВЫВОДУ СКРИПТА (D-10 против D-11). Маска
`+7 *** ***-**-67` нужна человеку, который глазами различает аккаунты в выводе
скрипта дозаполнения Фазы 20, — поэтому аргументы `mask_phone(...)` внутри `print`
под `scripts/` не судятся. В `app/` и `max_worker/` тот же `print` уходит в журнал
контейнера, и маска там — нарушение D-11, как и в любом вызове журнала.

АНТИВАКУУМ. Подложенная строка с номером в синтетическом дереве находится ТЕМ ЖЕ
обходом, что и живое дерево (`python_sources(root)`), а правило по живому дереву
печатает число файлов и распознанных вызовов журнала по каждому дереву и требует,
чтобы оба были больше нуля: обход пустого множества был бы зелёным всегда.

JS-ПОЛОВИНА (`wa_worker/`, без `node_modules` на любой глубине). JS-парсера в
окружении нет, поэтому разбор — собственный токенизатор `_lex_js`: комментарии,
строки и литералы регулярных выражений убираются из «кода», а выражения `${…}`
шаблонных строк остаются кодом (Pitfall 6). Вызов журнала —
`log`/`console`/`logger`/`baileysLogger` `.trace|debug|info|warn|error|fatal|log|child(`
вне комментариев; аргументы — до парной скобки. Краснят (а) литерал, похожий на
номер, в текстах строк; (б) идентификатор кода аргументов, содержащий `phone`, кроме
`phone_set`/`phoneSet`, чьё значение булевой формы (`Boolean(…)`, `!!…`, сравнение с
`null`/`undefined`); (в) носители JID с номером аккаунта — `sock.user` и `creds.me`
(в том числе `state.creds.me`), где имени `phone` нет вовсе.

РЕЕСТР ИСКЛЮЧЕНИЙ `PHONE_LOG_EXCEPTIONS` — ключ «`<путь>::<функция-владелец>`» и
причина, только для Python; потолок `PHONE_LOG_EXCEPTIONS_CEILING = 0`. Исключения
для JS гейт не принимает: их появление потребует правки самого гейта.

СКВОЗНОЙ ГЕЙТ: называть поимённо в каждом плане фаз 17–20
(`uv run pytest tests/test_phone_privacy_gate.py -q`) — исполнители не гоняют полную
суиту, а этот гейт читает чужие исходники: писатель номера Фаз 17–20, положивший его
в журнал, иначе узнает об этом только на сорокаминутном прогоне после слияния.

ГРАНИЦА СРЕДСТВА, НАЗВАННАЯ ПРЯМО (чего гейт НЕ видит):
* журналы сторонних библиотек — Baileys/pino на уровне `warn` (`baileysLogger`
  внутри Baileys), pymax, Telethon: гейт читает только наши исходники;
* номер аккаунта MAX в переменной окружения `PHONE` контейнера (виден в
  `docker inspect`) и в файле `phone.txt` тома сессии (`max_worker/main.py:296-305`,
  `app/services/max_container_manager.py:59-60`) — это не журнал; отложено
  (CONTEXT §Deferred, кандидат в бэклог);
* значение, пришедшее в журнал без имени `phone` и без носителя
  (`logger.info("x", value=v)`, где `v` — номер), — вне охвата правила имён;
* `wa_bridge/` — наследие вне D-09, под гейт не входит.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Деревья D-09: всё, что пишет журналы приложения и воркеров.
GATE_TREES = ("app", "scripts", "wa_worker", "max_worker")

# Python-половина гейта; `wa_worker/` — JS-половина.
PYTHON_TREES = ("app", "scripts", "max_worker")
JS_TREES = ("wa_worker",)
JS_SUFFIXES = (".js", ".mjs", ".cjs")

# Реестр исключений: "<путь>::<имя функции>" (функция-владелец вызова журнала или
# `<module>`) → причина. Исключения принимаются только для Python; для JS гейт их не
# принимает вовсе. Пустота — норма.
PHONE_LOG_EXCEPTIONS: dict[str, str] = {}

# Подъём потолка — решение владельца, а не исполнителя (D-17).
PHONE_LOG_EXCEPTIONS_CEILING = 0

# Каталоги, в которые обход не спускается: сторонний код и байткод. `node_modules`
# в рабочей копии воркера — тысячи чужих файлов, и их журналы — граница гейта.
SKIPPED_DIR_NAMES = frozenset({"node_modules", "__pycache__"})

LOG_METHODS = frozenset(
    {
        "debug",
        "info",
        "warning",
        "warn",
        "error",
        "exception",
        "critical",
        "fatal",
        "msg",
        "log",
        # `bind` и `new` — НАМЕРЕННО: привязанное значение уходит во все строки.
        "bind",
        "new",
    }
)

# Привязка к контексту structlog: значение уходит в КАЖДУЮ следующую строку журнала
# запроса или задачи — тот же довод, по которому в `LOG_METHODS` стоит `bind`. Судится
# по имени при любом получателе (`structlog.contextvars.…` или голое имя после ввоза):
# получатель `structlog.contextvars` на журнал не похож (ревью WR-02).
# `unbind_contextvars` / `clear_contextvars` номера не кладут и вызовом журнала не считаются.
# Устаревший `structlog.threadlocal` structlog 25.5.0 по-прежнему поставляет, и его
# привязки `bind_threadlocal` / `bound_threadlocal` / `tmp_bind` кладут значение в каждую
# следующую строку журнала потока тем же механизмом (ревью IN-06). `unbind_*`, `clear_*`,
# `merge_*`, `get_*`, `wrap_dict`, `as_immutable` значения не привязывают (замер `dir()`
# планирования, 2026-10-09).
CONTEXT_BINDERS = frozenset(
    {"bind_contextvars", "bound_contextvars", "bind_threadlocal", "bound_threadlocal", "tmp_bind"}
)

LOG_RECEIVERS = frozenset({"logger", "log", "logging", "_log", "_logger"})

LOGGER_FACTORIES = frozenset({"get_logger", "getLogger"})

# Имя признака наличия номера, разрешённое в журнале (D-11).
PRESENCE_FLAG_NAMES = frozenset({"phone_set"})

MASK_FUNCTION = "mask_phone"

# Три формы литерала, похожего на номер. У `plus` число цифр внутри совпадения
# дополнительно сверяется с пределами 7…15 (`phone_like`).
PHONE_LIKE_LITERAL = re.compile(
    r"(?P<plus>\+\d[\d\s\-().]{5,}\d)"
    r"|(?P<run>(?<![\d.])[78]\d{10}(?!\d))"
    r"|(?P<grouped>(?<![\d.+])[78][ \-]?\(?\d{3}\)?[ \-]?\d{3}[ \-]?\d{2}[ \-]?\d{2}(?!\d))"
)
PLUS_FORM_DIGITS = (7, 15)


def _walk(base: Path, suffix: str | tuple[str, ...]) -> list[Path]:
    """Файлы с окончанием `suffix` под `base` — ОБХОДОМ, а не перечнем.

    `os.walk` с отсечением каталогов `SKIPPED_DIR_NAMES` вместо `rglob`: тот же обход,
    но в `node_modules` он не спускается вовсе, а не перебирает тысячи чужих файлов,
    чтобы отбросить их после.
    """
    if not base.is_dir():
        return []
    found: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIPPED_DIR_NAMES)
        found.extend(Path(dirpath) / name for name in sorted(filenames) if name.endswith(suffix))
    return found


def python_sources(root: Path) -> dict[str, list[Path]]:
    """Исходники Python каждого дерева `PYTHON_TREES` под `root`.

    Параметр `root` — затем, чтобы тот же обход натравить на синтетическое дерево
    в `tmp_path`: помощник, применимый только к живому дереву, доказать нечем.
    """
    return {tree: _walk(root / tree, ".py") for tree in PYTHON_TREES}


def phone_like(text: str) -> str | None:
    """Первое похожее на номер место в тексте или `None` (правило (а))."""
    low, high = PLUS_FORM_DIGITS
    for match in PHONE_LIKE_LITERAL.finditer(text):
        plus = match.group("plus")
        if plus is not None and not low <= sum(char.isdigit() for char in plus) <= high:
            continue
        return match.group(0)
    return None


def _mentions_phone(name: str) -> bool:
    return "phone" in name.lower() and name not in PRESENCE_FLAG_NAMES


def _callee_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


_LOGGER_NAME = re.compile(r"(?:^|_)(?:log|logger)$")


@dataclass(frozen=True)
class ModuleLogNames:
    """Имена журнала, связанные в одном модуле (IN-06).

    `binders` — псевдонимы ввоза привязок `CONTEXT_BINDERS`
    (`from structlog.contextvars import bind_contextvars as bind_ctx` → `bind_ctx`).
    `receiver_names` / `receiver_attributes` — получатели журнала под именем вне
    `LOG_RECEIVERS` и шаблона `_LOGGER_NAME`. Область видимости — весь модуль.
    """

    binders: frozenset[str]
    receiver_names: frozenset[str]
    receiver_attributes: frozenset[str]


NO_MODULE_LOG_NAMES = ModuleLogNames(frozenset(), frozenset(), frozenset())


def module_log_names(tree: ast.AST) -> ModuleLogNames:
    """Имена журнала, которые модуль `tree` связывает ввозом или присваиванием."""
    binders: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in CONTEXT_BINDERS and alias.asname:
                    binders.add(alias.asname)
    return ModuleLogNames(frozenset(binders), frozenset(), frozenset())


def _is_log_receiver(node: ast.expr) -> bool:
    if isinstance(node, ast.Name):
        return node.id in LOG_RECEIVERS or bool(_LOGGER_NAME.search(node.id))
    if isinstance(node, ast.Attribute):
        return bool(_LOGGER_NAME.search(node.attr))
    if isinstance(node, ast.Call):
        # `structlog.get_logger(__name__).info(...)` и `logger.bind(...).info(...)`.
        return _callee_name(node.func) in LOGGER_FACTORIES or _is_log_method_call(node)
    return False


def _is_log_method_call(call: ast.Call) -> bool:
    func = call.func
    return isinstance(func, ast.Attribute) and func.attr in LOG_METHODS and _is_log_receiver(func.value)


def _is_context_binding(call: ast.Call, names: ModuleLogNames = NO_MODULE_LOG_NAMES) -> bool:
    """Привязка к контексту structlog — по имени вызова при любом получателе или по
    псевдониму, под которым привязка ввезена в модуль."""
    if _callee_name(call.func) in CONTEXT_BINDERS:
        return True
    return isinstance(call.func, ast.Name) and call.func.id in names.binders


def _is_print(call: ast.Call) -> bool:
    return isinstance(call.func, ast.Name) and call.func.id == "print"


def python_log_calls(source: str) -> list[ast.Call]:
    """Вызовы журнала в исходнике Python, в порядке строк."""
    tree = ast.parse(source)
    names = module_log_names(tree)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (_is_print(node) or _is_log_method_call(node) or _is_context_binding(node, names))
    ]
    return sorted(calls, key=lambda call: (call.lineno, call.col_offset))


def _is_presence_flag(value: ast.expr) -> bool:
    """Булева форма признака: сравнение с `None` или `bool(...)` (D-11)."""
    if isinstance(value, ast.Compare) and len(value.ops) == 1:
        if isinstance(value.ops[0], (ast.Is, ast.IsNot, ast.Eq, ast.NotEq)):
            sides = (value.left, *value.comparators)
            return any(isinstance(side, ast.Constant) and side.value is None for side in sides)
        return False
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "bool"
        and len(value.args) == 1
        and not value.keywords
    )


def _judge_arguments(call: ast.Call, *, mask_for_a_reader: bool) -> list[tuple[int, str, str]]:
    """Находки (строка, вид, предмет) во всём поддереве аргументов вызова журнала."""
    found: list[tuple[int, str, str]] = []
    stack: list[ast.AST] = [*call.args, *call.keywords]
    while stack:
        node = stack.pop()
        if isinstance(node, ast.keyword):
            if node.arg in PRESENCE_FLAG_NAMES and _is_presence_flag(node.value):
                continue
            if node.arg is not None and _mentions_phone(node.arg):
                found.append((node.lineno, "имя", f"{node.arg}="))
            stack.append(node.value)
            continue
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    if key.value in PRESENCE_FLAG_NAMES and _is_presence_flag(value):
                        continue
                    if _mentions_phone(key.value):
                        found.append((key.lineno, "ключ", repr(key.value)))
                if key is not None:
                    stack.append(key)
                stack.append(value)
            continue
        if isinstance(node, ast.Call) and _callee_name(node.func) == MASK_FUNCTION:
            if not mask_for_a_reader:
                found.append((node.lineno, "маска", f"{MASK_FUNCTION}(...)"))
            continue
        if isinstance(node, ast.Name) and _mentions_phone(node.id):
            found.append((node.lineno, "имя", node.id))
        elif isinstance(node, ast.Attribute) and _mentions_phone(node.attr):
            found.append((node.lineno, "имя", node.attr))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            literal = phone_like(node.value)
            if literal is not None:
                found.append((node.lineno, "литерал", literal))
        stack.extend(ast.iter_child_nodes(node))
    return found


def _function_ranges(tree: ast.AST) -> list[tuple[int, int, str]]:
    ranges = [
        (node.lineno, node.end_lineno or node.lineno, node.name)
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    return sorted(ranges, key=lambda item: item[1] - item[0])


def _owner(ranges: list[tuple[int, int, str]], line: int) -> str:
    for start, end, name in ranges:
        if start <= line <= end:
            return name
    return "<module>"


def python_log_offences(source: str, path: str) -> list[str]:
    """Находки «`путь:строка` — вид — предмет» в вызовах журнала исходника `path`.

    `path` — путь от корня проекта (`app/x.py`): по нему решается, читает ли вывод
    `print` человек (`scripts/`), и по нему же строится ключ реестра исключений.
    """
    tree = ast.parse(source)
    ranges = _function_ranges(tree)
    in_scripts = PurePosixPath(path).parts[:1] == ("scripts",)
    offences: list[str] = []
    for call in python_log_calls(source):
        if f"{path}::{_owner(ranges, call.lineno)}" in PHONE_LOG_EXCEPTIONS:
            continue
        mask_for_a_reader = in_scripts and _is_print(call)
        for line, kind, subject in sorted(_judge_arguments(call, mask_for_a_reader=mask_for_a_reader)):
            offences.append(f"{path}:{line} — {kind} — {subject} (владелец {_owner(ranges, call.lineno)})")
    return offences


@dataclass(frozen=True)
class TreeScan:
    tree: str
    files: int
    calls: int


def scan_python_trees(root: Path) -> tuple[list[TreeScan], list[str]]:
    """Обход Python-деревьев под `root`: число файлов и вызовов по дереву и находки."""
    scans: list[TreeScan] = []
    offences: list[str] = []
    for tree, paths in python_sources(root).items():
        calls = 0
        for path in paths:
            source = path.read_text(encoding="utf-8")
            calls += len(python_log_calls(source))
            offences.extend(python_log_offences(source, path.relative_to(root).as_posix()))
        scans.append(TreeScan(tree=tree, files=len(paths), calls=calls))
    return scans, offences


def js_sources(root: Path) -> list[Path]:
    """Исходники JS дерева `wa_worker/` под `root`, без `node_modules` на любой глубине."""
    found: list[Path] = []
    for tree in JS_TREES:
        found.extend(_walk(root / tree, JS_SUFFIXES))
    return found


@dataclass(frozen=True)
class JsLogCall:
    line: int
    args_start: int
    code: str
    strings: tuple[tuple[int, str], ...]


JS_LOG_CALL = re.compile(
    r"\b(?:log|console|logger|baileysLogger)\s*\.\s*(?:trace|debug|info|warn|error|fatal|log|child)\s*\("
)
JS_IDENTIFIER = re.compile(r"[A-Za-z_$][\w$]*")
# Носители JID с номером аккаунта: имени `phone` в них нет (правило (в)).
JS_CARRIER = re.compile(r"\bsock\s*\??\.\s*user\b|\bcreds\s*\??\.\s*me\b")
JS_PRESENCE_FLAG_NAMES = frozenset({"phone_set", "phoneSet"})
JS_PRESENCE_KEY = re.compile(r"\b(?:phone_set|phoneSet)\s*:")
_JS_NULLISH_COMPARISON = re.compile(r"^(?:.+?\s*(?:!==?|===?)\s*(?:null|undefined)|(?:null|undefined)\s*(?:!==?|===?)\s*.+)$", re.S)
# После этих слов `/` открывает литерал регулярного выражения, а не деление.
_JS_KEYWORDS_BEFORE_EXPRESSION = frozenset(
    {"return", "typeof", "case", "do", "else", "in", "of", "new", "delete", "void", "throw", "instanceof", "yield", "await"}
)
_JS_OPENERS = {"(": ")", "[": "]", "{": "}"}


@dataclass(frozen=True)
class _JsLexed:
    code: str  # исходник, где комментарии, строки и регулярные выражения заменены пробелами
    strings: tuple[tuple[int, str], ...]  # (смещение, текст) строк и кусков шаблонных строк


def _lex_js(source: str) -> _JsLexed:
    """Код и строки исходника JS без стороннего парсера (в окружении его нет).

    Комментарии `//…`, `/*…*/`, строки `'…'`/`"…"` и литералы регулярных выражений
    в «коде» заменяются пробелами (переводы строк сохраняются — номера строк те же).
    В шаблонной строке `` `…` `` текст уходит в «строки», а выражения `${…}` остаются
    «кодом» на любой глубине вложенности (Pitfall 6: первая версия вырезала их вместе
    со строкой и пропускала ``log.info(`connected ${phone}`)``). Строка-ключ объекта
    (`{ 'phone': x }`) возвращается в код своим содержимым: ключ — имя, а не текст.
    """
    out = list(source)
    strings: list[tuple[int, str]] = []
    keys: list[tuple[int, int]] = []
    length = len(source)

    def blank(start: int, end: int) -> None:
        for index in range(start, min(end, length)):
            if out[index] != "\n":
                out[index] = " "

    regions: list[int] = []  # открытые `${`: глубина фигурных скобок внутри каждого
    in_template = False
    expression_expected = True
    index = 0
    while index < length:
        if in_template:
            start = index
            while index < length and source[index] != "`" and not source.startswith("${", index):
                index += 2 if source[index] == "\\" else 1
            index = min(index, length)
            strings.append((start, source[start:index]))
            blank(start, index)
            if index >= length:
                break
            if source[index] == "`":
                blank(index, index + 1)
                index += 1
                in_template = False
                expression_expected = False
            else:
                blank(index, index + 2)
                index += 2
                regions.append(0)
                in_template = False
                expression_expected = True
            continue
        char = source[index]
        if source.startswith("//", index):
            end = source.find("\n", index)
            end = length if end < 0 else end
            blank(index, end)
            index = end
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            end = length if end < 0 else end + 2
            blank(index, end)
            index = end
            continue
        if char in "'\"":
            end = index + 1
            while end < length and source[end] != char and source[end] != "\n":
                end += 2 if source[end] == "\\" else 1
            end = min(end, length)
            strings.append((index + 1, source[index + 1 : end]))
            keys.append((index, end + 1))
            blank(index, end + 1)
            index = end + 1
            expression_expected = False
            continue
        if char == "`":
            blank(index, index + 1)
            index += 1
            in_template = True
            continue
        if char == "/" and expression_expected:
            end = index + 1
            in_class = False
            while end < length and source[end] != "\n":
                if source[end] == "\\":
                    end += 2
                    continue
                if source[end] == "[":
                    in_class = True
                elif source[end] == "]":
                    in_class = False
                elif source[end] == "/" and not in_class:
                    break
                end += 1
            if end < length and source[end] == "/":
                end += 1
                while end < length and source[end].isalpha():
                    end += 1
                blank(index, end)
                index = end
                expression_expected = False
                continue
        if char == "{" and regions:
            regions[-1] += 1
        elif char == "}" and regions:
            if regions[-1] == 0:
                regions.pop()
                blank(index, index + 1)
                index += 1
                in_template = True
                continue
            regions[-1] -= 1
        if char.isalpha() or char in "_$":
            word = JS_IDENTIFIER.match(source, index)
            assert word is not None
            index = word.end()
            expression_expected = word.group(0) in _JS_KEYWORDS_BEFORE_EXPRESSION
            continue
        if char.isdigit() or char in ")]":
            expression_expected = False
        elif not char.isspace():
            expression_expected = True
        index += 1

    code = "".join(out)
    for start, end in keys:
        text = source[start + 1 : end - 1]
        rest = code[end:].lstrip(" \t")
        if JS_IDENTIFIER.fullmatch(text) and rest.startswith(":"):
            code = code[: start + 1] + text + code[end - 1 :]
    return _JsLexed(code=code, strings=tuple(strings))


def _matching_close(code: str, open_index: int) -> int:
    """Индекс парной закрывающей скобки (по балансу `(`/`[`/`{`) или конец текста."""
    depth = 0
    for index in range(open_index, len(code)):
        char = code[index]
        if char in _JS_OPENERS:
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth == 0:
                return index
    return len(code)


def js_log_calls(source: str) -> list[JsLogCall]:
    """Вызовы журнала в исходнике JS: строка, код аргументов, тексты строк."""
    lexed = _lex_js(source)
    calls: list[JsLogCall] = []
    for match in JS_LOG_CALL.finditer(lexed.code):
        open_index = match.end() - 1
        close_index = _matching_close(lexed.code, open_index)
        calls.append(
            JsLogCall(
                line=source.count("\n", 0, match.start()) + 1,
                args_start=open_index + 1,
                code=lexed.code[open_index + 1 : close_index],
                strings=tuple(
                    (offset, text) for offset, text in lexed.strings if open_index < offset < close_index
                ),
            )
        )
    return calls


def _js_presence_flag(value: str) -> bool:
    """Булева форма признака: `Boolean(…)`, `!!…`, сравнение с `null`/`undefined`."""
    value = value.strip()
    if not value or "?" in value or "||" in value or "&&" in value:
        return False
    if value.startswith("Boolean"):
        open_index = value.find("(")
        return (
            open_index >= 0
            and not value[len("Boolean") : open_index].strip()
            and _matching_close(value, open_index) == len(value) - 1
        )
    return value.startswith("!!") or bool(_JS_NULLISH_COMPARISON.match(value))


def _blank_presence_values(code: str) -> str:
    """Значение `phone_set:`/`phoneSet:` булевой формы не судится; прочее — судится."""
    for key in reversed(list(JS_PRESENCE_KEY.finditer(code))):
        start = key.end()
        depth = 0
        end = start
        while end < len(code):
            char = code[end]
            if char in _JS_OPENERS:
                depth += 1
            elif char in ")]}":
                if depth == 0:
                    break
                depth -= 1
            elif char == "," and depth == 0:
                break
            end += 1
        if _js_presence_flag(code[start:end]):
            code = code[:start] + re.sub(r"[^\n]", " ", code[start:end]) + code[end:]
    return code


def js_log_offences(source: str, path: str) -> list[str]:
    """Находки «`путь:строка` — вид — предмет» в вызовах журнала JS исходника `path`.

    Исключений JS гейт не принимает: реестр `PHONE_LOG_EXCEPTIONS` судит только
    Python, и появление законного номера в журнале воркера потребует правки гейта.
    """

    def line_of(offset: int) -> int:
        return source.count("\n", 0, offset) + 1

    offences: list[str] = []
    for call in js_log_calls(source):
        code = _blank_presence_values(call.code)
        found: list[tuple[int, str, str]] = []
        for word in JS_IDENTIFIER.finditer(code):
            name = word.group(0)
            if "phone" in name.lower() and name not in JS_PRESENCE_FLAG_NAMES:
                found.append((line_of(call.args_start + word.start()), "имя", name))
        for carrier in JS_CARRIER.finditer(code):
            subject = re.sub(r"[\s?]", "", carrier.group(0))
            found.append((line_of(call.args_start + carrier.start()), "носитель", subject))
        for offset, text in call.strings:
            literal = phone_like(text)
            if literal is not None:
                found.append((line_of(offset), "литерал", literal))
        offences.extend(f"{path}:{line} — {kind} — {subject}" for line, kind, subject in sorted(found))
    return offences


def scan_js_trees(root: Path) -> tuple[list[TreeScan], list[str]]:
    """Обход JS-дерева под `root`: число файлов и вызовов и находки."""
    scans: list[TreeScan] = []
    offences: list[str] = []
    paths = js_sources(root)
    for tree in JS_TREES:
        calls = 0
        files = [path for path in paths if path.relative_to(root).parts[0] == tree]
        for path in files:
            source = path.read_text(encoding="utf-8")
            calls += len(js_log_calls(source))
            offences.extend(js_log_offences(source, path.relative_to(root).as_posix()))
        scans.append(TreeScan(tree=tree, files=len(files), calls=calls))
    return scans, offences


def scan_gate(root: Path) -> tuple[list[TreeScan], list[str]]:
    """Обе половины гейта под `root` — тот же помощник для живого и синтетического дерева."""
    python_scans, python_offences = scan_python_trees(root)
    js_scans, js_offences = scan_js_trees(root)
    return python_scans + js_scans, python_offences + js_offences


def _ceiling_offence(registry: Mapping[str, str], ceiling: int) -> str | None:
    """`None`, если реестр исключений не вырос выше потолка; иначе текст нарушения."""
    if len(registry) <= ceiling:
        return None
    return (
        f"реестр исключений гейта приватности вырос до {len(registry)} при потолке {ceiling}: "
        "номер в журнале исправляется, а не разрешается; подъём потолка — решение "
        "владельца, а не исполнителя (D-17)"
    )


def _render(scans: list[TreeScan]) -> str:
    return ", ".join(f"{scan.tree}: файлов {scan.files}, вызовов {scan.calls}" for scan in scans)


# --- Сквозной срез -------------------------------------------------------------


def test_a_planted_number_line_in_a_synthetic_tree_reddens_the_gate(tmp_path):
    """ТРАСЕР: строка журнала с номером в синтетическом `app/` находится тем же обходом."""
    planted = tmp_path / "app" / "planted.py"
    planted.parent.mkdir(parents=True)
    planted.write_text(
        "import structlog\n"
        "\n"
        "logger = structlog.get_logger(__name__)\n"
        "\n"
        "\n"
        "def connected(account):\n"
        '    logger.info("account_connected %s", account.phone)\n',
        encoding="utf-8",
    )

    assert planted in python_sources(tmp_path)["app"], (
        "обход синтетического дерева не нашёл подложенный файл — множество "
        "выписано перечнем, и новый модуль под гейт не попадёт"
    )
    scans, offences = scan_python_trees(tmp_path)

    assert offences, (
        "подложенная строка с номером не найдена: гейт обошёл синтетическое дерево "
        f"({_render(scans)}) и промолчал о `account.phone` в `logger.info`"
    )
    assert any(
        offence.startswith("app/planted.py:7 ") and "phone" in offence for offence in offences
    ), f"находка не называет файл, строку и имя: {offences}"


def test_a_planted_context_binding_in_app_reddens_the_gate(tmp_path):
    """WR-02: номер, привязанный к контексту structlog, уходит в каждую следующую строку.

    `structlog.contextvars.bind_contextvars(phone=…)` — тот же довод, что у `bind`:
    получатель `structlog.contextvars` на журнал не похож, поэтому вызов судится по
    имени. Подложенный файл находится тем же обходом, что и живое дерево.
    """
    planted = tmp_path / "app" / "planted_binding.py"
    planted.parent.mkdir(parents=True)
    planted.write_text(
        "import structlog\n"
        "\n"
        "\n"
        "def bind_account(account):\n"
        "    account_id = account.id\n"
        "    structlog.contextvars.bind_contextvars(phone=account.phone)\n",
        encoding="utf-8",
    )

    assert python_sources(tmp_path)["app"] == [planted], (
        "обход синтетического дерева `app` не нашёл ровно подложенный файл"
    )
    scans, offences = scan_python_trees(tmp_path)

    assert any(
        offence.startswith("app/planted_binding.py:6 — имя — phone=") for offence in offences
    ), (
        "привязка номера к контексту structlog не найдена: гейт обошёл синтетическое "
        f"дерево ({_render(scans)}) и промолчал о `bind_contextvars(phone=…)`: {offences}"
    )


def test_a_planted_aliased_binding_in_app_reddens_the_gate(tmp_path):
    """IN-06 (О-6): привязка, ввезённая под псевдонимом, — та же привязка.

    `from structlog.contextvars import bind_contextvars as bind_ctx` прячет имя
    `bind_contextvars` от распознавания по последнему имени вызова, а номер всё так же
    уходит в каждую следующую строку журнала. Подложенный файл находится тем же
    обходом `python_sources(root)`, что и живое дерево.
    """
    planted = tmp_path / "app" / "planted_alias.py"
    planted.parent.mkdir(parents=True)
    planted.write_text(
        "from structlog.contextvars import bind_contextvars as bind_ctx\n"
        "\n"
        "\n"
        "def bind_account(account):\n"
        "    bind_ctx(phone=account.phone)\n",
        encoding="utf-8",
    )

    assert python_sources(tmp_path)["app"] == [planted], (
        "обход синтетического дерева `app` не нашёл ровно подложенный файл"
    )
    scans, offences = scan_python_trees(tmp_path)

    assert any(
        offence.startswith("app/planted_alias.py:5 — имя — phone=") for offence in offences
    ), (
        "привязка номера под псевдонимом ввоза не найдена: гейт обошёл синтетическое "
        f"дерево ({_render(scans)}) и промолчал о `bind_ctx(phone=…)`: {offences}"
    )


# --- Отрицательные контроли: каждый краснит чистую функцию ----------------------

NEGATIVE_CONTROLS = [
    pytest.param("app/x.py", 'logger.info("x %s", account.phone)\n', "phone", id="positional-attribute"),
    pytest.param("app/x.py", 'log.warning("x", phone)\n', "phone", id="positional-name-log-warning"),
    pytest.param(
        "app/x.py",
        "class W:\n    def f(self, phone_number):\n        self.log.error(\"x %s\", phone_number)\n",
        "phone_number",
        id="self-log-phone-number",
    ),
    pytest.param("app/x.py", 'logger.info(f"connected {account.phone}")\n', "phone", id="fstring-attribute"),
    pytest.param("app/x.py", 'logger.info("connected", phone=value)\n', "phone=", id="keyword-phone"),
    pytest.param("app/x.py", "logger.bind(phone=value)\n", "phone=", id="bind-keyword-phone"),
    pytest.param(
        "app/x.py", "structlog.get_logger().bind(phone=value)\n", "phone=", id="structlog-get-logger-bind"
    ),
    pytest.param("app/x.py", 'logger.info("x", extra={"phone": value})\n', "'phone'", id="extra-dict-key"),
    pytest.param("app/x.py", 'logger.info("+7 999 123-45-67")\n', "+7 999 123-45-67", id="literal-plus-spaced"),
    pytest.param("app/x.py", 'logger.info("+79991234567")\n', "+79991234567", id="literal-plus-compact"),
    pytest.param("app/x.py", 'logger.info("79991234567")\n', "79991234567", id="literal-eleven-digits"),
    pytest.param("app/x.py", 'logger.info("8 999 123-45-67")\n', "8 999 123-45-67", id="literal-russian-spaced"),
    pytest.param(
        "app/x.py", 'logger.info("8 (999) 123-45-67")\n', "8 (999) 123-45-67", id="literal-russian-parens"
    ),
    pytest.param(
        "app/x.py", 'logger.info("x", phone_set=account.phone)\n', "phone", id="phone-set-carrying-the-number"
    ),
    pytest.param("app/x.py", 'logger.info("x", who=mask_phone(phone))\n', "mask_phone", id="mask-in-log-call"),
    pytest.param("app/x.py", "print(account.phone)\n", "phone", id="print-number-in-app"),
    pytest.param("app/x.py", "print(mask_phone(phone))\n", "mask_phone", id="print-mask-in-app"),
    pytest.param(
        "max_worker/x.py", "print(mask_phone(phone))\n", "mask_phone", id="print-mask-in-max-worker"
    ),
    pytest.param("scripts/x.py", "print(account.phone)\n", "phone", id="print-unmasked-number-in-scripts"),
    pytest.param(
        "app/x.py",
        "structlog.contextvars.bind_contextvars(phone=account.phone)\n",
        "phone=",
        id="structlog-bind-contextvars-phone",
    ),
    pytest.param("app/x.py", "bind_contextvars(phone=value)\n", "phone=", id="bare-bind-contextvars-phone"),
    pytest.param(
        "app/x.py",
        "with structlog.contextvars.bound_contextvars(phone=value):\n    pass\n",
        "phone=",
        id="bound-contextvars-context-manager",
    ),
    # IN-06 (О-6): привязка под псевдонимом ввоза и привязки `structlog.threadlocal`.
    pytest.param(
        "app/x.py",
        "from structlog.contextvars import bind_contextvars as bind_ctx\n\nbind_ctx(phone=account.phone)\n",
        "phone=",
        id="aliased-import-bind-contextvars",
    ),
    pytest.param(
        "app/x.py",
        "from structlog.contextvars import bound_contextvars as bound\n\nwith bound(phone=value):\n    pass\n",
        "phone=",
        id="aliased-import-bound-contextvars",
    ),
    pytest.param(
        "app/x.py", "structlog.threadlocal.bind_threadlocal(phone=account.phone)\n", "phone=", id="threadlocal-bind"
    ),
    pytest.param(
        "app/x.py",
        "with structlog.threadlocal.bound_threadlocal(phone=value):\n    pass\n",
        "phone=",
        id="threadlocal-bound-context-manager",
    ),
    pytest.param(
        "app/x.py", "with tmp_bind(logger, phone=value):\n    pass\n", "phone=", id="tmp-bind-context-manager"
    ),
    pytest.param(
        "app/x.py",
        "from structlog.threadlocal import bind_threadlocal as bind_tl\n\nbind_tl(phone=value)\n",
        "phone=",
        id="aliased-import-bind-threadlocal",
    ),
]


@pytest.mark.parametrize(("path", "source", "subject"), NEGATIVE_CONTROLS)
def test_a_number_handed_to_a_python_log_call_is_found(path, source, subject):
    offences = python_log_offences(source, path)

    assert offences, f"номер в вызове журнала не найден: {source!r} ({path})"
    assert any(subject in offence and offence.startswith(f"{path}:") for offence in offences), (
        f"находка не называет предмет {subject!r}: {offences}"
    )


# --- Положительные контроли: ничего не найдено ---------------------------------

POSITIVE_CONTROLS = [
    pytest.param(
        "app/x.py", 'logger.info("x", phone_set=account.phone is not None)\n', True, id="phone-set-is-not-none"
    ),
    pytest.param("app/x.py", 'logger.info("x", phone_set=bool(account.phone))\n', True, id="phone-set-bool"),
    pytest.param("scripts/x.py", "print(mask_phone(phone))\n", True, id="print-mask-in-scripts"),
    pytest.param("scripts/x.py", 'parser.error("phone required")\n', False, id="argparse-error-is-not-a-log"),
    pytest.param("app/x.py", 'logger.info("max_phone_required")\n', True, id="word-phone-inside-the-message"),
    pytest.param("app/x.py", 'logger.info("2026-10-08 14:54:23")\n', True, id="trap-timestamp"),
    pytest.param("app/x.py", 'logger.info("-1001234567890")\n', True, id="trap-chat-id"),
    pytest.param("app/x.py", 'logger.info("1696771234567")\n', True, id="trap-milliseconds"),
    pytest.param("app/x.py", 'logger.info("120363025246125888@g.us")\n', True, id="trap-group-jid"),
    pytest.param("app/x.py", 'logger.info("+7 *** ***-**-67")\n', True, id="trap-mask-text"),
    pytest.param(
        "app/x.py",
        "async def f(db, log_id):\n    log = await db.get(SendLog, log_id)\n    log.status = 'failed'\n",
        False,
        id="send-log-record-named-log",
    ),
    pytest.param(
        "app/x.py", 'logging.getLogger("x").setLevel(logging.WARNING)\n', False, id="set-level-is-not-a-log"
    ),
    pytest.param(
        "app/x.py",
        "structlog.contextvars.bind_contextvars(\n"
        "    request_id=request_id, method=request.method, path=request.url.path\n"
        ")\n",
        True,
        id="middleware-binding-without-phone",
    ),
    pytest.param(
        "app/x.py", "structlog.contextvars.bind_contextvars(task_id=task_id)\n", True, id="task-binding-without-phone"
    ),
    pytest.param(
        "app/x.py",
        "structlog.contextvars.bind_contextvars(phone_set=account.phone is not None)\n",
        True,
        id="binding-presence-flag",
    ),
    pytest.param(
        "app/x.py", 'structlog.contextvars.unbind_contextvars("task_id")\n', False, id="unbinding-is-not-a-log"
    ),
    # IN-06 (О-6): псевдоним привязки распознан и без номера не краснит; снятие и очистка
    # привязки `structlog.threadlocal` — не вызов журнала, и под псевдонимом тоже.
    pytest.param(
        "app/x.py",
        "from structlog.contextvars import bind_contextvars as bind_ctx\n\nbind_ctx(request_id=request_id)\n",
        True,
        id="aliased-binding-without-phone",
    ),
    pytest.param(
        "app/x.py",
        "from structlog.contextvars import bind_contextvars as bind_ctx\n\n"
        "bind_ctx(phone_set=account.phone is not None)\n",
        True,
        id="aliased-binding-presence-flag",
    ),
    pytest.param(
        "app/x.py", "structlog.threadlocal.clear_threadlocal()\n", False, id="threadlocal-clear-is-not-a-log"
    ),
    pytest.param(
        "app/x.py",
        'from structlog.threadlocal import unbind_threadlocal as unbind_tl\n\nunbind_tl("task_id")\n',
        False,
        id="aliased-threadlocal-unbind-is-not-a-log",
    ),
]


@pytest.mark.parametrize(("path", "source", "is_log_call"), POSITIVE_CONTROLS)
def test_a_recommended_form_does_not_redden_the_python_half(path, source, is_log_call):
    calls = python_log_calls(source)

    assert bool(calls) is is_log_call, (
        f"распознаватель {'не увидел' if is_log_call else 'принял за журнал'} вызов: {source!r}"
    )
    assert python_log_offences(source, path) == [], f"ложное срабатывание на {source!r} ({path})"


# --- Живое дерево ----------------------------------------------------------------


def test_no_number_reaches_a_python_log_call_in_the_live_trees():
    """Ноль находок в `app/`, `scripts/`, `max_worker/` при ненулевом обходе каждого."""
    scans, offences = scan_python_trees(PROJECT_ROOT)
    summary = _render(scans)
    print(f"Python-половина гейта приватности: {summary}; находок {len(offences)}")

    assert [scan.tree for scan in scans] == list(PYTHON_TREES), summary
    for scan in scans:
        assert scan.files > 0 and scan.calls > 0, (
            f"дерево `{scan.tree}` обойдено вакуумом ({summary}): гейт проверяет ничто"
        )
    assert offences == [], (
        f"номер уходит в журнал ({summary}):\n" + "\n".join(f"  {offence}" for offence in offences)
    )


# --- JS-половина: `wa_worker/` -----------------------------------------------------


def test_a_template_string_carrying_a_number_reddens_the_js_half():
    """Pitfall 6: выражение `${…}` шаблонной строки — код, а не текст сообщения."""
    source = "log.info(`connected ${phone}`);\n"

    offences = js_log_offences(source, "wa_worker/index.js")

    assert offences, (
        "шаблонная строка с номером не найдена: `${phone}` внутри "
        f"``log.info(`connected ${{phone}}`)`` ушёл в текст, а не в код ({source!r})"
    )
    assert any(
        offence.startswith("wa_worker/index.js:1 ") and "phone" in offence for offence in offences
    ), f"находка не называет файл, строку и имя: {offences}"


JS_NEGATIVE_CONTROLS = [
    pytest.param("log.info({ phone }, 'connected');\n", 1, "phone", id="object-shorthand"),
    pytest.param("log.info('connected ' + phone);\n", 1, "phone", id="string-concatenation"),
    pytest.param("log.info('connected',\n    phone);\n", 2, "phone", id="multiline-second-line"),
    pytest.param("console.log(`me ${sock.user.id}`);\n", 1, "sock.user", id="carrier-sock-user-in-template"),
    pytest.param("log.info({ me: creds.me });\n", 1, "creds.me", id="carrier-creds-me"),
    pytest.param("log.info({ me: state.creds.me });\n", 1, "creds.me", id="carrier-state-creds-me"),
    pytest.param("log.info('+79991234567');\n", 1, "+79991234567", id="literal-plus-compact"),
    pytest.param("console.error('8 999 123-45-67');\n", 1, "8 999 123-45-67", id="literal-russian-console"),
    pytest.param("baileysLogger.warn({ phone });\n", 1, "phone", id="baileys-logger"),
    pytest.param("log.info({ phone_set: phone });\n", 1, "phone", id="phone-set-carrying-the-number"),
    pytest.param("log.info({ 'phone': value });\n", 1, "phone", id="quoted-object-key"),
    pytest.param("const child = log.child({ phone });\n", 1, "phone", id="child-logger-binding"),
]


@pytest.mark.parametrize(("source", "line", "subject"), JS_NEGATIVE_CONTROLS)
def test_a_number_handed_to_a_js_log_call_is_found(source, line, subject):
    offences = js_log_offences(source, "wa_worker/index.js")

    assert offences, f"номер в вызове журнала JS не найден: {source!r}"
    assert any(
        offence.startswith(f"wa_worker/index.js:{line} ") and subject in offence for offence in offences
    ), f"находка не называет строку {line} и предмет {subject!r}: {offences}"


JS_POSITIVE_CONTROLS = [
    pytest.param("// log.info(phone)\n", False, id="commented-out-call"),
    pytest.param("log.info('connected' /* phone */);\n", True, id="block-comment-inside-arguments"),
    pytest.param("log.warn('phone required');\n", True, id="word-phone-inside-the-message"),
    pytest.param("log.info({ phone_set: Boolean(phone) });\n", True, id="phone-set-boolean"),
    pytest.param("log.info({ phoneSet: phone != null });\n", True, id="phone-set-compared-with-null"),
    pytest.param("log.info({ phone_set: !!account.phone });\n", True, id="phone-set-double-negation"),
    pytest.param("const phone = participant.id;\n", False, id="local-phone-outside-a-log-call"),
    pytest.param(
        "log.warn(err.message.replace(/'/g, ''), `groups ${groups.length}`);\n",
        True,
        id="regex-literal-with-a-quote",
    ),
    pytest.param("log.info('2026-10-08 14:54:23', '120363025246125888@g.us');\n", True, id="traps"),
]


@pytest.mark.parametrize(("source", "is_log_call"), JS_POSITIVE_CONTROLS)
def test_a_recommended_form_does_not_redden_the_js_half(source, is_log_call):
    calls = js_log_calls(source)

    assert bool(calls) is is_log_call, (
        f"распознаватель {'не увидел' if is_log_call else 'принял за журнал'} вызов: {source!r}"
    )
    assert js_log_offences(source, "wa_worker/index.js") == [], f"ложное срабатывание на {source!r}"


def test_the_js_walk_skips_node_modules_and_finds_the_planted_file(tmp_path):
    """Сторонний код в `node_modules` — граница гейта; подложенный свой файл — нет."""
    planted = tmp_path / "wa_worker" / "index.js"
    vendored = tmp_path / "wa_worker" / "node_modules" / "x" / "index.js"
    vendored.parent.mkdir(parents=True)
    planted.write_text("log.info({ phone });\n", encoding="utf-8")
    vendored.write_text("log.info({ phone });\n", encoding="utf-8")

    sources = js_sources(tmp_path)
    scans, offences = scan_js_trees(tmp_path)

    assert planted in sources, "обход не нашёл подложенный `wa_worker/index.js`"
    assert vendored not in sources, "обход спустился в `node_modules` — чужой код под гейтом"
    assert len(offences) == 1 and offences[0].startswith("wa_worker/index.js:1 "), (
        f"подложенная строка не найдена или найдена в `node_modules`: {offences} ({_render(scans)})"
    )


PLANTED_LINES = {
    "app": ("app/planted.py", 'logger.info("connected", phone=account.phone)\n'),
    "scripts": ("scripts/planted.py", "print(account.phone)\n"),
    "max_worker": ("max_worker/planted.py", 'log.info("session_started %s", state.phone)\n'),
    "wa_worker": ("wa_worker/planted.js", "log.info(`connected ${state.phone}`);\n"),
}


@pytest.mark.parametrize("tree", GATE_TREES)
def test_a_planted_number_line_is_found_in_every_gate_tree(tmp_path, tree):
    """Критерий 5: подложенная строка находится в КАЖДОМ из четырёх деревьев D-09."""
    relative, line = PLANTED_LINES[tree]
    planted = tmp_path / relative
    planted.parent.mkdir(parents=True)
    planted.write_text(line, encoding="utf-8")

    scans, offences = scan_gate(tmp_path)

    assert any(offence.startswith(f"{relative}:1 ") for offence in offences), (
        f"подложенная строка в `{tree}/` не найдена ({_render(scans)}): {offences}"
    )


def test_no_number_reaches_a_js_log_call_in_the_live_tree():
    """Ноль находок в `wa_worker/` без `node_modules` при ненулевом обходе."""
    scans, offences = scan_js_trees(PROJECT_ROOT)
    summary = _render(scans)
    print(f"JS-половина гейта приватности: {summary}; находок {len(offences)}")

    for scan in scans:
        assert scan.files > 0 and scan.calls > 0, (
            f"дерево `{scan.tree}` обойдено вакуумом ({summary}): гейт проверяет ничто"
        )
    assert offences == [], (
        f"номер уходит в журнал воркера ({summary}):\n" + "\n".join(f"  {offence}" for offence in offences)
    )


# --- Реестр исключений и охват --------------------------------------------------


def test_the_exception_registry_stays_under_its_ceiling():
    """Реестр не растёт выше потолка; каждая запись — существующий файл и причина."""
    assert _ceiling_offence(PHONE_LOG_EXCEPTIONS, PHONE_LOG_EXCEPTIONS_CEILING) is None, _ceiling_offence(
        PHONE_LOG_EXCEPTIONS, PHONE_LOG_EXCEPTIONS_CEILING
    )
    for key, reason in PHONE_LOG_EXCEPTIONS.items():
        path, separator, owner = key.partition("::")
        assert separator and owner, f"ключ реестра {key!r} не в форме «путь::функция»"
        assert reason.strip(), f"у исключения {key!r} нет причины"
        assert (PROJECT_ROOT / path).is_file(), f"исключение {key!r} называет несуществующий файл"

    synthetic = {"app/services/phone.py::<module>": "синтетическая запись контроля"}
    assert _ceiling_offence(synthetic, 0) is not None, (
        "реестр из одной записи при потолке 0 прошёл мимо гейта — потолок перестал держать"
    )
    assert _ceiling_offence({}, 0) is None, "пустой реестр при потолке 0 назван нарушением"


def test_a_registered_exception_silences_only_its_own_function(monkeypatch):
    """Ключ реестра — функция-владелец: соседняя функция того же файла судится как прежде."""
    source = (
        "def allowed(phone):\n"
        '    logger.info("x", phone=phone)\n'
        "\n"
        "\n"
        "def other(phone):\n"
        '    logger.info("x", phone=phone)\n'
    )
    monkeypatch.setitem(PHONE_LOG_EXCEPTIONS, "app/x.py::allowed", "синтетическая причина контроля")

    offences = python_log_offences(source, "app/x.py")

    assert offences and all(offence.startswith("app/x.py:6 ") for offence in offences), (
        f"исключение не сработало или погасило соседнюю функцию: {offences}"
    )


def test_every_gate_tree_is_walked():
    """D-09: две половины гейта вместе обходят ровно `GATE_TREES`."""
    walked = {tree for tree, paths in python_sources(PROJECT_ROOT).items() if paths}
    walked |= {path.relative_to(PROJECT_ROOT).parts[0] for path in js_sources(PROJECT_ROOT)}

    assert walked == set(GATE_TREES), f"обойдены {sorted(walked)}, объявлены {sorted(GATE_TREES)}"
