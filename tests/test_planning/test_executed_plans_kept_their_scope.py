"""Исторический запрет исполненного плана держится ПРОВЕРКОЙ ЕГО СОБСТВЕННЫХ КОММИТОВ.

ЗАЧЕМ. Четырнадцать запретов Фазы 10 объявили `verification: test` о фактах вида «этим планом
файл X не правится», а правила в дереве не было (находка D-05 плана 15-13, причина
`declared-rule-absent`). Решение владельца Г-1 «Правила сейчас» (`chubav`, 2026-09-25, прогон
`/gsd-plan-phase 15 --gaps`) требует правило. Исторический факт о плане машинно проверяем
одним честным способом: прочесть коммиты самого плана и пути, которых они касались.

КАК ЧИТАЕТСЯ ИСТОРИЯ. Журнал «коммит → тема → пути» снимается ОДНИМ вызовом `git log`
(`--name-only --no-renames`, от `HEAD`) и кэшируется: живой журнал читается один раз за прогон.
Всё остальное — чистые функции поданного журнала: `_parse_journal` (текст → записи),
`_plan_commits` (отбор коммитов плана по ТЕМЕ) и `_path_offences` (запрещённые пути в них).
Поэтому каждое их свойство показывается контролем на синтетическом журнале, а не заявляется.

ОТБОР ПО ТЕМЕ, А НЕ ПО ТЕЛУ. Коммит плана `10-NN` — тот, чья строка темы начинается
`тип(10-NN):` (номера сличаются без ведущих нулей, `!` после области допустим). Вхождение
`(10-NN)` в тело сообщения или дальше в теме коммит плану не приписывает: коммит планирования
`docs(10): …`, упомянувший план, чужой (замер планирования: `80a0378f` для 10-46, `354e9de3` —
правка файлов планов 10-48…10-51). Тело сообщения журнал не несёт вовсе.

ПУТЬ ЗАПРЕЩЁН, если он равен элементу перечня либо начинается с элемента, оканчивающегося `/`
(каталог). Элемент без `/` — ровно файл: `app/static/css/app.css.bak` запрещённым файлом
`app/static/css/app.css` не является.

АНТИВАКУУМ. Пустой отбор коммитов плана — отказ «коммитов плана 10-NN не найдено», а не пустой
список нарушений: правило, не нашедшее ни одного коммита, ничего о плане не узнало. Так же
отказом, а не зеленью, кончаются пустой перечень запрещённых путей и отбор, в котором коммиты
есть, а путей нет ни одного.

⚠️ ГРАНИЦЫ ПРАВИЛА — НАЗВАНЫ, А НЕ ПОДРАЗУМЕВАЮТСЯ.
1. История обязана быть ПОЛНОЙ: `git rev-parse --is-shallow-repository` обязан ответить `false`.
   Мелкий клон вне области и кончается ОТКАЗОМ с названной причиной ДО разбора журнала, а не
   пропуском: пропуск в мелком клоне зеленил бы правило вакуумом (угроза T-15-100). Любой иной
   ответ (`true`, старый git, эхом возвращающий флаг) — тоже отказ. Каталог без `.git` — отказ
   с текстом ошибки git.
2. Коммит плана БЕЗ ОБЛАСТИ В ТЕМЕ правилу НЕВИДИМ. Часть работы Фазы 10 сделана коммитами
   оркестратора (`fix: …`, `docs(phase-10): …`, `docs(10): …`), которые области плана не несут;
   правка запрещённого пути таким коммитом этим правилом не ловится.
3. ПЕРЕПИСАННАЯ ИСТОРИЯ (перебазирование, `filter-branch`, склейка коммитов) вне области: правило
   судит историю, достижимую из `HEAD` сегодня, а не ту, что была в день исполнения плана.
4. Коммиты слияния путей в журнале не несут (`--name-only` без `-m`); переименование читается
   обеими сторонами (`--no-renames`: удаление старого пути и добавление нового).

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ (D-16). Он не судит вердикт отчёта своей фазы и не читает его. Он
не видит правок, сделанных вне коммитов плана (граница 2), и не утверждает, что запрет соблюдён
ПО ДУХУ за пределами путей: запрет «пять замечаний не чинятся» держится здесь ровно как «файлы,
в которых их чинили бы, не тронуты». Он не утверждает, что план сделал то, что обещал, — только
то, чего план не трогал. И он ничего не говорит о планах, которых нет в `HISTORY_FACTS`.

ПОЧЕМУ ЭТО НЕ ОТМЕНА РЕШЕНИЯ D-33. D-33 отказал машинному гейту на ПРОЗЕ операционного
документа. Предмет здесь другой: машинно читаемый журнал git (тема коммита и пути) и объявленное
перечнем соответствие «план → запрещённые пути». Суждения этот предмет не требует; прочтение
формулировки запрета в перечень путей сделано человеком один раз и записано рядом с каждой
записью `HISTORY_FACTS`.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pytest

# Предмет модуля — ЗАПИСЬ проекта (история исполненных планов), а не его продукт. Основание
# маркера и запрет выключать каталог — `tests/test_planning/__init__.py`.
pytestmark = pytest.mark.planning

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RECORD_SEPARATOR = "\x1e"
FIELD_SEPARATOR = "\x1f"

# ОДИН вызов на весь журнал: `%x1e` открывает запись коммита, `%x1f` делит хэш и тему; пути
# идут следующими строками. `core.quotePath=false` — пути с не-ASCII символами не
# экранируются восьмеричными кодами; `--no-renames` — граница 4 докстринга.
JOURNAL_ARGS = (
    "-c",
    "core.quotePath=false",
    "log",
    "--no-renames",
    "--name-only",
    "--format=%x1e%H%x1f%s",
    "HEAD",
)
SHALLOW_ARGS = ("rev-parse", "--is-shallow-repository")

PLAN_SCOPE = re.compile(r"(\d+)-(\d+)")


class HistoryRefusal(Exception):
    """Отказ с названной причиной: история неполна, журнал неразборчив или отбор пуст."""


@dataclass(frozen=True)
class Commit:
    """Запись журнала: хэш, строка темы, пути, которых коммит касался."""

    sha: str
    subject: str
    paths: tuple[str, ...]


@dataclass(frozen=True)
class PathOffence:
    """Коммит плана, коснувшийся запрещённого пути: КТО, ЧЕГО и каким элементом перечня."""

    sha: str
    subject: str
    path: str
    forbidden: str

    def __str__(self) -> str:
        return f"{self.sha[:8]} «{self.subject}» тронул `{self.path}` (запрет `{self.forbidden}`)"


@dataclass(frozen=True)
class HistoryFact:
    """Исторический факт плана: область темы `10-NN` и пути, которых его коммиты не касаются."""

    scope: str
    forbidden: tuple[str, ...]


# Ключ — тождество строки реестра в форме `10-NN-PLAN.md#i`; значение — область темы и
# запрещённые пути по ПОЛНОЙ формулировке запрета. Заполняется задачей 2 плана 15-30.
HISTORY_FACTS: dict[str, HistoryFact] = {}


# --- журнал ------------------------------------------------------------------------------


def _run_git(*args: str) -> str:
    """Вывод `git <args>` из корня проекта; любой сбой — отказ с текстом ошибки git."""
    try:
        completed = subprocess.run(
            ("git", *args),
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = getattr(error, "stderr", "") or str(error)
        raise HistoryRefusal(f"`git {' '.join(args)}` не исполнился: {detail.strip()}") from error
    return completed.stdout


def _is_shallow(git: Callable[..., str] = _run_git) -> bool:
    """Ответ `git rev-parse --is-shallow-repository`; неразборчивый ответ — отказ."""
    answer = git(*SHALLOW_ARGS).strip()
    if answer in ("true", "false"):
        return answer == "true"
    raise HistoryRefusal(
        f"ответ `git {' '.join(SHALLOW_ARGS)}` неразборчив: {answer!r} — полнота истории не "
        f"установлена, и правило не судит (граница 1)"
    )


def _parse_journal(text: str) -> tuple[Commit, ...]:
    """Текст журнала в форме `JOURNAL_ARGS` → записи «хэш, тема, пути» в порядке журнала."""
    commits: list[Commit] = []
    for chunk in text.split(RECORD_SEPARATOR):
        if not chunk.strip():
            continue
        header, _, body = chunk.partition("\n")
        sha, separator, subject = header.partition(FIELD_SEPARATOR)
        if not separator or not sha:
            raise HistoryRefusal(f"запись журнала без хэша и темы: {chunk[:80]!r}")
        paths = tuple(line for line in body.splitlines() if line.strip())
        commits.append(Commit(sha, subject, paths))
    return tuple(commits)


def _read_journal(git: Callable[..., str] = _run_git) -> tuple[Commit, ...]:
    """Журнал истории; мелкий клон — отказ ДО чтения и разбора журнала (граница 1)."""
    if _is_shallow(git):
        raise HistoryRefusal(
            "мелкий клон: история укорочена, и коммиты исполненных планов могли не дойти — "
            "правило не судит неполную историю и не пропускается (граница 1); нужен полный "
            "клон (`git fetch --unshallow`)"
        )
    return _parse_journal(git(*JOURNAL_ARGS))


@cache
def _git_journal() -> tuple[Commit, ...]:
    """Живой журнал, прочитанный один раз за прогон."""
    return _read_journal()


# --- чистые функции поданного журнала ------------------------------------------------------


def _plan_commits(journal: Iterable[Commit], scope: str) -> tuple[Commit, ...]:
    """Коммиты плана `scope` (`10-44`) — по ОБЛАСТИ В ТЕМЕ; пустой отбор — отказ."""
    match = PLAN_SCOPE.fullmatch(scope)
    if match is None:
        raise HistoryRefusal(f"область `{scope}` не в форме `ФАЗА-ПЛАН`")
    phase, plan = int(match[1]), int(match[2])
    subject_scope = re.compile(rf"^[a-z]+\(0*{phase}-0*{plan}\)!?:")
    selected = tuple(commit for commit in journal if subject_scope.match(commit.subject))
    if not selected:
        raise HistoryRefusal(
            f"коммитов плана {scope} не найдено: ни одна тема журнала не начинается "
            f"`тип({scope}):` — правило ничего о плане не узнало и не зеленеет (антивакуум)"
        )
    return selected


def _path_offences(
    commits: Iterable[Commit], forbidden: Iterable[str]
) -> list[PathOffence]:
    """Каждый путь поданных коммитов, запрещённый перечнем, — с коммитом и элементом перечня."""
    forbidden = tuple(forbidden)
    if not forbidden:
        raise HistoryRefusal("перечень запрещённых путей пуст: запрещать нечего, и правило не судит")
    commits = tuple(commits)
    if not any(commit.paths for commit in commits):
        raise HistoryRefusal(
            f"у {len(commits)} поданных коммитов нет ни одного пути — журнал снят без "
            f"`--name-only` либо разбор выродился (антивакуум)"
        )
    offences: list[PathOffence] = []
    for commit in commits:
        for path in commit.paths:
            for item in forbidden:
                if path == item or (item.endswith("/") and path.startswith(item)):
                    offences.append(PathOffence(commit.sha, commit.subject, path, item))
    return offences


# --- контроли на синтетическом журнале -------------------------------------------------------

PLAN_COMMIT = Commit("a" * 40, "feat(10-44): правка плана", ("tests/test_planning/y.py",))
PADDED_PLAN_COMMIT = Commit("b" * 40, "docs(010-044): сводка плана", (".planning/x.md",))
PLANNING_COMMIT = Commit(
    "c" * 40, "docs(10): правка приборов плана (10-44) по замечаниям", ("app/pages/x.py",)
)
NEIGHBOUR_COMMIT = Commit("d" * 40, "feat(10-4): соседний план", ("app/pages/x.py",))
UNSCOPED_COMMIT = Commit("e" * 40, "fix: правка оркестратора после 10-44", ("app/pages/x.py",))
SYNTHETIC_JOURNAL = (PLAN_COMMIT, PADDED_PLAN_COMMIT, PLANNING_COMMIT, NEIGHBOUR_COMMIT, UNSCOPED_COMMIT)


def test_control_the_journal_text_parses_into_hash_subject_and_paths():
    """Текст в форме `JOURNAL_ARGS` разбирается в записи: хэш, тема, пути; слияние — без путей."""
    text = (
        f"{RECORD_SEPARATOR}{'1' * 40}{FIELD_SEPARATOR}feat(10-44): правка\n\n"
        "app/pages/x.py\ntests/test_pages/y.py\n\n"
        f"{RECORD_SEPARATOR}{'2' * 40}{FIELD_SEPARATOR}Merge branch 'gsd/phase-10'\n"
        f"{RECORD_SEPARATOR}{'3' * 40}{FIELD_SEPARATOR}docs(10-44): тема: с двоеточием\n\n"
        ".planning/STATE.md\n"
    )
    assert _parse_journal(text) == (
        Commit("1" * 40, "feat(10-44): правка", ("app/pages/x.py", "tests/test_pages/y.py")),
        Commit("2" * 40, "Merge branch 'gsd/phase-10'", ()),
        Commit("3" * 40, "docs(10-44): тема: с двоеточием", (".planning/STATE.md",)),
    )


def test_control_the_plan_commits_are_selected_by_the_subject_scope_only():
    """Отбор по ОБЛАСТИ В ТЕМЕ: `тип(10-44):` и `тип(010-044):` — да; `docs(10): … (10-44)`,
    соседний план `10-4` и коммит оркестратора без области — нет (угроза T-15-101)."""
    selected = _plan_commits(SYNTHETIC_JOURNAL, "10-44")
    assert [commit.sha for commit in selected] == [PLAN_COMMIT.sha, PADDED_PLAN_COMMIT.sha], (
        "коммиты плана 10-44 отобраны не по области темы: "
        + ", ".join(commit.subject for commit in selected)
    )


def test_control_a_forbidden_path_is_named_with_its_commit_and_an_allowed_one_is_not():
    """Путь под каталогом-запретом назван вместе с коммитом; путь вне перечня — нет; элемент
    без `/` запрещает ровно файл."""
    commits = (
        Commit("1" * 40, "feat(10-44): x", ("app/pages/x.py", "tests/test_planning/y.py")),
        Commit("2" * 40, "feat(10-44): y", ("app/static/css/app.css.bak",)),
        Commit("3" * 40, "feat(10-44): z", ("app/static/css/app.css",)),
    )
    offences = _path_offences(commits, ("app/pages/", "app/static/css/app.css"))
    assert offences == [
        PathOffence("1" * 40, "feat(10-44): x", "app/pages/x.py", "app/pages/"),
        PathOffence("3" * 40, "feat(10-44): z", "app/static/css/app.css", "app/static/css/app.css"),
    ]


def test_control_an_empty_commit_selection_is_a_refusal_not_a_green():
    """Коммитов плана не найдено — отказ с названной причиной, а не пустой список нарушений;
    пустой перечень запретов и коммиты без путей — тоже отказ (антивакуум)."""
    with pytest.raises(HistoryRefusal, match="коммитов плана 10-99 не найдено"):
        _plan_commits(SYNTHETIC_JOURNAL, "10-99")
    with pytest.raises(HistoryRefusal, match="перечень запрещённых путей пуст"):
        _path_offences((PLAN_COMMIT,), ())
    with pytest.raises(HistoryRefusal, match="ни одного пути"):
        _path_offences((Commit("1" * 40, "feat(10-44): x", ()),), ("app/",))


def test_control_a_shallow_clone_is_refused_before_the_journal_is_parsed():
    """Мелкий клон и неразборчивый ответ git — отказ ДО чтения журнала (угроза T-15-100)."""
    requested: list[tuple[str, ...]] = []

    def git_answering(answer: str) -> Callable[..., str]:
        def git(*args: str) -> str:
            requested.append(args)
            if args == SHALLOW_ARGS:
                return answer
            raise AssertionError(f"журнал запрошен до отказа: git {' '.join(args)}")

        return git

    with pytest.raises(HistoryRefusal, match="мелкий клон"):
        _read_journal(git_answering("true\n"))
    with pytest.raises(HistoryRefusal, match="неразборчив"):
        _read_journal(git_answering("--is-shallow-repository\n"))
    assert requested == [SHALLOW_ARGS, SHALLOW_ARGS], requested
