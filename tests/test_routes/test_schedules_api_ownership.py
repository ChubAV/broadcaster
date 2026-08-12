"""CR-02 / T-02G-06: владение ГРУППАМИ на JSON-входе расписаний.

`Schedule` не имеет собственного `user_id`, а `group_ids` хранятся массивом
идентификаторов. Ниже по потоку никто их не перепроверяет: `collect_due_schedules`
итерирует `schedule.group_ids` как есть, `send_message_once` резолвит группу по
первичному ключу. Поэтому чужой идентификатор группы, принятый на create или на
update, доезжает до `SendLog` со СВОИМ `user_id` — то есть в историю и дашборд
атакующего, — а сообщение уходит в чужой `group_external_id` везде, где своя
сессия мессенджера состоит в той же группе.

Страничный слой сводит присланные `group_ids` к группам владельца И выбранного
аккаунта (`app/pages/schedules.py`: `_groups_of_account`, затем фильтрация),
JSON-API — нет. Здесь закрепляется, что правило ОДНО на оба входа, и той же
проверкой — что определение полноты расписания тоже одно (WR-05, D-08).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from tests.conftest import seed_group


# --- Свои сущности ------------------------------------------------------------
#
# Объявление и аккаунт — через публичные маршруты. Группа — прямой вставкой
# через ORM: прикладного входа её создания в приложении нет (GRP-08 снято,
# JSON-маршрут групп удалён — план 03-07). Владельца группа наследует ОТ
# АККАУНТА, ровно как это делает синхронизация, — то есть «своя группа»
# остаётся своей по тому же признаку, что и раньше.


async def _create_ad(client: AsyncClient, auth_headers: dict, title: str = "Schedule Ad") -> int:
    response = await client.post(
        "/api/ads",
        json={"title": title, "text": "Текст объявления"},
        headers=auth_headers,
    )
    return response.json()["id"]


async def _create_account(
    client: AsyncClient, auth_headers: dict, credentials: str = "creds"
) -> int:
    response = await client.post(
        "/api/accounts",
        json={"type": "tg_user", "credentials": credentials},
        headers=auth_headers,
    )
    return response.json()["id"]


async def _create_group(
    db_session: AsyncSession,
    account_id: int,
    external_id: str = "-1001000000001",
    name: str = "Своя группа",
) -> int:
    group = await seed_group(
        db_session, account_id, group_external_id=external_id, name=name
    )
    return group.id


async def _own_setup(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
) -> tuple[int, int, int]:
    """Объявление, аккаунт и группа ЭТОГО аккаунта — минимальный полный набор."""
    ad_id = await _create_ad(client, auth_headers)
    account_id = await _create_account(client, auth_headers)
    group_id = await _create_group(db_session, account_id)
    return ad_id, account_id, group_id


# --- Чужие сущности: посевом, по образцу tests/test_pages/test_schedule_ownership.py


async def _seed_foreign_group(db_session: AsyncSession) -> int:
    """Группа ДРУГОГО пользователя, заведённая на ЕГО же аккаунте.

    Идентификаторы снимаются сразу после каждого посева: последующий `commit()`
    и `expire_all()` в проверках сбрасывают загруженные атрибуты, и обращение к
    живому ORM-объекту из синхронного кода теста ушло бы в ленивую подгрузку вне
    greenlet-а — падение по инфраструктурной причине, а не по существу дефекта.
    """
    stranger = User(email="stranger-groups@test.com", password_hash="x", name="Stranger")
    db_session.add(stranger)
    await db_session.commit()
    await db_session.refresh(stranger)
    stranger_id = stranger.id

    account = MessengerAccount(user_id=stranger_id, type="tg_user", credentials="creds")
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    foreign_account_id = account.id

    group = Group(
        user_id=stranger_id,
        account_id=foreign_account_id,
        messenger_type="tg_user",
        group_external_id="-1009000000009",
        name="Чужая группа",
    )
    db_session.add(group)
    await db_session.commit()
    await db_session.refresh(group)
    return group.id


async def _schedule_rows(db_session: AsyncSession) -> list[Schedule]:
    db_session.expire_all()
    return list((await db_session.execute(select(Schedule))).scalars().all())


async def _stored(db_session: AsyncSession, schedule_id: int) -> Schedule:
    db_session.expire_all()
    return (
        await db_session.execute(select(Schedule).where(Schedule.id == schedule_id))
    ).scalar_one()


async def _create_full_schedule(
    client: AsyncClient, auth_headers: dict, ad_id: int, account_id: int, group_id: int
) -> int:
    response = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": [group_id],
            "days_of_week": [0, 1, 2, 3, 4, 5, 6],
            "times_of_day": ["09:00"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


# --- Владение группами на создании --------------------------------------------


@pytest.mark.asyncio
async def test_create_rejects_a_group_id_of_another_user(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    ad_id, account_id, _ = await _own_setup(client, auth_headers, db_session)
    foreign_group_id = await _seed_foreign_group(db_session)

    response = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": [foreign_group_id],
            "days_of_week": [0],
            "times_of_day": ["09:00"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert await _schedule_rows(db_session) == []


@pytest.mark.asyncio
async def test_create_rejects_a_group_id_of_another_account_of_the_same_user(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """Правило то же, что на страничном пути: группа принадлежит владельцу И
    ВЫБРАННОМУ аккаунту. Своя группа чужого аккаунта — всё равно не та группа."""
    ad_id = await _create_ad(client, auth_headers)
    first_account_id = await _create_account(client, auth_headers, "creds-first")
    second_account_id = await _create_account(client, auth_headers, "creds-second")
    other_account_group_id = await _create_group(
        db_session,
        second_account_id,
        external_id="-1001000000002",
        name="Группа второго аккаунта",
    )

    response = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": first_account_id,
            "group_ids": [other_account_group_id],
            "days_of_week": [0],
            "times_of_day": ["09:00"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert await _schedule_rows(db_session) == []


@pytest.mark.asyncio
async def test_create_accepts_own_group_ids(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    ad_id, account_id, group_id = await _own_setup(client, auth_headers, db_session)

    response = await client.post(
        "/api/schedules",
        json={
            "ad_id": ad_id,
            "account_id": account_id,
            "group_ids": [group_id],
            "days_of_week": [0],
            "times_of_day": ["09:00"],
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["group_ids"] == [group_id]
    assert len(await _schedule_rows(db_session)) == 1


# --- Владение группами на обновлении ------------------------------------------


@pytest.mark.asyncio
async def test_update_rejects_swapping_in_a_foreign_group_id(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    ad_id, account_id, group_id = await _own_setup(client, auth_headers, db_session)
    schedule_id = await _create_full_schedule(
        client, auth_headers, ad_id, account_id, group_id
    )
    foreign_group_id = await _seed_foreign_group(db_session)

    response = await client.put(
        f"/api/schedules/{schedule_id}",
        json={"group_ids": [foreign_group_id]},
        headers=auth_headers,
    )

    assert response.status_code == 404
    stored = await _stored(db_session, schedule_id)
    assert stored.group_ids == [group_id]


@pytest.mark.asyncio
async def test_update_without_group_ids_leaves_them_untouched(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """Проверка владения выполняется, только когда ключ ПРИСУТСТВУЕТ в патче.

    Отсутствующий ключ означает «не трогать»; отказ на нём превратил бы частичное
    обновление в обязательную передачу всего состава групп.
    """
    ad_id, account_id, group_id = await _own_setup(client, auth_headers, db_session)
    schedule_id = await _create_full_schedule(
        client, auth_headers, ad_id, account_id, group_id
    )

    response = await client.put(
        f"/api/schedules/{schedule_id}",
        json={"days_of_week": [1, 3]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["group_ids"] == [group_id]
    assert response.json()["days_of_week"] == [1, 3]
    stored = await _stored(db_session, schedule_id)
    assert stored.group_ids == [group_id]


# --- Одно определение полноты на оба входа (WR-05, D-08) ----------------------


@pytest.mark.asyncio
async def test_api_toggle_refuses_to_enable_an_incomplete_schedule(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """Аккаунт есть, а групп, дней и времён нет — включать нечего.

    Страничный тумблер такое расписание уже не включает; API-тумблер сегодня
    смотрит только на `account_id`, и то же расписание через JSON включается.
    """
    ad_id = await _create_ad(client, auth_headers)
    account_id = await _create_account(client, auth_headers)
    schedule = Schedule(
        ad_id=ad_id,
        account_id=account_id,
        group_ids=[],
        days_of_week=[],
        times_of_day=[],
        timezone="UTC",
        is_active=False,
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)
    schedule_id = schedule.id

    response = await client.post(
        f"/api/schedules/{schedule_id}/toggle", headers=auth_headers
    )

    assert response.status_code == 400
    stored = await _stored(db_session, schedule_id)
    assert stored.is_active is False
    assert stored.next_run_at is None


@pytest.mark.asyncio
async def test_api_toggle_pausing_an_active_schedule_is_never_blocked(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """Право поставить на паузу не зависит от заполненности."""
    ad_id, account_id, group_id = await _own_setup(client, auth_headers, db_session)
    schedule_id = await _create_full_schedule(
        client, auth_headers, ad_id, account_id, group_id
    )

    response = await client.post(
        f"/api/schedules/{schedule_id}/toggle", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["next_run_at"] is None


@pytest.mark.asyncio
async def test_double_toggle_returns_to_the_initial_state(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """`is_active` вычисляется от значения В БАЗЕ, а не от присланного клиентом."""
    ad_id, account_id, group_id = await _own_setup(client, auth_headers, db_session)
    schedule_id = await _create_full_schedule(
        client, auth_headers, ad_id, account_id, group_id
    )
    initial = (await _stored(db_session, schedule_id)).is_active

    first = await client.post(
        f"/api/schedules/{schedule_id}/toggle", headers=auth_headers
    )
    second = await client.post(
        f"/api/schedules/{schedule_id}/toggle", headers=auth_headers
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["is_active"] is not initial
    assert second.json()["is_active"] is initial
    assert (await _stored(db_session, schedule_id)).is_active is initial


# --- Приостановленное расписание не рекламирует отправку (WR-06) --------------


@pytest.mark.asyncio
async def test_paused_schedule_does_not_carry_a_future_next_run(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    ad_id, account_id, group_id = await _own_setup(client, auth_headers, db_session)
    schedule_id = await _create_full_schedule(
        client, auth_headers, ad_id, account_id, group_id
    )
    paused = await client.post(
        f"/api/schedules/{schedule_id}/toggle", headers=auth_headers
    )
    assert paused.json()["is_active"] is False

    response = await client.put(
        f"/api/schedules/{schedule_id}",
        json={"days_of_week": [0, 1, 2], "times_of_day": ["10:00"]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["next_run_at"] is None
    stored = await _stored(db_session, schedule_id)
    assert stored.next_run_at is None


@pytest.mark.asyncio
async def test_repeated_update_is_idempotent(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    ad_id, account_id, group_id = await _own_setup(client, auth_headers, db_session)
    schedule_id = await _create_full_schedule(
        client, auth_headers, ad_id, account_id, group_id
    )
    body = {
        "group_ids": [group_id],
        "days_of_week": [0, 1, 2, 3, 4, 5, 6],
        "times_of_day": ["09:00"],
        "timezone": "UTC",
    }

    first = await client.put(
        f"/api/schedules/{schedule_id}", json=body, headers=auth_headers
    )
    second = await client.put(
        f"/api/schedules/{schedule_id}", json=body, headers=auth_headers
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["is_active"] == second.json()["is_active"]
    assert first.json()["next_run_at"] == second.json()["next_run_at"]
    assert first.json()["group_ids"] == second.json()["group_ids"] == [group_id]
    assert len(await _schedule_rows(db_session)) == 1
