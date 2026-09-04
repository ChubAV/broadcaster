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
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AD_STATUS_PUBLISHED
from app.pages.common import templates
from app.pages.schedules import ID_MAX
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
    db: AsyncSession,
    user_id: int,
    account_id: int,
    name: str = "Группа расписания",
    is_active: bool = True,
) -> Group:
    group = Group(
        user_id=user_id,
        account_id=account_id,
        messenger_type="tg_user",
        group_external_id=f"ext-{name}",
        name=name,
        is_active=is_active,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def _stranger(db: AsyncSession) -> User:
    """Второй пользователь — владелец «чужой» группы.

    Форма посева взята из tests/test_pages/test_ads_editor.py: чужая запись
    обязана принадлежать НАСТОЯЩЕМУ пользователю, иначе отсутствие группы в
    выдаче объяснялось бы отсутствием владельца, а не скоупом выборки.
    """
    user = User(email="stranger@test.com", password_hash="x", name="Stranger")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


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


def _hidden_fields_of_the_toggle_form(html: str, schedule_id: int) -> list[tuple[str, str]]:
    """Скрытые поля формы тумблера ИМЕННО этой карточки — из отрендеренной разметки.

    Поля берутся со страницы, а не собираются в тесте руками: собранный вручную
    набор прошёл бы и при разметке, которая этих полей не рисует, и связка
    «шаблон ↔ обработчик» осталась бы непроверенной.
    """
    block = re.search(
        rf'<form[^>]*action="/schedules/{schedule_id}/toggle"[^>]*>(.*?)</form>',
        html,
        re.DOTALL,
    )
    assert block, f"формы тумблера расписания {schedule_id} в разметке нет"
    return [
        (m.group("name"), m.group("value"))
        for m in re.finditer(
            r'<input[^>]*type="hidden"[^>]*name="(?P<name>[^"]+)"[^>]*value="(?P<value>[^"]*)"',
            block.group(1),
        )
    ]


@pytest.mark.asyncio
async def test_the_toggle_does_not_fold_or_unfold_the_schedule_card(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Тумблер меняет состояние расписания и НЕ трогает разворот карточек.

    Разворот — состояние СЕРВЕРНОЕ: его определяет единственный параметр адреса
    `sched`, и обработчик переключения перезаписывал его идентификатором нажатой
    карточки. Пользователь читал это как «тумблер нажал кнопку СВЕРНУТЬ /
    РАЗВЕРНУТЬ»: свёрнутая карточка от нажатия разворачивалась, а развёрнутая
    соседка схлопывалась.

    Тест сквозной — он проходит путь пользователя целиком: страница, форма из
    её разметки, POST, переход по адресу ответа. Утверждение про `is_active`
    обязательно: без него тест остался бы зелёным и при тумблере, переставшем
    работать вовсе.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)
    first = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id]
    )
    second = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id], times=["21:00"]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={second.id}")).text
    fields = _hidden_fields_of_the_toggle_form(html, first.id)

    response = await authed_client.post(
        f"/schedules/{first.id}/toggle",
        content=_form(fields),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )
    assert response.status_code == 302

    after = (await authed_client.get(response.headers["location"])).text
    assert f'action="/schedules/{first.id}/edit"' not in after, (
        "свёрнутая карточка РАЗВЕРНУЛАСЬ от нажатия собственного тумблера"
    )
    assert f'action="/schedules/{second.id}/edit"' in after, (
        "развёрнутая карточка СХЛОПНУЛАСЬ от нажатия тумблера соседней"
    )
    assert (await _reload(db_session, first.id)).is_active is False, (
        "тумблер перестал переключать расписание"
    )


@pytest.mark.asyncio
async def test_a_toggle_without_the_expansion_field_leaves_every_card_collapsed(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Нечего разворачивать — значит, после нажатия развёрнутых карточек нет.

    Форма браузера в этом состоянии именно такова: развёрнутых карточек не было,
    поле разворота не отрисовано. Адрес возврата обязан быть чистым — иначе
    тумблер РАЗВОРАЧИВАЛ БЫ свёрнутую карточку, что пользователь и сообщил.
    """
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
    assert response.headers["location"] == f"/ads/{ad.id}/edit", (
        "тумблер развернул карточку, которая была свёрнута"
    )
    assert (await _reload(db_session, schedule.id)).is_active is False


@pytest.mark.asyncio
async def test_a_malformed_expansion_field_is_dropped_instead_of_crashing(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Испорченное поле разворота отбрасывается, а переключение доводится до конца.

    Разметка — не точка принуждения: POST мимо браузера обязан получить тот же
    ответ, что и форма. Значение разворота — единственная величина, приходящая
    из формы в строку адреса, и непреобразуемое к целому в неё не попадает
    (T-mwo-01).
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    group = await _seed_group(db_session, owner.id, account.id)
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[group.id]
    )

    response = await authed_client.post(
        f"/schedules/{schedule.id}/toggle",
        content=_form(
            [("return_to", "editor"), ("keep_sched", "1&sched=99#hack")]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302, "мусор в поле разворота уронил обработчик"
    assert response.headers["location"] == f"/ads/{ad.id}/edit"
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
async def test_the_collapsed_cards_toggle_carries_the_expanded_card_id(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Тумблер СВЁРНУТОЙ карточки несёт ЧУЖОЙ идентификатор — развёрнутой.

    Утверждение о СВЯЗКЕ шаблона и обработчика: без него оба могли бы пройти
    свои проверки по отдельности при неработающей странице — обработчик читал бы
    поле, которого разметка не рисует.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    first = await _seed_schedule(db_session, ad.id, account.id)
    second = await _seed_schedule(db_session, ad.id, account.id, times=["21:00"])

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={second.id}")).text

    assert ("keep_sched", str(second.id)) in _hidden_fields_of_the_toggle_form(
        html, first.id
    ), "свёрнутая карточка не проносит через тумблер идентификатор развёрнутой"


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
    # Выключенное: недоступен тумблер именно на ВОЗОБНОВЛЕНИИ неполного (D-08),
    # а паузу активного не блокируют ни сервер, ни соседний шаблон.
    schedule = await _seed_schedule(db_session, ad.id, account.id, is_active=False)

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "У выбранного аккаунта нет подключённых групп" in html
    # Тумблер неполного ВЫКЛЮЧЕННОГО расписания недоступен (D-08)
    assert "disabled" in html.split(f"/schedules/{schedule.id}/toggle")[1][:400]


@pytest.mark.asyncio
async def test_active_incomplete_schedule_can_still_be_paused_from_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Пауза АКТИВНОГО не зависит от заполненности — тумблер доступен.

    Определение недоступности в карточке разъехалось с двумя другими носителями
    того же правила: `schedules/includes/schedule_row.html` и обработчик
    `app/pages/schedules.py` считают блокируемым только ВОЗОБНОВЛЕНИЕ
    неполного. Карточка отключала орган управления и в состоянии «активное И
    неполное», подпись при этом врала («Включить нельзя», когда пользователь
    хочет ВЫКЛЮЧИТЬ), а выключенный флажок браузер не отправляет и события
    `change` не порождает — пути поставить расписание на паузу из редактора не
    было вовсе.

    Состояние не теоретическое: удаление единственной группы вычищает
    идентификатор из `Schedule.group_ids`, не трогая `is_active`.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[], is_active=True
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    toggle_markup = html.split(f"/schedules/{schedule.id}/toggle")[1][:400]
    assert "disabled" not in toggle_markup, (
        "активное неполное расписание нельзя поставить на паузу из редактора"
    )
    assert "Приостановить" in toggle_markup, (
        "подпись обязана называть действие, которое пользователь может сделать"
    )


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


# --- D-07: выключенные группы в списке выбора редактора ------------------------
#
# С D-05 выключенная группа перестаёт получать рассылку. Выборка редактора брала
# только активные группы, и выбранная-но-выключенная группа ИСЧЕЗАЛА из карточки:
# пользователь не мог ни узнать, почему группа молчит, ни снять её выбор, а
# подпись «выбрано N из M» начинала врать (RESEARCH Pitfall 6).
#
# Правило ровно одно и о двух половинах: выключенная группа видна ТОЛЬКО если она
# уже выбрана в расписании ЭТОГО объявления; невыбранные выключенные список не
# захламляют.

# Строка списка выбора целиком: разбор строкой — тот же приём, что уже применяют
# этот файл и tests/test_pages/test_responsive_markup.py. Отдельной зависимости
# разбора HTML ради четырёх утверждений не заводится.
GROUP_ROW_RE = re.compile(r'<label class="group-pick__row".*?</label>', re.S)
GROUP_COUNTER_RE = re.compile(r"выбрано (\d+) из (\d+)")
OFF_MARK = "отключена"
# ВИДИМАЯ подпись, а не любое вхождение слова: то же слово стоит внутри
# пояснения («Группа отключена и пропускается при рассылке»), и счёт по голой
# подстроке мерил бы два вхождения на одну пометку.
OFF_MARK_CAPTION = ">отключена<"


def _group_rows(html: str) -> list[str]:
    return GROUP_ROW_RE.findall(html)


def _row_of(html: str, group_id: int) -> str:
    """Строка выбора конкретной группы. Отсутствие — падение, а не пустая строка."""
    for row in _group_rows(html):
        if f'value="{group_id}"' in row:
            return row
    raise AssertionError(f"строки группы {group_id} в списке выбора нет")


@pytest.mark.asyncio
async def test_disabled_group_chosen_in_the_schedule_stays_visible(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Выключенная группа, уже выбранная в расписании, из карточки не исчезает."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    off = await _seed_group(
        db_session, owner.id, account.id, "Выключенная выбранная группа", is_active=False
    )
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[off.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "Выключенная выбранная группа" in html, (
        "выбранная выключенная группа пропала из списка выбора"
    )
    assert "checked" in _row_of(html, off.id), "выбор с группы снялся сам"


@pytest.mark.asyncio
async def test_disabled_group_not_chosen_is_absent_from_the_picker(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Невыбранная выключенная группа список выбора не захламляет.

    Парный тест к предыдущему: без него выборка могла бы отдавать ВСЕ группы
    подряд и оба утверждения о видимости проходили бы разом.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    active = await _seed_group(db_session, owner.id, account.id, "Активная группа списка")
    await _seed_group(
        db_session, owner.id, account.id, "Выключенная невыбранная группа", is_active=False
    )
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[active.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "Активная группа списка" in html
    assert "Выключенная невыбранная группа" not in html, (
        "невыбранная выключенная группа попала в список выбора"
    )


@pytest.mark.asyncio
async def test_active_group_is_present_regardless_of_schedules(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Активная группа видна и тогда, когда ни в одном расписании не выбрана."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    active = await _seed_group(db_session, owner.id, account.id, "Активная невыбранная")
    schedule = await _seed_schedule(db_session, ad.id, account.id, group_ids=[])

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "Активная невыбранная" in html
    assert "checked" not in _row_of(html, active.id)


@pytest.mark.asyncio
async def test_disabled_group_chosen_in_another_ad_is_absent_here(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Множество выбранных строится из расписаний ИМЕННО ЭТОГО объявления.

    Иначе выключенная группа, выбранная где-то в другом объявлении, всплывала бы
    в списке выбора всех объявлений сразу.
    """
    ad = await _seed_ad(db_session, owner.id)
    other_ad = await _seed_ad(db_session, owner.id, title="Второе объявление")
    account = await _seed_account(db_session, owner.id)
    off = await _seed_group(
        db_session, owner.id, account.id, "Выключенная чужого объявления", is_active=False
    )
    await _seed_schedule(db_session, other_ad.id, account.id, group_ids=[off.id])
    schedule = await _seed_schedule(db_session, ad.id, account.id, group_ids=[])

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "Выключенная чужого объявления" not in html


@pytest.mark.asyncio
async def test_group_of_another_user_never_reaches_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """T-03-11: расширение выборки на выключенные не снимает скоуп по владельцу.

    Идентификатор чужой группы подставлен в СВОЁ расписание — то есть клиентское
    значение прошло весь путь до множества выбранных. Выборка обязана остаться
    ограниченной владельцем: чужое имя в карточку не попадает.
    """
    stranger = await _stranger(db_session)
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    foreign = await _seed_group(
        db_session, stranger.id, account.id, "Группа постороннего", is_active=False
    )
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[foreign.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "Группа постороннего" not in html, "чужая группа попала в список выбора"


@pytest.mark.asyncio
async def test_editor_without_disabled_selections_renders_the_same_group_set(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Обычный случай — нулевой диф: набор строк ровно тот же, что и до правки."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    first = await _seed_group(db_session, owner.id, account.id, "Первая активная")
    second = await _seed_group(db_session, owner.id, account.id, "Вторая активная")
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[first.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    rows = _group_rows(html)
    assert len(rows) == 2, "набор строк списка выбора изменился в обычном случае"
    assert "Первая активная" in html and "Вторая активная" in html
    assert OFF_MARK not in html, "пометка появилась там, где выключенных групп нет"
    assert "checked" in _row_of(html, first.id)
    assert "checked" not in _row_of(html, second.id)


# --- D-07: пометка «отключена» и согласованный счётчик -------------------------


@pytest.mark.asyncio
async def test_disabled_chosen_row_is_marked_as_off(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Пользователь видит ПРИЧИНУ молчания группы прямо в строке выбора.

    Без пометки выключенная группа выглядит в карточке ровно как работающая, и
    единственным наблюдаемым следствием D-05 остаётся отсутствие отправок.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    off = await _seed_group(
        db_session, owner.id, account.id, "Помеченная выключенная", is_active=False
    )
    active = await _seed_group(db_session, owner.id, account.id, "Обычная активная")
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[off.id, active.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    off_row = _row_of(html, off.id)
    assert off_row.count(OFF_MARK_CAPTION) == 1, "пометки нет или она задвоена"
    assert "Группа отключена и пропускается при рассылке" in off_row, (
        "у пометки нет пояснения"
    )
    assert OFF_MARK not in _row_of(html, active.id), (
        "активная группа помечена отключённой"
    )


@pytest.mark.asyncio
async def test_disabled_chosen_checkbox_stays_operable(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Снять выбор с выключенной группы обязано быть возможно.

    Недоступный флажок запер бы группу в расписании навсегда: убрать её было бы
    нечем, а отправок она уже не получает.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    off = await _seed_group(
        db_session, owner.id, account.id, "Выключенная снимаемая", is_active=False
    )
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[off.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    off_row = _row_of(html, off.id)
    assert "checked" in off_row
    assert "disabled" not in off_row, "флажок выключенной группы стал недоступен"

    # Разметка — не точка принуждения: снятие обязано доехать до хранилища.
    await authed_client.post(
        f"/schedules/{schedule.id}/edit",
        content=_form(
            [
                ("ad_id", str(ad.id)),
                ("account_id", str(account.id)),
                ("days_of_week", "1"),
                ("times_of_day", "09:00"),
                ("timezone", "UTC"),
                ("return_to", "editor"),
            ]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert (await _reload(db_session, schedule.id)).group_ids == []


@pytest.mark.asyncio
async def test_group_counter_agrees_with_the_rendered_rows(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """«выбрано N из M» считает ВИДИМЫЙ набор, а не хранимый список.

    Пока выключенные-выбранные группы выпадали из выборки, знаменатель считал
    одно, а числитель — другое, и подпись противоречила списку перед глазами
    (RESEARCH Pitfall 6).
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    off = await _seed_group(
        db_session, owner.id, account.id, "Счётная выключенная", is_active=False
    )
    chosen_active = await _seed_group(
        db_session, owner.id, account.id, "Счётная выбранная"
    )
    await _seed_group(db_session, owner.id, account.id, "Счётная невыбранная")
    schedule = await _seed_schedule(
        db_session, ad.id, account.id, group_ids=[off.id, chosen_active.id]
    )

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    rows = _group_rows(html)
    counter = GROUP_COUNTER_RE.search(html)
    assert counter is not None, "подписи «выбрано N из M» в карточке нет"
    chosen_shown = int(counter.group(1))
    total_shown = int(counter.group(2))

    assert total_shown == len(rows) == 3, "знаменатель разошёлся с видимым списком"
    assert chosen_shown == sum("checked" in row for row in rows) == 2, (
        "числитель разошёлся с отмеченными строками"
    )


# --- Фаза 10, план 10-01: единственный ФРАГМЕНТНЫЙ путь фазы ------------------
#
# ПОЧЕМУ ЭТОТ МАРШРУТ И ТОЛЬКО ОН (D-09). Из восьми обработчиков за панелями
# подтверждения фрагментом отвечает РОВНО ОДИН — удаление расписания из
# редактора объявления. Прокрутки в редакторе нет, `id="sched-{id}"` карточки и
# ключ панели `sched-del-{id}` собраны из ПЕРВИЧНОГО КЛЮЧА, а не из позиции
# строки, — сдвигаться нечему. Семь остальных уходят в ветку `HX-Location`, и
# основание у каждого измерено, а не предположено (D-06, D-08).
#
# ⚠️ ПАРА «БЕЗ ЗАГОЛОВКА → 302 / С ЗАГОЛОВКОМ → ФРАГМЕНТ» — НЕСУЩАЯ ФОРМА, А НЕ
# ДУБЛИРОВАНИЕ. Вторая половина утверждает ОТСУТСТВИЕ ДОКУМЕНТА в теле
# (`"<!DOCTYPE" not in response.text`): фикстура `htmx_client` идёт
# `follow_redirects=True`, поэтому обработчик, забывший путь письма и ответивший
# редиректом, приехал бы к тесту кодом 200 и телом ЧУЖОЙ СТРАНИЦЫ — и без этой
# половины тест позеленел бы на нём (GATE-01, D-16 Фазы 8).


def _editor_delete_body(ad: Ad) -> str:
    """Тело, которое шлют ОБЕ формы пути удаления расписания из редактора.

    ⚠️ СОБИРАЕТСЯ ЗДЕСЬ ОДИН РАЗ И НАМЕРЕННО: тест, пославший НЕ ТО, что шлёт
    разметка, проверяет маршрут, которым не идёт ни один пользователь. Оба поля
    — признак возврата и контекст экрана — стоят в обеих формах карточки
    расписания (`ads/includes/sched_card.html`); равенство наборов держит
    правило `test_both_editor_delete_forms_post_the_same_field_names`.
    """
    return _form([("return_to", "editor"), ("ad_id", str(ad.id))])


def _oob_top_level_tags(body: str) -> list[str]:
    """Открывающие теги ВЕРХНЕГО УРОВНЯ тела фрагментного ответа.

    Разбор нарочно грубый — по началу строки: тело фрагментного ответа обязано
    быть плоским (`allowNestedOobSwaps: false` в блоке конфигурации), и
    разборщик, умеющий во вложенность, скрыл бы ровно тот отказ, ради которого
    правило существует.
    """
    return [
        line for line in body.splitlines() if line.startswith("<") and "id=" in line
    ]


@pytest.mark.asyncio
async def test_editor_delete_degrades_without_htmx(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Путь деградации не тронут: без заголовка htmx — прежний 302 на прежний адрес.

    Перевод обработчика на слой ответа обязан оставить человека без JavaScript
    ровно там, где он был: подтверждение остаётся настоящей формой POST, а ответ
    — перенаправлением в редактор объявления.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)
    await _seed_schedule(db_session, ad.id, account.id)

    response = await authed_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == f"/ads/{ad.id}/edit"


@pytest.mark.asyncio
async def test_editor_delete_returns_oob_nodes(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Ответ htmx-пути — ФРАГМЕНТ из трёх внеполосных узлов, а не документ."""
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)
    await _seed_schedule(db_session, ad.id, account.id)

    response = await htmx_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 200
    assert "<!DOCTYPE" not in response.text, (
        "обработчик ответил документом — значит слой письма его не увидел и "
        "фикстура прошла по редиректу"
    )
    body = response.text
    assert f'id="sched-{schedule.id}"' in body, "узла снятия карточки в ответе нет"
    assert f'id="sched-del-{schedule.id}"' in body, "узла снятия панели в ответе нет"
    assert 'hx-swap-oob="innerHTML:#sched-count"' in body, (
        "линейка счётчика не приезжает подменой СОДЕРЖИМОГО долгоживущей области"
    )
    removals = body.count('hx-swap-oob="delete"')
    assert removals == 2, (
        f"узлов снятия в ответе {removals}, ожидалось два (карточка и "
        f"осиротевшая панель): {body!r}"
    )


@pytest.mark.asyncio
async def test_the_orphaned_panel_is_removed_by_its_own_oob_node(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Панель снимает СОБСТВЕННЫЙ узел, а не узел карточки (критерий 2 фазы).

    Панель подтверждения сознательно стоит СНАРУЖИ удаляемой карточки (T-11-04):
    внутри неё она стала бы её блоком и после первой же подмены задвоилась бы.
    Снаружи она вместе с карточкой и НЕ УЕЗЖАЕТ — без отдельного узла снятия
    после N удалений в документе копятся N узлов `role="dialog"`, каждый с живой
    ловушкой фокуса и живым обработчиком Escape, и признака отказа нет ни
    одного: ни в консоли, ни в статусе, ни в теле.

    Правило существует потому, что критерий 2 фазы — про ВТОРОЙ УЗЕЛ, а не про
    факт наличия ответа: тест на присутствие тела зеленел бы и без него.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)
    await _seed_schedule(db_session, ad.id, account.id)

    response = await htmx_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
    )

    tags = _oob_top_level_tags(response.text)
    card = [tag for tag in tags if f'id="sched-{schedule.id}"' in tag]
    panel = [tag for tag in tags if f'id="sched-del-{schedule.id}"' in tag]

    assert len(card) == 1, f"узел снятия карточки не один: {card}"
    assert len(panel) == 1, f"узел снятия панели не один: {panel}"
    assert card[0] != panel[0], (
        "снятие карточки и снятие панели оказались одним узлом — осиротевшая "
        "панель осталась бы в документе"
    )
    for tag in (card[0], panel[0]):
        assert 'hx-swap-oob="delete"' in tag, (
            f"узел верхнего уровня не несёт признака снятия: {tag!r}"
        )


@pytest.mark.asyncio
async def test_the_last_schedule_goes_to_location(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Опустевший редактор закрывается ПЕРЕХОДОМ, а не второй отрисовкой (D-04).

    Второго экземпляра пустого состояния во фрагменте не заводится: ветка
    «расписаний пока нет» живёт в `ads/form.html` в ОДНОМ экземпляре, и второй
    её отрисовкой она разошлась бы с первой молча.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)

    response = await htmx_client.post(
        f"/schedules/{schedule.id}/delete",
        content=_editor_delete_body(ad),
        headers=FORM_HEADERS,
    )

    assert response.status_code == 204
    assert response.headers["HX-Location"] == f"/ads/{ad.id}/edit"
    assert response.text == "", "у ответа 204 тела нет по определению"
    assert await _all_schedules(db_session) == []


@pytest.mark.asyncio
async def test_repeated_editor_delete_is_harmless(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Повтор БЕЗВРЕДЕН и НЕОТЛИЧИМ — и это два разных утверждения.

    Безвредность: единица записи — ОДИН commit одной строки под `WHERE` со
    связью `Ad.user_id`; второй запрос второй записи не создаёт и не удаляет
    ничего сверх.
    ⚠️ `hx-disabled-elt` СЕРВЕРНОЙ ЗАЩИТОЙ НЕ ЯВЛЯЕТСЯ и таковой здесь не
    объявляется: он блокирует кнопку в документе, а не маршрут на сервере. Два
    одновременных подтверждения дают одно удаление и один безвредный холостой
    путь, а не две записи.

    Неотличимость: тело собирается из `schedule_id` ПУТИ, а не из найденной
    строки, и ветви по факту удаления в шаблоне ответа нет. Иначе НАЛИЧИЕ узла
    стало бы признаком того, что удаление состоялось, и карту чужих
    идентификаторов можно было бы составить перебором.

    ⚠️ ЦЕНА НЕОТЛИЧИМОСТИ НАЗЫВАЕТСЯ ЧИСЛОМ, А НЕ СЛОВОМ «МОЛЧА»: холостой путь
    шлёт ДВА узла, чьих целей в документе нет, то есть ДВЕ строки
    `htmx:oobErrorNoTarget` в консоли на запрос (измерено Фазой 9 по
    вендоренному рантайму 2.0.10). Признак «200 и чистая консоль» на этом пути
    теряется; остаток наследуется перечнем `OOB_TARGET_EXCEPTIONS` с назначенной
    Фазой 15.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    schedule = await _seed_schedule(db_session, ad.id, account.id)
    survivor = await _seed_schedule(db_session, ad.id, account.id)

    body = _editor_delete_body(ad)
    first = await htmx_client.post(
        f"/schedules/{schedule.id}/delete", content=body, headers=FORM_HEADERS
    )
    after_first = await _all_schedules(db_session)

    second = await htmx_client.post(
        f"/schedules/{schedule.id}/delete", content=body, headers=FORM_HEADERS
    )
    after_second = await _all_schedules(db_session)

    assert second.status_code == first.status_code
    assert second.text == first.text, (
        "повторный ответ отличим от первого — по нему видно, состоялось ли "
        "удаление, и чужие идентификаторы перебираются по этому различию"
    )
    assert [s.id for s in after_first] == [survivor.id]
    assert [s.id for s in after_second] == [survivor.id], (
        "повтор тронул строки: единица записи перестала быть одним commit-ом"
    )


@pytest.mark.asyncio
async def test_editor_delete_does_not_trust_the_schedule_of_another_owner(
    authed_client: AsyncClient,
    htmx_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Чужое расписание НЕ удаляется, и ответ на него неотличим от несуществующего.

    Неотличимость проверяется СРАВНЕНИЕМ ДВУХ ОТВЕТОВ, а не глазами: чужой
    идентификатор и заведомо несуществующий обязаны давать один и тот же ответ,
    иначе перебор по адресу составил бы карту занятых идентификаторов, не
    получив ни одной строки (T-10-01, T-10-07).
    """
    stranger = await _stranger(db_session)
    foreign_ad = await _seed_ad(db_session, stranger.id, "Чужое объявление")
    foreign_account = await _seed_account(db_session, stranger.id)
    foreign = await _seed_schedule(db_session, foreign_ad.id, foreign_account.id)

    body = _form([("return_to", "editor")])
    on_foreign = await htmx_client.post(
        f"/schedules/{foreign.id}/delete", content=body, headers=FORM_HEADERS
    )
    on_missing = await htmx_client.post(
        "/schedules/98765/delete", content=body, headers=FORM_HEADERS
    )

    assert [s.id for s in await _all_schedules(db_session)] == [foreign.id], (
        "чужая строка расписания удалена — тройной скоуп выборки перестал "
        "ограничивать её владельцем"
    )
    assert on_foreign.status_code == on_missing.status_code
    assert on_foreign.text == on_missing.text
    assert on_foreign.headers.get("HX-Location") == on_missing.headers.get(
        "HX-Location"
    ), "чужой идентификатор отличим от несуществующего по адресу приземления"


# --- Фаза 10, план 10-01, задача 3: ветка деградации и неотличимость ----------
#
# ⚠️ ПРАВИЛА НИЖЕ УТВЕРЖДАЮТ ПОВЕДЕНИЕ, А НЕ ВХОЖДЕНИЕ СТРОКИ, и это следствие
# измерения, а не вкуса. Ревизия Фазы 9 нашла ДВА расхождения (DIV-09-01 и
# DIV-09-02) ровно там, где машинные правила были зелены: разметочное правило
# зеленеет на присутствии подстроки, которую соседний путь не исполняет.

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"
SCHED_CARD_TEMPLATE = "ads/includes/sched_card.html"
SCHED_DELETE_RESPONSE_TEMPLATE = "ads/partials/sched_delete_response.html"

HIDDEN_FIELD_RE = re.compile(
    r'<input[^>]*type="hidden"[^>]*name="([^"]+)"', re.S
)
FORM_TAG_RE = re.compile(r"<form\b[^>]*>", re.S)

# Число форм-ТРИГГЕРОВ подтверждения в дереве. Значение поставлено ПРОГОНОМ, а не
# выведено: обход `x-on:submit.prevent` по всем шаблонам дал 18 — ровно столько
# же, сколько мест подтверждения насчитывает инвентарь панели (`MODAL_PLACES`).
#
# ⚠️ КОНСТАНТА ЗАВЕДЕНА ПРОТИВ ВАКУУМА, А НЕ ДЛЯ ОТЧЁТНОСТИ. Правило ниже
# утверждает ОТСУТСТВИЕ признака отправки на этих формах; разборщик, вернувший
# пустое множество, дал бы зелёный цвет, посимвольно совпадающий с зелёным
# цветом соблюдённого правила.
TRIGGER_FORMS_DECLARED = 18


def _template_text(rel: str) -> str:
    return (TEMPLATES_DIR / rel).read_text(encoding="utf-8")


def _all_template_sources() -> list[tuple[str, str]]:
    return [
        (path.relative_to(TEMPLATES_DIR).as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(TEMPLATES_DIR.rglob("*.html"))
    ]


def _delete_trigger_form(source: str) -> str:
    """Форма-ТРИГГЕР удаления расписания целиком — от открывающего тега до конца."""
    start = source.index('<form method="post" action="/schedules/{{ s.id }}/delete"')
    return source[start : source.index("</form>", start)]


def _delete_panel_slot(source: str) -> str:
    """Слот скрытых полей БЛОЧНОГО вызова панели подтверждения удаления."""
    start = source.index("{% call modal(id='sched-del-")
    return source[start : source.index("{% endcall %}", start)]


@pytest.mark.asyncio
async def test_both_editor_delete_forms_post_the_same_field_names():
    """Обе формы пути удаления шлют ОДИН И ТОТ ЖЕ набор имён полей.

    Правило существует потому, что ровно этот разъезд Фаза 9 поймала
    расхождением WR-03: поле несла только форма панели, и путь БЕЗ Alpine
    приезжал на сервер без него — обработчик считал ветку по другому состоянию,
    чем видел перед собой человек. Отказ обязан называть разошедшиеся имена, а
    не только факт расхождения: «наборы не равны» не говорит, какой путь чего
    лишился.
    """
    source = _template_text(SCHED_CARD_TEMPLATE)
    trigger = set(HIDDEN_FIELD_RE.findall(_delete_trigger_form(source)))
    panel = set(HIDDEN_FIELD_RE.findall(_delete_panel_slot(source)))

    assert trigger, "в форме-триггере удаления не нашлось ни одного скрытого поля"
    assert panel, "в слоте панели подтверждения не нашлось ни одного скрытого поля"
    assert trigger == panel, (
        "наборы полей двух форм пути удаления разошлись — путь деградации "
        "приедет на сервер с другим состоянием, чем путь htmx: "
        f"только в триггере {sorted(trigger - panel)}; "
        f"только в панели {sorted(panel - trigger)}"
    )


def test_the_trigger_form_never_carries_the_htmx_post():
    """Ни одна форма-ТРИГГЕР в дереве не несёт признака отправки htmx (D-03).

    Все места диспетчеризации остаются ЧИСТЫМ путём деградации: без Alpine форма
    уходит обычным POST-ом, с Alpine — открывает панель. Признак отправки живёт
    ТОЛЬКО на форме панели подтверждения, и это граница, а не полумера: триггер,
    получивший его, слал бы запрос ВМЕСТО открытия панели — то есть выполнял бы
    необратимое действие без подтверждения.
    """
    triggers: list[tuple[str, str]] = []
    for rel, source in _all_template_sources():
        for tag in FORM_TAG_RE.findall(source):
            if "x-on:submit.prevent" in tag:
                triggers.append((rel, tag))

    assert len(triggers) == TRIGGER_FORMS_DECLARED, (
        f"форм-триггеров подтверждения найдено {len(triggers)}, объявлено "
        f"{TRIGGER_FORMS_DECLARED} — место диспетчеризации молча исчезло или "
        f"появилось незаявленное: {sorted(rel for rel, _ in triggers)}"
    )

    carrying = [(rel, tag) for rel, tag in triggers if "hx-post" in tag]
    assert not carrying, (
        "форма-триггер несёт признак отправки htmx — подтверждённое действие "
        "ушло бы на сервер ВМЕСТО открытия панели подтверждения: "
        + "; ".join(f"{rel} -> {tag!r}" for rel, tag in carrying)
    )


@pytest.mark.asyncio
async def test_the_editor_delete_address_is_the_same_on_both_transports(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
):
    """Адрес приземления ПОСИМВОЛЬНО один и тот же на обоих транспортах.

    Он же уезжает перенаправлением человеку без JavaScript, он же — заголовком
    перехода. Два независимо собранных адреса разошлись бы МОЛЧА, и путь
    деградации уводил бы на сводный список там, где путь htmx остаётся в
    редакторе. Тело формы в обоих запросах одно — иначе сравнивались бы два
    разных вопроса.

    ⚠️ ФИКСТУРА `htmx_client` ЗДЕСЬ НЕ ЗАПРАШИВАЕТСЯ, И ЭТО ВЫНУЖДЕННО, А НЕ
    НЕБРЕЖНОСТЬ. Она возвращает ТОТ ЖЕ объект клиента и ставит признак htmx на
    НЕГО — свойство несущее, оно и позволяет складывать её с фикстурами
    аутентификации. Но у пары «оба транспорта В ОДНОМ ТЕСТЕ» цена его обратная:
    запрошенная рядом, фикстура пометила бы и запрос, который обязан прийти БЕЗ
    признака, и половина деградации молча превратилась бы во вторую половину
    htmx. Поймано прогоном: запрос без JavaScript вернул 200 вместо 302.
    Поэтому признак ставится ЗДЕСЬ и ровно на один запрос из двух.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)
    first = await _seed_schedule(db_session, ad.id, account.id)
    second = await _seed_schedule(db_session, ad.id, account.id)
    body = _editor_delete_body(ad)

    degraded = await authed_client.post(
        f"/schedules/{first.id}/delete",
        content=body,
        headers=FORM_HEADERS,
        follow_redirects=False,
    )
    over_htmx = await authed_client.post(
        f"/schedules/{second.id}/delete",
        content=body,
        headers={**FORM_HEADERS, "HX-Request": "true"},
    )

    assert degraded.status_code == 302
    assert over_htmx.status_code == 204
    assert degraded.headers["location"] == over_htmx.headers["HX-Location"], (
        "адрес приземления разошёлся между транспортами: без JavaScript "
        f"{degraded.headers['location']!r}, через htmx "
        f"{over_htmx.headers['HX-Location']!r}"
    )


def test_control_negative_a_conditional_removal_node_reddens_the_gate():
    """ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ безусловности узлов снятия.

    Несущее правило (`test_editor_delete_returns_oob_nodes`) утверждает, что в
    ответе есть ОБА узла снятия. Зелёным оно обязано быть потому, что узлы
    БЕЗУСЛОВНЫ, а не потому, что на счастливом пути условие сложилось удачно.
    Контроль подставляет в прочитанный исходник ветвь по факту удаления и
    требует, чтобы правило на подделке ПОКРАСНЕЛО.

    ⚠️ ДВОЙНОЙ ПРЕДОХРАНИТЕЛЬ (образец — `_xdata_with_dead_teardown`): контроль
    отдельно доказывает, что подстановка ЧТО-ТО изменила и ИМЕННО ТО. Иначе
    неудавшаяся замена дала бы «правило покраснело» на нетронутом исходнике —
    или, того хуже, зелёный цвет, неотличимый от соблюдения.
    """
    source = _template_text(SCHED_DELETE_RESPONSE_TEMPLATE)
    panel_node = '<div id="sched-del-{{ schedule_id }}" hx-swap-oob="delete"></div>'

    assert source.count(panel_node) == 1, (
        "образец узла снятия панели встречается в источнике не один раз — "
        "подстановка контроля перестала быть однозначной"
    )
    forged = source.replace(
        panel_node, "{% if deleted %}" + panel_node + "{% endif %}"
    )
    assert forged != source, "подстановка контроля ничего не изменила"

    honest = templates.env.from_string(source).render(schedule_id=7, schedules_count=2)
    faked = templates.env.from_string(forged).render(
        schedule_id=7, schedules_count=2, deleted=False
    )

    # Первый предохранитель: несущее свойство на НАСТОЯЩЕМ источнике держится.
    assert honest.count('hx-swap-oob="delete"') == 2, (
        "на настоящем источнике узлов снятия не два — контроль сравнивал бы "
        f"подделку с уже сломанным образцом: {honest!r}"
    )
    # Второй: подделка снимает ИМЕННО узел панели, а не что-нибудь ещё.
    assert 'id="sched-del-7"' not in faked, "подстановка не убрала узел панели"
    assert 'id="sched-7"' in faked, (
        "подстановка задела узел снятия карточки — контроль доказывал бы не то "
        "свойство, которое объявил"
    )
    assert faked.count('hx-swap-oob="delete"') == 1, (
        "правило присутствия обоих узлов НЕ ПОКРАСНЕЛО на подделке: ветвь по "
        "факту удаления прошла бы в дерево незамеченной, и НАЛИЧИЕ узла стало "
        "бы признаком того, что удаление состоялось"
    )


# =============================================================================
# ГРАНИЦА ВЕЛИЧИНЫ ИДЕНТИФИКАТОРА — ПЯТЬ ВХОДОВ ФАЙЛА ОДНИМ ОТОБРАЖЕНИЕМ
# (CR-01 унаследованный, CR-02 новый; отчёт верификации Фазы 10, третий круг)
# =============================================================================
#
# ПРЕДМЕТ — ТОТ ЖЕ ИНВАРИАНТ, ЧТО У T-02-24 / T-02-25, НА ОСИ ВЕЛИЧИНЫ, А НЕ
# ТИПА: «прямой POST мимо браузера обязан давать отказ валидации, а не 500»
# (шапка этого модуля). Коэрция `int` ограничивает ТИП и пропускает число любой
# величины; значение вне диапазона колонки доезжает до драйвера БД и роняет
# запрос (`OverflowError` на SQLite суиты, `DataError` вне int32 на PostgreSQL
# боевого стенда) — то есть даёт ровно ту пятисотку, которую модуль себе
# запретил.
#
# ⚠️ ПЕРЕЧНЕМ, А НЕ ПЯТЬЮ ПРАВИЛАМИ, И ЭТО НЕСУЩЕЕ РЕШЕНИЕ. Правка, закрывшая
# один вход из пяти, уже была принята за закрытие блокера — дважды. Правило с
# ранним отказом показало бы одну несогласную строку из пяти, и следующий круг
# чинил бы вход за входом, воспроизводя ровно ту форму отказа, которой фаза
# провалена третьим кругом.


class _RouteInput(NamedTuple):
    """Один вход маршрута, по которому величина идентификатора доезжает до SQL.

    `url` и `body` — ШАБЛОНЫ: `{value}` подставляется испытуемой величиной,
    `{ad_id}` — ЖИВЫМ идентификатором объявления. Живой идентификатор в теле
    обязателен там, где маршрут читает его сам: иначе случай проверял бы отказ
    по ЧУЖОМУ входу, а не по тому, который назван его именем.

    `live` называет, какая ЖИВАЯ величина подставляется в антивакууме, — без
    неё правило зеленело бы на границе, отвергающей и годное тоже.
    """

    name: str
    carrier: str
    url: str
    body: tuple[tuple[str, str], ...]
    live: str


# Величина ВНЕ диапазона колонки идентификатора. Берётся СТРОКОЙ из двадцати
# пяти девяток — тем же способом, каким её берёт обход транспортов
# (tests/test_pages/test_confirm_delete_transport.py, UNUSABLE_AD_ID_VALUES).
# Приведение к числу на стороне правила спрятало бы предмет: предмет — именно
# то, что ДО приведения на стороне приложения значение доезжает до драйвера.
OUT_OF_COLUMN_RANGE = "9" * 25

# Форма ответа на негодную величину — отказ ВАЛИДАЦИИ, то есть ровно то, что
# модуль правил редактора себе и объявил.
VALIDATION_REFUSAL = 422

# Пять входов файла `app/pages/schedules.py`, доезжающих до сравнения SQL.
# Перечень взят из отчёта верификации третьего круга ДОСЛОВНО: три
# идентификатора пути (`CR-02`) и два поля формы маршрута создания (`CR-01`,
# унаследованный незакрытым).
UNBOUNDED_ROUTE_CASES: tuple[_RouteInput, ...] = (
    _RouteInput(
        name="delete/path:schedule_id",
        carrier="адрес запроса",
        url="/schedules/{value}/delete",
        body=(),
        live="schedule",
    ),
    _RouteInput(
        name="edit/path:schedule_id",
        carrier="адрес запроса",
        url="/schedules/{value}/edit",
        body=(("ad_id", "{ad_id}"),),
        live="schedule",
    ),
    _RouteInput(
        name="toggle/path:schedule_id",
        carrier="адрес запроса",
        url="/schedules/{value}/toggle",
        body=(),
        live="schedule",
    ),
    _RouteInput(
        name="new/form:ad_id",
        carrier="тело формы",
        url="/schedules/new",
        body=(("ad_id", "{value}"),),
        live="ad",
    ),
    _RouteInput(
        name="new/form:account_id",
        carrier="тело формы",
        url="/schedules/new",
        body=(("ad_id", "{ad_id}"), ("account_id", "{value}")),
        live="account",
    ),
)


async def _post_route_input(
    client: AsyncClient, case: _RouteInput, value: str, ad_id: int
):
    """Прямой POST мимо браузера по одному входу перечня.

    Тело собирается СЫРОЙ строкой (`_form`), а не отображением: величина из
    двадцати пяти девяток в отображении потребовала бы приведения, и первое же
    приведение спрятало бы предмет (записанное основание соседнего обхода).
    """
    return await client.post(
        case.url.format(value=value),
        content=_form(
            [(key, tmpl.format(value=value, ad_id=ad_id)) for key, tmpl in case.body]
        ),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )


@pytest.mark.asyncio
async def test_no_schedule_route_answers_with_a_handler_failure_on_an_out_of_range_identifier(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Ни один из ПЯТИ входов файла не роняет обработчик величиной вне диапазона.

    Отображение сличается ЦЕЛИКОМ, и текст отказа называет ВСЕ несогласные
    строки: правило, останавливающееся на первой, чинилось бы по одному входу
    за круг.
    """
    ad = await _seed_ad(db_session, owner.id)
    account = await _seed_account(db_session, owner.id)

    seen = {}
    for case in UNBOUNDED_ROUTE_CASES:
        response = await _post_route_input(
            authed_client, case, OUT_OF_COLUMN_RANGE, ad.id
        )
        seen[case.name] = response.status_code

    disagreed = {
        name: code for name, code in seen.items() if code != VALIDATION_REFUSAL
    }
    assert not disagreed, (
        "величина вне диапазона колонки доехала до обработчика (снято → "
        "ожидалось "
        f"{VALIDATION_REFUSAL}): "
        + "; ".join(f"{name} = {code}" for name, code in sorted(disagreed.items()))
        + ". Предмет — инвариант этого модуля: прямой POST мимо браузера обязан "
        "давать отказ валидации, а не 500 (T-02-24, T-02-25). Несогласных "
        f"строк {len(disagreed)} из {len(UNBOUNDED_ROUTE_CASES)}"
    )

    # АНТИВАКУУМ. Без него зелёное не значит ничего: помощник, отвергающий ВСЁ,
    # дал бы те же пять отказов валидации и объявил бы себя границей.
    alive = {}
    for case in UNBOUNDED_ROUTE_CASES:
        if case.live == "schedule":
            live_value = (await _seed_schedule(db_session, ad.id, account.id)).id
        elif case.live == "ad":
            live_value = ad.id
        else:
            live_value = account.id
        response = await _post_route_input(
            authed_client, case, str(live_value), ad.id
        )
        alive[case.name] = response.status_code

    refused_alive = {
        name: code
        for name, code in alive.items()
        if code == VALIDATION_REFUSAL or code >= 500
    }
    assert not refused_alive, (
        "граница отвергла ГОДНУЮ величину — она отвергает не то, что объявила: "
        + "; ".join(f"{name} = {code}" for name, code in sorted(refused_alive.items()))
        + f". Все снятые исходы: {sorted(alive.items())}"
    )


# --- СМЕЖНОСТЬ ГРАНИЦЫ: ОБЕ СТОРОНЫ, И ОНИ РАЗЛИЧНЫ --------------------------
#
# Ребро `adjacency` зонда покрытия по FORM-06 разрешается ЗДЕСЬ. Граница,
# проверенная только ИЗНУТРИ диапазона, зеленела бы на помощнике, не
# отвергающем ничего; проверенная только СНАРУЖИ — на помощнике, отвергающем
# всё. Замеряется ровно СТЫК: последняя допустимая величина и первая
# недопустимая.
#
# ⚠️ ВЕЛИЧИНА ЧИТАЕТСЯ ИЗ ПРИЛОЖЕНИЯ ВВОЗОМ, А НЕ ВЫПИСЫВАЕТСЯ ЛИТЕРАЛОМ.
# Вторая копия числа разошлась бы с первой молча при первой же правке, и правило
# начало бы утверждать о числе, которого в приложении нет.

# Заведомо несуществующий идентификатор ВНУТРИ диапазона. Нужен эталоном формы
# ответа: величина границы есть ЗАКОННЫЙ идентификатор, которого в базе нет, и
# ожидание для неё формулируется КАК СОВПАДЕНИЕ с ответом на такой же
# несуществующий, а не буквенным кодом. Правило, ожидающее код буквой,
# разъехалось бы с продуктом при первой правке формы ответа на отсутствующую
# запись.
MISSING_INSIDE_RANGE = 999_999

# Маршрут тумблера — самый короткий из трёх с идентификатором пути: ни тела
# формы, ни ветвления по признаку возврата.
ADJACENCY_ROUTE = "/schedules/{value}/toggle"


async def _response_shape(client: AsyncClient, value) -> tuple[int, str | None]:
    """ФОРМА ответа маршрута тумблера: код и адрес приземления.

    Форма — пара, а не один код: две ветви маршрута отвечают одним кодом 302 и
    различаются адресом, и утверждение по одному коду прошло бы на обеих.
    """
    response = await client.post(
        ADJACENCY_ROUTE.format(value=value),
        content=_form([]),
        headers=FORM_HEADERS,
        follow_redirects=False,
    )
    return response.status_code, response.headers.get("location")


@pytest.mark.asyncio
async def test_the_column_bound_admits_its_own_value_and_refuses_the_next_one(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Величина границы принимается, величина на единицу больше — отвергается."""
    reference = await _response_shape(authed_client, MISSING_INSIDE_RANGE)
    at_bound = await _response_shape(authed_client, ID_MAX)
    past_bound = await _response_shape(authed_client, ID_MAX + 1)

    assert at_bound == reference, (
        "величина, РАВНАЯ верхней границе колонки, отвергнута — граница "
        "отвергает годное, и «отказ валидации, а не 500» держалось бы ценой "
        f"сломанного продукта. На границе снято {at_bound}, на несуществующем "
        f"идентификаторе внутри диапазона — {reference}. Разошлась ВНУТРЕННЯЯ "
        "сторона границы"
    )
    assert past_bound[0] == VALIDATION_REFUSAL, (
        "величина НА ЕДИНИЦУ БОЛЬШЕ верхней границы колонки принята: снято "
        f"{past_bound}, ожидался отказ валидации {VALIDATION_REFUSAL}. "
        f"На самой границе снято {at_bound}. Разошлась ВНЕШНЯЯ сторона границы"
    )

    # АНТИВАКУУМ СМЕЖНОСТИ. Помощник, отвечающий одинаково на обе соседние
    # величины, зеленел бы на любом из двух ожиданий ПО ОТДЕЛЬНОСТИ.
    assert at_bound != past_bound, (
        "две СОСЕДНИЕ величины дали ОДИН исход "
        f"({at_bound}) — стык границы не замерен ничем: правило прошло бы и на "
        "помощнике, не отвергающем ничего, и на помощнике, отвергающем всё"
    )
