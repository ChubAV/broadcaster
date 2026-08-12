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

import itertools
import json
import re
from datetime import datetime, timedelta, timezone
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


def _row_html(html: str, group_id: int) -> str:
    """Разметка ОДНОЙ строки списка целиком, от её `<div` до парного `</div>`.

    Нужна для утверждения «панель подтверждения лежит ВНЕ строки»: подстрочный
    поиск по всей странице такого различить не может — идентификатор панели
    есть на странице в обоих случаях.
    """
    anchor = html.index(f'id="group-row-{group_id}"')
    start = html.rindex("<div", 0, anchor)
    depth = 0
    for match in re.finditer(r"<div\b|</div>", html[start:]):
        depth += 1 if match.group(0) == "<div" else -1
        if depth == 0:
            return html[start : start + match.end()]
    raise AssertionError(f"строка группы {group_id} не закрыта")


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


_external_id_counter = itertools.count(1)


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
        # Внешний идентификатор выводится из СЧЁТЧИКА, а не из имени: имена
        # чатов мессенджер отдаёт без гарантии уникальности, и на паре
        # одноимённых групп прежний `ext-{name}` порождал две строки с
        # одинаковым `group_external_id` — состояние, которое база с ревизии
        # 0015 не принимает, а фикстура не имела в виду.
        group_external_id=f"ext-{next(_external_id_counter)}",
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

    # Перехвата на форме для базового пути НЕДОСТАТОЧНО, и прежняя редакция
    # теста этого не ловила: форма, внутри которой один лишь чекбокс, без JS не
    # отправляется никак — неявной отправки по Enter спецификация для неё не
    # предусматривает. Проверяется наличие элемента, который отправляет форму
    # САМ, а не через Alpine.
    body = html[form_match.end():]
    body = body[: body.index("</form>")]
    assert re.search(r'<button[^>]*type="submit"', body), (
        "в форме тумблера нет элемента, отправляющего её без JS: "
        "при неподнявшемся Alpine группу нельзя ни включить, ни выключить"
    )


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


# =============================================================================
# План 03-05, Задача 2: удаление группы с панелью подтверждения (GRP-06)
# =============================================================================
#
# Удаление — единственное необратимое действие экрана, и у него два следствия,
# о которых пользователь обязан знать ДО нажатия: группа уходит из всех
# расписаний, а следующая синхронизация вернёт её как новую (D-10).
#
# Ключевое свойство маршрута — ТОЧНОСТЬ: удаляется ровно одна строка, из
# расписаний уходит ровно один идентификатор, соседние остаются. Ошибка здесь
# не роняет страницу — она молча вычищает из расписаний чужую группу, и увидит
# это только тот, у кого перестала уходить рассылка.


@pytest.mark.asyncio
async def test_delete_removes_the_group_and_redirects(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """GRP-06: своя группа удаляется, ответ — PRG-редирект на экран аккаунта."""
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа на удаление")

    response = await authed_client.post(
        f"/accounts/{account.id}/groups/{group.id}/delete", follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == f"/accounts/{account.id}/groups"
    assert (await db_session.get(Group, group.id)) is None


@pytest.mark.asyncio
async def test_delete_cleans_the_group_out_of_schedules(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Идентификатор удалённой группы исчезает из `group_ids` расписаний.

    Осиротевший идентификатор не роняет отправку — он делает её тихо неполной:
    расписание продолжает считаться настроенным на группу, которой уже нет.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа расписания")
    schedule = await _seed_schedule(db_session, account, [group.id])

    await authed_client.post(
        f"/accounts/{account.id}/groups/{group.id}/delete", follow_redirects=False
    )

    db_session.expunge_all()
    refreshed = await db_session.get(Schedule, schedule.id)
    assert group.id not in (refreshed.group_ids or []), (
        "идентификатор удалённой группы остался в расписании"
    )


@pytest.mark.asyncio
async def test_delete_keeps_the_neighbour_ids_in_the_same_schedule(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный тест: чистка снимает РОВНО один идентификатор.

    Без него предыдущий тест зеленел бы и на обработчике, обнуляющем состав
    расписания целиком.
    """
    account = await _seed_account(db_session)
    target = await _seed_group(db_session, account, "Удаляемая группа")
    neighbour = await _seed_group(db_session, account, "Соседняя группа")
    schedule = await _seed_schedule(db_session, account, [target.id, neighbour.id])

    await authed_client.post(
        f"/accounts/{account.id}/groups/{target.id}/delete", follow_redirects=False
    )

    db_session.expunge_all()
    refreshed = await db_session.get(Schedule, schedule.id)
    assert refreshed.group_ids == [neighbour.id], (
        "чистка расписания задела соседний идентификатор"
    )
    assert (await db_session.get(Group, neighbour.id)) is not None


@pytest.mark.asyncio
async def test_delete_spares_the_same_named_group_of_another_account(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Одноимённая группа соседнего аккаунта того же пользователя остаётся.

    Мессенджеры отдают имена чатов без гарантии уникальности: удаление по имени
    вместо идентификатора снесло бы обе.
    """
    first = await _seed_account(db_session, type_="wa")
    second = await _seed_account(db_session, type_="tg_user")
    target = await _seed_group(db_session, first, "Одинаковое имя")
    twin = await _seed_group(db_session, second, "Одинаковое имя")

    await authed_client.post(
        f"/accounts/{first.id}/groups/{target.id}/delete", follow_redirects=False
    )

    assert (await db_session.get(Group, target.id)) is None
    assert (await db_session.get(Group, twin.id)) is not None, (
        "удаление снесло одноимённую группу соседнего аккаунта"
    )


@pytest.mark.asyncio
async def test_delete_does_not_trust_the_account_id_from_the_url(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-03-20: тройной WHERE — своя группа, но чужой для неё аккаунт в адресе."""
    first = await _seed_account(db_session, type_="wa")
    second = await _seed_account(db_session, type_="tg_user")
    group_of_second = await _seed_group(db_session, second, "Группа второго аккаунта")

    response = await authed_client.post(
        f"/accounts/{first.id}/groups/{group_of_second.id}/delete",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert (await db_session.get(Group, group_of_second.id)) is not None, (
        "группа удалена через адрес чужого для неё аккаунта"
    )


@pytest.mark.asyncio
async def test_delete_leaves_a_foreign_group_alone(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-03-20: чужая группа не удаляется прямым POST мимо страницы."""
    foreign_user = await _seed_foreign_user(db_session)
    foreign_account = await _seed_account(db_session, user_id=foreign_user.id)
    foreign_group = await _seed_group(
        db_session, foreign_account, "Чужая группа удаления", user_id=foreign_user.id
    )

    response = await authed_client.post(
        f"/accounts/{foreign_account.id}/groups/{foreign_group.id}/delete",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert (await db_session.get(Group, foreign_group.id)) is not None


@pytest.mark.asyncio
async def test_repeated_delete_is_harmless(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Повтор запроса на уже удалённой группе — редирект, а не ошибка.

    Кнопка «назад» и повторная отправка формы приводят сюда штатно; ответ
    неотличим от успешного, поэтому по нему нельзя узнать, существовала ли
    группа вообще.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа двойного удаления")

    first = await authed_client.post(
        f"/accounts/{account.id}/groups/{group.id}/delete", follow_redirects=False
    )
    second = await authed_client.post(
        f"/accounts/{account.id}/groups/{group.id}/delete", follow_redirects=False
    )

    assert first.status_code == 302
    assert second.status_code == 302
    assert second.headers["location"] == f"/accounts/{account.id}/groups"


@pytest.mark.asyncio
async def test_delete_of_a_group_in_no_schedule_works(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Группа вне расписаний удаляется штатно — чистка просто ничего не находит."""
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа вне расписаний")

    response = await authed_client.post(
        f"/accounts/{account.id}/groups/{group.id}/delete", follow_redirects=False
    )

    assert response.status_code == 302
    assert (await db_session.get(Group, group.id)) is None


@pytest.mark.asyncio
async def test_remaining_rows_keep_the_id_order_after_delete(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """После удаления порядок оставшихся строк остаётся возрастающим."""
    account = await _seed_account(db_session)
    seeded = await _seed_many(
        db_session, account, ["Яблоко", "Смородина", "Абрикос", "Вишня"]
    )

    await authed_client.post(
        f"/accounts/{account.id}/groups/{seeded[1].id}/delete", follow_redirects=False
    )

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    expected = [seeded[0].id, seeded[2].id, seeded[3].id]
    assert _row_ids(html) == expected, "порядок строк после удаления изменился"


@pytest.mark.asyncio
async def test_delete_without_session_goes_to_login(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict
):
    """Разрушительный вход тоже закрыт аутентификацией."""
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа без сессии")

    response = await client.post(
        f"/accounts/{account.id}/groups/{group.id}/delete", follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    assert (await db_session.get(Group, group.id)) is not None


# --- Панель подтверждения ----------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_panel_names_the_group_and_both_consequences(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC §Destructive confirmation: тело панели называет ОБА следствия.

    Второе следствие (D-10: синк вернёт группу как новую) обязано быть сказано
    ДО удаления, а не обнаружено после.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Барахолка Северного района")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "Удалить группу?" in html
    assert "Барахолка Северного района" in html
    assert "группа исчезнет из всех расписаний" in html
    assert "следующая синхронизация вернёт её как новую" in html


@pytest.mark.asyncio
async def test_confirm_panel_is_unique_per_group(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-11-04 в родном изводе: панелей ровно одна на группу.

    Две панели с одним идентификатором открывались бы одним событием, и обход
    по Tab уходил бы в невидимую копию.
    """
    account = await _seed_account(db_session)
    first = await _seed_group(db_session, account, "Первая группа")
    second = await _seed_group(db_session, account, "Вторая группа")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    for group in (first, second):
        assert html.count(f'id="group-del-{group.id}"') == 1, (
            f"панель подтверждения группы {group.id} не единственная"
        )


@pytest.mark.asyncio
async def test_confirm_panel_lives_outside_the_row(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Панель стоит РЯДОМ со строкой, а не внутри неё.

    Панель позиционируется фиксированно, а внутри строки-карточки стала бы её
    колонкой; кроме того, панель обязана жить вне любого заменяемого блока
    (урок Фазы 1).
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа с панелью")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert f'id="group-del-{group.id}"' in html, "панель подтверждения не отрисована"
    assert f'id="group-del-{group.id}"' not in _row_html(html, group.id), (
        "панель подтверждения оказалась ВНУТРИ строки списка"
    )


@pytest.mark.asyncio
async def test_delete_trigger_is_a_real_post_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-09: без Alpine форма-триггер уходит настоящим POST-ом на тот же маршрут.

    Кнопка-триггер вне формы оставила бы экран без единственного способа
    удалить группу, когда скрипт не доехал.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа деградации удаления")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    row = _row_html(html, group.id)
    form_match = re.search(
        r'<form[^>]*action="/accounts/%d/groups/%d/delete"[^>]*>'
        % (account.id, group.id),
        row,
    )
    assert form_match, "триггер удаления не обёрнут формой на маршрут удаления"
    opening = form_match.group(0)
    assert 'method="post"' in opening.lower(), "форма удаления не POST"
    assert "x-on:submit" in opening, "перехват отправки навешен не на саму форму"


# =============================================================================
# План 03-05, Задача 3: шапка аккаунта, пустые состояния и секция стилей
# =============================================================================
#
# Экран собирается в тот вид, что описан макетом и UI-SPEC. Проверяется то, что
# отдаёт 200 и при этом врёт: шапка с выдуманным «0 минут назад» вместо честного
# «синхронизация ещё не выполнялась», одно пустое состояние вместо трёх
# различимых, линейка «0 активных из 0 групп» на пустом экране.

STATIC_DIR = Path(__file__).resolve().parents[2] / "app" / "static"

# Признаки utility-фреймворка: разметка разделов от них избавлена (D-06).
UTILITY_MARKERS = ("bg-white", "text-gray", "rounded-lg", "border-gray", "lg:")


async def _seed_synced_account(
    db: AsyncSession, hours_ago: int = 2, status: str = "active"
) -> MessengerAccount:
    """Аккаунт с заполненным временем последнего синка."""
    user = await _user(db)
    account = MessengerAccount(
        user_id=user.id,
        type="wa",
        credentials="session",
        status=status,
        last_synced_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


# --- Шапка аккаунта ----------------------------------------------------------


@pytest.mark.asyncio
async def test_header_says_the_sync_never_ran(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E1 empty: незаполненное время синка читается словами.

    Выдуманное «0 минут назад» выглядело бы как успешная синхронизация,
    которой не было (Pitfall 2: код обязан пережить NULL).
    """
    account = await _seed_account(db_session)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "data-acct-head" in html, "карточка аккаунта не отрисована"
    assert "синхронизация ещё не выполнялась" in html
    assert "назад" not in html


@pytest.mark.asyncio
async def test_header_shows_the_relative_time_of_the_last_sync(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный тест: при заполненном времени шапка показывает «N назад»."""
    account = await _seed_synced_account(db_session, hours_ago=2)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "последняя синхронизация 2 часа назад" in html
    assert "синхронизация ещё не выполнялась" not in html


@pytest.mark.asyncio
async def test_header_says_the_sync_is_in_flight(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E1 loading: во время синка строка идентичности говорит об этом."""
    account = await _seed_synced_account(db_session, status="syncing")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "синхронизация идёт сейчас" in html
    assert "Синхронизация..." in html, "бейдж статуса разошёлся со словарём аккаунтов"


@pytest.mark.asyncio
async def test_header_never_renders_the_account_credentials(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """`credentials` — строка сессии мессенджера, а не телефон.

    Сегмент телефона в строке идентичности отсутствует именно поэтому: поля
    телефона у аккаунта нет, а вывод `credentials` был бы утечкой сессии.
    """
    user = await _user(db_session)
    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials="1BQANOTEuMTA4LjU2LjE0MFsecretSessionString",
        status="active",
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert account.credentials not in html, "строка сессии аккаунта попала в разметку"


# --- Три пустых состояния ----------------------------------------------------


@pytest.mark.asyncio
async def test_empty_state_before_the_first_sync(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Синхронизации не было и групп нет — предлагается первая синхронизация."""
    account = await _seed_account(db_session)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "Групп пока нет" in html
    assert "Все группы удалены" not in html


@pytest.mark.asyncio
async def test_empty_state_after_all_groups_were_deleted(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Синхронизация была, групп нет — их удалили, и синк вернёт их (D-10)."""
    account = await _seed_synced_account(db_session)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "Все группы удалены" in html
    assert "Групп пока нет" not in html


@pytest.mark.asyncio
async def test_empty_state_when_the_search_matched_nothing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Поиск ничего не нашёл — состояние своё, и у него есть сброс.

    Без отдельной ветки пользователь читал бы «Групп пока нет» при непустом
    списке аккаунта и не понимал бы, что список просто отфильтрован.
    """
    account = await _seed_synced_account(db_session)
    await _seed_group(db_session, account, "Барахолка Северного района")

    html = (
        await authed_client.get(
            f"/accounts/{account.id}/groups", params={"search": "ничего такого"}
        )
    ).text

    assert "Группы не найдены" in html
    assert "Все группы удалены" not in html
    assert "Групп пока нет" not in html
    assert f'href="/accounts/{account.id}/groups"' in html, "действия сброса нет"
    assert "filters__toggle" in html, "строка поиска исчезла при пустой выдаче"


@pytest.mark.asyncio
async def test_zero_groups_render_no_counter_line(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E3 empty: «0 активных из 0 групп» — не сообщение.

    Сообщение при нуле несёт пустое состояние; линейка не рендерится вовсе.
    """
    account = await _seed_account(db_session)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "count-rule" not in html
    assert "ВЫКЛЮЧЕННЫЕ ГРУППЫ ПРОПУСКАЮТСЯ ПРИ РАССЫЛКЕ" not in html


# --- Разметка и стили --------------------------------------------------------


@pytest.mark.asyncio
async def test_screen_has_no_utility_classes(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Экран собран на дизайн-системе, а не на классах удалённого фреймворка."""
    account = await _seed_synced_account(db_session)
    await _seed_group(db_session, account, "Группа проверки классов")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    for marker in UTILITY_MARKERS:
        assert marker not in html, marker


def test_screen_has_its_own_css_section():
    """У экрана есть собственная секция стилей.

    Проверка по исходнику, а не по выдаче: таблица стилей отдаётся статикой и
    в HTML страницы не попадает, поэтому поведенческой проверки для неё не
    существует. Ловится ровно то, ради чего секция заводилась: разметка,
    оставшаяся без правил раскладки, выглядит «почти прилично» и молча теряет
    и колонку имени, и приглушение выключенной строки.
    """
    css = (STATIC_DIR / "css" / "app.css").read_text(encoding="utf-8")

    for selector in (
        "[data-acct-head]",
        ".count-rule",
        "[data-group-list]",
        "[data-group-row]",
        ".group-row__name",
        ".group-row--off",
        ".group-row__mark",
    ):
        assert selector in css, f"в таблице стилей нет правил для {selector}"


# =============================================================================
# План 03-06, Задача 1: плашка результата синка и действие запуска в шапке
# =============================================================================
#
# GRP-07 со стороны пользователя. Результат читается из АККАУНТА, а не из памяти
# запроса, поэтому переживает перезаход: сохранённое значение пишут все три пути
# синхронизации (план 03-04), а показывает его этот экран.
#
# Проверяется то, что отдаёт 200 и при этом бесполезно: экран без кнопки запуска,
# сводка без чисел, «не найдено 0» вместо молчания, стек-трейс вместо плашки на
# испорченном значении.


async def _seed_account_with_result(
    db: AsyncSession,
    result: str | None,
    status: str = "active",
    hours_ago: int = 1,
) -> MessengerAccount:
    """Аккаунт с СЫРЫМ сохранённым результатом синка.

    Значение кладётся строкой, а не через хелпер: колонка хранит именно строку,
    и плашка обязана быть проверена на том виде значения, который приходит из
    базы, включая испорченный.
    """
    user = await _user(db)
    account = MessengerAccount(
        user_id=user.id,
        type="wa",
        credentials="session",
        status=status,
        last_synced_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
        last_sync_result=result,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


def _summary(found: int, new: int, renamed: int, missing: int = 0) -> str:
    """Сохранённая сводка в том виде, в каком её пишет apply_group_resync."""
    return json.dumps(
        {"found": found, "new": new, "renamed": renamed, "missing": missing,
         "error": None},
        ensure_ascii=False,
    )


# --- Действие запуска синхронизации ------------------------------------------


@pytest.mark.asyncio
async def test_header_carries_the_sync_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Главное действие экрана — НАСТОЯЩАЯ форма на существующий вход синка.

    Утверждается не подпись кнопки, а маршрут и метод: подпись можно нарисовать
    и без формы, и экран останется валидным, а запустить синхронизацию с него
    станет нечем (D-09).
    """
    account = await _seed_account(db_session)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert f'action="/accounts/{account.id}/sync-groups"' in html, (
        "формы запуска синхронизации на экране нет"
    )
    assert re.search(
        rf'<form method="POST" action="/accounts/{account.id}/sync-groups"', html
    ), "запуск синхронизации собран не формой POST"
    assert "Синхронизировать всё" in html


@pytest.mark.asyncio
async def test_sync_action_says_it_is_in_flight(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E1 loading: подпись действия при выполнении — «Синхронизация…».

    Парный к предыдущему: без него подпись могла бы остаться одной на оба
    состояния, и пользователь нажимал бы «Синхронизировать всё» поверх уже
    идущей синхронизации, получая молчаливый отказ guard-а.
    """
    account = await _seed_account_with_result(db_session, None, status="syncing")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "Синхронизация…" in html
    assert "Синхронизировать всё" not in html.split("</form>")[0], (
        "подпись действия не отражает выполняющуюся синхронизацию"
    )


@pytest.mark.asyncio
async def test_no_per_group_sync_action_on_the_screen(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-12: кнопки синхронизации ОТДЕЛЬНОЙ группы на экране нет.

    Протокола синхронизации одной группы у воркеров не существует, а протоколы
    фаза не трогает. Нарисованная кнопка вела бы на несуществующий маршрут —
    отказ, который пользователь прочитал бы как поломку своей группы.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Барахолка Северного района")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert not re.search(r'/groups/\d+/sync', html), (
        "на экране есть действие синхронизации отдельной группы"
    )
    row = _row_html(html, group.id)
    assert "sync" not in row, f"в строке группы осталось действие синхронизации: {row}"


# --- Плашка результата: успех -------------------------------------------------


@pytest.mark.asyncio
async def test_success_plashka_prints_all_three_counters(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E2 populated: сводка печатает найдено, новых и обновлено имён."""
    account = await _seed_account_with_result(
        db_session, _summary(found=42, new=7, renamed=3)
    )

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "Синхронизация завершена: найдено 42, новых 7, обновлено имён 3" in html
    assert "alert--success" in html


@pytest.mark.asyncio
async def test_success_plashka_omits_the_missing_segment_when_zero(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """«не найдено 0» не рендерится никогда: это шум, а не сообщение."""
    account = await _seed_account_with_result(
        db_session, _summary(found=5, new=0, renamed=0, missing=0)
    )

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "не найдено" not in html


@pytest.mark.asyncio
async def test_success_plashka_shows_the_missing_segment_when_nonzero(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный к предыдущему: при ненулевом значении сегмент обязан быть.

    Без него отсутствие сегмента ничего не доказывало бы — он мог бы не
    рендериться вовсе, и пропавшие группы остались бы незамеченными (D-11).
    """
    account = await _seed_account_with_result(
        db_session, _summary(found=5, new=0, renamed=0, missing=2)
    )

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "Синхронизация завершена: найдено 5, новых 0, обновлено имён 0, не найдено 2" in html


@pytest.mark.asyncio
async def test_plashka_with_missing_groups_is_not_painted_as_success(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Массовая пропажа групп не имеет права выглядеть зелёной плашкой успеха.

    Ветвление плашки было бинарным — есть `error` или нет, — поэтому сводка
    «найдено 0, новых 0, обновлено имён 0, не найдено 42» красилась зелёным:
    сообщение об исчезновении ВСЕХ групп аккаунта в тоне «всё хорошо».
    Красный тут тоже неверен — синк состоялся, повторять его незачем.
    """
    account = await _seed_account_with_result(
        db_session, _summary(found=0, new=0, renamed=0, missing=42)
    )

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "не найдено 42" in html
    assert "alert--warning" in html
    assert "alert--success" not in html


@pytest.mark.asyncio
async def test_plashka_stays_success_while_nothing_went_missing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный к предыдущему: без пропаж плашка остаётся зелёной.

    Без этой стороны предупреждающий тон мог бы стоять всегда, и цвет перестал
    бы что-либо различать.
    """
    account = await _seed_account_with_result(
        db_session, _summary(found=9, new=2, renamed=1, missing=0)
    )

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "alert--success" in html
    assert "alert--warning" not in html


@pytest.mark.asyncio
async def test_plashka_renders_exactly_once(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E2 zero-one-many: результаты не накапливаются стопкой."""
    account = await _seed_account_with_result(
        db_session, _summary(found=3, new=1, renamed=0)
    )
    await _seed_group(db_session, account, "Группа проверки единственности")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert html.count("data-sync-plashka") == 1
    assert html.count("Синхронизация завершена") == 1


# --- Плашка результата: ошибка и деградация -----------------------------------


@pytest.mark.asyncio
async def test_error_plashka_names_the_error_and_the_next_step(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E2 error: провал показывает текст ошибки И следующий шаг.

    Одного текста ошибки мало: «Connection refused» без инструкции не говорит
    пользователю, что делать дальше (UI-SPEC §Error states).
    """
    stored = json.dumps(
        {"found": 0, "new": 0, "renamed": 0, "missing": 0,
         "error": "Мост WhatsApp недоступен"},
        ensure_ascii=False,
    )
    account = await _seed_account_with_result(db_session, stored, status="sync_failed")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "Синхронизация не удалась: Мост WhatsApp недоступен" in html
    assert "повторить" in html
    assert "alert--error" in html
    assert "Синхронизация завершена" not in html, "сводка успеха вытеснила ошибку"


@pytest.mark.asyncio
async def test_error_text_from_the_worker_is_escaped(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-03-27: текст ошибки приходит из внешней системы и экранируется."""
    stored = json.dumps(
        {"found": 0, "new": 0, "renamed": 0, "missing": 0,
         "error": '<script>alert("xss")</script>'},
        ensure_ascii=False,
    )
    account = await _seed_account_with_result(db_session, stored, status="sync_failed")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stored",
    [
        "не json вовсе",
        "{оборванный на полуслове",
        "[1, 2, 3]",
        '"строка верхнего уровня"',
        "null",
    ],
)
async def test_corrupt_stored_result_renders_no_plashka(
    authed_client: AsyncClient, db_session: AsyncSession, stored: str
):
    """T-03-08: испорченное значение даёт ОТСУТСТВИЕ плашки, а не стек-трейс.

    Значение пишется только кодом, но строка в колонке может оказаться
    оборванной или написанной прежней версией формата. Экран обязан
    деградировать в молчание, а не в 500-ю на весь список групп.
    """
    account = await _seed_account_with_result(db_session, stored)

    response = await authed_client.get(f"/accounts/{account.id}/groups")

    assert response.status_code == 200
    assert "data-sync-plashka" not in response.text
    assert "Синхронизация завершена" not in response.text
    assert "Синхронизация не удалась" not in response.text


@pytest.mark.asyncio
async def test_never_synced_account_renders_no_plashka(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E2 empty: пустой оболочки плашки не бывает.

    Синхронизации не было — сообщение несёт строка идентичности шапки, а не
    плашка с прочерками вместо чисел.
    """
    account = await _seed_account(db_session)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "data-sync-plashka" not in html
    assert "синхронизация ещё не выполнялась" in html


@pytest.mark.asyncio
async def test_stored_result_survives_a_revisit(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-09: результат читается из аккаунта, поэтому виден при перезаходе.

    Второй запрос — отдельный HTTP-запрос без каких-либо параметров: сводка,
    жившая бы в памяти запроса или в параметре редиректа, до него бы не дожила.
    """
    account = await _seed_account_with_result(
        db_session, _summary(found=9, new=2, renamed=1)
    )

    first = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    second = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "найдено 9, новых 2, обновлено имён 1" in first
    assert "найдено 9, новых 2, обновлено имён 1" in second


@pytest.mark.asyncio
async def test_plashka_of_a_running_sync_keeps_the_previous_summary(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E2 partial: пока идёт новая синхронизация, старая сводка стоит.

    Плашка отражает последнюю ЗАВЕРШЁННУЮ синхронизацию; состояние выполнения
    несёт отдельный блок статуса, а не подмена плашки на пустоту.
    """
    account = await _seed_account_with_result(
        db_session, _summary(found=11, new=4, renamed=0), status="syncing"
    )

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "найдено 11, новых 4, обновлено имён 0" in html
    assert "синхронизация идёт сейчас" in html


# =============================================================================
# План 03-06, Задача 2: самоостанавливающийся опрос статуса фоновой синхронизации
# =============================================================================
#
# Синхронизация WA и MAX уходит в Celery, и её завершение экрану приходится
# ДОБИРАТЬ. Опрос обязан быть самоостанавливающимся: команды «стоп» у него нет,
# он прекращается тем, что очередной ответ приходит БЕЗ атрибутов запроса и
# триггера. Вынести атрибуты из-под условия по статусу — значит превратить экран
# в вечный поток запросов каждые пять секунд на каждой открытой вкладке каждого
# пользователя (T-03-26).
#
# Поэтому тесты идут ПАРАМИ: присутствие опроса при выполнении и его отсутствие
# при остальных статусах. Одиночный тест присутствия зеленел бы и у вечного
# опроса; одиночный тест отсутствия зеленел бы на пустом ответе.

SYNC_BLOCK_ATTR = "data-acct-sync"
# Триггер именно ОПРОСА. Сентинел бесконечной прокрутки несёт hx-trigger со
# значением "revealed", и утверждение про голое имя атрибута ловило бы его тоже.
POLL_TRIGGER = 'hx-trigger="every'


def _sync_block(html: str) -> str:
    """Подменяемый блок статуса целиком, от его `<div` до парного `</div>`.

    Утверждение «плашка и панель подтверждения лежат ВНЕ подменяемого блока»
    подстрочным поиском по всей странице недоказуемо: и то и другое есть на
    странице в обоих случаях. Различает только извлечение по парным тегам.
    """
    anchor = html.index(SYNC_BLOCK_ATTR)
    start = html.rindex("<div", 0, anchor)
    depth = 0
    for match in re.finditer(r"<div\b|</div>", html[start:]):
        depth += 1 if match.group(0) == "<div" else -1
        if depth == 0:
            return html[start : start + match.end()]
    raise AssertionError("блок статуса синхронизации не закрыт")


# --- Опрос на странице: пара «продолжается / не начинается» -------------------


@pytest.mark.asyncio
async def test_page_polls_while_the_sync_is_running(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Статус выполнения — единственный, в котором страница объявляет опрос."""
    account = await _seed_account_with_result(db_session, None, status="syncing")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    block = _sync_block(html)
    assert f'hx-get="/accounts/{account.id}/groups/sync-status"' in block
    assert POLL_TRIGGER in block
    assert 'hx-swap="outerHTML"' in block
    assert "Синхронизация выполняется" in block


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,expected_badge",
    [("active", "Активно"), ("sync_failed", "Ошибка синхронизации")],
)
async def test_page_declares_no_poll_outside_the_running_state(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    status: str,
    expected_badge: str,
):
    """Парный тест: вне выполнения атрибутов опроса на странице нет вовсе.

    Без него предыдущий зеленел бы и у опроса, объявленного безусловно, — то
    есть у вечного (T-03-26).

    Начинается тест с ПОЛОЖИТЕЛЬНОГО утверждения — блок отрисован и несёт бейдж
    своего статуса. Без него «опроса нет» выполнялось бы и на странице, где
    блока нет вовсе, то есть тест зеленел бы, ничего не проверяя.
    """
    account = await _seed_account_with_result(db_session, None, status=status)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    block = _sync_block(html)
    assert expected_badge in block, "блок статуса не отрисован или потерял бейдж"

    assert POLL_TRIGGER not in html, "страница опрашивает сервер вне синхронизации"
    assert "/groups/sync-status" not in html
    assert "Синхронизация выполняется" not in html


# --- Вход статуса: пара «продолжает / останавливает» --------------------------


@pytest.mark.asyncio
async def test_status_endpoint_keeps_polling_while_syncing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Ответ входа при выполнении несёт атрибуты — опрос продолжается."""
    account = await _seed_account_with_result(db_session, None, status="syncing")

    response = await authed_client.get(f"/accounts/{account.id}/groups/sync-status")

    assert response.status_code == 200
    assert POLL_TRIGGER in response.text
    assert f'hx-get="/accounts/{account.id}/groups/sync-status"' in response.text
    assert SYNC_BLOCK_ATTR in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["active", "sync_failed"])
async def test_status_endpoint_stops_the_poll_when_the_sync_ends(
    authed_client: AsyncClient, db_session: AsyncSession, status: str
):
    """ЭТО И ЕСТЬ МЕХАНИЗМ ОСТАНОВКИ: ответ приходит без атрибутов опроса.

    Аккаунт, перешедший в завершённое состояние, отдаёт разметку статуса — но
    уже без запроса и триггера, поэтому следующего запроса не случится.
    """
    account = await _seed_account_with_result(db_session, None, status=status)

    response = await authed_client.get(f"/accounts/{account.id}/groups/sync-status")

    assert response.status_code == 200
    assert SYNC_BLOCK_ATTR in response.text, "разметка статуса не отдана вовсе"
    assert POLL_TRIGGER not in response.text
    assert "hx-get" not in response.text


@pytest.mark.asyncio
async def test_status_endpoint_of_a_foreign_account_leaks_nothing(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-03-25: вход опрашивается автоматически, и владение проверяется В НЁМ.

    Чужой `account_id` не отдаёт ни бейджа статуса этого аккаунта, ни блока
    вовсе: иначе опрос по перебору идентификаторов сообщал бы, какие аккаунты
    заняты и в каком они состоянии.
    """
    other = await _seed_foreign_user(db_session)
    foreign = MessengerAccount(
        user_id=other.id, type="wa", credentials="session", status="syncing"
    )
    db_session.add(foreign)
    await db_session.commit()
    await db_session.refresh(foreign)

    response = await authed_client.get(f"/accounts/{foreign.id}/groups/sync-status")

    # Утверждается КОНКРЕТНЫЙ ответ, а не только отсутствие разметки: код 404
    # несуществующего маршрута удовлетворял бы «разметки нет» и зеленил бы тест
    # ДО того, как вход вообще появится.
    assert response.status_code == 200
    assert response.text.strip() == ""
    assert SYNC_BLOCK_ATTR not in response.text
    assert "Синхронизация..." not in response.text
    assert POLL_TRIGGER not in response.text


@pytest.mark.asyncio
async def test_status_endpoint_without_session_leaks_nothing(
    client: AsyncClient, db_session: AsyncSession
):
    """Без cookie-сессии разметки статуса не выдаётся.

    Пустой ответ здесь ещё и ОСТАНАВЛИВАЕТ опрос вкладки, у которой истекла
    сессия: перенаправление на страницу входа вернуло бы в блок целую страницу
    логина, а опрос продолжился бы.

    Владелец аккаунта заводится ЗДЕСЬ, а не берётся общим помощником: тот
    ищет пользователя, которого создаёт фикстура авторизации, а этому тесту она
    по построению не положена.
    """
    owner = User(email="owner@test.com", password_hash="x", name="Owner")
    db_session.add(owner)
    await db_session.commit()
    await db_session.refresh(owner)
    account = MessengerAccount(
        user_id=owner.id, type="wa", credentials="session", status="syncing"
    )
    db_session.add(account)
    await db_session.commit()
    await db_session.refresh(account)

    response = await client.get(f"/accounts/{account.id}/groups/sync-status")

    assert response.status_code == 200
    assert response.text.strip() == ""
    assert SYNC_BLOCK_ATTR not in response.text
    assert POLL_TRIGGER not in response.text


@pytest.mark.asyncio
async def test_status_endpoint_accepts_the_layout_param(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-15: параметр компоновки принимается и игнорируется.

    У открытых вкладок адреса опроса могут нести прежний параметр — оба вида
    запроса обязаны отвечать одинаково.
    """
    account = await _seed_account_with_result(db_session, None, status="syncing")

    without = await authed_client.get(f"/accounts/{account.id}/groups/sync-status")
    legacy = await authed_client.get(
        f"/accounts/{account.id}/groups/sync-status?layout=cards"
    )

    assert without.status_code == 200
    assert legacy.status_code == 200
    assert legacy.text == without.text


# --- Состав подменяемого блока ------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_panel_never_lives_inside_the_polled_block(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Панель подтверждения внутри подменяемого блока задваивалась бы (T-11-04).

    Элемент, заменяемый целиком, приносит с каждым ответом свои дочерние блоки:
    после первого же опроса на странице оказались бы две панели с одинаковым
    идентификатором — событие открывало бы обе, а Tab уходил бы в невидимую
    копию.
    """
    account = await _seed_account_with_result(db_session, None, status="syncing")
    group = await _seed_group(db_session, account, "Барахолка Северного района")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    block = _sync_block(html)
    assert f"group-del-{group.id}" not in block, (
        "панель подтверждения удаления оказалась внутри подменяемого блока"
    )
    assert f"group-del-{group.id}" in html, "панель исчезла со страницы вовсе"


@pytest.mark.asyncio
async def test_result_plashka_never_lives_inside_the_polled_block(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Плашка внутри подменяемого блока исчезла бы после первого опроса."""
    account = await _seed_account_with_result(
        db_session, _summary(found=6, new=1, renamed=0), status="syncing"
    )

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    block = _sync_block(html)
    assert "data-sync-plashka" not in block
    assert "Синхронизация завершена" not in block
    assert "Синхронизация завершена" in html, "плашка исчезла со страницы вовсе"


@pytest.mark.asyncio
async def test_polled_block_is_declared_exactly_once():
    """Опрос объявлен в ОДНОМ месте: два объявления гонялись бы друг с другом.

    Проверка по исходнику, а не по выдаче: второе объявление, лежащее в ветке
    другого статуса, ни одним запросом не поймается — оно проявится только у
    пользователя, дошедшего до этой ветки.
    """
    source = (
        TEMPLATES_DIR / "account_groups" / "partials" / "sync_result.html"
    ).read_text(encoding="utf-8")

    assert source.count("hx-trigger") == 1, "объявлений опроса не одно"
    assert source.count("hx-get") == 1
    assert "syncing" in source, "объявление опроса не обусловлено статусом"
    assert "group-del-" not in source, "панель подтверждения попала в блок подмены"
    assert "aria-live" in source, "завершение синхронизации не будет объявлено"
