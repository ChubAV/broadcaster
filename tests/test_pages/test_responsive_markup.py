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
from typing import NamedTuple

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import CHART_BUCKETS_PER_DAY
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

# Адрес экрана групп аккаунта несёт ИДЕНТИФИКАТОР АККАУНТА, поэтому он записан
# образцом, а конкретный адрес возвращает ветка посева: аккаунт создаётся вместе
# с группой, и его идентификатор известен только там (план 03-08).
SECTION_URLS = {
    "ads": "/ads",
    "schedules": "/schedules",
    "account_groups": "/accounts/{account_id}/groups",
    "history": "/history",
    "accounts": "/accounts",
}

# Разделы на примитиве строки-таблицы data-row. История сюда НЕ входит: у неё
# собственный примитив data-hrow, перестраивающийся раньше остальных (1080px).
#
# Расписания вышли отсюда планом 02-07: сводный список стал КАРТОЧНЫМ на всех
# ширинах (UI-SPEC §Responsive Contract), и таблично-строчная обработка ячеек с
# подписями ему не нужна. Раздел не выпал из проверок — его собственный
# примитив закреплён test_schedules_summary_list_is_card_based ниже.
#
# Глобальный раздел «Группы» вышел отсюда планом 03-08 вместе со сносом самого
# раздела (D-01). Его замена — экран групп аккаунта — тоже КАРТОЧНАЯ на всех
# ширинах (03-05), поэтому в перечень строк-таблиц она не попадает; её
# собственный примитив закреплён test_account_groups_list_is_card_based по той
# же схеме, что у расписаний.
MIGRATED_SECTIONS = ["ads", "accounts"]

# Все разделы, переведённые на дизайн-систему, независимо от примитива.
# Планы 06-08 дописывают свои сюда.
CLEAN_SECTIONS = MIGRATED_SECTIONS + ["history", "schedules", "account_groups"]


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


async def _seed_group(
    db: AsyncSession,
    name: str = "Группа выходного дня",
    account: MessengerAccount | None = None,
) -> Group:
    """Группа на переданном аккаунте; без аккаунта — на своём новом.

    Параметр аккаунта добавлен планом 03-08: экран групп аккаунта адресуется
    идентификатором аккаунта, и посев обязан вернуть группу ИМЕННО на том
    аккаунте, чей адрес откроет тест. Своя ветка посева на каждый вызов
    оставила бы страницу пустой — рядом с аккаунтом из адреса групп бы не было.
    """
    user = await _user(db)
    account = account or await _seed_account(db)
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


async def _seed_account_groups_screen(db: AsyncSession) -> str:
    """Аккаунт с одной группой; возвращает адрес его экрана групп."""
    account = await _seed_account(db)
    await _seed_group(db, account=account)
    return SECTION_URLS["account_groups"].format(account_id=account.id)


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


async def _seed_section(db: AsyncSession, section: str) -> str:
    """Наполняет раздел и возвращает АДРЕС его списочной страницы.

    Пустая страница рисует empty_state и не содержит ни одной строки — тест на
    примитивы зазеленел бы вакуумно.

    Адрес возвращается, а не читается вызывающим из SECTION_URLS: у экрана
    групп аккаунта он содержит идентификатор аккаунта, созданного здесь же
    (план 03-08). Для остальных разделов это тот же адрес, что и в таблице.
    """
    if section == "ads":
        await _seed_ad(db)
    elif section == "schedules":
        await _seed_schedule(db)
    elif section == "account_groups":
        return await _seed_account_groups_screen(db)
    elif section == "history":
        await _seed_send_log(db)
    elif section == "accounts":
        # Тип MAX намеренно: у WA-аккаунта со статусом active экран подключения
        # WhatsApp редиректит, а тесты раздела ходят и туда (см. Плана 03
        # test_swap_anchors_present).
        await _seed_account(db, type_="max")
    else:  # pragma: no cover — защита от опечатки в параметризации
        raise AssertionError(f"неизвестный раздел: {section}")
    return SECTION_URLS[section]


@pytest.mark.asyncio
@pytest.mark.parametrize("section", MIGRATED_SECTIONS)
async def test_list_page_has_responsive_primitives(
    authed_client: AsyncClient, db_session: AsyncSession, section: str
):
    """Списочная страница собрана на примитивах, а не на своей вёрстке."""
    url = await _seed_section(db_session, section)

    html = (await authed_client.get(url)).text
    assert "data-row" in html, section


@pytest.mark.asyncio
@pytest.mark.parametrize("section", CLEAN_SECTIONS)
async def test_list_page_no_utility_classes(
    authed_client: AsyncClient, db_session: AsyncSession, section: str
):
    url = await _seed_section(db_session, section)

    html = (await authed_client.get(url)).text
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
    # Действие строки ведёт В РЕДАКТОР ОБЪЯВЛЕНИЯ к ЭТОМУ расписанию: параметр
    # выбранного расписания разворачивает нужную карточку (план 02-05).
    # До плана 02-06 здесь стоял адрес отдельной страницы редактирования
    # расписания; страница снята (D-14), поведение — переход к настройке именно
    # этого расписания — осталось прежним и проверяется на новом адресе.
    assert f"/ads/{schedule.ad_id}/edit?sched={schedule.id}" in html
    assert f"/schedules/{schedule.id}/toggle" in html


@pytest.mark.asyncio
async def test_schedules_summary_list_is_card_based(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Замена вклада раздела в обход по data-row (План 02-07).

    Сводный список карточный на ВСЕХ ширинах, поэтому примитив строки-таблицы
    ему не подходит. Утверждение положительное: у списка есть СВОЙ примитив, а
    не «нет старого». Без него раздел просто выпал бы из проверок вместе со
    строкой параметризации.
    """
    await _seed_schedule(db_session, ad_title="Карточное расписание")

    html = (await authed_client.get("/schedules")).text

    assert "data-sched-list" in html, "контейнер карточек сводного списка исчез"
    assert 'class="sched-item"' in html, "карточка расписания исчезла из разметки"
    assert "data-row" not in html, (
        "сводный список вернулся к строке-таблице — на 860px её колонки "
        "скрываются, а подписей ячеек у карточек нет"
    )


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


# --- План 03-08: вклад экрана групп аккаунта вместо снесённого раздела -------
#
# Глобальный раздел «Группы» снесён (D-01). Его вклад в этот файл не удалён, а
# ПЕРЕЕХАЛ на экран групп аккаунта — с одной названной потерей: фильтры по
# мессенджеру и по активности на новом экране не существуют вовсе (D-03),
# поэтому «фильтр доезжает до второй страницы» проверяется на строке ПОИСКА —
# единственном фильтре экрана — и живёт в tests/test_pages/test_htmx_preserved.py
# вместе с остальными проверками цепочки прокрутки.
#
# Отрисовка реальных данных строкой, владение при переключении и удаление с
# чисткой расписаний переехали не сюда, а в tests/test_pages/test_account_groups.py
# (планы 03-01 и 03-05): там они проверяются подробнее, чем проверялись здесь.


@pytest.mark.asyncio
async def test_account_groups_list_is_card_based(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Замена вклада снесённого раздела в обход по data-row (план 03-08).

    Экран групп аккаунта — список КАРТОЧЕК на всех ширинах, поэтому примитив
    строки-таблицы ему не подходит: на 860px её колонки скрываются, а подписей
    ячеек у карточки нет. Утверждение положительное — у списка есть СВОЙ
    примитив, а не «нет старого»: без него раздел просто выпал бы из проверок
    вместе со строкой параметризации.
    """
    url = await _seed_account_groups_screen(db_session)

    html = (await authed_client.get(url)).text

    assert "data-group-list" in html, "контейнер карточек экрана исчез"
    assert "data-group-row" in html, "карточка группы исчезла из разметки"
    assert "data-row" not in html, (
        "экран вернулся к строке-таблице — на 860px её колонки скрываются, а "
        "подписей ячеек у карточек нет"
    )


@pytest.mark.asyncio
async def test_account_groups_filters_block_collapsible(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Блок фильтров собран из общего макроса и свёрнут разметкой, а не Alpine.

    Свёрнутое состояние приходит с сервера классами, поэтому на мобильной
    ширине блок не мигает до инициализации Alpine. Утверждение переехало со
    снесённого раздела: полоса та же, макрос тот же, изменился только адрес
    отправки — у экрана он несёт идентификатор аккаунта.
    """
    account = await _seed_account(db_session)
    await _seed_group(db_session, account=account)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text
    assert 'class="filters' in html
    assert "filters__toggle" in html
    assert f'action="/accounts/{account.id}/groups"' in html


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
async def test_history_card_shows_error_text_in_full(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """План 04-07: в КАРТОЧКЕ СПИСКА текст ошибки лежит целиком (D-32).

    Соседний тест выше закрепляет полноту на странице записи, этот — в списке.
    Ограничение по высоте, введённое планом 04-07, ограничивает ВИДИМУЮ высоту
    блока средствами CSS; усечение текста СЕРВЕРОМ оно не вводит и ввести не
    имеет права — усечённое на сервере не раскрывается ничем.
    """
    long_error = (
        "PeerFloodError: Too many requests to join the group chat -420; "
        "retry after 86400 seconds (account temporarily restricted by Telegram)"
    )
    await _seed_send_log(
        db_session, status="fail", error_message=long_error, ad_title="Неудачная отправка"
    )

    response = await authed_client.get("/history")
    assert response.status_code == 200
    html = response.text
    assert long_error in html, "текст ошибки усечён сервером в карточке списка"
    assert "truncate" not in html


@pytest.mark.asyncio
async def test_history_card_escapes_error_text(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-26: разметка внутри текста ошибки остаётся текстом.

    Строка приходит из внешнего мессенджера и приложением не контролируется.
    Парный к test_admin_history_escapes_error_text: тот закрывает страницу
    записи в админке, этот — карточку пользовательского списка, где тот же текст
    теперь едет ещё и в диагностическом блоке для буфера обмена.
    """
    await _seed_send_log(
        db_session, status="fail", error_message='<img src=x onerror="alert(1)">'
    )

    html = (await authed_client.get("/history")).text
    assert "<img src=x" not in html, "текст ошибки отрисован как разметка"
    assert "&lt;img src=x" in html, "экранированного вывода ошибки нет"


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


# --- План 04-04: активность за неделю и ближайшие отправки ------------------
#
# Сетка 7×24 (прежнее решение D-09) снята на приёмке Фазы 4 в пользу бар-чарта
# макета. Часовая раскладка при этом ОСТАЛАСЬ в модуле аналитики и покрыта
# своими тестами — снят её показ на экране, а не сама раскладка.

@pytest.mark.asyncio
async def test_dashboard_activity_chart_renders_bars_without_table_elements(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """DASH-04: график построен примитивами раскладки, а не таблицей.

    Число столбцов утверждается ЯВНО: график, потерявший сутки или долю,
    отрисуется без единого исключения и вернёт те же 200, а пользователь увидит
    неполную неделю. Элементы таблицы запрещены по проекту
    (test_template_inventory), и график — самый естественный соблазн их вернуть.
    """
    await _seed_send_log(db_session, ad_title="Отправка недели")

    response = await authed_client.get("/dashboard")

    assert response.status_code == 200
    html = response.text
    assert "data-chart" in html, "график активности не отрисовался"
    assert html.count("data-chartcol") == 7 * CHART_BUCKETS_PER_DAY, (
        "график не 7 суток по четыре доли"
    )
    # Подпись у каждых суток окна ровно одна.
    assert html.count("data-chartdays") == 1
    for marker in ("<table", "<td", "<th ", "<thead", "<tbody"):
        assert marker not in html, marker
    for marker in UTILITY_MARKERS:
        assert marker not in html, marker


@pytest.mark.asyncio
async def test_dashboard_chart_bars_carry_height_but_never_inline_colour(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Высота столбца — инлайн-размер, цвет — атрибут.

    Запрет D-06 касается инлайн-ЦВЕТА: раскрасить график без него можно только
    признаком в атрибуте, на который обопрётся и Фаза 6. А размер по данным
    инлайном в проекте разрешён и применяется — ровно так его задаёт
    `components/progress.html`. Проверяется и то, и другое: подмена признака
    заливки инлайн-цветом прошла бы молча.
    """
    await _seed_send_log(db_session, ad_title="Отправка недели")

    html = (await authed_client.get("/dashboard")).text

    assert re.search(r'data-empty="[yn]" style="height: \d+%"', html), (
        "у столбцов нет доли высоты или признака пустоты"
    )
    assert 'data-empty="y"' in html, "пустые доли недели обязаны остаться видимыми"
    assert 'data-empty="n"' in html, "заполненная доля не помечена"
    assert 'style="background' not in html, "заливка выписана инлайн-стилем"


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


# --- План 12, Задача 1 → План 03-08: раздел «Группы» -------------------------
#
# Здесь стояли два последних места системного диалога раздела: удаление ОДНОЙ
# группы в строке и массовое удаление НАБОРА.
#
# План 03-08 снёс раздел целиком (D-01), и судьба этих утверждений разная:
#   * подтверждение удаления ОДНОЙ группы переехало на экран групп аккаунта и
#     проверяется подробнее прежнего — test_confirm_panel_names_the_group_and_
#     both_consequences, test_confirm_panel_is_unique_per_group,
#     test_confirm_panel_lives_outside_the_row и test_delete_trigger_is_a_real_
#     post_form в tests/test_pages/test_account_groups.py; присутствие настоящей
#     формы в этом месте закреплено ещё и перечнем ROW_DELETE_SITES
#     (tests/test_templates/test_components.py);
#   * массовое удаление НАБОРА исчезло вместе с возможностью (D-03): у экрана
#     групп аккаунта массовых операций нет, поэтому и щели между вопросом и
#     отправкой (T-12-01) взяться неоткуда — проверять больше нечего;
#   * подписи ячеек компенсировали шапку колонок, скрывающуюся на 860px. У
#     карточной строки нового экрана шапки нет вовсе, поэтому компенсировать
#     нечего — то же решение, что у сводного списка расписаний (план 02-07).

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
async def test_account_groups_row_names_each_value(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Замена подписей ячеек снесённого раздела (план 03-08).

    У карточной строки шапки колонок нет, значит и скрывать на 860px нечего —
    но пользовательская правда SC-5 «понятно, что означает каждое значение»
    обязана выполняться на любой ширине. У карточки она выполняется тем, что
    каждое значение названо СВОИМ СЛОВОМ прямо в строке, а не позицией в
    колонке: «в N расписаниях» / «не в расписаниях» и пометка «не найдена при
    синке». Утверждение положительное — иначе экран выпал бы из проверок вместе
    с удалёнными подписями.
    """
    account = await _seed_account(db_session)
    await _seed_group(db_session, name="Группа с названными значениями", account=account)

    html = (await authed_client.get(f"/accounts/{account.id}/groups")).text

    assert "Группа с названными значениями" in html, "строка отрисовалась пустой"
    assert "не в расписаниях" in html, (
        "значение «сколько расписаний» осталось без названия — на карточке его "
        "нечем объяснить, шапки колонок у экрана нет"
    )
    assert "data-cell-label" not in html, (
        "на карточном экране появились подписи ячеек скрывающейся шапки — "
        "компенсировать нечего, шапки колонок нет"
    )


# --- План 12, Задача 2 → План 02-07: раздел «Расписания» ---------------------
#
# Схема Задачи 1 Плана 12 повторялась дословно, пока сводный список был
# таблицей: форма удаления оставалась формой, перехват отправки навешивался на
# неё, панель стояла соседним элементом строки.
#
# План 02-07 перевернул раздел: удаления в сводном списке БОЛЬШЕ НЕТ (D-18), а
# строка стала карточкой. Оба обещания переехали, а не исчезли — ниже они
# утверждаются на своих новых местах:
#   * подтверждение удаления расписания — в редакторе объявления;
#   * понятность каждого значения на узкой ширине — строками «ключ — значение»
#     внутри карточки вместо подписей ячеек скрывающейся шапки.

# Каждое значение карточки названо СВОИМ ключом. Это замена SCHEDULE_CELL_LABELS:
# подписи ячеек компенсировали шапку колонок, скрывающуюся на 860px; у карточки
# шапки нет вовсе, и ключ стоит рядом со значением на любой ширине.
SCHEDULE_CARD_KEYS = (
    "Группы",
    "Время",
    "След. запуск",
)


@pytest.mark.asyncio
async def test_schedules_summary_list_offers_no_deletion(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-18: удаление расписания живёт ТОЛЬКО в редакторе объявления.

    Прежде сводный список предлагал удаление строкой. Утверждение не снято, а
    инвертировано: место, где не видно, что именно исчезнет, разрушительного
    действия не предлагает.
    """
    schedule = await _seed_schedule(db_session)

    html = (await authed_client.get("/schedules")).text

    assert f"/schedules/{schedule.id}/delete" not in html, (
        "удаление вернулось в сводный список — оно живёт только в редакторе (D-18)"
    )
    assert f"modal-open-schedule-del-{schedule.id}" not in html
    assert "confirm(" not in html, "системный диалог браузера остался"
    assert "onsubmit" not in html, "старый перехват отправки остался"


@pytest.mark.asyncio
async def test_schedule_delete_uses_modal_and_a_real_form_in_the_editor(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Оба прежних обещания раздела — на своём новом месте (SC-3, T-12-04).

    Подтверждение панелью дизайн-системы И настоящая форма под ним: без Alpine
    перехват не навешивается, и форма уходит POST-ом на прежний маршрут. Прежде
    это проверялось на строке сводного списка; после переезда удаления (D-18)
    единственное такое место — карточка редактора.
    """
    schedule = await _seed_schedule(db_session)

    html = (await authed_client.get(f"/ads/{schedule.ad_id}/edit?sched={schedule.id}")).text

    assert 'role="dialog"' in html, "панель подтверждения не отрисована"
    assert 'class="modal"' in html
    assert f"modal-open-sched-del-{schedule.id}" in html, (
        "форма удаления не открывает панель подтверждения"
    )
    assert html.count(f'id="sched-del-{schedule.id}"') == 1, (
        "панель подтверждения расписания не единственная"
    )
    assert "Отмена" in html, "у панели нет отказа от удаления"

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
async def test_schedules_card_names_each_value(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Каждое значение карточки расписания названо своим ключом (SC-5)."""
    schedules = [
        await _seed_schedule(db_session, ad_title=f"Объявление {i}") for i in range(2)
    ]

    html = (await authed_client.get("/schedules")).text

    for key in SCHEDULE_CARD_KEYS:
        assert html.count(f'<span class="kv__k">{key}</span>') == len(schedules), (
            f"ключ {key!r} проставлен не во всех карточках"
        )
    assert "<span data-cell-label>" not in html, (
        "подпись ячейки таблицы вернулась в карточный список — у него нет "
        "шапки колонок, которую она компенсирует"
    )


@pytest.mark.asyncio
async def test_schedules_partial_names_each_value(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Порция бесконечной прокрутки несёт те же ключи, что и первая страница.

    Правка живёт в МАКРОСЕ карточки, поэтому закрывает обе поверхности разом;
    тест доказывает это, а не проверяет второй файл на всякий случай.
    """
    schedules = [
        await _seed_schedule(db_session, ad_title=f"Объявление {i}") for i in range(2)
    ]

    response = await authed_client.get("/schedules/partial?offset=0&limit=30")
    assert response.status_code == 200
    html = response.text

    for key in SCHEDULE_CARD_KEYS:
        assert html.count(f'<span class="kv__k">{key}</span>') == len(schedules), (
            f"ключ {key!r} потерян в порции бесконечной прокрутки"
        )


def test_schedules_card_title_truncates_instead_of_pushing_controls():
    """Заголовок обрезается, а не выталкивает тумблер и переход в редактор.

    Замена признаку области сетки, на который опиралась строка-таблица: у
    карточки медиазапроса раздела нет, а молча ломается здесь другое — без
    min-width: 0 flex-элемент не сжимается ниже своего содержимого, и длинное
    название объявления выдавливает органы управления из шапки. Страница при
    этом отдаёт 200, и увидит поломку только пользователь на телефоне.
    """
    css = (
        Path(__file__).resolve().parents[2] / "app" / "static" / "css" / "app.css"
    ).read_text(encoding="utf-8")
    rule = css[css.index(".sched-item__title {") : css.index(".sched-item__tags")]

    assert "min-width: 0" in rule, "заголовок карточки перестал сжиматься"
    assert "text-overflow: ellipsis" in rule, "заголовок карточки перестал обрезаться"
    assert "white-space: nowrap" in rule, "заголовок карточки перестал быть однострочным"

    source = _template_source("schedules/includes/schedule_row.html")
    assert 'title="{{ item.ad_title }}"' in source, (
        "полное название объявления пропало из подсказки — обрезка стала потерей"
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
# RECENT_CELL_LABELS вместе с test_dashboard_cell_labels_present ВЫШЛИ отсюда
# планом 04-05: блок «Последние отправки» заменён живой лентой (DASH-03), её
# строка не таблица и колонок не имеет вовсе — подписывать в ней нечего.
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


# =============================================================================
# План 13, Задача 1: страховочная сетка подписей ячеек (UI-06, SC-5)
# =============================================================================
#
# Gap 2 из 01-VERIFICATION.md требует буквально: «каждый шаблон с data-rowhead
# несёт data-cell-label». Дословно это невыполнимо в двух местах сразу:
#
#   * литерал data-rowhead после Плана 09 эмитит МАКРОС rowhead, и в шаблонах
#     разделов его нет вовсе — поэтому обход идёт по ВЫЗОВУ макроса;
#   * литерал data-cell-label живёт в том же components/table.html, который
#     КАЖДЫЙ шаблон с шапкой импортирует. Проверка «признак есть где-то в
#     объединении с импортами» была бы зелёной на полностью НЕПОДПИСАННОЙ новой
#     таблице: признак пришёл бы из библиотеки. Такая сетка гарантирует ноль, а
#     читается как гарантия (T-13-02).
#
# Поэтому признак переопределён на ФОРМУ ВЫЗОВА в шаблоне РАЗДЕЛА, а файл
# библиотеки из объединения ИСКЛЮЧЁН. Это усиление требования, а не подмена:
# дословная проверка была бы зелёной на неподписанной новой таблице.

# Файл библиотеки. Исключается по ДВУМ причинам сразу:
#   1) он не потребитель — макросы rowhead / row_open / cell в нём ОБЪЯВЛЕНЫ, а
#      не вызваны, и наивный поиск по имени нашёл бы десятый файл там, где
#      потребителей девять;
#   2) признак подписи живёт именно здесь — и литералом атрибута, и ключевым
#      аргументом в сигнатуре макроса, — поэтому его исходник не имеет права
#      попадать в объединение как источник признака.
TABLE_COMPONENT = "components/table.html"

# Разрешение импортов — ОДИН уровень. Сознательное ограничение: в четырёх
# разделах шапку эмитит списочная страница, а ячейки — макрос строки из
# соседнего файла (ads, schedules, groups, dashboard). Обход, который смотрит
# только в файл с шапкой, объявил бы эти четыре раздела нарушителями, хотя
# подписи стоят. Цепочек длиннее одного уровня в проекте нет.
TEMPLATE_IMPORT_RE = re.compile(r"""\{%-?\s*(?:from|import)\s+["']([^"']+)["']""")

# Ключевой аргумент подписи. Левая граница проверяется НЕ через \b: перед словом
# не должно быть ни символа слова (show_label=, confirm_label=, cancel_label=,
# action_label=), ни дефиса (aria-label=). Утверждение, проходящее по чужому
# вхождению, гарантирует ноль и врёт про единицу (IN-08).
LABEL_KWARG_RE = re.compile(r"(?<![\w-])label\s*=")

# Атрибут подписи, написанный в шаблоне ВРУЧНУЮ — второй законный носитель:
# billing/balance.html и admin/groups_info.html эмитят подписи так с планов,
# предшествовавших набору 09-13.
CELL_LABEL_ATTR = "data-cell-label"

# Написанный вручную открывающий тег строки. Отрицательный просмотр вперёд
# отсекает data-rowhead: подстрока data-row внутри него — ровно тот промах,
# который разбирает IN-08. Второе условие обязательно для
# accounts/partials/sync_status_card.html: он собирает открывающий тег сам и
# макрос row_open не вызывает.
MANUAL_ROW_ATTR_RE = re.compile(r"data-row(?![\w-])")


# --- разрешитель признака ----------------------------------------------------


def _resolve_template(rel: str) -> str | None:
    """Исходник шаблона по пути относительно app/templates, либо None."""
    path = TEMPLATES_DIR / rel
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _macro_call_arglists(source: str, macro_name: str) -> list[str]:
    """Списки аргументов всех ВЫЗОВОВ макроса ``macro_name`` в исходнике.

    Разбор идёт от места вызова вперёд СО СЧЁТЧИКОМ СКОБОК до парной
    закрывающей. Регулярное выражение «до первой закрывающей» ломается на
    ``cell(text=(ad.sends_count or 0), …, label=AD_COLUMNS[2])`` и теряет
    подпись молча.

    ОБЪЯВЛЕНИЕ макроса вызовом не считается: ``{% macro cell(…, label=None) %}``
    несёт ключевой аргумент подписи в СИГНАТУРЕ, и наивный поиск по имени
    объявил бы библиотеку подписанной — ровно тот класс ошибки, который
    разбирает IN-08.
    """
    arglists: list[str] = []
    for match in re.finditer(rf"(?<![\w.]){re.escape(macro_name)}\s*\(", source):
        if source[: match.start()].rstrip().endswith("macro"):
            continue
        depth = 0
        start = match.end()
        for index in range(match.end() - 1, len(source)):
            char = source[index]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    arglists.append(source[start:index])
                    break
        else:  # pragma: no cover — незакрытая скобка в шаблоне
            arglists.append(source[start:])
    return arglists


def _has_cell_label_marker(source: str) -> bool:
    """Признак подписи ячейки в ОДНОМ исходнике шаблона раздела.

    Ровно два законных носителя:
      * вызов макроса ``cell``, в списке аргументов которого стоит ключевой
        аргумент ``label=`` — так подпись приходит после Плана 09;
      * атрибут ``data-cell-label``, написанный в шаблоне ВРУЧНУЮ — так подписи
        стоят в billing/balance.html и admin/groups_info.html с прежних планов.

    Голое слово ``label`` признаком НЕ является: оно принадлежит также макросам
    field / textarea_field / select_field, toggle, progress и составному
    аргументу ``show_label=`` у messenger_icon. Ограничение списком аргументов
    ВЫЗОВА ячейки отсекает первые, проверка левой границы — второй.
    """
    if CELL_LABEL_ATTR in source:
        return True
    return any(
        LABEL_KWARG_RE.search(arglist)
        for arglist in _macro_call_arglists(source, "cell")
    )


def _union_sources(source: str, resolve=_resolve_template) -> dict[str, str]:
    """Объединение: свой исходник + импорты на ОДИН уровень, МИНУС библиотека.

    Исключение components/table.html — одна строка кода и единственное, что
    отделяет работающую сетку от декоративной (T-13-02). Без него признак
    приходит из компонента за любой шаблон, который компонент импортирует, и
    обход зелёный на полностью неподписанной новой таблице.
    """
    union = {"<сам шаблон>": source}
    for rel in TEMPLATE_IMPORT_RE.findall(source):
        if rel == TABLE_COMPONENT:
            continue
        resolved = resolve(rel)
        if resolved is not None:
            union[rel] = resolved
    return union


def _has_cell_label_marker_in_union(source: str, resolve=_resolve_template) -> bool:
    return any(
        _has_cell_label_marker(src)
        for src in _union_sources(source, resolve).values()
    )


def _project_templates() -> list[tuple[str, str]]:
    """Все шаблоны проекта парами «путь относительно app/templates — исходник».

    Файл библиотеки исключён целиком: он не потребитель примитивов, он их
    объявляет.
    """
    result = []
    for path in sorted(TEMPLATES_DIR.rglob("*.html")):
        rel = path.relative_to(TEMPLATES_DIR).as_posix()
        if rel == TABLE_COMPONENT:
            continue
        result.append((rel, path.read_text(encoding="utf-8")))
    return result


def _templates_calling_macro(macro_name: str) -> set[str]:
    """Шаблоны, ВЫЗЫВАЮЩИЕ макрос примитива строки."""
    return {
        rel
        for rel, source in _project_templates()
        if _macro_call_arglists(source, macro_name)
    }


def _row_drawing_templates() -> set[str]:
    """Шаблоны, рисующие строку: вызов row_open ЛИБО ручной атрибут строки.

    Второе условие обязательно: accounts/partials/sync_status_card.html
    собирает открывающий тег сам и макрос не вызывает — без него
    инвентаризация из девяти файлов не сойдётся.
    """
    return {
        rel
        for rel, source in _project_templates()
        if _macro_call_arglists(source, "row_open") or MANUAL_ROW_ATTR_RE.search(source)
    }


# --- синтетические исходники: проверяют САМ разрешитель, а не проект ---------

SYNTHETIC_LIBRARY_IMPORT_NO_LABELS = (
    '{% from "components/table.html" import rowhead, row_open, row_close, cell %}\n'
    "{{ rowhead(columns=['Раз', 'Два'], cols='1fr 1fr') }}\n"
    "{{ row_open(cols='1fr 1fr') }}\n"
    "{{- cell(text='значение') }}\n"
    "{{- cell(text='ещё одно') }}\n"
    "{{ row_close() }}\n"
)

SYNTHETIC_FOREIGN_LABEL_KWARGS = {
    "макрос поля": "{{ field(name='search', label='Поиск', placeholder='Название') }}",
    "макрос тумблера": (
        "{{ toggle(name='select_all', id='select-all-checkbox', label='Выбрать все') }}"
    ),
    "макрос полосы прогресса": (
        "{{ progress(percent=40, label='Израсходовано 4 из 10') }}"
    ),
    "иконка мессенджера": (
        "{{ messenger_icon(group.messenger_type, size='avatar', show_label=false) }}"
    ),
}

SYNTHETIC_NESTED_PARENS_WITH_LABEL = (
    "{{- cell(text=(ad.sends_count or 0), mono=true, muted=true, "
    "title='Успешных отправок', label=AD_COLUMNS[2]) }}"
)

SYNTHETIC_NESTED_PARENS_WITHOUT_LABEL = (
    "{{- cell(text=(ad.sends_count or 0), mono=true, muted=true, "
    "title='Успешных отправок') }}"
)


def test_cell_label_marker_excludes_the_component_library():
    """Импорт библиотеки признаком подписи НЕ является.

    Тест против вырождения. Без исключения components/table.html из объединения
    обход зелёный на чём угодно: литерал атрибута и ключевой аргумент подписи
    живут в компоненте, а компонент импортирует каждый шаблон с шапкой.
    """
    library = _resolve_template(TABLE_COMPONENT)
    assert library is not None, "файл библиотеки не найден — проверь путь"
    # Библиотека признак НЕСЁТ. Именно поэтому её нельзя пускать в объединение.
    assert CELL_LABEL_ATTR in library
    assert "label=None" in library

    union = _union_sources(SYNTHETIC_LIBRARY_IMPORT_NO_LABELS)
    assert TABLE_COMPONENT not in union, (
        "файл библиотеки попал в объединение — сетка выродилась: признак придёт "
        "из компонента за любой шаблон, который его импортирует (T-13-02). "
        f"состав объединения: {sorted(union)}"
    )
    assert not _has_cell_label_marker_in_union(SYNTHETIC_LIBRARY_IMPORT_NO_LABELS), (
        "шаблон, который ТОЛЬКО импортирует библиотеку и вызывает ячейку без "
        "подписи, признан подписанным — обход гарантирует ноль, а читается как "
        "гарантия"
    )


def test_cell_label_marker_ignores_foreign_label_kwargs():
    """Ключевое слово подписи принадлежит ещё четырём макросам.

    Поле фильтра, тумблер, полоса прогресса и составной аргумент отключения
    подписи у иконки мессенджера. Новая неподписанная таблица в любом таком
    файле прошла бы обход по голому слову.
    """
    passing = {
        name: source
        for name, source in SYNTHETIC_FOREIGN_LABEL_KWARGS.items()
        if _has_cell_label_marker(source)
    }
    assert not passing, (
        "признак подписи прошёл по ЧУЖОМУ ключевому аргументу — "
        f"утверждение сильнее, чем есть: {sorted(passing)}"
    )


def test_cell_label_marker_survives_nested_parens():
    """Разбор аргументов доходит до ПАРНОЙ закрывающей скобки, а не до первой.

    В строке объявления есть вызов ячейки, у которого внутри списка аргументов
    стоит выражение в круглых скобках. «До первой закрывающей» теряет хвост
    вместе с подписью — и теряет молча.
    """
    (arglist,) = _macro_call_arglists(SYNTHETIC_NESTED_PARENS_WITH_LABEL, "cell")
    assert arglist.rstrip().endswith("label=AD_COLUMNS[2]"), (
        "разбор аргументов оборвался на вложенной скобке — подпись потеряна "
        f"молча: {arglist!r}"
    )
    assert _has_cell_label_marker(SYNTHETIC_NESTED_PARENS_WITH_LABEL)
    assert not _has_cell_label_marker(SYNTHETIC_NESTED_PARENS_WITHOUT_LABEL), (
        "вызов с аргументом подсказки вместо подписи признан подписанным"
    )


# --- перечни, закрепляющие область действия сетки ---------------------------

# Шаблоны с шапкой колонок, у которых нет собственного GET-роута. Перечень
# существует, чтобы такой файл был НАЗВАН, а не выпал из сверки молча. Сегодня
# он пуст: все девять шаблонов с шапкой достижимы по адресу.
ROWHEAD_TEMPLATES_WITHOUT_ROUTE: frozenset[str] = frozenset()

# Шаблоны, которые рисуют СТРОКУ, но шапку не вызывают. Обход по шапке их не
# видит, и утверждать обратное нельзя. Каждый закрыт названным классом причины,
# чтобы новый безымянный файл этого класса краснел, а не растворялся.
ROW_TEMPLATES_WITHOUT_HEADER = {
    # Класс 1: макрос строки, потребляемый шаблоном с шапкой. Его исходник уже
    # входит в объединение своего списочного шаблона — подписи проверяются там.
    "ads/includes/ad_card.html": "макрос строки внутри объединения ads/list.html",
    # groups/includes/group_row.html ВЫШЕЛ из перечня планом 03-08 вместе с
    # самим шаблоном: глобальный раздел снесён (D-01). Строка группы на экране
    # аккаунта его место не занимает — она КАРТОЧНАЯ и примитив строки-таблицы
    # не рисует вовсе, поэтому в обход по строкам не попадает по построению.
    # schedules/includes/schedule_row.html ВЫШЕЛ из перечня планом 02-07: он
    # больше не рисует строку вовсе — сводный список стал карточным, и ни
    # вызова примитива строки, ни написанного вручную признака в нём нет.
    # dashboard/includes/recent_send_card.html ВЫШЕЛ из перечня планом 04-05
    # вместе с самим шаблоном: блок «Последние отправки» на дашборде заменён
    # живой лентой (DASH-03), и его макрос строки стал недостижим. Строка ленты
    # его место не занимает — она КАРТОЧНАЯ (ссылка с точкой статуса) и
    # примитив строки-таблицы не рисует вовсе, поэтому в обход по строкам не
    # попадает по построению.
    # Класс 2: зеркала строки раздела «Аккаунты». Закрыты тестом синхронности
    # Плана 11 — test_accounts_three_files_label_the_same_columns считает
    # подписи Counter'ом, то есть краснеет и на потере подписи в одной ветке.
    "accounts/partial_cards.html": "зеркало строки раздела, тест синхронности Плана 11",
    "accounts/partials/sync_status_card.html": (
        "зеркало строки раздела, тест синхронности Плана 11; открывающий тег "
        "написан вручную, макрос row_open не вызывается"
    ),
    # Класс 3: страницы-карточки без шапки колонок вовсе. На 860px нечему
    # скрываться, значит и компенсировать подписью нечего.
    "admin/group_info_detail.html": "страница-карточка, шапки колонок нет вовсе",
    "admin/user_history_detail.html": "страница-карточка, шапки колонок нет вовсе",
    # history/detail.html ВЫШЕЛ из перечня планом 04-07: страница записи
    # перевёрстана на ПРИМИТИВ ЗАПИСИ (data-hrow) и строку-таблицу больше не
    # рисует вовсе — ни вызова row_open, ни написанного вручную признака строки
    # в ней не осталось, поэтому в обход по строкам она не попадает по
    # построению. Из проекта файл никуда не делся: страница сохранена (D-24),
    # лента дашборда и кнопка «Подробнее» ведут именно в неё. Её собственный
    # примитив закреплён test_history_detail_reuses_the_record_primitive_and_
    # adds_no_view_switch в tests/test_pages/test_history.py — по той же схеме,
    # по какой закреплены расписания и экран групп аккаунта.
}


class RowheadPage(NamedTuple):
    """Вход таблицы параметризации: одна страница с шапкой колонок.

    unlabelled — ОЖИДАЕМАЯ разность «названия колонок шапки минус подписи»,
    объявленная явно, а не выведенная. Это и делает сетку строгой: новая колонка
    без подписи увеличивает разность и роняет тест.
    """

    template: str
    url: str
    admin: bool
    seed: str
    unlabelled: frozenset[str]
    note: str = ""


ROWHEAD_PAGES = (
    RowheadPage(
        "accounts/list.html", "/accounts", False, "accounts", frozenset({"Аккаунт"})
    ),
    RowheadPage("ads/list.html", "/ads", False, "ads", frozenset({"Объявление"})),
    # schedules/list.html ВЫШЕЛ из таблицы планом 02-07: шапку колонок он больше
    # не вызывает — сводный список карточный, и компенсировать скрывающуюся на
    # 860px шапку ему нечем, потому что шапки нет. Обещание «понятно, что
    # означает каждое значение» переехало в
    # test_schedules_card_names_each_value.
    #
    # groups/list.html ВЫШЕЛ из таблицы планом 03-08 вместе с самим шаблоном:
    # глобальный раздел снесён (D-01). Замены в таблице у него нет и быть не
    # может — экран групп аккаунта шапки колонок не вызывает, потому что список
    # у него карточный; обещание «понятно, что означает каждое значение»
    # переехало в test_account_groups_row_names_each_value.
    # dashboard.html ВЫШЕЛ из таблицы планом 04-05: шапку колонок он больше не
    # вызывает — единственный блок дашборда со строкой-таблицей («Последние
    # отправки») заменён живой лентой (DASH-03), а её строка карточная.
    # Компенсировать скрывающуюся на 860px шапку ему нечем, потому что шапки
    # нет; обещание «понятно, что означает каждое значение» лента держит иначе —
    # текст события написан фразой («объявление → группа»), а не разложен по
    # безымянным колонкам.
    RowheadPage(
        "admin/users.html", "/admin/users", True, "admin_users",
        frozenset({"Пользователь"}),
    ),
    RowheadPage(
        "admin/user_detail.html", "/admin/users/{user_id}", True, "admin_user_detail",
        frozenset({"Аккаунт"}),
    ),
    # НАБЛЮДЕНИЕ, а НЕ принятая базовая линия. История операций эмитила подписи
    # ДО набора планов 09-13, причём атрибутом вручную, и покрыла две колонки из
    # четырёх. 01-VERIFICATION.md пробелом это не считает и относит страницу к
    # применившим примитив, поэтому дописывать подписи здесь нельзя — работа вне
    # закрываемого пробела. Но пользовательская правда SC-5 «понятно, что каждое
    # значение означает» на этой странице остаётся частично ложной: «Тип» и
    # «Описание» на 860px остаются без названия. Передано в /gsd-verify-work
    # (T-13-09). Формулировка «принято как базовая линия» запрещена.
    RowheadPage(
        "billing/balance.html", "/billing", False, "billing",
        frozenset({"Дата", "Тип", "Описание"}),
        note="НАБЛЮДЕНИЕ для /gsd-verify-work: «Тип» и «Описание» не подписаны "
        "помимо колонки даты; НЕ принятая базовая линия",
    ),
    # НАБЛЮДЕНИЕ, а НЕ принятая базовая линия — та же история, что у тарифов:
    # «Канал» и «Обновлено» на 860px остаются без названия (T-13-09).
    RowheadPage(
        "admin/groups_info.html", "/admin/groups-info", True, "admin_groups_info",
        frozenset({"Группа", "Канал", "Обновлено"}),
        note="НАБЛЮДЕНИЕ для /gsd-verify-work: «Канал» и «Обновлено» не подписаны "
        "помимо колонки названия; НЕ принятая базовая линия",
    ),
)


async def _seed_rowhead_page(db: AsyncSession, seed: str) -> None:
    """Наполняет страницу так, чтобы шапка и хотя бы одна строка отрисовались.

    Пустая страница рисует empty_state: и шапки, и подписей на ней нет, и
    сравнение разностей зазеленело бы вакуумно.
    """
    if seed == "accounts":
        await _seed_account(db, type_="max")
    elif seed == "ads":
        await _seed_ad(db)
    elif seed == "schedules":
        await _seed_schedule(db)
    elif seed == "dashboard":
        await _seed_send_log(db)
    elif seed == "admin_users":
        pass  # обычный пользователь и админ зарегистрированы фикстурами
    elif seed == "admin_user_detail":
        await _seed_account(db, type_="max")
    elif seed == "billing":
        await _seed_transaction(db)
    elif seed == "admin_groups_info":
        await _seed_group_info(db)
    else:  # pragma: no cover — защита от опечатки в таблице параметризации
        raise AssertionError(f"неизвестное наполнение: {seed}")


def test_every_rowhead_template_has_cell_labels():
    """Каждый шаблон, вызывающий шапку колонок, несёт признак подписи ячейки.

    Признак ищется в ОБЪЕДИНЕНИИ «свой исходник + импорты на один уровень»,
    из которого ИСКЛЮЧЁН components/table.html. Исключение — единственное, что
    отделяет работающую сетку от декоративной (T-13-02).
    """
    templates = _templates_calling_macro("rowhead")
    assert templates, "шаблоны с шапкой колонок не найдены — проверь разрешитель"

    offenders = {}
    for rel in sorted(templates):
        source = _resolve_template(rel)
        assert source is not None, rel
        if not _has_cell_label_marker_in_union(source):
            offenders[rel] = sorted(_union_sources(source))

    assert not offenders, (
        "шаблоны с шапкой колонок БЕЗ подписей ячеек — на 860px шапка "
        "скрывается, и значения остаются без названий. Искали: вызов cell(...) "
        f"с ключевым аргументом label= ЛИБО атрибут {CELL_LABEL_ATTR}, "
        f"написанный вручную; в объединении БЕЗ {TABLE_COMPONENT}. "
        + "; ".join(f"{rel} -> объединение {union}" for rel, union in offenders.items())
    )


def test_rowhead_pages_all_have_a_parametrization_entry():
    """Множество шаблонов с шапкой = таблица параметризации + перечень без роута.

    Новый шаблон с шапкой роняет тест на отсутствии входа, а не проходит по
    умолчанию: сетка нужна для тех таблиц, которых ещё нет.
    """
    found = _templates_calling_macro("rowhead")
    declared = {page.template for page in ROWHEAD_PAGES} | set(
        ROWHEAD_TEMPLATES_WITHOUT_ROUTE
    )

    assert TABLE_COMPONENT not in found, (
        f"{TABLE_COMPONENT} попал в потребители: ОБЪЯВЛЕНИЕ макроса принято за "
        "вызов — счёт не сойдётся ни здесь, ни в объединении"
    )
    assert found == declared, (
        "шаблоны с шапкой колонок разошлись с таблицей параметризации: "
        f"без входа в таблице {sorted(found - declared)}; "
        f"в таблице, но шапку не вызывают {sorted(declared - found)}"
    )
    # Восемь → семь → ШЕСТЬ: план 03-08 снёс groups/list.html вместе с разделом
    # (D-01), план 04-05 снял шапку с дашборда вместе с блоком последних
    # отправок. Уменьшение объявленного числа — признание СОЗНАТЕЛЬНОГО снятия;
    # молчаливое исчезновение шаблона с шапкой по-прежнему краснеет.
    assert len(declared) == 6, (
        f"ожидалось шесть шаблонов с шапкой колонок, объявлено {len(declared)}: "
        f"{sorted(declared)}"
    )


def test_row_templates_without_header_are_accounted_for():
    """Шаблоны, рисующие строку БЕЗ шапки, названы поимённо с классом причины.

    Обход по шапке их не видит. Перечень закрепляется утверждением, чтобы новый
    файл того же класса краснел, а не растворялся в прозе.
    """
    found = _row_drawing_templates() - _templates_calling_macro("rowhead")
    declared = set(ROW_TEMPLATES_WITHOUT_HEADER)

    assert found == declared, (
        "шаблоны строки без шапки колонок разошлись с объявленным перечнем: "
        f"не названы {sorted(found - declared)}; "
        f"названы, но строку не рисуют {sorted(declared - found)}"
    )
    # Восемь → семь → шесть → ПЯТЬ: макрос строки снесённого раздела удалён
    # планом 03-08 вместе с его списочной страницей, макрос строки последних
    # отправок — планом 04-05 вместе с заменённым блоком дашборда, а страница
    # записи истории планом 04-07 перестала рисовать строку вовсе (перевёрстана
    # на примитив записи). Уменьшение объявленного числа — признание
    # СОЗНАТЕЛЬНОГО снятия; молчаливое исчезновение файла по-прежнему краснеет.
    assert len(declared) == 5, (
        f"ожидалось пять таких шаблонов, объявлено {len(declared)}"
    )
    # Файл подмены попадает в перечень по написанному ВРУЧНУЮ атрибуту строки:
    # макрос row_open он не вызывает. Без второго условия разрешителя он выпал
    # бы, и инвентаризация из девяти файлов не сошлась бы.
    swap = _resolve_template("accounts/partials/sync_status_card.html")
    assert swap is not None
    assert not _macro_call_arglists(swap, "row_open")
    assert MANUAL_ROW_ATTR_RE.search(swap)


@pytest.mark.asyncio
@pytest.mark.parametrize("page", ROWHEAD_PAGES, ids=lambda page: page.template)
async def test_rowhead_titles_are_covered_by_labels(
    page: RowheadPage,
    client: AsyncClient,
    auth_headers: dict,
    test_settings,
    db_session: AsyncSession,
):
    """Разность «названия колонок минус подписи» равна ОБЪЯВЛЕННОМУ множеству.

    Порог «минимум одна подпись» и полное покрытие названий — разные
    утверждения: в карточке пользователя колонок две, а подпись одна, и это не
    недоработка. Поэтому ожидаемая разность объявлена явно по одному входу на
    страницу — новая колонка без подписи увеличивает разность и роняет тест.
    """
    await _seed_rowhead_page(db_session, page.seed)
    user = await _user(db_session)

    if page.admin:
        await client.post(
            "/api/auth/register",
            json={
                "email": test_settings.admin_email,
                "password": "testpass123",
                "name": "Admin User",
            },
        )
        email = test_settings.admin_email
    else:
        email = "testuser@test.com"
    await client.post(
        "/login",
        data={"email": email, "password": "testpass123"},
        follow_redirects=False,
    )

    response = await client.get(page.url.format(user_id=user.id))
    assert response.status_code == 200, (
        f"{page.template}: страница {page.url} вернула {response.status_code}"
    )
    html = response.text

    header = _header_in(html)
    labels = _labels_in(html)
    assert header, f"{page.template}: шапка колонок пуста — сравнивать нечего"

    unlabelled = header - labels
    assert unlabelled == set(page.unlabelled), (
        f"{page.template}: без подписи остались {sorted(unlabelled)}, "
        f"а объявлено {sorted(page.unlabelled)}. "
        f"Лишние без подписи: {sorted(unlabelled - page.unlabelled)}; "
        f"неожиданно подписанные: {sorted(page.unlabelled - unlabelled)}. "
        f"{page.note}"
    )
    assert labels - header == set(), (
        f"{page.template}: подписи, которых нет в шапке колонок — шапка и "
        f"подписи разъехались: {sorted(labels - header)}"
    )


# =============================================================================
# План 13, Задача 2: вторая половина сетки подтверждений — обход по ВЫДАЧЕ
# =============================================================================
#
# Обход по исходникам (tests/test_templates/test_components.py) находит шаблоны
# без GET-роута, но НЕ видит разметку, собранную строкой в обработчике. Дыра
# ровно этого класса у фазы уже находилась: разметку ответов опроса пришлось
# выносить в партиал. По одной половине требование не закрывается.

# Тот же признак, что и в обходе по исходникам: точка перед именем допускается
# (window.confirm), символ слова — нет (confirm_label= диалогом не является).
RENDERED_DIALOG_RE = re.compile(r"(?<!\w)confirm\s*\(")

# Адреса раздела, включая порции бесконечной прокрутки и ответ опроса статуса —
# единственную разметку, собираемую обработчиком.
DIALOG_SWEEP_URLS = (
    "/dashboard",
    "/accounts",
    "/accounts/partial?offset=0&limit=30",
    "/ads",
    "/ads/partial?offset=0&limit=30",
    "/schedules",
    "/schedules/partial?offset=0&limit=30",
    # Адреса снесённого раздела «Группы» ушли отсюда планом 03-08: обход требует
    # 200, а по ним стоит заглушка-перенаправление. Его место занял экран групп
    # аккаунта — он адресуется идентификатором и потому дописывается к обходу в
    # самом тесте, как и ответ опроса статуса аккаунта.
    "/history",
    "/billing",
    "/profile",
)

DIALOG_SWEEP_ADMIN_URLS = (
    "/admin/users",
    "/admin/groups-info",
)


@pytest.mark.asyncio
async def test_no_rendered_page_calls_browser_dialog(
    client: AsyncClient,
    auth_headers: dict,
    test_settings,
    db_session: AsyncSession,
):
    """Ни одна выдача раздела не содержит вызова системного диалога.

    Отдельно проходится ответ опроса статуса аккаунта: его разметки нет на
    первичной отрисовке страницы, и вернувшийся туда диалог не увидел бы ни
    один обход по списочным адресам.
    """
    account = await _seed_account(db_session, type_="max")
    for seed in ("ads", "schedules", "dashboard", "billing"):
        await _seed_rowhead_page(db_session, seed)
    await _seed_group_info(db_session)
    # Экран групп аккаунта адресуется идентификатором и в статический перечень
    # по построению не входит; в обход он попадает вместе со своей порцией
    # прокрутки — тем же приёмом, что ответ опроса статуса аккаунта.
    await _seed_group(db_session, account=account)
    account_groups_urls = (
        f"/accounts/{account.id}/groups",
        f"/accounts/{account.id}/groups/partial?offset=0&limit=30",
    )

    await client.post(
        "/login",
        data={"email": "testuser@test.com", "password": "testpass123"},
        follow_redirects=False,
    )

    offenders = {}
    urls = [
        *DIALOG_SWEEP_URLS,
        f"/accounts/{account.id}/sync-status",
        *account_groups_urls,
    ]
    for url in urls:
        response = await client.get(url)
        assert response.status_code == 200, f"{url} вернул {response.status_code}"
        if RENDERED_DIALOG_RE.search(response.text):
            offenders[url] = len(RENDERED_DIALOG_RE.findall(response.text))

    await client.post(
        "/api/auth/register",
        json={
            "email": test_settings.admin_email,
            "password": "testpass123",
            "name": "Admin User",
        },
    )
    await client.post(
        "/login",
        data={"email": test_settings.admin_email, "password": "testpass123"},
        follow_redirects=False,
    )
    for url in DIALOG_SWEEP_ADMIN_URLS:
        response = await client.get(url)
        assert response.status_code == 200, f"{url} вернул {response.status_code}"
        if RENDERED_DIALOG_RE.search(response.text):
            offenders[url] = len(RENDERED_DIALOG_RE.findall(response.text))

    assert not offenders, (
        "системный диалог браузера вернулся в ОТРЕНДЕРЕННУЮ страницу — обход по "
        f"исходникам такую разметку не видит: {offenders}"
    )


# --- План 02-04: редактор объявления ----------------------------------------
#
# Редактор — первый экран фазы 2 и единственный экран проекта с двухколоночной
# сеткой. Он собран на примитивах раздела 8 app.css и на макросах Фазы 1;
# собственной вёрстки и utility-классов в нём быть не должно.


@pytest.mark.asyncio
async def test_ads_editor_no_utility_classes(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Обе страницы редактора избавлены от классов удалённого фреймворка."""
    ad = await _seed_ad(db_session, title="Объявление редактора")

    for url in ("/ads/new", f"/ads/{ad.id}/edit"):
        response = await authed_client.get(url)
        assert response.status_code == 200, url
        for marker in UTILITY_MARKERS:
            assert marker not in response.text, f"{url}: {marker}"


@pytest.mark.asyncio
async def test_ads_editor_uses_grid_primitives(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Сетка редактора и липкая колонка размечены атрибутами раздела 8.

    Медиазапрос ≤900px опирается ровно на эти атрибуты: без них колонки не
    схлопнутся на телефоне, а страница продолжит отдавать 200.
    """
    ad = await _seed_ad(db_session, title="Сетка редактора")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    assert "data-editor" in html
    assert "data-editor-side" in html
    assert "data-media" in html, "полоса вложений размечена не примитивом раздела"


@pytest.mark.asyncio
async def test_ads_editor_action_bar_wraps_delete_to_its_own_row(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Строка действий и разрушительное действие — РАЗНЫЕ блоки разметки.

    На 400px «Сохранить»/«Отмена» переносятся вместе, а удаление стоит отдельным
    рядом ниже: перенос внутрь одного ряда поставил бы удаление рядом с
    первичной кнопкой.
    """
    ad = await _seed_ad(db_session, title="Строка действий")

    html = (await authed_client.get(f"/ads/{ad.id}/edit")).text

    bar = html.index("data-actions")
    delete_form = html.index(f'action="/ads/{ad.id}/delete"')
    assert bar < delete_form, "удаление оказалось в одном ряду с первичной кнопкой"


# --- План 02-05: секция расписаний в редакторе ------------------------------
#
# Карточка расписания собрана на примитивах второй половины раздела 8. Все её
# контейнеры — ПЕРЕНОСЯЩИЕСЯ: горизонтального скролла и обрезки не появляется
# ни на одной ширине (UI-SPEC §Responsive Contract).

APP_CSS = Path(__file__).resolve().parents[2] / "app" / "static" / "css" / "app.css"


async def _seed_editor_schedule(db: AsyncSession) -> tuple[Ad, Schedule]:
    """Объявление с расписанием, аккаунтом и группой — под редактор, не список."""
    user = await _user(db)
    ad = await _seed_ad(db, title="Объявление секции расписаний")
    account = await _seed_account(db, type_="tg_user")
    group = Group(
        user_id=user.id,
        account_id=account.id,
        messenger_type="tg_user",
        group_external_id="ext-sched",
        name="Группа секции расписаний",
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id,
        group_ids=[group.id],
        days_of_week=[0, 2, 4],
        times_of_day=["09:30"],
        timezone="UTC",
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return ad, schedule


@pytest.mark.asyncio
async def test_ads_editor_schedule_section_uses_section_8_primitives(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Секция расписаний размечена примитивами раздела, а не своей вёрсткой."""
    ad, schedule = await _seed_editor_schedule(db_session)

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text

    assert "data-sched-list" in html
    assert "data-sched-card" in html
    assert "chip-set" in html, "полоса аккаунтов размечена не примитивом раздела"
    assert "day-grid" in html, "сетка дней размечена не примитивом раздела"
    assert "time-pill" in html, "таблетка времени размечена не примитивом раздела"
    assert "group-pick" in html, "выбор групп размечен не примитивом раздела"


@pytest.mark.asyncio
async def test_ads_editor_schedule_section_no_utility_classes(
    authed_client: AsyncClient, db_session: AsyncSession
):
    ad, schedule = await _seed_editor_schedule(db_session)

    html = (await authed_client.get(f"/ads/{ad.id}/edit?sched={schedule.id}")).text
    for marker in UTILITY_MARKERS:
        assert marker not in html, marker


def test_editor_collapses_to_one_column_and_shrinks_day_cells():
    """Одноколоночная раскладка на ≤900px и ячейка дня 40px на ≤400px.

    Оба правила — CSS, поведенческой проверки для них не существует: страница
    отдаёт 200 одинаково и с ними, и без них, а увидел бы разницу только
    пользователь на телефоне.
    """
    css = APP_CSS.read_text(encoding="utf-8")

    assert "[data-editor] { grid-template-columns: minmax(0, 1fr) !important; }" in css
    assert "[data-editor-side] { position: static !important; }" in css
    assert ".day-grid .chip { width: 40px; }" in css
    # Полосы прогресса внутри карточки расписания нет и быть не может (D-17).
    assert ".sched-card__progress" not in css
    assert "[data-sched-card] .progress" not in css


# --- UAT Фазы 4, тест 1: три расхождения дашборда с макетом ------------------
#
# Все три — CSS/раскладка, и ни одно из них НЕ ВИДНО поведенческой проверке:
# страница отдаёт 200 и с ними, и без них, разметка на месте, данные верные.
# Отсюда форма проверок — утверждения о самом правиле, как у соседнего теста
# редактора выше. Каждое поймано на живом стеке и подтверждено скриншотом.


def test_upcoming_badge_sizes_the_messenger_glyph():
    """Бейдж канала задаёт размер иконки — иначе строка разъезжается.

    Макрос messenger_icon вызывается дашбордом с size='' по уговору «размер
    задаёт раздел» (его собственный докстринг). Раздел истории свою половину
    уговора выполняет правилом [data-hrow] [data-area=head] svg, дашборд — не
    выполнял, и svg с одним viewBox без width/height растягивался до размера
    контейнера: иконки каналов выросли в разы, высота строки «Ближайших
    отправок» — следом, подпись канала уехала за правый край.

    Размер 11px и форма пилюли взяты из макета (бейдж строки ближайшей
    отправки: mono 10px, отступы 4px 8px 4px 6px, радиус 6px).
    """
    css = APP_CSS.read_text(encoding="utf-8")

    assert "[data-upbadge] .msg__glyph { width: 11px; height: 11px; }" in css, (
        "размер иконки канала на дашборде снят — svg снова растянется по контейнеру"
    )
    assert "[data-upbadge] .msg {" in css, "пилюля бейджа макета снята"
    # Тон приходит атрибутом канала: иконка MAX залита градиентом, а не
    # currentColor, и через цвет глифа её бейдж не покрасить.
    for channel in ("tg_user", "wa", "max"):
        assert f'[data-upbadge][data-channel="{channel}"] .msg' in css, channel


def test_activity_chart_columns_are_fractional_not_fixed():
    """Столбцы графика — ДОЛЕВЫЕ, поэтому мёртвого поля справа не возникает.

    Прежняя сетка 7×24 держала ячейку в жёстких 14px при `width: max-content` и
    занимала около четырёхсот пикселей в карточке любой ширины — справа
    оставалась пустота в треть экрана. У долевого столбца этой болезни нет по
    построению, и фиксированная ширина сюда вернуться не должна.

    Высота контейнера ФИКСИРОВАНА намеренно: доля столбца считается процентом
    от неё, а высота по содержимому у пустых span схлопнулась бы в ноль ровно
    так же, как схлопывались ячейки прежней сетки.
    """
    css = APP_CSS.read_text(encoding="utf-8")

    assert (
        "[data-chart] { display: flex; align-items: flex-end; gap: 4px; height: 120px; }"
        in css
    ), "контейнер графика потерял высоту — проценты столбцов схлопнутся в ноль"
    assert "[data-chartcol] {\n  flex: 1;" in css, "столбец перестал быть долевым"
    # Ноль обязан остаться видимым — час без отправок не дырка в графике.
    assert "min-height: 2px" in css
    # Прокрутки этому блоку больше не нужно: долевой столбец влезает всегда.
    assert "[data-heatscroll]" not in css, "остался контейнер прокрутки снятой сетки"
    assert "[data-heatcell]" not in css, "остались правила снятой сетки"


def test_dashboard_blocks_share_one_head_without_a_divider():
    """Три блока дашборда несут ОДНУ шапку, и разделителя под ней нет.

    `card_open(title=...)` рисует `.card__head` с `border-bottom`, которого в
    макете нет ни у одной карточки дашборда: «Ближайшие отправки» шли через
    него и получали линию, а лента и график — нет, и две карточки одной пары
    выглядели по-разному.

    Правило ОДНО на три атрибута: до консолидации их было два с побайтово
    совпадающими телами. Сам примитив `.card__head` с разделителем остаётся —
    здесь снято его применение на этой странице, а не он сам.
    """
    css = APP_CSS.read_text(encoding="utf-8")
    page = (TEMPLATES_DIR / "dashboard.html").read_text(encoding="utf-8")
    chart = (
        TEMPLATES_DIR / "dashboard" / "includes" / "activity_chart.html"
    ).read_text(encoding="utf-8")

    assert (
        "[data-blockhead] { display: flex; align-items: center; gap: 10px;"
        " margin-bottom: 16px; }" in css
    )
    # Копии консолидированного правила не вернулись.
    assert "[data-feedhead]" not in css
    assert "[data-heathead]" not in css

    # Перепись шапок СТРАНИЦЫ: пара «Ближайшие отправки» / «Живая лента» плюс
    # перечень воркеров аккаунтов (DASH-05, план 04-11). Утверждение остаётся
    # тем же по смыслу — ни один блок страницы не заводит своей шапки в обход
    # общего атрибута, — и растёт вместе с числом блоков, а не ослабляется:
    # собственная шапка у нового блока это число НЕ увеличила бы.
    assert page.count("data-blockhead") == 3, "шапки блоков страницы разъехались"
    assert "data-blockhead" in chart, "у графика своя шапка вместо общей"

    # Комментарии Jinja снимаются ПЕРЕД проверкой вызова. Первая редакция этого
    # теста искала подстроку по сырому тексту и краснела на собственном
    # объяснении: докстринг шаблона называет `card_open(title=...)`, чтобы
    # сказать, почему он здесь НЕ применяется. Приём уже был пройден проектом на
    # запрете Docker SDK (план 04-05) — тот же вывод: объяснение запрета не
    # должно считаться его нарушением, иначе следующая правка снимет из
    # комментария самое ценное, ПРИЧИНУ.
    code = re.sub(r"\{#.*?#\}", "", page, flags=re.DOTALL)
    assert "card_open(title=" not in code, (
        "заголовок снова идёт через card_open — вернётся разделительная линия"
    )
    # Невакуумность: без снятия комментариев проверка ловила бы объяснение.
    assert "card_open(title=" in page, "объяснение причины ушло из шаблона"
    # Разделитель остаётся примитивом проекта для всех прочих разделов.
    assert ".card__head {" in css


def test_dashboard_pairs_upcoming_and_feed_in_two_columns():
    """«Ближайшие отправки» и «Живая лента» — пара в две колонки по макету.

    Оба шаблона называют себя «левой» и «правой половиной пары» в своих
    комментариях, но лежали прямыми детьми вертикальной стопки страницы и
    занимали полную ширину каждая: пара существовала в комментариях и не
    существовала на экране.

    Схлопывание в одну колонку делает сама сетка (`auto-fit` + `minmax`), и
    отдельного медиазапроса для этого нет — второй точки правды о том же
    переломе в проекте заводиться не должно.
    """
    css = APP_CSS.read_text(encoding="utf-8")
    page = (TEMPLATES_DIR / "dashboard.html").read_text(encoding="utf-8")

    assert (
        "grid-template-columns: repeat(auto-fit, minmax(330px, 1fr));" in css
    ), "сетка пары дашборда снята"
    assert "[data-dashpair] > * { min-width: 0; }" in css, (
        "без min-width: 0 длинное название вытолкнет колонку"
    )

    # Обёртка обязана охватывать ОБЕ половины, а не одну: открывающий тег стоит
    # до блока ближайших отправок, закрывающий — после контейнера ленты.
    assert "data-dashpair" in page
    assert page.index("data-dashpair") < page.index("Ближайшие отправки")
    assert page.index("/data-dashpair") > page.index('id="dash-feed"')
