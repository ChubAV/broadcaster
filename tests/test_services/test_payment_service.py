import pytest
import pytest_asyncio
from contextlib import contextmanager
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from yookassa.domain.notification import WebhookNotificationEventType

from app.application.billing.subscription_period import add_one_month
from app.models.subscription import Subscription
from app.models.user import User
from app.models.payment import Payment
from app.services.payment_service import (
    KIND_PACKAGE,
    KIND_SUBSCRIPTION,
    PENDING_INTENT_TTL_HOURS,
    PendingIntentCapError,
    create_payment,
    handle_webhook,
)
from app.services.billing_service import get_balance, add_messages

# Имена событий берутся КОНСТАНТАМИ SDK и в тестах тоже. Литерал с опечаткой не
# поднял бы ошибку: обработчик просто вернул бы False, и тест «событие не
# обработано» прошёл бы по неверной причине — проверяя опечатку, а не правило.
EVENT_SUCCEEDED = WebhookNotificationEventType.PAYMENT_SUCCEEDED
EVENT_CANCELED = WebhookNotificationEventType.PAYMENT_CANCELED

# Цена доступа — машинная строка формата ЮKassa. Выписана здесь ДОСЛОВНО, а не
# прочитана из `Settings`: тест, берущий значение из того же источника, что и
# код, утверждал бы «значение равно самому себе» и пережил бы подмену умолчания
# на «3 000,00 ₽», которую платёжное API отвергает в проде.
ACCESS_PRICE = "3000.00"


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


# --- ПОТОЛОК ОДНОВРЕМЕННЫХ ПОДПИСОЧНЫХ НАМЕРЕНИЙ ----------------------------
#
# ФОРМА ПОТОЛКА — «НЕ БОЛЕЕ ОДНОГО НЕЗАКРЫТОГО ПОДПИСОЧНОГО НАМЕРЕНИЯ НА
# ПОЛЬЗОВАТЕЛЯ» (решение владельца D-I, фаза 05.1). Прежняя форма
# `cap-different-plan` отбирала намерения по НЕСОВПАДЕНИЮ ТАРИФА; в плоской
# модели тариф у платежа один и тот же — его нет вовсе, — поэтому сравнение
# было бы ложно ВСЕГДА и защита перестала бы срабатывать МОЛЧА. Молчаливое
# вырождение и есть предмет замены: потолок либо снимают решением, либо
# переоснуют решением, но не оставляют выродившимся.
#
# ЧТО ПОТОЛОК ЗАКРЫВАЕТ СЕГОДНЯ. Человек, открывший две вкладки оплаты, заводит
# ОДНО намерение, а не два: второй счёт на те же 3000 ₽ означал бы два списания
# за один и тот же месяц доступа, и объяснять человеку, почему с него взяли
# дважды, было бы дороже, чем не дать нажать второй раз.
#
# СРОК ДАВНОСТИ — 24 часа, и он не удобство: подписка на событие
# `payment.canceled` в кабинете ЮKassa НЕ подтверждена (D-27), поэтому
# отменённый платёж остаётся `pending` навсегда, и потолок без срока давности
# запер бы человека, закрывшего вкладку оплаты, без единого пути наружу.
# Просроченное и отменённое намерение открытыми НЕ считаются — иначе один
# брошенный счёт заблокировал бы оплату навсегда.


def _yoo_settings():
    """Мок настроек ЮKassa — по образцу `test_create_payment` выше."""
    mock_settings = MagicMock()
    mock_settings.yookassa_shop_id = "shop123"
    mock_settings.yookassa_secret_key = "secret"
    mock_settings.yookassa_return_url = "https://app.com/billing"
    mock_settings.app_name = "Broadcaster"
    return mock_settings


@contextmanager
def _sdk(payment_id: str = "yoo_new"):
    """Подменённый SDK, ОТДАЮЩИЙ СВОЙ МОК НАРУЖУ.

    Мок нужен телу теста, а не только вызову: главная гарантия порядка
    проверяется ЧИСЛОМ ВЫЗОВОВ (`call_count == 0`), а не разбором исходника.
    Разбор ловит перенос строки; счётчик ловит и перенос, и обход.
    """
    mock_payment = MagicMock()
    mock_payment.id = payment_id
    mock_payment.confirmation = MagicMock()
    mock_payment.confirmation.confirmation_url = f"https://yookassa.ru/pay/{payment_id}"
    with patch(
        "app.services.payment_service.get_settings", return_value=_yoo_settings()
    ), patch(
        "app.services.payment_service.YooPayment.create", return_value=mock_payment
    ) as create_mock:
        yield create_mock


async def _open_intent(
    db,
    user: User,
    *,
    payment_id: str = "yoo_open",
    age_hours: float = 0,
    status: str = "pending",
    kind: str = KIND_SUBSCRIPTION,
) -> Payment:
    """Незакрытое намерение с УПРАВЛЯЕМЫМ возрастом.

    Возраст ставится ЯВНЫМ ПРИСВАИВАНИЕМ после вставки: у колонки
    `created_at` объявлен `server_default=func.now()`, то есть СУБД проставляет
    текущий момент, и прошлого им не выразить вовсе — а срок давности только о
    прошлом и говорит.

    ТАРИФА У НАМЕРЕНИЯ НЕТ. Параметр `plan` снят вместе с формой
    `cap-different-plan`: намерения плоской модели неразличимы по предмету
    покупки, и оставить его значило бы дать тесту рычаг, которого нет у
    продукта.
    """
    payment = await _payment(
        db,
        user,
        yookassa_payment_id=payment_id,
        kind=kind,
        plan=None,
        status=status,
        amount_value=ACCESS_PRICE if kind == KIND_SUBSCRIPTION else "149.00",
        messages_count=None if kind == KIND_SUBSCRIPTION else 100,
        package_name=None if kind == KIND_SUBSCRIPTION else "100 messages",
    )
    payment.created_at = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    await db.commit()
    await db.refresh(payment)
    return payment


async def _payments_count(db, user: User) -> int:
    return await db.scalar(
        select(func.count()).select_from(Payment).where(Payment.user_id == user.id)
    )


async def _subscribe(db, user: User, *, price: str = ACCESS_PRICE):
    """Намерение оплатить ДОСТУП — без тарифа и без записанного ответа гарда.

    `switch_authorized=None` не умолчание, а запись факта: правила смены тарифа
    больше нет, ответа никто не давал (T-05.1-11). Ровно это подаёт обработчик
    формы, и тест, подающий `True`, проверял бы вход, которого продукт не
    производит.
    """
    return await create_payment(
        db,
        user_id=user.id,
        price=price,
        kind=KIND_SUBSCRIPTION,
        plan=None,
        package_name=None,
        messages_count=None,
        switch_authorized=None,
    )


@pytest.mark.asyncio
async def test_a_second_subscription_intent_is_refused_before_the_money_moves(
    db_session,
):
    """Второе намерение при ОДНОМ уже открытом не заводится — и своим типом отказа.

    Чужой тип здесь не годится: `PaymentCreationError` говорит «ЮKassa не
    создала платёж», а здесь ЮKassa не спрашивали вовсе — отказали мы, и
    человеку об этом сообщается ДРУГИМИ словами.

    Тарифы в утверждении больше не участвуют: предмет покупки один, и «второе
    намерение» отличается от первого только тем, что первое ещё не закрыто.
    """
    user = await _user(db_session)
    await _open_intent(db_session, user, payment_id="yoo_first")
    before = await _payments_count(db_session, user)

    with _sdk("yoo_second"):
        with pytest.raises(PendingIntentCapError):
            await _subscribe(db_session, user)

    assert await _payments_count(db_session, user) == before, (
        "отвергнутое намерение оставило строку в `payments`"
    )


@pytest.mark.asyncio
async def test_the_refusal_never_reaches_yookassa(db_session):
    """Отказ происходит ДО обращения к ЮKassa — ЗЕРКАЛО ловушки T-05-49.

    Отдельный тест, а не утверждение внутри предыдущего, и это существенно.
    Запись в БД стоит ПОСЛЕ вызова SDK, потому что строка без платежа у ЮKassa
    висела бы `pending` вечно. Проверка потолка, поставленная ПОСЛЕ вызова,
    даёт зеркальную беду: платёж существует У НИХ и не существует у нас — он не
    придёт ни успехом, ни отменой. Одним тестом обе стороны не держатся.
    """
    user = await _user(db_session)
    await _open_intent(db_session, user, payment_id="yoo_first")

    with _sdk("yoo_second") as create_mock:
        with pytest.raises(PendingIntentCapError):
            await _subscribe(db_session, user)

    assert create_mock.call_count == 0, (
        f"ЮKassa вызвана {create_mock.call_count} раз(а) до отказа: платёж создан "
        "у них и не создан у нас"
    )


@pytest.mark.asyncio
async def test_a_stale_intent_does_not_block_a_new_one(db_session):
    """Потолок не превращается в запирание: старое намерение покупке не мешает.

    Срок давности — единственный выход, пока подписка на `payment.canceled` не
    подтверждена (D-27): отменённый платёж на проде остаётся `pending` навсегда.

    ⚠️ ЭТОТ ЗЕЛЁНЫЙ ТЕСТ ДОКАЗЫВАЕТ ВТОРОЕ ОСТАТОЧНОЕ ОКНО ПОТОЛКА, А НЕ ТОЛЬКО
    УДОБСТВО ПОЛЬЗОВАТЕЛЯ, И МОЛЧАТЬ ОБ ЭТОМ БЫЛО ДЕФЕКТОМ. Намерение старше
    `PENDING_INTENT_TTL_HOURS` перестаёт СЧИТАТЬСЯ, но ОПЛАЧИВАЕМЫМ быть не
    перестаёт: своей строки оно не теряет, терминальным не становится, и ссылка
    на оплату у ЮKassa продолжает работать. Значит после этого теста у
    пользователя ДВА оплачиваемых намерения — то самое состояние, ради сужения
    которого потолок и существует. Достигается оно не гонкой, а ожиданием, то
    есть ДЕТЕРМИНИРОВАННО и шире гонки. В плоской модели цена окна названа
    деньгами прямо: два оплачиваемых счёта на 3000 ₽ за один и тот же месяц
    доступа.

    Пока докстринг молчал, `create_payment` называл это состояние недостижимым,
    имея этот тест зелёным в двухстах строках от себя (гэп 2 раунда 5). Теперь
    оба окна названы там прямо, и новая редакция того абзаца ссылается сюда по
    имени — утверждение и его опровержение обязаны знать друг о друге.

    ЗАКРЫТИЕ ОКНА — РАБОТА СВОЕГО РАЗМЕРА, И ЭТОТ ТЕСТ ЕЁ НЕ ЖДЁТ. Нужно либо
    снимать намерение С ОПЛАТЫ при истечении срока давности (отменять его у
    ЮKassa и переводить строку в терминальный статус), либо подтвердить подписку
    на `payment.canceled` (D-27). Молчаливого исключения строки из подсчёта,
    которым окно «закрыто» сегодня, для этого мало.
    """
    assert PENDING_INTENT_TTL_HOURS == 24, (
        "срок давности назван ответом чекпойнта задачи 1 плана 05-15 — 24 часа"
    )
    user = await _user(db_session)
    await _open_intent(
        db_session,
        user,
        payment_id="yoo_stale",
        age_hours=PENDING_INTENT_TTL_HOURS + 1,
    )

    with _sdk("yoo_new"):
        result = await _subscribe(db_session, user)

    assert result["payment_id"] == "yoo_new"
    assert await _payments_count(db_session, user) == 2


@pytest.mark.asyncio
async def test_a_canceled_intent_does_not_block_a_new_one(db_session):
    """Отменённое намерение открытым НЕ считается — брошенный счёт не запирает.

    Утверждение отдельное от `test_a_terminal_payment_never_blocks_a_new_one`, и
    это не дубликат: тот держит ОБА терминальных статуса разом и отвечает на
    вопрос «выходит ли платёж из терминального состояния»; здесь предмет узкий и
    названный решением D-I — ЕДИНСТВЕННОЕ намерение пользователя, и оно
    отменено. При потолке «не более одного незакрытого» именно этот случай стал
    бы вечным замком, если бы отбор считал строку по факту существования, а не
    по статусу: человек, отказавшийся от оплаты, не смог бы заплатить НИКОГДА.
    """
    user = await _user(db_session)
    await _open_intent(
        db_session, user, payment_id="yoo_gone", status="canceled"
    )

    with _sdk("yoo_new"):
        result = await _subscribe(db_session, user)

    assert result["payment_id"] == "yoo_new"


@pytest.mark.asyncio
async def test_a_user_without_open_intents_pays_without_obstruction(db_session):
    """Ноль незакрытых намерений — оплата проходит. Граница потолка снизу.

    Без этого утверждения тесты потолка доказывали бы только «когда отказывает»,
    и потолок, отвергающий ВСЁ, прошёл бы их все до одного.
    """
    user = await _user(db_session)
    assert await _payments_count(db_session, user) == 0

    with _sdk("yoo_only"):
        result = await _subscribe(db_session, user)

    assert result["payment_id"] == "yoo_only"
    assert await _payments_count(db_session, user) == 1


@pytest.mark.asyncio
async def test_an_intent_of_another_user_does_not_reach_over(db_session):
    """Потолок считает намерения ВЛАДЕЛЬЦА, а не все незакрытые в базе.

    Отбор без условия по пользователю зеленел бы на всех утверждениях выше — они
    работают с одним человеком — и запирал бы оплату всему продукту, как только
    хоть у кого-то повиснет неоплаченный счёт. Дефект такого рода не ловится
    ничем, кроме второго пользователя в тесте.
    """
    stranger = await _user(db_session, "cap-stranger@t.com")
    await _open_intent(db_session, stranger, payment_id="yoo_stranger")

    buyer = await _user(db_session, "cap-buyer@t.com")
    with _sdk("yoo_buyer"):
        result = await _subscribe(db_session, buyer)

    assert result["payment_id"] == "yoo_buyer", (
        "чужое незакрытое намерение перекрыло оплату"
    )


@pytest.mark.asyncio
async def test_a_terminal_payment_never_blocks_a_new_one(db_session):
    """Из терминального статуса платёж не выходит — мешать он не вправе никогда."""
    user = await _user(db_session)
    await _open_intent(
        db_session, user, payment_id="yoo_done", status="succeeded"
    )
    await _open_intent(
        db_session, user, payment_id="yoo_gone", status="canceled"
    )

    with _sdk("yoo_new"):
        result = await _subscribe(db_session, user)

    assert result["payment_id"] == "yoo_new"


@pytest.mark.asyncio
async def test_a_package_payment_is_outside_the_cap(db_session):
    """Два утверждения в ОБЕ стороны: пакет и подписка друг другу не мешают.

    Потолок отвечает на вопрос «сколько раз человек может начать оплату
    ДОСТУПА»; покупка сообщений — другой предмет и другие деньги. Задевать её
    этим правилом не за что — ни как препятствие, ни как жертву.
    """
    buyer = await _user(db_session, "cap-a@t.com")
    await _open_intent(db_session, buyer, payment_id="yoo_access")

    with _sdk("yoo_pack"):
        package = await create_payment(
            db_session,
            user_id=buyer.id,
            price="149.00",
            kind=KIND_PACKAGE,
            package_name="100 messages",
            messages_count=100,
            switch_authorized=None,
        )
    assert package["payment_id"] == "yoo_pack", "подписочное намерение не даёт купить пакет"

    other = await _user(db_session, "cap-b@t.com")
    await _open_intent(
        db_session,
        other,
        payment_id="yoo_pack_open",
        kind=KIND_PACKAGE,
    )

    with _sdk("yoo_sub_new"):
        subscription = await _subscribe(db_session, other)
    assert subscription["payment_id"] == "yoo_sub_new", (
        "пакетный платёж не даёт купить подписку"
    )


@pytest.mark.asyncio
async def test_the_refusal_leaves_its_own_trace(db_session):
    """След обязателен: без него отказ неотличим от отказа ЮKassa.

    Уровень `warning`, а не `info`, по той же причине, что у
    `subscription_plan_preserved`: это исход, по которому к нам придёт человек.
    """
    user = await _user(db_session)
    await _open_intent(db_session, user, payment_id="yoo_first")

    with _sdk("yoo_second"), patch("app.services.payment_service.logger") as spy:
        with pytest.raises(PendingIntentCapError):
            await _subscribe(db_session, user)

    refusals = [
        call
        for call in spy.warning.call_args_list
        if call.args and call.args[0] == "subscription_intent_cap_reached"
    ]
    assert refusals, "отказ по потолку не оставил следа в журнале"
    fields = refusals[0].kwargs
    assert fields.get("user_id") == user.id
    assert fields.get("open_intents") == 1, "журнал не называет числа намерений"
