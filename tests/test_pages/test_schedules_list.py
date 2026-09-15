"""План 02-07: сводный список расписаний (SCH-04, SCH-05).

Файл закрепляет ДВА обещания сводного списка, каждое своим слоем:

* Задача 1 — ДАННЫЕ карточки. Имена групп разрешаются ОДНИМ запросом на всю
  страницу и только среди групп владельца; идентификатор без совпадения в имя
  не превращается; признак черновика доходит до шаблона сравнением с
  константой, а не со строковым литералом.
* Задача 3 — РАЗМЕТКА карточки, два пустых состояния, склонения счётчика и
  перекрёстная изоляция переключения.

Порядок именно такой: разрешение имён и признак черновика — свойства
обработчика, и утверждать их по отрендеренной странице значило бы проверять
разом две правки. Ошибка в разметке проявится ПУСТОЙ карточкой (страница
вернёт 200), поэтому Задача 3 утверждает реальные строки, а не код ответа.
"""

from datetime import datetime, timezone

import contextlib
import re
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.user import User
from app.pages.schedules import (
    PAGE_SIZE,
    SUMMARY_GROUP_NAMES,
    _build_schedule_items,
    _clean_choice,
    _group_names_for,
)
from tests.conftest import a_future_run_moment

# Запрос к таблице групп в журнале выполненных операторов. Имя таблицы может
# прийти в кавычках (groups — зарезервированное слово в части диалектов),
# поэтому сравнение идёт регулярным выражением, а не подстрокой.
GROUPS_QUERY_RE = re.compile(r'FROM\s+"?groups"?', re.I)

# Явная сортировка сводного списка в ВЫПОЛНЕННОМ операторе. Проверяется именно
# оператор, а не исходник: совпадение порядка карточек с порядком посева зелено
# и без ORDER BY, потому что SQLite и так отдаёт строки в порядке rowid.
SCHEDULES_ORDER_RE = re.compile(r'ORDER BY\s+"?schedules"?\.id', re.I)


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_ad(
    db: AsyncSession, title: str = "Объявление", status: str = AD_STATUS_PUBLISHED
) -> Ad:
    user = await _user(db)
    ad = Ad(user_id=user.id, title=title, text="Текст объявления", images=[], status=status)
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


async def _seed_group(
    db: AsyncSession, account: MessengerAccount, name: str, user_id: int | None = None
) -> Group:
    user = await _user(db)
    group = Group(
        user_id=user.id if user_id is None else user_id,
        account_id=account.id,
        messenger_type=account.type,
        group_external_id=f"ext-{name}",
        name=name,
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def _seed_schedule(
    db: AsyncSession,
    ad: Ad,
    account: MessengerAccount | None = None,
    group_ids: list[int] | None = None,
    days: list[int] | None = None,
    times: list[str] | None = None,
    is_active: bool = True,
) -> Schedule:
    schedule = Schedule(
        ad_id=ad.id,
        account_id=account.id if account else None,
        group_ids=group_ids if group_ids is not None else [],
        days_of_week=days if days is not None else [0, 2, 4],
        times_of_day=times if times is not None else ["09:30"],
        timezone="UTC",
        is_active=is_active,
        # Момент запуска ставится ТОЛЬКО включённой строке. Схема запрещает пару
        # «включено + нет момента» (CHECK ck_schedules_active_requires_next_run),
        # а приостановленной строке он не нужен и вреден: карточка печатает
        # «следующий запуск» по одному лишь наличию значения, и выданный паузе
        # момент менял бы разметку, к предмету этих тестов отношения не имеющую.
        next_run_at=(
            a_future_run_moment() if is_active else None
        ),
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@contextlib.contextmanager
def _statement_log(db_session: AsyncSession):
    """Журнал SQL-операторов, выполненных за время блока.

    Слушатель вешается на СИНХРОННЫЙ движок за асинхронным: событие
    before_cursor_execute объявлено именно там. Снимается в finally — иначе
    журнал следующего теста наследовал бы чужой слушатель.
    """
    engine = db_session.bind.sync_engine
    seen: list[str] = []

    def _before(conn, cursor, statement, parameters, context, executemany):
        seen.append(statement)

    event.listen(engine, "before_cursor_execute", _before)
    try:
        yield seen
    finally:
        event.remove(engine, "before_cursor_execute", _before)


def _row(schedule, ad_title="Объявление", ad_status=AD_STATUS_PUBLISHED, messenger_type="wa"):
    """Строка выдачи обработчика: ровно те поля, что даёт его select."""
    return SimpleNamespace(
        Schedule=schedule,
        ad_title=ad_title,
        ad_status=ad_status,
        messenger_type=messenger_type,
    )


def _fake_schedule(group_ids: list[int]) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        group_ids=group_ids,
        days_of_week=[0],
        times_of_day=["09:00"],
        next_run_at=None,
        is_active=True,
        account_id=1,
    )


# --- Задача 1: имена групп разрешаются одним запросом и только у владельца ----


@pytest.mark.asyncio
async def test_group_names_are_resolved_for_the_owner(
    auth_headers: dict, db_session: AsyncSession
):
    """Карточка получает ИМЕНА своих групп, а не только их число (SCH-04)."""
    user = await _user(db_session)
    account = await _seed_account(db_session)
    first = await _seed_group(db_session, account, "Клуб выходного дня")
    second = await _seed_group(db_session, account, "Барахолка района")
    schedule = _fake_schedule([first.id, second.id])

    names = await _group_names_for(db_session, user.id, [schedule])

    assert names == {first.id: "Клуб выходного дня", second.id: "Барахолка района"}


@pytest.mark.asyncio
async def test_foreign_group_name_never_becomes_a_card_value(
    auth_headers: dict, db_session: AsyncSession
):
    """T-02-34: идентификаторы групп приходят массивом внутри расписания.

    Без ограничения по владельцу имя ЧУЖОЙ группы попало бы в карточку — своё
    расписание достаточно сохранить с чужим идентификатором.
    """
    user = await _user(db_session)
    account = await _seed_account(db_session)
    own = await _seed_group(db_session, account, "Своя группа")
    foreign = await _seed_group(
        db_session, account, "Чужая группа", user_id=user.id + 1000
    )
    schedule = _fake_schedule([own.id, foreign.id])

    names = await _group_names_for(db_session, user.id, [schedule])

    assert names == {own.id: "Своя группа"}
    assert "Чужая группа" not in names.values()


@pytest.mark.asyncio
async def test_group_names_query_is_skipped_when_there_is_nothing_to_resolve(
    auth_headers: dict, db_session: AsyncSession
):
    """Расписание без групп не порождает запроса вовсе."""
    user = await _user(db_session)

    with _statement_log(db_session) as seen:
        names = await _group_names_for(db_session, user.id, [_fake_schedule([])])

    assert names == {}
    assert not [s for s in seen if GROUPS_QUERY_RE.search(s)]


@pytest.mark.asyncio
async def test_summary_page_resolves_group_names_in_one_query(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-02-38: тридцать расписаний — один запрос имён, а не тридцать.

    Утверждение о РОСТЕ, а не о конкретном числе: запросов страницы несколько
    (пользователь, расписания, счётчик, имена), но по числу расписаний не
    растёт ни один.
    """
    ad = await _seed_ad(db_session, title="Объявление страницы")
    account = await _seed_account(db_session)
    groups = [
        await _seed_group(db_session, account, f"Группа {i}") for i in range(30)
    ]
    for group in groups:
        await _seed_schedule(db_session, ad, account, group_ids=[group.id])

    with _statement_log(db_session) as seen:
        response = await authed_client.get("/schedules")

    assert response.status_code == 200
    group_queries = [s for s in seen if GROUPS_QUERY_RE.search(s)]
    assert len(group_queries) <= 1, (
        f"имена групп разрешаются {len(group_queries)} запросами — по запросу на "
        "расписание вместо одного на страницу"
    )
    assert len(seen) < 30, (
        f"число запросов страницы ({len(seen)}) растёт по числу расписаний"
    )


@pytest.mark.asyncio
async def test_missing_group_does_not_break_the_page(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Удалённая или недоступная группа не роняет страницу.

    Что на её месте НЕ появляется пустое имя — утверждает
    test_unresolved_group_id_does_not_become_an_empty_name на слое данных, а
    отрисовку оставшегося имени — test_summary_card_renders_group_names на слое
    разметки. Здесь проверяется только то, что страница переживает
    идентификатор без группы.
    """
    ad = await _seed_ad(db_session, title="Объявление с потерянной группой")
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Единственная живая группа")
    await _seed_schedule(db_session, ad, account, group_ids=[group.id, 999_999])

    response = await authed_client.get("/schedules")

    assert response.status_code == 200


# --- Задача 1: состав элемента строки ----------------------------------------


def test_item_carries_group_names_and_the_remainder():
    """Имена первых нескольких групп плюс остаток числом (RESEARCH Q3)."""
    ids = list(range(1, SUMMARY_GROUP_NAMES + 3))
    names = {gid: f"Группа {gid}" for gid in ids}
    user = SimpleNamespace(timezone="UTC")

    (item,) = _build_schedule_items([_row(_fake_schedule(ids))], user, None, names)

    assert item["group_names"] == [f"Группа {gid}" for gid in ids[:SUMMARY_GROUP_NAMES]]
    assert item["group_extra"] == len(ids) - SUMMARY_GROUP_NAMES
    assert item["group_total"] == len(ids)


def test_unresolved_group_id_does_not_become_an_empty_name():
    """Идентификатор без совпадения не рендерится пустой строкой.

    Остаток тоже считается по РАЗРЕШЁННЫМ именам: иначе карточка обещала бы
    «и ещё 1», которого показать нечем.
    """
    user = SimpleNamespace(timezone="UTC")

    (item,) = _build_schedule_items(
        [_row(_fake_schedule([1, 777]))], user, None, {1: "Живая группа"}
    )

    assert item["group_names"] == ["Живая группа"]
    assert "" not in item["group_names"]
    assert item["group_extra"] == 0
    assert item["group_total"] == 1


def test_draft_ad_marks_its_schedule():
    """Расписание объявления-черновика приходит в шаблон с признаком (D-01)."""
    user = SimpleNamespace(timezone="UTC")

    (item,) = _build_schedule_items(
        [_row(_fake_schedule([]), ad_status=AD_STATUS_DRAFT)], user, None, {}
    )

    assert item["is_draft"] is True


def test_published_ad_does_not_mark_its_schedule():
    """Парный тест: без него предыдущий зеленел бы на константе True."""
    user = SimpleNamespace(timezone="UTC")

    (item,) = _build_schedule_items(
        [_row(_fake_schedule([]), ad_status=AD_STATUS_PUBLISHED)], user, None, {}
    )

    assert item["is_draft"] is False


# --- Задача 1: испорченное значение фильтра (T-02-35) ------------------------


@pytest.mark.parametrize(
    "value",
    [None, "", "   ", "unknown", "'; DROP TABLE schedules; --", "tg_user\x00"],
)
def test_unknown_filter_value_falls_back_to_all(value):
    """Неизвестное значение приводит к варианту «Все», а не к ошибке (E14)."""
    assert _clean_choice(value, ("tg_user", "wa", "max")) == ""


@pytest.mark.parametrize("value", ["tg_user", "wa", "max"])
def test_known_filter_value_survives(value):
    """Парный тест: без него предыдущий зеленел бы на функции, всегда пустой."""
    assert _clean_choice(value, ("tg_user", "wa", "max")) == value


# =============================================================================
# Задача 3: разметка сводного списка (SCH-04, SCH-05)
# =============================================================================
#
# Утверждения на РЕАЛЬНЫЕ строки и адреса маршрутов, а не только на код ответа:
# ошибка в имени параметра макроса оставит страницу валидной, а карточку —
# пустой (образец — test_ads_card_renders_data).


@pytest.mark.asyncio
async def test_summary_card_renders_group_names(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """SCH-04: карточка показывает объявление, канал, ИМЕНА групп, дни и время.

    Имена, а не только число: SCH-04 и критерий приёмки 4 перечисляют группы
    наравне с объявлением, каналом, днями и временем, то есть требуют
    содержания.
    """
    ad = await _seed_ad(db_session, title="Летняя распродажа курсов")
    account = await _seed_account(db_session, type_="wa")
    group = await _seed_group(db_session, account, "Барахолка Северного района")
    schedule = await _seed_schedule(
        db_session, ad, account, group_ids=[group.id], days=[0, 4], times=["09:30"]
    )

    html = (await authed_client.get("/schedules")).text

    assert "Летняя распродажа курсов" in html
    assert "Барахолка Северного района" in html, "имя группы не дошло до карточки"
    assert "09:30" in html
    assert 'aria-label="WhatsApp"' in html, "иконка канала не отрисована"
    assert "Пн" in html and "Пт" in html, "дни расписания не отрисованы"
    assert f"/schedules/{schedule.id}/toggle" in html
    assert f"/ads/{ad.id}/edit?sched={schedule.id}" in html


@pytest.mark.asyncio
async def test_summary_card_folds_the_remainder_into_a_count(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Имена первых нескольких групп плюс остаток числом — карточка не растёт."""
    ad = await _seed_ad(db_session, title="Объявление многих групп")
    account = await _seed_account(db_session)
    groups = [
        await _seed_group(db_session, account, f"Группа номер {i}")
        for i in range(SUMMARY_GROUP_NAMES + 2)
    ]
    await _seed_schedule(
        db_session, ad, account, group_ids=[g.id for g in groups]
    )

    html = (await authed_client.get("/schedules")).text

    assert "Группа номер 0" in html
    assert "и ещё 2" in html, "остаток групп не свёрнут в число"
    assert groups[-1].name not in html, (
        "карточка перечислила все группы — предел показа не действует"
    )


@pytest.mark.asyncio
async def test_draft_ad_schedule_is_marked_and_promises_no_sends(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E13 `partial`: черновик виден и в бейдже, и в ячейке запуска."""
    ad = await _seed_ad(
        db_session, title="Черновик со расписанием", status=AD_STATUS_DRAFT
    )
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа черновика")
    await _seed_schedule(db_session, ad, account, group_ids=[group.id])

    html = (await authed_client.get("/schedules")).text

    assert "Объявление в черновике" in html
    assert "отправок не будет" in html


@pytest.mark.asyncio
async def test_published_ad_schedule_carries_no_draft_marker(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный тест: без него предыдущий зеленел бы на безусловном бейдже."""
    ad = await _seed_ad(db_session, title="Опубликованное объявление")
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа публикации")
    await _seed_schedule(db_session, ad, account, group_ids=[group.id])

    html = (await authed_client.get("/schedules")).text

    assert "Объявление в черновике" not in html
    assert "отправок не будет" not in html


# --- Два пустых состояния и полоса фильтров ----------------------------------


@pytest.mark.asyncio
async def test_empty_state_without_schedules_points_at_the_ads(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Расписаний нет вовсе: подсказка называет МЕСТО создания (D-14)."""
    html = (await authed_client.get("/schedules")).text

    assert "Расписаний пока нет" in html
    assert "Расписания создаются в редакторе объявления" in html
    assert 'href="/ads"' in html
    assert "Расписания не найдены" not in html, "показано не то пустое состояние"


@pytest.mark.asyncio
async def test_empty_state_with_no_matches_offers_to_reset_the_filters(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Фильтр ничего не нашёл: единственное осмысленное действие — сброс."""
    ad = await _seed_ad(db_session, title="Объявление с расписанием")
    account = await _seed_account(db_session, type_="wa")
    await _seed_schedule(db_session, ad, account)

    html = (await authed_client.get("/schedules?channel=tg_user")).text

    assert "Расписания не найдены" in html
    assert "СБРОСИТЬ ФИЛЬТРЫ" in html
    assert "Расписаний пока нет" not in html, (
        "нулевой результат отбора неотличим от отсутствия расписаний"
    )


@pytest.mark.asyncio
async def test_filter_bar_renders_when_the_list_is_empty(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E14 `empty`: снять фильтр можно и с пустого списка.

    Полоса, спрятанная вместе со списком, оставила бы пользователя, который
    отфильтровал всё до нуля, без способа вернуться.
    """
    ad = await _seed_ad(db_session, title="Единственное объявление")
    account = await _seed_account(db_session, type_="wa")
    await _seed_schedule(db_session, ad, account)

    html = (await authed_client.get("/schedules?channel=tg_user")).text

    assert 'id="schedules-filters"' in html, "полоса фильтров исчезла вместе со списком"
    assert 'name="channel"' in html and 'name="state"' in html
    assert "Поиск по объявлению и времени запуска" in html
    assert "Сбросить" in html


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "channel=unknown",
        "state=%3Cscript%3E",
        "channel=&state=&search=",
        "channel=wa&state=nonsense",
    ],
)
async def test_unknown_filter_value_does_not_break_the_page(
    authed_client: AsyncClient, db_session: AsyncSession, query: str
):
    """T-02-35: значение из строки запроса не роняет страницу."""
    ad = await _seed_ad(db_session, title="Объявление устойчивости")
    account = await _seed_account(db_session, type_="wa")
    await _seed_schedule(db_session, ad, account)

    response = await authed_client.get(f"/schedules?{query}")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_hostile_search_term_is_rendered_as_text(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-02-36: поисковый термин возвращается пользователю в поле полосы фильтров.

    Автоэкранирование Jinja обязано оставить его текстом; разметка, собранная
    из термина, была бы исполняемой на origin приложения.
    """
    term = '<script>alert(1)</script>'

    response = await authed_client.get("/schedules", params={"search": term})

    assert response.status_code == 200
    assert term not in response.text, "поисковый термин вернулся разметкой"
    assert "&lt;script&gt;" in response.text or "&#34;" in response.text


# --- Склонение счётчика найденных --------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "count,expected",
    [(1, "1 расписание"), (3, "3 расписания"), (5, "5 расписаний")],
)
async def test_result_count_is_declined(
    authed_client: AsyncClient, db_session: AsyncSession, count: int, expected: str
):
    """«1 расписаний» — заметный дефект копирайтинга (UI-SPEC E13 zero-one-many)."""
    ad = await _seed_ad(db_session, title="Объявление счётчика")
    account = await _seed_account(db_session)
    for _ in range(count):
        await _seed_schedule(db_session, ad, account)

    html = (await authed_client.get("/schedules")).text

    assert expected in html


# --- Фильтрация и поиск отбирают, а не украшают -------------------------------


@pytest.mark.asyncio
async def test_channel_filter_narrows_the_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Полоса фильтров ОТБИРАЕТ: иначе она украшение, а не орган управления."""
    ad = await _seed_ad(db_session, title="Объявление обоих каналов")
    wa = await _seed_account(db_session, type_="wa")
    tg = await _seed_account(db_session, type_="tg_user")
    wa_group = await _seed_group(db_session, wa, "Группа ватсапа")
    tg_group = await _seed_group(db_session, tg, "Группа телеграма")
    await _seed_schedule(db_session, ad, wa, group_ids=[wa_group.id])
    await _seed_schedule(db_session, ad, tg, group_ids=[tg_group.id])

    html = (await authed_client.get("/schedules?channel=wa")).text

    assert "Группа ватсапа" in html
    assert "Группа телеграма" not in html


@pytest.mark.asyncio
async def test_state_filter_narrows_the_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Вторая ось отбора: активные и поставленные на паузу."""
    ad = await _seed_ad(db_session, title="Объявление двух состояний")
    account = await _seed_account(db_session)
    live = await _seed_group(db_session, account, "Группа активного")
    paused = await _seed_group(db_session, account, "Группа на паузе")
    await _seed_schedule(db_session, ad, account, group_ids=[live.id], is_active=True)
    await _seed_schedule(
        db_session, ad, account, group_ids=[paused.id], is_active=False
    )

    active_html = (await authed_client.get("/schedules?state=active")).text
    paused_html = (await authed_client.get("/schedules?state=paused")).text

    assert "Группа активного" in active_html and "Группа на паузе" not in active_html
    assert "Группа на паузе" in paused_html and "Группа активного" not in paused_html


@pytest.mark.asyncio
async def test_search_matches_the_ad_title_and_the_launch_time(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Плейсхолдер обещает обе оси поиска — обещание проверяется обеими."""
    morning_ad = await _seed_ad(db_session, title="Утренняя рассылка")
    evening_ad = await _seed_ad(db_session, title="Вечерняя рассылка")
    account = await _seed_account(db_session)
    await _seed_schedule(db_session, morning_ad, account, times=["07:15"])
    await _seed_schedule(db_session, evening_ad, account, times=["21:45"])

    by_title = (await authed_client.get("/schedules?search=Утренняя")).text
    by_time = (await authed_client.get("/schedules?search=21:45")).text

    assert "Утренняя рассылка" in by_title and "Вечерняя рассылка" not in by_title
    assert "Вечерняя рассылка" in by_time and "Утренняя рассылка" not in by_time


# --- Переключение: свои права и честное состояние -----------------------------


@pytest.mark.asyncio
async def test_toggle_from_the_list_leaves_a_foreign_schedule_alone(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-02-37: перевёрстка сменила орган управления, а не права.

    Проверка владения живёт на маршруте и разметкой не подкрепляется: прямой
    POST мимо страницы обязан получить тот же отказ.
    """
    own_ad = await _seed_ad(db_session, title="Своё объявление")
    account = await _seed_account(db_session)
    own = await _seed_schedule(db_session, own_ad, account)

    user = await _user(db_session)
    foreign_ad = Ad(
        user_id=user.id + 1000, title="Чужое", text="Чужой текст", images=[]
    )
    db_session.add(foreign_ad)
    await db_session.commit()
    await db_session.refresh(foreign_ad)
    foreign = await _seed_schedule(db_session, foreign_ad, account)

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
    assert foreign.is_active is True, "чужое расписание переключилось из списка"


@pytest.mark.asyncio
async def test_refused_toggle_leaves_the_card_in_its_previous_state(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Тумблер никогда не показывает состояние, которого сервер не принял.

    Состояние приходит СЕРВЕРОМ на каждой отрисовке, поэтому отклонённое
    возобновление неполного расписания (D-08) не оставляет включённого вида.
    """
    ad = await _seed_ad(db_session, title="Неполное расписание")
    schedule = await _seed_schedule(db_session, ad, account=None, is_active=False)

    response = await authed_client.post(
        f"/schedules/{schedule.id}/toggle", follow_redirects=False
    )
    assert response.status_code == 302
    await db_session.refresh(schedule)
    assert schedule.is_active is False, "сервер принял возобновление неполного"

    html = (await authed_client.get("/schedules")).text
    toggle = html[
        html.index(f'id="schedule-toggle-{schedule.id}"') :
    ].split(">", 1)[0]
    assert "checked" not in toggle, "тумблер показывает непринятое состояние"
    assert "disabled" in toggle, "тумблер неполного расписания доступен к нажатию"
    assert "Пауза" in html


# =============================================================================
# План 02-11: грани сводного списка, оставшиеся без утверждения
# =============================================================================
#
# Отчёт верификации признал SCH-04 и SCH-05 выполненными, но три грани списка
# ничем не удерживались: различимость двух ОДИНАКОВЫХ расписаний, различие двух
# пустых состояний одним утверждением и СТАБИЛЬНОСТЬ порядка карточек. Порядок
# задан явной сортировкой (`app/pages/schedules.py` — `.order_by(Schedule.id)` в
# `schedules_list` и в `schedules_partial`), поэтому тесты ниже ЗАКРЕПЛЯЮТ уже
# существующее свойство. Незакреплённое, оно исчезает при первой же правке
# запроса — и исчезает молча: страница остаётся валидной, а порция прокрутки
# начинает дублировать и пропускать карточки.


def _card_ids(html: str) -> list[int]:
    """Идентификаторы расписаний в ПОРЯДКЕ отрисовки карточек.

    Якорь — `id` элемента карточки из `schedules/includes/schedule_row.html`.
    Утверждать порядок по именам групп или заголовкам объявлений нельзя: у
    одинаковых расписаний они совпадают, а различить нужно именно карточки.
    """
    return [int(value) for value in re.findall(r'id="schedule-row-(\d+)"', html)]


@pytest.mark.asyncio
async def test_two_identical_schedules_render_as_two_cards(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """SCH-04: два неразличимых по данным расписания — две карточки, не одна.

    Совпадают объявление, аккаунт, группа, дни и времена: различает их только
    идентификатор. Схлопывание таких расписаний в одну карточку (группировкой,
    `DISTINCT` или отбором по ключу шаблона) спрятало бы от пользователя
    вторую отправку, которая при этом реально произойдёт. Счётчик найденных
    обязан считать обе — иначе подпись и список разъедутся.
    """
    ad = await _seed_ad(db_session, title="Объявление-двойник")
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Общая группа двойников")
    first = await _seed_schedule(
        db_session, ad, account, group_ids=[group.id], days=[0, 2], times=["09:30"]
    )
    second = await _seed_schedule(
        db_session, ad, account, group_ids=[group.id], days=[0, 2], times=["09:30"]
    )

    html = (await authed_client.get("/schedules")).text

    assert _card_ids(html) == [first.id, second.id], (
        "одинаковые расписания схлопнулись в одну карточку"
    )
    assert "2 расписания" in html, "счётчик найденных не посчитал оба расписания"


@pytest.mark.asyncio
async def test_two_empty_states_differ(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """UI-SPEC E13/E14 `empty`: ноль расписаний и ноль совпадений — не одно и то же.

    Соседние тесты проверяют каждое состояние по отдельности и остались бы
    зелёными, даже если бы оба текста совпали. Здесь утверждается именно
    РАЗЛИЧИЕ: пользователю, отфильтровавшему всё до нуля, нельзя предлагать
    идти создавать расписание — у него их достаточно, ему нужен сброс фильтра.
    Полоса фильтров рендерится в обоих случаях, иначе снять фильтр нечем.
    """
    empty = (await authed_client.get("/schedules")).text

    ad = await _seed_ad(db_session, title="Объявление единственного канала")
    account = await _seed_account(db_session, type_="wa")
    await _seed_schedule(db_session, ad, account)
    no_matches = (await authed_client.get("/schedules?channel=tg_user")).text

    assert "Расписаний пока нет" in empty
    assert "Расписания не найдены" not in empty

    assert "Расписания не найдены" in no_matches
    assert "Расписаний пока нет" not in no_matches, (
        "нулевой результат отбора неотличим от отсутствия расписаний"
    )

    assert not _card_ids(empty) and not _card_ids(no_matches)
    for html in (empty, no_matches):
        assert 'id="schedules-filters"' in html, (
            "полоса фильтров исчезла вместе со списком — снять фильтр нечем"
        )


@pytest.mark.asyncio
async def test_card_order_is_stable_across_reloads_and_pages(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Порядок задан явно и стабилен: порция прокрутки не дублирует и не теряет.

    Без ЯВНОЙ сортировки порядок строк — свойство плана запроса, а не контракта.
    Стоит ему поплыть между двумя запросами, и бесконечная прокрутка покажет
    одну карточку дважды, а другую не покажет вовсе. Расписания посеяны
    неразличимыми по данным намеренно — тогда единственное, что может задавать
    порядок, это сортировка по идентификатору.

    ⚠️ ПРЕЖНЯЯ РЕДАКЦИЯ АБЗАЦА ОСТАВЛЕНА НАЗВАННОЙ, А НЕ СТЁРТОЙ (идиома
    D-30/D-32). Она говорила «смещение 30 отсчитывается уже по ДРУГОЙ
    последовательности» — довод был верен ДЛЯ СВОЕЙ ФОРМЫ курсора и снят вместе
    с ней планом 11-04 (D-11). Предмет правила не изменился: сортировка
    утверждается как свойство ВЫПОЛНЕННОГО запроса на обоих входах.

    ⚠️ АДРЕС ПОРЦИИ БОЛЬШЕ НЕ СОБИРАЕТСЯ ТЕСТОМ. Собранный тестом, он знал бы
    форму курсора наизусть: на ключевом курсоре `?offset=30` попал бы в
    НЕИЗВЕСТНЫЙ маршруту параметр, тот молча вернул бы ПЕРВУЮ страницу, и тест
    сообщил бы о порядке вместо разорванной цепочки (то же основание, что у
    `test_infinite_scroll_chain`, план 09-13).
    """
    ad = await _seed_ad(db_session, title="Объявление длинного списка")
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа длинного списка")
    seeded = [
        (
            await _seed_schedule(
                db_session, ad, account, group_ids=[group.id], times=["09:30"]
            )
        ).id
        for _ in range(PAGE_SIZE + 5)
    ]

    with _statement_log(db_session) as page_statements:
        first_html = (await authed_client.get("/schedules")).text
    first_page = _card_ids(first_html)
    with _statement_log(db_session) as chunk_statements:
        chunk = _card_ids((await authed_client.get(_sentinel_url(first_html))).text)

    # Совпадение порядка с посевом само по себе доказывает мало: без ORDER BY
    # SQLite всё равно вернул бы строки в порядке rowid, и утверждение было бы
    # зелено на запросе, порядок которого не задан вовсе. Поэтому явная
    # сортировка утверждается КАК СВОЙСТВО ВЫПОЛНЕННОГО ЗАПРОСА — на обоих
    # входах, потому что расходятся они именно попарно.
    for label, statements in (("страница", page_statements), ("порция", chunk_statements)):
        assert [s for s in statements if SCHEDULES_ORDER_RE.search(s)], (
            f"{label} сводного списка выполнена запросом без явной сортировки — "
            "порядок карточек стал свойством плана запроса, а не контракта"
        )

    assert first_page == seeded[:PAGE_SIZE], "первая страница отдана не по порядку"
    assert chunk == seeded[PAGE_SIZE:], "порция прокрутки продолжила не с того места"

    combined = first_page + chunk
    assert len(combined) == len(set(combined)), (
        "карточка попала и на страницу, и в порцию прокрутки"
    )
    assert sorted(combined) == sorted(seeded), "порция и страница вместе неполны"

    assert _card_ids((await authed_client.get("/schedules")).text) == first_page, (
        "повторный запрос той же страницы дал другой порядок карточек"
    )


@pytest.mark.asyncio
async def test_toggling_does_not_move_the_card(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """SCH-05: переключение меняет состояние расписания, а не его место в списке.

    Список отсортирован по идентификатору, а не по состоянию или по времени
    изменения, поэтому поставленная на паузу карточка обязана остаться там же.
    Сортировка, зависящая от `is_active`, превратила бы каждое нажатие в прыжок
    списка под курсором: пользователь, останавливающий несколько расписаний
    подряд, нажимал бы вслепую.
    """
    ad = await _seed_ad(db_session, title="Объявление трёх расписаний")
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа трёх расписаний")
    schedules = [
        await _seed_schedule(
            db_session, ad, account, group_ids=[group.id], times=[f"0{i}:30"]
        )
        for i in range(3)
    ]
    middle = schedules[1]

    before = _card_ids((await authed_client.get("/schedules")).text)

    response = await authed_client.post(
        f"/schedules/{middle.id}/toggle", follow_redirects=False
    )
    assert response.status_code == 302
    await db_session.refresh(middle)
    assert middle.is_active is False, "переключение не изменило состояние"

    after_html = (await authed_client.get("/schedules")).text

    assert _card_ids(after_html) == before, "переключение сдвинуло карточку в списке"
    toggle = after_html[
        after_html.index(f'id="schedule-toggle-{middle.id}"') :
    ].split(">", 1)[0]
    assert "checked" not in toggle, "тумблер показывает состояние, которого нет в базе"


# =============================================================================
# План 11-04: КЛЮЧЕВОЙ КУРСОР СВОДНОГО СПИСКА (D-11)
# =============================================================================
#
# Основание — CR-01 Фазы 9, воспроизведённый на этом экране. Смещённый курсор
# отсчитывает ПОРЯДКОВЫЙ НОМЕР по СЕГОДНЯШНЕЙ выдаче; фрагментный тумблер под
# фильтром состояния выводит строку ИЗ выдачи, выдача сдвигается на единицу, и
# порция по адресу, снятому ДО нажатия, пропускает ровно одну строку. Ключевой
# курсор считает от ИДЕНТИФИКАТОРА последней отрисованной строки, и сдвиг
# выдачи его не двигает — класс отказа становится НЕВЫРАЗИМЫМ формой контракта,
# а не ловится сверкой.

# Сентинел бесконечной прокрутки — единственный `hx-get`, ведущий на порцию
# этого раздела.
SENTINEL_RE = re.compile(r'hx-get="([^"]*/schedules/partial\?[^"]*)"')


def _sentinel_url(html: str) -> str:
    """Адрес следующей порции — ТОТ, КОТОРЫЙ ДАЛА СТРАНИЦА, а не собранный тестом.

    Тест, собирающий адрес сам, знает форму курсора наизусть: на смене формы он
    покраснел бы «нет смещения», то есть обвинил бы ФОРМУ вместо разорванной
    цепочки. Ровно это основание записано у `test_infinite_scroll_chain`
    (tests/test_pages/test_htmx_preserved.py, план 09-13), и здесь оно то же.
    """
    urls = SENTINEL_RE.findall(html)
    assert urls, "сентинела бесконечной прокрутки нет на странице"
    return urls[-1]


@pytest.mark.asyncio
async def test_the_next_portion_does_not_skip_a_row_after_a_toggle_under_the_state_filter(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-11: тумблер под фильтром состояния не съедает строку следующей порции.

    ⚠️ АДРЕС ПОРЦИИ СНИМАЕТСЯ ДО НАЖАТИЯ, И ЭТО НЕ УДОБСТВО ТЕСТА, А ТО, КАК
    ДЕРЖИТ ЕГО БРАУЗЕР. Сентинел отрисован ПЕРВОЙ порцией и переживает нажатие:
    человек, поставивший строку на паузу и докрутивший до низа, уходит на сервер
    по адресу, вычисленному до того, как выдача сдвинулась.

    Предмет теста — КУРСОР, а не форма ответа тумблера: запись паузы исполняется
    при любом ответе, поэтому утверждается состояние в базе, а не код ответа.
    """
    ad = await _seed_ad(db_session, title="Объявление под фильтром состояния")
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа под фильтром состояния")
    seeded = [
        (
            await _seed_schedule(
                db_session, ad, account, group_ids=[group.id], is_active=True
            )
        ).id
        for _ in range(PAGE_SIZE + 5)
    ]

    first = await authed_client.get("/schedules?state=active")
    assert first.status_code == 200
    assert _card_ids(first.text) == seeded[:PAGE_SIZE], (
        "первая порция под фильтром отдана не по порядку"
    )
    sentinel = _sentinel_url(first.text)

    # Пауза строки ИЗ ПЕРВОЙ порции запросом со сводного списка (признака
    # возврата строка не шлёт): под фильтром `active` строка выходит из выдачи.
    paused_id = seeded[0]
    response = await authed_client.post(
        f"/schedules/{paused_id}/toggle",
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )
    assert response.status_code in (200, 204), (
        f"тумблер со сводного списка ответил {response.status_code} слою письма"
    )
    paused_row = await db_session.get(Schedule, paused_id)
    await db_session.refresh(paused_row)
    assert paused_row.is_active is False, "тумблер не поставил строку на паузу"

    rest = await authed_client.get(sentinel)
    assert rest.status_code == 200

    assert _card_ids(rest.text) == seeded[PAGE_SIZE:], (
        "следующая порция потеряла строку: курсор отсчитывает СМЕЩЕНИЕ по "
        "выдаче, из которой тумблер вывел строку первой порции — дословно CR-01 "
        "Фазы 9 (D-11). Ключевой курсор считает от идентификатора последней "
        "отрисованной строки и сдвигом выдачи не двигается"
    )


# =============================================================================
# План 11-04, задача 2: ТУМБЛЕР СВОДНОГО СПИСКА ОТВЕЧАЕТ СВОЕЙ СТРОКОЙ (D-02)
# =============================================================================
#
# Экранов у тумблера ДВА, и узнаётся экран признаком возврата: редактор шлёт
# его, строка сводного списка — нет. Ответ обязан подменять ровно строку ТОГО
# экрана, откуда пришла форма, и всегда показывать СЕРВЕРНОЕ состояние.

# Узел строки ответа — первый верхнеуровневый узел тела (`schedule_row`).
ROW_ARTICLE = '<article class="sched-item" id="schedule-row-{schedule_id}">'


def _row_toggle_markup(html: str, schedule_id: int) -> str:
    """Разметка тумблера строки — узел `label.toggle` по его `for`.

    Узел берётся по идентификатору тумблера, а не срезом за адресом маршрута:
    форма строки идёт через макрос-обёртку, и адрес печатается ДВАЖДЫ подряд —
    в `action` и в атрибуте отправки слоя письма, — поэтому срез попал бы между
    ними (прибор плана 11-03, `tests/test_pages/test_editor_schedules.py`).
    """
    match = re.search(
        rf'<label class="toggle" for="schedule-toggle-{schedule_id}"[^>]*>.*?</label>',
        html,
        re.S,
    )
    assert match, f"тумблера строки {schedule_id} в разметке нет"
    return match.group(0)


@pytest.mark.asyncio
async def test_the_list_toggle_answers_with_its_own_row_over_htmx(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Со сводного списка ответ — СТРОКА этого экрана, а не карточка редактора.

    Признака возврата строка не шлёт, и по его отсутствию обработчик выбирает
    форму ответа (D-02). Фрагмент редактора, приехавший сюда, приземлиться не
    смог бы: цели `#sched-N` на сводном списке нет вовсе.

    Путь деградации проверяется на ВТОРОЙ строке: первая половина уже сменила
    состояние, и переиспользованная строка проверяла бы не тот исход.
    """
    ad = await _seed_ad(db_session, title="Объявление строки списка")
    account = await _seed_account(db_session)
    group = await _seed_group(db_session, account, "Группа строки списка")
    schedule = await _seed_schedule(
        db_session, ad, account, group_ids=[group.id], is_active=True
    )
    degraded_row = await _seed_schedule(
        db_session, ad, account, group_ids=[group.id], is_active=True
    )

    response = await authed_client.post(
        f"/schedules/{schedule.id}/toggle",
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )

    assert response.status_code == 200, (
        f"слою письма ответили {response.status_code} вместо 200 со строкой"
    )
    assert "<!DOCTYPE" not in response.text, (
        "слою письма приехал ЦЕЛЫЙ ДОКУМЕНТ — обработчик ответил переходом"
    )
    assert response.text.lstrip().startswith(
        ROW_ARTICLE.format(schedule_id=schedule.id)
    ), (
        "первый верхнеуровневый узел тела — не строка своего экрана: "
        f"{response.text.lstrip()[:200]!r}"
    )
    await db_session.refresh(schedule)
    assert schedule.is_active is False, "тумблер не поставил строку на паузу"
    assert "checked" not in _row_toggle_markup(response.text, schedule.id), (
        "строка ответа показывает состояние, которого нет в базе"
    )

    # Путь деградации не тронут: без признака — прежнее перенаправление.
    without = await authed_client.post(
        f"/schedules/{degraded_row.id}/toggle", follow_redirects=False
    )
    assert without.status_code == 302
    assert without.headers["location"] == "/schedules"


@pytest.mark.asyncio
async def test_a_blocked_resume_from_the_list_returns_the_row_unchanged(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Фрагмент строки ВСЕГДА отражает сервер (D-11, D-13/D-16 Фазы 9).

    Неполное расписание возобновить нельзя, и браузер уже переключил флажок
    ОПТИМИСТИЧНО. Молчание оставило бы человека с включённым на вид тумблером
    выключенной строки; строка в прежнем состоянии возвращает флажок на место.
    """
    ad = await _seed_ad(db_session, title="Неполное расписание сводного списка")
    schedule = await _seed_schedule(db_session, ad, account=None, is_active=False)

    response = await authed_client.post(
        f"/schedules/{schedule.id}/toggle",
        headers={"HX-Request": "true"},
        follow_redirects=False,
    )

    assert response.status_code == 200, (
        f"заблокированное возобновление ответило {response.status_code} вместо "
        "строки с серверным состоянием"
    )
    assert response.text.lstrip().startswith(
        ROW_ARTICLE.format(schedule_id=schedule.id)
    ), "ответ не начинается со строки своего экрана"
    await db_session.refresh(schedule)
    assert schedule.is_active is False, "сервер принял возобновление неполного"

    toggle = _row_toggle_markup(response.text, schedule.id)
    assert "checked" not in toggle, (
        "оптимистично переключённый флажок не встал обратно: строка ответа "
        "показывает состояние, которого сервер не принял"
    )
    assert "disabled" in toggle, "тумблер неполного расписания доступен к нажатию"
