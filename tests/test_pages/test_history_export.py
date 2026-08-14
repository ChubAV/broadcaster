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

from datetime import datetime, timezone

import pytest

from app.application.analytics.send_analytics import (
    STATUS_ACCOUNT_DISCONNECTED,
    STATUS_FAIL,
    STATUS_OK,
)
from app.models.group import Group
from app.models.send_log import SendLog
from app.models.user import User
from app.pages.history import (
    EXPORT_DELIMITER,
    EXPORT_HEADER,
    EXPORT_ROW_CAP,
    export_cell,
    export_row,
)

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
