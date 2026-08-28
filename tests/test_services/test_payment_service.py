import ast
import pytest
import pytest_asyncio
from contextlib import contextmanager
from pathlib import Path
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

# ИМЯ ЖУРНАЛЬНОГО КЛЮЧА ВЫПИСАНО ДОСЛОВНО, А НЕ ИМПОРТИРОВАНО ИЗ СЕРВИСА. Тест,
# берущий ключ из того же места, что и код, утверждал бы «значение равно самому
# себе» и пережил бы любое переименование молча — а ключ журнала есть контракт с
# читателем логов, и меняться он обязан ЗАМЕТНО.
PACKAGE_NOT_CREDITED_KEY = "webhook_package_payment_not_credited"

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

# НАЗНАЧЕНИЕ ПОДПИСОЧНОГО ПЛАТЕЖА — выписано ДОСЛОВНО, а не импортировано из
# `app.constants`, по тому же правилу, что `ACCESS_PRICE` и
# `PACKAGE_NOT_CREDITED_KEY` двумя абзацами выше. Тест, берущий строку из того же
# источника, что и код, утверждал бы «значение равно самому себе» и пережил бы
# любую подмену формулировки молча. А назначение платежа есть КОНТРАКТ С
# ПОКУПАТЕЛЕМ: его печатают страница оплаты ЮKassa, фискальный чек и кабинет
# мерчанта, — и меняться он обязан ЗАМЕТНО.
#
# Та же строка объявлена ВТОРОЙ раз в ветке пустого тарифа
# `app/templates/billing/includes/payment_row.html`, и два объявления связаны
# тестом `test_the_two_surfaces_of_the_payment_purpose_speak_one_string`, а не
# соглашением.
SUBSCRIPTION_DESCRIPTION_TEXT = "Доступ к системе"

# Исходник денежного модуля читается тестом разбора синтаксического дерева:
# утверждение «значение назначения есть ИМЯ, а не собранная строка» о теле вызова
# не выражается — снаружи любая строка выглядит строкой.
PAYMENT_SERVICE_PY = (
    Path(__file__).resolve().parents[2] / "app" / "services" / "payment_service.py"
)


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


# --- Пакетное уведомление ПОСЛЕ снятия валюты сообщений (T-05.1-24) ----------
#
# ПОЧЕМУ ВЕТКА НЕ УДАЛЕНА ЦЕЛИКОМ. Уведомление о покупке пакета всё ещё может
# прийти по платежу, заведённому ДО выката: человек нажал «купить» вчера,
# ЮKassa подтвердила сегодня. Купить пакет больше негде — ни формой, ни
# маршрутом, — но взятые деньги обязаны получить терминальный статус.
#
# ⚠️ ОТВЕТ ОБЯЗАН БЫТЬ УСПЕШНЫМ, А НЕ ПЯТИСОТКОЙ. Возврат 5xx спровоцировал бы
# новую попытку доставки ЮKassa по УЖЕ ПРОВЕДЁННОМУ платежу — то есть отказ,
# который сам себя повторяет.


@pytest.mark.asyncio
async def test_a_package_notification_marks_the_payment_and_credits_nothing(
    db_session,
):
    """Пакетное уведомление проводит платёж и НЕ начисляет ничего.

    Валюта сообщений снята из продукта целиком: начислять больше нечего, и
    начисление здесь означало бы, что величина, которой не существует, у
    кого-то всё-таки растёт.
    """
    user = await _user(db_session)
    payment = await _payment(db_session, user, yookassa_payment_id="yoo_pkg_late")

    processed = await handle_webhook(
        db_session,
        event=EVENT_SUCCEEDED,
        payment_data={"object": {"id": "yoo_pkg_late"}},
    )

    assert processed is True, "успешный ответ подменён отказом"
    await db_session.refresh(payment)
    assert payment.status == "succeeded"
    assert payment.confirmed_at is not None

    # ⚠️ ПРЕДМЕТ ЭТОГО УТВЕРЖДЕНИЯ СМЕНИЛСЯ ВМЕСТЕ С РЕВИЗИЕЙ `0020`. Прежде оно
    # считало строки журнала операций по остатку сообщений — таблицы, которой
    # больше нет: «начислить пакет» теперь невозможно ПО СХЕМЕ, и утверждать это
    # прогоном значило бы утверждать про SQLAlchemy, а не про продукт.
    #
    # Осталась граница, которая по схеме НЕ закрыта и закрыта быть не может:
    # пакетный платёж не имеет права выдать ДОСТУП. Обе величины лежат теперь в
    # одной таблице подписок, и ветка, перепутавшая предмет покупки, выдала бы
    # месяц доступа за цену пакета. Проверка идёт по СТРОКАМ, а не по моку: мок
    # ловит вызов известного имени, а строка, записанная в обход него, осталась
    # бы незамеченной.
    granted = await db_session.scalar(
        select(func.count()).select_from(Subscription)
    )
    assert granted == 0, f"пакетный платёж завёл {granted} строк доступа, а не ноль"


@pytest.mark.asyncio
async def test_a_package_notification_records_the_fact_by_its_own_key(db_session):
    """У непроведённого начисления есть СЛЕД, а не молчание.

    Платёж, помеченный проведённым без выдачи чего бы то ни было, обязан
    оставить в журнале причину: жалоба «я заплатил и ничего не получил» иначе
    не проверяема ничем, а ветка выглядит потерянным начислением.
    """
    user = await _user(db_session)
    await _payment(db_session, user, yookassa_payment_id="yoo_pkg_logged")

    with patch("app.services.payment_service.logger") as log:
        await handle_webhook(
            db_session,
            event=EVENT_SUCCEEDED,
            payment_data={"object": {"id": "yoo_pkg_logged"}},
        )

    keys = [call.args[0] for call in log.info.call_args_list if call.args]
    assert PACKAGE_NOT_CREDITED_KEY in keys, keys


@pytest.mark.asyncio
async def test_a_repeated_package_notification_is_still_processed_only_once(
    db_session,
):
    """Повторная доставка того же уведомления не даёт двойной обработки.

    ПАРНЫЙ ТЕСТ К ДВУМ ПРЕДЫДУЩИМ. Ветка перестала начислять, и соблазн
    посчитать защиту от двойной обработки ненужной появляется ровно здесь: она
    держит не только начисление, но и МОМЕНТ проведения платежа. Сдвинутая
    второй доставкой дата подтверждения — это неправда о том, когда деньги были
    взяты.
    """
    user = await _user(db_session)
    payment = await _payment(db_session, user, yookassa_payment_id="yoo_pkg_twice")

    first = await handle_webhook(
        db_session,
        event=EVENT_SUCCEEDED,
        payment_data={"object": {"id": "yoo_pkg_twice"}},
    )
    await db_session.refresh(payment)
    confirmed_once = _utc(payment.confirmed_at)

    second = await handle_webhook(
        db_session,
        event=EVENT_SUCCEEDED,
        payment_data={"object": {"id": "yoo_pkg_twice"}},
    )

    assert first is True and second is True, "повтор ответил отказом"
    await db_session.refresh(payment)
    assert _utc(payment.confirmed_at) == confirmed_once, (
        "повторная доставка сдвинула момент проведения платежа"
    )
    granted = await db_session.scalar(
        select(func.count()).select_from(Subscription)
    )
    assert granted == 0, f"пакетный платёж завёл {granted} строк доступа, а не ноль"


# --- Отмена платежа (D-16) --------------------------------------------------
#
# ЗАЧЕМ ЭТИ ТЕСТЫ. До D-16 `handle_webhook` возвращал False на всё, кроме
# успеха, поэтому отменённый ЮKassa платёж навсегда оставался `pending`: история
# показывала бы «в обработке» там, где деньги не взяты вовсе. Это не отсутствие
# данных, а неправда о них (прохибиция BILL-07).
#
# Ветка отмены НИЧЕГО НЕ НАЧИСЛЯЕТ — и это её главное свойство. Проверяется оно
# по СТРОКАМ журнала операций, а не по моку начисляющей функции: начислять после
# снятия валюты сообщений нечем и нечего, функции больше не существует, а строка,
# записанная в обход известного имени, моком не ловилась бы вовсе.


@pytest.mark.asyncio
async def test_a_canceled_webhook_gives_a_pending_payment_a_terminal_status(db_session):
    """Платёж перестаёт висеть `pending`: у него появляется терминальный статус."""
    user = await _user(db_session)
    payment = await _payment(db_session, user)

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
    """Отмена пакета не оставляет ни одной строки в журнале операций."""
    user = await _user(db_session)
    payment = await _payment(db_session, user)

    processed = await handle_webhook(
        db_session,
        event=EVENT_CANCELED,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )

    assert processed is True
    granted = await db_session.scalar(
        select(func.count()).select_from(Subscription)
    )
    assert granted == 0, f"пакетный платёж завёл {granted} строк доступа, а не ноль"


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
        user_id=user.id, expires_at=expires_at, is_active=True
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
        user_id=user.id, expires_at=current, is_active=True
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
        user_id=user.id, expires_at=expired, is_active=True
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
async def test_a_confirmed_subscription_payment_reopens_access_at_once(db_session):
    """Оплативший получает доступ НЕМЕДЛЕННО, а не через TTL кэша.

    ⚠️ ЭТО ДЕФЕКТ ПЛОСКОЙ МОДЕЛИ, А НЕ УЛУЧШЕНИЕ. Инвалидация кэша стояла только
    в ПАКЕТНОЙ ветке обработчика — после начисления сообщений, — и была там
    верна: подписка баланса не меняла. С переводом гейта на вердикт ДОСТУПА
    подписочная ветка стала писателем ровно той величины, которую кэш и хранит:
    без вызова здесь человек, который только что заплатил, до минуты видел бы
    «доступ закончился» на всех страницах и не рассылал бы по расписанию —
    ровно то, за что он заплатил, чтобы это прекратилось.

    Вызов утверждается ОДИН и С ВЛАДЕЛЬЦЕМ ПЛАТЕЖА: сброшенный чужой ключ был бы
    минутой неверных вердиктов у постороннего пользователя.
    """
    user = await _user(db_session)
    payment = await _subscription_payment(
        db_session, user, yookassa_payment_id="yoo_sub_access"
    )

    with patch(
        "app.services.payment_service.invalidate_access_cache", new_callable=AsyncMock
    ) as invalidate_access:
        processed = await handle_webhook(
            db_session,
            event=EVENT_SUCCEEDED,
            payment_data={"object": {"id": payment.yookassa_payment_id}},
        )

    assert processed is True
    invalidate_access.assert_awaited_once_with(user.id)


@pytest.mark.asyncio
async def test_the_first_purchase_creates_the_row_from_today(db_session):
    """У пользователя строки подписки нет — она заводится СРОКОМ ОТ СЕГОДНЯ.

    ⚠️ ПРЕЖНИЙ ПРЕДМЕТ ЭТОГО ТЕСТА СНЯТ РЕВИЗИЕЙ `0020` ВМЕСТЕ С КОЛОНКОЙ ТАРИФА.
    Он назывался `test_the_first_purchase_takes_the_plan_from_the_payment` и
    держал единственное место, где имя тарифа платежа становилось именем тарифа
    подписки. Тест ПЕРЕЦЕЛЕН, а не удалён: ветка первой вставки жива, и у неё
    осталась своя граница — она обязана считать срок от СЕГОДНЯ, а не от чего бы
    то ни было ещё. Продлевать ей нечего: активной строки нет, значит нет и
    оплаченного остатка, к которому мог бы прибавиться месяц. Удали мы тест
    вместе с колонкой — ветка первой вставки осталась бы без свидетеля вовсе.
    """
    user = await _user(db_session)
    bought_at = datetime.now(timezone.utc)
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
    assert rows[0].is_active is True
    # Месяц ОТ СЕГОДНЯ, тем же объявлением, что двигает срок действующей
    # подписки, — а не второй формулой рядом.
    assert _utc(rows[0].expires_at) >= add_one_month(bought_at)
    assert _utc(rows[0].expires_at) <= add_one_month(datetime.now(timezone.utc))


# --- ПРОДЛЕНИЕ ДЕЙСТВУЮЩЕЙ ПОДПИСКИ ПОСЛЕ СНЯТИЯ МАТРИЦЫ ТАРИФОВ -------------
#
# ЧТО ЗАКРЫВАЮТ ЭТИ ДВА ТЕСТА. План 05.1-07 снял из `_apply_extension` решение о
# ПЛАНЕ целиком: записанный ответ гарда, сравнение рангов, долю месяца и
# конверсию остатка. Осталась одна пара операторов — снятие признака живости и
# сдвиг срока, — и обе стороны этой пары обязаны иметь свидетеля, иначе «ветку
# случайно вернули» и «ветка отсутствует намеренно» неотличимы по прогону.


@pytest.mark.asyncio
async def test_a_confirmed_payment_only_moves_the_date(db_session):
    """Подтверждённый платёж двигает СРОК и не трогает больше ничего.

    ⚠️ ТЕСТ УТВЕРЖДАЕТ ОТСУТСТВИЕ ВЕТВЛЕНИЯ, А НЕ ЕГО ИСХОД, И ЭТО РАЗНЫЕ ВЕЩИ.
    Прежде план подписки перезаписывался планом платежа — либо сохранялся, если
    правило перехода отвергало его. Тарифов больше нет (D-A), и платёж, несущий в
    журнальной колонке имя тарифа, обязан двинуть срок и не тронуть больше
    НИЧЕГО.

    ⚠️ КОЛОНКИ, ПО КОТОРОЙ ЭТО ПРОВЕРЯЛОСЬ, БОЛЬШЕ НЕТ (ревизия `0020`), И
    УТВЕРЖДЕНИЕ ПЕРЕНЕСЕНО НА ТУ, ЧТО ОСТАЛАСЬ. Прежде тест требовал, чтобы
    `subscription.plan` не изменился; теперь измениться в строке подписки может
    только `is_active` и сам срок, и утверждается ОБА: строка та же самая (по
    идентификатору), вторая не заведена, признак активности не снят. Что решения
    о плане не вернулось в `_apply_extension` вовсе, держит греп-гейт
    `tests/test_application/test_no_metering_remains.py` и AST-ловушка порядка
    `test_the_liveness_is_sampled_before_the_date_moves`.
    """
    user = await _user(db_session)
    current = (datetime.now(timezone.utc) + timedelta(days=10)).replace(microsecond=0)
    subscription = Subscription(
        user_id=user.id, expires_at=current, is_active=True
    )
    db_session.add(subscription)
    await db_session.commit()
    row_id = subscription.id

    payment = await _subscription_payment(db_session, user, plan="basic")

    processed = await handle_webhook(
        db_session,
        event=EVENT_SUCCEEDED,
        payment_data={"object": {"id": payment.yookassa_payment_id}},
    )

    assert processed is True
    await db_session.refresh(subscription)
    assert _utc(subscription.expires_at) == add_one_month(current), (
        "срок не сдвинут на календарный месяц от собственной даты"
    )
    assert subscription.is_active is True
    assert subscription.id == row_id, "продлена не та строка"
    rows = await db_session.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.user_id == user.id)
    )
    assert rows == 1, f"продление завело вторую строку: строк {rows}"


@pytest.mark.asyncio
async def test_the_journal_of_an_extension_names_the_liveness_of_the_period(db_session):
    """Журнал различает ПРОДЛЕНИЕ живого срока и ВОЗВРАТ после перерыва.

    Строка подписки после обоих исходов выглядит одинаково — дата в будущем, —
    и человек, у которого «пропали дни», приходит с этим к нам. Признак живости
    потерял ветвление вместе с матрицей тарифов, но не потерял смысла: он и есть
    то единственное, что эти два исхода различает. Снятый ПОСЛЕ сдвига, он
    отвечал бы «живо» в обоих — то есть поле молча стало бы константой.
    """
    user = await _user(db_session)
    live = (datetime.now(timezone.utc) + timedelta(days=10)).replace(microsecond=0)
    subscription = Subscription(
        user_id=user.id, expires_at=live, is_active=True
    )
    db_session.add(subscription)
    await db_session.commit()
    payment = await _subscription_payment(
        db_session, user, yookassa_payment_id="yoo_sub_live"
    )

    with patch("app.services.payment_service.logger") as spy:
        await handle_webhook(
            db_session,
            event=EVENT_SUCCEEDED,
            payment_data={"object": {"id": payment.yookassa_payment_id}},
        )

    assert _extension_records(spy) == [True], "продление живого срока не названо"

    subscription.expires_at = (datetime.now(timezone.utc) - timedelta(days=40)).replace(
        microsecond=0
    )
    await db_session.commit()
    lapsed = await _subscription_payment(
        db_session, user, yookassa_payment_id="yoo_sub_lapsed"
    )

    with patch("app.services.payment_service.logger") as spy:
        await handle_webhook(
            db_session,
            event=EVENT_SUCCEEDED,
            payment_data={"object": {"id": lapsed.yookassa_payment_id}},
        )

    assert _extension_records(spy) == [False], (
        "возврат после перерыва записан как продление живого срока — признак "
        "снят ПОСЛЕ сдвига и стал константой"
    )


def _extension_records(spy) -> list[bool]:
    """Значения `period_was_live` у записей продления, в порядке испускания."""
    return [
        call.kwargs.get("period_was_live")
        for call in spy.info.call_args_list
        if call.args and call.args[0] == "subscription_extended"
    ]


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
async def test_the_intent_records_that_no_rule_was_asked(db_session):
    """Намерение записывает `NULL` в колонку ответа гарда — и наружу его не шлёт.

    ⚠️ СВИДЕТЕЛЬ ПЕРЕЦЕЛЕН ПЛАНОМ 05.1-07, А НЕ ЗАВЕДЁН НА ПУСТОМ МЕСТЕ. Прежде
    границу держали `test_the_deal_cannot_be_sold_without_recording_its_authorization`
    и `test_the_intent_stage_records_its_answer_on_the_payment`: оба утверждали,
    что ответ ГАРДА уезжает на строку платежа. Гарда смены тарифа не существует,
    и оба теста сняты вместе с ним, а колонка ЖУРНАЛЬНАЯ и осталась. Утверждать
    о ней теперь нужно ДРУГОЕ, и это другое — не слабее: значение `NULL` есть
    ЗАПИСЬ ФАКТА «правило не спрашивали», а литерал `True` был бы подписью под
    сделкой от имени правила, которого нет (T-05.1-11).

    ТРИ УТВЕРЖДЕНИЯ, И НИ ОДНО НЕ ЗАМЕНЯЕТ ДВА ОСТАЛЬНЫХ: что записано `NULL`;
    что аргумент нельзя ПРОПУСТИТЬ (иначе умолчание вернуло бы дисциплину
    вызывающего); что значение не уезжает в `metadata` платежа — всё, ушедшее в
    ЮKassa, возвращается оттуда входом из сети (T-05-08, T-05-68).
    """
    user = await _user(db_session)

    with _sdk("yoo_recorded") as create_mock:
        await _subscribe(db_session, user)

    payment = (
        await db_session.execute(
            select(Payment).where(Payment.yookassa_payment_id == "yoo_recorded")
        )
    ).scalar_one()
    assert payment.switch_authorized is None, (
        "намерение записало ответ правила, которого никто не спрашивал"
    )

    body = create_mock.call_args.args[0]
    assert "switch_authorized" not in str(body), (
        "условие сделки уехало в ЮKassa и вернётся оттуда входом из сети"
    )

    with pytest.raises(TypeError):
        await create_payment(
            db_session,
            user_id=user.id,
            price=ACCESS_PRICE,
            kind=KIND_SUBSCRIPTION,
            plan=None,
            package_name=None,
            messages_count=None,
        )


def _subscription_description_values() -> list[ast.AST]:
    """Узлы значений, присваиваемых `description` в ВЕТКЕ ПОДПИСКИ `create_payment`.

    Ветка ищется по СРАВНЕНИЮ с `KIND_SUBSCRIPTION`, а не по номеру строки:
    привязка к номеру рассыпалась бы на первой же правке соседнего абзаца.
    Ветка «иначе» (пакетная) сюда не попадает — у неё своё назначение, и её
    снятие есть предмет отложенного WR-05.
    """
    tree = ast.parse(PAYMENT_SERVICE_PY.read_text(encoding="utf-8"))
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "create_payment"
    ]
    assert functions, "функция create_payment не найдена в исходнике сервиса"

    values: list[ast.AST] = []
    for function in functions:
        for node in ast.walk(function):
            if not isinstance(node, ast.If):
                continue
            test = node.test
            if not isinstance(test, ast.Compare):
                continue
            names = [
                operand.id
                for operand in [test.left, *test.comparators]
                if isinstance(operand, ast.Name)
            ]
            if "KIND_SUBSCRIPTION" not in names:
                continue
            for statement in node.body:
                for inner in ast.walk(statement):
                    if not isinstance(inner, ast.Assign):
                        continue
                    if any(
                        isinstance(target, ast.Name) and target.id == "description"
                        for target in inner.targets
                    ):
                        values.append(inner.value)
    return values


@pytest.mark.asyncio
async def test_the_subscription_payment_names_its_purpose_in_words(db_session):
    """Подписочный платёж уезжает в SDK, НАЗЫВАЯ СВОЙ ПРЕДМЕТ СЛОВАМИ.

    ⚠️ УТВЕРЖДЕНИЕ СНЯТО С ТЕЛА ВЫЗОВА, А НЕ С ИСХОДНИКА. Строка назначения
    пересекает границу доверия: её печатают покупателю страница оплаты ЮKassa,
    фискальный чек и кабинет мерчанта. Разбор исходника поймал бы переписанное
    выражение, но не поймал бы ключ, переименованный в теле запроса, — а именно
    ключ `description` и есть то, что третья сторона показывает человеку
    (T-05.1-35). До этого теста назначение не утверждал в суите НИ ОДИН тест.

    ВТОРОЕ УТВЕРЖДЕНИЕ — ОТ ДЕФЕКТА, А НЕ ОТ ФОРМУЛИРОВКИ: текстового
    представления пустого значения в назначении нет. Оно переживёт любую
    будущую правку самих слов и покраснеет ровно тогда, когда снятое поле
    тарифа снова начнёт подставляться в чек.
    """
    user = await _user(db_session)

    with _sdk("yoo_named") as create_mock:
        await _subscribe(db_session, user)

    body = create_mock.call_args.args[0]
    assert body["description"] == SUBSCRIPTION_DESCRIPTION_TEXT, (
        "назначение подписочного платежа разошлось со строкой, которую печатает "
        "журнал платежей"
    )
    assert str(None) not in body["description"], (
        "в фискальный чек уехало текстовое представление пустого значения"
    )


@pytest.mark.asyncio
async def test_the_purpose_of_a_subscription_payment_is_not_a_substitution(db_session):
    """У назначения НЕТ МЕСТА ВСТАВКИ: непустой тариф даёт ТУ ЖЕ строку.

    Это не перефразировка соседнего теста, а НАБЛЮДАЕМОЕ СЛЕДСТВИЕ, которого у
    него нет. Реализация вида «если тариф пуст — одно, иначе — печатать тариф»
    прошла бы соседний тест целиком: единственный вызывающий подаёт пустой
    тариф намеренно (`app/pages/billing.py`). Но она оставила бы имени снятого
    тарифа ЖИВОЙ ПУТЬ в фискальный чек — путь, который открылся бы первому же
    будущему вызывающему. Этот тест закрывает именно её.

    Аргументы — те же, что подаёт `_subscribe`, кроме тарифа: он равен `basic`,
    то есть имени тарифа снятой эпохи.
    """
    user = await _user(db_session)

    with _sdk("yoo_no_slot") as create_mock:
        await create_payment(
            db_session,
            user_id=user.id,
            price=ACCESS_PRICE,
            kind=KIND_SUBSCRIPTION,
            plan="basic",
            package_name=None,
            messages_count=None,
            switch_authorized=None,
        )

    body = create_mock.call_args.args[0]
    assert body["description"] == SUBSCRIPTION_DESCRIPTION_TEXT, (
        "имя тарифа доехало до назначения платежа — место вставки осталось"
    )
    assert "basic" not in body["description"].lower(), (
        "имя тарифа снятой эпохи печатается покупателю в чеке"
    )


def test_the_subscription_purpose_is_a_name_and_not_an_fstring():
    """Значение, присваиваемое `description` в ветке подписки, — ИМЯ.

    ⚠️ РАЗБОР ИСХОДНИКА ЗДЕСЬ НЕЗАМЕНИМ ТЕЛОМ ВЫЗОВА. Снаружи собранная строка
    неотличима от постоянной: обе приезжают строкой. Утверждение «места вставки
    нет ПО ПОСТРОЕНИЮ» выражается только о синтаксическом дереве, и оно и есть
    гарантия того, что ни одно значение — ни из формы, ни из БД, ни из настроек
    — в текст, видимый третьей стороне, попасть не может (T-05.1-34).

    Образцы разбора по дереву в проекте есть:
    `tests/test_migrations/test_0020_flat_subscription.py` и
    `tests/test_application/test_declared_invariants.py`.
    """
    values = _subscription_description_values()

    assert values, (
        "в ветке подписки `create_payment` не нашлось присваивания `description`"
    )
    for value in values:
        assert isinstance(value, ast.Name), (
            "назначение подписочного платежа снова собирается выражением "
            f"({type(value).__name__}) — у него появилось место вставки"
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
async def test_a_user_without_an_open_intent_pays_without_obstruction(db_session):
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

    Уровень `warning`, а не `info`: это исход, по которому к нам придёт человек.
    Прежняя редакция ссылалась за обоснованием на ключ сохранённого тарифа, снятый
    планом 05.1-07 вместе с решением о плане, — довод от несуществующего соседа не
    проверяем ничем.

    ⚠️ УТВЕРЖДЕНИЕ О СОСТАВЕ ПОЛЕЙ ЗАМЕНЕНО НА БОЛЕЕ СИЛЬНОЕ, А НЕ ОСЛАБЛЕНО.
    Прежде тест требовал в записи ЧИСЛО незакрытых намерений. Считать его больше
    некому: прикладная проверка потолка снята целиком (D-06), отказ принимает
    ограничение схемы, и никакого подсчёта на этом пути не происходит. Теперь
    утверждается, что записи с числом НЕТ ВОВСЕ: журнал, по которому разбирают
    денежные жалобы, не имеет права называть величину, которой никто не
    вычислял, — а подставленная «для сохранения поля» единица была бы именно
    такой величиной.
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
    assert len(refusals) == 1, (
        f"запись об отказе сделана {len(refusals)} раз(а), а отказ был один"
    )
    fields = refusals[0].kwargs
    assert fields.get("user_id") == user.id
    counted = [name for name, value in fields.items() if isinstance(value, int)
               and name != "user_id"]
    assert not counted, (
        f"журнал называет величину, которой никто не вычислял: {counted}"
    )
