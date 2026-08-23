from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlencode

import structlog
from fastapi import APIRouter, Depends, Form, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings, require_admin
# ⚠️ АГРЕГАТОВ ЖУРНАЛА ОТПРАВОК ЭТОТ МОДУЛЬ НЕ СТРОИТ — ОН ИХ ЗОВЁТ (D-35, D-39).
# Конструктор SQL-функций (`func`) здесь не импортируется ВОВСЕ, и это не
# аккуратность, а проверяемое свойство: пока агрегат стоял в обработчике, запрет
# «не заводить второй счёт отправок» исполнял человек, а теперь его исполняет
# `test_the_admin_pages_module_builds_no_aggregate_over_the_send_journal`.
# Числа, о которых аналитика отправок не знает (люди, деньги, объявления,
# группы), считает `app/application/admin/overview_stats.py`.
from app.application.analytics.send_analytics import (
    apply_history_filters,
    history_filter_params,
    last_send_at,
    send_metrics,
)
from app.application.admin.incidents import (
    INCIDENT_LIST_CAP,
    WorkerLiveness,
    collect_incidents,
)
from app.application.admin.overview_stats import (
    account_counts_by_user,
    monthly_revenue,
    paying_total,
    user_card_counts,
    user_totals,
)
from app.application.admin.payments_query import (
    EXPIRED_LOOKBACK_DAYS,
    PAYMENT_PERIOD_CHIPS,
    PAYMENT_PERIOD_VALUES,
    PAYMENT_STATUS_CHIPS,
    PAYMENT_STATUS_VALUES,
    expired_not_renewed,
    payment_ledger,
)
from app.application.admin.queue_rows import (
    QUEUE_ROW_CAP,
    queue_rows,
    telegram_lag_seconds,
)
from app.application.admin.users_query import (
    ACCESS_CHIPS,
    ACCESS_VALUES,
    STATE_CHIPS,
    STATE_VALUES,
    users_page,
)
from app.application.billing.subscription_period import access_is_open, days_left
from app.pages.history import (
    MESSENGER_VALUES,
    PAGE_SIZE,
    PERIOD_VALUES,
    STATUS_VALUES,
    clean_choice,
    parse_account_id,
)
from app.models.user import User
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.models.subscription import Subscription
from app.pages.common import is_same_origin, templates
from app.services import max_container_manager, wa_container_manager
from app.services.billing_cache import invalidate_access_cache
from app.services.loki_client import (
    LEVEL_CHIP_OPTIONS,
    LOG_LINE_CAP,
    LOG_SOURCES,
    LOG_SOURCE_TELEGRAM_WORKER,
    LOG_WINDOWS,
    LOG_WINDOW_CHIPS,
    build_logql,
    clean_level,
    clean_source,
    clean_window,
    query_range,
)
from app.services.ops_state import (
    CHANNEL_MAX,
    CHANNEL_WA,
    DROP_MISSING,
    DROP_REMOVED,
    DROP_UNAVAILABLE,
    INFRA_BEAT,
    INFRA_WORKER_DEFAULT,
    INFRA_WORKER_TELEGRAM,
    WORKER_ONLINE,
    WORKER_UNKNOWN,
    drop_task,
    infra_heartbeat_key,
    infra_liveness,
    queue_page,
    telegram_queue_depth,
    worker_liveness,
)

logger = structlog.get_logger(__name__)

# ЧИТАТЕЛЕЙ ОСТАТКА СООБЩЕНИЙ ЗДЕСЬ БОЛЬШЕ НЕТ. Ревизия `0020` уронила таблицы
# `message_balances` и `balance_transactions`; две функции, которые их читали,
# сняты вместе с ними из `app/services/billing_service.py`. Их место заняли
# читатели ДОСТУПА, введённые планом `05.1-09` поверх строки подписки: колонка
# списка, плитка карточки и тумблер. Порядок был такой, потому что снятие таблиц
# необратимо, а тумблер нет.

router = APIRouter(prefix="/admin", tags=["admin"])

# ВТОРОЙ РОУТЕР МОДУЛЯ — ПАРШАЛЫ ОПРОСА, ВКЛЮЧАЕМЫЕ МИМО СТРАНИЧНОЙ СБОРКИ.
#
# ⚠️ ОН ОБЪЯВЛЕН ЗДЕСЬ, А ВКЛЮЧАЕТСЯ В `app/main.py` РЯДОМ С `dashboard_feed`.
# Причина ровно та же, по которой живая лента Фазы 4 вынесена из страничного
# роутера: `app/pages/__init__.py` вешает `load_shell_context` на КАЖДЫЙ свой
# маршрут, а та делает четыре обращения к базе. Опрос бессрочен (D-12), поэтому
# эта цена умножалась бы на число открытых вкладок и делилась на интервал
# опроса — то есть платилась бы вечно за то, чего паршал не рисует.
#
# ⚠️ ЕГО ОТСУТСТВИЕ В СТРАНИЧНОЙ СБОРКЕ НЕ ДЕЛАЕТ ЕГО ОТКРЫТЫМ. Права
# администратора висят на самом обработчике, а решение «закрывает ли его
# истёкший доступ» записано ВТОРЫМ местом в `tests/test_pages/test_access_gate.py`
# — молчаливое добавление роутера в сборку этот тест роняет по построению.
partials_router = APIRouter(prefix="/admin", tags=["admin"])


# ПОДРАЗДЕЛ АДМИН-ПАНЕЛИ ЕСТЬ МАРШРУТ, А НЕ СОСТОЯНИЕ НА ОДНОМ ЭКРАНЕ (D-01).
# В макете вкладки переключаются состоянием потому, что макет статический, —
# это не указание к архитектуре. Контракт Фазы 1 требует, чтобы базовый путь
# работал без JS, и переключение подраздела подменой блока сделало бы навигацию
# JS-зависимой: администратор, пришедший чинить аварию с урезанным браузером,
# остался бы с одним подразделом из шести.
#
# ⚠️ ПЕРЕЧЕНЬ ОБЪЯВЛЕН ЗДЕСЬ ОДИН РАЗ и читается И обработчиками, И разметкой
# вкладок (`admin/includes/_tabs.html`). Вторая копия подписей в шаблоне
# разъехалась бы с этой молча — подпись поменяли бы в одном месте, а активная
# вкладка продолжала бы подсвечиваться по старому ключу.
ADMIN_TABS: tuple[dict[str, str], ...] = (
    {"key": "overview", "label": "Обзор", "href": "/admin"},
    {"key": "users", "label": "Пользователи", "href": "/admin/users"},
    {"key": "workers", "label": "Воркеры", "href": "/admin/workers"},
    {"key": "queue", "label": "Очередь", "href": "/admin/queue"},
    {"key": "logs", "label": "Логи", "href": "/admin/logs"},
    {"key": "payments", "label": "Платежи", "href": "/admin/payments"},
)


# ИНФРАСТРУКТУРНЫЙ БЛОК ПОДРАЗДЕЛА «ВОРКЕРЫ» (D-09, источник признака — D-52).
#
# ⚠️ ПЕРЕЧЕНЬ СЛУЖБ ОБЪЯВЛЕН ОДИН РАЗ, а имена служб приходят из сервиса
# оперативного состояния: вторая копия имён разъехалась бы с ключами Redis
# молча — блок продолжал бы рисовать три строки, читая ключи, которых никто не
# пишет, и показывал бы «отключён» на исправных службах.
#
# ⚠️ `source` — ЭТО ТО, ЧТО ВИДИТ АДМИНИСТРАТОР В АВАРИИ. Вердикт без указания,
# ЧЕМ он получен, заставляет верить на слово; названный ключ позволяет
# проверить его руками за одну команду. Поэтому подпись источника печатается, а
# не живёт комментарием в исходнике.
INFRA_SERVICES: tuple[dict[str, str], ...] = (
    {
        "key": INFRA_BEAT,
        "label": "Планировщик расписаний",
        "source": "Процесс celery-beat обновляет этот ключ раз в 30 секунд",
    },
    {
        "key": INFRA_WORKER_TELEGRAM,
        "label": "Воркер Telegram",
        "source": "Процесс, разбирающий очередь telegram, обновляет этот ключ раз в 30 секунд",
    },
    {
        "key": INFRA_WORKER_DEFAULT,
        "label": "Воркер общих задач",
        "source": "Процесс, разбирающий очередь default, обновляет этот ключ раз в 30 секунд",
    },
)

# ИНТЕРВАЛ ОПРОСА ПОДРАЗДЕЛА (D-12). Живёт константой модуля, а не литералом в
# разметке: адрес паршала и его частота объявлены рядом, и выписанные порознь
# они разъехались бы молча — так же, как это уже закрыто у живой ленты
# (`FEED_POLL_SECONDS`, `app/pages/dashboard_feed.py`).
#
# ⚠️ АВТОСТОПА НЕТ НАМЕРЕННО, И МОТИВ ОТЛИЧАЕТСЯ ОТ ЖИВОЙ ЛЕНТЫ. Администратор
# открывает этот подраздел В МОМЕНТ АВАРИИ: замершее состояние здесь вреднее,
# чем на дашборде, потому что решение о перезапуске принимается по нему.
WORKERS_POLL_SEC = 20

# ЗАКРЫТОЕ МНОЖЕСТВО ПРИЧИН ОТКАЗА ПЕРЕЗАПУСКА, И СЛОВА ЖИВУТ ЗДЕСЬ, А НЕ В
# РАЗМЕТКЕ (Pitfall 7).
#
# ⚠️ КНОПКА, ВЕРНУВШАЯ ТУ ЖЕ СТРАНИЦУ МОЛЧА, ЧИТАЕТСЯ КАК СЛОМАННАЯ. Именно для
# этого проект держит форму «отказ не проглатывается молча»; здесь она нужнее,
# чем где-либо, потому что кнопку жмут в аварии и по её результату решают, идти
# ли на сервер руками.
#
# ⚠️ ТЕКСТ СТОРОННЕГО ИСКЛЮЧЕНИЯ НА ЭКРАН НЕ ВЫХОДИТ. Он ничего не сообщает
# администратору и способен вынести наружу внутренние пути и адреса; причина
# берётся ИЗ ЭТОГО СЛОВАРЯ по ключу, а неизвестный ключ из адресной строки не
# рисует ничего. Владелец ссылки не может ни выбрать чужой текст, ни подставить
# свой.
WORKER_RESTART_ERRORS: dict[str, str] = {
    "restart_failed": (
        "Не удалось перезапустить воркер — демон контейнеров не отвечает"
    ),
    "no_container": (
        "У этого канала своего воркера нет: перезапускать нечего. "
        "Задачи Telegram разбирает общий celery-воркер очереди telegram"
    ),
}

# Подписи каналов нижнего блока. Порядок несущий: telegram первым, потому что
# его строка — единственная, чей воркер общий, и объяснение стоит выше строк, к
# которым оно не относится.
WORKER_CHANNELS: tuple[dict[str, str], ...] = (
    {"key": "tg_user", "label": "Telegram"},
    {"key": "wa", "label": "WhatsApp"},
    {"key": "max", "label": "MAX"},
)

# КАКОЙ МЕНЕДЖЕР ПОДНИМАЕТ ВОРКЕР КАКОГО КАНАЛА (D-11).
#
# ⚠️ ОТСУТСТВИЕ КАНАЛА В ЭТОМ СЛОВАРЕ — ОТВЕТ, А НЕ ПРОБЕЛ. У telegram-канала
# своего контейнера нет вовсе, поэтому перезапускать нечего, и обработчик
# отказывает СЛОВАМИ вместо того, чтобы притвориться успешным. Ветка «если
# канал неизвестен — попробуем WhatsApp» отсутствует намеренно: она подняла бы
# контейнер чужого типа под идентификатором этого аккаунта.
#
# ⚠️ МОДУЛИ ИМПОРТИРУЮТСЯ ЦЕЛИКОМ, А НЕ ИМЕНАМИ ФУНКЦИЙ. Связывание имени при
# импорте сделало бы вызов неподменяемым в суите: тест подменяет функцию в её
# СОБСТВЕННОМ модуле, и локальная копия имени продолжала бы звать настоящий
# демон — то есть проверка «контейнер поднят» ходила бы на живой сокет.
WORKER_RESTART_MANAGERS = {
    "wa": wa_container_manager,
    "max": max_container_manager,
}


# ПОДРАЗДЕЛ «ОЧЕРЕДЬ» (ADMIN-08, D-13 … D-18).
#
# ⚠️ КАНАЛОВ ЗДЕСЬ ДВА, А НЕ ТРИ, И ЭТО ОТВЕТ, А НЕ ПРОБЕЛ. У telegram-канала
# тело задачи — конверт брокера с закодированным содержимым, и решение D-14
# запрещает его распаковывать: разбор привязал бы админку к внутренностям
# библиотеки, которые меняются между версиями молча. Поэтому построчного списка
# у него нет вовсе, а есть число задач и величина, измеримая СНАРУЖИ конверта.
# Третий блок собирается отдельно и устроен иначе — намеренно.
QUEUE_CHANNELS: tuple[dict[str, str], ...] = (
    {"key": "wa", "label": "WhatsApp"},
    {"key": "max", "label": "MAX"},
)

# Канал, чьи задачи разбирает общий celery-воркер. Значение — то же, которым
# `MessengerAccount.type` и `SendLog.messenger_type` называют telegram-аккаунт:
# вторая копия строки разъехалась бы с ними молча, и блок канала показывал бы
# уверенный ноль отправок.
QUEUE_TELEGRAM_CHANNEL = "tg_user"

# ЗАКРЫТОЕ МНОЖЕСТВО ИСХОДОВ СНЯТИЯ ЗАДАЧИ, И СЛОВА ЖИВУТ ЗДЕСЬ, А НЕ В
# РАЗМЕТКЕ — по той же форме, что у отказов перезапуска выше.
#
# ⚠️ ОТСУТСТВИЕ ЗАДАЧИ — ТОЖЕ ИСХОД, И ОН НАЗЫВАЕТСЯ СЛОВАМИ. Задача могла уйти
# из очереди сама, пока администратор читал экран; молчаливый возврат на ту же
# страницу он прочитал бы как «кнопка сломана» — и пошёл бы жать её снова.
#
# ⚠️ ПАРАМЕТР АДРЕСНОЙ СТРОКИ — КЛЮЧ, А НЕ ТЕКСТ. Владелец ссылки не может ни
# выбрать чужую формулировку, ни подставить свою: неизвестный ключ не рисует
# ничего.
QUEUE_DROP_RESULTS: dict[str, tuple[str, str]] = {
    DROP_REMOVED: ("Задача снята из очереди", "success"),
    DROP_MISSING: ("Задача уже ушла из очереди — снимать нечего", "warning"),
    DROP_UNAVAILABLE: (
        "Не удалось снять задачу: Redis не отвечает, а очередь хранится только "
        "в нём",
        "error",
    ),
    "unknown_account": (
        "Снимать нечего: у этого аккаунта нет своей очереди задач",
        "warning",
    ),
}

# ПОТОЛОК ЧТЕНИЯ НА ОДНУ ОЧЕРЕДЬ — НА ЕДИНИЦУ БОЛЬШЕ ПОТОЛКА ПОКАЗА.
#
# Лишний элемент читается НЕ ради показа: он и есть улика усечения. Без него
# «прочитано ровно столько, сколько потолок» было бы неотличимо от «в очереди
# ровно столько», и разметка не смогла бы назвать усечение — то есть молча
# ответила бы «остальных задач нет» на вопрос, ради которого сюда пришли.
QUEUE_READ_LIMIT = QUEUE_ROW_CAP + 1


def _admin_context(request: Request, admin: User, tab: str) -> dict:
    """Общая часть контекста любого подраздела админ-панели.

    `active_page` подсвечивает раздел в сайдбаре шелла и через `nav_label`
    рисует заголовок — собственного заголовка подразделам заводить не нужно.
    `admin_tab` отмечает активную вкладку, `admin_tabs` отдаёт сам перечень.
    """
    return {
        "request": request,
        "user": admin,
        "is_admin": True,
        "active_page": "admin",
        "admin_tab": tab,
        "admin_tabs": ADMIN_TABS,
    }


async def _active_subscriptions_by_user(
    db: AsyncSession, user_ids: list[int]
) -> dict[int, Subscription]:
    """Активные строки подписки перечисленных пользователей — ОДНИМ запросом.

    ⚠️ ОДИН ЗАПРОС НА СПИСОК, А НЕ ЗАПРОС НА СТРОКУ. Прежний цикл админского
    списка ходил в базу за каждым пользователем и вдобавок ЗАВОДИЛ недостающую
    строку прямо в `GET`-е; он снят планом `05.1-08` вместе со своим предметом, и
    возвращать его форму сюда нельзя: число обращений росло бы вместе с числом
    зарегистрированных, а страница администратора видит их всех сразу.

    ОТБОР ПОВТОРЯЕТ `get_shell_context` ДОСЛОВНО (`app/pages/common.py`): те же
    два условия и та же сортировка по сроку. Администратор обязан видеть ТУ
    строку, по которой продукт решает про доступ, — иначе колонка показывала бы
    одно, а дверь отвечала бы другое. Частичный уникальный индекс
    `uq_subscriptions_active_user` гарантирует не более одной активной строки на
    пользователя, поэтому словарь не теряет данных; сортировка оставлена ради
    совпадения с читателем, а не ради разрешения коллизий.

    Пустой список НЕ ходит в базу: `IN ()` — синтаксическая ошибка на части
    диалектов и бессмысленный запрос на остальных.
    """
    if not user_ids:
        return {}

    rows = (
        await db.execute(
            select(Subscription)
            .where(
                Subscription.user_id.in_(user_ids),
                Subscription.is_active.is_(True),
            )
            .order_by(Subscription.expires_at.desc())
        )
    ).scalars()
    return {row.user_id: row for row in rows}


def _access_view(subscription: Subscription | None, now: datetime) -> dict:
    """Состояние доступа пользователя ДЛЯ ПОКАЗА администратору.

    ⚠️ ВЕРДИКТ БЕРЁТСЯ У ЕДИНСТВЕННОГО ПРЕДИКАТА ПРОЕКТА, а не считается здесь
    вторым сравнением дат. Админская колонка — четвёртая поверхность, читающая
    одно и то же правило (шелл, гейт страниц, гейт пути отправки), и своя копия
    правила в админке разошлась бы с остальными молча: администратор видел бы
    «открыт» у человека, которому продукт уже отказывает, и снимал бы с него
    несуществующую проблему.

    ПРИЗНАК ЛЬГОТЫ ЕДЕТ ОТДЕЛЬНЫМ КЛЮЧОМ, А НЕ ВЫВОДИТСЯ ИЗ ВЕРДИКТА: «открыт»
    и «открыт бесплатно» — разные состояния для того, кто эту льготу выдаёт, и
    свести их в одно значило бы спрятать от администратора собственное действие.

    `days_left` может быть ОТРИЦАТЕЛЕН у льготного пользователя с мёртвой датой,
    и разметка обязана это учитывать — число дней печатается только там, где
    доступ открыт СРОКОМ. Здесь величина отдаётся как есть: подменять её нулём
    значило бы соврать о том, сколько срок как уже просрочен.
    """
    is_comped = bool(subscription.has_free_access) if subscription else False
    expires_at = subscription.expires_at if subscription else None
    return {
        "open": access_is_open(subscription, now),
        "is_comped": is_comped,
        "expires_at": expires_at,
        "days_left": days_left(expires_at, now),
    }


def _liveness_for_incidents(
    views: dict[int, dict],
) -> tuple[dict[int, WorkerLiveness], bool]:
    """Переходник от формы сервиса к форме прикладного модуля признаков.

    ⚠️ ПЕРЕХОДНИК ЖИВЁТ ЗДЕСЬ, НА СТОРОНЕ ПОТРЕБИТЕЛЯ, И ЭТО НЕСУЩЕЕ РЕШЕНИЕ
    СТЫКА. Модуль признаков (`app/application/admin/incidents.py`) принимает
    живость ЗНАЧЕНИЯМИ и не знает ни одного клиента внешней службы — именно
    поэтому пять признаков проверяются суитой на SQLite без единого поднятого
    стенда. Импортируй он сервис оперативного состояния, чтобы «самому
    разобраться» с формой ответа, — и суита признаков потребовала бы Redis, то
    есть перестала бы гонять их на каждом прогоне. Плата за это ровно одна: у
    сервиса своя форма ответа, и перевод её в форму модуля кто-то обязан
    написать. Пишем его здесь.

    ⚠️ СВЕЖЕСТЬ HEARTBEAT ПРИЕЗЖАЕТ УЖЕ РЕШЁННОЙ, а не сырым возрастом: порог
    объявлен там, где heartbeat читается (`MAX_HEARTBEAT_STALE_SEC`), и второй
    порог на стороне признаков разошёлся бы с первым молча.

    ⚠️ «НЕИЗВЕСТНО» НЕ ПРЕВРАЩАЕТСЯ НИ В ЧТО. Аккаунт, о котором наблюдатель не
    смог сказать ничего, из отображения ВЫПАДАЕТ, а вызывающий получает признак
    неполноты. Подстановка «живой» спрятала бы настоящий отказ, подстановка
    «мёртвый» подняла бы инцидент на исправном воркере, и обе были бы догадкой,
    поданной как измерение.
    """
    liveness: dict[int, WorkerLiveness] = {}
    partial = False
    for account_id, view in views.items():
        depth = view.get("queue_depth")
        state = view.get("worker")
        if depth is None or state == WORKER_UNKNOWN:
            partial = True
            continue
        liveness[account_id] = WorkerLiveness(
            queue_depth=int(depth),
            heartbeat_fresh=state == WORKER_ONLINE,
        )
    return liveness, partial


@dataclass(frozen=True, slots=True)
class _OpsSnapshot:
    """Оперативное состояние на момент запроса «Обзора» — ОДНИМ чтением.

    Живость воркеров аккаунтов и глубина очереди канала брокера нужны и плитке
    задач, и блоку инцидентов. Два независимых чтения дали бы два снимка разного
    момента, и плитка могла бы не сойтись с блоком под ней на глазах у
    администратора — при том что оба числа он читает как одно состояние.

    `queue_total` равен `None`, когда хотя бы один источник не прочитан:
    сумма, посчитанная по части источников, выглядит измеренной и таковой не
    является. Ноль вместо неё читался бы как «очередь пуста», то есть как ОТВЕТ
    на вопрос, которого мы не знаем.
    """

    liveness: dict[int, dict]
    telegram_depth: int | None
    queue_total: int | None
    partial: bool


async def _ops_snapshot(db: AsyncSession) -> _OpsSnapshot:
    """Живость воркеров аккаунтов и глубина очереди брокера — на один момент."""
    accounts = (
        (await db.execute(select(MessengerAccount).order_by(MessengerAccount.id)))
        .scalars()
        .all()
    )
    liveness = await worker_liveness(
        [a.id for a in accounts if a.type == CHANNEL_WA],
        [a.id for a in accounts if a.type == CHANNEL_MAX],
    )
    telegram_depth = await telegram_queue_depth()

    depths = [view.get("queue_depth") for view in liveness.values()]
    partial = telegram_depth is None or any(depth is None for depth in depths)
    queue_total = (
        None if partial else telegram_depth + sum(depth for depth in depths)
    )
    return _OpsSnapshot(
        liveness=liveness,
        telegram_depth=telegram_depth,
        queue_total=queue_total,
        partial=partial,
    )


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Подраздел «Обзор»: ключевые показатели сервиса и текущие инциденты.

    ⚠️ ЧИСЛО ОШИБОК БЕРЁТСЯ У МОДУЛЯ АНАЛИТИКИ, А НЕ СЧИТАЕТСЯ ЗДЕСЬ (D-39).
    На тот же вопрос отвечает пользовательский дашборд, и второй счёт рядом
    означал бы день, когда администратор и пользователь смотрят на РАЗНЫЕ числа
    об одном и том же периоде и оба считают своё верным. Общесистемная область
    передаётся ЯВНО (`user_id=None`), потому что умолчания у параметра нет.

    ⚠️ ОКНО ОШИБОК — СУТКИ, А НЕ ЧАС ИЗ МАКЕТА (D-40). Модуль настроен на
    скользящие 24 часа, дельта приезжает тем же обращением к базе, и цифра
    «Обзора» совпадает с той, что пользователь видит у себя. Острые всплески
    ловит блок инцидентов — у него на это свой признак с окном в час (D-51).
    """
    now = datetime.now(timezone.utc)

    users = await user_totals(db, now=now)
    paying = await paying_total(db, now=now)
    metrics = await send_metrics(db, user_id=None, now=now)

    ops = await _ops_snapshot(db)
    liveness, liveness_partial = _liveness_for_incidents(ops.liveness)
    board = await collect_incidents(db, liveness, now=now)

    # ⚠️ ВЕЛИЧИНА ВРЕМЕНИ СЧИТАЕТСЯ ТОЛЬКО ПРИ НЕПУСТОЙ ОЧЕРЕДИ КАНАЛА, и это то
    # же правило, по которому её печатает подраздел «Очередь». Время с последней
    # отправки на ПУСТОЙ очереди означает «работы не было», а не «работа стоит»,
    # и напечатанное оно тревожило бы администратора ровно там, где всё в
    # порядке.
    queue_time_sec = None
    if ops.telegram_depth:
        queue_time_sec = telegram_lag_seconds(
            await last_send_at(db, messenger_type=QUEUE_TELEGRAM_CHANNEL), now
        )

    return templates.TemplateResponse(
        "admin/overview.html",
        {
            **_admin_context(request, admin, "overview"),
            "users": users,
            "paying": paying,
            "mrr": monthly_revenue(paying, settings.subscription_price),
            "queue_total": ops.queue_total,
            "queue_time_sec": queue_time_sec,
            "metrics": metrics,
            "board": board,
            "incident_cap": INCIDENT_LIST_CAP,
            # ⚠️ НЕПОЛНОТА КАРТИНЫ НАЗЫВАЕТСЯ, А НЕ УМАЛЧИВАЕТСЯ. Признак «воркер
            # не забирает работу» считается из живости, а живость лежит только в
            # Redis: при недоступном наблюдателе он не считается ВОВСЕ. Блок,
            # промолчавший об этом, выглядел бы полным и таковым не был бы —
            # худший из возможных исходов, потому что администратор прочитал бы
            # «остальное в порядке» там, где остального просто не посчитали.
            "incidents_partial": liveness_partial,
        },
    )


def _parse_page(value: str | None) -> int:
    """Номер страницы из адреса — ЧИСЛОМ, и без отказа на мусоре.

    Объявить параметр как `int` значило бы отдать 422 на `?page=абв`, то есть
    отказать в обслуживании по значению, которое приезжает из ссылки, закладки
    или чужого сообщения (T-06-USR3). Разбор здесь, а зажим диапазона — в модуле
    выборки, который один знает, сколько страниц получилось.
    """
    try:
        return int((value or "").strip())
    except (TypeError, ValueError):
        return 1


def _users_href(params: dict[str, str], page: int) -> str:
    """Адрес подраздела с текущими фильтрами и ЗАДАННЫМ номером страницы.

    ⚠️ АДРЕС СОБИРАЕТСЯ ЗДЕСЬ, А НЕ В РАЗМЕТКЕ. Имена параметров объявлены
    подписью обработчика ниже; литерал, собранный в шаблоне, разъехался бы с
    ними молча — переход отвечал бы 200 и терял фильтр. Тот же довод стоит в
    модуле признаков инцидента, где адреса переходов тоже приходят из кода.
    """
    query = dict(params)
    query["page"] = str(page)
    return f"/admin/users?{urlencode(query)}"


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    q: str = "",
    access: str | None = Query(default=None),
    state: str | None = Query(default=None),
    page: str | None = Query(default=None),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Подраздел «Пользователи»: поиск, две оси, страницы по 50, честный счётчик.

    ⚠️ ПОИСК, ОБЕ ОСИ, СТРАНИЦА И СЧЁТЧИК СЧИТАЮТСЯ ОДНИМ ВЫРАЖЕНИЕМ (D-34).
    Обработчик не строит условий сам — он передаёт значения в модуль выборки,
    где `count_users` зовёт ту же `apply_user_filters`, что и страница. Проект
    уже платил за нарушение этого правила в разделе истории: счётчик обещал
    записи, которых в выдаче не было.

    ⚠️ ЗНАЧЕНИЯ ОСЕЙ САНИРУЮТСЯ ЗДЕСЬ ТОЖЕ, ХОТЯ МОДУЛЬ САНИРУЕТ ИХ САМ. Модуль
    отсекает мусор для ЗАПРОСА; здесь отсечка нужна для РАЗМЕТКИ: неотсечённое
    значение доехало бы до чипсов как активное, и администратор увидел бы
    подсвеченный фильтр, которого не задавал и который ничего не отбирает.
    Отсекает ОБЩАЯ функция проекта, а не своя копия (`clean_choice`).
    """
    search = (q or "").strip()
    access = clean_choice(access, ACCESS_VALUES)
    state = clean_choice(state, STATE_VALUES)

    # МОМЕНТ СНИМАЕТСЯ ОДИН НА ВЕСЬ ЗАПРОС — и для отбора по оси доступа, и для
    # вердикта каждой строки. Посчитанные от разных `now`, отбор и бейдж
    # разъехались бы на границе суток: строка попала бы под чипс «открыт» и
    # отрисовалась «закрыт» (T-05.1-19).
    now = datetime.now(timezone.utc)
    result = await users_page(
        db, search=search, access=access, state=state, now=now, page=_parse_page(page)
    )

    # СПИСОК НЕ ХОДИТ В БАЗУ ЗА КАЖДЫМ ПОЛЬЗОВАТЕЛЕМ: и подписки, и число
    # аккаунтов собираются ОДНИМ запросом на всю страницу.
    user_ids = [u.id for u in result.users]
    subscriptions = await _active_subscriptions_by_user(db, user_ids)
    accounts = await account_counts_by_user(db, user_ids)
    user_data = [
        {
            "user": u,
            "access": _access_view(subscriptions.get(u.id), now),
            "accounts": accounts.get(u.id, 0),
        }
        for u in result.users
    ]

    # ⚠️ НОМЕР СТРАНИЦЫ В НАБОР ФИЛЬТРОВ НЕ ВХОДИТ. Набор проносится чипсами при
    # смене оси, и сохранённый номер дал бы пустой экран при непустой выдаче:
    # страницы пересчитались, а адрес всё ещё указывает на седьмую.
    filter_params = {
        key: value
        for key, value in (("q", search), ("access", access), ("state", state))
        if value
    }

    return templates.TemplateResponse(
        "admin/users.html",
        {
            **_admin_context(request, admin, "users"),
            "users": user_data,
            "users_total": result.total,
            "users_page_number": result.page,
            "users_pages": result.pages,
            "search_query": search,
            "access_chips": ACCESS_CHIPS,
            "state_chips": STATE_CHIPS,
            "filter_access": access,
            "filter_state": state,
            "filter_params": filter_params,
            "prev_page_href": (
                _users_href(filter_params, result.page - 1) if result.page > 1 else None
            ),
            "next_page_href": (
                _users_href(filter_params, result.page + 1)
                if result.page < result.pages
                else None
            ),
        },
    )


@router.get("/workers", response_class=HTMLResponse)
async def admin_workers(
    request: Request,
    error: str | None = Query(None),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Подраздел «Воркеры»: состояние сессии из базы и живость воркера из Redis.

    ⚠️ ЖИВОСТЬ ЧИТАЕТСЯ СЕРВИСОМ, А НЕ ЭТИМ ОБРАБОТЧИКОМ. Обращение к Redis,
    написанное здесь, было бы непроверяемо: суита идёт на SQLite без внешних
    служб и подменяет ИМЕНОВАННУЮ точку `app.services.ops_state._get_redis`.

    ⚠️ КОНТЕЙНЕРНОГО API ЗДЕСЬ НЕТ НИ ОДНОЙ СТРОКОЙ, и это контракт Фазы 1,
    оставленный в силе буквально: демон, недоступный на пути рендера, вешал бы
    подраздел ровно тогда, когда его открывают ради аварии. Утверждение
    снимается разбором ЭТОГО исходника по синтаксическому дереву в
    `tests/test_pages/test_admin_panel.py`, а не наблюдением за страницей.

    ⚠️ ИМЯ КОНТЕЙНЕРНОГО КЛИЕНТА НЕ ВЫПИСАНО ЗДЕСЬ НИ РАЗУ, И ЭТО НАМЕРЕННО:
    страховочный греп по модулю считает вхождение и в докстринге тоже, поэтому
    объяснение «почему вызова нет» иначе роняло бы проверку, утверждающую, что
    вызова нет.
    """
    return templates.TemplateResponse(
        "admin/workers.html",
        {
            **_admin_context(request, admin, "workers"),
            **await _workers_view(db),
            # Параметр адресной строки — КЛЮЧ, а не текст: рисуется только то,
            # что объявлено закрытым множеством выше.
            "restart_error": WORKER_RESTART_ERRORS.get(error or ""),
        },
    )


@partials_router.get("/workers/partial", response_class=HTMLResponse)
async def admin_workers_partial(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Очередной снимок обоих блоков подраздела «Воркеры» (D-12).

    ⚠️ ЖИВЁТ ВНЕ СТРАНИЧНОГО РОУТЕРА, И ЭТО НЕ ОФОРМЛЕНИЕ. Страничный роутер
    несёт зависимость `load_shell_context` на КАЖДОМ своём маршруте, а та
    делает четыре обращения к базе ради шелла. Для страницы это правильная цена
    — шелл рисуется. Для паршала цена не разовая: опрос БЕССРОЧЕН, поэтому
    четыре запроса умножились бы на число открытых вкладок и поделились на
    двадцать секунд. Тот же довод и то же решение, что у живой ленты Фазы 4
    (`app/pages/dashboard_feed.py`).

    ⚠️ РОУТЕР БЕЗ ЗАВИСИМОСТИ ШЕЛЛА — ЭТО РОУТЕР БЕЗ ЗАВИСИМОСТИ ШЕЛЛА, А НЕ
    РОУТЕР БЕЗ ПРОВЕРКИ ПРАВ (T-06-PART). Права администратора проверяет
    параметр этого обработчика, и постороннему он отвечает 403 — утверждение
    снято тестом, а не намерением.
    """
    return templates.TemplateResponse(
        "admin/includes/workers_partial.html",
        {"request": request, "user": admin, **await _workers_view(db)},
    )


def _worker_logs_href(account: MessengerAccount) -> str:
    """Адрес логов ЭТОГО воркера с предустановленным фильтром источника (D-10).

    ⚠️ АДРЕС СОБИРАЕТСЯ ЗДЕСЬ, А НЕ В РАЗМЕТКЕ. Литерал в шаблоне разошёлся бы с
    санацией источника молча: ссылка вела бы на 200 и на выдачу БЕЗ фильтра, то
    есть показывала бы логи всех служб как логи одного воркера. Приём тот же,
    каким модуль признаков отдаёт «куда чинить» строкам инцидентов.

    ⚠️ У TELEGRAM-СТРОКИ ИСТОЧНИК — СЛУЖБА, А НЕ АККАУНТ. Своего контейнера у
    канала нет вовсе, поэтому метки идентификатора аккаунта у его записей не
    существует: фильтр по ней дал бы пустоту при исправном запросе. Задачи
    канала разбирает общая служба, и её логи — единственные, где эта строка
    вообще что-то оставляет.

    «Живой лог» в самой строке не делается (D-10): он стал бы вторым
    независимым путём чтения логов рядом с подразделом, а у остановленного по
    простою контейнера живого лога нет вовсе — кнопка была бы мёртвой у
    большинства строк.
    """
    source = (
        LOG_SOURCE_TELEGRAM_WORKER
        if account.type == QUEUE_TELEGRAM_CHANNEL
        else account.id
    )
    return f"/admin/logs?source={source}"


async def _workers_view(db: AsyncSession) -> dict:
    """Оба блока подраздела «Воркеры» — общий контекст страницы и её паршала.

    ⚠️ ОДИН СБОРЩИК НА ДВА ВХОДА. Первичная отрисовка и обновление обязаны
    показывать ОДНО И ТО ЖЕ: разъехавшись, они дали бы экран, который после
    первого же тика меняет содержание без изменения состояния мира — и
    администратор в аварии перестал бы верить обоим.

    Запрос дёшев по построению: живость инфраструктуры — один конвейер Redis,
    живость воркеров аккаунтов — второй, состояния аккаунтов — один `SELECT`.
    Это и есть цена, объявленная принятой в реестре угроз (T-06-POLL).
    """
    accounts = (
        (
            await db.execute(
                select(MessengerAccount).order_by(MessengerAccount.id)
            )
        )
        .scalars()
        .all()
    )

    infra_states = await infra_liveness()
    wa_ids = [a.id for a in accounts if a.type == "wa"]
    max_ids = [a.id for a in accounts if a.type == "max"]
    liveness = await worker_liveness(wa_ids=wa_ids, max_ids=max_ids)

    # ⚠️ У TELEGRAM-СТРОКИ КОЛОНКА «ВОРКЕР» ЧИТАЕТ ЖИВОСТЬ ОБЩЕГО ВОРКЕРА
    # КАНАЛА (D-52). Прежняя редакция D-09 требовала здесь константу «в пуле
    # app»; она отменена решением владельца, потому что истинна безусловно —
    # то есть выглядит измеренным состоянием, ничего не измеряя. Задачи канала
    # уходят в очередь telegram, и разбирает её именно эта служба, поэтому
    # подпись отвечает на вопрос, ради которого в подраздел заходят: есть ли
    # кому забрать мою задачу.
    #
    # ⚠️ ГЛУБИНА ОЧЕРЕДИ У TELEGRAM-СТРОКИ ОТСУТСТВУЕТ ПО ПРИЧИНЕ, А НЕ ПО
    # НЕУДАЧЕ: очередь `telegram` ОДНА на все telegram-аккаунты. Напечатать в
    # каждой строке общее число значило бы выдать его за величину аккаунта.
    telegram_state = {
        "worker": infra_states[INFRA_WORKER_TELEGRAM],
        "queue_depth": None,
        "queue_scope": "shared",
        "worker_hint": (
            "Своего воркера у канала нет: задачи Telegram разбирает общий "
            "celery-воркер очереди telegram — состояние взято у него"
        ),
    }

    rows = [
        {
            "account": account,
            "state": (
                telegram_state
                if account.type == "tg_user"
                else liveness.get(account.id)
            ),
            "logs_href": _worker_logs_href(account),
        }
        for account in accounts
    ]

    groups = [
        {
            "label": channel["label"],
            "rows": [row for row in rows if row["account"].type == channel["key"]],
        }
        for channel in WORKER_CHANNELS
    ]
    # Аккаунт неизвестного канала не исчезает молча: он попадает в собственную
    # группу с именем своего типа. Тихая пропажа строки была бы худшим исходом,
    # чем незнакомая подпись — администратор не узнал бы, что аккаунт вообще
    # есть.
    known = {channel["key"] for channel in WORKER_CHANNELS}
    for account_type in dict.fromkeys(
        row["account"].type for row in rows if row["account"].type not in known
    ):
        groups.append(
            {
                "label": account_type,
                "rows": [
                    row for row in rows if row["account"].type == account_type
                ],
            }
        )

    infra = [
        {
            "label": service["label"],
            "redis_key": infra_heartbeat_key(service["key"]),
            "source": service["source"],
            "state": infra_states[service["key"]],
        }
        for service in INFRA_SERVICES
    ]

    return {
        "infra": infra,
        "groups": groups,
        "rows": rows,
        "workers_poll_sec": WORKERS_POLL_SEC,
    }


@router.post("/workers/{account_id}/restart")
async def admin_restart_worker(
    request: Request,
    account_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Перезапустить воркер аккаунта — ЕДИНСТВЕННОЕ обращение фазы к демону.

    ⚠️ ГРАНИЦА D-07 НЕ НАРУШЕНА, А ПРОЙДЕНА ТАМ, ГДЕ ОНА ПРОВЕДЕНА. Контракт
    запрещает контейнерное API на пути ОТРИСОВКИ, а не в приложении вообще
    (D-11): недоступный демон обязан не мешать открыть подраздел, но обязан
    честно отказать нажатой кнопке. Что вызов не расползся по соседям,
    утверждает двусторонний разбор дерева в
    `tests/test_pages/test_admin_panel.py`.

    ⚠️ ГАРД ПРОИСХОЖДЕНИЯ СТОИТ ПЕРЕД ЛЮБЫМ ДЕЙСТВИЕМ И ОБЯЗАТЕЛЕН
    (T-06-RST2). Аутентификация проекта идёт cookie, поэтому браузер приложит
    её к межсайтовой форме сам, и запрос со стороннего сайта неотличим от
    своего. Сегодня гард несут ровно три формы проекта — две денежные и повтор
    отправки; новая изменяющая форма админки без него МОЛЧА расширила бы
    принятую границу риска. Названная граница самого гарда (запрос без обоих
    заголовков пропускается) наследуется осознанно и записана в реестре угроз
    плана.

    ⚠️ КАНАЛ ОПРЕДЕЛЯЕТСЯ ПО САМОМУ АККАУНТУ, А НЕ ПО ПОЛЮ ФОРМЫ (T-06-RST1).
    Поле подделывается вместе с запросом; колонка в базе — нет. Перепутанный
    канал поднял бы контейнер чужого типа под идентификатором этого аккаунта.

    ⚠️ ПОРЯДОК ПРОВЕРОК НЕСУЩИЙ: кто пришёл → откуда → что просит. Неизвестный
    аккаунт и канал без своего контейнера отвергаются ДО обращения к демону,
    иначе отказ приходил бы от чужой службы и по чужой причине.
    """
    if not is_same_origin(request):
        # Чужому источнику причина отказа не сообщается: межсайтовый запрос не
        # имеет права узнать даже, существует ли такой аккаунт. Форма ответа —
        # та же, что у денежных форм проекта.
        return Response(status_code=403)

    location = "/admin/workers"

    account = await db.get(MessengerAccount, account_id)
    if account is None:
        logger.warning(
            "worker_restart_unknown_account",
            admin_user_id=admin.id,
            account_id=account_id,
        )
        return RedirectResponse(url=location, status_code=302)

    manager = WORKER_RESTART_MANAGERS.get(account.type)
    if manager is None:
        # Молчаливый успех здесь был бы ХУЖЕ отказа: администратор решил бы,
        # что починил, и перестал бы искать настоящую причину.
        logger.warning(
            "worker_restart_unsupported_channel",
            admin_user_id=admin.id,
            account_id=account.id,
            channel=account.type,
        )
        return RedirectResponse(
            url=f"{location}?error=no_container", status_code=302
        )

    try:
        # ⚠️ В ОТДЕЛЬНОМ ПОТОКЕ, А НЕ ПРЯМО В ЦИКЛЕ СОБЫТИЙ. Менеджер синхронен и
        # ходит по сети к демону: вызванный здесь напрямую, он заблокировал бы
        # весь веб-процесс на время подъёма контейнера — включая опрос этого же
        # подраздела у всех открытых вкладок.
        await run_in_threadpool(manager.start_container, account.id)
    except Exception as e:
        # Причина в журнал, слова — на экран из ЗАКРЫТОГО множества. Текст
        # исключения на экран не выходит: он несёт внутренние пути и ничего не
        # сообщает администратору.
        logger.warning(
            "worker_restart_failed",
            admin_user_id=admin.id,
            account_id=account.id,
            channel=account.type,
            error=str(e),
        )
        return RedirectResponse(
            url=f"{location}?error=restart_failed", status_code=302
        )

    # Привилегированная операция над ЧУЖОЙ сущностью обязана оставлять след, и
    # форма следа в проекте уже есть (`free_access_toggled`): именованный ключ,
    # оба идентификатора и то, ЧТО именно сделано.
    logger.info(
        "worker_restarted",
        admin_user_id=admin.id,
        account_id=account.id,
        channel=account.type,
    )
    return RedirectResponse(url=location, status_code=302)


@router.get("/queue", response_class=HTMLResponse)
async def admin_queue(
    request: Request,
    result: str | None = Query(None),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Подраздел «Очередь»: что ждёт отправки прямо сейчас по трём каналам.

    ⚠️ ЧТЕНИЕ НИЧЕГО НЕ СНИМАЕТ. Подраздел отвечает на вопрос «что ждёт
    отправки», и чтение, снимающее задачи, отняло бы у пользователей оплаченные
    рассылки просто оттого, что администратор открыл страницу. Отсутствие
    снимающих команд закреплено грепом по сервису, а не намерением.

    ⚠️ СОСТОЯНИЯ «В РАБОТЕ» ЗДЕСЬ НЕТ (D-15). У WA и MAX задача физически
    уходит из списка, когда воркер её берёт, и «в работе» пришлось бы
    синтезировать из heartbeat — то есть подавать догадку как факт. Кто
    работает сейчас, показывает подраздел «Воркеры» свежим heartbeat.

    ⚠️ НЕДОСТУПНЫЙ REDIS ОТВЕЧАЕТ ПЛАШКОЙ, А НЕ ПУСТОЙ ОЧЕРЕДЬЮ И НЕ ПЯТИСОТКОЙ.
    Пустая очередь и сломанный наблюдатель — разные состояния мира; слитые в
    одно, они сообщили бы «рассылать нечего» ровно тогда, когда очередь стоит и
    её не видно.
    """
    accounts = (
        (
            await db.execute(
                select(MessengerAccount).order_by(MessengerAccount.id)
            )
        )
        .scalars()
        .all()
    )

    now = datetime.now(timezone.utc)
    unavailable = False
    blocks = []
    for channel in QUEUE_CHANNELS:
        entries = []
        for account in (a for a in accounts if a.type == channel["key"]):
            page = await queue_page(channel["key"], account.id, QUEUE_READ_LIMIT)
            unavailable = unavailable or page.unavailable
            rows = queue_rows(page.tasks, channel["key"], now)
            entries.append(
                {
                    "account": account,
                    "rows": rows.rows,
                    "capped": rows.capped,
                    "total": page.total,
                    "unavailable": page.unavailable,
                    "unreadable": page.unreadable,
                }
            )
        blocks.append({**channel, "accounts": entries})

    # БЛОК КАНАЛА БРОКЕРА УСТРОЕН ИНАЧЕ, И ЭТО ОСОЗНАННО (D-14).
    #
    # ⚠️ ВЕЛИЧИНА ИЗМЕРЯЕТСЯ ПО ЖУРНАЛУ ОТПРАВОК, А НЕ ПО СОДЕРЖИМОМУ ОЧЕРЕДИ, И
    # ПОДПИСЬ ОБЯЗАНА НАЗЫВАТЬ ИМЕННО ЭТО. Возраст самой старой задачи лежит
    # внутри конверта брокера, читать который запрещено тем же решением;
    # подпись, позволяющая прочитать величину так, была бы измеренной на вид
    # выдумкой.
    #
    # ⚠️ ПРИ ПУСТОЙ ОЧЕРЕДИ ВЕЛИЧИНА НЕ СЧИТАЕТСЯ ВОВСЕ: время с последней
    # отправки на пустой очереди означает «работы не было», а не «работа стоит»,
    # и напечатанное оно тревожило бы администратора ровно там, где всё в
    # порядке.
    telegram_depth = await telegram_queue_depth()
    unavailable = unavailable or telegram_depth is None
    telegram_lag = None
    if telegram_depth:
        telegram_lag = telegram_lag_seconds(
            await last_send_at(db, messenger_type=QUEUE_TELEGRAM_CHANNEL), now
        )

    has_telegram_accounts = any(
        a.type == QUEUE_TELEGRAM_CHANNEL for a in accounts
    )
    has_rows = any(
        entry["rows"] for block in blocks for entry in block["accounts"]
    )

    drop_result = QUEUE_DROP_RESULTS.get(result or "")
    return templates.TemplateResponse(
        "admin/queue.html",
        {
            **_admin_context(request, admin, "queue"),
            "blocks": blocks,
            "telegram": {
                "depth": telegram_depth,
                "lag_sec": telegram_lag,
                "has_accounts": has_telegram_accounts,
            },
            "queue_row_cap": QUEUE_ROW_CAP,
            "redis_unavailable": unavailable,
            "has_rows": has_rows,
            "drop_result": drop_result,
        },
    )


@router.post("/queue/{account_id}/drop")
async def admin_drop_task(
    request: Request,
    account_id: int,
    task_id: str = Form(...),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Снять ОДНУ задачу из очереди аккаунта (D-17). Необратимо.

    ⚠️ ДЕЙСТВИЯ, СТИРАЮЩЕГО ОЧЕРЕДЬ ЦЕЛИКОМ, НЕТ НИ ЗДЕСЬ, НИ В РАЗМЕТКЕ. Одно
    нажатие уничтожило бы пачку чужих оплаченных рассылок без возможности
    восстановления: задачи существуют ТОЛЬКО в очереди, и восстановить их
    нечем. Симметрично D-11: лекарство от конкретного отказа, а не рубильник.
    Отсутствие закреплено отрицательным тестом.

    ⚠️ ФОРМА НЕСЁТ ТОЛЬКО ИДЕНТИФИКАТОР ЗАДАЧИ (T-06-DROP2). Точные байты
    удаляемого элемента сервер берёт из СВОЕГО чтения очереди: тело содержит
    текст чужого объявления и может быть большим, а доверять клиенту байты
    удаляемого не нужно вовсе.

    ⚠️ ГАРД ПРОИСХОЖДЕНИЯ СТОИТ ПЕРЕД ДЕЙСТВИЕМ И ОБЯЗАТЕЛЕН (T-06-DROP1).
    Аутентификация проекта идёт cookie, поэтому браузер приложит её к
    межсайтовой форме сам, и запрос со стороннего сайта неотличим от своего.

    ⚠️ КАНАЛ ОПРЕДЕЛЯЕТСЯ ПО САМОМУ АККАУНТУ, А НЕ ПО ПОЛЮ ФОРМЫ. Поле
    подделывается вместе с запросом; колонка в базе — нет.

    ⚠️ ЗАПИСИ В ЖУРНАЛ ОТПРАВОК НЕ ДЕЛАЕТСЯ (D-18): журнал отражает совершённые
    попытки отправки, а снятая задача попытки не совершила. След остаётся
    именованной строкой журнала приложения и виден в подразделе логов.
    """
    if not is_same_origin(request):
        # Чужому источнику причина отказа не сообщается: межсайтовый запрос не
        # имеет права узнать даже, существует ли такой аккаунт.
        return Response(status_code=403)

    location = "/admin/queue"

    account = await db.get(MessengerAccount, account_id)
    known = {channel["key"] for channel in QUEUE_CHANNELS}
    if account is None or account.type not in known:
        # Молчаливый успех был бы хуже отказа: администратор решил бы, что снял
        # отправку, которой на самом деле не касался.
        logger.warning(
            "queue_task_drop_unsupported",
            admin_user_id=admin.id,
            account_id=account_id,
            channel=account.type if account else None,
        )
        return RedirectResponse(
            url=f"{location}?result=unknown_account", status_code=302
        )

    outcome = await drop_task(
        account.type, account.id, task_id, QUEUE_READ_LIMIT
    )

    if outcome != DROP_REMOVED:
        logger.warning(
            "queue_task_drop_failed",
            admin_user_id=admin.id,
            account_id=account.id,
            channel=account.type,
            task_id=task_id,
            outcome=outcome,
        )
        return RedirectResponse(
            url=f"{location}?result={outcome}", status_code=302
        )

    # Привилегированная операция над ЧУЖОЙ сущностью обязана оставлять след, и
    # форма следа в проекте уже есть (`worker_restarted`): именованный ключ, все
    # идентификаторы и то, ЧТО именно сделано. Без записи снятие неотличимо от
    # того, что его не было.
    logger.info(
        "queue_task_dropped",
        admin_user_id=admin.id,
        account_id=account.id,
        channel=account.type,
        task_id=task_id,
    )
    return RedirectResponse(
        url=f"{location}?result={DROP_REMOVED}", status_code=302
    )


@router.get("/logs", response_class=HTMLResponse)
async def admin_logs(
    request: Request,
    level: str | None = Query(None),
    source: str | None = Query(None),
    window: str | None = Query(None),
    q: str | None = Query(None),
    admin: User = Depends(require_admin),
):
    """Подраздел «Логи»: операционный срез журналов приложения и воркеров.

    ⚠️ ИСТОЧНИК ЛОГОВ ОПЦИОНАЛЕН, И ЕГО ОТСУТСТВИЕ — ШТАТНАЯ ВЕТКА (D-28).
    Мониторинг не поднимается боевыми командами запуска и выката: это решение
    проекта, а не недоделка. Поэтому недоступность приходит ОТДЕЛЬНЫМ полем
    результата и рисуется ПЛАШКОЙ с причиной и командой подъёма — не пустым
    списком. Пустой список здесь читается как «ошибок нет», то есть отвечает на
    вопрос, ради которого администратор в подраздел и пришёл, и отвечает
    неправдой.

    ⚠️ ТРИ СОСТОЯНИЯ, А НЕ ДВА, И РАЗМЕТКА РАЗЛИЧАЕТ ВСЕ ТРИ: пустая выдача при
    живом источнике, недоступный источник, сработавший потолок. Ни одно из них
    не выводится из длины перечня строк.

    ⚠️ ОПРОСА ЗДЕСЬ НЕТ, ОБНОВЛЕНИЕ ИДЁТ КНОПКОЙ (D-29). Администратор читает и
    ищет глазами, а лента, прыгающая под курсором, мешает; вдобавок каждый
    запрос — поход во внешний источник по сети, а не чтение из памяти.

    ⚠️ ЗНАЧЕНИЯ ТРЁХ ОСЕЙ САНИРУЮТСЯ ЗАМКНУТЫМ МНОЖЕСТВОМ ИЗ ОБЪЯВЛЕННЫХ
    СЛОВАРЕЙ (T-06-LOG3), а текст поиска экранируется сборщиком запроса: это
    единственный вход фазы, уходящий в чужой язык запросов (T-06-LQL).
    """
    level = clean_level(level)
    source = clean_source(source)
    window_key = clean_window(window)
    text = (q or "").strip()

    result = await query_range(
        build_logql(level, source, text), LOG_WINDOWS[window_key].delta
    )

    # Действующие значения осей для сборки адресов чипсов: переключение ОДНОЙ
    # оси обязано сохранить остальные, иначе выбор уровня молча сбросил бы окно
    # и текст поиска — при исправном на вид экране.
    filter_params = {"window": window_key}
    if level:
        filter_params["level"] = level
    if source:
        filter_params["source"] = source
    if text:
        filter_params["q"] = text

    return templates.TemplateResponse(
        "admin/logs.html",
        {
            **_admin_context(request, admin, "logs"),
            # Три поля результата приезжают ПОРОЗНЬ, потому что разметка
            # различает три случая. Признак, выведенный из длины списка, рано
            # или поздно ошибётся — и ошибётся молча.
            "log_lines": result.lines,
            "log_capped": result.capped,
            "log_unavailable": result.unavailable,
            "log_line_cap": LOG_LINE_CAP,
            "level_chips": LEVEL_CHIP_OPTIONS,
            "source_chips": LOG_SOURCES,
            "window_chips": LOG_WINDOW_CHIPS,
            "filter_level": level,
            "filter_source": source,
            "filter_window": window_key,
            "filter_text": text,
            "filter_params": filter_params,
        },
    )


@router.get("/payments", response_class=HTMLResponse)
async def admin_payments(
    request: Request,
    status: str | None = Query(default=None),
    period: str | None = Query(default=None),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Подраздел «Платежи»: две величины, журнал с двумя осями и честный потолок.

    ⚠️ ВЫРУЧКА БЕРЁТСЯ ТЕМ ЖЕ ПУТЁМ, ЧТО И НА «ОБЗОРЕ» — счётом платящих по трём
    условиям и умножением его на цену доступа (D-38). Второй счёт рядом дал бы
    два разных числа об одной величине на двух экранах одной админки, и узналось
    бы это по жалобе, что выручка на обзоре не сходится с выручкой в платежах.
    Агрегатов обработчик не строит вовсе — они живут в прикладном слое, и это
    машинное свойство модуля
    (`test_the_admin_pages_module_builds_no_aggregate_over_the_send_journal`).

    ⚠️ ЗНАЧЕНИЯ ОСЕЙ САНИРУЮТСЯ ЗДЕСЬ ТОЖЕ, ХОТЯ МОДУЛЬ САНИРУЕТ ИХ САМ. Модуль
    отсекает мусор для ЗАПРОСА; здесь отсечка нужна для РАЗМЕТКИ: неотсечённое
    значение доехало бы до чипсов как активное, и администратор увидел бы
    подсвеченный фильтр, которого не задавал и который ничего не отбирает.
    Отсекает ОБЩАЯ функция проекта, а не своя копия (`clean_choice`).

    ⚠️ МОМЕНТ СНИМАЕТСЯ ОДИН НА ВЕСЬ ЗАПРОС — и для отбора платящих, и для окна
    ушедших, и для отсечки периода. Посчитанные от разных моментов, три величины
    разъехались бы на границе суток.
    """
    status = clean_choice(status, PAYMENT_STATUS_VALUES)
    period = clean_choice(period, PAYMENT_PERIOD_VALUES)

    now = datetime.now(timezone.utc)
    paying = await paying_total(db, now=now)
    ledger = await payment_ledger(db, status=status, period=period, now=now)

    filter_params = {
        key: value
        for key, value in (("status", status), ("period", period))
        if value
    }

    return templates.TemplateResponse(
        "admin/payments.html",
        {
            **_admin_context(request, admin, "payments"),
            # ⚠️ ДВЕ ВЕЛИЧИНЫ, И РОВНО ДВЕ (D-41). Средней величины платежа нет:
            # при единственной цене она тождественно равна ей. Доли ушедших нет:
            # подписка одна на пользователя, дата окончания сдвигается при
            # продлении, истории продлений строка не хранит — доля из имеющегося
            # была бы числом без определения.
            "mrr": monthly_revenue(paying, settings.subscription_price),
            "lapsed": await expired_not_renewed(db, now=now),
            # Окно уезжает в подпись ЗНАЧЕНИЕМ, а не выписывается в шаблоне: копия
            # числа в копирайте разошлась бы с окном молча.
            "expired_lookback_days": EXPIRED_LOOKBACK_DAYS,
            "payments": ledger.rows,
            "payments_total": ledger.total,
            "payments_cap": ledger.cap,
            "payments_truncated": ledger.truncated,
            "status_chips": PAYMENT_STATUS_CHIPS,
            "period_chips": PAYMENT_PERIOD_CHIPS,
            "filter_status": status,
            "filter_period": period,
            "filter_params": filter_params,
        },
    )


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def admin_user_detail(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    accounts_result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == target_user.id
        )
    )
    accounts = list(accounts_result.scalars().all())

    counts = await user_card_counts(db, target_user.id)

    # Плитка доступа читает ТУ ЖЕ строку и ТОТ ЖЕ предикат, что список и продукт.
    subscriptions = await _active_subscriptions_by_user(db, [target_user.id])
    access = _access_view(
        subscriptions.get(target_user.id), datetime.now(timezone.utc)
    )

    return templates.TemplateResponse(
        "admin/user_detail.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "target_user": target_user,
            "accounts": accounts,
            "ads_count": counts.ads,
            "groups_count": counts.groups,
            # ⚠️ КЛЮЧ НАЗВАН `target_access`, А НЕ `access`. Шелл кладёт в
            # контекст СВОЙ словарь доступа — АДМИНИСТРАТОРА, который смотрит на
            # эту карточку, — и совпадение имён напечатало бы срок админа на
            # карточке чужого человека. Одно имя на две разные учётные записи —
            # ровно тот класс ошибки, который выглядит исправным на экране
            # админа и врёт про всех остальных.
            "target_access": access,
        },
    )


@router.get("/users/{user_id}/history", response_class=HTMLResponse)
async def admin_user_history(
    request: Request,
    user_id: int,
    status: str | None = Query(default=None),
    messenger: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    # Размер страницы — ТОТ ЖЕ, что у пользовательской истории, и берётся у неё
    # же. Своя копия числа здесь и в сентинелях разметки разъехалась бы с
    # `next_offset` молча: вторая страница выдачи начала бы перекрываться с
    # первой или пропускать записи, а экран остался бы исправным на вид.
    page_size = PAGE_SIZE

    # ОТСЕЧКА НЕИЗВЕСТНЫХ ЗНАЧЕНИЙ ОСЕЙ — ТА ЖЕ, ЧТО У ПОЛЬЗОВАТЕЛЬСКИХ
    # МАРШРУТОВ. Значения приезжают строкой запроса — из ссылки, закладки или
    # чужого сообщения. Без отсечки мусорное значение давало бы пустой список,
    # в котором НИ ОДИН чипс не отмечен активным, а сырая строка уезжала бы в
    # `filter_params` — то есть в сентинель прокрутки и в контекст шаблона как
    # действующий фильтр. Инъекции здесь нет (значения связываются параметрами),
    # но экран получается нечитаемым ровно так же, как получался бы у
    # пользователя, — а админка смотрит на ТУ ЖЕ историю.
    status = clean_choice(status, STATUS_VALUES)
    messenger = clean_choice(messenger, MESSENGER_VALUES)
    period = clean_choice(period, PERIOD_VALUES)
    account_id_int = parse_account_id(account_id)
    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user_id)
    )
    # Владелец записей — target_user, но «сегодня» отсчитывается от полуночи
    # ТОГО, КТО СМОТРИТ: границу дня задаёт часовой пояс читателя экрана.
    query = apply_history_filters(
        query,
        status=status,
        messenger_type=messenger,
        account_id=account_id_int,
        period=period,
        user=admin,
    )
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(page_size + 1)

    result = await db.execute(query)
    rows = list(result.all())

    has_next = len(rows) > page_size
    rows = rows[:page_size]

    logs = [
        {
            "id": r.id,
            "ad_title": r.ad_title or "—",
            # СНАПШОТА ТЕЛА ОБЪЯВЛЕНИЯ В СТРОКЕ СПИСКА НЕТ. Ни `ad_text`, ни
            # `ad_images` карточка списка не рисует — их читает только экран
            # записи, и он получает ORM-сущность, а не этот словарь. Пока они
            # тут лежали, каждый рендер списка и каждый тик бесконечной
            # прокрутки поднимал в память до тридцати полных снимков тела
            # объявления (`ad_text` — Text, длина не ограничена) ради контекста,
            # который их выбрасывает.
            "group_name": r.group_name or "—",
            "group_external_id": group.group_external_id if group else None,
            "account_id": group.account_id if group else None,
            "task_id": r.task_id,
            "status": r.status,
            "messenger_type": r.messenger_type,
            "error_message": r.error_message,
            "sent_at": r.sent_at,
        }
        for r, group in rows
    ]
    accounts_result = await db.execute(
        select(MessengerAccount).where(MessengerAccount.user_id == user_id)
    )
    all_accounts = accounts_result.scalars().all()
    filter_params = history_filter_params(status, messenger, account_id_int, period)

    return templates.TemplateResponse(
        "admin/user_history.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "target_user": target_user,
            "logs": logs,
            "all_accounts": all_accounts,
            "status_filter": status,
            "filter_messenger": messenger,
            "filter_account_id": account_id_int,
            "filter_period": period,
            "filter_params": filter_params,
            "offset": offset,
            "page_size": page_size,
            "has_next": has_next,
            "next_offset": offset + len(logs),
            "detail_base_path": f"/admin/users/{user_id}/history",
        },
    )


@router.get("/users/{user_id}/history/partial", response_class=HTMLResponse)
async def admin_user_history_partial(
    request: Request,
    user_id: int,
    status: str | None = Query(default=None),
    messenger: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)
    # Отсечка стоит и здесь: паршал прокрутки — ВТОРОЙ вход на те же оси, и
    # значение приезжает к нему из адреса сентинеля. Пропущенная тут, она
    # позволила бы мусору дожить до второй страницы выдачи.
    status = clean_choice(status, STATUS_VALUES)
    messenger = clean_choice(messenger, MESSENGER_VALUES)
    period = clean_choice(period, PERIOD_VALUES)
    account_id_int = parse_account_id(account_id)
    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user_id)
    )
    # Владелец записей — target_user, но «сегодня» отсчитывается от полуночи
    # ТОГО, КТО СМОТРИТ: границу дня задаёт часовой пояс читателя экрана.
    query = apply_history_filters(
        query,
        status=status,
        messenger_type=messenger,
        account_id=account_id_int,
        period=period,
        user=admin,
    )
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(limit + 1)
    result = await db.execute(query)
    rows = list(result.all())
    has_next = len(rows) > limit
    logs = [
        {
            "id": r.id,
            "ad_title": r.ad_title or "—",
            # СНАПШОТА ТЕЛА ОБЪЯВЛЕНИЯ В СТРОКЕ СПИСКА НЕТ. Ни `ad_text`, ни
            # `ad_images` карточка списка не рисует — их читает только экран
            # записи, и он получает ORM-сущность, а не этот словарь. Пока они
            # тут лежали, каждый рендер списка и каждый тик бесконечной
            # прокрутки поднимал в память до тридцати полных снимков тела
            # объявления (`ad_text` — Text, длина не ограничена) ради контекста,
            # который их выбрасывает.
            "group_name": r.group_name or "—",
            "group_external_id": group.group_external_id if group else None,
            "account_id": group.account_id if group else None,
            "task_id": r.task_id,
            "status": r.status,
            "messenger_type": r.messenger_type,
            "error_message": r.error_message,
            "sent_at": r.sent_at,
        }
        for r, group in rows[:limit]
    ]
    filter_params = history_filter_params(status, messenger, account_id_int, period)
    return templates.TemplateResponse(
        "admin/history_partial_cards.html",
        {
            "request": request,
            "user": admin,
            "target_user": target_user,
            "logs": logs,
            "has_next": has_next,
            "next_offset": offset + limit,
            # Размер страницы уезжает в сентинель из контекста — тем же
            # значением, которым выбрана ЭТА порция.
            "page_size": limit,
            "status_filter": status,
            "filter_messenger": messenger,
            "filter_account_id": account_id_int,
            "filter_period": period,
            "filter_params": filter_params,
            "detail_base_path": f"/admin/users/{user_id}/history",
        },
    )


@router.get("/users/{user_id}/history/{log_id}", response_class=HTMLResponse)
async def admin_user_history_detail(
    request: Request,
    user_id: int,
    log_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    log = await db.get(SendLog, log_id)
    if not log or log.user_id != user_id:
        return RedirectResponse(url=f"/admin/users/{user_id}/history", status_code=302)

    group = await db.get(Group, log.group_id) if log.group_id else None

    return templates.TemplateResponse(
        "admin/user_history_detail.html",
        {
            "request": request,
            "user": admin,
            "is_admin": True,
            "active_page": "admin",
            "target_user": target_user,
            "log": log,
            "group": group,
        },
    )


@router.post("/users/{user_id}/unlimited")
async def admin_toggle_free_access(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Выдать или снять БЕСПЛАТНЫЙ ДОСТУП пользователю (D-E, критерий 5 фазы).

    ⚠️ МАРШРУТ ПЕРЕИСПОЛЬЗОВАН, А НЕ ЗАВЕДЁН ЗАНОВО, И ПРЕДМЕТ У НЕГО СМЕНИЛСЯ.
    Прежний тумблер писал признак безлимита на таблице ОСТАТКА СООБЩЕНИЙ, и
    ревизия `0020` уронила таблицу под ним; право администратора открыть доступ
    бесплатно при этом не отменялось — оно переехало на строку подписки. Имя
    снятой колонки здесь не набирается: оно стоит под отрицательным греп-гейтом
    `tests/test_application/test_no_metering_remains.py`, а гейт читает
    ИСХОДНИКИ — объяснение, набранное запрещённым именем, уронило бы собственный
    запрет (находка плана 05.1-04). Адрес, метод и форма ответа сохранены
    дословно: меняются хранилище и подписи кнопок.

    ⚠️ ПРАВА НЕ ОСЛАБЛЕНЫ: маршрут остаётся за `require_admin`. Это
    привилегированная операция над ЧУЖОЙ учётной записью, раздающая платное
    благо, и она уходит в журнал ИМЕНОВАННЫМ ключом с обоими идентификаторами и
    НОВЫМ значением признака (T-05.1-05). Одно без другого бесполезно: проверка
    прав отвечает «кто имел право», журнал — «кто и кому это сделал», а без
    нового значения выдача неотличима от отзыва.

    ⚠️ КЭШ ВЕРДИКТА СБРАСЫВАЕТСЯ В ОБЕ СТОРОНЫ (T-05.1-04). Тумблер пишет РОВНО
    ту величину, из которой считается кэшируемый вердикт `check_access`, и без
    сброса выданная льгота до минуты не работала бы, а СНЯТАЯ — до минуты
    продолжала бы работать. Второе хуже: это платный ресурс, который продукт уже
    перестал выдавать. У прежнего тумблера сбрасывать было нечего — он писал не
    ту величину, которую кэш хранит.

    ⚠️ ПОЛЬЗОВАТЕЛЬ БЕЗ АКТИВНОЙ СТРОКИ ПОДПИСКИ НЕ ПОЛУЧАЕТ ПЯТИСОТКИ, И СТРОКА
    ЗДЕСЬ НЕ ЗАВОДИТСЯ. Ревизия `0020` населила строкой всех существующих
    пользователей (популяция П-о-1), поэтому в проде такого состояния быть не
    должно; но «не должно» — не то же, что «не бывает», и админский путь не имеет
    права падать на остатке. Заводить строку ПРЯМО В ТУМБЛЕРЕ нельзя: срок
    доступа — денежная величина, и выдумывать её в обход единственного писателя
    (подтверждённого уведомления ЮKassa) значило бы подарить месяц молча. Ответ —
    тот же редирект на карточку, где администратор увидит закрытый доступ и
    отсутствие льготы. Закреплено
    `test_the_free_access_toggle_survives_a_user_without_a_subscription_row`.

    ПОДТВЕРЖДЕНИЯ НЕТ НАМЕРЕННО (UI-контракт E5). Тумблер обратим, данных не
    разрушает, и у соседних админских тумблеров подтверждения тоже нет; завести
    его здесь значило бы сделать исключение из общего поведения админки.
    """
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    location = f"/admin/users/{user_id}"

    subscription = (
        await db.execute(
            select(Subscription).where(
                Subscription.user_id == target_user.id,
                Subscription.is_active.is_(True),
            )
        )
    ).scalar_one_or_none()

    if subscription is None:
        # Отказ НАЗВАН в журнале, а не проглочен: администратор нажал кнопку и
        # получил ту же страницу, и без записи это читалось бы как «кнопка
        # сломана» — ровно тот дефект, ради которого раздел оплаты завёл
        # закрытое множество причин отказа.
        logger.warning(
            "free_access_toggle_without_subscription",
            admin_user_id=admin.id,
            target_user_id=target_user.id,
        )
        return RedirectResponse(url=location, status_code=302)

    subscription.has_free_access = not subscription.has_free_access
    await db.commit()

    logger.info(
        "free_access_toggled",
        admin_user_id=admin.id,
        target_user_id=target_user.id,
        has_free_access=subscription.has_free_access,
    )

    await invalidate_access_cache(target_user.id)

    return RedirectResponse(url=location, status_code=302)


@router.post("/users/{user_id}/block")
async def admin_toggle_block(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    # Don't allow admin to block themselves
    if target_user.id == admin.id:
        return RedirectResponse(
            url=f"/admin/users/{user_id}", status_code=302
        )

    target_user.is_blocked = not target_user.is_blocked
    await db.commit()

    return RedirectResponse(
        url=f"/admin/users/{user_id}", status_code=302
    )


@router.post("/users/{user_id}/delete")
async def admin_delete_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target_user = await db.get(User, user_id)
    if not target_user:
        return RedirectResponse(url="/admin/users", status_code=302)

    # Don't allow admin to delete themselves
    if target_user.id == admin.id:
        return RedirectResponse(
            url=f"/admin/users/{user_id}", status_code=302
        )

    await db.delete(target_user)
    await db.commit()

    return RedirectResponse(url="/admin/users", status_code=302)
