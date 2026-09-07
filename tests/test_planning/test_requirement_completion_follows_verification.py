"""Отметка завершённости требования ОБЯЗАНА иметь вердикт отчёта верификации своей фазы.

ЗАЧЕМ. Событие названо поимённо: коммит `0ea886d` (план 10-11) поставил требованию
`FORM-06` отметку завершённости — заполненный флажок в теле `.planning/REQUIREMENTS.md`
и клетку `Complete` в таблице состояний — ПОСЛЕ того, как блокер `CR-01` был открыт
прежним отчётом верификации Фазы 10, и ДО того, как он был закрыт; ручной обход
`10-UAT.md` к тому моменту не был пройден НИ РАЗУ. Поймал это СЛЕДУЮЩИЙ круг
верификации, а не прогон, и вернул запись коммит `c899f04` — то есть чинил
расхождение не тот, кто его вносил, и механизма это не завело.

Регламент у проекта БЫЛ и записан его собственными словами: «условие перевода —
вердикт `passed` повторной верификации» (`.planning/REQUIREMENTS.md`, разбор круга
верификации Фазы 9). Правило существовало; ПРИНУЖДЕНИЯ у него не было. Настоящий
модуль и есть принуждение: он живёт в `tests/` и потому входит в `just test` —
команду, которую в проекте запускают все, — так что коммит, поставивший отметку
раньше вердикта, краснит прогон. Обходить становится нечего.

⚠️ ЧЕГО ЭТОТ ФАЙЛ НЕ ДОКАЗЫВАЕТ. Он НЕ СУДИТ ПРОЗУ записи требований ни одной
строкой: ни формулировку требования, ни летописи чисел, ни разборы кругов
верификации — из всего документа читаются ТОЛЬКО клетки таблицы состояний и
флажки требований, то есть два машинно читаемых поля. Он не утверждает, что отчёт
верификации ВЕРЕН: отчёт объявлен ИСТОЧНИКОМ вердикта, и модуль сверяется с ним, а
не проверяет его. Он не знает, поставлена ли отметка ВОВРЕМЯ, — он знает лишь, что
отметка и вердикт не противоречат друг другу. И он ничего не утверждает о строках,
НЕ помеченных завершёнными: их состояние — предмет роадмапа, а не этого модуля.

ПОЧЕМУ ЭТО НЕ ОТМЕНА РЕШЕНИЯ D-33. Решение D-33 отказало машинному гейту на ПРОЗЕ
операционного документа с названной причиной: отличить «константу величины, которую
документ не может держать истинной» от законного числа того же документа (даты,
цены, номера ревизии, числа, квалифицированного раундом) машине нечем, и такой гейт
давал бы либо ложные отказы, либо зелень всегда. Здесь предмет ДРУГОЙ: ДВА машинно
читаемых поля (клетка состояния требования и поле `status` шапки отчёта) и ОДИН
объявленный между ними источник соответствия. Суждения этот предмет не требует,
поэтому D-33 настоящим модулем НЕ ПЕРЕОТКРЫВАЕТСЯ и НЕ ОТМЕНЯЕТСЯ; документная
половина прохибиций по-прежнему судится человеком.

Разбор ведётся ПО ФОРМЕ СТРОКИ, а не по точному тексту требования: правка
формулировки состояния или текста требования не имеет права ронять правило —
хрупкое правило отключают, и вместе с ним отключается свойство.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLANNING_ROOT = PROJECT_ROOT / ".planning"
REQUIREMENTS_PATH = PLANNING_ROOT / "REQUIREMENTS.md"

# Состояние клетки, которым таблица объявляет требование завершённым. Литерал взят
# у самой записи (`.planning/REQUIREMENTS.md`, раздел Traceability) и НЕ выводится
# из вердикта отчёта: два литерала живут в двух разных документах, и вывод одного
# из другого молча связал бы их правкой любого из них.
COMPLETED_STATUS = "Complete"

# Вердикт шапки отчёта верификации, которым РЕГЛАМЕНТ ПРОЕКТА обусловил перевод
# требования в завершённое состояние: «условие перевода — вердикт `passed`
# повторной верификации». Литерал взят у поля `status` шапки отчётов и НЕ выводится
# из состояния клетки.
PASSED_VERDICT = "passed"

# ЛЕТОПИСЬ ЧИСЛА: 44. ОТКУДА ВЗЯЛОСЬ — поставлено ПРОГОНОМ покрасневшего правила
# ниже, дословно: «строк таблицы состояний в `.planning/REQUIREMENTS.md` найдено 44,
# а объявлено 0». ЧЕМ ИЗМЕРЕНО — самим разборщиком `_requirement_rows` на записи
# дерева, а не счётом глазом. КАКИМ ПЛАНОМ — 10-14 (2026-09-04, Фаза 10).
# ⚠️ ОРИЕНТИР ПЛАНА — 41 — И РАСХОЖДЕНИЕ ОБЪЯСНЕНО: 41 есть число требований
# ДЕЙСТВУЮЩЕЙ ВЕХИ, и ровно столько строк несут клетку фазы. Таблица держит СВЕРХ них
# ТРИ строки, заведённые 2026-08-29 и объявленные отложенными к СЛЕДУЮЩЕЙ вехе
# (`EDIT-01`, `UPLD-01`, `E2E-01`), — их клетка фазы имени фазы не несёт. Ориентир не
# был ошибкой: он верно называл вселенную действующей вехи, но не число СТРОК
# таблицы, а стережётся здесь именно число строк.
REQUIREMENT_ROWS_DECLARED = 44

_ROW_RE = re.compile(
    r"^\|\s*(?P<name>[A-Z0-9]+-\d+)\s*\|(?P<phase>[^|]*)\|(?P<status>[^|]*)\|\s*$",
    re.M,
)
_PHASE_RE = re.compile(r"Phase\s+(?P<number>\d+(?:\.\d+)?)")
_VERIFICATION_FILE_RE = re.compile(r"^(?P<number>\d+(?:\.\d+)?)-VERIFICATION\.md$")
_STATUS_FIELD_RE = re.compile(r"^status:\s*(?P<value>[^\s#]+)\s*$")
_FRONTMATTER_FENCE = "---"

# СОГЛАШЕНИЕ О РАСПОЛОЖЕНИИ ЗАПИСИ, СНЯТОЕ ЗАМЕРОМ ПО ДЕРЕВУ 2026-09-07, а не взятое
# из памяти. Обойдены все 13 файлов `*-VERIFICATION.md` под `.planning/`:
#   • отчёт ДЕЙСТВУЮЩЕЙ вехи — `.planning/phases/<NN-слог>/<NN>-VERIFICATION.md`
#     (найдено 4: фазы 07, 08, 09, 10). ИМЕНИ ВЕХИ В ПУТИ НЕТ ВОВСЕ;
#   • отчёт АРХИВНОЙ вехи — `.planning/milestones/<веха>-phases/<NN-слог>/…`
#     (найдено 7: фазы 01…06 и 05.1, каталог вехи — `v2.0-phases`);
#   • отчёт БЫСТРОЙ РАБОТЫ — `.planning/quick/<слог>/<слог>-VERIFICATION.md`
#     (найдено 2). Номера фазы его имя не несёт, и в индекс он не попадает —
#     основание записано докстрингом сборки индекса ниже.
MILESTONES_DIR_NAME = "milestones"
_ARCHIVE_MILESTONE_DIR_RE = re.compile(r"^(?P<milestone>.+)-phases$")

# МЕТКА РАСПОЛОЖЕНИЯ, А НЕ ИМЯ ВЕХИ, И ЭТО РАЗЛИЧЕНИЕ НЕСУЩЕЕ. Отчёты действующей
# вехи лежат в каталоге фаз, имени вехи в их пути нет, поэтому вывести это имя из
# пути НЕЧЕМ — и вписывать его сюда литералом ЗАПРЕЩЕНО: константа с именем вехи
# устарела бы в день её закрытия, то есть правило пришлось бы чинить подгонкой
# утверждения под сегодняшнее дерево — ровно тем движением, против которого написан
# весь этот модуль. Метка означает «та веха, чьи фазы лежат в каталоге фаз», и
# значением взята строка, каталогом вехи быть не могущая.
CURRENT_MILESTONE = "«действующая веха»"

# ФОРМА ЗАГОЛОВКА ЗАПИСИ ТРЕБОВАНИЙ, СНЯТАЯ ЧТЕНИЕМ ЕЁ ПЕРВОЙ СТРОКИ 2026-09-07:
# `# Requirements: Broadcaster — milestone v2.<N> «…»`. Разбирается ФОРМА, а не
# точный текст: правка формулировки заголовка не имеет права ронять правило —
# хрупкое правило отключают, и вместе с ним отключается свойство.
_RECORD_MILESTONE_RE = re.compile(r"milestone\s+(?P<label>v\d+(?:\.\d+)*)")


def _normalised_phase(number: str) -> str:
    """`07` и `7` — ОДНА фаза. Имя файла отчёта дополнено нулём, клетка таблицы нет."""
    whole, _, fraction = number.partition(".")
    whole = whole.lstrip("0") or "0"
    return f"{whole}.{fraction}" if fraction else whole


@dataclass(frozen=True)
class RequirementRow:
    """Одна клетка таблицы состояний: имя требования, его фаза и состояние."""

    name: str
    phase: str | None
    phase_cell: str
    status: str

    @property
    def is_completed(self) -> bool:
        return self.status == COMPLETED_STATUS


def _requirement_rows(text: str) -> list[RequirementRow]:
    """Строки таблицы состояний. ИСХОДНИК приходит параметром, а не из константы.

    Без параметра отрицательный контроль был бы невыразим, и зубы правила пришлось
    бы ЗАЯВЛЯТЬ вместо того, чтобы их ПОКАЗЫВАТЬ.

    Фаза берётся из клетки по форме `Phase N`. Клетка без неё (`— (v2.2)`) даёт
    `None` и разбор не роняет: строка, отложенная к следующей вехе, — штатное
    состояние таблицы, а не дефект.
    """
    rows: list[RequirementRow] = []
    for match in _ROW_RE.finditer(text):
        phase_cell = match.group("phase").strip()
        phase_match = _PHASE_RE.search(phase_cell)
        rows.append(
            RequirementRow(
                name=match.group("name"),
                phase=_normalised_phase(phase_match.group("number"))
                if phase_match
                else None,
                phase_cell=phase_cell,
                status=match.group("status").strip(),
            )
        )
    return rows


@dataclass(frozen=True)
class VerificationReport:
    """Вердикт отчёта верификации одной фазы ОДНОЙ вехи и путь, которым он найден.

    Веха — половина ключа индекса: номер фазы уникален ВНУТРИ вехи, а обход индекса
    рекурсивен и захватывает архив, поэтому одного номера ключом мало.
    """

    milestone: str
    phase: str
    verdict: str | None
    path: Path

    @property
    def has_passed(self) -> bool:
        return self.verdict == PASSED_VERDICT


def _record_milestone(text: str) -> str:
    """Веха записи требований, разобранная ИЗ ЕЁ СОБСТВЕННОГО ЗАГОЛОВКА ПО ФОРМЕ.

    ИСХОДНИК ПРИХОДИТ ТЕКСТОМ — той же идиомой, что у `_requirement_rows` и
    `_requirement_flags`, и по той же причине: без параметра отрицательный контроль
    был бы невыразим, и зубы правила пришлось бы ЗАЯВЛЯТЬ вместо того, чтобы их
    ПОКАЗЫВАТЬ.

    РАЗВИЛКА ИСТОЧНИКОВ ВЕХИ РАЗРЕШЕНА ЗДЕСЬ, А НЕ ОСТАВЛЕНА ЧИТАТЕЛЮ: следующий
    автор придёт ровно к ней. Кандидатов ДВА. Первый — ЗАГОЛОВОК документа, который
    называет веху ОДИН РАЗ и ДЛЯ ВСЕЙ записи. Второй — разделы `## v<N>.<N>
    Requirements`, которые веху тоже называют, но которыми веху СТРОКИ вывести
    НЕЛЬЗЯ: таблица состояний в документе ОДНА и лежит ВНЕ обоих разделов, поэтому
    судимая строка не живёт ни в одном из них. Веху ДОКУМЕНТА вывести можно, веху
    СТРОКИ — нет; выбран первый кандидат.

    ОТКАЗ ГРОМКИЙ И С ТЕКСТОМ ЗАГОЛОВКА: пустая метка означала бы, что индекс не
    найдёт НИ ОДНОГО отчёта и несущее правило зазеленеет ВАКУУМОМ — то есть перестанет
    проверять что бы то ни было, ничем этого не показав.
    """
    lines = text.splitlines()
    heading = next((line for line in lines if line.startswith("# ")), "")
    named = _RECORD_MILESTONE_RE.search(heading)
    if named is None:
        raise AssertionError(
            f"веха записи требований НЕ ВЫВЕДЕНА из её заголовка: «{heading}». "
            f"Заголовок обязан называть веху формой `milestone vN.N`; невыведенная "
            f"веха дала бы индексу ноль попаданий, и несущее правило зазеленело бы "
            f"ВАКУУМОМ, сверяя завершённые строки не с чем"
        )
    return named.group("label")


def _lookup_milestone_label(
    record_milestone: str, index: dict[tuple[str, str], VerificationReport]
) -> str:
    """ОДНО ОБЪЯВЛЕННОЕ СООТВЕТСТВИЕ «имя вехи записи ↔ метка расположения».

    ОСНОВАНИЕ, а не удобство. Веха записи названа её заголовком ИМЕНЕМ (`vN.N`), а
    метка расположения выводится из ПУТИ отчёта — и путь отчёта ДЕЙСТВУЮЩЕЙ вехи
    имени вехи не несёт вовсе: он лежит в каталоге фаз. Это СОГЛАШЕНИЕ О
    РАСПОЛОЖЕНИИ, а не свойство вехи, поэтому две величины и не совпадают.

    Правило соответствия одно: веха, НАЗВАННАЯ каким-нибудь путём индекса, и есть
    архивная — к ней ведёт её имя; веха, ни одним путём не названная, лежит в
    каталоге фаз — к ней ведёт метка расположения. Второе место этого соответствия
    разошлось бы с первым при первой же правке.
    """
    named_by_paths = {milestone for milestone, _ in index}
    return record_milestone if record_milestone in named_by_paths else CURRENT_MILESTONE


def _report_milestone(path: Path, root: Path) -> str:
    """Веха отчёта, выведенная ИЗ ЕГО ПУТИ по соглашению о расположении записи.

    Отчёт под `<корень>/milestones/<веха>-phases/…` принадлежит НАЗВАННОЙ вехе, и
    имя берётся из каталога. Всякий другой отчёт лежит в каталоге фаз действующей
    вехи и получает МЕТКУ `CURRENT_MILESTONE`, а не имя: имени вехи в его пути нет
    вовсе, и вписанное сюда оно устарело бы в день закрытия вехи.

    Путь ВНЕ поданного корня разбору не подлежит и получает ту же метку: корень
    приходит параметром, и синтетическое дерево контроля обязано читаться тем же
    разбором, что и живое.
    """
    try:
        relative = path.relative_to(root)
    except ValueError:
        return CURRENT_MILESTONE
    parts = relative.parts
    if len(parts) >= 2 and parts[0] == MILESTONES_DIR_NAME:
        named = _ARCHIVE_MILESTONE_DIR_RE.match(parts[1])
        if named:
            return named.group("milestone")
    return CURRENT_MILESTONE


def _report_verdict(text: str) -> str | None:
    """Поле `status` ПЕРВОГО блока frontmatter. Проза отчёта не читается вовсе."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_FENCE:
        return None
    for line in lines[1:]:
        if line.strip() == _FRONTMATTER_FENCE:
            return None
        field = _STATUS_FIELD_RE.match(line)
        if field:
            return field.group("value").strip("\"'")
    return None


def _verification_status_by_milestone_and_phase(
    root: Path,
) -> dict[tuple[str, str], VerificationReport]:
    """Индекс вердиктов по паре «веха, фаза», собранный ОБХОДОМ ВСЕГО дерева записи.

    Обход, а не чтение одного каталога: переезд фазы в архив
    (`.planning/milestones/…`) не имеет права молча выключить правило — отчёт
    отъехавшей фазы обязан находиться там же, где лежал.

    Номер фазы берётся ИЗ ИМЕНИ ФАЙЛА, и способ выбран ОДИН. Основание: поле
    `phase` шапки несёт СЛОГ (`10-rychag-components-modal-html`), а у отчётов
    быстрых работ — вовсе не номер (`quick-260825-hnf-…`), тогда как имя файла
    несёт номер у всех нумерованных фаз и только у них. Второй, независимый способ
    разошёлся бы с первым молча. Отчёт без номера в имени в индекс НЕ ПОПАДАЕТ: он
    принадлежит не фазе, а быстрой работе, и таблица состояний на него не ссылается.

    КЛЮЧ — ПАРА, А НЕ НОМЕР, и основание в том же обходе: номер фазы уникален ВНУТРИ
    вехи, потому что нумерация каждой вехи ведётся своя, а обход намеренно захватывает
    архив. Ключ из одного номера свёл бы отчёты РАЗНЫХ вех в один и молча оставил бы
    последний по обходу — с этого мгновения завершённая строка требования сверялась бы
    с вердиктом ЧУЖОЙ фазы, а несущее правило продолжало бы зеленеть.

    СТОЛКНОВЕНИЕ КЛЮЧЕЙ — ГРОМКИЙ ОТКАЗ ВНУТРИ СБОРКИ, а не возврат признака и не
    выбор «последнего по сортировке»: молчаливое разрешение и есть предмет находки, а
    признак, который потребитель может не прочитать, есть то же молчаливое разрешение
    под другим именем. Решение оставляется человеку, и отказ называет ОБА пути.
    """
    index: dict[tuple[str, str], VerificationReport] = {}
    for path in sorted(root.rglob("*-VERIFICATION.md")):
        named = _VERIFICATION_FILE_RE.match(path.name)
        if not named:
            continue
        phase = _normalised_phase(named.group("number"))
        key = (_report_milestone(path, root), phase)
        clash = index.get(key)
        if clash is not None:
            raise AssertionError(
                f"два отчёта верификации на один ключ «веха, фаза» {key}:\n"
                f"  {clash.path}\n"
                f"  {path}\n"
                f"индекс МОЛЧА вытеснил бы один отчёт другим, и завершённая строка "
                f"требования сверялась бы с вердиктом ЧУЖОЙ фазы. Разрешать это "
                f"выбором «последнего по обходу» нельзя: решение принадлежит человеку "
                f"— либо один из отчётов лежит не там, либо веха выведена неверно"
            )
        index[key] = VerificationReport(
            milestone=key[0],
            phase=phase,
            verdict=_report_verdict(path.read_text(encoding="utf-8")),
            path=path,
        )
    return index


@dataclass(frozen=True)
class PrematureCompletion:
    """Требование, помеченное завершённым, за которым не стоит вердикт `passed`."""

    requirement: str
    phase_cell: str
    status: str
    verdict: str | None

    def __str__(self) -> str:
        verdict = (
            f"вердикт `{self.verdict}`"
            if self.verdict is not None
            else "отчёта верификации этой фазы НЕТ ВОВСЕ"
        )
        return (
            f"требование `{self.requirement}` ({self.phase_cell}) помечено "
            f"`{self.status}` в таблице состояний `.planning/REQUIREMENTS.md`, "
            f"а у его фазы {verdict} — условие перевода записано самим проектом: "
            f"вердикт `{PASSED_VERDICT}` повторной верификации"
        )


def premature_completions(
    requirements_text: str, planning_root: Path
) -> list[PrematureCompletion]:
    """ВСЕ несогласные строки одним списком, а не первая.

    Утверждение на каждом шаге чинилось бы по одной строке за прогон; отказ обязан
    показать весь список сразу.

    Строки, НЕ помеченные завершёнными, не судятся вовсе. Отсутствие отчёта у
    ЗАВЕРШЁННОЙ строки — тот же случай, а не оправдание: запись, за которой нет
    вердикта, и есть предмет.

    ВЕХА ВЫВОДИТСЯ ИЗ САМОЙ ПОДАННОЙ ЗАПИСИ, а не приходит извне: оба входа функции
    — запись и корень — заданы вызывающим, и веха обязана следовать за ЗАПИСЬЮ, иначе
    она стала бы ВТОРЫМ, независимым источником одного решения и разошлась бы с
    первым при первой же правке. Имя вехи приводится к метке расположения ЕДИНСТВЕННЫМ
    объявленным соответствием `_lookup_milestone_label`.
    """
    reports = _verification_status_by_milestone_and_phase(planning_root)
    milestone = _lookup_milestone_label(
        _record_milestone(requirements_text), reports
    )
    premature: list[PrematureCompletion] = []
    for row in _requirement_rows(requirements_text):
        if not row.is_completed:
            continue
        report = reports.get((milestone, row.phase)) if row.phase is not None else None
        if report is not None and report.has_passed:
            continue
        premature.append(
            PrematureCompletion(
                requirement=row.name,
                phase_cell=row.phase_cell,
                status=row.status,
                verdict=report.verdict if report is not None else None,
            )
        )
    return premature


def _report(items) -> str:
    return "\n".join(str(item) for item in items)


# --- сами правила ------------------------------------------------------------------


def test_no_requirement_is_marked_complete_before_its_phase_verification_passed():
    """НЕСУЩЕЕ ПРАВИЛО: отметка завершённости не бывает шире вердикта отчёта."""
    premature = premature_completions(
        REQUIREMENTS_PATH.read_text(encoding="utf-8"), PLANNING_ROOT
    )
    assert not premature, _report(premature)


def test_the_number_of_requirement_rows_is_declared():
    """Строка, УШЕДШАЯ из таблицы, краснит прогон так же, как ПРИШЕДШАЯ.

    Без этого правила требование можно было бы «привести в согласие», просто сняв
    его строку: несущее правило судит только те строки, которые видит.
    """
    rows = _requirement_rows(REQUIREMENTS_PATH.read_text(encoding="utf-8"))
    assert len(rows) == REQUIREMENT_ROWS_DECLARED, (
        f"строк таблицы состояний в `.planning/REQUIREMENTS.md` найдено {len(rows)}, "
        f"а объявлено {REQUIREMENT_ROWS_DECLARED} — если строка добавлена или снята "
        f"осознанно, привести надо ОБЪЯВЛЕННОЕ ЧИСЛО и записать летопись; если нет "
        f"— привести надо таблицу"
    )


def test_a_row_without_a_phase_is_declared_deferred_by_the_record_itself():
    """Клетка без фазы законна ТОЛЬКО у отложенной строки.

    Иначе несущее правило обходилось бы стиранием фазы: строка без фазы выпадает
    из его вселенной, и «завершено при неизвестной фазе» проходило бы молча.
    """
    phaseless = [
        row
        for row in _requirement_rows(REQUIREMENTS_PATH.read_text(encoding="utf-8"))
        if row.phase is None
    ]
    not_deferred = [row for row in phaseless if row.status != "Deferred"]
    assert not not_deferred, (
        "строки без фазы, не объявленные отложенными: "
        + ", ".join(f"`{row.name}` ({row.phase_cell}, {row.status})" for row in not_deferred)
    )


# --- зубы: изменённая копия записи, а не правка файла дерева ------------------------


def _fake_planning_root(
    tmp_path: Path,
    verdicts: dict[str, str | None],
    *,
    milestone: str = CURRENT_MILESTONE,
    slug: str = "synthetic",
) -> Path:
    """Синтетический корень записи: «номер фазы → вердикт», `None` — отчёта НЕТ ВОВСЕ.

    ЗАЧЕМ КОРЕНЬ СИНТЕТИЧЕСКИЙ. Предмет отрицательного контроля обязан задаваться
    САМИМ КОНТРОЛЕМ, а не состоянием проекта на день прогона. Контроль, питающийся
    живым деревом, зеленеет ровно при том условии, что его фаза НЕ достигла цели:
    как только вердикт её отчёта станет `passed`, утверждение о вердикте упадёт, и
    чинить его придётся правкой утверждения — а это через круг превращает модуль в
    тест, «который принято подгонять», то есть ровно в тот класс отказа, который
    сам файл осуждает в своей шапке.

    Отчёты раскладываются ПО ПОДКАТАЛОГАМ, а не плоско: индекс
    `_verification_status_by_milestone_and_phase` собирается РЕКУРСИВНЫМ обходом, и
    плоский корень не проверял бы того обхода, ради которого правило написано.
    Тело отчёта открывается ТОЙ ЖЕ оградой frontmatter, какую читает
    `_report_verdict`, — иначе синтетика молча давала бы вердикт `None`, и контроль
    зеленел бы не на том, на чём думает.

    ВЕХА И СЛОГ КАТАЛОГА — ИМЕНОВАННЫЕ ПАРАМЕТРЫ С УМОЛЧАНИЯМИ, И УМОЛЧАНИЯ ВЫБРАНЫ
    ТАК, ЧТОБЫ НИ ОДИН ПРЕЖНИЙ КОНТРОЛЬ НЕ ПРАВИЛСЯ: без них сборка раскладывает
    отчёты ровно туда же, куда раскладывала. Сборка ДОБАВЛЯЮЩАЯ, а не замещающая, —
    повторный вызов на том же `tmp_path` кладёт в дерево ещё отчёты, и этим
    выражается дерево ДВУХ вех, а равно и столкновение двух отчётов одного номера
    ВНУТРИ одной вехи (тот же номер, другой слог каталога).

    РАСКЛАДКА ПОВТОРЯЕТ СОГЛАШЕНИЕ ЖИВОГО ДЕРЕВА, снятое замером: отчёт действующей
    вехи — под `phases/`, отчёт названной вехи — под `milestones/<веха>-phases/`.
    Синтетика, разложенная иначе, читалась бы не тем разбором, что живая запись.
    """
    if milestone == CURRENT_MILESTONE:
        milestone_root = tmp_path / "phases"
    else:
        milestone_root = tmp_path / MILESTONES_DIR_NAME / f"{milestone}-phases"
    for phase, verdict in verdicts.items():
        if verdict is None:
            continue
        directory = milestone_root / f"{phase}-{slug}"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{phase}-VERIFICATION.md").write_text(
            "\n".join(
                [
                    _FRONTMATTER_FENCE,
                    f"phase: {phase}-synthetic",
                    f"status: {verdict}",
                    _FRONTMATTER_FENCE,
                    "",
                    "Проза синтетического отчёта, которой правило не читает вовсе.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    return tmp_path


def _synthetic_requirements(rows, milestone: str = "v9.8") -> str:
    """Синтетическая запись требований из троек «имя, клетка фазы, состояние».

    ФОРМА СТРОКИ СНЯТА С `_ROW_RE` И С ЖИВОЙ ЗАПИСИ, а не взята из памяти:
    разборщик требует ровно ТРЁХ столбцов и конца строки сразу после третьего
    разделителя. Шапка таблицы и заголовок добавлены ради того, чтобы синтетика
    читалась записью, а не голым перечнем; разбору они безразличны — имя строки
    требуется формы `[A-Z0-9]+-\\d+`, которой ни одна строка шапки не отвечает.

    Что синтетика ДЕЙСТВИТЕЛЬНО разобралась, утверждается ВНУТРИ каждого контроля
    сличением числа строк с числом поданных троек: сборка, молча давшая пустой
    вход, оставила бы контроль зеленеть ВАКУУМОМ.

    ЗАГОЛОВОК НАЗЫВАЕТ ВЕХУ ТОЙ ЖЕ ФОРМОЙ, ЧТО И ЖИВАЯ ЗАПИСЬ, — иначе синтетика
    читалась бы не тем разбором, что живая, и `_record_milestone` падал бы на ней
    громко. Умолчание — веха, которой у проекта нет и роадмап её не планирует,
    поэтому синтетика никогда не выдаёт себя за живую запись; контроли, вехой не
    интересующиеся, умолчания не называют вовсе и правки не потребовали.
    """
    lines = [
        f"# Синтетическая запись требований — milestone {milestone}",
        "",
        "## Traceability",
        "",
        "| Требование | Фаза | Состояние |",
        "|---|---|---|",
    ]
    lines += [
        f"| {name} | {phase_cell} | {status} |" for name, phase_cell, status in rows
    ]
    lines.append("")
    return "\n".join(lines)


# ⚠️ ПОМОЩНИК `_with_status` СНЯТ ПЛАНОМ 10-17, И ЭТО РЕШЕНИЕ ПО ЗАМЕРУ, А НЕ
# МОЛЧАЛИВАЯ УБОРКА. Он был заведён ради подмены клетки ЖИВОЙ записи, а после
# переезда ОБОИХ отрицательных контролей на синтетические входы вызовов у него
# осталось НОЛЬ. ЗАМЕР ДО СНЯТИЯ: `grep -c '_with_status('` → 1, и то была сама
# строка `def`. ЗАМЕР ПОСЛЕ СНЯТИЯ даёт то же 1 — но это уже НАСТОЯЩАЯ СТРОКА
# КОММЕНТАРИЯ, а объявления в модуле нет вовсе (`grep -c '^def _with_status'` → 0).
# Оставленный, он был бы мёртвым кодом, который следующий читатель принял бы за
# действующий приём подмены — то есть за приглашение вернуть контроль на живое
# дерево. ДВА СОСЕДНИХ ПОМОЩНИКА НИЖЕ — подмены флажка и снятия строки таблицы —
# НЕ СНЯТЫ: их потребители суть два контроля правила согласия флажка с клеткой,
# которые живого дерева не покидают и предметом настоящей партии не являются.
# ⚠️ ИМЕНАМИ они здесь не названы намеренно: их отсутствие в диффе есть приёмочный
# критерий плана 10-17, снимаемый поиском по тексту диффа, — и комментарий,
# назвавший их, лишил бы гейт способности отличить упоминание от правки.


def test_control_negative_a_premature_completion_reddens_the_rule(tmp_path):
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ: то же событие `0ea886d`, но НА СИНТЕТИКЕ.

    ОБА входа `premature_completions` задаются САМИМ КОНТРОЛЕМ: запись собрана
    `_synthetic_requirements`, корень — `_fake_planning_root`. Прежняя форма читала
    ЖИВОЕ дерево и утверждала его сегодняшний вердикт (`gaps_found`) дословно, то
    есть зеленела ровно при том условии, что Фаза 10 НЕ достигла цели.

    ⚠️ ОСНОВАНИЕ ВЫБОРА ИМЁН, А НЕ ПРОИЗВОЛ. Номер фазы `91` взят из диапазона,
    которого у проекта нет и роадмап его не планирует, поэтому столкновение
    синтетики с реальной фазой невыразимо. Префикс `SYN` не совпадает ни с одним
    префиксом реестра требований (`FORM`, `FOUND`, `GATE`, `QUAL`, `PAY`, `FETCH`,
    `EDIT`, `UPLD`, `E2E`), поэтому синтетическую строку нельзя принять за живую.

    ПОЛОЖИТЕЛЬНЫЙ КОНТРОЛЬ НА ЖИВОЙ ЗАПИСИ ИЗ ЭТОЙ ФУНКЦИИ УБРАН НАМЕРЕННО: его
    предмет дословно совпадал с несущим правилом
    `test_no_requirement_is_marked_complete_before_its_phase_verification_passed`,
    которое живого дерева не покидает. Его место занял СИНТЕТИЧЕСКИЙ положительный
    контроль — `test_control_a_passed_verdict_in_the_synthetic_root_empties_the_finding`.
    """
    rows = [("SYN-01", "Phase 91", COMPLETED_STATUS)]
    text = _synthetic_requirements(rows)
    assert len(_requirement_rows(text)) == len(rows), (
        "синтетическая запись дала не столько строк, сколько подано троек — "
        "разборщик прочёл бы пустой вход, и контроль зеленел бы ВАКУУМОМ"
    )

    premature = premature_completions(
        text, _fake_planning_root(tmp_path, {"91": "gaps_found"})
    )

    assert len(premature) == 1, _report(premature)
    only = premature[0]
    assert only.requirement == "SYN-01"
    assert only.verdict == "gaps_found"
    message = str(only)
    assert "SYN-01" in message and "Phase 91" in message and "gaps_found" in message, (
        f"отказ обязан называть требование, фазу и вердикт отчёта: {message}"
    )


def test_control_a_passed_verdict_in_the_synthetic_root_empties_the_finding(tmp_path):
    """ЗУБЫ ПЕРВОГО ОТРИЦАТЕЛЬНОГО КОНТРОЛЯ — МУТАЦИЕЙ ВХОДА, А НЕ ЗАЯВЛЕНИЕМ.

    Та же синтетическая запись и тот же синтетический корень, что у контроля выше,
    но вердикт фазы `91` подменён на `PASSED_VERDICT`.

    ЧТО ДОКАЗЫВАЕТ МУТАЦИЯ: находка рождена ВЕРДИКТОМ ПОДАННОГО КОРНЯ, а не самим
    присутствием завершённой строки в записи. Без этой половины синтетика заменила
    бы вшитое состояние НЕПРОВЕРЕННЫМ — а это хуже, потому что незаметно: контроль
    зеленел бы и на разборщике, возвращающем находку ВСЕГДА.
    """
    rows = [("SYN-01", "Phase 91", COMPLETED_STATUS)]
    text = _synthetic_requirements(rows)
    assert len(_requirement_rows(text)) == len(rows), (
        "синтетическая запись дала не столько строк, сколько подано троек — "
        "разборщик прочёл бы пустой вход, и контроль зеленел бы ВАКУУМОМ"
    )

    premature = premature_completions(
        text, _fake_planning_root(tmp_path, {"91": PASSED_VERDICT})
    )

    assert not premature, _report(premature)


def test_control_negative_two_premature_completions_are_both_named(tmp_path):
    """ОТКАЗ ПОКАЗЫВАЕТ ВСЕ СТРОКИ, А НЕ ПЕРВУЮ — НА СИНТЕТИКЕ.

    Две строки и два РАЗНЫХ случая, ЗАДАННЫЕ ПОДАННЫМ КОРНЕМ: у фазы `91` отчёт с
    вердиктом `gaps_found` ЕСТЬ, у фазы `92` его НЕТ ВОВСЕ.

    ⚠️ ЧТО СМЕНИЛОСЬ ПРОТИВ ПРЕЖНЕЙ ФОРМЫ И ПОЧЕМУ ЭТО НЕСУЩЕЕ. Прежний контроль
    подменял ДВЕ клетки ЖИВОЙ записи и утверждал ОТСУТСТВИЕ отчёта У ФАЗЫ 11
    ПРОЕКТА (`assert absent.verdict is None`), то есть держался на том, что
    следующая фаза ещё НЕ верифицирована. Это утверждение ОПАСНЕЕ вердиктного
    литерала: оно падает от появления ЛЮБОГО отчёта Фазы 11 — события, стоящего в
    роадмапе ближайшей работой после настоящей фазы. Теперь отсутствие отчёта
    задано КОРНЕМ, и состояние роадмапа контролю безразлично.

    ⚠️ ИМЁН ТРЕБОВАНИЙ ЖИВОЙ ЗАПИСИ ЭТОТ ДОКСТРИНГ НЕ НАЗЫВАЕТ НАМЕРЕННО: их
    отсутствие в теле контроля есть приёмочный критерий плана 10-17, снимаемый
    поиском по тексту функции, — и проза, назвавшая их, лишила бы гейт способности
    отличить упоминание от возврата контроля на живое дерево.
    """
    rows = [
        ("SYN-01", "Phase 91", COMPLETED_STATUS),
        ("SYN-02", "Phase 92", COMPLETED_STATUS),
    ]
    text = _synthetic_requirements(rows)
    assert len(_requirement_rows(text)) == len(rows), (
        "синтетическая запись дала не столько строк, сколько подано троек — "
        "разборщик прочёл бы пустой вход, и контроль зеленел бы ВАКУУМОМ"
    )

    premature = premature_completions(
        text, _fake_planning_root(tmp_path, {"91": "gaps_found", "92": None})
    )

    named = {item.requirement for item in premature}
    assert named == {"SYN-01", "SYN-02"}, _report(premature)

    absent = next(item for item in premature if item.requirement == "SYN-02")
    assert absent.verdict is None
    assert "НЕТ ВОВСЕ" in str(absent), str(absent)

    present = next(item for item in premature if item.requirement == "SYN-01")
    assert present.verdict == "gaps_found", str(present)


def test_control_a_synthetic_report_for_the_second_phase_leaves_one_finding(tmp_path):
    """ЗУБЫ ВТОРОГО ОТРИЦАТЕЛЬНОГО КОНТРОЛЯ — МУТАЦИЕЙ НАЛИЧИЯ ОТЧЁТА.

    Та же синтетическая запись из двух строк, но фаза `92` ПОЛУЧАЕТ отчёт с
    вердиктом `passed`.

    ЧТО ДОКАЗЫВАЕТ МУТАЦИЯ: вторая находка рождена ОТСУТСТВИЕМ ОТЧЁТА В ПОДАННОМ
    КОРНЕ, а не состоянием дерева проекта. Именно этого различения у прежней формы
    контроля не было: она вшивала отсутствие отчёта Фазы 11 и не отличала «отчёта
    нет, потому что так задано корнем» от «отчёта нет, потому что фазу ещё не
    верифицировали».
    """
    rows = [
        ("SYN-01", "Phase 91", COMPLETED_STATUS),
        ("SYN-02", "Phase 92", COMPLETED_STATUS),
    ]
    text = _synthetic_requirements(rows)

    premature = premature_completions(
        text, _fake_planning_root(tmp_path, {"91": "gaps_found", "92": PASSED_VERDICT})
    )

    assert len(premature) == 1, _report(premature)
    assert premature[0].requirement == "SYN-01", _report(premature)


def test_the_verification_index_is_built_by_walking_the_whole_record_tree():
    """Индекс собран обходом: отчёты АРХИВНЫХ фаз в нём есть, и правило не пусто.

    Пустой либо однокаталожный индекс зеленел бы ВАКУУМОМ: завершённые строки
    сверялись бы не с чем.
    """
    index = _verification_status_by_milestone_and_phase(PLANNING_ROOT)
    assert index, "индекс отчётов пуст — правилу не с чем сверяться"

    archived = [
        report for report in index.values() if "milestones" in report.path.parts
    ]
    assert archived, (
        "в индексе нет ни одного отчёта архивной фазы — значит обход выродился в "
        "чтение одного каталога, и переезд фазы в архив выключил бы правило молча"
    )


def test_control_two_reports_of_one_number_in_different_milestones_coexist(tmp_path):
    """ЗУБЫ КЛЮЧА-ПАРЫ: один номер в ДВУХ вехах даёт ДВА ключа, а не один.

    Синтетическое дерево двух вех: отчёт номера `91` лежит в каталоге фаз
    (расположение действующей вехи) И в каталоге архивной вехи. Ключ, состоящий из
    ОДНОГО номера, свёл бы их в один и молча оставил бы в индексе последний по
    обходу; с этого мгновения завершённая строка сверялась бы с вердиктом ЧУЖОЙ
    фазы, а несущее правило продолжало бы зеленеть.

    ⚠️ ВЕРДИКТЫ ЗАДАНЫ РАЗНЫМИ НАМЕРЕННО: при равных вердиктах контроль не отличил
    бы два ключа от одного — он зеленел бы и на индексе, потерявшем один отчёт.
    """
    root = _fake_planning_root(tmp_path, {"91": "gaps_found"})
    _fake_planning_root(tmp_path, {"91": PASSED_VERDICT}, milestone="v9.9")

    index = _verification_status_by_milestone_and_phase(root)

    assert set(index) == {(CURRENT_MILESTONE, "91"), ("v9.9", "91")}, sorted(index)
    current = index[(CURRENT_MILESTONE, "91")]
    archived = index[("v9.9", "91")]
    assert current.verdict != archived.verdict, (
        "вердикты двух вех совпали — контроль не отличил бы два ключа от одного"
    )
    assert current.milestone == CURRENT_MILESTONE and archived.milestone == "v9.9"


def test_control_two_reports_of_one_number_in_one_milestone_fail_loudly(tmp_path):
    """ЗУБЫ ГРОМКОГО ОТКАЗА: два отчёта одного номера в ОДНОЙ вехе краснят сборку.

    Столкновение ключей НЕ разрешается ни «последним по сортировке», ни «первым»:
    молчаливое разрешение и есть предмет находки. Сборка обязана ПАДАТЬ и называть
    ОБА пути, оставляя решение человеку.
    """
    root = _fake_planning_root(tmp_path, {"91": "gaps_found"})
    _fake_planning_root(tmp_path, {"91": PASSED_VERDICT}, slug="dvoynik")

    with pytest.raises(AssertionError) as raised:
        _verification_status_by_milestone_and_phase(root)

    message = str(raised.value)
    assert "91-synthetic" in message and "91-dvoynik" in message, message


def test_the_milestone_of_the_record_is_derived_and_non_empty():
    """ВЫВОД ВЕХИ ЗАПИСИ НЕ ВЫРОЖДАЕТСЯ — ТРИ УТВЕРЖДЕНИЯ, И ТРЕТЬЕ НЕСУЩЕЕ.

    Метка разобрана; метка НЕПУСТА; и в индексе ЖИВОГО дерева есть ХОТЯ БЫ ОДИН
    отчёт, к которому эта метка приводит. Без третьей части правило зеленело бы
    ВАКУУМОМ: разобранная, но ни с чем не совпавшая метка даёт индексу ноль
    попаданий, несущее правило не находит НИ ОДНОГО нарушения — и не находит его
    потому, что не сверяет НИЧЕГО.
    """
    text = REQUIREMENTS_PATH.read_text(encoding="utf-8")

    milestone = _record_milestone(text)
    assert milestone, "веха записи разобралась в ПУСТУЮ метку"

    index = _verification_status_by_milestone_and_phase(PLANNING_ROOT)
    label = _lookup_milestone_label(milestone, index)
    found = [key for key in index if key[0] == label]
    assert found, (
        f"веха записи `{milestone}` привела к метке расположения `{label}`, а "
        f"отчётов с этой меткой в индексе живого дерева НЕТ НИ ОДНОГО — несущее "
        f"правило зеленело бы ВАКУУМОМ: завершённые строки сверялись бы не с чем. "
        f"Ключи индекса: {sorted(index)}"
    )


def test_control_a_record_of_another_milestone_looks_up_another_report(tmp_path):
    """ЗУБЫ ВЫВОДА ВЕХИ — ДВУМЯ ПОЛОВИНАМИ, И ОБЕ НЕСУЩИЕ.

    Синтетический корень держит отчёт ОДНОГО номера в ДВУХ вехах с РАЗНЫМИ
    вердиктами. Подаётся одна и та же завершённая строка, и меняется ТОЛЬКО
    заголовок записи.

    (а) заголовок называет АРХИВНУЮ веху корня — найден вердикт ЕЁ отчёта;
    (б) заголовок называет другую веху — запись читается как ДЕЙСТВУЮЩАЯ, и найден
        вердикт отчёта, лежащего в каталоге фаз.

    ⚠️ ОДНОЙ ПОЛОВИНЫ НЕ ХВАТИЛО БЫ: контроль, показавший только (а), зеленел бы и
    на поиске, ИГНОРИРУЮЩЕМ веху вовсе, — потому что при одном ключе искать больше
    негде.
    """
    root = _fake_planning_root(tmp_path, {"91": "gaps_found"})
    _fake_planning_root(tmp_path, {"91": PASSED_VERDICT}, milestone="v9.9")

    rows = [("SYN-01", "Phase 91", COMPLETED_STATUS)]

    # (а) ЗАГОЛОВОК НАЗЫВАЕТ АРХИВНУЮ ВЕХУ КОРНЯ.
    archived_text = _synthetic_requirements(rows, milestone="v9.9")
    assert len(_requirement_rows(archived_text)) == len(rows), (
        "синтетическая запись дала не столько строк, сколько подано троек — "
        "разборщик прочёл бы пустой вход, и контроль зеленел бы ВАКУУМОМ"
    )
    assert _record_milestone(archived_text) == "v9.9"
    from_archive = premature_completions(archived_text, root)
    assert not from_archive, _report(from_archive)

    # (б) ЗАГОЛОВОК НАЗЫВАЕТ ДРУГУЮ ВЕХУ — ЗАПИСЬ ЧИТАЕТСЯ КАК ДЕЙСТВУЮЩАЯ.
    current_text = _synthetic_requirements(rows, milestone="v9.8")
    assert _record_milestone(current_text) == "v9.8"
    from_current = premature_completions(current_text, root)

    assert len(from_current) == 1, _report(from_current)
    assert from_current[0].verdict == "gaps_found", _report(from_current)


# --- две записи одного факта: флажок в теле файла и клетка таблицы ------------------


_FLAG_RE = re.compile(
    r"^- \[(?P<mark>[ x])\] \*\*(?P<name>[A-Z0-9]+-\d+)\*\*", re.M
)

NO_CELL = "нет клетки"
NO_FLAG = "нет флажка"
VALUES_DIVERGE = "значения разошлись"


def _requirement_flags(text: str) -> dict[str, bool]:
    """Флажки требований в теле записи: «имя → заполнен ли».

    ИСХОДНИК приходит параметром — тем же приёмом, что у разборщика клеток, и по
    той же причине: без него отрицательный контроль был бы невыразим.

    Разбор ведётся ПО ФОРМЕ СТРОКИ флажка, а не по тексту требования: текст
    требований в этом проекте объёмен и правится (одни только летописи чисел
    занимают абзацы), и правило, привязанное к нему, отключат вместе со свойством.
    """
    return {
        match.group("name"): match.group("mark") == "x"
        for match in _FLAG_RE.finditer(text)
    }


@dataclass(frozen=True)
class Disagreement:
    """Одно несогласие двух записей одного факта."""

    requirement: str
    flag: bool | None
    cell: str | None

    def __str__(self) -> str:
        flag = (
            "флажка нет"
            if self.flag is None
            else ("флажок ЗАПОЛНЕН" if self.flag else "флажок ПУСТ")
        )
        cell = "клетки нет" if self.cell is None else f"клетка `{self.cell}`"
        return f"`{self.requirement}`: {flag}, {cell}"


def flag_cell_disagreements(text: str) -> dict[str, list[Disagreement]]:
    """ТРИ множества несогласий, названные РАЗДЕЛЬНО.

    Вселенная — строки таблицы, несущие клетку фазы, то есть требования действующей
    вехи.
    Строки без фазы отложены к следующей вехе самой записью и флажка не несут по
    решению; законность такой клетки стережёт отдельное правило, поэтому сузить
    вселенную стиранием фазы не выйдет молча.
    """
    flags = _requirement_flags(text)
    cells = {
        row.name: row.status
        for row in _requirement_rows(text)
        if row.phase is not None
    }

    disagreements: dict[str, list[Disagreement]] = {
        NO_CELL: [],
        NO_FLAG: [],
        VALUES_DIVERGE: [],
    }
    for name in sorted(set(flags) | set(cells)):
        flag = flags.get(name)
        cell = cells.get(name)
        if cell is None:
            disagreements[NO_CELL].append(Disagreement(name, flag, None))
        elif flag is None:
            disagreements[NO_FLAG].append(Disagreement(name, None, cell))
        elif flag != (cell == COMPLETED_STATUS):
            disagreements[VALUES_DIVERGE].append(Disagreement(name, flag, cell))
    return disagreements


def _disagreement_report(disagreements: dict[str, list[Disagreement]]) -> str:
    """Отказ печатает ВСЕ несогласия сразу и называет каждое множество своим именем.

    Пустое множество не печатается вовсе: иначе читатель ищет событие, которого не
    было.
    """
    parts = []
    for kind, items in disagreements.items():
        if not items:
            continue
        parts.append(f"{kind}: " + "; ".join(str(item) for item in items))
    return "\n".join(parts)


def _with_flag(text: str, requirement: str, *, checked: bool) -> str:
    """Копия записи с подменённым флажком ОДНОГО требования. Файл дерева не правится."""
    pattern = re.compile(
        rf"^- \[[ x]\] (\*\*{re.escape(requirement)}\*\*)", re.M
    )
    mark = "x" if checked else " "
    doctored, count = pattern.subn(lambda m: f"- [{mark}] {m.group(1)}", text)
    assert count == 1, (
        f"в записи ожидался ровно один флажок `{requirement}`, найдено {count}"
    )
    return doctored


def _without_row(text: str, requirement: str) -> str:
    """Копия записи БЕЗ строки таблицы одного требования. Файл дерева не правится."""
    pattern = re.compile(
        rf"^\|\s*{re.escape(requirement)}\s*\|[^|]*\|[^|]*\|[ \t]*\n", re.M
    )
    doctored, count = pattern.subn("", text)
    assert count == 1, (
        f"в записи ожидалась ровно одна строка `{requirement}`, найдено {count}"
    )
    return doctored



def test_the_flag_and_the_status_cell_of_every_requirement_agree():
    """ДВА МЕСТА ОДНОГО ФАКТА ГОВОРЯТ ОДНО.

    ⚠️ ЧЕГО ЭТО ПРАВИЛО НЕ УТВЕРЖДАЕТ. Оно НЕ утверждает, что ЛЮБОЕ из двух
    значений ВЕРНО: два согласных места могут быть согласно неверными, и именно так
    предмет и был заведён — коммит `0ea886d` поставил ОБЕ отметки разом, поэтому
    друг друга они не поймали. Утверждение о ВЕРНОСТИ значения принадлежит несущему
    правилу выше (`…_before_its_phase_verification_passed`), которое сверяет клетку
    с вердиктом отчёта. Настоящее правило ловит ДРУГОЙ случай: когда поедет ОДНО из
    двух. Разделение предметов записано здесь, а не оставлено читателю.

    Вселенная правила — строки, несущие клетку фазы, то есть требования действующей
    вехи.
    Строки без фазы отложены к следующей вехе САМОЙ ЗАПИСЬЮ и флажка не несут по
    решению; что клетка без фазы законна только у отложенной строки, стережёт
    отдельное правило выше — иначе вселенную можно было бы сузить стиранием фазы.
    """
    text = REQUIREMENTS_PATH.read_text(encoding="utf-8")
    disagreements = flag_cell_disagreements(text)
    assert not any(disagreements.values()), _disagreement_report(disagreements)


def test_control_negative_a_disagreeing_flag_reddens_the_agreement_rule():
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ: флажок заполнен, клетка — нет.

    `FORM-01` на дереве читается незавершённым ОБОИМИ местами. Копия, в которой
    заполнен только флажок, обязана покраснеть с названным требованием.
    """
    original = REQUIREMENTS_PATH.read_text(encoding="utf-8")
    assert not any(flag_cell_disagreements(original).values()), (
        "положительный контроль: на непрáвленой записи правило обязано быть зелено"
    )

    doctored = _with_flag(original, "FORM-01", checked=True)
    disagreements = flag_cell_disagreements(doctored)

    assert {item.requirement for item in disagreements[VALUES_DIVERGE]} == {
        "FORM-01"
    }, _disagreement_report(disagreements)
    assert not disagreements[NO_CELL] and not disagreements[NO_FLAG]
    message = _disagreement_report(disagreements)
    assert "FORM-01" in message, message


def test_control_negative_the_three_kinds_of_disagreement_are_named_apart():
    """ТРИ МНОЖЕСТВА НЕСОГЛАСИЙ РАЗДЕЛЬНЫ.

    «нет клетки», «нет флажка» и «значения разошлись» — РАЗНЫЕ события, и слитый
    отказ заставил бы следующего читателя разбирать, какое из трёх случилось.
    """
    doctored = _without_row(
        _with_flag(
            REQUIREMENTS_PATH.read_text(encoding="utf-8"), "FORM-01", checked=True
        ),
        "QUAL-04",
    )
    disagreements = flag_cell_disagreements(doctored)

    assert {item.requirement for item in disagreements[NO_CELL]} == {"QUAL-04"}
    assert {item.requirement for item in disagreements[VALUES_DIVERGE]} == {
        "FORM-01"
    }
    assert not disagreements[NO_FLAG]

    message = _disagreement_report(disagreements)
    assert NO_CELL in message and VALUES_DIVERGE in message, message
    assert NO_FLAG not in message, (
        "пустое множество в отказ не печатается — иначе читатель ищет событие, "
        f"которого не было: {message}"
    )
