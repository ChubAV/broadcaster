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

from app.application.accounts.use_cases import get_sync_status_view
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


# --- Порция подгрузки /accounts/partial --------------------------------------


@pytest.mark.asyncio
async def test_the_partial_batch_shows_the_number_at_its_address(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """PHONE-03: подгруженная карточка подписана номером по тому же адресу, что и страница."""
    await seed_account(db_session, owner.id, "tg_user", phone="+79001112233")
    middle = await seed_account(db_session, owner.id, "tg_user", phone="+79991234567")
    await seed_account(db_session, owner.id, "max", phone="+79005556677")

    html = (await authed_client.get("/accounts/partial?offset=1&limit=1")).text
    labels = label_texts(html)

    assert labels[str(middle)] == [NUMBER_TEXT], "порция несёт номер второго аккаунта по адресу"
    assert list(labels) == [str(middle)], "порция offset=1&limit=1 несёт ровно одну подпись"


@pytest.mark.asyncio
async def test_a_twin_split_across_the_page_and_the_batch_is_marked_in_both(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-14: двойник по ту сторону границы страницы из 30 помечен там и здесь.

    Первый `wa` без номера лежит на странице, последний — за её границей (на
    31-м месте), в порции. Признак считается по ВСЕМ аккаунтам пользователя:
    будь он по странице или по порции, каждый из двух видел бы только себя и
    остался бы без `#id`.
    """
    first = await seed_account(db_session, owner.id, "wa")
    for _ in range(29):
        await seed_account(db_session, owner.id, "max")
    last = await seed_account(db_session, owner.id, "wa")

    page = label_texts((await authed_client.get("/accounts")).text)
    batch = label_texts((await authed_client.get("/accounts/partial?offset=30&limit=5")).text)

    assert str(last) not in page, "последний аккаунт лежит за границей страницы из 30"
    assert page[str(first)] == [f"{UNKNOWN_TEXT} #{first}"], "двойник на странице несёт #id"
    assert batch[str(last)] == [f"{UNKNOWN_TEXT} #{last}"], "двойник в порции несёт #id"


@pytest.mark.asyncio
async def test_the_batch_delete_modal_carries_the_plain_label(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-13: модалка удаления подгруженной карточки называет аккаунт плоской подписью."""
    await seed_account(db_session, owner.id, "max")
    numbered = await seed_account(db_session, owner.id, "tg_user", phone="+79991234567")
    twin = await seed_account(db_session, owner.id, "wa")
    other_twin = await seed_account(db_session, owner.id, "wa")

    html = (await authed_client.get("/accounts/partial?offset=1&limit=5")).text

    assert element_text(html, f"acc-del-{numbered}-text") == f"Telegram {NUMBER_TEXT}"
    assert element_text(html, f"acc-del-{twin}-text") == f"WhatsApp {UNKNOWN_TEXT} #{twin}"
    assert element_text(html, f"acc-del-{other_twin}-text") == f"WhatsApp {UNKNOWN_TEXT} #{other_twin}"


# --- Фрагмент опроса /accounts/{id}/sync-status ------------------------------


@pytest.mark.asyncio
async def test_the_poll_fragment_shows_the_number_at_its_address(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """PHONE-03, D-18: подменённая опросом карточка не теряет номер.

    Фрагмент рисуется отдельным `.render(...)` без объекта аккаунта: забытый
    ключ контекста при мягком `Undefined` напечатал бы пустоту, а страница
    ответила бы 200. Подпись идёт ОБЪЕКТОМ, и тест читает её по адресу.
    """
    account_id = await seed_account(db_session, owner.id, "tg_user", phone="+79991234567", status="syncing")

    html = (await authed_client.get(f"/accounts/{account_id}/sync-status")).text

    assert label_texts(html)[str(account_id)] == [NUMBER_TEXT], (
        "фрагмент опроса должен показывать номер по адресу data-account-label"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["active", "syncing", "sync_failed"])
async def test_the_poll_fragment_reads_as_unknown_in_every_status(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, status: str
):
    """PHONE-04, D-02: «Номер неизвестен» и во фрагменте опроса, а не только на странице."""
    account_id = await seed_account(db_session, owner.id, "wa", status=status)

    html = (await authed_client.get(f"/accounts/{account_id}/sync-status")).text

    assert label_texts(html)[str(account_id)] == [UNKNOWN_TEXT], (
        f"статус {status}: подпись фрагмента опроса — «Номер неизвестен» без #id"
    )
    assert str(account_id) in muted_label_ids(html), f"статус {status}: «Номер неизвестен» приглушён"


@pytest.mark.asyncio
async def test_the_poll_fragment_marks_a_twin(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """PHONE-05, D-14: двойник помечен и во фрагменте, признак считается по строкам пользователя."""
    polled = await seed_account(db_session, owner.id, "wa", status="syncing")
    neighbour = await seed_account(db_session, owner.id, "wa")
    alone = await seed_account(db_session, owner.id, "max", status="active")

    polled_html = (await authed_client.get(f"/accounts/{polled}/sync-status")).text
    alone_html = (await authed_client.get(f"/accounts/{alone}/sync-status")).text

    assert label_texts(polled_html)[str(polled)] == [f"{UNKNOWN_TEXT} #{polled}"], (
        f"двойник (соседний аккаунт {neighbour}) несёт #id и во фрагменте опроса"
    )
    assert label_texts(alone_html)[str(alone)] == [UNKNOWN_TEXT], "уникальная подпись — без #id"


@pytest.mark.asyncio
async def test_a_foreign_account_poll_draws_no_label(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """T-17-05: опрос чужого аккаунта не рисует его номер — владение проверяет загрузчик вида."""
    stranger = await _stranger(db_session)
    foreign = await seed_account(db_session, stranger, "tg_user", phone="+79991234567", status="syncing")

    html = (await authed_client.get(f"/accounts/{foreign}/sync-status")).text

    assert "Аккаунт не найден" in html
    assert "data-account-label" not in html, "подпись чужого аккаунта не должна попасть в ответ"
    assert NUMBER_TEXT not in html, "номер чужого аккаунта не должен попасть в ответ"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["active", "sync_failed", "syncing", "connecting"])
async def test_the_sync_status_view_carries_the_phone_in_every_branch(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, status: str
):
    """D-18: `SyncStatusView.phone` заполняют все четыре конструктора."""
    numbered = await seed_account(db_session, owner.id, "tg_user", phone="+79991234567", status=status)
    bare = await seed_account(db_session, owner.id, "wa", status=status)

    numbered_view = await get_sync_status_view(db_session, owner.id, numbered)
    bare_view = await get_sync_status_view(db_session, owner.id, bare)

    assert numbered_view is not None and numbered_view.phone == "+79991234567"
    assert bare_view is not None and bare_view.phone is None
