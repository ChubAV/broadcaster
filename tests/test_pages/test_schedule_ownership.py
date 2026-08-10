"""CR-01 / D-20: владение `ad_id` и `account_id` при постановке расписания.

`Schedule` не имеет собственного `user_id` — принадлежность расписания выводится
через объявление. Поэтому `ad_id` и `account_id`, пришедшие полем формы, задают
не только содержание рассылки, но и её владельца: без проверки пользователь
ставит рассылку на чужое объявление и, что хуже, отправляет её ЧЕРЕЗ чужой
подключённый аккаунт мессенджера.

Форма теста — перекрёстная изоляция: чужая запись сеется с заведомо другим
`user_id`, и утверждается, что она не тронута, а новая не появилась.
"""

from urllib.parse import urlencode

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User

FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


@pytest_asyncio.fixture
async def owner(db_session: AsyncSession) -> User:
    """Пользователь, под которым ходит `authed_client`."""
    result = await db_session.execute(
        select(User).where(User.email == "testuser@test.com")
    )
    return result.scalar_one()


@pytest_asyncio.fixture
async def stranger(db_session: AsyncSession) -> User:
    """Другой пользователь — владелец «чужих» объявления и аккаунта."""
    user = User(email="stranger@test.com", password_hash="x", name="Stranger")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _seed_ad(db_session: AsyncSession, user_id: int, title: str) -> int:
    ad = Ad(user_id=user_id, title=title, text="Текст", images=[])
    db_session.add(ad)
    await db_session.commit()
    await db_session.refresh(ad)
    return ad.id


async def _seed_account(db_session: AsyncSession, user_id: int) -> int:
    account = MessengerAccount(user_id=user_id, type="tg_user", credentials="creds")
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)
    return account.id


async def _seed_schedule(db_session: AsyncSession, ad_id: int, account_id: int) -> int:
    schedule = Schedule(
        ad_id=ad_id,
        account_id=account_id,
        group_ids=[],
        days_of_week=[1],
        times_of_day=["09:00"],
        timezone="UTC",
    )
    db_session.add(schedule)
    await db_session.commit()
    await db_session.refresh(schedule)
    return schedule.id


def _form(ad_id: int, account_id: int) -> str:
    return urlencode(
        [
            ("ad_id", str(ad_id)),
            ("account_id", str(account_id)),
            ("days_of_week", "2"),
            ("times_of_day", "18:30"),
            ("timezone", "UTC"),
        ]
    )


async def _schedules(db_session: AsyncSession) -> list[Schedule]:
    db_session.expire_all()
    return list((await db_session.execute(select(Schedule))).scalars().all())


# --- Создание -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_page_create_rejects_foreign_ad(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    """Чужое `ad_id` — расписание не создаётся."""
    foreign_ad = await _seed_ad(db_session, stranger.id, "Чужое объявление")
    own_account = await _seed_account(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(foreign_ad, own_account),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert await _schedules(db_session) == []


@pytest.mark.asyncio
async def test_page_create_rejects_foreign_account(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    """Чужой `account_id` — расписание не создаётся.

    Это тяжелее подмены объявления: рассылка ушла бы через чужую подключённую
    сессию мессенджера и списалась бы с чужого баланса.
    """
    own_ad = await _seed_ad(db_session, owner.id, "Своё объявление")
    foreign_account = await _seed_account(db_session, stranger.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(own_ad, foreign_account),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert await _schedules(db_session) == []


@pytest.mark.asyncio
async def test_page_create_accepts_own_ad_and_account(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    own_ad = await _seed_ad(db_session, owner.id, "Своё объявление")
    own_account = await _seed_account(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(own_ad, own_account),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    created = await _schedules(db_session)
    assert len(created) == 1
    assert created[0].ad_id == own_ad
    assert created[0].account_id == own_account


# --- Обновление ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_page_update_rejects_swapping_in_foreign_ad(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    own_ad = await _seed_ad(db_session, owner.id, "Своё объявление")
    own_account = await _seed_account(db_session, owner.id)
    schedule_id = await _seed_schedule(db_session, own_ad, own_account)
    foreign_ad = await _seed_ad(db_session, stranger.id, "Чужое объявление")

    response = await authed_client.post(
        f"/schedules/{schedule_id}/edit",
        content=_form(foreign_ad, own_account),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    db_session.expire_all()
    stored = (
        await db_session.execute(select(Schedule).where(Schedule.id == schedule_id))
    ).scalar_one()
    assert stored.ad_id == own_ad


@pytest.mark.asyncio
async def test_page_update_rejects_swapping_in_foreign_account(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    own_ad = await _seed_ad(db_session, owner.id, "Своё объявление")
    own_account = await _seed_account(db_session, owner.id)
    schedule_id = await _seed_schedule(db_session, own_ad, own_account)
    foreign_account = await _seed_account(db_session, stranger.id)

    response = await authed_client.post(
        f"/schedules/{schedule_id}/edit",
        content=_form(own_ad, foreign_account),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    db_session.expire_all()
    stored = (
        await db_session.execute(select(Schedule).where(Schedule.id == schedule_id))
    ).scalar_one()
    assert stored.account_id == own_account


@pytest.mark.asyncio
async def test_page_update_accepts_own_ad_and_account(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    own_ad = await _seed_ad(db_session, owner.id, "Своё объявление")
    own_account = await _seed_account(db_session, owner.id)
    schedule_id = await _seed_schedule(db_session, own_ad, own_account)
    other_own_ad = await _seed_ad(db_session, owner.id, "Другое своё объявление")

    response = await authed_client.post(
        f"/schedules/{schedule_id}/edit",
        content=_form(other_own_ad, own_account),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    db_session.expire_all()
    stored = (
        await db_session.execute(select(Schedule).where(Schedule.id == schedule_id))
    ).scalar_one()
    assert stored.ad_id == other_own_ad
    assert stored.times_of_day == ["18:30"]


# --- План 02-05: путь из редактора не обходит проверки владения (T-02-26) -----
#
# Новый путь приходит на ТЕ ЖЕ маршруты с тем же набором идентификаторов —
# добавляется только признак происхождения. Соблазн ветки «пришло из редактора,
# значит своё» здесь и закрывается: признак подконтролен отправителю ровно так
# же, как ad_id и account_id, и доверия не несёт.


def _editor_form(ad_id: int, account_id: int) -> str:
    return urlencode(
        [
            ("ad_id", str(ad_id)),
            ("account_id", str(account_id)),
            ("days_of_week", "2"),
            ("times_of_day", "18:30"),
            ("timezone", "UTC"),
            ("return_to", "editor"),
        ]
    )


@pytest.mark.asyncio
async def test_editor_path_rejects_foreign_ad(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    foreign_ad = await _seed_ad(db_session, stranger.id, "Чужое объявление")
    own_account = await _seed_account(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_editor_form(foreign_ad, own_account),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert await _schedules(db_session) == []
    # Отказ уводит на сводный список: адрес редактора чужого объявления
    # построить не из чего — запись владением не подтверждена.
    assert response.headers["location"] == "/schedules"


@pytest.mark.asyncio
async def test_editor_path_rejects_foreign_account(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    own_ad = await _seed_ad(db_session, owner.id, "Своё объявление")
    foreign_account = await _seed_account(db_session, stranger.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_editor_form(own_ad, foreign_account),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert await _schedules(db_session) == []


@pytest.mark.asyncio
async def test_editor_path_rejects_swapping_in_a_foreign_ad(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    own_ad = await _seed_ad(db_session, owner.id, "Своё объявление")
    own_account = await _seed_account(db_session, owner.id)
    schedule_id = await _seed_schedule(db_session, own_ad, own_account)
    foreign_ad = await _seed_ad(db_session, stranger.id, "Чужое объявление")

    response = await authed_client.post(
        f"/schedules/{schedule_id}/edit",
        content=_editor_form(foreign_ad, own_account),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    db_session.expire_all()
    stored = (
        await db_session.execute(select(Schedule).where(Schedule.id == schedule_id))
    ).scalar_one()
    assert stored.ad_id == own_ad


@pytest.mark.asyncio
async def test_editor_path_cannot_delete_a_foreign_schedule(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    foreign_ad = await _seed_ad(db_session, stranger.id, "Чужое объявление")
    foreign_account = await _seed_account(db_session, stranger.id)
    foreign_schedule = await _seed_schedule(db_session, foreign_ad, foreign_account)

    response = await authed_client.post(
        f"/schedules/{foreign_schedule}/delete",
        content=urlencode([("return_to", "editor")]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/schedules"
    assert len(await _schedules(db_session)) == 1
