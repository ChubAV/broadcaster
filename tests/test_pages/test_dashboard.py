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


async def _seed_send_log(
    db: AsyncSession,
    user_id: int,
    *,
    sent_at: datetime,
    status: str = "ok",
    group_id: int | None = None,
) -> SendLog:
    log = SendLog(
        user_id=user_id,
        group_id=group_id,
        ad_title="Отправка объявления",
        ad_text="Текст отправленного объявления",
        ad_images=[],
        group_name="Группа отправки",
        messenger_type="wa",
        task_id="task-9f3c1d",
        status=status,
        sent_at=sent_at,
    )
    db.add(log)
    await db.commit()
    return log


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