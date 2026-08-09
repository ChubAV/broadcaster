"""Wave 0: адаптивные примитивы на мигрированных страницах (План 01-03, UI-06).

Засеян разделом «Объявления» — эталоном миграции. Планы 04-08 дописывают сюда
свои разделы, добавляя значения в параметризацию.

Ключевой тест файла — test_ads_card_renders_data. Перевод include в макрос
теряет неявный контекст вызывающего шаблона, и ошибка проявляется ПУСТОЙ
карточкой, а не исключением: страница вернёт 200, а данных в ней не будет.
Утверждения на статус ответа такую поломку не ловят.
"""

import ast
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.balance_transaction import BalanceTransaction
from app.models.group import Group
from app.models.group_info import GroupInfo
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.subscription import Subscription
from app.models.user import User

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"

# Признаки utility-фреймворка: разметка разделов от них избавлена (D-06).
UTILITY_MARKERS = ("bg-white", "text-gray", "rounded-lg", "border-gray", "lg:")

SECTION_URLS = {
    "ads": "/ads",
    "schedules": "/schedules",
    "groups": "/groups",
    "history": "/history",
    "accounts": "/accounts",
}

# Разделы на примитиве строки-таблицы data-row. История сюда НЕ входит: у неё
# собственный примитив data-hrow, перестраивающийся раньше остальных (1080px).
MIGRATED_SECTIONS = ["ads", "schedules", "groups", "accounts"]

# Все разделы, переведённые на дизайн-систему, независимо от примитива.
# Планы 06-08 дописывают свои сюда.
CLEAN_SECTIONS = MIGRATED_SECTIONS + ["history"]


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_ad(db: AsyncSession, title: str = "Летняя распродажа") -> Ad:
    user = await _user(db)
    ad = Ad(user_id=user.id, title=title, text="Скидки до 50% на весь ассортимент", images=[])
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


async def _seed_account(db: AsyncSession, type_: str = "wa") -> MessengerAccount:
    user = await _user(db)
    account = MessengerAccount(
        user_id=user.id, type=type_, credentials="session", status="active"
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def _seed_schedule(
    db: AsyncSession, ad_title: str = "Объявление расписания"
) -> Schedule:
    ad = await _seed_ad(db, title=ad_title)
    account = await _seed_account(db)
    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[],
        days_of_week=[0, 2, 4],
        times_of_day=["09:30"],
        timezone="UTC",
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


async def _seed_group(db: AsyncSession, name: str = "Группа выходного дня") -> Group:
    user = await _user(db)
    account = await _seed_account(db)
    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="wa",
        group_external_id="ext-4242",
        name=name,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def _seed_send_log(
    db: AsyncSession,
    ad_title: str = "Отправка объявления",
    status: str = "ok",
    error_message: str | None = None,
    group_name: str = "Группа отправки",
) -> SendLog:
    user = await _user(db)
    log = SendLog(
        user_id=user.id,
        ad_title=ad_title,
        ad_text="Текст отправленного объявления",
        ad_images=[],
        group_name=group_name,
        messenger_type="wa",
        task_id="task-9f3c1d",
        status=status,
        error_message=error_message,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def _seed_transaction(
    db: AsyncSession,
    amount: int = 25,
    type_: str = "purchase",
    description: str = "Пакет «Старт»",
) -> BalanceTransaction:
    user = await _user(db)
    tx = BalanceTransaction(
        user_id=user.id,
        amount=amount,
        balance_after=100 + amount,
        type=type_,
        description=description,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


async def _seed_subscription(db: AsyncSession, plan: str = "business") -> Subscription:
    user = await _user(db)
    sub = Subscription(
        user_id=user.id,
        plan=plan,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def _seed_group_info(
    db: AsyncSession,
    name: str = "Справочная группа",
    messenger_type: str = "tg_user",
    external_id: str = "-100777",
) -> GroupInfo:
    item = GroupInfo(
        messenger_type=messenger_type,
        external_id=external_id,
        name=name,
        member_count=128,
        admin_contacts=[{"id": "1", "name": "Админ группы", "username": "chief"}],
        raw_metadata={},
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def _seed_section(db: AsyncSession, section: str) -> None:
    """Наполняет раздел так, чтобы списочная страница не была пустой.

    Пустая страница рисует empty_state и не содержит ни одной строки — тест на
    примитивы зазеленел бы вакуумно.
    """
    if section == "ads":
        await _seed_ad(db)
    elif section == "schedules":
        await _seed_schedule(db)
    elif section == "groups":
        await _seed_group(db)
    elif section == "history":
        await _seed_send_log(db)
    elif section == "accounts":
        # Тип MAX намеренно: у WA-аккаунта со статусом active экран подключения
        # WhatsApp редиректит, а тесты раздела ходят и туда (см. Плана 03
        # test_swap_anchors_present).
        await _seed_account(db, type_="max")
    else:  # pragma: no cover — защита от опечатки в параметризации
        raise AssertionError(f"неизвестный раздел: {section}")


@pytest.mark.asyncio
@pytest.mark.parametrize("section", MIGRATED_SECTIONS)
async def test_list_page_has_responsive_primitives(
    authed_client: AsyncClient, db_session: AsyncSession, section: str
):
    """Списочная страница собрана на примитивах, а не на своей вёрстке."""
    await _seed_section(db_session, section)

    html = (await authed_client.get(SECTION_URLS[section])).text
    assert "data-row" in html, section


@pytest.mark.asyncio
@pytest.mark.parametrize("section", CLEAN_SECTIONS)
async def test_list_page_no_utility_classes(
    authed_client: AsyncClient, db_session: AsyncSession, section: str
):
    await _seed_section(db_session, section)

    html = (await authed_client.get(SECTION_URLS[section])).text
    for marker in UTILITY_MARKERS:
        assert marker not in html, f"{section}: {marker}"


@pytest.mark.asyncio
async def test_ads_card_renders_data(authed_client: AsyncClient, db_session: AsyncSession):
    """Карточка-макрос отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    Макросы Jinja не получают контекст вызывающего шаблона: если `ad` не стал
    явным параметром, страница останется валидной, а карточка — пустой.
    """
    ad = await _seed_ad(db_session, title="Уникальный заголовок объявления")

    response = await authed_client.get("/ads")
    assert response.status_code == 200
    html = response.text
    assert "Уникальный заголовок объявления" in html
    assert "Скидки до 50%" in html
    assert f"/ads/{ad.id}/edit" in html


@pytest.mark.asyncio
async def test_schedules_card_renders_data(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Строка расписания отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    Перевод include в макрос теряет неявный контекст вызывающего шаблона:
    страница останется валидной и вернёт 200, а строки будут пустыми.
    """
    schedule = await _seed_schedule(db_session, ad_title="Расписание летней акции")

    response = await authed_client.get("/schedules")
    assert response.status_code == 200
    html = response.text
    assert "Расписание летней акции" in html
    assert "09:30" in html
    assert f"/schedules/{schedule.id}/edit" in html
    assert f"/schedules/{schedule.id}/toggle" in html


@pytest.mark.asyncio
async def test_schedules_toggle_route_unchanged(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-03: перевёрстка меняет вид тумблера, а не маршрут и не права.

    Свой маршрут переключает состояние; чужое расписание остаётся нетронутым.
    """
    own = await _seed_schedule(db_session, ad_title="Своё расписание")
    foreign_ad = Ad(user_id=(await _user(db_session)).id + 1000, title="Чужое",
                    text="Чужой текст", images=[])
    db_session.add(foreign_ad)
    await db_session.commit()
    await db_session.refresh(foreign_ad)
    foreign = Schedule(
        ad_id=foreign_ad.id, account_id=None, group_ids=[],
        days_of_week=[1], times_of_day=["10:00"], timezone="UTC",
    )
    db_session.add(foreign)
    await db_session.commit()
    await db_session.refresh(foreign)
    assert own.is_active is True and foreign.is_active is True

    response = await authed_client.post(
        f"/schedules/{own.id}/toggle", follow_redirects=False
    )
    assert response.status_code == 302
    await db_session.refresh(own)
    assert own.is_active is False

    response = await authed_client.post(
        f"/schedules/{foreign.id}/toggle", follow_redirects=False
    )
    assert response.status_code == 302
    await db_session.refresh(foreign)
    assert foreign.is_active is True


@pytest.mark.asyncio
async def test_groups_card_renders_data(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Строка группы отрисовывает РЕАЛЬНЫЕ данные, а не пустоту."""
    group = await _seed_group(db_session, name="Уникальное имя группы")

    response = await authed_client.get("/groups")
    assert response.status_code == 200
    html = response.text
    assert "Уникальное имя группы" in html
    assert "ext-4242" in html
    assert f"/groups/{group.id}/toggle" in html


@pytest.mark.asyncio
async def test_groups_filters_survive_pagination(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-01: фильтр обязан доехать до ВТОРОЙ страницы выдачи.

    Потерянный фильтр не роняет страницу — он молча подмешивает чужие строки к
    отфильтрованным, и список продолжает выглядеть исправным.
    """
    user = await _user(db_session)
    account = await _seed_account(db_session)
    db_session.add_all(
        [
            Group(
                user_id=user.id,
                account_id=account.id,
                messenger_type="wa",
                group_external_id=f"ext-{i}",
                name=f"Группа {i}",
            )
            for i in range(61)
        ]
    )
    await db_session.commit()

    response = await authed_client.get(
        "/groups/partial?offset=30&limit=30&messenger_type=wa&is_active=1"
    )
    assert response.status_code == 200

    urls = re.findall(r'hx-get="([^"]*/partial\?[^"]*)"', response.text)
    assert urls, "сентинел бесконечной прокрутки не найден"
    sentinel = urls[-1]
    assert "messenger_type=wa" in sentinel, sentinel
    assert "is_active=1" in sentinel, sentinel
    offset = re.search(r"offset=(\d+)", sentinel)
    assert offset and int(offset.group(1)) > 30, sentinel


@pytest.mark.asyncio
async def test_groups_filters_block_collapsible(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Блок фильтров собран из общего макроса и свёрнут разметкой, а не Alpine.

    Свёрнутое состояние приходит с сервера классами, поэтому на мобильной
    ширине блок не мигает до инициализации Alpine.
    """
    await _seed_group(db_session)

    html = (await authed_client.get("/groups")).text
    assert 'class="filters' in html
    assert "filters__toggle" in html
    assert 'action="/groups"' in html


@pytest.mark.asyncio
async def test_groups_toggle_route_unchanged(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-03: тумблер группы меняет вид, а не маршрут и не права."""
    own = await _seed_group(db_session, name="Своя группа")
    foreign = Group(
        user_id=own.user_id + 1000,
        account_id=own.account_id,
        messenger_type="wa",
        group_external_id="ext-foreign",
        name="Чужая группа",
    )
    db_session.add(foreign)
    await db_session.commit()
    await db_session.refresh(foreign)
    assert own.is_active is True and foreign.is_active is True

    response = await authed_client.post(
        f"/groups/{own.id}/toggle", follow_redirects=False
    )
    assert response.status_code == 302
    await db_session.refresh(own)
    assert own.is_active is False

    response = await authed_client.post(
        f"/groups/{foreign.id}/toggle", follow_redirects=False
    )
    assert response.status_code == 302
    await db_session.refresh(foreign)
    assert foreign.is_active is True


@pytest.mark.asyncio
async def test_ads_delete_uses_modal(authed_client: AsyncClient, db_session: AsyncSession):
    """Модалка заменяет браузерный диалог, но не маршрут и не метод (D-18).

    Право передумать сохраняется: у окна есть отмена, а форма внутри него —
    та же самая, что была.
    """
    ad = await _seed_ad(db_session)

    html = (await authed_client.get("/ads")).text

    assert 'role="dialog"' in html
    assert 'class="modal"' in html
    assert re.search(
        rf'<form[^>]*method="post"[^>]*action="/ads/{ad.id}/delete"'
        rf'|<form[^>]*action="/ads/{ad.id}/delete"[^>]*method="post"',
        html,
    ), "форма удаления потеряла прежний маршрут или метод"
    assert "Отмена" in html
    # Браузерный диалог подтверждения больше не используется
    assert "onsubmit" not in html
    assert "confirm(" not in html


@pytest.mark.asyncio
async def test_ads_delete_route_unchanged(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Модалка меняет способ подтверждения — не маршрут, не метод, не права.

    T-03-02: серверная проверка владельца обязана остаться на месте, иначе
    новая кнопка удаления открыла бы чужие объявления.
    """
    own = await _seed_ad(db_session, title="Своё объявление")
    foreign = Ad(user_id=own.user_id + 1000, title="Чужое", text="Чужой текст", images=[])
    db_session.add(foreign)
    await db_session.commit()
    await db_session.refresh(foreign)

    response = await authed_client.post(f"/ads/{own.id}/delete", follow_redirects=False)
    assert response.status_code == 302
    assert (await db_session.get(Ad, own.id)) is None

    response = await authed_client.post(f"/ads/{foreign.id}/delete", follow_redirects=False)
    assert response.status_code == 302
    assert (await db_session.get(Ad, foreign.id)) is not None


# --- План 05: раздел «История» на собственном примитиве data-hrow -----------

@pytest.mark.asyncio
async def test_history_uses_hrow_primitive(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Запись истории собрана на data-hrow, а не на строке-таблице data-row.

    История — единственный раздел с собственным адаптивным примитивом: он
    перестраивается раньше остальных, на 1080px, и его медиазапрос уже лежит в
    app.css со времён Плана 01.
    """
    await _seed_send_log(db_session)

    html = (await authed_client.get("/history")).text
    assert "data-hrow" in html


@pytest.mark.asyncio
async def test_history_meta_marked_by_attribute(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Блок метаданных размечен атрибутом, на который опирается медиазапрос.

    В макете это правило завязано на подстроку инлайн-стиля дочернего элемента
    и при переезде на классы молча перестаёт совпадать: на узкой ширине блок
    остался бы с левой границей и левым отступом вместо верхней границы.
    План 01 перевёл селектор на data-area — здесь появляется его опора.
    """
    await _seed_send_log(db_session)

    html = (await authed_client.get("/history")).text
    assert 'data-area="meta"' in html


@pytest.mark.asyncio
async def test_history_card_renders_data(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Запись истории отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    Перевод include в макрос теряет неявный контекст вызывающего шаблона:
    страница останется валидной и вернёт 200, а записи будут пустыми.
    """
    log = await _seed_send_log(
        db_session, ad_title="Уникальный заголовок отправки", group_name="Уникальная группа"
    )

    response = await authed_client.get("/history")
    assert response.status_code == 200
    html = response.text
    assert "Уникальный заголовок отправки" in html
    assert "Уникальная группа" in html
    assert "task-9f3c1d" in html
    assert f"/history/{log.id}" in html


@pytest.mark.asyncio
async def test_history_filters_survive_pagination(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Фильтр истории обязан доехать до ВТОРОЙ страницы выдачи.

    Потерянный фильтр не роняет страницу — он молча подмешивает чужие записи к
    отфильтрованным, и список продолжает выглядеть исправным.
    """
    user = await _user(db_session)
    db_session.add_all(
        [
            SendLog(
                user_id=user.id,
                ad_title=f"Отправка {i}",
                ad_text="Текст",
                ad_images=[],
                group_name=f"Группа {i}",
                messenger_type="wa",
                status="ok",
            )
            for i in range(61)
        ]
    )
    await db_session.commit()

    response = await authed_client.get(
        "/history/partial?offset=30&limit=30&status=ok&period=30d"
    )
    assert response.status_code == 200

    urls = re.findall(r'hx-get="([^"]*/partial\?[^"]*)"', response.text)
    assert urls, "сентинел бесконечной прокрутки не найден"
    sentinel = urls[-1]
    assert "status=ok" in sentinel, sentinel
    assert "period=30d" in sentinel, sentinel
    offset = re.search(r"offset=(\d+)", sentinel)
    assert offset and int(offset.group(1)) > 30, sentinel


@pytest.mark.asyncio
async def test_history_detail_shows_error_text(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Текст ошибки виден ЦЕЛИКОМ — это единственное объяснение неудачи.

    Сообщение приходит из внешнего мессенджера, приложением не контролируется и
    выводится только через экранирование Jinja2 (T-05-01). Сокращать его нельзя:
    по нему пользователь понимает, почему реклама не ушла.
    """
    long_error = (
        "PeerFloodError: Too many requests to join the group chat -420; "
        "retry after 86400 seconds (account temporarily restricted by Telegram)"
    )
    log = await _seed_send_log(
        db_session, status="fail", error_message=long_error, ad_title="Неудачная отправка"
    )

    response = await authed_client.get(f"/history/{log.id}")
    assert response.status_code == 200
    html = response.text
    assert long_error in html, "текст ошибки усечён или отсутствует"
    assert "truncate" not in html


@pytest.mark.asyncio
async def test_history_detail_renders_for_successful_send(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный тест: без него предыдущий зеленел бы на одной лишь ветке ошибки."""
    log = await _seed_send_log(db_session, ad_title="Успешная отправка")

    response = await authed_client.get(f"/history/{log.id}")
    assert response.status_code == 200
    html = response.text
    assert "Успешная отправка" in html
    for marker in UTILITY_MARKERS:
        assert marker not in html, marker


# --- План 05: дашборд и профиль --------------------------------------------

@pytest.mark.asyncio
async def test_dashboard_no_utility_classes(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _seed_send_log(db_session, ad_title="Отправка дашборда")

    response = await authed_client.get("/dashboard")
    assert response.status_code == 200
    html = response.text
    assert "Отправка дашборда" in html, "карточка недавней отправки отрисовалась пустой"
    for marker in UTILITY_MARKERS:
        assert marker not in html, marker


@pytest.mark.asyncio
async def test_profile_no_utility_classes(authed_client: AsyncClient):
    response = await authed_client.get("/profile")
    assert response.status_code == 200
    for marker in UTILITY_MARKERS:
        assert marker not in response.text, marker


# --- План 06: раздел «Аккаунты» --------------------------------------------

@pytest.mark.asyncio
async def test_accounts_card_renders_data(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Строка аккаунта отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    У аккаунта нет поля с именем: его «имя» на экране — это канал и номер,
    то есть подпись мессенджера и идентификатор. Если разметка потеряет данные
    аккаунта, страница всё равно вернёт 200 — поэтому утверждения идут по
    содержимому, а не по статусу.
    """
    account = await _seed_account(db_session, type_="max")

    response = await authed_client.get("/accounts")
    assert response.status_code == 200
    html = response.text
    assert "MAX" in html, "подпись канала не отрисована"
    assert f"#{account.id}" in html, "идентификатор аккаунта не отрисован"
    assert f"/accounts/{account.id}/delete" in html, "действие удаления потеряно"


@pytest.mark.asyncio
async def test_accounts_polling_only_on_syncing_row(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-06-01: запрос статуса висит ТОЛЬКО на синхронизирующейся строке.

    Соблазн при переверстке — вынести запрос на каждую строку «ради
    единообразия разметки». Тогда каждая открытая вкладка каждого пользователя
    начнёт дёргать сервер раз в 5 секунд по каждому аккаунту, включая давно
    подключённые. Страница при этом выглядит исправной, поэтому проверка
    поведенческая: у не синхронизирующегося аккаунта запроса статуса быть
    не должно.
    """
    active = await _seed_account(db_session, type_="max")

    html = (await authed_client.get("/accounts")).text
    assert f"/accounts/{active.id}/sync-status" not in html, (
        "у не синхронизирующегося аккаунта появился опрос статуса"
    )

    user = await _user(db_session)
    syncing = MessengerAccount(
        user_id=user.id, type="max", credentials="session", status="syncing"
    )
    db_session.add(syncing)
    await db_session.commit()
    await db_session.refresh(syncing)

    html = (await authed_client.get("/accounts")).text
    assert re.search(rf'id="account-row-{syncing.id}"[^>]*hx-get="', html), (
        "якорь синхронизирующейся строки потерял запрос обновления"
    )
    assert f"/accounts/{active.id}/sync-status" not in html


@pytest.mark.asyncio
async def test_accounts_connect_pages_no_utility_classes(
    authed_client: AsyncClient,
):
    """Мастера подключения — те же три экрана раздела, что и список.

    Экран Telegram доступен GET-ом всегда; экраны WhatsApp и MAX на первом шаге
    тоже (редирект включается лишь при уже подключённом аккаунте).
    """
    for url in (
        "/accounts/connect/tg_user",
        "/accounts/connect/max",
    ):
        response = await authed_client.get(url)
        assert response.status_code == 200, url
        for marker in UTILITY_MARKERS:
            assert marker not in response.text, f"{url}: {marker}"


@pytest.mark.asyncio
async def test_accounts_connect_max_form_contract(
    authed_client: AsyncClient,
):
    """T-06-03: форма мастера MAX сохраняет метод, маршрут и имя поля.

    Потеря атрибута name не роняет страницу — она молча делает подключение
    аккаунта невозможным, а экран продолжает отдавать 200.
    """
    html = (await authed_client.get("/accounts/connect/max")).text

    assert 'name="phone"' in html
    assert 'action="/accounts/connect/max/start"' in html
    assert re.search(r'<form[^>]*method="POST"[^>]*action="/accounts/connect/max/start"'
                     r'|<form[^>]*action="/accounts/connect/max/start"[^>]*method="POST"',
                     html), "форма подключения MAX потеряла маршрут или метод"


# --- План 11: подтверждение удаления аккаунта панелью дизайн-системы (SC-3) --
#
# Раздел «Аккаунты» рисуется ТРЕМЯ файлами (list.html, partial_cards.html,
# partials/sync_status_card.html), и в каждом по три ветки статуса — девять мест
# подтверждения удаления. Тесты ниже проверяют все три поверхности: списочную
# страницу, порцию бесконечной прокрутки и блок подмены по опросу статуса.


async def _seed_account_with_status(
    db: AsyncSession, status: str, type_: str = "max"
) -> MessengerAccount:
    """Аккаунт в произвольном статусе: _seed_account умеет только active."""
    user = await _user(db)
    account = MessengerAccount(
        user_id=user.id, type=type_, credentials="session", status=status
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


def _delete_forms(html: str, account_id: int) -> list[str]:
    """Все формы удаления аккаунта в разметке, ЦЕЛИКОМ (открывающий тег + тело)."""
    return re.findall(
        rf'<form[^>]*action="/accounts/{account_id}/delete"[^>]*>.*?</form>',
        html,
        re.S,
    )


@pytest.mark.asyncio
async def test_accounts_delete_uses_modal(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Подтверждение удаления аккаунта — панель дизайн-системы, не диалог ОС.

    До этого плана пользователь видел спроектированную модалку при удалении
    объявления и системный диалог браузера при удалении аккаунта — один и тот же
    жест разрушения выглядел по-разному в двух разделах (SC-3).
    """
    account = await _seed_account(db_session, type_="max")

    html = (await authed_client.get("/accounts")).text

    assert 'role="dialog"' in html, "панель подтверждения не отрисована"
    assert 'class="modal"' in html
    assert f"modal-open-acc-del-{account.id}" in html, (
        "форма удаления не открывает панель подтверждения"
    )
    assert "Отмена" in html, "у панели нет отказа от удаления"
    assert "confirm(" not in html, "системный диалог браузера остался"
    assert "onsubmit" not in html, "старый перехват отправки остался"


@pytest.mark.asyncio
async def test_accounts_delete_form_degrades_without_alpine(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-11-02: без Alpine форма отправляется напрямую — как до правки.

    Панель подтверждения — УСИЛЕНИЕ поверх формы, а не единственный путь.
    Кнопка type="button" вместо формы лишила бы раздел единственного способа
    отключить аккаунт, когда скрипт не доехал: снять признак сокрытия с панели
    умеет только Alpine (WR-04).
    """
    account = await _seed_account(db_session, type_="max")

    html = (await authed_client.get("/accounts")).text

    forms = _delete_forms(html, account.id)
    assert forms, "форма удаления исчезла из разметки"

    row_forms = [f for f in forms if "modal__form" not in f]
    assert row_forms, "форма удаления осталась только внутри панели подтверждения"
    for form in row_forms:
        assert 'method="POST"' in form, f"форма удаления потеряла метод: {form[:200]}"
        assert 'type="submit"' in form, (
            f"кнопка подтверждения перестала отправлять форму: {form[:200]}"
        )


@pytest.mark.asyncio
async def test_accounts_modal_unique_per_account(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-11-04: на странице РОВНО одна панель на аккаунт.

    Две панели с одним идентификатором открывались бы одним событием, и Tab
    уходил бы в невидимую копию.
    """
    first = await _seed_account(db_session, type_="max")
    second = await _seed_account(db_session, type_="wa")

    html = (await authed_client.get("/accounts")).text

    for account in (first, second):
        assert html.count(f'id="acc-del-{account.id}"') == 1, (
            f"панель подтверждения аккаунта {account.id} не единственная"
        )


@pytest.mark.asyncio
async def test_accounts_swap_card_dispatches_same_modal(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-11-04 с другой стороны: блок подмены панель НЕ приносит.

    Заменяется РОВНО строка (hx-swap="outerHTML" стоит на ней), панель лежит
    вне заменяемого элемента и подмену переживает. Если бы файл подмены тоже
    эмитил панель, после первого же опроса их стало бы две.
    """
    for status in ("syncing", "sync_failed", "active"):
        account = await _seed_account_with_status(db_session, status)

        response = await authed_client.get(f"/accounts/{account.id}/sync-status")
        assert response.status_code == 200, status
        html = response.text

        assert f"modal-open-acc-del-{account.id}" in html, (
            f"{status}: подменённая строка не открывает панель подтверждения"
        )
        assert 'role="dialog"' not in html, f"{status}: подмена принесла вторую панель"
        assert 'class="modal"' not in html, f"{status}: подмена принесла вторую панель"
        assert "confirm(" not in html, f"{status}: системный диалог браузера остался"
        assert "onsubmit" not in html, f"{status}: старый перехват отправки остался"


@pytest.mark.asyncio
async def test_accounts_delete_route_unchanged(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-11-01: заменяется диалог, а не действие.

    Маршрут, метод и серверная проверка владельца те же: новая кнопка удаления
    не имеет права открыть чужой аккаунт.
    """
    own = await _seed_account(db_session, type_="max")
    foreign = MessengerAccount(
        user_id=own.user_id + 1000, type="wa", credentials="session", status="active"
    )
    db_session.add(foreign)
    await db_session.commit()
    await db_session.refresh(foreign)

    response = await authed_client.post(
        f"/accounts/{own.id}/delete", follow_redirects=False
    )
    assert response.status_code == 302
    assert (await db_session.get(MessengerAccount, own.id)) is None

    response = await authed_client.post(
        f"/accounts/{foreign.id}/delete", follow_redirects=False
    )
    assert response.status_code == 302
    assert (await db_session.get(MessengerAccount, foreign.id)) is not None


# --- План 11: подписи колонок в ячейках раздела «Аккаунты» (SC-5) -----------
#
# На 860px шапка колонок скрывается ([data-rowhead] { display: none }), и строка
# «12 · 3 · 87% · 09.08 14:22 · —» превращается в набор символов без смысла.
# Подпись живёт ВНУТРИ ячейки и проявляется ровно там, где шапка исчезла.
# Атрибут подсказки её не заменяет: на касании подсказки нет.

# Подпись получает каждая колонка с непустым названием, КРОМЕ первой — она несёт
# название самого аккаунта и уже является заголовком карточки.
ACCOUNT_CELL_LABELS = (
    "Групп",
    "Расписаний",
    "Успешность",
    "Последняя отправка",
    "Подключён",
    "Статус",
)

CELL_LABEL_RE = re.compile(r"<span data-cell-label>([^<]*)</span>")
ROWHEAD_RE = re.compile(r"<div data-rowhead[^>]*>(.*?)</div>", re.S)


async def _seed_all_account_branches(db: AsyncSession) -> list[MessengerAccount]:
    """По одному аккаунту на каждую из трёх веток статуса раздела."""
    return [
        await _seed_account_with_status(db, status)
        for status in ("active", "sync_failed", "syncing")
    ]


@pytest.mark.asyncio
async def test_accounts_cell_labels_present(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Каждая ячейка списочной страницы несёт название своей колонки.

    Счёт по числу веток статуса, а не проверка «встречается хотя бы раз»:
    пропущенная ветка иначе прошла бы незамеченной — на широкой ширине подпись
    скрыта, и увидел бы её отсутствие только пользователь на телефоне.
    """
    accounts = await _seed_all_account_branches(db_session)

    html = (await authed_client.get("/accounts")).text

    for label in ACCOUNT_CELL_LABELS:
        assert html.count(f"<span data-cell-label>{label}</span>") == len(accounts), (
            f"подпись {label!r} проставлена не во всех ветках статуса"
        )


@pytest.mark.asyncio
async def test_accounts_partial_labels_present(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Порция бесконечной прокрутки несёт те же подписи, что и первая страница.

    Строки после первой прокрутки приходят ДРУГИМ файлом; расхождение видно
    только тому, кто долистал.
    """
    accounts = await _seed_all_account_branches(db_session)

    response = await authed_client.get("/accounts/partial?offset=0&limit=30")
    assert response.status_code == 200
    html = response.text

    for label in ACCOUNT_CELL_LABELS:
        assert html.count(f"<span data-cell-label>{label}</span>") == len(accounts), (
            f"подпись {label!r} потеряна в порции бесконечной прокрутки"
        )


@pytest.mark.asyncio
async def test_accounts_sync_card_labels_present(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Блок подмены по опросу статуса несёт подписи во ВСЕХ трёх состояниях.

    Самая опасная из трёх поверхностей: её разметки нет на первичной отрисовке,
    поэтому потеря подписи здесь проявится только после первого опроса.
    """
    for status in ("active", "sync_failed", "syncing"):
        account = await _seed_account_with_status(db_session, status)

        response = await authed_client.get(f"/accounts/{account.id}/sync-status")
        assert response.status_code == 200, status
        html = response.text

        for label in ACCOUNT_CELL_LABELS:
            assert f"<span data-cell-label>{label}</span>" in html, (
                f"{status}: подпись {label!r} потеряна в блоке подмены"
            )


@pytest.mark.asyncio
async def test_accounts_labels_come_from_column_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Подписи и шапка колонок — один список, а не два независимых.

    Переписанная вручную подпись разъедется с шапкой при первом же
    переименовании колонки, и увидит это только пользователь на телефоне.
    """
    await _seed_all_account_branches(db_session)

    html = (await authed_client.get("/accounts")).text

    head = ROWHEAD_RE.search(html)
    assert head, "шапка колонок раздела не найдена"
    header = {name for name in re.findall(r"<span>([^<]*)</span>", head.group(1)) if name}
    assert header, "шапка колонок пуста"

    labels = {value for value in CELL_LABEL_RE.findall(html) if value}

    assert header - labels == {"Аккаунт"}, (
        "подписи разошлись с шапкой колонок: без подписи остались "
        f"{sorted(header - labels - {'Аккаунт'})}"
    )
    assert labels - header == set(), (
        f"подписи, которых нет в шапке колонок: {sorted(labels - header)}"
    )


@pytest.mark.asyncio
async def test_profile_form_contract(authed_client: AsyncClient):
    """Форма профиля сохраняет метод, маршрут и все прежние имена полей.

    Потеря атрибута name не роняет страницу — она молча ломает сохранение
    настроек (T-05-04).
    """
    html = (await authed_client.get("/profile")).text

    assert 'method="post"' in html
    assert 'action="/profile"' in html
    assert 'name="timezone"' in html
    assert "Профиль" in html


# --- План 07: раздел «Тарифы» ----------------------------------------------
#
# Здесь исчезает ЕДИНСТВЕННАЯ таблица проекта. Табличные данные баланса
# переведены на те же примитивы data-rowhead / data-row / data-grow, что и все
# списки: адаптив на 860px приходит бесплатно, второй вёрстки и JS не нужно.
# Фазы 5 и 6 строят табличные представления тем же способом.

# Элементы таблицы, которых в проекте после Плана 07 быть не должно.
TABLE_MARKERS = ("<table", "<thead", "<tbody", "<tr", "<td", "<th ", "<th>")


@pytest.mark.asyncio
async def test_billing_uses_row_primitives(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """История операций собрана на строке-таблице, а не на своей вёрстке."""
    await _seed_transaction(db_session)

    response = await authed_client.get("/billing")
    assert response.status_code == 200
    html = response.text
    assert "data-row" in html
    assert "data-rowhead" in html


@pytest.mark.asyncio
async def test_billing_no_table_markup(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """В макете нет ни одного элемента таблицы — и в проекте не остаётся.

    Элемент таблицы не перестраивается медиазапросом строки-таблицы: он либо
    уезжает в горизонтальную прокрутку, либо сжимает колонки до нечитаемости.
    Проверка идёт по ОТРЕНДЕРЕННОЙ выдаче, а не по файлу: таблица могла бы
    приехать из включаемого шаблона.
    """
    await _seed_transaction(db_session)

    html = (await authed_client.get("/billing")).text
    for marker in TABLE_MARKERS:
        assert marker not in html, marker


@pytest.mark.asyncio
async def test_billing_no_utility_classes(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _seed_transaction(db_session)

    html = (await authed_client.get("/billing")).text
    for marker in UTILITY_MARKERS:
        assert marker not in html, marker


@pytest.mark.asyncio
async def test_billing_renders_transaction_data(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Строка операции отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    Перевод таблицы на макросы теряет неявный контекст: страница останется
    валидной и вернёт 200, а строки будут пустыми.
    """
    await _seed_transaction(
        db_session, amount=25, description="Уникальное описание операции"
    )

    html = (await authed_client.get("/billing")).text
    assert "Уникальное описание операции" in html
    assert "+25" in html, "знак и величина операции не отрисованы"
    assert "125" in html, "баланс после операции не отрисован"
    assert "Покупка" in html, "тип операции не расшифрован"


@pytest.mark.asyncio
async def test_billing_shows_current_plan(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Раздел тарифов показывает НАЗВАНИЕ ТЕКУЩЕГО тарифа пользователя.

    Тариф приходит из живого контекста шелла (get_shell_context), а не из
    константы в разметке: подписка с другим названием обязана изменить выдачу.
    """
    await _seed_subscription(db_session, plan="business")

    html = (await authed_client.get("/billing")).text
    assert "Business" in html, "название текущего тарифа не отрисовано"


@pytest.mark.asyncio
async def test_billing_plans_template_is_migrated():
    """`billing/plans.html` мигрирован, хотя маршрута у него нет.

    Шаблон не рендерится ни одним обработчиком (см. SUMMARY Плана 07):
    поведенческой проверки для него не существует, поэтому здесь — проверка
    исходника. Она ловит ровно то, ради чего шаблон правился: возврат
    utility-классов и отказ от компонентов.
    """
    source = (TEMPLATES_DIR / "billing" / "plans.html").read_text(encoding="utf-8")

    for marker in UTILITY_MARKERS:
        assert marker not in source, marker
    for marker in TABLE_MARKERS:
        assert marker not in source, marker
    assert "{% block page_title %}" in source
    assert "components/progress.html" in source
    assert "components/card.html" in source


# --- План 07: админ-панель ---------------------------------------------------
#
# Перевёрстка меняет ТОЛЬКО оформление. Проверка прав живёт в обработчиках
# (require_admin) и в шаблон не переезжает; состав показываемых персональных
# данных не расширяется. Оба утверждения — поведенческие: страница админки
# отдаёт 200 и выглядит исправной независимо от того, сломана проверка или нет.


@pytest.mark.asyncio
async def test_admin_pages_use_row_primitives(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Список пользователей собран на строке-таблице, а не на своей вёрстке."""
    response = await admin_client.get("/admin/users")
    assert response.status_code == 200
    html = response.text
    assert "data-row" in html
    assert "data-rowhead" in html


@pytest.mark.asyncio
async def test_admin_no_utility_classes(
    admin_client: AsyncClient, db_session: AsyncSession
):
    await _seed_group_info(db_session)

    for url in ("/admin", "/admin/users", "/admin/groups-info"):
        response = await admin_client.get(url)
        assert response.status_code == 200, url
        for marker in UTILITY_MARKERS:
            assert marker not in response.text, f"{url}: {marker}"


@pytest.mark.asyncio
async def test_admin_users_renders_data(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    """Строка пользователя отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    Порядок фикстур важен: authed_client регистрирует обычного пользователя,
    admin_client затем перелогинивает того же клиента администратором — в
    списке оказываются оба.
    """
    response = await admin_client.get("/admin/users")
    assert response.status_code == 200
    html = response.text

    user = await _user(db_session)
    assert user.email in html, "адрес пользователя не отрисован"
    assert user.name in html, "имя пользователя не отрисовано"
    assert f"/admin/users/{user.id}" in html, "ссылка на карточку пользователя потеряна"


@pytest.mark.asyncio
async def test_admin_users_shows_no_extra_personal_data(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    """T-07-02: перевёрстка — не повод показать больше персональных данных.

    Набор полей в списке зафиксирован: имя, адрес, дата регистрации, баланс и
    признак блокировки. Хеш пароля не был виден и не должен появиться —
    ни одно утверждение выше такого расширения не заметит.
    """
    html = (await admin_client.get("/admin/users")).text

    user = await _user(db_session)
    assert user.password_hash not in html, "в списке пользователей появился хеш пароля"
    assert "password_hash" not in html


@pytest.mark.asyncio
async def test_admin_denied_for_regular_user(authed_client: AsyncClient):
    """T-07-01: обычный пользователь не получает содержимого админ-панели.

    Проверка прав остаётся в обработчиках; перевёрстка её не ослабляет.
    Утверждение идёт и по статусу, и по телу: отказ, отданный со страницей
    админки внутри, отказом не является.
    """
    for url in ("/admin", "/admin/users", "/admin/groups-info"):
        response = await authed_client.get(url, follow_redirects=False)
        assert response.status_code != 200, url
        assert "Администрирование" not in response.text, url
        assert "data-rowhead" not in response.text, url


@pytest.mark.asyncio
async def test_admin_groups_info_uses_row_primitives(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Справочник групп собран на строке-таблице, а не на своей вёрстке."""
    await _seed_group_info(db_session)

    response = await admin_client.get("/admin/groups-info")
    assert response.status_code == 200
    html = response.text
    assert "data-row" in html
    assert "data-rowhead" in html


@pytest.mark.asyncio
async def test_admin_groups_info_renders_data(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Строка справочника отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    Видимая подпись раздела зафиксирована существующим покрытием
    (tests/test_pages/test_admin_groups_info.py) и переименованию не подлежит:
    переименования D-11 касаются пунктов основной навигации, а не заголовков
    внутри админки.
    """
    item = await _seed_group_info(db_session, name="Уникальное имя справочника")

    html = (await admin_client.get("/admin/groups-info")).text
    assert "Справочник групп" in html, "видимая подпись раздела потеряна"
    assert "Уникальное имя справочника" in html, "название группы не отрисовано"
    assert "-100777" in html, "внешний идентификатор не отрисован"
    assert f"/admin/groups-info/{item.id}" in html, "ссылка на карточку потеряна"


@pytest.mark.asyncio
async def test_admin_groups_info_escapes_external_name(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """T-07-03: название группы приходит из внешнего мессенджера.

    Это недоверенная строка: приложение её не контролирует и проверить не
    может. Она обязана выводиться штатным экранированием — макросам передаётся
    текст, а не разметка.
    """
    await _seed_group_info(db_session, name='<img src=x onerror="alert(1)">')

    html = (await admin_client.get("/admin/groups-info")).text
    assert '<img src=x' not in html, "название группы отрисовано как разметка"
    assert "&lt;img src=x" in html, "экранированного вывода названия нет"


# --- План 08, Задача 1: детальные страницы админки ---------------------------
#
# Обе страницы адресуются по path-параметру и в общий параметризованный обход
# смоук-теста не попадают: их покрытие — только эти точечные тесты.


@pytest.mark.asyncio
async def test_admin_user_detail_renders_data(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    """Карточка пользователя отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    Главный класс ошибок фазы: сборка страницы из макросов теряет неявный
    контекст, страница остаётся валидной и отдаёт 200, а значения пропадают.
    Утверждение на статус ответа такую поломку не ловит.
    """
    user = await _user(db_session)

    response = await admin_client.get(f"/admin/users/{user.id}")
    assert response.status_code == 200
    html = response.text

    assert user.email in html, "адрес пользователя не отрисован"
    assert user.name in html, "имя пользователя не отрисовано"
    # Ссылка на историю отправок — единственный переход со страницы
    assert f"/admin/users/{user.id}/history" in html, "ссылка на историю потеряна"
    # Действия сохраняются на прежних маршрутах: новых не добавляется, старые
    # не теряются (блокировка и вход под пользователем — Фаза 6, ADMIN-04/05).
    for action in ("/balance", "/unlimited", "/block", "/delete"):
        assert f"/admin/users/{user.id}{action}" in html, action


@pytest.mark.asyncio
async def test_admin_group_info_detail_renders_data(
    admin_client: AsyncClient, db_session: AsyncSession
):
    """Деталь справочника групп отрисовывает реальные данные."""
    item = await _seed_group_info(db_session, name="Уникальная деталь справочника")

    response = await admin_client.get(f"/admin/groups-info/{item.id}")
    assert response.status_code == 200
    html = response.text

    assert "Уникальная деталь справочника" in html, "название группы не отрисовано"
    assert "-100777" in html, "внешний идентификатор не отрисован"
    assert "Админ группы" in html, "контакт администратора не отрисован"


@pytest.mark.asyncio
async def test_admin_detail_pages_no_utility_classes(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    user = await _user(db_session)
    item = await _seed_group_info(db_session)

    for url in (f"/admin/users/{user.id}", f"/admin/groups-info/{item.id}"):
        response = await admin_client.get(url)
        assert response.status_code == 200, url
        for marker in UTILITY_MARKERS:
            assert marker not in response.text, f"{url}: {marker}"


@pytest.mark.asyncio
async def test_admin_detail_denied_for_regular_user(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-08-01: обычный пользователь не получает содержимого детальных страниц.

    Проверка прав живёт в обработчиках (require_admin) и в шаблон не
    переезжает. Утверждение идёт и по статусу, и по телу: отказ, отданный с
    отрендеренной страницей внутри, отказом не является.
    """
    user = await _user(db_session)
    item = await _seed_group_info(db_session)

    for url in (f"/admin/users/{user.id}", f"/admin/groups-info/{item.id}"):
        response = await authed_client.get(url, follow_redirects=False)
        assert response.status_code != 200, url
        assert user.email not in response.text, url
        assert "Справочная группа" not in response.text, url


@pytest.mark.asyncio
async def test_admin_user_detail_shows_no_extra_personal_data(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    """T-08-02: перевёрстка — не основание показать больше персональных данных.

    Набор полей карточки зафиксирован: имя, адрес, баланс, счётчики объявлений
    и групп, дата регистрации. Хеша пароля не было и не должно появиться —
    ни одно утверждение выше такого расширения не заметит.
    """
    user = await _user(db_session)

    html = (await admin_client.get(f"/admin/users/{user.id}")).text
    assert user.password_hash not in html, "в карточке появился хеш пароля"
    assert "password_hash" not in html


# --- План 08, Задача 2: история пользователя в админке -----------------------
#
# Последние два HTMX-взаимодействия описи из 27. Тип данных тот же, что и в
# пользовательской истории, поэтому и примитив обязан быть тот же: data-hrow.


async def _seed_admin_history(db_session: AsyncSession, count: int = 61) -> User:
    """Наполняет историю пользователя так, чтобы вторая страница существовала."""
    user = await _user(db_session)
    db_session.add_all(
        [
            SendLog(
                user_id=user.id,
                ad_title=f"Админ-отправка {i}",
                ad_text="Текст",
                ad_images=[],
                group_name=f"Админ-группа {i}",
                messenger_type="wa",
                status="ok",
            )
            for i in range(count)
        ]
    )
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_admin_user_history_uses_hrow_primitive(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    """Запись истории в админке собрана на том же примитиве, что и у пользователя.

    Это тот же тип данных, и выглядеть он обязан одинаково: примитив data-hrow
    и блок метаданных, размеченный атрибутом data-area="meta" — опора
    медиазапроса 1080px.
    """
    user = await _seed_admin_history(db_session, count=3)

    response = await admin_client.get(f"/admin/users/{user.id}/history")
    assert response.status_code == 200
    html = response.text
    assert "data-hrow" in html
    assert 'data-area="meta"' in html
    # Фильтры собраны общим макросом, а не локальным сценарием
    assert 'class="filters' in html, "блок фильтров не собран общим макросом"
    # Записи отрисовывают реальные данные, а не пустоту
    assert "Админ-отправка 0" in html
    assert "Админ-группа 0" in html


@pytest.mark.asyncio
async def test_admin_user_history_infinite_scroll(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    """Последняя живая цепочка прокрутки фазы обязана довести до второй страницы.

    Сентинел заменяет сам себя и обязан нести смещение СТРОГО больше
    запрошенного — иначе прокрутка зациклится на одной и той же выдаче, а
    страница продолжит выглядеть исправной.
    """
    user = await _seed_admin_history(db_session)

    response = await admin_client.get(
        f"/admin/users/{user.id}/history/partial?offset=30&limit=30&status=ok&period=30d"
    )
    assert response.status_code == 200

    urls = re.findall(r'hx-get="([^"]*/partial\?[^"]*)"', response.text)
    assert urls, "сентинел бесконечной прокрутки не найден"
    sentinel = urls[-1]
    assert "status=ok" in sentinel, sentinel
    assert "period=30d" in sentinel, sentinel
    # Параметр компоновки убран вместе с парной вёрсткой (D-15)
    assert "layout=cards" not in sentinel, sentinel
    offset = re.search(r"offset=(\d+)", sentinel)
    assert offset and int(offset.group(1)) > 30, sentinel
    # Записи партиала не пустые
    assert "Админ-отправка" in response.text


@pytest.mark.asyncio
async def test_admin_history_no_utility_classes(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    user = await _seed_admin_history(db_session, count=3)
    log = await _seed_send_log(
        db_session, status="fail", error_message="ECONNRESET", ad_title="Сбойная отправка"
    )

    urls = (
        f"/admin/users/{user.id}/history",
        f"/admin/users/{user.id}/history/partial?offset=0&limit=30",
        f"/admin/users/{user.id}/history/{log.id}",
    )
    for url in urls:
        response = await admin_client.get(url)
        assert response.status_code == 200, url
        for marker in UTILITY_MARKERS:
            assert marker not in response.text, f"{url}: {marker}"


@pytest.mark.asyncio
async def test_admin_history_detail_shows_error_text(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    """Текст ошибки выводится ЦЕЛИКОМ, как и в пользовательской детали (T-08-03).

    Строка приходит из внешнего мессенджера, приложением не контролируется и
    выводится только штатным экранированием. Усечения многоточием нет.
    """
    user = await _user(db_session)
    long_error = (
        "PeerFloodError: Too many requests to join the group chat -420; "
        "retry after 86400 seconds (account temporarily restricted by Telegram)"
    )
    log = await _seed_send_log(
        db_session, status="fail", error_message=long_error, ad_title="Неудачная админ-отправка"
    )

    response = await admin_client.get(f"/admin/users/{user.id}/history/{log.id}")
    assert response.status_code == 200
    html = response.text
    assert long_error in html, "текст ошибки усечён или отсутствует"
    assert "truncate" not in html


@pytest.mark.asyncio
async def test_admin_history_escapes_error_text(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    """T-08-03: текст ошибки — недоверенная строка из внешнего мессенджера."""
    user = await _user(db_session)
    log = await _seed_send_log(
        db_session, status="fail", error_message='<img src=x onerror="alert(1)">'
    )

    html = (await admin_client.get(f"/admin/users/{user.id}/history/{log.id}")).text
    assert "<img src=x" not in html, "текст ошибки отрисован как разметка"
    assert "&lt;img src=x" in html, "экранированного вывода ошибки нет"


@pytest.mark.asyncio
async def test_admin_history_denied_for_regular_user(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-08-01: история чужого пользователя недоступна обычному пользователю."""
    user = await _user(db_session)
    log = await _seed_send_log(db_session, ad_title="Закрытая отправка")

    for url in (
        f"/admin/users/{user.id}/history",
        f"/admin/users/{user.id}/history/partial?offset=0&limit=30",
        f"/admin/users/{user.id}/history/{log.id}",
    ):
        response = await authed_client.get(url, follow_redirects=False)
        assert response.status_code != 200, url
        assert "Закрытая отправка" not in response.text, url


# --- План 08, Задача 3: сплошная проверка фазы -------------------------------
#
# Это не миграция, а ГАРАНТИЯ, что пропущенных файлов нет. Тесты ниже —
# единственные, которые доказывают D-06 («ни один экран не остался на старой
# вёрстке») целиком, а не по одному разделу.

# Признаки удалённого utility-фреймворка. Список закрывает то, что реально
# встречалось в этой кодовой базе: палитра, кегли, начертания, раскладка,
# рамки и адаптивные префиксы.
TAILWIND_TOKENS = (
    # палитра фона и текста
    "bg-white", "bg-gray", "bg-slate", "bg-emerald", "bg-indigo", "bg-amber",
    "bg-red", "bg-blue", "bg-green", "bg-violet", "bg-purple", "bg-yellow",
    "text-gray", "text-slate", "text-emerald", "text-indigo", "text-amber",
    "text-red", "text-blue", "text-violet", "text-yellow", "text-white",
    # кегли и начертания
    "text-xs", "text-sm", "text-base", "text-lg", "text-xl", "text-2xl",
    "font-medium", "font-semibold", "font-bold",
    # раскладка
    "inline-flex", "inline-block", "items-center", "justify-center",
    "flex-col", "flex-1", "shrink-0", "space-y-", "space-x-", "divide-",
    # рамки, радиусы, тени
    "rounded-lg", "rounded-full", "border-gray", "border-slate", "shadow-sm",
    # утилиты текста
    "truncate", "whitespace-pre-line",
    # адаптивные префиксы
    "sm:", "md:", "lg:", "xl:",
)

# Семейства с числовым суффиксом: подстрокой их не выразить, поэтому они заданы
# выражениями. Список выше эти семейства не ловил, и ровно из-за этого сплошной
# обход Плана 08 прошёл мимо мёртвого набора иконок в каталоге includes
# (удалён Планом 09).
TAILWIND_PATTERNS = (
    # бесконечное вращение
    re.compile(r"\banimate-spin\b"),
    # прозрачность с числовым суффиксом: opacity-25, opacity-75
    re.compile(r"\bopacity-\d+\b"),
    # отрицательный отступ с префиксом направления: -ml-0.5, -mt-2
    re.compile(r"(?:^|\s)-[mp][trblxy]?-\d"),
    # дробный отступ: mr-1.5, px-2.5
    re.compile(r"\b[mp][trblxy]?-\d+\.\d+\b"),
    # размерные классы высоты и ширины: h-4 w-4, h-8 w-8
    re.compile(r"\b[hw]-\d+(?:\.\d+)?\b"),
)

# Проверка идёт ТОЛЬКО по значениям class="…". Иначе тест падает на
# упоминаниях классов в комментариях («.btn уже inline-flex»), то есть на
# документации, а не на разметке.
CLASS_ATTR_RE = re.compile(r'class="([^"]*)"')


def utility_markers_in(value: str) -> set[str]:
    """Признаки удалённого фреймворка в одном значении class="…"."""
    found = {token for token in TAILWIND_TOKENS if token in value}
    found |= {match.group(0).strip() for rx in TAILWIND_PATTERNS if (match := rx.search(value))}
    return found


# Семейства классов, которые список признаков Плана 08 НЕ ловил. Именно из-за
# них сплошной обход прошёл мимо мёртвого набора иконок в каталоге includes:
# ни один из 40 токенов не совпадал с классами анимации, прозрачности и
# размеров, которые в том файле стояли.
MISSED_FAMILIES = {
    "бесконечное вращение": "animate-spin h-8 w-8",
    "прозрачность с числовым суффиксом": "opacity-25",
    "отрицательный отступ с префиксом направления": "-ml-0.5",
    "дробный отступ": "mr-1.5",
    "размерные классы высоты и ширины": "h-3 w-3",
}

# Значения class="…" собственной дизайн-системы. Ни одно не имеет права быть
# опознано как признак удалённого фреймворка: молча расширенный токен, который
# ловит свои же классы, заставил бы ослабить тест целиком.
OWN_DESIGN_SYSTEM_CLASSES = (
    "cell cell--mono cell--muted",
    "btn btn--ghost",
    "btn btn--danger",
    "msg__glyph msg__glyph--tg {{ size }}",
    "msg msg--plain",
    "modal__panel",
    "modal__actions",
    "badge badge--success",
    "card__head",
    "empty__hint",
    "avatar",
    "mono",
)


def test_utility_markers_catch_the_families_that_were_missed():
    """Список признаков ловит те семейства, из-за которых промах случился.

    Тест синтетический намеренно: реальный нарушитель — мёртвый набор иконок в
    каталоге includes — удаляется в этой же задаче, и после удаления проверять
    расширение списка станет не на чем. Этот тест — единственное, что держит
    свойство дальше.
    """
    for family, sample in MISSED_FAMILIES.items():
        assert utility_markers_in(sample), f"семейство не опознано: {family} ({sample!r})"

    for value in OWN_DESIGN_SYSTEM_CLASSES:
        assert not utility_markers_in(value), f"свой класс опознан как чужой: {value!r}"


def test_no_utility_classes_anywhere():
    """Ни ОДИН шаблон проекта не содержит utility-классов (D-06, UI-06).

    Единственный тест, доказывающий требование целиком. Обходит все файлы
    app/templates/**/*.html: пропущенный шаблон виден только сплошным обходом,
    а не проверкой отдельных разделов — он отдаёт 200 и выглядит исправным.
    """
    offenders: dict[str, set[str]] = {}
    for path in sorted(TEMPLATES_DIR.rglob("*.html")):
        source = path.read_text(encoding="utf-8")
        found: set[str] = set()
        for value in CLASS_ATTR_RE.findall(source):
            found |= utility_markers_in(value)
        if found:
            offenders[str(path.relative_to(TEMPLATES_DIR))] = found

    assert not offenders, f"utility-классы остались в шаблонах: {offenders}"


def test_no_utility_classes_in_python_handlers():
    """Разметка ответов не собирается строками в обработчиках.

    HTML-фрагменты опроса статуса подключения жили в app/pages/accounts.py и
    несли utility-классы: Tailwind удалён Планом 01, поэтому они приходили в
    #wa-status / #max-status без оформления. Обход шаблонов их не видел —
    они не шаблоны.
    """
    pages_dir = TEMPLATES_DIR.parent / "pages"
    offenders: dict[str, set[str]] = {}
    for path in sorted(pages_dir.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        found: set[str] = set()
        for value in CLASS_ATTR_RE.findall(source):
            found |= utility_markers_in(value)
        if found:
            offenders[str(path.relative_to(pages_dir))] = found

    assert not offenders, f"utility-классы остались в обработчиках: {offenders}"


# --- План 11: страховочная сетка синхронности трёх файлов «Аккаунтов» -------
#
# Сетка на уровне ИСХОДНИКОВ, а не отрендеренной страницы. Причина: файл подмены
# рендерится обработчиком напрямую через окружение, своего адреса в обходе
# страниц у него нет, а расхождение проявляется только в момент подмены и только
# визуально. Именно так уже терялась колонка даты подключения (WR-03) — тестов на
# это не было ни одного.

ACCOUNTS_SECTION_FILES = (
    "accounts/list.html",
    "accounts/partial_cards.html",
    "accounts/partials/sync_status_card.html",
)

# Файлы, ЭМИТЯЩИЕ панель подтверждения, и единственный, который её не эмитит.
ACCOUNTS_PANEL_FILES = ("accounts/list.html", "accounts/partial_cards.html")
ACCOUNTS_SWAP_FILE = "accounts/partials/sync_status_card.html"

ACCOUNTS_MODAL_EVENT = "modal-open-acc-del-"

# Подпись берётся ИНДЕКСОМ из списка колонок. Отрицательный просмотр назад
# отсекает confirm_label=, action_label= и show_label= — это не подписи ячеек.
LABEL_BY_INDEX_RE = re.compile(r"(?<!\w)label=ACCOUNT_COLUMNS\[(\d+)\]")
LABEL_LITERAL_RE = re.compile(r"""(?<!\w)label=(['"])([^'"]*)\1""")


def _accounts_sources() -> dict[str, str]:
    """Исходники трёх файлов раздела. Порядок фиксирован: list.html — эталон."""
    return {
        rel: (TEMPLATES_DIR / rel).read_text(encoding="utf-8")
        for rel in ACCOUNTS_SECTION_FILES
    }


def _declaration(source: str, name: str) -> str | None:
    """Правая часть объявления {% set NAME = … %} дословно, как в файле."""
    match = re.search(rf"\{{%-?\s*set {name} = (.+?)\s*-?%\}}", source)
    return match.group(1) if match else None


def test_accounts_three_files_declare_same_columns():
    """Раскладка колонок и список колонок совпадают в трёх файлах ПОСИМВОЛЬНО.

    Три файла рисуют одну и ту же строку. Разъехавшаяся раскладка не роняет
    страницу: строка после подмены просто встанет по другим колонкам, и увидит
    это только тот, кто дождался опроса.
    """
    sources = _accounts_sources()

    for name in ("ACCOUNT_COLS", "ACCOUNT_COLUMNS"):
        declared = {rel: _declaration(src, name) for rel, src in sources.items()}

        missing = sorted(rel for rel, value in declared.items() if value is None)
        assert not missing, f"{name} не объявлен в: {missing}"

        reference_file, reference = next(iter(declared.items()))
        divergent = {rel: v for rel, v in declared.items() if v != reference}
        assert not divergent, (
            f"{name} в {reference_file} объявлен как {reference}, но отстали: "
            + "; ".join(f"{rel} -> {value}" for rel, value in sorted(divergent.items()))
        )


def test_accounts_three_files_have_no_browser_dialog():
    """Ни один из трёх файлов не вызывает системный диалог подтверждения (SC-3).

    Обход по HTTP этого не закрывает: разметки файла подмены нет на первичной
    отрисовке, и оставшийся там confirm() проявился бы только после опроса.
    """
    sources = _accounts_sources()

    offenders = {
        rel: src.count("confirm(") for rel, src in sources.items() if "confirm(" in src
    }
    assert not offenders, f"системный диалог браузера остался в: {offenders}"

    intercepts = {
        rel: src.count("onsubmit") for rel, src in sources.items() if "onsubmit" in src
    }
    assert not intercepts, f"старый перехват отправки остался в: {intercepts}"


def test_accounts_three_files_dispatch_same_modal_event():
    """Все три файла открывают ОДНУ панель, но эмитят её только два из них.

    Асимметрия сознательная и закреплена отдельным утверждением: панель лежит
    ВНЕ заменяемого элемента, поэтому файл подмены её не эмитит. Появись она там
    — после первого же опроса в документе оказалось бы две панели с одинаковым
    идентификатором, событие открывало бы обе, а Tab уходил бы в невидимую
    копию (T-11-04).
    """
    sources = _accounts_sources()

    counts = {rel: src.count(ACCOUNTS_MODAL_EVENT) for rel, src in sources.items()}
    silent = sorted(rel for rel, count in counts.items() if not count)
    assert not silent, f"файлы, не открывающие панель подтверждения: {silent}"

    reference_file, reference = next(iter(counts.items()))
    divergent = {rel: count for rel, count in counts.items() if count != reference}
    assert not divergent, (
        f"в {reference_file} мест подтверждения {reference}, но отстали: "
        + "; ".join(f"{rel} -> {count}" for rel, count in sorted(divergent.items()))
    )

    for rel in ACCOUNTS_PANEL_FILES:
        assert "components/modal.html" in sources[rel], (
            f"{rel}: панель подтверждения перестала эмититься — открывать станет нечего"
        )
    assert "components/modal.html" not in sources[ACCOUNTS_SWAP_FILE], (
        f"{ACCOUNTS_SWAP_FILE}: файл подмены начал эмитить панель — после первого "
        "опроса их станет две с одним идентификатором (T-11-04)"
    )


def test_accounts_three_files_label_the_same_columns():
    """Подписи ячеек в трёх файлах совпадают по составу И ПО ЧИСЛУ вхождений.

    Подпись, вписанная строкой на месте, разъедется с шапкой при первом же
    переименовании колонки, и увидит это только пользователь на телефоне: на
    широкой ширине подпись скрыта.

    Счёт вхождений, а не множество значений: в каждом файле три ветки статуса, и
    подпись, потерянная в ОДНОЙ из них, множество не меняет — две оставшиеся
    ветки его удержат. Именно так и теряется подпись на практике: правят одну
    ветку, а расходится весь раздел.
    """
    sources = _accounts_sources()

    hardcoded = {
        rel: sorted({m.group(2) for m in LABEL_LITERAL_RE.finditer(src)})
        for rel, src in sources.items()
    }
    hardcoded = {rel: values for rel, values in hardcoded.items() if values}
    assert not hardcoded, (
        "подписи вписаны строкой вместо элемента списка колонок — шапке и "
        f"подписям есть на чём разъехаться: {hardcoded}"
    )

    labels: dict[str, Counter[str]] = {}
    for rel, src in sources.items():
        declared = _declaration(src, "ACCOUNT_COLUMNS")
        assert declared, f"{rel}: список колонок не объявлен"
        columns = ast.literal_eval(declared)
        labels[rel] = Counter(
            columns[int(i)] for i in LABEL_BY_INDEX_RE.findall(src)
        )

    reference_file, reference = next(iter(labels.items()))
    assert reference, f"{reference_file}: подписей нет ни одной"

    divergent = {}
    for rel, counted in labels.items():
        if counted == reference:
            continue
        divergent[rel] = sorted(
            f"{name}: {counted.get(name, 0)} вместо {reference.get(name, 0)}"
            for name in set(counted) | set(reference)
            if counted.get(name, 0) != reference.get(name, 0)
        )
    assert not divergent, (
        f"подписи в {reference_file} — {sorted(reference.items())}, но отстали: "
        + "; ".join(
            f"{rel} -> {diff}" for rel, diff in sorted(divergent.items())
        )
    )


def test_template_inventory():
    """Инвентаризация шаблонов сходится.

    Парной вёрстки «строки/карточки» не осталось (D-15): файлов строчной
    компоновки нет ни одного. Элементов таблицы в проекте нет тоже — табличные
    данные строятся примитивами строки (решение Плана 07).
    """
    templates = sorted(TEMPLATES_DIR.rglob("*.html"))
    assert templates, "шаблоны не найдены — проверь путь"

    # Парная вёрстка удалена Планом 03: ни одного файла строчной компоновки
    rows_layout = [p.name for p in templates if p.name.endswith("_rows.html")]
    assert not rows_layout, f"файлы строчной компоновки остались: {rows_layout}"

    # Элементов таблицы в проекте не осталось ни одного
    table_markers = ("<table", "<td", "<th ", "<thead", "<tbody")
    with_tables = {
        str(p.relative_to(TEMPLATES_DIR))
        for p in templates
        if any(m in p.read_text(encoding="utf-8") for m in table_markers)
    }
    assert not with_tables, f"элементы таблицы остались: {with_tables}"

    # Библиотека компонентов Плана 02 на месте целиком (12 макросов + filters)
    components = sorted((TEMPLATES_DIR / "components").glob("*.html"))
    assert len(components) == 13, [p.name for p in components]

    # Два шелла проекта: основной и auth
    assert (TEMPLATES_DIR / "base.html").exists()
    assert (TEMPLATES_DIR / "auth_base.html").exists()


def test_every_page_template_extends_a_shell():
    """Каждый шаблон РАЗДЕЛА наследует шелл (D-06, UI-02).

    Обход по HTTP видит только страницы с GET-роутом. Этот тест закрывает
    оставшееся: шаблон, потерявший extends, отрисуется «голой» разметкой без
    единого стиля, а страницы без роута (четыре экрана авторизации из POST)
    обход по GET не достаёт вовсе.

    Не наследуют шелл по построению: сами шеллы, библиотека компонентов,
    партиалы подмены и включаемые фрагменты.
    """
    exempt_dirs = {"components", "includes", "partials"}
    exempt_names = {"base.html", "auth_base.html"}

    missing = []
    for path in sorted(TEMPLATES_DIR.rglob("*.html")):
        rel = path.relative_to(TEMPLATES_DIR)
        if rel.name in exempt_names or exempt_dirs & set(rel.parts):
            continue
        # Партиалы подмены и включаемые карточки шелл не наследуют
        if "partial" in rel.name or rel.name.startswith("_"):
            continue
        if "{% extends" not in path.read_text(encoding="utf-8"):
            missing.append(str(rel))

    assert not missing, f"шаблоны разделов без наследования шелла: {missing}"


# --- План 12, Задача 1: раздел «Группы» -------------------------------------
#
# Два последних места системного диалога раздела: удаление ОДНОЙ группы в строке
# и массовое удаление НАБОРА. Второе не сводится к «замене диалога»: между
# вопросом и отправкой лежит клиентский код, и от того, одним ли снимком берутся
# число в вопросе и отправляемые идентификаторы, зависит, соответствует ли
# подтверждение происходящему (T-12-01).

# Подпись получает каждая колонка GROUP_COLUMNS с непустым названием, КРОМЕ
# 'Группа' — она несёт название самой сущности и уже является заголовком строки.
GROUP_CELL_LABELS = (
    "Идентификатор",
    "Расписаний",
    "Успех",
    "Отправлено",
    "Статус",
)

SCRIPT_RE = re.compile(r"<script>(.*?)</script>", re.S)


def _template_source(rel: str) -> str:
    return (TEMPLATES_DIR / rel).read_text(encoding="utf-8")


def _delete_forms_for(html: str, action: str) -> list[str]:
    """Все формы с данным адресом удаления ЦЕЛИКОМ (открывающий тег + тело)."""
    return re.findall(rf'<form[^>]*action="{re.escape(action)}"[^>]*>.*?</form>', html, re.S)


def _labels_in(html: str) -> set[str]:
    return {value for value in CELL_LABEL_RE.findall(html) if value}


def _header_in(html: str) -> set[str]:
    head = ROWHEAD_RE.search(html)
    assert head, "шапка колонок раздела не найдена"
    return {name for name in re.findall(r"<span>([^<]*)</span>", head.group(1)) if name}


@pytest.mark.asyncio
async def test_groups_delete_uses_modal(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Удаление группы подтверждается панелью дизайн-системы, а не диалогом ОС.

    Тот же жест разрушения обязан выглядеть одинаково во всех разделах (SC-3):
    после Плана 11 «Аккаунты» показывают панель, а «Группы» показывали бы
    системный диалог.
    """
    group = await _seed_group(db_session)

    html = (await authed_client.get("/groups")).text

    assert 'role="dialog"' in html, "панель подтверждения не отрисована"
    assert 'class="modal"' in html
    assert f"modal-open-group-del-{group.id}" in html, (
        "форма удаления не открывает панель подтверждения"
    )
    assert html.count(f'id="group-del-{group.id}"') == 1, (
        "панель подтверждения группы не единственная"
    )
    assert "Отмена" in html, "у панели нет отказа от удаления"
    assert "confirm(" not in html, "системный диалог браузера остался"
    assert "onsubmit" not in html, "старый перехват отправки остался"


@pytest.mark.asyncio
async def test_groups_delete_form_degrades_without_alpine(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-12-04: без Alpine форма удаления группы отправляется напрямую.

    Панель — УСИЛЕНИЕ поверх настоящей формы. Кнопка type="button" вместо формы
    оставила бы раздел без единственного пути удалить группу, когда скрипт не
    доехал: снять признак сокрытия с панели умеет только Alpine (WR-04).
    """
    group = await _seed_group(db_session)

    html = (await authed_client.get("/groups")).text

    forms = _delete_forms_for(html, f"/groups/{group.id}/delete")
    assert forms, "форма удаления исчезла из разметки"

    row_forms = [f for f in forms if "modal__form" not in f]
    assert row_forms, "форма удаления осталась только внутри панели подтверждения"
    for form in row_forms:
        assert re.search(r'method="post"', form, re.I), (
            f"форма удаления потеряла метод: {form[:200]}"
        )
        assert 'type="submit"' in form, (
            f"кнопка удаления перестала отправлять форму: {form[:200]}"
        )


@pytest.mark.asyncio
async def test_groups_bulk_delete_uses_modal(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Массовое удаление подтверждается панелью с собственной формой набора.

    Подтверждается НЕ одна сущность по идентификатору в маршруте, а НАБОР,
    приходящий полями формы: поэтому скрытое поле действия, контейнер под
    идентификаторы и счётчик лежат ВНУТРИ формы панели (слот Плана 09).
    """
    await _seed_group(db_session)

    html = (await authed_client.get("/groups")).text

    assert html.count('id="groups-bulk-del"') == 1, "панель массового удаления не одна"

    form = re.search(
        r'<form class="modal__form"[^>]*action="/groups/bulk"[^>]*>(.*?)</form>',
        html,
        re.S,
    )
    assert form, "форма панели массового удаления потеряла адрес массового действия"
    body = form.group(1)

    assert re.search(r'name="action"[^>]*value="delete"', body), (
        "в форме панели нет скрытого поля действия со значением удаления"
    )
    assert 'id="groups-bulk-del-ids"' in body, (
        "в форме панели нет контейнера под идентификаторы выбранных групп"
    )
    assert 'id="groups-bulk-del-count"' in body, (
        "в форме панели нет элемента под число выбранных групп"
    )
    assert 'type="submit"' in body, "кнопка подтверждения не отправляет форму панели"

    assert "confirm(" not in html, "системный диалог массового удаления остался"


def test_groups_bulk_modal_confirms_exact_set():
    """T-12-01: вопрос и отправка относятся к ОДНОМУ снимку набора.

    Проверка идёт по исходнику, а не по выдаче: щель между вопросом и удалением
    — свойство ПОРЯДКА операций в клиентском коде, и в отрендеренной разметке её
    не видно. Если идентификаторы читаются заново в момент отправки, человек
    подтверждает число, которое может не совпасть с тем, что уйдёт на сервер, и
    узнаёт об этом по пропавшим группам.
    """
    script = SCRIPT_RE.search(_template_source("groups/list.html"))
    assert script, "клиентский код раздела не найден"
    source = script.group(1)

    assert source.count(".group-checkbox:checked") == 1, (
        "набор отметок читается больше одного раза — между вопросом и отправкой "
        "появилась щель, в которой набор может измениться"
    )

    read = source.index(".group-checkbox:checked")
    ids_written = source.index("groups-bulk-del-ids")
    count_written = source.index("groups-bulk-del-count")
    dispatch = source.index("modal-open-groups-bulk-del")

    assert read < ids_written < dispatch, (
        "идентификаторы попадают в форму панели не ДО открытия вопроса"
    )
    assert read < count_written < dispatch, (
        "число выбранных групп пишется в вопрос не ДО его открытия"
    )

    assert "createElement" in source and "textContent" in source, (
        "скрытые поля собираются не узлами, а разметкой строкой (T-12-07)"
    )
    assert "innerHTML" not in source, (
        "разметка скрытых полей собирается конкатенацией строк (T-12-07)"
    )


@pytest.mark.asyncio
async def test_groups_cell_labels_present(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Каждая ячейка строки группы несёт название своей колонки.

    На 860px шапка колонок скрывается, и строка «ext-4242 · 0 · — · —»
    превращается в набор символов без смысла.
    """
    groups = [
        await _seed_group(db_session, name=f"Группа {i}") for i in range(2)
    ]

    html = (await authed_client.get("/groups")).text

    for label in GROUP_CELL_LABELS:
        assert html.count(f"<span data-cell-label>{label}</span>") == len(groups), (
            f"подпись {label!r} проставлена не во всех строках"
        )

    header = _header_in(html)
    labels = _labels_in(html)
    assert header - labels == {"Группа"}, (
        "подписи разошлись с шапкой колонок: без подписи остались "
        f"{sorted(header - labels - {'Группа'})}"
    )
    assert labels - header == set(), (
        f"подписи, которых нет в шапке колонок: {sorted(labels - header)}"
    )


@pytest.mark.asyncio
async def test_groups_partial_labels_present(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Порция бесконечной прокрутки несёт те же подписи, что и первая страница.

    Правка живёт в МАКРОСЕ строки, поэтому закрывает обе поверхности разом;
    тест доказывает это, а не проверяет второй файл на всякий случай.
    """
    groups = [
        await _seed_group(db_session, name=f"Группа {i}") for i in range(2)
    ]

    response = await authed_client.get("/groups/partial?offset=0&limit=30")
    assert response.status_code == 200
    html = response.text

    for label in GROUP_CELL_LABELS:
        assert html.count(f"<span data-cell-label>{label}</span>") == len(groups), (
            f"подпись {label!r} потеряна в порции бесконечной прокрутки"
        )


# --- План 12, Задача 2: раздел «Расписания» ---------------------------------
#
# Схема Задачи 1 повторяется дословно: форма остаётся формой, перехват отправки
# навешивается на неё, панель ставится соседним элементом строки. Правка живёт в
# МАКРОСЕ, поэтому list.html и partial_cards.html не правятся вовсе.

# Подпись получает каждая колонка SCHEDULE_COLUMNS с непустым названием, КРОМЕ
# 'Объявление' — она несёт название сущности и уже является заголовком строки.
SCHEDULE_CELL_LABELS = (
    "Группы",
    "Дни",
    "Время",
    "Следующий запуск",
    "Статус",
)


@pytest.mark.asyncio
async def test_schedules_delete_uses_modal(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Удаление расписания подтверждается панелью дизайн-системы (SC-3)."""
    schedule = await _seed_schedule(db_session)

    html = (await authed_client.get("/schedules")).text

    assert 'role="dialog"' in html, "панель подтверждения не отрисована"
    assert 'class="modal"' in html
    assert f"modal-open-schedule-del-{schedule.id}" in html, (
        "форма удаления не открывает панель подтверждения"
    )
    assert html.count(f'id="schedule-del-{schedule.id}"') == 1, (
        "панель подтверждения расписания не единственная"
    )
    assert "Отмена" in html, "у панели нет отказа от удаления"
    assert "confirm(" not in html, "системный диалог браузера остался"
    assert "onsubmit" not in html, "старый перехват отправки остался"


@pytest.mark.asyncio
async def test_schedules_delete_form_degrades_without_alpine(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-12-04: без Alpine форма удаления расписания отправляется напрямую."""
    schedule = await _seed_schedule(db_session)

    html = (await authed_client.get("/schedules")).text

    forms = _delete_forms_for(html, f"/schedules/{schedule.id}/delete")
    assert forms, "форма удаления исчезла из разметки"

    row_forms = [f for f in forms if "modal__form" not in f]
    assert row_forms, "форма удаления осталась только внутри панели подтверждения"
    for form in row_forms:
        assert re.search(r'method="post"', form, re.I), (
            f"форма удаления потеряла метод: {form[:200]}"
        )
        assert 'type="submit"' in form, (
            f"кнопка удаления перестала отправлять форму: {form[:200]}"
        )


@pytest.mark.asyncio
async def test_schedules_cell_labels_present(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Каждая ячейка строки расписания несёт название своей колонки."""
    schedules = [
        await _seed_schedule(db_session, ad_title=f"Объявление {i}") for i in range(2)
    ]

    html = (await authed_client.get("/schedules")).text

    for label in SCHEDULE_CELL_LABELS:
        assert html.count(f"<span data-cell-label>{label}</span>") == len(schedules), (
            f"подпись {label!r} проставлена не во всех строках"
        )

    header = _header_in(html)
    labels = _labels_in(html)
    assert header - labels == {"Объявление"}, (
        "подписи разошлись с шапкой колонок: без подписи остались "
        f"{sorted(header - labels - {'Объявление'})}"
    )
    assert labels - header == set(), (
        f"подписи, которых нет в шапке колонок: {sorted(labels - header)}"
    )


@pytest.mark.asyncio
async def test_schedules_partial_labels_present(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Порция бесконечной прокрутки несёт те же подписи, что и первая страница."""
    schedules = [
        await _seed_schedule(db_session, ad_title=f"Объявление {i}") for i in range(2)
    ]

    response = await authed_client.get("/schedules/partial?offset=0&limit=30")
    assert response.status_code == 200
    html = response.text

    for label in SCHEDULE_CELL_LABELS:
        assert html.count(f"<span data-cell-label>{label}</span>") == len(schedules), (
            f"подпись {label!r} потеряна в порции бесконечной прокрутки"
        )


def test_schedules_row_keeps_grid_area_marker():
    """Признак области сетки не потерян: подпись добавлена К нему, а не вместо.

    Медиазапрос раздела опирается на признак области у ячейки следующего
    запуска. Потеря признака не роняет страницу — она молча ломает раскладку
    строки на узкой ширине, и увидит это только пользователь на телефоне.
    """
    source = _template_source("schedules/includes/schedule_row.html")

    assert source.count("area='meta'") == 1, (
        "ячейка следующего запуска потеряла признак области сетки"
    )


# --- План 12, Задача 3, часть 1: два прежних подтверждения к общему механизму -
#
# Планы 03 и 08 поставили панель подтверждения кнопкой type="button", а настоящую
# форму спрятали ВНУТРЬ панели. Без Alpine кнопка не делает ничего, а форма
# остаётся скрытой навсегда: на странице не остаётся ни одного пути удаления
# (WR-04). Одиннадцать мест, поставленных Планами 11-12, деградируют; эти два —
# нет. Один механизм подтверждения означает один механизм, а не два похожих.


@pytest.mark.asyncio
async def test_ads_delete_form_degrades_without_alpine(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-12-04: на странице объявлений есть настоящая форма удаления.

    Кнопка type="button" рядом с формой, лежащей внутри скрытой панели, — это
    не подтверждение, а единственная точка отказа: снять признак сокрытия с
    панели умеет только Alpine.
    """
    ad = await _seed_ad(db_session)

    html = (await authed_client.get("/ads")).text

    forms = _delete_forms_for(html, f"/ads/{ad.id}/delete")
    assert forms, "форма удаления объявления исчезла из разметки"

    row_forms = [f for f in forms if "modal__form" not in f]
    assert row_forms, (
        "форма удаления объявления существует только внутри панели подтверждения — "
        "без Alpine удалить объявление нечем (WR-04)"
    )
    for form in row_forms:
        assert re.search(r'method="post"', form, re.I), (
            f"форма удаления потеряла метод: {form[:200]}"
        )
        assert 'type="submit"' in form, (
            f"кнопка удаления перестала отправлять форму: {form[:200]}"
        )


@pytest.mark.asyncio
async def test_admin_user_delete_form_degrades_without_alpine(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    """T-12-04: на карточке пользователя есть настоящая форма удаления."""
    user = await _user(db_session)

    html = (await admin_client.get(f"/admin/users/{user.id}")).text

    forms = _delete_forms_for(html, f"/admin/users/{user.id}/delete")
    assert forms, "форма удаления пользователя исчезла из разметки"

    row_forms = [f for f in forms if "modal__form" not in f]
    assert row_forms, (
        "форма удаления пользователя существует только внутри панели подтверждения — "
        "без Alpine удалить пользователя нечем (WR-04)"
    )
    for form in row_forms:
        assert re.search(r'method="post"', form, re.I), (
            f"форма удаления потеряла метод: {form[:200]}"
        )
        assert 'type="submit"' in form, (
            f"кнопка удаления перестала отправлять форму: {form[:200]}"
        )


# --- План 12, Задача 3, часть 2: подписи колонок в оставшихся четырёх шаблонах -
#
# Уточнение к списку семи шаблонов из 01-VERIFICATION.md: он называет списочные
# страницы, но в разделах объявлений и на дашборде ячейки живут в МАКРОСЕ строки.
# Правка макроса закрывает и страницу, и её партиал прокрутки одновременно, а в
# админке ячейки лежат в самих страницах — там правятся страницы.

AD_CELL_LABELS = ("Текст", "Отправок", "Расписаний", "Создано", "Статус")
RECENT_CELL_LABELS = ("Время", "Группа", "Статус")
ADMIN_USER_CELL_LABELS = ("Регистрация", "Баланс", "Статус")


@pytest.mark.asyncio
async def test_ads_cell_labels_present(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Строка объявления несёт подписи и на странице, и в порции прокрутки."""
    ads = [await _seed_ad(db_session, title=f"Объявление {i}") for i in range(2)]

    html = (await authed_client.get("/ads")).text

    for label in AD_CELL_LABELS:
        assert html.count(f"<span data-cell-label>{label}</span>") == len(ads), (
            f"подпись {label!r} проставлена не во всех строках"
        )

    header = _header_in(html)
    labels = _labels_in(html)
    assert header - labels == {"Объявление"}, (
        "подписи разошлись с шапкой колонок: без подписи остались "
        f"{sorted(header - labels - {'Объявление'})}"
    )
    assert labels - header == set(), (
        f"подписи, которых нет в шапке колонок: {sorted(labels - header)}"
    )

    response = await authed_client.get("/ads/partial?offset=0&limit=30")
    assert response.status_code == 200
    for label in AD_CELL_LABELS:
        assert response.text.count(f"<span data-cell-label>{label}</span>") == len(ads), (
            f"подпись {label!r} потеряна в порции бесконечной прокрутки"
        )


@pytest.mark.asyncio
async def test_dashboard_cell_labels_present(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Строка недавней отправки на дашборде несёт названия своих колонок."""
    logs = [
        await _seed_send_log(db_session, ad_title=f"Отправка {i}") for i in range(2)
    ]

    html = (await authed_client.get("/dashboard")).text

    for label in RECENT_CELL_LABELS:
        assert html.count(f"<span data-cell-label>{label}</span>") == len(logs), (
            f"подпись {label!r} проставлена не во всех строках"
        )

    header = _header_in(html)
    labels = _labels_in(html)
    assert header - labels == {"Объявление"}, (
        "подписи разошлись с шапкой колонок: без подписи остались "
        f"{sorted(header - labels - {'Объявление'})}"
    )
    assert labels - header == set(), (
        f"подписи, которых нет в шапке колонок: {sorted(labels - header)}"
    )


@pytest.mark.asyncio
async def test_admin_users_cell_labels_present(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    """Строка пользователя в админке несёт названия своих колонок.

    Подпись колонки НЕ является новым полем: она дублирует название, уже
    показанное в шапке. Состав персональных данных не расширяется (T-12-06).
    """
    html = (await admin_client.get("/admin/users")).text

    for label in ADMIN_USER_CELL_LABELS:
        assert f"<span data-cell-label>{label}</span>" in html, (
            f"подпись {label!r} потеряна в строке пользователя"
        )

    header = _header_in(html)
    labels = _labels_in(html)
    assert header - labels == {"Пользователь"}, (
        "подписи разошлись с шапкой колонок: без подписи остались "
        f"{sorted(header - labels - {'Пользователь'})}"
    )
    assert labels - header == set(), (
        f"подписи, которых нет в шапке колонок: {sorted(labels - header)}"
    )


@pytest.mark.asyncio
async def test_admin_user_detail_cell_labels_present(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    """Список аккаунтов в карточке пользователя несёт название колонки статуса.

    Подпись здесь ровно одна, и это не недоработка: колонок в таблице две, а
    первая несёт название самой сущности.
    """
    user = await _user(db_session)
    await _seed_account(db_session, type_="max")

    html = (await admin_client.get(f"/admin/users/{user.id}")).text

    assert "<span data-cell-label>Статус</span>" in html, (
        "подпись статуса потеряна в списке аккаунтов карточки"
    )

    header = _header_in(html)
    labels = _labels_in(html)
    assert header - labels == {"Аккаунт"}, (
        "подписи разошлись с шапкой колонок: без подписи остались "
        f"{sorted(header - labels - {'Аккаунт'})}"
    )
    assert labels - header == set(), (
        f"подписи, которых нет в шапке колонок: {sorted(labels - header)}"
    )
