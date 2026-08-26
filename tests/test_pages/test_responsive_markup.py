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

from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.payment import Payment
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.subscription import Subscription
from app.models.user import User
from app.pages.common import templates

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
    "billing": "/billing",
}

# ⚠️ ПЕРЕЧНЯ РАЗДЕЛОВ НА ПРИМИТИВЕ СТРОКИ-ТАБЛИЦЫ (MIGRATED_SECTIONS) БОЛЬШЕ НЕТ,
# И ЭТО ОБЪЯВЛЕННЫЙ ИТОГ, А НЕ ПРОПАЖА. Он опустел: раздел, стоявший в нём
# последним, вышел задачей 260825-of5. Пустую параметризацию оставлять нельзя —
# она не краснеет, а молча ничего не проверяет, поэтому перечень снят вместе с
# его единственным потребителем (test_list_page_has_responsive_primitives).
#
# История в перечень не входила НИКОГДА: у неё собственный примитив data-hrow,
# перестраивающийся раньше остальных (1080px).
#
# ЧЕТЫРЕ ВЫХОДА ПО ПОРЯДКУ, и у каждого — своя замена в проверках:
#   1. Расписания, план 02-07: сводный список стал КАРТОЧНЫМ на всех ширинах
#      (UI-SPEC §Responsive Contract). Замена — test_schedules_summary_list_is_card_based.
#   2. Глобальный раздел «Группы», план 03-08: снесён целиком (D-01). Его
#      замена — экран групп аккаунта, КАРТОЧНЫЙ с плана 03-05. Замена в
#      проверках — test_account_groups_list_is_card_based.
#   3. Объявления, задача 260825-m0b: список стал КАРТОЧНОЙ СЕТКОЙ — так его
#      описывает раздел `isAds` макета (unpacked.html:479). Замена —
#      test_ads_list_is_card_based.
#   4. Аккаунты, задача 260825-of5: список стал КАРТОЧНОЙ СЕТКОЙ — так его
#      описывает раздел `isAccounts` макета (unpacked.html:878). Замена —
#      test_accounts_list_is_card_based.
#
# Общая причина у всех четырёх одна: строку-таблицу разделы получили Планом
# 01-03, когда ОДНА форма списочной страницы была применена ко всем пяти
# разделам сразу, а макет описывает для них карточную сетку. Сетка
# перестраивается шириной трека сама, поэтому правила 860px и подписи ячеек,
# компенсирующие скрывающуюся шапку, этим разделам больше не нужны.

# Все разделы, переведённые на дизайн-систему, независимо от примитива.
# Планы 06-08 дописывают свои сюда.
#
# Перечень стал САМОСТОЯТЕЛЬНЫМ вместе со снятием MIGRATED_SECTIONS и
# по-прежнему СОДЕРЖИТ «Аккаунты»: проверка отсутствия utility-классов раздела
# не ослабляется ни на шаг — она никогда и не зависела от примитива.
#
# «Тарифы» встали сюда планом 05-05: раздел перевёрстан по макету и собран
# целиком из компонентов и примитивов Фазы 1; его собственные примитивы
# закреплены именованными проверками test_billing_* ниже, по той же схеме, что
# у расписаний и экрана групп аккаунта.
CLEAN_SECTIONS = [
    "accounts",
    "history",
    "schedules",
    "account_groups",
    "billing",
]


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


# ПОМОЩНИКА ПОСЕВА ЖУРНАЛА ОПЕРАЦИЙ ПО ОСТАТКУ ЗДЕСЬ БОЛЬШЕ НЕТ: ревизия `0020`
# уронила таблицу под ним, а раздел, который он наполнял, снят ещё планом
# `05.1-06`. Единственный его вызывающий — проверка отсутствия обработчиков
# события в разметке раздела — сеет теперь только строку журнала ДЕНЕГ, которая
# на странице и рисуется.


async def _seed_payment(
    db: AsyncSession, status: str = "succeeded", plan: str = "basic"
) -> Payment:
    """Строка журнала ДЕНЕГ. `created_at` ставится явно: у колонки есть умолчание."""
    user = await _user(db)
    payment = Payment(
        user_id=user.id,
        yookassa_payment_id="yoo_markup_seed",
        status=status,
        amount_value="1490.00",
        amount_currency="RUB",
        kind="subscription",
        plan=plan,
        created_at=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def _access_row(db: AsyncSession) -> Subscription:
    """Активная строка подписки пользователя — её заводит регистрация."""
    return (
        await db.execute(
            select(Subscription).where(
                Subscription.user_id == (await _user(db)).id,
                Subscription.is_active.is_(True),
            )
        )
    ).scalar_one()


async def _move_access_expiry(db: AsyncSession, delta: timedelta) -> datetime:
    """Сдвигает срок УЖЕ СУЩЕСТВУЮЩЕЙ строки, а не заводит вторую.

    Частичный уникальный индекс `uq_subscriptions_active_user` допускает у
    пользователя ровно одну активную строку, а пробный срок ему завела
    регистрация (план 05.1-01). Вторая вставка дала бы IntegrityError, то есть
    тест падал бы на посеве, а не на предмете.
    """
    row = await _access_row(db)
    row.expires_at = datetime.now(timezone.utc) + delta
    await db.commit()
    return row.expires_at


# _seed_group_info УДАЛЁН ПЛАНОМ 06-01 вместе со всеми своими потребителями:
# экраны справочника групп снесены (D-05), и наполнять стало нечего. Сама
# таблица `group_info`, её модель, её репозиторий и ревизия `0011` НЕ тронуты —
# снос касается поверхности, а не хранилища, и репозиторий по-прежнему покрыт
# tests/test_repositories/test_group_info.py.


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
    elif section == "billing":
        # ЕДИНСТВЕННЫЙ журнал раздела — деньги: история операций по балансу
        # сообщений снята планом 05.1-05 вместе с самим балансом. Пустой раздел
        # нарисовал бы пустое состояние, и проверка разметки зазеленела бы
        # вакуумно.
        await _seed_payment(db)
    else:  # pragma: no cover — защита от опечатки в параметризации
        raise AssertionError(f"неизвестный раздел: {section}")
    return SECTION_URLS[section]


# ⚠️ ЗДЕСЬ СТОЯЛ test_list_page_has_responsive_primitives — обход по перечню
# разделов на примитиве строки-таблицы. Он снят задачей 260825-of5 ВМЕСТЕ с
# перечнем: перечень опустел, а пустая параметризация не краснеет — она молча
# ничего не проверяет. Замены у него нет и быть не может: каждый из четырёх
# вышедших разделов закреплён СВОИМ положительным примитивом (перечисление — в
# комментарии над CLEAN_SECTIONS выше).


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
async def test_ads_card_shows_channel_pills(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Канал объявления показан пилюлей; объявление без расписаний — без пилюль.

    Обе половины утверждения обязательны. Без первой тест зеленел бы на разметке
    без каналов вовсе; без второй — на пилюле, приклеенной к КАЖДОЙ карточке
    независимо от данных, потому что на одном объявлении отличить «канал взят из
    расписания» от «канал нарисован всегда» нечем.

    Пилюля собрана на СУЩЕСТВУЮЩЕМ примитиве data-upbadge (заведён дашбордом,
    app/static/css/app.css): второй копии тонов пилюли канала в проекте нет, и
    признак здесь проверяется именно тот, что красит CSS.
    """
    await _seed_schedule(db_session, ad_title="Объявление с расписанием")
    await _seed_ad(db_session, title="Объявление без расписаний")

    html = (await authed_client.get("/ads")).text

    assert html.count("data-upbadge") == 1, (
        "пилюль канала на странице не ровно одна: расписание есть только у "
        "одного из двух объявлений"
    )
    assert 'data-upbadge data-channel="wa"' in html, (
        "канал пилюли не приехал атрибутом — тон пилюли красит CSS по нему"
    )


# Ключи значений карточки объявления. Это ТЕ ЖЕ ТРИ ВЕЛИЧИНЫ, что до задачи
# 260825-m0b стояли колонками строки-таблицы: раздел сменил вид, а не состав
# показанных данных.
ADS_CARD_KEYS = (
    "Отправок",
    "Расписаний",
    "Создано",
)


@pytest.mark.asyncio
async def test_ads_list_is_card_based(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Замена вклада раздела в обход по data-row (задача 260825-m0b).

    Список объявлений — карточная СЕТКА на всех ширинах, как раздел `isAds`
    канонического макета (unpacked.html:479), поэтому примитив строки-таблицы
    ему не подходит: на 860px её колонки скрываются, а подписей ячеек у карточек
    нет. Утверждение положительное: у списка есть СВОЙ примитив, а не «нет
    старого». Без него раздел просто выпал бы из проверок вместе со снятой
    строкой параметризации.
    """
    await _seed_ad(db_session, title="Карточное объявление")

    html = (await authed_client.get("/ads")).text

    assert "data-ads-grid" in html, "контейнер карточной сетки объявлений исчез"
    assert 'class="ad-card"' in html, "карточка объявления исчезла из разметки"
    assert "data-row" not in html, (
        "список объявлений вернулся к строке-таблице — на 860px её колонки "
        "скрываются, а подписей ячеек у карточек нет"
    )


@pytest.mark.asyncio
async def test_ads_card_names_each_value(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Каждое значение карточки объявления названо своим ключом.

    Сеются ДВА объявления и утверждается ЧИСЛО вхождений, а не факт: ключ,
    проставленный одной карточке из двух, зеленил бы проверку на вхождении и
    оставил бы половину выдачи с безымянными числами.
    """
    ads = [await _seed_ad(db_session, title=f"Объявление {i}") for i in range(2)]

    html = (await authed_client.get("/ads")).text

    for key in ADS_CARD_KEYS:
        assert html.count(f'<span class="kv__k">{key}</span>') == len(ads), (
            f"ключ {key!r} проставлен не во всех карточках"
        )
    assert "<span data-cell-label>" not in html, (
        "подпись ячейки таблицы вернулась в карточный список — у него нет "
        "шапки колонок, которую она компенсирует"
    )


async def _seed_ad_with_text(db: AsyncSession, title: str, text: str) -> Ad:
    """Объявление с ЗАДАННЫМ текстом.

    Отдельно от _seed_ad: тот ставит всем объявлениям один и тот же текст, и
    отличить поиск по названию от поиска по тексту на нём нечем — оба нашли бы
    всё.
    """
    user = await _user(db)
    ad = Ad(user_id=user.id, title=title, text=text, images=[])
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


@pytest.mark.asyncio
async def test_ads_search_matches_title_and_text(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Одно поле ищет по ДВУМ осям — по названию и по тексту объявления.

    Обе оси утверждаются порознь и каждая с отрицательной половиной: поиск,
    нашедший всё, зеленил бы проверку «нашлось нужное» ровно так же, как
    работающий.
    """
    await _seed_ad_with_text(db_session, "Аренда квартиры", "Тихий двор у метро")
    await _seed_ad_with_text(db_session, "Вакансия разработчика", "Питон и фастапи")

    by_title = (await authed_client.get("/ads?search=Аренда")).text
    assert "Аренда квартиры" in by_title, "поиск не нашёл по подстроке названия"
    assert "Вакансия разработчика" not in by_title, (
        "поиск по названию вернул объявление, названию не отвечающее"
    )

    by_text = (await authed_client.get("/ads?search=фастапи")).text
    assert "Вакансия разработчика" in by_text, "поиск не нашёл по подстроке ТЕКСТА"
    assert "Аренда квартиры" not in by_text, (
        "поиск по тексту вернул объявление, тексту не отвечающее"
    )


@pytest.mark.asyncio
async def test_ads_search_does_not_cross_ownership(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-m0b-01: поиск ДОПОЛНЯЕТ ограждение владения, а не заменяет его.

    Чужое объявление не находится ни по названию, ни по тексту. Условие отбора
    строится ОДНИМ выражением, первое слагаемое которого — владелец; потеряв
    его, страница отдала бы чужие записи по одной лишь строке запроса.
    """
    user = await _user(db_session)
    await _seed_ad_with_text(db_session, "Своё объявление", "Общее слово ромашка")
    foreign = Ad(
        user_id=user.id + 1000,
        title="Чужое объявление",
        text="Общее слово ромашка",
        images=[],
    )
    db_session.add(foreign)
    await db_session.commit()

    html = (await authed_client.get("/ads?search=ромашка")).text

    assert "Своё объявление" in html, "поиск не нашёл собственное объявление"
    assert "Чужое объявление" not in html, (
        "поиск вышел за границу владения — чужое объявление попало в выдачу"
    )


@pytest.mark.asyncio
async def test_ads_counter_counts_the_whole_result_not_the_page(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Счётчик считает ВСЮ выдачу, а не отданную страницу.

    Длина страницы ограничена PAGE_SIZE, поэтому на выдаче длиннее одной
    страницы она соврала бы — и соврала бы молча, показав ровно размер
    страницы.
    """
    user = await _user(db_session)
    db_session.add_all(
        [
            Ad(user_id=user.id, title=f"Объявление {i}", text="Текст", images=[])
            for i in range(31)
        ]
    )
    await db_session.commit()

    html = (await authed_client.get("/ads")).text

    assert "31 объявление" in html, (
        "счётчик показал не всю выдачу — на странице ровно PAGE_SIZE карточек, "
        "и её длина соврала бы именно этим числом"
    )


@pytest.mark.asyncio
async def test_ads_has_two_distinct_empty_states(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пустых состояния ДВА и они РАЗЛИЧАЮТСЯ действием (UI-SPEC E13 `empty`).

    Отфильтровавшему всё до нуля осмысленно предложить снять отбор, а не идти
    создавать ещё одно объявление; у пользователя без объявлений вовсе сбрасывать
    нечего.
    """
    empty = (await authed_client.get("/ads")).text
    assert "Объявлений пока нет" in empty, "пустое состояние «объявлений нет» исчезло"
    assert "Создать объявление" in empty, "приглашение создать первое объявление исчезло"

    await _seed_ad(db_session, title="Единственное объявление")
    not_found = (await authed_client.get("/ads?search=ничегонеподойдёт")).text
    assert "Объявления не найдены" in not_found, (
        "пустое состояние «поиск ничего не нашёл» исчезло"
    )
    assert "Объявлений пока нет" not in not_found, (
        "два пустых состояния слились в одно — отфильтровавшему всё до нуля "
        "предлагается создать объявление вместо сброса поиска"
    )
    assert "СБРОСИТЬ ПОИСК" in not_found, "сброса поиска в пустом состоянии нет"


@pytest.mark.asyncio
async def test_ads_search_survives_infinite_scroll(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Поиск доезжает до ВТОРОЙ порции — и в адресе сентинела, и в её составе.

    Утверждаются оба, потому что ломаются они порознь: сентинел без параметра
    отбора приносит неотобранное, а обработчик, игнорирующий параметр, приносит
    неотобранное даже при верном адресе. Потеря не роняет страницу — она молча
    подмешивает чужие по отбору объявления к отобранным.
    """
    user = await _user(db_session)
    db_session.add_all(
        [
            Ad(user_id=user.id, title=f"Акция {i}", text="Текст акции", images=[])
            for i in range(35)
        ]
        + [
            Ad(user_id=user.id, title=f"Прочее {i}", text="Другой текст", images=[])
            for i in range(5)
        ]
    )
    await db_session.commit()

    first = (await authed_client.get("/ads/partial?offset=0&limit=30&search=Акция")).text
    sentinel = re.findall(r'hx-get="([^"]+)"', first)
    assert sentinel, "сентинел исчез из первой порции"
    assert "search=" in sentinel[-1], (
        f"поиск потерян в адресе сентинела: {sentinel[-1]}"
    )

    second = (
        await authed_client.get("/ads/partial?offset=30&limit=30&search=Акция")
    ).text
    assert second.count('class="ad-card"') == 5, (
        "вторая порция отобрана не так, как первая: отобранных объявлений 35, "
        "и после смещения в 30 их обязано остаться ровно пять"
    )
    assert "Прочее" not in second, (
        "вторая порция подмешала объявления, отбору не отвечающие"
    )


@pytest.mark.asyncio
async def test_ads_partial_names_each_value(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Порция бесконечной прокрутки несёт те же ключи, что и первая страница.

    Правка живёт в МАКРОСЕ карточки, поэтому закрывает обе поверхности разом;
    тест доказывает это, а не проверяет второй файл на всякий случай.
    """
    ads = [await _seed_ad(db_session, title=f"Объявление {i}") for i in range(2)]

    response = await authed_client.get("/ads/partial?offset=0&limit=30")
    assert response.status_code == 200
    html = response.text

    for key in ADS_CARD_KEYS:
        assert html.count(f'<span class="kv__k">{key}</span>') == len(ads), (
            f"ключ {key!r} потерян в порции бесконечной прокрутки"
        )


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


# --- ЗАПРЕТ НА ВОЗВРАТ НЕДЕЛЬНОЙ АКТИВНОСТИ НА ДАШБОРД (задача 260826-9vv) ---
#
# Бар-чарт макета (он сменил сетку 7×24 прежнего решения D-09 на приёмке Фазы 4)
# снят со страницы целиком: он платил за свой ответ потоковым чтением недельного
# окна журнала отправок на КАЖДОЙ загрузке дашборда. Вместе с ним снят его
# шаблон, его правила в стилях и обе секции модуля аналитики, кроме него никем
# не читанные.
#
# Признаки блока перечислены ЗДЕСЬ ОДНИМ СПИСКОМ: три теста ниже проверяют
# разные поверхности (разметка, шаблоны, стили), но предмет у них один, и
# разъехавшиеся списки признаков дали бы запрет, дырявый ровно в том месте, где
# список короче. Тем же приёмом задача 260826-6jq свела признаки перечня
# воркеров в `WORKER_LIST_MARKERS`.
ACTIVITY_CHART_MARKERS = (
    "data-chart",
    "data-chartcol",
    "data-chartbar",
    "data-chartdays",
    "Активность за неделю",
    "отправок за 6 часов",
)


@pytest.mark.asyncio
async def test_the_dashboard_carries_no_weekly_activity_block(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """На дашборде нет ни столбцов недельной активности, ни их карточки.

    Отправка сеется НАРОЧНО: на пустых данных блок не рисовался и раньше, и
    запрет, поставленный без посева, прошёл бы вакуумно — он утверждал бы про
    пустой дашборд, а не про снятый блок.

    Разбирается ОТРЕНДЕРЕННЫЙ ответ, а не текст шаблона: комментарии Jinja до
    разметки не доезжают, и объяснение снятия, оставленное в `dashboard.html`,
    этот тест краснить не должно.

    Соседи по странице проверяются ТЕМ ЖЕ ТЕСТОМ: запрет, прошедший на
    снесённой заодно странице, запретом не является.

    Запрет инлайн-заливки (D-06) переехал сюда из снятого
    `test_dashboard_chart_bars_carry_height_but_never_inline_colour`: снятый
    вместе со своим предметом, он оставил бы страницу без единственной проверки
    того, что цвет на ней не выписывается инлайн-стилем.
    """
    await _seed_send_log(db_session, ad_title="Отправка недели")

    response = await authed_client.get("/dashboard")

    assert response.status_code == 200
    html = response.text
    for marker in ACTIVITY_CHART_MARKERS:
        assert marker not in html, (
            f"карточка недельной активности вернулась на дашборд: {marker!r}"
        )
    assert "За неделю отправок не было" not in html, (
        "пустое состояние снятого блока вернулось на дашборд"
    )
    assert 'style="background' not in html, "заливка выписана инлайн-стилем (D-06)"

    assert "data-metrics" in html, "вместе с блоком снесена сетка суточных плиток"
    assert "data-dashpair" in html, (
        "вместе с блоком снесена пара «Ближайшие отправки» / «Живая лента»"
    )
    assert 'hx-get="/dashboard/feed"' in html, (
        "вместе с блоком снесён опрос живой ленты"
    )


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


# --- Плана 11 «подписи колонок в ячейках раздела Аккаунты» БОЛЬШЕ НЕТ ---------
#
# ⚠️ ЧЕТЫРЕ ПРОВЕРКИ ПОДПИСЕЙ ЯЧЕЕК РАЗДЕЛА И ПРОВЕРКА «ПОДПИСИ ПРИШЛИ ИЗ СПИСКА
# КОЛОНОК» СНЯТЫ ЗАДАЧЕЙ 260825-of5, И ЭТО ОБЪЯВЛЕННОЕ СНЯТИЕ, А НЕ ПРОПАЖА.
# Подписи ячеек существовали, чтобы компенсировать шапку колонок, скрывающуюся
# на 860px. Раздел переведён на карточную сетку (unpacked.html:878): шапки
# колонок у него нет вовсе, компенсировать нечего, и подписи ячеек в карточку
# не переносятся.
#
# Обещание «понятно, что означает каждое значение» НЕ снято — оно переехало на
# КЛЮЧИ карточки и проверяется ТЕМ ЖЕ КОММИТОМ на всех ТРЁХ поверхностях
# раздела: test_accounts_card_names_each_value (списочная страница),
# test_accounts_partial_names_each_value (порция бесконечной прокрутки) и
# test_accounts_sync_card_names_each_value (блок подмены по опросу статуса).
# Счёт по веткам статуса сохранён: ключ, потерянный в одной ветке из трёх,
# по-прежнему краснеет.
#
# CELL_LABEL_RE и ROWHEAD_RE ОСТАЮТСЯ: у них есть другие потребители —
# страховочная сетка шапок и подписей прочих разделов ниже.

CELL_LABEL_RE = re.compile(r"<span data-cell-label>([^<]*)</span>")
ROWHEAD_RE = re.compile(r"<div data-rowhead[^>]*>(.*?)</div>", re.S)


async def _seed_all_account_branches(db: AsyncSession) -> list[MessengerAccount]:
    """По одному аккаунту на каждую из трёх веток статуса раздела."""
    return [
        await _seed_account_with_status(db, status)
        for status in ("active", "sync_failed", "syncing")
    ]


# --- Задача 260825-of5: карточная сетка раздела «Аккаунты» ------------------
#
# Раздел `isAccounts` макета (design/new_broadcaster_design.unpacked.html:878) —
# КАРТОЧНАЯ СЕТКА на всех ширинах. Строку-таблицу раздел получил Планом 01-03,
# когда одна форма списочной страницы была применена ко всем пяти разделам
# сразу; Фаза 6 своим объёмом брала подключение аккаунтов и опрос статуса, а
# формой списка не занималась.
#
# Ключи карточки — ТЕ ЖЕ ШЕСТЬ ВЕЛИЧИН, что до задачи стояли колонками: раздел
# сменил вид, а не состав показанных данных. Порядок повторяет объявление
# ACCOUNT_KEYS в трёх файлах раздела.

ACCOUNTS_GRID_MARKER = "data-accounts-grid"
ACCOUNTS_CARD_MARKER = 'class="acct-card"'

ACCOUNT_CARD_KEYS = (
    "Состояние",
    "Групп",
    "Расписаний",
    "Успешность",
    "Последняя отправка",
    "Подключён",
)


def _kv_key(name: str) -> str:
    """Разметка ключа карточки — ровно та, что проверяется у объявлений."""
    return f'<span class="kv__k">{name}</span>'


def _element_end(html: str, start: int) -> int:
    """Индекс конца элемента `<div …>`, открытого по смещению ``start``.

    Счёт по вложенности, а не «до первой закрывающей»: внутри контейнера сетки
    лежат карточки со своими блоками, и наивный поиск объявил бы сетку
    закрытой на первом же `</div>` внутри первой карточки.
    """
    depth = 0
    for match in re.finditer(r"<div\b|</div>", html[start:]):
        depth += 1 if match.group(0) == "<div" else -1
        if depth == 0:
            return start + match.end()
    raise AssertionError("контейнер сетки не закрыт")


@pytest.mark.asyncio
async def test_accounts_list_is_card_based(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Замена вклада раздела в обход по строке-таблице (задача 260825-of5).

    Список аккаунтов — карточная СЕТКА на всех ширинах, как раздел
    `isAccounts` канонического макета (unpacked.html:878), поэтому примитив
    строки-таблицы ему не подходит: на 860px её колонки скрываются, а подписей
    ячеек у карточек нет.

    Утверждение положительное: у списка есть СВОЙ примитив, а не «нет
    старого». Без положительной половины раздел просто выпал бы из проверок
    вместе со снятой строкой параметризации — ЧЕТВЁРТЫЙ тест этой формы после
    расписаний, экрана групп аккаунта и объявлений.
    """
    await _seed_account(db_session, type_="max")

    html = (await authed_client.get("/accounts")).text

    assert ACCOUNTS_GRID_MARKER in html, "контейнер карточной сетки аккаунтов исчез"
    assert ACCOUNTS_CARD_MARKER in html, "карточка аккаунта исчезла из разметки"
    assert "data-row" not in html, (
        "список аккаунтов вернулся к строке-таблице — на 860px её колонки "
        "скрываются, а подписей ячеек у карточек нет"
    )
    assert "data-rowhead" not in html, (
        "шапка колонок вернулась в раздел — у карточной сетки её нет"
    )


@pytest.mark.asyncio
async def test_accounts_card_names_each_value(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Каждое значение карточки названо своим ключом на списочной странице.

    Счёт по числу веток статуса, а не проверка «встречается хотя бы раз»:
    ключ, потерянный в ОДНОЙ ветке из трёх, прошёл бы незамеченным — две
    оставшиеся ветки его удержат.
    """
    accounts = await _seed_all_account_branches(db_session)

    html = (await authed_client.get("/accounts")).text

    for key in ACCOUNT_CARD_KEYS:
        assert html.count(_kv_key(key)) == len(accounts), (
            f"ключ {key!r} проставлен не во всех ветках статуса"
        )
    assert "<span data-cell-label>" not in html, (
        "подпись ячейки таблицы вернулась в карточный список — у него нет "
        "шапки колонок, которую она компенсирует"
    )


@pytest.mark.asyncio
async def test_accounts_partial_names_each_value(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Порция бесконечной прокрутки несёт те же ключи, что и первая страница.

    Карточки после первой прокрутки приходят ДРУГИМ файлом; расхождение видно
    только тому, кто долистал.
    """
    accounts = await _seed_all_account_branches(db_session)

    response = await authed_client.get("/accounts/partial?offset=0&limit=30")
    assert response.status_code == 200
    html = response.text

    for key in ACCOUNT_CARD_KEYS:
        assert html.count(_kv_key(key)) == len(accounts), (
            f"ключ {key!r} потерян в порции бесконечной прокрутки"
        )
    assert "<span data-cell-label>" not in html


@pytest.mark.asyncio
async def test_accounts_sync_card_names_each_value(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Блок подмены по опросу статуса несёт ключи во ВСЕХ трёх состояниях.

    Самая опасная из трёх поверхностей: её разметки нет на первичной
    отрисовке, поэтому потеря ключа здесь проявится только после первого
    опроса.
    """
    for status in ("active", "sync_failed", "syncing"):
        account = await _seed_account_with_status(db_session, status)

        response = await authed_client.get(f"/accounts/{account.id}/sync-status")
        assert response.status_code == 200, status
        html = response.text

        assert ACCOUNTS_CARD_MARKER in html, (
            f"{status}: блок подмены остался строкой-таблицей — после первого "
            "опроса карточка в сетке подменилась бы строкой"
        )
        for key in ACCOUNT_CARD_KEYS:
            assert _kv_key(key) in html, (
                f"{status}: ключ {key!r} потерян в блоке подмены"
            )


ACCOUNTS_SUBTITLE = "Per-account воркеры и статус сессий"


@pytest.mark.asyncio
async def test_accounts_page_carries_the_subtitle_from_the_layout(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Подзаголовок раздела приезжает ИЗ ШАБЛОНА страницы, а не из обработчика.

    Слово взято из макета (unpacked.html:1486). Гнездо подзаголовка в шелле уже
    существует и уже используется пятью страницами — заводить нечего,
    переопределяется существующий блок page_subtitle.

    Второе утверждение обязательно: контракт «страница → шелл» на то и заведён,
    чтобы ни один из обработчиков раздела ради подзаголовка не правился.
    Подзаголовок, уехавший в обработчик, работал бы точно так же — и увёл бы за
    собой следующий, а за ним заголовок и действия.
    """
    await _seed_account(db_session, type_="max")

    html = (await authed_client.get("/accounts")).text

    assert f'<p class="head-subtitle">{ACCOUNTS_SUBTITLE}</p>' in html, (
        "подзаголовок раздела не приехал в гнездо шелла"
    )

    page = (TEMPLATES_DIR / "accounts/list.html").read_text(encoding="utf-8")
    assert "{% block page_subtitle %}" in page, (
        "подзаголовок пришёл не переопределением блока шелла"
    )
    handler = (TEMPLATES_DIR.parent / "pages" / "accounts.py").read_text(
        encoding="utf-8"
    )
    assert ACCOUNTS_SUBTITLE not in handler, (
        "подзаголовок раздела уехал в обработчик — контракт «страница → шелл» "
        "заведён ровно ради того, чтобы обработчики о нём не знали"
    )


@pytest.mark.asyncio
async def test_accounts_sentinel_rides_inside_the_grid(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Сентинел прокрутки — ПОСЛЕДНИЙ элемент ВНУТРИ контейнера сетки.

    Снаружи контейнера он не подтянет следующую порцию в сетку, а без растяжки
    на всю строку встанет очередной колонкой рядом с последней карточкой, и
    подпись «Загрузка...» прочтётся как ещё один аккаунт.
    """
    for _ in range(31):
        await _seed_account(db_session, type_="max")

    html = (await authed_client.get("/accounts")).text

    grid_at = html.find(ACCOUNTS_GRID_MARKER)
    assert grid_at != -1, "контейнер карточной сетки аккаунтов исчез"
    grid_open = html.rfind("<div", 0, grid_at)
    grid = html[grid_open : _element_end(html, grid_open)]

    assert 'hx-trigger="revealed"' in grid, (
        "сентинел бесконечной прокрутки выпал из контейнера сетки"
    )
    assert grid.rindex(ACCOUNTS_CARD_MARKER) < grid.index('hx-trigger="revealed"'), (
        "сентинел стоит не последним: после него в сетке есть карточки"
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
    """Журнал платежей собран на строке-таблице, а не на своей вёрстке.

    ⚠️ ПОСЕВ СМЕНИЛСЯ ВМЕСТЕ С ЖУРНАЛОМ: история операций по балансу сообщений
    снята планом 05.1-05, и единственные табличные данные раздела — платежи.
    """
    await _seed_payment(db_session)

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
    await _seed_payment(db_session)

    html = (await authed_client.get("/billing")).text
    for marker in TABLE_MARKERS:
        assert marker not in html, marker


@pytest.mark.asyncio
async def test_billing_no_utility_classes(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _seed_payment(db_session)

    html = (await authed_client.get("/billing")).text
    for marker in UTILITY_MARKERS:
        assert marker not in html, marker


# ⚠️ `test_billing_renders_transaction_data` СНЯТ ВМЕСТЕ С ЖУРНАЛОМ ОПЕРАЦИЙ ПО
# БАЛАНСУ СООБЩЕНИЙ (D-D). Он охранял границу «строка журнала отрисовывает
# настоящие данные, а не пустоту», и граница НЕ потеряна: её держит
# `test_billing_renders_payment_data` ниже — на журнале, который остался.


@pytest.mark.asyncio
async def test_billing_shows_the_access_date_from_the_live_shell(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Раздел подписки показывает СРОК ДОСТУПА пользователя, а не имя тарифа.

    ⚠️ УТВЕРЖДЕНИЕ ПЕРЕЦЕЛЕНО ПЛАНОМ 05.1-04, А НЕ УДАЛЕНО. Оно охраняет ту же
    границу — «величина приходит из живого контекста шелла, а не из константы в
    разметке», — и сменило предмет вместе с моделью: имён тарифов больше нет
    (D-F), доступ стоит одно число, и единственная величина, которая у человека
    своя, — дата окончания. Подписка с другой датой обязана изменить выдачу.
    """
    expires_at = await _move_access_expiry(db_session, timedelta(days=30))
    user = await _user(db_session)

    from app.pages.common import format_datetime_for_user

    html = (await authed_client.get("/billing")).text
    # Сверяется ТЕЛО СТРАНИЦЫ, а не вся выдача: ту же дату печатает виджет
    # сайдбара, и утверждение по целому документу проходило бы и при
    # неотрисованной панели раздела — то есть проверяло бы чужую поверхность.
    body = html.split("<div data-body>", 1)[-1]
    assert format_datetime_for_user(expires_at, user) in body, (
        "срок доступа пользователя в теле раздела не отрисован"
    )


# --- План 05-05: паршалы раздела подписки ------------------------------------
#
# ⚠️ ПАРШАЛОВ ОСТАЛСЯ ОДИН ИЗ ТРЁХ (план 05.1-05). Карточка тарифа и метр оси
# удалены вместе с предметом: тарифов Free/Basic/Pro нет (D-F), а четыре оси
# потребления были счётом, ради снятия которого фаза и существует. Их проверки
# сняты здесь же — тест удалённого файла краснеет на чтении с диска и говорит
# не о том, о чём написан.
#
# Паршал живёт в billing/includes/, а НЕ в components/: он специфичен для
# раздела и в других не переиспользуется, а инвентаризация общей библиотеки
# держит жёсткое число файлов.
#
# Проверки идут ПРЯМЫМ рендером макроса, а не по странице: макрос, потерявший
# явный параметр, отрисуется пустотой, а страница всё равно вернёт 200
# (приём tests/test_templates/test_components.py).

BILLING_PARTIALS = (("billing/includes/payment_row.html", "payment_row"),)

# Разделитель разрядов и отбивка перед знаком рубля — НЕРАЗРЫВНЫЕ пробелы:
# обычный пробел переносит «1» и «490» на разные строки узкой карточки.
# Ожидания выписаны escape-последовательностью: невидимый символ в литерале
# теста читается как обычный пробел и «чинится» первым же редактором.
NBSP = "\u00a0"
BASIC_PRICE = f"1{NBSP}490{NBSP}₽"
PRO_PRICE = f"4{NBSP}900{NBSP}₽"

# ⚠️ ТРИ ЗАПИСИ ТАРИФА СНЯТЫ ВМЕСТЕ С ИХ ЕДИНСТВЕННЫМ ПОТРЕБИТЕЛЕМ — прямым
# рендером карточки тарифа. Суммы выше остались: они проверяют ГЛОБАЛ
# форматирования, а он живёт и после снятия прейскуранта — его зовут и цена
# доступа, и каждая строка платежа.


def _billing_macro(path: str, name: str):
    return getattr(templates.env.get_template(path).module, name)


def test_billing_amount_format_is_a_display_concern_only():
    """Глобал форматирования суммы добавляет разряды и знак рубля.

    Машинная строка ЮKassa («1490.00») остаётся в конфиге и в amount.value:
    строка с разделителем разрядов — отказ платёжного API в проде, который не
    поймает ни один мок. Форматирование живёт ТОЛЬКО на стороне показа.
    """
    format_amount = templates.env.globals["format_amount"]

    assert format_amount("1490.00") == BASIC_PRICE
    assert format_amount("4900.00") == PRO_PRICE
    # Нулевые копейки не показываются: «0,00 ₽» — шум, а не точность.
    assert format_amount("0.00") == f"0{NBSP}₽"
    assert format_amount("149.50") == f"149,50{NBSP}₽"
    assert format_amount(None) == ""


def test_billing_partials_are_macros_with_an_import_line():
    """Каждый паршал — МАКРОС и называет свою строку импорта комментарием."""
    for rel, macro_name in BILLING_PARTIALS:
        source = (TEMPLATES_DIR / rel).read_text(encoding="utf-8")
        assert "{% macro " in source, f"{rel}: паршал не макрос"
        assert rel in source, f"{rel}: строки импорта в комментарии нет"
        assert _billing_macro(rel, macro_name), rel


def test_billing_component_library_did_not_grow():
    """Паршалы раздела не уехали в общую библиотеку компонентов."""
    # 14, а не 13: четырнадцатый файл — filter_chips.html, переехавший из
    # history/includes/ планом 06-03, когда потребителей чипсов стало трое
    # (история, «Пользователи» и «Логи» админки). Число пинуется в этом файле
    # ДВАЖДЫ — здесь и в test_template_inventory, — и обе константы подняты
    # тем же коммитом, что и переезд: правка задним числом на время отключила
    # бы проверку, которая ловит молчаливое пополнение библиотеки.
    #
    # 15, а не 14: пятнадцатый файл — thumb.html, заведённый issue #40. Мест
    # показа вложения пять, правило у них одно (спросить миниатюру, оставить
    # полноразмерный адрес запасным), и собранное на месте пятое место
    # унаследовало бы из этого правила ровно ничего. Обе константы подняты ТЕМ
    # ЖЕ коммитом, что и файл, — по причине, записанной абзацем выше.
    components = sorted((TEMPLATES_DIR / "components").glob("*.html"))
    assert len(components) == 15, [p.name for p in components]

    partials = {p.name for p in (TEMPLATES_DIR / "billing" / "includes").glob("*.html")}
    assert partials == {"payment_row.html"}, (
        "паршалов раздела не один: карточка тарифа и метр оси удалены планом "
        "05.1-05 вместе с предметом"
    )


# ⚠️ ШЕСТЬ ТЕСТОВ ПРЯМОГО РЕНДЕРА СНЯТЫ ВМЕСТЕ С ДВУМЯ УДАЛЁННЫМИ МАКРОСАМИ:
# два про метр оси (безлимит и превышение) и четыре про карточку тарифа
# (текущий план, безлимитный лимит, бесплатный тариф без формы, выключенные
# платежи). Их предмет — оси потребления и прейскурант — снят решениями D-D и
# D-F; тест удалённого шаблона краснеет на чтении с диска и говорит не о том, о
# чём написан. Две границы, которые они охраняли и которые ПЕРЕЖИЛИ снос,
# закреплены в другом месте: «выключенные платежи гасят кнопку, а не витрину» —
# в test_billing_section.py, «сумма форматируется только на стороне показа» —
# тестом глобала выше.


def test_billing_payment_row_is_built_on_row_primitives():
    """Строка платежа — примитивы строки и подпись колонки внутри ячейки."""
    source = (TEMPLATES_DIR / "billing" / "includes" / "payment_row.html").read_text(
        encoding="utf-8"
    )

    assert "data-cell-label" in source, "подпись колонки не едет вместе со значением"
    for marker in TABLE_MARKERS:
        assert marker not in source, marker


# --- План 05-05, задача 3: снос, честная подпись, адаптивные регрессии -------
#
# ⚠️ НАЗВАННАЯ ГРАНИЦА ПРОВЕРКИ. Браузерных и e2e-тестов в проекте нет
# (блокер STATE.md), поэтому проверки ниже закрепляют РАЗМЕТКУ и ПРАВИЛО CSS, а
# не отрисовку. Зелёный прогон означает, что сетка объявлена складывающейся и
# что подписи колонок едут вместе со значениями, — но НЕ означает, что на
# настоящей мобильной ширине ничего не уехало в горизонтальную прокрутку.
# Соответствующая истина плана помечена требующей человеческого подтверждения:
# при отсутствии явного доказательства верификатор обязан позвать человека, а
# не засчитать молча.

APP_DIR = Path(__file__).resolve().parents[2] / "app"
COMMON_PY = APP_DIR / "pages" / "common.py"
REMOVED_PLANS_TEMPLATE = TEMPLATES_DIR / "billing" / "plans.html"


def test_the_unwired_plans_template_is_gone():
    """Неподключённый шаблон раздела снесён (D-19).

    Файл не рендерился НИ ОДНИМ маршрутом и ссылался на переменные, которых
    нет ни в одном контексте; его поведенческой проверки не существовало —
    была только проверка исходника, удалённая вместе с ним. Содержимое
    перенесено в живые паршалы раздела. Тот же ход, что снос шести
    недостижимых шаблонов в Фазе 1 и мёртвого репозитория групп в Фазе 3.
    """
    assert not REMOVED_PLANS_TEMPLATE.exists(), "неподключённый шаблон на месте"

    # Ссылок на снесённый файл в исходниках приложения не осталось: прозой
    # указывать на несуществующий путь — та же ложь, что мёртвый импорт.
    needle = REMOVED_PLANS_TEMPLATE.name
    offenders = [
        str(path.relative_to(APP_DIR))
        for path in sorted(APP_DIR.rglob("*"))
        if path.suffix in {".py", ".html"}
        and needle in path.read_text(encoding="utf-8")
    ]
    assert not offenders, f"ссылки на снесённый шаблон остались: {offenders}"


BASE_HTML = TEMPLATES_DIR / "base.html"


def _markup_without_comments(path: Path) -> str:
    """Разметка без объяснительных комментариев Jinja.

    Запреты этого блока адресованы КОПИРАЙТУ и КОДУ, а не прозе, которая
    объясняет, почему запрет существует. Абзац, называющий отвергнутую
    формулировку («осталось 0 дней» читается как «уже кончилось»), обязан
    остаться в файле: без него следующий читатель «приведёт ветку в
    соответствие» с соседней. Проверка по сырому тексту краснела бы от
    собственного объяснения — тот же приём, которым план 05.1-01 разрешил
    проверку отсутствия ветки разбором по синтаксическому дереву.
    """
    return re.sub(r"\{#.*?#\}", "", path.read_text(encoding="utf-8"), flags=re.S)


def _css_without_comments() -> str:
    """Таблица стилей без комментариев — по тому же основанию."""
    return re.sub(r"/\*.*?\*/", "", APP_CSS.read_text(encoding="utf-8"), flags=re.S)


@pytest.mark.asyncio
async def test_the_sidebar_widget_names_the_access_it_shows(
    authed_client: AsyncClient,
):
    """Виджет сайдбара подписан ТЕМ, ЧТО ПОКАЗЫВАЕТ (T-05-29, D-22).

    ⚠️ УТВЕРЖДЕНИЕ ПЕРЕЦЕЛЕНО ПЛАНОМ 05.1-04, А НЕ УДАЛЕНО. Правило прежнее,
    предмет у него сменился: виджет перестал показывать баланс сообщений и
    показывает СРОК ДОСТУПА — ту величину, по которой `require_access` впускает
    или отказывает. Подпись обязана следовать за предметом, иначе она врёт
    ровно так же, как врала подпись тарифом над балансом.

    Переименование ключа и классов (`quota` → `access`) здесь тоже не
    косметика: сменилась ФОРМА значения — `{used, limit, percent, plan}` →
    `{open, expires_at, days_left}`. Прецедент D-22 («менялся текст, а не
    контракт») к смене формы не применяется.
    """
    source = BASE_HTML.read_text(encoding="utf-8")

    assert "Тариф {{" not in source, "виджет по-прежнему подписан тарифом"
    assert "Баланс сообщений" not in source, (
        "виджет подписан балансом сообщений, которого он больше не показывает"
    )
    assert "quota" not in source, "имя снятого ключа осталось в разметке шелла"
    assert ">Доступ<" in source, "подписи виджета в разметке нет"

    for expression in ("access.get('open'", "access.get('days_left'", "access.get('expires_at'"):
        assert expression in source, expression
    assert 'href="/billing"' in source, "ссылка виджета на раздел исчезла"
    assert "ПОДПИСКА И ОПЛАТА →" in source, "подпись ссылки виджета не перецелена"

    html = (await authed_client.get("/profile")).text
    assert "data-access" in html
    assert "data-quota" not in html
    assert "Доступ" in html


@pytest.mark.asyncio
async def test_the_widget_calls_the_last_day_by_its_name_and_not_zero(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """P-6: последний день доступа называется словами, а не «осталось 0 дней».

    Ветка проверяется РАНЬШЕ ветки счёта дней, и это не оформление. «Осталось
    0 дней» формально верно и читается как «уже кончилось» — то есть человек, у
    которого доступ ещё работает, прочитал бы, что доступ закрыт. Формулировка
    едина с панелью раздела подписки: две разные фразы про один день на двух
    поверхностях — то же расхождение, за которое снят виджет с чужой подписью.
    """
    await _move_access_expiry(db_session, timedelta(hours=5))

    html = (await authed_client.get("/profile")).text

    assert "последний день" in html
    assert "осталось 0" not in html, "напечатан счёт вместо слов последнего дня"
    assert "закрыт" not in html, "живой доступ назван закрытым"


@pytest.mark.asyncio
async def test_the_widget_counts_the_days_inside_the_warning_threshold(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Внутри порога печатаются ДНИ, и форма слова приезжает склонением (P-1).

    Порог — именованная константа `ACCESS_SOON_DAYS`, приезжающая в разметку
    глобалом: выписанная семёрка была бы второй копией правила и разошлась бы с
    первой молча.
    """
    await _move_access_expiry(db_session, timedelta(days=3))

    html = (await authed_client.get("/profile")).text

    assert "осталось 2 дня" in html, "счёт дней внутри порога не напечатан"


@pytest.mark.asyncio
async def test_the_widget_prints_the_date_beyond_the_warning_threshold(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Вне порога печатается ДАТА — и только глобалом форматирования (P-2)."""
    expires_at = await _move_access_expiry(db_session, timedelta(days=30))
    user = await _user(db_session)

    html = (await authed_client.get("/profile")).text

    from app.pages.common import format_datetime_for_user

    assert f"до {format_datetime_for_user(expires_at, user)}" in html
    assert "осталось" not in html, "вне порога напечатан счёт дней"


@pytest.mark.asyncio
async def test_the_widget_says_the_access_is_closed_when_it_is(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Закрытый доступ назван бейджем `закрыт` — тон danger, а не warning.

    Тон изменён относительно контракта фазы 5 намеренно (A-9): там истечение
    НИЧЕГО не отключало, теперь отключает. Предупреждающий цвет остался бы от
    утверждения, переставшего быть правдой.
    """
    await _move_access_expiry(db_session, timedelta(days=-1))

    html = (await authed_client.get("/profile")).text

    assert "закрыт" in html
    assert "осталось" not in html
    assert "последний день" not in html


@pytest.mark.asyncio
async def test_the_widget_is_not_drawn_at_all_without_the_access_key(
    authed_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    """Нет ключа `access` — нет виджета. Умолчание «закрыт» ЗАПРЕЩЕНО.

    Ложное «доступ закрыт», выведенное из пустого словаря, — худший из
    возможных дефектов этого виджета: он сказал бы человеку, что работа
    остановлена, на каждой из 26 страниц, на которых она работает. Отсутствие
    виджета честнее неправды.
    """
    import app.pages as app_pages

    real = app_pages.get_shell_context

    async def without_access(db, user):
        context = await real(db, user)
        context.pop("access", None)
        return context

    monkeypatch.setattr("app.pages.get_shell_context", without_access)

    response = await authed_client.get("/profile")
    html = response.text

    assert response.status_code == 200, "страница упала вместо того, чтобы не рисовать виджет"
    assert "data-access" not in html, "виджет нарисован без данных"
    assert ">Доступ<" not in html
    assert "badge--danger" not in html, "пустой словарь выведен как «доступ закрыт»"
    # Сайдбар при этом цел: исчезает ВИДЖЕТ, а не блок пользователя под ним.
    assert "data-user" in html


def test_the_bottom_pinning_rides_with_the_widget_selector():
    """`margin-top: auto` объявлен на виджете, а не на блоке пользователя (D-J).

    Сайдбар — колонка flex, и к низу её прижимает ИМЕННО виджет, утаскивая за
    собой блок пользователя. Свойство обязано было уехать вместе с
    переименованием селектора: не уехав, оно оторвало бы блок пользователя от
    низа сайдбара на всех 26 страницах — правкой, выглядящей безобидным
    переименованием.
    """
    css = _css_without_comments()

    widget = re.search(r"\[data-access\]\s*\{([^}]*)\}", css)
    assert widget, "правила [data-access] в app.css нет"
    assert "margin-top: auto" in widget.group(1), (
        "прижатие к низу сайдбара не уехало вместе с переименованием виджета"
    )

    assert css.count("margin-top: auto;") == 1, (
        "прижатие к низу объявлено дважды — два элемента спорят за низ сайдбара"
    )


def test_the_widget_and_the_user_block_are_hidden_by_one_mobile_rule():
    """Мобильной поверхности у виджета нет и не появляется (A-4).

    Правило сохранено дословно, сменилось только имя атрибута. Ту же величину
    на телефоне несёт панель раздела подписки.
    """
    css = APP_CSS.read_text(encoding="utf-8")

    mobile = re.search(r"@media \(max-width: 860px\) \{(.*?)\n\}", css, re.S)
    assert mobile, "мобильного блока 860px в app.css нет"
    assert "[data-access], [data-user] { display: none !important; }" in mobile.group(1), (
        "виджет доступа и блок пользователя скрываются не одним правилом"
    )


def test_the_value_of_the_widget_wraps_instead_of_leaving_the_widget():
    """Ни подпись, ни значение не объявлены nowrap и flex:none (long-text E4).

    Под значение остаётся 147px, самое длинное — «до 2026-08-20 14:30» ≈138px.
    Запас узкий, и безопасным его делает именно отсутствие этих двух
    объявлений: при нехватке ширины значение переносится ВНУТРИ виджета, а не
    вылезает за его границу. Ровно этим строка long-text отличается от M1,
    требующего действия.
    """
    css = APP_CSS.read_text(encoding="utf-8")

    for selector in (r"\.access-plan", r"\.access-value"):
        rule = re.search(selector + r"\s*\{([^}]*)\}", css)
        assert rule, f"правила {selector} в app.css нет"
        body = rule.group(1)
        assert "nowrap" not in body, f"{selector}: значение перестало переноситься"
        assert "flex: none" not in body, f"{selector}: значение перестало сжиматься"


def test_the_reduced_motion_rule_names_only_living_classes():
    """Правило, адресованное несуществующему классу, — мусор.

    Вычеркнуты ДВА имени: заливка шкалы — вместе со шкалой (план 05.1-04), точка
    строки перечня воркеров — вместе с карточкой воркеров дашборда (задача
    260826-6jq). Остальные три имени остались нетронутыми. Следующий читатель
    принял бы мёртвое имя за живое.
    """
    css = APP_CSS.read_text(encoding="utf-8")

    rule = re.search(
        r"@media \(prefers-reduced-motion: reduce\) \{([^}]*)\}", css
    )
    assert rule, "правила prefers-reduced-motion в app.css нет"
    selectors = [s.strip() for s in rule.group(1).split("{")[0].split(",")]

    assert "quota-fill" not in rule.group(1)
    assert "worker-row" not in rule.group(1)
    assert len(selectors) == 3, f"имён в перечне не три: {selectors}"
    for name in (
        ".brand-mark::after",
        ".session-dot.is-online",
        ".animate-fade-in",
    ):
        assert name in selectors, f"живое имя {name} вычеркнуто заодно"


def test_the_dashboard_worker_list_left_no_css_behind():
    """Правил снятого перечня воркеров в стилях не осталось.

    Стили без разметки — тот же мусор, что и правило, адресованное
    несуществующему классу: следующий читатель примет их за живые и вернёт под
    них блок. Разбирается текст БЕЗ комментариев — объяснение снятия, оставленное
    комментарием в `app.css`, этот тест краснить не должно.

    Блок пилюли состояния сессий (`.session-pill` / `.session-dot`) проверяется
    рядом: он живёт в ШАПКЕ ШЕЛЛА на всех 26 маршрутах, к дашборду не привязан и
    снесённым заодно быть не должен.
    """
    css = _css_without_comments()

    for selector in (".worker-list", ".worker-row"):
        assert selector not in css, (
            f"в app.css остались правила снятого перечня воркеров: {selector}"
        )
    for selector in (".session-pill", ".session-dot"):
        assert selector in css, (
            f"вместе с перечнем снесён живой блок пилюли шапки: {selector}"
        )


def test_the_activity_chart_template_is_gone():
    """Шаблона карточки нет на диске, и его разметки нет ни в одном шаблоне дашборда.

    Недостижимых шаблонов в проекте не оставляют — тем же приёмом выведены
    `dashboard/includes/recent_send_card.html` (план 04-05) и
    `dashboard/includes/worker_row.html` (задача 260826-6jq).

    Каждый файл разбирается БЕЗ комментариев Jinja: объяснение снятия,
    оставленное в `dashboard.html`, разметкой не является и этот тест краснить
    не должно.

    Живой сосед по каталогу проверяется тем же тестом: запрет прошёл бы и на
    вычищенном каталоге, а из четырёх файлов снят ровно один.
    """
    dashboard_dir = TEMPLATES_DIR / "dashboard"

    assert not (dashboard_dir / "includes" / "activity_chart.html").exists(), (
        "шаблон карточки недельной активности вернулся на диск"
    )
    assert (dashboard_dir / "includes" / "feed_row.html").exists(), (
        "вместе с карточкой снесён живой сосед по каталогу — строка ленты"
    )

    owners = {}
    for path in [*dashboard_dir.rglob("*.html"), TEMPLATES_DIR / "dashboard.html"]:
        source = _markup_without_comments(path)
        hits = sorted(m for m in ACTIVITY_CHART_MARKERS if m in source)
        if hits:
            owners[path.relative_to(TEMPLATES_DIR).as_posix()] = hits

    assert not owners, f"разметка недельной активности вернулась в шаблоны: {owners}"


def test_the_dashboard_activity_chart_left_no_css_behind():
    """Правил снятой карточки недельной активности в стилях не осталось.

    Стили без разметки — тот же мусор, что и правило, адресованное
    несуществующему классу: следующий читатель примет их за живые и вернёт под
    них блок. Разбирается текст БЕЗ комментариев — объяснение снятия,
    оставленное комментарием в `app.css`, этот тест краснить не должно.

    Два запрета переехали сюда из снятого
    `test_activity_chart_columns_are_fractional_not_fixed`: правила прежней
    сетки 7×24 были сняты ещё при замене её столбцами, и снятые вместе со своим
    тестом эти запреты разрешили бы вернуть сетку под видом графика — ровно то,
    ради снятия чего их и писали.

    Живые правила проверяются рядом: пара дашборда и строка ленты стоят в тех
    же полутора сотнях строк стилей и снесёнными заодно быть не должны.
    """
    css = _css_without_comments()

    for marker in ACTIVITY_CHART_MARKERS:
        assert marker not in css, (
            f"в app.css остались правила снятой карточки активности: {marker!r}"
        )
    assert "[data-heatscroll]" not in css, "остался контейнер прокрутки снятой сетки"
    assert "[data-heatcell]" not in css, "остались правила снятой сетки"

    for selector in ("[data-dashpair]", "[data-feedrow]"):
        assert selector in css, (
            f"вместе с карточкой снесён живой блок правил дашборда: {selector}"
        )


def test_the_widget_carries_no_progress_bar_at_all():
    """Прохибиция P-4: шкалы в виджете нет ни в каком виде.

    Шкала «сколько месяца прошло» вернула бы на все 26 страниц счёт, ради
    снятия которого фаза существует.
    """
    source = _markup_without_comments(BASE_HTML)
    css = _css_without_comments()

    for marker in ("progress", "track", "fill", "percent"):
        assert marker not in source, f"в разметке шелла остался признак шкалы: {marker}"
    for marker in (".access-track", ".access-fill"):
        assert marker not in css, f"в app.css заведена шкала виджета: {marker}"


def test_the_warning_threshold_is_named_and_not_written_out_in_the_copy():
    """Ни порога, ни формы слова разметка не выписывает литералом.

    Числа не копируются в копирайт: порог живёт в одной константе
    (`ACCESS_SOON_DAYS`) и приезжает подстановкой, форма слова — склонением.
    «Осталось 1 дней» — дефект контракта, а не опечатка.
    """
    source = _markup_without_comments(BASE_HTML)

    assert "access_soon_days" in source, "порог выписан мимо константы"
    assert "plural_ru(access.get('days_left'), 'день', 'дня', 'дней')" in source, (
        "форма слова выписана вместо склонения"
    )
    assert source.count("дней") == 1, (
        "литерал «дней» встречается вне вызова склонения"
    )
    assert not re.search(r"days_left'\)\s*<=\s*\d", source), (
        "порог сравнивается с числом, выписанным в разметке"
    )


def test_the_shell_did_not_gain_a_query_for_the_widget():
    """Виджет стоит НОЛЬ дополнительных запросов, и их стало на два меньше.

    ⚠️ УТВЕРЖДЕНИЕ ИНВЕРТИРОВАНО ПЛАНОМ 05.1-04, А НЕ УДАЛЕНО. Гейт охраняет ту
    же границу — «на рендере каждой из 26 страниц не появляется запроса ради
    виджета», — изменилось направление: пока виджет показывал баланс сообщений,
    модели журнала в шелле БЫЛИ обязаны присутствовать; теперь он показывает
    срок доступа, который шелл уже читает строкой подписки, и присутствие
    журнала означало бы два чтения, за которые больше никто не платит.

    Перенаправить виджет на тарифную ось отклонено и остаётся отклонённым: это
    добавило бы запрос по журналу отправок во ВСЕ 26 рендеров ради метрики, у
    которой есть свой полноценный экран.
    """
    source = COMMON_PY.read_text(encoding="utf-8")

    for gone in ("BalanceTransaction", "MessageBalance"):
        assert gone not in source, (
            f"шелл по-прежнему читает {gone} — это чтение журнала сообщений на "
            "каждом из 26 страничных маршрутов"
        )
    for forbidden in ("plan_axes(", "sends_in_current_month"):
        assert forbidden not in source, (
            f"в контекст шелла приехал {forbidden} — это запрос на каждый рендер"
        )


@pytest.mark.asyncio
async def test_billing_payment_labels_ride_with_the_values(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Подписи колонок истории платежей едут вместе со значениями.

    На 860px шапка колонок скрывается, и сумма без подписи становится числом
    без смысла. Дата подписи не получает намеренно — форматированная дата
    самоописательна.
    """
    await _seed_payment(db_session)

    html = (await authed_client.get("/billing")).text

    for label in ("Назначение", "Сумма", "Статус"):
        assert f"<span data-cell-label>{label}</span>" in html, label


@pytest.mark.asyncio
async def test_billing_renders_payment_data(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Строка платежа отрисовывает РЕАЛЬНЫЕ данные, а не пустоту.

    ⚠️ ГРАНИЦА УНАСЛЕДОВАНА У СНЯТОГО `test_billing_renders_transaction_data`.
    Макрос, потерявший явный параметр, отрисуется ПУСТОТОЙ при статусе 200, и
    проверка «раздел отдал 200» этого не увидит. Журнал сменился — граница нет.
    """
    await _seed_payment(db_session)

    html = (await authed_client.get("/billing")).text

    assert BASIC_PRICE in html, "сумма платежа не отрисована подписью"
    assert "проведён" in html, "статус платежа не расшифрован"
    assert "2026-05-20" in html, "дата платежа не отрисована"
    assert "1490.00" not in html, "машинная строка суммы вышла на экран"


@pytest.mark.asyncio
async def test_billing_has_no_event_handler_on_a_button(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """В разметке раздела ноль обработчиков события на кнопке (D-20).

    Раздел был последним местом проекта, где действие недоступно без
    JavaScript. Проверка идёт по ОТРЕНДЕРЕННОЙ выдаче: обработчик мог бы
    приехать из паршала.
    """
    await _seed_payment(db_session)

    html = (await authed_client.get("/billing")).text

    for marker in ("onclick", "@click", "x-on:click", "onsubmit"):
        assert marker not in html, marker


def test_the_plan_card_rules_are_gone_and_the_dashboard_tiles_survived():
    """Разрез стилей: блок карточек тарифов вырезан, СОСЕДИ целы.

    ⚠️ ТЕСТ ИНВЕРТИРОВАН, А НЕ УДАЛЁН. Он утверждал, что сетка карточек
    объявлена складывающейся и не переопределяет плитки дашборда. Карточек нет
    (D-F), и предметом стала вторая половина того же утверждения — САМАЯ ДОРОГАЯ
    ОШИБКА ФАЗЫ ВЫЧИТАНИЯ: удалить лишнее. Правила плиток лежали ВПЛОТНУЮ к
    вырезанному блоку, их держат дашборд Фазы 4 и карточка пользователя в
    админке, и уйти вместе с соседями они не имели права.
    """
    css = APP_CSS.read_text(encoding="utf-8")

    for gone in ("[data-plans]", "[data-plan-name]", "[data-plan-limits]"):
        assert gone not in css, f"правило {gone} пережило снос карточек тарифов"
    assert css.count("[data-metrics] {") == 1, "правило плиток объявлено дважды"
    assert "minmax(210px, 1fr)" in css, "минимум плиток дашборда изменён"
    for kept in ("[data-metric-line] {", "[data-metric-value] {"):
        assert kept in css, f"правило {kept} удалено вместе с соседями"


# --- План 05-09: нажимаемая высота кнопок оплаты (M3 / C1) ------------------
#
# ⚠️ ФОРМА ОПЛАТЫ НА РАЗДЕЛЕ ОСТАЛАСЬ ОДНА ВМЕСТО ТРЁХ (план 05.1-05), И ОБЕ
# РЕГРЕССИИ ПЕРЕНАЦЕЛЕНЫ НА НЕЁ, А НЕ УДАЛЕНЫ ВМЕСТЕ С ДВУМЯ ИСЧЕЗНУВШИМИ.
# Атрибут `data-plan-cta` обязан был переехать на единственную оставшуюся форму:
# потерять его при переписывании — значит молча вернуть кнопку к 33px и заново
# открыть тот самый пункт UAT фазы 5, который эта фаза объявляет снятым.

# Шаблоны с формами оплаты и число форм в каждом. Правило без атрибута так же
# бесполезно, как атрибут без правила, и до плана 05-09 в разделе была ровно
# вторая половина.
PLAN_CTA_TEMPLATES = {
    "billing/balance.html": 1,
}

# Собственный порог проекта — токен `touch` из 05-UI-SPEC.md `## Spacing Scale`.
PLAN_CTA_MIN_HEIGHT_PX = 44


def test_billing_payment_buttons_declare_the_project_touch_height():
    """Кнопка оплаты объявлена не ниже собственного порога проекта — 44px.

    ⚠️ Проверяется ОБЪЯВЛЕНИЕ правила, а не отрисовка: браузера в суите нет.

    Арифметика унаследованной кнопки выписана здесь намеренно, чтобы будущая
    правка `--fs-md` или padding не прошла молча: `.btn` вычисляется в
    13px (`--fs-md` при `line-height:1`) + 9px×2 padding + 1px×2 border = 33px.
    Эти 33px ПРОХОДЯТ порог WCAG 2.5.8 AA (24px) и не проходят только
    собственный порог проекта 44px — формулировка не смягчается и не
    ужесточается.

    Правило адресовано `[data-plan-cta] .btn`, а не голому `.btn`: общая кнопка
    стоит на 26 страницах проекта, и её высота этой правкой не меняется.
    """
    css = APP_CSS.read_text(encoding="utf-8")

    rule = re.search(r"\[data-plan-cta\]\s+\.btn\s*\{([^}]*)\}", css)
    assert rule, "правила [data-plan-cta] .btn в app.css нет"

    declared = re.search(r"min-height:\s*(\d+)px", rule.group(1))
    assert declared, "у правила кнопки оплаты нет объявления min-height"
    assert int(declared.group(1)) >= PLAN_CTA_MIN_HEIGHT_PX, (
        f"высота кнопки оплаты ниже порога проекта {PLAN_CTA_MIN_HEIGHT_PX}px"
    )

    # Высота ОСТАЛЬНЫХ 26 страниц не тронута: у голого .btn min-height нет.
    base = re.search(r"(?<!\])\n\.btn\s*\{([^}]*)\}", css)
    assert base, "блок .btn в app.css не найден"
    assert "min-height" not in base.group(1), (
        "min-height уехал в общую кнопку — высота кнопок всех 26 страниц проекта "
        "изменилась вместе с разделом тарифов"
    )


def test_billing_payment_forms_carry_the_touch_attribute():
    """Атрибут `data-plan-cta` стоит на ЕДИНСТВЕННОЙ форме оплаты раздела.

    Правило CSS без атрибута бесполезно ровно так же, как атрибут без правила.
    Счёт по каждому шаблону, а не «встречается хотя бы раз»: лишний атрибут
    означал бы вторую форму оплаты на экране, где её быть не должно, а
    потерянный — кнопку на прежних 33px при статусе 200.
    """
    for template, expected in PLAN_CTA_TEMPLATES.items():
        markup = (TEMPLATES_DIR / template).read_text(encoding="utf-8")
        assert markup.count("data-plan-cta") == expected, (
            f"{template}: форм оплаты с атрибутом data-plan-cta не {expected}"
        )


@pytest.mark.asyncio
async def test_the_touch_attribute_reaches_the_rendered_form(
    authed_client: AsyncClient,
):
    """Вторая половина той же регрессии — по ОТРЕНДЕРЕННОЙ выдаче.

    Проверка по исходнику шаблона зеленеет и тогда, когда форма стоит в ветке,
    которая не срабатывает никогда. Здесь утверждается, что атрибут доехал до
    экрана в штатном состоянии — и что форма на экране ровно одна.
    """
    html = (await authed_client.get("/billing")).text

    assert html.count("data-plan-cta") == 1, (
        "форм оплаты на отрисованном экране не одна"
    )


# test_billing_plans_template_is_migrated УДАЛЁН планом 05-05 вместе с файлом,
# который он читал с диска (D-19). Это не обход поломки, а завершение работы
# теста: проверка исходника существовала ровно потому, что у неподключённого
# шаблона не было поведенческой проверки. Отсутствие самого файла закреплено
# test_the_unwired_plans_template_is_gone.


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
    # Четыре новых подраздела дописаны планом 06-01 вместе с их маршрутами;
    # адрес справочника групп тем же планом убран вместе с его экранами (D-05),
    # и посев справочника здесь стал беспредметным.
    for url in (
        "/admin",
        "/admin/users",
        "/admin/workers",
        "/admin/queue",
        "/admin/logs",
        "/admin/payments",
    ):
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
    for url in ("/admin", "/admin/users"):
        response = await authed_client.get(url, follow_redirects=False)
        assert response.status_code != 200, url
        assert "Администрирование" not in response.text, url
        assert "data-rowhead" not in response.text, url


# ТРИ ТЕСТА СПРАВОЧНИКА ГРУПП УДАЛЕНЫ ПЛАНОМ 06-01 ВМЕСТЕ С ПРЕДМЕТОМ (D-05), А
# НЕ ПЕРЕНАЦЕЛЕНЫ НА ДРУГОЙ ЭКРАН. Они утверждали про строку справочника: что
# она собрана примитивом, что рисует реальные данные и что экранирует пришедшее
# из мессенджера название. Экрана нет — утверждать не о чем, а тест, потерявший
# предмет и перенацеленный, перестаёт утверждать то, ради чего был написан.
# Вклад в проверки не потерян молча: экранирование внешних строк закрыто теми же
# проверками на остальных поверхностях, а отсутствие снесённого адреса
# закреплено test_groups_info_gone_from_templates_and_routes в test_admin_panel.py.


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
    #
    # ⚠️ ПОПОЛНЕНИЕ И ТУМБЛЕР БЕЗЛИМИТА УШЛИ ИЗ ПЕРЕЧНЯ ВМЕСТЕ СО СВОИМИ
    # МАРШРУТАМИ, А НЕ ПОТЕРЯЛИСЬ. Валюта сообщений снята из продукта целиком, а
    # ревизия `0020` уронила таблицы под обоими: пополнять нечего и переключать
    # нечего. Проверку, что вход пополнения действительно исчез, держит
    # `tests/test_admin.py::test_the_admin_top_up_route_no_longer_answers`.
    #
    # ⚠️ ВХОД ТУМБЛЕРА ВЕРНУЛСЯ ПЛАНОМ `05.1-09` — уже поверх признака подписки,
    # и перечень ниже дополнен ТЕМ ЖЕ планом, как и предписывал этот абзац.
    # Пополнение НЕ вернулось и не вернётся: валюта сообщений снята из продукта
    # целиком, пополнять нечего. Что тумблер именно ПЕРЕКЛЮЧАЕТ признак, а не
    # просто отвечает, держат тесты `-k free_access` в `tests/test_admin.py`;
    # здесь утверждается только присутствие входа на карточке.
    for action in ("/block", "/delete", "/unlimited"):
        assert f"/admin/users/{user.id}{action}" in html, action


# test_admin_group_info_detail_renders_data УДАЛЁН ПЛАНОМ 06-01 вместе с самой
# карточкой справочника (D-05). Он утверждал, что карточка отрисовывает реальные
# данные; карточки нет — утверждать не о чем.


@pytest.mark.asyncio
async def test_admin_detail_pages_no_utility_classes(
    authed_client: AsyncClient, admin_client: AsyncClient, db_session: AsyncSession
):
    user = await _user(db_session)

    # Адрес карточки справочника вышел из обхода вместе с самой карточкой:
    # детальных страниц админки осталась одна.
    for url in (f"/admin/users/{user.id}",):
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

    for url in (f"/admin/users/{user.id}",):
        response = await authed_client.get(url, follow_redirects=False)
        assert response.status_code != 200, url
        assert user.email not in response.text, url


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


def test_accounts_three_files_declare_same_keys():
    """Список ключей карточки совпадает в трёх файлах ПОСИМВОЛЬНО.

    Проверка та же, что держала раскладку колонок и список колонок до задачи
    260825-of5; сменилось ОБЪЯВЛЕНИЕ, а не утверждение: раздел переведён на
    карточную сетку, колонок у него больше нет, и синхронной величиной стал
    список ключей ACCOUNT_KEYS.

    Три файла рисуют одну и ту же карточку. Разъехавшийся список не роняет
    страницу: карточка после подмены просто назовёт те же числа другими
    словами, и увидит это только тот, кто дождался опроса.
    """
    sources = _accounts_sources()

    declared = {rel: _declaration(src, "ACCOUNT_KEYS") for rel, src in sources.items()}

    missing = sorted(rel for rel, value in declared.items() if value is None)
    assert not missing, f"ACCOUNT_KEYS не объявлен в: {missing}"

    reference_file, reference = next(iter(declared.items()))
    divergent = {rel: v for rel, v in declared.items() if v != reference}
    assert not divergent, (
        f"ACCOUNT_KEYS в {reference_file} объявлен как {reference}, но отстали: "
        + "; ".join(f"{rel} -> {value}" for rel, value in sorted(divergent.items()))
    )

    assert "ACCOUNT_COLS" not in "".join(sources.values()), (
        "раскладка колонок вернулась в раздел — у карточной сетки колонок нет"
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


# Ключ карточки берётся ИНДЕКСОМ из списка ключей. Образец заякорен на разметку
# ключа (class="kv__k"), и якорь делает ту же работу, какую до задачи 260825-of5
# делал отрицательный просмотр назад у образца подписи ячейки: подписи действий
# и подписи макросов (confirm_label=, action_label=, show_label=) ключами
# карточки не являются и по этому якорю не проходят по построению.
KEY_BY_INDEX_RE = re.compile(
    r'<span class="kv__k">\{\{\s*ACCOUNT_KEYS\[(\d+)\]\s*\}\}</span>'
)
# Ключ, вписанный на месте СТРОКОЙ: та же разметка, но без подстановки.
KEY_LITERAL_RE = re.compile(r'<span class="kv__k">(?!\{\{)([^<]*)</span>')


def test_accounts_three_files_key_the_same_values():
    """Ключи карточки в трёх файлах совпадают по составу И ПО ЧИСЛУ вхождений.

    Счёт вхождений, а не множество значений: в каждом файле три ветки статуса, и
    ключ, потерянный в ОДНОЙ из них, множества не меняет — две оставшиеся ветки
    его удержат. Именно так ключ и теряется на практике: правят одну ветку, а
    расходится весь раздел.

    Проверка идёт по ИСХОДНИКАМ трёх файлов, а не по отрендеренной странице, и
    причина та же, по которой так устроена вся сетка Плана 11: у файла подмены
    нет своего адреса в обходе страниц, а расхождение проявляется только в
    момент подмены и только визуально. На широкой ширине потеря ключа не видна
    вовсе — карточка просто становится на строку короче соседних.
    """
    sources = _accounts_sources()

    hardcoded = {
        rel: sorted({m.group(1) for m in KEY_LITERAL_RE.finditer(src)})
        for rel, src in sources.items()
    }
    hardcoded = {rel: values for rel, values in hardcoded.items() if values}
    assert not hardcoded, (
        "ключи вписаны строкой вместо элемента списка ключей — трём файлам "
        f"есть на чём разъехаться: {hardcoded}"
    )

    keys: dict[str, Counter[str]] = {}
    for rel, src in sources.items():
        declared = _declaration(src, "ACCOUNT_KEYS")
        assert declared, f"{rel}: список ключей не объявлен"
        names = ast.literal_eval(declared)
        keys[rel] = Counter(names[int(i)] for i in KEY_BY_INDEX_RE.findall(src))

    reference_file, reference = next(iter(keys.items()))
    assert reference, f"{reference_file}: ключей нет ни одного"

    divergent = {}
    for rel, counted in keys.items():
        if counted == reference:
            continue
        divergent[rel] = sorted(
            f"{name}: {counted.get(name, 0)} вместо {reference.get(name, 0)}"
            for name in set(counted) | set(reference)
            if counted.get(name, 0) != reference.get(name, 0)
        )
    assert not divergent, (
        f"ключи в {reference_file} — {sorted(reference.items())}, но отстали: "
        + "; ".join(f"{rel} -> {diff}" for rel, diff in sorted(divergent.items()))
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

    # Библиотека компонентов Плана 02 на месте целиком (12 макросов + filters),
    # плюс четырнадцатый файл — filter_chips.html, переехавший из
    # history/includes/ планом 06-03 вслед за вторым и третьим потребителями
    # («Пользователи» и «Логи» админки), плюс пятнадцатый — thumb.html из
    # issue #40, единственный способ показать вложение. Второе утверждение о том
    # же числе стоит в test_billing_component_library_did_not_grow; выборка
    # `-k inventory` берёт только ЭТО, поэтому поднимать надо оба — иначе
    # выборка зеленеет, а полный прогон краснеет из теста, названного по
    # чужому разделу.
    components = sorted((TEMPLATES_DIR / "components").glob("*.html"))
    assert len(components) == 15, [p.name for p in components]

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
    """Названия колонок ВСЕХ шапок страницы, а не только первой.

    ⚠️ РАНЬШЕ ЧИТАЛАСЬ ПЕРВАЯ ШАПКА, И ЭТО БЫЛА НЕЗАМЕЧЕННАЯ ДЫРА, А НЕ
    упрощение. Пока у каждой страницы была ровно одна таблица, разница не
    проявлялась; страница с двумя таблицами проверялась бы НАПОЛОВИНУ —
    подписи второй таблицы попадали бы в `labels`, их колонки в `header` не
    попадали бы, и сетка краснела бы на исправной разметке, пряча за этим
    настоящий вопрос: подписана ли вторая таблица вовсе. Объединение читает обе
    и делает утверждение строго сильнее, а не слабее.

    Первой такой страницей стал подраздел «Воркеры»: план 06-05 разделил его на
    блок инфраструктуры и блок воркеров аккаунтов (D-09).
    """
    heads = ROWHEAD_RE.findall(html)
    assert heads, "шапка колонок раздела не найдена"
    return {
        name
        for head in heads
        for name in re.findall(r"<span>([^<]*)</span>", head)
        if name
    }


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

# AD_CELL_LABELS вместе с test_ads_cell_labels_present ВЫШЛИ отсюда задачей
# 260825-m0b — ПЯТАЯ инвентаризация строки-таблицы, снятая тем же коммитом, что
# и четыре соседних: список объявлений переведён на карточную сетку макета
# (unpacked.html:479-508), шапки колонок у него больше нет, а подпись ячейки
# компенсировала именно её скрытие на 860px. Подписывать в карточке нечего —
# каждое значение называет себя само ключом kv__k, и это закреплено
# test_ads_card_names_each_value и test_ads_partial_names_each_value, которые
# проверяют ровно ту же пару поверхностей (страница и порция прокрутки), что
# проверял снятый тест. Форма снятия повторяет соседнюю, планом 04-05.
# RECENT_CELL_LABELS вместе с test_dashboard_cell_labels_present ВЫШЛИ отсюда
# планом 04-05: блок «Последние отправки» заменён живой лентой (DASH-03), её
# строка не таблица и колонок не имеет вовсе — подписывать в ней нечего.
# «Баланс» ВЫШЕЛ отсюда планом 05.1-08 вместе со своей колонкой: ревизия `0020`
# уронила таблицу остатка сообщений, и подписывать в строке стало нечего.
# «Доступ» ВЕРНУЛ сюда план `05.1-09` вместе с колонкой на её месте — тем самым
# планом, как и предписывал абзац выше: иначе новая колонка приехала бы без
# подписи и на 860px стала бы значением без названия. Подпись читается элементом
# `USER_COLUMNS` ПО ИНДЕКСУ и в шапке, и в ячейке; кортеж ниже — независимый
# свидетель того, что обе копии совпали, а не второй источник строки.
#
# ПЛАН 06-09 ПЕРЕПИСАЛ НАБОР КОЛОНОК ЦЕЛИКОМ (D-35, UI-контракт S5), и кортеж
# поднят ТЕМ ЖЕ планом — иначе новые колонки приехали бы без подписей и на 860px
# стали бы значениями без названий, ровно как предупреждает абзац выше.
# Изменений три, и каждое — сознательный шаг, а не переименование:
#   • «Статус» → «Состояние»: слово «статус» на этом экране занято состоянием
#     ДОСТУПА, и две разные величины под одним словом читаются как одна;
#   • добавлено «Аккаунтов» — число мессенджер-аккаунтов пользователя, первая и
#     единственная новая величина строки;
#   • «Регистрация» уехала в конец: порядок колонок задаёт UI-контракт.
# Состав персональных данных при этом не расширен сверх названной величины
# (T-07-02) — перевёрстка по-прежнему не основание показать больше.
ADMIN_USER_CELL_LABELS = ("Доступ", "Состояние", "Аккаунтов", "Регистрация")


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
    #
    # ads/includes/ad_card.html ВЫШЕЛ из перечня задачей 260825-m0b: он больше
    # не рисует строку ВОВСЕ — карточка объявления собрана по разделу `isAds`
    # макета (unpacked.html:481-508) и примитива строки-таблицы не несёт, а
    # значит в обход по строкам не попадает по построению. Замены в перечне у
    # него нет и быть не может; обещание «понятно, что означает каждое значение»
    # переехало в test_ads_card_names_each_value.
    "billing/includes/payment_row.html": (
        "макрос строки внутри объединения billing/balance.html"
    ),
    # Объединение переехало вместе с шапкой: план 06-05 вынес оба блока
    # подраздела в паршал опроса, и страница теперь только включает его внутрь
    # контейнера опроса. Подписи ячеек проверяются там, где рисуется шапка.
    "admin/includes/worker_row.html": (
        "макрос строки внутри объединения admin/includes/workers_partial.html"
    ),
    # Подраздел «Очередь» (план 06-07) повторяет форму подраздела «Воркеры»
    # дословно: макрос строки в своём файле, шапка — в шаблоне страницы.
    "admin/includes/queue_row.html": (
        "макрос строки внутри объединения admin/queue.html"
    ),
    # Подраздел «Пользователи» (план 06-09) — третий подряд той же формы:
    # макрос строки в своём файле, шапка — в шаблоне страницы. Строка вынесена
    # из самой страницы в отдельный файл вслед за воркерами и очередью: раздел,
    # рисующий строку иначе, чем два соседних, читался бы как другой механизм.
    "admin/includes/user_row.html": (
        "макрос строки внутри объединения admin/users.html"
    ),
    # Подраздел «Платежи» (план 06-11) — четвёртый подряд той же формы: макрос
    # строки в своём файле, шапка — в шаблоне страницы.
    "admin/includes/payment_row.html": (
        "макрос строки внутри объединения admin/payments.html"
    ),
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
    # Класс 2 — ЗЕРКАЛА СТРОКИ РАЗДЕЛА «АККАУНТЫ» — ОПУСТЕЛ ЗАДАЧЕЙ 260825-of5.
    # Оба входа (accounts/partial_cards.html и
    # accounts/partials/sync_status_card.html) СНЯТЫ: раздел переведён на
    # карточную сетку макета (unpacked.html:877-903), и ни один из двух файлов
    # больше не рисует строку ВОВСЕ — ни вызова примитива строки, ни написанного
    # вручную признака в них не осталось, а значит в обход по строкам они не
    # попадают по построению. Замены в перечне у них нет и быть не может;
    # синхронность трёх файлов держат тесты test_accounts_three_files_* выше, а
    # обещание «понятно, что означает каждое значение» переехало в три проверки
    # test_accounts_*_names_each_value.
    # Класс 3: страницы-карточки без шапки колонок вовсе. На 860px нечему
    # скрываться, значит и компенсировать подписью нечего.
    # admin/group_info_detail.html ВЫШЕЛ из перечня планом 06-01 вместе с самим
    # шаблоном: экраны справочника групп снесены (D-05).
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


class _QueueRowheadPipeline:
    """Конвейер заглушки: отвечает на пару «длина + диапазон» одной очереди."""

    def __init__(self):
        self._keys: list[str] = []

    def llen(self, key: str):
        self._keys.append(key)
        return self

    def lrange(self, key: str, start: int, stop: int):
        self._keys.append(key)
        return self

    def get(self, key: str):
        self._keys.append(key)
        return self

    async def execute(self):
        import json

        body = json.dumps(
            {
                "task_id": "rowhead-task",
                "ad_title": "Заголовок",
                "group_name": "Группа «Барахолка»",
            },
            ensure_ascii=False,
        ).encode()
        occupied = any(key.startswith("wa:queue:") for key in self._keys)
        return [1, [body]] if occupied else [0, []]


class _QueueRowheadRedis:
    """Заглушка Redis для подраздела «Очередь» — ровно одна задача в WA-очереди.

    ⚠️ БЕЗ НЕЁ ЭТОТ ВХОД ТАБЛИЦЫ ЗЕЛЕНЕЛ БЫ ВАКУУМНО. Шапка колонок подраздела
    рисуется ТОЛЬКО над непустой очередью — пустая печатает пустое состояние, у
    которого ни шапки, ни подписей нет вовсе, и сравнение разностей сошлось бы,
    ничего не сравнив. Очередь же живёт в Redis, которого в суите нет: подмена
    идёт через ту же именованную точку модуля, что у подраздела «Воркеры».
    """

    def pipeline(self):
        return _QueueRowheadPipeline()

    async def llen(self, key: str) -> int:
        return 0


class RowheadPage(NamedTuple):
    """Вход таблицы параметризации: одна страница с шапкой колонок.

    unlabelled — ОЖИДАЕМАЯ разность «названия колонок шапки минус подписи»,
    объявленная явно, а не выведенная. Это и делает сетку строгой: новая колонка
    без подписи увеличивает разность и роняет тест.

    ops_state — нужна ли странице подмена оперативного состояния, чтобы шапка
    вообще отрисовалась. Признак объявлен явно, а не выведен из имени шаблона:
    страница, которой подмена нужна и не досталась, показала бы пустое
    состояние, и вход таблицы утверждал бы про вёрстку, которой на экране нет.
    """

    template: str
    url: str
    admin: bool
    seed: str
    unlabelled: frozenset[str]
    note: str = ""
    ops_state: bool = False


ROWHEAD_PAGES = (
    # accounts/list.html ВЫШЕЛ из таблицы задачей 260825-of5: шапку колонок он
    # больше не вызывает — список стал карточной сеткой по каноническому макету
    # (unpacked.html:878), и компенсировать скрывающуюся на 860px шапку ему
    # нечем, потому что шапки нет. Обещание «понятно, что означает каждое
    # значение» переехало в test_accounts_card_names_each_value и в две парные
    # проверки остальных поверхностей раздела.
    #
    # ads/list.html ВЫШЕЛ из таблицы задачей 260825-m0b: шапку колонок он больше
    # не вызывает — список стал карточной сеткой по каноническому макету
    # (unpacked.html:479), и компенсировать скрывающуюся на 860px шапку ему
    # нечем, потому что шапки нет. Обещание «понятно, что означает каждое
    # значение» переехало в test_ads_card_names_each_value.
    #
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
    # Подраздел «Воркеры» (план 06-01, разделён надвое планом 06-05). Разность
    # ПУСТА: подписаны ВСЕ колонки обеих таблиц — на 860px шапки скрываются, и
    # «в работе» без названия колонки был бы неотличим от состояния сессии,
    # стоящего рядом.
    #
    # ⚠️ ШАБЛОН НАЗВАН ПАРШАЛОМ, А АДРЕС ОСТАЛСЯ СТРАНИЧНЫМ, И ЭТО НЕ
    # рассогласование. План 06-05 вынес ОБА блока подраздела в
    # `admin/includes/workers_partial.html`: он же первичная отрисовка, он же
    # ответ опроса (D-12). Шапку колонок вызывает теперь именно он — поэтому в
    # таблице стоит он, иначе обход по шапкам не сошёлся бы. Адрес оставлен
    # страничным намеренно: проверять подписи надо на том, что видит человек, а
    # человек открывает страницу, а не паршал.
    RowheadPage(
        "admin/includes/workers_partial.html", "/admin/workers", True,
        "admin_workers", frozenset(),
        note=(
            "Две таблицы на одной странице: блок инфраструктуры (D-09) и блок "
            "воркеров аккаунтов. Подписи обязаны покрывать колонки ОБЕИХ."
        ),
    ),
    # ⚠️ НАБЛЮДЕНИЕ T-13-09 ПО ЭТОЙ СТРАНИЦЕ ЗАКРЫТО — И ЗАКРЫТО СНОСОМ, А НЕ
    # ДОПИСЫВАНИЕМ ПОДПИСЕЙ. Колонки «Тип» и «Описание» принадлежали истории
    # операций по балансу сообщений; журнал снят планом 05.1-05 вместе с самим
    # балансом (D-D), и вместе с ним исчезла половина пользовательской правды
    # SC-5, которая на этой странице оставалась ложной. Осталась одна колонка
    # без подписи — «Дата», и она освобождена НАМЕРЕННО: форматированная дата
    # самоописательна (контракт C2 UI-SPEC фазы 05.1).
    # Подраздел «Очередь» (план 06-07). Разность ПУСТА: подписаны все четыре
    # колонки — на 860px шапка скрывается, и «ждёт» без названия колонки было бы
    # неотличимо от имени группы, стоящего рядом.
    RowheadPage(
        "admin/queue.html", "/admin/queue", True, "admin_queue", frozenset(),
        note=(
            "Шапка рисуется только над непустой очередью, поэтому вход требует "
            "подмены оперативного состояния."
        ),
        ops_state=True,
    ),
    # Подраздел «Платежи» (план 06-11). Разность ПУСТА — включая «Дату»,
    # освобождённую у раздела пользователя ниже, и это НЕ разнобой: там журнал
    # платежей человека, где каждая строка про него самого и колонок четыре;
    # здесь — журнал всего сервиса, где рядом с датой стоит имя ПЛАТЕЛЬЩИКА, а
    # на 860px шапка скрывается целиком. Дата без подписи в таком соседстве
    # читается как дата регистрации того, чьё имя напечатано следом.
    RowheadPage(
        "admin/payments.html", "/admin/payments", True, "admin_payments",
        frozenset(),
        note=(
            "Шапка рисуется только над непустым журналом, поэтому вход требует "
            "посева хотя бы одного платежа."
        ),
    ),
    RowheadPage(
        "billing/balance.html", "/billing", False, "billing",
        frozenset({"Дата"}),
    ),
    # НАБЛЮДЕНИЕ, а НЕ принятая базовая линия — та же история, что у тарифов:
    # «Канал» и «Обновлено» на 860px остаются без названия (T-13-09).
    # admin/groups_info.html ВЫШЕЛ из таблицы планом 06-01 вместе с самим
    # шаблоном: экраны справочника групп снесены (D-05). Вместе с ним закрыто и
    # НАБЛЮДЕНИЕ T-13-09 по этой странице («Канал» и «Обновлено» оставались без
    # подписи) — закрыто СНОСОМ предмета, а не дописыванием подписей. Замены в
    # таблице у него нет и быть не может: поверхность снята, а не переименована.
)


async def _seed_rowhead_page(db: AsyncSession, seed: str) -> None:
    """Наполняет страницу так, чтобы шапка и хотя бы одна строка отрисовались.

    Пустая страница рисует empty_state: и шапки, и подписей на ней нет, и
    сравнение разностей зазеленело бы вакуумно.
    """
    # Ветка "accounts" СНЯТА задачей 260825-of5 вместе с входом
    # accounts/list.html: она стала недостижимой — посевать нечего для таблицы,
    # в которой раздела больше нет.
    if seed == "ads":
        await _seed_ad(db)
    elif seed == "schedules":
        await _seed_schedule(db)
    elif seed == "dashboard":
        await _seed_send_log(db)
    elif seed == "admin_users":
        pass  # обычный пользователь и админ зарегистрированы фикстурами
    elif seed == "admin_user_detail":
        await _seed_account(db, type_="max")
    elif seed == "admin_workers":
        # ТЕЛЕГРАМ-АККАУНТ ВЫБРАН НАМЕРЕННО: у него нет отдельного воркера, и
        # сводка живости не делает ни одного обращения к Redis. Посеяв WA или
        # MAX, обход по выдаче начал бы стучаться в брокер, которого в суите
        # нет, — то есть проверка вёрстки зависела бы от внешней службы.
        await _seed_account(db, type_="tg_user")
    elif seed == "admin_queue":
        # WA-АККАУНТ ВЫБРАН НАМЕРЕННО: строки очереди есть только у каналов со
        # своим списком задач, а у telegram-канала их нет вовсе (D-14) — посеяв
        # его, страница осталась бы без шапки колонок.
        await _seed_account(db, type_="wa")
    elif seed == "admin_payments":
        # Журнал подраздела показывает платежи ВСЕХ пользователей, поэтому
        # достаточно любой одной строки: чья она — на вёрстку не влияет.
        await _seed_payment(db)
    elif seed == "billing":
        # Шапку колонок раздела рисует ЖУРНАЛ ПЛАТЕЖЕЙ: история операций по
        # балансу сообщений снята планом 05.1-05, и посев операцией оставлял бы
        # страницу с пустым состоянием вместо шапки.
        await _seed_payment(db)
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
    #
    # ШЕСТЬ → ШЕСТЬ, И ЭТО НЕ «БЕЗ ИЗМЕНЕНИЙ»: план 06-01 завёл подраздел
    # «Воркеры» со своей шапкой (+1) и снёс справочник групп вместе с его
    # шапкой (−1). Совпадение итога — арифметика двух РАЗНЫХ шагов, а не
    # отсутствие правки; проверку держат имена в `declared`, а не число.
    #
    # ШЕСТЬ → СЕМЬ: план 06-07 завёл подраздел «Очередь» со своей шапкой (+1).
    # Снятия в паре с ним нет — это чистое прибавление поверхности.
    #
    # СЕМЬ → ВОСЕМЬ: план 06-11 завёл журнал платежей подраздела «Платежи» со
    # своей шапкой (+1). Снятия в паре с ним нет — это тоже чистое прибавление
    # поверхности: до плана подраздел стоял честной пустотой без единой строки.
    #
    # ВОСЕМЬ → СЕМЬ: задача 260825-m0b сняла шапку колонок со списка объявлений
    # вместе с самой строкой-таблицей — раздел переведён на карточную сетку
    # канонического макета (unpacked.html:479). Прибавления в паре со снятием
    # нет. Уменьшение объявленного числа — признание СОЗНАТЕЛЬНОГО снятия;
    # молчаливое исчезновение шаблона с шапкой по-прежнему краснеет.
    #
    # СЕМЬ → ШЕСТЬ: задача 260825-of5 сняла шапку колонок со списка аккаунтов
    # вместе с самой строкой-таблицей — раздел переведён на карточную сетку
    # канонического макета (unpacked.html:878). Прибавления в паре со снятием
    # нет. Уменьшение объявленного числа — признание СОЗНАТЕЛЬНОГО снятия;
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
    # Восемь → семь → шесть → пять → ШЕСТЬ: макрос строки снесённого раздела
    # удалён планом 03-08 вместе с его списочной страницей, макрос строки
    # последних отправок — планом 04-05 вместе с заменённым блоком дашборда, а
    # страница записи истории планом 04-07 перестала рисовать строку вовсе
    # (перевёрстана на примитив записи). План 05-05 добавил ОДИН файл первого
    # класса: макрос строки платежа, чей исходник входит в объединение
    # billing/balance.html и там же проверяется на подписи. Изменение
    # объявленного числа — признание СОЗНАТЕЛЬНОГО шага; молчаливое появление
    # или исчезновение файла по-прежнему краснеет.
    #
    # ШЕСТЬ → ШЕСТЬ, И ЭТО НЕ «БЕЗ ИЗМЕНЕНИЙ»: план 06-01 добавил ОДИН файл
    # первого класса (макрос строки воркера, чей исходник входит в объединение
    # admin/workers.html) и снял ОДИН файл третьего класса (карточка справочника
    # групп снесена, D-05). Совпадение итога — арифметика двух разных шагов.
    #
    # ШЕСТЬ → СЕМЬ: план 06-07 добавил ОДИН файл первого класса — макрос строки
    # очереди, чей исходник входит в объединение admin/queue.html и там же
    # проверяется на подписи. Снятия в паре с ним нет.
    #
    # СЕМЬ → ВОСЕМЬ: план 06-09 добавил ОДИН файл первого класса — макрос строки
    # пользователя, чей исходник входит в объединение admin/users.html.
    # Разметка строки при этом не появилась, а ПЕРЕЕХАЛА: раньше она лежала в
    # теле самой страницы и в обход по строкам без шапки не попадала, потому что
    # шапку рисовал тот же файл. Снятия в паре с ним нет.
    #
    # ВОСЕМЬ → ДЕВЯТЬ: план 06-11 добавил ОДИН файл первого класса — макрос
    # строки платежа админского журнала, чей исходник входит в объединение
    # admin/payments.html и там же проверяется на подписи. Он ЧЕТВЁРТЫЙ подряд
    # той же формы (воркер, очередь, пользователь, платёж): подраздел, рисующий
    # строку иначе, чем три соседних, читался бы как другой механизм. Снятия в
    # паре с ним нет.
    #
    # ДЕВЯТЬ → ВОСЕМЬ: задача 260825-m0b сняла ОДИН файл первого класса — макрос
    # карточки объявления перестал рисовать строку вовсе вместе с переводом
    # раздела на карточную сетку макета (unpacked.html:481-508). Снятие идёт ТЕМ
    # ЖЕ коммитом, что и снятие шапки колонок с ads/list.html: разъехавшись, эти
    # два шага оставили бы список либо со строками без шапки, либо с шапкой без
    # строк. Прибавления в паре со снятием нет.
    #
    # ВОСЕМЬ → ШЕСТЬ: задача 260825-of5 сняла ДВА файла второго класса — оба
    # зеркала строки раздела «Аккаунты» (порция бесконечной прокрутки и блок
    # подмены по опросу статуса) перестали рисовать строку вовсе вместе с
    # переводом раздела на карточную сетку макета (unpacked.html:877-903).
    # Снятие идёт ТЕМ ЖЕ коммитом, что и снятие шапки колонок с
    # accounts/list.html: разъехавшись, эти два шага оставили бы раздел либо со
    # строками без шапки, либо с шапкой без строк. Прибавления в паре со снятием
    # нет; после него КЛАСС 2 перечня пуст.
    assert len(declared) == 6, (
        f"ожидалось шесть таких шаблонов, объявлено {len(declared)}"
    )
    # ⚠️ ЗДЕСЬ СТОЯЛО ХВОСТОВОЕ УТВЕРЖДЕНИЕ о написанном ВРУЧНУЮ признаке строки
    # у accounts/partials/sync_status_card.html. Оно снято задачей 260825-of5
    # вместе с обоими входами класса 2: утверждение существовало ради
    # разрешителя перечня, из которого файл ушёл, и на файле, строку больше не
    # рисующем, оно проверяло бы отсутствие того, чего нет. Второе условие
    # разрешителя (MANUAL_ROW_ATTR_RE) при этом ОСТАЁТСЯ: оно ловит любой новый
    # файл, собравший открывающий тег строки вручную.


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

    if page.ops_state:
        from unittest.mock import patch

        with patch(
            "app.services.ops_state._get_redis", return_value=_QueueRowheadRedis()
        ):
            response = await client.get(page.url.format(user_id=user.id))
    else:
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
    # Адрес справочника групп ушёл отсюда планом 06-01 вместе с его экранами
    # (D-05). Его место заняли подразделы админ-панели: обход требует 200, и все
    # пять новых адресов его дают.
    "/admin/workers",
    "/admin/queue",
    "/admin/logs",
    "/admin/payments",
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


def test_dashboard_blocks_share_one_head_without_a_divider():
    """Блоки дашборда несут ОДНУ шапку, и разделителя под ней нет.

    `card_open(title=...)` рисует `.card__head` с `border-bottom`, которого в
    макете нет ни у одной карточки дашборда: «Ближайшие отправки» шли через
    него и получали линию, а «Живая лента» — нет, и две карточки одной пары
    выглядели по-разному.

    Блоков на странице осталось ДВА — пара «Ближайшие отправки» / «Живая
    лента»: карточка недельной активности снята задачей 260826-9vv вместе со
    своим шаблоном, а собственная её шапка жила в том шаблоне, а не здесь,
    поэтому переписи шапок СТРАНИЦЫ её снятие не меняет.

    Правило ОДНО на три атрибута: до консолидации их было два с побайтово
    совпадающими телами. Сам примитив `.card__head` с разделителем остаётся —
    здесь снято его применение на этой странице, а не он сам.
    """
    css = APP_CSS.read_text(encoding="utf-8")
    page = (TEMPLATES_DIR / "dashboard.html").read_text(encoding="utf-8")

    assert (
        "[data-blockhead] { display: flex; align-items: center; gap: 10px;"
        " margin-bottom: 16px; }" in css
    )
    # Копии консолидированного правила не вернулись.
    assert "[data-feedhead]" not in css
    assert "[data-heathead]" not in css

    # Перепись шапок СТРАНИЦЫ: пара «Ближайшие отправки» / «Живая лента» — всё,
    # что на ней осталось. Одна из прежних трёх принадлежала карточке перечня
    # воркеров и ушла вместе с ней (задача 260826-6jq); шапка недельной
    # активности в этой переписи не участвовала никогда — она жила в шаблоне
    # своего макроса, снятом задачей 260826-9vv. Утверждение остаётся тем же по
    # смыслу — ни один блок страницы не заводит своей шапки в обход общего
    # атрибута, — и следует за числом блоков, а не ослабляется: собственная
    # шапка у нового блока это число НЕ увеличила бы.
    assert page.count("data-blockhead") == 2, "шапки блоков страницы разъехались"

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
