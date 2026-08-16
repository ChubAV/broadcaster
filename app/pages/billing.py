from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import normalize_utc
from app.application.billing.plan_usage import plan_axes
from app.config import Settings
from app.constants import PAYMENT_LIST_CAP
from app.dependencies import get_db, get_settings
from app.services.billing_service import (
    count_payments,
    get_balance_info,
    get_payment_history,
    get_transaction_history,
)
from app.services.payment_service import (
    KIND_PACKAGE,
    KIND_SUBSCRIPTION,
    create_payment,
)
from app.pages.common import (
    check_is_admin,
    get_user_from_cookie,
    is_same_origin,
    templates,
)

router = APIRouter(tags=["pages"])

# Бесплатный тариф не продаётся: платёж на «0.00» ЮKassa отвергнет, а если бы и
# принял — покупать нечего. Идентификатор выписан здесь, потому что решение
# «этот план не является предметом покупки» принадлежит маршруту покупки, а не
# конфигу, где план описан наравне с остальными.
FREE_PLAN_ID = "free"

# Потолок истории операций по балансу сообщений. Это ДРУГОЙ журнал и другой
# потолок: он считает штуки сообщений и живёт своим блоком экрана.
TRANSACTION_LIST_LIMIT = 20


@router.get("/billing", response_class=HTMLResponse)
async def billing_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Раздел «Тарифы» целиком: пять блоков экрана одним маршрутом (D-18).

    Сверху вниз: текущий тариф и срок → четыре оси тарифа → карточки планов →
    баланс сообщений и пакеты → история платежей. НИ ТАБОВ, НИ ВТОРОГО
    МАРШРУТА: табы в макете есть только у админки, и заводить здесь новый
    компонент раньше срока значило бы разложить один ответ на вопрос «что у
    меня с тарифом» по нескольким экранам.

    СТРАНИЦА НИЧЕГО НЕ АГРЕГИРУЕТ. Все числа приходят из модулей, которые зовёт
    не только этот экран: оси — из `plan_axes`, деньги — из журнала платежей,
    сообщения — из журнала операций. Своего запроса обработчик не пишет.

    ⚠️ ОБРАБОТЧИК НЕ ПИШЕТ В БД НИ ПРИ КАКИХ УСЛОВИЯХ (D-05, T-05-24). Сюда
    приводит `return_url` ЮKassa, и редирект браузера происходит ТАКЖЕ ПРИ
    ОТКАЗЕ ОТ ОПЛАТЫ. Ленивое создание подписки на рендере — самое лёгкое
    место, где раздел начал бы раздавать платный ресурс бесплатно, поэтому
    обработчика возврата в проекте нет вовсе, а срок двигает только вебхук.
    Пользователь, вернувшийся до прихода уведомления, видит свой платёж СТРОКОЙ
    истории в статусе «в обработке» — то есть узнаёт, что деньги в обработке, а
    не что оплата не прошла.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Тариф и срок берутся из УЖЕ ПОСЧИТАННОГО контекста шелла, вторым запросом
    # не считаются: показатель один — источник обязан быть один (D-09/D-19).
    shell = getattr(request.state, "shell", None) or {}
    quota = shell.get("quota", {})
    nav_counts = shell.get("nav_counts", {})

    # JSON разбирается ОДИН раз в обработчике, а не свойством из цикла Jinja:
    # `parsed_plan_limits` кэша не имеет (`@lru_cache` стоит на `get_settings`,
    # а не на нём), и вызов из шаблона парсил бы строку на каждой итерации.
    plans = settings.parsed_plan_limits
    current_plan_id = quota.get("plan", FREE_PLAN_ID)
    # Отсутствующая запись плана читается как «лимитов нет», а не как падение:
    # перечень тарифов правится переменной окружения, и опечатка в ней обязана
    # стоить ненарисованных шкал, а не пятисотки на странице тарифов.
    current_plan = next(
        (plan for plan in plans if plan.get("id") == current_plan_id), {}
    )

    # `nav_counts` приезжает ИЗ ШЕЛЛА, а не из тела запроса (T-05-17): два
    # числителя из четырёх уже посчитаны на этом же запросе, и второй их
    # источник разошёлся бы с навигационным счётчиком, стоящим рядом на экране.
    usage = await plan_axes(
        db, user=user, limits=current_plan, nav_counts=nav_counts
    )

    balance_info = await get_balance_info(db, user.id)
    transactions = await get_transaction_history(
        db, user.id, limit=TRANSACTION_LIST_LIMIT
    )

    # ПОТОЛОК СВЕРЯЕТСЯ ДО КОНСТРУИРОВАНИЯ СПИСКА (D-17), приёмом потолка
    # выгрузки истории. Вывести срабатывание из длины уже выбранного списка
    # нельзя: ровно на потолке список полон, и «показано не всё» стало бы
    # неотличимо от «столько и есть». Тихая обрезка запрещена — молча короткий
    # журнал денег читается как «других платежей не было».
    payments_total = await count_payments(db, user.id)
    payments = await get_payment_history(db, user.id, limit=PAYMENT_LIST_CAP)

    # Срок сравнивается через `normalize_utc`: колонка объявлена с таймзоной,
    # но SQLite отдаёт её naive, а PostgreSQL aware — сравнение без приведения
    # падало бы TypeError ровно на одном из двух диалектов, то есть только в
    # проде либо только в тестах.
    expires_at = quota.get("expires_at")
    normalized_expiry = normalize_utc(expires_at)
    # ⚠️ ИСТЕЧЕНИЕ СРОКА НИЧЕГО НЕ ОТКЛЮЧАЕТ (D-07). Применения лимитов в
    # системе нет вовсе, и вводить принуждение по сроку в фазе, которая
    # сознательно не вводит принуждение по лимитам, значило бы завести два
    # разных ответа на один вопрос. Истёкшая подписка меняет только показ.
    expired = (
        normalized_expiry is not None
        and normalized_expiry < datetime.now(timezone.utc)
    )

    return templates.TemplateResponse(
        "billing/balance.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "subscription": {
                "plan": current_plan_id,
                "expires_at": expires_at,
                "expired": expired,
            },
            "usage": usage,
            "plans": plans,
            "balance_info": balance_info,
            "packages": (
                settings.parsed_message_packages if settings.yookassa_enabled else []
            ),
            "transactions": transactions,
            "payments": payments,
            "payments_total": payments_total,
            "payments_cap": PAYMENT_LIST_CAP,
            "payments_truncated": payments_total > PAYMENT_LIST_CAP,
            "payments_enabled": settings.yookassa_enabled,
            "active_page": "billing",
        },
    )


@router.post("/billing/subscribe")
async def subscribe_to_plan(
    request: Request,
    plan: str = Form(""),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Заводит платёж за тариф и уводит пользователя на страницу оплаты ЮKassa.

    ИЗ ФОРМЫ ПРИЕЗЖАЕТ ТОЛЬКО ИДЕНТИФИКАТОР ПЛАНА. Цена и лимиты читаются из
    настроек ПО ЭТОМУ ИДЕНТИФИКАТОРУ — иначе покупатель назначает себе цену
    подменой поля формы (T-05-03). Неизвестный идентификатор возвращает на
    раздел, а НЕ выбирает «умолчание»: умолчание здесь означало бы продать не
    то, что нажали. Пустое умолчание у поля — по той же причине, что у соседней
    формы покупки пакета: обязательное поле, пришедшее пустым, FastAPI считает
    отсутствующим и отвечает 422 ещё до входа в обработчик, то есть страницей
    разбора запроса вместо возврата в раздел.

    ПОРЯДОК ПРОВЕРОК повторяет app/pages/history.py:946-961: сначала кто
    пришёл, потом откуда пришёл, потом что просит. Сверка источника стоит ДО
    любого обращения к БД и до создания платежа.

    СРОК ПОДПИСКИ ЭТОТ ОБРАБОТЧИК НЕ ТРОГАЕТ. Он создаёт намерение оплатить;
    оплату подтверждает только вебхук (D-05). Обработчика возврата с ЮKassa в
    проекте нет намеренно: редирект браузера происходит и при отказе от оплаты.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if not is_same_origin(request):
        return Response(status_code=403)

    if not settings.yookassa_enabled:
        return RedirectResponse(url="/billing", status_code=302)

    selected = next(
        (p for p in settings.parsed_plan_limits if p.get("id") == plan), None
    )
    if selected is None or selected.get("id") == FREE_PLAN_ID:
        return RedirectResponse(url="/billing", status_code=302)

    result = await create_payment(
        db,
        user_id=user.id,
        # Предмет покупки — КОНСТАНТОЙ, никогда голым литералом (WR-04):
        # опечатка в литерале не падает громко, а уводит подписочный платёж в
        # пакетную ветку вебхука с пустым `messages_count`.
        kind=KIND_SUBSCRIPTION,
        plan=selected["id"],
        price=selected["price"],
        package_name=None,
        messages_count=None,
    )
    return RedirectResponse(url=result["confirmation_url"], status_code=302)


@router.post("/billing/purchase")
async def purchase_package(
    request: Request,
    package_index: str = Form(""),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Заводит платёж за пакет сообщений и уводит на страницу оплаты ЮKassa.

    ОБЕ ОПЛАТЫ РАЗДЕЛА ЖИВУТ В ОДНОМ МОДУЛЕ и делят один порядок проверок —
    дословно тот же, что у повтора отправки: кто пришёл → откуда пришёл →
    включены ли платежи → что просит. Второй порядок проверок на соседнем
    входе означал бы, что усиление одного не усиливает другой.

    ИЗ ФОРМЫ ПРИЕЗЖАЕТ ТОЛЬКО ИНДЕКС ПАКЕТА (T-05-22). Цена и число сообщений
    читаются из конфига ПО ЭТОМУ ИНДЕКСУ; поля с ценой или количеством в теле
    запроса игнорируются, потому что иначе покупатель назначает себе цену.

    ИНДЕКС ПРИНИМАЕТСЯ СТРОКОЙ С ПУСТЫМ УМОЛЧАНИЕМ И РАЗБИРАЕТСЯ ЗДЕСЬ.
    Объявление его целым дало бы на нечисловом значении 422 со страницей
    разбора запроса — ответ для клиента JSON-API, а не для человека, нажавшего
    кнопку. Умолчание нужно по той же причине: обязательное поле формы,
    пришедшее ПУСТЫМ, FastAPI считает отсутствующим и отвечает тем же 422 ещё
    до входа в обработчик. Любое непригодное значение — пустое, нечисловое,
    отрицательное, вне диапазона — возвращает в раздел, и НИКОГДА не выбирает
    «умолчание по смыслу»: оно продало бы не то, что нажали.

    ⚠️ ЭТОТ ОБРАБОТЧИК — ЗАМЕНА JSON-МАРШРУТУ ПОКУПКИ (D-20, D-24). Тот
    возвращал `yookassa_payment_id` прямо в браузер, а идентификатор платежа —
    ключ подделки уведомления. Форма отдаёт 302 на страницу оплаты, и
    идентификатор наружу не попадает вовсе.
    """
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if not is_same_origin(request):
        return Response(status_code=403)

    if not settings.yookassa_enabled:
        return RedirectResponse(url="/billing", status_code=302)

    packages = settings.parsed_message_packages
    try:
        index = int(package_index)
    except (TypeError, ValueError):
        return RedirectResponse(url="/billing", status_code=302)
    if index < 0 or index >= len(packages):
        return RedirectResponse(url="/billing", status_code=302)

    package = packages[index]
    result = await create_payment(
        db,
        user_id=user.id,
        kind=KIND_PACKAGE,
        package_name=package["name"],
        messages_count=package["count"],
        price=package["price"],
    )
    return RedirectResponse(url=result["confirmation_url"], status_code=302)
