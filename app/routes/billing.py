import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from yookassa.domain.common.security_helper import SecurityHelper

from app.config import Settings
from app.dependencies import get_current_user_id, get_db, get_settings
from app.services.billing_service import get_balance_info, get_transaction_history
from app.services.payment_service import handle_webhook

logger = structlog.get_logger()

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/balance")
async def get_balance(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    info = await get_balance_info(db, user_id)
    return info


@router.get("/packages")
async def list_packages(settings: Settings = Depends(get_settings)):
    return {"packages": settings.parsed_message_packages}


@router.get("/transactions")
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    txs = await get_transaction_history(db, user_id, limit=limit, offset=offset)
    return {"transactions": txs}


# ЧЕТВЁРТОГО ЧТЕНИЯ И ПЯТОГО ВХОДА ЗДЕСЬ НЕТ НАМЕРЕННО.
#
# `POST /api/billing/purchase` вместе со своей моделью тела запроса снесён
# планом 05-04 (D-24). Покупка пакета сообщений идёт формой раздела
# (`app/pages/billing.py`), и у JSON-маршрута не осталось ни одного
# потребителя: его единственным вызывающим был скрипт шаблона.
#
# ⚠️ ЭТО БЫЛ НЕ ПРОСТО МЁРТВЫЙ КОД. Маршрут возвращал в браузер тело ответа с
# `yookassa_payment_id` — единственным «секретом», которым до этой фазы был
# защищён неаутентифицированный вебхук: зная идентификатор платежа, кто угодно
# отправлял уведомление об успешной оплате. Форма отдаёт 302 на страницу
# оплаты, и идентификатор наружу не попадает вовсе. Восстанавливать маршрут
# ради «удобства API» — значит вернуть утечку вместе с ним.
#
# Три ЧИТАЮЩИХ входа выше сохранены одним решением того же плана: удаление
# объявленного читающего API — отдельный вопрос совместимости, а не следствие
# перевода покупки на форму.


def _webhook_client_ip(request: Request, settings: Settings) -> str | None:
    """Адрес источника уведомления — с поправкой на обратный прокси.

    Пустая настройка `yookassa_webhook_client_ip_header` = читать
    `request.client.host` напрямую: так работает локальный запуск без прокси и
    вся тестовая суита.

    ⚠️ СПИСОК АДРЕСОВ ЧИТАЕТСЯ СПРАВА, А НЕ СЛЕВА. Если в настроенном заголовке
    всё-таки оказался список `a, b, c`, берётся ПРАВЫЙ элемент. Это ровно
    обратно тому, что подсказывает интуиция «левый элемент — исходный клиент»,
    и разница здесь не стилистическая, а решает исход атаки: список растёт
    слева направо, ЛЕВЫЙ элемент присылает сам клиент, а свой прокси лишь
    дописывает реальный адрес пира СПРАВА. Возьми этот код левый элемент —
    любой желающий подделал бы успешный платёж, прислав доверенный адрес
    ЮKassa первым в списке.
    """
    header_name = settings.yookassa_webhook_client_ip_header
    if header_name:
        raw = request.headers.get(header_name)
        if not raw:
            return None
        return raw.split(",")[-1].strip() or None
    client = request.client
    return client.host if client else None


def _is_trusted_source(ip: str) -> bool:
    """Входит ли адрес в боевые сети ЮKassa.

    Список сетей и разбор CIDR берутся ИЗ SDK (`SecurityHelper`): десять сетей
    живут там и обновляются вместе с пакетом, а своя копия устарела бы молча и
    начала отбрасывать легитимные уведомления — то есть останавливать приём
    денег без единой ошибки в логах.

    Неразбираемый адрес — НЕДОВЕРЕННЫЙ. `netaddr` поднимает на мусоре
    `AddrFormatError`, и любой отказ разбора обязан читаться как «источник не
    подтверждён»: исключение, ушедшее наверх, превратилось бы в 500, а 500 на
    вебхуке ЮKassa трактует как «попробовать позже» — то есть мусорный запрос
    получал бы повторные попытки вместо отказа.
    """
    try:
        return SecurityHelper().is_ip_trusted(ip)
    except Exception:
        return False


@router.post("/webhook")
async def yookassa_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Принимает уведомление ЮKassa о смене состояния платежа.

    ЗАЧЕМ ГАРД. Это вход, на котором принимается решение выдать ПЛАТНЫЙ ресурс,
    и до этой фазы он не был аутентифицирован ничем: единственным «секретом»
    служил `yookassa_payment_id`, который старый JSON-маршрут покупки возвращал
    прямо в браузер покупателю. С подключением подписки цена подделанного
    уведомления выросла до 4 900 ₽/мес, поэтому источник проверяется (T-05-01).

    ПРАВИЛО. Проверка стоит СРАЗУ после `yookassa_enabled` и ДО `request.json()`:
    недоверенный источник не должен доходить даже до разбора тела. Она вынесена
    ЗА пределы `try` намеренно — `except Exception` ниже превращает всё в 500, а
    отказ гарда обязан остаться 403.

    Механизм — проверка по IP. Проверки ПОДПИСИ уведомления в установленном
    `yookassa` (3.10.0) не существует вовсе: у `SecurityHelper` ровно два
    метода, и оба про адреса. Документация, обещающая метод сверки подписи,
    описывает не этот пакет — импортировать такой метод неверно по построению,
    в том числе через `getattr(..., None)` с тихим переходом в no-op, который
    выглядел бы как работающая криптографическая проверка, ничего не проверяя.

    ⚠️ НАЗВАННАЯ ГРАНИЦА ЗАЩИТЫ. За обратным прокси `request.client.host` — это
    адрес контейнера nginx, а не ЮKassa, поэтому боевой адрес приезжает
    ЗАГОЛОВКОМ (`yookassa_webhook_client_ip_header`, на бою `X-Real-IP`).
    Заголовку можно верить РОВНО ПОСТОЛЬКУ, поскольку свой прокси его
    ПЕРЕЗАПИСЫВАЕТ: nginx проекта ставит `proxy_set_header X-Real-IP
    $remote_addr` на каждом location, то есть затирает всё, что прислал клиент.
    Заголовок, который прокси лишь ДОПИСЫВАЕТ (`X-Forwarded-For` через
    `$proxy_add_x_forwarded_for`), такой гарантии не даёт, и настраивать сюда
    его нельзя. Если настройку заполнить именем заголовка, который прокси не
    перезаписывает, проверка станет декоративной — клиент подделает адрес сам.

    ⚠️ АВАРИЙНЫЙ ВЫКЛЮЧАТЕЛЬ. `yookassa_webhook_verify_ip = False` пропускает
    любой источник. Он существует, потому что ошибка настройки заголовка
    отвергает ВСЕ настоящие уведомления, и приём денег встаёт молча: ЮKassa
    повторит доставку несколько раз и сдастся. Выключатель — способ вернуть
    приём денег за одну правку окружения, не выкатывая код.
    """
    if not settings.yookassa_enabled:
        raise HTTPException(status_code=403, detail="Payments are disabled")

    if settings.yookassa_webhook_verify_ip:
        client_ip = _webhook_client_ip(request, settings)
        if not client_ip or not _is_trusted_source(client_ip):
            # Логируется АДРЕС, но не тело уведомления: в теле приезжает
            # `payment_method.card` с `first6` / `last4` (T-05-07).
            logger.warning("webhook_untrusted_source", client_ip=client_ip)
            raise HTTPException(status_code=403, detail="Untrusted source")

    try:
        body = await request.json()
        event = body.get("event", "")
        payment_data = body

        # Ключ НЕ называется `event`: у structlog первый позиционный параметр
        # `BoundLogger.info()` именно так и называется, поэтому `event=` рядом с
        # именем сообщения поднимал TypeError — и падал он ДО вызова
        # handle_webhook, то есть ни одно уведомление не обрабатывалось вовсе.
        logger.info("yookassa_webhook_received", webhook_event=event)

        processed = await handle_webhook(db, event, payment_data)
        return {"ok": processed}
    except Exception as e:
        logger.error("webhook_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")
