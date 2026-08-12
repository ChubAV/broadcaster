"""План 03-01: экран групп аккаунта `/accounts/{id}/groups` (GRP-04, GRP-05).

Файл закрепляет СКВОЗНОЙ срез экрана тремя слоями, и порядок именно такой:

* ВЛАДЕНИЕ. Идентификатор аккаунта приходит из URL, то есть от недоверенного
  клиента (T-03-01, T-03-02). Проверка живёт на маршруте и разметкой не
  подкрепляется, поэтому утверждается прямым запросом мимо страницы.
* СОСТАВ И ПОРЯДОК СПИСКА. Экран обязан показывать группы ИМЕННО этого
  аккаунта: ошибка в фильтре не роняет страницу, она молча подмешивает чужие
  строки. Порядок задан явной сортировкой по идентификатору — без неё порядок
  строк становится свойством плана запроса, а не контракта.
* ТУМБЛЕР. Маршрут ИНВЕРТИРУЕТ `is_active`, а не устанавливает его (D-08:
  действие обратимо одним нажатием), и НЕ трогает состав расписаний (D-05:
  выключение группы не редактирует `Schedule.group_ids`).

Утверждения идут на РЕАЛЬНЫЕ строки и адреса, а не только на код ответа: ошибка
в имени параметра макроса строки оставит страницу валидной (200), а список —
пустым (эталон — test_ads_card_renders_data).
"""

import re
from pathlib import Path
from urllib.parse import quote

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User

# Якорь строки списка. Утверждать порядок по именам групп нельзя: у двух групп
# с одинаковым именем они совпадают, а различить нужно именно строки.
GROUP_ROW_RE = re.compile(r'id="group-row-(\d+)"')

# Сентинел бесконечной прокрутки: адрес следующей порции.
SENTINEL_RE = re.compile(r'hx-get="([^"]*/groups/partial\?[^"]*)"')

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"


def _row_ids(html: str) -> list[int]:
    return [int(value) for value in GROUP_ROW_RE.findall(html)]


def _sentinels(html: str) -> list[str]:
    return SENTINEL_RE.findall(html)


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_account(
    db: AsyncSession, type_: str = "wa", user_id: int | None = None
) -> MessengerAccount:
    user = await _user(db)
    account = MessengerAccount(
        user_id=user.id if user_id is None else user_id,
        type=type_,
        credentials="session",
        status="active",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def _seed_group(
    db: AsyncSession,
    account: MessengerAccount,
    name: str,
    user_id: int | None = None,
    is_active: bool = True,
) -> Group:
    user = await _user(db)
    group = Group(
        user_id=user.id if user_id is None else user_id,
        account_id=account.id,
        messenger_type=account.type,
        group_external_id=f"ext-{name}",
        name=name,
        is_active=is_active,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def _seed_foreign_user(db: AsyncSession) -> User:
    """Второй пользователь: его аккаунт и группы недостижимы с этой сессии."""
    other = User(email="foreign@test.com", password_hash="x", name="Foreign")
    db.add(other)
    await db.commit()
    await db.refresh(other)
    return other


async def _seed_schedule(
    db: AsyncSession, account: MessengerAccount, group_ids: list[int]
) -> Schedule:
    user = await _user(db)
    ad = Ad(user_id=user.id, title="Объявление", text="Текст", images=[])
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=group_ids,
        days_of_week=[0, 2, 4],
        times_of_day=["09:30"],
        timezone="UTC",
        is_active=True,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


# --- Владение: страница ------------------------------------------------------


@pytest.mark.asyncio
async def test_page_shows_groups_of_this_account(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """GRP-04: на экране аккаунта — группы ИМЕННО этого аккаунта."""
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Барахолка Северного района")

    response = await authed_client.get(f"/accounts/{account.id}/groups")

    assert response.status_code == 200
    assert "Барахолка Северного района" in response.text, (
        "имя группы не дошло до строки списка"
    )
    assert _row_ids(response.text) == [group.id]


@pytest.mark.asyncio
async def test_page_hides_groups_of_another_account_of_the_same_user(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-02: экран привязан к аккаунту, а не к пользователю.

    Парный тест к предыдущему: без него фильтр по `account_id` мог бы вовсе
    отсутствовать, и экран показывал бы все группы владельца.
    """
    first = await _seed_account(db_session, type_="wa")
    second = await _seed_account(db_session, type_="tg_user")
    await _seed_group(db_session, first, "Группа первого аккаунта")
    await _seed_group(db_session, second, "Группа второго аккаунта")

    html = (await authed_client.get(f"/accounts/{first.id}/groups")).text

    assert "Группа первого аккаунта" in html
    assert "Группа второго аккаунта" not in html, (
        "экран показал группы соседнего аккаунта того же пользователя"
    )


@pytest.mark.asyncio
async def test_page_of_a_foreign_account_leaks_nothing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-03-01: `account_id` приходит из URL — ему не верят.

    Утверждение о ТЕЛЕ ответа, а не только о коде: редирект с именами групп в
    теле был бы такой же утечкой.
    """
    foreign_user = await _seed_foreign_user(db_session)
    foreign_account = await _seed_account(db_session, user_id=foreign_user.id)
    await _seed_group(
        db_session, foreign_account, "Чужая группа", user_id=foreign_user.id
    )

    response = await authed_client.get(
        f"/accounts/{foreign_account.id}/groups", follow_redirects=False
    )

    assert response.status_code in (302, 404)
    assert "Чужая группа" not in response.text
    assert not _row_ids(response.text)


@pytest.mark.asyncio
async def test_page_without_session_goes_to_login(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """Аутентификация проверяется на каждом входе (правило Фазы 2)."""
    account = await _seed_account(db_session)

    response = await client.get(
        f"/accounts/{account.id}/groups", follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


# --- Состав и порядок списка --------------------------------------------------


@pytest.mark.asyncio
async def test_rows_are_ordered_by_group_id(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Порядок строк задан явно и повторяется при повторном открытии.

    Без ЯВНОЙ сортировки порядок — свойство плана запроса: постраничная
    загрузка, работающая смещением, начала бы дублировать и пропускать строки.
    Имена посеяны в обратном алфавитном порядке намеренно — тогда совпадение с
    порядком идентификаторов не может быть случайным следствием сортировки по
    имени.
    """
    account = await _seed_account(db_session)
    seeded = [
        (await _seed_group(db_session, account, name)).id
        for name in ("Яблоко", "Смородина", "Абрикос")
    ]

    first = _row_ids((await authed_client.get(f"/accounts/{account.id}/groups")).text)
    second = _row_ids((await authed_client.get(f"/accounts/{account.id}/groups")).text)

    assert first == sorted(seeded), "строки отданы не по возрастанию Group.id"
    assert second == first, "повторное открытие дало другой порядок строк"


@pytest.mark.asyncio
async def test_two_groups_with_the_same_name_render_as_two_rows(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Ключ строки — `Group.id`, а не имя: слияния по имени нет.

    Мессенджер отдаёт имена чатов без гарантии уникальности. Схлопывание двух
    одноимённых групп в одну строку спрятало бы от пользователя вторую группу,
    которая при этом реально получает рассылку.
    """
    account = await _seed_account(db_session)
    first = await _seed_group(db_session, account, "Одинаковое имя")
    second = await _seed_group(db_session, account, "Одинаковое имя")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert _row_ids(html) == [first.id, second.id], (
        "одноимённые группы схлопнулись в одну строку"
    )


@pytest.mark.asyncio
async def test_empty_screen_tells_what_to_do(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E4 `empty`: у аккаунта без групп экран называет следующий шаг."""
    account = await _seed_account(db_session)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "Групп пока нет" in html
    assert not _row_ids(html)


# --- Тумблер: владение, инверсия, изоляция ------------------------------------


@pytest.mark.asyncio
async def test_toggle_inverts_is_active_and_redirects(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """GRP-05: одно действие — одно изменение состояния, ответ PRG-редиректом."""
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа тумблера")
    assert group.is_active is True, "предусловие теста"

    response = await authed_client.post(
        f"/accounts/{account.id}/groups/{group.id}/toggle", follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == f"/accounts/{account.id}/groups"
    await db_session.refresh(group)
    assert group.is_active is False


@pytest.mark.asyncio
async def test_double_toggle_returns_the_group_to_its_initial_state(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Маршрут ИНВЕРТИРУЕТ, а не устанавливает: действие обратимо (D-08).

    Обработчик, жёстко ставящий `is_active = False`, прошёл бы предыдущий тест
    и провалил этот — включить группу обратно стало бы нечем.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа двойного нажатия")

    for _ in range(2):
        response = await authed_client.post(
            f"/accounts/{account.id}/groups/{group.id}/toggle", follow_redirects=False
        )
        assert response.status_code == 302

    await db_session.refresh(group)
    assert group.is_active is True, "двойное переключение не вернуло исходное состояние"


@pytest.mark.asyncio
async def test_toggle_leaves_a_foreign_group_alone(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-03-02: чужая группа не переключается прямым POST мимо страницы."""
    foreign_user = await _seed_foreign_user(db_session)
    foreign_account = await _seed_account(db_session, user_id=foreign_user.id)
    foreign_group = await _seed_group(
        db_session, foreign_account, "Чужая группа тумблера", user_id=foreign_user.id
    )

    response = await authed_client.post(
        f"/accounts/{foreign_account.id}/groups/{foreign_group.id}/toggle",
        follow_redirects=False,
    )

    assert response.status_code == 302
    await db_session.refresh(foreign_group)
    assert foreign_group.is_active is True, "переключилась группа чужого аккаунта"


@pytest.mark.asyncio
async def test_toggle_does_not_trust_the_account_id_from_the_url(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Владение проверяется ТРОЙНЫМ WHERE, включая `Group.account_id`.

    Свой аккаунт в адресе и своя группа — но группа принадлежит ДРУГОМУ
    аккаунту. Обработчик, проверяющий только владельца, переключил бы её.
    """
    first = await _seed_account(db_session, type_="wa")
    second = await _seed_account(db_session, type_="tg_user")
    group_of_second = await _seed_group(db_session, second, "Группа второго аккаунта")

    response = await authed_client.post(
        f"/accounts/{first.id}/groups/{group_of_second.id}/toggle",
        follow_redirects=False,
    )

    assert response.status_code == 302
    await db_session.refresh(group_of_second)
    assert group_of_second.is_active is True, (
        "группа переключилась через адрес чужого для неё аккаунта"
    )


@pytest.mark.asyncio
async def test_toggle_touches_exactly_one_group(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Соседняя группа того же аккаунта состояния не меняет."""
    account = await _seed_account(db_session)
    target = await _seed_group(db_session, account, "Целевая группа")
    neighbour = await _seed_group(db_session, account, "Соседняя группа")

    await authed_client.post(
        f"/accounts/{account.id}/groups/{target.id}/toggle", follow_redirects=False
    )

    await db_session.refresh(target)
    await db_session.refresh(neighbour)
    assert target.is_active is False
    assert neighbour.is_active is True, "переключение задело соседнюю группу"


@pytest.mark.asyncio
async def test_toggle_does_not_edit_the_schedules(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-05: тумблер обратим, поэтому состав расписаний он не трогает.

    Выключение группы, вычищающее её идентификатор из `Schedule.group_ids`,
    было бы необратимым: включив группу обратно, пользователь не вернул бы её в
    расписания и молча перестал бы рассылать. Пропуск обеспечивается условием в
    диспетчеризации (Задача 2), а не правкой пользовательской настройки.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа расписания")
    other = await _seed_group(db_session, account, "Вторая группа расписания")
    schedule = await _seed_schedule(db_session, account, [group.id, other.id])
    before = list(schedule.group_ids)

    await authed_client.post(
        f"/accounts/{account.id}/groups/{group.id}/toggle", follow_redirects=False
    )

    await db_session.refresh(schedule)
    assert schedule.group_ids == before, (
        "переключение изменило состав расписания — тумблер перестал быть обратимым"
    )


@pytest.mark.asyncio
async def test_toggle_without_session_goes_to_login(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """Вход изменения состояния тоже закрыт аутентификацией."""
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа без сессии")

    response = await client.post(
        f"/accounts/{account.id}/groups/{group.id}/toggle", follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    await db_session.refresh(group)
    assert group.is_active is True


# --- Базовый путь без JS и вход на экран --------------------------------------


@pytest.mark.asyncio
async def test_toggle_is_a_real_post_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-09: без Alpine тумблер остаётся настоящей формой POST.

    Перехват висит на САМОЙ форме: не навесится — форма уйдёт POST-ом на тот же
    маршрут. Кнопка-триггер вне формы такого пути не оставила бы.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа деградации")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    form_match = re.search(
        r'<form[^>]*action="/accounts/%d/groups/%d/toggle"[^>]*>' % (account.id, group.id),
        html,
    )
    assert form_match, "тумблер не обёрнут формой на маршрут переключения"
    opening = form_match.group(0)
    assert 'method="post"' in opening.lower(), "форма тумблера не POST"
    assert "x-on:change" in opening, "перехват отправки навешен не на саму форму"


@pytest.mark.asyncio
async def test_accounts_screen_links_to_the_account_groups(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E8 `populated`: вход на экран есть в строке аккаунта."""
    account = await _seed_account(db_session, type_="max")

    html = (await authed_client.get("/accounts")).text

    assert f"/accounts/{account.id}/groups" in html, (
        "на экране «Аккаунты» нет входа на экран групп аккаунта"
    )
    assert "Настроить группы" in html


# =============================================================================
# План 03-05, Задача 1: паршал прокрутки, поиск и честные счётчики
# =============================================================================
#
# У Telegram-аккаунта бывают сотни чатов (D-03, D-04). Три свойства экрана
# закрепляются здесь и ни одно из них не видно по коду ответа:
#
# * ПОСТРАНИЧНАЯ ЗАГРУЗКА. Сентинел подтягивает следующие 30 строк. Ошибка в
#   смещении не роняет страницу — она молча дублирует одни строки и теряет
#   другие.
# * ПОИСК, ПЕРЕЖИВАЮЩИЙ ПОДГРУЗКУ. Потерянная на второй странице строка поиска
#   подмешивает к отфильтрованным строкам весь остальной список, и экран
#   продолжает выглядеть исправным (T-04-01, T-03-21).
# * ЧЕСТНЫЕ СЧЁТЧИКИ. «N активных из M групп» считается по ВСЕЙ таблице
#   аккаунта, а не по загруженной странице: подсчёт по странице врёт ровно
#   там, где цена вранья наибольшая — на списке длиннее 30 строк (D-04).


async def _seed_many(
    db: AsyncSession,
    account: MessengerAccount,
    names: list[str],
    active: bool = True,
) -> list[Group]:
    """Пакетный посев: 35 отдельных commit-ов заняли бы дольше, чем весь файл."""
    user = await _user(db)
    groups = [
        Group(
            user_id=user.id,
            account_id=account.id,
            messenger_type=account.type,
            group_external_id=f"ext-{index}-{name}",
            name=name,
            is_active=active,
        )
        for index, name in enumerate(names)
    ]
    db.add_all(groups)
    await db.commit()
    for group in groups:
        await db.refresh(group)
    return groups


# --- Постраничная загрузка ---------------------------------------------------


@pytest.mark.asyncio
async def test_page_shows_thirty_rows_and_a_sentinel(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-04: страница отдаёт первые 30 строк и адрес следующей порции."""
    account = await _seed_account(db_session)
    await _seed_many(db_session, account, [f"Группа {i:02d}" for i in range(35)])

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert len(_row_ids(html)) == 30, "страница отдала не 30 строк"
    sentinels = _sentinels(html)
    assert len(sentinels) == 1, f"сентинел не единственный: {sentinels}"
    assert "offset=30" in sentinels[0], sentinels[0]
    assert "limit=30" in sentinels[0], sentinels[0]


@pytest.mark.asyncio
async def test_partial_returns_the_rest_and_drops_the_sentinel(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Последняя порция приходит БЕЗ сентинела — иначе прокрутка не кончится."""
    account = await _seed_account(db_session)
    seeded = await _seed_many(
        db_session, account, [f"Группа {i:02d}" for i in range(35)]
    )

    page = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    response = await authed_client.get(_sentinels(page)[0])

    assert response.status_code == 200
    assert _row_ids(response.text) == [g.id for g in seeded[30:]], (
        "паршал отдал не продолжение списка"
    )
    assert not _sentinels(response.text), (
        "последняя порция принесла сентинел — прокрутка стала бесконечной"
    )


@pytest.mark.asyncio
async def test_partial_of_a_foreign_account_leaks_nothing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-03-19: владение проверяется в САМОМ паршале, а не наследуется страницей."""
    foreign_user = await _seed_foreign_user(db_session)
    foreign_account = await _seed_account(db_session, user_id=foreign_user.id)
    await _seed_group(
        db_session, foreign_account, "Чужая группа паршала", user_id=foreign_user.id
    )

    response = await authed_client.get(
        f"/accounts/{foreign_account.id}/groups/partial?offset=0&limit=30",
        follow_redirects=False,
    )

    # Утверждение ИМЕННО о редиректе, а не о «302 или 404»: пока входа не
    # существует, маршрутизатор отвечает 404, и мягкое утверждение зеленело бы
    # на отсутствии кода, который оно должно проверять.
    assert response.status_code == 302
    assert response.headers["location"] == "/accounts"
    assert "Чужая группа паршала" not in response.text
    assert not _row_ids(response.text)


@pytest.mark.asyncio
async def test_partial_without_session_goes_to_login(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """Аутентификация проверяется на каждом входе, включая паршал."""
    account = await _seed_account(db_session)

    response = await client.get(
        f"/accounts/{account.id}/groups/partial?offset=0&limit=30",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["offset=-1&limit=30", "offset=0&limit=101"])
async def test_partial_rejects_bad_pagination_params(
    authed_client: AsyncClient, db_session: AsyncSession, query: str
):
    """T-03-22: негодные параметры отвергаются ДО обращения к базе."""
    account = await _seed_account(db_session)

    response = await authed_client.get(
        f"/accounts/{account.id}/groups/partial?{query}", follow_redirects=False
    )

    assert response.status_code == 422, query


# --- Поиск -------------------------------------------------------------------

SEARCH_TERM = "Клуб садоводов"


@pytest.mark.asyncio
async def test_search_narrows_the_page(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-03: единственный фильтр экрана — поиск по названию."""
    account = await _seed_account(db_session)
    await _seed_many(db_session, account, [f"{SEARCH_TERM} {i}" for i in range(3)])
    await _seed_many(db_session, account, ["Барахолка района"])

    html = (
        await authed_client.get(
            f"/accounts/{account.id}/groups", params={"search": SEARCH_TERM}
        )
    ).text

    assert len(_row_ids(html)) == 3, "поиск не сузил список"
    assert "Барахолка района" not in html, "в выдачу поиска попала несовпавшая группа"


@pytest.mark.asyncio
async def test_sentinel_carries_the_search_urlencoded(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-03-21: строка поиска уходит в адрес сентинела в urlencode-виде."""
    account = await _seed_account(db_session)
    await _seed_many(db_session, account, [f"{SEARCH_TERM} {i:02d}" for i in range(35)])

    html = (
        await authed_client.get(
            f"/accounts/{account.id}/groups", params={"search": SEARCH_TERM}
        )
    ).text

    sentinel = _sentinels(html)[0]
    assert f"search={quote(SEARCH_TERM, safe='/')}" in sentinel, sentinel


@pytest.mark.asyncio
async def test_partial_keeps_the_search_on_the_second_page(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Вторая страница поиска не возвращается к неотфильтрованному списку.

    Потерянный фильтр не роняет страницу — он молча подмешивает к найденному
    остальной список аккаунта, и экран продолжает выглядеть исправным.
    """
    account = await _seed_account(db_session)
    matching = await _seed_many(
        db_session, account, [f"{SEARCH_TERM} {i:02d}" for i in range(35)]
    )
    await _seed_many(db_session, account, [f"Прочая группа {i}" for i in range(5)])

    page = (
        await authed_client.get(
            f"/accounts/{account.id}/groups", params={"search": SEARCH_TERM}
        )
    ).text
    response = await authed_client.get(_sentinels(page)[0])

    assert response.status_code == 200
    assert _row_ids(response.text) == [g.id for g in matching[30:]], (
        "паршал отдал продолжение НЕотфильтрованного списка"
    )
    assert "Прочая группа" not in response.text


# --- Линейка счётчика --------------------------------------------------------


@pytest.mark.asyncio
async def test_counter_line_counts_the_whole_table(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-04: числа линейки не зависят от того, сколько строк загружено.

    Подсчёт по загруженной странице дал бы «30 из 30» при 35 группах — то есть
    соврал бы ровно там, где список перестал помещаться на экран.
    """
    account = await _seed_account(db_session)
    await _seed_many(db_session, account, [f"Активная {i:02d}" for i in range(32)])
    await _seed_many(
        db_session, account, [f"Выключенная {i}" for i in range(3)], active=False
    )

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    # «32 активные», а не «32 активных»: склонение считается по последней цифре,
    # и 32 требует той же формы, что 2 (UI-SPEC: «2 активные из 5 групп»).
    assert "32 активные из 35 групп" in html, "линейка посчитана по загруженной странице"


@pytest.mark.asyncio
async def test_partial_carries_no_counter_line(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Паршал прокрутки линейку не трогает — у неё не бывает промежуточных чисел."""
    account = await _seed_account(db_session)
    await _seed_many(db_session, account, [f"Активная {i:02d}" for i in range(32)])
    await _seed_many(
        db_session, account, [f"Выключенная {i}" for i in range(3)], active=False
    )

    response = await authed_client.get(
        f"/accounts/{account.id}/groups/partial?offset=30&limit=30"
    )

    # Положительное утверждение первым: без него тест зеленел бы на пустом теле
    # несуществующего входа, ничего при этом не проверяя.
    assert response.status_code == 200
    html = response.text
    assert len(_row_ids(html)) == 5, "паршал не отдал последнюю порцию строк"
    assert "активных из" not in html, "паршал принёс линейку счётчика"
    assert "ВЫКЛЮЧЕННЫЕ ГРУППЫ" not in html


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "count,expected",
    [
        (1, "1 активная из 1 группы"),
        (2, "2 активные из 2 групп"),
        (5, "5 активных из 5 групп"),
    ],
)
async def test_counter_line_plurals(
    authed_client: AsyncClient, db_session: AsyncSession, count: int, expected: str
):
    """UI-SPEC E3 zero-one-many: «1 активная из 1 группы», а не «1 активных»."""
    account = await _seed_account(db_session)
    await _seed_many(db_session, account, [f"Группа {i}" for i in range(count)])

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert expected in html


# --- Подпись «в N расписаниях» (D-08) ----------------------------------------


@pytest.mark.asyncio
async def test_row_shows_the_number_of_schedules(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-08: подпись строки объясняет цену удаления группы."""
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа двух расписаний")
    await _seed_schedule(db_session, account, [group.id])
    await _seed_schedule(db_session, account, [group.id])

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "в 2 расписаниях" in html


@pytest.mark.asyncio
async def test_row_without_schedules_says_so(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """При нуле подпись читается словами, а не «в 0 расписаниях»."""
    account = await _seed_account(db_session)
    await _seed_group(db_session, account, "Группа без расписаний")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "не в расписаниях" in html


@pytest.mark.asyncio
async def test_schedule_count_ignores_foreign_schedules(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Считаются только расписания владельца.

    Аналог из старого раздела грузил ВСЕ расписания таблицы без ограничения
    владельцем: чужое расписание, случайно содержащее наш идентификатор,
    завышало бы подпись. Переносить дефект вместе с приёмом нельзя.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа одного расписания")
    await _seed_schedule(db_session, account, [group.id])

    foreign_user = await _seed_foreign_user(db_session)
    foreign_ad = Ad(user_id=foreign_user.id, title="Чужое", text="Текст", images=[])
    db_session.add(foreign_ad)
    await db_session.commit()
    await db_session.refresh(foreign_ad)
    db_session.add(
        Schedule(
            ad_id=foreign_ad.id,
            account_id=account.id,
            group_ids=[group.id],
            days_of_week=[1],
            times_of_day=["10:00"],
            timezone="UTC",
        )
    )
    await db_session.commit()

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "в 1 расписании" in html, "подпись завышена чужим расписанием"


# --- Синхронность двух разметок сентинела ------------------------------------


@pytest.mark.asyncio
async def test_sentinel_markup_is_identical_in_both_templates():
    """Сентинел страницы и сентинел порции — одна и та же строка разметки.

    Расхождение проявляется только у того, кто долистал до второй порции:
    первая страница остаётся исправной.
    """
    page = (TEMPLATES_DIR / "account_groups" / "list.html").read_text(encoding="utf-8")
    partial = (TEMPLATES_DIR / "account_groups" / "partial_cards.html").read_text(
        encoding="utf-8"
    )

    page_sentinel = [line.strip() for line in page.splitlines() if "hx-get=" in line]
    partial_sentinel = [
        line.strip() for line in partial.splitlines() if "hx-get=" in line
    ]

    assert page_sentinel, "сентинел исчез из list.html"
    assert page_sentinel == partial_sentinel, (
        "разметка сентинела разошлась между страницей и порцией прокрутки"
    )
