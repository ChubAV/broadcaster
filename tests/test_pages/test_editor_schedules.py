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

import re
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


# --- Секция расписаний в разметке редактора (Задача 3) ------------------------


FORM_OPEN_RE = re.compile(r"<form\b", re.I)
FORM_CLOSE_RE = re.compile(r"</form\s*>", re.I)


def _max_form_nesting(html: str) -> int:
    """Наибольшая глубина вложенности форм в разметке.

    Вложенную форму браузер молча ОТБРАСЫВАЕТ: симптом — неработающие кнопки на
    карточках расписаний, а не ошибка. Проверка идёт по отрендеренной выдаче, а
    не по файлу: форма могла бы приехать из макроса.
    """
    depth = 0
    peak = 0
    for match in re.finditer(r"<form\b|</form\s*>", html, re.I):
        if match.group(0).startswith("</"):
            depth = max(0, depth - 1)
        else:
            depth += 1
            peak = max(peak, depth)
    return peak


@pytest.mark.asyncio
async def test_editor_without_schedules_names_the_consequence(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Пустое состояние называет ПОСЛЕДСТВИЕ, а не только отсутствие."""
    ad = await _seed_ad(db_session, owner.id)
    await _seed_account(db_session, owner.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert "Расписаний пока нет — объявление не будет отправляться" in html
    assert "+ ДОБАВИТЬ ПЕРВОЕ" in html


@pytest.mark.asyncio
async def test_editor_card_renders_data(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Карточка-макрос отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    Импортированным макросам Jinja контекст вызывающего не передаёт: ошибка в
    имени параметра оставит страницу валидной, отдаст 200 и нарисует пустую
    карточку. Утверждение на статус ответа такую поломку не ловит.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id, "Уникальная группа карточки")
    schedule = await _seed_schedule(
        db_session,
        ad.id,
        account.id,
        group_ids=[group.id],
        days=[0, 2],
        times=["09:30", "18:45"],
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert f"Telegram #{account.id}" in html, "подпись аккаунта не отрисована"
    assert "09:30" in html and "18:45" in html, "времена не отрисованы"
    assert "Уникальная группа карточки" in html, "имя группы не отрисовано"
    assert f"/schedules/{schedule.id}/edit" in html
    assert f"/schedules/{schedule.id}/toggle" in html


@pytest.mark.asyncio
async def test_editor_markup_has_no_nested_forms(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Ни одна форма не открыта внутри другой — ни в одном состоянии секции."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id]
    )

    for url in (
        "/ads/new",
        f"/ads/{ad.id}/edit",
        f"/ads/{ad.id}/edit?sched={schedule.id}",
    ):
        html = (await authed_client.get(url)).text
        assert _max_form_nesting(html) == 1, f"{url}: в разметке есть вложенные формы"


@pytest.mark.asyncio
async def test_schedule_delete_is_a_real_form(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Деградация без Alpine: удаление остаётся настоящей формой с POST."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert re.search(
        rf'<form[^>]*method="post"[^>]*action="/schedules/{schedule.id}/delete"'
        rf'|<form[^>]*action="/schedules/{schedule.id}/delete"[^>]*method="post"',
        html,
    ), "путь удаления расписания перестал быть настоящей формой"
    assert "confirm(" not in html
    assert "onsubmit" not in html


@pytest.mark.asyncio
async def test_selected_schedule_is_the_expanded_one(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Параметр выбранного расписания разворачивает ИМЕННО эту карточку.

    Развёрнута одновременно одна: при многих расписаниях иначе получилась бы
    стена одновременно открытых форм.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    first = await _seed_schedule(db_session, ad.id, account.id)
    second = await _seed_schedule(db_session, ad.id, account.id, times=["21:00"])

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={second.id}")).text

    assert f'action="/schedules/{second.id}/edit"' in html, (
        "выбранная карточка не развёрнута: формы сохранения в разметке нет"
    )
    assert f'action="/schedules/{first.id}/edit"' not in html, (
        "невыбранная карточка тоже развёрнута"
    )

    collapsed = (await authed_client.get(f"/ads/{ad.id}/edit")).text
    assert f'action="/schedules/{first.id}/edit"' not in collapsed
    assert f'action="/schedules/{second.id}/edit"' not in collapsed


@pytest.mark.asyncio
async def test_user_without_accounts_is_offered_to_connect_one(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Ни одного аккаунта — подсказка со ссылкой в раздел, а не пустая полоса."""
    ad = await _seed_ad(db_session, owner.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert "Сначала подключите аккаунт мессенджера" in html
    assert "Без аккаунта расписание отправлять некуда" in html
    assert 'href="/accounts"' in html


@pytest.mark.asyncio
async def test_account_without_groups_says_so(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Аккаунт без групп — названная причина, а не пустой блок."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "У выбранного аккаунта нет подключённых групп" in html
    # Тумблер неполного расписания недоступен (D-08)
    assert "disabled" in html.split(f"/schedules/{schedule.id}/toggle")[1][:400]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "count,expected",
    [(1, "1 расписание"), (3, "3 расписания"), (5, "5 расписаний")],
)
async def test_section_caption_is_declined(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
    count: int,
    expected: str,
):
    """«1 расписаний» — заметный дефект копирайтинга; подпись СКЛОНЯЕТСЯ."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    for _ in range(count):
        await _seed_schedule(db_session, ad.id, account.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert expected in html, f"подпись секции не склонена для {count}"


@pytest.mark.asyncio
async def test_add_schedule_form_preselects_a_single_account(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Единственный аккаунт выбран заранее; при нескольких — ни один.

    Заставлять выбирать из одного варианта — лишний шаг; выбирать за
    пользователя из нескольких — решать за него, куда уйдёт рассылка.
    """
    ad = await _seed_ad(db_session, owner.id)
    only = await _seed_account(db_session, owner.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text
    add_form = html[html.index('action="/schedules/new"'):]
    add_form = add_form[: add_form.index("</form>")]
    assert f'name="account_id" value="{only.id}"' in add_form

    await _seed_account(db_session, owner.id, type_="wa")
    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text
    add_form = html[html.index('action="/schedules/new"'):]
    add_form = add_form[: add_form.index("</form>")]
    assert 'name="account_id"' not in add_form


@pytest.mark.asyncio
async def test_editor_schedule_section_is_a_sibling_of_the_ad_form(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Секция расписаний стоит ПОСЛЕ закрытия формы объявления.

    Проверка позиционная, а не «нет вложенных форм»: последнее верно и тогда,
    когда секция уехала выше формы и потеряла свой порядок чтения на узкой
    ширине (D-14, порядок разметки — порядок чтения).
    """
    ad = await _seed_ad(db_session, owner.id)
    await _seed_account(db_session, owner.id)

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    ad_form_close = html.index("</form>", html.index('id="ad-form"'))
    section = html.index('action="/schedules/new"')
    assert ad_form_close < section, "секция расписаний оказалась внутри формы объявления"


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

    # Отдельной страницы создания расписания больше НЕТ (D-14, план 02-06).
    # До 02-06 здесь стояло `== 200` — утверждение о сосуществовании двух путей,
    # верное ровно между планами 02-05 и 02-06. Теперь утверждение обратное и не
    # менее строгое: страница снесена, мёртвого кода не осталось.
    #
    # Код именно 405, а не 404: `POST /schedules/new` остаётся — на него ходит
    # форма добавления из редактора, — поэтому путь в приложении существует, а
    # метод GET на нём больше не обслуживается.
    legacy_form = await authed_client.get("/schedules/new")
    assert legacy_form.status_code == 405
