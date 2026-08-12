from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import AD_STATUS_DRAFT, AD_STATUS_PUBLISHED
from app.models.ad import Ad
from app.models.balance_transaction import BalanceTransaction
from app.models.message_balance import MessageBalance
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.subscription import Subscription
from app.models.user import User
from app.services.auth_service import decode_access_token
from app.services.s3 import get_image_url

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
_static_dir = Path(__file__).resolve().parent.parent / "static"
templates = Jinja2Templates(directory=str(_templates_dir))

# Глобалы изображений привязываются к настройкам ПРИЛОЖЕНИЯ, а не к окружению
# процесса (D-21). Раньше все три вызывали get_settings() — то есть собирали
# Settings() из `.env` рабочего каталога в обход create_app(settings=...) и
# dependency_overrides. Следствий было два: базовый URL приезжал из окружения
# мимо подменённых настроек, а без файла `.env` рендер /ads/new падал
# ValidationError на обязательных полях (T-02-02).
#
# Почему не параметрическая инъекция по образцу format_datetime_for_user.
# ad_card — это МАКРОС (app/templates/ads/includes/ad_card.html:25), а
# импортированным макросам Jinja контекст вызывающего не передаёт. Передача
# базового URL параметром потребовала бы менять сигнатуру макроса и все его
# вызовы в ads/list.html и ads/partial_cards.html, то есть трогать разметку
# списка ради починки настроек. Привязка на уровне create_app чинит ровно
# заявленный дефект и не касается ни одного шаблона.
#
# ОГРАНИЧЕНИЕ: templates — модульный синглтон, общий на процесс, поэтому
# привязка глобальна и последний create_app выигрывает. Для одного приложения
# на процесс (бой) и для теста, создающего своё приложение в фикстуре, этого
# достаточно. Разведение окружений Jinja по приложениям — архитектурная
# правка, выходящая за границы этого плана.
def _resolve_image_url(key: str, s3_public_url: str) -> str:
    """Return key as-is if it's already a full URL, else build S3 URL."""
    if not key:
        return ""
    if key.startswith("http://") or key.startswith("https://"):
        return key
    return get_image_url(key, s3_public_url)


def _bind_image_url_globals(s3_public_url: str) -> None:
    """Register the three image globals closed over an explicit base URL."""
    templates.env.globals["get_image_url"] = lambda key: get_image_url(key, s3_public_url)
    templates.env.globals["resolve_image_url"] = lambda key: _resolve_image_url(key, s3_public_url)
    templates.env.globals["s3_public_url"] = lambda: s3_public_url


def bind_image_url_globals(settings: Settings) -> None:
    """Bind image template globals to the settings the app actually owns.

    Вызывается из create_app (app/main.py) сразу после разрешения settings.
    """
    _bind_image_url_globals(settings.s3_public_url)


# Безопасный дефолт на импорте: имена существуют с пустым базовым URL, и НИ
# ОДНОГО конструирования Settings на импорте модуля не происходит.
_bind_image_url_globals("")


def _compute_asset_version() -> str:
    """Return a cache-busting suffix for /static links.

    Хешей в именах файлов нет и build-шаг запрещён (D-02), поэтому версия
    берётся от времени изменения app.css и считается один раз при импорте.
    """
    try:
        return str(int((_static_dir / "css" / "app.css").stat().st_mtime))
    except OSError:
        return "dev"


templates.env.globals["asset_version"] = _compute_asset_version()


# Состояние объявления доезжает до шаблонов ГЛОБАЛОМ, по образцу nav_items.
# Карточка объявления — макрос (app/templates/ads/includes/ad_card.html:25), а
# импортированным макросам Jinja контекст вызывающего не передаёт: параметром
# значение пришлось бы протащить через сигнатуру макроса и оба его вызова.
# Литерал, выписанный в шаблоне вручную, лишил бы app/constants.py статуса
# единственного источника — разъехавшись с моделью, он показывал бы
# «Опубликовано» тому, что планировщик не отправляет.
# Конструирования Settings здесь не происходит: значения — модульные константы.
templates.env.globals["AD_STATUS_DRAFT"] = AD_STATUS_DRAFT
templates.env.globals["AD_STATUS_PUBLISHED"] = AD_STATUS_PUBLISHED


# Состав навигации по D-11. Список выписан ОДИН раз и используется и в
# боковом меню (data-nav), и в нижних табах (data-tabs) — иначе переименования
# пришлось бы править в трёх местах, как было в старом шелле.
# «Группы» сохраняются до Фазы 3: экран групп аккаунта появится только там,
# и без пункта работающий раздел стал бы недостижим.
NAV_ITEMS: list[dict] = [
    {"key": "dashboard", "label": "Дашборд", "href": "/dashboard", "count_key": None},
    {"key": "accounts", "label": "Аккаунты", "href": "/accounts", "count_key": "accounts"},
    {"key": "groups", "label": "Группы", "href": "/groups", "count_key": None},
    {"key": "ads", "label": "Объявления", "href": "/ads", "count_key": "ads"},
    {"key": "schedules", "label": "Расписания", "href": "/schedules", "count_key": "schedules"},
    {"key": "history", "label": "История", "href": "/history", "count_key": "history"},
    {"key": "billing", "label": "Тарифы", "href": "/billing", "count_key": None},
    {"key": "profile", "label": "Профиль", "href": "/profile", "count_key": None},
]

ADMIN_NAV_ITEM: dict = {"key": "admin", "label": "Админ-панель", "href": "/admin", "tag": "SYS"}


def nav_label(active_page: str | None) -> str:
    """Return the visible section name for an active_page key."""
    for item in NAV_ITEMS:
        if item["key"] == active_page:
            return item["label"]
    if active_page == ADMIN_NAV_ITEM["key"]:
        return ADMIN_NAV_ITEM["label"]
    return "Broadcaster"


templates.env.globals["nav_items"] = NAV_ITEMS
templates.env.globals["admin_nav_item"] = ADMIN_NAV_ITEM
templates.env.globals["nav_label"] = nav_label


def _get_timezone_for_user(user: User | None) -> ZoneInfo:
    """Return ZoneInfo for user's timezone or UTC as fallback."""
    tz_name = "UTC"
    if user and getattr(user, "timezone", None):
        try:
            tz_name = user.timezone
            return ZoneInfo(tz_name)
        except Exception:
            tz_name = "UTC"
    return ZoneInfo(tz_name)


def format_datetime_for_user(
    value: datetime | None,
    user: User | None,
    fmt: str = "%Y-%m-%d %H:%M",
) -> str:
    """Format datetime in user's timezone for display."""
    if value is None:
        return ""
    # Если дата без tzinfo — считаем, что она в UTC
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    tz = _get_timezone_for_user(user)
    local = value.astimezone(tz)
    return local.strftime(fmt)


templates.env.globals["format_datetime_for_user"] = format_datetime_for_user


def plural_ru(count: int, one: str, few: str, many: str) -> str:
    """Return the Russian noun form matching `count`.

    Общего хелпера склонений в проекте не было: единственный случай был решён
    конкатенацией одной формы (`sched_card.html`). Линейка счётчика экрана
    групп обязана печатать «1 активная из 1 группы», а не «1 активных из 1
    групп» (UI-SPEC §Copywriting Contract, E3 zero-one-many), поэтому форма
    выбирается по числу, а не выписывается в разметке.

    Хелпер возвращает ТОЛЬКО форму слова и ничего не форматирует: число рядом с
    ней ставит вызывающий шаблон. Так один и тот же хелпер обслуживает и
    «5 активных», и «в 3 расписаниях», где число стоит в разных местах строки.
    """
    tail = abs(int(count)) % 100
    if 11 <= tail <= 14:
        return many
    tail %= 10
    if tail == 1:
        return one
    if 2 <= tail <= 4:
        return few
    return many


templates.env.globals["plural_ru"] = plural_ru


async def get_user_from_cookie(
    request: Request, db: AsyncSession, settings: Settings
) -> User | None:
    """Read JWT from httpOnly cookie and return the User, or None."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token, settings.secret_key)
    if not payload:
        return None
    user = await db.get(User, payload["sub"])
    if user and user.is_blocked:
        return None
    return user


def check_is_admin(user: User | None, settings: Settings) -> bool:
    """Check if user is admin."""
    if not user or not settings.admin_email:
        return False
    return user.email == settings.admin_email


async def get_shell_context(db: AsyncSession, user: User | None) -> dict:
    """Collect live shell data: nav counts, plan quota and messenger sessions.

    Публичный контракт живых данных шелла (D-09/D-19). Фаза 4 (DASH-05) и
    Фаза 6 переиспользуют его, а не пишут своё чтение.

    Ключи sessions_online / sessions_total измеряют состояние СЕССИИ
    мессенджера (MessengerAccount.status в БД), а не состояние
    Docker-контейнера. Перечисление контейнеров воркеров здесь не
    вызывается ни при каких условиях: это синхронный Docker SDK, он
    блокирует event loop на рендере каждой страницы, а в тестах сокет
    Docker недоступен.
    """
    if user is None:
        return {}

    # Один round-trip на все шесть счётчиков: скалярные подзапросы без FROM.
    counts = (
        await db.execute(
            select(
                select(func.count())
                .select_from(Ad)
                .where(Ad.user_id == user.id)
                .scalar_subquery()
                .label("ads"),
                select(func.count())
                .select_from(MessengerAccount)
                .where(MessengerAccount.user_id == user.id)
                .scalar_subquery()
                .label("accounts"),
                # У Schedule нет user_id — принадлежность идёт через Ad,
                # как во всех запросах app/pages/schedules.py.
                select(func.count())
                .select_from(Schedule)
                .join(Ad, Schedule.ad_id == Ad.id)
                .where(Ad.user_id == user.id)
                .scalar_subquery()
                .label("schedules"),
                select(func.count())
                .select_from(SendLog)
                .where(SendLog.user_id == user.id)
                .scalar_subquery()
                .label("history"),
                select(func.count())
                .select_from(MessengerAccount)
                .where(
                    MessengerAccount.user_id == user.id,
                    MessengerAccount.status == "active",
                )
                .scalar_subquery()
                .label("sessions_online"),
            )
        )
    ).one()

    subscription = (
        await db.execute(
            select(Subscription)
            .where(Subscription.user_id == user.id, Subscription.is_active.is_(True))
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    # Чтение без записи: get_or_create_balance создаёт строку и делает flush,
    # а рендер страницы не должен ничего писать в БД.
    balance = (
        await db.execute(select(MessageBalance).where(MessageBalance.user_id == user.id))
    ).scalar_one_or_none()
    remaining = max(balance.balance, 0) if balance else 0
    is_unlimited = bool(balance.is_unlimited) if balance else False
    period_start = balance.free_balance_reset_at if balance else None

    # Израсходовано за текущий период — по журналу списаний, а не оценкой.
    used_stmt = select(func.coalesce(func.sum(-BalanceTransaction.amount), 0)).where(
        BalanceTransaction.user_id == user.id,
        BalanceTransaction.amount < 0,
    )
    if period_start is not None:
        used_stmt = used_stmt.where(BalanceTransaction.created_at >= period_start)
    used = int(await db.scalar(used_stmt) or 0)

    if is_unlimited:
        limit = 0
        percent = 0
    else:
        limit = used + remaining
        percent = min(100, round(used * 100 / limit)) if limit > 0 else 0

    return {
        "nav_counts": {
            "ads": counts.ads,
            "accounts": counts.accounts,
            "schedules": counts.schedules,
            "history": counts.history,
        },
        "quota": {
            "plan": subscription.plan if subscription else "free",
            "used": used,
            "limit": limit,
            "percent": percent,
            "expires_at": subscription.expires_at if subscription else None,
        },
        "sessions_online": counts.sessions_online,
        "sessions_total": counts.accounts,
    }
