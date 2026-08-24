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
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import AsyncClient
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
from app.models.messenger_account import MessengerAccount
from app.models.subscription import Subscription
from app.models.user import User

# ⚠️ МОМЕНТ БЕРЁТСЯ НАСТОЯЩИЙ, А НЕ ЗАФИКСИРОВАННЫЙ ДАТОЙ В ИСХОДНИКЕ. Половина
# файла проверяет модуль, которому момент передаётся параметром, — ему всё равно.
# Вторая половина ходит через маршрут, а маршрут снимает момент сам, и
# зафиксированная в прошлом дата сделала бы «живую» подписку просроченной ровно
# тогда, когда до неё дойдёт календарь: тест позеленел бы навсегда на ветке
# «истёк» и перестал бы проверять ту, ради которой написан. Все сроки ниже
# заданы СМЕЩЕНИЯМИ от этого момента.
NOW = datetime.now(timezone.utc)


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
        # Хеш ЗАМЕТНЫЙ и разный у каждого: односимвольная заглушка нашлась бы в
        # любой разметке по построению, и утверждение «хеша на экране нет»
        # проверяло бы наличие буквы, а не отсутствие секрета.
        password_hash=f"ХЕШ-ПАРОЛЯ-{email}-НЕ-ДОЛЖЕН-ПОПАСТЬ-В-РАЗМЕТКУ",
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


# =============================================================================
# Подраздел: разметка, чипсы, страницы, счётчик
# =============================================================================
#
# ⚠️ ЭТА ПОЛОВИНА ФАЙЛА ХОДИТ ЧЕРЕЗ МАРШРУТ, А НЕ ЗОВЁТ МОДУЛЬ. Утверждения
# верхней половины про выборку остаются верными и при подразделе, который
# показывает НЕ ТО, что выбрал: между выборкой и экраном лежат санация значений,
# сборка контекста и разметка, и каждый из трёх шагов способен разойтись с
# остальными молча.

USERS_URL = "/admin/users"
ROW_TEMPLATE = Path("app/templates/admin/includes/user_row.html")
LIST_TEMPLATE = Path("app/templates/admin/users.html")
ADMIN_PAGES_SOURCE = Path("app/pages/admin.py")


def _chipset(html: str, axis: str) -> str:
    """Разметка ОДНОЙ группы чипсов. Группы проверяются порознь намеренно.

    Общий счёт отмеченных чипсов по всей полосе сошёлся бы и у экрана, где одна
    ось отмечена дважды, а вторая не отмечена вовсе.
    """
    match = re.search(rf'data-chipset="{axis}">(.*?)</div>', html, re.S)
    assert match, f"группа чипсов «{axis}» не отрисована"
    return match.group(1)


def _counters(html: str) -> list[tuple[str, str]]:
    """Все пары «N из M», напечатанные на экране."""
    return re.findall(r"(\d+) из (\d+)", html)


@pytest.mark.asyncio
async def test_the_subsection_answers_the_admin_and_refuses_everyone_else(
    authed_client: AsyncClient, admin_client: AsyncClient
):
    """Тест 1: 200 администратору, 403 постороннему.

    Отказ снимается и по коду, и по телу: отказ, отданный со страницей админки
    внутри, отказом не является.
    """
    assert (await admin_client.get(USERS_URL)).status_code == 200

    # authed_client и admin_client — ОДИН клиент с разными cookie; порядок
    # фикстур делает последним вход администратора, поэтому вход обычного
    # пользователя повторяется здесь явно.
    await authed_client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )
    refused = await authed_client.get(USERS_URL, follow_redirects=False)
    assert refused.status_code == 403
    assert "data-rowhead" not in refused.text


@pytest.mark.asyncio
async def test_the_counter_over_the_list_equals_the_list(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 2: «N из M» над списком совпадает с выборкой, и оба числа — одно выражение.

    Печатаются ДВА счётчика — над списком и в панели страниц, — и они обязаны
    совпадать посимвольно: два числа об одном и том же, собранные порознь,
    расходятся сперва на границе страницы, а потом везде.
    """
    for i in range(3):
        await _seed_user(db_session, name=f"Пользователь {i}", email=f"u{i}@test.com")

    html = (await admin_client.get(USERS_URL)).text
    counters = _counters(html)

    assert counters, "счётчика «N из M» на экране нет"
    assert len(set(counters)) == 1, f"счётчики разошлись: {counters}"
    shown, total = counters[0]
    # Администратор тоже пользователь и тоже попадает в список.
    assert int(total) == 4
    assert int(shown) == int(total)
    assert html.count("data-user-row") == int(shown)


@pytest.mark.asyncio
async def test_two_chip_groups_come_from_the_library_with_the_subsection_path(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 3: две группы чипсов, базовый адрес подраздела, ровно один отмеченный.

    ⚠️ БАЗОВЫЙ АДРЕС ПРОВЕРЯЕТСЯ У КАЖДОЙ ССЫЛКИ. Чипс с чужим адресом уводит
    администратора из подраздела при КАЖДОМ клике — при статусе 200 и верной на
    вид разметке; заметить это можно только по адресной строке ПОСЛЕ перехода.
    """
    html = (await admin_client.get(f"{USERS_URL}?access=comped&state=blocked")).text

    for axis in ("access", "state"):
        group = _chipset(html, axis)
        assert group.count("chip--on") == 1, f"в группе «{axis}» отмечен не один чипс"
        hrefs = re.findall(r'href="([^"]*)"', group)
        assert hrefs, f"в группе «{axis}» нет ссылок"
        for href in hrefs:
            assert href.startswith(USERS_URL), f"чипс уводит из подраздела: {href}"

    # Групп ровно две (D-32) — не три, как в «Логах», и не одна.
    assert len(re.findall(r"data-chipset=", html)) == 2


@pytest.mark.asyncio
async def test_switching_one_axis_keeps_the_other_and_drops_the_page(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 4: смена оси сохраняет вторую ось и поиск, но НЕ номер страницы.

    Сохранённый номер страницы после смены фильтра — это пустой экран при
    непустой выдаче: страницы пересчитались, а адрес всё ещё указывает на
    седьмую.
    """
    html = (
        await admin_client.get(f"{USERS_URL}?q=иван&access=comped&state=active&page=2")
    ).text

    for href in re.findall(r'href="([^"]*)"', _chipset(html, "state")):
        assert "access=comped" in href, f"смена состояния потеряла ось доступа: {href}"
        assert "q=" in href, f"смена состояния потеряла поиск: {href}"
        assert "page=" not in href, f"смена состояния сохранила номер страницы: {href}"

    for href in re.findall(r'href="([^"]*)"', _chipset(html, "access")):
        assert "state=active" in href, f"смена доступа потеряла ось состояния: {href}"
        assert "page=" not in href


@pytest.mark.asyncio
async def test_an_empty_filtered_result_is_not_an_empty_product(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 5: пустая выдача ФИЛЬТРОВ отличима от пустого состояния «пользователей нет».

    Слитые в одно, они отвечают «пользователей нет» на экран, где пользователи
    есть, — и администратор пойдёт искать поломку регистрации вместо того, чтобы
    снять свой же фильтр.
    """
    filtered = (await admin_client.get(f"{USERS_URL}?q=такого-точно-нет")).text

    assert "Пользователи не найдены" in filtered
    assert "Уточните запрос или снимите фильтры." in filtered
    # Выход из пустого состояния назван: предлагать снять фильтры и не давать
    # чем — это тупик с объяснением.
    assert f'href="{USERS_URL}"' in filtered


@pytest.mark.asyncio
async def test_the_row_prints_the_five_declared_columns(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 6: имя, адрес, доступ, состояние, число аккаунтов и дата регистрации."""
    user = await _seed_user(
        db_session, name="Иван Петров", email="ivan@test.com", subscription="paid"
    )
    db_session.add(
        MessengerAccount(user_id=user.id, type="wa", credentials="{}", status="active")
    )
    await db_session.commit()

    html = (await admin_client.get(f"{USERS_URL}?q=ivan@test.com")).text

    assert "Иван Петров" in html
    assert "ivan@test.com" in html
    assert f'href="/admin/users/{user.id}"' in html
    assert "открыт" in html
    assert (NOW - timedelta(days=30)).strftime("%d.%m.%Y") in html
    # Подписи колонок и подписи ячеек берутся из ОДНОГО списка (M2 UI-контракта).
    for column in ("Пользователь", "Доступ", "Состояние", "Аккаунтов", "Регистрация"):
        assert column in html, column


@pytest.mark.asyncio
async def test_a_comped_user_gets_no_number_of_days(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 7: у льготного число дней НЕ печатается — печатается признак бессрочности.

    ⚠️ ЭТО НЕ ОФОРМЛЕНИЕ (D-35). У пользователя с выданным бесплатным доступом
    дата окончания МЁРТВАЯ, и число дней получается отрицательным — сам
    `_access_view` об этом предупреждает. Напечатанное, оно прочиталось бы как
    «доступ кончился» у человека, чей доступ открыт бессрочно.
    """
    await _seed_user(
        db_session, name="Льготный", email="comped@test.com", subscription="comped-dead"
    )

    html = (await admin_client.get(f"{USERS_URL}?q=comped@test.com")).text

    assert "бесплатный" in html
    assert "бессрочно" in html
    assert "Осталось полных суток" not in html, "у льготного напечатано число дней"
    assert not re.search(r"-\d+\s*(дн|сут)", html), "на экране отрицательное число дней"


@pytest.mark.asyncio
async def test_an_expired_user_gets_a_date_and_not_a_negative_number(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 8: у истёкшего печатается дата окончания, а не отрицательное число дней."""
    await _seed_user(db_session, name="Истёкший", email="exp@test.com", subscription="expired")

    html = (await admin_client.get(f"{USERS_URL}?q=exp@test.com")).text

    assert "закрыт" in html
    assert (NOW - timedelta(days=10)).strftime("%d.%m.%Y") in html
    assert "Осталось полных суток" not in html
    assert not re.search(r"-\d+\s*(дн|сут)", html)


@pytest.mark.asyncio
async def test_no_consumption_or_quota_survived_the_reverse_layout(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 9 (отрицательный): величин потребления и квоты в подразделе нет.

    Макет рисует шкалу «использовано / квота». После смены модели тарификации
    такой величины НЕ СУЩЕСТВУЕТ, и перенос шкалы нарисовал бы предмет, которого
    нет: администратор принял бы по ней решение, а числа под ней ничего не
    значат.
    """
    await _seed_user(db_session, name="Кто-то", email="someone@test.com", subscription="paid")
    html = (await admin_client.get(USERS_URL)).text

    sources = (
        html
        + LIST_TEMPLATE.read_text(encoding="utf-8")
        + ROW_TEMPLATE.read_text(encoding="utf-8")
    )
    for marker in ("Использовано", "квота", "Квота", "usagePct", "лимит сообщений"):
        assert marker not in sources, marker


@pytest.mark.asyncio
async def test_no_manual_extension_of_access_exists(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 10 (отрицательный): ручного продления доступа нет ни в разметке, ни в маршрутах.

    Право открыть доступ бесплатно уже есть и покрыто. Третий способ управлять
    сроком рядом с оплатой и льготой немедленно поднял бы вопросы, на которые
    фаза не отвечает: попадает ли он в MRR, что с ним при последующей оплате
    (D-36). Отсутствие закрепляется тестом, потому что «мы решили не делать»
    возвращается первой же правкой, которая выглядит удобной.
    """
    sources = (
        (await admin_client.get(USERS_URL)).text
        + LIST_TEMPLATE.read_text(encoding="utf-8")
        + ROW_TEMPLATE.read_text(encoding="utf-8")
        + ADMIN_PAGES_SOURCE.read_text(encoding="utf-8")
    )
    # Литералы взяты у макета дословно: он рисует на развороте строки две
    # пунктирные кнопки, «+1000 ОТПРАВОК» и «+30 ДНЕЙ», — обе управляют
    # величинами, которых фаза не заводит.
    for marker in ("продлить", "Продлить", "extend_access", "+30 ДНЕЙ", "+1000 ОТПРАВОК"):
        assert marker not in sources, marker


@pytest.mark.asyncio
async def test_the_row_leads_to_the_card_and_does_not_unfold_in_place(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 11: строка ведёт в карточку; разворота строки на месте нет (D-03).

    Макетный разворот несёт доступ, действия и историю — 11 КБ разметки; на
    375px такой разворот нечитаем, и прецедент отдельной страницы детали в
    проекте прямой.
    """
    user = await _seed_user(db_session, name="Иван", email="ivan@test.com")

    html = (await admin_client.get(f"{USERS_URL}?q=ivan@test.com")).text
    assert f'href="/admin/users/{user.id}"' in html

    row_source = ROW_TEMPLATE.read_text(encoding="utf-8")
    for marker in ("adminOpenUser", "x-show", "x-data", "toggleOpen"):
        assert marker not in row_source, marker


@pytest.mark.asyncio
async def test_the_card_still_reaches_the_user_history(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Тест 12: вход из карточки в историю отправок жив и отвечает 200 (D-04).

    Экран отгружен требованием ADMIN-02 и уже переверстан Фазой 1. Переписывание
    подраздела списка не имеет права его отрезать — а отрезанный, он остаётся
    рабочим маршрутом, до которого просто нельзя дойти руками.
    """
    user = await _seed_user(db_session, name="Иван", email="ivan@test.com")

    card = await admin_client.get(f"/admin/users/{user.id}")
    assert card.status_code == 200
    assert f"/admin/users/{user.id}/history" in card.text

    history = await admin_client.get(f"/admin/users/{user.id}/history")
    assert history.status_code == 200


# --- Страницы в разметке ------------------------------------------------------


@pytest.mark.asyncio
async def test_the_pager_uses_the_shipped_primitive(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Панель страниц собрана на уже отгруженном `[data-pager]`, а не на своих классах.

    Примитив объявлен в `app.css` и до этого плана не имел ни одного
    потребителя; новых классов подраздел не заводит — utility-классы по проекту
    запрещены и проверяются сплошным обходом всех шаблонов.
    """
    html = (await admin_client.get(USERS_URL)).text

    assert "data-pager" in html
    assert "data-pager-actions" in html
    assert 'class="pager' not in html and "users-pager" not in html


@pytest.mark.asyncio
async def test_the_edge_pages_disable_the_button_instead_of_hiding_it(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """На краю списка кнопка ОТКЛЮЧЕНА, а не убрана.

    Исчезающая кнопка сдвигает соседнюю под курсор: администратор, листавший
    вперёд, на последней странице попадает нажатием в «назад».
    """
    one_page = (await admin_client.get(USERS_URL)).text
    assert one_page.count("disabled") >= 2, "на единственной странице обе кнопки живые"

    for i in range(USERS_PAGE_SIZE + 2):
        await _seed_user(db_session, name=f"User {i:03d}", email=f"u{i:03d}@test.com")

    first = (await admin_client.get(USERS_URL)).text
    last = (await admin_client.get(f"{USERS_URL}?page=2")).text

    assert "page=2" in first, "с первой страницы нет перехода вперёд"
    assert "page=1" in last, "с последней страницы нет перехода назад"


@pytest.mark.asyncio
async def test_the_page_number_from_the_address_never_breaks_the_subsection(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Мусорный или запредельный номер страницы отдаёт крайнюю страницу, а не отказ.

    Номер приезжает из ссылки, закладки или чужого сообщения (T-06-USR3). Отказ
    был бы отказом в обслуживании по подконтрольному отправителю значению.
    """
    await _seed_user(db_session, name="Кто-то", email="someone@test.com")

    for suffix in ("?page=99999", "?page=-3", "?page=абв", "?page=", "?page=1e9"):
        response = await admin_client.get(f"{USERS_URL}{suffix}")
        assert response.status_code == 200, suffix
        assert "data-user-row" in response.text, suffix


@pytest.mark.asyncio
async def test_the_subsection_does_not_query_per_row(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Число обращений к базе не растёт с числом строк — включая подписки и аккаунты.

    Прежний список ходил в базу за каждым пользователем. Сравниваются два
    прогона разного размера, а не сверка с магическим числом: константа в
    утверждении устарела бы при первом же законном изменении формы страницы.
    """
    for i in range(2):
        await _seed_user(db_session, name=f"User {i:03d}", email=f"u{i:03d}@test.com")
    with patch.object(db_session, "execute", wraps=db_session.execute) as small:
        await admin_client.get(USERS_URL)
    small_calls = small.call_count

    for i in range(2, 25):
        await _seed_user(db_session, name=f"User {i:03d}", email=f"u{i:03d}@test.com")
    with patch.object(db_session, "execute", wraps=db_session.execute) as big:
        html = (await admin_client.get(USERS_URL)).text

    assert html.count("data-user-row") == 26
    assert big.call_count == small_calls


@pytest.mark.asyncio
async def test_no_credentials_of_messenger_accounts_reach_the_markup(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """T-06-USR1: учётных данных и данных сессий в разметке подраздела нет.

    Они не нужны ни для одной операции поддержки, а один раз попав в разметку,
    уезжают в историю браузера, в скриншот и в тикет.
    """
    user = await _seed_user(db_session, name="Иван", email="ivan@test.com")
    db_session.add(
        MessengerAccount(
            user_id=user.id,
            type="wa",
            credentials='{"session": "СЕКРЕТНАЯ-СТРОКА-СЕССИИ"}',
            status="active",
        )
    )
    await db_session.commit()

    html = (await admin_client.get(USERS_URL)).text

    assert "СЕКРЕТНАЯ-СТРОКА-СЕССИИ" not in html
    assert "credentials" not in html
    assert "password_hash" not in html
    assert user.password_hash not in html


def test_the_unlimited_select_left_the_repository():
    """Выборки без предела в репозитории пользователей не осталось (D-33, T-06-USR2).

    Метод, оставленный «на всякий случай», — это приглашение вернуть страницу к
    полной таблице одной строкой правки, и вернувший её не узнает, что нарушил
    решение: тест списка останется зелёным.
    """
    source = Path("app/repositories/user.py").read_text(encoding="utf-8")
    assert "def get_all_users" not in source
    assert "def search_users" not in source


# --- Подстановочные знаки LIKE внутри искомого текста (WR-10) -----------------


@pytest.mark.asyncio
async def test_an_underscore_in_the_search_matches_an_underscore(
    db_session: AsyncSession,
):
    """Подчёркивание ищется как ЗНАК, а не как «любой один знак».

    ⚠️ ЭТО НЕ ВОПРОС БЕЗОПАСНОСТИ. Инъекции здесь нет и не было: текст едет
    параметром. Предмет — обещание подраздела «администратор ищет КОНКРЕТНОГО
    человека», которое тихо не выполнялось: `%` и `_` внутри текста сохраняли
    своё значение для `LIKE`. Подчёркивание — частый знак в локальной части
    почтового адреса, то есть случай рабочий.
    """
    await _seed_user(db_session, name="Первый", email="a_b@test.com")
    await _seed_user(db_session, name="Второй", email="axb@test.com")

    users, total = await _page_and_count(db_session, search="a_b")

    assert total == len(users) == 1, (
        f"поиск `a_b` нашёл {total} записей — подчёркивание сработало как "
        "«любой один знак», и администратор получил не того человека"
    )
    assert users[0].email == "a_b@test.com"


@pytest.mark.asyncio
async def test_a_percent_in_the_search_matches_a_percent(db_session: AsyncSession):
    """Знак процента ищется как знак, а не как «что угодно».

    Худший случай предыдущего дефекта: поиск из одного знака `%` (или `_`)
    возвращал ВСЕХ пользователей продукта, то есть выглядел как «поиск не
    работает» ровно наоборот — он находил всё.
    """
    await _seed_user(db_session, name="Скидка 50% навсегда", email="one@test.com")
    await _seed_user(db_session, name="Обычный", email="two@test.com")

    exact, exact_total = await _page_and_count(db_session, search="50% нав")
    assert exact_total == len(exact) == 1
    assert exact[0].email == "one@test.com"

    _everyone, wildcard_total = await _page_and_count(db_session, search="%")
    assert wildcard_total == 1, (
        f"поиск одного знака процента вернул {wildcard_total} записей — знак "
        "сработал подстановочным и нашёл всех"
    )


@pytest.mark.asyncio
async def test_a_backslash_in_the_search_is_matched_and_escapes_nothing(
    db_session: AsyncSession,
):
    """Обратная косая — тоже искомый знак, а не экранирующий.

    ⚠️ ПОРЯДОК ЗАМЕН НЕСУЩИЙ, И ЭТОТ СЛУЧАЙ ЕГО ЛОВИТ. Экранируй мы `%` и `_`
    раньше самой обратной косой — дописанные экранирующие знаки были бы
    экранированы повторно, и текст перестал бы находить сам себя.
    """
    await _seed_user(db_session, name=r"путь C:\temp", email="slash@test.com")
    await _seed_user(db_session, name="Обычный", email="plain@test.com")

    users, total = await _page_and_count(db_session, search=r"C:\temp")

    assert total == len(users) == 1, (
        f"поиск с обратной косой нашёл {total} записей — знак истолкован "
        "экранирующим, и текст перестал находить сам себя"
    )
    assert users[0].email == "slash@test.com"


@pytest.mark.asyncio
async def test_the_ordinary_substring_search_still_works(db_session: AsyncSession):
    """ГРАНИЦА СВЕРХУ: обычный поиск подстрокой не сломан экранированием.

    Без этого утверждения экранирование, применённое и к обрамляющим `%`,
    прошло бы все три случая выше и превратило бы поиск подстрокой в поиск
    точного совпадения — то есть отняло бы сам подраздел.
    """
    await _seed_user(db_session, name="Иван Петров", email="ivan@test.com")
    await _seed_user(db_session, name="Сергей Сидоров", email="sergey@test.com")

    users, total = await _page_and_count(db_session, search="етро")

    assert total == len(users) == 1, (
        f"поиск подстрокой нашёл {total} записей — обрамляющие знаки "
        "экранированы вместе с текстом, и поиск стал точным совпадением"
    )
    assert users[0].email == "ivan@test.com"
