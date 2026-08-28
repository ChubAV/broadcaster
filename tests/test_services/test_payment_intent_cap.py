"""Потолок незакрытых подписочных намерений КАК СВОЙСТВО СХЕМЫ (PAY-01).

Файл закрепляет переключение денежного пути плана 08-05: потолок держит
частичный уникальный индекс `uq_payments_open_subscription_intent`, а не
прикладная проверка; строка-намерение резервируется ДО обращения к ЮKassa;
просроченные намерения гасит ленивая уборка на пути самого пользователя.

ЧЕТЫРЕ ГРУППЫ УТВЕРЖДЕНИЙ, И НИ ОДНА НЕ ЗАМЕНЯЕТ ОСТАЛЬНЫЕ:

1. ПОТОЛОК. Второе незакрытое намерение отвергается, отказ приходит СВОИМ типом
   и НЕ ДОХОДИТ до платёжного SDK ни одним вызовом; чужой отказ ограничения не
   глотается.
2. УБОРКА. Гасит СТРОГО то, что считает предикат индекса, идемпотентна, честна
   счётчиком и применяет срок давности в Python.
3. ПОРЯДОК. У подписки «резерв → сеть → дозапись», у пакета «сеть → запись»;
   отказ SDK гасит СВОЮ ЖЕ строку, а не удаляет её и не оставляет `pending`.
4. ОПЛАЧИВАЕМОСТЬ. Погашенная строка остаётся зачисляемой: `expired` не входит
   в `TERMINAL_STATUSES`, и заявка на ней выигрывается.

⚠️ ОТКАЗ ОГРАНИЧЕНИЯ РАЗБИРАЕТСЯ ПЕРЕЧИТЫВАНИЕМ СОСТОЯНИЯ, А НЕ ИМЕНЕМ
ОГРАНИЧЕНИЯ, И ЭТО ГЛАВНОЕ, ЧТО ЗДЕСЬ ЗАКРЕПЛЕНО. Проектное решение фазы (D-06)
предписывало разбирать `IntegrityError` по имени
`uq_payments_open_subscription_intent`. Исполнимым такой разбор не является:
SQLite сообщает `UNIQUE constraint failed: payments.user_id` — КОЛОНКУ, а не
индекс, и разбор по имени зеленел бы на бою (PostgreSQL), молча не срабатывая на
ВСЕЙ суите проекта, которая идёт по SQLite. Потолок выглядел бы покрытым и покрыт
не был. Перенесён поэтому приём `_extend_subscription`: поймать, ПЕРЕЧИТАТЬ
состояние, при отсутствии конфликта поднять тот же объект заново. Что вердикт не
зависит от текста драйвера, закреплено машинно —
`test_the_verdict_does_not_depend_on_the_driver_text`.

ГРАНИЦА ФАЙЛА. Сверка двух ИСТОЧНИКОВ СХЕМЫ (модель против ревизии) живёт
отдельно — `tests/test_models/test_payment_open_intent_index.py`. Здесь
проверяется ПОВЕДЕНИЕ сервиса на базе, поднятой из моделей.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from yookassa.domain.notification import WebhookNotificationEventType

from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User
from app.services.payment_service import (
    KIND_PACKAGE,
    KIND_SUBSCRIPTION,
    PENDING_INTENT_TTL_HOURS,
    STATUS_EXPIRED,
    STATUS_PENDING,
    TERMINAL_STATUSES,
    PaymentCreationError,
    PendingIntentCapError,
    _expire_stale_intents,
    _is_open_intent_conflict,
    create_payment,
    handle_webhook,
)

# Цена доступа и текст отказа SDK выписаны ДОСЛОВНО, а не импортированы: тест,
# берущий значение из того же источника, что и код, утверждал бы «значение равно
# самому себе» и пережил бы подмену молча.
ACCESS_PRICE = "3000.00"
SDK_FAILURE_TEXT = "yookassa_sdk_internal_boom_do_not_render_me"

EVENT_SUCCEEDED = WebhookNotificationEventType.PAYMENT_SUCCEEDED


def _yoo_settings():
    mock_settings = MagicMock()
    mock_settings.yookassa_shop_id = "shop123"
    mock_settings.yookassa_secret_key = "secret"
    mock_settings.yookassa_return_url = "https://app.com/billing"
    mock_settings.app_name = "Broadcaster"
    return mock_settings


@contextmanager
def _sdk(payment_id: str = "yoo_new"):
    """Подменённый SDK, ОТДАЮЩИЙ СВОЙ МОК НАРУЖУ.

    Мок нужен телу теста, а не только вызову: гарантия «отказ не дошёл до сети»
    проверяется ЧИСЛОМ ВЫЗОВОВ, а не разбором исходника. Разбор ловит перенос
    строки; счётчик ловит и перенос, и обход.
    """
    payment = MagicMock()
    payment.id = payment_id
    payment.confirmation = MagicMock()
    payment.confirmation.confirmation_url = f"https://yookassa.ru/pay/{payment_id}"
    with patch(
        "app.services.payment_service.get_settings", return_value=_yoo_settings()
    ), patch(
        "app.services.payment_service.YooPayment.create", return_value=payment
    ) as create_mock:
        yield create_mock


@contextmanager
def _failing_sdk():
    """Подмена вызова SDK, ПОДНИМАЮЩАЯ исключение вместо возврата платежа."""
    with patch(
        "app.services.payment_service.get_settings", return_value=_yoo_settings()
    ), patch(
        "app.services.payment_service.YooPayment.create",
        side_effect=RuntimeError(SDK_FAILURE_TEXT),
    ) as create_mock:
        yield create_mock


async def _user(db, email: str = "cap@t.com") -> User:
    user = User(email=email, password_hash="h", name="T")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _intent(
    db,
    user: User,
    *,
    payment_id: str | None = "yoo_open",
    status: str = STATUS_PENDING,
    kind: str = KIND_SUBSCRIPTION,
    age_hours: float = 0,
) -> Payment:
    """Намерение с УПРАВЛЯЕМЫМ возрастом.

    Возраст ставится ЯВНЫМ ПРИСВАИВАНИЕМ после вставки: у колонки `created_at`
    объявлен `server_default=func.now()`, то есть СУБД проставляет текущий
    момент, и прошлого им не выразить вовсе — а срок давности только о прошлом и
    говорит.
    """
    payment = Payment(
        user_id=user.id,
        yookassa_payment_id=payment_id,
        status=status,
        amount_value=ACCESS_PRICE if kind == KIND_SUBSCRIPTION else "149.00",
        amount_currency="RUB",
        kind=kind,
        plan=None,
        messages_count=None if kind == KIND_SUBSCRIPTION else 100,
        package_name=None if kind == KIND_SUBSCRIPTION else "100 messages",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    payment.created_at = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    await db.commit()
    await db.refresh(payment)
    return payment


async def _subscribe(db, user: User):
    """Намерение оплатить ДОСТУП — ровно то, что подаёт обработчик формы."""
    return await create_payment(
        db,
        user_id=user.id,
        price=ACCESS_PRICE,
        kind=KIND_SUBSCRIPTION,
        plan=None,
        package_name=None,
        messages_count=None,
        switch_authorized=None,
    )


async def _buy_package(db, user: User):
    return await create_payment(
        db,
        user_id=user.id,
        price="149.00",
        kind=KIND_PACKAGE,
        package_name="100 messages",
        messages_count=100,
        switch_authorized=None,
    )


async def _rows(db, user: User) -> list[Payment]:
    db.expunge_all()
    return list(
        (
            await db.execute(
                select(Payment)
                .where(Payment.user_id == user.id)
                .order_by(Payment.id)
            )
        )
        .scalars()
        .all()
    )


async def _count(db, user: User) -> int:
    return await db.scalar(
        select(func.count()).select_from(Payment).where(Payment.user_id == user.id)
    )


# =============================================================================
# ПОТОЛОК: отказ приходит от схемы и не доходит до денег
# =============================================================================


@pytest.mark.asyncio
async def test_a_reserve_becomes_the_only_row_of_the_payment(db_session):
    """Резерв ДОЗАПИСЫВАЕТСЯ, а не дублируется второй строкой.

    Порядок «резерв → сеть → дозапись» имеет очевидный способ сломаться молча:
    вставить после успеха ВТОРУЮ строку, оставив резерв висеть рядом. Человек
    заплатил бы один раз, а в журнале у него оказалось бы два намерения — и
    второе, `pending`, заперло бы ему следующую оплату потолком.
    """
    user = await _user(db_session)

    with _sdk("yoo_only") as create_mock:
        result = await _subscribe(db_session, user)

    assert result["payment_id"] == "yoo_only"
    assert create_mock.call_count == 1
    rows = await _rows(db_session, user)
    assert len(rows) == 1, f"резерв продублирован: строк {len(rows)}"
    assert rows[0].yookassa_payment_id == "yoo_only", (
        "идентификатор платежа не дозаписан в резервную строку"
    )
    assert rows[0].status == STATUS_PENDING


@pytest.mark.asyncio
async def test_a_second_open_intent_is_refused_by_the_schema(db_session):
    """Второе незакрытое намерение отвергается — СУБД, а не проверкой в коде.

    Три утверждения разом, и ни одно не заменяет остальных: тип отказа СВОЙ
    (обработчик формы различает ветку по типу), ЮKassa не спрошена ни разу
    (отказ пришёл ДО того, как двинулись деньги), второй строки не осталось
    (точка сохранения откачена, а не оставлена мусором на денежной таблице).
    """
    user = await _user(db_session)
    await _intent(db_session, user, payment_id="yoo_first")
    before = await _count(db_session, user)

    with _sdk("yoo_second") as create_mock:
        with pytest.raises(PendingIntentCapError):
            await _subscribe(db_session, user)

    assert create_mock.call_count == 0, (
        f"ЮKassa вызвана {create_mock.call_count} раз(а) до отказа: платёж создан "
        "у них и не создан у нас"
    )
    assert await _count(db_session, user) == before, (
        "отвергнутое намерение оставило строку в `payments`"
    )


@pytest.mark.asyncio
async def test_the_refusal_says_nothing_of_the_database(db_session):
    """Текст отказа ФИКСИРОВАН: ни имени ограничения, ни текста драйвера, ни цифр.

    T-08-14: внутренности СУБД принадлежат журналу, а не экрану. Текст исходного
    отказа остаётся доступен отладчику через `__cause__` — и только ему.
    """
    user = await _user(db_session)
    await _intent(db_session, user, payment_id="yoo_first")

    with _sdk("yoo_second"):
        with pytest.raises(PendingIntentCapError) as refusal:
            await _subscribe(db_session, user)

    words = str(refusal.value)
    assert words == "Предыдущее подписочное намерение ещё не завершено"
    assert "uq_" not in words
    assert "UNIQUE" not in words.upper()
    assert not any(symbol.isdigit() for symbol in words), (
        "в тексте отказа появилась цифра — величина, которую человеку не объяснить"
    )
    assert isinstance(refusal.value.__cause__, IntegrityError), (
        "исходный отказ потерян: отладчику нечего прочитать в трассировке"
    )


@pytest.mark.asyncio
async def test_the_refusal_is_recorded_once_and_without_a_count(db_session):
    """Запись об отказе делается РОВНО ОДИН РАЗ и не называет числа намерений.

    Число незакрытых намерений больше никто не вычисляет: прикладная проверка
    снята целиком (D-06). Подставить сюда единицу «чтобы поле осталось» значило
    бы записать в журнал величину, которой никто не считал, — а по этому журналу
    разбирают денежные жалобы.
    """
    user = await _user(db_session)
    await _intent(db_session, user, payment_id="yoo_first")

    with _sdk("yoo_second"), patch(
        "app.services.payment_service.logger"
    ) as spy:
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
    assert set(fields) == {"user_id"}, (
        f"запись несёт поля сверх владельца отказа: {sorted(set(fields))}"
    )


@pytest.mark.asyncio
async def test_a_foreign_rejection_is_not_swallowed(db_session):
    """ЧУЖОЙ `IntegrityError` уходит наружу ТЕМ ЖЕ объектом.

    Чужой отказ, принятый за свой, показал бы человеку «предыдущая оплата не
    завершена» там, где сломалось что-то другое, — и настоящая поломка осталась
    бы незамеченной. Прецедент `_extend_subscription` поднимает исходный объект
    заново, и здесь проверяется именно ТОЖДЕСТВО объекта, а не совпадение типа.

    Отказ подаётся ПОДДЕЛКОЙ на вставке, потому что естественного чужого отказа
    у резервной строки нет: идентификатор платежа в ней `NULL`, а `NULL` оба
    диалекта считают различными. Существенно здесь не происхождение отказа, а
    поведение разбора: незакрытого намерения у пользователя НЕТ, значит вердикт
    обязан быть «не наш».
    """
    user = await _user(db_session)
    stranger = IntegrityError("INSERT", {}, Exception("some other constraint"))
    real_flush = db_session.flush
    calls = {"n": 0}

    async def flaky_flush(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise stranger
        return await real_flush(*args, **kwargs)

    with _sdk("yoo_new") as create_mock, patch.object(
        db_session, "flush", flaky_flush
    ):
        with pytest.raises(IntegrityError) as escaped:
            await _subscribe(db_session, user)

    assert escaped.value is stranger, (
        "чужой отказ подменён новым объектом — исходная поломка потеряна"
    )
    assert create_mock.call_count == 0


@pytest.mark.asyncio
async def test_the_sweep_survives_a_refused_reserve(db_session):
    """Уборка ЗАФИКСИРОВАНА СВОИМ КОММИТОМ и не уезжает в откат отказанного резерва.

    Путь отказа откатывает ТОЧКУ СОХРАНЕНИЯ резерва. Уборка, не зафиксированная
    отдельно, уехала бы в тот же откат — и человек, чьё просроченное намерение
    только что убрали, получил бы отказ И потерю уборки одновременно, то есть
    остался бы заперт ровно тем, что для него только что открыли.

    Отказ подаётся подделкой на вставке: под действующим индексом состояние
    «просроченная строка И живой отказ резерва» иначе недостижимо — просроченную
    строку уборка гасит первой, и отвергать вставку становится нечему.
    """
    user = await _user(db_session)
    stale = await _intent(
        db_session,
        user,
        payment_id="yoo_stale",
        age_hours=PENDING_INTENT_TTL_HOURS + 1,
    )
    stranger = IntegrityError("INSERT", {}, Exception("some other constraint"))
    real_flush = db_session.flush
    calls = {"n": 0}

    async def flaky_flush(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise stranger
        return await real_flush(*args, **kwargs)

    with _sdk("yoo_new"), patch.object(db_session, "flush", flaky_flush):
        with pytest.raises(IntegrityError):
            await _subscribe(db_session, user)

    survivors = {row.id: row.status for row in await _rows(db_session, user)}
    assert survivors == {stale.id: STATUS_EXPIRED}, (
        "уборка уехала в откат вместе с отвергнутым резервом — человек остался "
        f"заперт: {survivors}"
    )


@pytest.mark.asyncio
async def test_the_verdict_does_not_depend_on_the_driver_text(db_session):
    """Свой отказ различается ПЕРЕЧИТЫВАНИЕМ СОСТОЯНИЯ, а не текстом драйвера.

    ⚠️ ЭТО ГЛАВНОЕ УТВЕРЖДЕНИЕ ФАЙЛА, И ОНО ЗАКРЫВАЕТ ОШИБКУ ПРОЕКТИРОВАНИЯ.
    Решение D-06 предписывало разбирать отказ ПО ИМЕНИ ограничения. На SQLite,
    где идёт вся суита проекта, имени индекса в тексте отказа НЕТ вовсе —
    сообщается колонка (`UNIQUE constraint failed: payments.user_id`). Разбор по
    имени зеленел бы на бою и молчал в суите: потолок выглядел бы покрытым и
    покрыт не был.

    Проверяется поэтому НЕЗАВИСИМОСТЬ вердикта от текста в ОБЕ стороны: текст,
    называющий индекс поимённо, не делает отказ своим, если незакрытого
    намерения нет; и текст, не называющий ничего, не мешает признать отказ своим,
    когда намерение есть. Верно это на любом диалекте, потому что читается
    СОСТОЯНИЕ.
    """
    user = await _user(db_session)

    assert await _is_open_intent_conflict(db_session, user.id) is False, (
        "вердикт «наш отказ» вынесен пользователю без единого намерения"
    )

    await _intent(db_session, user, payment_id="yoo_open")
    assert await _is_open_intent_conflict(db_session, user.id) is True

    # Строка, выведенная из-под предиката индекса, конфликтом больше не является
    # — ровно потому, что вердикт читает СОСТОЯНИЕ, а не текст отказа.
    await _intent(
        db_session,
        await _user(db_session, "cap-expired@t.com"),
        payment_id="yoo_expired",
        status=STATUS_EXPIRED,
    )
    other = (
        await db_session.execute(
            select(User).where(User.email == "cap-expired@t.com")
        )
    ).scalar_one()
    assert await _is_open_intent_conflict(db_session, other.id) is False, (
        "погашенная строка засчитана конфликтом — предикат индекса её исключает"
    )


# =============================================================================
# УБОРКА: гасит ровно то, что считает предикат индекса
# =============================================================================


@pytest.mark.asyncio
async def test_a_stale_intent_is_swept_at_the_start_of_a_payment(db_session):
    """Просроченное намерение гасится В НАЧАЛЕ создания платежа, и оплата проходит.

    Без уборки включённый потолок запер бы владельца забытого намерения
    НАВСЕГДА: на проде отменённый платёж уведомления не получает и остаётся
    `pending` вечно (D-27). Уборка и потолок — одно переключение.
    """
    user = await _user(db_session)
    stale = await _intent(
        db_session,
        user,
        payment_id="yoo_stale",
        age_hours=PENDING_INTENT_TTL_HOURS + 1,
    )

    with _sdk("yoo_new"):
        result = await _subscribe(db_session, user)

    assert result["payment_id"] == "yoo_new"
    rows = {row.yookassa_payment_id: row.status for row in await _rows(db_session, user)}
    assert rows == {"yoo_stale": STATUS_EXPIRED, "yoo_new": STATUS_PENDING}, (
        "старая строка не погашена либо удалена: гасить — не значит удалять"
    )
    assert stale.id is not None


@pytest.mark.asyncio
async def test_a_second_sweep_touches_nothing_and_says_so(db_session):
    """ПОВТОРНАЯ уборка возвращает 0 и не трогает ни одной строки.

    Счётчик уборки — величина, по которой разбирают ДЕНЕЖНЫЕ жалобы, и врать он
    не вправе ни разу. Отбор «вне терминальных статусов» возвращал бы уже
    погашенные строки СНОВА при каждом создании платежа: уборка переписывала бы
    `expired` в `expired` и отдавала бы ненулевое число тронутых строк. Отбор
    сужен до равенства `pending` ровно поэтому (T-08-33).
    """
    user = await _user(db_session)
    await _intent(
        db_session,
        user,
        payment_id="yoo_stale",
        age_hours=PENDING_INTENT_TTL_HOURS + 1,
    )
    now = datetime.now(timezone.utc)

    assert await _expire_stale_intents(db_session, user.id, now) == 1
    before = {row.id: row.status for row in await _rows(db_session, user)}

    assert await _expire_stale_intents(db_session, user.id, now) == 0, (
        "уборка сосчитала проход вместо работы"
    )
    assert {row.id: row.status for row in await _rows(db_session, user)} == before


@pytest.mark.asyncio
async def test_the_sweep_takes_exactly_what_the_index_counts(db_session):
    """Уборка берёт РОВНО строки предиката индекса — ни одной сверх.

    Четыре соседние строки, каждая старше срока давности, и каждая обязана
    остаться нетронутой по своей причине: `expired` уже погашена (иначе счётчик
    соврал бы), `succeeded` терминальна и денег назад не отдаёт, `package` —
    другой предмет покупки и вне предиката, чужая строка принадлежит другому
    человеку. Тронуть лишнее здесь значит переписать ДЕНЕЖНУЮ строку.
    """
    user = await _user(db_session)
    old = PENDING_INTENT_TTL_HOURS + 5
    target = await _intent(
        db_session, user, payment_id="yoo_target", age_hours=old
    )
    already = await _intent(
        db_session,
        user,
        payment_id="yoo_already",
        status=STATUS_EXPIRED,
        age_hours=old,
    )
    done = await _intent(
        db_session,
        user,
        payment_id="yoo_done",
        status="succeeded",
        age_hours=old,
    )
    package = await _intent(
        db_session,
        user,
        payment_id="yoo_pack",
        kind=KIND_PACKAGE,
        age_hours=old,
    )
    stranger_user = await _user(db_session, "cap-stranger@t.com")
    stranger = await _intent(
        db_session, stranger_user, payment_id="yoo_stranger", age_hours=old
    )

    swept = await _expire_stale_intents(
        db_session, user.id, datetime.now(timezone.utc)
    )

    assert swept == 1, f"уборка тронула {swept} строк(и) вместо одной"
    states = {
        row.yookassa_payment_id: row.status
        for row in await _rows(db_session, user)
    }
    assert states[target.yookassa_payment_id] == STATUS_EXPIRED
    assert states[already.yookassa_payment_id] == STATUS_EXPIRED
    assert states[done.yookassa_payment_id] == "succeeded"
    assert states[package.yookassa_payment_id] == STATUS_PENDING
    survivors = await _rows(db_session, stranger_user)
    assert survivors[0].status == STATUS_PENDING, (
        f"уборка дотянулась до чужой строки {stranger.yookassa_payment_id}"
    )


@pytest.mark.asyncio
async def test_a_row_without_a_birth_time_is_left_alone(db_session):
    """Строка, чьё время рождения НЕ ПРОЧИТАЛОСЬ, считается СВЕЖЕЙ и не гасится.

    «Неизвестно когда» на денежной строке означало бы гашение по ОТСУТСТВИЮ
    данных, а это не то умолчание, которое ставят на денежном пути.

    ⚠️ СОСТОЯНИЕ ПОДАЁТСЯ ПОДМЕНОЙ ПРИВЕДЕНИЯ ВРЕМЕНИ, А НЕ СТРОКОЙ С `NULL`, И
    ЭТО ПРОВЕРЕНО, А НЕ ВЫБРАНО ИЗ УДОБСТВА. У колонки `created_at` в схеме
    стоит `NOT NULL` с `server_default`, поэтому строки с пустым временем
    рождения БАЗА НЕ ПРИНИМАЕТ ВОВСЕ — попытка её посадить падает
    `NOT NULL constraint failed: payments.created_at`. Пустое значение приходит с
    другой стороны: у объекта, которого СУБД ещё не проштамповала, и из
    `normalize_utc`, если прочитать время не удалось. Правило от этого не
    перестаёт быть несущим — оно защищает уборку от гашения по непрочитанным
    данным, — и подменяется здесь ровно то место, откуда пустое значение
    приходит на самом деле.
    """
    user = await _user(db_session)
    await _intent(
        db_session,
        user,
        payment_id="yoo_timeless",
        age_hours=PENDING_INTENT_TTL_HOURS + 10,
    )

    with patch(
        "app.services.payment_service.normalize_utc", return_value=None
    ) as unreadable:
        swept = await _expire_stale_intents(
            db_session, user.id, datetime.now(timezone.utc)
        )

    assert unreadable.call_count == 1, "уборка не читала время рождения строки"
    assert swept == 0, (
        "строка погашена по непрочитанному времени рождения — защита снята по "
        "отсутствию данных"
    )
    assert (await _rows(db_session, user))[0].status == STATUS_PENDING


@pytest.mark.asyncio
async def test_the_deadline_is_applied_in_python(db_session):
    """Срок давности считается в Python: наивное время обрабатывается как осведомлённое.

    Колонка объявлена `DateTime(timezone=True)`, но SQLite отдаёт её NAIVE, а
    PostgreSQL — aware. Сравнение, ушедшее в SQL, разошлось бы ровно на одном из
    двух диалектов: суита зеленела бы, а на бою уборка вела бы себя иначе — то
    есть дефект ловился бы пользователем, а не тестом.
    """
    aware_user = await _user(db_session, "cap-aware@t.com")
    aware = await _intent(
        db_session,
        aware_user,
        payment_id="yoo_aware",
        age_hours=PENDING_INTENT_TTL_HOURS + 1,
    )
    assert aware.created_at is not None

    naive_user = await _user(db_session, "cap-naive@t.com")
    naive = await _intent(
        db_session, naive_user, payment_id="yoo_naive", age_hours=0
    )
    naive.created_at = (
        datetime.now(timezone.utc) - timedelta(hours=PENDING_INTENT_TTL_HOURS + 1)
    ).replace(tzinfo=None)
    await db_session.commit()

    now = datetime.now(timezone.utc)
    assert await _expire_stale_intents(db_session, aware_user.id, now) == 1
    assert await _expire_stale_intents(db_session, naive_user.id, now) == 1, (
        "наивное время обработано иначе, чем осведомлённое — диалекты разойдутся"
    )


# =============================================================================
# ПОРЯДОК: у подписки «резерв → сеть», у пакета «сеть → запись»
# =============================================================================


@pytest.mark.asyncio
async def test_a_failed_sdk_call_expires_its_own_reserve(db_session):
    """Отказ SDK ПОСЛЕ резерва гасит СВОЮ ЖЕ строку — одна строка, `expired`, без id.

    Ни удаления, ни `pending`: удаление стёрло бы след попытки, а `pending`
    заперло бы человека потолком за платёж, которого ЮKassa не создала. Наружу
    поднимается `PaymentCreationError` — тот же тип, что и прежде, потому что
    ветка обработчика формы различает отказ по типу и этим планом не правится.
    """
    user = await _user(db_session)

    with _failing_sdk():
        with pytest.raises(PaymentCreationError):
            await _subscribe(db_session, user)

    rows = await _rows(db_session, user)
    assert len(rows) == 1, f"резерв удалён либо продублирован: строк {len(rows)}"
    assert rows[0].status == STATUS_EXPIRED
    assert rows[0].yookassa_payment_id is None


@pytest.mark.asyncio
async def test_a_reserve_killed_by_the_sdk_does_not_block_the_next_attempt(
    db_session,
):
    """Погашенная отказом SDK строка следующей попытке не мешает — и не ждёт уборки.

    Она СВЕЖАЯ (уборка её не возьмёт — срок давности не истёк) и при этом ВНЕ
    предиката индекса (`expired` им исключён). Без второго свойства человек,
    которому ЮKassa отказала, оказался бы заперт собственной неудачей на сутки.
    """
    user = await _user(db_session)

    with _failing_sdk():
        with pytest.raises(PaymentCreationError):
            await _subscribe(db_session, user)

    with _sdk("yoo_retry"):
        result = await _subscribe(db_session, user)

    assert result["payment_id"] == "yoo_retry"
    states = sorted(row.status for row in await _rows(db_session, user))
    assert states == [STATUS_EXPIRED, STATUS_PENDING]


@pytest.mark.asyncio
async def test_a_failed_package_payment_leaves_no_row_in_the_journal(db_session):
    """У ПАКЕТА порядок «сеть → запись» СОХРАНЁН: отказ SDK строки не оставляет.

    ⚠️ СВИДЕТЕЛЬ ЖИВЁТ ЗДЕСЬ, НА УРОВНЕ СЕРВИСА, И ЭТО НЕ ПЕРЕЕЗД РАДИ УДОБСТВА.
    Прежде утверждение стояло на уровне страницы
    (`tests/test_pages/test_billing_payment_errors.py`), но пакетной формы у
    раздела больше нет: валюта сообщений снята целиком, платёжный вход остался
    ОДИН — подписочный. Написать пакетный тест на уровне формы не из чего.
    Порядок при этом принадлежит сервису, а не форме, и утверждение стало ближе
    к своему предмету.

    Менять пакету порядок было не за чем: ограничение схемы существует ТОЛЬКО у
    подписочного намерения, поэтому только у него отказ способен прийти ПОСЛЕ
    вызова SDK. Для пакета рассуждение T-05-49 верно дословно — строка,
    оставшаяся после отказа, означала бы платёж, которого у ЮKassa нет вовсе.
    """
    user = await _user(db_session)

    with _failing_sdk():
        with pytest.raises(PaymentCreationError):
            await _buy_package(db_session, user)

    assert await _count(db_session, user) == 0


@pytest.mark.asyncio
async def test_the_predicate_catches_only_subscription_intents(db_session):
    """Подписка и пакет друг другу не мешают: предикат берёт только `subscription`.

    Утверждение в ОБЕ стороны. Индекс по пользователю целиком заперел бы его
    навсегда — ни одного второго платежа, ни за доступ, ни за сообщения.
    """
    buyer = await _user(db_session, "cap-both-a@t.com")
    await _intent(db_session, buyer, payment_id="yoo_access")

    with _sdk("yoo_pack"):
        package = await _buy_package(db_session, buyer)
    assert package["payment_id"] == "yoo_pack", (
        "подписочное намерение не даёт купить пакет"
    )

    other = await _user(db_session, "cap-both-b@t.com")
    await _intent(db_session, other, payment_id="yoo_pack_open", kind=KIND_PACKAGE)

    with _sdk("yoo_sub_new"):
        subscription = await _subscribe(db_session, other)
    assert subscription["payment_id"] == "yoo_sub_new", (
        "пакетный платёж не даёт купить подписку"
    )


# =============================================================================
# ОПЛАЧИВАЕМОСТЬ: погашенная строка остаётся зачисляемой
# =============================================================================


@pytest.mark.asyncio
async def test_a_claim_is_won_on_an_expired_intent(db_session):
    """Заявка ВЫИГРЫВАЕТСЯ на просроченной строке, и доступ выдаётся.

    ⚠️ ЭТО ОТВЕТ НА «ДЕНЬГИ ПРИНЯТЫ, ДОСТУП НЕ ВЫДАН» (T-08-24). Ссылка на
    оплату у ЮKassa переживает и уборку, и отказ SDK: человек по ней платит, и
    уведомление приезжает на строку, которую мы уже погасили. `expired` НЕ
    ВХОДИТ в `TERMINAL_STATUSES` именно поэтому — условие `_claim_payment`
    написано через множество, и ни одной правки под новый статус не
    потребовалось.
    """
    assert STATUS_EXPIRED not in TERMINAL_STATUSES, (
        "просроченная строка объявлена терминальной — заплативший по старой "
        "ссылке останется без доступа"
    )
    user = await _user(db_session)
    await _intent(
        db_session, user, payment_id="yoo_expired", status=STATUS_EXPIRED
    )

    processed = await handle_webhook(
        db_session,
        EVENT_SUCCEEDED,
        {"object": {"id": "yoo_expired", "status": "succeeded"}},
    )

    assert processed is True, "уведомление по погашенной строке не зачислено"
    granted = await db_session.scalar(
        select(func.count())
        .select_from(Subscription)
        .where(Subscription.user_id == user.id)
    )
    assert granted == 1, "доступ не выдан за принятые деньги"
