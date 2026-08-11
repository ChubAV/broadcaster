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


def _assert_returned_to_editor(response, ad_id: int) -> None:
    """Отказ при ПОДТВЕРЖДЁННО своём объявлении возвращает в его редактор.

    Ошибка по данным — не навигация: пользователь остаётся там, где набирал
    группы, дни и времена, и получает объяснение (WR-07). Адрес строится
    сервером из подтверждённой записи, поэтому проверяется он целиком.
    """
    location = response.headers["location"]
    assert location.startswith(f"/ads/{ad_id}/edit")
    assert "sched_error" in location


def _assert_indistinguishable_refusal(response) -> None:
    """Чужое или отсутствующее объявление — прежний молчаливый редирект.

    Различимое поведение подтверждало бы существование чужой записи перебором
    идентификаторов, поэтому здесь ни адреса редактора, ни признака ошибки.
    """
    assert response.headers["location"] == "/schedules"


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
    _assert_indistinguishable_refusal(response)


@pytest.mark.asyncio
async def test_page_create_rejects_foreign_account(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    """Чужой `account_id` — расписание не создаётся.

    Это тяжелее подмены объявления: рассылка ушла бы через чужую подключённую
    сессию мессенджера и списалась бы с чужого баланса.

    Объявление при этом СВОЁ, поэтому отказ возвращает в его редактор с
    объяснением, а не уводит на сводный список молча (WR-07). Сам отказ не
    ослаблен ни на йоту: строки `schedules` по-прежнему не появляется.
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
    _assert_returned_to_editor(response, own_ad)


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
    _assert_indistinguishable_refusal(response)
    db_session.expire_all()
    stored = (
        await db_session.execute(select(Schedule).where(Schedule.id == schedule_id))
    ).scalar_one()
    assert stored.ad_id == own_ad


@pytest.mark.asyncio
async def test_page_update_rejects_swapping_in_foreign_account(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    """Объявление своё, аккаунт чужой: отказ остаётся отказом, но объясняется."""
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
    _assert_returned_to_editor(response, own_ad)
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
    _assert_indistinguishable_refusal(response)


@pytest.mark.asyncio
async def test_editor_path_rejects_foreign_account(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    """Объявление своё — пользователь возвращается в его редактор с признаком.

    Признак происхождения на РЕШЕНИЕ по-прежнему не влияет: расписание не
    создаётся. Меняется только форма отказа, и только там, где объявление
    подтверждено своим.
    """
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
    _assert_returned_to_editor(response, own_ad)


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
    _assert_indistinguishable_refusal(response)
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


# --- План 02-09: отказ по данным перестаёт быть навигацией (WR-07) ------------


SCHEDULE_ERROR_TEXT = (
    "Аккаунт или объявление недоступны. Обновите страницу и попробуйте снова."
)


@pytest.mark.asyncio
async def test_editor_shows_the_refusal_message_in_the_schedules_section(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Формулировка контракта UI-SPEC (E4 `error`) видна и стоит ГДЕ надо.

    Сообщение живёт в секции расписаний, то есть ПОСЛЕ закрытия элемента
    `<form id="ad-form">`: внутри него оно было бы вложенной формой ровно тогда,
    когда его поставили бы неаккуратно, и браузер молча отключил бы кнопки
    карточек расписаний.
    """
    own_ad = await _seed_ad(db_session, owner.id, "Своё объявление")

    response = await authed_client.get(f"/ads/{own_ad}/edit?sched_error=account")

    assert response.status_code == 200
    body = response.text
    assert SCHEDULE_ERROR_TEXT in body

    form_open = body.index('<form id="ad-form"')
    form_close = body.index("</form>", form_open)
    assert body.index(SCHEDULE_ERROR_TEXT) > form_close


@pytest.mark.asyncio
async def test_editor_without_the_flag_shows_no_refusal_message(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    own_ad = await _seed_ad(db_session, owner.id, "Своё объявление")

    response = await authed_client.get(f"/ads/{own_ad}/edit")

    assert response.status_code == 200
    assert SCHEDULE_ERROR_TEXT not in response.text


@pytest.mark.asyncio
async def test_editor_never_prints_the_query_value_itself(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Признак ВЫБИРАЕТ серверный текст, а не является им.

    Приняв значение текстом, страница печатала бы произвольное сообщение от
    имени приложения по одной лишь ссылке с чужого сайта. Неизвестный признак
    не выбирает ничего — и страницу при этом не роняет: значение приходит
    строкой запроса, то есть из ссылки, закладки или чужого сообщения.
    """
    own_ad = await _seed_ad(db_session, owner.id, "Своё объявление")

    response = await authed_client.get(
        f"/ads/{own_ad}/edit?sched_error=Ваш+аккаунт+заблокирован"
    )

    assert response.status_code == 200
    assert "заблокирован" not in response.text
    assert SCHEDULE_ERROR_TEXT not in response.text


@pytest.mark.asyncio
async def test_update_of_a_missing_schedule_returns_to_the_own_editor(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Записи нет — правки всё равно не исчезают молча.

    Объявление подтверждено своим, поэтому пользователь возвращается в его
    редактор. О чужих расписаниях это не сообщает ничего: тот же ответ приходит
    и на несуществующий идентификатор, и на чужой.
    """
    own_ad = await _seed_ad(db_session, owner.id, "Своё объявление")
    own_account = await _seed_account(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/999999/edit",
        content=_form(own_ad, own_account),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    _assert_returned_to_editor(response, own_ad)
    assert await _schedules(db_session) == []


@pytest.mark.asyncio
async def test_update_of_a_foreign_schedule_with_a_foreign_ad_stays_silent(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, stranger: User
):
    foreign_ad = await _seed_ad(db_session, stranger.id, "Чужое объявление")
    foreign_account = await _seed_account(db_session, stranger.id)
    foreign_schedule = await _seed_schedule(db_session, foreign_ad, foreign_account)

    response = await authed_client.post(
        f"/schedules/{foreign_schedule}/edit",
        content=_form(foreign_ad, foreign_account),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    _assert_indistinguishable_refusal(response)
    db_session.expire_all()
    stored = (
        await db_session.execute(select(Schedule).where(Schedule.id == foreign_schedule))
    ).scalar_one()
    assert stored.times_of_day == ["09:00"]
