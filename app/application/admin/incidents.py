"""Пять признаков инцидента: что сломано ПРЯМО СЕЙЧАС (D-43…D-48, ADMIN-11).

ИНЦИДЕНТ ЕСТЬ СОСТОЯНИЕ, А НЕ СОБЫТИЕ. Ни таблицы инцидентов, ни ленты событий
проект не заводит — таблица отклонена третий раз подряд (Фаза 4 D-05, здесь
D-43 и D-24). Источник логов тоже отвергнут и не по доступности, а по существу:
строка лога отвечает на «БЫЛО ЛИ», а инцидент держится, пока не починен, и
вопрос к нему — «СЛОМАНО ЛИ СЕЙЧАС». Вдобавок источник логов у проекта
опционален (D-28), а блок на «Обзоре» обязан работать всегда.

СЛЕДСТВИЕ, КОТОРОЕ И ЕСТЬ ГЛАВНОЕ ПРАВИЛО МОДУЛЯ. Раз состояние выводится на
лету, УСЛОВИЕ СНЯТИЯ перестаёт быть удобством и становится ЕДИНСТВЕННЫМ
способом инциденту исчезнуть (D-44). Ручного «закрыть инцидент» здесь нет и не
заводится: закрытие вручную немедленно потребовало бы хранилища закрытых — той
самой отклонённой таблицы, — а блок, который нельзя очистить, администратор
перестаёт читать через неделю. Поэтому у каждого из пяти признаков ниже
выписаны ОБЕ стороны, и обе закреплены отдельными тестами.

ПОЧЕМУ МОДУЛЬ НИЧЕГО НЕ ИМПОРТИРУЕТ ИЗ СЕРВИСОВ. Пять признаков обязаны
проверяться суитой, которая идёт на SQLite БЕЗ единой поднятой службы. Живость
воркеров живёт у брокера, и импорт его клиента сделал бы зелёный прогон
невозможным без стенда — то есть перевёл бы проверку признаков в разряд ручной.
Поэтому живость приезжает сюда СЛОВАРЁМ ЗНАЧЕНИЙ (`WorkerLiveness`), ровно тем,
что отдаёт сервис оперативного состояния, а модуль не знает ни одного клиента.
Отсутствие импорта держится не договорённостью, а разбором дерева модуля в
`tests/test_application/test_incidents.py`.

ЧЕГО МОДУЛЬ НЕ ДЕЛАЕТ:

- не знает про Jinja, шаблоны и разметку: наружу выходят значения, а не строки
  разметки; показ блока со ссылками — предмет плана 06-10;
- ничего не пишет в БД: все функции только читают;
- не заводит своих чисел там, где у проекта число уже объявлено (см. «Числа»
  ниже) — второй ответ на один вопрос разошёлся бы с первым молча.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Mapping, Sequence

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import (
    FAILED_STATUSES,
    STATUS_ACCOUNT_DISCONNECTED,
    STATUS_FAIL,
    normalize_utc,
)
from app.config import Settings
from app.models.messenger_account import MessengerAccount
from app.models.payment import Payment
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.services.payment_service import PENDING_INTENT_TTL_HOURS, TERMINAL_STATUSES

# --- Виды инцидента (D-45) ----------------------------------------------------
#
# Перечень ЗАКРЫТ на пяти. Шестой вид — правка ROADMAP и добавление признака
# рядом, а не переделка модуля: форма ответа от числа видов не зависит.
INCIDENT_KIND_WORKER_STUCK = "worker_stuck"  # D-45.1
INCIDENT_KIND_ACCOUNT_DOWN = "account_down"  # D-45.2
INCIDENT_KIND_FAILURE_SPIKE = "failure_spike"  # D-45.3
INCIDENT_KIND_PAYMENT_STUCK = "payment_stuck"  # D-45.4
INCIDENT_KIND_BEAT_SILENT = "beat_silent"  # D-45.5

# --- Адреса «куда чинить» (D-48) ----------------------------------------------
#
# Строка без адреса сообщает об аварии и НЕ ГОВОРИТ, ЧТО С НЕЙ ДЕЛАТЬ. Адреса
# объявлены здесь, а не в шаблоне, потому что их обязаны называть одинаково
# сборка, тест и разметка «Обзора» (план 06-10); выписанный в шаблоне литерал
# разъехался бы со сборкой молча.
#
# Аккаунт ведёт в КАРТОЧКУ ПОЛЬЗОВАТЕЛЯ, а не в перечень: чинить отвалившуюся
# сессию администратор идёт к владельцу аккаунта (D-03, D-48).
HREF_WORKERS = "/admin/workers"
HREF_USER_CARD = "/admin/users/{user_id}"
HREF_PAYMENTS = "/admin/payments"
# «История» с фильтром по неуспешной отправке (D-48). Значение фильтра — та же
# строка статуса, которую объявляет модуль аналитики: своя копия разошлась бы с
# перечнем чипсов раздела истории.
HREF_SEND_HISTORY = "/history?status={status}"

# --- Числа: взятые, а не назначенные ------------------------------------------
#
# СОСТОЯНИЯ ОТВАЛА АККАУНТА — те же строки, которые пишет прикладной код
# синхронизации ("sync_failed", app/application/accounts/use_cases.py:60) и
# умолчание модели ("disconnected", app/models/messenger_account.py). Множество,
# а не сравнение с одной строкой: третье состояние, добавленное позже, не
# проедет мимо копии в условии.
ACCOUNT_DOWN_STATUSES = frozenset({"disconnected", "sync_failed"})

# ПОРОГ ВСПЛЕСКА ОТКАЗОВ — РЕШЕНИЕ ВЛАДЕЛЬЦА D-51, а не значение, выбранное
# исполнителем в момент написания константы. Вариант A: доля за окно с нижней
# границей объёма.
#
# Окно — ЧАС (D-45.3 буквально), а не скользящие сутки модуля аналитики: плитка
# «Ошибок за сутки» и блок инцидентов отвечают на РАЗНЫЕ вопросы (D-40), и
# авария десятиминутной давности растворилась бы в суточной доле, то есть
# перестала бы быть ВСПЛЕСКОМ ровно тогда, когда она и произошла.
FAILURE_SPIKE_WINDOW_MIN = 60

# ⚠️ НИЖНЯЯ ГРАНИЦА ОБЪЁМА СУЩЕСТВУЕТ ЗАТЕМ, ЧТОБЫ ДОЛЯ НЕ ВРАЛА НА МАЛОМ
# ЧИСЛЕ ОТПРАВОК. Без неё одна неудача из двух даёт 50% — то есть вечный горящий
# инцидент на любом тихом часе. Правка, «уточняющая» это число до нуля, вернёт
# ровно тот дефект; она краснит
# `test_the_same_ratio_below_the_volume_floor_does_not_raise_the_spike`.
#
# ЦЕНА ГРАНИЦЫ НАЗВАНА ВЕЛИЧИНОЙ И ПРИНЯТА (D-51): на сервисе, делающем меньше
# двадцати отправок в час, всплеск не виден ВООБЩЕ — а именно там он и означал
# бы, что сломано всё. Это осознанный размен, а не недосмотр.
FAILURE_SPIKE_MIN_TOTAL = 20
FAILURE_SPIKE_RATIO = 0.30

# ПРОСРОЧКА ПЛАНИРОВЩИКА ВЫВОДИТСЯ ИЗ ЕГО СОБСТВЕННОГО ИНТЕРВАЛА, а не
# назначается. Своё число здесь было бы ТРЕТЬИМ ответом на вопрос «как часто
# планировщик обязан просыпаться» — рядом с настройкой и с расписанием Celery,
# которое эту настройку читает.
#
# Значение берётся из ОБЪЯВЛЕНИЯ настройки, а не из живого экземпляра: создание
# экземпляра требует окружения (адрес базы и ключ подписи обязательны), а модуль
# обязан импортироваться и проверяться без окружения вовсе. Развёртывание,
# поднявшее интервал переменной среды, передаёт его в `collect_incidents`
# аргументом `beat_interval_sec`.
CELERY_BEAT_INTERVAL_SEC: int = Settings.model_fields["celery_beat_interval"].default

# Сколько подряд пропущенных проходов считаем отказом, а не задержкой. Один
# пропуск — это очередь задач под нагрузкой; десять подряд означают, что будить
# расписания некому.
BEAT_SILENT_MISSED_TICKS = 10

# Нижняя граница порога. При частом интервале (секунды) произведение выше дало бы
# порог в десятки секунд, и признак поднимался бы на каждой задержке отправки.
BEAT_SILENT_FLOOR_SEC = 300


def beat_silent_overdue_sec(beat_interval_sec: int) -> int:
    """Порог просрочки `next_run_at` при заданном интервале планировщика."""
    return max(int(beat_interval_sec) * BEAT_SILENT_MISSED_TICKS, BEAT_SILENT_FLOOR_SEC)


BEAT_SILENT_OVERDUE_SEC = beat_silent_overdue_sec(CELERY_BEAT_INTERVAL_SEC)


# --- Форма ответа -------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WorkerLiveness:
    """Живость воркера ЗНАЧЕНИЯМИ — вход признака D-45.1.

    Ни клиента брокера, ни адреса очереди здесь нет намеренно: сервис
    оперативного состояния читает их сам и отдаёт сюда уже прочитанное. Поэтому
    признак проверяется суитой без поднятой службы.

    `heartbeat_fresh` приходит РЕШЁННЫМ, а не сырым возрастом: порог свежести
    объявлен там, где heartbeat читается, и второй порог здесь разошёлся бы с
    первым молча. Глубина очереди приходит числом, потому что правило D-08
    считает именно её, а не факт «очередь непуста».
    """

    queue_depth: int
    heartbeat_fresh: bool
    last_seen_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Incident:
    """Одна строка блока: что сломано, с какого наблюдённого момента и куда идти.

    `at` — момент ПОСЛЕДНЕГО НАБЛЮДЁННОГО СЛЕДА отказа, а не момент смены
    состояния (D-47): колонки времени смены состояния проект не хранит, и
    подпись «с 11:42», выведенная из чего угодно другого, сообщила бы
    администратору выдуманную длительность аварии.

    `subject_id` — идентификатор предмета (аккаунта, платежа, воркера) для
    построения ссылки; у признаков без предмета его нет.
    """

    kind: str
    text: str
    at: datetime
    href: str
    subject_id: int | None = None


# --- Признак 1: воркер не забирает работу (D-45.1) ----------------------------


def detect_worker_stuck(
    liveness: Mapping[int, WorkerLiveness], *, now: datetime
) -> list[Incident]:
    """Непустая очередь И несвежий heartbeat.

    ПОДЪЁМ: `queue_depth > 0` и heartbeat несвеж. СНЯТИЕ: heartbeat снова свеж —
    либо очередь разобрана.

    ⚠️ ПУСТАЯ ОЧЕРЕДЬ ПРИ НЕСВЕЖЕМ HEARTBEAT — ЭТО ПРОСТОЙ, А НЕ ОТКАЗ (D-08).
    Воркеры самоубиваются по бездействию, а поднимаются только под непустую
    очередь: отсутствие heartbeat при пустой очереди есть ШТАТНОЕ состояние.
    Признак, красящий его красным, заставил бы администратора звонить по каждому
    простою — и через неделю он перестал бы смотреть блок вовсе. Закреплено
    `test_an_empty_queue_with_a_stale_heartbeat_is_idle_and_not_an_incident`.
    """
    incidents: list[Incident] = []
    for account_id, worker in sorted(liveness.items()):
        if worker.queue_depth <= 0 or worker.heartbeat_fresh:
            continue
        incidents.append(
            Incident(
                kind=INCIDENT_KIND_WORKER_STUCK,
                text=(
                    f"Воркер аккаунта {account_id} не забирает работу: "
                    f"в очереди {worker.queue_depth}, отклика нет"
                ),
                at=normalize_utc(worker.last_seen_at) or normalize_utc(now),
                href=HREF_WORKERS,
                subject_id=account_id,
            )
        )
    return incidents


# --- Признак 2: аккаунт отвалился (D-45.2) ------------------------------------


@dataclass(frozen=True, slots=True)
class DownAccountRow:
    """Строка отвалившегося аккаунта — значения, уже прочитанные из базы."""

    account_id: int
    user_id: int
    messenger_type: str | None
    status: str
    last_synced_at: datetime | None


def detect_account_down(
    accounts: Sequence[DownAccountRow],
    traces: Mapping[tuple[int, str | None], datetime | None],
    *,
    now: datetime,
) -> list[Incident]:
    """Состояние аккаунта в множестве отвала.

    ПОДЪЁМ: `status` ∈ `ACCOUNT_DOWN_STATUSES`. СНЯТИЕ: возврат в рабочее
    состояние — отбор идёт по множеству отвала, поэтому любое состояние вне его
    снимает строку само.

    ВРЕМЯ — ПОСЛЕДНИЙ НАБЛЮДЁННЫЙ СЛЕД (D-47): момент последней записи журнала
    со статусом отвала, а при её отсутствии — момент последней синхронизации.
    След ищется по паре «владелец и канал», потому что журнал отправок хранит
    владельца и канал, но не аккаунт; это самая узкая связь, которую даёт схема,
    и заводить ради подписи колонку значило бы заводить миграцию.
    """
    incidents: list[Incident] = []
    for row in accounts:
        if row.status not in ACCOUNT_DOWN_STATUSES:
            continue
        trace_at = normalize_utc(traces.get((row.user_id, row.messenger_type)))
        at = trace_at or normalize_utc(row.last_synced_at) or normalize_utc(now)
        incidents.append(
            Incident(
                kind=INCIDENT_KIND_ACCOUNT_DOWN,
                text=(
                    f"Аккаунт {row.account_id} пользователя {row.user_id} отвалился "
                    f"({row.status})"
                ),
                at=at,
                href=HREF_USER_CARD.format(user_id=row.user_id),
                subject_id=row.account_id,
            )
        )
    return incidents


# --- Признак 3: всплеск отказов отправки (D-45.3, порог — D-51) ---------------


def detect_failure_spike(
    *,
    total: int,
    failed: int,
    last_failure_at: datetime | None,
    now: datetime,
) -> Incident | None:
    """Доля неуспешных за окно выше порога при объёме не ниже границы.

    ПОДЪЁМ: `total >= FAILURE_SPIKE_MIN_TOTAL` И
    `failed / total >= FAILURE_SPIKE_RATIO`. СНЯТИЕ: падение доли ниже порога —
    либо уход объёма ниже границы вместе с концом окна.

    Обе части условия обязательны, и вторая без первой — известный дефект: на
    двух отправках одна неудача даёт 50% и вечный горящий инцидент (D-51).
    """
    if total < FAILURE_SPIKE_MIN_TOTAL:
        return None
    if failed / total < FAILURE_SPIKE_RATIO:
        return None
    share = round(failed / total * 100)
    return Incident(
        kind=INCIDENT_KIND_FAILURE_SPIKE,
        text=(
            f"Всплеск отказов отправки: {failed} из {total} за последний час "
            f"({share}%)"
        ),
        at=normalize_utc(last_failure_at) or normalize_utc(now),
        href=HREF_SEND_HISTORY.format(status=STATUS_FAIL),
    )


# --- Признак 4: платежи залипли (D-45.4, Pitfall 12) --------------------------


@dataclass(frozen=True, slots=True)
class UnclosedPaymentRow:
    """Незакрытый платёж — значения, уже прочитанные из базы.

    ⚠️ МОМЕНТА ПОДТВЕРЖДЕНИЯ ЗДЕСЬ НЕТ, И ЭТО НЕ УПУЩЕНИЕ. У незакрытого платежа
    он пуст ВСЕГДА, и арифметика от него даёт либо исключение, либо тишину
    (Pitfall 12). Возраст считается от момента СОЗДАНИЯ — единственного момента,
    который у такой строки существует. Закреплено
    `test_a_fresh_unclosed_payment_does_not_raise_the_incident`.
    """

    payment_id: int
    user_id: int
    created_at: datetime | None


def detect_payment_stuck(
    payments: Sequence[UnclosedPaymentRow], *, now: datetime
) -> list[Incident]:
    """Незакрытый платёж старше уже объявленного проектом срока давности.

    ПОДЪЁМ: возраст от момента создания больше `PENDING_INTENT_TTL_HOURS`.
    СНЯТИЕ: терминальный статус — отбор идёт по ОТСУТСТВИЮ терминального
    статуса (`unclosed_payments_stmt`), поэтому закрытая строка выпадает сама.

    Срок давности ВЗЯТ у платёжного сервиса, а не назначен: его комментарий
    объясняет, ЗАЧЕМ константа существует (подписка на отмену у платёжного
    провайдера не подтверждена, и отменённый платёж остаётся незакрытым
    навсегда), и второе число на тот же вопрос разошлось бы с первым молча.
    """
    threshold = normalize_utc(now) - timedelta(hours=PENDING_INTENT_TTL_HOURS)
    incidents: list[Incident] = []
    for row in payments:
        created = normalize_utc(row.created_at)
        if created is None or created > threshold:
            continue
        incidents.append(
            Incident(
                kind=INCIDENT_KIND_PAYMENT_STUCK,
                text=(
                    f"Платёж {row.payment_id} пользователя {row.user_id} "
                    f"не закрыт дольше {PENDING_INTENT_TTL_HOURS} ч"
                ),
                at=created,
                href=HREF_PAYMENTS,
                subject_id=row.payment_id,
            )
        )
    return incidents


def unclosed_payments_stmt():
    """Отбор незакрытых платежей — ЕДИНСТВЕННОЕ место правила статуса.

    Отбор по ОТСУТСТВИЮ терминального статуса, а не по равенству одному
    статусу: множество терминальных объявлено проектом ровно затем, чтобы третья
    ветка, добавленная позже, не проехала мимо копии в условии.
    """
    return select(Payment.id, Payment.user_id, Payment.created_at).where(
        Payment.status.not_in(tuple(TERMINAL_STATUSES))
    )


# --- Признак 5: планировщик не дышит (D-45.5) ---------------------------------


def detect_beat_silent(
    *,
    overdue_count: int,
    latest_overdue_at: datetime | None,
    threshold_sec: int,
    now: datetime,
) -> Incident | None:
    """Активные расписания с моментом запуска в прошлом дольше порога.

    ПОДЪЁМ: есть хотя бы одно просроченное активное расписание. СНЯТИЕ: сдвиг
    момента запуска вперёд — то есть проснувшийся планировщик, который сдвигает
    его сам.

    Признак ловит упавший планировщик, падение которого сегодня не видно нигде,
    кроме отсутствия рассылок.

    ВРЕМЯ — ПОЗДНЕЙШИЙ пропущенный момент, а не самый ранний: это последний раз,
    когда планировщик обязан был проснуться и не проснулся, то есть последний
    НАБЛЮДЁННЫЙ след отказа (D-47).
    """
    if overdue_count <= 0:
        return None
    return Incident(
        kind=INCIDENT_KIND_BEAT_SILENT,
        text=(
            f"Планировщик не просыпается: {overdue_count} расписаний просрочено "
            f"дольше {threshold_sec // 60} мин"
        ),
        at=normalize_utc(latest_overdue_at) or normalize_utc(now),
        href=HREF_WORKERS,
    )


# --- Сборка над базой ---------------------------------------------------------


async def collect_incidents(
    session: AsyncSession,
    liveness: Mapping[int, WorkerLiveness] | None = None,
    *,
    now: datetime | None = None,
    beat_interval_sec: int | None = None,
) -> list[Incident]:
    """Все пять признаков разом: четыре из базы, один — из поданной живости.

    ЧИСЛО ОБРАЩЕНИЙ К БАЗЕ НЕ ЗАВИСИТ ОТ ЧИСЛА НАЙДЕННЫХ ИНЦИДЕНТОВ. Блок живёт
    на «Обзоре», куда администратор заходит В МОМЕНТ АВАРИИ: запрос на строку
    умножился бы ровно тогда, когда база и так под нагрузкой.

    Каждый момент, пришедший из базы, проводится через приведение к единой зоне.
    Это не перестраховка: колонки объявлены с зоной, SQLite отдаёт их без зоны,
    PostgreSQL — с зоной, и вычитание без приведения падает ровно на одном из
    двух диалектов — то есть у пользователя, а не в суите (Pitfall 1).
    """
    moment = normalize_utc(now) if now else datetime.now(timezone.utc)
    threshold_sec = beat_silent_overdue_sec(
        beat_interval_sec if beat_interval_sec is not None else CELERY_BEAT_INTERVAL_SEC
    )

    incidents: list[Incident] = list(detect_worker_stuck(liveness or {}, now=moment))

    # (1) Отвалившиеся аккаунты.
    down_rows = (
        await session.execute(
            select(
                MessengerAccount.id,
                MessengerAccount.user_id,
                MessengerAccount.type,
                MessengerAccount.status,
                MessengerAccount.last_synced_at,
            ).where(MessengerAccount.status.in_(tuple(ACCOUNT_DOWN_STATUSES)))
        )
    ).all()
    accounts = [
        DownAccountRow(
            account_id=row[0],
            user_id=row[1],
            messenger_type=row[2],
            status=row[3],
            last_synced_at=row[4],
        )
        for row in down_rows
    ]

    # (2) Последний наблюдённый след отвала — одним сгруппированным запросом на
    # ВСЕ аккаунты сразу, а не по запросу на строку.
    traces: dict[tuple[int, str | None], datetime | None] = {}
    if accounts:
        trace_rows = (
            await session.execute(
                select(
                    SendLog.user_id,
                    SendLog.messenger_type,
                    func.max(SendLog.sent_at),
                )
                .where(SendLog.status == STATUS_ACCOUNT_DISCONNECTED)
                .group_by(SendLog.user_id, SendLog.messenger_type)
            )
        ).all()
        traces = {(row[0], row[1]): row[2] for row in trace_rows}
    incidents.extend(detect_account_down(accounts, traces, now=moment))

    # (3) Всплеск отказов: объём, число неуспешных и момент последнего неуспеха —
    # одним запросом, а не тремя.
    window_start = moment - timedelta(minutes=FAILURE_SPIKE_WINDOW_MIN)
    is_failed = SendLog.status.in_(tuple(FAILED_STATUSES))
    spike_row = (
        await session.execute(
            select(
                func.count(SendLog.id),
                func.sum(case((is_failed, 1), else_=0)),
                func.max(case((is_failed, SendLog.sent_at))),
            ).where(SendLog.sent_at >= window_start)
        )
    ).one()
    spike = detect_failure_spike(
        total=int(spike_row[0] or 0),
        failed=int(spike_row[1] or 0),
        last_failure_at=_parse_moment(spike_row[2]),
        now=moment,
    )
    if spike is not None:
        incidents.append(spike)

    # (4) Незакрытые платежи.
    payment_rows = (await session.execute(unclosed_payments_stmt())).all()
    incidents.extend(
        detect_payment_stuck(
            [
                UnclosedPaymentRow(
                    payment_id=row[0], user_id=row[1], created_at=row[2]
                )
                for row in payment_rows
            ],
            now=moment,
        )
    )

    # (5) Вставший планировщик: число просроченных и позднейший пропущенный
    # момент — одним запросом.
    beat_cutoff = moment - timedelta(seconds=threshold_sec)
    beat_row = (
        await session.execute(
            select(func.count(Schedule.id), func.max(Schedule.next_run_at)).where(
                Schedule.is_active.is_(True),
                Schedule.next_run_at.is_not(None),
                Schedule.next_run_at < beat_cutoff,
            )
        )
    ).one()
    beat = detect_beat_silent(
        overdue_count=int(beat_row[0] or 0),
        latest_overdue_at=_parse_moment(beat_row[1]),
        threshold_sec=threshold_sec,
        now=moment,
    )
    if beat is not None:
        incidents.append(beat)

    return incidents


def _parse_moment(value: datetime | None) -> datetime | None:
    """Момент из агрегата, приведённый к единой зоне.

    `max()` сохраняет тип колонки на обоих диалектах и отдаёт `datetime`
    (проверено прогоном на SQLite), но зону НЕ сохраняет: SQLite отдаёт момент
    naive, PostgreSQL — aware. Дальше он сравнивается и вычитается в Python,
    поэтому приведение обязательно (Pitfall 1).
    """
    return normalize_utc(value)
