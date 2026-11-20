"""Показ номера на экране «Аккаунты» (Фаза 17, PHONE-03, PHONE-04, PHONE-05).

Подпись аккаунта находится по адресу `data-account-label="<id>"`, а не
подстрокой: `#1` входит в `#10`, а слово «Номер неизвестен» у соседней карточки
засчитало бы подпись не тому элементу (разбор — `tests/account_label_support.py`).

Карточка аккаунта рисуется ТРЕМЯ файлами (первая отрисовка, порция подгрузки,
фрагмент опроса синхронизации), и в каждом из них подпись обязана читаться
одинаково: по D-14 признак двойника считается по ВСЕМ аккаунтам пользователя,
а не по странице из 30 и не по порции.

Номер в тестах ставит только писатель Фазы 16 (`seed_account`): запись мимо
него краснит гейты единственного писателя и приватности номера.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from tests.account_label_support import (
    element_text,
    label_texts,
    muted_label_ids,
    seed_account,
)

NUMBER_TEXT = "+7 999 123-45-67"
UNKNOWN_TEXT = "Номер неизвестен"


@pytest_asyncio.fixture
async def owner(db_session: AsyncSession) -> User:
    return (
        await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _stranger(db_session: AsyncSession) -> int:
    """Второй пользователь: его аккаунты чужие для `authed_client`."""
    user = User(email="stranger-17-02@test.com", password_hash="x", name="stranger")
    db_session.add(user)
    await db_session.commit()
    return user.id


# --- Страница /accounts ------------------------------------------------------


@pytest.mark.asyncio
async def test_the_account_card_shows_the_number_at_its_address(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """ТРАССЕР (PHONE-03): номер из колонки `phone` доезжает до карточки аккаунта.

    D-10: имя канала уже стоит отдельным `acct-card__chan`, поэтому на месте
    прежнего `#id` стоит ТОЛЬКО номер.
    """
    account_id = await seed_account(db_session, owner.id, "tg_user", phone="+79991234567")

    html = (await authed_client.get("/accounts")).text

    assert label_texts(html)[str(account_id)] == [NUMBER_TEXT], (
        "карточка должна показывать номер по адресу data-account-label"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["syncing", "sync_failed", "active"])
async def test_a_card_without_a_number_reads_as_unknown_in_every_status_branch(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, status: str
):
    """PHONE-04, D-02: во всех трёх ветках карточки — приглушённое «Номер неизвестен»."""
    account_id = await seed_account(db_session, owner.id, "wa", status=status)

    html = (await authed_client.get("/accounts")).text

    assert label_texts(html)[str(account_id)] == [UNKNOWN_TEXT], (
        f"ветка {status}: у аккаунта без номера подпись — «Номер неизвестен» без #id"
    )
    assert str(account_id) in muted_label_ids(html), (
        f"ветка {status}: «Номер неизвестен» должен быть приглушён"
    )


@pytest.mark.asyncio
async def test_twin_cards_carry_a_muted_id(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """PHONE-05, D-03: две подписи совпали у аккаунтов одного мессенджера — виден `#id`."""
    first = await seed_account(db_session, owner.id, "wa")
    second = await seed_account(db_session, owner.id, "wa")
    unique = await seed_account(db_session, owner.id, "max", phone="+79991234567")

    html = (await authed_client.get("/accounts")).text
    labels = label_texts(html)

    assert labels[str(first)] == [f"{UNKNOWN_TEXT} #{first}"], "двойник без номера несёт #id"
    assert labels[str(second)] == [f"{UNKNOWN_TEXT} #{second}"], "второй двойник тоже несёт #id"
    assert "#" not in labels[str(unique)][0], "у уникальной подписи #id быть не должно"


@pytest.mark.asyncio
async def test_the_delete_modal_names_the_account_by_its_plain_label(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-13, D-12: тело модалки удаления — плоская подпись пользователя; у двойника `#id`."""
    numbered = await seed_account(db_session, owner.id, "tg_user", phone="+79991234567")
    first_twin = await seed_account(db_session, owner.id, "wa")
    second_twin = await seed_account(db_session, owner.id, "wa")

    html = (await authed_client.get("/accounts")).text

    assert element_text(html, f"acc-del-{numbered}-text") == f"Telegram {NUMBER_TEXT}", (
        "тело модалки удаления называет аккаунт «{Мессенджер} {номер}»"
    )
    assert element_text(html, f"acc-del-{first_twin}-text") == f"WhatsApp {UNKNOWN_TEXT} #{first_twin}"
    assert element_text(html, f"acc-del-{second_twin}-text") == f"WhatsApp {UNKNOWN_TEXT} #{second_twin}", (
        "без #id двойники в модалке удаления неразличимы — удалят не тот аккаунт"
    )
