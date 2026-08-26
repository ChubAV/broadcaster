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

- не читает `Request`, не знает про cookie и про то, кто вошёл: ОБЛАСТЬ СЧЁТА
  приезжает обязательным именованным `user_id`, и опустить его нельзя ни у
  одной функции модуля. У `send_metrics` область расширена до двух значений
  (владелец либо весь сервис, D-39); у остальных функций ветки «по всем
  пользователям» нет вовсе. Проверяемая форма T-04-01 — именно
  ОБЯЗАТЕЛЬНОСТЬ параметра: умолчание сделало бы общесистемную выдачу
  достижимой по забывчивости, а не по решению;
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

import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.scheduling.use_cases import effective_ad_status
from app.constants import AD_STATUS_DRAFT
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
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
    user_id: int | None,
    now: datetime | None = None,
    window: timedelta = DEFAULT_WINDOW,
) -> SendMetrics:
    """Считает восемь чисел плиток ОДНИМ round-trip (D-38).

    ОБЛАСТЬ СЧЁТА — ПАРАМЕТР, А НЕ ВТОРАЯ ФУНКЦИЯ (D-39). `user_id` называет
    владельца сводки; `None` означает «по всему сервису» и читается админским
    «Обзором». Отдельная функция общесистемного счёта рядом продублировала бы
    восемь условных агрегатов, оба окна одним обращением и защиту от пустых
    значений — и первая же правка формулы разошлась бы между двумя копиями
    молча, то есть администратор и пользователь увидели бы РАЗНЫЕ числа об
    одном и том же периоде.

    ⚠️ ПАРАМЕТР ОСТАЁТСЯ ОБЯЗАТЕЛЬНЫМ, И УМОЛЧАНИЯ У НЕГО НЕТ (T-04-01).
    Расширение области — не повод сделать общесистемную выдачу достижимой по
    забывчивости: с `user_id: int | None = None` вызов, у которого владельца
    просто забыли передать, вернул бы пользователю чужие числа и отдал бы их
    на его собственный дашборд. Молчаливая ветка «все пользователи» и явная —
    это разные вещи, и разделяет их ровно отсутствие умолчания. Закреплено
    `test_the_owner_of_a_summary_cannot_be_omitted_by_accident`.

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

    # ОТБОР ПО ВЛАДЕЛЬЦУ — ЭТО УСЛОВИЕ, КОТОРОЕ ЛИБО ЕСТЬ, ЛИБО ЕГО НЕТ, и
    # ветвление стоит ЗДЕСЬ, при сборке условий, а не внутри восьми агрегатов.
    # Иначе общесистемный случай получил бы собственную копию формулы окон и
    # разошёлся бы с пользовательской при первой же правке.
    scope: tuple = () if user_id is None else (SendLog.user_id == user_id,)

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
                *scope,
                SendLog.sent_at >= previous_start,
                # ОКНО ОГРАНИЧЕНО И СВЕРХУ. Без верхней границы запись с
                # `sent_at` в БУДУЩЕМ — расхождение часов воркера и базы либо
                # явный `now` от вызывающего — попадала бы в ТЕКУЩЕЕ окно и
                # завышала бы плитку «за сутки» отправкой, которой ещё не было.
                # Граница включающая, как и нижняя: момент `now` принадлежит
                # текущему окну.
                SendLog.sent_at <= now,
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


async def last_send_at(
    session: AsyncSession, *, messenger_type: str
) -> datetime | None:
    """Момент последней зафиксированной отправки по каналу — по всему сервису.

    ⚠️ ФУНКЦИЯ ЖИВЁТ ЗДЕСЬ, А НЕ В МОДУЛЕ ПОДРАЗДЕЛА, ПОТОМУ ЧТО ЭТО АГРЕГАТ НАД
    ЖУРНАЛОМ ОТПРАВОК. Правило Фазы 4 (D-35) не про счётчики, а про источник:
    все агрегаты журнала объявлены В ОДНОМ модуле, и исключение «ну этот же не
    счётчик» открыло бы ровно ту дверь, ради закрытия которой модуль и заведён.

    ⚠️ ВЛАДЕЛЬЦА У ВЕЛИЧИНЫ НЕТ, И ЭТО НЕ ОСЛАБЛЕНИЕ T-04-01. Функция отвечает
    на операционный вопрос о СЕРВИСЕ — «уходит ли работа по этому каналу», — и
    возвращает ОДИН момент, а не чьи-либо записи: чужих данных через неё выйти
    не может. Читает её подраздел «Очередь» и плитка «Обзора», обе за правами
    администратора.

    Возвращает `None`, когда по каналу не зафиксировано ни одной отправки:
    отсчитывать тогда не от чего, и подменять это нулём значило бы сообщить
    «только что», когда верный ответ — «никогда».
    """
    return (
        await session.execute(
            select(func.max(SendLog.sent_at)).where(
                SendLog.messenger_type == messenger_type
            )
        )
    ).scalar()


# СЕКЦИЙ «HEATMAP АКТИВНОСТИ» И «СТОЛБЦЫ АКТИВНОСТИ ЗА НЕДЕЛЮ» ЗДЕСЬ БОЛЬШЕ НЕТ
# (задача 260826-9vv). Обе существовали ради одного экрана — карточки недельной
# активности дашборда, — и снятие карточки не оставило им ни одного потребителя.
# Часовая раскладка стримила недельное окно журнала отправок батчами на КАЖДОЙ
# загрузке дашборда и росла вместе с журналом пользователя: это было самое
# дорогое чтение экрана, и вместе с блоком ушло оно.
#
# Комментарий маршрута обещал, что раскладка «остаётся доступной Фазе 6». Фаза 6
# закрыта и заархивирована вместе с вехой v2.0, админка читает из этого модуля
# ЧЕТЫРЕ ДРУГИЕ функции, и обещание истекло невыполненным: держать ради него
# код, до которого нет ни одного пути, значит держать мусор с объяснением.
#
# Возврат имён запрещает `test_the_module_no_longer_carries_the_weekly_activity_surface`.
# Всё, что ниже, — живое: ближайшие отправки, лента, фильтры истории и ось
# календарного месяца читают история, админка и биллинг.


# --- Ближайшие отправки -------------------------------------------------------

# Пометки причин несрабатывания (D-15). Строки живут ЗДЕСЬ по той же причине,
# что и подписи рядов heatmap: это НАЗВАНИЯ трёх состояний, а не форматирование
# данных пользователя, и второй их источник в шаблоне разъехался бы с первым
# молча. Формулировки совпадают с бейджем карточки раздела расписаний
# (`schedules/includes/schedule_row.html`) ДОСЛОВНО: один и тот же факт обязан
# называться на двух экранах одними словами.
REASON_AD_DRAFT = "Объявление в черновике"
REASON_ACCOUNT_OFF = "Аккаунт отключён"
REASON_GROUPS_OFF = "Все группы выключены"

# Сколько строк показывает блок «Ближайшие отправки» по умолчанию (D-14).
UPCOMING_LIMIT = 8


@dataclass(slots=True)
class UpcomingSend:
    """Строка блока «Ближайшие отправки» ЦЕЛИКОМ.

    Все поля — простые значения, а не сущности ORM. Отдать наружу `Schedule`
    значило бы позвать шаблон на `schedule.ad`, а эта связь объявлена
    `lazy="raise"`: обращение к ней из Jinja поднимает исключение уже на
    рендере, то есть пятисотку на дашборде.
    """

    schedule_id: int
    ad_id: int
    ad_title: str
    next_run_at: datetime
    group_count: int
    messenger_type: str | None
    reason: str = ""


async def upcoming_sends(
    session: AsyncSession,
    *,
    user_id: int,
    now: datetime | None = None,
    limit: int = UPCOMING_LIMIT,
) -> list[UpcomingSend]:
    """Ближайшие запланированные отправки владельца с пометками причин (D-15).

    ВЛАДЕНИЕ ИДЁТ ЧЕРЕЗ ОБЪЯВЛЕНИЕ. Колонки `user_id` у расписания НЕТ
    (`app/models/schedule.py`), поэтому границу владельца держит
    `Ad.user_id == user_id` — так же, как во всех запросах
    `app/pages/schedules.py` и в счётчиках шелла (T-04-13).

    ОБЪЯВЛЕНИЕ И АККАУНТ ПРИЕЗЖАЮТ ЗАПРОСОМ. `Schedule.ad` и `Schedule.account`
    объявлены `lazy="raise"`, и обращение к ним как к атрибутам поднимает
    исключение — на боевом стеке это пятисотка на самом дашборде, а не тихая
    деградация блока. Поэтому сущности выбираются явным `select(...)` с `join`
    по объявлению.

    `outerjoin` ДЛЯ АККАУНТА ОБЯЗАТЕЛЕН. `Schedule.account_id` nullable с
    `ondelete="SET NULL"`: при удалении messenger-аккаунта расписание
    сохраняется и отвязывается (issue #35). Внутренний join потерял бы ровно те
    строки, ради которых D-15 и написан, — пользователь не увидел бы, что его
    рассылка больше никуда не уйдёт.

    ⚠️ ВТОРОЙ ЗАПРОС НА БЛОК — НАЗВАННОЕ ОТСТУПЛЕНИЕ ОТ D-38. Третья причина
    («все группы выключены») требует флагов групп, а состав групп расписания
    хранится JSON-списком (`Schedule.group_ids`), и join по его элементам не
    строится ни в SQLite, ни в PostgreSQL — то же ограничение уже разобрано в
    подборе расписаний к отправке (`collect_due_schedules`). Без флагов блок
    показывал бы отправку, которой не будет. Отступление ОГРАНИЧЕНО: флаги
    берутся ОДНИМ запросом по объединению идентификаторов не более чем `limit`
    строк. Обращение к БД внутри цикла запрещено — оно превратило бы
    отступление в дефект N+1 (T-04-19), закреплено тестом
    test_upcoming_sends_takes_two_queries_regardless_of_group_count.

    `now` НИЧЕГО НЕ ФИЛЬТРУЕТ и принят для единообразия сигнатур модуля.
    Ограничения по времени вперёд у блока нет по D-14, а отсечка назад
    (`next_run_at >= now`) спрятала бы просроченные расписания — то есть ровно
    те, о которых пользователю важнее всего узнать, и при остановленном воркере
    опустошила бы блок целиком, хотя активные расписания у пользователя есть.

    `group_count` — размер СОСТАВА расписания, а не число включённых групп: это
    то же число, что видит пользователь в редакторе, и расхождение двух экранов
    по одному вопросу — ровно та болезнь, которую лечит D-35. О том, что
    отправка не уйдёт, сообщает пометка причины, а не подменённое число.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    rows = (
        await session.execute(
            select(Schedule, Ad, MessengerAccount)
            .join(Ad, Schedule.ad_id == Ad.id)
            .outerjoin(MessengerAccount, Schedule.account_id == MessengerAccount.id)
            .where(
                Ad.user_id == user_id,
                Schedule.is_active.is_(True),
                Schedule.next_run_at.isnot(None),
            )
            .order_by(Schedule.next_run_at.asc())
            .limit(limit)
        )
    ).all()

    if not rows:
        return []

    # Объединение составов ВСЕХ показываемых строк — один запрос на блок.
    group_ids = {
        group_id
        for schedule, _ad, _account in rows
        for group_id in (schedule.group_ids or [])
    }
    group_active: dict[int, bool] = {}
    if group_ids:
        group_active = {
            group_id: bool(is_active)
            for group_id, is_active in (
                await session.execute(
                    # ПРЕДИКАТ ВЛАДЕНИЯ ЗДЕСЬ, А НЕ «ГДЕ-ТО РАНЬШЕ».
                    # `Schedule.group_ids` — JSON-список без внешнего ключа и
                    # без ограничения принадлежности, то есть корректность
                    # запроса без этого условия держалась бы на том, что
                    # редактор расписаний проверил владение в ДРУГОМ модуле, и
                    # на том, что идентификаторы не переиспользуются. Второе
                    # верно на PostgreSQL и НЕВЕРНО на SQLite, где INTEGER
                    # PRIMARY KEY без AUTOINCREMENT выдаёт max(rowid)+1 и
                    # переиспользует номер удалённой строки, — то есть именно
                    # тестовая среда способна нарушить инвариант, который
                    # тестом не поймать. Условие стоит ровно ничего.
                    select(Group.id, Group.is_active).where(
                        Group.id.in_(group_ids), Group.user_id == user_id
                    )
                )
            ).all()
        }

    items: list[UpcomingSend] = []
    for schedule, ad, account in rows:
        composition = list(schedule.group_ids or [])
        # Отсутствующий в выборке идентификатор — удалённая группа: получить
        # рассылку она не может, поэтому её флаг считается выключенным.
        # Пустой состав тоже даёт «все группы выключены»: расписание без групп
        # не отправит ничего, и назвать это отдельным словом значило бы
        # заводить четвёртую причину сверх трёх, названных D-15.
        any_group_on = any(
            group_active.get(group_id, False) for group_id in composition
        )

        # Приоритет причин — порядок этих ветвей. Совпасть могут все три сразу,
        # и показывать три бейджа в строке шириной в одну строку некуда.
        if effective_ad_status(ad) == AD_STATUS_DRAFT:
            reason = REASON_AD_DRAFT
        # Статус аккаунта сравнивается с ЛИТЕРАЛОМ "active" — так же, как в
        # `collect_due_schedules` и в счётчиках шелла. Своей константы под это
        # значение в проекте нет, и заводить её ЗДЕСЬ значило бы получить второй
        # источник одного значения, не сняв ни одного из существующих литералов.
        elif account is None or account.status != "active":
            reason = REASON_ACCOUNT_OFF
        elif not any_group_on:
            reason = REASON_GROUPS_OFF
        else:
            reason = ""

        items.append(
            UpcomingSend(
                schedule_id=schedule.id,
                ad_id=ad.id,
                ad_title=ad.title,
                next_run_at=schedule.next_run_at,
                group_count=len(composition),
                messenger_type=account.type if account else None,
                reason=reason,
            )
        )
    return items


# --- Живая лента --------------------------------------------------------------


@dataclass(slots=True)
class FeedRow:
    """Строка живой ленты дашборда ЦЕЛИКОМ (DASH-03).

    Простые значения, а не сущность ORM: маршрут ленты дёргается автоматически
    каждые несколько секунд на каждой открытой вкладке, и создавать на каждый
    тик восемь объектов ORM с их identity map незачем — шаблону нужны шесть
    значений, и ровно они здесь и лежат.
    """

    id: int
    ad_title: str | None
    group_name: str | None
    status: str
    messenger_type: str | None
    sent_at: datetime | None


async def recent_feed(
    session: AsyncSession, *, user_id: int, limit: int = 8
) -> list[FeedRow]:
    """Последние отправки владельца, самая свежая первой (DASH-03).

    ИСТОЧНИК ЛЕНТЫ — ТОЛЬКО ЖУРНАЛ ОТПРАВОК (D-05). «Живой» её делает частота
    обновления, а не разнообразие событий: синхронизации групп, переподключения
    воркера и активации расписания в базе не записываются вовсе, и подмешать их
    сюда нечем. Завести таблицу событий — работа отдельной фазы; выдумать их из
    косвенных признаков (например, из времени последней синхронизации аккаунта)
    значило бы печатать пользователю правдоподобную ложь о том, когда что
    случилось.

    ВЫБИРАЮТСЯ КОЛОНКИ, А НЕ СУЩНОСТЬ. Все шесть значений строки — снимки,
    лежащие в самой записи журнала: заголовок объявления и имя группы пишутся в
    `send_logs` в момент отправки. Именно снимок, а не живое имя группы,
    показывает и запись истории (`history/includes/history_card.html`), поэтому
    второго ответа на один вопрос здесь не заводится.

    ⚠️ СОЕДИНЕНИЯ С `groups` ЗДЕСЬ НЕТ, хотя блок последних отправок, который
    лента заменила, его нёс. Тому блоку строка группы была нужна ради внешнего
    идентификатора и аккаунта; ленте не нужна ни одна колонка `Group`, и
    соединение осталось бы платой без покупки — на маршруте, который вызывается
    каждые `FEED_POLL_SECONDS` на каждой открытой вкладке (T-04-18).

    Порядок — по `sent_at` ПО УБЫВАНИЮ: он же задаёт смысл блока. Запрос идёт по
    индексу времени отправки и берёт не больше `limit` строк.
    """
    rows = (
        await session.execute(
            select(
                SendLog.id,
                SendLog.ad_title,
                SendLog.group_name,
                SendLog.status,
                SendLog.messenger_type,
                SendLog.sent_at,
            )
            .where(SendLog.user_id == user_id)
            .order_by(SendLog.sent_at.desc())
            .limit(limit)
        )
    ).all()

    return [
        FeedRow(
            id=row.id,
            ad_title=row.ad_title,
            group_name=row.group_name,
            status=row.status,
            messenger_type=row.messenger_type,
            sent_at=row.sent_at,
        )
        for row in rows
    ]


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


# --- Календарный месяц: ось тарифа --------------------------------------------
#
# Ось «Отправок в месяц» экрана тарифов (D-10) — это вопрос к журналу отправок,
# а журналом владеет ЭТОТ модуль (D-35). Готового календарного окна в нём не
# было: плитки считают скользящие сутки, а фильтр истории умеет только
# `today` / `7d` / `30d`. Поэтому окно живёт здесь, рядом с остальными
# запросами к `send_logs`, а не в модуле осей тарифа.


def current_month_bounds_utc(
    user: User | None, now: datetime | None = None
) -> tuple[datetime, datetime]:
    """Полуинтервал `[начало, конец)` текущего календарного месяца ЧИТАТЕЛЯ в UTC.

    ОКНО — КАЛЕНДАРНЫЙ МЕСЯЦ В ЗОНЕ ПОЛЬЗОВАТЕЛЯ (D-11). Отправка 1-го числа в
    00:30 по Москве принадлежит НОВОМУ месяцу, хотя по UTC это ещё 31-е число
    предыдущего. Окно от UTC-полуночи первого числа для пользователя в UTC+3
    три часа подряд считало бы новые отправки в счёт прошлого месяца — то есть
    ровно в те часы, когда квота «уже обнулилась» по его календарю. Приём тот
    же, что у отсечки периода `today` (D-30): граница считается в зоне читателя
    и переводится в UTC.

    ВЕРХНЯЯ ГРАНИЦА — НАЧАЛО СЛЕДУЮЩЕГО МЕСЯЦА, а не «последняя секунда
    текущего», и условие запроса к ней СТРОГОЕ. Включающая граница «23:59:59»
    потеряла бы отправки внутри последней секунды месяца, а на PostgreSQL, где
    время хранится с микросекундами, — ещё и весь микросекундный хвост.

    ДЛИНА МЕСЯЦА — `calendar.monthrange`, а не `replace(month=month + 1)`.
    Наивный сдвиг падает в декабре («month must be in 1..12»), и падал бы у
    пользователя, а не в суите. Сложение с `timedelta` идёт по СТЕННЫМ часам
    зоны, поэтому переход на летнее время не сдвигает границу месяца на час.
    """
    # Импорт отложен в тело функции НАМЕРЕННО. `app/pages/__init__.py` собирает
    # роутеры разделов, поэтому импорт `app.pages.common` на верхнем уровне
    # этого модуля замыкает цикл: pages → dashboard → send_analytics → pages.
    # Цикл рвётся только отложенным импортом или копией хелпера таймзоны —
    # копия завела бы второй источник одного правила.
    from app.pages.common import _get_timezone_for_user

    tz = _get_timezone_for_user(user)
    if now is None:
        now = datetime.now(timezone.utc)
    # normalize_utc обязателен: `now` приезжает и из теста, и из `datetime.now`,
    # и naive-значение уронило бы `astimezone` не там, где это видно.
    local_now = normalize_utc(now).astimezone(tz)

    start_local = local_now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    days_in_month = calendar.monthrange(start_local.year, start_local.month)[1]
    end_local = start_local + timedelta(days=days_in_month)

    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def sends_in_current_month_query(
    user: User | None, *, user_id: int, now: datetime | None = None
) -> Select:
    """Счётный ЗАПРОС отправок владельца за календарный месяц — без исполнения.

    Запрос отдаётся отдельно от исполнения, чтобы у оси тарифа было ОДНО
    определение предиката при ДВУХ способах чтения: экран тарифов вкладывает
    его скалярным подзапросом в общий запрос осей и платит один round-trip, а
    любой одиночный вызывающий берёт `sends_in_current_month` ниже. Второй
    запрос, написанный на месте вызова, был бы вторым источником одного числа —
    ровно та болезнь, которую лечит D-35.

    ФИЛЬТРА ПО СТАТУСУ ЗДЕСЬ НЕТ НАМЕРЕННО (D-25). Квоту месяца расходует ЛЮБАЯ
    попытка отправки, а не только доставленная: неуспешная отправка уже заняла
    слот воркера и ушла в мессенджер. «Квота тратится только на доставленное» —
    отдельное продуктовое обещание со своей семантикой возвратов и ретраев, и
    ввести его внутри витрины значило бы завести второй ответ на вопрос
    «сколько я потратил». Это не забытый фильтр: не добавлять.

    КАЛЕНДАРНОЙ ГРУППИРОВКИ СРЕДСТВАМИ ДИАЛЕКТА ЗДЕСЬ НЕТ и быть не должно —
    границы посчитаны в Python, а в базу уезжает обычное сравнение по
    составному индексу `(user_id, sent_at)` ревизии 0016.
    """
    start, end = current_month_bounds_utc(user, now=now)
    return (
        select(func.count())
        .select_from(SendLog)
        .where(
            SendLog.user_id == user_id,
            SendLog.sent_at >= start,
            # Строго меньше верхней границы: момент 00:00 первого числа
            # принадлежит уже следующему месяцу.
            SendLog.sent_at < end,
        )
    )


async def sends_in_current_month(
    session: AsyncSession,
    *,
    user_id: int,
    user: User | None,
    now: datetime | None = None,
) -> int:
    """Сколько отправок владелец сделал за свой текущий календарный месяц.

    `user` нужен ТОЛЬКО ради таймзоны окна, а владение держит отдельный
    `user_id`-предикат запроса: числу владельца нельзя зависеть от того, какой
    объект пользователя случайно оказался у вызывающего под рукой.
    """
    return int(
        await session.scalar(
            sends_in_current_month_query(user, user_id=user_id, now=now)
        )
        or 0
    )
