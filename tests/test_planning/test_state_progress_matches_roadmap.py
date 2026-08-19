"""Машинно читаемый счёт планов ВЫВОДИТСЯ из ROADMAP, а не набирается руками.

ЗАЧЕМ. Расхождение `.planning/STATE.md` с `.planning/ROADMAP.md` внесено
ИНСТРУМЕНТОМ трекинга, а не автором записи, и коммиты названы поимённо:
`4430ef4` (трекинг волны 18) правил ОБА файла; `ada9500` и `1e80cb5` (трекинг
волн 19 и 20) правили ТОЛЬКО ROADMAP; `6ade68e` («update tracking after wave
21») привёл значения обратно — и механизма не завёл, поэтому следующий коммит
трекинга мог обойти файл снова. Раунд 7 нашёл расхождение спустя ОДИН раунд
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

from dataclasses import dataclass
from pathlib import Path

import yaml

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
