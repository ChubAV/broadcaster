from pathlib import Path

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.dependencies import get_db, get_settings
from app.config import Settings
from app.services.auth_service import (
    decode_access_token,
    hash_password,
    verify_password,
    create_access_token,
)
from app.models.user import User
from app.models.ad import Ad
from app.models.messenger_account import MessengerAccount
from app.models.group import Group
from app.models.schedule import Schedule
from app.models.send_log import SendLog
from app.models.telegram_auth_session import TelegramAuthSession
from app.services.billing_service import get_user_plan, get_plan_limits, get_usage, PLANS
from app.messengers.telegram_user import (
    TelegramUserMessenger,
    start_auth,
    resend_code,
    verify_code,
    verify_password as tg_verify_password,
    cleanup_auth_client,
)

router = APIRouter(tags=["pages"])

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


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
    return user


# ---------------------------------------------------------------------------
# Auth pages
# ---------------------------------------------------------------------------


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html", {"request": request, "error": "Неверный email или пароль"}
        )
    token = create_access_token(user.id, settings.secret_key)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Этот email уже зарегистрирован"},
        )
    user = User(email=email, password_hash=hash_password(password), name=name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(user.id, settings.secret_key)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Stats
    ads_count = (
        await db.execute(
            select(func.count(Ad.id)).where(
                Ad.user_id == user.id, Ad.is_active == True  # noqa: E712
            )
        )
    ).scalar() or 0
    accounts_count = (
        await db.execute(
            select(func.count(MessengerAccount.id)).where(
                MessengerAccount.user_id == user.id,
                MessengerAccount.status == "active",
            )
        )
    ).scalar() or 0
    groups_count = (
        await db.execute(
            select(func.count(Group.id)).where(
                Group.user_id == user.id, Group.is_active == True  # noqa: E712
            )
        )
    ).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    sent_today = (
        await db.execute(
            select(func.count(SendLog.id))
            .join(Ad, SendLog.ad_id == Ad.id)
            .where(Ad.user_id == user.id, SendLog.sent_at >= today_start)
        )
    ).scalar() or 0

    stats = {
        "active_ads": ads_count,
        "active_accounts": accounts_count,
        "active_groups": groups_count,
        "sent_today": sent_today,
    }

    # Recent sends (last 10)
    recent_query = (
        select(SendLog, Ad.title.label("ad_title"), Group.name.label("group_name"))
        .join(Ad, SendLog.ad_id == Ad.id)
        .join(Group, SendLog.group_id == Group.id)
        .where(Ad.user_id == user.id)
        .order_by(SendLog.sent_at.desc())
        .limit(10)
    )
    recent_result = await db.execute(recent_query)
    recent_sends = [
        {
            "ad_title": r.ad_title,
            "group_name": r.group_name,
            "status": r.SendLog.status,
            "sent_at": r.SendLog.sent_at,
        }
        for r in recent_result
    ]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "recent_sends": recent_sends,
            "active_page": "dashboard",
        },
    )


# ---------------------------------------------------------------------------
# Ads pages
# ---------------------------------------------------------------------------


@router.get("/ads", response_class=HTMLResponse)
async def ads_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.user_id == user.id).order_by(Ad.created_at.desc())
    )
    ads = result.scalars().all()
    return templates.TemplateResponse(
        "ads/list.html",
        {"request": request, "user": user, "ads": ads, "active_page": "ads"},
    )


@router.get("/ads/new", response_class=HTMLResponse)
async def ads_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "ads/form.html",
        {"request": request, "user": user, "ad": None, "active_page": "ads"},
    )


@router.post("/ads/new", response_class=HTMLResponse)
async def ads_create(
    request: Request,
    title: str = Form(...),
    text: str = Form(...),
    images: str = Form(""),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    image_list = [img.strip() for img in images.splitlines() if img.strip()]
    ad = Ad(user_id=user.id, title=title, text=text, images=image_list)
    db.add(ad)
    await db.commit()
    return RedirectResponse(url="/ads", status_code=302)


@router.get("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_edit(
    request: Request,
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)
    return templates.TemplateResponse(
        "ads/form.html",
        {"request": request, "user": user, "ad": ad, "active_page": "ads"},
    )


@router.post("/ads/{ad_id}/edit", response_class=HTMLResponse)
async def ads_update(
    request: Request,
    ad_id: int,
    title: str = Form(...),
    text: str = Form(...),
    images: str = Form(""),
    is_active: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if not ad:
        return RedirectResponse(url="/ads", status_code=302)

    image_list = [img.strip() for img in images.splitlines() if img.strip()]
    ad.title = title
    ad.text = text
    ad.images = image_list
    ad.is_active = is_active
    await db.commit()
    return RedirectResponse(url="/ads", status_code=302)


@router.post("/ads/{ad_id}/delete")
async def ads_delete(
    request: Request,
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.user_id == user.id)
    )
    ad = result.scalar_one_or_none()
    if ad:
        await db.delete(ad)
        await db.commit()
    return RedirectResponse(url="/ads", status_code=302)


# ---------------------------------------------------------------------------
# Accounts pages
# ---------------------------------------------------------------------------


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
    )
    accounts = result.scalars().all()
    return templates.TemplateResponse(
        "accounts/list.html",
        {
            "request": request,
            "user": user,
            "accounts": accounts,
            "active_page": "accounts",
        },
    )


@router.get("/accounts/connect/tg_bot", response_class=HTMLResponse)
async def accounts_connect_tg_bot_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        "accounts/connect_tg_bot.html",
        {"request": request, "user": user, "active_page": "accounts"},
    )


@router.post("/accounts/connect/tg_bot")
async def accounts_connect_tg_bot_submit(
    request: Request,
    credentials: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    account = MessengerAccount(
        user_id=user.id,
        type="tg_bot",
        credentials=credentials,
        status="active",
    )
    db.add(account)
    await db.commit()
    return RedirectResponse(url="/accounts", status_code=302)


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
        {"request": request, "user": user, "active_page": "accounts"},
    )


@router.post("/accounts/connect/tg_user/send-code")
async def accounts_connect_tg_user_send_code(
    request: Request,
    phone_number: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if not settings.telegram_api_id or not settings.telegram_api_hash:
        return templates.TemplateResponse(
            "accounts/connect_tg_user.html",
            {
                "request": request,
                "user": user,
                "active_page": "accounts",
                "error": "Telegram API не настроен. Обратитесь к администратору.",
            },
        )

    from datetime import timedelta

    auth_session = TelegramAuthSession(
        user_id=user.id,
        phone_number=phone_number,
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(auth_session)
    await db.commit()
    await db.refresh(auth_session)

    try:
        phone_code_hash = await start_auth(
            auth_session_id=auth_session.id,
            phone=phone_number,
            api_id=settings.telegram_api_id,
            api_hash=settings.telegram_api_hash,
        )
        auth_session.phone_code_hash = phone_code_hash
        auth_session.status = "code_sent"
        await db.commit()
    except Exception as e:
        auth_session.status = "error"
        auth_session.error_message = str(e)
        await db.commit()
        return templates.TemplateResponse(
            "accounts/connect_tg_user.html",
            {
                "request": request,
                "user": user,
                "active_page": "accounts",
                "error": f"Ошибка отправки кода: {e}",
            },
        )

    return RedirectResponse(
        url=f"/accounts/connect/tg_user/verify?session_id={auth_session.id}",
        status_code=302,
    )


@router.get("/accounts/connect/tg_user/verify", response_class=HTMLResponse)
async def accounts_connect_tg_user_verify_page(
    request: Request,
    session_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    auth_session = await db.get(TelegramAuthSession, session_id)
    if not auth_session or auth_session.user_id != user.id:
        return RedirectResponse(url="/accounts", status_code=302)

    expires_at = auth_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        cleanup_auth_client(auth_session.id)
        auth_session.status = "expired"
        await db.commit()
        return templates.TemplateResponse(
            "accounts/connect_tg_user.html",
            {
                "request": request,
                "user": user,
                "active_page": "accounts",
                "error": "Сессия авторизации истекла. Попробуйте снова.",
            },
        )

    needs_2fa = auth_session.status == "needs_2fa"

    return templates.TemplateResponse(
        "accounts/verify_tg_user.html",
        {
            "request": request,
            "user": user,
            "active_page": "accounts",
            "session_id": session_id,
            "phone_number": auth_session.phone_number,
            "needs_2fa": needs_2fa,
        },
    )


@router.post("/accounts/connect/tg_user/resend-code")
async def accounts_connect_tg_user_resend_code(
    request: Request,
    session_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    auth_session = await db.get(TelegramAuthSession, session_id)
    if not auth_session or auth_session.user_id != user.id:
        return RedirectResponse(url="/accounts", status_code=302)

    try:
        new_hash = await resend_code(
            auth_session_id=auth_session.id,
            phone=auth_session.phone_number,
            phone_code_hash=auth_session.phone_code_hash,
        )
        auth_session.phone_code_hash = new_hash
        await db.commit()
    except Exception as e:
        return templates.TemplateResponse(
            "accounts/verify_tg_user.html",
            {
                "request": request,
                "user": user,
                "active_page": "accounts",
                "session_id": session_id,
                "phone_number": auth_session.phone_number,
                "needs_2fa": False,
                "error": f"Ошибка повторной отправки: {e}",
            },
        )

    return RedirectResponse(
        url=f"/accounts/connect/tg_user/verify?session_id={auth_session.id}",
        status_code=302,
    )


@router.post("/accounts/connect/tg_user/verify")
async def accounts_connect_tg_user_verify_submit(
    request: Request,
    session_id: int = Form(...),
    step: str = Form(...),
    code: str = Form(None),
    password: str = Form(None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    auth_session = await db.get(TelegramAuthSession, session_id)
    if not auth_session or auth_session.user_id != user.id:
        return RedirectResponse(url="/accounts", status_code=302)

    expires_at = auth_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        cleanup_auth_client(auth_session.id)
        auth_session.status = "expired"
        await db.commit()
        return templates.TemplateResponse(
            "accounts/connect_tg_user.html",
            {
                "request": request,
                "user": user,
                "active_page": "accounts",
                "error": "Сессия авторизации истекла. Попробуйте снова.",
            },
        )

    try:
        if step == "code":
            from pyrogram.errors import SessionPasswordNeeded

            try:
                session_string = await verify_code(
                    auth_session_id=auth_session.id,
                    phone=auth_session.phone_number,
                    phone_code_hash=auth_session.phone_code_hash,
                    code=code,
                )
            except SessionPasswordNeeded:
                auth_session.status = "needs_2fa"
                await db.commit()
                return RedirectResponse(
                    url=f"/accounts/connect/tg_user/verify?session_id={auth_session.id}",
                    status_code=302,
                )
        elif step == "2fa":
            session_string = await tg_verify_password(
                auth_session_id=auth_session.id,
                password=password,
            )
        else:
            return RedirectResponse(url="/accounts", status_code=302)

    except Exception as e:
        error_msg = str(e)
        auth_session.error_message = error_msg
        await db.commit()
        needs_2fa = step == "2fa"
        return templates.TemplateResponse(
            "accounts/verify_tg_user.html",
            {
                "request": request,
                "user": user,
                "active_page": "accounts",
                "session_id": session_id,
                "phone_number": auth_session.phone_number,
                "needs_2fa": needs_2fa,
                "error": f"Ошибка: {error_msg}",
            },
        )

    # Success: create MessengerAccount
    auth_session.status = "completed"
    await db.commit()

    account = MessengerAccount(
        user_id=user.id,
        type="tg_user",
        credentials=session_string,
        status="active",
    )
    db.add(account)
    await db.commit()
    return RedirectResponse(url="/accounts", status_code=302)


@router.get("/accounts/connect/wa", response_class=HTMLResponse)
async def accounts_connect_wa_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    import httpx

    qr_code = None
    connected = False
    error = None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            status_resp = await client.get(f"{settings.wa_bridge_url}/api/status")
            if status_resp.status_code == 200 and status_resp.json().get("connected"):
                connected = True
            else:
                qr_resp = await client.get(f"{settings.wa_bridge_url}/api/qr")
                if qr_resp.status_code == 200:
                    data = qr_resp.json()
                    qr_code = data.get("qr")
    except httpx.ConnectError:
        error = "WA Bridge недоступен. Убедитесь, что сервис запущен."
    except Exception as e:
        error = f"Ошибка подключения к WA Bridge: {e}"

    return templates.TemplateResponse(
        "accounts/connect_wa.html",
        {
            "request": request,
            "user": user,
            "active_page": "accounts",
            "qr_code": qr_code,
            "connected": connected,
            "error": error,
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

    import httpx

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            status_resp = await client.get(f"{settings.wa_bridge_url}/api/status")
            if status_resp.status_code == 200 and status_resp.json().get("connected"):
                # Check if WA account already exists for this user
                existing = await db.execute(
                    select(MessengerAccount).where(
                        MessengerAccount.user_id == user.id,
                        MessengerAccount.type == "wa",
                        MessengerAccount.status == "active",
                    )
                )
                if not existing.scalar_one_or_none():
                    account = MessengerAccount(
                        user_id=user.id,
                        type="wa",
                        credentials="whatsapp-web",
                        status="active",
                    )
                    db.add(account)
                    await db.commit()

                return HTMLResponse(
                    '<div class="text-center">'
                    '<div class="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">'
                    '<svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>'
                    '</svg></div>'
                    '<p class="text-lg font-medium text-gray-900">WhatsApp подключён!</p>'
                    '<a href="/accounts" class="mt-4 inline-block rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500">К аккаунтам</a>'
                    '</div>'
                )

            # Not connected yet — return fresh QR
            qr_resp = await client.get(f"{settings.wa_bridge_url}/api/qr")
            if qr_resp.status_code == 200:
                data = qr_resp.json()
                qr = data.get("qr")
                if qr:
                    return HTMLResponse(
                        f'<div class="text-center">'
                        f'<div class="inline-block p-4 bg-white border rounded-lg">'
                        f'<img src="{qr}" alt="WhatsApp QR-код" class="mx-auto" style="max-width: 256px;">'
                        f'</div>'
                        f'<p class="mt-2 text-sm text-yellow-600">Ожидание сканирования...</p>'
                        f'</div>'
                    )

            return HTMLResponse('<span class="text-sm text-yellow-600">Ожидание QR-кода...</span>')

    except httpx.ConnectError:
        return HTMLResponse('<span class="text-sm text-red-600">WA Bridge недоступен</span>')
    except Exception:
        return HTMLResponse('<span class="text-sm text-red-600">Ошибка соединения с WA Bridge</span>')


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

    if account.type == "tg_user":
        import json

        api_id = settings.telegram_api_id
        api_hash = settings.telegram_api_hash
        if not api_id or not api_hash:
            meta = json.loads(account.session_data or "{}")
            api_id = meta.get("api_id", 0)
            api_hash = meta.get("api_hash", "")

        messenger = TelegramUserMessenger(
            session_string=account.credentials,
            api_id=api_id,
            api_hash=api_hash,
        )
        fetched_groups = await messenger.get_groups()
        messenger_type = "tg_user"

    elif account.type == "wa":
        from app.messengers.whatsapp import WhatsAppMessenger

        messenger = WhatsAppMessenger(bridge_url=settings.wa_bridge_url)
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
                    name=g["name"],
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
    result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.id == account_id,
            MessengerAccount.user_id == user.id,
        )
    )
    account = result.scalar_one_or_none()
    if account:
        await db.delete(account)
        await db.commit()
    return RedirectResponse(url="/accounts", status_code=302)


# ---------------------------------------------------------------------------
# Groups pages
# ---------------------------------------------------------------------------


@router.get("/groups", response_class=HTMLResponse)
async def groups_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Group).where(Group.user_id == user.id).order_by(Group.id)
    )
    groups = result.scalars().all()

    # Load tg_user accounts for sync buttons
    accounts_result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "tg_user",
        )
    )
    tg_user_accounts = accounts_result.scalars().all()

    # Load WA accounts for sync buttons
    wa_accounts_result = await db.execute(
        select(MessengerAccount).where(
            MessengerAccount.user_id == user.id,
            MessengerAccount.type == "wa",
            MessengerAccount.status == "active",
        )
    )
    wa_accounts = wa_accounts_result.scalars().all()

    return templates.TemplateResponse(
        "groups/list.html",
        {
            "request": request,
            "user": user,
            "groups": groups,
            "tg_user_accounts": tg_user_accounts,
            "wa_accounts": wa_accounts,
            "active_page": "groups",
        },
    )


@router.post("/groups/{group_id}/toggle")
async def groups_toggle(
    request: Request,
    group_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.user_id == user.id)
    )
    group = result.scalar_one_or_none()
    if group:
        group.is_active = not group.is_active
        await db.commit()
    return RedirectResponse(url="/groups", status_code=302)


@router.post("/groups/{group_id}/delete")
async def groups_delete(
    request: Request,
    group_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.user_id == user.id)
    )
    group = result.scalar_one_or_none()
    if group:
        await db.delete(group)
        await db.commit()
    return RedirectResponse(url="/groups", status_code=302)


# ---------------------------------------------------------------------------
# Schedules pages
# ---------------------------------------------------------------------------


@router.get("/schedules", response_class=HTMLResponse)
async def schedules_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule, Ad.title.label("ad_title"))
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Ad.user_id == user.id)
        .order_by(Schedule.id)
    )
    schedules = [
        {"schedule": r.Schedule, "ad_title": r.ad_title} for r in result
    ]
    return templates.TemplateResponse(
        "schedules/list.html",
        {
            "request": request,
            "user": user,
            "schedules": schedules,
            "active_page": "schedules",
        },
    )


@router.get("/schedules/new", response_class=HTMLResponse)
async def schedules_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    ads = (
        await db.execute(
            select(Ad).where(Ad.user_id == user.id, Ad.is_active == True)  # noqa: E712
        )
    ).scalars().all()
    accounts = (
        await db.execute(
            select(MessengerAccount).where(MessengerAccount.user_id == user.id)
        )
    ).scalars().all()
    groups = (
        await db.execute(
            select(Group).where(Group.user_id == user.id, Group.is_active == True)  # noqa: E712
        )
    ).scalars().all()

    return templates.TemplateResponse(
        "schedules/form.html",
        {
            "request": request,
            "user": user,
            "schedule": None,
            "ads": ads,
            "accounts": accounts,
            "groups": groups,
            "active_page": "schedules",
        },
    )


@router.post("/schedules/new")
async def schedules_create(
    request: Request,
    ad_id: int = Form(...),
    account_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    form_data = await request.form()
    group_ids = [int(g) for g in form_data.getlist("group_ids")]
    days_of_week = [int(d) for d in form_data.getlist("days_of_week")]
    times_of_day = [t for t in form_data.getlist("times_of_day") if t]

    from app.services.schedule_service import compute_next_run_at

    next_run = compute_next_run_at(
        days_of_week=days_of_week, times_of_day=times_of_day, tz_name="UTC"
    )

    schedule = Schedule(
        ad_id=ad_id,
        account_id=account_id,
        group_ids=group_ids,
        days_of_week=days_of_week,
        times_of_day=times_of_day,
        next_run_at=next_run,
    )
    db.add(schedule)
    await db.commit()
    return RedirectResponse(url="/schedules", status_code=302)


@router.get("/schedules/{schedule_id}/edit", response_class=HTMLResponse)
async def schedules_edit(
    request: Request,
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        return RedirectResponse(url="/schedules", status_code=302)

    ads = (
        await db.execute(
            select(Ad).where(Ad.user_id == user.id, Ad.is_active == True)  # noqa: E712
        )
    ).scalars().all()
    accounts = (
        await db.execute(
            select(MessengerAccount).where(MessengerAccount.user_id == user.id)
        )
    ).scalars().all()
    groups = (
        await db.execute(
            select(Group).where(Group.user_id == user.id, Group.is_active == True)  # noqa: E712
        )
    ).scalars().all()

    return templates.TemplateResponse(
        "schedules/form.html",
        {
            "request": request,
            "user": user,
            "schedule": schedule,
            "ads": ads,
            "accounts": accounts,
            "groups": groups,
            "active_page": "schedules",
        },
    )


@router.post("/schedules/{schedule_id}/edit")
async def schedules_update(
    request: Request,
    schedule_id: int,
    ad_id: int = Form(...),
    account_id: int = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    if not schedule:
        return RedirectResponse(url="/schedules", status_code=302)

    form_data = await request.form()
    group_ids = [int(g) for g in form_data.getlist("group_ids")]
    days_of_week = [int(d) for d in form_data.getlist("days_of_week")]
    times_of_day = [t for t in form_data.getlist("times_of_day") if t]

    from app.services.schedule_service import compute_next_run_at

    schedule.ad_id = ad_id
    schedule.account_id = account_id
    schedule.group_ids = group_ids
    schedule.days_of_week = days_of_week
    schedule.times_of_day = times_of_day
    schedule.next_run_at = compute_next_run_at(
        days_of_week=days_of_week, times_of_day=times_of_day, tz_name="UTC"
    )
    await db.commit()
    return RedirectResponse(url="/schedules", status_code=302)


@router.post("/schedules/{schedule_id}/toggle")
async def schedules_toggle(
    request: Request,
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    if schedule:
        schedule.is_active = not schedule.is_active
        if schedule.is_active:
            from app.services.schedule_service import compute_next_run_at

            schedule.next_run_at = compute_next_run_at(
                days_of_week=schedule.days_of_week,
                times_of_day=schedule.times_of_day,
                tz_name="UTC",
            )
        else:
            schedule.next_run_at = None
        await db.commit()
    return RedirectResponse(url="/schedules", status_code=302)


@router.post("/schedules/{schedule_id}/delete")
async def schedules_delete(
    request: Request,
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    result = await db.execute(
        select(Schedule)
        .join(Ad, Schedule.ad_id == Ad.id)
        .where(Schedule.id == schedule_id, Ad.user_id == user.id)
    )
    schedule = result.scalar_one_or_none()
    if schedule:
        await db.delete(schedule)
        await db.commit()
    return RedirectResponse(url="/schedules", status_code=302)


# ---------------------------------------------------------------------------
# Billing page
# ---------------------------------------------------------------------------


@router.get("/billing", response_class=HTMLResponse)
async def billing_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    plan = await get_user_plan(db, user.id)
    limits = get_plan_limits(plan)
    usage = await get_usage(db, user.id)
    return templates.TemplateResponse(
        "billing/plans.html",
        {
            "request": request,
            "user": user,
            "plan": plan,
            "limits": limits,
            "usage": usage,
            "all_plans": PLANS,
            "active_page": "billing",
        },
    )


# ---------------------------------------------------------------------------
# History pages
# ---------------------------------------------------------------------------


@router.get("/history", response_class=HTMLResponse)
async def history_list(
    request: Request,
    status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    page_size = 50

    query = (
        select(
            SendLog,
            Ad.title.label("ad_title"),
            Group.name.label("group_name"),
        )
        .join(Ad, SendLog.ad_id == Ad.id)
        .join(Group, SendLog.group_id == Group.id)
        .where(Ad.user_id == user.id)
    )
    if status:
        query = query.where(SendLog.status == status)
    query = query.order_by(SendLog.sent_at.desc()).offset(offset).limit(page_size + 1)

    result = await db.execute(query)
    rows = list(result)

    has_next = len(rows) > page_size
    rows = rows[:page_size]

    logs = [
        {
            "ad_title": r.ad_title,
            "group_name": r.group_name,
            "status": r.SendLog.status,
            "error_message": r.SendLog.error_message,
            "sent_at": r.SendLog.sent_at,
        }
        for r in rows
    ]

    return templates.TemplateResponse(
        "history/list.html",
        {
            "request": request,
            "user": user,
            "logs": logs,
            "status_filter": status,
            "offset": offset,
            "page_size": page_size,
            "has_next": has_next,
            "active_page": "history",
        },
    )


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------


@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse(url="/dashboard", status_code=302)
