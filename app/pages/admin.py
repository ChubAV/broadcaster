from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.concurrency import run_in_threadpool
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings, require_admin
from app.application.analytics.send_analytics import (
    apply_history_filters,
    history_filter_params,
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
from app.models.ad import Ad
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.models.subscription import Subscription
from app.pages.common import is_same_origin, templates
from app.repositories.user import UserRepository
from app.services import max_container_manager, wa_container_manager
from app.services.billing_cache import invalidate_access_cache
from app.services.ops_state import (
    INFRA_BEAT,
    INFRA_WORKER_DEFAULT,
    INFRA_WORKER_TELEGRAM,
    infra_heartbeat_key,
    infra_liveness,
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


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user_repo = UserRepository(db)
    total_users = await user_repo.count_all()

    total_accounts = (
        await db.execute(select(func.count(MessengerAccount.id)))
    ).scalar() or 0

    total_active_accounts = (
        await db.execute(
            select(func.count(MessengerAccount.id)).where(
                MessengerAccount.status == "active"
            )
        )
    ).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    sends_today = (
        await db.execute(
            select(func.count(SendLog.id)).where(
                SendLog.sent_at >= today_start
            )
        )
    ).scalar() or 0

    # ПЯТОГО ПОКАЗАТЕЛЯ ЗДЕСЬ НЕТ, И ЗАМЕНА ЕМУ НЕ ЗАВЕДЕНА НАМЕРЕННО (A-8).
    # Он суммировал остатки сообщений по всем пользователям — величину, которой
    # в продукте больше не существует. Подраздел обзора принадлежит фазе 6, и
    # показатель, заведённый здесь, будет ею переопределён: это работа под
    # снос. Раскладка не страдает — сетка плиток автозаполняемая, четыре плитки
    # переливаются без дыры.

    return templates.TemplateResponse(
        "admin/overview.html",
        {
            **_admin_context(request, admin, "overview"),
            "stats": {
                "total_users": total_users,
                "total_accounts": total_accounts,
                "active_accounts": total_active_accounts,
                "sends_today": sends_today,
            },
        },
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    q: str = "",
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user_repo = UserRepository(db)
    if q:
        users = await user_repo.search_users(q)
    else:
        users = await user_repo.get_all_users()

    # СПИСОК НЕ ХОДИТ В БАЗУ ЗА КАЖДЫМ ПОЛЬЗОВАТЕЛЕМ. Колонка доступа собирается
    # ОДНИМ запросом на всю страницу, а момент времени снимается ОДИН на весь
    # список: посчитанные от разных `now`, вердикт и остаток дней разъехались бы
    # на границе суток у соседних строк одной и той же таблицы (T-05.1-19).
    now = datetime.now(timezone.utc)
    subscriptions = await _active_subscriptions_by_user(db, [u.id for u in users])
    user_data = [
        {"user": u, "access": _access_view(subscriptions.get(u.id), now)}
        for u in users
    ]

    return templates.TemplateResponse(
        "admin/users.html",
        {
            **_admin_context(request, admin, "users"),
            "users": user_data,
            "search_query": q,
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
    admin: User = Depends(require_admin),
):
    """Каркас подраздела «Очередь». Содержимое приносит план 06-07."""
    return templates.TemplateResponse(
        "admin/queue.html", _admin_context(request, admin, "queue")
    )


@router.get("/logs", response_class=HTMLResponse)
async def admin_logs(
    request: Request,
    admin: User = Depends(require_admin),
):
    """Каркас подраздела «Логи». Содержимое приносит план 06-08."""
    return templates.TemplateResponse(
        "admin/logs.html", _admin_context(request, admin, "logs")
    )


@router.get("/payments", response_class=HTMLResponse)
async def admin_payments(
    request: Request,
    admin: User = Depends(require_admin),
):
    """Каркас подраздела «Платежи». Содержимое приносит план 06-11."""
    return templates.TemplateResponse(
        "admin/payments.html", _admin_context(request, admin, "payments")
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

    ads_count = (
        await db.execute(
            select(func.count(Ad.id)).where(Ad.user_id == target_user.id)
        )
    ).scalar() or 0

    groups_count = (
        await db.execute(
            select(func.count(Group.id)).where(
                Group.user_id == target_user.id
            )
        )
    ).scalar() or 0

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
            "ads_count": ads_count,
            "groups_count": groups_count,
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
