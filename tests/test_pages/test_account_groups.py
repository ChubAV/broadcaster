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
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User

# Размер страницы берётся у обработчика, а не выписывается сюда числом: посев
# «страница плюс хвост» обязан оставаться посевом «страница плюс хвост» и после
# того, как экран когда-нибудь сменит размер страницы. Соседние тесты файла
# сеют 35 строк литералом — они писались до появления курсорных утверждений и
# переписывать их эта задача не обязана.
from app.pages.account_groups import PAGE_SIZE

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


# --- Тумблер на двух транспортах (Фаза 9, план 09-01) -------------------------
#
# Пары написаны по идиоме SP-3 (D-16 Фазы 8): у каждого утверждения о фрагменте
# есть половина, утверждающая, что БЕЗ признака htmx тот же маршрут отвечает
# по-прежнему. Половина без htmx зовёт `follow_redirects=False` ЯВНО: умолчание
# фикстуры `htmx_client` — `True`, и редирект, пришедший вместо фрагмента,
# приехал бы к тесту кодом 200 и телом чужой страницы.


@pytest.mark.asyncio
async def test_toggle_degrades_without_htmx(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Без признака htmx тумблер отвечает ПРЕЖНИМ перенаправлением на экран.

    Половина пары, охраняющая путь деградации. Перевод обработчика на слой
    ответа не имеет права поменять ответ человеку без JavaScript: он по-прежнему
    обязан получить 302 на экран групп, а не фрагмент строки, который браузер
    показал бы ему как целый документ со статусом 200.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа деградации тумблера")

    response = await authed_client.post(
        f"/accounts/{account.id}/groups/{group.id}/toggle", follow_redirects=False
    )

    assert response.status_code == 302, (
        f"запрос без признака htmx получил {response.status_code} — путь "
        "деградации перестал быть прежним"
    )
    assert response.headers["location"] == f"/accounts/{account.id}/groups"

    await db_session.refresh(group)
    assert group.is_active is False, "переключение на базовом пути не состоялось"


@pytest.mark.asyncio
async def test_toggle_returns_the_row_fragment(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """С признаком htmx тумблер отвечает ФРАГМЕНТОМ строки и внеполосным счётчиком.

    Несущее утверждение второй половины — `"<!DOCTYPE" not in response.text`:
    редирект, случайно доехавший до запроса htmx, придёт к тесту кодом 200 и
    телом целой страницы (`htmx_client` следует ему НЕЗАМЕТНО, как браузер), и
    отличить его от фрагмента можно только по отсутствию документа.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа фрагмента")

    response = await htmx_client.post(
        f"/accounts/{account.id}/groups/{group.id}/toggle"
    )

    assert response.status_code == 200, (
        f"запрос htmx получил {response.status_code} вместо фрагмента"
    )
    assert "<!DOCTYPE" not in response.text, (
        "в теле приехал целый документ: обработчик ответил перенаправлением, а "
        "клиент незаметно по нему прошёл — ровно то, чего не видит человек"
    )
    assert f'id="group-row-{group.id}"' in response.text, (
        "во фрагменте нет строки группы — цели подмены #group-row-N подменять "
        "будет нечем, и рантайм промолчит об этом"
    )
    assert 'hx-swap-oob="innerHTML:#account-groups-count"' in response.text, (
        "во фрагменте нет внеполосного узла линейки счётчика — число активных "
        "групп молча разъедется с состоянием строк"
    )

    await db_session.refresh(group)
    assert group.is_active is False, "переключение на пути htmx не состоялось"


@pytest.mark.asyncio
async def test_toggle_fragment_carries_no_second_modal(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Во фрагменте НЕТ второй панели подтверждения (T-11-04).

    Своп `outerHTML` вставляет ВЕСЬ ответ. Строка, собранная тем же макросом с
    панелью, принесла бы вторую панель с тем же идентификатором и второй живой
    ловушкой фокуса: подтверждение удаления открывало бы то одну, то другую, и
    воспроизводилось бы это через раз.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа без второй панели")

    response = await htmx_client.post(
        f"/accounts/{account.id}/groups/{group.id}/toggle"
    )

    assert response.status_code == 200
    assert f'id="group-del-{group.id}"' not in response.text, (
        "фрагмент принёс вторую панель подтверждения с тем же идентификатором"
    )


@pytest.mark.asyncio
async def test_toggle_fragment_keeps_the_toggle_id(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Чекбокс несёт ТОТ ЖЕ стабильный идентификатор и в ответе (QUAL-06).

    Механизм восстановления фокуса htmx ищет в присланной разметке элемент с
    ТЕМ ЖЕ `id`, что был у активного до свапа. Идентификатор, собранный только
    первичной отрисовкой, лишил бы механизм предмета — и разметка, а не код,
    есть то единственное, что здесь можно утверждать машинно.

    ⚠️ ФАКТИЧЕСКИЙ возврат фокуса этим НЕ доказывается и доказан здесь быть не
    может: `hx-disabled-elt` снимает блокировку ПОСЛЕ свапа, и активным
    элементом на момент свапа успевает стать `<body>` (09-RESEARCH §4.3).
    Проверка вынесена в ручной UAT с записанным ожиданием «сегодня нет».
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа стабильного id")

    first = (await htmx_client.get(f"/accounts/{account.id}/groups")).text
    assert f'id="group-toggle-{group.id}"' in first, (
        "первичная отрисовка не несёт стабильного идентификатора чекбокса"
    )

    response = await htmx_client.post(
        f"/accounts/{account.id}/groups/{group.id}/toggle"
    )

    # ⚠️ ПОЛОВИНА «ЭТО ФРАГМЕНТ» ЗДЕСЬ ОБЯЗАТЕЛЬНА, А НЕ ИЗБЫТОЧНА. Без неё
    # утверждение зелено ПО ПОСТРОЕНИЮ: `htmx_client` следует редиректу
    # незаметно, и целая страница экрана групп несёт тот же идентификатор
    # чекбокса. Тест доказывал бы наличие разметки на странице, о которой и без
    # него всё известно, а про ответ тумблера не утверждал бы ничего.
    assert "<!DOCTYPE" not in response.text, (
        "в теле приехал целый документ, а не фрагмент — идентификатор ниже "
        "нашёлся бы в нём и без всякого механизма восстановления фокуса"
    )
    assert f'id="group-toggle-{group.id}"' in response.text, (
        "в разметке фрагмента идентификатор чекбокса пропал — восстанавливать "
        "фокус механизму htmx будет не на что"
    )


@pytest.mark.asyncio
async def test_foreign_toggle_goes_to_location(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Чужая и НЕСУЩЕСТВУЮЩАЯ группа отвечают ОДИНАКОВО (D-13).

    Утверждение о НЕОТЛИЧИМОСТИ, поэтому два ответа сравниваются между собой, а
    не с константой по отдельности: различимый отказ сообщал бы, какие
    идентификаторы заняты чужими группами, — то есть перебором по адресу можно
    было бы составить карту чужих данных, не получив ни одной строки (T-9-02).
    """
    account = await _seed_account(db_session)
    foreign_user = await _seed_foreign_user(db_session)
    foreign_account = await _seed_account(db_session, user_id=foreign_user.id)
    foreign_group = await _seed_group(
        db_session, foreign_account, "Чужая группа перехода", user_id=foreign_user.id
    )

    foreign = await htmx_client.post(
        f"/accounts/{account.id}/groups/{foreign_group.id}/toggle"
    )
    missing = await htmx_client.post(
        f"/accounts/{account.id}/groups/{foreign_group.id + 100000}/toggle"
    )

    assert foreign.status_code == 204, (
        f"чужая группа ответила {foreign.status_code} вместо перехода"
    )
    assert foreign.headers["HX-Location"] == f"/accounts/{account.id}/groups"
    assert not foreign.content, "у ответа 204 появилось тело"

    assert missing.status_code == foreign.status_code, (
        "несуществующая группа отличима от чужой по коду ответа"
    )
    assert missing.headers.get("HX-Location") == foreign.headers["HX-Location"], (
        "несуществующая группа отличима от чужой по адресу перехода"
    )
    assert missing.content == foreign.content, (
        "несуществующая группа отличима от чужой по телу ответа"
    )

    await db_session.refresh(foreign_group)
    assert foreign_group.is_active is True, "переключилась чужая группа"


@pytest.mark.asyncio
async def test_toggle_does_not_trust_the_account_id_from_the_url_over_htmx(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Пара к `test_toggle_does_not_trust_the_account_id_from_the_url` (T-9-01).

    Тройной `WHERE` вычисляется ДО развилки транспорта, и новый транспорт не
    имеет права его ослабить: свой аккаунт в адресе и своя группа — но группа
    принадлежит ДРУГОМУ аккаунту.
    """
    first = await _seed_account(db_session, type_="wa")
    second = await _seed_account(db_session, type_="tg_user")
    group_of_second = await _seed_group(db_session, second, "Группа второго аккаунта")

    response = await htmx_client.post(
        f"/accounts/{first.id}/groups/{group_of_second.id}/toggle"
    )

    assert response.status_code == 204, (
        f"адрес чужого для группы аккаунта ответил {response.status_code} — "
        "фрагментный транспорт ослабил тройной WHERE"
    )
    assert response.headers["HX-Location"] == f"/accounts/{first.id}/groups"

    await db_session.refresh(group_of_second)
    assert group_of_second.is_active is True, (
        "группа переключилась через адрес чужого для неё аккаунта"
    )


# --- Базовый путь без JS и вход на экран --------------------------------------


@pytest.mark.asyncio
async def test_toggle_is_a_real_post_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-09: без JS тумблер остаётся настоящей формой POST.

    Перехват висит на САМОЙ форме: не навесится — форма уйдёт POST-ом на тот же
    маршрут. Кнопка-триггер вне формы такого пути не оставила бы.

    ⚠️ ПРЕДМЕТ ПЕРВОЙ ПОЛОВИНЫ СМЕНИЛ МЕХАНИЗМ, А НЕ СМЫСЛ (Фаза 9, план 09-01).
    Отправку по изменению чекбокса забрал `hx-trigger="change"`
    (`components/form_wrapper.html`), а прежний перехват Alpine `x-on:change`
    снят (D-05): держать оба значило бы отправлять форму дважды на одно нажатие.
    Утверждается по-прежнему то же свойство — перехват объявлен на САМОЙ форме,
    а не кнопкой-триггером вне её.
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
    assert 'hx-trigger="change"' in opening, (
        "перехват отправки объявлен не на самой форме: без него изменение "
        "чекбокса не отправляет ничего, а кнопка-триггер вне формы не оставила "
        "бы базового пути вовсе"
    )

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

    rows = _row_ids(html)
    assert len(rows) == 30, "страница отдала не 30 строк"
    sentinels = _sentinels(html)
    assert len(sentinels) == 1, f"сентинел не единственный: {sentinels}"
    # ⚠️ УТВЕРЖДАЕТСЯ КЛЮЧ ПОСЛЕДНЕЙ ОТРИСОВАННОЙ СТРОКИ, А НЕ ЧИСЛО
    # ОТРИСОВАННЫХ (план 09-13, решение владельца `keyset`). Форма строже
    # прежней: прежнее `offset=30` зеленело бы и на курсоре, указывающем не на
    # ту строку, — оно утверждало ЧИСЛО, а не связь с документом.
    assert f"after_id={rows[-1]}" in sentinels[0], sentinels[0]
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
        f"/accounts/{foreign_account.id}/groups/partial?limit=30",
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
        f"/accounts/{account.id}/groups/partial?limit=30",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
# ⚠️ ПАРАМЕТРЫ ПЕРЕМЕРЕНЫ ПОД НОВУЮ ФОРМУ КУРСОРА (план 09-13, `keyset`):
# прежние `offset=-1` и `offset=0` называли параметр, которого у маршрута
# больше нет, и FastAPI молча пропускал бы их как неизвестные — правило
# зеленело бы на 200 вместо 422, ничего не проверяя. Курсор объявлен
# `Query(None, ge=1)`, поэтому вырожденный ключ отвергается ДО обращения к базе.
@pytest.mark.parametrize("query", ["after_id=0&limit=30", "after_id=1&limit=101"])
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
    active = await _seed_many(
        db_session, account, [f"Активная {i:02d}" for i in range(32)]
    )
    await _seed_many(
        db_session, account, [f"Выключенная {i}" for i in range(3)], active=False
    )

    # Ключ ТРИДЦАТОЙ строки — то, что несёт сентинел первой страницы после
    # плана 09-13: порция добирает строки строго больше него.
    response = await authed_client.get(
        f"/accounts/{account.id}/groups/partial?after_id={active[29].id}&limit=30"
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


# --- Единственность источника разметки сентинела ------------------------------

SENTINEL_SOURCE = "account_groups/includes/sentinel.html"

# Места, зовущие сентинел: страница и порция прокрутки. Перечень выписан здесь,
# а не выведен обходом: место, ПЕРЕСТАВШЕЕ звать общий макрос, обязано быть
# замечено, а обход, собирающий вызывающих по факту вызова, о таком месте
# промолчал бы — оно просто выпало бы из собранного множества.
#
# ЛЕТОПИСЬ ПЕРЕЧНЯ: 3 → 2, Фаза 9, план 09-13, решение владельца `keyset` —
# ответ удаления перестал отрисовывать курсор ВОВСЕ. Причина названа предметно:
# курсор стал ключом последней отрисованной строки, поэтому удаление любой уже
# отрисованной строки его не двигает, и чинить внеполосным узлом нечего. Запись
# сдвинута ЗДЕСЬ, а не подогнана молча: выпавшее из перечня место обязано быть
# отличимо от места, которое просто перестали проверять.
SENTINEL_CALLERS = (
    "account_groups/list.html",
    "account_groups/partial_cards.html",
)


def test_the_sentinel_markup_has_exactly_one_source():
    """Разметка сентинела существует в дереве ровно в ОДНОМ файле (план 09-05).

    ⚠️ ЧТО ИМЕННО УСИЛИЛОСЬ И ПОЧЕМУ ПРЕЖНЯЯ ФОРМА ЗАКРЫТА. Прежде здесь стояло
    `test_sentinel_markup_is_identical_in_both_templates`: оно сравнивало ДВЕ
    копии разметки строка в строку и говорило ровно то, что копий две и они
    совпадают. Утверждение было верно ровно до появления ТРЕТЬЕГО места
    отрисовки — ответа удаления. Попарное сравнение двух файлов при трёх копиях
    осталось бы ЗЕЛЁНЫМ и при разъехавшейся третьей, то есть перестало бы быть
    утверждением о единственности, не покраснев ни разу. Прежнее имя сохранить
    нельзя: оно говорит о двух копиях, которых больше нет.

    Теперь копий нет вовсе, и это утверждается СЧЁТОМ ФАЙЛОВ, несущих разметку,
    плюс проверкой, что все три места зовут один и тот же источник.
    """
    carriers = sorted(
        path.relative_to(TEMPLATES_DIR).as_posix()
        for path in TEMPLATES_DIR.rglob("*.html")
        if "group-list-sentinel" in _sentinel_ids(path.read_text(encoding="utf-8"))
    )

    assert carriers == [SENTINEL_SOURCE], (
        f"разметка сентинела списка групп лежит в файлах {carriers}, а обязана "
        f"лежать ровно в одном ({SENTINEL_SOURCE}) — копии разъезжаются молча, "
        f"и видит это только тот, кто долистал до второй порции"
    )

    for caller in SENTINEL_CALLERS:
        source = (TEMPLATES_DIR / caller).read_text(encoding="utf-8")
        assert SENTINEL_SOURCE in source and "sentinel(" in source, (
            f"{caller} перестал звать общий макрос сентинела — место отрисовки "
            f"обзавелось собственной разметкой курсора"
        )

    for screen in ("account_groups/list.html", "account_groups/partial_cards.html"):
        source = (TEMPLATES_DIR / screen).read_text(encoding="utf-8")
        assert not _sentinel_ids(source), (
            f"в {screen} вернулась собственная разметка сентинела"
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
async def test_repeated_delete_is_harmless_over_htmx(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Вторая половина пары к `test_repeated_delete_is_harmless` (T-9-07).

    ⚠️ УТВЕРЖДАЕТСЯ ПОБАЙТОВОЕ РАВЕНСТВО ДВУХ ОТВЕТОВ, А НЕ СОВПАДЕНИЕ КАЖДОГО
    С КОНСТАНТОЙ. Тело ответа удаления собирается из `group_id` ПУТИ, а не из
    найденной строки, поэтому найденная и уже удалённая группа обязаны отвечать
    неотличимо. Различимый ответ сообщал бы, какие идентификаторы заняты
    существующими группами: карту чужих данных можно было бы составить
    перебором по адресу, не получив ни одной строки.

    ⚠️ ЧТО ЗДЕСЬ БЫЛО ПОЧИНЕНО И ПОЧЕМУ ЭТО ЗАПИСАНО, А НЕ ПРОСТО ИСПРАВЛЕНО
    (WARN-4 / WR-04). Прежняя редакция сеяла ОДНУ группу: обе отправки уводили
    список в ноль строк, обе уходили в ветку перехода с ПУСТЫМ телом, и все
    четыре утверждения удовлетворялись тривиально — сравнивались два пустых
    тела. Инструментированный прогон обзора: `first=204 body=b'' second=204
    body=b''`. Охраняемое свойство («тело собирается из `group_id` ПУТИ, а не из
    найденной строки») не исполнялось НИ РАЗУ, то есть тест был зелен ПО
    ПОСТРОЕНИЮ и доехал таким до отгрузки. Приём, которым это теперь исключено,
    один и он назван: ДОСТИЖЕНИЕ ФРАГМЕНТНОЙ ВЕТКИ УТВЕРЖДАЕТСЯ ПОЛОЖИТЕЛЬНО И
    РАНЬШЕ ЛЮБОГО СРАВНЕНИЯ ТЕЛ.

    ⚠️ СМЕНА КОНТРАКТА ПОСЛЕ ПЛАНА 09-05 — ЭТО ВТОРАЯ ПРАВКА, И ОНА ВАЖНЕЕ
    ПЕРВОЙ. Ответ несёт ЧЕТВЁРТЫЙ внеполосный узел — починку курсора со
    смещением `rendered_rows` минус число снятых с экрана строк. Отсюда три
    вещи:

    1. РАВЕНСТВО ПЕРЕНОСИТСЯ НА ПАРУ ОТПРАВОК, ОБЕ ИЗ КОТОРЫХ ЛЕЖАТ В КЛАССЕ
       «СТРОКА НЕ НАЙДЕНА» (чужая, несуществующая, уже удалённая) — и это и есть
       охраняемое свойство D-04 в редакции амендмента D-04-A, а не его прокси.
    2. НАСТОЯЩИЙ ПОВТОР В ЖИВОМ ДОКУМЕНТЕ ИДЁТ С УМЕНЬШЕННЫМ `rendered_rows`:
       второе нажатие читает число из УЖЕ ПОДМЕНЁННОГО сентинела, то есть шлёт
       `R − 1`. На нём равенство держится побайтово, и это утверждается
       ОТДЕЛЬНО, а не подразумевается.
    3. ПРЕЖНЯЯ ФОРМА — «первый ответ равен повтору при ОДНОМ И ТОМ ЖЕ теле» —
       БОЛЬШЕ НЕ УТВЕРЖДАЕТСЯ, и это смена контракта, а не смягчение. При
       искусственно неизменном `rendered_rows` первая отправка снимает строку
       (смещение `R − 1`), а вторая не снимает ничего (смещение `R`), и
       расхождение ВЕРНО: одинаковое число отрисованных строк после разного
       числа снятых означает разное состояние экрана. Прежнее равенство
       держалось на совпадении, которого до четвёртого узла просто не могло не
       быть. Разбор целиком — `09-05-PLAN.md` §`<cursor_repair_vs_d04>`.
    """
    account = await _seed_account(db_session)
    seeded = await _seed_many(
        db_session, account, ["Первая двойного удаления", "Вторая двойного удаления"]
    )
    target = seeded[0]

    page = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    rendered = _row_ids(page)
    assert len(rendered) >= 2, (
        f"страница отрисовала {len(rendered)} строк — посев короче двух, и обе "
        f"отправки ушли бы в ветку перехода с пустым телом: ровно тот отказ, "
        f"ради починки которого тест переписан"
    )

    # (1) УДАЛЕНИЕ: живой документ шлёт своё число отрисованных строк.
    first = await htmx_client.post(
        f"/accounts/{account.id}/groups/{target.id}/delete",
        data={"rendered_rows": len(rendered)},
    )
    # (2) НАСТОЯЩИЙ ПОВТОР: второе нажатие читает число из уже подменённого
    # сентинела, поэтому шлёт УМЕНЬШЕННОЕ на снятую строку.
    repeat = await htmx_client.post(
        f"/accounts/{account.id}/groups/{target.id}/delete",
        data={"rendered_rows": len(rendered) - 1},
    )
    # (3) ТРЕТЬЯ ОТПРАВКА С ТЕМ ЖЕ ТЕЛОМ, ЧТО И (2): пара, между которой
    # сравниваются тела, обязана идти с ОДНИМ И ТЕМ ЖЕ телом — различие
    # ответов, полученное от разного тела, о неотличимости не сказало бы ничего.
    repeat_again = await htmx_client.post(
        f"/accounts/{account.id}/groups/{target.id}/delete",
        data={"rendered_rows": len(rendered) - 1},
    )

    # ⚠️ ПЕРВОЕ ИСПОЛНЯЕМОЕ УТВЕРЖДЕНИЕ — О ДОСТИГНУТОЙ ФРАГМЕНТНОЙ ВЕТКЕ.
    # Без него всякое равенство тел ниже ВАКУУМНО: ветка перехода отвечает
    # пустым телом, два пустых тела равны побайтово, и охраняемое свойство не
    # исполняется ни разу — ровно тот отказ, что доехал до отгрузки (WR-04).
    assert first.status_code == 200, (
        f"фрагментная ветка не достигнута: ответ {first.status_code} вместо "
        f"200 — сравнения тел ниже сравнивали бы два ПУСТЫХ тела ветки "
        f"перехода, и утверждение о неотличимости было бы зелено по построению"
    )
    assert f'id="group-row-{target.id}"' in first.text, (
        "в теле первого ответа нет узла снятия строки — сравнивать нечего, и "
        "равенство тел ниже было бы вакуумным"
    )

    # ⚠️ ПОЛОВИНА «ЭТО НЕ ЦЕЛЫЙ ДОКУМЕНТ» ЗДЕСЬ ОБЯЗАТЕЛЬНА, А НЕ ИЗБЫТОЧНА.
    # `htmx_client` следует перенаправлению НЕЗАМЕТНО, и ответы оказались бы
    # одной и той же целой страницей экрана групп — равной себе самой и не
    # говорящей об ответе удаления ничего.
    for name, response in (
        ("первый", first),
        ("повтор", repeat),
        ("третий", repeat_again),
    ):
        assert "<!DOCTYPE" not in response.text, (
            f"в теле ({name}) приехал целый документ: обработчик ответил "
            f"перенаправлением, а клиент незаметно по нему прошёл"
        )

    # РАВЕНСТВО — ВНУТРИ КЛАССА «СТРОКА НЕ НАЙДЕНА»: обе отправки идут по уже
    # удалённой группе и с одним и тем же телом. Это и есть охраняемое
    # свойство D-04 в редакции D-04-A, а не его прокси.
    assert repeat.status_code == repeat_again.status_code, (
        "две отправки по уже удалённой группе различимы по коду ответа"
    )
    assert repeat.content == repeat_again.content, (
        "две отправки по уже удалённой группе различимы по телу ответа — по "
        "ответу можно было бы узнать, какие идентификаторы заняты чужими "
        "группами"
    )
    assert repeat.headers.get("HX-Location") == repeat_again.headers.get(
        "HX-Location"
    ), "две отправки по уже удалённой группе различимы по адресу перехода"

    # НАСТОЯЩИЙ ПОВТОР — ОТДЕЛЬНЫМ УТВЕРЖДЕНИЕМ. Именно так пара «нажал —
    # нажал ещё раз» выглядит в живом документе: число отрисованных строк
    # приезжает уменьшенным, и смещение курсора сходится.
    assert repeat.status_code == first.status_code, (
        "повторное нажатие в живом документе отличимо от первого по коду ответа"
    )
    assert repeat.content == first.content, (
        "повторное нажатие в живом документе отличимо от первого по телу "
        "ответа: число отрисованных строк приезжает уменьшенным на снятую "
        "строку, поэтому смещение починенного курсора обязано сойтись"
    )
    assert repeat.headers.get("HX-Location") == first.headers.get("HX-Location"), (
        "повторное нажатие в живом документе отличимо от первого по адресу "
        "перехода"
    )

    assert (await db_session.get(Group, target.id)) is None, (
        "группа не удалена первой отправкой либо вернулась после повторных"
    )


@pytest.mark.asyncio
async def test_delete_degrades_without_htmx(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Без признака htmx удаление отвечает ПРЕЖНИМ перенаправлением (SP-3).

    Половина пары, охраняющая путь деградации. Перевод обработчика на слой
    ответа не имеет права поменять ответ человеку без JavaScript: он по-прежнему
    обязан получить 302 на экран групп. Половина без htmx зовёт
    `follow_redirects=False` ЯВНО.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа деградации удаления")

    response = await authed_client.post(
        f"/accounts/{account.id}/groups/{group.id}/delete", follow_redirects=False
    )

    assert response.status_code == 302, (
        f"запрос без признака htmx получил {response.status_code} — путь "
        "деградации перестал быть прежним"
    )
    assert response.headers["location"] == f"/accounts/{account.id}/groups"
    assert (await db_session.get(Group, group.id)) is None, (
        "удаление на базовом пути не состоялось"
    )


@pytest.mark.asyncio
async def test_delete_returns_oob_nodes(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """С признаком htmx удаление отвечает ТРЕМЯ внеполосными узлами (D-11, D-02).

    Основной цели свопа у ответа нет вовсе: форма панели идёт `hx-swap="none"`,
    и всё едет внеполосно — снятие строки, снятие ОСИРОТЕВШЕЙ панели
    подтверждения и линейка счётчика.

    ⚠️ СНЯТИЕ ПАНЕЛИ ЗДЕСЬ НЕ УКРАШЕНИЕ. Панель сознательно стоит СНАРУЖИ
    удаляемой строки (T-11-04), поэтому вместе со строкой она не уезжает: без
    второго узла после N удалений в документе копятся N панелей `role="dialog"`
    с живыми ловушками фокуса.
    """
    account = await _seed_account(db_session)
    seeded = await _seed_many(db_session, account, ["Первая", "Вторая"])
    target = seeded[0]

    response = await htmx_client.post(
        f"/accounts/{account.id}/groups/{target.id}/delete"
    )

    assert response.status_code == 200, (
        f"запрос htmx получил {response.status_code} вместо фрагмента"
    )
    assert "<!DOCTYPE" not in response.text, (
        "в теле приехал целый документ: обработчик ответил перенаправлением, а "
        "клиент незаметно по нему прошёл — ровно то, чего не видит человек"
    )
    assert f'id="group-row-{target.id}"' in response.text, (
        "в ответе нет узла снятия строки — строка удалённой группы осталась бы "
        "на экране до перезагрузки"
    )
    assert f'id="group-del-{target.id}"' in response.text, (
        "в ответе нет узла снятия панели подтверждения — осиротевшая панель "
        "останется в документе с живой ловушкой фокуса"
    )
    assert response.text.count('hx-swap-oob="delete"') == 2, (
        "внеполосных снятий в ответе не два: строка и панель обязаны сниматься "
        "каждая своим узлом"
    )
    assert 'hx-swap-oob="innerHTML:#account-groups-count"' in response.text, (
        "в ответе нет внеполосного узла линейки счётчика — число активных групп "
        "молча разъедется с составом строк"
    )

    assert (await db_session.get(Group, target.id)) is None


@pytest.mark.asyncio
async def test_last_group_goes_to_location(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Опустевший список закрывается переходом, а не вторым пустым состоянием (D-09).

    Три различимых пустых состояния живут в `account_groups/list.html` в ОДНОМ
    экземпляре. Второй их отрисовкой во фрагменте они разошлись бы молча, и
    человек видел бы разный экран в зависимости от того, как он на него попал.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Единственная группа")

    response = await htmx_client.post(
        f"/accounts/{account.id}/groups/{group.id}/delete"
    )

    assert response.status_code == 204, (
        f"удаление последней группы ответило {response.status_code} вместо "
        "перехода на опустевший список"
    )
    assert response.headers["HX-Location"] == f"/accounts/{account.id}/groups"
    assert not response.content, "у ответа 204 появилось тело"


@pytest.mark.asyncio
async def test_delete_does_not_trust_the_account_id_from_the_url_over_htmx(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Пара к `test_delete_does_not_trust_the_account_id_from_the_url` (T-9-07).

    Тройной `WHERE` вычисляется ДО развилки транспорта, и новый транспорт не
    имеет права его ослабить: свой аккаунт в адресе и своя группа — но группа
    принадлежит ДРУГОМУ аккаунту. Ответ при этом неотличим от успешного
    удаления последней группы в этом аккаунте: ветвление считается по числам
    аккаунта из адреса, а не по факту нахождения строки (D-04).
    """
    first = await _seed_account(db_session, type_="wa")
    second = await _seed_account(db_session, type_="tg_user")
    group_of_second = await _seed_group(db_session, second, "Группа второго аккаунта")

    response = await htmx_client.post(
        f"/accounts/{first.id}/groups/{group_of_second.id}/delete"
    )

    assert response.status_code == 204, (
        f"адрес чужого для группы аккаунта ответил {response.status_code} — "
        "фрагментный транспорт ослабил тройной WHERE"
    )
    assert response.headers["HX-Location"] == f"/accounts/{first.id}/groups"
    assert (await db_session.get(Group, group_of_second.id)) is not None, (
        "группа удалена через адрес чужого для неё аккаунта"
    )


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
async def test_successful_sync_that_found_nothing_does_not_claim_deletion(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Аккаунт без единого чата не читает «Все группы удалены».

    `last_synced_at` отвечает на вопрос «синк состоялся?», а не «группы были?».
    Успешный синк, законно вернувший ноль групп, эту колонку ставит — и
    различение только по ней превращало пустой экран в утверждение об удалении,
    которого не было. К времени добавлена сводка: ноль найденных, ноль новых и
    ноль пропавших означают «групп нет».
    """
    account = await _seed_synced_account(db_session)
    account.last_sync_result = json.dumps(
        {"found": 0, "new": 0, "renamed": 0, "missing": 0, "error": None}
    )
    await db_session.commit()

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "Групп пока нет" in html
    assert "Все группы удалены" not in html


@pytest.mark.asyncio
async def test_sync_that_lost_every_group_still_says_they_were_deleted(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный тест: сводка с пропажами оставляет утверждение об удалении.

    Без него утверждение соседнего теста зеленело бы и на ветке, стёртой
    целиком: «Все группы удалены» обязано оставаться там, где группы
    действительно исчезли.
    """
    account = await _seed_synced_account(db_session)
    account.last_sync_result = json.dumps(
        {"found": 0, "new": 0, "renamed": 0, "missing": 3, "error": None}
    )
    await db_session.commit()

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

    ⚠️ ОДНО СЛОВО `sync` НА ДВА РАЗНЫХ ПРЕДМЕТА, И РАЗЛИЧАТЬ ИХ ПРАВИЛО ОБЯЗАНО
    (план 09-09). Строка группы несёт `hx-sync="this:drop"` — стратегию
    наложения ЗАПРОСОВ htmx, выбранную владельцем взамен блокировки чекбокса, —
    и голая проверка вхождения подстроки покраснела бы на ней, не имея к
    предмету правила никакого отношения. Значение этого атрибута снимается со
    строки ПЕРЕД проверкой, но снимается не молча: адрес, спрятанный в него,
    краснеет отдельным утверждением ниже, поэтому вывести действие
    синхронизации группы из-под правила, записав его в `hx-sync`, нельзя.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Барахолка Северного района")

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert not re.search(r'/groups/\d+/sync', html), (
        "на экране есть действие синхронизации отдельной группы"
    )
    row = _row_html(html, group.id)

    request_sync = re.findall(r'\shx-sync="([^"]*)"', row)
    for value in request_sync:
        assert "/" not in value, (
            f"в стратегии наложения запросов спрятан адрес: {value!r} — правило "
            f"снимает это значение со строки и таким способом обойдено быть не "
            f"может"
        )
    row_without_request_sync = re.sub(r'\shx-sync="[^"]*"', "", row)

    assert "sync" not in row_without_request_sync, (
        f"в строке группы осталось действие синхронизации: {row}"
    )


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


# =============================================================================
# План 09-05, Задача 1: курсор бесконечной прокрутки переживает удаление
# =============================================================================
#
# ЧТО ЗДЕСЬ ЗАКРЕПЛЯЕТСЯ И ПОЧЕМУ ЭТО НЕ ВИДНО НИ ПО КОДУ ОТВЕТА, НИ ГЛАЗОМ.
# Перевод удаления на фрагментный ответ (план 09-02) убрал полную перестройку
# страницы, а вместе с ней — единственное, что чинило курсор бесконечной
# прокрутки. Сентинел несёт АБСОЛЮТНОЕ смещение, запечённое в его адресе при
# отрисовке; ответ удаления снимает строку, снимает панель и обновляет линейку,
# но сентинела не касается. На 35 группах удаление первой строки делает
# тридцать первую неотрисовываемой НИ ОДНОЙ из двух порций: статус 200, консоль
# чистая, линейка честно говорит «34 групп», а на экране их 33.
#
# Обратная половина того же отказа — задвоение: курсор, уехавший назад там, где
# с экрана ничего не снялось, отрисует одну строку ВТОРОЙ РАЗ. Обе половины
# утверждаются, потому что починка «вычитать всегда единицу» лечит первую и
# заводит вторую.

# Тег сентинела целиком: идентификатор у него обязан быть, и он обязан быть
# ОДНИМ И ТЕМ ЖЕ во всех трёх местах отрисовки. Признак срабатывания взят
# якорем, а не идентификатор: тест, ищущий сразу идентификатор, не отличил бы
# «сентинела нет вовсе» от «сентинел без идентификатора».
SENTINEL_TAG_RE = re.compile(r'<[^<>]*hx-trigger="revealed"[^<>]*>')
ID_IN_TAG_RE = re.compile(r'id="([^"]*)"')


def _sentinel_ids(html: str) -> list[str]:
    """Идентификаторы всех сентинелов разметки — по одному на тег."""
    return [
        found.group(1)
        for tag in SENTINEL_TAG_RE.findall(html)
        if (found := ID_IN_TAG_RE.search(tag))
    ]


def _scroll_read_on_url(page_html: str, delete_response: str) -> str:
    """Адрес, по которому ЖИВОЙ документ пойдёт дочитывать список после ответа.

    ⚠️ ПОМОЩНИК МОДЕЛИРУЕТ ДОКУМЕНТ, А НЕ ЧИТАЕТ АДРЕС ИЗ ОТВЕТА НАПРЯМУЮ, И
    ЭТО НЕ ПОБЛАЖКА ТЕСТУ. Узел, который никто не подменил, остаётся стоять со
    своим прежним адресом — ровно так отказ и воспроизводится в живом браузере.
    Тест, читающий адрес только из ответа, на дереве без починки свалился бы
    раньше утверждения об объединении и сообщил бы «в ответе нет сентинела»
    вместо названных поимённо потерянных групп, то есть обвинил бы не то.
    """
    repaired = _sentinels(delete_response)
    if repaired:
        assert len(repaired) == 1, (
            f"ответ удаления принёс не один адрес дочитывания, а {len(repaired)}: "
            f"{repaired} — документ подменит сентинел дважды, и какой адрес "
            f"останется, разметкой не задано"
        )
        return repaired[0]
    on_page = _sentinels(page_html)
    assert on_page, (
        "сентинела нет ни в ответе удаления, ни на самой странице — дочитывать "
        "список документу нечем, и посев теста короче страницы"
    )
    return on_page[0]


@pytest.mark.asyncio
async def test_the_scroll_cursor_survives_a_fragment_delete(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """CR-01: после фрагментного удаления список не теряет ни одной группы.

    Объединение того, что уже отрисовано, и того, что дочитает сентинел,
    обязано покрывать ВЕСЬ оставшийся список — без потерь и без повторов.
    """
    account = await _seed_account(db_session)
    seeded = await _seed_many(
        db_session, account, [f"Группа {i:02d}" for i in range(PAGE_SIZE + 5)]
    )

    page = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    rendered = _row_ids(page)
    assert len(rendered) == PAGE_SIZE, (
        f"страница отрисовала {len(rendered)} строк вместо {PAGE_SIZE} — посев "
        "не создаёт условия, ради которого тест написан"
    )
    target = rendered[0]

    response = await htmx_client.post(
        f"/accounts/{account.id}/groups/{target}/delete",
        data={"rendered_rows": len(rendered)},
    )
    assert response.status_code == 200, (
        f"запрос htmx получил {response.status_code} вместо фрагмента"
    )

    rest = await authed_client.get(_scroll_read_on_url(page, response.text))
    assert rest.status_code == 200

    on_screen = [group_id for group_id in rendered if group_id != target]
    read_on = _row_ids(rest.text)
    alive = {group.id for group in seeded} - {target}

    lost = sorted(alive - (set(on_screen) | set(read_on)))
    doubled = sorted(set(on_screen) & set(read_on))

    assert not lost, (
        f"после удаления строки список потерял группы: {lost} — их не "
        f"отрисовала ни первая страница, ни порция, которую дочитает сентинел; "
        f"человек не увидит их до перезагрузки, а линейка счётчика продолжит "
        f"их считать"
    )
    assert not doubled, (
        f"после удаления строка показана дважды: {doubled} — курсор уехал "
        f"дальше, чем документ снял с экрана"
    )
    assert set(on_screen) | set(read_on) == alive, (
        "объединение отрисованного и дочитанного не равно оставшемуся списку"
    )


@pytest.mark.asyncio
async def test_a_no_op_delete_does_not_double_a_row(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Холостое удаление не двигает курсор ни на единицу (D-04-A, QUAL-01).

    Обе половины класса «строка не найдена», достижимые с живого экрана,
    проверяются в одном теле: чужая группа и уже удалённая. Третья половина —
    вовсе несуществующий идентификатор — покрыта задачей 3.

    ⚠️ ЭТОТ ТЕСТ — ЕДИНСТВЕННОЕ, ЧТО СТОИТ МЕЖДУ ПОЧИНКОЙ КУРСОРА И ЕЁ
    ЗЕРКАЛЬНЫМ ОТКАЗОМ. Починка «вычитать единицу всегда» чинит потерю строки и
    заводит её задвоение: на холостом пути внеполосное снятие не находит узла,
    на экране остаются все отрисованные строки, а курсор уезжает назад.
    """
    account = await _seed_account(db_session)
    seeded = await _seed_many(
        db_session, account, [f"Группа {i:02d}" for i in range(PAGE_SIZE + 5)]
    )
    alive = {group.id for group in seeded}

    foreign_user = await _seed_foreign_user(db_session)
    foreign_account = await _seed_account(db_session, user_id=foreign_user.id)
    foreign_group = await _seed_group(
        db_session, foreign_account, "Чужая группа", user_id=foreign_user.id
    )

    # --- (а) идентификатор ЧУЖОЙ группы --------------------------------------
    page = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    rendered = _row_ids(page)

    foreign = await htmx_client.post(
        f"/accounts/{account.id}/groups/{foreign_group.id}/delete"
    )
    assert foreign.status_code == 200, (
        f"холостое удаление получило {foreign.status_code} вместо фрагмента"
    )

    rest = await authed_client.get(_scroll_read_on_url(page, foreign.text))
    read_on = _row_ids(rest.text)

    doubled = sorted(set(rendered) & set(read_on))
    assert not doubled, (
        f"строка показана дважды после удаления, которое ничего не удалило: "
        f"{doubled} — курсор уехал назад там, где с экрана не снялось ни одной "
        f"строки"
    )
    assert set(rendered) | set(read_on) == alive, (
        "холостое удаление сдвинуло состав списка: объединение отрисованного и "
        "дочитанного не равно всем группам аккаунта"
    )
    assert (await db_session.get(Group, foreign_group.id)) is not None, (
        "холостое удаление снесло чужую группу"
    )

    # --- (б) идентификатор УЖЕ УДАЛЁННОЙ группы ------------------------------
    victim = rendered[0]
    first = await htmx_client.post(
        f"/accounts/{account.id}/groups/{victim}/delete"
    )
    assert first.status_code == 200

    page_again = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    rendered_again = _row_ids(page_again)

    repeat = await htmx_client.post(
        f"/accounts/{account.id}/groups/{victim}/delete"
    )
    assert repeat.status_code == 200

    rest_again = await authed_client.get(
        _scroll_read_on_url(page_again, repeat.text)
    )
    read_on_again = _row_ids(rest_again.text)

    doubled_again = sorted(set(rendered_again) & set(read_on_again))
    assert not doubled_again, (
        f"строка показана дважды после повторного удаления уже удалённой "
        f"группы: {doubled_again}"
    )
    assert set(rendered_again) | set(read_on_again) == alive - {victim}, (
        "повторное удаление сдвинуло состав списка"
    )

    # Число внеполосных узлов НЕ ЗАВИСИТ от того, нашлась ли строка: иначе оно
    # само стало бы признаком состоявшегося удаления, и неотличимость сломалась
    # бы с другой стороны (T-09-05-06).
    #
    # ЛЕТОПИСЬ ЧИСЛА: 4 → 3, Фаза 9, план 09-13, решение владельца `keyset` —
    # четвёртый узел (починка курсора) снят вместе с задачей, которую решал.
    # Утверждение НЕ ослаблено: оно по-прежнему говорит, что число одинаково у
    # найденной и у ненайденной строки, и краснеет при возврате условной сборки.
    assert foreign.text.count("hx-swap-oob") == 3, (
        f"на холостом пути внеполосных узлов "
        f"{foreign.text.count('hx-swap-oob')}, а не три — по их числу стало бы "
        f"видно, состоялось ли удаление"
    )
    assert repeat.text.count("hx-swap-oob") == 3, (
        f"на повторном удалении внеполосных узлов "
        f"{repeat.text.count('hx-swap-oob')}, а не три"
    )


@pytest.mark.asyncio
async def test_the_delete_response_never_carries_a_scroll_cursor(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Ответ удаления не несёт узла курсора НИ ПРИ КАКОМ теле запроса.

    ⚠️ ПРАВИЛО ОБРАЩЕНО ПЛАНОМ 09-13 (решение владельца `keyset`), А НЕ СНЯТО, И
    ЭТО НАЗЫВАЕТСЯ ЗДЕСЬ ПРЯМО. Прежде оно звалось
    `test_the_delete_response_repairs_the_sentinel_only_over_htmx` и
    утверждало, что четвёртый узел приезжает ТОЛЬКО когда документ прислал своё
    число отрисованных строк. Числа документ больше не шлёт, и правило в прежней
    форме зеленело бы на любом дереве — включая дерево, куда четвёртый узел
    вернули. Теперь утверждается СИЛЬНОЕ: узла курсора в ответе нет ВООБЩЕ, и
    подослать его нельзя ничем — ни прежним полем, ни любым другим телом.
    Правило краснеет ровно тогда, когда в контракт возвращается величина,
    снимаемая в один момент и применяемая в другой (CR-01).

    Половина пары SP-3: путь деградации не тронут вовсе, и присланное тело его
    не переключает — без признака htmx ответом остаётся прежнее
    перенаправление.

    ⚠️ ПРИЗНАК htmx СНИМАЕТСЯ ЯВНО ПУСТЫМ ЗНАЧЕНИЕМ ЗАГОЛОВКА, А НЕ ВЫБОРОМ
    ФИКСТУРЫ, И ЭТО ВЫНУЖДЕННО. `htmx_client` возвращает ТОТ ЖЕ объект клиента,
    что и `authed_client` (см. её докстринг: складываемость фикстур — несущее
    свойство), поэтому в тесте, запросившем обе, запроса без признака не бывает
    вовсе. Пустое значение считается отсутствием признака ЯВНО и по объявлению
    (`app/pages/htmx.py::is_htmx`), а не по совпадению.
    """
    account = await _seed_account(db_session)
    await _seed_many(
        db_session, account, [f"Группа {i:02d}" for i in range(PAGE_SIZE + 5)]
    )

    page = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    rendered = _row_ids(page)
    target, neighbour, third = rendered[0], rendered[1], rendered[2]

    # ДВА ТЕЛА: пустое и несущее ПРЕЖНЕЕ, СНЯТОЕ ПОЛЕ. Второе — не украшение:
    # оно доказывает, что вернуть починку курсора ПОДСУНУТЫМ полем нельзя.
    # Правило, проверившее только пустое тело, зеленело бы и на обработчике,
    # который снятое поле всё ещё читает.
    for label, victim, body in (
        ("пустом", target, None),
        ("несущем снятое поле", third, {"rendered_rows": 30}),
    ):
        response = await htmx_client.post(
            f"/accounts/{account.id}/groups/{victim}/delete", data=body
        )
        assert response.status_code == 200, (
            f"при {label} теле ответ {response.status_code} вместо фрагмента"
        )
        assert response.text.count("hx-swap-oob") == 3, (
            f"при {label} теле ответ несёт "
            f"{response.text.count('hx-swap-oob')} внеполосных узла вместо трёх "
            f"— в ответе появился узел, которого контракт не предусматривает"
        )
        assert not _sentinels(response.text), (
            f"при {label} теле ответ подменил сентинел — починка курсора "
            f"вернулась в контракт, а вместе с ней и класс отказа CR-01"
        )
        assert f'id="group-row-{victim}"' in response.text, (
            f"при {label} теле узел снятия строки пропал: три узла обязаны "
            f"остаться на месте"
        )
        assert f'id="group-del-{victim}"' in response.text, (
            f"при {label} теле узел снятия панели подтверждения пропал"
        )
        assert 'hx-swap-oob="innerHTML:#account-groups-count"' in response.text, (
            f"при {label} теле узел линейки счётчика пропал"
        )

    degraded = await authed_client.post(
        f"/accounts/{account.id}/groups/{neighbour}/delete",
        data={"rendered_rows": len(rendered)},
        headers={"HX-Request": ""},
        follow_redirects=False,
    )
    assert degraded.status_code == 302, (
        f"запрос без признака htmx получил {degraded.status_code} — присланное "
        "тело переключило путь деградации на фрагментный ответ"
    )
    assert degraded.headers["location"] == f"/accounts/{account.id}/groups"
    assert not _sentinels(degraded.text), (
        "на пути деградации собрался четвёртый внеполосный узел — страница и "
        "так перестраивается целиком вместе с сентинелом"
    )


@pytest.mark.asyncio
async def test_the_sentinel_carries_a_stable_id_in_both_templates(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Идентификатор сентинела ОДИН И ТОТ ЖЕ в обоих местах отрисовки.

    Без стабильного идентификатора узел, названный по-разному на странице и в
    порции, подменял бы себя через раз — ровно у того, кто долистал.

    ⚠️ ТРЕТЬЕ МЕСТО ОТРИСОВКИ СНЯТО ПЛАНОМ 09-13 (решение владельца `keyset`), И
    УТВЕРЖДЕНИЕ О НЁМ НЕ УБРАНО, А ОБРАЩЕНО. Прежде здесь требовалось, чтобы
    ответ удаления нёс ТОТ ЖЕ идентификатор — иначе починка курсора целилась бы
    в узел, которого в документе нет, и рантайм промолчал бы. Теперь требуется
    обратное и не менее строго: ответ удаления не несёт узла курсора ВОВСЕ.
    Утверждение краснеет, если четвёртый узел вернётся в дерево, — то есть если
    вернётся и величина, которую можно снять в один момент и применить в
    другой (CR-01).
    """
    account = await _seed_account(db_session)
    await _seed_many(
        db_session, account, [f"Группа {i:03d}" for i in range(PAGE_SIZE * 2 + 5)]
    )

    page = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    portion = (await authed_client.get(_sentinels(page)[0])).text
    rendered = _row_ids(page)
    response = await htmx_client.post(
        f"/accounts/{account.id}/groups/{rendered[0]}/delete"
    )

    on_page = _sentinel_ids(page)
    in_portion = _sentinel_ids(portion)
    in_response = _sentinel_ids(response.text)

    assert on_page == ["group-list-sentinel"], (
        f"сентинел страницы не несёт стабильного идентификатора: {on_page}"
    )
    assert in_portion == on_page, (
        f"идентификатор сентинела в порции прокрутки разошёлся со страницей: "
        f"{in_portion} против {on_page}"
    )
    assert in_response == [], (
        f"ответ удаления принёс узел курсора {in_response} — курсор снова "
        f"чинится подменой, то есть в контракт вернулась величина, снимаемая в "
        f"один момент и применяемая в другой (CR-01). При ключевом курсоре "
        f"чинить нечего: удаление уже отрисованной строки его не двигает"
    )


# =============================================================================
# План 09-05, Задача 3: новое поле не тронуло ни деградацию, ни неотличимость
# =============================================================================
#
# Поле `rendered_rows` существует ТОЛЬКО на пути htmx: живой документ несёт его
# скрытым полем внутри сентинела, а человек без JavaScript отправляет ту же
# форму без него. Обе половины закрепляются машинно — и обе именно здесь, а не
# рассуждением о том, что «сервер и так проверит».


def _search_param(url: str) -> list[str] | None:
    """Строка поиска, доехавшая до адреса подгрузки, — или None, если её нет."""
    return parse_qs(urlsplit(url).query).get("search")


@pytest.mark.asyncio
async def test_the_delete_degrades_without_the_rendered_rows_field(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Без признака htmx и без нового поля удаление отвечает как прежде.

    Половина пары SP-3 к тестам починки курсора: поле, заведённое ради htmx,
    не имеет права стать обязательным. Фикстура здесь ОДНА намеренно —
    `htmx_client` возвращает тот же объект клиента и выставил бы признак htmx
    всему тесту.
    """
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа деградации курсора")

    response = await authed_client.post(
        f"/accounts/{account.id}/groups/{group.id}/delete", follow_redirects=False
    )

    assert response.status_code == 302, (
        f"запрос без признака htmx и без поля числа строк получил "
        f"{response.status_code} — путь деградации стал требовать поля, "
        f"которого у человека без JavaScript нет вовсе"
    )
    assert response.headers["location"] == f"/accounts/{account.id}/groups"
    assert not response.text, (
        "на пути деградации собралось тело фрагмента — страница и так "
        "перестраивается целиком"
    )
    assert (await db_session.get(Group, group.id)) is None, (
        "удаление на базовом пути не состоялось"
    )


@pytest.mark.asyncio
async def test_the_scroll_cursor_keeps_the_search_filter_after_a_delete(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Курсор дочитывает ОТФИЛЬТРОВАННУЮ выдачу и после удаления.

    Потерянная строка поиска не роняет страницу и не меняет кода ответа: она
    молча подмешивает к найденному остальной список аккаунта, и человек видит в
    выдаче поиска чужие по смыслу строки.

    ⚠️ ИМЯ И ФОРМА ПРАВИЛА СДВИНУТЫ ПЛАНОМ 09-13 (решение владельца `keyset`), А
    ПРЕДМЕТ СОХРАНЁН ЦЕЛИКОМ, И ЭТО НАЗЫВАЕТСЯ ЗДЕСЬ ПРЯМО. Прежде правило
    звалось `test_the_repaired_sentinel_keeps_the_search_filter` и утверждало,
    что ПОЧИНЕННЫЙ ответом удаления сентинел несёт тот же фильтр. Починки
    больше нет; правило с прежним именем стало бы утверждением о несуществующем
    узле, то есть зелёным по построению — ровно та форма отказа, против которой
    заведён этот круг. Спрашивается теперь то же самое, но у ДОКУМЕНТА: узел
    курсора удаление переживает нетронутым, и дочитывание ПОСЛЕ удаления обязано
    вернуть строки только отфильтрованной выдачи.
    """
    account = await _seed_account(db_session)
    await _seed_many(
        db_session, account, [f"Альфа {i:02d}" for i in range(PAGE_SIZE + 5)]
    )
    await _seed_many(db_session, account, [f"Бета {i:02d}" for i in range(5)])

    page = (
        await authed_client.get(
            f"/accounts/{account.id}/groups", params={"search": "Альфа"}
        )
    ).text

    # НЕВАКУУМНОСТЬ ПЕРВЫМ ДЕЛОМ: без сентинела на странице сравнивать было бы
    # нечего, и утверждение о фильтре стало бы зелёным по построению.
    page_sentinels = _sentinels(page)
    assert page_sentinels, (
        "сентинела нет на отфильтрованной странице — поиск отсёк выдачу до "
        "размера страницы, и утверждение о фильтре сравнивать не с чем"
    )
    assert _search_param(page_sentinels[0]) == ["Альфа"], (
        f"строка поиска не доехала до адреса сентинела страницы: "
        f"{page_sentinels[0]}"
    )

    rendered = _row_ids(page)
    response = await htmx_client.post(
        f"/accounts/{account.id}/groups/{rendered[0]}/delete",
        data={"search": "Альфа"},
    )
    assert response.status_code == 200, (
        f"фрагментная ветка не достигнута: {response.status_code}"
    )
    assert not _sentinels(response.text), (
        "ответ удаления принёс узел курсора — курсор снова чинится подменой, и "
        "вместе с починкой возвращается величина, снимаемая в один момент и "
        "применяемая в другой (CR-01)"
    )

    # Документ дочитывает СВОИМ узлом, который удаление не тронуло.
    rest = await authed_client.get(page_sentinels[0])
    assert rest.status_code == 200
    assert _row_ids(rest.text), (
        "дочитывание после удаления не вернуло ни одной строки — утверждение о "
        "фильтре ниже стало бы вакуумным"
    )
    assert "Бета" not in rest.text, (
        f"после удаления курсор дочитал НЕотфильтрованный список: в выдаче "
        f"поиска «Альфа» появились строки «Бета» — {page_sentinels[0]}"
    )


@pytest.mark.asyncio
async def test_the_delete_response_is_indistinguishable_for_a_foreign_and_a_missing_group(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """D-04 (в редакции D-04-A): чужая и несуществующая группа отвечают одинаково.

    ⚠️ ПОСЕВ «ЧУЖАЯ ГРУППА ЕСТЬ, СВОИХ НЕТ» ЗАПРЕЩЁН, И ЭТО ЛОВУШКА, А НЕ
    ПРИДИРКА. Он уводит ОБА запроса в ветку опустевшего списка — она отвечает
    переходом с ПУСТЫМ телом, и тогда два пустых тела равны побайтово, два
    статуса равны, два заголовка равны, а фрагмент не собирается ни разу.
    Ровно этот отказ фаза уже допустила однажды (09-REVIEW.md §WR-04:
    `first=204 body=b'' second=204 body=b''`). Поэтому у действующего человека
    заведены СВОИ группы, и после обоих запросов у него остаётся не меньше
    одной: ни один из двух запросов ничего не удаляет.

    ⚠️ ПОРЯДОК УТВЕРЖДЕНИЙ ВАЖНЕЕ САМОГО СРАВНЕНИЯ. Достижение фрагментной
    ветки утверждается ПЕРВЫМ исполняемым утверждением; без него равенство тел
    вакуумно.
    """
    account = await _seed_account(db_session)
    seeded = await _seed_many(
        db_session, account, [f"Группа {i:02d}" for i in range(PAGE_SIZE + 5)]
    )
    rendered_rows = PAGE_SIZE

    foreign_user = await _seed_foreign_user(db_session)
    foreign_account = await _seed_account(db_session, user_id=foreign_user.id)
    foreign_group = await _seed_group(
        db_session, foreign_account, "Чужая группа", user_id=foreign_user.id
    )
    missing_id = max([group.id for group in seeded] + [foreign_group.id]) + 1000

    body = {"rendered_rows": rendered_rows}
    foreign = await htmx_client.post(
        f"/accounts/{account.id}/groups/{foreign_group.id}/delete", data=body
    )
    missing = await htmx_client.post(
        f"/accounts/{account.id}/groups/{missing_id}/delete", data=body
    )

    # ПЕРВОЕ ИСПОЛНЯЕМОЕ УТВЕРЖДЕНИЕ — О ДОСТИГНУТОЙ ФРАГМЕНТНОЙ ВЕТКЕ.
    assert foreign.status_code == 200, (
        f"фрагментная ветка не достигнута: ответ {foreign.status_code} вместо "
        f"200 — без неё равенство тел ниже вакуумно, потому что сравнивало бы "
        f"два пустых тела ветки перехода"
    )
    assert f'id="group-row-{foreign_group.id}"' in foreign.text, (
        "в теле первого ответа нет узла снятия строки — сравнивать нечего, и "
        "равенство тел ниже было бы зелено по построению"
    )

    assert missing.status_code == foreign.status_code, (
        "чужая и несуществующая группа различимы по коду ответа"
    )
    assert missing.headers.get("HX-Location") == foreign.headers.get("HX-Location"), (
        "чужая и несуществующая группа различимы по адресу перехода"
    )

    # ⚠️ ПОДСТАНОВКА ИДЕНТИФИКАТОРА ЗАКОННА, И ВОТ ПОЧЕМУ. Он приходит из ПУТИ,
    # то есть назван САМИМ спрашивающим; два разных случая одним и тем же
    # идентификатором не адресуются в принципе. Подставляются ровно два якоря, а
    # не всякое вхождение числа, — иначе замена задела бы соседние величины.
    substituted = foreign.text.replace(
        f'id="group-row-{foreign_group.id}"', f'id="group-row-{missing_id}"'
    ).replace(f'id="group-del-{foreign_group.id}"', f'id="group-del-{missing_id}"')

    assert substituted == missing.text, (
        "чужая и несуществующая группа различимы ПО ТЕЛУ ответа — по ответу "
        "можно составить карту чужих идентификаторов перебором по адресу, не "
        "получив ни одной строки"
    )
    assert (await db_session.get(Group, foreign_group.id)) is not None, (
        "чужая группа удалена"
    )


@pytest.mark.asyncio
async def test_a_degenerate_cursor_is_rejected_before_the_database(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Вырожденный ключ курсора отвергается ДО обращения к базе (T-09-13-01).

    ⚠️ ПРАВИЛО ПЕРЕНАЦЕЛЕНО ПЛАНОМ 09-13 (решение владельца `keyset`), А НЕ
    СНЯТО, И КЛАСС УГРОЗЫ У НЕГО ТОТ ЖЕ. Прежде оно звалось
    `test_a_non_positive_rendered_rows_does_not_build_a_sentinel` и утверждало,
    что ноль и отрицательное ЧИСЛО ОТРИСОВАННЫХ СТРОК не строят курсор вовсе
    (T-09-05-01). Поля этого в контракте больше нет, и правило в прежней форме
    зеленело бы на любом дереве — то есть перестало бы отличать закрытую угрозу
    от отменённой. Недоверенная величина курсора никуда не делась, она сменила
    ФОРМУ: теперь это `after_id` в адресе порции. Спрашивается ровно то же —
    вырожденная величина не должна ни уронить обработчик, ни молча оборвать
    список.

    Ключ объявлен `Query(None, ge=1)`, поэтому ноль и отрицательное значение
    отвергаются маршрутом, а не превращаются в тихо съехавшую выдачу. Отсутствие
    ключа — законный случай: он означает «с начала списка», и выдача при нём
    полная, а не пустая.
    """
    account = await _seed_account(db_session)
    seeded = await _seed_many(
        db_session, account, [f"Группа {i:02d}" for i in range(PAGE_SIZE + 5)]
    )

    for value in (0, -5):
        response = await authed_client.get(
            f"/accounts/{account.id}/groups/partial?after_id={value}&limit=30",
            follow_redirects=False,
        )
        assert response.status_code == 422, (
            f"after_id={value} принят маршрутом ({response.status_code}) — "
            f"вырожденный ключ дошёл бы до выборки, и список оборвался бы молча"
        )
        assert not _row_ids(response.text), (
            f"после отказа при after_id={value} в теле оказались строки"
        )

    # АНТИВАКУУМ: отсутствие ключа — не отказ, а «с начала списка». Без этого
    # утверждения правило зеленело бы и на маршруте, отвергающем ВСЁ подряд.
    full = await authed_client.get(
        f"/accounts/{account.id}/groups/partial?limit=30"
    )
    assert full.status_code == 200, (
        f"порция без ключа получила {full.status_code} — «с начала списка» "
        f"перестало быть законным случаем"
    )
    assert _row_ids(full.text) == [group.id for group in seeded[:PAGE_SIZE]], (
        "порция без ключа вернула не начало списка"
    )


# =============================================================================
# План 09-06, Задача 1: ветка «список опустел» решается ПО ТЕКУЩЕЙ ВЫДАЧЕ
# =============================================================================
#
# WR-06 / WARN-6. Ветвление, считанное по числам АККАУНТА, оставляло человека
# перед ПУСТОЙ КАРТОЧКОЙ БЕЗ ВЫХОДА: поиск сузил выдачу до одной строки, человек
# её удалил, `total_groups` остался больше нуля — и ответ снял строку на месте
# фрагментом. Три различимых пустых состояния живут в `account_groups/list.html`
# и во фрагмент не приезжают (D-09), поэтому на экране не оставалось ни ветви
# «Группы не найдены», ни кнопки «Сбросить»: вернуться к неотфильтрованному
# списку можно было только правкой адреса.
#
# Тот же по форме отказ у удаления последней строки ТЕКУЩЕЙ ПОРЦИИ при непустых
# следующих страницах здесь НЕ закрывается и закрываться не должен: выдача не
# пуста, фрагментная ветка верна, а курсор чинит четвёртый внеполосный узел
# плана 09-05.


@pytest.mark.asyncio
async def test_deleting_the_last_matched_row_lands_on_the_empty_state(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Удаление ПОСЛЕДНЕЙ НАЙДЕННОЙ строки закрывается переходом, несущим фильтр.

    ⚠️ НЕВАКУУМНОСТЬ УТВЕРЖДАЕТСЯ ОТДЕЛЬНО: после удаления в аккаунте ОСТАЮТСЯ
    другие группы. Без этой половины тест зеленел бы и на прежней ветке по
    числам аккаунта — та тоже отвечает переходом, когда групп не осталось вовсе,
    и утверждение не сказало бы о починке ничего.
    """
    account = await _seed_account(db_session)
    await _seed_many(db_session, account, ["Бета один", "Бета два", "Бета три"])
    alpha = await _seed_group(db_session, account, "Альфа единственная")

    page = (
        await authed_client.get(
            f"/accounts/{account.id}/groups", params={"search": "Альфа"}
        )
    ).text
    rendered = _row_ids(page)
    assert rendered == [alpha.id], (
        f"поиск отвечает не ровно одной строке ({rendered}) — посев не создаёт "
        f"условия, ради которого тест написан"
    )

    response = await htmx_client.post(
        f"/accounts/{account.id}/groups/{alpha.id}/delete",
        data={"rendered_rows": len(rendered), "search": "Альфа"},
    )

    assert response.status_code == 204, (
        f"удаление последней НАЙДЕННОЙ строки ответило {response.status_code} "
        f"вместо перехода: человек остался перед пустой карточкой без ветви "
        f"«Группы не найдены» и без кнопки «Сбросить» — вернуться к полному "
        f"списку можно только правкой адреса"
    )
    assert not response.content, "у ответа 204 появилось тело"

    location = response.headers["HX-Location"]
    assert _search_param(location) == ["Альфа"], (
        f"адрес перехода не несёт строки поиска: {location} — человек "
        f"приземляется на НЕотфильтрованный список и не видит, что его поиск "
        f"больше ничему не отвечает"
    )

    remaining = (
        (
            await db_session.execute(
                select(Group).where(Group.account_id == account.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(remaining) == 3, (
        f"в аккаунте осталось {len(remaining)} групп вместо трёх — утверждение "
        f"о ветке вакуумно: она совпала бы со старой веткой «групп не осталось "
        f"вовсе»"
    )


@pytest.mark.asyncio
async def test_deleting_the_last_matched_row_degrades_with_the_filter(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Путь деградации сохраняет фильтр: перенаправление несёт ту же строку.

    Фикстура здесь ОДНА намеренно — `htmx_client` возвращает тот же объект
    клиента и выставил бы признак htmx всему тесту.
    """
    account = await _seed_account(db_session)
    await _seed_many(db_session, account, ["Бета один", "Бета два"])
    alpha = await _seed_group(db_session, account, "Альфа единственная")

    response = await authed_client.post(
        f"/accounts/{account.id}/groups/{alpha.id}/delete",
        data={"search": "Альфа"},
        follow_redirects=False,
    )

    assert response.status_code == 302, (
        f"запрос без признака htmx получил {response.status_code} — путь "
        f"деградации перестал быть прежним"
    )
    assert _search_param(response.headers["location"]) == ["Альфа"], (
        f"перенаправление после удаления потеряло строку поиска: "
        f"{response.headers['location']} — человек без JavaScript приземляется "
        f"на НЕотфильтрованный список"
    )
    assert (await db_session.get(Group, alpha.id)) is None, (
        "удаление на базовом пути не состоялось"
    )


@pytest.mark.asyncio
async def test_the_delete_branch_does_not_reveal_a_foreign_group_under_search(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Под активным поиском чужая и несуществующая группа отвечают одинаково.

    Смена условия ветвления не имеет права завести различимость: у ЧУЖОЙ и у
    НЕСУЩЕСТВУЮЩЕЙ группы текущая выдача не меняется ни на строку, значит и
    ветка у них та же, какой она была бы у соседнего успешного удаления в том же
    аккаунте (D-04 в редакции D-04-A, T-9-10).

    ⚠️ ПОРЯДОК УТВЕРЖДЕНИЙ ВАЖНЕЕ САМОГО СРАВНЕНИЯ: достижение фрагментной ветки
    утверждается ПЕРВЫМ исполняемым утверждением, иначе равенство тел вакуумно.
    """
    account = await _seed_account(db_session)
    seeded = await _seed_many(
        db_session, account, ["Альфа один", "Альфа два", "Альфа три"]
    )

    foreign_user = await _seed_foreign_user(db_session)
    foreign_account = await _seed_account(db_session, user_id=foreign_user.id)
    foreign_group = await _seed_group(
        db_session, foreign_account, "Альфа чужая", user_id=foreign_user.id
    )
    missing_id = max([group.id for group in seeded] + [foreign_group.id]) + 1000

    body = {"rendered_rows": len(seeded), "search": "Альфа"}
    foreign = await htmx_client.post(
        f"/accounts/{account.id}/groups/{foreign_group.id}/delete", data=body
    )
    missing = await htmx_client.post(
        f"/accounts/{account.id}/groups/{missing_id}/delete", data=body
    )

    # ПЕРВОЕ ИСПОЛНЯЕМОЕ УТВЕРЖДЕНИЕ — О ДОСТИГНУТОЙ ФРАГМЕНТНОЙ ВЕТКЕ.
    assert foreign.status_code == 200, (
        f"фрагментная ветка под поиском не достигнута: ответ "
        f"{foreign.status_code} вместо 200 — равенство тел ниже сравнивало бы "
        f"два пустых тела ветки перехода"
    )
    assert f'id="group-row-{foreign_group.id}"' in foreign.text, (
        "в теле первого ответа нет узла снятия строки — сравнивать нечего, и "
        "равенство тел ниже было бы зелено по построению"
    )

    assert missing.status_code == foreign.status_code, (
        "под активным поиском чужая и несуществующая группа различимы по коду "
        "ответа"
    )
    assert missing.headers.get("HX-Location") == foreign.headers.get("HX-Location"), (
        "под активным поиском чужая и несуществующая группа различимы по адресу "
        "перехода"
    )

    # Подстановка идентификатора законна: он приходит из ПУТИ, то есть назван
    # САМИМ спрашивающим, и двумя разными случаями один и тот же идентификатор
    # не адресуется (тот же приём, что в плане 09-05, задача 3).
    substituted = foreign.text.replace(
        f'id="group-row-{foreign_group.id}"', f'id="group-row-{missing_id}"'
    ).replace(f'id="group-del-{foreign_group.id}"', f'id="group-del-{missing_id}"')

    assert substituted == missing.text, (
        "под активным поиском чужая и несуществующая группа различимы ПО ТЕЛУ "
        "ответа — по ответу можно составить карту чужих идентификаторов "
        "перебором по адресу, не получив ни одной строки"
    )
    assert (await db_session.get(Group, foreign_group.id)) is not None, (
        "холостое удаление снесло чужую группу"
    )


# =============================================================================
# Объявленные включаемые данные против отрисованного документа (DIV-09-01)
# =============================================================================
#
# ⚠️ ПРАВИЛО ПОВЕДЕНЧЕСКОЕ, А НЕ СКАНИРУЮЩЕЕ ИСХОДНИК, И ЭТО НЕ ВЫБОР СТИЛЯ.
# Узел, на который целится объявление включаемых данных, рисуется УСЛОВИЕМ
# обработчика («есть следующая порция»), а само объявление печатается
# БЕЗУСЛОВНО. По тексту шаблонов узнать, стоят ли они рядом на живом экране,
# нельзя в принципе: оба фрагмента разметки в исходнике есть всегда. Поэтому
# документ рисуется НАСТОЯЩИМ обработчиком, и селекторы сверяются с
# идентификаторами ТОГО ЖЕ документа.
#
# Вреда данным у разрыва нет — это проверено по коду: число отрисованных строк
# приходит пустым, смещение не собирается, четвёртый внеполосный узел не
# отправляется. Вред другой: разрешатель селекторов при нуле совпадений
# возвращает детачнутый узел и пишет строку в консоль на КАЖДОЕ удаление, а на
# признак «ответ 200 и ЧИСТАЯ КОНСОЛЬ» обход опирается в трёх местах.

# Значение объявления включаемых данных — как оно стоит в ОТРИСОВАННОМ
# документе.
INCLUDE_ATTR_RE = re.compile(r'hx-include="([^"]*)"')

# Селектор, называющий ИДЕНТИФИКАТОР, — и только он. Селектор по классу, по
# атрибуту или с префиксом обхода дерева идентификатора не называет, и сверять
# его с множеством идентификаторов документа значило бы сравнивать разные
# величины: правило переехало бы на другой предмет и молча зеленело.
ID_SELECTOR_RE = re.compile(r"^#([A-Za-z][\w:.-]*)$")

# Идентификатор узла документа. Граница слева обязательна: без неё
# `data-group-id="5"` прочиталось бы как идентификатор `5`, и множество
# идентификаторов документа распухло бы вымышленными узлами — то есть правило
# зеленело бы ровно там, где узла на самом деле нет.
DOCUMENT_ID_RE = re.compile(r'(?<![\w-])id="([^"]*)"')

# ⚠️ ЧИСЛО ОБЪЯВЛЕНИЙ ВЫПИСАНО ОТДЕЛЬНЫМ УТВЕРЖДЕНИЕМ НАМЕРЕННО (идиома SP-1).
# Без него правило зеленело бы от того, что разборщик перестал находить
# объявления ВОВСЕ, — то есть молчало бы громче всего там, где сломалось
# сильнее всего: разность пустого множества с любым другим пуста.
#
# ⚠️ ЧИСЛО ПЕРЕМЕРЕНО ПЛАНОМ 09-11 ПОСЛЕ ПРАВКИ, И МЕСТО ИЗМЕРЕНИЯ ПЕРЕЕХАЛО.
# ЛЕТОПИСЬ:
#   3, план 09-11, задача 1 — измерено на СПИСКЕ КОРОЧЕ СТРАНИЦЫ: объявление
#     печаталось БЕЗУСЛОВНО, поэтому три строки давали три объявления при
#     полном отсутствии цели в документе. Это и было предъявленным DIV-09-01.
#   3 → 30, план 09-11, задача 3 — ветвь владельца `conditional-include`
#     сделала объявление условным, и на списке короче страницы объявлений не
#     стало ВОВСЕ (см. INCLUDE_DECLARATIONS_ON_A_SHORT_LIST ниже). Антивакуумное
#     утверждение обязано жить там, где объявления ЕСТЬ, иначе оно перестаёт
#     быть антивакуумным: измерение переехало на страницу КРУПНОГО аккаунта, где
#     следующая порция есть и узел курсора в документе стоит.
#
# Число ИЗМЕРЕНО на живом дереве, а не выведено ожиданием: страница крупного
# аккаунта рисует полную страницу строк, и панель подтверждения строки —
# единственное место экрана, объявляющее включаемые данные. С сегодняшним
# размером страницы оно совпадает, но выведено НЕ из него: сменившийся размер
# страницы обязан покраснеть здесь и быть перемеренным осознанно, а не
# подстроиться молча.
#
#   30 → 0, план 09-13, задача 4, решение владельца `keyset` — ПРЕДМЕТ СНЯТ.
#     Курсор прокрутки стал ключом последней отрисованной строки, поэтому
#     панели подтверждения нечего включать из живого документа: объявление
#     снято с вызова панели, и объявлений включаемых данных на экране групп не
#     осталось НИ ОДНОГО. Число перемерено прогоном на отгруженном дереве.
#
# ⚠️ ОБНУЛИВШИЙСЯ ПРЕДМЕТ ДЕЛАЕТ ПРАВИЛО ВАКУУМНЫМ, И ЭТО ЗАКРЫТО ДВУМЯ
# ПОЛОВИНАМИ, А НЕ ОДНОЙ. Правило вида «объявленное достижимо» на дереве без
# объявлений зеленеет ВСЕГДА: разность пустого множества с любым пуста. Такое
# правило перестаёт отличать ЗАКРЫТУЮ запись от ТИХО ОТМЕНЁННОЙ — то есть
# становится ровно той формой отказа, ради поимки которой круг и собран
# (цена WARN-4 первого круга уже оплачена однажды). Поэтому:
#   (а) антивакуум ПЕРЕЕХАЛ на ПОДСТАВЛЕННОЕ дерево — см.
#       SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED ниже;
#   (б) у правила заведён свой отрицательный контроль
#       test_control_negative_an_include_declaration_without_a_target_reddens_the_gate.
# Ни одна из половин не факультативна: (а) без (б) утверждает, что предмет
# найдётся, но не что правило на нём краснеет; (б) без (а) доказывает зубы на
# синтетике, не измерив предмета. Обе проверяются гейтом плана, а не поручены
# прозой.
#
# ⚠️ ПРАВИЛО ОСТАЁТСЯ ЗАРЯЖЕННЫМ НА ФАЗУ 15, раздающую формы массово: вернувшееся
# в дерево объявление включаемых данных немедленно поднимет это число, и решение
# о нём придётся принять, а не обнаружить через фазу.
INCLUDE_DECLARATIONS_MEASURED = 0

# ⚠️ ЧИСЛО ОБЪЯВЛЕНИЙ НА ПОДСТАВЛЕННОМ ДЕРЕВЕ — ВТОРАЯ ПОЛОВИНА ЗАМЕНЫ (идиома
# SP-1). Заведено планом 09-13, задача 4, и вот ПОЧЕМУ: живого предмета у
# правила в дереве больше нет, а правило обязано остаться способным отличать
# достижимое объявление от недостижимого. Поэтому антивакуум снимается с
# дерева, ПОДСТАВЛЕННОГО существующим механизмом подстановки этого файла
# (`re.subn` по живой странице — тот же приём, которым собирается склейка
# `glued`), а живое дерево при доказательстве не правится ни на символ.
#
# Значение ПОСТАВЛЕНО ИЗМЕРЕНИЕМ на подставленном дереве, а не ожиданием и не
# переносом прежних тридцати. ⚠️ И ИЗМЕРЕНИЕ ЭТО СРАЗУ ЖЕ ОПРАВДАЛО СЕБЯ:
# ожидание было «тридцать, по числу строк страницы», а прогон вернул ШЕСТЬДЕСЯТ.
# Подстановка идёт на КАЖДОЕ место, отправляющее POST, а таких у строки ДВА —
# форма тумблера и форма панели подтверждения. Ровно это и есть причина, по
# которой числа в этом дереве ставятся прогоном, а не арифметикой: число,
# выведенное умножением «строк на единицу», зеленело бы и на дереве, где
# подстановка попала не туда.
#
# ЛЕТОПИСЬ: 0 → 60, Фаза 9, план 09-13, задача 4 — константа заведена вместе с
# переездом антивакуума на подставленное дерево.
SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED = 60

# ⚠️ НОЛЬ ЗДЕСЬ — САМО СОДЕРЖАНИЕ ПОЧИНКИ, А НЕ ОТСУТСТВИЕ ИЗМЕРЕНИЯ. У списка
# короче страницы узла курсора нет НИКОГДА, и строка, узнавшая об этом от
# отрисовщика, не объявляет включаемые данные вовсе. Утверждается это числом, а
# не молчанием: вернувшееся сюда объявление означает, что признак перестал
# доезжать до вызова панели, и строка в консоли вернулась на КАЖДОЕ удаление —
# ровно то расхождение, которое план 09-11 закрывал.
#
# Вместе с INCLUDE_DECLARATIONS_MEASURED эти два числа утверждают свойство
# сильнее исходного: объявление появляется РОВНО ТОГДА, когда цель есть.
INCLUDE_DECLARATIONS_ON_A_SHORT_LIST = 0


@dataclass(frozen=True)
class IncludeTargetException:
    """Положение экрана, в котором объявленная цель включаемых данных недостижима.

    ``position`` — то самое положение, названное словами: запись обязана
    сообщать, ГДЕ объявление остаётся без цели, иначе следующий читатель примет
    её за общее разрешение расходиться.
    ``assigned_phase`` — фаза, которой отступление назначено. Запись без
    назначенной фазы есть бессрочный долг, а не принятое решение.
    ``reason`` — обоснование.
    """

    position: str
    assigned_phase: str
    reason: str


# ⚠️ ПЕРЕЧЕНЬ ОБЪЯВЛЕН, А НЕ ВЫВЕДЕН ИЗ ФАКТА РАСХОЖДЕНИЯ, И ЭТО СУТЬ ФОРМЫ
# (идиома SP-1, источник — tests/test_pages/test_impersonation_gate.py). Правило
# ниже могло бы просто вычесть недостижимое из проверяемого — и тогда КАЖДОЕ
# следующее такое же расхождение попало бы под исключение молча, в тот же миг,
# как появилось. Здесь у записи написано, ПОЧЕМУ она есть и КОГДА закроется, и
# добавление новой требует написать причину — то есть принять решение.
#
# ⚠️ ЗАПИСЬ ЗАВЕДЕНА РЕШЕНИЕМ ВЛАДЕЛЬЦА, А НЕ ПРИЁМКОЙ (план 09-11, задача 2,
# ответ `conditional-include`). Сужение правила до первого положения экрана
# владельцем отклонено прямым текстом: правило потеряло бы зубы на втором
# положении навсегда, и следующее такое же расхождение там прошло бы молча.
INCLUDE_TARGET_EXCEPTIONS: dict[str, IncludeTargetException] = {}

# ⚠️ ЗАПИСЬ `group-list-sentinel` ЗАКРЫТА ПЛАНОМ 09-13, А НЕ УДАЛЕНА МОЛЧА, И
# ПРЕЖНИЙ ЕЁ ТЕКСТ СОХРАНЁН НИЖЕ ЦЕЛИКОМ. ПРЕДМЕТ СНЯТ, А НЕ ОТЛОЖЕН:
# объявлений включаемых данных в дереве не осталось ни одного, поэтому
# отступление закрыто ЗДЕСЬ, а не перенесено в назначенную ему Фазу 15.
# Назначенная фаза обязана увидеть, ЧТО именно ей назначалось и почему это
# перестало существовать, — иначе закрытие неотличимо от тихой отмены.
#
# ⚠️ ОБСТОЯТЕЛЬСТВО, ИЗМЕНИВШЕЕ РЕШЕНИЕ, НАЗЫВАЕТСЯ ПРЯМО. Прежняя запись
# объясняла, что закрыть ОБА следствия DIV-09-01 разом мог только вариант
# `always-present-cursor`, и он отклонён владельцем как `costly` — он снимал
# совпадение «число отрисованных строк = смещение следующей порции». Ветвь
# `keyset` плана 09-13 снимает то же совпадение, и владелец пересмотрел отказ
# СОЗНАТЕЛЬНО: та самая арифметика оказалась источником зеркального отказа
# CR-01, доказанного исполнением (задача 1, коммит RED), и «не трогать её»
# перестало быть безрисковым выбором.
#
# --- ПРЕЖНИЙ ТЕКСТ ЗАПИСИ, СОХРАНЁННЫЙ ДОСЛОВНО ---------------------------
#
# INCLUDE_TARGET_EXCEPTIONS: dict[str, IncludeTargetException] = {
#     "group-list-sentinel": IncludeTargetException(
#         position=(
#             "долистали до конца: последняя порция пришла без узла курсора, а "
#             "строки ПЕРВОЙ порции сохранили объявление, поставленное при их "
#             "отрисовке"
#         ),
#         assigned_phase="Фаза 15 — Упрочнение и сводный обход 47 форм",
#         reason=(
#             "ВТОРОЕ СЛЕДСТВИЕ DIV-09-01, ОСТАВЛЕННОЕ ОТКРЫТЫМ СОЗНАТЕЛЬНО И "
#             "РЕШЕНИЕМ ВЛАДЕЛЬЦА, А НЕ НЕЗАМЕЧЕННОЕ. Ветвь `conditional-include` "
#             "ставит признак ПРИ ОТРИСОВКЕ строки, а узел курсора уходит из "
#             "документа ПОЗЖЕ — когда человек долистал до конца и последняя "
#             "порция пришла без него. Строки первой порции переписать задним "
#             "числом отрисовщику нечем, и объявление на них остаётся. Первое и "
#             "основное следствие — аккаунт с числом групп не больше размера "
#             "страницы, где узла нет НИКОГДА и строка в консоли валилась на "
#             "КАЖДОЕ удаление — закрыто целиком: там объявления больше нет вовсе. "
#             "ЗАКРЫТЬ ОБА РАЗОМ МОГ ТОЛЬКО ВАРИАНТ `always-present-cursor`, И ОН "
#             "ОТКЛОНЁН ВЛАДЕЛЬЦЕМ С ПРИЧИНОЙ: он `costly` — меняет контракт узла, "
#             "который несут три места отрисовки и ответ удаления, и снимает "
#             "совпадение «число отрисованных строк = смещение следующей порции», "
#             "на котором стоит вся арифметика починки курсора CR-01, шипнутой "
#             "планом 09-05. Переигрывать её в круге закрытия расхождений, в конце "
#             "фазы, на арифметике, которую предыдущий план чинил, признано "
#             "рискованным. Вариант `defer` отклонён потому, что строка осталась бы "
#             "в консоли на каждое удаление у большинства аккаунтов. "
#             "ВРЕДА ДАННЫМ У ОСТАТКА НЕТ, и это проверено по коду: число "
#             "отрисованных строк приходит пустым, смещение не собирается, "
#             "четвёртый внеполосный узел не отправляется — что КОРРЕКТНО, чинить "
#             "нечего, узла курсора в документе нет. Остаётся строка в консоли, то "
#             "есть потерянный диагностический признак, и остаётся она на "
#             "положении, которого достигает не каждый пользователь."
#         ),
#     ),
# }
#
# # ⚠️ ЧИСЛО ВЫПИСАНО ОТДЕЛЬНОЙ КОНСТАНТОЙ НАМЕРЕННО (второе утверждение SP-1).
# # Беззвучно выросшее означает, что объявленная цель разошлась с документом ещё
# # где-то, а решения об этом никто не принимал; беззвучно упавшее — что
# # отступление закрыто, и это обязано быть записано следующей строкой летописи, а
# # не обнаружено через фазу.
# #
# # ЛЕТОПИСЬ:
# #   0 → 1, Фаза 9, план 09-11 — второе следствие DIV-09-01, назначено Фазе 15.
#
# --- КОНЕЦ СОХРАНЁННОГО ТЕКСТА --------------------------------------------

#   1 → 0, Фаза 9, план 09-13, задача 4 — ПРЕДМЕТ СНЯТ, А НЕ ОТЛОЖЕН:
#     объявлений включаемых данных в дереве не осталось ни одного, поэтому
#     отступление закрыто планом 09-13, а не перенесено в Фазу 15. Прежний
#     текст записи сохранён комментарием выше целиком.
INCLUDE_TARGET_EXCEPTIONS_DECLARED = 0


def _include_selectors(html: str) -> set[str]:
    """Идентификаторы, названные объявлениями включаемых данных документа.

    Возвращаются ТОЛЬКО селекторы вида «по идентификатору», без ведущего
    символа. Селекторы иного вида в выборку не попадают: о них это правило не
    утверждает ничего и утверждать не может.
    """
    return {
        found.group(1)
        for value in INCLUDE_ATTR_RE.findall(html)
        if (found := ID_SELECTOR_RE.match(value.strip()))
    }


def _with_include_declarations(html: str, target: str) -> tuple[str, int]:
    """ПОДСТАВЛЕННОЕ дерево: объявления включаемых данных возвращены на место.

    ⚠️ ПОМОЩНИК ЗАВЕДЁН ПЛАНОМ 09-13, ЗАДАЧА 4, И ВОТ ЗАЧЕМ. Ветвь владельца
    `keyset` сняла объявления включаемых данных с дерева целиком, и правило о
    их достижимости осталось БЕЗ ПРЕДМЕТА — на живом дереве оно зеленеет
    всегда. Чтобы правило сохранило способность отличать достижимое объявление
    от недостижимого, предмет ему подставляется: объявление возвращается на
    КАЖДОЕ место подтверждения полученной с экрана страницы.

    ⚠️ ПОДСТАВЛЯЕТСЯ СТРОКА ОТВЕТА, А НЕ ФАЙЛ НА ДИСКЕ: живое дерево при
    доказательстве зубов не правится ни на символ. Возвращается ещё и ЧИСЛО
    подстановок — механизм, переставший попадать в места подтверждения, обязан
    быть отличим от дерева, где мест не осталось.
    """
    return re.subn(r'(?<![-\w])hx-post="', f'hx-include="#{target}" hx-post="', html)


def _document_ids(html: str) -> set[str]:
    """Идентификаторы всех узлов документа."""
    return set(DOCUMENT_ID_RE.findall(html))


@pytest.mark.asyncio
async def test_no_declared_include_selector_names_an_id_the_document_lacks(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Каждый объявленный источник включаемых данных есть В ЭТОМ ЖЕ документе.

    Утверждается на ОБОИХ достижимых с экрана положениях, и одного мало:

    * у аккаунта с числом групп не больше размера страницы сентинела нет
      НИКОГДА — это основной путь в бою, а не край случая;
    * у аккаунта крупнее сентинел на первой странице есть, но после
      долистывания до конца уходит из документа насовсем — дальше то же самое.

    Правило, закрывшее только первое, оставило бы второе молчаливым.

    ⚠️ ГРАНИЦА МОДЕЛИ ВТОРОГО ПОЛОЖЕНИЯ НАЗВАНА ПРЯМЫМ ТЕКСТОМ. Склейка
    «страница, в которой узел сентинела заменён телом последней порции»
    ПОДРАЖАЕТ подмене `outerHTML`, а не исполняет её: рантайма здесь нет, и
    тест проверяет СООТНОШЕНИЕ объявлений с идентификаторами получившегося
    документа, а не работу механизма подмены. Того, что рантайм действительно
    подменит узел именно так, это утверждение не доказывает и доказать не
    может — доказано оно отдельно, тестами самого сентинела.

    ⚠️ ГДЕ ЖИВЁТ АНТИВАКУУМ ПОСЛЕ ПРАВКИ ПЛАНА 09-11 — НАЗВАНО ЗДЕСЬ, А НЕ
    ОСТАВЛЕНО НА ДОГАДКУ. Ветвь владельца `conditional-include` сделала
    объявление УСЛОВНЫМ, и на первом положении экрана объявлений не стало вовсе:
    там утверждение о достижимости зелено по построению, и притворяться иначе
    нечестно. Поэтому антивакуум держат ТРИ утверждения, а не молчание:
    измеренное число объявлений на КРУПНОМ аккаунте (их там полная страница),
    измеренный НОЛЬ на коротком списке — это и есть содержание починки, — и
    отрицательный контроль помощников на синтетической разметке: он ловит
    сломавшийся разборщик независимо от дерева.

    ⚠️ ВТОРОЕ ПОЛОЖЕНИЕ ЗЕЛЕНЕЕТ ЧЕРЕЗ ИМЕНОВАННЫЙ ПЕРЕЧЕНЬ, А НЕ ЧЕРЕЗ СНЯТОЕ
    УТВЕРЖДЕНИЕ. Недостижимая цель принимается ТОЛЬКО если она записана в
    ``INCLUDE_TARGET_EXCEPTIONS`` — с обоснованием, назначенной фазой и отдельно
    утверждаемым числом. Любая ДРУГАЯ недостижимая цель здесь краснеет, как и
    краснела: правило не сужено ни на одно из двух положений экрана.
    """
    # --- Отрицательный контроль помощников: правило не переезжает на другой
    #     предмет. Селектор, идентификатора не называющий, в выборку не
    #     попадает — иначе разность множеств распухла бы селекторами, о
    #     достижимости которых правило не утверждает ничего.
    mixed = (
        '<form hx-include="#real-node"></form>'
        '<form hx-include="closest form"></form>'
        '<form hx-include=".form-busy"></form>'
        '<div id="real-node" data-group-id="777"></div>'
    )
    assert _include_selectors(mixed) == {"real-node"}, (
        "выборка объявлений собрала не только селекторы по идентификатору: "
        f"{_include_selectors(mixed)} — правило будет сравнивать разные "
        f"величины и краснеть на том, о чём не утверждает"
    )
    assert _document_ids(mixed) == {"real-node"}, (
        f"множество идентификаторов документа собрано неверно: "
        f"{_document_ids(mixed)} — граница слева в разборщике идентификатора "
        f"потеряна, и документ «несёт» узлы, которых у него нет"
    )

    # --- Положение 1: сентинела нет НИКОГДА -------------------------------
    account = await _seed_account(db_session)
    await _seed_many(db_session, account, [f"Группа {i:02d}" for i in range(3)])

    page = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    assert len(_row_ids(page)) == 3, (
        f"страница отрисовала {len(_row_ids(page))} строк вместо трёх — посев "
        f"не создаёт положения «список короче страницы», ради которого "
        f"утверждение написано"
    )
    assert not _sentinel_ids(page), (
        "у списка короче страницы в документе оказался сентинел — посев не "
        "даёт первого положения экрана"
    )

    declarations = INCLUDE_ATTR_RE.findall(page)
    assert len(declarations) == INCLUDE_DECLARATIONS_ON_A_SHORT_LIST, (
        f"объявлений включаемых данных на коротком списке {len(declarations)}, "
        f"а измерено было {INCLUDE_DECLARATIONS_ON_A_SHORT_LIST}: у списка "
        f"короче страницы узла курсора нет НИКОГДА, и строка, узнавшая об этом "
        f"от отрисовщика, объявлять включаемые данные не должна вовсе. "
        f"Вернувшееся объявление означает, что признак has_sentinel перестал "
        f"доезжать до вызова панели, и строка в консоли вернулась на КАЖДОЕ "
        f"удаление — ровно то расхождение, которое план 09-11 закрывал"
    )

    unreachable = _include_selectors(page) - _document_ids(page)
    assert not unreachable, (
        f"панель подтверждения объявляет источник включаемых данных, которого "
        f"документ не несёт: {sorted(unreachable)} — положение экрана «список "
        f"короче страницы, сентинела нет никогда». Разрешатель селекторов "
        f"вернёт детачнутый узел и напишет строку в консоль на КАЖДОЕ удаление "
        f"на этом экране, и опорный признак обхода «ответ 200 и чистая "
        f"консоль» перестанет работать на основном пути в бою"
    )

    # --- Положение 2: долистали до конца ----------------------------------
    big = await _seed_account(db_session)
    await _seed_many(
        db_session, big, [f"Хвост {i:02d}" for i in range(PAGE_SIZE + 5)]
    )

    big_page = (await authed_client.get(f"/accounts/{big.id}/groups")).text
    urls = _sentinels(big_page)
    assert len(urls) == 1, (
        f"на странице крупного аккаунта адресов дочитывания {len(urls)}, а не "
        f"один — посев не даёт положения «есть следующая порция»"
    )

    # --- ЖИВОЕ ДЕРЕВО: ОБЪЯВЛЕНИЙ НЕТ НИ ОДНОГО, И ЭТО ИЗМЕРЕНО --------
    #
    # ⚠️ ЗДЕСЬ ЖИЛ АНТИВАКУУМ ДО ПЛАНА 09-13, И ОН ОТСЮДА ПЕРЕЕХАЛ, А НЕ ПРОПАЛ.
    # Прежде это было единственное положение экрана, где объявления есть по
    # замыслу, и число `INCLUDE_DECLARATIONS_MEASURED = 30` держало правило от
    # вакуума. Ветвь владельца `keyset` сняла объявления с дерева целиком,
    # поэтому здесь теперь утверждается ИЗМЕРЕННЫЙ НОЛЬ — факт о дереве, а не
    # молчание, — а антивакуум держит ПОДСТАВЛЕННОЕ дерево ниже.
    big_declarations = INCLUDE_ATTR_RE.findall(big_page)
    assert len(big_declarations) == INCLUDE_DECLARATIONS_MEASURED, (
        f"объявлений включаемых данных на странице крупного аккаунта "
        f"{len(big_declarations)}, а измерено было "
        f"{INCLUDE_DECLARATIONS_MEASURED}: объявление вернулось в дерево, и "
        f"решения об этом никто не принимал — либо ушло вместе с чем-то ещё"
    )

    unreachable_on_a_full_page = _include_selectors(big_page) - _document_ids(
        big_page
    )
    assert not unreachable_on_a_full_page, (
        f"панель подтверждения объявляет источник включаемых данных, которого "
        f"документ не несёт: {sorted(unreachable_on_a_full_page)}"
    )

    # --- ПОДСТАВЛЕННОЕ ДЕРЕВО: ЗДЕСЬ ЖИВЁТ АНТИВАКУУМ (половина «а») ------
    #
    # ⚠️ ЖИВОЕ ДЕРЕВО ПРИ ЭТОМ НЕ ПРАВИТСЯ НИ НА СИМВОЛ: подстановка идёт по
    # строке ответа, уже полученного с экрана. Без этой половины правило на
    # дереве без объявлений зеленело бы ВСЕГДА — разность пустого множества с
    # любым пуста, — то есть перестало бы отличать закрытую запись от тихо
    # отменённой.
    substituted, substituted_count = _with_include_declarations(
        big_page, "group-list-sentinel"
    )
    assert substituted_count == SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED, (
        f"подстановка вернула {substituted_count} объявлений вместо измеренных "
        f"{SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED} — механизм подстановки "
        f"перестал попадать в места подтверждения, и утверждения ниже говорили "
        f"бы не о том документе"
    )
    substituted_declarations = _include_selectors(substituted)
    assert substituted_declarations, (
        "на ПОДСТАВЛЕННОМ дереве объявлений включаемых данных не найдено ни "
        "одного — правило зелено ПО ПОСТРОЕНИЮ и о достижимости не утверждает "
        "ничего"
    )

    unreachable_substituted = substituted_declarations - _document_ids(substituted)
    assert not unreachable_substituted, (
        f"на подставленном дереве объявленный источник недостижим: "
        f"{sorted(unreachable_substituted)} — узел курсора на странице крупного "
        f"аккаунта СТОИТ, значит недостижимость может взяться только из "
        f"потерянного идентификатора, и правило ловит именно её"
    )


def _last_portion_glued_in(big_page: str, portion: str) -> str:
    """Документ, каким он станет ПОСЛЕ долистывания до конца.

    Узел курсора подменяется телом последней порции — той, что пришла без
    собственного адреса дочитывания. Подражание подмене `outerHTML`, а не её
    исполнение: рантайма у суиты нет, и утверждается СООТНОШЕНИЕ объявлений с
    идентификаторами получившегося документа.
    """
    glued, replaced = re.subn(
        r'<div id="group-list-sentinel".*?</div>',
        lambda _: portion,
        big_page,
        flags=re.S,
    )
    assert replaced == 1, (
        f"узел сентинела на странице подменён {replaced} раз вместо одного — "
        f"склейка не воспроизводит документ после долистывания"
    )
    return glued


@pytest.mark.asyncio
async def test_control_negative_an_include_declaration_without_a_target_reddens_the_gate(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ЗУБЫ ПРАВИЛА включаемых данных: объявление без цели обязано КРАСНИТЬ.

    ⚠️ ВТОРАЯ ПОЛОВИНА ЗАМЕНЫ, И БЕЗ НЕЁ ПЕРВАЯ НЕ ЗАКРЫВАЕТ НИЧЕГО (план
    09-13, задача 4). Ветвь владельца `keyset` сняла с дерева объявления
    включаемых данных целиком, и правило
    `test_no_declared_include_selector_names_an_id_the_document_lacks` на живом
    дереве стало зелёным по построению. Измеренный антивакуум на подставленном
    дереве говорит, что предмет НАЙДЁТСЯ; этот контроль говорит, что правило на
    нём КРАСНЕЕТ. Два разных высказывания, и второе из первого не следует.

    ⚠️ ЖИВОЕ ДЕРЕВО ПРИ ДОКАЗАТЕЛЬСТВЕ НЕ ПРАВИТСЯ. Подставляется строка
    ответа, уже полученного с экрана, а не файл на диске.

    ВОСПРОИЗВОДИТСЯ ИМЕННО ТОТ ОТКАЗ, КОТОРЫЙ ФАЗА ЛОВИЛА ЖИВЬЁМ (DIV-09-01,
    второе следствие): объявление, поставленное строке при отрисовке, остаётся
    на ней и после того, как узел курсора ушёл из документа насовсем.
    """
    account = await _seed_account(db_session)
    await _seed_many(
        db_session, account, [f"Хвост {i:02d}" for i in range(PAGE_SIZE + 5)]
    )

    big_page = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    urls = _sentinels(big_page)
    assert len(urls) == 1, (
        f"на странице крупного аккаунта адресов дочитывания {len(urls)}, а не "
        f"один — посев не даёт положения «есть следующая порция»"
    )

    portion = (await authed_client.get(urls[0])).text
    assert not _sentinels(portion), (
        "последняя порция принесла собственный адрес дочитывания — посев не "
        "доводит экран до положения «долистали до конца»"
    )

    substituted, count = _with_include_declarations(big_page, "group-list-sentinel")
    assert count == SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED, (
        f"подстановка вернула {count} объявлений вместо измеренных "
        f"{SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED}"
    )

    # ДО долистывания цель В ДОКУМЕНТЕ ЕСТЬ — правило зелено, и это половина
    # утверждения «краснеет ТОЛЬКО на нарушении».
    assert not (_include_selectors(substituted) - _document_ids(substituted)), (
        "подставленное дерево краснит правило ещё ДО долистывания — контроль "
        "доказывал бы не то: краснота взялась бы из подстановки, а не из "
        "ушедшей цели"
    )

    # ПОСЛЕ долистывания узел курсора ушёл, а объявления на строках первой
    # порции остались — правило ОБЯЗАНО покраснеть.
    glued = _last_portion_glued_in(substituted, portion)
    unreachable = _include_selectors(glued) - _document_ids(glued)
    assert unreachable == {"group-list-sentinel"}, (
        f"правило включаемых данных НЕ покраснело на дереве, где объявление "
        f"называет идентификатор, которого документ не несёт: недостижимых "
        f"целей {sorted(unreachable)}. Значит зубов у правила нет, и его "
        f"зелёный цвет на живом дереве не означает ничего"
    )


# =============================================================================
# Перечень исключений цели включаемых данных — три утверждения идиомы SP-1
# =============================================================================
#
# Образец формы — tests/test_pages/test_impersonation_gate.py (ALLOWED_ROUTES,
# MUTATING_ROUTE_COUNT, test_every_allowed_route_carries_a_reason), записанный
# в 09-PATTERNS.md §Shared Patterns → SP-1. Форма берётся оттуда, а не
# изобретается заново: перечень без этих трёх утверждений — декорация, которая
# через фазу читается как список без основания.


def test_every_include_target_exception_carries_a_reason_and_a_phase():
    """У каждой записи написана ПРИЧИНА и названа ФАЗА, а не пустая строка.

    Перечень, у которого не написано, почему цель разрешено объявлять там, где
    её нет, через фазу превращается в «наверное, так надо», и снять из него
    запись становится страшнее, чем добавить.

    Назначенная фаза утверждается наравне с обоснованием, и это не
    формальность: запись без названной фазы есть БЕССРОЧНЫЙ долг, а не принятое
    решение. Ровно этим долговой маркер и отличается от объявленного
    отступления.
    """
    unexplained = {
        target
        for target, entry in INCLUDE_TARGET_EXCEPTIONS.items()
        if not entry.reason.strip() or not entry.position.strip()
    }
    assert not unexplained, (
        f"цель включаемых данных выведена из-под общего правила без "
        f"обоснования или без названного положения экрана: "
        f"{sorted(unexplained)} — читатель через фазу не отличит принятое "
        f"решение от забытой работы"
    )

    undated = {
        target
        for target, entry in INCLUDE_TARGET_EXCEPTIONS.items()
        if not entry.assigned_phase.strip()
    }
    assert not undated, (
        f"отступлению не назначена фаза: {sorted(undated)} — бессрочный долг "
        f"под видом объявленного отступления"
    )


def test_the_number_of_include_target_exceptions_is_the_declared_one():
    """Исключений ровно ``INCLUDE_TARGET_EXCEPTIONS_DECLARED`` (второе из трёх).

    Правило достижимости объявленной цели живёт на ДВУХ положениях экрана.
    Молчаливый рост этого числа означает, что объявленная цель разошлась с
    документом ещё где-то, а решения об этом никто не принимал; молчаливое
    падение — что отступление закрыто, и записать это обязана следующая строка
    летописи, а не следующая фаза, обнаружившая перечень пустым.
    """
    assert len(INCLUDE_TARGET_EXCEPTIONS) == INCLUDE_TARGET_EXCEPTIONS_DECLARED, (
        f"исключений цели включаемых данных в перечне "
        f"{len(INCLUDE_TARGET_EXCEPTIONS)}, объявлено "
        f"{INCLUDE_TARGET_EXCEPTIONS_DECLARED}: "
        f"{sorted(INCLUDE_TARGET_EXCEPTIONS)} — из-под общего правила выведена "
        f"цель, о которой решения никто не принимал"
    )


@pytest.mark.asyncio
async def test_every_include_target_exception_is_actually_unreachable(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """НЕСУЩЕЕ, третье утверждение SP-1: запись правда в исключаемом положении.

    Краснеет в трёх случаях, и каждый — свой вид устаревания перечня:

    * цель, названная записью, в объявлениях документа НЕ ВСТРЕЧАЕТСЯ вовсе —
      запись стала фантомной, и исключение прикрывает то, чего нет;
    * цель ДОСТИЖИМА на положении «долистали до конца» — значит отступление
      закрыто (например, Фазой 15), и запись обязана уйти вместе с числом, а не
      остаться выводить из-под правила подчиняющееся ему место;
    * цель недостижима УЖЕ НА ПЕРВИЧНОЙ отрисовке крупного аккаунта — а это
      положение запись не покрывает и покрывать не должна: там узел курсора в
      документе стоит, и недостижимость означала бы, что сломался
      идентификатор, а не что сработало принятое отступление.

    Без этого утверждения перечень был бы декорацией: устаревшая запись жила бы
    вечно и молча выводила бы из-под правила положение, которое правилу
    подчиняется.
    """
    account = await _seed_account(db_session)
    await _seed_many(
        db_session, account, [f"Хвост {i:02d}" for i in range(PAGE_SIZE + 5)]
    )

    page = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    portion = (await authed_client.get(_sentinels(page)[0])).text
    glued, replaced = re.subn(
        r'<div id="group-list-sentinel".*?</div>',
        lambda _: portion,
        page,
        flags=re.S,
    )
    assert replaced == 1, (
        f"узел сентинела на странице подменён {replaced} раз вместо одного — "
        f"склейка не воспроизводит документ после долистывания, и утверждения "
        f"ниже говорили бы не о том документе"
    )

    declared_on_page = _include_selectors(page)
    unreachable_on_page = declared_on_page - _document_ids(page)
    unreachable_when_read_to_the_end = _include_selectors(glued) - _document_ids(
        glued
    )

    offenders: dict[str, str] = {}
    for target in INCLUDE_TARGET_EXCEPTIONS:
        if target not in declared_on_page:
            offenders[target] = (
                "цель не объявлена ни одним узлом первичной отрисовки — запись "
                "фантомная и прикрывает то, чего в документе нет"
            )
        elif target in unreachable_on_page:
            offenders[target] = (
                "цель недостижима УЖЕ на первичной отрисовке крупного "
                "аккаунта, где узел курсора обязан стоять — это не принятое "
                "отступление, а потерянный идентификатор"
            )
        elif target not in unreachable_when_read_to_the_end:
            offenders[target] = (
                "цель ДОСТИЖИМА и после долистывания до конца — отступление "
                "закрыто, и запись обязана уйти вместе с объявленным числом"
            )

    assert not offenders, (
        "перечень исключений цели включаемых данных устарел:\n  "
        + "\n  ".join(
            f"{target}: {why}" for target, why in sorted(offenders.items())
        )
    )


# =============================================================================
# План 09-13, Задача 1: ЧЕРЕДОВАНИЕ порции и удаления становится ИСПОЛНЯЕМЫМ
# =============================================================================
#
# ЧТО ЗДЕСЬ ЗАКРЕПЛЯЕТСЯ И ПОЧЕМУ ЭТОГО НЕ ЛОВИТ НИ ОДНО ПРЕЖНЕЕ ПРАВИЛО.
# Починка курсора (план 09-05) сняла молчаливую ПОТЕРЮ группы четвёртым
# внеполосным узлом. Узел работает — и вносит ЗЕРКАЛЬНЫЙ отказ (CR-01,
# 09-VERIFICATION.md, gap 1). Число отрисованных строк снимается из ЖИВОГО
# документа в момент ОТПРАВКИ запроса удаления (его забирает `hx-include` формы
# панели подтверждения), а применяется к тому узлу курсора, который существует
# в момент ПРИМЕНЕНИЯ ответа. Это РАЗНЫЕ МОМЕНТЫ, и тождество узла между ними
# не утверждается ни кодом, ни гейтом.
#
# ОКНО МЕЖДУ ЭТИМИ МОМЕНТАМИ ДОСТИЖИМО, И ЭТО ПРОЧИТАНО, А НЕ ВЫВЕДЕНО.
# `.modal` объявлен `position: fixed; inset: 0` БЕЗ блокировки прокрутки тела
# (app/static/css/app.css:941-943), поэтому список за открытой панелью
# подтверждения продолжает прокручиваться; `hx-trigger="revealed"` сентинела
# срабатывает В ПОЛЁТЕ, порция приезжает и двигает узел курсора ВПЕРЁД; ответ
# удаления затем тащит его НАЗАД — к числу, снятому в другой момент, — и порция
# уже видимых строк приезжает ВТОРИЧНО, с задвоенными `id="group-row-N"` и
# `id="group-del-N"`.
#
# ПОЧЕМУ ОБА ОХРАНЯЮЩИХ ПРАВИЛА ЭТО ПРОПУСКАЮТ.
# `test_the_scroll_cursor_survives_a_fragment_delete` и
# `test_a_no_op_delete_does_not_double_a_row` исполняют ТОЛЬКО
# ПОСЛЕДОВАТЕЛЬНЫЙ случай: запрос, ответ, потом чтение порции. Порядок, в
# котором отказ и живёт, не исполняет ни один — и это содержание gap 1, а не
# придирка к формулировке.
#
# ЗАДВОЕННЫЙ `id` — НЕ КОСМЕТИКА. На единственности идентификаторов документа
# стоит КАЖДЫЙ `hx-target` и КАЖДЫЙ `hx-swap-oob` экрана: рантайм целится в
# первый попавшийся из двух, и какой это будет, разметкой не задано. Признак
# отказа тот же МОЛЧАЛИВЫЙ, ради поимки которого пилот и брался: 200, чистая
# консоль, честный счётчик. Фазы 10-11 наследуют этот образец на десять
# потребителей.
#
# --- КРУГ КОНТРОЛЕЙ ФАЙЛА: ПРАВИЛО → ЕГО КОНТРОЛЬ ----------------------------
#
# Перечень выписан затем, чтобы «правило без контроля» было ВИДНО списком, а не
# обнаруживалось пересчётом. Правило, у которого контроля нет, доказывает ровно
# ничего: красным оно не бывало никогда, и отличить его зубы от его слепоты
# нечем.
#
#   test_an_interleaved_portion_and_delete_never_double_a_row (09-13)
#     → test_control_positive_the_reverse_order_keeps_the_document_whole
#   test_no_declared_include_selector_names_an_id_the_document_lacks (09-11,
#   предмет обнулён 09-13)
#     → test_control_negative_an_include_declaration_without_a_target_reddens_the_gate
#   test_every_claim_about_a_missing_oob_target_names_the_runtime_event (09-14)
#     → test_control_negative_a_claim_site_without_the_runtime_event_reddens_the_gate
#
# --- ЧИСЛО КОНТРОЛЕЙ ФАЙЛА: 3 ------------------------------------------------
#
# Один положительный и два отрицательных. Число записано ЗДЕСЬ затем,
# что контроль, добавленный молча, неотличим от контроля, добавленного ВМЕСТО
# правила: список выше говорит, у КАКОГО правила контроль есть, а число
# говорит, сколько их всего, — и разойтись эти две записи обязаны заметно.
#
# ЛЕТОПИСЬ ЧИСЛА: 0 → 1, Фаза 9, план 09-13, задача 1 — у файла заведён ПЕРВЫЙ
# контроль, и число выписано, чтобы следующие контроли не появлялись молча. До
# этой задачи блока в файле не было ВОВСЕ: `grep -c "def test_control"` давал
# `0`, и единственный такой блок в проекте стоял один —
# tests/test_templates/test_htmx_markup_gates.py:4521, откуда форма записи и
# взята целиком.
#
# ЛЕТОПИСЬ ЧИСЛА: 1 → 2, Фаза 9, план 09-13, задача 4 — ветвь владельца
# `keyset` обнулила предмет правила включаемых данных
# (`INCLUDE_DECLARATIONS_MEASURED` 30 → 0), и правило, зеленеющее на любом
# дереве, обязано было получить свои зубы:
# `test_control_negative_an_include_declaration_without_a_target_reddens_the_gate`.
# Это ВТОРАЯ половина замены; первая — переезд антивакуума на подставленное
# дерево (`SUBSTITUTED_INCLUDE_DECLARATIONS_MEASURED`). Ни одна из половин не
# факультативна, и обе проверяются гейтом плана.
#
# ЛЕТОПИСЬ ЧИСЛА: 2 → 3, Фаза 9, план 09-14, задача 1 — у нового правила
# `test_every_claim_about_a_missing_oob_target_names_the_runtime_event` заведены
# свои зубы:
# `test_control_negative_a_claim_site_without_the_runtime_event_reddens_the_gate`.
# Движение это было ОБЪЯВЛЕНО ЗАРАНЕЕ строкой ниже, оставленной планом 09-13, и
# оно её закрывает. Число поставлено ИЗМЕРЕНИЕМ, а не арифметикой:
# `grep -c "^def test_control\|^async def test_control"` по этому файлу.
#
# --- ЗАКРЫТАЯ ЗАПИСЬ ПЛАНА 09-13, СОХРАНЁННАЯ ДОСЛОВНО ------------------------
#
# ⚠️ ЧИСЛО ДВИНЕТСЯ ЕЩЁ ОДИН РАЗ В ЭТОМ ЖЕ КРУГЕ, И ДВИЖЕНИЕ ОБЯЗАНО ПОЛУЧИТЬ
# СВОЮ СТРОКУ ЛЕТОПИСИ, а не пройти молча: задача 1 плана 09-14
# (`test_control_negative_a_claim_site_without_the_runtime_event_reddens_the_gate`).
#
# --- КОНЕЦ ЗАКРЫТОЙ ЗАПИСИ ---------------------------------------------------
#
# ⚠️ МЕХАНИЗМ ПОДМЕНЫ: контроли этого файла подают ПОДСТАВЛЕННОЕ дерево
# существующими помощниками, а ЖИВОЕ дерево при доказательстве зубов не
# правится ни на символ. Положительный контроль ниже подставляет не дерево, а
# ПОРЯДОК ПРИМЕНЕНИЯ двух ответов: он утверждает, что правило ловит ТОЛЬКО
# нарушение. «Ловит нарушение» и «ловит только нарушение» суть разные
# высказывания, и второе из первого не следует.

# Число строк, которое возвращает порция бесконечной прокрутки на посеве этих
# двух тестов. Значение ИЗМЕРЕНО НА ЖИВОМ ДЕРЕВЕ (идиома SP-1, 09-PATTERNS.md),
# а не выведено ожиданием: адрес, который несёт страница
# (`/accounts/N/groups/partial?offset=30&limit=30`), вернул 30 строк, и
# следующий адрес пришёл со смещением 60.
#
# ПОЧЕМУ ЧИСЛО ВЫПИСАНО ОТДЕЛЬНО, А НЕ ПРИРАВНЕНО К `PAGE_SIZE`. Приравненное,
# оно молчало бы: размер страницы и размер порции совпадают сегодня ПО
# ПОСТРОЕНИЮ — оба берутся из одного значения, — но это свойство маршрута, а не
# закон. Сменившийся размер обязан ПОКРАСНЕТЬ здесь и быть перемеренным
# осознанно; приравненное число поехало бы вслед за предметом и перестало бы
# утверждать что-либо вовсе.
INTERLEAVED_PORTION_ROWS_MEASURED = 30

# Предел числа дочитываний в модели документа. Живой список конечен, и цепочка
# адресов обязана оборваться ответом без сентинела; предел стоит затем, чтобы
# курсор, зациклившийся на месте, дал ВНЯТНЫЙ отказ, а не висящий тест.
READ_TO_THE_END_LIMIT = 10

# Узел курсора целиком — от открывающего тега до парного закрытия. Нужен затем,
# что `_sentinels` даёт только АДРЕС, а `hx-include` снимает с узла ПОЛЯ, и
# именно поля уезжают на сервер в момент отправки.
CURSOR_NODE_RE = re.compile(r'<div[^<>]*id="group-list-sentinel".*?</div>', re.S)
CURSOR_FIELD_RE = re.compile(r'<input[^<>]*name="([^"]+)"[^<>]*value="([^"]*)"')


def _cursor_fields(html: str) -> dict[str, str]:
    """Поля, которые `hx-include` СНИМЕТ с узла курсора в момент ОТПРАВКИ.

    ⚠️ ЧИТАЕТСЯ ИМЕННО ДОКУМЕНТ, А НЕ ВЫПИСЫВАЕТСЯ ЧИСЛО РУКАМИ, И ЭТО НЕСУЩЕЕ
    СВОЙСТВО ЭТИХ ДВУХ ТЕСТОВ. Соседние правила файла шлют `len(rendered)`
    литералом — они утверждают арифметику ответа и вправе так делать. Здесь же
    предметом является САМО СНЯТИЕ величины с живого документа, поэтому тест
    обязан взять ровно то, что взял бы рантайм: сменится форма курсора —
    сменится и то, что уедет на сервер, а утверждения ниже говорят об
    идентификаторах и переживут смену.
    """
    node = CURSOR_NODE_RE.search(html)
    if not node:
        return {}
    return dict(CURSOR_FIELD_RE.findall(node.group(0)))


async def _read_to_the_end(client: AsyncClient, read_on_url: str) -> list[int]:
    """Строки, которые документ дочитает по цепочке адресов ДО КОНЦА списка.

    ⚠️ ЭТО НЕ ВТОРОЙ `_scroll_read_on_url`, И НАЗНАЧЕНИЕ У НИХ РАЗНОЕ. Тот
    отвечает на вопрос «КАКОЙ адрес документ понесёт после ответа удаления»;
    этот — на вопрос «что документ ПОКАЖЕТ, если человек долистает до конца».
    Одного дочитывания для второго вопроса не хватает: после чередования
    документ показывает две порции, и остаток списка приезжает третьей.
    Утверждение «ни одна строка не потеряна» без дочитывания до конца было бы
    высказыванием о произвольно выбранной середине.

    Возвращается СПИСОК, а не множество: повтор внутри самой цепочки — такой же
    отказ, как повтор между цепочкой и экраном, и множество его бы съело.
    """
    seen: list[int] = []
    visited: list[str] = []
    while read_on_url is not None:
        assert read_on_url not in visited, (
            f"цепочка дочитывания зациклилась на адресе {read_on_url}: "
            f"курсор не двигается вперёд, и список до конца не дочитывается "
            f"никогда — пройдено {visited}"
        )
        assert len(visited) < READ_TO_THE_END_LIMIT, (
            f"цепочка дочитывания не оборвалась за {READ_TO_THE_END_LIMIT} "
            f"шагов: пройдено {visited}"
        )
        visited.append(read_on_url)

        response = await client.get(read_on_url)
        assert response.status_code == 200, (
            f"дочитывание по адресу {read_on_url} получило "
            f"{response.status_code} вместо порции"
        )
        seen.extend(_row_ids(response.text))

        following = _sentinels(response.text)
        assert len(following) <= 1, (
            f"порция по адресу {read_on_url} принесла не один адрес "
            f"дочитывания, а {len(following)}: {following} — какой из них "
            f"останется в документе, разметкой не задано"
        )
        read_on_url = following[0] if following else None
    return seen


@pytest.mark.asyncio
async def test_an_interleaved_portion_and_delete_never_double_a_row(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """CR-01: чередование порции и удаления не задваивает и не теряет строк.

    ПОРЯДОК, В КОТОРОМ ОТКАЗ И ЖИВЁТ: порция применяется ПОСЛЕ снятия величины
    курсора и ДО применения ответа удаления.

    ⚠️ ВЕЛИЧИНА КУРСОРА СНИМАЕТСЯ ОДИН РАЗ И БОЛЬШЕ НЕ ПЕРЕЧИТЫВАЕТСЯ — В ЭТОМ
    ВСЯ СУТЬ ЧЕРЕДОВАНИЯ. Живой документ отдаёт `hx-include`-у то, что стоит в
    узле курсора В МОМЕНТ НАЖАТИЯ; приехавшая следом порция этот узел подменяет,
    но отправленный запрос уже несёт прежнее значение. Тест, перечитавший
    величину после порции, проверял бы не тот мир и зеленел бы на сломанном
    дереве.

    ⚠️ УТВЕРЖДЕНИЯ СФОРМУЛИРОВАНЫ ОБ ИДЕНТИФИКАТОРАХ, А НЕ О ЧИСЛЕ СМЕЩЕНИЯ, И
    ЭТО СДЕЛАНО НАМЕРЕННО. Форма курсора — предмет решения владельца (план
    09-13, задача 2); утверждение о числе пришлось бы переписывать вместе с
    формой, то есть починка доказывалась бы правкой теста, а не переходом
    цвета.

    Браузера у суиты нет, поэтому применение ответов моделируется явно: список
    идентификаторов, которые документ показывает, и ОДИН адрес дочитывания,
    который документ несёт сейчас.
    """
    account = await _seed_account(db_session)
    seeded = await _seed_many(
        db_session,
        account,
        [f"Группа {i:02d}" for i in range(PAGE_SIZE * 2 + 5)],
    )

    # --- АНТИВАКУУМ ПЕРВЫМИ ИСПОЛНЯЕМЫМИ УТВЕРЖДЕНИЯМИ ------------------------
    # Без них правило зеленело бы от пустого посева, то есть молчало бы громче
    # всего там, где сломалось сильнее всего.
    page = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    rendered = _row_ids(page)
    assert len(rendered) == PAGE_SIZE, (
        f"страница отрисовала {len(rendered)} строк вместо {PAGE_SIZE} — посев "
        "не создаёт условия, ради которого тест написан"
    )

    on_page = _sentinels(page)
    assert len(on_page) == 1, (
        f"страница несёт {len(on_page)} адресов дочитывания вместо одного: "
        f"{on_page} — чередовать нечего"
    )
    document_read_on_url = on_page[0]

    # Величина курсора снимается СО СТРАНИЦЫ и больше не перечитывается.
    captured_cursor_fields = _cursor_fields(page)

    # --- ПОРЦИЯ ПРИЕЗЖАЕТ В ПОЛЁТЕ -------------------------------------------
    portion_response = await authed_client.get(document_read_on_url)
    assert portion_response.status_code == 200, (
        f"порция по адресу {document_read_on_url} получила "
        f"{portion_response.status_code}"
    )
    portion = _row_ids(portion_response.text)
    assert INTERLEAVED_PORTION_ROWS_MEASURED > 0, (
        "измеренное число строк порции обнулилось: правило ниже стало бы "
        "вакуумным и зеленело бы на любом дереве"
    )
    assert len(portion) == INTERLEAVED_PORTION_ROWS_MEASURED, (
        f"порция вернула {len(portion)} строк вместо измеренных "
        f"{INTERLEAVED_PORTION_ROWS_MEASURED} — число перемеряется осознанно, "
        f"а не подгоняется под новое дерево"
    )

    # --- ОТВЕТ УДАЛЕНИЯ НА ВЕЛИЧИНЕ, СНЯТОЙ РАНЬШЕ ---------------------------
    # Цель — ПЕРВАЯ отрисованная строка: удаление НАД курсором есть тот случай,
    # ради которого починка курсора и заводилась.
    target = rendered[0]
    delete = await htmx_client.post(
        f"/accounts/{account.id}/groups/{target}/delete",
        data=captured_cursor_fields,
    )
    assert delete.status_code == 200, (
        f"запрос htmx получил {delete.status_code} вместо фрагмента"
    )
    assert f'id="group-row-{target}"' in delete.text, (
        "ответ удаления не несёт узла снятия строки — применять нечего, и "
        "утверждения ниже говорили бы не о том документе"
    )

    # Применение ответа удаления: узел, который никто не подменил, остаётся
    # стоять со своим прежним адресом. Тело порции подаётся туда, где помощник
    # ждёт тело страницы, — документ к этому моменту показывает именно порцию.
    document_read_on_url = _scroll_read_on_url(portion_response.text, delete.text)
    read_on = await _read_to_the_end(authed_client, document_read_on_url)

    on_screen = [group_id for group_id in rendered if group_id != target]
    document_before_reading = set(on_screen) | set(portion)
    shown = on_screen + portion + read_on
    alive = {group.id for group in seeded} - {target}

    # --- (а) ПОВТОРОВ НЕТ ----------------------------------------------------
    doubled = sorted({group_id for group_id in shown if shown.count(group_id) > 1})
    assert not doubled, (
        f"документ показывает одни и те же строки дважды: {doubled} — на "
        f"каждую из них в документе стоят два узла с одним `id` "
        f"(`group-row-N` и `group-del-N`), и каждый `hx-target` и каждый "
        f"`hx-swap-oob` экрана после этого целятся в ПЕРВЫЙ ПОПАВШИЙСЯ из "
        f"двух: какой это будет, разметкой не задано. Курсор уехал НАЗАД к "
        f"числу, снятому до приезда порции, и порция уже видимых строк "
        f"приехала вторично"
    )

    # --- (б) КУРСОР НЕ УЕХАЛ НАЗАД -------------------------------------------
    assert read_on, (
        f"адрес дочитывания {document_read_on_url} не вернул ни одной строки, "
        f"хотя список длиннее показанного — утверждение о курсоре осталось бы "
        f"без предмета"
    )
    assert read_on[0] not in document_before_reading, (
        f"курсор уехал НАЗАД: адрес дочитывания {document_read_on_url} вернул "
        f"первой строку {read_on[0]}, которая в документе УЖЕ СТОИТ. Величина, "
        f"снятая в момент отправки, применена к узлу другого момента"
    )

    # --- (в) НИ ОДНА СТРОКА НЕ ПОТЕРЯНА --------------------------------------
    lost = sorted(alive - set(shown))
    assert not lost, (
        f"после чередования список потерял группы: {lost} — их не отрисовала "
        f"ни страница, ни приехавшая порция, ни дочитывание до конца; человек "
        f"не увидит их до перезагрузки, а линейка счётчика продолжит их "
        f"считать"
    )
    assert set(shown) == alive, (
        f"объединение отрисованного, приехавшей порции и дочитанного не равно "
        f"оставшемуся списку: лишние {sorted(set(shown) - alive)}"
    )


@pytest.mark.asyncio
async def test_control_positive_the_reverse_order_keeps_the_document_whole(
    authed_client: AsyncClient, htmx_client: AsyncClient, db_session: AsyncSession
):
    """Положительный контроль: обратный порядок применения ответов безвреден.

    ⚠️ ЭТОТ ПОРЯДОК СЕГОДНЯ БЕЗВРЕДЕН, И КОНТРОЛЬ ЗЕЛЕН ДО ПРАВКИ. Он
    существует затем, чтобы правило выше нельзя было зазеленить починкой,
    ломающей второй порядок: «ловит нарушение» и «ловит ТОЛЬКО нарушение» суть
    разные высказывания, и второе из первого не следует.

    Ответ удаления применяется ПЕРВЫМ. Устаревший ответ порции целит в узел,
    который ответ удаления уже подменил, и в документ не входит ни одной
    строкой — ровно так рантайм и поступает с внеполосным свопом по
    отсоединённому узлу.
    """
    account = await _seed_account(db_session)
    seeded = await _seed_many(
        db_session,
        account,
        [f"Группа {i:02d}" for i in range(PAGE_SIZE * 2 + 5)],
    )

    page = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    rendered = _row_ids(page)
    assert len(rendered) == PAGE_SIZE, (
        f"страница отрисовала {len(rendered)} строк вместо {PAGE_SIZE} — посев "
        "не создаёт условия, ради которого контроль написан"
    )

    on_page = _sentinels(page)
    assert len(on_page) == 1, (
        f"страница несёт {len(on_page)} адресов дочитывания вместо одного: "
        f"{on_page}"
    )
    captured_cursor_fields = _cursor_fields(page)

    # Порция ВЫЧИСЛЯЕТСЯ до удаления, но в документ НЕ входит: её своп целит в
    # узел, который ответ удаления подменит раньше.
    stale_portion = _row_ids((await authed_client.get(on_page[0])).text)
    assert len(stale_portion) == INTERLEAVED_PORTION_ROWS_MEASURED, (
        f"устаревшая порция вернула {len(stale_portion)} строк вместо "
        f"измеренных {INTERLEAVED_PORTION_ROWS_MEASURED} — контроль потерял "
        f"предмет: отбрасывать стало нечего"
    )

    target = rendered[0]
    delete = await htmx_client.post(
        f"/accounts/{account.id}/groups/{target}/delete",
        data=captured_cursor_fields,
    )
    assert delete.status_code == 200, (
        f"запрос htmx получил {delete.status_code} вместо фрагмента"
    )

    # Ответ удаления применяется к документу ПЕРВЫМ — то есть к странице.
    document_read_on_url = _scroll_read_on_url(page, delete.text)
    read_on = await _read_to_the_end(authed_client, document_read_on_url)

    on_screen = [group_id for group_id in rendered if group_id != target]
    shown = on_screen + read_on
    alive = {group.id for group in seeded} - {target}

    doubled = sorted({group_id for group_id in shown if shown.count(group_id) > 1})
    assert not doubled, (
        f"обратный порядок задвоил строки: {doubled} — починка, зеленящая "
        f"чередование, сломала порядок, который был исправен"
    )

    lost = sorted(alive - set(shown))
    assert not lost, (
        f"обратный порядок потерял группы: {lost} — отброшенная устаревшая "
        f"порция унесла с собой строки, до которых документ больше не дойдёт"
    )
    assert set(shown) == alive, (
        f"объединение отрисованного и дочитанного не равно оставшемуся списку: "
        f"лишние {sorted(set(shown) - alive)}"
    )


# =============================================================================
# ПРАВИЛО 09-14: МЕСТО, РАССУЖДАЮЩЕЕ О НЕНАЙДЕННОЙ ЦЕЛИ ВНЕПОЛОСНОГО УЗЛА,
# ОБЯЗАНО НАЗЫВАТЬ СОБЫТИЕ РАНТАЙМА ПОИМЁННО.
# =============================================================================
#
# ⚠️ ИМЯ СОБЫТИЯ ПРИХОДИТ ИЗ ВЕНДОРЕННОГО РАНТАЙМА И ПРОВЕРЕНО ЧТЕНИЕМ
# `app/static/js/htmx.min.js` (`version:"2.0.10"`) ПРИ ИСПОЛНЕНИИ ПЛАНА 09-14, а
# не набрано по памяти. Цепочка прочитана целиком, и вот она дословно:
#
#   1. ветка внеполосной подмены, у которой цель НЕ РАЗРЕШИЛАСЬ:
#        else{o.parentNode.removeChild(o);
#             fe(te().body,"htmx:oobErrorNoTarget",{content:o,target:n})}
#      — узел СНИМАЕТСЯ из ответа, и поднимается событие;
#   2. function fe(e,t,n){ae(e,t,le({error:t},n))}
#      — подъём идёт с полем признака ошибки, равным ИМЕНИ события;
#   3. function ae(e,t,n){...if(n.error){H(n.error+(n.target?", "+n.target:""));
#        ae(e,"htmx:error",{errorInfo:n})}...}
#      — непустое поле признака ошибки заводит вызов `H`;
#   4. function H(e){console.error(e)}
#      — `H` и есть `console.error`.
#
# ⚠️ СОСЕДНЯЯ ВЕТКА РАНТАЙМА — ВЛОЖЕННЫЙ ВНЕПОЛОСНЫЙ УЗЕЛ ПРИ
# `allowNestedOobSwaps: false` — МОЛЧИТ ПО-НАСТОЯЩЕМУ, и это прочитано ТАМ ЖЕ:
#   else{e.removeAttribute("hx-swap-oob");e.removeAttribute("data-hx-swap-oob")}
# — признак снимается, события нет. Проза, рассуждающая о ВЛОЖЕННОМ узле,
# утверждает верное, предметом этого правила не является и им не правится.
# Различие названо здесь затем, чтобы следующий читатель не «исправил» верное
# заодно с неверным.
#
# Второе объявление имени события в тестах означало бы, что две проверки говорят
# о РАЗНЫХ событиях. Поэтому имя объявлено ровно один раз и берётся отсюда.
OOB_RUNTIME_EVENT = "htmx:oobErrorNoTarget"

REPO_ROOT = Path(__file__).resolve().parents[2]

# ⚠️ ПЕРЕЧЕНЬ МЕСТ ВЫПИСАН РУКАМИ, А НЕ ВЫВЕДЕН ПОИСКОМ ПО САМОЙ ПРОЗЕ (идиома
# SP-1, образец — соседний INCLUDE_TARGET_EXCEPTIONS). Правило, выводящее
# предмет проверки ИЗ ПРОВЕРЯЕМОЙ ПРОЗЫ, согласилось бы с любой её
# переформулировкой: достаточно переписать фразу другими словами, и место
# перестало бы попадать в выборку — то есть правило зеленело бы ровно от того
# действия, ради поимки которого заведено. Здесь у перечня написано, ПОЧЕМУ
# каждое место в нём, и добавление нового требует прочитать файл, а не подобрать
# образец.
#
# ⚠️ ЧИСЛО МЕСТ — ШЕСТЬ, А НЕ ЧЕТЫРЕ, И РАСХОЖДЕНИЕ НАЗЫВАЕТСЯ ЗДЕСЬ, А НЕ
# ПРЯЧЕТСЯ. Отчёт верификации (09-VERIFICATION.md, gap 2) и план 09-14 набирают
# «ЧЕТЫРЕ места» и перечисляют их тремя путями, один из которых указан по
# номерам строк ДО плана 09-13. Перечень ниже поставлен ИЗМЕРЕНИЕМ на отгруженном
# дереве (обход `app/` по прозе о ненайденной цели), и измерение вернуло ШЕСТЬ
# мест в ШЕСТИ файлах. Два из них — области уведомления шелла, то есть тот самый
# канал обратной связи, на который Фазы 10-15 переводят все 47 форм: оставить
# ложную гарантию именно там значило бы починить узкое место и сохранить широкое.
OOB_SILENCE_CLAIM_SITES: tuple[str, ...] = (
    # «по несуществующему идентификатору внеполосное снятие не находит узла и
    # не делает НИЧЕГО» — шапка ответа удаления, на которой стоит D-04-A.
    "app/templates/account_groups/partials/delete_response.html",
    # «унесённая один раз, она лишает цели ВСЕ последующие, и молча» — узел
    # линейки счётчика, общий для ответов тумблера и удаления.
    "app/templates/account_groups/partials/count_rule_oob.html",
    # «молчать об этом он будет так же, как молчит о ненайденной цели любого
    # другого свопа» — УСИЛЕННАЯ форма того же утверждения, абзац про постоянную
    # обёртку линейки.
    "app/templates/account_groups/list.html",
    # «молчать об этом браузер будет так же, как молчит о ненайденной цели
    # любого другого свопа» — область уведомления шелла.
    "app/templates/includes/notice_area.html",
    # «и молча, потому что о ненайденной цели свопа браузер не сообщает ничем» —
    # самая категоричная форма утверждения во всём дереве.
    "app/templates/includes/notice_oob.html",
    # докстринг `_fragment` обработчика удаления: «не находит узла и не делает
    # ничего — молча и безвредно».
    "app/pages/account_groups.py",
)

# ⚠️ ЧИСЛО ВЫПИСАНО ОТДЕЛЬНЫМ УТВЕРЖДЕНИЕМ НАМЕРЕННО (второе утверждение идиомы
# SP-1). Беззвучно упавшее означает, что место рассуждения снято, а решения об
# этом никто не принимал: правило, зеленеющее от опустевшего перечня, молчит
# громче всего там, где сломалось сильнее всего. Беззвучно выросшее означает, что
# место заведено без чтения рантайма.
#
# ЛЕТОПИСЬ: 0 → 6, Фаза 9, план 09-14, задача 1 — перечень заведён; число
# поставлено обходом дерева, а не переписано из отчёта верификации (тот называет
# четыре).
OOB_SILENCE_CLAIM_SITES_DECLARED = 6

OOB_ATTR_RE = re.compile(r'hx-swap-oob="([^"]*)"')
OOB_TARGET_SELECTOR_RE = re.compile(r"#([A-Za-z][-\w]*)")
LITERAL_ID_RE = re.compile(r'id="([A-Za-z][-\w]*)"')
NAMED_TEMPLATE_RE = re.compile(r'"([\w][\w/.-]*\.html)"')


def _claim_site_sources() -> dict[str, str]:
    """Исходники мест перечня, прочитанные с диска.

    Читаются именно ИСХОДНИКИ, а не отрендеренный документ: предмет правила —
    ПРОЗА (комментарии шаблонов и докстринги модуля), которой в ответе сервера
    нет вовсе.
    """
    return {
        site: (REPO_ROOT / site).read_text(encoding="utf-8")
        for site in OOB_SILENCE_CLAIM_SITES
    }


def _oob_targeted_ids() -> set[str]:
    """Идентификаторы, в которые целятся внеполосные подмены дерева шаблонов."""
    targeted: set[str] = set()
    for path in TEMPLATES_DIR.rglob("*.html"):
        for value in OOB_ATTR_RE.findall(path.read_text(encoding="utf-8")):
            targeted.update(OOB_TARGET_SELECTOR_RE.findall(value))
    return targeted


def _templates_printing_an_oob_node() -> set[str]:
    """Шаблоны, печатающие признак внеполосной подмены."""
    return {
        path.relative_to(TEMPLATES_DIR).as_posix()
        for path in TEMPLATES_DIR.rglob("*.html")
        if "hx-swap-oob" in path.read_text(encoding="utf-8")
    }


def _sites_not_naming_the_runtime_event(sources: dict[str, str]) -> set[str]:
    """Места, чья проза о ненайденной цели не называет события рантайма."""
    return {
        site for site, source in sources.items() if OOB_RUNTIME_EVENT not in source
    }


def _sites_that_are_not_places_of_oob_reasoning(sources: dict[str, str]) -> set[str]:
    """Места перечня, которые перестали быть местами внеполосной подмены.

    Место РЕАЛЬНО, если оно печатает признак внеполосной подмены, либо несёт
    идентификатор области, в которую такая подмена целится, либо называет по
    имени шаблон, который такой узел печатает. Запись о месте, переставшем быть
    местом, обязана краснеть, а не превращаться в мёртвую строку.
    """
    targeted = _oob_targeted_ids()
    printing = _templates_printing_an_oob_node()
    astray: set[str] = set()
    for site, source in sources.items():
        prints_the_attribute = "hx-swap-oob" in source
        carries_a_targeted_id = bool(set(LITERAL_ID_RE.findall(source)) & targeted)
        names_a_printing_template = bool(
            set(NAMED_TEMPLATE_RE.findall(source)) & printing
        )
        if not (
            prints_the_attribute or carries_a_targeted_id or names_a_printing_template
        ):
            astray.add(site)
    return astray


def _with_the_runtime_event_planted(
    sources: dict[str, str],
) -> tuple[dict[str, str], int]:
    """ПОДСТАВЛЕННОЕ дерево: событие названо в КАЖДОМ месте перечня.

    ⚠️ ПОДСТАВЛЯЕТСЯ ПРОЧИТАННАЯ СТРОКА, А НЕ ФАЙЛ НА ДИСКЕ: живое дерево при
    доказательстве зубов не правится ни на символ. Механизм тот же, которым
    подставляют соседние помощники файла (`_with_include_declarations`,
    `_last_portion_glued_in`) — подстановка в прочитанный текст; свой помощник
    заведён потому, что те подставляют ОТВЕТ, а предмет этого правила —
    ИСХОДНИКИ.

    Возвращается ещё и ЧИСЛО досаженных мест: подстановка, ничего не изменившая,
    «проходит» на нетронутом дереве и утверждает ровно ничего.
    """
    planted: dict[str, str] = {}
    added = 0
    for site, source in sources.items():
        if OOB_RUNTIME_EVENT in source:
            planted[site] = source
            continue
        planted[site] = f"{source}\nПОДСТАВЛЕНО КОНТРОЛЕМ: {OOB_RUNTIME_EVENT}\n"
        added += 1
    return planted, added


def test_every_claim_about_a_missing_oob_target_names_the_runtime_event():
    """Проза о ненайденной цели внеполосного узла называет событие ПОИМЁННО.

    ⚠️ ПРЕДМЕТ ПРАВИЛА — УТВЕРЖДЕНИЕ О ВЕНДОРЕННОМ РАНТАЙМЕ, А НЕ ФОРМУЛИРОВКА.
    Внеполосный узел, чью цель htmx 2.0.10 не разрешил, СНИМАЕТСЯ из ответа, и
    рантайм поднимает `htmx:oobErrorNoTarget` — а подъём события с полем признака
    ошибки заканчивается `console.error` (цепочка выписана дословно у константы
    OOB_RUNTIME_EVENT). Проза, утверждающая обратное, не «неточна»: она отдаёт
    следующему читателю ГАРАНТИЮ, которой рантайм не исполняет.

    ⚠️ ЦЕНА ЭТОГО ИМЕННО ЗДЕСЬ. Приёмочный признак обхода вехи — «ответ 200 И
    ЧИСТАЯ КОНСОЛЬ», и Фазы 10-15 наследуют его как свой. Холостой путь удаления
    (чужая, несуществующая, УЖЕ УДАЛЁННАЯ группа) шлёт два узла с отсутствующей
    целью, то есть две строки `console.error` на запрос, а достижим он ровно тем
    повторным запросом, ради безвредности которого неотличимость и заведена.

    ⚠️ ЧЕГО ЭТО ПРАВИЛО НЕ ВИДИТ — ВЫПИСАНО ЗДЕСЬ, А НЕ ОСТАВЛЕНО НА ДОГАДКУ
    (образец — шапка tests/test_pages/test_money_perimeter_gate.py). Правило
    видит РОВНО файлы перечня OOB_SILENCE_CLAIM_SITES и ничего кроме них. Новое
    рассуждение о ненайденной цели, заведённое в ЛЮБОМ другом файле, ему
    невидимо: перечень выписан руками намеренно (иначе правило соглашалось бы с
    переформулировкой), и цена этого выбора — ровно эта слепая зона. Закрытие
    границы — предмет ФАЗЫ 15 («Упрочнение и сводный обход 47 форм»), чей SC5
    называет поимённо известную слепую зону гейтов разметки и где инвентари
    закрываются сводно; ту же фазу несёт соседняя запись OOB_TARGET_EXCEPTIONS.
    До тех пор граница НАЗВАНА, а не закрыта молчанием.

    ⚠️ ЧЕГО ПРАВИЛО НЕ ТРЕБУЕТ. Оно не требует конкретной формулировки и не
    запрещает слова «безвредно»: вреда ДАННЫМ и ДОКУМЕНТУ у ненайденной цели
    действительно нет. Требуется одно — чтобы название события стояло там, где о
    событии рассуждают, и читатель мог проверить утверждение по рантайму сам.
    """
    # (1) АНТИВАКУУМ. Без него правило зеленело бы от опустевшего перечня.
    assert OOB_SILENCE_CLAIM_SITES_DECLARED > 0, (
        "перечень мест объявлен пустым — правило стало бы зелёным по построению "
        "и молчало бы громче всего там, где сломалось сильнее всего"
    )
    assert len(OOB_SILENCE_CLAIM_SITES) == OOB_SILENCE_CLAIM_SITES_DECLARED, (
        f"мест в перечне {len(OOB_SILENCE_CLAIM_SITES)}, а объявлено "
        f"{OOB_SILENCE_CLAIM_SITES_DECLARED}: место заведено или снято — обнови "
        f"число вместе с решением о нём и допиши строку летописи"
    )
    assert len(set(OOB_SILENCE_CLAIM_SITES)) == len(OOB_SILENCE_CLAIM_SITES), (
        "в перечне есть повтор: одно место, посчитанное дважды, завышает число "
        "и прикрывает снятое место"
    )
    absent = sorted(
        site for site in OOB_SILENCE_CLAIM_SITES if not (REPO_ROOT / site).is_file()
    )
    assert not absent, (
        f"место перечня не существует на диске: {absent} — правило читало бы "
        f"пустоту и зеленело бы на ней"
    )

    sources = _claim_site_sources()
    empty = sorted(site for site, source in sources.items() if not source.strip())
    assert not empty, f"место перечня пусто: {empty}"

    # (2) НЕСУЩЕЕ УТВЕРЖДЕНИЕ.
    silent = _sites_not_naming_the_runtime_event(sources)
    assert not silent, (
        "проза рассуждает о ненайденной цели внеполосного узла, НЕ НАЗЫВАЯ "
        f"события рантайма `{OOB_RUNTIME_EVENT}`:\n  "
        + "\n  ".join(sorted(silent))
        + "\n\nСЛЕДСТВИЕ, НАЗВАННОЕ ПРЯМЫМ ТЕКСТОМ: приёмочный признак вехи "
        "«ответ 200 И ЧИСТАЯ КОНСОЛЬ» обоснован в этих файлах утверждением, "
        "которого вендоренный рантайм НЕ ИСПОЛНЯЕТ — узел с неразрешимой целью "
        "снимается из ответа и поднимает событие, а подъём события с признаком "
        "ошибки печатает строку в консоль. Фазы 10-15 наследуют этот признак как "
        "свой приёмочный, и следующий автор внеполосного узла с иногда "
        "отсутствующей целью унаследует отсюда ложную гарантию тишины."
    )

    # (3) МЕСТО РЕАЛЬНО, А НЕ ОСТАЛОСЬ МЁРТВОЙ СТРОКОЙ ПЕРЕЧНЯ.
    astray = _sites_that_are_not_places_of_oob_reasoning(sources)
    assert not astray, (
        "место перечня перестало быть местом внеполосной подмены — оно не "
        "печатает признака, не несёт цели внеполосного узла и не называет "
        f"шаблона, который такой узел печатает:\n  {sorted(astray)}\n"
        "Запись о месте, которое перестало быть местом, обязана краснеть, а не "
        "превращаться в мёртвую строку."
    )


def test_control_negative_a_claim_site_without_the_runtime_event_reddens_the_gate():
    """ЗУБЫ ПРАВИЛА: место без названия события обязано КРАСНИТЬ.

    ⚠️ БЕЗ ЭТОГО КОНТРОЛЯ ПРАВИЛО ДОКАЗЫВАЕТ РОВНО НИЧЕГО: зелёное правило,
    красным не бывавшее ни разу, неотличимо от слепого. Контроль подаёт
    ПОДСТАВЛЕННОЕ дерево, в котором событие названо ВЕЗДЕ (иначе краснота
    взялась бы не из вырезанного названия, а из остатков живой прозы), и режет
    название из ОДНОГО места.

    ⚠️ ЖИВОЕ ДЕРЕВО ПРИ ДОКАЗАТЕЛЬСТВЕ НЕ ПРАВИТСЯ НИ НА СИМВОЛ, и это
    утверждается ЗДЕСЬ ЖЕ, последним утверждением, а не поручается прозе.

    ⚠️ КОНТРОЛЬ ЗЕЛЕН И ДО ПРАВКИ ПРОЗЫ, И ПОСЛЕ НЕЁ, И ЭТО НАМЕРЕННО. Он
    доказывает СВОЙСТВО ПРАВИЛА, а не состояние дерева: досадка названия делает
    его высказывание одинаковым по обе стороны перехода цвета задачи 2.
    """
    sources = _claim_site_sources()
    planted, added = _with_the_runtime_event_planted(sources)

    assert len(planted) == len(sources), (
        "подстановка потеряла место перечня — контроль доказывал бы не то"
    )
    assert added <= len(sources), "подстановка досадила больше мест, чем их есть"
    assert not _sites_not_naming_the_runtime_event(planted), (
        "правило краснеет на дереве, где событие названо ВЕЗДЕ: краснота ниже "
        "взялась бы не из вырезанного названия, и контроль утверждал бы не то"
    )

    victim = OOB_SILENCE_CLAIM_SITES[0]
    cut, removed = re.subn(re.escape(OOB_RUNTIME_EVENT), "", planted[victim])
    assert removed > 0, (
        f"из `{victim}` нечего было вырезать — подстановка ничего не изменила, "
        f"и контроль «проходит» на дереве, которого не трогал"
    )

    reddened = dict(planted)
    reddened[victim] = cut
    silent = _sites_not_naming_the_runtime_event(reddened)
    assert silent == {victim}, (
        f"правило НЕ покраснело на дереве, где название события вырезано из "
        f"`{victim}`: молчащих мест {sorted(silent)} вместо ровно одного. "
        f"Правило без зубов зелено по построению."
    )

    assert (REPO_ROOT / victim).read_text(encoding="utf-8") == sources[victim], (
        f"живое дерево изменилось при доказательстве зубов: `{victim}` на диске "
        f"больше не равен прочитанному — контроль правит то, что проверяет"
    )
