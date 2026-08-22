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
from pathlib import Path
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
    ad_text: str = "Текст отправленного объявления",
    ad_images: list | None = None,
    group_name: str = "Группа отправки",
    task_id: str | None = "task-9f3c1d",
    error_message: str | None = None,
) -> SendLog:
    log = SendLog(
        user_id=user_id,
        group_id=group_id,
        ad_title=ad_title,
        ad_text=ad_text,
        ad_images=ad_images if ad_images is not None else [],
        group_name=group_name,
        messenger_type=messenger_type,
        task_id=task_id,
        status=status,
        error_message=error_message,
        sent_at=sent_at or datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
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


# ⚠️ ЗДЕСЬ СТОЯЛ test_filter_chips_template_lives_outside_the_component_library
# — ТРЕТЬЕ место, пинившее число файлов библиотеки компонентов (13), и
# единственное, утверждавшее, что шаблон чипсов лежит ВНЕ библиотеки.
#
# Его предмет снят планом 06-03, а не сломан им: макрос переехал в
# app/templates/components/filter_chips.html ровно по сроку, назначенному его
# собственным докстрингом («второй потребитель станет поводом для переезда»), и
# потребителей стало трое — история, «Пользователи» и «Логи» админки. Тест
# утверждал обратное текущему устройству проекта и краснел бы на чтении с
# диска, говоря не о том, о чём написан.
#
# Обе половины утверждения ПЕРЕЖИЛИ снос и закреплены в других местах:
#   * число файлов библиотеки — двумя утверждениями в
#     tests/test_pages/test_responsive_markup.py (обе константы подняты до 14
#     тем же коммитом, что и переезд);
#   * место шаблона — тестом test_no_template_imports_the_old_path в
#     tests/test_pages/test_filter_chips.py, который обходит всё дерево
#     шаблонов и ловит возврат старого пути импорта постоянно, а не разово.


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


# =============================================================================
# План 04-07, задача 1: блок ошибки, ограничение по высоте и копирование
# =============================================================================
#
# Текст ошибки — единственное, по чему пользователь понимает, почему его реклама
# не ушла, поэтому все обещания этого блока проверяются ПАРАМИ «есть там, где
# должно быть» и «нет там, где не должно»: одиночное утверждение зеленеет на
# реализации, которая применила ограничение везде или нигде.

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "app" / "templates"
APP_CSS = Path(__file__).resolve().parents[2] / "app" / "static" / "css" / "app.css"

HISTORY_CARD = "history/includes/history_card.html"
HISTORY_DETAIL = "history/detail.html"

# Сток разметки: значение, попавшее в строку разметки, разбирается парсером
# всегда. Перечень тот же, что закрепляет редактор объявления
# (tests/test_templates/test_ads_form_security.py) — второго определения одного
# запрета в проекте не заводится.
MARKUP_SINKS = ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write")

# Разметка, которую браузер НЕ отрисовывает: содержимое <template> попадает в
# документ только через клиентский код. Кнопка копирования объявлена внутри
# такого блока — это и есть «без Alpine её в разметке нет» (D-34).
_TEMPLATE_BLOCK_RE = re.compile(r"<template\b[^>]*>.*?</template>", re.DOTALL)

# Примитив длинного текста ДОСЛОВНО. Ограничение по высоте вводится соседним
# модификатором, а сам примитив трогать нельзя: его свойство «текст читается
# целиком» закреплено полнотой на странице записи и в админской истории.
LONGTEXT_PRIMITIVE = """[data-longtext] {
  display: block; margin: 0;
  font-size: var(--fs-md); line-height: 1.6; color: var(--text-secondary);
  white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere;
}"""

LONG_ERROR = (
    "PeerFloodError: Too many requests to join the group chat -420; "
    "retry after 86400 seconds (account temporarily restricted by Telegram); "
    "the session will stay limited until the flood wait expires"
)


def _template_text(rel: str) -> str:
    return (TEMPLATES_DIR / rel).read_text(encoding="utf-8")


def _outside_templates(html: str) -> str:
    """Разметка без содержимого <template>: ровно то, что видит браузер без JS."""
    return _TEMPLATE_BLOCK_RE.sub("", html)


def _diag_blocks(html: str) -> list[str]:
    """Диагностические блоки, приготовленные сервером для буфера обмена."""
    return re.findall(r'data-diag="([^"]*)"', html)


@pytest.mark.asyncio
async def test_copy_button_is_absent_without_alpine(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-34: без поднявшегося Alpine кнопки копирования в разметке НЕТ.

    Кнопка, отрисованная сервером и мёртвая без JavaScript, — обещание, которого
    страница не выполняет: пользователь жмёт и не получает ничего, причём
    молча. Объявление внутри <template> делает недоступность честной — кнопки
    просто нет.
    """
    user = await _current_user(db_session)
    await _seed_send_log(
        db_session, user.id, status=STATUS_FAIL, error_message="ECONNRESET"
    )

    html = _page_body((await authed_client.get("/history")).text)

    assert "data-copybtn" in html, "кнопка копирования не объявлена вовсе"
    assert "data-copybtn" not in _outside_templates(html), (
        "кнопка копирования отрисована сервером — без Alpine она останется "
        "мёртвой кнопкой, а не отсутствующей"
    )
    template_with_button = [
        block
        for block in _TEMPLATE_BLOCK_RE.findall(html)
        if "data-copybtn" in block
    ]
    assert template_with_button, "кнопка не внутри <template>"
    for block in template_with_button:
        assert "x-if" in block, block[:200]


@pytest.mark.asyncio
async def test_error_block_stays_copyable_without_the_button(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Базовый путь копирования — выделение одним действием, без JavaScript.

    Он и остаётся единственным там, где Alpine не поднялся: кнопки в разметке
    нет, а текст ошибки и идентификатор задачи выделяются одним действием
    средствами CSS.
    """
    user = await _current_user(db_session)
    await _seed_send_log(
        db_session, user.id, status=STATUS_FAIL, error_message=LONG_ERROR
    )

    html = _page_body((await authed_client.get("/history")).text)
    plain = _outside_templates(html)

    assert plain.count("data-selectall") >= 2, (
        "выделение одним действием потеряно: его обязаны нести и текст ошибки, "
        "и значение идентификатора задачи"
    )
    assert LONG_ERROR in plain, "текст ошибки виден только при поднятом Alpine"

    css = APP_CSS.read_text(encoding="utf-8")
    rule = css[css.index("[data-selectall]") : css.index("[data-selectall]") + 200]
    assert "user-select: all" in rule, rule


@pytest.mark.asyncio
async def test_copy_button_carries_the_whole_diagnostic_block(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-33: в буфер уходит диагностический блок, а не голый текст ошибки.

    Голый текст ошибки бесполезен тому, кому его перешлют: без времени, канала,
    группы, объявления и идентификатора задачи по нему нельзя найти ни отправку,
    ни причину.
    """
    user = await _current_user(db_session)
    await _seed_send_log(
        db_session,
        user.id,
        status=STATUS_FAIL,
        messenger_type="max",
        ad_title="Объявление диагностики",
        group_name="Группа диагностики",
        task_id="task-diag-4242",
        error_message="RPCError 500 internal",
    )

    html = _page_body((await authed_client.get("/history")).text)

    blocks = _diag_blocks(html)
    assert len(blocks) == 1, f"диагностических блоков не один, а {len(blocks)}"
    diag = blocks[0]
    for part in (
        "max",
        "Группа диагностики",
        "Объявление диагностики",
        "task-diag-4242",
        "RPCError 500 internal",
    ):
        assert part in diag, f"в диагностическом блоке нет {part!r}: {diag!r}"
    # Время отправки: год достаточно, формат проверять смысла нет — его считает
    # тот же глобал, что печатает время в шапке записи.
    assert str(datetime.now(timezone.utc).year) in diag, diag


def test_copy_handler_checks_the_clipboard_before_reaching_for_it():
    """T-04-29: доступность буфера проверяется ДО обращения к нему.

    Интерфейс буфера существует только в защищённом контексте, а развёртывание
    проекта допускает режим без шифрования. Обращение без проверки — исключение
    в консоли и кнопка, которая молча не работает.
    """
    source = _template_text(HISTORY_CARD)

    assert "isSecureContext" in source, "проверки защищённого контекста нет"
    assert source.index("isSecureContext") < source.index("navigator.clipboard"), (
        "обращение к буферу стоит РАНЬШЕ проверки его доступности"
    )


def test_copy_handler_never_claims_a_copy_that_did_not_happen():
    """T-04-29: сообщение об успехе появляется ТОЛЬКО по свершившемуся копированию.

    Сообщение об успешном копировании, которого не произошло, — прямая ложь:
    пользователь уходит вставлять то, чего в буфере нет.
    """
    source = _template_text(HISTORY_CARD)

    assert "if (!done) return" in source, (
        "признак успеха выставляется без проверки результата записи в буфер"
    )
    # Признак успеха выставляется ровно в одном месте — в охраняемом методе.
    assert source.count("copied = true") == 1, source.count("copied = true")


def test_copy_handler_builds_dom_not_markup():
    """T-04-30: узлы для запасного пути создаются как узлы DOM.

    Уязвимость этого класса — свойство СПОСОБА сборки, а не конкретного
    значения, поэтому проверяется исходник, а не отрисованная страница.
    """
    for rel in (HISTORY_CARD, HISTORY_DETAIL):
        source = _template_text(rel)
        offenders = [sink for sink in MARKUP_SINKS if sink in source]
        assert not offenders, f"{rel}: {offenders}"

    assert "createElement" in _template_text(HISTORY_CARD), (
        "запасной путь копирования собран не узлами DOM"
    )


@pytest.mark.asyncio
async def test_error_block_is_height_limited_only_in_the_list_card(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """D-32: ограничение по высоте живёт в карточке списка и только там.

    Страница записи — то место, куда человек приходит ЗА полным текстом.
    Ограничение, применённое и там, теряло бы гарантию в двух местах ради
    одного.
    """
    user = await _current_user(db_session)
    log = await _seed_send_log(
        db_session, user.id, status=STATUS_FAIL, error_message=LONG_ERROR
    )

    listing = _page_body((await authed_client.get("/history")).text)
    detail = (await authed_client.get(f"/history/{log.id}")).text

    assert "data-clamp" in listing, "карточка списка не несёт модификатора"
    assert "data-clamp" not in detail, (
        "страница записи получила ограничение по высоте — за полным текстом "
        "идти стало некуда"
    )
    # И в ИСХОДНИКЕ страницы записи имени модификатора нет. Утверждение строже
    # предыдущего намеренно: комментарий Jinja до ответа не доезжает, поэтому
    # модификатор, закомментированный «на будущее» или названный контрпримером,
    # прошёл бы проверку по отрисованной странице незамеченным.
    assert "data-clamp" not in _template_text(HISTORY_DETAIL), (
        "имя модификатора ограничения названо в исходнике страницы записи"
    )
    assert LONG_ERROR in listing, "текст ошибки усечён сервером в карточке списка"
    assert LONG_ERROR in detail, "текст ошибки усечён сервером на странице записи"


def test_clamp_expansion_needs_no_javascript():
    """Раскрытие ограниченного блока не зависит от JavaScript.

    Раскрытие обработчиком означало бы, что при выключенном Alpine длинный текст
    ошибки недоступен — ровно то, что D-32 прямо запрещает.
    """
    source = _template_text(HISTORY_CARD)
    start = source.index("<details data-clamp")
    block = source[start : source.index("</details>", start)]

    assert "<summary" in block, "пары «сводка + раскрытие» нет"
    for handler in ("x-on:", "@click", "onclick", "hx-get", "hx-trigger"):
        assert handler not in block, f"раскрытие повешено на обработчик: {handler}"


def test_long_text_primitive_is_untouched():
    """Примитив длинного текста и его запрет усечения остались как были.

    Ограничение по высоте вводится СОСЕДНИМ модификатором именно поэтому:
    правка примитива распространила бы усечение на страницу записи, на
    админскую историю и на снапшот текста объявления разом.
    """
    css = APP_CSS.read_text(encoding="utf-8")

    assert LONGTEXT_PRIMITIVE in css, "примитив длинного текста изменён"
    assert "Ни усечения, ни многоточия, ни скрытия за" in css, (
        "комментарий, дословно запрещающий усечение, изменён или удалён"
    )
    assert "[data-clamp]" in css, "правила модификатора ограничения нет"


@pytest.mark.asyncio
async def test_successful_record_has_neither_error_block_nor_copy_button(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """У успешной записи копировать нечего и объяснять нечего."""
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id, status=STATUS_OK)

    html = _page_body((await authed_client.get("/history")).text)

    assert 'data-area="err"' not in html
    assert "data-copybtn" not in html


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status", [STATUS_FAIL, STATUS_ACCOUNT_DISCONNECTED, "обрыв-связи"]
)
async def test_every_unsuccessful_record_offers_the_copy_button(
    status: str, authed_client: AsyncClient, db_session: AsyncSession
):
    """Неуспешная — это «не успешная», а не «из известного списка неудач».

    Перечень неудачных статусов конечен ровно до появления следующего: запись с
    неизвестным статусом осталась бы без кнопки копирования, то есть без
    диагностики, именно тогда, когда диагностика и нужна. Проверяется и запись
    БЕЗ текста ошибки: диагностический блок ценен и без него — по нему находят
    отправку.
    """
    user = await _current_user(db_session)
    await _seed_send_log(db_session, user.id, status=status, error_message=None)

    html = _page_body((await authed_client.get("/history")).text)

    assert "data-copybtn" in html, status


# =============================================================================
# План 04-07, задача 2: страница записи истории
# =============================================================================
#
# Страница СОХРАНЯЕТСЯ, а не сносится: лента дашборда (план 04-05) ведёт именно
# в неё, а снапшот содержимого с изображениями в строку списка не влезает.
# Переверстка идёт по областям карточки записи из макета, и примитив записи
# переиспользуется целиком — своей копии областей, бейджа и иконки канала
# страница не заводит.


async def _seed_own_record(db: AsyncSession, user: User, **kwargs) -> SendLog:
    """Запись текущего пользователя со значениями, различимыми в разметке."""
    defaults = dict(
        status=STATUS_FAIL,
        messenger_type="wa",
        ad_title="Объявление записи",
        ad_text="Снапшот текста объявления",
        group_name="Группа записи",
        task_id="task-detail-77",
        error_message=LONG_ERROR,
    )
    defaults.update(kwargs)
    return await _seed_send_log(db, user.id, **defaults)


@pytest.mark.asyncio
async def test_history_detail_shows_the_whole_record(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Страница записи отвечает на все вопросы об отправке сразу.

    Перевёрстка теряет значения молча: страница остаётся валидной и отдаёт 200,
    а поля из неё исчезают. Поэтому проверяются ЗНАЧЕНИЯ, а не разметка.
    """
    user = await _current_user(db_session)
    log = await _seed_own_record(db_session, user)

    response = await authed_client.get(f"/history/{log.id}")

    assert response.status_code == 200
    html = response.text
    for part in (
        "Объявление записи",
        "Группа записи",
        "task-detail-77",
        "WhatsApp",
        "Ошибка",
        str(datetime.now(timezone.utc).year),
    ):
        assert part in html, f"со страницы записи пропало {part!r}"


@pytest.mark.asyncio
async def test_history_detail_shows_the_content_snapshot(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Снапшот содержимого — то, ради чего страница и существует (D-24).

    Текст и изображения сохранены в самой записи: объявление могли с тех пор
    переписать или удалить, а история обязана показывать отправленное.
    """
    user = await _current_user(db_session)
    log = await _seed_own_record(
        db_session, user, ad_images=["snapshot-image-key.png"]
    )

    html = (await authed_client.get(f"/history/{log.id}")).text

    assert "Снапшот текста объявления" in html
    assert "snapshot-image-key.png" in html, "изображение снапшота не отрисовано"


@pytest.mark.asyncio
async def test_history_detail_reuses_the_record_primitive_and_adds_no_view_switch(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Страница собрана на примитиве записи и своего переключателя вида не имеет.

    Примитив перестраивается медиазапросами 1080px и 860px, которые в файле уже
    лежат: переиспользование делает страницу пригодной на мобильных ширинах, не
    заводя ни одного нового правила раскладки. Переключатель вида на JS ломает
    подмену через HTMX и запрещён по разделу.
    """
    user = await _current_user(db_session)
    log = await _seed_own_record(db_session, user)

    html = (await authed_client.get(f"/history/{log.id}")).text

    assert "data-hrow" in html, "примитив записи не переиспользован"
    assert 'data-area="err"' in html, "блок ошибки не размечен областью"
    assert "layout=" not in html, "на странице появился переключатель вида"


@pytest.mark.asyncio
async def test_history_detail_offers_the_same_copy_button(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Кнопка копирования приходит сюда ИЗ ТОГО ЖЕ макроса, что и в список.

    Вторая кнопка со своими правилами разошлась бы с первой при первой правке —
    и разойтись ей было бы где: в проверке доступности буфера, в составе
    диагностического блока и в отказе сообщать об успехе, которого не было.
    """
    user = await _current_user(db_session)
    log = await _seed_own_record(db_session, user)

    html = (await authed_client.get(f"/history/{log.id}")).text

    assert "data-copybtn" in html
    assert "data-copybtn" not in _outside_templates(html), (
        "на странице записи кнопка отрисована сервером — без Alpine она мертва"
    )
    diag = _diag_blocks(html)
    assert len(diag) == 1, f"диагностических блоков не один, а {len(diag)}"
    assert "task-detail-77" in diag[0]

    source = _template_text(HISTORY_DETAIL)
    assert "import copy_button" in source, "макрос кнопки не импортирован"
    assert source.count("copy_button(") == 1, (
        "страница записи собрала кнопку копирования сама, а не вызвала макрос: "
        f"вызовов {source.count('copy_button(')}"
    )


@pytest.mark.asyncio
async def test_history_detail_inherits_the_shell_and_draws_no_section_heading(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Заголовок раздела рисует шапка шелла — второй задвоился бы."""
    user = await _current_user(db_session)
    log = await _seed_own_record(db_session, user)

    source = _template_text(HISTORY_DETAIL)
    assert '{% extends "base.html" %}' in source, "страница потеряла шелл"
    assert "<h1" not in source, "страница рисует собственный заголовок раздела"

    response = await authed_client.get(f"/history/{log.id}")
    assert response.status_code == 200
    assert "<div data-body>" in response.text, "шелл не отрисован"


@pytest.mark.asyncio
async def test_history_detail_of_another_users_record_redirects_to_the_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """T-04-27: чужую запись не открыть — граница держится проверкой владения.

    Текст стороннего исключения виден ТОЛЬКО владельцу записи, и держит это
    ровно эта проверка на входе страницы. Перевёрстка её ослабить не имеет
    права.
    """
    stranger = User(email="detail-stranger@test.com", password_hash="x", name="Чужой")
    db_session.add(stranger)
    await db_session.commit()
    await db_session.refresh(stranger)
    foreign = await _seed_own_record(
        db_session, stranger, ad_title="Чужая отправка", error_message="Чужая ошибка"
    )

    response = await authed_client.get(
        f"/history/{foreign.id}", follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["location"] == "/history"


@pytest.mark.asyncio
async def test_history_detail_of_a_missing_record_redirects_to_the_list(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Несуществующая запись ведёт в список, а не в пятисотку."""
    await _current_user(db_session)

    response = await authed_client.get("/history/999999", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/history"
