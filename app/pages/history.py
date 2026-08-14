from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import (
    FAILED_STATUSES,
    HISTORY_PERIODS,
    STATUS_ACCOUNT_DISCONNECTED,
    STATUS_FAIL,
    STATUS_OK,
    apply_history_filters,
    history_filter_params,
)
from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.send_log import SendLog
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30

# --- Оси фильтрации: значения и подписи ---------------------------------------
#
# Перечни объявлены ЗДЕСЬ, а не в шаблоне (тот же приём, что у осей сводного
# списка расписаний): неизвестное значение обязано отсекаться сервером, а
# разметка точкой принуждения не является — она только рисует. Из этих же
# перечней строятся допустимые наборы `_clean_choice`, поэтому нарисованное и
# принимаемое разойтись не могут в принципе.

# Три значения журнала, а не два. Прежний выпадающий список знал «Успешные» и
# «Ошибки» и терял `account_disconnected` — единственный статус, по которому
# видно, что отправка не ушла из-за отвалившегося аккаунта. Набор СОБИРАЕТСЯ из
# констант модуля аналитики: четвёртый статус, заведённый там, обязан здесь
# упасть по KeyError, а не потеряться молча.
STATUS_LABELS = {
    STATUS_OK: "Успешно",
    STATUS_FAIL: "Ошибка",
    STATUS_ACCOUNT_DISCONNECTED: "Аккаунт отключён",
}
STATUS_CHIPS = (("", "Все"),) + tuple(
    (value, STATUS_LABELS[value]) for value in (STATUS_OK,) + FAILED_STATUSES
)

# Значения канала — те же, что у `MessengerAccount.type` и у оси канала
# сводного списка расписаний (`app.pages.schedules.CHANNEL_FILTER_VALUES`);
# подписи — те же слова, что печатают предпросмотр объявления и раздел
# аккаунтов. Совпадение значений с осью расписаний закреплено тестом, а не
# импортом: ось расписаний описывает ДРУГОЙ экран, и связывать их импортом
# значило бы объявить одну осью другой.
MESSENGER_CHIPS = (
    ("", "Все"),
    ("tg_user", "Telegram"),
    ("wa", "WhatsApp"),
    ("max", "MAX"),
)

# Произвольного диапазона дат нет (D-30): четыре варианта и ни одного поля
# ввода даты. Порядок «сегодня → 7 дней → 30 дней → всё время» — от узкого к
# широкому, как в макете; «всё время» стоит последним, потому что это снятие
# фильтра, а не самый широкий период.
PERIOD_LABELS = {"today": "Сегодня", "7d": "7 дней", "30d": "30 дней"}
PERIOD_CHIPS = tuple((value, PERIOD_LABELS[value]) for value in HISTORY_PERIODS) + (
    ("", "Всё время"),
)


def _values(chips) -> frozenset[str]:
    """Допустимые значения оси без варианта «все»."""
    return frozenset(value for value, _ in chips if value)


STATUS_VALUES = _values(STATUS_CHIPS)
MESSENGER_VALUES = _values(MESSENGER_CHIPS)
PERIOD_VALUES = _values(PERIOD_CHIPS)


def _clean_choice(value: str | None, allowed: frozenset[str]) -> str | None:
    """Неизвестное или испорченное значение оси → «фильтр не применён».

    Значение приезжает строкой запроса, то есть из ссылки, закладки или чужого
    сообщения (T-04-23). Отказ страницы был бы здесь отказом в обслуживании по
    подконтрольному отправителю значению, а молча применённый мусор — пустым
    списком, в котором НИ ОДИН чипс не отмечен активным: по такому экрану не
    прочитать, что вообще произошло. Оба исхода хуже, чем «мусор не выбирает
    ничего», и последнее ровно то же, что делает ось канала сводного списка
    расписаний.

    Период отсекается той же дорогой, хотя модуль аналитики и сам не применяет
    отсечку по неизвестному периоду: без отсечки здесь мусорный период доехал
    бы до адреса чипса и до сентинеля прокрутки как действующий фильтр.
    """
    if not value:
        return None
    value = value.strip()
    return value if value in allowed else None


def _parse_account_id(v: str | None) -> int | None:
    """Разбор HTTP-параметра, а не аналитика — поэтому остаётся здесь.

    Определение самих фильтров переехало в
    `app/application/analytics/send_analytics.py` (D-35): его зовут и история,
    и админка, и счётчик, и ни один из них не владеет копией. Этот же хелпер
    знает про то, что `account_id` приезжает строкой из query-строки, — знание
    транспорта, которому в слое аналитики не место.
    """
    if not v or not v.strip():
        return None
    try:
        return int(v)
    except ValueError:
        return None


@router.get("/history/partial", response_class=HTMLResponse)
async def history_partial(
    request: Request,
    status: str | None = Query(default=None),
    messenger: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(PAGE_SIZE, ge=1, le=100),
    # D-15: параметр компоновки принимается и игнорируется — см. app/pages/ads.py
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    status = _clean_choice(status, STATUS_VALUES)
    messenger = _clean_choice(messenger, MESSENGER_VALUES)
    period = _clean_choice(period, PERIOD_VALUES)
    account_id_int = _parse_account_id(account_id)
    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user.id)
    )
    query = apply_history_filters(
        query,
        status=status,
        messenger_type=messenger,
        account_id=account_id_int,
        period=period,
        user=user,
    )
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(limit + 1)
    result = await db.execute(query)
    rows = list(result.all())
    has_next = len(rows) > limit
    logs = [
        {
            "id": r.id,
            "ad_title": r.ad_title or "—",
            "ad_text": r.ad_text or "",
            "ad_images": r.ad_images or [],
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
        "history/partial_cards.html",
        {
            "request": request,
            "user": user,
            "logs": logs,
            "has_next": has_next,
            "next_offset": offset + limit,
            "status_filter": status,
            "filter_messenger": messenger,
            "filter_account_id": account_id_int,
            "filter_period": period,
            "filter_params": filter_params,
        },
    )


@router.get("/history/{log_id}", response_class=HTMLResponse)
async def history_detail(
    request: Request,
    log_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    log = await db.get(SendLog, log_id)
    if not log or log.user_id != user.id:
        return RedirectResponse(url="/history", status_code=302)

    group = await db.get(Group, log.group_id) if log.group_id else None

    return templates.TemplateResponse(
        "history/detail.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "log": log,
            "group": group,
            "active_page": "history",
        },
    )


@router.get("/history", response_class=HTMLResponse)
async def history_list(
    request: Request,
    status: str | None = Query(default=None),
    messenger: str | None = Query(default=None),
    account_id: str | None = Query(default=None),
    period: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    status = _clean_choice(status, STATUS_VALUES)
    messenger = _clean_choice(messenger, MESSENGER_VALUES)
    period = _clean_choice(period, PERIOD_VALUES)
    account_id_int = _parse_account_id(account_id)
    query = (
        select(SendLog, Group)
        .outerjoin(Group, SendLog.group_id == Group.id)
        .where(SendLog.user_id == user.id)
    )
    query = apply_history_filters(
        query,
        status=status,
        messenger_type=messenger,
        account_id=account_id_int,
        period=period,
        user=user,
    )
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(PAGE_SIZE + 1)
    result = await db.execute(query)
    rows = list(result.all())
    has_next = len(rows) > PAGE_SIZE
    rows = rows[:PAGE_SIZE]

    logs = [
        {
            "id": r.id,
            "ad_title": r.ad_title or "—",
            "ad_text": r.ad_text or "",
            "ad_images": r.ad_images or [],
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
        select(MessengerAccount).where(MessengerAccount.user_id == user.id)
    )
    all_accounts = accounts_result.scalars().all()
    filter_params = history_filter_params(status, messenger, account_id_int, period)

    return templates.TemplateResponse(
        "history/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "logs": logs,
            "all_accounts": all_accounts,
            "status_filter": status,
            "filter_messenger": messenger,
            "filter_account_id": account_id_int,
            "filter_period": period,
            "filter_params": filter_params,
            # Наборы значений уходят ТОЛЬКО в список: чипсы живут над выдачей и
            # подменой порций прокрутки не затрагиваются. Паршал получает
            # активные значения (они едут в адресе сентинеля) и не получает
            # перечней, которых не рисует.
            "status_chips": STATUS_CHIPS,
            "messenger_chips": MESSENGER_CHIPS,
            "period_chips": PERIOD_CHIPS,
            "offset": offset,
            "page_size": PAGE_SIZE,
            "has_next": has_next,
            "next_offset": offset + len(logs),
            "active_page": "history",
        },
    )
