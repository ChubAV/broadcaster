import random
import structlog
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.models.user import User
from app.models.email_verification import EmailVerificationCode
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_verification_token,
    decode_verification_token,
)
from app.services.email_service import send_verification_email
from app.pages.common import templates

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["pages"])

CODE_LENGTH = 6
CODE_TTL_MINUTES = 10
CODE_MAX_ATTEMPTS = 5
CODE_RESEND_COOLDOWN_SECONDS = 60


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


# ---- Step 1: Enter email ----

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register/send-code", response_class=HTMLResponse)
async def register_send_code(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    # Check if email already registered
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Этот email уже зарегистрирован", "email": email},
        )

    # Rate limit: check last code sent to this email
    result = await db.execute(
        select(EmailVerificationCode)
        .where(EmailVerificationCode.email == email)
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    last_code = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if last_code and (now - last_code.created_at.replace(tzinfo=timezone.utc)).total_seconds() < CODE_RESEND_COOLDOWN_SECONDS:
        token = create_verification_token(email, settings.secret_key)
        return templates.TemplateResponse(
            "auth/register_verify.html",
            {
                "request": request,
                "email": email,
                "token": token,
                "error": "Код уже отправлен. Подождите минуту перед повторной отправкой.",
            },
        )

    # Generate and save code
    code = "".join([str(random.randint(0, 9)) for _ in range(CODE_LENGTH)])
    verification = EmailVerificationCode(
        email=email,
        code=code,
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
    )
    db.add(verification)
    await db.commit()

    # Send email directly (async)
    try:
        if settings.smtp_host:
            await send_verification_email(
                to_email=email,
                code=code,
                smtp_host=settings.smtp_host,
                smtp_port=settings.smtp_port,
                smtp_user=settings.smtp_user,
                smtp_password=settings.smtp_password,
                smtp_from=settings.smtp_from,
                smtp_use_tls=settings.smtp_use_tls,
            )
        else:
            logger.warning("smtp_not_configured", email=email)
    except Exception as e:
        logger.error("verification_email_send_failed", email=email, error=str(e))

    # Create token and show verify page
    token = create_verification_token(email, settings.secret_key)
    return templates.TemplateResponse(
        "auth/register_verify.html",
        {"request": request, "email": email, "token": token},
    )


# ---- Step 2: Verify code ----

@router.post("/register/verify", response_class=HTMLResponse)
async def register_verify(
    request: Request,
    token: str = Form(...),
    code: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    # Decode token to get email
    payload = decode_verification_token(token, settings.secret_key)
    if not payload:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Ссылка устарела. Начните регистрацию заново."},
        )
    email = payload["email"]

    # Find latest non-expired, non-verified code for this email
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.verified_at.is_(None),
            EmailVerificationCode.expires_at > now,
            EmailVerificationCode.attempts < CODE_MAX_ATTEMPTS,
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    code_record = result.scalar_one_or_none()

    if not code_record:
        return templates.TemplateResponse(
            "auth/register_verify.html",
            {
                "request": request,
                "email": email,
                "token": token,
                "error": "Код истёк или превышено число попыток. Отправьте код заново.",
            },
        )

    if code_record.code != code.strip():
        code_record.attempts += 1
        await db.commit()
        remaining = CODE_MAX_ATTEMPTS - code_record.attempts
        return templates.TemplateResponse(
            "auth/register_verify.html",
            {
                "request": request,
                "email": email,
                "token": token,
                "error": f"Неверный код. Осталось попыток: {remaining}",
            },
        )

    # Mark as verified
    code_record.verified_at = now
    await db.commit()

    # Issue verified token
    verified_token = create_verification_token(email, settings.secret_key, verified=True)
    return templates.TemplateResponse(
        "auth/register_complete.html",
        {"request": request, "email": email, "token": verified_token},
    )


@router.post("/register/resend-code", response_class=HTMLResponse)
async def register_resend_code(
    request: Request,
    token: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    payload = decode_verification_token(token, settings.secret_key)
    if not payload:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Ссылка устарела. Начните регистрацию заново."},
        )
    email = payload["email"]

    # Rate limit check
    result = await db.execute(
        select(EmailVerificationCode)
        .where(EmailVerificationCode.email == email)
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    last_code = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if last_code and (now - last_code.created_at.replace(tzinfo=timezone.utc)).total_seconds() < CODE_RESEND_COOLDOWN_SECONDS:
        return templates.TemplateResponse(
            "auth/register_verify.html",
            {
                "request": request,
                "email": email,
                "token": token,
                "error": "Подождите минуту перед повторной отправкой.",
            },
        )

    # Generate new code
    code = "".join([str(random.randint(0, 9)) for _ in range(CODE_LENGTH)])
    verification = EmailVerificationCode(
        email=email,
        code=code,
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
    )
    db.add(verification)
    await db.commit()

    try:
        if settings.smtp_host:
            await send_verification_email(
                to_email=email,
                code=code,
                smtp_host=settings.smtp_host,
                smtp_port=settings.smtp_port,
                smtp_user=settings.smtp_user,
                smtp_password=settings.smtp_password,
                smtp_from=settings.smtp_from,
                smtp_use_tls=settings.smtp_use_tls,
            )
        else:
            logger.warning("smtp_not_configured", email=email)
    except Exception as e:
        logger.error("verification_email_send_failed", email=email, error=str(e))

    new_token = create_verification_token(email, settings.secret_key)
    return templates.TemplateResponse(
        "auth/register_verify.html",
        {
            "request": request,
            "email": email,
            "token": new_token,
            "success": "Новый код отправлен на вашу почту.",
        },
    )


# ---- Step 3: Complete registration ----

@router.post("/register/complete", response_class=HTMLResponse)
async def register_complete(
    request: Request,
    token: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    payload = decode_verification_token(token, settings.secret_key)
    if not payload or not payload.get("verified"):
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Ссылка устарела. Начните регистрацию заново."},
        )
    email = payload["email"]

    # Double-check email not taken
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": "Этот email уже зарегистрирован"},
        )

    if len(password) < 6:
        verified_token = create_verification_token(email, settings.secret_key, verified=True)
        return templates.TemplateResponse(
            "auth/register_complete.html",
            {"request": request, "email": email, "token": verified_token, "error": "Пароль должен быть не менее 6 символов"},
        )

    user = User(email=email, password_hash=hash_password(password), name=name)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(user.id, settings.secret_key)
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="lax")
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse(url="/dashboard", status_code=302)
