import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from yookassa.domain.notification import WebhookNotificationEventType

from app.application.billing.subscription_period import add_one_month
from app.models.subscription import Subscription
from app.models.user import User
from app.models.payment import Payment
from app.services.payment_service import create_payment, handle_webhook
from app.services.billing_service import get_balance, add_messages

# Имена событий берутся КОНСТАНТАМИ SDK и в тестах тоже. Литерал с опечаткой не
# поднял бы ошибку: обработчик просто вернул бы False, и тест «событие не
# обработано» прошёл бы по неверной причине — проверяя опечатку, а не правило.
EVENT_SUCCEEDED = WebhookNotificationEventType.PAYMENT_SUCCEEDED
EVENT_CANCELED = WebhookNotificationEventType.PAYMENT_CANCELED


def _utc(value: datetime | None) -> datetime | None:
    """Доводит значение из БД до aware-UTC.

    SQLite отдаёт `DateTime(timezone=True)` NAIVE, PostgreSQL — aware. Сравнение
    naive с aware поднимает TypeError ровно на одном из двух диалектов, поэтому
    сравнивать без приведения нельзя даже в тесте.
    """
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def _user(db, email: str = "t@t.com") -> User:
    user = User(email=email, password_hash="h", name="T")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _payment(db, user: User, **overrides) -> Payment:
    """Строка платежа в состоянии «уведомление ещё не приходило»."""
    fields = {
        "user_id": user.id,
        "yookassa_payment_id": "yoo_c1",
        "status": "pending",
        "amount_value": "149.00",
        "amount_currency": "RUB",
        "kind": "package",
        "messages_count": 100,
        "package_name": "100 messages",
    }
    fields.update(overrides)
    payment = Payment(**fields)
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@pytest.mark.asyncio
async def test_create_payment(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    mock_yoo_payment = MagicMock()
    mock_yoo_payment.id = "yoo_123"
    mock_yoo_payment.confirmation = MagicMock()
    mock_yoo_payment.confirmation.confirmation_url = "https://yookassa.ru/pay/123"

    mock_settings = MagicMock()
    mock_settings.yookassa_shop_id = "shop123"
    mock_settings.yookassa_secret_key = "secret"
    mock_settings.yookassa_return_url = "https://app.com/billing"
    mock_settings.app_name = "Broadcaster"

    with patch("app.services.payment_service.get_settings", return_value=mock_settings), \
         patch("app.services.payment_service.YooPayment.create", return_value=mock_yoo_payment):
        result = await create_payment(
            db_session,
            user_id=user.id,
            kind="package",
            package_name="100 messages",
            messages_count=100,
            price="149.00",
            # Тело меняется НАМЕРЕННО: сигнатура изменилась намеренно. Правило
            # смены тарифа пакета не касается, и это записывается ЗНАЧЕНИЕМ
            # `None`, а не пропуском аргумента (D-28).
            switch_authorized=None,
        )

    assert result["confirmation_url"] == "https://yookassa.ru/pay/123"
    assert result["payment_id"] == "yoo_123"


@pytest.mark.asyncio
async def test_handle_webhook_success(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    payment = Payment(
        user_id=user.id,
        yookassa_payment_id="yoo_456",
        status="pending",
        amount_value="149.00",
        amount_currency="RUB",
        messages_count=100,
        package_name="100 messages",
    )
    db_session.add(payment)
    await db_session.commit()

    with patch("app.services.payment_service.invalidate_balance_cache", new_callable=AsyncMock):
        processed = await handle_webhook(
            db_session,
            event="payment.succeeded",
            payment_data={"object": {"id": "yoo_456"}},
        )

    assert processed is True
    assert await get_balance(db_session, user.id) == 100


@pytest.mark.asyncio
async def test_handle_webhook_idempotent(db_session):
    user = User(email="t@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()

    payment = Payment(
        user_id=user.id,
        yookassa_payment_id="yoo_dup",
        status="succeeded",
        amount_value="149.00",
        amount_currency="RUB",
        messages_count=100,
        package_name="100 messages",
        confirmed_at=datetime.now(timezone.utc),
    )
    db_session.add(payment)
    await db_session.commit()

    # Already processed — should return True but not add more balance
    processed = await handle_webhook(
        db_session,
        event="payment.succeeded",
        payment_data={"object": {"id": "yoo_dup"}},
    )
    assert processed is True
    assert await get_balance(db_session, user.id) == 0


# --- Отмена платежа (D-16) --------------------------------------------------
#
# ЗАЧЕМ ЭТИ ТЕСТЫ. До D-16 `handle_webhook` возвращал False на всё, кроме
# успеха, поэтому отменённый ЮKassa платёж навсегда оставался `pending`: история
# показывала бы «в обработке» там, где деньги не взяты вовсе. Это не отсутствие
# данных, а неправда о них (прохибиция BILL-07).
#
# Ветка отмены НИЧЕГО НЕ НАЧИСЛЯЕТ — и это её главное свойство, поэтому оно
# проверяется с двух сторон: и «не позвали», и «баланс не изменился». Мока
# достаточно, чтобы поймать вызов; настоящего баланса — чтобы поймать начисление
# в обход мока.


@pytest.mark.asyncio
async def test_a_canceled_webhook_gives_a_pending_payment_a_terminal_status(db_session):
    """Платёж перестаёт висеть `pending`: у него появляется терминальный статус."""
    user = await _user(db_session)
    payment = await _payment(db_session, user)

    with patch(
        "app.services.payment_service.add_messages", new_callable=AsyncMock
    ), patch(
        "app.services.payment_service.invalidate_balance_cache", new_callable=AsyncMock
    ):
        processed = await handle_webhook(
            db_session,
            event=EVENT_CANCELED,
            payment_data={"object": {"id": payment.yookassa_payment_id}},
        )

    assert processed is True
    await db_session.refresh(payment)
    assert payment.status == "canceled"
    # Момент решения пишется в существующую колонку времени подтверждения: это
    # «когда платёж перешёл в терминальное состояние», а второй колонки под
    # отмену D-15 не заводит.
    assert payment.confirmed_at is not None


@pytest.mark.asyncio
async def test_a_canceled_package_payment_credits_nothing(db_session):
    """Отмена пакета не начисляет сообщений и не трогает кэш баланса."""
    user = await _user(db_session)
    payment = await _payment(db_session, user)

    with patch(
        "app.services.payment_service.add_messages", new_callable=AsyncMock
    ) as add_messages_mock, patch(
        "app.services.payment_service.invalidate_balance_cache", new_callable=AsyncMock
    ) as invalidate_mock:
        processed = await handle_webhook(
            db_session,
            event=EVENT_CANCELED,
            payment_data={"object": {"id": payment.yookassa_payment_id}},
        )

    assert processed is True
    add_messages_mock.assert_not_awaited()
    # Баланс не изменился — инвалидировать нечего.
    invalidate_mock.assert_not_awaited()
    assert await get_balance(db_session, user.id) == 0


@pytest.mark.asyncio
async def test_a_canceled_subscription_payment_creates_no_subscription(db_session):
    """Отмена платежа за тариф не заводит подписку."""
    user = await _user(db_session)
    payment = await _payment(
        db_session,
        user,
        yookassa_payment_id="yoo_sub_c",
        kind="subscription",
        plan="basic",
        messages_count=None,
        package_name=None,
    )

    processed = await handle_webhook(
        db_session,
        event=EVENT_CANCELED,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )

    assert processed is True
    count = await db_session.scalar(
        select(func.count()).select_from(Subscription).where(
            Subscription.user_id == user.id
        )
    )
    assert count == 0


@pytest.mark.asyncio
async def test_a_canceled_subscription_payment_does_not_move_an_existing_expiry(
    db_session,
):
    """Отмена не продлевает действующую подписку — срок остаётся прежним."""
    user = await _user(db_session)
    expires_at = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    subscription = Subscription(
        user_id=user.id, plan="basic", expires_at=expires_at, is_active=True
    )
    db_session.add(subscription)
    await db_session.commit()

    payment = await _payment(
        db_session,
        user,
        yookassa_payment_id="yoo_sub_c2",
        kind="subscription",
        plan="basic",
        messages_count=None,
        package_name=None,
    )

    processed = await handle_webhook(
        db_session,
        event=EVENT_CANCELED,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )

    assert processed is True
    await db_session.refresh(subscription)
    assert _utc(subscription.expires_at) == expires_at


@pytest.mark.asyncio
async def test_a_repeated_canceled_webhook_writes_nothing_twice(db_session):
    """Терминальный статус обрабатывается один раз — так же, как успех.

    ЮKassa повторяет доставку уведомления до подтверждения, поэтому второй
    вебхук по тому же платежу — не исключение, а норма. Момент решения обязан
    остаться тем, в который решение было принято.
    """
    user = await _user(db_session)
    decided_at = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
    payment = await _payment(
        db_session,
        user,
        yookassa_payment_id="yoo_c_dup",
        status="canceled",
        confirmed_at=decided_at,
    )

    processed = await handle_webhook(
        db_session,
        event=EVENT_CANCELED,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )

    assert processed is True
    await db_session.refresh(payment)
    assert payment.status == "canceled"
    assert _utc(payment.confirmed_at) == decided_at


@pytest.mark.asyncio
async def test_a_canceled_webhook_does_not_roll_back_a_succeeded_payment(db_session):
    """Проведённый платёж не переводится в отмену припоздавшим уведомлением.

    T-05-10: проверка терминального статуса стоит ДО ветки отмены. Иначе
    уведомление об отмене (подлинное или подделанное) отнимало бы уже выданное.
    """
    user = await _user(db_session)
    confirmed_at = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)
    payment = await _payment(
        db_session,
        user,
        yookassa_payment_id="yoo_done",
        status="succeeded",
        confirmed_at=confirmed_at,
    )

    processed = await handle_webhook(
        db_session,
        event=EVENT_CANCELED,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )

    assert processed is True
    await db_session.refresh(payment)
    assert payment.status == "succeeded"
    assert _utc(payment.confirmed_at) == confirmed_at


@pytest.mark.asyncio
async def test_a_canceled_webhook_for_an_unknown_payment_is_not_processed(db_session):
    """Платёж не из своей базы обработкой не считается."""
    processed = await handle_webhook(
        db_session,
        event=EVENT_CANCELED,
        payment_data={"object": {"id": "yoo_never_seen"}},
    )

    assert processed is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event",
    [
        WebhookNotificationEventType.REFUND_SUCCEEDED,
        WebhookNotificationEventType.PAYMENT_WAITING_FOR_CAPTURE,
    ],
)
async def test_handle_webhook_ignores_an_event_it_does_not_know(db_session, event):
    """Знакомых событий ровно два; остальные пять SDK объявляет, но фаза не берёт.

    Прежняя редакция этого теста звалась «неверное событие» и брала предметом
    проверки отмену платежа. После D-16 отмена — событие ЗНАКОМОЕ, и то
    утверждение стало ложью. Проверяемое свойство сохранено, предмет проверки
    заменён на ДЕЙСТВИТЕЛЬНО неизвестные обработчику события; заодно
    проверяется, что неизвестное событие не меняет статус платежа — прежняя
    редакция звала обработчик по НЕСУЩЕСТВУЮЩЕМУ платежу и потому прошла бы
    даже с полностью сломанной проверкой события.
    """
    user = await _user(db_session)
    payment = await _payment(db_session, user, yookassa_payment_id="yoo_other")

    processed = await handle_webhook(
        db_session,
        event=event,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )

    assert processed is False
    await db_session.refresh(payment)
    assert payment.status == "pending", "неизвестное событие ничего не решает"


# --- Новый срок подписки: обе половины D-04 ---------------------------------
#
# Правило одно, а половин у него две, и каждая ломается отдельно:
#   * срок ещё не истёк → месяц от СРОКА (оплаченный остаток не сгорает);
#   * срок уже истёк    → месяц от СЕГОДНЯ (прошедший месяц не воскресает).
# Реализация, отвечающая только за одну половину, проходит однополовинный тест
# и обкрадывает пользователя во второй, поэтому половины закреплены РАЗНЫМИ
# именованными тестами, а не одним «продление работает».
#
# ПОСЕВЫ СТАВЯТ `expires_at` ЯВНО. У колонки нет `server_default`, но неявное
# «сейчас» сделало бы тест действующей подписки неотличимым от теста истёкшей в
# момент прогона на границе.


async def _subscription_payment(db, user: User, plan: str = "basic", **overrides):
    return await _payment(
        db,
        user,
        yookassa_payment_id=overrides.pop("yookassa_payment_id", "yoo_sub"),
        kind="subscription",
        plan=plan,
        messages_count=None,
        package_name=None,
        **overrides,
    )


@pytest.mark.asyncio
async def test_an_active_subscription_is_extended_from_its_own_expiry(db_session):
    """Остаток не сгорает: месяц прибавляется к СРОКУ, а не к сегодняшнему дню."""
    user = await _user(db_session)
    current = (datetime.now(timezone.utc) + timedelta(days=10)).replace(microsecond=0)
    subscription = Subscription(
        user_id=user.id, plan="basic", expires_at=current, is_active=True
    )
    db_session.add(subscription)
    await db_session.commit()

    payment = await _subscription_payment(db_session, user)

    processed = await handle_webhook(
        db_session,
        event=EVENT_SUCCEEDED,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )

    assert processed is True
    await db_session.refresh(subscription)
    assert _utc(subscription.expires_at) == add_one_month(current)


@pytest.mark.asyncio
async def test_an_expired_subscription_is_extended_from_today(db_session):
    """Прошедший месяц не воскресает: отсчёт идёт от сегодня, а не от старой даты."""
    user = await _user(db_session)
    expired = (datetime.now(timezone.utc) - timedelta(days=40)).replace(microsecond=0)
    subscription = Subscription(
        user_id=user.id, plan="basic", expires_at=expired, is_active=True
    )
    db_session.add(subscription)
    await db_session.commit()

    payment = await _subscription_payment(db_session, user)

    before = datetime.now(timezone.utc)
    processed = await handle_webhook(
        db_session,
        event=EVENT_SUCCEEDED,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )
    after = datetime.now(timezone.utc)

    assert processed is True
    await db_session.refresh(subscription)
    new_expiry = _utc(subscription.expires_at)
    # Окно, а не точка: «сейчас» берётся внутри обработчика. Границы окна —
    # моменты вокруг вызова, поэтому утверждение остаётся точным.
    assert add_one_month(before) <= new_expiry <= add_one_month(after)
    assert new_expiry > datetime.now(timezone.utc), "срок в прошлом ничего не продаёт"


@pytest.mark.asyncio
async def test_a_repeated_subscription_webhook_moves_the_expiry_once(db_session):
    """Близнец `test_handle_webhook_idempotent` для подписки.

    Тот держит идемпотентность на балансе; этот — на сроке. Именно он поймает
    будущую перестановку проверки терминального статуса ЗА ветвление по предмету
    покупки: баланс при такой перестановке уцелел бы, а срок уехал бы на два
    месяца за один платёж.
    """
    user = await _user(db_session)
    payment = await _subscription_payment(db_session, user)

    await handle_webhook(
        db_session,
        event=EVENT_SUCCEEDED,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )
    subscription = (
        await db_session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
    ).scalar_one()
    first_expiry = _utc(subscription.expires_at)

    processed = await handle_webhook(
        db_session,
        event=EVENT_SUCCEEDED,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )

    assert processed is True
    rows = (
        (
            await db_session.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1, "повтор не заводит вторую строку"
    assert _utc(rows[0].expires_at) == first_expiry


@pytest.mark.asyncio
async def test_the_first_purchase_takes_the_plan_from_the_payment(db_session):
    """У пользователя на Free строки подписки нет — она заводится с ПЛАНОМ ПЛАТЕЖА.

    Умолчание модели `Subscription.plan` — `"free"`, и строка, заведённая без
    явного плана, молча выдала бы бесплатный тариф за оплаченный: страница
    вернула бы 200, а пользователь не получил бы купленного.
    """
    user = await _user(db_session)
    payment = await _subscription_payment(db_session, user, plan="pro")

    processed = await handle_webhook(
        db_session,
        event=EVENT_SUCCEEDED,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )

    assert processed is True
    rows = (
        (
            await db_session.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].plan == "pro"
    assert rows[0].is_active is True
