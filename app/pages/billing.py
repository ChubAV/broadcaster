from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_db, get_settings
from app.services.billing_service import get_balance_info, get_transaction_history
from app.services.payment_service import create_payment
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


@router.get("/billing", response_class=HTMLResponse)
async def billing_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    user = await get_user_from_cookie(request, db, settings)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    balance_info = await get_balance_info(db, user.id)
    transactions = await get_transaction_history(db, user.id, limit=20)
    packages = settings.parsed_message_packages if settings.yookassa_enabled else []
    # JSON разбирается ОДИН раз в обработчике, а не свойством из цикла Jinja:
    # `parsed_plan_limits` кэша не имеет (`@lru_cache` стоит на `get_settings`,
    # а не на нём), и вызов из шаблона парсил бы строку на каждой итерации.
    plans = settings.parsed_plan_limits
    # Тариф и срок берутся из УЖЕ ПОСЧИТАННОГО контекста шелла, вторым запросом
    # не считаются: показатель один — источник обязан быть один (D-09/D-19).
    shell = getattr(request.state, "shell", None) or {}
    quota = shell.get("quota", {})
    return templates.TemplateResponse(
        "billing/balance.html",
        {
            "request": request,
            "user": user,
            "is_admin": check_is_admin(user, settings),
            "balance_info": balance_info,
            "transactions": transactions,
            "packages": packages,
            "plans": plans,
            "subscription": {
                "plan": quota.get("plan", FREE_PLAN_ID),
                "expires_at": quota.get("expires_at"),
            },
            "payments_enabled": settings.yookassa_enabled,
            "active_page": "billing",
        },
    )


@router.post("/billing/subscribe")
async def subscribe_to_plan(
    request: Request,
    plan: str = Form(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Заводит платёж за тариф и уводит пользователя на страницу оплаты ЮKassa.

    ИЗ ФОРМЫ ПРИЕЗЖАЕТ ТОЛЬКО ИДЕНТИФИКАТОР ПЛАНА. Цена и лимиты читаются из
    настроек ПО ЭТОМУ ИДЕНТИФИКАТОРУ — иначе покупатель назначает себе цену
    подменой поля формы (T-05-03). Неизвестный идентификатор возвращает на
    раздел, а НЕ выбирает «умолчание»: умолчание здесь означало бы продать не
    то, что нажали.

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
        kind="subscription",
        plan=selected["id"],
        price=selected["price"],
        package_name=None,
        messages_count=None,
    )
    return RedirectResponse(url=result["confirmation_url"], status_code=302)
