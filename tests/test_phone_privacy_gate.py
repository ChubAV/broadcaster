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
строку этого журнала. `parser.error(...)` у argparse, `log.status` у записи
`SendLog` и `logging.getLogger(...).setLevel(...)` вызовом журнала не считаются.

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
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Деревья D-09: всё, что пишет журналы приложения и воркеров.
GATE_TREES = ("app", "scripts", "wa_worker", "max_worker")

# Python-половина гейта; `wa_worker/` — JS-половина.
PYTHON_TREES = ("app", "scripts", "max_worker")

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


def _walk(base: Path, suffix: str) -> list[Path]:
    """Файлы с окончанием `suffix` под `base` — ОБХОДОМ, а не перечнем."""
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


def python_log_calls(source: str) -> list[ast.Call]:
    """Вызовы журнала в исходнике Python (RED-заготовка)."""
    return []


def python_log_offences(source: str, path: str) -> list[str]:
    """Находки «`путь:строка` — вид — предмет» в вызовах журнала (RED-заготовка)."""
    return []


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
