"""ADS-07 / ADS-08: полный цикл расписания внутри редактора объявления.

Этот файл — ГЕЙТ следующего плана. 02-06 несёт предусловие «`uv run pytest
tests/test_pages/test_editor_schedules.py -q` завершается с кодом 0» и обязан
остановиться, если файл красный или отсутствует: только зелёный новый путь даёт
02-06 право сносить `/schedules/new` и `/schedules/{id}/edit` (D-16, SC-3).

Две группы утверждений:

* **Возврат в редактор** — четыре страничных обработчика расписаний
  заканчивались редиректом на сводный список, и в редакторе это выкидывало бы
  пользователя со страницы после каждой правки (Pitfall 11). Признак
  происхождения приходит полем формы; адрес редиректа строит СЕРВЕР из
  идентификатора объявления уже проверенной на владение записи — подстановка
  значения поля как есть была бы открытым редиректом (T-02-23).
* **Неполнота и валидация** — неполное расписание сохраняется ВЫКЛЮЧЕННЫМ
  (D-08), а значения, не приводящиеся к своему типу, отбрасываются ДО разбора:
  прямой POST мимо браузера обязан давать отказ валидации, а не 500
  (T-02-24, T-02-25).
"""

from urllib.parse import urlencode

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User

FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


@pytest_asyncio.fixture
async def owner(db_session: AsyncSession) -> User:
    return (
        await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_ad(db: AsyncSession, user_id: int, title: str = "Объявление редактора") -> Ad:
    ad = Ad(
        user_id=user_id,
        title=title,
        text="Текст объявления",
        images=[],
        status=AD_STATUS_PUBLISHED,
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


async def _seed_account(db: AsyncSession, user_id: int, type_: str = "tg_user") -> MessengerAccount:
    account = MessengerAccount(
        user_id=user_id, type=type_, credentials="creds", status="active"
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def _seed_group(
    db: AsyncSession, user_id: int, account_id: int, name: str = "Группа расписания"
) -> Group:
    group = Group(
        user_id=user_id,
        account_id=account_id,
        messenger_type="tg_user",
        group_external_id=f"ext-{name}",
        name=name,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def _seed_schedule(
    db: AsyncSession,
    ad_id: int,
    account_id: int | None,
    group_ids: list[int] | None = None,
    days: list[int] | None = None,
    times: list[str] | None = None,
    is_active: bool = True,
) -> Schedule:
    schedule = Schedule(
        ad_id=ad_id,
        account_id=account_id,
        group_ids=group_ids if group_ids is not None else [],
        days_of_week=days if days is not None else [0],
        times_of_day=times if times is not None else ["09:00"],
        timezone="UTC",
        is_active=is_active,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


def _form(pairs: list[tuple[str, str]]) -> str:
    return urlencode(pairs)


# populate_existing, а не expire_all: сессия теста — ТА ЖЕ, что у обработчика
# (dependency_overrides), поэтому в карте идентичности уже лежит объект,
# созданный запросом. Без принудительного заполнения часть его атрибутов
# остаётся истёкшей, и первое же обращение к ним уходит в ленивую загрузку вне
# greenlet-контекста — тест падает MissingGreenlet вместо своего утверждения.
async def _reload(db: AsyncSession, schedule_id: int) -> Schedule:
    return (
        await db.execute(
            select(Schedule)
            .where(Schedule.id == schedule_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one()


async def _all_schedules(db: AsyncSession) -> list[Schedule]:
    return list(
        (
            await db.execute(
                select(Schedule)
                .order_by(Schedule.id)
                .execution_options(populate_existing=True)
            )
        )
        .scalars()
        .all()
    )


# --- Возврат в редактор -------------------------------------------------------


@pytest.mark.asyncio
async def test_create_from_editor_returns_to_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Создание расписания из редактора возвращает в редактор ЭТОГО объявления."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith(f"/ads/{ad.id}/edit"), location
    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert f"sched={created[0].id}" in location, location


@pytest.mark.asyncio
async def test_create_without_the_editor_marker_still_goes_to_the_summary_list(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Без признака происхождения поведение прежнее — редирект на сводный список.

    Парный тест к предыдущему: без него признак мог бы игнорироваться, и оба
    пути молча вели бы в редактор.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form([("ad_id", str(ad.id)), ("account_id", str(account.id))]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/schedules"


@pytest.mark.asyncio
async def test_update_from_editor_returns_to_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    response = await authed_client.post(
        f"/schedules/{schedule.id}/edit",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "1"),
                ("times_of_day", "18:30"),
                ("timezone", "UTC"),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith(f"/ads/{ad.id}/edit"), location
    assert f"sched={schedule.id}" in location, location


@pytest.mark.asyncio
async def test_toggle_from_editor_returns_to_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """SCH-05: маршрут переключения не меняется, меняется только место возврата."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id]
    )

    response = await authed_client.post(
        f"/schedules/{schedule.id}/toggle",
        content=_form([("return_to", "editor")]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].startswith(f"/ads/{ad.id}/edit")
    assert (await _reload(db_session, schedule.id)).is_active is False


@pytest.mark.asyncio
async def test_delete_from_editor_returns_to_the_editor_and_removes_the_schedule(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    response = await authed_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_form([("return_to", "editor")]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].startswith(f"/ads/{ad.id}/edit")
    assert await _all_schedules(db_session) == []


@pytest.mark.asyncio
async def test_return_value_never_reaches_the_redirect_verbatim(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """T-02-23: поле возврата — ПРИЗНАК происхождения, а не адрес.

    Значение подконтрольно отправителю. Подставленное в редирект как есть, оно
    даёт открытый редирект: страница входа увела бы пользователя на чужой домен
    сразу после успешной аутентификации.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("return_to", "https://evil.example/steal"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers["location"]
    assert "evil.example" not in location, location
    assert location.startswith("/"), location


# --- D-08: неполное расписание сохраняется выключенным -------------------------


@pytest.mark.asyncio
async def test_schedule_without_groups_is_saved_disabled(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "1"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].is_active is False
    assert created[0].next_run_at is None


@pytest.mark.asyncio
async def test_schedule_without_days_is_saved_disabled(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)

    await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("group_ids", str(group.id)),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].is_active is False
    assert created[0].next_run_at is None


@pytest.mark.asyncio
async def test_schedule_without_times_is_saved_disabled(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)

    await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("group_ids", str(group.id)),
                ("days_of_week", "3"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].is_active is False
    assert created[0].next_run_at is None


@pytest.mark.asyncio
async def test_schedule_without_account_is_saved_disabled(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Только что добавленная карточка не несёт аккаунта — и это законно.

    При нескольких аккаунтах ни один не выбран заранее, поэтому «+ РАСПИСАНИЕ»
    обязано создать расписание БЕЗ аккаунта. Отказ формы (422) на этом месте
    лишил бы пользователя единственного способа добавить расписание в редакторе.
    """
    ad = await _seed_ad(db_session, owner.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form([("ad_id", str(ad.id)), ("return_to", "editor")]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].account_id is None
    assert created[0].is_active is False
    assert created[0].next_run_at is None


@pytest.mark.asyncio
async def test_changing_the_account_clears_the_previously_chosen_groups(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Расписание не может нести группы другого аккаунта.

    Сервер и раньше молча отбрасывал группы, не принадлежащие выбранному
    аккаунту, — но оставлял расписание АКТИВНЫМ с нулём групп: планировщик
    выбирал бы его к отправке и ничего не отправлял (Pitfall 8).
    """
    ad = await _seed_ad(db_session, owner.id)
    first = await _seed_account(db_session, owner.id)
    second = await _seed_account(db_session, owner.id, type_="wa")
    group_of_first = await _seed_group(db_session, owner.id, first.id, "Группа первого")
    schedule = await _seed_schedule(
        db_session, ad.id, first.id, group_ids=[group_of_first.id]
    )

    response = await authed_client.post(
        f"/schedules/{schedule.id}/edit",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(second.id)),
                ("group_ids", str(group_of_first.id)),
                ("days_of_week", "1"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    stored = await _reload(db_session, schedule.id)
    assert stored.account_id == second.id
    assert stored.group_ids == []
    assert stored.is_active is False
    assert stored.next_run_at is None


@pytest.mark.asyncio
async def test_complete_schedule_is_saved_active_with_a_next_run(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Парный позитивный тест: без него выключение проходило бы всегда."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("group_ids", str(group.id)),
                ("days_of_week", "0"),
                ("days_of_week", "1"),
                ("days_of_week", "2"),
                ("days_of_week", "3"),
                ("days_of_week", "4"),
                ("days_of_week", "5"),
                ("days_of_week", "6"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].group_ids == [group.id]
    assert created[0].is_active is True
    assert created[0].next_run_at is not None


@pytest.mark.asyncio
async def test_incomplete_schedule_cannot_be_switched_on(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-08: тумблер неполного расписания не включает его.

    Тумблер размечен недоступным, но разметка — не точка принуждения: прямой
    POST на маршрут переключения обязан получить отказ так же, как и клик.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[], is_active=False
    )

    response = await authed_client.post(
        f"/schedules/{schedule.id}/toggle", follow_redirects=False
    )

    assert response.status_code == 302
    stored = await _reload(db_session, schedule.id)
    assert stored.is_active is False
    assert stored.next_run_at is None


# --- Валидация клиентских значений (Pitfall 9, D-13) ---------------------------


@pytest.mark.asyncio
async def test_malformed_time_does_not_crash_and_is_dropped(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """T-02-24: значение времени не формата ЧЧ:ММ роняло вычисление запуска.

    `int(parts[0])` бросает ValueError, `parts[1]` — IndexError. Через браузер
    сюда приходит `input type="time"`, но POST можно послать мимо браузера, и
    сегодня это давало 500 вместо отказа валидации.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("group_ids", str(group.id)),
                ("days_of_week", "1"),
                ("times_of_day", "не-время"),
                ("times_of_day", "25:00"),
                ("times_of_day", "10:61"),
                ("times_of_day", "10"),
                ("times_of_day", "09:30"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code < 500, response.status_code
    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].times_of_day == ["09:30"]


@pytest.mark.asyncio
async def test_non_numeric_group_and_day_values_do_not_crash(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """T-02-25: `int(g)` на списках идентификаторов падал на любой строке."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)

    response = await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("group_ids", "не-число"),
                ("group_ids", str(group.id)),
                ("days_of_week", "понедельник"),
                ("days_of_week", "2"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code < 500, response.status_code
    created = await _all_schedules(db_session)
    assert len(created) == 1
    assert created[0].group_ids == [group.id]
    assert created[0].days_of_week == [2]


@pytest.mark.asyncio
async def test_out_of_range_day_values_are_dropped(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """День недели вне 0..6 не отправится никогда — он не должен и храниться."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    await authed_client.post(
        "/schedules/new",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "9"),
                ("days_of_week", "-1"),
                ("days_of_week", "4"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    created = await _all_schedules(db_session)
    assert created[0].days_of_week == [4]


@pytest.mark.asyncio
async def test_malformed_time_on_update_does_not_crash(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Тот же отказ на маршруте изменения: обход одной ветки не помогает."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    response = await authed_client.post(
        f"/schedules/{schedule.id}/edit",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "1"),
                ("times_of_day", "24:00"),
                ("timezone", "UTC"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code < 500, response.status_code
    stored = await _reload(db_session, schedule.id)
    assert stored.times_of_day == []
    assert stored.is_active is False


# --- Старый путь не тронут ----------------------------------------------------


@pytest.mark.asyncio
async def test_summary_list_keeps_working(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Обращение НЕ из редактора обслуживается тем же способом, что и раньше."""
    ad = await _seed_ad(db_session, owner.id, title="Расписание сводного списка")
    account = await _seed_account(db_session, owner.id)
    await _seed_schedule(db_session, ad.id, account.id)

    response = await authed_client.get("/schedules")
    assert response.status_code == 200
    assert "Расписание сводного списка" in response.text

    legacy_form = await authed_client.get("/schedules/new")
    assert legacy_form.status_code == 200
