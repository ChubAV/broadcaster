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
from datetime import datetime, timedelta, timezone, tzinfo

from sqlalchemy import case, func, select
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


# --- Heatmap активности -------------------------------------------------------

# Короткие имена дней в порядке `datetime.weekday()` (0 — понедельник).
# Выписаны ЯВНО, а не получены через `strftime('%a')`: результат strftime
# зависит от локали ПРОЦЕССА, и на машине без установленной русской локали
# подпись ряда молча отрисовалась бы английским сокращением. Это единственная
# строка, которую модуль формирует сам, и она допустима: это подпись РЯДА
# сетки, а не форматирование данных пользователя.
SHORT_WEEKDAYS = ("ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС")

# Размер батча потокового чтения окна heatmap. На asyncpg `yield_per` включает
# настоящий серверный курсор, на aiosqlite — буферизацию батчами; API `stream`
# одинаков на обоих.
HEATMAP_YIELD_PER = 1000


@dataclass(slots=True)
class HeatmapView:
    """Сетка активности: `days` рядов по 24 часа, подписи рядов и пик.

    `peak` отдаётся ВЫЗЫВАЮЩЕМУ, а не превращается в ступени насыщенности
    здесь: шкала — вопрос отображения, и её место в макросе разметки. Но
    считать максимум заново в шаблоне значило бы обходить всю сетку второй раз
    средствами Jinja, поэтому число, уже известное после раскладки, уезжает
    полем.
    """

    grid: list[list[int]]
    day_labels: list[str]
    peak: int


async def activity_heatmap(
    session: AsyncSession,
    *,
    user_id: int,
    now: datetime | None = None,
    tz: tzinfo | None = None,
    days: int = 7,
) -> HeatmapView:
    """Раскладывает отправки окна по (сутки, локальный час) — сетка `days`×24.

    ОКНО СКОЛЬЗЯЩЕЕ (D-12). Ряд `i` — сутки, начинающиеся в `local_origin + i
    дней`, где `local_origin` есть `now - days` суток. Календарной недели
    ПН-ВС макета здесь нет: она показывала бы в понедельник утром одну колонку
    данных и шесть пустых. Подписи рядов поэтому следуют ОКНУ — `day_labels[i]`
    есть день недели даты `local_origin + i дней`, а не фиксированный
    понедельник.

    РАСКЛАДКА ИДЁТ В PYTHON, А НЕ В БАЗЕ. Группировка по календарным единицам
    средствами диалекта в этом модуле запрещена: тесты идут на SQLite, бой — на
    PostgreSQL, и ветка, написанная под боевой диалект, не исполнилась бы
    тестами НИ РАЗУ — она проверялась бы впервые на деплое. Прецедент выписан в
    докстринге ревизии 0015; перечень запрещённых имён — в комментарии над
    запросом ниже (в докстринге их нет НАМЕРЕННО: запрет держит тест
    test_module_has_no_dialect_specific_calendar_functions, и он ищет имена по
    сырому тексту модуля, снимая только строчные комментарии).
    Дополнительная причина именно здесь: час ячейки — ЛОКАЛЬНЫЙ час
    пользователя (D-10), а перевод в его зону база не делает вовсе.

    ПОЧЕМУ ПРОЕКЦИЯ И ПОТОК. Выбирается ТОЛЬКО `sent_at`, а не сущность
    `SendLog`: ни одного ORM-объекта не создаётся и identity map не растёт.
    Чтение идёт `session.stream(...)` с `yield_per`, поэтому память держится
    порядка размера батча, а не размера окна — окно недели на самой растущей
    таблице системы иначе поднималось бы в память целиком (T-04-14).

    ЧТО В СЕТКУ ПОПАДАЕТ. ВСЕ отправки окна, принадлежащие `user_id`. Запись с
    пустым `group_id` или пустым `messenger_type` считается наравне с
    остальными: она произошла в реальный час, и выбросить её ради «чистой»
    сетки значило бы соврать о том, работала система в этот час или стояла.
    Запись, попавшая ровно в правый край окна, приписывается последним суткам,
    а не отбрасывается — по той же причине.

    Пустой набор данных даёт сетку НУЛЕЙ, а не пустой список: шаблон обходит
    ряды и ячейки, и пустой список отрисовал бы вместо сетки ничего — блок
    выглядел бы сломанным, а не пустым.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if tz is None:
        tz = timezone.utc

    window_start = now - timedelta(days=days)
    local_origin = window_start.astimezone(tz)

    grid = [[0] * 24 for _ in range(days)]

    # Запрещённые в этом модуле имена календарной группировки средствами
    # диалекта: func.strftime, func.date_trunc, func.extract, func.to_char,
    # func.julianday (RESEARCH §Pitfall 2). Запрос ниже выбирает ЗНАЧЕНИЯ и
    # ничего не группирует — вся календарная арифметика идёт в Python.
    stream = await session.stream(
        select(SendLog.sent_at)
        .where(
            SendLog.user_id == user_id,
            SendLog.sent_at >= window_start,
        )
        .execution_options(yield_per=HEATMAP_YIELD_PER)
    )
    async for row in stream:
        # normalize_utc обязателен: SQLite отдаёт `sent_at` NAIVE, и вычитание
        # naive из aware поднимает TypeError — то есть дефект существовал бы
        # только на одном из двух диалектов и ловился бы не тестами.
        local = normalize_utc(row.sent_at).astimezone(tz)
        offset_hours = int((local - local_origin).total_seconds() // 3600)
        day_index = offset_hours // 24
        # Клампы, а не `continue`: запись ровно в `now` даёт смещение `days*24`
        # и индекс на один больше последнего ряда. Она принадлежит самым свежим
        # суткам окна, и пропуск такой записи был бы ровно тем молчаливым
        # выбрасыванием, которое прохибиция плана запрещает.
        if day_index >= days:
            day_index = days - 1
        elif day_index < 0:
            day_index = 0
        grid[day_index][local.hour] += 1

    return HeatmapView(
        grid=grid,
        day_labels=[
            SHORT_WEEKDAYS[(local_origin + timedelta(days=i)).weekday()]
            for i in range(days)
        ],
        peak=max((max(day) for day in grid), default=0),
    )


# --- Столбцы активности за неделю ---------------------------------------------

# Столбцов у бар-чарта макета 28: семь суток окна по четыре шестичасовых доли.
# Число живёт ЗДЕСЬ, а не в шаблоне и не в CSS: от него считаются и сами
# столбцы, и то, сколько их приходится на одну подпись дня. Второй источник
# этого числа разъехался бы с первым молча — подписи поехали бы относительно
# столбцов, и заметил бы это только глаз.
CHART_BUCKETS_PER_DAY = 4
CHART_BUCKET_HOURS = 24 // CHART_BUCKETS_PER_DAY


@dataclass(slots=True)
class ActivityChartView:
    """Столбцы активности окна: `days * CHART_BUCKETS_PER_DAY` долей и подписи суток.

    `peak` отдаётся ВЫЗЫВАЮЩЕМУ по той же причине, что и у сетки: высота
    столбца — вопрос отображения, а обход всех столбцов второй раз средствами
    Jinja ради максимума был бы обходом уже известного числа.
    """

    bars: list[int]
    day_labels: list[str]
    peak: int


def activity_chart(view: HeatmapView) -> ActivityChartView:
    """Свёртывает часовую сетку в столбцы бар-чарта.

    ВТОРОГО ЗАПРОСА ЗДЕСЬ НЕТ и быть не должно. Столбец есть сумма своих шести
    часов, а часы уже разложены `activity_heatmap` — с локальной зоной читателя
    (D-10), скользящим окном и подписями, следующими окну (D-12). Посчитать их
    заново своим запросом значило бы завести второй источник тех же чисел и
    вторую копию календарной арифметики, которой в этом модуле разрешено
    существовать ровно в одном месте.

    Функция ЧИСТАЯ и синхронная: сессия ей не нужна, и тест на неё не требует
    ни базы, ни фикстур.

    Пустое окно даёт столбцы НУЛЕЙ, а не пустой список — по той же причине, что
    и сетка: шаблон обходит столбцы, и пустой список отрисовал бы вместо графика
    ничего, то есть блок выглядел бы сломанным, а не пустым.
    """
    bars: list[int] = []
    for day_row in view.grid:
        for start in range(0, 24, CHART_BUCKET_HOURS):
            # Срез, а не sum по индексам: доля последнего блока обязана взять
            # ровно оставшиеся часы, даже если 24 перестанет делиться нацело.
            bars.append(sum(day_row[start : start + CHART_BUCKET_HOURS]))
    return ActivityChartView(
        bars=bars,
        day_labels=list(view.day_labels),
        peak=max(bars, default=0),
    )


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
                    select(Group.id, Group.is_active).where(Group.id.in_(group_ids))
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
