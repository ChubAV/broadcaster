"""Сквозной гейт подписи аккаунта: `#` перед идентификатором — только в помощнике (Фаза 17, D-06, D-19).

ЧТО ГЕЙТ ЗАПРЕЩАЕТ. Сборку знака `#` перед идентификатором аккаунта вне помощника
подписи (`components/account_label.html`, `app/services/account_label.py`). Подпись
пользователя — номер, а не `#id`; `#id` печатается только у двойника и в админке, и
печатает его ОДНО место — макрос `account_id_mark`. Шаблон, пропущенный при замене
(критерий 5 ROADMAP), роняет суиту.

КЛАСС, А НЕ НАПИСАНИЕ (урок Фазы 16, О-23). Гейт запрещает конструкцию, а не
перечень её написаний: «13 раундов верификации и 64 плана — распознавание написаний
не сходилось, каждая партия чинила одни формы и открывала другие».

  К1 — строковый литерал выражения, оканчивающийся на `#` (`'#' ~ account.id`,
       `'Акк #' ~ …`, `' #' ~ …`), при любом операторе вокруг (`~`, `+`, `format`,
       `join`): `['"][^'"]*#\\s*['"]`.
"""

import re
from pathlib import Path
from typing import NamedTuple

import pytest

# Вырезание комментариев берётся ИМПОРТОМ, а не второй копией: два разборщика
# одного и того же вырезания разъехались бы молча (тот же довод, что у
# `test_htmx_markup_security.py`).
from tests.test_templates.test_htmx_inventory import _strip_comments

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = PROJECT_ROOT / "app"
TEMPLATES_DIR = APP_ROOT / "templates"


class HashException(NamedTuple):
    """Запись реестра: причина и предмет (то, что обязано стоять за законным `#`)."""

    reason: str
    subject: str


# Реестр исключений адресует ВХОЖДЕНИЕ (`путь#порядковый номер`), а не файл: в
# `history_card.html` рядом стоят идентификатор группы (законно) и прежнее место
# аккаунта; исключение на файл пропустило бы возврат `#` аккаунта (D-19,
# RESEARCH Pitfall 5).
TEMPLATE_HASH_EXCEPTIONS: dict[str, HashException] = {
    "history/detail.html#0": HashException(
        "`#` перед `group_external_id` — идентификатор ГРУППЫ, не аккаунта (D-19)",
        "group_external_id",
    ),
    "history/includes/history_card.html#0": HashException(
        "`#` перед `group_external_id` — идентификатор ГРУППЫ, не аккаунта (D-19)",
        "group_external_id",
    ),
    "components/account_label.html#0": HashException(
        "`account_id_mark` — единственное место печати `#` перед id аккаунта (D-06)",
        "account_id",
    ),
}

# Число исключений шаблонов — ОТДЕЛЬНОЙ литеральной константой (образец
# `MACRO_DEFINITION_SITES_DECLARED`): беззвучно выросшее означает новое место
# печати `#`, о котором никто не решал; упавшее — закрытое исключение.
TEMPLATE_HASH_EXCEPTIONS_DECLARED = 3

# Python-половина (К3). Законных вхождений два; ключ — по вхождению, как и у
# шаблонов, поэтому ВТОРАЯ сборка знака в модуле помощника выходит за реестр.
PYTHON_HASH_EXCEPTIONS: dict[str, HashException] = {
    "app/pages/htmx.py#0": HashException(
        "разделитель фрагмента адреса в `redirect.partition(\"#\")`, а не подпись аккаунта",
        "partition",
    ),
    "app/services/account_label.py#0": HashException(
        "`id_mark` — плоская половина помощника подписи (D-06, D-12)",
        "[id_mark]",
    ),
}
PYTHON_HASH_EXCEPTIONS_DECLARED = 2

# Класс К1: литерал, оканчивающийся на `#`.
STRING_ENDING_IN_HASH = re.compile(r"""['"][^'"]*#\s*['"]""")


def _template_sources() -> dict[str, str]:
    """Все шаблоны проекта: путь относительно `app/templates` → исходник.

    Обход РЕКУРСИВНЫЙ (`rglob`) и по ОТСОРТИРОВАННОМУ списку: плоский обход не
    увидел бы `includes/`, `components/` и `*/partials/`, а порядок делает
    сообщение об отказе воспроизводимым.
    """
    return {
        path.relative_to(TEMPLATES_DIR).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(TEMPLATES_DIR.rglob("*.html"))
    }


# Хвост выражения за литералом: до закрывающей скобки или конца строки. Нужен
# записи реестра — она проверяет, ЧТО стоит за законным `#` (предмет записи).
EXPRESSION_TAIL = re.compile(r"[^)\n]*")


def hash_id_findings(sources: dict[str, str]) -> dict[str, str]:
    """Места сборки `#` в шаблонах: ключ `путь#порядковый номер` → описание.

    Комментарии обоих видов вырезаются ДО счёта: проза комментариев-обоснований
    свободно содержит и `'#' ~ id`, и `#{{` (довод `_strip_comments`). Ключ —
    ПУТЬ ПЛЮС ПОРЯДКОВЫЙ НОМЕР ВХОЖДЕНИЯ, нумерация — по положению в исходнике:
    исключение на файл пропустило бы возврат `#` аккаунта рядом с законным `#`
    группы. Обходчик принимает СЛОВАРЬ, а не читает дерево сам — контроль подаёт
    изменённую копию и не трогает файлов проекта.
    """
    found: dict[str, str] = {}
    for rel, source in sorted(sources.items()):
        body = _strip_comments(source)
        hits: list[tuple[int, str]] = []
        for match in STRING_ENDING_IN_HASH.finditer(body):
            tail = EXPRESSION_TAIL.match(body, match.end())
            fragment = (match.group(0) + (tail.group(0) if tail else "")).strip()
            hits.append((match.start(), f"К1, литерал на `#`: {fragment!r}"))
        for ordinal, (_position, description) in enumerate(sorted(hits)):
            found[f"{rel}#{ordinal}"] = description
    return found


def _python_sources() -> dict[str, str]:
    """Все модули `app/`: путь от корня проекта → исходник.

    Область — РОВНО `app/`: каталог `tests/` в неё не входит (тесты называют
    подложенные строки и законно печатают `#`).
    """
    return {
        path.relative_to(PROJECT_ROOT).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(APP_ROOT.rglob("*.py"))
    }


def python_hash_findings(sources: dict[str, str]) -> dict[str, str]:
    """Места сборки `#` в Python: ключ `путь#порядковый номер` → описание."""
    return {}


def registry_violations(
    findings: dict[str, str], registry: dict[str, HashException]
) -> list[str]:
    """Что в находках не сходится с реестром: лишнее, устаревшее, не тот предмет.

    Три отказа, и каждый назван поимённо: находка вне реестра; запись реестра,
    у которой находки нет (исключение пережило место); запись, за чьим `#` стоит
    не её предмет (на месте группы теперь аккаунт — гейт не должен их путать).
    """
    problems: list[str] = []
    for key, text in sorted(findings.items()):
        entry = registry.get(key)
        if entry is None:
            problems.append(f"{key}: вне реестра: {text}")
        elif entry.subject not in text:
            problems.append(f"{key}: за `#` не предмет записи {entry.subject!r}: {text}")
    for key in sorted(registry):
        if key not in findings:
            problems.append(f"{key}: запись реестра устарела — находки нет")
    return problems


def test_control_a_planted_concatenation_is_named() -> None:
    """Подложенная склейка `'#' ~ account.id` названа поимённо (контроль против вакуума)."""
    findings = hash_id_findings(
        {**_template_sources(), "planted/k1.html": "{{ mono('#' ~ account.id) }}"}
    )
    assert "planted/k1.html#0" in findings


def test_the_live_tree_has_no_account_hash_outside_the_registry() -> None:
    """Находки живого дерева — ровно записи реестра; лишние названы с текстом."""
    findings = hash_id_findings(_template_sources())
    extra = {key: text for key, text in findings.items() if key not in TEMPLATE_HASH_EXCEPTIONS}
    assert not extra, "`#` перед идентификатором вне реестра:\n" + "\n".join(
        f"  {key}: {text}" for key, text in sorted(extra.items())
    )


def test_the_scanner_ignores_comments() -> None:
    """Комментарии (Jinja и HTML) не считаются; живая склейка рядом — единственная находка."""
    source = (
        "{# '#' ~ account.id #}<!-- '#' ~ x -->"
        "{{ mono('#' ~ account.id) }}"
    )
    findings = hash_id_findings({"planted/comments.html": source})
    assert list(findings) == ["planted/comments.html#0"]
    assert "account.id" in findings["planted/comments.html#0"]


# =============================================================================
# Задача 2: класс К2, формы-двойники знака, Python-половина, реестр по вхождению.
# =============================================================================


def test_control_a_planted_bare_markup_hash_is_named() -> None:
    """Подложенное `Аккаунт #{{ acc.id }}` названо поимённо (класс К2)."""
    findings = hash_id_findings(
        {**_template_sources(), "planted/k2.html": "<h3>Аккаунт #{{ acc.id }}</h3>"}
    )
    assert "planted/k2.html#0" in findings


def test_control_an_account_hash_returned_before_the_group_one_is_named() -> None:
    """Возврат `Акк #` ПЕРЕД законным `#` группы краснит гейт: исключение — на вхождение."""
    path = "history/includes/history_card.html"
    anchor = "{%- if log.group_external_id %}"
    original = _template_sources()[path]
    assert anchor in original, "точка вставки контроля исчезла из шаблона — обновить контроль"
    returned = original.replace(
        anchor, "{{ mono('Акк #' ~ log.account_id, 'muted') }}" + anchor, 1
    )
    findings = hash_id_findings({**_template_sources(), path: returned})
    card = {key: text for key, text in findings.items() if key.startswith(f"{path}#")}
    assert sorted(card) == [f"{path}#0", f"{path}#1"], card
    problems = registry_violations(findings, TEMPLATE_HASH_EXCEPTIONS)
    assert any(problem.startswith(f"{path}#0: за `#` не предмет") for problem in problems), problems
    assert any(problem.startswith(f"{path}#1: вне реестра") for problem in problems), problems


def test_every_registry_entry_points_at_its_declared_subject() -> None:
    """Живые находки и реестр сходятся: ни лишнего, ни устаревшего, ни чужого предмета."""
    findings = hash_id_findings(_template_sources())
    assert registry_violations(findings, TEMPLATE_HASH_EXCEPTIONS) == []
    for key in ("history/detail.html#0", "history/includes/history_card.html#0"):
        assert "group_external_id" in findings[key]
    assert "account_id" in findings["components/account_label.html#0"]


def test_the_registry_declares_its_own_length() -> None:
    """Число исключений шаблонов — литерал; рост и падение краснят."""
    assert len(TEMPLATE_HASH_EXCEPTIONS) == TEMPLATE_HASH_EXCEPTIONS_DECLARED == 3
    for key, entry in TEMPLATE_HASH_EXCEPTIONS.items():
        assert entry.reason.strip(), f"{key}: у исключения нет причины"
        assert entry.subject.strip(), f"{key}: у исключения нет предмета"


LOOKALIKES = {
    "entity-decimal": "&#35;",
    "entity-named": "&num;",
    "fullwidth": "＃",
    "escape-x": "\\x23",
    "escape-u": "\\u0023",
}


def test_hash_lookalikes_are_forbidden_as_a_class() -> None:
    """Формы-двойники знака в живых шаблонах — ноль."""
    findings = hash_id_findings(_template_sources())
    lookalikes = {key: text for key, text in findings.items() if text.startswith("двойник знака")}
    assert not lookalikes, "\n".join(f"  {key}: {text}" for key, text in sorted(lookalikes.items()))


@pytest.mark.parametrize("form", LOOKALIKES.values(), ids=LOOKALIKES.keys())
def test_control_a_planted_hash_lookalike_is_named(form: str) -> None:
    """Подложенный двойник знака перед идентификатором назван поимённо (контроль)."""
    findings = hash_id_findings(
        {**_template_sources(), "planted/k4.html": f"{form}{{{{ acc.id }}}}"}
    )
    assert "planted/k4.html#0" in findings
    assert findings["planted/k4.html#0"].startswith("двойник знака")


def test_control_a_planted_python_hash_is_named() -> None:
    """Подложенная `f"#{account.id}"` в постороннем модуле названа поимённо."""
    findings = python_hash_findings(
        {**_python_sources(), "app/pages/x.py": 'label = f"#{account.id}"'}
    )
    assert "app/pages/x.py#0" in findings


def test_the_live_python_has_no_account_hash_outside_the_registry() -> None:
    """Живое `app/**/*.py`: находки — ровно две записи реестра, с предметом."""
    findings = python_hash_findings(_python_sources())
    assert registry_violations(findings, PYTHON_HASH_EXCEPTIONS) == []


def test_the_python_registry_declares_its_own_length() -> None:
    """Число исключений Python — литерал; причина и предмет у каждого."""
    assert len(PYTHON_HASH_EXCEPTIONS) == PYTHON_HASH_EXCEPTIONS_DECLARED == 2
    assert set(PYTHON_HASH_EXCEPTIONS) == {"app/pages/htmx.py#0", "app/services/account_label.py#0"}
    for key, entry in PYTHON_HASH_EXCEPTIONS.items():
        assert entry.reason.strip(), f"{key}: у исключения нет причины"
        assert entry.subject.strip(), f"{key}: у исключения нет предмета"


def test_control_a_second_mark_in_the_helper_is_named() -> None:
    """Второй знак в любом из двух файлов помощника выходит за реестр: помощник один (D-06)."""
    python_path = "app/services/account_label.py"
    twice = _python_sources()[python_path] + '\nEXTRA = f" #{1}"\n'
    python_findings = python_hash_findings({**_python_sources(), python_path: twice})
    assert f"{python_path}#1" in python_findings
    assert f"{python_path}#1" not in PYTHON_HASH_EXCEPTIONS

    template_path = "components/account_label.html"
    twice_markup = _template_sources()[template_path] + "\n<span>#{{ other_id }}</span>\n"
    template_findings = hash_id_findings({**_template_sources(), template_path: twice_markup})
    assert f"{template_path}#1" in template_findings
    assert f"{template_path}#1" not in TEMPLATE_HASH_EXCEPTIONS


def test_the_universe_is_not_empty() -> None:
    """Ноль находок вне реестра — не сломанный сканер: вселенная непуста и находки названы."""
    templates = _template_sources()
    python = _python_sources()
    assert len(templates) > 0
    assert len(python) > 0
    assert "components/account_label.html" in templates
    assert "app/services/account_label.py" in python
    assert set(hash_id_findings(templates)) == set(TEMPLATE_HASH_EXCEPTIONS)
    assert set(python_hash_findings(python)) == set(PYTHON_HASH_EXCEPTIONS)
