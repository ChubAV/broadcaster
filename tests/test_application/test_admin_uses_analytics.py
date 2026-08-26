"""«Обзор» ЗОВЁТ модуль аналитики — и это утверждение машинное, а не устное.

ПРЕДМЕТ. Фаза 4 объявила модуль аналитики ЕДИНСТВЕННЫМ местом агрегаций над
журналом отправок (D-35), и не ради красоты слоёв: до этого модуля один и тот
же вопрос — «сколько отправок и чем они кончились» — задавали четыре разных
места четырьмя разными запросами, и ответы уже разошлись. Расхождение такого
рода не роняет ни один тест и не даёт пятисотки: оно просто печатает два разных
числа на один вопрос, и первым его замечает не разработчик, а человек, который
по этим числам принимает решение.

Фаза 6 добавляет ПЯТОЕ место — админский «Обзор». Путь наименьшего
сопротивления ведёт к тому, чтобы посчитать отправки прямо в страничном модуле
админки: там уже есть и сессия, и `select`, и три соседних счётчика. Ровно так
и появилась бы вторая агрегация — а с ней и день, когда администратор и
пользователь смотрят на РАЗНЫЕ числа об одном и том же периоде и оба считают
своё верным.

ПОЧЕМУ РАЗБОР ДЕРЕВА, А НЕ ПОИСК СТРОКИ. Поиск подстроки считает вхождение и в
комментарии, и в докстринге — то есть объяснение, ПОЧЕМУ агрегации здесь нет,
роняло бы тест, утверждающий, что её нет. И наоборот: агрегация, записанная
через локальный псевдоним, поиск строки прошла бы насквозь. Поэтому запрет
проверяется обходом синтаксического дерева страничного модуля.

ЧЕГО ЭТОТ ФАЙЛ НЕ ДОКАЗЫВАЕТ. Он не утверждает, что «Обзор» печатает числа
правильно — это предмет `tests/test_pages/test_admin_panel.py`. Он утверждает
ровно две вещи: общесистемный счёт живёт в модуле аналитики и считает верно, а
страничный модуль админки своих агрегаций не строит.
"""

from datetime import datetime, timedelta, timezone

import ast
from pathlib import Path

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import (
    STATUS_ACCOUNT_DISCONNECTED,
    STATUS_FAIL,
    STATUS_OK,
    SendMetrics,
    send_metrics,
    sliding_window_bounds,
)
from app.models.send_log import SendLog
from app.models.user import User

ADMIN_PAGES_SOURCE = Path("app/pages/admin.py")

# Обработчик подраздела «Обзор». Имя закреплено УТВЕРЖДЕНИЕМ, а не
# подразумевается: переименованный обработчик вынес бы утверждения ниже в
# пустоту, и файл продолжал бы зеленеть, не проверяя ничего.
OVERVIEW_HANDLER = "admin_dashboard"

# Имя общесистемного счёта модуля аналитики — то, которое «Обзор» обязан звать.
ANALYTICS_ENTRY = "send_metrics"

NOW = datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)


async def _user(db: AsyncSession, email: str) -> User:
    user = User(email=email, password_hash="x", name="U", timezone="UTC")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _seed(
    db: AsyncSession,
    user_id: int,
    *,
    sent_at: datetime,
    status: str = STATUS_OK,
    group_id: int | None = None,
) -> None:
    """Запись журнала с ЯВНЫМ временем отправки.

    У колонки есть `server_default=func.now()`, и запись без явного времени
    попала бы в текущее окно всегда — независимо от того, что проверяет тест.
    """
    db.add(
        SendLog(
            user_id=user_id,
            group_id=group_id,
            ad_title="Объявление",
            ad_text="Текст",
            ad_images=[],
            group_name="Группа",
            messenger_type="wa",
            task_id="task-1",
            status=status,
            sent_at=sent_at,
        )
    )
    await db.commit()


def _admin_tree() -> ast.Module:
    return ast.parse(ADMIN_PAGES_SOURCE.read_text(encoding="utf-8"))


def _handler(tree: ast.Module, name: str) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(
        f"обработчик {name} не найден в {ADMIN_PAGES_SOURCE}: "
        "утверждения этого файла адресовать нечему"
    )


def _called_names(node: ast.AST) -> set[str]:
    """Имена всех вызовов внутри узла — и `имя(...)`, и `объект.имя(...)`."""
    return {
        child.func.id if isinstance(child.func, ast.Name) else child.func.attr
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, (ast.Name, ast.Attribute))
    }


# ---- Общесистемный счёт живёт В МОДУЛЕ АНАЛИТИКИ ----


@pytest.mark.asyncio
async def test_the_systemwide_count_sums_every_user(db_session: AsyncSession):
    """Счёт БЕЗ владельца возвращает сумму по всем пользователям."""
    first = await _user(db_session, "one@test.com")
    second = await _user(db_session, "two@test.com")
    third = await _user(db_session, "three@test.com")

    await _seed(db_session, first.id, sent_at=NOW - timedelta(hours=1))
    await _seed(db_session, second.id, sent_at=NOW - timedelta(hours=2))
    await _seed(
        db_session, third.id, sent_at=NOW - timedelta(hours=3), status=STATUS_FAIL
    )

    system = await send_metrics(
        db_session, user_id=None, bounds=sliding_window_bounds(now=NOW)
    )

    assert system.total == 3
    assert system.ok == 2
    assert system.failed == 1


@pytest.mark.asyncio
async def test_the_single_user_contract_is_unchanged_by_the_generalisation(
    db_session: AsyncSession,
):
    """ИНВАРИАНТ: счёт С владельцем отдаёт ровно то же, что до обобщения.

    Сводку на одного пользователя читают дашборд и раздел истории. Обобщение
    модуля не имеет права поменять НИ ОДНОГО их числа — иначе цена расширения
    админки была бы уплачена поведением пользовательских экранов, и заметил бы
    это пользователь, а не суита. Утверждение адресуется ВСЕМ восьми полям, а
    не одному: разъехаться могло бы любое.
    """
    owner = await _user(db_session, "owner@test.com")
    stranger = await _user(db_session, "stranger@test.com")

    await _seed(db_session, owner.id, sent_at=NOW - timedelta(hours=1), group_id=None)
    await _seed(
        db_session,
        owner.id,
        sent_at=NOW - timedelta(hours=2),
        status=STATUS_ACCOUNT_DISCONNECTED,
    )
    await _seed(db_session, owner.id, sent_at=NOW - timedelta(hours=30))
    # Чужие записи — в обоих окнах: они обязаны не попасть ни в одно поле.
    await _seed(db_session, stranger.id, sent_at=NOW - timedelta(hours=1))
    await _seed(db_session, stranger.id, sent_at=NOW - timedelta(hours=30))

    mine = await send_metrics(
        db_session, user_id=owner.id, bounds=sliding_window_bounds(now=NOW)
    )

    expected = SendMetrics(
        total=2,
        ok=1,
        failed=1,
        groups=0,
        total_prev=1,
        ok_prev=1,
        failed_prev=0,
        groups_prev=0,
    )
    assert mine == expected


@pytest.mark.asyncio
async def test_the_systemwide_count_keeps_the_single_round_trip(
    db_session: AsyncSession,
):
    """Одно обращение к базе, и предыдущее окно приезжает тем же обращением.

    Второй запрос ради предыдущего окна удвоил бы обращения к самой растущей
    таблице системы ради одной строки результата — и сделал бы это на пути
    рендера страницы, которую открывают В МОМЕНТ АВАРИИ.
    """
    user = await _user(db_session, "single@test.com")
    await _seed(db_session, user.id, sent_at=NOW - timedelta(hours=1))
    await _seed(db_session, user.id, sent_at=NOW - timedelta(hours=30))

    statements: list[str] = []

    def _record(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    engine = db_session.bind.sync_engine
    event.listen(engine, "before_cursor_execute", _record)
    try:
        system = await send_metrics(
            db_session, user_id=None, bounds=sliding_window_bounds(now=NOW)
        )
    finally:
        event.remove(engine, "before_cursor_execute", _record)

    assert len(statements) == 1, statements
    assert system.total == 1
    assert system.total_prev == 1


@pytest.mark.asyncio
async def test_the_previous_window_covers_the_same_users_as_the_current_one(
    db_session: AsyncSession,
):
    """Дельта считается по ТОМУ ЖЕ множеству пользователей, что и текущее окно.

    Расхождение множеств дало бы дельту, сравнивающую разные совокупности, —
    то есть число, которое выглядит измеренным и не значит ничего.
    """
    first = await _user(db_session, "prev-one@test.com")
    second = await _user(db_session, "prev-two@test.com")

    await _seed(db_session, first.id, sent_at=NOW - timedelta(hours=1))
    await _seed(db_session, second.id, sent_at=NOW - timedelta(hours=2))
    await _seed(db_session, first.id, sent_at=NOW - timedelta(hours=30))
    await _seed(db_session, second.id, sent_at=NOW - timedelta(hours=40))

    system = await send_metrics(
        db_session, user_id=None, bounds=sliding_window_bounds(now=NOW)
    )

    assert system.total == 2
    assert system.total_prev == 2
    assert system.total_delta == 0


@pytest.mark.asyncio
async def test_an_empty_journal_gives_zeroes_and_not_an_exception(
    db_session: AsyncSession,
):
    """Пустая база даёт нули, а не пустые значения и не исключение.

    `func.sum` над пустым набором отдаёт NULL, и плитка, получившая его,
    напечатала бы пустоту там, где верный ответ — ноль.
    """
    system = await send_metrics(
        db_session, user_id=None, bounds=sliding_window_bounds(now=NOW)
    )

    assert system == SendMetrics()
    assert system.total == 0
    assert system.failed_delta == 0


def test_the_owner_of_a_summary_cannot_be_omitted_by_accident():
    """У области счёта НЕТ умолчания, и это форма T-04-01 после обобщения.

    До фазы 6 изоляция по владельцу держалась на том, что ветки «все
    пользователи» в модуле не было вовсе. Ветка появилась (D-39), и держать
    изоляцию теперь может ровно одно: параметр обязателен. С умолчанием `None`
    вызов, у которого владельца просто забыли передать, вернул бы чужие числа
    и напечатал бы их на СОБСТВЕННОМ дашборде пользователя — без исключения,
    без пятисотки и без единого красного теста. Разница между молчаливой
    общесистемной выдачей и явной — ровно отсутствие умолчания.
    """
    import inspect

    parameter = inspect.signature(send_metrics).parameters["user_id"]

    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, (
        "область счёта обязана приезжать ИМЕНЕМ: позиционный аргумент подставился "
        "бы соседним значением молча"
    )
    assert parameter.default is inspect.Parameter.empty, (
        "у области счёта появилось умолчание: общесистемная выдача стала "
        "достижимой по забывчивости, а не по решению (T-04-01)"
    )


# ---- Машинный свидетель: страничный модуль админки агрегаций не строит ----


def test_the_admin_pages_module_builds_no_aggregate_over_the_send_journal():
    """Разбор ДЕРЕВА: в страничном модуле админки нет своих агрегатов.

    Утверждение сильнее, чем «нет второго счёта отправок»: страничный модуль не
    строит агрегирующих выражений ВООБЩЕ. Так проверяемое свойство перестаёт
    зависеть от того, угадал ли автор теста имя следующей агрегируемой
    величины, — а следующий план, которому понадобится счёт, обязан завести его
    там, где такие выражения и живут: в прикладном слое.
    """
    tree = _admin_tree()

    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported += [alias.name for alias in node.names]
    assert "func" not in imported, (
        "страничный модуль админки импортирует конструктор SQL-функций: "
        f"агрегат в нём стал возможен снова ({imported})"
    )

    aggregates = [
        child.value.attr
        for child in ast.walk(tree)
        if isinstance(child, ast.Attribute)
        and isinstance(child.value, ast.Attribute)
        and isinstance(child.value.value, ast.Name)
        and child.value.value.id == "func"
    ]
    calls = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "func"
    ]
    assert not aggregates and not calls, (
        "агрегирующее выражение в страничном модуле админки: "
        f"{aggregates + calls}"
    )


def test_the_overview_handler_calls_the_analytics_module():
    """Обработчик «Обзора» ЗОВЁТ общесистемный счёт модуля аналитики.

    Отрицательного утверждения выше недостаточно: модуль админки мог бы не
    строить агрегатов просто оттого, что чисел не показывает вовсе. Это
    утверждение говорит, откуда «Обзор» берёт своё число, — и краснеет в тот
    день, когда вызов из обработчика уходит.
    """
    handler = _handler(_admin_tree(), OVERVIEW_HANDLER)

    assert ANALYTICS_ENTRY in _called_names(handler), (
        f"обработчик {OVERVIEW_HANDLER} не зовёт {ANALYTICS_ENTRY}: "
        "число ошибок «Обзора» взялось откуда-то ещё"
    )
