"""Команда посева артефакта обхода Фазы 10 ИСПОЛНИМА НА СЕГОДНЯШНЕЙ СХЕМЕ.

ЗАЧЕМ. Обход Фазы 10 третий раз подряд начался с отказа собственного прибора, и на
этот раз прибор не соврал в числах, а НЕ ДАЛ ОБХОДУ НАЧАТЬСЯ. Команда посева §
«Как привести стенд в нужное состояние» упала первым же действием:

    CheckViolationError: new row for relation "schedules" violates check constraint
    "ck_schedules_active_requires_next_run"

Команда сеет `is_active=True` при `next_run_at=None`. Ограничение, отвергающее ровно
эту пару, отгружено коммитом `d46780b` В ТОТ ЖЕ ДЕНЬ, что и обход. Команда написана
планом 10-10 (2026-09-03) и взяла набор полей у `_seed_schedule` тогдашней суиты
(`tests/test_pages/test_editor_schedules.py`), где поля `next_run_at` в наборе не было
вовсе. ДЕРЕВО УШЛО ВПЕРЁД АРТЕФАКТА; АРТЕФАКТ ЭТОГО НЕ УЗНАЛ, ПОТОМУ ЧТО СТЕРЕГУЩЕГО
ПРАВИЛА У КОМАНДЫ ПОСЕВА НЕ БЫЛО НИ ОДНОГО. Запись дефекта — `G-10-A3` раздела
`## Gaps` того же артефакта.

⚠️ ХРУПКОСТЬ РАЗБОРА НАЗЫВАЕТСЯ ЗДЕСЬ ПРЯМО, А НЕ ОСТАВЛЯЕТСЯ ЧИТАТЕЛЮ. Правило
привязано к ФОРМЕ раздела: заголовок «Как привести стенд в нужное состояние», блок в
тройных кавычках, вызов интерпретатора с ключом `-c`. Перестройка раздела уронит
правило ОТКАЗОМ О РАЗБОРЕ — и это принято сознательно. Альтернатива (правило,
выбирающее блок молча, когда форма разошлась) вернула бы ровно тот класс, который
`G-10-A3` и есть: зелёный прибор над негодным текстом.

⚠️ ГРАНИЦА ИСПОЛНЕНИЯ НАЗЫВАЕТСЯ СВОИМ ИМЕНЕМ, А НЕ ПРЯЧЕТСЯ. Правило ИСПОЛНЯЕТ ТЕКСТ
ЗАПИСИ ПРОЕКТА — файл, лежащий в том же дереве и проходящий ту же ревизию, что
исходники. Исполняется РОВНО ОДИН УЗЕЛ — тело цикла, строящего `Schedule(...)`, — а не
программа целиком: программа целиком построила бы движок по `DATABASE_URL` из `.env`,
то есть вставила бы строки в БОЕВУЮ базу (рабочее дерево и прод смотрят в одну базу —
замер `walkthrough.environment` артефакта). Никакой строки, кроме тела цикла, правило
не исполняет.

⚠️ ПРОСТРАНСТВО ИМЁН, ВЫДАВАЕМОЕ ТЕЛУ ЦИКЛА, ПЕРЕЧИСЛЕНО ЗДЕСЬ ДОСЛОВНО, И ЭТО ДОГОВОР
С АРТЕФАКТОМ, А НЕ ПОДРОБНОСТЬ РЕАЛИЗАЦИИ. Выдаются ЧЕТЫРЕ ПРЕДМЕТНЫХ имени:

    Schedule              — настоящий класс модели `app.models.schedule`
    compute_next_run_at   — настоящий вычислитель `app.services.schedule_service`
    ad, acc               — носители идентификаторов посеянных объявления и аккаунта
    s                     — накопитель с методом `add`

— и ПЯТЫЙ ключ `__builtins__`, узкий перечень встроенных имён (`ALLOWED_BUILTINS`).

⚠️ ПЯТЫЙ КЛЮЧ НАЗВАН ЗДЕСЬ ПОТОМУ, ЧТО ПРЕЖНЯЯ ЗАПИСЬ ОПИСЫВАЛА ГРАНИЦУ ШИРЕ ФАКТА
(WR-04, ревизия 2026-09-11). Она утверждала «ровно четыре имени и ничего сверх», а
`exec(code, namespace)` при ОТСУТСТВИИ ключа `__builtins__` в словаре ПОДСТАВЛЯЕТ
настоящий модуль встроенных имён сам: тело цикла имело доступ к `__import__`, `open`,
`eval` и через них ко всему интерпретатору и файловой системе прогона. Названная
«несущей» граница держалась комментарием. Теперь ключ подаётся ЯВНО, а его отсутствие
закрыто контролем-зубом (`test_control_negative_the_loop_body_cannot_reach_the_interpreter`),
а не заявлением. Пустым словарём граница не ставится: тело цикла читает `range`, и
запрет всех встроенных имён подряд уронил бы основное правило отказом ПРИБОРА.

⚠️ ЧТО ЭТОТ ПЕРЕЧЕНЬ НЕ ЯВЛЯЕТСЯ ПЕСОЧНИЦЕЙ — ГОВОРИТСЯ ПРЯМО, ЧТОБЫ НЕ ПОВТОРИТЬ ТУ
ЖЕ ОШИБКУ ВТОРОЙ РАЗ. Песочницы для Python не существует: из любого объекта достижимы
`().__class__.__bases__` и `__subclasses__()`. Несущая граница здесь ДРУГАЯ — артефакт
лежит в том же дереве и проходит ту же ревизию, что исходники; перечень снимает
СЛУЧАЙНОЕ и ровно на это претендует. Разбор — у самой константы.

Всякое ПРЕДМЕТНОЕ имя, которое тело цикла читает и которого в перечне выше нет, обязано
ВЫЧИСЛЯТЬСЯ ВНУТРИ САМОГО ТЕЛА. Имя, вычисленное программой артефакта ВЫШЕ цикла, при
исполнении одного узла не существует, и правило упало бы отказом о НЕИЗВЕСТНОМ ИМЕНИ —
то есть отказом ПРИБОРА, выданным за отказ предмета. ⚠️ ТА ЖЕ ЦЕНА ТЕПЕРЬ У ВСТРОЕННЫХ
ИМЁН: тело цикла, начавшее читать встроенное имя вне `ALLOWED_BUILTINS`, покраснит
модуль `NameError` — и починка состоит в том, чтобы дописать имя в перечень СОЗНАТЕЛЬНО,
проверив, что оно чистое.

⚠️ ЧЕГО ЭТО ПРАВИЛО НЕ ДОКАЗЫВАЕТ. Оно НЕ доказывает, что команда посева отработает НА
БОЕВОЙ БАЗЕ: схема тестовой базы создаётся из моделей (`Base.metadata.create_all`), а
боевая живёт ревизиями Alembic. Оно доказывает РОВНО ОДНО: набор полей, которым
артефакт строит расписание, СЕГОДНЯШНЕЙ СХЕМЕ МОДЕЛЕЙ не противоречит. Совпадение двух
половин схемы держат ДРУГИЕ правила, и они названы здесь поимённо, а не
подразумеваются: `tests/test_models/test_schedule_active_requires_next_run.py` и
`tests/test_migrations/test_0022_schedules_active_requires_next_run.py`.
"""

import ast
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import ACTIVE_REQUIRES_NEXT_RUN_NAME, Schedule
from app.models.user import User
from app.services.schedule_service import compute_next_run_at

# Предмет модуля — ЗАПИСЬ проекта, а не его продукт. Основание маркера, его
# граница годности и запрет выключать каталог — `tests/test_planning/__init__.py`;
# само имя объявлено хуком в `tests/conftest.py`.
pytestmark = pytest.mark.planning

TREE_ROOT = Path(__file__).resolve().parents[2]
WALKTHROUGH_PATH = (
    TREE_ROOT
    / ".planning"
    / "phases"
    / "10-rychag-components-modal-html"
    / "10-UAT.md"
)

# ⚠️ ПУТЬ ЗДЕСЬ ОДИН, И ГРАНИЦА НАЗВАНА: правило стережёт РОВНО ОДНУ команду РОВНО
# ОДНОГО артефакта. Прочие записи проекта, несущие исполнимый текст по живым моделям,
# этим правилом НЕ СТЕРЕГУТСЯ — ни одной. Это передаётся следующему кругу прямо, а не
# выдаётся за общее решение.
SEED_SECTION_HEADING = "## Как привести стенд в нужное состояние"

_FENCED_BLOCK_RE = re.compile(r"^```[^\n]*\n(?P<body>.*?)^```", re.M | re.S)
_INTERPRETER_CALL_RE = re.compile(r"python\s+-c\s+'(?P<program>.*)'\s*\Z", re.S)
_SAME_LEVEL_HEADING_RE = re.compile(r"^## ", re.M)

# Имя, под которым тело цикла артефакта строит расписание. Литерал здесь ОДИН и
# описывает не колонку схемы, а ИМЯ В ЧУЖОМ ИСХОДНИКЕ — выводить его неоткуда.
SCHEDULE_CALL_NAME = "Schedule"

# ВСТРОЕННЫЕ ИМЕНА, ВЫДАВАЕМЫЕ ТЕЛУ ЦИКЛА, — УЗКИЙ ПЕРЕЧЕНЬ, А НЕ МОДУЛЬ ЦЕЛИКОМ
# (WR-04). Пустым словарём здесь не обойтись: тело цикла артефакта читает
# `range`, и запрет всех встроенных имён подряд уронил бы ОСНОВНОЕ правило
# модуля отказом ПРИБОРА, выданным за отказ предмета.
#
# ЧТО ВОШЛО: имена, которыми строят ЗНАЧЕНИЯ, — перебор, длина, приведение
# типов, сортировка, арифметика. Все они чистые: ни файла, ни сети, ни импорта.
#
# ЧЕГО НЕТ НАМЕРЕННО: `__import__`, `open`, `eval`, `exec`, `compile`, `input`,
# `globals`, `locals`, `vars`, `getattr`, `setattr`, `breakpoint` — то есть
# ровно те имена, через которые тело цикла дотягивалось до файловой системы и
# сети прогона, пока словарь встроенных имён подставлялся сам собой. Отсутствие
# первого закреплено контролем-зубом, а не заявлено.
#
# ⚠️ ЭТО ГИГИЕНА, А НЕ ПЕСОЧНИЦА, И ЭТО ГОВОРИТСЯ ПРЯМО. Песочницы для Python
# не существует: из любого объекта достижимы `().__class__.__bases__` и
# `__subclasses__()`, то есть КТО УГОДНО, ПИШУЩИЙ ТЕЛО ЦИКЛА НАМЕРЕННО, выйдет
# наружу и через этот перечень. Несущая граница здесь ДРУГАЯ и названа в шапке:
# артефакт лежит в том же дереве и проходит ту же ревизию, что исходники.
# Перечень снимает СЛУЧАЙНОЕ — опечатку, скопированный из другого места вызов
# `open`, — и ровно на это претендует. Прежняя запись претендовала на большее,
# чем стояло; эта не претендует ни на что сверх измеренного.
ALLOWED_BUILTINS: dict[str, object] = {
    name: __builtins__[name]
    if isinstance(__builtins__, dict)
    else getattr(__builtins__, name)
    for name in (
        "abs",
        "bool",
        "dict",
        "divmod",
        "enumerate",
        "float",
        "frozenset",
        "int",
        "len",
        "list",
        "max",
        "min",
        "range",
        "reversed",
        "round",
        "set",
        "sorted",
        "str",
        "sum",
        "tuple",
        "zip",
    )
}


def walkthrough_source() -> str:
    """Исходник артефакта обхода Фазы 10 — и ничего кроме него."""
    return WALKTHROUGH_PATH.read_text(encoding="utf-8")


def seed_section(text: str) -> str:
    """Раздел «Как привести стенд в нужное состояние» ЦЕЛИКОМ.

    Границы — заголовок раздела и СЛЕДУЮЩИЙ заголовок того же уровня. Разбор по
    форме, а не по тексту шага: правка формулировки шага не имеет права ронять
    правило.
    """
    assert text.count(SEED_SECTION_HEADING) == 1, (
        f"заголовок {SEED_SECTION_HEADING!r} встречается в артефакте "
        f"{text.count(SEED_SECTION_HEADING)} раз(а), а не один — разбирать нечего, "
        "и молчаливый выбор одного из нескольких вернул бы ровно тот класс, "
        "который правило и стережёт"
    )
    start = text.index(SEED_SECTION_HEADING) + len(SEED_SECTION_HEADING)
    rest = text[start:]
    boundary = _SAME_LEVEL_HEADING_RE.search(rest)
    return rest[: boundary.start()] if boundary else rest


def seed_program(text: str) -> str:
    """Тело программы `uv run python -c '…'` из раздела посева.

    Программ в разделе обязано быть РОВНО ОДНА — иначе отказ С ИМЕНЕМ ЧИСЛА, а не
    молчаливый выбор первой попавшейся.
    """
    programs = [
        found.group("program")
        for found in (
            _INTERPRETER_CALL_RE.search(block.group("body").strip())
            for block in _FENCED_BLOCK_RE.finditer(seed_section(text))
        )
        if found is not None
    ]
    assert len(programs) == 1, (
        f"в разделе посева программ интерпретатора {len(programs)}, а не одна — "
        "правило не имеет права выбирать между ними молча"
    )
    return programs[0]


def seed_schedule_loop(program: str) -> tuple[ast.AST, frozenset[str]]:
    """Узел цикла, строящего `Schedule(...)`, и множество имён-ключей вызова.

    Разбор идёт ДЕРЕВОМ, а не образцом строки: образец строки согласился бы с
    закомментированным вызовом и разошёлся бы с программой при первой же правке
    отступов.
    """
    tree = ast.parse(program)

    loops: list[tuple[ast.AST, list[ast.Call]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            continue
        calls = [
            call
            for statement in node.body
            for call in ast.walk(statement)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == SCHEDULE_CALL_NAME
        ]
        if calls:
            loops.append((node, calls))

    assert len(loops) == 1, (
        f"циклов, строящих {SCHEDULE_CALL_NAME}(...), в программе посева "
        f"{len(loops)}, а не один — правило не имеет права выбирать молча"
    )
    loop, calls = loops[0]
    assert len(calls) == 1, (
        f"вызовов {SCHEDULE_CALL_NAME}(...) в теле цикла {len(calls)}, а не один — "
        "ключи двух вызовов слились бы в одно множество и скрыли бы разницу"
    )
    return loop, frozenset(
        keyword.arg for keyword in calls[0].keywords if keyword.arg is not None
    )


def rows_built_by_the_seed_loop(
    program: str, ad_id: int, account_id: int
) -> list[Schedule]:
    """Строки, построенные ТЕЛОМ ЦИКЛА артефакта, — исполнением, а не чтением.

    ⚠️ ИСПОЛНЯЕТСЯ РОВНО УЗЕЛ ЦИКЛА: в скомпилированный модуль кладётся ОДИН
    узел, и эту половину границы держит сама сборка, а не комментарий.

    ⚠️ ПРОСТРАНСТВО ИМЁН ВЫДАЁТСЯ ПЯТЬЮ КЛЮЧАМИ, А НЕ ЧЕТЫРЬМЯ: пятый —
    `__builtins__`, и подаётся он ЯВНО узким перечнем `ALLOWED_BUILTINS`. Без
    этого ключа `exec` подставляет модуль встроенных имён целиком (WR-04).
    Чем этот перечень является и чем НЕ является — разобрано у самой константы.
    """
    loop, _ = seed_schedule_loop(program)

    built: list[Schedule] = []

    class _Sink:
        """Накопитель под именем `s`: у сессии артефакта берётся ОДИН метод."""

        def add(self, row: Schedule) -> None:
            built.append(row)

    namespace = {
        # ⚠️ КЛЮЧ `__builtins__` ПОДАЁТСЯ ЯВНО, И ЭТО НЕСУЩАЯ СТРОКА (WR-04).
        # `exec(code, namespace)` при его ОТСУТСТВИИ подставляет настоящий
        # модуль встроенных имён — то есть прежний словарь выдавал телу цикла не
        # четыре имени, а четыре плюс весь интерпретатор. Граница, объявленная
        # шапкой «несущей», держалась комментарием.
        "__builtins__": dict(ALLOWED_BUILTINS),
        "Schedule": Schedule,
        "compute_next_run_at": compute_next_run_at,
        "ad": SimpleNamespace(id=ad_id),
        "acc": SimpleNamespace(id=account_id),
        "s": _Sink(),
    }

    module = ast.Module(body=[loop], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(  # noqa: S102 — граница исполнения названа в шапке модуля
        compile(module, "<10-UAT.md: тело цикла посева>", "exec"), namespace
    )
    return built


async def seed_stand_owner(session) -> tuple[int, int]:
    """Пользователь, аккаунт и объявление — ТЕМИ ЖЕ МОДЕЛЯМИ, что и суита.

    Возвращает идентификаторы объявления и аккаунта: ровно то, что тело цикла
    артефакта читает с носителей `ad` и `acc`.
    """
    user = User(
        email="uat10-stand@test.com", password_hash="x", name="UAT10 Stand"
    )
    session.add(user)
    await session.flush()

    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials="UAT10-account",
        status="connected",
    )
    session.add(account)
    await session.flush()

    ad = Ad(
        user_id=user.id,
        title="UAT10-объявление обхода",
        text="UAT10- текст объявления обхода",
        images=[],
    )
    session.add(ad)
    await session.flush()

    return ad.id, account.id


def test_the_seed_program_parses_and_builds_exactly_one_schedule():
    """АНТИВАКУУМ РАЗБОРА: в разделе посева ОДНА программа и ОДИН строящий цикл.

    Без этого утверждения красный поведенческий прогон был бы неотличим от отказа
    разбора: читатель не узнал бы, упало ли правило на схеме или на форме раздела.
    """
    program = seed_program(walkthrough_source())
    loop, keys = seed_schedule_loop(program)

    assert isinstance(loop, (ast.For, ast.AsyncFor, ast.While))
    assert keys, (
        "вызов Schedule(...) в программе артефакта не несёт НИ ОДНОГО ключа — "
        "множество имён пусто, и всякое утверждение о покрытии полей было бы "
        "утверждением о пустоте"
    )


@pytest.mark.asyncio
async def test_the_seeded_row_satisfies_todays_schema(db_session):
    """ПОВЕДЕНЧЕСКАЯ ПОЛОВИНА: строки артефакта ложатся в НАСТОЯЩУЮ схему.

    ⚠️ ЧТО ЭТА ПОЛОВИНА ЛОВИТ, А ЧЕГО НЕ ЛОВИТ. Она ловит нарушение СЕГОДНЯШНИМИ
    значениями сегодняшних ограничений — ровно то падение, на котором остановился
    обход `walkthrough_3`. Она НЕ ловит умолчание о поле, добавленном схеме завтра,
    если сегодняшние значения его случайно удовлетворяют: это предмет статической
    половины (`test_every_checked_column_is_named_by_the_seed_program`), и ни одна
    из двух не покрывает предмет другой.
    """
    ad_id, account_id = await seed_stand_owner(db_session)

    built = rows_built_by_the_seed_loop(
        seed_program(walkthrough_source()), ad_id, account_id
    )

    # ⚠️ АНТИВАКУУМ ДО ВСТАВКИ, А НЕ ПОСЛЕ: цикл, не построивший ничего, дал бы
    # зелёную вставку пустоты, и «команда исполнима» было бы неотличимо от
    # «команда не сеет ничего».
    assert built, (
        "тело цикла артефакта не построило НИ ОДНОЙ строки — вставлять нечего, "
        "и зелёный вердикт утверждал бы пустоту"
    )

    for row in built:
        db_session.add(row)
    await db_session.commit()


# --- Статическая половина: поля ограничений добываются, а не выписываются -------
#
# ⚠️ ЗАМЕР, ОПРЕДЕЛИВШИЙ ФОРМУ ЭТОЙ ПОЛОВИНЫ (2026-09-11, SQLAlchemy 2.0):
# у `CheckConstraint`, заданного СТРОКОЙ условия, коллекция `.columns` ПУСТА —
# движок не разбирает текст условия на колонки. Поэтому имена колонок, названных
# таким ограничением, добываются СЛИЧЕНИЕМ текста условия со списком колонок САМОЙ
# таблицы: обе стороны сличения приходят из модели, и выписанного имени колонки в
# правиле нет ни одного. У `ForeignKeyConstraint`/`PrimaryKeyConstraint` коллекция
# непуста и берётся как есть.


def _columns_named_by(constraint, table) -> frozenset[str]:
    """Имена колонок таблицы, названные ОДНИМ ограничением."""
    named = frozenset(column.name for column in getattr(constraint, "columns", ()))
    if named:
        return named
    sqltext = getattr(constraint, "sqltext", None)
    if sqltext is None:
        return frozenset()
    condition = str(sqltext)
    return frozenset(
        name
        for name in table.columns.keys()
        if re.search(rf"\b{re.escape(name)}\b", condition)
    )


def constrained_columns() -> frozenset[str]:
    """Имена колонок, названные ограничениями таблицы модели расписания.

    ⚠️ ИЗ МНОЖЕСТВА ИЗЫМАЮТСЯ КОЛОНКИ, ЗНАЧЕНИЕ КОТОРЫХ ПИШЕТ САМА БАЗА, и
    основание названо, а не умолчано: первичный ключ с автонумерацией назван
    `PrimaryKeyConstraint`, но подать его ключом вызова писатель НЕ МОЖЕТ — правило,
    требующее этого, требовало бы невозможного и краснело бы всегда. Признак
    изъятия добывается у колонки (`primary_key` + `autoincrement`), а не выписан
    именем.
    """
    table = Schedule.__table__
    written_by_the_database = frozenset(
        column.name
        for column in table.columns
        if column.primary_key and column.autoincrement
    )
    named: frozenset[str] = frozenset()
    for constraint in table.constraints:
        named |= _columns_named_by(constraint, table)
    return named - written_by_the_database


def uncovered_constraint_columns(text: str) -> frozenset[str]:
    """Поля ограничений, НЕ названные ключами вызова `Schedule(...)` артефакта."""
    _, keys = seed_schedule_loop(seed_program(text))
    return constrained_columns() - keys


def test_every_checked_column_is_named_by_the_seed_program():
    """СТАТИЧЕСКАЯ ПОЛОВИНА: каждое поле ограничений названо командой посева.

    ⚠️ ЗАЧЕМ ЭТА ПОЛОВИНА ПРИ ЖИВОЙ ПОВЕДЕНЧЕСКОЙ. Затем, что она краснеет на
    ограничении, добавленном схеме ЗАВТРА на поле, которого команда не называет, —
    даже если сегодняшние значения его случайно удовлетворяют. Поведенческая
    половина (`test_the_seeded_row_satisfies_todays_schema`) ловит нарушение
    СЕГОДНЯШНИХ значений, статическая — умолчание о НОВОМ поле. НИ ОДНА ИЗ ДВУХ НЕ
    ПОКРЫВАЕТ ПРЕДМЕТА ДРУГОЙ, и граница между ними показана отрицательным
    контролём ниже, а не заявлена.
    """
    constrained = constrained_columns()

    # ⚠️ АНТИВАКУУМ ПЕРВЫМ, ДО ПОЛОЖИТЕЛЬНОГО УТВЕРЖДЕНИЯ: на модели без единого
    # ограничения «все поля покрыты» неотличимо от «покрывать нечего».
    assert constrained, (
        "ограничения таблицы расписаний не назвали НИ ОДНОЙ колонки — покрывать "
        "нечего, и зелёный вердикт утверждал бы пустоту"
    )

    uncovered = uncovered_constraint_columns(walkthrough_source())
    assert not uncovered, (
        "команда посева артефакта НЕ НАЗЫВАЕТ поля, названные ограничениями схемы: "
        f"{sorted(uncovered)}. Схема отвергнет построенную строку либо примет её "
        "случайно — и следующий обход упрётся в отказ, как упёрся walkthrough_3"
    )


# --- Отрицательный контроль ----------------------------------------------------
#
# ⚠️ ИМЯ ПОЛЯ И ОЖИДАНИЯ КОНТРОЛЯ ВЫПИСАНЫ ЗДЕСЬ ЛИТЕРАЛАМИ НАМЕРЕННО. Контроль,
# вычисляющий ожидание из проверяемого источника, согласился бы с любой правкой
# этого источника — то есть доказывал бы тождество, а не зубы правила.

CONTROL_KEY = "next_run_at"


def _doctored(text: str, transform) -> str:
    """Копия текста артефакта В ПАМЯТИ с доктóренным вызовом `Schedule(...)`.

    Настоящий файл НЕ ПРАВИТСЯ НИ НА СИМВОЛ: правится разобранное дерево, и
    обратно в текст оно уходит печатью, а не записью на диск.
    """
    program = seed_program(text)
    tree = ast.parse(program)
    calls = [
        call
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == SCHEDULE_CALL_NAME
    ]
    assert len(calls) == 1, (
        f"вызовов {SCHEDULE_CALL_NAME}(...) в программе {len(calls)}, а не один — "
        "доктóрить нечего, и контроль ничего не доказал бы"
    )
    assert any(keyword.arg == CONTROL_KEY for keyword in calls[0].keywords), (
        f"ключа {CONTROL_KEY!r} в настоящем вызове нет — доктóривание доказывало "
        "бы отсутствие того, чего и так нет"
    )

    transform(calls[0])
    doctored_program = ast.unparse(tree)
    assert doctored_program != program, "доктóривание не изменило программы"
    assert text.count(program) == 1, (
        "тело программы встречается в артефакте не один раз — подстановка задела "
        "бы не тот блок"
    )
    return text.replace(program, doctored_program)


def _without_the_key(call: ast.Call) -> None:
    call.keywords = [k for k in call.keywords if k.arg != CONTROL_KEY]


def _with_an_empty_key(call: ast.Call) -> None:
    for keyword in call.keywords:
        if keyword.arg == CONTROL_KEY:
            keyword.value = ast.Constant(None)


async def _refusal_of_todays_schema(session, text: str) -> str | None:
    """Текст отказа базы на строках, построенных данным текстом, либо `None`.

    Сессия откатывается ПЕРЕД посевом: предыдущее доктóривание могло оставить её
    в оборванной транзакции, и второй контроль упал бы отказом ПРИБОРА.
    """
    await session.rollback()
    ad_id, account_id = await seed_stand_owner(session)
    rows = rows_built_by_the_seed_loop(seed_program(text), ad_id, account_id)
    assert rows, "доктóренный цикл не построил ни одной строки — вставлять нечего"
    for row in rows:
        session.add(row)
    try:
        await session.commit()
    except IntegrityError as refusal:
        await session.rollback()
        return str(refusal)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# ГРАНИЦА ПРОСТРАНСТВА ИМЁН: КОНТРОЛЬ-ЗУБ (WR-04)
# ─────────────────────────────────────────────────────────────────────────────

# Источник попытки выхода. `__import__` выбран не случайно: это САМОЕ КОРОТКОЕ
# имя, через которое тело цикла дотягивалось до файловой системы и сети прогона,
# пока словарь встроенных имён подставлялся сам собой.
ESCAPE_SOURCE = "__import__('os')"


def _with_an_escape_attempt(program: str) -> str:
    """Копия ПРОГРАММЫ В ПАМЯТИ, у которой в тело цикла вписан выход наружу.

    Настоящий артефакт не правится ни на символ — правится разобранное дерево,
    и обратно в текст оно уходит печатью. Довод дословно тот же, что у
    `_doctored`.
    """
    tree = ast.parse(program)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
            continue
        builds_schedule = any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == SCHEDULE_CALL_NAME
            for statement in node.body
            for call in ast.walk(statement)
        )
        if not builds_schedule:
            continue
        node.body.insert(0, ast.parse(ESCAPE_SOURCE).body[0])
        ast.fix_missing_locations(tree)
        doctored = ast.unparse(tree)
        assert doctored != program, "доктóривание не изменило программы"
        return doctored
    raise AssertionError(
        f"цикла, строящего {SCHEDULE_CALL_NAME}(...), в программе нет — "
        "доктóрить нечего, и контроль ничего не доказал бы"
    )


def test_control_negative_the_loop_body_cannot_reach_the_interpreter():
    """ЧТО ДОКАЗЫВАЕТ: граница пространства имён ПОСТАВЛЕНА, а не описана.

    ⚠️ ЭТОТ КОНТРОЛЬ ЗАВЕДЁН ПОТОМУ, ЧТО ГРАНИЦА БЫЛА ОПИСАНА ШИРЕ ФАКТА
    (WR-04, ревизия 2026-09-11). Шапка утверждала «выдаются РОВНО ЧЕТЫРЕ имени и
    ничего сверх», а `exec(code, namespace)` при ОТСУТСТВИИ ключа
    `__builtins__` в словаре ПОДСТАВЛЯЕТ настоящий модуль встроенных имён сам:
    тело цикла имело полный доступ к `__import__`, `open`, `eval` — и через них
    ко всей файловой системе прогона. Названная «несущей» граница фактически не
    стояла.

    Красным этот контроль обязан быть ИМЕННО `NameError`: это отказ ПОИСКА
    ИМЕНИ, то есть свидетельство, что словарь встроенных имён заменён, а не
    просто вызов не удался.
    """
    program = _with_an_escape_attempt(seed_program(walkthrough_source()))

    with pytest.raises(NameError):
        rows_built_by_the_seed_loop(program, ad_id=1, account_id=2)


def test_control_positive_the_untouched_loop_still_builds_its_rows():
    """АНТИВАКУУМНАЯ ПОЛОВИНА: сужение не убило самого прибора.

    Без этой половины контроль выше зеленел бы и у пространства имён, в котором
    НЕ РАБОТАЕТ НИЧЕГО, — а тело цикла артефакта читает `range`, и запрет всех
    встроенных имён подряд уронил бы ОСНОВНОЕ правило модуля отказом прибора.
    Перечень разрешённых имён потому и назван, что он НЕ ПУСТ.
    """
    rows = rows_built_by_the_seed_loop(
        seed_program(walkthrough_source()), ad_id=1, account_id=2
    )

    assert rows, "сужение пространства имён лишило цикл возможности строить строки"


@pytest.mark.asyncio
async def test_control_a_seed_program_without_the_next_run_reddens(db_session):
    """ЧТО ДОКАЗЫВАЕТ: обе половины правила имеют зубы, и предметы у них РАЗНЫЕ.

    ⚠️ ДОКТÓРИВАНИЙ ДВА, И ВТОРОЕ НЕ ИЗБЫТОЧНО. Первое изымает ключ момента
    ЦЕЛИКОМ — так выглядела команда до плана 10-48, и краснеть обязаны ОБЕ
    половины. Второе ключ НАЗЫВАЕТ, а значением оставляет пустое: статическая
    половина здесь ЗЕЛЕНА (поле названо), а схема строку всё равно отвергает.
    ЭТО И ЕСТЬ ГРАНИЦА МЕЖДУ «ПОЛЕ НАЗВАНО» И «СТРОКА ЗАКОННА»: без второго
    доктóривания правило приняло бы починку, роняющую следующий обход ровно тем
    же отказом, на котором остановился `walkthrough_3`.
    """
    text = walkthrough_source()

    # Доктóривание (а): ключ изъят целиком → КРАСНЫ ОБЕ ПОЛОВИНЫ.
    without = _doctored(text, _without_the_key)
    assert uncovered_constraint_columns(without) == frozenset({CONTROL_KEY}), (
        "статическая половина НЕ ЗАМЕТИЛА изъятого ключа момента: "
        f"{sorted(uncovered_constraint_columns(without))}"
    )
    refusal = await _refusal_of_todays_schema(db_session, without)
    assert refusal is not None and ACTIVE_REQUIRES_NEXT_RUN_NAME in refusal, (
        "поведенческая половина ПРИНЯЛА строку без момента следующего запуска — "
        f"отказ базы: {refusal!r}"
    )

    # Доктóривание (б): ключ назван, значение пустое → статическая ЗЕЛЕНА,
    # поведенческая КРАСНА.
    empty = _doctored(text, _with_an_empty_key)
    assert uncovered_constraint_columns(empty) == frozenset(), (
        "статическая половина покраснела на НАЗВАННОМ ключе — она судит о "
        "названности поля, а не о законности значения: "
        f"{sorted(uncovered_constraint_columns(empty))}"
    )
    refusal = await _refusal_of_todays_schema(db_session, empty)
    assert refusal is not None and ACTIVE_REQUIRES_NEXT_RUN_NAME in refusal, (
        "поведенческая половина ПРИНЯЛА строку с пустым моментом следующего "
        f"запуска — починка, роняющая обход, прошла бы гейт; отказ базы: {refusal!r}"
    )
