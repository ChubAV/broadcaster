"""Закрытое множество состояний отказа обеих форм оплаты (U1, U2, U3, IN-06).

Предмет файла — ОТВЕТ РАЗДЕЛА НА НЕУДАВШУЮСЯ ОПЛАТУ. До плана 05-10 его не было
вовсе: `create_payment` звался без обёртки, поэтому отказ API ЮKassa выходил
необработанной пятисоткой, а все пять веток гардов возвращали голый редирект на
`/billing` — то есть человек, нажавший «Оплатить», получал ту же самую страницу
без единого слова и следующим действием нажимал ещё раз.

ЧТО ЗДЕСЬ ПРОВЕРЯЕТСЯ И ЧЕГО НЕТ.

- Здесь: что КАЖДАЯ ветка отказа несёт свою причину, что причина приезжает из
  ЗАКРЫТОГО множества, а не из адресной строки, и что отказ создания платежа не
  оставляет строки в `payments`.
- Не здесь: сборка раздела (`test_billing_section.py`), сквозная линия подписки
  (`test_billing_subscription.py`), сам сервис платежей
  (`test_services/test_payment_service.py`).

ПОЧЕМУ МНОЖЕСТВО ПРИЧИН ЗАКРЫТО (T-05-46). В разметку уходит строка ИЗ
ОТОБРАЖЕНИЯ `_payment_error_message`, а не значение параметра запроса. Владелец
ссылки может подставить в адрес что угодно — на экран это не попадёт ни
значением, ни атрибутом, потому что подставлять нечего: вход в разметку не
связан со входом из адреса. Тем же приёмом закрыт признак исхода повтора
отправки (`RETRY_NOTICES` в `app/pages/history.py`).

ПОЧЕМУ ТЕКСТ ЧУЖОГО ИСКЛЮЧЕНИЯ НЕ ПОКАЗЫВАЕТСЯ (T-05-47). Прецедент R-03-09
Фазы 3 — раскрытие текста стороннего исключения в плашке — принят владельцем
риском severity medium. Повторять его на ДЕНЕЖНОМ пути не следует: текст SDK
уходит в журнал, на экран — фиксированная строка.
"""
import ast
import inspect
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.constants import PLAN_ORDER
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.services.payment_service import create_payment, handle_webhook

BILLING_PY = Path(__file__).resolve().parents[2] / "app" / "pages" / "billing.py"

SAME_ORIGIN = {"Origin": "http://test"}
CROSS_SITE = {"Origin": "https://evil.example"}
CONFIRMATION_URL = "https://yookassa.ru/checkout/payments/2c85a"

FIRST_PACKAGE_INDEX = "0"

# Текст «стороннего исключения». Строка нарочно узнаваемая: она не встречается
# ни в одном шаблоне проекта, поэтому её появление в разметке однозначно значит
# «текст чужого исключения вышел на экран», а не совпадение со словом верстки.
SDK_FAILURE_TEXT = "yookassa_sdk_internal_boom_do_not_render_me"

# Строки закрытого множества. Выписаны здесь ДОСЛОВНО, потому что предмет
# проверки — что человек читает названную причину, а не что обработчик положил в
# контекст непустое значение.
MSG_PAYMENT = "Не удалось начать оплату — попробуйте ещё раз через минуту"
MSG_DISABLED = "Оплата сейчас недоступна — обратитесь к администратору"
MSG_PLAN = "Этот тариф больше не предлагается — обновите страницу и выберите другой"
MSG_PACKAGE = "Этот пакет больше не предлагается — обновите страницу и выберите другой"
MSG_DOWNGRADE = (
    "Перейти на младший тариф можно после окончания оплаченного срока — "
    "оплаченные дни не сгорают"
)

# Подпись четвёртого состояния CTA карточки плана. Она обязана НАЗЫВАТЬ ПРИЧИНУ,
# по которой кнопки нет: карточка без кнопки и без слов читается как поломка
# витрины, а не как правило продукта.
CAPTION_DOWNGRADE = (
    "Переход на младший тариф — после окончания оплаченного срока: "
    "оплаченные дни не сгорают"
)

# Признак нарисованной плашки отказа. Проверяется ИМЕННО он, а не наличие слова
# из текста: слово может прийти из соседнего блока экрана, обёртка — только из
# ветки показа причины.
ALERT_MARKER = "data-payment-error"


# --- Инструменты --------------------------------------------------------------


def _yoo_settings():
    """Мок настроек ЮKassa по образцу tests/test_services/test_payment_service.py."""
    mock_settings = MagicMock()
    mock_settings.yookassa_shop_id = "shop123"
    mock_settings.yookassa_secret_key = "secret"
    mock_settings.yookassa_return_url = "http://test/billing"
    mock_settings.app_name = "Broadcaster"
    return mock_settings


def _yoo_payment(payment_id: str = "yoo_1"):
    mock_payment = MagicMock()
    mock_payment.id = payment_id
    mock_payment.confirmation = MagicMock()
    mock_payment.confirmation.confirmation_url = CONFIRMATION_URL
    return mock_payment


def _failing_sdk():
    """Подмена вызова SDK, ПОДНИМАЮЩАЯ исключение вместо возврата платежа.

    Тот же способ подмены, что у успешного пути, — меняется только исход:
    настоящая сеть ЮKassa в суите не участвует ни в одном тесте.
    """
    return patch(
        "app.services.payment_service.YooPayment.create",
        side_effect=RuntimeError(SDK_FAILURE_TEXT),
    )


def _healthy_sdk(payment_id: str = "yoo_1"):
    return patch(
        "app.services.payment_service.YooPayment.create",
        return_value=_yoo_payment(payment_id),
    )


async def _post(
    client: AsyncClient,
    url: str,
    data: dict,
    *,
    failing: bool = False,
    headers=None,
    payment_id: str = "yoo_1",
):
    """POST формы оплаты с подменённым SDK.

    ИДЕНТИФИКАТОР ПЛАТЕЖА ПАРАМЕТРИЗОВАН, А НЕ ЗАШИТ. Пока тест заводил ровно
    один платёж, разницы не было; сценариям стадии ПРИМЕНЕНИЯ нужны ДВА платежа
    одного пользователя, и с одинаковым `yookassa_payment_id` второй заводился
    бы дубликатом — выборка платежа в `handle_webhook` поднимала бы
    `MultipleResultsFound` вместо воспроизведения дефекта. Значение по умолчанию
    оставлено прежним, поэтому ни один существующий тест не меняется.
    """
    sdk = _failing_sdk() if failing else _healthy_sdk(payment_id)
    with patch(
        "app.services.payment_service.get_settings", return_value=_yoo_settings()
    ), sdk:
        return await client.post(
            url,
            data=data,
            headers=SAME_ORIGIN if headers is None else headers,
            follow_redirects=False,
        )


async def _subscribe(
    client: AsyncClient,
    plan: str = "basic",
    *,
    failing: bool = False,
    headers=None,
    payment_id: str = "yoo_1",
):
    return await _post(
        client,
        "/billing/subscribe",
        {"plan": plan},
        failing=failing,
        headers=headers,
        payment_id=payment_id,
    )


async def _purchase(
    client: AsyncClient,
    index: str = FIRST_PACKAGE_INDEX,
    *,
    failing: bool = False,
    headers=None,
):
    return await _post(
        client,
        "/billing/purchase",
        {"package_index": index},
        failing=failing,
        headers=headers,
    )


async def _payments_count(db: AsyncSession) -> int:
    return await db.scalar(select(func.count()).select_from(Payment))


async def _current_user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "testuser@test.com"))
    ).scalar_one()


# =============================================================================
# U1 / U2 — отказ API ЮKassa на форме тарифа
# =============================================================================


@pytest.mark.asyncio
async def test_a_failed_subscription_payment_returns_the_person_with_a_reason(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Отказ SDK — состояние раздела, а не необработанная пятисотка.

    До плана 05-10 исключение выходило наружу: `create_payment` звался без
    обёртки, и человек получал страницу ошибки сервера вместо ответа раздела.
    """
    response = await _subscribe(authed_client, failing=True)

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=payment"


@pytest.mark.asyncio
async def test_a_failed_package_payment_returns_the_person_with_a_reason(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Один порядок проверок на обоих входах означает один ответ на отказ."""
    response = await _purchase(authed_client, failing=True)

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=payment"


@pytest.mark.asyncio
@pytest.mark.parametrize("form", ["subscribe", "purchase"])
async def test_a_failed_payment_leaves_no_row_in_the_journal(
    authed_client: AsyncClient, db_session: AsyncSession, form: str
):
    """Платёж не заводится в журнале, если ЮKassa его не создала (T-05-49).

    Порядок «сначала SDK, потом запись в БД» — не деталь реализации, а условие
    этого свойства: строка `payments`, оставшаяся после отказа, означала бы
    платёж, которого у ЮKassa нет вовсе.
    """
    if form == "subscribe":
        await _subscribe(authed_client, failing=True)
    else:
        await _purchase(authed_client, failing=True)

    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("form", ["subscribe", "purchase"])
async def test_the_third_party_exception_text_never_reaches_the_screen(
    authed_client: AsyncClient, form: str
):
    """T-05-47: текст исключения SDK уходит в журнал и НИКОГДА на экран.

    Проверяется вся линия: и заголовок перенаправления, и страница, на которую
    оно привело.
    """
    if form == "subscribe":
        response = await _subscribe(authed_client, failing=True)
    else:
        response = await _purchase(authed_client, failing=True)

    assert SDK_FAILURE_TEXT not in response.text
    landing = await authed_client.get(response.headers["location"])
    assert response.headers["location"] == "/billing?error=payment"
    assert SDK_FAILURE_TEXT not in landing.text


def test_the_failure_is_recorded_in_the_journal_by_its_own_key():
    """T-05-48: у отказа есть след — ключ `payment_create_failed`.

    Отказ без следа — это repudiation: жалоба «я нажал, ничего не произошло»
    не проверяема ничем.
    """
    source = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "services"
        / "payment_service.py"
    ).read_text(encoding="utf-8")

    assert "payment_create_failed" in source
    assert "PaymentCreationError" in source


# =============================================================================
# U3 — каждая ветка гарда несёт СВОЮ причину
# =============================================================================


@pytest.mark.asyncio
async def test_subscribing_with_payments_disabled_names_the_reason(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    """Устаревшая страница ДОСТИЖИМА: администратор выключил платежи после
    отрисовки, и голый редирект читался бы как «кнопка сломана»."""
    test_settings.yookassa_enabled = False
    try:
        response = await _subscribe(authed_client)
    finally:
        test_settings.yookassa_enabled = True

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=disabled"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
async def test_purchasing_with_payments_disabled_names_the_reason(
    authed_client: AsyncClient, db_session: AsyncSession, test_settings
):
    test_settings.yookassa_enabled = False
    try:
        response = await _purchase(authed_client)
    finally:
        test_settings.yookassa_enabled = True

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=disabled"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("plan", ["platinum", "free", ""])
async def test_subscribing_to_a_plan_the_config_does_not_sell_names_the_reason(
    authed_client: AsyncClient, db_session: AsyncSession, plan: str
):
    """План, ушедший из конфига, и бесплатный тариф — одна причина: продать
    нечего. Обе ветки различимы на экране, а не сливаются в возврат на
    неизменившуюся страницу."""
    response = await _subscribe(authed_client, plan=plan)

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=plan"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("index", ["99", "-1", "не число", ""])
async def test_purchasing_an_index_the_config_does_not_have_names_the_reason(
    authed_client: AsyncClient, db_session: AsyncSession, index: str
):
    """Нечисловой и внедиапазонный индексы ведут в ОДНУ ветку с одной причиной:
    для человека это один и тот же случай — «этого пакета нет»."""
    response = await _purchase(authed_client, index=index)

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=package"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["/billing/subscribe", "/billing/purchase"])
async def test_a_cross_site_post_is_refused_without_a_reason(
    authed_client: AsyncClient, db_session: AsyncSession, url: str
):
    """Чужому источнику причина отказа НЕ сообщается.

    Порядок проверок не меняется: сначала кто пришёл, потом откуда, потом что
    просит. 403 без тела и без перенаправления — межсайтовый запрос не имеет
    права узнать даже, включены ли платежи.
    """
    response = await _post(
        authed_client,
        url,
        {"plan": "basic", "package_index": FIRST_PACKAGE_INDEX},
        headers=CROSS_SITE,
    )

    assert response.status_code == 403
    assert "location" not in response.headers
    assert await _payments_count(db_session) == 0


def test_no_bare_redirect_without_a_reason_is_left_in_the_section():
    """Структурно: голых редиректов на `/billing` в обработчиках не осталось.

    Поведенческие тесты выше проверяют известные ветки; этот держит инвариант
    для веток, которых ещё нет.
    """
    source = BILLING_PY.read_text(encoding="utf-8")

    assert 'url="/billing"' not in source, (
        "в разделе снова появился возврат на неизменившуюся страницу без причины"
    )


# =============================================================================
# T-05-46 — множество причин ЗАКРЫТО
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "code,message",
    [
        ("payment", MSG_PAYMENT),
        ("disabled", MSG_DISABLED),
        ("plan", MSG_PLAN),
        ("package", MSG_PACKAGE),
        ("downgrade", MSG_DOWNGRADE),
    ],
)
async def test_a_known_reason_code_prints_its_own_words(
    authed_client: AsyncClient, code: str, message: str
):
    response = await authed_client.get(f"/billing?error={code}")

    assert response.status_code == 200
    assert ALERT_MARKER in response.text, "плашки отказа на экране нет"
    assert message in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "code",
    ["zzz_unknown_reason", "<script>alert(1)</script>", "paymentt", "PAYMENT"],
)
async def test_an_unknown_reason_code_prints_nothing_at_all(
    authed_client: AsyncClient, code: str
):
    """Подставить произвольный текст через адрес невозможно (T-05-46).

    Проверяется НЕ экранирование, а недостижимость: в разметку уходит строка из
    закрытого отображения, поэтому значение параметра не попадает на экран ни
    значением, ни атрибутом.
    """
    response = await authed_client.get(f"/billing?error={code}")

    assert response.status_code == 200
    assert ALERT_MARKER not in response.text, "неизвестный код нарисовал плашку"
    assert code not in response.text, "значение параметра напечатано на экране"


@pytest.mark.asyncio
async def test_the_section_without_the_parameter_prints_no_alert(
    authed_client: AsyncClient,
):
    """Парный тест: без него предыдущие зеленели бы на разметке без плашки."""
    response = await authed_client.get("/billing")

    assert response.status_code == 200
    assert ALERT_MARKER not in response.text


@pytest.mark.asyncio
async def test_the_alert_stands_before_the_current_plan_block(
    authed_client: AsyncClient,
):
    """Причина читается РАНЬШЕ неизменившихся чисел.

    Плашка под блоком тарифа была бы прочитана после того, как человек уже
    сделал вывод «ничего не изменилось, кнопка сломана».
    """
    html = (await authed_client.get("/billing?error=payment")).text

    assert html.index(ALERT_MARKER) < html.index("Текущий тариф")


def test_the_reason_codes_of_the_handlers_are_exactly_the_known_set():
    """Ни одного кода в редиректе мимо отображения — и ни одного лишнего ключа.

    Коды выписаны в редиректах ЛИТЕРАЛАМИ намеренно: адрес обязан читаться
    целиком в той строке, где он строится. Расхождение литерала с отображением
    даёт молчаливый редирект без слов — ровно тот дефект, который закрывает этот
    план, — поэтому связь держится этой регрессией, а не аккуратностью автора.
    """
    from app.pages import billing as billing_module

    source = BILLING_PY.read_text(encoding="utf-8")
    used = set(re.findall(r"/billing\?error=([a-z]+)", source))

    assert used == {"payment", "disabled", "plan", "package", "downgrade"}, used
    for code in used:
        assert billing_module._payment_error_message(code), code
    assert billing_module._payment_error_message("zzz") == ""
    assert billing_module._payment_error_message(None) == ""


def test_the_get_handler_still_contains_no_write_path():
    """Параметр запроса ничего не меняет — только показывает (D-05)."""
    source = BILLING_PY.read_text(encoding="utf-8")
    rest = source[source.index("async def billing_page(") :]
    body = rest[: rest.find("\n@router")]

    assert not re.search(r"\b(db|session)\.(add|commit|flush)\(", body)


# =============================================================================
# IN-06 — управляющий элемент, упирающийся в молчаливый отказ
# =============================================================================


@pytest.mark.asyncio
async def test_an_expired_free_plan_is_offered_no_renewal_button(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Кнопка «Продлить» у бесплатного тарифа обещала оплату, которой нет.

    `free` есть в перечне конфига, поэтому проверка `current_in_config`
    пропускала его, а обработчик такой платёж отвергал: управляющий элемент,
    упирающийся в отказ, читается как сломанный платёжный путь.
    """
    owner = await _current_user(db_session)
    db_session.add(
        Subscription(
            user_id=owner.id,
            plan="free",
            expires_at=datetime.now(timezone.utc) - timedelta(days=3),
            is_active=True,
        )
    )
    await db_session.commit()

    html = (await authed_client.get("/billing")).text

    assert 'value="free"' not in html, "бесплатный тариф получил кнопку оплаты"


@pytest.mark.asyncio
async def test_an_expired_paid_plan_still_keeps_its_renewal_button(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный тест: правка IN-06 не должна снести предложение продлить платный
    тариф — именно ради него блок и существует (D-07)."""
    owner = await _current_user(db_session)
    db_session.add(
        Subscription(
            user_id=owner.id,
            plan="basic",
            expires_at=datetime.now(timezone.utc) - timedelta(days=3),
            is_active=True,
        )
    )
    await db_session.commit()

    html = (await authed_client.get("/billing")).text

    assert "истёк" in html
    assert 'value="basic"' in html


# =============================================================================
# C2 / WR-02 — семантика смены тарифа, вариант `upgrade-only`
# =============================================================================
#
# РЕШЕНИЕ ВЛАДЕЛЬЦА (чекпойнт плана 05-10): повышение разрешено и НЕ сжигает
# оплаченный остаток; понижение не предлагается и не принимается.
#
# ЧТО ЭТО ЗАКРЫВАЕТ. До решения `_extend_subscription` перезаписывал план
# безусловно, а срок двигал от существующего: подписчик Pro с 25 неистёкшими
# днями, купивший Basic, немедленно понижался и сохранял эти дни — то есть
# 4 900 ₽, уплаченные за них, превращались в дни младшего тарифа. Путь был
# ДОСТИЖИМ: карточка чужого платного плана рисовала «Перейти на {план}», а
# обработчик такой платёж принимал.
#
# ЧЕМ ЭТО ОПЛАЧЕНО (принятая цена варианта, а не недосмотр). Повышение отдаёт
# лимиты старшего тарифа на оставшиеся дни младшего бесплатно (T-05-51).
# Применения лимитов в системе нет вовсе (D-08), поэтому сегодня «лимиты Pro»
# не дают доступа ни к чему сверх показа.
#
# ЗАЩИТА НА ОБОИХ КОНЦАХ. Карточка младшего плана не рисует CTA, а обработчик
# отвергает такой платёж названной причиной — устаревшая страница безопасна.
# Прохибиция 05-01 («не сжигать неистраченный остаток») СОБЛЮДЕНА: ни один
# разрешённый переход остатка не сжигает, переопределять её не пришлось.

# Конфиг с планом, которого НЕТ в PLAN_ORDER. Отдельная константа, потому что
# её читают два теста отказа по умолчанию.
UNRANKED_PLAN_LIMITS = json.dumps(
    [
        {
            "id": "free",
            "name": "Free",
            "price": "0.00",
            "ads": 3,
            "groups": 5,
            "sends": 300,
            "accounts": 1,
        },
        {
            "id": "basic",
            "name": "Basic",
            "price": "1490.00",
            "ads": 15,
            "groups": 30,
            "sends": 5000,
            "accounts": 5,
        },
        {
            "id": "platinum",
            "name": "Platinum",
            "price": "9900.00",
            "ads": None,
            "groups": None,
            "sends": 50000,
            "accounts": 20,
        },
    ]
)


async def _seed_live_subscription(
    db: AsyncSession, plan: str, *, days: int = 25
) -> datetime:
    """Действующая (неистёкшая) подписка владельца. Возвращает её срок."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=days)
    db.add(
        Subscription(
            user_id=(await _current_user(db)).id,
            plan=plan,
            expires_at=expires_at,
            is_active=True,
        )
    )
    await db.commit()
    return expires_at


async def _subscription_rows(db: AsyncSession) -> list[Subscription]:
    owner = await _current_user(db)
    return list(
        (
            await db.execute(
                select(Subscription).where(Subscription.user_id == owner.id)
            )
        )
        .scalars()
        .all()
    )


def _aware(value: datetime) -> datetime:
    """SQLite отдаёт колонку с таймзоной NAIVE, PostgreSQL — aware."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def test_the_order_of_plans_is_declared_and_not_derived_from_price():
    """Порядок тарифов объявлен ЯВНО, а не выведен из цены.

    Цена настраивается окружением. Вывод порядка из неё сделал бы порядок
    тарифов конфигурируемым ПОБОЧНО: правка цены Basic выше цены Pro молча
    превратила бы понижение в повышение и разрешила бы отвергаемый сегодня
    переход.
    """
    assert isinstance(PLAN_ORDER, tuple), "порядок обязан быть неизменяемым"
    assert PLAN_ORDER == ("free", "basic", "pro")
    assert len(set(PLAN_ORDER)) == len(PLAN_ORDER), "повтор в порядке тарифов"


def test_every_shipped_plan_of_the_config_has_a_rank():
    """Ни один план УМОЛЧАНИЯ конфига не остаётся без ранга.

    Отказ по умолчанию — правильное поведение для незнакомого плана, но если в
    него попадает план, который проект отгружает сам, то отказ становится не
    защитой, а поломкой: пользователь Pro не смог бы даже продлиться.
    """
    shipped = {
        plan["id"]
        for plan in json.loads(Settings.model_fields["plan_limits"].default)
    }

    assert shipped <= set(PLAN_ORDER), shipped - set(PLAN_ORDER)


@pytest.mark.asyncio
async def test_an_upgrade_is_accepted(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Повышение остаётся открытым: растущему клиенту не отказывают в продаже."""
    await _seed_live_subscription(db_session, "basic")

    response = await _subscribe(authed_client, plan="pro")

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL
    payment = (await db_session.execute(select(Payment))).scalar_one()
    assert payment.plan == "pro"


@pytest.mark.asyncio
async def test_an_upgrade_does_not_burn_the_paid_remainder(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Прохибиция 05-01 соблюдена: срок считается от СРОКА, а не от сегодня.

    Это половина решения, ради которой оно и выбрано: остаток младшего тарифа
    переживает переход, а не превращается в ноль в момент оплаты старшего.
    """
    current = await _seed_live_subscription(db_session, "basic", days=25)

    await _subscribe(authed_client, plan="pro")
    with patch("app.services.payment_service.add_messages", new_callable=AsyncMock):
        processed = await handle_webhook(
            db_session,
            event="payment.succeeded",
            payment_data={"object": {"id": "yoo_1"}},
        )

    assert processed is True
    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "переход не должен заводить вторую строку"
    assert rows[0].plan == "pro", "оплаченный старший тариф не применён"
    assert _aware(rows[0].expires_at) > current + timedelta(days=27), (
        "оплаченный остаток младшего тарифа сгорел"
    )


@pytest.mark.asyncio
async def test_a_downgrade_is_refused_with_a_named_reason(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Понижение отвергается НА ВХОДЕ и говорит, почему.

    Отвергнуть молча было бы тем же дефектом, который закрывает задача 1:
    устаревшая страница достижима, и голый редирект читался бы как «кнопка
    сломана».
    """
    await _seed_live_subscription(db_session, "pro")

    response = await _subscribe(authed_client, plan="basic")

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=downgrade"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
async def test_renewing_the_own_live_plan_is_still_accepted(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Гард смены плана не задевает продление СВОЕГО тарифа.

    Самый вероятный способ сломать этот вариант — отвергнуть вместе с
    понижением и продление, у которого план тоже «уже есть».
    """
    await _seed_live_subscription(db_session, "pro")

    response = await _subscribe(authed_client, plan="pro")

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL
    assert await _payments_count(db_session) == 1


@pytest.mark.asyncio
async def test_a_first_purchase_from_free_is_still_accepted(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Подписки нет вовсе — сжигать нечего, и гард не участвует."""
    response = await _subscribe(authed_client, plan="basic")

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL
    assert await _payments_count(db_session) == 1


@pytest.mark.asyncio
async def test_a_downgrade_after_the_period_has_ended_is_accepted(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Истёкший срок снимает гард: остатка, который можно сжечь, больше нет.

    Правило защищает УПЛАЧЕННОЕ, а не запирает пользователя в тарифе навсегда.
    """
    owner = await _current_user(db_session)
    db_session.add(
        Subscription(
            user_id=owner.id,
            plan="pro",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            is_active=True,
        )
    )
    await db_session.commit()

    response = await _subscribe(authed_client, plan="basic")

    assert response.status_code == 302
    assert response.headers["location"] == CONFIRMATION_URL


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "live_plan,requested", [("platinum", "basic"), ("basic", "platinum")]
)
async def test_a_plan_without_a_rank_fails_closed(
    authed_client: AsyncClient,
    db_session: AsyncSession,
    test_settings,
    live_plan: str,
    requested: str,
):
    """ОТКАЗ ПО УМОЛЧАНИЮ: незнакомому плану ранг не угадывается.

    Перечень тарифов правится переменной окружения, а `PLAN_ORDER` — кодом.
    Разойтись они могут в любую сторону, и в обеих «догадка» стоила бы денег:
    угаданное повышение подарило бы месяц, угаданное понижение сожгло бы
    остаток. Отказ стоит одного лишнего экрана, догадка — уплаченных денег.
    """
    test_settings.plan_limits = UNRANKED_PLAN_LIMITS
    try:
        await _seed_live_subscription(db_session, live_plan)
        response = await _subscribe(authed_client, plan=requested)
    finally:
        test_settings.plan_limits = Settings.model_fields["plan_limits"].default

    assert response.status_code == 302
    assert response.headers["location"] == "/billing?error=downgrade"
    assert await _payments_count(db_session) == 0


@pytest.mark.asyncio
async def test_the_lower_plan_card_explains_itself_instead_of_offering_a_button(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Четвёртое состояние CTA: подпись С ПРИЧИНОЙ вместо кнопки.

    Карточка без кнопки и без слов читается как поломка витрины. Асимметрия
    («вверх можно, вниз нельзя») обязана быть объяснена НА ЭКРАНЕ, а не только
    в коде: пользователь кода не читает.
    """
    await _seed_live_subscription(db_session, "pro")

    html = (await authed_client.get("/billing")).text

    assert CAPTION_DOWNGRADE in html, "младший тариф не объяснил отсутствие кнопки"
    assert 'value="basic"' not in html, "младший тариф всё ещё обещает оплату"
    # Витрина при этом НЕ гаснет: карточка младшего плана на месте целиком.
    assert "Basic" in html
    assert "data-plans" in html


@pytest.mark.asyncio
async def test_the_higher_plan_card_still_offers_the_upgrade(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Парный тест: подпись не должна встать на карточки, которым она не нужна.

    Без него предыдущий тест зеленел бы на разметке, погасившей ВСЕ кнопки.
    """
    await _seed_live_subscription(db_session, "basic")

    html = (await authed_client.get("/billing")).text

    assert 'value="pro"' in html, "повышение перестало предлагаться"
    assert CAPTION_DOWNGRADE not in html, "подпись встала на карточку повышения"


@pytest.mark.asyncio
async def test_without_a_live_subscription_every_paid_card_keeps_its_button(
    authed_client: AsyncClient,
):
    """Гард не трогает витрину пользователя без действующей подписки."""
    html = (await authed_client.get("/billing")).text

    assert 'value="basic"' in html
    assert 'value="pro"' in html
    assert CAPTION_DOWNGRADE not in html


# =============================================================================
# СТАДИЯ ПРИМЕНЕНИЯ — правило `upgrade-only` там, где приходят деньги
# =============================================================================
#
# ЧЕМ ЭТИ ТЕСТЫ ОТЛИЧАЮТСЯ ОТ СОСЕДНИХ. Все тесты выше останавливаются на 302
# гарда формы — то есть на стадии НАМЕРЕНИЯ, где решается, продавать ли. Ниже
# проверяется вторая стадия: что подтверждённый платёж делает с УЖЕ ДЕЙСТВУЮЩЕЙ
# подпиской. До этого плана регрессии на неё не было ни одной, и правило
# `upgrade-only` существовало ровно на входе: `_apply_extension` перезаписывал
# `subscription.plan` безусловно.
#
# ВОСПРОИЗВЕДЁННЫЙ ДЕФЕКТ (гэп 1, 05-VERIFICATION.md). Пользователь без
# подписки нажимает «Оплатить» дважды — сначала Pro, потом Basic. Гард формы в
# этом сценарии не срабатывает ВОВСЕ: на момент ОБОИХ нажатий действующей
# подписки нет, сжигать нечего. Оба платежа подтверждаются, и оплаченный месяц
# старшего тарифа становится днями младшего.


def _app_settings() -> Settings:
    """Настоящие `Settings` с УМОЛЧАНИЯМИ конфига, а не MagicMock.

    Нужны стадии применения с решения D-29: цена действующего плана читается из
    `parsed_plan_limits`, то есть доля месяца считается по НАСТОЯЩИМ ценам
    проекта (Free 0 ₽, Basic 1490 ₽, Pro 4900 ₽). MagicMock здесь не годится
    принципиально: его `parsed_plan_limits` не список словарей, и тест зеленел бы
    на откате к полному месяцу — то есть ровно на том исходе, который D-29
    отменяет.

    Два обязательных поля задаются теми же значениями, что в `tests/conftest.py`:
    боевой `.env` в суите не читается, а `Settings()` без них не строится.
    """
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret-key",
    )


async def _confirm(db: AsyncSession, payment_id: str = "yoo_1") -> bool:
    """Подтверждённое уведомление ЮKassa по конкретному платежу.

    `add_messages` подменяется по образцу соседних тестов: подписочная ветка его
    не зовёт, но подмена держит тест независимым от порядка ветвления.

    `get_settings` подменяется по образцу `_post`, и с решения D-29 это не
    оформление: ветка отказа читает цену действующего плана из конфига, а
    `Settings()` в суите не строится — боевого `.env` здесь нет.
    """
    with patch(
        "app.services.payment_service.add_messages", new_callable=AsyncMock
    ), patch(
        "app.services.payment_service.get_settings", return_value=_app_settings()
    ):
        return await handle_webhook(
            db,
            event="payment.succeeded",
            payment_data={"object": {"id": payment_id}},
        )


@pytest.mark.asyncio
async def test_a_confirmed_lower_plan_does_not_strip_the_higher_one_at_the_apply_stage(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Воспроизведение верификатора: младший тариф не снимает уплаченный старший.

    ПОРЯДОК ЗДЕСЬ — ПРЕДМЕТ ПРОВЕРКИ, А НЕ ОФОРМЛЕНИЕ. Оба платежа заводятся ДО
    первого уведомления, потому что именно так дефект и достижим: пока подписки
    нет, гард формы не участвует, и «понижение» проскакивает мимо него обоими
    нажатиями.

    РАЗДЕЛЕНИЕ СРОКОВ ЧИСЛОВОЕ. Один календарный месяц — не больше 31 дня, два —
    не меньше 59; порог в 45 дней лежит между ними, поэтому промах в любую
    сторону однозначен: «срок сдвинут один раз» и «сдвинут дважды» не могут
    оказаться по одну сторону порога.

    ⚠️ УТВЕРЖДЕНИЕ О СРОКЕ ПОМЕНЯЛО ЗНАК ВМЕСТЕ С РЕШЕНИЕМ ВЛАДЕЛЬЦА D-29, И ЭТО
    ГЛАВНОЕ В ЭТОЙ ПРАВКЕ. Раньше здесь стояло `> now + 45 дней` с пояснением
    «деньги второго платежа не превратились в дни» — и ровно это утверждение
    ЗАКРЕПЛЯЛО обход цены как ожидаемое поведение: платёж `basic` за 1490 ₽
    покупал полный календарный месяц действующего `pro` стоимостью 4900 ₽, и
    повторов не ограничивало ничто. Решение D-29: отвергнутый платёж продолжает
    давать дни, но ПО УПЛАЧЕННОМУ тарифу — долю месяца по отношению уплаченной
    суммы к цене действующего плана.

    Утверждение стало ДВУСТОРОННИМ, и обе стороны несущие: нижняя граница
    (`> now + 33 дня`) держит принцип «деньги ВСЕГДА превращаются в дни» — без
    неё тест зеленел бы на коде, не выдавшем ничего; верхняя (`< now + 45 дней`)
    держит то, ради чего решение принято, — второй платёж НЕ купил второго
    полного месяца старшего тарифа. Порог 45 дней сохранён и поменял сторону:
    именно это и делает регрессию доказательной.

    ⚠️ ВТОРОЙ ПЛАТЁЖ ЗАВОДИТСЯ НАПРЯМУЮ И БЕЗ ЗАПИСАННОГО ОТВЕТА (D-28). Пока
    ответа гарда на платеже не существовало, форма годилась: оба нажатия
    проходили мимо гарда, потому что подписки на их момент не было. С появлением
    колонки `switch_authorized` форма записывает на ОБА платежа разрешение
    `True` — и путь, который проверяет ЭТОТ тест (решение принимает ПРАВИЛО),
    через форму больше не достижим. Достижим он остаётся у строк, заведённых до
    ревизии `0019`, и именно они здесь и сеются. Путь, где оба платежа несут
    записанное `True`, ЭТИМ ПЛАНОМ НЕ ЗАКРЫТ и закрывается планом `05-17`
    потолком одновременных намерений (`cap-different-plan`).
    """
    await _subscribe(authed_client, plan="pro", payment_id="yoo_pro")
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None
    )

    assert await _confirm(db_session, "yoo_pro") is True
    assert await _confirm(db_session, "yoo_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "два платежа завели две подписки"
    assert rows[0].plan == "pro", "оплаченный старший тариф снят младшим платежом"
    now = datetime.now(timezone.utc)
    assert _aware(rows[0].expires_at) > now + timedelta(days=33), (
        "деньги второго платежа не превратились в дни — исход «взяли и не выдали "
        "ничего», названный решением D-29 худшим"
    )
    assert _aware(rows[0].expires_at) < now + timedelta(days=45), (
        "платёж младшего тарифа купил ПОЛНЫЙ месяц действующего старшего: "
        "1490 ₽ за месяц Pro стоимостью 4900 ₽ (D-29 нарушен)"
    )


@pytest.mark.asyncio
async def test_the_preserved_plan_is_visible_in_the_log(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Расхождение уплаченного и действующего тарифа оставляет свой след.

    Без собственного ключа исход прячется за `subscription_payment_succeeded`,
    который печатает план ПЛАТЕЖА как обычный успех: разбирающему обращение
    пользователя опереться не на что. Уровень `warning`, а не `info` — платёж
    принят, дни выданы, но уплаченный тариф применён НЕ был.

    ⚠️ ВТОРОЙ ПЛАТЁЖ БЕЗ ЗАПИСАННОГО ОТВЕТА — по той же причине, что у соседа
    выше: ключ `subscription_plan_preserved` пишется только там, где переход
    ОТВЕРГНУТ, а через форму после D-28 оба платежа уносят разрешение `True` и
    отказа не возникает ни у одного.
    """
    await _subscribe(authed_client, plan="pro", payment_id="yoo_pro")
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None
    )

    await _confirm(db_session, "yoo_pro")
    with patch("app.services.payment_service.logger") as spy:
        await _confirm(db_session, "yoo_basic")

    preserved = [
        call
        for call in spy.warning.call_args_list
        if call.args and call.args[0] == "subscription_plan_preserved"
    ]
    assert preserved, "сохранение старшего тарифа не оставило следа в журнале"
    fields = preserved[0].kwargs
    assert fields.get("plan") == "pro", "не назван сохранённый тариф"
    assert fields.get("paid_plan") == "basic", "не назван уплаченный тариф"
    assert fields.get("yookassa_id") == "yoo_basic"
    assert fields.get("user_id") == (await _current_user(db_session)).id


@pytest.mark.asyncio
async def test_a_confirmed_higher_plan_is_applied_at_the_apply_stage(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Повышение на стадии применения ОСТАЁТСЯ повышением.

    Самый вероятный способ сломать этот план — отвергнуть вместе с понижением и
    повышение, перепутав направление сравнения рангов.
    """
    await _seed_live_subscription(db_session, "basic")

    await _subscribe(authed_client, plan="pro")
    assert await _confirm(db_session) is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "оплаченное повышение не применено"


@pytest.mark.asyncio
async def test_renewing_the_own_plan_still_moves_the_date_at_the_apply_stage(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Продление СВОЕГО тарифа новой сверкой не задето: план тот же, срок дальше."""
    current = await _seed_live_subscription(db_session, "pro", days=25)

    await _subscribe(authed_client, plan="pro")
    assert await _confirm(db_session) is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro"
    assert _aware(rows[0].expires_at) > current + timedelta(days=27), (
        "продление перестало двигать срок от существующего"
    )


async def _seed_subscription_payment(
    db: AsyncSession,
    plan: str | None,
    payment_id: str,
    *,
    switch_authorized: bool | None = None,
    amount: str = "1490.00",
) -> Payment:
    """Подписочный платёж в состоянии «уведомление ещё не приходило».

    Строка заводится НАПРЯМУЮ, а не формой: оба сценария ниже описывают платежи,
    которые форма завести не может вовсе — с пустым планом (поле обязательное) и
    с планом, которого нет в конфиге. Дефект при этом достижим: платёж мог быть
    заведён до того, как конфиг разошёлся с `PLAN_ORDER`.

    Владелец платежа — пользователь, которого заводит фикстура `authed_client`;
    поэтому тесты, ходящие только в БД, её всё равно запрашивают.

    `switch_authorized` — ЗАПИСАННЫЙ ОТВЕТ ГАРДА (D-28). Умолчание `None`
    означает «правило не спрашивали», то есть строку, заведённую ДО ревизии
    `0019`; именно на таких строках живёт остаточный путь, который форма после
    плана `05-17` завести уже не сможет. Умолчание оставлено прежним по смыслу,
    поэтому ни один существующий вызов помощника не меняется.

    `amount` — УПЛАЧЕННАЯ СУММА, и она перестала быть безразличной с решением
    D-29: платёж, чей план не применён, покупает долю месяца ПО НЕЙ, а не
    календарный месяц действующего тарифа. Умолчание — цена Basic, то есть
    прежнее зашитое значение; сценарии, где важна разница цен, называют её явно.
    """
    payment = Payment(
        user_id=(await _current_user(db)).id,
        yookassa_payment_id=payment_id,
        status="pending",
        amount_value=amount,
        amount_currency="RUB",
        kind="subscription",
        plan=plan,
        messages_count=None,
        package_name=None,
        switch_authorized=switch_authorized,
    )
    db.add(payment)
    await db.commit()
    return payment


@pytest.mark.asyncio
async def test_a_payment_without_a_plan_moves_the_date_and_leaves_the_plan_alone(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пустой план платежа двигает срок и НЕ трогает действующий тариф.

    Ветка существовала в коде и до этого плана, но регрессии не имела ни одной.
    Сверка ранга встала рядом с ней, поэтому проверка нужна именно теперь:
    `switch_is_refused("pro", "")` вернул бы `True` — и без явного выхода по
    пустому плану ветка начала бы писать в журнал строку о расхождении, которого
    не было.
    """
    current = await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(db_session, None, "yoo_noplan")

    assert await _confirm(db_session, "yoo_noplan") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "пустой план платежа переписал действующий"
    assert _aware(rows[0].expires_at) > current + timedelta(days=27), (
        "оплаченные дни не выданы"
    )


@pytest.mark.asyncio
async def test_a_paid_plan_without_a_rank_keeps_the_live_plan_at_the_apply_stage(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Зеркало `test_a_plan_without_a_rank_fails_closed` на стадии применения.

    Тот держит отказ по умолчанию на входе, этот — там, где приходят деньги.
    Инвариант один и тот же: догадка о ранге незнакомого плана стоит денег в обе
    стороны. Разница только в цене отказа — на входе это лишний экран, здесь
    отказать платежу нельзя вовсе, поэтому «отказ» означает сохранение
    действующего тарифа при выданных днях.

    ⚠️ ЧИСЛО ДНЕЙ ИЗМЕНИЛОСЬ ВМЕСТЕ С РЕШЕНИЕМ D-29, ПРЕДМЕТ ТЕСТА — НЕТ. Раньше
    здесь стояло `> current + 27 дней`, то есть отказ покупал ПОЛНЫЙ месяц
    действующего Pro за 1490 ₽. Теперь он покупает долю по уплаченному. Держится
    ровно то же, что и раньше: ранг не угадан И дни выданы, — но верхняя граница
    добавлена, потому что без неё тест снова закреплял бы обход цены.
    """
    current = await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(db_session, "platinum", "yoo_unranked")

    with patch("app.services.payment_service.logger") as spy:
        assert await _confirm(db_session, "yoo_unranked") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "незнакомому плану угадали ранг"
    assert _aware(rows[0].expires_at) > current, "оплаченные дни не выданы"
    assert _aware(rows[0].expires_at) < current + timedelta(days=27), (
        "отвергнутый платёж купил полный месяц действующего тарифа (D-29)"
    )
    assert any(
        call.args and call.args[0] == "subscription_plan_preserved"
        for call in spy.warning.call_args_list
    ), "отказ по умолчанию не оставил следа"


@pytest.mark.asyncio
async def test_the_first_subscription_still_takes_its_plan_from_the_payment(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Первая покупка с Free заводит подписку с планом ИЗ ПЛАТЕЖА.

    Ветка вставки сверку ранга не получила и получить не должна: подписки нет,
    защищать нечего, а сравнение ранга с пустотой отвергло бы первую же покупку.
    Тест держит её от правки «заодно».
    """
    await _subscribe(authed_client, plan="basic")
    assert await _confirm(db_session) is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "basic", "первая подписка не взяла план из платежа"
    assert _aware(rows[0].expires_at) > datetime.now(timezone.utc)


# =============================================================================
# СТАДИЯ ПРИМЕНЕНИЯ НА ИСТЁКШЕМ СРОКЕ — ветка, которой у соседнего раздела нет
# =============================================================================
#
# ЧЕМ ЭТОТ РАЗДЕЛ ОТЛИЧАЕТСЯ ОТ ПРЕДЫДУЩЕГО. Там КАЖДЫЙ тест сеет ЖИВУЮ подписку
# (`_seed_live_subscription`), и ровно поэтому суита из 1665 тестов оставалась
# зелёной при работающем блокере: единственный тест истёкшего срока
# (`test_a_downgrade_after_the_period_has_ended_is_accepted`) останавливается на
# 302 гарда формы и до `handle_webhook` не доходит вовсе. Стадия ПРИМЕНЕНИЯ на
# истёкшем сроке не была покрыта ни одним тестом.
#
# ВОСПРОИЗВЕДЁННЫЙ ДЕФЕКТ (гэп 1 раунда 3, `05-VERIFICATION.md`). Подписка `pro`,
# срок истёк вчера; пользователь покупает `basic` — гард формы его ПРОПУСКАЕТ
# (защищать нечего). Уведомление подтверждает платёж, и `_apply_extension` зовёт
# правило БЕЗУСЛОВНО: план остаётся `pro`. Деньги взяты за тариф, который не
# выдан, а со следующей попытки подписка снова живая и гард отвечает
# `?error=downgrade` — понижение становится недостижимым на всё время жизни
# аккаунта.
#
# РЕШЕНИЕ ВЛАДЕЛЬЦА (чекпойнт плана 05-13): `apply-after-expiry` — истёкший срок
# снимает отказ на ОБЕИХ стадиях, оплаченное понижение применяется.


async def _seed_expired_subscription(
    db: AsyncSession, plan: str, *, days_ago: int = 1
) -> datetime:
    """Зеркало `_seed_live_subscription` с ПРОШЕДШИМ сроком. Возвращает срок.

    Срок возвращается, чтобы тест умел отличить «сдвинут от старого срока» от
    «сдвинут от сегодня»: правило D-04 требует второго, и без возврата исходной
    величины разница была бы неотличима.
    """
    expires_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    db.add(
        Subscription(
            user_id=(await _current_user(db)).id,
            plan=plan,
            expires_at=expires_at,
            is_active=True,
        )
    )
    await db.commit()
    return expires_at


@pytest.mark.asyncio
async def test_an_expired_period_lets_the_paid_plan_through_at_the_apply_stage(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Прямое воспроизведение верификатора: истёкший срок ВЫДАЁТ уплаченный план.

    РАЗДЕЛЕНИЕ СРОКОВ ЧИСЛОВОЕ И ДВУСТОРОННЕЕ. Месяц от СЕГОДНЯ лежит между 28 и
    31 днём, поэтому проверяются ОБЕ границы — больше «сейчас + 27 дней» и меньше
    «сейчас + 45 дней». Одной верхней границы мало: без нижней тест зеленел бы на
    коде, который дней не выдал вовсе или посчитал их от прошедшей даты.
    """
    await _seed_expired_subscription(db_session, "pro")

    await _subscribe(authed_client, plan="basic")
    assert await _confirm(db_session) is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "подтверждение завело вторую строку подписки"
    assert rows[0].plan == "basic", (
        "деньги взяты за тариф, который не выдан: истёкший срок оставил "
        "старший план на стадии применения"
    )
    now = datetime.now(timezone.utc)
    assert _aware(rows[0].expires_at) > now + timedelta(days=27), (
        "оплаченные дни не выданы"
    )
    assert _aware(rows[0].expires_at) < now + timedelta(days=45), (
        "срок посчитан не от сегодня — D-04 нарушен"
    )


@pytest.mark.asyncio
async def test_the_expired_period_writes_no_preserved_plan_warning(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """На этом пути сохранять нечего — значит и следа о сохранении быть не должно.

    Ключ `subscription_plan_preserved` читается разбирающим обращение как «тариф
    сохранён, уплаченный не применён». Написать его там, где тариф КАК РАЗ выдан,
    значило бы соврать журналу (T-05-65).
    """
    await _seed_expired_subscription(db_session, "pro")
    await _subscribe(authed_client, plan="basic")

    with patch("app.services.payment_service.logger") as spy:
        assert await _confirm(db_session) is True

    preserved = [
        call
        for call in spy.warning.call_args_list
        if call.args and call.args[0] == "subscription_plan_preserved"
    ]
    assert preserved == [], (
        "журнал сообщает о сохранении тарифа там, где тариф выдан"
    )


@pytest.mark.asyncio
async def test_an_expired_period_still_renews_the_own_plan(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Продление СВОЕГО тарифа на истёкшем сроке не задето правкой «заодно».

    Равные планы правилом не задеваются вовсе, и снятие отказа по сроку не имеет
    права это изменить: подписчик Pro, пропустивший месяц, продлевает Pro.
    """
    await _seed_expired_subscription(db_session, "pro")

    await _subscribe(authed_client, plan="pro")
    assert await _confirm(db_session) is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "продление своего тарифа сменило план"
    now = datetime.now(timezone.utc)
    assert now + timedelta(days=27) < _aware(rows[0].expires_at) < now + timedelta(
        days=45
    ), "срок продления посчитан не от сегодня"


@pytest.mark.asyncio
async def test_a_live_period_still_keeps_the_higher_plan(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ПАРНЫЙ тест: истёкшего срока здесь НЕТ, и отказ обязан остаться.

    Без него первый тест раздела зеленел бы на коде, снявшем отказ вообще везде —
    то есть на возврате ровно того дефекта, который закрыл план 05-11. Платёж
    заводится напрямую, потому что гард формы такую покупку не пропустит.

    ⚠️ ЧИСЛО ДНЕЙ ИЗМЕНИЛОСЬ ВМЕСТЕ С РЕШЕНИЕМ D-29, ПРЕДМЕТ ТЕСТА — НЕТ.
    Отказ по-прежнему означает «действующий тариф сохранён, дни выданы»; менялась
    только МЕРА дней, и верхняя граница добавлена, чтобы полный месяц старшего
    тарифа за цену младшего не вернулся сюда молча.
    """
    current = await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(db_session, "basic", "yoo_live_basic")

    assert await _confirm(db_session, "yoo_live_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", (
        "живой оплаченный старший тариф снят младшим платежом"
    )
    assert _aware(rows[0].expires_at) > current, "оплаченные дни не выданы"
    assert _aware(rows[0].expires_at) < current + timedelta(days=27), (
        "отвергнутый платёж купил полный месяц действующего тарифа (D-29)"
    )


def test_the_liveness_is_sampled_before_the_date_moves():
    """ЛОВУШКА ПОРЯДКА, проверяемая машиной, а не прочтением.

    Признак живости, снятый ПОСЛЕ `next_expiry`, всегда отвечает «живо»: сдвиг
    срока перезаписывает ту самую величину, по которой принимается следующее
    решение в той же функции. Блокер восстанавливается молча, правкой, которая
    выглядит безобидной перестановкой двух строк (T-05-63).

    СОВПАДЕНИЕ ИЩЕТСЯ ПО ТИПАМ УЗЛОВ, А НЕ ПОДСТРОКОЙ. Докстринг самой
    `_apply_extension` обязан НАЗВАТЬ оба имени (задача 3 плана 05-13), поэтому
    поиск подстроки в тексте или в дампе дерева прочёл бы содержимое строкового
    литерала: при обоих именах оба индекса стали бы нулевыми и тест падал бы на
    ВЕРНОМ коде, при одном имени — зеленел бы при ЛЮБОМ порядке. Поэтому
    докстринг из перечня операторов вычёркивается, а ищется присваивание, ЗНАЧЕНИЕ
    которого — вызов функции с этим именем. Упоминание имени в комментарии
    оператором не является и тест не ломает; перестановка двух операторов — ломает.

    ⚠️ ТЕСТ ДЕРЖИТ И ВЕЛИЧИНУ, А НЕ ТОЛЬКО ПОРЯДОК (IN-02 раунда 4). Держа один
    порядок, он зеленел бы при подмене АРГУМЕНТА снятия на любое другое поле
    платежа или подписки — правило начинало бы решать по чужой величине, стоя
    при этом на верном месте. Проверяется, что признак снимается ИМЕННО от
    `subscription.expires_at`, то есть от той величины, которую перезаписывает
    `next_expiry`: только для неё порядок вообще что-то значит. Нагрузка на этот
    тест выросла вместе с планом 05-15 — сдвиг срока теперь стоит В ДВУХ ВЕТКАХ,
    и половина инварианта под возросшей нагрузкой была бы долгом следующего
    раунда.
    """
    import app.services.payment_service as module

    function = ast.parse(inspect.getsource(module._apply_extension)).body[0]
    statements = [
        node
        for node in function.body
        if not (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
    ]

    def _assignment_from(name: str) -> int:
        for index, node in enumerate(statements):
            if (
                isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Call)
                and getattr(node.value.func, "id", None) == name
            ):
                return index
        raise AssertionError(f"в теле нет присваивания из вызова {name}")

    live = _assignment_from("subscription_is_live")
    moved = _assignment_from("next_expiry")

    assert live < moved, (
        "признак живости снимается ПОСЛЕ сдвига срока — правило всегда получит "
        f"«живо», и блокер восстановлен молча (индексы {live} и {moved})"
    )

    sampled = statements[live].value.args[0]
    assert isinstance(sampled, ast.Attribute) and sampled.attr == "expires_at", (
        "признак снимается НЕ от той величины, которую перезаписывает "
        "`next_expiry`: порядок соблюдён, а правило решает по чужому полю "
        f"({ast.dump(sampled)})"
    )


def test_the_switch_semantics_are_named_in_the_place_that_moves_the_date():
    """Правило записано ТАМ, ГДЕ двигается срок, а не только в документах фазы.

    Докстринг `_extend_subscription` объясняет, почему запрос активной подписки
    повторяет читателя дословно, и до этого плана МОЛЧАЛ о том, что делается с
    планом. Читатель этой функции — тот самый человек, который завтра будет
    решать, можно ли поменять здесь порядок двух строк.

    НАЗВАТЬ СЕМАНТИКУ МАЛО — ОНА ОБЯЗАНА СОВПАДАТЬ С КОДОМ. Верификатор нашёл
    ровно это расхождение: докстринг утверждал, что понижение «не предлагается
    карточкой и не принимается гардом», умалчивая, что подтверждённый платёж его
    ПРИМЕНЯЕТ. Поэтому к двум словам добавлено утверждение об ИСХОДЕ: расхождение
    уплаченного и действующего тарифа названо своим ключом журнала, а ключ
    существует только вместе с поведением, которое его пишет.
    """
    source = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "services"
        / "payment_service.py"
    ).read_text(encoding="utf-8")
    body = source[source.index("async def _extend_subscription(") :]
    docstring = body[: body.index('"""', body.index('"""') + 3)]

    assert "upgrade-only" in docstring, "выбранная семантика не названа"
    assert "05-01" in docstring, "решение не связано с прохибицией, которую щадит"
    assert "subscription_plan_preserved" in docstring, (
        "докстринг молчит о том, чем кончается подтверждённый платёж младшего "
        "тарифа — то есть снова описывает не исполняемое поведение"
    )
    # УРОК ПРЕДЫДУЩЕГО РАУНДА, ПРИМЕНЁННЫЙ ВТОРОЙ РАЗ. Проверка на два слова
    # зеленела при неверном поведении, поэтому КАЖДОЕ новое утверждение
    # докстринга получает своё утверждение теста. Подстрока «истёк» существует
    # только вместе с абзацем об исходе на ИСТЁКШЕМ сроке — том самом, о котором
    # докстринг молчал, пока код брал деньги за невыдаваемый тариф (гэп 1
    # раунда 3).
    assert "истёк" in docstring, (
        "докстринг молчит об исходе на ИСТЁКШЕМ сроке — стадии, где деньги уже "
        "ушли, а тариф мог остаться невыданным"
    )
    assert "subscription_is_live" in docstring, (
        "докстринг не называет, ЧЕМ считается признак живости и где он объявлен"
    )
    # ТРЕТЬЕ ПРИМЕНЕНИЕ ТОГО ЖЕ УРОКА. Подстрока `switch_authorized` существует
    # только вместе с абзацем о том, ЧТО решает, применять ли план: записанное
    # разрешение, а не сегодняшнее состояние подписки. Пока абзаца не было,
    # докстринг описывал стадию, которая принимает решение заново, — то есть
    # снова не исполняемое поведение (гэп 1 раунда 4).
    assert "switch_authorized" in docstring, (
        "докстринг молчит о том, что решение о плане принимается по ЗАПИСАННОМУ "
        "разрешению, а не по состоянию подписки в момент уведомления"
    )


# =============================================================================
# РАЗРЕШЕНИЕ СДЕЛКИ ЗАПИСАНО НА ПЛАТЕЖЕ — состояние подписки МЕНЯЕТСЯ между
# продажей и подтверждением
# =============================================================================
#
# ЧЕМ ЭТОТ РАЗДЕЛ ОТЛИЧАЕТСЯ ОТ ВСЕХ СОСЕДНИХ, И ЭТО ЕДИНСТВЕННОЕ ОТЛИЧИЕ.
# Соседние разделы держат состояние подписки НЕИЗМЕННЫМ между стадией ПРОДАЖИ
# и стадией ПОДТВЕРЖДЕНИЯ: подписка либо живая на обеих, либо истёкшая на
# обеих, либо отсутствует на обеих. Ровно поэтому суита из 1681 теста
# оставалась зелёной при работающем блокере — класса тестов, меняющих это
# состояние МЕЖДУ двумя стадиями, не было ни одного.
#
# Здесь состояние МЕНЯЕТСЯ. Между двумя моментами лежит вся сессия оплаты у
# ЮKassa, и за это время подписка успевает ожить (соседний платёж подтверждён),
# истечь (прошло время) или появиться впервые.
#
# РЕШЕНИЕ ВЛАДЕЛЬЦА D-28: ответ гарда о разрешённом переходе записывается НА
# ПЛАТЁЖ (`payments.switch_authorized`, ревизия `0019`), и стадия применения
# читает записанный ФАКТ, а не пересчитывает предикат по изменившейся строке
# подписки. `True` — правило спросили и переход разрешило; `False` — спросили и
# отвергло; `NULL` — НЕ спрашивали (пакетный платёж либо строка старше ревизии).


@pytest.mark.asyncio
async def test_a_deal_sold_on_an_expired_period_is_delivered_after_the_period_revives(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Зеркальный путь WR-01 раунда 4: продано на истёкшем — выдано на ожившем.

    ВРЕД ЗДЕСЬ ДОСТАЁТСЯ ПОЛЬЗОВАТЕЛЮ, а не кассе, и этим путь отличается от
    денежного (CR-01). Подписка `pro` истекла вчера; пользователь покупает
    `basic` — гард ПРОПУСКАЕТ покупку, потому что защищать нечего, и обещание
    карточки «переход на младший тариф — после окончания оплаченного срока»
    исполнено ровно в этот момент. Дальше подтверждается соседний платёж `pro`,
    и период ОЖИВАЕТ. К моменту, когда приходит уведомление о проданном
    `basic`, состояние подписки уже другое — и правило, пересчитанное по нему,
    отвечает «отказ»: сделка продана под обещание и не выдана.

    Записанный ответ гарда (D-28) убирает эту переменную: платёж несёт то, что
    было ПРОДАНО, и стадия применения читает его, а не текущее состояние БД.
    """
    await _seed_expired_subscription(db_session, "pro")

    # ПРОДАЖА: период истёк, гард пропускает, ответ обязан быть записан.
    await _subscribe(authed_client, plan="basic", payment_id="yoo_basic")

    # ОКНО МЕЖДУ СТАДИЯМИ: соседний платёж оживляет период и ставит план `pro`.
    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=True
    )
    assert await _confirm(db_session, "yoo_pro") is True

    # ПРИМЕНЕНИЕ проданного: состояние подписки уже ДРУГОЕ.
    assert await _confirm(db_session, "yoo_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "два платежа завели две подписки"
    assert rows[0].plan == "basic", (
        "сделка продана под обещание «понижение будет применено» и НЕ выдана: "
        "стадия применения решила заново по состоянию, которого в момент "
        "продажи не было"
    )


@pytest.mark.asyncio
async def test_the_intent_stage_records_its_answer_on_the_payment(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Ответ гарда существует на строке платежа, а не только в стеке вызова.

    Пока ответ нигде не записан, любая пара «продали → выдали» решает заново по
    тому, что успело измениться. Утверждение самое простое из раздела и самое
    несущее: без него всё остальное чинило бы следствие.
    """
    await _subscribe(authed_client, plan="basic", payment_id="yoo_recorded")

    payment = (
        await db_session.execute(
            select(Payment).where(Payment.yookassa_payment_id == "yoo_recorded")
        )
    ).scalar_one()

    assert payment.switch_authorized is True, (
        "стадия намерения не записала СВОЙ ответ на платёж"
    )


@pytest.mark.asyncio
async def test_the_deal_cannot_be_sold_without_recording_its_authorization(
    db_session: AsyncSession,
):
    """Разрешение НЕЛЬЗЯ не записать: вызов без него падает громко.

    МАШИННАЯ ГАРАНТИЯ ВМЕСТО ДИСЦИПЛИНЫ ВЫЗЫВАЮЩЕГО. Параметр со значением по
    умолчанию однажды не подадут — ровно так разошлись две стадии дважды
    подряд, и ровно поэтому `kind` тоже объявлен обязательным keyword-only.
    Четвёртый вызывающий, заведённый завтра, обязан упасть НА ВЫЗОВЕ, а не
    тихо записать платёж, о котором неизвестно, что было продано.
    """
    with pytest.raises(TypeError):
        create_payment(
            db_session,
            user_id=1,
            kind="subscription",
            plan="basic",
            price="1490.00",
            package_name=None,
            messages_count=None,
        )


@pytest.mark.asyncio
async def test_a_package_payment_records_that_the_rule_was_not_asked(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Пакетный платёж записывает `NULL` ЗНАЧЕНИЕМ, а не отсутствием поля.

    Правило смены тарифа пакета не касается вовсе, и это обязано быть выражено
    записанным `NULL`, а не «забыли записать». Разница видна на стадии
    применения: `NULL` означает «не спрашивали», а не «спрашивали и отказали».
    """
    await _purchase(authed_client)

    payment = (
        await db_session.execute(
            select(Payment).where(Payment.yookassa_payment_id == "yoo_1")
        )
    ).scalar_one()

    assert payment.kind == "package"
    assert payment.switch_authorized is None, (
        "пакетному платежу записан ответ правила, которое его не касается"
    )


@pytest.mark.asyncio
async def test_a_legacy_payment_without_a_recorded_answer_still_decides_by_the_rule(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ПАРНЫЙ тест: строка старше ревизии `0019` по-прежнему решается правилом.

    Без него «читать записанный факт» можно было бы исполнить так, что строки
    без записанного ответа перестали бы решаться вовсе — и действующий старший
    тариф снимался бы любым подтверждённым младшим платежом, заведённым до
    ревизии. У такой строки записанному ответу взяться неоткуда, и выдумать его
    хуже, чем пересчитать.
    """
    await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_old", switch_authorized=None
    )

    assert await _confirm(db_session, "yoo_old") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", (
        "строка без записанного ответа перестала решаться правилом"
    )


# =============================================================================
# ДНИ ПО УПЛАЧЕННОМУ ТАРИФУ (D-29) — платёж, чей план не применён
# =============================================================================
#
# ДО ЭТОГО ПЛАНА `subscription.expires_at = next_expiry(...)` стоял БЕЗУСЛОВНО и
# ВЫШЕ решения о плане, поэтому отвергнутый платёж младшего тарифа покупал полный
# календарный месяц действующего СТАРШЕГО: 1490 ₽ давали месяц Pro стоимостью
# 4900 ₽, и повторов не ограничивало ничто.
#
# РЕШЕНИЕ ВЛАДЕЛЬЦА D-29: платёж продолжает давать дни — принцип «деньги ВСЕГДА
# превращаются в дни» сохранён, и «не выдать ничего» остаётся худшим из исходов,
# — но дни считаются ПО УПЛАЧЕННОМУ: доля календарного месяца по отношению
# уплаченной суммы к цене действующего плана, не меньше одного дня.


@pytest.mark.asyncio
async def test_a_pro_deal_sold_before_any_subscription_is_not_erased_by_a_later_basic(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """СЛУЧАЙ (1) третьего пункта `missing:` — подписки НЕТ на момент ОБЕИХ продаж.

    ⚠️ ЧЕМ ЭТОТ СЛУЧАЙ ОТЛИЧАЕТСЯ ОТ СОСЕДНЕГО, И ОТЛИЧИЕ ПРИНЦИПИАЛЬНО.
    У соседа подписка к моменту второго подтверждения уже существует как
    ПРОДЛЕВАЕМАЯ. Здесь подписки нет ВОВСЕ, поэтому первый подтверждённый платёж
    идёт веткой ПЕРВОЙ ВСТАВКИ, а не веткой продления — ровно то состояние,
    которое воспроизводил верификатор. Считать эти два теста дубликатами и
    удалить один нельзя.

    У ТРЁХ УТВЕРЖДЕНИЙ ЗДЕСЬ РАЗНЫЕ РОЛИ, и путать их значило бы записать в
    отчёт величину, которой ни один прогон не даёт:

    * «строка одна» — ЗАЩИТНОЕ, на входе ЗЕЛЁНОЕ;
    * `plan == "pro"` — ЗАЩИТНОЕ, на входе ЗЕЛЁНОЕ. У строки без записанного
      ответа решение принимает правило: `switch_is_refused("pro", "basic",
      period_is_live=True)` отвечает `True`, ветка `subscription_plan_preserved`
      возвращает управление, и план НЕ перезаписывается уже сегодня.
      Утверждение ловит регрессию БУДУЩЕГО — снятие старшего плана записанным
      фактом или долей месяца, — а не сегодняшний дефект;
    * срок строго между «сейчас + 33 дня» и «сейчас + 45 дней» — ЕДИНСТВЕННОЕ
      КРАСНОЕ на входе: сегодня отвергнутый платёж двигает срок на полный
      календарный месяц, и итог уходит за 59 дней.

    Путь, на котором план ДЕЙСТВИТЕЛЬНО стирается последним подтверждением, —
    это путь строк С записанным разрешением `True`, то есть заведённых ФОРМОЙ.
    Он этим планом НЕ достижим и закрывается планом `05-17` (потолок
    одновременных намерений, форма `cap-different-plan`).
    """
    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=None, amount="4900.00"
    )
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount="1490.00"
    )

    assert await _confirm(db_session, "yoo_pro") is True
    assert await _confirm(db_session, "yoo_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1, "два платежа завели две подписки"
    assert rows[0].plan == "pro", (
        "сделка на 4900 ₽ продана и не выдана: старший тариф снят последним "
        "подтверждённым младшим платежом"
    )
    now = datetime.now(timezone.utc)
    assert _aware(rows[0].expires_at) > now + timedelta(days=33), (
        "деньги второго платежа не превратились в дни"
    )
    assert _aware(rows[0].expires_at) < now + timedelta(days=45), (
        "второй платёж купил ВТОРОЙ полный месяц старшего тарифа за цену "
        "младшего (D-29 нарушен)"
    )


@pytest.mark.asyncio
async def test_an_upgrade_confirmed_last_is_still_applied_without_a_recorded_answer(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """ЗЕРКАЛО предыдущего по ПОРЯДКУ подтверждений: тот же посев, обратный порядок.

    Целиком защитный и на входе зелёный. Без него предыдущий тест зеленел бы на
    коде, запретившем менять план ВООБЩЕ: повышение обязано остаться повышением,
    а оплаченный остаток — не сгореть.
    """
    await _seed_subscription_payment(
        db_session, "pro", "yoo_pro", switch_authorized=None, amount="4900.00"
    )
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount="1490.00"
    )

    assert await _confirm(db_session, "yoo_basic") is True
    assert await _confirm(db_session, "yoo_pro") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "pro", "оплаченное повышение не применено"
    assert _aware(rows[0].expires_at) > datetime.now(timezone.utc) + timedelta(
        days=45
    ), "повышение сожгло оплаченный остаток младшего тарифа"


@pytest.mark.asyncio
async def test_a_refused_payment_buys_days_of_what_it_paid_for(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Журнал объясняет, ПОЧЕМУ дней девять, а не тридцать.

    НАЧАЛЬНОЕ СОСТОЯНИЕ НАЗВАНО ЗДЕСЬ ЯВНО, потому что соседних прогонов теперь
    три, а число выданных дней зависит от того, какой из них взят: ЖИВАЯ `pro`
    плюс отвергнутый `basic` без записанного ответа.

    Без своего ключа исход «выдано девять дней вместо тридцати» неотличим в
    журнале от «дни не выданы», и разбирающий обращение не сможет объяснить
    человеку ни числа, ни его основания.
    """
    await _seed_live_subscription(db_session, "pro", days=25)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount="1490.00"
    )

    with patch("app.services.payment_service.logger") as spy:
        assert await _confirm(db_session, "yoo_basic") is True

    preserved = [
        call
        for call in spy.warning.call_args_list
        if call.args and call.args[0] == "subscription_plan_preserved"
    ]
    assert preserved, "сохранение старшего тарифа не оставило следа в журнале"
    fields = preserved[0].kwargs
    assert fields.get("plan") == "pro"
    assert fields.get("paid_plan") == "basic"

    granted = fields.get("granted_days")
    assert isinstance(granted, int), "журнал не называет числа выданных дней"
    assert 1 <= granted <= 12, (
        f"выдано {granted} дней — это не доля месяца от 1490 ₽ при цене 4900 ₽"
    )
    assert str(fields.get("price_basis")) == "4900.00", (
        "журнал не называет цену, ПО КОТОРОЙ посчитаны дни — без неё число "
        "выданных дней нечем объяснить"
    )


@pytest.mark.asyncio
async def test_a_price_that_cannot_be_read_falls_back_to_the_whole_month(
    authed_client: AsyncClient, db_session: AsyncSession
):
    """Непрочитанная цена НЕ поднимает исключения и НЕ отнимает дней.

    ПРИЧИНА ТРЕБОВАНИЯ ПРИКЛАДНАЯ. Необработанное исключение в обработчике
    уведомления даёт 5xx, а 5xx на уведомлении ЮKassa запускает цикл повторов и
    оставляет платёж `pending` навсегда — класс отказа, уже стоивший фазе
    находки `WR-04` раунда 2.

    Перечень тарифов правится окружением, а действующий план записан в строке
    подписки: разойтись они могут в любую сторону, и тогда цены, по которой
    считать долю, взяться неоткуда. Откат к полному месяцу выбран в сторону
    пользователя — отнимать дни за расхождение конфига с базой не за что.
    """
    current = await _seed_live_subscription(db_session, "platinum", days=25)
    await _seed_subscription_payment(
        db_session, "basic", "yoo_basic", switch_authorized=None, amount="1490.00"
    )

    with patch("app.services.payment_service.logger") as spy:
        assert await _confirm(db_session, "yoo_basic") is True

    rows = await _subscription_rows(db_session)
    assert len(rows) == 1
    assert rows[0].plan == "platinum", "незнакомому плану угадали ранг"
    assert _aware(rows[0].expires_at) > current + timedelta(days=27), (
        "откат к полному месяцу не сработал — дни отняты за расхождение конфига"
    )

    assert any(
        call.args and call.args[0] == "subscription_prorating_skipped"
        for call in spy.warning.call_args_list
    ), "непрочитанная цена не оставила следа в журнале"
