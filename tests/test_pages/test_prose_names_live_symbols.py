"""Проза продуктового комментария называет ИМЕНА символов, и имена разрешаются в объявления.

ЗАЧЕМ. Предупреждение `WR-03` ПЯТОГО круга ревизии не закрыто третьим кругом
подряд, и причина не в трёх числах, а в ФОРМЕ ССЫЛКИ. Пометка рычага
`app/templates/components/modal.html` называла объявление заголовка перехода «на
:148» и сборку ответа «(:375)»; замер 2026-09-10 даёт `HX_LOCATION_HEADER`
объявленным на другой строке, `:357` занятым СОВСЕМ ДРУГОЙ функцией, а `respond()`
объявленным ещё ниже. ⚠️ ОТЯГЧАЮЩЕЕ, названное замером: план 10-35 правил ЭТОТ ЖЕ
файл двадцатью строками выше и протухшую пометку не тронул — то есть номер строки
протухает МОЛЧА, и правка трёх чисел вернула бы ту же пометку в то же состояние
через круг.

ЧТО ПРИНУЖДАЕТ ЭТОТ МОДУЛЬ. Реестр `PROSE_SYMBOL_CITATIONS` выписывает тройки «файл
прозы → имя символа → файл объявления». Правило требует ДВУХ вещей разом:
имя разрешается в ОБЪЯВЛЕНИЕ в названном файле (а не встречается там где угодно —
вхождение нашлось бы и в комментарии), и файл прозы это имя ДЕЙСТВИТЕЛЬНО называет
(реестр, стерегущий несуществующую ссылку, стережёт пустоту и зеленеет впустую).
Переименование символа краснит прогон ГРОМКО; сдвиг строк не значит ничего, потому
что строк в пометке больше нет.

⚠️ ЧЕГО ЭТОТ ФАЙЛ НЕ ДОКАЗЫВАЕТ. Он не судит СОДЕРЖАНИЕ пометки — верно ли
утверждение о транспорте, о статусе и о признаке успешности: это предмет
`tests/test_templates/test_components.py`, где живут два исполняющих правила и
правило единственности места сборки. Он не перебирает ВСЕ имена, названные прозой
проекта: реестр литеральный и растёт внесением записи, а не обходом, — обход
именованных прозой символов потребовал бы суждения о том, что в тексте является
именем, а что словом.
"""

import re
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Пометка рычага, чью форму ссылки чинит план 10-46. Тело комментария опознаётся
# по его собственному первому предложению, а не по номерам строк: модуль,
# сторожащий негниющую форму ссылки, не имеет права сам ссылаться строкой.
LEVER_NOTE_FILE = "app/templates/components/modal.html"
LEVER_NOTE_MARKER = "ВТОРОЙ ДИЗЪЮНКТ УСЛОВИЯ ЗАКРЫТИЯ ПАНЕЛИ"
_JINJA_COMMENT_RE = re.compile(r"\{#-?(?P<body>.*?)-?#\}", re.S)


@dataclass(frozen=True)
class Citation:
    """Ссылка прозы на живой символ: где названо, ЧТО названо, где объявлено."""

    prose_file: str
    symbol: str
    declaring_file: str


# ⚠️ РЕЕСТР ЛИТЕРАЛЬНЫЙ И ЭТО НЕСУЩЕЕ: он ОБЪЯВЛЯЕТ договор, а не выводит его из
# проверяемого текста. Реестр, собранный разбором самой пометки, доказывал бы, что
# пометка называет то, что называет, — то есть ничего.
PROSE_SYMBOL_CITATIONS: tuple[Citation, ...] = (
    Citation(LEVER_NOTE_FILE, "HX_LOCATION_HEADER", "app/pages/htmx.py"),
    Citation(LEVER_NOTE_FILE, "location_response", "app/pages/htmx.py"),
    Citation(LEVER_NOTE_FILE, "respond", "app/pages/htmx.py"),
    Citation(LEVER_NOTE_FILE, "htmx_refusal_handler", "app/main.py"),
)

REASON_UNRESOLVED = "имя не разрешается в объявление"
REASON_PROSE_SILENT = "файл прозы имени не называет"


@dataclass(frozen=True)
class Finding:
    """Одно расхождение реестра с деревом: основание и подробность, называющая имя и файл."""

    reason: str
    detail: str

    def __str__(self) -> str:
        return f"{self.reason}: {self.detail}"


def _declaration_patterns(symbol: str) -> tuple[re.Pattern[str], ...]:
    """Образцы ОБЪЯВЛЕНИЯ, а не вхождения.

    Имя верхнего уровня — присваивание В НАЧАЛЕ СТРОКИ; функция — ключевое слово
    объявления перед именем, с необязательным `async` и любым отступом (обработчик
    исключения объявляется внутри сборщика приложения). Простое вхождение годным
    признаком не является: оно нашлось бы и в комментарии, и в докстринге, — то
    есть пометка стерегла бы саму себя.
    """
    escaped = re.escape(symbol)
    return (
        re.compile(rf"^{escaped}\s*(?::[^=]+)?=", re.M),
        re.compile(rf"^\s*(?:async\s+)?def\s+{escaped}\s*\(", re.M),
        re.compile(rf"^\s*class\s+{escaped}\b", re.M),
    )


def resolves_to_declaration(symbol: str, source: str) -> bool:
    """Разрешается ли имя в объявление внутри поданного исходника."""
    return any(pattern.search(source) for pattern in _declaration_patterns(symbol))


def citation_findings(
    citations: tuple[Citation, ...], *, root: Path = PROJECT_ROOT
) -> list[Finding]:
    """Расхождения реестра с деревом. Пустой список — каждая ссылка жива.

    Реестр и корень приходят ПАРАМЕТРАМИ: иначе отрицательный контроль был бы
    невыразим — негодную ссылку пришлось бы класть на дерево, то есть портить
    продукт ради проверки правила.
    """
    findings: list[Finding] = []

    for citation in citations:
        declaring = root / citation.declaring_file
        if not declaring.is_file() or not resolves_to_declaration(
            citation.symbol, declaring.read_text(encoding="utf-8")
        ):
            findings.append(
                Finding(
                    reason=REASON_UNRESOLVED,
                    detail=(
                        f"имя `{citation.symbol}`, названное прозой "
                        f"`{citation.prose_file}`, не разрешается в объявление в "
                        f"`{citation.declaring_file}` — символ переименован, "
                        "переехал либо снят, и проза пережила свою истинность"
                    ),
                )
            )
            continue

        prose = root / citation.prose_file
        if not prose.is_file() or citation.symbol not in prose.read_text(
            encoding="utf-8"
        ):
            findings.append(
                Finding(
                    reason=REASON_PROSE_SILENT,
                    detail=(
                        f"проза `{citation.prose_file}` имени `{citation.symbol}` "
                        "не называет — запись реестра стережёт ссылку, которой нет, "
                        "то есть стережёт пустоту и зеленеет впустую"
                    ),
                )
            )

    return findings


def lever_note_body(source: str) -> str:
    """Тело комментария разметки, несущего пометку рычага."""
    for match in _JINJA_COMMENT_RE.finditer(source):
        body = match.group("body")
        if LEVER_NOTE_MARKER in body:
            return body
    raise AssertionError(
        f"в `{LEVER_NOTE_FILE}` не найден комментарий разметки, несущий "
        f"«{LEVER_NOTE_MARKER}» — пометка снята либо переписана до неузнаваемости"
    )


def _report(findings: list[Finding]) -> str:
    return "\n".join(f"  — {item}" for item in findings)


# --- сам гейт ----------------------------------------------------------------------


def test_every_prose_citation_resolves_to_a_live_declaration():
    """КАЖДОЕ ИМЯ, НАЗВАННОЕ ПРОЗОЙ, ЖИВО, И КАЖДАЯ ЗАПИСЬ РЕЕСТРА СТЕРЕЖЁТ ЖИВУЮ ССЫЛКУ.

    Антивакуумная половина идёт ПЕРВОЙ: пустой реестр зеленел бы сам собой — то есть
    ровно тогда, когда последнюю ссылку из него вынули.
    """
    assert PROSE_SYMBOL_CITATIONS, (
        "реестр ссылок пуст — правило зеленеет вакуумом, не предъявив требования "
        "ни одному имени"
    )

    findings = citation_findings(PROSE_SYMBOL_CITATIONS)
    assert not findings, _report(findings)


def test_the_lever_note_points_by_name_and_not_by_line_number():
    """В ТЕЛЕ ПОМЕТКИ НЕТ НИ ОДНОЙ ССЫЛКИ НОМЕРОМ СТРОКИ.

    Это и есть смена ФОРМЫ ССЫЛКИ, ради которой заведён модуль. Номер строки
    протухает молча — доказано трижды: пометка пережила три круга ревизии и правку
    соседнего плана в том же файле. Имя протухает громко: его разрешение в живое
    объявление принуждается гейтом выше.
    """
    body = lever_note_body(
        (PROJECT_ROOT / LEVER_NOTE_FILE).read_text(encoding="utf-8")
    )
    line_references = re.findall(r":\d+", body)
    assert not line_references, (
        f"в теле пометки `{LEVER_NOTE_FILE}` осталось "
        f"{len(line_references)} ссылок номером строки ({', '.join(line_references)}) "
        "— форма, протухающая молча; называть надо ИМЯ символа и файл его "
        "объявления, а разрешение имени стережёт "
        "`test_every_prose_citation_resolves_to_a_live_declaration`"
    )


def test_the_lever_note_names_every_symbol_of_the_registry():
    """Пометка называет ВСЕ имена реестра — реестр и проза не разошлись."""
    body = lever_note_body(
        (PROJECT_ROOT / LEVER_NOTE_FILE).read_text(encoding="utf-8")
    )
    missing = [
        citation.symbol
        for citation in PROSE_SYMBOL_CITATIONS
        if citation.prose_file == LEVER_NOTE_FILE and citation.symbol not in body
    ]
    assert not missing, (
        "имена реестра, которых нет в ТЕЛЕ пометки: "
        f"{', '.join(missing)} — запись реестра говорит о пометке, а имя стои́т "
        "где-то ещё в файле, то есть связь реестра с пометкой мнимая"
    )


# --- зубы: реестры, выписанные ЛИТЕРАЛАМИ прямо в контроле --------------------------

# ⚠️ НЕЦИКЛИЧНОСТЬ ОБЪЯВЛЯЕТСЯ ПРЯМО: ожидание обоих контролей ниже НЕ БЕРЁТСЯ из
# `PROSE_SYMBOL_CITATIONS`. Контроль, строящий негодный реестр из проверяемого,
# доказывал бы согласие правила с самим собой, а не его зубы.

_REGISTRY_WITH_A_DEAD_NAME: tuple[Citation, ...] = (
    Citation(LEVER_NOTE_FILE, "HX_LOCATION_HEADER_RENAMED_AWAY", "app/pages/htmx.py"),
)

_REGISTRY_WHOSE_PROSE_IS_SILENT: tuple[Citation, ...] = (
    Citation("app/templates/components/modal.html", "NOTICE_QUERY_KEY", "app/pages/htmx.py"),
)


def test_a_name_that_no_longer_resolves_is_caught():
    """Негативный контроль 1: имя, которого в названном файле НЕТ, краснит правило.

    Ожидание выписано здесь литералом и из живого реестра не берётся.
    """
    findings = citation_findings(_REGISTRY_WITH_A_DEAD_NAME)

    assert len(findings) == 1, _report(findings)
    only = findings[0]
    assert only.reason == REASON_UNRESOLVED
    assert "HX_LOCATION_HEADER_RENAMED_AWAY" in only.detail, (
        f"сообщение обязано назвать ИМЯ: {only.detail}"
    )
    assert "app/pages/htmx.py" in only.detail, (
        f"сообщение обязано назвать ФАЙЛ объявления: {only.detail}"
    )


def test_a_registry_entry_whose_prose_is_silent_is_caught():
    """Негативный контроль 2: ДРУГОЕ основание — реестр стережёт пустоту.

    `NOTICE_QUERY_KEY` объявлен в слое перехода живым — то есть первое основание
    к нему НЕ ПРИМЕНИМО, — но пометка рычага его не называет ни разу. Без этого
    контроля реестр можно было бы набить именами, которых проза не знает, и
    правило зеленело бы, не стерегя ничего.
    """
    findings = citation_findings(_REGISTRY_WHOSE_PROSE_IS_SILENT)

    assert len(findings) == 1, _report(findings)
    only = findings[0]
    assert only.reason == REASON_PROSE_SILENT
    assert only.reason != REASON_UNRESOLVED
    assert "NOTICE_QUERY_KEY" in only.detail


def test_a_live_registry_shows_no_finding():
    """Позитивный контроль: без него оба негативных не отличали бы работу от красноты всегда."""
    live = (Citation(LEVER_NOTE_FILE, "location_response", "app/pages/htmx.py"),)
    assert citation_findings(live) == []
