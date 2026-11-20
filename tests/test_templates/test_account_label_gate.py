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


def hash_id_findings(sources: dict[str, str]) -> dict[str, str]:
    """Места сборки `#` в шаблонах: ключ `путь#порядковый номер` → описание."""
    return {}


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
