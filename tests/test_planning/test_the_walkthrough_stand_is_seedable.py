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
С АРТЕФАКТОМ, А НЕ ПОДРОБНОСТЬ РЕАЛИЗАЦИИ. Выдаются РОВНО ЧЕТЫРЕ имени и ничего сверх:

    Schedule              — настоящий класс модели `app.models.schedule`
    compute_next_run_at   — настоящий вычислитель `app.services.schedule_service`
    ad, acc               — носители идентификаторов посеянных объявления и аккаунта
    s                     — накопитель с методом `add`

Всякое имя, которое тело цикла читает и которого в этом перечне нет, обязано
ВЫЧИСЛЯТЬСЯ ВНУТРИ САМОГО ТЕЛА. Имя, вычисленное программой артефакта ВЫШЕ цикла, при
исполнении одного узла не существует, и правило упало бы отказом о НЕИЗВЕСТНОМ ИМЕНИ —
то есть отказом ПРИБОРА, выданным за отказ предмета.

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

from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
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

    ⚠️ ИСПОЛНЯЕТСЯ РОВНО УЗЕЛ ЦИКЛА и выдаётся РОВНО пространство имён, перечисленное
    в шапке модуля. Границу держит не комментарий, а сама сборка: в скомпилированный
    модуль кладётся ОДИН узел.
    """
    loop, _ = seed_schedule_loop(program)

    built: list[Schedule] = []

    class _Sink:
        """Накопитель под именем `s`: у сессии артефакта берётся ОДИН метод."""

        def add(self, row: Schedule) -> None:
            built.append(row)

    namespace = {
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
