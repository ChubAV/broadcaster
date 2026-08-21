"""Сквозная линия BILL-05: форма доступа → ЮKassa → вебхук → сдвинутый срок.

Тест намеренно идёт ЧЕРЕЗ HTTP-форму, а не через вызов сервиса: предмет проверки —
что все семь слоёв (конфиг → страница → сервис → модель → вебхук → подписка →
шаблон) соединены, а не что каждый по отдельности работает. Единственная
подменённая часть — сеть ЮKassa.

⚠️ ФАЙЛ ПЕРЕПИСАН ПОД ПЛОСКУЮ МОДЕЛЬ, А НЕ ПОДКРУЧЕН. Он был написан на линию с
ТРЕМЯ тарифами: форма несла поле `plan`, цена искалась в прейскуранте по нему,
подписка заводилась с именем тарифа, а два теста охраняли отказ на непродаваемых
значениях этого поля. Ничего из перечисленного больше нет — прейскурант снят
планом `05.1-07`, колонка тарифа подписки ревизией `0020`, — и восемь его тестов
краснели с волны 5 не потому, что продукт сломан, а потому, что описывали
позапрошлую модель.

⚠️ ПРОБНЫЙ СРОК ЗАВОДИТСЯ ПРИ РЕГИСТРАЦИИ, И ЭТО МЕНЯЕТ ПОСЕВ КАЖДОГО ТЕСТА
ЗДЕСЬ. Фикстура `authed_client` регистрирует пользователя, а регистрация зовёт
`start_trial` — значит АКТИВНАЯ строка подписки у него есть УЖЕ ДО первого
платежа. Утверждения вида «строк подписки ноль» на этом посеве неверны по
построению, а второй активной строки не допускает частичный уникальный индекс
`uq_subscriptions_active_user`. Поэтому проверяется СДВИГ СРОКА существующей
строки, а не её появление.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.services.payment_service import handle_webhook

SAME_ORIGIN = {"Origin": "http://test"}
CONFIRMATION_URL = "https://yookassa.ru/checkout/payments/2c85a"

# Цена доступа — машинная строка формата ЮKassa. Выписана здесь ДОСЛОВНО, а не
# прочитана из `Settings`: тест, берущий значение из того же источника, что и
# код, утверждал бы «значение равно самому себе» и пережил бы подмену умолчания
# на «3 000,00 ₽», которую платёжное API отвергает в проде.
ACCESS_PRICE = "3000.00"


def _yoo_mocks(payment_id: str = "yoo_sub_1"):
    """Мок сети ЮKassa по образцу tests/test_services/test_payment_service.py."""
    mock_payment = MagicMock()
    mock_payment.id = payment_id
    mock_payment.confirmation = MagicMock()
    mock_payment.confirmation.confirmation_url = CONFIRMATION_URL

    mock_settings = MagicMock()
    mock_settings.yookassa_shop_id = "shop123"
    mock_settings.yookassa_secret_key = "secret"
    mock_settings.yookassa_return_url = "http://test/billing"
    mock_settings.app_name = "Broadcaster"
    return mock_payment, mock_settings


async def _current_user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


async def _subscribe(client: AsyncClient, data: dict | None = None, headers=None):
    """Нажатие кнопки покупки доступа.

    ⚠️ ПО УМОЛЧАНИЮ ФОРМА ПУСТА, И ЭТО ГЛАВНОЕ СВОЙСТВО ОБРАБОТЧИКА, А НЕ
    экономия на посеве: доступ стоит ОДНО число, оно живёт в настройке, и читает
    его сервер. Покупателю нечего подменить — поверхность подмены суммы схлопнута
    до нуля, а не отфильтрована.
    """
    mock_payment, mock_settings = _yoo_mocks()
    with patch(
        "app.services.payment_service.get_settings", return_value=mock_settings
    ), patch(
        "app.services.payment_service.YooPayment.create", return_value=mock_payment
    ):
        return await client.post(
            "/billing/subscribe",
            data={} if data is None else data,
            headers=SAME_ORIGIN if headers is None else headers,
            follow_redirects=False,
        )


async def _active_expiry(db: AsyncSession, user: User) -> datetime:
    """Срок активной строки владельца, приведённый к UTC.

    Запрос повторяет читателя приложения (`get_shell_context`) сортировкой и
    `limit`: смотреть на другую строку, чем видит пользователь, значило бы
    проверять не тот срок.
    """
    # ⚠️ ВЫБИРАЕТСЯ КОЛОНКА, А НЕ СУЩНОСТЬ, И ЭТО НЕ ЭКОНОМИЯ. Выборка сущности
    # вернула бы объект из карты идентичности этой сессии — то есть значение,
    # прочитанное ДО запроса к приложению, которое ходит в базу своей сессией.
    # Утверждение «срок не сдвинут» тогда было бы верно всегда и ни о чём.
    expires_at = (
        await db.execute(
            select(Subscription.expires_at)
            .where(Subscription.user_id == user.id, Subscription.is_active.is_(True))
            .order_by(Subscription.expires_at.desc())
            .limit(1)
        )
    ).scalar_one()
    return expires_at if expires_at.tzinfo else expires_at.replace(tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_subscribe_redirects_to_the_yookassa_confirmation_url(
    authed_client: AsyncClient, db_session: AsyncSession
):
    response = await _subscribe(authed_client)

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL

    payment = (await db_session.execute(select(Payment))).scalar_one()
    assert payment.kind == "subscription"
    assert payment.messages_count is None
    # ⚠️ ТАРИФА У ПЛАТЕЖА НЕТ ВОВСЕ, И `None` ЗДЕСЬ — ЗАПИСЬ ФАКТА, А НЕ
    # УМОЛЧАНИЕ. Колонка ЖУРНАЛЬНАЯ и остаётся: исторические строки помнят, что
    # и по какой цене было продано. Значение `None` в ней означает «предмет
    # покупки один, называть нечего»; записать сюда имя тарифа значило бы завести
    # второй источник правды о проданном.
    assert payment.plan is None
    # Цена приезжает ИЗ НАСТРОЙКИ, а не из прейскуранта по идентификатору плана,
    # и в машинном формате ЮKassa — подпись макета с неразрывным пробелом здесь
    # была бы отказом API.
    assert payment.amount_value == ACCESS_PRICE


@pytest.mark.asyncio
async def test_subscribe_reads_the_price_from_config_not_from_the_form(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Поля формы игнорируются ЦЕЛИКОМ: покупатель не назначает себе цену.

    ⚠️ ПОДСОВЫВАЕТСЯ И ЦЕНА, И СНЯТОЕ ПОЛЕ ТАРИФА. Форма сегодня не несёт ни
    одного поля, но HTTP не мешает прислать любое: обработчик обязан не читать
    их, а не отфильтровывать. Поле `plan` в посеве стоит намеренно — оно
    проверяет, что снятый вход не воскрес обходным путём и не влияет ни на сумму,
    ни на предмет покупки.
    """
    mock_payment, mock_settings = _yoo_mocks()
    with patch(
        "app.services.payment_service.get_settings", return_value=mock_settings
    ), patch(
        "app.services.payment_service.YooPayment.create", return_value=mock_payment
    ):
        response = await authed_client.post(
            "/billing/subscribe",
            data={"plan": "basic", "price": "1.00"},
            headers=SAME_ORIGIN,
            follow_redirects=False,
        )

    assert response.status_code == 302
    payment = (await db_session.execute(select(Payment))).scalar_one()
    assert payment.amount_value == ACCESS_PRICE
    assert payment.plan is None, "снятое поле тарифа доехало из формы до платежа"


@pytest.mark.asyncio
async def test_subscribe_rejects_a_cross_site_origin(
    authed_client: AsyncClient, db_session: AsyncSession
):
    response = await _subscribe(
        authed_client, headers={"Origin": "https://evil.example"}
    )

    assert response.status_code == 403
    count = await db_session.scalar(select(func.count()).select_from(Payment))
    assert count == 0, "отклонённый источник не должен создавать платёж"


@pytest.mark.asyncio
@pytest.mark.parametrize("smuggled", ["free", "platinum", ""])
async def test_a_smuggled_plan_field_changes_nothing_about_the_purchase(
    authed_client: AsyncClient, db_session: AsyncSession, smuggled: str
):
    """Присланное поле тарифа не меняет ни сумму, ни предмет, ни исход.

    ⚠️ ДВА ПРЕЖНИХ ТЕСТА ОТКАЗА СЛИТЫ СЮДА, И ЭТО СНЯТИЕ ПРЕДМЕТА, А НЕ
    ОСЛАБЛЕНИЕ. Они назывались `test_subscribe_rejects_the_free_plan` и
    `test_subscribe_rejects_an_unknown_plan` и держали отказ `?error=plan` —
    ветку, снятую планом `05.1-05` вместе с гардом смены тарифа: тарифов
    Free/Basic/Pro не существует (D-A, D-F), непродаваемого значения у поля,
    которого нет, тоже.

    Граница, которая ОСТАЛАСЬ и которую держит этот тест: снятый вход не имеет
    права воскреснуть обходным путём. Отказывать присланному полю не нужно —
    нужно его НЕ ЧИТАТЬ, и разница здесь не словесная: обработчик, начавший
    отказывать, снова стал бы читателем тарифа. Прежде непродаваемое значение и
    пустая строка проверяются оба, потому что «отказ вернулся» и «отказ вернулся
    только для одного значения» — разные события.
    """
    response = await _subscribe(authed_client, data={"plan": smuggled})

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL, (
        "обработчик ответил отказом на поле, которого он читать не должен"
    )

    payment = (await db_session.execute(select(Payment))).scalar_one()
    assert payment.kind == "subscription"
    assert payment.plan is None
    assert payment.amount_value == ACCESS_PRICE


@pytest.mark.asyncio
async def test_the_first_payment_moves_the_trial_period_it_finds(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Первый платёж двигает ПРОБНЫЙ срок, а не заводит вторую строку.

    ⚠️ ТЕСТ НАЗЫВАЛСЯ `test_webhook_creates_the_first_subscription` И ПРОВЕРЯЛ
    ПОЯВЛЕНИЕ СТРОКИ. Он был верен, пока строку заводил ТОЛЬКО платёж; сегодня её
    заводит регистрация (`start_trial`), и «появление» проверять не на чем —
    строка есть до платежа. Предмет переехал на исход, который остался: срок
    сдвинут вперёд, строка ОДНА, и вторую не допустит частичный уникальный
    индекс. Оплата, заведшая вторую активную строку, показала бы пользователю
    один срок, а планировщику отдала бы другой.
    """
    await _subscribe(authed_client)
    user = await _current_user(db_session)
    before = await _active_expiry(db_session, user)

    processed = await handle_webhook(
        db_session,
        event="payment.succeeded",
        payment_data={"object": {"id": "yoo_sub_1"}},
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
    assert len(rows) == 1, f"строк подписки {len(rows)}: оплата завела вторую"
    assert rows[0].is_active is True
    # Признак бесплатного доступа платёж не трогает: он про решение
    # администратора, а не про деньги (D-E).
    assert rows[0].has_free_access is False

    after = await _active_expiry(db_session, user)
    assert after > before, "оплата не сдвинула срок"
    assert after > datetime.now(timezone.utc) + timedelta(days=27)


@pytest.mark.asyncio
async def test_webhook_extends_an_active_subscription_without_burning_the_remainder(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _subscribe(authed_client)
    user = await _current_user(db_session)

    # ⚠️ СТРОКА НЕ ДОБАВЛЯЕТСЯ, А ПРАВИТСЯ. Прежде тест вставлял ВТОРУЮ активную
    # строку — на посеве без пробного срока это проходило; сегодня частичный
    # уникальный индекс `uq_subscriptions_active_user` отвергает такую вставку, и
    # тест падал бы на посеве, ничего не сказав о продлении.
    current = (datetime.now(timezone.utc) + timedelta(days=10)).replace(microsecond=0)
    existing = (
        await db_session.execute(
            select(Subscription).where(
                Subscription.user_id == user.id, Subscription.is_active.is_(True)
            )
        )
    ).scalar_one()
    existing.expires_at = current
    await db_session.commit()

    await handle_webhook(
        db_session,
        event="payment.succeeded",
        payment_data={"object": {"id": "yoo_sub_1"}},
    )

    rows = (
        (
            await db_session.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1, "продление не должно заводить вторую строку"

    expires_at = rows[0].expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    # Считается от прежнего срока, а не от сегодняшнего дня: остаток оплачен.
    assert expires_at > current + timedelta(days=27)


@pytest.mark.asyncio
async def test_a_repeated_webhook_does_not_move_the_date_twice(
    authed_client: AsyncClient, db_session: AsyncSession
):
    await _subscribe(authed_client)
    user = await _current_user(db_session)

    await handle_webhook(
        db_session,
        event="payment.succeeded",
        payment_data={"object": {"id": "yoo_sub_1"}},
    )
    first = (
        await db_session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
    ).scalar_one()
    first_expiry = first.expires_at

    processed = await handle_webhook(
        db_session,
        event="payment.succeeded",
        payment_data={"object": {"id": "yoo_sub_1"}},
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
    assert rows[0].expires_at == first_expiry


@pytest.mark.asyncio
async def test_returning_to_billing_does_not_move_the_date(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Возврат браузера с ЮKassa — не доказательство оплаты (D-05, T-05-05).

    ⚠️ УТВЕРЖДЕНИЕ ПЕРЕЕХАЛО С «СТРОКИ НЕТ» НА «СРОК НЕ СДВИНУТ». Строка есть у
    каждого зарегистрировавшегося (пробный период), поэтому счёт строк здесь
    больше ничего не доказывает: он был бы ненулевым и без всякого возврата.
    Предмет решения D-05 при этом не изменился ни на букву — срок двигает ТОЛЬКО
    подтверждённое уведомление, а редирект браузера происходит и при отказе от
    оплаты.
    """
    await _subscribe(authed_client)
    user = await _current_user(db_session)
    before = await _active_expiry(db_session, user)

    response = await authed_client.get("/billing")
    assert response.status_code == 200

    assert await _active_expiry(db_session, user) == before, (
        "GET /billing сдвинул срок доступа — возврат с ЮKassa принят за оплату"
    )
    count = await db_session.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.user_id == user.id)
    )
    assert count == 1, "GET /billing завёл вторую строку подписки"


@pytest.mark.asyncio
async def test_the_billing_page_renders_one_real_form_without_a_single_field(
    authed_client: AsyncClient
):
    """Базовый путь покупки работает без JavaScript и НЕ несёт полей.

    ⚠️ ТЕСТ НАЗЫВАЛСЯ `test_the_billing_page_renders_a_real_form_per_paid_plan` И
    ТРЕБОВАЛ ФОРМУ НА КАЖДЫЙ ПЛАТНЫЙ ТАРИФ. Витрины тарифов не существует (D-F),
    и требование «форма на тариф» описывает позапрошлый экран.

    Первая половина утверждения сохранена ДОСЛОВНО: форма НАСТОЯЩАЯ, действие —
    прежний маршрут, и покупка обязана работать при выключенном JavaScript.
    Вторая половина ИНВЕРТИРОВАНА: прежде проверялось, что среди значений поля
    нет непродаваемого; теперь — что поля нет вовсе. Это строже, и не на вкус:
    поверхность подмены суммы схлопнута до нуля, а не отфильтрована (T-05.1-22).
    """
    response = await authed_client.get("/billing")

    assert response.status_code == 200
    body = response.text
    assert 'action="/billing/subscribe"' in body

    form = body.split('action="/billing/subscribe"', 1)[1].split("</form>", 1)[0]
    assert "<input" not in form, f"в форме покупки появилось поле: {form}"
    for gone in ('value="free"', 'value="basic"', 'value="pro"'):
        assert gone not in body, f"витрина тарифов вернулась на экран: {gone}"
