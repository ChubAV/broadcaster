"""Пять признаков инцидента: подъём, снятие, время следа и адрес «куда чинить».

СУИТА ИДЁТ БЕЗ ЕДИНОЙ ВНЕШНЕЙ СЛУЖБЫ. Живость воркеров приезжает в модуль
СЛОВАРЁМ ЗНАЧЕНИЙ, а не клиентом брокера, поэтому здесь нет ни одного `patch`
внешнего клиента и ни одного пропуска по недоступности службы: тест признака,
который зелен только на поднятом стенде, не проверяет признак — он проверяет
стенд.

КАЖДЫЙ ПРИЗНАК ЗАКРЕПЛЁН ДВУМЯ ТЕСТАМИ, А НЕ ОДНИМ (D-44). Условие снятия —
единственный способ инциденту исчезнуть: ручного «закрыть» нет и не заводится,
потому что оно немедленно потребовало бы хранилища закрытых, то есть отклонённой
трижды таблицы событий. Признак, у которого проверен только подъём, — это блок,
который администратор перестаёт читать через неделю.
"""
from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import event

from app.application.admin.incidents import (
    ACCOUNT_DOWN_STATUSES,
    BEAT_SILENT_OVERDUE_SEC,
    FAILURE_SPIKE_MIN_TOTAL,
    FAILURE_SPIKE_RATIO,
    FAILURE_SPIKE_WINDOW_MIN,
    INCIDENT_DESTINATIONS,
    INCIDENT_KIND_ACCOUNT_DOWN,
    INCIDENT_KIND_BEAT_SILENT,
    INCIDENT_KIND_FAILURE_SPIKE,
    INCIDENT_KIND_PAYMENT_STUCK,
    INCIDENT_KIND_WORKER_STUCK,
    INCIDENT_LIST_CAP,
    WorkerLiveness,
    collect_incidents,
    detect_failure_spike,
    detect_worker_stuck,
)
from app.application.analytics.send_analytics import (
    STATUS_ACCOUNT_DISCONNECTED,
    STATUS_FAIL,
    STATUS_OK,
)
from app.models.messenger_account import MessengerAccount
from app.models.payment import Payment
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.services.payment_service import (
    PENDING_INTENT_TTL_HOURS,
    STATUS_CANCELED,
    STATUS_PENDING,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INCIDENTS_MODULE = PROJECT_ROOT / "app" / "application" / "admin" / "incidents.py"

NOW = datetime(2026, 8, 22, 12, 0, 0, tzinfo=timezone.utc)


def _naive(moment: datetime) -> datetime:
    """Момент в том виде, в каком его отдаёт SQLite: БЕЗ таймзоны.

    Сидирование пишет naive намеренно. Колонки объявлены `DateTime(timezone=True)`,
    но SQLite отдаёт их naive, а PostgreSQL — aware; арифметика без приведения
    падает ровно на одном из двух диалектов, то есть у пользователя, а не в суите
    (Pitfall 1).
    """
    return moment.astimezone(timezone.utc).replace(tzinfo=None)


async def _seed_account(
    session,
    *,
    account_id: int,
    user_id: int = 1,
    status: str = "active",
    kind: str = "wa",
    last_synced_at: datetime | None = None,
) -> MessengerAccount:
    account = MessengerAccount(
        id=account_id,
        user_id=user_id,
        type=kind,
        credentials="{}",
        status=status,
        last_synced_at=_naive(last_synced_at) if last_synced_at else None,
    )
    session.add(account)
    await session.flush()
    return account


async def _seed_send_logs(
    session,
    *,
    user_id: int = 1,
    statuses: list[str],
    sent_at: datetime,
    messenger_type: str = "wa",
) -> None:
    for status in statuses:
        session.add(
            SendLog(
                user_id=user_id,
                status=status,
                messenger_type=messenger_type,
                sent_at=_naive(sent_at),
            )
        )
    await session.flush()


async def _seed_payment(
    session,
    *,
    payment_id: int,
    user_id: int = 1,
    status: str = STATUS_PENDING,
    created_at: datetime,
) -> None:
    session.add(
        Payment(
            id=payment_id,
            user_id=user_id,
            yookassa_payment_id=f"yk-{payment_id}",
            status=status,
            amount_value="3000.00",
            created_at=_naive(created_at),
        )
    )
    await session.flush()


async def _seed_schedule(
    session, *, schedule_id: int, next_run_at: datetime, is_active: bool = True
) -> Schedule:
    schedule = Schedule(
        id=schedule_id,
        ad_id=schedule_id,
        account_id=None,
        group_ids=[],
        days_of_week=[],
        times_of_day=[],
        is_active=is_active,
        next_run_at=_naive(next_run_at),
    )
    session.add(schedule)
    await session.flush()
    return schedule


async def _collect(session, liveness=None, *, now: datetime = NOW):
    """Единственное место, знающее ФОРМУ ответа сборки.

    Задача 3 меняет ответ со списка на структуру с признаком потолка; тесты
    признаков не обязаны об этом знать, поэтому форму разбирает один хелпер.
    """
    return (await collect_incidents(session, liveness or {}, now=now)).incidents


def _kinds(incidents) -> list[str]:
    return [incident.kind for incident in incidents]


# --- Признак 1: воркер не забирает работу (D-45.1) ----------------------------


def test_a_worker_with_work_and_a_stale_heartbeat_raises_the_incident():
    liveness = {
        7: WorkerLiveness(
            queue_depth=3, heartbeat_fresh=False, last_seen_at=NOW - timedelta(minutes=5)
        )
    }
    incidents = detect_worker_stuck(liveness, now=NOW)
    assert _kinds(incidents) == [INCIDENT_KIND_WORKER_STUCK]
    assert incidents[0].subject_id == 7
    assert incidents[0].at == NOW - timedelta(minutes=5)


def test_a_fresh_heartbeat_clears_the_worker_incident():
    liveness = {
        7: WorkerLiveness(queue_depth=3, heartbeat_fresh=True, last_seen_at=NOW)
    }
    assert detect_worker_stuck(liveness, now=NOW) == []


def test_an_empty_queue_with_a_stale_heartbeat_is_idle_and_not_an_incident():
    """Простой — не отказ (D-08, Pitfall 2).

    Воркеры самоубиваются по бездействию, а поднимаются только под непустую
    очередь: отсутствие heartbeat при пустой очереди есть ШТАТНОЕ состояние.
    Признак, красящий его красным, заставляет администратора звонить по каждому
    простою — и через неделю он перестаёт смотреть блок вовсе.
    """
    liveness = {
        7: WorkerLiveness(queue_depth=0, heartbeat_fresh=False, last_seen_at=None)
    }
    assert detect_worker_stuck(liveness, now=NOW) == []


# --- Признак 2: аккаунт отвалился (D-45.2) ------------------------------------


@pytest.mark.asyncio
async def test_a_downed_account_raises_the_incident(db_session):
    await _seed_account(
        db_session,
        account_id=1,
        status="disconnected",
        last_synced_at=NOW - timedelta(hours=2),
    )
    incidents = await _collect(db_session)
    assert _kinds(incidents) == [INCIDENT_KIND_ACCOUNT_DOWN]
    assert incidents[0].subject_id == 1


@pytest.mark.asyncio
async def test_a_return_to_active_clears_the_account_incident(db_session):
    account = await _seed_account(
        db_session,
        account_id=1,
        status="sync_failed",
        last_synced_at=NOW - timedelta(hours=2),
    )
    assert _kinds(await _collect(db_session)) == [INCIDENT_KIND_ACCOUNT_DOWN]

    account.status = "active"
    await db_session.flush()
    assert await _collect(db_session) == []


def test_both_downed_statuses_are_declared_as_a_set_and_active_is_not_one():
    assert ACCOUNT_DOWN_STATUSES == frozenset({"disconnected", "sync_failed"})
    assert "active" not in ACCOUNT_DOWN_STATUSES


# --- Признак 3: всплеск отказов отправки (D-45.3, порог — D-51) ---------------


def test_a_failure_ratio_above_the_threshold_raises_the_spike():
    incident = detect_failure_spike(
        total=FAILURE_SPIKE_MIN_TOTAL,
        failed=FAILURE_SPIKE_MIN_TOTAL,
        last_failure_at=NOW - timedelta(minutes=3),
        now=NOW,
    )
    assert incident is not None
    assert incident.kind == INCIDENT_KIND_FAILURE_SPIKE
    assert incident.at == NOW - timedelta(minutes=3)


def test_the_same_ratio_below_the_volume_floor_does_not_raise_the_spike():
    """Нижняя граница объёма — записанная решением ЦЕНА, а не недосмотр (D-51).

    Доля здесь та же самая, что в тесте выше, и признак всё равно не поднимается:
    без нижней границы одна неудача из двух даёт 50% и вечный горящий инцидент.
    Правка, «уточняющая» границу до нуля, краснит именно этот тест.
    """
    below = FAILURE_SPIKE_MIN_TOTAL - 1
    assert (
        detect_failure_spike(
            total=below, failed=below, last_failure_at=NOW, now=NOW
        )
        is None
    )


def test_a_ratio_falling_below_the_threshold_clears_the_spike():
    total = FAILURE_SPIKE_MIN_TOTAL * 2
    failed = int(total * FAILURE_SPIKE_RATIO) - 1
    assert (
        detect_failure_spike(
            total=total, failed=failed, last_failure_at=NOW, now=NOW
        )
        is None
    )


@pytest.mark.asyncio
async def test_the_spike_is_counted_over_the_declared_window_and_not_wider(db_session):
    """Окно есть ЧАС (D-45.3, D-51), а не скользящие сутки модуля аналитики.

    Отказы часовой давности плюс один час — вне окна: авария, растворённая в
    суточной доле, перестаёт быть всплеском, а плитка «Ошибок за сутки» и блок
    инцидентов отвечают на РАЗНЫЕ вопросы (D-40).
    """
    outside = NOW - timedelta(minutes=FAILURE_SPIKE_WINDOW_MIN + 5)
    await _seed_send_logs(
        db_session, statuses=[STATUS_FAIL] * FAILURE_SPIKE_MIN_TOTAL, sent_at=outside
    )
    assert INCIDENT_KIND_FAILURE_SPIKE not in _kinds(await _collect(db_session))


@pytest.mark.asyncio
async def test_the_spike_reads_both_failing_statuses_and_not_only_fail(db_session):
    """`account_disconnected` — такая же несостоявшаяся отправка, как `fail`.

    Множество неуспешных статусов читается из объявления модуля аналитики; своя
    копия в условии считала бы ноль ошибок ровно при отвалившемся аккаунте.
    """
    inside = NOW - timedelta(minutes=5)
    await _seed_send_logs(
        db_session,
        statuses=[STATUS_ACCOUNT_DISCONNECTED] * FAILURE_SPIKE_MIN_TOTAL,
        sent_at=inside,
    )
    assert INCIDENT_KIND_FAILURE_SPIKE in _kinds(await _collect(db_session))


# --- Признак 4: платежи залипли (D-45.4, Pitfall 12) --------------------------


@pytest.mark.asyncio
async def test_an_unclosed_payment_older_than_the_ttl_raises_the_incident(db_session):
    await _seed_payment(
        db_session,
        payment_id=1,
        created_at=NOW - timedelta(hours=PENDING_INTENT_TTL_HOURS + 1),
    )
    incidents = await _collect(db_session)
    assert _kinds(incidents) == [INCIDENT_KIND_PAYMENT_STUCK]
    assert incidents[0].subject_id == 1


@pytest.mark.asyncio
async def test_a_fresh_unclosed_payment_does_not_raise_the_incident(db_session):
    """Возраст считается от момента СОЗДАНИЯ (Pitfall 12).

    У незакрытого платежа момент подтверждения пуст ВСЕГДА, поэтому реализация,
    считающая возраст от него, либо падает, либо молчит. Эта строка свежа по
    моменту создания и пуста по моменту подтверждения — она краснит обе.
    """
    await _seed_payment(
        db_session,
        payment_id=1,
        created_at=NOW - timedelta(hours=PENDING_INTENT_TTL_HOURS - 1),
    )
    assert await _collect(db_session) == []


@pytest.mark.asyncio
async def test_a_terminal_status_clears_the_payment_incident(db_session):
    await _seed_payment(
        db_session,
        payment_id=1,
        created_at=NOW - timedelta(hours=PENDING_INTENT_TTL_HOURS + 1),
    )
    assert _kinds(await _collect(db_session)) == [INCIDENT_KIND_PAYMENT_STUCK]

    payment = await db_session.get(Payment, 1)
    payment.status = STATUS_CANCELED
    await db_session.flush()
    assert await _collect(db_session) == []


# --- Признак 5: планировщик не дышит (D-45.5) ---------------------------------


@pytest.mark.asyncio
async def test_a_schedule_overdue_longer_than_the_threshold_raises_the_incident(
    db_session,
):
    overdue_at = NOW - timedelta(seconds=BEAT_SILENT_OVERDUE_SEC + 60)
    await _seed_schedule(db_session, schedule_id=1, next_run_at=overdue_at)
    incidents = await _collect(db_session)
    assert _kinds(incidents) == [INCIDENT_KIND_BEAT_SILENT]
    assert incidents[0].at == overdue_at


@pytest.mark.asyncio
async def test_moving_the_next_run_forward_clears_the_beat_incident(db_session):
    schedule = await _seed_schedule(
        db_session,
        schedule_id=1,
        next_run_at=NOW - timedelta(seconds=BEAT_SILENT_OVERDUE_SEC + 60),
    )
    assert _kinds(await _collect(db_session)) == [INCIDENT_KIND_BEAT_SILENT]

    schedule.next_run_at = _naive(NOW + timedelta(minutes=10))
    await db_session.flush()
    assert await _collect(db_session) == []


@pytest.mark.asyncio
async def test_an_inactive_schedule_does_not_wake_the_beat_incident(db_session):
    await _seed_schedule(
        db_session,
        schedule_id=1,
        next_run_at=NOW - timedelta(days=30),
        is_active=False,
    )
    assert await _collect(db_session) == []


# --- Время инцидента: последний НАБЛЮДЁННЫЙ след (D-47) -----------------------


@pytest.mark.asyncio
async def test_the_account_incident_time_is_the_last_observed_disconnect_trace(
    db_session,
):
    last_trace = NOW - timedelta(minutes=20)
    await _seed_account(
        db_session,
        account_id=1,
        status="disconnected",
        last_synced_at=NOW - timedelta(hours=6),
    )
    await _seed_send_logs(
        db_session,
        statuses=[STATUS_ACCOUNT_DISCONNECTED],
        sent_at=NOW - timedelta(hours=3),
    )
    await _seed_send_logs(
        db_session, statuses=[STATUS_ACCOUNT_DISCONNECTED], sent_at=last_trace
    )
    incidents = await _collect(db_session)
    assert incidents[0].at == last_trace


@pytest.mark.asyncio
async def test_without_a_disconnect_trace_the_account_time_is_the_last_sync(db_session):
    """Колонки времени смены состояния у аккаунта НЕТ (D-47).

    Подпись «с 11:42» честна ровно в том смысле, в каком объявлена: это момент,
    когда отказ последний раз НАБЛЮДАЛСЯ. Ради подписи миграция не заводится.
    """
    synced_at = NOW - timedelta(hours=4)
    await _seed_account(
        db_session, account_id=1, status="disconnected", last_synced_at=synced_at
    )
    await _seed_send_logs(
        db_session, statuses=[STATUS_OK], sent_at=NOW - timedelta(minutes=1)
    )
    incidents = await _collect(db_session)
    assert incidents[0].at == synced_at


# --- Переносимость арифметики над временем (Pitfall 1) ------------------------


@pytest.mark.asyncio
async def test_every_signal_survives_the_naive_moments_sqlite_returns(db_session):
    """Все моменты сидированы БЕЗ таймзоны — как их отдаёт SQLite.

    Вычитание naive из aware поднимает `TypeError`, поэтому реализация без
    приведения зелена на PostgreSQL и красна здесь — либо наоборот. Этот тест
    поднимает все пять признаков разом и утверждает, что ни один не упал.
    """
    await _seed_account(
        db_session,
        account_id=1,
        status="disconnected",
        last_synced_at=NOW - timedelta(hours=2),
    )
    await _seed_payment(
        db_session,
        payment_id=1,
        created_at=NOW - timedelta(hours=PENDING_INTENT_TTL_HOURS + 1),
    )
    await _seed_schedule(
        db_session,
        schedule_id=1,
        next_run_at=NOW - timedelta(seconds=BEAT_SILENT_OVERDUE_SEC + 60),
    )
    await _seed_send_logs(
        db_session,
        statuses=[STATUS_FAIL] * FAILURE_SPIKE_MIN_TOTAL,
        sent_at=NOW - timedelta(minutes=5),
    )
    liveness = {
        7: WorkerLiveness(
            queue_depth=1, heartbeat_fresh=False, last_seen_at=NOW - timedelta(minutes=9)
        )
    }

    incidents = await _collect(db_session, liveness)

    assert set(_kinds(incidents)) == {
        INCIDENT_KIND_WORKER_STUCK,
        INCIDENT_KIND_ACCOUNT_DOWN,
        INCIDENT_KIND_FAILURE_SPIKE,
        INCIDENT_KIND_PAYMENT_STUCK,
        INCIDENT_KIND_BEAT_SILENT,
    }
    assert all(incident.at.tzinfo is not None for incident in incidents)


# --- Отрицательный контроль: модуль не знает внешних клиентов -----------------

FORBIDDEN_CLIENT_ROOTS = frozenset({"redis", "aioredis", "docker", "httpx", "yookassa"})


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def test_the_module_imports_no_client_of_an_external_service():
    """Утверждение об ИСТОЧНИКЕ, а не о поведении.

    Признаки обязаны проверяться суитой без единой поднятой службы, и держит это
    не договорённость, а отсутствие импорта: клиент, попавший в модуль, сделал бы
    зелёный прогон невозможным без стенда. Разбор дерева ловит добавление импорта
    в момент добавления, а не на первом красном прогоне у того, у кого стенда нет.
    """
    assert not (_imported_roots(INCIDENTS_MODULE) & FORBIDDEN_CLIENT_ROOTS)


def test_the_module_declares_five_kinds_and_not_four():
    kinds = {
        INCIDENT_KIND_WORKER_STUCK,
        INCIDENT_KIND_ACCOUNT_DOWN,
        INCIDENT_KIND_FAILURE_SPIKE,
        INCIDENT_KIND_PAYMENT_STUCK,
        INCIDENT_KIND_BEAT_SILENT,
    }
    assert len(kinds) == 5


# ============================================================================
# Задача 3: сборка блока — порядок, потолок, пустота и адрес «куда чинить»
# ============================================================================


def _select_statements(statements: list[str]) -> list[str]:
    return [s for s in statements if s.lstrip().upper().startswith("SELECT")]


async def _collect_board(session, liveness=None, *, now: datetime = NOW):
    return await collect_incidents(session, liveness or {}, now=now)


@pytest.mark.asyncio
async def test_a_healthy_service_returns_an_empty_board(db_session):
    """Пустота — ВАЛИДНЫЙ ответ, а не признак поломки сборки.

    «Сейчас ничего не сломано» — это то, что блок обязан уметь сказать. Сборка,
    падающая или молчащая на здоровом сервисе, делает блок неотличимым от
    сломанного показа ровно в тот момент, когда всё в порядке.
    """
    await _seed_account(db_session, account_id=1, status="active")
    board = await _collect_board(db_session)
    assert board.incidents == ()
    assert board.capped is False


@pytest.mark.asyncio
async def test_incidents_are_ordered_by_the_freshest_trace_first(db_session):
    """Свежая авария важнее давней: порядок — по убыванию времени следа."""
    await _seed_account(
        db_session,
        account_id=1,
        status="disconnected",
        last_synced_at=NOW - timedelta(hours=9),
    )
    await _seed_payment(
        db_session,
        payment_id=1,
        created_at=NOW - timedelta(hours=PENDING_INTENT_TTL_HOURS + 2),
    )
    liveness = {
        7: WorkerLiveness(
            queue_depth=2, heartbeat_fresh=False, last_seen_at=NOW - timedelta(minutes=2)
        )
    }
    board = await _collect_board(db_session, liveness)
    moments = [incident.at for incident in board.incidents]
    assert moments == sorted(moments, reverse=True)
    assert board.incidents[0].kind == INCIDENT_KIND_WORKER_STUCK


@pytest.mark.asyncio
async def test_the_number_of_queries_does_not_grow_with_the_number_of_incidents(
    db_session,
):
    """Блок живёт на «Обзоре», куда заходят В МОМЕНТ АВАРИИ (T-06-INC1).

    Запрос на строку умножился бы ровно тогда, когда база и так под нагрузкой,
    и стоимость показа росла бы вместе с тяжестью аварии.
    """
    sync_engine = db_session.bind.sync_engine

    async def _count_queries(liveness) -> int:
        statements: list[str] = []

        def _record(conn, cursor, statement, parameters, context, executemany):
            statements.append(statement)

        event.listen(sync_engine, "before_cursor_execute", _record)
        try:
            await _collect_board(db_session, liveness)
        finally:
            event.remove(sync_engine, "before_cursor_execute", _record)
        return len(_select_statements(statements))

    await _seed_account(
        db_session,
        account_id=1,
        status="disconnected",
        last_synced_at=NOW - timedelta(hours=1),
    )
    await _seed_payment(
        db_session,
        payment_id=1,
        created_at=NOW - timedelta(hours=PENDING_INTENT_TTL_HOURS + 1),
    )
    few = await _count_queries({})

    for extra in range(2, 12):
        await _seed_account(
            db_session,
            account_id=extra,
            user_id=extra,
            status="sync_failed",
            last_synced_at=NOW - timedelta(hours=extra),
        )
        await _seed_payment(
            db_session,
            payment_id=extra,
            user_id=extra,
            created_at=NOW - timedelta(hours=PENDING_INTENT_TTL_HOURS + extra),
        )
    many = await _count_queries({})

    board = await _collect_board(db_session)
    assert len(board.incidents) > 2
    assert few == many, f"запросов было {few}, стало {many}"


@pytest.mark.asyncio
async def test_the_cap_truncates_and_names_itself_in_its_own_field(db_session):
    """Сработавший потолок ОБЯЗАН НАЗЫВАТЬ СЕБЯ — правило проекта.

    Молча короткий перечень читается как «других инцидентов нет», то есть как
    ответ на вопрос, ради которого администратор в блок и смотрит. Признак
    срабатывания — ОТДЕЛЬНОЕ поле, а не вывод из длины перечня: длина, равная
    потолку, случайно совпасть может, а поле — нет.
    """
    for number in range(1, INCIDENT_LIST_CAP + 5):
        await _seed_payment(
            db_session,
            payment_id=number,
            user_id=number,
            created_at=NOW - timedelta(hours=PENDING_INTENT_TTL_HOURS + number),
        )
    board = await _collect_board(db_session)
    assert len(board.incidents) == INCIDENT_LIST_CAP
    assert board.capped is True


@pytest.mark.asyncio
async def test_every_incident_carries_a_destination_declared_for_its_kind(db_session):
    """Строка без адреса сообщает об аварии и не говорит, что с ней делать (D-48)."""
    await _seed_account(
        db_session,
        account_id=1,
        status="disconnected",
        last_synced_at=NOW - timedelta(hours=2),
    )
    await _seed_payment(
        db_session,
        payment_id=1,
        created_at=NOW - timedelta(hours=PENDING_INTENT_TTL_HOURS + 1),
    )
    await _seed_schedule(
        db_session,
        schedule_id=1,
        next_run_at=NOW - timedelta(seconds=BEAT_SILENT_OVERDUE_SEC + 60),
    )
    await _seed_send_logs(
        db_session,
        statuses=[STATUS_FAIL] * FAILURE_SPIKE_MIN_TOTAL,
        sent_at=NOW - timedelta(minutes=5),
    )
    liveness = {
        7: WorkerLiveness(queue_depth=1, heartbeat_fresh=False, last_seen_at=NOW)
    }
    board = await _collect_board(db_session, liveness)

    assert set(INCIDENT_DESTINATIONS) == {
        INCIDENT_KIND_WORKER_STUCK,
        INCIDENT_KIND_ACCOUNT_DOWN,
        INCIDENT_KIND_FAILURE_SPIKE,
        INCIDENT_KIND_PAYMENT_STUCK,
        INCIDENT_KIND_BEAT_SILENT,
    }
    assert {incident.kind for incident in board.incidents} == set(INCIDENT_DESTINATIONS)
    for incident in board.incidents:
        assert incident.href
        assert incident.href.startswith(INCIDENT_DESTINATIONS[incident.kind])


@pytest.mark.asyncio
async def test_no_recovered_row_is_ever_returned(db_session):
    """Зелёных строк «восстановлен» нет ни в каком виде (D-46).

    Восстановление — СОБЫТИЕ, а не состояние: чтобы его показать, понадобилась бы
    история, то есть отклонённая трижды таблица. Аккаунт, вернувшийся в рабочее
    состояние, обязан исчезнуть из блока молча, а не оставить зелёную строку.
    """
    await _seed_account(db_session, account_id=1, status="active")
    await _seed_send_logs(
        db_session,
        statuses=[STATUS_ACCOUNT_DISCONNECTED],
        sent_at=NOW - timedelta(minutes=30),
    )
    board = await _collect_board(db_session)
    assert board.incidents == ()

    source = INCIDENTS_MODULE.read_text(encoding="utf-8").lower()
    for token in ("recovered", "restored", "восстановлен"):
        assert f'"{token}' not in source and f"'{token}" not in source
