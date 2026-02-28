import base64
import io

import qrcode
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.group import Group
from app.models.messenger_account import MessengerAccount
from app.application.accounts.use_cases import (
    delete_account,
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
from app.messengers.whatsapp import WhatsAppMessenger
from app.pages.common import check_is_admin, get_user_from_cookie, templates

router = APIRouter(tags=["pages"])
PAGE_SIZE = 30


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
    return templates.TemplateResponse(
        "accounts/partial_rows.html",
        {
            "request": request,
            "user": user,
            "accounts": accounts,
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
    return templates.TemplateResponse(
        "accounts/list.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "accounts": accounts,
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
        return HTMLResponse('<span class="text-sm text-red-600">Не авторизован</span>')

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
        return HTMLResponse('<span class="text-sm text-red-600">Нет активной сессии подключения</span>')

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

            return HTMLResponse(
                '<div class="text-center">'
                '<div class="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 rounded-full mb-4">'
                '<svg class="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
                '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>'
                '</svg></div>'
                '<p class="text-lg font-medium text-gray-900">WhatsApp подключён!</p>'
                '<p class="mt-2 text-sm text-slate-500">Начинаем синхронизацию групп...</p>'
                '<script>setTimeout(() => window.location.href = "/accounts", 2000);</script>'
                '</div>'
            )

        # Not connected — get fresh QR
        qr_data = await messenger.get_qr()
        qr = qr_data.get("qr")

        if qr:
            return HTMLResponse(
                f'<div class="text-center">'
                f'<div class="inline-block p-4 bg-white border rounded-lg">'
                f'<img src="{qr}" alt="WhatsApp QR-код" class="mx-auto" style="max-width: 256px;">'
                f'</div>'
                f'<p class="mt-2 text-sm text-yellow-600">Ожидание сканирования...</p>'
                f'</div>'
            )

        return HTMLResponse('<span class="text-sm text-amber-600">Ожидание...</span>')

    except Exception as e:
        import structlog
        structlog.get_logger().error("wa_connect_status_error", error=str(e), exc_info=True)
        return HTMLResponse('<span class="text-sm text-red-600">Ошибка соединения с WA Bridge</span>')


@router.get("/accounts/{account_id}/sync-status", response_class=HTMLResponse)
async def accounts_sync_status(
    request: Request,
    account_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """HTMX polling endpoint: reads account status from DB (Celery task updates it)."""
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return HTMLResponse('<span class="text-sm text-red-600">Не авторизован</span>')

    # Используем application-слой для чтения актуального статуса.
    view = await get_sync_status_view(db, user.id, account_id)
    if view is None:
        return HTMLResponse('<span class="text-sm text-red-600">Аккаунт не найден</span>')

    if view.status in ("active", "sync_failed", "syncing"):
        html = templates.env.get_template("accounts/partials/sync_status_row.html").render(
            account_id=account_id,
            status=view.status,
            group_count=view.group_count,
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
            MessengerAccount.type == "wa",
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        return RedirectResponse(url="/accounts", status_code=302)

    session_id = str(account.id)
    messenger = WhatsAppMessenger(session_id=session_id)
    await messenger.retry_sync()

    account.status = "syncing"
    await db.commit()

    # Dispatch background Celery task to poll bridge and save groups
    from app.worker.celery_app import celery
    celery.send_task("app.worker.tasks.sync_wa_groups", args=[account.id])

    return RedirectResponse(url="/accounts", status_code=302)


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
    if not account or account.type not in ("tg_user", "wa"):
        return RedirectResponse(url="/groups", status_code=302)

    if account.status == "syncing":
        return RedirectResponse(url="/groups", status_code=302)

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

    # Load existing groups for this account to skip duplicates
    existing = await db.execute(
        select(Group.group_external_id).where(
            Group.account_id == account_id,
            Group.user_id == user.id,
        )
    )
    existing_ids = {row[0] for row in existing}

    for g in fetched_groups:
        if g["id"] not in existing_ids:
            db.add(
                Group(
                    user_id=user.id,
                    account_id=account_id,
                    messenger_type=messenger_type,
                    group_external_id=g["id"],
                    name=g.get("name") or g["id"],
                )
            )

    await db.commit()
    return RedirectResponse(url="/groups", status_code=302)


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
