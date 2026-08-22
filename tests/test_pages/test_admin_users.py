"""Подраздел «Пользователи»: выборка, фильтры, страницы и счётчик (ADMIN-04).

⚠️ ГЛАВНОЕ УТВЕРЖДЕНИЕ ФАЙЛА ОДНО, И ОНО ПОВТОРЯЕТСЯ В НЕСКОЛЬКИХ ТЕСТАХ
НАМЕРЕННО: число, напечатанное над списком, равно тому, что в списке лежит
(D-34). Проект уже платил за нарушение этого правила в разделе истории и закрыл
его общим выражением фильтров; повтор дефекта здесь означает, что администратор
видит «найдено 12», листает и не находит человека, за которым пришёл. Поэтому
совпадение проверяется НЕ двумя независимыми вызовами, а сравнением счёта с
содержимым ОДНОЙ и той же выборки при одних и тех же условиях.

⚠️ ВТОРОЕ УТВЕРЖДЕНИЕ — ПРО КИРИЛЛИЦУ, И ОНО НЕ КОСМЕТИЧЕСКОЕ. `LIKE` и
`lower()` в SQLite складывают регистр ТОЛЬКО для латиницы, а PostgreSQL — для
юникода (§Pitfall 6 исследования фазы). Тест на русское имя в разном регистре
поэтому проверяет не «работает ли поиск», а «одинаково ли он работает в суите и
в бою»: без явного приведения обеих сторон он зелен на боевой СУБД и красен на
тестовой, то есть ловит расхождение ровно там, где оно и живёт.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.admin.users_query import (
    ACCESS_CHIPS,
    ACCESS_VALUES,
    STATE_CHIPS,
    STATE_VALUES,
    USERS_PAGE_SIZE,
    apply_user_filters,
    count_users,
    users_page,
)
from app.application.billing.subscription_period import access_is_open
from app.models.subscription import Subscription
from app.models.user import User

NOW = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)


async def _seed_user(
    db_session: AsyncSession,
    *,
    name: str,
    email: str,
    blocked: bool = False,
    subscription: str | None = None,
) -> User:
    """Пользователь с ЯВНО заданным состоянием доступа.

    `subscription` перечисляет ровно те состояния, которые различает ось
    доступа, плюс два, которых она различать не должна:

      None        — строки подписки нет вовсе
      'paid'      — активная строка с живым сроком
      'expired'   — активная строка с мёртвым сроком
      'comped'    — активная строка с признаком бесплатного доступа
      'comped-dead' — льгота поверх МЁРТВОЙ даты (ровно та популяция, у которой
                    число дней отрицательно, D-35)
      'inactive'  — деактивированная строка с живым сроком: доступа не даёт
    """
    user = User(
        email=email,
        password_hash="x",
        name=name,
        is_blocked=blocked,
        created_at=NOW - timedelta(days=30),
    )
    db_session.add(user)
    await db_session.flush()

    if subscription is not None:
        rows = {
            "paid": (NOW + timedelta(days=10), True, False),
            "expired": (NOW - timedelta(days=10), True, False),
            "comped": (NOW + timedelta(days=10), True, True),
            "comped-dead": (NOW - timedelta(days=10), True, True),
            "inactive": (NOW + timedelta(days=10), False, False),
        }
        expires_at, is_active, has_free_access = rows[subscription]
        db_session.add(
            Subscription(
                user_id=user.id,
                expires_at=expires_at,
                is_active=is_active,
                has_free_access=has_free_access,
            )
        )
    await db_session.commit()
    return user


async def _page_and_count(db_session: AsyncSession, **filters) -> tuple[list[User], int]:
    """Страница и счёт ПО ОДНИМ И ТЕМ ЖЕ условиям — форма всех проверок ниже."""
    page = await users_page(db_session, now=NOW, **filters)
    total = await count_users(db_session, now=NOW, **filters)
    return page.users, total


# --- Ось объявлена один раз ---------------------------------------------------


def test_the_closed_sets_are_derived_from_the_chip_declarations():
    """Допустимые значения выводятся ИЗ объявления чипсов, а не выписаны второй раз.

    Второй перечень значений — это ровно тот способ, которым чипс переживает
    снятие своего условия: подпись рисуется, значение принимается, а выражения
    за ним нет. Проверяется обе стороны: множество равно ключам объявления, и
    вариант «все» в него не входит.
    """
    assert ACCESS_VALUES == frozenset(v for v, _ in ACCESS_CHIPS if v)
    assert STATE_VALUES == frozenset(v for v, _ in STATE_CHIPS if v)
    assert "" not in ACCESS_VALUES and "" not in STATE_VALUES
    assert ACCESS_CHIPS[0][0] == "" and STATE_CHIPS[0][0] == ""


def test_every_declared_axis_value_has_an_expression_behind_it():
    """У каждого объявленного значения есть условие; лишних условий нет.

    Чипс без условия отрисовался бы и НИЧЕГО не отбирал — экран при этом
    исправен на вид: 200, подсветка активного значения на месте, список полный.
    """
    for value in ACCESS_VALUES:
        clause = apply_user_filters(select(User), access=value, now=NOW)
        assert str(clause) != str(select(User)), f"ось доступа: {value} ничего не отбирает"
    for value in STATE_VALUES:
        clause = apply_user_filters(select(User), state=value, now=NOW)
        assert str(clause) != str(select(User)), f"ось состояния: {value} ничего не отбирает"


# --- Счётчик и содержимое -----------------------------------------------------


@pytest.mark.asyncio
async def test_count_without_filters_equals_the_whole_table(db_session: AsyncSession):
    """Тест 1: пустые фильтры — счёт равен числу пользователей, страница не длиннее предела."""
    for i in range(3):
        await _seed_user(db_session, name=f"User {i}", email=f"u{i}@test.com")

    users, total = await _page_and_count(db_session)
    everyone = (await db_session.execute(select(func.count(User.id)))).scalar()

    assert total == everyone == 3
    assert len(users) <= USERS_PAGE_SIZE


@pytest.mark.asyncio
async def test_the_search_count_equals_the_search_contents(db_session: AsyncSession):
    """Тест 2: счёт равен найденному, и КАЖДЫЙ элемент страницы условию удовлетворяет.

    Совпадение снимается с ОДНОЙ выборки: два независимых запроса могли бы
    сойтись числом и разойтись содержимым — ровно тот дефект, который D-34
    закрывает.
    """
    await _seed_user(db_session, name="Иван Петров", email="ivan@test.com")
    await _seed_user(db_session, name="Пётр Иванов", email="petr@test.com")
    await _seed_user(db_session, name="Сергей Сидоров", email="sergey@test.com")

    users, total = await _page_and_count(db_session, search="иван")

    assert total == len(users) == 2
    for user in users:
        assert "иван" in user.name.lower() or "иван" in user.email.lower()


@pytest.mark.asyncio
async def test_the_search_folds_cyrillic_case_both_ways(db_session: AsyncSession):
    """Тест 3: кириллица складывается по регистру в ОБЕ стороны на СУБД суиты.

    Ловушка именно здесь: `ilike` и `lower()` SQLite складывают регистр только
    для латиницы. Тест, написанный на «Alice», зелен при любой реализации и не
    отличает поведения суиты от боевого.
    """
    await _seed_user(db_session, name="иван петров", email="lower@test.com")
    await _seed_user(db_session, name="ИВАН СИДОРОВ", email="upper@test.com")

    upper_query, upper_total = await _page_and_count(db_session, search="ИВАН")
    lower_query, lower_total = await _page_and_count(db_session, search="иван")

    assert upper_total == 2, "верхний регистр не нашёл запись в нижнем"
    assert lower_total == 2, "нижний регистр не нашёл запись в верхнем"
    assert {u.email for u in upper_query} == {u.email for u in lower_query}


@pytest.mark.asyncio
async def test_the_search_matches_the_address_like_the_name(db_session: AsyncSession):
    """Тест 4: поиск по адресу работает так же, как по имени."""
    await _seed_user(db_session, name="Первый", email="Needle@Test.Com")
    await _seed_user(db_session, name="Второй", email="other@test.com")

    users, total = await _page_and_count(db_session, search="needle")

    assert total == len(users) == 1
    assert users[0].email == "Needle@Test.Com"


# --- Оси фильтра --------------------------------------------------------------


@pytest.mark.asyncio
async def test_the_access_axis_partitions_everyone(db_session: AsyncSession):
    """Тест 5: открытый, бесплатный и истёкший НЕ пересекаются, а вместе дают всех.

    Разбиение — не украшение: пересечение означало бы, что человек виден под
    двумя взаимоисключающими ярлыками, а недостача — что кто-то не находится ни
    одним фильтром вообще.
    """
    await _seed_user(db_session, name="Платный", email="paid@test.com", subscription="paid")
    await _seed_user(db_session, name="Льготный", email="comped@test.com", subscription="comped")
    await _seed_user(
        db_session, name="Льготный мёртвый", email="dead@test.com", subscription="comped-dead"
    )
    await _seed_user(db_session, name="Истёкший", email="exp@test.com", subscription="expired")
    await _seed_user(db_session, name="Без строки", email="none@test.com")
    await _seed_user(
        db_session, name="Отменённый", email="inactive@test.com", subscription="inactive"
    )

    buckets = {}
    for value in ("open", "comped", "expired"):
        users, total = await _page_and_count(db_session, access=value)
        assert total == len(users), f"счётчик разошёлся с содержимым на оси {value}"
        buckets[value] = {u.email for u in users}

    everyone = {
        e
        for (e,) in (await db_session.execute(select(User.email))).all()
    }
    assert buckets["open"] | buckets["comped"] | buckets["expired"] == everyone
    assert not buckets["open"] & buckets["comped"]
    assert not buckets["open"] & buckets["expired"]
    assert not buckets["comped"] & buckets["expired"]

    assert buckets["comped"] == {"comped@test.com", "dead@test.com"}
    assert buckets["open"] == {"paid@test.com"}
    assert buckets["expired"] == {"exp@test.com", "none@test.com", "inactive@test.com"}


@pytest.mark.asyncio
async def test_the_sql_axis_agrees_with_the_single_python_verdict(db_session: AsyncSession):
    """Отбор в запросе и вердикт в разметке отвечают ОДНО И ТО ЖЕ на каждой строке.

    ⚠️ ЭТОТ ТЕСТ — ЦЕНА ФИЛЬТРАЦИИ В ЗАПРОСЕ, И ОН ОБЯЗАТЕЛЕН. Правило доступа
    объявлено ОДИН раз, в `access_is_open`, и объявлено на Python: модуль срока
    подписки по своей границе ничего не знает про сессию SQLAlchemy. Чтобы
    счётчик и страница считались одним выражением (D-34), ось доступа обязана
    жить в SQL — а значит, рядом с единственным объявлением появляется его
    перевод. Разойтись переводу с оригиналом было бы на чём: достаточно забыть
    про активность строки или про строгость сравнения дат. Здесь оба выражения
    прогоняются по одной и той же популяции, и расхождение падает тестом, а не
    показывает администратору «открыт» у человека, которому продукт отказывает.
    """
    seeded = [
        ("paid@test.com", "paid"),
        ("comped@test.com", "comped"),
        ("dead@test.com", "comped-dead"),
        ("exp@test.com", "expired"),
        ("none@test.com", None),
        ("inactive@test.com", "inactive"),
    ]
    for email, state in seeded:
        await _seed_user(db_session, name=email, email=email, subscription=state)

    subscriptions = {
        row.user_id: row
        for row in (
            await db_session.execute(
                select(Subscription).where(Subscription.is_active.is_(True))
            )
        ).scalars()
    }

    expected: dict[str, set[str]] = {"open": set(), "comped": set(), "expired": set()}
    for user in (await db_session.execute(select(User))).scalars():
        subscription = subscriptions.get(user.id)
        if subscription is not None and subscription.has_free_access:
            expected["comped"].add(user.email)
        elif access_is_open(subscription, NOW):
            expected["open"].add(user.email)
        else:
            expected["expired"].add(user.email)

    for value, emails in expected.items():
        users, _ = await _page_and_count(db_session, access=value)
        assert {u.email for u in users} == emails, f"перевод оси {value} разошёлся с вердиктом"


@pytest.mark.asyncio
async def test_the_state_axis_partitions_everyone(db_session: AsyncSession):
    """Тест 6: заблокированные и активные не пересекаются, а вместе дают всех."""
    await _seed_user(db_session, name="Активный", email="ok@test.com")
    await _seed_user(db_session, name="Заблокированный", email="banned@test.com", blocked=True)

    active, active_total = await _page_and_count(db_session, state="active")
    blocked, blocked_total = await _page_and_count(db_session, state="blocked")

    assert active_total == len(active) == 1
    assert blocked_total == len(blocked) == 1
    assert {u.email for u in active} == {"ok@test.com"}
    assert {u.email for u in blocked} == {"banned@test.com"}


@pytest.mark.asyncio
async def test_both_axes_and_the_search_apply_together(db_session: AsyncSession):
    """Тест 7: две оси и поиск применяются совместно, счётчик по-прежнему равен содержимому."""
    await _seed_user(
        db_session, name="Иван Целевой", email="target@test.com", subscription="comped"
    )
    await _seed_user(
        db_session,
        name="Иван Заблокированный",
        email="ivan-blocked@test.com",
        blocked=True,
        subscription="comped",
    )
    await _seed_user(db_session, name="Иван Платный", email="ivan-paid@test.com", subscription="paid")
    await _seed_user(db_session, name="Пётр Льготный", email="petr@test.com", subscription="comped")

    users, total = await _page_and_count(
        db_session, search="иван", access="comped", state="active"
    )

    assert total == len(users) == 1
    assert users[0].email == "target@test.com"


# --- Страницы -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_the_second_page_shares_nothing_with_the_first(db_session: AsyncSession):
    """Тест 8: вторая страница не повторяет первую, последняя короче предела."""
    for i in range(USERS_PAGE_SIZE + 7):
        await _seed_user(db_session, name=f"User {i:03d}", email=f"u{i:03d}@test.com")

    first = await users_page(db_session, now=NOW, page=1)
    second = await users_page(db_session, now=NOW, page=2)

    assert len(first.users) == USERS_PAGE_SIZE
    assert len(second.users) == 7
    assert not {u.id for u in first.users} & {u.id for u in second.users}
    assert first.total == second.total == USERS_PAGE_SIZE + 7
    assert first.pages == second.pages == 2


@pytest.mark.asyncio
async def test_a_page_number_outside_the_range_does_not_break_the_query(
    db_session: AsyncSession,
):
    """Тест 10: номер страницы из адреса зажимается, а не роняет выборку.

    Номер приезжает строкой запроса, то есть из ссылки, закладки или чужого
    сообщения. Отказ страницы был бы отказом в обслуживании по подконтрольному
    отправителю значению (T-06-USR3).
    """
    for i in range(3):
        await _seed_user(db_session, name=f"User {i}", email=f"u{i}@test.com")

    beyond = await users_page(db_session, now=NOW, page=999)
    before = await users_page(db_session, now=NOW, page=-5)

    assert beyond.page == beyond.pages == 1
    assert before.page == 1
    assert len(beyond.users) == len(before.users) == 3


@pytest.mark.asyncio
async def test_an_empty_result_still_has_one_page(db_session: AsyncSession):
    """Пустая выдача — это ОДНА пустая страница, а не ноль страниц.

    Ноль страниц заставил бы разметку делить на ноль при подписи «страница X из
    Y» и печатать «страница 1 из 0» — подпись, которой не соответствует ни одно
    состояние.
    """
    page = await users_page(db_session, now=NOW, search="никого-нет")

    assert page.total == 0
    assert page.users == []
    assert page.page == page.pages == 1


# --- Санация ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_an_unknown_axis_value_means_all_and_never_reaches_the_expression(
    db_session: AsyncSession,
):
    """Тест 9: мусорное значение оси трактуется как «все» и в запрос не попадает сырым."""
    await _seed_user(db_session, name="Платный", email="paid@test.com", subscription="paid")
    await _seed_user(db_session, name="Истёкший", email="exp@test.com", subscription="expired")

    garbage = "'; DROP TABLE users; --"
    users, total = await _page_and_count(db_session, access=garbage, state=garbage)

    assert total == len(users) == 2, "мусорное значение сузило выдачу"

    compiled = str(
        apply_user_filters(select(User), access=garbage, state=garbage, now=NOW).compile(
            compile_kwargs={"literal_binds": True}
        )
    )
    assert "DROP TABLE" not in compiled


@pytest.mark.asyncio
async def test_a_blank_search_is_not_a_filter(db_session: AsyncSession):
    """Пробельный поиск — это ОТСУТСТВИЕ поиска, а не поиск по пробелу.

    Иначе случайно отправленная форма с пробелом в поле давала бы пустой
    список при полной таблице — и объяснения этому на экране не было бы.
    """
    await _seed_user(db_session, name="Первый", email="a@test.com")

    users, total = await _page_and_count(db_session, search="   ")

    assert total == len(users) == 1


# --- Число обращений к базе ---------------------------------------------------


@pytest.mark.asyncio
async def test_the_number_of_queries_does_not_grow_with_the_rows(db_session: AsyncSession):
    """Тест 11: число обращений к базе не зависит от числа строк страницы.

    Прежний список ходил в базу за каждым пользователем; проверка сравнивает
    два прогона разного размера, а не сверяет с магическим числом — константа
    в утверждении устарела бы при первом же законном изменении формы запроса.
    """
    for i in range(3):
        await _seed_user(db_session, name=f"User {i}", email=f"u{i}@test.com")
    with patch.object(db_session, "execute", wraps=db_session.execute) as small:
        await users_page(db_session, now=NOW)
    small_calls = small.call_count

    for i in range(3, 30):
        await _seed_user(db_session, name=f"User {i}", email=f"u{i}@test.com")
    with patch.object(db_session, "execute", wraps=db_session.execute) as big:
        page = await users_page(db_session, now=NOW)

    assert len(page.users) == 30
    assert big.call_count == small_calls
