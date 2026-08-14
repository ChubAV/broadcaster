"""Аналитика журнала отправок — один модуль на дашборд, историю и Фазу 6.

ПОЧЕМУ МОДУЛЬ ОДИН (D-35). Один и тот же вопрос — «сколько отправок и чем они
кончились» — задают четыре разных места: плитки дашборда, список истории,
счётчик истории и JSON-API. До этого модуля каждое отвечало на него своим
запросом, и ответы уже разошлись: дашборд считал отправки от UTC-полуночи, а
история — скользящим окном; «ошибками» дашборд считал только `fail`, оставляя
`account_disconnected` не посчитанным нигде. Расхождение такого рода не роняет
ни один тест и не даёт пятисотки — оно просто печатает пользователю два разных
числа на один вопрос. Поэтому определение живёт ЗДЕСЬ, а потребители его
ВЫЗЫВАЮТ; ни один из них не владеет собственной копией.

ЧЕГО МОДУЛЬ НЕ ДЕЛАЕТ:

- не читает `Request`, не знает про cookie и про то, кто вошёл: владелец
  приезжает обязательным именованным `user_id`, а ветки «по всем пользователям»
  здесь нет вовсе — её отсутствие и есть проверяемая форма T-04-01;
- ничего не пишет в БД и не коммитит: все функции только читают;
- не знает про Jinja, шаблоны и разметку: наружу выходят числа и запросы, а не
  строки для показа;
- не вызывает Docker SDK и вообще ничего синхронно-блокирующего — он живёт на
  пути рендера страницы;
- НЕ КЭШИРУЕТ (D-37). Агрегаты считаются на каждый рендер. Образец Redis-кэша
  в проекте есть (`app/services/billing_cache.py`) и здесь сознательно не
  применён: любая отправка любого воркера меняет ответ, поэтому кэш потребовал
  бы инвалидации из воркера на каждую запись журнала — то есть нового канала
  связи воркера с web-слоем ради экономии одного индексированного запроса.
  Слоя инвалидации фаза не заводит.

ПЕРЕНОСИМОСТЬ АГРЕГАЦИИ. Тесты проекта идут на SQLite, бой работает на
PostgreSQL. Календарная группировка средствами БД пишется на этих диалектах
по-разному, и ветка, написанная под боевой диалект, не исполнилась бы тестами
НИ РАЗУ — то есть проверялась бы только в проде. Поэтому окна режутся
сравнением `sent_at` с посчитанными в Python границами, а любое бакетирование
по календарным единицам (Фаза 4, планы heatmap и ленты) делается в Python над
проекцией значений.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group
from app.models.send_log import SendLog
from app.models.user import User

# --- Статусы журнала ----------------------------------------------------------
#
# Единственный на проект источник значений `send_logs.status`. Статусов ТРИ, а
# не два: `account_disconnected` пишет диспетчер отправки, когда сессия
# мессенджера отвалилась, и для пользователя это ровно такая же несостоявшаяся
# отправка, как `fail`. Плитка «Ошибок», считавшая только `fail`, показывала
# ноль ошибок при отвалившемся аккаунте — то есть врала ровно в тот момент,
# ради которого её и смотрят (RESEARCH §Pitfall 3).
STATUS_OK = "ok"
STATUS_FAIL = "fail"
STATUS_ACCOUNT_DISCONNECTED = "account_disconnected"

FAILED_STATUSES = (STATUS_FAIL, STATUS_ACCOUNT_DISCONNECTED)

# Допустимые значения фильтра периода. Читают и фильтр ниже, и разметка чипсов
# (план 04-06) — выписанный в шаблоне литерал разъехался бы с фильтром молча.
HISTORY_PERIODS = ("today", "7d", "30d")

# Ширина окна плиток по умолчанию: скользящие сутки от момента запроса (D-02).
# НЕ полночь: пользователь смотрит дашборд, чтобы понять, что происходит
# СЕЙЧАС, а счётчик от полуночи в 00:10 показывает почти ноль независимо от
# того, работала система ночью или стояла.
DEFAULT_WINDOW = timedelta(hours=24)


def normalize_utc(value: datetime | None) -> datetime | None:
    """Доводит значение `sent_at` до aware-UTC.

    Колонка объявлена `DateTime(timezone=True)`, но SQLite отдаёт её NAIVE, а
    PostgreSQL — aware. Сравнение naive и aware в Python поднимает TypeError,
    поэтому код, читающий `sent_at`, обязан пройти через этот хелпер — иначе
    дефект существует только на одном из двух диалектов и ловится не тестами, а
    пользователем. Приём копируется из `app/pages/common.py:161-162`: значение
    без таймзоны считается временем UTC, потому что и приложение, и
    `server_default` пишут туда UTC.

    Значение с таймзоной возвращается КАК ЕСТЬ, а не переводится в UTC: перевод
    сменил бы календарный день у aware-значения из другой зоны, а вызывающий
    ждёт тот же момент времени, а не другую его запись.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@dataclass(slots=True)
class SendMetrics:
    """Восемь чисел плиток: четыре за текущее окно и четыре за предыдущее.

    Дельты — вычисляемые свойства, а не поля: хранить разность рядом с
    слагаемыми значит завести второй источник одного и того же числа.
    """

    total: int = 0
    ok: int = 0
    failed: int = 0
    groups: int = 0
    total_prev: int = 0
    ok_prev: int = 0
    failed_prev: int = 0
    groups_prev: int = 0

    @property
    def total_delta(self) -> int:
        return self.total - self.total_prev

    @property
    def ok_delta(self) -> int:
        return self.ok - self.ok_prev

    @property
    def failed_delta(self) -> int:
        return self.failed - self.failed_prev

    @property
    def groups_delta(self) -> int:
        return self.groups - self.groups_prev


async def send_metrics(
    session: AsyncSession,
    *,
    user_id: int,
    now: datetime | None = None,
    window: timedelta = DEFAULT_WINDOW,
) -> SendMetrics:
    """Считает восемь чисел плиток ОДНИМ round-trip (D-38).

    Окно берётся шириной `window * 2` и режется условными агрегатами на
    текущее и предыдущее — два отдельных запроса дали бы вдвое больше обращений
    к самой растущей таблице системы ради одной строки результата (T-04-03).

    Граница текущего окна ВКЛЮЧАЮЩАЯ: запись ровно в `now - window`
    принадлежит текущим суткам. Иначе момент границы не принадлежал бы ни
    одному из двух окон, и сумма плиток за двое суток была бы на одну запись
    меньше правды.

    ЧТО СЧИТАЕТСЯ ОШИБКОЙ. `failed` — это «не `ok`», а не «входит в
    `FAILED_STATUSES`». Разница видна только на статусе, которого модуль не
    знает: при проверке членства такая запись не попала бы ни в «Успешно», ни в
    «Ошибки», и сумма двух плиток молча разошлась бы с плиткой «Отправок за
    сутки» — то есть неклассифицируемая запись исчезла бы из счёта ради ровных
    чисел (прохибиция P-04-01). Сторона отказа выбрана несимметрично по образцу
    `effective_ad_status`: назвать несостоявшуюся отправку успешной хуже, чем
    наоборот. `FAILED_STATUSES` остаётся именем ДВУХ известных неуспешных
    значений — его читают фильтры и разметка.

    `groups` считает различные `group_id`. Запись с пустым `group_id`
    (отправка, чья группа уже удалена) в счёт групп не идёт, но из `total` НЕ
    выпадает: она всё равно отправка.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    current_start = now - window
    previous_start = now - window * 2

    in_current = SendLog.sent_at >= current_start
    in_previous = SendLog.sent_at < current_start

    is_ok = SendLog.status == STATUS_OK
    is_failed = SendLog.status != STATUS_OK

    row = (
        await session.execute(
            select(
                func.sum(case((in_current, 1), else_=0)).label("total"),
                func.sum(case((in_current & is_ok, 1), else_=0)).label("ok"),
                func.sum(case((in_current & is_failed, 1), else_=0)).label("failed"),
                # COUNT(DISTINCT CASE WHEN ... THEN group_id END): ветка без
                # `else_` даёт NULL, а NULL в счёт различных значений не идёт —
                # тем же выражением отсекаются и чужое окно, и пустая группа.
                func.count(func.distinct(case((in_current, SendLog.group_id)))).label(
                    "groups"
                ),
                func.sum(case((in_previous, 1), else_=0)).label("total_prev"),
                func.sum(case((in_previous & is_ok, 1), else_=0)).label("ok_prev"),
                func.sum(case((in_previous & is_failed, 1), else_=0)).label(
                    "failed_prev"
                ),
                func.count(func.distinct(case((in_previous, SendLog.group_id)))).label(
                    "groups_prev"
                ),
            ).where(
                SendLog.user_id == user_id,
                SendLog.sent_at >= previous_start,
            )
        )
    ).one()

    # `func.sum` над пустым набором отдаёт NULL, а плитка обязана показать ноль,
    # а не пустоту — приём `int(... or 0)` тот же, что в get_shell_context.
    return SendMetrics(
        total=int(row.total or 0),
        ok=int(row.ok or 0),
        failed=int(row.failed or 0),
        groups=int(row.groups or 0),
        total_prev=int(row.total_prev or 0),
        ok_prev=int(row.ok_prev or 0),
        failed_prev=int(row.failed_prev or 0),
        groups_prev=int(row.groups_prev or 0),
    )


# --- Фильтры истории ----------------------------------------------------------


def history_filter_params(
    status: str | None,
    messenger_type: str | None,
    account_id: int | None,
    period: str | None,
) -> dict:
    """Набор действующих фильтров для проброса в URL порций прокрутки.

    Ключи (`status`, `messenger`, `account_id`, `period`) — контракт разметки:
    их читает сентинел бесконечной прокрутки, и переименование одного из них
    теряет фильтр на второй странице выдачи, не роняя ни одного запроса.

    Позиционная сигнатура сохранена от приватного предшественника дословно:
    перенос обязан быть поведенчески нулевым.
    """
    p = {}
    if status:
        p["status"] = status
    if messenger_type:
        p["messenger"] = messenger_type
    if account_id is not None:
        p["account_id"] = account_id
    if period:
        p["period"] = period
    return p


def _period_cutoff(period: str | None, user: User | None) -> datetime | None:
    """Нижняя граница периода в UTC либо None, если отсечки нет.

    Неизвестное значение периода отсечки НЕ применяет и исключения НЕ
    поднимает: значение приходит из query-строки, то есть от кого угодно, и
    подобранный вручную мусор обязан давать «фильтр не применён», а не
    пятисотку (V5 из RESEARCH §Security Domain).
    """
    if period == "today":
        # ЛОКАЛЬНАЯ полночь пользователя, переведённая в UTC (D-30). Отсечка от
        # UTC-полуночи для пользователя в UTC+3 начинает «сегодня» в три часа
        # ночи по его часам: утренние отправки в списке за сегодня отсутствуют,
        # а вчерашние вечерние — присутствуют. Это ровно тот дефект, который
        # D-02 чинит на плитках дашборда.
        #
        # Импорт отложен в тело функции НАМЕРЕННО. `app/pages/__init__.py`
        # собирает роутеры разделов, поэтому импорт `app.pages.common` на
        # верхнем уровне этого модуля замыкает цикл: pages → dashboard →
        # send_analytics → pages. Цикл рвётся только отложенным импортом или
        # копией хелпера таймзоны — копия завела бы второй источник одного
        # правила.
        from app.pages.common import _get_timezone_for_user

        tz = _get_timezone_for_user(user)
        local_midnight = datetime.now(tz).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return local_midnight.astimezone(timezone.utc)
    if period == "7d":
        return datetime.now(timezone.utc) - timedelta(days=7)
    if period == "30d":
        return datetime.now(timezone.utc) - timedelta(days=30)
    return None


def apply_history_filters(
    query,
    *,
    status: str | None = None,
    messenger_type: str | None = None,
    account_id: int | None = None,
    period: str | None = None,
    user: User | None = None,
):
    """Навешивает условия фильтрации истории на готовый запрос.

    Запрос ОБЯЗАН уже нести `outerjoin(Group, SendLog.group_id == Group.id)`:
    условие по аккаунту строится по `Group.account_id`, и без соединения оно не
    построится вовсе. Соединение остаётся у вызывающего, потому что страницы
    выбирают `SendLog, Group` парой и им нужна сама строка группы, а счётчику
    ниже — только соединение.

    `user` нужен ТОЛЬКО периоду `today` и по умолчанию отсутствует: остальные
    периоды от таймзоны не зависят, и требовать пользователя ради них значило
    бы протаскивать его через вызовы, которым он не нужен.
    """
    if status:
        query = query.where(SendLog.status == status)
    if messenger_type:
        query = query.where(SendLog.messenger_type == messenger_type)
    if account_id is not None:
        query = query.where(Group.account_id == account_id)
    cutoff = _period_cutoff(period, user)
    if cutoff is not None:
        query = query.where(SendLog.sent_at >= cutoff)
    return query


async def history_count(
    session: AsyncSession,
    *,
    user_id: int,
    status: str | None = None,
    messenger_type: str | None = None,
    account_id: int | None = None,
    period: str | None = None,
    user: User | None = None,
) -> int:
    """Число записей истории под тем же набором фильтров, что и список (D-31).

    Счётчик и список обязаны отвечать на один вопрос одним числом, поэтому
    условия навешивает ТА ЖЕ функция, а не переписанный рядом набор `where`.

    `outerjoin(Group)` стоит здесь БЕЗУСЛОВНО, даже когда фильтр по аккаунту не
    задан. Соединение внутри `if` выглядело бы экономнее, но условие по
    `Group.account_id` тогда не с чем было бы связать, и фильтр развалился бы
    молча — счётчик отдавал бы полное число при отфильтрованном списке.
    Внешнее соединение записей не теряет: отправка без группы остаётся в счёте.
    """
    query = (
        select(func.count())
        .select_from(SendLog)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user_id)
    )
    query = apply_history_filters(
        query,
        status=status,
        messenger_type=messenger_type,
        account_id=account_id,
        period=period,
        user=user,
    )
    return int(await session.scalar(query) or 0)
