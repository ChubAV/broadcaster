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

ФАКТЫ СОДЕРЖАНИЯ (план 15-31). Пять запретов Фазы 10 говорят не «путь не тронут», а «в
тронутом пути не изменено ВОТ ЭТО»: исходник группы правил, поля шапки отчёта, строка критерия
раздела, строки `status:` гэпов, исполняемое содержание продукта. Для них запись `HISTORY_FACTS`
несёт ВИД предиката, наблюдаемые пути и данные вида; для каждого коммита плана, коснувшегося
наблюдаемого пути, читается пара «до / после» (`git show <коммит>^:<путь>` и `<коммит>:<путь>`,
один раз за прогон), и предикат вида — чистая функция этой пары — называет каждое изменение.
Каждый вид показан контролем на синтетической паре, направление — на настоящей паре коммита
`415b0cfe` с подменённой стороной «после». Антивакуум вида: коммиты плана не коснулись ни одного
наблюдаемого пути — отказ; предикат, которому сличать нечего (группы нет до коммита, поля нет в
шапке, раздела нет, дифф пуст), — отказ. Прочтение каждой формулировки — над её записью.

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
5. Факт содержания судит ПАРУ КАЖДОГО КОММИТА ПЛАНА, а не сумму: изменение, внесённое одним
   коммитом плана и отменённое другим, названо (строже буквы); изменение, внесённое коммитом без
   области плана, — невидимо (граница 2).

ИСТОРИЧЕСКИЕ ПРОЧТЕНИЯ, ВЫБРАННЫЕ ВЛАДЕЛЬЦЕМ (план 15-32). На чекпойнте плана 15-32 владелец
(`chubav`, 2026-09-26; записаны выбранные варианты, а не его слова) выбрал ветвь (а′) для строк,
сформулированных ОБЛАСТЬЮ фазы или плана («фаза не заводит…», «этим планом…»): формулировка
проверяется коммитами той области, о которой она говорит. Отсюда три перемены модуля.
1. ОБЛАСТЬ ФАЗЫ. Область записи — номер плана `10-NN` либо номер фазы `10`. Коммит фазы — тот,
   чья тема начинается `тип(10-NN):` для ЛЮБОГО плана NN этой фазы. ⚠️ ГРАНИЦА, ВЫБРАННАЯ
   ВЛАДЕЛЬЦЕМ («plan commits only»): коммиты правок ревизии без номера плана — `fix(10): …`,
   `docs(10): …` — в отбор фазы НЕ входят (граница 2). Пример — `aa516a2e fix(10): CR-01 …`: он
   добавил код реестра уведомлений, и прочтение «навсегда» либо отбор «с `fix(10):`» были бы
   красны. Этот коммит здесь невидим по выбору владельца, а не по недосмотру.
2. ВИДЫ СОДЕРЖАНИЯ БЕЗ ВЕРИФИКАЦИИ `test`. Записи плана 15-32 названы строками с
   `verification: none` (класс `product-invariant`), и правило согласия принимает любую строку
   Фазы 10 (летопись — у правила согласия).
3. ТРИ ВИДА ПРЕДИКАТА: дословный перенос видимого текста (судит ВЕСЬ КОММИТ, а не пару одного
   пути: перенос из файла в файл законен), сохранение предикатов отказа и граница на каждом
   источнике идентификатора.
Летопись абзаца «ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ» ниже: фраза «только то, чего план не трогал или
не менял» верна для всех видов, кроме «граница на каждом источнике» (`10-12#1`) — он утверждает
СОСТОЯНИЕ файла после коммита плана: запрет «правка не ставится только там, где предмет замерен»
есть утверждение о полноте правки, и держится он именно так.

ЧЕГО ЭТОТ ФАЙЛ НЕ УТВЕРЖДАЕТ (D-16). Он не судит вердикт отчёта своей фазы и не читает его. Он
не видит правок, сделанных вне коммитов плана (граница 2), и не утверждает, что запрет соблюдён
ПО ДУХУ за пределами путей: запрет «пять замечаний не чинятся» держится здесь ровно как «файлы,
в которых их чинили бы, не тронуты». Он не утверждает, что план сделал то, что обещал, — только
то, чего план не трогал или не менял. И он ничего не говорит о планах, которых нет в
`HISTORY_FACTS`.

ПОЧЕМУ ЭТО НЕ ОТМЕНА РЕШЕНИЯ D-33. D-33 отказал машинному гейту на ПРОЗЕ операционного
документа. Предмет здесь другой: машинно читаемый журнал git (тема коммита и пути) и объявленное
перечнем соответствие «план → запрещённые пути». Суждения этот предмет не требует; прочтение
формулировки запрета в перечень путей сделано человеком один раз и записано рядом с каждой
записью `HISTORY_FACTS`.
"""

from __future__ import annotations

import ast
import difflib
import re
import subprocess
from collections import Counter
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
# Область ФАЗЫ (план 15-32): номер фазы без номера плана — отбор коммитов ВСЕХ планов фазы.
PHASE_SCOPE = re.compile(r"(\d+)")


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
# Виды плана 15-32 (исторические прочтения, выбранные владельцем):
REFUSAL_PREDICATES_KEPT = "refusal-predicates-kept"
IDENTIFIER_SOURCES_BOUNDED = "identifier-sources-bounded"
# Вид КОММИТА, а не пары одного пути: дословный перенос текста законно пересекает границу файла.
VISIBLE_TEXT_CARRIED = "visible-text-carried"


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
SHELL_SUITE = "tests/test_pages/test_shell.py"

# ГРУППА ПРАВИЛ СНЯТИЯ ЗАГОТОВОК ПЛАНА 10-35 — определения верхнего уровня, которые коммиты
# `(10-35)` завели в `test_shell.py`, в порядке появления. Снята ИСТОРИЕЙ, а не набрана руками
# (план 15-31, 2026-09-26): `ba908912` — пять констант и три функции, `6f3b8b55` — пять функций;
# `b3a3fa3c` новых определений не завёл (правил чужую `test_failure_banner_has_single_source`).
# Состав сверяет с историей `test_every_definition_group_is_what_its_owner_plan_introduced`.
PLAN_10_35_GROUP = (
    "MODAL_OPEN_METHOD",
    "MODAL_CLOSE_METHOD",
    "FAILURE_BANNER_HIDDEN_ATTR",
    "_JS_BLOCK_COMMENT_RE",
    "_MODAL_OPEN_METHOD_RE",
    "_lever_show_body",
    "_lever_clearing_findings",
    "test_the_lever_clears_both_failure_banners_when_the_panel_opens",
    "_lever_raises_the_scroll_lock",
    "_scratch_lever",
    "_lever_clearing_chunk",
    "test_control_a_lever_that_keeps_a_stale_banner_reddens",
    "test_control_a_lever_that_names_the_flag_only_in_prose_reddens",
)
STYLESHEET = "app/static/css/app.css"
PHASE_10_DIR = ".planning/phases/10-rychag-components-modal-html/"
# Реестр кодов уведомлений `?notice=` — единственное место, где код становится кодом реестра.
NOTICES = "app/pages/notices.py"
PAGES = "app/pages/"

# Ключ — тождество строки реестра в форме `10-NN-PLAN.md#i`; значение — область темы и
# запрещённые пути по ПОЛНОЙ формулировке запрета (вид `PATHS`) либо вид содержания, наблюдаемые
# пути и данные вида (план 15-31). Прочтение каждой формулировки — в
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
    # --- факты СОДЕРЖАНИЯ правки (план 15-31) ---
    # «ГРУППА ПРАВИЛ СНЯТИЯ ЗАГОТОВОК (план 10-35) НЕ ТРОГАЕТСЯ НИ НА СИМВОЛ» — группа есть ВСЕ
    # определения верхнего уровня, которые коммиты `(10-35)` завели в `test_shell.py`: восемь
    # функций и пять констант, на которых они стоят (прочтение шире «функций» таблицы планирования:
    # «ни на символ» и «группа правил» включают их данные). Состав снят историей и сверяется с ней
    # правилом `test_every_definition_group_is_what_its_owner_plan_introduced`.
    "10-37-PLAN.md#3": HistoryFact(
        "10-37",
        kind=DEFINITION_SOURCES,
        watched=(SHELL_SUITE,),
        subject=PLAN_10_35_GROUP,
        owner="10-35",
    ),
    # «ПОЛЕ СОСТОЯНИЯ НИ У ОДНОГО ГЭПА НЕ ПРАВИТСЯ И НЕ ВЫЧЁРКИВАЕТСЯ … запись о закрытии идёт
    # ОТДЕЛЬНЫМ ключом» — реестр гэпов обхода живёт в ТЕЛЕ `10-UAT.md` (блок YAML), в шапке гэпов
    # нет (замер планирования: 0 до и после). Держится строже буквы: ни одна строка `status:`
    # файла — гэпа или шапки — диффом коммитов плана не удалена и не изменена.
    "10-39-PLAN.md#2": HistoryFact(
        "10-39", kind=STATUS_LINES_KEPT, watched=(PHASE_10_DIR + "10-UAT.md",)
    ),
    # «ПОЛЕ СОСТОЯНИЯ ОТЧЁТА, СЧЁТ ИСТИН, СПИСОК ГЭПОВ И БЛОК ПОВТОРНОЙ ВЕРИФИКАЦИИ НЕ ПРАВЯТСЯ» —
    # четыре поля шапки `10-VERIFICATION.md`: `status`, `score`, `gaps`, `re_verification`.
    "10-40-PLAN.md#1": HistoryFact(
        "10-40",
        kind=HEADER_FIELDS,
        watched=(PHASE_10_DIR + "10-VERIFICATION.md",),
        subject=("status", "score", "gaps", "re_verification"),
    ),
    # «ФОРМУЛИРОВКА КРИТЕРИЯ 3 В `.planning/ROADMAP.md` НЕ ПРАВИТСЯ НИ НА СИМВОЛ» — строка пункта 3
    # раздела `### Phase 10:`.
    "10-40-PLAN.md#2": HistoryFact(
        "10-40", kind=SECTION_LINE, watched=(".planning/ROADMAP.md",), subject=("### Phase 10:", "3")
    ),
    # «ПОВЕДЕНИЕ ПРОДУКТА НЕ ПРАВИТСЯ: в `…/modal.html` и `app/pages/schedules.py` правится
    # ИСКЛЮЧИТЕЛЬНО тело комментария» — оба названных файла и, по полной формулировке, весь
    # ПРОДУКТ: любой его файл, которого коснулся коммит плана, равен себе без комментариев.
    "10-46-PLAN.md#3": HistoryFact(
        "10-46",
        kind=EQUAL_WITHOUT_COMMENTS,
        watched=("app/templates/components/modal.html", "app/pages/schedules.py") + PRODUCT,
    ),
    # --- исторические прочтения, выбранные владельцем на чекпойнте плана 15-32 ---
    # Строки `verification: none` класса `product-invariant`, сформулированные ОБЛАСТЬЮ фазы или
    # плана. Выбор `chubav` 2026-09-26 (выбранные варианты, а не его слова): (а′) над коммитами
    # с областью плана `(10-NN)`; коммиты без номера плана (`fix(10): …`, пример `aa516a2e`) в
    # отбор не входят — граница названа в докстринге модуля.
    # «новых кодов реестра ?notice= ФАЗА не заводит (D-03)» — ни один коммит ЛЮБОГО плана Фазы 10
    # (область фазы) не тронул реестр кодов: строже буквы «не добавил кода» — файл целиком.
    "10-01-PLAN.md#3": HistoryFact("10", (NOTICES,)),
    # «новых кодов реестра уведомлений ФАЗА НЕ ЗАВОДИТ (D-03)» — то же прочтение, та же область.
    "10-24-PLAN.md#2": HistoryFact("10", (NOTICES,)),
    # «новых кодов реестра уведомлений ПЛАН НЕ ЗАВОДИТ (D-03), в том числе кода для
    # неподтверждённого источника» — коммиты плана 10-31 реестр не тронули (файл целиком).
    "10-31-PLAN.md#1": HistoryFact("10-31", (NOTICES,)),
    # «тексты и подписи карточки расписания и панели её подтверждения переносятся ДОСЛОВНО» — в
    # каждом коммите плана 10-01 каждый фрагмент видимого текста шаблонов, ушедший из файла,
    # пришёл добавленным в том же коммите (перенос между файлами законен).
    "10-01-PLAN.md#6": HistoryFact("10-01", kind=VISIBLE_TEXT_CARRIED, watched=(TEMPLATES,)),
    # «правка НЕ ставится только там, где предмет замерен: закрытие одного из двух источников
    # одной величины оставляет маршрут … открытым» — коммит плана 10-12, тронувший страничный
    # модуль, оставил верхнюю границу на КАЖДОМ параметре-идентификаторе каждого обработчика
    # маршрута (замер: `73df7780`, `app/pages/schedules.py`, 7 параметров, все ограничены).
    # ⚠️ Источник величины вне параметров обработчика (поле формы, прочитанное руками,
    # `_ad_id_from_form`) этим видом не судится: у него своя граница и свои правила.
    "10-12-PLAN.md#1": HistoryFact("10-12", kind=IDENTIFIER_SOURCES_BOUNDED, watched=(PAGES,)),
    # «цель третьего внеполосного узла НЕ становится динамической ЭТИМ ПЛАНОМ» — цель узла живёт в
    # разметке шаблона, и сделать её динамической без правки шаблона нельзя: коммиты плана 10-22
    # не изменили ни одного шаблона иначе, чем в комментарии `{# … #}` (замер: `1d93cb07`,
    # `a3972cfd` — только комментарии). Правку докстринга `app/pages/schedules.py` (`a3972cfd`)
    # вид не судит: цель узла там не живёт.
    "10-22-PLAN.md#1": HistoryFact("10-22", kind=EQUAL_WITHOUT_COMMENTS, watched=(TEMPLATES,)),
    # «предикат отказа и ответ тому, кто пришёл без слоя письма, не меняются ни на символ» —
    # ПОЛОВИНА «предикат отказа»: коммиты плана 10-03 не сняли, не изменили и не добавили ни
    # одного условия охранной ветки отказа и ни одного `raise` ни в одной функции тронутых
    # модулей `app/` (замер: 3 коммита плана тронули `app/`, до них 131 предикат). Половину «ответ без слоя письма» этот
    # вид не держит — текст ответа ушёл в слой ответа (`respond`); её разрешил владелец
    # записью `row_decisions` (поведение держит `test_every_pair_case_answers_both_transports`).
    "10-03-PLAN.md#6": HistoryFact("10-03", kind=REFUSAL_PREDICATES_KEPT, watched=("app/",)),
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
    """Коммиты плана `scope` (`10-44`) либо всех планов фазы `scope` (`10`) — по ОБЛАСТИ В ТЕМЕ;
    пустой отбор — отказ. Область фазы отбирает `тип(10-NN):` любого плана NN и НЕ отбирает
    `тип(10):` — коммит без номера плана (граница выбора владельца, план 15-32)."""
    match = PLAN_SCOPE.fullmatch(scope)
    phase_match = PHASE_SCOPE.fullmatch(scope)
    if match is not None:
        phase, plan = int(match[1]), int(match[2])
        subject_scope = re.compile(rf"^[a-z]+\(0*{phase}-0*{plan}\)!?:")
    elif phase_match is not None:
        subject_scope = re.compile(rf"^[a-z]+\(0*{int(phase_match[1])}-\d+\)!?:")
    else:
        raise HistoryRefusal(f"область `{scope}` не в форме `ФАЗА-ПЛАН` и не номер фазы")
    selected = tuple(commit for commit in journal if subject_scope.match(commit.subject))
    if not selected:
        raise HistoryRefusal(
            f"коммитов плана {scope} не найдено: ни одна тема журнала не начинается "
            f"`тип({scope}):` — правило ничего о плане не узнало и не зеленеет (антивакуум)"
        )
    return selected


def _covered_by(path: str, item: str) -> bool:
    """Путь покрыт элементом перечня: равен ему либо лежит под ним (элемент с `/` — каталог)."""
    return path == item or (item.endswith("/") and path.startswith(item))


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
                if _covered_by(path, item):
                    offences.append(PathOffence(commit.sha, commit.subject, path, item))
    return offences


# --- факты содержания: чистые предикаты пары «до / после» -----------------------------------
#
# Каждый предикат — чистая функция `(путь, до, после, subject) → [описание изменения]`; `None`
# вместо текста — пути в этой ревизии нет. Пара, о которой предикат ничего узнать не может
# (группы нет до коммита, поля нет в шапке, раздела нет, дифф пуст), — отказ `HistoryRefusal`,
# а не пустой список: факт, ничего не узнавший, не зеленеет (антивакуум).


def _definitions(text: str) -> dict[str, str]:
    """Определения верхнего уровня → их исходник: функции и классы (с декораторами) и имена,
    присвоенные на уровне модуля (исходник всего оператора присваивания)."""
    return dict(_definitions_cached(text))


@cache
def _definitions_cached(text: str) -> tuple[tuple[str, str], ...]:
    lines = text.splitlines(keepends=True)
    found: dict[str, str] = {}
    for node in ast.parse(text).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            first = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
            found[node.name] = "".join(lines[first - 1 : node.end_lineno])
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            source = "".join(lines[node.lineno - 1 : node.end_lineno])
            for target in targets:
                if isinstance(target, ast.Name):
                    found[target.id] = source
    return tuple(found.items())


def _definition_source_changes(
    path: str, before: str | None, after: str | None, names: tuple[str, ...]
) -> list[str]:
    """Определения группы `names`, чей исходник после коммита не равен исходнику до.

    Исходник — строки определения целиком, от первого декоратора до последней строки тела:
    комментарий внутри тела есть символ группы («не трогается ни на символ»). Определения группы
    нет до коммита — отказ: факт о группе, которой ещё нет, ничего не проверяет."""
    before_definitions = _definitions(before or "")
    absent = [name for name in names if name not in before_definitions]
    if absent:
        raise HistoryRefusal(
            f"`{path}`: определений группы {', '.join(absent)} нет до коммита — состав группы "
            f"не тот, и факт о ней ничего не проверил бы (антивакуум)"
        )
    after_definitions = _definitions(after) if after is not None else {}
    changes: list[str] = []
    for name in names:
        if name not in after_definitions:
            changes.append(f"`{name}`: определение снято")
        elif after_definitions[name] != before_definitions[name]:
            changes.append(f"`{name}`: исходник определения изменён")
    return changes


_MISSING = object()


def _header_field_changes(
    path: str, before: str | None, after: str | None, fields: tuple[str, ...]
) -> list[str]:
    """Поля `fields` шапки, чьё значение после коммита не равно значению до.

    Шапка разбирается прибором переписи (`_frontmatter`); прочие поля — в том числе добавленные
    коммитом — предмет не этого вида. Поля нет в шапке до коммита — отказ."""
    try:
        header_before = tool._frontmatter(before or "")
        header_after = tool._frontmatter(after or "")
    except tool.CensusError as error:
        raise HistoryRefusal(f"`{path}`: шапка не разбирается — {error}") from error
    absent = [field for field in fields if field not in header_before]
    if absent:
        raise HistoryRefusal(
            f"`{path}`: полей {', '.join(absent)} нет в шапке до коммита — факт о них ничего "
            f"не проверил бы (антивакуум)"
        )
    changes: list[str] = []
    for field in fields:
        value = header_after.get(field, _MISSING)
        if value is _MISSING:
            changes.append(f"поле шапки `{field}` снято")
        elif value != header_before[field]:
            changes.append(
                f"поле шапки `{field}` изменено: {header_before[field]!r} → {value!r}"
            )
    return changes


def _section_lines(text: str, heading: str, item: str) -> list[str] | None:
    """Строки пункта `item.` раздела, чей заголовок начинается `heading`; раздела нет — None.

    Раздел — от своего заголовка до следующего заголовка того же или старшего уровня
    (подразделы входят в раздел); пункт — строка, которая после отступа начинается `<item>. `."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if line.startswith(heading)]
    if not starts:
        return None
    closing = re.compile(rf"^#{{1,{level}}} ")
    item_line = re.compile(rf"^\s*{re.escape(item)}\.\s")
    found: list[str] = []
    for line in lines[starts[0] + 1 :]:
        if closing.match(line):
            break
        if item_line.match(line):
            found.append(line)
    return found


def _section_line_changes(
    path: str, before: str | None, after: str | None, subject: tuple[str, ...]
) -> list[str]:
    """Строка пункта `subject[1]` раздела `subject[0]`, не равная себе до коммита.

    До коммита строка пункта обязана быть РОВНО ОДНА — иначе отказ: раздела нет либо пункт
    неоднозначен, и сличать нечего."""
    heading, item = subject
    lines_before = _section_lines(before or "", heading, item)
    if lines_before is None:
        raise HistoryRefusal(f"`{path}`: раздела `{heading}` нет до коммита (антивакуум)")
    if len(lines_before) != 1:
        raise HistoryRefusal(
            f"`{path}`: строк пункта {item} в разделе `{heading}` до коммита "
            f"{len(lines_before)}, а не одна — сличать нечего"
        )
    lines_after = _section_lines(after or "", heading, item)
    if lines_after != lines_before:
        return [
            f"строка пункта {item} раздела `{heading}` изменена: было {lines_before[0]!r}, "
            f"стало {lines_after!r}"
        ]
    return []


STATUS_LINE = re.compile(r"^\s*(?:-\s+)?status\s*:")


def _status_line_changes(
    path: str, before: str | None, after: str | None, subject: tuple[str, ...]
) -> list[str]:
    """Строки `status:`, удалённые или изменённые диффом пары.

    Дифф строк (`difflib`, без эвристики «мусора»): каждая строка `status:` стороны «до» в
    блоке замены или удаления названа. Вставка — в том числе отдельного ключа `status_note` —
    предметом не является. Пустой дифф и файл без строк `status:` до коммита — отказ."""
    if before is None:
        raise HistoryRefusal(f"`{path}`: файла нет до коммита — строк `status:` не было")
    if before == after:
        raise HistoryRefusal(f"`{path}`: дифф пуст — коммит файла не менял (антивакуум)")
    lines_before = before.splitlines()
    if not any(STATUS_LINE.match(line) for line in lines_before):
        raise HistoryRefusal(
            f"`{path}`: строк `status:` до коммита нет ни одной — факт ничего не проверил бы"
        )
    lines_after = (after or "").splitlines()
    matcher = difflib.SequenceMatcher(None, lines_before, lines_after, autojunk=False)
    changes: list[str] = []
    for tag, first, last, _, _ in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            changes.extend(
                f"строка `{line.strip()}` удалена или изменена"
                for line in lines_before[first:last]
                if STATUS_LINE.match(line)
            )
    return changes


JINJA_COMMENT = re.compile(r"\{#.*?#\}", re.S)


def _without_comments(path: str, text: str) -> str:
    """Исполняемое содержание файла: `.py` — `ast.dump` (комментариев в дереве нет, строка
    документации есть); `.html` — текст без комментариев шаблонизатора `{# … #}` (комментарий
    HTML `<!-- … -->` уходит в ответ и потому содержание); иной файл — текст целиком."""
    if path.endswith(".py"):
        return ast.dump(ast.parse(text))
    if path.endswith(".html"):
        return JINJA_COMMENT.sub("", text)
    return text


def _executable_changes(
    path: str, before: str | None, after: str | None, subject: tuple[str, ...]
) -> list[str]:
    """Изменение пары за вычетом комментариев: `.py` — `ast.dump`, `.html` — без `{# … #}`."""
    if before is None:
        return ["файл заведён коммитом"]
    if after is None:
        return ["файл снят коммитом"]
    if _without_comments(path, before) != _without_comments(path, after):
        return ["исполняемое содержание изменено (сличение без комментариев)"]
    return []


def _exits(statements: list[ast.stmt]) -> bool:
    """Ветка уходит из функции: её последний оператор — `return` или `raise`."""
    return bool(statements) and isinstance(statements[-1], (ast.Return, ast.Raise))


def _refusal_predicates(text: str) -> dict[str, Counter]:
    """Предикаты отказа каждой функции модуля (по имени, вложенные — тоже): текст условия каждого
    охранного `if`, чья ветка уходит из функции, и текст каждого `raise`. Сличается ТЕКСТ
    выражения (`ast.unparse`), а не номер строки: перенос строки предикат не меняет."""
    found: dict[str, Counter] = {}
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        predicates: Counter = Counter()
        for inner in ast.walk(node):
            if isinstance(inner, ast.If) and _exits(inner.body):
                predicates[f"if {ast.unparse(inner.test)}"] += 1
            elif isinstance(inner, ast.Raise):
                predicates[f"raise {ast.unparse(inner.exc) if inner.exc else ''}".strip()] += 1
        found[node.name] = predicates
    return found


def _refusal_predicate_changes(
    path: str, before: str | None, after: str | None, subject: tuple[str, ...]
) -> list[str]:
    """Предикаты отказа, которых после коммита нет или которых до коммита не было, — по функциям.

    Предмет — ЧТО действие отвергает (условие охранной ветки и `raise`), а не КАК отвечает:
    `return RedirectResponse(…)` → `return await respond(…)` под тем же условием предикат не
    меняет. Сличаются функции, стоявшие до коммита; снятая функция теряет все свои предикаты.
    Не `.py` — не предмет вида (`[]`). Модуль без единого предиката до коммита — отказ: сличать
    нечего (антивакуум)."""
    if not path.endswith(".py"):
        return []
    if before is None:
        return []
    predicates_before = _refusal_predicates(before)
    if not any(predicates_before.values()):
        raise HistoryRefusal(
            f"`{path}`: предикатов отказа до коммита нет ни одного — факт ничего не проверил бы"
        )
    predicates_after = _refusal_predicates(after) if after is not None else {}
    changes: list[str] = []
    for name, kept in predicates_before.items():
        now = predicates_after.get(name, Counter())
        for predicate in sorted(kept - now):
            changes.append(f"`{name}`: предикат отказа `{predicate}` снят или изменён")
        for predicate in sorted(now - kept):
            changes.append(f"`{name}`: предикат отказа `{predicate}` добавлен")
    return changes


ROUTE_METHODS = frozenset({"get", "post", "put", "patch", "delete"})


def _upper_bounded(node: ast.expr | None) -> bool:
    """Выражение объявляет верхнюю границу: вызов с ключом `le` (`Path(…, le=…)`)."""
    return isinstance(node, ast.Call) and any(keyword.arg == "le" for keyword in node.keywords)


def _bounded_annotation(annotation: ast.expr | None, aliases: frozenset[str]) -> bool:
    """Аннотация несёт границу: псевдоним модуля с границей либо `Annotated[…, X(…, le=…)]`."""
    if isinstance(annotation, ast.Name):
        return annotation.id in aliases
    if isinstance(annotation, ast.Subscript) and getattr(annotation.value, "id", None) == "Annotated":
        parts = (
            annotation.slice.elts if isinstance(annotation.slice, ast.Tuple) else [annotation.slice]
        )
        return any(_upper_bounded(part) for part in parts[1:])
    return False


def _unbounded_identifier_sources(text: str) -> tuple[list[str], int]:
    """Параметры-идентификаторы обработчиков маршрутов без верхней границы и число всех таких.

    Обработчик маршрута — функция верхнего уровня с декоратором `<роутер>.<метод>(…)`.
    Идентификатор — параметр `id` либо `*_id`. Граница — псевдоним модуля, присвоенный
    `Annotated[…, X(…, le=…)]`, та же форма прямо в аннотации либо значение по умолчанию
    `X(…, le=…)`."""
    tree = ast.parse(text)
    aliases = frozenset(
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and _bounded_annotation(node.value, frozenset())
    )
    unbounded: list[str] = []
    total = 0
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr in ROUTE_METHODS
            for decorator in node.decorator_list
        ):
            continue
        positional = node.args.posonlyargs + node.args.args
        defaults = [None] * (len(positional) - len(node.args.defaults)) + list(node.args.defaults)
        pairs = list(zip(positional, defaults)) + list(
            zip(node.args.kwonlyargs, node.args.kw_defaults)
        )
        for argument, default in pairs:
            if argument.arg != "id" and not argument.arg.endswith("_id"):
                continue
            total += 1
            if not (_bounded_annotation(argument.annotation, aliases) or _upper_bounded(default)):
                unbounded.append(f"`{node.name}({argument.arg})`")
    return unbounded, total


def _identifier_source_offences(
    path: str, before: str | None, after: str | None, subject: tuple[str, ...]
) -> list[str]:
    """Каждый источник идентификатора в файле ПОСЛЕ коммита плана несёт верхнюю границу.

    Прочтение `10-12#1` («правка НЕ ставится только там, где предмет замерен: закрытие одного
    из двух источников одной величины оставляет маршрут … открытым»): коммит плана, тронувший
    страничный модуль, оставляет границу на КАЖДОМ параметре-идентификаторе каждого обработчика
    маршрута этого модуля, а не на замеренном. Не `.py` — не предмет. Модуль без единого
    источника идентификатора до коммита — отказ (сличать нечего)."""
    if not path.endswith(".py") or after is None:
        return []
    if before is None or not _unbounded_identifier_sources(before)[1]:
        raise HistoryRefusal(
            f"`{path}`: источников идентификатора до коммита нет — факт ничего не проверил бы"
        )
    unbounded, _total = _unbounded_identifier_sources(after)
    return [f"источник идентификатора {name} остался без границы" for name in unbounded]


HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
CYRILLIC = re.compile(r"[А-Яа-яЁё]")
TEXT_RUN = re.compile(r"[^<>{}\"'`]+")


def _visible_text(text: str | None) -> Counter:
    """Фрагменты видимого текста шаблона: отрезки между разметкой, кавычками и скобками
    шаблонизатора, несущие кириллицу, — текст узлов, значения атрибутов, строковые литералы
    шаблонизатора. Комментарии `{# … #}` и `<!-- … -->` гасятся, пробелы сводятся к одному:
    перенос строки текста фрагмент не меняет."""
    if text is None:
        return Counter()
    flattened = " ".join(HTML_COMMENT.sub(" ", JINJA_COMMENT.sub(" ", text)).split())
    return Counter(
        fragment
        for fragment in (match.group().strip() for match in TEXT_RUN.finditer(flattened))
        if CYRILLIC.search(fragment)
    )


def _visible_text_losses(
    pairs: tuple[tuple[str, str | None, str | None], ...]
) -> list[tuple[str, str]]:
    """Фрагменты видимого текста, убранные коммитом и НЕ добавленные им же ни в одном файле.

    Прочтение `10-01#6` («тексты и подписи … переносятся ДОСЛОВНО»): перенос законен и между
    файлами, поэтому судится ВЕСЬ КОММИТ — каждый фрагмент, ушедший из файла, обязан прийти
    добавленным в том же коммите; переформулировка (ушёл старый, пришёл новый) называет старый.
    Новый текст без убранного предметом не является. Ни в одной паре до коммита нет видимого
    текста — отказ (сличать нечего)."""
    befores = {path: _visible_text(before) for path, before, _after in pairs}
    afters = {path: _visible_text(after) for path, _before, after in pairs}
    if not any(befores.values()):
        raise HistoryRefusal(
            "видимого текста до коммита нет ни в одном наблюдаемом пути — факт ничего не проверил бы"
        )
    added: Counter = Counter()
    for path in befores:
        added += afters[path] - befores[path]
    losses: list[tuple[str, str]] = []
    for path in befores:
        for fragment, count in sorted((befores[path] - afters[path]).items()):
            carried = min(count, added[fragment])
            added[fragment] -= carried
            if count > carried:
                losses.append(
                    (path, f"фрагмент видимого текста {fragment!r} убран и не перенесён дословно")
                )
    return losses


# Виды, чей предикат читает данные `subject`; у остальных `subject` пуст.
SUBJECT_KINDS = (DEFINITION_SOURCES, HEADER_FIELDS, SECTION_LINE)

CONTENT_PREDICATES: dict[
    str, Callable[[str, str | None, str | None, tuple[str, ...]], list[str]]
] = {
    DEFINITION_SOURCES: _definition_source_changes,
    HEADER_FIELDS: _header_field_changes,
    SECTION_LINE: _section_line_changes,
    STATUS_LINES_KEPT: _status_line_changes,
    EQUAL_WITHOUT_COMMENTS: _executable_changes,
    REFUSAL_PREDICATES_KEPT: _refusal_predicate_changes,
    IDENTIFIER_SOURCES_BOUNDED: _identifier_source_offences,
}

# Виды КОММИТА (план 15-32): предикат судит все наблюдаемые пары одного коммита вместе и
# называет путь каждого изменения сам.
COMMIT_PREDICATES: dict[
    str, Callable[[tuple[tuple[str, str | None, str | None], ...]], list[tuple[str, str]]]
] = {
    VISIBLE_TEXT_CARRIED: _visible_text_losses,
}


def _content_offences(
    journal: Iterable[Commit],
    fact: HistoryFact,
    revisions: Callable[[str, str], tuple[str | None, str | None]],
) -> list[ContentOffence]:
    """Каждое изменение содержания наблюдаемого пути коммитами плана — с коммитом и путём.

    Читаются только пары путей, которых коснулся коммит плана и которые покрыты перечнем
    `watched` (элемент с `/` на конце — каталог). Коммиты плана не коснулись ни одного
    наблюдаемого пути — отказ: факт ничего о плане не узнал (антивакуум)."""
    if not fact.watched:
        raise HistoryRefusal("перечень наблюдаемых путей пуст: факт содержания не судит ничего")
    offences: list[ContentOffence] = []
    touched = 0
    for commit in _plan_commits(journal, fact.scope):
        paths = [
            path for path in commit.paths if any(_covered_by(path, item) for item in fact.watched)
        ]
        touched += len(paths)
        if not paths:
            continue
        if fact.kind in COMMIT_PREDICATES:
            pairs = tuple((path, *revisions(commit.sha, path)) for path in paths)
            offences.extend(
                ContentOffence(commit.sha, commit.subject, path, detail)
                for path, detail in COMMIT_PREDICATES[fact.kind](pairs)
            )
            continue
        predicate = CONTENT_PREDICATES[fact.kind]
        for path in paths:
            before, after = revisions(commit.sha, path)
            offences.extend(
                ContentOffence(commit.sha, commit.subject, path, detail)
                for detail in predicate(path, before, after, fact.subject)
            )
    if not touched:
        raise HistoryRefusal(
            f"коммиты плана {fact.scope} не коснулись ни одного наблюдаемого пути "
            f"({', '.join(fact.watched[:3])}…) — факт содержания ничего не узнал (антивакуум)"
        )
    return offences


def _blob(revision: str, path: str, git: Callable[..., str] = _run_git) -> str | None:
    """Содержимое `path` в ревизии; пути в ревизии нет — None, прочий сбой git — отказ."""
    listing = git("-c", "core.quotePath=false", "ls-tree", "--name-only", revision, "--", path)
    if path not in listing.splitlines():
        return None
    return git("show", f"{revision}:{path}")


@cache
def _revisions(sha: str, path: str) -> tuple[str | None, str | None]:
    """Живая пара «до / после» коммита `sha` для `path`, прочитанная один раз за прогон."""
    return _blob(f"{sha}^", path), _blob(sha, path)


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


def _offences_of(
    journal: Iterable[Commit],
    identity: str,
    revisions: Callable[[str, str], tuple[str | None, str | None]] = _revisions,
) -> list[PathOffence] | list[ContentOffence]:
    fact = HISTORY_FACTS[identity]
    if fact.kind == PATHS:
        return _path_offences(_plan_commits(journal, fact.scope), fact.forbidden)
    return _content_offences(journal, fact, revisions)


def _introduced_definitions(
    journal: Iterable[Commit],
    scope: str,
    path: str,
    revisions: Callable[[str, str], tuple[str | None, str | None]] = _revisions,
) -> tuple[str, ...]:
    """Определения верхнего уровня, которые коммиты плана `scope` завели в `path`, в порядке
    появления (журнал — от новых к старым, обход — от старых). Ни один коммит плана `path` не
    касался — отказ."""
    introduced: list[str] = []
    touched = False
    for commit in reversed(_plan_commits(journal, scope)):
        if path not in commit.paths:
            continue
        touched = True
        before, after = revisions(commit.sha, path)
        known = _definitions(before or "")
        introduced.extend(
            name for name in _definitions(after or "") if name not in known and name not in introduced
        )
    if not touched:
        raise HistoryRefusal(f"коммиты плана {scope} не касались `{path}` — состав не снять")
    return tuple(introduced)


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
    """Правило согласия: каждый ключ `HISTORY_FACTS` — тождество записи переписи Фазы 10, его
    область есть номер его плана либо номер его фазы, перечень путей не пуст; и каждая строка
    реестра, называющая несущее правило, имеет запись здесь — иначе строка числилась бы
    принуждённой правилом, которое её не проверяет.

    ЛЕТОПИСЬ (план 15-32, задача 3). До плана 15-32 правило требовало от строки
    `verification: test`: записи планов 15-30/15-31 закрывали находки D-05. Владелец на чекпойнте
    плана 15-32 выбрал историческое прочтение (а′) и для строк `verification: none` класса
    `product-invariant`, сформулированных областью фазы или плана, — поэтому принимается любая
    строка Фазы 10. Область ФАЗЫ (`10`) — прочтение формулировок «фаза не заводит» (`10-01#3`,
    `10-24#2`): коммиты всех планов фазы, без коммитов `тип(10):` (граница выбора владельца).

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
        if record.phase != tool.DECISION_SCOPE_PHASE:
            problems.append(
                f"`{identity}`: фаза {record.phase} — не запрет Фазы {tool.DECISION_SCOPE_PHASE}"
            )
        plan_number = identity.partition("-PLAN.md#")[0]
        if fact.scope not in (plan_number, record.phase):
            problems.append(
                f"`{identity}`: область `{fact.scope}`, а план `{plan_number}` (фаза {record.phase})"
            )
        if fact.kind == PATHS:
            if not fact.forbidden or fact.watched or fact.subject:
                problems.append(
                    f"`{identity}`: вид `{PATHS}` несёт непустой `forbidden` и ничего иного"
                )
        elif fact.kind in CONTENT_PREDICATES or fact.kind in COMMIT_PREDICATES:
            if fact.forbidden or not fact.watched:
                problems.append(
                    f"`{identity}`: вид `{fact.kind}` несёт непустой `watched` и пустой `forbidden`"
                )
            if fact.kind in SUBJECT_KINDS and not fact.subject:
                problems.append(f"`{identity}`: вид `{fact.kind}` без данных `subject`")
            if (fact.kind == DEFINITION_SOURCES) != bool(fact.owner):
                problems.append(f"`{identity}`: `owner` стоит ровно у вида `{DEFINITION_SOURCES}`")
        else:
            problems.append(f"`{identity}`: вид `{fact.kind}` неизвестен")

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


def test_every_definition_group_is_what_its_owner_plan_introduced():
    """Состав группы вида `DEFINITION_SOURCES` СНЯТ ИСТОРИЕЙ: литерал `subject` равен множеству
    определений, которые коммиты плана `owner` завели в наблюдаемом файле, — без пропусков,
    лишних и повторов. Группа, набранная руками, разошлась бы с историей молча."""
    groups = {
        identity: fact for identity, fact in HISTORY_FACTS.items() if fact.kind == DEFINITION_SOURCES
    }
    assert groups, "фактов вида исходника определений нет — правило зеленело бы вакуумом"
    for identity, fact in sorted(groups.items()):
        (path,) = fact.watched
        introduced = _introduced_definitions(_git_journal(), fact.owner, path)
        assert len(set(fact.subject)) == len(fact.subject), f"`{identity}`: повтор в составе"
        assert set(fact.subject) == set(introduced), (
            f"`{identity}`: состав группы разошёлся с историей плана {fact.owner}: лишние "
            f"{sorted(set(fact.subject) - set(introduced))}, пропущенные "
            f"{sorted(set(introduced) - set(fact.subject))}"
        )


def test_control_a_doctored_revision_of_a_real_commit_reddens_10_40_1():
    """Замер направления вида содержания на ЖИВОЙ истории: настоящая пара коммита `415b0cfe`
    зелена, а та же пара с `status: passed` в шапке стороны «после» краснит запись
    `10-40-PLAN.md#1`, и назван ровно этот коммит, путь и поле."""
    journal = _git_journal()
    assert _offences_of(journal, "10-40-PLAN.md#1") == []

    def doctored(sha: str, path: str) -> tuple[str | None, str | None]:
        before, after = _revisions(sha, path)
        assert after is not None and "\nstatus: human_needed\n" in after, "якоря подмены нет"
        return before, after.replace("\nstatus: human_needed\n", "\nstatus: passed\n", 1)

    offences = _offences_of(journal, "10-40-PLAN.md#1", doctored)
    assert [(offence.sha[:8], offence.path, offence.detail) for offence in offences] == [
        (
            "415b0cfe",
            PHASE_10_DIR + "10-VERIFICATION.md",
            "поле шапки `status` изменено: 'human_needed' → 'passed'",
        )
    ]


# Коммит плана 10-38, заведший контроли цепи предков (запрет `10-38#5`; правило —
# `tests/test_pages/test_shell.py::test_the_ancestor_chain_controls_take_property_names_from_the_canon`).
PLAN_10_38_CONTROLS_COMMIT = "9809b643"
PLAN_10_38_CONTROLS_LITERAL = "PLAN_10_38_ANCESTOR_CHAIN_CONTROLS"


def _declared_tuple(source: str, name: str) -> tuple[str, ...]:
    """Литерал кортежа строк, присвоенный имени `name` на уровне модуля, — по `ast`, без ввоза."""
    for node in ast.parse(source).body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
        ):
            return tuple(ast.literal_eval(node.value))
    raise HistoryRefusal(f"литерала `{name}` в модуле нет — сверять нечего")


def test_the_plan_10_38_control_group_in_the_shell_suite_is_what_history_introduced():
    """Состав `PLAN_10_38_ANCESTOR_CHAIN_CONTROLS` в `test_shell.py` СНЯТ ИСТОРИЕЙ: это контроли
    (`test_control_*`), которые коммит `9809b643` плана 10-38 завёл в файл, за вычетом снятых с
    тех пор (`test_control_a_trapping_ancestor_reddens` — план 10-42). Модуль читается текстом,
    а не ввозится."""
    commits = [
        commit
        for commit in _plan_commits(_git_journal(), "10-38")
        if commit.sha.startswith(PLAN_10_38_CONTROLS_COMMIT)
    ]
    assert len(commits) == 1, f"коммит {PLAN_10_38_CONTROLS_COMMIT} плана 10-38 не найден ровно один"
    before, after = _revisions(commits[0].sha, SHELL_SUITE)
    known = _definitions(before or "")
    introduced = [
        name for name in _definitions(after or "") if name not in known and name.startswith("test_control_")
    ]
    assert introduced, "коммит не завёл ни одного контроля — сверять не с чем (антивакуум)"
    source = (PROJECT_ROOT / SHELL_SUITE).read_text(encoding="utf-8")
    today = _definitions(source)
    surviving = {name for name in introduced if name in today}
    declared = _declared_tuple(source, PLAN_10_38_CONTROLS_LITERAL)
    assert len(set(declared)) == len(declared), f"повтор в `{PLAN_10_38_CONTROLS_LITERAL}`"
    assert set(declared) == surviving, (
        f"состав `{PLAN_10_38_CONTROLS_LITERAL}` разошёлся с историей: лишние "
        f"{sorted(set(declared) - surviving)}, пропущенные {sorted(surviving - set(declared))}; "
        f"заведено коммитом {introduced}"
    )


# --- исторические прочтения плана 15-32: контроли видов и направление на живой истории --------


def test_control_a_phase_scope_selects_every_plan_of_the_phase_and_no_unscoped_commit():
    """Область ФАЗЫ `10`: коммиты `тип(10-NN):` любого плана и `тип(010-044):` — да; коммит
    правки ревизии без номера плана (`docs(10): …`, `fix(10): …`), оркестратора без области и
    чужой фазы — нет (граница выбора владельца, план 15-32)."""
    review_fix = Commit("9" * 40, "fix(10): CR-01 правка ревизии", ("app/pages/notices.py",))
    other_phase = Commit("8" * 40, "feat(11-14): чужая фаза", ("app/pages/notices.py",))
    journal = SYNTHETIC_JOURNAL + (review_fix, other_phase)
    selected = _plan_commits(journal, "10")
    assert [commit.sha for commit in selected] == [
        PLAN_COMMIT.sha,
        PADDED_PLAN_COMMIT.sha,
        NEIGHBOUR_COMMIT.sha,
    ], [commit.subject for commit in selected]
    with pytest.raises(HistoryRefusal, match="не в форме"):
        _plan_commits(journal, "10-")


def test_control_a_lost_visible_text_fragment_is_named_and_a_carried_one_is_not():
    """Вид «видимый текст переносится дословно»: переформулировка подписи называет прежнюю;
    перенос фрагмента в другой файл того же коммита, перенос строки и правка комментария — нет;
    добавленный текст — не предмет; ни одного фрагмента до коммита — отказ."""
    card = '<p class="hint">Заполните группы, дни и время</p>\n<span aria-label="Аккаунт">x</span>\n'
    reworded = card.replace("Заполните группы", "Выберите группы")
    assert _visible_text_losses((("a.html", card, reworded),)) == [
        ("a.html", "фрагмент видимого текста 'Заполните группы, дни и время' убран и не перенесён дословно")
    ]
    moved_out = card.replace('<p class="hint">Заполните группы, дни и время</p>\n', "")
    moved_in = "{# перенос #}<p>Заполните группы,\n   дни и время</p>\n"
    assert _visible_text_losses((("a.html", card, moved_out), ("b.html", "", moved_in))) == []
    assert _visible_text_losses((("a.html", card, card + "<p>Новая подпись</p>"),)) == []
    commented = card.replace("<p", "{# комментарий #}<p", 1)
    assert _visible_text_losses((("a.html", card, commented),)) == []
    with pytest.raises(HistoryRefusal, match="видимого текста до коммита нет"):
        _visible_text_losses((("a.html", "<div></div>", "<p>Текст</p>"),))


REFUSING_HANDLER = (
    "async def delete(request, user, account_id):\n"
    "    if not user:\n"
    '        return RedirectResponse(url="/login", status_code=302)\n'
    "    if account_id < 1:\n"
    "        raise HTTPException(status_code=404)\n"
    '    return RedirectResponse(url="/accounts", status_code=302)\n'
)


def test_control_a_changed_refusal_predicate_is_named_and_a_changed_answer_is_not():
    """Вид «предикаты отказа сохранены»: изменённое условие охранной ветки, снятый `raise` и
    добавленная ветка отказа называются; тот же отказ через слой ответа (`respond`) — нет; не
    `.py` — не предмет; модуль без предикатов до коммита — отказ."""
    path = "app/pages/accounts.py"
    layered = REFUSING_HANDLER.replace(
        'return RedirectResponse(url="/login", status_code=302)',
        'return await respond(request, redirect="/login")',
    )
    assert _refusal_predicate_changes(path, REFUSING_HANDLER, layered, ()) == []
    widened = REFUSING_HANDLER.replace("if not user:", "if not user or user.blocked:")
    assert _refusal_predicate_changes(path, REFUSING_HANDLER, widened, ()) == [
        "`delete`: предикат отказа `if not user` снят или изменён",
        "`delete`: предикат отказа `if not user or user.blocked` добавлен",
    ]
    unraised = REFUSING_HANDLER.replace(
        "        raise HTTPException(status_code=404)\n", "        return None\n"
    )
    assert _refusal_predicate_changes(path, REFUSING_HANDLER, unraised, ()) == [
        "`delete`: предикат отказа `raise HTTPException(status_code=404)` снят или изменён"
    ]
    assert _refusal_predicate_changes("app/templates/x.html", "<p>", "<div>", ()) == []
    with pytest.raises(HistoryRefusal, match="предикатов отказа до коммита нет"):
        _refusal_predicate_changes(path, "def f():\n    return 1\n", "def f():\n    return 2\n", ())


ROUTES_BEFORE = (
    "from typing import Annotated\n"
    "from fastapi import APIRouter, Form, Path\n"
    "router = APIRouter()\n\n\n"
    '@router.post("/s/{schedule_id}/toggle")\n'
    "async def toggle(schedule_id: int):\n"
    "    return schedule_id\n\n\n"
    '@router.post("/s")\n'
    "async def create(ad_id: int = Form(...), account_id: int | None = Form(None)):\n"
    "    return ad_id\n"
)
ROUTES_AFTER = ROUTES_BEFORE.replace(
    "router = APIRouter()\n",
    "router = APIRouter()\nIdPathBound = Annotated[int, Path(ge=1, le=ID_MAX)]\n",
).replace("schedule_id: int)", "schedule_id: IdPathBound)").replace(
    "ad_id: int = Form(...)", "ad_id: Annotated[int, Form(ge=1, le=ID_MAX)]"
).replace("Form(None)", "Form(None, le=ID_MAX)")


def test_control_an_unbounded_identifier_source_is_named():
    """Вид «граница на каждом источнике»: все три источника ограничены (псевдоним, аннотация,
    значение по умолчанию) — тишина; граница поставлена только на замеренном входе — остальные
    названы; модуль без источников до коммита — отказ."""
    path = "app/pages/schedules.py"
    assert _identifier_source_offences(path, ROUTES_BEFORE, ROUTES_AFTER, ()) == []
    only_measured = ROUTES_BEFORE.replace(
        "schedule_id: int)", "schedule_id: Annotated[int, Path(ge=1, le=ID_MAX)])"
    )
    assert _identifier_source_offences(path, ROUTES_BEFORE, only_measured, ()) == [
        "источник идентификатора `create(ad_id)` остался без границы",
        "источник идентификатора `create(account_id)` остался без границы",
    ]
    with pytest.raises(HistoryRefusal, match="источников идентификатора до коммита нет"):
        _identifier_source_offences(path, "x = 1\n", "x = 2\n", ())


def _doctored_after(sha_prefix: str, path: str, old: str, new: str):
    """Живые пары, у которых сторона «после» пары `sha_prefix`/`path` доктóрена заменой."""

    def revisions(sha: str, touched: str) -> tuple[str | None, str | None]:
        before, after = _revisions(sha, touched)
        if sha.startswith(sha_prefix) and touched == path:
            assert after is not None and old in after, f"якоря подмены нет: {sha_prefix} {path}"
            after = after.replace(old, new, 1)
        return before, after

    return revisions


PLAN_15_32_CONTENT_DIRECTIONS = {
    "10-01-PLAN.md#6": (
        "14face55", "app/templates/ads/includes/sched_card.html",
        "Заполните группы, дни и время", "Выберите группы, дни и время",
    ),
    "10-03-PLAN.md#6": ("1889ac05", "app/pages/accounts.py", "    if not user:", "    if user is None:"),
    "10-12-PLAN.md#1": (
        "73df7780", "app/pages/schedules.py", "schedule_id: ScheduleIdPath,", "schedule_id: int,",
    ),
    "10-22-PLAN.md#1": (
        "a3972cfd", "app/templates/ads/partials/sched_delete_response.html",
        'hx-swap-oob="innerHTML:#sched-count"', 'hx-swap-oob="innerHTML:#{{ count_target }}"',
    ),
}


@pytest.mark.parametrize("identity", sorted(PLAN_15_32_CONTENT_DIRECTIONS))
def test_control_a_doctored_real_revision_reddens_each_plan_15_32_content_fact(identity):
    """Замер направления видов содержания плана 15-32 на ЖИВОЙ истории: настоящие пары
    зелены, а та же история с доктóренной стороной «после» одного настоящего коммита плана
    краснит запись, и назван ровно этот коммит и путь."""
    sha_prefix, path, old, new = PLAN_15_32_CONTENT_DIRECTIONS[identity]
    journal = _git_journal()
    assert _offences_of(journal, identity) == []
    offences = _offences_of(journal, identity, _doctored_after(sha_prefix, path, old, new))
    assert offences, f"`{identity}`: подмена стороны «после» {sha_prefix} не названа"
    assert {(offence.sha[:8], offence.path) for offence in offences} == {(sha_prefix, path)}, [
        str(offence) for offence in offences
    ]


@pytest.mark.parametrize("identity", ["10-01-PLAN.md#3", "10-24-PLAN.md#2", "10-31-PLAN.md#1"])
def test_control_a_synthetic_plan_commit_on_the_notice_registry_reddens(identity):
    """Замер направления фактов реестра кодов: копия живого журнала с синтетическим коммитом
    плана области записи на `app/pages/notices.py` краснит запись; тот же путь коммитом правки
    ревизии `fix(10): …` — нет (граница выбора владельца, план 15-32)."""
    fact = HISTORY_FACTS[identity]
    scope = fact.scope if "-" in fact.scope else f"{fact.scope}-99"
    journal = _git_journal()
    assert _offences_of(journal, identity) == []
    review_fix = Commit("e" * 40, "fix(10): правка ревизии", (NOTICES,))
    assert _offences_of(journal + (review_fix,), identity) == []
    synthetic = Commit("f" * 40, f"feat({scope}): новый код", (NOTICES,))
    assert _offences_of(journal + (synthetic,), identity) == [
        PathOffence(synthetic.sha, synthetic.subject, NOTICES, NOTICES)
    ]
