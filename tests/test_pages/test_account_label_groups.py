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

from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from tests.account_label_support import (
    MANUAL_MARK,
    label_texts,
    muted_label_ids,
    seed_account,
    title_text,
)

TEMPLATE = Path(__file__).resolve().parents[2] / "app" / "templates" / "account_groups" / "list.html"

HOSTILE = '"><script>alert(1)</script>'


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


@pytest.mark.asyncio
async def test_a_twin_header_and_title_carry_the_id(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """PHONE-05 / D-03 / D-14: у двойника `#id` стоит в обоих заголовках и в `<title>`.

    Два WhatsApp без номера — подписи совпали. Признак считается по ВСЕМ аккаунтам
    пользователя, поэтому первый экран помечен так же, как была бы его карточка в списке.
    """
    first_id = await seed_account(db_session, owner.id, "wa")
    await seed_account(db_session, owner.id, "wa")

    html = await _groups_html(authed_client, first_id)

    expected = f"WhatsApp Номер неизвестен #{first_id}"
    assert label_texts(html)[str(first_id)] == [expected, expected]
    assert title_text(html).startswith(f"{expected} — "), (
        f"<title> двойника обязан нести #id простым текстом: {title_text(html)!r}"
    )


@pytest.mark.asyncio
async def test_a_hostile_stored_value_is_escaped_in_every_header_sink(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-07 / T-17-09: неразбираемое значение колонки — «как есть», но текстом.

    Приёмников три: `<title>`, шелловый `<h1>` и `<h2>` карточки. Ни в одном из них
    значение не становится живой разметкой.
    """
    account_id = await seed_account(db_session, owner.id, "tg_user", stored_as_is=HOSTILE)

    html = await _groups_html(authed_client, account_id)

    assert "<script>alert(1)" not in html, "значение колонки попало в ответ живым <script>"
    assert label_texts(html)[str(account_id)] == [f"Telegram {HOSTILE}"] * 2
    assert HOSTILE in title_text(html), "в <title> значение обязано читаться текстом"


@pytest.mark.asyncio
async def test_a_manual_number_is_marked_in_both_headings_but_not_in_the_title(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """ТРАССЕР (PHONE-08, D-10): ручной номер несёт пометку в `<h1>` и `<h2>`, `<title>` — без неё."""
    account_id = await seed_account(db_session, owner.id, "tg_user", manual_phone="8 999 123 45 67")

    html = await _groups_html(authed_client, account_id)

    expected = f"Telegram +7 999 123-45-67 {MANUAL_MARK}"
    assert label_texts(html)[str(account_id)] == [expected, expected], (
        "оба заголовка экрана групп обязаны нести пометку после номера"
    )
    assert MANUAL_MARK not in title_text(html), "в плоской форме (<title>) пометки нет (D-10)"


@pytest.mark.asyncio
async def test_a_manual_twin_reads_number_mark_then_id(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-10, порядок: номер → «указан вручную» → `#id` двойника."""
    manual_id = await seed_account(db_session, owner.id, "tg_user", manual_phone="8 999 123 45 67")
    automatic_id = await seed_account(db_session, owner.id, "tg_user", phone="+79991234567")

    html = await _groups_html(authed_client, manual_id)

    expected = f"Telegram +7 999 123-45-67 {MANUAL_MARK} #{manual_id}"
    assert label_texts(html)[str(manual_id)] == [expected, expected]
    assert automatic_id != manual_id


def test_the_header_prose_no_longer_denies_the_phone_column():
    """Комментарий шапки не отрицает колонку номера: Фаза 16 её завела.

    Фраза-отрицание собирается из двух половин, чтобы сам модуль теста не был её
    носителем; сравнение идёт по тексту без пробелов и переводов строк, чтобы перенос
    строки в комментарии не прятал её.
    """
    glued = "".join(TEMPLATE.read_text(encoding="utf-8").split()).lower()
    denials = (
        "колонкителефона" + "уаккаунтанесуществует",
        "телефонавстроке" + "нетибытьнеможет",
    )

    for denial in denials:
        assert denial not in glued, (
            "проза шапки всё ещё отрицает колонку телефона у аккаунта: "
            "номер берётся из `phone` через помощника подписи"
        )
