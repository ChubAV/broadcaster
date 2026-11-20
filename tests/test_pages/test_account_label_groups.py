"""Шапка и `<title>` экрана групп аккаунта показывают номер, а не `#id` (Фаза 17, план 03).

PHONE-03 / PHONE-04 / PHONE-05 на экране `/accounts/{id}/groups`, который Фаза 18 сделает
экраном ручной правки номера. Подпись печатается в трёх местах одной страницы:
шелловом `<h1 class="head-title">` (блок `page_title`), `<h2 class="acct-head__name">`
карточки аккаунта и `<title>`. Первые два — разметкой по адресу `data-account-label`
(там приглушается `#id` двойника), `<title>` — плоской строкой `plain`.

Подпись находится по адресу элемента, а не подстрокой по странице: `#1` входит в `#10`.
Номер в аккаунт кладёт только писатель Фазы 16 (`seed_account`); «как есть» — внутри
`writer_scope()` в самом посеве.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from tests.account_label_support import label_texts, muted_label_ids, seed_account, title_text


@pytest_asyncio.fixture
async def owner(db_session: AsyncSession) -> User:
    return (
        await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _groups_html(client: AsyncClient, account_id: int) -> str:
    response = await client.get(f"/accounts/{account_id}/groups")
    assert response.status_code == 200
    return response.text


@pytest.mark.asyncio
async def test_the_groups_header_shows_the_number_at_both_addresses(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """ТРАССЕР (PHONE-03): номер доезжает до шелловой шапки и карточки аккаунта.

    Адрес `data-account-label="<id>"` стоит на странице ровно дважды: в `<h1>` шелла
    и в `<h2 class="acct-head__name">` — и оба несут одну подпись «{Мессенджер} {номер}».
    """
    account_id = await seed_account(db_session, owner.id, "tg_user", phone="+79991234567")

    html = await _groups_html(authed_client, account_id)

    assert label_texts(html)[str(account_id)] == [
        "Telegram +7 999 123-45-67",
        "Telegram +7 999 123-45-67",
    ], "шапка экрана групп обязана подписывать аккаунт номером в обоих заголовках"


@pytest.mark.asyncio
async def test_the_page_title_carries_the_plain_label(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-12: `<title>` — та же подпись простой строкой с прежним хвостом."""
    account_id = await seed_account(db_session, owner.id, "tg_user", phone="+79991234567")

    html = await _groups_html(authed_client, account_id)

    assert title_text(html).startswith("Telegram +7 999 123-45-67 — группы аккаунта"), (
        f"<title> не несёт номера: {title_text(html)!r}"
    )


@pytest.mark.asyncio
async def test_an_unknown_number_is_muted_in_the_header(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """PHONE-04: аккаунт без номера — приглушённое «Номер неизвестен» в обоих заголовках."""
    account_id = await seed_account(db_session, owner.id, "wa")

    html = await _groups_html(authed_client, account_id)

    assert label_texts(html)[str(account_id)] == [
        "WhatsApp Номер неизвестен",
        "WhatsApp Номер неизвестен",
    ]
    assert str(account_id) in muted_label_ids(html), "«Номер неизвестен» обязан быть приглушён"
