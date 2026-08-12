import base64
import io

import qrcode
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.application.accounts.group_resync import (
    apply_group_resync,
    record_sync_failure,
)
from app.application.accounts.use_cases import (
    delete_account,
    detach_schedules_from_account,
    get_sync_status_view,
)
from app.messengers.telegram_user import (
    TelegramUserMessenger,
    start_qr_auth,
    get_qr_status,
    refresh_qr,
    submit_2fa,
    complete_auth,
)
from app.messengers.base import MessengerFetchError
from app.messengers.max import MaxMessenger
from app.messengers.whatsapp import WhatsAppMessenger
from app.pages.common import check_is_admin, get_user_from_cookie, templates

# Разметка ответов опроса статуса подключения живёт в шаблоне, а не в строках
# обработчика (План 08). До этого она собиралась конкатенацией и несла
# utility-классы удалённого фреймворка, а адрес QR-кода от внешнего моста
# подставлялся в src без экранирования.
_CONNECT_STATUS = "accounts/partials/connect_status.html"


def _connect_status(macro: str, *args) -> HTMLResponse:
    """Рендерит макрос ответа опроса подключения через окружение Jinja2."""
    module = templates.env.get_template(_CONNECT_STATUS).module
    return HTMLResponse(str(getattr(module, macro)(*args)))

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30


async def _get_account_stats(
    db: AsyncSession, user_id: int, account_ids: list[int]
) -> dict[int, dict]:
    """Возвращает статистику по аккаунтам: группы, попытки, успехи, расписания, последняя отправка."""
    if not account_ids:
        return {}

    # groups_count
    groups_r = await db.execute(
        select(Group.account_id, func.count(Group.id).label("cnt"))
        .where(Group.account_id.in_(account_ids), Group.user_id == user_id)
        .group_by(Group.account_id)
    )
    groups_map = {r.account_id: r.cnt for r in groups_r}

    # schedules_count
    sched_r = await db.execute(
        select(Schedule.account_id, func.count(Schedule.id).label("cnt"))
        .where(Schedule.account_id.in_(account_ids))
        .group_by(Schedule.account_id)
    )
    sched_map = {r.account_id: r.cnt for r in sched_r}

    # send_attempts, send_success, last_sent_at (через Group -> account_id)
    send_sub = (
        select(
            Group.account_id,
            func.count(SendLog.id).label("attempts"),
            func.sum(case((SendLog.status == "ok", 1), else_=0)).label("success"),
            func.max(SendLog.sent_at).label("last_sent"),
        )
        .join(SendLog, SendLog.group_id == Group.id)
        .where(
            Group.account_id.in_(account_ids),
            Group.user_id == user_id,
            SendLog.user_id == user_id,
        )
        .group_by(Group.account_id)
    )
    send_result = await db.execute(send_sub)
    send_map = {}
    for r in send_result:
        send_map[r.account_id] = {
            "attempts": r.attempts or 0,
            "success": int(r.success or 0),
            "last_sent_at": r.last_sent,
        }

    # Собираем итог
    result = {}
    for aid in account_ids:
        result[aid] = {
            "groups_count": groups_map.get(aid, 0),
            "schedules_count": sched_map.get(aid, 0),
            "send_attempts": send_map.get(aid, {}).get("attempts", 0),
            "send_success": send_map.get(aid, {}).get("success", 0),
            "last_sent_at": send_map.get(aid, {}).get("last_sent_at"),
        }
    return result


def _generate_qr_base64(data: str) -> str:
    """Generate QR code as base64 PNG data URI."""
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


@router.get("/accounts/partial", response_class=HTMLResponse)
async def accounts_partial(
    request: Request,
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
    result = await db.execute(
        select(MessengerAccount)
        .where(MessengerAccount.user_id == user.id)
        .order_by(MessengerAccount.id)
        .offset(offset)
        .limit(limit + 1)
    )
    rows = list(result.scalars().all())
    has_next = len(rows) > limit
    accounts = rows[:limit]
    account_stats = await _get_account_stats(
        db, user.id, [a.id for a in accounts]
    )
    return templates.TemplateResponse(
        "accounts/partial_cards.html",
        {
            "request": request,
            "user": user,
            "accounts": accounts,
            "account_stats": account_stats,
            "has_next": has_next,
            "next_offset": offset + limit,
        },
    )


@router.get("/accounts", response_class=HTMLResponse)
async def accounts_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(MessengerAccount)
        .where(MessengerAccount.user_id == user.id)
        .order_by(MessengerAccount.id)
        .limit(PAGE_SIZE + 1)
    )
    rows = list(result.scalars().all())
    has_next = len(rows) > PAGE_SIZE
    accounts = rows[:PAGE_SIZE]
    account_stats = await _get_account_stats(
        db, user.id, [a.id for a in accounts]
    )
    return templates.TemplateResponse(
        "accounts/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "accounts": accounts,
            "account_stats": account_stats,
            "has_next": has_next,
            "next_offset": PAGE_SIZE,
            "active_page": "accounts",
        },
    )


@router.get("/accounts/connect/tg_user", response_class=HTMLResponse)
async def accounts_connect_tg_user_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "accounts/connect_tg_user.html",
        {"request": request, "user": user, "is_admin": check_is_admin(user, settings), "active_page": "accounts"},
    )


@router.post("/accounts/connect/tg_user/start-qr")
async def accounts_connect_tg_user_start_qr(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return {"error": "Не авторизован"}

    if not settings.telegram_api_id or not settings.telegram_api_hash:
        return {"error": "Telegram API не настроен. Обратитесь к администратору."}

    try:
        session_id, login_url = await start_qr_auth(
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
        )
    except Exception as e:
        return {"error": f"Ошибка запуска QR авторизации: {e}"}

    return {
        "session_id": session_id,
        "qr_image": _generate_qr_base64(login_url),
    }


@router.get("/accounts/connect/tg_user/qr-status")
async def accounts_connect_tg_user_qr_status(
    request: Request,
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return {"status": "error", "error": "Не авторизован"}

    return get_qr_status(session_id)


@router.post("/accounts/connect/tg_user/refresh-qr")
async def accounts_connect_tg_user_refresh_qr(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return {"error": "Не авторизован"}

    data = await request.json()
    session_id = data.get("session_id")
    if not session_id:
        return {"error": "session_id required"}

    new_url = await refresh_qr(session_id)
    if not new_url:
        return {"error": "Не удалось обновить QR. Начните заново."}

    return {"qr_image": _generate_qr_base64(new_url)}


@router.post("/accounts/connect/tg_user/verify-2fa")
async def accounts_connect_tg_user_verify_2fa(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return {"error": "Не авторизован"}

    data = await request.json()
    session_id = data.get("session_id")
    password = data.get("password")

    if not session_id or not password:
        return {"error": "session_id и password обязательны"}

    try:
        session_string = await submit_2fa(session_id, password)
    except ValueError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}

    # Clean up auth client
    await complete_auth(session_id)

    # Create MessengerAccount
    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials=session_string,
        status="active",
    )
    db.add(account)
    await db.commit()

    return {"status": "success"}


@router.post("/accounts/connect/tg_user/complete")
async def accounts_connect_tg_user_complete(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return {"error": "Не авторизован"}

    data = await request.json()
    session_id = data.get("session_id")
    if not session_id:
        return {"error": "session_id required"}

    session_string = await complete_auth(session_id)
    if not session_string:
        return {"error": "Сессия не найдена или авторизация не завершена."}

    # Create MessengerAccount
    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials=session_string,
        status="active",
    )
    db.add(account)
    await db.commit()

    return {"status": "success"}


@router.get("/accounts/connect/wa", response_class=HTMLResponse)
async def accounts_connect_wa_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Start QR-based WA connection (default flow)."""
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Check if user already has an active or syncing WA account
    existing = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "wa",
            MessengerAccount.status.in_(["active", "syncing"]),
        )
    )
    if existing.scalar_one_or_none():
        return RedirectResponse(url="/accounts", status_code=302)

    # Clean up stale connecting/failed accounts
    stale = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "wa",
            MessengerAccount.status.in_(["connecting", "sync_failed"]),
        )
    )
    for old in stale.scalars().all():
        # issue #35: расписания сохраняются и приостанавливаются, а не удаляются
        await detach_schedules_from_account(db, old.id)
        await db.delete(old)
    await db.commit()

    # Create a pending WA account to get a session_id
    account = MessengerAccount(
        user_id=user.id,
        type="wa",
        credentials="pending",
        status="connecting",
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)

    session_id = str(account.id)
    messenger = WhatsAppMessenger(session_id=session_id)

    qr_code = None
    connected = False
    error = None

    try:
        await messenger.start_session()
        qr_data = await messenger.get_qr()
        qr_code = qr_data.get("qr")
        if qr_data.get("status") == "connected":
            connected = True
    except Exception as e:
        error = f"Ошибка подключения к WA Bridge: {e}"

    return templates.TemplateResponse(
        "accounts/connect_wa.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "active_page": "accounts",
            "step": "qr",
            "qr_code": qr_code,
            "connected": connected,
            "error": error,
            "account_id": account.id,
        },
    )


@router.get("/accounts/connect/wa/status", response_class=HTMLResponse)
async def accounts_connect_wa_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return _connect_status("notice", "Не авторизован")

    # Find the pending/connecting WA account for this user
    result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "wa",
            MessengerAccount.status == "connecting",
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return _connect_status("notice", "Нет активной сессии подключения")

    session_id = str(account.id)
    messenger = WhatsAppMessenger(session_id=session_id)

    try:
        is_connected = await messenger.check_connection()
        if is_connected:
            account.credentials = session_id
            account.status = "syncing"
            await db.commit()

            # Dispatch background Celery task to poll bridge and save groups
            from app.worker.celery_app import celery
            celery.send_task("app.worker.tasks.sync_wa_groups", args=[account.id])

            return _connect_status("connected", "WhatsApp")

        # Not connected — get fresh QR
        qr_data = await messenger.get_qr()
        qr = qr_data.get("qr")

        if qr:
            return _connect_status("qr", qr, "WhatsApp")

        return _connect_status("notice", "Ожидание...", "warning")

    except Exception as e:
        import structlog
        structlog.get_logger().error("wa_connect_status_error", error=str(e), exc_info=True)
        return _connect_status("notice", "Ошибка соединения с WA Bridge")


@router.get("/accounts/connect/max", response_class=HTMLResponse)
async def accounts_connect_max_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Show phone input form for MAX connection."""
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Check if user already has an active or syncing MAX account
    existing = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "max",
            MessengerAccount.status.in_(["active", "syncing"]),
        )
    )
    if existing.scalar_one_or_none():
        return RedirectResponse(url="/accounts", status_code=302)

    # Clean up stale connecting/failed accounts
    stale = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "max",
            MessengerAccount.status.in_(["connecting", "sync_failed"]),
        )
    )
    for old in stale.scalars().all():
        # issue #35: расписания сохраняются и приостанавливаются, а не удаляются
        await detach_schedules_from_account(db, old.id)
        await db.delete(old)
    await db.commit()

    return templates.TemplateResponse(
        "accounts/connect_max.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "active_page": "accounts",
            "step": "phone",
        },
    )


@router.post("/accounts/connect/max/start", response_class=HTMLResponse)
async def accounts_connect_max_start(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Receive phone, create account, start session, show QR."""
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    form = await request.form()
    phone = (form.get("phone") or "").strip()

    if not phone:
        return templates.TemplateResponse(
            "accounts/connect_max.html",
            {
                "request": request,
                "user": user,
                "is_admin": check_is_admin(user, settings),
                "active_page": "accounts",
                "step": "phone",
                "error": "Введите номер телефона",
            },
        )

    # Reuse existing "connecting" MAX account or create a new one
    result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "max",
            MessengerAccount.status == "connecting",
        )
    )
    account = result.scalars().first()
    if account:
        account.credentials = phone
        await db.commit()
    else:
        account = MessengerAccount(
            user_id=user.id,
            type="max",
            credentials=phone,
            status="connecting",
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)

    session_id = str(account.id)
    messenger = MaxMessenger(session_id=session_id)

    qr_code = None
    error = None

    try:
        await messenger.start_session(phone=phone)
        import asyncio
        await asyncio.sleep(5)
        qr_data = await messenger.get_qr()
        qr_link = qr_data.get("qr")
        if qr_link:
            qr_code = _generate_qr_base64(qr_link)
    except Exception as e:
        error = f"Ошибка подключения к MAX: {e}"

    return templates.TemplateResponse(
        "accounts/connect_max.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "active_page": "accounts",
            "step": "qr",
            "qr_code": qr_code,
            "connected": False,
            "error": error,
            "account_id": account.id,
        },
    )


@router.get("/accounts/connect/max/status", response_class=HTMLResponse)
async def accounts_connect_max_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """HTMX polling endpoint for MAX connection status."""
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return _connect_status("notice", "Не авторизован")

    # Find the pending/connecting MAX account for this user
    result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "max",
            MessengerAccount.status == "connecting",
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return _connect_status("notice", "Нет активной сессии подключения")

    session_id = str(account.id)
    messenger = MaxMessenger(session_id=session_id)

    try:
        is_connected = await messenger.check_connection()
        if is_connected:
            account.credentials = session_id
            account.status = "syncing"
            await db.commit()

            # Dispatch background Celery task to sync groups
            from app.worker.celery_app import celery
            celery.send_task("app.worker.tasks.sync_max_groups", args=[account.id])

            return _connect_status("connected", "MAX")

        # Not connected — get fresh QR
        qr_data = await messenger.get_qr()
        qr_link = qr_data.get("qr")

        if qr_link:
            qr_img = _generate_qr_base64(qr_link)
            return _connect_status("qr", qr_img, "MAX")

        return _connect_status("notice", "Ожидание...", "warning")

    except Exception as e:
        import structlog
        structlog.get_logger().error("max_connect_status_error", error=str(e), exc_info=True)
        return _connect_status("notice", "Ошибка соединения с MAX")


@router.get("/accounts/{account_id}/sync-status", response_class=HTMLResponse)
async def accounts_sync_status(
    request: Request,
    account_id: int,
    # D-15: параметр компоновки принимается и игнорируется — см. app/pages/ads.py
    layout: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """HTMX polling endpoint: reads account status from DB (Celery task updates it)."""
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return _connect_status("notice", "Не авторизован")

    # Используем application-слой для чтения актуального статуса.
    view = await get_sync_status_view(db, user.id, account_id)
    if view is None:
        return _connect_status("notice", "Аккаунт не найден")

    if view.status in ("active", "sync_failed", "syncing"):
        stats_map = await _get_account_stats(db, user.id, [account_id]) if view.status == "active" else {}
        stats = stats_map.get(account_id, {}) if view.status == "active" else {}
        html = templates.env.get_template("accounts/partials/sync_status_card.html").render(
            account_id=account_id,
            status=view.status,
            group_count=view.group_count,
            messenger_type=view.messenger_type,
            user=user,
            stats=stats,
        )
        return HTMLResponse(html)

    return HTMLResponse("")


@router.post("/accounts/{account_id}/retry-sync")
async def accounts_retry_sync(
    request: Request,
    account_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Retry failed group sync."""
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.id == account_id,
            MessengerAccount.user_id == user.id,
            MessengerAccount.type.in_(["wa", "max"]),
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return RedirectResponse(url="/accounts", status_code=302)

    session_id = str(account.id)
    if account.type == "max":
        messenger = MaxMessenger(session_id=session_id)
    else:
        messenger = WhatsAppMessenger(session_id=session_id)
    await messenger.retry_sync()

    account.status = "syncing"
    await db.commit()

    # Dispatch background Celery task to poll bridge and save groups
    from app.worker.celery_app import celery
    task_name = "app.worker.tasks.sync_max_groups" if account.type == "max" else "app.worker.tasks.sync_wa_groups"
    celery.send_task(task_name, args=[account.id])

    # Повторный запуск нажимают с экрана групп аккаунта — туда же и возвращаем.
    return RedirectResponse(url=f"/accounts/{account_id}/groups", status_code=302)


@router.post("/accounts/{account_id}/sync-groups")
async def accounts_sync_groups(
    request: Request,
    account_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.id == account_id,
            MessengerAccount.user_id == user.id,
        )
    )
    account = result.scalar_one_or_none()
    # Адрес несуществующего экрана предлагать нечему: аккаунт, не разрешённый в
    # собственный аккаунт пользователя, уводит на список аккаунтов. Все
    # остальные ветки возвращают пользователя туда, откуда он нажал кнопку.
    if not account:
        return RedirectResponse(url="/accounts", status_code=302)

    account_groups_url = f"/accounts/{account_id}/groups"

    if account.type not in ("tg_user", "wa", "max"):
        return RedirectResponse(url=account_groups_url, status_code=302)

    # Guard повторного запуска: он же закрывает гонку двойного нажатия.
    if account.status == "syncing":
        return RedirectResponse(url=account_groups_url, status_code=302)

    # Протоколы обращения к мессенджерам не меняются: те же конструкторы и тот
    # же единственный get_groups() в каждой ветке. Новое здесь только одно —
    # отказ внешней системы записывается на аккаунт, а не теряется 500-й.
    #
    # Ветка отказа ДОСТИЖИМА только потому, что адаптеры больше не глушат
    # исключение и не возвращают вместо него пустой список: `MessengerFetchError`
    # — это «состав групп получить не удалось», и оно отличимо от «групп нет».
    # Пока адаптеры возвращали `[]`, этот except не срабатывал никогда, а сбой
    # моста доезжал до переинвентаризации сводкой успеха.
    try:
        if account.type == "tg_user":
            messenger = TelegramUserMessenger(
                session_string=account.credentials,
                api_id=settings.telegram_api_id,
                api_hash=settings.telegram_api_hash,
            )
            fetched_groups = await messenger.get_groups()
            messenger_type = "tg_user"

        elif account.type == "wa":
            messenger = WhatsAppMessenger(session_id=str(account.id))
            fetched_groups = await messenger.get_groups()
            messenger_type = "wa"

        elif account.type == "max":
            messenger = MaxMessenger(session_id=str(account.id))
            fetched_groups = await messenger.get_groups()
            messenger_type = "max"

    except MessengerFetchError as e:
        import structlog
        structlog.get_logger().error(
            "sync_groups_fetch_failed",
            account_id=account_id,
            account_type=account.type,
            error=str(e),
            exc_info=True,
        )
        # Пишется сообщение исключения, а не строка подключения (T-03-17).
        await record_sync_failure(db, account, str(e) or e.__class__.__name__)
        await db.commit()
        return RedirectResponse(url=account_groups_url, status_code=302)

    except Exception as e:
        # Широкий except СОХРАНЁН намеренно и стоит ПОСЛЕ узкого: отказ на
        # конструкторе адаптера или на запуске wa-worker (RuntimeError из
        # свойства `bridge_url`) случается ДО запроса за составом групп, и он
        # тоже обязан лечь сводкой на аккаунт, а не пятисоткой. Сузить блок до
        # одного `MessengerFetchError` означало бы вернуть на экран стек-трейс
        # там, где раньше была красная плашка.
        import structlog
        structlog.get_logger().error(
            "sync_groups_failed",
            account_id=account_id,
            account_type=account.type,
            error=str(e),
            exc_info=True,
        )
        await record_sync_failure(db, account, str(e) or e.__class__.__name__)
        await db.commit()
        return RedirectResponse(url=account_groups_url, status_code=302)

    # Состав групп считает единственная реализация переинвентаризации —
    # та же, что у обеих фоновых задач (D-10, D-11, D-12). Транзакцией
    # по-прежнему управляет обработчик: хелпер не коммитит.
    await apply_group_resync(db, account, fetched_groups, messenger_type=messenger_type)
    await db.commit()
    return RedirectResponse(url=account_groups_url, status_code=302)


@router.post("/accounts/{account_id}/delete")
async def accounts_delete(
    request: Request,
    account_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    await delete_account(db, user.id, account_id)
    return RedirectResponse(url="/accounts", status_code=302)
