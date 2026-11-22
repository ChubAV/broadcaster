"""Ручная правка номера на экране групп аккаунта — `POST /accounts/{id}/phone` (Фаза 18, план 18-02).

PHONE-09 / PHONE-10 / PHONE-11. Форма стоит в шапке экрана `/accounts/{id}/groups`
и работает на ОБОИХ транспортах: без JS браузер отправляет её сам и получает
перенаправление обратно на экран с кодом исхода, с JS слой письма получает
фрагмент без перезагрузки.

Номер в базу пишет ТОЛЬКО `set_manual_phone` (писатель Фазы 16): маршрут владельца
сам проверяет, потому что писатель его не проверяет (T-16-19, закрывается здесь).

ПОСТЫ ИДУТ НА ЛИТЕРАЛЬНЫЕ АДРЕСА. Гейт полноты утверждений о переходах
(`tests/test_pages/test_htmx_post_pairs.py`) разбирает адрес запроса по f-строке с
идентификатором и сличает с таблицей маршрутов приложения; помощник, оборачивающий
POST, спрятал бы адрес от него. Поэтому каждый запрос написан по месту.

ЧИСЛО УТВЕРЖДЕНИЙ О ПЕРЕХОДЕ ЗДЕСЬ ЗАФИКСИРОВАНО И ДВИГАЕТ ОБЪЯВЛЕННОЕ ЧИСЛО ГЕЙТА
НА ДВА: по одному утверждению в двух тестах (сохранение и очистка). Остальные тесты
модуля статус перехода между ответами СРАВНИВАЮТ и числом не утверждают — иначе
объявленное число гейта разошлось бы с этим файлом.
"""

from html.parser import HTMLParser

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.accounts.phone import (
    PhoneWrite,
    fill_reported_phone,
    set_manual_phone,
)
from app.models.messenger_account import MessengerAccount
from app.models.user import User
from app.pages.identifiers import ID_MAX
from app.services.phone import (
    EXAMPLE_PHONE,
    PHONE_ERROR_BLANK,
    PHONE_ERROR_NOT_A_NUMBER,
    PHONE_ERROR_TOO_LONG,
)
from tests.account_label_support import (
    MANUAL_MARK,
    element_text,
    label_texts,
    seed_account,
)

HTMX = {"HX-Request": "true"}
DISPLAY_FORM = "+7 999 123-45-67"
STORED_FORM = "+79991234567"


@pytest_asyncio.fixture
async def owner(authed_client: AsyncClient, db_session: AsyncSession) -> User:
    return (
        await db_session.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _stored(db: AsyncSession, account_id: int) -> tuple[str | None, bool]:
    """Номер и признак ручного ввода, прочитанные из базы после `expire_all`."""
    db.expire_all()
    row = (
        await db.execute(
            select(MessengerAccount.phone, MessengerAccount.phone_is_manual).where(
                MessengerAccount.id == account_id
            )
        )
    ).one()
    return row.phone, row.phone_is_manual


async def _foreign_user(db: AsyncSession) -> User:
    other = User(email="foreign@test.com", password_hash="x", name="Foreign")
    db.add(other)
    await db.commit()
    await db.refresh(other)
    return other


class _Screen(HTMLParser):
    """Разбор экрана групп: форма номера, её поле, подсказка и положение внутри шапки."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[tuple[str, bool, bool]] = []  # (тег, в шапке, в контейнере формы)
        self.phone_forms: list[tuple[dict[str, str], bool]] = []
        self.phone_inputs: list[tuple[dict[str, str], bool]] = []
        self.container_in_head = False
        self.container_text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {k: (v if v is not None else "") for k, v in attrs}
        in_head = any(flag for _t, flag, _c in self._stack) or "data-acct-head" in a
        in_box = any(flag for _t, _h, flag in self._stack) or a.get("id") == "acct-phone"
        if a.get("id") == "acct-phone":
            self.container_in_head = in_head
        if tag == "form" and a.get("action", "").endswith("/phone"):
            self.phone_forms.append((a, in_head))
        if tag == "input" and a.get("name") == "phone":
            self.phone_inputs.append((a, in_head))
        if tag not in {"input", "br", "hr", "img", "link", "meta"}:
            self._stack.append((tag, "data-acct-head" in a, a.get("id") == "acct-phone"))

    def handle_data(self, data: str) -> None:
        if any(flag for _t, _h, flag in self._stack):
            self.container_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        for pos in range(len(self._stack) - 1, -1, -1):
            if self._stack[pos][0] == tag:
                del self._stack[pos:]
                break


def _screen(html: str) -> _Screen:
    parser = _Screen()
    parser.feed(html)
    parser.close()
    return parser


class _OobBlocks(HTMLParser):
    """Внеполосные блоки ответа: значение признака подмены, внутренний текст и число потомков.

    Считаются только блоки верхнего уровня; вложенный в блок элемент в счёт не идёт,
    а увеличивает `children` своего блока.
    """

    _VOID = frozenset({"input", "br", "hr", "img", "link", "meta"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict[str, object]] = []
        self._current: dict[str, object] | None = None
        self._depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if self._current is not None:
            self._current["children"] = int(self._current["children"]) + 1  # type: ignore[arg-type]
            if tag not in self._VOID:
                self._depth += 1
            return
        a = {k: (v if v is not None else "") for k, v in attrs}
        if "hx-swap-oob" in a:
            self._current = {"value": a["hx-swap-oob"], "text": "", "children": 0}
            self.blocks.append(self._current)
            self._depth = 1

    def handle_data(self, data: str) -> None:
        if self._current is not None:
            self._current["text"] = str(self._current["text"]) + data

    def handle_endtag(self, tag: str) -> None:
        if self._current is not None:
            self._depth -= 1
            if self._depth == 0:
                self._current = None


def _oob_blocks(html: str) -> list[dict[str, object]]:
    parser = _OobBlocks()
    parser.feed(html)
    parser.close()
    return parser.blocks


def _echoed_value(html: str) -> str | None:
    """Значение поля `phone` в ответе (единственного)."""
    inputs = _screen(html).phone_inputs
    assert len(inputs) == 1, f"поле номера стоит {len(inputs)} раз, ожидалось одно"
    return inputs[0][0].get("value")


# --- 1. Трассер ---------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "raw",
    ["8 999 123 45 67", "+7 (999) 123-45-67", DISPLAY_FORM],
    ids=["eight_prefix", "plus7_parens", "display_form"],
)
async def test_a_valid_number_is_saved_and_the_redirect_carries_only_the_outcome_code(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, raw: str
):
    """ТРАССЕР (PHONE-09, D-02, D-13, D-16): годный ввод — запись и переход с кодом исхода.

    Без признака htmx браузер получает перенаправление обратно на экран с кодом
    `phone_saved`; номера в адресе нет, в базе — `(+79991234567, True)`.
    """
    account_id = await seed_account(db_session, owner.id, "tg_user")

    response = await authed_client.post(
        f"/accounts/{account_id}/phone", data={"phone": raw}, follow_redirects=False
    )

    assert response.status_code == 302, "маршрут сохранения номера не ответил переходом"
    assert (
        response.headers["location"]
        == f"/accounts/{account_id}/groups?notice=phone_saved#phone"
    ), "адрес возврата обязан нести только код исхода"
    assert await _stored(db_session, account_id) == (STORED_FORM, True)


# --- 2. Ответ с JS ------------------------------------------------------------


@pytest.mark.asyncio
async def test_the_htmx_answer_replaces_the_form_the_headings_and_the_notice(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-13, D-14: фрагмент — `<title>`, форма, два внеполосных блока и уведомление."""
    account_id = await seed_account(db_session, owner.id, "tg_user")

    response = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": "8 999 123 45 67"},
        headers=HTMX,
        follow_redirects=False,
    )

    assert response.status_code == 200
    body = response.text
    assert body.lstrip().startswith("<title>"), "заголовок вкладки обязан быть верхним узлом ответа"
    title = body.lstrip().split("</title>")[0]
    assert f"Telegram {DISPLAY_FORM} — группы аккаунта" in title
    assert 'id="acct-phone"' in body
    assert 'hx-swap-oob="innerHTML:#acct-head-name"' in body
    assert 'hx-swap-oob="innerHTML:#page-title"' in body
    labels = label_texts(body)[str(account_id)]
    assert len(labels) == 2 and all(
        text == f"Telegram {DISPLAY_FORM} {MANUAL_MARK}" for text in labels
    ), f"подпись в ответе устарела или без пометки: {labels}"
    assert "Номер сохранён." in body
    assert "<!DOCTYPE" not in body
    lowered = {name.lower() for name in response.headers}
    assert "hx-location" not in lowered and "hx-redirect" not in lowered


# --- 3. Экран -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_the_screen_carries_the_phone_form_in_the_account_head(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-04, D-11: форма стоит в шапке, видна всегда, действие и `hx-post` равны."""
    with_phone = await seed_account(db_session, owner.id, "tg_user", phone=STORED_FORM)
    without_phone = await seed_account(db_session, owner.id, "wa")

    page = await authed_client.get(f"/accounts/{with_phone}/groups")
    assert page.status_code == 200
    html = page.text
    screen = _screen(html)

    assert len(screen.phone_forms) == 1, "на экране ровно одна форма номера"
    form, form_in_head = screen.phone_forms[0]
    assert form_in_head, "форма номера обязана стоять внутри шапки аккаунта"
    assert screen.container_in_head
    assert form["method"] == "post"
    assert form["action"] == f"/accounts/{with_phone}/phone"
    assert form["hx-post"] == form["action"]

    (field, _in_head) = screen.phone_inputs[0]
    assert field["type"] == "tel"
    assert field["id"] == "phone"
    assert field["value"] == DISPLAY_FORM
    assert field["autocomplete"] == "off"
    assert field["inputmode"] == "tel"
    assert field["maxlength"] == "64"
    assert "required" not in field, "пустое поле означает очистку, а не ошибку"
    text = " ".join("".join(screen.container_text).split())
    assert f"Пример: {EXAMPLE_PHONE}" in text
    assert "Сохранить" in text
    assert html.count('id="acct-head-name"') == 1
    assert html.count('id="page-title"') == 1

    empty_page = await authed_client.get(f"/accounts/{without_phone}/groups")
    empty_field = _screen(empty_page.text).phone_inputs[0][0]
    assert empty_field["value"] == ""


# --- 4. Неверный ввод ---------------------------------------------------------


@pytest.mark.asyncio
async def test_an_invalid_number_answers_422_with_the_echo_on_both_transports(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-03, критерий 2: 422 с эхом и текстом константы; без уведомления на обоих транспортах."""
    account_id = await seed_account(db_session, owner.id, "tg_user", manual_phone="8 999 123 45 67")

    plain = await authed_client.post(
        f"/accounts/{account_id}/phone", data={"phone": "abc"}, follow_redirects=False
    )
    assert plain.status_code == 422
    assert "<!DOCTYPE" in plain.text and "data-acct-head" in plain.text
    assert _echoed_value(plain.text) == "abc"
    assert PHONE_ERROR_NOT_A_NUMBER in plain.text
    assert element_text(plain.text, "notice") == ""
    assert element_text(plain.text, "notice-alert") == ""

    fragment = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": "abc"},
        headers=HTMX,
        follow_redirects=False,
    )
    assert fragment.status_code == 422
    assert "<!DOCTYPE" not in fragment.text
    assert _echoed_value(fragment.text) == "abc"
    assert PHONE_ERROR_NOT_A_NUMBER in fragment.text
    fragment_blocks = _oob_blocks(fragment.text)
    assert [block["value"] for block in fragment_blocks] == ["innerHTML:#notice"], (
        "единственный внеполосный блок 422 — пустая подмена содержимого `#notice`"
    )
    assert not [name for name in fragment.headers if name.lower().startswith("hx-")]

    too_long = await authed_client.post(
        f"/accounts/{account_id}/phone", data={"phone": "9" * 33}, follow_redirects=False
    )
    assert too_long.status_code == 422
    assert PHONE_ERROR_TOO_LONG in too_long.text

    hostile = '"><script>alert(1)</script>'
    attack = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": hostile},
        headers=HTMX,
        follow_redirects=False,
    )
    assert attack.status_code == 422
    assert "<script>alert(1)" not in attack.text, "эхо введённого обязано быть экранировано"
    assert "&lt;script&gt;" in attack.text

    for response in (plain, fragment, too_long, attack):
        for word in ("phone_saved", "phone_cleared", "Номер сохранён.", "Номер удалён."):
            assert word not in response.text
            assert word not in " ".join(response.headers.values())
    assert await _stored(db_session, account_id) == (STORED_FORM, True), (
        "неверный ввод не имеет права менять номер в базе"
    )


@pytest.mark.asyncio
async def test_a_422_htmx_answer_clears_the_previous_notice(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """ТРАССЕР (D-13, D-03, D-16, OBS-422): 422 с JS снимает плашку прошлого сохранения.

    После годного сохранения вежливая область несёт «Номер сохранён.»; ответ 422 на
    следующий неверный ввод обязан опустошить её пустым блоком подмены содержимого
    `#notice`: ни текста, ни потомков, ни кода исхода, ни цифр номера. Настойчивую
    область `#notice-alert` ответ не трогает.
    """
    account_id = await seed_account(db_session, owner.id, "tg_user")

    saved = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": "8 999 123 45 67"},
        headers=HTMX,
        follow_redirects=False,
    )
    assert saved.status_code == 200
    assert "Номер сохранён." in saved.text

    refused = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": "abc"},
        headers=HTMX,
        follow_redirects=False,
    )
    assert refused.status_code == 422
    blocks = _oob_blocks(refused.text)
    assert [block["value"] for block in blocks] == ["innerHTML:#notice"], (
        "422 с JS не снимает прежнюю плашку"
    )
    (block,) = blocks
    assert str(block["text"]).strip() == "" and block["children"] == 0, (
        "блок, снимающий плашку, обязан быть пустым"
    )
    assert "#notice-alert" not in refused.text
    for leaked in ("phone_saved", "phone_cleared", "Номер сохранён.", "Номер удалён.", "9991234567"):
        assert leaked not in refused.text, f"в ответе 422 стоит {leaked!r}"
    assert PHONE_ERROR_NOT_A_NUMBER in refused.text
    assert _echoed_value(refused.text) == "abc"


# --- 5. Очистка ---------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("blank", ["", "   ", " " * 40], ids=["empty", "spaces", "long_spaces"])
async def test_an_empty_field_clears_the_number_and_never_shows_the_blank_error(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, blank: str
):
    """D-09 (PHONE-09, PHONE-10): пустое и пробельное поле — очистка, а не ошибка."""
    account_id = await seed_account(db_session, owner.id, "tg_user", manual_phone="8 999 123 45 67")

    response = await authed_client.post(
        f"/accounts/{account_id}/phone", data={"phone": blank}, follow_redirects=False
    )

    assert response.status_code == 302, "очистка обязана отвечать переходом, а не отказом"
    assert response.headers["location"].endswith("?notice=phone_cleared#phone")
    assert PHONE_ERROR_BLANK not in response.text
    assert await _stored(db_session, account_id) == (None, False)

    saved_again = await set_manual_phone(db_session, account_id, "8 999 123 45 67")
    assert saved_again == STORED_FORM
    await db_session.commit()
    fragment = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": blank},
        headers=HTMX,
        follow_redirects=False,
    )
    assert fragment.status_code == 200
    assert "Номер удалён." in fragment.text
    assert PHONE_ERROR_BLANK not in fragment.text
    labels = label_texts(fragment.text)[str(account_id)]
    assert labels and all(text == "Telegram Номер неизвестен" for text in labels), labels
    assert all(MANUAL_MARK not in text for text in labels)


# --- 6. Поля нет --------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_post_without_the_field_leaves_the_number_untouched(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Pitfall 3, T-18-08: запрос без поля `phone` — отказ разбора, а не очистка."""
    account_id = await seed_account(db_session, owner.id, "tg_user", manual_phone="8 999 123 45 67")

    plain = await authed_client.post(
        f"/accounts/{account_id}/phone", data={"unrelated": "x"}, follow_redirects=False
    )
    fragment = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"unrelated": "x"},
        headers=HTMX,
        follow_redirects=False,
    )

    assert plain.status_code == 422
    assert fragment.status_code == 400 and fragment.content == b""
    assert await _stored(db_session, account_id) == (STORED_FORM, True)


# --- 7. Чужой, несуществующий, вне колонки ------------------------------------


@pytest.mark.asyncio
async def test_a_foreign_a_missing_and_an_out_of_column_account_answer_alike(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-05, T-18-04: три случая неразличимы по статусу, адресу и телу; номер чужого цел."""
    other = await _foreign_user(db_session)
    foreign_id = await seed_account(db_session, other.id, "tg_user", phone="+79995550000")
    missing_id = foreign_id + 500
    cases = {
        "foreign": foreign_id,
        "missing": missing_id,
        "out_of_column": ID_MAX + 1,
    }

    plain = {}
    for name, account_id in cases.items():
        response = await authed_client.post(
            f"/accounts/{account_id}/phone",
            data={"phone": "8 999 123 45 67"},
            follow_redirects=False,
        )
        plain[name] = (response.status_code, response.headers.get("location"), response.content)
    assert plain["foreign"] == plain["missing"] == plain["out_of_column"], plain
    assert plain["foreign"][1] == "/accounts"

    fragments = {}
    for name, account_id in cases.items():
        response = await authed_client.post(
            f"/accounts/{account_id}/phone",
            data={"phone": "8 999 123 45 67"},
            headers=HTMX,
            follow_redirects=False,
        )
        fragments[name] = (response.status_code, response.headers.get("hx-location"), response.content)
    assert fragments["foreign"] == fragments["missing"] == fragments["out_of_column"], fragments
    assert fragments["foreign"][0] == 204 and fragments["foreign"][1]

    assert await _stored(db_session, foreign_id) == ("+79995550000", False)


@pytest.mark.asyncio
async def test_a_writer_lookup_error_answers_like_a_missing_account(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    owner: User,
    monkeypatch: pytest.MonkeyPatch,
):
    """D-05: строку удалили между проверкой и записью — ответ как у несуществующего."""
    account_id = await seed_account(db_session, owner.id, "tg_user")

    missing = await authed_client.post(
        f"/accounts/{account_id + 500}/phone",
        data={"phone": "8 999 123 45 67"},
        follow_redirects=False,
    )

    async def _gone(*_args, **_kwargs):
        raise LookupError("аккаунт удалён")

    monkeypatch.setattr("app.pages.account_groups.set_manual_phone", _gone)
    raced = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": "8 999 123 45 67"},
        follow_redirects=False,
    )

    assert (raced.status_code, raced.headers.get("location"), raced.content) == (
        missing.status_code,
        missing.headers.get("location"),
        missing.content,
    )


# --- 9. Источник запроса ------------------------------------------------------


@pytest.mark.asyncio
async def test_a_cross_origin_post_is_refused_before_any_lookup(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """T-18-05: чужой источник — 403 с пустым телом ДО выборки; ответы равны."""
    account_id = await seed_account(db_session, owner.id, "tg_user", phone="+79995550000")
    hostile_origin = {"Origin": "http://evil.example"}

    own = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": "8 999 123 45 67"},
        headers=hostile_origin,
        follow_redirects=False,
    )
    missing = await authed_client.post(
        f"/accounts/{account_id + 500}/phone",
        data={"phone": "8 999 123 45 67"},
        headers=hostile_origin,
        follow_redirects=False,
    )

    assert own.status_code == 403 and own.content == b""
    assert (own.status_code, own.content) == (missing.status_code, missing.content)
    assert await _stored(db_session, account_id) == ("+79995550000", False)


# --- 10. Приватность ----------------------------------------------------------


@pytest.mark.asyncio
async def test_the_number_reaches_neither_the_address_nor_the_notice_nor_the_log(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User, caplog
):
    """D-16, PHONE-21, T-18-07: журнал — `account_id` и `phone_set`; номера нет нигде."""
    account_id = await seed_account(db_session, owner.id, "tg_user")

    with caplog.at_level("INFO", logger="app.pages.account_groups"):
        response = await authed_client.post(
            f"/accounts/{account_id}/phone",
            data={"phone": "8 999 123 45 67"},
            follow_redirects=False,
        )

    entries = [
        record.msg
        for record in caplog.records
        if isinstance(record.msg, dict) and record.msg.get("event") == "account_phone_saved"
    ]
    assert len(entries) == 1, f"событие правки номера должно быть одно: {entries}"
    entry = entries[0]
    assert entry.get("account_id") == account_id
    assert entry.get("phone_set") is True
    for key in ("phone", "text", "saved"):
        assert key not in entry, f"ключ {key!r} несёт номер в журнал"
    assert "9991234567" not in str(entry)

    location = response.headers["location"]
    assert "9991234567" not in location
    landed = await authed_client.get(location.split("#")[0])
    notice = element_text(landed.text, "notice") or ""
    assert notice and not any(ch.isdigit() for ch in notice), notice


# --- Закрепляющие: свежая подпись, дубликат, без правки, критерий 3 ----------


@pytest.mark.asyncio
async def test_the_answer_shows_the_saved_number_not_the_stale_object(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-14: подпись ответа строится из перечитанных данных, а не из устаревшего объекта."""
    account_id = await seed_account(db_session, owner.id, "tg_user", phone="+79990000000")

    response = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": DISPLAY_FORM},
        headers=HTMX,
        follow_redirects=False,
    )

    assert response.status_code == 200
    labels = label_texts(response.text)[str(account_id)]
    assert labels and all(text == f"Telegram {DISPLAY_FORM} {MANUAL_MARK}" for text in labels), labels
    assert "+7 999 000-00-00" not in response.text


@pytest.mark.asyncio
async def test_the_same_number_on_two_accounts_makes_them_twins_without_a_refusal(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-15: номер, совпавший с номером другого аккаунта, принимается молча; оба — двойники."""
    first = await seed_account(db_session, owner.id, "tg_user", phone=STORED_FORM)
    second = await seed_account(db_session, owner.id, "tg_user")

    response = await authed_client.post(
        f"/accounts/{second}/phone", data={"phone": DISPLAY_FORM}, follow_redirects=False
    )

    assert response.headers["location"] == f"/accounts/{second}/groups?notice=phone_saved#phone"
    listing = await authed_client.get("/accounts")
    texts = label_texts(listing.text)
    assert texts[str(first)] and all(text.endswith(f"#{first}") for text in texts[str(first)])
    assert texts[str(second)] and all(text.endswith(f"#{second}") for text in texts[str(second)])


@pytest.mark.asyncio
async def test_saving_an_automatic_number_unchanged_makes_it_manual(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """Решение владельца 2026-11-21: «Сохранить» без правки делает автономер ручным."""
    account_id = await seed_account(db_session, owner.id, "tg_user", phone=STORED_FORM)
    assert await _stored(db_session, account_id) == (STORED_FORM, False)

    await authed_client.post(
        f"/accounts/{account_id}/phone", data={"phone": DISPLAY_FORM}, follow_redirects=False
    )

    assert await _stored(db_session, account_id) == (STORED_FORM, True)
    page = await authed_client.get(f"/accounts/{account_id}/groups")
    assert any(MANUAL_MARK in text for text in label_texts(page.text)[str(account_id)])


@pytest.mark.asyncio
async def test_after_the_clearing_an_automatic_source_may_fill_the_number_again(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """D-07, критерий 3: ручной номер — `KEPT`; после очистки — `WRITTEN`, пометки нет."""
    account_id = await seed_account(db_session, owner.id, "tg_user")

    await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": "8 999 123 45 67"},
        follow_redirects=False,
    )
    assert await fill_reported_phone(db_session, account_id, "+79995556677") is PhoneWrite.KEPT
    await db_session.commit()

    await authed_client.post(
        f"/accounts/{account_id}/phone", data={"phone": ""}, follow_redirects=False
    )
    assert await fill_reported_phone(db_session, account_id, "+79995556677") is PhoneWrite.WRITTEN
    await db_session.commit()

    page = await authed_client.get(f"/accounts/{account_id}/groups")
    labels = label_texts(page.text)[str(account_id)]
    assert labels and all(text == "Telegram +7 999 555-66-77" for text in labels), labels


# --- 5. Фокус после ответа (Фаза 18, план 18-05, UI-P1 = IN-01) ----------------


@pytest.mark.asyncio
async def test_the_answer_to_a_submission_puts_focus_back_into_the_field(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """ТРАССЕР (UI-P1, IN-01): ответ на отправку несёт `autofocus` у поля номера.

    Три ответа: успех с JS (200), 422 с JS и страница 422 без JS. Рантайм htmx
    фокусирует `[autofocus]` в подменённом содержимом, поэтому на 422 текст
    ошибки озвучивается вместе с именем поля.
    """
    account_id = await seed_account(db_session, owner.id, "tg_user")

    saved = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": DISPLAY_FORM},
        headers=HTMX,
        follow_redirects=False,
    )
    assert saved.status_code == 200
    refused_fragment = await authed_client.post(
        f"/accounts/{account_id}/phone",
        data={"phone": "abc"},
        headers=HTMX,
        follow_redirects=False,
    )
    assert refused_fragment.status_code == 422
    refused_page = await authed_client.post(
        f"/accounts/{account_id}/phone", data={"phone": "abc"}, follow_redirects=False
    )
    assert refused_page.status_code == 422

    for name, response in (
        ("успех с JS", saved),
        ("422 с JS", refused_fragment),
        ("422 без JS", refused_page),
    ):
        (field, _in_head) = _screen(response.text).phone_inputs[0]
        assert "autofocus" in field, (
            f"{name}: после ответа фокус не возвращается в поле номера"
        )


@pytest.mark.asyncio
async def test_the_plain_screen_never_autofocuses_the_field(
    authed_client: AsyncClient, db_session: AsyncSession, owner: User
):
    """T-18-21: обычный показ экрана и посадка после перехода без JS фокус не отнимают."""
    account_id = await seed_account(db_session, owner.id, "tg_user", phone=STORED_FORM)

    shown = await authed_client.get(f"/accounts/{account_id}/groups")
    landed = await authed_client.get(f"/accounts/{account_id}/groups?notice=phone_saved")

    for name, response in (("обычный показ", shown), ("посадка после перехода", landed)):
        assert response.status_code == 200
        assert "autofocus" not in response.text, f"{name}: экран отнимает фокус у человека"
        assert _screen(response.text).phone_inputs, f"{name}: поля номера нет"
