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
    normalize_utc,
)
from app.config import Settings
from app.models.messenger_account import MessengerAccount
from app.models.payment import Payment
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.services.payment_service import AWAITING_STATUSES, PENDING_INTENT_TTL_HOURS

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
# ⚠️ АДРЕС ВСПЛЕСКА ОТКАЗОВ — «ЛОГИ», А НЕ «ИСТОРИЯ». ПРАВКА D-48, решение
# владельца, с причиной.
#
# D-48 записывал «отказы → „История“ с фильтром». Адрес заменён, потому что
# признак и цель отвечали на РАЗНЫЕ вопросы: всплеск по D-51 считает отказы ПО
# ВСЕМУ СЕРВИСУ (`total >= 20` и `failed / total >= 0.30`), а `/history`
# фильтрует `SendLog.user_id == user.id` — это ЛИЧНАЯ лента того, кто смотрит.
# У администратора, который сам почти не рассылает, она пуста ровно в тот
# момент, когда инцидент горит; пустая лента при горящем инциденте читается как
# «всё в порядке», то есть отвечает на вопрос ЛОЖНО. Ссылка «куда чинить»,
# ведущая туда, где аварии не видно, хуже отсутствия ссылки: она выглядит
# рабочей.
#
# Когда писался D-48, подраздела «Логи» ещё не существовало в построенном виде;
# теперь он отгружен планом 06-08 и отвечает на сервис-широкий вопрос напрямую.
HREF_SERVICE_ERRORS = "/admin/logs?level=error"

# Вид инцидента → КОРЕНЬ его адреса. Отображение объявлено ЦЕЛИКОМ и проверяется
# тестом на полноту: вид, заведённый без адреса, краснит прогон в момент
# добавления, а не показывает администратору строку, из которой некуда идти.
INCIDENT_DESTINATIONS: dict[str, str] = {
    INCIDENT_KIND_WORKER_STUCK: HREF_WORKERS,
    INCIDENT_KIND_ACCOUNT_DOWN: "/admin/users/",
    INCIDENT_KIND_FAILURE_SPIKE: HREF_SERVICE_ERRORS,
    INCIDENT_KIND_PAYMENT_STUCK: HREF_PAYMENTS,
    INCIDENT_KIND_BEAT_SILENT: HREF_WORKERS,
}

# ПОТОЛОК ЧИСЛА СТРОК БЛОКА. Потолок стоит не ради экономии рендера, а ради
# ОГРАНИЧЕННОСТИ выборки: число строк задаёт состояние системы, и перечень без
# границы растёт вместе с аварией — то есть ровно тогда, когда «Обзор» и так
# открывают под нагрузкой.
#
# ПОЧЕМУ ДВАДЦАТЬ. Блок — это то, что читают глазами в момент аварии; двадцать
# строк ещё читаются подряд, а сотня уже пролистывается, то есть перестаёт быть
# ответом на вопрос «что чинить первым».
#
# ⚠️ СРАБОТАВШИЙ ПОТОЛОК ОБЯЗАН НАЗЫВАТЬ СЕБЯ (правило проекта, ср.
# `PAYMENT_LIST_CAP`). Молча усечённый перечень читается как «других инцидентов
# нет» — то есть как ответ на вопрос, ради которого администратор в блок и
# пришёл. Признак срабатывания кладётся ОТДЕЛЬНЫМ полем `capped`, а не выводится
# из длины перечня: длина, равная потолку, совпасть случайно может, а поле — нет.
INCIDENT_LIST_CAP = 20

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


@dataclass(frozen=True, slots=True)
class IncidentBoard:
    """Готовый к показу блок: перечень и честная пометка сработавшего потолка.

    ПУСТОЙ ПЕРЕЧЕНЬ — ВАЛИДНЫЙ И ОЖИДАЕМЫЙ ОТВЕТ. Он означает «сейчас ничего не
    сломано», и показывать его нужно именно так. Строк «восстановлен после
    рестарта» здесь не бывает ни в каком виде (D-46): восстановление — событие,
    а не состояние, и для него понадобилась бы история, то есть отклонённая
    таблица.
    """

    incidents: tuple[Incident, ...]
    capped: bool


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
        href=HREF_SERVICE_ERRORS,
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
    СНЯТИЕ: ВЫХОД ИЗ НАБЛЮДАЕМЫХ статусов, а не приход в терминальный — отбор
    идёт по объявленному множеству наблюдаемых (`unclosed_payment_clause`),
    поэтому и закрытая строка, и снятая по сроку давности выпадают сами.

    Срок давности ВЗЯТ у платёжного сервиса, а не назначен: его комментарий
    объясняет, ЗАЧЕМ константа существует (подписка на отмену у платёжного
    провайдера не подтверждена, и отменённый платёж остаётся незакрытым
    навсегда), и второе число на тот же вопрос разошлось бы с первым молча.
    """
    threshold = payment_stuck_before(now)
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


def unclosed_payment_clause():
    """«Платёж не закрыт» — ЕДИНСТВЕННОЕ место этого правила на проект.

    Отбор ПОЛОЖИТЕЛЬНЫЙ: строка попадает под правило потому, что её статус
    ОБЪЯВЛЕН наблюдаемым (`AWAITING_STATUSES` платёжного сервиса), а не потому,
    что он не оказался терминальным.

    ⚠️ ПРЕЖНЯЯ ФОРМА ПРЕДСКАЗАЛА СВОЙ ОТКАЗ ДОСЛОВНО И НЕ УГАДАЛА ВИНОВНИКА.
    Она защищала дополнение терминальных словами «достаточно, чтобы платёжный
    провайдер завёл четвёртый статус». Четвёртый статус завели МЫ САМИ:
    `expired` — снятое по сроку давности намерение (D-01), оставленное вне
    терминальных намеренно, чтобы заплативший по старой ссылке получил свой
    месяц. Дополнение поглотило его молча, и благополучно снятая строка
    становилась постоянным денежным инцидентом и приходила под чипсом «В
    обработке», хотя та же таблица печатала её словом «просрочен».

    ⚠️ ЦЕНА ПОЛОЖИТЕЛЬНОЙ ФОРМЫ НАЗВАНА И ОПЛАЧЕНА. Незнакомый статус под
    правило не попал бы — но попасть ему неоткуда: словарь колонки
    `payments.status` ЗАКРЫТ и принадлежит нам, писатели статуса живут только в
    `app/services/payment_service.py`, и это УТВЕРЖДАЕТСЯ гейтом
    `tests/test_services/test_payment_status_vocabulary.py`, а не наблюдается.

    ⚠️ УСЛОВИЕ ОТДЕЛЕНО ОТ СВОЕЙ ВЫБОРКИ, ПОТОМУ ЧТО ЧИТАТЕЛЕЙ У НЕГО ДВА.
    Признак инцидента берёт три колонки залипших платежей, журнал подраздела
    «Платежи» — строки под чипсом «В обработке»; выборки у них разные, а правило
    одно. Скопированное во второе место, оно разошлось бы с первым молча, и
    залипший платёж пропал бы из журнала ровно тогда, когда за ним и приходят.
    """
    return Payment.status.in_(tuple(AWAITING_STATUSES))


def payment_stuck_before(now: datetime) -> datetime:
    """Момент, СТАРШЕ которого незакрытый платёж считается залипшим.

    ⚠️ ЕДИНСТВЕННОЕ ВЫРАЖЕНИЕ СРОКА ДАВНОСТИ НА ПРОЕКТ. Читателей у него два —
    выборка (`unclosed_payments_stmt`, которой он нужен, чтобы не читать
    таблицу целиком) и признак (`detect_payment_stuck`, которому он нужен,
    чтобы решить). Выписанный дважды, он разошёлся бы молча, и выборка
    отбрасывала бы строки, которые признак посчитал бы инцидентом: платёж
    исчезал бы из блока ровно тогда, когда за ним и приходят.
    """
    return normalize_utc(now) - timedelta(hours=PENDING_INTENT_TTL_HOURS)


def unclosed_payments_stmt(before: datetime, limit: int = INCIDENT_LIST_CAP + 1):
    """Три колонки ЗАЛИПШИХ незакрытых платежей — ограниченной выборкой.

    Условие незакрытости берётся у `unclosed_payment_clause`, а не выписывается
    здесь: см. его объяснение.

    ⚠️ ПОТОЛОК И СРОК СТОЯТ В ЗАПРОСЕ, А НЕ ТОЛЬКО В PYTHON (WR-07 ревизии фазы
    6). Прежняя редакция читала КАЖДЫЙ нетерминальный платёж за всю историю и
    отсеивала лишнее уже в памяти. Множество это РАСТЁТ МОНОТОННО — сам признак
    и существует потому, что отменённые у провайдера намерения не закрываются
    никогда, — и полное чтение приходилось на «Обзор», то есть на страницу,
    которую открывают в момент аварии. Фаза ограничивает КАЖДОЕ такое чтение
    (`WORKER_LIST_CAP`, `QUEUE_ROW_CAP`, `LOG_LINE_CAP`, `PAYMENT_LIST_CAP`,
    `USERS_PAGE_SIZE`); это было единственным исключением.

    ⚠️ ПОРЯДОК — ОТ СВЕЖИХ К СТАРЫМ, И ЭТО НЕ ВКУС. Блок сортирует инциденты по
    убыванию момента и оставляет первые `INCIDENT_LIST_CAP`; выборка, читающая
    самые СТАРЫЕ строки, отдала бы ровно те, которые блок отбросил бы последними.

    Строка сверх потолка читается НАМЕРЕННО (`+ 1`): она единственная улика
    того, что перечень усечён, и без неё «ровно двадцать» было бы неотличимо от
    «двадцать и есть все».
    """
    return (
        select(Payment.id, Payment.user_id, Payment.created_at)
        .where(unclosed_payment_clause(), Payment.created_at <= before)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .limit(limit)
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
) -> IncidentBoard:
    """Все пять признаков разом: четыре из базы, один — из поданной живости.

    ЧИСЛО ОБРАЩЕНИЙ К БАЗЕ НЕ ЗАВИСИТ ОТ ЧИСЛА НАЙДЕННЫХ ИНЦИДЕНТОВ. Блок живёт
    на «Обзоре», куда администратор заходит В МОМЕНТ АВАРИИ: запрос на строку
    умножился бы ровно тогда, когда база и так под нагрузкой. Обращений ПЯТЬ, и
    ни одно из них не стоит внутри цикла по строкам.

    ПОРЯДОК — ПО УБЫВАНИЮ ВРЕМЕНИ ПОСЛЕДНЕГО СЛЕДА: свежая авария важнее давней,
    и первая строка блока обязана отвечать на вопрос «что чинить первым».

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

    # (1) Отвалившиеся аккаунты — ОГРАНИЧЕННОЙ выборкой (WR-07). В массовой
    # аварии в этом состоянии оказываются ВСЕ аккаунты продукта, и чтение
    # приходится на страницу, которую в аварии и открывают. Порядок — от
    # свежих к старым по последней синхронизации: точный момент строки блок
    # берёт из последнего СЛЕДА отвала, а он живёт в другой таблице и в
    # выборку не заводится (это был бы запрос на строку — ровно то, что
    # `collect_incidents` запрещает себе явно). Приближение названо: в аварии,
    # где отвалилось больше двадцати аккаунтов, вопрос «какие именно двадцать»
    # смысла не имеет, а вопрос «прочитана ли таблица целиком на пути
    # отрисовки» — имеет.
    down_rows = (
        await session.execute(
            select(
                MessengerAccount.id,
                MessengerAccount.user_id,
                MessengerAccount.type,
                MessengerAccount.status,
                MessengerAccount.last_synced_at,
            )
            .where(MessengerAccount.status.in_(tuple(ACCOUNT_DOWN_STATUSES)))
            .order_by(
                MessengerAccount.last_synced_at.desc().nullslast(),
                MessengerAccount.id.desc(),
            )
            .limit(INCIDENT_LIST_CAP + 1)
        )
    ).all()
    sources_capped = len(down_rows) > INCIDENT_LIST_CAP
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

    # (4) Незакрытые платежи — ограниченной выборкой по тому же сроку давности,
    # который применяет сам признак (WR-07).
    payment_rows = (
        await session.execute(unclosed_payments_stmt(payment_stuck_before(moment)))
    ).all()
    sources_capped = sources_capped or len(payment_rows) > INCIDENT_LIST_CAP
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

    incidents.sort(key=lambda incident: incident.at, reverse=True)
    return IncidentBoard(
        incidents=tuple(incidents[:INCIDENT_LIST_CAP]),
        # ⚠️ ПОТОЛОК, СРАБОТАВШИЙ В ВЫБОРКЕ, — ТОТ ЖЕ СРАБОТАВШИЙ ПОТОЛОК.
        # Ограничив чтение, но не сказав об этом, блок сообщал бы «других
        # инцидентов нет» ровно там, где их не читали. Признак поэтому
        # объединяет две причины усечения: перечень длиннее потолка и источник,
        # отдавший строку сверх потолка.
        capped=len(incidents) > INCIDENT_LIST_CAP or sources_capped,
    )


def _parse_moment(value: datetime | None) -> datetime | None:
    """Момент из агрегата, приведённый к единой зоне.

    `max()` сохраняет тип колонки на обоих диалектах и отдаёт `datetime`
    (проверено прогоном на SQLite), но зону НЕ сохраняет: SQLite отдаёт момент
    naive, PostgreSQL — aware. Дальше он сравнивается и вычитается в Python,
    поэтому приведение обязательно (Pitfall 1).
    """
    return normalize_utc(value)
