from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.analytics.send_analytics import normalize_utc
from app.application.billing.plan_switch import switch_is_refused
from app.application.billing.plan_usage import plan_axes
from app.application.billing.subscription_period import subscription_is_live
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
    PaymentCreationError,
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


# ЗАКРЫТОЕ МНОЖЕСТВО ПРИЧИН ОТКАЗА (U1, U2, U3, T-05-46).
#
# Раздел, который берёт деньги, обязан отвечать на отказ словами. До этого
# отображения все ветки гардов возвращали ГОЛЫЙ редирект на `/billing`: человек
# нажимал «Оплатить» и получал ту же самую страницу без единого слова — а это
# читается как «кнопка сломана», и следующим действием становится повторное
# нажатие. Из отрисованной разметки эти ветки недостижимы, но УСТАРЕВШАЯ
# СТРАНИЦА достижима: администратор выключает платежи или план уходит из
# конфига между отрисовкой и нажатием.
#
# ПОЧЕМУ МНОЖЕСТВО ЗАКРЫТО. В разметку уходит строка ИЗ ЭТОГО отображения, а не
# значение параметра запроса, поэтому подставить через адрес произвольный текст
# невозможно. Это НЕДОСТИЖИМОСТЬ, а не экранирование: подставлять нечего,
# потому что вход в разметку не связан со входом из адреса. Тем же приёмом
# закрыт признак исхода повтора отправки (RETRY_NOTICES, app/pages/history.py).
#
# ТЕКСТ СТОРОННЕГО ИСКЛЮЧЕНИЯ СЮДА НЕ ПОПАДАЕТ НИ ПРИ КАКИХ УСЛОВИЯХ (T-05-47):
# он уходит в журнал ключом `payment_create_failed`, а на экран — одна из этих
# четырёх строк.
PAYMENT_ERROR_MESSAGES = {
    "payment": "Не удалось начать оплату — попробуйте ещё раз через минуту",
    "disabled": "Оплата сейчас недоступна — обратитесь к администратору",
    "plan": "Этот тариф больше не предлагается — обновите страницу и выберите другой",
    "package": "Этот пакет больше не предлагается — обновите страницу и выберите другой",
    # Понижение тарифа при действующей подписке (C2/WR-02, вариант
    # `upgrade-only`). Строка НАЗЫВАЕТ ВЫГОДУ, а не только запрет: отказ без
    # причины читается как поломка, а «оплаченные дни не сгорают» объясняет,
    # ради чего отказ существует.
    "downgrade": (
        "Перейти на младший тариф можно после окончания оплаченного срока — "
        "оплаченные дни не сгорают"
    ),
}

# Подпись четвёртого состояния CTA карточки плана. Живёт РЯДОМ со строкой
# отказа обработчика намеренно: это две половины одного правила, и разъехаться
# им негде, пока они стоят в одном месте.
DOWNGRADE_CARD_CAPTION = (
    "Переход на младший тариф — после окончания оплаченного срока: "
    "оплаченные дни не сгорают"
)


def _payment_error_message(code: str | None) -> str:
    """Код причины отказа → готовая строка. Неизвестный код даёт пустую.

    Пустая строка означает «плашки нет вовсе», а не «плашка без текста»:
    неизвестный код не имеет права ни напечатать себя, ни нарисовать пустую
    рамку, потому что владелец ссылки не должен уметь сообщить пользователю о
    событии, которого не было.
    """
    return PAYMENT_ERROR_MESSAGES.get(code or "", "")


# ОБА ОБЪЯВЛЕНИЯ ПРАВИЛА ЖИВУТ В `app/application/billing/`, А МОДУЛЬ ИХ ТОЛЬКО
# ЧИТАЕТ: `switch_is_refused` (`plan_switch.py`) — порядок тарифов,
# `subscription_is_live` (`subscription_period.py`) — признак живости
# оплаченного срока, который правило принимает обязательным аргументом. Своей
# копии ни того, ни другого этот файл не держит: пока признак живости стоял
# здесь, вторая стадия (`_apply_extension` в `app/services/payment_service.py`)
# его не получала вовсе, и подтверждённый платёж на истёкшем сроке брал деньги
# за тариф, который не выдавался (гэп 1, 05-VERIFICATION.md).


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

    ПАРАМЕТР `error` ТОЛЬКО ПОКАЗЫВАЕТ И НИЧЕГО НЕ МЕНЯЕТ. Он приезжает
    перенаправлением от форм оплаты и прогоняется через закрытое отображение
    `_payment_error_message`; в контекст уходит ГОТОВАЯ СТРОКА, а не код и не
    значение параметра (T-05-46). Запрет на запись из этого обработчика
    параметр не ослабляет ни на йоту.
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

    # ЧЕТВЁРТОЕ СОСТОЯНИЕ CTA КАРТОЧКИ считается ЗДЕСЬ, а не в разметке
    # (C2/WR-02, вариант `upgrade-only`): правило перехода между тарифами — одно
    # на раздел, и вторая его копия в Jinja разъехалась бы с гардом обработчика
    # молча. Разметке достаётся ГОТОВЫЙ ответ «этой карточке кнопку не рисовать».
    #
    # Множество, а не предикат в цикле шаблона: карточек три, а правило одно.
    #
    # ПРИЗНАК ЖИВОСТИ УХОДИТ В ВЫЗОВ АРГУМЕНТОМ, а не стоит средним членом
    # конъюнкции: член условия можно забыть, обязательный аргумент — нельзя.
    # Ровно на забытом члене и разошлись две стадии правила (гэп 1 раунда 3).
    live = subscription_is_live(expires_at, datetime.now(timezone.utc))
    refused_plan_ids = {
        plan["id"]
        for plan in plans
        if plan.get("id")
        and switch_is_refused(current_plan_id, plan["id"], period_is_live=live)
    }

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
            # ГОТОВАЯ СТРОКА, а не код: значение параметра запроса в разметку не
            # уходит ни значением, ни атрибутом (T-05-46).
            "error_message": _payment_error_message(
                request.query_params.get("error")
            ),
            # Зеркало FREE_PLAN_ID для разметки: бесплатный тариф ЕСТЬ в
            # перечне конфига, поэтому проверки «план есть в конфиге» мало,
            # чтобы не нарисовать ему кнопку оплаты (IN-06).
            "free_plan_id": FREE_PLAN_ID,
            "refused_plan_ids": refused_plan_ids,
            "downgrade_caption": DOWNGRADE_CARD_CAPTION,
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

    # СВЕРКА ИСТОЧНИКА ОСТАЁТСЯ 403 БЕЗ ПРИЧИНЫ. Чужому источнику причина
    # отказа не сообщается: межсайтовый запрос не имеет права узнать даже,
    # включены ли платежи. Порядок проверок не меняется — сначала кто пришёл,
    # потом откуда, потом что просит.
    if not is_same_origin(request):
        return Response(status_code=403)

    if not settings.yookassa_enabled:
        return RedirectResponse(url="/billing?error=disabled", status_code=302)

    selected = next(
        (p for p in settings.parsed_plan_limits if p.get("id") == plan), None
    )
    if selected is None or selected.get("id") == FREE_PLAN_ID:
        return RedirectResponse(url="/billing?error=plan", status_code=302)

    # ГАРД СМЕНЫ ТАРИФА (C2/WR-02, вариант `upgrade-only`). Стоит ПОСЛЕ сверки
    # плана с конфигом: сравнивать ранги имеет смысл только у тарифа, который
    # вообще продаётся.
    #
    # Действующая подписка берётся из УЖЕ ПОСЧИТАННОГО контекста шелла
    # (зависимость `load_shell_context` висит на всём роутере страниц, включая
    # POST), вторым запросом не считается — правило раздела D-09/D-19.
    #
    # ЗАЧЕМ ГАРД, ЕСЛИ КАРТОЧКА МЛАДШЕГО ПЛАНА КНОПКИ НЕ РИСУЕТ. Затем, что
    # УСТАРЕВШАЯ СТРАНИЦА ДОСТИЖИМА: подписка могла быть куплена в соседней
    # вкладке после отрисовки этой. Разметка гарантий не даёт вовсе, и правило,
    # живущее только в ней, не является правилом.
    # ОДИН ВЫЗОВ, А НЕ КОНЪЮНКЦИЯ ИЗ ДВУХ ЧЛЕНОВ. Признак живости оплаченного
    # срока — обязательный вход правила, поэтому выражения, которое могло бы
    # разъехаться с таким же выражением второй стадии, здесь не остаётся вовсе.
    quota = (getattr(request.state, "shell", None) or {}).get("quota", {})
    if switch_is_refused(
        quota.get("plan", FREE_PLAN_ID),
        selected["id"],
        period_is_live=subscription_is_live(
            quota.get("expires_at"), datetime.now(timezone.utc)
        ),
    ):
        return RedirectResponse(url="/billing?error=downgrade", status_code=302)

    try:
        result = await create_payment(
            db,
            user_id=user.id,
            # Предмет покупки — КОНСТАНТОЙ, никогда голым литералом (WR-04):
            # опечатка в литерале не падает громко, а уводит подписочный платёж
            # в пакетную ветку вебхука с пустым `messages_count`.
            kind=KIND_SUBSCRIPTION,
            plan=selected["id"],
            price=selected["price"],
            package_name=None,
            messages_count=None,
        )
    except PaymentCreationError:
        # Текст исключения СЮДА НЕ ПРИХОДИТ И НЕ НУЖЕН: он уже записан журналом
        # сервиса ключом `payment_create_failed`. На экран уезжает код причины,
        # а строку по нему подбирает `_payment_error_message` (T-05-47).
        return RedirectResponse(url="/billing?error=payment", status_code=302)
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

    # Та же оговорка, что у соседней формы: чужому источнику причина отказа не
    # сообщается, и сверка стоит ДО любого обращения к БД.
    if not is_same_origin(request):
        return Response(status_code=403)

    if not settings.yookassa_enabled:
        return RedirectResponse(url="/billing?error=disabled", status_code=302)

    packages = settings.parsed_message_packages
    # НЕЧИСЛОВОЙ И ВНЕДИАПАЗОННЫЙ ИНДЕКС ВЕДУТ В ОДНУ ПРИЧИНУ: для человека это
    # один случай — «этого пакета нет», — а различие между ними принадлежит
    # разбору запроса, а не экрану.
    try:
        index = int(package_index)
    except (TypeError, ValueError):
        return RedirectResponse(url="/billing?error=package", status_code=302)
    if index < 0 or index >= len(packages):
        return RedirectResponse(url="/billing?error=package", status_code=302)

    package = packages[index]
    try:
        result = await create_payment(
            db,
            user_id=user.id,
            kind=KIND_PACKAGE,
            package_name=package["name"],
            messages_count=package["count"],
            price=package["price"],
        )
    except PaymentCreationError:
        return RedirectResponse(url="/billing?error=payment", status_code=302)
    return RedirectResponse(url=result["confirmation_url"], status_code=302)
