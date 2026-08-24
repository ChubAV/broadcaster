"""Разбор тела задачи в строку подраздела «Очередь».

⚠️ ГЛАВНОЕ УТВЕРЖДЕНИЕ ФАЙЛА — ПАРА `test_..._delay_...`, И ОНА ПАРНАЯ
НАМЕРЕННО. Два канала пишут отложенность задачи в РАЗНЫХ единицах времени:
WA — миллисекунды (`Date.now() + delaySec * 1000`, wa_worker/index.js:583),
MAX — секунды (`time.time() + delay_sec`, max_worker/main.py:719). Каждый воркер
читает своё значение своей меркой и потому работает; подраздел читает ОБА списка
одним кодом.

Единая формула здесь НЕ ПАДАЕТ — и в этом весь дефект. `fromtimestamp(v)` покажет
WA-задачу отложенной до 55-го тысячелетия, `fromtimestamp(v / 1000)` покажет
MAX-задачу отложенной до 1970 года. Обе даты правдоподобны на вид, обе
напечатаются без единого исключения, и администратор прочитает выдумку как
измеренную величину. Поэтому улика — два теста на НАСТОЯЩИХ телах задач обоих
каналов, падающие ПО ОТДЕЛЬНОСТИ: любая единая формула красит ровно один из
них, и одиночная проверка одного канала прошла бы мимо.

⚠️ ПОЛЕЙ ПОВТОРА И ОТЛОЖЕННОСТИ В СВЕЖЕЙ ЗАДАЧЕ НЕТ ВОВСЕ. Постановщик
(`dispatch_send_tasks`, app/worker/tasks.py:113-140) кладёт двенадцать полей, и
`_retry_count`/`_delay_until` среди них отсутствуют — их дописывает ТОЛЬКО воркер
при повторе. Чтение по индексу уронило бы подраздел на первой же нормальной
задаче, то есть в самом частом случае, а не в краевом.
"""
import time
from datetime import datetime, timedelta, timezone

import pytest

from app.application.admin.queue_rows import (
    QUEUE_ROW_CAP,
    QUEUE_STATE_DELAYED,
    QUEUE_STATE_RETRYING,
    QUEUE_STATE_WAITING,
    parse_delay_until,
    queue_row_state,
    queue_rows,
)


def _dispatched_task(**overrides) -> dict:
    """Тело задачи РОВНО в той форме, в какой его кладёт постановщик.

    Поля переписаны с `dispatch_send_tasks` (app/worker/tasks.py:113-140)
    один в один. Выдуманное тело проверяло бы разбор выдуманного формата:
    именно полнота этого словаря делает тест уликой, а не иллюстрацией.
    """
    task = {
        "task_id": "0f6b3f4e-2a1d-4c8e-9f2b-7c5a1d3e9b04",
        "ad_id": 11,
        "group_id": 22,
        "account_id": 33,
        "schedule_id": 44,
        "user_id": 55,
        "ad_text": "Текст объявления",
        "ad_title": "Заголовок",
        "ad_images": [],
        "group_external_id": "-100123456789",
        "group_name": "Группа «Барахолка»",
        "created_at": "2026-08-22T10:00:00+00:00",
    }
    task.update(overrides)
    return task


# ---- Отложенность: единицы времени зависят от КАНАЛА (Ф-7) ----

def test_wa_delay_until_written_in_milliseconds_reads_as_a_near_moment():
    """Тело WA-задачи с отложенностью В МИЛЛИСЕКУНДАХ → момент рядом с текущим.

    Значение взято ровно тем выражением, которым его пишет воркер. Формула для
    секунд отнесла бы этот момент в 55-е тысячелетие — и напечатала бы его без
    единой жалобы.
    """
    now = datetime.now(timezone.utc)
    task = _dispatched_task(
        _retry_count=1,
        _delay_until=int((time.time() + 60) * 1000),  # wa_worker/index.js:583
    )

    until = parse_delay_until(task["_delay_until"], "wa")

    assert until is not None
    assert timedelta(0) < until - now < timedelta(hours=1)


def test_max_delay_until_written_in_seconds_reads_as_a_near_moment():
    """Тело MAX-задачи с отложенностью В СЕКУНДАХ → такой же близкий момент.

    Парный к предыдущему. Формула для миллисекунд отнесла бы этот момент в
    1970 год — тоже молча.
    """
    now = datetime.now(timezone.utc)
    task = _dispatched_task(
        _retry_count=1,
        _delay_until=time.time() + 60,  # max_worker/main.py:719
    )

    until = parse_delay_until(task["_delay_until"], "max")

    assert until is not None
    assert timedelta(0) < until - now < timedelta(hours=1)


def test_the_same_delay_value_reads_differently_for_the_two_channels():
    """ОДНО И ТО ЖЕ число, прочитанное по двум каналам, даёт РАЗНЫЕ моменты.

    Утверждение адресовано именно единой формуле: пока она возможна, эти два
    вызова совпадают. Расхождение в тысячу раз — и есть содержание Ф-7.
    """
    raw = time.time() + 60

    as_max = parse_delay_until(raw, "max")
    as_wa = parse_delay_until(raw, "wa")

    assert as_max is not None and as_wa is not None
    assert as_max.year > as_wa.year


def test_parse_delay_until_requires_the_channel_as_an_explicit_argument():
    """Канал — ОБЯЗАТЕЛЬНЫЙ аргумент, а не значение по умолчанию.

    Умолчание сделало бы единую формулу достижимой по недосмотру: вызов без
    канала молча выбрал бы одну из двух мерок и на второй половине задач
    рисовал бы правдоподобную ложь.
    """
    with pytest.raises(TypeError):
        parse_delay_until(time.time() + 60)


def test_non_numeric_and_missing_delay_do_not_break_the_parsing():
    """Мусор и отсутствие отложенности возвращают пустоту, а не исключение."""
    assert parse_delay_until(None, "wa") is None
    assert parse_delay_until("", "wa") is None
    assert parse_delay_until("not-a-number", "max") is None


# ---- Три состояния строки (D-16) ----

def test_a_freshly_dispatched_task_reads_as_waiting():
    """СВЕЖЕПОСТАВЛЕННАЯ задача — «ждёт», и разбор её не роняет.

    Ни `_retry_count`, ни `_delay_until` в ней нет вовсе: их дописывает только
    воркер при повторе. Это самый частый случай подраздела, а не краевой.
    """
    row = queue_row_state(_dispatched_task(), "wa")

    assert row.state == QUEUE_STATE_WAITING
    assert row.delay_until is None
    assert row.retries == 0


def test_a_task_with_retries_and_no_delay_reads_as_retrying_with_its_number():
    """Счётчик повторов без отложенности — «ретрай N», и N настоящий."""
    row = queue_row_state(_dispatched_task(_retry_count=2), "max")

    assert row.state == QUEUE_STATE_RETRYING
    assert row.retries == 2
    assert row.delay_until is None


def test_a_delayed_task_reads_as_delayed_until_its_moment():
    """Отложенность в будущем — «отложена до T», и момент отдаётся строкой."""
    row = queue_row_state(
        _dispatched_task(_retry_count=1, _delay_until=int((time.time() + 60) * 1000)),
        "wa",
    )

    assert row.state == QUEUE_STATE_DELAYED
    assert row.delay_until is not None
    assert row.delay_until > datetime.now(timezone.utc)


def test_a_delay_already_in_the_past_is_not_printed_as_a_future_moment():
    """Отложенность В ПРОШЛОМ — это «ретрай N», а не «отложена до вчера».

    Момент, уже наступивший, означает, что задача снова ждёт своей очереди.
    Напечатанный как «отложена до», он сообщал бы, что подраздел ждёт события,
    которое уже произошло.
    """
    row = queue_row_state(
        _dispatched_task(_retry_count=1, _delay_until=int((time.time() - 600) * 1000)),
        "wa",
    )

    assert row.state == QUEUE_STATE_RETRYING
    assert row.delay_until is None


def test_the_parsing_does_not_mutate_the_task_body_it_was_given():
    """Разбор ничего не дописывает в поданное тело задачи.

    Тело читается из очереди и в неё же возвращается при снятии по совпадению
    байтов: дописанное разбором поле сделало бы прочитанное отличным от
    записанного.
    """
    task = _dispatched_task(_retry_count=1)
    before = dict(task)

    queue_row_state(task, "wa")

    assert task == before


# ---- Потолок перечня строк ----

def test_the_row_list_is_capped_and_says_so_with_a_separate_flag():
    """Перечень усечён потолком, и срабатывание отдано ОТДЕЛЬНЫМ полем.

    Молча укороченный список читается как «остальных задач нет» — то есть как
    ответ на вопрос, ради которого в подраздел и пришли. Признак выводить из
    длины нельзя: ровно `QUEUE_ROW_CAP` задач — это неусечённый список.
    """
    page = queue_rows([_dispatched_task() for _ in range(QUEUE_ROW_CAP + 5)], "wa")

    assert len(page.rows) == QUEUE_ROW_CAP
    assert page.capped is True


def test_a_short_list_is_not_reported_as_capped():
    """Список короче потолка не объявляет себя усечённым."""
    page = queue_rows([_dispatched_task(), _dispatched_task()], "max")

    assert len(page.rows) == 2
    assert page.capped is False
