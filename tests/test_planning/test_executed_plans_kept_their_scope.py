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

from scripts import prohibitions_census as tool

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
class ContentOffence:
    """Коммит плана, изменивший СОДЕРЖАНИЕ наблюдаемого пути вопреки факту: КТО, ГДЕ и ЧТО."""

    sha: str
    subject: str
    path: str
    detail: str

    def __str__(self) -> str:
        return f"{self.sha[:8]} «{self.subject}» — `{self.path}`: {self.detail}"


# ВИДЫ ФАКТА (план 15-31). `PATHS` — вид плана 15-30: коммиты плана не касаются путей перечня
# `forbidden`. Остальные — факты о СОДЕРЖАНИИ правки: коммиты плана касаться наблюдаемых путей
# `watched` МОГУТ, но содержимое до и после каждого такого коммита (`git show <коммит>^:<путь>`
# и `<коммит>:<путь>`) обязано держать предикат вида над данными `subject`.
PATHS = "paths"
DEFINITION_SOURCES = "definition-sources"
HEADER_FIELDS = "header-fields"
SECTION_LINE = "section-line"
STATUS_LINES_KEPT = "status-lines-kept"
EQUAL_WITHOUT_COMMENTS = "equal-without-comments"


@dataclass(frozen=True)
class HistoryFact:
    """Исторический факт плана: область темы `10-NN` и то, чего его коммиты не делают.

    Вид `PATHS` — пути `forbidden` коммитами плана не тронуты. Вид содержания — наблюдаемые пути
    `watched` тронуты могут быть, но предикат вида над данными `subject` держится на каждой паре
    «до / после» такого коммита. `owner` — у вида `DEFINITION_SOURCES` план, чьи определения
    составляют группу `subject` (состав сверяется с историей правилом ниже).
    """

    scope: str
    forbidden: tuple[str, ...] = ()
    kind: str = PATHS
    watched: tuple[str, ...] = ()
    subject: tuple[str, ...] = ()
    owner: str = ""


# СУИТА — каталог `tests/`.
SUITE = ("tests/",)

# ПРОДУКТ — всё отслеживаемое, из чего собирается и запускается система. Перечень снят с
# `git ls-tree --name-only HEAD` 2026-09-26 (план 15-30): взяты все корни, кроме записей и
# документов — `.planning/`, `CLAUDE.md`, `README.md`, `design/`, `new_broadcaster_design.html`,
# `.gitignore`. Прочтение шире таблицы планирования (`app/`): формулировки говорят «ПРОДУКТ», а
# не «`app/`», и по указанию плана берётся полная формулировка. Корень, заведённый позже, в
# коммиты исполненных планов Фазы 10 попасть не мог иначе как новым коммитом с их областью.
PRODUCT = (
    "app/",
    "main.py",
    "alembic/",
    "alembic.ini",
    "wa_worker/",
    "wa_bridge/",
    "max_worker/",
    "scripts/",
    "nginx/",
    "monitoring/",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.dev.yml",
    "docker-compose.prod.yml",
    "docker-compose.monitoring.yml",
    "entrypoint.sh",
    "init-letsencrypt.sh",
    "justfile",
    "pyproject.toml",
    "uv.lock",
    ".env.example",
    ".python-version",
)

TEMPLATES = "app/templates/"
STYLESHEET = "app/static/css/app.css"
PHASE_10_DIR = ".planning/phases/10-rychag-components-modal-html/"

# Ключ — тождество строки реестра в форме `10-NN-PLAN.md#i`; значение — область темы и
# запрещённые пути по ПОЛНОЙ формулировке запрета. Прочтение каждой формулировки — в
# комментарии над записью; где формулировка говорит больше, чем пути, это названо там же.
HISTORY_FACTS: dict[str, HistoryFact] = {
    # «РАЗМЕТКА НЕ ПРАВИТСЯ НИ НА СИМВОЛ: … дописать узел в шаблон …» — разметка есть шаблоны.
    "10-36-PLAN.md#2": HistoryFact("10-36", (TEMPLATES,)),
    # «НИ ОДНО ОБЪЯВЛЕНИЕ `app/static/css/app.css` НЕ ПРАВИТСЯ» — файл целиком (строже «объявления»).
    "10-37-PLAN.md#0": HistoryFact("10-37", (STYLESHEET,)),
    # «НИ ОДИН ШАБЛОН `app/templates/` НЕ ПРАВИТСЯ».
    "10-38-PLAN.md#2": HistoryFact("10-38", (TEMPLATES,)),
    # «НИ ОДНО ОБЪЯВЛЕНИЕ `app/static/css/app.css` НЕ ПРАВИТСЯ: контроли доктóрят КОПИИ …» —
    # после двоеточия описан способ (копии во временном каталоге), а запрет — правка файла.
    "10-38-PLAN.md#3": HistoryFact("10-38", (STYLESHEET,)),
    # «ПЯТЬ ЗАМЕЧАНИЙ НЕ ЧИНЯТСЯ …: правка `tests/test_pages/test_shell.py` либо
    # `app/static/css/app.css` настоящим планом запрещена» — формулировка сама сводит запрет к
    # двум файлам.
    "10-39-PLAN.md#4": HistoryFact("10-39", ("tests/test_pages/test_shell.py", STYLESHEET)),
    # «ПРОДУКТ И СУИТА НЕ ПРАВЯТСЯ НИ НА СТРОКУ».
    "10-39-PLAN.md#5": HistoryFact("10-39", PRODUCT + SUITE),
    # «ЗАПИСЬ D-13 В `10-CONTEXT.md` НЕ ПРАВИТСЯ» — файл целиком (строже одной записи).
    "10-40-PLAN.md#3": HistoryFact("10-40", (PHASE_10_DIR + "10-CONTEXT.md",)),
    # «ПРОДУКТ И СУИТА НЕ ПРАВЯТСЯ НИ НА СТРОКУ: ветвь отказа НЕ ОТКАТЫВАЕТ ни двух строк
    # обёртки, ни правки плана 10-35 …» — обёртка (`app/templates/ads/form.html`) и правки 10-35
    # (`app/…`, `tests/…`) лежат в продукте и суите; откат был бы их правкой.
    "10-40-PLAN.md#4": HistoryFact("10-40", PRODUCT + SUITE),
    # «`10-VERIFICATION.md` НЕ ПРАВИТСЯ».
    "10-44-PLAN.md#2": HistoryFact("10-44", (PHASE_10_DIR + "10-VERIFICATION.md",)),
    # «ПРОДУКТ И СУИТА НЕ ПРАВЯТСЯ НИ НА СТРОКУ НИ ОДНОЙ ВЕТВЬЮ».
    "10-44-PLAN.md#5": HistoryFact("10-44", PRODUCT + SUITE),
    # «ПРОДУКТ НЕ ПРАВИТСЯ НИ НА СИМВОЛ: `app/` этим планом не трогается вовсе» — суита правилась.
    "10-48-PLAN.md#4": HistoryFact("10-48", PRODUCT),
    # «`app/static/css/app.css` НЕ ТРОГАЕТСЯ».
    "10-49-PLAN.md#4": HistoryFact("10-49", (STYLESHEET,)),
    # «`…/htmx_error_banner.html`, `…/modal.html` И `app/static/css/app.css` НЕ ТРОГАЮТСЯ».
    "10-50-PLAN.md#4": HistoryFact(
        "10-50",
        (
            "app/templates/includes/htmx_error_banner.html",
            "app/templates/components/modal.html",
            STYLESHEET,
        ),
    ),
    # «`app/templates/` НЕ ПРАВИТСЯ НИ НА СИМВОЛ».
    "10-51-PLAN.md#0": HistoryFact("10-51", (TEMPLATES,)),
}

HISTORY_RULE = "test_every_declared_history_fact_holds_over_its_plans_commits"


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


# --- факты содержания: чистые предикаты пары «до / после» -----------------------------------
#
# Каждый предикат — чистая функция `(путь, до, после, subject) → [описание изменения]`; `None`
# вместо текста — пути в этой ревизии нет. Пара, о которой предикат ничего узнать не может
# (группы нет до коммита, поля нет в шапке, раздела нет, дифф пуст), — отказ `HistoryRefusal`,
# а не пустой список: факт, ничего не узнавший, не зеленеет (антивакуум).


def _definition_source_changes(
    path: str, before: str | None, after: str | None, names: tuple[str, ...]
) -> list[str]:
    """Определения группы `names`, чей исходник после коммита не равен исходнику до."""
    return []


def _header_field_changes(
    path: str, before: str | None, after: str | None, fields: tuple[str, ...]
) -> list[str]:
    """Поля `fields` шапки, чьё значение после коммита не равно значению до."""
    return []


def _section_line_changes(
    path: str, before: str | None, after: str | None, subject: tuple[str, ...]
) -> list[str]:
    """Строка пункта `subject[1]` раздела `subject[0]`, не равная себе до коммита."""
    return []


def _status_line_changes(
    path: str, before: str | None, after: str | None, subject: tuple[str, ...]
) -> list[str]:
    """Строки `status:`, удалённые или изменённые диффом пары."""
    return []


def _executable_changes(
    path: str, before: str | None, after: str | None, subject: tuple[str, ...]
) -> list[str]:
    """Изменение пары за вычетом комментариев: `.py` — `ast.dump`, `.html` — без `{# … #}`."""
    return []


def _content_offences(
    journal: Iterable[Commit],
    fact: HistoryFact,
    revisions: Callable[[str, str], tuple[str | None, str | None]],
) -> list[ContentOffence]:
    """Каждое изменение содержания наблюдаемого пути коммитами плана — с коммитом и путём."""
    return []


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


# --- контроли видов содержания на синтетических парах ------------------------------------------

GROUP_BEFORE = (
    "import pytest\n\n\n"
    "GROUP_FLAG = 3\n\n\n"
    "@pytest.mark.slow\n"
    "def kept_rule():\n"
    "    # комментарий внутри тела — тоже символ исходника группы\n"
    "    return GROUP_FLAG\n\n\n"
    "def outside_rule():\n"
    "    return 2\n"
)
GROUP = ("GROUP_FLAG", "kept_rule")


def test_control_a_changed_group_definition_is_named_and_an_outside_one_is_not():
    """Вид «исходник определений группы равен»: правка тела, декоратора, комментария внутри
    тела и значения константы группы называются; правка определения вне группы — нет; снятое
    определение названо; группы нет до коммита — отказ."""
    path = "tests/test_pages/test_shell.py"
    body = GROUP_BEFORE.replace("return GROUP_FLAG", "return GROUP_FLAG + 1")
    assert _definition_source_changes(path, GROUP_BEFORE, body, GROUP) == [
        "`kept_rule`: исходник определения изменён"
    ]
    for doctored in (
        GROUP_BEFORE.replace("@pytest.mark.slow\n", ""),
        GROUP_BEFORE.replace("тоже символ", "тоже знак"),
        GROUP_BEFORE.replace("GROUP_FLAG = 3", "GROUP_FLAG = 4"),
    ):
        assert len(_definition_source_changes(path, GROUP_BEFORE, doctored, GROUP)) == 1, doctored
    outside = GROUP_BEFORE.replace("return 2", "return 20")
    assert _definition_source_changes(path, GROUP_BEFORE, outside, GROUP) == []
    removed = GROUP_BEFORE.replace("GROUP_FLAG = 3\n", "")
    assert _definition_source_changes(path, GROUP_BEFORE, removed, GROUP) == [
        "`GROUP_FLAG`: определение снято"
    ]
    with pytest.raises(HistoryRefusal, match="нет до коммита"):
        _definition_source_changes(path, GROUP_BEFORE, GROUP_BEFORE, ("absent_rule",))


HEADER_BEFORE = (
    "---\n"
    "phase: 10\n"
    "status: human_needed\n"
    "score: 7/8 must-haves verified\n"
    "re_verification:\n"
    "  previous_status: gaps_found\n"
    "gaps:\n"
    "  - truth: x\n"
    "    status: failed\n"
    "---\n\n"
    "# Отчёт\n\nstatus: это тело, а не шапка\n"
)
HEADER_FIELDS_OF_10_40 = ("status", "score", "gaps", "re_verification")


def test_control_a_changed_header_field_is_named_and_an_added_one_is_not():
    """Вид «поля шапки равны»: изменённый `status` и изменённый гэп называются; добавленный
    блок `overrides` и правка тела — нет; поля нет в шапке до коммита — отказ."""
    path = PHASE_10_DIR + "10-VERIFICATION.md"
    status = HEADER_BEFORE.replace("status: human_needed", "status: passed")
    assert _header_field_changes(path, HEADER_BEFORE, status, HEADER_FIELDS_OF_10_40) == [
        "поле шапки `status` изменено: 'human_needed' → 'passed'"
    ]
    gap = HEADER_BEFORE.replace("    status: failed", "    status: resolved")
    assert len(_header_field_changes(path, HEADER_BEFORE, gap, HEADER_FIELDS_OF_10_40)) == 1
    overrides = HEADER_BEFORE.replace("gaps:\n", "overrides:\n  - must_have: y\ngaps:\n")
    assert _header_field_changes(path, HEADER_BEFORE, overrides, HEADER_FIELDS_OF_10_40) == []
    prose = HEADER_BEFORE.replace("это тело", "это правленое тело")
    assert _header_field_changes(path, HEADER_BEFORE, prose, HEADER_FIELDS_OF_10_40) == []
    with pytest.raises(HistoryRefusal, match="нет в шапке до коммита"):
        _header_field_changes(path, HEADER_BEFORE, HEADER_BEFORE, ("verdict",))


ROADMAP_BEFORE = (
    "## Phase Details\n\n"
    "### Phase 9: Пилот\n\n"
    "  3. третий критерий чужой фазы\n\n"
    "### Phase 10: Рычаг\n\n"
    "**Success Criteria** (what must be TRUE):\n\n"
    "  1. первый критерий\n"
    "  2. второй критерий\n"
    "  3. третий критерий: новых строк JS фаза не добавляет\n"
    "  4. четвёртый критерий\n\n"
    "#### Подраздел фазы\n\n"
    "- [x] 10-40-PLAN.md — отметка плана\n\n"
    "### Phase 11: Разделы\n\n"
    "  3. третий критерий следующей фазы\n"
)
CRITERION_3_OF_PHASE_10 = ("### Phase 10:", "3")


def test_control_a_changed_section_line_is_named_and_a_neighbour_is_not():
    """Вид «строка раздела равна»: правка критерия 3 Фазы 10 называется; правка соседнего
    критерия, критерия 3 соседних фаз и отметки плана — нет; раздела нет — отказ."""
    path = ".planning/ROADMAP.md"
    changed = ROADMAP_BEFORE.replace("новых строк JS", "новых сущностей JS")
    assert _section_line_changes(path, ROADMAP_BEFORE, changed, CRITERION_3_OF_PHASE_10) == [
        "строка пункта 3 раздела `### Phase 10:` изменена: было "
        "'  3. третий критерий: новых строк JS фаза не добавляет', стало "
        "['  3. третий критерий: новых сущностей JS фаза не добавляет']"
    ]
    for neighbour in (
        ROADMAP_BEFORE.replace("четвёртый критерий", "четвёртый критерий, правленый"),
        ROADMAP_BEFORE.replace("третий критерий чужой", "третий критерий правленый чужой"),
        ROADMAP_BEFORE.replace("третий критерий следующей", "третий правленый следующей"),
        ROADMAP_BEFORE.replace("- [x] 10-40", "- [ ] 10-40"),
    ):
        assert _section_line_changes(path, ROADMAP_BEFORE, neighbour, CRITERION_3_OF_PHASE_10) == []
    with pytest.raises(HistoryRefusal, match="раздела `### Phase 12:` нет"):
        _section_line_changes(path, ROADMAP_BEFORE, ROADMAP_BEFORE, ("### Phase 12:", "3"))


UAT_BEFORE = (
    "---\nstatus: partial\n---\n\n"
    "## Gaps\n\n```yaml\n"
    "- truth: панель закрывается\n"
    "  status: failed\n"
    "  reason: не наблюдено\n"
    "```\n"
)


def test_control_a_removed_status_line_is_named_and_an_insertion_is_not():
    """Вид «строки `status:` не удалены»: удалённая и изменённая строка `status:` называются;
    дифф из одних вставок (отдельный ключ `status_note`) — нет; пустой дифф — отказ."""
    path = PHASE_10_DIR + "10-UAT.md"
    removed = UAT_BEFORE.replace("  status: failed\n", "")
    assert _status_line_changes(path, UAT_BEFORE, removed, ()) == [
        "строка `status: failed` удалена или изменена"
    ]
    changed = UAT_BEFORE.replace("status: failed", "status: resolved")
    assert _status_line_changes(path, UAT_BEFORE, changed, ()) == [
        "строка `status: failed` удалена или изменена"
    ]
    inserted = UAT_BEFORE.replace(
        "  reason: не наблюдено\n", "  reason: не наблюдено\n  status_note: закрыт планом\n"
    )
    assert _status_line_changes(path, UAT_BEFORE, inserted, ()) == []
    with pytest.raises(HistoryRefusal, match="дифф пуст"):
        _status_line_changes(path, UAT_BEFORE, UAT_BEFORE, ())


PY_BEFORE = 'def handler():\n    # пометка, протухающая громко\n    return "ok"\n'
TEMPLATE_BEFORE = '<div class="modal">{# пометка #}\n  {{ body }}\n</div>\n'


def test_control_an_executable_change_is_named_and_a_comment_change_is_not():
    """Вид «равно без комментариев»: `.py` — `ast.dump`, шаблон — без `{# … #}`; правка
    исполняемой строки называется, правка комментария — нет; иной файл сличается целиком."""
    py = "app/pages/schedules.py"
    assert _executable_changes(py, PY_BEFORE, PY_BEFORE.replace("громко", "тихо"), ()) == []
    assert _executable_changes(py, PY_BEFORE, PY_BEFORE.replace('"ok"', '"no"'), ()) == [
        "исполняемое содержание изменено (сличение без комментариев)"
    ]
    html = "app/templates/components/modal.html"
    comment = TEMPLATE_BEFORE.replace("{# пометка #}", "{# другая пометка #}")
    assert _executable_changes(html, TEMPLATE_BEFORE, comment, ()) == []
    body = TEMPLATE_BEFORE.replace("{{ body }}", "{{ other }}")
    assert len(_executable_changes(html, TEMPLATE_BEFORE, body, ())) == 1
    css = "app/static/css/app.css"
    assert len(_executable_changes(css, "a{}\n", "/* x */a{}\n", ())) == 1
    assert _executable_changes(py, None, PY_BEFORE, ()) == ["файл заведён коммитом"]


def test_control_a_content_fact_reads_every_touched_watched_path_and_refuses_on_none():
    """Разводка вида содержания: читается каждый наблюдаемый путь, которого коснулся коммит
    плана (и только он), изменение названо с коммитом; ни одного наблюдаемого пути коммиты
    плана не коснулись — отказ, а не зелень (антивакуум)."""
    watched = PHASE_10_DIR + "10-UAT.md"
    journal = (
        Commit("1" * 40, "docs(10-39): правка", (watched, "app/pages/x.py")),
        Commit("2" * 40, "docs(10): чужой", (watched,)),
    )
    removed = UAT_BEFORE.replace("  status: failed\n", "")
    read: list[tuple[str, str]] = []

    def revisions(sha: str, path: str) -> tuple[str | None, str | None]:
        read.append((sha, path))
        return UAT_BEFORE, removed

    fact = HistoryFact("10-39", kind=STATUS_LINES_KEPT, watched=(watched,))
    assert _content_offences(journal, fact, revisions) == [
        ContentOffence(
            "1" * 40, "docs(10-39): правка", watched, "строка `status: failed` удалена или изменена"
        )
    ]
    assert read == [("1" * 40, watched)], read
    elsewhere = HistoryFact("10-39", kind=STATUS_LINES_KEPT, watched=("docs/other.md",))
    with pytest.raises(HistoryRefusal, match="ни одного наблюдаемого пути"):
        _content_offences(journal, elsewhere, revisions)


# --- правила над живым журналом ---------------------------------------------------------------


def _offences_of(journal: Iterable[Commit], identity: str) -> list[PathOffence]:
    fact = HISTORY_FACTS[identity]
    return _path_offences(_plan_commits(journal, fact.scope), fact.forbidden)


@pytest.mark.parametrize("identity", sorted(HISTORY_FACTS))
def test_every_declared_history_fact_holds_over_its_plans_commits(identity):
    """НЕСУЩЕЕ ПРАВИЛО: коммиты плана найдены (антивакуум) и ни один не коснулся пути, который
    запрет плана объявил нетронутым. Мелкий клон и пустой отбор — отказ, а не зелень."""
    offences = _offences_of(_git_journal(), identity)
    assert not offences, (
        f"запрет `{identity}` нарушен коммитами своего плана:\n"
        + "\n".join(str(offence) for offence in offences)
    )


def test_every_history_fact_names_a_phase_10_prohibition_by_identity():
    """Правило согласия: каждый ключ `HISTORY_FACTS` — тождество записи переписи Фазы 10 с
    `verification: test`, его область есть номер его плана, перечень путей не пуст; и каждая
    строка реестра, называющая несущее правило, имеет запись здесь — иначе строка числилась бы
    принуждённой правилом, которое её не проверяет.

    ⚠️ ОБРАТНОЕ НАПРАВЛЕНИЕ (каждая запись здесь названа строкой реестра) НЕ утверждается: лишняя
    запись есть лишняя проверка, а не ложное принуждение."""
    assert HISTORY_FACTS, "перечень исторических фактов пуст — несущее правило зеленело бы вакуумом"
    records = tool.census(tool._plan_sources(tool.TREE_ROOT))
    problems: list[str] = []
    for identity, fact in sorted(HISTORY_FACTS.items()):
        try:
            record = tool._resolve_identity(records, identity)
        except tool.CensusError as error:
            problems.append(f"`{identity}`: {error}")
            continue
        if record.phase != tool.DECISION_SCOPE_PHASE or record.verification != "test":
            problems.append(
                f"`{identity}`: фаза {record.phase}, verification {record.verification!r} — "
                f"не запрет Фазы {tool.DECISION_SCOPE_PHASE} с `verification: test`"
            )
        plan_number = identity.partition("-PLAN.md#")[0]
        if fact.scope != plan_number:
            problems.append(f"`{identity}`: область `{fact.scope}`, а план `{plan_number}`")
        if not fact.forbidden:
            problems.append(f"`{identity}`: перечень запрещённых путей пуст")

    registry = tool.load_registry(tool.TREE_ROOT / tool.REGISTRY_RELATIVE_PATH)
    for row_identity, row in tool._registry_rows(registry).items():
        names = str(row.get(tool.RULE_NAME_FIELD) or "").split(tool.RULE_SEPARATOR)
        tail = row_identity.plan_path.rpartition("/")[2] + f"#{row_identity.index}"
        if HISTORY_RULE in names and tail not in HISTORY_FACTS:
            problems.append(f"строка реестра `{row_identity}` называет `{HISTORY_RULE}`, а записи нет")

    assert not problems, "\n".join(problems)


def test_control_a_synthetic_commit_on_a_forbidden_path_reddens_10_44_5():
    """Замер направления на ЖИВОМ журнале: копия журнала с добавленным коммитом `feat(10-44): x`
    на пути `app/x.py` краснит запись `10-44-PLAN.md#5`, и назван ровно этот коммит."""
    journal = _git_journal()
    assert _offences_of(journal, "10-44-PLAN.md#5") == []
    synthetic = Commit("f" * 40, "feat(10-44): x", ("app/x.py",))
    assert _offences_of(journal + (synthetic,), "10-44-PLAN.md#5") == [
        PathOffence(synthetic.sha, synthetic.subject, "app/x.py", "app/")
    ]
