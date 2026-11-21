"""Ссылка к полю номера на карточке аккаунта (Фаза 18, план 18-03, PHONE-09).

С карточки аккаунта к ручной правке номера ведёт ссылка «Указать номер» (номер
неизвестен) или «Изменить» (номер есть) на `/accounts/{id}/groups#phone` — якорь
стоит на поле формы плана 18-02 (D-01, D-12). Ссылка GET: формы и нового адреса
записи она не заводит, поэтому числа сквозных гейтов этот модуль не двигает (D-08).

АДРЕС, А НЕ ПОДСТРОКА. Ссылка находится разбором `html.parser` по `href`, равному
`/accounts/{id}/groups#phone`: подстрока `#phone` встречается у ссылок соседних
аккаунтов, а слово «Изменить» стоит и на других кнопках страницы. Идентификатор
аккаунта — часть адреса, поэтому ссылка соседа найденной не засчитывается.

Тесты этого модуля POST не шлют и утверждений о коде перехода не пишут: число
таких утверждений в тестовых модулях считает гейт `test_htmx_post_pairs.py`.
"""

from __future__ import annotations

from html.parser import HTMLParser

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from tests.account_label_support import seed_account

NUMBER = "+79991234567"
NUMBER_DIGITS = "9991234567"
WORD_WITH_NUMBER = "Изменить"
WORD_WITHOUT_NUMBER = "Указать номер"
STATUSES = ["active", "syncing", "sync_failed"]


class _Page(HTMLParser):
    """Один проход: ссылки (адрес и текст), поля форм и контейнер правки номера."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        # Ссылки в порядке документа: [href, куски текста]; открытая — на вершине счётчика.
        self.anchors: list[list] = []
        self._open_anchor: int | None = None
        self.has_phone_container = False
        # Поля `id="phone"`: (тег, внутри ли контейнера правки, action охватывающей формы).
        self.phone_fields: list[tuple[str, bool, str | None]] = []
        self._container_depth: int | None = None
        self._depth = 0
        self._form_action: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v if v is not None else "") for k, v in attrs}
        if tag in {"br", "hr", "img", "input", "link", "meta"}:
            void = True
        else:
            void = False
        if "data-acct-phone" in a:
            self.has_phone_container = True
            self._container_depth = self._depth
        if tag == "form":
            self._form_action = a.get("action")
        if tag == "a" and "href" in a:
            self.anchors.append([a["href"], []])
            self._open_anchor = len(self.anchors) - 1
        if a.get("id") == "phone":
            inside = self._container_depth is not None and self._depth > self._container_depth
            self.phone_fields.append((tag, inside, self._form_action))
        if not void:
            self._depth += 1

    def handle_data(self, data: str) -> None:
        if self._open_anchor is not None:
            self.anchors[self._open_anchor][1].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self._open_anchor = None
        if tag in {"br", "hr", "img", "input", "link", "meta"}:
            return
        self._depth = max(0, self._depth - 1)
        if self._container_depth is not None and self._depth <= self._container_depth:
            self._container_depth = None
        if tag == "form":
            self._form_action = None


def _parse(html: str) -> _Page:
    page = _Page()
    page.feed(html)
    page.close()
    return page


def phone_link_texts(html: str, account_id: int) -> list[str]:
    """Тексты (пробелы схлопнуты) всех `<a>` с `href`, равным `/accounts/{id}/groups#phone`."""
    want = f"/accounts/{account_id}/groups#phone"
    return [" ".join("".join(chunks).split()) for href, chunks in _parse(html).anchors if href == want]


def _hrefs_worded(html: str) -> list[str]:
    """Адреса всех ссылок с текстом «Изменить» / «Указать номер» — без привязки к аккаунту."""
    words = {WORD_WITH_NUMBER, WORD_WITHOUT_NUMBER}
    return [href for href, chunks in _parse(html).anchors if " ".join("".join(chunks).split()) in words]


@pytest_asyncio.fixture
async def owner(db_session: AsyncSession) -> User:
    return (
        await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


# --- Страница /accounts ------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("status", STATUSES)
@pytest.mark.parametrize(
    ("phone", "word"),
    [(NUMBER, WORD_WITH_NUMBER), (None, WORD_WITHOUT_NUMBER)],
    ids=["with_number", "without_number"],
)
async def test_every_page_card_links_to_the_phone_field_with_the_right_word(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
    status: str,
    phone: str | None,
    word: str,
):
    """ТРАССЕР (PHONE-09, D-01, D-12): карточка страницы в любой ветке статуса ведёт к полю номера.

    Слово ссылки выбирает наличие номера: «Изменить», если он есть, «Указать
    номер», если неизвестен. Ветки `syncing` и `sync_failed` ссылку НЕ прячут:
    условная ветка оставила бы номер синхронизирующегося аккаунта без входа.
    """
    account_id = await seed_account(db_session, owner.id, "tg_user", phone=phone, status=status)

    html = (await authed_client.get("/accounts")).text

    assert phone_link_texts(html, account_id) == [word], (
        f"ветка {status}: карточка аккаунта {account_id} несёт одну ссылку к полю номера «{word}»"
    )


@pytest.mark.asyncio
async def test_the_phone_link_lands_on_the_phone_field_of_the_same_account(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-12: переход по ссылке (адрес без якоря) открывает экран групп того же аккаунта с полем номера.

    Якорь `#phone` браузер прокручивает сам; суита проверяет, что на экране есть
    ровно один узел `id="phone"` — поле формы внутри `[data-acct-phone]`, чья
    форма пишет в `/accounts/{id}/phone` ЭТОГО аккаунта.
    """
    other = await seed_account(db_session, owner.id, "wa", phone="+79005556677")
    account_id = await seed_account(db_session, owner.id, "tg_user", phone=NUMBER)

    cards = (await authed_client.get("/accounts")).text
    hrefs = _hrefs_worded(cards)
    want = f"/accounts/{account_id}/groups#phone"
    assert want in hrefs, f"на странице нет ссылки на {want}; ссылки со словами: {hrefs}"
    assert f"/accounts/{other}/groups#phone" in hrefs, "у соседнего аккаунта своя ссылка"

    target = want.split("#", 1)[0]
    response = await authed_client.get(target)

    assert response.status_code == 200
    page = _parse(response.text)
    assert page.has_phone_container, "на экране групп нет контейнера [data-acct-phone]"
    assert page.phone_fields == [("input", True, f"/accounts/{account_id}/phone")], (
        "якорь #phone должен стоять на одном поле формы внутри контейнера, "
        "а форма — писать в маршрут того же аккаунта"
    )


@pytest.mark.asyncio
async def test_the_phone_link_carries_no_number(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-16, T-18-15: в адресе ссылки только идентификатор аккаунта и якорь, номера нет."""
    account_id = await seed_account(db_session, owner.id, "tg_user", phone=NUMBER)

    html = (await authed_client.get("/accounts")).text
    hrefs = _hrefs_worded(html)

    assert hrefs == [f"/accounts/{account_id}/groups#phone"], "ровно одна ссылка к полю номера"
    for href in hrefs:
        assert NUMBER_DIGITS not in href, "номер не должен попасть в адрес ссылки"
        assert "%2B7" not in href.upper(), "номер не должен попасть в адрес и в закодированной форме"
