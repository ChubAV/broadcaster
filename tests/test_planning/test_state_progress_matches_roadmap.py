"""Машинно читаемый счёт планов ВЫВОДИТСЯ из ROADMAP, а не набирается руками.

ЗАЧЕМ. Расхождение `.planning/STATE.md` с `.planning/ROADMAP.md` внесено
ИНСТРУМЕНТОМ трекинга, а не автором записи, и коммиты названы поимённо:
`4430ef4` (трекинг волны 18) правил ОБА файла; `ada9500`, `1e80cb5` и `6ade68e`
(трекинг волн 19, 20 и 21) правили ТОЛЬКО ROADMAP — три обхода подряд. Значения
свело обратно `75fbdfa`, коммит ВЕРИФИКАЦИИ раунда 7, а не шага трекинга: то
есть чинил расхождение не тот, кто его вносил, и механизма это не завело —
следующий коммит трекинга мог обойти файл снова. Раунд 7 нашёл расхождение спустя ОДИН раунд
после того, как оно было закрыто правилом «единственный источник счёта планов —
ROADMAP». Правило существовало; принуждения у него не было. Настоящий модуль и
есть принуждение: он живёт в `tests/` и потому входит в `just test` — команду,
которую в проекте запускают все, — так что коммит, тронувший ROADMAP и обошедший
машинно читаемое поле, краснит прогон. Обходить становится нечего.

⚠️ ЧЕГО ЭТОТ ФАЙЛ НЕ ДОКАЗЫВАЕТ. Он НЕ СУДИТ ПРОЗУ `.planning/STATE.md` — ни
секцию текущей позиции фазы, ни прозаическую строку остановки во frontmatter, ни
прозаическую полосу хода работ: ни одна из них этим модулем не читается вовсе,
разбирается ТОЛЬКО первый блок frontmatter. Он не утверждает, что ROADMAP верен —
ROADMAP объявлен единственным ИСТОЧНИКОМ счёта, и модуль сверяет с ним, а не
проверяет его. Он не утверждает ничего о прочих полях блока `progress`: из пяти
читаются два. И он не знает, отмечен ли план в ROADMAP вовремя, — он знает лишь,
что два места одного счёта говорят одно.

ПОЧЕМУ ЭТО НЕ ОТМЕНА РЕШЕНИЯ D-33. Решение D-33 отказало машинному гейту на
ПРОЗЕ операционного документа с названной причиной: отличить «константу величины,
которую документ не может держать истинной» от законного числа того же документа
(даты, цены, номера ревизии, числа, квалифицированного раундом) машине нечем, и
такой гейт давал бы либо ложные отказы, либо зелень всегда. Здесь предмет ДРУГОЙ:
одно машинно читаемое поле и один объявленный источник, между которыми обязано
держаться равенство. Суждения этот предмет не требует, поэтому D-33 настоящим
модулем НЕ ПЕРЕОТКРЫВАЕТСЯ и НЕ ОТМЕНЯЕТСЯ; документная половина прохибиций
по-прежнему судится человеком.

Разбор ведётся ПО ФОРМЕ СТРОКИ, а не по точному тексту названия плана: правка
формулировки строки ROADMAP не имеет права ронять тест — хрупкий тест отключают,
и вместе с ним отключается свойство.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

# Предмет модуля — ЗАПИСЬ проекта, а не его продукт. Основание маркера, его
# граница годности и запрет выключать каталог — `tests/test_planning/__init__.py`;
# само имя объявлено хуком в `tests/conftest.py`.
pytestmark = pytest.mark.planning

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROADMAP_PATH = PROJECT_ROOT / ".planning" / "ROADMAP.md"
STATE_PATH = PROJECT_ROOT / ".planning" / "STATE.md"

FRONTMATTER_FENCE = "---"
PHASE_SECTION_PREFIX = "### Phase "
EXECUTED_PLAN_PREFIX = "- [x] "
PLANNED_PLAN_PREFIX = "- [ ] "

TOTAL_PLANS_FIELD = "total_plans"
COMPLETED_PLANS_FIELD = "completed_plans"


# --- вывод счёта из объявленного источника -----------------------------------------


def roadmap_plan_counts(text: str) -> dict[str, tuple[int, int]]:
    """Счёт планов по разделам `### Phase N:` — «исполнено / всего».

    Раздел открывается заголовком и закрывается следующим заголовком того же
    уровня. Внутри раздела считаются строки, начинающиеся с `- [x] ` и `- [ ] `.
    Раздел без перечня планов даёт `(0, 0)` и разбор не роняет: фаза, планы
    которой ещё не написаны, — штатное состояние roadmap, а не дефект.
    """
    counts: dict[str, tuple[int, int]] = {}
    section: str | None = None

    for line in text.splitlines():
        if line.startswith(PHASE_SECTION_PREFIX):
            section = line[len(PHASE_SECTION_PREFIX) :].strip()
            counts.setdefault(section, (0, 0))
            continue
        if section is None:
            continue
        stripped = line.lstrip()
        executed, total = counts[section]
        if stripped.startswith(EXECUTED_PLAN_PREFIX):
            counts[section] = (executed + 1, total + 1)
        elif stripped.startswith(PLANNED_PLAN_PREFIX):
            counts[section] = (executed, total + 1)

    return counts


def roadmap_totals(text: str) -> tuple[int, int]:
    """Сумма по ВСЕМ разделам: `(исполнено, всего)`."""
    per_phase = roadmap_plan_counts(text)
    executed = sum(pair[0] for pair in per_phase.values())
    total = sum(pair[1] for pair in per_phase.values())
    return executed, total


# Строка перечня планов раздела фазы. Форм в роадмапе НЕСКОЛЬКО, и опознаётся
# РОВНО ОДНА — «N планов, из них M исполнено». Остальные («7 планов — 3 исходных
# …», «11/11 plans executed …», «TBD») пропускаются МОЛЧА, и молчание это
# названо числом в антивакуумной половине правила, а не оставлено на догадку:
# правило, не нашедшее ни одной прозы опознаваемой формы, зеленело бы само собой —
# то есть ровно тогда, когда форма прозы сменилась целиком.
PLANS_PROSE_PREFIX = "**Plans**"
_PLANS_PROSE_RE = re.compile(
    r"(?P<total>\d+)\s+планов,\s+из\s+них\s+(?P<executed>\d+)\s+исполнено"
)


def roadmap_plan_prose(text: str) -> dict[str, tuple[int, int]]:
    """Карта «раздел фазы → пара чисел ПРОЗЫ» — «исполнено / всего».

    Читается ТОЛЬКО строка перечня планов раздела и ТОЛЬКО опознаваемая форма.
    Раздел, чья строка написана иначе либо отсутствует, в карту не попадает
    вовсе — это НЕ ноль: ноль означал бы «проза объявила ноль планов», и смешение
    этих двух вещей изъяло бы раздел из правила молча.
    """
    prose: dict[str, tuple[int, int]] = {}
    section: str | None = None

    for line in text.splitlines():
        if line.startswith(PHASE_SECTION_PREFIX):
            section = line[len(PHASE_SECTION_PREFIX) :].strip()
            continue
        if section is None or not line.startswith(PLANS_PROSE_PREFIX):
            continue
        match = _PLANS_PROSE_RE.search(line)
        if match is not None:
            prose.setdefault(
                section,
                (int(match.group("executed")), int(match.group("total"))),
            )

    return prose


@dataclass(frozen=True)
class ProseDivergence:
    """Расхождение ПРОЗЫ раздела с его ОТМЕТКАМИ: раздел, что сказано, что отмечено.

    ⚠️ ПОЧЕМУ ЭТО СОСЕДНИЙ ТИП, А НЕ `Divergence`, И РАЗНИЦА НАЗЫВАЕТСЯ. Поля те
    же по смыслу — величина, выведенное, записанное, — но `Divergence` называет
    ПОЛЕ frontmatter `.planning/STATE.md`, а у прозаической строки роадмапа поля
    нет вовсе и файл другой. Переиспользование положило бы в сообщение об отказе
    ЧУЖОЕ имя файла, и следующий автор «починил» бы не тот документ. Сверх того
    здесь обязателен РАЗДЕЛ: расхождений может быть несколько, и без имени
    раздела они неразличимы.
    """

    section: str
    quantity: str
    prose: int
    marks: int

    def __str__(self) -> str:
        return (
            f"раздел `{PHASE_SECTION_PREFIX}{self.section}` файла "
            f"`.planning/ROADMAP.md`: проза строки `{PLANS_PROSE_PREFIX}` говорит "
            f"{self.prose} ({self.quantity}), а ОТМЕТОК перечня — {self.marks}; "
            "привести надо ПРОЗУ, потому что источником счёта планов объявлены "
            "отметки, и действующий гейт читает именно их"
        )


def prose_divergence(roadmap_text: str) -> list[ProseDivergence]:
    """Расхождения прозы с отметками ПО ВСЕМ разделам. Пустой список — согласие.

    ⚠️ ЧИСЛО ИСПОЛНЕННЫХ В ПРОЗЕ СЛИЧАЕТСЯ С ЧИСЛОМ ОТМЕТОК, А НЕ СО ЧИСЛОМ
    СВОДОК. Сводка есть свидетельство завершения, а отметку ставит оркестратор;
    сличение с иным источником краснело бы на состоянии оркестратора, а не на
    расхождении записи, — и правило чинили бы правкой не того документа.
    """
    marks = roadmap_plan_counts(roadmap_text)
    prose = roadmap_plan_prose(roadmap_text)

    divergences: list[ProseDivergence] = []
    for section, (prose_executed, prose_total) in prose.items():
        marks_executed, marks_total = marks.get(section, (0, 0))
        if prose_total != marks_total:
            divergences.append(
                ProseDivergence(
                    section=section,
                    quantity="всего планов",
                    prose=prose_total,
                    marks=marks_total,
                )
            )
        if prose_executed != marks_executed:
            divergences.append(
                ProseDivergence(
                    section=section,
                    quantity="исполнено планов",
                    prose=prose_executed,
                    marks=marks_executed,
                )
            )
    return divergences


def _frontmatter(text: str) -> str:
    lines = text.splitlines()
    assert lines and lines[0].strip() == FRONTMATTER_FENCE, (
        "документ не открывается блоком frontmatter — читать поле счёта неоткуда"
    )
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_FENCE:
            return "\n".join(lines[1:index])
    raise AssertionError("блок frontmatter не закрыт — читать поле счёта неоткуда")


def state_progress(text: str) -> tuple[int, int]:
    """`(completed_plans, total_plans)` из блока `progress` frontmatter.

    Прозу документа функция не читает и не имеет права читать: это граница,
    отделяющая настоящий гейт от того, от которого отказалось решение D-33.
    """
    data = yaml.safe_load(_frontmatter(text)) or {}
    progress = data.get("progress") or {}
    assert COMPLETED_PLANS_FIELD in progress and TOTAL_PLANS_FIELD in progress, (
        "во frontmatter нет блока `progress` с полями "
        f"`{COMPLETED_PLANS_FIELD}` и `{TOTAL_PLANS_FIELD}`"
    )
    return int(progress[COMPLETED_PLANS_FIELD]), int(progress[TOTAL_PLANS_FIELD])


@dataclass(frozen=True)
class Divergence:
    """Расхождение одной величины: что выведено, что записано и что править."""

    field: str
    derived: int
    recorded: int

    def __str__(self) -> str:
        return (
            f"поле `progress.{self.field}` во frontmatter `.planning/STATE.md` "
            f"записано как {self.recorded}, а из отметок `.planning/ROADMAP.md` "
            f"выводится {self.derived} — привести надо ПОЛЕ, потому что источником "
            f"счёта планов объявлен ROADMAP"
        )


def progress_divergence(roadmap_text: str, state_text: str) -> list[Divergence]:
    """Список расхождений выведенного счёта с записанным. Пустой — согласие."""
    derived_completed, derived_total = roadmap_totals(roadmap_text)
    recorded_completed, recorded_total = state_progress(state_text)

    divergences: list[Divergence] = []
    if derived_total != recorded_total:
        divergences.append(
            Divergence(
                field=TOTAL_PLANS_FIELD,
                derived=derived_total,
                recorded=recorded_total,
            )
        )
    if derived_completed != recorded_completed:
        divergences.append(
            Divergence(
                field=COMPLETED_PLANS_FIELD,
                derived=derived_completed,
                recorded=recorded_completed,
            )
        )
    return divergences


def _report(divergences: list[Divergence]) -> str:
    return "\n".join(str(item) for item in divergences)


# --- сам гейт ----------------------------------------------------------------------


def test_the_machine_readable_progress_is_derived_from_the_roadmap():
    """МАШИННО ЧИТАЕМЫЙ СЧЁТ РАВЕН ВЫВЕДЕННОМУ ИЗ ОБЪЯВЛЕННОГО ИСТОЧНИКА.

    Числовых констант счёта в теле нет вовсе — оно их ВЫВОДИТ. Константа сделала
    бы тест хрупким ровно к тому событию, ради которого он написан: появление
    следующего плана требовало бы правки теста, а тест, требующий правки при
    каждом плане, отключают.
    """
    divergences = progress_divergence(
        ROADMAP_PATH.read_text(encoding="utf-8"),
        STATE_PATH.read_text(encoding="utf-8"),
    )
    assert not divergences, _report(divergences)


def test_the_prose_plan_counts_agree_with_the_marks():
    """ПРОЗА О ЧИСЛЕ ПЛАНОВ РАВНА ОТМЕТКАМ СВОЕГО РАЗДЕЛА.

    ЗАЧЕМ ОТДЕЛЬНОЕ ПРАВИЛО ПРИ ЖИВОМ ГЕЙТЕ ВЫШЕ. Действующий гейт читает ОТМЕТКИ
    и прозы не видит ПО ПОСТРОЕНИЮ — и ровно поэтому строка `**Plans**` Фазы 10
    прожила устаревшей целую партию, объявляя «40 планов, из них 34 исполнено»
    при сорока отметках. Собственная идиома фазы («прежнее значение не было
    ошибкой — оно устарело») САМА устарела на ту партию, которая её дописывала.
    Пока принуждения нет, расхождение прозы с деревом ловит только круг ревизии.

    ⚠️ АНТИВАКУУМНАЯ ПОЛОВИНА ИДЁТ ПЕРВОЙ И НАЗЫВАЕТ ЧИСЛА. Разделов фаз найдено
    не ноль; разделов с прозой опознаваемой формы — не ноль; число опознанных и
    число пропущенных названо в тексте утверждения. Без этого правило зеленело бы
    на роадмапе, где форма прозы сменилась целиком, — то есть ровно тогда, когда
    оно нужнее всего.
    """
    roadmap_text = ROADMAP_PATH.read_text(encoding="utf-8")

    sections = roadmap_plan_counts(roadmap_text)
    assert sections, (
        "в `.planning/ROADMAP.md` не найдено ни одного раздела "
        f"`{PHASE_SECTION_PREFIX}` — разбор прочёл бы пустоту, и правило зеленело "
        "бы ВАКУУМОМ"
    )

    prose = roadmap_plan_prose(roadmap_text)
    skipped = len(sections) - len(prose)
    assert prose, (
        f"разделов фаз найдено {len(sections)}, из них с прозой опознаваемой формы "
        f"«N планов, из них M исполнено» — 0, пропущено {skipped}: форма прозы "
        "сменилась целиком, и сличать стало нечего. Правило обязано покраснеть "
        "ЗДЕСЬ, а не зазеленеть впустую"
    )

    divergences = prose_divergence(roadmap_text)
    assert not divergences, (
        f"опознано разделов с прозой: {len(prose)}, пропущено: {skipped}.\n"
        + "\n".join(str(item) for item in divergences)
    )


# --- зубы: синтетические пары, а не правка настоящих файлов -------------------------


def _synthetic_roadmap(*, executed: int, planned: int) -> str:
    lines = [
        "# Синтетический roadmap",
        "",
        "### Phase 1: Синтетическая фаза",
        "",
        "Plans:",
        "",
    ]
    lines += [
        f"- [x] СИНТ-{index}-PLAN.md — исполненный план" for index in range(executed)
    ]
    lines += [
        f"- [ ] СИНТ-{index}-PLAN.md — запланированный план"
        for index in range(executed, executed + planned)
    ]
    lines += ["", "### Phase 2: Фаза без перечня планов", "", "**Plans**: TBD", ""]
    return "\n".join(lines)


def _synthetic_state(*, completed: int, total: int) -> str:
    return "\n".join(
        [
            FRONTMATTER_FENCE,
            "current_phase: 01",
            "progress:",
            f"  {TOTAL_PLANS_FIELD}: {total}",
            f"  {COMPLETED_PLANS_FIELD}: {completed}",
            FRONTMATTER_FENCE,
            "",
            "# Синтетическое состояние",
            "",
            "Проза, которой гейт не читает.",
        ]
    )


# Воспроизведение РОВНО той пары, которую раунд 7 нашёл на дереве и назвал
# регрессией против закрытого гэпа 3 раунда 5: ROADMAP отмечает исполненными
# больше планов, чем держит машинно читаемое поле состояния. Числа стоят ТОЛЬКО
# в самих синтетических текстах ниже и больше нигде в модуле.
_SYNTHETIC_ROADMAP_OF_THE_ROUND_SEVEN_TREE = _synthetic_roadmap(executed=78, planned=3)
_SYNTHETIC_STATE_OF_THE_ROUND_SEVEN_REGRESSION = _synthetic_state(
    completed=73, total=81
)
_SYNTHETIC_STATE_AGREEING_WITH_THAT_ROADMAP = _synthetic_state(completed=78, total=81)
_SYNTHETIC_ROADMAP_WITH_ONE_MORE_UNCHECKED_PLAN = _synthetic_roadmap(
    executed=78, planned=4
)


def test_the_helper_catches_the_round_seven_regression():
    """Негативный контроль 1: пара раунда 7 краснит помощника, называя ОБА числа."""
    divergences = progress_divergence(
        _SYNTHETIC_ROADMAP_OF_THE_ROUND_SEVEN_TREE,
        _SYNTHETIC_STATE_OF_THE_ROUND_SEVEN_REGRESSION,
    )

    assert len(divergences) == 1, _report(divergences)
    only = divergences[0]
    assert only.field == COMPLETED_PLANS_FIELD
    derived_completed, _ = roadmap_totals(_SYNTHETIC_ROADMAP_OF_THE_ROUND_SEVEN_TREE)
    recorded_completed, _ = state_progress(
        _SYNTHETIC_STATE_OF_THE_ROUND_SEVEN_REGRESSION
    )
    assert only.derived == derived_completed
    assert only.recorded == recorded_completed
    message = str(only)
    assert str(derived_completed) in message and str(recorded_completed) in message, (
        "сообщение об отказе обязано называть ОБА числа — иначе следующий автор "
        f"«починит» не то: {message}"
    )
    assert "STATE.md" in message and "ROADMAP.md" in message, (
        f"сообщение обязано называть файл с полем, которое надо привести: {message}"
    )


def test_a_newly_added_unchecked_plan_raises_the_total():
    """Негативный контроль 2: добавленный неотмеченный план краснит устаревший счёт.

    Это второй способ обойти STATE — не отметить исполненный план, а ДОБАВИТЬ
    новый и не тронуть поле. Первый контроль его не покрывает: там расходится
    `completed_plans`, здесь — `total_plans`.
    """
    divergences = progress_divergence(
        _SYNTHETIC_ROADMAP_WITH_ONE_MORE_UNCHECKED_PLAN,
        _SYNTHETIC_STATE_AGREEING_WITH_THAT_ROADMAP,
    )

    assert len(divergences) == 1, _report(divergences)
    only = divergences[0]
    assert only.field == TOTAL_PLANS_FIELD
    assert only.derived == only.recorded + 1, str(only)


def test_an_agreeing_pair_shows_no_divergence():
    """Позитивный контроль: без него негативные не отличали бы работу от красноты всегда."""
    divergences = progress_divergence(
        _SYNTHETIC_ROADMAP_OF_THE_ROUND_SEVEN_TREE,
        _SYNTHETIC_STATE_AGREEING_WITH_THAT_ROADMAP,
    )
    assert not divergences, _report(divergences)


def test_a_phase_without_a_plan_list_is_counted_as_empty():
    """Раздел без перечня планов даёт `(0, 0)` и разбор не роняет."""
    counts = roadmap_plan_counts(_SYNTHETIC_ROADMAP_OF_THE_ROUND_SEVEN_TREE)
    empty = [pair for pair in counts.values() if pair == (0, 0)]
    assert empty, "раздел без перечня планов обязан быть отобран и посчитан пустым"


# --- зубы правила согласия прозы с отметками ---------------------------------------

# ⚠️ НЕЦИКЛИЧНОСТЬ. Оба текста ниже выписаны ЛИТЕРАЛАМИ целиком и не строятся из
# `.planning/ROADMAP.md`: контроль, собирающий негодный вход из проверяемого,
# доказывал бы согласие правила с самим собой. Ожидания в контролях тоже
# литеральные и из живого роадмапа не выводятся.

_SYNTHETIC_ROADMAP_WHOSE_PROSE_LAGS = """# Синтетический roadmap

### Phase 1: Синтетическая фаза с прозой

**Plans**: 3 планов, из них 1 исполнено

- [x] СИНТ-1-PLAN.md — исполненный план
- [x] СИНТ-2-PLAN.md — исполненный план
- [ ] СИНТ-3-PLAN.md — запланированный план

### Phase 2: Фаза с прозой иной формы

**Plans**: 11/11 plans executed в 4 волнах
"""

_SYNTHETIC_ROADMAP_WITHOUT_RECOGNISABLE_PROSE = """# Синтетический roadmap

### Phase 1: Фаза с прозой иной формы

**Plans**: 7 планов — 3 исходных плюс 4 плана закрытия разрывов

- [x] СИНТ-1-PLAN.md — исполненный план
- [ ] СИНТ-2-PLAN.md — запланированный план

### Phase 2: Фаза без перечня планов

**Plans**: TBD
"""


def test_the_prose_helper_catches_a_stale_prose_line():
    """Негативный контроль 1: проза отстала от отметок — ровно одна находка с ОБОИМИ числами.

    Дословный класс предупреждения восьмого круга: отметок два, проза говорит
    одно. Числа стоя́т ТОЛЬКО в литеральном тексте выше и в ожиданиях здесь.
    """
    divergences = prose_divergence(_SYNTHETIC_ROADMAP_WHOSE_PROSE_LAGS)

    assert len(divergences) == 1, "\n".join(str(item) for item in divergences)
    only = divergences[0]
    assert only.section == "1: Синтетическая фаза с прозой"
    assert only.prose == 1 and only.marks == 2, str(only)
    message = str(only)
    assert "1" in message and "2" in message, (
        f"сообщение обязано называть ОБА числа: {message}"
    )
    assert "ROADMAP.md" in message, (
        f"сообщение обязано называть файл, который надо привести: {message}"
    )
    assert "Синтетическая фаза с прозой" in message, (
        f"сообщение обязано называть РАЗДЕЛ — иначе находки неразличимы: {message}"
    )


def test_the_prose_helper_finds_nothing_when_no_prose_is_recognised():
    """Негативный контроль 2: прозы опознаваемой формы нет — сличать НЕЧЕГО, и это ловит вакуум.

    Правило само по себе даёт пустоту (расхождений нет, потому что нет и входа);
    краснеть обязана АНТИВАКУУМНАЯ половина. Здесь показано ОБА факта разом:
    карта прозы пуста при непустой карте отметок.
    """
    text = _SYNTHETIC_ROADMAP_WITHOUT_RECOGNISABLE_PROSE

    assert roadmap_plan_counts(text), (
        "разделы фаз в синтетике есть — иначе контроль показывал бы не вакуум "
        "прозы, а вакуум разбора"
    )
    assert roadmap_plan_prose(text) == {}, (
        "ни одна из двух форм синтетики не имеет права быть опознанной: "
        "«7 планов — 3 исходных …» и «TBD»"
    )
    assert prose_divergence(text) == [], (
        "без опознанной прозы расхождений нет ПО ПОСТРОЕНИЮ — именно поэтому "
        "пустая карта прозы обязана краснить антивакуумную половину гейта, а не "
        "проходить его зелёной"
    )
