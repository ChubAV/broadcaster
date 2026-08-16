import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value
from yookassa import Configuration, Payment as YooPayment
from yookassa.domain.notification import WebhookNotificationEventType

from app.application.billing.subscription_period import next_expiry
from app.config import get_settings
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.services.billing_service import add_messages
from app.services.billing_cache import invalidate_balance_cache

logger = structlog.get_logger()

# Предметы покупки. Строки живут здесь, потому что их читает и пишет один этот
# модуль; ревизия 0017 выписывает свои копии отдельно и намеренно (правило 0013).
KIND_PACKAGE = "package"
KIND_SUBSCRIPTION = "subscription"

STATUS_PENDING = "pending"
STATUS_SUCCEEDED = "succeeded"
STATUS_CANCELED = "canceled"

# ТЕРМИНАЛЬНЫЕ СТАТУСЫ — те, из которых платёж больше не выходит. Их два, и
# защита от повторной обработки написана через это множество, а не через
# перечисление в каждой ветке: копия в ветке рано или поздно разойдётся с
# оригиналом — достаточно, чтобы третью ветку добавили, забыв её скопировать.
TERMINAL_STATUSES = frozenset({STATUS_SUCCEEDED, STATUS_CANCELED})

# ЗНАКОМЫЕ СОБЫТИЯ — КОНСТАНТАМИ SDK, НИКОГДА СТРОКОВЫМИ ЛИТЕРАЛАМИ (T-05-12).
# Опечатка в литерале не поднимает ошибку: событие просто молча не
# обрабатывается, платёж остаётся pending, а обнаруживается это на боевом
# приёме денег. Константа с опечаткой падает AttributeError на импорте модуля.
#
# В SDK объявлено семь событий; refund.succeeded, payout.* и deal.closed этой
# фазе не принадлежат и по-прежнему возвращают False.
KNOWN_EVENTS = frozenset(
    {
        WebhookNotificationEventType.PAYMENT_SUCCEEDED,
        WebhookNotificationEventType.PAYMENT_CANCELED,
    }
)


class PaymentCreationError(Exception):
    """ЮKassa не создала платёж. Своё исключение модуля, а не чужое дерево.

    ЗАЧЕМ ОТДЕЛЬНЫЙ ТИП. Вызывающий обязан отличить «платёж не создан» от любой
    другой поломки, и делать это по типу исключения SDK он не может: дерево
    исключений `yookassa` — чужой контракт, который меняется без нашего ведома,
    а сетевые отказы приходят из `requests` вовсе не через него. Ловить здесь
    `Exception` и поднимать СВОЙ тип — единственный способ дать вызывающему
    ветку, которая не разъедется с версией SDK.

    ТЕКСТ ЧУЖОГО ИСКЛЮЧЕНИЯ В ЭТОТ ОБЪЕКТ НЕ КЛАДЁТСЯ. Он уходит в журнал ключом
    `payment_create_failed` и НИКОГДА на экран (T-05-47): прецедент R-03-09
    Фазы 3 — раскрытие текста стороннего исключения в плашке — принят владельцем
    риском severity medium, и повторять его на ДЕНЕЖНОМ пути не следует.
    Исходное исключение остаётся доступным через `__cause__` для отладчика,
    который читает трассировку, а не страницу.
    """


def _configure_yookassa():
    settings = get_settings()
    Configuration.account_id = settings.yookassa_shop_id
    Configuration.secret_key = settings.yookassa_secret_key


async def create_payment(
    db: AsyncSession,
    user_id: int,
    price: str,
    *,
    kind: str,
    package_name: str | None = None,
    messages_count: int | None = None,
    plan: str | None = None,
) -> dict:
    """Создаёт платёж в ЮKassa и строку `payments` под него.

    `kind` ОБЯЗАТЕЛЕН И KEYWORD-ONLY намеренно. Сигнатура стала строже, чем
    была: необновлённый вызывающий обязан упасть громко на вызове, а не тихо
    записать платёж с угаданным предметом покупки — угаданный предмет
    обнаружился бы только на вебхуке, то есть после того, как деньги списаны.
    """
    _configure_yookassa()
    settings = get_settings()

    if kind == KIND_SUBSCRIPTION:
        description = f"Подписка «{plan}»"
        # Ключ `kind` в metadata обязателен: без него в личном кабинете ЮKassa
        # два предмета покупки неразличимы, и вопрос «за что этот платёж»
        # разрешается только сверкой со своей базой (T-05-08).
        metadata = {
            "user_id": str(user_id),
            "kind": kind,
            "plan": str(plan or ""),
        }
    else:
        description = f"Пополнение баланса: {package_name}"
        metadata = {
            "user_id": str(user_id),
            "kind": kind,
            "messages_count": str(messages_count),
            "package_name": str(package_name or ""),
        }

    idempotency_key = str(uuid.uuid4())
    # ВЫЗОВ SDK СТОИТ ДО ЗАПИСИ В БД, И ЭТОТ ПОРЯДОК ОБЯЗАТЕЛЕН (T-05-49).
    # Строка `payments`, оставшаяся после отказа, означала бы платёж, которого у
    # ЮKassa нет вовсе: он не пришёл бы ни успехом, ни отменой и висел бы
    # `pending` вечно, показывая пользователю «в обработке» там, где обработки
    # не начиналось.
    #
    # ЛОВИТСЯ `Exception`, А НЕ ТИП ИЗ SDK. Отказ приезжает и своим деревом
    # исключений `yookassa`, и сетевым исключением `requests` из-под него, и
    # разбором чужого ответа. Перечислить это множество нельзя, а всякий
    # непойманный его элемент — необработанная пятисотка на кнопке оплаты.
    # `KeyboardInterrupt` и `SystemExit` наследуются от `BaseException` и сюда
    # намеренно не попадают.
    try:
        payment = YooPayment.create(
            {
                "amount": {"value": price, "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": settings.yookassa_return_url or f"{settings.app_name}/billing",
                },
                "capture": True,
                "description": description,
                "metadata": metadata,
            },
            idempotency_key,
        )
    except Exception as exc:
        # СЛЕД ОБЯЗАТЕЛЕН (T-05-48). Отказ без записи в журнале превращает
        # жалобу «я нажал, ничего не произошло» в непроверяемую: на экране
        # человек видит одну фиксированную строку, и различить по ней сеть,
        # неверный ключ магазина и отвергнутую сумму невозможно.
        #
        # Уровень `error`, а не `warning`: этот отказ останавливает приём денег,
        # и в потоке предупреждений он потерялся бы (тот же выбор, что у
        # `webhook_ip_header_not_configured`).
        logger.error(
            "payment_create_failed",
            user_id=user_id,
            kind=kind,
            plan=plan,
            package_name=package_name,
            messages=messages_count,
            amount=price,
            error_type=type(exc).__name__,
            error=str(exc),
        )
        raise PaymentCreationError(
            "ЮKassa не создала платёж"
        ) from exc

    db_payment = Payment(
        user_id=user_id,
        yookassa_payment_id=payment.id,
        status="pending",
        amount_value=price,
        amount_currency="RUB",
        kind=kind,
        plan=plan,
        messages_count=messages_count,
        package_name=package_name,
    )
    db.add(db_payment)
    await db.commit()

    logger.info(
        "payment_created",
        user_id=user_id,
        yookassa_id=payment.id,
        amount=price,
        kind=kind,
        plan=plan,
        messages=messages_count,
    )

    return {
        "confirmation_url": payment.confirmation.confirmation_url,
        "payment_id": payment.id,
    }


async def _claim_payment(
    db: AsyncSession, yookassa_id: str, new_status: str, now: datetime
) -> bool:
    """Заявляет платёж на обработку. True — заявка выиграна, False — опередили.

    ЭТО COMPARE-AND-SWAP, А НЕ ПРОВЕРКА С ПОСЛЕДУЮЩЕЙ ЗАПИСЬЮ. Условие «статус
    ещё не терминальный» стоит В ТОМ ЖЕ операторе, что и запись нового статуса,
    поэтому между проверкой и записью не остаётся зазора ВОВСЕ. Прежняя пара
    «прочитали статус → много позже записали» оставляла окно, в которое
    помещалась целая вторая доставка: обе видели `pending`, обе начисляли.

    РАБОТАЕТ ОДИНАКОВО НА PostgreSQL И НА SQLite, и это принципиально. Суита
    проекта живёт на SQLite, где `SELECT ... FOR UPDATE` диалектом ИГНОРИРУЕТСЯ
    — то есть блокировка строки сама по себе регрессией непокрываема. Условный
    UPDATE покрываем, потому что атомарность одного оператора даёт и SQLite.

    `synchronize_session=False`: оператор идёт мимо identity map, и сессия о
    записи не знает. Поля объекта платежа отзеркаливает вызывающий.
    """
    result = await db.execute(
        update(Payment)
        .where(
            Payment.yookassa_payment_id == yookassa_id,
            Payment.status.not_in(TERMINAL_STATUSES),
        )
        .values(status=new_status, confirmed_at=now)
        .execution_options(synchronize_session=False)
    )
    return result.rowcount == 1


def _mirror_claim(db_payment: Payment, new_status: str, now: datetime) -> None:
    """Отзеркаливает выигранную заявку на объект платежа в Python.

    `synchronize_session=False` означает, что сессия о записи не знает, а ниже
    по ветке эти поля читаются логированием и `_extend_subscription`.

    Значения ставятся `set_committed_value`, а не присваиванием: присваивание
    пометило бы объект грязным, и ORM выдала бы на коммите ВТОРОЙ UPDATE тех же
    колонок — лишний оператор, притворяющийся, что запись сделал он.
    """
    set_committed_value(db_payment, "status", new_status)
    set_committed_value(db_payment, "confirmed_at", now)


async def handle_webhook(
    db: AsyncSession, event: str, payment_data: dict
) -> bool:
    """Доводит платёж до терминального статуса по подтверждённому уведомлению.

    ПОРЯДОК ПРОВЕРОК ЗНАЧИМ И МЕНЯТЬСЯ НЕ ДОЛЖЕН: событие → наличие `id` →
    строка платежа в СВОЕЙ базе → терминальный статус → и только потом
    ветвление по исходу платежа и по предмету покупки.

    ЗАЩИТА ОТ ДВОЙНОГО НАЧИСЛЕНИЯ ДЕРЖИТСЯ ДВУМЯ МЕХАНИЗМАМИ, И ГРАНИЦА МЕЖДУ
    НИМИ НАЗВАНА ЗДЕСЬ НАМЕРЕННО (T-05-04, T-05-35):

    * `_claim_payment` — условный UPDATE, держит НАЛОЖИВШИЕСЯ доставки. Их обе
      прошли проверку статуса ниже, потому что обе прочитали строку, пока она
      была `pending`; заявку выигрывает ровно одна, проигравшая до начисления не
      доходит физически. Работает на обоих диалектах и покрыт регрессией
      `tests/test_services/test_payment_concurrency.py`;
    * `with_for_update()` на выборке — убирает саму конкуренцию НА PostgreSQL:
      вторая доставка ждёт на выборке и доходит до проверки статуса уже с
      обновлённым значением, то есть выходит раньше и без единой записи. НА
      SQLite эта половина не исполняется вовсе — диалект молча опускает
      `FOR UPDATE`, поэтому суита её не проверяет и проверить не может.

    Проверка терминального статуса стоит ДО ветвления намеренно, но единственной
    защитой она БОЛЬШЕ НЕ ЯВЛЯЕТСЯ: это быстрый выход для ПОСЛЕДОВАТЕЛЬНОЙ
    повторной доставки (первая завершилась, вторая пришла после). Ровно она же не
    даёт припоздавшему уведомлению об отмене отнять уже выданное (T-05-10):
    платёж в `succeeded` не переводится в `canceled`.

    ЗНАКОМЫХ СОБЫТИЙ ДВА — успех и отмена (D-16). До этого отмена возвращала
    False, и отменённый платёж навсегда оставался `pending`: история показывала
    бы «в обработке» там, где денег не взяли вовсе — то есть неправду, а не
    отсутствие данных (BILL-07).

    ПРЕДМЕТ ПОКУПКИ РЕШАЕТ КОЛОНКА `kind` ИЗ БД, никогда `metadata`
    уведомления: тело уведомления приезжает из сети и источником истины быть не
    может (T-05-02). Пользователь берётся оттуда же — из строки платежа.
    """
    if event not in KNOWN_EVENTS:
        return False

    obj = payment_data.get("object", {})
    yookassa_id = obj.get("id")
    if not yookassa_id:
        logger.warning("webhook_missing_payment_id")
        return False

    result = await db.execute(
        select(Payment)
        .where(Payment.yookassa_payment_id == yookassa_id)
        .with_for_update()
    )
    db_payment = result.scalar_one_or_none()
    if db_payment is None:
        logger.warning("webhook_payment_not_found", yookassa_id=yookassa_id)
        return False

    if db_payment.status in TERMINAL_STATUSES:
        logger.info("webhook_payment_already_processed", yookassa_id=yookassa_id)
        return True

    now = datetime.now(timezone.utc)

    if event == WebhookNotificationEventType.PAYMENT_CANCELED:
        # ВЕТКА ОТМЕНЫ НАМЕРЕННО НИЧЕГО НЕ НАЧИСЛЯЕТ: ни сообщений, ни дней
        # подписки. Она только записывает исход — и тем снимает платёж с вечного
        # `pending`. Баланс при этом не изменился, поэтому и инвалидировать
        # кэш нечего.
        #
        # Момент решения пишется в СУЩЕСТВУЮЩУЮ колонку времени подтверждения:
        # колонка одна, и её смысл — «когда платёж перешёл в терминальное
        # состояние». Второй колонки под отмену D-15 не заводит, а расширять
        # решение владельца этот код не вправе.
        #
        # Причина отмены (`cancellation_details` в теле уведомления) не пишется
        # и не логируется (T-05-13): её не называет ни требование, ни макет, а
        # разбор чужой структуры ради неиспользуемого поля — лишний контракт с
        # внешним форматом.
        if not await _claim_payment(db, yookassa_id, STATUS_CANCELED, now):
            await db.rollback()
            logger.info("webhook_claim_lost", yookassa_id=yookassa_id)
            return True

        _mirror_claim(db_payment, STATUS_CANCELED, now)
        await db.commit()

        logger.info(
            "payment_canceled",
            user_id=db_payment.user_id,
            yookassa_id=yookassa_id,
            kind=db_payment.kind,
        )
        return True

    # ПРОВЕРКА ПРИГОДНОСТИ ПАКЕТА СТОИТ ДО ЗАЯВКИ (T-05-39, WR-04). Платёж с
    # пустым `messages_count` — последствие опечатки в `kind` у вызывающего:
    # подписочная покупка ушла в пакетную ветку, где считать нечего. Заявить его
    # проведённым и потом отказаться значило бы пометить платёж выданным, ничего
    # не выдав. Раньше начисление падало TypeError, маршрут отвечал 500, и
    # ЮKassa повторяла доставку до отказа при взятых деньгах.
    if db_payment.kind != KIND_SUBSCRIPTION and not db_payment.messages_count:
        logger.error(
            "webhook_package_without_messages_count",
            yookassa_id=yookassa_id,
            user_id=db_payment.user_id,
            kind=db_payment.kind,
        )
        return False

    # ЗАЯВКА СТОИТ ПЕРЕД ЛЮБЫМ НАЧИСЛЕНИЕМ И В ТОЙ ЖЕ ТРАНЗАКЦИИ, ЧТО И ОНО:
    # единственный `commit` в конце ветки остаётся единственным. Отдельный
    # коммит заявки завёл бы окно, в котором платёж помечен проведённым, а
    # ресурс не выдан.
    if not await _claim_payment(db, yookassa_id, STATUS_SUCCEEDED, now):
        # Не отказ: уведомление обработано — просто не этой доставкой. 5xx здесь
        # спровоцировал бы новую попытку ЮKassa по уже проведённому платежу.
        await db.rollback()
        logger.info("webhook_claim_lost", yookassa_id=yookassa_id)
        return True

    _mirror_claim(db_payment, STATUS_SUCCEEDED, now)

    if db_payment.kind == KIND_SUBSCRIPTION:
        await _extend_subscription(db, db_payment, now)
        await db.commit()
        logger.info(
            "subscription_payment_succeeded",
            user_id=db_payment.user_id,
            yookassa_id=yookassa_id,
            amount=db_payment.amount_value,
            plan=db_payment.plan,
        )
        return True

    new_balance = await add_messages(
        db,
        db_payment.user_id,
        db_payment.messages_count,
        type="purchase",
        description=f"Покупка: {db_payment.package_name}",
        payment_id=yookassa_id,
    )
    await db.commit()
    await invalidate_balance_cache(db_payment.user_id)

    logger.info(
        "payment_succeeded",
        user_id=db_payment.user_id,
        yookassa_id=yookassa_id,
        messages=db_payment.messages_count,
        new_balance=new_balance,
    )
    return True


async def _extend_subscription(
    db: AsyncSession, db_payment: Payment, now: datetime
) -> None:
    """Двигает срок подписки владельца платежа или заводит её впервые.

    ЗАПРОС АКТИВНОЙ ПОДПИСКИ ПОВТОРЯЕТ `get_shell_context` ДОСЛОВНО
    (app/pages/common.py:397-404): те же три условия, та же сортировка, тот же
    `limit(1)`. Одинаковый запрос у ЧИТАТЕЛЯ (шелл показывает тариф и срок) и у
    ПИСАТЕЛЯ (этот код) держит их в согласии; разойдись они, продление двигало
    бы одну строку, а пользователь видел бы другую.

    ВТОРАЯ АКТИВНАЯ СТРОКА С РЕВИЗИИ 0018 НЕВОЗМОЖНА НА УРОВНЕ СУБД — частичный
    уникальный индекс `uq_subscriptions_active_user`. Это закрывает остаточную
    щель, которую прикладная заявка `_claim_payment` закрыть не могла: два
    РАЗНЫХ платежа одного пользователя, доставленные внахлёст при отсутствующей
    подписке, честно выигрывают КАЖДЫЙ СВОЮ заявку — строки платежей-то разные,
    — оба видят «подписки нет» и оба вставляют.

    ОТКАЗ ОГРАНИЧЕНИЯ ЗДЕСЬ ОБРАБАТЫВАЕТСЯ, А НЕ ПРОПУСКАЕТСЯ НАВЕРХ. Платёж
    настоящий, деньги взяты, и ответить на него 500-й значило бы наказать
    пользователя за гонку внутри платформы. Проигравшая вставку доставка
    перечитывает чужую строку и двигает срок НА НЕЙ — исход тот же, что при
    последовательном приходе двух платежей.

    ВСТАВКА ИДЁТ В SAVEPOINT. Откат по нарушению ограничения обязан снять ТОЛЬКО
    неудавшуюся вставку: снаружи, в той же транзакции, уже лежит выигранная
    заявка на платёж (`_claim_payment`), и полный откат вернул бы платёж в
    `pending` — то есть потерял бы факт обработки денег.

    Срок двигается ТОЛЬКО ЗДЕСЬ — то есть только по подтверждённому платежу.
    Возврат браузера с `return_url` доказательством оплаты не является и
    происходит в том числе при отказе (D-05, T-05-05).
    """
    subscription = await _active_subscription(db, db_payment.user_id)

    if subscription is not None:
        _apply_extension(subscription, db_payment, now)
        return

    try:
        async with db.begin_nested():
            db.add(
                Subscription(
                    user_id=db_payment.user_id,
                    plan=db_payment.plan or "free",
                    expires_at=next_expiry(None, now),
                    is_active=True,
                )
            )
            await db.flush()
        return
    except IntegrityError as rejection:
        logger.info(
            "subscription_insert_lost",
            user_id=db_payment.user_id,
            yookassa_id=db_payment.yookassa_payment_id,
        )
        rejected_by = rejection

    subscription = await _active_subscription(db, db_payment.user_id)
    if subscription is None:
        # Ограничение отвергло вставку, но активной строки нет — значит отказ
        # пришёл НЕ от `uq_subscriptions_active_user`, и глотать его нельзя:
        # исключение поднимается тем же объектом, а не новым.
        raise rejected_by
    _apply_extension(subscription, db_payment, now)


async def _active_subscription(db: AsyncSession, user_id: int) -> Subscription | None:
    """Действующая подписка пользователя — тем же запросом, что у читателя."""
    return (
        await db.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.is_active.is_(True),
            )
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


def _apply_extension(
    subscription: Subscription, db_payment: Payment, now: datetime
) -> None:
    subscription.expires_at = next_expiry(subscription.expires_at, now)
    if db_payment.plan:
        subscription.plan = db_payment.plan
