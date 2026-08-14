"""История отправок: фильтры-чипсы и счётчик найденного (HIST-01).

Собственного файла тестов у раздела истории до Фазы 4 не было: его обещания
были размазаны по сплошному обходу разметки (`test_responsive_markup.py`) и по
файлу сохранности HTMX (`test_htmx_preserved.py`). Оба продолжают держать своё
— примитив записи и проброс фильтров в сентинеле прокрутки, — и сюда НЕ
переносятся и НЕ дублируются: два теста одного свойства расходятся при первой
же правке, и красным оказывается тот, который правили последним.

Этот файл держит то, чего не держал никто: набор значений чипсов, устойчивость
выбора к мусору в адресе, сохранение остальных фильтров при переходе по чипсу и
совпадение числа над списком с фактической выдачей тех же фильтров (D-31).
"""

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import (
    STATUS_ACCOUNT_DISCONNECTED,
    STATUS_FAIL,
    STATUS_OK,
)
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.models.user import User
from app.pages.history import MESSENGER_CHIPS, PERIOD_CHIPS, STATUS_CHIPS

# --- посев --------------------------------------------------------------------


async def _current_user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_send_log(
    db: AsyncSession,
    user_id: int,
    *,
    status: str = STATUS_OK,
    messenger_type: str | None = "wa",
    sent_at: datetime | None = None,
    group_id: int | None = None,
    ad_title: str = "Отправка объявления",
) -> SendLog:
    log = SendLog(
        user_id=user_id,
        group_id=group_id,
        ad_title=ad_title,
        ad_text="Текст отправленного объявления",
        ad_images=[],
        group_name="Группа отправки",
        messenger_type=messenger_type,
        task_id="task-9f3c1d",
        status=status,
        sent_at=sent_at or datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    return log


async def _seed_account_with_group(
    db: AsyncSession, user_id: int, *, seq: str = "1"
) -> tuple[MessengerAccount, Group]:
    account = MessengerAccount(
        user_id=user_id, type="wa", credentials="creds", status="active"
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    group = Group(
        user_id=user_id,
        account_id=account.id,
        messenger_type="wa",
        group_external_id=f"-300{seq}",
        name=f"Группа аккаунта {seq}",
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return account, group


# --- разбор разметки ----------------------------------------------------------
#
# Чипсы опознаются по АТРИБУТАМ, а не по подписям: подпись — предмет
# редактуры, атрибут — контракт разметки. Тест на подписи краснел бы на смене
# слова «Ошибка» на «Неудача», то есть на копирайтинге, а не на потерянном
# фильтре.

_CHIPSET_RE_TMPL = r'<div class="chip-set" data-chipset="{name}">(.*?)</div>'
_A_TAG_RE = re.compile(r"<a\b[^>]*>", re.DOTALL)


def _page_body(html: str) -> str:
    """Тело страницы без шелла: навигация несёт те же слова, что и подписи."""
    marker = "<div data-body>"
    assert marker in html, "шелл изменился — тело страницы больше не размечено"
    return html[html.index(marker) :]


def _attr(tag: str, name: str) -> str:
    match = re.search(rf'{name}="([^"]*)"', tag)
    return match.group(1) if match else ""


def _chips(html: str, chipset: str) -> list[tuple[str, str, bool]]:
    """Чипсы группы: (значение, адрес, активен)."""
    match = re.search(
        _CHIPSET_RE_TMPL.format(name=re.escape(chipset)), html, re.DOTALL
    )
    assert match, f"группа чипсов {chipset!r} не найдена"
    return [
        (_attr(tag, "data-chip"), _attr(tag, "href"), "chip--on" in _attr(tag, "class"))
        for tag in _A_TAG_RE.findall(match.group(1))
    ]


def _chip_values(html: str, chipset: str) -> list[str]:
    return [value for value, _, _ in _chips(html, chipset)]


def _active_chips(html: str, chipset: str) -> list[str]:
    return [value for value, _, active in _chips(html, chipset) if active]


def _href_of(html: str, chipset: str, value: str) -> str:
    for chip_value, href, _ in _chips(html, chipset):
        if chip_value == value:
            return href
    raise AssertionError(f"чипса {value!r} нет в группе {chipset!r}")


def _titles(html: str) -> list[str]:
    """Заголовки отрисованных записей — по ним видно, что именно попало в выдачу."""
    return re.findall(r"<span data-grow>([^<]*)</span>", html)


def _counter(html: str) -> int | None:
    """Число над списком либо None, если линейки счётчика нет."""
    match = re.search(r'data-hcount="(\d+)"', html)
    return int(match.group(1)) if match else None


def _counter_text(html: str) -> str:
    """Подпись счётчика целиком — по ней видно склонение."""
    match = re.search(r'data-hcount="\d+"[^>]*>\s*<span[^>]*>([^<]*)</span>', html)
    assert match, "линейка счётчика не найдена"
    return match.group(1).strip()


# =============================================================================
# Задача 1: чипсы-ссылки для статуса, канала и периода
# =============================================================================


@pytest.mark.asyncio
async def test_status_chips_cover_all_three_journal_statuses(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Три значения журнала, а не два.

    Прежний выпадающий список знал «Успешные» и «Ошибки» и терял
    `account_disconnected` — единственный статус, по которому видно, что
    отправка не ушла из-за отвалившегося аккаунта, а не из-за мессенджера.
    Отфильтровать такие отправки было НЕЧЕМ.
    """
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id)

    html = _page_body((await authed_client.get("/history")).text)

    assert _chip_values(html, "status") == [
        "",
        STATUS_OK,
        STATUS_FAIL,
        STATUS_ACCOUNT_DISCONNECTED,
    ]


@pytest.mark.asyncio
async def test_messenger_chips_cover_all_three_channels(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Каналов у проекта три: Telegram, WhatsApp и MAX."""
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id)

    html = _page_body((await authed_client.get("/history")).text)

    assert _chip_values(html, "messenger") == ["", "tg_user", "wa", "max"]


@pytest.mark.asyncio
async def test_period_chips_cover_four_options(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Сегодня, 7 дней, 30 дней и «всё время» — произвольного диапазона нет (D-30)."""
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id)

    html = _page_body((await authed_client.get("/history")).text)

    assert _chip_values(html, "period") == ["today", "7d", "30d", ""]


@pytest.mark.asyncio
async def test_chip_sets_are_declared_on_the_server(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Перечни значений объявлены обработчиком, а не выписаны в разметке.

    Разметка точкой принуждения не является: значение приходит строкой запроса
    и обязано отсекаться сервером. Перечень, живущий в шаблоне, отсекать не
    может — он только рисует.
    """
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id)

    html = _page_body((await authed_client.get("/history")).text)

    for chipset, declared in (
        ("status", STATUS_CHIPS),
        ("messenger", MESSENGER_CHIPS),
        ("period", PERIOD_CHIPS),
    ):
        assert _chip_values(html, chipset) == [value for value, _ in declared], chipset


@pytest.mark.asyncio
async def test_status_chip_filters_the_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """При статусе «Ошибка» в ответе остаются только неуспешные отправки."""
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id, status=STATUS_OK, ad_title="Успешная")
    await _seed_send_log(db_session, user.id, status=STATUS_FAIL, ad_title="Неудачная")

    html = _page_body((await authed_client.get(f"/history?status={STATUS_FAIL}")).text)

    assert _titles(html) == ["Неудачная"]


@pytest.mark.asyncio
async def test_account_disconnected_chip_filters_the_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Статус отключённого аккаунта отбирается СВОИМ чипсом, а не вместе с ошибками."""
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id, status=STATUS_FAIL, ad_title="Неудачная")
    await _seed_send_log(
        db_session,
        user.id,
        status=STATUS_ACCOUNT_DISCONNECTED,
        ad_title="Аккаунт отвалился",
    )

    response = await authed_client.get(f"/history?status={STATUS_ACCOUNT_DISCONNECTED}")
    assert response.status_code == 200
    assert _titles(_page_body(response.text)) == ["Аккаунт отвалился"]


@pytest.mark.asyncio
async def test_messenger_chip_filters_the_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Канал MAX отбирается чипсом канала."""
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id, messenger_type="wa", ad_title="Через WA")
    await _seed_send_log(db_session, user.id, messenger_type="max", ad_title="Через MAX")

    response = await authed_client.get("/history?messenger=max")
    assert response.status_code == 200
    assert _titles(_page_body(response.text)) == ["Через MAX"]


@pytest.mark.asyncio
async def test_period_today_cuts_at_user_local_midnight(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Период «сегодня» отсчитывается от локальной полуночи ЧИТАТЕЛЯ (D-30).

    Границы считаются той же формулой, что и в модуле аналитики, поэтому тест
    детерминирован в любой час суток: реализация, отсекающая по UTC-полуночи,
    у пользователя UTC+3 всегда роняет одну из двух записей не на ту сторону.
    """
    user = await _current_user(db_session)
    user.timezone = "Europe/Moscow"
    await db_session.commit()

    tz = ZoneInfo("Europe/Moscow")
    cutoff = (
        datetime.now(tz)
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .astimezone(timezone.utc)
    )
    await _seed_send_log(
        db_session, user.id, sent_at=cutoff + timedelta(minutes=1), ad_title="Сегодняшняя"
    )
    await _seed_send_log(
        db_session, user.id, sent_at=cutoff - timedelta(minutes=1), ad_title="Вчерашняя"
    )

    response = await authed_client.get("/history?period=today")
    assert response.status_code == 200
    assert _titles(_page_body(response.text)) == ["Сегодняшняя"]


@pytest.mark.asyncio
async def test_active_chip_is_marked_and_the_others_are_not(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Активный чипс несёт признак активности; активный в группе ровно один.

    Признак на всех сразу и признак ни на одном одинаково молчаливы: страница
    отдаёт 200 и выглядит исправной, а выбранный фильтр по ней не читается.
    """
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id)

    html = _page_body((await authed_client.get(f"/history?status={STATUS_FAIL}")).text)

    assert _active_chips(html, "status") == [STATUS_FAIL]
    # Без фильтра канала активен чипс «все» — не пустота
    assert _active_chips(html, "messenger") == [""]
    assert _active_chips(html, "period") == [""]


@pytest.mark.asyncio
async def test_chip_link_keeps_the_other_filters(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Переход по чипсу сохраняет остальные активные фильтры в адресе.

    Потерянный при переходе фильтр не роняет страницу — он молча подмешивает
    записи, которые пользователь только что отфильтровал.
    """
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id)

    html = _page_body(
        (await authed_client.get(f"/history?status={STATUS_OK}&messenger=wa")).text
    )

    href = _href_of(html, "period", "7d")
    assert "period=7d" in href, href
    assert f"status={STATUS_OK}" in href, href
    assert "messenger=wa" in href, href


@pytest.mark.asyncio
async def test_all_chip_drops_only_its_own_filter(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Чипс «все» снимает СВОЮ ось и не трогает соседние."""
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id)

    html = _page_body(
        (await authed_client.get(f"/history?status={STATUS_OK}&messenger=wa")).text
    )

    href = _href_of(html, "status", "")
    assert "status=" not in href, href
    assert "messenger=wa" in href, href


@pytest.mark.asyncio
async def test_chips_are_links_and_need_no_javascript(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Чипс — обычная ссылка: смена фильтра работает при выключенном JavaScript.

    Кнопка с обработчиком отдала бы ту же разметку и тот же 200, а при
    выключенном JavaScript не делала бы ничего.
    """
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id)

    html = _page_body((await authed_client.get("/history")).text)

    match = re.search(
        _CHIPSET_RE_TMPL.format(name="status"), html, re.DOTALL
    )
    assert match, "группа чипсов статуса не найдена"
    block = match.group(1)
    assert "<button" not in block, "чипс сделан кнопкой — без JavaScript он мёртв"
    assert "x-on:click" not in block and "hx-get" not in block, block
    for _, href, _ in _chips(html, "status"):
        assert href.startswith("/history"), href


@pytest.mark.asyncio
async def test_record_without_messenger_survives_the_all_chip(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Старая запись с пустым каналом видна при варианте «все» и только при нём.

    Скрывать её из «всех» нельзя: это настоящая отправка, случившаяся до того,
    как канал стали писать в журнал. Спрятанная, она исчезла бы из истории
    навсегда и не сошлась бы ни с одним счётчиком.
    """
    user = await _current_user(db_session)
    await _seed_send_log(
        db_session, user.id, messenger_type=None, ad_title="Отправка без канала"
    )
    await _seed_send_log(db_session, user.id, messenger_type="wa", ad_title="Через WA")

    all_html = _page_body((await authed_client.get("/history")).text)
    assert "Отправка без канала" in all_html

    wa_html = _page_body((await authed_client.get("/history?messenger=wa")).text)
    assert "Отправка без канала" not in wa_html
    assert "Через WA" in wa_html


@pytest.mark.asyncio
async def test_account_dropdown_survives_a_chip_switch(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Фильтр по аккаунту сохранён выпадающим списком и переживает смену чипса (D-29).

    Аккаунтов может быть много, и чипсами полоса переполнилась бы; список
    остаётся, но обязан ехать в адресе чипса — иначе выбор аккаунта сбрасывался
    бы каждым нажатием на статус.
    """
    user = await _current_user(db_session)
    account, group = await _seed_account_with_group(db_session, user.id)
    await _seed_send_log(
        db_session, user.id, group_id=group.id, ad_title="На аккаунте"
    )
    await _seed_send_log(db_session, user.id, ad_title="Без группы")

    response = await authed_client.get(f"/history?account_id={account.id}")
    assert response.status_code == 200
    html = _page_body(response.text)

    assert _titles(html) == ["На аккаунте"]
    assert 'name="account_id"' in html, "выпадающий список аккаунта пропал"
    assert f"account_id={account.id}" in _href_of(html, "status", STATUS_FAIL)


@pytest.mark.asyncio
async def test_account_filter_cannot_reach_another_users_records(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-24: чужой идентификатор аккаунта в фильтре не открывает чужих записей.

    Условие владения стоит ДО применения фильтров, поэтому фильтр аккаунта
    только сужает выборку внутри записей текущего пользователя.
    """
    user = await _current_user(db_session)
    stranger = User(email="stranger@test.com", password_hash="x", name="Чужой")
    db_session.add(stranger)
    await db_session.commit()
    await db_session.refresh(stranger)

    _, foreign_group = await _seed_account_with_group(db_session, stranger.id, seq="9")
    await _seed_send_log(
        db_session, stranger.id, group_id=foreign_group.id, ad_title="Чужая отправка"
    )

    response = await authed_client.get(
        f"/history?account_id={foreign_group.account_id}"
    )
    assert response.status_code == 200
    assert "Чужая отправка" not in response.text


@pytest.mark.asyncio
async def test_unknown_filter_values_do_not_break_the_page(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-23: значение вне допустимого набора не применяется и не роняет страницу.

    Значение приезжает из query-строки, то есть из ссылки, закладки или чужого
    сообщения. Пятисотка на подобранном вручную мусоре — отказ в обслуживании;
    молча применённый мусор — пустой список без единого активного чипса, по
    которому непонятно, что вообще произошло.
    """
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id, ad_title="Единственная отправка")

    for query in (
        "status=не-такой-статус",
        "messenger=не-такой-канал",
        "period=не-такой-период",
        "account_id=не-число",
        "status='; DROP TABLE send_logs--",
    ):
        response = await authed_client.get(f"/history?{query}")
        assert response.status_code == 200, query
        html = _page_body(response.text)
        assert _titles(html) == ["Единственная отправка"], query


@pytest.mark.asyncio
async def test_unknown_filter_value_leaves_the_all_chip_active(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Мусорное значение оси не оставляет полосу чипсов без активного варианта."""
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id)

    html = _page_body(
        (await authed_client.get("/history?status=не-такой-статус")).text
    )

    assert _active_chips(html, "status") == [""]


@pytest.mark.asyncio
async def test_reset_link_appears_only_with_active_filters(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Кнопка сброса по макету: она есть, когда есть что сбрасывать."""
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id)

    clean = _page_body((await authed_client.get("/history")).text)
    assert "data-chipreset" not in clean

    filtered = _page_body(
        (await authed_client.get(f"/history?status={STATUS_OK}")).text
    )
    assert 'data-chipreset href="/history"' in filtered


def test_messenger_chips_match_the_channel_axis_of_the_project():
    """Значения канала не расходятся с осью канала сводного списка расписаний.

    Связь закреплена ТЕСТОМ, а не импортом: ось расписаний описывает другой
    экран, и импорт объявил бы одну ось определением другой. Разойтись им при
    этом нельзя — канал у проекта один и тот же, и чипс, отбирающий по
    значению, которого не пишет ни один аккаунт, не отберёт ничего никогда.
    """
    from app.pages.schedules import CHANNEL_FILTER_VALUES

    assert tuple(value for value, _ in MESSENGER_CHIPS if value) == CHANNEL_FILTER_VALUES


def test_period_chips_cover_every_period_the_module_knows():
    """Каждый период модуля аналитики имеет свой чипс.

    Период, заведённый в HISTORY_PERIODS и не показанный чипсом, недостижим с
    экрана: он работает по прямой ссылке и не существует для пользователя.
    """
    from app.application.analytics.send_analytics import HISTORY_PERIODS

    assert tuple(value for value, _ in PERIOD_CHIPS if value) == HISTORY_PERIODS


@pytest.mark.asyncio
async def test_filter_chips_template_lives_outside_the_component_library():
    """Новый шаблон положен в каталог включений раздела, а не в библиотеку.

    Инвентаризация библиотеки компонентов фиксирует число файлов ровно 13
    (`test_template_inventory`). Файл, положенный туда, потребовал бы правки
    константы в том же плане — то есть сдвинул бы инвентаризацию под своё же
    появление, а именно она и ловит молчаливое пополнение библиотеки.
    """
    from pathlib import Path

    import app

    templates_dir = Path(app.__file__).parent / "templates"
    assert (templates_dir / "history/includes/filter_chips.html").exists()
    assert len(sorted((templates_dir / "components").glob("*.html"))) == 13


# =============================================================================
# Задача 2: точное число найденного и пустой результат фильтров
# =============================================================================


@pytest.mark.asyncio
async def test_counter_shows_the_number_of_found_records(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Над списком стоит число найденного (D-31)."""
    user = await _current_user(db_session)
    for i in range(3):
        await _seed_send_log(db_session, user.id, ad_title=f"Отправка {i}")

    html = _page_body((await authed_client.get("/history")).text)

    assert _counter(html) == 3


@pytest.mark.asyncio
async def test_counter_counts_beyond_the_first_page(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Число — это число НАЙДЕННОГО, а не число загруженных строк.

    Самая правдоподобная ошибка счётчика — `logs|length`: она даёт верное число
    на любом наборе меньше страницы и молча врёт ровно там, где счётчик и нужен.
    Именно на это число будет опираться потолок выгрузки (план 04-08).
    """
    user = await _current_user(db_session)
    for i in range(35):
        await _seed_send_log(db_session, user.id, ad_title=f"Отправка {i}")

    html = _page_body((await authed_client.get("/history")).text)

    assert _counter(html) == 35
    assert len(_titles(html)) == 30, "страница отдаёт больше 30 записей — посев неверен"


@pytest.mark.asyncio
async def test_counter_follows_the_filters(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """При смене фильтра число меняется соответственно."""
    user = await _current_user(db_session)
    for i in range(4):
        await _seed_send_log(db_session, user.id, status=STATUS_OK)
    await _seed_send_log(db_session, user.id, status=STATUS_FAIL)

    assert _counter(_page_body((await authed_client.get("/history")).text)) == 5
    assert (
        _counter(_page_body((await authed_client.get(f"/history?status={STATUS_OK}")).text))
        == 4
    )
    assert (
        _counter(
            _page_body((await authed_client.get(f"/history?status={STATUS_FAIL}")).text)
        )
        == 1
    )


@pytest.mark.asyncio
async def test_counter_matches_the_full_selection_of_the_same_filters(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Число совпадает с длиной ПОЛНОЙ выборки тех же фильтров.

    Именно это сравнение делает проверяемым обещание плана 04-08 «выгружен
    именно отфильтрованный результат»: выгрузка и счётчик обязаны отвечать
    одним числом на один вопрос. Выборка здесь строится НЕЗАВИСИМО от
    `history_count` — иначе сравнивались бы два вызова одной функции.
    """
    from app.application.analytics.send_analytics import apply_history_filters

    user = await _current_user(db_session)
    for i in range(33):
        await _seed_send_log(
            db_session,
            user.id,
            status=STATUS_OK if i % 3 else STATUS_FAIL,
            messenger_type="wa" if i % 2 else "max",
        )

    query = apply_history_filters(
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user.id),
        status=STATUS_OK,
        messenger_type="wa",
        user=user,
    )
    expected = len((await db_session.execute(query)).all())
    assert expected, "посев не дал ни одной подходящей записи — сравнивать нечего"

    html = _page_body(
        (await authed_client.get(f"/history?status={STATUS_OK}&messenger=wa")).text
    )

    assert _counter(html) == expected


@pytest.mark.asyncio
async def test_counter_ignores_other_users(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-22: счётчик считает записи ТЕКУЩЕГО пользователя.

    Счётчик — самостоятельный запрос, и условие владения в нём приходится
    ставить отдельно: потерянное, оно не роняет ничего и не видно на экране —
    список остаётся своим, а число молча сообщает объём чужого журнала.
    """
    user = await _current_user(db_session)
    stranger = User(email="counter-stranger@test.com", password_hash="x", name="Чужой")
    db_session.add(stranger)
    await db_session.commit()
    await db_session.refresh(stranger)

    await _seed_send_log(db_session, user.id)
    for _ in range(7):
        await _seed_send_log(db_session, stranger.id)

    html = _page_body((await authed_client.get("/history")).text)

    assert _counter(html) == 1


@pytest.mark.asyncio
async def test_counter_is_declined_in_russian(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """«1 запись», «2 записи», «5 записей» — форма выбирается по числу."""
    user = await _current_user(db_session)

    await _seed_send_log(db_session, user.id)
    assert "1 запись" == _counter_text(
        _page_body((await authed_client.get("/history")).text)
    )

    await _seed_send_log(db_session, user.id)
    assert "2 записи" == _counter_text(
        _page_body((await authed_client.get("/history")).text)
    )

    for _ in range(3):
        await _seed_send_log(db_session, user.id)
    assert "5 записей" == _counter_text(
        _page_body((await authed_client.get("/history")).text)
    )


@pytest.mark.asyncio
async def test_empty_filter_result_differs_from_the_empty_journal(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пустой результат ФИЛЬТРОВ — своё состояние со сбросом (D-41).

    Одно общее «Нет записей» называло бы одним словом два разных положения дел,
    и следующий шаг пользователя в них разный: в одном — снять фильтр, в другом
    — завести расписание. Сообщение «здесь появятся отправки» человеку с полным
    журналом и отфильтрованным в ноль экраном просто неправда.
    """
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id, status=STATUS_OK)

    html = _page_body((await authed_client.get(f"/history?status={STATUS_FAIL}")).text)

    assert "Ничего не найдено" in html
    assert "измените фильтры или период" in html
    assert 'href="/history"' in html, "сбросить фильтры нечем"
    assert "Здесь появятся отправки" not in html


@pytest.mark.asyncio
async def test_empty_journal_keeps_the_old_text(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парная половина: без фильтров пустой журнал говорит прежнее.

    Одиночный тест предыдущего свойства зеленел бы и на реализации, которая
    заменила старый текст новым ВЕЗДЕ.
    """
    await _current_user(db_session)

    html = _page_body((await authed_client.get("/history")).text)

    assert "Нет записей" in html
    assert "Здесь появятся отправки" in html
    assert "Ничего не найдено" not in html
    assert _counter(html) is None, "«0 записей» — не сообщение, сообщение несёт пустое состояние"


@pytest.mark.asyncio
async def test_infinite_scroll_sentinel_is_identical_in_page_and_partial():
    """Разметка сентинела на странице и в паршале посимвольно одинакова.

    Инвариант выписан комментарием в обоих файлах и держится ровно до первой
    правки одного из них. Разошедшись, сентинелы теряют фильтр на второй
    странице выдачи: список продолжает выглядеть исправным и молча подмешивает
    к отфильтрованному остальной журнал.
    """
    from pathlib import Path

    import app

    templates_dir = Path(app.__file__).parent / "templates"

    def sentinel(rel: str) -> str:
        source = (templates_dir / rel).read_text(encoding="utf-8")
        lines = [line.strip() for line in source.splitlines() if "hx-trigger" in line]
        assert len(lines) == 1, f"{rel}: сентинелов не один, а {len(lines)}"
        return lines[0]

    assert sentinel("history/list.html") == sentinel("history/partial_cards.html")
