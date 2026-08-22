import random
import structlog
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Form, Request, Response
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
from app.services.email_service import send_verification_email, send_password_reset_email
from app.services.subscription_service import start_trial
from app.pages.common import templates

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["pages"])

CODE_LENGTH = 6
CODE_TTL_MINUTES = 10
CODE_MAX_ATTEMPTS = 5
CODE_RESEND_COOLDOWN_SECONDS = 60

SESSION_COOKIE_NAME = "access_token"


def _session_cookie_attrs(settings: Settings) -> dict:
    """ЕДИНСТВЕННОЕ объявление набора атрибутов cookie сессии.

    ⚠️ НАБОР ОБЪЯВЛЕН ОДИН РАЗ, И ЭТО ПРЕДМЕТ, А НЕ ЭКОНОМИЯ ПЕЧАТИ (Pitfall 9).
    Браузер сопоставляет cookie установки и снятия по имени, пути и домену, а
    `secure` определяет, уйдёт ли она вообще. Пока набор объявлялся отдельно у
    каждой точки, снятие брало умолчания `delete_cookie` — без `samesite` и без
    `secure`, — и стоило установке получить признак транспортной защиты, как
    выход переставал снимать cookie: она переживала выход. На равенство этих
    наборов встаёт и перевыпуск токена при возврате из имперсонации (план
    06-12): он ПЕРЕЗАПИСЫВАЕТ cookie тем же набором, а не заводит вторую.

    ⚠️ СРОКА ЖИЗНИ У COOKIE НЕТ НАМЕРЕННО. Она сеансовая, такой была до правки
    признака `secure`, и этот набор её таковой оставляет: `max_age`/`expires`
    здесь появиться не должны молча — это отдельное решение о том, переживает
    ли вход закрытие браузера.

    Признак транспортной защиты читается из НАСТРОЙКИ, а не из литерала
    (CR-03, Ф-9): прод-nginx сам уходит в HTTP-only режим при отсутствии
    сертификата, и невыключаемый признак в этот момент отменил бы вход целиком.
    Разбор умолчания — в `app/config.py` у поля `cookie_secure`.
    """
    return {
        "path": "/",
        "httponly": True,
        "samesite": "lax",
        "secure": settings.cookie_secure,
    }


def set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    """Поставить cookie сессии — единственная точка установки в модуле."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME, value=token, **_session_cookie_attrs(settings)
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    """Снять cookie сессии ТЕМ ЖЕ набором атрибутов, каким она поставлена."""
    response.delete_cookie(key=SESSION_COOKIE_NAME, **_session_cookie_attrs(settings))


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
    set_session_cookie(response, token, settings)
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
        .where(EmailVerificationCode.purpose == "registration")
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
        purpose="registration",
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
            EmailVerificationCode.purpose == "registration",
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
        .where(EmailVerificationCode.purpose == "registration")
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
        purpose="registration",
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
    if not payload or not payload.get("verified") or payload.get("purpose") != "email_verification":
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

    # ПРОБНЫЙ СРОК ЗАВОДИТСЯ ДО ВЫДАЧИ COOKIE, И ПОРЯДОК ЗДЕСЬ НЕСУЩИЙ (D-B).
    # Cookie, выданная раньше строки подписки, уводит человека на `/dashboard`,
    # где первый же рендер шелла увидит пользователя БЕЗ доступа — то есть новый
    # пользователь встретит продукт закрытым в ту же секунду, как в него вошёл.
    #
    # Заведение вызывается ОДНОЙ функцией, общей со вторым путём регистрации
    # (`POST /api/auth/register`, `app/routes/auth.py`): копия тела здесь
    # развела бы длину пробного периода по двум входам регистрации.
    await start_trial(db, user.id)
    await db.commit()

    access_token = create_access_token(user.id, settings.secret_key)
    response = RedirectResponse(url="/dashboard", status_code=302)
    set_session_cookie(response, access_token, settings)
    return response


@router.get("/logout")
async def logout(settings: Settings = Depends(get_settings)):
    # Настройки нужны ВЫХОДУ, хотя он ничего не читает из БД: снятие обязано
    # объявить тот же набор атрибутов, что и установка, а он зависит от
    # признака транспортной защиты (Pitfall 9). Без этой зависимости снятие
    # ушло бы на умолчания `delete_cookie`, и cookie пережила бы выход.
    response = RedirectResponse(url="/login", status_code=302)
    clear_session_cookie(response, settings)
    return response


# ---- Forgot Password ----

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("auth/forgot_password.html", {"request": request})


@router.post("/forgot-password/send-code", response_class=HTMLResponse)
async def forgot_password_send_code(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    # Check if email exists
    existing = await db.execute(select(User).where(User.email == email))
    if not existing.scalar_one_or_none():
        return templates.TemplateResponse(
            "auth/forgot_password.html",
            {"request": request, "error": "Пользователь с таким email не найден", "email": email},
        )

    # Rate limit: check last code sent to this email for password_reset
    result = await db.execute(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.purpose == "password_reset",
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    last_code = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if last_code and (now - last_code.created_at.replace(tzinfo=timezone.utc)).total_seconds() < CODE_RESEND_COOLDOWN_SECONDS:
        token = create_verification_token(email, settings.secret_key, purpose="password_reset")
        return templates.TemplateResponse(
            "auth/forgot_password_verify.html",
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
        purpose="password_reset",
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
    )
    db.add(verification)
    await db.commit()

    # Send email
    try:
        if settings.smtp_host:
            await send_password_reset_email(
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
        logger.error("password_reset_email_send_failed", email=email, error=str(e))

    token = create_verification_token(email, settings.secret_key, purpose="password_reset")
    return templates.TemplateResponse(
        "auth/forgot_password_verify.html",
        {"request": request, "email": email, "token": token},
    )


@router.post("/forgot-password/verify", response_class=HTMLResponse)
async def forgot_password_verify(
    request: Request,
    token: str = Form(...),
    code: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    payload = decode_verification_token(token, settings.secret_key)
    if not payload or payload.get("purpose") != "password_reset":
        return templates.TemplateResponse(
            "auth/forgot_password.html",
            {"request": request, "error": "Ссылка устарела. Начните сброс пароля заново."},
        )
    email = payload["email"]

    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.purpose == "password_reset",
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
            "auth/forgot_password_verify.html",
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
            "auth/forgot_password_verify.html",
            {
                "request": request,
                "email": email,
                "token": token,
                "error": f"Неверный код. Осталось попыток: {remaining}",
            },
        )

    code_record.verified_at = now
    await db.commit()

    verified_token = create_verification_token(email, settings.secret_key, verified=True, purpose="password_reset")
    return templates.TemplateResponse(
        "auth/forgot_password_reset.html",
        {"request": request, "email": email, "token": verified_token},
    )


@router.post("/forgot-password/resend-code", response_class=HTMLResponse)
async def forgot_password_resend_code(
    request: Request,
    token: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    payload = decode_verification_token(token, settings.secret_key)
    if not payload or payload.get("purpose") != "password_reset":
        return templates.TemplateResponse(
            "auth/forgot_password.html",
            {"request": request, "error": "Ссылка устарела. Начните сброс пароля заново."},
        )
    email = payload["email"]

    # Rate limit check
    result = await db.execute(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.purpose == "password_reset",
        )
        .order_by(EmailVerificationCode.created_at.desc())
        .limit(1)
    )
    last_code = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if last_code and (now - last_code.created_at.replace(tzinfo=timezone.utc)).total_seconds() < CODE_RESEND_COOLDOWN_SECONDS:
        return templates.TemplateResponse(
            "auth/forgot_password_verify.html",
            {
                "request": request,
                "email": email,
                "token": token,
                "error": "Подождите минуту перед повторной отправкой.",
            },
        )

    code = "".join([str(random.randint(0, 9)) for _ in range(CODE_LENGTH)])
    verification = EmailVerificationCode(
        email=email,
        code=code,
        purpose="password_reset",
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
    )
    db.add(verification)
    await db.commit()

    try:
        if settings.smtp_host:
            await send_password_reset_email(
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
        logger.error("password_reset_email_send_failed", email=email, error=str(e))

    new_token = create_verification_token(email, settings.secret_key, purpose="password_reset")
    return templates.TemplateResponse(
        "auth/forgot_password_verify.html",
        {
            "request": request,
            "email": email,
            "token": new_token,
            "success": "Новый код отправлен на вашу почту.",
        },
    )


@router.post("/forgot-password/reset", response_class=HTMLResponse)
async def forgot_password_reset(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    payload = decode_verification_token(token, settings.secret_key)
    if not payload or not payload.get("verified") or payload.get("purpose") != "password_reset":
        return templates.TemplateResponse(
            "auth/forgot_password.html",
            {"request": request, "error": "Ссылка устарела. Начните сброс пароля заново."},
        )
    email = payload["email"]

    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return templates.TemplateResponse(
            "auth/forgot_password.html",
            {"request": request, "error": "Пользователь не найден."},
        )

    if len(password) < 6:
        verified_token = create_verification_token(email, settings.secret_key, verified=True, purpose="password_reset")
        return templates.TemplateResponse(
            "auth/forgot_password_reset.html",
            {"request": request, "email": email, "token": verified_token, "error": "Пароль должен быть не менее 6 символов"},
        )

    user.password_hash = hash_password(password)
    await db.commit()

    response = RedirectResponse(url="/login?reset=success", status_code=302)
    return response


@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse(url="/dashboard", status_code=302)
