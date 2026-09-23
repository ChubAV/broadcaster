import secrets
import structlog
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import forbid_when_impersonating, get_db, get_settings
from app.models.user import User
from app.models.email_verification import EmailVerificationCode
from app.services.auth_service import (
    actor_id,
    decode_access_token,
    hash_password,
    verify_password,
    create_access_token,
    create_verification_token,
    decode_verification_token,
)
from app.services.email_service import send_verification_email, send_password_reset_email
from app.services.subscription_service import start_trial
from app.pages import notices
from app.pages.common import is_same_origin, templates
from app.pages.htmx import (
    redirect_internal,
    respond,
    respond_field_error,
    respond_screen,
)

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["pages"])

# ⚠️ КОД ПОДТВЕРЖДЕНИЯ БЕРЁТСЯ ИЗ КРИПТОГРАФИЧЕСКОГО ИСТОЧНИКА (CR-02).
# Прежний генератор общего назначения — Mersenne Twister: наблюдатель, набравший
# достаточно выходов, восстанавливает состояние генератора и предсказывает
# СЛЕДУЮЩИЕ коды, а выборка добывается бесплатно и легально — коды раздаются
# любому желающему через собственную регистрацию. Цена успеха — захват чужой
# учётки вместе с платёжным путём.
#
# ⚠️ СРОК ЖИЗНИ КОДА И ЛИМИТ ПОПЫТОК ЗДЕСЬ НЕ ЗАЩИТА. Они ограничивают ПЕРЕБОР,
# а предсказание перебором не является: предсказанный код принимается с первой
# попытки и внутри срока. Заменить смену источника ими нельзя.
#
# Форма значения при замене НЕ изменилась: та же длина, те же десятичные цифры,
# тот же тип — сменился только источник, и свидетель этого
# (`tests/test_pages/test_reset_code_source.py`) утверждает ИСТОЧНИК разбором
# дерева модуля, потому что по значению два источника неотличимы.
CODE_LENGTH = 6
CODE_TTL_MINUTES = 10
CODE_MAX_ATTEMPTS = 5
CODE_RESEND_COOLDOWN_SECONDS = 60

SESSION_COOKIE_NAME = "access_token"

# ⚠️ ОТКАЗ ЗАБЛОКИРОВАННОМУ НАЗЫВАЕТСЯ СЛОВАМИ, А НЕ МОЛЧИТ (CR-01, T-06-BL5).
# Молчаливый отказ неотличим для человека от «пароль не подходит»: он пойдёт
# восстанавливать пароль, восстановит, снова не войдёт — и придёт в поддержку с
# «у меня не работает», без единого способа отличить блокировку от поломки.
#
# ПОСТОРОННЕМУ ЭТОТ ТЕКСТ НЕ ДОСТАЁТСЯ (T-06-BL6, disposition `accept`): он
# выдаётся только ПОСЛЕ успешной проверки пароля, то есть тому, кто пароль и
# так знает.
BLOCKED_LOGIN_ERROR = (
    "Учётная запись заблокирована. Обратитесь в поддержку — вход закрыт до "
    "снятия блокировки."
)


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


# ⚠️ ОТВЕТ-ФРАГМЕНТ ЭКРАНА — ОДИН ШАБЛОН НА ВСЕ ЭКРАНЫ (Фаза 14, D-06, D-07).
# Он несёт `<title>` экрана верхним узлом и включает разметку экрана — ту же,
# что включает страница. Страницы этот шаблон не используют.
AUTH_STEP_RESPONSE_TEMPLATE = "auth/includes/step_response.html"


@dataclass(frozen=True)
class AuthScreen:
    """Экран второго шелла: страница, включаемая разметка и заголовок вкладки.

    ⚠️ ЗАГОЛОВОК ФРАГМЕНТА — ЭТА ЗАПИСЬ, А ЗАГОЛОВОК СТРАНИЦЫ — БЛОК `title`
    ЕЁ ШАБЛОНА (D-07). Двум записям одного текста негде разойтись незаметно:
    их сличает правило суиты (`tests/test_pages/test_auth_transport.py`).
    """

    page: str
    step: str
    title: str


# Реестр переведённых экранов. Прочие экраны дописывают планы 14-02…14-05.
# После плана 14-05 в реестре все семь экранов второго шелла.
AUTH_SCREENS: dict[str, AuthScreen] = {
    "login": AuthScreen(
        page="auth/login.html",
        step="auth/includes/login_step.html",
        title="Вход — Broadcaster",
    ),
    # Фаза 14, план 14-02: начало регистрации и экран кода.
    "register": AuthScreen(
        page="auth/register.html",
        step="auth/includes/register_step.html",
        title="Регистрация — Broadcaster",
    ),
    "register_verify": AuthScreen(
        page="auth/register_verify.html",
        step="auth/includes/register_verify_step.html",
        title="Подтверждение email — Broadcaster",
    ),
    # Фаза 14, план 14-03: экран имени и пароля.
    "register_complete": AuthScreen(
        page="auth/register_complete.html",
        step="auth/includes/register_complete_step.html",
        title="Завершение регистрации — Broadcaster",
    ),
    # Фаза 14, план 14-04: начало восстановления пароля и экран его кода.
    "forgot_password": AuthScreen(
        page="auth/forgot_password.html",
        step="auth/includes/forgot_password_step.html",
        title="Забыли пароль — Broadcaster",
    ),
    "forgot_password_verify": AuthScreen(
        page="auth/forgot_password_verify.html",
        step="auth/includes/forgot_password_verify_step.html",
        title="Код подтверждения — Broadcaster",
    ),
    # Фаза 14, план 14-05: экран нового пароля — последний экран второго шелла.
    "forgot_password_reset": AuthScreen(
        page="auth/forgot_password_reset.html",
        step="auth/includes/forgot_password_reset_step.html",
        title="Новый пароль — Broadcaster",
    ),
}


def _screen_markup(screen: str, **context) -> str:
    """Ответ-фрагмент экрана, собранный ОКРУЖЕНИЕМ ШАБЛОНОВ (форма `_max_step_markup`).

    ⚠️ ОДНА РАЗМЕТКА НА СТРАНИЦУ И ФРАГМЕНТ (D-06): обёртка включает тот же
    шаблон экрана, что и страница, — второй копии разметки нет, и разойтись
    им негде. `<title>` берётся из одной записи реестра (D-07).

    ⚠️ ЭКРАНИРОВАНИЕ — ОКРУЖЕНИЯ, А НЕ ЭТОГО ПОМОЩНИКА. Эхо введённого
    уезжает в шаблон параметром; ни фильтра безопасной разметки, ни обёртки
    готовой разметки на этом пути нет.
    """
    entry = AUTH_SCREENS[screen]
    return templates.env.get_template(AUTH_STEP_RESPONSE_TEMPLATE).render(
        screen_title=entry.title, screen_template=entry.step, **context
    )


def _screen_builders(request: Request, screen: str, **context):
    """Пара сборщиков экрана — страница и фрагмент — для выходов слоя ответа.

    Страничный отдаёт шаблон страницы тем же ответом-шаблоном, каким отвечает
    её GET; фрагментный — обёртку ответа с `<title>` верхним узлом. Какой из
    двух позвать, решает слой ответа по транспорту.

    ⚠️ ПАРОЛЬ В КОНТЕКСТ ЭКРАНА НЕ ПЕРЕДАЁТСЯ НИКОГДА (D-04). Шаблон, получивший
    пароль, мог бы однажды его напечатать, и это обнаружилось бы в чужом
    ответе; отказ стоит здесь, у единственного входа в экран. Текст отказа
    значения не подставляет — иначе пароль ушёл бы в журнал трассировкой.
    """
    if "password" in context:
        raise ValueError(
            "пароль не передаётся в контекст экрана авторизации: поле пароля "
            "приходит пустым всегда (D-04)"
        )
    entry = AUTH_SCREENS[screen]

    async def _page():
        """Страница экрана — путь деградации."""
        return templates.TemplateResponse(entry.page, {"request": request, **context})

    async def _fragment():
        """Ответ-фрагмент экрана — содержимое постоянного якоря шага."""
        return HTMLResponse(_screen_markup(screen, **context))

    return _page, _fragment


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
    """Вход страничной формой — на выходах слоя ответа (Фаза 14, план 14-01).

    ⚠️ ОШИБКА — 422 НА ОБОИХ ТРАНСПОРТАХ С ЭХОМ EMAIL (D-03, D-04). Человек
    остаётся на экране входа со своим email; пароль не возвращается никогда —
    поле приходит пустым. Отказ заблокированному — тот же 422 со своими
    словами и без cookie (D-05).

    ⚠️ УСПЕХ — ПОЛНАЯ ЗАГРУЗКА (D-10): без признака htmx 302, с ним 204 и
    заголовок полной перезагрузки. ПОРЯДОК НЕСУЩИЙ: сначала ответ слоя, потом
    cookie на ТОТ ЖЕ объект — cookie на отдельно собранном ответе не уехала бы
    никуда, и вход молча не состоялся бы.

    Решения обработчика прежние (D-15): тексты, порядок «пароль → блокировка →
    cookie» и набор атрибутов cookie не меняются.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    error = None
    if not user or not verify_password(password, user.password_hash):
        error = "Неверный email или пароль"
    # Отказ стоит ДО выдачи cookie — первый из трёх путей блокировки (D-30).
    # До этой правки заблокированный входил СТРАНИЧНОЙ формой как ни в чём не
    # бывало: проверка `is_blocked` стояла только в JSON-маршруте входа, а
    # человек ходит сюда.
    elif user.is_blocked:
        logger.warning("blocked_login_refused", user_id=user.id)
        error = BLOCKED_LOGIN_ERROR
    if error is not None:
        page, fragment = _screen_builders(request, "login", error=error, email=email)
        return await respond_field_error(request, page=page, fragment=fragment)
    token = create_access_token(user.id, settings.secret_key)
    response = await redirect_internal(request, redirect="/dashboard")
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
    """Шаг адреса регистрации — на выходах слоя ответа (Фаза 14, план 14-02).

    ⚠️ КРИТЕРИЙ КОДА — ЭКРАН, А НЕ ТЕКСТ (D-03). 422 — человек остаётся на ТОМ
    ЖЕ экране (адрес занят: экран начала с адресом в поле); 200 — экран
    сменился (код отправлен или «код уже отправлен»: экран кода).

    ⚠️ ЭКРАН КОДА ПРИЕЗЖАЕТ ЦЕЛИКОМ В ПОСТОЯННЫЙ ЯКОРЬ (D-06): обе его формы
    несут подписанный токен скрытым полем, и путь без JavaScript получает
    страницу прямо в ответ на POST — токен в адрес не кладётся (D-08).

    Решения обработчика прежние (D-15): запросы, минута между кодами, срок и
    источник кода, отправка письма и тексты не меняются.
    """
    # Check if email already registered
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        page, fragment = _screen_builders(
            request, "register", error="Этот email уже зарегистрирован", email=email
        )
        return await respond_field_error(request, page=page, fragment=fragment)

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
        page, fragment = _screen_builders(
            request,
            "register_verify",
            email=email,
            token=token,
            error="Код уже отправлен. Подождите минуту перед повторной отправкой.",
        )
        return await respond_screen(request, page=page, fragment=fragment)

    # Generate and save code
    code = "".join([str(secrets.randbelow(10)) for _ in range(CODE_LENGTH)])
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
    page, fragment = _screen_builders(
        request, "register_verify", email=email, token=token
    )
    return await respond_screen(request, page=page, fragment=fragment)


# ---- Step 2: Verify code ----

@router.post("/register/verify", response_class=HTMLResponse)
async def register_verify(
    request: Request,
    token: str = Form(...),
    code: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Подтверждение кода регистрации — на выходах слоя ответа (Фаза 14, план 14-03).

    ⚠️ НЕВЕРНЫЙ КОД НЕ СТИРАЕТ НАБРАННОЕ (D-03, D-04). Кода нет, код истёк,
    попытки кончились или код не тот — 422: человек остаётся на экране кода,
    набранный код стоит в поле, прежний токен — скрытым полем. Устаревшая
    ссылка — 200: экран сменился на начало регистрации. Успех — 200: экран
    имени и пароля с подтверждённым токеном.

    Решения обработчика прежние (D-15): запрос кода, счёт попыток и его запись
    ДО ответа, лимит пять, срок и тексты не меняются — эхо счёта не трогает.
    """
    # Decode token to get email
    payload = decode_verification_token(token, settings.secret_key)
    if not payload:
        page, fragment = _screen_builders(
            request, "register", error="Ссылка устарела. Начните регистрацию заново."
        )
        return await respond_screen(request, page=page, fragment=fragment)
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
        page, fragment = _screen_builders(
            request,
            "register_verify",
            email=email,
            token=token,
            code=code,
            error="Код истёк или превышено число попыток. Отправьте код заново.",
        )
        return await respond_field_error(request, page=page, fragment=fragment)

    if code_record.code != code.strip():
        code_record.attempts += 1
        await db.commit()
        remaining = CODE_MAX_ATTEMPTS - code_record.attempts
        page, fragment = _screen_builders(
            request,
            "register_verify",
            email=email,
            token=token,
            code=code,
            error=f"Неверный код. Осталось попыток: {remaining}",
        )
        return await respond_field_error(request, page=page, fragment=fragment)

    # Mark as verified
    code_record.verified_at = now
    await db.commit()

    # Issue verified token
    verified_token = create_verification_token(email, settings.secret_key, verified=True)
    page, fragment = _screen_builders(
        request, "register_complete", email=email, token=verified_token
    )
    return await respond_screen(request, page=page, fragment=fragment)


@router.post("/register/resend-code", response_class=HTMLResponse)
async def register_resend_code(
    request: Request,
    token: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Повтор кода регистрации — на выходах слоя ответа (Фаза 14, план 14-02).

    ⚠️ КРИТЕРИЙ КОДА — ЭКРАН (D-03). Раньше минуты — 422: человек остаётся на
    экране кода с присланным токеном. Устаревшая ссылка — 200: экран сменился
    на начало регистрации. Успех — 200: экран кода с новым кодом.

    ⚠️ ПОВТОР ВЫДАЁТ НОВЫЙ ТОКЕН, ПОЭТОМУ ПОДМЕНЯЕТСЯ ВЕСЬ ЯКОРЬ (D-06,
    Landmine CONTEXT): подмена одной формы повтора оставила бы форму
    подтверждения со старым токеном.

    Решения обработчика прежние (D-15).
    """
    payload = decode_verification_token(token, settings.secret_key)
    if not payload:
        page, fragment = _screen_builders(
            request, "register", error="Ссылка устарела. Начните регистрацию заново."
        )
        return await respond_screen(request, page=page, fragment=fragment)
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
        page, fragment = _screen_builders(
            request,
            "register_verify",
            email=email,
            token=token,
            error="Подождите минуту перед повторной отправкой.",
        )
        return await respond_field_error(request, page=page, fragment=fragment)

    # Generate new code
    code = "".join([str(secrets.randbelow(10)) for _ in range(CODE_LENGTH)])
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
    page, fragment = _screen_builders(
        request,
        "register_verify",
        email=email,
        token=new_token,
        success="Новый код отправлен на вашу почту.",
    )
    return await respond_screen(request, page=page, fragment=fragment)


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
    """Завершение регистрации — на выходах слоя ответа (Фаза 14, план 14-03).

    ⚠️ КОРОТКИЙ ПАРОЛЬ — 422 С ИМЕНЕМ В ПОЛЕ И БЕЗ ПАРОЛЯ (D-03, D-04): человек
    остаётся на экране завершения, пароль в контекст экрана не передаётся
    вовсе (сборщики его и не примут), токен — новый подтверждённый, как
    сегодня.

    ⚠️ АДРЕС, ЗАНЯТЫЙ К ЗАВЕРШЕНИЮ, — 200, А НЕ 422 (критерий D-03, RESEARCH
    §Карта выходов, Open Question 3). Перечень 422 в D-03 называет «адрес уже
    зарегистрирован», но критерий самого D-03 — остаётся ли человек на ТОМ ЖЕ
    экране. Здесь экран меняется на начало регистрации, значит это смена
    экрана. У шага адреса (`register_send_code`) тот же текст — 422: экран там
    тот же.

    ⚠️ УСПЕХ — ПОЛНАЯ ЗАГРУЗКА (D-10): без признака htmx 302, с ним 204 и
    заголовок полной перезагрузки. Cookie ставится на ТОТ ЖЕ объект, который
    вернул выход слоя, — на отдельно собранном ответе она не уехала бы никуда.

    Решения обработчика прежние (D-15): порядок «пользователь → пробный срок →
    cookie» (D-B), тексты и набор атрибутов cookie не меняются.
    """
    payload = decode_verification_token(token, settings.secret_key)
    if not payload or not payload.get("verified") or payload.get("purpose") != "email_verification":
        page, fragment = _screen_builders(
            request, "register", error="Ссылка устарела. Начните регистрацию заново."
        )
        return await respond_screen(request, page=page, fragment=fragment)
    email = payload["email"]

    # Double-check email not taken
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        page, fragment = _screen_builders(
            request, "register", error="Этот email уже зарегистрирован"
        )
        return await respond_screen(request, page=page, fragment=fragment)

    if len(password) < 6:
        verified_token = create_verification_token(email, settings.secret_key, verified=True)
        page, fragment = _screen_builders(
            request,
            "register_complete",
            email=email,
            token=verified_token,
            name=name,
            error="Пароль должен быть не менее 6 символов",
        )
        return await respond_field_error(request, page=page, fragment=fragment)

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
    response = await redirect_internal(request, redirect="/dashboard")
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


@router.post("/impersonation/stop")
async def stop_impersonation(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """ВЕРНУТЬСЯ В СВОЮ УЧЁТНУЮ ЗАПИСЬ из-под чужой личности (D-19, D-25).

    ⚠️ ВОЗВРАТ ПЕРЕЗАПИСЫВАЕТ COOKIE, А НЕ УДАЛЯЕТ ЕЁ И НЕ ЗАВОДИТ ВТОРУЮ
    (Pitfall 9). Удаление выставляет удаляющую cookie со СВОИМ набором
    атрибутов, и если установка получила признак транспортной защиты, а
    удаление нет, браузер их не сопоставит: старая cookie переживёт возврат —
    администратор остался бы под чужой личностью, будучи уверен, что вышел.
    Единая функция установки, объявленная планом 06-02, снимает этот класс
    ошибок целиком, и возврат обязан ходить через неё. Закреплено сравнением
    НАБОРОВ атрибутов и запретом `delete_cookie` в обработчиках имперсонации.

    ⚠️ ОБРАБОТЧИК ЖИВЁТ ЗДЕСЬ, А НЕ В АДМИНКЕ, И ЭТО ПРЕДМЕТ. Полоса возврата
    рисуется в шелле, то есть на КАЖДОЙ из 26 страниц; маршрут возврата в
    админском роутере означал бы, что вернуться можно только оттуда, куда
    администратор под чужой личностью может и не дойти. Здесь же лежит
    единственная функция установки cookie, через которую возврат обязан идти.

    ⚠️ ПРАВ АДМИНИСТРАТОРА ОБРАБОТЧИК НЕ СПРАШИВАЕТ, И ЭТО НЕ ПОСЛАБЛЕНИЕ.
    Единственный вход сюда — ПРИЗНАК В СОБСТВЕННОМ ПОДПИСАННОМ ТОКЕНЕ
    предъявителя: нет признака — нет и токена на выпуск, обработчик возвращает
    человека туда же, откуда он пришёл, ничего не выдав. Спросить `require_admin`
    значило бы закрыть возврат ровно тому, у кого админство под чужой личностью
    почему-либо не прочиталось, — то есть запереть в чужой учётной записи того,
    кого этот обработчик и должен из неё вывести.

    СРОК ВОЗВРАЩЁННОГО ТОКЕНА — ОБЫЧНЫЙ, а признака действующего лица в нём
    нет: это снова простой вход администратора в свою учётную запись, и
    короткий срок имперсонации к нему не относится.

    ⚠️ ТРИ ВЕТКИ ВОЗВРАТА УХОДЯТ ДВУМЯ РАЗНЫМИ ЗАГОЛОВКАМИ ПЕРЕХОДА, И РАЗНИЦА
    МЕЖДУ НИМИ — ГРАНИЦА ШЕЛЛОВ (Фаза 14, план 14-06, D-12). ДВЕ ветки —
    успех на `/admin` и «действующего лица нет» на `/dashboard` — приземляются
    в ОСНОВНОМ шелле, том же, в котором нарисована полоса возврата, и потому
    уходят заголовком ЧАСТИЧНОГО перехода: рантайм подменяет содержимое `body`
    целиком, полоса `[data-impersonation]` стоит внутри `body` и уезжает
    вместе с ним, а `<title>` становится заголовком приземлившейся страницы
    (RESEARCH Находка 5, вендоренный htmx 2.0.10). ТРЕТЬЯ — «действующего лица
    больше нет либо оно закрыто» — уводит на экран входа, то есть во ВТОРОЙ
    шелл (`auth_base.html`), и уходит ПОЛНОЙ ЗАГРУЗКОЙ: фрагментом смену шелла
    не отдать, подменённым содержимым `body` чужой шелл не собрать. Это и есть
    первая из двух оговорок к буквальному тексту критерия 3 фазы, и записана
    она летописью, а не переписыванием критерия.

    ⚠️ ПОРЯДОК «ОТВЕТ СЛОЯ → COOKIE НА ТОТ ЖЕ ОБЪЕКТ» НЕСУЩИЙ (прецедент
    `admin_impersonate`, `app/pages/admin.py`). Ветка перехода собирает НОВЫЙ
    ответ со статусом 204; cookie, навешенная на отдельно собранный редирект,
    не уехала бы никуда — и отказ был бы МОЛЧАЛИВЫМ: браузер ушёл бы по
    заголовку, а администратор остался бы под чужой личностью. Тест,
    проверяющий ТОЛЬКО заголовок, остался бы при этом зелёным, поэтому пара
    написана ТРОЙНОЙ (`tests/test_pages/test_impersonation.py`): заголовок,
    cookie без признака действующего лица и ФАКТИЧЕСКИ открывшаяся админка.
    """
    if not is_same_origin(request):
        # Возврат — изменяющая операция (перевыпуск токена и перезапись
        # cookie), и гард у неё тот же, что у остальных изменяющих форм.
        #
        # ⚠️ ГОЛЫЙ 403 ОСТАЁТСЯ И ПОСЛЕ ПЕРЕВОДА НА СЛОЙ ОТВЕТА — ЭТО
        # ИМЕНОВАННОЕ ИЗЪЯТИЕ, А НЕ НЕДОДЕЛКА (D-01 Фазы 14, решение владельца
        # 2026-09-22; продление D-08 Фазы 11). Из интерфейса на пути htmx этот
        # отказ недостижим: своя страница шлёт `same-origin`. Цена названа:
        # при редком сбое заголовков у прокси человек увидит общую плашку
        # «Действие не выполнено», а поддельная форма стороннего сайта
        # получает ровно тот же 403, что и до фазы. Выход объявлен записью
        # `OWN_RESPONSE_EXITS` (`tests/test_pages/test_htmx_gates.py`) в
        # состоянии `DECISION_OWNER_D01_F14`.
        return Response(status_code=403)

    token = request.cookies.get(SESSION_COOKIE_NAME)
    payload = decode_access_token(token, settings.secret_key) if token else None
    admin_id = actor_id(payload)
    if admin_id is None:
        # Действующего лица нет — возвращаться неоткуда. Человек уходит туда
        # же, откуда пришёл, и НИ ОДНОГО токена ему не выдаётся.
        #
        # Приземление — в ОСНОВНОМ шелле, поэтому уход идёт заголовком
        # частичного перехода; путь деградации — прежнее перенаправление 302 на
        # тот же адрес (Фаза 14, план 14-06, D-12).
        return await respond(request, redirect="/dashboard")

    admin = await db.get(User, admin_id)
    if admin is None or admin.is_blocked:
        # Учётной записи действующего лица больше нет ЛИБО она закрыта:
        # вернуть человека не к кому. Единственный честный исход — выход, а не
        # молчаливое оставление под чужой личностью.
        #
        # ⚠️ ЗАКРЫТОСТЬ ДЕЙСТВУЮЩЕГО ЛИЦА СПРАШИВАЕТСЯ ЗДЕСЬ, ХОТЯ ПРАВА — НЕТ,
        # И РАЗНИЦА НЕ В СТРОГОСТИ (WR-02 ревизии фазы 6). Выход отсюда —
        # ВЫПУСК ПОЛНОГО СУТОЧНОГО ТОКЕНА, и без этой ветки администратор,
        # заблокированный ВО ВРЕМЯ шестидесятиминутного окна имперсонации,
        # выходил бы из него со свежим сеансом на учётную запись, доступ
        # которой только что отозвали, — то есть блокировка снималась бы
        # действием самого заблокированного.
        #
        # ⚠️ АДМИНСТВО ЗДЕСЬ НЕ ПЕРЕСПРАШИВАЕТСЯ, И ЭТО НЕ ЗАБЫТАЯ ПОЛОВИНА.
        # Возврат в СВОЮ учётную запись привилегией не является: разжалованный
        # администратор получает обычный сеанс обычного пользователя, а в
        # админку его всё равно не пустит `require_admin`. Требование прав
        # здесь заперло бы в чужой учётной записи ровно того, кого этот
        # обработчик обязан из неё вывести, — довод, уже выписанный в
        # докстринге выше.
        #
        # ⚠️ ЕДИНСТВЕННАЯ ВЕТКА ВОЗВРАТА, УХОДЯЩАЯ ПОЛНОЙ ЗАГРУЗКОЙ (Фаза 14,
        # план 14-06, D-12): экран входа живёт во ВТОРОМ шелле, и подменённым
        # содержимым `body` его не собрать. Cookie снимается на ВОЗВРАЩЁННОМ
        # объекте — тем же набором атрибутов, каким она поставлена.
        response = await redirect_internal(request, redirect="/login")
        clear_session_cookie(response, settings)
        return response

    response = await respond(request, redirect="/admin")
    set_session_cookie(
        response, create_access_token(admin.id, settings.secret_key), settings
    )

    logger.info(
        "impersonation_stop",
        admin_user_id=admin.id,
        target_user_id=payload["sub"],
    )
    return response


# ---- Forgot Password ----
#
# ⚠️ ВЕСЬ ЭТОТ ПУТЬ ЗАПРЕЩЁН ПОД ЧУЖОЙ ЛИЧНОСТЬЮ (D-22), И ЗАПРЕТ НАВЕШЕН
# ПОМАРШРУТНО, А НЕ НА РОУТЕР. Роутер авторизации закрывать целиком НЕЛЬЗЯ: в
# нём живут вход, регистрация и возврат из имперсонации — закрыв его, мы лишили
# бы продукт входа, а администратора под чужой личностью — пути назад. Ровно
# этот случай и делает чисто пер-роутерную форму запрета недостаточной.
#
# ЗАКРЫТЫ ВСЕ ЧЕТЫРЕ ШАГА, А НЕ ТОЛЬКО ПОСЛЕДНИЙ. Закрытый один лишь `reset`
# оставил бы администратору три первых: код ушёл бы НА ПОЧТУ ПОЛЬЗОВАТЕЛЯ, то
# есть захват учётной записи начался бы и остановился на полпути — с письмом,
# которого пользователь не просил, и с поводом для обращения в поддержку на
# ровном месте.
#
# ⚠️ ОБЫЧНОГО ЧЕЛОВЕКА ЭТО НЕ ЗАДЕВАЕТ: у запроса без действующего лица
# зависимость отказа не даёт вовсе. Восстановление пароля остаётся открытым
# всем, включая незалогиненного, — а он и есть его основной посетитель.

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("auth/forgot_password.html", {"request": request})


@router.post("/forgot-password/send-code", response_class=HTMLResponse)
async def forgot_password_send_code(
    request: Request,
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _under_another_identity: None = Depends(forbid_when_impersonating),
):
    """Шаг адреса восстановления — на выходах слоя ответа (Фаза 14, план 14-04).

    ⚠️ КРИТЕРИЙ КОДА — ЭКРАН, А НЕ ТЕКСТ (D-03). 422 — человек остаётся на ТОМ
    ЖЕ экране (адрес не найден: экран начала с адресом в поле); 200 — экран
    сменился (код отправлен или «код уже отправлен»: экран кода).

    ⚠️ ЭКРАН КОДА ПРИЕЗЖАЕТ ЦЕЛИКОМ В ПОСТОЯННЫЙ ЯКОРЬ (D-06): обе его формы
    несут подписанный токен восстановления скрытым полем, и путь без
    JavaScript получает страницу прямо в ответ на POST — токен в адрес не
    кладётся (D-08).

    ⚠️ ОТКАЗ ПОД ЧУЖОЙ ЛИЧНОСТЬЮ — ЗАВИСИМОСТИ, И ОНА НЕ ТРОНУТА (D-13, D-22):
    до тела обработчика запрос под чужой личностью не доходит вовсе.

    Решения обработчика прежние (D-15): запросы, минута между кодами, срок и
    источник кода, отправка письма и тексты не меняются.
    """
    # Check if email exists
    existing = await db.execute(select(User).where(User.email == email))
    if not existing.scalar_one_or_none():
        page, fragment = _screen_builders(
            request,
            "forgot_password",
            error="Пользователь с таким email не найден",
            email=email,
        )
        return await respond_field_error(request, page=page, fragment=fragment)

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
        page, fragment = _screen_builders(
            request,
            "forgot_password_verify",
            email=email,
            token=token,
            error="Код уже отправлен. Подождите минуту перед повторной отправкой.",
        )
        return await respond_screen(request, page=page, fragment=fragment)

    # Generate and save code
    code = "".join([str(secrets.randbelow(10)) for _ in range(CODE_LENGTH)])
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
    page, fragment = _screen_builders(
        request, "forgot_password_verify", email=email, token=token
    )
    return await respond_screen(request, page=page, fragment=fragment)


@router.post("/forgot-password/verify", response_class=HTMLResponse)
async def forgot_password_verify(
    request: Request,
    token: str = Form(...),
    code: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _under_another_identity: None = Depends(forbid_when_impersonating),
):
    """Подтверждение кода восстановления — на выходах слоя ответа (Фаза 14, план 14-05).

    ⚠️ НЕВЕРНЫЙ КОД НЕ СТИРАЕТ НАБРАННОЕ (D-03, D-04). Кода нет, код истёк,
    попытки кончились или код не тот — 422: человек остаётся на экране кода,
    набранный код стоит в поле, прежний токен — скрытым полем. Устаревшая
    ссылка — 200: экран сменился на начало восстановления. Успех — 200: экран
    нового пароля с подтверждённым токеном.

    Отказ под чужой личностью — зависимости, она не тронута (D-13, D-22).
    Решения обработчика прежние (D-15): запрос кода, счёт попыток и его запись
    ДО ответа, лимит пять, срок и тексты не меняются — эхо счёта не трогает.
    """
    payload = decode_verification_token(token, settings.secret_key)
    if not payload or payload.get("purpose") != "password_reset":
        page, fragment = _screen_builders(
            request,
            "forgot_password",
            error="Ссылка устарела. Начните сброс пароля заново.",
        )
        return await respond_screen(request, page=page, fragment=fragment)
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
        page, fragment = _screen_builders(
            request,
            "forgot_password_verify",
            email=email,
            token=token,
            code=code,
            error="Код истёк или превышено число попыток. Отправьте код заново.",
        )
        return await respond_field_error(request, page=page, fragment=fragment)

    if code_record.code != code.strip():
        code_record.attempts += 1
        await db.commit()
        remaining = CODE_MAX_ATTEMPTS - code_record.attempts
        page, fragment = _screen_builders(
            request,
            "forgot_password_verify",
            email=email,
            token=token,
            code=code,
            error=f"Неверный код. Осталось попыток: {remaining}",
        )
        return await respond_field_error(request, page=page, fragment=fragment)

    code_record.verified_at = now
    await db.commit()

    verified_token = create_verification_token(email, settings.secret_key, verified=True, purpose="password_reset")
    page, fragment = _screen_builders(
        request, "forgot_password_reset", email=email, token=verified_token
    )
    return await respond_screen(request, page=page, fragment=fragment)


@router.post("/forgot-password/resend-code", response_class=HTMLResponse)
async def forgot_password_resend_code(
    request: Request,
    token: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _under_another_identity: None = Depends(forbid_when_impersonating),
):
    """Повтор кода восстановления — на выходах слоя ответа (Фаза 14, план 14-04).

    ⚠️ КРИТЕРИЙ КОДА — ЭКРАН (D-03). Раньше минуты — 422: человек остаётся на
    экране кода с присланным токеном. Устаревшая ссылка — 200: экран сменился
    на начало восстановления. Успех — 200: экран кода с новым кодом.

    ⚠️ ПОВТОР ВЫДАЁТ НОВЫЙ ТОКЕН, ПОЭТОМУ ПОДМЕНЯЕТСЯ ВЕСЬ ЯКОРЬ (D-06,
    Landmine CONTEXT): подмена одной формы повтора оставила бы форму
    подтверждения со старым токеном.

    Отказ под чужой личностью — зависимости, она не тронута (D-13, D-22).
    Решения обработчика прежние (D-15).
    """
    payload = decode_verification_token(token, settings.secret_key)
    if not payload or payload.get("purpose") != "password_reset":
        page, fragment = _screen_builders(
            request,
            "forgot_password",
            error="Ссылка устарела. Начните сброс пароля заново.",
        )
        return await respond_screen(request, page=page, fragment=fragment)
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
        page, fragment = _screen_builders(
            request,
            "forgot_password_verify",
            email=email,
            token=token,
            error="Подождите минуту перед повторной отправкой.",
        )
        return await respond_field_error(request, page=page, fragment=fragment)

    code = "".join([str(secrets.randbelow(10)) for _ in range(CODE_LENGTH)])
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
    page, fragment = _screen_builders(
        request,
        "forgot_password_verify",
        email=email,
        token=new_token,
        success="Новый код отправлен на вашу почту.",
    )
    return await respond_screen(request, page=page, fragment=fragment)


@router.post("/forgot-password/reset", response_class=HTMLResponse)
async def forgot_password_reset(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _under_another_identity: None = Depends(forbid_when_impersonating),
):
    """Новый пароль — на выходах слоя ответа (Фаза 14, план 14-05).

    ⚠️ КОРОТКИЙ ПАРОЛЬ — 422 БЕЗ ПАРОЛЯ (D-03, D-04): человек остаётся на экране
    нового пароля, пароль в контекст экрана не передаётся вовсе (сборщики его и
    не примут), токен — новый подтверждённый, как сегодня. Устаревшая ссылка и
    исчезнувший пользователь — 200: экран сменился на начало восстановления.

    ⚠️ УСПЕХ — ПОЛНАЯ ЗАГРУЗКА НА ВХОД (D-10): без признака htmx 302, с ним 204
    и заголовок полной перезагрузки на тот же адрес с кодом исхода. Cookie
    сессии смена пароля не выдаёт: человек входит новым паролем сам.

    Отказ под чужой личностью — зависимости, она не тронута (D-13, D-22).
    Решения обработчика прежние (D-15): проверки, их порядок, хеш и тексты не
    меняются.
    """
    payload = decode_verification_token(token, settings.secret_key)
    if not payload or not payload.get("verified") or payload.get("purpose") != "password_reset":
        page, fragment = _screen_builders(
            request,
            "forgot_password",
            error="Ссылка устарела. Начните сброс пароля заново.",
        )
        return await respond_screen(request, page=page, fragment=fragment)
    email = payload["email"]

    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        page, fragment = _screen_builders(
            request, "forgot_password", error="Пользователь не найден."
        )
        return await respond_screen(request, page=page, fragment=fragment)

    if len(password) < 6:
        verified_token = create_verification_token(email, settings.secret_key, verified=True, purpose="password_reset")
        page, fragment = _screen_builders(
            request,
            "forgot_password_reset",
            email=email,
            token=verified_token,
            error="Пароль должен быть не менее 6 символов",
        )
        return await respond_field_error(request, page=page, fragment=fragment)

    user.password_hash = hash_password(password)
    await db.commit()

    # ИСХОД ЕДЕТ ОДНИМ ПАРАМЕТРОМ И КОДОМ ИЗ РЕЕСТРА (FOUND-05). Прежде здесь
    # стояло СОБСТВЕННОЕ написание, а слова к нему набирались прямо в разметке
    # экрана входа — то есть у одного исхода были и свой канал, и свой владелец
    # слов. Не осталось ни того, ни другого: код выбирает запись реестра
    # (`app/pages/notices.py`), а рисует её общая область шелла — та же, что и
    # на всех остальных экранах обоих шеллов.
    # На пути htmx — полная загрузка тем же адресом (D-10).
    return await redirect_internal(request, redirect="/login", notice=notices.PASSWORD_RESET_DONE)


@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    return RedirectResponse(url="/dashboard", status_code=302)
