"""План 02-07: сводный список расписаний (SCH-04, SCH-05).

Файл закрепляет ДВА обещания сводного списка, каждое своим слоем:

* Задача 1 — ДАННЫЕ карточки. Имена групп разрешаются ОДНИМ запросом на всю
  страницу и только среди групп владельца; идентификатор без совпадения в имя
  не превращается; признак черновика доходит до шаблона сравнением с
  константой, а не со строковым литералом.
* Задача 3 — РАЗМЕТКА карточки, два пустых состояния, склонения счётчика и
  перекрёстная изоляция переключения.

Порядок именно такой: разрешение имён и признак черновика — свойства
обработчика, и утверждать их по отрендеренной странице значило бы проверять
разом две правки. Ошибка в разметке проявится ПУСТОЙ карточкой (страница
вернёт 200), поэтому Задача 3 утверждает реальные строки, а не код ответа.
"""

import contextlib
import re
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from app.pages.schedules import (
    SUMMARY_GROUP_NAMES,
    _build_schedule_items,
    _clean_choice,
    _group_names_for,
)

# Запрос к таблице групп в журнале выполненных операторов. Имя таблицы может
# прийти в кавычках (groups — зарезервированное слово в части диалектов),
# поэтому сравнение идёт регулярным выражением, а не подстрокой.
GROUPS_QUERY_RE = re.compile(r'FROM\s+"?groups"?', re.I)


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_ad(
    db: AsyncSession, title: str = "Объявление", status: str = AD_STATUS_PUBLISHED
) -> Ad:
    user = await _user(db)
    ad = Ad(user_id=user.id, title=title, text="Текст объявления", images=[], status=status)
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


async def _seed_account(db: AsyncSession, type_: str = "wa") -> MessengerAccount:
    user = await _user(db)
    account = MessengerAccount(
        user_id=user.id, type=type_, credentials="session", status="active"
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def _seed_group(
    db: AsyncSession, account: MessengerAccount, name: str, user_id: int | None = None
) -> Group:
    user = await _user(db)
    group = Group(
        user_id=user.id if user_id is None else user_id,
        account_id=account.id,
        messenger_type=account.type,
        group_external_id=f"ext-{name}",
        name=name,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def _seed_schedule(
    db: AsyncSession,
    ad: Ad,
    account: MessengerAccount | None = None,
    group_ids: list[int] | None = None,
    days: list[int] | None = None,
    times: list[str] | None = None,
    is_active: bool = True,
) -> Schedule:
    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id if account else None,
        group_ids=group_ids if group_ids is not None else [],
        days_of_week=days if days is not None else [0, 2, 4],
        times_of_day=times if times is not None else ["09:30"],
        timezone="UTC",
        is_active=is_active,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@contextlib.contextmanager
def _statement_log(db_session: AsyncSession):
    """Журнал SQL-операторов, выполненных за время блока.

    Слушатель вешается на СИНХРОННЫЙ движок за асинхронным: событие
    before_cursor_execute объявлено именно там. Снимается в finally — иначе
    журнал следующего теста наследовал бы чужой слушатель.
    """
    engine = db_session.bind.sync_engine
    seen: list[str] = []

    def _before(conn, cursor, statement, parameters, context, executemany):
        seen.append(statement)

    event.listen(engine, "before_cursor_execute", _before)
    try:
        yield seen
    finally:
        event.remove(engine, "before_cursor_execute", _before)


def _row(schedule, ad_title="Объявление", ad_status=AD_STATUS_PUBLISHED, messenger_type="wa"):
    """Строка выдачи обработчика: ровно те поля, что даёт его select."""
    return SimpleNamespace(
        Schedule=schedule,
        ad_title=ad_title,
        ad_status=ad_status,
        messenger_type=messenger_type,
    )


def _fake_schedule(group_ids: list[int]) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        group_ids=group_ids,
        days_of_week=[0],
        times_of_day=["09:00"],
        next_run_at=None,
        is_active=True,
        account_id=1,
    )


# --- Задача 1: имена групп разрешаются одним запросом и только у владельца ----


@pytest.mark.asyncio
async def test_group_names_are_resolved_for_the_owner(db_session: AsyncSession):
    """Карточка получает ИМЕНА своих групп, а не только их число (SCH-04)."""
    user = await _user(db_session)
    account = await _seed_account(db_session)
    first = await _seed_group(db_session, account, "Клуб выходного дня")
    second = await _seed_group(db_session, account, "Барахолка района")
    schedule = _fake_schedule([first.id, second.id])

    names = await _group_names_for(db_session, user.id, [schedule])

    assert names == {first.id: "Клуб выходного дня", second.id: "Барахолка района"}


@pytest.mark.asyncio
async def test_foreign_group_name_never_becomes_a_card_value(db_session: AsyncSession):
    """T-02-34: идентификаторы групп приходят массивом внутри расписания.

    Без ограничения по владельцу имя ЧУЖОЙ группы попало бы в карточку — своё
    расписание достаточно сохранить с чужим идентификатором.
    """
    user = await _user(db_session)
    account = await _seed_account(db_session)
    own = await _seed_group(db_session, account, "Своя группа")
    foreign = await _seed_group(
        db_session, account, "Чужая группа", user_id=user.id + 1000
    )
    schedule = _fake_schedule([own.id, foreign.id])

    names = await _group_names_for(db_session, user.id, [schedule])

    assert names == {own.id: "Своя группа"}
    assert "Чужая группа" not in names.values()


@pytest.mark.asyncio
async def test_group_names_query_is_skipped_when_there_is_nothing_to_resolve(
    db_session: AsyncSession,
):
    """Расписание без групп не порождает запроса вовсе."""
    user = await _user(db_session)

    with _statement_log(db_session) as seen:
        names = await _group_names_for(db_session, user.id, [_fake_schedule([])])

    assert names == {}
    assert not [s for s in seen if GROUPS_QUERY_RE.search(s)]


@pytest.mark.asyncio
async def test_summary_page_resolves_group_names_in_one_query(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-02-38: тридцать расписаний — один запрос имён, а не тридцать.

    Утверждение о РОСТЕ, а не о конкретном числе: запросов страницы несколько
    (пользователь, расписания, счётчик, имена), но по числу расписаний не
    растёт ни один.
    """
    ad = await _seed_ad(db_session, title="Объявление страницы")
    account = await _seed_account(db_session)
    groups = [
        await _seed_group(db_session, account, f"Группа {i}") for i in range(30)
    ]
    for group in groups:
        await _seed_schedule(db_session, ad, account, group_ids=[group.id])

    with _statement_log(db_session) as seen:
        response = await authed_client.get("/schedules")

    assert response.status_code == 200
    group_queries = [s for s in seen if GROUPS_QUERY_RE.search(s)]
    assert len(group_queries) <= 1, (
        f"имена групп разрешаются {len(group_queries)} запросами — по запросу на "
        "расписание вместо одного на страницу"
    )
    assert len(seen) < 30, (
        f"число запросов страницы ({len(seen)}) растёт по числу расписаний"
    )


@pytest.mark.asyncio
async def test_missing_group_does_not_break_the_page(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Удалённая или недоступная группа не роняет страницу."""
    ad = await _seed_ad(db_session, title="Объявление с потерянной группой")
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Единственная живая группа")
    await _seed_schedule(db_session, ad, account, group_ids=[group.id, 999_999])

    response = await authed_client.get("/schedules")

    assert response.status_code == 200
    assert "Единственная живая группа" in response.text


# --- Задача 1: состав элемента строки ----------------------------------------


def test_item_carries_group_names_and_the_remainder():
    """Имена первых нескольких групп плюс остаток числом (RESEARCH Q3)."""
    ids = list(range(1, SUMMARY_GROUP_NAMES + 3))
    names = {gid: f"Группа {gid}" for gid in ids}
    user = SimpleNamespace(timezone="UTC")

    (item,) = _build_schedule_items([_row(_fake_schedule(ids))], user, None, names)

    assert item["group_names"] == [f"Группа {gid}" for gid in ids[:SUMMARY_GROUP_NAMES]]
    assert item["group_extra"] == len(ids) - SUMMARY_GROUP_NAMES
    assert item["group_total"] == len(ids)


def test_unresolved_group_id_does_not_become_an_empty_name():
    """Идентификатор без совпадения не рендерится пустой строкой.

    Остаток тоже считается по РАЗРЕШЁННЫМ именам: иначе карточка обещала бы
    «и ещё 1», которого показать нечем.
    """
    user = SimpleNamespace(timezone="UTC")

    (item,) = _build_schedule_items(
        [_row(_fake_schedule([1, 777]))], user, None, {1: "Живая группа"}
    )

    assert item["group_names"] == ["Живая группа"]
    assert "" not in item["group_names"]
    assert item["group_extra"] == 0
    assert item["group_total"] == 1


def test_draft_ad_marks_its_schedule():
    """Расписание объявления-черновика приходит в шаблон с признаком (D-01)."""
    user = SimpleNamespace(timezone="UTC")

    (item,) = _build_schedule_items(
        [_row(_fake_schedule([]), ad_status=AD_STATUS_DRAFT)], user, None, {}
    )

    assert item["is_draft"] is True


def test_published_ad_does_not_mark_its_schedule():
    """Парный тест: без него предыдущий зеленел бы на константе True."""
    user = SimpleNamespace(timezone="UTC")

    (item,) = _build_schedule_items(
        [_row(_fake_schedule([]), ad_status=AD_STATUS_PUBLISHED)], user, None, {}
    )

    assert item["is_draft"] is False


# --- Задача 1: испорченное значение фильтра (T-02-35) ------------------------


@pytest.mark.parametrize(
    "value",
    [None, "", "   ", "unknown", "'; DROP TABLE schedules; --", "tg_user\x00"],
)
def test_unknown_filter_value_falls_back_to_all(value):
    """Неизвестное значение приводит к варианту «Все», а не к ошибке (E14)."""
    assert _clean_choice(value, ("tg_user", "wa", "max")) == ""


@pytest.mark.parametrize("value", ["tg_user", "wa", "max"])
def test_known_filter_value_survives(value):
    """Парный тест: без него предыдущий зеленел бы на функции, всегда пустой."""
    assert _clean_choice(value, ("tg_user", "wa", "max")) == value
