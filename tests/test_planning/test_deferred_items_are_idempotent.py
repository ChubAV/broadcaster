"""Правка файла отложенного ПОВТОРЯЕМА: второй прогон не заводит второго раздела.

ЗАЧЕМ. Окно 70 журнала `.planning/WINDOWS.md` называет истину плана 10-39
«ПОВТОРНОЕ ИСПОЛНЕНИЕ ПРАВОК НЕОТЛИЧИМО ОТ ПЕРВОГО» достигнутой ДВУМЯ правками
из ТРЁХ. Третья — задача 3 того плана — внесла раздел «## План 10-39» в
`deferred-items.md` ДОПИСЫВАНИЕМ В КОНЕЦ, без якоря: второй прогон дал бы ВТОРОЙ
такой раздел, и счёт подразделов вырос бы с 11 до 16. Латентно ровно потому, что
план исполняется один раз, — то есть свойство держится расписанием, а не формой
файла. Настоящий модуль и есть форма: у файла появляется ЯКОРЬ КОНЦА ПЕРЕЧНЯ,
раздел вносится ПЕРЕД ним, а единственность раздела на план принуждается прогоном.

⚠️ ЧЕГО ЭТОТ ФАЙЛ НЕ ДОКАЗЫВАЕТ. Он не судит СОДЕРЖАНИЕ отложенного — ни владельца
записи, ни основание неправки, ни то, закрыта ли находка на дереве: всё это
предмет человека и кругов ревизии. Он не утверждает, что раздел внесён по якорю, —
он утверждает НАБЛЮДАЕМОЕ СЛЕДСТВИЕ этого: раздел на план один, якорь один.
Он не читает `.planning/STATE.md` и не знает, какая фаза текущая.

ГРАНИЦА ТРЕБОВАНИЯ ЯКОРЯ НАЗВАНА, А НЕ ПОДРАЗУМЕВАЕТСЯ. Якорь требуется у файла
ЖИВОГО отложенного — того, что лежит под `.planning/phases/` и разделы которого
именованы ПЛАНАМИ, то есть у файла, в который очередной план ещё будет ДОПИСЫВАТЬ.
Файл заархивированной вехи (`.planning/milestones/`) новых разделов не получит
никогда, и требовать от него сторожа против события, которого не будет, значило бы
завести шум вместо правила. А вот УДВОЕНИЕ — раздела ли, якоря ли — судится у ВСЕХ
файлов дерева планирования без изъятия: удвоение, которое уже случилось, есть
дефект независимо от того, ждут ли файл новые дописывания.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

# Предмет модуля — ЗАПИСЬ проекта, а не его продукт. Основание маркера, его
# граница годности и запрет выключать каталог — `tests/test_planning/__init__.py`.
pytestmark = pytest.mark.planning

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLANNING_ROOT = PROJECT_ROOT / ".planning"
DEFERRED_FILE_NAME = "deferred-items.md"

# ⚠️ ЯКОРЬ ЕСТЬ КОММЕНТАРИЙ РАЗМЕТКИ, А НЕ ЗАГОЛОВОК, И ЭТО РЕШЕНИЕ. Заголовок
# попал бы в оглавление и в счёт подразделов — то есть сам стал бы величиной,
# которую надо сверять, и сторож завёл бы себе сторожа. Комментарий разметки при
# отрисовке документа невидим и ни в один счёт не входит.
DEFERRED_END_ANCHOR = "<!-- deferred-items:end -->"

# Раздел отложенного, ИМЕНОВАННЫЙ ПЛАНОМ, — единственная форма, которую дописывает
# исполнитель плана. Разделы, именованные находкой (`## DEF-09-01`, `## D-02-09-01`),
# заводятся по одному на находку и удвоения по плану не знают.
_PLAN_SECTION_RE = re.compile(r"^##\s+План\s+(?P<plan>[^\n]+?)\s*$")

REASON_DUPLICATE_SECTION = "заголовок раздела плана встречается более одного раза"
REASON_ANCHOR_MISSING = "якоря конца перечня нет"
REASON_ANCHOR_DUPLICATED = "якорь конца перечня встречается более одного раза"


def _anchor_lines(text: str) -> list[int]:
    """Номера строк, СОСТОЯЩИХ из якоря целиком.

    ⚠️ СЧЁТ ИДЁТ ПО ОТДЕЛЬНОЙ СТРОКЕ, А НЕ ПО ВХОЖДЕНИЮ ПОДСТРОКИ, И ЭТО НЕСУЩЕЕ.
    Шапка файла отложенного ОБЯЗАНА называть якорь дословно — иначе автор правки
    узнаёт о правиле только из отказа прогона. Подстрочный счёт объявил бы это
    упоминание вторым якорём, то есть краснел бы на самом объявлении правила.
    Точкой внесения служит строка, состоящая из якоря целиком; упоминание внутри
    прозы точкой внесения не является и ею не притворяется.
    """
    return [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if line.strip() == DEFERRED_END_ANCHOR
    ]


@dataclass(frozen=True)
class Finding:
    """Одно расхождение: основание и подробность, называющая ЧИСЛА, а не ощущение."""

    reason: str
    detail: str

    def __str__(self) -> str:
        return f"{self.reason}: {self.detail}"


def deferred_items_findings(text: str, *, anchor_required: bool = True) -> list[Finding]:
    """Расхождения ОДНОГО текста отложенного. Пустой список — файл повторяем.

    Текст приходит ПАРАМЕТРОМ, а не читается функцией с диска: иначе отрицательный
    контроль был бы невыразим — синтетику пришлось бы класть на дерево, то есть
    править то, что проверяется. Та же форма и то же основание, что у соседних
    правил каталога.

    `anchor_required` отделяет живой файл от архивного; граница названа в докстринге
    модуля целиком.
    """
    findings: list[Finding] = []

    sections: dict[str, list[int]] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        match = _PLAN_SECTION_RE.match(line)
        if match is not None:
            sections.setdefault(match.group("plan"), []).append(number)

    for plan, lines in sections.items():
        if len(lines) > 1:
            findings.append(
                Finding(
                    reason=REASON_DUPLICATE_SECTION,
                    detail=(
                        f"раздел «## План {plan}» встречается {len(lines)} раза "
                        f"— строки {', '.join(str(item) for item in lines)}; "
                        "второй раздел заводится дописыванием в конец вместо "
                        "внесения ПЕРЕД якорем"
                    ),
                )
            )

    anchors = _anchor_lines(text)
    if not anchors:
        if anchor_required:
            findings.append(
                Finding(
                    reason=REASON_ANCHOR_MISSING,
                    detail=(
                        f"якоря `{DEFERRED_END_ANCHOR}` в файле нет ни одного — "
                        "вносить раздел некуда, кроме конца файла, а дописывание "
                        "в конец на втором прогоне удваивает раздел"
                    ),
                )
            )
    elif len(anchors) > 1:
        findings.append(
            Finding(
                reason=REASON_ANCHOR_DUPLICATED,
                detail=(
                    f"якорь `{DEFERRED_END_ANCHOR}` стои́т отдельной строкой "
                    f"{len(anchors)} раза — строки "
                    f"{', '.join(str(item) for item in anchors)}; точка внесения "
                    "перестала быть единственной, и два прогона разойдутся по "
                    "разным точкам"
                ),
            )
        )

    return findings


def deferred_files() -> list[Path]:
    """Все файлы отложенного дерева планирования, найденные ОБХОДОМ, а не списком.

    Список путей не пережил бы ни появления новой фазы, ни переезда фазы в архив
    вехи, — а обход переживёт и то и другое.
    """
    return sorted(PLANNING_ROOT.rglob(DEFERRED_FILE_NAME))


LIVE_PHASES_ROOT = PLANNING_ROOT / "phases"


def anchor_is_required(path: Path, phases_root: Path = LIVE_PHASES_ROOT) -> bool:
    """Живой ли это файл отложенного: под `.planning/phases/` и с разделами ПЛАНОВ.

    `phases_root` — параметр с умолчанием живого корня (план 16-01): без него
    синтетический контроль в `tmp_path` был бы невыразим. Тело и смысл прежние.
    """
    if phases_root not in path.parents:
        return False
    return any(
        _PLAN_SECTION_RE.match(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    )


# Три состояния живой половины. ⚠️ Значения — русские слова, НЕ совпадающие ни с одним
# вердиктом отчёта верификации: мета-гейт
# `test_planning_gates_are_independent_of_the_live_verdict.py` ловит вердиктные литералы
# в функциях, называющих живой корень, и состояние, названное вердиктом, покраснело бы
# там на работе, а не на дефекте.
DEFERRED_NO_CANDIDATES = "кандидатов нет"
DEFERRED_UNRECOGNISED = "кандидат не опознан"
DEFERRED_LIVE = "живые есть"


def live_deferred_state(files: list[Path], phases_root: Path) -> tuple[str, list[Path]]:
    """Состояние живой половины по ПОДАННЫМ файлам и корню — чистая функция.

    КАНДИДАТ — файл отложенного, лежащий под `phases_root`. Кандидатов нет —
    `DEFERRED_NO_CANDIDATES` (законная пустота: дописывать отложенное ещё некуда).
    Кандидаты есть, но ни один не несёт раздела плана — `DEFERRED_UNRECOGNISED` со
    списком кандидатов (вакуум: файл есть, требование якоря не предъявлено никому).
    Иначе — `DEFERRED_LIVE` со списком живых.

    Корень и файлы приходят параметрами, а не читаются с живого дерева: иначе все три
    состояния нельзя было бы показать на синтетике, не правя `.planning/`.
    """
    candidates = [path for path in files if phases_root in path.parents]
    if not candidates:
        return DEFERRED_NO_CANDIDATES, []
    live = [path for path in candidates if anchor_is_required(path, phases_root)]
    if not live:
        return DEFERRED_UNRECOGNISED, candidates
    return DEFERRED_LIVE, live


def unrecognised_report(candidates: list[Path], base: Path) -> str:
    """Текст отказа состояния `DEFERRED_UNRECOGNISED`: каждый кандидат назван путём."""
    listed = "\n".join(f"  — {path.relative_to(base)}" for path in candidates)
    return (
        "файл отложенного под `.planning/phases/` есть, но разделов плана в нём нет — "
        "требование якоря не предъявлено никому, правило зеленело бы впустую:\n"
        f"{listed}"
    )


# ЛЕТОПИСЬ УСЛОВИЯ ПРОПУСКА (план 16-01, 2026-10-08): до плана 16-01 пропуск ставился,
# только когда в `.planning/phases/` не было ни одного каталога фазы (помощник
# `_require_live_phases`); старт вехи v2.2 (коммит `36f01b39`: каталог фазы 16 есть,
# файла отложенного нет) показал третье состояние, и правило краснело на законной
# пустоте; различитель — наличие КАНДИДАТА, а не каталога. Состояние «`.planning/phases/`
# пуст» (между вехами) — частный случай отсутствия кандидатов, отдельной ветки не нужно.
# Вакуум по-прежнему красный: кандидат есть, а опознанного живого нет.
def _live_deferred_or_skip(files: list[Path]) -> list[Path]:
    """Живые файлы отложенного; законная пустота — пропуск С ИМЕНЕМ ПРИЧИНЫ, вакуум — отказ."""
    state, subjects = live_deferred_state(files, LIVE_PHASES_ROOT)
    if state == DEFERRED_NO_CANDIDATES:
        pytest.skip(
            "в живых фазах `.planning/phases/` нет ни одного файла `deferred-items.md` — "
            "дописывать отложенное ещё некуда (старт вехи либо фаза без отложенного); "
            "архивные файлы проверены правилом append-safe"
        )
    if state == DEFERRED_UNRECOGNISED:
        pytest.fail(unrecognised_report(subjects, PROJECT_ROOT))
    return subjects


def _report(path: Path, findings: list[Finding]) -> str:
    listed = "\n".join(f"  — {item}" for item in findings)
    return f"{path.relative_to(PROJECT_ROOT)}:\n{listed}"


# --- сам гейт ----------------------------------------------------------------------


def test_every_deferred_items_file_stays_append_safe():
    """ПОВТОРНАЯ ПРАВКА ОТЛОЖЕННОГО НЕОТЛИЧИМА ОТ ПЕРВОЙ — у ВСЕХ файлов дерева.

    Антивакуумная половина «файлов найдено больше нуля» идёт ПЕРВОЙ и называет числа:
    правило, не нашедшее ни одного файла отложенного, зеленело бы само собой — то есть
    ровно тогда, когда каталог переехал и сторожить стало нечего.

    ⚠️ ПОРЯДОК НЕСУЩИЙ (план 16-01). Проверка ВСЕХ файлов дерева (архив включительно)
    идёт ВТОРОЙ, живая половина `_live_deferred_or_skip` — ПОСЛЕДНЕЙ: законный пропуск
    старта вехи никогда не снимает проверку архивных файлов, а вакуум живой половины
    (кандидат есть, не опознан) краснит правило после неё.
    """
    files = deferred_files()
    assert files, (
        "в дереве планирования не найдено ни одного файла отложенного — обход "
        f"ищет `{DEFERRED_FILE_NAME}` под {PLANNING_ROOT.relative_to(PROJECT_ROOT)}"
    )

    reports = []
    for path in files:
        findings = deferred_items_findings(
            path.read_text(encoding="utf-8"),
            anchor_required=anchor_is_required(path),
        )
        if findings:
            reports.append(_report(path, findings))

    assert not reports, "\n".join(reports)

    live = _live_deferred_or_skip(files)
    assert live, "живая половина вернула пустой перечень — помощник обязан был отказать"


def test_the_anchor_closes_every_live_deferred_file():
    """ЯКОРЬ СТОИ́Т ПОСЛЕДНИМ СОДЕРЖАТЕЛЬНЫМ ЭЛЕМЕНТОМ, а не где придётся.

    Якорь посреди файла разделил бы перечень надвое, и «внести перед якорем»
    означало бы для двух авторов два разных места.
    """
    live = _live_deferred_or_skip(deferred_files())
    assert live, "живых файлов отложенного не найдено — сторожить нечего"

    for path in live:
        lines = [
            line
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert lines, f"{path.relative_to(PROJECT_ROOT)} пуст"
        assert lines[-1].strip() == DEFERRED_END_ANCHOR, (
            f"{path.relative_to(PROJECT_ROOT)}: последний содержательный элемент — "
            f"«{lines[-1].strip()}», а обязан быть якорем `{DEFERRED_END_ANCHOR}`"
        )

        # Проза шапки обязана называть якорь ДОСЛОВНО: правило, известное только
        # прогону, автор правки узнаёт из отказа, а не до него. Упоминание сверх
        # самой точки внесения — то есть вхождений строго больше одного.
        raw = path.read_text(encoding="utf-8")
        assert raw.count(DEFERRED_END_ANCHOR) > len(_anchor_lines(raw)), (
            f"{path.relative_to(PROJECT_ROOT)}: якорь стои́т, но шапка файла его не "
            "называет — правило внесения ПЕРЕД якорем нигде не объявлено, и автор "
            "правки узнает о нём только из отказа прогона"
        )


# --- зубы: синтетические тексты, выписанные ЛИТЕРАЛАМИ, а не снятые с дерева --------

# ⚠️ НЕЦИКЛИЧНОСТЬ. Все три текста ниже выписаны здесь целиком и НЕ строятся из
# боевого файла отложенного: контроль, собирающий негодный вход из проверяемого,
# доказывал бы согласие правила с самим собой, а не его зубы.

_SYNTHETIC_WITH_A_DOUBLED_SECTION = "\n".join(
    [
        "# Синтетическое отложенное",
        "",
        "## План 99-01",
        "",
        "### Находка первая",
        "",
        "## План 99-02",
        "",
        "### Находка вторая",
        "",
        "## План 99-01",
        "",
        "### Тот же раздел, внесённый вторым прогоном",
        "",
        DEFERRED_END_ANCHOR,
    ]
)

_SYNTHETIC_WITHOUT_AN_ANCHOR = "\n".join(
    [
        "# Синтетическое отложенное",
        "",
        "## План 99-01",
        "",
        "### Находка первая",
        "",
        "## План 99-02",
        "",
        "### Находка вторая",
    ]
)

_SYNTHETIC_WITH_TWO_ANCHORS = "\n".join(
    [
        "# Синтетическое отложенное",
        "",
        DEFERRED_END_ANCHOR,
        "",
        "## План 99-01",
        "",
        "### Находка первая",
        "",
        DEFERRED_END_ANCHOR,
    ]
)

_SYNTHETIC_APPEND_SAFE = "\n".join(
    [
        "# Синтетическое отложенное",
        "",
        "## План 99-01",
        "",
        "### Находка первая",
        "",
        "## План 99-02",
        "",
        "### Находка вторая",
        "",
        DEFERRED_END_ANCHOR,
    ]
)


def test_a_section_written_twice_is_caught():
    """Негативный контроль 1: второй раздел того же плана краснит правило.

    Дословный класс окна 70: раздел, внесённый дописыванием в конец, на втором
    прогоне встаёт вторым.
    """
    findings = deferred_items_findings(_SYNTHETIC_WITH_A_DOUBLED_SECTION)

    assert len(findings) == 1, "\n".join(str(item) for item in findings)
    only = findings[0]
    assert only.reason == REASON_DUPLICATE_SECTION
    assert "99-01" in only.detail, (
        f"сообщение обязано назвать ПЛАН, чей раздел удвоен: {only.detail}"
    )
    assert "3" in only.detail and "11" in only.detail, (
        "сообщение обязано назвать ОБА вхождения строками — иначе следующий "
        f"автор «починит» не то: {only.detail}"
    )


def test_a_file_without_the_anchor_is_caught():
    """Негативный контроль 2: ДРУГОЕ основание — вносить раздел некуда, кроме конца."""
    findings = deferred_items_findings(_SYNTHETIC_WITHOUT_AN_ANCHOR)

    assert len(findings) == 1, "\n".join(str(item) for item in findings)
    only = findings[0]
    assert only.reason == REASON_ANCHOR_MISSING
    assert only.reason != REASON_DUPLICATE_SECTION
    assert DEFERRED_END_ANCHOR in only.detail


def test_a_file_with_two_anchors_is_caught():
    """Негативный контроль 3: ТРЕТЬЕ основание — точка внесения перестала быть одной."""
    findings = deferred_items_findings(_SYNTHETIC_WITH_TWO_ANCHORS)

    assert len(findings) == 1, "\n".join(str(item) for item in findings)
    only = findings[0]
    assert only.reason == REASON_ANCHOR_DUPLICATED
    assert only.reason not in {REASON_ANCHOR_MISSING, REASON_DUPLICATE_SECTION}
    assert "2" in only.detail


def test_an_append_safe_file_shows_no_finding():
    """Позитивный контроль: без него три негативных не отличали бы работу от красноты всегда."""
    assert deferred_items_findings(_SYNTHETIC_APPEND_SAFE) == []


def test_the_archived_file_is_judged_without_the_anchor_requirement():
    """Изъятие архива названо ЗАМЕРОМ: без якоря архив зелен, удвоение в нём — краснит.

    Изымается ТОЛЬКО требование якоря. Удвоение раздела судится у архива наравне
    с живым файлом: дефект, который уже случился, не перестаёт быть дефектом от
    того, что новых дописываний не ждут.
    """
    assert deferred_items_findings(_SYNTHETIC_WITHOUT_AN_ANCHOR, anchor_required=False) == []

    doubled_without_anchor = _SYNTHETIC_WITHOUT_AN_ANCHOR + "\n\n## План 99-01\n"
    findings = deferred_items_findings(doubled_without_anchor, anchor_required=False)
    assert len(findings) == 1, "\n".join(str(item) for item in findings)
    assert findings[0].reason == REASON_DUPLICATE_SECTION


# --- зубы живой половины: три состояния на синтетическом корне (план 16-01) ----------

# ⚠️ НЕЦИКЛИЧНОСТЬ — та же, что выше: тексты выписаны литералами, файлы кладутся в
# `tmp_path`, а не в `.planning/`. Правка живого дерева ради контроля была бы правкой
# того, что проверяется.

_SYNTHETIC_LIVE_WITHOUT_A_PLAN_SECTION = "\n".join(
    [
        "# Синтетическое отложенное без разделов плана",
        "",
        "## DEF-90-01",
        "",
        "### Находка, именованная находкой, а не планом",
    ]
)

_SYNTHETIC_LIVE_WITH_A_PLAN_SECTION = "\n".join(
    [
        "# Синтетическое отложенное",
        "",
        f"Разделы вносятся ПЕРЕД якорем `{DEFERRED_END_ANCHOR}`.",
        "",
        "## План 90-01",
        "",
        "### Находка первая",
        "",
        DEFERRED_END_ANCHOR,
    ]
)


def _plant(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_control_an_unrecognised_live_candidate_is_named(tmp_path):
    """Вакуум: кандидат под `phases/` без раздела плана — `DEFERRED_UNRECOGNISED`, путь назван.

    Без этого контроля развилка старта вехи могла бы зеленеть и там, где файл
    отложенного в живой фазе есть, но правило якоря никому не предъявлено.
    """
    phases_root = tmp_path / "phases"
    planted = _plant(
        phases_root, "90-sintetika/deferred-items.md", _SYNTHETIC_LIVE_WITHOUT_A_PLAN_SECTION
    )

    state, subjects = live_deferred_state([planted], phases_root)

    assert state == DEFERRED_UNRECOGNISED, state
    assert subjects == [planted], subjects
    report = unrecognised_report(subjects, tmp_path)
    assert "phases/90-sintetika/deferred-items.md" in report, report
    assert state != DEFERRED_NO_CANDIDATES, "вакуум не обязан выглядеть законной пустотой"


def test_control_a_recognised_live_candidate_is_live(tmp_path):
    """Позитивная пара: тот же путь с разделом `## План 90-01` и якорем — `DEFERRED_LIVE`.

    Это и есть состояние после волны, если исполнитель фазы заведёт живой файл
    отложенного с разделом плана: правило не пропускается, а судит его.
    """
    phases_root = tmp_path / "phases"
    planted = _plant(
        phases_root, "90-sintetika/deferred-items.md", _SYNTHETIC_LIVE_WITH_A_PLAN_SECTION
    )

    state, subjects = live_deferred_state([planted], phases_root)

    assert state == DEFERRED_LIVE, state
    assert subjects == [planted], subjects
    assert deferred_items_findings(planted.read_text(encoding="utf-8")) == []


def test_control_an_archive_only_tree_has_no_live_candidates(tmp_path):
    """Законная пустота: файл только в архиве вехи (с разделом плана) — `DEFERRED_NO_CANDIDATES`.

    Раздел плана у архивного файла живым его не делает: граница — корень `phases/`,
    а не форма текста.
    """
    phases_root = tmp_path / "phases"
    phases_root.mkdir()
    archived = _plant(
        tmp_path,
        "milestones/v9.8-phases/90-x/deferred-items.md",
        _SYNTHETIC_LIVE_WITH_A_PLAN_SECTION,
    )

    state, subjects = live_deferred_state([archived], phases_root)

    assert state == DEFERRED_NO_CANDIDATES, state
    assert subjects == [], subjects
