"""Регрессия на КОНКУРЕНТНУЮ доставку уведомления ЮKassa (гэп 2).

Соседний `test_payment_service.py` проверяет ПОСЛЕДОВАТЕЛЬНУЮ повторную
доставку: первая завершилась, вторая пришла после и вышла на проверке
терминального статуса. Это другой случай, и защита от него держится сама собой.
Здесь проверяется НАЛОЖЕНИЕ: обе доставки прочитали строку платежа, пока она ещё
`pending`, обе прошли проверку терминального статуса — и дальше исход обязана
решать заявка на обработку, а не порядок, в котором доставки дошли до записи.

**Файловая база SQLite, а не база в памяти.** По той же причине, что выписана в
докстринге `tests/test_migrations/test_0017_payment_kind_and_plan.py`: содержимое
базы, живущей в оперативной памяти, между соединениями не сохраняется, а
конкурентная доставка по определению требует ДВУХ соединений.

**Наложение задаётся детерминированно, а не гонкой.** `asyncio.gather` дал бы
недетерминированный порядок и блокировки записи SQLite; тест, который иногда
зелёный, хуже отсутствующего. Порядок задаётся подменой `execute` у сессии
ПЕРВОЙ доставки: сразу после того, как первая доставка прочитала строку платежа
(первый же `execute` в `handle_webhook` — это `select(Payment)`), вторая доставка
прогоняется ЦЕЛИКОМ другой сессией и коммитит свой исход. Только после этого
первая доставка продолжает свой путь. Флаг однократности обязателен: без него
вложенные `execute` второй доставки ушли бы в рекурсию.

Подменяется метод СЕССИИ, а не введённый ради теста крючок в боевом коде: сеамов
для тестов в `app/` не добавляется.

**Почему подмена `execute` не упирается в блокировки SQLite.** Драйвер pysqlite
(и обёртка aiosqlite над ним) открывает транзакцию не на `SELECT`, а на первом
операторе записи. Поэтому первая доставка, прочитавшая строку, никаких блокировок
не держит, и вторая свободно пишет и коммитит.
"""

from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from yookassa.domain.notification import WebhookNotificationEventType

from app.application.billing.subscription_period import add_one_month
from app.config import Settings
from app.database import Base
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.services import payment_service
from app.services.payment_service import handle_webhook

EVENT_SUCCEEDED = WebhookNotificationEventType.PAYMENT_SUCCEEDED

YOO_ID = "yoo_overlap_1"


def _utc(value: datetime | None) -> datetime | None:
    """Доводит значение из БД до aware-UTC: SQLite отдаёт naive, PostgreSQL — aware."""
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _app_settings() -> Settings:
    """Настоящие `Settings` с УМОЛЧАНИЯМИ конфига, а не MagicMock.

    MagicMock здесь не годится принципиально: денежный путь читает из настроек
    цену доступа, и мок отдал бы вместо строки формата ЮKassa объект, на котором
    ветка отказа зеленела бы по неверной причине. Два обязательных поля задаются
    теми же значениями, что в `tests/conftest.py`: боевой `.env` в суите не
    читается.
    """
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret-key",
    )


@pytest_asyncio.fixture
async def sessions(tmp_path):
    """Фабрика НЕЗАВИСИМЫХ сессий поверх ОДНОЙ файловой базы."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'concurrency.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


async def _seed(factory, **payment_overrides) -> tuple[int, int]:
    """Пользователь и платёж в состоянии «уведомление ещё не приходило»."""
    fields = {
        "yookassa_payment_id": YOO_ID,
        "status": "pending",
        "amount_value": "149.00",
        "amount_currency": "RUB",
        "kind": "package",
        "messages_count": 100,
        "package_name": "100 messages",
    }
    fields.update(payment_overrides)
    async with factory() as session:
        user = User(email="overlap@t.com", password_hash="h", name="T")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        payment = Payment(user_id=user.id, **fields)
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return user.id, payment.id


def _payload(yookassa_id: str = YOO_ID) -> dict:
    return {"object": {"id": yookassa_id}}


def _interleave_after_first_read(session, second_delivery):
    """Прогоняет `second_delivery` ровно один раз — после первого `execute`.

    Первый `execute` в `handle_webhook` — выборка строки платежа. К моменту
    возврата обёртки первая доставка уже держит объект платежа в статусе
    `pending`, то есть проверку терминального статуса она пройдёт независимо от
    того, что успела записать вторая. Ровно эта картина описана в отчёте
    верификации как гэп 2.
    """
    original = session.execute
    fired = {"done": False}

    async def wrapper(*args, **kwargs):
        result = await original(*args, **kwargs)
        if not fired["done"]:
            fired["done"] = True
            await second_delivery()
        return result

    session.execute = wrapper


async def _overlapping_deliveries(factory, payload=None, logger_mock=None):
    """Две наложившиеся доставки одного уведомления. Возвращает исход ПЕРВОЙ.

    Первая — та, чья сессия подменена: она читает строку раньше, а пишет позже.
    Именно она и обязана оказаться проигравшей заявку.
    """
    payload = payload or _payload()

    async def second_delivery():
        async with factory() as second:
            await handle_webhook(second, EVENT_SUCCEEDED, payload)

    async with factory() as first:
        _interleave_after_first_read(first, second_delivery)
        with ExitStack() as stack:
            # ПОДМЕНЫ СБРОСА КЭША ЗДЕСЬ БОЛЬШЕ НЕТ. Она держала сброс вердикта
            # об ОСТАТКЕ СООБЩЕНИЙ, снятом вместе со всей валютой. Оставшийся
            # сброс вердикта доступа Redis не требует: и он, и чтение обёрнуты,
            # а отсутствие Redis вердикта не отменяет.
            if logger_mock is not None:
                stack.enter_context(
                    patch("app.services.payment_service.logger", logger_mock)
                )
            return await handle_webhook(first, EVENT_SUCCEEDED, payload)


@pytest.mark.asyncio
async def test_overlapping_deliveries_of_a_package_credit_nothing(sessions):
    """Наложившиеся доставки пакета не начисляют НИ РАЗУ, а не ровно один раз.

    ⚠️ ПРЕДМЕТ УТВЕРЖДЕНИЯ ИНВЕРТИРОВАН ВМЕСТЕ С ПРЕДМЕТОМ КОДА, А НЕ СНЯТ.
    Прежде здесь проверялось, что заявка не даёт удвоить начисление; валюта
    сообщений снята целиком, и начислять нечего вовсе — граница «две доставки
    одного платежа не выдают лишнего» осталась той же и стала строже.

    ДВА ПРЕЖНИХ УТВЕРЖДЕНИЯ СЛИТЫ В ОДНО НАМЕРЕННО: соседнее считало строки
    журнала операций, и после снятия валюты оба свелись к одному вопросу —
    «выдано ли хоть что-нибудь». Держать два имени под одним вопросом значило бы
    получить пару, которая расходится при первой же правке.

    ⚠️ ВЕЛИЧИНА, ПО КОТОРОЙ СЧИТАЛОСЬ «ВЫДАННОЕ», СМЕНИЛАСЬ ВМЕСТЕ С РЕВИЗИЕЙ
    `0020`. Остаток сообщений и его журнал сняты вместе с таблицами: начислить их
    невозможно ПО СХЕМЕ, и прогон, это утверждающий, утверждал бы о SQLAlchemy, а
    не о продукте. Единственное, что пакетная доставка может выдать сегодня и не
    имеет права, — ДОСТУП, и считается теперь он.
    """
    user_id, _ = await _seed(sessions)

    await _overlapping_deliveries(sessions)

    async with sessions() as check:
        granted = await check.scalar(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.user_id == user_id)
        )

    assert granted == 0, f"наложившиеся доставки пакета выдали {granted} строк доступа"


@pytest.mark.asyncio
async def test_overlapping_deliveries_extend_subscription_by_one_month(sessions):
    """Ровно одна строка подписки и сдвиг ровно на один месяц, а не на два."""
    started = datetime.now(timezone.utc)
    user_id, _ = await _seed(
        sessions, kind="subscription", plan="basic", messages_count=None, package_name=None
    )

    await _overlapping_deliveries(sessions)

    async with sessions() as check:
        rows = list(
            (
                await check.execute(
                    select(Subscription).where(Subscription.user_id == user_id)
                )
            ).scalars()
        )

    assert len(rows) == 1, f"строк подписки {len(rows)}, а не одна"
    expires = rows[0].expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    # Один календарный месяц — это 28…31 день. Два месяца (нынешнее поведение)
    # выходят за верхнюю границу, поэтому окно ловит удвоение, не завися от того,
    # в каком месяце запущен тест.
    assert started + timedelta(days=27) < expires < started + timedelta(days=32), (
        f"срок сдвинут не на один месяц: {expires} при старте {started}"
    )


@pytest.mark.asyncio
async def test_the_losing_delivery_answers_accepted(sessions):
    """Проигравшая доставка возвращает True, а не поднимает исключение.

    Отказ здесь дал бы 5xx, а 5xx — повод для ЮKassa доставить уведомление ещё
    раз по УЖЕ проведённому платежу.
    """
    await _seed(sessions)

    processed = await _overlapping_deliveries(sessions)

    assert processed is True


@pytest.mark.asyncio
async def test_the_losing_delivery_is_visible_in_the_log(sessions):
    """Проигрыш заявки виден отдельным ключом — наложение перестало быть немым."""
    await _seed(sessions)
    logger_mock = MagicMock()

    await _overlapping_deliveries(sessions, logger_mock=logger_mock)

    keys = [call.args[0] for call in logger_mock.info.call_args_list if call.args]
    assert "webhook_claim_lost" in keys, f"ключа проигрыша заявки нет в журнале: {keys}"


@pytest.mark.asyncio
async def test_a_package_payment_without_a_count_credits_nothing(db_session):
    """Пустой `messages_count` не начисляет и не роняет обработчик TypeError.

    Такой платёж — последствие опечатки в `kind` у вызывающего: подписочная
    покупка уходит в пакетную ветку, где считать нечего. Сегодня начисление
    падает TypeError, маршрут отвечает 500, а ЮKassa повторяет доставку до
    отказа при взятых деньгах.
    """
    user = User(email="nocount@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    payment = Payment(
        user_id=user.id,
        yookassa_payment_id="yoo_no_count",
        status="pending",
        amount_value="149.00",
        amount_currency="RUB",
        kind="package",
        messages_count=None,
        package_name=None,
    )
    db_session.add(payment)
    await db_session.commit()

    processed = await handle_webhook(
        db_session, EVENT_SUCCEEDED, _payload("yoo_no_count")
    )

    assert processed is False
    # Начислять после снятия валюты сообщений нечего и некуда — проверяется
    # ОСТАВШАЯСЯ выдача: пустой пакет не имеет права открыть доступ.
    granted = await db_session.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.user_id == user.id)
    )
    assert granted == 0, f"пустой пакет выдал {granted} строк доступа"


# --- Остаточная щель: ДВА РАЗНЫХ платежа одного пользователя ------------------
#
# Заявка `_claim_payment` эту пару не разводит и не обязана: строки платежей
# РАЗНЫЕ, поэтому каждая доставка честно выигрывает СВОЮ заявку. Разводит их
# ограничение схемы — частичный уникальный индекс `uq_subscriptions_active_user`
# ревизии 0018 (решение владельца: `constraint-plus-backfill-guard`).


async def _seed_two_subscription_payments(factory) -> int:
    """Пользователь БЕЗ подписки и два его платежа за тариф."""
    async with factory() as session:
        user = User(email="two@t.com", password_hash="h", name="T")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        for yoo_id in ("yoo_sub_a", "yoo_sub_b"):
            session.add(
                Payment(
                    user_id=user.id,
                    yookassa_payment_id=yoo_id,
                    status="pending",
                    amount_value="1490.00",
                    amount_currency="RUB",
                    kind="subscription",
                    plan="basic",
                    messages_count=None,
                    package_name=None,
                )
            )
        await session.commit()
        return user.id


@pytest.mark.asyncio
async def test_two_different_payments_leave_one_active_subscription(sessions):
    """Два РАЗНЫХ платежа внахлёст: одна активная строка, два оплаченных месяца.

    Каждая доставка выигрывает свою заявку — платежи разные, и отказывать в
    одном из них было бы кражей оплаченного месяца. Проверяется, что при этом
    строка подписки остаётся ОДНА (её больше не может быть две — ограничение
    схемы), а срок двигается ДВАЖДЫ: пользователь заплатил дважды.
    """
    started = datetime.now(timezone.utc)
    user_id = await _seed_two_subscription_payments(sessions)

    async def second_delivery():
        async with sessions() as second:
            await handle_webhook(second, EVENT_SUCCEEDED, _payload("yoo_sub_b"))

    async with sessions() as first:
        _interleave_after_first_read(first, second_delivery)
        processed = await handle_webhook(
            first, EVENT_SUCCEEDED, _payload("yoo_sub_a")
        )

    assert processed is True, "обработчик отказал по настоящему платежу"

    async with sessions() as check:
        rows = list(
            (
                await check.execute(
                    select(Subscription).where(
                        Subscription.user_id == user_id,
                        Subscription.is_active.is_(True),
                    )
                )
            ).scalars()
        )

    assert len(rows) == 1, f"активных строк подписки {len(rows)}, а не одна"
    expires = rows[0].expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    # Два платежа — два месяца. Один месяц означал бы, что второй платёж взят и
    # не отработан.
    assert started + timedelta(days=57) < expires < started + timedelta(days=63), (
        f"два платежа сдвинули срок не на два месяца: {expires}"
    )


@pytest.mark.asyncio
async def test_a_rejected_subscription_insert_is_recovered_not_raised(db_session):
    """Отказ ограничения на вставке обрабатывается, а не роняет обработчик 500-й.

    ⚠️ ЭТУ ВЕТКУ НЕЛЬЗЯ ПОЛУЧИТЬ НАСТОЯЩЕЙ КОНКУРЕНЦИЕЙ НА SQLite, и это
    свойство ДВИЖКА, а не теста: чтобы столкнуться на вставке, обе доставки
    обязаны держать открытые транзакции записи одновременно, а SQLite второй
    такой транзакции просто не даёт («database is locked»). PostgreSQL даёт.
    Поэтому момент «мы прочитали до конкурента, а вставляем после него» задаётся
    подменой `_active_subscription`: её ПЕРВЫЙ вызов отвечает «подписки нет», как
    и было в момент чтения. Всё остальное — настоящее: настоящий уникальный
    индекс отвергает настоящую вставку, и дальше работает настоящий разбор
    отказа.
    """
    user = User(email="rejected@t.com", password_hash="h", name="T")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    current = (datetime.now(timezone.utc) + timedelta(days=10)).replace(microsecond=0)
    existing = Subscription(
        user_id=user.id, expires_at=current, is_active=True
    )
    db_session.add(existing)
    db_session.add(
        Payment(
            user_id=user.id,
            yookassa_payment_id="yoo_rejected",
            status="pending",
            amount_value="1490.00",
            amount_currency="RUB",
            kind="subscription",
            plan="pro",
            messages_count=None,
            package_name=None,
        )
    )
    await db_session.commit()

    real_lookup = payment_service._active_subscription
    calls = {"n": 0}

    async def lookup_that_missed_the_competitor(db, user_id):
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return await real_lookup(db, user_id)

    with patch(
        "app.services.payment_service._active_subscription",
        lookup_that_missed_the_competitor,
    ), patch(
        "app.services.payment_service.get_settings", return_value=_app_settings()
    ):
        processed = await handle_webhook(
            db_session, EVENT_SUCCEEDED, _payload("yoo_rejected")
        )

    assert processed is True
    assert calls["n"] == 2, "разбор отказа не перечитал чужую строку"

    rows = list(
        (
            await db_session.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
        ).scalars()
    )
    assert len(rows) == 1, f"строк подписки {len(rows)}: отвергнутая вставка уцелела"
    # Платёж отработан НА ЧУЖОЙ строке: срок сдвинут от ЕЁ даты.
    #
    # ⚠️ УТВЕРЖДЕНИЕ ВЕРНУЛОСЬ К РАВЕНСТВУ ВМЕСТЕ СО СНЯТИЕМ МАТРИЦЫ ТАРИФОВ
    # (план 05.1-07), А НЕ ОСЛАБЛЕНО. Форма `convert-remainder` требовала окна,
    # потому что остаток младшего тарифа переносился на старший ПО ОТНОШЕНИЮ
    # ЦЕН, а точка отсчёта считалась от `now` денежного пути. Цена в системе
    # одна (D-A), переносить нечего и не во что: продление кладёт месяц поверх
    # собственного остатка чужой строки — то есть ровно `add_one_month(current)`.
    # Равенство здесь строже окна и держит обе прежние стороны разом.
    assert _utc(rows[0].expires_at) == add_one_month(current), (
        "срок сдвинут не на календарный месяц от даты чужой строки"
    )
    # Строку подписки платёж не переписывает: решение о плане снято из
    # `_apply_extension` вместе с рангом тарифов, а сама колонка — ревизией
    # `0020`. Утверждение переехало с колонки тарифа на ТОЖДЕСТВО СТРОКИ: сдвинута
    # именно ЧУЖАЯ строка, а не заведённая заново под тем же пользователем.
    assert rows[0].id == existing.id, "продлена не чужая строка, а новая"
    assert rows[0].is_active is True
