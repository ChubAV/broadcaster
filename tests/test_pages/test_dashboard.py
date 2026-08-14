"""Дашборд: плитки метрик за скользящие сутки (DASH-01).

Собственного файла тестов у дашборда до Фазы 4 не было — страницу задевали
только сквозные обходы разметки. Этот файл держит её прикладное обещание:
четыре плитки отправок живы, считаются модулем аналитики и не смешаны со
счётчиками сущностей, снятыми D-01.
"""

import re
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import recent_feed
from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.pages.dashboard import dashboard_next_step
from app.pages.dashboard_feed import FEED_LIMIT, FEED_POLL_SECONDS
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.user import User

# Подписи четырёх плиток отправок — ровно те, что рендерит dashboard.html.
TILE_LABELS = ("Отправок за сутки", "Успешно", "Ошибок", "Групп охвачено")

# Подписи счётчиков сущностей, снятые D-01. В ТЕЛЕ страницы их быть не должно;
# в боковом меню одноимённые пункты навигации остаются и сюда не попадают —
# тело вырезается по <div data-body> шелла.
REMOVED_LABELS = ("Объявления", "Аккаунты", "Группы", "Отправлено сегодня")


def _page_body(html: str) -> str:
    """Тело страницы без шелла: навигация несёт те же слова, что и снятые плитки."""
    marker = "<div data-body>"
    assert marker in html, "шелл изменился — тело страницы больше не размечено"
    return html[html.index(marker) :]


def _tile_value(html: str, label: str) -> int:
    """Число плитки с указанной подписью."""
    assert label in html, f"плитка {label!r} не найдена"
    tail = html[html.index(label) :]
    match = re.search(r"<span data-metric-value>(\d+)</span>", tail)
    assert match, f"у плитки {label!r} нет значения"
    return int(match.group(1))


async def _current_user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_user(db: AsyncSession, email: str) -> User:
    """Владелец записей для тестов БЕЗ поднятия страницы.

    Пользователя `testuser@test.com` заводит фикстура регистрации, которую
    тянет только `authed_client`. Тесты самой выборки страницу не поднимают —
    им нужен владелец, а не сессия, — поэтому владелец заводится прямой
    вставкой.
    """
    user = User(email=email, password_hash="x", name="Владелец")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _seed_send_log(
    db: AsyncSession,
    user_id: int,
    *,
    sent_at: datetime,
    status: str = "ok",
    group_id: int | None = None,
    ad_title: str = "Отправка объявления",
    group_name: str = "Группа отправки",
    messenger_type: str = "wa",
) -> SendLog:
    log = SendLog(
        user_id=user_id,
        group_id=group_id,
        ad_title=ad_title,
        ad_text="Текст отправленного объявления",
        ad_images=[],
        group_name=group_name,
        messenger_type=messenger_type,
        task_id="task-9f3c1d",
        status=status,
        sent_at=sent_at,
    )
    db.add(log)
    await db.commit()
    return log


async def _seed_schedule(
    db: AsyncSession,
    *,
    next_run_at: datetime | None,
    title: str = "Объявление рассылки",
    ad_status: str = AD_STATUS_PUBLISHED,
    account_status: str = "active",
    with_account: bool = True,
    group_flags: tuple[bool, ...] = (True,),
    is_active: bool = True,
    seq: str = "1",
) -> Schedule:
    """Расписание текущего пользователя вместе с объявлением, аккаунтом и группами.

    Владение расписанием идёт ЧЕРЕЗ ОБЪЯВЛЕНИЕ: колонки user_id у расписания
    нет, поэтому посев обязан заводить объявление владельца.
    """
    user = await _current_user(db)
    ad = Ad(
        user_id=user.id, title=title, text="Текст объявления", images=[], status=ad_status
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)

    account = None
    group_ids: list[int] = []
    if with_account:
        account = MessengerAccount(
            user_id=user.id, type="wa", credentials="creds", status=account_status
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        for index, flag in enumerate(group_flags):
            group = Group(
                user_id=user.id,
                account_id=account.id,
                messenger_type="wa",
                group_external_id=f"-200{seq}{index}",
                name=f"Группа {seq}{index}",
                is_active=flag,
            )
            db.add(group)
            await db.commit()
            await db.refresh(group)
            group_ids.append(group.id)

    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id if account else None,
        group_ids=group_ids,
        days_of_week=[0, 1, 2, 3, 4, 5, 6],
        times_of_day=["10:00"],
        timezone="UTC",
        is_active=is_active,
        next_run_at=next_run_at,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@pytest.mark.asyncio
async def test_dashboard_renders_four_send_tiles(
    authed_client: AsyncClient, db_session: AsyncSession
):
    response = await authed_client.get("/dashboard")

    assert response.status_code == 200
    body = _page_body(response.text)
    for label in TILE_LABELS:
        assert label in body, f"плитка {label!r} не отрисовалась"


@pytest.mark.asyncio
async def test_dashboard_body_has_no_entity_counters(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-01: счётчики объявлений, аккаунтов и групп из тела дашборда убраны."""
    response = await authed_client.get("/dashboard")

    body = _page_body(response.text)
    leftovers = [label for label in REMOVED_LABELS if label in body]
    assert not leftovers, f"счётчики сущностей остались в теле дашборда: {leftovers}"


@pytest.mark.asyncio
async def test_dashboard_tile_counts_last_day_sends(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Значение плитки «Отправок за сутки» равно числу записей за сутки."""
    user = await _current_user(db_session)
    now = datetime.now(timezone.utc)
    for hours in (1, 2, 3):
        await _seed_send_log(db_session, user.id, sent_at=now - timedelta(hours=hours))
    # За пределами окна — в плитку не попадает.
    await _seed_send_log(db_session, user.id, sent_at=now - timedelta(hours=30))

    body = _page_body((await authed_client.get("/dashboard")).text)

    assert _tile_value(body, "Отправок за сутки") == 3


@pytest.mark.asyncio
async def test_dashboard_tiles_split_ok_and_failed(
    authed_client: AsyncClient, db_session: AsyncSession
):
    user = await _current_user(db_session)
    now = datetime.now(timezone.utc)
    await _seed_send_log(db_session, user.id, sent_at=now - timedelta(hours=1))
    await _seed_send_log(
        db_session, user.id, sent_at=now - timedelta(hours=2), status="fail"
    )
    await _seed_send_log(
        db_session,
        user.id,
        sent_at=now - timedelta(hours=3),
        status="account_disconnected",
    )

    body = _page_body((await authed_client.get("/dashboard")).text)

    assert _tile_value(body, "Отправок за сутки") == 3
    assert _tile_value(body, "Успешно") == 1
    assert _tile_value(body, "Ошибок") == 2


@pytest.mark.asyncio
async def test_dashboard_tiles_carry_a_delta(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Дельта к предыдущим суткам — часть плитки, а не отдельный экран (D-03)."""
    user = await _current_user(db_session)
    now = datetime.now(timezone.utc)
    await _seed_send_log(db_session, user.id, sent_at=now - timedelta(hours=1))

    body = _page_body((await authed_client.get("/dashboard")).text)

    deltas = re.findall(r"<span data-metric-delta data-tone=\"[a-z]+\">", body)
    assert len(deltas) == len(TILE_LABELS), (
        f"дельта проставлена не у всех плиток: найдено {len(deltas)}"
    )


@pytest.mark.asyncio
async def test_dashboard_survives_send_log_without_group(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Плитка «Групп охвачено» не падает на записи с пустым group_id."""
    user = await _current_user(db_session)
    now = datetime.now(timezone.utc)
    await _seed_send_log(db_session, user.id, sent_at=now - timedelta(hours=1))

    response = await authed_client.get("/dashboard")

    assert response.status_code == 200
    assert _tile_value(_page_body(response.text), "Групп охвачено") == 0


@pytest.mark.asyncio
async def test_dashboard_hides_other_users_sends(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-01: чужие отправки в плитки не попадают."""
    stranger = User(
        email="stranger-dash@test.com", password_hash="x", name="S", timezone="UTC"
    )
    db_session.add(stranger)
    await db_session.commit()
    await db_session.refresh(stranger)
    await _seed_send_log(
        db_session, stranger.id, sent_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )

    body = _page_body((await authed_client.get("/dashboard")).text)

    assert _tile_value(body, "Отправок за сутки") == 0


@pytest.mark.asyncio
async def test_dashboard_requires_authentication(client: AsyncClient):
    response = await client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


# --- Ближайшие отправки (DASH-02) -------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_upcoming_row_renders_data(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Строка блока отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    Перевод include в макрос теряет неявный контекст вызывающего, и ошибка
    проявляется ПУСТОЙ строкой при статусе 200 — утверждения на статус такую
    поломку не ловят.
    """
    await _seed_schedule(
        db_session,
        next_run_at=datetime.now(timezone.utc) + timedelta(hours=2),
        title="Летняя распродажа",
        group_flags=(True, True),
    )

    response = await authed_client.get("/dashboard")

    assert response.status_code == 200
    body = _page_body(response.text)
    assert "Летняя распродажа" in body, "название объявления не отрисовано"
    assert "2 группы" in body, "подпись состава групп не отрисована"


@pytest.mark.asyncio
async def test_dashboard_upcoming_row_links_to_the_ad_editor(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-16: клик по строке ведёт в редактор объявления, обычной ссылкой.

    Отдельной страницы расписания в проекте нет (D-14), поэтому адрес — тот же,
    что у карточки раздела расписаний: редактор объявления с развёрнутым
    расписанием.
    """
    schedule = await _seed_schedule(
        db_session, next_run_at=datetime.now(timezone.utc) + timedelta(hours=2)
    )

    body = _page_body((await authed_client.get("/dashboard")).text)

    assert f"/ads/{schedule.ad_id}/edit?sched={schedule.id}" in body


@pytest.mark.asyncio
async def test_dashboard_upcoming_marks_detached_account(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-15: расписание с отвязанным аккаунтом ВИДНО и помечено причиной."""
    await _seed_schedule(
        db_session,
        next_run_at=datetime.now(timezone.utc) + timedelta(hours=2),
        title="Расписание без аккаунта",
        with_account=False,
    )

    body = _page_body((await authed_client.get("/dashboard")).text)

    assert "Расписание без аккаунта" in body, "внутренний join потерял строку"
    assert "Аккаунт отключён" in body


@pytest.mark.asyncio
async def test_dashboard_upcoming_marks_draft_ad(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _seed_schedule(
        db_session,
        next_run_at=datetime.now(timezone.utc) + timedelta(hours=2),
        title="Черновик рассылки",
        ad_status=AD_STATUS_DRAFT,
    )

    body = _page_body((await authed_client.get("/dashboard")).text)

    assert "Черновик рассылки" in body
    assert "Объявление в черновике" in body


@pytest.mark.asyncio
async def test_dashboard_upcoming_marks_all_groups_off(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _seed_schedule(
        db_session,
        next_run_at=datetime.now(timezone.utc) + timedelta(hours=2),
        title="Рассылка в выключенные группы",
        group_flags=(False, False),
    )

    body = _page_body((await authed_client.get("/dashboard")).text)

    assert "Рассылка в выключенные группы" in body
    assert "Все группы выключены" in body


@pytest.mark.asyncio
async def test_dashboard_upcoming_is_sorted_by_next_run_at(
    authed_client: AsyncClient, db_session: AsyncSession
):
    now = datetime.now(timezone.utc)
    await _seed_schedule(
        db_session, next_run_at=now + timedelta(hours=6), title="Вечерняя", seq="1"
    )
    await _seed_schedule(
        db_session, next_run_at=now + timedelta(hours=1), title="Утренняя", seq="2"
    )

    body = _page_body((await authed_client.get("/dashboard")).text)

    assert body.index("Утренняя") < body.index("Вечерняя")


@pytest.mark.asyncio
async def test_dashboard_upcoming_survives_lazy_raise_relationships(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """`Schedule.ad`/`Schedule.account` объявлены lazy="raise".

    Обращение к ним как к атрибутам даёт не пустой блок, а ПЯТИСОТКУ на самом
    дашборде — поэтому статус ответа здесь утверждается наравне с содержимым.
    """
    await _seed_schedule(
        db_session,
        next_run_at=datetime.now(timezone.utc) + timedelta(hours=2),
        title="Проверка ленивой загрузки",
    )

    response = await authed_client.get("/dashboard")

    assert response.status_code == 200
    assert "Проверка ленивой загрузки" in _page_body(response.text)


# --- Поблочные пустые состояния (D-39, D-40) --------------------------------


def test_next_step_without_accounts_leads_to_connecting_one():
    """Первое, чего не хватает пользователю без ничего, — подключённый канал."""
    label, href = dashboard_next_step(
        {"accounts": 0, "ads": 0, "schedules": 0, "history": 0}
    )

    assert label
    assert href == "/accounts"


def test_next_step_with_account_but_no_ads_leads_to_creating_an_ad():
    label, href = dashboard_next_step(
        {"accounts": 1, "ads": 0, "schedules": 0, "history": 0}
    )

    assert label
    assert href == "/ads/new"


def test_next_step_with_ads_but_no_schedules_leads_to_the_ads_section():
    """Расписания создаются В РЕДАКТОРЕ ОБЪЯВЛЕНИЯ (D-14).

    Отдельной страницы создания расписания в проекте нет, поэтому призыв ведёт
    туда же, куда ведёт пустое состояние самого раздела расписаний, — иначе на
    два одинаковых вопроса продукт отвечал бы двумя разными адресами.
    """
    label, href = dashboard_next_step(
        {"accounts": 1, "ads": 2, "schedules": 0, "history": 0}
    )

    assert label
    assert href == "/ads"


def test_next_step_is_empty_when_everything_is_set_up():
    """Всё заведено — призыва к действию нет, остаётся только текст."""
    assert dashboard_next_step(
        {"accounts": 1, "ads": 2, "schedules": 3, "history": 0}
    ) == ("", "")


def test_next_step_survives_an_empty_counter_dict():
    """Счётчики шелла отсутствуют — функция не роняет страницу.

    `get_shell_context` возвращает ПУСТОЙ словарь, когда пользователя нет, и
    обращение к отсутствующему ключу дало бы пятисотку на дашборде вместо
    призыва к действию.
    """
    label, href = dashboard_next_step({})

    assert href == "/accounts"
    assert label


@pytest.mark.asyncio
async def test_dashboard_tiles_render_zeros_on_completely_empty_data(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-39: плитки видны ВСЕГДА. Ноль — честный ответ, а не повод спрятать блок."""
    response = await authed_client.get("/dashboard")

    assert response.status_code == 200
    body = _page_body(response.text)
    for label in TILE_LABELS:
        assert _tile_value(body, label) == 0


@pytest.mark.asyncio
async def test_dashboard_empty_grid_is_replaced_by_an_empty_state(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Сетка из нулей выглядит как поломка, поэтому её место занимает объяснение."""
    body = _page_body((await authed_client.get("/dashboard")).text)

    assert "data-heatmap" not in body, "пустая сетка отрисована вместо объяснения"
    assert 'href="/accounts"' in body, "пустое состояние не ведёт к подключению канала"


@pytest.mark.asyncio
async def test_dashboard_empty_blocks_lead_to_creating_an_ad(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-40: у пользователя с аккаунтом, но без объявлений призыв другой."""
    user = await _current_user(db_session)
    account = MessengerAccount(
        user_id=user.id, type="wa", credentials="creds", status="active"
    )
    db_session.add(account)
    await db_session.commit()

    body = _page_body((await authed_client.get("/dashboard")).text)

    assert 'href="/ads/new"' in body
    assert 'href="/accounts"' not in body, "призыв не сменился на следующий шаг"


@pytest.mark.asyncio
async def test_dashboard_empty_blocks_lead_to_the_ads_section_without_schedules(
    authed_client: AsyncClient, db_session: AsyncSession
):
    user = await _current_user(db_session)
    account = MessengerAccount(
        user_id=user.id, type="wa", credentials="creds", status="active"
    )
    db_session.add(account)
    ad = Ad(
        user_id=user.id,
        title="Объявление без расписания",
        text="Текст",
        images=[],
        status=AD_STATUS_PUBLISHED,
    )
    db_session.add(ad)
    await db_session.commit()

    body = _page_body((await authed_client.get("/dashboard")).text)

    assert 'href="/ads"' in body
    assert 'href="/ads/new"' not in body, "призыв не сменился на следующий шаг"


@pytest.mark.asyncio
async def test_dashboard_empty_state_has_no_action_when_everything_is_set_up(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Всё заведено, отправок ещё не было — пустое состояние БЕЗ призыва.

    Призыв «создайте объявление» пользователю, у которого уже всё создано, —
    это не помощь, а шум: ждать первой отправки ему больше нечего.
    """
    await _seed_schedule(
        db_session, next_run_at=datetime.now(timezone.utc) + timedelta(hours=3)
    )

    body = _page_body((await authed_client.get("/dashboard")).text)

    assert "empty__action" not in body, "призыв к действию остался при заполненном аккаунте"
    assert "data-heatmap" not in body, "пустая сетка отрисована вместо объяснения"


@pytest.mark.asyncio
async def test_dashboard_empty_upcoming_block_has_its_own_text(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Тексты пустых состояний РАЗНЫЕ: пустая сетка и пустой список — не одно и то же."""
    body = _page_body((await authed_client.get("/dashboard")).text)

    titles = re.findall(r'<span class="empty__title">([^<]+)</span>', body)
    assert len(titles) >= 2, f"пустых состояний меньше двух: {titles}"
    assert len(set(titles)) == len(titles), f"тексты пустых состояний совпадают: {titles}"


# --- Живая лента: выборка строк (DASH-03) -----------------------------------
#
# Источник ленты — ТОЛЬКО журнал отправок (D-05). Событий синхронизации,
# переподключения воркера и активации расписания в базе нет вовсе, и заводить
# ради них таблицу событий — работа отдельной фазы, а не этого блока.


@pytest.mark.asyncio
async def test_recent_feed_returns_newest_first(db_session: AsyncSession):
    """Лента отсортирована по времени отправки ПО УБЫВАНИЮ.

    Обратный порядок не роняет ни одного утверждения на статус: блок остаётся
    заполненным, просто «живая» лента показывает самое старое сверху и не
    меняется при новых отправках.
    """
    user = await _seed_user(db_session, "feed-order@test.com")
    now = datetime.now(timezone.utc)
    await _seed_send_log(
        db_session, user.id, sent_at=now - timedelta(hours=3), ad_title="Старая"
    )
    await _seed_send_log(
        db_session, user.id, sent_at=now - timedelta(minutes=1), ad_title="Свежая"
    )
    await _seed_send_log(
        db_session, user.id, sent_at=now - timedelta(hours=1), ad_title="Средняя"
    )

    rows = await recent_feed(db_session, user_id=user.id)

    assert [row.ad_title for row in rows] == ["Свежая", "Средняя", "Старая"]


@pytest.mark.asyncio
async def test_recent_feed_respects_the_limit(db_session: AsyncSession):
    """Лента отдаёт не больше `limit` строк — и по умолчанию, и по аргументу."""
    user = await _seed_user(db_session, "feed-limit@test.com")
    now = datetime.now(timezone.utc)
    for index in range(FEED_LIMIT + 4):
        await _seed_send_log(
            db_session, user.id, sent_at=now - timedelta(minutes=index)
        )

    assert len(await recent_feed(db_session, user_id=user.id)) == FEED_LIMIT
    assert len(await recent_feed(db_session, user_id=user.id, limit=3)) == 3


@pytest.mark.asyncio
async def test_recent_feed_row_carries_the_fields_of_the_record(
    db_session: AsyncSession,
):
    """Строка несёт идентификатор записи, название, группу, статус и время.

    Идентификатор — не украшение: по нему строится адрес записи истории, и
    строка без него вела бы в никуда.
    """
    user = await _seed_user(db_session, "feed-fields@test.com")
    sent_at = datetime.now(timezone.utc) - timedelta(minutes=7)
    log = await _seed_send_log(
        db_session,
        user.id,
        sent_at=sent_at,
        status="fail",
        ad_title="Объявление ленты",
        group_name="Группа ленты",
        messenger_type="tg_user",
    )

    (row,) = await recent_feed(db_session, user_id=user.id)

    assert row.id == log.id
    assert row.ad_title == "Объявление ленты"
    assert row.group_name == "Группа ленты"
    assert row.status == "fail"
    assert row.messenger_type == "tg_user"
    assert row.sent_at is not None


@pytest.mark.asyncio
async def test_recent_feed_ignores_other_users(db_session: AsyncSession):
    """T-04-17: чужие записи в ленту не попадают.

    Маршрут ленты дёргается автоматически каждые несколько секунд на каждой
    открытой вкладке — утечка здесь тиражируется, а не случается однажды.
    """
    user = await _seed_user(db_session, "feed-owner@test.com")
    stranger = await _seed_user(db_session, "feed-stranger@test.com")

    now = datetime.now(timezone.utc)
    await _seed_send_log(
        db_session, stranger.id, sent_at=now, ad_title="Чужая отправка"
    )
    await _seed_send_log(db_session, user.id, sent_at=now, ad_title="Своя отправка")

    rows = await recent_feed(db_session, user_id=user.id)

    assert [row.ad_title for row in rows] == ["Своя отправка"]


# --- Живая лента: маршрут паршала (DASH-03) ---------------------------------


@pytest.mark.asyncio
async def test_dashboard_feed_returns_rows(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Маршрут отдаёт 200 и РАЗМЕТКУ строк, а не пустой фрагмент."""
    user = await _current_user(db_session)
    await _seed_send_log(
        db_session,
        user.id,
        sent_at=datetime.now(timezone.utc) - timedelta(minutes=2),
        ad_title="Отправка в ленте",
        group_name="Группа в ленте",
    )

    response = await authed_client.get("/dashboard/feed")

    assert response.status_code == 200
    assert "Отправка в ленте" in response.text
    assert "Группа в ленте" in response.text
    assert "data-feedrow" in response.text


@pytest.mark.asyncio
async def test_dashboard_feed_row_links_to_the_history_record(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-08: строка ленты — обычная ССЫЛКА в запись истории.

    Не элемент с обработчиком щелчка: ссылка работает при выключенном
    JavaScript, открывается средним щелчком и попадает под Tab.
    """
    user = await _current_user(db_session)
    log = await _seed_send_log(
        db_session, user.id, sent_at=datetime.now(timezone.utc) - timedelta(minutes=2)
    )

    response = await authed_client.get("/dashboard/feed")

    assert f'href="/history/{log.id}"' in response.text


@pytest.mark.asyncio
async def test_dashboard_feed_requires_authentication(client: AsyncClient):
    """T-04-17: неавторизованному маршрут ленты не отвечает данными."""
    response = await client.get("/dashboard/feed", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_dashboard_feed_response_is_a_fragment_not_a_page(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Ответ паршала — фрагмент: шелл он не наследует и не рисует.

    Наследование шелла здесь означало бы целую страницу внутри контейнера
    ленты каждые несколько секунд.
    """
    user = await _current_user(db_session)
    await _seed_send_log(
        db_session, user.id, sent_at=datetime.now(timezone.utc) - timedelta(minutes=2)
    )

    body = (await authed_client.get("/dashboard/feed")).text

    for marker in ("<html", "data-shell", "data-side", "data-body"):
        assert marker not in body, f"паршал ленты несёт разметку шелла: {marker}"


@pytest.mark.asyncio
async def test_dashboard_feed_does_not_load_the_shell_context(
    authed_client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Открытое решение 4: маршрут ленты объявлен МИМО страничного роутера.

    Страничный роутер несёт `load_shell_context` зависимостью на КАЖДОМ своём
    маршруте — четыре round-trip на вызов. При бессрочном опросе эта цена
    умножается на число открытых вкладок и делится на интервал.

    Тест ПАРНЫЙ внутри себя: сначала утверждается, что счётчик вообще
    срабатывает (на самой странице), иначе вторая половина зеленела бы на
    сломанном шпионе.
    """
    import app.pages as pages_package

    original = pages_package.get_shell_context
    calls: list[int] = []

    async def _spy(db, user):
        calls.append(1)
        return await original(db, user)

    monkeypatch.setattr(pages_package, "get_shell_context", _spy)

    assert (await authed_client.get("/dashboard")).status_code == 200
    assert calls, "шпион не сработал даже на странице — вторая половина бессмысленна"

    calls.clear()
    assert (await authed_client.get("/dashboard/feed")).status_code == 200
    assert not calls, (
        "паршал ленты тянет контекст шелла: четыре запроса на каждый тик "
        "каждой открытой вкладки"
    )


def test_feed_constants_are_inside_the_decided_ranges():
    """Интервал опроса и число строк — середины вилок D-07 (15-30 с) и D-08 (6-10).

    Значения вынесены константами, чтобы разметка страницы и паршал читали ОДИН
    источник: интервал, выписанный литералом в шаблоне, разъехался бы с лимитом
    молча.
    """
    assert 15 <= FEED_POLL_SECONDS <= 30
    assert 6 <= FEED_LIMIT <= 10