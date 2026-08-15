"""Выгрузка отфильтрованной истории в файл (HIST-03).

Экспорта в проекте не существовало вовсе, поэтому вместе с возможностью
появляется НОВЫЙ для проекта класс угрозы: заголовок объявления, имя группы и
текст ошибки приходят от пользователя и от стороннего мессенджера, попадают в
файл, и файл этот открывают табличным редактором — возможно, не тот, кто его
выгрузил. Значение, начинающееся с символа формулы, редактор исполнит.

Файл держит обещания выгрузки целиком: состав строки, экранирование опасных
значений, совпадение числа строк со счётчиком над списком, порядок объявления
маршрутов и честный отказ вместо тихой обрезки.
"""

import csv
import io
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
from app.pages import history as history_module
from app.pages.history import (
    EXPORT_DELIMITER,
    EXPORT_FILENAME,
    EXPORT_HEADER,
    EXPORT_ROW_CAP,
    export_cell,
    export_row,
)

HISTORY_PY = Path(__file__).resolve().parents[2] / "app" / "pages" / "history.py"

# --- посев чистых объектов ----------------------------------------------------
#
# Функции состава строки — ЧИСТЫЕ: они не ходят в базу и не читают запрос.
# Поэтому объекты собираются в памяти, без сессии: тест, гоняющий ради проверки
# порядка колонок целую базу, краснеет на чужих причинах.


def _user(tz: str = "UTC") -> User:
    return User(email="owner@test.com", name="Владелец", timezone=tz)


def _log(**kwargs) -> SendLog:
    defaults = dict(
        user_id=1,
        group_id=7,
        ad_title="Летняя распродажа",
        ad_text="Скидки до 50% на весь ассортимент",
        ad_images=[],
        group_name="Чат покупателей",
        messenger_type="wa",
        task_id="task-9f3c1d",
        status=STATUS_OK,
        error_message=None,
        sent_at=datetime(2026, 3, 14, 9, 5, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    return SendLog(**defaults)


def _group(account_id: int = 42) -> Group:
    return Group(
        user_id=1,
        account_id=account_id,
        messenger_type="wa",
        group_external_id="-1001234567890",
        name="Чат покупателей",
    )


# --- Шапка файла --------------------------------------------------------------


def test_export_header_has_eight_columns():
    """Восемь колонок из D-28 — ни одной сверх и ни одной вместо."""
    assert len(EXPORT_HEADER) == 8, EXPORT_HEADER


def test_export_header_carries_no_ad_body_column():
    """Снапшот текста объявления в файл НЕ идёт (D-28).

    Он раздувает файл в разы и ломает сетку переводами строк внутри значения:
    открытый в редакторе такой файл рассыпается на строки, которых не было.
    """
    assert not any("текст" in label.lower() for label in EXPORT_HEADER), EXPORT_HEADER


def test_export_delimiter_is_not_a_comma():
    """Разделитель — точка с запятой (Open Question 2).

    Метка порядка байтов решает вопрос КОДИРОВКИ, но не разделителя: в русской
    локали табличный редактор берёт разделитель списка из системных настроек, и
    файл с запятыми открывается ОДНОЙ колонкой. Намерение D-25 «открывается
    нормально» выполнялось бы ровно наполовину, причём молча.
    """
    assert EXPORT_DELIMITER == ";"


# --- Экранирование опасных значений (T-04-16) ---------------------------------


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r"])
def test_export_cell_defuses_a_formula_value(prefix: str):
    """Значение, начинающееся с символа формулы, обезврежено апострофом.

    Табличный редактор исполняет содержимое ячейки, начинающееся с одного из
    этих символов. Значение приезжает из заголовка объявления, имени группы или
    текста ошибки мессенджера — то есть от кого угодно, а открывают файл на
    чужой машине.
    """
    value = f"{prefix}HYPERLINK(\"http://evil\";\"счёт\")"

    assert export_cell(value) == f"'{value}"


def test_export_cell_defuses_a_formula_in_every_value_bearing_column():
    """Три поля, приезжающие от пользователя и от мессенджера, — обезврежены.

    Проверяются ИМЕННО они, потому что остальные колонки формирует сервер:
    время, статус и канал подставить снаружи нельзя.
    """
    row = export_row(
        _log(
            ad_title="=1+1",
            group_name="+cmd|'/c calc'!A1",
            error_message="@SUM(1)",
        ),
        _group(),
        _user(),
    )

    dangerous = [cell for cell in row if cell.startswith(("=", "+", "-", "@"))]
    assert dangerous == [], f"необезвреженные значения в строке: {dangerous}"
    assert "'=1+1" in row
    assert "'+cmd|'/c calc'!A1" in row
    assert "'@SUM(1)" in row


def test_export_cell_leaves_a_plain_value_untouched():
    """Обычное значение не обрастает апострофом: файл читают люди."""
    assert export_cell("Летняя распродажа") == "Летняя распродажа"
    assert export_cell("Скидка 50%") == "Скидка 50%"


def test_export_cell_turns_none_into_an_empty_string():
    """Пустое поле — пустая ячейка, а не слово «None».

    `error_message` пуст у КАЖДОЙ успешной отправки, то есть у большинства
    строк файла; слово «None» в них было бы не опечаткой, а неверными данными.
    """
    assert export_cell(None) == ""


def test_export_cell_turns_an_empty_value_into_an_empty_string():
    assert export_cell("") == ""


# --- Состав строки ------------------------------------------------------------


def test_export_row_matches_the_header_length():
    """Полей в строке ровно столько же, сколько подписей в шапке.

    Разъехавшаяся на одну колонку строка не роняет ничего: файл открывается, и
    все значения правее разрыва оказываются подписаны чужими колонками.
    """
    assert len(export_row(_log(), _group(), _user())) == len(EXPORT_HEADER)


def test_export_row_formats_time_in_the_user_timezone():
    """Время в файле — то же, что пользователь видел на экране (D-30).

    Оно проходит через тот же хелпер, что и разметка записи, поэтому UTC в
    файле при московском пользователе означал бы два разных ответа на вопрос
    «когда это случилось».
    """
    log = _log(sent_at=datetime(2026, 3, 14, 21, 30, tzinfo=timezone.utc))

    moscow = export_row(log, _group(), _user("Europe/Moscow"))[0]
    utc = export_row(log, _group(), _user("UTC"))[0]

    assert "2026-03-15 00:30" == moscow
    assert "2026-03-14 21:30" == utc


def test_export_row_survives_a_missing_group():
    """Отправка, чья группа удалена, даёт пустые поля, а не исключение.

    Такие записи в журнале есть: `group_id` обнуляемый, и запись переживает
    удаление группы. Исключение здесь оборвало бы уже начатый поток — то есть
    отдало бы пользователю обрезанный файл со статусом успеха.
    """
    row = export_row(_log(group_id=None, group_name=None), None, _user())

    assert len(row) == len(EXPORT_HEADER)
    assert row[2] == ""
    assert row[3] == ""


def test_export_row_survives_an_empty_messenger():
    """Старая запись без канала (он появился позже) выгружается наравне."""
    row = export_row(_log(messenger_type=None), _group(), _user())

    assert len(row) == len(EXPORT_HEADER)
    assert row[1] == ""


def test_export_row_omits_the_ad_body_snapshot():
    """Тела объявления в строке нет ни в одной колонке (D-28)."""
    body = "Текст объявления, который не должен попасть в файл"

    row = export_row(_log(ad_text=body), _group(), _user())

    assert all(body not in cell for cell in row), row


def test_export_row_carries_the_account_through_the_group():
    """Колонки аккаунта в журнале НЕТ — аккаунт выводится через группу."""
    row = export_row(_log(), _group(account_id=42), _user())

    assert "42" in row[2]


def test_export_row_keeps_the_title_status_error_and_task():
    """Все обещанные значения действительно доехали до строки."""
    row = export_row(
        _log(
            ad_title="Летняя распродажа",
            group_name="Чат покупателей",
            status=STATUS_FAIL,
            error_message="PEER_FLOOD",
            task_id="task-9f3c1d",
        ),
        _group(),
        _user(),
    )

    joined = EXPORT_DELIMITER.join(row)
    for expected in ("Летняя распродажа", "Чат покупателей", "PEER_FLOOD", "task-9f3c1d"):
        assert expected in joined, f"{expected!r} потеряно: {row}"


def test_export_row_names_a_disconnected_account_status():
    """Третий статус журнала в файле назван, а не отдан кодом.

    `account_disconnected` — единственный статус, по которому видно, что
    отправка не ушла из-за отвалившегося аккаунта; в файле он обязан читаться
    так же, как на экране.
    """
    row = export_row(_log(status=STATUS_ACCOUNT_DISCONNECTED), _group(), _user())

    assert row[5] == "Аккаунт отключён"


def test_export_row_keeps_an_unknown_status_visible():
    """Незнакомый статус печатается КАК ЕСТЬ, а не пустеет.

    Пустая ячейка вместо неопознанного значения — то же молчаливое
    выбрасывание, которое запрещает прохибиция P-04-01: строка осталась бы в
    файле без единого признака того, чем кончилась отправка.
    """
    row = export_row(_log(status="quarantined"), _group(), _user())

    assert row[5] == "quarantined"


# =============================================================================
# Задача 2: маршрут потоковой выгрузки
# =============================================================================


# --- посев базы ---------------------------------------------------------------


async def _current_user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _seed_logs(
    db: AsyncSession,
    user_id: int,
    count: int,
    *,
    status: str = STATUS_OK,
    messenger_type: str | None = "wa",
    group_id: int | None = None,
    sent_at: datetime | None = None,
    ad_title: str = "Летняя распродажа",
    error_message: str | None = None,
) -> None:
    """Пачка записей журнала ОДНИМ коммитом: посев не предмет проверки."""
    base = sent_at or datetime.now(timezone.utc)
    for i in range(count):
        db.add(
            SendLog(
                user_id=user_id,
                group_id=group_id,
                ad_title=ad_title,
                ad_text="Скидки до 50% на весь ассортимент",
                ad_images=[],
                group_name="Чат покупателей",
                messenger_type=messenger_type,
                task_id=f"task-{i:04d}",
                status=status,
                error_message=error_message,
                sent_at=base - timedelta(seconds=i),
            )
        )
    await db.commit()


async def _seed_other_user(db: AsyncSession) -> User:
    other = User(
        email="stranger@test.com",
        password_hash="x",
        name="Чужой",
        timezone="UTC",
    )
    db.add(other)
    await db.commit()
    await db.refresh(other)
    return other


async def _seed_account_with_group(db: AsyncSession, user_id: int) -> Group:
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
        group_external_id="-1005550001",
        name="Чат покупателей",
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


# --- разбор ответа ------------------------------------------------------------

BOM = b"\xef\xbb\xbf"

_EXPORT_LINK_RE = re.compile(r"<a\b[^>]*\bdata-hexport\b[^>]*>")


def _csv_rows(response) -> list[list[str]]:
    """Строки файла как их прочитает табличный редактор — БЕЗ метки порядка."""
    text = response.content.decode("utf-8-sig")
    return [row for row in csv.reader(io.StringIO(text), delimiter=EXPORT_DELIMITER)]


def _data_rows(response) -> list[list[str]]:
    return _csv_rows(response)[1:]


def _counter_of(html: str) -> int:
    match = re.search(r'data-hcount="(\d+)"', html)
    assert match, "линейки счётчика на странице нет — сравнивать не с чем"
    return int(match.group(1))


def _export_link(html: str) -> str:
    match = _EXPORT_LINK_RE.search(html)
    assert match, "ссылки выгрузки на странице нет"
    tag = match.group(0)
    href = re.search(r'href="([^"]*)"', tag)
    assert href, f"у ссылки выгрузки нет адреса: {tag}"
    return href.group(1)


# --- Отдача файла -------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_returns_a_csv_attachment(
    authed_client: AsyncClient, db_session: AsyncSession
):
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 3)

    response = await authed_client.get("/history/export")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "charset=utf-8" in response.headers["content-type"].lower()
    disposition = response.headers["content-disposition"]
    assert "attachment" in disposition
    assert EXPORT_FILENAME in disposition


@pytest.mark.asyncio
async def test_export_body_starts_with_the_byte_order_mark(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Метка порядка байтов — ПЕРВЫЕ байты тела (D-25).

    Без неё табличный редактор в русской локали читает файл однобайтовой
    кодировкой, и кириллица приезжает мусором — файл открывается, выглядит
    заполненным и не содержит ни одного читаемого слова.
    """
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 2)

    response = await authed_client.get("/history/export")

    assert response.content.startswith(BOM), response.content[:16]
    assert "Летняя распродажа" in response.content.decode("utf-8-sig")


@pytest.mark.asyncio
async def test_export_first_line_is_the_header(
    authed_client: AsyncClient, db_session: AsyncSession
):
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 2)

    response = await authed_client.get("/history/export")

    assert _csv_rows(response)[0] == list(EXPORT_HEADER)


@pytest.mark.asyncio
async def test_export_row_count_matches_the_counter(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Строк в файле ровно столько, сколько обещает число над списком.

    Посев ЗАВЕДОМО больше страницы выдачи (30): реализация, выгружающая
    страницу вместо выборки, зеленела бы на трёх записях и врала бы на всех
    остальных — причём именно там, где выгрузка и нужна.
    """
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 35)

    counter = _counter_of((await authed_client.get("/history")).text)
    response = await authed_client.get("/history/export")

    assert counter == 35
    assert len(_data_rows(response)) == counter


@pytest.mark.asyncio
async def test_export_honours_the_status_filter(
    authed_client: AsyncClient, db_session: AsyncSession
):
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 4, status=STATUS_OK)
    await _seed_logs(db_session, user.id, 2, status=STATUS_FAIL, error_message="PEER_FLOOD")

    response = await authed_client.get(f"/history/export?status={STATUS_FAIL}")

    rows = _data_rows(response)
    assert len(rows) == 2
    assert {row[5] for row in rows} == {"Ошибка"}


@pytest.mark.asyncio
async def test_export_honours_the_period_filter(
    authed_client: AsyncClient, db_session: AsyncSession
):
    user = await _current_user(db_session)
    now = datetime.now(timezone.utc)
    await _seed_logs(db_session, user.id, 2, sent_at=now)
    await _seed_logs(db_session, user.id, 3, sent_at=now - timedelta(days=40))

    response = await authed_client.get("/history/export?period=7d")

    assert len(_data_rows(response)) == 2


@pytest.mark.asyncio
async def test_export_ignores_an_unknown_filter_value(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Мусор в оси не становится условием запроса — выгрузка третий вход.

    Отсечка стоит в обработчике списка и в паршале прокрутки; выгрузка — ТРЕТИЙ
    вход на те же фильтры, и без отсечки здесь подобранное вручную значение
    молча отдавало бы пустой файл, неотличимый от «записей действительно нет».
    """
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 3)

    response = await authed_client.get("/history/export?status=не-такой-статус")

    assert response.status_code == 200
    assert len(_data_rows(response)) == 3


@pytest.mark.asyncio
async def test_export_hides_other_users_records(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Условие владения стоит в БАЗОВОМ запросе выгрузки (T-04-31)."""
    user = await _current_user(db_session)
    other = await _seed_other_user(db_session)
    await _seed_logs(db_session, user.id, 2, ad_title="Своя запись")
    await _seed_logs(db_session, other.id, 5, ad_title="Чужая запись")

    response = await authed_client.get("/history/export")

    text = response.content.decode("utf-8-sig")
    assert "Чужая запись" not in text
    assert len(_data_rows(response)) == 2


@pytest.mark.asyncio
async def test_export_carries_the_account_of_the_group(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Аккаунт в файле приезжает через группу — соединение в запросе есть."""
    user = await _current_user(db_session)
    group = await _seed_account_with_group(db_session, user.id)
    await _seed_logs(db_session, user.id, 1, group_id=group.id)

    response = await authed_client.get("/history/export")

    assert _data_rows(response)[0][2] == str(group.account_id)


@pytest.mark.asyncio
async def test_export_defuses_a_formula_coming_from_the_messenger(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Опасное значение обезврежено В ФАЙЛЕ, а не только в чистой функции.

    Проверка сквозная НАМЕРЕННО: подготовка поля, забытая в одной из восьми
    колонок маршрута, зеленела бы на всех тестах чистой функции.
    """
    user = await _current_user(db_session)
    await _seed_logs(
        db_session,
        user.id,
        1,
        status=STATUS_FAIL,
        ad_title='=HYPERLINK("http://evil";"счёт")',
        error_message="+cmd|'/c calc'!A1",
    )

    response = await authed_client.get("/history/export")

    row = _data_rows(response)[0]
    assert not any(cell.startswith(("=", "+", "-", "@")) for cell in row), row


@pytest.mark.asyncio
async def test_export_requires_login(client: AsyncClient):
    """Гард входа тот же, что у остальных страничных обработчиков (T-04-31)."""
    response = await client.get("/history/export", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


# --- Порядок объявления маршрутов ---------------------------------------------


def test_export_route_order_precedes_the_record_route_in_the_source():
    """Выгрузка объявлена ВЫШЕ маршрута записи истории.

    Сопоставление идёт в порядке объявления: объявленный ниже адрес уехал бы в
    параметр пути маршрута записи и вернул бы ошибку разбора вместо файла.
    Ровно по этой причине выше маршрута записи уже стоит паршал прокрутки.
    """
    source = HISTORY_PY.read_text(encoding="utf-8")

    export_at = source.index('@router.get("/history/export"')
    record_at = source.index('@router.get("/history/{log_id}"')

    assert export_at < record_at, (
        "маршрут выгрузки объявлен ниже маршрута записи — адрес /history/export "
        "будет разобран как идентификатор записи"
    )


@pytest.mark.asyncio
async def test_export_route_order_survives_the_record_route_at_runtime(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Проверка по ВЫДАЧЕ, а не по исходнику: файл, а не ошибка разбора.

    Порядок в тексте модуля — причина, а следствие проверяется здесь: маршрут
    записи объявляет `log_id: int`, поэтому перехваченный им адрес дал бы 422.
    """
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 1)

    response = await authed_client.get("/history/export", follow_redirects=False)

    assert response.status_code == 200, response.text[:400]
    assert "text/csv" in response.headers["content-type"]


# --- Потолок числа строк (D-27, T-04-32, T-04-33) -----------------------------


@pytest.mark.asyncio
async def test_export_cap_gives_no_file_when_exceeded(
    authed_client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Превышение потолка не даёт файла ВООБЩЕ — ни целого, ни обрезанного.

    Проверка обязана стоять ДО конструирования потокового ответа: у потока код
    и заголовки уходят до первого фрагмента тела и после уже неизменяемы, а
    значит проверка внутри генератора дала бы либо файл со статусом успеха и
    текстом ошибки внутри, либо обрезанный файл без единого признака обрезки.
    """
    monkeypatch.setattr(history_module, "EXPORT_ROW_CAP", 2)
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 3)

    response = await authed_client.get("/history/export", follow_redirects=False)

    assert response.status_code == 302
    assert "content-disposition" not in response.headers
    assert response.headers["location"].startswith("/history?")
    assert "export=" in response.headers["location"]


@pytest.mark.asyncio
async def test_export_cap_explains_and_offers_to_narrow_the_period(
    authed_client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Пользователь получает ОБЪЯСНЕНИЕ, а не молчание (T-04-33)."""
    monkeypatch.setattr(history_module, "EXPORT_ROW_CAP", 2)
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 3)

    response = await authed_client.get("/history/export", follow_redirects=True)

    html = response.text
    assert 'data-export-cap="2"' in html, "плашки отказа на списке нет"
    assert "период" in html.lower(), "объяснение не предлагает сузить период"


@pytest.mark.asyncio
async def test_export_cap_keeps_the_active_filters_in_the_explanation(
    authed_client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Отказ возвращает на ТОТ ЖЕ отфильтрованный список, а не на чистый.

    Перенаправление, потерявшее фильтры, показало бы пользователю другой экран
    и предложило бы сузить период у выборки, которую он не выгружал.
    """
    monkeypatch.setattr(history_module, "EXPORT_ROW_CAP", 1)
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 3, status=STATUS_OK)

    response = await authed_client.get(
        f"/history/export?status={STATUS_OK}", follow_redirects=False
    )

    assert f"status={STATUS_OK}" in response.headers["location"]


@pytest.mark.asyncio
async def test_export_cap_lets_the_boundary_selection_through(
    authed_client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Ровно потолок — ещё файл: отказ начинается ЗА границей, а не на ней."""
    monkeypatch.setattr(history_module, "EXPORT_ROW_CAP", 3)
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 3)

    response = await authed_client.get("/history/export", follow_redirects=False)

    assert response.status_code == 200
    assert len(_data_rows(response)) == 3


def test_export_cap_is_checked_before_the_streaming_response():
    """Вызов счётчика стоит в исходнике ВЫШЕ конструирования потока.

    Структурная проверка НАМЕРЕННО: поведенчески «проверено до потока» и
    «проверено в первом фрагменте генератора» неразличимы на тестовом клиенте,
    который читает ответ целиком. Отличается ровно порядок в коде, и здесь
    проверяется он.
    """
    source = HISTORY_PY.read_text(encoding="utf-8")
    export_at = source.index('@router.get("/history/export"')
    body = source[export_at : source.index('@router.get("/history/{log_id}"')]

    assert "history_count(" in body, "потолок не с чем сравнивать"
    assert body.index("history_count(") < body.index("StreamingResponse("), (
        "счётчик вызван после конструирования потока — отказ уже нечем отдать"
    )


def test_export_reads_the_selection_as_a_stream():
    """Чтение идёт партиями, а не одной выборкой в память (T-04-32).

    Структурная проверка: размер памяти процесса тестом не наблюдается, а
    подмена потока обычным `execute` не роняет ни одного утверждения о
    содержимом файла — она проявляется только на боевом объёме.
    """
    source = HISTORY_PY.read_text(encoding="utf-8")
    export_at = source.index('@router.get("/history/export"')
    body = source[export_at : source.index('@router.get("/history/{log_id}"')]

    assert ".stream(" in body
    assert "EXPORT_YIELD_PER" in body


# --- Ссылка выгрузки на странице списка ---------------------------------------


@pytest.mark.asyncio
async def test_export_link_carries_the_active_filters(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Ссылка выгрузки несёт те же фильтры, что и адрес списка.

    Ссылка без фильтров выгружала бы ВСЮ историю с экрана, показывающего
    отфильтрованную, — то есть отдавала бы не то, что пользователь видит.
    """
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 2, status=STATUS_OK)

    html = (await authed_client.get(f"/history?status={STATUS_OK}&period=30d")).text

    href = _export_link(html)
    assert href.startswith("/history/export")
    assert f"status={STATUS_OK}" in href
    assert "period=30d" in href


@pytest.mark.asyncio
async def test_export_link_needs_no_javascript(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Выгрузка — ОБЫЧНАЯ ссылка (D-26): ни подмены, ни обработчика."""
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 2)

    html = (await authed_client.get("/history")).text

    tag = _EXPORT_LINK_RE.search(html).group(0)
    assert "hx-" not in tag, tag
    assert "onclick" not in tag.lower(), tag
    assert 'href="/history/export' in tag, tag


@pytest.mark.asyncio
async def test_export_link_absent_when_there_is_nothing_to_export(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """На пустом журнале ссылки нет: выгрузка пустого файла — не действие."""
    html = (await authed_client.get("/history")).text

    assert "/history/export" not in html


@pytest.mark.asyncio
async def test_export_cap_notice_is_absent_on_a_normal_visit(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Объяснение появляется только по признаку отказа, а не всегда.

    Парный тест к объяснению отказа: одиночный зеленел бы на реализации,
    печатающей плашку на каждом заходе в раздел.
    """
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 2)

    html = (await authed_client.get("/history")).text

    assert "alert--warning" not in html


@pytest.mark.asyncio
async def test_export_cap_notice_ignores_a_garbage_reason(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Подобранное вручную значение признака не рисует плашку.

    Признак приезжает строкой запроса, то есть из чужой ссылки: плашка по
    любому непустому значению позволяла бы нарисовать пользователю сообщение о
    несостоявшейся выгрузке, которой не было.
    """
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 2)

    html = (await authed_client.get("/history?export=что-угодно")).text

    assert "alert--warning" not in html


@pytest.mark.asyncio
async def test_export_announces_a_failure_that_happens_mid_stream(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings, monkeypatch
):
    """Обрыв ПОСРЕДИ потока дописывает в файл строку-маркёр.

    Потолок строк проверяется ДО начала ответа именно затем, чтобы неполный
    файл нельзя было принять за полный (D-27). У генератора такой защиты не
    было: код 200 и заголовок с именем файла уходят до первого фрагмента тела и
    после уже неизменяемы, поэтому ошибка базы, оборванный курсор или сбой
    сериализации после первого `yield` отдавали пользователю файл, который
    открывается, выглядит полным и короче правды — тот же исход, только другой
    дорогой.

    ПРОВЕРКА ИДЁТ ПО ТЕЛУ ГЕНЕРАТОРА, а не через тестовый HTTP-клиент: у
    ASGI-транспорта исключение внутри потокового тела снимает ответ целиком, и
    уже отданные фрагменты до клиента не доезжают — то есть через клиент этот
    тест зеленел бы на любом поведении. Обработчик поэтому вызывается напрямую,
    а `body_iterator` вычитывается вручную.

    Сбой вносится подменой `AsyncSession.stream`: суита никогда не заставляла
    поток упасть, и именно поэтому дефект дожил до ревью.
    """
    from starlette.requests import Request

    from app.pages.history import history_export

    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 3)

    token = authed_client.cookies.get("access_token")
    assert token, "фикстура не положила cookie входа — тест проверяет не то"

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/history/export",
            "raw_path": b"/history/export",
            "root_path": "",
            "scheme": "http",
            "query_string": b"",
            "headers": [(b"cookie", f"access_token={token}".encode())],
            "server": ("test", 80),
            "client": ("test", 12345),
        }
    )

    response = await history_export(
        request,
        status=None,
        messenger=None,
        account_id=None,
        period=None,
        db=db_session,
        settings=test_settings,
    )
    assert response.status_code == 200, (
        "заголовки ответа уходят до тела — именно поэтому обрыв можно назвать "
        "только внутри самого файла"
    )

    async def _boom(self, *args, **kwargs):
        raise RuntimeError("курсор оборван посреди выгрузки")

    monkeypatch.setattr(AsyncSession, "stream", _boom)

    chunks: list[str] = []
    with pytest.raises(RuntimeError):
        async for chunk in response.body_iterator:
            chunks.append(chunk)

    body = "".join(chunks)
    assert history_module.EXPORT_TRUNCATED_MARKER in body, (
        f"оборванная выгрузка отдана без единого признака неполноты: {body!r}"
    )
    assert EXPORT_HEADER[0] in body, "шапка файла не отдана — тест проверяет не то"


@pytest.mark.asyncio
async def test_export_writes_no_truncation_marker_on_a_healthy_run(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Целая выгрузка себя оборванной НЕ называет.

    Маркёр, попадающий в исправный файл, был бы ровно той же неправдой, только
    с другим знаком: пользователь выбросил бы полные данные.
    """
    user = await _current_user(db_session)
    await _seed_logs(db_session, user.id, 3)

    body = (await authed_client.get("/history/export")).text

    assert history_module.EXPORT_TRUNCATED_MARKER not in body
