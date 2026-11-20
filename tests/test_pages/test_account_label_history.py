"""Номер аккаунта на экране истории пользователя (Фаза 17, PHONE-03/04/05).

Подпись находится по АДРЕСУ `data-account-label="<id>"`, а не подстрокой: `#1`
входит в `#10`, а слово «Номер неизвестен» у соседней записи засчитало бы подпись
не тому аккаунту (`tests/account_label_support.py`). Здесь закреплены карточка
страницы `/history`, порция прокрутки `/history/partial` и подписи `<option>`
фильтра: номер, «Номер неизвестен», двойник с `#id`, запись без аккаунта (D-15).

Гейты номера (`tests/test_phone_privacy_gate.py`, `tests/test_phone_gates_parity.py`,
`tests/test_application/test_phone_single_writer_gate.py`) этот модуль не трогает:
номер ставится только писателем Фазы 16 через `seed_account`.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.send_log import SendLog
from app.models.user import User
from tests.account_label_support import (
    label_texts,
    muted_label_ids,
    seed_account,
)
from tests.conftest import seed_group


async def _current_user_id(db: AsyncSession) -> int:
    return (
        await db.execute(select(User.id).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_log(
    db: AsyncSession, user_id: int, group_id: int | None, *, name: str = "Группа отправки"
) -> int:
    """Запись журнала на группу (или без неё); возвращает id."""
    log = SendLog(
        user_id=user_id,
        group_id=group_id,
        ad_title="Объявление",
        ad_text="Текст",
        ad_images=[],
        group_name=name,
        messenger_type="wa",
        task_id="task-1",
        status="ok",
        sent_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    return log.id


async def _history_with_one_record(
    db: AsyncSession, client: AsyncClient, type_: str = "tg_user", **account_kw
) -> tuple[int, str]:
    """Аккаунт, группа, одна запись; возвращает (id аккаунта, html `/history`)."""
    user_id = await _current_user_id(db)
    account_id = await seed_account(db, user_id, type_, **account_kw)
    group = await seed_group(db, account_id, user_id)
    await _seed_log(db, user_id, group.id)
    response = await client.get("/history")
    assert response.status_code == 200
    return account_id, response.text


@pytest.mark.asyncio
async def test_the_history_card_shows_the_number_at_its_address(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ТРАССЕР: номер из колонки `phone` доходит до карточки страницы истории."""
    account_id, html = await _history_with_one_record(
        db_session, authed_client, "tg_user", phone="+79991234567"
    )

    assert label_texts(html)[str(account_id)] == ["+7 999 123-45-67"]


@pytest.mark.asyncio
async def test_a_history_card_without_a_number_reads_as_unknown(
    authed_client: AsyncClient, db_session: AsyncSession
):
    account_id, html = await _history_with_one_record(db_session, authed_client, "wa")

    assert label_texts(html)[str(account_id)] == ["Номер неизвестен"]
    assert str(account_id) in muted_label_ids(html)


@pytest.mark.asyncio
async def test_a_twin_history_card_carries_the_id(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Два `wa` без номера — двойники: у записи первого рядом приглушённый `#id`."""
    user_id = await _current_user_id(db_session)
    first = await seed_account(db_session, user_id, "wa")
    await seed_account(db_session, user_id, "wa")
    group = await seed_group(db_session, first, user_id)
    await _seed_log(db_session, user_id, group.id)

    html = (await authed_client.get("/history")).text

    assert label_texts(html)[str(first)] == [f"Номер неизвестен #{first}"]


# --- порция прокрутки `/history/partial` ----------------------------------------


@pytest.mark.asyncio
async def test_the_history_batch_shows_the_number_at_its_address(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Порция подписана так же, как страница: фрагмент строит карту отдельно."""
    user_id = await _current_user_id(db_session)
    account_id = await seed_account(db_session, user_id, "tg_user", phone="+79991234567")
    group = await seed_group(db_session, account_id, user_id)
    await _seed_log(db_session, user_id, group.id)

    response = await authed_client.get("/history/partial?offset=0&limit=5")

    assert response.status_code == 200
    assert label_texts(response.text)[str(account_id)] == ["+7 999 123-45-67"]


@pytest.mark.asyncio
async def test_the_batch_twin_flag_matches_the_accounts_screen(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-14: признак двойника считается по ВСЕМ аккаунтам, а не по записям порции.

    Второй аккаунт в порцию не попал — записи на нём нет, — но подпись первого
    несёт `#id`, ровно как на экране «Аккаунты», где тот же `build_labels`
    считает по списку аккаунтов пользователя.
    """
    from app.application.accounts.labels import load_account_rows
    from app.services.account_label import build_labels

    user_id = await _current_user_id(db_session)
    first = await seed_account(db_session, user_id, "wa")
    second = await seed_account(db_session, user_id, "wa")
    group = await seed_group(db_session, first, user_id)
    await _seed_log(db_session, user_id, group.id)

    html = (await authed_client.get("/history/partial?offset=0&limit=5")).text

    rule = build_labels(await load_account_rows(db_session, user_id))
    assert rule[first].twin and rule[second].twin
    assert label_texts(html)[str(first)] == [f"Номер неизвестен #{first}"]
    assert str(second) not in label_texts(html), "записи на втором аккаунте нет"


@pytest.mark.asyncio
async def test_a_record_without_a_group_carries_no_account_label(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-15: у записи без группы нет и аккаунта — «Номер неизвестен» ей не приписывается."""
    user_id = await _current_user_id(db_session)
    await seed_account(db_session, user_id, "wa")  # живой аккаунт без номера рядом
    await _seed_log(db_session, user_id, None, name="Группа удалена")

    response = await authed_client.get("/history/partial?offset=0&limit=5")

    assert response.status_code == 200
    assert 'id="history-row-' in response.text, "запись на месте"
    assert "data-account-label" not in response.text
    assert "Номер неизвестен" not in response.text


@pytest.mark.asyncio
async def test_the_batch_reads_accounts_once(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-18: карта аккаунтов на порцию — ОДИН запрос с проекцией `phone`, без записи."""
    from sqlalchemy import event

    user_id = await _current_user_id(db_session)
    account_id = await seed_account(db_session, user_id, "tg_user", phone="+79991234567")
    group = await seed_group(db_session, account_id, user_id)
    for _ in range(5):
        await _seed_log(db_session, user_id, group.id)

    statements: list[str] = []
    sync_engine = db_session.bind.sync_engine

    def _record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(sync_engine, "before_cursor_execute", _record)
    try:
        response = await authed_client.get("/history/partial?offset=0&limit=5")
    finally:
        event.remove(sync_engine, "before_cursor_execute", _record)

    assert response.status_code == 200
    assert response.text.count('data-account-label="') == 5, "пять записей — пять подписей"
    with_phone = [s for s in statements if "messenger_accounts.phone" in s]
    assert len(with_phone) == 1, f"карта номеров прочитана {len(with_phone)} раз, ожидался один запрос"
    writes = [
        s for s in statements if s.lstrip().upper().split(None, 1)[0] in {"INSERT", "UPDATE", "DELETE"}
    ]
    assert not writes, f"порция истории ничего не пишет: {writes}"
